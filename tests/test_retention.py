"""Retention engine: bank repair, BKT, Bayes diagnosis, graph walk, FSRS scheduling, simulation."""
import json
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fsrs")

from conftest import ROOT  # noqa: E402
from sakshi.retention import bkt  # noqa: E402
from sakshi.retention.bank import bank_from_dict, load_bank  # noqa: E402
from sakshi.retention.bayes import NONE, RANDOM, Diagnosis  # noqa: E402
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
    p = 0.05
    assert bkt.update(p, True) > p
    assert bkt.update(0.3, False) < 0.3
    # an application question is harder to guess, so a right answer is stronger evidence
    assert bkt.update(p, True, application=True) > bkt.update(p, True)
    assert p < bkt.implicit_credit(p) < bkt.update(p, True)
    q = 0.5
    for _ in range(20):
        q = bkt.update(q, True)
    assert 0.95 < q <= 1.0


def test_bkt_guess_floor_is_one_over_the_options():
    # a blind guess on a 3-option question is right 1 time in 3, so a right answer there proves less
    assert bkt.update(0.05, True, application=True, n_options=3) < bkt.update(0.05, True, application=True, n_options=6)


def test_bkt_one_right_answer_is_not_mastery():
    p = 0.3
    for _ in range(10):
        p = bkt.update(p, False, n_options=4)
    one = bkt.update(p, True, n_options=4)
    assert one - p <= bkt.BKTParams().max_step + 1e-9 and one < 0.7  # was 0.23 -> 0.71 before the cap
    assert bkt.update(0.3, True, n_options=4) < 0.7                  # from the prior too
    two = bkt.update(bkt.update(0.3, True, n_options=4), True, n_options=4)
    assert two >= 0.7
    tries = [{"concept": "c", "correct": c} for c in (False, False, True)]
    assert not bkt.mastered(0.99, tries, "c", 0.7)  # high P(L) alone is not enough: needs 2 right answers
    assert bkt.mastered(0.8, tries + [{"concept": "c", "correct": True}], "c", 0.7)


# ---- Bayes --------------------------------------------------------------------------------------------

def test_bayes_names_a_belief_only_after_repeated_consistent_picks(bank):
    d = Diagnosis("C4", bank.concepts["C4"].misconceptions)
    assert RANDOM in d.posterior and NONE in d.posterior
    d.update(bank.questions["Q10"], "B")  # "just how leaves breathe" = C4M1
    assert d.top()[0] == "C4M1" and d.confirmed() is None and d.suspected() is None  # one pick: not sure yet
    d.update(bank.questions["Q11"], "D")  # C4M1 again
    assert d.confirmed() is None and d.top()[1] < 0.8  # two picks could still be a guesser
    d.update(bank.questions["Q12"], "A")  # C4M1 a third time
    assert d.confirmed() == "C4M1" and d.posterior["C4M1"] >= 0.8
    assert abs(sum(d.posterior.values()) - 1) < 1e-9


def test_bayes_random_guessers_are_rarely_named():
    import random
    from sakshi.retention.bank import Option, Question
    rng, named, n = random.Random(0), 0, 4000
    for _ in range(n):
        d = Diagnosis("c", ["m1", "m2", "m3"])
        for i in range(3):
            tags = ["m1", "m2", "m3"]
            rng.shuffle(tags)
            q = Question(f"q{i}", "c", "recall", "s", [Option("A", "a", True)] + [Option(k, k, False, t) for k, t in zip("BCD", tags)])
            d.update(q, rng.choice("ABCD"))
        named += d.confirmed() is not None
    # 3 blind picks landing on one belief's option every time: 3 x (1/4)^3 = 4.7% is the floor any rule that
    # names a belief after 3 consistent picks must accept (inside a real session it measured 3.8% per diagnosis)
    assert named / n < 0.06


def test_bayes_untagged_or_correct_picks_never_raise_a_belief_against_guessing():
    from sakshi.retention.bank import Option, Question
    q = Question("q", "c", "recall", "s", [Option("A", "a", True), Option("B", "b", False, "m1"),
                                           Option("C", "c", False, None), Option("D", "d", False, None)])
    for pick in "ACD":
        d = Diagnosis("c", ["m1", "m2"])
        before = {h: d.posterior[h] / d.posterior[RANDOM] for h in ("m1", "m2")}
        d.update(q, pick)
        for h in ("m1", "m2"):
            assert d.posterior[h] / d.posterior[RANDOM] <= before[h] + 1e-12


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


def test_demo_path_walks_down_and_does_not_overclaim(bank):
    io = ModelStudent(knows={"C1"}, holds={"C2M1", "C4M1"})
    res, state = run(bank, io)
    # 3 questions per concept: 2 picks of a belief is not enough to name it, and one right answer after the
    # explanation is not mastery, so the climb waits for review day instead of claiming success
    assert not res.detected and not res.suspected
    concepts = [bank.questions[q].concept for q in res.asked]
    assert concepts[0] == "C4" and concepts.index("C1") > concepts.index("C2")
    assert res.outcomes["C1"] == "good" and res.outcomes["C4"] == "again"
    assert state.blocked == {"C4": ["C2", "C3"]}


def test_stubborn_believer_is_named(bank):
    io = ModelStudent(knows={"C1", "C2", "C3"}, holds={"C4M1"}, learns_after_feedback=False)
    res, state = run(bank, io)
    assert "C4M1" in res.detected
    text = "\n".join(io.lines)
    assert "Not sure yet which idea is behind this" in text  # abstains after 1-2 picks
    assert 'Misconception detected: "Photosynthesis is just the way plants breathe"' in text  # named after the 3rd
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
    assert due["again"] <= due["hard"] <= due["good"] <= due["easy"]
    # children: 1st revision within a day, 2nd within 3 days, then FSRS decides
    assert datetime.fromisoformat(due["easy"]) <= NOW + timedelta(days=1)
    c2 = review(s, review(s, None, "easy", NOW), "easy", NOW + timedelta(days=1))
    assert datetime.fromisoformat(c2["due"]) <= NOW + timedelta(days=4)
    c3 = review(s, c2, "easy", NOW + timedelta(days=4))
    assert datetime.fromisoformat(c3["due"]) > NOW + timedelta(days=7)
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
