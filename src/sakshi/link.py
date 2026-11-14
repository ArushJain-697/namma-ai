"""Connect GURU's quiz to the retention engine: tag each wrong option with a misconception from the graph,
pick a concept for each question, and build the bank the adaptive session reads.

Option -> misconception uses retrieve-then-rerank (the standard design for this task):
  1. retrieve: embed "question + wrong answer" (bge-small) and take the top-k misconceptions by cosine,
     only inside the passage's topics (the graph narrows ~4,000 beliefs to ~50);
  2. rerank: an NLI cross-encoder scores whether "a student who picked this answer" entails the belief;
     final score = cosine + w * P(entail);
  3. abstain: below a threshold the option keeps no misconception (the Bayes step then treats it as a plain
     wrong answer instead of evidence for a belief). Threshold measured on 3,647 teacher-labelled pairs.
Prerequisite concepts from the graph get template questions built from the graph itself (fix = right answer,
misconception statements = wrong options), so the walk-down has something to ask without another model call.
"""
from __future__ import annotations

import random

import numpy as np

ABSTAIN = 0.76      # cosine; keeps ~75% of options at ~57% top-1 precision within the topic (measured)
NLI_W = 0.3


def option_text(q: str, opt: str) -> str:
    return f"{q} Wrong answer: {opt}"


class Linker:
    def __init__(self, mapper, k: int = 8, rerank: bool = True):
        self.mp, self.lib, self.k, self.rerank = mapper, mapper.lib, k, rerank
        self.E = mapper.E_mis / np.linalg.norm(mapper.E_mis, axis=1, keepdims=True)

    def candidates(self, topics) -> list[int]:
        return [i for i, m in enumerate(self.mp.items) if m["topic_id"] in topics]

    def tag(self, text: str, cand: list[int], exclude: set = frozenset()) -> tuple[dict | None, float]:
        cand = [i for i in cand if self.mp.items[i]["id"] not in exclude]
        v = self.mp.enc.embed([text])[0]
        s = self.E[cand] @ v
        top = [cand[j] for j in np.argsort(-s)[: self.k]]
        cos = {i: float(self.E[i] @ v) for i in top}
        score = dict(cos)
        if self.rerank and hasattr(self.mp.enc, "nli"):
            p = self.mp.enc.nli([(text, self.mp.items[i]["statement"]) for i in top])
            score = {i: cos[i] + NLI_W * float(p[k, 1]) for k, i in enumerate(top)}
        best = max(score, key=score.get)
        return (self.mp.items[best] if cos[best] >= ABSTAIN else None), cos[best]


def template_questions(lib, cid: str, rng: random.Random, n: int = 2) -> list[dict]:
    """Recall/application questions for a graph concept, made from its own misconceptions."""
    c = lib.concepts.get(cid)
    ids = [m if isinstance(m, str) else m.get("id") for m in (c or {}).get("misconceptions", [])]
    mis = [lib.by_id[i] for i in ids if i in lib.by_id and lib.by_id[i].get("fix")]
    out = []
    for k in range(min(n, len(mis))):
        right, wrongs = mis[k], [m for j, m in enumerate(mis) if j != k][:3]
        if len(wrongs) < 3:  # pad with beliefs from the same topic's other concepts (false statements too)
            pool = [m for m in lib.items if m["topic_id"] == right["topic_id"] and m["concept_id"] != cid]
            rng.shuffle(pool)
            wrongs += pool[: 3 - len(wrongs)]
        if len(wrongs) < 2:
            break
        opts = [(right["fix"], True, None)] + [(w["statement"], False, w["id"]) for w in wrongs]
        rng.shuffle(opts)
        out.append({"id": f"{cid}-t{k}", "concept": cid, "type": "recall",
                    "stem": f"Which statement about '{c['name'] if c else cid}' is true?",
                    "options": [{"key": "ABCD"[j], "text": t, "correct": ok, "misconception": mid}
                                for j, (t, ok, mid) in enumerate(opts)],
                    "explanation": right["fix"]})
    return out


def probe_question(lib, mid: str, rng: random.Random, qid: str | None = None) -> dict | None:
    """An application question for one belief, from the graph's ready-made probe (a situation question).
    Options are all statements, so their shape gives nothing away: the belief's fix (right), the belief's own
    statement (picking it = evidence for the belief) and two neighbouring beliefs' statements."""
    m = lib.by_id.get(mid)
    if not m or not m.get("fix") or not (m.get("probe") or {}).get("question"):
        return None
    pool = [x for x in lib.items if x["concept_id"] == m["concept_id"] and x["id"] != mid]
    if len(pool) < 2:
        pool += [x for x in lib.items if x["topic_id"] == m["topic_id"] and x["concept_id"] != m["concept_id"]]
    pool = [x for x in pool if x["id"] != mid]
    rng.shuffle(pool)
    others = pool[:2]
    opts = [(m["fix"], True, None), (m["statement"], False, mid)] + [(x["statement"], False, x["id"]) for x in others]
    rng.shuffle(opts)
    return {"id": qid or f"{mid}-probe", "concept": m["concept_id"], "type": "application", "stem": m["probe"]["question"],
            "options": [{"key": "ABCD"[j], "text": t, "correct": ok, "misconception": x} for j, (t, ok, x) in enumerate(opts)],
            "explanation": m["fix"], "targets": mid}


