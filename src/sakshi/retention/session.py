"""The adaptive quiz: diagnose, walk down to the basics, climb back up, then schedule revision.

For each top concept (most advanced first):
  1. Ask a recall question.
  2. Right -> done with this concept (an application question answered right also credits the ideas below it).
  3. Wrong -> diagnose: ask the question that best separates the possible misconceptions (always keeping
     one question back to check the student afterwards), then show the misconception and its fix.
  4. Walk DOWN to each prerequisite (recall questions), at most `max_depth` levels.
  5. Climb back UP: an application question on the concept. Right -> "hard" (learned with help).
     Wrong -> "again"; the answer still counts as evidence for the diagnosis.
Concepts not reached this way are asked at the end, while the question budget lasts.
Finally: one FSRS review per concept (its final outcome), saved state, and a report with the revision plan.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import bkt
from .bank import Bank, Question
from .bayes import NONE, BayesParams, Diagnosis
from .fsrs_sched import days_until, make_scheduler, review
from .graph import ConceptGraph
from .io import IO
from .ranker import revision_plan
from .state import LearnerState, MisconceptionState


@dataclass
class SessionConfig:
    bkt: bkt.BKTParams = field(default_factory=bkt.BKTParams)
    bayes: BayesParams = field(default_factory=BayesParams)
    max_depth: int = 2          # how many levels down the walk may go
    max_questions: int = 12     # question budget for one session
    max_diagnostic: int = 2     # extra questions spent pinning down a misconception
    climb_threshold: float = 0.6  # BKT P(learned) a concept needs before we climb back to what is built on it
    climb_retries: int = 1        # after a wrong application answer: re-teach, then this many more tries
    desired_retention: float = 0.9
    application_outcome: str = "easy"  # FSRS rating for a first-time correct application answer
    show_summary: bool = True


@dataclass
class SessionResult:
    asked: list[str]
    outcomes: dict[str, str]
    implicit: list[str]
    detected: dict[str, float]   # misconception id -> probability (confirmed ones)
    suspected: dict[str, float]
    stopped_early: bool


class _Stop(Exception):
    pass


class AdaptiveSession:
    def __init__(self, bank: Bank, state: LearnerState, io: IO, config: SessionConfig | None = None,
                 now: datetime | None = None):
        self.bank, self.state, self.io = bank, state, io
        self.cfg = config or SessionConfig()
        self.now = now or datetime.now(timezone.utc)
        self.graph = ConceptGraph(bank)
        self.scheduler = make_scheduler(self.cfg.desired_retention)
        self.state.bank_title = bank.title
        self.state.ensure(bank.concepts, self.cfg.bkt.p_init)
        self.asked: list[str] = []
        self.outcome: dict[str, str] = {}
        self.implicit: set[str] = set()
        self.diag: dict[str, Diagnosis] = {}
        self.stopped = False

    # ---- asking ---------------------------------------------------------------------------------------

    def _remaining(self, cid: str) -> list[Question]:
        return [q for q in self.bank.questions_for(cid) if q.id not in self.asked]

    def _pick(self, cid: str, prefer: str) -> Question | None:
        if len(self.asked) >= self.cfg.max_questions:
            return None
        qs = self._remaining(cid)
        preferred = [q for q in qs if q.type == prefer]
        return (preferred or qs or [None])[0]

    def _ask(self, q: Question) -> bool:
        self.io.show_question(q, len(self.asked) + 1)
        t0 = time.monotonic()
        picked = self.io.answer(q)
        if picked is None:
            raise _Stop()
        latency = int((time.monotonic() - t0) * 1000)
        self.asked.append(q.id)
        opt = q.option(picked)
        correct = bool(opt and opt.correct)

        cs = self.state.concepts[q.concept]
        before = cs.p_mastery
        cs.p_mastery = bkt.update(cs.p_mastery, correct, self.cfg.bkt, application=q.type == "application")
        cs.attempts += 1
        self.state.attempts.append({"q": q.id, "concept": q.concept, "picked": picked, "correct": correct,
                                    "latency_ms": latency, "ts": self.now.isoformat()})
        self.io.log(f"{q.concept} mastery {before:.2f} -> {cs.p_mastery:.2f}")

        if not correct and q.concept not in self.diag:
            self.diag[q.concept] = Diagnosis(q.concept, self.bank.concepts[q.concept].misconceptions, self.cfg.bayes)
        if q.concept in self.diag:
            d = self.diag[q.concept]
            d.update(q, picked)
            top = sorted(d.posterior.items(), key=lambda kv: -kv[1])[:3]
            self.io.log(f"{q.concept} misconception odds: " + ", ".join(f"{h} {p:.2f}" for h, p in top))

        right = next(o for o in q.options if o.correct)
        self.io.event("result", qid=q.id, ok=correct, picked=picked, correct=right.key, correct_text=right.text,
                      explanation=q.explanation)
        if correct:
            self.io.show("Correct! " + q.explanation)
        else:
            self.io.show(f"Not quite. The answer is {right.key}) {right.text}.")
        return correct

    # ---- the walk -------------------------------------------------------------------------------------

    def _diagnose(self, cid: str) -> None:
        """Spend up to max_diagnostic questions narrowing down the misconception, keeping one back."""
        d = self.diag[cid]
        for _ in range(self.cfg.max_diagnostic):
            if d.confirmed() or len(self.asked) >= self.cfg.max_questions:
                break
            pool = self._remaining(cid)
            if len(pool) <= 1:  # keep the last question for checking after the walk
                break
            q = d.best_question(pool)
            self.io.log(f"{cid}: asking {q.id} next (expected information gain {d.expected_gain(q):.2f} bits)")
            self.io.show("Let me ask that another way.")
            self.io.event("again", concept=self.bank.concepts[cid].name)
            self._ask(q)

    def _last_on(self, cid: str):
        return next((self.bank.questions[q] for q in reversed(self.asked)
                     if q in self.bank.questions and self.bank.questions[q].concept == cid), None)

    def _explain(self, cid: str) -> None:
        d = self.diag[cid]
        m = d.confirmed() or d.suspected()
        name = self.bank.concepts[cid].name
        if m:
            mis = self.bank.misconceptions[m]
            label = "Misconception detected" if d.confirmed() else "Possible misconception"
            self.io.event("diagnosis", concept=name, confirmed=bool(d.confirmed()), text=mis.text, fix=mis.fix,
                          sure=round(d.posterior[m], 2),
                          remember=(last.explanation if (last := self._last_on(cid)) else ""))
            self.io.show(f"\n>> {label}: \"{mis.text}\" ({d.posterior[m]:.0%} sure)")
            self.io.show(f"   Fix: {mis.fix or 'See the explanation.'}")
        else:
            self.io.event("rebuild", concept=name, remember=(last.explanation if (last := self._last_on(cid)) else ""))
            self.io.show(f"\n>> No single misconception stands out for \"{name}\". Let's rebuild it from the basics.")
        last = next((self.bank.questions[q] for q in reversed(self.asked) if self.bank.questions[q].concept == cid), None)
        if last and last.explanation:
            self.io.show(f"   Remember: {last.explanation}")
        self.io.taught(cid)

    def extend(self, bank: Bank) -> None:
        """A bigger bank (a new question arrived while the student was answering): keep everything learned so far."""
        self.bank, self.graph = bank, ConceptGraph(bank)
        self.state.ensure(bank.concepts, self.cfg.bkt.p_init)

    def explore_question(self, qid: str) -> None:
        """Streaming mode: start from THIS question (the one just written). If its concept is already settled
        this session, the question is still asked as extra evidence, without another walk."""
        q = self.bank.questions[qid]
        if len(self.asked) >= self.cfg.max_questions or qid in self.asked:
            return
        if q.concept in self.outcome:
            self._ask(q)
            return
        self._explore(q.concept, 0, first=q)

    def _explore(self, cid: str, depth: int, first: Question | None = None) -> bool:
        """Does the student understand `cid` by the end? Walks down on a wrong answer, back up after."""
        if cid in self.outcome:
            return self.outcome[cid] != "again"
        name = self.bank.concepts[cid].name
        q = first or self._pick(cid, "recall")
        if q is None:
            return self.state.concepts[cid].p_mastery >= 0.5
        if self._ask(q):
            self.outcome[cid] = self.cfg.application_outcome if q.type == "application" else "good"
            if q.type == "application":
                self._credit_below(cid)
            return True

        self._diagnose(cid)
        self._explain(cid)
        prereqs = [p for p in self.graph.prereqs(cid) if p not in self.outcome]
        shaky: list[str] = []
        if prereqs and depth < self.cfg.max_depth:
            names = ", ".join(f'"{self.bank.concepts[p].name}"' for p in prereqs)
            self.io.show(f"\nLet's go back to the idea{'s' if len(prereqs) > 1 else ''} this builds on: {names}.")
            self.io.event("walk_down", concept=name, to=[self.bank.concepts[p].name for p in prereqs])
            self.io.log(f"walk DOWN from {cid} to {', '.join(prereqs)} (depth {depth + 1})")
            for p in prereqs:
                if not self._explore(p, depth + 1) and self.bank.questions_for(p):
                    shaky.append(p)  # a prerequisite with no questions cannot be checked, so it cannot block
        if shaky:  # do not build on a base the student has not got yet: stop the climb here
            names = ", ".join(f'"{self.bank.concepts[p].name}"' for p in shaky)
            self.io.show(f"\nWe'll come back to \"{name}\" once {names} is solid. It's first in your next revision.")
            self.io.event("climb_stop", concept=name, waits=[self.bank.concepts[p].name for p in shaky])
            self.io.log(f"climb STOPPED at {cid}: prerequisite(s) below threshold: {', '.join(shaky)}")
            self.outcome[cid] = "again"
            self.state.blocked[cid] = shaky
            return False
        if prereqs:
            self.io.log(f"climb UP back to {cid}")
        return self._climb(cid)

    def _climb(self, cid: str) -> bool:
        """Application question(s) on a concept the student got wrong, after re-teaching (and after its base is
        solid). Climb on only when BKT says the concept is learned: P(L) >= climb_threshold."""
        name = self.bank.concepts[cid].name
        cs = self.state.concepts[cid]
        for attempt in range(1 + self.cfg.climb_retries):
            self.io.show(f"\nNow let's use \"{name}\"." if attempt == 0 else "\nLet's try using it once more.")
            self.io.event("climb_up", concept=name, retry=attempt > 0)
            check = self._pick(cid, "application")  # falls back to an unasked recall question
            if check is None:
                break
            ok = self._ask(check)
            if ok and cs.p_mastery >= self.cfg.climb_threshold:
                self.io.log(f"{cid}: P(L) {cs.p_mastery:.2f} >= {self.cfg.climb_threshold}: climb on")
                self.outcome[cid] = "hard"
                self.state.blocked.pop(cid, None)
                return True
            if not ok and cid in self.diag:
                self._explain(cid)
            elif not ok:
                self.io.taught(cid)
        self.io.log(f"{cid}: P(L) {cs.p_mastery:.2f} < {self.cfg.climb_threshold} after re-teaching: stop here")
        self.outcome[cid] = "again"
        return False

    def _credit_below(self, cid: str) -> None:
        for p in self.graph.below(cid):
            if p in self.outcome:
                continue
            cs = self.state.concepts[p]
            cs.p_mastery = bkt.implicit_credit(cs.p_mastery, self.cfg.bkt)
            self.implicit.add(p)
            self.io.log(f"{p}: implicit credit from applying {cid} (mastery now {cs.p_mastery:.2f})")

    # ---- the whole session ----------------------------------------------------------------------------

    def finish_stream(self) -> SessionResult:
        """Streaming mode, after the last question: concepts nobody reached, then FSRS + report (as in run)."""
        try:
            rest = sorted((c for c in self.bank.concepts if c not in self.outcome and c not in self.implicit),
                          key=lambda c: -self.graph.level(c))
            for cid in rest:
                self._explore(cid, 0)
        except _Stop:
            self.stopped = True
        return self._finish()

    def run(self) -> SessionResult:
        if self.cfg.show_summary and self.bank.summary:
            self.io.show(f"Summary: {self.bank.summary}\n")
        try:
            for top in self.graph.tops():
                self._explore(top, 0)
            # Anything not reached by the walk (and not credited by an application answer), most advanced first.
            rest = sorted((c for c in self.bank.concepts if c not in self.outcome and c not in self.implicit),
                          key=lambda c: -self.graph.level(c))
            for cid in rest:
                self._explore(cid, 0)
        except _Stop:
            self.stopped = True
            self.io.show("\nStopped. Saving what we have so far.")
        return self._finish()

    def _finish(self) -> SessionResult:
        for cid in self.bank.concepts:
            out = self.outcome.get(cid) or ("good" if cid in self.implicit else None)
            if out is None:
                continue
            cs = self.state.concepts[cid]
            cs.fsrs_card = review(self.scheduler, cs.fsrs_card, out, self.now)
            cs.last_outcome = out if cid in self.outcome else "good (implicit)"

        detected, suspected = {}, {}
        for cid, d in self.diag.items():
            for h, p in d.posterior.items():
                if h == NONE:
                    continue
                if p >= d.params.confirm:
                    status, detected[h] = "confirmed", p
                elif p >= d.params.suspect:
                    status, suspected[h] = "suspected", p
                elif h in self.state.misconceptions:
                    status = "cleared"  # held before, no longer likely
                else:
                    continue
                if status != "cleared" and self.outcome.get(cid) in ("hard", "good", "easy"):
                    status += ", corrected in session"
                self.state.misconceptions[h] = MisconceptionState(cid, self.bank.misconceptions[h].text, round(p, 4),
                                                                  status, self.now.isoformat())
        self.state.sessions += 1
        self._report()
        return SessionResult(list(self.asked), dict(self.outcome), sorted(self.implicit), detected, suspected, self.stopped)

    def _report(self) -> None:
        io, b = self.io, self.bank
        io.show("\n" + "=" * 60 + "\nYOUR REPORT\n" + "=" * 60)
        io.show(f"Questions answered: {len(self.asked)}")
        io.show("\nHow well you know each idea:")
        for cid, c in b.concepts.items():
            cs = self.state.concepts[cid]
            bar = "#" * round(cs.p_mastery * 10)
            next_in = days_until(cs.fsrs_card, self.now)
            when = f"revise in {max(0, round(next_in))} day(s)" if next_in is not None else "not tested yet"
            io.show(f"  {c.name:<42} {bar:<10} {cs.p_mastery:4.0%}   {when}")
        found = [(m, s) for m, s in self.state.misconceptions.items()
                 if b.misconceptions.get(m) and s.status != "cleared" and s.last_checked == self.now.isoformat()]
        if found:
            io.show("\nMisconceptions found today:")
            for m, s in found:
                io.show(f"  - \"{s.text}\" ({s.status}, {s.p_holds:.0%})")
                if b.misconceptions[m].fix:
                    io.show(f"    Fix: {b.misconceptions[m].fix}")
        plan = revision_plan(self.state, {k: c.name for k, c in b.concepts.items()}, self.scheduler, self.now)
        io.show("\nRevision plan (most at risk first):")
        for i, r in enumerate(plan, 1):
            date = r.due.strftime("%a %d %b") if r.due else "next session"
            io.show(f"  {i}. {r.name:<42} on {date}")
