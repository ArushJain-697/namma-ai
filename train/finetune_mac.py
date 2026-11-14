#!/usr/bin/env python3
"""LoRA fine-tune of Qwen3-0.6B on an NVIDIA GPU (CUDA) or an Apple-silicon Mac (MPS), no trl needed. Same recipe as finetune_qwen3_lora.py
(LoRA on all linear layers, cosine lr 2e-4, loss on the answer only) and the SAME prompt text the device uses
(sakshi.backends.base.chat_prompt, Qwen3 format with thinking off). Merges the adapter at the end so the result
exports to ExecuTorch exactly like the base model.

  .venv-ml/bin/python train/finetune_mac.py --train data/dataset_mcq/train.jsonl --val data/dataset_mcq/val.jsonl \\
      --out out/qwen3-0.6b-mcq [--smoke 20]
Recipe sources: Gemini Deep Research "Small Model MCQ Generation" (13 Nov): rank 16-32, alpha 2x rank, all linear
modules, 2-3 epochs on 2-5k examples; reports/Diagnostic MCQ small model design.md (16-bit base, not 4-bit).
"""
import argparse
import json
import math
import os
import random
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.backends.base import chat_prompt  # noqa: E402

END = "<|im_end|>"


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        m = json.loads(line)["messages"]
        rows.append((chat_prompt("qwen3", m[0]["content"], m[1]["content"]), m[2]["content"] + END))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--val", required=True)
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--out", default="out/qwen3-0.6b-mcq")
    ap.add_argument("--epochs", type=float, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-len", type=int, default=448)
    ap.add_argument("--smoke", type=int, default=0, help="run only N steps and print the time per step")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
    ap.add_argument("--accum", type=int, default=1, help="gradient accumulation steps")
    ap.add_argument("--eval-every", type=int, default=100, help="held-out check every N steps; the best is kept")
    ap.add_argument("--start-adapter", default=None,
                    help="LoRA adapter merged into --model BEFORE training (continue from an earlier fine-tune)")
    a = ap.parse_args()

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dev = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print("device:", dev, torch.cuda.get_device_name(0) if dev == "cuda" else "")
    torch.manual_seed(3407)
    random.seed(3407)
    tok = AutoTokenizer.from_pretrained(a.model)
    from peft import PeftModel

    def load_start(dtype):
        m = AutoModelForCausalLM.from_pretrained(a.model, dtype=dtype)
        if a.start_adapter:  # e.g. version 1's adapter: recreate version 1, then train a new adapter on top
            m = PeftModel.from_pretrained(m, a.start_adapter).merge_and_unload()
            print(f"started from {a.model} + merged {a.start_adapter}")
        return m

    model = load_start(getattr(torch, a.dtype)).to(dev)
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, bias="none",
                                             task_type="CAUSAL_LM",
                                             target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                                             "gate_proj", "up_proj", "down_proj"]))
    model.print_trainable_parameters()

    def encode(rows):
        out = []
        for p, c in rows:
            pi, ci = tok(p, add_special_tokens=False)["input_ids"], tok(c, add_special_tokens=False)["input_ids"]
            ids = (pi + ci)[: a.max_len]
            lab = ([-100] * len(pi) + ci)[: a.max_len]
            out.append((ids, lab))
        return out

    train, val = encode(load(a.train)), encode(load(a.val))
    print(f"{len(train)} train, {len(val)} val; longest {max(len(x[0]) for x in train)} tokens")
    print("loss tokens of example 0:", repr(tok.decode([t for t in train[0][1] if t != -100])))

    def batches(data, shuffle):
        idx = list(range(len(data)))
        if shuffle:
            random.shuffle(idx)
        for b in range(0, len(idx), a.batch):
            chunk = [data[i] for i in idx[b: b + a.batch]]
            L = max(len(x[0]) for x in chunk)
            ids = torch.full((len(chunk), L), tok.pad_token_id, dtype=torch.long)
            lab = torch.full((len(chunk), L), -100, dtype=torch.long)
            att = torch.zeros((len(chunk), L), dtype=torch.long)
            for k, (x, y) in enumerate(chunk):
                ids[k, : len(x)], lab[k, : len(y)], att[k, : len(x)] = torch.tensor(x), torch.tensor(y), 1
            yield ids.to(dev), lab.to(dev), att.to(dev)

    inner = model.base_model.model  # Qwen3ForCausalLM (LoRA layers live inside .model)
    ce = torch.nn.CrossEntropyLoss()

    def answer_loss(ids, lab, att):
        """Next-token loss on the answer tokens only. Computing the 152k-word vocabulary scores for every prompt
        position (what model(labels=...) does) took ~2 GB per batch and pushed the Mac into swap."""
        h = inner.model(input_ids=ids, attention_mask=att).last_hidden_state[:, :-1]
        tgt = lab[:, 1:]
        keep = tgt != -100
        return ce(inner.lm_head(h[keep]).float(), tgt[keep])

    def val_loss():
        model.eval()
        tot = n = 0
        with torch.no_grad():
            for ids, lab, att in batches(val, False):
                tot += answer_loss(ids, lab, att).item()
                n += 1
        model.train()
        return tot / n

    steps_per_epoch = math.ceil(len(train) / a.batch)
    total = a.smoke or int(steps_per_epoch * a.epochs)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr, weight_decay=0.01)
    warm = max(1, int(0.05 * total))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / warm if s < warm else 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total - warm))))
    print(f"steps: {total} ({steps_per_epoch}/epoch), start val loss {val_loss():.3f}", flush=True)
    model.train()
    step, t0, best = 0, time.time(), 1e9
    os.makedirs(a.out, exist_ok=True)
    while step < total:
        for ids, lab, att in batches(train, True):
            loss = answer_loss(ids, lab, att)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if step % 20 == 0 or step == total or (a.smoke and step <= 5):
                el = time.time() - t0
                print(f"step {step}/{total} loss {loss.item():.3f} lr {sched.get_last_lr()[0]:.2e} "
                      f"{el / step:.2f} s/step, ~{(total - step) * el / step / 60:.0f} min left", flush=True)
            if not a.smoke and (step % a.eval_every == 0 or step == total):
                v = val_loss()
                print(f"  val loss {v:.3f}", flush=True)
                if v < best:
                    best = v
                    model.save_pretrained(os.path.join(a.out, "adapter"))
            if step >= total:
                break
    if a.smoke:
        print("smoke test done")
        return
    print(f"best val loss {best:.3f}; merging the best adapter")
    base = load_start(torch.float32)
    merged = PeftModel.from_pretrained(base, os.path.join(a.out, "adapter")).merge_and_unload().to(torch.bfloat16)
    mdir = os.path.join(a.out, "merged")
    merged.save_pretrained(mdir, safe_serialization=True)
    tok.save_pretrained(mdir)
    print(f"merged model saved to {mdir}")


if __name__ == "__main__":
    main()
