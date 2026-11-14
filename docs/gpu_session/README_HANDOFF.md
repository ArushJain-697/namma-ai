# GPU-laptop session handoff for the main Claude (namma-ai repo), 14 Nov 2026

Everything here was trained/tested on an **RTX 4060 Laptop 8 GB** (not a 4080). **Nothing was run on a Raspberry Pi.**
All adapters are LoRA (rank 16, all linear layers) for **Qwen3-0.6B** unless the folder says 1.7b. Merge into the plain base model
(`Qwen/Qwen3-0.6B`) to use. They are NOT interchangeable between 0.6B and 1.7B. Merged models (1.2 GB each) are not included; rebuild with
`PeftModel.from_pretrained(base, adapter).merge_and_unload()`. The 0.6B single-call adapters were trained on top of the version-1 adapter
(`start/v1_adapter`, in the repo/zip you already have), so merge v1 first, then the new adapter.

## Folder map
- `adapters/` : trained LoRA adapters (one folder each, ~36 MB; 1.7B ~62 MB)
  - `qwen3-0.6b_BEST_single-call_lr5e5` : v1 + 1 epoch lr 5e-5 on the 1,205-example single-call set. val loss 1.256 (start 1.292). Use for the old single-call quiz format.
  - `qwen3-0.6b_first-run_lr1e4_2ep` : same data, 2 epochs lr 1e-4, val 1.272, overfits after step 100. Spare.
  - `qwen3-1.7b_single-call` : Qwen3-1.7B from scratch (no v1), val 1.273. Not recommended.
  - `job-both_COMBINED_Q+W_recommended` : **two-job adapter (Job Q and Job W chosen by the system prompt)**, from v1, 1 epoch lr 5e-5, on the teammate's `two_job_data/train.jsonl`. Recommended: one file for the Pi.
  - `job-w_wrong-options_teacher`, `job-q_question+answer` : specialist adapters on `train_W.jsonl` / `train_Q.jsonl`.
  - `job-w-mix_wrong-options_teacher+gemini` : Job W on teacher + 793 Gemini examples. No gain (held-out W loss 1.440 vs 1.435), dropped.
- `logs/` : training logs (val loss every 50 steps; the best checkpoint is kept).
- `scripts/` : every test script (see list below) + `quiz_filter.py` (output filter, no dependencies, Pi-ready).
- `datasets/` : `gemini-clean-dataset/` (Gemini data cleaned by extra filters; `opts/`, `qa/`, `w-job/`, builder `build_opts.py`) and `train_W_mix.jsonl`.
- `results/` : raw outputs (`bench_out.json` 120 questions A vs B, `overgen_out.json`, blind maps).
- `docs/` : `PI5_TECH_PLAN.md`, `SUBMISSION_SUMMARY.md` (hackathon summary template), the request/reply with the other Claude.

## Measured results (all on GPU, bf16 unless stated)
1. **Held-out loss** (teacher val, 26 passages; lower better): v1 start 1.292 -> 1 epoch lr 5e-5 **1.256** (best) ; 2 epochs lr 1e-4 1.272.
   Two-job (310 val examples): job-w 1.435, job-w-mix 1.440, job-q 1.218.
