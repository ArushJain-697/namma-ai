"""Training data for "sensible" multiple-choice questions from existing, human-checked sources (13 Nov 2026).

Why: the teammate's Opus data is not ready, and Gemini Deep Research (Small Model MCQ Generation report) points to
existing passage -> question datasets plus plain LoRA SFT on ~2-5k examples as the proven route for 0.5B models.
Sources:
  * SciQ (allenai/sciq, 11,679 train): crowd-written science questions, each with a supporting paragraph, the
    correct answer and 3 same-type wrong options. Licence CC BY-NC 3.0 (non-commercial: fine for a hackathon).
  * RACE middle (ehovy/race): English exam reading comprehension for Chinese middle schools, distractors written
    by teachers; prose passages and why-questions balance SciQ's science recall. Research licence.
  * NCERT_MCQs (goenkalokesh/NCERT_MCQs): optional; most rows have no marked answer (~6 usable).
Format = what the Pi runs (one call per question): the user turn is a 3-sentence window around a key sentence +
the key sentence; the answer is "Question / A) B) C) D) / Answer". Options are shuffled so the key letter is
balanced. Output: data/dataset_mcq/{train,val}.jsonl in the same {"messages": [...]} format as the teammate's data,
so both can be mixed in one training run.

  .venv-ml/bin/python scripts/make_mcq_dataset.py
"""
from __future__ import annotations

import argparse
import io
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from sakshi.text import split_sentences, tokens, STOPWORDS  # noqa: E402

OUT = ROOT / "data" / "dataset_mcq"
SYSTEM = ("You write one multiple-choice question for a Class 6-10 student about the key sentence of a text. "
          "Exactly one option is correct and the text proves it. The three wrong options are the same kind of thing "
          "as the answer and sound believable, but the text shows they are wrong. Never use 'all of the above' or "
          "'none of the above'. Use exactly this layout: Question, A) B) C) D), Answer.")
BANNED = re.compile(r"\b(all|none|both) of the above\b|_{2,}|\bnot\b|\bexcept\b|according to the (passage|text)", re.I)


def content(s: str) -> set[str]:
    return {re.sub(r"(ing|ed|es|s)$", "", t.lower()) for t in tokens(s) if len(t) > 2 and t.lower() not in STOPWORDS}


def user_turn(sents: list[str], i: int) -> str:
    return f"Text: {' '.join(sents[max(0, i - 1): i + 2])}\nKey sentence: {sents[i]}"


def answer_turn(q: str, opts: list[str], key: int) -> str:
    return "Question: " + q + "\n" + "\n".join(f"{c}) {o}" for c, o in zip("ABCD", opts)) + f"\nAnswer: {'ABCD'[key]}"


def key_sentence(sents: list[str], q: str, ans: str) -> int | None:
    """The sentence that best supports question + answer; must contain the answer's content words."""
    a, qa = content(ans), content(q) | content(ans)
    best, bi = 0.0, None
    for i, s in enumerate(sents):
        sc = content(s)
        if a and not a <= sc:
            continue
        score = len(sc & qa)
        if score > best:
            best, bi = score, i
    return bi if best >= 2 else None


def ok_item(q: str, opts: list[str]) -> bool:
    if BANNED.search(q) or any(BANNED.search(o) for o in opts):
        return False
    if len(tokens(q)) > 30 or len(tokens(q)) < 4 or any(not (1 <= len(tokens(o)) <= 12) for o in opts):
        return False
    return len({o.lower().strip(" .") for o in opts}) == 4


def make(sents: list[str], q: str, ans: str, wrong: list[str], rng: random.Random, source: str) -> dict | None:
    q, ans, wrong = q.strip(), ans.strip().rstrip("."), [w.strip().rstrip(".") for w in wrong]
    if not q.endswith("?"):
        return None
    opts = [ans] + wrong
    if not ok_item(q, opts):
        return None
    i = key_sentence(sents, q, ans)
    if i is None or not (6 <= len(tokens(sents[i])) <= 50):
        return None
    rng.shuffle(opts)
    return {"source": source, "messages": [{"role": "system", "content": SYSTEM},
                                           {"role": "user", "content": user_turn(sents, i)},
                                           {"role": "assistant", "content": answer_turn(q, opts, opts.index(ans))}]}


