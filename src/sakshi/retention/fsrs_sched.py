"""When should each concept be revised? One FSRS card per concept, scheduled by the py-fsrs library.

We do not reimplement FSRS. Two settings differ from the library defaults:
  * no minute-scale learning steps: a school student revises across days, not minutes;
  * no random fuzzing, so the demo and tests give the same dates every time.
Only ONE review per concept per session is recorded (FSRS models day-scale memory; what happens inside a
session is the Bayes and graph engine's job). The rating is the concept's final outcome in the session.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fsrs import Card, Rating, Scheduler

OUTCOME_RATING = {
    "again": Rating.Again,  # still wrong at the end
    "hard": Rating.Hard,    # right only after the explanation or the walk down
    "good": Rating.Good,    # right first time (recall), or implicitly shown by applying a harder idea
    "easy": Rating.Easy,    # right first time on an application question
}


def make_scheduler(desired_retention: float = 0.9) -> Scheduler:
    return Scheduler(desired_retention=desired_retention, learning_steps=(), relearning_steps=(), enable_fuzzing=False)


def review(scheduler: Scheduler, card_dict: dict | None, outcome: str, when: datetime) -> dict:
    card = Card.from_dict(card_dict) if card_dict else Card()
    card, _ = scheduler.review_card(card, OUTCOME_RATING[outcome], when)
    return card.to_dict()


def retrievability(scheduler: Scheduler, card_dict: dict | None, when: datetime) -> float:
    """Chance the student can still recall the concept at `when` (0 for a concept never reviewed)."""
    if not card_dict:
        return 0.0
    return scheduler.get_card_retrievability(Card.from_dict(card_dict), when)


def due(card_dict: dict | None) -> datetime | None:
    return Card.from_dict(card_dict).due if card_dict else None


def days_until(card_dict: dict | None, now: datetime) -> float | None:
    d = due(card_dict)
    return None if d is None else (d - now) / timedelta(days=1)
