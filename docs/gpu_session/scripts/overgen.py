import json,re,torch,random,sys;sys.stdout.reconfigure(encoding="utf-8")
P="C:/Users/Arush/gpu-train/"
src=open(P+"cmp/bench.py",encoding="utf8").read().split("items=[]")[0]   # reuse prompts, load/gen helpers
exec(src)
def pickW(ans,cands):
    pool=[]
    for c in cands:
        c=norm(c)
        if not c or len(c.split())>14 or BAD.search(c) or jac(c,ans)>=0.6 or any(jac(c,q)>=0.6 for q in pool): continue
        pool.append(c)
    if len(pool)<3: return None
    la=len(ans.split());pool.sort(key=lambda c:(abs(len(c.split())-la)/max(la,1),c.split()[0].lower()!=ans.split()[0].lower()));return pool[:3]
def score(r,key,passage):
    s=0;q,ans,opts=r["q"],r["ans"],r["opts"];wrong=[o for o in opts if o!=ans]
    if re.match(r"(why|how|what happens|which (explains|example)|what is the difference|what would|what might|what will)",q.strip().lower()): s+=2
    aw=[x for x in w(ans) if len(x)>3]
    if aw and len(set(aw)&w(key))/len(aw)>=0.5: s+=1
    if aw and len(set(aw)&w(q))/len(aw)>=0.6: s-=2
    L=[len(o.split()) for o in opts]
    if not(len(ans.split())>=max(L) and L.count(max(L))==1): s+=1
    if any(jac(o,key)>=0.5 or jac(o,ans)>=0.5 for o in wrong): s-=3
    s-=sum(len(o.split())>10 for o in opts)
    if re.search(r"which of (the following|these)|according to the (passage|text)",q.lower()): s-=2
    return s+(2 if r.get("agree") else 0)
m=load(P+"final-training/out/job-both/merged");random.seed(7);torch.manual_seed(7);out=[]
passages=[json.loads(l) for l in open(P+"nammaai/repo/data/passages/eval/passages.jsonl",encoding="utf8")]
for pr in passages:
    ss=sents(pr["text"]);cand=[i for i,s in enumerate(ss) if len(s.split())>=10]
    if len(cand)<3: continue
    pos=sorted({cand[int(k*(len(cand)-1)/5)] for k in range(6)})            # up to 6 spaced key sentences
    base={cand[len(cand)//6],cand[len(cand)//2],cand[-2 if len(cand)>3 else -1]}  # the 3 used in the earlier benchmark
    res=[]
    for i in pos:
        user="Text: "+" ".join(ss[max(0,i-1):i+2])+"\nKey sentence: "+ss[i];qa=[]
        for _ in range(2):
            t=gen(m,Q_SYS,user)[0];q=re.search(r"^Question:\s*(.+)$",t,re.M);a=re.search(r"^Answer:\s*(.+)$",t,re.M)
            if q and a: qa.append((q.group(1).strip(),norm(a.group(1))))
        if not qa: continue
        wu=user+f"\nQuestion: {qa[0][0]}\nCorrect answer: {qa[0][1]}";cands=[];ws=None
        for _ in range(2):
            for t in gen(m,W_SYS,wu,n=2,temp=0.8,mx=90): cands+=re.findall(r"^\d\) (.+?)\s*$",t.split("\n\n")[0],re.M)
            ws=pickW(qa[0][1],cands)
            if ws: break
        if not ws: continue
        o=ws+[qa[0][1]];random.shuffle(o)
        r={"q":qa[0][0],"ans":qa[0][1],"opts":o,"agree":len(qa)>1 and jac(qa[0][1],qa[1][1])>=0.5,"idx":i,"key":ss[i]}
        r["score"]=score(r,ss[i],pr["text"]);r["base"]=i in base;res.append(r)
    out.append({"pid":pr["id"],"passage":pr["text"],"res":res});print(pr["id"],len(res),flush=True)
json.dump(out,open(P+"cmp/overgen_out.json","w"),indent=1)
