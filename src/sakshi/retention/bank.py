"""A question bank: the passage, a summary, concepts (with prerequisites and misconceptions) and questions.

This is the contract between the model and the engine. The model writes it; the engine only reads it.
Model output is messy, so `load_bank` repairs what it safely can and records every repair in
`bank.notes` instead of crashing:

  * a question whose concept is unknown, or without exactly one correct option, is dropped;
  * a prerequisite that is unknown, or that would make a cycle, is dropped;
  * a wrong option's misconception may be an id ("C1M2") or free text. Free text is matched to the
    concept's list by similarity, and becomes a new misconception if nothing is close enough.
"""
from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field

MATCH_RATIO = 0.8  # free-text misconceptions this similar are treated as the same one


@dataclass
class Misconception:
    id: str
    concept: str
    text: str
    fix: str = ""


@dataclass
class Option:
    key: str
    text: str
    correct: bool
    misconception: str | None = None  # a Misconception id after loading


@dataclass
class Question:
    id: str
    concept: str
    type: str  # recall | application
    stem: str
    options: list[Option]
    explanation: str = ""

    @property
    def correct_key(self) -> str:
        return next(o.key for o in self.options if o.correct)

    def option(self, key: str) -> Option | None:
        return next((o for o in self.options if o.key == key.upper()), None)


@dataclass
class Concept:
    id: str
    name: str
    prereqs: list[str]
    misconceptions: list[str] = field(default_factory=list)  # Misconception ids


@dataclass
class Bank:
    title: str
    passage: str
    summary: str
    concepts: dict[str, Concept]
    questions: dict[str, Question]
    misconceptions: dict[str, Misconception]
    notes: list[str] = field(default_factory=list)

    def questions_for(self, concept_id: str) -> list[Question]:
        return [q for q in self.questions.values() if q.concept == concept_id]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def _creates_cycle(prereqs: dict[str, list[str]], child: str, parent: str) -> bool:
    """Would adding child -> parent (child needs parent) create a cycle? True if parent already needs child."""
    stack, seen = [parent], set()
    while stack:
        c = stack.pop()
        if c == child:
            return True
        if c in seen:
            continue
        seen.add(c)
        stack.extend(prereqs.get(c, []))
    return False


def bank_from_dict(d: dict) -> Bank:
    notes: list[str] = []
    concepts: dict[str, Concept] = {}
    miscs: dict[str, Misconception] = {}

    for c in d.get("concepts", []):
        cid = str(c.get("id", "")).strip()
        if not cid or cid in concepts:
            notes.append(f"dropped a concept with a missing or repeated id: {c.get('name')!r}")
            continue
        concepts[cid] = Concept(cid, str(c.get("name", cid)), [])
        for i, m in enumerate(c.get("misconceptions", []) or []):
            m = m if isinstance(m, dict) else {"text": str(m)}
            mid = str(m.get("id") or f"{cid}M{i + 1}")
            if mid in miscs:
                mid = f"{cid}M{len(miscs) + 1}"
            miscs[mid] = Misconception(mid, cid, str(m.get("text", "")).strip(), str(m.get("fix", "")).strip())
            concepts[cid].misconceptions.append(mid)

    # Prerequisites, in order, skipping unknown ids and anything that would close a cycle.
    accepted: dict[str, list[str]] = {cid: [] for cid in concepts}
    for c in d.get("concepts", []):
        cid = str(c.get("id", "")).strip()
        if cid not in concepts:
            continue
        for p in c.get("prereqs", []) or []:
            p = str(p)
            if p not in concepts or p == cid:
                notes.append(f"{cid}: dropped unknown prerequisite {p!r}")
            elif _creates_cycle(accepted, cid, p):
                notes.append(f"{cid}: dropped prerequisite {p} (it would make a cycle)")
            elif p not in accepted[cid]:
                accepted[cid].append(p)
        concepts[cid].prereqs = accepted[cid]

    def resolve(cid: str, ref) -> str | None:
        if ref is None or str(ref).strip() == "":
            return None
        ref = str(ref).strip()
        if ref in miscs and miscs[ref].concept == cid:
            return ref
        best, best_r = None, 0.0
        for mid in concepts[cid].misconceptions:
            r = difflib.SequenceMatcher(None, _norm(ref), _norm(miscs[mid].text)).ratio()
            if r > best_r:
                best, best_r = mid, r
        if best and best_r >= MATCH_RATIO:
            return best
        mid = f"{cid}M{len(concepts[cid].misconceptions) + 1}"
        while mid in miscs:
            mid += "x"
        miscs[mid] = Misconception(mid, cid, ref)
        concepts[cid].misconceptions.append(mid)
        return mid

    questions: dict[str, Question] = {}
    for q in d.get("questions", []):
        qid, cid = str(q.get("id", "")).strip(), str(q.get("concept", "")).strip()
        if not qid or qid in questions:
            notes.append(f"dropped a question with a missing or repeated id: {q.get('stem')!r}")
            continue
        if cid not in concepts:
            notes.append(f"{qid}: dropped (unknown concept {cid!r})")
            continue
        raw = q.get("options", []) or []
        if sum(bool(o.get("correct")) for o in raw) != 1 or len(raw) < 2:
            notes.append(f"{qid}: dropped (needs at least 2 options and exactly one correct)")
            continue
        opts = []
        for i, o in enumerate(raw):
            key = str(o.get("key") or "ABCDEFG"[i]).strip().upper()
            correct = bool(o.get("correct"))
            opts.append(Option(key, str(o.get("text", "")).strip(), correct,
                               None if correct else resolve(cid, o.get("misconception"))))
        qtype = str(q.get("type", "recall")).lower()
        if qtype not in ("recall", "application"):
            notes.append(f"{qid}: unknown type {qtype!r}, treated as recall")
            qtype = "recall"
        questions[qid] = Question(qid, cid, qtype, str(q.get("stem", "")).strip(), opts, str(q.get("explanation", "")).strip())

    for cid in concepts:
        if not any(q.concept == cid for q in questions.values()):
            notes.append(f"{cid}: has no questions")
    return Bank(str(d.get("title", "")), str(d.get("passage", "")), str(d.get("summary", "")),
                concepts, questions, miscs, notes)


def load_bank(path: str) -> Bank:
    with open(path, encoding="utf-8") as f:
        return bank_from_dict(json.load(f))
