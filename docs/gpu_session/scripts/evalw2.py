import json,re,torch,sys
from transformers import AutoTokenizer,AutoModelForCausalLM
P="C:/Users/Arush/gpu-train/"
rows=[json.loads(l) for l in open(P+"for-gpu-claude/two_job_data/val_W.jsonl",encoding="utf8")]
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
w=lambda s:set(re.findall(r"\w+",s.lower()))
jac=lambda a,b:len(w(a)&w(b))/max(1,len(w(a)|w(b)))
def parse(t): return re.findall(r"^\d\) (.+?)\s*$",t.split("\n\n")[0],re.M)
def norm(x): return x.strip().rstrip(".").strip()
BAD=re.compile(r"\b(all|none|both)\b.*\b(above|these)\b",re.I)
def pick(ans,cands):
    pool=[]
    for c in cands:
        c=norm(c)
        if not c or len(c.split())>14 or BAD.search(c) or jac(c,ans)>=0.6 or any(jac(c,p)>=0.6 for p in pool): continue
        pool.append(c)
    if len(pool)<3: return None
    la=len(ans.split())
    pool.sort(key=lambda c:(abs(len(c.split())-la)/max(la,1), (c.split()[0].lower()!=ans.split()[0].lower())))
    return pool[:3]
def run(m,n_calls):
    st=dict(ok=0,longest=0,ov=[]);ex=[]
    for r in rows:
        ans=norm(re.search(r"Correct answer: (.*)$",r["messages"][1]["content"]).group(1))
        ref=parse(r["messages"][2]["content"])
        p=tok.apply_chat_template(r["messages"][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)
        i=tok(p,return_tensors="pt").to("cuda")
        o=m.generate(**i,max_new_tokens=90,do_sample=True,temperature=0.8,top_p=0.9,num_return_sequences=n_calls)
        cands=[x for s in o for x in parse(tok.decode(s[i.input_ids.shape[1]:],skip_special_tokens=True))]
        ws=pick(ans,cands)
        if not ws: continue
        st["ok"]+=1;st["longest"]+=len(ans.split())>max(len(x.split()) for x in ws)
        st["ov"]+=[max(jac(x,y) for y in ref) for x in ws]
        if len(ex)<3 and r is rows[[3,40,90][len(ex)]]: ex.append((r["messages"][1]["content"][-160:].replace("\n"," | "),ans,ws))
    st["ov"]=round(sum(st["ov"])/max(1,len(st["ov"])),3);return st,ex
for n in sys.argv[1:]:
    m=AutoModelForCausalLM.from_pretrained(P+f"final-training/out/{n}/merged",torch_dtype=torch.bfloat16).to("cuda").eval()
    torch.manual_seed(0)
    for calls in (2,4):
        st,ex=run(m,calls);print(n,"calls",calls,"-> got 3 distinct options for %d/156 | key longest %d | overlap with ref %.3f"%(st["ok"],st["longest"],st["ov"]))
    if n=="job-both":
        for u,a,ws in ex: print("\n",u,"\n ANSWER:",a,"\n WRONG:",ws)
    del m;torch.cuda.empty_cache()
