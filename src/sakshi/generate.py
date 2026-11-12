"""Layers 2 and 4: model-written wording, always fenced by code.

The model never decides facts:
  * summary: code picks the central sentences; the model only simplifies ONE sentence at a
    time and sees nothing else, so it cannot import facts from elsewhere. Each rewrite is
    checked against its own source sentence; on failure the source sentence is used verbatim
    and labelled FALLBACK. "No witness, no summary sentence."
  * stems: the model is given the witness sentence and the code-picked answer and writes only
    the question wording. The key is never read from model output.
Retries vary temperature, because the runner has no seed and temperature 0 repeats itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .backends.base import Backend, chat_for
from .checks import (HARD, WARN, CheckResult, failures, reasons, stem_checks, summary_overall_checks,
                     summary_sentence_checks, tier)
from .select import Analysis
from .text import blank_term, stem, tokens

TEMPERATURES = (0.0, 0.4, 0.7)
SEEDS = (0, 1, 2)

SIMPLIFY_SYSTEM = (
    "You rewrite one sentence for a school student in simple words. Use short, common words. "
    "Keep every number and every name exactly as written. Do not add any new fact. "
    "Reply with one sentence only."
)
STEM_SYSTEM = (
    "You write one short quiz question for a Class 6 student. The answer to your question must be "
    "the given answer word. Never write the answer word inside the question. "
    "Reply with the question only, on one line."
)
WHOLE_SYSTEM = (
    "You summarise a passage for a school student in 2 or 3 simple sentences. Use short, common words. "
    "Keep every number and name exactly as written. Do not add any fact that is not in the passage."
)
# Worked examples, given as earlier finished chat turns (see backends.base.chat_prompt): two different topics, so
# the model learns the pattern, not one question to copy.
_STEM_EXAMPLES = (
    ("Sentence: Plants make food using sunlight.\nAnswer: sunlight", "What do plants use to make food?"),
    ("Sentence: The Ganga river begins at the Gangotri glacier in the Himalayas.\nAnswer: Gangotri",
     "At which glacier does the Ganga river begin?"),
)
VERIFY_SYSTEM = ("Answer the question using only the given sentence. Reply with the answer only: "
                 "one to four words copied from the sentence.")
_VERIFY_EXAMPLES = (
    ("Sentence: Plants make food using sunlight.\nQuestion: What do plants use to make food?", "sunlight"),
    ("Sentence: The Ganga river begins at the Gangotri glacier in the Himalayas.\n"
     "Question: In which mountains does the Ganga river begin?", "the Himalayas"),
)
VERIFY_MAX_WORDS = 6  # a longer reply is the model copying the sentence, which would "contain" any key
_SPECIAL = re.compile(r"<\|[^|>]*\|>")
_LABEL = re.compile(r"^(question|rewrite|rewritten|sentence|answer|summary)\s*:\s*", re.I)


def clean_line(text: str) -> str:
    """First non-empty line, special tokens and labels stripped."""
    text = _SPECIAL.sub("", text or "")
    for line in text.splitlines():
        line = _LABEL.sub("", line.strip()).strip().strip('"“”')
        if line:
            return line
    return ""


def _chat(backend: Backend, system: str, user: str) -> str:
    return chat_for(backend, system, user)


@dataclass
class Attempt:
    text: str
    temperature: float
    checks: list[CheckResult]
    wall_s: float = 0.0
    prompt_tokens: int = 0
    new_tokens: int = 0
    ttft_ms: float | None = None
    tokens_per_s: float | None = None
    verify: dict | None = None  # the extra model call that answered this question back (stems only)


def _score(a: Attempt) -> tuple[int, int]:
    return (len(failures(a.checks, HARD)), len(failures(a.checks, WARN)))


def _run_attempts(backend: Backend, prompt: str, task: str, payload: dict, max_new: int, checker, retries: int) -> list[Attempt]:
    """Call the backend up to 1+retries times, stopping at the first attempt with no failures."""
    out: list[Attempt] = []
    for i in range(1 + retries):
        temp, seed = TEMPERATURES[min(i, len(TEMPERATURES) - 1)], SEEDS[min(i, len(SEEDS) - 1)]
        res = backend.generate(prompt, max_new_tokens=max_new, temperature=temp, seed=seed, task=task, payload=payload)
        text = clean_line(res.text)
        a = Attempt(text, temp, checker(text), res.wall_s, res.prompt_tokens, res.new_tokens, res.ttft_ms, res.tokens_per_s)
        out.append(a)
        if _score(a) == (0, 0):
            break
    return out


# ---- summary ---------------------------------------------------------------------------
@dataclass
class SummarySentence:
    src_idx: int
    source: str
    text: str
    fallback: bool
    tier: str
    checks: list[CheckResult]
    attempts: list[Attempt] = field(default_factory=list)


@dataclass
class SummaryResult:
    sentences: list[SummarySentence]
    text: str
    checks: list[CheckResult]
    word_count: int


def simplify_sentence(backend: Backend, src_idx: int, source: str, retries: int = 2) -> SummarySentence:
    user = f"Sentence: {source}\nRewrite it in simple words for a Class 6 student."
    attempts = _run_attempts(backend, _chat(backend, SIMPLIFY_SYSTEM, user), "simplify", {"sentence": source}, 80,
                             lambda t: summary_sentence_checks(source, t), retries)
    usable = [a for a in attempts if not failures(a.checks, HARD)]
    if usable:
        best = min(usable, key=_score)
        return SummarySentence(src_idx, source, best.text, False, tier(best.checks), best.checks, attempts)
    # No witness, no summary sentence: fall back to the source sentence itself.
    return SummarySentence(src_idx, source, source, True, "GREEN", [], attempts)


def make_summary(backend: Backend, analysis: Analysis, retries: int = 2, lo: int = 30, hi: int = 80) -> SummaryResult:
    """Witnessed summary: 2-3 central sentences, each simplified on its own and checked against its source."""
    chosen: list[SummarySentence] = []
    for idx in analysis.central_ranked:
        chosen.append(simplify_sentence(backend, idx, analysis.sentences[idx], retries))
        words = sum(len(tokens(s.text)) for s in chosen)
        if len(chosen) >= 3 or (len(chosen) >= 2 and words >= lo):
            break
    while len(chosen) > 1 and sum(len(tokens(s.text)) for s in chosen) > hi:
        chosen.pop()  # drop the least central sentence added last
    chosen.sort(key=lambda s: s.src_idx)
    text = " ".join(s.text for s in chosen)
    return SummaryResult(chosen, text, summary_overall_checks(text), len(tokens(text)))


def make_whole_summary(backend: Backend, passage: str, retries: int = 2, extra: dict | None = None) -> dict:
    """The v1.2 comparison arm: one model call over the whole passage. Used only for ticket 7b."""
    user = f"Passage: {passage}\nWrite the summary."
    attempts = _run_attempts(backend, _chat(backend, WHOLE_SYSTEM, user), "whole_summary", {"passage": passage, **(extra or {})}, 140,
                             lambda t: summary_sentence_checks(passage, t) + summary_overall_checks(t), retries)
    best = min(attempts, key=_score)
    return {"text": best.text, "checks": best.checks, "attempts": attempts}


# ---- stems -----------------------------------------------------------------------------
@dataclass
class StemResult:
    text: str | None  # None means every attempt failed a HARD check (RED)
    tier: str
    checks: list[CheckResult]
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def reasons(self) -> list[str]:
        return reasons(self.checks)


def answers_match(reply: str, key: str) -> bool:
    """Does a short reply name the key? Every word stem of the key must appear in the reply."""
    got = {stem(t) for t in tokens(reply)}
    want = [stem(t) for t in tokens(key)]
    return bool(want) and all(w in got for w in want)


def verify_stem(backend: Backend, question: str, witness: str, answer: str) -> tuple[CheckResult, dict]:
    """Ask the model to answer its own question from the witness sentence alone.

    Catches the commonest small-model failure: a fluent question about the sentence that does not ask for the
    code-picked answer (Qwen3-0.6B: "What is exposed underneath each flake?" with the key "layer"; the passage says
    "fresh iron"). The reply is only compared with the key; it never becomes the key.
    """
    user = f"Sentence: {witness}\nQuestion: {question}"
    res = backend.generate(chat_for(backend, VERIFY_SYSTEM, user, examples=_VERIFY_EXAMPLES), max_new_tokens=16,
                           temperature=0.0, task="answer", payload={"sentence": witness, "question": question, "answer": answer})
    reply = clean_line(res.text)
    n = len(tokens(reply))
    ok = 0 < n <= VERIFY_MAX_WORDS and answers_match(reply, answer)
    detail = "" if ok else f"asked to answer its own question, the model said {reply!r}, not {answer!r}"
    stats = {"text": reply, "wall_s": round(res.wall_s, 4), "prompt_tokens": res.prompt_tokens, "new_tokens": res.new_tokens,
             "ttft_ms": res.ttft_ms, "tokens_per_s": res.tokens_per_s}
    return CheckResult("stem_answers_to_key", HARD, ok, detail), stats


def make_stem(backend: Backend, witness: str, answer: str, passage: str, other_stems: list[str] | None = None,
              retries: int = 2, verify: bool = True) -> StemResult:
    """Ask for one question about the code-picked answer. The answer is never read from the output.

    With `verify`, a draft that passes the text checks is also answered back by the model (verify_stem), and is
    only accepted if that answer is the key. Each verification is one more short model call.
    """
    user = f"Sentence: {witness}\nAnswer: {answer}"
    prompt = chat_for(backend, STEM_SYSTEM, user, examples=_STEM_EXAMPLES)
    verifications: list[dict | None] = []

    def check(text: str) -> list[CheckResult]:
        results = stem_checks(text, answer, witness, passage, other_stems)
        if verify and not failures(results, HARD):
            result, stats = verify_stem(backend, text, witness, answer)
            results.append(result)
            verifications.append(stats)
        else:
            verifications.append(None)
        return results

    attempts = _run_attempts(backend, prompt, "stem", {"sentence": witness, "answer": answer}, 48, check, retries)
    for a, v in zip(attempts, verifications):
        a.verify = v
    usable = [a for a in attempts if a.text and not failures(a.checks, HARD)]
    if usable:
        best = min(usable, key=_score)
        return StemResult(best.text, tier(best.checks), best.checks, attempts)
    worst_reasons = min(attempts, key=_score)
    return StemResult(None, "RED", worst_reasons.checks, attempts)


def build_cloze(sentence: str, term: str) -> str:
    """Code-only fill-in-the-blank. Its key is the blanked word, so it cannot be wrong against the passage."""
    return "Fill in the blank: " + blank_term(sentence, term)
