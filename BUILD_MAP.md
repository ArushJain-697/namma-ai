# SAKSHI: Build Map v1

*4 Nov 2026. Built from Master Bible v1.3, `RED_TEAM_LOG.md` and `CHECKLIST.md`. Ticket format is blueprint 12.4. **This file is the memory of the build: update the Status column after every ticket, before starting the next.***

**Dates:** proposal **6 Nov** · finalists told by 11 Nov · live event **14 Nov** · winners 19 Nov.

## How to read this

- **Golden rule (blueprint 8.2):** don't start a ticket until its blockers pass their own tests. "Mostly works" poisons everything downstream.
- **Window** says where a ticket can happen:
  - **HERE**: in the cloud container. Writing code, tests with a stub model, docs. The container can reach PyPI, **not** Hugging Face or GitHub, and has **no Pi**.
  - **PI**: needs your real Raspberry Pi. I write the script here; you run it there and send back the output.
  - **HUMAN**: a person must do it (email, teacher conversation, rating, printing).
- **Priority:** CORE (spine, mandatory deliverable, or headline claim) · SUPPORTING · STRETCH.
- **Status:** `DONE` (built and tested) · `V0` (built, tested only on easy cases, quality unmeasured) · `NEXT` · `TODO` · `BLOCKED(x)`.
- **Untested means untested.** Anything touching the real model is `TODO` until it has run on the Pi. Nothing in this map has.

## Standing assumptions (change them here if they change)

