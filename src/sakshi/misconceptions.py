"""The misconception library on the device: find the topic and misconceptions that fit a passage, with no model.

The library (data/misconceptions/library.jsonl + concepts.jsonl) is built once, offline, by
scripts/build_misconception_library.py. Here we only read it and rank it against a passage with BM25 (the classic
keyword-ranking formula), using the repo's own tokenizer and stemmer. Standard library only; a few milliseconds.

  lib = Library.load()
  match = lib.match(passage)          # best topics, then the misconceptions of the best topic(s)
  match.topics[0].topic_id, [m["id"] for m in match.misconceptions]
"""
from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .text import content_stems

DEFAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "misconceptions")


def _doc_terms(m: dict, topic_title: str) -> list[str]:
    """Words that describe one misconception. Trigger cues and names count double: they are chosen to appear in
    passages, while the statement and fix contain the wrong idea and the right one."""
    cues = " ".join(m.get("trigger_cues") or [])
    return (content_stems(cues) * 2 + content_stems(f"{topic_title} {m.get('concept', '')}") * 2
            + content_stems(m.get("statement", "")) + content_stems(m.get("fix", "")))


@dataclass
class TopicHit:
    topic_id: str
    title: str
    score: float


@dataclass
class Match:
    topics: list[TopicHit]
    misconceptions: list[dict]
    concepts: list[dict] = field(default_factory=list)


class Library:
    def __init__(self, misconceptions: list[dict], concepts: list[dict], include_held_out: bool = True):
        self.items = [m for m in misconceptions if not m.get("duplicate_of") and (include_held_out or not m.get("held_out"))]
        self.by_id = {m["id"]: m for m in self.items}
        self.concepts = {c["id"]: c for c in concepts}
        self.docs = [Counter(_doc_terms(m, m.get("topic", ""))) for m in self.items]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 1.0
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    @classmethod
    def load(cls, directory: str = DEFAULT_DIR, include_held_out: bool = True) -> "Library":
        def read(name):
            path = os.path.join(directory, name)
            with open(path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        return cls(read("library.jsonl"), read("concepts.jsonl"), include_held_out)

    def _scores(self, passage: str, k1: float = 1.2, b: float = 0.75) -> list[float]:
        q = Counter(content_stems(passage))
        out = []
        for doc, length in zip(self.docs, self.lengths):
            s = 0.0
            for t in q:
                tf = doc.get(t)
                if tf:
                    s += self.idf[t] * tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / self.avg_len))
            out.append(s)
        return out

    def match(self, passage: str, n_topics: int = 3, n_misconceptions: int = 8, topic_share: float = 0.6) -> Match:
        """Rank topics by the sum of their best three misconception scores; return the top topics and the best
        misconceptions from topics scoring at least `topic_share` of the best topic."""
        scores = self._scores(passage)
        per_topic: dict[str, list[float]] = defaultdict(list)
        for m, s in zip(self.items, scores):
            per_topic[m["topic_id"]].append(s)
        titles = {m["topic_id"]: m.get("topic", "") for m in self.items}
        ranked = sorted(((sum(sorted(v, reverse=True)[:3]), t) for t, v in per_topic.items()), reverse=True)
        topics = [TopicHit(t, titles[t], round(s, 2)) for s, t in ranked[:n_topics] if s > 0]
        if not topics:
            return Match([], [])
        keep = {t.topic_id for t in topics if t.score >= topic_share * topics[0].score}
        best = sorted(((s, m) for m, s in zip(self.items, scores) if m["topic_id"] in keep and s > 0),
                      key=lambda x: -x[0])[:n_misconceptions]
        mis = [m for _, m in best]
        concept_ids = []
        for m in mis:
            if m["concept_id"] not in concept_ids:
                concept_ids.append(m["concept_id"])
        return Match(topics, mis, [self.concepts[c] for c in concept_ids if c in self.concepts])
