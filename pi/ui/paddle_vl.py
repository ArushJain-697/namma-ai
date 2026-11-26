"""PaddleOCR-VL (0.9B vision-language OCR model) through llama.cpp's llama-server, fully offline.

The server is started once (model load ~2-5 s, ~2 GB RAM) and every page is one HTTP request to localhost.
Used when the fast line model (PP-OCRv6) is unsure: a blurry or far-away photo. See docs/JUDGE_BRIEF.md.
Speed: ~8 s per page on an Apple M4 GPU, but 271 s on the M4's CPU alone (the vision encoder runs at ~3 tokens/s),
so it is OFF on the Pi 5 (CPU only) unless SAKSHI_OCR_VL=auto; meant for a board with a GPU or NPU.

    SAKSHI_VL_DIR    folder with PaddleOCR-VL-1.5.gguf + PaddleOCR-VL-1.5-mmproj.gguf (default ~/models/paddleocr-vl)
    SAKSHI_VL_PORT   default 8091
    SAKSHI_VL_NGL    layers on the GPU (default 0 = CPU only, as on the Pi)
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

DIR = Path(os.environ.get("SAKSHI_VL_DIR", str(Path.home() / "models" / "paddleocr-vl")))
PORT = int(os.environ.get("SAKSHI_VL_PORT", "8091"))
MAX_SIDE = int(os.environ.get("SAKSHI_VL_MAX_SIDE", "1280"))


class VLServer:
    def __init__(self, model_dir: Path = DIR, port: int = PORT, threads: int | None = None, ngl: int | None = None):
        self.dir, self.port = Path(model_dir), port
        self.threads = threads or int(os.environ.get("SAKSHI_VL_THREADS", "4"))
        self.ngl = int(os.environ.get("SAKSHI_VL_NGL", "0")) if ngl is None else ngl
        self.proc, self.error = None, None

    def available(self) -> bool:
        exe = os.environ.get("SAKSHI_LLAMA_SERVER") or shutil.which("llama-server")
        return bool(exe) and os.path.exists(exe) and any(self.dir.glob("*mmproj*.gguf"))

    def start(self, wait: float = 120.0) -> bool:
        if self.proc and self.proc.poll() is None:
            return True
        if not self.available():
            self.error = f"llama-server or the model files in {self.dir} not found"
            return False
        model = next(p for p in sorted(self.dir.glob("*.gguf")) if "mmproj" not in p.name)
        mmproj = next(iter(sorted(self.dir.glob("*mmproj*.gguf"))))
        cmd = [os.environ.get("SAKSHI_LLAMA_SERVER") or shutil.which("llama-server"), "-m", str(model), "--mmproj", str(mmproj), "--jinja", "--temp", "0",
               "--host", "127.0.0.1", "--port", str(self.port), "-t", str(self.threads), "-ngl", str(self.ngl),
               "-c", "4096", "--no-webui"]
        if self.ngl == 0:
            cmd.append("--no-mmproj-offload")
        log = open(os.environ.get("SAKSHI_VL_LOG", "/tmp/sakshi_vl.log"), "ab")
        self.proc = subprocess.Popen(cmd, stdout=log, stderr=log)
        t0 = time.time()
        while time.time() - t0 < wait:
            if self.proc.poll() is not None:
                self.error = "llama-server exited; see /tmp/sakshi_vl.log"
                return False
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=1) as r:
                    if r.status == 200:
                        return True
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.5)
        self.error = "llama-server did not become ready"
        return False

    def read(self, frame, box=None, max_tokens: int = 900, timeout: float | None = None) -> str:
        """BGR frame -> page text. box = (x0, y0, x1, y1) crops to the text first (page_ocr.text_region). The image
        is shrunk so its long side is MAX_SIDE: every 28x28 pixels is one token the CPU must encode."""
        import cv2
        timeout = timeout or float(os.environ.get("SAKSHI_VL_TIMEOUT", "120"))  # then the line model's text is kept
        if not self.start():
            raise RuntimeError(self.error)
        if box is not None:
            x0, y0, x1, y1 = box
            frame = frame[y0:y1, x0:x1]
        h, w = frame.shape[:2]
        s = min(1.0, MAX_SIDE / max(h, w))
        if s < 1:
            frame = cv2.resize(frame, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        b64 = base64.b64encode(jpg.tobytes()).decode()
        body = {"messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": "OCR:"}]}],
            "temperature": 0, "max_tokens": max_tokens}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read())
        return out["choices"][0]["message"]["content"] or ""

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
        self.proc = None


_SERVER: VLServer | None = None


def to_text(raw: str) -> str:
    import page_ocr
    return page_ocr.drop_repeats(page_ocr.join_lines([page_ocr.clean_line(l) for l in raw.splitlines()]))


def read_page_vl(frame, box=None) -> str:
    """Module-level helper for scripts/ocr_bench.py: one shared server, text joined into running text."""
    global _SERVER
    if _SERVER is None:
        _SERVER = VLServer()
    return to_text(_SERVER.read(frame, box=box))
