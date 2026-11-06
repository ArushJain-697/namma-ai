# Requirement map: the brief, Problem Statement 1

*Status is what has actually been run. As of 4 Nov 2026 nothing has run on a Raspberry Pi or a real model; "tested here" means against a stub model in a cloud container.*

| Brief (verbatim where quoted) | How it is met | Command | Status |
|---|---|---|---|
| 1. "Identify one learning barrier, the intended learner group and how the PoC addresses that barrier." | Bible section 2; `PROPOSAL_DRAFT.md` | n/a | Drafted; needs team review and a sourced statistic |
| 2. "Process one organiser-provided educational passage (approximately 150-300 words) with an approved lightweight model running locally through ExecuTorch on Raspberry Pi." | Gate warns inside a 10% margin; ExecuTorch backend wraps the Python `TextLLMRunner` | `python -m sakshi prepare PASSAGE --backend executorch --model M.pte --tokenizer T.model --out RUN` | Backend written and tested with a fake runner; **never run on a real model**; model approval unknown |
| 3. "a short, understandable summary and at least three relevant quiz questions ... Terminal output is sufficient." | Witnessed summary (readability-checked); relevance-scored answers; cloze fallback guarantees three | `report RUN`, `study RUN` | Tested here with the stub; question quality unmeasured (ratings tools exist) |
| 4. "Demonstrate operation without cloud AI inference; report approximate inference time, model used and model size or memory usage" | Run card on every run; `metrics.json`; offline evidence; model process isolation | run card (printed by `prepare`), `scripts/prove_offline.sh`, `scripts/prove_isolation.sh`, `scripts/pi_bench.py` | Run card and isolation tested here (isolation really, in a network namespace); **no real number exists yet** |
| 5. "a brief impact explanation ... with one concrete example from the supplied passage" | Template filled from the organiser's passage on the day (bible section 11) | n/a | Template only |
| Expected outcome: "a credible demonstration of how this supports learners" | Student quiz with the witness as feedback and the Reread Loop; phone page | `study RUN`, `serve RUN` | Tested here (terminal and a real headless browser); not tested with students |
| Not required: chatbot, multilingual, document management, custom interface, mobile app | None built. The phone page is an optional extra; the terminal is the deliverable | | |
