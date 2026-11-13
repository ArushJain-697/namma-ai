"""Diagnostic multiple-choice questions: one shared format for TRAINING data and for the DEVICE.

The model's job, per question (one short call):
  input  = the passage, one evidence sentence chosen by code, and a menu of 3-5 student beliefs (B1..B5) chosen by
           code from the misconception library;
  output = JSON, in this field order:  {"answer", "stem", "options": [{"b", "why", "text"} x3]}
           answer first (commit to what is tested), then the question, then for each wrong option the belief label,
           a short reason, and the wrong answer that belief produces.
Code does everything else: picks the evidence and beliefs, checks the output, maps B-labels to library ids,
shuffles A-D, writes the explanation from the evidence sentence and the feedback from the library's `fix` text,
and assembles the question bank the retention engine reads. The model never picks the answer letter, never
writes feedback and never judges its own work.

`build_messages` is used by scripts/make_dataset.py (training) and by `generate_bank` (device), so the two
prompts are byte-identical. Change it only together with retraining.
"""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field

from .text import content_stems, split_sentences, stem, tokens

SYSTEM = ("You write one diagnostic multiple-choice question for a school student. Use only facts from the "
          "passage. The answer must come from the evidence sentence. Each wrong option must be the answer a "
          "student holding the given belief would choose. Reply with JSON only.")
FORMAT_HINT = ('{"answer": "...", "stem": "...?", "options": [{"b": "B1", "why": "...", "text": "..."}, '
               '{"b": "B2", "why": "...", "text": "..."}, {"b": "B3", "why": "...", "text": "..."}]}')
LABELS = ("B1", "B2", "B3", "B4", "B5")


def build_user(passage: str, evidence: str, beliefs: list[str]) -> str:
    menu = "\n".join(f"{LABELS[i]}: {b}" for i, b in enumerate(beliefs))
    return (f"Passage:\n{passage.strip()}\n\nEvidence sentence:\n{evidence.strip()}\n\n"
            f"Student beliefs (use three different ones):\n{menu}\n\nReply in this JSON format:\n{FORMAT_HINT}")


def build_messages(passage: str, evidence: str, beliefs: list[str]) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": build_user(passage, evidence, beliefs)}]


def target_json(answer: str, stem_: str, options: list[dict]) -> str:
    """The exact assistant text the model is trained to produce (compact JSON, fixed key order)."""
    return json.dumps({"answer": answer, "stem": stem_,
                       "options": [{"b": o["b"], "why": o["why"], "text": o["text"]} for o in options]},
                      ensure_ascii=False, separators=(", ", ": "))


# ---- parsing and checks ---------------------------------------------------------------------------------
_JSON = re.compile(r"\{.*\}", re.S)


def parse_item(text: str) -> dict | None:
    """Tolerant: take the first {...} block, drop trailing commas, require the three keys."""
    m = _JSON.search(text or "")
    if not m:
        return None
    raw = re.sub(r",\s*([}\]])", r"\1", m.group(0))
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(d, dict) or not all(k in d for k in ("answer", "stem", "options")):
        return None
    opts = [o for o in d.get("options") or [] if isinstance(o, dict) and str(o.get("text", "")).strip()]
    return {"answer": str(d["answer"]).strip(), "stem": str(d["stem"]).strip(),
            "options": [{"b": str(o.get("b", "")).strip().upper(), "why": str(o.get("why", "")).strip(),
                         "text": str(o.get("text", "")).strip()} for o in opts]}


def _stems(s: str) -> set[str]:
    return set(content_stems(s))


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


