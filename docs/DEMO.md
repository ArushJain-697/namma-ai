# Demo script and failure runbook

*Draft 4 Nov 2026, from Master Bible section 11 (v1.3) and what was actually built. Timings are TARGETS: nothing here has been rehearsed on a Pi or with a stopwatch yet (build map T33). Rehearse with `bash scripts/demo.sh`; with no `BACKEND_ARGS` it uses the stub and says SIMULATED.*

## The 3:00 arc

| Time | Beat | Command / screen | Say (honest version) |
|---|---|---|---|
| 0:00 | **Hook.** One student, one passage, no internet. QR cards already on the table so judges can join the Wi-Fi during this and the next beat. | Pi, no slides | "A Class 7 student rereads today's passage. She can read every word and can't tell if she understood it. [Illustrative, or a real quote.]" |
| 0:15 | **Offline toggle.** Unplug Ethernet on camera. | `bash scripts/prove_offline.sh demo` | "No route out. The result line says so; if it says UNKNOWN I'd tell you." |
| 0:25 | **The villain (trap, shown).** A saved baseline failure next to Sakshi on the same sentence. | `python -m sakshi villain demo/villain.json` | "This is a SAVED run, chosen because the baseline failed. It answered from the model's memory, not the passage." |
| 1:00 | **Judges are the students.** Two pre-joined phones, or the terminal quiz. Get one wrong on purpose; the sentence lights up; a second question comes from that sentence. | `python -m sakshi serve RUN` or `study RUN` | "Every answer shows the sentence it came from." |
| 1:45 | **A judge plants the trap.** Sentences with a question are listed; the judge edits one. Only that question changes; the stale summary line is caught by the number check. | `python -m sakshi edit RUN --list` then `--sentence N --text '...'` | "Everything else is exactly as it was." |
| 2:15 | **Impact explanation (deliverable 5)** from the organiser's passage, with the run card on screen. | Terminal | Template in the bible, section 11 |
| 2:30 | **Proof card.** Caveat first, then numbers from the metrics file. | `python scripts/proof_card.py` | "These passages are built to expose the trap, so this is not the baseline's everyday rate." |
| 2:50 | **Close.** | | "No witness, no question. We haven't tested learning gains; that's the pilot." |

**60-second table walkaround:** the villain (20 s) -> a judge answers on their phone (30 s) -> run card (10 s).

## Say it before they ask
- Simulated or prepared things are named as such ("saved run", "prepared output").
- GREEN means "passed the rules and shows its sentence", not "correct".
- Sakshi's key following the passage is a **guarantee of the design** (code picks the key), not a model result; the summary is the real test.
- A plain "is the answer in the passage?" check also catches these planted facts (our own test says so); the design's value is that the key cannot be invented at all.
- No students have used it.

## Failure runbook

| What breaks | Do this | Say |
|---|---|---|
| Model won't load / `prepare` fails | Show the SAVED RUN (`results/*.json`) with `report` and `study` | "The model didn't load; this is a saved run from earlier." |
| Generation too slow | Start `prepare` before the talk; show true elapsed time from the run card | |
| Judge's edit too slow (>15 s measured) | Move the edit to Q&A | |
| Hotspot / phones fail | Judges play in the terminal (`study`); same beats | "The phone page is an extra; the terminal is the deliverable." |
| Prove-offline says NOT OFFLINE or UNKNOWN | Unplug, re-run; if still not, **do not claim offline** | Say so plainly |
| The trap doesn't fire live | Use the saved villain; if none exists, skip the beat and say why | |
| Pi dies | Backup recording | "This is a recording." |

## Before the demo
- [ ] `bash scripts/selfcheck.sh` green on the demo machine.
- [ ] Two full stopwatch rehearsals; backup recording exists.
- [ ] Saved villain made from a REAL trapping case (`scripts/save_villain.py` refuses otherwise).
- [ ] Hotspot tested with 5 phones (iPhone and Android), mobile data off; QR cards printed in advance.
- [ ] Proof card regenerated from the final metrics files; no number typed by hand.
