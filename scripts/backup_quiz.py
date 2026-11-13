"""Backup quiz for the demo, in case the fine-tuned model is late: the PLAIN Qwen3-0.6B, one call per question.

Method (evidence: Generate-Then-Validate, Wei et al., LAK 2026, arXiv 2512.10110: an un-tuned 2.7B model's
questions agreed with teachers' answer keys ~90% of the time after it (1) wrote question -> options -> answer in a
plain layout and (2) answered its own question, keeping only confident matches):
  1. code picks key sentences (content-rich, causal words preferred, spread across the passage);
  2. the model writes one question in a plain-text layout (small models break JSON far more than big ones,
     StructuredRAG arXiv 2408.11061), guided by 2 hand-written examples placed as earlier chat turns;
  3. code checks (rubric H2/H5/H6/H7: no fill-in-the-blank, no all/none-of-the-above, distinct options, no answer
     leak, short options);
  4. self-check: the model answers its own question with shuffled options; keep only if it picks the key.
  Up to 6 key sentences are tried to get 4 questions.

Two variants of what the model sees: "window" (key sentence plus its neighbours: short prompt, fast on the Pi)
and "passage" (the whole passage).

  .venv-ml/bin/python scripts/backup_quiz.py generate [--limit N]   -> results/backup_quiz/<variant>.jsonl
  .venv-ml/bin/python scripts/backup_quiz.py judge                  -> results/backup_quiz/judged.jsonl (Sonnet)
  .venv-ml/bin/python scripts/backup_quiz.py report                 -> results/backup_quiz/REPORT.md
  .venv-ml/bin/python scripts/backup_quiz.py demo PASSAGE.txt         one passage, v2, printed in the terminal

DECIDED 13 Nov: v2 = "hybrid_mis" is the demo backup (40 eval passages, Sonnet blind grade: 31/40 passages with >= 3
questions, key right 73%, sensible 19%, ~62 s per quiz on the Pi). v3 (reason cut from the passage): key 78% but
sensible 6% (answers read as recall, the key gives itself away). v4 (model rewrites each misconception into a wrong
answer for this question): options fit the question but some are also true, and 74-182 s per quiz on the Pi.
This file only reads src/ (it does not change the question-quality teammate's code).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from sakshi.text import split_sentences, tokens, STOPWORDS  # noqa: E402

OUT = ROOT / "results" / "backup_quiz"
MODEL = ROOT / "models" / "qwen3-0.6b-8da4w"
VARIANTS = ("window", "passage", "hybrid", "hybrid_mis", "v3", "v4")

SYSTEM = (
    "You write one multiple-choice question for a Class 6-10 student about the key sentence of a text.\n"
    "Rules: ask why or how, never a word to fill in. Exactly one option is correct and the text proves it. "
    "The three wrong options are mistakes a student could really make. All four options are short and about "
    "the same length. Never use 'all of the above' or 'none of the above'.\n"
    "Use exactly this layout: Question, A) B) C) D), Answer, Why."
)
EXAMPLES = (
    ("Text: During a storm, lightning and thunder are produced at the same moment. Light travels about 3,00,000 km "
     "every second, while sound travels only about 340 metres every second. That is why we see the flash first "
     "and hear the thunder a few seconds later.\n"
     "Key sentence: That is why we see the flash first and hear the thunder a few seconds later.",
     "Question: Why do we see lightning before we hear the thunder?\n"
     "A) Light travels much faster than sound\nB) Thunder is made a few seconds later\n"
     "C) Our eyes work faster than our ears\nD) Sound slows down in the rain\n"
     "Answer: A\nWhy: Both are made at the same moment, but light is far faster than sound, so it reaches us first."),
    ("Text: In Champaran, British planters forced farmers to grow indigo on part of their land. The planters paid "
     "very low prices, and farmers could not grow enough food for their families. In 1917 Gandhiji came to "
     "Champaran, listened to the farmers and led a peaceful protest against this system.\n"
     "Key sentence: The planters paid very low prices, and farmers could not grow enough food for their families.",
     "Question: Why were the farmers of Champaran unhappy about growing indigo?\n"
     "A) Indigo plants harmed their animals\nB) Gandhiji told them indigo spoils the soil\n"
     "C) They earned little and lost land for food\nD) They wanted to grow cotton instead\n"
     "Answer: C\nWhy: Planters paid very low prices, and indigo used land the farmers needed to grow food."),
)
CHECK_SYSTEM = "Answer the question using the text. Reply with one letter only."
CAUSAL = re.compile(r"\b(because|so|therefore|thus|due to|as a result|when|if|unless|helps?|causes?|leads? to|"
                    r"allows?|prevents?|makes?|means|unlike|while|instead|which is why|so that)\b", re.I)
BANNED = re.compile(r"\b(all|none|both) of the above\b|_{2,}|\bfill in\b|according to the passage", re.I)


def content(s: str) -> set[str]:
    return {t.lower() for t in tokens(s) if len(t) >= 3 and t.lower() not in STOPWORDS}


def pick_sentences(passage: str, k: int = 8) -> list[int]:
    """Indexes of up to k key sentences: content-rich, causal words preferred, not adjacent, in passage order."""
    sents = split_sentences(passage)
    scored = sorted(((len(content(s)) + (4 if CAUSAL.search(s) else 0), -i, i) for i, s in enumerate(sents)
                     if 8 <= len(tokens(s)) <= 40), reverse=True)
    picked: list[int] = []
    for _, _, i in scored:
        if all(abs(i - j) > 1 for j in picked):
            picked.append(i)
        if len(picked) == k:
            break
    # first the best 4 in passage order (spread), then the spares
    return sorted(picked[:4]) + picked[4:]


def window(sents: list[str], i: int) -> str:
    return " ".join(sents[max(0, i - 1): i + 2])


def parse(text: str) -> dict | None:
    q = re.search(r"Question:\s*(.+)", text)
    opts = {m.group(1): m.group(2).strip() for m in re.finditer(r"^\s*([ABCD])[).:]\s*(.+)$", text, re.M)}
    ans = re.search(r"Answer:\s*\(?([ABCD])\b", text)
    why = re.search(r"Why:\s*(.+)", text)
    if not (q and ans and len(opts) == 4):
        return None
    return {"q": q.group(1).strip(), "options": [opts[c] for c in "ABCD"], "answer": "ABCD".index(ans.group(1)),
            "explain": why.group(1).strip() if why else ""}


def code_check(item: dict) -> str | None:
    """None if it passes, else the reason."""
    q, opts, key = item["q"], item["options"], item["options"][item["answer"]]
    if BANNED.search(q) or any(BANNED.search(o) for o in opts):
        return "banned phrase (blank / all-none of the above)"
    if len({o.lower().strip(" .") for o in opts}) < 4:
        return "repeated option"
    if len(tokens(q)) > 30 or any(len(tokens(o)) > 14 for o in opts):
        return "too long"
    if any(len(tokens(o)) == 0 for o in opts):
        return "empty option"
    kc = content(key)
    if kc and len(kc & content(q)) / len(kc) >= 0.75:
        return "answer leaked in question"
    if re.search(r"\bnot\b", q, re.I) and re.search(r"\b(which|what)\b", q, re.I):
        return "NOT question"
    return None


class Model:
    def __init__(self, path: Path = MODEL):
        from sakshi.backends.executorch_backend import ExecuTorchBackend
        from sakshi.backends.base import chat_prompt
        self.b = ExecuTorchBackend(str(path / "model.pte"), str(path / "tokenizer.json"))
        self.chat = chat_prompt
        self.calls: list[dict] = []

    def run(self, system: str, user: str, max_new: int, examples=(), kind: str = "", prefix: str = "") -> str:
        """`prefix` is written for the model as the start of its answer, which it must continue (the
        incremental-completion trick from Generate-Then-Validate: steer the stem instead of hoping)."""
        r = self.b.generate(self.chat("qwen3", system, user, examples=examples) + prefix, max_new_tokens=max_new)
        self.calls.append({"kind": kind, "in": r.prompt_tokens, "out": r.new_tokens, "s": round(r.wall_s, 2)})
        return prefix + r.text


def self_check(m: Model, ctx: str, item: dict, rng: random.Random) -> tuple[bool, str]:
    order = list(range(4))
    rng.shuffle(order)
    user = f"Text: {ctx}\nQuestion: {item['q']}\n" + "\n".join(f"{c}) {item['options'][j]}"
                                                              for c, j in zip("ABCD", order))
    out = m.run(CHECK_SYSTEM, user, 4, kind="check")
    got = re.match(r"\s*\(?([ABCD])", out)
    picked = order["ABCD".index(got.group(1))] if got else -1
    return picked == item["answer"], (got.group(1) if got else out.strip()[:20])


def quiz(m: Model, passage: str, variant: str, n: int = 4, seed: int = 0) -> dict:
    rng = random.Random(seed)
    sents = split_sentences(passage)
    start = len(m.calls)
    kept, rejected = [], []
    for i in pick_sentences(passage):
        if len(kept) == n:
            break
        ev = sents[i]
        ctx = window(sents, i) if variant == "window" else passage
        stem = "How" if re.search(r"\b(by|through|using|steps?|process)\b", ev, re.I) and not CAUSAL.search(ev) else "Why"
        raw = m.run(SYSTEM, f"Text: {ctx}\nKey sentence: {ev}", 120, examples=EXAMPLES, kind="question",
                    prefix=f"Question: {stem}")
        item = parse(raw)
        rec = {"evidence": ev, "raw": raw}
        if item is None:
            rejected.append({**rec, "reason": "could not parse"})
            continue
        rec.update(item)
        why = code_check(item)
        if why:
            rejected.append({**rec, "reason": why})
            continue
        ok, said = self_check(m, window(sents, i), item, rng)
        if not ok:
            rejected.append({**rec, "reason": f"self-check failed (picked {said})"})
            continue
        kept.append(rec)
    calls = m.calls[start:]
    return {"kept": kept, "rejected": rejected, "calls": calls}


def pi_seconds(calls: list[dict], read: float = 60, write: float = 20) -> float:
    return round(sum(c["in"] / read + c["out"] / write for c in calls), 1)


def cmd_generate(a) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    passages = [json.loads(l) for l in open(ROOT / "data/passages/eval/passages.jsonl")][: a.limit]
    m = Model()
    from sakshi.misconceptions import Library
    lib = Library.load()
    beliefs = Beliefs(lib) if {"v3", "v4"} & set(a.variants) else None
    for v in a.variants:
        with open(OUT / f"{v}.jsonl", "w") as f:
            for p in passages:
                t = time.time()
                if v == "v3":
                    r = quiz_v3(m, p["text"], beliefs, lib)
                elif v == "v4":
                    r = quiz_v4(m, p["text"], beliefs, lib)
                elif v.startswith("hybrid"):
                    r = quiz_hybrid(m, p["text"], lib=lib if v == "hybrid_mis" else None)
                else:
                    r = quiz(m, p["text"], v)
                r.update(id=p["id"], subject=p["subject"], mac_s=round(time.time() - t, 1), pi_s=pi_seconds(r["calls"]))
                f.write(json.dumps(r) + "\n")
                f.flush()
                print(f"{v:8} {p['id']:20} kept {len(r['kept'])}/4  rejected {len(r['rejected'])}  "
                      f"mac {r['mac_s']}s  pi~{r['pi_s']}s", flush=True)


JUDGE = """You are grading quiz questions for Class 6-10 students against this rubric.

