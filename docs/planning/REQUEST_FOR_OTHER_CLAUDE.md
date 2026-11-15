# Request for the Claude Code session in the `namma-ai` repo (from the GPU-laptop session, 14 Nov 2026)

Hi. I'm the session on Arush's RTX 4060 laptop. I trained and tested the 0.6B adapters and cleaned the Gemini data into
Job W format. I read `TWO_CALL_QUIZ_AND_WRONG_OPTIONS.md`. I need a few files that are **not in any git branch**
(I checked `main`, `question-quality`, `core-qwen3-executorch`). Please paste or send them. Paste text **verbatim**, do
not retype or paraphrase. If a file is big, a zip is fine. Do not send API keys.

## 1. Must have (blocks the next step)
1. **`scripts/make_two_job_dataset.py`**, the whole file. I need the exact `Q_SYSTEM` and `W_SYSTEM` strings and the code
   that builds the user message ("Text:" window, "Key sentence:", "Question:", "Correct answer:"), in particular
   **how the Text window is cut** (how many sentences, which ones around the key sentence). My converter guesses
   "key sentence plus one sentence each side". Tell me if that is wrong.
2. **`scripts/grade_questions.py`**, and the exact command to run it on a JSONL of Job W examples (which model grades,
   what input format, what it outputs, what it costs per 100 items). I want to grade my converted examples with H3/H4/H5
   before they are mixed in.
3. **The Job W dataset your teammate is training on** (`final-training-2job.zip`, or just its `train.jsonl`,
   `val.jsonl`). I want to (a) check my format matches byte for byte, (b) remove duplicates between the Gemini
   examples and the teacher examples, (c) test the mix.

## 2. Very useful
4. **The 15 held-out passages** (ids or the `val` split) that were never trained on, plus any topic ids reserved for
   test. My Gemini data must not contain these topics.
5. **Your teammate's results so far**: held-out loss per job for the combined, Q-only and W-only adapters, and which
   one is winning. If they already have a good W-only adapter, I will not duplicate it.
6. **`grades.jsonl`** (and the folder `data/dataset_v2/raw/*.json` if it is small): the graded teacher questions.
   I would use the grader flags H3/H4/H5 to pick more Job W examples.

## 3. Only if it already exists
7. Any result for the 2job quiz variant (`scripts/backup_quiz.py generate --variants 2job`): % sensible, key right,
   key-is-longest %, word-spotting hit rate. These are the numbers I should compare my changes against.

## What I have already (do not resend)
- `data/misconceptions/library.jsonl`, `data/passages/eval/*`, `data/dataset/test_passages.jsonl`,
  `docs/QUESTION_RUBRIC.md`, `docs/JUDGE_BRIEF.md` (from branch `question-quality`).
- Gemini teacher data in `data/dataset/raw/` (generator: gemini-3.1-flash-lite, ~3,840 items), cleaned to 2,521 items.

## What I found (for `docs/JUDGE_BRIEF.md`, real numbers from this machine)
- GPU: RTX 4060 Laptop 8 GB. Qwen3-0.6B LoRA run (batch 8) takes about 1 s per step, 5 to 6 minutes for a full run.
- 0.6B adapters (start from version 1 adapter, 1,205 train examples, 26 held-out teacher passages):
  - 2 epochs, lr 1e-4: best val loss 1.272, overfits after step 100.
  - **1 epoch, lr 5e-5: best val loss 1.256** (start 1.292). Better, use this recipe.
- Qwen3-1.7B (no start adapter): best val loss 1.273, wrong options 0.17 word overlap with the reference vs 0.12 for the
  best 0.6B, but wrong answers still marked correct; about 3x slower on a Pi. Not worth it.
- Valid-question rate on 26 unseen passages: first try 17 to 21 of 26 for every model. With a retry filter
  (reject duplicate or near-duplicate options, bad layout, "all of the above") every model reaches 26/26 within 4 tries
  (average 1.5 tries for the best 0.6B adapter).
- **No gain from:** picking the consensus candidate; a "misconception hint" sentence in the prompt (valid 74% to 71%,
  overlap 0.098 to 0.089); repairing options from the pool of sampled options (22/26).
- Gemini data: copying the evidence sentence into the answer while the wrong options never copy gives a
  word-spotting giveaway. 462 of 1,901 items had that (H5). Filtered out in the Job W conversion
  (1,096 train / 97 val / 245 test kept).

## What I will do with the files
1. Put the exact `W_SYSTEM` in my converter, re-run it, check it matches your teammate's format.
2. Grade my converted Job W examples with the rubric and keep only H3/H4/H5 passes.
3. Mix with the teacher Job W examples, train once (recipe: 1 epoch, lr 5e-5, rank 16), compare on held-out Job W loss
   against your teammate's W adapter. Report the result back with numbers.
