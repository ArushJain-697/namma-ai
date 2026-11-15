#!/usr/bin/env python3
"""Job 6: measure quiz quality on the 200 test passages (the number we show judges).

  # a model on the device pipeline (plain Qwen3-0.6B, or the fine-tuned one):
  PYTHONPATH=src .venv-export/bin/python scripts/eval_quiz.py generate --label base \\
      --backend executorch --model models/qwen3-0.6b-8da4w/model.pte --tokenizer models/qwen3-0.6b-8da4w-portable/tokenizer.json
  # Opus's own questions on the same passages (the ceiling):
  python scripts/eval_quiz.py ceiling [--limit 40]
  # grade every label's questions with the rubric grader (Sonnet), then write results/question_quality.md:
  python scripts/eval_quiz.py grade
  python scripts/eval_quiz.py report

Per label it writes results/quiz_eval/<label>/items.jsonl (one line per passage: questions, attempts, timings) and,
after `grade`, grades.jsonl. Reruns skip passages already done. Test passages are only READ, never changed.
Pi time per quiz is estimated from the tokens each quiz really used, at the "likely" Pi 5 speed in
QUESTION_QUALITY_HANDOFF.md (read 60 tok/s, write 20 tok/s), until the Pi itself is measured.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import random
import sys
import threading
import time
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = os.path.join(ROOT, "results", "quiz_eval")
PASSAGES = os.path.join(ROOT, "data", "dataset", "test_passages.jsonl")
N_Q = 4
PI_READ, PI_WRITE = 60.0, 20.0


def load_passages(limit=None):
    return [json.loads(l) for l in open(PASSAGES, encoding="utf-8")][:limit]


def done_ids(path):
    if not os.path.exists(path):
        return set()
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8")}


def cmd_generate(a) -> int:
    from sakshi.backends.factory import build_backend
    from sakshi.diagnostic import generate_quiz
    from sakshi.misconceptions import Library
    out_dir = os.path.join(OUT, a.label)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "items.jsonl")
    seen = done_ids(path)
    rows = [p for p in load_passages(a.limit) if p["id"] not in seen]
    backend = build_backend(a)
    lib = None if a.no_library else Library.load()
    print(f"{len(rows)} passages to run for {a.label} ({backend.info().get('name')})", flush=True)
    for k, p in enumerate(rows, 1):
        t0 = time.perf_counter()
        bank, rep = generate_quiz(p["text"], backend, lib, n_questions=N_Q, seed=k)
        rec = {"id": p["id"], "label": a.label, "model": backend.info().get("name"), "split_reason": p.get("split_reason"),
               "passage": p["text"], "summary": bank["summary"], "wall_s": round(time.perf_counter() - t0, 2),
               "calls": rep["calls"], "prompt_tokens": rep["prompt_tokens"], "new_tokens": rep["new_tokens"],
               "slots_tried": len(rep["items"]),
               "questions": [{"q": q["stem"], "options": [next(o["text"] for o in q["options"] if o["correct"])]
                              + [o["text"] for o in q["options"] if not o["correct"]],
                              "explain": q["explanation"], "evidence": q["evidence"]} for q in bank["questions"]],
               "rejected": [r for it in rep["items"] for att in it["attempts"] if not att["ok"] for r in att["reasons"]]}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[{k}/{len(rows)}] {p['id']}: {len(rec['questions'])} questions, {rec['wall_s']}s", flush=True)
    return 0


def cmd_ceiling(a) -> int:
    """Opus writes questions for the test passages with the same teacher prompt used for training data."""
    import make_dataset as md
    from build_misconception_library import claude_generate, loads_lenient
    from sakshi.diagnostic import check_quiz_item
    from sakshi.misconceptions import Library
    out_dir = os.path.join(OUT, "opus")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "items.jsonl")
    seen = done_ids(path)
    rows = [p for p in load_passages(a.limit) if p["id"] not in seen]
    lib = Library.load()
    prefix = md.REWRITE_PREFIX.format(rubric=md._rubric_text(), gold=md._gold_text())
    lock = threading.Lock()
    print(f"{len(rows)} test passages for the Opus ceiling", flush=True)

    def one(p):
        m = lib.match(p["text"], n_misconceptions=12).misconceptions
        prompt = prefix + md.REWRITE_TASK.format(grade=p.get("grade") or 8, topic=p.get("topic_id") or "general reading",
                                                 n=N_Q, passage=p["text"],
                                                 menu="\n".join(f"{x['id']}: {x['statement']}" for x in m))
        t0 = time.perf_counter()
        text, _ = claude_generate(prompt, a.model)
        items = loads_lenient(text).get("items", []) or []
        qs, rejected = [], []
        for it in items[:N_Q]:
            item = {"q": str(it.get("q", "")), "options": [str(o) for o in it.get("options", [])], "answer": 0,
                    "explain": str(it.get("explain", ""))}
            chk = check_quiz_item(item, p["text"], str(it.get("evidence", "")))
            if chk.ok:
                qs.append({**{k: item[k] for k in ("q", "options", "explain")}, "evidence": it.get("evidence", "")})
            else:
                rejected += chk.reasons
        rec = {"id": p["id"], "label": "opus", "model": a.model, "split_reason": p.get("split_reason"), "passage": p["text"],
               "summary": "", "wall_s": round(time.perf_counter() - t0, 2), "calls": 1, "prompt_tokens": 0, "new_tokens": 0,
               "slots_tried": N_Q, "questions": qs, "rejected": rejected}
        with lock, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return f"{p['id']}: {len(qs)} questions"

    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        for fut in cf.as_completed([pool.submit(one, p) for p in rows]):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                print("FAILED:", str(e)[:160], flush=True)
                if "quota" in str(e).lower():
                    break
    return 0


def cmd_grade(a) -> int:
    from grade_questions import grade_passage
    labels = [a.label] if a.label else sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []
    for label in labels:
        ipath, gpath = os.path.join(OUT, label, "items.jsonl"), os.path.join(OUT, label, "grades.jsonl")
        if not os.path.exists(ipath):
            continue
        seen = done_ids(gpath)
        recs = [json.loads(l) for l in open(ipath, encoding="utf-8")]
        recs = [r for r in recs if r["id"] not in seen and r["questions"]]
        print(f"{label}: {len(recs)} passages to grade", flush=True)
        lock = threading.Lock()

        def one(r):
            g = grade_passage(r["passage"], r["questions"], a.model)
            with lock, open(gpath, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": r["id"], "grades": g}, ensure_ascii=False) + "\n")
            return f"{label} {r['id']}: {[x['score'] for x in g]}"

        with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
            for fut in cf.as_completed([pool.submit(one, r) for r in recs]):
                try:
                    print(fut.result(), flush=True)
                except Exception as e:  # noqa: BLE001
                    print("FAILED:", str(e)[:160], flush=True)
    return 0


def summarise(label: str) -> dict | None:
    ipath, gpath = os.path.join(OUT, label, "items.jsonl"), os.path.join(OUT, label, "grades.jsonl")
    if not os.path.exists(ipath):
        return None
    recs = [json.loads(l) for l in open(ipath, encoding="utf-8")]
    grades = {json.loads(l)["id"]: json.loads(l)["grades"] for l in open(gpath, encoding="utf-8")} if os.path.exists(gpath) else {}
    n = len(recs)
    slots = n * N_Q
    valid = sum(len(r["questions"]) for r in recs)
    gs = [g for r in recs for g in grades.get(r["id"], [])]
    good = [g for g in gs if g["hard_pass"] and g["score"] >= 4]
    pi = [r["prompt_tokens"] / PI_READ + r["new_tokens"] / PI_WRITE for r in recs if r["prompt_tokens"]]
    return {"label": label, "model": recs[0]["model"] if recs else "", "passages": n, "slots": slots, "valid": valid,
            "valid_pct": round(100 * valid / slots, 1) if slots else None,
            "passages_with_3plus": sum(len(r["questions"]) >= 3 for r in recs),
            "graded": len(gs), "mean_score": round(sum(g["score"] for g in gs) / len(gs), 2) if gs else None,
            "good": len(good), "good_pct_of_graded": round(100 * len(good) / len(gs), 1) if gs else None,
            "good_pct_of_slots": round(100 * len(good) / slots, 1) if slots and gs else None,
            "mac_s_per_quiz": round(sorted(r["wall_s"] for r in recs)[n // 2], 1) if n else None,
            "pi_s_per_quiz_est": round(sorted(pi)[len(pi) // 2], 1) if pi else None,
            "top_rejections": Counter(x.split("(")[0].strip() for r in recs for x in r["rejected"]).most_common(5),
            "recs": recs, "grades": grades}


def cmd_report(a) -> int:
    labels = sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []
    sums = [s for s in (summarise(l) for l in labels) if s]
    lines = ["# Quiz question quality (job 6)", "",
             f"Test set: `data/dataset/test_passages.jsonl` (200 passages never used for training). {N_Q} question slots per "
             "passage. Grader: the rubric in `docs/QUESTION_RUBRIC.md`, Claude Sonnet 5.5, blind to which model wrote the "
             "question. 'Good' = all hard rules pass and score >= 4.",
             "Pi seconds are an ESTIMATE from each quiz's real token counts at the 'likely' Pi 5 speed (read 60, write 20 "
             "tokens/s) until the Pi is measured. The Opus row is the ceiling (one call, not the device pipeline).", "",
             "| Model | Passages | Valid question slots | Passages with >= 3 | Graded | Mean score | Good (of graded) | Good (of all slots) | Mac s/quiz | Pi s/quiz (est.) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in sums:
        lines.append(f"| {s['label']} ({s['model']}) | {s['passages']} | {s['valid']}/{s['slots']} ({s['valid_pct']}%) | "
                     f"{s['passages_with_3plus']} | {s['graded']} | {s['mean_score']} | {s['good']} ({s['good_pct_of_graded']}%) | "
                     f"{s['good_pct_of_slots']}% | {s['mac_s_per_quiz']} | {s['pi_s_per_quiz_est']} |")
    for s in sums:
        lines += ["", f"## {s['label']}: 10 random questions", "",
                  "Most common code-check rejections: " + (", ".join(f"{r} ({c})" for r, c in s["top_rejections"]) or "none"), ""]
        pool = [(r, i, q) for r in s["recs"] for i, q in enumerate(r["questions"])]
        for r, i, q in random.Random(5).sample(pool, min(10, len(pool))):
            g = (s["grades"].get(r["id"]) or [{}] * (i + 1))[i] if s["grades"].get(r["id"]) else {}
            lines.append(f"- **{q['q']}** (`{r['id']}`)" + (f" — score {g.get('score')}, {g.get('note', '')}" if g else ""))
            lines.append(f"  - ✅ {q['options'][0]}")
            lines += [f"  - ❌ {o}" for o in q["options"][1:]]
    path = os.path.join(ROOT, "results", "question_quality.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:8 + len(sums)]))
    print("wrote", path)
    return 0


def main() -> int:
    from sakshi.backends.factory import add_backend_args
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--label", required=True)
    g.add_argument("--limit", type=int)
    g.add_argument("--no-library", action="store_true")
    add_backend_args(g)
    c = sub.add_parser("ceiling")
    c.add_argument("--limit", type=int)
    c.add_argument("--model", default="claude-opus-5-5")
    c.add_argument("--workers", type=int, default=2)
    gr = sub.add_parser("grade")
    gr.add_argument("--label")
    gr.add_argument("--model", default="claude-sonnet-5-5")
    gr.add_argument("--workers", type=int, default=2)
    sub.add_parser("report")
    a = ap.parse_args()
    return {"generate": cmd_generate, "ceiling": cmd_ceiling, "grade": cmd_grade, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
