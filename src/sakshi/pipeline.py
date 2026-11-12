"""Pipeline: prepare a passage into a Run (summary, items, tiers, timings), save and load it.

Order (bible section 6): gate -> witnessed summary -> selection -> stems -> options -> checks
-> tiers. Code owns every key; the model only writes wording. No item is ever dropped
silently: RED items stay in the run with their reasons.
"""
from __future__ import annotations

import json
import time
import zlib
from dataclasses import asdict, dataclass, field

from .backends.base import Backend
from .checks import HARD, failures, item_assertions, reasons, tier
from .distract import make_options
from .gate import GateResult, check_passage
from .metrics import capture_env
from .generate import Attempt, build_cloze, make_stem, make_summary, SummaryResult
from .select import Analysis, Candidate, analyse
from .text import find_span

VERSION = 1


@dataclass
class Item:
    id: int
    kind: str  # mcq | short | cloze
    stem: str
    key: str
    options: list[str] | None
    witness_idx: int
    witness: str
    tier: str  # GREEN | AMBER | RED
    fallback: bool = False
    detail: bool = False
    signals: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    attempts: list[dict] = field(default_factory=list)
    reserve: dict | None = None  # code-built cloze from the same witness, for the Reread Loop


@dataclass
class Run:
    passage: str
    gate: dict
    summary: dict
    items: list[Item]
    backend: dict
    timings: dict
    counts: dict
    version: int = VERSION
    created: str = ""
    env: dict = field(default_factory=dict)  # peak memory, network, throttling (captured after the run)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "Run":
        d = json.loads(text)
        d["items"] = [Item(**i) for i in d["items"]]
        return cls(**d)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "Run":
        with open(path, encoding="utf-8") as f:
            return cls.from_json(f.read())


def visible_items(run: Run, include_amber: bool = False) -> list[Item]:
    """Items a student may see: GREEN (including labelled cloze fallbacks); AMBER only on request; never RED."""
    ok = {"GREEN", "AMBER"} if include_amber else {"GREEN"}
    return [i for i in run.items if i.tier in ok]


def _seed(term: str, idx: int, passage: str) -> int:
    return zlib.crc32(f"{term}|{idx}|{len(passage)}".encode())


def _attempt_dicts(attempts: list[Attempt]) -> list[dict]:
    return [{"text": a.text, "temperature": a.temperature, "wall_s": round(a.wall_s, 4),
             "failed": [c.name for c in failures(a.checks)], "prompt_tokens": a.prompt_tokens, "new_tokens": a.new_tokens,
             "ttft_ms": a.ttft_ms, "tokens_per_s": a.tokens_per_s, "verify": getattr(a, "verify", None)} for a in attempts]


def _reserve(passage: str, a: Analysis, c: Candidate) -> dict | None:
    """Code-built cloze on a DIFFERENT term of the same witness sentence."""
    if not c.reserve:
        return None
    w = a.sentences[c.sent_idx]
    if find_span(w, c.reserve) is None or c.reserve.lower() == c.term.lower():
        return None
    return {"stem": build_cloze(w, c.reserve), "key": c.reserve, "witness_idx": c.sent_idx, "witness": w,
            "options": make_options(passage, c.reserve, c.sent_idx, "word" if not c.reserve[0].isdigit() else "number",
                                    _seed(c.reserve, c.sent_idx, passage))}


def _cloze_item(item_id: int, passage: str, a: Analysis, c: Candidate) -> Item:
    w = a.sentences[c.sent_idx]
    opts = make_options(passage, c.term, c.sent_idx, c.kind, _seed(c.term, c.sent_idx, passage))
    res = item_assertions(c.term, w, opts)
    t = "RED" if failures(res, HARD) else "GREEN"
    return Item(item_id, "cloze", build_cloze(w, c.term), c.term, opts, c.sent_idx, w, t, fallback=True,
                detail=c.detail, signals=list(c.signals), checks=[asdict(r) for r in res], reasons=reasons(res),
                reserve=_reserve(passage, a, c))


def _model_item(item_id: int, passage: str, a: Analysis, c: Candidate, backend: Backend, accepted: list[str]) -> Item:
    w = a.sentences[c.sent_idx]
    opts = make_options(passage, c.term, c.sent_idx, c.kind, _seed(c.term, c.sent_idx, passage))
    sr = make_stem(backend, w, c.term, passage, accepted)
    assertions = item_assertions(c.term, w, opts)
    checks = sr.checks + assertions
    t = "RED" if (sr.text is None or failures(assertions, HARD)) else tier(checks, detail=c.detail)
    return Item(item_id, "mcq" if opts else "short", sr.text or "(withheld: no valid question was written)", c.term, opts,
                c.sent_idx, w, t, detail=c.detail, signals=list(c.signals), checks=[asdict(r) for r in checks],
                reasons=reasons(checks), attempts=_attempt_dicts(sr.attempts), reserve=_reserve(passage, a, c))


