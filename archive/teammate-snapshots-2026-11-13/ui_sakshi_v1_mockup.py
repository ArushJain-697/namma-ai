#!/usr/bin/env python3
"""
Sakshi - 3-button UI mockup for a 176x220 ILI9225 TFT on a Raspberry Pi 5.

  python3 sakshi.py          drive the real screen
  python3 sakshi.py --sim    no hardware: writes the frame to /tmp/sakshi.png

Send key presses from the terminal (no Enter needed):
  l = Left button     m = Middle button     r = Right button     q = quit
You can type several at once, e.g.  rrm
"""
import os
import select
import sys
import time

from PIL import Image, ImageDraw, ImageFont

W, H = 176, 220
SPI_HZ = 8_000_000          # lower to 4_000_000 if the picture is unstable


# --------------------------------------------------------------------------
# Display drivers
# --------------------------------------------------------------------------
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
        a = np.asarray(img.convert("RGB"), dtype=np.uint16)
        p = ((a[:, :, 0] & 0xF8) << 8) | ((a[:, :, 1] & 0xFC) << 3) | (a[:, :, 2] >> 3)
        self._reg(0x36, W - 1); self._reg(0x37, 0)
        self._reg(0x38, H - 1); self._reg(0x39, 0)
        self._reg(0x20, 0); self._reg(0x21, 0)
        self._cmd(0x22)
        self._data(p.astype(">u2").tobytes())


class SimDisplay:
    def __init__(self, path="/tmp/sakshi.png"):
        self.path = path

    def show(self, img):
        img.resize((W * 3, H * 3), Image.NEAREST).save(self.path)


# --------------------------------------------------------------------------
# Look & feel
# --------------------------------------------------------------------------
BG = (11, 15, 30)
CARD = (24, 30, 58)
TEXT = (236, 239, 250)
DIM = (125, 135, 168)
GOOD = (52, 199, 120)
BAD = (236, 84, 84)
WARN = (245, 185, 66)
TEAL = (45, 212, 191)
AMBER = (251, 191, 36)
VIOLET = (167, 139, 250)
INK = (10, 14, 30)

_FONT_DIRS = ["/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/"]
_fcache = {}


def F(size, bold=False):
    key = (size, bold)
    if key not in _fcache:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        font = None
        for d in _FONT_DIRS:
            try:
                font = ImageFont.truetype(d + name, size)
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


