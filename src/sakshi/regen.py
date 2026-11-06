"""Layer 9: one-question regeneration (build map T29). A judge edits one fact; only what depends on it changes.

Steps (bible Layer 9):
  1. Diff old and new passage by sentence. Unchanged sentences keep their items byte for byte.
  2. An item whose witness sentence changed gets its KEY updated by code first (same kind: a changed year gives a
     new year), options rebuilt, stem checks re-run. The model is called ONLY if a check fails or the answer kind changed.
  3. A summary sentence whose source changed is checked against the new source: the number check marks the old text
     STALE (this is a second visible catch, by a rule, not a person) and the sentence is regenerated.
  4. A deleted witness sends its item RED with the reason "witness removed".
The model is never trusted with a key: whatever it writes, the key is the code-picked term.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field, replace
from difflib import SequenceMatcher

from .backends.base import Backend
from .checks import HARD, failures, item_assertions, reasons, stem_checks, summary_sentence_checks, summary_overall_checks, tier
from .distract import make_options
from .gate import check_passage
from .generate import build_cloze, make_stem, simplify_sentence
from .metrics import capture_env
from .pipeline import Candidate, Item, Run, _attempt_dicts, _reserve, _seed
from .select import analyse
from .text import find_span, is_number, split_sentences, tokens


def item_sentences(run: Run) -> dict[int, list[int]]:
    """{0-based sentence index: [item ids]} for items a student sees. The judge picks one of these to edit."""
    out: dict[int, list[int]] = {}
    for it in run.items:
        if it.tier == "GREEN":
            out.setdefault(it.witness_idx, []).append(it.id)
    return out


def replace_sentence(passage: str, idx: int, new_text: str) -> str:
    """Passage with one sentence replaced. Paragraph breaks are not preserved (sentences are re-joined with spaces)."""
    sents = split_sentences(passage)
    if not 0 <= idx < len(sents):
        raise IndexError(f"sentence {idx + 1} does not exist (passage has {len(sents)})")
    sents[idx] = new_text.strip()
    return " ".join(sents)


@dataclass
class EditReport:
    changed: list[dict] = field(default_factory=list)
    items_updated: list[dict] = field(default_factory=list)
    items_untouched: list[int] = field(default_factory=list)
    items_red: list[dict] = field(default_factory=list)
    summary_stale: list[dict] = field(default_factory=list)
    summary_dropped: list[int] = field(default_factory=list)
    model_calls: int = 0
    seconds: float = 0.0
    notes: list[str] = field(default_factory=list)


def _kind(key: str) -> str:
    return "number" if key[:1].isdigit() else ("name" if key[:1].isupper() else "word")


def _align(old: list[str], new: list[str]):
    """old index -> (new index, changed?); plus the set of deleted old indices and the changed pairs."""
    mapping: dict[int, tuple[int, bool]] = {}
    deleted: set[int] = set()
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                mapping[i1 + k] = (j1 + k, False)
        elif tag in ("replace", "delete"):
            pairs = min(i2 - i1, j2 - j1) if tag == "replace" else 0
            for k in range(pairs):
                mapping[i1 + k] = (j1 + k, True)
            deleted.update(range(i1 + pairs, i2))
    return mapping, deleted


def _edited_candidate(a, j: int, key: str) -> Candidate:
    base = a.per_sentence.get(j)
    alt = base.term if base and base.term.lower() != key.lower() else (base.reserve if base else None)
    return Candidate(key, j, 0.0, ("edited",), _kind(key), True, False, reserve=alt)


def _update_item(it: Item, j: int, new_s: list[str], new_passage: str, a, backend: Backend, others: list[str],
                 rep: EditReport) -> Item:
    witness = new_s[j]
    others = [o for o in others if o != it.stem]  # an item must not be compared with its own old question
    key, kind = it.key, _kind(it.key)
    key_changed = False
    if not find_span(witness, key):
        key_changed = True
        pick = None
        if kind == "number":
            nums = [t for t in tokens(witness) if is_number(t) and t != key]
            pick = (nums[0], "number") if nums else None
        if pick is None and a.per_sentence.get(j):
            pick = (a.per_sentence[j].term, a.per_sentence[j].kind)
        if pick is None:
            return replace(it, witness=witness, witness_idx=j, tier="RED", stem="(withheld: no usable answer in the edited sentence)",
                           reasons=["no usable answer in the edited sentence"], checks=[])
        key, kind_new = pick
    else:
        kind_new = kind
    opts = make_options(new_passage, key, j, kind_new, _seed(key, j, new_passage))
    stem, attempts = it.stem, it.attempts
    if it.kind == "cloze":
        stem = build_cloze(witness, key)
        stem_res = []
    else:
        # Keep the existing question only when it still fits: same answer kind and every check still passes.
        reuse = (not key_changed) or (kind == "number" and kind_new == "number")
        stem_res = stem_checks(stem, key, witness, new_passage, others) if reuse else None
        if stem_res is None or failures(stem_res, HARD):
            sr = make_stem(backend, witness, key, new_passage, others)
            rep.model_calls += len(sr.attempts)
            stem, stem_res, attempts = (sr.text or "(withheld: no valid question was written)"), sr.checks, _attempt_dicts(sr.attempts)
            if sr.text is None:
                stem_res = sr.checks
    assertions = item_assertions(key, witness, opts)
    checks = list(stem_res) + assertions
    dead = it.kind != "cloze" and stem.startswith("(withheld")
    t = "RED" if (dead or failures(assertions, HARD)) else tier(checks, detail=it.detail)
    return Item(it.id, it.kind if it.kind == "cloze" else ("mcq" if opts else "short"), stem, key, opts, j, witness, t,
                fallback=it.fallback, detail=it.detail, signals=list(it.signals), checks=[asdict(c) for c in checks],
                reasons=reasons(checks), attempts=attempts, reserve=_reserve(new_passage, a, _edited_candidate(a, j, key)))


def edit(run: Run, new_passage: str, backend: Backend) -> tuple[Run, EditReport]:
    t0 = time.perf_counter()
    rep = EditReport()
    old_s, new_s = split_sentences(run.passage), split_sentences(new_passage)
    mapping, deleted = _align(old_s, new_s)
    for i, (j, changed) in sorted(mapping.items()):
        if changed:
            rep.changed.append({"old_idx": i, "new_idx": j, "old": old_s[i], "new": new_s[j]})
    if not rep.changed and not deleted and old_s == new_s:
        rep.notes.append("no change detected")
    a = analyse(new_passage)
    others = [i.stem for i in run.items if i.tier != "RED"]

    items: list[Item] = []
    for it in run.items:
        if it.witness_idx in deleted or it.witness_idx not in mapping:
            red = replace(it, tier="RED", stem="(withheld: witness removed)", reasons=["witness removed: the sentence this "
                          "question was about is gone"], checks=[], reserve=None)
            items.append(red)
            rep.items_red.append({"id": it.id, "reason": "witness removed"})
            continue
        j, changed = mapping[it.witness_idx]
        if not changed:
            moved = replace(it, witness_idx=j, reserve=(dict(it.reserve, witness_idx=j) if it.reserve else None))
            items.append(moved)
            rep.items_untouched.append(it.id)
            continue
        upd = _update_item(it, j, new_s, new_passage, a, backend, others, rep)
        items.append(upd)
        (rep.items_red if upd.tier == "RED" else rep.items_updated).append(
            {"id": it.id, "old_key": it.key, "new_key": upd.key, "old_stem": it.stem, "new_stem": upd.stem, "tier": upd.tier,
             "model_called_for_stem": upd.attempts is not it.attempts})

    summary = dict(run.summary)
    sents = []
    for s in run.summary.get("sentences", []):
        i = s["src_idx"]
        if i in deleted or i not in mapping:
            rep.summary_dropped.append(i)
            continue
        j, changed = mapping[i]
        if not changed:
            sents.append(dict(s, src_idx=j))
            continue
        # The number check, not a person, notices the old summary sentence no longer matches its source.
        stale = summary_sentence_checks(new_s[j], s["text"])
        why = reasons([c for c in stale if c.severity == HARD])
        if why:
            rep.summary_stale.append({"src_idx": j, "old_text": s["text"], "reasons": why})
        res = simplify_sentence(backend, j, new_s[j])
        rep.model_calls += len(res.attempts)
        sents.append({"src_idx": j, "source": new_s[j], "text": res.text, "fallback": res.fallback, "tier": res.tier,
                      "reasons": reasons(res.checks), "attempts": _attempt_dicts(res.attempts),
                      "stale_reasons": why})
    text = " ".join(x["text"] for x in sents)
    summary.update({"sentences": sents, "text": text, "word_count": len(tokens(text)),
                    "checks": [asdict(c) for c in summary_overall_checks(text)]})

    gate = check_passage(new_passage)
    if not gate.ok:
        rep.notes.append(gate.reason)
    counts = {"green": sum(i.tier == "GREEN" for i in items), "amber": sum(i.tier == "AMBER" for i in items),
              "red": sum(i.tier == "RED" for i in items), "fallback": sum(i.fallback for i in items) + sum(s["fallback"] for s in sents)}
    rep.seconds = round(time.perf_counter() - t0, 4)
    new_run = replace(run, passage=new_passage, gate=asdict(gate), summary=summary, items=items, counts=counts,
                      timings={"edit_s": rep.seconds, "model_calls": rep.model_calls, "total_s": rep.seconds,
                               "summary_s": 0.0, "stems_s": 0.0, "load_s": run.timings.get("load_s", 0.0)}, env=capture_env())
    return new_run, rep


def render_report(rep: EditReport) -> str:
    out = []
    for c in rep.changed:
        out.append(f"Sentence {c['new_idx'] + 1} changed:\n  was: {c['old']}\n  now: {c['new']}")
    for u in rep.items_updated:
        out.append(f"Question {u['id']}: answer {u['old_key']!r} -> {u['new_key']!r} ({u['tier']})"
                   + ("; the question was rewritten by the model" if u["model_called_for_stem"] else "; the question text is unchanged"))
    for r in rep.items_red:
        out.append(f"Question {r['id']} withheld: {r.get('reason') or r.get('new_stem')}")
    for s in rep.summary_stale:
        out.append(f"STALE summary sentence (caught by a rule): {s['old_text']!r}\n  because: {'; '.join(s['reasons'])}")
    out.append(f"Questions left exactly as they were: {len(rep.items_untouched)}")
    out.append(f"Model calls: {rep.model_calls}; time: {rep.seconds:.2f} s")
    out += [f"Note: {n}" for n in rep.notes]
    return "\n".join(out)
