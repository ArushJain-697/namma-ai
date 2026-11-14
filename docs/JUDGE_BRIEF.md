# Judge brief: decisions, evidence and numbers (keep this updated)

*Living document. Every important decision we make goes here with the reason, the evidence, and the number it
produced. Source for the pitch, the slides and Q&A. Numbers marked TBD are filled from real runs; never type a
number here that a script did not produce. Last updated: 13 Nov 2026, evening (night before the event).*

## Measured on the Raspberry Pi 5 (8 GB), 14 Nov 2026 (the judged device)
- `pi-kit/install.sh` offline install OK (ExecuTorch 1.5.1 runner loads, 6/6 model checksums OK, 216/217 tests pass).
- `test.sh` (4-bit model, 329-token prompt, 119 new tokens): load 0.7 s, **prefill 122 tok/s, decode 12.1 tok/s,
  peak 1.48 GB**. ExecuTorch on the Pi 5 works at normal speed (the 0.87 tok/s worst case reported online did not
  happen to us).
- **Full deliverable** (`pi-kit/quiz.sh`, rust passage, 224 words): summary + 4 questions, each with its proving
  sentence, in **86 s** (load 3.1 s, summary 14.6 s, quiz 68.6 s), peak 2.7 GB with GURU + plain Qwen3 loaded.
- **Speed fix found on the Pi:** the fine-tuned model never writes its end-of-turn token, so every call wrote until
  its cap (1,412 tokens). We stop each call as soon as the answer is complete (watching the text as it streams;
  works with "π", "²"): **147 s -> 86 s with identical output**, 750 tokens written. One summary attempt instead of
  two saved another ~15 s.
- **Final setting: 3 questions (the brief asks for at least 3): 57.9 s total** (load 3.0 s, summary 14.2 s, quiz
  40.7 s, 16 model calls, 3,012 tokens read, 539 written). Under our 1-minute budget.
- Thermal: the board reached **84 C and throttled** (`vcgencmd get_throttled` = 0xe0008) without a fan. Use a fan.
- Offline proof: run `scripts/prove_offline.sh` at the venue with Wi-Fi off (it correctly said NOT OFFLINE while
  Wi-Fi was on for SSH).

## Names (decided 14 Nov)
- System: **Sakshi** (offline learning assistant). Quiz model: **GURU-0.6B** = **G**rounded **U**nderstanding,
  **R**uns **U**nplugged. Always say it is **fine-tuned from Qwen3-0.6B** (Apache 2.0 allows this; hiding the base
  model would be an overclaim). Slide line: "Sakshi runs GURU-0.6B, our quiz model fine-tuned from Qwen3-0.6B,
  offline on a Raspberry Pi."
- To do when the final model is in: name the export folder `models/guru-0.6b/` and show "GURU-0.6B (fine-tuned
  Qwen3-0.6B)" on the run card.

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
- Topic matching: the right topic for **39/40** test passages (37/40 after the graph grew to 258 topics on 14 Nov:
  heart and vaccine passages now match the NEW, more specific topics Heart/circulation and Vaccines/immunity, with the
  old expected topics still in the top 3; 39/40 in the top 3); off-syllabus passages are detected **12/12 with 0
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
- Teacher data (13 Nov night): Claude Opus (then Sonnet, to save quota) wrote ~5 why/how questions for each of 401
  syllabus passages, every wrong option tagged with a misconception id; a separate Sonnet grader scored each against
  our rubric. **2,773 graded, 1,039 kept (score 4-5, all hard rules)**: Opus 62% pass, Sonnet 53%. Zero overlap with
  the 40 test passages (checked by 8-word runs).
- Final run starts FROM version 1 (its 39 MB LoRA adapter is merged into Qwen first), then trains a new adapter on
  905 graded teacher questions + 300 RACE "reminder" examples (replay, so version 1's format skills are not
  forgotten), lr 1e-4, 2 epochs, held-out check every 50 steps, best checkpoint kept. Tested end to end on the Mac
  before shipping. Epoch choice checked against published advice: Unsloth's LoRA guide (1-3 epochs, >3 risks
  overfitting), Raschka's LoRA experiments (a 2nd epoch sometimes hurt; "number of epochs is still an open
  problem"), "LoRA Learns Less and Forgets Less" (peak at 4 epochs) -> all say decide by held-out loss, which we do;
  our own run on this data peaked at ~1.3 views per teacher question.
