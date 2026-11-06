import json

import pytest
from cf_fixtures import P1, cases
from sakshi.backends.stub import StubBackend
from sakshi.baseline import parse_qa, run_baseline, touches, BaselineItem
from sakshi.cf_eval import classify, evaluate, trap_check, wilson, write_d_sheet
from sakshi.counterfactual import Case, load_cases, notes, planted_term, validate, value_matches

C = {c.id: c for c in cases()}


def test_value_matches_units_and_whole_numbers():
    assert value_matches("It boiled at 90°C today", "90 degrees Celsius")
    assert value_matches("90", "90 degrees Celsius") and value_matches("about 1,000 coins", "1000")
    assert not value_matches("1000", "100")  # whole numbers only
    assert not value_matches("100", "90 degrees Celsius")
    assert value_matches("the month of Magha", "Magha") and not value_matches("Maghalaya", "Magha")


def test_planted_term_and_validation():
    assert planted_term(C["boil"]) == "90" and planted_term(C["fair"]) == "Magha" and planted_term(C["bridge"]) == "1887"
    for c in C.values():
        assert validate(c, allow_short=True) == []
    assert "Rejected" not in "".join(validate(C["boil"], allow_short=True))
    assert any("REJECTED" in p for p in validate(C["boil"]))  # too short for the real gate


@pytest.mark.parametrize("change,expect", [
    (dict(passage_value="95 degrees"), "not in the planted sentence"),
    (dict(memory_value="90 degrees Celsius"), "memory_value"),
    (dict(sentence_idx=99), "out of range"),
    (dict(split="test"), "split must be"),
    (dict(type="color"), "type must be"),
])
def test_validation_catches_bad_cases(change, expect):
    base = dict(id="x", passage=P1, sentence_idx=1, passage_value="90 degrees Celsius", memory_value="100 degrees Celsius",
                type="number", split="dev")
    base.update(change)
    assert any(expect in p for p in validate(Case(**base), allow_short=True))


def test_notes_flag_memory_value_elsewhere():
    c = Case("x", P1 + " Water usually boils at 100 degrees.", 1, "90 degrees Celsius", "100 degrees Celsius", "number", "dev")
    assert notes(c) and not notes(C["boil"])


def test_load_cases_from_disk(tmp_path):
    (tmp_path / "a.txt").write_text(P1)
    (tmp_path / "a.json").write_text(json.dumps({"planted": {"sentence_idx": 1, "passage_value": "90 degrees Celsius",
                                                              "memory_value": "100 degrees Celsius", "type": "number"}, "split": "heldout"}))
    (tmp_path / "_template.json").write_text("{}")
    got = load_cases(str(tmp_path))
    assert [c.id for c in got] == ["a"] and got[0].split == "heldout" and load_cases(str(tmp_path), "dev") == []
    (tmp_path / "b.json").write_text(json.dumps({"planted": {"sentence_idx": 0, "passage_value": "x", "memory_value": "y"}}))
    with pytest.raises(FileNotFoundError):
        load_cases(str(tmp_path))


def test_parse_qa_is_forgiving_and_never_invents():
    items = parse_qa("Question: What is it?\nAnswer: Magha\nSupport: The fair is in Magha.\nQuestion: Next?\nAnswer: yes\n")
    assert len(items) == 2 and items[0].support == "The fair is in Magha." and items[1].support is None
    assert parse_qa("I think the answer is 90.") == [] and parse_qa("") == [] and parse_qa(None) == []
    assert parse_qa("Question: no answer here") == []


def test_touches():
    s = "At the hill station the water boiled at 90 degrees Celsius."
    assert touches(BaselineItem("What did the water do at the hill station?", "boiled at 90"), s)
    assert not touches(BaselineItem("Who is mentioned?", "students"), s)


def test_baseline_modes_run_and_grounded_includes_support():
    b = StubBackend(baseline="memory")
    extra = {"passage_value": "90 degrees Celsius", "memory_value": "100 degrees Celsius"}
    sent = C["boil"].sentence
    t, _ = run_baseline(b, P1, "targeted", sent, extra)
    g, _ = run_baseline(b, P1, "grounded", sent, extra)
    f, _ = run_baseline(b, P1, "free", sent, extra)
    assert t[0].answer == "100 degrees Celsius" and g[0].support == sent and len(f) == 3
    with pytest.raises(ValueError):
        run_baseline(b, P1, "bogus")


