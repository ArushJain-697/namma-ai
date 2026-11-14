#!/usr/bin/env python3
"""Sakshi 3-button UI mockup. Run over SSH on the Pi; type l / m / r (Enter not needed).

  python3 sakshi_ui.py                 # draw to /dev/fb1 (SPI TFT)
  python3 sakshi_ui.py --fb /dev/fb0   # other framebuffer
  python3 sakshi_ui.py --png out.png   # no TFT: write each frame to a PNG (dev on laptop)
  python3 sakshi_ui.py --keys lmrrm --png out.png   # replay keys, save last frame

Needs Pillow:  pip install pillow   (sudo apt install python3-pil on the Pi)
Quit with q or Ctrl-C.
"""
import argparse, os, sys, termios, tty, threading, time
from PIL import Image, ImageDraw, ImageFont

W, H = 320, 240
BG, PANEL, LINE = (14, 17, 22), (26, 32, 41), (43, 51, 64)
FG, DIM, AMBER, GOOD, BAD = (232, 236, 241), (154, 166, 181), (245, 165, 36), (61, 220, 151), (255, 107, 107)

FONT_PATHS = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"]
def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()
F_S, F_M, F_L = font(11), font(14), font(20)

SETS = {
 "study": [
  dict(t="q", text="What is 6 + 4 x 2 ?", c=1, e="x ranks above +. 4x2=8, then 6+8=14.",
       o=[("20", "Worked left to right: 6+4 first"), ("14", None), ("48", "Multiplied everything"), ("10", "Dropped the x 2")]),
  dict(t="q", text="12 - 2 x (3 + 1) = ?", c=2, e="Bracket: 4. Then 2x4=8. Then 12-8=4.",
       o=[("7", "Ignored the brackets"), ("40", "Worked left to right"), ("4", None), ("10", "Stopped after 12-2")]),
  dict(t="p", title="Why x comes before +", body="2 x 3 means two groups of three. It is a shortcut for adding, so it is resolved before the other + or - in the line."),
  dict(t="q", text="In 3 + 5 x 2, what is first?", c=1, e="x has higher priority: 5x2=10, then 3+10.",
       o=[("The addition", "Thinks + comes first"), ("The multiplication", None), ("Leftmost one", "Reads strictly left to right"), ("Either", "Unaware operators have priority")]),
 ],
 "mentor": [
  dict(t="q", text="(8 - 3) x 2 = ?", c=1, e="Bracket first: 5. Then 5x2=10.",
       o=[("2", "Ignored the brackets"), ("10", None), ("16", "Dropped the subtraction"), ("5", "Dropped the x 2")]),
  dict(t="q", text="20 / 4 x 5 = ?", c=1, e="/ and x share rank: 20/4=5, then 5x5=25.",
       o=[("1", "Did 4x5 first"), ("25", None), ("100", "Multiplied all three"), ("9", "Treated / as -")]),
 ],
 "revision": [
  dict(t="q", text="7 - 3 + 2 = ?", c=1, e="Left to right: 7-3=4, then 4+2=6.",
       o=[("2", "Added 3+2 first"), ("6", None), ("8", "Flipped sign of 3"), ("12", "Multiplied instead")]),
  dict(t="q", text="2 x 3^2 = ?", c=1, e="Orders first: 3^2=9. Then 2x9=18.",
       o=[("36", "Squared the product"), ("18", None), ("12", "Took 3^2 as 6"), ("9", "Dropped the 2")]),
 ],
}
MENU = [("Study", "Scan a page / mentor"), ("Revision", "Questions on known topics"), ("Diagnostics", "Weak spots + tips")]
STUDY = [("New Study", "Photograph a page"), ("Mentor Study", "Fix past misconceptions (max 3)")]
WEAK = [("Brackets first", 40, "ignores brackets"), ("Order of operations", 55, "works left to right"), ("Powers", 70, "squares the product")]


