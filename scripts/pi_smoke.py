#!/usr/bin/env python3
"""Run ON the Pi:  python scripts/pi_smoke.py --model MODEL.pte --tokenizer tokenizer.model

Loads the model, settles the BOS and special-token questions with real token counts,
generates twice, and prints one block to paste back. Needs the venv from scripts/pi_setup.sh.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from sakshi.smoke import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
