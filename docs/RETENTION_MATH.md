# How Sakshi turns GURU's quiz into a diagnosis and a revision plan (the maths)

Code: `src/sakshi/link.py` (linking), `src/sakshi/retention/` (engine). Run on the Mac:
```bash
.venv-export/bin/python scripts/study_json.py passage.txt > result.txt        # GURU: summary + 3 questions
.venv-ml/bin/python scripts/retention_demo.py passage.txt result.txt          # link -> bank -> session -> plan
```
`--student human` lets a person answer in the terminal; `wrong`/`right` use a pretend student.

Pipeline: **passage → GURU questions → (1) option→misconception linking → (2) bank with graph prerequisites →
(3) Bayes diagnosis + (4) BKT mastery + (5) graph walk → (6) FSRS memory → (7) revision priority.**

---

## 1. Wrong option → misconception (retrieve, rerank, abstain)

The standard two-stage design for this task (also what top teams used in the 2024 Kaggle "Eedi: Mining
Misconceptions in Mathematics" competition; we adapted it, we did not invent it):

1. **Topic filter (the graph).** `Mapper.topics(passage)` fuses keyword rank and embedding rank with reciprocal
   rank fusion, `score(t) = 1/(60 + r_kw(t)) + 1/(60 + r_emb(t))`, keeps the top 3 topics. 4,073 beliefs → ~50.
2. **Retrieve.** Query `x = "question  Wrong answer: option"`, embedded with bge-small (unit vectors).
   For each candidate belief `m`: `cos(x, m) = e_x · e_m`. Keep the top k = 8.
3. **Rerank.** NLI cross-encoder (deberta-v3-xsmall) gives `P_entail(x ⇒ statement_m)`.
   `score(m) = cos(x, m) + 0.3 · P_entail`. Pick the argmax, but each belief at most once per question.
4. **Abstain.** If `cos < 0.76` the option stays untagged (a plain wrong answer). An untagged option is not
   evidence for any belief, so a weak link cannot create a false diagnosis.

Measured on 3,647 teacher-labelled (option → misconception) pairs, candidates = the item's own topic (~16):
recall@1 **53%**, recall@3 **81%**; answering only the most confident 75%: precision 57%; top 25%: 64%.
NLI rerank on a 400-pair sample: 46% → 47% (small gain; kept because it is cheap).

## 2. Bank

Each GURU question gets a concept (the concept of the best-matching belief for question + answer + evidence).
Graph prerequisites of those concepts (up to 2 each) are added. Every concept with fewer than 2 questions gets
template questions built from the graph itself: right option = a belief's `fix`, wrong options = other beliefs'
`statement`s (padded from the same topic), each tagged. So the walk-down always has something to ask, with no
extra model call.

## 3. Which belief does the student hold? (Bayes)

Hypotheses for a concept: its beliefs `m₁…m_k` plus `NONE`. Prior uniform: `P(h) = 1/(k+1)`.
Likelihood of picking option `o` on question `q` (`n` options, `W` wrong ones):

| hypothesis | picks own belief's option | picks correct | picks another wrong |
|---|---|---|---|
| `m` on this question | 0.70 | 0.15 | 0.15 / (W − 1) |
| `m` not on this question | 1/n | 1/n | 1/n |
| `NONE` | 0.50 / W | 0.50 | 0.50 / W |

Update: `P(h | o) = P(o | h) P(h) / Σ_h' P(o | h') P(h')`.
**Next question = max expected information gain:**
`EIG(q) = H(P) − Σ_o P(o) · H(P(· | o))`, with `P(o) = Σ_h P(o|h) P(h)` and `H(P) = −Σ p log₂ p`.
Report: posterior ≥ 0.75 → "detected"; ≥ 0.50 → "possible".

## 4. Has the student learned the concept? (Bayesian Knowledge Tracing)

Parameters: `P(L₀) = 0.3`, learn `T = 0.2`, slip `s = 0.1`, guess `g = 0.25` (recall, 1 in 4) or `0.15`
(application).
- correct: `P(L | ✓) = P(L)(1−s) / [P(L)(1−s) + (1−P(L)) g]`
- wrong:   `P(L | ✗) = P(L) s / [P(L) s + (1−P(L))(1−g)]`
- learning from the attempt + feedback: `P(L)ₙₑₓₜ = P(L|obs) + (1 − P(L|obs)) T`
- correct application answer → each prerequisite gets implicit credit `P + (1−P) · T · 0.5`.

Example from the Mac run: start 0.30; one wrong recall answer → 0.30·0.1/(0.03 + 0.7·0.75) = 0.054 → +learning
0.054 + 0.946·0.2 = **0.24**. A right answer after the walk-down climbs to **0.63–0.73**.

## 5. Graph walk (session)

For each top concept: recall question → right: done. Wrong: diagnose (≤ 2 EIG-chosen questions, keep one back),
show the belief and its fix, walk **down** to prerequisites (≤ 2 levels), climb back **up** with an application
question: right → FSRS "Hard" (learned with help), wrong → "Again". Right first time on application → "Easy".

### 5b. Climbing back up is gated by BKT (added 14 Nov)
After walking down, the climb back up happens one level at a time, and only on a solid base:
- a prerequisite answered wrong (and still below the gate after re-teaching) **stops the climb**: the concept above
  is rated Again and saved in `state.blocked` (concept → shaky prerequisites), first in line for the review day;
- otherwise the concept gets an **application question** (graph probe; guess rate 0.15). Climb on only if right
  **and** `P(L) ≥ 0.6`. If not: show the fix, one more application question, then stop (Again).
- 0.6 is "ready to build on", not mastery (the classic BKT mastery line is 0.95, Corbett & Anderson 1995).
  One right application answer from 0.24 gives `0.24·0.9 / (0.216 + 0.76·0.15) = 0.655`, then `+ (1−0.655)·0.2 = 0.72`.
- A prerequisite with no questions in the bank cannot be checked, so it does not block.
- Application questions come from each misconception's **probe** (a situation question in the graph). Options are
  all statements: the belief's fix (right), the belief itself, two neighbouring beliefs.

## 6. When will they forget? (FSRS-6, py-fsrs 6.3.2, 21 weights w₀…w₂₀)

Memory state per concept: stability `S` (days until recall falls to 90%), difficulty `D ∈ [1, 10]`.
- **Recall probability** after `t` days: `R(t, S) = (1 + F · t / S)^(−w₂₀)`, `F = 0.9^(−1/w₂₀) − 1`
  (so `R(S, S) = 0.9`).
- **First rating** `G ∈ {1 Again, 2 Hard, 3 Good, 4 Easy}`: `S₀ = w_{G−1}`, `D₀(G) = w₄ − e^{w₅(G−1)} + 1`.
- **Difficulty:** `ΔD = −w₆ (G − 3)`, `D' = D + ΔD · (10 − D)/9` (linear damping),
  then mean reversion `D'' = w₇ D₀(4) + (1 − w₇) D'`.
- **Success (G ≥ 2):** `S' = S · (1 + e^{w₈} (11 − D) S^{−w₉} (e^{w₁₀(1−R)} − 1) · h · b)`,
  `h = w₁₅` if Hard else 1, `b = w₁₆` if Easy else 1. Harder to recall now (low R) ⇒ bigger gain.
- **Lapse (G = 1):** `S' = min(S, w₁₁ D^{−w₁₂} ((S + 1)^{w₁₃} − 1) e^{w₁₄(1−R)})`.
- **Same-day review:** `S' = S · e^{w₁₇ (G − 3 + w₁₈)} · S^{−w₁₉}`.
- **Next review** for desired retention `r = 0.9`: `I = (S / F) · (r^{−1/w₂₀} − 1)` days.

From the Mac run: a concept rated Again is due tomorrow (15 Nov); its R falls 1.00 → 0.66 (3 days) → 0.55 (10 days).

## 7. What to revise first

`priority(C, t) = 1 − P_mastery(C) · R_fsrs(C, t)`. High if probably never learned (low BKT) **or** probably
forgotten (low FSRS recall). Untested concepts have R = 0 ⇒ priority 1.

## 8. Review day (`sakshi review`, `src/sakshi/retention/review.py`)
1. **Forgetting:** `P(L)_today = P(L)_saved × R(t, S)` (FSRS recall since the last review, floor 0.05).
2. **Held beliefs** (confirmed, suspected or still held), riskiest concept first: a NEW question aimed at the
   belief, then Bayes with two hypotheses, holds `h` or not `¬h`, using the likelihoods of section 3:
   `P(h | o) = P(h)·P(o|h) / (P(h)·P(o|h) + (1−P(h))·P(o|¬h))`. Right but still ≥ 0.5 → one more question.
   - still ≥ 0.5: show the fix again, FSRS Again (due sooner);
   - below 0.5: cleared, FSRS Good, then **follow the graph**: a belief this one `causes` (288 edges), else
     the nearest belief (bge-small cosine) with the **same root belief** (120 roots), other concepts first. Prior
     0.3; picking it gives `0.3·0.7 / (0.21 + 0.7·0.5/3) ≈ 0.64` → a new suspected belief, "same root as …".
3. **Blocked climbs:** the prerequisite's application question first, then the concept; same 0.6 gate.
4. **Other due concepts** (FSRS due ≤ today): one application question each.
5. One FSRS review per concept touched, then save.

Multi-day check (`scripts/retention_days.py`, pretend students guess at random when they do not know):
- learns from feedback: climbs up on day 0 (P(L) 0.73 ≥ 0.6); review days clear beliefs and leave nothing blocked;
- never learns: climbs stop at shaky bases; a belief that only looked held from one random guess on day 0 (55%)
  is cleared on day 1 (36%); the root belief is followed into another topic; "Aquatic life" stays blocked until
  day 7, when its base is finally solid and it climbs back up.
Tests: `tests/test_review.py` (blocked/unblocked climb, untestable prerequisite, state saved, belief still held,
cleared → related belief found, forgetting).

## Honest limits
- Linking is right about half the time at top-1 (81% in top 3); abstaining keeps weak links out of the Bayes step.
- Bayes and BKT parameters are hand-set from the literature defaults, not fitted to our students (no student data yet).
- FSRS uses py-fsrs default weights (trained on Anki users, not school children).
- Padded template options can bring in a belief from a neighbouring concept of the same topic.
