import pytest

from sakshi.backends.base import llama3_chat
from sakshi.backends.stub import MODES, StubBackend
from sakshi.text import contains_term, tokens

S = "In 1999, a town in our district repainted its old iron bridge to protect it."


def gen(b, task, **payload):
    return b.generate("prompt", task=task, payload=payload).text


def test_faithful_simplify_and_stem():
    b = StubBackend()
    assert gen(b, "simplify", sentence=S) == S
    q = gen(b, "stem", sentence=S, answer="bridge")
    assert q.endswith("?") and not contains_term(q, "bridge")


def test_bad_number_changes_a_number():
    out = gen(StubBackend("bad_number"), "simplify", sentence=S)
    assert "1999" not in out and out != S
    assert "1989" in gen(StubBackend("bad_number"), "simplify", sentence="The gate is old.")  # adds a number


def test_invent_negate_hard_empty():
    assert "Paris" in gen(StubBackend("invent"), "simplify", sentence=S)
    assert " not " in " " + gen(StubBackend("negate"), "simplify", sentence="Iron is strong.") + " "
    assert "Ferrous" in gen(StubBackend("hard_words"), "simplify", sentence=S)
    assert gen(StubBackend("empty"), "simplify", sentence=S) == ""


def test_stem_faults():
    assert contains_term(gen(StubBackend("leak"), "stem", sentence=S, answer="bridge"), "bridge")
    assert not gen(StubBackend("nomark"), "stem", sentence=S, answer="bridge").endswith("?")
    assert len(tokens(gen(StubBackend("long"), "stem", sentence=S, answer="bridge"))) > 20


def test_echo_returns_prompt():
    assert StubBackend("echo").generate("hello prompt", task="stem", payload={"sentence": S, "answer": "bridge"}).text == "hello prompt"


def test_fail_first_then_recovers():
    b = StubBackend("bad_number", fail_first=2)
    outs = [gen(b, "simplify", sentence=S) for _ in range(3)]
    assert outs[0] != S and outs[1] != S and outs[2] == S


def test_deterministic_and_modes_cover_all():
    for m in MODES:
        assert gen(StubBackend(m), "simplify", sentence=S) == gen(StubBackend(m), "simplify", sentence=S)
    with pytest.raises(ValueError):
        StubBackend("nope")


def test_llama3_template_has_all_headers_and_bos_flag():
    t = llama3_chat("SYS", "USER")
    assert t.count("<|start_header_id|>") == 3 and t.count("<|eot_id|>") == 2 and "<|begin_of_text|>" not in t
    assert llama3_chat("a", "b", bos=True).startswith("<|begin_of_text|>")
    assert t.endswith("<|start_header_id|>assistant<|end_header_id|>\n\n")
