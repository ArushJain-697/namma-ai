# Harvest 06: hackathon entries (how to present and measure)

Harvested 2026-11-04. Firecrawl ran out of credits part-way through and was dropped. The rest came from `curl` to raw.githubusercontent.com and public pages, a few GitHub API tree calls, WebSearch and WebFetch. Nothing was cloned, saved or run.

All wording is paraphrased, and no source code or write-up text is copied. Treat every number here as the team's own claim; none was reproduced. Licences were identified from the opening lines of each LICENSE file, so read the full file before copying code.

## Key findings

1. **Toddle AI is the closest technical match:** it runs Llama 3.2 1B Instruct through ExecuTorch on the CPU (XNNPACK), and the model only explains results that deterministic code produced. Its README says it has no committed latency or throughput numbers, so measured benchmarks would set us apart from it.
2. **LENTERA does what we do, but without checks:** its quiz generator parses the model's JSON and returns it, with no check in that file for four choices or that the answer is among them. Deterministic validation is our clearest difference from this education winner. Its other files were not reviewed for validation.
3. **Offline was shown by airplane mode and missing permissions, not by evidence artefacts:** see the offline section. Saving a network-off proof with the results would go further than the entries read.
4. **Bharat PS4 (education) requires an Arm Android phone, not a Pi.** Don't describe our PoC as fitting it.
5. **Arm's rules allow open source only if licences are followed and the entry builds on it.** Bharat also requires original, solely owned work. Check Namma's equivalent wording, since our plan is reuse. Namma's rules were outside this harvest.

## How far to trust placings

| Entry | Placing | Evidence |
|---|---|---|
| Lodestar | 1st ("Champion") | Lablab results page, via a summarising fetch; the "Champion" label is in the raw page. Its own README claims the Copilot-Powered Build Award instead, so it may hold both |
| SixthSense | 2nd | Own README only |
| Toddle AI | 3rd | Own README only |
| SafeScreen AI | Unknown | Repo returns 404 |
| WALDO | 3rd | Own Devpost page only |
| Sound Sense, DCSM, Cube Tutor | Unknown | Arm page still said winners would be announced soon (cached 2 Nov) |
| LENTERA | Ollama Prize | Confirmed by Kaggle and Google |
| AptusTutor | Not a winner | Absent from the winners list |

**Numbers do not transfer.** These ran on an Alif E8 microcontroller board, a Galaxy S25 Ultra, x86 mini PCs and a low-end phone. Use them as examples of how to report, not as Pi 5 targets.

## Findings table

Effort is my estimate to apply the item to our PoC: S under 1 h, M 1-3 h, L over 3 h.

Tags: TAKE-CODE means a permissive licence plus code worth reusing. Documents stay TAKE-IDEA even in MIT repos, because a write-up's structure is an idea.

**Pinned repo roots used below:**

- **Lodestar** (repo renamed from QCOM): https://github.com/arpan-s-dev/LodeStar/tree/b691708f78eb9e79b7696620be315eafb6ffd26c
- **SixthSense** (renamed): https://github.com/shanayg15/SixthSense-QualcommxMeta/tree/05f46d7b50a9b11837299a3b0e6eebbecc7f9555
- **Toddle AI:** https://github.com/preyashyadav/toddle-ai/tree/702f532a27bfc66c7aeaad46afe2f13f2a09a46a
- **Sound Sense:** https://github.com/Parth-Bansal30/e8-hackathon/tree/0d8b0f135db371f686cb4cec83925973f604206a
- **DCSM:** https://github.com/abhijitbetigeri/executorch-alife8/tree/3d43f690888f2f6a584bd2fdddbb0f3bad6b609d
- **LENTERA:** https://github.com/fengkiej/lentera/tree/136f026bf069c54bc02fc81506c02d6a2ba90ed3
- **AptusTutor:** https://github.com/MathiasKwi900/AptusTutor/tree/579c444df6b4e040e59ddfca2c37b72f941ad79f

### Code worth taking

