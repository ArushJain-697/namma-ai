#!/usr/bin/env bash
# Start Sakshi on the device: the screen + three buttons (UI, ~/venv: display, GPIO, camera, OCR), which starts
# the engine itself (~/sakshi-venv: GURU-0.6B on ExecuTorch + misconception graph + Bayes/BKT/FSRS).
# Put the organiser's passage in ~/passage.txt for "Saved page". Engine log: /tmp/sakshi_engine.log
cd ~/Sakshi && exec ~/venv/bin/python sakshi.py "$@"
