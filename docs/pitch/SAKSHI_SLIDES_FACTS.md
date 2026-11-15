# Sakshi + GURU-0.6B: every fact and number for the slides

*Namma AI Hackathon (Arm + IIIT Bangalore + NASSCOM), Problem Statement 1: AI for Inclusive Education.
Compiled 14 Nov 2026 from `docs/JUDGE_BRIEF.md` (main source), `docs/SUBMISSION.md`, `docs/RETENTION_MATH.md`,
`docs/gpu_session/*`, `docs/MISCONCEPTION_MAPPING_PLAN.md`, `docs/PITCH.md` and the build sessions.
Every number below came from a script run. Where a number is a Mac estimate, a GPU simulation or not yet measured on
the Pi, it says so. Slide rule from the team: no competition or company names on slides (see the internal Q&A note
at the end).*

---

## 0. The mic drop (one slide)

> **Everyone makes a quiz that gives a score. Sakshi gives a diagnosis.**
> When a child picks a wrong answer, Sakshi names the *belief* behind it, from a graph of **4,080 student
> misconceptions**, teaches the fix, walks down to the idea underneath, climbs back up only when the child has
> really got it, and brings the belief back on later days to check it is gone.
> All of it runs on a **Raspberry Pi 5 with the network unplugged**.

Three numbers to put big on that slide:
- **57.9 s**: summary + 3 questions on the Raspberry Pi 5, fully offline.
- **4,080** student misconceptions, **120** root beliefs, **5,585** concepts, **258** topics (Class 6-10).
- **Every wrong option** is linked to a named belief, **81%** of the time the right belief is in the top 3
  (measured on 3,647 labelled examples).

---

## 1. Names

- **Sakshi**: the offline learning assistant (the whole system and the device).
- **GURU-0.6B**: our quiz model. **G**rounded **U**nderstanding, **R**uns **U**nplugged.
  Always say: *fine-tuned from Qwen3-0.6B* (Apache 2.0).
- Slide line: "Sakshi runs GURU-0.6B, our quiz model fine-tuned from Qwen3-0.6B, offline on a Raspberry Pi."

---

## 2. The problem (barrier and learner)

**Barrier:** a student studying a textbook passage alone has no timely, understandable way to check whether they
understood it, and nobody to correct them when they did not. Without internet there is no tutor, search or AI app,
and the teacher has a whole class.

**Learner group:** Class 6-10 students in low-connectivity government schools, self-studying from English or
bilingual textbooks.

| Fact | Number | Source | Status |
|---|---|---|---|
| Class 8 rural govt-school students who can read a Class 2 text | **67.5%** | ASER 2024 national findings (primary PDF) | verified |
| Class 8 rural students who can do a 3-digit by 1-digit division | **45.8%** | ASER 2024 | verified |
| Indian schools with internet | **63.5%** (so ~1 in 3 has none) | UDISE+ 2024-25 (PIB release) | reported |
| Class 9 national average in science / social science | **~40%** | PARAKH 2024 (~21 lakh students) | reported |

Point to land: **reading the words is not understanding them**, and the children who most need a check are the ones
without internet.

Evidence that the approach works (research, not our results):

| Number | What | Source |
|---|---|---|
| **0.37 SD** | maths gain from an adaptive, misconception-driven tutor in 4.5 months (RCT, Delhi) | Muralidharan, Singh, Ganimian 2019 |
| **g ~ 0.41** | refutation texts ("you might think X; actually Y") correcting misconceptions | Tippett 2010 meta-analysis |
| **g ~ 0.5** | practice testing in classrooms | Adesope et al. 2017 |
| **d = 0.83** | interleaving problem types, 787 students, RCT | Rohrer et al. 2020 |

---

## 3. The five mandatory deliverables, all met

