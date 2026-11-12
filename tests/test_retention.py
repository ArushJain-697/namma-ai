"""Retention engine: bank repair, BKT, Bayes diagnosis, graph walk, FSRS scheduling, simulation."""
import json
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fsrs")

from conftest import ROOT  # noqa: E402
from sakshi.retention import bkt  # noqa: E402
from sakshi.retention.bank import bank_from_dict, load_bank  # noqa: E402
from sakshi.retention.bayes import NONE, Diagnosis  # noqa: E402
from sakshi.retention.fsrs_sched import make_scheduler, retrievability, review  # noqa: E402
from sakshi.retention.graph import ConceptGraph  # noqa: E402
from sakshi.retention.io import ModelStudent, ScriptedIO  # noqa: E402
from sakshi.retention.ranker import revision_plan  # noqa: E402
from sakshi.retention.session import AdaptiveSession, SessionConfig  # noqa: E402
from sakshi.retention.simulate import ascii_chart, simulate  # noqa: E402
from sakshi.retention.state import LearnerState  # noqa: E402

BANK = ROOT / "data" / "banks" / "photosynthesis.json"
NOW = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)


@pytest.fixture
def bank():
    return load_bank(str(BANK))


def run(bank, io, state=None, **cfg):
    state = state or LearnerState()
    res = AdaptiveSession(bank, state, io, SessionConfig(**cfg), now=NOW).run()
    return res, state


# ---- the sample bank ---------------------------------------------------------------------------------

def test_sample_bank_is_clean_and_diagnostic(bank):
    assert bank.notes == []
    assert len(bank.concepts) == 4 and len(bank.questions) == 12
    for q in bank.questions.values():
        assert sum(o.correct for o in q.options) == 1
        wrong = [o.misconception for o in q.options if not o.correct]
        assert all(wrong), f"{q.id}: every wrong option must name a misconception"
        assert len(set(wrong)) == len(wrong), f"{q.id}: each wrong option should reveal a different misconception"
        assert set(wrong) <= set(bank.concepts[q.concept].misconceptions)
    for cid in bank.concepts:
        types = {q.type for q in bank.questions_for(cid)}
        assert types == {"recall", "application"}, cid


# ---- bank repair (model output is messy) -------------------------------------------------------------

def _q(qid, concept, misc=("m1", "m2", "m3"), correct_count=1):
    opts = [{"key": "A", "text": "right", "correct": True}] if correct_count else []
    opts += [{"key": k, "text": f"wrong {k}", "correct": correct_count > 1 and k == "B", "misconception": m}
             for k, m in zip("BCD", misc)]
    return {"id": qid, "concept": concept, "type": "recall", "stem": "?", "options": opts}


def test_bank_drops_bad_questions_and_prereqs():
    b = bank_from_dict({
        "concepts": [{"id": "C1", "name": "a", "prereqs": ["C2"]}, {"id": "C2", "name": "b", "prereqs": ["C1", "C9"]}],
        "questions": [_q("Q1", "C1"), _q("Q2", "C7"), _q("Q3", "C1", correct_count=0), _q("Q4", "C2", correct_count=2)],
    })
    assert set(b.questions) == {"Q1"}
    assert b.concepts["C1"].prereqs == ["C2"]
    assert b.concepts["C2"].prereqs == []  # C1 would make a cycle; C9 does not exist
    assert any("cycle" in n for n in b.notes) and any("C9" in n for n in b.notes)


def test_free_text_misconceptions_are_merged_by_similarity():
    b = bank_from_dict({
        "concepts": [{"id": "C1", "name": "a", "prereqs": [],
                      "misconceptions": [{"id": "X1", "text": "Sunlight is the plant's food"}]}],
        "questions": [_q("Q1", "C1", misc=("sunlight is the plants food!", "X1", "Plants eat soil"))],
    })
    ms = [o.misconception for o in b.questions["Q1"].options if not o.correct]
    assert ms[0] == "X1" and ms[1] == "X1"
    assert ms[2] not in ("X1", None) and b.misconceptions[ms[2]].text == "Plants eat soil"


# ---- BKT ----------------------------------------------------------------------------------------------

