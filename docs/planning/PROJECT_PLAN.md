# Project Plan: Offline Retention Tutor (Namma AI Hackathon, Problem Statement 1)

> Hand this file to Claude Code. It contains the full context, the scope, the architecture and the build order.
> Rule #1: **the mandatory core must never break.** Every extra feature has a fallback to the core.

---

## 1. Context

**Event:** Namma AI Hackathon (Arm + IIIT Bangalore + NASSCOM), a one-day Edge AI challenge.
- Live hackathon: **14 Nov 2026**, NASSCOM office, **6–8 hours of active development**.
- Team: 1–3 members. Project must be **hosted on GitHub** and submitted via the challenge form.
- Required tech: **ExecuTorch on Raspberry Pi** (we get a **Pi with 8 GB RAM**).
- Program lead is Arm, so judges will care about **on-device performance and optimisation**, not just features.

**Problem Statement 1: AI for Inclusive Education, an Offline Smart Learning Assistant**

Mandatory deliverables (all must be met):
1. Identify **one learning barrier**, the **intended learner group**, and how the PoC addresses it.
2. Process **one organiser-provided passage (~150–300 words)** with an **approved lightweight model** running locally through **ExecuTorch on Raspberry Pi**.
3. Generate a **short, understandable summary** and **at least 3 relevant quiz questions**. Terminal output is sufficient.
4. Show operation **without cloud inference**; report **approx inference time, model used, model size / memory usage**.
5. Brief **impact explanation** with **one concrete example from the supplied passage**.

Not required: chatbot, multilingual, document management, custom UI, mobile app.
(We add a physical tutor box anyway, as an extra. It is **not** core.)

### Open questions (confirm with organisers: support@nammaAIchallenge.com)
- [ ] Which models are on the **approved list**? (Expected something like Llama 3.2 1B / Qwen-class small instruct models. Design must be model-agnostic.)
- [ ] Is **pre-written code** (engine, prompts, hardware drivers) allowed before the event?
- [ ] Can non-ExecuTorch preprocessing be used (e.g. Tesseract OCR for the camera)?

---

## 2. Our angle (the pitch)

**Barrier: forgetting, made worse by no access.**
Students forget most of what they study within days unless it is revised at the right time and misunderstandings are caught early. Urban students have tutors, coaching and online apps to do this. Students in low-connectivity areas have none: they study once, forget, and nobody catches their misconceptions.

**Learner group:** Class 6–10 students in rural / low-connectivity schools, self-studying from textbooks.

**Our PoC:** an offline device that turns any passage into:
1. a summary,
2. **diagnostic** quiz questions (every wrong option reveals a specific misconception),
3. an **adaptive walk** through the passage's concepts (go down to basics when wrong, climb back up with application questions when right),
4. a **scientifically scheduled revision plan** (FSRS) so the student revises each concept just before forgetting it.

**Hero = retention.** Every component serves it:
| Component | Why it helps retention |
|---|---|
| Diagnostic MCQs + Bayesian misconception detection | You can't retain what you misunderstood, so fix the misconception first |
| Concept graph walk (down/up) | Weak foundations are forgotten first: repair the base, then apply |
| Application questions on the way up | Applying knowledge is one of the strongest ways to make it stick |
| BKT (knowledge tracing) | Separates real learning from lucky guesses |
| FSRS scheduler | Brings each concept back right before it would be forgotten |

One-line pitch: *"A normal quiz says 'wrong'. Ours says **why**, fixes it, and tells you **when** to revise, fully offline, on a ₹-cheap box."*

---

## 3. Priorities (build in this order, never skip ahead)

1. **CORE (mandatory):** ExecuTorch model on Pi → summary + ≥3 questions → metrics in terminal.
2. **RETENTION ENGINE:** diagnostic MCQs, Bayes detection, concept graph walk, BKT, FSRS, `--simulate-days`, retention chart.
3. **TUTOR BOX (extra, impressive):** 3D-printed box (already printed) with Pi, TFT screen, buttons, USB camera. **No mic, no STT, no TTS.**

