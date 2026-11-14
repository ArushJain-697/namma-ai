#!/usr/bin/env python3
"""End to end on the Mac: GURU quiz (study_json.py RESULT) -> misconception tags -> bank -> adaptive session
(Bayes diagnosis, BKT, graph walk-down, FSRS) with a pretend student, then the revision plan.

  .venv-ml/bin/python scripts/retention_demo.py PASSAGE.txt RESULT.txt [--student wrong|right|human]
RESULT.txt = the "RESULT {json}" line study_json.py printed (run it in .venv-export first).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("passage")
    ap.add_argument("result")
    ap.add_argument("--student", default="wrong", choices=["wrong", "right", "human"])
    ap.add_argument("--save", default=None, help="write the bank JSON here")
    a = ap.parse_args()
    from sakshi.link import build_bank
    from sakshi.mapper import Mapper, TorchEncoders
    from sakshi.misconceptions import Library
    from sakshi.retention.bank import bank_from_dict
    from sakshi.retention.fsrs_sched import make_scheduler
    from sakshi.retention.io import ModelStudent, TerminalIO
    from sakshi.retention.ranker import revision_plan
    from sakshi.retention.session import AdaptiveSession
    from sakshi.retention.state import LearnerState

    line = next(l for l in open(a.result) if l.startswith("RESULT "))
    res = json.loads(line[7:])
    passage = Path(a.passage).read_text().strip()
    mp = Mapper(Library.load(), TorchEncoders())
    d, log = build_bank(mp, passage, res["summary"], res["questions"], title=Path(a.passage).stem)
    print("== option -> misconception links (retrieve + NLI rerank, abstain below cos 0.76)")
    for r in log:
        print(f"  Q{r['q']} '{r['option']}' -> {r['misconception'] or '(abstain)'}  [{r['cos']}]")
    if a.save:
        json.dump(d, open(a.save, "w"), indent=1)
    bank = bank_from_dict(d)
    print(f"== bank: {len(bank.concepts)} concepts, {len(bank.questions)} questions "
          f"({sum(q.id.startswith('g') for q in bank.questions.values())} from GURU)")
    tagged = [o.misconception for q in bank.questions.values() if q.id.startswith("g") for o in q.options if o.misconception]
    if a.student == "human":
        io = TerminalIO()
    elif a.student == "right":
        io = ModelStudent(knows=set(bank.concepts), echo=True)
    else:  # holds the first misconception GURU's options were linked to
        io = ModelStudent(holds=set(tagged[:1]), echo=True)
        print(f"== pretend student holds: {tagged[:1]}")
    state, now = LearnerState(), datetime.now(timezone.utc)
    r = AdaptiveSession(bank, state, io, now=now).run()
    print("\n== result")
    print("asked:", r.asked)
    print("FSRS outcomes:", r.outcomes)
    print("detected:", r.detected, "suspected:", r.suspected)
    print("BKT P(learned):", {c: round(s.p_mastery, 2) for c, s in state.concepts.items()})
    names = {c.id: c.name for c in bank.concepts.values()}
    for days in (0, 3, 10):
        plan = revision_plan(state, names, make_scheduler(), now + timedelta(days=days))
        print(f"-- revision plan in {days} days:")
        for p in plan[:4]:
            print("  ", p)


if __name__ == "__main__":
    main()
