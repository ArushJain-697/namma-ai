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
                  mapper=None, cloze: bool = False) -> tuple[dict, dict]:
    """Device pipeline: summary -> misconception mapping -> evidence -> one model call per question -> checks -> bank.

    With a `mapper` (sakshi.mapper.Mapper) the evidence sentences and belief menus come from the multi-stage
    mapper and every wrong option gets the round-trip check; without it, keyword matching is used.
    Returns (bank, report). The report keeps every attempt, its raw text and its rejection reasons, for evaluation.
    `cloze=True` brings back the old fill-in-the-blank top-up; it is off because judges must not see one.
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
    if cloze and len(questions) < 3:  # old last resort, OFF by default since 13 Nov: no fill-in-the-blank in the demo
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


# =========================================================================================================
# Quiz format v2 (13 Nov): the model writes the WHOLE question. One short call per question.
#
#   input  = the passage, one evidence sentence chosen by code, and (optional) up to 3 common student mistakes
#            for the topic, from the misconception library;
#   output = {"q": "...?", "options": [correct, wrong, wrong, wrong], "answer": 0, "explain": "..."}
#
# The correct option is always written FIRST ("answer": 0), so the model commits to the answer before it writes
# the wrong options; code shuffles A-D before anyone sees it. The old format above (code picks the answer word,
# model writes only wording) produced dull questions and is kept only so older data and tests still work.
# `build_quiz_messages` is shared by training (scripts/make_dataset.py) and the device (`generate_quiz`), so the
# two prompts are byte-identical. Change it only together with retraining.
# Speed: keep this prompt short. On a Pi 5 every extra 100 prompt tokens costs ~8 s per quiz (QUESTION_QUALITY_
# HANDOFF.md); passage ~250 + this ~150 tokens, output ~85 tokens, so max_new_tokens=120.
# =========================================================================================================
QUIZ_SYSTEM = ("You write one multiple-choice question for a Class 6-10 student about the evidence sentence of a "
               "passage. Ask why, how or what happens, never a word to fill in. Write the correct option first, then "
               "three wrong options a real student might believe. Keep all four short and alike. Reply with JSON only.")
QUIZ_FORMAT = '{"q": "...?", "options": ["correct", "wrong", "wrong", "wrong"], "answer": 0, "explain": "..."}'
QUIZ_MAX_BELIEFS = 3
QUIZ_MAX_NEW_TOKENS = 120
Q_MAX_WORDS, OPT_MAX_WORDS, EXPLAIN_MAX_WORDS = 25, 12, 25


def build_quiz_user(passage: str, evidence: str, beliefs: list[str] | None = None) -> str:
    parts = [f"Passage:\n{passage.strip()}", f"Evidence sentence:\n{evidence.strip()}"]
    beliefs = [b.strip() for b in (beliefs or []) if b and b.strip()][:QUIZ_MAX_BELIEFS]
    if beliefs:
        parts.append("Common student mistakes on this topic:\n" + "\n".join(f"- {b}" for b in beliefs))
    parts.append(f"JSON:\n{QUIZ_FORMAT}")
    return "\n\n".join(parts)


def build_quiz_messages(passage: str, evidence: str, beliefs: list[str] | None = None) -> list[dict]:
    return [{"role": "system", "content": QUIZ_SYSTEM},
            {"role": "user", "content": build_quiz_user(passage, evidence, beliefs)}]


def quiz_target_json(q: str, options: list[str], explain: str) -> str:
    """The exact assistant text the model is trained to produce: compact JSON, fixed key order, correct option
    first (answer 0)."""
    return json.dumps({"q": q, "options": list(options), "answer": 0, "explain": explain},
                      ensure_ascii=False, separators=(", ", ": "))


def _first_object(text: str) -> str | None:
    """The first balanced {...} block (string-aware), so trailing chatter or a second object is ignored. If the
    output was cut off before the closing brace, returns what there is (parse then fails cleanly)."""
    start = text.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def parse_quiz_item(text: str) -> dict | None:
    """Tolerant parser for the v2 format. Returns {"q", "options", "answer", "explain"} with the correct option
    moved to index 0 (answer 0), or None. Accepts "answer" as an index, a letter (A-D) or the option's text."""
    block = _first_object(text or "")
    if not block:
        return None
    raw = re.sub(r",\s*([}\]])", r"\1", block)
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(d, dict):
        return None
    q = d.get("q", d.get("question", d.get("stem")))
    opts = d.get("options")
    if not isinstance(q, str) or not isinstance(opts, list):
        return None
    opts = [str(o.get("text", "") if isinstance(o, dict) else o).strip() for o in opts]
    a = d.get("answer", 0)
    idx = None
    if isinstance(a, bool):
        idx = None
    elif isinstance(a, int):
        idx = a
    elif isinstance(a, str):
        s = a.strip()
        if s.isdigit():
            idx = int(s)
        elif len(s) == 1 and s.upper() in "ABCD":
            idx = "ABCD".index(s.upper())
        else:
            idx = next((i for i, o in enumerate(opts) if _norm(o) == _norm(s)), None)
    if idx is None or not 0 <= idx < len(opts):
        return None
    opts = [opts[idx]] + [o for i, o in enumerate(opts) if i != idx]
    return {"q": q.strip(), "options": opts, "answer": 0, "explain": str(d.get("explain", "")).strip()}