@dataclass
class ItemCheck:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def check_item(item: dict, passage: str, evidence: str, n_beliefs: int) -> ItemCheck:
    """Rules that every accepted question must pass (used to filter training data and on the device)."""
    r = []
    ans, st, opts = item["answer"], item["stem"], item["options"]
    a_stems, ev_stems = _stems(ans), _stems(evidence)
    if not ans or len(tokens(ans)) > 12:
        r.append("answer empty or longer than 12 words")
    elif not a_stems or len(a_stems & ev_stems) / len(a_stems) < 0.6:
        r.append("answer is not taken from the evidence sentence")
    if not st.endswith("?") or not 4 <= len(tokens(st)) <= 30:
        r.append("stem is not a question of 4-30 words")
    if a_stems and a_stems <= _stems(st):
        r.append("answer appears in the question")
    if len(opts) != 3:
        r.append(f"needs exactly 3 wrong options, got {len(opts)}")
    labels = [o["b"] for o in opts]
    valid = set(LABELS[:n_beliefs])
    if any(b not in valid for b in labels) or len(set(labels)) != len(labels):
        r.append("options must use three different given belief labels")
    texts = [_norm(o["text"]) for o in opts] + [_norm(ans)]
    if len(set(texts)) != len(texts):
        r.append("duplicate options, or a wrong option equal to the answer")
    for o in opts:
        o_st = _stems(o["text"])
        if a_stems and o_st and (o_st == a_stems):
            r.append(f"wrong option says the same as the answer: {o['text']!r}")
        if not o["text"] or len(tokens(o["text"])) > 16:
            r.append("wrong option empty or longer than 16 words")
        if re.search(r"\b(all|none) of the above\b", o["text"], re.I):
            r.append("all/none of the above")
    lens = [len(tokens(o["text"])) for o in opts] + [len(tokens(ans))]
    if max(lens) >= 3 * max(1, min(lens)) and max(lens) - min(lens) >= 6:
        r.append("option lengths too uneven (a length cue)")
    return ItemCheck(not r, r)


# ---- choosing evidence and beliefs (device side) ---------------------------------------------------------
def choose_evidence(passage: str, misconceptions: list[dict], k: int = 4) -> list[str]:
    """Content-rich sentences that touch the matched misconceptions' cue words, spread across the passage."""
    sents = [s for s in split_sentences(passage) if 8 <= len(tokens(s)) <= 45]
    cues = set()
    for m in misconceptions:
        for c in m.get("trigger_cues") or []:
            cues |= _stems(c)
        cues |= _stems(m.get("concept", ""))
    scored = sorted(((len(_stems(s) & cues) * 2 + len(_stems(s)) / 10, i, s) for i, s in enumerate(sents)), reverse=True)
    picked, used = [], set()
    for _, i, s in scored:
        if i in used or (i - 1) in used or (i + 1) in used:
            continue
        picked.append((i, s))
        used.add(i)
        if len(picked) == k:
            break
    return [s for _, s in sorted(picked)]


def choose_beliefs(evidence: str, passage: str, misconceptions: list[dict], n: int = 5) -> list[dict]:
    ev, ps = _stems(evidence), _stems(passage)

    def score(m):
        d = _stems(" ".join(m.get("trigger_cues") or []) + " " + m.get("concept", "") + " " + m["statement"])
        return 3 * len(d & ev) + len(d & ps)
    return sorted(misconceptions, key=score, reverse=True)[:n]


# ---- assembling the question bank ------------------------------------------------------------------------
def assemble_question(qid: str, item: dict, menu: list[dict], evidence: str, rng: random.Random) -> dict:
    """Model output + the belief menu -> one bank question (retention-engine format)."""
    by_label = {LABELS[i]: m for i, m in enumerate(menu)}
    options = [{"text": item["answer"], "correct": True, "misconception": None}]
    for o in item["options"]:
        m = by_label[o["b"]]
        options.append({"text": o["text"], "correct": False, "misconception": m["id"], "why": o["why"],
                        "feedback": m.get("fix", "")})
    rng.shuffle(options)
    for letter, o in zip("ABCD", options):
        o["key"] = letter
    concept = by_label[item["options"][0]["b"]]["concept_id"]
    return {"id": qid, "concept": concept, "type": "recall", "stem": item["stem"], "options": options,
            "evidence": evidence, "explanation": f"The passage says: \"{evidence}\"", "source": "diagnostic"}


TEMPERATURES = (0.0, 0.5)
# Below BOTH thresholds a passage counts as off-syllabus and gets the generic reading-skill menu.
# Provisional values; calibrate with scripts/calibrate_fallback.py on on-/off-syllabus passages.
GENERIC_COS = 0.69   # best meaning similarity between the passage and any topic (calibrated on the full graph: 12/12 off, 0/40 on)
GENERIC_KW = 110.0   # best keyword (BM25) topic score (on-syllabus minimum 112.7: tight, recalibrate if the library changes)
_CAUSE = re.compile(r"\b(because|so|therefore|causes?|caused|leads? to|due to|as a result|results? in)\b", re.I)
_ABSOLUTE = re.compile(r"\b(all|always|never|every|only|none|most|some|many|usually)\b", re.I)


