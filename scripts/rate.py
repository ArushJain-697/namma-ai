#!/usr/bin/env python3
"""Rating sheets for the go/no-go gates. A person fills in the rating column; 'score' reads it back.

  rate.py stems build --passages data/passages --out results/stem_rating.csv [backend args]   (T21)
  rate.py stems score results/stem_rating.csv
  rate.py summaries build|score ...                                                            (T22)
  rate.py relevance build|score ...                                                            (T23)
  rate.py ablation-c build --run results/run1.json --out ... | score ...                       (T27)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import argparse
import json

from sakshi import rate_tools as rt
from sakshi.backends.factory import add_backend_args, build_backend
from sakshi.pipeline import Run

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="what", required=True)
for what in ("stems", "summaries", "relevance", "ablation-c"):
    s = sub.add_parser(what).add_subparsers(dest="action", required=True)
    b = s.add_parser("build")
    b.add_argument("--passages", default="data/passages")
    b.add_argument("--run")
    b.add_argument("--out", required=True)
    b.add_argument("--n", type=int, default=20)
    add_backend_args(b)
    s.add_parser("score").add_argument("sheet")
a = p.parse_args()

if a.action == "build":
    if a.what == "relevance":
        n = rt.build_relevance_sheet(rt.load_passages(a.passages), a.out)
    elif a.what == "ablation-c":
        if not a.run:
            sys.exit("ablation-c build needs --run")
        n = rt.build_ablation_c_sheet(Run.load(a.run), a.out)
    else:
        passages = rt.load_passages(a.passages)
        backend = build_backend(a)
        n = (rt.build_stem_sheet(backend, passages, a.out, a.n) if a.what == "stems"
             else rt.build_summary_sheet(backend, passages, a.out))
    print(f"wrote {a.out}: {n} rows. Fill in the rating column(s), then run: rate.py {a.what} score {a.out}")
else:
    fn = {"stems": rt.score_stems, "summaries": rt.score_summaries, "relevance": rt.score_relevance,
          "ablation-c": rt.score_ablation_c}[a.what]
    print(json.dumps(fn(a.sheet), indent=2))
