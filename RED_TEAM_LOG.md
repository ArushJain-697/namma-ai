# SAKSHI: red-team and mock-judge log

*4 Nov 2026. Target: Master Bible v1.2. Result: fixes folded into v1.3. Method: blueprint prompts P4 (hostile engineer and hostile judge, repeated) and P5 (mock judge).*

**Read this first: the limits of this review.** The same model that wrote the plan reviewed it. Self-review has blind spots, and it can only attack what is written down. Nothing here was run on a Pi, so every "this will fail" below is reasoning from the harvest files, not a test. A real mock judge is still needed: someone who has shipped on a Pi, and a teacher. Severity labels are ours.

**Severity:** CRITICAL = breaks a headline claim or a mandatory deliverable · HIGH = a judge or the build will likely hit it · MED = costs points or time · LOW = hygiene.

---

## Round 1: hostile engineer ("what won't run")

| # | Sev | Flaw | Fix applied in v1.3 |
|---|---|---|---|
| F1 | **CRITICAL** | **The trap may not fire.** Ticket 8c checked each planted fact by asking the 1B model the *bare question, with no passage*. But the baseline arm gets the passage in context. Models that fall for a planted fact with no passage may copy it correctly when it is right there. The headline demo beat (evade, then catch) rests on this. | 8c now tests the **baseline arm as it will run, with the passage in context**. A planted fact counts as a trap only if the baseline follows memory in at least 1 of 3 tries. If few facts trap the model, the beat is replaced by the prepared ordinary-passage villain, and we say so. |
| F2 | HIGH | **Filtering inflates the headline.** Keeping only facts that trap the model, then quoting "baseline followed memory X%", is selection. | The filter is applied to the **dev half only**. The held-out half is unfiltered. Both rates are reported with n, and the filter is stated on stage. |
| F3 | HIGH | **Scoring A-D is undefined for items the system didn't choose.** Layer 3 may not select the planted sentence; the free-form baseline may not ask about it. | Eval mode **forces** the item for the planted sentence (term from that sentence). Baseline runs two ways: *targeted* (told which sentence) and *free-form* (coverage of the planted sentence reported). |
| F4 | **CRITICAL** | **The isolation and the resident process collide.** The model runs under `unshare -n` so "the model has no network" is literally true. But `study`, `edit` and `serve` would talk to a resident model over localhost TCP, and a process in its own network namespace is not reachable that way. | The resident model process talks over a **Unix domain socket at a filesystem path** (pathname sockets cross network namespaces). New ticket 8i tests this. |
| F5 | MED | `unshare -n` normally needs root or enabled user namespaces. | `sudo unshare -n` (or `unshare -rn`) tested on the Pi in ticket 8i; fallback is to unplug and show `ip route`, and say the namespace claim was not available. |
| F6 | MED | **Model load is unmeasured.** A ~1.8 GB file on a Pi's storage may take tens of seconds. If every `edit` or run reloads it, the "under 15 s" regeneration claim is false. | One **resident model process**; load time measured once and shown on the run card. |
| F7 | MED | Running `llama_main` (measurement) and the Python runner at once doubles memory on a Pi whose RAM is unknown. | Never run both together. RAM added to the questions for organisers. |
| F8 | HIGH | **Scope.** Layers 1-10 plus baseline, scorer, ablations and metrics in 6-8 hours is not credible if pre-written code is banned. | **Plan P / Plan E** in section 19: what we build before the event if allowed, and what is cut if everything is written on the day. |
| F9 | LOW | Hotspot hygiene: an open access point in a venue, congested 2.4 GHz, DFS channels. | WPA2 password on the QR card; 5 GHz non-DFS channel; tested at the venue's start. |
| F10 | MED | A judge may edit a sentence with no item (about half the sentences have none). Beat falls flat. | Item-bearing sentences are **highlighted and numbered** on screen; the judge picks one. |

## Round 2: hostile judge ("what will I say")

