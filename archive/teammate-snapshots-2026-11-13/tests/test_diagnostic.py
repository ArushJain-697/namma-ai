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


# ---- quiz format v2: the model writes the whole question ------------------------------------------------
import os
import pathlib

from sakshi.backends.stub import StubBackend
from sakshi.diagnostic import (QUIZ_MAX_BELIEFS, build_quiz_messages, check_quiz_item, generate_quiz, parse_quiz_item,
                               quiz_target_json)

ROOT = pathlib.Path(__file__).resolve().parent.parent
KP = ("A sharp knife cuts better than a blunt one because the same force acts on a much smaller area, so the "
      "pressure is greater. A blunt knife spreads the force over a wider area. Heavier knives are not always sharper.")
KEV = ("A sharp knife cuts better than a blunt one because the same force acts on a much smaller area, so the "
       "pressure is greater.")
KGOOD = {"q": "Why does a sharp knife cut better than a blunt one?",
         "options": ["It puts the same force on a smaller area", "It is heavier than a blunt knife",
                     "It is made of a stronger metal", "It moves faster through the food"],
         "answer": 0, "explain": "Same force on a smaller area means more pressure, so the sharp edge cuts easily."}


def test_quiz_prompt_is_shared_short_and_caps_beliefs():
    msgs = build_quiz_messages(KP, KEV, ["b1", "b2", "b3", "b4", "b5"])
    user = msgs[1]["content"]
    assert KEV in user and "- b3" in user and "- b4" not in user and QUIZ_MAX_BELIEFS == 3
    assert "mistakes" not in build_quiz_messages(KP, KEV)[1]["content"]
    rendered = chat_prompt("qwen3", msgs[0]["content"], user)
    assert rendered.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")


def test_quiz_target_round_trips_with_correct_first():
    t = quiz_target_json(KGOOD["q"], KGOOD["options"], KGOOD["explain"])
    assert list(json.loads(t)) == ["q", "options", "answer", "explain"] and json.loads(t)["answer"] == 0
    assert parse_quiz_item("noise " + t + ' trailing {"x": 1}') == KGOOD


def test_quiz_parse_accepts_letter_or_text_answers_and_moves_correct_first():
    shuffled = {**KGOOD, "options": [KGOOD["options"][2], KGOOD["options"][0], KGOOD["options"][1], KGOOD["options"][3]]}
    for a in (1, "B", "b", KGOOD["options"][0]):
        assert parse_quiz_item(json.dumps({**shuffled, "answer": a}))["options"][0] == KGOOD["options"][0]
    assert parse_quiz_item('{"q": "Why {so}?", "options": ["a", "b", "c", "d"], "answer": 0, "explain": "x y z"}')["q"] == "Why {so}?"
    assert parse_quiz_item('{"q": "Why?", "options": ["a", "b"') is None          # cut off: max_new_tokens ran out
    assert parse_quiz_item('{"q": "Why?", "options": ["a", "b", "c", "d"], "answer": 7}') is None
    assert parse_quiz_item("not json") is None


def test_quiz_good_item_passes():
    assert check_quiz_item(KGOOD, KP, KEV).ok, check_quiz_item(KGOOD, KP, KEV).reasons


def qbad(**changes):
    return check_quiz_item({**json.loads(json.dumps(KGOOD)), **changes}, KP, KEV)


def opts_with(i, text):
    o = list(KGOOD["options"])
    o[i] = text
    return o


