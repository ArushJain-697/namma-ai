"""The answer-back check: a question is only accepted if the model, given only the witness sentence, answers it
with the code-picked key. Found necessary with the real Qwen3-0.6B (fluent questions that ask for the wrong thing)."""
from conftest import sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.generate import answers_match, make_stem, verify_stem
from sakshi.metrics import token_stats
from sakshi.pipeline import prepare, visible_items

W = "Rust is a reddish-brown layer that flakes away from the metal, and each flake exposes fresh iron underneath."


def test_answers_match():
    assert answers_match("fresh iron", "iron")
    assert answers_match("The Himalayas.", "Himalayas")
    assert answers_match("it rusts", "rusting")  # same stem
    assert not answers_match("a layer", "iron")
    assert not answers_match("", "iron")
    assert not answers_match("iron", "fresh iron")  # every word of the key must be named


def test_verify_rejects_a_question_that_asks_for_something_else():
    ok, stats = verify_stem(StubBackend(), "What is exposed underneath each flake?", W, "iron")
    assert ok.passed and stats["text"] == "iron"
    bad, stats = verify_stem(StubBackend("off_key"), "What is exposed underneath each flake?", W, "layer")
    assert not bad.passed and bad.severity == "HARD" and "something else" in bad.detail


def test_a_long_reply_does_not_count_as_naming_the_key():
    class Copier(StubBackend):
        def generate(self, prompt, **kw):
            r = super().generate(prompt, **kw)
            if kw.get("task") == "answer":
                r.text = W  # copies the whole sentence: it "contains" every possible key
            return r
    res, _ = verify_stem(Copier(), "What flakes away?", W, "layer")
    assert not res.passed


def test_make_stem_retries_until_the_answer_back_matches():
    sr = make_stem(StubBackend("off_key", fail_first=1), W, "layer", W)
    assert sr.text is not None and sr.tier != "RED"
    assert len(sr.attempts) == 2
    assert "stem_answers_to_key" in [c.name for c in sr.attempts[0].checks if not c.passed]
    assert sr.attempts[1].verify["text"] == "layer"


def test_off_key_questions_never_reach_students_and_the_quiz_still_has_three():
    run = prepare(sample_passage(), StubBackend("off_key"))
    vis = visible_items(run)
    assert len(vis) >= 3 and all(i.fallback for i in vis)  # only code-built cloze items survive
    model_items = [i for i in run.items if not i.fallback]
    assert model_items and all(i.tier == "RED" for i in model_items)
    assert any("stem_answers_to_key" in r for i in model_items for r in i.reasons)


def test_verification_calls_count_in_the_token_totals():
    run = prepare(sample_passage(), StubBackend())
    ts = token_stats(run)
    n_verify = sum(1 for i in run.items for a in i.attempts if a.get("verify"))
    n_attempts = sum(len(i.attempts) for i in run.items) + sum(len(s["attempts"]) for s in run.summary["sentences"])
    assert n_verify > 0 and ts["calls"] == n_attempts + n_verify
