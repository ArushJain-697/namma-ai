"""Deterministic stand-in for the model, with fault injection.

Lets every check, the pipeline and the quiz be tested without a Pi. Modes:
  faithful   behaves well
  bad_number changes a number (or adds a new one)
  invent     adds a fluent invented fact
  negate     flips the meaning with a negation
  hard_words rewrites in hard, unsupported words
  empty      returns nothing
  echo       echoes the prompt back
  leak       (stems) puts the answer in the question
  nomark     (stems) returns a statement with no question mark
  long       (stems) returns a question over 20 words
`fail_first=k`: fault only for the first k calls per input, then behave (tests retries).
`fail_first=None`: fault on every call.
"""
from __future__ import annotations

import re
import time
import zlib
from collections import defaultdict

from ..text import blank_term, iter_tokens, tokens
from .base import Backend, GenResult

MODES = ("faithful", "bad_number", "invent", "negate", "hard_words", "empty", "echo", "leak", "nomark", "long",
         "off_key")  # off_key: questions look fine but, answered back, give something other than the key


class StubBackend(Backend):
    name = "stub"

    def __init__(self, mode: str = "faithful", fail_first: int | None = None, baseline: str = "memory",
                 baseline_rate: float = 1.0, free_covers: bool = True, summary_leak: bool = False):
        if mode not in MODES:
            raise ValueError(f"unknown stub mode {mode!r}")
        if baseline not in ("memory", "passage"):
            raise ValueError("baseline must be 'memory' or 'passage'")
        self.mode = mode
        self.fail_first = fail_first
        # Baseline behaviour (STUB ONLY, read from the payload): does the one-call quiz writer answer from
        # memory or from the passage, for what share of cases; does a whole-passage summary leak the memory value.
        self.baseline, self.baseline_rate = baseline, (baseline_rate if baseline == "memory" else 0.0)
        self.free_covers, self.summary_leak = free_covers, summary_leak
        self.calls: list[dict] = []
        self._seen: dict[tuple, int] = defaultdict(int)

    # -- helpers -----------------------------------------------------------------
    def _faulty(self, key: tuple) -> bool:
        if self.mode == "faithful":
            return False
        n = self._seen[key]
        self._seen[key] += 1
        return self.fail_first is None or n < self.fail_first

    @staticmethod
    def _simplify_ok(sentence: str) -> str:
        return sentence

    @staticmethod
    def _stem_ok(sentence: str, answer: str) -> str:
        blanked = blank_term(sentence, answer)
        words = blanked.split()
        idx = next((i for i, w in enumerate(words) if "_____" in w), 0)
        window = words[max(0, idx - 6): idx + 7]
        return "What word is missing: " + " ".join(window).rstrip(".!?,;:") + "?"

    def _simplify_fault(self, sentence: str) -> str:
        m = self.mode
        if m == "bad_number":
            nums = re.findall(r"\d+", sentence)
            if nums:
                return sentence.replace(nums[0], str(int(nums[0]) + 90), 1)
            return sentence.rstrip(".") + " in 1989."
        if m == "invent":
            return sentence + " Scientists in Paris proved this in a famous experiment."
        if m == "negate":
            for a, b in ((" is ", " is not "), (" are ", " are not "), (" does ", " does not "), (" can ", " can not ")):
                if a in sentence:
                    return sentence.replace(a, b, 1)
            return "It is not true that " + sentence[0].lower() + sentence[1:]
        if m == "hard_words":
            return "Ferrous substances undergo oxidative degradation upon atmospheric exposure."
        if m == "empty":
            return ""
        return sentence

    def _stem_fault(self, sentence: str, answer: str) -> str:
        m = self.mode
        if m == "leak":
            return f"Why is {answer} important in this passage?"
        if m == "nomark":
            return "Name the missing word in this sentence."
        if m == "long":
            return "What is the one single word that is missing from the long sentence which we have just read together " \
                   "in class today about the topic of this passage?"
        if m == "empty":
            return ""
        return self._stem_ok(sentence, answer)

    def _follows_memory(self, payload: dict) -> bool:
        h = zlib.crc32((payload.get("passage_value", "") + payload.get("sentence", "")).encode()) % 100
        return h < self.baseline_rate * 100

    def _baseline(self, task: str, payload: dict) -> str:
        sent = payload.get("sentence", "")
        val = payload.get("memory_value", "") if self._follows_memory(payload) else payload.get("passage_value", "")
        q = f"According to the text: {sent.rstrip('.')}, what is the value?"
        if task == "baseline_free":
            first = q if self.free_covers else "What is this passage about?"
            return (f"Question: {first}\nAnswer: {val if self.free_covers else 'school'}\n"
                    "Question: What is this passage about?\nAnswer: school\n"
                    "Question: Who is mentioned?\nAnswer: students\n")
        out = f"Question: {q}\nAnswer: {val}"
        return out + (f"\nSupport: {sent}" if task == "baseline_grounded" else "")

    def _whole_summary(self, payload: dict) -> str:
        if self.summary_leak:
            return f"The text says the value is {payload.get('memory_value', '')}."
        return payload.get("sentence", "")

    # -- interface ---------------------------------------------------------------
    def generate(self, prompt, max_new_tokens=64, temperature=0.0, seed=None, task=None, payload=None) -> GenResult:
        t0 = time.perf_counter()
        payload = payload or {}
        self.calls.append({"task": task, "temperature": temperature, "seed": seed})
        if self.mode == "echo" and self._faulty((task, prompt)):
            text = prompt
        elif task in ("baseline_targeted", "baseline_free", "baseline_grounded"):
            text = self._baseline(task, payload)
        elif task == "whole_summary":
            text = self._whole_summary(payload)
        elif task == "simplify":
            s = payload.get("sentence", "")
            text = self._simplify_fault(s) if self._faulty((task, s)) else self._simplify_ok(s)
        elif task == "stem":
            s, a = payload.get("sentence", ""), payload.get("answer", "")
            faulty = self.mode != "off_key" and self._faulty((task, s, a))
            text = self._stem_fault(s, a) if faulty else self._stem_ok(s, a)
        elif task == "diagnostic":  # sakshi.diagnostic: a well-formed item built from the payload (stub only)
            import json as _json
            words = [w.strip(".,;:") for w in payload.get("evidence", "").split() if len(w.strip(".,;:")) > 3]
            answer = " ".join(words[-2:]) if words else "it"
            opts = [{"b": f"B{i + 1}", "why": "follows the belief",
                     "text": " ".join(((m.get("probe") or {}).get("wrong_answer") or m["statement"]).split()[:6])}
                    for i, m in enumerate(payload.get("beliefs", [])[:3])]
            text = _json.dumps({"answer": answer, "stem": "According to the passage, what is true here?", "options": opts})
        elif task == "answer":  # answering its own question back (generate.verify_stem)
            a = payload.get("answer", "")
            off = self.mode == "off_key" and self._faulty((task, payload.get("question", ""), a))
            text = "something else" if off else a
        else:
            text = "stub output"
        wall = time.perf_counter() - t0
        return GenResult(text=text, prompt_tokens=len(prompt.split()), new_tokens=len(text.split()),
                         ttft_ms=0.0, tokens_per_s=None, wall_s=wall)

    def info(self):
        return {"name": f"stub:{self.mode}", "model_path": None, "model_bytes": 0, "load_s": 0.0}