def generic_menu(evidence: str, library, n: int = 5) -> list[dict]:
    """The generic reading-skill beliefs (GEN-READ-M1..M7), ordered to suit this evidence sentence."""
    g = {m["id"]: m for m in getattr(library, "generic", [])}
    if not g:
        return []
    order = []
    if re.search(r"\d", evidence):
        order.append("GEN-READ-M6")
    if _CAUSE.search(evidence):
        order.append("GEN-READ-M2")
    if sum(1 for w in tokens(evidence)[1:] if w[:1].isupper()) >= 2:
        order.append("GEN-READ-M1")
    if _ABSOLUTE.search(evidence):
        order.append("GEN-READ-M3")
    order += ["GEN-READ-M7", "GEN-READ-M5", "GEN-READ-M4", "GEN-READ-M1", "GEN-READ-M3", "GEN-READ-M2", "GEN-READ-M6"]
    return [g[i] for i in dict.fromkeys(order) if i in g][:n]


def cloze_fallback(passage: str, n: int, used_evidence: set[str], seed: int) -> list[dict]:
    """Hidden last resort: code-built 4-option fill-in-the-blank questions (never shown when real MCQs exist)."""
    from .distract import make_options
    from .generate import build_cloze
    from .select import analyse
    a = analyse(passage, n_candidates=n + 6)
    out = []
    for c in a.candidates:
        w = a.sentences[c.sent_idx]
        if w in used_evidence:
            continue
        opts = make_options(passage, c.term, c.sent_idx, c.kind, seed + c.sent_idx)
        if not opts or len(opts) != 4:
            continue
        out.append({"id": "", "concept": "GEN-READ-K7", "type": "recall", "stem": build_cloze(w, c.term),
                    "options": [{"key": "ABCD"[i], "text": o, "correct": o == c.term, "misconception": None}
                                for i, o in enumerate(opts)],
                    "evidence": w, "explanation": f"The passage says: \"{w}\"", "source": "cloze_fallback"})
        used_evidence.add(w)
        if len(out) == n:
            break
    return out


def reconcile_options(item: dict, menu: list[dict], mapper) -> list[str]:
    """Round-trip check: does each wrong option really express the belief it is labelled with?
    Relabels an option to the belief that best explains it when that belief is free; returns problems left."""
    predicted = mapper.option_consistency(item["options"], menu)
    problems = []
    used = {o["b"] for o in item["options"]}
    for o, p in zip(item["options"], predicted):
        if p is None or p == o["b"]:
            continue
        if p not in used:
            used.discard(o["b"])
            o["relabelled_from"], o["b"] = o["b"], p
            used.add(p)
        else:
            problems.append(f"option {o['text']!r} matches belief {p}, not {o['b']}")
    return problems


