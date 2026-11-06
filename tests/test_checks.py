"""Seeded-fault test: every check must fire on its own bad input and stay quiet on a good one.

A pass rate on its own proves nothing (bible section 10); this is the test that shows the
checks can fail at all.
"""
import pytest

from sakshi.checks import (HARD, WARN, item_assertions, reasons, stem_checks, summary_overall_checks,
                           summary_sentence_checks, tier)

SRC = "In 1999, a town in our district repainted its old iron bridge to protect it."
GOOD_RW = "In 1999, a town repainted its old iron bridge to protect it."
LONG_SRC = "In 1999, a town in our district repainted its old iron bridge to protect it, and workers scraped off the loose rust first."
PASSAGE = (SRC + " Workers scraped off the loose rust with wire brushes. Then they covered the bridge with red primer. "
           "The town checks the bridge every year.")
WITNESS = SRC


def by_name(results):
    return {c.name: c for c in results}


# (check name, results produced from a BAD input)
SUMMARY_FAULTS = [
    ("summary_nonempty", lambda: summary_sentence_checks(SRC, "")),
    ("summary_support", lambda: summary_sentence_checks(SRC, "Scientists in Paris proved a famous experiment about iron.")),
    ("summary_numbers", lambda: summary_sentence_checks(SRC, GOOD_RW.replace("1999", "1989"))),
    ("summary_negation", lambda: summary_sentence_checks(SRC, "In 1999, a town did not repaint its old iron bridge to protect it.")),
    ("summary_new_names", lambda: summary_sentence_checks(SRC, "In 1999, a town in Mysore repainted its old iron bridge to protect it.")),
    ("summary_readability", lambda: summary_sentence_checks(LONG_SRC, LONG_SRC)),
    ("summary_length", lambda: summary_overall_checks("Too short.")),
]

STEM_FAULTS = [
    ("stem_nonempty", lambda: stem_checks("", "bridge", WITNESS, PASSAGE)),
    ("stem_question_mark", lambda: stem_checks("What did the town repaint", "bridge", WITNESS, PASSAGE)),
    ("stem_length", lambda: stem_checks("What did the town in our district repaint in the year that the old iron thing was "
                                        "painted by the workers who came every year to look at it carefully?", "bridge", WITNESS, PASSAGE)),
    ("stem_no_answer_leak", lambda: stem_checks("Why was the bridge repainted?", "bridge", WITNESS, PASSAGE)),
    ("stem_not_echo", lambda: stem_checks(WITNESS.rstrip(".") + "?", "bridge", WITNESS, PASSAGE)),
    ("stem_not_duplicate", lambda: stem_checks("What did the town repaint?", "bridge", WITNESS, PASSAGE,
                                               other_stems=["What did the town repaint?"])),
    ("stem_in_passage", lambda: stem_checks("Which philosopher discussed quantum teleportation?", "bridge", WITNESS, PASSAGE)),
    ("stem_readability", lambda: stem_checks("Which extraordinarily sophisticated infrastructure deteriorates progressively?",
                                             "bridge", "Bridges are old.", PASSAGE)),
]

ITEM_FAULTS = [
    ("key_in_witness", lambda: item_assertions("castle", WITNESS, None)),
    ("options_distinct", lambda: item_assertions("bridge", WITNESS, ["bridge", "gate", "gate", "road"])),
    ("options_one_key", lambda: item_assertions("bridge", WITNESS, ["gate", "road", "tower", "wall"])),
    ("options_not_from_witness", lambda: item_assertions("bridge", WITNESS, ["bridge", "town", "road", "wall"])),
]


@pytest.mark.parametrize("name,make", SUMMARY_FAULTS + STEM_FAULTS + ITEM_FAULTS, ids=lambda x: x if isinstance(x, str) else "")
def test_check_fires_on_its_own_fault(name, make):
    res = by_name(make())
    assert name in res and not res[name].passed, f"{name} did not fire: {res.get(name)}"


def test_good_inputs_pass_every_check():
    good = (summary_sentence_checks(SRC, GOOD_RW)
            + summary_overall_checks(" ".join(["word"] * 40))
            + stem_checks("What did the town repaint?", "bridge", WITNESS, PASSAGE)
            + item_assertions("bridge", WITNESS, ["bridge", "wire", "primer", "year"]))
    assert all(c.passed for c in good), [c for c in good if not c.passed]
    assert tier(good) == "GREEN"


def test_each_fault_fires_only_hard_or_warn_as_designed():
    # severities are part of the design: leak, numbers, negation, support are HARD
    sev = {c.name: c.severity for _, f in SUMMARY_FAULTS + STEM_FAULTS + ITEM_FAULTS for c in f()}
    for hard in ("summary_support", "summary_numbers", "summary_negation", "stem_no_answer_leak",
                 "stem_question_mark", "key_in_witness"):
        assert sev[hard] == HARD
    for warn in ("summary_new_names", "summary_readability", "stem_in_passage", "stem_readability"):
        assert sev[warn] == WARN


def test_tier_mapping():
    red = summary_sentence_checks(SRC, GOOD_RW.replace("1999", "1989"))
    amber = summary_sentence_checks(SRC, "In 1999, a town in Mysore repainted its old iron bridge to protect it.")
    green = summary_sentence_checks(SRC, GOOD_RW)
    assert tier(red) == "RED" and tier(amber) == "AMBER" and tier(green) == "GREEN"
    assert tier(green, detail=True) == "AMBER"  # a detail-only question is AMBER
    assert reasons(red) and not reasons(green)


def test_number_check_normalises_commas():
    ok = summary_sentence_checks("The bridge cost 1,000 coins.", "The bridge cost 1000 coins.")
    assert by_name(ok)["summary_numbers"].passed


def test_negation_contractions():
    res = by_name(summary_sentence_checks("Iron does rust in damp air.", "Iron doesn't rust in damp air."))
    assert not res["summary_negation"].passed
    same = by_name(summary_sentence_checks("Zinc does not rust easily.", "Zinc doesn't rust easily."))
    assert same["summary_negation"].passed
