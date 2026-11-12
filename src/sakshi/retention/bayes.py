"""Which misconception does the student hold? Bayes' rule over a concept's misconceptions.

Hypotheses for one concept: each of its misconceptions, plus NONE ("no specific misconception; they
just didn't know or slipped"). Without NONE, any random wrong answer would look like proof of some
misconception. The prior is uniform.

Likelihood of what the student picked, if they hold misconception m (hand-set, see config):
  * m is one of this question's wrong options:  that option 0.70, correct 0.15, other wrong options share 0.15
  * m is not on this question:                   every option equally likely (the question says nothing about m)
  * NONE:                                        correct 0.50, wrong options share 0.50

Next question: the one with the highest expected information gain, i.e. the one whose answer we expect
to shrink our uncertainty (entropy) the most.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .bank import Question

NONE = "NONE"


@dataclass(frozen=True)
class BayesParams:
    p_pick_own: float = 0.70       # holds m and m is on the question: picks m's option
    p_correct_holding: float = 0.15
    p_correct_none: float = 0.50
    confirm: float = 0.75          # posterior needed to say "misconception detected"
    suspect: float = 0.50          # posterior needed to mention it as "possible"


def likelihood(q: Question, picked: str, hypothesis: str, params: BayesParams = BayesParams()) -> float:
    n = len(q.options)
    wrong = [o for o in q.options if not o.correct]
    opt = q.option(picked)
    if opt is None:
        return 1.0 / n
    if hypothesis == NONE:
        return params.p_correct_none if opt.correct else (1 - params.p_correct_none) / max(1, len(wrong))
    owned = [o for o in wrong if o.misconception == hypothesis]
    if not owned:
        return 1.0 / n
    if opt.correct:
        return params.p_correct_holding
    if opt.misconception == hypothesis:
        return params.p_pick_own / len(owned)
    others = len(wrong) - len(owned)
    return (1 - params.p_pick_own - params.p_correct_holding) / others if others else 1e-6


def entropy(dist: dict[str, float]) -> float:
    return -sum(p * math.log2(p) for p in dist.values() if p > 0)


@dataclass
class Diagnosis:
    """The posterior over one concept's misconceptions, updated after every answer on that concept."""
    concept: str
    hypotheses: list[str]
    params: BayesParams = BayesParams()
    posterior: dict[str, float] = field(default_factory=dict)
    evidence: int = 0

    def __post_init__(self):
        if not self.posterior:
            hs = list(self.hypotheses) + [NONE]
            self.posterior = {h: 1.0 / len(hs) for h in hs}

    def predict(self, q: Question) -> dict[str, float]:
        """Probability of each option being picked, under the current posterior."""
        return {o.key: sum(p * likelihood(q, o.key, h, self.params) for h, p in self.posterior.items()) for o in q.options}

    def _updated(self, q: Question, picked: str) -> dict[str, float]:
        un = {h: p * likelihood(q, picked, h, self.params) for h, p in self.posterior.items()}
        z = sum(un.values()) or 1.0
        return {h: v / z for h, v in un.items()}

    def update(self, q: Question, picked: str) -> None:
        self.posterior = self._updated(q, picked)
        self.evidence += 1

    def expected_gain(self, q: Question) -> float:
        before = entropy(self.posterior)
        pred = self.predict(q)
        after = sum(p_o * entropy(self._updated(q, k)) for k, p_o in pred.items() if p_o > 0)
        return before - after

    def best_question(self, candidates: list[Question]) -> Question | None:
        if not candidates:
            return None
        return max(candidates, key=lambda q: round(self.expected_gain(q), 9))  # ties: first in the list wins

    def top(self) -> tuple[str, float]:
        """Most likely real misconception (never NONE) and its probability."""
        real = {h: p for h, p in self.posterior.items() if h != NONE}
        if not real:
            return NONE, 0.0
        h = max(real, key=real.get)
        return h, real[h]

    def confirmed(self) -> str | None:
        h, p = self.top()
        return h if p >= self.params.confirm else None

    def suspected(self) -> str | None:
        h, p = self.top()
        return h if self.params.suspect <= p < self.params.confirm else None
