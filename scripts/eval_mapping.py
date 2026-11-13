#!/usr/bin/env python3
"""How accurately do we map an evidence sentence to the right misconceptions? Compare methods; learn the weights.

  .venv-ml/bin/python scripts/eval_mapping.py --fit          # learn fusion weights on TRAINING items -> index/weights.json
  .venv-ml/bin/python scripts/eval_mapping.py                # score every method on TEST items -> results/mapping/

Gold labels: in the teacher-written dataset (data/dataset/raw/), each question names the 3 misconceptions its wrong
options target, for one evidence sentence. A method is good if those 3 are near the top of its ranking.
Metrics: recall@5 (share of the 3 gold in the top 5 = in the menu the model sees), hit@1, MAP@25 (the Eedi
competition metric), and topic top-1 for the passage.
Methods: keywords (today's matcher), embed (meaning only), embed+kw+topic, full (+NLI re-rank), learned (weights
fitted with --fit), and finetuned (a retriever fine-tuned by train/finetune_retriever.py, if present).
"""
import argparse
import json
import os
import random
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.diagnostic import choose_beliefs  # noqa: E402
from sakshi.mapper import DEFAULT_WEIGHTS, FEATURES, INDEX_DIR, Mapper, TorchEncoders  # noqa: E402
from sakshi.misconceptions import Library  # noqa: E402

RAW = os.path.join(ROOT, "data", "dataset", "raw")
FINETUNED = os.path.join(ROOT, "models", "retriever-finetuned")


def load_items(split: str, limit: int | None, lib: Library) -> list[dict]:
    out = []
    d = os.path.join(RAW, split)
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        r = json.load(open(os.path.join(d, f), encoding="utf-8"))
        passage = r["response"].get("passage", "")
        for it in r["response"].get("items", []) or []:
            gold = [o.get("belief_id") for o in it.get("options", []) or []]
            if len(gold) == 3 and all(g in lib.by_id for g in gold) and it.get("evidence"):
                out.append({"passage": passage, "evidence": it["evidence"], "gold": gold,
                            "topic_id": r["job"]["topic_id"], "test_only": r["job"].get("test_only_topic", False)})
    random.Random(5).shuffle(out)
    return out[:limit] if limit else out


def ap_at_k(ranked: list[str], gold: set, k: int = 25) -> float:
    hits, s = 0, 0.0
    for i, x in enumerate(ranked[:k], 1):
        if x in gold:
            hits += 1
            s += hits / i
    return s / min(len(gold), k)


def rank_keywords(lib: Library, it: dict) -> list[str]:
    mis = lib.match(it["passage"], n_misconceptions=40).misconceptions
    return [m["id"] for m in choose_beliefs(it["evidence"], it["passage"], mis, 25)]


def rank_mapper(mp: Mapper, it: dict, cache: dict) -> tuple[list[str], str | None]:
    key = it["passage"]
    if key not in cache:
        cache[key] = mp.topics(key)
    ts = cache[key]
    mp.rerank = 25
    sc = mp.score_sentence(it["evidence"], ts, n=25)
    return [s.misconception["id"] for s in sc], (max(ts, key=ts.get) if ts else None)


def evaluate(name: str, fn, items: list[dict]) -> dict:
    t0 = time.perf_counter()
    r5 = h1 = mp = top = 0.0
    split = {"test-only topics": [0, 0], "training topics": [0, 0]}
    for it in items:
        ranked, topic = fn(it)
        g = set(it["gold"])
        r = len(g & set(ranked[:5])) / 3
        r5 += r
        h1 += bool(ranked) and ranked[0] in g
        mp += ap_at_k(ranked, g)
        top += topic == it["topic_id"]
        s = split["test-only topics" if it["test_only"] else "training topics"]
        s[0] += r
        s[1] += 1
    n = max(len(items), 1)
    res = {"method": name, "items": len(items), "recall@5": round(r5 / n, 3), "hit@1": round(h1 / n, 3),
           "MAP@25": round(mp / n, 3), "topic_top1": round(top / n, 3) if name != "keywords" else None,
           "recall@5_by_split": {k: round(v[0] / v[1], 3) if v[1] else None for k, v in split.items()},
           "ms_per_item": round((time.perf_counter() - t0) * 1000 / n, 1)}
    print(json.dumps(res), flush=True)
    return res


