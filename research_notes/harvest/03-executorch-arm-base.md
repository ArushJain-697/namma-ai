# Harvest 03: official base (ExecuTorch and Arm)

**Status: desk review complete for all coordinator priorities. Nothing has been built or run,** so every "works" below means "the source says so". Firecrawl ran out of credits partway through; the coordinator then directed the rest through `curl`, WebSearch and WebFetch. Section 5 lists what remains unread.

## Pins

| Repo | Commit | Basis |
|---|---|---|
| pytorch/executorch, release/1.5 | `985c1ceccc8bb8b6a32294f71aeb5d2f299562f7` (PR #23018) | First entry on the release/1.5 commits page, 2026-11-04. `setup.sh` re-fetched at this SHA: same size, and line numbers match. |
| ArmDeveloperEcosystem/courses-code-executorch, main | `1045d5161effcf8df08ffbb734109118f1beab28` (13 Oct 2026) | Latest commit. The repo was renamed from `arm-courses-code-executorch`. |
| meta-pytorch/tokenizers | `61a10ac61245a68374ace4900e49cd2aba65fb39` | Submodule pin in `extension/llm` |
| google/XNNPACK | `92a7ad501b9516f9fecae119e0146dd1f58e54c1` | Submodule pin, `backends/xnnpack/third-party/XNNPACK` |

## Evidence labels

- **[READ]**: the cited lines were fetched and read. Most files were read by targeted line range or search, not end to end.
- **[LISTED]**: only the path, or a README heading, was seen.
- **[MEMORY]**: my recollection, unchecked. Treat as a hypothesis.

Effort figures are my estimates.

## 1. Licences

| Project | Licence | Source | Tag consequence |
|---|---|---|---|
| pytorch/executorch | BSD 3-clause. Keep the copyright notice and disclaimer in source and binary distributions; no use of Meta's or contributors' names for endorsement. | Root `LICENSE`, read | TAKE-CODE |
| `examples/models/llama/` | **Conflict.** The folder's `LICENSE` is the **Llama 2 Community License Agreement** (125 lines; first lines read), while the `main.cpp` and `runner.cpp` headers point to the root BSD licence. | Both read | **TAKE-IDEA, as unclear.** Build it unmodified from upstream rather than vendoring. Ask a human only if we ever need to copy from this folder. |
| courses-code-executorch | Arm-authored code is **BSD-3-Clause-Clear**. Third-party code, dependencies, weights and datasets keep their own licences. `LICENSE.md` is a short pointer with no full text or copyright line, so take the text from SPDX. [MEMORY] Clear BSD expressly grants no patent rights. | `LICENSE.md`, read in full | TAKE-CODE (BSD family); retain the notice |
| meta-pytorch/tokenizers | BSD 3-clause, Copyright 2024 Meta | `LICENSE`, first lines read | TAKE-CODE |
| Llama 3.2 weights | Hugging Face metadata says `llama3.2`; licence text not read. Learning Path FAQ confirms an acceptable use policy applies. | HF API | Download, never commit. Check attribution terms. |
| google/XNNPACK, arm-learning-paths | Not read | n/a | Cited for reference only; TAKE-IDEA |

## 2. Harvest table

Pinned base used below: `ET` = `https://github.com/pytorch/executorch/blob/985c1ceccc8bb8b6a32294f71aeb5d2f299562f7`, `AC` = `https://github.com/ArmDeveloperEcosystem/courses-code-executorch/blob/1045d5161effcf8df08ffbb734109118f1beab28`.

### pytorch/executorch

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| executorch | **Python `TextLLMRunner`** | **[READ]** Text-only runner exposed to Python. Takes model path, tokenizer path, optional data path; `generate` takes prompt, config, a per-token callback and a stats callback, and releases the GIL. | `ET/extension/llm/runner/_llm_runner.pyi` L346-415; `ET/extension/llm/runner/pybindings.cpp` L47-135, L703-740 | BSD-3 | TAKE-CODE | **Avoids wrapping a CLI.** Call it directly; no copying needed. | 0.5 day if the wheel works |
| executorch | `GenerationConfig` (Python) | **[READ]** Exposes echo, max_new_tokens, warming, seq_len, temperature, num_bos, num_eos. Not exposed: `ignore_eos`, grammar. | `_llm_runner.pyi` L11-32 | BSD-3 | TAKE-CODE | Set echo off, temperature low or 0, bounded max_new_tokens. | Minutes |
| executorch | `Stats` and JSON report | **[READ]** Records model load start/end, inference start/end, encode end, prompt-eval end, first token, sampling and execution totals, prompt and generated token counts. JSON adds prefill and decode tok/s. Printed on a `PyTorchObserver` line, except in warmup. Same fields reach Python through `stats_callback`. | `ET/extension/llm/runner/stats.h` L26-53, L113-173; `_llm_runner.pyi` L67-109; `ET/extension/llm/runner/text_llm_runner.cpp` L215, L271-279 | BSD-3 | TAKE-CODE | **Ready source of tok/s and time to first token.** TTFT = `first_token_ms` minus `inference_start_ms`. Load time = load end minus start. | 1-2 hours |
| executorch | `get_rss_bytes` | **[READ]** Returns `ru_maxrss`, so it is **peak** RSS despite the name. The runner logs it after load, after prefill and after generation. Not in `Stats` and not in the Python stubs. | `ET/extension/llm/runner/util.h` L219-232; `text_llm_runner.cpp` L90-92, L229-231, L259-261 | BSD-3 | TAKE-CODE | Same measure is available from Python's `resource` module, or `wait4` for a subprocess. | 1 hour |
| executorch | Python build wiring | **[READ]** `_llm_runner` builds with `EXECUTORCH_BUILD_PYBIND=ON`. The Linux pybind preset turns on the LLM runner, and `setup.py` packages it. | `ET/extension/llm/runner/CMakeLists.txt` L113-129; `ET/tools/cmake/preset/pybind.cmake` L84-91; `ET/setup.py` L2593-2595; `ET/extension/llm/runner/README.md` L171-196 | BSD-3 | TAKE-CODE | Evidence the wheel includes it. Wheel contents themselves not inspected. | n/a |
| PyPI | `executorch` 1.5.1 wheels | **[READ, metadata only]** `manylinux_2_28_aarch64` wheels for cp310 to cp314, about 18 MB. Licence metadata BSD-3-Clause. Would remove cross-compiling if `_llm_runner` is inside. | https://pypi.org/project/executorch/1.5.1/ (not SHA-pinned) | BSD-3 | TAKE-CODE | **First smoke test on the Pi.** Pin the version. | 1-2 hours |
| executorch | `examples/raspberry_pi/setup.sh` | **[READ in full]** Cross-compile script for `pi4`/`pi5`: toolchain 14.3.rel1, generated CMake toolchain, `--preset llm`, `llama_main` build, output checks. | `ET/examples/raspberry_pi/setup.sh`: `create_toolchain_cmake` L375-430; `build_executorch_core` L433-477; `build_llama_runner` L480-497; `verify_build` L500-540 | BSD-3 | TAKE-CODE | CLI route, and needed for the KleidiAI A/B test. See risks in section 4. | 0.5-1 day |
| executorch | Pi 5 compiler flags | **[READ]** `armv8.2-a+dotprod+fp16`, tuned for Cortex-A76. | `setup.sh` L387 | BSD-3 | TAKE-CODE | Quote to judges. | Minutes |
| executorch | Deployment bundle | **[READ]** `llama_main` plus `libllama_runner.so`, with model and tokenizer, using `LD_LIBRARY_PATH`. | `setup.sh` L543-587 | BSD-3 | TAKE-CODE | Defines the CLI runtime bundle. | 1 hour |
| executorch | `docs/source/raspberry_pi_llama_tutorial.md` | **[READ, parts]** Official Pi walkthrough for release/1.5, including SpinQuant export (L131-135), dry run (L181-188) and GLIBC troubleshooting (L192 on). | `ET/docs/source/raspberry_pi_llama_tutorial.md` | BSD-3 (root) | TAKE-CODE | Our build runbook; link it. | 1 hour |
| executorch | `examples/models/llama/main.cpp` | **[READ, parts]** The `llama_main` CLI. Flags: temperature (0 = greedy), deprecated seq_len, max_new_tokens, cpu_threads (-1 = heuristic), num_bos, num_eos, warmup, ignore_eos. Prompt is passed as given; no template logic. | `ET/examples/models/llama/main.cpp` L37, L43-71, L73-76, L150-162 | Header BSD; folder `LICENSE` is Llama 2 | TAKE-IDEA | Build unmodified. Fallback runner, and our thread sweep target. | Covered by build |
| executorch | `examples/models/llama/runner/runner.cpp` | **[READ, parts]** A thin layer: Llama tokenizer loader plus a call into `create_text_llm_runner`. So the CLI and Python share the same C++ runner. | `ET/examples/models/llama/runner/runner.cpp` L24-29, L82 | As above | TAKE-IDEA | Justifies comparing CLI and Python numbers. | None |
| executorch | `config/llama_xnnpack_spinquant.yaml` | **[READ in full]** SpinQuant export: 8da4w with 8-bit output layer, group size 32, 8-bit embeddings, KV cache, 2048 context, XNNPACK enabled. Sets BOS and EOS ids. | `ET/examples/models/llama/config/llama_xnnpack_spinquant.yaml` | Folder `LICENSE` is Llama 2 | TAKE-IDEA | Use unmodified if we export ourselves. Context 2048 comfortably fits a 300-word passage. | 0.5 day if exporting |
| HF, linked from llama README | Prebuilt Llama 3.2 1B: [SpinQuant](https://huggingface.co/executorch-community/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8-ET), [QLORA](https://huggingface.co/executorch-community/Llama-3.2-1B-Instruct-QLORA_INT4_EO8-ET), [BF16](https://huggingface.co/executorch-community/Llama-3.2-1B-ET) | **[READ, API metadata only]** All ungated; each has `.pte`, `tokenizer.model`, `params.json` and export notebook. **Last modified April 2025**, so loading on 1.5 is unproven. Plain `llama3_2-1B` is unquantised-style BF16 and won't exercise the INT4 KleidiAI path. | Links shown; HF repos, not SHA-pinned | `llama3.2` (metadata) | TAKE-IDEA | Try first to skip export; re-export if it fails to load. Do not commit. | 1 hour, or 0.5 day if re-exporting |
| executorch | Tokenizer handling | **[READ]** The Python binding calls the generic loader with no special token list; the loader falls back to the default Tiktoken list, which includes the Llama 3 headers and `eot_id`. Encoding recognises special tokens written in the prompt text. | `pybindings.cpp` L55-56; `ET/extension/llm/runner/llm_runner_helper.cpp` L34-89; [tiktoken.h L76-99](https://github.com/meta-pytorch/tokenizers/blob/61a10ac61245a68374ace4900e49cd2aba65fb39/include/pytorch/tokenizers/tiktoken.h#L76-L99); [bpe_tokenizer_base.cpp L264-271](https://github.com/meta-pytorch/tokenizers/blob/61a10ac61245a68374ace4900e49cd2aba65fb39/src/bpe_tokenizer_base.cpp#L264-L271) | BSD-3 | TAKE-CODE | We can write Llama prompt headers as literal text. Confirm once with a token count. | Minutes |
| executorch | `examples/llm_server/python/chat_template.py` | **[READ, parts]** Its docstring states the runner tokenizes a plain prompt and chat formatting belongs to the caller. Uses the Hugging Face template via `transformers`, with an opt-in generic ChatML fallback. | `ET/examples/llm_server/python/chat_template.py` L7-15, L91-122 | BSD-3 (header) | TAKE-IDEA | Too heavy for us. Confirms we write our own small prompt builder. | n/a |
| executorch | Qwen 2.5 fallback | **[READ, README lines; config LISTED]** Shares the Llama example code. Has a 1.5B config, a q8da4w export YAML, and uses `tokenizer.json`, which the loader handles via `HFTokenizer`. No prebuilt `.pte` checked. | `ET/examples/models/qwen2_5/README.md` L6, L33-35; `.../config/1_5b_config.json`; `.../config/qwen2_5_xnnpack_q8da4w.yaml` | BSD-3 (root; no folder licence listed). Model licence not read. | TAKE-CODE | Fallback model; needs its own prompt format and an export. | 0.5-1 day |
| executorch | `GenerationConfig.grammar`, `grammar_type` | **[READ]** Declared for JSON schema, regex, Lark and GBNF in C++. **Zero references** in `text_llm_runner.cpp`, `text_token_generator.h`, `pybindings.cpp`, `multimodal_runner.cpp` and `main.cpp`. Not in Python stubs. The llm_server README lists `response_format` as rejected. Sampler code shows temperature-style sampling only. | `ET/extension/llm/runner/irunner.h` L36-42; `ET/examples/llm_server/README.md` L39-40; `ET/extension/llm/sampler/sampler.h` L64-74 | BSD-3 | SKIP | **Do not plan on it.** Whole-repo content search was not possible, so another consumer can't be fully excluded. | n/a |
| executorch | KleidiAI build wiring | **[READ]** `EXECUTORCH_XNNPACK_ENABLE_KLEIDI` defaults ON and passes through to XNNPACK. `llama_main` links `kleidiai` when the target exists. The runtime selects QP8 for INT4/INT8 filters. | `ET/tools/cmake/preset/default.cmake` L304-306; `ET/backends/xnnpack/cmake/Dependencies.cmake` L51-61; `ET/backends/xnnpack/CMakeLists.txt` L34-35; `ET/examples/models/llama/CMakeLists.txt` L150-151; `ET/backends/xnnpack/runtime/XNNCompiler.cpp` L705-752, L767-777 | BSD-3 | TAKE-CODE | Basis of the proof in section 3. | 0.5 day |
| XNNPACK | KleidiAI kernel choice | **[READ]** On ARM64 with KleidiAI, INT4 QP8 config picks SME where present, then I8MM, then **DOTPROD**. [MEMORY] Cortex-A76 has dotprod but no i8mm, so the Pi 5 should get the dotprod kernels. | [gemm-config.c L2889-2964, L3036-3078](https://github.com/google/XNNPACK/blob/92a7ad501b9516f9fecae119e0146dd1f58e54c1/src/configs/gemm-config.c#L3036-L3078) | Not read | TAKE-IDEA | Cite to judges; matches the [PyTorch blog](https://pytorch.org/blog/bringing-generative-ai-to-the-masses-with-executorch-and-kleidiai/) on SDOT for Int4 and on Pi 5. | Minutes |
| executorch | `eval_llama.py`, `evaluate/` | **[LISTED]** Accuracy evaluation. | `ET/examples/models/llama/eval_llama.py` | Folder `LICENSE` | SKIP | Our checks are deterministic. | n/a |
| executorch | Low-bit kernels via torchao | **[READ, README lines]** Described as experimental; optional `TORCHAO_BUILD_KLEIDIAI`. | `ET/examples/models/llama/README.md` L340-349 | Folder `LICENSE` | SKIP | Avoid before the event. | n/a |
| executorch | Apple, Android, QNN, multimodal, llm_server | Out of scope for a Pi terminal PoC. | n/a | n/a | SKIP | None. | n/a |

### ArmDeveloperEcosystem/courses-code-executorch

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| courses-code-executorch | `course_support/benchmarking.py`: `save_plots`, `write_results`, `print_stats` | **[READ]** Histogram and run-order plots (matplotlib); JSON metadata plus per-run CSV, including platform details; small stats table. | `AC/course_support/benchmarking.py` L44-82, L85-115, L118-127 | Clear BSD | TAKE-CODE | Reuse for reporting. Retain notice. | 1-2 hours |
| courses-code-executorch | `benchmarking.py`: `benchmark` | **[READ]** Runs warmups, then times a callable and returns mean, median, std, min, max and percentiles. **Whole-call latency only: no tok/s, no TTFT, no memory, no threads.** | `AC/course_support/benchmarking.py` L15-41 | Clear BSD | TAKE-CODE | Wrap one generation call for the end-to-end time; add token metrics from `Stats`. | 1 hour |
| courses-code-executorch | `module-1-.../scripts/pi/benchmark_model.py` | **[READ, parts]** PyTorch vs ExecuTorch latency of a **single forward pass** on Pi. Flags cover runtime, backend, spec, pte, runs, warmups, out. Not a token-generation benchmark. | `AC/module-1-transformer-inference-with-xnnpack/scripts/pi/benchmark_model.py` L35-42, L66-92 | Clear BSD | TAKE-IDEA (usable as pattern) | Structure to imitate. Cite to show we follow Arm's method. | 1 hour |
| courses-code-executorch | `course_support/serve_results.py` | **[READ, first lines]** Small local benchmark dashboard, default 127.0.0.1:8080. | `AC/course_support/serve_results.py` L1-15 | Clear BSD | TAKE-CODE (optional) | Stretch demo; terminal output is enough. | Low priority |
| courses-code-executorch | `module-1-.../requirements.txt` | **[READ]** Known-good set with **executorch 1.3.1**, torch 2.12.1, Python 3.12.14. | `AC/module-1-transformer-inference-with-xnnpack/requirements.txt` | Clear BSD | TAKE-IDEA | **Differs from our release/1.5.** Don't mix environments. | n/a |
| courses-code-executorch | Modules 2-4, GPT-2/DistilBERT scripts, `open_images_calibration.py`, `.agents/` | **[LISTED]** Other models and platforms. | n/a | n/a | SKIP | None. | n/a |

The course README warns module scripts import from `course_support`; copying `benchmarking.py` alone is fine since it has no such imports [READ: stdlib only at top level, numpy and matplotlib imported lazily].

### Arm learning material

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| arm-learning-paths | [rpi-llama3](https://learn.arm.com/learning-paths/embedded-and-microcontrollers/rpi-llama3/) (updated 14 Aug 2026) | **[READ, intro only]** Docker running Raspberry Pi OS on an Arm Linux host, compile model, transfer, run `llama_main`, vary prompt and thread count. Web page, not SHA-pinned. | Page URL | Not read | TAKE-IDEA | Fallback build route. | 1 hour |
| Arm course site | [executorch-on-arm](https://learn.arm.com/courses/executorch-on-arm/) | **[READ, overview only]** Pi 5 on 64-bit Trixie; macOS (Apple silicon) or Ubuntu dev machine. Text CC BY-SA 4.0. | Page URL | CC BY-SA 4.0 / Clear BSD | TAKE-IDEA | Reference; Module 1 covers the Mac host case. | 1 hour |

## 3. Answers

| Question | Answer | Confidence |
|---|---|---|
| Which files give a working runner? | Either the `executorch` Python package's `TextLLMRunner`, or `setup.sh` producing `llama_main` and `libllama_runner.so`. Both reach the same C++ runner. | High on source; not run |
| Avoid wrapping a CLI? | **Yes.** `TextLLMRunner` supports text-only models. Costs: importing the package loads torch ([`__init__.py` L14](https://github.com/pytorch/executorch/blob/985c1ceccc8bb8b6a32294f71aeb5d2f299562f7/extension/llm/runner/__init__.py#L14)), which adds memory and start-up time to anything measured in-process; `get_vocab_size` returns -1 (`pybindings.cpp` L132-135); no thread argument. | High on API; wheel unproven |
| Thread control from Python? | Not on the runner. `extension/pybindings` exposes `_unsafe_reset_threadpool` (`pybindings.cpp` in that folder, L1871-1876). Whether it affects the LLM runner is inferred from the shared runtime link (`runner/CMakeLists.txt` L129). Test it. | Medium |
| Ready harness for tok/s, TTFT, memory? | **No single harness.** `Stats` gives tok/s and TTFT. Peak RSS comes from `ru_maxrss`. `benchmarking.py` gives run statistics, CSV/JSON and plots. Our glue is small. | High |
| Chat template? | **None in `llama_main` or the runner.** Write a small Llama 3.2 prompt builder in Python using the literal header tokens; Qwen would need ChatML. Exact Llama format should be taken from Meta's documentation (not fetched here). | High |
| Structured output? | **Not usable.** Fields are declared but no consumer found in the runner. Use a prompted format, deterministic parsing and bounded retries. | Medium-high |
| Thread sweep tooling? | None found in `benchmark_model.py`, `common.py` or the setup script. A loop over `--cpu_threads` 1-4 is 1-2 hours. | Medium-high |

### KleidiAI proof for judges (designed from source, not tried)

No log line or official verification method was found. The [PyTorch blog](https://pytorch.org/blog/bringing-generative-ai-to-the-masses-with-executorch-and-kleidiai/) says it is on by default since 0.7 but gives no check. Strongest first:

1. **A/B timing:** build twice, the second with `EXECUTORCH_XNNPACK_ENABLE_KLEIDI=OFF`; same `.pte`, same prompt, compare prefill and decode tok/s from `Stats`. This is the result to show.
2. **Profiler:** on a build without stripping, `perf` should show KleidiAI `kai_` kernels in the hot path. Plain `nm` on `llama_main` **won't work** in Release: it is linked with `-s` (`examples/models/llama/CMakeLists.txt` L233-239).
3. **Debug log:** a Debug-level log build prints the QP8 flag message per convert node (`XNNCompiler.cpp` L773-776). This shows the QP8 path was requested, not that a kernel ran.
4. **Config and hardware:** the CMake cache shows the option ON, and `/proc/cpuinfo` shows `asimddp` (dotprod) on the Pi. Necessary but weak on its own.

The A/B test needs a source build; the wheel can't be switched. Use a quantised INT4 `.pte`, because the BF16 model won't exercise this path.

One [dev.to report](https://dev.to/bamb00boy/first-gemma-4-executorch-deployment-on-raspberry-pi-5-and-why-its-77x-slower-than-llamacpp-gmb) surfaced via search claims ExecuTorch 1.2.0 XNNPACK rejected fused INT4 subgraphs on aarch64 (Gemma 4). The page returned 404 when fetched, so this is unverified and only known from a search summary. Check for this early: a silent fallback would ruin the speed story.

## 4. Recommendation and risks

**Recommended route:** Python `TextLLMRunner` with the pinned `executorch` wheel for the pipeline, plus a source-built `llama_main` for thread sweep and KleidiAI A/B.

**Decision for the team:** the brief names `llama_main`. Python gives token streaming and in-process stats, but torch inflates its memory figure. Reporting memory from `llama_main` would be cleaner and more flattering. Both are measurable.

### Risks

1. **`setup.sh` exits on macOS** (L149-154). This machine is a Mac, so use Linux, Docker or a native Pi build.
2. **Toolchain MD5 check:** the same hash is listed for x86_64 and aarch64 (L324, L327); a mismatch exits. One host architecture probably fails. Not tested.
3. **GLIBC mismatch** between cross-compiled binaries and the Pi is the tutorial's first documented issue (L192 on). Building on the Pi, or using the manylinux_2_28 wheel, should avoid it.
4. **April 2025 `.pte` files** may not load on 1.5. Keep time for a re-export, which needs the Llama checkpoint and a host with enough RAM.
5. **Stale environment:** `setup_environment` returns early if `executorch` already imports (L228-230), skipping submodule init.
6. **Course pins 1.3.1**, we pin 1.5; results and scripts may not transfer directly.

### Minimum set

- **On the Pi (Python route):** the `executorch` wheel and torch, one `.pte`, `tokenizer.model`.
- **On the Pi (CLI route):** `llama_main`, `libllama_runner.so`, the same model files.
- **Upstream, built not vendored:** full `pytorch/executorch` at the pinned SHA with submodules.
- **Copied with notice:** at most `course_support/benchmarking.py` (Clear BSD).
- **Ours to write:** prompt builder, parser and validators, metrics glue (`Stats` plus peak RSS), thread sweep loop.
- **Notice duties:** ExecuTorch BSD notice if we distribute binaries; Clear BSD notice if we copy Arm code; Llama terms for weights.

## 5. Not yet read

- **Wheel contents:** whether the 1.5.1 aarch64 wheel really contains `_llm_runner` and whether KleidiAI is on in it. Needs inspecting the wheel on the Pi.
- **Model compatibility:** whether the April 2025 `.pte` files load on 1.5. Needs a run.
- **Licence texts:** remainder of the Llama 2 licence in the folder, Llama 3.2 licence, XNNPACK, arm-learning-paths.
- **Partly read:** `main.cpp`, `llama/README.md`, `extension/llm/runner/README.md`, `pybind.cmake` conditions, `chat_template.py`, `serve_results.py`, `common.py` (search only).
- **Not opened:** Learning Path subpages, course Module 1 lesson pages, `text_token_generator.h`, `export_llm`, Qwen YAML contents, Meta's Llama 3.2 prompt format page.
- **Whole-repo content search** for grammar consumers: not possible with the allowed routes.
