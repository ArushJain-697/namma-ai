# Fine-tuning the quiz model (for Arush's GPU, a teammate's laptop or Colab)

What you get: our own **Qwen3-0.6B** that writes a whole multiple-choice question in one short call (quiz format
v2: `{"q", "options" (correct first), "answer": 0, "explain"}`, see `src/sakshi/diagnostic.py`), trained on
Opus-written questions that passed the rubric grader, merged into one model file and exported to ExecuTorch.

**Updated 13 Nov (question-quality branch):** defaults now point at `data/dataset_v2/` (build it with
`python scripts/make_dataset.py build-v2`), LoRA rank 64 / alpha 64, 3 epochs. Try `--full` too (full fine-tune,
`--lr 2e-5`); keep whichever scores better on the 200 test passages (`scripts/eval_quiz.py`).

## 0. What you need
- This repo (`git clone` / copy), including `data/dataset/train.jsonl` and `val.jsonl` (made overnight by
  `scripts/overnight.sh`; check `data/dataset/stats.json` for counts).
- A GPU: a free **Google Colab T4** is enough for 0.6B (about 30-50 minutes). An NVIDIA laptop GPU with 8 GB+ works too.
  Apple Silicon (MPS) can work but is slow and less tested: prefer Colab.

## 1. Train (Colab)
```bash
# in a Colab cell, after uploading or cloning the repo:
%cd namma-ai
!pip install -q -r train/requirements.txt
!python train/finetune_qwen3_lora.py --limit 64 --epochs 0.2 --out out/smoke     # 2-minute smoke test first
!python train/finetune_qwen3_lora.py --out out/qwen3-0.6b-quiz                   # the real run (LoRA)
!python train/finetune_qwen3_lora.py --full --lr 2e-5 --out out/qwen3-0.6b-quiz-full   # also try: full fine-tune
```
Before training starts, the script prints one prompt, its answer, and **the tokens that carry the loss**. That
last block must be the JSON answer only. If it shows the passage, stop and tell us.
Settings are the script defaults (rank 64, alpha 64, all linear layers, lr 2e-4, 3 epochs, batch 16, length 2048,
16-bit, answer-only loss). Watch `eval_loss` fall; the best checkpoint is kept automatically.

Output: `out/qwen3-0.6b-diag/merged/` (about 1.2 GB, safetensors + tokenizer). Zip it and send it back
(`!zip -r merged.zip out/qwen3-0.6b-diag/merged`, then download).

Fallback if the 0.6B results are weak: `--model Qwen/Qwen3-1.7B` (about 1.5-3 h on a T4, better questions, slower on the Pi).

## 2. Export to ExecuTorch (on the Mac, in this repo's export environment)
```bash
.venv-export/bin/optimum-cli export executorch --model out/qwen3-0.6b-diag/merged --task text-generation \
  --recipe xnnpack --use_custom_sdpa --use_custom_kv_cache --qlinear 8da4w --qlinear_group_size 32 \
  --qembedding 8w --max_seq_len 1024 --output_dir models/qwen3-0.6b-diag-8da4w
cp out/qwen3-0.6b-diag/merged/tokenizer.json models/qwen3-0.6b-diag-8da4w/
```
Keep `--max_seq_len 1024`: the model reserves memory for the whole limit, and 2048 costs ~0.8 GB more RAM
(2.49 GB vs 1.67 GB peak on the Mac) for the same speed and identical answers; one quiz call needs ~600 tokens.
Do not use `--qembedding 4w`: it saves only ~75 MB and changed every test answer.
For the Arduino UNO Q (Cortex-A53) also make a portable copy: drop `--use_custom_sdpa --use_custom_kv_cache`.
If 4-bit quality drops more than about 2 points against the merged model on the test set, export with
`--qlinear 8da8w` instead (bigger file, slower, near-lossless).

## 3. Test it on the 200 passages
```bash
PYTHONPATH=src .venv-export/bin/python scripts/eval_diagnostic.py --out results/eval_diag_finetuned \
  --backend executorch --model models/qwen3-0.6b-diag-8da4w/model.pte --tokenizer models/qwen3-0.6b-diag-8da4w/tokenizer.json
```
Compare with the same command on the base model (`results/eval_diag_base`).