| Brief | How Sakshi meets it | Number |
|---|---|---|
| 1. Barrier + learner group + how the PoC helps | Section 2 | - |
| 2. One organiser passage, approved lightweight model, ExecuTorch, on the Pi | GURU-0.6B, ExecuTorch 1.5.1, XNNPACK, Arm Cortex-A76 CPU | runs on the Pi 5 8 GB |
| 3. Summary + at least 3 quiz questions (terminal OK) | Summary, 3+ multiple-choice questions, each with the passage sentence that proves the answer | **57.9 s** total on the Pi |
| 4. No cloud; report time, model, size, memory | Run card after every run; `scripts/prove_offline.sh` (to run at venue with Wi-Fi off) | 469 MB model, 2.7 GB peak with both models |
| 5. Impact explanation with one example from the passage | Filled from the organiser's passage on the day | template ready |

---

## 4. Raspberry Pi 5 measurements (the judged device, 14 Nov)

| Measurement | Value |
|---|---|
| Device | Raspberry Pi 5, **8 GB**, Debian 13, Python 3.13, ExecuTorch **1.5.1** |
| Offline install | `pi-kit/install.sh` OK; 6/6 model checksums OK; 216/217 tests passed |
| Reading speed (prefill) | **122 tokens/s** |
| Writing speed (decode) | **12.1 tokens/s** |
| Model load | **0.7 s** (one model), 3.0 s (both) |
| Peak memory, one model | **1.48 GB** |
| Peak memory, GURU + summary model | **2.7 GB** (of 8 GB) |
| **Summary + 3 questions (final setting)** | **57.9 s** = load 3.0 + summary 14.2 + quiz 40.7; 16 model calls, 3,012 tokens read, 539 written |
| Summary + 4 questions | 86 s |
| Before our stop-early fix | 147 s (same output) |
| Thermal | reached **84 °C** and throttled (0xe0008) without a fan, so use the active cooler |

**Speed fix found on the Pi (good slide):** the fine-tuned model never writes its end-of-turn token, so every call
ran to its cap (1,412 tokens). We watch the text as it streams and stop each call the moment the answer is complete.
**147 s → 86 s, identical output.** Going from two summary attempts to one saved another ~15 s.

Other devices (for the "it is portable" point):

| Device | Total time | Prefill | Decode | Peak memory | Note |
|---|---|---|---|---|---|
| Apple M4 Mac (dev) | 20.4 s | 826 tok/s | 95 tok/s | 1.7 GB | 32 model calls |
| Arduino UNO Q (Cortex-A53, 4 GB) | 56 min | 9.8 tok/s | 0.37 tok/s | 1.7 GB | network OFF; offline install 4 min 10 s; same questions word for word as on the Mac |

**Two exports, chosen by the CPU automatically:** the fast kernels need the Arm dot-product instructions
(`asimddp`). On the UNO Q (no dot-product) they crashed with "Illegal instruction", so the installer reads
`/proc/cpuinfo` and picks the portable export when needed.

---

## 5. Model engineering (Arm efficiency slide)

| Decision | Number |
|---|---|
| Base model | Qwen3-0.6B: **596 M parameters** (440 M transformer + 156 M embedding), 28 layers, hidden 1024 |
| Export | `optimum-cli export executorch ... --qlinear 8da4w --qembedding 8w --max_seq_len 1024 --use_custom_sdpa --use_custom_kv_cache` (4-bit weights, 8-bit dynamic activations, XNNPACK) |
| Model file | **469 MB** (4-bit); 720 MB 8-bit version also built |
| Memory cut | context limit 2,048 → 1,024 tokens (longest call needs ~600): **peak 2.49 GB → 1.67 GB**, same speed, **identical answers on 8/8 passages** |
| Rejected after measuring | 4-bit word table (saved 74 MB, changed all 8 answers); bigger quantization group (no change); shared in/out word table (kernels not in pip build) |
| Why not 1.7B | ~3x the weights → ~3x slower writing on the Pi; on our data it was not clearly better (held-out 1.273 vs 1.256) |
| Quantization cost (GPU simulation, held-out loss Q/W) | bf16 1.217/1.429; **8-bit 1.223/1.436 (lossless)**; 4-bit g32 1.345/1.564 (+0.13); mixed 4/8-bit 1.306/1.511 |
| Helper models (for linking, ExecuTorch too) | bge-small embedder (33 M params, **128 MB** .pte) + NLI cross-encoder (**317 MB** .pte), ~12 ms per pair on the Mac |

