#!/usr/bin/env python3
"""
Sakshi - 3-button study device UI for a 176x220 ILI9225 TFT (Raspberry Pi 5).

  ~/venv/bin/python sakshi.py          the real screen and the three buttons (GPIO 17 / 27 / 22)
  ~/venv/bin/python sakshi.py --png    developer check without the screen: frames go to /tmp/sakshi.png

Everything on screen comes from the real system: GURU-0.6B on ExecuTorch writes the summary and questions,
the misconception graph + Bayes + BKT + FSRS run the session, and the learner is saved on this device
(~/namma-ai/scripts/sakshi_engine.py, started automatically). No internet is used.
Keys l / m / r (and q to quit) also work in a terminal, e.g. over SSH.

Design notes
  * One accent colour. Green/red are reserved for right/wrong. Nothing else
    is coloured, so colour always carries meaning.
  * Every screen shares one skeleton: status bar (22px) / content / hint bar
    (22px). The hint bar labels sit under the physical buttons they describe
    (left label left-aligned, middle centred, right right-aligned).
  * 8px grid, 10px side margin, hairline dividers instead of boxed cards.
  * Text is hinted 1x; icons, rings and rounded corners are drawn 4x
    supersampled so edges are smooth on a low-DPI panel.
  * No gradients (they band badly in RGB565).
"""
import json
import math
import os
import re
import subprocess
import threading
import select
import sys
import time

from PIL import Image, ImageDraw, ImageFont

PW, PH = 176, 220            # the ILI9225 panel is physically portrait
ROTATE = int(os.environ.get("SAKSHI_ROTATE", "90"))   # 90 or 270: landscape UI; 0: portrait. Flip 90<->270 if upside down
W, H = (PH, PW) if ROTATE in (90, 270) else (PW, PH)  # the canvas every screen is drawn on (220 x 176 landscape)
SPI_HZ = 8_000_000          # lower to 4_000_000 if the picture is unstable


# ==========================================================================
# Display drivers (unchanged hardware path)
# ==========================================================================
class ILI9225:
    """Minimal ILI9225 driver (spidev + Blinka GPIO). Wiring: CS=CE0(pin 24),
    DC/RS=GPIO25 (pin 22), RST=GPIO24 (pin 18)."""

    def __init__(self, hz=SPI_HZ):
        import numpy as np
        import spidev, board, digitalio
        self.np = np
        self.dc = digitalio.DigitalInOut(board.D25)
        self.dc.direction = digitalio.Direction.OUTPUT
        self.rst = digitalio.DigitalInOut(board.D24)
        self.rst.direction = digitalio.Direction.OUTPUT
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = hz
        self.spi.mode = 0
        self._init()

    def _cmd(self, reg):
        self.dc.value = False
        self.spi.writebytes([0x00, reg])

    def _data(self, buf):
        self.dc.value = True
        self.spi.writebytes2(bytes(buf))

    def _reg(self, r, v):
        self._cmd(r)
        self._data([v >> 8, v & 0xFF])

    @staticmethod
    def _ms(t):
        time.sleep(t / 1000)

    def _init(self):
        reg, ms = self._reg, self._ms
        self.rst.value = True;  ms(10)
        self.rst.value = False; ms(20)
        self.rst.value = True;  ms(50)
        reg(0x10, 0x0000); reg(0x11, 0x0000); reg(0x12, 0x0000)
        reg(0x13, 0x0000); reg(0x14, 0x0000); ms(40)
        reg(0x11, 0x0018); reg(0x12, 0x6121); reg(0x13, 0x006F)
        reg(0x14, 0x495F); reg(0x10, 0x0800); ms(10)
        reg(0x11, 0x103B); ms(50)
        reg(0x01, 0x011C); reg(0x02, 0x0100); reg(0x03, 0x1030)
        reg(0x07, 0x0000); reg(0x08, 0x0808); reg(0x0B, 0x1100)
        reg(0x0C, 0x0000); reg(0x0F, 0x0D01); reg(0x15, 0x0020)
        reg(0x20, 0x0000); reg(0x21, 0x0000)
        reg(0x30, 0x0000); reg(0x31, 0x00DB); reg(0x32, 0x0000)
        reg(0x33, 0x0000); reg(0x34, 0x00DB); reg(0x35, 0x0000)
        gamma = [0x0000, 0x0808, 0x080A, 0x000A, 0x0A08,
                 0x0808, 0x0000, 0x0A00, 0x0710, 0x0710]
        for r, v in zip(range(0x50, 0x5A), gamma):
            reg(r, v)
        reg(0x07, 0x0012); ms(50)
        reg(0x07, 0x1017)

    def show(self, img):
        np = self.np
        if ROTATE:
            img = img.rotate(ROTATE, expand=True)       # landscape canvas -> portrait panel
        a = np.asarray(img.convert("RGB"), dtype=np.uint16)
        p = ((a[:, :, 0] & 0xF8) << 8) | ((a[:, :, 1] & 0xFC) << 3) | (a[:, :, 2] >> 3)
        self._reg(0x36, PW - 1); self._reg(0x37, 0)
        self._reg(0x38, PH - 1); self._reg(0x39, 0)
        self._reg(0x20, 0); self._reg(0x21, 0)
        self._cmd(0x22)
        self._data(p.astype(">u2").tobytes())


class SimDisplay:
    """Developer check over SSH: saves each frame as a PNG instead of driving the screen."""

    def __init__(self, path="/tmp/sakshi.png"):
        self.path = path

    def show(self, img):
        img.resize((W * 3, H * 3), Image.NEAREST).save(self.path)


# ==========================================================================
# Design tokens
# ==========================================================================
BG = (13, 15, 19)           # canvas
SURF = (25, 28, 35)         # raised surface
SURF2 = (36, 40, 49)        # selected surface
LINE = (46, 51, 61)         # hairlines, empty tracks
FAINT = (96, 103, 116)      # disabled / tertiary text
DIM = (146, 153, 166)       # secondary text
BODY = (206, 211, 219)      # reading text
TEXT = (238, 240, 244)      # primary text
ACC = (255, 170, 51)        # the one accent (saffron)
INK = (20, 15, 5)           # text on accent
GOOD = (80, 205, 134)
BAD = (243, 100, 92)

SB_H = 22                   # status bar height
HB_H = 22                   # hint bar height
HB_Y = H - HB_H             # hint bar top
MX = 10                     # side margin
SS = 4                      # supersampling factor for shapes

_FONT_FILES = {
    False: ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    True: ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}
_fcache = {}


