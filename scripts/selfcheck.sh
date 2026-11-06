#!/usr/bin/env bash
# Run every test and the stub demo. Green here means the pipeline logic is sound; it says
# NOTHING about the real model, which only runs on the Pi (see scripts/pi_smoke.py).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

if ! "$PY" -c "import pytest" 2>/dev/null; then
  echo "pytest is missing. Install it with:  $PY -m pip install pytest" >&2
  exit 2
fi

echo "== unit tests"
"$PY" -m pytest -q

echo "== syntax of every script"
for f in scripts/*.sh; do bash -n "$f"; done
for f in scripts/*.py; do "$PY" -m py_compile "$f"; done
echo "ok"

echo "== stub demo (no model involved)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
PYTHONPATH=src "$PY" -m sakshi check data/passages/rust_ordinary.txt
PYTHONPATH=src "$PY" -m sakshi prepare data/passages/rust_ordinary.txt --out "$tmp/run.json" --metrics "$tmp/metrics.json" | tail -6
PYTHONPATH=src "$PY" -m sakshi report "$tmp/run.json" | head -12
echo
echo "selfcheck: OK (stub only; nothing here has touched a real model)"