---

## 6. How GURU was made (training numbers)

**Step 0: the plain model is not enough (measured).** 4 prompting versions, each blind-graded on 40 test passages:
best had only **19%** "sensible" questions, answer key right **73%**. A bot that just picks the option most like the
passage scored **66%** (chance 25%), so we dropped our own "beats word-spotting" claim.

**Version 1 (Mac, no GPU):** LoRA on all layers, 4,300 human-written questions (SciQ science + RACE middle-school
reading). Validation loss **2.08 → 0.95** (1 epoch, ~55 min on an M4, ~3.4 s/step).
Result on 40 test passages: sensible **30%** (was 19%), answer key right **82%** (was 73%).

**Teacher data:** ~5 why/how questions for each of **401** syllabus passages, every wrong option tagged with a
misconception id, then graded by a separate model against our rubric: **2,773 graded, 1,039 kept** (score 4-5 and
all hard rules). **0 overlap** with the 40 test passages (checked by 8-word runs).

**Final recipe:** start from version 1, LoRA rank 16, alpha 32, all linear layers, **lr 5e-5, 1 epoch**, held-out
check every 50 steps, best checkpoint kept. Held-out loss **1.292 → 1.256** (single-call model). 0.6B runs took
5-6 min each on an RTX 4060 laptop.

**Two-job GURU (shipped):** one small model, two short jobs, the system prompt picks the job.
- **Job Q:** text + key sentence → question + correct answer.
- **Job W:** + question + correct answer → 3 wrong answers a student would believe.
- Data chosen **per job by the grader's rule flags**: Job Q 1,353 examples, Job W 1,410, + 300 RACE each =
  **3,363** training examples; 310 held-out from 15 never-trained passages.
- **One combined model beat two specialists at both jobs:** Job Q **1.217 vs 1.227**, Job W **1.429 vs 1.439**,
  and it is one 469 MB file instead of two.

**Two-job vs single-call (40 unseen passages):**

| | Two-job | Single-call |
|---|---|---|
| Correct answer is the longest option (a giveaway; chance ~25%) | **6%** | 15% |
| Why/how questions | **49%** | 39% |
| Blind read, good questions | **8/12** | 3/12 |

Honest quality numbers: wrong options blind-read 20 sets, teacher **20/20** good, GURU **10/20** (main failure: a
"wrong" option that is also correct). Strict blind read of 60 two-job questions: **~40-55% fully sound**. That is
why the checks below exist.

Tried with **no gain** (we say so): consensus candidate picking; a "misconception hint" in the prompt (valid 74% →
71%); repairing options from a pool; mixing in another model's data (W loss 1.440 vs 1.435); Qwen3-1.7B.

---

## 7. The quiz checks (what the AI is never allowed to decide alone)

1. **Code picks the key sentence**, not the model.
2. GURU writes question + answer, then wrong answers in a separate call.
3. **No giveaways:** the 3 wrong options closest to the answer in length, opening and passage-word overlap are
   kept; near-duplicates (≥ 80% same words) rejected; "all/none of the above" banned.
4. **Self-check:** the plain model answers the question with shuffled options; if it disagrees, the question is
   dropped. Of 11 questions it rejected in one test, ~9 were truly bad (wrong key or two right answers).
5. Every answer shows **the passage sentence that proves it**.

---

## 8. The misconception graph (built before the event, used offline)

