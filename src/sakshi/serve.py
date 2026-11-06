"""Classroom Hotspot server (build map T30): serve a PREPARED quiz to phones over the Pi's own Wi-Fi.

The model is not involved here: it already ran. This is a static page plus a JSON quiz, standard library only.
Answers are checked in the browser against the code-picked key. The only thing a phone ever sends back is the
sentence NUMBER of a missed question, counted anonymously in memory (never written to disk, no identifiers).
This is the spectator layer, not the deliverable: the terminal quiz meets every requirement of the brief.
"""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .pipeline import Run, visible_items
from .quiz import HEADER
from .text import split_sentences

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web")


def build_quiz_payload(run: Run, include_amber: bool = False) -> dict:
    """What the phone page needs. Keys are included because answers are checked in the browser (a study aid, not a test)."""
    items = []
    for it in visible_items(run, include_amber):
        items.append({"id": it.id, "stem": it.stem, "options": it.options, "key": it.key, "witness": it.witness,
                      "witness_idx": it.witness_idx, "tier": it.tier,
                      "reserve": ({k: it.reserve[k] for k in ("stem", "key", "options", "witness", "witness_idx")} if it.reserve else None)})
    return {"header": HEADER, "passage_sentences": split_sentences(run.passage), "summary": run.summary.get("text", ""), "items": items}


class RoomCounts:
    """Anonymous miss counts per sentence number. In memory only."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counts: dict[int, int] = {}

    def add(self, sentence_no: int) -> None:
        with self._lock:
            self._counts[sentence_no] = self._counts.get(sentence_no, 0) + 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {str(k): v for k, v in sorted(self._counts.items())}


def make_handler(payload: dict, counts: RoomCounts, web_dir: str = WEB_DIR):
    body = json.dumps(payload).encode()

    class Handler(BaseHTTPRequestHandler):
        server_version = "SakshiRoom"

        def _send(self, code: int, data: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            path = self.path.split("?")[0]
            if path in ("/", "/index.html"):
                with open(os.path.join(web_dir, "index.html"), "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            if path == "/quiz.json":
                return self._send(200, body, "application/json")
            if path == "/room":
                return self._send(200, json.dumps({"misses_by_sentence": counts.snapshot()}).encode(), "application/json")
            if path == "/healthz":
                return self._send(200, b"ok", "text/plain")
            self._send(404, b"not found", "text/plain")

        def do_POST(self):  # noqa: N802
            if self.path != "/miss":
                return self._send(404, b"not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                sentence = int(json.loads(self.rfile.read(min(n, 256))).get("sentence"))
                if 1 <= sentence <= len(payload["passage_sentences"]):
                    counts.add(sentence)
                    return self._send(204, b"", "text/plain")
            except (ValueError, TypeError, json.JSONDecodeError):
                pass
            self._send(400, b"bad request", "text/plain")

        def log_message(self, *a):  # no request logging: nothing about who connected is kept
            pass

    return Handler


def make_server(run: Run, host: str = "0.0.0.0", port: int = 8000, include_amber: bool = False,
                counts: RoomCounts | None = None) -> tuple[ThreadingHTTPServer, RoomCounts]:
    counts = counts or RoomCounts()
    # 0.0.0.0 so phones on the Pi's own Wi-Fi can reach it; 127.0.0.1 would silently serve nobody but the Pi itself.
    return ThreadingHTTPServer((host, port), make_handler(build_quiz_payload(run, include_amber), counts)), counts
