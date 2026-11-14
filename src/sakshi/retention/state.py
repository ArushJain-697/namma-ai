"""The learner's saved state: mastery, FSRS card and misconceptions per concept, and every attempt.

Plain JSON, so a teacher (or a judge) can open it and read it.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field


@dataclass
class ConceptState:
    p_mastery: float
    fsrs_card: dict | None = None
    attempts: int = 0
    last_outcome: str | None = None


@dataclass
class MisconceptionState:
    concept: str
    text: str
    p_holds: float
    status: str  # confirmed | suspected | cleared
    last_checked: str


@dataclass
class LearnerState:
    bank_title: str = ""
    concepts: dict[str, ConceptState] = field(default_factory=dict)
    misconceptions: dict[str, MisconceptionState] = field(default_factory=dict)
    attempts: list[dict] = field(default_factory=list)
    sessions: int = 0
    blocked: dict[str, list[str]] = field(default_factory=dict)  # concept -> shaky prerequisites stopping the climb

    def ensure(self, concept_ids, p_init: float) -> None:
        for cid in concept_ids:
            self.concepts.setdefault(cid, ConceptState(p_init))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "LearnerState":
        return cls(d.get("bank_title", ""),
                   {k: ConceptState(**v) for k, v in d.get("concepts", {}).items()},
                   {k: MisconceptionState(**v) for k, v in d.get("misconceptions", {}).items()},
                   list(d.get("attempts", [])), int(d.get("sessions", 0)),
                   {k: list(v) for k, v in d.get("blocked", {}).items()})

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)  # never leave a half-written file behind

    @classmethod
    def load(cls, path: str) -> "LearnerState":
        if not os.path.exists(path):
            return cls()
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
