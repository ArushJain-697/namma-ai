from conftest import sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.generate import (build_cloze, clean_line, make_stem, make_summary, make_whole_summary, simplify_sentence)
from sakshi.select import analyse
from sakshi.text import contains_term, tokens

P = sample_passage()
A = analyse(P)
W = A.sentences[9]  # "In 1999, a town in our district repainted its old iron bridge to protect it."


def test_clean_line_strips_tokens_labels_quotes():
    assert clean_line("What is it?<|eot_id|>") == "What is it?"
    assert clean_line('Question: "What is it?"\nextra') == "What is it?"
    assert clean_line("\n\n  Rewrite: Iron rusts.  <|eot_id|>") == "Iron rusts."
    assert clean_line("") == "" and clean_line(None) == ""


def test_faithful_summary_is_witnessed_and_in_range():
    b = StubBackend("faithful")
    s = make_summary(b, A)
    assert 2 <= len(s.sentences) <= 3
    assert [x.src_idx for x in s.sentences] == sorted(x.src_idx for x in s.sentences)  # passage order
    assert all(not x.fallback and x.source == A.sentences[x.src_idx] for x in s.sentences)
    assert all(c.passed for c in s.checks), s.checks
    assert 30 <= s.word_count <= 80
    assert all(c["task"] == "simplify" for c in b.calls)


def test_every_fault_falls_back_to_the_source_sentence():
    for mode in ("bad_number", "invent", "negate", "hard_words", "empty"):
        r = simplify_sentence(StubBackend(mode), 9, W) if mode != "negate" else simplify_sentence(StubBackend(mode), 0, A.sentences[0])
        src = W if mode != "negate" else A.sentences[0]
        assert r.fallback and r.text == src, mode  # no witness, no summary sentence
        assert len(r.attempts) == 3, mode


def test_fail_first_recovers_without_fallback():
    r = simplify_sentence(StubBackend("bad_number", fail_first=1), 9, W)
    assert not r.fallback and r.text == W and len(r.attempts) == 2


def test_retries_change_temperature():
    b = StubBackend("bad_number")
    simplify_sentence(b, 9, W)
    assert [c["temperature"] for c in b.calls] == [0.0, 0.4, 0.7]


def test_summary_with_a_lying_model_still_contains_only_passage_text():
    s = make_summary(StubBackend("invent"), A)
    assert all(x.fallback for x in s.sentences)
    assert "Paris" not in s.text
    assert all(any(x.text == sent for sent in A.sentences) for x in s.sentences)


def test_stem_faithful_is_valid_and_never_leaks():
    r = make_stem(StubBackend("faithful"), W, "bridge", P)
    assert r.text and r.text.endswith("?") and not contains_term(r.text, "bridge")
    assert r.tier in ("GREEN", "AMBER")


def test_stem_faults_end_red_with_reasons():
    for mode in ("leak", "nomark", "long", "empty", "echo"):
        r = make_stem(StubBackend(mode), W, "bridge", P)
        assert r.text is None and r.tier == "RED" and r.reasons, mode
        assert len(r.attempts) == 3


def test_stem_retry_recovers():
    r = make_stem(StubBackend("leak", fail_first=1), W, "bridge", P)
    assert r.text and len(r.attempts) == 2 and r.tier in ("GREEN", "AMBER")


def test_stem_duplicate_of_existing_is_rejected():
    first = make_stem(StubBackend(), W, "bridge", P)
    again = make_stem(StubBackend(), W, "bridge", P, other_stems=[first.text])
    assert again.text is None and any("duplicate" in r for r in again.reasons)


def test_cloze_is_code_built_and_blanks_the_key():
    c = build_cloze(W, "bridge")
    assert c.startswith("Fill in the blank:") and "_____" in c and not contains_term(c, "bridge")


def test_whole_summary_arm_runs():
    r = make_whole_summary(StubBackend(), P)
    assert "text" in r and r["attempts"]


# ---- summary stop rule and strip_reasons (device pipeline) ---------------------------------------------------------
import re as _re

from sakshi.generate import SENTENCE_STOP, first_sentence, strip_reason, strip_reasons, summary_in_parts


def _stops_at(stream: str) -> str | None:
    """Feed the text one character at a time, as the runner's token callback does; return the text when it stops."""
    pat = _re.compile(SENTENCE_STOP, _re.S)
    for i in range(1, len(stream) + 1):
        if pat.search(stream[:i]):
            return stream[:i]
    return None


def test_summary_stop_rule_does_not_cut_at_a_decimal_point():
    s = "A leaf is about 3.5 cm long and makes food. Then more."
    assert _stops_at(s) == "A leaf is about 3.5 cm long and makes food. "  # old rule stopped at "about 3."
    assert first_sentence("Light moves at 3.0 lakh km per second. It is fast.") == "Light moves at 3.0 lakh km per second."


def test_summary_stop_rule_skips_abbreviations_and_initials_but_ends_real_sentences():
    assert first_sentence("Metals, e.g. iron, rust in air. Next.") == "Metals, e.g. iron, rust in air."
    assert first_sentence("J. C. Bose showed plants respond. Next.") == "J. C. Bose showed plants respond."
    assert first_sentence("Is it hot? Yes.") == "Is it hot?"
    assert first_sentence("No end here") == "No end here"
    assert _stops_at("Water boils at 100.") is None  # end of the stream so far is not a sentence end yet


def test_summary_in_parts_keeps_the_decimal_number():
    calls = []

    def run(system, user, max_new, examples=(), kind="", stop=None):
        calls.append(stop)
        return " The leaf is 3.5 cm long. Extra text."
    sents = ["One fact here.", "Two facts here.", "Three facts here."]
    out = summary_in_parts(run, " ".join(sents), lambda p: sents, "SYS")
    assert out["text"] == "The leaf is 3.5 cm long." and calls[0] == SENTENCE_STOP


def test_strip_reasons_only_cuts_the_trailing_reason_clause():
    k, w = strip_reasons("The rougher one, since it has more bumps",
                         ["The smoother one, since it is flat", "The heavier one, because it weighs more",
                          "The lighter one due to its size"])
    assert (k, w) == ("The rougher one", ["The smoother one", "The heavier one", "The lighter one"])


def test_strip_reasons_keeps_answers_that_merely_contain_as_or_since():
    key, wrong = "As hard as steel", ["As soft as clay", "As light as air", "As bendy as rubber"]
    assert strip_reasons(key, wrong) == (key, wrong)  # starts with "As": nothing is a reason here
    for o in ("It stays the same since 1947", "Water as a gas", "It was used as fuel", "Bigger so it floats"):
        assert strip_reason(o) == o  # the old rule cut " since 1947", " as a gas", " as fuel"
    assert strip_reason("Ice floats because it is less dense") == "Ice floats"
    assert strip_reason("Ice floats, as it is less dense") == "Ice floats"


def test_strip_reasons_leaves_options_alone_when_cutting_makes_two_equal_or_one_starts_with_a_reason():
    key, wrong = "Ice, because it is cold", ["Ice, because it is wet", "Steam", "Water"]
    assert strip_reasons(key, wrong) == (key, wrong)
    key, wrong = "Because air pushes it", ["Because it is heavy", "Since it is light", "Due to gravity"]
    assert strip_reasons(key, wrong) == (key, wrong)
