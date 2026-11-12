"""ExecuTorch backend: the Python TextLLMRunner from the `executorch` wheel.

Written against the real 1.5.1 API:
  TextLLMRunner(model_path, tokenizer_path, data_path=None)   loads the model (there is no separate load())
  runner.generate(prompt, GenerationConfig, token_callback, stats_callback)
  runner.reset()   clears the KV cache
  GenerationConfig(echo, max_new_tokens, seq_len, temperature, num_bos, num_eos, warming)
There is NO seed argument, so retries must vary temperature (generate.py does).

Verified on real ARM hardware (Arduino UNO Q, Cortex-A53, 13 Nov 2026) with Qwen3-0.6B and Qwen2.5-0.5B
converted by optimum-executorch. Three things learned there are handled here:
  1. Extra kernels. A model converted with 8-bit embeddings needs the quantized kernel library, and one converted
     with --use_custom_sdpa / --use_custom_kv_cache needs the custom-ops library. Both must be loaded into the
     process BEFORE the model. The custom-ops library is built for newer ARM chips (dot-product instructions,
     e.g. the Pi 5): on an older chip it kills the process with "Illegal instruction", so it is only loaded when
     the CPU reports that support. Models for older chips must be converted without those two flags.
  2. Text capture. The token callback receives one token at a time, and a token can be half of a multi-byte
     character: the Python bridge then raises UnicodeDecodeError and the whole generation is lost. The runner also
     prints the text to stdout itself, so we capture file descriptor 1 and decode it once, leniently.
  3. Chat format. Qwen models use <|im_start|> turns, not Llama headers. It is detected from the tokenizer.
"""
from __future__ import annotations

import hashlib
import os
import platform
import re
import sys
import tempfile
import time
from typing import Any, Callable

from .base import CHAT_FORMATS, Backend, GenResult

_STOP = re.compile(r"<\|(eot_id|end_of_text|eom_id|start_header_id|end_header_id|im_end|im_start|endoftext)\|>")
_THINK = re.compile(r"<think>.*?(</think>|$)", re.S)
_OBSERVER = re.compile(r"^PyTorchObserver .*$", re.M)  # the runner prints its stats as a line of JSON on stdout


def cpu_has_dotprod() -> bool:
    """Can this CPU run the custom-ops kernels? (ARMv8.2 dot-product: Pi 5 yes, UNO Q no, Apple silicon yes.)"""
    if sys.platform == "darwin":
        return platform.machine() == "arm64"
    try:
        with open("/proc/cpuinfo") as f:
            return any("asimddp" in line.split() for line in f if line.startswith("Features"))
    except OSError:
        return False


def load_kernel_libraries() -> list[str]:
    """Load the quantized and (when the CPU supports it) custom-ops kernel libraries into this process."""
    import ctypes
    import executorch
    import torch  # noqa: F401  (the libraries link against libtorch, which must be loaded first)
    base = list(executorch.__path__)[0]
    ext = ".dylib" if sys.platform == "darwin" else ".so"
    wanted = ["kernels/quantized/libquantized_ops_aot_lib"]
    if cpu_has_dotprod():
        wanted.append("extension/llm/custom_ops/libcustom_ops_aot_lib")
    loaded = []
    for rel in wanted:
        path = os.path.join(base, rel + ext)
        if os.path.exists(path):
            ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
            loaded.append(os.path.basename(path))
    return loaded


def detect_chat_format(tokenizer_path: str) -> str:
    """qwen3 if the tokenizer knows <think>, chatml if it knows <|im_start|>, otherwise llama3."""
    try:
        with open(tokenizer_path, "rb") as f:
            head = f.read(20_000_000)
    except OSError:
        return "llama3"
    if b"<|im_start|>" in head:
        return "qwen3" if b"<think>" in head else "chatml"
    return "llama3"


def capture_stdout(fn: Callable[[], None]) -> str:
    """Run fn and return whatever native code wrote to file descriptor 1, decoded leniently.

    Always fd 1, not sys.stdout.fileno(): native code writes to fd 1 even when Python's sys.stdout was replaced."""
    sys.stdout.flush()
    fd = 1
    saved = os.dup(fd)
    with tempfile.TemporaryFile() as tmp:
        os.dup2(tmp.fileno(), fd)
        try:
            fn()
        finally:
            try:
                sys.stdout.flush()
            finally:
                os.dup2(saved, fd)
                os.close(saved)
        tmp.seek(0)
        return tmp.read().decode("utf-8", errors="replace")


def clean_output(text: str) -> str:
    """Drop stop tokens, any thinking block and the runner's stats line."""
    text = _OBSERVER.sub("", text)
    text = _THINK.sub("", text)
    return _STOP.sub("", text).strip()


