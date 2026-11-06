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
