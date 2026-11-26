#!/usr/bin/env bash
# Start Sakshi on the device: the screen + three buttons (UI, ~/venv: display, GPIO, camera, OCR), which starts
# the engine itself (~/sakshi-venv: GURU-0.6B on ExecuTorch + misconception graph + Bayes/BKT/FSRS).
# Put the organiser's passage in ~/passage.txt for "Saved page". Engine log: /tmp/sakshi_engine.log
# OCR: PP-OCRv6 + PaddleOCR-VL for unclear photos when pi/setup_ocr.sh has installed it (log: /tmp/sakshi_vl.log).
# SAKSHI_OCR=v6s (default)|v6m|v5m picks the line model; SAKSHI_OCR_VL=auto turns on the PaddleOCR-VL re-read (off: too slow on a CPU-only Pi).
if [ -z "${SAKSHI_LLAMA_SERVER:-}" ] && [ -x "$HOME/llama.cpp/build/bin/llama-server" ]; then
  export SAKSHI_LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
fi
cd ~/Sakshi && exec ~/venv/bin/python sakshi.py "$@"
