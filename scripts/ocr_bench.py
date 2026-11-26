#!/usr/bin/env python3
"""OCR benchmark on simulated webcam photos of textbook passages.

    python scripts/ocr_bench.py make  OUT_DIR [--n 6]          render pages + "photograph" them
    python scripts/ocr_bench.py run   OUT_DIR --method NAME    OCR every photo, score against the passage
    python scripts/ocr_bench.py table OUT_DIR                  one table of all methods run so far

Why simulated: the device's camera was not available on the day this was written. The photos are made from the 40
frozen eval passages (data/passages/eval/passages.jsonl): the passage is typeset like a textbook page (serif, 11 pt),
then turned into a 1920x1080 webcam frame with a tilted perspective, uneven light, lower contrast, lens blur, sensor
noise and MJPG compression. Three framings x four blur levels:

    framing  page     the whole A4 page fills the frame height (what the device used to ask for: ~3.3 px per mm)
             half     camera at about half that distance (~5.5 px per mm)
             passage  the passage block fills the frame (~9 px per mm)
    blur     0 sharp, 1 soft (defocus radius 1.5 px), 2 blurry (2.5 px), 3 very blurry (3.5 px)

Scores: CER (character edit distance / passage length, case and punctuation kept) and WER (word edit distance on
lower-cased words, punctuation dropped). The text the quiz model receives is what matters, so both are measured on the
final string each method hands to the engine.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pi" / "ui"))

PASSAGES = ROOT / "data" / "passages" / "eval" / "passages.jsonl"
FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FW, FH = 1920, 1080
FRAMINGS = ("page", "half", "passage")
BLURS = {0: 0.0, 1: 1.5, 2: 2.5, 3: 3.5}
PICK = ["phy_friction", "chem_acids", "bio_pitcher", "his_dandi", "geo_monsoon", "civ_panchayat",
        "phy_sound", "eco_money"]


# --------------------------------------------------------------------------------------------- rendering
def _paragraphs(text: str) -> list[str]:
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    cut = max(1, len(sents) // 2)
    return [" ".join(sents[:cut]), " ".join(sents[cut:])]


def render_page(text: str, rng: random.Random, px_mm: float = 10.0, pt: float = 11.0):
    """Typeset the passage on an A4 page. Returns (RGB page array, passage block box x0, y0, x1, y1)."""
    from PIL import Image, ImageDraw, ImageFont
    pw, ph = int(210 * px_mm), int(297 * px_mm)
    em = pt * 0.3528 * px_mm
    font = ImageFont.truetype(FONT, int(round(em)))
    page = Image.new("RGB", (pw, ph), (250, 247, 238))
    d = ImageDraw.Draw(page)
    left, right = 22 * px_mm, pw - 22 * px_mm
    y = (40 + rng.uniform(0, 60)) * px_mm
    y0, lh, indent = y, em * 1.42, 6 * px_mm
    for para in _paragraphs(text):
        words, line, x_start = para.split(), [], left + indent
        for w in words + [None]:
            trial = " ".join(line + [w]) if w else None
            if w and d.textlength(trial, font=font) <= right - x_start:
                line.append(w)
                continue
            d.text((x_start, y), " ".join(line), font=font, fill=(28, 28, 30))
            y += lh
            line, x_start = ([w] if w else []), left
        y += em * 0.5
    return np.array(page), (left, y0, right, y)


def _disk(r: float) -> np.ndarray:
    k = int(math.ceil(r))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    m = ((xx ** 2 + yy ** 2) <= r * r).astype(np.float32)
    return m / m.sum()


def photograph(page: np.ndarray, box, framing: str, blur_r: float, rng: random.Random) -> np.ndarray:
    """Page array -> a BGR 1920x1080 webcam frame."""
    import cv2
    ph, pw = page.shape[:2]
    bx0, by0, bx1, by1 = box
    if framing == "page":
        s = 0.92 * FH / ph
        cx, cy = pw / 2, ph / 2
    elif framing == "passage":
        bw, bh = (bx1 - bx0) + 160, (by1 - by0) + 160
        s = min(0.95 * FW / bw, 0.95 * FH / bh)
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    else:
        s = math.sqrt((0.92 * FH / ph) * min(0.95 * FW / ((bx1 - bx0) + 160), 0.95 * FH / ((by1 - by0) + 160)))
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    small = cv2.resize(page, (int(pw * s), int(ph * s)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    # where the page corners land in the frame: centred on the region of interest, tilted and rotated a little
    ox, oy = FW / 2 - cx * s, FH / 2 - cy * s
    src = np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]])
    ang = math.radians(rng.uniform(-3, 3))
    ca, sa = math.cos(ang), math.sin(ang)
    dst = []
    for x, y in src:
        x, y = x + ox - FW / 2, y + oy - FH / 2
        x, y = x * ca - y * sa + FW / 2, x * sa + y * ca + FH / 2
        dst.append([x + rng.uniform(-0.02, 0.02) * FW, y + rng.uniform(-0.02, 0.02) * FH])
    M = cv2.getPerspectiveTransform(src, np.float32(dst))
    bg = np.empty((FH, FW, 3), np.float32)
    bg[:] = (rng.uniform(70, 110), rng.uniform(95, 125), rng.uniform(125, 160))  # a desk, RGB
    noise = cv2.resize(np.float32(np.random.default_rng(rng.randrange(1 << 30)).normal(0, 18, (9, 16))), (FW, FH))
    bg += noise[..., None]
    warped = cv2.warpPerspective(small.astype(np.float32), M, (FW, FH), flags=cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.ones((sh, sw), np.float32), M, (FW, FH), flags=cv2.INTER_LINEAR)[..., None]
    img = warped * mask + bg * (1 - mask)
    # uneven light: a gradient from one side plus a vignette, and a duller contrast than print
    gx, gy = np.meshgrid(np.linspace(-1, 1, FW), np.linspace(-1, 1, FH))
    a = rng.uniform(0, 2 * math.pi)
    light = 0.86 + 0.12 * (gx * math.cos(a) + gy * math.sin(a)) - 0.10 * (gx ** 2 + gy ** 2) / 2
    img = (img * 0.82 + 22) * light[..., None]
    img = cv2.GaussianBlur(img, (0, 0), 0.6)                       # every cheap lens is a little soft
    if blur_r > 0:
        img = cv2.filter2D(img, -1, _disk(blur_r))
    nrng = np.random.default_rng(rng.randrange(1 << 30))
    img = img + nrng.normal(0, 5.0, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)[..., ::-1]          # RGB -> BGR, like OpenCV's camera frames
    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])  # the camera streams MJPG
    return cv2.imdecode(jpg, cv2.IMREAD_COLOR)


def make(out: Path, n: int, seed: int = 7):
    import cv2
    rows = {json.loads(l)["id"]: json.loads(l) for l in PASSAGES.open()}
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    meta = []
    for pid in PICK[:n]:
        page, box = render_page(rows[pid]["text"], rng)
        for framing in FRAMINGS:
            for lvl, r in BLURS.items():
                name = f"{pid}__{framing}__b{lvl}.jpg"
                cv2.imwrite(str(out / name), photograph(page, box, framing, r, rng), [cv2.IMWRITE_JPEG_QUALITY, 95])
                meta.append({"file": name, "id": pid, "framing": framing, "blur": lvl, "text": rows[pid]["text"]})
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"{len(meta)} photos in {out}")


# --------------------------------------------------------------------------------------------- scoring
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"}))
    return " ".join(s.split())


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:['-][a-z0-9]+)*", _norm(s).lower())


def score(hyp: str, ref: str) -> dict:
    from rapidfuzz.distance import Levenshtein
    h, r = _norm(hyp), _norm(ref)
    hw, rw = _words(hyp), _words(ref)
    return {"cer": Levenshtein.distance(h, r) / max(1, len(r)), "wer": Levenshtein.distance(hw, rw) / max(1, len(rw))}


# --------------------------------------------------------------------------------------------- methods
def _rapid(det: str, rec: str, ver: str, lang_rec: str | None = None, threads: int = 4, **params):
    from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
    p = {"Det.ocr_version": OCRVersion(ver), "Rec.ocr_version": OCRVersion(ver),
         "Det.model_type": ModelType(det), "Rec.model_type": ModelType(rec),
         "EngineConfig.onnxruntime.intra_op_num_threads": threads, "Global.log_level": "error"}
    if lang_rec:
        p["Rec.lang_type"] = LangRec(lang_rec)
    p.update(params)
    return RapidOCR(params=p)


def method(name: str):
    """name -> callable(BGR frame) -> text. 'raw' = what the device does today (join the lines with spaces)."""
    import page_ocr
    if name == "vl":                         # the VLM on the whole frame
        from paddle_vl import read_page_vl  # pi/ui/paddle_vl.py (llama.cpp server)
        return lambda f: read_page_vl(f)
    if name.startswith(("hyb_", "vlc_")):   # the device pipeline: hyb_v6m = line model, VLM only when weak
        import paddle_vl                     # vlc_v6m = always the VLM, on the text region the line model found
        kind, fast = name.split("_", 1)
        eng, vl = method(fast + "+eng"), paddle_vl.VLServer()

        def read(f):
            text, info = page_ocr.read_page(eng, f, vl, "always" if kind == "vlc" else "auto")
            return text, {k: v for k, v in info.items() if k != "crop"}
        return read
    family, _, post = name.partition("+")
    cfg = {
        "v5m": ("mobile", "mobile", "PP-OCRv5", None),
        "v5m_en": ("mobile", "mobile", "PP-OCRv5", "en"),
        "v5s": ("server", "server", "PP-OCRv5", None),
        "v6t": ("tiny", "tiny", "PP-OCRv6", None),
        "v6s": ("small", "small", "PP-OCRv6", None),
        "v6m": ("medium", "medium", "PP-OCRv6", None),
    }[family]
    extra = {}
    if "up" in post:
        extra = {"Det.limit_side_len": 1440, "Global.max_side_len": 3000}
    eng = _rapid(*cfg, **extra)
    if post == "eng":
        return eng
    if not post:
        return lambda f: " ".join(eng(f).txts or ())

    def read(f):
        r = eng(f)
        return page_ocr.assemble(r), {"conf": round(page_ocr.mean_confidence(r), 4), "lines": len(r.txts or ())}
    return read


def run(out: Path, name: str, limit: int | None = None):
    import cv2
    meta = json.loads((out / "meta.json").read_text())[:limit]
    fn = method(name)
    fn(cv2.imread(str(out / meta[0]["file"])))   # warm-up: model load is not part of the per-photo time
    rows = []
    for m in meta:
        frame = cv2.imread(str(out / m["file"]))
        t = time.perf_counter()
        text = fn(frame)
        dt = time.perf_counter() - t
        text, extra = text if isinstance(text, tuple) else (text, {})
        s = score(text, m["text"])
        rows.append({"file": m["file"], "framing": m["framing"], "blur": m["blur"], "seconds": round(dt, 2),
                     **{k: round(v, 4) for k, v in s.items()}, "words": len(text.split()), **extra, "text": text})
        print(f"{name:14s} {m['file']:40s} cer {s['cer']:.3f} wer {s['wer']:.3f} {dt:5.1f}s", flush=True)
    (out / f"res_{name}.json").write_text(json.dumps(rows, indent=1))


def table(out: Path):
    res = sorted(out.glob("res_*.json"))
    print(f"{'method':16s} " + " ".join(f"{f[:4]}-b{b}" for f in FRAMINGS for b in BLURS) + "   all  sec")
    summary = {}
    for p in res:
        rows = json.loads(p.read_text())
        name = p.stem[4:]
        cells, summary[name] = [], {}
        for f in FRAMINGS:
            for b in BLURS:
                v = [r["wer"] for r in rows if r["framing"] == f and r["blur"] == b]
                cells.append(f"{100 * np.mean(v):6.1f}" if v else "     -")
                if v:
                    summary[name][f"{f}_b{b}"] = round(100 * float(np.mean(v)), 1)
        summary[name]["all_wer"] = round(100 * float(np.mean([r["wer"] for r in rows])), 1)
        summary[name]["all_cer"] = round(100 * float(np.mean([r["cer"] for r in rows])), 1)
        summary[name]["sec_per_photo_mac"] = round(float(np.mean([r["seconds"] for r in rows])), 2)
        summary[name]["n"] = len(rows)
        print(f"{name:16s} " + " ".join(cells) + f" {summary[name]['all_wer']:5.1f} {summary[name]['sec_per_photo_mac']:4.1f}")
    print("cells: word error rate % (lower is better)")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "run", "table"])
    ap.add_argument("out", type=Path)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--method", default="v5m")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--save", type=Path, help="table: also write the summary JSON here")
    a = ap.parse_args()
    if a.cmd == "make":
        make(a.out, a.n)
    elif a.cmd == "run":
        run(a.out, a.method, a.limit)
    else:
        s = table(a.out)
        if a.save:
            a.save.write_text(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
