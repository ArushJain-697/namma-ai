# Handoff: make the quiz questions GOOD (Qwen3-0.6B + Opus 5.5 teacher)

Written 13 Nov 2026, the day before the hackathon (Arm + NASSCOM + IIIT Bangalore + UK Government; winners may
go to the UK). Give this file to Claude Code on the friend's laptop: "Read this file and do the jobs in order."

## The one thing that matters
Judges want: a 150-300 word passage in, a short summary and **at least 3 very good quiz questions** out, offline,
on a Raspberry Pi 5 via ExecuTorch. Everything else (retention, misconception graph) is secondary. Today the
questions are bad:
- the plain Qwen3-0.6B produces **0 usable questions** in our diagnostic format (copies the sentence as the answer,
  repeats it as the question, rambles, runs out of tokens, broken JSON);
- the fallback is fill-in-the-blank (one word removed from a sentence) — **not acceptable, must not appear in the demo**;
- the existing training data (2,758 examples) was written by Gemini's weakest model: mediocre.

## Decisions already made by the team (do not reopen)
- **Model on the Pi: Qwen3-0.6B.** 1.7B and bigger are too slow for the demo.
- **Time budget: about 1 minute for the whole quiz on the Pi** (summary + 3-4 questions).
- **Teacher: Claude Opus 5.5** (`claude-opus-5-5`) through the Claude Code CLI on this laptop's account (it is
  unused, so it has its full limit). Sonnet 5.5 only as a fallback.
- **GPU for training: the team provides it.** Do not decide the GPU is a bottleneck; ask Arush.
- Nobody will hand-review the 20 gold questions: make them good yourself.

## Repo
```bash
git clone <repo> namma-ai && cd namma-ai && git checkout core-qwen3-executorch && git pull
git checkout -b question-quality
```
Get `.env` (Gemini keys) from Arush privately if needed; never commit it. Read `HANDOFF_NEXT.md` for the full
project history. Key files: `src/sakshi/diagnostic.py` (question format + checks, shared by training and device),
`scripts/make_dataset.py` (teacher data), `train/finetune_qwen3_lora.py` (LoRA), `scripts/eval_diagnostic.py`
(200-passage test), `data/dataset/` (800 training passages in `raw/train/`, 200 test passages), `TEAMMATE_TODO.md`
(the OTHER teammate's graph-growth jobs; never run those here, this account's Opus budget is for questions).

Check the CLI works with Opus first:
```bash
cd /tmp && echo 'Return only: {"ok": true}' | claude -p --model claude-opus-5-5 --output-format json
```
If the full id is rejected, use `--model opus`. `scripts/build_misconception_library.py::claude_generate` and the
`Teacher` class accept `claude:<model>` entries.

## Job 1 (1 hour): the quality bar
Write `docs/QUESTION_RUBRIC.md` and `data/gold_questions.jsonl` (20 questions on 5-6 of the training passages, all
subjects, written by Opus, checked by you against the rubric). A GOOD question:
1. Tests understanding, not word-spotting: why / how / what happens if / which explains / which example shows.
   At most 1 in 4 questions may be plain recall. **No fill-in-the-blank. No "according to the passage, what is true".**
