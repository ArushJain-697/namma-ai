#!/usr/bin/env python3
"""Sakshi's engine for the device UI (~/Sakshi/sakshi.py). One long-running process: GURU-0.6B and the helper
models are loaded once, the learner is saved after every session. It talks JSON, one object per line.

UI -> engine (stdin):
  {"cmd": "status"}                       numbers for the menu, Revision and Diagnostics screens
  {"cmd": "study", "text": "..."}         a page (from the camera + OCR, or the passage file)
  {"cmd": "mentor"}                       re-check misconceptions, follow the graph
  {"cmd": "revision"}                     finish blocked climbs, then concepts that are due
  {"cmd": "answer", "key": "B"}           the child's answer to the current question
  {"cmd": "stop"}                         the child left: save and end the session
engine -> UI (stdout): {"type": ...}
  ready, loading, stage {n}, summary {text}, waiting, question {...}, result {...},
  diagnosis / rebuild / walk_down / climb_stop / climb_up / again / recheck / still / cleared / related /
  related_found / blocked / climbed {...}, done {...}, status {...}, error {msg}

  ~/sakshi-venv/bin/python scripts/sakshi_engine.py [--eight-bit]
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import resource
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
STATE = Path(os.environ.get("SAKSHI_STATE", ROOT / "state" / "learner.json"))
MIN_WORDS = 40

# The ExecuTorch backend collects model text by pointing fd 1 at a temp file while it writes. Our messages go to a
# private copy of the original stdout (the pipe to the UI), which that capture never touches.
_OUT = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
_LOCK = threading.Lock()


def emit(kind: str, **data) -> None:
    with _LOCK:
        _OUT.write(json.dumps({"type": kind, **data}, ensure_ascii=False) + "\n")
        _OUT.flush()


def now() -> datetime:
    return datetime.now(timezone.utc)


def peak_mb() -> int:
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(r / (2**20 if sys.platform == "darwin" else 2**10))


class DeviceIO:
    """The session's IO: questions and events go to the UI; answers come back from it."""

    def __init__(self, answers: queue.Queue):
        self.answers = answers
        self.n = 0

    def show(self, text):  # the UI draws from events instead of sentences
        pass

    def log(self, text):
        pass

    def taught(self, concept_id):
        pass

    def show_question(self, q, number):
        self.n += 1
        tag = ("From your page" if q.id.startswith("g") else
               "Use it" if q.type == "application" else "Basics")
        emit("question", qid=q.id, n=self.n, tag=tag, stem=q.stem,
             options=[o.text for o in q.options], keys=[o.key for o in q.options])

    def answer(self, q):
        a = self.answers.get()
        return a  # None = the child left

    def event(self, kind, **data):
        emit(kind, **data)


