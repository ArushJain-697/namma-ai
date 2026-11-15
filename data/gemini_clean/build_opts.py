"""Build clean datasets from the Gemini 'raw' items.
  opts/   : wrong-options model  (passage+key sentence+question+answer -> 3 x 'Misconception | Wrong option')
  qa/     : question+answer model (passage+key sentence -> Question + Answer)
Extra filters on top of the repo's own validators; counts per filter are printed."""
import json, glob, random, collections, os, re
RAW = "C:/Users/Arush/gpu-train/nammaai/repo/data/dataset/raw/"
BASE = "C:/Users/Arush/gpu-train/nammaai/"

SYS_OPTS = ("You write the three wrong options for a multiple-choice question. For each one, first name the specific "
            "mistake a student could make, then write the wrong option that student would pick. The three options must "
            "be different from each other and from the correct answer. Use exactly this layout, one per line: "
            "Misconception: <the mistake> | Wrong option: <short option text>")
SYS_QA = ("You write one question for a Class 6-10 student about the key sentence of a text, and its correct answer. "
          "The answer must come from the key sentence. Use exactly this layout: Question: <question> then Answer: <short answer>")

def words(s): return re.findall(r"\w+", s.lower())
def jac(a, b):
    a, b = set(words(a)), set(words(b)); return len(a & b) / max(1, len(a | b))
def contains(a, b):  # one option fully inside another
    A, B = words(a), words(b); sa, sb = " ".join(A), " ".join(B)
    return bool(sa) and bool(sb) and (sa in sb or sb in sa)

BAD_OPT = re.compile(r"\b(all|none|both)\b.*\b(above|these)\b|\bnot (given|mentioned)\b|\bi don'?t know\b", re.I)
drop = collections.Counter()

def keep(it, passage):
    if not all(k in it and it[k] for k in ("stem", "answer", "options", "evidence")): drop["missing field"] += 1; return False
    ops = it["options"]
    if len(ops) != 3 or not all(o.get("why") and o.get("text") for o in ops): drop["not 3 options with why+text"] += 1; return False
    ans = it["answer"].strip(); texts = [o["text"].strip() for o in ops]; whys = [o["why"].strip() for o in ops]
    if not it["stem"].strip().endswith("?"): drop["stem is not a question"] += 1; return False
    if any(BAD_OPT.search(t) for t in texts + [ans]): drop["all/none-of-the-above style option"] += 1; return False
    if any(not (1 <= len(words(t)) <= 14) for t in texts): drop["option too short/long"] += 1; return False
    allt = texts + [ans]
    for i in range(4):
        for j in range(i + 1, 4):
            if jac(allt[i], allt[j]) >= 0.6 or contains(allt[i], allt[j]): drop["options near-duplicate or contained"] += 1; return False
    if any(len(words(w)) < 5 for w in whys): drop["misconception text too short"] += 1; return False
    if max(jac(whys[i], whys[j]) for i in range(3) for j in range(i + 1, 3)) >= 0.7: drop["two options share the same misconception"] += 1; return False
    wl = [len(words(t)) for t in allt]
    if max(wl) > 3 * max(1, min(wl)) and max(wl) - min(wl) > 4: drop["option length cue"] += 1; return False
    DANGLE = {"the","a","an","of","by","to","in","on","for","with","and","or","as","at","from","than","that","which","is","are","was","were","be","not","into","its","their","his","her","our","this","these","those","but","if","so"}
    if any(words(t)[-1] in DANGLE or words(t)[0] in {"and","or","but","than","that","which"} for t in allt): drop["cut-off option (ends/starts mid-phrase)"] += 1; return False
    isnum = lambda t: bool(re.fullmatch(r"[\d.,%/\s-]+\s*(kg|km|m|cm|mm|g|years?|days?|percent|rs|rupees)?", t.strip().lower()))
    if len({isnum(t) for t in allt}) > 1: drop["numbers mixed with words among options"] += 1; return False
    if any(re.search(r"^(picks?|states?|selects?|chooses?|uses?|mentions?|lists?|repeats?|copies|takes?)\b|found elsewhere|found near|true fact that|different number|picks? a (date|number|name)|selects? a (different|date|number|name)|random|any other (number|date|name)|unrelated|same as (the )?(answer|key)", w, re.I) for w in whys): drop["generic misconception text"] += 1; return False
    if ans.lower() in it["stem"].lower(): drop["answer inside the question"] += 1; return False
    if any(t.lower() in it["stem"].lower() for t in texts): drop["a wrong option is inside the question"] += 1; return False
    if passage.lower().count(it["evidence"].lower()[:60]) == 0: drop["evidence not in passage"] += 1; return False
    # answer must be supported by the evidence sentence (>=50% of its content words)
    aw = [w for w in words(ans) if len(w) > 3]
    if aw and sum(w in set(words(it["evidence"])) for w in aw) / len(aw) < 0.5: drop["answer not supported by evidence"] += 1; return False
    return True

