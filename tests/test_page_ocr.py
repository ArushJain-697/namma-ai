"""Text assembly after OCR (pi/ui/page_ocr.py): no OCR model needed."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pi" / "ui"))
import page_ocr  # noqa: E402


def box(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def res(rows):
    return SimpleNamespace(boxes=[box(*b) for b, _, _ in rows], txts=[t for _, t, _ in rows],
                           scores=[s for _, _, s in rows])


def test_hyphenated_word_across_lines_is_joined():
    lines = ["The Sundarbans lie in the delta formed by the Ganga, the Brahma-", "putra and the Meghna rivers."]
    assert page_ocr.join_lines(lines) == ("The Sundarbans lie in the delta formed by the Ganga, the Brahmaputra "
                                          "and the Meghna rivers.")


def test_real_dash_before_a_capital_or_number_is_kept():
    assert page_ocr.join_lines(["from 1857 -", "1858 the"]) == "from 1857 - 1858 the"
    assert page_ocr.join_lines(["North-", "East India"]) == "North- East India"


def test_chinese_punctuation_from_blurry_english_maps_to_ascii():
    assert page_ocr.clean_line("Friction is a force，it acts against motion。") == \
        "Friction is a force,it acts against motion."
    assert page_ocr.clean_line("roots（called pneumatophores）") == "roots(called pneumatophores)"


def test_stray_non_latin_characters_are_dropped():
    assert page_ocr.clean_line("the 水 tiger swims") == "the tiger swims"


def test_boxes_are_read_in_line_order_even_when_shuffled_and_split():
    r = res([
        ((0, 40, 90, 60), "second line", 0.95),
        ((300, 0, 400, 20), "end.", 0.95),
        ((0, 1, 290, 21), "First line goes to the", 0.97),
        ((0, 80, 200, 100), "third line", 0.95),
    ])
    assert page_ocr.assemble(r) == "First line goes to the end. second line third line"


def test_low_confidence_and_tiny_fragments_are_dropped():
    r = res([((0, 0, 300, 20), "Plants make food in leaves.", 0.97),
             ((0, 30, 300, 50), "xq7 lkj", 0.31),          # unreadable smudge
             ((310, 0, 320, 20), "|", 0.70)])               # page edge read as a bar
    assert page_ocr.assemble(r) == "Plants make food in leaves."


def test_a_looping_generation_is_cut():
    loop = "the roots take in air " * 5
    assert page_ocr.drop_repeats("Mangroves grow in salt water. " + loop) == \
        "Mangroves grow in salt water. the roots take in air"
    once = "Ordinary plants cannot survive in such salty, muddy soil."
    assert page_ocr.drop_repeats(once) == once


def test_text_region_pads_and_clips_to_the_frame():
    r = res([((100, 50, 900, 80), "a line", 0.9), ((100, 400, 700, 430), "another", 0.9)])
    assert page_ocr.text_region(r, (1080, 1920, 3)) == (42, 17, 957, 462)
    assert page_ocr.text_region(res([]), (1080, 1920, 3)) is None


def test_read_page_uses_the_vlm_only_when_the_line_model_is_weak():
    good = res([((0, i * 30, 900, i * 30 + 20), "word " * 12, 0.97) for i in range(12)])   # 144 words
    bad = res([((0, 0, 900, 20), "wrd smdge frction is a frce that acts btween two srfaces", 0.82)])
    illegible = res([((0, 0, 900, 20), "wrd smdge", 0.62)])

    class VL:
        calls = 0

        def read(self, frame, box=None):
            VL.calls += 1
            return "Friction is a force that acts be-\ntween two surfaces that touch each other."

    frame = SimpleNamespace(shape=(1080, 1920, 3))
    text, info = page_ocr.read_page(lambda f: good, frame, VL())
    assert VL.calls == 0 and info["words"] == 144
    text, info = page_ocr.read_page(lambda f: bad, frame, VL())
    assert VL.calls == 1 and info["used"] == "vl" and text == "Friction is a force that acts between two surfaces that touch each other."
    text, info = page_ocr.read_page(lambda f: bad, frame, None)          # no VLM installed: line text stays
    assert text.startswith("wrd smdge frction")
    # too little legible text: the VLM would invent a passage, so it is not asked (the engine asks for a retake)
    text, info = page_ocr.read_page(lambda f: illegible, frame, VL())
    assert VL.calls == 1 and info["too_unclear"] and text == "wrd smdge"


def test_empty_result():
    assert page_ocr.assemble(SimpleNamespace(boxes=None, txts=None, scores=None)) == ""


def test_sharpest_frame_is_picked():
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    rng = np.random.default_rng(0)
    sharp = (rng.random((360, 640)) > 0.5).astype(np.uint8) * 255
    frames = [cv2.GaussianBlur(sharp, (0, 0), s) for s in (3.0, 0.1, 1.5)]
    best, val, vals = page_ocr.pick_sharpest(frames)
    assert vals.index(val) == 1 and best is frames[1]
