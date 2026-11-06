#!/usr/bin/env bash
# Demo / rehearsal runner. See docs/DEMO.md for the 3:00 script and the failure runbook.
#   REHEARSAL (stub model, every number SIMULATED):   bash scripts/demo.sh
#   REAL, on the Pi:
#     PASSAGE=organiser.txt BACKEND_ARGS="--backend executorch --model M.pte --tokenizer T.model" bash scripts/demo.sh
# Optional: EDIT_SENTENCE=10 EDIT_TEXT='In 1887, a town ...'   NONINTERACTIVE=1 (no pauses, scripted student)
set -u
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"; export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
PASSAGE="${PASSAGE:-data/passages/rust_ordinary.txt}"
RUN="${RUN:-results/demo_run.json}"; mkdir -p results
BACKEND_ARGS="${BACKEND_ARGS:-}"
pause() { [ -n "${NONINTERACTIVE:-}" ] || read -rp $'\n[Enter] ' _; }
step() { printf '\n\n=== %s\n' "$1"; }

if [ -z "$BACKEND_ARGS" ]; then
  echo "*** REHEARSAL: stub model. Everything below is SIMULATED and must not be shown as a result. ***"
fi

step "1/6  It is offline"
bash scripts/prove_offline.sh "demo-$(date +%H%M%S)" || echo "(not offline here: unplug Ethernet before the real demo)"
pause

step "2/6  Passage in, summary and questions out, run card at the end"
# shellcheck disable=SC2086
$PY -m sakshi prepare "$PASSAGE" --out "$RUN" $BACKEND_ARGS || { echo "prepare failed: fall back to a SAVED RUN (docs/DEMO.md)"; exit 1; }
pause

step "3/6  The villain: a quiz generator answering from the model's memory"
if [ -f demo/villain.json ]; then $PY -m sakshi villain demo/villain.json
else echo "(no saved villain yet: run scripts/save_villain.py once counterfactual cases exist)"; fi
pause

step "4/6  The student (the judge plays them; get one wrong on purpose)"
if [ -n "${NONINTERACTIVE:-}" ]; then yes zzz | head -40 | $PY -m sakshi study "$RUN"; else $PY -m sakshi study "$RUN"; fi
pause

step "5/6  A judge plants the trap: edit one sentence that has a question"
$PY -m sakshi edit "$RUN" --list
if [ -n "${EDIT_SENTENCE:-}" ] && [ -n "${EDIT_TEXT:-}" ]; then
  # shellcheck disable=SC2086
  $PY -m sakshi edit "$RUN" --sentence "$EDIT_SENTENCE" --text "$EDIT_TEXT" --out "${RUN%.json}_edited.json" $BACKEND_ARGS
else echo "(set EDIT_SENTENCE and EDIT_TEXT to run the edit; or:  python -m sakshi edit RUN --sentence N --text '...')"; fi
pause

step "6/6  Proof card (caveat first; numbers come from a metrics file)"
if [ -f results/cf_metrics.json ]; then $PY scripts/proof_card.py --cf results/cf_metrics.json --run "$RUN"
else echo "Counterfactual Passage Test: not measured"; fi
