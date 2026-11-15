"""Convert the cleaned Gemini 'opts' data to the teammate's Job W format (docs: TWO_CALL_QUIZ_AND_WRONG_OPTIONS.md).
  user      = "Text: <2-3 sentence window>\nKey sentence: ...\nQuestion: ...\nCorrect answer: ..."
  assistant = "Wrong answers:\n1) ...\n2) ...\n3) ..."
Extra rubric filters (docs/QUESTION_RUBRIC.md H5): similar length, key not longest, no passage-copy giveaway, same style.
!!! W_SYSTEM below is a PLACEHOLDER. Replace it with the exact W_SYSTEM from scripts/make_two_job_dataset.py before training."""
import json, re, os, collections
BASE = "C:/Users/Arush/gpu-train/nammaai/"
OUT = "C:/Users/Arush/Downloads/gemini-clean-dataset/w-job/"
os.makedirs(OUT, exist_ok=True)
W_SYSTEM = "PLACEHOLDER_REPLACE_WITH_EXACT_W_SYSTEM"

def words(s): return re.findall(r"\w+", s.lower())
def sents(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s.strip()]
def window(passage, key):
    ss = sents(passage); i = next((k for k, s in enumerate(ss) if key[:50].lower() in s.lower()), None)
    if i is None: return None
    return " ".join(ss[max(0, i - 1):i + 2])
def overlap(opt, passage):
    w = set(words(opt)); p = set(words(passage)); return len(w & p) / max(1, len(w))
HEDGE = {"usually", "can", "may", "often", "sometimes", "generally", "mostly"}
drop = collections.Counter()

def ok(ans, wrong, passage):
    allo = [ans] + wrong; wl = [len(words(o)) for o in allo]
    if max(wl) - min(wl) > 4: drop["H5 length spread > 4 words"] += 1; return False
    if len(words(ans)) > max(len(words(w)) for w in wrong): drop["H5 key is the longest option"] += 1; return False
    ovs = [overlap(o, passage) for o in allo]
    if ovs[0] - max(ovs[1:]) >= 0.4: drop["H5 only the key copies passage wording"] += 1; return False
    first_up = lambda o: o[:1].isupper()
    if len({first_up(o) for o in allo}) > 1: drop["H5 capitalisation style differs"] += 1; return False
    if (words(ans)[0] in HEDGE) != any(words(w)[0] in HEDGE for w in wrong) and words(ans)[0] in HEDGE: drop["H5 only key has a hedge"] += 1; return False
    return True

def norm(o): return o.strip().rstrip(".").strip()

for sp in ("train", "val", "test"):
    kept = 0; tot = 0; out = []
    for line in open(BASE + f"opts/{sp}.jsonl", encoding="utf8"):
        r = json.loads(line); tot += 1
        u = r["messages"][1]["content"]
        m = re.match(r"Passage:\n(.*)\nKey sentence: (.*)\nQuestion: (.*)\nCorrect answer: (.*)$", u, re.S)
        if not m: drop["could not parse"] += 1; continue
        passage, key, q, ans = m.groups(); wrong = [norm(w) for w in r["ref_wrong"]]; ans = norm(ans)
        if not ok(ans, wrong, passage): continue
        win = window(passage, key)
        if not win: drop["key sentence not found"] += 1; continue
        user = f"Text: {win}\nKey sentence: {key}\nQuestion: {q}\nCorrect answer: {ans}"
        asst = "Wrong answers:\n" + "\n".join(f"{i+1}) {w}" for i, w in enumerate(wrong))
        out.append({"messages": [{"role": "system", "content": W_SYSTEM}, {"role": "user", "content": user}, {"role": "assistant", "content": asst}],
                    "topic": r["topic"]})
    with open(OUT + f"{sp}.jsonl", "w", encoding="utf8") as f:
        for o in out: f.write(json.dumps(o) + "\n")
    print(sp, "kept", len(out), "of", tot)
print("dropped:"); [print(f"  {v:5d}  {k}") for k, v in drop.most_common()]
