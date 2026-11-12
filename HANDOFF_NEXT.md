# Handoff for the next Claude session (written 13 Nov 2026, the night before the hackathon)

Read this first, then `docs/SUBMISSION.md` (deliverables + measured numbers) and
`reports/Diagnostic MCQ small model design.md` (the researched architecture and fine-tuning plan).
The older docs (`HANDOFF.md`, `BUILD_MAP.md`, `MASTER_BIBLE.md`) describe the 4 Nov "Sakshi" design and are history.

## The user and the event
- Team lead (non-ML-specialist; prefers plain language, no jargon). Uses git for versions; **commit only when asked, never push**.
- Namma AI Hackathon (Arm + IIIT Bangalore + NASSCOM), Problem Statement 1, **live on 14 Nov 2026**, 6-8 h, on a
  **Raspberry Pi 5 (8 GB)** they receive on the day. Required: ExecuTorch on the Pi, a 150-300 word organiser passage,
  short summary + at least 3 relevant quiz questions, no cloud inference, report time / model / size / memory,
  impact explanation with one example from the passage. Organisers suggested Qwen2.5-0.5B-Instruct INT8 or TinyLlama
  1.1B INT8 but said **any model is fine, and fine-tuning before the event is allowed**.
- The pitch (user's `PROJECT_PLAN.md` in ~/Downloads): retention. Diagnostic questions (each wrong option = a named
  misconception) -> Bayes misconception detection -> concept-graph walk down/up -> BKT -> FSRS revision schedule ->
  `--simulate-days` retention chart. Tutor box hardware (TFT + buttons + camera) is an extra, owned by a teammate.

## Agreed order of work (user's words: "first something complete, then fine-tune")
1. Core deliverables working end to end on Qwen3 + ExecuTorch, tested on the Arduino UNO Q. **DONE.**
2. Misconception library (Gemini teacher). **IN PROGRESS** (see below).
3. Connect the retention engine to real model output + a small simulator ("tomorrow").
4. Diagnostic-question generation mode (staged, library-driven), then LoRA fine-tune Qwen3-0.6B, re-run the 40-passage eval.

## Repo state
- Branch `core-qwen3-executorch` (local only). Two commits on top of `cf30ee3`:
  `dcfe236` retention engine, `d9c57c1` real-model core. **Uncommitted** since then: `.gitignore`, `docs/SUBMISSION.md`,
  `data/passages/eval/` (40 passages + expected topics), `results/eval_qwen3_base/` (baseline eval),
  `scripts/batch_eval.py`, `scripts/build_misconception_library.py`, `scripts/check_library_match.py`,
  `src/sakshi/misconceptions.py`, `data/misconceptions/`, `reports/`, `research_notes/`. Ask before committing.
- Never commit: `.env` (holds GEMINI_API_KEY, git-ignored; the user pasted the key in chat, suggest rotating it later),
  `models/`, `.venv/`, `.venv-export/`.

## Environments
- `.venv` (Python 3.14): tests, retention engine (`fsrs` 6.3.2, matplotlib, pytest). Run tests:
  `.venv/bin/python -m pytest -q --ignore=tests/test_resident.py` (resident test needs Linux `unshare`). 218 tests pass.
- `.venv-export` (Python 3.12 via uv): executorch 1.5.1, torch 2.14.1, optimum-executorch 1.1.0, transformers 5.0.0rc1.
  Use it to run the real model on the Mac: `PYTHONPATH=src .venv-export/bin/python -m sakshi run PASSAGE --backend executorch --model models/qwen3-0.6b-8da4w/model.pte --tokenizer models/qwen3-0.6b-8da4w-portable/tokenizer.json`
- Model conversion (Mac): `.venv-export/bin/optimum-cli export executorch --model Qwen/Qwen3-0.6B --task text-generation --recipe xnnpack --use_custom_sdpa --use_custom_kv_cache --qlinear 8da4w --qembedding 8w --output_dir models/X`
  then download `tokenizer.json` with huggingface_hub (the export does not save it).