def _default_factory(model_path: str, tokenizer_path: str, data_path: str | None):
    try:
        load_kernel_libraries()
        from executorch.extension.llm.runner import TextLLMRunner
    except Exception as e:  # missing torch, missing wheel, or built without the LLM runner
        raise ImportError(
            f"cannot import the ExecuTorch LLM runner ({type(e).__name__}: {e}). "
            "It needs `pip install executorch==1.5.1 torch numpy tqdm typing_extensions`; see scripts/pi_setup.sh") from e
    try:
        return TextLLMRunner(model_path, tokenizer_path, data_path)
    except RuntimeError as e:
        raise RuntimeError(f"ExecuTorch could not load the model or tokenizer: {e}") from e


def _generation_config(**kw):
    from executorch.extension.llm.runner import GenerationConfig
    return GenerationConfig(**kw)


class ExecuTorchBackend(Backend):
    name = "executorch"

    def __init__(self, model_path: str, tokenizer_path: str, data_path: str | None = None, bos_in_prompt: bool = False,
                 num_bos: int = 0, hash_model: bool = False, label: str | None = None, chat_format: str = "auto",
                 runner_factory: Callable[[str, str, str | None], Any] | None = None,
                 config_factory: Callable[..., Any] | None = None, capture: Callable[[Callable[[], None]], str] | None = None):
        for what, path in (("model", model_path), ("tokenizer", tokenizer_path)):
            if not os.path.isfile(path):
                raise FileNotFoundError(f"{what} file not found: {path}")
        if chat_format != "auto" and chat_format not in CHAT_FORMATS:
            raise ValueError(f"unknown chat format {chat_format!r}; choose auto or one of {', '.join(CHAT_FORMATS)}")
        self.model_path, self.tokenizer_path, self.data_path = model_path, tokenizer_path, data_path
        self.bos_in_prompt, self.num_bos, self.label = bos_in_prompt, num_bos, label
        self.chat_format = detect_chat_format(tokenizer_path) if chat_format == "auto" else chat_format
        self._config_factory = config_factory or _generation_config
        self._capture = capture or capture_stdout
        t0 = time.perf_counter()
        self._runner = (runner_factory or _default_factory)(model_path, tokenizer_path, data_path)
        self.load_s = round(time.perf_counter() - t0, 3)
        self.sha256 = self.hash_file() if hash_model else None

    def hash_file(self) -> str:
        h = hashlib.sha256()
        with open(self.model_path, "rb") as f:
            while block := f.read(1 << 20):
                h.update(block)
        return h.hexdigest()

    def info(self) -> dict:
        return {"name": self.label or f"executorch:{os.path.basename(os.path.dirname(self.model_path)) or 'model'}",
                "model_path": self.model_path, "tokenizer_path": self.tokenizer_path,
                "model_bytes": os.path.getsize(self.model_path), "sha256": self.sha256, "load_s": self.load_s,
                "chat_format": self.chat_format, "bos_in_prompt": self.bos_in_prompt, "num_bos": self.num_bos}

    def generate(self, prompt, max_new_tokens=64, temperature=0.0, seed=None, task=None, payload=None) -> GenResult:
        # `seed`, `task` and `payload` are ignored on purpose: the runner has no seed, and the model must not be
        # told anything beyond the prompt.
        self._runner.reset()  # independent prompts: no KV-cache carry-over between questions
        cfg = self._config_factory(echo=False, max_new_tokens=max_new_tokens, temperature=temperature,
                                   num_bos=self.num_bos, num_eos=0)
        box: dict[str, Any] = {}

        def on_stats(st) -> None:  # copy values now: the runner may reuse the object
            box.update({k: getattr(st, k, None) for k in (
                "inference_start_ms", "prompt_eval_end_ms", "first_token_ms", "inference_end_ms",
                "num_prompt_tokens", "num_generated_tokens")})

        t0 = time.perf_counter()
        raw = self._capture(lambda: self._runner.generate(prompt, cfg, None, on_stats))
        wall = time.perf_counter() - t0
        text = clean_output(raw)

        n_prompt = int(box.get("num_prompt_tokens") or 0)
        n_new = int(box.get("num_generated_tokens") or 0)
        start, pe, ft, end = (box.get(k) for k in ("inference_start_ms", "prompt_eval_end_ms", "first_token_ms", "inference_end_ms"))
        ttft_ms = (ft - start) if (ft is not None and start is not None and ft >= start) else None
        decode_s = ((end - ft) / 1000) if (end is not None and ft is not None and end > ft) else None
        prefill_s = ((pe - start) / 1000) if (pe is not None and start is not None and pe > start) else None
        return GenResult(
            text=text, prompt_tokens=n_prompt, new_tokens=n_new, ttft_ms=ttft_ms,
            tokens_per_s=(round((n_new - 1) / decode_s, 2) if decode_s and n_new > 1 else None), wall_s=wall,
            extra={"prefill_tokens_per_s": round(n_prompt / prefill_s, 2) if prefill_s and n_prompt else None,
                   "raw_stats": box})
