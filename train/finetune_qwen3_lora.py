#!/usr/bin/env python3
"""LoRA fine-tune of Qwen3-0.6B (or 1.7B) for diagnostic questions. Run on a GPU (Colab T4 is enough).

  pip install -r train/requirements.txt
  python train/finetune_qwen3_lora.py --train data/dataset/train.jsonl --val data/dataset/val.jsonl --out out/qwen3-diag

Recipe (from reports/Diagnostic MCQ small model design.md): plain LoRA, 16-bit base (NOT 4-bit QLoRA: Qwen3-0.6B
is unusually sensitive to 4-bit), rank 32, alpha 32, dropout 0.05, all linear layers, lr 2e-4 cosine, 5% warmup,
2 epochs, effective batch 16, max length 2048, loss on the answer only.
The prompt is rendered with the repo's own chat_prompt(), the exact function the device uses, so training and
inference see byte-identical text (Qwen3 chat format with thinking switched off).
At the end the adapter is MERGED into the base and saved in 16-bit to OUT/merged, ready for ExecuTorch export.
"""
import argparse
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.backends.base import chat_prompt  # noqa: E402  (same prompt as the device)

END = "<|im_end|>"


def load(path, fmt):
    rows = []
    for line in open(path, encoding="utf-8"):
        m = json.loads(line)["messages"]
        system, user, answer = m[0]["content"], m[1]["content"], m[2]["content"]
        rows.append({"prompt": chat_prompt(fmt, system, user), "completion": answer + END})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/dataset/train.jsonl")
    ap.add_argument("--val", default="data/dataset/val.jsonl")
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--out", default="out/qwen3-0.6b-diag")
    ap.add_argument("--epochs", type=float, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--batch", type=int, default=4, help="per-device batch; gradient accumulation makes it 16")
    ap.add_argument("--max-len", type=int, default=2048)
    ap.add_argument("--limit", type=int, help="use only N training rows (quick smoke test)")
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16 if bf16 else torch.float16)
    train = load(args.train, "qwen3")[: args.limit]
    val = load(args.val, "qwen3")
    print(f"{len(train)} train, {len(val)} val examples")
    print("--- example prompt ---\n" + train[0]["prompt"][-400:] + "\n--- example completion ---\n" + train[0]["completion"])

    cfg = SFTConfig(
        output_dir=args.out, num_train_epochs=args.epochs, learning_rate=args.lr, lr_scheduler_type="cosine",
        warmup_ratio=0.05, per_device_train_batch_size=args.batch, per_device_eval_batch_size=args.batch,
        gradient_accumulation_steps=max(1, 16 // args.batch), weight_decay=0.01, max_length=args.max_len,
        completion_only_loss=True, bf16=bf16, fp16=not bf16, gradient_checkpointing=True, logging_steps=10,
        eval_strategy="steps", eval_steps=50, save_strategy="steps", save_steps=50, save_total_limit=2,
        load_best_model_at_end=True, metric_for_best_model="eval_loss", report_to="none", seed=3407)
    lora = LoraConfig(r=args.rank, lora_alpha=args.rank, lora_dropout=0.05, target_modules="all-linear",
                      bias="none", task_type="CAUSAL_LM")
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(train),
                         eval_dataset=Dataset.from_list(val), processing_class=tok, peft_config=lora)

    # Check the loss really covers only the answer: decode the trained tokens of one example.
    batch = trainer.data_collator([trainer.train_dataset[0]])
    labels = batch["labels"][0]
    print("--- tokens that carry loss (should be the JSON answer only) ---\n"
          + tok.decode([t for t in labels.tolist() if t != -100])[:400])

    trainer.train()
    trainer.save_model(os.path.join(args.out, "adapter"))
    print("best eval loss:", trainer.state.best_metric)

    merged = trainer.model.merge_and_unload()
    merged = merged.to(torch.bfloat16)
    mdir = os.path.join(args.out, "merged")
    merged.save_pretrained(mdir, safe_serialization=True)
    tok.save_pretrained(mdir)
    print(f"merged 16-bit model saved to {mdir}")

    # A few greedy generations on validation prompts, to eyeball before exporting.
    merged.eval()
    for row in val[:3]:
        ids = tok(row["prompt"], return_tensors="pt").to(merged.device)
        out = merged.generate(**ids, max_new_tokens=220, do_sample=False)
        print("\n--- sample ---\n" + tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))


if __name__ == "__main__":
    main()