2. Exactly one correct answer, provable from the passage (store the evidence sentence).
3. Three wrong options that a real Class 6-10 student could believe (ideally each tied to a misconception from
   `data/misconceptions/library.jsonl` for the passage's topic), same length, grammar and style as the answer,
   clearly wrong by the passage. Never "all/none of the above", never a second correct answer, no length cue.
4. Simple English for Class 6-10, question at most 25 words, options at most 12 words.
5. A one-line explanation for the student.

## Job 2 (code, 1-2 hours): new output format — the model writes the WHOLE question
The current format (code picks the answer word, model writes only wording) caused dull questions. New format, one
model call per question, short output so 0.6B stays fast and never runs out of tokens:
```json
{"q": "Why does a sharp knife cut better than a blunt one?",
 "options": ["It puts the same force on a smaller area", "It is heavier", "It is made of stronger metal", "It moves faster"],
 "answer": 0,
 "explain": "Same force on a smaller area means more pressure."}
```
- Input: the passage + one evidence sentence chosen by code + (optional) 3-5 misconception statements for the topic.
- Change `src/sakshi/diagnostic.py`: new `build_messages` / `target_json` / `parse_item` / `check_item` for this format
  (keep the old ones under new names so old tests still pass). Code still shuffles option order and records which
  misconception each wrong option targets (the teacher provides that mapping in training data).
- Checks to keep: answer supported by the evidence sentence (word overlap or NLI), no option repeated, no wrong
  option equal to the answer, lengths similar, no answer words leaked into the question, valid JSON.
- Keep `max_new_tokens` around 120 per question. Stop generation at the closing brace if possible.
- **Decided (13 Nov): one call per question, plus one call for the summary (5 calls per quiz). Do not switch to
  "all 4 questions in one call"; train and run in this layout only.** Speed budget for it (Qwen3 tokenizer, our 200
  test passages: passage avg 246 / max 323 tokens; one question in this format ~84 tokens; prompt per call ~400):
  | Pi 5 speed (read / write tokens per s) | Whole quiz |
  |---|---|
  | good: 150 / 22 | ~31 s |
  | likely: 60 / 20 (published Pi 5 Qwen3-0.6B decode is 21-23 tok/s, llama.cpp, not ExecuTorch) | ~52 s |
  | bad: 30 / 8 | ~115 s |
  So keep every call short: rubric + gold examples must stay small (each extra 100 prompt tokens costs ~8 s per
  quiz on the Pi in the likely case), no retries by default (a retry costs ~10 s), no best-of-2 unless the Pi
  measures much faster than "likely". Today's old pipeline (~25 calls, ~4,000 tokens in) would take ~2 minutes.
- When exporting the fine-tuned model, use `--max_seq_len 1024` (as in `train/README.md`), not 2048: same speed and
  answers, but peak memory 1.67 GB instead of 2.49 GB. So keep every call (prompt + answer) under ~900 tokens.
- Remove the fill-in-the-blank fallback from the demo path (`generate_bank` and `sakshi run`): if a slot fails twice,
  try another evidence sentence; if still under 3 questions, show fewer rather than fill-in-the-blank.
- Update `tests/test_diagnostic.py`; run `.venv/bin/python -m pytest -q --ignore=tests/test_resident.py`.

## Job 3 (3-5 hours, mostly waiting): Opus writes the training data
Reuse the 800 training passages already in `data/dataset/raw/train/*.json` (`response.passage`). For each passage,
Opus writes 4-5 questions in the new format following the rubric, with the 20 gold questions as examples in the
prompt (put the rubric + gold examples first and identical in every call so prompt caching helps). Add a mode to
`scripts/make_dataset.py` (e.g. `rewrite --teacher claude:claude-opus-5-5`) that saves to `data/dataset_v2/raw/`,
resumes after interruptions, and runs 2-3 workers. Expect usage limits: it must stop cleanly and resume later.
Target: ~3,000-4,000 questions. Keep the 200 test passages OUT of training (never rewrite `test_passages.jsonl`).

## Job 4 (1 hour): grade and filter
A grader (Sonnet 5.5 is fine, to save Opus quota) scores every question against the rubric (pass/fail per rule +
overall 1-5). Keep only overall >= 4 with all hard rules passed. Also drop questions where the code checks fail.
Build `data/dataset_v2/train.jsonl` and `val.jsonl` in the exact prompt format the device uses
(`chat_prompt("qwen3", ...)` from `src/sakshi/backends/base.py`). Report counts and 10 random examples.

## Job 5 (GPU, Arush's team): train
Update `train/finetune_qwen3_lora.py` defaults to the new data path. Suggested starting point for 0.6B: LoRA rank 64,
alpha 64, all linear layers, lr 2e-4, 3 epochs, batch 16, max length 2048, 16-bit (not 4-bit), answer-only loss.
Also try a full fine-tune of 0.6B if the GPU allows (often better for small models with this much data); keep the
better one by Job 6. Run the `--limit 64` smoke test first and check the "tokens that carry loss" print shows only
the JSON answer. Export with the command in `train/README.md` (8da4w; if quality drops vs the merged model, 8da8w).

## Job 6: measure (the number we show judges)
On the 200 test passages, for: plain Qwen3-0.6B, fine-tuned 0.6B, and Opus's own questions (the ceiling):
- % of question slots that produce a valid question;
- grader score (same rubric) and % "good" (>= 4);
- seconds per full quiz on the Mac and, when available, on the Pi (must fit ~1 minute on the Pi).
Write `results/question_quality.md` with the table and 10 example questions per model. If the fine-tuned 0.6B is
still weak, options to raise quality without a bigger model: best-of-2 per question with the checks picking the
better one (costs time), more/better Opus data, a second training pass on good-vs-bad pairs (preference training).

## Rules
- Do not touch `data/passages/eval/` or `data/dataset/test_passages.jsonl` except to read them.
- Do not edit `data/misconceptions/*`: the graph-growth teammate owns it (read-only for you; misconception ids are
  stable, new topics may appear when you `git pull` their branch).
- You own `src/`, `scripts/make_dataset.py`, `train/`, `data/dataset_v2/`. If the graph teammate reports new
  off-syllabus threshold suggestions, update `GENERIC_COS` / `GENERIC_KW` in `src/sakshi/diagnostic.py`.
- Commit often on `question-quality`; never commit `.env`, `models/`, `.venv*`.
- Tell Arush the numbers from Job 6 before anything goes into the demo.
