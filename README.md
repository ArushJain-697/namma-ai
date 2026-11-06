# Sakshi: an offline study aid that answers only from the passage

*Namma AI Hackathon, Problem 1 (AI for Inclusive Education). Draft, 4 Nov 2026.*

A student gives Sakshi a 150-300 word passage and gets a short, simple summary and a self-check quiz. **The model never
writes the answer key**: code picks each answer from the passage, so every answer shows the exact sentence that holds it
(the "witness"). No witness, no question; no witness, no summary sentence. It is designed to run on a Raspberry Pi with no
internet, through ExecuTorch.

## Honest status
Everything here is tested **against a stub model** in a cloud container. **Nothing has run on a real model or a Raspberry
Pi yet**, so no speed, memory or quality number exists. See `HANDOFF.md` for what is verified and `BUILD_MAP.md` for the
tickets. The simple "does the answer appear in the passage?" check also catches our planted-fact test cases (our own tests
say so); the design's value is that the key cannot be invented at all.

## Try it (no model needed)
```bash
python3 -m venv .venv && .venv/bin/pip install pytest
PYTHON=.venv/bin/python bash scripts/selfcheck.sh      # tests + a stub demo
PYTHONPATH=src python3 -m sakshi prepare data/passages/rust_ordinary.txt --out run.json
PYTHONPATH=src python3 -m sakshi report run.json        # tiers, witnesses, reasons, run card
PYTHONPATH=src python3 -m sakshi study run.json         # the student quiz
```
On the Pi: `bash scripts/pi_setup.sh`, then `scripts/pi_smoke.py` (see `HANDOFF.md`).

## Commands
| Command | What it does |
|---|---|
| `sakshi check PASSAGE` | is the passage usable (150-300 words, 10% margin)? |
| `sakshi prepare PASSAGE --out RUN [--backend stub\|executorch\|resident ...]` | summary, questions, tiers, run card |
| `sakshi study RUN` | student quiz: questions first, the witness after every answer, then a second question from any missed sentence |
| `sakshi report RUN` | for teachers and judges: tiers, witnesses, reasons for withheld items |
| `sakshi edit RUN --list` / `--sentence N --text ...` | change one fact; only the questions that depend on it change |
| `sakshi serve RUN` | serve the quiz to phones over the machine's own Wi-Fi (optional extra) |
| `sakshi resident --socket PATH` / `probe` | hold the model in one process, optionally with no network at all |
| `sakshi villain FILE` | show the saved baseline failure |

## Layout
`src/sakshi/` core (standard library only) · `backends/` stub, ExecuTorch, factory · `web/index.html` phone page ·
`scripts/` Pi setup, smoke test, benchmark, offline and isolation evidence, evaluation, rating sheets, demo ·
`data/` passages and counterfactual cases · `tests/` · `docs/` demo script and requirement map ·
`MASTER_BIBLE.md` (why), `BUILD_MAP.md` (what and when), `RED_TEAM_LOG.md`, `CHECKLIST.md`, `HANDOFF.md`.

## Not included
No learning-gain claim, no Kannada, no chatbot, no accounts or student data (the optional room view counts missed
sentence numbers anonymously, in memory only). Licence: not chosen yet. Third-party terms: `THIRD_PARTY_NOTICES.md`.
