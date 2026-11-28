"""Review day: come back on a later day, re-check the beliefs the student held, and follow the misconception graph.

Order of work (question budget permitting):
  0. Forgetting: each concept's BKT mastery is discounted by FSRS recall since the last review (once per elapsed
       interval: a second review before the next FSRS review only discounts the extra days),
       P(L)_today = P(L)_saved x R(t, S)        (mastery the student has partly forgotten is not mastery today)
  1. Held beliefs (confirmed / suspected), most at-risk concept first. Ask a NEW question aimed at that belief and
     update P(holds) with Bayes (two hypotheses: holds it / does not; same likelihoods as bayes.py).
       still >= 0.5 -> show the fix again, FSRS "Again" (comes back sooner)
       below 0.5   -> cleared, FSRS "Good", then FOLLOW THE GRAPH: ask about a related belief (a `causes` edge from
                      this belief, else the nearest belief with the same root belief in another concept). Picking it
                      means the root belief is still there in a new place: it becomes a suspected belief of its own.
  2. Blocked climbs from last time (a concept whose prerequisite was shaky): prerequisite first, then the concept,
     application questions, climbing only when BKT P(L) >= threshold.
  3. Other concepts FSRS says are due: one application question each.
A question not seen before is always preferred. When a concept has none left (most have only one or two), the one
seen longest ago comes back with its options reshuffled, never within REPEAT_AFTER of the last time. (Without
this, due concepts could never be reviewed again: 5 due, 0 asked, on a learner after 43 sessions.)
A question that was only looked at (the student pressed Back) counts as shown too: the next visit starts with a
different idea and a different question, instead of the same one every time.
Then one FSRS review per concept touched, and the saved state.
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

from . import bkt
from .bank import Option, Question
from .bayes import BayesParams
from .fsrs_sched import make_scheduler, retrievability, review
from .io import IO
from .session import _Stop
from .state import LearnerState, MisconceptionState

MIS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "misconceptions")


def _aware(t: datetime) -> datetime:
    """FSRS works in UTC-aware datetimes; treat a naive time as UTC."""
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


class RelatedBeliefs:
    """Belief -> beliefs that probably share its cause: explicit `causes` edges, then same root belief (nearest
    by meaning, other concepts first)."""

    def __init__(self, library, directory: str = MIS_DIR):
        self.lib = library
        links = json.load(open(os.path.join(directory, "links_v2.json")))
        self.root = links.get("misconception_root", {})
        self.root_name = {r["id"]: r["name"] for r in links.get("roots", [])}
        self.causes: dict[str, list[str]] = {}
        for line in open(os.path.join(directory, "graph", "edges.jsonl")):
            e = json.loads(line)
            if e.get("type") == "causes":
                self.causes.setdefault(e["src"], []).append(e["dst"])
        self.vec = None
        idx = os.path.join(directory, "index", "BAAI_bge-small-en-v1.5.npz")
        if os.path.exists(idx):
            z = np.load(idx, allow_pickle=False)
            self.pos = {m: i for i, m in enumerate(z["ids"])}
            v = z["mis"]
            self.vec = v / np.linalg.norm(v, axis=1, keepdims=True)

    def related(self, mid: str, n: int = 3) -> list[str]:
        out = [m for m in self.causes.get(mid, []) if m in self.lib.by_id]
        r = self.root.get(mid)
        if r:
            same = [m for m, rr in self.root.items() if rr == r and m != mid and m in self.lib.by_id]
            here = self.lib.by_id[mid]["concept_id"]
            if self.vec is not None and mid in self.pos:
                v = self.vec[self.pos[mid]]
                same.sort(key=lambda m: -float(self.vec[self.pos[m]] @ v) if m in self.pos else 0.0)
            same.sort(key=lambda m: self.lib.by_id[m]["concept_id"] == here)  # other concepts first (stable)
            out += same
        return list(dict.fromkeys(out))[:n]


REPEAT_AFTER = timedelta(hours=12)  # a used question is not shown again the same day


def _q(d: dict) -> Question:
    return Question(d["id"], d["concept"], d["type"], d["stem"],
                    [Option(o["key"], o["text"], o["correct"], o["misconception"]) for o in d["options"]],
                    d.get("explanation", ""))


def belief_question(lib, mid: str, asked: set[str], rng: random.Random) -> Question | None:
    """A question aimed at one belief that this student has not seen: its probe first, else a statement check."""
    from ..link import probe_question
    d = probe_question(lib, mid, rng, f"{mid}-probe")
    if d and d["id"] not in asked and d.get("stem") not in asked:  # same stem asked under another id = a repeat
        return _q(d)
    m = lib.by_id[mid]
    pool = [x for x in lib.items if x["concept_id"] == m["concept_id"] and x["id"] != mid] or \
           [x for x in lib.items if x["topic_id"] == m["topic_id"] and x["id"] != mid]
    rng.shuffle(pool)
    opts = [(m["fix"], True, None), (m["statement"], False, mid)] + [(x["statement"], False, x["id"]) for x in pool[:2]]
    rng.shuffle(opts)
    qid = f"{mid}-stmt"
    if qid in asked or not m.get("fix"):
        return None
    return Question(qid, m["concept_id"], "recall", f"Which statement about '{m.get('concept', m['concept_id'])}' is true?",
                    [Option("ABCD"[j], t, ok, x) for j, (t, ok, x) in enumerate(opts)], m["fix"])


def concept_question(lib, cid: str, asked: set[str], rng: random.Random) -> Question | None:
    c = lib.concepts.get(cid) or {}
    for mid in [x if isinstance(x, str) else x.get("id") for x in c.get("misconceptions", [])]:
        if mid in lib.by_id:
            q = belief_question(lib, mid, asked, rng)
            if q:
                return q
    return None


def stored_questions(lib, state: LearnerState, cid: str, rng: random.Random) -> list[Question]:
    """Everything that can be asked about a concept: questions this student has had, then the library's."""
    out = {stem: _q(d) for stem, d in state.saved.items() if d["concept"] == cid}
    c = lib.concepts.get(cid) or {}
    for mid in [x if isinstance(x, str) else x.get("id") for x in c.get("misconceptions", [])]:
        if mid not in lib.by_id:
            continue
        first = belief_question(lib, mid, set(), rng)
        second = belief_question(lib, mid, {first.id, first.stem}, rng) if first else None
        for q in (first, second):
            if q:
                out.setdefault(q.stem, q)
    return list(out.values())


