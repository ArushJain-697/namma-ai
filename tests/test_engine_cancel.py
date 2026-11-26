"""Back on the device: the REAL scripts/sakshi_engine.py in a subprocess, with the models replaced by a slow stub
(StubBackend text, a fixed time per call, cancellable like the ExecuTorch runner). No ExecuTorch needed.

Regression tests for: Back hanging the engine (finish_stream blocked on a second answer; the main loop blocked on the
writer), and the old writer thread reviving when the next session cleared the shared stop flag and then running
model calls at the same time as the new session."""
import json
import os
import queue
import subprocess
import sys
import textwrap
import threading
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HARNESS = textwrap.dedent('''
    import os, sys, threading, time, types
    from pathlib import Path
    sys.dont_write_bytecode = True
    REPO = os.environ["REPO"]
    sys.path.insert(0, REPO + "/src"); sys.path.insert(0, REPO + "/scripts")
    from sakshi.backends.stub import StubBackend

    ACTIVE = {"n": 0, "max": 0}
    LOCK = threading.Lock()

    class SlowStub:
        """StubBackend text after CALL_S seconds; cancel() cuts the call short, like runner.stop()."""
        def __init__(self):
            self.stub, self.cancelled = StubBackend(), threading.Event()
        def cancel(self):
            self.cancelled.set()
        def generate(self, prompt):
            with LOCK:
                ACTIVE["n"] += 1; ACTIVE["max"] = max(ACTIVE["max"], ACTIVE["n"])
                sys.stderr.write(f"[overlap] {ACTIVE['max']}\\n"); sys.stderr.flush()
            self.cancelled.clear()
            end = time.time() + float(os.environ.get("CALL_S", "0.3"))
            while time.time() < end and not self.cancelled.is_set():
                time.sleep(0.01)
            with LOCK:
                ACTIVE["n"] -= 1
            return self.stub.generate(prompt).text

    bq = types.ModuleType("backup_quiz")
    class Model:
        def __init__(self, path): self.b, self.calls = SlowStub(), []
        def run(self, system, user, max_new, examples=(), kind="", prefix="", stop=None):
            return prefix + self.b.generate(user)
    bq.Model = Model
    bq.summary_in_parts = lambda m, passage: {"text": m.run("s", passage, 8).strip() or "A summary."}
    def quiz_2job(mq, mw, passage, n=4, seed=None, checker=None, on_kept=None, should_stop=None, **kw):
        kept = []
        for i in range(8):
            if len(kept) == n or (should_stop and should_stop()):
                break
            mq.run("q", passage, 8)
            rec = {"q": f"Why {i}?", "options": ["right", "w1", "w2", "w3"], "answer": 0, "evidence": "e"}
            kept.append(rec)
            sys.stderr.write(f"[writer] {passage[:6]} q{i}\\n"); sys.stderr.flush()
            on_kept(rec)
        return {"kept": kept, "rejected": [], "calls": []}
    bq.quiz_2job = quiz_2job
    sys.modules["backup_quiz"] = bq

    import sakshi.mapper, sakshi.link
    app = types.ModuleType("sakshi_app")
    HERE = Path(os.environ["FAKE_MODELS"])
    app.model_dirs = lambda eight_bit: (HERE, HERE)
    sys.modules["sakshi_app"] = app
    from sakshi.misconceptions import Library
    LIB = Library.load()
    CID = next(c for c, v in LIB.concepts.items() if v.get("prereqs"))
    class FakeMapper:
        def __init__(self, lib, enc): self.lib = lib
        def topics(self, passage): return {}
    class FakeLinker:
        def __init__(self, mp): self.lib = mp.lib
        def candidates(self, topics): return []
    def link_question(linker, cand, q, i):
        return ({"id": f"g{i + 1}", "concept": CID, "type": "recall", "stem": q["q"],
                 "options": [{"key": k, "text": t, "correct": j == 0, "misconception": None}
                             for j, (k, t) in enumerate(zip("ABCD", q["options"]))], "explanation": "e"}, [])
    sakshi.mapper.Mapper, sakshi.mapper.PteEncoders = FakeMapper, (lambda: None)
    sakshi.link.Linker, sakshi.link.link_question = FakeLinker, link_question
    import sakshi_engine
    sakshi_engine.main()
''')