def test_classify():
    c = C["boil"]
    assert classify("100", c) == "memory" and classify("90 degrees", c) == "passage" and classify("", c) == "empty"
    assert classify("somewhere", c) == "other" and classify("90 or 100", c) == "both"


def test_wilson_interval_is_wide_for_small_n():
    assert wilson(0, 0) is None
    lo, hi = wilson(3, 3)
    assert lo < 0.7 and hi == 1.0  # 3 of 3 is NOT "100% certain"
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and 0.2 < hi < 0.35


def test_trap_check_with_memory_and_passage_baselines():
    dev = [c for c in cases() if c.split == "dev"]
    mem = trap_check(dev, StubBackend(baseline="memory"))
    assert all(v["trap"] for v in mem.values()) and all(len(v["tries"]) == 3 for v in mem.values())
    pas = trap_check(dev, StubBackend(baseline="passage"))
    assert not any(v["trap"] for v in pas.values())


def test_evaluate_memory_baseline_vs_sakshi():
    m = evaluate(cases(), StubBackend(baseline="memory"), StubBackend(), gate_override=True)
    dev, held = m["splits"]["dev"], m["splits"]["heldout"]
    assert dev["A_targeted"]["memory_rate"] == 1.0 and dev["A_targeted"]["n"] == 2 and held["A_targeted"]["n"] == 1
    assert dev["A_grounded"]["memory_rate"] == 1.0  # the stub ignores the grounding instruction by design
    assert dev["B_sakshi_key"]["passage_rate"] == 1.0 and held["B_sakshi_key"]["passage_rate"] == 1.0
    assert dev["A_free"]["coverage"]["rate"] == 1.0
    assert "NOT" in m["caveat"] and "guarantee of the design" in m["caveat"]
    # the planted memory values are absent from these passages, so a plain span check would catch every one
    assert dev["A_span_check"]["released_by_a_plain_span_check"] == 0 and dev["A_span_check"]["memory_answers"] == 2


def test_evaluate_passage_baseline_has_no_effect():
    m = evaluate(cases(), StubBackend(baseline="passage"), StubBackend(), gate_override=True)
    assert m["splits"]["dev"]["A_targeted"]["memory_rate"] == 0.0 and m["splits"]["dev"]["A_targeted"]["counts"]["passage"] == 2


def test_free_form_coverage_is_reported_when_baseline_does_not_touch_the_sentence():
    b = StubBackend(baseline="memory", free_covers=False)
    m = evaluate(cases(), b, StubBackend(), gate_override=True)
    assert m["splits"]["dev"]["A_free"]["coverage"]["rate"] == 0.0 and m["splits"]["dev"]["A_free"]["n"] == 0


def test_summary_leak_is_measured():
    leak = evaluate(cases(), StubBackend(baseline="memory", summary_leak=True), StubBackend(), gate_override=True)
    assert leak["splits"]["dev"]["C_whole_summary_has_memory_value"]["memory_rate"] == 1.0
    assert leak["splits"]["dev"]["C_sakshi_summary_has_memory_value"]["memory_rate"] == 0.0  # witnessed summary cannot add it
    clean = evaluate(cases(), StubBackend(baseline="memory"), StubBackend(), gate_override=True)
    assert clean["splits"]["dev"]["C_whole_summary_has_memory_value"]["memory_rate"] == 0.0


def test_dev_filter_applies_to_dev_only_and_heldout_is_never_filtered():
    m = evaluate(cases(), StubBackend(baseline="memory"), StubBackend(), kept_dev={"boil"}, gate_override=True)
    assert m["splits"]["dev"]["n_total"] == 2 and m["splits"]["dev"]["n_scored"] == 1
    assert m["splits"]["dev"]["filtered_to_trapping_facts"] is True
    assert m["splits"]["heldout"]["n_scored"] == 1 and m["splits"]["heldout"]["filtered_to_trapping_facts"] is False
    assert "never filtered" in m["filter"]


def test_d_sheet_written(tmp_path):
    m = evaluate(cases(), StubBackend(), StubBackend(), gate_override=True)
    n = write_d_sheet(m, str(tmp_path / "d.csv"))
    text = (tmp_path / "d.csv").read_text()
    assert n == 3 and "sensible / awkward" in text and "boil" in text
