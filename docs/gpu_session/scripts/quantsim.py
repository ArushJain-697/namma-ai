import sys,json,torch,re;sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0,r"C:/Users/Arush/gpu-train/final-training/src")
from sakshi.backends.base import chat_prompt
from transformers import AutoTokenizer,AutoModelForCausalLM
P="C:/Users/Arush/gpu-train/";tok=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
m=AutoModelForCausalLM.from_pretrained(P+"final-training/out/job-both/merged",torch_dtype=torch.bfloat16).to("cuda").eval()
orig={k:v.clone() for k,v in m.state_dict().items()}
rows=[json.loads(l) for l in open(P+"for-gpu-claude/two_job_data/val.jsonl",encoding="utf8")]
enc=[]
for r in rows:
    s,u,a=[x["content"] for x in r["messages"]];pi=tok(chat_prompt("qwen3",s,u),add_special_tokens=False)["input_ids"];ci=tok(a+"<|im_end|>",add_special_tokens=False)["input_ids"]
    enc.append((r["job"],pi,ci))
def fq_w(w,bits,group):            # symmetric group-wise weight fake-quant along input dim
    o,i=w.shape;qmax=2**(bits-1)-1;g=w.float().reshape(o,i//group,group) if group else w.float().reshape(o,1,i)
    s=g.abs().amax(-1,keepdim=True).clamp(min=1e-8)/qmax;return ((g/s).round().clamp(-qmax-1,qmax)*s).reshape(o,i).to(w.dtype)
def a8_hook(mod,args):             # dynamic per-token int8 activation fake-quant
    x=args[0].float();s=x.abs().amax(-1,keepdim=True).clamp(min=1e-8)/127;return ((x/s).round().clamp(-128,127)*s).to(args[0].dtype),
def apply(cfg):
    m.load_state_dict(orig);hs=[]
    emb=cfg.get("emb")
    if emb: m.model.embed_tokens.weight.data=fq_w(m.model.embed_tokens.weight.data,emb,0)   # row-wise (per token) 8-bit; tied lm_head shares it
    L=len(m.model.layers)
    for li,layer in enumerate(m.model.layers):
        hi=li in cfg.get("hi_layers",())
        for name,mod in list(layer.self_attn.named_children())+list(layer.mlp.named_children()):
            if isinstance(mod,torch.nn.Linear) and cfg.get("wbits"):
                b=8 if (hi or (cfg.get("hi_mods") and name in cfg["hi_mods"])) else cfg["wbits"];g=0 if b==8 else cfg["group"]
                mod.weight.data=fq_w(mod.weight.data,b,g)
                if cfg.get("a8"): hs.append(mod.register_forward_pre_hook(a8_hook))
    return hs
@torch.no_grad()
def evaluate():
    tot={"Q":[0,0,0],"W":[0,0,0]}
    for job,pi,ci in enc:
        ids=torch.tensor([pi+ci],device="cuda");lg=m(ids).logits[0,len(pi)-1:-1].float()
        t=torch.tensor(ci,device="cuda");nll=torch.nn.functional.cross_entropy(lg,t,reduction="sum").item()
        tot[job][0]+=nll;tot[job][1]+=len(ci);tot[job][2]+=(lg.argmax(-1)==t).sum().item()
    return {j:(round(v[0]/v[1],4),round(100*v[2]/v[1],1)) for j,v in tot.items()}
cfgs=[("bf16 (what we tested so far)",{}),
 ("emb 8-bit only",{"emb":8}),
 ("w8 a8 + emb8",{"emb":8,"wbits":8,"group":0,"a8":True}),
 ("w4 g128 a8 + emb8",{"emb":8,"wbits":4,"group":128,"a8":True}),
 ("w4 g32 a8 + emb8  (= 8da4w default style)",{"emb":8,"wbits":4,"group":32,"a8":True}),
 ("w4 g32 a8 + emb8, down_proj at 8-bit",{"emb":8,"wbits":4,"group":32,"a8":True,"hi_mods":("down_proj",)}),
 ("w4 g32 a8 + emb8, first2+last2 layers 8-bit",{"emb":8,"wbits":4,"group":32,"a8":True,"hi_layers":(0,1,26,27)}),
 ("w4 g32 a8 + emb8, down_proj + first/last layers 8-bit",{"emb":8,"wbits":4,"group":32,"a8":True,"hi_mods":("down_proj",),"hi_layers":(0,1,26,27)}),
 ("w4 g32, activations NOT quantised + emb8",{"emb":8,"wbits":4,"group":32,"a8":False})]
print("avg answer-token loss and top-1 token accuracy %, per job (Q = question+answer, W = wrong options). Lower loss is better.")
for name,c in cfgs:
    hs=apply(c);r=evaluate();[h.remove() for h in hs];print(f"{name:60s} Q loss {r['Q'][0]} acc {r['Q'][1]} | W loss {r['W'][0]} acc {r['W'][1]}",flush=True)
