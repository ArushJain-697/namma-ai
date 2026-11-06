#!/usr/bin/env python3
"""T28: print the proof card from metrics files. Nothing is typed by hand; missing numbers say 'not measured'."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import argparse

from sakshi.proof import render_files

p = argparse.ArgumentParser()
p.add_argument("--cf", default="results/cf_metrics.json")
p.add_argument("--run")
p.add_argument("--bench")
a = p.parse_args()
print(render_files(a.cf, a.run, a.bench))