_BLANK = re.compile(r"_{2,}|\.{4,}|\bfill in the blank\b|\bblank\b", re.I)
_VAGUE = re.compile(r"\b(according to the (passage|text)|which of the following (statements )?(is|are) "
                    r"(true|correct|false))\b", re.I)
_NEGATED_Q = re.compile(r"\b(NOT|EXCEPT)\b")
_ABOVE = re.compile(r"\b(all|none|both) of (the )?(above|these)\b|\bboth [a-d] and [a-d]\b", re.I)


def _window_stems(passage: str, evidence: str) -> set[str]:
    """Stems of the evidence sentence and its neighbours (an answer often uses the sentence before or after)."""
    sents = split_sentences(passage)
    ev = _norm(evidence)
    idx = next((i for i, s in enumerate(sents) if _norm(s) == ev), None)
    if idx is None:
        return _stems(evidence)
    out: set[str] = set()
    for s in sents[max(0, idx - 1): idx + 2]:
        out |= _stems(s)
    return out


def _sym_tokens(s: str) -> list[str]:
    """Lowercase words/numbers AND single symbols (+, −, ², -, =), so maths options stay distinct."""
    return re.findall(r"[a-z0-9]+|[^\sa-z0-9.,;:!?'\"()]", s.lower())


def check_quiz_item(item: dict, passage: str, evidence: str, support: bool = True) -> ItemCheck:
    """Code checks for one v2 question (rubric hard rules that code can test). Used to filter training data, in
    the grader report, and on the device. A pass does not mean the question is good: the rubric grader decides that.
    `support=False` skips the word-overlap support test (training data: the grader's H3 check of the answer against
    the passage is stricter and handles paraphrase; on the device there is no grader, so it stays on)."""
    r: list[str] = []
    q, opts, expl = item.get("q", ""), item.get("options") or [], item.get("explain", "")
    nq = len(tokens(q))
    if not q.endswith("?") or not 4 <= nq <= Q_MAX_WORDS:
        r.append(f"question must end with '?' and have 4-{Q_MAX_WORDS} words (has {nq})")
    if _BLANK.search(q):
        r.append("fill-in-the-blank question")
    if _VAGUE.search(q):
        r.append("vague 'according to the passage / which is true' question")
    if _NEGATED_Q.search(q):
        r.append("NOT/EXCEPT question")
    if len(opts) != 4:
        r.append(f"needs exactly 4 options, got {len(opts)}")
        return ItemCheck(False, r)
    lens = [len(tokens(o)) for o in opts]
    if any(n == 0 or n > OPT_MAX_WORDS for n in lens):
        r.append(f"every option needs 1-{OPT_MAX_WORDS} words")
    if any(_ABOVE.search(o) for o in opts):
        r.append("all/none/both of the above")
    normed = [" ".join(_sym_tokens(o)) for o in opts]   # symbols count: "n + 5" != "n − 5"
    if len(set(normed)) != 4:
        r.append("two options are the same")
    ans_st = _stems(opts[0])

    def seq(o: str) -> list[str]:  # word order, numbers and symbols matter: "A then B" != "B then A", "5n" != "n + 5"
        return [stem(t) for t in _sym_tokens(o) if t not in ("a", "an", "the")]
    for o in opts[1:]:
        if seq(o) == seq(opts[0]):
            r.append(f"a wrong option says the same as the answer: {o!r}")
    # length cue: the correct option clearly the longest, or options very uneven
    if lens[0] - max(lens[1:]) >= 4:
        r.append("the correct option is much longer than the others (a length cue)")
    if max(lens) - min(lens) > 7:
        r.append("option lengths too uneven")
    # answer must come from the passage, near the evidence sentence
    p_st = _stems(passage)
    if ans_st and support:
        # Loose on purpose: good answers paraphrase, and whether the answer is RIGHT is the grader's job (H3).
        # Code only rejects an answer with no visible link to the passage near the evidence sentence.
        share = len(ans_st & p_st) / len(ans_st)
        if not ans_st & _window_stems(passage, evidence) and share < 0.5:
            r.append(f"answer not supported by the passage ({share:.0%} of its words are in it, none near the evidence)")
    if ans_st:
        # A giveaway is an answer word that is in the question but in NO wrong option (words all options share,
        # like the objects being compared, single nothing out).
        wrong_st = set().union(*(_stems(o) for o in opts[1:]))
        leak = (ans_st & _stems(q)) - wrong_st
        if len(ans_st) >= 2 and len(leak) / len(ans_st) >= 0.6:
            r.append("the question gives away the answer words")
        elif len(ans_st) == 1 and leak:
            r.append("the answer word appears in the question")
    if _norm(evidence) not in _norm(passage):
        r.append("evidence sentence is not in the passage")
    ne = len(tokens(expl))
    if not 3 <= ne <= EXPLAIN_MAX_WORDS:
        r.append(f"explanation must have 3-{EXPLAIN_MAX_WORDS} words (has {ne})")
    return ItemCheck(not r, r)


