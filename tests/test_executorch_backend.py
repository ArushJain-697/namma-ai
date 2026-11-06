"""The ExecuTorch backend, tested with a FAKE runner that mimics the real callback protocol.

This proves our wrapper's logic only. It says nothing about a real model; that needs the Pi.
"""
from types import SimpleNamespace

import pytest
from sakshi.backends.executorch_backend import ExecuTorchBackend


class FakeRunner:
    def __init__(self, tokens=("Hello", " ", "world", "<|eot_id|>"), stats=None):
        self.tokens, self.calls, self.resets = tokens, [], 0
        self.stats = stats or SimpleNamespace(inference_start_ms=1000, prompt_eval_end_ms=1100, first_token_ms=1150,
                                              inference_end_ms=1650, num_prompt_tokens=50, num_generated_tokens=11)

    def reset(self):
        self.resets += 1

    def generate(self, prompt, config, token_cb, stats_cb):
        self.calls.append((prompt, config))
        for t in self.tokens:
            token_cb(t)
        stats_cb(self.stats)


def cfg(**kw):
    return SimpleNamespace(**kw)


@pytest.fixture
def files(tmp_path):
    m, t = tmp_path / "m.pte", tmp_path / "tok.model"
    m.write_bytes(b"x" * 2048)
    t.write_bytes(b"tok")
    return str(m), str(t)


def backend(files, runner=None, **kw):
    r = runner or FakeRunner()
    return ExecuTorchBackend(files[0], files[1], runner_factory=lambda *a: r, config_factory=cfg, **kw), r


def test_missing_files_raise_clearly(tmp_path, files):
    with pytest.raises(FileNotFoundError, match="model file not found"):
        ExecuTorchBackend(str(tmp_path / "nope.pte"), files[1], runner_factory=lambda *a: None, config_factory=cfg)
    with pytest.raises(FileNotFoundError, match="tokenizer file not found"):
        ExecuTorchBackend(files[0], str(tmp_path / "nope"), runner_factory=lambda *a: None, config_factory=cfg)


def test_generate_strips_stop_tokens_and_computes_stats(files):
    b, r = backend(files)
    res = b.generate("PROMPT", max_new_tokens=16, temperature=0.4, seed=7, task="stem", payload={"answer": "x"})
    assert res.text == "Hello world"  # <|eot_id|> stripped
    assert res.prompt_tokens == 50 and res.new_tokens == 11
    assert res.ttft_ms == 150  # first_token_ms - inference_start_ms
    assert res.tokens_per_s == 20.0  # (11 - 1) tokens over 0.5 s
    assert res.extra["prefill_tokens_per_s"] == 500.0  # 50 tokens over 0.1 s


def test_runner_is_reset_before_every_independent_prompt_and_seed_is_ignored(files):
    b, r = backend(files)
    b.generate("a")
    b.generate("b", seed=123)
    assert r.resets == 2 and [c[0] for c in r.calls] == ["a", "b"]
    c = r.calls[1][1]
    assert c.echo is False and c.num_eos == 0 and not hasattr(c, "seed")  # no seed exists in the real API


def test_config_carries_temperature_and_num_bos(files):
    b, r = backend(files, num_bos=1)
    b.generate("p", max_new_tokens=33, temperature=0.7)
    c = r.calls[0][1]
    assert (c.max_new_tokens, c.temperature, c.num_bos) == (33, 0.7, 1)


def test_missing_stats_fall_back_to_wall_time(files):
    r = FakeRunner(stats=SimpleNamespace())
    b, _ = backend(files, runner=r)
    res = b.generate("p")
    assert res.text == "Hello world" and res.new_tokens == 4 and res.tokens_per_s is None
    assert res.ttft_ms is not None and res.ttft_ms >= 0


def test_info_has_what_the_run_card_needs(files):
    b, _ = backend(files, hash_model=True, label="llama-3.2-1b-spinquant")
    i = b.info()
    assert i["name"] == "llama-3.2-1b-spinquant" and i["model_bytes"] == 2048
    assert len(i["sha256"]) == 64 and i["load_s"] >= 0 and i["model_path"].endswith("m.pte")
    plain, _ = backend(files)
    assert plain.info()["sha256"] is None  # hashing a 1.8 GB file is slow; opt-in only


def test_default_factory_gives_a_clear_error_when_runner_missing(files, monkeypatch):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name.startswith("executorch"):
            raise ModuleNotFoundError("No module named 'torch'")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(ImportError, match="pip install executorch"):
        ExecuTorchBackend(files[0], files[1])
