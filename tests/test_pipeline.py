import json

import pytest
from conftest import sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.pipeline import Run, prepare, visible_items
from sakshi.text import contains_term, find_span

P = sample_passage()


def test_stub_run_end_to_end():
    run = prepare(P, StubBackend())
    assert run.gate["status"] == "OK"
    assert run.summary["sentences"] and run.summary["word_count"] >= 30
    vis = visible_items(run)
    assert len(vis) >= 3  # the brief's "at least three"
    for it in vis:
        assert it.witness and find_span(it.witness, it.key)  # no witness, no question
        assert it.tier == "GREEN"
        assert not contains_term(it.stem, it.key) or it.kind == "cloze"
    assert run.timings["model_calls"] > 0 and run.counts["green"] >= 3


def test_json_roundtrip_is_lossless():
    run = prepare(P, StubBackend())
    again = Run.from_json(run.to_json())
    assert again.to_json() == run.to_json()
    json.loads(run.to_json())  # valid JSON


def test_rejected_passage_returns_a_reason_and_no_items():
    run = prepare("Too short.", StubBackend())
    assert run.gate["status"] == "REJECTED" and "need 150-300" in run.gate["reason"] and run.items == []


def test_red_items_are_kept_with_reasons_never_dropped():
    run = prepare(P, StubBackend("leak"))  # every model stem leaks the answer
    reds = [i for i in run.items if i.tier == "RED"]
    assert reds and all(i.reasons for i in reds)
    assert all(i.stem.startswith("(withheld") for i in reds)
    assert run.counts["red"] == len(reds)


def test_cloze_fallback_fills_to_three_visible_when_model_fails():
    run = prepare(P, StubBackend("leak"))
    vis = visible_items(run)
    assert len(vis) >= 3 and all(i.fallback and i.kind == "cloze" for i in vis)
    assert all("_____" in i.stem and not contains_term(i.stem, i.key) for i in vis)
    assert run.counts["fallback"] >= 3


def test_visible_keys_are_unique():
    run = prepare(P, StubBackend("leak"))
    keys = [i.key.lower() for i in visible_items(run)]
    assert len(keys) == len(set(keys))


def test_keys_come_from_code_not_the_model():
    # A misbehaving model changes the wording and tiers; it must never change a key or a witness.
    good, bad = prepare(P, StubBackend("faithful")), prepare(P, StubBackend("leak"))
    assert [(i.key, i.witness_idx) for i in good.items[:6]] == [(i.key, i.witness_idx) for i in bad.items[:6]]
    assert good.counts["red"] == 0 and bad.counts["red"] == 6
    for run in (good, bad):
        for it in run.items:
            assert find_span(it.witness, it.key)


def test_reserve_is_a_different_term_from_same_witness():
    run = prepare(P, StubBackend())
    with_reserve = [i for i in run.items if i.reserve]
    assert with_reserve
    for it in with_reserve:
        r = it.reserve
        assert r["witness_idx"] == it.witness_idx and r["key"].lower() != it.key.lower()
        assert find_span(it.witness, r["key"]) and "_____" in r["stem"]


def test_force_sentence_puts_that_sentence_first():
    run = prepare(P, StubBackend(), force_sentences=[9])
    assert run.items[0].witness_idx == 9


def test_untouched_determinism():
    a, b = prepare(P, StubBackend()), prepare(P, StubBackend())
    strip = lambda r: [(i.stem, i.key, i.options, i.tier) for i in r.items]
    assert strip(a) == strip(b)
