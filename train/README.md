# Training GURU-0.6B

GURU-0.6B is Qwen3-0.6B fine-tuned with LoRA (rank 16, alpha 32, all linear layers, loss on the answer only),
merged, then exported to ExecuTorch for the Pi. Trained weights: the
[GURU-0.6B v1 release](https://github.com/ArushJain-697/namma-ai/releases/tag/guru-0.6b-v1).

## 1. Data
| Round | Script | Data | Examples |
|---|---|---|---|
| Version 1 | `scripts/make_mcq_dataset.py` | SciQ + RACE middle (human-written) -> `data/dataset_mcq/` | ~4,300 |
| Two-job (shipped) | `scripts/make_two_job_dataset.py` | teacher dataset `data/dataset_v2/` (401 passages, graded) + 300 RACE per job -> `data/two_job/` | 3,363 |

Two jobs, one model: the system prompt picks the job. Job Q: text + key sentence -> question + answer.
Job W: + question + answer -> 3 wrong answers. Data is picked per job by the grader's rule flags.

## 2. Train (CUDA GPU or Apple-silicon Mac)
```bash
python train/finetune_mac.py --train data/two_job/train.jsonl --val data/two_job/val.jsonl \
  --out out/guru-2job --start-adapter out/qwen3-0.6b-mcq/adapter --lr 5e-5 --epochs 1 --eval-every 50
```
Best recipe found: start from the version 1 adapter, lr 5e-5, 1 epoch, check held-out loss every 50 steps and keep
the best. A 0.6B run takes ~5-6 min on an RTX 4060 laptop GPU. Held-out loss: Q 1.217, W 1.429 (the combined model
beat two single-job specialists, 1.227 and 1.439). Output: `out/guru-2job/merged/`.

## 3. Export to ExecuTorch
```bash
optimum-cli export executorch --model out/guru-2job/merged --task text-generation --recipe xnnpack \
  --use_custom_sdpa --use_custom_kv_cache --qlinear 8da4w --qlinear_group_size 32 --qembedding 8w \
  --max_seq_len 1024 --output_dir models/guru-0.6b-2job
cp out/guru-2job/merged/tokenizer.json models/guru-0.6b-2job/
```
- `--max_seq_len 1024`: the runner reserves memory for the whole limit; 2,048 cost ~0.8 GB more RAM (2.49 vs 1.67 GB)
  for identical answers. One quiz call needs ~600 tokens.
- Keep `--qembedding 8w`: 4-bit embeddings saved only ~75 MB and changed every test answer.
- `--qlinear 8da8w` gives a near-lossless 8-bit model (720 MB instead of 469 MB) if quality matters more than speed.
- For CPUs without the Arm dot-product instructions (e.g. Cortex-A53), drop `--use_custom_sdpa --use_custom_kv_cache`.

## 4. Check it
Run the quiz on the 40 frozen test passages (`data/passages/eval/`) and grade blind against `docs/QUESTION_RUBRIC.md`;
compare with the previous model on the same passages. Never train on or edit the test passages.
