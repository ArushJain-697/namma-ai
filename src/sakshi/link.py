"""Connect GURU's quiz to the retention engine: tag each wrong option with a misconception from the graph,
pick a concept for each question, and build the bank the adaptive session reads.

Option -> misconception is hybrid retrieval, offline and CPU-cheap (no extra model):
  1. candidates: only misconceptions inside the passage's topics (the graph narrows ~4,000 beliefs to ~50).
     Off-syllabus gate: when the passage fits no topic (the same calibrated strength test the diagnostic path
     uses, diagnostic.GENERIC_KW / GENERIC_COS), there are no candidates and every option stays unlinked;
  2. rank the candidates twice, by keywords (BM25 over the belief's statement + its typical wrong answer, with the
     repo's own stemmer) and by meaning (bge-small cosine, the embeddings the mapper already holds), and fuse the
     two rankings with reciprocal rank fusion (RRF, k=60; Cormack et al. 2009);
  3. abstain: if the fused winner's cosine is below ABSTAIN the option keeps no misconception (the Bayes step then
     treats it as a plain wrong answer instead of evidence for a belief). A question none of whose options link
     gets the concept UNLINKED instead of an arbitrary graph concept.
ABSTAIN is tuned on a held-out split of the teacher-labelled pairs and reported on the other split
(scripts/eval_mapping.py --links -> results/mapping_eval_v2.json).
Default is method="legacy" (cosine + NLI rerank): on the held-out split it has the best top-1 precision at ~75% coverage (0.626 vs RRF 0.605), and top-1 is what feeds the diagnosis. RRF has better recall@5 (0.923 vs 0.907).
Prerequisite concepts from the graph get template questions built from the graph itself (fix = right answer,
misconception statements = wrong options), so the walk-down has something to ask without another model call.
"""
from __future__ import annotations

import math
import random
from collections import Counter

import numpy as np

from .text import content_stems

ABSTAIN = 0.755       # cosine of the fused winner; 75% coverage on the TUNE split (0.754-0.756) (see scripts/eval_mapping.py --links)
LEGACY_ABSTAIN = 0.76  # the old linker's threshold (it was set on all labelled pairs, so it saw the test items)
NLI_W = 0.3
RRF_K = 60
UNLINKED = "unlinked"
UNLINKED_NAME = "Ideas from your page"  # shown to the child: a page question that matched no graph concept


def option_text(q: str, opt: str) -> str:
    return f"{q} Wrong answer: {opt}"


def belief_text(m: dict) -> str:
    return f"{m.get('statement', '')} {(m.get('probe') or {}).get('wrong_answer', '')}"


class BM25:
    """Okapi BM25 over a fixed list of documents (standard library + the repo's stemmer; runs on the device)."""

    def __init__(self, docs: list[str], k1: float = 1.2, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(content_stems(d)) for d in docs]
        self.len = [sum(d.values()) for d in self.docs]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 1.0
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query: str, idx: list[int]) -> np.ndarray:
        q = set(content_stems(query))
        out = np.zeros(len(idx), dtype=np.float32)
        for j, i in enumerate(idx):
            d, ln, s = self.docs[i], self.len[i], 0.0
            for t in q:
                tf = d.get(t)
                if tf:
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * ln / self.avg))
            out[j] = s
        return out


def rrf(*rankings: list[int], k: int = RRF_K) -> list[int]:
    """Reciprocal rank fusion of several rankings of the same items (best first)."""
    s: dict[int, float] = {}
    for r in rankings:
        for pos, i in enumerate(r):
            s[i] = s.get(i, 0.0) + 1.0 / (k + pos + 1)
    return sorted(s, key=lambda i: (-s[i], i))


def off_syllabus(mapper) -> bool:
    """The passage fits no topic: the calibrated test diagnostic.generate_bank uses, on mapper.topics()' strength."""
    from .diagnostic import GENERIC_COS, GENERIC_KW
    st = getattr(mapper, "last_strength", None)
    if not st:
        return False
    return st.get("kw", 1e9) < GENERIC_KW and (st.get("cos") is None or st["cos"] < GENERIC_COS)


class Linker:
    def __init__(self, mapper, k: int = 8, rerank: bool = True, method: str = "legacy", abstain: float | None = None):
        self.mp, self.lib, self.k, self.rerank, self.method = mapper, mapper.lib, k, rerank, method
        self.abstain = abstain if abstain is not None else (LEGACY_ABSTAIN if method == "legacy" else ABSTAIN)
        self.E = mapper.E_mis / np.linalg.norm(mapper.E_mis, axis=1, keepdims=True)
        self.bm25 = BM25([belief_text(m) for m in mapper.items])
        self.gated = False

    def candidates(self, topics) -> list[int]:
        """Misconceptions in the passage's topics; none when the passage is off-syllabus (call after mapper.topics)."""
        self.gated = off_syllabus(self.mp)
        if self.gated:
            return []
        return [i for i, m in enumerate(self.mp.items) if m["topic_id"] in topics]

    def rank(self, text: str, cand: list[int], method: str | None = None) -> tuple[list[int], dict[int, float]]:
        """Candidates best-first by `method` (bm25 | dense | rrf | legacy), and the cosine of each."""
        method = method or self.method
        v = self.mp.enc.embed([text])[0]
        cos_arr = self.E[cand] @ v
        cos = {i: float(c) for i, c in zip(cand, cos_arr)}
        dense = [cand[j] for j in np.argsort(-cos_arr, kind="stable")]
        if method == "dense":
            return dense, cos
        bm = self.bm25.score(text, cand)
        lex = [cand[j] for j in np.argsort(-bm, kind="stable")]
        if method == "bm25":
            return lex, cos
        if method == "rrf":
            return rrf(lex, dense), cos
        # legacy: top-k by cosine, then cosine + NLI_W * P(entail) re-rank
        top = dense[: self.k]
        score = {i: cos[i] for i in top}
        if self.rerank and getattr(self.mp.enc, "nli", None):
            p = self.mp.enc.nli([(text, self.mp.items[i]["statement"]) for i in top])
            score = {i: cos[i] + NLI_W * float(p[k, 1]) for k, i in enumerate(top)}
        return sorted(top, key=lambda i: -score[i]) + dense[self.k:], cos

    def tag(self, text: str, cand: list[int], exclude: set = frozenset()) -> tuple[dict | None, float]:
        """Best misconception for `text`, or None (abstain / off-syllabus / no candidates), and its cosine."""
        cand = [i for i in cand if self.mp.items[i]["id"] not in exclude]
        if not cand:
            return None, 0.0
        order, cos = self.rank(text, cand)
        best = order[0]
        return (self.mp.items[best] if cos[best] >= self.abstain else None), cos[best]


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
    cid = cid or UNLINKED  # no believable link: say so instead of filing it under an arbitrary concept
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
        for p in lib.concepts.get(cid, {}).get("prereqs", [])[:2] if cid != UNLINKED else []:
            if p in lib.concepts and p not in cids:
                cids.append(p)
    for cid in cids:
        if cid == UNLINKED:
            continue
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
        c = lib.concepts.get(cid, {"name": UNLINKED_NAME if cid == UNLINKED else cid, "prereqs": []})
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
