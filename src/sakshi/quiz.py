"""Layer 7: student quiz mode, the "study aid", with the Reread Loop.

Rules (bible sections 7 and 8):
  * Only GREEN items reach a student (AMBER on request, labelled; RED never).
  * Marking is exact match on the normalised answer, in CODE. The model never marks.
  * After EVERY answer the student sees the witness: the passage sentence that holds it.
  * After round one, each miss gets one new question from the SAME witness sentence
    (the Reread Loop). It is a fixed rule, not learning, and never reuses a revealed key.
  * Questions come before the summary. The summary restates the central sentences, which
    are also where questions come from, so showing it first would give the answers away.
Input and output are injected so tests can script a student.
"""
from __future__ import annotations

import string
from dataclasses import dataclass, field
from typing import Callable

from .pipeline import Item, Run, visible_items
from .text import normalize_answer

HEADER = ("Study aid. Each answer shows the sentence it comes from. "
          "If a question seems odd, trust the passage.")
LETTERS = string.ascii_uppercase


@dataclass
class QuizResult:
    score: int = 0
    total: int = 0
    missed: list[int] = field(default_factory=list)  # item ids missed in round one
    reread: list[int] = field(default_factory=list)  # 1-based sentence numbers worth rereading
    retries: list[dict] = field(default_factory=list)  # {item_id, key, witness_idx, correct}
    skipped: int = 0
    ended_early: bool = False


def _as_q(it) -> dict:
    if isinstance(it, Item):
        return {"stem": it.stem, "key": it.key, "options": it.options, "witness": it.witness,
                "witness_idx": it.witness_idx, "tier": it.tier, "id": it.id}
    return it


def resolve(answer: str, options: list[str] | None) -> str:
    """Turn what the student typed into a comparable form: a letter or option text maps to the option."""
    raw = answer.strip()
    if options:
        if len(raw) == 1 and raw.upper() in LETTERS[:len(options)]:
            return normalize_answer(options[LETTERS.index(raw.upper())])
        for o in options:
            if normalize_answer(o) == normalize_answer(raw):
                return normalize_answer(o)
    return normalize_answer(raw)


class Session:
    def __init__(self, run: Run, input_fn: Callable[[str], str] = input, print_fn: Callable[[str], None] = print,
                 include_amber: bool = False, summary_first: bool = False, max_empty: int = 3):
        self.run, self.inp, self.out = run, input_fn, print_fn
        self.include_amber, self.summary_first, self.max_empty = include_amber, summary_first, max_empty
        self.result = QuizResult()

    # -- one question ------------------------------------------------------------------
    def _ask(self, q: dict, label: str) -> bool | None:
        """Ask one question. Returns True/False, or None if the input ended (EOF)."""
        self.out(f"\n{label}")
        if q["tier"] == "AMBER":
            self.out("(check this one with your teacher)")
        self.out(q["stem"])
        opts = q["options"]
        if opts:
            for i, o in enumerate(opts):
                self.out(f"  {LETTERS[i]}) {o}")
        prompt = "Your answer (letter or word): " if opts else "Your answer: "
        answer = ""
        for _ in range(self.max_empty):
            try:
                answer = self.inp(prompt)
            except EOFError:
                return None
            if answer.strip():
                break
            self.out("Please type an answer.")
        if not answer.strip():
            self.result.skipped += 1
            correct = False
            self.out("Skipped.")
        else:
            correct = resolve(answer, opts) == normalize_answer(q["key"])
        n = q["witness_idx"] + 1
        if correct:
            self.out(f"Correct. Here is where the passage says it (sentence {n}):")
            self.out(f'  "{q["witness"]}"')
        else:
            self.out(f"Not quite. Read this sentence again (sentence {n}):")
            self.out(f'  "{q["witness"]}"')
            self.out(f"The answer is: {q['key']}")
        return correct

    def _show_summary(self) -> None:
        text = self.run.summary.get("text", "")
        if text:
            self.out("\nIn short:")
            self.out(f"  {text}")

    # -- the session ---------------------------------------------------------------------
    def run_quiz(self) -> QuizResult:
        items = visible_items(self.run, self.include_amber)
        r = self.result
        r.total = len(items)
        self.out(HEADER)
        if not items:
            self.out("\nNo questions passed the checks for this passage.")
            self._show_summary()
            return r
        if self.summary_first:
            self._show_summary()

        revealed: set[str] = set()
        for n, it in enumerate(items, 1):
            q = _as_q(it)
            res = self._ask(q, f"Question {n} of {len(items)}")
            if res is None:
                r.ended_early = True
                return r
            revealed.add(normalize_answer(q["key"]))
            if res:
                r.score += 1
            else:
                r.missed.append(q["id"])
        missed_items = [i for i in items if i.id in r.missed]

        # Reread Loop: one new question from the same witness sentence, for each miss.
        for it in missed_items:
            n = it.witness_idx + 1
            res_q = it.reserve
            if res_q and normalize_answer(res_q["key"]) not in revealed:
                self.out(f"\nYou missed sentence {n}. Read it once more, then try this one.")
                q = {"stem": res_q["stem"], "key": res_q["key"], "options": res_q.get("options"), "tier": "GREEN",
                     "witness": res_q["witness"], "witness_idx": res_q["witness_idx"]}
                res = self._ask(q, "Try again")
                if res is None:
                    r.ended_early = True
                    return r
                revealed.add(normalize_answer(q["key"]))
                r.retries.append({"item_id": it.id, "key": q["key"], "witness_idx": q["witness_idx"], "correct": res})
            else:
                self.out(f"\nSentence {n} is worth one more read:")
                self.out(f'  "{it.witness}"')

        r.reread = sorted({it.witness_idx + 1 for it in missed_items})
        line = f"\nYou got {r.score} of {r.total}."
        if r.retries:
            line += f" On the second try you got {sum(x['correct'] for x in r.retries)} of {len(r.retries)}."
        self.out(line)
        if r.reread:
            self.out("Worth rereading: " + ", ".join(f"sentence {n}" for n in r.reread) + ".")
        if not self.summary_first:
            self._show_summary()
        return r
