"""Bayesian Knowledge Tracing: how likely is it that the student has really learned a concept?

It separates real learning from lucky guesses and careless slips:
  correct:  P(L | obs) = P(L)(1-s) / (P(L)(1-s) + (1-P(L)) g)
  wrong:    P(L | obs) = P(L) s     / (P(L) s     + (1-P(L))(1-g))
  then:     P(L) = P(L | obs) + (1 - P(L | obs)) * T        (a chance to learn from the attempt)
Application questions are harder to guess, so they use a lower guess rate.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.3     # chance the student already knows a concept before any question
    p_learn: float = 0.2    # chance of learning it from one attempt plus feedback (T)
    p_slip: float = 0.1     # knows it but answers wrong (s)
    p_guess: float = 0.25   # does not know it but guesses right: 1 in 4 options (g)
    p_guess_application: float = 0.15
    implicit_share: float = 0.5  # a correct application answer gives each prerequisite this share of p_learn


def update(p: float, correct: bool, params: BKTParams = BKTParams(), application: bool = False) -> float:
    s = params.p_slip
    g = params.p_guess_application if application else params.p_guess
    if correct:
        post = p * (1 - s) / (p * (1 - s) + (1 - p) * g)
    else:
        post = p * s / (p * s + (1 - p) * (1 - g))
    return post + (1 - post) * params.p_learn


def implicit_credit(p: float, params: BKTParams = BKTParams()) -> float:
    """A small bump for a prerequisite when the student correctly applies the idea built on it."""
    return p + (1 - p) * params.p_learn * params.implicit_share
