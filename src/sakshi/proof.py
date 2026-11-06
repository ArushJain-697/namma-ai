"""Proof card (build map T28): rendered from the metrics files, never typed by hand.

Anything that has not been measured says "not measured". The caveat comes FIRST, before any number
(blueprint 7.11: say the caveat first, the number second).
"""
from __future__ import annotations

import json

from .cf_eval import CAVEAT


def _load(path: str | None) -> dict | None:
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _frac(k, n, ci=None) -> str:
    if not n:
        return "not measured"
    s = f"{k} of {n} ({k / n:.0%})"
    return s + (f", 95% CI {ci[0]:.0%} to {ci[1]:.0%}" if ci else "")


def _block(label: str, b: dict | None, key: str) -> str:
    if not b:
        return f"  {label}: not measured"
    return f"  {label}: {_frac(b.get(f'{key}_count', 0), b.get('n', 0), b.get('ci95'))}"


def render_card(cf: dict | None = None, run: dict | None = None, bench: dict | None = None) -> str:
    out = ["SAKSHI PROOF CARD"]
    names = [str((b or {}).get("name", "")) for b in list(((cf or {}).get("backends") or {}).values())
             + [(run or {}).get("backend"), (bench or {}).get("model")]]
    if any(n.startswith("stub") for n in names):
        out += ["*** SIMULATED: produced with a stub model, NOT a real model result. Do not quote any number below. ***"]
    real = sorted({n for n in names if n and not n.startswith("stub")})
    out += [f"Produced with: {', '.join(real) if real else 'not recorded'}",
            "Every number below is read from a metrics file. Anything missing says 'not measured'.", "",
            "CAVEAT FIRST: " + CAVEAT, ""]
    if not cf or not cf.get("splits"):
        out += ["Counterfactual Passage Test: not measured", ""]
    else:
        for split in ("dev", "heldout"):
            s = cf["splits"].get(split)
            if not s:
                continue
            label = "Dev" if split == "dev" else "Held-out (never filtered, never tuned on)"
            filt = " (filtered to facts that trapped the baseline)" if s.get("filtered_to_trapping_facts") else ""
            out.append(f"{label}{filt}: scored {s['n_scored']} of {s['n_total']} passages")
            out.append(_block("Baseline key followed MEMORY, targeted", s.get("A_targeted"), "memory"))
            out.append(_block("Baseline key followed MEMORY, grounded-prompt", s.get("A_grounded"), "memory"))
            fr = s.get("A_free") or {}
            cov = fr.get("coverage") or {}
            out.append(f"  Free-form baseline touched the planted sentence in {_frac(cov.get('covered', 0), cov.get('n', 0))}; "
                       f"of those, followed memory: {_frac(fr.get('memory_count', 0), fr.get('n', 0), fr.get('ci95'))}")
            sp = s.get("A_span_check") or {}
            out.append(f"  A plain 'is the answer in the passage?' check would have released "
                       f"{sp.get('released_by_a_plain_span_check', 'not measured')} of {sp.get('memory_answers', 'not measured')} memory answers")
            out.append(_block("Sakshi key followed the PASSAGE (by construction)", s.get("B_sakshi_key"), "passage"))
            out.append(_block("Sakshi summary contained the memory value", s.get("C_sakshi_summary_has_memory_value"), "memory"))
            out.append(_block("Whole-passage summary contained the memory value", s.get("C_whole_summary_has_memory_value"), "memory"))
            out.append("")
        out.append(f"Filter: {cf.get('filter', 'not recorded')}")
        out.append("")
    if run:
        b, t, e = run.get("backend", {}), run.get("timings", {}), run.get("env", {})
        out += ["Run card (from the last prepared run):",
                f"  Model: {b.get('name', 'not measured')}",
                f"  Size on disk: {(b.get('model_bytes') or 0) / 1e6:.0f} MB" if b.get("model_bytes") else "  Size on disk: not measured",
                f"  Time: {t['total_s']:.1f} s" if t.get("total_s") is not None else "  Time: not measured",
                f"  Peak memory: {e['peak_rss_mb']} MB ({e.get('peak_rss_what', '')})" if e.get("peak_rss_mb") is not None else "  Peak memory: not measured",
                f"  Network: {(e.get('network') or {}).get('status', 'not measured')}", ""]
    if bench:
        t = bench.get("total_s") or {}
        out += ["Benchmark:",
                f"  Time per passage: median {t['median']:.1f} s, max {t['max']:.1f} s (n={t['n']})" if t.get("median") is not None else "  Time per passage: not measured",
                f"  Decode speed: {bench.get('decode_tokens_per_s_weighted')} tokens/s" if bench.get("decode_tokens_per_s_weighted") else "  Decode speed: not measured", ""]
    out.append("Not tested: learning gains, use with students, Kannada, inference-level questions.")
    return "\n".join(out)


def render_files(cf_path=None, run_path=None, bench_path=None) -> str:
    return render_card(_load(cf_path), _load(run_path), _load(bench_path))
