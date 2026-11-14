#!/usr/bin/env python3
"""Bridge for the TFT UI (~/Sakshi/sakshi.py on the Pi): run the offline pipeline on one passage and print
progress markers, then the result as JSON. The UI runs this in its own process with ~/sakshi-venv, so the UI's
Python environment needs nothing from ExecuTorch.

  ~/sakshi-venv/bin/python scripts/study_json.py PASSAGE.txt [--questions 3] [--eight-bit]
stdout lines:  STAGE 1 (models loaded) / STAGE 2 (summary done) / QUESTION i (question i kept) /
               STAGE 3 (quiz done) / RESULT {json}   (or ERROR <message>)
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def say(s: str) -> None:
    print(s, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("passage")
    ap.add_argument("--questions", type=int, default=3)
    ap.add_argument("--eight-bit", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    try:
        import backup_quiz as bq
        from sakshi.generate import make_whole_summary
        models = ROOT / "models"
        quiz_dir = models / ("guru-0.6b-2job-8bit" if a.eight_bit else "guru-0.6b-2job")
        dot = any("asimddp" in l for l in open("/proc/cpuinfo")) if os.path.exists("/proc/cpuinfo") else True
        sum_dir = models / ("qwen3-0.6b-fast" if dot else "qwen3-0.6b-portable")
        if not sum_dir.exists():
            sum_dir = models / "qwen3-0.6b-8da4w"  # the Mac's name for the same model
        passage = Path(a.passage).read_text().strip()
        m, sm = bq.Model(quiz_dir), bq.Model(sum_dir)
        say("STAGE 1")
        t1 = time.time()
        summ = make_whole_summary(sm.b, passage, retries=0)
        say("STAGE 2")
        t2 = time.time()
        r = bq.quiz_2job(m, m, passage, n=a.questions, checker=sm)
        say("STAGE 3")
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (2**20 if sys.platform == "darwin" else 2**10)
        out = {
            "summary": summ.get("text") or "",
            "questions": [{"q": q["q"], "options": q["options"], "answer": q["answer"], "evidence": q["evidence"]}
                          for q in r["kept"]],
            "run_card": {"model": f"GURU-0.6B (fine-tuned Qwen3-0.6B), ExecuTorch, {quiz_dir.name}",
                         "summary_model": sum_dir.name,
                         "size_mb": round(os.path.getsize(quiz_dir / "model.pte") / 2**20),
                         "peak_mb": round(rss), "total_s": round(time.time() - t0, 1),
                         "summary_s": round(t2 - t1, 1), "quiz_s": round(time.time() - t2, 1),
                         "words": len(passage.split())},
        }
        say("RESULT " + json.dumps(out, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        say(f"ERROR {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
