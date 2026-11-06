"""Counterfactual Passage Test (build map T24, T26): the headline measurement, scored by code.

For each case (one planted fact) we ask: does an answer follow the PASSAGE or the model's MEMORY?
  A  the baseline's key  (three arms, all with the passage in context: targeted, free-form, grounded-prompt)
  B  Sakshi's key        (forced to use the planted term; follows the passage BY CONSTRUCTION, which is a
                          guarantee of the design, not a model result. Reported as such.)
  C  the summary         (model-written wording, so this is the non-circular test of OUR system)
  D  stems that still make sense (human rated; a sheet is written, nothing is scored here)
Honesty rules baked in (red-team F1-F3, F13, F18):
  * counterfactual passages are chosen to expose the trap, so A is NOT the baseline's everyday error rate;
  * Sakshi's item is forced onto the planted sentence in eval mode, and that is stated;
  * the dev half may be filtered to facts that trap the model; the held-out half is NEVER filtered;
  * counts, denominators and Wilson 95% intervals are reported, never a bare percentage.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter

from .baseline import run_baseline, touches
from .counterfactual import Case, planted_term, value_matches
from .generate import TEMPERATURES, make_whole_summary
from .pipeline import prepare

CAVEAT = ("These passages are built to expose the trap, so the baseline's rate on them is NOT its everyday error "
          "rate. Sakshi's key follows the passage because code picks the key (a guarantee of the design, not a "
          "skill of the model); the summary, which the model writes, is the real test of our system.")


def classify(answer: str | None, case: Case) -> str:
    """memory | passage | both | other | empty. Numbers match as whole numbers with units ignored."""
    if not answer or not answer.strip():
        return "empty"
    mem, pas = value_matches(answer, case.memory_value), value_matches(answer, case.passage_value)
    return "both" if mem and pas else "memory" if mem else "passage" if pas else "other"


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    """95% Wilson interval for k of n. With n this small the interval is wide, and that is the honest picture."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def rate_block(classes: list[str], key: str = "memory") -> dict:
    c = Counter(classes)
    n = len(classes)
    k = c.get(key, 0)
    return {"n": n, "counts": dict(c), f"{key}_count": k, f"{key}_rate": round(k / n, 3) if n else None, "ci95": wilson(k, n)}


def _extra(case: Case) -> dict:
    return {"passage_value": case.passage_value, "memory_value": case.memory_value}


def trap_check(cases: list[Case], backend, tries: int = 3) -> dict:
    """Which facts actually trap the targeted baseline (passage IN context)? Run on the DEV half only.
    A fact counts as a trap if the baseline follows memory in at least one of `tries` tries."""
    out = {}
    for c in cases:
        seen = []
        for t in range(tries):
            items, _ = run_baseline(backend, c.passage, "targeted", c.sentence, _extra(c),
                                    temperature=TEMPERATURES[min(t, len(TEMPERATURES) - 1)], seed=t)
            seen.append(classify(items[0].answer, c) if items else "unparsed")
        out[c.id] = {"trap": "memory" in seen, "tries": seen}
    return out


