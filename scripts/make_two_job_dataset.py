"""Two-job training data for GURU-0.6B (14 Nov 2026): one model, two short jobs, chosen by the system prompt.

Why: the fine-tuned model writes good questions but weak wrong options. Research on small models (answer-first
generation, step-by-step generation, overgenerate-and-filter for distractors) says one small job at a time works
better than one big job, and a dedicated wrong-option call can be asked for traps only (and run more than once).
  Job Q (question + answer): 3-sentence window + key sentence  ->  "Question: ...\\nAnswer: <correct answer>"
  Job W (wrong options):     window + key sentence + question + correct answer  ->  "Wrong answers:\\n1) ...\\n2) ...\\n3) ..."
Inputs: the single-call examples already built (teacher questions graded 4-5, RACE reminder) in the training zip
format: user = "Text: ...\\nKey sentence: ...", assistant = "Question: ...\\nA) ..\\nB) ..\\nC) ..\\nD) ..\\nAnswer: X".

  .venv-ml/bin/python scripts/make_two_job_dataset.py --src /Users/arushjain/Documents/final-training/data \\
      --out /Users/arushjain/Documents/final-training-2job/data
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
from pathlib import Path

Q_SYSTEM = ("You write one quiz question for a Class 6-10 student about the key sentence of a text, and its correct "
            "answer. Ask why, how or what happens, never a word to fill in. The text must prove the answer. "
            "Use exactly this layout: Question, Answer.")
W_SYSTEM = ("You write wrong answers for a quiz question for a Class 6-10 student. Each wrong answer is something a "
            "real student could believe (a common mistake or misconception), is clearly wrong according to the text, "
            "and is the same kind of answer, length and style as the correct answer. Never repeat the correct answer, "
            "never write 'all/none of the above'. Use exactly this layout: Wrong answers, 1) 2) 3).")


def split_single(r: dict) -> dict | None:
    user, ans = r["messages"][1]["content"], r["messages"][2]["content"]
    q = re.search(r"^Question:\s*(.+)$", ans, re.M)
    opts = dict(re.findall(r"^([ABCD])\)\s*(.+)$", ans, re.M))
    key = re.search(r"^Answer:\s*([ABCD])", ans, re.M)
    if not (q and key and len(opts) == 4):
        return None
    k = key.group(1)
    return {"user": user, "q": q.group(1).strip(), "answer": opts[k].strip(),
            "wrong": [opts[c].strip() for c in "ABCD" if c != k]}


def jobs(x: dict, src: dict, rng: random.Random) -> list[dict]:
    meta = {k: src.get(k) for k in ("source", "kind", "passage_id", "wrong_misconceptions")}
    wrong = x["wrong"][:]
    rng.shuffle(wrong)
    qa = {**meta, "job": "Q", "messages": [
        {"role": "system", "content": Q_SYSTEM}, {"role": "user", "content": x["user"]},
        {"role": "assistant", "content": f"Question: {x['q']}\nAnswer: {x['answer']}"}]}
    wa = {**meta, "job": "W", "messages": [
        {"role": "system", "content": W_SYSTEM},
        {"role": "user", "content": f"{x['user']}\nQuestion: {x['q']}\nCorrect answer: {x['answer']}"},
        {"role": "assistant", "content": "Wrong answers:\n" + "\n".join(f"{i}) {w}" for i, w in enumerate(wrong, 1))}]}
    return [qa, wa]


QRULE, WRULE = ("H1", "H3", "H6", "H7"), ("H3", "H4", "H5")


def from_raw(raw_dir: str, grades: str, hold: set[str], rng: random.Random) -> tuple[list[dict], list[dict]]:
    """Per-job selection from the graded teacher questions: Job Q needs a good question + provable key (H1,H3,H6,H7)
    whatever its options are like; Job W needs a provable key + believable options + no giveaways (H3,H4,H5) even if
    the question is plain recall. Each job gets the examples that teach ITS skill."""
    import glob
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    import make_mcq_dataset as mk
    from sakshi.text import split_sentences, tokens
    G = {}
    for line in open(grades):
        g = json.loads(line)
        G[g["key"]] = g
    train, val, c = [], [], collections.Counter()
    for f in sorted(glob.glob(f"{raw_dir}/*.json")):
        d = json.load(open(f))
        src, sents = d["source"], split_sentences(d["passage"])
        teacher = "opus" if "opus" in d.get("teacher", "") else "sonnet"
        for k, it in enumerate(d["response"]["items"]):
            g = G.get(f"{src}#{k}")
            if not g:
                continue
            ev = it["evidence"].strip()
            idx = next((i for i, s in enumerate(sents) if ev[:60] in s or s[:60] in ev), None)
            opts = [o.strip().rstrip(".") for o in it["options"]]
            if idx is None or len({o.lower() for o in opts}) < 4 or any(len(tokens(o)) > 14 for o in opts) \
                    or len(tokens(it["q"])) > 32:
                continue
            x = {"user": mk.user_turn(sents, idx), "q": it["q"].strip(), "answer": opts[0], "wrong": opts[1:]}
            meta = {"source": teacher, "kind": it.get("kind"), "passage_id": src,
                    "wrong_misconceptions": [w.get("misconception") for w in it.get("wrong", [])]}
            qa, wa = jobs(x, meta, rng)
            dest = val if src in hold else train
            if all(g.get(h) for h in QRULE):
                dest.append(qa)
                c[("Q", "val" if src in hold else "train")] += 1
            if all(g.get(h) for h in WRULE):
                dest.append(wa)
                c[("W", "val" if src in hold else "train")] += 1
    print("teacher per-job selection:", dict(sorted(c.items())))
    return train, val


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw", help="teacher raw folder (data/dataset_v2/raw): per-job selection by rubric flags")
    ap.add_argument("--grades", help="grades.jsonl for --raw")
    a = ap.parse_args()
    if a.raw:  # teacher questions selected per job + the non-teacher rows (RACE reminder, SciQ val) from --src
        rng = random.Random(55)
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        hold = {json.loads(l).get("passage_id") for l in open(Path(a.src) / "val.jsonl")} - {None}
        t_train, t_val = from_raw(a.raw, a.grades, hold, rng)
        for name, teacher_rows in (("train", t_train), ("val", t_val)):
            rows = list(teacher_rows)
            for line in open(Path(a.src) / f"{name}.jsonl"):
                r = json.loads(line)
                if r.get("source") in ("opus", "sonnet"):
                    continue
                x = split_single(r)
                if x:
                    rows += jobs(x, r, rng)
            rng.shuffle(rows)
            with open(out / f"{name}.jsonl", "w") as f:
                for j in rows:
                    f.write(json.dumps(j) + "\n")
            print(f"{name}: {len(rows)}", dict(collections.Counter((j["job"], j["source"]) for j in rows)))
        return
    rng = random.Random(55)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("train", "val"):
        rows, made, bad = [], collections.Counter(), 0
        for line in open(Path(a.src) / f"{name}.jsonl"):
            r = json.loads(line)
            x = split_single(r)
            if x is None:
                bad += 1
                continue
            for j in jobs(x, r, rng):
                rows.append(j)
                made[(j["job"], r.get("source"))] += 1
        rng.shuffle(rows)
        with open(out / f"{name}.jsonl", "w") as f:
            for j in rows:
                f.write(json.dumps(j) + "\n")
        print(f"{name}: {len(rows)} examples, unparseable {bad}; {dict(sorted(made.items()))}")


if __name__ == "__main__":
    main()