def map_wrong_options(options: list[str], menu: list[dict]) -> list[str | None]:
    """Which library misconception does each wrong option express? Best word overlap with the belief statement
    (and its example wrong answer); None when nothing overlaps by at least 2 stems. Code-only, no model."""
    out = []
    for o in options[1:]:
        o_st = _stems(o)
        best, best_n = None, 1
        for m in menu:
            d = _stems(m.get("statement", "") + " " + str((m.get("probe") or {}).get("wrong_answer", "")))
            n = len(o_st & d)
            if n > best_n:
                best, best_n = m["id"], n
        out.append(best)
    return out


def assemble_quiz_question(qid: str, item: dict, evidence: str, rng: random.Random, menu: list[dict] | None = None,
                           concept: str = "GEN-READ-K7") -> dict:
    """v2 model output -> one bank question (retention-engine format), options shuffled to A-D."""
    menu = menu or []
    by_id = {m["id"]: m for m in menu}
    mapped = map_wrong_options(item["options"], menu)
    options = [{"text": item["options"][0], "correct": True, "misconception": None}]
    for text, mid in zip(item["options"][1:], mapped):
        options.append({"text": text, "correct": False, "misconception": mid,
                        "feedback": by_id[mid].get("fix", "") if mid else ""})
    rng.shuffle(options)
    for letter, o in zip("ABCD", options):
        o["key"] = letter
    first = next((mid for mid in mapped if mid), None)
    if first and by_id[first].get("concept_id"):
        concept = by_id[first]["concept_id"]
    return {"id": qid, "concept": concept, "type": "understanding", "stem": item["q"], "options": options,
            "evidence": evidence, "explanation": item.get("explain") or f"The passage says: \"{evidence}\"",
            "source": "quiz_v2"}


def quick_summary(backend, passage: str) -> tuple[str, list]:
    """One model call for the summary (speed budget: 1 summary call + 1 call per question). If it fails the
    summary checks, fall back to the passage's most central sentences, unchanged (no model, no invention)."""
    from .generate import make_whole_summary
    from .select import analyse
    res = make_whole_summary(backend, passage, retries=0)
    hard = [c for c in res["checks"] if c.severity == "HARD" and not c.passed]
    if res["text"] and not hard:
        return res["text"], res["attempts"]
    a = analyse(passage)
    picked, words = [], 0
    for i in a.central_ranked:
        picked.append(i)
        words += len(tokens(a.sentences[i]))
        if len(picked) >= 2 and words >= 30 or words > 70:
            break
    return " ".join(a.sentences[i] for i in sorted(picked)), res["attempts"]


