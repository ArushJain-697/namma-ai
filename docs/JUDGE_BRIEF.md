# Judge brief: decisions, evidence and numbers (keep this updated)

*Living document. Every important decision we make goes here with the reason, the evidence, and the number it
produced. Source for the pitch, the slides and Q&A. Numbers marked TBD are filled from real runs; never type a
number here that a script did not produce. Last updated: 13 Nov 2026, evening (night before the event).*

## The one-liner
Everyone makes a quiz that gives a score. Sakshi gives a diagnosis: wrong answers point to the belief a student
holds, from a graph of student misconceptions, and it all runs on a Raspberry Pi with the network unplugged.

## How we work (say this; it is true and it is rare)
- **Research before building.** Every feature starts with a search for what has been shown to work, with numbers
  and links; we only build what has evidence. Example: we tested small fact-checking models on 10 questions we
  knew had wrong answer keys. They caught 0-3 of 10, so we did not ship that check (a negative result we keep).
- **Measure, don't guess.** Every claim below comes from a script run: blind grading by a separate model,
  word-spotting tests, memory and timing on real hardware.
- **Say the weak spots first** (section "What we do not claim").

## Decisions, with evidence

### 1. Model: Qwen3-0.6B, 4-bit, ExecuTorch (XNNPACK) on the Arm CPU
- Picked by the time budget: the brief wants a fast offline tool; we budgeted about 1 minute for summary + quiz on
  the Pi. Qwen3-1.7B was rejected as too slow for that budget.
- Exported with `optimum-cli ... --qlinear 8da4w --qembedding 8w` (4-bit weights, 8-bit dynamic activations).
- Organisers confirmed a **Raspberry Pi 5, 8 GB** (Cortex-A76, has the dot-product instructions the fast kernels need).

### 2. Two exports, chosen automatically by the CPU
- The fast export uses custom attention kernels that need the Arm dot-product instructions. On an Arduino UNO Q
  (Cortex-A53, no dot-product) it crashed with "Illegal instruction". We built a portable export and an installer
  that checks `/proc/cpuinfo` for `asimddp` and picks the right one.
- **Rehearsal on the UNO Q (no internet, USB only):** offline install of the whole kit in **4 min 10 s**, all checks
  OK; full summary + quiz ran end to end, network OFF ("RESULT: no route out"), 1.7 GB peak.

### 3. Memory cut by a third with zero quality change
- The model reserves memory for its whole context limit. Default export: 2,048 tokens. Our longest quiz call needs
  ~600. Re-exported at 1,024 tokens.
- **Peak memory 2.49 GB -> 1.67 GB** (Mac M4), same speed, **identical answers on 8/8 test passages**.
- Rejected after measuring: 4-bit word table (saves only 74 MB but changed all 8 answers); larger quantization
  group (no change in file or output); a shared input/output word table (needs kernels not in the pip build).
- Remaining ~220 MB is Python + torch, which the Python runner always loads (said openly on the run card).

### 4. Time budget, decided from token counts
- One model call per question + one for the summary. Measured with the Qwen3 tokenizer on 200 passages: passage
  avg 246 tokens, one question ~84 tokens out.
- Estimated whole quiz on the Pi 5: ~31 s (fast case), ~52 s (likely), ~115 s (worst case). The real number comes
  from `test.sh` on the day: Pi 5 = TBD.
- Rejected: "all questions in one call" (faster, but small models break long structured outputs), Tree-of-Thoughts
  style agents (no evidence below 1B, and 3x the calls).

### 5. The misconception graph (built before the event, used offline)
- **249 topics, 5,311 concepts, 3,838 student misconceptions, 120 named root beliefs** (Class 6-10, maths, science,
  social science, general). Each misconception has: the belief, why students hold it, the fix, and a test question
  with the wrong answer a believer would give.
- Prerequisite links between topics are found by **meaning** (embeddings) and checked by Sonnet; an earlier
  word-overlap version linked "decimals" to "integers", so we replaced it.
- **We caught and fixed our own bug:** a re-link run during a usage limit silently dropped links (1,955 -> 843) and
  erased root-belief names. Fix: incremental re-linking that keeps every earlier checked decision and refuses to
  write a worse file. Repaired result: **2,657 links (2,391 Sonnet-checked), 120 named roots**.
