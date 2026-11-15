import json,re,torch,random,sys
sys.path.insert(0,r"C:/Users/Arush/gpu-train/final-training")
from quiz_filter import parse as parseA,is_valid
from transformers import AutoTokenizer,AutoModelForCausalLM
P="C:/Users/Arush/gpu-train/"
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
w=lambda s:set(re.findall(r"\w+",s.lower()));jac=lambda a,b:len(w(a)&w(b))/max(1,len(w(a)|w(b)))
sents=lambda t:[s.strip() for s in re.split(r"(?<=[.!?])\s+",t.strip()) if s.strip()]
norm=lambda x:x.strip().rstrip(".").strip()
A_SYS="You write one multiple-choice question for a Class 6-10 student about the key sentence of a text. Exactly one option is correct and the text proves it. The three wrong options are the same kind of thing as the answer and sound believable, but the text shows they are wrong. Never use 'all of the above' or 'none of the above'. Use exactly this layout: Question, A) B) C) D), Answer."
Q_SYS=("You write one quiz question for a Class 6-10 student about the key sentence of a text, and its correct answer. Ask why, how or what happens, never a word to fill in. The text must prove the answer. Use exactly this layout: Question, Answer.")
W_SYS=("You write wrong answers for a quiz question for a Class 6-10 student. Each wrong answer is something a real student could believe (a common mistake or misconception), is clearly wrong according to the text, and is the same kind of answer, length and style as the correct answer. Never repeat the correct answer, never write 'all/none of the above'. Use exactly this layout: Wrong answers, 1) 2) 3).")
BAD=re.compile(r"\b(all|none|both)\b.*\b(above|these)\b",re.I)
def load(p): return AutoModelForCausalLM.from_pretrained(p,torch_dtype=torch.bfloat16).to("cuda").eval()
def gen(m,sysm,user,n=1,temp=0.7,mx=130):
    p=tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":user}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda");o=m.generate(**i,max_new_tokens=mx,do_sample=True,temperature=temp,top_p=0.9,num_return_sequences=n)
    return [tok.decode(s[i.input_ids.shape[1]:],skip_special_tokens=True).strip() for s in o]
items=[]
for l in open(P+"nammaai/repo/data/passages/eval/passages.jsonl",encoding="utf8"):
    r=json.loads(l);ss=sents(r["text"]);cand=[i for i,s in enumerate(ss) if len(s.split())>=10]
    if len(cand)<3: continue
    for i in (cand[len(cand)//6],cand[len(cand)//2],cand[-2 if len(cand)>3 else -1]):
        items.append({"pid":r["id"],"passage":r["text"],"key":ss[i],"user":"Text: "+" ".join(ss[max(0,i-1):i+2])+"\nKey sentence: "+ss[i]})
items=list({(x["pid"],x["key"]):x for x in items}.values());print("items",len(items))
def pickW(ans,cands):
    pool=[]
    for c in cands:
        c=norm(c)
        if not c or len(c.split())>14 or BAD.search(c) or jac(c,ans)>=0.6 or any(jac(c,q)>=0.6 for q in pool): continue
        pool.append(c)
    if len(pool)<3: return None
    la=len(ans.split());pool.sort(key=lambda c:(abs(len(c.split())-la)/max(la,1),c.split()[0].lower()!=ans.split()[0].lower()));return pool[:3]
random.seed(7);torch.manual_seed(7)
mA=load(P+"final-training/out/qwen3-0.6b-lr5e5/merged");A=[]
for it in items:
    got=None
    for _ in range(4):
        x=parseA(gen(mA,A_SYS,it["user"])[0])
        if is_valid(x): got=x;break
    A.append(None if not got else {"q":got["question"],"opts":list(got["options"].values()),"ans":got["options"][got["answer"]]})
del mA;torch.cuda.empty_cache()
mB=load(P+"final-training/out/job-both/merged");B=[]
for it in items:
    qa=None
    for _ in range(3):
        t=gen(mB,Q_SYS,it["user"])[0];q=re.search(r"^Question:\s*(.+)$",t,re.M);a=re.search(r"^Answer:\s*(.+)$",t,re.M)
        if q and a: qa=(q.group(1).strip(),norm(a.group(1)));break
    if not qa: B.append(None);continue
    wu=it["user"]+f"\nQuestion: {qa[0]}\nCorrect answer: {qa[1]}";ws=None;cands=[]
    for _ in range(2):
        for t in gen(mB,W_SYS,wu,n=2,temp=0.8,mx=90): cands+=re.findall(r"^\d\) (.+?)\s*$",t.split("\n\n")[0],re.M)
        ws=pickW(qa[1],cands)
        if ws: break
    if not ws: B.append(None);continue
    o=ws+[qa[1]];random.shuffle(o);B.append({"q":qa[0],"opts":o,"ans":qa[1]})
def metrics(R):
    ok=[(it,r) for it,r in zip(items,R) if r];n=len(R);m=dict(made=f"{len(ok)}/{n}",longest=0,spot=0,leak=0,why=0,gap=[],copy=0)
    for it,r in ok:
        L=[len(o.split()) for o in r["opts"]];m["longest"]+=len(r["ans"].split())>=max(L) and L.count(max(L))==1
        ov=[len(w(o)&w(it["passage"]))/max(1,len(w(o))) for o in r["opts"]];m["spot"]+=r["opts"][ov.index(max(ov))]==r["ans"]
        aw={x for x in w(r["ans"]) if len(x)>3};m["leak"]+=bool(aw) and len(aw&w(r["q"]))/len(aw)>=0.6
        m["why"]+=bool(re.match(r"(why|how|what happens|which (explains|example)|what is the difference|what would|what might|what will)",r["q"].strip().lower()))
        m["gap"].append(max(L)-min(L));m["copy"]+=jac(r["ans"],it["key"])>=0.8
    k=max(1,len(ok));return {"made":m["made"],"key longest %":round(100*m["longest"]/k),"word-spotting bot hit %":round(100*m["spot"]/k),"answer leaks into question %":round(100*m["leak"]/k),"why/how-style question %":round(100*m["why"]/k),"avg option length gap":round(sum(m["gap"])/k,1),"answer = whole key sentence %":round(100*m["copy"]/k)}
print("A (last time: single-call lr5e5 + filter):",metrics(A));print("B (now: job-both two-call + sampled W + dedupe):",metrics(B))
json.dump([{"it":{k:v for k,v in it.items() if k!="passage"},"A":a,"B":b} for it,a,b in zip(items,A,B)],open(P+"cmp/bench_out.json","w"),indent=1)
