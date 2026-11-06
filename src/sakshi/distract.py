"""Layer 5: wrong options. Code picks them from OTHER parts of the passage; the model never does.

Why not the model: multiple-correct-answer detection is unreliable even for large models
(bible, section 7), so we avoid creating the problem. Same-type terms only: numbers with
numbers, names with names, plain words with plain words.
"""
from __future__ import annotations

import random
from collections import Counter

from .lexicon import PLAIN_WORDS
from .text import STOPWORDS, BLOCKLIST, is_content, is_number, iter_tokens, split_sentences, stem


def _kind(tok: str, pos: int) -> str:
    if is_number(tok):
        return "number"
    if tok[0].isupper() and pos > 0:
        return "name"
    return "word"


def make_options(passage: str, key: str, witness_idx: int, kind: str, seed: int, n_wrong: int = 3) -> list[str] | None:
    """Return key plus n_wrong distractors, shuffled (numbers sorted), or None if too few exist.

    None means the item becomes a short-answer question with no options, and is labelled so.
    """
    sents = split_sentences(passage)
    if witness_idx >= len(sents):
        return None
    witness_stems = {stem(t) for t, _, _ in iter_tokens(sents[witness_idx])}
    key_stem = stem(key)

    freq: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    surface: dict[str, str] = {}
    order = 0
    for i, s in enumerate(sents):
        if i == witness_idx:
            continue
        for pos, (tok, _, _) in enumerate(iter_tokens(s)):
            low = tok.lower()
            if low in STOPWORDS or low in BLOCKLIST or not is_content(tok):
                continue
            if _kind(tok, pos) != kind:
                continue
            st = stem(tok)
            if st == key_stem or st in witness_stems:
                continue  # also excludes defensible alternative answers from the witness
            freq[st] += 1
            if st not in first_seen:
                first_seen[st] = order
                surface[st] = tok if kind == "name" else tok.lower()  # no capital-letter giveaway
            order += 1

    key_plain = kind == "word" and (key.lower() in PLAIN_WORDS or key_stem in PLAIN_WORDS)

    def plain(st: str) -> bool:
        return kind == "word" and (surface[st] in PLAIN_WORDS or st in PLAIN_WORDS)

    def ending(w: str) -> str:
        w = w.lower()
        return "ing" if w.endswith("ing") else "ed" if w.endswith("ed") else "s" if w.endswith("s") and not w.endswith("ss") else ""

    key_end = ending(key) if kind == "word" else ""

    # Prefer the same kind, the same plain/specific class and the same word-ending class as the key
    # (so an -ing form or a verb in -s is not the odd one out), then more frequent terms first.
    ranked = sorted(freq, key=lambda st: (plain(st) != key_plain,
                                          kind == "word" and ending(surface[st]) != key_end,
                                          -freq[st], first_seen[st]))
    if kind == "number":
        same_len = [st for st in ranked if len(st) == len(key)]
        ranked = same_len + [st for st in ranked if st not in same_len]
    # Sample from the best few with a per-item seed, so the same four words don't recur in every question.
    top = ranked[:max(n_wrong, 8)]
    if len(top) < n_wrong:
        return None
    rng = random.Random(seed)
    pool = [surface[st] for st in rng.sample(top, n_wrong)]
    options = pool + [key]
    if kind == "number":
        try:
            return sorted(options, key=lambda x: float(x.replace(",", "")))
        except ValueError:
            pass
    rng = random.Random(seed)
    rng.shuffle(options)
    return options