2. **Filter** (`quiz_filter.py`: layout, 4 distinct options, no all/none-of-the-above, retry up to 4): every model reaches 26/26 valid within 4 tries (best 0.6B: avg 1.5 tries). Without it 17-21 of 26 are valid first try.
3. **Wrong options, greedy** are often near-duplicates (~60%) or copy the correct answer (18-26%). **Sampled twice + dedupe + pick 3 closest to the key** (the handoff's method): 141-154 of 156 held-out examples get 3 distinct options. The combined adapter is best at 2 samples (147/156, key-longest 5/156).
4. **Two-job vs single-call pipeline**, 40 unseen eval passages x3 key sentences, automatic: key is the longest option 6% vs 15%; why/how-style questions 49% vs 39%; word-spotting bot hit 47% vs 43% (chance 25%, not improved).
   Blind read by Claude (12 pairs): good questions two-job **8/12** vs single-call **3/12**.
5. **Wrong options blind (20 sets, same questions, teacher vs model)**: teacher-written **20/20** fully good, model (combined adapter) **10/20**. Main failure: a wrong option that is really also correct (5/10), then near-duplicates, nonsense.
6. **Strict blind read of 60 two-job questions on unseen passages**: about **40-55% fully sound** (answer supported by the text, no 2nd correct option, wrong options clearly wrong). Typical faults: unsupported answer, two correct options, garbled question. Subjective, one grader.
7. **Quantization (simulated on GPU; re-measure on the real .pte)**, held-out loss Q/W: bf16 1.217/1.429; **8-bit weights+8-bit activations 1.223/1.436 (lossless)**; 4-bit g128 1.385/1.661; 4-bit g32 (8da4w-style) 1.345/1.564; 4-bit g32 with sensitive layers at 8-bit 1.306/1.511.
   So 4-bit costs about +0.13 loss. Recommendation: export 8-bit (about 600 MB, about 1.5x slower decode than 4-bit), 4-bit only as an eco mode.
8. **Things that did NOT help** (do not repeat): consensus-answer candidate picking; a "misconception hint" sentence in the prompt (valid 74% -> 71%); repairing options from a pool of sampled options (22/26); rule-based picking of best 3 of 6 questions (picked 8/15 vs rejected 6/15); Gemini data mixed into Job W; Qwen3-1.7B (word-overlap 0.17 vs 0.12 but still wrong keys marked correct, 3x slower on Pi).
9. A local Qwen3-1.7B judge was tried and discarded (too weak); the user also does not want the Claude CLI used. All quality judgements above were done by reading, blind where noted.

## Gemini data (from branch `question-quality`, data/dataset/raw)
Generator is **gemini-3.1-flash-lite**, not Opus/Sonnet; passed automatic validators only, no LLM grading. Each wrong option carries a misconception `why`.
Cleaned further (`build_opts.py`): 3,839 items -> 2,521 kept. For Job W conversion the extra H5 filters removed 462 items where only the key copies passage wording
(a giveaway the model would learn), 329 capitalisation mismatches, 256 key-longest. Topics in `heldout.json` and `data/passages/eval/expected_topics.json` were excluded from any training mix.

## Known issues / not done
- **Pi numbers are all missing** (speed, RAM, power, size, thermals). `PI5_TECH_PLAN.md` has calculated values (~390 MB at 4-bit, ~596 MB at 8-bit, KV 117 MB fp16 at 1,024 tokens) and the measurement checklist.
  One web source reports ExecuTorch+XNNPACK on Pi 5 far slower than llama.cpp (and an INT4 fusion failure on aarch64); compare both backends first.
- Task page requires (Problem 1): summary + 3 quiz questions from an organiser passage on ExecuTorch/Pi, report time/model/size, impact example, GitHub repo. "Approved lightweight model": check the Notice Board that Qwen3-0.6B is allowed.
- How the passage **summary** is produced is not covered by these adapters; confirm it is the repo's summariser.
- Idea not built: let code pick the answer phrase from the key sentence and have the model write only the question (removes the "answer not supported" failures); retrain needed.
- Short (1-word) system prompts to save Pi prefill tokens: not trained or verified (accept only if held-out loss and a blind read stay equal).

## Scripts (all in `scripts/`, Windows paths inside; run with the final-training venv)
`evalw.py` greedy W eval; `evalw2.py` sampled W + dedupe; `cmp3.py`/`cmp4.py` valid-rate tests; `pipe.py` repair pipeline; `bench.py` two-pipeline benchmark;
`optblind.py` blind teacher-vs-model options; `quantsim.py` quantization simulation; `overgen.py` over-generate test; `convert_w.py`/`mix_w.py` Gemini -> Job W; `build_opts.py` cleaning; `quiz_filter.py` filter.
Recipe used by every adapter: `train/finetune.py --start-adapter start/v1_adapter --epochs 1 --lr 5e-5 --rank 16 --batch 8 --eval-every 50`.