{rubric}

PASSAGE ({pid}):
{passage}

QUESTIONS (the marked key is what the quiz says is correct):
{questions}

For EACH question, independently decide which option the passage proves correct, then grade it. Return JSON:
{{"grades": [{{"n": <number>, "correct": "<A|B|C|D|none|two>", "score": <1-5>, "broken": ["H1", ...], "sensible": <true|false>, "note": "<= 15 words"}}]}}
"sensible" is a lower, practical bar than the rubric score: true when the key is correct, all four options are
grammatical and about the question's topic, and a student could not pick the answer just from its form or because
it is the only on-topic option. Misconception-based distractors are NOT required for "sensible"."""


def cmd_judge(a) -> None:
    from build_misconception_library import claude_generate, loads_lenient
    rubric = (ROOT / "docs/QUESTION_RUBRIC.md").read_text().split("## Good vs bad")[0]
    passages = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/passages/eval/passages.jsonl")}
    runs = {v: {json.loads(l)["id"]: json.loads(l) for l in open(OUT / f"{v}.jsonl")} for v in VARIANTS
            if (OUT / f"{v}.jsonl").exists()}
    done = set()
    jpath = OUT / "judged.jsonl"
    if jpath.exists():
        done = {json.loads(l)["id"] for l in open(jpath)}
    rng = random.Random(1)
    for pid in sorted(set().union(*[set(r) for r in runs.values()])):
        if pid in done:
            continue
        items = []  # blind: variants and kept/rejected mixed, shuffled
        for v, r in runs.items():
            for status in ("kept", "rejected"):
                for q in r.get(pid, {}).get(status, []):
                    if "options" in q:
                        items.append({"variant": v, "status": status, **q})
        rng.shuffle(items)
        text = "\n\n".join(f"{n}. {q['q']}\n" + "\n".join(f"   {c}) {o}" for c, o in zip("ABCD", q["options"]))
                           + f"\n   Key: {'ABCD'[q['answer']]}" for n, q in enumerate(items, 1))
        prompt = JUDGE.format(rubric=rubric, pid=pid, passage=passages[pid]["text"], questions=text)
        for attempt in range(3):
            try:
                out, _ = claude_generate(prompt, a.judge_model)
                grades = {g["n"]: g for g in loads_lenient(out)["grades"]}
                break
            except Exception as e:  # noqa: BLE001
                print(f"  judge retry {pid}: {e}", flush=True)
                if "429" in str(e):
                    sys.exit("judge model unavailable (limit); rerun later, finished passages are kept")
                time.sleep(10)
        else:
            continue
        for n, q in enumerate(items, 1):
            q["grade"] = grades.get(n, {})
        with open(jpath, "a") as f:
            f.write(json.dumps({"id": pid, "items": items}) + "\n")
        print(f"judged {pid}: {len(items)} questions", flush=True)


def cmd_report(a) -> None:
    judged = [json.loads(l) for l in open(OUT / "judged.jsonl")]
    runs = {v: [json.loads(l) for l in open(OUT / f"{v}.jsonl")] for v in VARIANTS if (OUT / f"{v}.jsonl").exists()}
    lines = ["# Backup quiz (plain Qwen3-0.6B, one call per question) on the 40 eval passages\n",
             f"Judge: Sonnet against docs/QUESTION_RUBRIC.md, blind to variant and to kept/rejected.\n",
             "| Variant | Passages with >= 3 questions | Questions shown | Key correct | Score >= 4 (good) | "
             "Score <= 2 (bad) | Pi time per quiz (est. 60/20 tok/s), median / max |",
             "|---|---|---|---|---|---|---|"]
    for v, rs in runs.items():
        shown = [q for j in judged for q in j["items"] if q["variant"] == v and q["status"] == "kept"]
        g = [q["grade"] for q in shown if q.get("grade")]
        right = sum("ABCD".find(x.get("correct", "?")) == q["answer"] for q, x in zip(shown, g))
        pis = sorted(r["pi_s"] for r in rs)
        lines.append(f"| {v} | {sum(len(r['kept']) >= 3 for r in rs)}/{len(rs)} | {len(shown)} | "
                     f"{right}/{len(g)} | {sum(x.get('score', 0) >= 4 for x in g)}/{len(g)} | "
                     f"{sum(x.get('score', 9) <= 2 for x in g)}/{len(g)} | {pis[len(pis) // 2]} s / {pis[-1]} s |")
    for v in runs:
        g = [q["grade"] for j in judged for q in j["items"] if q["variant"] == v and q["status"] == "kept" and q.get("grade")]
        lines.append(f"- **{v}: sensible {sum(bool(x.get('sensible')) for x in g)}/{len(g)}** (key right, all options "
                     "on topic and grammatical, answer not obvious; the lower, practical bar)")
    lines.append("\n## Did the self-check help? (rejected-by-self-check questions vs shown ones, same judge)\n")
    for v in runs:
        rej = [q for j in judged for q in j["items"] if q["variant"] == v and q["status"] == "rejected"
               and q.get("grade") and "self-check" in q.get("reason", "")]
        right = sum("ABCD".find(q["grade"].get("correct", "?")) == q["answer"] for q in rej)
        lines.append(f"- {v}: questions the self-check threw out had a correct key {right}/{len(rej)} times, "
                     f"score >= 4 in {sum(q['grade'].get('score', 0) >= 4 for q in rej)}/{len(rej)}")
    reasons: dict = {}
    for v, rs in runs.items():
        for r in rs:
            for q in r["rejected"]:
                k = (v, q["reason"].split(" (")[0])
                reasons[k] = reasons.get(k, 0) + 1
    lines.append("\n## Why questions were rejected\n")
    lines += [f"- {v}: {k} x{n}" for (v, k), n in sorted(reasons.items())]
    lines.append("\n## Every shown question with its grade\n")
    for j in judged:
        for q in j["items"]:
            if q["status"] != "kept":
                continue
            g = q.get("grade", {})
            ok = "ABCD".find(g.get("correct", "?")) == q["answer"]
            lines.append(f"**{j['id']} [{q['variant']}] score {g.get('score')} {'key OK' if ok else 'KEY WRONG'}"
                         f" {'SENSIBLE' if g.get('sensible') else 'not sensible'}"
                         f" {' '.join(g.get('broken', []))}**: {q['q']}  ")
            lines += [f"{'  ✅' if i == q['answer'] else '  -'} {o}  " for i, o in enumerate(q["options"])]
            lines.append(f"  _{g.get('note', '')}_\n")
    (OUT / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines[:12]))


def cmd_demo(a) -> None:
    """The backup (v2) on one passage, the full deliverable: summary, quiz (with the sentence each answer comes
    from), and a run card (model, size, memory, time, tokens)."""
    import os
    import resource
    from sakshi.generate import make_whole_summary
    from sakshi.misconceptions import Library
    passage = Path(a.passage).read_text()
    t0 = time.time()
    mdir = Path(a.model)
    m, lib = Model(mdir), Library.load()
    load = time.time() - t0
    t1 = time.time()
    summ = make_whole_summary(m.b, passage, retries=1)
    n_sum_calls = len(summ.get("attempts", []))
    for at in summ.get("attempts", []):  # count summary calls in the run card too
        m.calls.append({"kind": "summary", "in": getattr(at, "prompt_tokens", 0) or 0,
                        "out": getattr(at, "new_tokens", 0) or 0, "s": getattr(at, "wall_s", 0) or 0})
    t_sum = time.time() - t1
    print("SUMMARY\n" + (summ.get("text") or "(no summary passed the checks)"))
    t2 = time.time()
    r = quiz_hybrid(m, passage, lib=lib)
    t_quiz = time.time() - t2
    print("\nQUIZ")
    for n, q in enumerate(r["kept"], 1):
        print(f"\nQ{n}. {q['q']}")
        for i, o in enumerate(q["options"]):
            print(f"   {'ABCD'[i]}) {o}")
        print(f"   Answer: {'ABCD'[q['answer']]}   (from the passage: \"{q['evidence']}\")")
    c = m.calls
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (2**20 if sys.platform == "darwin" else 2**10)
    size = os.path.getsize(mdir / "model.pte") / 2**20
    print(f"\nRUN CARD (model ran on this device through ExecuTorch; no cloud call)\n"
          f"Model:   Qwen3-0.6B, ExecuTorch 8da4w ({mdir.name}), {size:.0f} MB on disk\n"
          f"Memory:  peak {rss:.0f} MB (whole process)\n"
          f"Time:    {time.time() - t0:.1f} s total (load {load:.1f} s, summary {t_sum:.1f} s, quiz {t_quiz:.1f} s)\n"
          f"Calls:   {len(c)} model calls ({n_sum_calls} summary), {sum(x['in'] for x in c)} tokens in, "
          f"{sum(x['out'] for x in c)} out\n"
          f"Quiz:    {len(r['kept'])} questions (backup method v2, plain model)")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--limit", type=int, default=None)
    g.add_argument("--variants", nargs="+", default=list(VARIANTS))
    j = sub.add_parser("judge")
    j.add_argument("--judge-model", default="sonnet")
    sub.add_parser("report")
    d = sub.add_parser("demo")
    d.add_argument("passage")
    d.add_argument("--model", default=str(MODEL), help="model folder with model.pte + tokenizer.json "
                   "(UNO Q / Pi 4: the portable model)")
    a = ap.parse_args()
    {"generate": cmd_generate, "judge": cmd_judge, "report": cmd_report, "demo": cmd_demo}[a.cmd](a)



# ---- hybrid: the model writes question + short answer; wrong options come from OTHER passage phrases ----------
# Reading-comprehension practice (Gao et al. 2019, arXiv 1809.02768; EMNLP 2024 distractor survey): good wrong
# options relate to the question and "have some trace in the article". A true passage fact that does not answer
# THIS question is the commonest real reading mistake, and it can never be a repeat, a fragment or nonsense.
QA_SYSTEM = (
    "You write one quiz question for a Class 6-10 student about the key sentence of a text, and its short "
    "correct answer. Ask why or how. The answer is at most 10 words and the text proves it.\n"
    "Use exactly this layout: Question, Answer."
)
QA_EXAMPLES = (
    (EXAMPLES[0][0], "Question: Why do we see lightning before we hear the thunder?\n"
                     "Answer: Because light travels much faster than sound"),
    (EXAMPLES[1][0], "Question: Why were the farmers of Champaran unhappy about growing indigo?\n"
                     "Answer: Because they earned little and lost land for food"),
)
_CLAUSE_SPLIT = re.compile(r"[,;:()]|\s(?:and|but|while|which|because|so|so that|when|whereas|although)\s", re.I)
_LEAD = re.compile(r"^(?:and|but|so|because|then|also|however)\s+", re.I)


_BAD_START = set("when if as after before while give gives does do did is are was were to for with from by of in on at "
                 "than there what how why where who whose its their his her".split())
_NOT_BEFORE_VERB = set("the a an of on in at to for with from by into than this that these those its their his her "
                       "our your my very more most less".split())
_AUX = set("is are was were has have had can could will would may might must should does do did".split())


def is_clause(c: str) -> bool:
    """A full little statement (has a verb), not a fragment like 'give a better grip' or 'the treads on tyres'."""
    w = [t.lower() for t in tokens(c)]
    if not w or w[0] in _BAD_START or w[-1] in _NOT_BEFORE_VERB or w[0].endswith("ing") \
            or w[0] in ("this", "it", "these", "that", "which", "they", "he", "she", "such") \
            or w[0] in ("means", "called", "used", "made", "reactive", "known", "found"):
        return False
    if any(t in _AUX for t in w[1:]):
        return True
    return any(i > 0 and w[i - 1] not in _NOT_BEFORE_VERB and len(t) > 3 and (t.endswith("s") or t.endswith("ed"))
               and not t.endswith("ss") for i, t in enumerate(w))


def stem_set(s: str) -> set[str]:
    return {re.sub(r"(ing|ed|es|s)$", "", t) for t in content(s)}


def passage_phrases(sents: list[str], skip: set[int]) -> list[str]:
    out = []
    for i, s in enumerate(sents):
        if i in skip:
            continue
        for c in _CLAUSE_SPLIT.split(s):
            c = _LEAD.sub("", c.strip(" .\"'")).strip()
            n = len(tokens(c))
            if 4 <= n <= 12 and len(content(c)) >= 2 and is_clause(c):
                out.append(c)
    return out


def styled(phrase: str, like: str) -> str:
    """Give a passage phrase the same opening as the correct answer (e.g. 'Because ...')."""
    p = phrase[0].lower() + phrase[1:] if phrase[:2].lower() != phrase[:2] or not phrase[1:2].isupper() else phrase
    lead = re.match(r"(Because|Since|So that|To|By)\b", like)
    if lead and not re.match(lead.group(1), phrase, re.I):
        if lead.group(1) in ("To", "By"):  # verb phrases: only keep phrases that already fit
            return ""
        return f"{lead.group(1)} {p}"
    return phrase[0].upper() + phrase[1:]


def build_wrong(sents: list[str], i: int, q: str, ans: str, rng: random.Random, k: int = 3) -> list[str]:
    key_c, q_c, ans_c = content(sents[i]), content(q), content(ans)
    na = len(tokens(ans))
    cands = []
    for ph in passage_phrases(sents, skip={i - 1, i, i + 1}):
        pc = content(ph)
        if len(pc & (ans_c | key_c)) / max(1, len(pc)) > 0.34:  # too close to the real answer: could be right
            continue
        if len(pc & q_c) / max(1, len(pc)) > 0.5:  # mostly about the question's own subject: may also answer it
            continue
        opt = styled(ph, ans)
        if not opt:
            continue
        score = 2 * len(pc & q_c) - abs(len(tokens(opt)) - na) + rng.random()  # on topic, similar length
        cands.append((score, opt))
    picked, seen = [], set()
    for _, o in sorted(cands, reverse=True):
        oc = frozenset(content(o))
        if any(len(oc & s) / max(1, len(oc)) > 0.5 for s in seen):
            continue
        picked.append(o)
        seen.add(oc)
        if len(picked) == k:
            break
    return picked


def belief_options(beliefs: list[dict], q: str, ev: str, ans: str, k: int = 3, ranked: bool = False) -> list[str]:
    """Wrong options from the misconception graph: the student beliefs closest to this question, shortened to the
    belief itself ('A handspan is a standard unit because ...' -> 'A handspan is a standard unit') and styled like
    the answer. On topic and believable by construction, wrong by definition."""
    want = stem_set(q) | stem_set(ev)
    ans_s = stem_set(ans)
    cand = []
    for b in beliefs:
        st = re.split(r"\s(?:because|since)\s|[;:(]", b["statement"].strip())[0].strip(" .,")
        if not (3 <= len(tokens(st)) <= 13):
            continue
        bs = stem_set(st)
        if not bs or len(bs & ans_s) / len(bs) > 0.8:
            continue
        cand.append((len(bs & want), st))
    out, seen = [], []
    for sc, st in (cand if ranked else sorted(cand, key=lambda x: -x[0])):
        if sc == 0 and not ranked:
            break
        o = styled(st, ans)
        oc = stem_set(o)
        if not o or any(len(oc & x) / max(1, len(oc)) > 0.5 for x in seen):
            continue
        out.append(o)
        seen.append(oc)
        if len(out) == k:
            break
    return out


def quiz_hybrid(m: Model, passage: str, n: int = 4, seed: int = 0, lib=None, skip=frozenset(), wrong_fn=None) -> dict:
    rng = random.Random(seed)
    sents = split_sentences(passage)
    start = len(m.calls)
    kept, rejected = [], []
    beliefs = lib.match(passage, n_misconceptions=40).misconceptions if lib else []
    for i in pick_sentences(passage):
        if len(kept) == n:
            break
        if i in skip:
            continue
        ev = sents[i]
        raw = m.run(QA_SYSTEM, f"Text: {window(sents, i)}\nKey sentence: {ev}", 50, examples=QA_EXAMPLES,
                    kind="question", prefix="Question: Why")
        qm, am = re.search(r"Question:\s*(.+?\?)", raw), re.search(r"Answer:\s*(.+)", raw)
        rec = {"evidence": ev, "raw": raw}
        if not (qm and am):
            rejected.append({**rec, "reason": "could not parse"})
            continue
        q = re.sub(r"^Why(?=\w)", "Why ", qm.group(1).strip())
        ans = am.group(1).strip().rstrip(".")
        if len(tokens(ans)) > 10:  # the model ignores "at most 10 words": keep the first clause
            ans = re.split(r",\s*(?:so|and|which|because|but|as)\b|\s(?:so that|which|so)\s|;", ans)[0].strip(" ,")
        ac = stem_set(re.sub(r"^(Because|Since)\s+", "", ans))
        if ac and len(ac - stem_set(q)) < 2:
            rejected.append({**rec, "q": q, "reason": "answer only repeats the question"})
            continue
        if len(tokens(ans)) > 13:
            rejected.append({**rec, "q": q, "reason": "answer too long"})
            continue
        if wrong_fn:
            wrong = wrong_fn(sents, i, q, ans, rng)
        else:
            wrong = belief_options(beliefs, q, ev, ans) if beliefs else []
            if len(wrong) < 3:
                wrong += [w for w in build_wrong(sents, i, q, ans, rng) if w not in wrong][: 3 - len(wrong)]
        if len(wrong) < 3:
            rejected.append({**rec, "q": q, "reason": "not enough wrong options"})
            continue
        if len(tokens(ans)) > max(len(tokens(w)) for w in wrong) + 3:
            rejected.append({**rec, "q": q, "reason": "answer is clearly the longest option"})
            continue
        opts = [ans] + wrong
        rng.shuffle(opts)
        item = {"q": q, "options": opts, "answer": opts.index(ans), "explain": ev}
        rec.update(item)
        why = code_check(item)
        if why:
            rejected.append({**rec, "reason": why})
            continue
        ok, said = self_check(m, window(sents, i), item, rng)
        if not ok:
            rejected.append({**rec, "reason": f"self-check failed (picked {said})"})
            continue
        kept.append(rec)
    return {"kept": kept, "rejected": rejected, "calls": m.calls[start:]}



# ---- v3: code cuts the reason out of the passage; options = 2 matched beliefs + 1 true-but-irrelevant fact ----
# Fixes the two commonest judge complaints on v2 ("why" asked where the passage gives no reason; the answer only
# restates the question): the answer is the passage's own stated reason, so it is correct by construction. Mixing
# one passage phrase into the wrong options stops word-matching (tested: 66% -> 27%, chance is 25%).
_REASON = [
    # (pattern, which group is the effect, which is the reason, answer opening)
    (re.compile(r"^(?P<e>.+?),?\s+because\s+of\s+(?P<r>.+)$", re.I), "Because of"),
    (re.compile(r"^(?P<e>.+?),?\s+because\s+(?P<r>.+)$", re.I), "Because"),
    (re.compile(r"^(?P<e>.+?),?\s+due\s+to\s+(?P<r>.+)$", re.I), "Because of"),
    (re.compile(r"^(?P<e>.+?),?\s+so\s+that\s+(?P<r>.+)$", re.I), "So that"),
    (re.compile(r"^since\s+(?P<r>.+?),\s*(?P<e>.+)$", re.I), "Because"),
    (re.compile(r"^(?P<r>.+?),?\s+which\s+is\s+why\s+(?P<e>.+)$", re.I), "Because"),
    (re.compile(r"^(?P<r>.+?),\s*so\s+(?P<e>.+)$", re.I), "Because"),
    (re.compile(r"^(?P<r>.+?);?\s+therefore,?\s+(?P<e>.+)$", re.I), "Because"),
]
_WHEN = re.compile(r"^(?:when|if)\s+(?P<c>[^,]{8,}),\s*(?P<x>.+)$", re.I)


def first_clause(t: str, max_words: int = 12) -> str:
    t = t.strip(" .")
    if len(tokens(t)) > max_words:
        t = re.split(r",\s*|\s(?:and|while|which|so)\s", t)[0].strip(" .")
    return t if 3 <= len(tokens(t)) <= max_words else ""


def reason_items(sents: list[str]) -> list[dict]:
    """Sentences where the passage itself states a reason (or a when-then): effect, reason/answer, kind."""
    out = []
    for i, s in enumerate(sents):
        s0 = s.strip().rstrip(".")
        for pat, opening in _REASON:
            m = pat.match(s0)
            if m:
                r, e = first_clause(m.group("r")), m.group("e").strip(" ,")
                if r and len(tokens(e)) >= 3:
                    out.append({"i": i, "kind": "why", "effect": e, "answer": f"{opening} {r[0].lower() + r[1:]}"})
                break
        else:
            m = _WHEN.match(s0)
            x = m.group("x") if m else ""
            if m:
                c = m.group("c").strip()
                k = re.search(r",\s*(?=(it|they|this|these|the \w+)\s+\w+)", x)
                if k and len(tokens(x[: k.start()])) <= 6:  # "smooth, shiny surface ..., it bounces back"
                    c, x = f"{c}, {x[: k.start()]}", x[k.end():]
            if m and first_clause(x):
                a = first_clause(x)
                out.append({"i": i, "kind": "when", "q": f"What happens when {c[0].lower() + c[1:]}?",
                            "answer": a[0].upper() + a[1:]})
    return out


WHY_SYSTEM = ("Rewrite the fact as one short question for a Class 6-10 student that asks why it happens. "
              "Do not include the reason in the question. Reply with the question only.")
WHY_EXAMPLES = (("Fact: we see the flash first and hear the thunder a few seconds later",
                 "Why do we see lightning before we hear the thunder?"),
                ("Fact: farmers could not grow enough food for their families",
                 "Why could the farmers not grow enough food for their families?"))


class Beliefs:
    """Misconceptions nearest in MEANING to the question + answer (the on-device embedding helper; the library's
    vectors are precomputed, so the Pi embeds only the question)."""

    def __init__(self, lib):
        import numpy as np
        from sakshi.mapper import Mapper, PteEncoders
        self.np, self.mapper = np, Mapper(lib, PteEncoders())
        E = self.mapper.E_mis
        self.E = E / np.linalg.norm(E, axis=1, keepdims=True)
        self.lib = lib

    def options(self, pool: list[dict], q: str, ans: str, k: int = 2) -> list[str]:
        if not pool:
            return []
        v = self.mapper.enc.embed([f"{q} {ans}"])[0]
        v = v / self.np.linalg.norm(v)
        idx = [self.mapper.pos[m["id"]] for m in pool]
        order = sorted(range(len(pool)), key=lambda j: -float(self.E[idx[j]] @ v))
        return belief_options([pool[j] for j in order], q, "", ans, k=k, ranked=True)


def mixed_wrong(beliefs: "Beliefs | None", pool: list[dict], sents: list[str], i: int, q: str, ans: str,
                rng: random.Random) -> list[str]:
    b = beliefs.options(pool, q, ans, k=2) if beliefs else []
    p = [w for w in build_wrong(sents, i, q, ans, rng) if w not in b]
    return (b + p)[:3] if len(b) == 2 else (b + p)[:3]


def quiz_v3(m: Model, passage: str, beliefs: "Beliefs | None", lib, n: int = 4, seed: int = 0) -> dict:
    rng = random.Random(seed)
    sents = split_sentences(passage)
    start = len(m.calls)
    kept, rejected, used = [], [], set()
    pool = lib.match(passage, n_misconceptions=40).misconceptions
    for it in reason_items(sents):
        if len(kept) == n:
            break
        i = it["i"]
        rec = {"evidence": sents[i], "source": it["kind"]}
        if it["kind"] == "why":
            raw = m.run(WHY_SYSTEM, f"Fact: {it['effect']}", 30, examples=WHY_EXAMPLES, kind="question",
                        prefix="Why")
            q = re.sub(r"^Why(?=\w)", "Why ", raw.strip().split("\n")[0]).strip()
            q = q if q.endswith("?") else q.split("?")[0] + "?"
        else:
            q, raw = it["q"], ""
        ans = it["answer"]
        rec.update(raw=raw, q=q)
        if re.match(r"^(Why|What happens when)\s+((do|does|is|are|was|were|did|can)\s+)?(it|they|this|these|he|she)\b", q, re.I):
            rejected.append({**rec, "reason": "unclear it/they question"})
            continue
        if len(stem_set(re.sub(r"^(Because( of)?|So that)\s+", "", ans)) - stem_set(q)) < 2:
            rejected.append({**rec, "reason": "answer only repeats the question"})
            continue
        wrong = mixed_wrong(beliefs, pool, sents, i, q, ans, rng)
        if len(wrong) < 3:
            rejected.append({**rec, "reason": "not enough wrong options"})
            continue
        opts = [ans] + wrong
        rng.shuffle(opts)
        item = {"q": q, "options": opts, "answer": opts.index(ans), "explain": sents[i]}
        rec.update(item)
        why = code_check(item)
        if why:
            rejected.append({**rec, "reason": why})
            continue
        ok, said = self_check(m, window(sents, i), item, rng)
        if not ok:
            rejected.append({**rec, "reason": f"self-check failed (picked {said})"})
            continue
        kept.append(rec)
        used.add(i)
    if len(kept) < n:  # top up with the v2 method on other sentences (model writes question + answer)
        rest = quiz_hybrid(m, passage, n=n - len(kept), seed=seed, lib=lib, skip=used | {k["i"] for k in []},
                           wrong_fn=lambda sents_, i_, q_, a_, r_: mixed_wrong(beliefs, pool, sents_, i_, q_, a_, r_))
        for q in rest["kept"]:
            q["source"] = "model"
        kept += rest["kept"]
        rejected += rest["rejected"]
    return {"kept": kept, "rejected": rejected, "calls": m.calls[start:]}



# ---- v4: the model turns each matched misconception into THIS question's wrong answer -----------------------
# v3's code-picked wrong options were on the topic but did not answer the question, so the key was the only
# on-topic option (judge, 13 Nov). DiVERT (arXiv 2406.19356) / MISTAKE: make the misconception explicit, then
# write the answer a student holding it would give. Here that is a short rewrite, which a 0.6B model can do.
BELIEF_SYSTEM = ("A student holds the wrong belief below. Write the short answer (at most 10 words) this student "
                 "would give to the question. It must be wrong. Reply with the answer only.")
BELIEF_EXAMPLES = (
    ("Belief: Heavier objects always cut better than lighter ones.\nQuestion: Why does a sharp knife cut better "
     "than a blunt one?", "Because a sharp knife is heavier"),
    ("Belief: Plants get their food from the soil through their roots.\nQuestion: What happens when a leaf is "
     "kept in sunlight?", "It soaks up food from the soil"),
)


def belief_answers(m: "Model", beliefs: "Beliefs", pool: list[dict], q: str, ans: str, k: int = 3) -> list[str]:
    if not pool:
        return []
    v = beliefs.mapper.enc.embed([f"{q} {ans}"])[0]
    v = v / beliefs.np.linalg.norm(v)
    order = sorted(pool, key=lambda b: -float(beliefs.E[beliefs.mapper.pos[b["id"]]] @ v))
    lead = re.match(r"(Because of|Because|So that)\b", ans)
    out, seen = [], [stem_set(ans)]
    for b in order[: k + 2]:
        raw = m.run(BELIEF_SYSTEM, f"Belief: {b['statement']}\nQuestion: {q}", 24, examples=BELIEF_EXAMPLES,
                    kind="distractor", prefix=(lead.group(1) + " ") if lead else "")
        o = raw.strip().split("\n")[0].strip(" .\"'")
        oc = stem_set(o)
        if not (2 <= len(tokens(o)) <= 14) or any(len(oc & x) / max(1, len(oc)) > 0.6 for x in seen):
            continue
        out.append(o[0].upper() + o[1:])
        seen.append(oc)
        if len(out) == k:
            break
    return out


def quiz_v4(m: "Model", passage: str, beliefs: "Beliefs", lib, n: int = 4, seed: int = 0) -> dict:
    global mixed_wrong
    orig = mixed_wrong
    pool = lib.match(passage, n_misconceptions=40).misconceptions

    def wrong(beliefs_, pool_, sents, i, q, ans, rng):
        w = belief_answers(m, beliefs_, pool, q, ans)
        return w if len(w) == 3 else (w + [x for x in orig(beliefs_, pool, sents, i, q, ans, rng) if x not in w])[:3]
    mixed_wrong = wrong
    try:
        return quiz_v3(m, passage, beliefs, lib, n=n, seed=seed)
    finally:
        mixed_wrong = orig


if __name__ == "__main__":
    main()
