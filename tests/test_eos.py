"""Qwen's two end tokens, <|im_end|> (151645) and <|endoftext|> (151643): generation must stop at either one."""
import os
from types import SimpleNamespace

from sakshi.backends.executorch_backend import QWEN_EOS_IDS, ExecuTorchBackend, clean_output


class StreamingRunner:
    """Calls the token callback per token and honours stop(), like TextLLMRunner; writes to fd 1 as it goes."""

    def __init__(self, tokens):
        self.tokens, self.emitted, self.stopped, self.cfg = tokens, [], False, None

    def reset(self):
        self.stopped = False

    def stop(self):
        self.stopped = True

    def generate(self, prompt, config, token_cb, stats_cb):
        self.cfg = config
        for t in self.tokens:
            if self.stopped:
                break
            os.write(1, t.encode())
            self.emitted.append(t)
            if token_cb:
                token_cb(t)
        stats_cb(SimpleNamespace())


def _backend(tmp_path, tokens):
    m, t = tmp_path / "m.pte", tmp_path / "tokenizer.json"
    m.write_bytes(b"x")
    t.write_text('{"added_tokens": ["<|im_start|>", "<think>"]}')  # a Qwen3 tokenizer
    r = StreamingRunner(tokens)
    return ExecuTorchBackend(str(m), str(t), runner_factory=lambda *a: r, config_factory=lambda **k: SimpleNamespace(**k)), r


def test_qwen_backend_knows_both_eos_ids(tmp_path):
    b, _ = _backend(tmp_path, ["x"])
    assert b.eos_ids == QWEN_EOS_IDS == (151645, 151643) and b.info()["eos_ids"] == [151645, 151643]


def test_generation_stops_at_im_end(tmp_path):
    b, r = _backend(tmp_path, ["Question: Why", "?", "<|im_end|>", "<|im_start|>", "user", " junk"])
    res = b.generate("p", stop_regex=r"Answer:[^\n]*\n")
    assert "junk" not in r.emitted and res.text == "Question: Why?"


def test_generation_stops_at_endoftext(tmp_path):
    b, r = _backend(tmp_path, ["Plants make food.", "<|endoftext|>", "More text"])
    res = b.generate("p", stop_regex=r"zzz")
    assert "More text" not in r.emitted and res.text == "Plants make food."


def test_text_after_the_first_end_token_is_dropped_even_without_a_callback():
    assert clean_output("Answer: B<|im_end|>\n<|im_start|>user\nanother question") == "Answer: B"
    assert clean_output("Done.<|endoftext|>Next doc") == "Done."


def test_cancel_stops_the_runner(tmp_path):
    b, r = _backend(tmp_path, ["a"])
    b.cancel()
    assert r.stopped
