#!/usr/bin/env python3
"""Run many passages through the pipeline with one loaded model, and write a report a person can read.

  python scripts/batch_eval.py --passages data/passages/eval/passages.jsonl --out results/eval_qwen3 \
      --backend executorch --model model.pte --tokenizer tokenizer.json

--passages takes a .jsonl file (one {"id", "text", ...} per line) or a folder of .txt files (the file name is the id).
Writes to --out:
  report.md     every passage: summary, EVERY question with all options (shown and held back), drafts and reasons
  rating.csv    one row per question a student would see, with an empty "rating" column (good / ok / bad)
  totals.json   the numbers in the report header
  runs/ID.json  the full saved run for each passage
Question quality here does not depend on the device: the same .pte gives the same questions on a Mac or a Pi,
so run this on the fastest machine and measure speed separately on the board.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from sakshi.backends.factory import add_backend_args, build_backend  # noqa: E402
from sakshi.metrics import token_stats  # noqa: E402
from sakshi.pipeline import prepare, visible_items  # noqa: E402


def load_passages(path: str) -> list[dict]:
    if os.path.isdir(path):
        rows = []
        for f in sorted(glob.glob(os.path.join(path, "*.txt"))):
            with open(f, encoding="utf-8") as fh:
                rows.append({"id": os.path.splitext(os.path.basename(f))[0], "text": fh.read()})
        return rows
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def letter_options(it) -> list[str]:
    out = []
    for letter, opt in zip("ABCDEFG", it.options or []):
        out.append(f"{letter}) {opt}" + ("  ✅" if opt == it.key else ""))
    return out


def passage_section(p: dict, run, secs: float) -> list[str]:
    meta = ", ".join(f"{k} {p[k]}" for k in ("subject", "class", "style") if k in p)
    L = [f"## {p['id']}", f"*{meta}* · {run.gate['reason']} · {secs:.1f} s", ""]
    s = run.summary or {}
    if s.get("sentences"):
        L.append("**Summary**")
        for x in s["sentences"]:
            how = "kept original (rewrite failed checks)" if x["fallback"] else "model rewrite"
            L.append(f"- [{how}] {x['text']}")
        L.append("")
    vis = visible_items(run)
    L.append(f"**Shown to the student: {len(vis)}**  ({sum(not i.fallback for i in vis)} written by the model, "
             f"{sum(i.fallback for i in vis)} fill-in-the-blank by code)")
    L.append("")
    for n, it in enumerate(vis, 1):
        src = "code fill-in-the-blank" if it.fallback else "model"
        L.append(f"{n}. **{it.stem}**  _({src}, from sentence {it.witness_idx + 1})_")
        L.extend(f"   - {o}" for o in letter_options(it))
        L.append(f"   - source: \"{it.witness}\"")
    held = [i for i in run.items if i not in vis]
    if held:
        L += ["", f"**Held back: {len(held)}**", ""]
        for it in held:
            L.append(f"- {it.tier}, answer **{it.key}**, sentence {it.witness_idx + 1}: \"{it.witness}\"")
            for a in it.attempts:
                back = (a.get("verify") or {}).get("text")
                back_s = f"  → answered back: \"{back}\"" if back is not None else ""
                fails = ", ".join(a.get("failed") or []) or "passed"
                L.append(f"  - draft \"{a['text']}\"  [{fails}]{back_s}")
            if it.options and it.stem and not it.stem.startswith("(withheld"):
                L.append(f"  - options: {' | '.join(it.options)}")
    L.append("")
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passages", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-items", type=int, default=6)
    ap.add_argument("--limit", type=int, help="only the first N passages")
    add_backend_args(ap)
    args = ap.parse_args()

    passages = load_passages(args.passages)[: args.limit]
    os.makedirs(os.path.join(args.out, "runs"), exist_ok=True)
    backend = build_backend(args)
    print(f"{len(passages)} passages, backend {backend.info().get('name')}", flush=True)

    rows, sections, tot = [], [], Counter()
    fail_reasons, summary_kinds = Counter(), Counter()
    t_all = time.perf_counter()
    for k, p in enumerate(passages, 1):
        t0 = time.perf_counter()
        try:
            run = prepare(p["text"], backend, n_items=args.n_items)
        except Exception as e:  # one bad passage must not stop the batch
            print(f"[{k}/{len(passages)}] {p['id']}: ERROR {type(e).__name__}: {e}", flush=True)
            tot["errors"] += 1
            sections.append([f"## {p['id']}", f"ERROR: {type(e).__name__}: {e}", ""])
            continue
        secs = time.perf_counter() - t0
        run.save(os.path.join(args.out, "runs", f"{p['id']}.json"))
        vis = visible_items(run)
        tot["passages"] += 1
        tot["gate_ok"] += bool(run.items)
        tot["shown"] += len(vis)
        tot["shown_model"] += sum(not i.fallback for i in vis)
        tot["shown_cloze"] += sum(i.fallback for i in vis)
        tot["at_least_3"] += len(vis) >= 3
        model_items = [i for i in run.items if not i.fallback]
        tot["model_drafted_items"] += len(model_items)
        tot["model_items_green"] += sum(i.tier == "GREEN" for i in model_items)
        for i in run.items:
            for r in i.reasons:
                fail_reasons[r.split(":")[0]] += 1
        for x in (run.summary or {}).get("sentences", []):
            summary_kinds["kept original" if x["fallback"] else "model rewrite"] += 1
        ts = token_stats(run)
        tot["model_calls"] += ts["calls"]
        tot["tokens_out"] += ts["generated_tokens"]
        tot["seconds"] += secs
        for n, it in enumerate(vis, 1):
            rows.append({"passage": p["id"], "subject": p.get("subject", ""), "q": n, "source": "cloze" if it.fallback else "model",
                         "question": it.stem, "options": " | ".join(it.options or []), "answer": it.key,
                         "witness": it.witness, "rating": "", "note": ""})
        sections.append(passage_section(p, run, secs))
        print(f"[{k}/{len(passages)}] {p['id']:<22} shown {len(vis)} ({sum(not i.fallback for i in vis)} model)  {secs:.1f}s",
              flush=True)

    n = max(tot["passages"], 1)
    totals = {
        "passages": tot["passages"], "errors": tot["errors"], "backend": backend.info().get("name"),
        "passages_with_3_or_more_shown": tot["at_least_3"],
        "questions_shown": tot["shown"], "shown_written_by_model": tot["shown_model"], "shown_fill_in_blank": tot["shown_cloze"],
        "model_share_of_shown": round(tot["shown_model"] / max(tot["shown"], 1), 3),
        "model_drafted_items": tot["model_drafted_items"],
        "model_items_accepted_green": tot["model_items_green"],
        "model_acceptance_rate": round(tot["model_items_green"] / max(tot["model_drafted_items"], 1), 3),
        "summary_sentences": dict(summary_kinds),
        "why_items_were_held_back": dict(fail_reasons.most_common()),
        "avg_seconds_per_passage": round(tot["seconds"] / n, 1), "model_calls": tot["model_calls"],
        "tokens_out": tot["tokens_out"], "wall_seconds": round(time.perf_counter() - t_all, 1),
    }
    with open(os.path.join(args.out, "totals.json"), "w", encoding="utf-8") as f:
        json.dump(totals, f, indent=2)
    with open(os.path.join(args.out, "rating.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["passage"])
        w.writeheader()
        w.writerows(rows)
    head = [f"# Batch evaluation: {totals['backend']}", "",
            f"- passages: {totals['passages']} (errors {totals['errors']}); with at least 3 questions shown: "
            f"{totals['passages_with_3_or_more_shown']}",
            f"- questions shown: {totals['questions_shown']} = {totals['shown_written_by_model']} written by the model + "
            f"{totals['shown_fill_in_blank']} fill-in-the-blank by code (model share {totals['model_share_of_shown']:.0%})",
            f"- model-drafted questions accepted: {totals['model_items_accepted_green']} of {totals['model_drafted_items']} "
            f"({totals['model_acceptance_rate']:.0%})",
            f"- summary sentences: {totals['summary_sentences']}",
            f"- why questions were held back: {totals['why_items_were_held_back']}",
            f"- {totals['avg_seconds_per_passage']} s per passage on this machine, {totals['model_calls']} model calls in all", "",
            "Rate the shown questions in rating.csv (good / ok / bad). ✅ marks the answer key.", ""]
    with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(head + [line for sec in sections for line in sec]))
    print(json.dumps(totals, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