def F(size, bold=False):
    key = (size, bold)
    if key not in _fcache:
        font = None
        for path in _FONT_FILES[bold]:
            try:
                font = ImageFont.truetype(path, size)
                break
            except OSError:
                pass
        if font is None:
            try:
                font = ImageFont.load_default(size=size)
            except TypeError:
                font = ImageFont.load_default()
        _fcache[key] = font
    return _fcache[key]


# ==========================================================================
# Drawing primitives
# ==========================================================================
def _mask(w, h, fn):
    m = Image.new("L", (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(m))
    return m.resize((w, h), Image.BOX)


def rrect(img, box, r=4, fill=None, outline=None, width=1):
    """Anti-aliased rounded rectangle. box = (x0, y0, x1, y1), x1/y1 exclusive."""
    x0, y0, x1, y1 = (int(v) for v in box)
    w, h = x1 - x0, y1 - y0
    if fill is not None:
        m = _mask(w, h, lambda d: d.rounded_rectangle(
            (0, 0, w * SS - 1, h * SS - 1), r * SS, fill=255))
        img.paste(fill, (x0, y0, x1, y1), m)
    if outline is not None:
        def ring(d):
            d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=255)
            i = width * SS
            d.rounded_rectangle((i, i, w * SS - 1 - i, h * SS - 1 - i),
                                max(r - width, 0) * SS, fill=0)
        img.paste(outline, (x0, y0, x1, y1), _mask(w, h, ring))


def ring(img, cx, cy, r, width, frac, color, track=LINE, start=-90):
    """Progress ring, anti-aliased."""
    x0, y0 = int(cx - r - 1), int(cy - r - 1)
    size = int(2 * r + 2)
    bb = (1 * SS, 1 * SS, (size - 1) * SS - 1, (size - 1) * SS - 1)

    def arc(d, a0, a1):
        d.arc(bb, a0, a1, fill=255, width=width * SS)

    img.paste(track, (x0, y0, x0 + size, y0 + size),
              _mask(size, size, lambda d: arc(d, 0, 360)))
    if frac > 0:
        img.paste(color, (x0, y0, x0 + size, y0 + size),
                  _mask(size, size, lambda d: arc(d, start, start + 360 * min(frac, 1))))


def _poly(m, pts, k, wd, closed=False):
    pts = [(a * k, b * k) for a, b in pts]
    seq = pts + [pts[0]] if closed else pts
    m.line(seq, fill=255, width=max(1, int(wd * k)), joint="curve")
    r = wd * k / 2
    for a, b in pts:
        m.ellipse((a - r, b - r, a + r, b + r), fill=255)


def _icon_book(m, k, w):
    _poly(m, [(12, 6.5), (3.5, 4.5), (3.5, 18.5), (12, 20.5)], k, w)
    _poly(m, [(12, 6.5), (20.5, 4.5), (20.5, 18.5), (12, 20.5)], k, w)
    _poly(m, [(12, 6.5), (12, 20.5)], k, w)


def _icon_loop(m, k, w):
    m.arc((4 * k, 4 * k, 20 * k, 20 * k), 70, 350, fill=255, width=int(w * k))
    a = math.radians(350)
    ex, ey = 12 + 8 * math.cos(a), 12 + 8 * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)
    nx, ny = math.cos(a), math.sin(a)
    tip = (ex + tx * 4.2, ey + ty * 4.2)
    b1 = (ex + nx * 3.6, ey + ny * 3.6)
    b2 = (ex - nx * 3.6, ey - ny * 3.6)
    m.polygon([(p[0] * k, p[1] * k) for p in (tip, b1, b2)], fill=255)


def _icon_diag(m, k, w):
    _poly(m, [(3.5, 3.5), (3.5, 20.5), (20.5, 20.5)], k, w)
    _poly(m, [(7.5, 16), (11, 11), (14.5, 14), (20, 6.5)], k, w)


def _icon_camera(m, k, w):
    m.rounded_rectangle((3 * k, 7 * k, 21 * k, 20 * k), 2.5 * k, outline=255, width=int(w * k))
    _poly(m, [(8, 7), (9.5, 4.2), (14.5, 4.2), (16, 7)], k, w)
    m.ellipse((8 * k, 10.2 * k, 16 * k, 17.2 * k), outline=255, width=int(w * k))


def _icon_mentor(m, k, w):
    m.rounded_rectangle((3 * k, 4 * k, 21 * k, 16 * k), 3 * k, outline=255, width=int(w * k))
    _poly(m, [(8, 16), (8, 20.5), (12.5, 16)], k, w)
    for x in (8.5, 12, 15.5):
        m.ellipse(((x - 1) * k, 9 * k, (x + 1) * k, 11 * k), fill=255)


def _icon_check(m, k, w):
    _poly(m, [(5, 12.5), (10, 17.5), (19, 7)], k, w)


def _icon_cross(m, k, w):
    _poly(m, [(6, 6), (18, 18)], k, w)
    _poly(m, [(18, 6), (6, 18)], k, w)


def _icon_circle(m, k, w):
    m.ellipse((4 * k, 4 * k, 20 * k, 20 * k), outline=255, width=int(w * k))


_ICONS = {"study": _icon_book, "revision": _icon_loop, "diag": _icon_diag,
          "camera": _icon_camera, "mentor": _icon_mentor, "check": _icon_check,
          "cross": _icon_cross, "circle": _icon_circle}


def icon(img, name, x, y, size, color, stroke=1.9):
    """24-unit grid line icon, top-left at (x, y)."""
    k = size * SS / 24.0
    m = Image.new("L", (size * SS, size * SS), 0)
    _ICONS[name](ImageDraw.Draw(m), k, stroke)
    m = m.resize((size, size), Image.BOX)
    img.paste(color, (int(x), int(y), int(x) + size, int(y) + size), m)


def spinner(img, cx, cy, r, ang, color):
    size = 2 * r + 2
    x0, y0 = int(cx - r - 1), int(cy - r - 1)

    def fn(d):
        d.arc((SS, SS, (size - 1) * SS, (size - 1) * SS), ang, ang + 110,
              fill=255, width=int(2.2 * SS))
    img.paste(color, (x0, y0, x0 + size, y0 + size), _mask(size, size, fn))


# ---- text -----------------------------------------------------------------
def text(d, x, cy, s, font, fill, align="l"):
    d.text((x, cy), s, font=font, fill=fill, anchor={"l": "lm", "r": "rm", "c": "mm"}[align])


