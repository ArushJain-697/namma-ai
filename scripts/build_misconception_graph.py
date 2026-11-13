#!/usr/bin/env python3
"""Build the detailed misconception GRAPH for Class 6-10 Maths, Science and Social Science (v2 of the library).

  python scripts/build_misconception_graph.py generate [--model M] [--only ID ...] [--workers 2] [--force]
  python scripts/build_misconception_graph.py assemble

Per topic, a teacher model (Gemini) writes a 3-level concept tree down to the smallest single ideas, prerequisite
links, and misconceptions attached to those ideas (with a deeper root belief and cause links). `assemble` then
resolves links ACROSS topics and classes in code and writes a graph:

  data/misconceptions/graph/nodes.jsonl   one node per line: subject, topic, concept (level 1-3), misconception, root_belief
  data/misconceptions/graph/edges.jsonl   {"src", "dst", "type"} with types:
      part_of        concept -> parent concept or topic; topic -> subject
      needs          concept -> concept it requires first (inside a topic or from an earlier topic/class)
      about          misconception -> the concept it is a wrong idea about
      causes         misconception -> misconception it leads to (same topic)
      from_root      misconception -> root_belief node shared across topics and subjects
      topic_needs    topic -> topic (derived from cross-topic concept links)
  data/misconceptions/graph/stats.json
It also rewrites data/misconceptions/library.jsonl and concepts.jsonl from the graph, so the on-device matcher
(src/sakshi/misconceptions.py) and the retention engine keep working.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_misconception_library as v1  # noqa: E402  (key handling, Gemini call, topic list)

DIR = v1.DIR
RAW = os.path.join(DIR, "raw_v2")
OUT = os.path.join(DIR, "graph")
ERROR_TYPES = dict(v1.ERROR_TYPES)
ERROR_TYPES["general"] = ["everyday_myth", "overgeneralisation", "single_cause_explanation", "confusing_related_terms",
                          "scale_or_quantity", "media_misinformation", "other"]
ERROR_TYPES["maths"] = ["overgeneralised_rule", "whole_number_thinking", "procedure_without_meaning", "notation_misread",
                        "visual_prototype", "language_confusion", "sign_error_belief", "place_value", "scale_or_quantity",
                        "confusing_related_terms", "other"]

PROMPT = """You are an expert teacher-educator in India who studies the misconceptions of school students (HBCSE
Mumbai, AAAS Project 2061, Eedi diagnostic questions, Rosalind Driver's children's ideas in science, concept
inventories). You are building a DETAILED misconception graph for an offline tutor used by Class {grades}
students following the NCERT syllabus.

Topic: {title}
Subject: {subject} ({strand})
What the topic covers: {scope}

Part A: concept tree. Break the topic down to the SMALLEST level, in three levels:
- level 1: the 2 to 4 big ideas of the topic;
- level 2: the sub-concepts under each big idea;
- level 3: the smallest single ideas or skills, each one a single fact, rule or step a student can get right or wrong
  (e.g. "Like poles repel", "Adding fractions needs a common denominator", "The Gram Sabha is all adult voters of a village").
