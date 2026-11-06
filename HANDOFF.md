# HANDOFF

*Rewritten 4 Nov 2026, after building everything that does not need the Pi. Read this, then `BUILD_MAP.md` (tickets and findings), then `MASTER_BIBLE.md` (the why).*

## State
**190 tests pass** (`bash scripts/selfcheck.sh`, stub model only). 19 of 36 tickets done, 14 tool-ready and waiting on the Pi or on you, 3 not started (T19, T31, T32). **Nothing has run on a real model or a Raspberry Pi: no speed, memory or quality number exists.**

**Built and tested here:** gate, witnessed summary, selection, distractors, checks (one seeded fault each), tiers, student quiz with the Reread Loop, run card, baseline arms, Counterfactual Passage Test scorer (A-D, Wilson intervals, dev filter, held-out never filtered), proof card, regeneration (`edit`), rating tools, benchmark, resident model process (tested in a **real network namespace**, with a control), phone page (tested in a **real headless browser**), saved villain, demo runner, docs.
**Written but only tested with fakes:** the ExecuTorch backend (fake runner) and `hotspot.sh` (never run).

## What only YOU can do (the critical path)
1. **Email the organisers** (build map H1); the model list and the Pi's RAM matter most. Plan P (pre-written code allowed) is recorded as confirmed by you; get it in writing.
2. **On the Pi:** `bash scripts/pi_setup.sh` and paste back `results/pi_setup.log`.
3. **Model files** onto the Pi (download elsewhere; read Meta's licence), then:
   ```bash
   ~/sakshi-venv/bin/python scripts/pi_smoke.py --model M.pte --tokenizer T.model
   ```
   Paste the whole output back. The April 2025 export may not load on ExecuTorch 1.5.1.
4. **First real numbers:**
   ```bash
   ~/sakshi-venv/bin/python scripts/pi_bench.py --backend executorch --model M.pte --tokenizer T.model --runs 3
   ```
5. **The four go/no-go gates** (all need steps 2-4 first):
   ```bash
   python scripts/rate.py stems build --out results/stem_rating.csv --backend executorch --model M.pte --tokenizer T.model
   ```
   Fill in the rating column, then `python scripts/rate.py stems score results/stem_rating.csv`. Same pattern for `summaries` and `relevance`.
6. **Write the counterfactual passages** (`data/counterfactual/README.md`; 16-20, half held-out and kept by one person), then `python scripts/trap_check.py --backend executorch ...`.
7. **Isolation and offline evidence on the Pi:** `bash scripts/prove_isolation.sh pi-iso -- --backend executorch --model M.pte --tokenizer T.model` and `bash scripts/prove_offline.sh pi-offline` with Ethernet unplugged. Read the RESULT line; UNKNOWN is not a pass.
8. **Proposal** (due 6 Nov): `PROPOSAL_DRAFT.md`. Two facts need primary sources before they go in (the 63% school-internet figure and the quizzing-with-feedback evidence; neither source is in the files I was given).

## Not started
- **T19** build `llama_main` (measurement runner, needed for clean memory numbers, the thread sweep and KleidiAI). I can't write it reliably without GitHub access from this container.
- **T31** thread sweep, **T32** energy per passage: both need the Pi.

## Traps already hit (don't repeat)
- Summary before the questions gives the answers away: `study` asks first.
- `pip install executorch` does not install `torch`; the runner imports it. Slim install verified on x86.
- The runner has no seed: temperature 0 repeats; retries raise temperature. `reset()` before each prompt.
- A plain span check catches planted-fact memory answers (our own scorer says so): don't headline "span checks fail".
- Stub-made proof cards and villains say SIMULATED; never show one as a result. The villain refuses to be staged.
- Pressing Enter on a typed answer also pressed Next (found only in a real browser); regen compared an item to its own old stem (found by tests). Search tests for `or True`.
- `prove_offline.sh` once reported "no route out" on a machine with a route: it fails closed now.
- `python -I` ignores `PYTHONPATH`.

## Honest weak points to keep in mind
- **Selection quality is unmeasured** (T05/T23): `rusts` still beats `oxygen` on the sample passage; distractors are limited without a part-of-speech tagger. Do not tune on one passage; tune on the dev half only, after ratings.
- The headline Counterfactual test only has meaning if the baseline really falls for planted facts **with the passage in context** (T24 decides; NO-GO means the live beat becomes a prepared example).
- Everything marked `[ESTIMATE]` in the bible stays an estimate until T18 runs.

## Files
`src/sakshi/`: `text gate readability lexicon select distract checks generate pipeline quiz metrics smoke baseline counterfactual cf_eval rate_tools bench proof regen resident serve villain qr cli`, `backends/{base stub executorch_backend factory}` · `web/index.html` · `scripts/` · `tests/` (incl. `e2e_phone.js`) · `data/passages`, `data/counterfactual` · `docs/{DEMO,REQUIREMENTS}.md` · `README.md`, `THIRD_PARTY_NOTICES.md`, `PROPOSAL_DRAFT.md`, `MASTER_BIBLE.md`, `BUILD_MAP.md`, `RED_TEAM_LOG.md`, `CHECKLIST.md`.
