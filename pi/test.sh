#!/usr/bin/env bash
# Pi day kit: prove it works and collect the numbers judges asked for. Run after install.sh:
#   bash test.sh [passage.txt]      (log: test.log; default passage: the sample rust passage)
#   QUICK=1 bash test.sh            skip the full summary+quiz run (it takes ~1 hour on slow boards like the UNO Q)
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
LOG="$KIT/test.log"
exec > >(tee "$LOG") 2>&1
PY="$HOME/sakshi-venv/bin/python"
REPO="$HOME/namma-ai"
[ -f "$REPO/.kit_model" ] || { echo "Run install.sh first."; exit 1; }
. "$REPO/.kit_model"
PASSAGE="${1:-$REPO/data/passages/rust_ordinary.txt}"
cd "$REPO"

echo "== 1/4 Model speed and memory (prompt of ~330 tokens, 120 new tokens)"
"$PY" scripts/llm_probe.py --model "$MODEL_DIR/model.pte" --tokenizer "$MODEL_DIR/tokenizer.json" --chat qwen3 --max-new 120 2>&1 \
  | grep -E "extra kernels|model file|import / load|^prompt|^generated|total wall|peak memory" | sed 's/^/  /'

echo; echo "== 2/4 Full deliverable on: $PASSAGE (summary + quiz + run card)"
if [ -n "${QUICK:-}" ]; then echo "  skipped (QUICK=1)"; else
START=$(date +%s)
PYTHONPATH=src "$PY" -m sakshi run "$PASSAGE" --backend executorch --model "$MODEL_DIR/model.pte" \
  --tokenizer "$MODEL_DIR/tokenizer.json" --out "$REPO/results/pi_run.json" 2>/dev/null
echo "  wall time: $(( $(date +%s) - START )) s"
fi

echo; echo "== 3/4 Offline evidence"
bash scripts/prove_offline.sh "pi-offline-$(date +%H%M)" 2>&1 | tail -3 | sed 's/^/  /'

echo; echo "== 4/4 Board health"
command -v vcgencmd >/dev/null && { vcgencmd measure_temp; vcgencmd get_throttled; } | sed 's/^/  /' || echo "  (vcgencmd not available)"
echo; echo "TEST DONE. Numbers above go into docs/SUBMISSION.md (the Raspberry Pi row). Log: $LOG"
