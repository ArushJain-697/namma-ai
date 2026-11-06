"""Layer 8: run card and environment capture (deliverable 4 of the brief).

The brief asks for approximate inference time, the model used, and model size OR memory
"where measurable". The run card is that requirement and nothing more. Every number the pitch
quotes must come from `metrics.json`, written here, never typed by hand.

Honest limits, stated in the card itself:
  * peak memory is this PROCESS's peak RSS (ru_maxrss). Importing torch inflates it. A clean
    model-only figure needs llama_main (build map T19) and must be labelled as such.
  * "network OFF" means no default route. It is evidence, not a proof; scripts/prove_offline.sh
    saves the stronger evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys

_THROTTLE_BITS = {
    0x1: "under-voltage now", 0x2: "frequency capped now", 0x4: "throttled now", 0x8: "soft temperature limit now",
    0x10000: "under-voltage since boot", 0x20000: "frequency capped since boot",
    0x40000: "throttled since boot", 0x80000: "soft temperature limit since boot",
}


def peak_rss_mb() -> float:
    """Peak resident memory of this process in MB (ru_maxrss: KB on Linux, bytes on macOS)."""
    v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(v / (1024 * 1024 if sys.platform == "darwin" else 1024), 1)


def network_status(route_path: str = "/proc/net/route") -> dict:
    """Is there a default route? Parses /proc/net/route (Linux). Unknown elsewhere."""
    try:
        with open(route_path) as f:
            lines = f.read().strip().splitlines()[1:]
    except OSError:
        return {"known": False, "default_route": None, "status": "unknown (no /proc/net/route)"}
    defaults = [ln.split()[0] for ln in lines if len(ln.split()) > 1 and ln.split()[1] == "00000000"]
    if defaults:
        return {"known": True, "default_route": True, "via": defaults, "status": f"ON (default route via {', '.join(defaults)})"}
    return {"known": True, "default_route": False, "via": [], "status": "OFF (no default route)"}


def _vcgencmd(*args: str) -> str | None:
    try:
        out = subprocess.run(["vcgencmd", *args], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def throttle_status() -> dict | None:
    """Raspberry Pi throttling flags, or None when vcgencmd is not available (not a Pi)."""
    raw = _vcgencmd("get_throttled")
    if not raw or "=" not in raw:
        return None
    try:
        val = int(raw.split("=", 1)[1], 16)
    except ValueError:
        return None
    return {"raw": hex(val), "flags": [name for bit, name in _THROTTLE_BITS.items() if val & bit], "clean": val == 0}


def temp_c() -> float | None:
    raw = _vcgencmd("measure_temp")
    if raw and "=" in raw:
        try:
            return float(raw.split("=")[1].replace("'C", ""))
        except ValueError:
            pass
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def file_sha256(path: str, chunk: int = 1 << 20) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while block := f.read(chunk):
                h.update(block)
        return h.hexdigest()
    except OSError:
        return None


def capture_env() -> dict:
    return {"peak_rss_mb": peak_rss_mb(), "peak_rss_what": "this process (ru_maxrss)", "network": network_status(),
            "throttle": throttle_status(), "temp_c": temp_c(), "python": platform.python_version(),
            "machine": platform.machine(), "system": platform.system()}


def run_card(run) -> str:
    """Four lines, as in the bible. Duck-typed on run.backend / run.timings / run.env."""
    b, t, e = run.backend, run.timings, getattr(run, "env", {}) or {}
    sha = b.get("sha256")
    model = f"{b.get('name', '?')}" + (f" ({os.path.basename(b['model_path'])}, sha256 {sha[:8]}…)" if b.get("model_path") and sha else "")
    size = b.get("model_bytes") or 0
    size_s = f"{size / (1024 * 1024):.0f} MB on disk" if size else "n/a (no model file)"
    peak = e.get("peak_rss_mb")
    peak_s = f"{peak:.0f} MB ({e.get('peak_rss_what', 'this process')})" if peak is not None else "not recorded"
    net = (e.get("network") or {}).get("status", "not recorded")
    time_s = (f"{t.get('total_s', 0):.1f} s total  (summary {t.get('summary_s', 0):.1f} s, questions {t.get('stems_s', 0):.1f} s, "
              f"model load {t.get('load_s', 0) or 0:.1f} s)   network: {net}")
    lines = [f"Model:        {model}", f"Model size:   {size_s}", f"Peak memory:  {peak_s}", f"Time:         {time_s}"]
    th = e.get("throttle")
    if th is not None:
        lines.append(f"Throttling:   {'none' if th['clean'] else ', '.join(th['flags'])} ({th['raw']})"
                     + (f", {e['temp_c']} °C" if e.get("temp_c") is not None else ""))
    return "\n".join(lines)


def metrics_dict(run) -> dict:
    """Everything the pitch may quote, in one place."""
    return {"backend": run.backend, "timings": run.timings, "counts": run.counts, "env": getattr(run, "env", {}),
            "gate": run.gate, "summary_words": run.summary.get("word_count"), "version": run.version, "created": run.created}


def write_metrics(run, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics_dict(run), f, indent=2, ensure_ascii=False)