| # | Sev | Flaw | Fix applied in v1.3 |
|---|---|---|---|
| F11 | **CRITICAL** | **The principle has a hole at the first thing the student reads.** The "In short" summary is model-written, protected only by a number check. A non-numeric claim from the model's memory goes straight to the student, who is the person least able to spot it. "No witness, no question" doesn't cover it. | **Witnessed summary:** code picks the 2-3 most central passage sentences; the model only *simplifies each one* in a short call; code checks each summary sentence against its source sentence (support check, numbers, names). **No witness, no summary sentence.** The whole-passage summary becomes a comparison arm. Also makes the summary part of the counterfactual test (C) fairer and cheaper (shorter prompts). |
| F12 | HIGH | **"Why is there an LLM at all? This is fill-in-the-blank with reworded stems."** | Ablation C: answer-first with a code template stem vs the model stem, rated for wording. If the model adds little, we report it. Q&A answer added. |
| F13 | HIGH | **Strawman baseline.** "One call, no checks" is weaker than what a competent person would do. | Added **grounded-prompt baseline** ("answer only from the passage and quote the supporting sentence"), a prompt-only fix. If it closes most of the gap, we report that. |
| F14 | MED | **Demo timing.** Joining a Wi-Fi network by QR takes 30-60 s per judge; two participatory beats in 3 minutes is tight. | QR cards are up from 0:00 and judges join during the hook and proof toggle; two pre-joined phones take the quiz in the beat; others optional. |
| F15 | MED | **Arm is the program lead and the Arm proof is cut first.** | Thread sweep is cheap (a loop around one run) and moves to "keep"; KleidiAI comparison is last to cut among extras. |
| F16 | MED | **No real user.** Societal relevance leans on one news statistic and an invented student. | One teacher or student conversation (8b) is targeted **before the 6 Nov proposal**, even if 15 minutes on a call. |
| F17 | LOW | "About 63%" and "affordable" are unverified: the figure comes from a news report of official data, and no price is checked. | New ticket 8g: read the primary source for the school figure and write a priced bill of materials. Neither claim goes in the proposal unsourced. |
| F18 | MED | Metric D (stem sensible) and the readability check rest on human judgement and a rough formula. A 2026 study found the choice of judge changes estimated conflict strength several-fold. | One fixed written rubric, two raters if possible, n and rater stated. Readability reported as a guide only. |

## Round 3: organiser, sponsor and ethics ("what could embarrass us")

| # | Sev | Flaw | Fix applied in v1.3 |
|---|---|---|---|
| F19 | MED | **Llama licence.** The weights are under Meta's own community licence, not MIT or BSD. It likely requires a "Built with Llama" notice and carries an acceptable-use policy. We haven't read it. | Provenance row added: notice in README, `THIRD_PARTY_NOTICES.md` and a slide; link the `.pte`, don't redistribute it; **read Meta's licence page before relying on this** [UNVERIFIED]. |
| F20 | MED | **Unknown event logistics:** demo format and length, venue power outlets, whether a Wi-Fi hotspot is allowed, how the passage is delivered. | Questions 7-9 added for the organisers. |
| F21 | LOW | **The proposal (due 6 Nov) isn't designed.** It's the first screening, and the bible has no proposal outline. | Noted as the next deliverable: a one-page proposal from v1.3. |
| F22 | LOW | Consent and data for any student try-out; an open AP is also a privacy hole. | Already covered (risk 9); WPA2 added (F9). |
| F23 | LOW | The counterfactual test cited prior work as `[UNKNOWN]`. | Found: it is an established setup (see below). We say we **apply a known test** to a classroom tool. |

### Prior work found (search snippets only, papers not read: label `[SOURCE, snippet only]`)
- Xie et al., 2023, *Adaptive Chameleon or Stubborn Sloth* (arXiv 2305.13300): builds counter-memory passages and studies whether models follow context or memory. The snippet hints that smaller models lean on stored answers, which is fragmentary.
- *Investigating Context-Faithfulness in LLMs: The Roles of Memory Strength and Evidence Style* (arXiv 2409.10955).
- *LLMs' Reading Comprehension Is Affected by Parametric Knowledge and Struggles with Hypothetical Statements* (arXiv 2404.06283): directly about comprehension, which fits our "reads the passage" framing.
- None of the results isolated small models. **Read at least 2305.13300 before quoting any of it.**

---

## Mock judge (blueprint P5)

