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
ref=[r["messages"][2]["content"][-1] for r in rows]
for n in res:
    ok=sum(bool(pat.match(x)) for x in res[n]);ac=sum(x[-1:]==c for x,c in zip(res[n],ref))
    print(n,"format ok",ok,"/40; answer letter == reference",ac,"/40")
for k in [0,5,12,20]:
    print("\n=====",rows[k]["kind"],"\n",rows[k]["messages"][1]["content"][:300],"\n--v1--\n",res["v1"][k],"\n--new--\n",res["new"][k])