def test_bkt_moves_the_right_way():
    p = 0.3
    assert bkt.update(p, True) > p
    assert bkt.update(p, False) < p
    # an application question is harder to guess, so a right answer is stronger evidence
    assert bkt.update(p, True, application=True) > bkt.update(p, True)
    assert p < bkt.implicit_credit(p) < bkt.update(p, True)
    q = 0.5
    for _ in range(20):
        q = bkt.update(q, True)
    assert 0.95 < q <= 1.0


# ---- Bayes --------------------------------------------------------------------------------------------

def test_bayes_confirms_after_two_consistent_picks(bank):
    d = Diagnosis("C4", bank.concepts["C4"].misconceptions)
    d.update(bank.questions["Q10"], "B")  # "just how leaves breathe" = C4M1
    h, p = d.top()
    assert h == "C4M1" and p < 0.75 and d.confirmed() is None and d.suspected() == "C4M1"
    d.update(bank.questions["Q11"], "D")  # C4M1 again
    assert d.confirmed() == "C4M1"
    assert abs(sum(d.posterior.values()) - 1) < 1e-9


def test_bayes_mixed_picks_do_not_confirm(bank):
    d = Diagnosis("C3", bank.concepts["C3"].misconceptions)
    d.update(bank.questions["Q7"], "A")  # C3M1
    d.update(bank.questions["Q8"], "A")  # C3M3
    assert d.confirmed() is None


def test_bayes_correct_answer_lowers_the_misconception(bank):
    d = Diagnosis("C2", bank.concepts["C2"].misconceptions)
    d.update(bank.questions["Q4"], "D")
    before = d.posterior["C2M1"]
    d.update(bank.questions["Q6"], "C")  # correct
    assert d.posterior["C2M1"] < before and d.posterior[NONE] > 0


def test_information_gain_prefers_a_question_that_tests_the_suspect(bank):
    d = Diagnosis("C1", bank.concepts["C1"].misconceptions)
    d.update(bank.questions["Q1"], "A")
    useless = bank_from_dict({"concepts": [{"id": "C1", "name": "a", "prereqs": []}],
                              "questions": [_q("Z1", "C1", misc=(None, None, None))]}).questions["Z1"]
    useless.concept = "C1"
    assert d.expected_gain(bank.questions["Q2"]) > d.expected_gain(useless)
    assert d.best_question([useless, bank.questions["Q2"]]).id == "Q2"


# ---- graph --------------------------------------------------------------------------------------------

def test_graph_levels_and_tops(bank):
    g = ConceptGraph(bank)
    assert g.tops() == ["C4"]
    assert [g.level(c) for c in ["C1", "C2", "C3", "C4"]] == [0, 1, 1, 2]
    assert g.below("C4") == {"C1", "C2", "C3"}
    assert set(g.parents("C1")) == {"C2", "C3"}


# ---- the session --------------------------------------------------------------------------------------

def test_strong_student_is_quick_and_gets_good_ratings(bank):
    io = ModelStudent(knows=set(bank.concepts))
    res, state = run(bank, io)
    assert set(res.outcomes) == set(bank.concepts)
    assert all(o in ("good", "easy") for o in res.outcomes.values())
    assert len(res.asked) == 4  # one question per concept, nothing wasted
    assert not res.detected and not res.suspected
    assert all(c.fsrs_card for c in state.concepts.values())


def test_demo_path_detects_walks_down_and_climbs_back(bank):
    io = ModelStudent(knows={"C1"}, holds={"C2M1", "C4M1"})
    res, state = run(bank, io)
    assert "C4M1" in res.detected and "C2M1" in res.detected
    # order: C4 first (most advanced), then down to C2 and C1, back up to C2, then C3, then back to C4
    concepts = [bank.questions[q].concept for q in res.asked]
    assert concepts[0] == "C4" and concepts[-1] == "C4"
    assert concepts.index("C1") > concepts.index("C2")
    assert res.outcomes == {"C1": "good", "C2": "hard", "C3": "hard", "C4": "hard"}
    text = "\n".join(io.lines)
    assert 'Misconception detected: "Photosynthesis is just the way plants breathe"' in text
    assert "Let's go back to the ideas this builds on" in text
    assert state.misconceptions["C4M1"].status.startswith("confirmed")


