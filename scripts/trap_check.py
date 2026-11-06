#!/usr/bin/env python3
"""T24: which counterfactual facts really trap the baseline (passage IN context)? Dev half only.

  python scripts/trap_check.py --cases data/counterfactual [backend args] [--tries 3]
Writes kept_dev.json. GO/NO-GO for the live evade-then-catch beat: if too few facts trap the model, the beat is
replaced by a prepared ordinary-passage example and we say so.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import argparse
import json

from sakshi.backends.factory import add_backend_args, build_backend
from sakshi.cf_eval import trap_check
from sakshi.counterfactual import load_cases, notes, validate

p = argparse.ArgumentParser()
p.add_argument("--cases", default="data/counterfactual")
p.add_argument("--tries", type=int, default=3)
p.add_argument("--out")
p.add_argument("--allow-short", action="store_true", help="accept passages outside 150-300 words (testing only)")
add_backend_args(p)
a = p.parse_args()

cases = load_cases(a.cases, "dev")
bad = {c.id: validate(c, a.allow_short) for c in cases}
for cid, probs in bad.items():
    for pr in probs:
        print(f"INVALID {cid}: {pr}")
for c in cases:
    for n in notes(c):
        print(f"note {c.id}: {n}")
if any(bad.values()):
    sys.exit(2)
if not cases:
    sys.exit("no dev cases found in " + a.cases)
res = trap_check(cases, build_backend(a), a.tries)
kept = [cid for cid, r in res.items() if r["trap"]]
for cid, r in res.items():
    print(f"{cid:20} {'TRAPS the baseline' if r['trap'] else 'does not trap':20} tries: {', '.join(r['tries'])}")
share = len(kept) / len(cases)
verdict = (f"GO: {len(kept)} of {len(cases)} dev facts trap the baseline; keep the live evade-then-catch beat" if share >= 1 / 3
           else f"NO-GO: only {len(kept)} of {len(cases)} dev facts trap the baseline; replace the live beat with a prepared "
                f"ordinary-passage example and say so")
print("\n" + verdict)
out = a.out or os.path.join(a.cases, "kept_dev.json")
with open(out, "w") as f:
    json.dump({"kept": kept, "n_dev": len(cases), "tries": a.tries, "verdict": verdict,
               "rule": "kept if the targeted baseline (passage in context) followed memory in at least 1 of N tries; dev half only"}, f, indent=2)
print("wrote", out)
