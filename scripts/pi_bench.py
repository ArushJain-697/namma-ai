#!/usr/bin/env python3
"""T18: first true speed and memory numbers on a real passage. Run ON the Pi.

  ~/sakshi-venv/bin/python scripts/pi_bench.py --passage data/passages/rust_ordinary.txt --runs 3 \\
      --backend executorch --model MODEL.pte --tokenizer tokenizer.model --out results/bench.json
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import argparse

from sakshi import bench
from sakshi.backends.factory import add_backend_args, build_backend

p = argparse.ArgumentParser()
p.add_argument("--passage", default="data/passages/rust_ordinary.txt")
p.add_argument("--runs", type=int, default=3)
p.add_argument("--no-warmup", action="store_true")
p.add_argument("--out", default="results/bench.json")
add_backend_args(p)
a = p.parse_args()
text = open(a.passage, encoding="utf-8").read()
b = bench.bench(text, build_backend(a), runs=a.runs, warmup=not a.no_warmup)
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
bench.save(b, a.out)
print(bench.render(b))
print("\nwrote", a.out)