def generate_bank(passage: str, backend, library, n_questions: int = 4, title: str = "", seed: int = 0,
                  mapper=None) -> tuple[dict, dict]:
    """Device pipeline: summary -> misconception mapping -> evidence -> one model call per question -> checks -> bank.

    With a `mapper` (sakshi.mapper.Mapper) the evidence sentences and belief menus come from the multi-stage
    mapper and every wrong option gets the round-trip check; without it, keyword matching is used.
    Returns (bank, report). The report keeps every attempt, its raw text and its rejection reasons, for evaluation.
    """
    import time
    from .backends.base import chat_for
    from .generate import make_summary
    from .select import analyse

    t0 = time.perf_counter()
    rng = random.Random(seed)
    summary = make_summary(backend, analyse(passage)).text
    t_summary = time.perf_counter() - t0
    if mapper is not None:
        plan, topic_scores = mapper.plan(passage, k=n_questions, n=5)
        strength = getattr(mapper, "last_strength", {"cos": 1.0, "kw": 1e9})
        slots = [(ev, [s.misconception for s in scored]) for ev, scored in plan]
        topics = sorted(topic_scores.items(), key=lambda kv: -kv[1])
    else:
        match = library.match(passage, n_misconceptions=14)
        mis = match.misconceptions
        strength = {"cos": None, "kw": match.topics[0].score if match.topics else 0.0}
        slots = [(ev, choose_beliefs(ev, passage, mis, 5)) for ev in choose_evidence(passage, mis, k=n_questions)]
        topics = [(t.topic_id, t.score) for t in match.topics]
    off_syllabus = strength["kw"] < GENERIC_KW and (strength["cos"] is None or strength["cos"] < GENERIC_COS)
    if off_syllabus or not slots:
        slots = [(ev, generic_menu(ev, library)) for ev in choose_evidence(passage, [], k=n_questions)]
    report = {"topics": topics, "items": [], "summary_s": round(t_summary, 2), "mapper": mapper is not None,
              "mode": "generic" if off_syllabus else "topic", "match_strength": strength}
    questions = []
    for ev, menu in slots:
        rec = {"evidence": ev, "beliefs": [m["id"] for m in menu], "attempts": []}
        menus = [menu] if len(menu) >= 3 else []
        gm = generic_menu(ev, library)
        if not off_syllabus and len(gm) >= 3:
            menus.append(gm)  # a topic question that keeps failing gets one try with the generic menu
        if not menus:
            rec["skipped"] = "fewer than 3 beliefs to build options from"
            report["items"].append(rec)
            continue
        tries = [(m, t) for m in menus[:1] for t in TEMPERATURES] + [(m, 0.0) for m in menus[1:]]
        for menu, temp in tries:
            rec["beliefs"] = [m["id"] for m in menu]
            msgs = build_messages(passage, ev, [m["statement"] for m in menu])
            prompt = chat_for(backend, msgs[0]["content"], msgs[1]["content"])
            res = backend.generate(prompt, max_new_tokens=260, temperature=temp, task="diagnostic",
                                   payload={"evidence": ev, "beliefs": menu, "passage": passage})
            item = parse_item(res.text)
            chk = check_item(item, passage, ev, len(menu)) if item else ItemCheck(False, ["output is not valid JSON"])
            if chk.ok and mapper is not None:
                probs = reconcile_options(item, menu, mapper)
                if probs:
                    chk = ItemCheck(False, ["round-trip: " + p for p in probs])
            rec["attempts"].append({"text": res.text, "temperature": temp, "ok": chk.ok, "reasons": chk.reasons,
                                    "new_tokens": res.new_tokens, "prompt_tokens": res.prompt_tokens, "wall_s": round(res.wall_s, 2),
                                    "tokens_per_s": res.tokens_per_s, "ttft_ms": res.ttft_ms})
            if chk.ok:
                q = assemble_question(f"Q{len(questions) + 1}", item, menu, ev, rng)
                questions.append(q)
                rec["question"] = q
                break
        report["items"].append(rec)
    if len(questions) < 3:  # hidden last resort, flagged in the bank and the report
        used = {q["evidence"] for q in questions}
        for q in cloze_fallback(passage, 3 - len(questions), used, seed):
            q["id"] = f"Q{len(questions) + 1}"
            questions.append(q)
        report["cloze_fallback"] = sum(q.get("source") == "cloze_fallback" for q in questions)
    report["total_s"] = round(time.perf_counter() - t0, 2)
    bank = bank_from_questions(title, passage, summary, questions, library) if questions else \
        {"title": title, "passage": passage, "summary": summary, "concepts": [], "questions": []}
    return bank, report


def bank_from_questions(title: str, passage: str, summary: str, questions: list[dict], library) -> dict:
    """Build the bank JSON the retention engine reads (data/banks/*.json format) from accepted questions."""
    used = {o["misconception"] for q in questions for o in q["options"] if o.get("misconception")}
    concept_ids = list(dict.fromkeys(q["concept"] for q in questions))
    for mid in used:
        cid = library.by_id[mid]["concept_id"]
        if cid not in concept_ids:
            concept_ids.append(cid)
    concepts = []
    for cid in concept_ids:
        c = library.concepts.get(cid, {"name": cid, "prereqs": []})
        mis = [{"id": m, "text": library.by_id[m]["statement"], "fix": library.by_id[m].get("fix", "")}
               for m in used if library.by_id[m]["concept_id"] == cid]
        concepts.append({"id": cid, "name": c.get("name", cid),
                         "prereqs": [p for p in c.get("prereqs", []) if p in concept_ids], "misconceptions": mis})
    for q in questions:  # a question's concept must be in the bank
        if q["concept"] not in concept_ids:
            q["concept"] = concept_ids[0]
    return {"title": title, "source": "diagnostic generation", "passage": passage, "summary": summary,
            "concepts": concepts, "questions": questions}
