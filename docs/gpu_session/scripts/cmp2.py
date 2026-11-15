import json,re,torch,random
from transformers import AutoTokenizer,AutoModelForCausalLM
from peft import PeftModel
R="C:/Users/Arush/gpu-train/final-training/"
rows=[json.loads(l) for l in open(R+"data/val.jsonl")]
rows=[r for r in rows if r["source"]=="opus"]
random.seed(1);random.shuffle(rows);rows=rows[:40]
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
def gen(m,r):
    p=tok.apply_chat_template(r["messages"][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda")
    o=m.generate(**i,max_new_tokens=150,do_sample=False)
    return tok.decode(o[0][i.input_ids.shape[1]:],skip_special_tokens=True).strip()
pat=re.compile(r"^Question: .+\nA\) .+\nB\) .+\nC\) .+\nD\) .+\nAnswer: [ABCD]$")
res={}
for name in ["v1","new"]:
    if name=="v1":
        m=AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B",torch_dtype=torch.bfloat16).to("cuda")
        m=PeftModel.from_pretrained(m,R+"start/v1_adapter").merge_and_unload()
    else:
        m=AutoModelForCausalLM.from_pretrained(R+"out/qwen3-0.6b-final/merged",torch_dtype=torch.bfloat16).to("cuda")
    m.eval();res[name]=[gen(m,r) for r in rows];del m;torch.cuda.empty_cache()
def opts(t):
    o=dict(re.findall(r"^([ABCD])\) (.+?)\s*$",t,re.M)); a=re.search(r"Answer: ([ABCD])",t)
    return o,(a.group(1) if a else None)
def toks(s): return set(re.findall(r"\w+",s.lower()))
def jac(a,b): return len(a&b)/max(1,len(a|b))
for n in res:
    full=dup=n_ok=0;sim=[];ans_in_wrong=0
    for g,r in zip(res[n],rows):
        o,a=opts(g)
        if len(o)!=4 or a is None: continue
        n_ok+=1
        if len({v.lower() for v in o.values()})<4: dup+=1
        ro,ra=opts(r["messages"][2]["content"])
        rw=[toks(v) for k,v in ro.items() if k!=ra]
        for k,v in o.items():
            if k!=a: sim.append(max(jac(toks(v),x) for x in rw))
    print(n,"parsed",n_ok,"| questions with duplicate options",dup,"| avg best word-overlap of wrong options with reference wrong options %.2f"%(sum(sim)/len(sim)))
