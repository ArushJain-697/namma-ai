#!/usr/bin/env python3
"""Calibrate the off-syllabus thresholds (sakshi.diagnostic GENERIC_COS, GENERIC_KW).

  .venv-ml/bin/python scripts/calibrate_fallback.py

Scores the 40 on-syllabus eval passages and data/passages/offsyllabus.jsonl on keyword and meaning match, and
prints the thresholds that separate them (it never edits code: copy the suggestion into diagnostic.py).
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.mapper import Mapper, TorchEncoders  # noqa: E402
from sakshi.misconceptions import Library  # noqa: E402


def main():
    lib = Library.load()
    mp = Mapper(lib, TorchEncoders(nli_model=None))
    on = [json.loads(l)["text"] for l in open(os.path.join(ROOT, "data/passages/eval/passages.jsonl"))]
    off = [json.loads(l)["text"] for l in open(os.path.join(ROOT, "data/passages/offsyllabus.jsonl"))]

    def strength(p):
        mp.topics(p)
        return mp.last_strength
    S_on, S_off = [strength(p) for p in on], [strength(p) for p in off]
    for name, S in (("on-syllabus", S_on), ("off-syllabus", S_off)):
        cos, kw = sorted(s["cos"] for s in S), sorted(s["kw"] for s in S)
        print(f"{name:13} cos min/median/max {cos[0]:.3f} {cos[len(cos) // 2]:.3f} {cos[-1]:.3f}   "
              f"kw min/median/max {kw[0]:.1f} {kw[len(kw) // 2]:.1f} {kw[-1]:.1f}")
    best = None
    for c in [x / 100 for x in range(40, 90)]:
        for k in range(0, 200, 5):
            fp = sum(s["cos"] < c and s["kw"] < k for s in S_on)      # on-syllabus wrongly sent to generic
            tp = sum(s["cos"] < c and s["kw"] < k for s in S_off)     # off-syllabus correctly caught
            score = tp - 3 * fp                                         # a false fallback costs more than a miss
            if best is None or score > best[0]:
                best = (score, c, k, tp, fp)
    _, c, k, tp, fp = best
    print(f"\nsuggested GENERIC_COS = {c:.2f}, GENERIC_KW = {k}: catches {tp}/{len(off)} off-syllabus, "
          f"wrongly flags {fp}/{len(on)} on-syllabus")


if __name__ == "__main__":
    main()
