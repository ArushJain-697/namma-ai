import sys,copy;sys.path.insert(0,r"C:\Users\Arush\gpu-train\final-training")
exec(open(r"C:\Users\Arush\gpu-train\cmp\cmp3.py").read().split("torch.manual_seed(0)")[0])
from quiz_filter import parse,is_valid
rows=[json.loads(l) for l in open(R+"data/val.jsonl")];rows=[r for r in rows if r["source"]=="opus"]
HINT=" Each wrong option must be a different, specific mistake a student could really make about this text (for example a misread detail, a mix-up with a similar idea, or an over-generalisation). The wrong options must not repeat or rephrase each other."
def run(m,hint):
    torch.manual_seed(0);first=0;wo=[];rep=0
    for r in rows:
        msgs=copy.deepcopy(r["messages"][:2])
        if hint: msgs[0]["content"]+=HINT
        outs=gens2(m,msgs,6)
        its=[parse(t) for t in outs];first+=sum(bool(is_valid(x)) for x in its)
        v=[x for x in its if is_valid(x)]
        if v:
            ro,ra=opts(r["messages"][2]["content"]);rw=[toks(a) for k,a in ro.items() if k!=ra]
            wo+=[max(jac(toks(a),x) for x in rw) for k,a in v[0]["options"].items() if k!=v[0]["answer"]]
    return first/(6*len(rows)),sum(wo)/len(wo)
def gens2(m,msgs,n):
    p=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda")
    o=m.generate(**i,max_new_tokens=150,do_sample=True,temperature=0.7,top_p=0.9,num_return_sequences=n)
    return [tok.decode(x[i.input_ids.shape[1]:],skip_special_tokens=True).strip() for x in o]
m=load("qwen3-0.6b-lr5e5")
for h in (False,True): print("hint" if h else "no hint","| share of valid candidates %.2f | wrong-option overlap %.3f"%run(m,h))