| Part | Count |
|---|---|
| Subjects | 5 (maths, science, social science, general + reading skills) |
| Topics | **258** |
| Concepts | **5,585** (849 basic, 1,718 middle, 3,011 advanced) |
| Student misconceptions | **4,080** (science 1,222, maths 1,268, social 927, general 656) |
| Root beliefs (deeper habits of thinking) | **120**, all named, e.g. "A rule that works in one case works everywhere" (497 beliefs) |
| Prerequisite links ("needs") | **6,052**; **2,949** cross-topic |
| "Causes" links between beliefs | **288** |

Each misconception has: the belief, why students hold it, the **fix**, and a **probe** (a situation question plus
the wrong answer a believer would give).

- Topic matching: right topic for **39/40** test passages (37/40 after the graph grew, still 39/40 in the top 3).
- Off-syllabus passages detected **12/12 with 0 false alarms** (falls back to reading-skill mistakes).
- **We caught our own bug:** a re-link run under a usage limit silently dropped links (1,955 → 843) and erased
  root names. Fix: incremental re-linking that never writes a worse file. Repaired and merged.

---

## 9. Linking a wrong answer to the belief behind it

Design (the standard two-stage search design, scaled down to run offline on a Pi):
1. **Topic shortlist** from the passage: ~4,000 beliefs → ~16-50 candidates.
2. **Retrieve** with a small embedding model (bge-small, ExecuTorch).
3. **Rerank** with an NLI cross-encoder (ExecuTorch).
4. **Abstain** below a confidence threshold, so we never invent a diagnosis.

Measured on **3,647** teacher-labelled (wrong option → misconception) pairs:

| Metric | Value |
|---|---|
| Right belief ranked first | **53%** |
| Right belief in top 3 | **81%** |
| Answer only the most confident 75% | precision 57% |
| Answer only the most confident 25% | precision 64% |
| Reranker gain | +1 point (46% → 47% on 400 pairs), small, reported honestly |

Slide wording (team-approved): "We researched how to link a wrong answer to the belief behind it and chose a
two-stage retrieve-and-rerank design: a small embedding model shortlists likely misconceptions, a reranker picks the
best, and it abstains when unsure. We scaled it to run offline on a Raspberry Pi and measured it on our own ~3,600
labelled examples."

---

## 10. The learning engine (the maths slide)

Four ideas working together, all tiny enough for a Pi CPU (microseconds per update):

**1. Which belief does the child hold? Bayes.**
- Hypotheses: each of the concept's beliefs + "**no specific belief**" (so one random slip does not label a child).
- Likelihood if the child holds belief m: picks m's option **0.70**, correct **0.15**, others share 0.15.
- Next question = the one with the **highest expected information gain**:
  `EIG(q) = H(P) − Σ P(o)·H(P(·|o))`.
- Say "found" at **≥ 75%**, "maybe" at **≥ 50%**.

**2. Has the child learned the concept? Bayesian Knowledge Tracing.**
- Start 0.30, learn 0.20, slip 0.10, guess **0.25** (recall) or **0.15** (situation question).
- Correct: `P(L|✓) = P(L)(1−s) / [P(L)(1−s) + (1−P(L))g]`; wrong: `P(L|✗) = P(L)s / [P(L)s + (1−P(L))(1−g)]`;
  then `P(L) += (1 − P(L))·0.2`.
- Worked example: one wrong answer 0.30 → **0.24**; one right situation answer 0.24 → **0.72**.

**3. Walk down, climb back up.**
- Wrong → find the belief, show the fix, **walk down** to the prerequisite ideas (graph).
- **Climb back up one level at a time** with a real-life situation question, only if right **and** BKT
  P(learned) **≥ 0.6**. Otherwise re-teach, one more try, then **stop** and save the concept as "blocked".
- 0.6 = "ready to build on", not mastery (classic BKT mastery is 0.95).

**4. When will they forget? FSRS-6** (the open-source spaced-repetition scheduler, 21 weights).
- Recall after t days: `R(t,S) = (1 + F·t/S)^(−w20)`; next review at 90% target recall.
- Example from a run: recall **1.00 → 0.66 after 3 days → 0.55 after 10 days**; a failed idea is due the next day.

