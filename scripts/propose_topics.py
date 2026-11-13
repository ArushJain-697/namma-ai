#!/usr/bin/env python3
"""Ask Sonnet for NEW topics to add to the misconception graph, reject near-duplicates, append the rest.

  python3 scripts/propose_topics.py --subject science --n 10
  python3 scripts/propose_topics.py --subject general --n 10 --area "agriculture and rural life"

Appends to data/misconceptions/topics.jsonl and prints the new ids (feed them to build_misconception_graph.py).
Rules: a new topic must be a distinct idea taught or met by Class 6-10 students, not a sub-part or rename of an
existing topic (look-alike topics confuse passage matching). Candidates whose title+scope overlap an existing
topic by 50% or more of their words are dropped.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_misconception_library as v1  # noqa: E402

TOPICS = os.path.join(ROOT, "data", "misconceptions", "topics.jsonl")
PREFIX = {"maths": "MAT", "science": "SCI", "social": "SOC", "general": "GEN"}
STRANDS = {"maths": "maths", "science": "physics | chemistry | biology | earth_space",
           "social": "history | geography | civics | economics",
           "general": "health | nutrition | environment | technology | sports | space | safety | money | citizenship | culture | careers | other"}

PROMPT = """You are helping build a misconception graph for an offline tutor for Indian Class 6-10 students.
Subject: {subject}. {area}
Topics the graph ALREADY has, in ALL subjects (do not repeat, rename, re-frame or split any of these, even
under a different subject):
{existing}

Propose {n} NEW topics that Class 6-10 students in India study or meet in daily life and that are clearly
different from every topic above. For each: "key" (UPPERCASE letters/digits, at most 16 characters, unique),
"strand" (one of: {strands}), "grades" (list of classes 6-10 where it fits), "title" (short), "scope"
(one line listing the concrete sub-ideas, in the style of the existing ones). Prefer topics where students
commonly hold misconceptions. Return only JSON: {{"topics": [{{"key": "...", "strand": "...", "grades": [7, 8],
"title": "...", "scope": "..."}}]}}
"""

_STOP = set("and the of in a an to for with on its their from how what why".split())


def words(t: dict) -> set:
    return {w for w in re.findall(r"[a-z]+", (t["title"] + " " + t.get("scope", "")).lower()) if w not in _STOP and len(w) > 2}


_EMB = {}


def closest(t: dict, topics: list) -> tuple[float, str]:
    """Most similar existing topic by MEANING (small embedding model) when available, else by shared words."""
    text = lambda x: f"{x['title']}: {x.get('scope', '')}"  # noqa: E731
    try:
        from sentence_transformers import SentenceTransformer
        if "m" not in _EMB:
            _EMB["m"] = SentenceTransformer("BAAI/bge-small-en-v1.5")
        m = _EMB["m"]
        key = len(topics)
        if _EMB.get("n") != key:
            _EMB["v"], _EMB["n"] = m.encode([text(o) for o in topics], normalize_embeddings=True), key
        q = m.encode([text(t)], normalize_embeddings=True)[0]
        sims = _EMB["v"] @ q
        i = int(sims.argmax())
        return float(sims[i]), topics[i]["title"]
    except ImportError:
        w = words(t)
        best = max(((len(w & words(o)) / max(1, min(len(w), len(words(o)))), o["title"]) for o in topics), default=(0, ""))
        return best[0] + 0.3, best[1]  # word overlap underestimates sameness; shift onto the same 0.8 scale


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True, choices=list(PREFIX))
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--area", default="", help="optional focus, e.g. 'Class 9-10 chemistry' or 'rural livelihoods'")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--max-similar", type=float, default=0.78,
                    help="meaning similarity (0-1) to an existing topic above which a proposal is rejected")
    args = ap.parse_args()

    topics = [json.loads(l) for l in open(TOPICS, encoding="utf-8") if l.strip()]
    existing = "\n".join(f"- [{t['subject']}] {t['title']}" for t in topics)
    prompt = PROMPT.format(subject=args.subject, area=f"Focus: {args.area}." if args.area else "", existing=existing,
                           n=args.n, strands=STRANDS[args.subject])
    text, _ = v1.claude_generate(prompt, args.model, timeout=900)
    cand = v1.loads_lenient(text).get("topics", [])
    ids = {t["id"] for t in topics}
    added = []
    for c in cand:
        key = re.sub(r"[^A-Z0-9]", "", str(c.get("key", "")).upper())[:16]
        tid = f"{PREFIX[args.subject]}-{key}"
        grades = sorted({int(g) for g in c.get("grades", []) if str(g).isdigit() and 6 <= int(g) <= 10}) or [6, 7, 8, 9, 10]
        t = {"id": tid, "subject": args.subject, "strand": str(c.get("strand", "other")).split("|")[0].strip() or "other",
             "grades": grades, "title": str(c.get("title", "")).strip(), "scope": str(c.get("scope", "")).strip()}
        if not key or tid in ids or not t["title"] or not t["scope"]:
            print(f"skip (bad or duplicate id): {c.get('title')}")
            continue
        sim, other = closest(t, topics)
        if sim >= args.max_similar:
            print(f"skip (same idea as '{other}', similarity {sim:.2f}): {t['title']}")
            continue
        topics.append(t)
        ids.add(tid)
        added.append(t)
    with open(TOPICS, "a", encoding="utf-8") as f:
        for t in added:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"added {len(added)} topics: " + " ".join(t["id"] for t in added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
