import json,re,torch,random
from transformers import AutoTokenizer,AutoModelForCausalLM
from peft import PeftModel
R="C:/Users/Arush/gpu-train/final-training/"
rows=[json.loads(l) for l in open(R+"data/val.jsonl")]
rows=[r for r in rows if r["source"]=="opus"];random.seed(1);random.shuffle(rows);rows=rows[:40]
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
def opts(t):
    o=dict(re.findall(r"^([ABCD])\) (.+?)\s*$",t,re.M));a=re.search(r"Answer: ([ABCD])",t);return o,(a.group(1) if a else None)
def toks(s): return set(re.findall(r"\w+",s.lower()))
def jac(a,b): return len(a&b)/max(1,len(a|b))
def valid(t):
    o,a=opts(t)
    if len(o)!=4 or not a or "Question:" not in t: return False
    v=[x.lower().strip(" .") for x in o.values()]
    if len(set(v))<4: return False
    # no option containing another entirely (near-dup)
    return True
def gens(m,r,n,sample):
    p=tok.apply_chat_template(r["messages"][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda")
    kw=dict(do_sample=True,temperature=0.7,top_p=0.9,num_return_sequences=n) if sample else dict(do_sample=False)
    o=m.generate(**i,max_new_tokens=150,**kw)
    return [tok.decode(x[i.input_ids.shape[1]:],skip_special_tokens=True).strip() for x in o]
def score(outs):
    sim=[]
    for g,r in outs:
        o,a=opts(g);ro,ra=opts(r["messages"][2]["content"]);rw=[toks(v) for k,v in ro.items() if k!=ra]
        sim+= [max(jac(toks(v),x) for x in rw) for k,v in o.items() if k!=a]
    return sum(sim)/max(1,len(sim))
def load(n):
    if n=="v1":
        m=AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B",torch_dtype=torch.bfloat16).to("cuda");return PeftModel.from_pretrained(m,R+"start/v1_adapter").merge_and_unload().eval()
    return AutoModelForCausalLM.from_pretrained(R+"out/"+n+"/merged",torch_dtype=torch.bfloat16).to("cuda").eval()
torch.manual_seed(0)
for n in ["qwen3-1.7b"]:
    m=load(n);gv=0;fv=0;picked=[]
    for r in rows:
        g=gens(m,r,1,False)[0];gv+=valid(g)
        c=[x for x in gens(m,r,6,True) if valid(x)]
        if c: fv+=1;picked.append((c[0],r))
    print(n,"| greedy valid %d/40 | with 6-sample filter: %d/40 get a valid question | wrong-option overlap w/ reference %.2f"%(gv,fv,score(picked)))
    del m;torch.cuda.empty_cache()
