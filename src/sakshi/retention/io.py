"""Input and output for the adaptive session. The engine talks only to this interface, so the same
session runs in a terminal, on the tutor box (screen + buttons), or with a scripted student in tests.
"""
from __future__ import annotations

from .bank import Question


class IO:
    def show(self, text: str) -> None:
        """Something for the student: summary, feedback, a step in the walk."""
        raise NotImplementedError

    def show_question(self, q: Question, number: int) -> None:
        raise NotImplementedError

    def answer(self, q: Question) -> str | None:
        """The option key the student picked, or None to stop the session."""
        raise NotImplementedError

    def log(self, text: str) -> None:
        """Engine reasoning for teachers and judges (never shown on the student's screen)."""

    def taught(self, concept_id: str) -> None:
        """Called after the student has been shown the fix for a concept. Only pretend students use it."""


class TerminalIO(IO):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def show(self, text: str) -> None:
        print(text, flush=True)

    def show_question(self, q: Question, number: int) -> None:
        kind = "Apply it" if q.type == "application" else "Recall"
        print(f"\nQ{number} ({kind}). {q.stem}")
        for o in q.options:
            print(f"   {o.key}) {o.text}")

    def answer(self, q: Question) -> str | None:
        keys = [o.key for o in q.options]
        while True:
            try:
                raw = input(f"Your answer ({'/'.join(keys)}, or q to stop): ").strip().upper()
            except EOFError:
                return None
            if raw == "Q":
                return None
            if raw in keys:
                return raw
            print(f"Please type one of {', '.join(keys)}.")

    def log(self, text: str) -> None:
        if self.verbose:
            print(f"    \033[2m[engine] {text}\033[0m", flush=True)


class ScriptedIO(IO):
    """Plays a fixed list of answers and records everything shown. For tests and recorded demos."""

    def __init__(self, answers: list[str], echo: bool = False, verbose: bool = False):
        self.answers = [a.strip().upper() for a in answers]
        self.lines: list[str] = []
        self.logs: list[str] = []
        self.asked: list[str] = []
        self.echo, self.verbose = echo, verbose

    def _out(self, text: str) -> None:
        self.lines.append(text)
        if self.echo:
            print(text, flush=True)

    def show(self, text: str) -> None:
        self._out(text)

    def show_question(self, q: Question, number: int) -> None:
        self.asked.append(q.id)
        self._out(f"\nQ{number}. {q.stem}\n" + "\n".join(f"   {o.key}) {o.text}" for o in q.options))

    def answer(self, q: Question) -> str | None:
        if not self.answers:
            return None
        a = self.answers.pop(0)
        self._out(f"Your answer: {a}")
        return a

    def log(self, text: str) -> None:
        self.logs.append(text)
        if self.echo and self.verbose:
            print(f"    \033[2m[engine] {text}\033[0m", flush=True)


class ModelStudent(ScriptedIO):
    """A pretend student who knows some concepts and holds some misconceptions (by id).

    Knows the concept -> picks the right answer. Holds a misconception on this question -> picks it.
    Otherwise -> picks the first wrong option. Used by tests and by the demo's `--student` option.
    """

    def __init__(self, knows: set[str] = frozenset(), holds: set[str] = frozenset(), echo: bool = False,
                 verbose: bool = False, learns_after_feedback: bool = True):
        super().__init__([], echo, verbose)
        self.knows, self.holds = set(knows), set(holds)
        self.learns = learns_after_feedback

    def answer(self, q: Question) -> str | None:
        if q.concept in self.knows:
            a = q.correct_key
        else:
            held = [o for o in q.options if o.misconception in self.holds]
            a = held[0].key if held else next(o.key for o in q.options if not o.correct)
        self._out(f"Your answer: {a}")
        return a

    def taught(self, concept_id: str) -> None:
        if self.learns:  # this student understands once the fix is shown: the demo's happy path
            self.knows.add(concept_id)