def fit(mp: Mapper, items: list[dict]) -> dict:
    """Logistic regression on candidate features: gold misconception (1) vs other candidates (0)."""
    from sklearn.linear_model import LogisticRegression
    X, y, cache = [], [], {}
    mp.rerank = 25
    for it in items:
        if it["passage"] not in cache:
            cache[it["passage"]] = mp.topics(it["passage"])
        for s in mp.score_sentence(it["evidence"], cache[it["passage"]], n=25):
            X.append([s.features[k] for k in FEATURES])
            y.append(int(s.misconception["id"] in it["gold"]))
    clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000).fit(np.array(X), np.array(y))
    w = {k: round(float(c), 4) for k, c in zip(FEATURES, clf.coef_[0])}
    w["bias"] = round(float(clf.intercept_[0]), 4)
    print(f"fitted on {len(y)} candidates ({sum(y)} gold): {w}")
    return w


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--limit", type=int, default=600)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "mapping"))
    ap.add_argument("--nli", default="cross-encoder/nli-deberta-v3-xsmall")
    args = ap.parse_args()
    lib = Library.load()
    enc = TorchEncoders(nli_model=args.nli)
    if args.fit:
        items = load_items("train", 1500, lib)
        mp = Mapper(lib, enc, weights=dict(DEFAULT_WEIGHTS))
        w = fit(mp, items)
        os.makedirs(INDEX_DIR, exist_ok=True)
        json.dump(w, open(os.path.join(INDEX_DIR, "weights.json"), "w"), indent=2)
        if os.path.isdir(FINETUNED):
            mpf = Mapper(lib, TorchEncoders(embed_model=FINETUNED, nli_model=args.nli), weights=dict(DEFAULT_WEIGHTS))
            wf = fit(mpf, items)
            json.dump(wf, open(os.path.join(INDEX_DIR, "weights_finetuned.json"), "w"), indent=2)
        return 0

    items = load_items("test", args.limit, lib)
    print(f"{len(items)} test items ({sum(i['test_only'] for i in items)} on test-only topics)")
    results = [evaluate("keywords", lambda it: (rank_keywords(lib, it), None), items)]
    only = lambda keys: {k: (DEFAULT_WEIGHTS[k] if k in keys else 0.0) for k in DEFAULT_WEIGHTS}  # noqa: E731
    variants = [("embed", only({"cos_fix", "cos_mis"})), ("embed+kw+topic", only({"cos_fix", "cos_mis", "kw", "topic"})),
                ("full (+NLI)", dict(DEFAULT_WEIGHTS))]
    wpath = os.path.join(INDEX_DIR, "weights.json")
    if os.path.exists(wpath):
        variants.append(("learned", json.load(open(wpath))))
    for name, w in variants:
        mp, cache = Mapper(lib, enc, weights=w), {}
        results.append(evaluate(name, lambda it: rank_mapper(mp, it, cache), items))
    wf = os.path.join(INDEX_DIR, "weights_finetuned.json")
    if os.path.isdir(FINETUNED):
        encf = TorchEncoders(embed_model=FINETUNED, nli_model=args.nli)
        mp, cache = Mapper(lib, encf, weights=json.load(open(wf)) if os.path.exists(wf) else dict(DEFAULT_WEIGHTS)), {}
        results.append(evaluate("finetuned retriever + learned", lambda it: rank_mapper(mp, it, cache), items))
    os.makedirs(args.out, exist_ok=True)
    json.dump(results, open(os.path.join(args.out, "mapping_results.json"), "w"), indent=2)
    lines = ["| method | recall@5 | hit@1 | MAP@25 | topic top-1 | recall@5 test-only topics | ms/item |", "|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['method']} | {r['recall@5']} | {r['hit@1']} | {r['MAP@25']} | {r['topic_top1']} | "
                     f"{r['recall@5_by_split']['test-only topics']} | {r['ms_per_item']} |")
    open(os.path.join(args.out, "mapping_results.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
