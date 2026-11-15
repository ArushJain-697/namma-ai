# Train the quiz model on this NVIDIA GPU (hand this file + the zip to Claude Code)

Say to Claude Code: **"Read TRAIN_ON_GPU.md and do it step by step. Don't change the data or the training recipe."**

## Context (what this is)
Hackathon project (Namma AI, 14 Nov 2026): an offline quiz maker that runs on a Raspberry Pi with the small model
**Qwen3-0.6B**. We teach it to write good multiple-choice questions by fine-tuning it with **LoRA** (small add-on
weights, ~10M of 600M parameters). We already trained **version 1** on 4,300 SciQ/RACE questions (it learned the
clean 4-option format); its adapter is in `start/v1_adapter/`. This run **starts from version 1** (the script merges
that adapter into Qwen first) and trains a new adapter on:
- 905 questions written by Claude Opus/Sonnet for school passages and graded 4-5/5 by a separate grader (the
  "why / how / what happens if" style we want);
- 300 RACE questions as a "reminder" so version 1's format skills are not forgotten.
Curated on purpose (small + clean beats big; LIMA): 1,205 examples, near-duplicates and giveaway items removed,
question types balanced, answer letters balanced, no example repeated.
The data is ready in `data/`. Your job: **train once, check it worked, send back the small adapter folder.**
The main team converts it for the Raspberry Pi on their Mac. You do not need ExecuTorch or a Pi.

## 1. Check the GPU (2 min)
```bash
nvidia-smi
```
Note the GPU name and memory (expected: RTX 4080, ~8 GB; it supports bfloat16, so no `--dtype` change is needed). If `nvidia-smi` fails, the NVIDIA driver is missing: stop and tell
the human.

## 2. Python environment (10 min)
Needs Python 3.10-3.12 and internet (to install packages and download Qwen/Qwen3-0.6B, ~1.2 GB, once).
```bash
cd final-training
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
The last line must print `True` and the GPU name. If it prints `False`, the CUDA torch build does not match the
driver: try `--index-url https://download.pytorch.org/whl/cu121` (older drivers) or `cu126`, then re-check.

## 3. Quick smoke test (2 min): proves memory and speed are fine
```bash
python train/finetune.py --model Qwen/Qwen3-0.6B --start-adapter start/v1_adapter --train data/train.jsonl \
    --val data/val.jsonl --out out/smoke --smoke 20 --batch 8
```
Expect `device: cuda <GPU name>`, `started from Qwen/Qwen3-0.6B + merged start/v1_adapter`, a starting val loss
around 1.5-2.0, and lines like
`step 5/20 ... 0.4 s/step`. If you see **CUDA out of memory**: rerun with `--batch 4` (and use `--batch 4` below too).
If the GPU is older (GTX 10xx/16xx, RTX 20xx) and you see a bfloat16 error: add `--dtype float32` everywhere.

## 4. Real training (~5-15 min on an RTX 4080)
```bash
python train/finetune.py --model Qwen/Qwen3-0.6B --start-adapter start/v1_adapter --train data/train.jsonl \
    --val data/val.jsonl --out out/qwen3-0.6b-final --batch 8 --epochs 2 --lr 1e-4 --rank 16 --eval-every 50 2>&1 | tee out/train_final.log
```
(Same `--batch`/`--dtype` changes as the smoke test if you needed them.)
- It prints progress every 20 steps and a `val loss` every 50 steps on held-out questions (from passages it never
  trains on). Only the version with the BEST val loss is saved, so if the model starts memorising (val loss going
  back up), the later worse version is not kept. That is the guard against overfitting; do not add more epochs. (Settings checked against the Unsloth LoRA guide:
  1-3 epochs, lr 1e-4-2e-4, rank 16 / alpha 32 on all linear layers.)
- At the end it prints `best val loss ...` and `merged model saved to out/qwen3-0.6b-final/merged`.
- Good sign: val loss ends clearly below the starting value (e.g. 1.8 -> about 1.3-1.4; an earlier Mac run on
  part of this data reached 1.38).

## 5. Send back (small)
Only the NEW adapter (~40 MB) and the log (the main team merges version 1 + this adapter on their side):
```bash
cd out/qwen3-0.6b-final && zip -r ../../trained-adapter.zip adapter && cd ../.. && zip -j trained-adapter.zip out/train_final.log
```
Send `trained-adapter.zip` to the human. (The `merged` folder is 1.2 GB; only send it if they ask.)

## Rules
- Do not edit `data/` or change the recipe numbers (only `--batch` / `--dtype` if memory or GPU type forces it).
- If anything fails, send the human the last 30 lines of the terminal output.
- Never commit, push or paste keys anywhere.