- `models/`: `qwen3-0.6b-8da4w` (fast, custom ops: Pi 5 / Mac), `qwen3-0.6b-8da4w-portable` and `-portable-1k`
  (no custom ops, max_seq_len 1024: for Cortex-A53), `qwen2.5-0.5b-8da4w` (+ `-portable`).

## Arduino UNO Q (dev board) facts
- Reached only over USB with `adb` (installed via `brew install --cask android-platform-tools`), user `arduino`.
  **No internet** on the board; clock ~14 months behind; use `/home/arduino` (18 GB), root has ~3 GB.
- Offline install recipe (reuse on the Pi if it has no internet): `pip download --only-binary=:all: --platform manylinux_2_28_aarch64 --python-version 3.13 ...` on the Mac,
  `adb push` wheels, venv with `--without-pip` and bootstrap pip from its wheel, `pip install --no-index --find-links`.
  **Use the CPU torch wheel** from `https://download.pytorch.org/whl/cpu` (the PyPI aarch64 torch pulls CUDA deps).
  executorch 1.5.1 installed `--no-deps`. Venv at `~/sakshi-venv`, repo copy at `~/namma-ai`, models at `~/models/`.
- Cortex-A53 has no dot-product instructions: loading ExecuTorch's `libcustom_ops_aot_lib.so` dies with
  **Illegal instruction**, so the board needs the "portable" export. Result: prefill ~10 tok/s, decode 0.37 tok/s,
  full pipeline 56 min, 1.7 GB peak, network OFF, **identical questions to the Mac** (so test quality on the Mac).
- `scripts/prove_offline.sh` passes on the board (fixed a bug: it read the loopback "UNKNOWN" state as a failure).

## What the code does now (key fixes found on real hardware)
- `src/sakshi/backends/executorch_backend.py`: loads the quantized kernel library always and the custom-ops library
  only if the CPU has `asimddp`; **captures fd 1** instead of using the token callback (the callback crashed on split
  UTF-8 characters); strips Qwen stop tokens and the runner's `PyTorchObserver` line; detects chat format
  (qwen3 / chatml / llama3) from the tokenizer (`--chat-format` overrides).
- `src/sakshi/backends/base.py`: `chat_prompt()` with worked examples as **separate turns** (Qwen3-0.6B copied an
  in-message example into every question). Qwen3 format appends an empty `<think>` block (thinking off).
- `src/sakshi/generate.py`: **answer-back check** (`verify_stem`): the model answers its own question from the
  witness sentence; mismatch -> held back. Catches some wrong questions but **misses shared errors**.
- `python -m sakshi run PASSAGE ...`: one screen with summary, quiz (options, answer, source sentence), run card
  (time, tokens in/out, prefill/decode tok/s, model, size, peak memory, device, network). This is the deliverable.
