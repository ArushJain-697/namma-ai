"""Build a backend from command-line style options, shared by the CLI and the scripts."""
from __future__ import annotations

import argparse
import sys

from .stub import MODES, StubBackend


def add_backend_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--backend", default="stub", choices=["stub", "executorch", "resident"])
    p.add_argument("--stub-mode", default="faithful", choices=MODES)
    p.add_argument("--stub-baseline", default="memory", choices=["memory", "passage"],
                   help="STUB ONLY: does the simulated one-call baseline answer from memory or the passage")
    p.add_argument("--model")
    p.add_argument("--tokenizer")
    p.add_argument("--socket", help="Unix socket of a running `sakshi resident` process (backend=resident)")
    p.add_argument("--bos-in-prompt", action="store_true", help="put <|begin_of_text|> in the prompt (see build map T17)")
    p.add_argument("--num-bos", type=int, default=0, help="BOS tokens the runner adds (see scripts/pi_smoke.py)")
    p.add_argument("--hash-model", action="store_true", help="sha256 the .pte for the run card (slow on a Pi)")
    p.add_argument("--chat-format", default="auto", choices=["auto", "llama3", "chatml", "qwen3"],
                   help="prompt template; auto reads it from the tokenizer (Qwen3 -> qwen3, Qwen2.5 -> chatml)")


def build_backend(args):
    b = args.backend
    if b == "stub":
        return StubBackend(args.stub_mode, baseline=getattr(args, "stub_baseline", "memory"))
    if b == "resident":
        from ..resident import ResidentClient
        if not args.socket:
            sys.exit("--backend resident needs --socket")
        try:
            return ResidentClient(args.socket)
        except OSError as e:
            sys.exit(f"cannot reach the resident model process at {args.socket}: {e}")
    if b == "executorch":
        if not (args.model and args.tokenizer):
            sys.exit("--backend executorch needs --model and --tokenizer")
        try:
            from .executorch_backend import ExecuTorchBackend
            return ExecuTorchBackend(args.model, args.tokenizer, bos_in_prompt=args.bos_in_prompt, num_bos=args.num_bos,
                                     hash_model=args.hash_model, chat_format=getattr(args, "chat_format", "auto"))
        except (FileNotFoundError, ImportError, RuntimeError, ValueError) as e:  # a clear message, not a traceback
            sys.exit(f"The ExecuTorch backend is not available: {e}")
    sys.exit(f"unknown backend {b!r}")
