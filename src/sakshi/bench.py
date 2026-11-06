"""Benchmark (build map T18): the first TRUE speed and memory numbers, replacing every [ESTIMATE].

Runs `prepare` several times and reports medians and extremes with n. With n this small a "p95" is just the
slowest run, so it is reported as `max` and n is always shown.
"""
from __future__ import annotations

import json

from .metrics import capture_env
from .pipeline import prepare


def percentile(vals: list[float], p: float) -> float | None:
    """Nearest-rank percentile. Returns None for an empty list."""
    if not vals:
        return None
    s = sorted(vals)
    k = max(0, min(len(s) - 1, int(round(p / 100 * len(s) + 0.5)) - 1))
    return s[k]


def _stats(vals: list[float]) -> dict:
    v = [x for x in vals if x is not None]
    return {"n": len(v), "min": min(v) if v else None, "median": percentile(v, 50), "max": max(v) if v else None}


def attempts_of(run) -> list[dict]:
    a = [at for it in run.items for at in it.attempts]
    a += [at for s in run.summary.get("sentences", []) for at in s.get("attempts", [])]
    return a


def bench(passage: str, backend, runs: int = 3, warmup: bool = True, **kw) -> dict:
    """`warmup` does one throwaway run first (the first call is slower: caches, page-ins) and says so."""
    if warmup:
        prepare(passage, backend, **kw)
    results = [prepare(passage, backend, **kw) for _ in range(runs)]
    att = [a for r in results for a in attempts_of(r)]
    new_tok = sum(a["new_tokens"] or 0 for a in att)
    speeds = [(a["tokens_per_s"], a["new_tokens"] or 0) for a in att if a.get("tokens_per_s")]
    weighted = (sum(s * w for s, w in speeds) / sum(w for _, w in speeds)) if speeds and sum(w for _, w in speeds) else None
    last = results[-1]
    return {
        "runs": runs, "warmup_run_discarded": warmup, "gate": last.gate["status"],
        "total_s": _stats([r.timings["total_s"] for r in results]),
        "summary_s": _stats([r.timings["summary_s"] for r in results]),
        "questions_s": _stats([r.timings["stems_s"] for r in results]),
        "model_calls_per_run": _stats([r.timings["model_calls"] for r in results]),
        "prompt_tokens_total": sum(a["prompt_tokens"] or 0 for a in att), "generated_tokens_total": new_tok,
        "decode_tokens_per_s_weighted": round(weighted, 2) if weighted else None,
        "ttft_ms": _stats([a["ttft_ms"] for a in att]),
        "model_load_s": last.backend.get("load_s"), "model": last.backend,
        "counts_last_run": last.counts, "env": capture_env(),
        "note": "n is small: 'max' is the slowest run, not a true p95. Peak memory includes torch when run in-process.",
    }


def render(b: dict) -> str:
    def f(s, unit="s"):
        return "not measured" if not s or s["median"] is None else f"median {s['median']:.2f}{unit}, min {s['min']:.2f}, max {s['max']:.2f} (n={s['n']})"
    lines = [f"Runs: {b['runs']} (warm-up run discarded: {b['warmup_run_discarded']})",
             f"Total time per passage:  {f(b['total_s'])}",
             f"  summary:               {f(b['summary_s'])}", f"  questions:             {f(b['questions_s'])}",
             f"Model calls per run:     {f(b['model_calls_per_run'], '')}",
             f"Decode speed:            {b['decode_tokens_per_s_weighted']} tokens/s (weighted by tokens)",
             f"Time to first token:     {f(b['ttft_ms'], ' ms')}",
             f"Model load:              {b['model_load_s']} s",
             f"Peak memory:             {b['env']['peak_rss_mb']} MB ({b['env']['peak_rss_what']})",
             f"Network:                 {b['env']['network']['status']}"]
    th = b["env"].get("throttle")
    if th is not None:
        lines.append(f"Throttling:              {'none' if th['clean'] else ', '.join(th['flags'])} ({th['raw']})")
    lines.append(b["note"])
    return "\n".join(lines)


def save(b: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(b, f, indent=2, ensure_ascii=False)
