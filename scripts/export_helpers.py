#!/usr/bin/env python3
"""Export the misconception-mapping helper models to ExecuTorch (.pte) for the Pi, and check them against PyTorch.

  .venv-ml/bin/python scripts/export_helpers.py [--embed MODEL_OR_PATH] [--nli MODEL] [--seq 128]

Writes models/helpers/{embed,nli}/model.pte + tokenizer.json + meta.json. Plain fp32 XNNPACK graphs with no custom
ops, so the same files run on the Pi 5 and on older ARM chips (Cortex-A53). Sequences are padded to a fixed length.
"""
import argparse
import json
import os

import numpy as np
import torch

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "models", "helpers")


class EmbedWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.m = model

    def forward(self, input_ids, attention_mask):
        h = self.m(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0]  # CLS pooling (bge)
        return torch.nn.functional.normalize(h, dim=-1)


class ClsWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.m = model

    def forward(self, input_ids, attention_mask):
        return self.m(input_ids=input_ids, attention_mask=attention_mask).logits


def lower(module, example, path):
    from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner
    from executorch.exir import to_edge_transform_and_lower
    ep = torch.export.export(module.eval(), example, strict=False)
    prog = to_edge_transform_and_lower(ep, partitioner=[XnnpackPartitioner()]).to_executorch()
    with open(path, "wb") as f:
        f.write(prog.buffer)
    return os.path.getsize(path)


def export(kind, name, seq):
    from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name)
    d = os.path.join(OUT, kind)
    os.makedirs(d, exist_ok=True)
    if kind == "embed":
        model = EmbedWrapper(AutoModel.from_pretrained(name, attn_implementation="eager"))
        texts = [("Plants respire all the time, day and night.",), ("Plants only respire at night.",)]
    else:
        hf = AutoModelForSequenceClassification.from_pretrained(name, attn_implementation="eager")
        model = ClsWrapper(hf)
        texts = [("Plants respire all the time, day and night.", "Plants only respire at night."),
                 ("Plants respire all the time, day and night.", "Plants respire during the day.")]
    enc = tok(*zip(*texts), padding="max_length", truncation=True, max_length=seq, return_tensors="pt")
    example = (enc["input_ids"][:1], enc["attention_mask"][:1])
    size = lower(model, example, os.path.join(d, "model.pte"))
    tok.backend_tokenizer.save(os.path.join(d, "tokenizer.json")) if hasattr(tok, "backend_tokenizer") else tok.save_pretrained(d)
    meta = {"source": name, "seq": seq, "kind": kind}
    if kind == "nli":
        meta["id2label"] = {int(k): v for k, v in hf.config.id2label.items()}
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)

    # parity check: PyTorch vs ExecuTorch on the examples
    from executorch.runtime import Runtime
    method = Runtime.get().load_program(os.path.join(d, "model.pte")).load_method("forward")
    with torch.no_grad():
        ref = model(enc["input_ids"], enc["attention_mask"]).numpy()
    got = np.concatenate([method.execute([enc["input_ids"][i:i + 1], enc["attention_mask"][i:i + 1]])[0].numpy()
                          for i in range(len(texts))])
    print(f"{kind}: {name} -> {size / 1e6:.0f} MB, max |torch - pte| = {np.abs(ref - got).max():.2e}")
    print("   pte output:", np.round(got[:, :3] if kind == "embed" else got, 3).tolist())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--embed", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--nli", default="cross-encoder/nli-MiniLM2-L6-H768")
    ap.add_argument("--seq", type=int, default=128)
    ap.add_argument("--only", choices=["embed", "nli"])
    a = ap.parse_args()
    if a.only != "nli":
        export("embed", a.embed, a.seq)
    if a.only != "embed":
        export("nli", a.nli, a.seq)


if __name__ == "__main__":
    main()
