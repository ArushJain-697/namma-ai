#!/usr/bin/env python3
"""Fine-tune the misconception retriever (the Eedi-competition recipe) on our own teacher-labelled pairs.

  .venv-ml/bin/python train/finetune_retriever.py            # writes models/retriever-finetuned/

Training pairs come from data/dataset/raw/train: (evidence sentence -> each misconception its wrong options target).
Positives are the misconception's fix text and its belief text; hard negatives are other misconceptions of the SAME
topic (the hardest confusions). Loss: MultipleNegativesRankingLoss (in-batch + hard negatives). Test topics and
held-out misconceptions are never used. Base: BAAI/bge-small-en-v1.5 (33M parameters), a few minutes on a Mac.
"""
import json
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from sakshi.mapper import fix_text, mis_text  # noqa: E402
from sakshi.misconceptions import Library  # noqa: E402


def main():
    from datasets import Dataset
    from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                       SentenceTransformerTrainingArguments)
    from sentence_transformers.losses import MultipleNegativesRankingLoss
    from sentence_transformers.training_args import BatchSamplers

    lib = Library.load(include_held_out=False)
    by_topic = {}
    for m in lib.items:
        by_topic.setdefault(m["topic_id"], []).append(m)
    rng = random.Random(11)
    rows = []
    d = os.path.join(ROOT, "data", "dataset", "raw", "train")
    for f in sorted(os.listdir(d)):
        r = json.load(open(os.path.join(d, f), encoding="utf-8"))
        for it in r["response"].get("items", []) or []:
            gold = [o.get("belief_id") for o in it.get("options", []) or []]
            ev = it.get("evidence", "")
            if not ev or not all(g in lib.by_id for g in gold):
                continue
            negs = [m for m in by_topic.get(r["job"]["topic_id"], []) if m["id"] not in gold]
            for g in gold:
                m = lib.by_id[g]
                neg = rng.choice(negs) if negs else rng.choice(lib.items)
                rows.append({"anchor": ev, "positive": fix_text(m), "negative": fix_text(neg)})
                rows.append({"anchor": ev, "positive": mis_text(m), "negative": mis_text(neg)})
    rng.shuffle(rows)
    print(f"{len(rows)} training pairs")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    out = os.path.join(ROOT, "models", "retriever-finetuned")
    args = SentenceTransformerTrainingArguments(
        output_dir=out + "-ckpt", num_train_epochs=2, per_device_train_batch_size=64, learning_rate=3e-5,
        warmup_ratio=0.1, batch_sampler=BatchSamplers.NO_DUPLICATES, save_strategy="no", logging_steps=50,
        report_to="none", seed=11)
    trainer = SentenceTransformerTrainer(model=model, args=args, train_dataset=Dataset.from_list(rows),
                                         loss=MultipleNegativesRankingLoss(model))
    trainer.train()
    model.save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