**Joining them:** mastery today = saved BKT mastery × FSRS chance of remembering. Revision priority =
`1 − mastery × recall` (never learned **or** probably forgotten → first).

**Review days (Mentor Study):**
- Re-check each held belief with a **new** question (Bayes with 2 hypotheses; right but unsure → one more question).
- Still there → fix again, due sooner. Gone → **follow the graph** to a related belief (a "causes" link, else the
  same root belief, in another topic) to test whether the deeper habit is fixed.

**Checked over a week with two pretend students (days 0, 1, 3, 7):**
- Learner: climbs all the way up on day 0 (P(learned) 0.73).
- Non-learner: climb stops at shaky bases; a belief that only looked held from one guess (55%) is **cleared** on
  day 1 (36%); the shared root belief is followed into another topic; a blocked concept climbs back up on day 7.
- Stubborn beliefs re-detected at **90-94%** on review days.

---

## 11. Speed: time per question (the metric that matters)

Measured on 6 test passages (Pi estimate = prompt tokens / 122 + new tokens / 12.1, our measured Pi speeds):

| Setting | Questions kept | Mac s/question | Pi estimate s/question |
|---|---|---|---|
| Wrong answers written twice + self-check (old) | 11 | 6.7 | 47.8 |
| **Wrong answers written once + self-check (now)** | 11 | **4.6** | **31.4** |
| Once, no self-check | 22 | 2.1 | 14.3 |

- **Writing wrong answers twice was pure waste:** decoding is deterministic, so the second run was identical in
  **38/38** calls. Removed: **1.5x faster, same questions**.
- **Streaming:** the child sees question 1 as soon as it is ready; the next is written while they answer.
  Mac test: the child waited **3.4 s, then 0 s, then 0 s**. A real child takes ~20-40 s per question, longer than
  the Pi needs to write one, so the child only waits for the first question (Pi measurement pending).
- One full Mac run: load 6.3 s, summary 2.4 s, first question at 2.9 s, 3.0 s per question, linking 1.2 s; the
  session found "friction only acts on moving objects" at **96%**, and a review 2 days later found it at **91%**.

---

## 12. The device (what the judges hold)

