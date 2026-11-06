# SAKSHI: Master Bible v1.3
### Namma AI Hackathon, Problem 1: AI for Inclusive Education

*Version 1.3, 4 Nov 2026: red-teamed (three rounds and a mock judge, 23 flaws, see `RED_TEAM_LOG.md`). Structure follows the Hackathon Winning Blueprint (Part 12.3). Copies the method, never another project's idea. v1.1 reframed the project around the student and aligned it with the official problem statement (section 1). v1.2 adds the blueprint's "impressive" machinery: the trap beaten live and measured by script (Counterfactual Passage Test), a judge-played edit, judges' phones as students over the Pi's own hotspot, a Reread Loop, and a power-bank and classroom-throughput angle for Arm. See the scorecard (section 1b) and changelog.*

**Status in one line: this is a desk plan. Nothing here has been run on a Raspberry Pi. Every speed, memory and quality figure for our system is an estimate or `TODO(measure)`.**

**Evidence labels**
- **[SOURCE]** came from a page or repo, read by the research agents. Most secondary sources were not rechecked by a second reader.
- **[ESTIMATE]** is arithmetic or judgement of ours.
- **[DESIGN]** is our proposal and is untested.
- **[UNKNOWN]** must be answered before anyone relies on it.

**Key dates:** proposal **6 Nov** · finalists told by 11 Nov · live event **14 Nov** (6-8 hours of building, at a NASSCOM office) · winners 19 Nov.

---

## 0. One-line pitch

**Sakshi gives a student studying alone a short summary and a self-check quiz for any 150-300 word passage, on a Raspberry Pi with no internet. The model is never allowed to write the answer key, and every answer points to the sentence that proves it, so the student can check themselves without a teacher.**

*Sakshi* means "witness". Every question has to name its witness: the exact sentence in the passage that proves its answer. For the student, the witness **is** the feedback: get it wrong, and Sakshi shows the one sentence to reread. The name is a proposal and can change.

**Named parts (blueprint 7.14):** the **Fluent Wrong Answer Trap** (what we beat) · the **Witness Gate** (answer-first selection plus checks: no witness, no question) · the **Counterfactual Passage Test** (how we prove it, by script) · the **Reread Loop** (how the student gets a second chance on the sentence they missed) · the **Classroom Hotspot** (one offline Pi serving a room of phones or tablets).

---

## 1. Rules dossier

### Official problem statement (verbatim from the hackathon page, Problem 1)

> **Societal Challenge.** Students in underserved and low-connectivity regions may face barriers to learning, including limited internet access and a lack of timely, understandable study support. Can affordable offline Edge AI help overcome one clearly identified learning barrier?
>
> **Hackathon Task.** Build an offline learning assistant using ExecuTorch on Raspberry Pi. Identify a specific learning-access barrier (for example, inability to access study support without connectivity) and show how locally generated learning aids help address it. For this one-day challenge, the demonstrable intervention is offline educational content support—not a complete education platform.
>
> **Minimum Deliverables (Mandatory)**
> 1. Identify one learning barrier, the intended learner group and how the PoC addresses that barrier.
> 2. Process one organiser-provided educational passage (approximately 150–300 words) with an approved lightweight model running locally through ExecuTorch on Raspberry Pi.
> 3. Generate a short, understandable summary and at least three relevant quiz questions as an accessible, offline study aid. Terminal output is sufficient.
> 4. Demonstrate operation without cloud AI inference; report approximate inference time, model used and model size or memory usage where measurable.
> 5. In a brief impact explanation, show how the generated aids could reduce the chosen learning barrier, with one concrete example from the supplied passage.
>
> **Expected Outcome.** A working offline PoC that converts a short passage into a summary and three quiz questions, accompanied by a credible demonstration of how this supports learners facing the identified access barrier.
>
> **Not required.** Full chatbot, multilingual support, document management, custom interface or mobile app.

### What the wording tells us (each point drives a change in v1.1)

| Phrase in the brief | What it means for us | Where it lands |
|---|---|---|
| "**Students** … may face barriers"; "supports **learners**" | The user is the student. The teacher is a supporting role, not the main user. | Sections 0, 2, 11, 23 |
| "lack of **timely, understandable** study support" | Our barrier: no one to check understanding at the moment a student studies, in a place with no connection. | Section 2 |
| "**one clearly identified** learning barrier" | Name one barrier and one learner group. Don't list several. | Section 2 |
| "**offline learning assistant**", "**study aid**" | Output is for a student revising alone, so feedback must work without a teacher present. | Layers 6-7, tiers |
| "**short, understandable** summary" | Readability is a requirement, not polish. Grade-level prompt plus a readability check, never cut. | Layer 3, cut list |
| "at least three **relevant** quiz questions" | Code-picked answers must be key ideas, not stray words. Relevance scoring and a relevance rating. | Layer 2, metrics |
| "**approximate** inference time, model used and model size **or** memory usage **where measurable**" | The required measurement is light: time, model name, `.pte` size, peak memory. Thread sweep and KleidiAI are extras. | Layer 8, metrics, cut list |
| "one **concrete example from the supplied passage**" | Impact explanation is filled in live from the organiser's passage, using one question and its witness. | Section 11 |
| "**credible** demonstration of how this supports learners" | Show a student-shaped interaction (answer wrong, get pointed to the sentence), not only a printout. | Section 11 |
| "**not a complete education platform**"; "Not required: chatbot, multilingual, document management, custom interface, mobile app" | Terminal only. No accounts, no content library, no Kannada in v1, no app. | Sections 15, 16 |
| "**affordable** offline Edge AI" | Cost per school matters; one shared Pi, costed. | Sections 12, 21 |

### Other rules

| Item | What we know | Source |
|---|---|---|
| Scoring | **No rubric published.** Closest wording: "practical implementation, measurable results and societal relevance". A production-ready app or polished UI is not expected. | Hackathon page |
| Selection | Proposal screened by 10 Nov; top 30-40 teams told by 11 Nov | Hackathon page |
| Mandatory tech | ExecuTorch on Raspberry Pi; "approved lightweight model"; no cloud inference | Hackathon page |
| Team | 1-3 members, Indian nationals, same college or organisation, one Team Leader who alone registers. Students need a college nomination. | Hackathon page |
| Deliverables | GitHub project submitted through the challenge form | Hackathon page |
| Support | Virtual training for finalists before the event; mentors through support@nammaAIchallenge.com | Hackathon page |
| Not required | Full chatbot, multilingual support, document management, custom UI, mobile app | Hackathon page |

### Requirement map

| Mandatory deliverable | How we meet it | State |
|---|---|---|
| 1. One barrier, learner group and how the PoC addresses it | Section 2: barrier = no timely way to check understanding while studying, in schools with no connection; group = Class 6-8 students in English or bilingual sections of Karnataka government schools | Drafted |
| 2. Organiser passage (~150-300 words) processed locally with an approved model through ExecuTorch on a Pi | Layers 1-5; model subject to organisers' list; gate warns rather than rejects near the word limits | Not run |
| 3. Short, understandable summary and at least 3 relevant quiz questions, as an accessible offline study aid, terminal output | Layers 2-7: grade-level summary with readability check; relevance-scored answers; student quiz mode in the terminal | Not run |
| 4. No cloud inference; approximate inference time, model used, model size or memory | `prove_offline.sh`; Layer 8 prints a four-line run card (time, model, `.pte` size, peak memory) at the end of every run | Not run |
| 5. Brief impact explanation with one concrete example from the passage | Filled in on the day: one question from the organiser's passage, a wrong answer, and the witness sentence the student is sent back to (section 11) | Template only |
| Expected outcome: "credible demonstration of how this supports learners" | Judges take the quiz on their own phones from the offline Pi (or the terminal quiz as fallback), with the witness highlight and the Reread Loop | Sections 7, 11 |

### Questions for the organisers (send today)

1. Which models are on the approved list? Is Llama 3.2 1B through ExecuTorch acceptable?
2. Who supplies the Raspberry Pi, and which model and RAM?
3. **May teams bring code written before 14 Nov, including reused open-source code?** This decides the build plan.
4. What must the proposal contain? Is there a template or word limit?
5. What are the judging criteria and who judges?
6. Can we bring our own laptop, passages and exported model files? Is venue internet available for setup?
7. What is the demo format and length (stage, table, recorded), and how is the organiser's passage delivered (file, paper, on screen)?
8. Are venue power outlets provided, and may we run our own Wi-Fi hotspot (with no uplink) in the room?
9. How much RAM does the Pi we'll be given have? (A 1B model plus a runner can need 2 GB or more; unknown RAM changes the plan.)

### Proxy rubric until they answer

The nearest public model is the ExecuTorch Hackathon: technical 40, use case 25, local and privacy 15, deployment 10, presentation 10 [SOURCE, different event]. Arm + ExecuTorch rewarded reliability 20 and performance 20 [SOURCE, different event]. **These are analogies, not Namma's rules.** The plan puts weight on measured reliability and performance because both Arm-linked rubrics do.

---

## 1b. Idea scorecard (blueprint 12.2)

Scored honestly against the blueprint's own weights. v1.1 was correct but quiet: it had the rigour (trap, fence, tiers, held-out, admitting limits) and little of the theatre (trap beaten live, judge participation, spectator layer, visible adaptation, physical angle). v1.2 adds the theatre without changing the core.

| Criterion | Weight | v1.1 | v1.2 | What moved it |
|---|---|---|---|---|
| Human stakes | ×3 | 4 | 4 | Unchanged. Softer than his projects: no one is physically hurt. Compensated by a trap that is visible and measured |
| Named trap | ×3 | 4 | 5 | Trap beaten **live** on a counterfactual passage, not a saved run |
| Category shift | ×2 | 3 | 4 | "Follows the passage, not its memory", proven by a test the baseline fails |
| Rubric coverage | ×3 | 4 | 4 | Every deliverable met; no rubric published |
| Sponsor tech load-bearing | ×2 | 2 | 3 | Arm speed-up turned into "students served per period" and "passages per charge". Still honest that llama.cpp exists |
| Independent evidence | ×2 | 3 | 4 | Adds a physical measure (energy) and a script-scored fidelity test |
| Provable in event time | ×2 | 3 | 5 | Headline metric scored by script, not slow human rating |
| Live, participatory demo | ×2 | 2 | 5 | Judges answer on their own phones; a judge edits a fact and watches one question regenerate |
| Spine by checkpoint | ×3 | 4 | 4 | Spine unchanged; theatre is layered on after |
| Reuses your pattern library | ×1 | 2 | 2 | |
| Low demo variance | ×1 | 4 | 4 | Phone page is cut first; terminal still covers every beat |
| **Total (max 120)** | | **≈80, Rework** | **≈99, Go** | |

**Red-team re-score (v1.3):** the v1.2 self-score of about 99 was generous. After three red-team rounds (`RED_TEAM_LOG.md`) the honest figure is about **88**, just over the "Go" line of 85, rising to about **94** only if tickets 8c (the trap really fires with the passage present), 8d (hotspot) and 8g (priced bill of materials) come back well. Mock-judge paper score on the nearest public rubric: **69 of 100**, projected 77. Lowest criterion: deployment ("affordable" is unpriced, device access unknown).

**Kill-rule check:** person and moment named ✓ · trap demoable live ✓ · hardware obtainable (Pi 5, power bank, USB power meter) ✓ · demo doesn't need venue internet (Pi's own hotspot, no uplink) ✓ · "isn't this just a quiz generator?" answered in one sentence (section 14) ✓.

---

## 2. The problem: person, moment, cost

**Person:** a Class 6-8 student in an English or bilingual section of a Karnataka government school with no internet.

**Moment:** a study period, a library period or the minutes after class, when the student rereads today's textbook passage on their own. They can read every word but can't tell whether they understood it. The teacher has 40 other students, and the school has no connection, so online help and AI tutors aren't available at that moment.

**Cost:** the student moves on believing they understood, and finds out only at the test, if at all. If an AI tool fills that gap with a fluent but wrong answer key, it is worse: the student is told they are wrong when they are right, or "learns" an error, and **no one is there to catch it**. A study aid that does this does more harm than no aid.

**The barrier, in one line (deliverable 1):** *no timely, understandable way for a student to check their own understanding of a passage while studying, in a school with no internet.* This is the brief's own example ("inability to access study support without connectivity") made specific.