def from_sciq(rng: random.Random) -> list[dict]:
    from datasets import load_dataset
    out = []
    for split in ("train", "validation"):
        for r in load_dataset("allenai/sciq", split=split):
            if len(tokens(r["support"])) < 25:
                continue
            ex = make(split_sentences(r["support"]), r["question"], r["correct_answer"],
                      [r["distractor1"], r["distractor2"], r["distractor3"]], rng, "sciq")
            if ex:
                out.append(ex)
    return out


def from_race(rng: random.Random) -> list[dict]:
    """RACE middle-school reading comprehension (teacher-written exam distractors; research licence)."""
    from datasets import load_dataset
    out = []
    for r in load_dataset("ehovy/race", "middle", split="train"):
        q = r["question"].strip()
        if "_" in q or not q.endswith("?"):
            continue  # cloze-style RACE questions are banned in our quiz
        if re.search(r"\b(title|passage|article|author|writer|mainly|main idea|probably|infer|learn from)\b", q, re.I):
            continue  # whole-passage questions cannot be answered from a 3-sentence window
        if len(re.findall(r"[a-z][.!?][A-Z]", r["article"])) > 2:
            continue  # missing spaces after full stops: sentence splitting would be wrong
        opts = list(r["options"])
        key = "ABCD".index(r["answer"])
        ex = make(split_sentences(r["article"]), q, opts[key], [o for k, o in enumerate(opts) if k != key], rng, "race")
        if ex:
            out.append(ex)
    return out


def from_ncert(path: str, rng: random.Random) -> list[dict]:
    import pandas as pd
    df = pd.read_csv(io.StringIO(open(path, "rb").read().decode("utf-8", errors="replace")))
    out = []
    for _, r in df.iterrows():
        sents = split_sentences(str(r["passage"]).replace("\n", " "))
        text = "".join(eval(r["mcqs"])) if str(r["mcqs"]).startswith("[") else str(r["mcqs"])  # noqa: S307 (list of str)
        for m in re.finditer(r"^\s*\d+\.\s+\*\*(.+?)\*\*\s*\n\s*(\(A\).+?)$", text, re.M):
            q, line = m.group(1).strip(), m.group(2)
            parts = re.split(r"\(([ABCD])\)", line)[1:]
            opts = {parts[k]: parts[k + 1].strip() for k in range(0, len(parts) - 1, 2)}
            if len(opts) != 4:
                continue
            bold = [c for c, o in opts.items() if o.startswith("**")]
            if len(bold) != 1:
                continue
            clean = {c: o.strip("* ").strip() for c, o in opts.items()}
            ans = clean[bold[0]]
            ex = make(sents, q, ans, [o for c, o in clean.items() if c != bold[0]], rng, "ncert")
            if ex:
                out.append(ex)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ncert", default=None, help="optional: only ~6 usable rows (most have no marked answer)")
    ap.add_argument("--race-max", type=int, default=1500)
    ap.add_argument("--sciq-max", type=int, default=3000)
    ap.add_argument("--val", type=int, default=200)
    a = ap.parse_args()
    rng = random.Random(7)
    sciq, race = from_sciq(rng), from_race(rng)
    ncert = from_ncert(a.ncert, rng) if a.ncert else []
    print(f"usable: SciQ {len(sciq)}, RACE-middle {len(race)}, NCERT {len(ncert)}")
    rng.shuffle(sciq)
    rng.shuffle(race)
    rows = sciq[: a.sciq_max] + race[: a.race_max] + ncert
    rng.shuffle(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    val, train = rows[: a.val], rows[a.val:]
    for name, part in (("train", train), ("val", val)):
        with open(OUT / f"{name}.jsonl", "w") as f:
            for r in part:
                f.write(json.dumps(r) + "\n")
    letters = [r["messages"][2]["content"][-1] for r in train]
    print(f"wrote {len(train)} train, {len(val)} val to {OUT}; answer letters {dict(sorted(__import__('collections').Counter(letters).items()))}")
    for r in train[:2]:
        print("\n---", r["source"], "\n" + r["messages"][1]["content"] + "\n>>>\n" + r["messages"][2]["content"])


if __name__ == "__main__":
    main()
