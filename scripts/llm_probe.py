#!/usr/bin/env python3
"""Quick check that a converted model runs on this board, and how fast.

  python scripts/llm_probe.py --model model.pte --tokenizer tokenizer.json [--chat qwen3|chatml|llama3]

Loads the .pte with ExecuTorch's TextLLMRunner, asks for a summary and 3 quiz questions on a sample
passage, and prints load time, prompt speed, generation speed, peak memory and the model's answer.
"""
import argparse
import os
import resource
import sys
import time

PASSAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "passages", "rust_ordinary.txt")

SYSTEM = "You are a helpful teacher for Class 7 students. Use simple words."
TASK = ("Read the passage. Write a 2-sentence summary, then 3 multiple-choice questions with options A-D "
        "and the correct answer.\n\nPassage:\n{passage}")


def chat(kind: str, system: str, user: str) -> str:
    if kind == "llama3":
        return (f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
                f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n")
    prompt = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
    if kind == "qwen3":  # skip Qwen3's "thinking" block: we want the answer, not a long hidden monologue
        prompt += "<think>\n\n</think>\n\n"
    return prompt


def cpu_has(flag: str) -> bool:
    try:
        with open("/proc/cpuinfo") as f:
            return any(flag in line.split() for line in f if line.startswith("Features"))
    except OSError:
        return False


def load_op_libraries() -> list[str]:
    """Register the extra kernels a converted LLM may need, inside this process.

    * quantized kernels (e.g. the 8-bit word lookup): safe on every ARM64 chip;
    * the custom attention / KV-cache kernels: built for newer chips (ARMv8.2 dot-product, e.g. the Pi 5).
      Loading them on an older chip (Cortex-A53, e.g. the Arduino UNO Q) kills the process with
      "Illegal instruction", so they are loaded only when the CPU reports dot-product support.
    Models for older chips must be converted WITHOUT --use_custom_sdpa / --use_custom_kv_cache.
    """
    import ctypes
    import executorch
    import torch  # noqa: F401  (the libraries link against libtorch)
    base = list(executorch.__path__)[0]
    libs = ["kernels/quantized/libquantized_ops_aot_lib.so"]
    if cpu_has("asimddp"):
        libs.append("extension/llm/custom_ops/libcustom_ops_aot_lib.so")
    loaded = []
    for rel in libs:
        path = os.path.join(base, rel)
        if os.path.exists(path):
            ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
            loaded.append(os.path.basename(rel))
    return loaded


def capture_stdout(fn) -> str:
    """Run fn and return what native code wrote to file descriptor 1, decoded leniently."""
    import tempfile
    sys.stdout.flush()
    fd = 1  # native code writes to fd 1 even if Python's sys.stdout was replaced
    saved = os.dup(fd)
    with tempfile.TemporaryFile() as tmp:
        os.dup2(tmp.fileno(), fd)
        try:
            fn()
        finally:
            sys.stdout.flush()
            os.dup2(saved, fd)
            os.close(saved)
        tmp.seek(0)
        return tmp.read().decode("utf-8", errors="replace")


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux reports KB


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--tokenizer", required=True)
    p.add_argument("--chat", default="qwen3", choices=["qwen3", "chatml", "llama3"])
    p.add_argument("--max-new", type=int, default=300)
    p.add_argument("--seq-len", type=int, default=-1, help="-1 = the model's own maximum")
    args = p.parse_args()

    rss0 = peak_rss_mb()
    t0 = time.perf_counter()
    libs = load_op_libraries()
    from executorch.extension.llm.runner import GenerationConfig, TextLLMRunner
    t_import = time.perf_counter() - t0
    print(f"extra kernels: {', '.join(libs) or 'none'}  (dot-product CPU: {cpu_has('asimddp')})")

    t0 = time.perf_counter()
    runner = TextLLMRunner(args.model, args.tokenizer)  # loads the model (the runner has no separate load())
    t_load = time.perf_counter() - t0
    rss_loaded = peak_rss_mb()

    passage = open(PASSAGE, encoding="utf-8").read().strip()
    prompt = chat(args.chat, SYSTEM, TASK.format(passage=passage))
    stats = {}

    def on_stats(st):
        stats.update({k: getattr(st, k, None) for k in (
            "inference_start_ms", "prompt_eval_end_ms", "first_token_ms", "inference_end_ms",
            "num_prompt_tokens", "num_generated_tokens")})

    cfg = GenerationConfig(echo=False, max_new_tokens=args.max_new, seq_len=args.seq_len, temperature=0.0)
    print("---- model output ----", flush=True)
    t0 = time.perf_counter()
    # No token callback: the runner hands Python one token at a time, and a token can be half of a multi-byte
    # character, which crashes the Python bridge (UnicodeDecodeError). The runner also writes the text to
    # stdout itself, so we let it, and decode the whole output at the end.
    text = capture_stdout(lambda: runner.generate(prompt, cfg, None, on_stats))
    wall = time.perf_counter() - t0
    print(text)
    print("---- end ----\n")

    n_in, n_out = stats.get("num_prompt_tokens") or 0, stats.get("num_generated_tokens") or 0
    s, pe, ft, e = (stats.get(k) for k in ("inference_start_ms", "prompt_eval_end_ms", "first_token_ms", "inference_end_ms"))
    prefill_s = (pe - s) / 1000 if pe and s else None
    decode_s = (e - ft) / 1000 if e and ft else None
    size_mb = os.path.getsize(args.model) / 1e6
    print(f"model file      {os.path.basename(args.model)}  {size_mb:.0f} MB")
    print(f"import / load   {t_import:.1f} s / {t_load:.1f} s")
    print(f"prompt          {n_in} tokens" + (f" in {prefill_s:.1f} s ({n_in / prefill_s:.1f} tok/s)" if prefill_s else ""))
    print(f"generated       {n_out} tokens" + (f" in {decode_s:.1f} s ({(n_out - 1) / decode_s:.1f} tok/s)" if decode_s and n_out > 1 else ""))
    print(f"total wall      {wall:.1f} s")
    print(f"peak memory     {peak_rss_mb():.0f} MB (after load {rss_loaded:.0f} MB, before {rss0:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
