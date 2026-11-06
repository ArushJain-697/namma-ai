"""Layer 1: passage gate. Is this passage usable?

The brief says "approximately 150-300 words", so we warn inside a 10% margin and
reject beyond it, always with a stated reason. Code decides; no model involved.
"""
from __future__ import annotations

from dataclasses import dataclass

from .text import tokens

LO, HI, MARGIN = 150, 300, 0.10


@dataclass
class GateResult:
    status: str  # OK | WARN | REJECTED
    words: int
    reason: str

    @property
    def ok(self) -> bool:
        return self.status != "REJECTED"


def check_passage(text: str, lo: int = LO, hi: int = HI, margin: float = MARGIN, override: bool = False) -> GateResult:
    n = len(tokens(text or ""))
    if n == 0:
        return GateResult("REJECTED", 0, "REJECTED: empty passage")
    if override:
        return GateResult("WARN", n, f"OVERRIDE: {n} words accepted for testing")
    if lo <= n <= hi:
        return GateResult("OK", n, f"OK: {n} words")
    soft_lo, soft_hi = int(lo * (1 - margin)), int(hi * (1 + margin))
    if soft_lo <= n <= soft_hi:
        return GateResult("WARN", n, f"WARN: {n} words, expected {lo}-{hi} (inside the {int(margin*100)}% margin)")
    return GateResult("REJECTED", n, f"REJECTED: {n} words, need {lo}-{hi}")
