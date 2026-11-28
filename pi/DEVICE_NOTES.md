# Sakshi on this Pi: notes

## Saved passages (no camera needed)
- Folder: `~/passages/*.txt` (one passage per file, 150-300 words). On the device pick **Saved pages**; new files
  appear without a restart. Included: friction, photosynthesis, salt_march, water_cycle, electric_circuit,
  states_of_matter, democracy_elections, linear_equations, sound_waves.

## Test the real pipeline from SSH (same code the device runs)
    ~/sakshi-venv/bin/python ~/Sakshi/quiz_test.py friction.txt water_cycle.txt --runs 3 --n 3
Prints the summary + questions for every run, says whether runs are identical, and samples CPU %, CPU temperature,
ARM clock and throttle flags once a second while the model runs.

## Randomness (fixed 27 Nov)
- Before: `Model.run()` never passed a temperature (greedy, 0.0) and the engine passed `seed=1`, so the same passage
  gave byte-identical summary, questions and answers every run.
- Now (`~/namma-ai/scripts/backup_quiz.py`): questions / wrong answers sample at `SAKSHI_TEMP` (default 0.4), the
  summary at <= 0.3, the self-check stays at 0.0. Key sentences are chosen with random jitter, the engine seed is None.
- `SAKSHI_TEMP=0` restores the old repeatable behaviour; `SAKSHI_TEMP=0.6` is more varied but writes more bad items.
- Rejected on purpose: a key that is just a letter ("D").

## UI CPU fix
`sakshi.py` spun at 100% of a core under systemd (stdin = /dev/null made `select()` always ready). Fixed: on EOF
it stops watching the keyboard.

Originals are in `~/Sakshi/backup_orig/`.

## Event-driven input (28 Nov)
- Buttons use libgpiod kernel edge interrupts (GPIO 5/6/13, falling edge, 50 ms kernel debounce): a thread blocks
  until a press, so 0 wake-ups when idle. gpiozero/lgpio (the old way) woke ~1,800 times a second; it is now only
  the fallback. Startup log says which one is in use: `journalctl -u sakshi.service | grep buttons`.
- The main loop sleeps on a wake-up pipe; button presses, engine events and finished OCR wake it at once (no more
  up-to-120 ms polling delay). Spinner / camera screens still redraw at ~8 fps.
- Idle UI: 0.2% CPU, ~14 wake-ups/s (was 100% of a core before 27 Nov, then ~1% / ~1,870 wake-ups/s).
- Previous version: `~/Sakshi/backup_orig/sakshi.py.before_irq`.
