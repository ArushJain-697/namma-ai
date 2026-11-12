"""Backend interface. One interface, many engines (ExecuTorch on the Pi, a stub for tests).

The model's text never becomes an answer key: backends only return text, and code decides
what to do with it. Real backends ignore `task` and `payload`; those exist so the stub can
behave sensibly without a model.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenResult:
    text: str
    prompt_tokens: int = 0
    new_tokens: int = 0
    ttft_ms: float | None = None  # time to first token
    tokens_per_s: float | None = None  # decode rate
    wall_s: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)


class Backend(ABC):
    name: str = "backend"
    chat_format: str = "llama3"  # how prompts are wrapped for this model; see chat_prompt()
    bos_in_prompt: bool = False

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.0,
        seed: int | None = None,
        task: str | None = None,
        payload: dict | None = None,
    ) -> GenResult: ...

    def info(self) -> dict[str, Any]:
        """Name, model path, size on disk, load seconds. Used by the run card."""
        return {"name": self.name}


def llama3_chat(system: str, user: str, bos: bool = False) -> str:
    """Llama 3.x instruct chat template.

    BOS handling is UNVERIFIED: the runner may add a BOS itself (num_bos), in which case
    adding one here doubles it. `scripts/pi_smoke.py` counts BOS tokens to settle this
    (build map T17), so `bos` defaults to False.
    """
    head = "<|begin_of_text|>" if bos else ""
    return (
        f"{head}<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )


CHAT_FORMATS = ("llama3", "chatml", "qwen3")


def chat_prompt(fmt: str, system: str, user: str, bos: bool = False, examples: tuple = ()) -> str:
    """Wrap a system and user message in the chat template the model was trained on.

    llama3  Llama 3.x instruct headers.
    chatml  <|im_start|> / <|im_end|> turns: Qwen2.5 and most other instruct models.
    qwen3   chatml plus an EMPTY thinking block, which switches Qwen3's "thinking mode" off. Otherwise it writes
            a long hidden monologue first, which costs minutes on a Pi.
    `examples` are (user, assistant) pairs placed as earlier, finished turns. Small models copy an example that
    sits inside the same message as the task (seen with Qwen3-0.6B: every question became the example question);
    as a separate turn they treat it as a pattern instead.
    """
    if fmt not in CHAT_FORMATS:
        raise ValueError(f"unknown chat format {fmt!r}; choose one of {', '.join(CHAT_FORMATS)}")
    if fmt == "llama3":
        if not examples:
            return llama3_chat(system, user, bos=bos)
        turn = lambda role, text: f"<|start_header_id|>{role}<|end_header_id|>\n\n{text}<|eot_id|>"  # noqa: E731
        return (("<|begin_of_text|>" if bos else "") + turn("system", system)
                + "".join(turn("user", u) + turn("assistant", a) for u, a in examples)
                + turn("user", user) + "<|start_header_id|>assistant<|end_header_id|>\n\n")
    think = "<think>\n\n</think>\n\n" if fmt == "qwen3" else ""
    turn = lambda role, text: f"<|im_start|>{role}\n{text}<|im_end|>\n"  # noqa: E731
    return (turn("system", system)
            + "".join(turn("user", u) + turn("assistant", think + a) for u, a in examples)
            + turn("user", user) + "<|im_start|>assistant\n" + think)


def chat_for(backend: Backend, system: str, user: str, examples: tuple = ()) -> str:
    """The prompt for this backend's model."""
    return chat_prompt(getattr(backend, "chat_format", "llama3"), system, user,
                       bos=getattr(backend, "bos_in_prompt", False), examples=examples)
