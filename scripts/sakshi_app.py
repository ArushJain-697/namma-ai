#!/usr/bin/env python3
"""Sakshi as ONE program: passage -> summary + quiz (GURU-0.6B, ExecuTorch) -> each wrong option linked to a
misconception (ExecuTorch helper models) -> adaptive session (Bayes, BKT, walk down / climb up, FSRS) -> saved
learner. Later days: `review`. Everything in one process and one Python environment (the same as the Pi's).

  .venv-export/bin/python scripts/sakshi_app.py study PASSAGE.txt [--questions 5] [--student learns|stubborn] [--quiz-only]
  .venv-export/bin/python scripts/sakshi_app.py review [--student ...] [--now 2026-11-16T09:00]
  .venv-export/bin/python scripts/sakshi_app.py plan
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
STATE = ROOT / "state" / "learner.json"


class Clock:
    def __init__(self):
        self.t0 = self.last = time.time()
        self.marks: dict[str, float] = {}

    def mark(self, name: str) -> float:
        now = time.time()
        self.marks[name] = round(now - self.last, 2)
        self.last = now
        return self.marks[name]

    def total(self) -> float:
        return round(time.time() - self.t0, 2)


def peak_mb() -> int:
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(r / (2**20 if sys.platform == "darwin" else 2**10))


def model_dirs(eight_bit: bool) -> tuple[Path, Path]:
    models = ROOT / "models"
    quiz = models / ("guru-0.6b-2job-8bit" if eight_bit else "guru-0.6b-2job")
    dot = any("asimddp" in l for l in open("/proc/cpuinfo")) if os.path.exists("/proc/cpuinfo") else True
    summ = models / ("qwen3-0.6b-fast" if dot else "qwen3-0.6b-portable")
    if not summ.exists():
        summ = models / "qwen3-0.6b-8da4w"  # the Mac's name for the same model
    return quiz, summ


def make_io(kind: str | None, holds: set[str], verbose: bool):
    from sakshi.retention.io import ModelStudent, TerminalIO
    if kind is None:
        return TerminalIO(verbose=verbose)
    return ModelStudent(holds=holds, echo=True, verbose=verbose, learns_after_feedback=kind == "learns", guess_seed=1)


def cmd_study(a) -> None:
    import backup_quiz as bq
    from sakshi.generate import make_whole_summary
    from sakshi.link import Linker, build_bank
    from sakshi.mapper import Mapper, PteEncoders
    from sakshi.misconceptions import Library
    from sakshi.retention.bank import bank_from_dict
    from sakshi.retention.session import AdaptiveSession, SessionConfig
    from sakshi.retention.state import LearnerState

    clock = Clock()
    passage = Path(a.passage).read_text().strip()
    quiz_dir, sum_dir = model_dirs(a.eight_bit)
    m = bq.Model(quiz_dir)
    sm = m if a.one_model else bq.Model(sum_dir)
    lib = Library.load()
    mp = Mapper(lib, PteEncoders())
    clock.mark("load")
    print(f"[loaded GURU + helpers in {clock.marks['load']} s]", flush=True)

    summ = make_whole_summary(sm.b, passage, retries=0)
    clock.mark("summary")
    print(f"\nSUMMARY ({clock.marks['summary']} s)\n{summ.get('text', '')}\n", flush=True)

    linker = Linker(mp)
    cand = linker.candidates(mp.topics(passage))
    if a.quiz_only:
        quiz_batch(a, bq, m, sm, mp, passage, summ, clock, quiz_dir)
        return
    stream_session(a, bq, m, sm, lib, linker, cand, passage, summ, clock, quiz_dir)


def quiz_batch(a, bq, m, sm, mp, passage, summ, clock, quiz_dir) -> None:
    """All questions in one go (the old way; for measuring the quiz alone)."""
    from sakshi.link import build_bank
    ready: list[float] = []
    t_quiz = time.time()

    def shown(rec):
        ready.append(round(time.time() - t_quiz, 1))
        print(f"  question {len(ready)} ready at {ready[-1]} s: {rec['q']}", flush=True)

    r = bq.quiz_2job(m, m, passage, n=a.questions, checker=sm, w_runs=a.w_runs, self_check_on=not a.no_check,
                     on_kept=shown)
    clock.mark("quiz")
    qs = [{"q": q["q"], "options": q["options"], "answer": q["answer"], "evidence": q["evidence"]} for q in r["kept"]]
    d, log = build_bank(mp, passage, summ.get("text", ""), qs, title=Path(a.passage).stem)
    clock.mark("link")
    n = len(qs)
    calls = r["calls"] + ([c for c in sm.calls if c["kind"] == "check"] if sm is not m else [])
    card = {"model": f"GURU-0.6B ({quiz_dir.name}), ExecuTorch XNNPACK, Arm/Apple CPU",
            "questions": n, "attempted": n + len(r["rejected"]),
            "load_s": clock.marks["load"], "summary_s": clock.marks["summary"], "quiz_s": clock.marks["quiz"],
            "link_s": clock.marks["link"], "s_per_question": round(clock.marks["quiz"] / max(1, n), 1),
            "first_question_s": ready[0] if ready else None,
            "model_calls": {k: [sum(c["kind"] == k for c in calls), round(sum(c["s"] for c in calls if c["kind"] == k), 1)]
                            for k in ("question", "distractor", "check")},
            "peak_mb": peak_mb(), "words": len(passage.split()),
            "rejected": [x["reason"][:40] for x in r["rejected"]]}
    print("\nLINKS")
    for x in log:
        print(f"  Q{x['q']} '{x['option']}' -> {x['misconception'] or '(no match, plain wrong answer)'}")
    print("\nRUN CARD " + json.dumps(card))
    out = ROOT / "state" / "last_bank.json"
    out.parent.mkdir(exist_ok=True)
    json.dump(d, open(out, "w"), indent=1)


def stream_session(a, bq, m, sm, lib, linker, cand, passage, summ, clock, quiz_dir) -> None:
    """The child sees question 1 as soon as it is written. A background thread writes (and links) the next
    question while the child reads and answers the current one, and the session grows as questions arrive."""
    import queue
    import threading
    from sakshi.link import assemble_bank, link_question
    from sakshi.retention.bank import bank_from_dict
    from sakshi.retention.session import AdaptiveSession, SessionConfig, _Stop
    from sakshi.retention.state import LearnerState

    title, summary = Path(a.passage).stem, summ.get("text", "")
    inbox: queue.Queue = queue.Queue()
    stop = threading.Event()
    t_quiz = time.time()
    written: list[float] = []
    out: dict = {}

    def on_kept(rec):  # runs in the writer thread
        q = {"q": rec["q"], "options": rec["options"], "answer": rec["answer"], "evidence": rec["evidence"]}
        item, rows = link_question(linker, cand, q, len(written))
        written.append(round(time.time() - t_quiz, 1))
        inbox.put((item, rows))

    def writer():
        try:
            out["r"] = bq.quiz_2job(m, m, passage, n=a.questions, checker=sm, w_runs=a.w_runs,
                                    self_check_on=not a.no_check, on_kept=on_kept, should_stop=stop.is_set)
        except Exception as e:  # noqa: BLE001
            out["error"] = f"{type(e).__name__}: {e}"
        finally:
            inbox.put(None)

    threading.Thread(target=writer, daemon=True).start()

    state = LearnerState() if a.fresh else LearnerState.load(str(a.state))
    io = make_io(a.student, set(), a.verbose)
    if a.student and a.think:
        io.answer = slow(io.answer, a.think)  # a pretend child who takes time to read and think
    sess = AdaptiveSession(bank_from_dict(assemble_bank(lib, [], passage, summary, title)), state, io,
                           SessionConfig(show_summary=False, max_questions=a.max_session), now=datetime.now(timezone.utc))
    linked, waits, links = [], [], []
    try:
        while True:
            t_wait = time.time()
            if inbox.empty():
                print("  (writing the next question...)", flush=True)
            got = inbox.get()
            if got is None:
                break
            waits.append(round(time.time() - t_wait, 1))
            item, rows = got
            linked.append(item)
            links += rows
            if a.student and not io.holds:  # the pretend child holds the first belief GURU's options revealed
                first = next((o["misconception"] for o in item["options"] if o["misconception"]), None)
                if first:
                    io.holds = {first} | (stubborn_extra(lib, first) if a.student == "stubborn" else set())
            sess.extend(bank_from_dict(assemble_bank(lib, linked, passage, summary, title)))
            sess.explore_question(item["id"])
    except _Stop:
        sess.stopped = True
    stop.set()  # the child stopped or we are done: the writer finishes its current call and ends
    sess.finish_stream()
    state.save(str(a.state))
    r = out.get("r") or {"kept": [], "rejected": [], "calls": []}
    card = {"model": f"GURU-0.6B ({quiz_dir.name}), ExecuTorch XNNPACK", "mode": "streaming",
            "load_s": clock.marks["load"], "summary_s": clock.marks["summary"],
            "guru_questions": len(linked), "rejected": [x["reason"][:40] for x in r["rejected"]],
            "written_at_s": written, "s_per_question_writing": round(written[-1] / len(written), 1) if written else None,
            "child_waited_s": waits, "first_question_wait_s": waits[0] if waits else None,
            "later_waits_s": round(sum(waits[1:]), 1),
            "session_questions": len(sess.asked), "peak_mb": peak_mb()}
    if "error" in out:
        card["error"] = out["error"]
    print("\nRUN CARD " + json.dumps(card))
    print(f"Saved learner to {a.state}. Come back later: scripts/sakshi_app.py review")


def slow(fn, seconds: float):
    def wrapped(q):
        time.sleep(seconds)
        return fn(q)
    return wrapped


def stubborn_extra(lib, mid: str) -> set[str]:
    from sakshi.retention.review import RelatedBeliefs
    rel = RelatedBeliefs(lib)
    return {k for k, v in rel.root.items() if v == rel.root.get(mid)}


def cmd_review(a) -> None:
    from sakshi.misconceptions import Library
    from sakshi.retention.review import ReviewSession
    from sakshi.retention.state import LearnerState
    state = LearnerState.load(str(a.state))
    if not state.concepts:
        sys.exit("No learner yet: run `study` first.")
    now = datetime.fromisoformat(a.now).replace(tzinfo=timezone.utc) if a.now else datetime.now(timezone.utc)
    holds = {k for k, v in state.misconceptions.items() if a.student == "stubborn"}
    ReviewSession(state, Library.load(), make_io(a.student, holds, a.verbose), now).run()
    state.save(str(a.state))


def cmd_plan(a) -> None:
    from sakshi.retention.fsrs_sched import make_scheduler
    from sakshi.retention.ranker import revision_plan
    from sakshi.misconceptions import Library
    from sakshi.retention.state import LearnerState
    state, lib = LearnerState.load(str(a.state)), Library.load()
    now = datetime.fromisoformat(a.now).replace(tzinfo=timezone.utc) if a.now else datetime.now(timezone.utc)
    names = {c: (lib.concepts.get(c) or {}).get("name", c) for c in state.concepts}
    for i, r in enumerate(revision_plan(state, names, make_scheduler(), now), 1):
        print(f"{i}. {r.name:<40} mastery {r.mastery:4.0%}  recall {r.recall:4.0%}  due {r.due:%a %d %b}" if r.due
              else f"{i}. {r.name:<40} mastery {r.mastery:4.0%}  not tested yet")


def own_screen() -> None:
    """The ExecuTorch backend collects the model's text by pointing file descriptor 1 at a temp file while it
    writes. With the writer in a background thread, the child's screen (also fd 1) would vanish into that file and
    leak into the model's text (seen 14 Nov: a different wrong-answer list, one question lost). So Python's output
    goes to a private copy of the terminal that the capture never touches."""
    sys.stdout.flush()
    sys.stdout = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")


def main() -> None:
    own_screen()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("study")
    s.add_argument("passage")
    s.add_argument("--questions", type=int, default=10, help="most GURU questions to write (the passage may give fewer)")
    s.add_argument("--w-runs", type=int, default=1, help="wrong-answer generations per question")
    s.add_argument("--no-check", action="store_true", help="skip the answer self-check")
    s.add_argument("--one-model", action="store_true", help="GURU also writes the summary and does the check")
    s.add_argument("--eight-bit", action="store_true")
    s.add_argument("--quiz-only", action="store_true")
    s.add_argument("--fresh", action="store_true")
    s.add_argument("--think", type=float, default=0, help="pretend child: seconds to read and answer each question")
    s.add_argument("--max-session", type=int, default=30, help="most questions in one sitting (GURU + graph)")
    for p in (s, sub.add_parser("review"), sub.add_parser("plan")):
        p.add_argument("--state", default=str(STATE))
        p.add_argument("--student", choices=["learns", "stubborn"], default=None)
        p.add_argument("--now", default=None)
        p.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    {"study": cmd_study, "review": cmd_review, "plan": cmd_plan}[a.cmd](a)


if __name__ == "__main__":
    main()
