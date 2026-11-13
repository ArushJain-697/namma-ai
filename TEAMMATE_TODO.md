# Teammate jobs: run these all day (written 13 Nov 2026, the day before the hackathon)

Give this file to Claude Code on your laptop and say: "Read TEAMMATE_TODO.md and do the jobs in order."
The person running it does not need ML knowledge. Everything uses Sonnet 5.5 through the Claude Code CLI
(`claude -p`, your own Claude login) with Gemini as backup.

## 0. One-time setup (15 minutes)
```bash
git clone <repo> namma-ai && cd namma-ai
git checkout core-qwen3-executorch          # the working branch; ask Arush if it changed
git checkout -b graph-growth                # ALL your work goes on this branch
claude --version                            # Claude Code must be installed and logged in (run `claude` once, /login)
```
- `.env` with the Gemini keys: get it from Arush privately (never commit it, never paste keys in chat).
- Python environments:
```bash
python3 -m venv .venv && .venv/bin/pip install fsrs matplotlib pytest
uv venv --python 3.12 .venv-ml && VIRTUAL_ENV=.venv-ml uv pip install "torch==2.14.1" "sentence-transformers>=5" scikit-learn numpy "executorch==1.5.1" datasets accelerate
.venv/bin/python -m pytest -q --ignore=tests/test_resident.py     # should pass
```

## Job A: finish the meaning-based links (if Arush's run did not finish)
Check: if `data/misconceptions/links_v2.json` exists and `results/fix_links.log` ends with "wrote ...", skip this.
```bash
.venv-ml/bin/python scripts/fix_graph_links.py
python3 scripts/build_misconception_graph.py assemble && python3 scripts/graph_viewer.py
```
What it fixes: (1) "needs first" links between topics were matched by exact words (e.g. "multiplication of decimals"
was linked to Integers); now matched by meaning, with Sonnet judging close calls. (2) Root beliefs were 2,326 tiny
groups for 3,299 misconceptions; now ~120 named root beliefs, every misconception attached.
Report back: the last 4 lines it prints (link counts, root counts, biggest roots).

## Job B: redo the weak training data with Sonnet (most important for model quality)
All 2,758 training examples were written by Gemini's lightest model. Redo up to 300 passages with Sonnet.
IMPORTANT: run this in a SEPARATE copy of the repo on the original branch, NOT in the graph-growth folder: the job
list depends on the topic list, and Job C keeps adding topics, which would change the job names.
```bash
git clone <repo> namma-ai-data && cd namma-ai-data && git checkout core-qwen3-executorch   # + copy .env in
python3 scripts/make_dataset.py generate --split train --n 800 --workers 2 \
  --models claude:claude-sonnet-5-5,gemini-3.1-flash-lite --redo-teacher gemini-3.1-flash-lite --max-jobs 300
python3 scripts/make_dataset.py build        # prints counts; check "teachers" shows claude for ~1,000+ examples
```
- Safe to stop and rerun the same command (it continues). Old Gemini answers are kept in `data/dataset/raw_replaced/`.
- Sonnet takes 1-3 minutes per passage and has a usage limit; when it hits the limit the script falls back to Gemini.
  If you want ONLY Sonnet, drop `,gemini-3.1-flash-lite` from `--models` and rerun after the limit resets.
- Send back: `data/dataset/train.jsonl`, `val.jsonl`, `stats.json` (and the `raw/train/` folder if easy).

## Job C: grow the misconception graph all day
```bash
bash scripts/grow_graph.sh        # runs forever; Ctrl-C to stop; log: results/grow_graph.log
```
Each round: Sonnet proposes 8 new topics for one subject/area (rotating through maths, science, social, general),
duplicates of existing topics are rejected by meaning, then each topic gets a concept tree (big idea -> sub-concept
-> smallest idea), 12-30 misconceptions with fixes and diagnostic probes, and thin topics are deepened. Every 5
rounds it re-links prerequisites and root beliefs by meaning. After every round it rebuilds the graph and viewer and
runs two checks.
- Every hour or two, look at the log and commit:
```bash
grep -E "added|scored|suggested|topic\"" results/grow_graph.log | tail -12
git add data/misconceptions && git commit -m "Grow misconception graph: <N> topics"
```
- STOP and tell Arush if: "top-1 topic right" drops below 38/40, or the "suggested GENERIC_KW/COS" line changes a
  lot (the off-syllabus thresholds in src/sakshi/diagnostic.py must then be updated).
- To steer it, edit the AREAS list at the top of `scripts/grow_graph.sh` (e.g. add "science|Class 10 electricity").
- View the graph: `cd data/misconceptions/graph && python3 -m http.server 8765`, open http://localhost:8765/viewer.html

## Rules (breaking these breaks the training data or the demo)
1. Never run `build_misconception_graph.py generate --force` on topics that already exist: it renumbers their
   misconception ids, and the training data points at those ids.
2. Never edit `data/passages/eval/` or `data/dataset/test_passages.jsonl` (the frozen test sets).
3. Only touch `data/misconceptions/` on the graph-growth branch; Arush works on the code.
4. Never commit `.env`, `models/`, `.venv*`.
5. If Sonnet keeps failing with "hit your limit", let it be: the scripts fall back to Gemini or sleep and retry.

## Everything else that is still open (for Arush's main session, not for you)
- Plain Qwen3-0.6B writes 0 accepted diagnostic questions (copies the sentence, rambles, broken JSON): fix by
  prompt changes (worked examples as earlier turns, split each question into smaller calls, trim long answers,
  stop at the closing brace) and later by LoRA fine-tuning (`train/README.md`).
- Misconception mapper upgrades (`scripts/overnight_mapping.sh`: fine-tune the retriever, compare methods, export
  the winner to ExecuTorch) were stopped to cool the Mac; rerun when convenient.
- Helper models (meaning matcher, fact-checker) not yet timed on the Pi / Arduino UNO Q; the fact-checker is 329 MB.
- Off-syllabus thresholds have a thin margin (keyword cut-off 110 vs lowest syllabus passage 112.7): recalibrate
  after graph changes (`.venv-ml/bin/python scripts/calibrate_fallback.py`).
- "Documented in research" labels on misconceptions are model claims, not verified.
- Retention engine still needs connecting to real generated banks + the daily interleaved revision quiz.
- Nothing from 13 Nov is committed yet on the main branch.
