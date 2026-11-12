"""First real run on the Pi (build map T17): load the model, count tokens, generate once, report.

The token-count experiments settle two questions that only the real tokenizer can answer:
  1. Does the runner add a BOS token itself, or must we (num_bos=1, or a literal in the prompt)?
  2. Do the Llama 3 header tokens in the prompt text parse as SPECIAL tokens (a handful of ids)
     or get split into dozens of ordinary pieces (which would quietly wreck the chat format)?
"Hi" is a single token in the Llama 3 vocabulary, so counts of 1/2/3 are interpretable.
"""
from __future__ import annotations

import sys
import time

from .backends.base import chat_for
from .metrics import capture_env

SYSTEM = "You rewrite one sentence for a school student in simple words. Keep every number and name. Add nothing new."
USER = "Sentence: Iron rusts when it reacts with oxygen and water.\nRewrite it in simple words for a Class 6 student."


def bos_verdict(n0: int, n1: int, n_literal: int) -> list[str]:
    """Interpret prompt-token counts for 'hi' with num_bos=0 (n0) and num_bos=1 (n1), and for
    '<|begin_of_text|>hi' with num_bos=0 (n_literal)."""
    out = []
    if (n0, n1) == (1, 2):
        out.append("BOS: the runner adds NO BOS by default and num_bos is honoured. Use --num-bos 1.")
    elif (n0, n1) == (2, 2):
        out.append("BOS: the runner adds a BOS itself and ignores num_bos. Keep --num-bos 0 and no BOS in the prompt.")
    elif (n0, n1) == (2, 3):
        out.append("BOS: the runner adds a BOS itself and num_bos adds ANOTHER. Keep --num-bos 0 (double BOS otherwise).")
    elif (n0, n1) == (1, 1):
        out.append("BOS: no BOS is added and num_bos is ignored. Put <|begin_of_text|> in the prompt (--bos-in-prompt).")
    else:
        out.append(f"BOS: unexpected counts (n0={n0}, n1={n1}). Paste them back; do not guess.")
    if n_literal == n0 + 1:
        out.append("BOS: a literal <|begin_of_text|> in the prompt parses as ONE special token.")
    elif n_literal > n0 + 1:
        out.append(f"BOS: a literal <|begin_of_text|> is split into {n_literal - n0} pieces (NOT parsed as special). Do not use --bos-in-prompt.")
    return out


def header_verdict(n_header: int, auto_bos: int = 0) -> str:
    """'<|start_header_id|>user<|end_header_id|>' should be 3 tokens when parsed as special tokens."""
    n = n_header - auto_bos
    if n == 3:
        return "HEADERS: parse as special tokens (3 ids). The Llama 3 chat template is safe to use as written."
    return (f"HEADERS: PROBLEM. The header string became {n} tokens, not 3, so it is being split as ordinary text. "
            "The chat format is broken until this is fixed. Paste this back.")


def _count(backend, prompt: str, num_bos: int) -> int:
    old = backend.num_bos
    backend.num_bos = num_bos
    try:
        return backend.generate(prompt, max_new_tokens=1, temperature=0.0).prompt_tokens
    finally:
        backend.num_bos = old


def run_smoke(backend, max_new: int = 48, out=print) -> dict:
    """Run every smoke step. Returns the numbers so they can be saved or tested."""
    info = backend.info()
    out(f"model:          {info.get('model_path')}  ({(info.get('model_bytes') or 0) / 1e6:.0f} MB)")
    out(f"model load:     {info.get('load_s')} s")

    n0, n1 = _count(backend, "hi", 0), _count(backend, "hi", 1)
    nl = _count(backend, "<|begin_of_text|>hi", 0)
    nh = _count(backend, "<|start_header_id|>user<|end_header_id|>", 0)
    out(f"token counts:   'hi' num_bos=0 -> {n0}; num_bos=1 -> {n1}; literal BOS -> {nl}; header string -> {nh}")
    verdicts = bos_verdict(n0, n1, nl)
    verdicts.append(header_verdict(nh, auto_bos=1 if n0 == 2 else 0))
    for v in verdicts:
        out(v)

    prompt = chat_for(backend, SYSTEM, USER)
    runs = []
    for label in ("cold", "warm"):
        t0 = time.perf_counter()
        r = backend.generate(prompt, max_new_tokens=max_new, temperature=0.0)
        runs.append(r)
        out(f"\ngeneration ({label}): {time.perf_counter() - t0:.2f} s")
        out(f"  text:            {r.text!r}")
        out(f"  prompt tokens:   {r.prompt_tokens}   generated: {r.new_tokens}")
        out(f"  time to first token: {r.ttft_ms and round(r.ttft_ms)} ms")
        out(f"  decode:          {r.tokens_per_s} tokens/s    prefill: {r.extra.get('prefill_tokens_per_s')} tokens/s")
    same = runs[0].text == runs[1].text
    out(f"\ntemperature 0 repeats itself: {same}  ({'expected: retries must change temperature' if same else 'differs: investigate'})")

    env = capture_env()
    out(f"\npeak memory:    {env['peak_rss_mb']} MB ({env['peak_rss_what']}); includes torch, so it overstates the model alone")
    out(f"network:        {env['network']['status']}")
    if env.get("throttle") is not None:
        out(f"throttling:     {'none' if env['throttle']['clean'] else ', '.join(env['throttle']['flags'])} ({env['throttle']['raw']}), {env.get('temp_c')} C")
    ok = bool(runs[0].text.strip())
    out("\nRESULT: " + ("generation produced text. Paste everything above back." if ok else "EMPTY OUTPUT. Paste everything above back."))
    return {"n0": n0, "n1": n1, "n_literal": nl, "n_header": nh, "verdicts": verdicts, "text": runs[0].text, "ok": ok,
            "env": env, "repeats": same}


def main(argv=None) -> int:
    import argparse
    from .backends.executorch_backend import ExecuTorchBackend

    p = argparse.ArgumentParser(description="First real run on the Pi: load, count tokens, generate once.")
    p.add_argument("--model", required=True)
    p.add_argument("--tokenizer", required=True)
    p.add_argument("--bos-in-prompt", action="store_true")
    p.add_argument("--num-bos", type=int, default=0)
    p.add_argument("--max-new", type=int, default=48)
    p.add_argument("--hash-model", action="store_true")
    p.add_argument("--chat-format", default="auto", choices=["auto", "llama3", "chatml", "qwen3"])
    a = p.parse_args(argv)
    try:
        backend = ExecuTorchBackend(a.model, a.tokenizer, bos_in_prompt=a.bos_in_prompt, num_bos=a.num_bos,
                                    hash_model=a.hash_model, chat_format=a.chat_format)
    except (FileNotFoundError, ImportError, RuntimeError, ValueError) as e:
        print(f"SMOKE FAILED before generating: {e}")
        return 2
    return 0 if run_smoke(backend, a.max_new)["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