Each layer must degrade gracefully to the layer below.

---

## 4. Architecture

```
            ┌──────────── Input ────────────┐
            │ passage.txt  (mandatory path) │
            │ camera → OCR → text (extra)   │
            └───────────────┬───────────────┘
                            ▼
  ┌──────────────── LLM pipeline (ExecuTorch, on Pi) ───────────────┐
  │ Stage 1: concepts  → 4–6 key concepts, ordered basic→advanced    │
  │ Stage 2: summary   → short, simple-language summary              │
  │ Stage 3: questions → per concept: 1 recall + 1 application MCQ,  │
  │                      each wrong option tagged with a misconception│
  │ Every stage: timed, token-counted, JSON-validated, retry+fallback│
  └───────────────┬──────────────────────────────────────────────────┘
                  ▼
  ┌──────────── Retention engine (pure Python, no model) ────────────┐
  │ bayes.py   misconception posterior + next-question selection      │
  │ graph.py   concept graph walk (down on wrong, up on right)        │
  │ bkt.py     mastery per concept (learn/slip/guess)                 │
  │ fsrs_sched.py  py-fsrs cards per concept, review dates            │
  │ ranker.py  priority = P_mastery × R_fsrs(t)                       │
  │ simulate.py  --simulate-days N, retention-curve comparison        │
  └───────────────┬──────────────────────────────────────────────────┘
                  ▼
  ┌──────────────────── I/O layer (swappable) ───────────────────────┐
  │ TerminalIO  (default, always works, shows metrics & logs)        │
  │ BoxIO       (TFT screen + GPIO buttons + camera)                 │
  └──────────────────────────────────────────────────────────────────┘
```

**Key design rule:** the engine never imports the LLM or hardware. It works on plain JSON. That lets us build and test it **before** the hackathon with a fake LLM.

---

## 5. Repo layout

```
retention-tutor/
├── README.md                 # pitch, setup, metrics table, demo instructions
├── main.py                   # CLI entry: --passage, --io terminal|box, --simulate-days N, --fake-llm
├── config.yaml               # model path, max tokens, thresholds, BKT params
├── llm/
│   ├── runner.py             # ExecuTorch wrapper: generate(prompt, max_tokens) -> text, stats
│   ├── fake_runner.py        # returns fixtures; used for tests / offline dev
│   ├── prompts.py            # the 3 prompt templates (few-shot)
│   └── parse.py              # tolerant JSON extraction + schema validation
├── pipeline.py               # stages 1–3, timing, retries, fallbacks, streaming
├── engine/
│   ├── bayes.py
│   ├── graph.py
│   ├── bkt.py
│   ├── fsrs_sched.py
│   ├── ranker.py
│   └── session.py            # the adaptive quiz loop
├── simulate.py               # fast-forward days + retention chart (PNG + ASCII)
├── metrics.py                # timings, tokens/s, peak RSS, model file size
├── io_layer/
│   ├── base.py               # abstract IO interface
│   ├── terminal_io.py
│   └── box_io.py             # TFT + GPIO + camera (teammate)
├── ocr.py                    # camera image -> text (extra)
├── state/                    # saved learner state (JSON), FSRS cards
├── fixtures/                 # sample passages + fake LLM outputs
└── tests/
```

Language: **Python** (ExecuTorch tooling is Python/C++). Dependencies: `fsrs` (py-fsrs), `matplotlib` (chart), `psutil` (memory), GPIO/display libs for the box.

---

## 6. Data schemas

