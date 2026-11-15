import sys;sys.path.insert(0,r"C:\Users\Arush\gpu-train\final-training")
exec(open(r"C:\Users\Arush\gpu-train\cmp\cmp3.py").read().split("torch.manual_seed(0)")[0])
from quiz_filter import parse,is_valid,_sim
rows=[json.loads(l) for l in open(R+"data/val.jsonl")];rows=[r for r in rows if r["source"]=="opus"]
def consensus(items):
    return max(items,key=lambda x:sum(_sim(x["options"][x["answer"]],y["options"][y["answer"]]) for y in items if y is not x))
def stats(picks):
    ca=[];wo=[]
    for it,r in picks:
        ro,ra=opts(r["messages"][2]["content"]);ca.append(_sim(it["options"][it["answer"]],ro[ra]))
        rw=[toks(v) for k,v in ro.items() if k!=ra]
        wo+= [max(jac(toks(v),x) for x in rw) for k,v in it["options"].items() if k!=it["answer"]]
    return sum(ca)/len(ca),sum(wo)/len(wo)
m=load("qwen3-0.6b-lr5e5")
for seed in (0,1):
    torch.manual_seed(seed);A=[];B=[]
    for r in rows:
        its=[x for x in (parse(t) for t in gens(m,r,4,True)) if is_valid(x)]
        if not its: continue
        A.append((its[0],r));B.append((consensus(its) if len(its)>1 else its[0],r))
    print("seed",seed,"n",len(A),"| first-valid: correct-answer match %.3f, wrong-opt overlap %.3f"%stats(A),"| consensus: %.3f, %.3f"%stats(B))
