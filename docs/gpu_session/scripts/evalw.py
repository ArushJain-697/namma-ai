import json,re,torch,sys
from transformers import AutoTokenizer,AutoModelForCausalLM
P="C:/Users/Arush/gpu-train/"
rows=[json.loads(l) for l in open(P+"for-gpu-claude/two_job_data/val_W.jsonl",encoding="utf8")]
tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
w=lambda s:set(re.findall(r"\w+",s.lower()))
jac=lambda a,b:len(w(a)&w(b))/max(1,len(w(a)|w(b)))
def parse(t):
    o=re.findall(r"^\d\) (.+?)\s*$",t,re.M);return o if len(o)>=3 else None
def gen(m,r):
    p=tok.apply_chat_template(r["messages"][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    i=tok(p,return_tensors="pt").to("cuda");o=m.generate(**i,max_new_tokens=90,do_sample=False)
    t=tok.decode(o[0][i.input_ids.shape[1]:],skip_special_tokens=True).strip()
    return t.split("\n\n")[0]
res={}
for n in sys.argv[1:]:
    m=AutoModelForCausalLM.from_pretrained(P+f"final-training/out/{n}/merged",torch_dtype=torch.bfloat16).to("cuda").eval()
    st=dict(valid=0,dup=0,copyans=0,longest=0,ov=[]);outs=[]
    for r in rows:
        ans=re.search(r"Correct answer: (.*)$",r["messages"][1]["content"]).group(1).strip()
        ref=[x for x in parse(r["messages"][2]["content"])]
        o=gen(m,r);outs.append(o);ws=parse(o)
        if not ws or len(ws)<3: continue
        ws=ws[:3];st["valid"]+=1
        allo=[ans]+ws
        if any(jac(allo[i],allo[j])>=0.6 for i in range(4) for j in range(i+1,4)): st["dup"]+=1
        if any(jac(x,ans)>=0.6 for x in ws): st["copyans"]+=1
        if len(ans.split())>max(len(x.split()) for x in ws): st["longest"]+=1
        st["ov"]+= [max(jac(x,y) for y in ref) for x in ws]
    st["ov"]=sum(st["ov"])/max(1,len(st["ov"]));res[n]=(st,outs);del m;torch.cuda.empty_cache()
    print(n,{k:(round(v,3) if isinstance(v,float) else v) for k,v in st.items()},"of",len(rows))
n=sys.argv[1]
for k in (3,40,90):
    print("\nUSER:",rows[k]["messages"][1]["content"][-230:].replace("\n"," | "));print("REF:",rows[k]["messages"][2]["content"].replace("\n"," "));
    for n in res: print(n,":",res[n][1][k].replace("\n"," "))
