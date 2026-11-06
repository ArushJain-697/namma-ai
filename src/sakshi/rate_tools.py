"""Rating sheets and scorers for the go/no-go gates (build map T21, T22, T23) and Ablation C (T27).

Pattern: `build` writes a CSV with generated output and a blank rating column; a person fills it in; `score`
reads it back and prints shares with denominators. Nothing here rates anything by itself: judgement stays human,
and every verdict says how many items were rated.

Verdict thresholds for T21 are PROPOSED ([DESIGN]) and should be agreed before the numbers are seen.
"""
from __future__ import annotations

import csv
import os
from collections import Counter, defaultdict

from .checks import failures, summary_sentence_checks
from .generate import build_cloze, make_stem, make_summary, make_whole_summary
from .readability import fk_grade
from .select import analyse
from .text import contains_term, tokens

STEM_RATINGS = ("usable", "awkward", "wrong_term", "leaks_answer", "nonsense")
SUMMARY_FAITHFUL = ("yes", "no")
SUMMARY_UNDERSTOOD = ("yes", "mostly", "no")
RELEVANCE_RATINGS = ("key_idea", "minor_detail", "trivial")
ABL_C_RATINGS = ("model", "cloze", "same")
MIN_RATED = 15  # below this a verdict is "INCOMPLETE"
GO, MARGINAL = 0.50, 0.30  # share of rated stems that are "usable" (proposed thresholds)


def load_passages(directory: str) -> dict[str, str]:
    out = {}
    for name in sorted(os.listdir(directory)):
        if name.endswith(".txt"):
            with open(os.path.join(directory, name), encoding="utf-8") as f:
                out[name[:-4]] = f.read().strip()
    return out


