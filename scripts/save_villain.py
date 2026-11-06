#!/usr/bin/env python3
"""T33: save ONE real baseline failure for the demo's 'villain' beat. Refuses to stage a failure.

  python scripts/save_villain.py --cases data/counterfactual [--case ID] --out demo/villain.json [backend args]
Without --case it tries each case and keeps the first where the baseline really answered from memory.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import argparse

from sakshi.backends.factory import add_backend_args, build_backend
from sakshi.counterfactual import load_cases, validate
from sakshi.villain import NotAVillain, build_villain, render, save

p = argparse.ArgumentParser()
p.add_argument("--cases", default="data/counterfactual")
p.add_argument("--case")
p.add_argument("--out", default="demo/villain.json")
p.add_argument("--allow-short", action="store_true")
add_backend_args(p)
a = p.parse_args()
cases = [c for c in load_cases(a.cases) if not a.case or c.id == a.case]
if not cases:
    sys.exit("no matching cases")
backend = build_backend(a)
for c in cases:
    if validate(c, a.allow_short):
        print(f"skip {c.id}: invalid ({validate(c, a.allow_short)[0]})")
        continue
    try:
        v = build_villain(c, backend, backend, gate_override=a.allow_short)
    except NotAVillain as e:
        print(f"{c.id}: {e}")
        continue
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    save(v, a.out)
    print(render(v))
    print("\nwrote", a.out)
    break
else:
    sys.exit("no case produced a real baseline failure; the live trap beat is NO-GO (see scripts/trap_check.py)")
