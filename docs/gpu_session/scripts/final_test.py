import sys;sys.path.insert(0,r"C:\Users\Arush\gpu-train\final-training")
exec(open(r"C:\Users\Arush\gpu-train\cmp\cmp3.py").read().split("torch.manual_seed(0)")[0])
from quiz_filter import parse,is_valid
rows=[json.loads(l) for l in open(R+"data/val.jsonl")];rows=[r for r in rows if r["source"]=="opus"]
m=load("qwen3-0.6b-lr5e5");torch.manual_seed(0);hist=[];fails=0
for r in rows:
    n=0;ok=False
    while n<4 and not ok:
        n+=1;ok=is_valid(parse(gens(m,r,1,True)[0]))
    hist.append(n if ok else 0)
print("passages",len(rows),"| valid within 4 tries:",sum(h>0 for h in hist),"| tries needed:",hist)
