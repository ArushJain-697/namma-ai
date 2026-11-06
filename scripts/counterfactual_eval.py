#!/usr/bin/env python3
"""T26: score the Counterfactual Passage Test (A-D) and write metrics for the proof card.

  python scripts/counterfactual_eval.py --cases data/counterfactual [--kept data/counterfactual/kept_dev.json] [backend args]
The dev half is filtered to the facts in --kept (if given); the held-out half is NEVER filtered.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import argparse
import json

from sakshi.backends.factory import add_backend_args, build_backend
from sakshi.cf_eval import evaluate, save, write_d_sheet
from sakshi.counterfactual import load_cases, validate
from sakshi.proof import render_card

p = argparse.ArgumentParser()
p.add_argument("--cases", default="data/counterfactual")
p.add_argument("--kept")
p.add_argument("--out", default="results/cf_metrics.json")
p.add_argument("--d-sheet", default="results/cf_d_sheet.csv")
p.add_argument("--allow-short", action="store_true", help="accept passages outside 150-300 words (testing only)")
add_backend_args(p)
a = p.parse_args()

cases = load_cases(a.cases)
probs = [(c.id, x) for c in cases for x in validate(c, a.allow_short)]
for cid, x in probs:
    print(f"INVALID {cid}: {x}")
if probs:
    sys.exit(2)
if not cases:
    sys.exit("no cases found in " + a.cases)
kept = set(json.load(open(a.kept))["kept"]) if a.kept else None
backend = build_backend(a)
m = evaluate(cases, backend, backend, kept_dev=kept, gate_override=a.allow_short)
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
save(m, a.out)
n = write_d_sheet(m, a.d_sheet)
print(render_card(m))
print(f"\nwrote {a.out} and {a.d_sheet} ({n} stems to rate for D)")
