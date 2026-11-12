"""Baseline arms (build map T25): the "everyone generates quizzes" approach we compare against.

The model writes the question AND the key in one call, with no code choosing the answer and no checks.
Three arms, all given the passage in context (red-team F1, F13):
  targeted  told which sentence to write about
  free      asked for 3 questions about the passage; only items touching the planted sentence are scored,
            and COVERAGE (how often any item touched it) is reported
  grounded  the targeted arm plus "answer only from the passage and quote the supporting sentence":
            the honest prompt-only fix. If it closes most of the gap, we report that.

Format note: a plain "Question:/Answer:" line format, not JSON. LENTERA-style JSON from a 1B model breaks
often, and a baseline that fails on formatting would flatter us. Parsing is forgiving for the same reason, and
nothing here ever invents an answer when parsing fails (an unparseable output is counted as such).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .backends.base import Backend, chat_for
from .text import content_stems, contains_term

MODES = ("targeted", "free", "grounded")

_FORMAT = "Reply in exactly this format and nothing else:\nQuestion: <one question>\nAnswer: <the short answer>"
SYSTEM = {
    "targeted": "You write quiz questions for school students. " + _FORMAT,
    "grounded": ("You write quiz questions for school students. Answer ONLY from the passage, not from what you "
                 "already know. Reply in exactly this format and nothing else:\nQuestion: <one question>\n"
                 "Answer: <the short answer>\nSupport: <copy the sentence from the passage that proves the answer>"),
    "free": ("You write quiz questions for school students. Write 3 different questions, each in exactly this "
             "format:\nQuestion: <one question>\nAnswer: <the short answer>"),
}


@dataclass
class BaselineItem:
    question: str
    answer: str
    support: str | None = None


def user_prompt(mode: str, passage: str, sentence: str | None) -> str:
    if mode == "free":
        return f"Passage:\n{passage}\n\nWrite 3 different quiz questions about the passage."
    return f"Passage:\n{passage}\n\nWrite one quiz question about this sentence of the passage: {sentence}"


def parse_qa(text: str) -> list[BaselineItem]:
    """Forgiving line parser. Returns only items that have both a question and an answer."""
    items: list[BaselineItem] = []
    cur: dict[str, str] = {}
    def flush():
        if cur.get("question") and cur.get("answer"):
            items.append(BaselineItem(cur["question"].strip(), cur["answer"].strip(), cur.get("support")))
        cur.clear()
    for line in (text or "").splitlines():
        m = re.match(r"\s*(question|answer|support)\s*[:\-]\s*(.*)", line, re.I)
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2).strip()
        if key == "question":
            flush()
        cur[key] = val
    flush()
    return items


def run_baseline(backend: Backend, passage: str, mode: str, sentence: str | None = None, extra: dict | None = None,
                 temperature: float = 0.0, seed: int = 0) -> tuple[list[BaselineItem], str]:
    """One model call. Returns (parsed items, raw text). `extra` is read by the stub only."""
    if mode not in MODES:
        raise ValueError(f"unknown baseline mode {mode!r}")
    prompt = chat_for(backend, SYSTEM[mode], user_prompt(mode, passage, sentence))
    payload = {"passage": passage, "sentence": sentence or "", **(extra or {})}
    res = backend.generate(prompt, max_new_tokens=160 if mode == "free" else 90, temperature=temperature, seed=seed,
                           task=f"baseline_{mode}", payload=payload)
    return parse_qa(res.text), res.text


def touches(item: BaselineItem, sentence: str) -> bool:
    """Does a free-form item concern this sentence? Shares 2+ content words with it, or its answer is in it."""
    shared = set(content_stems(item.question + " " + item.answer)) & set(content_stems(sentence))
    return len(shared) >= 2 or (bool(item.answer) and contains_term(sentence, item.answer))
