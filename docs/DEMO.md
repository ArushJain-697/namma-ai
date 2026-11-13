# Demo script and failure runbook

*Rewritten 13 Nov 2026 for the current design (diagnostic quiz from the misconception graph). The 4 Nov version
(fill-in-the-blank fallback, "witness" framing) is retired. Not yet rehearsed with a stopwatch or on a Pi 5. Pitch
facts and Q&A: `docs/PITCH.md`.*

## Which quiz command on the day (decide at the venue, before judging)

| Situation | Command (on the Pi) |
|---|---|
| Fine-tuned model ready AND its Job 6 numbers beat the backup (sensible > 19%) | `bash ~/pi-kit/test.sh ~/passage.txt` (runs `sakshi run`: summary, quiz, run card) |
| Otherwise: the backup (plain model, v2) | `~/sakshi-venv/bin/python scripts/backup_quiz.py demo ~/passage.txt` (summary, quiz, run card) |

Start the run **before** speaking (it takes about a minute on the Pi; measure it in rehearsal). Never claim the
backup's questions are good: Sonnet rated 19% of them sensible.

## The 3:00 arc

| Time | Beat | Screen / command | Say (honest version) |
|---|---|---|---|
| 0:00 | **Hook** | Pi terminal, nothing else | "A Class 8 student in a rural government school finishes today's science passage. Only 67.5% of Class 8 students in rural government schools can read a Class 2 text (ASER 2024). Reading the words is not understanding them, and she has no internet to check." |
| 0:15 | **Offline proof** (live toggle) | Unplug Ethernet / Wi-Fi off, then `bash scripts/prove_offline.sh demo` | "No route out. If it said UNKNOWN I would tell you." |
| 0:25 | **The organisers' passage goes in** (already running since before the talk) | The run's output scrolling | "A 0.6-billion-parameter model on this Pi, through ExecuTorch, 4-bit weights. No cloud." |
| 0:40 | **The idea** (while it finishes) | `data/misconceptions/graph/viewer.html` on the laptop | "Everyone makes quizzes that give a score. Ours gives a diagnosis: every wrong option is a real student belief, from a graph of 3,398 misconceptions across Class 6 to 10, grouped into 120 root beliefs." |
| 1:10 | **The output** (deliverable) | Summary, then the questions with the passage sentence each answer comes from | "Code picks the sentence; the model writes the question; the wrong options come from the graph; the model must answer its own question correctly or the question is dropped." |
| 1:40 | **A judge answers** | Ask a judge to pick an answer to Q1 (terminal `study`, or read aloud) | If wrong: "That option is the belief '...' — this is what a teacher learns from a wrong answer." |
| 2:10 | **Run card** (deliverable) | The run card | Read time, model, size, peak memory. "Memory was 2.5 GB; we cut it to 1.7 GB by sizing the model's memory to what a quiz needs, with identical answers." |
| 2:25 | **Impact** (deliverable) | One example from the organisers' passage | One question from their passage + the belief behind one wrong option + who it helps |
| 2:45 | **Confess and close** | — | "Not tested with students yet; the misconceptions were drafted by AI from research and not yet reviewed by teachers; a small model makes imperfect questions, which is why every answer shows its sentence. Next: one school pilot." |

**60-second table walkaround:** offline proof (10 s) → one question + the belief behind a wrong option (30 s) →
run card (20 s).

## Say it before they ask
- Name anything saved or prepared ("this is a saved run from 10 minutes ago").
- The Pi numbers are from today; earlier numbers are from a Mac and an Arduino UNO Q.
- Do NOT say the quiz beats word-spotting (not supported by our own test, see `docs/PITCH.md` section 3).

## Failure runbook

| What breaks | Do this | Say |
|---|---|---|
| "Illegal instruction" on load | `.kit_model` -> portable model (`pi-kit/CHECKLIST.md`) | "Older chip path; slower but same answers." |
| Model won't load at all | Show the saved run from rehearsal (`results/pi_run.json` + its printout) | "The model didn't load; this is a saved run from earlier today." |
| Run slower than the slot | Start it before the talk; if still running, show the saved run and the live elapsed time | |
| Fewer than 3 questions | Run the backup command on the same passage, or show the saved run | "The checks dropped questions rather than show bad ones." |
| A question is clearly wrong on screen | Say so | "That one slipped past the checks; this is a 0.6B model." |
| prove_offline says NOT OFFLINE / UNKNOWN | Unplug again and re-run; if still not, **do not claim offline** | Say so plainly |
| Pi dies | Backup recording | "This is a recording of a full run." |

## Before the demo (checklist)
- [ ] Decide the quiz command (table at the top) from the teammate's Job 6 numbers.
- [ ] Re-pack `pi-kit/namma-ai.tar` with the final code, model and `data/misconceptions/index/` (rebuilt 13 Nov after the graph merge; not in git).
- [ ] `QUICK=1 bash test.sh` on the Pi, then one full run; write the numbers into `docs/SUBMISSION.md`.
- [ ] Two stopwatch rehearsals; one backup recording of a clean full run.
- [ ] Fan on; record the second run, not the first.
- [ ] Graph viewer opens offline on the laptop.