class State:
    def __init__(self):
        self.screen, self.menu, self.study, self.mode = "menu", 0, 0, "study"
        self.qi = self.sel = self.right = self.wrong = self.page = 0
        self.ocr_at = None
        self.queued = False

    def item(self): return SETS[self.mode][self.qi]
    def home(self): return "menu" if self.mode == "revision" else "study"

    def start(self, mode):
        self.mode, self.qi, self.right, self.wrong = mode, 0, 0, 0
        self.show()

    def show(self):
        self.sel = 0
        self.screen = "passage" if self.item()["t"] == "p" else "question"

    def nxt(self):
        self.qi += 1
        if self.qi >= len(SETS[self.mode]): self.screen = "result"
        else: self.show()

    def tick(self):
        if self.screen == "ocr" and time.time() >= self.ocr_at:
            self.screen = "summary"; return True
        return False

    def press(self, b):
        s = self.screen
        if s == "menu":
            if b == "l": self.menu = (self.menu - 1) % 3
            if b == "r": self.menu = (self.menu + 1) % 3
            if b == "m":
                if self.menu == 0: self.screen, self.study = "study", 0
                elif self.menu == 1: self.start("revision")
                else: self.screen, self.page = "diag", 0
        elif s == "study":
            if b == "l": self.screen = "menu"
            if b == "r": self.study = (self.study + 1) % 2
            if b == "m":
                if self.study == 0: self.screen = "camera"
                else: self.start("mentor")
        elif s == "camera":
            if b == "l": self.screen = "study"
            if b == "m": self.screen = "captured"
        elif s == "captured":
            if b == "l": self.screen = "camera"
            if b == "m": self.screen, self.ocr_at = "ocr", time.time() + 1.5
        elif s == "ocr":
            if b == "l": self.screen = "camera"
        elif s == "summary":
            if b == "l": self.screen = "study"
            if b == "m": self.start("study")
        elif s == "passage":
            if b == "l": self.screen = self.home()
            if b == "m": self.nxt()
        elif s == "question":
            if b == "l": self.screen = self.home()
            if b == "r": self.sel = (self.sel + 1) % 4
            if b == "m":
                ok = self.sel == self.item()["c"]
                self.right += ok; self.wrong += not ok
                self.screen = "feedback"
        elif s == "feedback":
            if b == "l": self.screen = self.home()
            if b == "m": self.nxt()
        elif s == "result":
            if b in "lm": self.screen = self.home()
        elif s == "diag":
            if b == "l": self.screen = "menu"
            if b == "r": self.page = (self.page + 1) % 3
            if b == "m" and self.page == 2: self.start("mentor")