def evaluate_case(case: Case, baseline_backend, sakshi_backend, gate_override: bool = False) -> dict:
    sent, extra = case.sentence, _extra(case)
    rec: dict = {"id": case.id, "split": case.split, "type": case.type, "sentence": sent}

    items, raw = run_baseline(baseline_backend, case.passage, "targeted", sent, extra)
    a = items[0] if items else None
    rec["targeted"] = {"class": classify(a.answer, case) if a else "unparsed", "question": a.question if a else None,
                       "answer": a.answer if a else None,
                       # would a plain "is the answer in the passage?" check have released it? (ablation A)
                       "span_check_releases": bool(a) and value_matches(case.passage, a.answer)}
    items, raw = run_baseline(baseline_backend, case.passage, "grounded", sent, extra)
    g = items[0] if items else None
    rec["grounded"] = {"class": classify(g.answer, case) if g else "unparsed", "answer": g.answer if g else None,
                       "support": g.support if g else None}
    items, raw = run_baseline(baseline_backend, case.passage, "free", None, {**extra, "sentence": sent})
    touching = [i for i in items if touches(i, sent)]
    rec["free"] = {"covered": bool(touching), "n_items": len(items),
                   "class": classify(touching[0].answer, case) if touching else None}

    term = planted_term(case)
    run = prepare(case.passage, sakshi_backend, force_sentences=[case.sentence_idx],
                  force_terms={case.sentence_idx: term} if term else None, gate_override=gate_override)
    it = next((i for i in run.items if i.witness_idx == case.sentence_idx), None)
    rec["sakshi"] = {"term": term, "item": None if not it else {"key": it.key, "stem": it.stem, "tier": it.tier,
                                                                "reasons": it.reasons, "witness": it.witness},
                     "class": classify(it.key, case) if it else "no_item"}
    summ = run.summary.get("text", "")
    rec["summary"] = {"text": summ, "has_memory": value_matches(summ, case.memory_value),
                      "has_passage": value_matches(summ, case.passage_value)}
    w = make_whole_summary(baseline_backend, case.passage, extra={**extra, "sentence": sent})["text"]
    rec["whole_summary"] = {"text": w, "has_memory": value_matches(w, case.memory_value),
                            "has_passage": value_matches(w, case.passage_value)}
    return rec


def _split_block(recs: list[dict], n_total: int, filtered: bool) -> dict:
    n = len(recs)
    free = [r["free"] for r in recs]
    covered = [f for f in free if f["covered"]]
    mem_followers = [r for r in recs if r["targeted"]["class"] == "memory"]
    return {
        "n_total": n_total, "n_scored": n, "filtered_to_trapping_facts": filtered,
        "A_targeted": rate_block([r["targeted"]["class"] for r in recs]),
        "A_grounded": rate_block([r["grounded"]["class"] for r in recs]),
        "A_free": {"coverage": {"covered": len(covered), "n": n, "rate": round(len(covered) / n, 3) if n else None},
                   **rate_block([f["class"] for f in covered])},
        "A_span_check": {"memory_answers": len(mem_followers),
                         "released_by_a_plain_span_check": sum(r["targeted"]["span_check_releases"] for r in mem_followers),
                         "note": "a memory answer whose value is absent from the passage is caught by a plain span check; "
                                 "it passes only when the value also appears elsewhere in the passage"},
        "B_sakshi_key": {**rate_block([r["sakshi"]["class"] for r in recs], "passage"),
                         "note": "100% by construction when an item exists; no_item counts as not measured"},
        "C_sakshi_summary_has_memory_value": rate_block(["memory" if r["summary"]["has_memory"] else "ok" for r in recs]),
        "C_whole_summary_has_memory_value": rate_block(["memory" if r["whole_summary"]["has_memory"] else "ok" for r in recs]),
    }


def evaluate(cases: list[Case], baseline_backend, sakshi_backend, kept_dev: set[str] | None = None,
             gate_override: bool = False) -> dict:
    records = [evaluate_case(c, baseline_backend, sakshi_backend, gate_override) for c in cases]
    out: dict = {"caveat": CAVEAT, "splits": {}, "cases": records,
                 "backends": {"baseline": baseline_backend.info(), "sakshi": sakshi_backend.info()},
                 "filter": ("dev facts kept only if the targeted baseline followed memory in at least 1 of 3 tries; "
                            "held-out is never filtered" if kept_dev is not None else "no filter applied")}
    for split in ("dev", "heldout"):
        recs = [r for r in records if r["split"] == split]
        total = len(recs)
        filtered = split == "dev" and kept_dev is not None
        if filtered:
            recs = [r for r in recs if r["id"] in kept_dev]
        if total:
            out["splits"][split] = _split_block(recs, total, filtered)
    return out


def write_d_sheet(metrics: dict, path: str) -> int:
    """Human rating sheet for D: does Sakshi's stem still make sense next to the planted fact?"""
    rows = [r for r in metrics["cases"] if r["sakshi"]["item"]]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "split", "planted_sentence", "key", "stem", "tier", "rating (sensible / awkward / fights_the_fact / nonsense)"])
        for r in rows:
            it = r["sakshi"]["item"]
            w.writerow([r["id"], r["split"], r["sentence"], it["key"], it["stem"], it["tier"], ""])
    return len(rows)


def save(metrics: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