```jsonc
// Stage 1 output
{ "concepts": [
    { "id": "C1", "name": "Photosynthesis needs sunlight", "prereqs": [] },
    { "id": "C2", "name": "Chlorophyll absorbs light",     "prereqs": ["C1"] }
] }

// Stage 2 output
{ "summary": "Plants make their own food using sunlight, water and air..." }

// Stage 3 output (per concept)
{ "questions": [
  { "id": "Q1", "concept": "C1", "type": "recall",          // recall | application
    "stem": "Why do plants need sunlight?",
    "options": [
      { "key": "A", "text": "To absorb water",  "correct": false,
        "misconception": "Confuses the role of roots with leaves" },
      { "key": "B", "text": "To make food",     "correct": true,  "misconception": null },
      { "key": "C", "text": "To stay warm",     "correct": false,
        "misconception": "Thinks sunlight only provides heat" },
      { "key": "D", "text": "To grow taller at night", "correct": false,
        "misconception": "Confuses light with growth timing" }
    ],
    "explanation": "Sunlight gives the energy plants use to make glucose."
  }
] }

// Learner state (state/learner.json)
{ "concepts": { "C1": { "p_mastery": 0.62, "fsrs_card": {...}, "attempts": 3 } },
  "misconceptions": { "C1:Thinks sunlight only provides heat": { "p_holds": 0.78, "last_checked": "..." } },
  "attempts": [ { "q": "Q1", "picked": "C", "correct": false, "latency_ms": 4200, "ts": "..." } ] }
```

Misconceptions are identified by `concept_id + text` (the LLM generates them per question; similar ones can be merged by simple string similarity if time permits).

---

## 7. Engine logic (exact behaviour)

### 7.1 Bayes misconception detection (`bayes.py`)
- When a concept is answered wrong, start a **uniform prior** over that concept's misconceptions (from all its questions' distractors).
- Likelihood model (simple, hand-set):
  - `P(pick option o | holds misconception m) = 0.7` if `o.misconception == m`, else `0.3 / (n_options - 1)`.
  - Correct answer: `P(correct | holds m) = 0.15` (slip/guess).
- Update: `posterior[m] ∝ prior[m] * likelihood(observation | m)`, then normalise.
- **Next question selection:** among unanswered questions of the concept (and its prereqs), choose the one with the **highest expected information gain** (expected entropy reduction of the posterior). With few questions, a simple fallback: pick the question whose options cover the most remaining high-probability misconceptions.
- **Confirmed** when `max(posterior) ≥ 0.75` → show "Misconception detected: <text>" + the explanation.

### 7.2 Concept graph walk (`graph.py`)
- Concepts form a DAG from Stage 1 (`prereqs`). Usually a chain, which is fine.
- **Wrong** on concept C → after diagnosis, move **down** to C's prereqs, asking **recall** questions.
- **Right** at the base → move **up** step by step, asking **application** questions on each parent.
- Wrong on an application question on the way up → treat it as new diagnostic evidence, restart the local loop.
- **Depth cap:** max 2–3 levels down per session.
- **Implicit credit (FIRe-style):** a correct application answer on C gives partial credit to its prereqs: an FSRS "Good" review for C, plus a small BKT bump (e.g. +0.5 × learn rate) for each prereq.

### 7.3 BKT (`bkt.py`)
Per concept, params (config): `p_init=0.3, p_learn=0.2, p_slip=0.1, p_guess=0.25` (0.25 for 4-option MCQ).
```
correct:  P(L|obs) = P(L)(1-s) / (P(L)(1-s) + (1-P(L))g)
wrong:    P(L|obs) = P(L)s     / (P(L)s     + (1-P(L))(1-g))
then:     P(L) = P(L|obs) + (1 - P(L|obs)) * T
```
Application questions count as stronger evidence: use a lower guess rate for them (e.g. 0.15).

