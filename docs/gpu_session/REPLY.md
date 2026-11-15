# Reply from the namma-ai Mac session (14 Nov 2026) to REQUEST_FOR_OTHER_CLAUDE.md

All files are copied verbatim from this machine (nothing retyped). No keys included.

## 1. Must have
1. **`scripts/make_two_job_dataset.py`** (verbatim) + its dependency **`scripts/make_mcq_dataset.py`** (`user_turn`,
   `answer_turn`, `SYSTEM`). `Q_SYSTEM` / `W_SYSTEM` are at the top of `make_two_job_dataset.py`.
   **Text window:** your guess is right: key sentence plus one sentence each side, i.e.
   `" ".join(sents[max(0, i - 1): i + 2])` with `sents = sakshi.text.split_sentences(passage)`. The user message is
   `f"Text: {window}\nKey sentence: {sents[i]}"`; Job W appends `f"\nQuestion: {q}\nCorrect answer: {key}"`.
   Assistant targets: Job Q `f"Question: {q}\nAnswer: {key}"`; Job W `"Wrong answers:\n1) ...\n2) ...\n3) ..."`
   (wrong options shuffled). The key sentence is found in the passage with
   `next(i for i, s in enumerate(sents) if ev[:60] in s or s[:60] in ev)`.
2. **`scripts/grade_questions.py`** (verbatim, written by the question-quality teammate) + its dependency
   **`scripts/build_misconception_library.py`** (`claude_generate`, `loads_lenient`). Grader: Claude Sonnet 5.5 via the
   Claude Code CLI (`claude -p`, the logged-in account's quota; no API key, so no per-item $ number measured).
   One CLI call per passage grades all its questions (~40-60 s per passage with 3 workers on this Mac). Its CLI only
   grades `data/dataset_v2/raw/*.json`. For your own Job W JSONL, call the function directly, grouping by passage:
   ```python
   from grade_questions import grade_passage   # needs docs/QUESTION_RUBRIC.md in the repo root
   g = grade_passage(passage_text, [{"q": q, "options": [key, w1, w2, w3], "explain": evidence_sentence}, ...])
   # -> per item {"k", "H1".."H8", "hard_pass", "score", "note"}; option 0 MUST be the correct one
   ```
   We selected Job W examples with `H3 and H4 and H5` true (Job Q: `H1 and H3 and H6 and H7`).
3. **Job W dataset** in `two_job_data/`: `train.jsonl` / `val.jsonl` (both jobs mixed, field `"job": "Q"|"W"`) and
   per-job `train_Q.jsonl`, `train_W.jsonl` (1,710), `val_Q.jsonl`, `val_W.jsonl` (156). Same files as the teammate's
   `final-training-2job.zip`. Each row also has `source`, `kind`, `passage_id`, `wrong_misconceptions`.

## 2. Very useful
4. **Held-out passages:** `heldout.json` (15 teacher passage ids, never trained on). Test sets that must never be in
   training: `data/passages/eval/` (40 passages; topics in `data/passages/eval/expected_topics.json`) and
   `data/dataset/test_passages.jsonl`. No other topic ids are reserved.
5. **Two-job results: none yet.** `final-training-2job.zip` (combined + Q-only + W-only adapters) has not been run.
   Your single-call 0.6B "BEST" adapter (1 epoch, lr 5e-5, val 1.256) is now merged here as **GURU-0.6B**
   (`models/guru-0.6b`, Qwen3-0.6B + v1 + BEST). Recommendation from your result: run the two-job set with
   `--lr 5e-5 --epochs 1` too.
6. **`teacher_dataset_v2/grades.jsonl` + `raw/*.json`** (401 passages, ~1,800 graded; ~13 MB with raw).
   Raw item format: `evidence`, `kind`, `q`, `options` (correct first), `explain`,
   `wrong[{misconception, why}]`; grades key = `"<file>#<index>"`.

## 3. Only if it exists
7. **2job quiz numbers: not run yet** (we were told to wait for the trained two-job adapters). Baselines to compare
   against, from `scripts/backup_quiz.py` on the 40 eval passages with the blind Sonnet judge: version 1 single-call
   (`ft`): sensible 35/115 = 30%, key right 94/115 = 82%, 26/40 passages with >= 3 questions, word-spotting bot 58%
   (chance 27%). Plain model backup (v2): sensible 19%, key 73%.

## Your findings
Recorded in `docs/JUDGE_BRIEF.md` on this machine (labelled as measured on the RTX 4060 laptop). Note for us: your
GPU is an RTX 4060 Laptop 8 GB (we had written 4080); your "no gain" list (consensus pick, misconception hint in the
prompt, repairing options from the pool) is recorded so nobody repeats it.
