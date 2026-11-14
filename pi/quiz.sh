#!/usr/bin/env bash
# Sakshi: offline summary + quiz on the Raspberry Pi (ExecuTorch, no cloud).
#   bash ~/pi-kit/quiz.sh passage.txt        # passage from a file
#   bash ~/pi-kit/quiz.sh                    # paste the passage, then press Ctrl-D on a new line
#   EIGHT_BIT=1 bash ~/pi-kit/quiz.sh f.txt  # 8-bit GURU (better quality, slower)
# Prints: SUMMARY, QUIZ (each answer with the passage sentence that proves it), RUN CARD (model, size, memory, time).
set -u
PY="$HOME/sakshi-venv/bin/python"
REPO="$HOME/namma-ai"
[ -x "$PY" ] || { echo "Run ~/pi-kit/install.sh first."; exit 1; }
QUIZ_MODEL="$REPO/models/guru-0.6b-2job"
[ -n "${EIGHT_BIT:-}" ] && QUIZ_MODEL="$REPO/models/guru-0.6b-2job-8bit"
SUMMARY_MODEL="$REPO/models/qwen3-0.6b-fast"
grep -q -m1 asimddp /proc/cpuinfo || SUMMARY_MODEL="$REPO/models/qwen3-0.6b-portable"

if [ $# -ge 1 ]; then
  PASSAGE_FILE="$1"
else
  PASSAGE_FILE="$(mktemp /tmp/passage.XXXX.txt)"
  echo "Paste the passage (150-300 words), then press Ctrl-D on a new line:"
  cat > "$PASSAGE_FILE"
fi
WORDS=$(wc -w < "$PASSAGE_FILE")
echo; echo "Passage: $WORDS words. Working offline on this Raspberry Pi... (about a minute)"; echo
cd "$REPO" && PYTHONPATH=src "$PY" scripts/backup_quiz.py demo "$PASSAGE_FILE" --quiz 2job \
  --model "$QUIZ_MODEL" --summary-model "$SUMMARY_MODEL" 2>/dev/null
