#!/usr/bin/env python3
"""Evaluate diagnostic-question generation on the 200 test passages (base vs fine-tuned model).

  PYTHONPATH=src .venv-export/bin/python scripts/eval_diagnostic.py --out results/eval_diag_base \
      --backend executorch --model models/qwen3-0.6b-8da4w/model.pte --tokenizer models/qwen3-0.6b-8da4w-portable/tokenizer.json

Writes to --out: report.md (every passage: matched topic, every question with options, each wrong option's
misconception and the model's reason, every rejected attempt with reasons), rating.csv (one row per accepted
question for a person to rate good / ok / bad / WRONG), totals.json, banks/ID.json (retention-engine banks).
Question quality does not depend on the device: run this on the fastest machine.
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.backends.factory import add_backend_args, build_backend  # noqa: E402
from sakshi.diagnostic import generate_bank  # noqa: E402
from sakshi.misconceptions import Library  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passages", default=os.path.join(ROOT, "data/dataset/test_passages.jsonl"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--questions", type=int, default=4)
    ap.add_argument("--mapper", choices=["keywords", "torch", "pte"], default="keywords",
                    help="how misconceptions are mapped: keywords only, or the multi-stage mapper (sakshi.mapper) "
                         "with PyTorch helper models or with the ExecuTorch .pte helpers (device-faithful)")
    add_backend_args(ap)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.passages, encoding="utf-8")][: args.limit]
    os.makedirs(os.path.join(args.out, "banks"), exist_ok=True)
    backend = build_backend(args)
    lib = Library.load()
    mapper = None
    if args.mapper != "keywords":
        from sakshi.mapper import Mapper, PteEncoders, TorchEncoders
        enc = PteEncoders() if args.mapper == "pte" else TorchEncoders()
        mapper = Mapper(lib, enc)
    tot, reasons, sections, rating = Counter(), Counter(), [], []
    t_all = time.perf_counter()
    for k, p in enumerate(rows, 1):
        try:
            bank, rep = generate_bank(p["text"], backend, lib, n_questions=args.questions, title=p["id"], seed=k, mapper=mapper)
        except Exception as e:  # noqa: BLE001
            tot["errors"] += 1
            sections.append(f"## {p['id']}\nERROR {type(e).__name__}: {e}\n")
            print(f"[{k}/{len(rows)}] {p['id']}: ERROR {e}", flush=True)
            continue
        json.dump(bank, open(os.path.join(args.out, "banks", p["id"] + ".json"), "w"), indent=1, ensure_ascii=False)
        nq = len(bank["questions"])
        tot["passages"] += 1
        tot["questions"] += nq
        tot["passages_3plus"] += nq >= 3
        tot["slots"] += len(rep["items"])
        tot["attempts"] += sum(len(i["attempts"]) for i in rep["items"])
        tot["first_try_ok"] += sum(1 for i in rep["items"] if i["attempts"] and i["attempts"][0]["ok"])
        tot["seconds"] += rep["total_s"]
        tot["tokens_out"] += sum(a["new_tokens"] or 0 for i in rep["items"] for a in i["attempts"])
        top = rep["topics"][0][0] if rep["topics"] else None
        tot["topic_known"] += bool(p.get("topic_id"))
        tot["topic_right"] += bool(p.get("topic_id")) and top == p["topic_id"]
        for i in rep["items"]:
            for a in i["attempts"]:
                for r in a["reasons"]:
                    reasons[r.split(":")[0]] += 1
        L = [f"## {p['id']}", f"*{p.get('split_reason')} · style {p.get('style')} · class {p.get('grade')}* · "
             f"matched topic {top} (expected {p.get('topic_id')}) · {nq} questions · {rep['total_s']} s", "",
             f"**Summary:** {bank['summary']}", ""]
        for i in rep["items"]:
            q = i.get("question")
            if q:
                L.append(f"- **{q['stem']}**  _(evidence: \"{i['evidence']}\")_")
                for o in q["options"]:
                    if o["correct"]:
                        L.append(f"  - {o['key']}) {o['text']}  ✅")
                    else:
                        L.append(f"  - {o['key']}) {o['text']}  ← {lib.by_id[o['misconception']]['statement']} "
                                 f"_(model: {o.get('why', '')})_")
                rating.append({"passage": p["id"], "split": p.get("split_reason"), "question": q["stem"],
                               "answer": next(o["text"] for o in q["options"] if o["correct"]),
                               "wrong_options": " | ".join(f"{o['text']} [{o['misconception']}]" for o in q["options"] if not o["correct"]),
                               "evidence": i["evidence"], "rating": "", "note": ""})
            else:
                why = i.get("skipped") or "; ".join(r for a in i["attempts"] for r in a["reasons"])[:300]
                L.append(f"- ✗ no question for \"{i['evidence'][:90]}…\": {why}")
        sections.append("\n".join(L) + "\n")
        print(f"[{k}/{len(rows)}] {p['id']:<40} {nq} questions  topic {'ok' if top == p.get('topic_id') else top}  {rep['total_s']}s", flush=True)

    n = max(tot["passages"], 1)
    totals = {"backend": backend.info().get("name"), "passages": tot["passages"], "errors": tot["errors"],
              "questions_accepted": tot["questions"], "questions_per_passage": round(tot["questions"] / n, 2),
              "passages_with_3_or_more": tot["passages_3plus"],
              "slot_success_rate": round(tot["questions"] / max(tot["slots"], 1), 3),
              "first_try_success_rate": round(tot["first_try_ok"] / max(tot["slots"], 1), 3),
              "topic_match_top1": f"{tot['topic_right']}/{tot['topic_known']}",
              "rejection_reasons": dict(reasons.most_common()), "avg_seconds_per_passage": round(tot["seconds"] / n, 1),
              "tokens_out": tot["tokens_out"], "wall_seconds": round(time.perf_counter() - t_all, 1)}
    json.dump(totals, open(os.path.join(args.out, "totals.json"), "w"), indent=2)
    with open(os.path.join(args.out, "rating.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rating[0]) if rating else ["passage"])
        w.writeheader()
        w.writerows(rating)
    head = [f"# Diagnostic evaluation: {totals['backend']}", "", "```", json.dumps(totals, indent=2), "```", "",
            "Each wrong option shows the misconception it targets (←) and the model's reason. Rate rating.csv: "
            "good / ok / bad / WRONG (wrong key or a second correct option).", ""]
    open(os.path.join(args.out, "report.md"), "w", encoding="utf-8").write("\n".join(head + sections))
    print(json.dumps(totals, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
