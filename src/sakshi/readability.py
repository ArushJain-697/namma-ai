"""Readability: a rough Flesch-Kincaid grade. English only, standard library only.

The bible says to treat this as a WARN-level guide: readability formulas correlate
poorly with human judgement on short texts. Never present it as a verdict.
"""
from __future__ import annotations

import re

from .text import split_sentences, tokens

_VOWELS = "aeiouy"


def count_syllables(word: str) -> int:
    """Heuristic syllable count. Never raises: digits and hyphenated words are handled."""
    w = word.lower()
    if not w:
        return 0
    if w[0].isdigit():
        return max(1, len(re.sub(r"\D", "", w)) // 2 + 1)
    if "-" in w:
        return sum(count_syllables(p) for p in w.split("-") if p) or 1
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return 1
    count, prev_vowel = 0, False
    for ch in w:
        is_v = ch in _VOWELS
        if is_v and not prev_vowel:
            count += 1
        prev_vowel = is_v
    if w.endswith("e") and not w.endswith(("le", "ee")) and count > 1:
        count -= 1
    return max(1, count)


def avg_sentence_len(text: str) -> float:
    sents = split_sentences(text)
    if not sents:
        return 0.0
    return sum(len(tokens(s)) for s in sents) / len(sents)


def fk_grade(text: str) -> float:
    """Flesch-Kincaid grade level. Returns 0.0 for empty text."""
    words = tokens(text)
    sents = split_sentences(text)
    if not words or not sents:
        return 0.0
    syl = sum(count_syllables(w) for w in words)
    return 0.39 * (len(words) / len(sents)) + 11.8 * (syl / len(words)) - 15.59