- **Result of that run (14 Nov morning, teammate's RTX 4080):** questions very good, wrong options still weak.
  A Qwen3-1.7B run on the same data was not clearly better, so we stay with 0.6B (3x faster on the Pi).
  Held-out error (lower is better, 146 held-out examples): 0.6B from v1 at lr 1e-4 x2 epochs 1.292 -> 1.272 (then
  rose to 1.32 = overfitting, early stop kept 1.272); **0.6B from v1 at lr 5e-5 x1 epoch 1.292 -> 1.256 (best,
  shipped as GURU-0.6B = Qwen3-0.6B + v1 adapter + this adapter, `models/guru-0.6b`, 469 MB)**; Qwen3-1.7B from
  scratch 5.10 -> 1.273 (no better, ~3x slower). Measured on the teammate's RTX 4060 Laptop 8 GB (~1 s/step,
  5-6 min per 0.6B run). Valid-question rate on 26 unseen passages: 17-21/26 on the first try for every model;
  26/26 within 4 tries with a retry filter (avg 1.5 tries for the best 0.6B). Tried with **no gain**: picking the
  consensus candidate; a "misconception hint" sentence in the prompt (valid 74% -> 71%); repairing options from
  the sampled pool. Gemini-written data: 462 of 1,901 items copied the evidence into the answer while wrong options
  never did (a word-spotting giveaway); filtered out. Teammate's output filter idea adopted: reject near-duplicate
  options (>= 80% the same words), alongside our exact-repeat, giveaway and self-checks.
- **Decision: split the work into two short jobs ("two-job" GURU).** Job Q: text + key sentence -> question +
  correct answer. Job W: + question + correct answer -> 3 wrong answers a student would believe. One model, the
  system prompt picks the job. Why: small-model research (answer-first generation; step-by-step generation;
  overgenerate-and-filter for distractors) says one small job at a time beats one big job, and a dedicated
  wrong-answer call can focus only on traps and can be run more than once to pick the best options. Not a
  context-window issue (one call used ~500 of 1,024 tokens). **Data selected per job by the grader's rule flags**
  (not one overall score): Job Q takes questions passing the question rules (understanding, one provable answer,
  no leak, simple English) even if their options were weak = 1,353; Job W takes questions whose wrong options pass
  the option rules (believable, no giveaways, provable key) even if the question was plain recall = 1,410. Each job
  gets ~35-40% more examples of exactly its own skill. + 300 RACE per job = 3,363 training examples; 310 held-out
  from 15 never-trained passages (0 overlap, checked).
- **The correct answer must not stand out (no giveaways).** With two calls the key and the wrong options are written
  separately, so they could differ in length, grammar or wording. Four layers: (1) Job W sees the correct answer
  and is trained only on teacher items that passed the grader's "no giveaway" rule (same grammar/style, similar
  length, key not the longest); (2) code checks each question: length gap, same opening/shape, and the key must not
  share far more words with the passage than the wrong options (word-spotting check); (3) Job W runs twice and the
  3 options closest to the key's length and form that pass the checks are kept; (4) measured on the 40 test
  passages: % of questions where the key is the longest option (target ~25% = chance) and the word-spotting bot's
  hit rate (target near chance; version 1 was 58%). Results: **TBD**.
- **Combined vs specialist adapters (experiment):** one LoRA adapter doing both jobs vs one adapter per job (the
  multi-LoRA idea). ExecuTorch describes adapters sharing base weights ("program-data separation"), but runtime
  adapter swapping is not a documented feature yet (GitHub issue #9580 still open), so if specialists win we ship
  two merged models (`guru-q`, `guru-w`, 469 MB each, both loaded at start, ~3 GB RAM of 8 GB) instead of swapping.
  All three trained in the same GPU session; chosen by held-out loss per job + a format check.
  **Result (lr 5e-5, 1 epoch, from v1; per-job held-out loss measured on the same sets):** combined Job Q 1.217 /
  Job W 1.429 vs specialists 1.227 / 1.439 -> **the combined model is slightly better at both jobs** (learning both
  together helps), and it is one 469 MB model instead of two. Shipped as `models/guru-0.6b-2job` (Qwen3-0.6B + v1 +
  combined adapter). Adding the teammate's cleaned Gemini Job W data did not help (1.440 vs 1.435). Quiz-level test
  on the 40 passages: **TBD**.
- **GPU session's quiz-level measurements (RTX 4060 laptop, bf16, 40 unseen eval passages x3 key sentences;
  `docs/gpu_session/README_HANDOFF.md`):** two-job vs single-call: key is the longest option **6% vs 15%**; why/how
  questions **49% vs 39%**; blind read of 12 pairs **8/12 vs 3/12 good**; word-spotting bot 47% vs 43% (chance 25%,
  not yet improved). Wrong options blind vs teacher-written (20 sets): teacher 20/20 good, model **10/20** (main
  failure: a "wrong" option that is also correct). Strict blind read of 60 two-job questions: ~40-55% fully sound.
  Wrong options sampled twice + dedupe + pick 3 closest to the key: 147/156 held-out get 3 distinct options.
- **Quantization matters:** simulated held-out loss Q/W: bf16 1.217/1.429; 8-bit weights 1.223/1.436 (lossless);
  4-bit (our 8da4w Pi export) 1.345/1.564 (+0.13). So we export BOTH: `models/guru-0.6b-2job` (4-bit, 469 MB) and
  `models/guru-0.6b-2job-8bit` (8da8w, 720 MB, ~1.5x slower writing). Choose on the Pi by measured time vs the
  1-minute budget. To be confirmed on the real .pte files. Cost on the Pi: one extra short
  call per question (~8-10 s). Package: `~/Downloads/final-training-2job.zip`. Result: **TBD**.
