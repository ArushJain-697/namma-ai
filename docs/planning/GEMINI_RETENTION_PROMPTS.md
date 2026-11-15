# Gemini Deep Research prompts: retention, knowledge tracing, misconception diagnosis (3)

Paste each into Gemini Deep Research separately, then drop the reports into the chat.

Shared context (inside each prompt): an offline quiz tutor on a Raspberry Pi 5 for Class 6-10 students. Each
multiple-choice question's wrong options are linked to known student misconceptions in a knowledge graph
(about 3,800 misconceptions, about 5,000 concepts with prerequisite links, 120 "root" wrong beliefs). Today we use:
a Bayesian update to diagnose which misconception a student holds from the wrong options they pick, Bayesian
Knowledge Tracing (BKT) per concept, the prerequisite graph to check earlier concepts, and FSRS (py-fsrs 6) to
schedule revision. Everything must run offline on a small CPU with very few answers per student.

---

## 1. Knowledge tracing and misconception diagnosis that works with very little data

```
I'm building an offline quiz tutor for Indian Class 6-10 students that runs on a Raspberry Pi 5 (no internet, small
CPU). Each multiple-choice question's wrong options map to known student misconceptions in a knowledge graph
(~3,800 misconceptions, ~5,000 concepts with prerequisite links). Today I diagnose misconceptions with a simple
Bayesian update over the wrong options a student picks, and track mastery per concept with Bayesian Knowledge
Tracing (BKT). A student answers only 5-20 questions in a session.

Research, with sources from 2015-2026 and real numbers:
1. Knowledge tracing methods compared on public data (ASSISTments, EdNet, Eedi, Junyi): BKT and its variants,
   Performance Factors Analysis, logistic models (IRT, KTM, LKT), and deep ones (DKT, SAKT, AKT, simpleKT, and newer).
   Report AUC/accuracy, how many interactions they need, CPU cost, and interpretability. Which are best when data
   per student is tiny (cold start) and there is no training data from our own students?
2. Cognitive diagnosis models (DINA, DINO, G-DINA, NeuralCD, and newer) and Bayesian networks that diagnose
   specific misconceptions from which wrong option was chosen (distractor-based diagnosis). How many questions are
   needed for a reliable diagnosis? How do they handle guessing and slips?
3. How Eedi, ALEKS, Khan Academy, Mindspark, Duolingo and Carnegie Learning diagnose and track knowledge in practice,
   and what they report about accuracy and learning gains.
4. How to set BKT / Bayesian priors without our own data (from literature, from item difficulty, from teacher
   estimates), and how to validate a tracer honestly without real students (simulation methodology and its limits).

Output: a comparison table (method, data needed, accuracy, CPU cost, interpretable?, link); then a concrete
recommendation for our setup (what to keep, what to change) with the evidence; then what we can honestly claim in
a 3-minute hackathon demo and what we must not claim.
```

## 2. Spaced repetition beyond FSRS: scheduling concepts and misconceptions, not flashcards

```
My offline tutor uses FSRS (py-fsrs 6) to schedule when a student should revisit a concept or a misconception.
Research the state of the art in spaced-repetition scheduling and its evidence, 2015-2026, with numbers and links:
1. FSRS in detail: the model (difficulty, stability, retrievability), FSRS-4.5/5/6 changes, default parameters, how
   it is optimized, how many reviews it needs before personal parameters beat defaults, and benchmark results vs
   SM-2, Half-Life Regression (Duolingo), Ebisu, ACT-R, and neural schedulers (e.g. the open-spaced-repetition
   benchmark). Typical predicted recall after 1, 3, 7, 30 days with default parameters.
2. Scheduling CONCEPTS and MISCONCEPTIONS rather than individual flashcards: knowledge-graph-aware or
   prerequisite-aware scheduling, propagating a review of one concept to related concepts, scheduling "unlearning"
   of a misconception (refutation texts, contrasting cases) and how often it must be revisited.
3. Evidence from classrooms: effect sizes of retrieval practice, spacing and interleaving for school students
   (meta-analyses: Adesope 2017, Dunlosky 2013, Rohrer interleaving studies, and newer), especially for science and
   maths at ages 11-16, and any Indian studies.
4. Practical design of a short daily revision quiz: how many items, how to mix new vs due items, interleaving
   rules, what to do when a student misses days, and how existing apps (Anki, Duolingo, Quizlet, Eedi, Seneca)
   do it.

Output: a table of schedulers with benchmark numbers and links; the classroom effect sizes with sources; a concrete
daily-quiz algorithm for our setup; and the 3 most defensible numbers to show judges.
```

## 3. Using the misconception knowledge graph: next-question choice, root causes, and a demo that shows it

```
I have a knowledge graph for Class 6-10 subjects: ~5,000 concepts with prerequisite edges, ~3,800 misconceptions
attached to concepts, and 120 "root" wrong beliefs that group misconceptions across subjects (e.g. "a bigger number
always means more"). A small offline tutor on a Raspberry Pi uses it to diagnose students from multiple-choice
answers. Research, with sources 2015-2026 and numbers:
1. Adaptive question selection on a prerequisite graph: computerized adaptive testing, information-gain / expected
   entropy reduction, knowledge space theory (ALEKS), and graph-based remediation (go back to a prerequisite when a
   student fails). How many questions they need to locate a gap; simple algorithms that run on a small CPU.
2. Root-cause diagnosis: research on "root" or "deep" misconceptions that cause many surface errors across topics
   (conceptual change theory, p-prims, framework theories, Eedi misconception cascades), and evidence that fixing
   the root fixes downstream errors.
3. Building and checking prerequisite graphs automatically with LLMs and embeddings: methods, measured accuracy vs
   expert graphs, common errors, and cheap validation.
4. Remediation that works for misconceptions: refutation texts, contrasting cases, worked examples; effect sizes.
5. How products and research systems VISUALISE a student's knowledge state and misconceptions for teachers and
   students (knowledge maps, mastery maps, misconception dashboards) and which visualisations teachers find useful.

Output: recommended algorithms for next-question choice and root-cause diagnosis on our graph (with evidence and
CPU cost); a short list of claims about root beliefs we can make honestly; and 2-3 visualisation ideas for a live
3-minute demo, each with an example from a real product or paper and a link.
```
