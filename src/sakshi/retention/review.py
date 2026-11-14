"""Review day: come back on a later day, re-check the beliefs the student held, and follow the misconception graph.

Order of work (question budget permitting):
  0. Forgetting: each concept's BKT mastery is discounted by FSRS recall since the last review,
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
Then one FSRS review per concept touched, and the saved state.
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from . import bkt
from .bank import Option, Question
from .bayes import BayesParams
from .fsrs_sched import make_scheduler, retrievability, review
from .io import IO
from .session import _Stop
from .state import LearnerState, MisconceptionState

MIS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "misconceptions")


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


def _q(d: dict) -> Question:
    return Question(d["id"], d["concept"], d["type"], d["stem"],
                    [Option(o["key"], o["text"], o["correct"], o["misconception"]) for o in d["options"]],
                    d.get("explanation", ""))


def belief_question(lib, mid: str, asked: set[str], rng: random.Random) -> Question | None:
    """A question aimed at one belief that this student has not seen: its probe first, else a statement check."""
    from ..link import probe_question
    d = probe_question(lib, mid, rng, f"{mid}-probe")
    if d and d["id"] not in asked:
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


@dataclass
class ReviewConfig:
    bkt: bkt.BKTParams = bkt.BKTParams()
    bayes: BayesParams = BayesParams()
    max_questions: int = 10
    climb_threshold: float = 0.6
    related_per_belief: int = 1
    desired_retention: float = 0.9


class ReviewSession:
    def __init__(self, state: LearnerState, library, io: IO, now: datetime, config: ReviewConfig | None = None,
                 related: RelatedBeliefs | None = None, seed: int = 0):
        self.state, self.lib, self.io, self.now = state, library, io, now
        self.cfg = config or ReviewConfig()
        self.rel = related or RelatedBeliefs(library)
        self.sched = make_scheduler(self.cfg.desired_retention)
        self.rng = random.Random(seed)
        self.asked_ever = {a["q"] for a in state.attempts}
        self.asked: list[str] = []
        self.outcome: dict[str, str] = {}
        self.log: list[str] = []

    def name(self, cid: str) -> str:
        return (self.lib.concepts.get(cid) or {}).get("name", cid)

    # ---- one question ---------------------------------------------------------------------------------
    def _ask(self, q: Question) -> tuple[bool, str]:
        self.state.ensure([q.concept], self.cfg.bkt.p_init)
        self.io.show_question(q, len(self.asked) + 1)
        picked = self.io.answer(q)
        if picked is None:
            raise _Stop()
        opt = q.option(picked) if picked else None
        ok = bool(opt and opt.correct)
        cs = self.state.concepts[q.concept]
        before = cs.p_mastery
        cs.p_mastery = bkt.update(cs.p_mastery, ok, self.cfg.bkt, application=q.type == "application")
        cs.attempts += 1
        self.asked.append(q.id)
        self.asked_ever.add(q.id)
        self.state.attempts.append({"q": q.id, "concept": q.concept, "picked": picked, "correct": ok,
                                    "ts": self.now.isoformat(), "review": True})
        self.io.log(f"{q.concept} mastery {before:.2f} -> {cs.p_mastery:.2f}")
        right = next(o for o in q.options if o.correct)
        self.io.event("result", qid=q.id, ok=ok, picked=picked, correct=right.key, correct_text=right.text,
                      explanation=q.explanation)
        self.io.show("Correct! " + q.explanation if ok else f"Not quite. The answer is {right.key}) {right.text}.")
        return ok, (opt.misconception if opt else None) or ""

    def _holds_update(self, prior: float, q: Question, mid: str, picked_mis: str, ok: bool) -> float:
        """Bayes with two hypotheses (holds `mid` / does not), the likelihoods of bayes.py."""
        b, wrong = self.cfg.bayes, [o for o in q.options if not o.correct]
        if picked_mis == mid:
            lh, ln = b.p_pick_own, (1 - b.p_correct_none) / len(wrong)
        elif ok:
            lh, ln = b.p_correct_holding, b.p_correct_none
        else:
            lh = (1 - b.p_pick_own - b.p_correct_holding) / max(1, len(wrong) - 1)
            ln = (1 - b.p_correct_none) / len(wrong)
        return prior * lh / (prior * lh + (1 - prior) * ln)

    def _budget(self) -> bool:
        return len(self.asked) < self.cfg.max_questions

    # ---- the steps ------------------------------------------------------------------------------------
    def _forget(self) -> None:
        for cid, cs in self.state.concepts.items():
            if cs.fsrs_card:
                r = retrievability(self.sched, cs.fsrs_card, self.now)
                new = max(0.05, cs.p_mastery * r)
                self.io.log(f"{cid}: P(L) {cs.p_mastery:.2f} x recall {r:.2f} = {new:.2f}")
                cs.p_mastery = new

    def _priority(self, cid: str) -> float:
        cs = self.state.concepts.get(cid)
        if not cs:
            return 1.0
        r = retrievability(self.sched, cs.fsrs_card, self.now) if cs.fsrs_card else 0.0
        return 1 - cs.p_mastery * r

    def _recheck(self, mid: str, ms: MisconceptionState) -> None:
        q = belief_question(self.lib, mid, self.asked_ever, self.rng)
        if q is None:
            return
        self.io.show(f"\nLast time you seemed to think: \"{ms.text}\". Let's check.")
        self.io.event("recheck", concept=self.name(q.concept), text=ms.text)
        ok, picked = self._ask(q)
        p = self._holds_update(ms.p_holds, q, mid, picked, ok)
        if ok and p >= self.cfg.bayes.suspect and self._budget():  # right, but not yet convincing: one more check
            q2 = belief_question(self.lib, mid, self.asked_ever, self.rng)
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
        q = concept_question(self.lib, cid, self.asked_ever, self.rng)
        if q is None:
            return None
        self.io.show(f"\nUsing \"{self.name(cid)}\":")
        ok, _ = self._ask(q)
        solid = ok and self.state.concepts[cid].p_mastery >= self.cfg.climb_threshold
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
                tested = [c for c, cs in self.state.concepts.items() if cs.fsrs_card and c not in self.outcome]
                due = [c for c in tested if datetime.fromisoformat(self.state.concepts[c].fsrs_card["due"]) <= self.now]
                if mode == "revision" and not due:
                    due = tested
                for cid in sorted(due, key=lambda c: -self._priority(c)):
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