def write_sheet(path: str, header: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def read_sheet(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _rating_col(rows: list[dict]) -> str:
    return next(k for k in rows[0].keys() if k.startswith("rating")) if rows else "rating"


def _tally(rows: list[dict], col: str, allowed: tuple[str, ...]) -> tuple[Counter, int, list[str]]:
    """Count valid ratings. Returns (counts, n_blank, unknown_values)."""
    c: Counter = Counter()
    blank, unknown = 0, []
    for r in rows:
        v = (r.get(col) or "").strip().lower()
        if not v:
            blank += 1
        elif v in allowed:
            c[v] += 1
        else:
            unknown.append(v)
    return c, blank, unknown


# ---- T21: stem quality (go/no-go for answer-first) ------------------------------------------------------
def build_stem_cases(passages: dict[str, str], n: int = 20) -> list[dict]:
    """Round-robin over passages so no single passage dominates."""
    per = {name: analyse(text).candidates for name, text in passages.items()}
    sents = {name: analyse(text).sentences for name, text in passages.items()}
    cases, i = [], 0
    while len(cases) < n and any(i < len(c) for c in per.values()):
        for name, cands in per.items():
            if i < len(cands) and len(cases) < n:
                c = cands[i]
                cases.append({"case_id": f"{name}:{c.sent_idx + 1}", "passage": name, "witness": sents[name][c.sent_idx],
                              "answer": c.term})
        i += 1
    return cases


def build_stem_sheet(backend, passages: dict[str, str], path: str, n: int = 20) -> int:
    cases = build_stem_cases(passages, n)
    rows = []
    for c in cases:
        sr = make_stem(backend, c["witness"], c["answer"], passages[c["passage"]])
        rows.append([c["case_id"], c["witness"], c["answer"], sr.text or "(withheld)", sr.tier, "; ".join(sr.reasons), ""])
    write_sheet(path, ["case_id", "witness", "answer", "generated_question", "tier", "auto_reasons",
                       "rating (" + " / ".join(STEM_RATINGS) + ")"], rows)
    return len(rows)


def score_stems(path: str) -> dict:
    rows = read_sheet(path)
    col = _rating_col(rows)
    c, blank, unknown = _tally(rows, col, STEM_RATINGS)
    rated = sum(c.values())
    share = c["usable"] / rated if rated else None
    if rated < MIN_RATED:
        verdict = f"INCOMPLETE: {rated} rated, need at least {MIN_RATED}"
    elif share >= GO:
        verdict = "GO: answer-first is viable; keep the design"
    elif share >= MARGINAL:
        verdict = ("MARGINAL: consider code-template stems with a model-simplified summary (Ablation C) and say so in the pitch")
    else:
        verdict = "NO-GO: the model's questions are not good enough; change the pitch (cloze with a model-simplified summary)"
    return {"rated": rated, "blank": blank, "unknown_ratings": unknown, "counts": dict(c),
            "usable_share": round(share, 3) if share is not None else None, "verdict": verdict,
            "thresholds": f"GO >= {GO:.0%} usable, MARGINAL >= {MARGINAL:.0%} (proposed, agree before looking)"}


# ---- T22: summary arms ----------------------------------------------------------------------------------
def build_summary_sheet(backend, passages: dict[str, str], path: str) -> int:
    rows = []
    for name, text in passages.items():
        pg = fk_grade(text)
        a = analyse(text)
        w = make_summary(backend, a)
        fallbacks = sum(s.fallback for s in w.sentences)
        rows.append([name, "witnessed", w.text, len(tokens(w.text)), round(fk_grade(w.text), 1), round(pg, 1),
                     f"{fallbacks} of {len(w.sentences)} sentences fell back to the original", "", ""])
        whole = make_whole_summary(backend, text)
        hard = [c.name for c in failures(whole["checks"], "HARD")]
        rows.append([name, "whole_passage", whole["text"], len(tokens(whole["text"])), round(fk_grade(whole["text"]), 1),
                     round(pg, 1), ("hard check failures: " + ", ".join(hard)) if hard else "no hard failures", "", ""])
    write_sheet(path, ["passage", "arm", "summary", "words", "summary_fk_grade", "passage_fk_grade", "auto_notes",
                       "rating_faithful (yes / no)", "rating_understandable (yes / mostly / no)"], rows)
    return len(rows)


def score_summaries(path: str) -> dict:
    rows = read_sheet(path)
    out: dict = {}
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    for arm, rs in by_arm.items():
        f, fb, fu = _tally(rs, "rating_faithful (yes / no)", SUMMARY_FAITHFUL)
        u, ub, uu = _tally(rs, "rating_understandable (yes / mostly / no)", SUMMARY_UNDERSTOOD)
        nf, nu = sum(f.values()), sum(u.values())
        out[arm] = {"n": len(rs), "faithful_rated": nf, "faithful_yes": f["yes"],
                    "faithful_share": round(f["yes"] / nf, 3) if nf else None,
                    "understandable_rated": nu, "understandable_yes_or_mostly": u["yes"] + u["mostly"],
                    "understandable_share": round((u["yes"] + u["mostly"]) / nu, 3) if nu else None,
                    "mean_words": round(sum(float(r["words"]) for r in rs) / len(rs), 1)}
    out["rule"] = "keep the arm that is more faithful first, more understandable second; report both"
    return out


# ---- T23: relevance -------------------------------------------------------------------------------------
def build_relevance_sheet(passages: dict[str, str], path: str) -> int:
    rows = []
    for name, text in passages.items():
        a = analyse(text)
        for rank, c in enumerate(a.candidates, 1):
            rows.append([name, rank, c.sent_idx + 1, a.sentences[c.sent_idx], c.term, "+".join(c.signals),
                         "relevant" if c.relevant else "detail only", ""])
    write_sheet(path, ["passage", "rank", "sentence_no", "sentence", "answer", "signals", "auto_flag",
                       "rating (" + " / ".join(RELEVANCE_RATINGS) + ")"], rows)
    return len(rows)


def score_relevance(path: str) -> dict:
    rows = read_sheet(path)
    col = _rating_col(rows)
    c, blank, unknown = _tally(rows, col, RELEVANCE_RATINGS)
    rated = sum(c.values())
    violations = [f"{r['passage']} rank {r['rank']}: {r['answer']!r}" for r in rows
                  if int(r["rank"]) <= 3 and (r.get(col) or "").strip().lower() == "trivial"]
    return {"rated": rated, "blank": blank, "unknown_ratings": unknown, "counts": dict(c),
            "key_idea_share": round(c["key_idea"] / rated, 3) if rated else None,
            "top3_trivial_violations": violations,
            "passes": rated > 0 and not violations,
            "note": "selection weights may change ONLY on the dev half, and only after this sheet is filled in"}


# ---- T27: Ablation C (what does the model's wording add over a code template?) -------------------------
def ablation_c_rows(run) -> list[dict]:
    rows = []
    for it in run.items:
        if it.fallback or it.tier == "RED":
            continue
        cloze = build_cloze(it.witness, it.key)
        rows.append({"id": it.id, "key": it.key, "model_stem": it.stem, "cloze_stem": cloze,
                     "model_words": len(tokens(it.stem)), "cloze_words": len(tokens(cloze)),
                     "model_fk": round(fk_grade(it.stem), 1), "cloze_fk": round(fk_grade(cloze), 1),
                     "model_leaks": contains_term(it.stem, it.key), "cloze_leaks": contains_term(cloze, it.key)})
    return rows


def build_ablation_c_sheet(run, path: str) -> int:
    rows = ablation_c_rows(run)
    write_sheet(path, ["id", "key", "model_stem", "cloze_stem", "model_words", "cloze_words", "model_fk", "cloze_fk",
                       "model_leaks", "cloze_leaks", "rating (" + " / ".join(ABL_C_RATINGS) + ")"],
                [[r[k] for k in ("id", "key", "model_stem", "cloze_stem", "model_words", "cloze_words", "model_fk",
                                 "cloze_fk", "model_leaks", "cloze_leaks")] + [""] for r in rows])
    return len(rows)


def score_ablation_c(path: str) -> dict:
    rows = read_sheet(path)
    col = _rating_col(rows)
    c, blank, unknown = _tally(rows, col, ABL_C_RATINGS)
    n = sum(c.values())
    return {"rated": n, "counts": dict(c), "blank": blank, "unknown_ratings": unknown,
            "model_better_share": round(c["model"] / n, 3) if n else None,
            "reading": ("the model's wording earns its place" if n and c["model"] > c["cloze"] else
                        "the model adds little over a code template: say so in the pitch" if n else "not rated yet")}