def rows(split):
    out = []; seen = set()
    for f in sorted(glob.glob(RAW + split + "/*.json")):
        d = json.load(open(f, encoding="utf8")); r = d.get("response") or {}
        for it in r.get("items", []):
            if not keep(it, r.get("passage", "")): continue
            key = re.sub(r"\W+", " ", it["stem"].lower()).strip()
            if key in seen: drop["duplicate question"] += 1; continue
            seen.add(key)
            ctx = f"Passage:\n{r['passage']}\nKey sentence: {it['evidence']}"
            out.append({"topic": str(d["job"].get("topic_id")), "subject": str(d["job"].get("topic_id")).split("-")[0],
                "stem": it["stem"].strip(), "answer": it["answer"].strip(), "ctx": ctx, "ref_wrong": [o["text"].strip() for o in it["options"]],
                "opts": [(o["why"].strip(), o["text"].strip()) for o in it["options"]]})
    return out

def write(name, data, mk):
    os.makedirs(BASE + name, exist_ok=True)
    with open(BASE + name + ".jsonl", "w", encoding="utf8") as f:
        for r in data:
            msgs = mk(r)
            f.write(json.dumps({"messages": msgs, "stem": r["stem"], "answer": r["answer"], "ref_wrong": r["ref_wrong"], "topic": r["topic"]}) + "\n")

def mk_opts(r):
    asst = "\n".join(f"Misconception: {w} | Wrong option: {t}" for w, t in r["opts"])
    return [{"role": "system", "content": SYS_OPTS},
            {"role": "user", "content": f"{r['ctx']}\nQuestion: {r['stem']}\nCorrect answer: {r['answer']}"},
            {"role": "assistant", "content": asst}]
def mk_qa(r):
    return [{"role": "system", "content": SYS_QA}, {"role": "user", "content": r["ctx"]},
            {"role": "assistant", "content": f"Question: {r['stem']}\nAnswer: {r['answer']}"}]

tr = rows("train"); te = rows("test")
print("dropped (train+test):"); [print(f"  {v:5d}  {k}") for k, v in drop.most_common()]
topics = sorted({r["topic"] for r in tr}); random.seed(0); random.shuffle(topics)
val_t = set(topics[:max(8, len(topics) // 12)])
val = [r for r in tr if r["topic"] in val_t]; tr = [r for r in tr if r["topic"] not in val_t]
for nm, mk in (("opts", mk_opts), ("qa", mk_qa)):
    for sp, d in (("train", tr), ("val", val), ("test", te)):
        os.makedirs(BASE + nm, exist_ok=True)
        with open(BASE + f"{nm}/{sp}.jsonl", "w", encoding="utf8") as f:
            for r in d:
                f.write(json.dumps({"messages": mk(r), "stem": r["stem"], "answer": r["answer"], "ref_wrong": r["ref_wrong"], "topic": r["topic"]}) + "\n")
print("kept: train", len(tr), "val", len(val), "test", len(te))
print("train subjects:", dict(collections.Counter(r["subject"] for r in tr)))
