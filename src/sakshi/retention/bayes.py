"""Which misconception does the student hold? Bayes' rule over a concept's misconceptions.

Hypotheses for one concept (uniform prior):
  * each of its misconceptions m,
  * NONE   - the student knows the idea (right answer, except for an occasional slip),
  * RANDOM - the student has no idea and guesses: every option 1/n.
Without RANDOM, a guesser who happens to hit a tagged option twice looks like proof of a belief
(simulation: 34-85% of pure guessers got a belief "confirmed"). With it, a tagged pick only counts
as much as it beats chance.

Likelihood of the option the student picked:
  * RANDOM:                              1/n for every option
  * NONE:                                correct 1 - p_slip, wrong options share p_slip
  * m, m tagged on this question:        m's option(s) share p_pick_own (0.5); every other option shares the rest
  * m, m not on this question:           1/n (the question says nothing about m; same as RANDOM)
So an untagged wrong pick or a right answer never raises a misconception relative to RANDOM.

Naming a belief (confirmed): posterior >= `confirm` (0.8) AND the student picked that misconception's
options at least `min_picks` (2) times, more often than any other misconception's. Otherwise we abstain
("not sure yet") - there is no weaker "possible misconception" label in the quiz.

Next question: the one with the highest expected information gain.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .bank import Question

NONE = "NONE"
RANDOM = "RANDOM"
SPECIAL = (NONE, RANDOM)


@dataclass(frozen=True)
class BayesParams:
    p_pick_own: float = 0.50       # holds m and m is on the question: total chance of picking m's option(s)
    p_slip: float = 0.15           # knows it (NONE) but picks a wrong option
    confirm: float = 0.80          # posterior needed to name a belief
    min_picks: int = 2             # ...and at least this many picks of that belief's options
    suspect: float = 0.50          # review day only: P(still holds) at or above this keeps a belief "still held"


def likelihood(q: Question, picked: str, hypothesis: str, params: BayesParams = BayesParams()) -> float:
    n = len(q.options)
    opt = q.option(picked)
    if opt is None or hypothesis == RANDOM:
        return 1.0 / n
    if hypothesis == NONE:
        wrong = n - 1
        return 1 - params.p_slip if opt.correct else params.p_slip / max(1, wrong)
    owned = [o for o in q.options if not o.correct and o.misconception == hypothesis]
    if not owned:
        return 1.0 / n
    if opt.misconception == hypothesis and not opt.correct:
        return params.p_pick_own / len(owned)
    return (1 - params.p_pick_own) / max(1, n - len(owned))


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
    picks: dict[str, int] = field(default_factory=dict)  # misconception -> times its option was picked

    def __post_init__(self):
        if not self.posterior:
            hs = list(self.hypotheses) + list(SPECIAL)
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
        opt = q.option(picked)
        if opt is not None and not opt.correct and opt.misconception in self.posterior:
            self.picks[opt.misconception] = self.picks.get(opt.misconception, 0) + 1

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
        """Most likely real misconception (never NONE or RANDOM) and its probability."""
        real = {h: p for h, p in self.posterior.items() if h not in SPECIAL}
        if not real:
            return NONE, 0.0
        h = max(real, key=real.get)
        return h, real[h]

    def confirmed(self) -> str | None:
        """The belief to name, or None ("not sure yet"): high posterior AND repeated, consistent picks."""
        h, p = self.top()
        k = self.picks.get(h, 0)
        others = max((v for m, v in self.picks.items() if m != h), default=0)
        if p >= self.params.confirm and k >= self.params.min_picks and k > others:
            return h
        return None

    def suspected(self) -> str | None:
        """The quiz abstains rather than naming a weaker 'possible' belief. Kept for API compatibility."""
        return None