| Entry | Item | What it does | URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| Toddle AI | Llama prompt builder | Builds the Llama 3 chat template, tells the model to use only supplied measurements, and lists stop markers to strip from visible output. | [PromptBuilder.kt](https://github.com/preyashyadav/toddle-ai/blob/702f532a27bfc66c7aeaad46afe2f13f2a09a46a/app/src/main/kotlin/com/toddleai/app/llm/PromptBuilder.kt) | MIT | TAKE-CODE | Port the template and stop-marker list to Python; write our own instructions. Check how `llama_main` handles special tokens first. Keep the MIT notice. | S |
| Toddle AI | Artefact hashing | Writes SHA-256 hashes of model files to a report. | [hash_artifacts.sh](https://github.com/preyashyadav/toddle-ai/blob/702f532a27bfc66c7aeaad46afe2f13f2a09a46a/toddleai_pte_export_starter/scripts/hash_artifacts.sh) | MIT | TAKE-CODE | Record the `.pte` and tokenizer hash with each result. Remove its failure-masking; use `sha256sum` if `shasum` is absent. Keep the MIT notice. | S |
| LENTERA | Quiz generator | Prompts for a set number of 4-choice questions, returns a JSON array of question, choices and answer, and strips code fences. | [generate_flashquiz.ts](https://github.com/fengkiej/lentera/blob/136f026bf069c54bc02fc81506c02d6a2ba90ed3/lentera-be/src/libs/flashquiz/generate_flashquiz.ts) | MIT-form text, no title line | TAKE-CODE | Use the schema as our starting output format, adapted for a passage. Add the missing checks ourselves. Keep the notice. Test on 1B, which is far smaller than the Gemma model it was written for. | S |
| AptusTutor | JSON extractor | Looks for fenced JSON, falls back to bracket matching, then validates. Documents its own weakness with brackets inside strings. | [JsonExtractionUtils.kt](https://github.com/MathiasKwi900/AptusTutor/blob/579c444df6b4e040e59ddfca2c37b72f941ad79f/app/src/main/java/com/nexttechtitan/aptustutor/utils/JsonExtractionUtils.kt) | Apache-2.0 with NOTICE | TAKE-CODE | Follow the fallback order in Python. A port is a derivative: keep LICENSE and NOTICE, mark changes. Python's `json.JSONDecoder.raw_decode` may avoid the bracket weakness; writing it fresh from that would avoid the duties. | M |
| Lodestar | Standalone check script | Python script that runs the rule logic and its proof cases without the app or the model. | [verify_safety_tree.py](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/scripts/verify_safety_tree.py) | MIT | TAKE-IDEA | Same shape: checks that run with no model. The triage rules themselves don't apply, so no code is needed. | M |
| Lodestar | Llama export script | Exports Llama 3.2 1B, but for the Qualcomm QNN NPU. | [export_llama.sh](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/runtime/scripts/export_llama.sh) | MIT | SKIP | Wrong backend for a Pi 5 CPU. | - |
| DCSM | Measurement tools | Reads metrics from the running board without halting it, writes timestamped JSON and Markdown, and has dry-run and simulate modes plus a fake debugger for tests. | [dcops/board/](https://github.com/abhijitbetigeri/executorch-alife8/tree/3d43f690888f2f6a584bd2fdddbb0f3bad6b609d/dcops/board) | Mixed: root has an Alif proprietary licence and an Apache-2.0 file; `measure.py` declares Apache-2.0 | TAKE-IDEA | J-Link code is useless on a Pi, and repo licensing is unclear. Copy the design: timestamped JSON plus Markdown, and a simulate mode. | M |

### Documents and methods

| Entry | Item | What it does | URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| Toddle AI | Gate, deterministic core, grounded Llama | Rejects bad input and explains why, computes metrics in code, then has Llama 1B explain only those metrics. Calls itself a research prototype, not a diagnostic tool. | [README](https://github.com/preyashyadav/toddle-ai/blob/702f532a27bfc66c7aeaad46afe2f13f2a09a46a/README.md) | MIT | TAKE-IDEA | Our architecture story. Reject passages outside 150-300 words with a reason. Describe output as a teacher's draft. | S |
| Toddle AI | Load-and-generate smoke test | Times model load and one generation as an early feasibility check. | [LlmSmokeTest.kt](https://github.com/preyashyadav/toddle-ai/blob/702f532a27bfc66c7aeaad46afe2f13f2a09a46a/app/src/androidTest/kotlin/com/toddleai/app/llm/LlmSmokeTest.kt) | MIT | TAKE-IDEA | First script to write on the Pi. | S |
| Lodestar | Deterministic authority | Rules set the verdict, and the model explains but cannot override it. | [README](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/README.md) | MIT | TAKE-IDEA | Core claim: the model drafts, the checks decide. | S |
| Lodestar | Honest-claims demo script | 5-minute judge script that opens with what may truthfully be claimed, and scripts a plain sentence if the model path isn't live. | [DEMO.md](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/DEMO.md) | MIT | TAKE-IDEA | Structure for our 14 Nov script. | M |
| Lodestar | Failure runbook | Golden rule of what works with no model, a safe demo path, a pre-stage checklist, and a matrix of what to say and do per failure. | [DEMO_SAFE_RUNBOOK.md](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/docs/DEMO_SAFE_RUNBOOK.md) | MIT | TAKE-IDEA | Write one. Checks can run on saved outputs if generation fails. | M |
| Lodestar | 10-slide pitch outline | Problem evidence with sources, what was built, signature element, why it can be trusted. | [PITCH_OUTLINE.md](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/docs/PITCH_OUTLINE.md) | MIT | TAKE-IDEA | Slide order for the live event. | M |
| Lodestar | Status dashboard | Checklist with a named de-risk gate. **Caution:** at this commit it still lists Llama and the airplane-mode end-to-end run as open, while the README describes Qwen as working. | [STATUS.md](https://github.com/arpan-s-dev/LodeStar/blob/b691708f78eb9e79b7696620be315eafb6ffd26c/STATUS.md) | MIT | TAKE-IDEA | Keep ours current; stale status undermines honesty claims. | S |
| SixthSense | 5-minute demo script | Timed roles and beats, airplane mode switched on stage, why-on-device section, operator failure playbook, backup video, pre-demo checklist. | [demo_script.md](https://github.com/shanayg15/SixthSense-QualcommxMeta/blob/05f46d7b50a9b11837299a3b0e6eebbecc7f9555/docs/demo_script.md) | MIT | TAKE-IDEA | Best timing template. Copy its step of re-verifying airplane mode after the model loads. | S |
| SixthSense | Risk register and mock contract | Risks with mitigations, a mock mode emitting the same data contract, and a rule-based fallback. | [risk_register.md](https://github.com/shanayg15/SixthSense-QualcommxMeta/blob/05f46d7b50a9b11837299a3b0e6eebbecc7f9555/docs/risk_register.md) | MIT | TAKE-IDEA | One-page risk register. Stub backend emitting the same output JSON. Its listing's Demo link pointed to localhost, so check ours. | M |
| Sound Sense | Measured-on-board table | Each row names what, result and conditions: build, date, clock. Reports denominators, such as the 437 ms median covering 18 of 30 recognised sounds. Links to logs. | [README](https://github.com/Parth-Bansal30/e8-hackathon/blob/0d8b0f135db371f686cb4cec83925973f604206a/README.md) | **No root LICENSE** (Alif licence for firmware) | TAKE-IDEA | Results format; always give the denominator. | M |
| Sound Sense | Gate results and raw logs | Pre-set tests with verdicts of GO or SOFT, what each verdict changed, and raw logs committed. | [GATES-results.md](https://github.com/Parth-Bansal30/e8-hackathon/blob/0d8b0f135db371f686cb4cec83925973f604206a/docs/GATES-results.md), [docs/gates/](https://github.com/Parth-Bansal30/e8-hackathon/tree/0d8b0f135db371f686cb4cec83925973f604206a/docs/gates) | No root LICENSE | TAKE-IDEA | Commit raw `llama_main` logs. Define pass thresholds before running. | M |
| Sound Sense | Video script | One unedited take of about 2:35: shot list with time, action and screen, narration, recovery lines, and every number traced to a source file. | [VIDEO-SCRIPT.md](https://github.com/Parth-Bansal30/e8-hackathon/blob/0d8b0f135db371f686cb4cec83925973f604206a/docs/VIDEO-SCRIPT.md) | No root LICENSE | TAKE-IDEA | Format for a backup recording. | M |
| Sound Sense | Run sheet and submission draft | Pre-flight checks, timed run of show; a table mapping each requirement to where it is met and its state; a rule that numbers change at one source first. | [DEMO.md](https://github.com/Parth-Bansal30/e8-hackathon/blob/0d8b0f135db371f686cb4cec83925973f604206a/docs/DEMO.md), [SUBMISSION.md](https://github.com/Parth-Bansal30/e8-hackathon/blob/0d8b0f135db371f686cb4cec83925973f604206a/docs/SUBMISSION.md) | No root LICENSE | TAKE-IDEA | Requirement map for Namma's rules; a single source for numbers. | S |
| Sound Sense | Judged tag and self-test | Tags the judged firmware and notes later commits only change docs and tools. Self-test failures stay on screen. **Discrepancy:** Devpost names `v1.2-judged` (0d8b0f1), while the README names `v1.1-judged` ([1d5fe72](https://github.com/Parth-Bansal30/e8-hackathon/tree/1d5fe7236b385e81017fda78b6ea9341573b14b5)). | as above | No root LICENSE | TAKE-IDEA | Quote one tag everywhere. `selfcheck.sh` before the demo. | S |
| Sound Sense | Reports a bad result | Discloses 54% live against 88% offline, and that this reshaped the product. | as above | No root LICENSE | TAKE-IDEA | Report failures per check and what changed. | S |
| DCSM | Results and architecture docs | Separates PC and board numbers, warns where runs can't be compared, states noise, marks unmeasured power as `TODO(measure)`, and gives a workload placement table. | [RESULTS.md](https://github.com/abhijitbetigeri/executorch-alife8/blob/3d43f690888f2f6a584bd2fdddbb0f3bad6b609d/dcops/docs/RESULTS.md), [ARCHITECTURE.md](https://github.com/abhijitbetigeri/executorch-alife8/blob/3d43f690888f2f6a584bd2fdddbb0f3bad6b609d/dcops/docs/ARCHITECTURE.md) | Mixed, as above | TAKE-IDEA | Use the `TODO(measure)` convention rather than estimating. Add a placement table with timings. | S |
| DCSM | Landing page and 15 slides | Stat bar, demo, how it works, slides, under the hood, roadmap. Slides include a page of measured decisions. Video described as unedited apart from trimming. | [Landing page](https://abhijitbetigeri.github.io/executorch-alife8/) | Not stated | TAKE-IDEA | Optional GitHub Pages site. "Measured decisions" slide. | M |
| DCSM | Blank beats wrong; rejected options; "Built on" | Reports correct, wrong and blank rates. Explains with memory figures why no generative model. Lists what predated the event. Pins versions. | [Devpost](https://devpost.com/software/dcsm-simplified-datacenter-service-management-simplified) | Not stated | TAKE-IDEA | Withhold failed output. Report pass, fail and retry. Add a provenance section, essential for our reuse plan. | S |
| LENTERA | Hardware comparison and latency | Table of hardware with cost and 2-16 tokens/s. States a fast cached path and a slow path of 30-90 s. Sourced cost argument. | [Write-up](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/lentera-offline-ai-microserver-for-remote-and-rura) | Write-up CC BY 4.0 per Kaggle | TAKE-IDEA | State real latency honestly and frame use as batch preparation. Only list configurations we measured. | M |
| AptusTutor | Low-end benchmark and stateless runs | Chooses a 4 GB phone as representative. Uses a fresh engine per task to prevent context bleed, at a disclosed 6 min 26 s per task. Sets low temperature. Checks RAM and thermals, with one engine at a time. | [Write-up](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/unlocking-offline-ai-power-with-aptustutor) | Write-up CC BY 4.0 per Kaggle | TAKE-IDEA | One `llama_main` process per task, a lock, temperature logging. Frame the Pi 5 as school-affordable. Report load overhead. | M |
| AptusTutor | Engineering log | Documents each abandoned approach with evidence. | same | as above | TAKE-IDEA | `docs/engineering_log.md` for Q&A. | S |
| Cube Tutor | Honest scope, observability | Says what is unfinished, and discloses that the live path differs from its ExecuTorch prototype. Debugged by inspecting intermediate data. | [Devpost](https://devpost.com/software/cube-tutor) (no repo found) | Not stated | TAKE-IDEA | Save prompt, raw output, parsed output and verdicts per run. | S |
| WALDO | Before-and-after with cause | Names one bottleneck, the fix and the result (frame time halved to 29.7 ms). | [Devpost](https://devpost.com/software/waldo-ztjixc) (no repo found) | Not stated | TAKE-IDEA | Report one measured optimisation. Keep the whole Pi in shot. | S |
| Gemma Vision | User involvement | The developer's blind brother shaped the features, per Google. | [Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/) | Not stated | TAKE-IDEA | Have a real teacher try it, if possible. | M |

### Rules and rubrics

| Entry | Item | What it does | URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| ExecuTorch Hackathon | Proposal criteria | Five tests: edge use case, realistic scope, reason for the stack, specific user problem, path to a live demo. | [Lablab page](https://lablab.ai/ai-hackathons/qualcomm-x-meta-executorch-hackathon) | Not stated | TAKE-IDEA | Closest public model for our proposal, also a proposal-based shortlist. Use as a self-check. | S |
| ExecuTorch Hackathon | Weights and repo rules | Technical 40, use case 25, local and privacy 15, deployment 10, presentation 10. README needs description, team, setup, run and licence. 5-minute demo. | same | Not stated | TAKE-IDEA | Allocate space by weight; README checklist. | S |
| Arm + ExecuTorch | Requirements and rubric | Live demo, public repo, fixed tag, README, architecture, workload placement, measurements. Reliability 20, performance 20, hardware use 15, sensors 15, innovation 10, ambition 10, engineering 10. Good architecture is rewarded over maximum NPU use. | [Devpost](https://arm-executorch.devpost.com/) | Not stated | TAKE-IDEA | Direct checklist. Supports a CPU-only design. Sensors don't apply to us. | S |
| Bharat AI-SoC | Theme and brief | Moves from building AI apps to engineering AI products, across optimisation, benchmarking and validation. Requires Llama through ExecuTorch; names Llama 3.2 1B and Pi 5 CPU-only as options. | [Challenge page](https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html) | Not stated | TAKE-IDEA | Shared vocabulary; confirms our stack is an accepted pattern. | S |
| Bharat AI-SoC | Deliverables and evaluation | Source, application, demo video, technical report, on GitHub. Winners follow a live virtual demo and jury Q&A. **No weighted criteria published.** | same | Not stated | TAKE-IDEA | Add a technical report; prepare for Q&A. | M |
| Bharat AI-SoC | PS4 education brief | Learning assistant, requiring an Arm Android phone. Registration closed 19 Oct 2026. | same | Not stated | SKIP | Doesn't fit a Pi 5 PoC. | - |
| Bharat 1st edition | NeuroTouch | The only public past submission found: a gesture interface on Jetson Nano at 5 W, with `Project_Report.pdf` (unread). No Llama. | [Repo](https://github.com/Vishnudev2006/bharat_ai_soc_challenge/tree/7dcf3dc02b8574b70f1a1ebe6ab6ae15bd08aa8f) | MIT | SKIP | Different domain. Its report may show the expected format. | - |
| Arm Education | Getting Started Resources | Lists Arm LLM and generative AI optimisation courses; nothing on ExecuTorch, benchmarking or report templates. | [Resources](https://arm-education.github.io/online-resources-arm/) | Not stated | SKIP | Too long for this deadline. | - |
| Others | SafeScreen AI, tutor-ai | Repos return 404, so they may be private or removed. SafeScreen's page has mostly aims and no measurements. | - | Unknown | SKIP | - | - |
| Others | Remaining Gemma 3n winners | Not education. | - | - | SKIP | - | - |

## What the entries stressed

| Pattern | Seen in |
|---|---|
| Numbers measured on the device, with conditions and logs | Sound Sense, DCSM; Arm and lablab rubrics |
| Deterministic logic decides, the model explains | Lodestar, Toddle AI |
| Scripted honesty about what is and isn't live | Lodestar, Cube Tutor, Toddle AI, DCSM |
| A demo that survives failure: mock, stub, backup video | SixthSense, Lodestar |
| A specific reason local matters for this user | DCSM, LENTERA, SixthSense; lablab criteria |
| Failures reported with what changed | Sound Sense, DCSM, AptusTutor |

**Repo layouts observed:** source folders plus a heavy `docs/`. Recurring files are `DEMO.md` (Lodestar, SixthSense, Sound Sense), `STATUS.md` (Lodestar, Sound Sense), a demo or video script (SixthSense, Sound Sense), and committed evidence or results (Sound Sense, DCSM). Sound Sense also has a layout section in its README.

**README order observed:** one-line purpose, judged tag or award, what it does, measured results, how it works and placement, layout, build and run, credits (Sound Sense). SixthSense and Lodestar add architecture diagrams and a docs index.

**Benchmark scripts:** only DCSM's `measure.py` is a real harness, and it is J-Link-specific. Sound Sense has `model/eval_ss.py` and `model/delay_sweep.py` (not read). None of these measures an LLM on a Pi, so our harness must be written fresh.

### Proposal phrasing patterns (described, not copied)

1. Open on a concrete scene: who is stuck, where, and why connectivity or cost blocks them.
2. Name the flow in a few verbs, like DCSM's point, hold, inspect. Ours could be paste, generate, check, review.
3. State authority clearly: the model proposes, fixed rules decide.
4. Put a number beside every claim, with sample size and hardware. Before results exist, label them as targets.
5. Justify the hardware as representative of the target user.
6. Disclaim scope in one sentence: a draft for a teacher to review.
7. Separate done from planned.
8. Credit what was reused and state what is new.

### How offline operation was shown

| Method | Entry |
|---|---|
| Airplane mode switched on stage, re-verified after model load | SixthSense |
| Airplane mode on, plus no internet permission | Lodestar |
| Only camera permission, and a Settings screen said to verify this at runtime (README claim; code not checked) | Toddle AI |
| Stated no network and no stored data; unedited video | DCSM, Sound Sense |

**Our version (my suggestion, untested on a Pi):** run the pipeline in an empty network namespace (`unshare -n`), and turn off Ethernet and Wi-Fi on camera. Save `ip addr`, a failed ping and the run's log to `results/<tag>/`, so judges can inspect the evidence later.

## Recommended repo skeleton

Assembled from observed repos and requirement lists.

```text
namma-offline-quiz/
├── README.md                  # Order below
├── LICENSE                    # Lablab: licence required
├── THIRD_PARTY_NOTICES.md     # Arm rule; MIT and Apache duties; Sound Sense credits
├── docs/
│   ├── proposal.md            # Lablab proposal criteria
│   ├── architecture.md        # Arm requirement; DCSM ARCHITECTURE.md
│   ├── technical_report.md    # Bharat deliverable
│   ├── requirements_map.md    # Sound Sense SUBMISSION.md
│   ├── STATUS.md              # Lodestar, Sound Sense
│   ├── DEMO.md                # SixthSense timing; Lodestar honest claims
│   ├── failure_runbook.md     # Lodestar DEMO_SAFE_RUNBOOK
│   ├── risk_register.md       # SixthSense
│   └── engineering_log.md     # AptusTutor
├── models/README.md           # DCSM pinned versions; Toddle hashes; no weights
├── prompts/                   # Toddle template; LENTERA schema
├── src/
│   ├── gate.py                # Toddle: 150-300 words, with a stated reason
│   ├── runner.py              # AptusTutor: one llama_main per task, with a lock
│   ├── backends/              # Lodestar, SixthSense: stub + llama_main, same contract
│   ├── parse.py               # AptusTutor fallback order
│   └── checks.py              # Lodestar, Toddle: the deterministic verdicts
├── tests/fixtures/            # Lablab: tests; Lodestar: known-bad cases, no model needed
├── data/passages/             # Own or clearly licensed passages
├── benchmarks/
│   ├── run_bench.py           # New; DCSM's JSON + Markdown design
│   └── results/<tag>/         # Sound Sense docs/gates: raw logs and per-run artefacts
└── scripts/
    ├── setup.sh               # Arm, lablab: build and run
    ├── selfcheck.sh           # Sound Sense self-test; Toddle hashes
    ├── prove_offline.sh       # Our addition
    └── demo.sh                # SixthSense has one; Arm: repeatable demo
```

Tag the demo commit (e.g. `v1.0-demo`) and quote that one tag everywhere, per the Arm rule and the Sound Sense discrepancy.

**README order:**
1. Purpose and who it's for.
2. Team (lablab).
3. Demo link and judged tag (Sound Sense).
4. Flow in a few verbs (DCSM).
5. Measured results (Sound Sense).
6. Architecture and placement table (Arm, DCSM).
7. Repo layout (Sound Sense).
8. Setup and run (Arm, lablab).
9. Offline proof (our addition).
10. Tests (lablab).
11. Status: done, in progress, not doing (Lodestar).
12. Built on and licences (DCSM, Sound Sense).
13. References (lablab, LENTERA).

**Results table columns** (leave as `TODO(measure)` until measured):

`device and cooling | ExecuTorch version | model hash | runs (n) | load s | time to first token s | tokens/s | total s (p50, p95) | peak RSS MB | max temp C, throttled? | checks pass rate (x/n)`

Sources: Sound Sense and DCSM for format, LENTERA for tokens/s, AptusTutor for prompt prefill and thermals. Peak RSS and pass rate come from your brief.

## Recommended proposal outline

Check first against Namma's own proposal format and criteria.

| # | Section | Content | Source |
|---|---|---|---|
| 1 | Title and pitch | What, for whom, on what device | Lablab fields |
| 2 | Problem and user | A specific teacher workflow, with sourced figures (still to be found) | Lablab criteria; LENTERA, Lodestar citations |
| 3 | Why on-device | Connectivity, cost, student privacy | Lablab criteria; DCSM |
| 4 | Solution flow | Paste, generate, check, review | DCSM |
| 5 | Architecture | Word gate, `llama_main`, parser, checks, report; all on the Pi 5 CPU | Arm placement; Toddle AI |
| 6 | Why this stack | Llama 3.2 1B, ExecuTorch, Pi 5, and rejected options | Lablab; DCSM; Bharat brief |
| 7 | Reliability | The check list, withholding failed output, and the gap in earlier work | Lodestar; DCSM; LENTERA code |
| 8 | Measurement plan | Metrics, method, sample size; labelled targets unless measured | Arm; Sound Sense gates |
| 9 | Offline proof | How judges can verify it | SixthSense, Lodestar, our addition |
| 10 | Scope and limits | Not an auto-grader; what's unfinished | Toddle AI; Cube Tutor; Lodestar |
| 11 | Built on and new work | Reused projects, licences, what we added | DCSM; Arm rule |
| 12 | Live demo and fallback | Beats below; recorded backup | SixthSense; Lodestar; Sound Sense |
| 13 | Next steps | Local languages, teacher pilot | Sound Sense, LENTERA future work |
| 14 | Team and repo | Names, roles, tagged GitHub link | Sound Sense |

**Demo beats (under 5 minutes; my assembly using the SixthSense and Lodestar timing and honesty patterns):**

| Time | Beat |
|---|---|
| 0:00-0:30 | Who it's for. Show the Pi, cut the network, run `prove_offline.sh` |
| 0:30-1:00 | Architecture: the model drafts, the checks decide |
| 1:00-1:20 | A short passage is rejected by the gate, with its reason |
| 1:20-3:00 | Real passage; show true elapsed time, or start it early and return to it. Then summary, at least 3 questions, and check results |
| 3:00-3:30 | A known-bad output fails the checks, like Lodestar's negation pair |
| 3:30-4:15 | Results table, sample sizes, repo tag |
| 4:15-5:00 | Limits, reused projects, next steps |

Generation time on the Pi could consume the whole slot, so measure it before fixing these timings. Keep a saved run and a backup video ready, and say plainly if either is used.

## What remains unread

- **Demo videos:** none watched. Scripts came from repo docs.
- **Slide PDFs:** Lablab's submission PDFs are unread; Lodestar's pitch outline and DCSM's slide list stood in.
- **Bharat first edition:** `www.armbharatchallenge.com` has a certificate mismatch, which I did not bypass. `armbharatchallenge.com/edition1/` loads but returned no readable text, so its winners and evaluation levels are unread. The 2026-27 page gives only totals. PS mentoring videos are unwatched.
- **Gemma 3n judging criteria:** Kaggle's rubric was not obtained.
- **WALDO and Cube Tutor repos:** not found; their Devpost pages link none.
- **Partly read:** several long docs were read only in part (Lodestar `README.md`, `DEMO.md`, runbook and pitch; Sound Sense `DEMO.md`, `GATES-results.md` and `SUBMISSION.md`; DCSM `RESULTS.md` and `ARCHITECTURE.md`; READMEs for LENTERA, AptusTutor and Toddle AI). The LENTERA whitepaper, Toddle `TODDLEAI_TECHNICAL_ARCHITECTURE.md`, SixthSense `DEMO.md` and the Sound Sense handoff docs are unread.
- **Licences:** opening lines only, as noted at the top. AptusTutor's and LENTERA's write-ups were read in full through Firecrawl.
