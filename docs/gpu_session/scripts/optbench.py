import json,re,torch,random,sys
from transformers import AutoTokenizer,AutoModelForCausalLM
P="C:/Users/Arush/gpu-train/"
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
w=lambda s:set(re.findall(r"\w+",s.lower()));jac=lambda a,b:len(w(a)&w(b))/max(1,len(w(a)|w(b)))
norm=lambda x:x.strip().rstrip(".").strip()
BAD=re.compile(r"\b(all|none|both)\b.*\b(above|these)\b",re.I)
W_SYS=("You write wrong answers for a quiz question for a Class 6-10 student. Each wrong answer is something a real student could believe (a common mistake or misconception), is clearly wrong according to the text, and is the same kind of answer, length and style as the correct answer. Never repeat the correct answer, never write 'all/none of the above'. Use exactly this layout: Wrong answers, 1) 2) 3).")
def load(p): return AutoModelForCausalLM.from_pretrained(p,torch_dtype=torch.bfloat16).to("cuda").eval()
def gen(m,user,n=2):
    p=tok.apply_chat_template([{"role":"system","content":W_SYS},{"role":"user","content":user}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda");o=m.generate(**i,max_new_tokens=90,do_sample=True,temperature=0.8,top_p=0.9,num_return_sequences=n)
    return [tok.decode(s[i.input_ids.shape[1]:],skip_special_tokens=True).strip() for s in o]
def pickW(ans,cands):
    pool=[]
    for c in cands:
        c=norm(c)
        if not c or len(c.split())>14 or BAD.search(c) or jac(c,ans)>=0.6 or any(jac(c,q)>=0.6 for q in pool): continue
        pool.append(c)
    if len(pool)<3: return None
    la=len(ans.split());pool.sort(key=lambda c:(abs(len(c.split())-la)/max(la,1),c.split()[0].lower()!=ans.split()[0].lower()));return pool[:3]
rows=[json.loads(l) for l in open(P+"for-gpu-claude/two_job_data/val_W.jsonl",encoding="utf8")]
rows=[r for r in rows if r["source"] in ("opus","sonnet")]          # teacher-written held-out questions only
print("teacher held-out questions:",len(rows))
random.seed(5);torch.manual_seed(5);mW=load(P+"final-training/out/job-both/merged");S=[]
for r in rows:
    u=r["messages"][1]["content"];ans=norm(re.search(r"Correct answer: (.*)$",u).group(1));q=re.search(r"Question: (.*)",u).group(1)
    text=re.search(r"Text: (.*?)\nKey sentence:",u,re.S).group(1);ref=[norm(x) for x in re.findall(r"^\d\) (.+?)\s*$",r["messages"][2]["content"],re.M)]
    c=[];ws=None
    for _ in range(2):
        for t in gen(mW,u): c+=re.findall(r"^\d\) (.+?)\s*$",t.split("\n\n")[0],re.M)
        ws=pickW(ans,c)
        if ws: break
    if ws and len(ref)==3: S.append((text,q,ans,ref,ws))
print("usable:",len(S));del mW;torch.cuda.empty_cache()
mJ=load(P+"q17");L=[tok.encode(x,add_special_tokens=False)[0] for x in "ABCD"]
def probs(text,q,opts):
    body=("Text: "+text+"\n" if text else "")+f"Question: {q}\n"+"\n".join(f"{'ABCD'[i]}) {o}" for i,o in enumerate(opts))+"\nAnswer with one letter."
    p=tok.apply_chat_template([{"role":"user","content":body}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda")
    with torch.no_grad(): lg=mJ(**i).logits[0,-1,L].float()
    return torch.softmax(lg,-1).tolist()
rnd=random.Random(9);res={"teacher options":dict(o=0,c=0,amb=0,pull=0),"model options (job-both, sampled+dedupe)":dict(o=0,c=0,amb=0,pull=0)}
for text,q,ans,ref,ws in S:
    for name,wrong in (("teacher options",ref),("model options (job-both, sampled+dedupe)",ws)):
        o=wrong+[ans];rnd.shuffle(o);k=o.index(ans);po=probs(text,q,o);pc=probs("",q,o)
        d=res[name];d["o"]+=po.index(max(po))==k;d["c"]+=pc.index(max(pc))==k
        d["amb"]+=(max(po)>0.6 and po.index(max(po))!=k)      # reader confidently picks a WRONG option -> 2nd correct or bad key
        d["pull"]+=max(pc[j] for j in range(4) if j!=k)>0.5   # a wrong option attracts a reader who never saw the passage
n=len(S)
for name,d in res.items(): print(f"{name}: reads passage -> picks key {100*d['o']/n:.0f}% | confident wrong pick (likely 2nd-correct/bad) {100*d['amb']/n:.0f}% | WITHOUT passage picks key {100*d['c']/n:.0f}% | a wrong option strongly attracts no-passage reader {100*d['pull']/n:.0f}%")
print("(chance for picking the key = 25%)")