def link_question(linker, cand: list[int], q: dict, i: int) -> tuple[dict, list[dict]]:
    """One GURU question -> a bank question (concept + a misconception per wrong option, or none). Done the moment
    the question is written, so questions can stream to the child one by one."""
    lib = linker.lib
    key = q["answer"] if isinstance(q["answer"], int) else "ABCD".index(q["answer"])
    anchor, _ = linker.tag(f"{q['q']} {q['options'][key]} {q.get('evidence', '')}", cand)
    cid = anchor["concept_id"] if anchor else None
    opts, used, log = [], set(), []
    for j, o in enumerate(q["options"]):
        if j == key:
            opts.append({"key": "ABCD"[j], "text": o, "correct": True, "misconception": None})
            continue
        m, s = linker.tag(option_text(q["q"], o), cand, used)  # one belief per option within a question
        if m:
            used.add(m["id"])
        opts.append({"key": "ABCD"[j], "text": o, "correct": False, "misconception": m["id"] if m else None})
        log.append({"q": i + 1, "option": o, "misconception": m["statement"] if m else None,
                    "id": m["id"] if m else None, "cos": round(s, 3)})
        if m and cid is None:
            cid = m["concept_id"]
    cid = cid or next(iter(lib.concepts))
    return ({"id": f"g{i + 1}", "concept": cid, "type": "recall", "stem": q["q"], "options": opts,
             "explanation": q.get("evidence", "")}, log)


def assemble_bank(lib, linked: list[dict], passage: str, summary: str, title: str = "passage") -> dict:
    """Bank JSON from the linked GURU questions so far + graph prerequisites + graph questions. Cheap (no model),
    so it is rebuilt each time a new question arrives. Graph questions are seeded per concept, so a question id
    always has the same content however many GURU questions have arrived."""
    import copy
    import zlib
    bq = copy.deepcopy(linked)
    tagged = {o["misconception"] for q in bq for o in q["options"] if o["misconception"]}
    cids = list(dict.fromkeys([q["concept"] for q in bq] + [lib.by_id[m]["concept_id"] for m in tagged]))
    for cid in list(cids):
        for p in lib.concepts.get(cid, {}).get("prereqs", [])[:2]:
            if p in lib.concepts and p not in cids:
                cids.append(p)
    for cid in cids:
        rng = random.Random(zlib.crc32(cid.encode()))
        # every concept: a recall question (GURU's, else a graph template) for the way down ...
        if not any(q["concept"] == cid for q in bq):
            for t in template_questions(lib, cid, rng, n=1):
                bq.append(t)
                tagged |= {o["misconception"] for o in t["options"] if o["misconception"]}
        # ... and two application questions (graph probes) for the climb back up and its one retry
        ids = [x if isinstance(x, str) else x.get("id") for x in lib.concepts.get(cid, {}).get("misconceptions", [])]
        for k, mid in enumerate(ids):
            if sum(q["concept"] == cid and q["type"] == "application" for q in bq) >= 2:
                break
            pq = probe_question(lib, mid, rng, f"{cid}-a{k}")
            if pq:
                bq.append(pq)
                tagged |= {o["misconception"] for o in pq["options"] if o["misconception"]}
    home: dict[str, str] = {}
    for q in bq:
        for o in q["options"]:
            if o["misconception"]:
                home.setdefault(o["misconception"], q["concept"])
    for q in bq:  # a belief shared by two concepts' questions: keep it under its first concept, plain wrong elsewhere
        for o in q["options"]:
            if o["misconception"] and home[o["misconception"]] != q["concept"]:
                o["misconception"] = None
    concepts = []
    for cid in cids:
        c = lib.concepts.get(cid, {"name": cid, "prereqs": []})
        concepts.append({"id": cid, "name": c.get("name", cid),
                         "prereqs": [p for p in c.get("prereqs", []) if p in cids],
                         "misconceptions": [{"id": m, "text": lib.by_id[m]["statement"], "fix": lib.by_id[m].get("fix", "")}
                                            for m in sorted(home) if home[m] == cid]})
    return {"title": title, "source": "GURU-0.6B + misconception graph", "passage": passage, "summary": summary,
            "concepts": concepts, "questions": [q for q in bq if q["concept"] in cids]}


def build_bank(mapper, passage: str, summary: str, questions: list[dict], title: str = "passage",
               seed: int = 0) -> tuple[dict, list[dict]]:
    """All at once (questions: GURU output [{q, options, answer, evidence}]). Returns (bank dict, link log)."""
    linker = Linker(mapper)
    cand = linker.candidates(mapper.topics(passage))
    linked, log = [], []
    for i, q in enumerate(questions):
        item, rows = link_question(linker, cand, q, i)
        linked.append(item)
        log += rows
    return assemble_bank(mapper.lib, linked, passage, summary, title), log
