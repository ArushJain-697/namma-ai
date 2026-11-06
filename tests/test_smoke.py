from types import SimpleNamespace

from sakshi.backends.executorch_backend import ExecuTorchBackend
from sakshi.smoke import bos_verdict, header_verdict, run_smoke


def test_bos_verdicts_cover_every_combination():
    assert "--num-bos 1" in bos_verdict(1, 2, 2)[0]
    assert "adds a BOS itself and ignores" in bos_verdict(2, 2, 3)[0]
    assert "ANOTHER" in bos_verdict(2, 3, 3)[0]
    assert "--bos-in-prompt" in bos_verdict(1, 1, 2)[0]
    assert "unexpected" in bos_verdict(5, 9, 9)[0]
    assert any("ONE special token" in v for v in bos_verdict(1, 2, 2))
    assert any("NOT parsed" in v for v in bos_verdict(1, 2, 6))


def test_header_verdict():
    assert "special tokens" in header_verdict(3)
    assert "PROBLEM" in header_verdict(14)
    assert "special tokens" in header_verdict(4, auto_bos=1)


class CountingRunner:
    """Token count = number of words in the prompt, plus num_bos, plus 1 if the runner adds BOS itself."""
    def __init__(self, auto_bos=False):
        self.auto_bos = auto_bos

    def reset(self): pass

    def generate(self, prompt, cfg, tok_cb, stats_cb):
        n = len(prompt.split()) + cfg.num_bos + (1 if self.auto_bos else 0)
        for t in ("Iron", " rusts", " in", " damp", " air"):
            tok_cb(t)
        stats_cb(SimpleNamespace(inference_start_ms=0, prompt_eval_end_ms=10, first_token_ms=20, inference_end_ms=120,
                                 num_prompt_tokens=n, num_generated_tokens=5))


def test_run_smoke_end_to_end_with_a_fake_runner(tmp_path):
    m, t = tmp_path / "m.pte", tmp_path / "t.model"
    m.write_bytes(b"x" * 100)
    t.write_bytes(b"x")
    b = ExecuTorchBackend(str(m), str(t), runner_factory=lambda *a: CountingRunner(),
                          config_factory=lambda **k: SimpleNamespace(**k))
    lines = []
    r = run_smoke(b, out=lines.append)
    text = "\n".join(lines)
    assert r["ok"] and r["n0"] == 1 and r["n1"] == 2  # 'hi' = 1 word; num_bos=1 adds one
    assert "Use --num-bos 1" in text and "temperature 0 repeats itself: True" in text and "RESULT: generation produced text" in text
    assert "model load:" in text and "peak memory:" in text and "network:" in text
