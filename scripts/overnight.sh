#!/usr/bin/env bash
# The overnight data pipeline. Safe to rerun: every step skips work that is already done.
#   bash scripts/overnight.sh            (log: results/overnight.log)
set -u
cd "$(dirname "$0")/.."
LOG=results/overnight.log
mkdir -p results
say() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
retry() {  # run a resumable generate step up to 5 times (transient overload errors); stop early when clean
  for i in 1 2 3 4 5; do
    out="$("$@" 2>&1 | tee -a "$LOG" | tail -1)"
    say "$out"
    case "$out" in *"done; 0 failed"*) return 0 ;; esac
    if grep -q "out of quota for today" <(tail -5 "$LOG"); then say "all keys out of quota; stopping this step"; return 1; fi
    say "retry $i in 60 s"; sleep 60
  done
}

say "== 1/6 misconception graph (219 topics: maths, science, social, general)"
retry python3 scripts/build_misconception_graph.py generate --workers 3 --models "gemini-3-flash-preview,claude:claude-sonnet-5-5,gemini-3.1-flash-lite"
say "== 1b/6 deepen thin topics (fewer than 10 misconceptions)"
retry python3 scripts/build_misconception_graph.py deepen --workers 3 --models "gemini-3-flash-preview,claude:claude-sonnet-5-5,gemini-3.1-flash-lite"
say "== 2/6 assemble graph + viewer + matching check + off-syllabus threshold check"
python3 scripts/build_misconception_graph.py assemble 2>&1 | grep -vE '^\s+"(SOC|SCI|MAT|GEN)-' | tee -a "$LOG" | tail -30
python3 scripts/graph_viewer.py | tee -a "$LOG"
.venv/bin/python scripts/check_library_match.py | tail -8 | tee -a "$LOG"
.venv-ml/bin/python scripts/calibrate_fallback.py 2>&1 | grep -E "syllabus|suggested" | tee -a "$LOG"

say "== 3/6 training passages + questions (target 800 passages)"
retry python3 scripts/make_dataset.py generate --split train --n 800 --workers 2
say "== 4/6 test passages (160 new + the 40 hand-written = 200)"
retry python3 scripts/make_dataset.py generate --split test --n 160 --workers 2
say "== 5/6 build training files"
python3 scripts/make_dataset.py build | tee -a "$LOG"
say "== 6/6 done"
say "== 7/7 baseline: plain Qwen3-0.6B in diagnostic mode on the 200 test passages"
PYTHONPATH=src .venv-export/bin/python scripts/eval_diagnostic.py --out results/eval_diag_base --backend executorch \
  --model models/qwen3-0.6b-8da4w/model.pte --tokenizer models/qwen3-0.6b-8da4w-portable/tokenizer.json 2>/dev/null | tail -20 | tee -a "$LOG"
say "== 7/7 done"
