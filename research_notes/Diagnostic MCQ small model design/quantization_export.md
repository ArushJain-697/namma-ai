# Getting a LoRA-fine-tuned Qwen3-0.6B / 1.7B into an ExecuTorch .pte for Raspberry Pi 5 with minimal quality loss

Research date: 2026-11-13. Project baseline: ExecuTorch 1.5.1, optimum-executorch 1.1.0, torch 2.14, transformers 5.0.0rc1. Base Qwen3-0.6B export already works. Most sources below come from upstream `main` branches or 2025-2026 posts. Behaviour pinned to exactly optimum-executorch 1.1.0 / ExecuTorch 1.5.1 could **not** be checked against those release tags, and the Gaps sections flag this where it matters.

## Q1. PTQ quality loss for sub-2B models: 8da4w (group size 32/64/128) vs 8da8w vs 8-bit embeddings

### Takeaway
8-bit weight PTQ is effectively lossless on Qwen3-0.6B/1.7B. 4-bit weight PTQ costs a clear 3-10 MMLU points on Qwen3-0.6B depending on the method: RTN per-channel is worst, and GPTQ with group size 128 is best among the methods tested. The best direct evidence for the exact ExecuTorch scheme (8da4w, group size 32, 8-bit embeddings) is Meta's Llama-3.2-1B "vanilla PTQ" row. It shows large losses on reasoning, tool-use and instruction-following tasks (MMLU -6, GSM8K -11, IFEval -8, BFCL -11). QAT+LoRA or SpinQuant recover most of that loss.

