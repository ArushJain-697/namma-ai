# Namma AI Hackathon: internal checklist

Follows the blueprint's flow (Part 11 timeline, Part 13 gates), adapted to this event.
Last updated: 4 Nov 2026 (bible v1.3: red-teamed, mock-judged). `[x]` done, `[~]` started or draft, `[ ]` not started.

Key dates: proposal **6 Nov** · finalists told by 11 Nov · live event **14 Nov** · winners 19 Nov.

## 0. Rules dossier
- [~] Scoring: no rubric is published. Closest wording is "practical implementation, measurable results and societal relevance".
- [x] Mandatory tech: ExecuTorch on Raspberry Pi, approved lightweight model, no cloud inference.
- [x] Mandatory deliverables for Problem 1 listed, and the full problem statement quoted verbatim in bible section 1.
- [x] Brief's wording mapped to design changes (student user, "short, understandable", "relevant", "study aid", light measurement).
- [x] Deliverables: project on GitHub, submitted through the challenge form.
- [x] Sponsors mapped: Arm, IIIT Bangalore, NASSCOM / AI CoE (CATS), UK Government (TSI), K-Tech.
- [x] Pre-written code allowed (Plan P), per the team on 4 Nov; confirm in writing, and whether reused open-source code is covered.
- [ ] Ask organisers: approved models; who supplies the Pi, which model **and RAM**; proposal contents; judging criteria; pre-written code and reuse rules (decides Plan P or Plan E); judge panel; demo format and length; passage delivery; power outlets; whether a no-uplink hotspot is allowed.
- [ ] Judge personas confirmed (currently inference only).

## A. Idea gate
- [~] Person, moment, cost: reframed student-first in v1.1 (Class 6-8 student studying alone, no internet at school). Your review needed.
- [~] One barrier in one line: "no timely, understandable way for a student to check their own understanding while studying, in a school with no internet".
- [x] Trap named and approved: the Fluent Wrong Answer Trap.
- [x] Category shift approved: everyone generates quizzes; we only release what traces back to the passage and refuse the rest.
- [ ] Sponsor tech load-bearing test written.
- [~] At least 3 independent signals beyond the model (validators being harvested).
- [~] "The AI is never allowed to decide ___" written (proposed: see bible).
- [~] Headline metric fixed (v1.2): Counterfactual Passage Test, script-scored, held-out half kept by the owner. Baseline and ablations specced.
- [x] Live proof toggle and judge part chosen (v1.2): unplug plus `unshare -n`; counterfactual evade-then-catch; judges take the quiz on their phones over the Classroom Hotspot; a judge edits a fact and one question regenerates.
- [ ] Answer to "isn't this just ___?" in one sentence.
- [~] Scorecard (12.2): v1.2 self-score 99 was generous; red-team-adjusted about 88, projected about 94 if tickets 8c, 8d, 8g pass.

## Research
- [x] Models, build and tuning, learning barrier, existing projects (first round).
- [x] Harvest agents: all six finished and folded into the bible.
- [ ] Sceptical triage of every claim (verified, verify first, skip).

## Proposal (6 Nov)
- [ ] Team type, size and education background from you.
- [ ] Eligibility and college nomination, if a student team.
- [ ] You write and submit the proposal.
- [ ] Only the Team Leader registers.

## B. Bible gate
- [x] Master bible v1 on the 12.3 skeleton (`MASTER_BIBLE.md`).
- [ ] Every layer has mechanism, worked example with real numbers, edge cases and test.
- [ ] Rubric mapping and competitor table.
- [ ] "What this is NOT" and "Considered and rejected".
- [x] 3 red-team rounds logged (23 flaws, `RED_TEAM_LOG.md`); mock judge scored 69/100 on the nearest public rubric, projected 77; lowest criterion (deployment) has a fix ticket (8g). Self-review only: get one outside human judge.
- [ ] Killer facts and 30-second hook.
- [ ] Status table: proven, not field-tested, pitch-only.
- [ ] Decision map and build map with cut list.

## C. Pre-event gate (by 13 Nov)
- [ ] Pi 5, active cooler, 64-bit Trixie, Linux x86_64 build machine.
- [ ] Toolchain proven end to end, in line with whatever the organisers say on pre-written code.
- [ ] First real measurement on a 300-word passage.
- [ ] Ticket 7b: 1B summaries simpler than the passage (readability recorded).
- [ ] Ticket 7c: relevance scoring picks no trivial answers in the top 3 on 5 dev passages.
- [ ] Ticket 8c: 16-20 counterfactual passages written; **baseline run with the passage in context** follows memory at least once in 3 tries per kept fact (dev half only). Go/no-go for the live trap beat.
- [ ] Ticket 8d: hotspot rehearsed with 5 phones (iPhone and Android), no uplink.
- [ ] Ticket 8e: USB-PD power bank and USB-C meter tested with the Pi 5; throttling checked.
- [ ] Ticket 8f: QR cards (WPA2 password) printed and scanned by a fresh phone.
- [ ] Ticket 8g: school-internet figure read at source; priced bill of materials; device-access question named.
- [ ] Ticket 8h: read Xie et al. 2023 and Meta's Llama 3.2 licence.
- [ ] Ticket 8i: resident model behind a Unix socket under `unshare -n` works on the Pi.
- [ ] Ticket 7b (both summary arms): witnessed vs whole-passage summary compared.
- [ ] Proof plan and `metrics.py` spec.
- [ ] Offline kit: binaries, model and tokenizer on local storage.
- [ ] Real student or teacher conversation (ticket 8b), or the proxy caveat ready.
- [ ] Roles set, including a held-out owner and a demo owner.
- [ ] Teammate guide; everyone can explain the trap.

## D. First working milestone (event day, hour 3)
- [ ] One end-to-end run on the real Pi, ending with the run card (time, model, size, memory).
- [ ] Student quiz mode shows the witness on a wrong answer, and the Reread Loop asks again from that sentence.
- [ ] Hour 4.5 check: counterfactual test and one-question regeneration working, or cut ablations and the room view.
- [ ] Hour 5.5 check: hotspot working, or fall back to the terminal quiz.
- [ ] Works with networking off.
- [ ] Nothing STRETCH started.

## E. Demo gate
- [ ] Hook, villain and trap beat scripted with timestamps.
- [ ] Proof toggle works three times in a row.
- [ ] Judge part tested on a stranger's phone (hotspot join, quiz, witness highlight) and the judge's edit timed.
- [ ] Proof card numbers come from the script.
- [ ] Held-out and dev numbers labelled separately.
- [ ] Impact explanation written from the organiser's passage (deliverable 5).
- [ ] Limits stated before anyone asks.
- [ ] Two stopwatch rehearsals; backup recording exists.

## F. Q&A gate
- [ ] Key numbers known by heart.
- [ ] Best negative result ready.
- [ ] "Why ExecuTorch and Arm?" answer ready.
- [ ] "What's next?" in one sentence.
- [ ] Every teammate gives the same answer to "what's simulated?"

## G. Red-team follow-ups (v1.3)
- [ ] One outside human mock judge (a teacher, and someone who has shipped on a Pi).
- [ ] One teacher or student conversation before the 6 Nov proposal.
- [ ] Plan P or Plan E chosen as soon as organisers answer; assume Plan E if silent by 11 Nov.
- [ ] One-page proposal drafted from v1.3 (barrier, group, how, the trap, measurements, deployment sketch with sourced figures).
- [ ] Negation-word check added to the summary support check.