def generate_quiz(passage: str, backend, library=None, n_questions: int = 4, seed: int = 0, extra_slots: int = 2,
                  attempts_per_slot: int = 1, title: str = "") -> tuple[dict, dict]:
    """Device pipeline v2: summary (1 call) -> evidence sentences -> one call per question -> code checks -> bank.

    No fill-in-the-blank, ever: if a question fails its checks, the next evidence sentence is tried (up to
    `extra_slots` spares); if fewer than 3 questions survive, the quiz shows fewer. `attempts_per_slot` > 1 retries
    a failed slot at temperature 0.5 first (costs ~10 s per retry on a Pi, so it is off by default).
    Returns (bank, report); the report keeps every attempt, its raw text and its rejection reasons.
    """
    import time
    from .backends.base import chat_for

    t0 = time.perf_counter()
    rng = random.Random(seed)
    summary, sum_attempts = quick_summary(backend, passage)
    t_summary = time.perf_counter() - t0
    mis, generic = [], False
    if library is not None:
        match = library.match(passage, n_misconceptions=14)
        mis = match.misconceptions
        if not match.topics or match.topics[0].score < GENERIC_KW:
            mis, generic = [], True
    evidence = choose_evidence(passage, mis, k=n_questions + extra_slots)
    report = {"summary_s": round(t_summary, 2), "summary_calls": len(sum_attempts), "items": [],
              "mode": "generic" if generic else ("topic" if mis else "no-library"), "calls": len(sum_attempts),
              "prompt_tokens": sum(a.prompt_tokens or 0 for a in sum_attempts),
              "new_tokens": sum(a.new_tokens or 0 for a in sum_attempts)}
    questions = []
    for ev in evidence:
        if len(questions) >= n_questions:
            break
        if generic and library is not None:
            menu = generic_menu(ev, library, n=QUIZ_MAX_BELIEFS)
        else:
            menu = choose_beliefs(ev, passage, mis, QUIZ_MAX_BELIEFS) if mis else []
        rec = {"evidence": ev, "beliefs": [m["id"] for m in menu], "attempts": []}
        msgs = build_quiz_messages(passage, ev, [m["statement"] for m in menu])
        prompt = chat_for(backend, msgs[0]["content"], msgs[1]["content"])
        for k in range(max(1, attempts_per_slot)):
            temp = 0.0 if k == 0 else 0.5
            res = backend.generate(prompt, max_new_tokens=QUIZ_MAX_NEW_TOKENS, temperature=temp, task="quiz",
                                   payload={"evidence": ev, "passage": passage, "beliefs": menu})
            report["calls"] += 1
            report["prompt_tokens"] += res.prompt_tokens or 0
            report["new_tokens"] += res.new_tokens or 0
            item = parse_quiz_item(res.text)
            chk = check_quiz_item(item, passage, ev) if item else ItemCheck(False, ["output is not valid JSON"])
            rec["attempts"].append({"text": res.text, "temperature": temp, "ok": chk.ok, "reasons": chk.reasons,
                                    "new_tokens": res.new_tokens, "prompt_tokens": res.prompt_tokens,
                                    "wall_s": round(res.wall_s, 2), "tokens_per_s": res.tokens_per_s,
                                    "ttft_ms": res.ttft_ms})
            if chk.ok:
                q = assemble_quiz_question(f"Q{len(questions) + 1}", item, ev, rng, menu)
                questions.append(q)
                rec["question"] = q
                break
        report["items"].append(rec)
    report["questions"] = len(questions)
    report["total_s"] = round(time.perf_counter() - t0, 2)
    bank = {"title": title, "source": "quiz_v2", "passage": passage, "summary": summary, "questions": questions}
    if library is not None and questions:
        bank = bank_from_questions(title, passage, summary, questions, library) | {"source": "quiz_v2"}
    return bank, report