### 7.4 FSRS (`fsrs_sched.py`)
- Use the **py-fsrs** library (FSRS-6, default parameters). **Do not reimplement FSRS.**
- One FSRS card **per concept** (not per question).
- Map answers to ratings: wrong → `Again`; correct recall → `Good`; correct application → `Easy` (or `Good` with a bonus, configurable); correct after a hint/explanation → `Hard`.
- Only apply **one FSRS review per concept per session** (FSRS is designed for day-scale reviews; within-session sequencing is the Bayes/graph engine's job). Use the final outcome of the concept in the session.
- Misconceptions are **not** FSRS cards. Track `p_holds` and schedule a "relapse check" question with the concept's next review.

### 7.5 Ranker (`ranker.py`)
```
priority(C, t) = 1 - P_mastery(C) * R_fsrs(C, t)
```
Highest priority = most at risk of being unknown today → shown first in the revision plan.

### 7.6 Session flow (`session.py`)
1. Show summary.
2. Quiz starts at the **most advanced concept** (or ordered concept list) using recall/application questions.
3. Apply the walk logic from 7.1–7.3 after each answer.
4. End: print **report**: per-concept mastery %, detected misconceptions with explanations, FSRS next-review dates, ranked revision plan.
5. Save state to `state/learner.json`.

---

## 8. LLM pipeline (`pipeline.py`, `llm/`)

- **Three separate prompts** (small models do better with short, focused tasks). Few-shot with 1 good example each. Ask for **JSON only**.
- **Streaming / staging:** run Stage 1 + Stage 2 + questions for the first concept first, then start the quiz while remaining questions generate in a background thread. The student never waits for all questions.
- **Target:** 4–6 concepts × 2 questions = **8–12 questions** (min 3 is mandatory; more makes Bayes/BKT meaningful).
- **Robustness:**
  - `parse.py`: extract the first JSON block, fix trailing commas and missing quotes where possible, validate against the schema.
  - On failure: retry once with a stricter prompt → if still failing, **fallback**: plain MCQ without misconception tags (still meets the mandatory deliverable) → final fallback: plain-text questions printed as-is.
  - Cap `max_new_tokens` per stage.
- **Model is a config value.** Must work with whichever approved model is used.
- `fake_runner.py` returns fixtures so everything runs without the Pi / model.

---

## 9. Metrics (`metrics.py`): this matters to Arm judges

Print and save (also to README) a table:
| Stage | Time (s) | Tokens out | Tokens/s |
|---|---|---|---|
| Model load | | | |
| Concepts | | | |
| Summary | | | |
| Questions (each + total) | | | |
| **Total** | | | |

Also: model name, `.pte` file size (MB), quantization (e.g. 4-bit vs 8-bit), **peak RSS** (psutil), Pi model and RAM, and confirmation "network: offline" (e.g. check no default route / run with Wi-Fi off).
Stretch: compare 2 quantization settings or 2 thread counts in a small benchmark table.

---

## 10. Retention demo (`simulate.py`)

Retention plays out over days and the demo is 2 minutes, so we fast-forward:
- `--simulate-days 14`: a simulated clock steps day by day; on each scheduled review, simulate an answer (correct with probability = current R) and print:
  ```
  Day 1  review C2 (R=0.71 → after review S=5.2d)
  Day 3  review C1, C4
  Day 7  ...
  ```
- **Retention comparison chart** (`retention.png` + ASCII version in terminal):
  - *Study once, no revision*: recall % decaying via the FSRS forgetting curve from the first-session stability.
  - *With our schedule*: sawtooth staying around the target retention (~90%).
  - Use py-fsrs retrievability so the numbers come from the real model, not made up.

---

## 11. Tutor box (extra; teammate owns hardware)

Hardware: Raspberry Pi (8 GB) in a 3D-printed box, **TFT screen**, **buttons**, **USB camera**. **No mic, no STT, no TTS.**

IO interface (`io_layer/base.py`). The engine only talks to this:
```python
class IO:
    def show(self, text: str) -> None: ...                      # summary, question, feedback
    def show_question(self, q: dict) -> None: ...                # stem + A/B/C/D options
    def wait_button(self) -> str: ...                            # "A"|"B"|"C"|"D"|"NEXT"
    def capture_image(self) -> str: ...                          # returns image path (BoxIO only)
    def log(self, text: str) -> None: ...                        # metrics/logs, always to terminal
```
- `TerminalIO`: keyboard input, prints everything. **Default and always works.**
- `BoxIO`: screen = student view; buttons = answers; terminal (laptop over SSH) still shows metrics/logs for the judges.
- **Camera flow (extra):** capture textbook page → `ocr.py` (Tesseract, pending rules check) → text → same pipeline. In the demo, run the **organiser's passage as text first**, camera second.

---

## 11b. Dev hardware before the event (no Pi until hackathon day)

We **don't have the Pi until 14 Nov**. Dev setup:

| Machine | Use it for | Don't use it for |
|---|---|---|
| **Laptop** | Engine, fake LLM, tests, prompt tuning, simulation chart, **model export/quantization to `.pte`** | Final benchmarks |
| **Arduino UNO Q (4 GB, aarch64 Debian)** | Prove the **ARM Linux ExecuTorch build + `.pte` run** works; test prompts/JSON parsing on real ARM; test `metrics.py` | Final timing numbers (Cortex-A53 is much slower than Pi 5's Cortex-A76; treat timings as worst case) |
| **Raspberry Pi (8 GB), on the day** | Real run, real metrics | — |

Not useful: SimulIDE (microcontroller circuit sim, can't run Linux) and QEMU (too slow; meaningless timings).

**UNO Q steps:**
1. Use it as a Linux SBC (SSH/adb or USB-C hub). Verify: `uname -m` → `aarch64`, `free -h` → ~4 GB.
2. Add 2–4 GB swap before any build. Keep it cooled.
3. **Export + quantize the model on the laptop** (export needs lots of RAM), copy the `.pte` to the board.
4. Install ExecuTorch on the board: try the pip package first; otherwise build from source with the XNNPACK backend for aarch64. Build the LLM runner.
5. Run the 3 prompts on a fixture passage; verify JSON parsing + fallbacks; run `metrics.py`.
6. **Record every command in `README.md` → "Setup on ARM Linux"** so it can be replayed on the Pi on hackathon day.
7. If generation is very slow, reduce question count for testing only; the engine is count-agnostic.

Everything must stay **target-agnostic**: model path, thread count and max tokens come from `config.yaml`, with no hard-coded board specifics.

---

## 12. Timeline

**Before the hackathon (12–13 Nov):**
1. Get ExecuTorch running and export/run an approved-style small model on ARM (Pi if available). Record the exact commands in README. *(Biggest risk: do first.)*
2. Build the engine (Section 7) with `fake_runner` + tests.
3. Write and tune the 3 prompts on 3–4 sample passages (150–300 words, school-science style).
4. `simulate.py` + chart.
5. Teammate: assemble the box, implement `BoxIO`.
6. Draft the impact explanation with a placeholder for the passage-specific example.

**Hackathon day (6–8 h):**
- H1–2: model on the competition Pi → mandatory output (summary + ≥3 Qs + metrics). **Commit.**
- H3–5: connect the real LLM to the engine; tune prompts on the organiser passage; staging/streaming.
- H5–6: BoxIO integration; camera only if everything else is stable.
- H6–7: benchmarks, fallbacks test, demo rehearsal **with Wi-Fi off**.
- Last hour: README (metrics table, pitch, concrete example), GitHub push, submission form.

---

## 13. Demo script (~2 min)

1. "Wi-Fi is off." Show it.
2. Organiser passage → summary + diagnostic questions; terminal shows timings and memory.
3. On the box: answer one question **wrong on purpose** → "Misconception detected: ___" + explanation → system goes down to the basic concept → correct → climbs back with an application question.
4. End report: mastery per concept + FSRS revision plan.
5. `--simulate-days 14` + retention chart: "Without revision about 30% by day 7; with our schedule about 90%."
6. Optional: snap a textbook page with the camera → new quiz.

**Concrete example (fill in on the day):**
> "From the passage, the student picked '<wrong option>'. The system detected the misconception '<text>', explained it, verified with an application question, and FSRS scheduled the concept for Day X and Day Y. Predicted recall at day 7: ~30% without revision vs ~90% with it."

---

## 14. Non-negotiables for Claude Code

- Mandatory core first; **commit a working core before adding anything**.
- Engine is pure Python, model-agnostic, hardware-agnostic, and **unit-tested** with fixtures.
- Every LLM call: timed, token-counted, validated, with retry + fallback.
- No cloud calls anywhere. No network dependencies at runtime.
- Use **py-fsrs**, don't reimplement FSRS.
- Keep the code readable. Judges may read the GitHub repo.
