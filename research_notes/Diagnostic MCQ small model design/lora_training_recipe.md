# LoRA Training Recipe: Qwen3-0.6B (and 1.7B) for Strict-JSON Diagnostic MCQ Generation

Scope: parameter-efficient SFT of Qwen3-0.6B on ~1,500-2,500 examples (150-300 word passage in, strict JSON MCQ out, ~800-1,500 tokens per example), plus whether a preference stage helps, and realistic time/cost. Research date: 2026-11-13. Older (pre-2025) sources are flagged.

**Bottom-line recipe (synthesised from the findings below; details and evidence per section):**

```python
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

peft_config = LoraConfig(
    r=32, lora_alpha=32,            # alpha = r (scale 1.0); r=16..64 all reasonable
    use_rslora=False,               # only matters if you go to r>=64
    lora_dropout=0.05,              # 0-0.1; low value of this knob per Unsloth
    target_modules="all-linear",    # q,k,v,o,gate,up,down; NOT attention-only
    task_type="CAUSAL_LM",
)
args = SFTConfig(
    learning_rate=2e-4,             # LoRA ~10x full-FT LR; sweep {1e-4, 2e-4, 3e-4} if time
    lr_scheduler_type="cosine",     # or "linear"
    warmup_ratio=0.05,              # 5-10% of steps (newer TRL: warmup_steps accepts a float ratio)
    num_train_epochs=2,             # 2-3; pick checkpoint by eval JSON-validity / field accuracy
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # effective batch 16 (keep < 32)
    weight_decay=0.01,
    max_length=2048,                # TRL default is 1024 -> would truncate the JSON!
    completion_only_loss=True,      # (prompt-completion data) or assistant_only_loss=True (messages data)
    packing=False,                  # keep simple; packing only if using flash-attn padding-free
    bf16=True,                      # on T4 use fp16=True, bf16=False (no bf16 on Turing)
    gradient_checkpointing=True,    # TRL default
    eval_strategy="steps", eval_steps=50, save_steps=50,
    load_best_model_at_end=True, metric_for_best_model="eval_loss",
    neftune_noise_alpha=None,       # optional ablation at 5; no evidence it helps strict JSON
    seed=3407,
)
```
16-bit LoRA (not QLoRA) for a 0.6B model. Train in non-thinking format (empty `<think>\n\n</think>\n\n` before the JSON), infer with `enable_thinking=False`. Expected wall-clock: roughly 0.5-1 h on a free T4 for 0.6B (2-3 epochs), ~5-15 min on an A100; 1.7B roughly 3x those (estimates, see last section).

---

## 1. How do plain LoRA, rsLoRA, DoRA, LoRA+, PiSSA (and full FT) compare for sub-1B models on narrow structured-output tasks? Library support?

### Takeaway
No 2025-2026 benchmark directly tests these variants at 0.5-1B on a narrow JSON task; the best available evidence (Thinking Machines "LoRA Without Regret", EfficientLLM, PEFT-Arena) says well-configured plain LoRA on all linear layers matches full FT on small/medium SFT data, and the variants give at most ~1-2 point, task-inconsistent gains while some (PiSSA, full FT) forget much more. Use plain LoRA on all-linear; treat DoRA/LoRA+/rsLoRA as optional ablations, not defaults.

