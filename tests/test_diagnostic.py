"""Diagnostic question format: the shared prompt, the parser, the checks and bank assembly."""
import json
import random

from sakshi.backends.base import chat_prompt
from sakshi.diagnostic import (LABELS, assemble_question, build_messages, check_item, parse_item, target_json)

P = ("Plants make their own food by photosynthesis. It happens mainly in the leaves, where chlorophyll traps "
     "sunlight. Roots take in water and minerals from the soil, but the soil does not give the plant ready-made food.")
EV = "It happens mainly in the leaves, where chlorophyll traps sunlight."
GOOD = {"answer": "in the leaves", "stem": "Where does photosynthesis mainly take place?",
        "options": [{"b": "B1", "why": "thinks food comes from soil", "text": "in the soil around roots"},
                    {"b": "B3", "why": "thinks roots eat", "text": "inside the roots"},
                    {"b": "B2", "why": "confuses storage", "text": "inside the seeds"}]}


def test_prompt_is_identical_for_training_and_device():
    msgs = build_messages(P, EV, ["a", "b", "c"])
    assert msgs[0]["role"] == "system" and "B3: c" in msgs[1]["content"] and EV in msgs[1]["content"]
    rendered = chat_prompt("qwen3", msgs[0]["content"], msgs[1]["content"])
    assert rendered.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")


def test_target_json_round_trips_and_keeps_field_order():
    t = target_json(GOOD["answer"], GOOD["stem"], GOOD["options"])
    assert list(json.loads(t)) == ["answer", "stem", "options"]
    assert list(json.loads(t)["options"][0]) == ["b", "why", "text"]
    assert parse_item("noise " + t + " trailing") == GOOD


def test_parse_is_tolerant_but_strict_about_keys():
    assert parse_item('{"answer": "x", "stem": "y?", "options": [{"b":"B1","why":"","text":"z"},]}')["answer"] == "x"
    assert parse_item("not json") is None
    assert parse_item('{"answer": "x"}') is None


def test_good_item_passes():
    assert check_item(GOOD, P, EV, 3).ok


def bad(**changes):
    item = json.loads(json.dumps(GOOD))
    item.update(changes)
    return check_item(item, P, EV, 3)


def test_checks_catch_each_fault():
    assert not bad(answer="in the roots").ok                                   # answer not from evidence
    assert not bad(stem="Where in the leaves does it happen?").ok             # answer leaks into the stem
    assert not bad(stem="Leaves").ok                                           # not a question
    assert not bad(options=GOOD["options"][:2]).ok                             # only 2 wrong options
    o = json.loads(json.dumps(GOOD["options"]))
    o[1]["b"] = "B1"
    assert not bad(options=o).ok                                               # same belief twice
    o = json.loads(json.dumps(GOOD["options"]))
    o[0]["text"] = "in the leaves"
    assert not bad(options=o).ok                                               # wrong option equals the answer
    o = json.loads(json.dumps(GOOD["options"]))
    o[2]["b"] = "B5"
    assert not check_item({**GOOD, "options": o}, P, EV, 3).ok                 # label outside the menu


def test_assemble_maps_labels_to_misconception_ids_and_shuffles():
    menu = [{"id": f"M{i}", "statement": f"belief {i}", "fix": f"fix {i}", "concept_id": "C1"} for i in range(3)]
    q = assemble_question("Q1", GOOD, menu, EV, random.Random(1))
    assert [o["key"] for o in q["options"]] == list("ABCD")
    assert sum(o["correct"] for o in q["options"]) == 1
    wrong = {o["text"]: o["misconception"] for o in q["options"] if not o["correct"]}
    assert wrong["in the soil around roots"] == "M0" and wrong["inside the seeds"] == "M1"
    assert all(o["feedback"].startswith("fix") for o in q["options"] if not o["correct"])
    assert LABELS[0] == "B1"