- Raspberry Pi 5 + 176×220 colour screen + **3 buttons** + camera.
- **Study:** New Study (photo of a page → on-device OCR → summary → streamed quiz → diagnosis), Saved page (the
  organiser's passage), **Mentor Study** (fix old mix-ups, follow the graph).
- **Revision:** ideas with mastery bars, what is due today.
- **Diagnostics:** questions solved, accuracy, where the child is stuck (named beliefs), what to do next.
- Every screen reads the real engine and the saved learner; no internet.
- Status (14 Nov): engine and UI connected and synced to the Pi; the Pi was missing two small packages for the
  helper models (installed, helpers now run on the Pi). **Full on-device session timing still to measure.**

---

## 13. Engineering bugs we found and fixed (proof we measured, not assembled)

| Bug | How we found it | Fix / result |
|---|---|---|
| Model never stops writing | Pi run: every call hit 1,412 tokens | Stop on the finished answer: **147 s → 86 s**, same output |
| GURU "answers" A almost always when asked to check | Self-check kept 0 questions | Plain model does the check |
| Graph re-link silently dropped links (1,955 → 843) | Counted links after a run | Incremental re-link that never writes a worse file |
| All 3 wrong options linked to the same belief | First linking run | One belief per option |
| Child shown a raw ID ("SCI-CHM-AIR-K19-M9") | First session run | Show the belief text and its fix |
| A concept blocked forever ("Nitrogen Fixation") | 7-day run | Untestable prerequisites never block |
| One right answer "cleared" an 80%-sure belief | A unit test | Ask one more question first |
| Child's screen swallowed by the model's output capture | Streaming lost a question | Proved by elimination (threads, CPU load, helpers all fine); separate output channel; results identical again |
| Pretend student always picked option A | Engine "found" beliefs that were only option A | Pretend students guess at random |

Tests: **225 passing** (8 new for the engine).

---

## 14. How we work (say it; it is true and rare)

- **Research before building:** every feature starts with a search for what has been shown to work. Example: small
  fact-checking models caught **0-3 of 10** known-wrong answer keys, so we did not ship that check.
- **Measure, don't guess:** blind grading, word-spotting bots, timing and memory on real hardware.
- **Say the weak spots first** (next section).

---

## 15. What we do not claim (say it first)

- No students have used it yet; no learning-gain claim. That needs a pilot.
- The misconceptions were drafted by AI from research on student errors; not yet reviewed by teachers.
- A 0.6B model writes imperfect questions (~40-55% fully sound in a strict read); the checks drop the worst.
- Linking picks the right belief first about half the time (81% in the top 3); low-confidence links are dropped.
- Bayes, BKT and FSRS settings are standard defaults, not yet fitted to children.
- The automatic grader is itself a model; we also read questions ourselves.
- English only for now.

---

## 16. Suggested slide order

1. Title: Sakshi, an offline tutor that diagnoses, not just scores (GURU-0.6B on a Raspberry Pi 5).
2. The child and the barrier (ASER 67.5%, 1 in 3 schools without internet).
3. The mic drop: score vs diagnosis (section 0).
4. Live demo / device photo (section 12).
5. How it works in one picture: passage → GURU (Q then W) → checks → link to belief → Bayes/BKT/graph/FSRS.
6. GURU: how we made a 0.6B model write questions (19% → 30% → two-job 8/12 vs 3/12; 1.217 vs 1.227).
7. The misconception graph (4,080 / 120 / 5,585 / 258).
8. Linking a wrong answer to a belief (53% top-1, 81% top-3, abstain).
9. The learning engine maths (section 10).
10. Arm efficiency: 57.9 s, 122/12.1 tok/s, 469 MB, 2.49 → 1.67 GB, 147 → 86 s, 38/38 waste removed.
11. Bugs we caught (section 13).
12. What we do not claim + next step (school pilot).

---

## 17. Q&A table

| Question | Answer |
|---|---|
| Isn't this just ChatGPT on a Pi? | ChatGPT needs the internet and writes recall questions. Here code picks the sentence, our fine-tuned 0.6B model writes the question, checks drop bad ones, and wrong answers are linked to a graph of real student beliefs. |
| How do you know the answer key is right? | Code picks the sentence, a second model answers the question as a check, and the proving sentence is shown with every answer. |
| Why such a small model? | It must run on a Pi in about a minute with no internet; 1.7B was ~3x slower and not clearly better on our data. |
| Where do the misconceptions come from? | A graph built before the event: 4,080 beliefs across Class 6-10, linked by prerequisites and 120 root beliefs, drafted by AI from research on student errors. |
| What if the passage is off-syllabus? | Detected 12/12 with 0 false alarms; falls back to reading-skill mistakes. |
| How fast, how much memory? | 57.9 s for summary + 3 questions; 1.48 GB with one model, 2.7 GB with both; memory cut from 2.49 to 1.67 GB by sizing the context to what a quiz needs. |
| Did you fine-tune? | Yes: two rounds of LoRA, held-out loss 1.292 → 1.256 (single-call) and a two-job model that beat two specialists (1.217 vs 1.227, 1.429 vs 1.439). |
| What failed? | Prompting alone (19% sensible), a 1.7B model, a misconception hint in the prompt, mixing in another model's data. All measured, all dropped. |
| What's next? | A pilot in one school, where a teacher sees which belief each child holds, then fit the engine's settings to real answers. |
| *(Internal only, not for slides)* Where does the linking design come from? | Answer honestly: retrieve-and-rerank is a standard search design; a 2024 Kaggle competition (Eedi) on the same task used it. We adapted it to a Pi and to our own data and measured it. Never claim we invented it. |