- Earlier plan (superseded): final training set, curated by evidence (LIMA: 1,000 curated examples beat 52,000; diversity beats volume):
  2,676 examples = 905 teacher why/how questions + 1,071 RACE + 700 SciQ. Removed near-duplicates (cosine > 0.92)
  and items whose key is clearly the longest option; capped the most common type ("what if") so types stay
  varied; cut SciQ because its 1-2-word options (avg 1.4 words) clash with the target style (teacher avg 7.3);
  answer letters balanced. Considered and skipped with reasons: DPO preference training (only "modest" and
  pair-count-sensitive gains in the studies found, needs graded on-policy samples), NEFTune (gains on chat, not
  on structured tasks). Previous plan: 993 teacher questions (once each) + 2,000 SciQ/RACE (no repeats), held-out check every 100
  steps on 15 never-trained passages; only the best checkpoint is kept. Evidence for that guard: in an earlier run
  held-out error fell to 1.381 then rose (1.39 -> 1.44), and the script kept the 1.381 version automatically.
  Trained on a teammate's RTX 4080 laptop. Result: **TBD**.

### 7. Linking each wrong option to a misconception: retrieve-and-rerank, run on a Pi
*(The first bullet is team background with sources, for Q&A; slides use the wording further down.)*
- The retention engine needs to know WHICH misconception each wrong option represents. This is exactly the task of
  the Kaggle competition "Eedi - Mining Misconceptions in Mathematics" (2024): question + wrong answer ->
  misconception. The winning solutions used **retrieve-and-rerank** (an embedding model shortlists candidates, a
  reranker picks the best), with the retriever **fine-tuned contrastively on labelled pairs with hard negatives**,
  and LLM-written "why a student would pick this" rationales (1st place).
- We use the same architecture scaled down to run offline on the Pi: topic shortlist (39/40 passages matched to
  the right topic) -> bge-small embedder (33M params, ExecuTorch, 133 MB) -> cross-encoder reranker (ExecuTorch,
  ~12 ms per pair on a Mac) -> **abstain** below a confidence threshold, so we never invent a diagnosis.
- Our own labelled data makes it measurable and trainable: every wrong option in the ~2,800 graded teacher
  questions carries a misconception id and the student's reasoning (~3,000 pairs), split by passage for an honest
  test. Plan and steps: `docs/MISCONCEPTION_MAPPING_PLAN.md`.
- Numbers (TBD, to be measured): recall@1, recall@5 and MAP@25 (standard ranking metrics) before vs after fine-tuning;
  precision and coverage at the abstain threshold; time per option on the Pi.
- **Slide / pitch wording (team decision: no competition names on slides):** "We researched how to link a wrong
  answer to the belief behind it and chose a two-stage retrieve-and-rerank design: a small embedding model
  shortlists likely misconceptions, a reranker picks the best, and it abstains when unsure. We scaled it to run
  offline on a Raspberry Pi and trained and measured it on our own ~3,000 labelled examples."
  (All true: we did the research, the adaptation, the data and the measurement.)
- **If a judge asks where the idea comes from, answer honestly:** retrieve-and-rerank is a standard search
  architecture, and a 2024 Kaggle competition (Eedi) on the same task used it; we adapted it to a Pi and our own
  data. Never claim we invented it. (Internal note, not for slides.)

### 8. Learner model: chosen for zero data and a small CPU
- Bayesian Knowledge Tracing per concept + Bayesian diagnosis from which wrong option was picked + prerequisite
  graph + FSRS revision scheduling. Research: deep knowledge-tracing models perform near chance (AUC ~0.5) for brand
  new students and are too heavy for a Pi; BKT works from the first answer and costs microseconds.
- Two kinds of questions, two jobs (decided 13 Nov): **recall questions** ("What is...?") feed spaced revision,
  because retrieval practice of facts is what spacing helps (practice testing g ~ 0.5 in classrooms, Adesope et
  al. 2017); **why/how questions with misconception options** are for the first check of understanding and for
  diagnosis. The fine-tuned model's recall questions are therefore not wasted: they become the revision deck.
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

## Retention engine connected to GURU on the Mac (14 Nov)
- `src/sakshi/link.py` + `scripts/retention_demo.py`: GURU's 3 questions → each wrong option linked to a graph
  misconception (retrieve bge-small within the passage's topics → NLI rerank → abstain below cos 0.76) → bank with
  graph prerequisites and template questions → adaptive session (Bayes + EIG, BKT, walk-down/climb-up, FSRS-6) → revision plan.
- Linking measured on 3,647 teacher-labelled pairs: recall@1 53%, recall@3 81%; NLI rerank +1 point (46→47% on 400).
- Photosynthesis run: 10 concepts, 12 questions (3 GURU), belief named with its fix, BKT 0.30 → 0.24 (wrong) / 0.63-0.73
  (after walk-down), FSRS due next day, recall 1.00 → 0.66 (3 d) → 0.55 (10 d). Maths: `docs/RETENTION_MATH.md`.
- Mac only; not on the Pi. Parameters are hand-set (no student data yet).