### Cited Findings
- **Qwen3-0.6B (An Empirical Study of Qwen3 Quantization, arXiv 2505.02214, Table 4, per-group G128)**: FP16 Wiki2 PPL 20.9 / C4 25.4 / 0-shot avg 52.9 / MMLU 47.1. AWQ w8 = 20.9 / 25.4 / 52.8 / 47.0. GPTQ w8 = 20.9 / 25.4 / 53.1 / 47.0. AWQ w4 = 26.9 / 31.6 / 50.1 / 42.1. GPTQ w4 = 25.3 / 31.1 / 49.1 / 44.0 — [arXiv 2505.02214](https://arxiv.org/html/2505.02214v1)
- **Qwen3-0.6B, per-channel (no groups)**: RTN w8 is lossless (MMLU 47.0). RTN w4 per-channel drops to Wiki2 37.5, MMLU 37.3. SmoothQuant w8a8 gives MMLU 46.3. SmoothQuant w4a8 per-channel collapses to MMLU 30.8, Wiki2 49.5 — [arXiv 2505.02214](https://arxiv.org/html/2505.02214v1)
- **Qwen3-1.7B (same paper, G128)**: FP16 MMLU 60.0, Wiki2 16.7. GPTQ w8 59.9. AWQ w4 52.5. GPTQ w4 55.7 (Wiki2 19.5). SmoothQuant w4a8 per-channel gives MMLU 44.1 — [arXiv 2505.02214](https://arxiv.org/html/2505.02214v1)
- The authors report that 8-bit is near-lossless, that all methods degrade noticeably at 4-bit, and that larger models are more stable under quantization. They also say Qwen3 degrades more than LLaMA3 at 3 bits or fewer — [arXiv 2505.02214](https://arxiv.org/html/2505.02214v1)
- **Llama-3.2-1B-Instruct, the exact ExecuTorch mobile scheme.** The scheme is 4-bit groupwise weights with group size 32 and 8-bit per-token dynamic activations in transformer linears, 8-bit per-channel weights for the classifier/lm_head, and 8-bit per-channel embeddings. Results as BF16 → Vanilla PTQ → SpinQuant → QAT+LoRA:
  - MMLU 49.3 → 43.3 → 47.3 → 49.0
  - IFEval 59.5 → 51.5 → 58.4 → 55.6
  - GSM8K CoT 44.4 → 33.1 → 40.6 → 46.5
  - MATH 30.6 → 20.5 → 25.3 → 31.0
  - ARC-C 59.4 → 54.3 → 57.0 → 60.7
  - Hellaswag 41.2 → 38.1 → 41.3 → 41.5
  - BFCL V2 25.7 → 14.3 → 15.9 → 23.7
  - MGSM 24.5 → 13.7 → 18.2 → 24.4

  Meta notes that the "Vanilla PTQ" model was not released — [Llama-3.2-1B-Instruct model card](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)
- **Qwen3-4B with the PyTorch-team INT8-INT4 recipe** (8da4w, PerGroup(32), int8 per-axis embeddings, embeddings untied from lm_head first). BF16 → INT8-INT4: MMLU 68.38 → 66.74, MMLU-Pro 49.71 → 46.73, BBH 74.86 → 67.47, GSM8K 84.76 → 82.87, overall 55.08 → 52.01. Runs at 14.8 tok/s and 3379 MB on iPhone 15 Pro — [pytorch/Qwen3-4B-INT8-INT4](https://huggingface.co/pytorch/Qwen3-4B-INT8-INT4)
- **optimum-executorch defaults (main branch `quantization.py`)**:
  - `qlinear_group_size` defaults to 32. `qembedding_group_size` defaults to 0, which means per-axis/per-row.
  - `8da8w` always uses PerAxis(0) and ignores group size.
  - Weight scales use `qparams_algorithm="hqq_scale_only"` by default.
  - Linear layers whose in_features isn't divisible by the group size are left **unquantized and not logged**, unless a fallback such as `--qlinear 8da4w,8da8w` is given. The fallback then applies per-axis 8da8w.
  - The source carries a TODO saying tied weights aren't handled explicitly.

  — [optimum-executorch quantization.py](https://raw.githubusercontent.com/huggingface/optimum-executorch/main/optimum/exporters/executorch/quantization.py)
- `--qlinear` choices on main are `8da4w`, `4w`, `8w`, `8da8w`, `8da4w,8da8w`, `fpa4w` (fpa4w is MPS only). `--qembedding` choices are `4w` and `8w`. `--qlinear_group_size`, `--qembedding_group_size` and `--max_seq_len` also exist — [optimum-executorch CLI source](https://raw.githubusercontent.com/huggingface/optimum-executorch/main/optimum/commands/export/executorch.py)
- An Unsloth QAT'd Qwen3-0.6B exported with 8da4w via export_llama produces a .pte of about 472 MB — [Unsloth phone deployment docs](https://unsloth.ai/docs/basics/inference-and-deployment/deploy-llms-phone). In the ExecuTorch LoRA example, quantized Qwen3-0.6B foundation weights (8da4w plus embedding quantization) take 473 MB as a .ptd, versus 2.3 GB in FP32 — [executorch-examples LoRA README](https://raw.githubusercontent.com/meta-pytorch/executorch-examples/main/program-data-separation/cpp/lora_example/README.md)

### Inferences
- For a diagnostic-MCQ task, the Llama-3.2-1B row is the most relevant warning. Instruction-following (IFEval -8) and structured-output/tool-calling (BFCL -11, Nexus -8) are hit hardest by plain 8da4w PTQ. If the model must emit a strict format (option letter + misconception tag, JSON), 4-bit PTQ is where failures will appear. Measure format-validity rate, not only accuracy.
- Group size: 32 is the ExecuTorch/optimum default and what Meta and the PyTorch team ship. Smaller groups are more accurate and slightly larger. I found no published 0.6B ablation comparing g32, g64 and g128 under 8da4w. The Qwen3 paper's w4 G128 numbers (MMLU -3 to -5 on 0.6B) are therefore a rough upper bound for g32 loss with a good scale algorithm. Plain RTN per-channel (-10 MMLU) shows what happens with no grouping.
- 8-bit embeddings are a free win. Qwen3-0.6B's embedding table is a large fraction of its parameters (vocab ~152k × hidden 1024 ≈ 155M of ~600M; this is arithmetic from the model config, not a sourced figure). 8-bit per-row embedding is lossless in every source here, while 4-bit embeddings would add risk.
- A practical recipe for 0.6B: start with `--qlinear 8da4w --qlinear_group_size 32 --qembedding 8w`. If the eval set shows more than about 2 points of loss, try `--qlinear 8da8w` (expect near-lossless quality, a .pte roughly 1.5-1.8× larger, and slower decode because more bytes are read per token). Alternatively, add QAT (Q2). For 1.7B, 8da4w g32 is the realistic choice on a Pi 5 for memory and speed reasons.
- Use `--qlinear 8da4w,8da8w` so that no linear is silently left in fp32 when group-size divisibility fails. All Qwen3-0.6B/1.7B hidden and intermediate dims (1024/3072, 2048/6144) are divisible by 32, so this is likely moot here, but it costs nothing.

### Gaps
- No published Qwen3-0.6B or Qwen2.5-0.5B numbers for the exact torchao 8da4w g32 + 8-bit embedding scheme. No g32 vs g64 vs g128 ablation for sub-1B models.
- No published 8da8w (dynamic int8 activations + int8 weights) accuracy for Qwen3-0.6B. SmoothQuant w8a8 (MMLU 46.3 vs 47.1) is the closest proxy.
- Couldn't confirm whether `hqq_scale_only` is the default in the **1.1.0 release** or only on main.

## Q2. Quantization-aware training (torchao, Unsloth, QAT+LoRA): export compatibility, recovery numbers, overhead

### Takeaway
QAT reliably recovers roughly 30-70% of the PTQ degradation (headline "up to 96%" on Llama3-8B Hellaswag). On Llama-3.2-1B under the exact ExecuTorch 8da4w-g32 scheme, Meta's QAT+LoRA essentially closed the gap. The cleanest path where trained and deployed quantization exactly match is the Unsloth / PyTorch-team flow:
1. torchao QAT `convert`.
2. Save the torchao-quantized checkpoint.
3. Run `executorch.examples.models.qwen3.convert_weights`.
4. Run `export_llama`/`export_llm` **without re-quantizing**.

optimum-executorch has no code that detects pre-quantized torchao checkpoints. With optimum, you would export the QAT-trained high-precision weights and re-run PTQ with a matching config, which gives only an approximate match.

### Cited Findings
- **Current torchao API**:
  - `quantize_(model, QATConfig(base_config, step="prepare"))`, then train, then `quantize_(model, QATConfig(base_config, step="convert"))`.
  - As of torchao 0.16.0, INT4 weights with INT8 activations ("for edge") are supported via `Int8DynamicActivationIntxWeightConfig`.
  - With LoRA, fake-quantization is applied to the frozen weights, the LoRA adapters and (optionally) the activations, "since the adapters will eventually be merged back into the weights".
  - "The quantization scheme simulated during QAT should match the actual post-training quantization scheme as much as possible."

  — [PyTorch blog: QAT in TorchAO (II), 2026-03-04](https://pytorch.org/blog/quantization-aware-training-in-torchao-ii/)
- The torchao QAT docs show the int8 per-token asymmetric activation + int4 group-32 weight fake-quant via `IntxFakeQuantizeConfig`. Embeddings get a separate weight-only prepare pass with a `filter_fn`, since activation fake-quant isn't supported for embeddings. The legacy `Int8DynActInt4WeightQATQuantizer(group_size=32)` covers the same scheme but "may be removed soon" — [torchao QAT docs](https://docs.pytorch.org/ao/main/workflows/qat.html)
- **LoRA+QAT overhead**: 1.89× faster and 36.1% less memory than vanilla full QAT — [PyTorch blog QAT II](https://pytorch.org/blog/quantization-aware-training-in-torchao-ii/); [torchao QAT docs](https://docs.pytorch.org/ao/main/workflows/qat.html)
- **Recovery numbers**:
  - Unsloth INT4 QAT+LoRA recovered 66.9% of Gemma3-4B's GPQA loss, 45.5% of Gemma3-12B's BBH loss, 36.3% of Qwen3-4B's WikiText PPL increase and 36.0% of Llama-3.2-1B's MMLU-Pro loss.
  - In raw accuracy: +2.0 of the 5.8 points lost on Qwen3-4B MMLU-Pro, and +0.7 of the 2.0 points lost on Llama-3.2-3B MMLU-Pro.

  — [PyTorch blog QAT II](https://pytorch.org/blog/quantization-aware-training-in-torchao-ii/)
- **torchao docs table (int4 weight-only QAT+LoRA, group size 128, 1×H100, FineTome-100k, lr 2e-5, bs 64)**:
  - Qwen3-4B-Instruct MMLU-Pro 0.4909 bf16 / 0.4328 int4 / 0.4524 QAT (33.7% recovered).
  - Llama3.2-3B WikiText 12.13 / 13.35 / 12.88 (38.4%), BBH 0.548 / 0.497 / 0.517 (40.1%).

  — [torchao QAT docs](https://docs.pytorch.org/ao/main/workflows/qat.html)
- **Earlier torchao/torchtune full QAT, Llama3-8B, 8da4w**: recovers up to 96% of the Hellaswag degradation and 68% of the WikiText perplexity degradation vs PTQ. For Llama2-7B: 62% of Hellaswag, 58%/57% of word/byte PPL — [PyTorch QAT blog (I)](https://pytorch.org/blog/quantization-aware-training/) (figures as surfaced in search results; the original page wasn't fetched)
- **Meta Llama-3.2-1B QAT+LoRA ("QLoRA")** on the ExecuTorch 8da4w-g32 scheme. The recipe was a QAT SFT round, then a frozen backbone with LoRA SFT on all layers (LoRA kept in BF16), then DPO. MMLU 49.0 vs BF16 49.3 vs vanilla PTQ 43.3, and GSM8K 46.5 vs 44.4 vs 33.1. On a OnePlus 12: decode 45.8 tok/s, prefill 252 tok/s, 1127 MB model — [Llama-3.2-1B-Instruct card](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)
- **Unsloth**:
  - QAT is enabled via `qat_scheme` in `FastLanguageModel.get_peft_model(...)` (LoRA) or `from_pretrained(..., full_finetuning=True)`.
  - Documented schemes are `fp8-int4`, `fp8-fp8`, `int8-int4`, `int4`. The PyTorch blog's code comment also lists `phone-deployment`.
  - After training, `quantize_(model, QATConfig(step="convert"))` then `save_pretrained_torchao`.
  - Install pin: `torchao==0.14.0`.
  - Claims "up to 70%" recovery.

  — [Unsloth QAT docs](https://unsloth.ai/docs/blog/quantization-aware-training-qat); [PyTorch blog QAT II](https://pytorch.org/blog/quantization-aware-training-in-torchao-ii/)
- **Unsloth phone flow for Qwen3-0.6B** (`qat_scheme="phone-deployment"` = int8 dynamic activations + int4 weights on Linear, with `full_finetuning=True`, `max_seq_length=1024`). Export goes through `export_llama`, not optimum:
  ```
  python -m executorch.examples.models.qwen3.convert_weights "phone_model" pytorch_model_converted.bin
  python -m executorch.examples.models.llama.export_llama --model "qwen3_0_6b" --checkpoint pytorch_model_converted.bin --params 0.6B_config.json --output_name qwen3_0.6B_model.pte -kv --use_sdpa_with_kv_cache -X --xnnpack-extended-ops --max_context_length 1024 --max_seq_length 128 --dtype fp32 --metadata '{"get_bos_id":199999, "get_eos_ids":[200020,199999]}'
  ```
  The result is a ~472 MB .pte running at ~40 tok/s on Pixel 8 / iPhone 15 Pro. Note that the export command has no `--qmode`: the checkpoint is already torchao-quantized — [Unsloth deploy-llms-phone](https://unsloth.ai/docs/basics/inference-and-deployment/deploy-llms-phone)
- The PyTorch-team Qwen3-4B-INT8-INT4 card uses the same pattern: torchao-quantized HF checkpoint → `convert_weights` → `export_llama` with no qmode. It warns that the ExecuTorch CI test is the source of truth for the steps — [pytorch/Qwen3-4B-INT8-INT4](https://huggingface.co/pytorch/Qwen3-4B-INT8-INT4)
- optimum-executorch's quantize step has no logic to detect or skip already-quantized checkpoints. It applies its own PTQ configs (default `hqq_scale_only` scale selection) — [optimum-executorch quantization.py](https://raw.githubusercontent.com/huggingface/optimum-executorch/main/optimum/exporters/executorch/quantization.py)

### Inferences
- **Exact-match route (recommended if doing QAT)**: QAT-train with `Int8DynamicActivationIntxWeightConfig(weight_dtype=torch.int4, weight_granularity=PerGroup(32))` plus int8 per-axis embedding fake-quant. Then convert and save, then `convert_weights` + `export_llm`/`export_llama` without qmode. The deployed integer weights are then exactly the trained ones.
- **optimum route with QAT**: skip `convert`, strip the fake-quant wrappers (or reload the trained bf16 weights), merge LoRA, then run `optimum-cli ... --qlinear 8da4w --qlinear_group_size 32 --qembedding 8w`. The weights will have "learned" the int4 grid, so re-quantization should land close. But optimum's default `hqq_scale_only` scale search may pick different scales than the min/max symmetric fake-quant used in training, so the match is not exact. Verify by comparing logits of the QAT-converted torchao model against the .pte (ExecuTorch pybindings) on a handful of prompts. Neither path's numerical equivalence has been verified by a primary source for Qwen3-0.6B with ExecuTorch 1.5.1.
- Unsloth's `int8-int4` group size isn't documented on the pages read. It must equal the export group size (32 in the ExecuTorch/optimum defaults). torchao's Unsloth int4 example used 128.
- Version risk: Unsloth pins torchao 0.14.0, while the project stack (torch 2.14 / ExecuTorch 1.5.1) almost certainly ships a newer torchao. A torchao-quantized checkpoint serialised with one torchao version may not deserialise in another. Training and export should probably happen in the same environment, or the QAT'd weights should be passed as plain bf16.
- Recovery to expect: about 35-70% of the PTQ gap on general benchmarks. For a narrow fine-tuned task (MCQ diagnosis), Meta's Llama-3.2-1B and the PARQ GSM8K results suggest QAT on in-domain data can fully close the gap. The PARQ result is a 4-bit QAT model nearly 17% more accurate than 4-bit PTQ on grade-school math — [PyTorch blog QAT II](https://pytorch.org/blog/quantization-aware-training-in-torchao-ii/).
- Time overhead: QAT+LoRA is cheaper than full QAT (1.89×). I found no number for QAT+LoRA vs plain LoRA wall-clock; fake-quant ops add some per-step cost.

### Gaps
- No published QAT recovery numbers specifically for Qwen3-0.6B or 1.7B with 8da4w. Unsloth's "70%" claim gives no benchmark or baseline.
- No source confirming that optimum-executorch 1.1.0 can consume a torchao-quantized (QAT-converted) checkpoint directly. The code read suggests it cannot.
- Wall-clock overhead of QAT+LoRA vs plain LoRA is unreported.
- Whether `qat_scheme="phone-deployment"` / `int8-int4` works with LoRA (vs full fine-tuning only) in current Unsloth isn't explicitly documented. The phone guide uses `full_finetuning=True`.

## Q3. Merge LoRA → bf16/fp32 checkpoint → `optimum-cli export executorch` (local path, tokenizer, chat template, known errors)

### Takeaway
optimum-executorch's CLI accepts "path on disk" for `--model` (main branch help text), so a merged local Qwen3 checkpoint should export with the same command already proven for base Qwen3-0.6B. The tokenizer is **not** packaged into the .pte: ship `tokenizer.json` alongside it and apply the chat template in the app. Release-specific behaviour of 1.1.0 wasn't verified.

### Cited Findings
- `-m, --model`: "Model ID on huggingface.co or path on disk to load model from." Other flags: `--task` (default text-generation), `--recipe` (default xnnpack), `--use_custom_sdpa`, `--use_custom_kv_cache`, `--qlinear`, `--qlinear_group_size`, `--qembedding`, `--qembedding_group_size`, `--max_seq_len` (defaults to the model's `max_position_embeddings` if unset), `--dtype`, `--disable_dynamic_shapes` — [optimum-executorch CLI source (main)](https://raw.githubusercontent.com/huggingface/optimum-executorch/main/optimum/commands/export/executorch.py)
- The Transformers docs say a local export needs weights and tokenizer files in one directory passed via `--model`, with `--task` set explicitly. They show an `optimum-cli export executorch` command for Qwen3 with XNNPACK, custom SDPA and custom KV cache — [Transformers serialization docs](https://huggingface.co/docs/transformers/serialization.md) (via search snippet; not fetched in full)
- The optimum-executorch README examples load the tokenizer separately with `AutoTokenizer.from_pretrained(...)`. On-device it points to the ExecuTorch Qwen3 runner guide — [optimum-executorch README](https://github.com/huggingface/optimum-executorch)
- The ExecuTorch LoRA example runner takes `--tokenizer_path` pointing at the HF tokenizer directory and an `--apply_chat_template` flag — [executorch-examples LoRA README](https://raw.githubusercontent.com/meta-pytorch/executorch-examples/main/program-data-separation/cpp/lora_example/README.md)
- The ExecuTorch Qwen3 export via export_llama needs BOS/EOS metadata: `{"get_bos_id":199999, "get_eos_ids":[200020,199999]}` in the PyTorch-team and Unsloth examples. export_llm docs say these values "can usually be found in the model's `tokenizer_config.json`" — [pytorch/Qwen3-4B-INT8-INT4](https://huggingface.co/pytorch/Qwen3-4B-INT8-INT4); [ExecuTorch export_llm docs](https://docs.pytorch.org/executorch/main/llm/export-llm.html)
- To quantize the embedding and lm_head differently, the PyTorch-team recipe first **unties** them: set `tie_word_embeddings=False`, clone `lm_head.weight`, clear `_tied_weights_keys` — [pytorch/Qwen3-4B-INT8-INT4](https://huggingface.co/pytorch/Qwen3-4B-INT8-INT4). optimum's quantization code has a TODO that tied weights aren't handled explicitly — [optimum-executorch quantization.py](https://raw.githubusercontent.com/huggingface/optimum-executorch/main/optimum/exporters/executorch/quantization.py)
- Known export error in the other path: `AttributeError: 'BaseConfig' object has no attribute 'adapter_checkpoint'` with `export_llama` on ExecuTorch 0.7.0 (Llama 3.2 1B / Qwen2.5 1.5B). A maintainer suggested ExecuTorch 1.0 or optimum-executorch, and it was closed without a root cause — [pytorch/executorch#14810](https://github.com/pytorch/executorch/issues/14810)
- In Unsloth's phone guide, training used `max_seq_length=1024` but export used `--max_seq_length 128` (prompt-length cap) with `--max_context_length 1024`. The two are different knobs in export_llm: `max_seq_length` is the max prompt length and `max_context_length` is the KV cache size — [Unsloth deploy-llms-phone](https://unsloth.ai/docs/basics/inference-and-deployment/deploy-llms-phone); [ExecuTorch export_llm docs](https://docs.pytorch.org/executorch/main/llm/export-llm.html)

### Inferences (recommended concrete steps; not verified end-to-end on 1.1.0/1.5.1)
1. `base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", torch_dtype=torch.bfloat16)`. Load the base in bf16, **not** a 4-bit bnb base, even if training used QLoRA, because merging into dequantized NF4 weights bakes in NF4 error.
2. `model = PeftModel.from_pretrained(base, adapter_dir).merge_and_unload()`, then `model.save_pretrained(out_dir, safe_serialization=True)` and `tokenizer.save_pretrained(out_dir)`. This copies `tokenizer.json`, `tokenizer_config.json` (which holds the chat template) and `generation_config.json`.
3. Keep `config.json` `tie_word_embeddings` as in the base model. Merging LoRA doesn't untie unless LoRA targeted `lm_head`/`embed_tokens`. If it did, check that the saved config matches the weights.
4. Run:
   ```
   optimum-cli export executorch --model ./merged --task text-generation --recipe xnnpack --use_custom_sdpa --use_custom_kv_cache --qlinear 8da4w --qlinear_group_size 32 --qembedding 8w --max_seq_len 1024 --output_dir ./out
   ```
   Pass the group size explicitly so it doesn't depend on version defaults.
5. Ship `out/model.pte` plus `merged/tokenizer.json`. Apply the Qwen3 chat template yourself, using the exact same template string used during fine-tuning, including `enable_thinking=False` / the empty `<think></think>` block if training used that format. Then set EOS so the runner stops on `<|im_end|>`.
6. Sanity check: generate a few eval prompts with the merged HF model in fp32, then with the .pte via ExecuTorch pybindings. Diff the outputs to separate quantization loss from export bugs.
- A mismatch between the training chat format and the runtime prompt format is likely to cost more quality than 8da4w on a fine-tuned 0.6B. Keep one source of truth for the template.

### Gaps
- Couldn't confirm against the 1.1.0 release tag that `--qlinear_group_size`, `--qembedding_group_size` and the `8da4w,8da8w` fallback exist in that version. They are verified on main only. Run `optimum-cli export executorch --help` locally.
- Found no issue reports specific to exporting a *local fine-tuned* Qwen3 checkpoint with optimum-executorch. No known errors were surfaced, which is not proof there are none.
- Whether transformers 5.0.0rc1's `save_pretrained` writes anything optimum-executorch 1.1.0 can't read (e.g., new config fields) wasn't verified. The project's working base export suggests it is fine.

## Q4. ExecuTorch-native LoRA (adapter checkpoint + program-data separation .ptd) vs merging

### Takeaway
Yes, it exists. ExecuTorch ≥1.1.0 can export a LoRA model as a small .pte (program + adapter) plus a shared foundation .ptd, with Qwen3-0.6B as the reference example. It only pays off when **several** adapters share one base on the device. For a single fine-tuned model, merging is simpler and has no runtime LoRA matmul overhead. When merged, the quantizer also sees the final weights; native LoRA keeps adapters unquantized on top of a quantized base.

### Cited Findings
- The executorch-examples `program-data-separation/cpp/lora_example` uses base `unsloth/Qwen3-0.6B` and adapter `lucylq/qwen3_06B_lora_math`. It needs the training outputs `adapter_config.json` + `adapter_model.safetensors` and requires `executorch>=1.1.0`. Export is `bash export_lora.sh` (fp32) or `bash export_lora.sh -q` (8da4w + embedding quant) — [LoRA example README](https://raw.githubusercontent.com/meta-pytorch/executorch-examples/main/program-data-separation/cpp/lora_example/README.md)
- Quantized artefacts: LoRA weights .ptd 39 MB, LoRA program .pte 855 KB, base weights .ptd 473 MB, base program .pte 621 KB. The LoRA .ptd is also 39 MB in the fp32 variant, which suggests the adapters stay unquantized — [LoRA example README](https://raw.githubusercontent.com/meta-pytorch/executorch-examples/main/program-data-separation/cpp/lora_example/README.md)
- Runtime RSS: LoRA model 1393.59 MiB after load and 1468.09 MiB after prefill, vs base 2227.76 MiB. With 8da4w + embedding quant and XNNPACK weight sharing, two models total 2.1 GB vs 2.5 GB without sharing. Weight sharing relies on the XNNPACK global weight cache (`-DEXECUTORCH_XNNPACK_ENABLE_WEIGHT_CACHE`) — [LoRA example README](https://raw.githubusercontent.com/meta-pytorch/executorch-examples/main/program-data-separation/cpp/lora_example/README.md)
- An executorch-examples PR shows `export_llm` with `base.checkpoint` and `export.foundation_weights_file="foundation.ptd"`; "You only need to keep one `foundation.ptd` file." — [executorch-examples PR #121 (mirror)](https://google.18789066745.workers.dev/meta-pytorch/executorch-examples/pull/121/files). The ExecuTorch paper describes PTE programs referencing external PTD weights shared across LoRA variants — [ExecuTorch paper, arXiv 2605.08195](https://arxiv.org/pdf/2605.08195)
- The export_llm docs page does not document the LoRA flags (`adapter_checkpoint`, `adapter_config`, `foundation_weights_file`). They have to be read from `export_lora.sh` or the source — [ExecuTorch export_llm docs](https://docs.pytorch.org/executorch/main/llm/export-llm.html)

### Inferences
- For this project (one diagnostic model on a Pi 5), merge, then quantize, then single .pte is the better path. It has fewer moving parts, the existing optimum pipeline works, and there is no extra adapter compute per token. Native LoRA becomes attractive only if, for example, separate per-subject or per-language adapters are swapped on one device. In that case the 39 MB per adapter vs ~470 MB per full model matters.
- With native LoRA plus PTQ, the base is quantized independently of the adapter, so the adapter never "saw" the int4 base error unless training used QAT. The QAT-on-frozen-weights design in torchao (Q2) addresses exactly this.

### Gaps
- Exact `export_llm` LoRA flag names weren't read from source (the `export_lora.sh` contents weren't retrieved). No Pi 5 numbers for the LoRA-separated model, and no decode-speed comparison of merged vs unmerged.

## Q5. Constrained / grammar (JSON) decoding in ExecuTorch's TextLLMRunner

### Takeaway
No grammar or JSON-schema engine ships in ExecuTorch. On 15 May 2026 a `LogitProcessor` hook was merged into `main` (`TextTokenGenerator.add_logit_processor`); its stated purpose includes grammar-constrained decoding. Whether that is in 1.5.1 is unverified. For an MCQ task, restricting or scoring the answer tokens yourself is simpler than full grammar decoding.

### Cited Findings
- PR #19517 (merged into `main` 15 May 2026) adds a `LogitProcessor` interface under `extension/llm/sampler/`. `TextTokenGenerator` gains `add_logit_processor` / `clear_logit_processors` / `num_logit_processors`, and processors run in registration order between the forward pass and the sampler. The description says it "Enables grammar-constrained decoding, logit biasing, repetition penalties, and similar transforms". It does not implement a grammar engine — [pytorch/executorch#19517](https://github.com/pytorch/executorch/pull/19517)
- Review notes (via mirror) say processors must be set before `generate()` and the chain only accepts Float logits — [PR #19517 mirror](https://gh.ali360.cloudns.ch/pytorch/executorch/pull/19517)
- Follow-up PR #19991 (mirror) factors out logit-processor application and adds session primitives (seek, prefill, single-step decode) to the text LLM runner. PR #19351 (mirror) makes the sampler persistent with per-call `set_temperature` — [PR #19991 mirror](https://gh.r-mj.com/pytorch/executorch/pull/19991); [PR #19351 mirror](https://github.kxpsado.workers.dev/pytorch/executorch/pull/19351/)
- Grammar engines such as XGrammar compile CFGs (including JSON) into token masks applied before sampling, which is the mechanism such a hook would host — [XGrammar, arXiv 2411.15100](https://arxiv.org/html/2411.15100v2)

### Inferences
- MCQ-specific alternatives that need no grammar engine:
  - **Option scoring**: run one prefill of prompt + "Answer:" through the ExecuTorch `Module` (or a runner with single-step decode), read logits for the tokens " A" / " B" / " C" / " D", and take the argmax. You get calibrated probabilities as well. It is deterministic and always valid.
  - **Logit masking**: if 1.5.1 contains the `LogitProcessor` hook, register a processor that masks everything except allowed tokens at each step. For fixed short schemas, a hand-written state machine over a small token whitelist is enough.
  - **Prompt + validate + retry** in the host language. This is cheap for short outputs, but each retry costs a full decode on a Pi 5.
- Option scoring also sidesteps the IFEval/BFCL-style format degradation seen under 4-bit PTQ (Q1).

### Gaps
- Not verified whether ExecuTorch 1.5.1 contains PR #19517 or #19991. Check the 1.5.x release notes or `extension/llm/sampler/` in the installed source.
- No ExecuTorch issue or PR found that implements JSON-schema or GBNF constrained decoding. No XGrammar/llguidance integration found.

## Q6. Expected Raspberry Pi 5 speed for Qwen3-0.6B / 1.7B 8da4w with XNNPACK/KleidiAI (measured numbers only)

### Takeaway
I found **no published measured ExecuTorch numbers for Qwen3-0.6B or 1.7B on a Raspberry Pi 5**. The only ExecuTorch-on-Pi-5 data points are other models: Llama3-8B 4-bit at about 2 tok/s (2024), and a Gemma 4 E2B anecdote at 0.87 tok/s (post no longer reachable). The Pi 5's Cortex-A76 relies on the SDOT int4 path that KleidiAI/XNNPACK added in ExecuTorch 0.7, not the faster I8MM path. Measure it yourself.

### Cited Findings
- ExecuTorch 0.7 enabled KleidiAI by default. The 2025 work targeted Int4 matmul using SDOT (Armv8.2+) to reach older phones "and edge devices like the Raspberry Pi 5". The I8MM-optimized kernels need Armv8.6. The flagship numbers (Llama 3.2 1B on Galaxy S24+: >350 tok/s prefill, >40 tok/s decode) are I8MM figures. No Pi 5 numbers are given — [PyTorch blog: ExecuTorch + KleidiAI, 2025-08-13](https://pytorch.org/blog/bringing-generative-ai-to-the-masses-with-executorch-and-kleidiai/); [Arm/HF blog, ExecuTorch 0.7](https://huggingface.co/blog/arm/executorch-0-dot-7)
- Llama3-8B 4-bit on Pi 5 with ExecuTorch: about 2 tok/s (2024) — [PyTorch dev-discuss](https://dev-discuss.pytorch.org/t/run-llama3-8b-on-a-raspberry-pi-5-with-executorch/2048) (from search snippet)
- Gemma 4 E2B on Pi 5 (8 GB) with ExecuTorch 1.2.0 + XNNPACK: 0.87 tok/s, vs 6.71 tok/s for llama.cpp on a 16 GB Pi 5. The author blamed an XNNPACK fused-INT4 issue on aarch64 and worked around it with `per_op_mode=True` — [dev.to post](https://dev.to/bamb00boy/first-gemma-4-executorch-deployment-on-raspberry-pi-5-and-why-its-77x-slower-than-llamacpp-gmb) (from search snippet; the page returned 404 when fetched, so treat as unverified anecdote)
- Comparison points from other runtimes and devices:
  - Qwen3 (size unstated in snippet) at 13.9 tok/s with llama.cpp on Pi 5 — [LiteRT INT8 LLM ICCVW 2025 supplemental](https://openaccess.thecvf.com/content/ICCV2025W/AIM/supplemental/Yoon_LiteRT-Optimized_INT8_LLM_ICCVW_2025_supplemental.pdf) (search snippet)
  - Qwen3-0.6B QAT 8da4w via ExecuTorch at ~40 tok/s on Pixel 8 / iPhone 15 Pro — [Unsloth](https://unsloth.ai/docs/basics/inference-and-deployment/deploy-llms-phone)
  - Llama-3.2-1B QAT+LoRA at 45.8 tok/s decode on OnePlus 12 — [Llama-3.2-1B card](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)
- The project's own measurements (repo `docs/SUBMISSION.md`) for the base Qwen3-0.6B .pte (~470 MB): Arduino UNO Q (Cortex-A53) prefill 9.8 tok/s and decode 0.37 tok/s ("no custom kernels on this chip"); Apple M4 Mac prefill 854 tok/s and decode 96 tok/s — /Users/arushjain/Documents/namma-ai/docs/SUBMISSION.md

### Inferences
- The Cortex-A53 result (0.37 tok/s decode) isn't predictive for the Pi 5. The A53 lacks SDOT (Armv8.0), so it falls back to slow generic kernels. The A76 has SDOT and should hit the KleidiAI path.
- Rough, **unmeasured** expectation: phones with I8MM decode Qwen3-0.6B 8da4w at ~40 tok/s. Pi 5 decode is memory-bandwidth-bound (LPDDR4X), and the lack of I8MM mainly hurts prefill. That points to roughly the low tens of tok/s decode for 0.6B and somewhat under half that for 1.7B. This is an estimate only and must be measured. Build ExecuTorch's `llama_main` (or the project runner) natively on the Pi 5 with XNNPACK + KleidiAI enabled. Check the Gemma report's fused-INT4 issue does not reproduce, and record prefill and decode tok/s for 0.6B and 1.7B at the target prompt length.

### Gaps
- No measured ExecuTorch numbers for Qwen3-0.6B or 1.7B (or Llama-3.2-1B) on a Raspberry Pi 5 from any source. The Gemma 4 Pi 5 report couldn't be re-fetched. The dev-discuss and ICCVW figures were seen only as search snippets.
- No confirmation of whether the aarch64 XNNPACK fused-INT4 issue (if real) affects ExecuTorch 1.5.1.
