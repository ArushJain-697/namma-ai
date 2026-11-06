import pytest
from conftest import sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.pipeline import prepare
from sakshi.regen import edit, item_sentences, render_report, replace_sentence
from sakshi.text import find_span, split_sentences

P = sample_passage()
S = split_sentences(P)
B = StubBackend()


def snapshot(it):
    return (it.stem, it.key, it.options, it.witness, it.tier, it.reserve and (it.reserve["stem"], it.reserve["key"]))


def test_item_sentences_lists_only_sentences_with_questions():
    run = prepare(P, B)
    m = item_sentences(run)
    assert m and all(0 <= k < len(S) for k in m)
    assert set(m) == {i.witness_idx for i in run.items if i.tier == "GREEN"}


def test_replace_sentence_and_bounds():
    new = replace_sentence(P, 9, "In 1887, a town repainted its bridge.")
    assert split_sentences(new)[9] == "In 1887, a town repainted its bridge." and len(split_sentences(new)) == len(S)
    with pytest.raises(IndexError):
        replace_sentence(P, 99, "x")


def test_no_change_changes_nothing():
    run = prepare(P, B)
    new, rep = edit(run, P, B)
    assert "no change detected" in rep.notes and rep.model_calls == 0 and not rep.changed
    assert [snapshot(i) for i in new.items] == [snapshot(i) for i in run.items]


def test_year_edit_updates_only_the_affected_item_and_flags_the_stale_summary():
    run = prepare(P, B, force_sentences=[9], force_terms={9: "1999"})
    assert run.items[0].key == "1999" and run.items[0].witness_idx == 9
    stem_before = run.items[0].stem
    new_passage = replace_sentence(P, 9, S[9].replace("1999", "1887"))
    new, rep = edit(run, new_passage, B)
    first = new.items[0]
    assert first.key == "1887" and "1887" in first.witness
    # this passage has no other numbers to use as wrong options, so a year question is short-answer (options None)
    assert first.options is None or ("1887" in first.options and "1999" not in first.options)
    assert first.stem == stem_before  # a year swap keeps the question: no model call for the stem
    assert not rep.items_updated[0]["model_called_for_stem"]
    # every other item is byte-identical
    assert [snapshot(i) for i in new.items[1:]] == [snapshot(i) for i in run.items[1:]]
    assert set(rep.items_untouched) == {i.id for i in run.items[1:]}
    # the summary sentence built from sentence 9 contained 1999: the number check marks it STALE, then it is rewritten
    assert rep.summary_stale and any("numbers" in r for r in rep.summary_stale[0]["reasons"])
    assert "1887" in new.summary["text"] and "1999" not in new.summary["text"]
    assert rep.model_calls >= 1 and rep.seconds >= 0
    assert "STALE" in render_report(rep) and "answer '1999' -> '1887'" in render_report(rep)


def test_key_still_present_keeps_the_question():
    run = prepare(P, B)
    it9 = next(i for i in run.items if i.witness_idx == 9)
    new, rep = edit(run, replace_sentence(P, 9, S[9].replace("1999", "1887")), B)
    after = next(i for i in new.items if i.id == it9.id)
    assert after.key == it9.key and "1887" in after.witness and after.tier in ("GREEN", "AMBER")


def test_word_key_removed_gets_a_new_code_picked_key():
    run = prepare(P, B)
    it = next(i for i in run.items if i.key == "zinc")
    new_s = S[it.witness_idx].replace("zinc", "copper")
    new, rep = edit(run, replace_sentence(P, it.witness_idx, new_s), B)
    after = next(i for i in new.items if i.id == it.id)
    assert after.key != "zinc" and find_span(after.witness, after.key)  # the key is always a span of the new witness
    assert "zinc" not in (after.options or [])
    assert rep.items_updated and rep.items_updated[0]["old_key"] == "zinc"


def test_deleted_witness_goes_red_with_a_reason():
    run = prepare(P, B)
    it = next(i for i in run.items if i.tier == "GREEN")
    kept = [s for k, s in enumerate(S) if k != it.witness_idx]
    new, rep = edit(run, " ".join(kept), B)
    after = next(i for i in new.items if i.id == it.id)
    assert after.tier == "RED" and "witness removed" in after.reasons[0]
    assert {"id": it.id, "reason": "witness removed"} in rep.items_red


def test_sentence_inserted_earlier_shifts_indices_but_not_content():
    run = prepare(P, B)
    new_passage = "Metal care matters in every town. " + P
    new, rep = edit(run, new_passage, B)
    assert rep.model_calls == 0 and not rep.changed
    for old, now in zip(run.items, new.items):
        assert now.witness_idx == old.witness_idx + 1 and (now.stem, now.key, now.options) == (old.stem, old.key, old.options)
        assert find_span(now.witness, now.key)


def test_cloze_items_are_rebuilt_by_code_not_the_model():
    run = prepare(P, StubBackend("leak"))  # all model stems fail: visible items are cloze fallbacks
    it = next(i for i in run.items if i.fallback and i.tier == "GREEN")
    new_s = S[it.witness_idx].replace(it.key, "XYZ" if False else it.key)  # keep the key, change another word
    other = [w for w in S[it.witness_idx].split() if w.lower().strip(".,") != it.key.lower()][1]
    new, rep = edit(run, replace_sentence(P, it.witness_idx, S[it.witness_idx].replace(other, "different", 1)), StubBackend("leak"))
    after = next(i for i in new.items if i.id == it.id)
    assert after.kind == "cloze" and "_____" in after.stem and after.key.lower() == it.key.lower()


def test_edit_time_and_calls_are_recorded_in_the_new_run():
    run = prepare(P, B, force_sentences=[9], force_terms={9: "1999"})
    new, rep = edit(run, replace_sentence(P, 9, S[9].replace("1999", "1887")), B)
    assert new.timings["edit_s"] == rep.seconds and new.timings["model_calls"] == rep.model_calls
    assert new.passage != run.passage and new.counts["green"] >= 1