**Rubric used:** Namma publishes none, so this uses the nearest public analogy, the ExecuTorch Hackathon rubric (technical 40, use case 25, local and privacy 15, deployment 10, presentation 10) [SOURCE, different event]. **An analogy, not Namma's rules.** Scores are "on paper": a plan cannot earn points for what hasn't been run, so no score here is higher than a plan can justify.

**Panel (personas inferred from sponsor roles, not confirmed):** an Arm engineer, an IIIT Bangalore education researcher, a NASSCOM / industry deployment reviewer.

| Criterion | Max | v1.2 as written | Projected with v1.3 | Why |
|---|---|---|---|---|
| Technical | 40 | 26 | 30 | Strong design, nothing run. Gap: unprotected summary (F11). Arm-specific optimisation optional. Lifts if the trap test (F1) holds and the thread sweep gives an Arm-specific number. |
| Use case | 25 | 19 | 20 | Clear student and barrier. Gap: no real user (F16); home-internet challenge answered but not sourced. |
| Local and privacy | 15 | 12 | 13 | Offline proof strong. Gap: hotspot needs the "no route out" explanation to land; AP security (F9). |
| Deployment | 10 | 5 | 6 | **Lowest, by share (50%).** "Affordable" unpriced; device access in schools unknown; Pi supply unknown. |
| Presentation | 10 | 7 | 8 | Strong beats, timing risk (F14). |
| **Total** | **100** | **69** | **77** | Projection assumes tickets 8c, 8d and 8g pass. It is a plan, not a result. |

**Lowest-scoring criterion and the fix:** Deployment. Ticket 8g adds a priced bill of materials (Pi 5, cooler, power bank, SD card) with a source for each price, and the proposal gets a one-paragraph deployment sketch with the device-access question named as unknown. Technical is next: F11 and F1.

### Questions each judge would ask, and what raises the score
**Arm engineer:** "What did Arm's kernels add, measured?" → keep the thread sweep and try the KleidiAI A/B. "Which numbers are in-process and which from `llama_main`?" → the run card names the runner. "Does it throttle?" → `vcgencmd get_throttled` on the card.
**Education researcher:** "Are these questions worth asking?" → relevance rating and ablation C. "How do you know students understand the summary?" → readability guide plus rater rubric; say it is untested with students. "Does the Reread Loop help?" → we don't claim it does.
**Industry reviewer:** "Who pays for the Pi, who loads the passages, what devices do students use?" → priced BOM and workflow as a proposal; device access stated as unknown.

### Scorecard re-score (blueprint 12.2, max 120)

| Criterion | Wt | v1.2 (self) | Red-team-adjusted | Projected v1.3 | Reason for change |
|---|---|---|---|---|---|
| Human stakes | ×3 | 4 | 4 | 4 | |
| Named trap | ×3 | 5 | **4** | 5 | Unproven until 8c shows the baseline falls for planted facts with the passage present |
| Category shift | ×2 | 4 | 4 | 4 | |
| Rubric coverage | ×3 | 4 | 4 | 4 | |
| Sponsor tech load-bearing | ×2 | 3 | 3 | 3 | |
| Independent evidence | ×2 | 4 | 4 | 4 | |
| Provable in event time | ×2 | 5 | **4** | 4 | Filtering and forced selection must be disclosed; scorer needs a build |
| Live, participatory demo | ×2 | 5 | **4** | 4 | Join-time and variance (F14) |
| Spine by checkpoint | ×3 | 4 | **3** | 4 | Scope, until Plan P/E tiering (F8) |
| Reuses your pattern library | ×1 | 2 | 2 | 2 | |
| Low demo variance | ×1 | 4 | **3** | 3 | Hotspot and resident process |
| **Total** | | **99** | **88** | **94** | Still a "Go" (85+), by a smaller margin than v1.2 claimed |

**Honest read:** v1.2's 99 was generous. Adjusted for what the red team found, it is about 88, just over the line. The plan reaches about 94 only if tickets 8c, 8d and 8g come back well. **Tickets 8c and 7b are now go/no-go points for the pitch itself**, alongside ticket 7.

---

## What this review did not do
- Did not run anything. All of F1, F4, F5, F6 and F14 are predictions to confirm on a real Pi and phones.
- Did not read the three cited papers; snippets only.
- Did not read Meta's licence page.
- Did not test the timing of any demo beat.
- Did not use an outside human judge.