def askable(lib, state: LearnerState, cid: str) -> bool:
    """False for a concept with nothing to ask (it must not be listed as due: it could never be cleared)."""
    return bool(stored_questions(lib, state, cid, random.Random(0)))


def todays_mastery(sched, cs, now: datetime) -> float:
    """Saved mastery discounted by what has probably been forgotten since (does not change the state)."""
    if not cs.fsrs_card:
        return cs.p_mastery
    now = _aware(now)
    since = cs.fsrs_card.get("decayed_at")
    if since and _aware(datetime.fromisoformat(since)) >= now:
        return cs.p_mastery
    r_now = retrievability(sched, cs.fsrs_card, now)
    r_then = retrievability(sched, cs.fsrs_card, _aware(datetime.fromisoformat(since))) if since else 1.0
    factor = r_now / r_then if r_then > 0 else r_now
    return max(0.05, cs.p_mastery * min(1.0, factor))


@dataclass
class ReviewConfig:
    bkt: bkt.BKTParams = bkt.BKTParams()
    bayes: BayesParams = BayesParams()
    max_questions: int = 10
    climb_threshold: float = 0.7
    related_per_belief: int = 1
    desired_retention: float = 0.9


class ReviewSession:
    def __init__(self, state: LearnerState, library, io: IO, now: datetime, config: ReviewConfig | None = None,
                 related: RelatedBeliefs | None = None, seed: int = 0):
        self.state, self.lib, self.io, self.now = state, library, io, _aware(now)
        self.cfg = config or ReviewConfig()
        self.rel = related or RelatedBeliefs(library)
        self.sched = make_scheduler(self.cfg.desired_retention)
        self.rng = random.Random(seed)
        # ids AND stems already shown: a review probe can carry the same stem as a quiz question under a new id
        self.asked_ever = ({a["q"] for a in state.attempts} | {a["stem"] for a in state.attempts if a.get("stem")}
                           | set(state.shown))
        self.asked: list[str] = []
        self.outcome: dict[str, str] = {}
        self.log: list[str] = []

    def name(self, cid: str) -> str:
        return (self.lib.concepts.get(cid) or {}).get("name", cid)

    # ---- bringing a used question back ----------------------------------------------------------------
    def _again(self, questions: list[Question]) -> Question | None:
        """The least recently seen of `questions`, options reshuffled; None if all were seen too recently."""
        last: dict[str, tuple[int, datetime | None]] = {}
        for i, a in enumerate(self.state.attempts):
            ts = _aware(datetime.fromisoformat(a["ts"])) if a.get("ts") else None
            if a.get("stem"):
                last[a["stem"]] = (i, ts)
        seen = {stem: i for i, stem in enumerate(self.state.shown)}  # oldest first
        ready = [q for q in questions if q.id not in self.asked
                 and (last.get(q.stem, (-1, None))[1] is None or self.now - last[q.stem][1] >= REPEAT_AFTER)]
        if not ready:
            return None
        q = min(ready, key=lambda q: (seen.get(q.stem, -1), last.get(q.stem, (-1, None))[0]))
        opts = list(q.options)
        self.rng.shuffle(opts)
        return Question(q.id, q.concept, q.type, q.stem,
                        [Option("ABCDEFG"[j], o.text, o.correct, o.misconception) for j, o in enumerate(opts)],
                        q.explanation)

    def _belief(self, mid: str) -> Question | None:
        """A question on one belief: unseen if there is one, else the one seen longest ago."""
        q = belief_question(self.lib, mid, self.asked_ever, self.rng)
        if q:
            return q
        cid = self.lib.by_id[mid]["concept_id"]
        return self._again([x for x in stored_questions(self.lib, self.state, cid, self.rng)
                            if any(o.misconception == mid for o in x.options)])

    # ---- one question ---------------------------------------------------------------------------------
    def _ask(self, q: Question) -> tuple[bool, str]:
        self.state.ensure([q.concept], self.cfg.bkt.p_init)
        self.state.saved[q.stem] = asdict(q)
        self.state.show(q.stem, self.now.isoformat())
        self.io.show_question(q, len(self.asked) + 1)
        picked = self.io.answer(q)
        if picked is None:
            raise _Stop()
        opt = q.option(picked) if picked else None
        ok = bool(opt and opt.correct)
        cs = self.state.concepts[q.concept]
        before = cs.p_mastery
        cs.p_mastery = bkt.update(cs.p_mastery, ok, self.cfg.bkt, application=q.type == "application",
                                  n_options=len(q.options))
        cs.attempts += 1
        self.asked.append(q.id)
        self.asked_ever.update((q.id, q.stem))
        self.state.attempts.append({"q": q.id, "stem": q.stem, "concept": q.concept, "picked": picked, "correct": ok,
                                    "ts": self.now.isoformat(), "review": True})
        self.io.log(f"{q.concept} mastery {before:.2f} -> {cs.p_mastery:.2f}")
        right = next(o for o in q.options if o.correct)
        self.io.event("result", qid=q.id, ok=ok, picked=picked, correct=right.key, correct_text=right.text,
                      explanation=q.explanation)
        self.io.show("Correct! " + q.explanation if ok else f"Not quite. The answer is {right.key}) {right.text}.")
        return ok, (opt.misconception if opt else None) or ""

    def _holds_update(self, prior: float, q: Question, mid: str, picked_mis: str, ok: bool) -> float:
        """Bayes with two hypotheses, likelihoods from bayes.py: holds `mid`, or does not (half "knows it",
        half "guessing at random"). A right answer or another wrong option never raises P(holds)."""
        b, n = self.cfg.bayes, len(q.options)
        owned = [o for o in q.options if not o.correct and o.misconception == mid]
        if not owned:
            return prior
        if picked_mis == mid:
            lh = b.p_pick_own / len(owned)
            ln = 0.5 * (b.p_slip / (n - 1)) + 0.5 / n
        else:
            lh = (1 - b.p_pick_own) / max(1, n - len(owned))
            ln = 0.5 * ((1 - b.p_slip) if ok else b.p_slip / (n - 1)) + 0.5 / n
        return prior * lh / (prior * lh + (1 - prior) * ln)

    def _budget(self) -> bool:
        return len(self.asked) < self.cfg.max_questions

    # ---- the steps ------------------------------------------------------------------------------------
    def _last_visit(self, cid: str) -> int:
        """Position of this concept's most recently shown question (-1: none), so a new visit starts elsewhere."""
        return max((i for i, stem in enumerate(self.state.shown)
                    if self.state.saved.get(stem, {}).get("concept") == cid), default=-1)

    def _forget(self) -> None:
        """Discount mastery by FSRS recall, ONCE per elapsed interval. A concept not reviewed in an earlier review
        session keeps its FSRS card, so recall R(t) is still measured from the last real review; we store when decay
        was last applied ("decayed_at", ignored by FSRS) and apply only R(now) / R(decayed_at)."""
        for cid, cs in self.state.concepts.items():
            if not cs.fsrs_card:
                continue
            r_now = retrievability(self.sched, cs.fsrs_card, self.now)
            since = cs.fsrs_card.get("decayed_at")
            r_then = retrievability(self.sched, cs.fsrs_card, _aware(datetime.fromisoformat(since))) if since else 1.0
            if since and _aware(datetime.fromisoformat(since)) >= self.now:
                continue  # already discounted up to (or past) today
            factor = r_now / r_then if r_then > 0 else r_now
            new = max(0.05, cs.p_mastery * min(1.0, factor))
            self.io.log(f"{cid}: P(L) {cs.p_mastery:.2f} x recall {factor:.2f} = {new:.2f}")
            cs.p_mastery = new
            cs.fsrs_card["decayed_at"] = self.now.isoformat()

    def _priority(self, cid: str) -> float:
        """Risk of not knowing it today. Mastery is already discounted by _forget, so no second recall factor."""
        cs = self.state.concepts.get(cid)
        return 1.0 if not cs else 1 - cs.p_mastery

    def _recheck(self, mid: str, ms: MisconceptionState) -> None:
        q = self._belief(mid)
        if q is None:
            return
        self.io.show(f"\nLast time you seemed to think: \"{ms.text}\". Let's check.")
        self.io.event("recheck", concept=self.name(q.concept), text=ms.text)
        ok, picked = self._ask(q)
        p = self._holds_update(ms.p_holds, q, mid, picked, ok)
        if ok and p >= self.cfg.bayes.suspect and self._budget():  # right, but not yet convincing: one more check
            q2 = self._belief(mid)
            if q2 is not None:
                self.io.show("Good. One more on the same idea.")
                ok, picked = self._ask(q2)
                p = self._holds_update(p, q2, mid, picked, ok)
        fix = self.lib.by_id[mid].get("fix", "")
        cid = q.concept
        if p >= self.cfg.bayes.suspect:
            ms.status, ms.p_holds = "still held", round(p, 4)
            self.io.show(f">> Still there ({p:.0%}). Remember: {fix}")
            self.io.event("still", concept=self.name(cid), text=ms.text, fix=fix, sure=round(p, 2))
            self.io.taught(cid)
            self.outcome[cid] = "again"
        else:
            ms.status, ms.p_holds = "cleared", round(p, 4)
            self.io.show(f">> Cleared (now {p:.0%}).")
            self.io.event("cleared", concept=self.name(cid), text=ms.text)
            self.outcome.setdefault(cid, "good")
            self._follow(mid)
        ms.last_checked = self.now.isoformat()

    def _follow(self, mid: str) -> None:
        """Same root belief elsewhere? Ask about a related belief the student has not been tested on."""
        root = self.rel.root.get(mid)
        for r in self.rel.related(mid, n=6):
            if not self._budget() or self.cfg.related_per_belief <= 0:
                return
            if r in self.state.misconceptions:
                continue
            q = belief_question(self.lib, r, self.asked_ever, self.rng)
            if q is None:
                continue
            why = f'the same root idea: "{self.rel.root_name.get(root, root)}"' if self.rel.root.get(r) == root else "a belief this one leads to"
            self.io.show(f"\nNext, a related idea (from {why}).")
            self.io.event("related", root=self.rel.root_name.get(root, ""), same_root=self.rel.root.get(r) == root,
                          concept=self.name(self.lib.by_id[r]["concept_id"]))
            self.io.log(f"follow graph: {mid} -> {r}")
            ok, picked = self._ask(q)
            p = self._holds_update(0.3, q, r, picked, ok)
            m = self.lib.by_id[r]
            if p >= self.cfg.bayes.suspect:
                self.state.misconceptions[r] = MisconceptionState(m["concept_id"], m["statement"], round(p, 4),
                                                                  f"suspected (same root as {mid})", self.now.isoformat())
                self.io.show(f">> This one may be there too ({p:.0%}): \"{m['statement']}\"\n   Fix: {m.get('fix', '')}")
                self.io.event("related_found", concept=self.name(m["concept_id"]), text=m["statement"],
                              fix=m.get("fix", ""), sure=round(p, 2))
                self.io.taught(m["concept_id"])
                self.outcome[m["concept_id"]] = "again"
            else:
                self.outcome.setdefault(m["concept_id"], "good")
            return

    def _unblock(self, cid: str, prereqs: list[str]) -> None:
        for p in prereqs:
            if self._apply(p) is False:
                self.io.show(f"\"{self.name(cid)}\" waits until \"{self.name(p)}\" is solid.")
                self.io.event("blocked", concept=self.name(cid), waits=[self.name(p)])
                return
        if self._apply(cid) is not False:
            self.state.blocked.pop(cid, None)
            self.io.show(f">> Climbed back up to \"{self.name(cid)}\".")
            self.io.event("climbed", concept=self.name(cid))

    def _apply(self, cid: str) -> bool | None:
        """Application question on a concept; solid = right answer and BKT P(L) >= threshold.
        None = nothing left to ask about it (cannot be checked, so it does not block a climb)."""
        if cid in self.outcome:
            return self.outcome[cid] != "again"
        if not self._budget():
            return False
        q = concept_question(self.lib, cid, self.asked_ever, self.rng) \
            or self._again(stored_questions(self.lib, self.state, cid, self.rng))
        if q is None:
            return None
        self.io.show(f"\nUsing \"{self.name(cid)}\":")
        ok, _ = self._ask(q)
        solid = ok and bkt.mastered(self.state.concepts[cid].p_mastery, self.state.attempts, cid,
                                    self.cfg.climb_threshold, self.cfg.bkt)
        self.outcome[cid] = "good" if solid else "again"
        if not ok:
            self.io.taught(cid)
        return solid

    def run(self, mode: str = "all") -> dict:
        """mode: "mentor" = held beliefs + the graph walk from them; "revision" = blocked climbs + concepts due
        (if nothing is due yet, the riskiest concepts, so practice is never empty); "all" = both, in that order."""
        self.io.show(f"Review on {self.now:%a %d %b}.")
        self._forget()
        stopped = False
        try:
            if mode in ("all", "mentor"):
                held = [(m, s) for m, s in self.state.misconceptions.items()
                        if s.status.startswith(("confirmed", "suspected", "still held"))]
                held.sort(key=lambda x: -self._priority(x[1].concept))
                for mid, ms in held:
                    if self._budget() and mid in self.lib.by_id:
                        self._recheck(mid, ms)
            if mode in ("all", "revision"):
                for cid, prereqs in list(self.state.blocked.items()):
                    if self._budget():
                        self._unblock(cid, prereqs)
                tested = [c for c, cs in self.state.concepts.items()
                          if cs.fsrs_card and c not in self.outcome and askable(self.lib, self.state, c)]
                due = [c for c in tested if _aware(datetime.fromisoformat(self.state.concepts[c].fsrs_card["due"])) <= self.now]
                if mode == "revision" and not due:
                    due = tested
                for cid in sorted(due, key=lambda c: (self._last_visit(c), -self._priority(c))):
                    if self._budget():
                        self._apply(cid)
        except _Stop:
            stopped = True
        for cid, out in self.outcome.items():
            cs = self.state.concepts[cid]
            cs.fsrs_card = review(self.sched, cs.fsrs_card, out, self.now)
            cs.last_outcome = out
        self.state.sessions += 1
        self._report()
        return {"asked": list(self.asked), "outcomes": dict(self.outcome), "stopped": stopped}

    def _report(self) -> None:
        self.io.show("\n" + "=" * 60 + "\nREVIEW REPORT\n" + "=" * 60)
        for mid, ms in self.state.misconceptions.items():
            if ms.last_checked == self.now.isoformat():
                self.io.show(f"  [{ms.status}] {ms.text} ({ms.p_holds:.0%})")
        for cid, out in self.outcome.items():
            cs = self.state.concepts[cid]
            self.io.show(f"  {self.name(cid):<40} {out:<6} mastery {cs.p_mastery:.0%}  next review {cs.fsrs_card['due'][:10]}")
        if self.state.blocked:
            self.io.show("  Still waiting on basics: " + ", ".join(self.name(c) for c in self.state.blocked))
