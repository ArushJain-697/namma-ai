"""Text helpers: sentence splitting, tokens, light stemming. Standard library only.

Everything here is deterministic. The bible's rule: code, not the model, owns facts.
"""
from __future__ import annotations

import re
from typing import Iterator

# Abbreviations whose trailing dot must not end a sentence. Deliberately short:
# words like "no", "co", "st", "etc" often DO end sentences.
ABBREVS = ("mr", "mrs", "ms", "dr", "prof", "vs", "fig", "approx", "cf", "mt", "jr", "sr")
_DOT = "․"  # one-dot leader: stands in for a protected "."

_ABBR_RE = re.compile(r"\b(" + "|".join(ABBREVS) + r")\.", re.I)
_EG_RE = re.compile(r"\b(?:e\.g|i\.e)\.", re.I)
_DECIMAL_RE = re.compile(r"(?<=\d)\.(?=\d)")
_INITIAL_RE = re.compile(r"\b([A-Z])\.(?=\s+[A-Z])")
_SPLIT_RE = re.compile(
    r"(?:(?<=[.!?])|(?<=[.!?][\"'”’)]))\s+(?=[\"'“‘(\[]?[A-Z0-9])"
)

TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)*|[^\W_]+(?:['’\-][^\W_]+)*")

STOPWORDS = frozenset(
    """a about above after again against all also am an and any are as at be because been
    before being below between both but by can could did do does doing down during each few
    for from further had has have having he her here hers herself him himself his how i if in
    into is it its itself just me more most my myself no nor not now of off on once only or
    other our ours ourselves out over own same she should so some such than that the their
    theirs them themselves then there these they this those through to too under until up
    very was we were what when where which while who whom why will with would you your yours
    yourself yourselves one two three four five six seven eight nine ten many much may might
    must shall like make made makes often usually sometimes called known""".split()
)

# Generic words that make poor quiz answers (blocklist from the bible, Layer 3).
BLOCKLIST = frozenset(
    "thing things way ways people many lot lots kind kinds part parts type types example "
    "examples place places time times something anything everything someone year years".split()
)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split a passage into sentences, protecting abbreviations, initials and decimals."""
    t = normalize_space(text)
    if not t:
        return []
    t = _DECIMAL_RE.sub(_DOT, t)
    t = _EG_RE.sub(lambda m: m.group(0).replace(".", _DOT), t)
    t = _ABBR_RE.sub(lambda m: m.group(0).replace(".", _DOT), t)
    t = _INITIAL_RE.sub(lambda m: m.group(0).replace(".", _DOT), t)
    parts = _SPLIT_RE.split(t)
    return [p.replace(_DOT, ".").strip() for p in parts if p.strip()]


def iter_tokens(text: str) -> Iterator[tuple[str, int, int]]:
    """Yield (token, start, end) for every word or number token."""
    for m in TOKEN_RE.finditer(text):
        yield m.group(0), m.start(), m.end()


def tokens(text: str) -> list[str]:
    return [t for t, _, _ in iter_tokens(text)]


def stem(word: str) -> str:
    """A deliberately light stemmer, good enough for overlap checks."""
    w = word.lower().strip("'’-")
    if w.endswith("'s") or w.endswith("’s"):
        w = w[:-2]
    if w.isdigit() or len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("sses"):
        return w[:-2]
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    if w.endswith("es") and len(w) > 4 and (w[-3] in "sxz" or w.endswith(("ches", "shes"))):
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def is_number(tok: str) -> bool:
    return bool(tok) and tok[0].isdigit()


def is_content(tok: str) -> bool:
    low = tok.lower()
    if is_number(tok):
        return True
    return len(low) >= 3 and low not in STOPWORDS


def content_stems(text: str) -> list[str]:
    return [stem(t) for t in tokens(text) if is_content(t)]


def find_span(sentence: str, term: str) -> tuple[int, int] | None:
    """Return (start, end) of the first WHOLE-TOKEN occurrence of term in sentence.

    Whole-token matters: "art" must not match inside "party", "100" not inside "1000".
    Multi-token terms match as a token sequence (case-insensitive).
    """
    want = [t.lower() for t in tokens(term)]
    if not want:
        return None
    toks = [(t.lower(), s, e) for t, s, e in iter_tokens(sentence)]
    n = len(want)
    for i in range(len(toks) - n + 1):
        if [toks[i + k][0] for k in range(n)] == want:
            return toks[i][1], toks[i + n - 1][2]
    return None


def contains_term(text: str, term: str) -> bool:
    return find_span(text, term) is not None


def blank_term(sentence: str, term: str, blank: str = "_____") -> str:
    """Replace every whole-token occurrence of term (case-insensitive) with a blank."""
    want = [t.lower() for t in tokens(term)]
    n = len(want)
    if n == 0:
        return sentence
    toks = list(iter_tokens(sentence))
    out, last, i = [], 0, 0
    while i < len(toks):
        if [t.lower() for t, _, _ in toks[i:i + n]] == want:
            out.append(sentence[last:toks[i][1]])
            out.append(blank)
            last = toks[i + n - 1][2]
            i += n
        else:
            i += 1
    out.append(sentence[last:])
    return "".join(out)


def normalize_answer(ans: str) -> str:
    """Lowercase, drop punctuation and articles, collapse spaces. Unicode-aware.

    "Oxygen." -> "oxygen"; "the Oxygen" -> "oxygen"; "1,000" -> "1000".
    """
    toks = [t.lower().replace(",", "") for t in tokens(ans)]
    return " ".join(t for t in toks if t not in ("a", "an", "the"))
