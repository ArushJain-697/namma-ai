"""Fast-forward N days: what does the student still remember with and without our revision schedule?

Both worlds start from the SAME cards the real session produced:
  * "Study once": no more reviews. Recall decays along each concept's FSRS forgetting curve.
  * "With our schedule": on each day a concept is due, the pretend student answers correctly with
    probability = their current recall chance (seeded, so runs repeat), and FSRS reschedules it.
Every number comes from py-fsrs's own forgetting model, not from a made-up curve.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fsrs import Card, Rating, Scheduler

from .state import LearnerState


@dataclass
class ReviewEvent:
    day: int
    concept: str
    recall_before: float
    correct: bool
    stability_after: float
    next_in_days: float


@dataclass
class SimResult:
    days: int
    times: list[float]                 # days since the session, for the curves
    once: list[float]                  # average recall chance, study once
    scheduled: list[float]             # average recall chance, with our schedule
    daily_once: list[float]            # at each day mark, before that day's reviews
    daily_scheduled: list[float]
    events: list[ReviewEvent] = field(default_factory=list)


def _avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def session_time(state: LearnerState) -> datetime | None:
    last = [Card.from_dict(c.fsrs_card).last_review for c in state.concepts.values() if c.fsrs_card]
    last = [t for t in last if t]
    return max(last) if last else None


def simulate(state: LearnerState, scheduler: Scheduler, days: int = 14, seed: int = 7,
             samples_per_day: int = 1) -> SimResult:
    # py-fsrs counts elapsed time in whole days, so more than one sample per day only draws stairs.
    start = session_time(state)
    if start is None:
        raise ValueError("no concept has been reviewed yet: run a session first")
    once = {cid: Card.from_dict(c.fsrs_card) for cid, c in state.concepts.items() if c.fsrs_card}
    sched = {cid: Card.from_dict(state.concepts[cid].fsrs_card) for cid in once}  # separate copies
    rng = random.Random(seed)

    def recall(cards: dict[str, Card], t: datetime) -> float:
        return _avg([scheduler.get_card_retrievability(c, t) for c in cards.values()])

    res = SimResult(days, [], [], [], [], [])
    for step in range(days * samples_per_day + 1):
        x = step / samples_per_day
        t = start + timedelta(days=x)
        res.times.append(x)
        res.once.append(recall(once, t))
        res.scheduled.append(recall(sched, t))
        if step % samples_per_day or step == 0:
            continue
        day = step // samples_per_day
        res.daily_once.append(res.once[-1])
        res.daily_scheduled.append(res.scheduled[-1])
        for cid in sorted(sched):  # this day's reviews: every concept due by now
            card = sched[cid]
            if card.due > t:
                continue
            r = scheduler.get_card_retrievability(card, t)
            ok = rng.random() < r
            card, _ = scheduler.review_card(card, Rating.Good if ok else Rating.Again, t)
            sched[cid] = card
            res.events.append(ReviewEvent(day, cid, r, ok, card.stability, (card.due - t) / timedelta(days=1)))
        # show the jump right after the reviews, at the same moment
        res.times.append(x)
        res.once.append(res.once[-1])
        res.scheduled.append(recall(sched, t))
    return res


def review_log(res: SimResult, names: dict[str, str]) -> str:
    lines = []
    for day in range(1, res.days + 1):
        evs = [e for e in res.events if e.day == day]
        if not evs:
            continue
        parts = [f"{names.get(e.concept, e.concept)} (recall {e.recall_before:.0%} -> {'right' if e.correct else 'forgot'}, "
                 f"next in {e.next_in_days:.0f}d)" for e in evs]
        lines.append(f"Day {day:>2}  revise: " + "; ".join(parts))
    return "\n".join(lines) or "(no reviews were due)"


def ascii_chart(res: SimResult, height: int = 10) -> str:
    """One column per day: o = study once, # = with our schedule, * = both. Values are the low point
    of each day (just before that day's revision), so the chart never flatters us."""
    cols = [(1.0, 1.0)] + list(zip(res.daily_once, res.daily_scheduled))
    rows = []
    for level in range(height, -1, -1):
        y = level / height
        cells = []
        for o, s in cols:
            ho, hs = round(o * height) == level, round(s * height) == level
            cells.append(" * " if ho and hs else " # " if hs else " o " if ho else "   ")
        rows.append(f"{y:4.0%} |" + "".join(cells))
    rows.append("      " + "---" * len(cols))
    rows.append("  day " + "".join(f"{d:^3}" for d in range(len(cols))))
    rows.append("  o = study once, no revision     # = revise on our schedule     * = both")
    return "\n".join(rows)


def save_chart(res: SimResult, path: str, title: str = "") -> bool:
    """PNG chart via matplotlib, if it is installed. Returns False (and does nothing) if it is not."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    ax.plot(res.times, [v * 100 for v in res.once], color="#b0b0b0", lw=2.2, label="Study once, no revision")
    ax.plot(res.times, [v * 100 for v in res.scheduled], color="#1f6feb", lw=2.2, label="Revise on our FSRS schedule")
    for e in res.events:
        ax.axvline(e.day, color="#1f6feb", alpha=0.08, lw=6)
    ax.set_ylim(0, 102)
    ax.set_xlim(0, res.days)
    ax.set_xlabel("Days after the first session")
    ax.set_ylabel("Chance of remembering (%)")
    ax.set_title(title or "Predicted recall, from the FSRS memory model")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower left", frameon=False)
    end_o, end_s = res.daily_once[-1] * 100, res.daily_scheduled[-1] * 100
    ax.annotate(f"{end_o:.0f}%", (res.days, end_o), xytext=(-28, -14), textcoords="offset points", color="#707070")
    ax.annotate(f"{end_s:.0f}%", (res.days, end_s), xytext=(-28, 8), textcoords="offset points", color="#1f6feb")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True