class Engine:
    def __init__(self, eight_bit: bool):
        from sakshi.misconceptions import Library
        self.lib = Library.load()
        self.eight_bit = eight_bit
        self.models_ready = threading.Event()
        self.models_error = None
        self.answers: queue.Queue = queue.Queue()
        self.stop = threading.Event()
        self.last_card: dict = {}
        threading.Thread(target=self._load_models, daemon=True).start()

    # ---- models (loaded once, in the background, so the menu is usable at once) ----------------------------
    def _load_models(self):
        try:
            import backup_quiz as bq
            from sakshi.link import Linker
            from sakshi.mapper import Mapper, PteEncoders
            from sakshi_app import model_dirs
            t = time.time()
            self.quiz_dir, sum_dir = model_dirs(self.eight_bit)
            self.bq = bq
            self.m, self.sm = bq.Model(self.quiz_dir), bq.Model(sum_dir)
            self.mp = Mapper(self.lib, PteEncoders())
            self.linker = Linker(self.mp)
            self.load_s = round(time.time() - t, 1)
        except Exception as e:  # noqa: BLE001
            self.models_error = f"{type(e).__name__}: {e}"
        self.models_ready.set()

    def state(self):
        from sakshi.retention.state import LearnerState
        return LearnerState.load(str(STATE))

    def name(self, cid):
        return (self.lib.concepts.get(cid) or {}).get("name", cid)

    # ---- status for the menu / Revision / Diagnostics screens --------------------------------------------
    def status(self):
        from sakshi.retention.fsrs_sched import make_scheduler
        from sakshi.retention.ranker import revision_plan
        st, t = self.state(), now()
        held = [{"text": m.text, "concept": self.name(m.concept), "sure": m.p_holds, "status": m.status}
                for m in st.misconceptions.values() if m.status.startswith(("confirmed", "suspected", "still held"))]
        tested = {c: s for c, s in st.concepts.items() if s.fsrs_card}
        plan = revision_plan(st, {c: self.name(c) for c in st.concepts}, make_scheduler(), t) if tested else []
        due = sum(1 for r in plan if r.due and r.due <= t)
        wrong: dict[str, int] = {}
        for a in st.attempts:
            if not a["correct"]:
                wrong[self.name(a["concept"])] = wrong.get(self.name(a["concept"]), 0) + 1
        emit("status", solved=len(st.attempts), correct=sum(a["correct"] for a in st.attempts),
             held=held, due=due, blocked=[self.name(c) for c in st.blocked],
             topics=[{"name": r.name, "mastery": round(r.mastery, 2), "recall": round(r.recall, 2),
                      "due": r.due.strftime("%a %d %b") if r.due else None} for r in plan[:6]],
             weak=sorted(wrong.items(), key=lambda kv: -kv[1])[:5], sessions=st.sessions,
             models_ready=self.models_ready.is_set() and not self.models_error, last_card=self.last_card)

    # ---- New Study ----------------------------------------------------------------------------------------
    def study(self, text: str):
        from sakshi.generate import make_whole_summary
        from sakshi.link import assemble_bank, link_question
        from sakshi.retention.bank import bank_from_dict
        from sakshi.retention.session import AdaptiveSession, SessionConfig, _Stop
        passage = " ".join(text.split())
        if len(passage.split()) < MIN_WORDS:
            emit("error", msg=f"Only {len(passage.split())} words could be read. Try a clearer photo of the page.")
            return
        if not self.models_ready.is_set():
            emit("loading")
            self.models_ready.wait()
        if self.models_error:
            emit("error", msg="The model could not be loaded: " + self.models_error)
            return
        t0 = time.time()
        emit("stage", n=2)
        summ = make_whole_summary(self.sm.b, passage, retries=0)
        summary = summ.get("text") or ""
        t_sum = round(time.time() - t0, 1)
        emit("summary", text=summary, seconds=t_sum)
        emit("stage", n=3)

        cand = self.linker.candidates(self.mp.topics(passage))
        inbox: queue.Queue = queue.Queue()
        self.stop.clear()
        written: list[float] = []
        out: dict = {}
        t_quiz = time.time()

        def on_kept(rec):
            q = {"q": rec["q"], "options": rec["options"], "answer": rec["answer"], "evidence": rec["evidence"]}
            item, _ = link_question(self.linker, cand, q, len(written))
            written.append(round(time.time() - t_quiz, 1))
            inbox.put(item)

        def writer():
            try:
                out["r"] = self.bq.quiz_2job(self.m, self.m, passage, n=10, checker=self.sm, on_kept=on_kept,
                                             should_stop=self.stop.is_set)
            except Exception as e:  # noqa: BLE001
                out["error"] = f"{type(e).__name__}: {e}"
            finally:
                inbox.put(None)

        th = threading.Thread(target=writer, daemon=True)
        th.start()
        st = self.state()
        io = DeviceIO(self.answers)
        title = "page " + now().strftime("%d %b %H:%M")
        sess = AdaptiveSession(bank_from_dict(assemble_bank(self.lib, [], passage, summary, title)), st, io,
                               SessionConfig(show_summary=False, max_questions=20), now=now())
        linked = []
        try:
            while True:
                if inbox.empty():
                    emit("waiting")
                item = inbox.get()
                if item is None:
                    break
                linked.append(item)
                sess.extend(bank_from_dict(assemble_bank(self.lib, linked, passage, summary, title)))
                sess.explore_question(item["id"])
                if self.stop.is_set():
                    raise _Stop()
        except _Stop:
            sess.stopped = True
        self.stop.set()
        res = sess.finish_stream()
        st.save(str(STATE))
        r = out.get("r") or {"kept": [], "rejected": []}
        self.last_card = {"model": "GURU-0.6B (fine-tuned Qwen3-0.6B), ExecuTorch on the Pi CPU",
                          "words": len(passage.split()), "summary_s": t_sum,
                          "questions_written": len(written), "written_at_s": written,
                          "s_per_question": round(written[-1] / len(written), 1) if written else None,
                          "size_mb": round(os.path.getsize(self.quiz_dir / "model.pte") / 2**20),
                          "peak_mb": peak_mb(), "load_s": self.load_s}
        print("RUN CARD " + json.dumps(self.last_card), file=sys.stderr, flush=True)
        right = sum(1 for a in st.attempts[-len(sess.asked):] if a["correct"]) if sess.asked else 0
        self._done("study", len(sess.asked), right, res.detected, res.suspected, st, stopped=sess.stopped,
                   error=out.get("error"))

    # ---- Mentor / Revision ----------------------------------------------------------------------------------
    def review(self, mode: str):
        from sakshi.retention.review import ReviewSession
        st = self.state()
        if not st.concepts:
            emit("done", mode=mode, asked=0, right=0, found=[], message="Study a page first.")
            return
        before = len(st.attempts)
        r = ReviewSession(st, self.lib, DeviceIO(self.answers), now()).run(mode)
        st.save(str(STATE))
        new = st.attempts[before:]
        found = [m.text for m in st.misconceptions.values()
                 if m.last_checked and m.last_checked >= now().strftime("%Y-%m-%d") and
                 m.status.startswith(("still held", "suspected"))]
        emit("done", mode=mode, asked=len(r["asked"]), right=sum(a["correct"] for a in new), found=found,
             stopped=r["stopped"], next_review=self._next_review(st),
             message="" if r["asked"] else ("Nothing waiting. Well done!" if mode == "mentor" else "Nothing to revise yet."))

    def _next_review(self, st):
        dues = [s.fsrs_card["due"] for s in st.concepts.values() if s.fsrs_card]
        return datetime.fromisoformat(min(dues)).strftime("%a %d %b") if dues else None

    def _done(self, mode, asked, right, detected, suspected, st, stopped=False, error=None):
        found = [self._mis_text(st, m) for m in list(detected) + list(suspected)]
        emit("done", mode=mode, asked=asked, right=right, found=found, stopped=stopped,
             next_review=self._next_review(st), card=self.last_card, error=error)

    @staticmethod
    def _mis_text(st, mid):
        m = st.misconceptions.get(mid)
        return m.text if m else mid

    # ---- main loop ------------------------------------------------------------------------------------------
    def serve(self):
        jobs: queue.Queue = queue.Queue()

        def reader():
            for line in sys.stdin:
                try:
                    c = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if c.get("cmd") == "answer":
                    self.answers.put(c.get("key"))
                elif c.get("cmd") == "stop":
                    self.stop.set()
                    self.answers.put(None)
                else:
                    jobs.put(c)
            jobs.put({"cmd": "quit"})

        threading.Thread(target=reader, daemon=True).start()
        emit("ready")
        while True:
            c = jobs.get()
            cmd = c.get("cmd")
            if cmd == "quit":
                return
            while not self.answers.empty():  # a stale answer from a finished session must not leak into this one
                self.answers.get_nowait()
            self.stop.clear()
            try:
                if cmd == "status":
                    self.status()
                elif cmd == "study":
                    self.study(c.get("text", ""))
                elif cmd in ("mentor", "revision"):
                    self.review(cmd)
            except Exception as e:  # noqa: BLE001
                traceback.print_exc(file=sys.stderr)
                emit("error", msg=f"{type(e).__name__}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eight-bit", action="store_true")
    a = ap.parse_args()
    Engine(a.eight_bit).serve()


if __name__ == "__main__":
    main()