def test_no_question_is_asked_twice_and_budget_is_respected(bank):
    io = ModelStudent(learns_after_feedback=False)
    res, _ = run(bank, io, max_questions=7)
    assert len(res.asked) == 7 and len(set(res.asked)) == 7


def test_stubborn_student_ends_with_again(bank):
    res, _ = run(bank, ModelStudent(learns_after_feedback=False))
    assert len(res.asked) == len(set(res.asked))
    assert "again" in res.outcomes.values()


def test_depth_cap_stops_the_walk(bank):
    res, _ = run(bank, ModelStudent(learns_after_feedback=False), max_depth=0)
    assert [bank.questions[q].concept for q in res.asked][:3] == ["C4"] * 3  # no walk down before checking C4


def test_application_answer_gives_implicit_credit(bank):
    b = bank_from_dict(json.loads(BANK.read_text()))
    del b.questions["Q10"]  # C4's only recall question: the session now opens with an application question
    io = ModelStudent(knows=set(b.concepts))
    res, state = run(b, io)
    assert res.asked[0] in ("Q11", "Q12")
    assert set(res.implicit) == {"C1", "C2", "C3"}
    assert len(res.asked) == 1
    assert all(state.concepts[c].fsrs_card for c in b.concepts)


def test_stopping_early_saves_what_was_learned(bank, tmp_path):
    io = ScriptedIO(["C"])  # one answer, then the student stops
    res, state = run(bank, io)
    assert res.stopped_early and len(res.asked) == 1
    path = tmp_path / "s.json"
    state.save(str(path))
    again = LearnerState.load(str(path))
    assert again.concepts["C4"].fsrs_card and again.attempts[0]["picked"] == "C"


def test_second_session_builds_on_saved_state(bank):
    state = LearnerState()
    run(bank, ModelStudent(knows={"C1"}, holds={"C2M1", "C4M1"}), state)
    stab1 = state.concepts["C1"].fsrs_card["stability"]
    AdaptiveSession(bank, state, ModelStudent(knows=set(bank.concepts)), now=NOW + timedelta(days=3)).run()
    assert state.sessions == 2
    assert state.concepts["C1"].fsrs_card["stability"] > stab1


# ---- FSRS, ranker, simulation -------------------------------------------------------------------------

def test_fsrs_ratings_order_the_intervals():
    s = make_scheduler()
    due = {o: review(s, None, o, NOW)["due"] for o in ["again", "hard", "good", "easy"]}
    assert due["again"] <= due["hard"] <= due["good"] < due["easy"]
    card = review(s, None, "good", NOW)
    assert retrievability(s, card, NOW + timedelta(days=1)) > retrievability(s, card, NOW + timedelta(days=10))
    assert retrievability(s, None, NOW) == 0.0


def test_revision_plan_puts_the_weakest_first(bank):
    _, state = run(bank, ModelStudent(knows={"C1"}, holds={"C2M1", "C4M1"}))
    plan = revision_plan(state, {}, make_scheduler(), NOW + timedelta(days=2))
    assert plan[0].priority >= plan[-1].priority
    assert all(0 <= r.priority <= 1 for r in plan)


def test_simulation_schedule_beats_studying_once(bank):
    _, state = run(bank, ModelStudent(knows={"C1"}, holds={"C2M1", "C4M1"}))
    res = simulate(state, make_scheduler(), days=14, seed=1)
    assert len(res.daily_once) == len(res.daily_scheduled) == 14
    assert res.daily_scheduled[-1] > res.daily_once[-1]
    assert res.daily_once[-1] < res.daily_once[0]                                   # it decays...
    assert all(b <= a + 1e-9 for a, b in zip(res.daily_once, res.daily_once[1:]))  # ...and never recovers alone
    assert res.events and simulate(state, make_scheduler(), days=14, seed=1).events == res.events  # repeatable
    assert "day" in ascii_chart(res)


def test_simulation_needs_a_session_first():
    with pytest.raises(ValueError):
        simulate(LearnerState(), make_scheduler())