**The teacher's role (supporting, not the user):** loads the day's passage onto the shared Pi, or picks one already there, and can look over any AMBER item. The PoC works for the student without the teacher present.

### Deliverable text (barrier, group, how)

> **Barrier:** Many Class 6-8 students can read a passage without understanding it, and when they study on their own there is no timely way to check. In schools without internet, online help and AI tutors are out of reach.
> **Learner group:** Class 6-8 students in English or bilingual sections of Karnataka government schools, where about 63% of schools lack internet.
> **How the PoC addresses it:** On one shared Raspberry Pi, with no connectivity, a student gives Sakshi a 150-300 word passage and gets a short, simple summary and at least three questions to answer. When they answer wrongly, Sakshi shows them the exact sentence in the passage that holds the answer, so they reread the part they missed. The model never writes the answer key: code picks each answer from the passage, so the feedback cannot be invented. Whether this improves learning is something a later pilot would need to test.

### Killer facts

| Fact | Source quality | Use in |
|---|---|---|
| 18,007 of 48,527 Karnataka government schools have internet, so about 63% do not (UDISE+ 2025-26) | News report of official data | Hook, proposal |
| 51.7% of all Karnataka schools have internet, against 67.4% nationally | News and PIB | Proposal |
| 29% of Karnataka Class 6 students are proficient or above in language, against 33% nationally (PARAKH 2024) | Secondary source | Proposal |
| A small survey found Class 7 English-medium students "read texts, but fail to understand" (201 students, 20 schools; the source favours mother-tongue education) | Small, with a stated position | Q&A only |
| Classroom quizzing effect g=0.499; middle school 0.597; with feedback 0.537 vs 0.374 without | Meta-analysis | **Core of the student framing:** self-quizzing helps, and feedback roughly adds half again. The witness sentence is our feedback. |
| LENTERA's frontend code silently marks choice 1 correct when the answer key is missing | Read from code, not run | Trap beat, only after we confirm it by running |

### Claims we do not make

- Learning gains. No trial found tests AI-generated quizzes.
- That reading a machine summary helps. The evidence is for students writing summaries. We say the summary is a short, simpler restatement to read before the questions, nothing more.
- Time saved for teachers. Nothing measures quiz preparation time, and the teacher is no longer the headline user.
- That students lack internet at home. 83.3% of rural households have it nationally, and about 90% of 14-16 year olds have a smartphone at home. We claim the **school** gap: the place and time where the student studies, with a school device, has no connection. Home phones are usually shared, data-limited and not the student's own; say this only if we can source it, otherwise stay with the school claim.
- That every student gets a Pi. It is one shared device per school or classroom, used in turns.
- A Kannada-medium solution. Version 1 is English only, which the brief allows ("multilingual support" is not required).

---

## 3. The trap

### The Fluent Wrong Answer Trap

A small model writes polished questions whose answers can come from its own memory, not the passage. Polish looks like correctness, so nobody gets a signal that anything is wrong.

**Why it is worse for a student than for a teacher.** A teacher might spot a wrong key. A student studying alone is the person *least* able to: they are using the quiz precisely because they are unsure of the content. If the key says they're wrong, they believe it. So a study aid for students must be right by construction, or not speak.

**Why the obvious fix fails.** The obvious fix is to check that the answer appears in the passage. The evidence says this is not enough [SOURCE: Pi 5 study, arXiv 2610.33732]:
- Span matching hit **96% on both correct and unanswerable** answers from a 7B model, so a real phrase can still fail to answer the question.
- Only **36-56%** of correct answers from 1.5B and 3B models matched a span, so a strict check also rejects good answers from small models.

So checking after generation is weak in both directions. That finding drove the design below.

### How we beat it: answer-first generation [DESIGN]

**Code picks the answer before the model writes anything.** The steps are:
1. Code picks a sentence from the passage and a term in it.
2. The model is asked only to write a question whose answer is that term.
3. Code builds the wrong options from other parts of the passage.

The key is then correct by construction relative to the passage. The remaining risk moves to whether the *question* really asks for that term, and that is what the checks look at. For the student, the witness sentence is shown with every answer, so even a badly worded question sends them back to the right line of text.

**Tradeoff stated openly:** this favours recall-level questions over inference. We accept that, because a small model on a Pi writing inference questions is the riskiest thing it could do.

### Making the trap visible: counterfactual passages [DESIGN]

The trap is invisible on ordinary passages, because the passage and the model's memory agree. It shows up only when they **disagree**. So we write passages where one fact deliberately differs from general knowledge, or is local and unknowable:
- **Changed fact:** a science passage saying water boils at 90 °C at the hill station in the story (true at altitude, but the model "knows" 100 °C).
- **Local fact:** "In 1999, our town repainted the old bridge" (the model has no way to know, so it guesses).
- **Swapped name or number:** a history-style passage about a fictional village fair held in *Magha*, not the month a model would expect.

A model writing its own key tends to answer from memory and is caught. Sakshi's key comes from the passage, so it follows the passage by construction. This is the blueprint's **evade, then catch** beat (7.4), and it doubles as our headline metric (section 10), scored by script.