Aim for 15 to 30 nodes in total. For every node give:
  "key" (n1, n2, ...), "name" (short), "level" (1, 2 or 3), "parent" (key of its level above, null for level 1),
  "prereqs" (keys of nodes in THIS topic that must be understood first, never a node's own parent or descendants),
  "external_prereqs" (names of concepts from OTHER topics or earlier classes that must be understood first,
  e.g. "multiplication of whole numbers", "concept of force", "what is a democracy"; empty list if none).

Part B: misconceptions. Attach misconceptions to level 2 and level 3 nodes, 1 to 3 per node wherever real student
misconceptions exist, 12 to 30 in total. Each misconception:
  "key" (m1, m2, ...), "node" (key of the concept it is about),
  "statement": the wrong belief as one short sentence the student would agree with, clearly FALSE, never vague,
  "why": why students come to believe it (one sentence),
  "fix": what is actually true, {truth}, in one or two simple sentences at Class {grades} level,
  "probe": {{"question": "...", "wrong_answer": "..."}} where the wrong answer follows from the belief,
  "error_type": one of {error_types},
  "root_belief": the deeper general belief behind it, in at most 10 words, phrased generally so that the same root
    can apply in other topics or subjects (e.g. "bigger or more means more effect", "what you cannot see does not exist",
    "a rule from whole numbers works everywhere", "one event has one single cause", "a word means its everyday meaning"),
  "causes": keys of other misconceptions in this topic that this one leads to (often empty),
  "trigger_cues": 3 to 8 lowercase words likely to appear in a textbook passage about it,
  "confidence": "lit_supported" only if documented in education research, else "plausible",
  "source_hint": the KIND of source if lit_supported (never invent a paper title or URL), else null.
Misconceptions on the same node must have different root ideas. Do not copy NCERT sentences.

Return only JSON: {{"nodes": [...], "misconceptions": [...]}}
"""


def truth_rule(topic: dict) -> str:
    if topic["subject"] == "general":
        return "correct according to reliable public sources (WHO, ISRO, RBI, Government of India)"
    return "correct by the NCERT syllabus"


def _clean_nodes(raw_nodes: list) -> tuple[list[dict], list[str]]:
    probs, nodes, keys = [], [], set()
    for n in raw_nodes or []:
        k, name = str(n.get("key", "")).strip(), str(n.get("name", "")).strip()
        if not k or not name or k in keys:
            probs.append(f"node dropped: {n.get('name')!r}")
            continue
        keys.add(k)
        lvl = n.get("level") if n.get("level") in (1, 2, 3) else 3
        nodes.append({"key": k, "name": name, "level": lvl, "parent": n.get("parent"), "prereqs": n.get("prereqs") or [],
                      "external_prereqs": [str(x).strip() for x in (n.get("external_prereqs") or []) if str(x).strip()]})
    for n in nodes:  # repair parents and prereqs
        if n["parent"] not in keys or n["parent"] == n["key"]:
            n["parent"] = None
        n["prereqs"] = [p for p in dict.fromkeys(map(str, n["prereqs"])) if p in keys and p != n["key"]]
    by_key = {n["key"]: n for n in nodes}

    def ancestors(k):
        seen, cur = set(), by_key[k]["parent"]
        while cur and cur not in seen:
            seen.add(cur)
            cur = by_key[cur]["parent"]
        return seen

    # Drop prereq links that would make a cycle (keep in the order given).
    accepted: dict[str, list[str]] = {n["key"]: [] for n in nodes}

    def reaches(a, b):
        stack, seen = [a], set()
        while stack:
            x = stack.pop()
            if x == b:
                return True
            if x not in seen:
                seen.add(x)
                stack.extend(accepted[x])
        return False

    for n in nodes:
        for p in n["prereqs"]:
            if p in ancestors(n["key"]) or reaches(p, n["key"]):
                probs.append(f"{n['key']}: dropped cyclic prereq {p}")
            else:
                accepted[n["key"]].append(p)
        n["prereqs"] = accepted[n["key"]]
    return nodes, probs


def _clean_misconceptions(topic: dict, raw: list, node_keys: set) -> tuple[list[dict], list[str]]:
    probs, out, keys = [], [], set()
    allowed = set(ERROR_TYPES[topic["subject"]])
    for m in raw or []:
        k, st, fix = str(m.get("key", "")).strip(), str(m.get("statement", "")).strip(), str(m.get("fix", "")).strip()
        if not k or k in keys or str(m.get("node")) not in node_keys or not (3 <= len(st.split()) <= 35) or not fix:
            probs.append(f"misconception dropped: {st[:50]!r}")
            continue
        if re.search(r"\b(students?|learners?|children)\b.*\b(do not|don't|fail to|confuse)\b", st, re.I):
            probs.append(f"vague misconception dropped: {st[:50]!r}")
            continue
        keys.add(k)
        probe = m.get("probe") if isinstance(m.get("probe"), dict) else {}
        et = str(m.get("error_type", "other"))
        out.append({"key": k, "node": str(m["node"]), "statement": st, "why": str(m.get("why", "")).strip(), "fix": fix,
                    "probe": {"question": str(probe.get("question", "")).strip(),
                              "wrong_answer": str(probe.get("wrong_answer", "")).strip()},
                    "error_type": et if et in allowed else "other",
                    "root_belief": str(m.get("root_belief", "")).strip().rstrip("."),
                    "causes": [str(c) for c in (m.get("causes") or [])],
                    "trigger_cues": [str(t).lower().strip() for t in (m.get("trigger_cues") or []) if str(t).strip()][:8],
                    "confidence": "lit_supported" if m.get("confidence") == "lit_supported" else "plausible",
                    "source_hint": (str(m["source_hint"]).strip() or None) if m.get("source_hint") else None})
    for m in out:
        m["causes"] = [c for c in dict.fromkeys(m["causes"]) if c in keys and c != m["key"]]
    return out, probs


def validate(topic: dict, data: dict) -> tuple[list[dict], list[dict], list[str]]:
    nodes, p1 = _clean_nodes(data.get("nodes"))
    mis, p2 = _clean_misconceptions(topic, data.get("misconceptions"), {n["key"] for n in nodes})
    probs = p1 + p2
    if len(nodes) < 8:
        probs.append(f"only {len(nodes)} concept nodes")
    if len(mis) < 6:
        probs.append(f"only {len(mis)} misconceptions")
    return nodes, mis, probs


def cmd_generate(args) -> int:
    teacher = v1.Teacher(args.models.split(","))
    print("teacher order:", teacher.describe(), flush=True)
    topics = [t for t in v1.load_topics() if not args.only or t["id"] in args.only]
    os.makedirs(RAW, exist_ok=True)
    todo = [t for t in topics if args.force or not os.path.exists(os.path.join(RAW, t["id"] + ".json"))]
    print(f"{len(todo)} of {len(topics)} topics to generate", flush=True)

    def one(t):
        prompt = PROMPT.format(grades="/".join(map(str, t["grades"])), title=t["title"], subject=t["subject"],
                               strand=t["strand"], scope=t["scope"], error_types=", ".join(ERROR_TYPES[t["subject"]]), truth=truth_rule(t))
        t0 = time.time()
        text, usage, used = teacher.generate(prompt)
        data = v1.loads_lenient(text)
        nodes, mis, probs = validate(t, data)
        with open(os.path.join(RAW, t["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump({"topic": t, "model": used, "usage": usage, "seconds": round(time.time() - t0, 1),
                       "response": data, "problems": probs}, f, indent=1, ensure_ascii=False)
        return f"{t['id']:<26} {used:<28} {len(nodes)} nodes, {len(mis)} misconceptions, {len(probs)} notes, {time.time() - t0:.0f}s"

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(one, t): t for t in todo}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"{futs[fut]['id']:<26} FAILED: {str(e)[:160]}", flush=True)
    print(f"done; {failed} failed (rerun to retry)")
    return 1 if failed else 0


DEEPEN = """You are an expert teacher-educator in India who studies school students' misconceptions.
Topic: {title} ({subject}, Class {grades}). Concept tree of the topic (key, level, name):
{nodes}
Misconceptions already listed (do NOT repeat these or their root ideas):
{existing}

Add {want} MORE distinct, real misconceptions that Class {grades} students hold about this topic, attached to
level 2 and level 3 concepts (spread them across different concepts). Same rules: "statement" is the wrong belief
as one short sentence the student would agree with, clearly FALSE and specific; "why"; "fix" ({truth},
simple); "probe" {{"question", "wrong_answer"}} where the wrong answer follows from the belief; "error_type" one
of {error_types}; "root_belief" (general, at most 10 words); "causes" (keys, may be empty); "trigger_cues"
(3-8 lowercase words); "confidence" ("lit_supported" only if documented in research, else "plausible");
"source_hint" (kind of source or null). Use keys {first_key} onwards and "node" = a concept key from the tree.
Return only JSON: {{"misconceptions": [...]}}
"""


def cmd_deepen(args) -> int:
    """Add misconceptions to thin topics (fewer than --min) in place; the raw file records the extra call."""
    teacher = v1.Teacher(args.models.split(","))
    print("teacher order:", teacher.describe(), flush=True)
    topics = {t["id"]: t for t in v1.load_topics()}
    todo = []
    for f in sorted(os.listdir(RAW)):
        raw = json.load(open(os.path.join(RAW, f), encoding="utf-8"))
        n = len(raw["response"].get("misconceptions") or [])
        if n < args.min and not raw.get("deepened_by") and raw["topic"]["id"] in topics:
            todo.append(f)
    print(f"{len(todo)} thin topics to deepen", flush=True)

    def one(f):
        path = os.path.join(RAW, f)
        raw = json.load(open(path, encoding="utf-8"))
        t = topics[raw["topic"]["id"]]
        nodes, mis, _ = validate(t, raw["response"])
        want = max(6, args.min + 2 - len(mis))
        prompt = DEEPEN.format(title=t["title"], subject=t["subject"], grades="/".join(map(str, t["grades"])),
                               nodes="\n".join(f"{n['key']} L{n['level']} {n['name']}" for n in nodes),
                               existing="\n".join(f"- {m['statement']}" for m in mis) or "(none)", want=want,
                               error_types=", ".join(ERROR_TYPES[t["subject"]]), first_key=f"m{len(mis) + 1}",
                               truth=truth_rule(t))
        text, usage, used = teacher.generate(prompt)
        extra = v1.loads_lenient(text).get("misconceptions") or []
        have = {m["key"] for m in raw["response"].get("misconceptions") or []}
        k = len(have)
        for m in extra:  # re-key to avoid collisions
            k += 1
            old = m.get("key")
            m["key"] = f"m{k}"
            m["causes"] = []
        raw["response"].setdefault("misconceptions", []).extend(extra)
        raw["deepened_by"] = used
        json.dump(raw, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        _, mis2, _ = validate(t, raw["response"])
        return f"{t['id']:<26} {used:<28} {len(mis)} -> {len(mis2)} misconceptions"

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(one, f): f for f in todo}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"{futs[fut]:<30} FAILED: {str(e)[:150]}", flush=True)
    print(f"done; {failed} failed (rerun to retry)")
    return 0


# ---- assembling the graph ----------------------------------------------------------------------------------
_STOP = v1._STOP | set("concept concepts idea ideas basic understanding knowledge meaning what how why".split())


def _toks(s: str) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z0-9]+", s.lower()):
        if w in _STOP or len(w) < 3:
            continue
        out.add(w[:-1] if w.endswith("s") and len(w) > 4 else w)
    return out


def _sim(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def cmd_assemble(args) -> int:
    topics = {t["id"]: t for t in v1.load_topics()}
    nodes, edges, notes = [], [], {}
    concepts, mis_all = [], []
    subjects = sorted({t["subject"] for t in topics.values()})
    for s in subjects:
        nodes.append({"id": f"SUBJ-{s}", "type": "subject", "name": s})
    for tid, t in topics.items():
        path = os.path.join(RAW, tid + ".json")
        nodes.append({"id": tid, "type": "topic", "name": t["title"], "subject": t["subject"], "strand": t["strand"],
                      "grades": t["grades"], "generated": os.path.exists(path)})
        edges.append({"src": tid, "dst": f"SUBJ-{t['subject']}", "type": "part_of"})
        if not os.path.exists(path):
            notes[tid] = ["not generated"]
            continue
        raw = json.load(open(path, encoding="utf-8"))
        cn, mn, probs = validate(t, raw["response"])
        if probs:
            notes[tid] = probs
        kid = {n["key"]: f"{tid}-K{i + 1}" for i, n in enumerate(cn)}
        for n in cn:
            cid = kid[n["key"]]
            c = {"id": cid, "type": "concept", "name": n["name"], "level": n["level"], "topic_id": tid,
                 "topic": t["title"], "subject": t["subject"], "grades": t["grades"],
                 "external_prereqs": n["external_prereqs"]}
            nodes.append(c)
            concepts.append(c)
            edges.append({"src": cid, "dst": kid[n["parent"]] if n["parent"] else tid, "type": "part_of"})
            for p in n["prereqs"]:
                edges.append({"src": cid, "dst": kid[p], "type": "needs"})
        mid = {m["key"]: f"{kid[m['node']]}-M{i + 1}" for i, m in enumerate(mn)}
        for m in mn:
            rec = {"id": mid[m["key"]], "type": "misconception", "topic_id": tid, "topic": t["title"],
                   "subject": t["subject"], "strand": t["strand"], "grades": t["grades"], "concept_id": kid[m["node"]],
                   "concept": next(n["name"] for n in cn if n["key"] == m["node"]),
                   **{k: v for k, v in m.items() if k not in ("key", "node", "causes")},
                   "source": "teacher_generated", "teacher_model": raw.get("model")}
            nodes.append(rec)
            mis_all.append(rec)
            edges.append({"src": rec["id"], "dst": rec["concept_id"], "type": "about"})
            for c in m["causes"]:
                edges.append({"src": rec["id"], "dst": mid[c], "type": "causes"})

    # Cross-topic prerequisites: match each external prereq name to the most similar concept in another topic
    # taught in the same or an earlier class (same subject preferred).
    index = [(c, _toks(c["name"] + " " + c["topic"])) for c in concepts]
    unresolved = 0
    topic_links = Counter()
    for c in concepts:
        for name in c.pop("external_prereqs"):
            q = _toks(name)
            best, best_s = None, 0.0
            for d, dt in index:
                if d["topic_id"] == c["topic_id"] or min(d["grades"]) > max(c["grades"]):
                    continue
                s = _sim(q, dt) + (0.05 if d["subject"] == c["subject"] else 0.0) + (0.03 if d["level"] < 3 else 0.0)
                if s > best_s:
                    best, best_s = d, s
            if best and best_s >= args.link:
                edges.append({"src": c["id"], "dst": best["id"], "type": "needs", "via": name, "score": round(best_s, 2)})
                topic_links[(c["topic_id"], best["topic_id"])] += 1
            else:
                unresolved += 1
                c.setdefault("unresolved_prereqs", []).append(name)
    for (a, b), n in topic_links.items():
        edges.append({"src": a, "dst": b, "type": "topic_needs", "weight": n})

    # Root beliefs: cluster similar root_belief texts across all topics and subjects into shared nodes.
    roots: list[dict] = []
    for m in mis_all:
        rb = m.get("root_belief") or ""
        q = _toks(rb)
        if not q:
            continue
        hit = max(roots, key=lambda r: _sim(q, r["toks"]), default=None)
        if hit and _sim(q, hit["toks"]) >= args.root:
            hit["members"].append(m["id"])
        else:
            hit = {"id": f"ROOT-{len(roots) + 1}", "name": rb, "toks": q, "members": [m["id"]]}
            roots.append(hit)
    for r in roots:
        subjects_r = sorted({next(x["subject"] for x in mis_all if x["id"] == r["members"][0])})
        nodes.append({"id": r["id"], "type": "root_belief", "name": r["name"], "members": len(r["members"]),
                      "subjects": sorted({x["subject"] for x in mis_all if x["id"] in set(r["members"])}) or subjects_r})
        for mid_ in r["members"]:
            edges.append({"src": mid_, "dst": r["id"], "type": "from_root"})

    # Meaning-based links (scripts/fix_graph_links.py) replace the word-overlap ones above when available.
    lpath = os.path.join(DIR, "links_v2.json")
    if os.path.exists(lpath):
        lv = json.load(open(lpath, encoding="utf-8"))
        ids = {n["id"] for n in nodes}
        edges = [e for e in edges if not (e["type"] == "needs" and "via" in e) and e["type"] not in ("topic_needs", "from_root")]
        nodes = [n for n in nodes if n["type"] != "root_belief"]
        linked = defaultdict(set)
        topic_of = {n["id"]: n.get("topic_id") for n in nodes if n["type"] == "concept"}
        tl = Counter()
        for l in lv["prereq_links"]:
            if l["src"] in ids and l["dst"] in ids:
                edges.append({"src": l["src"], "dst": l["dst"], "type": "needs", "via": l["via"], "how": l["how"], "score": l["score"]})
                linked[l["src"]].add(l["via"])
                tl[(topic_of[l["src"]], topic_of[l["dst"]])] += 1
        for (a, b), k in tl.items():
            edges.append({"src": a, "dst": b, "type": "topic_needs", "weight": k})
        for c in concepts:
            left = [x for x in c.get("unresolved_prereqs", []) if x not in linked[c["id"]]]
            if left:
                c["unresolved_prereqs"] = left
            else:
                c.pop("unresolved_prereqs", None)
        for r in lv["roots"]:
            nodes.append({"id": r["id"], "type": "root_belief", "name": r["name"], "explanation": r.get("explanation", ""),
                          "members": r["members"], "subjects": r["subjects"]})
        for mid, rid in lv["misconception_root"].items():
            if mid in ids:
                edges.append({"src": mid, "dst": rid, "type": "from_root"})
        roots = [{"members": [None] * r["members"]} for r in lv["roots"]]  # for the stats below
        unresolved = sum(len(c.get("unresolved_prereqs", [])) for c in concepts)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "nodes.jsonl"), "w", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "edges.jsonl"), "w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Library + concepts files in the v1 format, for the on-device matcher and the retention engine.
    needs = defaultdict(list)
    for e in edges:
        if e["type"] == "needs":
            needs[e["src"]].append(e["dst"])
    by_concept = defaultdict(list)
    for m in mis_all:
        by_concept[m["concept_id"]].append(m["id"])
    import hashlib
    with open(os.path.join(DIR, "library.jsonl"), "w", encoding="utf-8") as f:
        for m in mis_all:
            rec = {k: v for k, v in m.items() if k != "type"}
            rec["held_out"] = int(hashlib.sha1(m["id"].encode()).hexdigest(), 16) % 100 < v1.HELD_OUT_PERCENT
            rec["duplicate_of"] = None
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(os.path.join(DIR, "concepts.jsonl"), "w", encoding="utf-8") as f:
        for c in concepts:
            f.write(json.dumps({"id": c["id"], "topic_id": c["topic_id"], "topic": c["topic"], "name": c["name"],
                                "level": c["level"], "prereqs": needs[c["id"]], "misconceptions": by_concept[c["id"]]},
                               ensure_ascii=False) + "\n")

    # Generic reading-skill beliefs (fallback menu for off-syllabus passages): library + concepts + graph nodes.
    gpath = os.path.join(DIR, "generic.jsonl")
    if os.path.exists(gpath):
        generic = [json.loads(l) for l in open(gpath, encoding="utf-8") if l.strip()]
        with open(os.path.join(DIR, "library.jsonl"), "a", encoding="utf-8") as f:
            for m in generic:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        with open(os.path.join(DIR, "concepts.jsonl"), "a", encoding="utf-8") as f:
            for m in generic:
                f.write(json.dumps({"id": m["concept_id"], "topic_id": m["topic_id"], "topic": m["topic"],
                                    "name": m["concept"], "level": 3, "prereqs": [], "misconceptions": [m["id"]]}) + "\n")
        nodes.append({"id": "SUBJ-reading_skill", "type": "subject", "name": "reading_skill"})
        nodes.append({"id": "GEN-READ", "type": "topic", "name": "Reading and reasoning", "subject": "reading_skill",
                      "strand": "reading", "grades": [6, 7, 8, 9, 10], "generated": True})
        edges.append({"src": "GEN-READ", "dst": "SUBJ-reading_skill", "type": "part_of"})
        for m in generic:
            nodes.append({"id": m["concept_id"], "type": "concept", "name": m["concept"], "level": 3, "topic_id": "GEN-READ",
                          "topic": m["topic"], "subject": "reading_skill", "grades": m["grades"]})
            nodes.append({**m, "type": "misconception"})
            edges.append({"src": m["concept_id"], "dst": "GEN-READ", "type": "part_of"})
            edges.append({"src": m["id"], "dst": m["concept_id"], "type": "about"})
        with open(os.path.join(OUT, "nodes.jsonl"), "w", encoding="utf-8") as f:
            for n in nodes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")
        with open(os.path.join(OUT, "edges.jsonl"), "w", encoding="utf-8") as f:
            for e in edges:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    et = Counter(e["type"] for e in edges)
    nt = Counter(n["type"] for n in nodes)
    stats = {"nodes": dict(nt), "edges": dict(et),
             "topics_generated": sum(1 for n in nodes if n["type"] == "topic" and n["generated"]),
             "concepts_by_level": dict(Counter(c["level"] for c in concepts)),
             "misconceptions_by_subject": dict(Counter(m["subject"] for m in mis_all)),
             "cross_topic_needs": sum(1 for e in edges if e["type"] == "needs" and "via" in e),
             "unresolved_external_prereqs": unresolved,
             "root_beliefs_shared_by_2plus": sum(1 for r in roots if len(r["members"]) > 1),
             "root_beliefs_spanning_subjects": sum(1 for n in nodes if n["type"] == "root_belief" and len(n["subjects"]) > 1),
             "teacher_tokens_out": sum(json.load(open(os.path.join(RAW, f))).get("usage", {}).get("candidatesTokenCount", 0)
                                       for f in os.listdir(RAW) if f.endswith(".json")) if os.path.isdir(RAW) else 0,
             "notes": notes}
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps({k: v for k, v in stats.items() if k != "notes"}, indent=2))
    print(f"{len(notes)} topics with notes (graph/stats.json)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("--models", default="gemini-3-flash-preview,gemini-3.1-flash-lite,claude:claude-sonnet-5-5,claude:sonnet",
                   help="comma-separated, strongest first; each is tried on every key before the next")
    g.add_argument("--only", nargs="*")
    g.add_argument("--workers", type=int, default=2)
    g.add_argument("--force", action="store_true")
    dp = sub.add_parser("deepen")
    dp.add_argument("--models", default="gemini-3-flash-preview,gemini-3.1-flash-lite,claude:claude-sonnet-5-5,claude:sonnet")
    dp.add_argument("--min", type=int, default=10)
    dp.add_argument("--workers", type=int, default=2)
    a = sub.add_parser("assemble")
    a.add_argument("--link", type=float, default=0.34, help="similarity needed to link a cross-topic prerequisite")
    a.add_argument("--root", type=float, default=0.5, help="similarity needed to merge two root beliefs")
    args = ap.parse_args()
    if args.cmd == "generate":
        return cmd_generate(args)
    if args.cmd == "deepen":
        return cmd_deepen(args)
    if args.cmd == "assemble":
        return cmd_assemble(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
