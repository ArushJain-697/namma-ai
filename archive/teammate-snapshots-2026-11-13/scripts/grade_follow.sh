#!/usr/bin/env bash
# Grade rewritten passages as they appear, until the rewrite run ends, then once more. Resumable.
#   nohup bash scripts/grade_follow.sh > results/grade_v2.log 2>&1 &
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
while pgrep -f "make_dataset.py rewrite" >/dev/null; do
  "$PY" scripts/grade_questions.py dataset --workers 2
  sleep 300
done
"$PY" scripts/grade_questions.py dataset --workers 3
echo "grade_follow: finished"
