#!/usr/bin/env python3
"""Does the misconception library find the right topic for each evaluation passage (no model involved)?

  python scripts/check_library_match.py [--show N]

Uses data/passages/eval/passages.jsonl and the hand-written answer key data/passages/eval/expected_topics.json.
Prints top-1 and top-3 topic accuracy, the misses, and (with --show) the matched misconceptions for N passages.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.misconceptions import Library  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=0)
    args = ap.parse_args()
    lib = Library.load()
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "data/passages/eval/passages.jsonl"), encoding="utf-8")]
    expected = json.load(open(os.path.join(ROOT, "data/passages/eval/expected_topics.json"), encoding="utf-8"))
    have = {m["topic_id"] for m in lib.items}
    top1 = top3 = n = 0
    misses = []
    t0 = time.perf_counter()
    for k, r in enumerate(rows):
        exp = [t for t in expected[r["id"]] if t in have]
        if not exp:
            continue  # the library has no entry yet for this passage's topic
        n += 1
        m = lib.match(r["text"])
        got = [t.topic_id for t in m.topics]
        top1 += bool(got) and got[0] in exp
        top3 += any(t in exp for t in got[:3])
        if not got or got[0] not in exp:
            misses.append((r["id"], exp, [(t.topic_id, t.score) for t in m.topics]))
        if k < args.show:
            print(f"\n{r['id']}: topics {[(t.topic_id, t.score) for t in m.topics]}")
            for x in m.misconceptions[:6]:
                print(f"   - {x['statement']}  [{x['id']}]")
    ms = (time.perf_counter() - t0) * 1000 / max(len(rows), 1)
    print(f"\nlibrary: {len(lib.items)} misconceptions in {len(have)} topics")
    print(f"passages scored: {n}   top-1 topic right: {top1}/{n}   right topic in top 3: {top3}/{n}   ({ms:.1f} ms per passage)")
    for pid, exp, got in misses:
        print(f"  MISS {pid}: expected {exp}, got {got}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
