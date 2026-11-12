"""Resident model process behind a Unix socket (build map T20, red-team F4/F6).

One process holds the model, so the load cost is paid once. It can run inside an empty network namespace
(`unshare -n`): a pathname Unix socket lives on the FILESYSTEM, so clients outside the namespace can still reach it,
while the process itself has no network interface at all. That makes "the model has no network" literally true,
and the `probe_network` request lets the process report its own network state as evidence.

Protocol: one JSON object per line, request then response. ops: ping, info, generate, probe_network, shutdown.
The model is not thread-safe, so generation is serialised behind a lock.
"""
from __future__ import annotations

import json
import os
import socket
import threading
from dataclasses import asdict

from .backends.base import Backend, GenResult
from .metrics import network_status

MAX_SOCKET_PATH = 100  # sun_path is 108 bytes on Linux; stay under it


def probe_network(timeout: float = 1.0) -> dict:
    """What can THIS process see? Interfaces, default route, and a real TCP attempt that must fail."""
    try:
        with open("/proc/net/dev") as f:
            ifaces = [ln.split(":")[0].strip() for ln in f.read().splitlines()[2:] if ":" in ln]
    except OSError:
        ifaces = None
    net = network_status()
    tcp = "not attempted"
    try:
        s = socket.create_connection(("1.1.1.1", 53), timeout=timeout)
        s.close()
        tcp = "CONNECTED"
    except OSError as e:
        tcp = f"failed ({e.__class__.__name__})"
    isolated = (ifaces is not None and set(ifaces) <= {"lo"} and net.get("default_route") is False and tcp.startswith("failed"))
    return {"interfaces": ifaces, "network": net.get("status"), "default_route": net.get("default_route"),
            "tcp_probe_1.1.1.1:53": tcp, "isolated": bool(isolated), "pid": os.getpid()}


class ResidentServer:
    def __init__(self, backend: Backend, path: str):
        if len(path.encode()) > MAX_SOCKET_PATH:
            raise ValueError(f"socket path too long ({len(path.encode())} bytes, max {MAX_SOCKET_PATH}): {path}")
        self.backend, self.path = backend, path
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self.sock: socket.socket | None = None

    def handle(self, req: dict) -> dict:
        op = req.get("op")
        if op == "ping":
            return {"ok": True}
        if op == "info":
            return {"ok": True, "info": self.backend.info()}
        if op == "generate":
            with self.lock:
                r = self.backend.generate(req["prompt"], int(req.get("max_new_tokens", 64)), float(req.get("temperature", 0.0)),
                                          req.get("seed"), req.get("task"), req.get("payload"))
            return {"ok": True, "result": asdict(r)}
        if op == "probe_network":
            return {"ok": True, "probe": probe_network()}
        if op == "shutdown":
            self._stop.set()
            return {"ok": True}
        return {"ok": False, "error": f"unknown op {op!r}"}

    def _serve_conn(self, conn: socket.socket) -> None:
        with conn, conn.makefile("rwb") as f:
            for line in f:
                try:
                    resp = self.handle(json.loads(line))
                except Exception as e:  # never let one bad request kill the model process
                    resp = {"ok": False, "error": f"{type(e).__name__}: {e}"}
                f.write((json.dumps(resp) + "\n").encode())
                f.flush()
                if self._stop.is_set():
                    break

    def start(self) -> None:
        """Bind and listen (separate from serving so tests and the CLI can signal readiness)."""
        if os.path.exists(self.path):
            os.unlink(self.path)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.path)
        os.chmod(self.path, 0o660)
        self.sock.listen(8)
        self.sock.settimeout(0.2)

    def serve_forever(self) -> None:
        assert self.sock is not None, "call start() first"
        while not self._stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._serve_conn, args=(conn,), daemon=True).start()
        self.close()

    def close(self) -> None:
        self._stop.set()
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        try:
            os.unlink(self.path)
        except OSError:
            pass


class ResidentClient(Backend):
    """A Backend that forwards to a resident process, so the whole pipeline can use it unchanged."""
    name = "resident"

    def __init__(self, path: str, timeout: float = 600.0):
        self.path = path
        self._lock = threading.Lock()
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect(path)
        self._f = self._sock.makefile("rwb")
        served = self._call({"op": "info"})["info"]  # build prompts in the format of the model the process holds
        self.chat_format = served.get("chat_format", "llama3")
        self.bos_in_prompt = bool(served.get("bos_in_prompt", False))

    def _call(self, req: dict) -> dict:
        with self._lock:
            self._f.write((json.dumps(req) + "\n").encode())
            self._f.flush()
            line = self._f.readline()
        if not line:
            raise ConnectionError("the resident model process closed the connection")
        resp = json.loads(line)
        if not resp.get("ok"):
            raise RuntimeError(f"resident process error: {resp.get('error')}")
        return resp

    def generate(self, prompt, max_new_tokens=64, temperature=0.0, seed=None, task=None, payload=None) -> GenResult:
        r = self._call({"op": "generate", "prompt": prompt, "max_new_tokens": max_new_tokens, "temperature": temperature,
                        "seed": seed, "task": task, "payload": payload})["result"]
        return GenResult(**r)

    def info(self) -> dict:
        return {**self._call({"op": "info"})["info"], "resident_socket": self.path}

    def ping(self) -> bool:
        return bool(self._call({"op": "ping"}).get("ok"))

    def probe_network(self) -> dict:
        return self._call({"op": "probe_network"})["probe"]

    def shutdown(self) -> None:
        try:
            self._call({"op": "shutdown"})
        except (ConnectionError, OSError):
            pass

    def close(self) -> None:
        try:
            self._f.close()
            self._sock.close()
        except OSError:
            pass