PAGE_A = "AAAAAA " + " ".join(["Iron rusts when water and air react with it over many days."] * 6)
PAGE_B = "BBBBBB " + " ".join(["Plants make food from sunlight, water and carbon dioxide."] * 6)


class Eng:
    def __init__(self, tmp_path, call_s):
        (tmp_path / "models").mkdir()
        (tmp_path / "models" / "model.pte").write_bytes(b"x")
        (tmp_path / "h.py").write_text(HARNESS)
        env = dict(os.environ, REPO=ROOT, FAKE_MODELS=str(tmp_path / "models"), CALL_S=str(call_s),
                   SAKSHI_STATE=str(tmp_path / "learner.json"), PYTHONDONTWRITEBYTECODE="1")
        self.p = subprocess.Popen([sys.executable, str(tmp_path / "h.py")], env=env, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.ev, self.err = queue.Queue(), []
        threading.Thread(target=lambda: [self.ev.put(json.loads(ln)) for ln in self.p.stdout], daemon=True).start()
        threading.Thread(target=lambda: [self.err.append((time.time(), ln.strip())) for ln in self.p.stderr],
                         daemon=True).start()
        assert self.wait("ready", 60)

    def send(self, **c):
        self.p.stdin.write(json.dumps(c) + "\n")
        self.p.stdin.flush()

    def wait(self, kind, t, job=None):
        end = time.time() + t
        while time.time() < end:
            try:
                e = self.ev.get(timeout=max(0.01, end - time.time()))
            except queue.Empty:
                return None
            if e["type"] == kind and (job is None or e.get("job") == job):
                return e
        return None

    def max_overlap(self):
        return max([int(ln.split()[1]) for _, ln in self.err if ln.startswith("[overlap]")] or [0])

    def close(self):
        self.p.kill()


@pytest.fixture
def eng(request, tmp_path):
    e = Eng(tmp_path, getattr(request, "param", 0.3))
    yield e
    e.close()


def test_back_during_a_question_ends_the_session_and_the_engine_stays_responsive(eng):
    eng.send(cmd="study", text=PAGE_A, job=1)
    assert eng.wait("question", 20, job=1)
    t = time.time()
    eng.send(cmd="stop", job=1)
    done = eng.wait("done", 5, job=1)
    assert done and done["stopped"] is True and time.time() - t < 4  # used to hang in finish_stream forever
    eng.send(cmd="status")
    assert eng.wait("status", 5)


@pytest.mark.parametrize("eng", [1.0], indirect=True)
def test_old_writer_never_revives_or_overlaps_the_next_session(eng):
    eng.send(cmd="study", text=PAGE_A, job=1)
    assert eng.wait("question", 20, job=1)
    eng.send(cmd="stop", job=1)
    assert eng.wait("done", 5, job=1)
    t_done = time.time()
    eng.send(cmd="stop", job=1)  # a late second Back for the old session must not cancel the new one
    eng.send(cmd="study", text=PAGE_B, job=2)
    assert eng.wait("question", 20, job=2)
    time.sleep(3)
    late_a = [ln for ts, ln in eng.err if ln.startswith("[writer] AAAAAA") and ts > t_done + 0.5]
    assert late_a == []                 # the old writer stayed dead after the next session began
    assert eng.max_overlap() == 1       # never two model calls at once
    assert any(ln.startswith("[writer] BBBBBB") for _, ln in eng.err)


@pytest.mark.parametrize("eng", [15.0], indirect=True)
def test_back_while_the_model_is_writing_cancels_the_call_in_flight(eng):
    eng.send(cmd="study", text=PAGE_A, job=7)
    assert eng.wait("stage", 20, job=7)  # summary call of 15 s now running
    time.sleep(0.5)
    t = time.time()
    eng.send(cmd="stop", job=7)
    done = eng.wait("done", 5, job=7)
    assert done and done["stopped"] and time.time() - t < 3


def test_events_carry_the_job_id(eng):
    eng.send(cmd="study", text=PAGE_A, job="x9")
    q = eng.wait("question", 20)
    assert q["job"] == "x9"
