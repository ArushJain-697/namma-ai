# Pitch pack: Sakshi (offline diagnostic quiz on a Raspberry Pi)

*Written 13 Nov 2026, the night before Namma AI. Numbers marked TO MEASURE are filled from `test.sh` on the Pi.
Every fact has a source; "reported" means a secondary source we could not open at the primary site, so check it
before saying it on stage, or drop it.*

## 0. Rules dossier (what we know and what we assume)

We do **not** have the organisers' scoring rubric. What the problem statement requires (all must be visibly met):

| Requirement | How we show it | Status |
|---|---|---|
| 150-300 word passage in, from the organisers | `bash test.sh passage.txt` on their passage | ready |
| Approved lightweight model, locally, ExecuTorch, Raspberry Pi | Qwen3-0.6B, ExecuTorch 1.5.1 8da4w; organisers said any model is fine | Pi run TO MEASURE |
| Short summary + at least 3 relevant questions, terminal is fine | `sakshi run` prints summary, quiz, run card | quality depends on the fine-tune |
| No cloud inference | `prove_offline.sh`: network unplugged, "RESULT: no route out" | proven on the UNO Q |
| Report time, model, size, memory | run card after every run | Mac: 20 s, 469 MB, 1.7 GB |
| Impact explanation | section 2 below, plus one example from the organisers' passage | write on the day |

**Assumptions** (Arm + NASSCOM + IIIT-B judges): they will weigh (1) the requirements above actually working on
the Pi, (2) efficiency on Arm (time, memory), (3) educational value, (4) originality, (5) presentation.

**Ask the organisers on arrival:** the scoring criteria and weights; how long the demo slot is; whether judges
come to the table or we present on stage; whether we may use our own fine-tuned model (they said yes earlier,
confirm); whether the Pi has internet during setup; Raspberry Pi OS version and Python version on their Pi.

## 1. One line, and the category shift

**Everyone makes a quiz that gives a score. Sakshi gives a diagnosis.** Every wrong option is a real student
belief from a graph of 3,299 misconceptions (Class 6-10, all subjects), so a wrong answer tells the teacher *what
the child believes*, not just that they are wrong. And it runs on a Raspberry Pi with the network unplugged.

## 2. Hook: one child, one moment, one cost

> A Class 8 student in a rural government school finishes today's science passage. She can read most of the words.
> Nobody can tell her whether she understood it, and there is no internet to ask an app.

Facts (use one or two, not all):

