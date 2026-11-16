# Sakshi: an offline tutor that diagnoses, not just scores

**Winner, Namma AI Hackathon 2026** (Arm × IIIT Bangalore × NASSCOM), Problem Statement 1: AI for Inclusive Education.

A student studying a textbook page alone has no way to check whether she understood it. Quizzes give a score; Sakshi
names the **belief behind a wrong answer**, teaches the fix, steps down to the idea underneath, climbs back up only
when she has it, and brings the belief back on later days. It runs on a **Raspberry Pi 5 with the network off**.

- **GURU-0.6B**, our quiz model: Qwen3-0.6B fine-tuned with LoRA, run with **ExecuTorch** (4-bit, XNNPACK) on the Arm CPU.
- **Misconception graph**: 4,080 student misconceptions, 5,585 concepts, 120 root beliefs, 258 Class 6-10 topics.
- **Learning engine**: Bayesian diagnosis, Bayesian Knowledge Tracing, a prerequisite-graph walk, FSRS-6 revision.
- **Measured on the Pi 5**: summary + 3 questions in 57.9 s; 15.7 s per question while the child answers; 3.2 GB peak.

## How it works

```
passage (camera + OCR, or a saved page)
  -> summary            plain Qwen3-0.6B, one own-words sentence per third of the passage
  -> key sentence       picked by code, never by the model
  -> question + answer  GURU job Q
  -> 3 wrong answers    GURU job W
  -> checks             no giveaways, no duplicates, a second model must agree on the answer
  -> misconception      each wrong option linked to the graph: embedding shortlist -> NLI rerank -> abstain if unsure
  -> session            Bayes picks the belief, BKT tracks learning, walk down / climb up, FSRS schedules revision
```

Questions stream: the next one is written while the child answers the current one.

## Run it

**Raspberry Pi 5 (the device):** offline install with `pi/install.sh`, check with `pi/test.sh`, then
`~/start_sakshi.sh` (screen + three buttons). Put passages in `~/passages` with `pi/send_passages.sh`.
Checklist: `pi/CHECKLIST.md`.

**Any machine, one program:**
```bash
python scripts/sakshi_app.py study passage.txt      # summary, streamed questions, adaptive session
python scripts/sakshi_app.py review                 # a later day: re-check misconceptions, follow the graph
```

**Models:** download from the [GURU-0.6B v1 release](https://github.com/ArushJain-697/namma-ai/releases/tag/guru-0.6b-v1)
(ExecuTorch `.pte` for the Pi, plus every LoRA adapter we trained).

**Tests:** `python -m pytest -q --ignore=tests/test_resident.py`

## Repository

| Path | What |
|---|---|
| `pi/` | Device: install and test scripts, screen UI (`pi/ui/sakshi.py`), passage upload |
| `scripts/sakshi_engine.py`, `sakshi_app.py`, `backup_quiz.py` | The engine behind the screen, the one-program app, the quiz pipeline |
| `src/sakshi/` | Library: model backends, misconception linking, retention engine (`retention/`) |
| `train/`, `scripts/make_*_dataset.py` | Fine-tuning and dataset building |
| `data/` | Misconception graph, training datasets, test passages |
| `results/` | Evaluation outputs behind the numbers we quote |
| `docs/` | `JUDGE_BRIEF.md` (every decision with evidence), `RETENTION_MATH.md`, `SUBMISSION.md`, `pitch/`, `history/` |
| `research_notes/` | Research behind the design choices |

## What we do not claim

No students have used it yet, so there is no learning-gain claim. The misconceptions were drafted by AI from research
on student errors and are not yet teacher-reviewed. A 0.6B model writes imperfect questions; the checks drop the
worst. English only for now. Details: `docs/JUDGE_BRIEF.md`.
