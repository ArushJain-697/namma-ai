"""The revision plan: which concept is most at risk today?

  priority(C, t) = 1 - P_mastery(C) x R_fsrs(C, t)

High when the student probably never learned it (low mastery) or has probably forgotten it (low recall).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fsrs import Scheduler

from .fsrs_sched import due, retrievability
from .state import LearnerState


@dataclass
class PlanRow:
    concept: str
    name: str
    mastery: float
    recall: float
    priority: float
    due: datetime | None


def revision_plan(state: LearnerState, names: dict[str, str], scheduler: Scheduler, now: datetime) -> list[PlanRow]:
    rows = []
    for cid, cs in state.concepts.items():
        r = retrievability(scheduler, cs.fsrs_card, now)
        rows.append(PlanRow(cid, names.get(cid, cid), cs.p_mastery, r, 1 - cs.p_mastery * r, due(cs.fsrs_card)))
    return sorted(rows, key=lambda x: (-x.priority, x.concept))
