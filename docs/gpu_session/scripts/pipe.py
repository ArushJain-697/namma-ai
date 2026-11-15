import json,re,torch,random,sys
from transformers import AutoTokenizer,AutoModelForCausalLM
R="C:/Users/Arush/gpu-train/final-training/"
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
def toks(s): return set(re.findall(r"\w+",s.lower()))
def jac(a,b): a,b=toks(a),toks(b); return len(a&b)/max(1,len(a|b))
def parse(t):
    q=re.search(r"Question:\s*(.+)",t); o=dict(re.findall(r"^([ABCD])\) (.+?)\s*$",t,re.M)); a=re.search(r"Answer:\s*([ABCD])",t)
    if not q or not a or a.group(1) not in o: return None
    c=o[a.group(1)]; w=[v for k,v in o.items() if k!=a.group(1)]
    return q.group(1).strip(),c,w
def make_question(m,messages,n=8):
    p=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda")
    o=m.generate(**i,max_new_tokens=150,do_sample=True,temperature=0.8,top_p=0.9,num_return_sequences=n)
    ps=[x for x in (parse(tok.decode(s[i.input_ids.shape[1]:],skip_special_tokens=True)) for s in o) if x]
    if not ps: return None
    # pick question whose correct answer is most agreed-upon (consensus)
    best=max(ps,key=lambda p:sum(jac(p[1],x[1]) for x in ps))
    q,c,_=best
    pool=[]
    for x in ps:
        if jac(x[0],q)<0.25 and x is not best: continue   # only options written for a similar question
        for w in x[2]+([x[1]] if jac(x[1],c)<0.5 else []):
            if jac(w,c)<0.6 and all(jac(w,y)<0.6 for y in pool): pool.append(w)
    own=[w for w in best[2] if jac(w,c)<0.6]
    d=[]
    for w in own+pool:
        if all(jac(w,y)<0.6 for y in d) and jac(w,c)<0.6: d.append(w)
    if len(d)<3: return None
    d=d[:3]; opts=d+[c]; random.shuffle(opts)
    return q,opts,"ABCD"[opts.index(c)]
if __name__=="__main__":
    m=AutoModelForCausalLM.from_pretrained(R+"out/qwen3-0.6b-lr5e5/merged",torch_dtype=torch.bfloat16).to("cuda").eval()
    rows=[json.loads(l) for l in open(R+"data/val.jsonl")];rows=[r for r in rows if r["source"]=="opus"];random.seed(1);random.shuffle(rows);rows=rows[:40]
    ok=0;shown=0
    for r in rows:
        x=make_question(m,r["messages"][:2])
        if x:
            ok+=1
            if shown<5:
                shown+=1;print("\n",r["messages"][1]["content"][:200].replace("\n"," "),"\nQ:",x[0]);[print(" ","ABCD"[i]+")",o) for i,o in enumerate(x[1])];print("  Answer:",x[2])
    print("\nPIPELINE valid %d/40"%ok)
