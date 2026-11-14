#!/usr/bin/env python3
"""Several days with a pretend student: day 0 adaptive session on a bank, then review days.

  .venv-ml/bin/python scripts/retention_days.py BANK.json [--student learns|stubborn] [--days 1,3,7] [-v]
learns:   holds one belief from GURU's options, understands once the fix is shown.
stubborn: holds that belief AND every belief with the same root belief, never learns from feedback.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bank")
    ap.add_argument("--student", default="learns", choices=["learns", "stubborn"])
    ap.add_argument("--days", default="1,3,7")
    ap.add_argument("--state", default=None)
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    from sakshi.misconceptions import Library
    from sakshi.retention.bank import load_bank
    from sakshi.retention.io import ModelStudent
    from sakshi.retention.review import RelatedBeliefs, ReviewSession
    from sakshi.retention.session import AdaptiveSession
    from sakshi.retention.state import LearnerState

    bank, lib = load_bank(a.bank), Library.load()
    rel = RelatedBeliefs(lib)
    first = next(o.misconception for q in bank.questions.values() if q.id.startswith("g")
                 for o in q.options if o.misconception and o.misconception in lib.by_id)
    holds = {first}
    if a.student == "stubborn":
        holds |= {m for m, r in rel.root.items() if r == rel.root.get(first)}
    student = ModelStudent(holds=holds, echo=True, verbose=a.verbose, learns_after_feedback=a.student == "learns", guess_seed=1)
    print(f"pretend student ({a.student}) holds {first}: \"{lib.by_id[first]['statement']}\""
          + (f" + {len(holds) - 1} beliefs with the same root" if len(holds) > 1 else ""))
    state, t0 = LearnerState(), datetime(2026, 11, 14, 9, tzinfo=timezone.utc)
    print("\n" + "#" * 70 + "\nDAY 0: learning session\n" + "#" * 70)
    AdaptiveSession(bank, state, student, now=t0).run()
    for d in [int(x) for x in a.days.split(",")]:
        print("\n" + "#" * 70 + f"\nDAY {d}: review\n" + "#" * 70)
        ReviewSession(state, lib, student, t0 + timedelta(days=d), related=rel).run()
    if a.state:
        state.save(a.state)


if __name__ == "__main__":
    main()
