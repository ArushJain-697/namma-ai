#!/usr/bin/env python3
"""Build the misconception library (concepts + misconceptions per NCERT Class 6-10 topic) with Gemini.

  python scripts/build_misconception_library.py --list-models     # which Gemini models this key can use
  python scripts/build_misconception_library.py generate [--model M] [--only ID ...] [--workers 6] [--force]
  python scripts/build_misconception_library.py assemble          # validate, de-duplicate, assign ids, write the library

Needs GEMINI_API_KEY in the environment or in a .env file at the repo root (never committed).
Input:  data/misconceptions/topics.jsonl  (topic names and scope only: syllabus facts, no textbook text)
Output: data/misconceptions/raw/ID.json   (one Gemini answer per topic, so reruns resume)
        data/misconceptions/library.jsonl (one misconception per line, stable ids)
        data/misconceptions/concepts.jsonl(one concept per line with its prerequisites and misconception ids)
        data/misconceptions/review.csv    (a ~10% sample for a person to check: ok / fix / drop)
        data/misconceptions/stats.json
Standard library only, so it also runs on the board.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DIR = os.path.join(ROOT, "data", "misconceptions")
API = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

ERROR_TYPES = {
    "science": ["everyday_language", "intuitive_physics", "living_thing_reasoning", "overgeneralisation",
                "confusing_related_terms", "scale_or_quantity", "single_cause", "process_vs_product",
                "visible_only", "part_whole", "other"],
    "social": ["chronology_slip", "confuses_people_or_places", "confuses_institutions", "single_cause_explanation",
               "presentism", "confusing_related_terms", "overgeneralisation", "numerical_misreading",
               "stereotype", "other"],
}
HELD_OUT_PERCENT = 15  # misconception ids kept out of fine-tuning, to test beliefs the model has never seen

PROMPT = """You are an expert teacher-educator in India who studies the misconceptions of school students
(for example the work of HBCSE in Mumbai, AAAS Project 2061, Rosalind Driver's research on children's ideas
in science, and concept inventories). You are helping build a misconception library for an offline tutor
used by Class {grades} students studying the NCERT syllabus.

Topic: {title}
Subject: {subject} ({strand})
What the topic covers: {scope}

Task:
1. List the 3 to 6 key concepts of this topic, ordered from most basic to most advanced. For each concept give
   the keys of the other concepts in THIS list that a student must understand first ("prereqs").
2. For each concept, list 2 to 4 misconceptions that Class {grades} students in India commonly hold about it.

Rules for each misconception:
- "statement": the wrong belief written as one short sentence the student would agree with, in simple words,
  e.g. "Plants get their food ready-made from the soil." It must be clearly FALSE. Never write vague things
  like "Students do not understand photosynthesis".
- "why": one sentence on why students come to believe it (everyday experience, language, how it is taught).
- "fix": one or two simple sentences saying what is actually true, correct by the NCERT syllabus, at Class {grades} level.
- "probe": a typical question and the wrong answer a student holding this belief would give:
  {{"question": "...", "wrong_answer": "..."}}. The wrong answer must follow from the belief.
- "error_type": one of {error_types}.
- "trigger_cues": 3 to 8 lowercase words or short phrases likely to appear in a textbook passage on this idea.
- "confidence": "lit_supported" only if this misconception is documented in education research; otherwise "plausible".
- "source_hint": if lit_supported, the KIND of source (e.g. "AAAS Project 2061", "Driver et al. children's ideas",
  "HBCSE study"); never invent a paper title, author list or URL. Use null if plausible.
- Misconceptions under one concept must be clearly different from each other (different root ideas).
- Do not copy sentences from NCERT textbooks. Write everything in your own words.

Return only JSON in exactly this shape:
{{"concepts": [{{"key": "c1", "name": "...", "prereqs": [], "misconceptions": [
   {{"statement": "...", "why": "...", "fix": "...", "probe": {{"question": "...", "wrong_answer": "..."}},
     "error_type": "...", "trigger_cues": ["..."], "confidence": "...", "source_hint": null}}]}}],
 "requires_topics": ["titles of earlier topics a student should know first"]}}
