"""Bayesian Knowledge Tracing: how likely is it that the student has really learned a concept?

It separates real learning from lucky guesses and careless slips:
  correct:  P(L | obs) = P(L)(1-s) / (P(L)(1-s) + (1-P(L)) g)
  wrong:    P(L | obs) = P(L) s     / (P(L) s     + (1-P(L))(1-g))
  then:     P(L) = P(L | obs) + (1 - P(L | obs)) * T        (a chance to learn from the attempt)

Guards against "one lucky answer = mastered":
  * guess floor: g is never below 1/n_options (a blind guess on a 3-option question is right 1 time in 3);
  * one answer can move P(L) by at most `max_step`, so from below 0.4 a single right answer cannot reach the
    0.7 climb threshold: it takes at least two;
  * `mastered()` also asks for at least 2 right answers among the concept's recent attempts.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.3     # chance the student already knows a concept before any question
    p_learn: float = 0.2    # chance of learning it from one attempt plus feedback (T)
    p_slip: float = 0.1     # knows it but answers wrong (s)
    p_guess: float = 0.25   # does not know it but guesses right (g); never below 1/n_options
    p_guess_application: float = 0.15
    max_step: float = 0.3   # most one answer may move P(L)
    min_correct: int = 2    # right answers (among the last `recent`) needed to call it mastered
    recent: int = 3
    implicit_share: float = 0.5  # a correct application answer gives each prerequisite this share of p_learn


def update(p: float, correct: bool, params: BKTParams = BKTParams(), application: bool = False,
           n_options: int | None = None) -> float:
    s = params.p_slip
    g = params.p_guess_application if application else params.p_guess
    if n_options:
        g = max(g, 1.0 / n_options)
    if correct:
        post = p * (1 - s) / (p * (1 - s) + (1 - p) * g)
    else:
        post = p * s / (p * s + (1 - p) * (1 - g))
    new = post + (1 - post) * params.p_learn
    return min(p + params.max_step, max(p - params.max_step, new))


def implicit_credit(p: float, params: BKTParams = BKTParams()) -> float:
    """A small bump for a prerequisite when the student correctly applies the idea built on it."""
    return p + (1 - p) * params.p_learn * params.implicit_share


def mastered(p: float, attempts: list[dict], concept: str, threshold: float, params: BKTParams = BKTParams()) -> bool:
    """P(L) at or above threshold AND at least `min_correct` right answers in the concept's last `recent` attempts."""
    mine = [a for a in attempts if a.get("concept") == concept][-params.recent:]
    return p >= threshold and sum(bool(a.get("correct")) for a in mine) >= params.min_correct