### Cited Findings
- **LoRA vs full FT (2025):** "For small-to-medium instruction-tuning and reasoning datasets, LoRA performs the same as full fine-tuning"; LoRA underperforms only when the dataset exceeds adapter capacity. Sweeps covered 14 Llama/Qwen models, smallest explicitly named 1B, ranks 1-512. — [Thinking Machines, LoRA Without Regret (Sep 2025)](https://thinkingmachines.ai/blog/lora/)
- TRL's reproduction guide states LoRA "can match full fine-tuning performance when configured correctly, while using only ~67% of the compute." — [TRL docs: LoRA Without Regret](https://huggingface.co/docs/trl/main/en/lora_without_regret)
- **EfficientLLM (May 2025)** compared LoRA, RSLoRA, DoRA, LoRA+, PiSSA, freeze and full FT on 1B-72B: "LoRA and its variants performed exceptionally well for smaller models (1B to 3B parameters), achieving the lowest loss metrics"; "For models above 14B parameters, RSLoRA dominates on both loss and latency"; DoRA "incurred significant latency overhead"; parameter freezing cut latency 3x at a cost of ~1-2 benchmark points. The paper's text is ambiguous on which specific variant wins at 1-3B (I could not read the tables). — [EfficientLLM, arXiv 2505.13840](https://arxiv.org/html/2505.13840)
- **PEFT-Arena (May 2026)**, Qwen2.5-7B math SFT, target gain / general-capability change: Full FT +15.33 / -12.74; LoRA-r8 +7.17 / -7.75; DoRA-r8 +7.03 / -6.72; MiLoRA-r8 +7.30 / -9.35; **PiSSA-r8 +9.23 / -22.19**; OFT-b32 +11.63 / -2.60. Authors: target-only reporting overestimates quality; "SFT is less resistant to forgetting than RLVR." Settings: PEFT LR 2e-4, full FT 5e-5, cosine. Models were 7B and 3B, not sub-1B. — [PEFT-Arena, arXiv 2605.28819](https://arxiv.org/html/2605.28819)
- RLVR benchmark (Dec 2025, RL not SFT): DoRA and LoRA+ 55.0% avg vs LoRA 54.8%; PiSSA and MiLoRA "suffer from a spectral collapse." — [Evaluating PEFT Methods for RLVR, arXiv 2512.23165](https://arxiv.org/pdf/2512.23165) (via search snippet; not read in full)
- LoRA-Pro (2024, older) benchmarked LoRA, PiSSA, rsLoRA, LoRA+, DoRA side by side with no consistent winner across tasks. — [LoRA-Pro, arXiv 2407.18242](https://arxiv.org/pdf/2407.18242) (via search summary)
- "LoRA Learns Less and Forgets Less" (2024, older): LoRA underperforms full FT on code/math targets but better preserves base-model abilities. — [Biderman et al., arXiv 2405.09673](https://arxiv.org/pdf/2405.09673)
- **Practitioner evidence at 0.5B for JSON:** A LoRA-tuned Qwen2.5-0.5B-Instruct raised app-review-to-JSON field accuracy from ~62% (3-shot base) to ~77%; JSON validity was already 100% for both, so the gain was field correctness, not formatting. Single seed, small test set. — [HF Space: App-review to structured JSON](https://tanmaydeshpande-app-review-extraction.static.hf.space/index.html)
- **PEFT flags (current PEFT docs):**
  - rsLoRA: `LoraConfig(use_rslora=True)` sets scaling to `lora_alpha/sqrt(r)` instead of `lora_alpha/r`; "increases the performance potential from using a higher r."
  - DoRA: `LoraConfig(use_dora=True)`; only Linear/Conv2D; "introduces a bigger overhead than pure LoRA, so it is recommended to merge weights for inference"; not compatible with mixed-adapter batches.
  - PiSSA: `init_lora_weights="pissa"` (full SVD, minutes) or `"pissa_niter_16"` (fast SVD, seconds). Note PiSSA mutates the residual base weights, so the adapter must be converted/merged before deploying on the original base.
  - LoRA+: not a LoraConfig flag; `from peft.optimizers import create_loraplus_optimizer` with `loraplus_lr_ratio` (example uses 16) and pass the optimizer to the trainer. Docs claim "up to 2x" speed and "1-2%" performance.
  - Also available: `init_lora_weights="olora" | "corda" | "eva" | "loftq" | "gaussian"`; `target_modules="all-linear"` excludes the output layer.
  — [PEFT LoRA developer guide](https://huggingface.co/docs/peft/main/en/developer_guides/lora)
- TRL `SFTTrainer` takes `peft_config=LoraConfig(...)` directly; CLI flags `--use_peft --lora_r --lora_alpha --lora_target_modules all-linear --lora_dropout`. — [TRL SFT Trainer docs](https://huggingface.co/docs/trl/main/en/sft_trainer); [TRL LoRA Without Regret](https://huggingface.co/docs/trl/main/en/lora_without_regret)
- Unsloth exposes `use_rslora` (default False) and target modules `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`; supports `full_finetuning=True` and `load_in_8bit=True` as alternatives to 4-bit. — [Unsloth LoRA hyperparameters guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide); [Unsloth Qwen3 docs](https://unsloth.ai/docs/models/qwen)

### Inferences
- For a ~2,000-example narrow task, the dataset is far below "LoRA capacity" even at r=16-32, so the LoRA-vs-full-FT gap should be negligible; full FT of 0.6B is feasible (1.2 GB weights) but buys little and forgets more (PEFT-Arena pattern), and makes the deployable artifact a full model rather than a small adapter.
- Avoid PiSSA as a default: largest forgetting in PEFT-Arena and spectral collapse in RLVR, plus it complicates merging/export (relevant because the project exports to ExecuTorch). DoRA's overhead is wasted on a one-day budget; merge before export if used.
- Since the base 0.5B-class model already emits valid JSON reasonably often, expect SFT gains mainly in schema adherence and content quality (distractor/misconception fields), which is where evaluation should focus.

### Gaps
- No controlled head-to-head of LoRA/rsLoRA/DoRA/LoRA+/PiSSA at 0.5-1B on a structured-output task was found.
- Could not verify whether Unsloth's fast kernels support `use_dora` for Qwen3 (not stated in the pages read).
- EfficientLLM's per-variant numbers at 1-3B were not extractable from the portion read.

---

## 2. Recommended rank, alpha, target modules, dropout, LR, scheduler, warmup, epochs, batch size, max length for ~2,000 examples; overfitting evidence

### Takeaway
All-linear LoRA, r=16-32 with alpha=r (or 2r), LR ~2e-4, cosine/linear with 5-10% warmup, effective batch 16 (<32), 2-3 epochs with eval-based checkpoint selection, and `max_length` >= 2048 (TRL's default 1,024 would silently truncate). Overfitting signal: train loss < ~0.2.

### Cited Findings
- **Target modules:** "Attention-only LoRA significantly underperforms MLP-only LoRA"; attention-only at r=256 (0.25B params) does worse than MLP-only at r=128 (0.24B); higher rank does not compensate. — [Thinking Machines](https://thinkingmachines.ai/blog/lora/); [TRL guide](https://huggingface.co/docs/trl/main/en/lora_without_regret)
- **Learning rate:** optimal LoRA LR is ~10x full-FT LR, "consistently 10x" across SFT and RL; fitted multiplier 9.8; for short runs (<~100 steps) ~15x (preliminary/anecdotal). With 1/r scaling the optimal LR is approximately rank-independent. Their parametrization used alpha=32 in all experiments. — [Thinking Machines](https://thinkingmachines.ai/blog/lora/)
- TRL docs: adapters "typically use a higher learning rate (≈1e-4)"; SFTConfig default is 2e-5 (a full-FT value, too low for LoRA). — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)
- TRL LoRA-without-regret SFT example: `LoraConfig(r=256, lora_alpha=16, target_modules="all-linear")`, `learning_rate=2e-4`, batch 1 x GA 4 (for large post-training datasets; rank 256 recommended at "post-training scale"). — [TRL guide](https://huggingface.co/docs/trl/main/en/lora_without_regret)
- **Batch size:** LoRA "less tolerant of large batch sizes than full fine-tuning"; recommend effective batch < 32; not fixable by raising rank. — [TRL guide](https://huggingface.co/docs/trl/main/en/lora_without_regret); [Thinking Machines](https://thinkingmachines.ai/blog/lora/)
- **Unsloth defaults:** r=16 ("choose 16 or 32"; range 8-128; "rank should be bigger for smaller models/more complex datasets; it usually is between 4 and 64"); alpha = r or 2r; dropout 0 (default) to 0.1, "not that useful"; weight decay 0.01-0.1; warmup 5-10% of steps; linear or cosine; LR 2e-4 for LoRA/QLoRA, 5e-6 for DPO/GRPO; 1-3 epochs (>3 diminishing returns); batch 2 x GA 8 = effective 16 (range 4-16). — [Unsloth LoRA hyperparameters guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)
- **Overfitting:** "If your training loss drops below 0.2, your model is likely overfitting"; remedies: fewer epochs, higher weight decay, dropout 0.1, early stopping on eval loss, or scale alpha by 0.5 post hoc. — [Unsloth guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)
- **Max length:** `SFTConfig.max_length` defaults to **1024** and truncates with `keep_start` (i.e., cuts the end, which is the JSON answer). — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)
- Unsloth Qwen3 notebook uses `max_seq_length = 2048`. — [Unsloth Qwen3 docs](https://unsloth.ai/docs/models/qwen)
- PEFT-Arena used PEFT LR 2e-4 with cosine. — [PEFT-Arena](https://arxiv.org/html/2605.28819)
- Other SFTConfig defaults worth knowing: `num_train_epochs=3.0`, `per_device_train_batch_size=8`, `lr_scheduler_type='linear'`, `warmup_steps=0` (float accepted), `weight_decay=0.0`, `gradient_checkpointing=True`, `bf16=True` unless fp16 set, `optim='adamw_torch_fused'`. — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)

### Inferences
- Step math: 2,000 examples / effective batch 16 = 125 steps/epoch, ~250-375 steps for 2-3 epochs: well above the "<100 step" regime, so ~10x full-FT LR (≈1e-4 to 3e-4) applies. With only ~2k examples, r=16-32 is ample capacity; r=64+ only with `use_rslora=True` and is unlikely to help.
- Because outputs are long and templated, token-level train loss will fall fast; judge overfitting by held-out JSON parse rate, schema-field accuracy and distractor quality, not loss alone. Save a checkpoint every ~50 steps and select by eval.
- Set `max_length` to cover the longest example plus margin (2,048) and assert no example is truncated before training.

### Gaps
- No source gives dataset-size-specific rank guidance for ~2k examples at 0.6B; the r=16-32 recommendation is an inference from capacity arguments and Unsloth defaults.
- Thinking Machines' fitted "model pow" exponent (LR vs hidden size) was not given, so a size-adjusted LR for hidden size 1,024 could not be computed.

---

## 3. Does QLoRA (4-bit base during training) hurt sub-1B models vs 16-bit LoRA?

### Takeaway
No controlled QLoRA-vs-LoRA study at 0.5-1B was found, but Qwen3-0.6B is documented to be unusually sensitive to 4-bit quantization, and a 0.6B model in bf16 needs only ~1.2 GB, so QLoRA's memory savings are irrelevant. Use 16-bit LoRA.

### Cited Findings
- QLoRA paper (2023, older) showed NF4 + double quant recovers 16-bit LoRA performance, but only at 7B-65B; the precision trade-off was left open. — [QLoRA, arXiv 2305.14314](https://arxiv.org/pdf/2305.14314)
- "An Empirical Study of Qwen3 Quantization" (May 2025), PTQ on Qwen3 0.6B-72B: at 4 bits "all quantization methods exhibit noticeable performance degradation"; larger models are more stable (14B ~1% MMLU drop under 4-bit GPTQ) while 0.6B degrades much more. — [arXiv 2505.02214](https://arxiv.org/html/2505.02214v1) (via search snippets; exact 0.6B table numbers not retrieved)
- A 2026 paper on Qwen3-0.6B..14B finds smaller models degrade earlier as precision drops, while 8B/14B stay stable at W4/W3. — [Quantization Degradation in LLMs: A Signal-Noise Perspective, arXiv 2608.08188](https://arxiv.org/pdf/2608.08188) (via search snippet)
- Unsloth: QLoRA is "slightly slower and marginally less accurate" with ~4x less VRAM than LoRA. — [Unsloth guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)
- Llama-3.2-1B anecdote: QLoRA r=8 had similar accuracy trends to LoRA but slower progress. — [Infosys blog](https://blogs.infosys.com/emerging-technology-solutions/?p=3820) (weak, single task)
- PEFT recommends `init_lora_weights="loftq"` if you must train on a quantized base. — [PEFT LoRA guide](https://huggingface.co/docs/peft/main/en/developer_guides/lora)

### Inferences
- PTQ sensitivity is not the same as QLoRA training degradation, but it implies the 4-bit-dequantized base the adapter is trained against differs materially from the bf16 base; if the adapter is then merged into the 16-bit (or differently quantized ExecuTorch) weights, there is a train/deploy mismatch. With ample memory, 16-bit LoRA removes that risk.
- Note the Unsloth Qwen3 notebook sets `load_in_4bit = True` by default; flip it to `False` for 0.6B/1.7B.

### Gaps
- No measured QLoRA-vs-LoRA fine-tuning result at 0.5-1B was found.

---

## 4. Loss masking in current TRL, NEFTune evidence, replay/general data mixing

### Takeaway
Use completion-only loss (default for prompt-completion datasets) or `assistant_only_loss=True` for messages datasets (TRL auto-patches the Qwen3 template); verify the mask by decoding. NEFTune has no evidence of helping strict-JSON tasks: leave off or ablate at alpha=5. Replay data is mainly needed if you care about retaining general/reasoning ability; for a single-purpose on-device model, a small (~10-20%) general mix is optional.

### Cited Findings
- `completion_only_loss` (default `None`): for prompt-completion datasets loss is computed on the completion only by default; full sequence for language-modeling datasets. — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)
- `assistant_only_loss` (default `False`): only for conversational datasets; requires `{% generation %}`/`{% endgeneration %}` in the chat template, but "For known model families (e.g. Qwen3), TRL automatically patches the template when `assistant_only_loss=True`." Compatible with completion-only on a conversational prompt-completion dataset. — [TRL SFT docs (main)](https://huggingface.co/docs/trl/main/en/sft_trainer)
- Older TRL (v0.20) wording differs; check the installed version. A forum report says `assistant_only_loss=True` errors with VLMs. — [TRL v0.20 docs](https://huggingface.co/docs/trl/v0.20.0/sft_trainer); [HF forum](https://discuss.huggingface.co/t/sfttrainerflags-blocks-assistant-only-loss-true/176210)
- Pre-tokenized datasets: a `labels` column with -100 is used as-is, else built from `assistant_masks` / `completion_mask`. — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)
- Unsloth equivalent is `train_on_responses_only(trainer, instruction_part=..., response_part=...)`; the guide lists strings for Llama/Gemma but not ChatML. — [Unsloth guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)
- TRL also offers `loss_type="dft"` (Dynamic Fine-Tuning, claimed better generalization). — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)
- **NEFTune:** `SFTConfig(neftune_noise_alpha=...)` is supported (default None). Original paper (2023, older): LLaMA-2-7B AlpacaEval 29.79% -> 64.69%; gains attributed to reduced overfitting on small instruction datasets; typical alpha 5-15. A Shisa 8B fine-tune with alpha=5 was "within MOE" of no-NEFTune. No study on small models or structured output found. — [NEFTune paper, arXiv 2310.05914](https://arxiv.org/pdf/2310.05914v1); [Shisa model card](https://huggingface.co/shisa-ai/shisa-v1-llama3-8b.neftune/raw/main/README.md); [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)
- **Mixing:** Unsloth recommends ~75% reasoning / 25% non-reasoning data to retain Qwen3 reasoning; "Fine-tuning only on non-reasoning data may weaken reasoning." — [Unsloth Qwen3 docs](https://unsloth.ai/docs/models/qwen)
- SFT causes notable forgetting even with LoRA (LoRA-r8 -7.75 general points on Qwen2.5-7B). — [PEFT-Arena](https://arxiv.org/html/2605.28819)

### Inferences
- Safest masking route for Qwen3: build a *standard* (string) prompt-completion dataset where `prompt = tokenizer.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False, tokenize=False)` (ends with `<think>\n\n</think>\n\n`) and `completion = json_string + "<|im_end|>"`. This makes training text byte-identical to the inference prompt and uses the default completion-only loss with no template patching. Always decode `labels != -100` on a sample to confirm only JSON + `<|im_end|>` is trained.
- NEFTune's mechanism (regularising open-ended style) is mismatched to exact-format targets; at most run one ablation with alpha=5.
- Since the deployed model is task-specific, forgetting matters less; if the same weights must still chat or reason, mix ~10-25% general non-thinking chat (and some thinking data if reasoning is kept), per Unsloth's guidance.

### Gaps
- No evidence on NEFTune for sub-1B or JSON outputs; no quantified replay ratio for narrow structured-output SFT.

---

## 5. Qwen3 specifics: chat template, thinking vs non-thinking training data, Unsloth support

### Takeaway
Train in non-thinking format: the Qwen3 template renders the final assistant turn with an empty `<think>\n\n</think>\n\n` block and the `enable_thinking=False` generation prompt appends the same block, so train and inference match. Unsloth supports Qwen3-0.6B and 1.7B (use the 14B notebooks with the model name swapped).

### Cited Findings
- Qwen3-0.6B: 0.6B params (0.44B non-embedding), 28 layers, 16 Q / 8 KV heads (GQA), 32,768 context. `enable_thinking` defaults True; False is a hard switch; `/think` `/no_think` soft switches are ignored when False. Non-thinking sampling: temperature 0.7, top_p 0.8, top_k 20, min_p 0; presence_penalty 0-2 (1.5 if repetition). Multi-turn history should contain only final outputs, not thinking. — [Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B)
- Chat template (verified from tokenizer_config.json): for assistant turns after the last user query, a `<think>` block is written if `loop.last or reasoning_content`, i.e. the final assistant message always gets a (possibly empty) think block; with `add_generation_prompt` and `enable_thinking=false` the template appends `<|im_start|>assistant\n` + empty think block. `eos_token = <|im_end|>`, `pad_token = <|endoftext|>`. — [Qwen3-0.6B tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-0.6B/raw/main/tokenizer_config.json)
- Unsloth: "Non-thinking mode inserts an empty think block: `<think>\n\n</think>\n\n`"; prompt format `<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n`. — [Unsloth Qwen3 docs](https://unsloth.ai/docs/models/qwen)
- Apparent conflict: the model card says non-thinking mode produces no think block, Unsloth says an empty block appears. Resolution from the template: the empty block is part of the *prompt* (inserted by the template), so the model never *generates* it. — [Qwen3 model card](https://huggingface.co/Qwen/Qwen3-0.6B); [Unsloth](https://unsloth.ai/docs/models/qwen); [tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-0.6B/raw/main/tokenizer_config.json)
- Unsloth lists Qwen3 0.6B, 1.7B, 4B, 8B, 14B, 30B-A3B, 32B for fine-tuning; notebooks: Qwen3 (14B) Reasoning+Conversational (recommended), Qwen3 (14B) Alpaca, Qwen3 (4B) GRPO; claims 2x faster, ~70% less VRAM. No dedicated 0.6B notebook; change model name to `unsloth/Qwen3-0.6B`. — [Unsloth Qwen3 docs](https://unsloth.ai/docs/models/qwen); [search summary of Unsloth JP docs](https://unsloth.ai/docs/jp/moderu/tutorials/qwen3-how-to-run-and-fine-tune)
- TRL's own SFT quickstart uses `Qwen/Qwen3-0.6B`. — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)

### Inferences
- For strict JSON, decode greedily or at low temperature (the "no greedy" warning applies to thinking mode) and use constrained decoding if the runtime allows; Qwen's 0.7 temperature is for open chat.
- Do not put `/no_think` in prompts if `enable_thinking=False` is used consistently; it is ignored and wastes tokens. For ExecuTorch, hard-code the rendered prompt string (ending in the empty think block) exactly as in training.
- Qwen3-0.6B has tied embeddings per general knowledge of the config (unverified here); `all-linear` excludes the output layer anyway.

### Gaps
- Did not verify whether TRL's auto-patched Qwen3 training template includes the empty think block inside the generation mask (hence the string prompt-completion recommendation).

---

## 6. Is a short DPO/ORPO stage after SFT (rejected = bad distractors) worth it in a one-day budget?

### Takeaway
Probably not as a first priority: evidence that DPO adds a reliable win over well-tuned SFT at small scale is weak, and no timing data exists for this setup. Do it only if SFT is done by midday and you have >= ~500 clean pairs; it is cheap in compute (minutes for 0.6B) but costly in data construction and evaluation time.

### Cited Findings
- 2026 preprint on small LMs (GPT-2 class): DPO "is not a reliable large win over a well-tuned SFT baseline at this scale"; LoRA did not reduce wall-clock in their compute-bound H100 setup. — [An Empirical Study of SFT-DPO Interaction in Small LMs, arXiv 2603.20100](https://arxiv.org/abs/2603.20100) (via search snippet)
- Stanford CS224R student report on Qwen2.5-0.5B (~460K SFT examples): ORPO "consistently outperforms all other methods," 70.1% win rate vs SFT at ~20% of training time. Course project, weak evidence. — [CS224R report](https://cs224r.stanford.edu/projects/pdfs/CS224R_Project_Final_Report1.pdf)
- Qwen2.5-0.5B LoRA DPO with only 40 pairs: SFT alone won more often. — [rag-dpo-qwen2.5-0.5b](https://friendli.ai/models/sidmhuggingface/rag-dpo-qwen2.5-0.5b) (anecdotal)
- Unsloth suggests LR ~5e-6 for DPO/GRPO stages. — [Unsloth guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)

### Inferences
- Compute: DPO processes chosen + rejected sequences and (unless the reference is the adapter-disabled base, as TRL does for PEFT models) reference log-probs, so roughly 2-4x SFT cost per pair; for ~1,000 pairs of ~1,200 tokens on 0.6B, that is minutes on an A100 and well under an hour on a T4 (estimate, not measured).
- Rejected distractors that differ from the chosen output in only a few JSON fields give a sharp, targeted signal; DPO on long, mostly identical sequences can also push down likelihood of shared tokens, so watch JSON validity after DPO.
- Higher-value use of the same time: hard-negative filtering of SFT data, rejection sampling (generate N, keep schema-valid best by a judge) and a second SFT round.

### Gaps
- No measured DPO/ORPO timings or gains for Qwen3-0.6B or for MCQ-distractor preference data were found.

---

## 7. Realistic wall-clock time, memory and cost (Qwen3-0.6B and 1.7B, ~2,000 x 800-1,500 tokens, 2-3 epochs)

### Takeaway
No reliable measured numbers exist for this exact setup; FLOP-based estimates give ~30-60 min (0.6B) and ~1.5-3 h (1.7B) on a free T4, ~5-15 min and ~15-40 min on an A100, ~10-20 min and ~30-60 min on an L4. Memory is dominated by the 152k-vocab logits, not the weights.

### Cited Findings
- Only direct anecdote found: a Qwen 0.6B question-categorization fine-tune reported 18 min training and 1.8 GB VRAM with 4-bit weights (settings/data size unstated, page partly garbled). — [PromptZone write-up](https://www.promptzone.com/samir_hansen/fine-tuning-qwen-06b-for-local-question-categorization-4djc)
- Unsloth: Qwen3-14B QLoRA fits on a free 16 GB T4; 2x faster, ~70% less VRAM than baseline. — [Unsloth Qwen3 docs](https://unsloth.ai/docs/models/qwen)
- Unsloth: 16-bit LoRA uses ~4x more VRAM than QLoRA (relevant only for large models). — [Unsloth guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)
- TRL supports `use_liger_kernel=True` (fused kernels incl. cross-entropy), `packing`, `padding_free` (FlashAttention 2/3 only), `activation_offloading`. — [TRL SFT docs](https://huggingface.co/docs/trl/main/en/sft_trainer)

### Inferences (my estimates; not measured, verify with a 20-step timing run)
- Tokens: 2,000 x ~1,150 avg = ~2.3M tokens/epoch; 3 epochs ~6.9M tokens. Training FLOPs ~6 x 0.6e9 x 6.9e6 ~ 2.5e16 (LoRA saves weight-gradient compute, gradient checkpointing adds ~1/3 back, so ~6N is a fair budget).
  - **T4** (65 TFLOPS fp16 peak, ~15-20 effective for HF/Unsloth on a small model): ~25-45 min for 0.6B x 3 epochs; ~1.5-3 h for 1.7B. Padding without packing adds 10-30%.
  - **A100 40/80GB** (312 TFLOPS bf16 peak, ~80-120 effective): ~4-8 min (0.6B), ~12-25 min (1.7B).
  - **L4** (~121 TFLOPS dense bf16, ~30-45 effective): ~10-20 min (0.6B), ~30-60 min (1.7B).
- **Memory (0.6B, bf16 LoRA):** weights ~1.2 GB; LoRA r=32 all-linear adapters + Adam states < 0.3 GB; the logits for batch 4 x 1,536 tokens x 151,936 vocab in fp32 are ~3.7 GB (plus a similar-size gradient), so per-device batch 2-4 with gradient checkpointing fits a 16 GB T4; enable Liger fused cross-entropy (`use_liger_kernel=True`) or Unsloth to cut this. 1.7B (~3.4 GB weights, hidden 2,048) should fit a T4 at batch 1-2 x GA 8-16 in 16-bit LoRA.
- **T4 caveat:** Turing has no bf16; set `fp16=True, bf16=False` (TRL defaults to bf16=True). Unsloth handles fp16 on T4 automatically.
- **Cost:** free on Colab T4 (session limits; risk of disconnect on multi-hour 1.7B runs, so save checkpoints to Drive). On paid clouds an A100 is typically on the order of $1-2/h and an L4 under $1/h, so a full 0.6B run plus a few LR ablations costs a few dollars. (Pricing not verified against a current source.)
- Practical budget: on an A100 you can afford a 3-point LR sweep (1e-4/2e-4/3e-4) x 2 ranks in under an hour for 0.6B; on a T4 pick one config.

### Gaps
- No published wall-clock or peak-memory measurements for Qwen3-0.6B or 1.7B LoRA SFT at this data size were found; all timings above are FLOP-based estimates.
- Current GPU rental prices and Colab free-tier session limits were not verified.