- Retention engine: `src/sakshi/retention/` (`learn`, `plan`, `simulate` CLI commands; sample bank
  `data/banks/photosynthesis.json`; that JSON format is what generated questions must eventually produce).
  Honest note: real FSRS says recall without revision is ~77% at day 7 / ~70% at day 14 (not the 30% in the
  user's plan); with the schedule ~96-98%.

## Baseline quality (40 passages, plain Qwen3-0.6B, Mac) -> `results/eval_qwen3_base/`
- All 40 got at least 3 questions; summaries good (94/96 model rewrites accepted).
- Only 21% of model-drafted questions pass checks; 73 of 122 shown are code fill-in-the-blanks.
- Of 49 model questions shown (my ratings in `rating.csv`, column `rating_claude`): 16 good, 13 ok, 12 bad,
  **8 factually wrong keys** (e.g. Ashoka's dhamma -> "religion", Nana Saheb -> "Jhansi"). Distractors are random
  passage words: zero diagnostic value. Most common failure: answer leaks into the question (119).
- **Before the demo**: consider showing only fill-ins + strongly verified questions, so no wrong key reaches judges.

## Misconception library (in progress at handoff)
- `data/misconceptions/topics.jsonl`: 143 NCERT Class 6-10 topics (science 67, social 76), names + scope only.
- `scripts/build_misconception_library.py generate --model gemini-3.1-flash-lite --workers 2` was running; ~47 of
  143 done at handoff. **Rerun the same command to resume** (it skips topics already in `data/misconceptions/raw/`).
  Gemini key is free tier: Pro models have zero quota; `gemini-3.5-flash`/`3.8-flash`/`flash-latest` returned 503
  overload; `gemini-2.5-flash` returned 404; **only `gemini-3.1-flash-lite` worked**. Its quality on the pilot was
  good (classic misconceptions, correct fixes), but it gives ~1-2 misconceptions per concept and over-claims
  "lit_supported". Optional later: rerun selected topics with a stronger model when available (`--only ... --force`).
- Then: `python3 scripts/build_misconception_library.py assemble` -> `library.jsonl`, `concepts.jsonl`
  (concept graph with prereqs), `review.csv` (~10% sample for the user: ok / fix / drop), `stats.json`.
- Then: `.venv/bin/python scripts/check_library_match.py --show 5` checks BM25 topic matching
  (`src/sakshi/misconceptions.py`, no model) against `data/passages/eval/expected_topics.json`. Tune if top-1 is low.
  Not yet run on real library output. Add unit tests for `misconceptions.py`.

## Next steps (in order)
1. Finish + assemble the library, run the match check, show the user `review.csv` and a sample.
2. Connect retention to real output: build a question-bank JSON (format of `data/banks/photosynthesis.json`) from
   a passage, then `learn` / `simulate` on it. The engine already accepts free-text or id misconceptions.
3. Diagnostic generation mode per the report: code retrieves 5-8 library misconceptions -> model stage Q writes
   answer then stem from a code-chosen evidence sentence -> model stage D writes one wrong option per belief label
   (B1-B5: label, short why, text) -> code keeps best 3, shuffles, fills feedback from library `fix` -> checks.
   Keep today's safe quiz as the fallback. Measure on the 40 passages with `scripts/batch_eval.py`.
4. Stronger verification (independent of the generator): code span/proximity checks, small NLI cross-encoder
   (`cross-encoder/nli-deberta-v3-xsmall`), extractive QA (`tinyroberta-squad2`); never use the 0.6B as a judge.
5. Fine-tune (report has details): ~2,000 filtered examples from a Gemini teacher (no NCERT text; teacher-written
   passages on NCERT topics + OpenStax / Simple Wikipedia / FineWeb-Edu), **plain LoRA r=32, alpha=32, dropout 0.05,
   all-linear, lr 2e-4 cosine, 2 epochs, batch 16, max_length 2048, completion-only loss, 16-bit (not QLoRA)**,
   Unsloth/TRL on Colab T4 (~30-50 min for 0.6B). Merge, export with the same optimum command (group size 32),
   compare before/after on the 40 frozen passages. Fallback: Qwen3-1.7B, same recipe.
6. On the day: first measure Pi 5 speed with `scripts/llm_probe.py` (fast export should load there; it never ran
   on Linux ARM yet), run `bash scripts/prove_offline.sh`, then `sakshi run` on the organiser passage, fill the
   Pi row in `docs/SUBMISSION.md` and the impact example.

## Gotchas
- `pkill -f llm_probe` inside an `adb shell '...'` kills the adb shell itself (pattern matches its own command line).
- `optimum-cli` export does not save the tokenizer; fetch `tokenizer.json` separately.
- TRL default max length (1024) would silently truncate training JSON; set 2048.
- Board run of `prepare` takes ~1 h with the portable model; run it with `nohup` and poll a file.
