#!/usr/bin/env python3
"""Grade quiz questions against docs/QUESTION_RUBRIC.md with a Claude grader (Sonnet 5.5 by default, to save Opus).

  python scripts/grade_questions.py dataset [--workers 3] [--model claude-sonnet-5-5]
      grades every rewritten training passage in data/dataset_v2/raw/ -> data/dataset_v2/grades.jsonl
      (one line per question, key "<file>#<index>"; reruns skip passages already graded; stops cleanly on a
      usage limit, rerun later to resume). Then: python scripts/make_dataset.py build-v2

`grade_passage()` is also used by scripts/eval_quiz.py (job 6), so training data and the final numbers are judged by
the same rubric and the same grader. Needs the Claude CLI logged in (set CLAUDE_BIN if `claude` is not on PATH).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
import threading

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DD2 = os.path.join(ROOT, "data", "dataset_v2")
HARD = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")

GRADER = """You are a strict, independent examiner checking multiple-choice questions written for Class 6-10 students
in India. Judge each question ONLY by the passage and the rubric below. You did not write these questions.

{rubric}

For each question, the option marked [CORRECT] is the intended answer. Check it yourself: is it really proved by the
passage, and is no other option also correct or defensible? If either fails, H3 fails and the score is at most 2.
For H1: a plain recall question passes only if it is the only plain recall question in this set.

PASSAGE:
{passage}

QUESTIONS:
{items}

Return only JSON: {{"grades": [{{"k": 0, "H1": true, "H2": true, "H3": true, "H4": true, "H5": true, "H6": true,
"H7": true, "H8": true, "score": 4, "note": "one short sentence: the main weakness, or 'none'"}}]}}
with exactly one entry per question, in order, k starting at 0.
"""


def rubric_text() -> str:
    t = open(os.path.join(ROOT, "docs", "QUESTION_RUBRIC.md"), encoding="utf-8").read()
    start, end = t.find("## Hard rules"), t.find("## Good vs bad")
    return t[start:end].strip() if start >= 0 and end > start else t


def format_items(items: list[dict]) -> str:
    """items: {"q", "options" (correct first), "explain", "evidence"?}. Options are shown in a fixed shuffled order so
    the grader cannot rely on position."""
    out = []
    for k, it in enumerate(items):
        opts = list(it["options"])
        order = [1, 0, 3, 2] if k % 2 else [2, 3, 0, 1]
        lines = [f"Q{k} ({k}). {it['q']}"]
        for letter, i in zip("ABCD", order[: len(opts)] if len(opts) == 4 else range(len(opts))):
            lines.append(f"   {letter}) {opts[i]}" + ("   [CORRECT]" if i == 0 else ""))
        lines.append(f"   Explanation shown to the student: {it.get('explain', '')}")
        out.append("\n".join(lines))
    return "\n\n".join(out)


def grade_passage(passage: str, items: list[dict], model: str = "claude-sonnet-5-5") -> list[dict]:
    """One grader call for all questions of one passage. Returns one dict per item:
    {"k", "H1".."H8", "hard_pass", "score", "note"}. Raises on a usage limit (message contains 'quota')."""
    from build_misconception_library import claude_generate, loads_lenient
    if not items:
        return []
    prompt = GRADER.format(rubric=rubric_text(), passage=passage, items=format_items(items))
    text, _ = claude_generate(prompt, model)
    data = loads_lenient(text)
    grades = {int(g.get("k", -1)): g for g in data.get("grades", []) if isinstance(g, dict)}
    out = []
    for k in range(len(items)):
        g = grades.get(k, {})
        hard = {h: bool(g.get(h)) for h in HARD}
        try:
            score = int(g.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        out.append({"k": k, **hard, "hard_pass": bool(g) and all(hard.values()), "score": score,
                    "note": str(g.get("note", "missing from grader output" if not g else ""))[:300]})
    return out


def cmd_dataset(args) -> int:
    raw_dir = os.path.join(DD2, "raw")
    gpath = os.path.join(DD2, "grades.jsonl")
    done = set()
    if os.path.exists(gpath):
        for line in open(gpath, encoding="utf-8"):
            done.add(json.loads(line)["key"].split("#")[0])
    files = sorted(f for f in os.listdir(raw_dir) if f.endswith(".json"))
    todo = [f for f in files if f not in done][: args.limit]
    print(f"{len(todo)} of {len(files)} rewritten passages to grade with {args.model}", flush=True)
    lock, stop = threading.Lock(), threading.Event()

    def one(f):
        if stop.is_set():
            return f"{f:<48} skipped (stopping)"
        rec = json.load(open(os.path.join(raw_dir, f), encoding="utf-8"))
        items = [{"q": str(it.get("q", "")), "options": [str(o) for o in it.get("options", [])],
                  "explain": str(it.get("explain", ""))} for it in rec["response"].get("items", []) or []]
        try:
            grades = grade_passage(rec["passage"], items, args.model)
        except Exception as e:  # noqa: BLE001
            if "quota" in str(e).lower():
                stop.set()
            raise
        with lock, open(gpath, "a", encoding="utf-8") as fh:
            for g in grades:
                fh.write(json.dumps({"key": f"{f}#{g['k']}", "grader": args.model, **g}, ensure_ascii=False) + "\n")
        return f"{f:<48} scores {[g['score'] for g in grades]} hard {[int(g['hard_pass']) for g in grades]}"

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(one, f): f for f in todo}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"{futs[fut]:<48} FAILED: {str(e)[:160]}", flush=True)
    print(f"done; {failed} failed" + ("; STOPPED on a usage limit, rerun later to resume" if stop.is_set() else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dataset")
    d.add_argument("--model", default="claude-sonnet-5-5")
    d.add_argument("--workers", type=int, default=3)
    d.add_argument("--limit", type=int)
    args = ap.parse_args()
    return cmd_dataset(args)


if __name__ == "__main__":
    sys.exit(main())