def wrap(d, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            t = (line + " " + w).strip()
            if d.textlength(t, font=font) <= maxw:
                line = t
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines


def canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def header(d, title, color, right=""):
    d.rectangle((0, 0, W, 23), fill=color)
    d.text((8, 12), title, anchor="lm", font=F(14, True), fill=INK)
    if right:
        d.text((W - 8, 12), right, anchor="rm", font=F(11, True), fill=INK)


def footer(d, left, mid, right):
    y = H - 22
    d.rectangle((0, y, W, H), fill=(20, 26, 50))
    cw = W // 3
    for i, (k, label) in enumerate((("L", left), ("M", mid), ("R", right))):
        if not label:
            continue
        x = i * cw
        d.rounded_rectangle((x + 4, y + 4, x + 17, y + 18), 3, fill=(64, 74, 118))
        d.text((x + 10.5, y + 11), k, anchor="mm", font=F(10, True), fill=TEXT)
        d.text((x + 21, y + 11), label, anchor="lm", font=F(10), fill=TEXT)


def dots(d, n, active, y, color):
    gap = 12
    x0 = W / 2 - (n - 1) * gap / 2
    for i in range(n):
        r = 3.5 if i == active else 2.5
        d.ellipse((x0 + i * gap - r, y - r, x0 + i * gap + r, y + r),
                  fill=color if i == active else (60, 68, 100))


def icon(d, kind, cx, cy, color, s=1.0):
    u = 10 * s
    if kind == "study":                     # open book
        d.polygon([(cx, cy - u * .6), (cx - u * 2, cy - u * 1.1), (cx - u * 2, cy + u * 1.1),
                   (cx, cy + u * 1.6)], fill=color)
        d.polygon([(cx, cy - u * .6), (cx + u * 2, cy - u * 1.1), (cx + u * 2, cy + u * 1.1),
                   (cx, cy + u * 1.6)], fill=tuple(int(c * .7) for c in color))
        for k in (-.2, .4):
            d.line((cx - u * 1.6, cy + k * u, cx - u * .3, cy + k * u + u * .4), fill=INK, width=1)
            d.line((cx + u * .3, cy + k * u + u * .4, cx + u * 1.6, cy + k * u), fill=INK, width=1)
    elif kind == "revision":                # circular arrow
        d.arc((cx - u * 1.6, cy - u * 1.6, cx + u * 1.6, cy + u * 1.6), 40, 330, fill=color, width=int(4 * s))
        d.polygon([(cx + u * 1.5, cy - u * .2), (cx + u * 2.2, cy - u * 1.4), (cx + u * .6, cy - u * 1.3)], fill=color)
    elif kind == "diag":                    # bar chart
        for i, h in enumerate((1.0, 2.2, 1.6)):
            x = cx - u * 1.7 + i * u * 1.2
            d.rounded_rectangle((x, cy + u * 1.4 - h * u, x + u * .9, cy + u * 1.4), 2, fill=color)
        d.line((cx - u * 2, cy + u * 1.5, cx + u * 2, cy + u * 1.5), fill=DIM, width=1)
    elif kind == "camera":
        d.rounded_rectangle((cx - u * 1.8, cy - u * 1.1, cx + u * 1.8, cy + u * 1.4), 4, fill=color)
        d.rectangle((cx - u * .8, cy - u * 1.6, cx + u * .6, cy - u * 1.0), fill=color)
        d.ellipse((cx - u * .9, cy - u * .6, cx + u * .9, cy + u * 1.2), fill=INK)
        d.ellipse((cx - u * .5, cy - u * .2, cx + u * .5, cy + u * .8), fill=color)
    elif kind == "mentor":                  # speech bubble
        d.rounded_rectangle((cx - u * 1.9, cy - u * 1.4, cx + u * 1.9, cy + u * 1.0), 6, fill=color)
        d.polygon([(cx - u * .8, cy + u * .9), (cx - u * 1.4, cy + u * 1.8), (cx + u * .1, cy + u * .9)], fill=color)
        for k in (-.9, 0, .9):
            d.ellipse((cx + k * u - 2, cy - u * .2 - 2, cx + k * u + 2, cy - u * .2 + 2), fill=INK)


# --------------------------------------------------------------------------
# Content (mock data)
# --------------------------------------------------------------------------
def Q(tag, q, opts, ans, why, concept):
    return dict(kind="mcq", tag=tag, q=q, opts=opts, ans=ans, why=why, concept=concept)


def P(tag, title, text, nodes, active):
    return dict(kind="passage", tag=tag, title=title, text=text, nodes=nodes, active=active)


NEW_STUDY = [
    Q("Diagnostic", "8 + 2 × 5 = ?",
      [("50", "Adds first, left to right"), ("18", None),
       ("80", "Treats every operator as ×"), ("13", "Drops the ×2 factor")],
      1, "× binds tighter than +. 2×5 = 10, then 8 + 10 = 18.", "Order of operations"),
    Q("Diagnostic", "(6 + 2) × 3 = ?",
      [("12", "Ignores the brackets"), ("24", None),
       ("18", "Multiplies only the nearest number"), ("11", "Swaps × for +")],
      1, "Brackets first: 6 + 2 = 8, then 8 × 3 = 24.", "Brackets"),
    P("Prerequisite", "Multiplication",
      "3 × 4 is just 4 added 3 times: 4 + 4 + 4.\nThat is why × goes before +: it is a shortcut for repeated addition.",
      ["Order of ops", "Multiply", "Repeated +"], 1),
    Q("Prerequisite", "2 × 5 is the same as...",
      [("2 + 5", "Confuses × with +"), ("5 + 5", None),
       ("5 × 5", "Repeats the wrong number"), ("2 + 2 + 5", "Mixes up what repeats")],
      1, "2 × 5 means 5 added 2 times: 5 + 5 = 10.", "Multiplication"),
]

MENTOR = [
    Q("Mentor", "4 × (3 + 2) = ?",
      [("14", "Ignores the brackets"), ("20", None),
       ("24", "Treats brackets as ×"), ("9", "Adds everything")],
      1, "Do 3 + 2 = 5 inside the brackets, then 4 × 5 = 20.", "Brackets"),
    Q("Mentor", "10 − 4 ÷ 2 = ?",
      [("3", "Subtracts first, left to right"), ("8", None),
       ("12", "Adds instead of dividing"), ("5", "Halves the wrong number")],
      1, "÷ goes before −. 4 ÷ 2 = 2, then 10 − 2 = 8.", "Order of operations"),
]

REVISION = [
    Q("Revision", "1/2 + 1/4 = ?",
      [("2/6", "Adds tops and bottoms"), ("3/4", None),
       ("1/6", "Multiplies denominators"), ("2/4", "Adds tops only")],
      1, "Make a common bottom: 2/4 + 1/4 = 3/4.", "Fractions"),
    Q("Revision", "25% of 80 = ?",
      [("25", "Reads % as the number itself"), ("32", "Uses 40% by mistake"),
       ("20", None), ("55", "Subtracts 25 from 80")],
      2, "25% is a quarter. 80 ÷ 4 = 20.", "Percentages"),
    Q("Revision", "0.5 as a fraction?",
      [("1/5", "Reads 0.5 as five tenths wrongly"), ("5/100", "Misplaces the decimal"),
       ("1/2", None), ("5/1", "Flips the fraction")],
      2, "0.5 = 5/10 = 1/2.", "Decimals"),
]

SUMMARY = [
    ("Order of operations",
     "A sum with mixed operators is not always read left to right.\nThere is a fixed priority: Brackets, Orders, ÷ ×, then + − (BODMAS)."),
    ("Think of it like this",
     "× and ÷ are stronger glue: they join numbers first.\n8 + 2 × 5 → 2 × 5 sticks as 10, then 8 + 10 = 18."),
    ("Ready?",
     "Next come a few questions.\nEach wrong answer tells us exactly what to fix."),
]

OCR_STAGES = ["Reading text (OCR)", "Writing summary", "Making questions"]
SESSION_CAP = 5


# --------------------------------------------------------------------------
# UI state machine
# --------------------------------------------------------------------------
class UI:
    def __init__(self):
        self.screen = "menu"
        self.sel = 0
        self.t0 = time.time()
        self.ctx = None
        self.choice = None
        # seeded sample stats so Diagnostics looks populated
        self.stats = dict(solved=12, correct=8,
                          weak={"Order of operations": 3, "Fractions": 2, "Brackets": 1})
        self.queue = []          # misconceptions waiting for Mentor Study

    # ---- navigation helpers
    def go(self, screen, sel=0):
        self.screen, self.sel, self.t0 = screen, sel, time.time()

    def start_session(self, name, bank, home, color):
        bank = list(bank)
        mcq_seen = 0
        if name == "Mentor Study":     # keep a cap on questions
            cut = []
            for it in bank:
                if it["kind"] == "mcq":
                    if mcq_seen >= SESSION_CAP:
                        break
                    mcq_seen += 1
                cut.append(it)
            bank = cut
        self.ctx = dict(name=name, bank=bank, i=-1, home=home, color=color, right=0, found=[])
        self.next_item()

    def next_item(self):
        c = self.ctx
        c["i"] += 1
        if c["i"] >= len(c["bank"]):
            self.go("results")
            return
        self.go("q" if c["bank"][c["i"]]["kind"] == "mcq" else "passage")

    def qnum(self):
        c = self.ctx
        total = sum(1 for it in c["bank"] if it["kind"] == "mcq")
        n = sum(1 for it in c["bank"][:c["i"] + 1] if it["kind"] == "mcq")
        return n, total

    def answer(self):
        c = self.ctx
        item = c["bank"][c["i"]]
        self.choice = self.sel
        self.stats["solved"] += 1
        if self.choice == item["ans"]:
            self.stats["correct"] += 1
            c["right"] += 1
        else:
            w = self.stats["weak"]
            w[item["concept"]] = w.get(item["concept"], 0) + 1
            misc = item["opts"][self.choice][1]
            c["found"].append(misc)
            if c["name"] != "Mentor Study":
                self.queue.append((item["concept"], misc))
        self.go("fb")

    # ---- input
    def press(self, k):
        getattr(self, "on_" + self.screen)(k)

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
            self.sel = (self.sel + 1) % 2
        elif k == "M":
            if self.sel == 0:
                self.go("camera")
            else:
                self.start_session("Mentor Study", MENTOR, "study_home", TEAL)

    def on_camera(self, k):
        if k == "L":
            self.go("study_home")
        elif k == "M":
            self.go("captured")

    def on_captured(self, k):
        if k == "L":
            self.go("camera")
        elif k == "M":
            self.go("ocr")

    def on_ocr(self, k):
        if k == "L":
            self.go("camera")

    def on_summary(self, k):
        if k == "L":
            self.go("study_home")
        elif k == "R":
            self.sel = (self.sel + 1) % len(SUMMARY)
        elif k == "M":
            self.start_session("New Study", NEW_STUDY, "study_home", TEAL)

    def on_passage(self, k):
        if k == "L":
            self.go(self.ctx["home"])
        elif k == "M":
            self.next_item()

    def on_q(self, k):
        if k == "L":
            self.go(self.ctx["home"])
        elif k == "R":
            self.sel = (self.sel + 1) % 4
        elif k == "M":
            self.answer()

    def on_fb(self, k):
        if k == "L":
            self.go(self.ctx["home"])
        elif k == "M":
            self.next_item()

    def on_results(self, k):
        if k in ("L", "M"):
            self.go(self.ctx["home"])

    def on_rev_home(self, k):
        if k == "L":
            self.go("menu", 1)
        elif k == "M":
            self.start_session("Revision", REVISION, "rev_home", AMBER)

    def on_diag(self, k):
        if k == "L":
            self.go("menu", 2)
        elif k == "R":
            self.sel = (self.sel + 1) % 3

    def tick(self):
        """Called ~8x/second. Returns True when the screen needs a redraw."""
        if self.screen == "ocr":
            el = time.time() - self.t0
            if el > 3.8:
                self.go("summary")
            return True
        return False

    # ---- drawing
    def render(self):
        return getattr(self, "draw_" + self.screen)()

    def draw_menu(self):
        img, d = canvas()
        header(d, "SAKSHI", TEXT, "Menu")
        apps = [("Study", TEAL, "study", "Learn new things\nand fix the gaps"),
                ("Revision", AMBER, "revision", "Practise what you\nalready know"),
                ("Diagnostics", VIOLET, "diag", "See where you are\nstuck, and why")]
        name, col, ic, sub = apps[self.sel]
        d.rounded_rectangle((22, 32, W - 22, 168), 14, fill=CARD, outline=col, width=2)
        icon(d, ic, W / 2, 72, col, 1.3)
        d.text((W / 2, 112), name, anchor="mm", font=F(17, True), fill=TEXT)
        for i, ln in enumerate(sub.split("\n")):
            d.text((W / 2, 134 + i * 13), ln, anchor="mm", font=F(10), fill=DIM)
        d.polygon([(8, 97), (16, 89), (16, 105)], fill=DIM)
        d.polygon([(W - 8, 97), (W - 16, 89), (W - 16, 105)], fill=DIM)
        dots(d, 3, self.sel, 184, col)
        footer(d, "Prev", "Open", "Next")
        return img

    def draw_study_home(self):
        img, d = canvas()
        header(d, "Study", TEAL)
        opts = [("New Study", "camera", "Photograph a page,\nlearn it, get quizzed"),
                ("Mentor Study", "mentor", "Fix misconceptions\nfrom earlier")]
        for i, (name, ic, sub) in enumerate(opts):
            y = 32 + i * 82
            on = i == self.sel
            d.rounded_rectangle((10, y, W - 10, y + 74), 12, fill=CARD if on else BG,
                                outline=TEAL if on else (50, 58, 90), width=2 if on else 1)
            icon(d, ic, 40, y + 37, TEAL if on else DIM, .9)
            d.text((68, y + 22), name, anchor="lm", font=F(12, True), fill=TEXT if on else DIM)
            for j, ln in enumerate(sub.split("\n")):
                d.text((68, y + 40 + j * 12), ln, anchor="lm", font=F(9), fill=DIM)
            if i == 1 and self.queue:
                d.rounded_rectangle((46, y + 6, 66, y + 22), 8, fill=WARN)
                d.text((56, y + 14), str(len(self.queue)), anchor="mm", font=F(10, True), fill=INK)
        footer(d, "Back", "Select", "Next")
        return img

    def _page(self, d, lit=False):
        d.rounded_rectangle((8, 30, W - 8, 170), 4, fill=(30, 34, 44), outline=(90, 96, 110))
        d.polygon([(30, 44), (146, 40), (150, 158), (26, 162)], fill=(236, 232, 218) if lit else (214, 210, 196))
        for i in range(9):
            y = 54 + i * 12
            d.line((38 + (i % 3), y, 138 - (i % 4) * 6, y - 1), fill=(120, 116, 104), width=2)
        for cx, cy, sx, sy in ((8, 30, 1, 1), (W - 8, 30, -1, 1), (8, 170, 1, -1), (W - 8, 170, -1, -1)):
            d.line((cx + 4 * sx, cy + 4 * sy, cx + 18 * sx, cy + 4 * sy), fill=TEXT, width=2)
            d.line((cx + 4 * sx, cy + 4 * sy, cx + 4 * sx, cy + 18 * sy), fill=TEXT, width=2)

    def draw_camera(self):
        img, d = canvas()
        header(d, "New Study", TEAL, "Camera")
        self._page(d)
        d.ellipse((14, 36, 20, 42), fill=BAD)
        d.text((24, 39), "LIVE", anchor="lm", font=F(8, True), fill=TEXT)
        d.text((W / 2, 184), "Aim at the textbook page", anchor="mm", font=F(10), fill=DIM)
        footer(d, "Back", "Snap", "")
        return img

    def draw_captured(self):
        img, d = canvas()
        header(d, "New Study", TEAL, "Captured")
        self._page(d, lit=True)
        d.rounded_rectangle((44, 90, W - 44, 116), 13, fill=GOOD)
        d.text((W / 2, 103), "Captured", anchor="mm", font=F(12, True), fill=INK)
        d.text((W / 2, 184), "Is the text readable?", anchor="mm", font=F(10), fill=DIM)
        footer(d, "Retake", "Use it", "")
        return img

    def draw_ocr(self):
        img, d = canvas()
        header(d, "New Study", TEAL, "Working")
        el = time.time() - self.t0
        stage = min(int(el / 1.2), 3)
        for i, name in enumerate(OCR_STAGES):
            y = 52 + i * 38
            done, act = i < stage, i == stage
            col = GOOD if done else (TEAL if act else (60, 68, 100))
            d.ellipse((16, y - 9, 34, y + 9), outline=col, width=2, fill=col if done else None)
            if done:
                d.line((20, y, 24, y + 4), fill=INK, width=2)
                d.line((24, y + 4, 31, y - 4), fill=INK, width=2)
            elif act:
                ang = (el * 360) % 360
                d.arc((16, y - 9, 34, y + 9), ang, ang + 100, fill=TEAL, width=3)
            d.text((44, y), name, anchor="lm", font=F(12, act), fill=TEXT if (done or act) else DIM)
        d.rounded_rectangle((16, 176, W - 16, 184), 4, fill=(40, 48, 80))
        d.rounded_rectangle((16, 176, 16 + (W - 32) * min(el / 3.6, 1), 184), 4, fill=TEAL)
        footer(d, "Cancel", "", "")
        return img

    def draw_summary(self):
        img, d = canvas()
        header(d, "Summary", TEAL, f"{self.sel + 1}/{len(SUMMARY)}")
        title, text = SUMMARY[self.sel]
        d.text((10, 38), title, anchor="lm", font=F(13, True), fill=TEAL)
        y = 54
        for ln in wrap(d, text, F(11), W - 20):
            d.text((10, y), ln, font=F(11), fill=TEXT)
            y += 15
        dots(d, len(SUMMARY), self.sel, 184, TEAL)
        footer(d, "Back", "Start", "More")
        return img

    def draw_passage(self):
        img, d = canvas()
        item = self.ctx["bank"][self.ctx["i"]]
        header(d, self.ctx["name"], self.ctx["color"], "Prereq")
        xs = (30, 88, 146)
        d.line((xs[0], 44, xs[2], 44), fill=(70, 78, 112), width=2)
        for i, (x, lab) in enumerate(zip(xs, item["nodes"])):
            on = i == item["active"]
            d.ellipse((x - 7, 37, x + 7, 51), fill=VIOLET if on else (70, 78, 112))
            d.text((x, 62), lab, anchor="mm", font=F(8, on), fill=TEXT if on else DIM)
        d.text((10, 86), item["title"], anchor="lm", font=F(13, True), fill=VIOLET)
        y = 100
        for ln in wrap(d, item["text"], F(11), W - 20):
            d.text((10, y), ln, font=F(11), fill=TEXT)
            y += 15
        footer(d, "Back", "Next", "")
        return img

    def draw_q(self):
        img, d = canvas()
        c = self.ctx
        item = c["bank"][c["i"]]
        n, total = self.qnum()
        col = c["color"]
        header(d, item["tag"], col, f"Q{n}/{total}")
        y = 30
        for ln in wrap(d, item["q"], F(13, True), W - 20):
            d.text((10, y), ln, font=F(13, True), fill=TEXT)
            y += 17
        top = max(y + 6, 62)
        rh = (H - 22 - 4 - top) // 4
        for i, (txt, _) in enumerate(item["opts"]):
            yy = top + i * rh
            on = i == self.sel
            d.rounded_rectangle((8, yy, W - 8, yy + rh - 3), 8, fill=CARD if on else BG,
                                outline=col if on else (50, 58, 90), width=2 if on else 1)
            d.ellipse((14, yy + rh / 2 - 9, 32, yy + rh / 2 + 6), fill=col if on else (50, 58, 90))
            d.text((23, yy + rh / 2 - 1.5), "ABCD"[i], anchor="mm", font=F(10, True), fill=INK if on else TEXT)
            d.text((42, yy + rh / 2 - 1.5), txt, anchor="lm", font=F(12, on), fill=TEXT if on else DIM)
        footer(d, "Back", "Select", "Next")
        return img

    def draw_fb(self):
        img, d = canvas()
        c = self.ctx
        item = c["bank"][c["i"]]
        n, total = self.qnum()
        header(d, item["tag"], c["color"], f"Q{n}/{total}")
        ok = self.choice == item["ans"]
        d.rounded_rectangle((8, 30, W - 8, 56), 8, fill=GOOD if ok else BAD)
        d.text((W / 2, 43), "Correct!" if ok else "Not quite", anchor="mm", font=F(13, True), fill=INK)
        y = 64
        if not ok:
            d.text((10, y), f"You: {'ABCD'[self.choice]}) {item['opts'][self.choice][0]}", font=F(10), fill=DIM)
            y += 14
        d.text((10, y), f"Answer: {'ABCD'[item['ans']]}) {item['opts'][item['ans']][0]}", font=F(10, True), fill=TEXT)
        y += 18
        for ln in wrap(d, item["why"], F(10), W - 20)[:4]:
            d.text((10, y), ln, font=F(10), fill=TEXT)
            y += 13
        if not ok:
            y += 4
            misc = item["opts"][self.choice][1]
            lines = wrap(d, misc, F(10, True), W - 36)[:2]
            bh = 26 + 13 * len(lines) + (12 if c["name"] != "Mentor Study" else 0)
            d.rounded_rectangle((8, y, W - 8, y + bh), 8, fill=(60, 44, 20), outline=WARN)
            d.text((14, y + 9), "MISCONCEPTION", anchor="lm", font=F(8, True), fill=WARN)
            for i, ln in enumerate(lines):
                d.text((14, y + 20 + i * 13), ln, font=F(10, True), fill=TEXT)
            if c["name"] != "Mentor Study":
                d.text((14, y + bh - 9), "→ queued for Mentor Study", anchor="lm", font=F(8), fill=WARN)
        footer(d, "Back", "Next", "")
        return img

    def draw_results(self):
        img, d = canvas()
        c = self.ctx
        header(d, c["name"], c["color"], "Done")
        total = sum(1 for it in c["bank"] if it["kind"] == "mcq")
        d.arc((48, 36, 128, 116), 0, 360, fill=(50, 58, 90), width=7)
        if total:
            d.arc((48, 36, 128, 116), -90, -90 + 360 * c["right"] / total, fill=GOOD, width=7)
        d.text((W / 2, 76), f"{c['right']}/{total}", anchor="mm", font=F(22, True), fill=TEXT)
        d.text((W / 2, 130), "Session complete", anchor="mm", font=F(12, True), fill=TEXT)
        found = len(c["found"])
        d.text((W / 2, 150), f"{found} misconception{'s' if found != 1 else ''} found",
               anchor="mm", font=F(10), fill=WARN if found else GOOD)
        if c["name"] == "Revision":
            d.text((W / 2, 166), "Wrong answers go to Mentor", anchor="mm", font=F(9), fill=DIM)
        footer(d, "Back", "Done", "")
        return img

    def draw_rev_home(self):
        img, d = canvas()
        header(d, "Revision", AMBER)
        icon(d, "revision", W / 2, 66, AMBER, 1.2)
        d.text((W / 2, 108), "Topics you know well", anchor="mm", font=F(12, True), fill=TEXT)
        x, y = 12, 124
        for t in ("Fractions", "Percentages", "Decimals"):
            w = d.textlength(t, font=F(10)) + 14
            if x + w > W - 8:
                x, y = 12, y + 22
            d.rounded_rectangle((x, y, x + w, y + 18), 9, outline=AMBER, width=1)
            d.text((x + w / 2, y + 9), t, anchor="mm", font=F(10), fill=AMBER)
            x += w + 6
        d.text((W / 2, 176), "Questions only • no hints", anchor="mm", font=F(9), fill=DIM)
        footer(d, "Back", "Start", "")
        return img

    def draw_diag(self):
        img, d = canvas()
        header(d, "Diagnostics", VIOLET, f"{self.sel + 1}/3")
        s = self.stats
        wrong = s["solved"] - s["correct"]
        acc = round(100 * s["correct"] / max(s["solved"], 1))
        weak = sorted(s["weak"].items(), key=lambda kv: -kv[1])
        if self.sel == 0:
            d.text((10, 38), "Questions solved", anchor="lm", font=F(10), fill=DIM)
            d.text((10, 58), str(s["solved"]), anchor="lm", font=F(22, True), fill=TEXT)
            d.text((W - 10, 58), f"{acc}%", anchor="rm", font=F(22, True), fill=GOOD if acc >= 60 else WARN)
            d.text((W - 10, 38), "accuracy", anchor="rm", font=F(10), fill=DIM)
            bw = W - 20
            gw = bw * s["correct"] / max(s["solved"], 1)
            d.rounded_rectangle((10, 82, 10 + bw, 94), 6, fill=BAD)
            if gw > 0:
                d.rounded_rectangle((10, 82, 10 + gw, 94), 6, fill=GOOD)
            d.ellipse((12, 110, 20, 118), fill=GOOD)
            d.text((26, 114), f"Correct  {s['correct']}", anchor="lm", font=F(11), fill=TEXT)
            d.ellipse((12, 130, 20, 138), fill=BAD)
            d.text((26, 134), f"Incorrect  {wrong}", anchor="lm", font=F(11), fill=TEXT)
            d.text((10, 160), f"Waiting in Mentor: {len(self.queue)}", anchor="lm", font=F(10), fill=WARN)
        elif self.sel == 1:
            d.text((10, 38), "Weak concepts", anchor="lm", font=F(12, True), fill=VIOLET)
            top = weak[0][1] if weak else 1
            for i, (name, cnt) in enumerate(weak[:5]):
                y = 62 + i * 28
                d.text((10, y), name, anchor="lm", font=F(10), fill=TEXT)
                d.rounded_rectangle((10, y + 8, W - 40, y + 14), 3, fill=(50, 58, 90))
                d.rounded_rectangle((10, y + 8, 10 + (W - 50) * cnt / top, y + 14), 3, fill=WARN)
                d.text((W - 10, y + 11), str(cnt), anchor="rm", font=F(10, True), fill=WARN)
        else:
            d.text((10, 38), "Smart suggestions", anchor="lm", font=F(12, True), fill=VIOLET)
            tips = []
            if weak:
                tips.append(f"Re-study “{weak[0][0]}” in Mentor Study.")
            if self.queue:
                tips.append(f"{len(self.queue)} new misconception(s) are waiting for you.")
            tips.append("Keep sessions short: 5 questions a day beats 30 once." if acc >= 60
                        else "Accuracy is low: slow down and read each option.")
            y = 56
            for t in tips[:3]:
                lines = wrap(d, t, F(10), W - 34)
                d.ellipse((10, y + 3, 16, y + 9), fill=VIOLET)
                for ln in lines:
                    d.text((22, y), ln, font=F(10), fill=TEXT)
                    y += 13
                y += 10
        dots(d, 3, self.sel, 190, VIOLET)
        footer(d, "Back", "", "Next")
        return img


# --------------------------------------------------------------------------
# Main loop: read l / m / r from the terminal
# --------------------------------------------------------------------------
def main():
    disp = SimDisplay() if "--sim" in sys.argv else ILI9225()
    ui = UI()
    disp.show(ui.render())
    print("Keys: l m r  (q quits).  Type several at once, e.g. rrm\r")

    fd = sys.stdin.fileno()
    old = None
    if sys.stdin.isatty():
        import termios, tty
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0.12)
            dirty = False
            if ready:
                chunk = os.read(fd, 64)
                if not chunk:
                    break
                for ch in chunk.decode(errors="ignore").lower():
                    if ch == "q":
                        return
                    if ch in "lmr":
                        ui.press(ch.upper())
                        dirty = True
                        print(f"{ch.upper()} -> {ui.screen}\r")
            if ui.tick():
                dirty = True
            if dirty:
                disp.show(ui.render())
    finally:
        if old is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


if __name__ == "__main__":
    main()
