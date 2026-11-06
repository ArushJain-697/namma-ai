"""ExecuTorch backend: the Python TextLLMRunner from the `executorch` wheel.

Written against the real 1.5.1 API (read from the wheel's type stubs, build map findings log):
  TextLLMRunner(model_path, tokenizer_path, data_path=None)
  runner.generate(prompt, GenerationConfig, token_callback, stats_callback)
  runner.reset()   clears the KV cache
  GenerationConfig(echo, max_new_tokens, seq_len, temperature, num_bos, num_eos, warming)
There is NO seed argument, so retries must vary temperature (generate.py does).

STATUS: tested here only with a fake runner. It has NOT run a real model. The first real run is
scripts/pi_smoke.py on the Pi (build map T17).

Open questions that only the Pi can answer (pi_smoke.py measures them):
  * BOS: does the runner add a BOS itself, or must we (num_bos=1 or a literal in the prompt)?
  * Do the Llama 3 header tokens parse as special tokens from the prompt text?
  * Does the April 2025 SpinQuant .pte load on ExecuTorch 1.5.1?
"""
from __future__ import annotations

import hashlib
import os
import re
import time
from typing import Any, Callable

from .base import Backend, GenResult

_STOP = re.compile(r"<\|(eot_id|end_of_text|eom_id|start_header_id|end_header_id)\|>")


def _default_factory(model_path: str, tokenizer_path: str, data_path: str | None):
    try:
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
                 num_bos: int = 0, hash_model: bool = False, label: str | None = None,
                 runner_factory: Callable[[str, str, str | None], Any] | None = None,
                 config_factory: Callable[..., Any] | None = None):
        for what, path in (("model", model_path), ("tokenizer", tokenizer_path)):
            if not os.path.isfile(path):
                raise FileNotFoundError(f"{what} file not found: {path}")
        self.model_path, self.tokenizer_path, self.data_path = model_path, tokenizer_path, data_path
        self.bos_in_prompt, self.num_bos, self.label = bos_in_prompt, num_bos, label
        self._config_factory = config_factory or _generation_config
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
        return {"name": self.label or f"executorch:{os.path.basename(self.model_path)}", "model_path": self.model_path,
                "tokenizer_path": self.tokenizer_path, "model_bytes": os.path.getsize(self.model_path),
                "sha256": self.sha256, "load_s": self.load_s, "bos_in_prompt": self.bos_in_prompt, "num_bos": self.num_bos}

    def generate(self, prompt, max_new_tokens=64, temperature=0.0, seed=None, task=None, payload=None) -> GenResult:
        # `seed`, `task` and `payload` are ignored on purpose: the runner has no seed, and the model must not be
        # told anything beyond the prompt.
        self._runner.reset()  # independent prompts: no KV-cache carry-over between questions
        cfg = self._config_factory(echo=False, max_new_tokens=max_new_tokens, temperature=temperature,
                                   num_bos=self.num_bos, num_eos=0)
        pieces: list[str] = []
        box: dict[str, Any] = {}
        t0 = time.perf_counter()
        first = [None]

        def on_token(tok: str) -> None:
            if first[0] is None:
                first[0] = time.perf_counter()
            pieces.append(tok)

        def on_stats(st) -> None:  # copy values now: the runner may reuse the object
            box.update({k: getattr(st, k, None) for k in (
                "inference_start_ms", "prompt_eval_end_ms", "first_token_ms", "inference_end_ms",
                "num_prompt_tokens", "num_generated_tokens")})

        self._runner.generate(prompt, cfg, on_token, on_stats)
        wall = time.perf_counter() - t0
        text = _STOP.sub("", "".join(pieces)).strip()

        n_prompt = int(box.get("num_prompt_tokens") or 0)
        n_new = int(box.get("num_generated_tokens") or len(pieces))
        start, pe, ft, end = (box.get(k) for k in ("inference_start_ms", "prompt_eval_end_ms", "first_token_ms", "inference_end_ms"))
        ttft_ms = (ft - start) if (ft is not None and start is not None and ft >= start) else (
            (first[0] - t0) * 1000 if first[0] else None)
        decode_s = ((end - ft) / 1000) if (end is not None and ft is not None and end > ft) else None
        prefill_s = ((pe - start) / 1000) if (pe is not None and start is not None and pe > start) else None
        return GenResult(
            text=text, prompt_tokens=n_prompt, new_tokens=n_new, ttft_ms=ttft_ms,
            tokens_per_s=(round((n_new - 1) / decode_s, 2) if decode_s and n_new > 1 else None), wall_s=wall,
            extra={"prefill_tokens_per_s": round(n_prompt / prefill_s, 2) if prefill_s and n_prompt else None,
                   "raw_stats": box})
