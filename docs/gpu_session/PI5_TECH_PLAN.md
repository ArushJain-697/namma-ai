# GURU-0.6B on Raspberry Pi 5 (8 GB): technical plan for the Arm judge (14 Nov 2026)

Labels used below: **[calc]** = arithmetic from the real model config (no Pi needed), **[src]** = from a web source (link),
**[TODO-Pi]** = must be measured on the Pi, **[GPU]** = measured on the RTX 4060 laptop. Nothing here is a Pi measurement.

## 1. What an Arm judge will ask, and what we answer
| Question | Our answer / how we get the number |
|---|---|
| Model size on disk and in RAM | **[calc]** Qwen3-0.6B: 28 layers, hidden 1024, 16 q heads / 8 KV heads, head_dim 128, vocab 151,936, tied embeddings. 440 M non-embedding + 156 M embedding = 596 M params. fp16 = 1,192 MB. **8da4w + 8-bit embedding ~ 390 MB**. [TODO-Pi] confirm the .pte file size. |
| Peak RAM (RSS) | **[calc]** weights ~390 MB + KV cache 117 MB (fp16, 1,024 tokens) or 59 MB (int8) + activations/runtime. Expect well under 1 GB of the 8 GB. [TODO-Pi] `/usr/bin/time -v` -> "Maximum resident set size". |
| Why 0.6B and not bigger | **[GPU]** 1.7B was not clearly better on options (word overlap 0.17 vs 0.12), still marked wrong answers correct. **[calc]** 1.7B has ~3x the weight bytes, so ~3x slower decode (decode is memory-bandwidth bound). |
| Decode speed (tokens/s) | **[calc]** Pi 5 LPDDR4X-4267 peak ~17 GB/s (my background knowledge, not verified by a source). Each token reads ~390 MB -> upper bound ~44 tok/s; at ~35% efficiency ~15 tok/s. A paper reports Qwen3-0.6B INT8 on a Pi 5 with llama.cpp at 13.9 tok/s ([ICCV 2025 W supplement](https://openaccess.thecvf.com/content/ICCV2025W/AIM/supplemental/Yoon_LiteRT-Optimized_INT8_LLM_ICCVW_2025_supplemental.pdf)). [TODO-Pi] measure ours. |
| Prefill speed / time to first token | **[calc]** 0.44 GMAC per prompt token. Prefill is compute bound (Cortex-A76 NEON + dot-product int8). [TODO-Pi] measure tok/s on a 150-token prompt. |
| End-to-end time per quiz question | Two-call design: Job Q (~40 tokens) + Job W x2 (~30 tokens each, plus 2 more only if fewer than 3 distinct options). [TODO-Pi] time = prefill + decode for each call. |
| Power and energy | [TODO-Pi] Report **watts and joules per question**. Method from Arm: read the Pi 5 PMIC, energy per token ([Arm learning path](https://learn.arm.com/learning-paths/cross-platform/rpi5-energy-per-token/)). Jeff Geerling measured an 8 GB Pi 5 at 13.9 W peak on an LLM run ([benchmarks](https://github.com/geerlingguy/ai-benchmarks)); model size there is unknown, so treat as an upper reference. |
| Thermals | [TODO-Pi] `vcgencmd measure_temp` and `vcgencmd get_throttled` before/after 50 questions; use the official active cooler. |
| Accuracy cost of quantization | [GPU] have: held-out loss 1.256 (fp16 merged). [TODO] re-run the same held-out set on the exported 8da4w model and report the change. A judge will ask. |
| Offline / privacy | No network at inference; model + code only. |
| Instruction-set use | Cortex-A76 has NEON and dot-product (int8), no SVE or i8mm (my knowledge, verify with `lscpu`). XNNPACK/KleidiAI int4/int8 kernels use dot-product. |

## 2. RISK to check first (backend speed)
One developer reports ExecuTorch + XNNPACK on a Pi 5 (Cortex-A76) at **0.87 tok/s vs 6.71 tok/s for llama.cpp** on a larger model, and says the
XNNPACK backend rejected fused INT4 subgraphs on aarch64 (workaround `per_op_mode=True`, which disables fusion)
([write-up](https://dev.to/bamb00boy/first-gemma-4-executorch-deployment-on-raspberry-pi-5-and-why-its-77x-slower-than-llamacpp-gmb)). One unverified source, other
model, but it is exactly our stack. **Do this first:** run the same merged model through both ExecuTorch (8da4w) and llama.cpp (GGUF Q4_0 / Q4_K_M)
on the Pi, take the faster one, and report the comparison. Arm's own post claims KleidiAI in ExecuTorch 0.7 gives >350 tok/s prefill and >40 tok/s decode, but the
snippet does not name the model or device, so do not quote it for the Pi 5 ([Arm blog](https://huggingface.co/blog/arm/executorch-0-dot-7)).

## 2b. Quantization costs QUALITY (measured on GPU by simulating the export; re-measure on the real .pte)
Held-out loss on the 310 two-job validation examples (lower is better). Simulated with group-wise weight rounding + int8 dynamic activations + 8-bit embedding.
| Setting | Q loss | W loss | Est. weights | Est. decode on Pi* |
|---|---|---|---|---|
| bf16 (what all our quality tests used) | 1.217 | 1.429 | 1,192 MB | not used |
| **8-bit weights + 8-bit activations** | **1.223** | **1.436** | ~596 MB | ~10 tok/s |
| 4-bit, group 128 | 1.385 | 1.661 | ~390 MB | ~15 tok/s |
| 4-bit, group 32 (default 8da4w style) | 1.345 | 1.564 | ~404 MB | ~15 tok/s |
| 4-bit g32, down_proj + first/last layers at 8-bit | 1.306 | 1.511 | ~464 MB | ~13 tok/s |
*[calc] 17 GB/s x 35% efficiency / bytes read per token. Not measured on a Pi.
**Reading:** 8-bit is effectively lossless (+0.006). 4-bit costs about +0.13 loss, bigger than the gap between all our training runs; mixed precision wins back only about 30% of it.
**Recommendation (quality first):** export with 8-bit weights (check `optimum-cli export executorch --help` for the exact flag, e.g. 8w/8da8w) and report 4-bit as an optional "eco mode".
Cost: ~1.5x slower decode, still ~600 MB of 8 GB RAM. Source for the risk: [Qwen3 quantization study](https://arxiv.org/pdf/2505.02214) (0.6B degrades most at low bits).
If 4-bit is needed for speed/power: quantization-aware training recovers part of the loss ([torchao](https://pytorch.org/blog/quantization/), [Qwen3-4B QAT+LoRA](https://github.com/pytorch/ao/pull/3214/files)).

## 3. Optimisations, ranked by (impact x ease)
(Quality-neutral only. Retraining-based items must be accepted only if held-out loss and a blind read stay the same.)
0. **Lossless speedups to test on the Pi:** prompt-lookup / n-gram speculative decoding (llama.cpp `--spec-type ngram-simple`; output is checked by the model so it does not change the answer; gain depends on how much output copies the prompt) and reusing the cached system-prompt prefix ([llama.cpp](https://www.mintlify.com/ggml-org/llama.cpp/inference/speculative-decoding), [KV reuse](https://github.com/ggml-org/llama.cpp/discussions/13606)).
   Over-generate then filter: ask for 5-6 questions and show the best 3 (valid layout, distinct options, key not the longest). Same model, better shown quality, costs extra seconds.
1. **Stop at `<|im_end|>` and cap tokens per job.** The ExecuTorch runner does not stop at Qwen's end token (from the handoff). Set max new tokens ~48 (Q) and ~40 (W). Saves decode time and joules directly.
2. **Short system prompts.** Q_SYSTEM / W_SYSTEM are ~60-80 tokens each, re-read on every call. The fine-tuned model does not need them: retrain with a 1-word prompt ("Q", "W"). Saves ~60-80 prefill tokens x 3-5 calls per question. Cheap to do (a 6-minute run here). Also cache the KV of the fixed prefix if the runtime allows.
3. **Adaptive sampling.** Call Job W twice; call two more times only if fewer than 3 distinct options. [GPU] measured 141-154 of 156 questions get 3 distinct options with 2-4 samples.
4. **Pick the faster backend** (section 2), then tune threads (3 vs 4 on the 4 cores), `performance` governor, active cooling.
5. **KV cache**: keep `--max_seq_len 1024`; prompts are ~150-250 tokens, so 512 would halve KV memory (117 -> 58 MB fp16). Try int8 KV cache if the exporter supports it (check).
6. **Power mode for the demo**: Arm's data shows 1 thread at 1.5 GHz used 30% less net energy per token than at 2.4 GHz, at 32% fewer tokens/s ([Arm](https://learn.arm.com/learning-paths/cross-platform/rpi5-energy-per-token/clock-and-threads/)). Offer "eco mode" vs "fast mode" and report both (joules/question, seconds/question).
7. **Quantization settings**: compare 8da4w group size 32 vs 128 (accuracy vs size) and 8-bit embedding vs 4-bit. Report held-out loss for each.
8. **Do not load Python/torch on the Pi**: use the C++ runner; mmap the .pte file.

## 4. Measurement checklist for the Pi (copy-paste)
- `lscpu | grep -i -E "model name|flags"`  (confirm asimddp)
- `/usr/bin/time -v <runner ...>`  -> peak RSS, wall time
- `vcgencmd measure_temp ; vcgencmd get_throttled`  before and after a 50-question run
- `vcgencmd pmic_read_adc`  sampled every 100 ms during a run -> mean W and joules per question
- Per call log: prompt tokens, new tokens, prefill ms, decode ms, tok/s. Report mean and p95 over the 40 eval passages (3 questions each).
- Same 120 questions on both backends, same quantization, same prompts.

## 5. What we can claim today (honest)
- Model quality **[GPU]**: two-job pipeline beat the single-call pipeline in a blind read (8/12 vs 3/12 good questions). Wrong-option sets fully good: 10/20 (model) vs 20/20 (teacher-written) in a blind read. Known failure: a wrong option that is really correct.
- Efficiency **[calc]**: ~390 MB weights, ~117 MB KV, expected <1 GB RSS.
- Everything about Pi speed, power and temperature is **not measured yet**.
