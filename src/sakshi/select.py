"""Layer 3: answer and witness selection (relevant ideas only). Code decides, never the model.

For every sentence we find the best answer term, score it with independent relevance
signals, and keep the top few. Each candidate carries its witness sentence index, so
"no witness, no question" is true by construction.

Signals (bible Layer 3, thresholds are DESIGN and must be tuned on the dev set only):
  repeat   the term's stem appears in two or more sentences
  central  the term sits in one of the sentences code ranked most central
  topic    the sentence also contains the passage's topic word (term is not the topic)
  type     numbers and mid-sentence capitalised names make clean, checkable answers
A candidate is "relevant" if any of repeat/central/topic fired. If it passed on type
alone it is a "detail" question and is tiered AMBER later.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .lexicon import PLAIN_WORDS
from .text import BLOCKLIST, STOPWORDS, is_content, is_number, iter_tokens, split_sentences, stem

MIN_SENTENCE_TOKENS = 5
RELEVANCE_SIGNALS = ("repeat", "central", "topic")


@dataclass
class Candidate:
    term: str
    sent_idx: int
    score: float
    signals: tuple[str, ...]
    kind: str  # number | name | word
    relevant: bool
    detail: bool
    reserve: str | None = None


@dataclass
class Analysis:
    sentences: list[str]
    topic: str
    central: list[int]  # indices of the most central sentences, in passage order
    central_ranked: list[int] = field(default_factory=list)  # same sentences, most central first
    candidates: list[Candidate] = field(default_factory=list)
    per_sentence: dict[int, Candidate] = field(default_factory=dict)  # best term of EVERY usable sentence (eval forcing)


def _sentence_tokens(sentence: str) -> list[tuple[str, int]]:
    return [(t, i) for i, (t, _, _) in enumerate(iter_tokens(sentence))]


def analyse(passage: str, n_candidates: int = 6, n_central: int = 3) -> Analysis:
    sents = split_sentences(passage)
    per_sent_toks = [[t for t, _, _ in iter_tokens(s)] for s in sents]

    total: Counter[str] = Counter()
    sent_freq: Counter[str] = Counter()
    sent_stems: list[set[str]] = []
    for toks in per_sent_toks:
        stems = [stem(t) for t in toks if is_content(t) and not is_number(t)]
        total.update(stems)
        sent_freq.update(set(stems))
        sent_stems.append(set(stems))

    topic = ""
    if total:
        best = max(total.items(), key=lambda kv: (kv[1], -min(
            (i for i, ss in enumerate(sent_stems) if kv[0] in ss), default=0)))
        topic = best[0]

    # Sentence centrality: unique content stems weighted by passage frequency.
    cent_scores: list[float] = []
    for i, ss in enumerate(sent_stems):
        base = sum(total[s] for s in ss) / (len(ss) ** 0.5) if ss else 0.0
        base += 2.0 if topic in ss else 0.0
        base += 1.0 if i == 0 else 0.0
        cent_scores.append(base)
    usable = [i for i, toks in enumerate(per_sent_toks) if len(toks) >= MIN_SENTENCE_TOKENS]
    ranked = sorted(usable, key=lambda i: (-cent_scores[i], i))
    central = sorted(ranked[:n_central])
    central_set = set(central)

    best_per_sentence: list[Candidate] = []
    for i, toks in enumerate(per_sent_toks):
        if len(toks) < MIN_SENTENCE_TOKENS:
            continue
        scored: list[tuple[float, int, str, str, tuple[str, ...]]] = []
        for pos, tok in enumerate(toks):
            low = tok.lower()
            if low in STOPWORDS or low in BLOCKLIST or not is_content(tok):
                continue
            kind = "number" if is_number(tok) else ("name" if tok[0].isupper() and pos > 0 else "word")
            st = stem(tok)
            plain = kind == "word" and (low in PLAIN_WORDS or st in PLAIN_WORDS)
            sig: list[str] = []
            if kind != "number" and not plain and sent_freq[st] >= 2:
                sig.append("repeat")
            if i in central_set:
                sig.append("central")
            if topic and topic in sent_stems[i] and st != topic:
                sig.append("topic")
            if kind in ("number", "name"):
                sig.append("type")
            if not sig:
                continue
            score = (2.0 * ("repeat" in sig) + 1.5 * ("central" in sig) + 0.5 * ("topic" in sig)
                     + 2.0 * ("type" in sig) + 0.5 * (pos / max(1, len(toks))))
            if plain:
                score -= 3.0  # everyday words make weak answers
            if kind == "word" and pos < 3:
                score -= 1.0
            if st == topic:
                score -= 2.0
            scored.append((score, pos, tok, kind, tuple(sig)))
        if not scored:
            continue
        scored.sort(key=lambda x: (-x[0], -x[1]))
        score, pos, tok, kind, sig = scored[0]
        is_plain = kind == "word" and (tok.lower() in PLAIN_WORDS or stem(tok) in PLAIN_WORDS)
        relevant = (not is_plain) and any(s in sig for s in ("repeat", "central"))
        reserve = None
        for _, _, rtok, _, _ in scored[1:]:
            if stem(rtok) != stem(tok):
                reserve = rtok
                break
        best_per_sentence.append(Candidate(tok, i, round(score, 3), sig, kind, relevant,
                                           detail=(not relevant), reserve=reserve))

    per_sentence = {c.sent_idx: c for c in best_per_sentence}
    best_per_sentence.sort(key=lambda c: (-c.score, c.sent_idx))
    chosen: list[Candidate] = []
    used: set[str] = set()
    for c in best_per_sentence:
        if stem(c.term) in used:
            continue
        used.add(stem(c.term))
        chosen.append(c)
        if len(chosen) >= n_candidates:
            break
    return Analysis(sents, topic, central, central_ranked=ranked[:max(n_central, 4)], candidates=chosen, per_sentence=per_sentence)
