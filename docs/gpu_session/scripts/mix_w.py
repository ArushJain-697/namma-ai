"""Gemini 'opts' data -> Job W rows in the teammate's EXACT format, minus held-out/eval topics, then mixed with teacher Job W."""
import json,re,random,sys
sys.path.insert(0,r"C:/Users/Arush/gpu-train/cmp")
src=open(r"C:/Users/Arush/gpu-train/cmp/convert_w.py",encoding="utf8").read()
# reuse helpers (words, window, ok, norm) from the converter without running its main loop
ns={}; exec(src.split('for sp in ("train", "val", "test"):')[0],ns)
W_SYSTEM=("You write wrong answers for a quiz question for a Class 6-10 student. Each wrong answer is something a "
          "real student could believe (a common mistake or misconception), is clearly wrong according to the text, "
          "and is the same kind of answer, length and style as the correct answer. Never repeat the correct answer, "
          "never write 'all/none of the above'. Use exactly this layout: Wrong answers, 1) 2) 3).")
P=r"C:/Users/Arush/gpu-train/"
held=json.load(open(P+"for-gpu-claude/heldout.json"))["heldout_teacher_passages"]
topic_of=lambda f:re.sub(r"^train-\d+-|\.json$","",f)
block={topic_of(f) for f in held}
for v in json.load(open(P+"nammaai/repo/data/passages/eval/expected_topics.json")).values(): block|=set(v)
rng=random.Random(55);out=[];skipped=0
for sp in ("train","val"):
    for line in open(P+f"nammaai/opts/{sp}.jsonl",encoding="utf8"):
        r=json.loads(line)
        if r["topic"] in block: skipped+=1;continue
        m=re.match(r"Passage:\n(.*)\nKey sentence: (.*)\nQuestion: (.*)\nCorrect answer: (.*)$",r["messages"][1]["content"],re.S)
        if not m: continue
        passage,key,q,ans=m.groups();wrong=[ns["norm"](w) for w in r["ref_wrong"]];ans=ns["norm"](ans)
        if not ns["ok"](ans,wrong,passage): continue
        ss=ns["sents"](passage);i=next((k for k,s in enumerate(ss) if key[:60] in s or s[:60] in key),None)
        if i is None: continue
        win=" ".join(ss[max(0,i-1):i+2]);rng.shuffle(wrong)
        out.append({"source":"gemini","kind":None,"passage_id":None,"wrong_misconceptions":None,"job":"W","messages":[
            {"role":"system","content":W_SYSTEM},
            {"role":"user","content":f"Text: {win}\nKey sentence: {ss[i]}\nQuestion: {q}\nCorrect answer: {ans}"},
            {"role":"assistant","content":"Wrong answers:\n"+"\n".join(f"{n}) {w}" for n,w in enumerate(wrong,1))}]})
print("gemini W rows kept:",len(out),"| skipped for held-out/eval topics:",skipped)
D=P+"for-gpu-claude/two_job_data/"
tw=[json.loads(l) for l in open(D+"train_W.jsonl",encoding="utf8")]
mix=tw+out;rng.shuffle(mix)
open(D+"train_W_mix.jsonl","w",encoding="utf8").write("".join(json.dumps(x)+"\n" for x in mix))
print("teacher W",len(tw),"+ gemini",len(out),"= mix",len(mix))
