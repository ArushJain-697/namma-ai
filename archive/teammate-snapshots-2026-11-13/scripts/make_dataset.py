#!/usr/bin/env python3
"""Make the fine-tuning dataset and the 200-passage test set for diagnostic questions, with a Gemini teacher.

  python scripts/make_dataset.py generate --split train --n 800     # teacher writes passages + 4 questions each
  python scripts/make_dataset.py generate --split test  --n 160
  python scripts/make_dataset.py build                              # filter + write the training files

Needs the misconception graph (data/misconceptions/library.jsonl, concepts.jsonl) and GEMINI_API_KEY in .env.
Fairness: ~12% of topics are TEST-ONLY (never in training), and misconceptions flagged held_out in the library
never appear in training menus. The 40 hand-written eval passages are added to the test set as they are.

Writes data/dataset/:
  raw/{train,test}/JOB.json      one teacher answer per job (reruns skip finished jobs)
  train.jsonl, val.jsonl         chat examples {"messages": [system, user, assistant]} in the exact device format
  test_passages.jsonl            200 passages {id, text, topic_id, split_reason, reference_items}
  stats.json
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import re
import sys
import threading
import time
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_misconception_library as v1  # noqa: E402
from sakshi.diagnostic import (LABELS, build_messages, check_item, target_json, build_quiz_messages,  # noqa: E402
                               check_quiz_item, choose_beliefs, quiz_target_json, QUIZ_MAX_BELIEFS)

DD = os.path.join(ROOT, "data", "dataset")
DD2 = os.path.join(ROOT, "data", "dataset_v2")
MIS = os.path.join(ROOT, "data", "misconceptions")
TEST_TOPIC_PERCENT = 12
MODELS = ["gemini-3-flash-preview", "gemini-3.1-flash-lite", "claude:claude-sonnet-5-5", "claude:sonnet"]  # on a daily-quota error, move to the next one

STYLES = {
    "default": ["a clear textbook explanation", "a short story with Indian characters in everyday life",
                "a description of a classroom activity or experiment and what it shows",
                "a conversation between a teacher and two students", "a news-style report about a real-world situation",
                "a step-by-step explanation of a process", "a comparison of two related ideas",
                "a passage rich in numbers, dates or measurements", "a cause-and-effect explanation",
                "a passage that starts from a common wrong idea and corrects it", "a diary entry or letter by a student",
                "a question-and-answer (FAQ) style passage"],
    "maths": ["a clear textbook explanation with one worked example", "a short story where children solve a real problem",
              "a market or shop situation that uses the idea", "a conversation between a teacher and two students",
              "a rule explained with two contrasting examples", "a passage that shows a common wrong method and corrects it",
              "a step-by-step worked example", "a puzzle or game that uses the idea"],
}

PROMPT = """You are an expert Indian school teacher and assessment designer (diagnostic questions in the style of
Eedi and Dylan Wiliam's hinge questions). Create ONE training example for a small offline tutor model.

Class {grade} | Subject: {subject} | Topic: {topic}
Key concepts of the topic: {concepts}
Known student misconceptions for this topic (id: belief | example wrong answer):
{menu}

1. "passage": write an ORIGINAL passage of 170 to 270 words for a Class {grade} student, as {style}.
   It must be factually correct by the NCERT syllabus, self-contained, in simple English, and must contain the
   facts needed to correct several of the misconceptions above. Do not copy NCERT text.
2. "summary": 2 or 3 simple sentences summarising the passage.
3. "items": exactly 4 diagnostic multiple-choice questions, each on a DIFFERENT sentence of the passage:
   - "evidence": one sentence copied EXACTLY, word for word, from your passage, that proves the answer;
   - "answer": the correct answer, a short phrase (1 to 8 words) taken from the evidence sentence;
   - "stem": the question (ends with "?", at most 25 words); it must NOT contain the answer words;
     prefer "why/what happens/which" questions that a misconception would get wrong, not trivial recall;
   - "options": exactly 3 wrong options, each built from a DIFFERENT misconception id from the list above:
     {{"belief_id": "...", "why": "how that belief leads to this answer, at most 12 words",
      "text": "the wrong answer a student holding that belief would choose"}};
     wrong options must be plausible, similar in length and grammar to the answer, and clearly wrong according
     to the passage. Never "all/none of the above". Never a second correct answer.
Return only JSON: {{"passage": "...", "summary": "...", "items": [{{"evidence": "...", "answer": "...",
"stem": "...", "options": [{{"belief_id": "...", "why": "...", "text": "..."}}]}}]}}
"""

GENERIC_SHARE = 0.18  # share of training jobs that use the generic reading-skill menu
OFF_THEMES_TRAIN = [
    "a school sports day", "a village fair", "making a kite for Makar Sankranti", "a train journey across India",
    "a visit to a zoo", "a family wedding", "a cricket match between two schools", "learning to ride a bicycle",
    "the life of a famous Indian scientist", "a local handloom weaver", "a monsoon trek in the Western Ghats",
    "a school science exhibition", "a street food stall", "the history of a famous fort", "a day in a fishing village",
    "a pet dog adopted from a shelter", "a chess tournament", "a classical dance performance", "a farmer's market",
    "a library that runs on donations", "a robotics club", "a folk tale retold", "an old lighthouse", "a hockey legend",
    "a bird-watching walk", "a festival of lights in a town", "a museum of old coins", "a pottery workshop",
    "a story about a lost umbrella", "a recipe for a regional dish"]
OFF_THEMES_TEST = [
    "a kabaddi championship", "a boat race in Kerala", "a desert camel fair", "a puppet show", "a tea garden in Assam",
    "a newspaper delivery boy's morning", "an annual school play", "a temple elephant festival", "a spice market",
    "a mountain railway", "a rangoli competition", "a carpenter's workshop", "a book fair", "a rescued street cat",
    "a lighthouse keeper's diary", "a marathon in the city", "a weaving cooperative", "a stargazing night",
    "a grandmother's recipe book", "a flood relief camp run by students"]

_model_lock = threading.Lock()
_model_idx = [0]


def generic_beliefs(lib) -> list[dict]:
    return [m for m in lib if m.get("subject") == "reading_skill"]


def load_library():
    lib = [json.loads(l) for l in open(os.path.join(MIS, "library.jsonl"), encoding="utf-8")]
    concepts = [json.loads(l) for l in open(os.path.join(MIS, "concepts.jsonl"), encoding="utf-8")]
    return lib, concepts


def test_topics(topic_ids) -> set[str]:
    return {t for t in topic_ids if int(hashlib.sha1(t.encode()).hexdigest(), 16) % 100 < TEST_TOPIC_PERCENT}


def plan_jobs(split: str, n: int, lib, topics) -> list[dict]:
    by_topic = defaultdict(list)
    for m in lib:
        if not m.get("duplicate_of") and m.get("subject") != "reading_skill":
            by_topic[m["topic_id"]].append(m)
    ids = sorted(t for t in topics if len(by_topic.get(t, [])) >= 3)
    tt = test_topics(ids)
    if split == "train":
        pool = [t for t in ids if t not in tt]
    else:  # test: half on test-only topics, half new passages on training topics
        pool = sorted(tt) + [t for t in ids if t not in tt]
    rng = random.Random(f"{split}-plan")
    jobs = []
    n_generic = round(n * GENERIC_SHARE) if split == "train" else 20
    n = n - n_generic
    per = math.ceil(n / max(1, len(pool))) if split == "train" else 1
    order = pool * per if split == "train" else (sorted(tt) * math.ceil((n // 2) / max(1, len(tt))))[: n // 2] + \
        rng.sample([t for t in ids if t not in tt], min(n - n // 2, len(ids) - len(tt)))
    for k, tid in enumerate(order[:n]):
        t = topics[tid]
        styles = STYLES["maths" if t["subject"] == "maths" else "default"]
        jobs.append({"job": f"{split}-{k:04d}-{tid}", "topic_id": tid, "split": split,
                     "test_only_topic": tid in tt, "grade": rng.choice(t["grades"]),
                     "style": styles[(k + rng.randrange(len(styles))) % len(styles)], "seed": k})
    # generic reading-skill jobs: off-syllabus themes (train and test lists differ) and, in training, some topics
    themes = OFF_THEMES_TRAIN if split == "train" else OFF_THEMES_TEST
    for g in range(n_generic):
        k = len(jobs)
        on_topic = split == "train" and g % 2 == 1
        tid = rng.choice(pool) if on_topic else None
        theme = topics[tid]["title"] if on_topic else themes[g % len(themes)]
        jobs.append({"job": f"{split}-{k:04d}-GENERIC-{re.sub('[^A-Za-z0-9]+', '_', theme)[:30]}", "topic_id": tid,
                     "split": split, "generic": True, "theme": theme, "test_only_topic": False,
                     "grade": rng.choice([6, 7, 8, 9, 10]), "style": rng.choice(STYLES["default"]), "seed": k})
    return jobs


def combos(keys: list[str]) -> list[tuple[str, str]]:
    """Try the strong model on every key before falling back to the light model."""
    return [(k, m) for m in MODELS for k in keys]


GENERIC_PROMPT = """You are an expert Indian school teacher and assessment designer. Create ONE training example for a
small offline tutor model, for a passage that is NOT about a school-syllabus topic, so the questions test careful
READING and REASONING rather than subject knowledge.

Class {grade} | Theme: {theme}
Reading/reasoning mistakes students make (id: belief | example wrong answer):
{menu}

1. "passage": write an ORIGINAL passage of 170 to 270 words for a Class {grade} student about {theme}, as {style}.
   Include several named people or places, at least two numbers or dates, and at least one cause-and-effect link,
   so that the mistakes above can be tested. Simple English, Indian context where natural.
2. "summary": 2 or 3 simple sentences summarising the passage.
3. "items": exactly 4 multiple-choice questions, each on a DIFFERENT sentence of the passage:
   - "evidence": one sentence copied EXACTLY, word for word, from your passage, that proves the answer;
   - "answer": the correct answer, a short phrase (1 to 8 words) taken from the evidence sentence;
   - "stem": the question (ends with "?", at most 25 words); it must NOT contain the answer words;
   - "options": exactly 3 wrong options, each built from a DIFFERENT mistake id from the list above, using details
     from the passage (for example a different person, number or reason that IS in the passage):
     {{"belief_id": "...", "why": "how that mistake leads to this answer, at most 12 words", "text": "..."}};
     plausible, similar in length and grammar to the answer, clearly wrong for this question. Never a second
     correct answer, never "all/none of the above".
Return only JSON: {{"passage": "...", "summary": "...", "items": [{{"evidence": "...", "answer": "...",
"stem": "...", "options": [{{"belief_id": "...", "why": "...", "text": "..."}}]}}]}}
"""


def run_job(job, teacher, lib, concepts, topics) -> str:
    if job.get("generic"):
        gb = generic_beliefs(lib)
        menu = "\n".join(f"{m['id']}: {m['statement']} | {m.get('probe', {}).get('wrong_answer', '')}" for m in gb)
        prompt = GENERIC_PROMPT.format(grade=job["grade"], theme=job["theme"], menu=menu, style=job["style"])
        t0 = time.time()
        text, usage, model = teacher.generate(prompt)
        data = v1.loads_lenient(text)
        with open(os.path.join(DD, "raw", job["split"], job["job"] + ".json"), "w", encoding="utf-8") as f:
            json.dump({"job": job, "model": model, "usage": usage, "menu_ids": [m["id"] for m in gb], "response": data,
                       "seconds": round(time.time() - t0, 1)}, f, indent=1, ensure_ascii=False)
        return f"{job['job']:<40} {model:<24} {len(data.get('items', []))} items {time.time() - t0:.0f}s"
    t = topics[job["topic_id"]]
    rng = random.Random(job["seed"])
    ms = [m for m in lib if m["topic_id"] == job["topic_id"] and not m.get("duplicate_of")
          and (job["split"] == "test" or not m.get("held_out"))]
    rng.shuffle(ms)
    ms = ms[:14]
    menu = "\n".join(f"{m['id']}: {m['statement']} | {m.get('probe', {}).get('wrong_answer', '')}" for m in ms)
    cnames = ", ".join(c["name"] for c in concepts if c["topic_id"] == job["topic_id"] and c.get("level", 1) <= 2)[:900]
    prompt = PROMPT.format(grade=job["grade"], subject=t["subject"], topic=t["title"], concepts=cnames, menu=menu,
                           style=job["style"])
    t0 = time.time()
    text, usage, model = teacher.generate(prompt)
    data = v1.loads_lenient(text)
    path = os.path.join(DD, "raw", job["split"], job["job"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"job": job, "model": model, "usage": usage, "menu_ids": [m["id"] for m in ms], "response": data,
                   "seconds": round(time.time() - t0, 1)}, f, indent=1, ensure_ascii=False)
    return f"{job['job']:<40} {model:<24} {len(data.get('items', []))} items {time.time() - t0:.0f}s"


def cmd_generate(args) -> int:
    teacher = v1.Teacher(args.models.split(",") if args.models else MODELS)
    print("teacher order:", teacher.describe(), flush=True)
    lib, concepts = load_library()
    topics = {t["id"]: t for t in v1.load_topics()}
    os.makedirs(os.path.join(DD, "raw", args.split), exist_ok=True)
    jobs = plan_jobs(args.split, args.n, lib, topics)
    def path(j):
        return os.path.join(DD, "raw", args.split, j["job"] + ".json")

    def teacher_of(j):
        try:
            return json.load(open(path(j), encoding="utf-8")).get("model", "")
        except (OSError, json.JSONDecodeError):
            return ""
    todo = [j for j in jobs if not os.path.exists(path(j))]
    if args.redo_teacher:  # re-write jobs a weaker teacher made (old answer kept in raw_replaced/)
        redo = [j for j in jobs if os.path.exists(path(j)) and teacher_of(j).startswith(args.redo_teacher)]
        rng = random.Random(21)
        rng.shuffle(redo)
        redo = redo[: args.max_jobs] if args.max_jobs else redo
        bak = os.path.join(DD, "raw_replaced", args.split)
        os.makedirs(bak, exist_ok=True)
        for j in redo:
            os.replace(path(j), os.path.join(bak, j["job"] + ".json"))
        print(f"redoing {len(redo)} jobs written by {args.redo_teacher}", flush=True)
        todo += redo
    print(f"{len(todo)} of {len(jobs)} {args.split} jobs to run", flush=True)
    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_job, j, teacher, lib, concepts, topics): j for j in todo}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"{futs[fut]['job']:<40} FAILED: {str(e)[:150]}", flush=True)
                if "out of quota" in str(e):
                    break
    print(f"done; {failed} failed (rerun to retry)")
    return 0


# ---- build ----------------------------------------------------------------------------------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[“”]", '"', s.replace("’", "'"))).strip().lower()


def convert(raw: dict, lib_by_id: dict, topic_ms: list[dict], allow_held_out: bool, rng: random.Random):
    """Teacher answer -> (accepted training examples, rejection reasons)."""
    d = raw["response"]
    passage = str(d.get("passage", "")).strip()
    out, why = [], Counter()
    n_words = len(passage.split())
    if not 150 <= n_words <= 300:
        why["passage not 150-300 words"] += 1
        return out, why, passage
    for it in d.get("items", []) or []:
        ev = str(it.get("evidence", "")).strip()
        if not ev or _norm(ev) not in _norm(passage):
            why["evidence not copied from passage"] += 1
            continue
        used = [str(o.get("belief_id", "")) for o in it.get("options", []) or []]
        if len(used) != 3 or len(set(used)) != 3 or any(u not in lib_by_id for u in used):
            why["options not tied to 3 known misconceptions"] += 1
            continue
        if not allow_held_out and any(lib_by_id[u].get("held_out") for u in used):
            why["uses a held-out misconception"] += 1
            continue
        extra = [m for m in topic_ms if m["id"] not in used and (allow_held_out or not m.get("held_out"))]
        menu = [lib_by_id[u] for u in used] + rng.sample(extra, min(2, len(extra)))
        rng.shuffle(menu)
        label = {m["id"]: LABELS[i] for i, m in enumerate(menu)}
        options = [{"b": label[o["belief_id"]], "why": str(o.get("why", "")).strip(), "text": str(o.get("text", "")).strip()}
                   for o in it["options"]]
        item = {"answer": str(it.get("answer", "")).strip(), "stem": str(it.get("stem", "")).strip(), "options": options}
        chk = check_item(item, passage, ev, len(menu))
        if not chk.ok:
            for r in chk.reasons:
                why[r.split(":")[0]] += 1
            continue
        msgs = build_messages(passage, ev, [m["statement"] for m in menu])
        msgs.append({"role": "assistant", "content": target_json(item["answer"], item["stem"], options)})
        out.append({"messages": msgs, "meta": {"job": raw["job"]["job"], "topic_id": raw["job"]["topic_id"],
                                               "teacher": raw.get("model"), "beliefs": [m["id"] for m in menu]}})
    return out, why, passage


def cmd_build(args) -> int:
    lib, _ = load_library()
    lib_by_id = {m["id"]: m for m in lib}
    by_topic = defaultdict(list)
    for m in lib:
        if not m.get("duplicate_of") and m.get("subject") != "reading_skill":
            by_topic[m["topic_id"]].append(m)
    rng = random.Random(7)
    stats = {"train": Counter(), "test": Counter()}
    rejects = Counter()
    examples, seen_passages = [], []
    for f in sorted(os.listdir(os.path.join(DD, "raw", "train"))) if os.path.isdir(os.path.join(DD, "raw", "train")) else []:
        raw = json.load(open(os.path.join(DD, "raw", "train", f), encoding="utf-8"))
        tms = generic_beliefs(lib) if raw["job"].get("generic") else by_topic[raw["job"]["topic_id"]]
        ex, why, passage = convert(raw, lib_by_id, tms, False, rng)
        rejects.update(why)
        stats["train"]["generic_examples" if raw["job"].get("generic") else "topic_examples"] += len(ex)
        stats["train"]["passages"] += 1
        stats["train"]["items_in"] += len(raw["response"].get("items", []) or [])
        examples += ex
        seen_passages.append(passage)
    stats["train"]["examples"] = len(examples)
    # validation: 5% of passages (whole passages, so no leakage between train and val)
    jobs = sorted({e["meta"]["job"] for e in examples})
    val_jobs = set(random.Random(3).sample(jobs, max(1, len(jobs) // 20))) if jobs else set()
    os.makedirs(DD, exist_ok=True)
    with open(os.path.join(DD, "train.jsonl"), "w", encoding="utf-8") as ft, \
            open(os.path.join(DD, "val.jsonl"), "w", encoding="utf-8") as fv:
        for e in examples:
            (fv if e["meta"]["job"] in val_jobs else ft).write(json.dumps(e, ensure_ascii=False) + "\n")
    stats["train"]["val_examples"] = sum(1 for e in examples if e["meta"]["job"] in val_jobs)

    # test passages: teacher-written test jobs + the 40 hand-written eval passages
    tests = []
    tdir = os.path.join(DD, "raw", "test")
    for f in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
        raw = json.load(open(os.path.join(tdir, f), encoding="utf-8"))
        generic = raw["job"].get("generic")
        tms = generic_beliefs(lib) if generic else by_topic[raw["job"]["topic_id"]]
        ex, why, passage = convert(raw, lib_by_id, tms, True, rng)
        if not 150 <= len(passage.split()) <= 300:
            continue
        tests.append({"id": raw["job"]["job"], "text": passage, "topic_id": raw["job"]["topic_id"],
                      "split_reason": "off-syllabus (generic)" if generic else
                      ("test-only topic" if raw["job"]["test_only_topic"] else "new passage, training topic"),
                      "style": raw["job"]["style"], "grade": raw["job"]["grade"],
                      "reference_items": [json.loads(e["messages"][-1]["content"]) | {"beliefs": e["meta"]["beliefs"]}
                                          for e in ex]})
    expected = json.load(open(os.path.join(ROOT, "data/passages/eval/expected_topics.json"), encoding="utf-8"))
    for line in open(os.path.join(ROOT, "data/passages/eval/passages.jsonl"), encoding="utf-8"):
        p = json.loads(line)
        tests.append({"id": "eval40-" + p["id"], "text": p["text"], "topic_id": expected.get(p["id"], [None])[0],
                      "split_reason": "hand-written eval passage", "style": p.get("style"), "grade": p.get("class"),
                      "reference_items": []})
    with open(os.path.join(DD, "test_passages.jsonl"), "w", encoding="utf-8") as f:
        for t in tests:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    stats["test"]["passages"] = len(tests)
    stats["test"]["by_reason"] = dict(Counter(t["split_reason"] for t in tests))
    out = {"train": dict(stats["train"]), "test": dict(stats["test"]), "rejected_items": dict(rejects.most_common()),
           "teachers": dict(Counter(e["meta"]["teacher"] for e in examples)),
           "topics_in_train": len({e["meta"]["topic_id"] for e in examples}),
           "subjects_in_train": dict(Counter((e["meta"]["topic_id"] or "OFFSYLLABUS-").split("-")[0] for e in examples))}
    with open(os.path.join(DD, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return 0


# ---- v2: Opus rewrites the questions of the 800 training passages (QUESTION_QUALITY_HANDOFF.md, job 3) ------
def _rubric_text() -> str:
    t = open(os.path.join(ROOT, "docs", "QUESTION_RUBRIC.md"), encoding="utf-8").read()
    start, end = t.find("## Hard rules"), t.find("## Score")
    return t[start:end].strip() if start >= 0 and end > start else t


def _gold_text() -> str:
    lines = []
    for line in open(os.path.join(ROOT, "data", "gold_questions.jsonl"), encoding="utf-8"):
        g = json.loads(line)
        lines.append(json.dumps({"evidence": g["evidence"], "kind": g["kind"], "q": g["q"], "options": g["options"],
                                 "explain": g["explain"], "wrong": [{"misconception": w["misconception"], "why": w["why"]}
                                                                    for w in g["wrong"]]}, ensure_ascii=False))
    return "\n".join(lines)


# Identical in every call (rubric + 20 gold examples first), so prompt caching can reuse it.
REWRITE_PREFIX = """You are an expert Indian school teacher and assessment designer. You write multiple-choice questions
that will train a tiny offline tutor model (Qwen3-0.6B) for Class 6-10 students. Quality matters more than anything.

RUBRIC (every question must pass every hard rule):
{rubric}

GOLD EXAMPLES (the quality bar; each line is one question; the correct option is ALWAYS listed first, code shuffles
the order later; "wrong" gives, for each of the 3 wrong options in order, the misconception id it comes from, or
null for a reading mistake, and why a student would choose it):
{gold}
"""

REWRITE_TASK = """
NOW YOUR TASK. Class {grade} | Topic: {topic}
Known student misconceptions for this topic (id: belief):
{menu}

PASSAGE:
{passage}

Write {n} questions on this passage, each on a DIFFERENT sentence, testing DIFFERENT ideas. At most one may be plain
recall. Prefer why / how / what happens if / which explains / which example shows. Correct option FIRST. KEEP IT
SHORT (the tiny model must write it in under ~110 tokens): question at most 20 words, each option at most 9 words,
explanation at most 18 words. Each wrong
option should come from a DIFFERENT misconception id above where one fits (else null), be clearly wrong by the
passage, and match the correct option in length, grammar and style. The evidence sentence must be copied word for
word from the passage.
AVOID THESE GIVEAWAYS (a strict grader rejects them):
- the correct option is the only one that reuses the passage's wording: paraphrase the answer, and let some wrong
  options reuse passage words too (e.g. a nearby detail or a reversed cause);
- the correct option is the odd one out in form: all four options must start the same way and have the same
  structure (never three "No, ..." and one "Yes, ..."; never one "To ..." among three "Because ...");
- a key word of the question appears in only one option;
- a wrong option that needs outside knowledge to rule out, or that nobody would believe: every wrong option must
  be clearly wrong BY THE PASSAGE, yet tempting to a student holding that misconception.
Return only JSON:
{{"items": [{{"evidence": "...", "kind": "why|how|what_if|which_explains|which_example|difference|recall",
"q": "...?", "options": ["correct", "wrong", "wrong", "wrong"], "explain": "...",
"wrong": [{{"misconception": "id or null", "why": "..."}}, {{...}}, {{...}}]}}]}}
"""


def _menu_for(raw: dict, lib) -> list[dict]:
    if raw["job"].get("generic"):
        return generic_beliefs(lib)
    return [m for m in lib if m["topic_id"] == raw["job"]["topic_id"] and not m.get("duplicate_of")
            and not m.get("held_out")]


def cmd_rewrite(args) -> int:
    from build_misconception_library import claude_generate
    model = args.teacher.split(":", 1)[1] if args.teacher.startswith("claude:") else args.teacher
    lib, _ = load_library()
    topics = {t["id"]: t for t in v1.load_topics()}
    prefix = REWRITE_PREFIX.format(rubric=_rubric_text(), gold=_gold_text())
    out_dir = os.path.join(DD2, "raw")
    os.makedirs(out_dir, exist_ok=True)
    src = sorted(f for f in os.listdir(os.path.join(DD, "raw", "train")) if f.endswith(".json"))
    todo = [f for f in src if not os.path.exists(os.path.join(out_dir, f))][: args.limit]
    if args.total:  # stop at N passages in all, spread evenly over the list (topics and generic passages alike)
        need = max(0, args.total - (len(src) - len(todo) if not args.limit else len(src) - len(
            [f for f in src if not os.path.exists(os.path.join(out_dir, f))])))
        rest = [f for f in src if not os.path.exists(os.path.join(out_dir, f))]
        todo = [rest[int(i * len(rest) / need)] for i in range(need)] if need else []
    print(f"{len(todo)} of {len(src)} training passages to rewrite with {model}; {args.workers} workers", flush=True)
    stop = threading.Event()

    def one(f):
        if stop.is_set():
            return f"{f:<48} skipped (stopping)"
        raw = json.load(open(os.path.join(DD, "raw", "train", f), encoding="utf-8"))
        passage = str(raw["response"].get("passage", "")).strip()
        menu = _menu_for(raw, lib)[:14]
        j = raw["job"]
        topic = j.get("theme") if j.get("generic") else topics.get(j["topic_id"], {}).get("title", j["topic_id"])
        n = 5 if len(passage.split()) >= 200 else 4
        prompt = prefix + REWRITE_TASK.format(grade=j.get("grade", 8), topic=topic, n=n, passage=passage,
                                              menu="\n".join(f"{m['id']}: {m['statement']}" for m in menu))
        t0 = time.time()
        try:
            text, usage = claude_generate(prompt, model)
        except Exception as e:  # noqa: BLE001
            if "quota" in str(e).lower():
                stop.set()
            raise
        try:
            data = v1.loads_lenient(text)
        except Exception:  # noqa: BLE001
            data = {"items": [], "unparsed": text}
        tmp = os.path.join(out_dir, f + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"source": f, "job": j, "teacher": f"claude:{model}", "usage": usage, "passage": passage,
                       "menu_ids": [m["id"] for m in menu], "response": data, "seconds": round(time.time() - t0, 1)},
                      fh, indent=1, ensure_ascii=False)
        os.replace(tmp, os.path.join(out_dir, f))  # atomic: an interrupted call never leaves a half file
        return f"{f:<48} {len(data.get('items', []))} items {time.time() - t0:.0f}s"

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(one, f): f for f in todo}
        for fut in cf.as_completed(futs):
            try:
                print(fut.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"{futs[fut]:<48} FAILED: {str(e)[:160]}", flush=True)
    done = len([f for f in os.listdir(out_dir) if f.endswith(".json")])
    print(f"done: {done} of {len(src)} passages rewritten; {failed} failed this run"
          + ("; STOPPED on a usage limit, rerun the same command later to resume" if stop.is_set() else ""), flush=True)
    return 0


MAX_TARGET_TOKENS = 115  # device: max_new_tokens 120 (diagnostic.QUIZ_MAX_NEW_TOKENS); keep a margin
_TOK = []


def target_tokens(text: str) -> int:
    """Qwen3 token count (tokenizer from the Hugging Face cache if available; else ~4 characters per token)."""
    if not _TOK:
        try:
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
            _TOK.append(Tokenizer.from_file(hf_hub_download("Qwen/Qwen3-0.6B", "tokenizer.json")))
        except Exception:  # noqa: BLE001
            _TOK.append(None)
    return len(_TOK[0].encode(text).ids) if _TOK[0] else len(text) // 4


def build_v2_examples(rec: dict, lib_by_id: dict, topic_pool: list[dict], rng: random.Random, grades: dict | None = None,
                      min_score: int = 4) -> tuple[list[dict], Counter]:
    """One rewritten passage -> device-format training examples, keeping only items that pass the code checks
    and (when a grade file is given) the rubric grader."""
    out, why = [], Counter()
    passage = rec["passage"]
    for k, it in enumerate(rec["response"].get("items", []) or []):
        key = f"{rec['source']}#{k}"
        ev = str(it.get("evidence", "")).strip()
        opts = [str(o).strip() for o in it.get("options", []) or []]
        item = {"q": str(it.get("q", "")).strip(), "options": opts, "answer": 0, "explain": str(it.get("explain", "")).strip()}
        if _norm(ev) not in _norm(passage):
            why["evidence not copied from passage"] += 1
            continue
        chk = check_quiz_item(item, passage, ev, support=False)  # answer correctness: the grader's H3
        if not chk.ok:
            for r in chk.reasons:
                why["code: " + r.split("(")[0].split(":")[0].strip()] += 1
            continue
        if grades is not None:
            g = grades.get(key)
            if not g:
                why["not graded"] += 1
                continue
            if not g.get("hard_pass") or (g.get("score") or 0) < min_score:
                why[f"grader: score {g.get('score')} hard_pass {g.get('hard_pass')}"] += 1
                continue
        target = quiz_target_json(item["q"], opts, item["explain"])
        if target_tokens(target) > MAX_TARGET_TOKENS:
            why["answer longer than the device budget"] += 1
            continue
        mids = [w.get("misconception") for w in (it.get("wrong") or [])][:3]
        mapped = [lib_by_id[m] for m in mids if m and m in lib_by_id]
        # Device-like menu: the beliefs this question's wrong options use, topped up the way the device picks them.
        menu = list({m["id"]: m for m in mapped}.values())[:QUIZ_MAX_BELIEFS]
        if len(menu) < QUIZ_MAX_BELIEFS and topic_pool:
            extra = [m for m in choose_beliefs(ev, passage, topic_pool, 6) if m["id"] not in {x["id"] for x in menu}]
            menu += extra[: QUIZ_MAX_BELIEFS - len(menu)]
        rng.shuffle(menu)
        msgs = build_quiz_messages(passage, ev, [m["statement"] for m in menu])
        msgs.append({"role": "assistant", "content": quiz_target_json(item["q"], opts, item["explain"])})
        out.append({"messages": msgs, "meta": {"key": key, "job": rec["source"], "topic_id": rec["job"].get("topic_id"),
                                               "teacher": rec.get("teacher"), "kind": it.get("kind"),
                                               "wrong_misconceptions": mids, "beliefs": [m["id"] for m in menu]}})
    return out, why


def cmd_build_v2(args) -> int:
    lib, _ = load_library()
    lib_by_id = {m["id"]: m for m in lib}
    raw_dir = os.path.join(DD2, "raw")
    grades = None
    gpath = os.path.join(DD2, "grades.jsonl")
    if os.path.exists(gpath) and not args.ignore_grades:
        grades = {}
        for line in open(gpath, encoding="utf-8"):
            g = json.loads(line)
            grades[g["key"]] = g
    rng = random.Random(7)
    examples, why, n_items = [], Counter(), 0
    for f in sorted(x for x in os.listdir(raw_dir) if x.endswith(".json")):
        rec = json.load(open(os.path.join(raw_dir, f), encoding="utf-8"))
        n_items += len(rec["response"].get("items", []) or [])
        ex, w = build_v2_examples(rec, lib_by_id, _menu_for({"job": rec["job"]}, lib), rng, grades, args.min_score)
        examples += ex
        why.update(w)
    jobs = sorted({e["meta"]["job"] for e in examples})
    val_jobs = set(random.Random(3).sample(jobs, max(1, len(jobs) // 20))) if jobs else set()
    with open(os.path.join(DD2, "train.jsonl"), "w", encoding="utf-8") as ft, \
            open(os.path.join(DD2, "val.jsonl"), "w", encoding="utf-8") as fv:
        for e in examples:
            (fv if e["meta"]["job"] in val_jobs else ft).write(json.dumps(e, ensure_ascii=False) + "\n")
    stats = {"passages": len(jobs), "items_written_by_teacher": n_items, "examples_kept": len(examples),
             "val_examples": sum(e["meta"]["job"] in val_jobs for e in examples), "graded": grades is not None,
             "min_score": args.min_score, "rejected": dict(why.most_common()),
             "kinds": dict(Counter(e["meta"]["kind"] for e in examples))}
    json.dump(stats, open(os.path.join(DD2, "stats.json"), "w"), indent=2)
    print(json.dumps(stats, indent=2))
    for e in random.Random(11).sample(examples, min(args.show, len(examples))):
        print("\n---", e["meta"]["key"], e["meta"]["kind"], "\n" + e["messages"][-1]["content"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("generate")
    g.add_argument("--split", choices=["train", "test"], required=True)
    g.add_argument("--n", type=int, required=True)
    g.add_argument("--workers", type=int, default=2)
    g.add_argument("--models", help="comma-separated teacher order, e.g. claude:claude-sonnet-5-5,gemini-3.1-flash-lite")
    g.add_argument("--redo-teacher", help="regenerate jobs whose answer came from this teacher (prefix match)")
    g.add_argument("--max-jobs", type=int, help="with --redo-teacher: at most this many jobs per run")
    sub.add_parser("build")
    rw = sub.add_parser("rewrite", help="v2: the teacher rewrites questions for the 800 training passages")
    rw.add_argument("--teacher", default="claude:claude-opus-5-5")
    rw.add_argument("--workers", type=int, default=3)
    rw.add_argument("--limit", type=int)
    rw.add_argument("--total", type=int, help="aim for this many rewritten passages in all, spread evenly")
    b2 = sub.add_parser("build-v2", help="v2: checks + grades -> data/dataset_v2/train.jsonl, val.jsonl")
    b2.add_argument("--min-score", type=int, default=4)
    b2.add_argument("--ignore-grades", action="store_true")
    b2.add_argument("--show", type=int, default=10)
    args = ap.parse_args()
    if args.cmd == "generate":
        return cmd_generate(args)
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "rewrite":
        return cmd_rewrite(args)
    if args.cmd == "build-v2":
        return cmd_build_v2(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
