# Teammate jobs: run these all day (written 13 Nov 2026, the day before the hackathon)

Give this file to Claude Code on your laptop and say: "Read TEAMMATE_TODO.md and do the jobs in order."
The person running it does not need ML knowledge. Everything uses Sonnet 5.5 through the Claude Code CLI (your account; the OTHER teammate's account is reserved
for Opus question writing)
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

## Job A: DONE (meaning-based links finished and committed on 13 Nov, commit e9888dd)
`data/misconceptions/links_v2.json` exists: 1,955 Sonnet-checked cross-topic links, 120 named root beliefs.
The growth loop below re-runs it every 5 rounds; you do not need to run it by hand.

## Job B: CANCELLED (training data is now the other teammate's job, with Opus, in a new format; see
`QUESTION_QUALITY_HANDOFF.md`). Do not run `make_dataset.py` on this laptop.

## Job C (your only job): grow the misconception graph all day
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
3. Only touch `data/misconceptions/` (and `scripts/grow_graph.sh` AREAS) on the graph-growth branch. Never edit
   `src/` or `data/dataset*`: the question-quality teammate owns those. If the off-syllabus thresholds drift,
   report the "suggested" line to Arush instead of editing `src/sakshi/diagnostic.py`.
4. Never commit `.env`, `models/`, `.venv*`.
5. If Sonnet keeps failing with "hit your limit", let it be: the scripts fall back to Gemini or sleep and retry.

## Everything else that is still open (for Arush's main session, not for you)
- Misconception mapper upgrades (`scripts/overnight_mapping.sh`: fine-tune the retriever, compare methods, export
  the winner to ExecuTorch) were stopped to cool the Mac; rerun when convenient.
- Helper models (meaning matcher, fact-checker) not yet timed on the Pi / Arduino UNO Q; the fact-checker is 329 MB.
- Off-syllabus thresholds have a thin margin (keyword cut-off 110 vs lowest syllabus passage 112.7): recalibrate
  after graph changes (`.venv-ml/bin/python scripts/calibrate_fallback.py`).
- "Documented in research" labels on misconceptions are model claims, not verified.
- Retention engine still needs connecting to real generated banks + the daily interleaved revision quiz.
- Question quality (the top priority) is handled by the other teammate: `QUESTION_QUALITY_HANDOFF.md`.