def wrap(d, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

def hint_for(st):
    return {"menu": ("prev", "open", "next"), "study": ("back", "select", "next"),
            "camera": ("back", "shutter", ""), "captured": ("retake", "start", ""),
            "ocr": ("cancel", "", ""), "summary": ("back", "questions", ""),
            "passage": ("leave", "continue", ""), "question": ("leave", "answer", "next opt"),
            "feedback": ("leave", "next", ""), "result": ("back", "done", ""),
            "diag": ("back", "mentor" if st.page == 2 else "", "next page")}[st.screen]

def render(st):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    s = st.screen
    app = "SAKSHI" if s == "menu" else "DIAGNOSTICS" if s == "diag" else "REVISION" if (st.mode == "revision" and s in ("passage", "question", "feedback", "result")) else "STUDY"
    d.rectangle([0, 0, W, 22], fill=PANEL); d.line([0, 22, W, 22], fill=LINE)
    d.text((8, 4), app, font=F_M, fill=AMBER)
    top = 30

    if s == "menu":
        for i, (n, sub) in enumerate(MENU):
            x = 8 + i * 104; on = i == st.menu
            d.rectangle([x, 40, x + 98, 180], outline=AMBER if on else LINE, width=2, fill=(31, 38, 48) if on else (20, 26, 34))
            d.text((x + 49, 80), n[0], font=F_L, fill=FG, anchor="mm")
            d.text((x + 49, 110), n, font=F_M, fill=FG, anchor="mm")
            for k, ln in enumerate(wrap(d, sub, F_S, 86)): d.text((x + 49, 134 + k * 13), ln, font=F_S, fill=DIM, anchor="mm")
    elif s == "study":
        for i, (n, sub) in enumerate(STUDY):
            y = 40 + i * 72; on = i == st.study
            d.rectangle([8, y, W - 8, y + 62], outline=AMBER if on else LINE, width=2, fill=(31, 38, 48) if on else (20, 26, 34))
            d.text((18, y + 8), n, font=F_L, fill=FG); d.text((18, y + 38), sub, font=F_S, fill=DIM)
    elif s == "camera":
        d.rectangle([12, 34, W - 12, 190], outline=LINE, width=2)
        d.text((W // 2, 112), "Live camera view", font=F_M, fill=DIM, anchor="mm")
    elif s == "captured":
        d.rectangle([12, 32, W - 12, 170], fill=(242, 239, 230))
        d.text((20, 38), "4.2 Order of operations", font=F_M, fill=(27, 27, 27))
        for k, ln in enumerate(wrap(d, "Brackets first, then orders, then division and multiplication, then addition and subtraction.", F_S, W - 44)):
            d.text((20, 62 + k * 14), ln, font=F_S, fill=(27, 27, 27))
        d.text((20, 120), "Example: 6 + 4 x 2 = ?", font=F_M, fill=(27, 27, 27))
        d.text((12, 180), "Photo captured. Start reading it?", font=F_S, fill=DIM)
    elif s == "ocr":
        d.text((W // 2, 100), "Reading the page...", font=F_L, fill=FG, anchor="mm")
        d.rectangle([60, 124, 260, 132], fill=LINE); d.rectangle([60, 124, 160, 132], fill=AMBER)
    elif s == "summary":
        d.text((10, top), "Order of operations", font=F_L, fill=FG)
        for k, ln in enumerate(wrap(d, "Think of a sum as a recipe with a fixed order. Brackets first. Then x and / before + and -. So 6 + 4 x 2 is 6 + 8, not 10 x 2.", F_M, W - 20)):
            d.text((10, 62 + k * 18), ln, font=F_M, fill=(213, 220, 229))
        d.text((10, 180), "Next: 3 quick questions", font=F_S, fill=DIM)
    elif s == "passage":
        it = st.item()
        d.text((10, top), "PREREQUISITE - READ FIRST", font=F_S, fill=AMBER)
        d.text((10, 48), it["title"], font=F_L, fill=FG)
        for k, ln in enumerate(wrap(d, it["body"], F_M, W - 20)): d.text((10, 80 + k * 18), ln, font=F_M, fill=(213, 220, 229))
    elif s in ("question", "feedback"):
        it = st.item()
        qn = sum(1 for x in SETS[st.mode][:st.qi + 1] if x["t"] == "q"); tot = sum(1 for x in SETS[st.mode] if x["t"] == "q")
        d.text((10, top - 2), f"Question {qn} of {tot}" + (" | mentor cap 3" if st.mode == "mentor" else ""), font=F_S, fill=DIM)
        if s == "question":
            d.text((10, 44), it["text"], font=F_L, fill=FG)
            for i, (txt, _) in enumerate(it["o"]):
                y = 82 + i * 32; on = i == st.sel
                d.rectangle([8, y, W - 8, y + 28], outline=AMBER if on else BG, width=2, fill=(31, 38, 48) if on else BG)
                d.text((16, y + 6), "ABCD"[i], font=F_M, fill=AMBER); d.text((40, y + 6), txt, font=F_M, fill=FG)
        else:
            ok = st.sel == it["c"]
            d.text((10, 44), "Correct" if ok else "Not quite", font=F_L, fill=GOOD if ok else BAD)
            d.text((10, 72), f"Answer: {'ABCD'[it['c']]}  {it['o'][it['c']][0]}", font=F_M, fill=FG)
            y = 96
            if not ok:
                d.rectangle([8, y, W - 8, y + 44], fill=(42, 26, 29)); d.rectangle([8, y, 12, y + 44], fill=BAD)
                d.text((18, y + 3), "MISCONCEPTION", font=F_S, fill=(255, 156, 156))
                for k, ln in enumerate(wrap(d, it["o"][st.sel][1], F_M, W - 36)[:2]): d.text((18, y + 16 + k * 14), ln, font=F_M, fill=FG)
                y += 52
            for k, ln in enumerate(wrap(d, it["e"], F_M, W - 20)[:3]): d.text((10, y + k * 16), ln, font=F_M, fill=(213, 220, 229))
            if not ok and st.mode == "revision": d.text((10, 190), "+ Added to Mentor Study queue", font=F_S, fill=AMBER)
    elif s == "result":
        tot = sum(1 for x in SETS[st.mode] if x["t"] == "q")
        d.text((W // 2, 70), "SESSION DONE", font=F_S, fill=DIM, anchor="mm")
        d.text((W // 2, 110), f"{st.right}/{tot}", font=font(48), fill=AMBER, anchor="mm")
        d.text((W // 2, 150), "Misses sent to Mentor Study." if st.mode == "revision" and st.wrong else "Wrong answers show in Diagnostics.", font=F_S, fill=(213, 220, 229), anchor="mm")
    elif s == "diag":
        d.text((10, top - 2), ["Questions solved", "Weak concepts", "Study suggestions"][st.page] + " (sample)", font=F_S, fill=DIM)
        if st.page == 0:
            for i, (n, c, col) in enumerate([(14, "solved", FG), (9, "correct", GOOD), (5, "wrong", BAD)]):
                x = 8 + i * 104
                d.rectangle([x, 50, x + 98, 110], fill=PANEL); d.text((x + 49, 74), str(n), font=F_L, fill=col, anchor="mm"); d.text((x + 49, 98), c, font=F_S, fill=DIM, anchor="mm")
            d.rectangle([8, 124, 8 + 190, 136], fill=GOOD); d.rectangle([198, 124, 312, 136], fill=BAD)
            d.text((10, 148), "64% accuracy this week", font=F_M, fill=FG)
        elif st.page == 1:
            for i, (n, pct, slip) in enumerate(WEAK):
                y = 46 + i * 52
                d.text((10, y), n, font=F_M, fill=FG); d.text((W - 10, y), f"{pct}%", font=F_M, fill=(255, 156, 156), anchor="ra")
                d.rectangle([10, y + 18, W - 10, y + 26], fill=LINE); d.rectangle([10, y + 18, 10 + (W - 20) * pct // 100, y + 26], fill=BAD if pct < 50 else AMBER)
                d.text((10, y + 30), "slip: " + slip, font=F_S, fill=DIM)
        else:
            for k, ln in enumerate(["1. Revisit brackets first", "   with Mentor Study.", "2. Retry 3 mixed x / + sums.", "3. Revision unlocks at 80%."]):
                d.text((10, 50 + k * 22), ln, font=F_M, fill=(213, 220, 229))

    # footer hint bar
    d.rectangle([0, H - 22, W, H], fill=PANEL); d.line([0, H - 22, W, H - 22], fill=LINE)
    for i, (k, h) in enumerate(zip("LMR", hint_for(st))):
        d.text((6 + i * 107, H - 17), k, font=F_M, fill=AMBER); d.text((20 + i * 107, H - 16), h, font=F_S, fill=DIM)
    return im


class FB:
    def __init__(self, dev):
        self.dev = dev; name = os.path.basename(dev)
        base = f"/sys/class/graphics/{name}"
        self.w, self.h = (int(x) for x in open(f"{base}/virtual_size").read().strip().split(","))
        self.bpp = int(open(f"{base}/bits_per_pixel").read())
        self.f = open(dev, "wb", buffering=0)

    def show(self, im):
        im = im.resize((self.w, self.h))
        if self.bpp == 16:
            raw = bytearray(); px = im.tobytes()
            for i in range(0, len(px), 3):
                v = ((px[i] & 0xF8) << 8) | ((px[i + 1] & 0xFC) << 3) | (px[i + 2] >> 3)
                raw += v.to_bytes(2, "little")
            data = bytes(raw)
        else:
            data = im.convert("RGBA").tobytes("raw", "BGRA")
        self.f.seek(0); self.f.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fb", default="/dev/fb1"); ap.add_argument("--png"); ap.add_argument("--keys")
    a = ap.parse_args()
    st = State(); out = None if a.png else FB(a.fb)

    def draw():
        im = render(st)
        if a.png: im.resize((W * 2, H * 2), Image.NEAREST).save(a.png)
        else: out.show(im)

    if a.keys:  # replay mode, for dev without hardware
        for k in a.keys.lower():
            st.press(k)
            if st.screen == "ocr": st.ocr_at = 0; st.tick()
        draw(); print("screen:", st.screen); return

    draw()
    fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    def watcher():
        while True:
            time.sleep(0.2)
            if st.tick(): draw()
    threading.Thread(target=watcher, daemon=True).start()
    try:
        while True:
            k = sys.stdin.read(1).lower()
            if k in ("q", "\x03"): break
            if k in "lmr" and k: st.press(k); draw()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


if __name__ == "__main__":
    main()