"""


# ---- Gemini ---------------------------------------------------------------------------------------------
def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    env = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            m = re.match(r"\s*(GEMINI_API_KEY|GOOGLE_API_KEY)\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                key = m.group(2)
    if not key:
        sys.exit("No Gemini key: put GEMINI_API_KEY=... in a .env file at the repo root (it is git-ignored).")
    return key


def _request(url: str, body: dict | None, key: str, timeout: float = 180) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET",
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def list_models(key: str) -> list[str]:
    out = _request(f"{API}/models?pageSize=200", None, key)
    return [m["name"].split("/", 1)[1] for m in out.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])]


def generate(key: str, model: str, prompt: str, retries: int = 4) -> tuple[str, dict]:
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3, "maxOutputTokens": 16384}}
    last = None
    for attempt in range(retries + 1):
        try:
            out = _request(f"{API}/models/{model}:generateContent", body, key)
            parts = out["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts if not p.get("thought")), out.get("usageMetadata", {})
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:300]!r}"
            if e.code not in (429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError) as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(min(60, 4 * 2 ** attempt))
    raise RuntimeError(last)


# ---- validation -----------------------------------------------------------------------------------------
def validate_topic(topic: dict, data: dict) -> tuple[list[dict], list[str]]:
    """Return clean concepts (with clean misconceptions) and a list of problems found."""
    problems, concepts = [], []
    allowed = set(ERROR_TYPES[topic["subject"]])
    raw = data.get("concepts") or []
    keys = [str(c.get("key", f"c{i + 1}")) for i, c in enumerate(raw)]
    for i, c in enumerate(raw):
        name = str(c.get("name", "")).strip()
        if not name:
            problems.append(f"concept {i + 1}: no name")
            continue
        prereqs = [str(p) for p in (c.get("prereqs") or []) if str(p) in keys[:i]]  # only earlier concepts: no cycles
        mis = []
        for m in c.get("misconceptions") or []:
            st = str(m.get("statement", "")).strip()
            fix = str(m.get("fix", "")).strip()
            n = len(st.split())
            if not (3 <= n <= 35) or not fix:  # 3: "Fish breathe water." is a real, well-known misconception
                problems.append(f"{name}: dropped misconception {st[:50]!r} (length {n} words or no fix)")
                continue
            if re.search(r"\b(students?|learners?|children)\b.*\b(do not|don't|fail to|confuse)\b", st, re.I):
                problems.append(f"{name}: dropped vague statement {st[:60]!r}")
                continue
            et = str(m.get("error_type", "other"))
            probe = m.get("probe") if isinstance(m.get("probe"), dict) else {}
            mis.append({"statement": st, "why": str(m.get("why", "")).strip(), "fix": fix,
                        "probe": {"question": str(probe.get("question", "")).strip(),
                                  "wrong_answer": str(probe.get("wrong_answer", "")).strip()},
                        "error_type": et if et in allowed else "other",
                        "trigger_cues": [str(t).lower().strip() for t in (m.get("trigger_cues") or []) if str(t).strip()][:8],
                        "confidence": "lit_supported" if m.get("confidence") == "lit_supported" else "plausible",
                        "source_hint": (str(m["source_hint"]).strip() or None) if m.get("source_hint") else None})
        if not mis:
            problems.append(f"{name}: no usable misconceptions")
        concepts.append({"key": keys[i], "name": name, "prereqs": prereqs, "misconceptions": mis})
    if not 2 <= len(concepts) <= 8:
        problems.append(f"{len(concepts)} concepts (expected 3-6)")
    return concepts, problems


_STOP = set("a an the of to in on and or is are be it its for with that this as by from at into than they their "
            "them can will only always never all any some do does".split())


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP}


def jaccard(a: str, b: str) -> float:
    x, y = _tokens(a), _tokens(b)
    return len(x & y) / len(x | y) if x and y else 0.0


# ---- commands -------------------------------------------------------------------------------------------
def load_topics() -> list[dict]:
    with open(os.path.join(DIR, "topics.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cmd_generate(args) -> int:
    key = api_key()
    topics = [t for t in load_topics() if not args.only or t["id"] in args.only]
    os.makedirs(os.path.join(DIR, "raw"), exist_ok=True)
    todo = [t for t in topics if args.force or not os.path.exists(os.path.join(DIR, "raw", t["id"] + ".json"))]
    print(f"{len(todo)} of {len(topics)} topics to generate with {args.model}", flush=True)

    def one(t: dict) -> str:
        prompt = PROMPT.format(grades="/".join(map(str, t["grades"])), title=t["title"], subject=t["subject"],
                               strand=t["strand"], scope=t["scope"], error_types=", ".join(ERROR_TYPES[t["subject"]]))
        t0 = time.time()
        text, usage = generate(key, args.model, prompt)
        data = json.loads(text)  # raises on broken JSON: the topic is retried on the next run
        concepts, problems = validate_topic(t, data)
        n = sum(len(c["misconceptions"]) for c in concepts)
        with open(os.path.join(DIR, "raw", t["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump({"topic": t, "model": args.model, "usage": usage, "seconds": round(time.time() - t0, 1),
                       "response": data, "problems": problems}, f, indent=1, ensure_ascii=False)
        return f"{t['id']:<26} {len(concepts)} concepts, {n} misconceptions, {len(problems)} problems, {time.time() - t0:.0f}s"

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one, t): t for t in todo}
        for fut in cf.as_completed(futures):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001  (report and carry on; rerun picks it up)
                failed += 1
                print(f"{futures[fut]['id']:<26} FAILED: {e}", flush=True)
    print(f"done; {failed} failed (rerun the same command to retry them)")
    return 1 if failed else 0


def cmd_assemble(args) -> int:
    topics = {t["id"]: t for t in load_topics()}
    lib, concepts_out, problems_all = [], [], {}
    usage_in = usage_out = 0
    for tid, t in topics.items():
        path = os.path.join(DIR, "raw", tid + ".json")
        if not os.path.exists(path):
            problems_all[tid] = ["not generated yet"]
            continue
        raw = json.load(open(path, encoding="utf-8"))
        usage_in += raw.get("usage", {}).get("promptTokenCount", 0)
        usage_out += raw.get("usage", {}).get("candidatesTokenCount", 0)
        concepts, problems = validate_topic(t, raw["response"])
        if problems:
            problems_all[tid] = problems
        key_to_id = {c["key"]: f"{tid}-C{i + 1}" for i, c in enumerate(concepts)}
        for i, c in enumerate(concepts):
            cid = key_to_id[c["key"]]
            mids = []
            for k, m in enumerate(c["misconceptions"]):
                mid = f"{cid}M{k + 1}"
                held = int(hashlib.sha1(mid.encode()).hexdigest(), 16) % 100 < HELD_OUT_PERCENT
                lib.append({"id": mid, "topic_id": tid, "subject": t["subject"], "strand": t["strand"],
                            "grades": t["grades"], "topic": t["title"], "concept_id": cid, "concept": c["name"],
                            **m, "source": "teacher_generated", "teacher_model": raw.get("model"),
                            "held_out": held, "duplicate_of": None})
                mids.append(mid)
            concepts_out.append({"id": cid, "topic_id": tid, "topic": t["title"], "name": c["name"],
                                 "prereqs": [key_to_id[p] for p in c["prereqs"] if p in key_to_id],
                                 "misconceptions": mids, "requires_topics": raw["response"].get("requires_topics", [])})

    # Near-duplicate statements across the whole library: keep the first, mark the rest.
    kept: list[dict] = []
    for m in lib:
        twin = next((k for k in kept if jaccard(k["statement"], m["statement"]) >= args.dup), None)
        if twin:
            m["duplicate_of"] = twin["id"]
        else:
            kept.append(m)

    with open(os.path.join(DIR, "library.jsonl"), "w", encoding="utf-8") as f:
        for m in lib:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    with open(os.path.join(DIR, "concepts.jsonl"), "w", encoding="utf-8") as f:
        for c in concepts_out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    rng = random.Random(14)
    sample = rng.sample(kept, max(1, len(kept) // 10)) if kept else []
    with open(os.path.join(DIR, "review.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "topic", "concept", "statement", "fix", "probe_question", "probe_wrong_answer",
                    "confidence", "verdict (ok/fix/drop)", "note"])
        for m in sorted(sample, key=lambda x: x["id"]):
            w.writerow([m["id"], m["topic"], m["concept"], m["statement"], m["fix"], m["probe"]["question"],
                        m["probe"]["wrong_answer"], m["confidence"], "", ""])

    from collections import Counter
    stats = {"topics": len(topics), "topics_generated": len({m["topic_id"] for m in lib}),
             "concepts": len(concepts_out), "misconceptions": len(lib), "unique": len(kept),
             "duplicates": len(lib) - len(kept), "held_out": sum(m["held_out"] for m in kept),
             "by_strand": dict(Counter(m["strand"] for m in kept)),
             "confidence": dict(Counter(m["confidence"] for m in kept)),
             "error_types": dict(Counter(m["error_type"] for m in kept).most_common()),
             "teacher_tokens": {"in": usage_in, "out": usage_out}, "review_sample": len(sample),
             "topics_with_problems": {k: v for k, v in problems_all.items()}}
    with open(os.path.join(DIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps({k: v for k, v in stats.items() if k != "topics_with_problems"}, indent=2))
    print(f"{len(problems_all)} topics with notes (see stats.json)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-models", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("--model", default=DEFAULT_MODEL)
    g.add_argument("--only", nargs="*", help="topic ids to (re)generate")
    g.add_argument("--workers", type=int, default=6)
    g.add_argument("--force", action="store_true", help="regenerate topics that already have an answer")
    a = sub.add_parser("assemble")
    a.add_argument("--dup", type=float, default=0.75, help="word-overlap ratio at which two statements count as duplicates")
    args = ap.parse_args()
    if args.list_models:
        print("\n".join(list_models(api_key())))
        return 0
    if args.cmd == "generate":
        return cmd_generate(args)
    if args.cmd == "assemble":
        return cmd_assemble(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