def tracked(d, x, cy, s, font, fill, track=1, align="l"):
    """Letter-spaced text (for small caps labels)."""
    widths = [d.textlength(ch, font=font) for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    if align == "r":
        x -= total
    elif align == "c":
        x -= total / 2
    for ch, cw in zip(s, widths):
        d.text((x, cy), ch, font=font, fill=fill, anchor="lm")
        x += cw + track


def label(d, x, cy, s, fill=FAINT, align="l"):
    tracked(d, x, cy, s.upper(), F(9, True), fill, 1, align)


def wrap(d, s, font, maxw):
    lines = []
    for para in s.split("\n"):
        line = ""
        for w in para.split():
            t = (line + " " + w).strip()
            if d.textlength(t, font=font) <= maxw:
                line = t
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
    return lines


def fit(d, s, font, maxw):
    """Truncate with an ellipsis so the text never overflows."""
    if d.textlength(s, font=font) <= maxw:
        return s
    while s and d.textlength(s + "…", font=font) > maxw:
        s = s[:-1]
    return s + "…"


def para(d, x, y, s, font, fill, maxw, lh, max_lines=None):
    """Draw wrapped text starting at top y. Returns the y below the block."""
    lines = wrap(d, s, font, maxw)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit(d, lines[-1] + " …", font, maxw)
    for ln in lines:
        d.text((x, y + lh / 2), ln, font=font, fill=fill, anchor="lm")
        y += lh
    return y


# ---- chrome ---------------------------------------------------------------
def canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def status_bar(img, d, title, right="", brand=False):
    cy = SB_H // 2
    if brand:
        d.rectangle((MX, cy - 5, MX + 2, cy + 5), fill=ACC)
        tracked(d, MX + 8, cy, "SAKSHI", F(11, True), TEXT, 2)
    else:
        text(d, MX, cy, title, F(12, True), TEXT)
    if right:
        text(d, W - MX, cy, right, F(10), DIM, "r")
    d.line((0, SB_H - 1, W, SB_H - 1), fill=LINE)


def hint_bar(img, d, left="", mid="", right=""):
    d.line((0, HB_Y, W, HB_Y), fill=LINE)
    cy = HB_Y + HB_H // 2 + 1
    if left:
        text(d, MX, cy, "‹  " + left, F(10), DIM)
    if mid:
        text(d, W // 2, cy, mid, F(11, True), ACC, "c")
    if right:
        text(d, W - MX, cy, right + "  ›", F(10), DIM, "r")


def pager(img, d, n, i, y, color=ACC):
    seg, gap = 14, 4
    x = (W - (n * seg + (n - 1) * gap)) // 2
    for j in range(n):
        d.rectangle((x, y, x + seg - 1, y + 1), fill=color if j == i else LINE)
        x += seg + gap


def segments(d, n, upto, y=SB_H):
    """Thin progress strip under the status bar."""
    gap = 2
    sw = (W - gap * (n - 1)) / n
    for j in range(n):
        x0 = round(j * (sw + gap))
        x1 = round(j * (sw + gap) + sw) - 1
        d.rectangle((x0, y, x1, y + 1), fill=ACC if j < upto else LINE)


def kv(d, y, k, v, vfill=TEXT, kfont=None):
    """Key/value row with a hairline above it. y is the row's top; height 22."""
    d.line((MX, y, W - MX, y), fill=LINE)
    text(d, MX, y + 11, k, kfont or F(10), DIM)
    text(d, W - MX, y + 11, v, F(11, True), vfill, "r")


def bar(d, x0, y, x1, h, frac, fill=ACC, track=LINE):
    d.rectangle((x0, y, x1 - 1, y + h - 1), fill=track)
    w = int(round((x1 - x0) * max(0.0, min(frac, 1.0))))
    if w > 0:
        d.rectangle((x0, y, x0 + w - 1, y + h - 1), fill=fill)



# ==========================================================================
# The engine: GURU-0.6B + misconception graph + Bayes / BKT / FSRS, in its own
# process (~/sakshi-venv, ExecuTorch). It is loaded once when the device starts.
# Messages are JSON lines; see ~/namma-ai/scripts/sakshi_engine.py.
# ==========================================================================
HOME = os.path.expanduser("~")
ENGINE_PY = os.environ.get("SAKSHI_PY", os.path.join(HOME, "sakshi-venv", "bin", "python"))
ENGINE_REPO = os.environ.get("SAKSHI_REPO", os.path.join(HOME, "namma-ai"))
PASSAGE_FILE = os.environ.get("SAKSHI_PASSAGE", os.path.join(HOME, "passage.txt"))
STAGES = ["Reading text", "Writing summary", "Building questions"]


class Engine:
    def __init__(self):
        import collections
        self.events = collections.deque()
        self.alive = False
        self.p = None
        try:
            env = dict(os.environ, PYTHONPATH=os.path.join(ENGINE_REPO, "src"))
            log = open("/tmp/sakshi_engine.log", "a")
            self.p = subprocess.Popen([ENGINE_PY, os.path.join(ENGINE_REPO, "scripts", "sakshi_engine.py")],
                                      cwd=ENGINE_REPO, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=log, text=True, bufsize=1)
            self.alive = True
            threading.Thread(target=self._read, daemon=True).start()
        except Exception as e:  # noqa: BLE001
            self.events.append({"type": "error", "msg": f"Engine did not start: {e}"})

    def _read(self):
        for line in self.p.stdout:
            try:
                self.events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        self.alive = False
        self.events.append({"type": "error", "msg": "The engine stopped. Restart the device."})

    def send(self, **cmd):
        if self.p and self.alive:
            try:
                self.p.stdin.write(json.dumps(cmd) + "\n")
                self.p.stdin.flush()
            except (BrokenPipeError, OSError):
                self.alive = False

    def pop(self):
        return self.events.popleft() if self.events else None


# ==========================================================================
# Camera + OCR (RapidOCR PP-OCRv5 mobile, runs on the Pi, models on disk)
# ==========================================================================
class Camera:
    def __init__(self):
        self.cap, self.frame, self.error = None, None, None

    def open(self):
        if self.cap is not None:
            return True
        try:
            import cv2
            cap = cv2.VideoCapture(int(os.environ.get("SAKSHI_CAM", "0")))
            if not cap.isOpened():
                raise RuntimeError("no camera found")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
            self.cap, self.error = cap, None
            return True
        except Exception as e:  # noqa: BLE001
            self.error = str(e)
            return False

    def read(self):
        if self.cap is None:
            return None
        ok, f = self.cap.read()
        if ok:
            self.frame = f
        return self.frame if ok else None

    def close(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = None


def frame_to_area(frame, w, h):
    """BGR camera frame -> PIL image filling w x h (centre crop, no stretching)."""
    import cv2
    fh, fw = frame.shape[:2]
    scale = max(w / fw, h / fh)
    small = cv2.resize(frame, (int(fw * scale) + 1, int(fh * scale) + 1))
    y0, x0 = (small.shape[0] - h) // 2, (small.shape[1] - w) // 2
    rgb = cv2.cvtColor(small[y0:y0 + h, x0:x0 + w], cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


class OCR:
    """Loaded in the background at start-up; reading a page takes a few seconds on the Pi."""

    def __init__(self):
        self.engine, self.error = None, None
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            from rapidocr import ModelType, OCRVersion, RapidOCR
            self.engine = RapidOCR(params={"Det.ocr_version": OCRVersion.PPOCRV5, "Rec.ocr_version": OCRVersion.PPOCRV5,
                                           "Det.model_type": ModelType.MOBILE, "Rec.model_type": ModelType.MOBILE})
        except Exception as e:  # noqa: BLE001
            self.error = str(e)

    def read(self, frame):
        while self.engine is None and self.error is None:
            time.sleep(0.1)
        if self.engine is None:
            raise RuntimeError("OCR not available: " + self.error)
        return " ".join(self.engine(frame).txts or ())


# ==========================================================================
# What each engine event looks like on screen
# ==========================================================================
NOTE_KINDS = {"again", "diagnosis", "rebuild", "walk_down", "climb_stop", "climb_up", "recheck", "still",
              "cleared", "related", "related_found", "blocked", "climbed"}


def note_view(e):
    """Engine event -> (label, label colour, title, body, breadcrumb nodes or None, active node)."""
    k, c = e["type"], e.get("concept", "")
    q = lambda s: f"“{s}”"  # noqa: E731
    if k == "again":
        return "One more", ACC, c, "Let me ask that in another way.", None, 0
    if k == "diagnosis":
        lab = "We found a mix-up" if e.get("confirmed") else "Maybe a mix-up"
        return lab, ACC, "You may think:", f"{q(e['text'])}\nIn fact: {e.get('fix') or e.get('remember', '')}", None, 0
    if k == "rebuild":
        return "Let's rebuild", ACC, c, e.get("remember") or "Let's go over this idea again.", None, 0
    if k == "walk_down":
        to = e.get("to") or []
        return "Step down", ACC, to[0] if to else c, f"First, the idea that {c} builds on.", [c] + to[:2], 1
    if k == "climb_stop":
        w = ", ".join(e.get("waits") or [])
        return "Pause here", ACC, c, f"We come back to this once {w} is solid. It is first in your next revision.", None, 0
    if k == "climb_up":
        return "Step up", ACC, c, ("Let's try using it once more." if e.get("retry")
                                    else "Now use the idea in a real situation."), None, 0
    if k == "recheck":
        return "Check", ACC, c, f"Last time you seemed to think {q(e['text'])}. Let's check.", None, 0
    if k == "still":
        return "Still there", BAD, c, f"{q(e['text'])}\nIn fact: {e.get('fix', '')}", None, 0
    if k == "cleared":
        return "Fixed", GOOD, c, f"You no longer think {q(e['text'])}. Well done.", None, 0
    if k == "related":
        root = e.get("root")
        return "Related idea", ACC, c, (f"Same root idea: {root}." if root and e.get("same_root")
                                        else "An idea that often comes with the last one."), None, 0
    if k == "related_found":
        return "Also found", BAD, c, f"{q(e['text'])}\nIn fact: {e.get('fix', '')}", None, 0
    if k == "blocked":
        return "Not yet", ACC, c, "First make " + ", ".join(e.get("waits") or []) + " solid.", None, 0
    if k == "climbed":
        return "Step up done", GOOD, c, "You climbed back up. Well done.", None, 0
    return "Note", ACC, c, "", None, 0


# ==========================================================================
# UI state machine
# ==========================================================================
APPS = [("Study", "study", "Learn from a photo of\nyour textbook page"),
        ("Revision", "revision", "Practise what you\nalready know well"),
        ("Diagnostics", "diag", "See where you are\nstuck, and why")]
STUDY_OPTS = [("New Study", "camera", "Photograph a page, get\na summary and quiz"),
              ("Saved page", "study", "Study the page saved\non this device"),
              ("Mentor Study", "mentor", "Fix mix-ups from\nearlier sessions")]


class UI:
    def __init__(self, engine, camera, ocr):
        self.eng, self.cam, self.ocr = engine, camera, ocr
        self.screen, self.sel, self.t0 = "menu", 0, time.time()
        self.st = dict(solved=0, correct=0, held=[], due=0, blocked=[], topics=[], weak=[], models_ready=False)
        self.ready = False            # engine process answered
        self.mode = None              # "study" | "mentor" | "revision" while a session runs
        self.home = "menu"
        self.queue = []               # engine events waiting to be shown, in order
        self.q = self.res = self.note = self.done = None
        self.summary, self.stage, self.err = [], 0, ""
        self.choice = 0
        self.right = self.asked = 0
        self.leaving = False
        self.photo = None
        self.ocr_job = None

    # ---- navigation
    def go(self, screen, sel=0):
        self.screen, self.sel, self.t0 = screen, sel, time.time()

    def press(self, k):
        getattr(self, "on_" + self.screen)(k)

    # ---- sessions
    def start(self, mode, home, text_=None):
        self.mode, self.home, self.queue = mode, home, []
        self.q = self.res = self.note = self.done = None
        self.right = self.asked = 0
        self.leaving = False
        if mode == "study":
            self.summary, self.stage = [], 2
            self.eng.send(cmd="study", text=text_)
            self.go("ocr")
        else:
            self.eng.send(cmd=mode)
            self.go("wait")

    def leave(self):
        """Back during a session: the engine saves what was learned so far."""
        if self.mode:
            self.eng.send(cmd="stop")
            self.leaving = True
        self.go(self.home)

    def advance(self):
        """Show the next thing the engine sent. Called after Next / Continue / Start quiz."""
        while self.queue:
            e = self.queue.pop(0)
            t = e["type"]
            if t == "question":
                self.q, self.sel = e, 0
                self.go("q")
                return
            if t == "result":
                self.res = e
                self.asked += 1
                self.right += bool(e["ok"])
                self.go("fb")
                return
            if t in NOTE_KINDS:
                self.note = e
                self.go("note")
                return
            if t == "done":
                self.finish(e)
                return
            if t == "error":
                self.err = e["msg"]
                self.mode = None
                self.go("error")
                return
        self.go("wait")

    def finish(self, e):
        if e.get("card"):   # the judges' run card goes to the terminal / log, not the child's screen
            print("RUN CARD " + json.dumps(e["card"]) + "\r", flush=True)
        self.done, self.mode = e, None
        self.eng.send(cmd="status")
        self.go("results")

    # ---- engine events, ~8x a second
    def pump(self):
        dirty = False
        while True:
            e = self.eng.pop()
            if e is None:
                return dirty
            dirty = True
            t = e["type"]
            if t == "ready":
                self.ready = True
                self.eng.send(cmd="status")
            elif t == "status":
                self.st.update(e)
            elif self.leaving:                       # the child left: drop the rest of that session
                if t in ("done", "error"):
                    self.leaving, self.mode = False, None
                    self.eng.send(cmd="status")
            elif t == "stage":
                self.stage = e["n"]
            elif t == "loading":
                self.stage = max(self.stage, 1)
            elif t == "summary":
                self.summary = summary_cards(e["text"])
                if self.screen == "ocr":
                    self.go("summary")
            elif t == "waiting":
                pass                                  # the wait screen covers it
            elif t == "error" and self.screen in ("ocr", "summary"):
                self.err, self.mode = e["msg"], None
                self.go("error")
            else:
                self.queue.append(e)
                if self.screen == "wait":
                    self.advance()

    def tick(self):
        dirty = self.pump()
        if self.screen in ("menu", "study_home", "rev_home", "diag") and time.time() - getattr(self, "_st_t", 0) > 5:
            self._st_t = time.time()      # keep the numbers fresh (the model finishes loading in the background)
            self.eng.send(cmd="status")
        if self.screen == "camera":
            return self.cam.read() is not None or dirty
        if self.screen == "reading" and self.ocr_job and self.ocr_job.get("done"):
            job, self.ocr_job = self.ocr_job, None
            if job.get("error"):
                self.err = job["error"]
                self.go("error")
            else:
                self.start("study", "study_home", job["text"])
            return True
        return dirty or self.screen in ("ocr", "wait", "reading")  # spinners

    # ---- input handlers
    def on_menu(self, k):
        if k == "L":
            self.sel = (self.sel - 1) % 3
        elif k == "R":
            self.sel = (self.sel + 1) % 3
        elif k == "M":
            self.go(("study_home", "rev_home", "diag")[self.sel])

    def on_study_home(self, k):
        if k == "L":
            self.go("menu", 0)
        elif k == "R":
            self.sel = (self.sel + 1) % len(STUDY_OPTS)
        elif k == "M":
            if self.sel == 0:
                self.go("camera" if self.cam.open() else "nocam")
            elif self.sel == 1:
                if os.path.exists(PASSAGE_FILE):
                    self.start("study", "study_home", open(PASSAGE_FILE, encoding="utf-8").read())
                else:
                    self.err = "No saved page. Put the text in passage.txt."
                    self.go("error")
            else:
                self.start("mentor", "study_home")

    def on_nocam(self, k):
        if k in ("L", "M"):
            self.go("study_home")

    def on_camera(self, k):
        if k == "L":
            self.cam.close()
            self.go("study_home")
        elif k == "M" and self.cam.frame is not None:
            self.photo = self.cam.frame.copy()
            self.go("captured")

    def on_captured(self, k):
        if k == "L":
            self.go("camera")
        elif k == "M":
            self.cam.close()
            job = {}
            self.ocr_job = job

            def run(frame=self.photo):
                try:
                    job["text"] = self.ocr.read(frame)
                except Exception as e:  # noqa: BLE001
                    job["error"] = str(e)
                job["done"] = True
            threading.Thread(target=run, daemon=True).start()
            self.stage = 1
            self.go("reading")

    def on_reading(self, k):
        pass

    def on_ocr(self, k):
        if k == "L":
            self.leave()

    def on_summary(self, k):
        if k == "L":
            self.leave()
        elif k == "R":
            self.sel = (self.sel + 1) % max(1, len(self.summary))
        elif k == "M":
            self.advance()

    def on_q(self, k):
        if k == "L":
            self.leave()
        elif k == "R":
            self.sel = (self.sel + 1) % len(self.q["options"])
        elif k == "M":
            self.choice = self.sel
            self.eng.send(cmd="answer", key=self.q["keys"][self.sel])
            self.go("wait")

    def on_fb(self, k):
        if k == "L":
            self.leave()
        elif k == "M":
            self.advance()

    def on_note(self, k):
        if k == "L":
            self.leave()
        elif k == "M":
            self.advance()

    def on_wait(self, k):
        if k == "L":
            self.leave()

    def on_results(self, k):
        if k in ("L", "M"):
            self.go(self.home)

    def on_error(self, k):
        if k in ("L", "M"):
            self.go(self.home if self.home else "menu")

    def on_rev_home(self, k):
        if k == "L":
            self.go("menu", 1)
        elif k == "M" and self.st.get("topics"):
            self.start("revision", "rev_home")

    def on_diag(self, k):
        if k == "L":
            self.go("menu", 2)
        elif k == "R":
            self.sel = (self.sel + 1) % 3

    def render(self):
        return getattr(self, "draw_" + self.screen)()

    def accuracy(self):
        return round(100 * self.st["correct"] / max(self.st["solved"], 1))

    # ======================================================================
    # Screens
    # ======================================================================
    def draw_menu(self):
        img, d = canvas()
        status_bar(img, d, "", f"{self.sel + 1} / 3", brand=True)
        tw, th, gap = 60, 40, 10
        x0 = (W - (3 * tw + 2 * gap)) // 2
        for i, (_, ic, _) in enumerate(APPS):
            x = x0 + i * (tw + gap)
            on = i == self.sel
            if on:
                rrect(img, (x, 28, x + tw, 28 + th), 6, fill=SURF2)
                d.rectangle((x + 12, 28 + th - 2, x + tw - 13, 28 + th - 1), fill=ACC)
            else:
                rrect(img, (x, 28, x + tw, 28 + th), 6, outline=LINE)
            icon(img, ic, x + (tw - 24) // 2, 36, 24, ACC if on else FAINT)
        name, _, sub = APPS[self.sel]
        text(d, MX, 84, name, F(16, True), TEXT)
        text(d, MX, 100, sub.replace("\n", " "), F(10), DIM)
        s = self.st
        if self.sel == 0:
            rows = [("Mix-ups to fix", f"{len(s['held'])} waiting", ACC if s["held"] else TEXT),
                    ("Device", "ready" if s.get("models_ready") else "getting ready", GOOD if s.get("models_ready") else DIM)]
        elif self.sel == 1:
            rows = [("Ideas learned", str(len(s["topics"])), TEXT), ("Due today", str(s["due"]), ACC if s["due"] else TEXT)]
        else:
            rows = [("Solved", str(s["solved"]), TEXT), ("Accuracy", f"{self.accuracy()}%" if s["solved"] else "-", TEXT)]
        for j, (k, v, c) in enumerate(rows):
            kv(d, 110 + j * 22, k, v, c)
        hint_bar(img, d, "Prev", "Open", "Next")
        return img

    def draw_study_home(self):
        img, d = canvas()
        status_bar(img, d, "Study")
        for i, (name, ic, sub) in enumerate(STUDY_OPTS):
            y = 26 + i * 42
            on = i == self.sel
            if on:
                rrect(img, (6, y, W - 6, y + 38), 4, fill=SURF2)
                d.rectangle((6, y + 7, 8, y + 31), fill=ACC)
            icon(img, ic, 18, y + 8, 22, ACC if on else FAINT)
            text(d, 50, y + 12, name, F(12, True), TEXT if on else BODY)
            text(d, 50, y + 27, fit(d, sub.replace("\n", " "), F(9), W - 50 - (40 if i == 2 else 12)), F(9), DIM)
            if i == 2 and self.st["held"]:
                rrect(img, (W - 34, y + 11, W - 12, y + 27), 8, fill=ACC)
                text(d, W - 23, y + 19, str(len(self.st["held"])), F(10, True), INK, "c")
        hint_bar(img, d, "Back", "Open", "Next")
        return img

    def draw_nocam(self):
        img, d = canvas()
        status_bar(img, d, "New Study", "Camera")
        text(d, MX, 46, "Camera not found", F(14, True), TEXT)
        para(d, MX, 64, "Check the camera cable, or use Saved page to study the page on this device.",
             F(11), BODY, W - 2 * MX, 15, 5)
        hint_bar(img, d, "Back", "OK", "")
        return img

    def draw_camera(self):
        img, d = canvas()
        status_bar(img, d, "New Study", "Camera")
        if self.cam.frame is not None:
            img.paste(frame_to_area(self.cam.frame, W, HB_Y - SB_H), (0, SB_H))
        d = ImageDraw.Draw(img)
        d.rectangle((0, HB_Y - 20, W, HB_Y - 1), fill=(10, 11, 14))
        text(d, W // 2, HB_Y - 10, "Fit the whole page in the frame", F(10), BODY, "c")
        hint_bar(img, d, "Back", "Capture", "")
        return img

    def draw_captured(self):
        img, d = canvas()
        status_bar(img, d, "New Study", "Photo")
        if self.photo is not None:
            img.paste(frame_to_area(self.photo, W, HB_Y - SB_H), (0, SB_H))
        d = ImageDraw.Draw(img)
        d.rectangle((0, HB_Y - 36, W, HB_Y - 1), fill=(10, 11, 14))
        icon(img, "check", MX, HB_Y - 30, 14, GOOD, 2.4)
        text(d, MX + 20, HB_Y - 23, "Photo taken", F(12, True), TEXT)
        text(d, MX, HB_Y - 9, "Is the text sharp and readable?", F(10), DIM)
        hint_bar(img, d, "Retake", "Use photo", "")
        return img

    def _stages(self, img, d, stage, title, sub):
        el = time.time() - self.t0
        text(d, MX, 36, title, F(13, True), TEXT)
        text(d, W - MX, 36, f"{int(el)} s", F(9, True), DIM, "r")
        text(d, MX, 52, sub, F(9), DIM)
        for i, name in enumerate(STAGES):
            cy = 78 + i * 25
            done, act = i < stage - 1, i == stage - 1
            if done:
                icon(img, "check", MX, cy - 8, 16, GOOD, 2.6)
            else:
                icon(img, "circle", MX, cy - 8, 16, LINE, 2.2)
                if act:
                    spinner(img, MX + 8, cy, 7, (el * 360) % 360, ACC)
            text(d, MX + 26, cy, name, F(12, act), TEXT if (done or act) else FAINT)
            if done:
                text(d, W - MX, cy, "done", F(9), FAINT, "r")
            if i < 2:
                d.line((MX + 26, cy + 12, W - MX, cy + 12), fill=LINE)

    def draw_reading(self):
        img, d = canvas()
        status_bar(img, d, "New Study", "Working")
        self._stages(img, d, 1, "Reading your page", "Runs on this device. No internet.")
        hint_bar(img, d, "", "", "")
        return img

    def draw_ocr(self):
        img, d = canvas()
        status_bar(img, d, "New Study", "Working")
        sub = "Getting ready, first time only." if self.stage <= 1 else "Runs on this device. No internet."
        self._stages(img, d, max(self.stage, 2), "Analysing your page", sub)
        hint_bar(img, d, "Cancel", "", "")
        return img

    def draw_summary(self):
        img, d = canvas()
        n = max(1, len(self.summary))
        status_bar(img, d, "Summary", f"{self.sel + 1} / {n}")
        if self.summary:
            tag, title, body = self.summary[self.sel]
            label(d, MX, 32, tag, ACC)
            text(d, MX, 48, title, F(14, True), TEXT)
            para(d, MX, 62, body, F(12), BODY, W - 2 * MX, 16, 5)
        pager(img, d, n, self.sel, HB_Y - 6)
        ready = any(e["type"] == "question" for e in self.queue)
        hint_bar(img, d, "Back", "Start quiz" if ready else "Start", "More")
        return img

    def draw_wait(self):
        img, d = canvas()
        status_bar(img, d, {"study": "New Study", "mentor": "Mentor Study", "revision": "Revision"}.get(self.mode, "Sakshi"))
        el = time.time() - self.t0
        spinner(img, W // 2, 70, 16, (el * 360) % 360, ACC)
        msg = "Writing your next question" if self.mode == "study" else "Thinking"
        text(d, W // 2, 106, msg, F(12, True), TEXT, "c")
        text(d, W // 2, 122, "on this device, no internet", F(9), DIM, "c")
        hint_bar(img, d, "Stop", "", "")
        return img

    def draw_q(self):
        img, d = canvas()
        e = self.q
        status_bar(img, d, e["tag"], f"Q {e['n']}")
        n, ow = len(e["options"]), W - 38 - 10
        full = wrap(d, e["options"][self.sel], F(10, True), ow)
        for font, lh in ((F(12, True), 15), (F(11, True), 13), (F(10, True), 12)):  # shrink before cutting
            stem_lines = len(wrap(d, e["stem"], font, W - 2 * MX))
            room = (HB_Y - 4 - (30 + min(stem_lines, 5) * lh)) - (n - 1) * 14
            if stem_lines <= 3 and (room - 6) // 11 >= len(full):
                break
        y = para(d, MX, 28, e["stem"], font, TEXT, W - 2 * MX, lh, 5)
        top = y + 2
        room = (HB_Y - 2 - top) - (n - 1) * 14          # height left for the selected option
        sel_lines = full[:max(1, min(len(full), (room - 5) // 11))]
        if len(sel_lines) < len(full):
            sel_lines[-1] = fit(d, sel_lines[-1] + " " + full[len(sel_lines)], F(10, True), ow)
        yy = top
        for i, txt in enumerate(e["options"]):
            on = i == self.sel
            lines = sel_lines if on else [fit(d, txt, F(10), ow)]
            h = max(12, len(lines) * 11 + 2)
            if on:
                rrect(img, (6, yy, W - 6, yy + h), 4, fill=SURF2)
                d.rectangle((6, yy + 3, 8, yy + h - 3), fill=ACC)
            box = (14, yy + 0, 27, yy + 12)
            rrect(img, box, 3, fill=ACC) if on else rrect(img, box, 3, outline=LINE)
            text(d, 20.5, yy + 6, e["keys"][i], F(9, True), INK if on else DIM, "c")
            for k, ln in enumerate(lines):
                text(d, 34, yy + 6.5 + k * 11, ln, F(10, on), TEXT if on else BODY)
            yy += h + 2
        hint_bar(img, d, "Stop", "Answer", "Next")
        return img

    def draw_fb(self):
        img, d = canvas()
        e, q = self.res, self.q
        status_bar(img, d, q["tag"], f"Q {q['n']}")
        ok = e["ok"]
        col = GOOD if ok else BAD
        d.rectangle((6, 28, 8, 46), fill=col)
        icon(img, "check" if ok else "cross", 16, 29, 16, col, 2.6)
        text(d, 38, 37, "Correct" if ok else "Not quite", F(14, True), col)
        label(d, MX, 56, "Answer", GOOD)
        y = para(d, MX, 63, f"{e['correct']}) {e['correct_text']}", F(11, True), TEXT, W - 2 * MX, 13, 4)
        why = e.get("explanation") or ""
        if why and why.strip(" .").lower() != e["correct_text"].strip(" .").lower() and y < HB_Y - 30:
            label(d, MX, y + 8, "Why", ACC)
            para(d, MX, y + 15, why, F(10), BODY, W - 2 * MX, 12, max(1, (HB_Y - y - 19) // 12))
        hint_bar(img, d, "Stop", "Next", "")
        return img

    def draw_note(self):
        img, d = canvas()
        lab, col, title, body, nodes, active = note_view(self.note)
        status_bar(img, d, {"study": "New Study", "mentor": "Mentor Study", "revision": "Revision"}.get(self.mode, "Sakshi"))
        y = 32
        if nodes:                                   # where we are in the idea map
            xs = [30 + i * ((W - 60) // max(1, len(nodes) - 1)) for i in range(len(nodes))]
            d.line((xs[0], 34, xs[-1], 34), fill=LINE, width=2)
            for i, (x, nm) in enumerate(zip(xs, nodes)):
                on = i == active
                r = 5 if on else 4
                d.ellipse((x - r, 34 - r, x + r, 34 + r), fill=ACC if on else FAINT)
                al = "l" if i == 0 else "r" if i == len(nodes) - 1 else "c"
                lx = MX if al == "l" else W - MX if al == "r" else x
                text(d, lx, 48, fit(d, nm, F(8, on), 66), F(8, on), TEXT if on else DIM, al)
            d.line((MX, 57, W - MX, 57), fill=LINE)
            y = 66
        label(d, MX, y, lab, col)
        y = para(d, MX, y + 8, title, F(12, True), TEXT, W - 2 * MX, 15, 2)
        para(d, MX, y + 4, body, F(11), BODY, W - 2 * MX, 13, max(1, (HB_Y - y - 8) // 13))
        hint_bar(img, d, "Stop", "Continue", "")
        return img

    def draw_results(self):
        img, d = canvas()
        e = self.done or {}
        name = {"study": "New Study", "mentor": "Mentor Study", "revision": "Revision"}.get(e.get("mode"), "Done")
        status_bar(img, d, name, "Complete")
        if e.get("message") and not e.get("asked"):
            text(d, W // 2, 80, e["message"], F(13, True), TEXT, "c")
            hint_bar(img, d, "Back", "Done", "")
            return img
        total = self.asked or e.get("asked", 0)
        right = self.right if self.asked else e.get("right", 0)
        frac = right / total if total else 0
        ring(img, 48, 68, 32, 6, frac, GOOD if frac >= .6 else ACC)
        text(d, 48, 66, f"{right}/{total}", F(17, True), TEXT, "c")
        text(d, 48, 80, "correct", F(8), DIM, "c")
        found = e.get("found") or []
        x0 = 96
        for j, (k, v, c) in enumerate((("Mix-ups", str(len(found)), ACC if found else GOOD),
                                       ("Revise on", e.get("next_review") or "-", TEXT))):
            y = 40 + j * 26
            d.line((x0, y - 11, W - MX, y - 11), fill=LINE)
            text(d, x0, y, k, F(10), DIM)
            text(d, W - MX, y, v, F(11, True), c, "r")
        if found:
            label(d, MX, 114, "Work on", ACC)
            para(d, MX, 122, "“" + found[0] + "”", F(9), DIM, W - 2 * MX, 11, 2)
        hint_bar(img, d, "Back", "Done", "")
        return img

    def draw_error(self):
        img, d = canvas()
        status_bar(img, d, "Sakshi")
        icon(img, "cross", MX, 34, 16, BAD, 2.6)
        text(d, MX + 24, 42, "Let's try again", F(12, True), TEXT)
        para(d, MX, 62, self.err, F(11), BODY, W - 2 * MX, 14, 6)
        hint_bar(img, d, "Back", "OK", "")
        return img

    def draw_rev_home(self):
        img, d = canvas()
        status_bar(img, d, "Revision")
        icon(img, "revision", MX, 28, 22, ACC)
        text(d, MX + 32, 34, "Practise to remember", F(12, True), TEXT)
        due = self.st["due"]
        text(d, MX + 32, 48, f"{due} due today" if due else "Nothing due today", F(10), ACC if due else DIM)
        topics = self.st["topics"]
        label(d, MX, 66, "How well you know it")
        if not topics:
            para(d, MX, 80, "Study a page first. Ideas you learn appear here.", F(11), DIM, W - 2 * MX, 15, 4)
        for i, tp in enumerate(topics[:4]):
            y = 74 + i * 19
            d.line((MX, y, W - MX, y), fill=LINE)
            text(d, MX, y + 10, fit(d, tp["name"], F(10), 110), F(10), TEXT)
            bar(d, 126, y + 8, W - 44, 3, tp["mastery"], ACC)
            text(d, W - MX, y + 10, f"{round(tp['mastery'] * 100)}%", F(9, True), DIM, "r")
        hint_bar(img, d, "Back", "Start" if topics else "", "")
        return img

    def draw_diag(self):
        img, d = canvas()
        status_bar(img, d, "Diagnostics", f"{self.sel + 1} / 3")
        s = self.st
        acc = self.accuracy()
        if self.sel == 0:
            label(d, MX, 32, "Questions solved")
            text(d, MX, 52, str(s["solved"]), F(26, True), TEXT)
            if s["solved"]:
                text(d, W - MX, 46, f"{acc}%", F(17, True), GOOD if acc >= 60 else ACC, "r")
                label(d, W - MX, 61, "accuracy", DIM, "r")
                gw = (W - 2 * MX) * s["correct"] / max(s["solved"], 1)
                d.rectangle((MX, 74, W - MX - 1, 78), fill=BAD)
                if gw >= 1:
                    d.rectangle((MX, 74, MX + int(gw) - 1, 78), fill=GOOD)
            for j, (lab, v, c) in enumerate((("Correct", s["correct"], GOOD), ("Incorrect", s["solved"] - s["correct"], BAD))):
                y = 86 + j * 18
                d.line((MX, y, W - MX, y), fill=LINE)
                d.rectangle((MX, y + 6, MX + 5, y + 11), fill=c)
                text(d, MX + 14, y + 9, lab, F(11), BODY)
                text(d, W - MX, y + 9, str(v), F(12, True), TEXT, "r")
            kv(d, 122, "Mix-ups to fix", str(len(s["held"])), ACC if s["held"] else TEXT)
        elif self.sel == 1:
            label(d, MX, 32, "Where you are stuck", ACC)
            if s["held"]:
                y = 40
                for h in s["held"][:3]:
                    if y > HB_Y - 34:
                        break
                    text(d, MX, y + 6, fit(d, h["concept"], F(10, True), W - 2 * MX), F(10, True), TEXT)
                    y = para(d, MX, y + 13, "“" + h["text"] + "”", F(9), DIM, W - 2 * MX, 11, 2) + 4
            elif s["weak"]:
                top = s["weak"][0][1]
                for i, (name, cnt) in enumerate(s["weak"][:4]):
                    y = 42 + i * 24
                    text(d, MX, y + 6, fit(d, name, F(10), W - 2 * MX - 24), F(10), TEXT)
                    text(d, W - MX, y + 6, f"{cnt}×", F(10, True), ACC, "r")
                    bar(d, MX, y + 14, W - MX, 3, cnt / top, ACC)
            else:
                text(d, MX, 60, "Nothing yet. Keep going!", F(11), DIM)
        else:
            label(d, MX, 32, "What to do next", ACC)
            tips = []
            if s["held"]:
                n = len(s["held"])
                tips.append(f"Open Mentor Study: {n} mix-up{'s' if n != 1 else ''} to fix.")
            if s["blocked"]:
                tips.append(f"Revise the basics of {s['blocked'][0]} first.")
            if s["due"]:
                tips.append(f"Revision: {s['due']} idea{'s' if s['due'] != 1 else ''} due today.")
            if not tips:
                tips.append("Study a new page." if s["solved"] else "Start with Study: photograph a page.")
            if s["solved"]:
                tips.append("Short daily practice beats one long session." if acc >= 60
                            else "Read every option slowly before answering.")
            y = 42
            for i, t in enumerate(tips[:3]):
                if y > HB_Y - 24:
                    break
                text(d, MX, y + 7, str(i + 1), F(11, True), ACC)
                y = para(d, MX + 16, y, t, F(11), BODY, W - 2 * MX - 16, 14, 2) + 6
        pager(img, d, 3, self.sel, HB_Y - 6)
        hint_bar(img, d, "Back", "", "Next")
        return img


def summary_cards(summary, max_lines=5):
    """The generated summary as cards, each holding whole sentences that fit on the screen (no cut-off text)."""
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", summary.strip()) if x.strip()]
    if not sents:
        return [("Summary", "Your page", "No summary could be written for this page.")]
    d = ImageDraw.Draw(Image.new("RGB", (W, H)))
    fits = lambda t: len(wrap(d, t, F(12), W - 2 * MX)) <= max_lines  # noqa: E731
    chunks, cur = [], ""
    for snt in sents:
        nxt = (cur + " " + snt).strip()
        if cur and not fits(nxt):
            chunks.append(cur)
            nxt = snt
        cur = nxt
    chunks.append(cur)
    return [("In short" if i == 0 else "Also", f"Key points {i + 1}/{len(chunks)}", c) for i, c in enumerate(chunks)]


# ==========================================================================
# Main loop: the three buttons (GPIO 17 / 27 / 22 = Left / Middle / Right),
# and l / m / r typed in a terminal for testing over SSH
# ==========================================================================
def buttons(press_q):
    try:
        from gpiozero import Button
        bs = [Button(p, pull_up=True, bounce_time=0.05) for p in (17, 27, 22)]
        for b, k in zip(bs, "LMR"):
            b.when_pressed = (lambda k=k: press_q.append(k))
        return bs
    except Exception as e:  # noqa: BLE001
        print(f"buttons not available ({e}); use l / m / r keys\r")
        return []


def main():
    import collections
    disp = SimDisplay() if "--png" in sys.argv else ILI9225()
    ui = UI(Engine(), Camera(), OCR())
    presses = collections.deque()
    keep = buttons(presses)  # noqa: F841  (keep the Button objects alive)
    disp.show(ui.render())
    fd = sys.stdin.fileno()
    old = None
    if sys.stdin.isatty():
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0.12)
            if ready:
                chunk = os.read(fd, 64)
                for ch in chunk.decode(errors="ignore").lower():
                    if ch == "q":
                        return
                    if ch in "lmr":
                        presses.append(ch.upper())
            dirty = False
            while presses:
                ui.press(presses.popleft())
                dirty = True
                print(f"-> {ui.screen}\r")
            if ui.tick() or dirty:
                disp.show(ui.render())
    finally:
        ui.cam.close()
        if ui.eng.p:
            ui.eng.p.terminate()
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


if __name__ == "__main__":
    main()
