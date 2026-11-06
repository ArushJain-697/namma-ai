import pytest
from conftest import sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.pipeline import prepare, visible_items
from sakshi.quiz import LETTERS, Session, resolve
from sakshi.text import normalize_answer

RUN = prepare(sample_passage(), StubBackend())
ITEMS = visible_items(RUN)


def scripted(answers):
    it = iter(answers)
    log = {"printed": [], "asked_at": []}

    def inp(prompt):
        log["asked_at"].append(len(log["printed"]))
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    return inp, (lambda s: log["printed"].append(s)), log


def right(item):
    if item.options:
        return LETTERS[[normalize_answer(o) for o in item.options].index(normalize_answer(item.key))]
    return item.key


def play(answers, **kw):
    inp, out, log = scripted(answers)
    res = Session(RUN, inp, out, **kw).run_quiz()
    return res, "\n".join(log["printed"]), log


def test_resolve_letter_text_and_word():
    opts = ["rust", "Oxygen", "zinc", "gate"]
    assert resolve("b", opts) == resolve("B", opts) == resolve("oxygen.", opts) == resolve("The Oxygen", opts) == "oxygen"
    assert resolve("Z", opts) == "z"  # a letter outside the options is just text
    assert resolve("  ", None) == ""


def test_all_right_no_retries():
    res, text, _ = play([right(i) for i in ITEMS])
    assert res.score == res.total == len(ITEMS) and not res.missed and not res.retries and not res.reread
    assert f"You got {res.total} of {res.total}." in text
    assert text.count("Correct. Here is where the passage says it") == len(ITEMS)


def test_all_wrong_shows_every_witness_and_closing_lists_exactly_them():
    res, text, _ = play(["zzz"] * 100)
    assert res.score == 0 and len(res.missed) == len(ITEMS)
    for it in ITEMS:
        assert it.witness in text  # the witness is the feedback
    assert res.reread == sorted({i.witness_idx + 1 for i in ITEMS})
    line = [l for l in text.splitlines() if l.startswith("Worth rereading:")][0]
    for n in res.reread:
        assert f"sentence {n}" in line


def test_retries_use_the_same_witness_and_never_a_revealed_key():
    res, _, _ = play(["zzz"] * 100)
    by_id = {i.id: i for i in ITEMS}
    revealed = {normalize_answer(i.key) for i in ITEMS}
    assert res.retries
    for r in res.retries:
        assert r["witness_idx"] == by_id[r["item_id"]].witness_idx
        assert normalize_answer(r["key"]) not in revealed


def test_mixed_answers_score_and_retry_counts():
    ans = [right(ITEMS[0]), "zzz", right(ITEMS[2])] + [right(i) for i in ITEMS[3:]]
    inp_answers = ans + ["zzz"] * 10
    res, text, _ = play(inp_answers)
    assert res.score == len(ITEMS) - 1 and res.missed == [ITEMS[1].id]
    assert res.reread == [ITEMS[1].witness_idx + 1]


def test_empty_input_repeats_then_skips_and_never_crashes():
    res, text, _ = play([""] * 3 + [right(ITEMS[1])] + [right(i) for i in ITEMS[2:]])
    assert res.skipped == 1 and "Please type an answer." in text and res.missed == [ITEMS[0].id]


def test_full_option_text_and_lowercase_letter_are_accepted():
    first = ITEMS[0]
    typed = first.options[[normalize_answer(o) for o in first.options].index(normalize_answer(first.key))] + "."
    res, _, _ = play([typed] + [right(i).lower() if len(right(i)) == 1 else right(i) for i in ITEMS[1:]])
    assert res.score == res.total


def test_answer_is_not_shown_before_the_student_types():
    res, text, log = play(["zzz"] * 100)
    before_first = "\n".join(log["printed"][:log["asked_at"][0]])
    assert "The answer is" not in before_first
    assert ITEMS[0].witness not in before_first  # the witness only appears AFTER answering


def test_summary_comes_after_questions_by_default_and_before_when_asked():
    _, text, _ = play([right(i) for i in ITEMS])
    assert text.index("Question 1 of") < text.index("In short:")
    _, text2, _ = play([right(i) for i in ITEMS], summary_first=True)
    assert text2.index("In short:") < text2.index("Question 1 of")


def test_eof_ends_gracefully():
    res, text, _ = play([right(ITEMS[0])])
    assert res.ended_early and res.score == 1


def test_amber_hidden_by_default_and_labelled_when_included():
    run = prepare(sample_passage(), StubBackend())
    assert all(i.tier == "GREEN" for i in visible_items(run))
    amber = [i for i in run.items if i.tier == "AMBER"]
    if amber:
        inp, out, log = scripted(["zzz"] * 100)
        Session(run, inp, out, include_amber=True).run_quiz()
        assert any("check this one with your teacher" in l for l in log["printed"])


def test_no_visible_items_message():
    empty = prepare("Too short.", StubBackend())
    inp, out, log = scripted([])
    res = Session(empty, inp, out).run_quiz()
    assert res.total == 0 and any("No questions passed" in l for l in log["printed"])
