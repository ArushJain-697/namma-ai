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
