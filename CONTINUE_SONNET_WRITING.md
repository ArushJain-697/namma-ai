# Continue writing questions with Sonnet (hand this file + opus-continue.zip to Claude Code)

Say to Claude Code: **"Read CONTINUE_OPUS_WRITING.md and do it. Don't change anything else."**

## Context (5 lines)
Hackathon project (Namma AI, 14 Nov 2026): an offline quiz maker on a Raspberry Pi with a small model
(Qwen3-0.6B). We fine-tune it on multiple-choice questions written by Claude (Opus so far, **Sonnet 5.5 from now on**).
For each of 800 training passages, the teacher writes ~4-5 questions. **283 of 800 passages are done** (in `data/dataset_v2/raw/`). Your only job:
**write questions for the remaining passages with Sonnet 5.5**. Grading is done by the main team on another machine, so
**do NOT run any grading script**. The writer skips passages that already have a file, so it continues from 284.

## Setup (5 minutes)
1. Unzip `opus-continue.zip`; it contains a folder `namma-ai`. Work inside it:
   ```bash
   cd namma-ai
   ```
2. Needs **Python 3.10+** (standard library only) and the **Claude Code CLI logged in** (any account with
   Sonnet). Test (should print JSON with `"ok": true` inside):
   ```bash
   cd /tmp && echo 'Return only: {"ok": true}' | claude -p --model claude-sonnet-5-5 --output-format json; cd -
   ```
   If that model name is rejected, check `claude -p --model sonnet` works and tell the human (do not change scripts).
3. Starting point (expect 283):
   ```bash
   ls data/dataset_v2/raw | wc -l
   ```

## Run (one background job; leave it running)
```bash
nohup python3 scripts/make_dataset.py rewrite --teacher claude:claude-sonnet-5-5 --workers 3 > results/rewrite_v3.log 2>&1 &
```
- Progress: `tail -3 results/rewrite_v3.log ; ls data/dataset_v2/raw | wc -l`
- About 40 s per passage per worker (3 workers: ~4 passages a minute). Target: as many as possible; 400+ total is
  the goal, all 800 is great.

## If it stops
- "STOPPED on a usage limit" / "hit your limit": normal. Wait for the reset time shown, then run the **same
  command** again; it resumes. Never delete files in `data/dataset_v2/raw/`.
- Any other error: send the last 20 lines of `results/rewrite_v3.log` to the human. Do not edit scripts.

## Rules
- Only this machine writes. Nobody else runs `make_dataset.py rewrite` at the same time.
- Do NOT run `grade_questions.py`, `grade_follow.sh`, `make_dataset.py build-v2`, or anything else.
- Do not edit `scripts/`, `src/`, `docs/`, `data/misconceptions/`, `data/passages/`, `data/dataset/`.
- Never commit, push or paste API keys anywhere.

## Send back (every 1-2 hours, and when it stops for the night)
Only the new data, small zip:
```bash
zip -r ~/Downloads/opus-raw-$(date +%H%M).zip data/dataset_v2/raw results/rewrite_v3.log
```
Tell the human how many files are in `data/dataset_v2/raw` (`ls data/dataset_v2/raw | wc -l`).
