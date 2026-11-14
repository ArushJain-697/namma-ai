"""BKT-gated climb-up and the review day that follows the misconception graph."""
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fsrs")

from sakshi.retention.bank import bank_from_dict  # noqa: E402
from sakshi.retention.io import ModelStudent  # noqa: E402
from sakshi.retention.review import ReviewSession  # noqa: E402
from sakshi.retention.session import AdaptiveSession, SessionConfig  # noqa: E402
from sakshi.retention.state import LearnerState, MisconceptionState  # noqa: E402

NOW = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)


def q(qid, cid, typ, mis):
    return {"id": qid, "concept": cid, "type": typ, "stem": qid,
            "options": [{"key": "A", "text": "right", "correct": True}] +
                       [{"key": k, "text": f"{qid} {k}", "correct": False, "misconception": m} for k, m in zip("BC", mis)]}


def chain_bank(base_questions=True):
    """top <- base (top builds on base)."""
    qs = [q("t1", "top", "recall", ["tm1", "tm2"]), q("t2", "top", "application", ["tm1", "tm2"]),
          q("t3", "top", "application", ["tm1", "tm2"])]
    if base_questions:
        qs += [q("b1", "base", "recall", ["bm1", "bm2"]), q("b2", "base", "application", ["bm1", "bm2"]),
               q("b3", "base", "application", ["bm1", "bm2"])]
    return bank_from_dict({"title": "t", "concepts": [
        {"id": "top", "name": "Top", "prereqs": ["base"], "misconceptions": [{"id": "tm1", "text": "x"}, {"id": "tm2", "text": "y"}]},
        {"id": "base", "name": "Base", "prereqs": [], "misconceptions": [{"id": "bm1", "text": "x"}, {"id": "bm2", "text": "y"}]}],
        "questions": qs})


def session(bank, student):
    st = LearnerState()
    AdaptiveSession(bank, st, student, SessionConfig(show_summary=False), now=NOW).run()
    return st


def test_climb_stops_when_base_is_shaky():
    st = session(chain_bank(), ModelStudent(learns_after_feedback=False))
    assert st.blocked == {"top": ["base"]}
    assert st.concepts["top"].last_outcome == "again"


def test_climb_continues_when_base_is_learned():
    st = session(chain_bank(), ModelStudent(learns_after_feedback=True))
    assert st.blocked == {}
    assert st.concepts["top"].last_outcome == "hard"
    assert st.concepts["top"].p_mastery >= 0.6  # BKT gate passed


def test_untestable_prerequisite_does_not_block():
    st = session(chain_bank(base_questions=False), ModelStudent(learns_after_feedback=True))
    assert st.blocked == {}


def test_blocked_state_survives_save(tmp_path):
    st = session(chain_bank(), ModelStudent(learns_after_feedback=False))
    st.save(str(tmp_path / "s.json"))
    assert LearnerState.load(str(tmp_path / "s.json")).blocked == {"top": ["base"]}


# ---- review day on the real graph ----------------------------------------------------------------------

@pytest.fixture(scope="module")
def lib():
    from sakshi.misconceptions import Library
    return Library.load()


def held_state(lib, mid):
    st = LearnerState()
    m = lib.by_id[mid]
    st.ensure([m["concept_id"]], 0.3)
    st.misconceptions[mid] = MisconceptionState(m["concept_id"], m["statement"], 0.8, "confirmed", NOW.isoformat())
    return st


def a_probe_belief(lib):
    return next(m["id"] for m in lib.items if (m.get("probe") or {}).get("question") and m.get("fix"))


def test_review_keeps_a_belief_still_held(lib):
    mid = a_probe_belief(lib)
    st = held_state(lib, mid)
    ReviewSession(st, lib, ModelStudent(holds={mid}, learns_after_feedback=False), NOW + timedelta(days=1)).run()
    assert st.misconceptions[mid].status == "still held"
    assert st.misconceptions[mid].p_holds > 0.8
    assert st.concepts[lib.by_id[mid]["concept_id"]].last_outcome == "again"


def test_review_clears_then_follows_the_graph(lib):
    mid = a_probe_belief(lib)
    st = held_state(lib, mid)
    cid = lib.by_id[mid]["concept_id"]
    from sakshi.retention.review import RelatedBeliefs
    rel = RelatedBeliefs(lib)
    related = rel.related(mid, n=6)
    assert related, "every belief has a root, so there is always somewhere to go next"
    student = ModelStudent(knows={cid}, holds=set(related), learns_after_feedback=False)
    r = ReviewSession(st, lib, student, NOW + timedelta(days=1), related=rel).run()
    assert st.misconceptions[mid].status == "cleared"
    found = [m for m, s in st.misconceptions.items() if s.status.startswith("suspected (same root")]
    assert found and found[0] in related
    assert len(r["asked"]) >= 2


def test_forgetting_discounts_mastery(lib):
    from sakshi.retention.fsrs_sched import make_scheduler, review
    st = LearnerState()
    st.ensure(["c"], 0.3)
    st.concepts["c"].p_mastery = 0.9
    st.concepts["c"].fsrs_card = review(make_scheduler(), None, "good", NOW)
    ReviewSession(st, lib, ModelStudent(), NOW + timedelta(days=30), config=None)._forget()
    assert st.concepts["c"].p_mastery < 0.9


def test_streaming_session_grows_question_by_question():
    """Questions arrive one at a time; the session asks each as it arrives and keeps what it learned."""
    full = chain_bank()
    st = LearnerState()
    first = bank_from_dict({"title": "t", "concepts": [{"id": "base", "name": "Base", "prereqs": []}],
                            "questions": [q("b1", "base", "recall", ["bm1", "bm2"])]})
    from sakshi.retention.io import ModelStudent
    sess = AdaptiveSession(first, st, ModelStudent(knows={"base"}), SessionConfig(show_summary=False), now=NOW)
    sess.explore_question("b1")
    assert sess.asked == ["b1"] and sess.outcome["base"] == "good"
    sess.extend(full)  # a new question (on "top") arrives while the child was answering
    sess.explore_question("t1")
    assert sess.asked[:2] == ["b1", "t1"]
    sess.finish_stream()
    assert st.concepts["top"].fsrs_card and st.concepts["base"].fsrs_card
