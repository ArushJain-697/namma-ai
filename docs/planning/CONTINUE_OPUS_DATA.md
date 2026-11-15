# Continue the Opus question data (hand this file + team-data.zip to Claude Code)

Say to Claude Code: **"Read CONTINUE_OPUS_DATA.md and do it. Don't change anything else."**

## What this is (context in 5 lines)
Hackathon project (Namma AI, 14 Nov 2026): an offline quiz maker on a Raspberry Pi using a small model
(Qwen3-0.6B). We fine-tune it on high-quality multiple-choice questions written by Claude Opus. A teammate started
the job: Opus writes ~5 questions for each of 800 training passages, Sonnet grades each one, and we keep only
score >= 4. It stopped at **146 of 800 passages** on a usage limit. Your job: **continue it from 147 onward**.
Nothing else. The scripts resume automatically: they skip passages already in `data/dataset_v2/raw/` and questions
already in `data/dataset_v2/grades.jsonl`.

## Setup (5 minutes)
1. Unzip `team-data.zip`. It contains a folder `namma-ai`. Work inside it:
   ```bash
   cd namma-ai
   ```
2. Needs only **Python 3.10+** (standard library) and the **Claude Code CLI logged in** (`claude --version`; if not
   logged in, run `claude` once and `/login`). The account needs **Opus** access. Test:
   ```bash
   cd /tmp && echo 'Return only: {"ok": true}' | claude -p --model claude-opus-5-5 --output-format json; cd -
   ```
   If the full id is rejected, check `claude -p --model opus` works and tell the human.
3. Check the starting point (expect 146 files, ~510 graded lines):
   ```bash
   ls data/dataset_v2/raw | wc -l ; wc -l data/dataset_v2/grades.jsonl
   ```

## Run (two background jobs; leave them running)
```bash
nohup python3 scripts/make_dataset.py rewrite --workers 3 > results/rewrite_v2.log 2>&1 &
nohup env PYTHON=python3 bash scripts/grade_follow.sh > results/grade_v2.log 2>&1 &
```
- Job 1: Opus writes questions for the remaining passages -> `data/dataset_v2/raw/<passage>.json`.
- Job 2: Sonnet grades them as they appear -> `data/dataset_v2/grades.jsonl`, then a final pass when job 1 ends.
- Progress: `tail -3 results/rewrite_v2.log ; tail -3 results/grade_v2.log ; ls data/dataset_v2/raw | wc -l`
- Each passage takes ~40 s per worker (3 workers: ~4-5 passages a minute when not rate-limited).

## If it stops
- "STOPPED on a usage limit" / "hit your limit": normal. Wait until the reset time shown, then **run the same two
  commands again**; they resume. Do not delete anything.
- Any other error: copy the last 20 lines of both logs to the human. Do not edit the scripts.

## Rules
- **Only one machine runs this at a time.** The teammate's laptop must NOT run it while you do, or both redo the
  same passages.
- Do not edit `scripts/`, `src/`, `data/misconceptions/`, `data/passages/eval/`, or `data/dataset/test_passages.jsonl`.
- Do not run `make_dataset.py build-v2` or anything else; the main team builds the training set from the raw files
  + grades.
- Never commit or push anything; never paste API keys anywhere.

## Send back (every few hours, and at the end)
Zip just the data folder and send the zip to the human:
```bash
zip -r opus-data-$(date +%H%M).zip data/dataset_v2 results/rewrite_v2.log results/grade_v2.log
```
Report: number of passages in `data/dataset_v2/raw`, number of lines in `grades.jsonl`, and how many have
`"score": 4` or `5` (`grep -cE '"score": (4|5)' data/dataset_v2/grades.jsonl`).