- Topic matching: the right topic for **39/40** test passages; off-syllabus passages are detected **12/12 with 0
  false alarms** and fall back to reading-skill mistakes.

### 6. Question quality: the hardest problem, attacked with measurement
- **Plain model, prompting only (4 versions, each blind-graded by Sonnet on 40 passages):** best version had **19%**
  of questions rated "sensible"; the answer key was right 73% of the time. Research says why: even the Kaggle Eedi
  winners used 14-72B models for misconception options; small models cannot do it by prompting.
- **We tested our own pitch claim and dropped it:** a bot that just picks the option sounding most like the passage
  got 66% right on our best plain-model version (chance is 25%), so "our quiz beats word-spotting" was false for it.
- **Fine-tuned our own model on the Mac** (no GPU) on 4,300 human-written multiple-choice questions (SciQ science
  questions with supporting paragraphs + RACE middle-school reading tests), LoRA on all layers, in the exact prompt
  layout the Pi uses. Validation loss 2.08 -> 0.95 (1 epoch, ~55 min on an M4 Mac, ~3.4 s/step).
  **Result on the 40 test passages (blind Sonnet grade, same bar):** sensible **30%** (35/115, was 19%), answer key
  right **82%** (was 73%), 26/40 passages with >= 3 questions, ~54 s estimated on the Pi. Weakness: almost all
  questions are plain recall ("What is...?"), because SciQ teaches recall; the strict rubric (why/how) scores none
  of them >= 4. Word-spotting bot: 58% (chance 27%), so no "beats word-spotting" claim yet.
- Engineering fixes found while testing: the runner does not stop at Qwen's end-of-turn marker (the model keeps
  writing), so output is cut at the first "Answer:" line; the model put the key in option A ~80% of the time, so
  code shuffles options; repeated options are dropped and 3-option questions kept (three options are as good as
  four: Rodriguez 2005, meta-analysis of 80 years of research).
- Next: add the teammate's Opus-written NCERT-style questions (with evidence sentences) and retrain.

### 7. Learner model: chosen for zero data and a small CPU
- Bayesian Knowledge Tracing per concept + Bayesian diagnosis from which wrong option was picked + prerequisite
  graph + FSRS revision scheduling. Research: deep knowledge-tracing models perform near chance (AUC ~0.5) for brand
  new students and are too heavy for a Pi; BKT works from the first answer and costs microseconds.
- FSRS (the Anki scheduler) predicts recall honestly: with default settings a 7-day-stable memory is still ~77% at
  day 30, so we do not show exaggerated forgetting curves.

## Numbers safe to show (with sources)
| Number | What | Source |
|---|---|---|
| 67.5% | Class 8 students in rural government schools who can read a Class 2 text | ASER 2024 national findings (primary PDF) |
| 45.8% | Class 8 students (rural) who can do a simple division | ASER 2024 |
| 0.37 SD | Maths gain from Mindspark (adaptive, misconception-driven) in 4.5 months, RCT, Delhi | Muralidharan, Singh, Ganimian 2019 |
| d = 0.83 | Gain from mixing problem types (interleaving), 787 students, RCT | Rohrer et al. 2020 |
| g ~ 0.41 | Refutation texts ("you might think X; actually Y") correcting misconceptions | Tippett 2010 meta-analysis |
| 2.49 -> 1.67 GB | Our peak memory after the 1,024-token export | our run card |
| 39/40 | Passages matched to the right syllabus topic | `scripts/check_library_match.py` |

## What we do not claim (say it first)
- No students have used it; no learning-gain claim. That needs a pilot.
- The misconceptions were drafted by AI (Gemini, Claude) from research on student errors, not yet reviewed by
  teachers.
- A 0.6B model writes imperfect questions; the checks drop the worst, they do not make the rest perfect.
- Our automatic grader is itself a model (Sonnet) and research shows model graders have biases; we also read the
  questions ourselves.

## Open items (update as they land)
- Fine-tuned model v1 (SciQ + RACE): sensible 30%, key 82%. Next: add the teammate's Opus why/how data and retrain.
- Pi 5 timing and memory (TBD on the day).
- Possible add-ons, only if questions are good: show the misconception's fix after a wrong answer (refutation
  text, g ~ 0.41); camera page reader; read-aloud.
