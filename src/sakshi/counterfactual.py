"""Counterfactual passages (build map T24): the data format, loader and validator.

A case is a passage with ONE planted fact that differs from what a model "remembers" (water boils at
90 degrees at the hill station in the story). Format, per case `<id>`:
  data/counterfactual/<id>.txt    the passage
  data/counterfactual/<id>.json   {"planted": {"sentence_idx": 1, "passage_value": "90 degrees Celsius",
                                               "memory_value": "100 degrees Celsius", "type": "number"},
                                   "split": "dev" | "heldout", "note": "..."}
sentence_idx is 0-based, as split by sakshi.text.split_sentences. The held-out half is written and KEPT by
its owner; nobody tunes on it (bible section 10).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from .gate import check_passage
from .text import contains_term, is_number, split_sentences, tokens

TYPES = ("number", "name", "word")
SPLITS = ("dev", "heldout")


@dataclass
class Case:
    id: str
    passage: str
    sentence_idx: int
    passage_value: str
    memory_value: str
    type: str
    split: str
    note: str = ""

    @property
    def sentence(self) -> str:
        return split_sentences(self.passage)[self.sentence_idx]


def _numbers(value: str) -> list[str]:
    return [t.replace(",", "") for t in tokens(value) if is_number(t)]


def value_matches(text: str, value: str) -> bool:
    """Does `text` contain `value`? Numbers match as whole numbers with units ignored ("90 degrees Celsius",
    "90°C" and "90" all match "90"); other values match as whole-token phrases. 100 never matches 1000."""
    nums = _numbers(value)
    if nums:
        have = {t.replace(",", "") for t in tokens(text) if is_number(t)}
        return all(n in have for n in nums)
    return contains_term(text, value)


def planted_term(case: Case) -> str | None:
    """The single term in the planted sentence that carries the planted value (the first number, or the phrase)."""
    nums = _numbers(case.passage_value)
    if nums:
        for t in tokens(case.sentence):
            if is_number(t) and t.replace(",", "") == nums[0]:
                return t
        return None
    return case.passage_value if contains_term(case.sentence, case.passage_value) else None


def validate(case: Case, allow_short: bool = False) -> list[str]:
    """Problems that would make a case meaningless. Empty list means usable."""
    out: list[str] = []
    sents = split_sentences(case.passage)
    if case.type not in TYPES:
        out.append(f"type must be one of {TYPES}")
    if case.split not in SPLITS:
        out.append(f"split must be one of {SPLITS}")
    if not (0 <= case.sentence_idx < len(sents)):
        return out + [f"sentence_idx {case.sentence_idx} is out of range (passage has {len(sents)} sentences)"]
    s = sents[case.sentence_idx]
    if not value_matches(s, case.passage_value):
        out.append(f"passage_value {case.passage_value!r} is not in the planted sentence")
    elif planted_term(case) is None:
        out.append("could not find a single term carrying the passage value")
    if value_matches(s, case.memory_value):
        out.append(f"memory_value {case.memory_value!r} appears in the planted sentence (it must differ)")
    if case.passage_value.strip().lower() == case.memory_value.strip().lower():
        out.append("passage_value and memory_value are the same")
    if not allow_short and not check_passage(case.passage).ok:
        out.append(check_passage(case.passage).reason)
    return out


def notes(case: Case) -> list[str]:
    """Not errors, but things a reader should know."""
    n = []
    if value_matches(case.passage, case.memory_value):
        n.append("memory_value also appears elsewhere in the passage: a plain 'is the answer in the passage' check "
                 "would NOT catch a memory answer for this case")
    return n


def load_cases(directory: str, split: str | None = None) -> list[Case]:
    cases: list[Case] = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json") or name.startswith("_") or name.startswith("kept"):
            continue
        cid = name[:-5]
        txt = os.path.join(directory, cid + ".txt")
        if not os.path.exists(txt):
            raise FileNotFoundError(f"{cid}.json has no matching {cid}.txt")
        with open(os.path.join(directory, name), encoding="utf-8") as f:
            meta = json.load(f)
        pl = meta["planted"]
        with open(txt, encoding="utf-8") as f:
            passage = f.read().strip()
        c = Case(cid, passage, int(pl["sentence_idx"]), str(pl["passage_value"]), str(pl["memory_value"]),
                 pl.get("type", "number"), meta.get("split", "dev"), meta.get("note", ""))
        if split is None or c.split == split:
            cases.append(c)
    return cases