1. **Plan P: writing code before the event is allowed (confirmed by the team on 4 Nov; get the organisers' answer in writing if you can, and check whether reused open-source code is covered too).** So everything in Layers 1-9 is built and tested BEFORE 14 Nov, and event day is integration, the organiser's passage, and rehearsal. Keep the git history honest.
2. **Core is Python standard library only.** The only third-party code is the `executorch` wheel on the Pi. `pytest` is for development only.
3. **A stub backend stands in for the model** so every check, the pipeline and the quiz can be tested without a Pi.
4. **No number goes in any pitch unless a script produced it** (`metrics.json`).

## Progress at a glance

| Track | Tickets | Done |
|---|---|---|
| **Overall** | 36 tickets + 6 human | **19 done, 14 tool-ready (waiting on the Pi or on you), 3 not started** (4 Nov, 190 tests) |
| A. Core pipeline (HERE) | T01-T14 | **All done (M0 reached): 123 tests pass.** T05 selection quality is unmeasured |
| B. Pi bring-up (PI) | T15-T20 | T15-T18 written and waiting for the Pi; T20 done and tested here; **T19 not started** |
| C. Go/no-go gates | T21-T24 | All four tools ready; each needs the Pi and/or your ratings or passages |
| D. Evaluation | T25-T28 | T25, T26, T28 done; T27 tools ready |
| E. Demo layers | T29-T33 | T29 done; T30, T33 ready for Pi testing; **T31, T32 not started (need the Pi)** |
| F. Docs and handoff | T34-T36 | T34, T36 done; T35 drafted (needs your blanks) |
| H. Humans (parallel) | H1-H6 | none |

**M0 is reached and everything that can be built without the Pi is built.** What remains needs the Pi or you: T15 → T17 → T18 → T21-T24 (run on the Pi, then rate), T19, T31, T32, and the human tickets H1-H6. See `HANDOFF.md`.

---

## Track H: things only people can do (start now, in parallel; some are due before code matters)

| # | Ticket | Priority | Due | Done when |
|---|---|---|---|---|
| H1 | **Email the organisers** the 9 questions in bible section 1 (approved models, Pi supply and RAM, **pre-written code**, proposal contents, judging, laptop and model files, demo format, power and hotspot, passage delivery). support@nammaAIchallenge.com | CORE | **today** | Sent; answers logged in `CHECKLIST.md` |
| H2 | **Write and submit the proposal** (T35 drafts it) | CORE | **6 Nov** | Submitted by the Team Leader only |
| H3 | **One teacher or student conversation**: how do students check their own understanding of a passage when no one is free? Would a witness sentence help? | CORE for the pitch | before 6 Nov if possible | One real quote, or the proxy caveat written down |
| H4 | **Get a Pi 5** (ask organisers about RAM first; 8 GB preferred), an **active cooler**, a good SD card or NVMe, a USB-C PD power bank and an inline USB-C power meter | CORE | 5 Nov | Pi boots Trixie 64-bit |
| H5 | **One outside mock judge** (a teacher, and someone who has shipped on a Pi) reads the bible and the proposal | SUPPORTING | before 11 Nov | Their questions added to the challenge table |
| H6 | **Write the counterfactual passages by hand** (T24 gives the format) and rate stems, summaries and relevance (T21-T23 give the sheets) | CORE | 8-12 Nov | Files committed; held-out half kept by its owner |

---

## Track A: core pipeline (HERE; testable with the stub)

### T01: Repo skeleton and tooling
Priority: CORE · Window: HERE · Blocked by: none · **Status: DONE**
Spec: `src/sakshi/` package, `tests/`, `scripts/`, `data/passages/`, `results/`. Standard library only.
Done when: `python -m pytest` runs from the repo root.

### T02: `text.py`: sentences, tokens, stemming, whole-token matching
Priority: CORE · Window: HERE · Blocked by: T01 · **Status: DONE** (43-test suite with T03-T07; whole-token, abbreviation, decimal and quote cases)
Spec: `split_sentences` protects abbreviations, initials and decimals. `find_span` / `contains_term` match **whole tokens**, case-insensitive, multi-token terms. `blank_term` blanks every occurrence. `normalize_answer` lowercases, drops punctuation and articles.
Watch out: `art` inside `party`; `100` inside `1000`; "Dr." and "e.g." splitting; decimals ("3.5"); `\w` on non-English text; quotes after a full stop.
Test: 20+ assertions: split cases (Dr., e.g., 3.5, quotes, ?/!), `find_span("a party","art") is None`, `find_span("in 1000","100") is None`, `normalize_answer("The Oxygen.") == "oxygen"`, `"1,000" -> "1000"`.
Done when: all pass.

### T03: `gate.py`: passage gate (Layer 1)
Priority: CORE · Window: HERE · Blocked by: T02 · **Status: DONE** (all boundaries 134/135/149/150/300/301/330/331 tested)
Spec: 150-300 words OK; 135-149 and 301-330 WARN; outside that REJECTED with a stated reason; empty REJECTED; `override` for testing.
Test: 134, 135, 149, 150, 300, 301, 330, 331 words; empty; non-ASCII punctuation.
Done when: boundaries exact.

### T04: `readability.py`: syllables, Flesch-Kincaid grade
Priority: CORE ("understandable" is a deliverable) · Window: HERE · Blocked by: T02 · **Status: DONE** (syllables and ordering tested; never crashes on digits or hyphens)
Watch out: crash on digits and hyphenated words; silent-e; empty text returns 0.0. A guide only, never a verdict.
Test: syllables for known words (water 2, oxygen 3, rust 1, galvanising 4, 1999 no crash); a hard sentence grades higher than an easy one.
Done when: ordering and no-crash tests pass.

### T05: `lexicon.py` + `select.py`: answer and witness selection (Layer 3)
Priority: CORE ("relevant" is a deliverable) · Window: HERE · Blocked by: T02 · **Status: V0** (invariants tested; **selection quality still unmeasured**, see T23)
Spec: topic word, sentence centrality (top 3), per-sentence best term from signals repeat / central / topic / type, plain-word penalty, one candidate per sentence, top 6, unique stems, **reserve** term per candidate, `relevant` and `detail` flags.
**Known weakness (found on the first passage):** `rusts` beat `oxygen` in "Iron rusts when it reacts with oxygen and water." because repetition outweighs it. Selection quality is **unmeasured**. Do not tune on one passage. T23 measures it on dev passages with human ratings; only then change weights.
Watch out: the term must be a whole-token span of its witness; `reserve` must differ in stem from the key; plain words must never be `relevant`.
Test: every candidate is a whole-token span of its witness; reserve stem != key stem; no stopword or blocklist term; a passage with no numbers or names still returns candidates; a passage of very short sentences returns few or none rather than crashing.
Done when: invariants pass on 5 passages. (Quality is T23, not this ticket.)

### T06: `distract.py`: wrong options (Layer 5)
Priority: CORE · Window: HERE · Blocked by: T05 · **Status: DONE** (invariants tested: no key duplicate, none from witness, deterministic, no case giveaway)
Spec: same-kind terms from **other** sentences; exclude the key's stem and any stem in the witness sentence; numbers same-length first and sorted; names keep case, words are lowercased (no capital-letter giveaway); `None` if fewer than 3 (short-answer item).
Test: no option equals the key; no duplicates; no option stem from the witness sentence; deterministic for a given seed; all options lowercase when the key is a word.
Done when: invariants pass.

### T07: Backend interface and stub with fault modes
Priority: CORE · Window: HERE · Blocked by: T01 · **Status: DONE** (stub with 10 fault modes and fail_first for retry tests; Llama 3 template)
Spec: `backends/base.py`: `GenResult(text, prompt_tokens, new_tokens, ttft_ms, tokens_per_s, wall_s)`, `Backend.generate(prompt, max_new_tokens, temperature=0.0, seed=None, task=None, payload=None)`, `Backend.info()` (name, model path, size, load seconds). `llama3_chat(system, user, bos=False)` builds the Llama 3 instruct template. `backends/stub.py`: deterministic rules for `task="simplify"` and `task="stem"`, with modes `faithful`, `bad_number`, `invent` (fluent invented fact), `negate`, `hard_words`, `empty`, `leak` (answer in the stem), `echo`.
Watch out: the real backend must ignore `task` and `payload`; retries at temperature 0 with the same seed return the **same** text, so retries must change temperature or seed; BOS handling is unverified (T17 checks token counts).
Test: each fault mode produces its fault; same inputs give same output.
Done when: tests pass.

### T08: `checks.py`: checks and tiers
Priority: CORE · Window: HERE · Blocked by: T02, T04, T07 · **Status: DONE** (24 tests including one seeded fault per check; all fire on their own fault)
Spec: `CheckResult(name, severity HARD|WARN, passed, detail)`.
- **Summary sentence (per rewrite vs its source):** support (>=70% of rewrite content stems in the source, HARD); numbers all in source (HARD); **negation parity** (source and rewrite agree on not/no/never/n't, HARD); new capitalised names WARN; readability WARN (avg sentence <=15 words and grade <= max(source grade, 7)). Whole summary 30-80 words HARD.
- **Stem:** empty HARD; ends with "?" HARD; <=20 words HARD; **answer not in stem** (whole-token) HARD; >=60% content stems in passage WARN; near-duplicate of another stem (difflib ratio >= 0.92) HARD; readability WARN.
- **Item assertions (must never fail):** key is a whole-token span of the witness; no option equals the key; no duplicate options; no option stem in the witness sentence.
- `tier(results, detail)`: any HARD fail -> RED; any WARN fail or `detail` -> AMBER; else GREEN.
Watch out: substring vs whole-token; case and punctuation in the number check ("1,999" vs "1999", "90 °C"); negation inside contractions.
Test: **seeded-fault test**: one bad item per check, and each check must fire on its own bad item and not on a good one. This is the bible's "seeded-fault catch rate".
Done when: every check fires on its seeded fault and stays quiet on the good item.

### T09: `generate.py`: witnessed summary, stems, retries, cloze fallback
Priority: CORE · Window: HERE · Blocked by: T05, T07, T08 · **Status: DONE** (witnessed summary and stems; every fault mode ends in fallback or RED; retries vary temperature)
Spec:
- **Summary (default):** code picks the 2-3 central sentences; one short call each ("Rewrite this sentence in simple words for a Class 6 student. Keep every number and name. Add nothing."); each rewrite checked against its own source; fail after 2 retries -> source sentence verbatim, labelled `FALLBACK`. **Comparison arm:** one whole-passage call.
- **Stem:** one short call per candidate, sent **only** the witness sentence and the answer, one worked example, one line out. Up to 3 attempts at temperatures 0.0 / 0.4 / 0.7 and seeds 0 / 1 / 2. Take the first attempt with no HARD and no WARN failure, else the best with no HARD failure, else RED with reasons.
- **Cloze:** `build_cloze(sentence, term)` blanks the term, code only.
Watch out: the model echoing the prompt or the sentence; unstripped stop markers; a stem that fights the planted fact; the same seed at temperature 0 repeating itself; the answer leaking into the stem.
Test: with the stub, each fault mode ends in the right outcome (retry succeeds, falls back, or goes RED); no model output ever becomes a key.
Done when: pass.

### T10: `pipeline.py`: prepare a run
Priority: CORE · Window: HERE · Blocked by: T03, T06, T09 · **Status: DONE** (prepare, JSON round-trip, cloze fill to 3, RED kept with reasons, forced sentence for eval, keys proven independent of the model)
Spec: `prepare(passage, backend, n_items=6, min_visible=3)` -> `Run` (gate result, summary, items, timings, fallbacks, raw outputs, backend info). Item = `{id, kind mcq|short|cloze, stem, key, options, witness_idx, witness, reserve (code cloze), tier, checks, fallback, detail}`. Fill with labelled cloze items until at least 3 are student-visible. JSON save and load. Eval mode can **force** a term from a given sentence (needed by T26).
Watch out: never drop an item silently (RED keeps its reason); reserve key must never equal a key already revealed; options must be absent (short-answer) when fewer than 3 distractors exist.
Test: end-to-end on the sample passage with the stub; >=3 visible items; every visible item has a witness; JSON round-trip is lossless.
Done when: pass.

### T11: `quiz.py`: student mode and the Reread Loop (Layer 7)
Priority: CORE · Window: HERE · Blocked by: T10 · **Status: DONE** (scripted-student tests; **design change:** summary now comes AFTER the questions, see findings)
Spec: **questions first, summary after (changed during the build: the summary restates the central sentences that the questions come from, so showing it first gives the answers away; `--summary-first` exists for comparison).** GREEN and FALLBACK-cloze items only (`--include-amber` adds AMBER, labelled). Ask each item; accept a letter, the full option text, or a typed word; mark by exact normalised match **in code only**. Right: show the witness. Wrong: "Not quite. Read this sentence again:" + witness + the answer. After round one, one new question per miss from the same witness (the reserve cloze), never reusing a revealed key. Closing line lists the witness numbers. Input and output are injected so tests can script a student.
Watch out: "Oxygen." vs `oxygen`; empty input repeats the question; the answer must not appear before the student types.
Test: scripted students (all right, all wrong, mixed, empty, full-text option): the closing line lists exactly the witnesses of the misses; every retry's witness equals the missed item's witness; no retry key was already revealed.
Done when: pass.

### T12: `metrics.py`: run card
Priority: CORE (deliverable 4) · Window: HERE · Blocked by: T10 · **Status: DONE** (run card, metrics.json, network and throttle detection tested against fake files)
Spec: four-line card: model name and hash, model size on disk, peak memory (`resource.getrusage` ru_maxrss in KB on Linux; state which process), time (total, summary, stems, load), network status (no default route in `/proc/net/route`), plus `vcgencmd get_throttled` when present. Writes `metrics.json`; all pitch numbers come from it.
Watch out: ru_maxrss is KB on Linux and bytes on macOS; importing torch inflates in-process memory, so the card names which runner produced the number.
Test: card renders with stub data; network detection works against a fake `/proc/net/route`.
Done when: pass.

### T13: `cli.py`: `python -m sakshi`
Priority: CORE · Window: HERE · Blocked by: T10, T11, T12 · **Status: DONE** (check, prepare, study, report; tested through subprocess; executorch backend gives a clear message until T16)
Spec: `check PASSAGE`, `prepare PASSAGE --backend stub|executorch --model --tokenizer --out run.json`, `study run.json [--include-amber]`, `report run.json` (tiers, witnesses, reasons, run card; labelled "checked by rules, not by a person").
Test: subprocess run of `check`, `prepare` and `report` with the stub; `study` fed from stdin.
Done when: the three-command demo works end to end with the stub.

### T14: Test suite, fixtures, `selfcheck.sh`, `pyproject.toml`
Priority: CORE · Window: HERE · Blocked by: T02-T13 · **Status: DONE** (123 tests; `bash scripts/selfcheck.sh` green; pyproject with the `sakshi` script)
Spec: one test file per module; fixtures in `tests/fixtures/`; `scripts/selfcheck.sh` runs everything and prints a pass count; `pyproject.toml` with the `sakshi` console script.
Done when: `bash scripts/selfcheck.sh` is green from a clean checkout.

---

## Track B: Pi bring-up (you run these; I write them here)

### T15: `scripts/pi_setup.sh`
Priority: CORE · Window: HERE writes, **PI runs** · Blocked by: H4 · **Status: WRITTEN, UNTESTED ON A PI** (`scripts/pi_setup.sh`: machine checks, slim install with full fallback, import check, selfcheck)
Spec: checks 64-bit Trixie (`uname -m`, `/etc/os-release`), `asimddp` in `/proc/cpuinfo`, `vcgencmd measure_temp` and `get_throttled`, RAM; creates a venv; `pip install executorch==1.5.1`; imports `executorch.extension.llm.runner` and prints which names exist; prints the result as a block you paste back.
Watch out: the wheel might not contain `_llm_runner`, or might need a newer Python than the Pi has; Bookworm fails on GLIBC with cross-built binaries; importing the runner loads torch (RAM and start-up time).
Done when: **you paste the output back** and `_llm_runner` imports, or we switch to T19.

### T16: `backends/executorch_backend.py` (Python `TextLLMRunner`)
Priority: CORE · Window: HERE writes (against the installed wheel's real API), **PI tests** · Blocked by: T07 · **Status: WRITTEN, TESTED WITH A FAKE RUNNER ONLY** (real API; reset before each prompt; no seed; stop tokens stripped; **has never loaded a real model**)
Spec: load once; `generate` with echo off, bounded `max_new_tokens`, low temperature; per-token callback gives time to first token; stats callback gives prefill and decode rates; record load seconds, model file size and sha256.
Watch out: BOS may be added by `num_bos` **and** by the prompt (double BOS); strip stop markers; the April 2025 SpinQuant `.pte` may not load on 1.5.1; there is no thread argument in the Python runner; `get_vocab_size` returns -1.
Done when: T17 passes on the Pi.

### T17: `scripts/pi_smoke.py`: load, one generation, token-count check
Priority: CORE · Window: HERE writes, **PI runs** · Blocked by: T15, T16, and the model + tokenizer files on the Pi · **Status: WRITTEN, UNTESTED ON A PI** (`scripts/pi_smoke.py`; settles BOS and special-token questions from real token counts; verdict logic tested)
Spec: load the `.pte`, run one fixed prompt, print the text, tokens/s, time to first token, load time, peak RSS; tokenise the chat template and confirm header tokens parse as **special tokens** and BOS appears exactly once.
Done when: coherent output plus the stats line, or a re-export is scheduled.
**How you get the model (not possible from here):** on any machine with internet, download the SpinQuant `.pte` and tokenizer from `executorch-community/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8-ET`, copy them to the Pi. Read Meta's licence page first (bible ticket 8h).

### T18: `scripts/pi_bench.py`: first true speed number on a real passage
Priority: CORE · Window: HERE writes, **PI runs** · Blocked by: T17, T10 · **Status: TOOL READY** (`scripts/pi_bench.py`, tested with the stub; **needs the Pi to produce any real number**)
Spec: run `prepare` on the sample passage three times; report p50 and p95 time, tokens/s, peak memory, `get_throttled`. First true replacement for every `[ESTIMATE]` in the bible's time budget.
Done when: numbers pasted back; bible time budget updated from them.

### T19: Source-built `llama_main` (measurement runner)
Priority: SUPPORTING · Window: PI · Blocked by: T17 · **Status: TODO**
Spec: build script and instructions; needed for clean memory numbers, the thread sweep and the KleidiAI A/B. **Never run it at the same time as the Python runner** (RAM).
Done when: `--help` runs with no GLIBC error and one generation matches T17.

### T20: Resident model + Unix socket + `prove_offline.sh` (bible ticket 8i)
Priority: CORE (protects the offline claim) · Window: HERE writes, **PI runs** · Blocked by: T16 · **Status: DONE HERE; Pi run pending** (resident process, Unix socket, `prove_isolation.sh` with a control; tested in a REAL network namespace here: isolated process sees only `lo`, control sees `eth0`)
Spec: `src/sakshi/resident.py`: one process holds the model and answers JSON requests on a **Unix socket path**; `prove_offline.sh` saves `ip route`, `ip addr`, a failed ping and the process listing to `results/<tag>/`; run the resident process under `sudo unshare -n` and show a client outside the namespace still gets a reply.
Watch out: localhost TCP does **not** cross a network namespace; `unshare -n` needs root or user namespaces; the hotspot must stay up (no Wi-Fi-off in the proof).
Done when: a reply crosses the namespace and the evidence files exist.

---

## Track C: go/no-go gates (each one can change the pitch)

### T21: Stem quality test (bible ticket 7): **go/no-go for answer-first**
Priority: CORE · Window: HERE writes the tool, **PI generates, HUMAN rates** · Blocked by: T18 · **Status: TOOL READY** (`scripts/rate.py stems`; **needs the Pi to generate, then your ratings**; thresholds are proposed)
Spec: `scripts/rate_stems.py` makes 20 (sentence, answer) cases from the sample passages, generates stems with the real model, writes a rating sheet (usable / awkward / wrong-term / leaks answer), computes the share usable.
Decision: if too few are usable, move toward cloze with a model-simplified summary and **change the pitch**.
Done when: sheet rated; decision written in `BUILD_MAP.md`.

### T22: Summary arms test (bible ticket 7b)
Priority: CORE · Window: HERE writes, **PI generates, HUMAN rates** · Blocked by: T21 · **Status: TOOL READY** (`scripts/rate.py summaries`; needs the Pi and your ratings)
Spec: 10 passages, both summary arms; record support-check results, readability grade vs passage, and a "would a Class 6 student understand this?" rating. Keep the arm that is more faithful first, more readable second; report both.
Done when: choice recorded with numbers.

### T23: Relevance test (bible ticket 7c)
Priority: CORE · Window: HERE writes the sheet, **HUMAN rates** · Blocked by: T05, 10 dev passages (H6) · **Status: TOOL READY** (`scripts/rate.py relevance`; needs your ratings; **the only place selection weights may change**)
Spec: a human marks each chosen answer "key idea / minor detail / trivial"; no candidate in the top 3 may be "trivial". **Only here may selection weights change, and only on the dev half.**
Done when: share "key idea" recorded; weights changed or left alone, with reasons.

### T24: Counterfactual passages and the trap check (bible ticket 8c): **go/no-go for the live trap beat**
Priority: CORE (headline metric) · Window: **HUMAN writes**, HERE writes the checker, PI runs it · Blocked by: T18 · **Status: TOOL READY** (loader, validator, `trap_check.py`, template, validated example; **you write the 16-20 passages**; needs the Pi for the trap check)
Spec: 16-20 passages in `data/counterfactual/<id>.txt` plus `<id>.json`: `{sentence_idx, passage_value, memory_value, type}`. Half dev, half held-out (held-out owner keeps theirs, nobody tunes on it). `scripts/trap_check.py` runs the **targeted baseline with the passage in context**, 3 tries per fact, on the dev half only, and lists which facts trap the model.
Go/no-go: if fewer than about a third of dev facts trap the model, replace the live evade-then-catch beat with a prepared ordinary-passage example and say so.
Done when: kept facts listed with the filter stated.

---

## Track D: evaluation (numbers come from scripts)

### T25: Baseline arms
Priority: CORE · Window: HERE · Blocked by: T07, T09 · **Status: DONE** (three baseline arms with the passage in context; plain `Question:/Answer:` format; never invents an answer on a parse failure)
Spec: three arms, all with the passage in context: **targeted** (told the sentence), **free-form** (scored only on items touching the planted sentence, **coverage reported**), **grounded-prompt** ("answer only from the passage and quote the supporting sentence"). The LENTERA-style JSON schema and the number-extraction helpers are the only things reused.
Watch out: JSON from a 1B model breaks; repair for the baseline only, and **do not copy fallbacks that invent answers** (they would flatter the baseline's failure rate).
Done when: all three arms produce a scorable item for each planted passage.

### T26: `scripts/counterfactual_eval.py`: scores A-D
Priority: CORE · Window: HERE · Blocked by: T24, T25, T10 · **Status: DONE** (scores A-D, Wilson intervals, dev filter only, held-out never filtered; stub-tested)
Spec: A = baseline key follows memory; B = Sakshi key follows passage (100% **by construction**; stated as a design guarantee); C = summary mentions the memory value; D = stem sensible (human-rated). Whole-token match with units normalised (`90 °C`, `90°C`, `90 degrees`). Writes `metrics.json`.
Watch out: `100` matching inside `1000`; Sakshi's forced selection must be stated; dev (filtered) and held-out (unfiltered) reported separately.
Done when: runs on the stub arms with known answers and reports the expected numbers.

### T27: Ablations A and C
Priority: SUPPORTING (A and C are on the keep list) · Window: HERE · Blocked by: T26 · **Status: TOOL READY** (ablation A is the plain span check, computed in T26; ablation C sheet and scorer written; ratings pending)
Spec: A = baseline plus our checks; C = answer-first with a code template stem instead of the model's, to show what the model adds.
Done when: reported even if the model adds little.

### T28: `scripts/proof_card.py`
Priority: CORE · Window: HERE · Blocked by: T26 · **Status: DONE** (proof card from metrics files; caveat first; says SIMULATED when a stub produced the numbers)
Spec: renders the proof card text straight from `metrics.json`, caveat first ("these passages are built to expose the trap"), n and denominators shown, dev and held-out labelled.
Done when: no number in the card is typed by hand.

---

## Track E: demo layers

### T29: `regen.py`: one-question regeneration (Layer 9)
Priority: CORE (judge's edit) · Window: HERE · Blocked by: T10, T20 · **Status: DONE** (`regen.py`, `sakshi edit`; untouched items proven identical; **Pi timing pending**, target under 15 s)
Spec: diff old and new passage by sentence; for items whose witness changed, re-pick the term (same kind), update the key at once, re-run stem checks, call the model only if a check fails; rebuild options; re-run the summary support and number checks and flag `STALE`; leave untouched items byte-identical. Highlight item-bearing sentences for the judge.
Watch out: re-picking every item; a deleted witness goes RED ("witness removed"); an edit to a sentence with no item.
Done when: byte-identical untouched items; time measured on the Pi (target under 15 s, else the edit moves to Q&A).

### T30: Classroom Hotspot: `serve.py`, `web/index.html`, `scripts/hotspot.sh`
Priority: STRETCH (first on the cut list) · Window: HERE writes, **PI + phones test** · Blocked by: T11, T20 · **Status: DONE HERE; Pi and phones pending** (page tested in a real headless browser: highlight, typed answers, both Reread Loop paths, zero external requests; `hotspot.sh` UNTESTED)
Spec: standard-library `http.server` bound to `0.0.0.0`, one static page with inline CSS and JS (no CDN, no web fonts), quiz as JSON, answers checked in the browser, wrong answer highlights the witness, optional anonymous per-sentence miss counts in memory only; NetworkManager hotspot, WPA2, 5 GHz non-DFS, **no uplink**; QR cards printed in advance.
Watch out: bound to `127.0.0.1` (phones can't reach it); a CDN hang offline; captive-portal pop-ups on iOS and Android; answer key visible in the DOM before answering (acceptable, but don't print it).
Done when: 5 phones (iPhone and Android) join with the uplink unplugged and `ip route` shows no default route.

### T31: Thread sweep (and KleidiAI A/B if time)
Priority: SUPPORTING (thread sweep is on the keep list) · Window: PI · Blocked by: T19 · **Status: TODO**
Done when: numbers with conditions, translated into classroom numbers (passages per period, seconds per regeneration).

### T32: Energy per passage
Priority: STRETCH · Window: PI + HUMAN (hand-read meter) · Blocked by: T18, H4 · **Status: TODO**
Done when: `energy.json` with the power bank named; throttling checked.

### T33: Demo script, saved run, backup recording
Priority: CORE · Window: HERE writes, PI runs · Blocked by: T10, T28 · **Status: TOOL READY** (`docs/DEMO.md`, `scripts/demo.sh` rehearsal verified end to end with the stub, `save_villain.py` refuses to stage a failure; **rehearsals, real villain and recording pending**)
Spec: `docs/DEMO.md` with the 3:00 cut, a 60-second walkaround and a failure runbook (bible ladder 4b, 4c, 5, 6); `scripts/demo.sh`; a saved run for the villain beat; a backup recording; two stopwatch rehearsals.
Done when: two timed clean runs.

---

## Track F: docs and handoff

### T34: README, `THIRD_PARTY_NOTICES.md`, provenance, requirement map
Priority: CORE · Window: HERE · Blocked by: T14 · **Status: DONE** (README, `docs/REQUIREMENTS.md`, `THIRD_PARTY_NOTICES.md`; licence not chosen; Llama licence unverified)
Spec: README order from blueprint 12.9; provenance table (what we reused, under which licence, what's new); "Built with Llama" notice **after** reading Meta's page; requirement map to the five mandatory deliverables.
Done when: a stranger can run the stub demo from the README in one command.

### T35: One-page proposal (due 6 Nov)
Priority: **CORE, due first** · Window: HERE drafts, HUMAN submits · Blocked by: H3 (soft), `BIBLE` v1.3 · **Status: DRAFTED** (`PROPOSAL_DRAFT.md`; needs your blanks; **two facts cannot be cited because their sources are not in the files provided**)
Spec: barrier, learner group, how the PoC addresses it (the bible's deliverable text), the trap, the measurements we will report, one-paragraph deployment sketch **with only sourced figures**, and what we have not tested.
Watch out: do not quote our own numbers (none exist); do not claim learning gains; verify the 63% figure at its source (bible ticket 8g).
Done when: submitted.

### T36: `HANDOFF.md`
Priority: SUPPORTING · Window: HERE · Blocked by: any milestone · **Status: DONE (first version at M0; overwrite at the end of every session)**
Spec: so a fresh session can continue: what's built (by ticket), what's verified versus only read, open bugs, exact commands, next three tickets, traps already hit, stale sections. Written at the end of every working session.

---

## Milestones

| Milestone | Tickets | Meaning |
|---|---|---|
| **M0: stub demo** | T01-T14 | The whole pipeline, quiz and report run end to end with the stub model. Nothing real yet |
| **M1: first real generation on the Pi** | T15-T17 | The real model produces text on your Pi |
| **M2: spine on the Pi** | T18, T20 | One passage, real model, run card, offline proof. **Meets deliverables 2-4** |
| **M3: go/no-go answered** | T21-T24 | Stem quality, summary arm, relevance, trap: the design is confirmed or changed |
| **M4: measured** | T25-T28 | Counterfactual numbers and proof card from scripts |
| **M5: demo-ready** | T29, T33, T34 (T30-T32 if time) | Rehearsed twice, backup recording exists |

## Cut list (from the bible, in order)

room view → checks 14-20 → 8-bit comparison → ablation B → **T30 hotspot** → **T32 energy** → `--include-amber` → human rating beyond one rater → KleidiAI. **Keep:** thread sweep, ablations A and C, grounded-prompt baseline.
**Never cut:** offline proof (T20), run card (T12), readability and relevance (T04, T05), >=3 questions with cloze fallback (T10), student quiz with Reread Loop (T11), tiers (T08), **counterfactual test (T24-T26)**, **regeneration (T29)**, impact explanation, results table with denominators, backup recording (T33).

## Findings log (add as the build teaches us things)

| Date | Finding | Effect |
|---|---|---|
| 4 Nov | Container reaches PyPI but not Hugging Face or GitHub; no Pi attached | Model download and all real runs are PI tickets |
| 4 Nov | First selection run picked filler verbs; fixed with a plain-words list and a case-leak fix in distractors | Selection quality still unmeasured (T23). `rusts` beats `oxygen`; do not tune on one passage |
| 4 Nov | `pip install executorch==1.5.1` pulls a large dependency set; the import needs `torch` | Confirms the in-process memory and start-up warning in bible ticket 2; T12 must name the runner |
| 4 Nov | **`pip install executorch` does not install `torch`, but the runner imports it at load time** (`import torch` is the first line of `executorch/extension/llm/runner/__init__.py`) | T15 must install a `torch` wheel on the Pi too: bigger install, more RAM, slower start-up. The run card must name which process produced memory numbers |
| 4 Nov | **Real runner API** (read from the 1.5.1 wheel's type stubs): `TextLLMRunner(model_path, tokenizer_path, data_path=None)`; `generate(prompt, GenerationConfig, token_callback, stats_callback)`; `GenerationConfig(echo, max_new_tokens, warming, seq_len, temperature, num_bos, num_eos)`; `Stats` has `first_token_ms`, `inference_start_ms`, `prompt_eval_end_ms`, `inference_end_ms`, `num_prompt_tokens`, `num_generated_tokens`, model load start/end; `reset()` clears the KV cache | **No seed parameter**: retries must vary temperature (temperature 0 repeats). Call `reset()` before each independent prompt so one question's context cannot leak into the next. Set `echo=False`. `num_bos` must be settled against the prompt template (T17) |
| 4 Nov | **Showing the summary before the questions leaks the answers**: questions come from central sentences, and the summary restates exactly those | `study` asks questions first and shows "In short" as a review (bible Layer 7 updated) |
| 4 Nov | Distractors were the same four words in every question and mixed word forms (`rusts`, `painting`, nouns). Fixed: sampled per item from a wider pool, preferring the key's word ending | Quality still limited without a part-of-speech tagger (`thin`, `reddish-brown` offered for `layer`); judge it in T21/T23, not by eye |
| 4 Nov | `python -I` (isolated mode) ignores `PYTHONPATH`, so subprocess tests failed until they dropped it | Test harness only. Use `-I` for scripts that read untrusted files, not for our own CLI tests |
| 4 Nov | **The first `prove_offline.sh` lied**: it printed "no route out" in this container, which does have a route, because `ip` was missing and direct HTTPS is proxied, so every probe "failed". Fixed: default route read from `/proc/net/route`, a missing tool is `UNKNOWN` (exit 2), proxies bypassed and warned about | A proof script must fail closed. Re-run it on the Pi with Ethernet unplugged and read the result line, not just the "good" lines |
| 4 Nov | The runner's import needs only `executorch`, `torch`, `numpy`, `tqdm`, `typing_extensions` (measured by diffing `sys.modules`). A full `pip install executorch` also pulls pandas, scikit-learn, scipy and coremltools | `pi_setup.sh` tries a slim install first and falls back to the full set; slim result recorded below once the test finishes |
| 4 Nov | A missing model file, tokenizer or runner raised a traceback from the CLI | CLI now exits with a one-line message for FileNotFoundError, ImportError and RuntimeError |
| 4 Nov | **Slim install verified on x86**: `pip install --no-deps executorch==1.5.1` plus `torch numpy tqdm typing_extensions` imports the runner (1.9 s). No pandas, scipy, scikit-learn or coremltools needed. 5.5 GB here only because x86 torch pulls CUDA libraries; the Pi's aarch64 wheel size is **unverified** | `pi_setup.sh` slim path is a good first try on the Pi; the full fallback stays |
| 4 Nov | The 63% school-internet figure and the quizzing-with-feedback numbers have **no source in the harvest files** (they came from a first research round not in the zip) | Proposal marks both as needing a primary source (bible ticket 8g); do not quote either until it is read |
| 4 Nov | **A plain "is the answer in the passage?" check catches every planted-fact memory answer** whenever the memory value is absent from the passage (our own scorer reports it as `A_span_check`). It would NOT catch a wrong answer that IS in the passage, which is what the published 96% figure is about, and it cannot give a witness | Do not headline "span checks fail". Say: our test shows the simple check works here; the design's value is that the key cannot be invented, plus the witness, plus the summary guarantee |
| 4 Nov | **Real-browser test found a bug unit tests could not**: pressing Enter to submit a typed answer also pressed "Next" (focus moved mid-keypress), so the student never saw the feedback | Fixed (preventDefault, deferred focus). Keep the headless-browser test in the suite |
| 4 Nov | **Regeneration compared an item with its own old question**: the near-duplicate check failed every edited item, regenerated, failed again and sent it RED | Fixed; found by the regen tests |
| 4 Nov | The proof card and saved villain made from a stub looked like real results | Both now print a loud SIMULATED banner when any backend is a stub; the villain refuses to build unless the baseline really answered from memory |
| 4 Nov | `unshare -n` works in this container, so isolation is tested for real, with a control that must report NOT isolated | `prove_isolation.sh` saves both probes and fails if the control looks isolated |
| 4 Nov | `sakshi report | head` crashed with a traceback (BrokenPipeError) | CLI now exits quietly when the reader leaves |
