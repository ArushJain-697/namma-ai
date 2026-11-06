#!/usr/bin/env bash
# Prove the MODEL PROCESS has no network, and save the evidence. Run ON the Pi (or anywhere with `unshare`):
#   bash scripts/prove_isolation.sh [tag] [-- backend args for `sakshi resident`]
# Example with the real model:
#   bash scripts/prove_isolation.sh pi-iso -- --backend executorch --model M.pte --tokenizer T.model
# It starts the resident model process (1) with NO isolation as a CONTROL and (2) inside an empty network
# namespace, asks each what network it can see, and saves both answers. The control must say "not isolated",
# otherwise the isolated result proves nothing. Needs root or user namespaces (`sudo` is used if not root).
set -u
cd "$(dirname "$0")/.."
TAG="${1:-isolation-$(date +%Y%m%d-%H%M%S)}"; shift || true
[ "${1:-}" = "--" ] && shift
BACKEND_ARGS=("$@")
OUT="results/$TAG"; mkdir -p "$OUT"
PY="${PYTHON:-python3}"
D="$(mktemp -d /tmp/sakshi-iso.XXXXXX)"; trap 'kill $(jobs -p) 2>/dev/null; rm -rf "$D"' EXIT
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
SUDO=""; [ "$(id -u)" != 0 ] && SUDO="sudo"

wait_ready() { for _ in $(seq 1 600); do [ -S "$1" ] && return 0; sleep 0.1; done; return 1; }

run_case() {  # $1=name  $2=socket  rest=command prefix
  local name="$1" sock="$2"; shift 2
  "$@" "$PY" -m sakshi resident --socket "$sock" "${BACKEND_ARGS[@]}" > "$D/$name.log" 2>&1 &
  if ! wait_ready "$sock"; then echo "$name: resident process did not start"; cat "$D/$name.log"; return 1; fi
  "$PY" -m sakshi probe --socket "$sock" > "$OUT/probe_$name.json" 2>"$D/$name.err" || { cat "$D/$name.err"; return 1; }
  echo "--- $name"; cat "$OUT/probe_$name.json"
}

{
  echo "# model-process isolation evidence $(date -Is) on $(uname -n)"
  run_case control "$D/control.sock" env            || exit 3
  run_case isolated "$D/isolated.sock" $SUDO unshare -n || { echo "unshare -n failed (root or user namespaces needed)"; exit 3; }
} 2>&1 | tee "$OUT/isolation_evidence.txt"

CTRL=$("$PY" -c "import json;print(json.load(open('$OUT/probe_control.json'))['isolated'])")
ISO=$("$PY" -c "import json;print(json.load(open('$OUT/probe_isolated.json'))['isolated'])")
echo
if [ "$CTRL" = "False" ] && [ "$ISO" = "True" ]; then
  echo "RESULT: the model process in the namespace has no network (control did NOT). Evidence in $OUT/"
else
  echo "RESULT: NOT PROVEN (control isolated=$CTRL, namespaced isolated=$ISO). Do not claim isolation."; exit 1
fi