def summary_to_dict(s: SummaryResult) -> dict:
    return {
        "text": s.text, "word_count": s.word_count, "checks": [asdict(c) for c in s.checks],
        "sentences": [{"src_idx": x.src_idx, "source": x.source, "text": x.text, "fallback": x.fallback, "tier": x.tier,
                       "reasons": reasons(x.checks), "attempts": _attempt_dicts(x.attempts)} for x in s.sentences],
    }


def prepare(passage: str, backend: Backend, n_items: int = 6, min_visible: int = 3,
            force_sentences: list[int] | None = None, gate_override: bool = False,
            force_terms: dict[int, str] | None = None) -> Run:
    t0 = time.perf_counter()
    gate: GateResult = check_passage(passage, override=gate_override)
    base = dict(passage=passage, gate=asdict(gate), backend=backend.info(), created=time.strftime("%Y-%m-%dT%H:%M:%S"))
    if not gate.ok:
        return Run(summary={}, items=[], timings={"total_s": 0.0}, counts={"green": 0, "amber": 0, "red": 0, "fallback": 0}, **base)

    a = analyse(passage, n_candidates=n_items + 4)
    forced: list[Candidate] = []
    for i in (force_sentences or []):
        if not (0 <= i < len(a.sentences)):
            continue
        term = (force_terms or {}).get(i)
        cand0 = a.per_sentence.get(i)
        if term and find_span(a.sentences[i], term):
            kind = "number" if term[0].isdigit() else ("name" if term[0].isupper() else "word")
            alt = cand0.term if cand0 and cand0.term.lower() != term.lower() else (cand0.reserve if cand0 else None)
            forced.append(Candidate(term, i, 99.0, ("forced",), kind, True, False, reserve=alt))
        elif cand0:
            forced.append(cand0)
    forced_idx = {c.sent_idx for c in forced}
    ordered = forced + [c for c in a.candidates if c.sent_idx not in forced_idx]
    first, spares = ordered[:max(n_items, len(forced))], ordered[max(n_items, len(forced)):]

    ts = time.perf_counter()
    summary = make_summary(backend, a)
    summary_s = time.perf_counter() - ts

    ts = time.perf_counter()
    items: list[Item] = []
    accepted: list[str] = []
    for c in first:
        it = _model_item(len(items) + 1, passage, a, c, backend, accepted)
        if it.tier != "RED":
            accepted.append(it.stem)
        items.append(it)
    stems_s = time.perf_counter() - ts

    # Fewer than min_visible GREEN items: fill with code-built cloze items, labelled FALLBACK.
    visible_keys = {i.key.lower() for i in items if i.tier == "GREEN"}
    n_green = len(visible_keys)
    if n_green < min_visible:
        pool = spares + [c for c in first if c.term.lower() not in visible_keys]
        for c in pool:
            if n_green >= min_visible:
                break
            if c.term.lower() in visible_keys:
                continue
            it = _cloze_item(len(items) + 1, passage, a, c)
            items.append(it)
            if it.tier == "GREEN":
                visible_keys.add(c.term.lower())
                n_green += 1

    model_wall = sum(at["wall_s"] for it in items for at in it.attempts) + sum(
        at["wall_s"] for s in summary.sentences for at in _attempt_dicts(s.attempts))
    n_calls = sum(len(it.attempts) for it in items) + sum(len(s.attempts) for s in summary.sentences)
    counts = {"green": sum(i.tier == "GREEN" for i in items), "amber": sum(i.tier == "AMBER" for i in items),
              "red": sum(i.tier == "RED" for i in items), "fallback": sum(i.fallback for i in items)
              + sum(s.fallback for s in summary.sentences)}
    timings = {"total_s": round(time.perf_counter() - t0, 4), "summary_s": round(summary_s, 4), "stems_s": round(stems_s, 4),
               "model_wall_s": round(model_wall, 4), "model_calls": n_calls,
               "load_s": backend.info().get("load_s", 0.0)}
    return Run(summary=summary_to_dict(summary), items=items, timings=timings, counts=counts, env=capture_env(), **base)
