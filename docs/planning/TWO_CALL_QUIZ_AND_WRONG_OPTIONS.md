# GURU-0.6B two-call quiz + training wrong options from the misconception graph (handoff, 14 Nov 2026)

Give this to a Claude Code session working in the `namma-ai` repo. Read `docs/JUDGE_BRIEF.md` too (decisions and
numbers). Standing rules: research before building (show sources with numbers), measure everything, never invent
numbers, record results in `docs/JUDGE_BRIEF.md`, commit only when the human asks.

## 1. Where things stand
- Model: **GURU-0.6B** (Grounded Understanding, Runs Unplugged) = Qwen3-0.6B fine-tuned with LoRA, runs on a
  Raspberry Pi 5 via ExecuTorch (4-bit 8da4w, `--max_seq_len 1024`). Version 1 adapter (SciQ+RACE):
  `out/qwen3-0.6b-mcq/adapter`. Version-1 test result: 30% "sensible", answer key right 82% (40 test passages,
  blind Sonnet grade). Later run on teacher data: questions very good, **wrong options still weak**. 1.7B was not
  clearly better, so we stay with 0.6B.
- Current plan: **two short jobs instead of one big one** (the "two-call" quiz):
  - **Job Q:** text window + key sentence -> `Question: ...\nAnswer: <correct answer>`
  - **Job W:** text window + key sentence + `Question:` + `Correct answer:` -> `Wrong answers:\n1) ...\n2) ...\n3) ...`
  - One combined adapter (prompt picks the job) AND two specialist adapters (Q-only, W-only) are being trained on a
    teammate's RTX 4080 from `~/Downloads/final-training-2job.zip`; pick by held-out loss per job + format check.
- Training data (two-job): selected PER JOB from ~1,800 graded teacher questions by the grader's rule flags:
  Job Q = questions passing H1,H3,H6,H7 (1,353); Job W = questions whose options pass H3,H4,H5 (1,410); + 300 RACE
  per job. 3,363 train / 310 held-out from 15 never-trained passages (0 overlap). Builder:
  `scripts/make_two_job_dataset.py` (prompts `Q_SYSTEM`, `W_SYSTEM` live there; reuse them EXACTLY).
- Raw teacher data (not in git): `/Users/arushjain/Documents/opus-work/namma-ai/data/dataset_v2/raw/*.json` +
  `grades.jsonl`. Each item: `evidence`, `q`, `options` (correct first), `wrong[{misconception: id, why}]`.

## 2. The two-call quiz at inference (built, NOT yet run on a trained model)
Code: `scripts/backup_quiz.py`, function `quiz_2job`, variant `2job`:
```bash
.venv-ml/bin/python scripts/backup_quiz.py generate --variants 2job --model models/guru-0.6b [--w-model models/guru-w]
.venv-ml/bin/python scripts/backup_quiz.py judge && .venv-ml/bin/python scripts/backup_quiz.py report
```
Steps per key sentence (code picks key sentences with `pick_sentences`):
1. Call Job Q (prefix "Question:") -> question + correct answer.
2. Call Job W **twice** (prefix "Wrong answers:\n1)") -> up to 6 candidates; normalise case/full stop; drop repeats,
   "all/none of the above", > 14 words.
3. **Pick the 3 candidates most similar to the key**: rank by length gap (relative), same opening word, and
   |passage-word overlap(candidate) - overlap(key)| (a trap that reuses the passage's words wrongly, e.g. "sound
   travels faster than light", beats one that does not).
4. **Giveaway check** `option_shape_ok`: reject if the key is > 3 words longer/shorter than every wrong option, has a
   distinctive opening ("Because/To/By/So") the others lack, or copies the passage (overlap gap >= 0.6) while no
   wrong option does; tries the next-best candidates first.
5. `code_check` (repeats, leaks, length, NOT-questions) + **self-check** (model answers its own question with
   shuffled options; wrong -> drop). Options are shuffled; 3-option questions are allowed (Rodriguez 2005).
Unit cases checked: circle formulas pass; long key caught; key-copies-passage caught; a passage-word trap passes.
Metrics to report on the 40 test passages (`data/passages/eval/`): % sensible + key right (blind Sonnet,
`judge`), **% where the key is the longest option (target ~25%)**, **word-spotting bot hit rate (target near
chance; version 1 was 58%)**, Pi time estimate (from token counts; real Pi number from `pi-kit/test.sh`).
Known runtime quirk: the ExecuTorch runner does not stop at Qwen's `<|im_end|>`, so parsers cut after the first
answer block.

## 3. Experiment: train Job W from the misconception graph (for the other Claude)
Goal: more and better **wrong-option** training examples, each wrong option being a real student belief.
Source: `data/misconceptions/library.jsonl` (~3,400 misconceptions in git; graph grows on the teammate's branch).
Fields per misconception: `id, topic_id, concept, statement` (the wrong belief), `why` (why students hold it),
`fix` (the correct idea), `probe` = `{question, wrong_answer}` (a test question and the answer a believer gives),
`root_belief`, `grades`, `trigger_cues`.
Ideas, in order of expected value (measure each; keep only what beats the baseline on held-out Job W loss and on
the 2job quiz metrics above):
1. **Probe-based Job W examples.** Each `probe` already gives a question and one believer's wrong answer. Use
   Claude (Sonnet is enough) offline to add: the correct answer (from `fix`), and 2 more wrong answers from OTHER
   misconceptions of the same concept/topic, written in the same length/style as the key. Write each example in the
   exact Job W format (`W_SYSTEM`, user = `Text: <2-3 sentences built from concept + fix>\nKey sentence: ...\n
   Question: ...\nCorrect answer: ...`, assistant = `Wrong answers:\n1) ...`). Then grade them with the same rubric
   (`scripts/grade_questions.py` logic / `docs/QUESTION_RUBRIC.md`) and keep only H3+H4+H5 passes.
2. **Teacher items + graph link.** The teacher data's `wrong[].misconception` ids map options to graph nodes; add
   the misconception `statement` as a hint in the Job W input during training (and at inference retrieve the top
   misconceptions for the topic with `src/sakshi/mapper.py`). Only if it clearly helps: it costs prompt tokens on
   the Pi (~8 s per 100 tokens per quiz).
3. Do NOT train wrong options as raw misconception statements (we tried using them directly as options: graded
   only 19% sensible, mostly off-topic; see `results/backup_quiz/old/REPORT_v2.md`).
Rules for the experiment:
- **Split by topic** (or by passage) so test topics never appear in training; never use `data/passages/eval/` or
  `data/dataset/test_passages.jsonl` for training.
- Same training script and recipe: `train/finetune_mac.py` (MPS or CUDA; `--start-adapter` to start from version
  1; `--eval-every 50`; best held-out checkpoint kept; 1-3 epochs, lr 1e-4-2e-4, rank 16 / alpha 32 all linear
  layers, per the Unsloth LoRA guide). On a Mac close heavy apps (MPS ran out of memory once at batch 4; batch 2 ok).
- Mix, don't replace: combine graph-derived Job W examples with the teacher Job W examples; report the effect of
  the mix ratio.
- Export for the Pi exactly like the others: `optimum-cli export executorch ... --qlinear 8da4w --qembedding 8w
  --max_seq_len 1024` (see `train/README.md`), then test with the `2job` variant above.
- Write results into `docs/JUDGE_BRIEF.md` (what was tried, numbers, kept or dropped).
