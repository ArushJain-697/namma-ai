"""The concept graph: each concept lists the simpler ideas (prerequisites) it builds on.

Wrong on a concept -> walk DOWN to its prerequisites. Right at the base -> climb back UP.
The bank loader already removed unknown prerequisites and cycles, so this is a DAG.
"""
from __future__ import annotations

from functools import lru_cache

from .bank import Bank


class ConceptGraph:
    def __init__(self, bank: Bank):
        self.bank = bank
        self.order = list(bank.concepts)  # the model lists concepts basic -> advanced
        self._prereqs = {cid: list(c.prereqs) for cid, c in bank.concepts.items()}
        self._parents = {cid: [] for cid in bank.concepts}
        for cid, ps in self._prereqs.items():
            for p in ps:
                self._parents[p].append(cid)
        self.level = lru_cache(maxsize=None)(self._level)

    def prereqs(self, cid: str) -> list[str]:
        return self._prereqs[cid]

    def parents(self, cid: str) -> list[str]:
        """Concepts that build directly on this one."""
        return self._parents[cid]

    def _level(self, cid: str) -> int:
        """0 for a basic concept; otherwise one more than its deepest prerequisite."""
        ps = self._prereqs[cid]
        return 0 if not ps else 1 + max(self.level(p) for p in ps)

    def tops(self) -> list[str]:
        """Concepts nothing builds on, most advanced first. The quiz starts here."""
        tops = [c for c in self.order if not self._parents[c]]
        return sorted(tops, key=lambda c: (-self.level(c), self.order.index(c)))

    def below(self, cid: str) -> set[str]:
        """Every concept this one depends on, directly or not."""
        out, stack = set(), list(self._prereqs[cid])
        while stack:
            c = stack.pop()
            if c not in out:
                out.add(c)
                stack.extend(self._prereqs[c])
        return out
