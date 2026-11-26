"""Turn camera frames of a textbook page into clean passage text (runs in the UI process on the Pi).

Three steps, each measured in scripts/ocr_bench.py and docs/JUDGE_BRIEF.md ("Camera + OCR"):

1. pick_sharpest: the camera streams frames; take the sharpest of the last few instead of whichever frame was
   current when the button was pressed (a hand-held page shakes, and the press itself shakes the device).
   Sharpness = variance of the Laplacian (Pech-Pacheco et al. 2000), the standard focus measure.
2. The OCR model reads text lines (PP-OCRv6 via RapidOCR; boxes + text + confidence per line).
3. assemble: lines are put back in reading order, a word split across two lines with a hyphen is joined
   ("Brahma-" + "putra" -> "Brahmaputra"), Chinese punctuation the multilingual model sometimes emits on blurry
   English is mapped back to ASCII, stray non-Latin characters and low-confidence fragments are dropped.

No model is imported here, so this file loads instantly and is unit-tested without the OCR models.
"""
from __future__ import annotations

import re
import unicodedata

# Full-width / CJK punctuation the Chinese+English recogniser can output for English text -> ASCII.
_PUNCT = str.maketrans({"。": ".", "，": ",", "、": ",", "：": ":", "；": ";", "！": "!", "？": "?", "（": "(",
                        "）": ")", "【": "[", "】": "]", "「": '"', "」": '"', "『": '"', "』": '"', "《": '"',
                        "》": '"', "·": ".", "‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                        "−": "-", "…": "..."})
# Anything outside Latin letters, digits, common punctuation and spaces is dropped (an English textbook page).
_KEEP = re.compile(r"[^A-Za-z0-9À-ɏ\s.,;:!?'\"()\[\]%&/+=<>°*#@$-]")


def clean_line(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").translate(_PUNCT)
    s = _KEEP.sub("", s)
    return " ".join(s.split())


def sharpness(frame) -> float:
    """Variance of the Laplacian on a grey, downscaled centre crop. Higher = sharper. Comparable between frames
    of the same scene only (it also grows with contrast and the amount of text in view)."""
    import cv2
    g = frame if frame.ndim == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = g.shape[:2]
    g = g[h // 8: h - h // 8, w // 8: w - w // 8]
    if g.shape[1] > 960:
        g = cv2.resize(g, (960, int(g.shape[0] * 960 / g.shape[1])), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def pick_sharpest(frames):
    """Return (frame, its sharpness, all sharpness values) for a non-empty list of frames."""
    vals = [sharpness(f) for f in frames]
    i = max(range(len(frames)), key=vals.__getitem__)
    return frames[i], vals[i], vals


def _lines(items):
    """Group OCR boxes into text lines by vertical overlap, each line left to right, lines top to bottom."""
    items = sorted(items, key=lambda it: it["yc"])
    lines = []
    for it in items:
        for ln in lines:
            # same line if the vertical centres are within half a line height of each other
            if abs(ln["yc"] - it["yc"]) < 0.5 * max(ln["h"], it["h"]) and not any(
                    it["x0"] < o["x1"] - 2 and o["x0"] < it["x1"] - 2 for o in ln["items"]):
                ln["items"].append(it)
                n = len(ln["items"])
                ln["yc"] += (it["yc"] - ln["yc"]) / n
                ln["h"] = max(ln["h"], it["h"])
                break
        else:
            lines.append({"yc": it["yc"], "h": it["h"], "items": [it]})
    lines.sort(key=lambda ln: ln["yc"])
    return [" ".join(o["t"] for o in sorted(ln["items"], key=lambda o: o["x0"])) for ln in lines]


def join_lines(lines) -> str:
    """Join text lines into running text, re-joining words hyphenated across a line break."""
    out = ""
    for ln in lines:
        if not ln:
            continue
        if out.endswith("-") and len(out) > 1 and out[-2].isalpha() and ln[:1].islower():
            out = out[:-1] + ln          # "Brahma-" + "putra ..." -> "Brahmaputra ..."
        else:
            out = f"{out} {ln}" if out else ln
    return " ".join(out.split())


def assemble(res, min_score: float = 0.6, min_chars: int = 2) -> str:
    """RapidOCR output (boxes, txts, scores) -> passage text."""
    boxes = getattr(res, "boxes", None)
    txts, scores = getattr(res, "txts", None) or (), getattr(res, "scores", None) or ()
    if boxes is None or not len(txts):
        return ""
    items = []
    for b, t, s in zip(boxes, txts, scores):
        t = clean_line(t)
        # a short fragment is only kept when the model is confident (stray marks, page edges, the desk)
        if not t or s < min_score or (len(t) < min_chars and s < 0.9):
            continue
        ys = [p[1] for p in b]
        xs = [p[0] for p in b]
        items.append({"x0": min(xs), "x1": max(xs), "yc": sum(ys) / len(ys), "h": max(ys) - min(ys), "t": t})
    return join_lines(_lines(items))


def text_region(res, shape, margin: float = 0.03):
    """Bounding box (x0, y0, x1, y1) of every detected text line, padded, or None. Detection survives blur much
    better than recognition, so this finds the passage even when the line model cannot read it."""
    boxes = getattr(res, "boxes", None)
    if boxes is None or not len(boxes):
        return None
    xs = [p[0] for b in boxes for p in b]
    ys = [p[1] for b in boxes for p in b]
    h, w = shape[:2]
    mx, my = margin * w, margin * h
    x0, y0 = max(0, int(min(xs) - mx)), max(0, int(min(ys) - my))
    x1, y1 = min(w, int(max(xs) + mx)), min(h, int(max(ys) + my))
    return (x0, y0, x1, y1) if x1 - x0 > 32 and y1 - y0 > 32 else None


def drop_repeats(text: str, n: int = 6, times: int = 3) -> str:
    """Cut a generated text where a run of n words starts repeating (a VLM can loop on a very blurry photo)."""
    w = text.split()
    seen: dict = {}
    for i in range(len(w) - n + 1):
        k = tuple(x.lower() for x in w[i:i + n])
        seen.setdefault(k, []).append(i)
        if len(seen[k]) >= times:
            return " ".join(w[:seen[k][1]])
    return text


def mean_confidence(res) -> float:
    sc = list(getattr(res, "scores", None) or ())
    return sum(sc) / len(sc) if sc else 0.0


# Set from scripts/ocr_bench.py (docs/JUDGE_BRIEF.md, "Camera + OCR"):
#  * a read is weak (re-read with the VLM) below VL_MIN_CONF mean confidence or VL_MIN_WORDS words: at 0.90-0.95 the
#    line model still gets 7-13% of words wrong, the VLM 0-1%;
#  * the VLM is NOT used when the line model saw fewer than VL_MIN_SEEN words: on photos that illegible the VLM
#    writes fluent text that is not on the page (5-84% words wrong, "In 1990 ... Dilatton Goodwill"), so asking for
#    a closer photo is the honest answer.
VL_MIN_WORDS, VL_MIN_CONF, VL_MIN_SEEN = 120, 0.95, 10


def read_page(engine, frame, vl=None, mode: str = "auto", on_phase=None):
    """The device's whole read: line model -> assemble; if that looks weak and a VLM server is given, re-read the
    text region with it. mode: auto | always | off. Returns (text, info dict for the run log)."""
    import time
    info, text, res, t0 = {}, "", None, time.time()
    if engine is not None:
        res = engine(frame)
        text = assemble(res)
        info.update(s=round(time.time() - t0, 2), words=len(text.split()), conf=round(mean_confidence(res), 3))
    weak = info.get("words", 0) < VL_MIN_WORDS or info.get("conf", 0) < VL_MIN_CONF
    if mode == "auto" and weak and info.get("words", 0) < VL_MIN_SEEN:
        info["too_unclear"] = True       # the VLM would be guessing: keep the (short) line text, ask for a retake
    elif vl is not None and (mode == "always" or (mode == "auto" and weak)):
        if on_phase:
            on_phase("careful")
        t1 = time.time()
        box = text_region(res, frame.shape) if res is not None else None
        try:
            raw = vl.read(frame, box=box)
            vtext = drop_repeats(join_lines([clean_line(l) for l in raw.splitlines()]))
            info.update(vl_s=round(time.time() - t1, 2), vl_words=len(vtext.split()), crop=box)
            # keep the line model's text if the VLM returned much less (it gave up or was cut off)
            if len(vtext.split()) >= 0.8 * len(text.split()):
                text, info["used"] = vtext, "vl"
        except Exception as e:  # noqa: BLE001
            info["vl_error"] = str(e)[:200]
    return text, info
