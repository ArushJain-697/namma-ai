"""Layer 6: checks and tiers. Pure code, standard library only.

Each check returns a CheckResult. HARD failures withhold an item (RED); WARN failures
mark it AMBER. Thresholds are DESIGN values to be set on the dev set only (bible Layer 2/4).
A pass rate alone proves nothing: tests/test_checks.py seeds one bad input per check and
requires each check to fire on its own fault and stay quiet on a good input.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .readability import avg_sentence_len, fk_grade
from .text import content_stems, find_span, is_number, iter_tokens, stem, tokens

HARD, WARN = "HARD", "WARN"

SUPPORT_MIN = 0.70  # share of a rewrite's content stems that must appear in its source sentence
PASSAGE_OVERLAP_MIN = 0.60
MAX_STEM_WORDS = 20
DUP_RATIO = 0.92
ECHO_RATIO = 0.85
SUMMARY_WORDS = (30, 80)
SUMMARY_AVG_SENT = 15
NEGATIONS = frozenset({"not", "no", "never", "cannot", "none", "nothing", "nobody", "neither", "nor"})


@dataclass
class CheckResult:
    name: str
    severity: str
    passed: bool
    detail: str = ""


def _numbers(text: str) -> set[str]:
    return {t.replace(",", "") for t in tokens(text) if is_number(t)}


def _has_negation(text: str) -> bool:
    for t in tokens(text):
        low = t.lower().replace("’", "'")
        if low in NEGATIONS or low.endswith("n't"):
            return True
    return False


def _new_names(rewrite: str, source: str) -> list[str]:
    src = {t.lower() for t in tokens(source)}
    out = []
    for pos, (t, _, _) in enumerate(iter_tokens(rewrite)):
        if pos > 0 and t[0].isupper() and not is_number(t) and t.lower() not in src:
            out.append(t)
    return out


# ---- summary ---------------------------------------------------------------------------
def summary_sentence_checks(source: str, rewrite: str) -> list[CheckResult]:
    """Check one simplified summary sentence against its own source sentence."""
    r: list[CheckResult] = []
    rw = rewrite.strip()
    r.append(CheckResult("summary_nonempty", HARD, bool(rw), "empty rewrite" if not rw else ""))
    if not rw:
        return r
    rw_stems, src_stems = content_stems(rw), set(content_stems(source))
    share = (sum(1 for s in rw_stems if s in src_stems) / len(rw_stems)) if rw_stems else 0.0
    r.append(CheckResult("summary_support", HARD, share >= SUPPORT_MIN,
                         f"{share:.0%} of content words are in the source sentence (need {SUPPORT_MIN:.0%})"))
    bad_nums = sorted(_numbers(rw) - _numbers(source))
    r.append(CheckResult("summary_numbers", HARD, not bad_nums, f"numbers not in source: {bad_nums}" if bad_nums else ""))
    neg_ok = _has_negation(source) == _has_negation(rw)
    r.append(CheckResult("summary_negation", HARD, neg_ok, "negation differs from source" if not neg_ok else ""))
    names = _new_names(rw, source)
    r.append(CheckResult("summary_new_names", WARN, not names, f"new capitalised words: {names}" if names else ""))
    grade, limit = fk_grade(rw), max(fk_grade(source), 7.0)
    sent_len = avg_sentence_len(rw)
    ok = grade <= limit and sent_len <= SUMMARY_AVG_SENT
    r.append(CheckResult("summary_readability", WARN, ok, f"grade {grade:.1f} (limit {limit:.1f}), {sent_len:.0f} words/sentence"))
    return r


def summary_overall_checks(summary_text: str) -> list[CheckResult]:
    n = len(tokens(summary_text))
    lo, hi = SUMMARY_WORDS
    return [CheckResult("summary_length", HARD, lo <= n <= hi, f"{n} words (need {lo}-{hi})")]


# ---- stems -----------------------------------------------------------------------------
def stem_checks(question: str, answer: str, witness: str, passage: str, other_stems: list[str] | None = None) -> list[CheckResult]:
    r: list[CheckResult] = []
    q = question.strip()
    r.append(CheckResult("stem_nonempty", HARD, bool(q), "empty" if not q else ""))
    if not q:
        return r
    r.append(CheckResult("stem_question_mark", HARD, q.endswith("?"), "does not end with ?" if not q.endswith("?") else ""))
    n = len(tokens(q))
    r.append(CheckResult("stem_length", HARD, n <= MAX_STEM_WORDS, f"{n} words (max {MAX_STEM_WORDS})"))
    leak = find_span(q, answer) is not None
    r.append(CheckResult("stem_no_answer_leak", HARD, not leak, "the answer appears in the question" if leak else ""))
    echo = SequenceMatcher(None, q.lower(), witness.lower()).ratio()
    r.append(CheckResult("stem_not_echo", HARD, echo < ECHO_RATIO, f"similarity to the witness {echo:.2f}"))
    dup = max((SequenceMatcher(None, q.lower(), o.lower()).ratio() for o in (other_stems or [])), default=0.0)
    r.append(CheckResult("stem_not_duplicate", HARD, dup < DUP_RATIO, f"similarity to another stem {dup:.2f}"))
    stems_q = content_stems(q)
    p_stems = set(content_stems(passage))
    share = (sum(1 for s in stems_q if s in p_stems) / len(stems_q)) if stems_q else 0.0
    r.append(CheckResult("stem_in_passage", WARN, share >= PASSAGE_OVERLAP_MIN, f"{share:.0%} of content words are in the passage"))
    grade, limit = fk_grade(q), max(fk_grade(witness), 8.0)
    r.append(CheckResult("stem_readability", WARN, grade <= limit, f"grade {grade:.1f} (limit {limit:.1f})"))
    return r


# ---- item assertions (must never fail: a failure is a bug, not a bad model output) -----
def item_assertions(key: str, witness: str, options: list[str] | None) -> list[CheckResult]:
    r = [CheckResult("key_in_witness", HARD, find_span(witness, key) is not None, "key is not a whole-token span of its witness")]
    if options:
        low = [o.lower() for o in options]
        r.append(CheckResult("options_distinct", HARD, len(set(low)) == len(low), "duplicate options"))
        r.append(CheckResult("options_one_key", HARD, low.count(key.lower()) == 1, "key must appear exactly once"))
        wstems = {stem(t) for t in tokens(witness)}
        bad = [o for o in options if o.lower() != key.lower() and stem(o) in wstems]
        r.append(CheckResult("options_not_from_witness", HARD, not bad, f"options from the witness sentence: {bad}" if bad else ""))
    return r


# ---- tiers -----------------------------------------------------------------------------
def failures(results: list[CheckResult], severity: str | None = None) -> list[CheckResult]:
    return [c for c in results if not c.passed and (severity is None or c.severity == severity)]


def tier(results: list[CheckResult], detail: bool = False) -> str:
    """RED if any HARD check failed; AMBER if any WARN failed or the item is a detail question."""
    if failures(results, HARD):
        return "RED"
    if failures(results, WARN) or detail:
        return "AMBER"
    return "GREEN"


def reasons(results: list[CheckResult]) -> list[str]:
    return [f"{c.name}: {c.detail}".rstrip(": ") for c in failures(results)]