def test_quiz_checks_catch_each_fault():
    assert not qbad(q="A sharp knife cuts better because the force acts on a smaller ____?").ok   # fill in the blank
    assert not qbad(q="According to the passage, which statement is true?").ok                     # vague
    assert not qbad(q="Which is NOT a reason a sharp knife cuts better?").ok                       # NOT question
    assert not qbad(q="Knife?").ok                                                                 # too short
    assert not qbad(q="Why does a sharp knife cut well").ok                                        # no question mark
    assert not qbad(options=KGOOD["options"][:3]).ok                                               # 3 options
    assert not qbad(options=opts_with(3, "None of the above")).ok                                  # none of the above
    assert not qbad(options=opts_with(2, KGOOD["options"][0])).ok                                  # duplicate
    assert not qbad(options=opts_with(0, "It puts the same force on a much smaller area of the food so pressure rises")).ok  # long
    assert not qbad(options=opts_with(0, "Because it was blessed by a priest")).ok                # not in the passage
    assert not qbad(q="Why does putting the same force on a smaller area help a knife?").ok        # answer leaked
    assert not qbad(explain="").ok                                                                 # no explanation
    assert not check_quiz_item(KGOOD, KP, "This sentence is not in the passage.").ok


def test_all_gold_questions_pass_the_code_checks():
    gold = [json.loads(l) for l in open(ROOT / "data" / "gold_questions.jsonl", encoding="utf-8")]
    assert len(gold) == 20
    for g in gold:
        raw = json.load(open(ROOT / "data" / "dataset" / "raw" / "train" / (g["source_job"] + ".json"), encoding="utf-8"))
        chk = check_quiz_item(g, raw["response"]["passage"], g["evidence"])
        assert chk.ok, (g["id"], chk.reasons)
    from collections import Counter
    per_passage, recall = Counter(g["source_job"] for g in gold), Counter(g["source_job"] for g in gold if g["kind"] == "recall")
    assert all(recall[j] * 4 <= per_passage[j] for j in recall)   # rubric H1: at most 1 in 4 plain recall


def test_sakshi_run_shows_no_fill_in_the_blank(capsys):
    from sakshi.cli import main
    out = ROOT / "results" / "_test_run.json"
    try:
        main(["run", str(ROOT / "data" / "passages" / "rust_ordinary.txt"), "--out", str(out), "--no-library"])
        text = capsys.readouterr().out
        assert "QUIZ" in text and "Why:" in text and "fill-in-the-blank" not in text and "____" not in text
    finally:
        for f in (out, out.with_name("_test_run_metrics.json")):
            if f.exists():
                f.unlink()


def test_generate_quiz_never_falls_back_to_fill_in_the_blank():
    passage = (ROOT / "data" / "passages" / "rust_ordinary.txt").read_text()
    bank, rep = generate_quiz(passage, StubBackend(), None, n_questions=4)
    assert 1 <= len(bank["questions"]) <= 4 and all(q["source"] == "quiz_v2" for q in bank["questions"])
    assert all(sum(o["correct"] for o in q["options"]) == 1 for q in bank["questions"])
    assert rep["calls"] == rep["summary_calls"] + sum(len(r["attempts"]) for r in rep["items"])
    bank, rep = generate_quiz(passage, StubBackend("empty"), None, n_questions=4)
    assert bank["questions"] == [] and "cloze" not in json.dumps(bank)


def test_old_generate_bank_cloze_top_up_is_off_by_default():
    import inspect
    from sakshi.diagnostic import generate_bank
    assert inspect.signature(generate_bank).parameters["cloze"].default is False


def test_quiz_checks_keep_maths_symbols_and_word_order_distinct():
    base = {"q": "Ravi has n marbles and then gets 5 more. Which shows his total?", "answer": 0,
            "explain": "Getting 5 more means adding 5 to n."}
    p = "Ravi has n marbles. Then he gets 5 more marbles, so we add 5 to n to find his total."
    ev = "Then he gets 5 more marbles, so we add 5 to n to find his total."
    assert check_quiz_item({**base, "options": ["n + 5", "5n", "n − 5", "n + 5 = 10"]}, p, ev).ok
    swap = {**KGOOD, "options": ["Priya has a sprain and Aman a strain", "Priya has a strain and Aman a sprain",
                                 "Both have a strain", "Both have a sprain"]}
    assert "says the same" not in " ".join(check_quiz_item(swap, KP, KEV).reasons)
    assert not qbad(options=opts_with(1, "It puts the same force on the smaller area")).ok   # same words, same order