| Fact | Source | Status |
|---|---|---|
| Only **67.5%** of Class 8 students in rural government schools can read a Class 2-level text (ASER 2024, 649,491 children surveyed) | [ASER 2024 national findings](https://asercentre.org/wp-content/uploads/2022/12/ASER-2024-National-findings.pdf) | verified (primary PDF) |
| Only **45.8%** of Class 8 students (rural) can do a 3-digit by 1-digit division | same | verified (primary PDF) |
| **63.5%** of Indian schools have internet (UDISE+ 2024-25), up from 53.9% | [PIB release](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2161543), [UDISE+ booklet](https://dashboard.udiseplus.gov.in/report2026/static/media/UDISE+2024_25_Booklet_existing.118ba29d4773e6372f72.pdf) | reported (site blocked our fetch); so about 1 in 3 schools has none |
| Government schools 58.6% internet vs private 77.1% | [educationforallinindia](https://educationforallinindia.com/63-percent-of-indian-schools-now-online-yet-over-25000-languish-without-electricity/) | **unverified**, do not say on stage |
| Class 9 national average about **40%** in science and social science (PARAKH 2024, ~21 lakh students) | [PARAKH report](https://parakh.ncert.gov.in/sites/default/files/2025-07/REPORT_India_IND.pdf), [summary](https://thefederal.com/category/education/parakh-2024-survey-learning-gaps-indian-school-students-196870) | reported |

The point to land: **reading the words is not understanding them**, and the children who most need a check are the
ones without internet.

## 3. The named trap: the Word-Spotting Trap

> **NOT YET SUPPORTED — do not claim on stage until the numbers change (measured 13 Nov).** A bot that only picks
> the option sharing the most words with the passage got: fill-in-the-blank 38%, backup quiz with passage-phrase
> wrong options 6%, backup quiz with misconception wrong options **66%** (random = 25%). The correct answer copies
> passage words while misconception options do not, so our best version is currently *easier* to word-spot. Fix
> under test: mix one true-but-irrelevant passage phrase into the wrong options so word-matching stops working.

**The obvious approach is confidently wrong.** An ordinary quiz generator turns a passage into fill-in-the-blank or
"according to the passage" questions. A child can score full marks by matching words, without understanding
anything, and the teacher sees 100% and moves on. Our own first version did exactly this (its fallback was
fill-in-the-blank), which is why we know.

**How Sakshi beats it (several independent checks, the model is one voter):**
1. **Code** picks the key sentence (content-rich, prefers cause-and-effect), never the model.
2. The question must ask **why or how** (a fill-in-the-blank is rejected by a rule, not by asking the model).
3. Wrong options come from the **misconception graph** (real student beliefs for that topic), so a word-matcher
   cannot find the answer by spotting words.
4. **Rule checks** reject repeats, "all of the above", answer words leaked into the question, and an answer that is
   obviously the longest.
5. The model **answers its own question** with shuffled options; if it gets it wrong, the question is dropped.

**Show it live** (`python -m sakshi villain ...`): the same passage through a fill-in-the-blank generator next to
Sakshi. Read one fill-in-the-blank aloud and answer it *without reading the passage*, by word spotting.

## 4. What the AI is never allowed to decide
- **Which sentence the question is about**: code decides.
- **What the misconceptions are**: the graph is built ahead of time and stored on the Pi; the small model never
  invents a belief on stage.
- **Whether a question is shown**: the checks decide. Fewer questions rather than a bad one; never fill-in-the-blank.

## 5. Competitors (say it before a judge does)

| Product | What it does | How Sakshi differs |
|---|---|---|
| [Eedi](https://eedi.com/blog/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions) | Diagnostic maths questions: 36,000 wrong options each mapped to a misconception, 4 million student answers | The idea we build on. Eedi is online, maths only, and its questions are written by people. Its own research found LLM-written wrong options capture misconceptions "only to a limited degree" ([EDM 2024](https://educationaldatamining.org/EDM2024/proceedings/2024.EDM-posters.113/index.html)) |
| [Google Read Along](https://blog.google/outreach-initiatives/education/early-access-read-along/) | Offline reading tutor on 1 GB phones, born in India as Bolo | Checks *reading aloud* (fluency), not *understanding* of a science or history passage |
| ChatGPT / Gemini quiz prompts, AI quiz websites | Generate quizzes from any text | Need the cloud, and default to recall and fill-in-the-blank (the trap) |
| Khanmigo (Khan Academy) | AI tutor | Cloud web app; not built for offline classrooms |
| Arm's own ExecuTorch Pi tutorial | Runs Llama on a Pi 5 with ExecuTorch | We use the same stack (sponsor tech is load-bearing); the tutorial is a chat demo, ours is a classroom tool |

## 6. Key numbers (learn these; regenerate before the demo)

| Number | Value | Source of truth |
|---|---|---|
| Model | Qwen3-0.6B, ExecuTorch 1.5.1, 4-bit weights (8da4w), XNNPACK, Arm CPU | `docs/SUBMISSION.md` |
| Model file | 469 MB | run card |
| Peak memory | 1.7 GB (Mac); Pi TO MEASURE. Cut from 2.5 GB by exporting with a 1,024-token limit, same answers | run card, `train/README.md` |
| Time for summary + quiz | Mac 20 s; Pi TO MEASURE (budget about 1 minute) | `test.sh` |
| Offline | "RESULT: no route out" | `scripts/prove_offline.sh` |
| Misconception graph | 220 topics, 4,531 concepts, 3,299 misconceptions, 120 root beliefs | `data/misconceptions/stats.json` |
| Question quality | TO MEASURE: fine-tuned model on the 200 held-out passages (teammate's Job 6), or the backup quiz grades | `results/question_quality.md` / `results/backup_quiz/REPORT.md` |

## 7. Say it first (what this is NOT)
- **Not tested with students yet.** We have not measured learning gains; that is the pilot.
- **A small model (0.6B).** Some questions will be imperfect; the checks drop the worst ones, they do not make the
  rest perfect.
- **The misconceptions were drafted by AI** (Gemini and Claude) from research on student errors, not yet reviewed by
  teachers. Labels like "documented in research" are model claims.
- **The Pi numbers come from today's run**; earlier numbers are from a Mac and an Arduino UNO Q.
- If anything on screen is a saved run, say "this is a saved run" before showing it.

## 8. Q&A table

| Question | Answer (one or two sentences) |
|---|---|
| Isn't this just ChatGPT on a Pi? | ChatGPT needs the internet and writes recall questions. Here the model only writes the question and the answer; code picks the sentence and the wrong options come from a graph of real student beliefs. |
| How do you know the right answer is right? | Code picks the sentence it must come from, the model answers its own question as a check, and the sentence is shown with the answer. We measured the key on 40 test passages (TO FILL from the report). |
| Why such a small model? | It has to run on a Raspberry Pi in about a minute with no internet. A 1.7B model was too slow on the Pi. |
| Where do the misconceptions come from? | A graph built before the event: 3,299 student misconceptions across Class 6-10, linked by prerequisite and grouped into 120 root beliefs, drafted by AI from research on student errors. |
| What if the passage is not from the syllabus? | It falls back to reading-skill mistakes (confusing cause and effect, picking a nearby fact). |
| How fast, how much memory? | (Pi numbers from the run card.) Memory was cut from 2.5 GB to 1.7 GB by sizing the model's memory to what a quiz needs. |
| Did you fine-tune? | (Say what is true on the day: fine-tuned on N Opus-written examples, scores before and after; or "plain model, fine-tune in progress".) |
| What's next? | One sentence: a pilot in one school, where a teacher sees which belief each child holds. |
| What failed? | Our first version made fill-in-the-blank questions (the trap). The plain small model writes good "why" questions but cannot write four sensible options, so options come from the graph. |
