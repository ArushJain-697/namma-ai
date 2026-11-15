import json,re,torch,random,sys
sys.argv=['x']
exec(open(r'C:\Users\Arush\gpu-train\cmp\cmp3.py').read().split("torch.manual_seed(0)")[0])
m=load("qwen3-1.7b")
bad=[];good=[]
for r in rows:
    outs=gens(m,r,6,True)
    (good if any(valid(x) for x in outs) else bad).append((r,outs))
print("good",len(good),"bad",len(bad))
for r,outs in bad[:3]:
    print("\n#### FAIL | kind",r["kind"],"|",r["messages"][1]["content"][:130].replace("\n"," "));print(outs[0]);print("--");print(outs[1])
for r,outs in good[:4]:
    v=[x for x in outs if valid(x)][0];print("\n#### OK |",r["messages"][1]["content"][:130].replace("\n"," "));print(v)