Prior work studies this failure under the names "knowledge conflict" and "context faithfulness", including with counter-memory passages: Xie et al. 2023, [*Adaptive Chameleon or Stubborn Sloth*](https://arxiv.org/pdf/2305.13300v1); [*Investigating Context-Faithfulness in LLMs*](https://arxiv.org/html/2409.10955v1); [*LLMs' Reading Comprehension Is Affected by Parametric Knowledge*](https://fugumt.com/fugumt/paper_check/2404.06283v2_enmode) [SOURCE, search snippets only; none of the papers read, and none isolated small models]. **Read the first before quoting it.** We say we apply a known test to a classroom tool, not that we discovered it. A snippet hints that smaller models lean more on stored answers, but that is not established for a 1B model, which is why ticket 8c tests our own.

**Honesty line:** counterfactual passages are chosen to expose the trap, so the baseline's failure rate on them is **not** its failure rate on ordinary passages. We report both sets separately.

---

## 4. Positioning

**Everyone generates quizzes. We only release what traces back to the passage, and we refuse the rest.**

**Sharper form (v1.2), for the stage:** *"Most quiz generators answer from what the model remembers. Sakshi answers from what the passage says, and we prove it on passages built to make memory wrong."*

| Competitor | What it does | Where we differ | One-sentence answer |
|---|---|---|---|
| **LENTERA** (Gemma 3n Ollama Prize) | Offline summaries and quizzes through Ollama on a $350-500 x86 box with 16GB RAM | No retries, output validation or metrics in the code read | "They proved offline summaries and quizzes are wanted; we add a checked answer key on far cheaper Arm hardware." |
| **Toddle AI** (self-reported 3rd, ExecuTorch Hackathon) | Llama 3.2 1B on ExecuTorch, with code computing facts and the model explaining them | Different domain and device; its README says it has no committed latency numbers | "Same principle, and we publish the measurements." |
| **ALAB** | Android study app using ExecuTorch and Qwen for quizzes from PDFs | Compares answers to no source | "It validates format; we validate origin." |
| **UNIVERSAL-OFFLINE-AI** (created 3 Nov, possible rival) | Maps itself to this brief; llama.cpp on a laptop, no output validation | Not ExecuTorch on a Pi | Don't name it unless asked. |
| **Kolibri, RACHEL, Internet-in-a-Box** | Offline delivery of existing content | They deliver content; we generate checks from any passage. Kolibri's AI drafting status is unconfirmed. | "We could sit alongside these." |
| **DIKSHA** | Downloadable content; Ask DIKSHA exists, on-device status unverified | Works on any passage the school loads, with no connection, and gives the student feedback | "We're complementary, not a replacement." |
| **Shiksha Copilot** (Karnataka, 1,043 teachers in one study) | Teacher planning tool | It serves the teacher; we serve the student studying alone. Its on-device status is unverified | "It shows Karnataka classrooms will use AI help; we give the student a self-check that works with no connection." |
| **Arm's own material** (course, Learning Paths, Bharat AI-SoC brief) | Shows Llama through ExecuTorch on a Pi 5 is an accepted pattern | We apply it to a specific user and add a validation layer | "We followed Arm's path, then measured it." |

**Do not claim "first".** Every piece has prior art. The GitHub search found no ExecuTorch + Pi + passage-to-quiz project, but it was partial.

---

## 5. The one principle

**No witness, no question.** A question reaches a student only if code can point to the sentence that proves its answer. And every time the student answers, right or wrong, they see that sentence.

---

## 6. The ordered questions, which become the pipeline

| # | Question | Module | Who decides |
|---|---|---|---|
| 1 | Is this passage usable? | `gate.py` | Code |
| 2 | What does the passage say, in short and in simple words, with a witness for every summary sentence? | `generate.py` (summary) | Code picks the sentences; model only simplifies each; code checks support, numbers, readability |
| 3 | Which ideas matter, what are the candidate answers, and where are their witness sentences? | `select.py` | Code; uses the summary as one relevance signal |
| 4 | What question asks for this answer? | `generate.py` (stems) | Model, then code checks |
| 5 | What are the wrong options? | `distract.py` | Code |
| 6 | Does each item pass every check, and which tier is it? | `checks.py` | Code |
| 7 | How does the student use it, and what if they miss one? | `quiz.py` (student mode, Reread Loop) | Code: ask, take an answer, show the witness, ask again from the missed sentence |
| 8 | What did this cost? | `metrics.py` | Code: run card of time, model, size, memory, energy |
| 9 | What changes if one fact in the passage changes? | `regen.py` | Code finds the changed sentences; model rewrites only what's affected |
| 10 | How does a room use one Pi? | `serve.py` + `web/index.html` (Classroom Hotspot) | Code: serves the prepared quiz to phones over the Pi's own Wi-Fi, no internet |

**Order (v1.1, revised v1.3):** the summary sentences are chosen by code before selection, so a term in one of those central sentences scores as more relevant (Layer 3, signal 2). The model never influences which sentences are central, so selection is independent of the model and still works if every summary sentence falls back to its source.

---

## 7. Layer by layer

Worked example passage for this section (ours, illustrative):

> "Iron rusts when it reacts with oxygen and water. Rust is a reddish-brown layer that flakes away from the metal. Painting a gate stops air and moisture from reaching the iron. In 1999, a town in our district repainted its old bridge to protect it..."

### Layer 1: passage gate
- **Mechanism:** count words; reject outside 150-300 with a stated reason. Allow an override flag only for testing.
- **Example:** a 90-word passage returns `REJECTED: 90 words, need 150-300`.
- **Edge cases:** the organiser's passage may be slightly outside "approximately 150-300", so use a soft margin of 10% that warns instead of rejecting [ESTIMATE].
- **Test:** 149, 150, 300 and 301 words; empty input; non-ASCII punctuation.

### Layer 2: summary (short and understandable)
- **Why it matters:** the brief asks for a "short, **understandable** summary". For a student who read the passage without understanding it, the summary is the simpler second telling. Readability is a requirement here, not polish, and it is never on the cut list.
- **Why v1.3 changed this (red-team F11):** the student reads the summary *first*, and in v1.2 it was the one model-written part with no witness, protected only by a number check. A non-numeric claim from the model's memory would reach the person least able to spot it. The principle must cover the summary too: **no witness, no summary sentence.**
- **Mechanism (default, witnessed summary) [DESIGN]:**
  1. Code ranks passage sentences by centrality (content-word frequency, overlap with the topic word, position) and picks the top 2-3, kept in passage order.
  2. For each, one short model call (about 60-100 tokens in): "Rewrite this sentence in simple words for a Class 6 student. Keep every number and name. Add nothing." The model sees **only that one sentence**, so it cannot import facts from elsewhere in the passage or from memory about the rest.
  3. Code checks each rewrite against its source sentence (below). A summary sentence that fails after 2 retries is replaced by its source sentence verbatim, labelled `FALLBACK`.
  4. The 2-3 results are joined as "In short". Each summary sentence carries its source sentence number, shown in the report.
- **Comparison arm (the v1.2 design):** one model call over the whole passage asking for 2-3 simple sentences. Rules adapted from LENTERA (MIT): `paraphrase_and_translate.ts` L22, `generate_search_summary.ts` L59-64, and grounding from `generate_mindmap.ts` L61. Grade-level wording from `elix/index.ts` L14-18. Ticket 7b runs both and keeps the better one on faithfulness first, readability second; the choice and numbers are reported.
- **Cost:** 2-3 short calls instead of one long one. Prefill is smaller (about 100 tokens each instead of about 460), decode about the same [ESTIMATE].
- **Trade-off, stated openly:** a summary of 2-3 simplified key sentences is less fluent than a free summary and can miss a point that no single sentence makes. We accept that for a witness on every line.
- **Checks:**
  - 30-80 words (HARD, "short").
  - Every **number** must appear in the passage (HARD).
  - **Readability (WARN, one retry):** average sentence length 15 words or fewer, and a Flesch-Kincaid grade at or below the passage's own grade, or 7, whichever is higher [DESIGN; thresholds `TODO(set after first run)`]. Syllables from `english-syllable` (MIT-style). A summary harder to read than the passage defeats its purpose.
  - **Support check (HARD, v1.3):** at least 70% of a summary sentence's content-word stems appear in its own source sentence [DESIGN; threshold `TODO(set on dev set)`]. A rewrite that drifts away from its source fails.
  - New names WARN (a capitalised word or number not in the source sentence).
  - Copying WARN applies only to the whole-passage comparison arm; in the default path the extractive fallback is a copy by definition.
- **Fallback:** applied per sentence (see Mechanism step 3): a rewrite that fails after 2 retries is replaced by its own source sentence, labelled `FALLBACK`. If the model won't load at all, the summary is the 2-3 central source sentences, labelled `FALLBACK`.
- **Example:** if the summary says "painted in 1989" while the passage says 1999, the number check fails and it retries. If it says "Ferrous materials undergo oxidation upon exposure to atmospheric moisture", the readability check fires and it retries with the simpler-words reminder.
- **Edge cases:** a summary that is a copy; truncation at the token limit; a model-added fact with no number or name, which these checks **cannot** catch (see honesty inventory); a passage that is already simple, where the summary can't be simpler (hence "at or below the passage's grade").
- **Test:** seeded summaries with a wrong number, a truncated end, an empty output, one in deliberately hard words, and one **fluent summary sentence with an invented non-numeric fact** (the support check must catch it).

### Layer 3: answer and witness selection (relevant ideas only)
- **Why it matters:** the brief asks for "**relevant** quiz questions". Answer-first only works if code picks answers that are key ideas of the passage, not stray words. This is now a headline design problem, not a detail.
- **Mechanism:** split into sentences. Score each candidate term with several independent relevance signals [DESIGN; weights `TODO(tune on dev set only)`]:
  1. **Repetition:** the term (or its stem) appears in two or more sentences.
  2. **Central sentence (v1.3):** the term sits in one of the 2-3 sentences code ranked most central for the summary. This is a sentence-centrality signal computed by code, not a model vote (in the whole-passage comparison arm it is a model vote).
  3. **Topic link:** the term shares a sentence with the passage's most frequent content word (the topic).
  4. **Type:** numbers, dates and mid-sentence capitalised terms score a bonus; they make clean, checkable answers.
  5. **Penalties:** stopwords, words of 3 letters or fewer, generic words from a small blocklist ("thing", "way", "people", "many"), and terms in the first 3 words of a sentence.
  Keep at most one candidate per sentence and pick the top 5-6. Require at least one signal from 1-3 for a candidate to count as relevant; candidates passing only on type are labelled AMBER ("detail question").
- **Example:** "Iron rusts when it reacts with oxygen and water." gives `oxygen` (in the summary, shares a sentence with the topic word `iron`) as the candidate, witness sentence 1. `1999` scores on type alone, so it can be used but is marked as a detail question.
- **Edge cases:** abbreviations break sentence splitting ("Dr."); very short sentences give no context; a passage with no numbers or names falls back to frequent words; in the whole-passage comparison arm signal 2 is a model vote; in the default path it is a code-ranked centrality signal, so it is always available and never circular with the model.
- **Reserve items (v1.2, for the Reread Loop):** for each released item's witness sentence, also keep the second-best term in that same sentence as a reserve. Reserves are never shown first; they are only for asking again after a miss (Layer 7).
- **Test:** hand-labelled splits on 5 passages; every candidate must be a whole-token span of its witness; on the dev set, a human marks each chosen answer "key idea / minor detail / trivial", and no candidate in the top 3 may be "trivial".
- **Reuse:** normaliser and span logic from `securagenai/edge-rag-trust-mechanisms` (MIT); idea only from YAKE (AGPL) and the cloze pipeline in `fighting41love/Question-Generation` (GPL).

### Layer 4: question stems
- **Mechanism:** one short model call per candidate, sent **only the witness sentence and its answer**, with one worked example in the prompt. The prompt shape comes from Toddle's builder and LENTERA's rules. No JSON is needed, since we ask for one line.
- **Example:** given the sentence and `oxygen`, the model might write "What does iron react with, along with water, to form rust?"
- **Why short prompts matter:** prefill cost drops, because each call carries about 60-100 tokens and not the whole passage [ESTIMATE].
- **Checks:** ends in "?"; 20 words or fewer; the answer is not in the stem; at least 60% of stem content words appear in the passage; not a near-duplicate of another stem (similarity below 0.92).
- **Wording for students:** the prompt asks for a question a Class 6 student would understand, using words from the passage. The same readability check as the summary runs as a WARN.
- **Edge cases:** the model echoes the sentence; the model asks about the wrong term. That is the main remaining risk. For the student, the witness sentence shown with every answer limits the damage: even a badly worded question sends them back to the right line. AMBER items are flagged for a teacher to look over when one is available.
- **Test:** hand-made bad stems for each check.

### Layer 5: wrong options
- **Mechanism:** pick three same-type terms from **other sentences**: numbers with numbers, names with names, frequent words with frequent words. Shuffle. Sort numeric options.
- **Example:** for `oxygen`, the candidates could be `rust`, `metal`, `bridge`. `water` is excluded because it sits in the witness sentence and could also be a defensible answer.
- **Edge cases:** too few same-type terms, in which case the item becomes a short-answer question with no options, and is labelled so.
- **Test:** no option equals the key; no duplicates; no option from the witness sentence.
- **Why not the model:** multiple-correct-answer detection is unreliable even with GPT-4 (F1 .00-.46, SAQUET) [SOURCE], so we avoid creating the problem.

### Layer 6: checks and tiers
The full list is `harvest/04-quiz-validators.md` (20 checks, Python standard library only, none run yet). Build checks 1-13 first. Answer-first removes some of them, such as single-key and answer-grounding, or turns them into assertions that must never fail.

### Layer 7: student quiz mode (the "study aid") [DESIGN]
- **Why it matters:** the brief asks for an "accessible, offline **study aid**" and a "credible demonstration of how this **supports learners**". A printout proves generation; an interaction proves support. This stays in the terminal, so it is not the "custom interface" the brief rules out.
- **Mechanism:** `sakshi study passage.txt` runs the pipeline (or loads a cached run for that passage), then:
  1. Asks each released question in turn. **(Build change: the summary is shown AFTER the questions, under "In short", as a review. It restates the central sentences that questions come from, so showing it first gives the answers away. `--summary-first` exists for comparison.)**
  2. Continues as below. The student types a letter (multiple choice) or a word (short answer).
  3. **Right:** "Correct. Here's where the passage says it:" plus the witness sentence.
  4. **Wrong:** "Not quite. Read this sentence again:" plus the witness sentence, then the correct answer. No score shaming, no timer.
  5. **Reread Loop (v1.2):** after the first round, for each missed item, Sakshi asks **one new question from the same witness sentence**: "You missed sentence 4. Read it once more, then try this one." The new question is the reserve item for that sentence (Layer 3), prepared in advance. If there is no reserve, or it failed checks, a code-built cloze of that sentence is used instead (labelled `FALLBACK`), blanking a different term from the one already revealed.
  6. End: "You got 3 of 4, and the retry right. Sentence 4 is worth one more read." The sentence numbers come from the witnesses.
- **Why the Reread Loop matters:** it is the blueprint's "system visibly adapts" beat (7.6) done honestly. Nothing is learned or stored; the system responds to *this* student's miss, deterministically, and the second question tests whether rereading worked.
- **What the student sees:** GREEN items only by default. AMBER items appear only with `--include-amber`, labelled "check this one with your teacher". RED items never appear in student mode.
- **Short-answer marking:** case-insensitive, punctuation-stripped exact match against the code-picked key, plus its stem (`oxygen` / `Oxygen.`). Anything else is "not quite" with the witness shown, so a near-miss still gets the right sentence. Never let the model mark answers.
- **Caching:** the student shouldn't wait 1-2 minutes per passage. A teacher or student can prepare the day's passages once (`sakshi prepare`), then `study` is instant. Live generation is still shown in the demo.
- **Edge cases:** empty input (repeat the question); the student types the full option text, not the letter (accept it); fewer than 3 GREEN items (fill with labelled `FALLBACK` cloze items so the deliverable's three questions are always met); the reserve item's answer was shown in the first round's feedback (never use it; fall back to cloze on another term); a sentence with only one usable term (no retry; just "reread sentence 4").
- **Test:** scripted answers (all right, all wrong, mixed, empty, full-text) against a fixture quiz; the closing line lists exactly the witnesses of the wrong items; every retry question's witness equals the missed item's witness; no retry's key equals a key already revealed.

### Layer 8: metrics and run card
- **Required by the brief (deliverable 4), printed at the end of every run as a four-line run card:**
  ```
  Model:        Llama-3.2-1B-Instruct SpinQuant INT4 (.pte, sha256 ab12…)
  Model size:   TODO(measure) MB on disk
  Peak memory:  TODO(measure) MB (llama_main)  |  TODO(measure) MB (this process)
  Time:         TODO(measure) s total  (summary s, stems s, load s)   network: OFF
  ```
  The brief says "approximate" and "where measurable", so this card is the whole requirement. Everything else in this layer is extra.
- Prefill and decode tokens/s and time to first token come from the runner's `Stats`. First token time = `first_token_ms` minus `inference_start_ms`.
- Peak memory comes from `ru_maxrss`.
- Save prompt, raw output, parsed output and verdict for each call, with `.pte` hash, version, temperature and thread count.
- **Importing torch inflates in-process memory**, so report the memory figure from `llama_main`, and state which runner produced each number.
- **Energy (v1.2, extra):** an inline USB-C power meter between a USB-PD power bank and the Pi gives watt-hours per prepared passage. From that: *passages prepared per power-bank charge* `TODO(measure)`. Rural schools have power cuts, so "runs a day off a power bank" is a physical, Arm-relevant claim, if the numbers support it. The meter reading is typed into `energy.json` by hand once per run; say so.
  - **Watch out:** the Pi 5 wants 5 V 5 A. Many power banks give 5 V 3 A, which the Pi accepts but with USB current limited, and it may report under-voltage. Check `vcgencmd get_throttled` during the run and report it. Test the exact power bank before the event.
- **What Arm's speed actually buys (v1.2, corrected framing):** the student's quiz is instant once prepared, so CPU speed does **not** decide how many students can study. It decides (a) how many passages a teacher can prepare in one period or on one charge, and (b) how long a one-question regeneration takes (Layer 9). Quote those two, with and without the KleidiAI build if both exist.

### Layer 9: one-question regeneration (`sakshi edit`) [DESIGN]
- **Why it matters:** it lets a judge plant the trap themselves (blueprint 7.5) and watch only the affected part change, in seconds rather than the 1-2 minutes of a full rerun.
- **Mechanism:**
  1. Split the old and new passage into sentences; find the changed sentences by exact comparison.
  2. For each released item whose witness sentence changed: re-pick the term in that sentence, preferring the same type (if the key was `1999` and the sentence now says `1887`, the new key is `1887`). Code updates the key immediately.
  3. Re-run the stem checks on the existing stem against the new key. Only if a check fails (for example the new key now appears in the stem) is the stem regenerated: one short model call.
  4. Rebuild wrong options for that item (the new key may clash with an old option).
  5. Re-run the summary's number check. If the summary still says `1999`, it is flagged on screen as `STALE: mentions 1999; passage now says 1887` and regenerated. **This is a second visible catch:** the number check, not a person, notices the summary is out of date.
  6. Items whose witness didn't change are left exactly as they were.
- **Example:** judge changes "In 1999, a town in our district repainted its old bridge" to "In 1887…". Within seconds the bridge question's key reads `1887`, its witness shows the new sentence, the summary is flagged STALE by the number check, and every other question stays put.
- **Time [ESTIMATE, not measured]:** one stem call is about 100 prompt tokens and 25 output tokens, so roughly 2-12 s on the decode range in the runtime table, plus summary regeneration if needed. `TODO(measure)`.
- **Edge cases:** the judge edits a sentence that held no item (nothing changes except the summary check; say so on screen); the judge deletes a sentence (its item goes RED with "witness removed"); the edit pushes the passage outside the word gate (warn, continue); the judge changes a word to one the model "knows" is wrong (that's the point).
- **Test:** fixture passage with one number changed, one name changed, one sentence deleted; untouched items byte-identical before and after.

### Layer 10: the Classroom Hotspot (spectator layer) [DESIGN]
- **Why it matters:** the blueprint's spectator layer and QR beat (7.5, 7.8). Judges become the students, on their own phones. It also answers "students don't own a Pi": one offline Pi serves a room of phones or shared tablets at once.
- **Not the deliverable:** the brief says terminal output is sufficient and a custom interface is not required. The terminal stays the deliverable; this is the show, and it is the **first** thing on the cut list.
- **Mechanism:**
  - The Pi runs a Wi-Fi access point with **no uplink** (NetworkManager hotspot). Ethernet unplugged.
  - `serve.py`: Python standard-library `http.server`, serving one static `web/index.html` (inline CSS and JS, **no CDN, no external fonts**) and the prepared quiz as JSON. Answers are checked in the browser against the code-picked key; nothing is sent back except an optional anonymous "missed sentence N" count.
  - **Model process isolated:** inference runs under `unshare -n` (no network interfaces at all) and writes the prepared quiz to disk. The web server only reads files. So "the model has no network" is literally true even while the hotspot is up.
  - **QR cards printed before the event:** one Wi-Fi join QR (SSID, password) and one URL QR (`http://10.42.0.1:8000`). No QR code is generated on the day.
  - Phone view: passage at the top, questions below. A wrong answer **highlights the witness sentence in the passage** and scrolls to it. Then the Reread Loop question appears.
  - **Room view (STRETCH):** the presenter's terminal shows an anonymous tally, "3 of 4 phones missed Q2 → sentence 4". For a teacher, that is which sentence the class didn't get. Counts only, held in memory, never written to disk.
- **Edge cases:** a phone's captive-portal check (Android or iOS shows "no internet"; tell judges to stay connected anyway, and test this on both platforms); a phone that drops to mobile data (the URL is a local IP, so it fails clearly; put "turn off mobile data" on the card); five or more phones at once (test with five).
- **Test:** three different phones (one iPhone, two Android) join, load the page with the Pi's uplink physically unplugged, answer, see the witness highlight; `ip route` on the Pi shows no default route.

### Runtime and model

| Decision | Choice | Why |
|---|---|---|
| Model | **Llama 3.2 1B** | Official Pi tutorial uses it; Arm publishes a build; likely but not confirmed approved |
| Build to try first | [SpinQuant 4-bit `.pte`](https://huggingface.co/executorch-community/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8-ET) | Ungated, includes tokenizer. **April 2025 export, may not load on 1.5** |
| Fallback models | Re-export; then Qwen2.5 1.5B, or SmolLM2 360M at 7.09 tokens/s, 299 MB | Qwen scored 27% correct with 30% empty in one different-task study on llama.cpp, so answer-first matters even more with it |
| Pipeline runner | Python `TextLLMRunner` | Avoids wrapping a command-line tool |
| Measurement runner | Source-built `llama_main` | Clean memory figures, thread sweep, KleidiAI comparison |
| OS | 64-bit Raspberry Pi OS Trixie | Bookworm fails on GLIBC with cross-built binaries |
| Build host | Linux x86_64, or try the aarch64 wheel on the Pi first | `setup.sh` exits on macOS, and you're on a Mac |
| Cooling | Active cooler | CPU drops from 2.4 to 1.5 GHz above 85°C |
| Process model (v1.3) | **One resident process holds the model.** `study`, `edit` and `serve` reach it over a **Unix domain socket at a filesystem path**, not localhost TCP | Model load of a ~1.8 GB file is paid once, `TODO(measure)`, and shown on the run card. A pathname socket works across network namespaces, so the model can run under `unshare -n` and still be reachable. Never run `llama_main` and the Python runner at the same time on a small-RAM Pi |

**Time budget per passage [ESTIMATE, not measured]:**
- **Output:** summary about 100 tokens, plus 6 stems at about 25 tokens each, makes about 250 tokens.
- **Prompt:** summary about 460 tokens, plus 6 stems at about 100 each, makes about 1,060 tokens. At about 90 tokens/s that is about 12 s.
- **Decode range:** at 2.67 tokens/s (Arm's one-token figure) about 94 s; at 16.6 tokens/s (a 7-token prompt in a GitHub issue) about 15 s.
- **Total: about 27-106 s** plus model load. Neither source reflects a real passage, so **the first test is to measure this.**

---

## 8. Uncertainty and safety

**The AI is never allowed to decide:** the answer key, the wrong options, which sentences go into the summary, or whether an item is released.

| Tier | Meaning | Student mode (`study`) | Full report (`report`, for teacher and judges) |
|---|---|---|---|
| **GREEN** | All HARD checks and all WARN checks pass | Asked, with the witness after every answer | Question, answer, witness sentence |
| **AMBER** | HARD checks pass, one or more WARN fired (including "detail question" and readability) | Hidden by default; with `--include-amber`, labelled "check this one with your teacher" | Same, plus the reason to look closer |
| **RED** | A HARD check failed after retries | Never shown | Withheld, with the reason shown. Never silently dropped. |

**The student is the user, so the rules are stricter than in v1.** In v1 a teacher reviewed every item before students saw it. A student studying alone has no reviewer, so student mode shows only GREEN items, and always shows the witness. If fewer than 3 GREEN items survive, labelled `FALLBACK` cloze items fill the gap: a cloze item's key is the blanked word, so it can't be wrong relative to the passage.

**GREEN does not mean correct.** It means it passed the checks, its key comes from the passage by construction, and it shows its witness. This has to be said on stage and in the output itself. Student mode's header reads: "Study aid. Each answer shows the sentence it comes from. If a question seems odd, trust the passage." The full report reads "draft: checked by rules, not by a person".

**Why the witness is shown:** for the student, it is the feedback that turns a quiz into study (quizzing with feedback g=0.537 vs 0.374 without, section 2). For a teacher, it makes checking a question a matter of seconds. One 2026 paper title suggests automation bias raises flaws in AI-assisted items (excerpt only), so don't let the tier replace the reading.

---

## 9. Degradation ladder

| Level | Trigger | What happens | Labelled |
|---|---|---|---|
| 1 | Normal | Model stem, code key, code options | Normal |
| 2 | Stem fails after 2 retries | Try the next candidate answer | Normal |
| 3 | Fewer than 3 GREEN items survive | Fill with cloze questions from code, so the brief's "at least three" is always met | `FALLBACK` |
| 4 | Summary fails after 2 retries | Extractive summary | `FALLBACK` |
| 4b | One-question regeneration too slow on the day | Judge's edit moves to Q&A; the counterfactual beat still runs from prepared output | Said aloud |
| 4c | Hotspot or phones fail | Judges play the student in the terminal (`sakshi study`), same beats | Said aloud |
| 5 | Model won't load | Show saved run, say so plainly | `SAVED RUN` |
| 6 | Pi fails | Backup recording, say so plainly | `RECORDING` |

**Stub backend:** a mock emitting the same output format lets the checks run without the model, from the Lodestar and SixthSense pattern. The checks can then be demonstrated on saved outputs even if generation fails.

---

## 10. Metrics and evaluation

### Headline metric (v1.2): the Counterfactual Passage Test, scored by script

**Set:** 16-20 counterfactual passages (section 3), each with exactly one **planted fact** recorded in `data/counterfactual/<id>.json`: sentence index, passage value (`90 °C`), memory value (`100 °C`), type. Split half dev, half held-out; the held-out owner writes and keeps the held-out half.

**Task, same for every arm:** produce a question with an answer key about the planted sentence, plus the passage summary.

**Fairness rules (red-team F1-F3, F13):**
- **Forced selection:** in eval mode Sakshi's Layer 3 is forced to use a term from the planted sentence. Otherwise Sakshi might not ask about it and the test measures selection, not fidelity. Say so.
- **Baseline arms, all with the passage in context:** (1) *targeted*: told which sentence to write about; (2) *free-form*: asked for a quiz, scored only on items touching the planted sentence, **with coverage reported**; (3) *grounded-prompt*: the targeted baseline plus "answer only from the passage and quote the supporting sentence". If arm 3 closes most of the gap, we report it: the honest conclusion would be that the prompt fix gets most of the way and our design adds a guarantee.
- **Filter protocol:** planted facts are kept only if the targeted baseline follows memory in at least 1 of 3 tries. The filter is applied to the **dev half only**; the held-out half is unfiltered. Report A for both halves, with n, and say on stage that dev facts were filtered.
- **Raters for D:** one fixed written rubric, two raters if possible, n and rater stated (a 2026 study found the choice of judge changes estimated conflict strength several-fold).

**Scored by `scripts/counterfactual_eval.py`, no human in the loop:**

| Number | What it shows | Expected |
|---|---|---|
| **A. Baseline key follows memory** | Share of planted facts where the baseline's key matches the memory value, not the passage value | The trap, measured. `TODO(measure)` |
| **B. Sakshi key follows passage** | Same, for Sakshi | 100% **by construction**. We say so: it is a guarantee of the design, not a skill of the model |
| **C. Summary mentions the memory value** | Share of summaries containing the memory value, before and after the number check | The non-circular test of *our* system: the summary is model-written. Numbers should be caught; names and months may not be, and we report that |
| **D. Stem still makes sense** | Share of Sakshi stems on planted sentences that a rater marks sensible (the model may write a stem that fights the planted fact, e.g. "Why does water boil at 100 °C…?") | The honest residual risk. Human rated, small n |

**Stage line:** "On N held-out passages built to make memory wrong, the baseline's key followed memory X times. Ours followed the passage every time, by design, and here's where our summary still slipped: Y."

**Honesty:** counterfactual passages are chosen to expose the trap, so A is **not** the baseline's error rate on ordinary passages. Ordinary-passage numbers are reported separately (below).

### Secondary metric: wrong-or-unsupported key rate on ordinary passages

**Wrong-or-unsupported answer key rate:** of the questions released, what share does a human rater mark as having a key that the passage does not support?

| Arm | Description |
|---|---|
| **Baseline** | LENTERA-style: the model writes questions, options and key in one call, no checks. A realistic baseline, adapted from a prize-winning project's schema. |
| **Ablation A** | Same baseline plus our checks |
| **Ablation B** | Answer-first with checks switched off |
| **Ours** | Answer-first with all checks |
| **Baseline-grounded (v1.3)** | The baseline call, but the prompt says "answer only from the passage and quote the supporting sentence". The honest-baseline test: a prompt-only fix. Reported even if it narrows our gap |
| **Ablation C (v1.3)** | Answer-first with a **code template stem** ("What is ___?" cloze) instead of the model's stem. Does the model earn its place? Rated for wording and relevance; reported even if the model adds little |

Ablation A vs Ours tells us whether answer-first earns its place. Ablation B vs Ours tells us whether the checks do. **We report whichever way this comes out.** If checks add little, that's our best negative result.

**Why this is the right headline for a student tool:** a wrong key is the failure a student alone can't detect. Lower is the claim.

### The brief's three quality words, each with a number

| Word in the brief | Metric | How measured |
|---|---|---|
| "**short**" summary | Summary word count, and ratio to passage length | Code, every run |
| "**understandable**" summary | Flesch-Kincaid grade of summary vs passage; share of summaries at or below passage grade | Code (`english-syllable`), every run. Readability formulas are rough for short texts, so report them as a guide, with one human "would a Class 6 student understand this? yes / mostly / no" rating per summary |
| "**relevant**" questions | Share of released questions whose answer a rater marks "key idea" vs "minor detail" vs "trivial" | Human rated on the rating sheet, with n. Compared against the baseline arm |

### Data split

- **Development:** 10 ordinary passages plus 8-10 counterfactual passages, ours or clearly licensed, for tuning.
- **Held-out:** 10 ordinary passages plus 8-10 counterfactual passages, kept by one named owner and never tuned on.
- **The organiser's passage** on the day is a natural held-out test.
- **Treat NCERT text as not reusable without permission.** This rests on a search summary, because NCERT's own pages failed to load, and dataset licences don't clear it. Prefer our own passages or `global-asp/pb-source` (CC BY per its README).

### Other numbers

| Metric | Target | Dev | Held-out | Notes |
|---|---|---|---|---|
| Counterfactual A-D (headline) | A high for baseline; C low after checks | `TODO(measure)` | `TODO(measure)` | Script-scored except D |
| Wrong-or-unsupported key rate | Lower than baseline | `TODO(measure)` | `TODO(measure)` | Human rated, with n |
| One-question regeneration time (Layer 9) | Under 15 s [DESIGN] | `TODO(measure)` | | The judge's edit beat depends on it |
| Passages prepared per power-bank charge | Report | `TODO(measure)` | | USB meter, hand-entered in `energy.json`; name the power bank |
| Passages prepared per 40-minute period | Report | `TODO(measure)` | | From measured time per passage |
| Hotspot: phones served at once | 5 tested | `TODO(measure)` | | iPhone and Android both |
| Seeded-fault catch rate | Every check fires on its bad item | `TODO(measure)` | n/a | Shows checks work at all |
| Release rate | `TODO(set after first run)` | `TODO(measure)` | `TODO(measure)` | Too low means too strict |
| Relevance: share "key idea" | Higher than baseline | `TODO(measure)` | `TODO(measure)` | Human rated, with n |
| Summary readability at or below passage grade | Most summaries [DESIGN] | `TODO(measure)` | `TODO(measure)` | Plus one human rating per summary |
| Usefulness rating: use as is, small edit, not at all | Reported as measured | `TODO(measure)` | `TODO(measure)` | Sheet in harvest 04; rater is a teacher, or us if no teacher is available, stated |
| Student try-out: did the witness help them find the answer? | Reported as measured | `TODO(measure)` | | STRETCH. Only with consent and a parent or school's permission; otherwise say "not tested with students" |
| **Time per passage** (p50, p95) — required | Under 3 min [DESIGN] | `TODO(measure)` | `TODO(measure)` | On the run card. Prepared in advance for students |
| **Model and model size** — required | Report | `TODO(measure)` | | On the run card |
| Tokens/s, first-token time | Report only | `TODO(measure)` | | With threads and temp |
| **Peak memory** — required | Fits the Pi supplied | `TODO(measure)` | | From `llama_main`, on the run card |
| Max temp, throttled? | Not throttled | `TODO(measure)` | | `vcgencmd get_throttled` |

**A pass rate on its own proves nothing.** A review calculated that an always-negative detector would score 93.09% where one published tool scored 94.13% [SOURCE: arXiv 2610.04267]. So always report the pass rate with the seeded-fault test and human ratings.

**Rules:** numbers come from `metrics.json`, never typed by hand. Always state the denominator and the conditions. Commit raw logs. Quote one git tag everywhere.

### Arm proof (extra, not required by the brief)

The brief only asks for approximate time, model and size or memory. These are for Arm's interest and the "measurable results" wording, and they sit on the cut list.

1. **Thread sweep:** 1, 2, 3 and 4 threads on the same model and prompt.
2. **4-bit vs 8-bit**, if both builds load.
3. **KleidiAI comparison:** the same `.pte` with a normal build and with `EXECUTORCH_XNNPACK_ENABLE_KLEIDI=OFF`, comparing prefill and decode. This needs a source build. It's the one measured optimisation we'd headline, if it shows a real difference. If it doesn't, say so.
4. Confirm `asimddp` in `/proc/cpuinfo`, and quote the build's `armv8.2-a+dotprod` flags. The Pi 5 has no I8MM per one cpuinfo dump, so expect dotprod kernels.
5. **Translate every speed number into a classroom number (v1.2):** passages prepared per period, passages per charge, seconds per one-question regeneration. Quote each with and without the KleidiAI build if both exist. A tokens/s figure means nothing to a teacher; "the whole week's passages prepared in one period" does.

---

## 11. Demo design (3 minutes, timed against measured generation)

| Time | Beat | What's on screen |
|---|---|---|
| 0:00-0:15 | **Hook:** one student, one evening, one passage. "A Class 7 student in a Karnataka government school rereads today's science passage. She can read every word. She can't tell if she understood it, and about 63% of these schools have no internet to ask anything." (Illustrative student; say so, or replace with a real quote.) | Pi, no slides |
| 0:15-0:25 | **Proof toggle:** unplug Ethernet on camera. `prove_offline.sh`: no default route, failed ping, and the model process running under `unshare -n` with no network interfaces. The hotspot stays up, with no uplink. Saved with the results. | Terminal |
| 0:25-1:00 | **Evade, then catch (the trap, live):** a counterfactual passage ("at the hill station, the water boiled at 90 °C"). Baseline and Sakshi run side by side on it. Baseline key: `100 °C`, from memory. Sakshi key: `90 °C`, with the witness sentence. "If this student trusts the first one, she now 'knows' something the passage never said." Prepared output is fine here if live generation is slow; label it. | Split terminal |
| 1:00-1:45 | **Judges become the students:** QR cards are up from 0:00 and judges join during the hook and the proof toggle (joining takes 30-60 s, so it cannot happen inside this beat); two pre-joined phones take the organiser's-passage quiz here, the rest optional. A wrong answer highlights the witness sentence in the passage; the Reread Loop asks again from that sentence. (Room view, if built: "3 of 4 phones missed Q2 → sentence 4.") | Judges' phones; presenter terminal |
| 1:45-2:15 | **A judge plants the trap:** the sentences that have a question are highlighted and numbered on screen; a judge edits one fact in one of them (a year, a number). `sakshi edit` regenerates only the affected question; its key follows the edit; the summary is flagged `STALE` by the number check and refreshed; everything else stays put. | Live terminal |
| 2:15-2:30 | **Impact explanation (deliverable 5):** one question from the organiser's passage, its witness, and what it fixes for this student (template below). Run card on screen: time, model, size, memory. | Terminal |
| 2:30-2:50 | **Proof card:** Counterfactual Test A and C on held-out passages with n; "key idea" share vs baseline; passages per period and per charge; regeneration seconds. Caveat first: "these passages are built to expose the trap." | From `metrics.json` |
| 2:50-3:00 | **Close:** "No witness, no question. A study aid that answers from the passage, not from memory. We haven't tested learning gains; that's the pilot." | |

**Impact explanation for the mandatory deliverable, on the day (template):**

> **Barrier:** a student studying alone, with no internet, can't check whether they understood a passage.
> **Example from the supplied passage:** Sakshi asked "`<question>`". A student who answered "`<plausible wrong answer>`" was shown: "`<witness sentence>`" — the one line that holds the answer.
> **How this reduces the barrier:** instead of finding out at the test, or never, the student learns *where* their understanding broke, right away, with no teacher and no connection. Because code took the answer from that sentence, the correction can't be invented.

Pick the question during the event from the organiser's passage, preferring a GREEN, "key idea" item whose wrong answer is a realistic misunderstanding.

**Blueprint beats, all present (7.1-7.8):** human hook ✓ · one villain (the memory answer) ✓ · live proof toggle (unplug, `unshare -n`) ✓ · evade then catch ✓ · judge takes part twice (phones, the edit) ✓ · system visibly adapts (Reread Loop, honestly deterministic) ✓ · spectator layer (Classroom Hotspot) ✓ · close on one proof card ✓.

**Variance plan:**
- The phone quiz runs on a prepared quiz, so it is instant. The hotspot is the highest-variance beat: rehearse with five phones, both platforms, mobile data off. If it fails, the judge plays the student in the terminal (ladder 4c).
- The judge's edit depends on measured regeneration time. If it is over about 15 s on the day, the edit moves to Q&A (ladder 4b).
- The side-by-side counterfactual can use prepared output, labelled as such.
- Keep a saved run and a backup recording; say plainly if either is used.

**60-second table walkaround:** counterfactual side by side (20 s) → judge takes the quiz on their phone (30 s) → run card (10 s).

**Offline proof:** Ethernet unplugged; no default route; DNS and ping fail; the resident model process runs under `sudo unshare -n` (or `unshare -rn` if user namespaces are enabled; tested in ticket 8i) and answers over a Unix socket; the Wi-Fi radio is an access point with no uplink, secured with a WPA2 password printed on the QR card, on a 5 GHz non-DFS channel. Evidence (`ip route`, `ip addr`, failed ping, `unshare` process listing) saved to `results/<tag>/` [DESIGN, untested]. The v1 plan of turning Wi-Fi off conflicts with the hotspot, so the proof is now "no route out", which is the stronger claim anyway.

---

## 12. Sponsors

Roles come from the page. What each one wants is **inference**.

| Sponsor | Role | Likely wants | What we show |
|---|---|---|---|
| **Arm** | Program lead | Skills in on-device AI and hardware-software optimisation | Speed turned into classroom numbers (passages per period, per charge, seconds per regeneration); thread sweep and KleidiAI comparison behind them; one Arm board as a whole room's offline server; dotprod explanation |
| **IIIT Bangalore** | Mentor institute, gives cash award | Method and real learning value | Your education expertise, the quizzing-with-feedback evidence, rubric, held-out set, honest limits |
| **NASSCOM / AI CoE (CATS)** | Collaborator and supporter; logo reads "nasscom AI Center of Excellence", a MeitY initiative with the Govt. of Karnataka | PoCs that could be deployed | One shared Pi per school ("affordable"), costed once real prices are checked; students use it in turns during study or library periods; a teacher loads passages |
| **UK Government (TSI)** | Supporter; TSI factsheet talks of skills and "safe, responsible, human-centric and trustworthy AI" | Skills and trustworthy AI | Fence around the model, visible refusal, a student never sees an unchecked item, no student data stored or leaving the device |
| **K-Tech / Karnataka** | Supporter | Karnataka as an AI talent hub | Karnataka data, named learner group, Kannada as an honest next step |

**Load-bearing test: the hard truth.** "If we remove the sponsor's tech, does our product still work?" Technically llama.cpp could run this, so we can't claim otherwise. Our honest answer:
- ExecuTorch and a Pi are the brief.
- We'll measure what Arm's optimisations contribute with the KleidiAI comparison, and state it in classroom terms (v1.2): how many passages a teacher can prepare in a period, how long a judge waits for a regenerated question.
- The whole system is one low-power Arm board: model, checks and a room's hotspot, on a power bank. That is the "affordable" in the brief.
- Fixed-size, ahead-of-time exported models fit a deployment with no download step.

**Vocabulary from Arm's sister challenge:** moving from building AI apps to engineering AI products across optimisation, benchmarking and validation. This matches our pitch, and it's worth using in the proposal.

---

## 13. Rubric mapping (against the page's wording)

| Criterion | What answers it |
|---|---|
| Expected outcome: "working offline PoC that converts a short passage into a summary and three quiz questions" | One command on the Pi, network off; the deliverable is met even on the fallback path (`FALLBACK` cloze fills to three) |
| Expected outcome: "credible demonstration of how this supports learners facing the identified access barrier" | Judges take the quiz on their own phones from an offline Pi; witness highlight and Reread Loop; impact explanation from the organiser's passage |
| Practical implementation | Working run on a Pi, one command, repo with setup that has been re-verified |
| Measurable results | Run card on every run (required); Counterfactual Passage Test scored by script on held-out passages; results table, ablations; classroom numbers (per period, per charge, regeneration seconds); thread sweep and KleidiAI as extras |
| Societal relevance | One named barrier and learner group, Karnataka data, quizzing-with-feedback evidence, a student or teacher conversation, honest limits |
| "Short, understandable, relevant" | Word count, readability vs passage, "key idea" share (section 10) |
| Offline operation | `prove_offline.sh`, saved evidence |
| Edge optimisation (page objective) | Same as Arm proof above |

---

## 14. Challenge and answer table

| Challenge | Our one-sentence answer |
|---|---|
| "Isn't this just LENTERA or a quiz generator?" | "They generate and return; our model never writes the key, and each item shows the sentence that proves it." |
| "Isn't your 100% on the counterfactual test circular?" | "Yes, for the key it's a guarantee of the design, and we say so; the real tests of our system are the summary, which the model writes, and whether the stem still makes sense, and here are those numbers." |
| "Did you rig the counterfactual passages?" | "They're built to expose the trap, so we never quote the baseline's rate on them as its everyday rate; ordinary passages are reported separately." |
| "Isn't the phone page the custom interface the brief says isn't needed?" | "The terminal is the deliverable and meets every requirement; the phone page is how one offline Pi serves a whole room, and it's the first thing we'd cut." |
| "Isn't the hotspot a network? How is this offline?" | "There's no route out: no uplink, no default route, and the model process runs with no network interface at all; the Wi-Fi only connects phones in the room to the Pi." |
| "Is the Reread Loop real learning?" | "It's not machine learning and we don't call it that; it's a deterministic second question from the sentence the student missed." |
| "Why is there an LLM at all? Isn't this fill-in-the-blank?" | "The model writes readable wording and simplifies sentences; code owns every fact. Ablation C shows what the model adds over a template, and if it adds little we report that." |
| "Your baseline is a strawman." | "We also ran a baseline told to answer only from the passage and quote its source; here are all three baseline arms and what each scored." |
| "The student reads the summary first. Is that protected?" | "Yes: code picks the sentences, the model only simplifies each one, and every summary sentence has a source sentence it must stay close to, or it falls back to the original sentence." |
| "Is the counterfactual test a new idea?" | "No: knowledge-conflict tests exist in the literature; we apply one to a classroom tool and say so." |
| "Is that number real? On what data?" | "Held-out passages we didn't tune on, n stated; the raw logs are in the repo at this tag." |
| "What happens when it's wrong?" | "The worst case is an oddly worded question; the answer still comes from the passage, and the student is shown the exact sentence, so they're sent back to the text, not misled." |
| "Who is the user, the student or the teacher?" | "The student studying alone; the teacher only loads passages and can look over anything flagged AMBER." |
| "Students don't own a Raspberry Pi." | "They don't need to: one Pi per school prepares the passages and serves the quiz over its own Wi-Fi to whatever shared phones or tablets the school has, with no internet; or students take turns at its terminal." |
| "Don't most students have a phone with internet at home?" | "Many homes do, and we don't claim otherwise; our barrier is the school, where they study with no connection and no one free to check their understanding." |
| "Why not let a student just ask a chatbot?" | "No internet, and a chatbot that's fluently wrong is the trap; a study aid must not invent the answer, so ours can't." |
| "Is a summary plus three questions really 'support'?" | "With feedback it is: quizzing with feedback beats quizzing without in the meta-analysis we cite, and the witness sentence is that feedback; whether it improves results here is for a pilot." |
| "Isn't answer-first just fill-in-the-blank?" | "It's close to that for recall, and we say so; we trade depth for a key that can't be invented, and inference questions are the next step, once measured." |
| "Why not check the model's answers instead?" | "On our own planted-fact test a plain span check does catch memory answers, because the planted value isn't in the passage; what it can't do is stop a wrong answer that IS in the passage (published results: 96% of unanswerable questions' answers still matched a span), and it can't show the student where the answer comes from. Answer-first removes the need and gives the witness." |
| "Why not a bigger model?" | "Larger builds were slower on Arm's Pi 5 figures, and a school's Pi must fit the model; our accuracy comes from design." |
| "Why ExecuTorch rather than llama.cpp?" | "It's the brief, it gives us ahead-of-time export, and here's what Arm's kernels measurably added on this Pi." |
| "Who did you test with?" | State exactly who, or "no students; here's what we'd test in a pilot." |
| "What's simulated?" | Honesty inventory, from memory. |
| "Doesn't this exclude Kannada-medium students?" | "Yes, version 1 does, and we state it; Kannada needs its own tokeniser testing because our cleanup could break it." |
| "How is this used in a school?" | "A teacher loads the day's passages once; students take turns on the shared Pi in a study or library period, or the quiz is printed with its witness sentences." Say as a proposal, not a finding. |
| "What failed?" | Our best negative result, from the engineering log. |
| "Is this your code?" | "Here's the provenance section: what we reused, under which licence, and what's new." |

---

## 15. Considered and rejected

| Option | Why not |
|---|---|
| Model writes full quiz, then check it | Span checks are weak both ways; that's the trap |
| Entailment model (NLI) as verifier | AUROC 0.50-0.64 and 0.8-4.4 s per check on a Pi 5, at a cost of 3-7 points of correct answers |
| Constrained or grammar output | `grammar` fields exist with no consumer found in the runner |
| Self-answer check | Extra inference, weak signal (35.3% sensitivity for a related signal); stretch only |
| T5 question generators (Questgen, Leaf) | Heavy dependencies and extra models |
| Larger models (3B to 8B) | Slower on Arm's figures; Phi-3 20 s prefill; SmolLM3 1.12 tokens/s |
| Arm prebuilt `.pte` files first | Separate prefill and decode files, or no tokenizer, in those checked; may not run on `llama_main` |
| Chatbot, Kannada, custom UI, mobile app, document management | Explicitly "not required" in the brief; would cost points elsewhere |
| Teacher as the main user (v1 framing) | The brief names students and learners; a teacher tool reads as off-brief. The teacher stays in a supporting role |
| Model marks the student's answer | It could mark a right answer wrong; marking is exact-match against the code-picked key, and a near-miss still gets the witness |
| Student scores, accounts or progress tracking | That is the "complete education platform" the brief rules out, and storing student data raises consent questions |
| Showing AMBER items to students by default | No reviewer is present when a student studies alone |
| Spectator 3D dashboard | A 3D view adds nothing to a text task. v1.2 takes the blueprint's spectator rule in a form that fits: judges' own phones as students over the Pi's hotspot |
| Generating the QR code on the day | Extra dependency and a live failure point; the SSID and IP are fixed, so the QR cards are printed in advance |
| Web frameworks, CDNs or web fonts for the phone page | They need the internet or add install risk; one static page with inline CSS and JS on `http.server` |
| Storing students' answers for a teacher dashboard | Student data, consent, and "complete education platform" territory; the room view is anonymous counts in memory only |
| "Students served per period" as the Arm number | Wrong: the quiz is instant once prepared, so CPU speed doesn't limit students. Arm's speed limits preparation and regeneration, and that is what we quote |
| Calling the Reread Loop "learning" | It's deterministic; overclaiming it would cost more than it earns |

---

## 16. What this is NOT

- Not a tutor, a chatbot or "a complete education platform" (the brief's words). It is offline educational content support: one passage in, a summary and a self-check quiz out.
- Not a teacher's tool first. The student is the user; the teacher supports.
- Not an auto-grader or a test. No scores are stored and nothing is reported to anyone. The room view, if built, is anonymous counts in memory.
- Not online. The hotspot connects phones in the room to the Pi; nothing connects the Pi to the internet.
- Not adaptive learning. The Reread Loop is one fixed rule: miss a sentence, get another question from it.
- Not a replacement for the teacher. Anything AMBER is for a teacher to look over.
- Not proven to improve learning.
- Not for Kannada-medium classes in version 1.
- Not suited to inference or higher-order questions in version 1.
- Not fast to generate. Passages are prepared in advance (1-2 minutes each, estimated); the student's quiz is then instant.
- Not free of errors: GREEN means checked, not correct.

---

## 17. Reuse plan: what we take from where

**Rules:** read each licence in full before copying, since agents mostly read opening lines. Keep notices in `THIRD_PARTY_NOTICES.md`. List what predates the event in a "Built on" section. Arm's rules allowed open source if the entry builds on it, while Bharat required original work, and **Namma's rule is unknown.** So treat this table as a plan until the organisers answer.

| Item | Source | Licence | Use |
|---|---|---|---|
| Runner, tokenizer, stats | `pytorch/executorch` release/1.5 at `985c1cec` | BSD-3 | Depend on it, unmodified |
| `examples/models/llama/` | Same | **Folder has Llama 2 licence; file headers say BSD** | Build unmodified, never copy into our repo |
| Llama 3.2 1B weights (the community SpinQuant `.pte`) | Meta, via Hugging Face `executorch-community` | **Llama 3.2 Community License**, not MIT or BSD. Likely needs a "Built with Llama" notice and has an acceptable-use policy **[UNVERIFIED: read Meta's page, ticket 8h]** | Name it in the README, `THIRD_PARTY_NOTICES.md` and a slide; link the file, don't redistribute it in our repo |
| Benchmark reporting | `courses-code-executorch/course_support/benchmarking.py` at `1045d516` | Clear BSD | Reuse for CSV, JSON and plots, then add token metrics |
| Prompt template, stop markers | Toddle AI `PromptBuilder.kt` | MIT | Port; verify against Meta's page, which we have not read |
| Model file hashing | Toddle AI `hash_artifacts.sh` | MIT | Port, removing failure-masking |
| Summary and grade rules | LENTERA at `136f026`, files in Layer 3 | MIT | Adapt, shorten for 1B |
| JSON cleanup, if used | LENTERA `extract_keyword.ts` L34-38; AptusTutor `JsonExtractionUtils.kt` | MIT; Apache-2.0 with NOTICE | Likely unneeded for one-line stems; needed for the baseline |
| Normaliser, span and empty-output rules | `securagenai/edge-rag-trust-mechanisms` at `54c07b3` | MIT | Reuse small parts; extend beyond ASCII |
| Syllable counter | `english-syllable` | MIT-style | For readability warning |
| Quiz audit, quote-in-source check | `syuan03/skill-anything` | MIT | Compare with our checks; closest existing validator found |
| Small-model JSON repair | `SamoyeHN/lexis-wiki` `_heal_json` | MIT | Baseline arm only. **Don't copy its failure fallback, which invents answers** |
| Correct answer first, then shuffle | `timothyckl/quizard-generator` | MIT | Compare with our option step |
| Bloom's verbs and stems | `microsoft/Shiksha-Copilot` | MIT | Stem wording ideas, from a tool used in Karnataka |
| Kannada and English passages | `global-asp/pb-source` | CC BY per README | Possible test passages, if you accept CC BY |
| Fallback logic | StudyBuddy, Lexis, PDF-summary-quiz-generator | Various | **Never copy: they invent answers on failure, which would inflate our pass rate** |
| Passage wrapper, context budget | UNIVERSAL-OFFLINE-AI `app.py` | MIT | Reference; possible rival, so check overlap before reuse |
| Demo script, failure runbook, risk register | Lodestar, SixthSense | MIT, but documents are structure only | Follow the format and write our own |
| Measured table, gate logs, video script | Sound Sense | No root licence | Ideas only |
| Check design | Lecture-to-Quiz, Generate-Then-Validate, SAQUET | Ideas only | Write checks ourselves |
| Validate, merge, fallback design | ALAB | No licence | Ideas only |

**Ours to write:** answer selection, stem prompts, option picker, checks, metrics glue, thread sweep, offline proof.

---

## 18. Team roles (fill in)

| Role | Owns | Person |
|---|---|---|
| Systems and demo | Pi, build, runner, thread sweep, demo operation | `TODO` |
| Pipeline and checks | Selection, prompts, checks, tests | `TODO` |
| Education and held-out owner | Barrier, passages, student/teacher conversation, rating sheet (relevance, understandability), impact explanation, **holds held-out set** | You, probably |

With fewer than 3 people, one person can hold two roles. **The held-out owner must not tune prompts.**

---

## 19. Timeline and build map

### Before the proposal

| When | Do |
|---|---|
| **Today, 4 Nov** | Email organisers; confirm eligibility and any college nomination; request Llama access as a backup |
| **5 Nov** | Find a Pi 5, active cooler and Linux machine |
| **6 Nov** | Proposal deadline (you are writing it). Only the Team Leader registers. |

### Before the event (7-13 Nov)

Whether this builds real code or only rehearses depends on organisers' answer 3. **If pre-written code is banned, run these on a throwaway project and carry in only the spec.** Finalists are told by 11 Nov, so do the cheap proving work before then, only as far as you're willing to spend time before selection.

| # | Ticket | Priority | Test / done when |
|---|---|---|---|
| 1 | Flash Trixie, active cooler, check `asimddp`, `vcgencmd` | CORE | Commands return as expected |
| 2 | `pip install executorch==1.5.1` on the Pi; import `_llm_runner` | CORE | Import works. If not, go to 3 first. |
| 3 | Source build of `llama_main` on Linux or the Pi | CORE | `--help` runs with no GLIBC error |
| 4 | Load SpinQuant `.pte`, one generation | CORE | Output plus `PyTorchObserver` line. If it fails, re-export. |
| 5 | **Real passage test: first true speed number** | CORE | 300-word prompt, tokens/s and peak memory recorded |
| 6 | Prompt format check: token count shows headers parsed as special tokens | CORE | Count matches expectation |
| 7 | One stem by hand: does 1B write usable questions from a sentence and term? | **CORE: go or no-go for the design** | 20 hand-judged stems. Decide on stem quality before more work. |
| 7b | Summary by hand, **both arms (v1.3)**: code-picked sentences simplified one by one vs one whole-passage call. Is each simpler than the passage and faithful to it? | **CORE: "understandable" is a deliverable** | 10 summaries; readability grade vs passage recorded; hand rating "would a Class 6 student understand this?" |
| 7c | Relevance scoring on paper: do the five signals pick key ideas? | CORE | On 5 dev passages, top 3 picks contain no "trivial" answer |
| 8 | Write 20 passages at Class 6-8 level, split 10/10, held-out owner stores theirs | CORE | Licences clear |
| 8b | Talk to one student or teacher about how students revise a passage alone, and whether a witness sentence would help | SUPPORTING | One real quote for the hook, or the proxy caveat |
| 8c | **Write 16-20 counterfactual passages** with planted-fact records (sentence, passage value, memory value, type); held-out owner writes and keeps their half. This is data, not code, so it's allowed whatever the organisers say about pre-written code | **CORE: headline metric** | **Run the targeted baseline exactly as it will run in the test, with the passage in context** (v1.3: v1.2 tested the bare question, which proves nothing about the passage-present case). A fact counts as a trap only if the baseline follows memory in at least 1 of 3 tries. Apply this filter to the dev half only. **Go/no-go:** if fewer than about a third of facts trap the model, replace the live evade-then-catch beat with a prepared ordinary-passage villain and say so |
| 8d | Hotspot rehearsal on a throwaway: Pi as access point with no uplink; 5 phones (iPhone and Android) load a static page | SUPPORTING | Captive-portal behaviour known on both platforms; mobile-data warning on the card |
| 8e | Buy and test a USB-PD power bank and an inline USB-C power meter with the Pi 5 | SUPPORTING | `vcgencmd get_throttled` clean, or the under-voltage limit noted |
| 8f | Print QR cards (Wi-Fi join with WPA2 password, URL) and a laminated "turn off mobile data" line | SUPPORTING | Scanned by a phone that has never seen the network |
| 8g | **Verify and price (v1.3):** read the primary source for the school-internet figure; write a bill of materials (Pi 5, cooler, power bank, card) with a source for each price; ask whether schools have shared phones or tablets | **SUPPORTING; needed for the proposal** | Every figure in the proposal has a link; "affordable" is a number, or is dropped |
| 8h | Read Xie et al. 2023 and Meta's Llama 3.2 licence page | SUPPORTING | Quotes and the notice wording checked, not recalled |
| 8i | **Resident model behind a Unix socket under `unshare -n`** (throwaway) | **CORE: protects the offline claim** | A client outside the namespace gets a reply; `sudo unshare -n` works, or the fallback is noted |
| 9 | Thread sweep and KleidiAI comparison | SUPPORTING (extra, not required) | Numbers with conditions |
| 10 | Rehearse everything on a stopwatch; freeze | CORE | Two full runs |

### Plan P and Plan E (red-team F8): decided by organiser answer 3

| | **Plan P: pre-written code allowed** | **Plan E: everything written on the day** |
|---|---|---|
| Before 14 Nov | Build and test Layers 1-9 on the Pi; counterfactual set; scorer; QR cards | Data and specs only: counterfactual passages, rating rubric, prompts as text, QR cards, rehearsal on a throwaway project |
| 14 Nov | Integrate, run on the organiser's passage, rehearse | Spine first (hour 3), then in order: quiz mode → counterfactual test → regeneration |
| Cut at the start | Nothing | **Classroom Hotspot, energy, ablations A-C, checks 14-20, KleidiAI**; keep the thread sweep only if the `llama_main` build already works |
| Trap beat | Live, side by side | Prepared output, labelled |

**Decide the plan the moment the organisers answer.** If they haven't answered by 11 Nov, assume Plan E.

**Decision (4 Nov, from the team): Plan P.** Writing code before the event is allowed. Build and test Layers 1-9 before 14 Nov; event day is integration, the organiser's passage and rehearsal.

### Event day (8 hours, adjust once schedule is known)

| Hour | Do | Tickets |
|---|---|---|
| 0-1 | Setup, re-read rules, dry run, thermal check, **confirm network-off works** | Ticket 11: gate; `prove_offline.sh` |
| 1-3 | **Spine: one end-to-end run on the real Pi, in terminal, ending with the run card.** This alone meets deliverables 2-4 | 12: summary. 13: selection, reserves and options. 14: stems. 15: output and run card |
| 3-4.5 | Checks 1-13 plus readability and relevance, tiers, retries, fallback, **student quiz mode with Reread Loop**, saved run | 16, 17: `quiz.py`, 18: metrics |
| 4.5-5.5 | **Counterfactual Passage Test**: baseline arm, `counterfactual_eval.py`, held-out run. **One-question regeneration** (`regen.py`) | 19, 20, 21 |
| 5.5-6.5 | **Classroom Hotspot** (`serve.py`, `web/index.html`); organiser's passage; energy reading; results table; ablations if time | 22, 23 |
| 6.5-7 | **Freeze.** README, impact explanation from the organiser's passage (deliverable 5), requirement map, git tag, backup recording | 24 |
| 7-8 | Stopwatch rehearsals with five phones; fix only what rehearsal breaks | |

**If behind at hour 4.5:** skip ablations and the room view; keep the counterfactual test and regeneration. **If behind at hour 5.5:** skip the hotspot; the terminal quiz covers every beat (ladder 4c).

**Watch out for generated code in these tickets:** sentence splitting on abbreviations; substring vs whole-token matching (`art` in `party`); case and punctuation in the number check; `\w` breaking on non-English text; unstripped stop markers counted as output; the model echoing the prompt; retries that silently reuse the same seed at temperature 0, which will return the **same** output; memory measured in the Python process vs `llama_main`; syllable counting that crashes on numbers or hyphenated words; quiz mode that marks "Oxygen." wrong against `oxygen`; quiz mode that reveals the answer before the student types; the counterfactual scorer matching `100` inside `1000` (whole-token match, units normalised: `90 °C`, `90°C`, `90 degrees`); `regen.py` re-picking every item instead of only changed sentences; a web page that pulls a font or script from a CDN and hangs offline; `http.server` bound to `127.0.0.1` so phones can't reach it; the answer key embedded in the page in a way that's visible before answering (acceptable for a study aid, but don't print it in the DOM).

### Cut list

Cut without hesitation, in this order: room view → checks 14-20 → 8-bit comparison → ablation B → Classroom Hotspot (terminal quiz covers it) → energy measurement → `--include-amber` option → human rating beyond one rater → KleidiAI comparison. **Keep:** the thread sweep (a cheap loop around one run, and the only Arm-specific measured finding if the KleidiAI build fails), ablation A, ablation C and the grounded-prompt baseline (the honest-baseline tests).

**Never cut** (each one is a mandatory deliverable or the core claim): offline proof; the run card (time, model, size, memory); the summary readability check ("understandable"); relevance scoring ("relevant"); at least three questions, with cloze fallback; student quiz mode with the witness as feedback and the Reread Loop ("study aid", "supports learners"); the three tiers; **the Counterfactual Passage Test (the trap, live and measured)**; **one-question regeneration (the judge's edit)**; the impact explanation from the organiser's passage; the results table with denominators; backup recording.

### Repo layout

Follows `harvest/06-hackathon-entries.md`: `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `docs/` (proposal, architecture, technical report, requirement map, STATUS, DEMO, failure runbook, risk register, engineering log), `prompts/`, `src/` (`gate.py`, `select.py`, `generate.py`, `distract.py`, `checks.py`, `readability.py`, `quiz.py`, `regen.py`, `serve.py`, `metrics.py`, `backends/`), `web/index.html`, `tests/fixtures/`, `data/passages/`, `data/counterfactual/`, `benchmarks/results/<tag>/`, `scripts/` (`setup.sh`, `selfcheck.sh`, `prove_offline.sh`, `hotspot.sh`, `counterfactual_eval.py`, `demo.sh`), `print/` (QR cards).

---

## 20. Status table

| Item | State |
|---|---|
| Barrier, learner group, trap, shift | **Reframed student-first in v1.1** to match the brief; pending your review |
| Answer-first design | **Design only. Ticket 7 can kill it.** |
| Relevance scoring, readability check | Design only (tickets 7b, 7c) |
| Student quiz mode, Reread Loop | Design only |
| Counterfactual passages | Not written (ticket 8c); planted facts not yet checked against a 1B model |
| One-question regeneration | Design only; time not measured |
| Classroom Hotspot | Design only; captive-portal behaviour untested (ticket 8d) |
| Energy per passage | Not measured; power bank not chosen (ticket 8e) |
| Model speed on real passage | Not measured |
| Quality of 1B stems | Not measured |
| SpinQuant `.pte` on 1.5 | Not tested |
| Wheel includes `_llm_runner` | Not tested |
| Offline proof method | Not tested; resident model behind a Unix socket under `unshare -n` untested (8i) |
| Witnessed summary and support check | Design only (7b compares it with the whole-passage arm) |
| Trap fires with the passage present | **Unknown, ticket 8c, go/no-go for the live beat** |
| Red team and mock judge | **Run once on v1.2 (4 Nov), 23 flaws logged, `RED_TEAM_LOG.md`.** Self-review only |
| LENTERA key bug | Read from code, not run |
| Reuse allowed | **Unknown, ask organisers** |
| Approved model list, Pi supply, judging | **Unknown, ask organisers** |
| Student or teacher conversation | Not done |

### Honesty inventory

| Component | What it really is | Judge-facing risk | What we say |
|---|---|---|---|
| Summary (v1.3) | Code-picked sentences, each simplified by the model one at a time, support-checked against its source sentence, number- and readability-checked | The model can still change meaning within a sentence in a way word-overlap doesn't catch; readability formulas are rough | "Numbers and reading level are checked. Other claims aren't, which is why the questions point back to the passage, not the summary." |
| Stem | Model-written, checked by rules | Can ask about the wrong thing | "This is the main remaining risk, and the witness shown to the student limits it." |
| Key, options | Code-chosen, relevance-scored | Options can be odd, or the key a minor detail | "Recall-level by design; relevance is rated by a human, here's the share." |
| Answer marking in quiz mode | Exact match by code | A correct synonym is marked "not quite" | "The student still sees the sentence, so a near-miss is harmless." |
| Student use | **Not tested with students** unless ticket 8b happens | Overclaim that students like it | Say who we spoke to, or that we didn't. |
| Counterfactual passages | Curated by us to expose the trap | Looks rigged | "Built to expose the trap; never quoted as the baseline's everyday rate." |
| Sakshi's 100% key fidelity | A design guarantee | Sounds like a model result | "By construction. The model-written summary is the real test, and here's its number." |
| Reread Loop | Deterministic rule | Sounds like adaptive AI | "One fixed rule, no learning." |
| Room view | Anonymous counts, in memory | Sounds like tracking students | "Counts only, never stored." |
| Energy figure | USB meter read by hand | Looks precise | "Hand-read from a meter, one power bank, stated conditions." |
| Tiers | Rule output | Sounds like confidence, isn't probability | "Green means passed checks, not correct." |
| Baseline villain | Saved run | Looks staged | "This is a saved run, chosen because it fails." |
| Learning impact | **Not tested** | Biggest overclaim risk | Say it before they ask. |
| Reused parts | Others' code | Looks like copying | Point at provenance section. |

---

## 21. Open risks (red team comes later)

1. **Ticket 7 might fail:** a 1B model may write poor stems. If so, move toward cloze with a model-written summary, and the pitch changes.
2. **Code-picked terms may be trivial,** such as a stray frequent word. The brief says "relevant", so this is now a deliverable risk. Relevance scoring (Layer 3) and the human "key idea" rating address it; ticket 7c tests it early.
3. **"One Pi per school"** needs a real cost figure and workflow. Single-teacher schools average about 26 students, which weakens per-school hardware. v1.2's hotspot changes the access question: the quiz is instant and served to many devices at once, so the limit is how many shared phones or tablets a school has, which we don't know. `TODO(find a source on device access in Karnataka government schools, or state it as unknown)`.
4. **Weak readers may not read English summaries,** so the fit with the learner group needs your judgement. The readability check helps but doesn't solve it.
5. **The hook needs a real student's or teacher's words** in place of our illustrative scene.
6. **Sponsor tech is not truly load-bearing,** as section 12 states. v1.2 makes Arm's contribution concrete in classroom numbers, but llama.cpp could still run this.
7. **The LENTERA key bug is unverified,** so confirm it by running it, or drop that fact.
8. **Home internet weakens the barrier** if a judge pushes it (83.3% of rural households). Our answer is the school setting; keep that line sharp and don't drift into "students have no internet".
9. **Students as users raises consent questions** for any try-out. No student data is stored; any student conversation needs a teacher's or parent's permission.
10. **The 1B model may not fall for the planted facts** (v1.2). If the baseline rarely answers from memory on our passages, the evade-then-catch beat is weak. Ticket 8c checks every planted fact against the model before the event; keep only facts that trap it, and report that we filtered them.
11. **Venue Wi-Fi interference** may make the hotspot flaky in a crowded room (v1.2). Rehearsed fallback: terminal quiz (ladder 4c).
12. **Scope creep** (v1.2): four new parts on a 6-8 hour day. The cut list and the hour-4.5 and hour-5.5 checkpoints in section 19 are the guard. The spine and every mandatory deliverable come first. v1.3 adds Plan P / Plan E.
13. **The trap may not fire with the passage present** (v1.3, F1). Ticket 8c is go/no-go for the live beat, and we say how many facts were kept.
14. **Support check limits** (v1.3): word overlap doesn't catch a rewrite that flips meaning ("does" to "does not", swapped subject and object). Add a negation-word check (HARD if the source and rewrite differ on "not", "no", "never"); disclose the residual risk.
15. **Resident process and RAM** (v1.3): one process holding the model plus the Python runner may exceed a small Pi's RAM; organisers' answer 9 and ticket 5 decide.
16. **Everything here is unrun** (v1.3): the red team reasons from documents. The first real Pi run (tickets 1-7) can overturn any of it.
17. **No outside judge yet:** a self-review has blind spots. Get one human mock judge (a teacher, and someone who has shipped on a Pi) before 14 Nov.

Red-team rounds and the mock judge have not been run.

---

## 22. Key numbers by heart

- 18,007 of 48,527 government schools online; about 63% not.
- 29% of Karnataka Class 6 students proficient or above in language (33% nationally).
- Quizzing effect g=0.499; with feedback 0.537 vs 0.374 without.
- 96% span match on unanswerable; 36-56% on correct small-model answers.
- Llama 3.2 1B: about 1.76 GB file and 2.08 GB peak (Arm's INT8 build), 2.67 tokens/s (one-token runs); SpinQuant on a phone uses about 1.9 GB RSS vs 3.2 GB for BF16.
- Our own numbers: `TODO(measure)`. **Don't quote any of ours until they exist.** v1.2 adds: counterfactual A and C, regeneration seconds, passages per period, passages per charge.

---

## 23. One-paragraph pitch

A Class 7 student in a Karnataka government school can read a passage without understanding it, and when she studies alone there's no timely way to check. About 63% of these schools have no internet, so online help is out of reach. A small AI model on a shared Raspberry Pi could help, but small models are fluent and confidently wrong, and a student studying alone is the person least able to spot a polished wrong answer. So in Sakshi, the model never writes the answer key. Code picks the answer and the sentence that proves it from the passage; the model only writes a short, simple summary and the wording of each question. When the student answers, right or wrong, Sakshi shows the one sentence to reread, and if they missed it, asks again from that sentence. We prove it on passages built to make the model's memory wrong: an ordinary generator answers from memory, Sakshi answers from the passage. One Arm board runs the model, the checks and the whole room's quiz over its own Wi-Fi, with no route to the internet, off a power bank. No witness, no question. We publish exactly what it costs and how often it fails.

---

## 24. Glossary

- **ExecuTorch:** PyTorch's runtime for on-device models. `.pte` is its model file.
- **XNNPACK:** CPU kernels used by ExecuTorch.
- **KleidiAI:** Arm's optimised kernels, used through XNNPACK.
- **SpinQuant / INT4:** ways of compressing a model to 4-bit weights.
- **Prefill / decode:** reading the prompt / generating new tokens.
- **Ablation:** switching a part off to measure what it contributes.
- **Held-out:** data never used for tuning.
- **Witness:** the passage sentence that proves an answer.
- **Cloze:** a fill-in-the-blank question.
- **Run card:** the four lines printed after every run (model, size, peak memory, time) that meet deliverable 4.
- **Student mode / `study`:** the terminal quiz a student answers, with the witness as feedback.
- **Flesch-Kincaid grade:** a rough reading-level formula from sentence and word length.
- **Counterfactual passage:** a passage with one planted fact that differs from what a model "remembers", used to expose answering from memory.
- **Planted fact:** the one changed fact in a counterfactual passage, recorded with its passage value and memory value.
- **Reread Loop:** after a miss, one new question from the same witness sentence.
- **Reserve item:** a second candidate from a released item's witness sentence, kept for the Reread Loop.
- **Classroom Hotspot:** the Pi's own Wi-Fi with no uplink, serving the quiz to phones in the room.
- **`unshare -n`:** runs a process with no network interfaces at all.

---

## 25. Changelog

- **v1 (4 Nov 2026):** first version from six harvests and five research agents; GitHub sweep folded in. Not red-teamed yet. Answer-first design replaces the earlier check-after-generation plan.
- **v1.1 (4 Nov 2026):** aligned with the official Problem 1 statement, now quoted verbatim in section 1. Changes made:
  1. **Off-brief user.** v1 targeted the teacher; the brief names students and learners. The person is now a Class 6-8 student studying alone, the teacher is a supporting role, and the barrier is written in one line using the brief's own example (sections 0, 2, 3, 23).
  2. **No study aid.** v1 produced a printout for a teacher. New Layer 7 adds a terminal student quiz mode where the witness sentence is the feedback ("study aid", "supports learners").
  3. **Student safety.** With no reviewer present, student mode shows GREEN only and fills to three questions with cloze items; marking is by code, never the model (section 8).
  4. **"Understandable" was on the cut list.** The readability check is now part of the summary layer and on the never-cut list (Layer 2, cut list).
  5. **"Relevant" had no mechanism.** Layer 3 now scores relevance with five signals, and the summary runs first so it can act as one of them. A human "key idea" rating was added to the metrics (sections 6, 7, 10).
  6. **Measurement was over-scoped.** The brief asks for approximate time, model and size or memory. Layer 8 prints these as a run card, and the thread sweep and KleidiAI comparison are marked as extras (sections 7, 10, cut list).
  7. **The demo didn't show learner support.** The judge now plays the student, and the impact explanation has a template using the organiser's passage (section 11).
  8. **Q&A gaps.** New answers cover who the user is, students not owning a Pi, home internet, chatbots, and whether the output counts as "support" (section 14).
  9. **Other updates:** new rejected options (section 15), a rewritten "What this is NOT" (section 16), tickets 7b, 7c and 8b, new honesty rows, and new risks 8-9.
- **v1.2 (4 Nov 2026):** checked against the blueprint's "impressive" machinery. v1.1 scored about 80 of 120 on its scorecard ("rework"): rigorous but quiet. Changes, each tied to a blueprint rule:
  1. **Trap shown only as a saved run (4.3, 7.4).** New counterfactual passages make the trap visible; it is beaten live, side by side with the baseline (sections 3, 11).
  2. **Headline metric needed slow human rating (6.1, 6.8).** The Counterfactual Passage Test is scored by script (A-D), with the key's 100% stated as a design guarantee and the summary as the real test (section 10).
  3. **Judge's edit was pushed to Q&A (7.5).** New Layer 9 regenerates only the affected question, so the edit fits the demo; the summary's number check visibly flags the stale summary.
  4. **No spectator layer (7.8).** New Layer 10: the Classroom Hotspot. Judges take the quiz on their own phones from the offline Pi; the model process runs under `unshare -n`. The terminal stays the deliverable, and the hotspot is cut first.
  5. **"Visibly learns" left out (7.6).** New Reread Loop: a deterministic second question from the missed sentence, with reserve items picked in Layer 3. Not called learning.
  6. **Sponsor tech weak (4.7) and no physical angle (5.9).** Speed is now quoted as classroom numbers (passages per period, per charge, regeneration seconds), plus energy from a USB meter on a power bank. Corrected a framing error from the chat: CPU speed doesn't limit students served, because the quiz is instant once prepared.
  7. **Offline proof conflicted with the hotspot.** It is now "no route out" plus `unshare -n` (section 11).
  8. **No named parts (7.14).** Added the Witness Gate, Counterfactual Passage Test, Reread Loop and Classroom Hotspot (section 0).
  9. **Supporting updates:** scorecard (section 1b), pipeline rows 9-10, degradation steps 4b and 4c, metrics rows, sponsors, rubric mapping, five Q&A answers, rejected options, "What this is NOT", tickets 8c-8f, a re-timed event day with cut checkpoints, a new cut list and never-cut list, repo layout, status, honesty rows, risks 10-12, pitch and glossary.
  - **Not done yet:** red-team rounds and the mock judge (blueprint P4, P5). *(Done in v1.3.)*
- **v1.3 (4 Nov 2026):** red-teamed (three rounds, 23 flaws, full log in `RED_TEAM_LOG.md`) and mock-judged (69/100 on the nearest public rubric, projected 77; scorecard re-scored to about 88, projected 94). Most important changes:
  1. **Summary hole closed (F11, CRITICAL).** Witnessed summary: code picks sentences, the model only simplifies each, a support check ties each to its source. The whole-passage summary is now a comparison arm (Layer 2).
  2. **Trap may not fire (F1, CRITICAL).** Ticket 8c now tests the baseline with the passage present and is go/no-go for the live beat; a fallback villain is named (sections 3, 19).
  3. **Isolation versus resident process (F4, CRITICAL).** Resident model behind a Unix socket under `unshare -n`; ticket 8i tests it (runtime table, offline proof).
  4. **Metric fairness (F2, F3, F13).** Forced selection in eval mode, three baseline arms including a grounded-prompt baseline, filter on dev only, held-out unfiltered, rater rubric (section 10).
  5. **Does the model earn its place? (F12).** Ablation C: template stem versus model stem.
  6. **Scope (F8).** Plan P and Plan E (section 19).
  7. **Demo (F10, F14).** Judges join Wi-Fi from 0:00; two pre-joined phones in the beat; item-bearing sentences highlighted for the judge's edit.
  8. **Sponsor and deployment (F15, F17).** Thread sweep kept; ticket 8g for a sourced school figure and a priced bill of materials.
  9. **Licence and logistics (F19, F20).** Llama licence row; organiser questions 7-9.
  10. **Prior work found (F23).** Counterfactual test cited to knowledge-conflict literature (snippets only; ticket 8h to read).
  11. **Still open:** unrun everywhere; no outside judge; proposal not yet drafted.

**Source files:** `harvest/01-lentera.md`, `02-executorch-apps.md`, `03-executorch-arm-base.md`, `04-quiz-validators.md`, `05-github-sweep.md`, `06-hackathon-entries.md`. Pins and line ranges are there.
