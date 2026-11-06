# Harvest 04: quiz generation and validation methods

Prepared 2026-11-04 for the Namma AI Problem 1 PoC (live event 14 Nov 2026).

## How this was gathered

Firecrawl ran out of credits partway through and was dropped, per the coordinator's relay of your instruction. The rest used `curl` to stdout and WebSearch. Nothing was cloned, installed or run. Licences come from each repo's root licence file at the pinned SHA, reading only its opening lines. "No licence" means none of the common filenames exists at the repo root.

**What remains unread** is listed at the end of this file.

**Bottom line on reuse:** every check below is simple enough to write in-house from paper-level rules, so licences block nothing. Directly reusable permissive code is small: the Pi 5 normaliser, span and empty-output logic, and a syllable counter. **No good reusable non-LLM question generator was found**, so the fallback is ours to build.

## Findings that change the plan

1. **The Pi 5 "deterministic validator" is one rule.** It treats a response holding only citation markers and no answer text as an abstention. The authors say this re-routes malformed outputs and does not reduce substantive false claims. It is not evidence for a broad validator.
2. **An answer appearing in the passage does not show it is right.** The span check matched 96% of 7B answers to *unanswerable* questions, the same rate as for correct answers (Table 5). It catches invented answers, but not a real phrase that fails to answer the question.
3. **A strict span check can reject good answers from small models.** Only 56% (1.5B) and 36-43% (3B) of correct answers matched a passage span, partly because small models answer verbosely (median 12 answer tokens for 3B, 2 for 7B). Ask for answers of 5 words or fewer, and measure the rejection rate on our data before making this a hard failure.
4. **Qwen2.5 1.5B is a weak fallback on this evidence.** It was 27% correct against 75% for 3B, with 30% empty outputs (llama.cpp, Q4_K_M, citation-style RAG prompt, 64-token limit). This is a different task from ours, so test early; it is a warning, not a verdict.
5. **Memory in that study may not transfer.** `results_v2/final_summary.json` records llama-server peak RSS of about 6.5 GB (1.5B), 9.6 GB (3B, k=3) and 13.9 GB (7B) on a 16 GB Pi, with an in-memory prompt cache on. The paper does not break down why it grew. ExecuTorch will differ, so measure peak RSS ourselves, and check our Pi's RAM.
6. **L2Q's 120/120 pass rate will not transfer.** It used Qwen2.5-14B on an NVIDIA A100 with llama.cpp grammar-constrained JSON. Unless `llama_main` can constrain output (another harvest should confirm), expect many more JSON failures. Budget for tolerant parsing and retries.
7. **L2Q's QC is not purely deterministic in its code.** The notebook also defines an LLM verifier for unique-correct checking (cell 12, L226-296). Whether it ran in the published sweep was not traced. Its deterministic rules are still what we want.
8. **Generate-Then-Validate cannot be copied as published.** It generates 200 candidates per objective, and its strongest step needs next-token probabilities. Syntactic filtering alone kept 73.7%. The usable idea is to over-generate a little (for example 6-8 candidates to keep 3 or more; our number) and filter. No code release was found.
9. **A high pass rate is not evidence of quality.** A review (arXiv 2610.04267) calculates that an always-negative detector would score 93.09% on the data behind SAQUET's 94.13% accuracy. Report pass rate alongside (a) a seeded-fault test showing each check fires and (b) human ratings of the items that passed.
10. **Flesch-style checks are English-only and crude.** Most metrics, including FKGL, correlated poorly with human judgement (arXiv 2508.19221; plain-language summaries). One search found no Kannada formula, which does not prove none exists. Use them as warnings. If passages may be in Kannada, that needs a decision (check 17).

## Check list, ordered by value for effort

Action: **HARD** = reject and retry, **WARN** = keep and show to the teacher, **FIX** = correct automatically.
† = our starting proposal, not a published value; tune on a small development set.
Effort: S = under 1 hour, M = 1-3 hours, L = half a day or more (our estimates).

Checks 1-20 need **Python standard library only** (`json`, `re`, `string`, `unicodedata`, `difflib`, `statistics`, `random`, `decimal`). None has been run yet. They should cost little beside inference; the Pi 5 paper calls its validator's time negligible.

| # | Check | Pass | Fail | Action | Basis | Effort |
|---|---|---|---|---|---|---|
| 1 | Parse and schema | Output parses as JSON (after trimming text outside the outermost braces) with all required keys and correct types | Parse error or missing key | HARD | L2Q hard QC; tolerant extraction also in its notebook cell 10 | S |
| 2 | Empty or degenerate output | Summary, stem, answer and explanation each hold word characters after stripping | Empty, punctuation or citation markers only, refusal text, or echoed prompt text† | HARD | Pi 5 validator, extended | S |
| 3 | Truncation | Last field complete and text ends in terminal punctuation† | Hit the token limit or stops mid-sentence | HARD | Ours | S |
| 4 | Single valid key (MCQ) | Exactly one correct label, mapping to an existing option | None, several, or a label outside the option set | HARD | L2Q | S |
| 5 | Options distinct (MCQ) | All options non-empty and different after canonicalising | Empty or duplicate option | HARD | L2Q; Generate-Then-Validate Table 1 | S |
| 6 | Banned option types (MCQ) | None present | "all/none of the above"; yes/no/true/false; option starting "both" or "neither" | HARD | Generate-Then-Validate Table 1. SAQUET F1: none-of-above .91-1.00, all-of-above .80-1.00 | S |
| 7 | Minimum lengths | Stem and explanation at least 10 characters | Shorter | HARD | Generate-Then-Validate Table 1. **Do not copy its 5-character option minimum:** it would reject valid answers such as "iron" or "1947" | S |
| 8 | Answer grounded in passage | Normalised answer is a whole-token span of the normalised passage, or at least 80%† of its content words appear in one sentence | Neither holds | WARN until rejection rate is measured, then HARD | Pi 5 span check; coverage fallback ours. See findings 2 and 3 | S |
| 9 | Numbers and names in the summary | Every number and mid-sentence capitalised term appears in the passage | Any that does not | HARD for numbers; WARN for names† | Ours; maps to QGEval Consistency | S |
| 10 | Summary length | 30-80 words† and under 40%† of passage length | Outside range, or copied from the passage (difflib ratio at or above 0.92 with a passage span†) | HARD for length; WARN for copying | Ours | S |
| 11 | Question count | At least 3 questions survive all HARD checks | Fewer | Retry, then no-model fallback | Problem statement | S |
| 12 | Near-duplicate questions | Pairwise stem similarity below 0.92 | Exact match or at or above 0.92 | HARD | L2Q threshold, `difflib` ratio confirmed in notebook | S |
| 13 | Option order and key position (MCQ) | Options shuffled; numeric options sorted | n/a | FIX | Shuffle from Generate-Then-Validate (position bias); order from IWF "lost sequence" (F1 .50-1.00) | S |
| 14 | Stem grounded in passage | At least 60%† of stem content words appear in the passage | Below threshold | WARN, later HARD | Ours; maps to QGEval Consistency | S |
| 15 | Evidence sentence | One sentence (or two adjacent†) holds the answer and at least 2† stem content words | No such sentence | WARN | Ours. Partial proxy for answerability, which QGEval found weak in generators | M |
| 16 | Numeric consistency | Plain numeric options differ by more than 1e-9; a number in the key also appears in the explanation; non-integer key has "about" or a rounding instruction in the stem | Equal values, key and explanation disagree, rounding unstated | HARD for equal; WARN for others | L2Q Dup and Rnd; key-explanation rule is in the notebook but not the paper. **Parse with `decimal`; do not use `eval`** (L2Q's expression evaluation is not needed at this level) | S |
| 17 | Readability | Over summary plus all questions (at least 100 words†): FKGL at or below passage FKGL + 1† and at or below 8†. Stem at most 20 words†; sentence at most 25 words† | Any limit exceeded | WARN | Flesch-Kincaid. For Kannada, keep only word limits. Python `\w` may split words at Kannada vowel signs, so test tokenising first | M |
| 18 | New-word rate | At most 15%† of content words in questions and summary are absent from the passage | Above threshold | WARN | Ours. No word list needed; serves grounding and weak readers together | S |
| 19 | Answer cues (MCQ) | Key not uniquely longest (second-longest at least 80% of its length); no key content word repeated in the stem | Either cue present | WARN | IWF "longest option" (F1 .60-1.00; 80% is one rater interpretation in SAQUET) and "word repeats" (F1 .53-1.00, exact match only here) | S |
| 20 | Wording flags | Stem not negative ("not", "except", "never", "least"); options free of absolutes and vague terms; no mid-stem blank; stem ends in "?" | Any present | WARN (exempt cloze from blank and "?" rules) | IWF. Negative .00-.91, fill-in-blank 1.00, absolute .00-.89, vague .00-1.00, so warnings only | S |

**Build order:** checks 1-13 first (about 1 day), then 14-20 (about half a day), writing hand-made bad items for each check as you go.

**Readability formulas (public):** FKGL = 0.39 x (words/sentences) + 11.8 x (syllables/words) - 15.59. Reading Ease = 206.835 - 1.015 x (words/sentences) - 84.6 x (syllables/words). Recalled from standard references, not fetched here. Do not apply them to single stems; a sentence or two is too short to be meaningful (our judgement).

### Needs more than the standard library

| Check | Dependency | Evidence | Recommendation |
|---|---|---|---|
| Entailment verification (NLI) | Torch-class runtime, DeBERTa-v3-base checkpoint | AUROC 0.50-0.64; median 0.8-4.4 s per check on Pi 5; cost 3-7 points of correct answers | **SKIP** |
| Answer-confidence filter | Next-token probabilities, plus inference time | Agreement kappa 0.67 to 0.91, retained items 6,043 to 2,856 (Phi-2 judged by Gemini) | Only if `llama_main` exposes probabilities |
| Self-answer check (re-ask model, compare with key) | No new library; one inference per question | Failing to solve an item does not prove a flaw; one two-model disagreement signal had 35.3% sensitivity (review 2610.04267) | Stretch goal, WARN only |
| Grammatical cues, logical cues, ambiguity, implausible distractors | spaCy, word vectors or transformer (SAQUET lists torch, transformers, spacy, openai and more) | F1 .00-.86 even with those tools | Human sheet |
| Multiple correct answers | Strong LLM | F1 .00-.46 even using GPT-4 in SAQUET | Human sheet |
| Learning-objective alignment | Log-probabilities, plus objectives we lack | 59% to 61% agreement | **SKIP** |

## No-model fallback (idea, standard library only)

Choose sentences holding a number, a capitalised term or a frequent content word, and blank that term, preferably at the end of the sentence. Take distractors from same-type terms elsewhere in the passage (numbers with numbers, names with names), so vocabulary stays familiar. Run the same checks, exempting cloze from check 20's blank rule, and label these items as fallback.

Limits: recall-level questions only, and a passage term used as a distractor could also be a defensible answer. Effort: M to L. The pipeline shape (pick answer, blank it, generate wrong answers) appears in the GPL `fighting41love/Question-Generation`, idea only.

## Human evaluation sheet (proposed, for 2 or more teachers)

Blind raters to the source and the validator result. A Frontiers 2026 title reports that AI assistance increased item-writing flaws through automation bias; only a search excerpt was seen.

| Step | Measure | Scale and rule | Source |
|---|---|---|---|
| 1 | Answer the item as a student, with "none of the above" added, before seeing the key | Compare with key; report kappa | Generate-Then-Validate Study 1 |
| 2 | Fluency, Clarity, Conciseness | 1-3 each | QGEval |
| 3 | Relevance, Consistency, Answerability, Answer Consistency, against the passage | 1-3 each | QGEval |
| 4 | Flaws our checks miss: ambiguous, implausible distractors, more than one correct, logical and grammatical cues, unfocused stem, gratuitous information | 0-1 flaws acceptable; 2 or more unacceptable | Tarrant et al. rubric, via Moore et al. |
| 5 | Fit for Class 6-8 weak readers: could a typical student read and understand this? | 1-3 | Ours |
| 6 | Summary: faithful, covers the main idea, easy to read | 1-3 each | Ours; adapted from QGEval |
| 7 | Use as is, after a small edit, or not at all | 3 options | Ours |

**Calibrate first.** QGEval's raters reached Krippendorff's alpha of only 0.18-0.56 in round one and 0.43-0.80 after review and discussion. Rate about 5 items† together, discuss, then proceed. For scale: Generate-Then-Validate used 7 teachers, 64 items and 30 minutes.

## Source table

Notice duty for every MIT item: keep the copyright line and permission notice in any copied code. arXiv `vN` URLs are version-fixed, so they act as pins for papers and ancillary files. Notebook lines are per cell, since notebooks have no stable file line numbers.

### Named targets

| Source | Item | What it does | Pinned URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| Shintani 2026, Lecture-to-Quiz | Two-level QC design (Sec. 3.1) | Hard checks reject and retry (`retry_max` = 3); warnings go to human review | https://arxiv.org/html/2603.08729v1#S3 | Paper: CC BY 4.0 | TAKE-IDEA | Validator structure; checks 1, 4, 5, 12, 16 | S |
| Shintani 2026 | Item validator, notebook cell 12 L155-200 (with helpers L8-52) | Empty question, key label, empty and duplicate options, fuzzy duplicates against earlier items | https://arxiv.org/src/2603.08729v1/anc/arxiv_dummy_entropy_pack/RUN_ALL_end_to_end_mcq_pipeline.ipynb | No licence text in notebook; no LICENSE in the visible listing; CC BY on the paper may not extend to it | TAKE-IDEA | Rewrite as checks 4, 5, 12 | S |
| Shintani 2026 | Run-level audit, same notebook, cell 13 L93-165 | Adds key-versus-explanation number mismatch and rounding flag | Same | Same | TAKE-IDEA | Check 16 | S |
| Shintani 2026 | Tolerant JSON extraction, cell 10 from L5; manifest, cell 14 L49 on | Pulls an object out of noisy output; records config, timing and checksums | Same | Same | TAKE-IDEA | Check 1; shape of our report | S |
| Shintani 2026 | LLM verifier, cell 12 L226-296 | Asks a model which options are correct | Same | Same | SKIP | Too costly on Pi for PoC | n/a |
| Feretzakis & Papaspyridis 2026, Pi 5 study | Findings (Secs. 4, 5.2, Table 5) | Validator, span-check and NLI results | https://arxiv.org/html/2610.33732v1#S5.SS2 | Paper: arXiv non-exclusive | TAKE-IDEA | Findings 1-5 | S |
| Same | Answer normaliser | Lowercase, drop punctuation and articles, collapse spaces. `string.punctuation` is ASCII only, so extend it for non-English text | https://github.com/securagenai/edge-rag-trust-mechanisms/blob/54c07b35f9121c5639459ecc5d313708d6bdcb17/device/nli_verify_v2.py#L35-L37 | MIT (LICENSE; (c) 2026 securagen.ai P.C.) | TAKE-CODE | Check 8. Copy only these lines; the module also holds NLI code | S |
| Same | Span check | Whole-token containment test of answer in passage | Same file #L56 | MIT | TAKE-CODE | Check 8 | S |
| Same | Empty-output rule | Strips citation markers and tests for nothing left | https://github.com/securagenai/edge-rag-trust-mechanisms/blob/54c07b35f9121c5639459ecc5d313708d6bdcb17/analysis/final_analysis.py#L11 | MIT | TAKE-CODE | Check 2 | S |
| Same | Peak memory logging | Reads server RSS per query with `psutil` (non-stdlib) | https://github.com/securagenai/edge-rag-trust-mechanisms/blob/54c07b35f9121c5639459ecc5d313708d6bdcb17/device/gen_v2.py#L29-L31 | MIT | TAKE-IDEA (stdlib `resource` or `/proc` may do; needs its own check) | Memory metric | S |
| Same | Network isolation and power method (Sec. 4; `device/run_v2.sh`, not opened) | Network namespace with loopback only; PMIC power sampled every 0.5 s | https://arxiv.org/html/2610.33732v1#S4 | Paper as above; repo MIT | TAKE-IDEA | Credible "really offline" demo | M |
| Same | NLI verifier | Entailment check over rewritten answers | https://github.com/securagenai/edge-rag-trust-mechanisms/blob/54c07b35f9121c5639459ecc5d313708d6bdcb17/device/nli_verify_v2.py | MIT | SKIP | Cite as the reason not to add NLI | n/a |
| Same | Derived SQuAD data in repo | Questions and per-query results | https://zenodo.org/records/23620709 | CC BY-SA 4.0 per Zenodo; not in the permissive list | SKIP | Do not ship | n/a |
| Wei, Stamper & Carvalho, LAK 2026 | Syntactic filter (Table 1) | Published exclusion list; kept 6,043 of 8,200 | https://arxiv.org/abs/2512.10110v2 ; https://dl.acm.org/doi/10.1145/3785022.3785100 | Paper: CC BY 4.0. No code found | TAKE-IDEA | Checks 5-7, minus the 5-character rule | S |
| Same | Over-generate then filter | Treats candidates as abundant, validates afterwards | Same, Sec. 3 | CC BY 4.0 | TAKE-IDEA | Small candidate budget, sized by measured Pi speed | S |
| Same | Answer confidence | Next-token probability at or above 0.9, with "none of the above" added | Same, Sec. 3.2.2 | CC BY 4.0 | TAKE-IDEA (stretch) | Only if probabilities are exposed | L |
| Same | Objective alignment | Relevance as a log-probability difference | Same, Sec. 3.2.3 | CC BY 4.0 | SKIP | Small gain; we lack objectives | n/a |
| Same | Teacher evaluation design | Teachers answer as students, then judge | Same, Sec. 4.1 | CC BY 4.0 | TAKE-IDEA | Human sheet step 1 | S |

### Item-writing flaws and rubrics

| Source | Item | What it does | Pinned URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| Moore et al. 2024, SAQUET | 19-criterion rubric, per-flaw F1 (Tables 1, 3) | Flaw definitions; 8 criteria by text matching, others by NLP or GPT-4 | https://arxiv.org/abs/2405.20529 | Paper licence not checked | TAKE-IDEA | Checks 6, 13, 19, 20; sheet step 4 | S |
| Same | Rule functions, `SAQUET.ipynb` cells 6, 8, 10, 12, 14, 16, 18, 20, 24, 38 (bodies not read) | None/all of the above, blank, true/false, absolute, longest, negative, repeats, sequence, vague | https://github.com/StevenJamesMoore/SAQUET/blob/7a6d8e484bfe6a877b02ab3d4cfb848dedc4bd8c/SAQUET.ipynb | **No licence file** | TAKE-IDEA | Read for keyword ideas; write our own | S |
| Moore et al. 2023 | Rule-based detector | Per-flaw rules; 91% of flaws detected against 79% for GPT-4, though it still uses pretrained models | https://github.com/StevenJamesMoore/ECTEL23/blob/acecb8864e13087a7d0982537cc2c86ee74f2180/IWF.ipynb ; https://arxiv.org/abs/2307.08161 | **No licence file** | TAKE-IDEA | Reference only | S |
| Moore & Diana 2026, review | Criterion map (Table 2) | Sorts flaws by detection route and F1 range; warns on accuracy denominators | https://arxiv.org/html/2610.04267v1 | Paper: CC BY 4.0 | TAKE-IDEA | Chose which flaws become checks | S |
| Fu et al. 2024, QGEval | 7 dimensions, 1-3 scoring guide (Table 7) | Human scale with worked examples | https://arxiv.org/html/2406.05707v2 | Paper licence not checked | TAKE-IDEA | Sheet steps 2-3; rater training | S |
| Same | Dataset and code | Annotated generated questions and metrics | https://github.com/WeipingFu/QGEval/tree/9ba901b69043e6ddf874ce8802352f9ac0d368d3 | **No licence file** | TAKE-IDEA | Do not redistribute; tuning use needs your call | M |
| Balepur et al. 2026, BenchMarker | LLM-judge toolkit | Flags contamination, shortcuts, writing errors | https://arxiv.org/abs/2602.06221 | Not checked | SKIP | Needs large LLM judges | n/a |

### Question and distractor generation

| Source | Item | What it does | Pinned URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| fighting41love | Question-Generation | Classifier picks answers, blanks them, then generates wrong answers; spaCy-tag features | https://github.com/fighting41love/Question-Generation/tree/cea66148f8502168008c891eba2bf84f3601505c | GPL-3.0 | TAKE-IDEA | Fallback pipeline shape; notebooks not opened | S |
| cristianoarbex | clozeQuestionGenerator | Script for Moodle cloze questionnaires; numpy and pandas; may be a format tool and not text-based generation (body not read) | https://github.com/cristianoarbex/clozeQuestionGenerator/blob/07d3ef93b73eb3dfee736d8029e986eb2cbdc055/clozeQuestionGenerator.py | GPL-3.0 | TAKE-IDEA (low) | Probably not useful | S |
| Ayushmansahoo098 | pdf-to-quiz-nlp | Described as offline TF-IDF and spaCy quiz maker; repo commits a `.venv` | https://github.com/Ayushmansahoo098/pdf-to-quiz-nlp/tree/954b2341942d15411cede69baa8d8046f81e05c1 | **No licence file** | TAKE-IDEA (low) | Only the TF-IDF answer-picking idea | S |
| Mbajwa | MCQ_Generator | Keyphrases plus sense2vec-style distractors; excerpt only | https://github.com/Michael-Mbajwa/MCQ_Generator/tree/125bcf4798c6d0aa08072963ba91dee3a4085315 | **No licence file** | TAKE-IDEA (low) | Pipeline shape only | S |
| INESC TEC | YAKE keyword extractor | Unsupervised single-document keywords; needs numpy, networkx, segtok, jellyfish | https://github.com/INESCTEC/yake/tree/f7944f645106d8c37c6999a1ba66d222f215a151 | AGPL-3.0 or commercial in LICENSE (package classifier says GPLv3; mismatch) | TAKE-IDEA | Frequency and position scoring idea for cloze answers | M |
| Vachev, Leaf | T5 question and distractor generator | Two fine-tuned T5 models plus sense2vec; RACE-trained distractors | https://github.com/KristiyanVachev/Leaf-Question-Generation/tree/0870a22ce73a87b28fdb53dec831d0cac694ba47 | MIT ((c) 2018 Kristiyan Vachev) | SKIP (heavy) | None | n/a |
| Golla, Questgen | T5 MCQ and boolean generator | Several T5 models plus sense2vec vectors | https://github.com/ramsrigouthamg/Questgen.ai/tree/edf8f6aa6c1ad5e803ce2b6adfac8825a3e5a553 | MIT ((c) 2020 Ramsri Goutham Golla) | SKIP (heavy) | None | n/a |
| Explosion | sense2vec | Phrase vectors for similar-word distractors | https://github.com/explosion/sense2vec/tree/72129b83ead7299df060df0e8ebc52df7766ae9a | MIT ((c) 2019-2023 ExplosionAI GmbH) | SKIP (heavy) | None | n/a |
| Chowdari | AutomatedQuestionGeneration-AQG- | T5, BART and OpenAI API scripts | https://github.com/Lohithchowdari/AutomatedQuestionGeneration-AQG-/tree/619f05bd65234aba81d90767a0dc1d9866789d5c | MIT ((c) 2025 Dupati Lohith Chowdari) | SKIP (heavy, online) | None | n/a |
| arXiv 1906.04980 | Unsupervised QA by cloze translation | Noun phrases or named entities become blanks (abstract only) | https://arxiv.org/abs/1906.04980v2 (version not checked) | Not checked | TAKE-IDEA | Fallback answer selection | S |
| arXiv 2410.04266 | CQG | WordNet siblings plus transformer ranking (abstract only) | https://arxiv.org/abs/2410.04266v1 | Not checked | TAKE-IDEA (low) | Sibling-word idea; WordNet is a dependency | M |
| arXiv 2004.09853 | Knowledge-driven distractors | Knowledge base plus learning-to-rank (abstract only) | https://arxiv.org/abs/2004.09853 | Not checked | SKIP | Too heavy | n/a |

### Readability

| Source | Item | What it does | Pinned URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| Lababidi | english-syllable | One rule-based `count` function, about 50 lines, imports only `re`. Accuracy not tested | https://github.com/lababidi/english-syllable/blob/098c78a52bb7f40fa112446f1b17011acdb1e6b8/english_syllable/__init__.py#L4-L52 | MIT-style permission text in LICENSE.txt ((c) 2014 Mahmoud Lababidi) | TAKE-CODE | Syllables for check 17; simplest option | S |
| Holtzscher | syllapy | Dictionary lookup with rule fallback; bundled CSV; no required dependency seen; Python 3.10 or later | https://github.com/mholtzscher/syllapy/blob/f8ab6cab87082537f5df564f2a2cae8065504780/syllapy/__init__.py#L25-L83 | MIT ((c) 2018 Michael Holtzscher). Bundled data's origin not checked | TAKE-CODE | Alternative if the rule-only version is too rough | S |
| Bansal et al. | textstat | Readability scores; requires pyphen, nltk, setuptools | https://github.com/textstat/textstat/tree/5679e7ccc0c2627bca1c0506eae1a7feb802a163 | MIT ((c) 2016 Shivam Bansal). Dependency licences not checked | TAKE-CODE, development machine only | Cross-check our FKGL; keep off the Pi | S |
| DiMascio | py-readability-metrics | Readability scores; requires nltk | https://github.com/cdimascio/py-readability-metrics/tree/296e958a460178f3f2e9ffe9fe1d2ffdfdb57ddf | MIT ((c) 2018 Carmine M DiMascio) | SKIP | textstat covers the cross-check | n/a |
| Flesch; Kincaid | FKGL and Reading Ease | Public formulas | n/a | Formula, not code | TAKE-IDEA | Check 17, in-house | S |
| arXiv 2508.19221 | Metrics versus human judgement | Most metrics correlate poorly, including FKGL | https://arxiv.org/abs/2508.19221 | Not checked | TAKE-IDEA | Reason for WARN-only | n/a |

## What remains unread

- **Licence text past the opening lines.** MIT and GPL identifications rest on headers; have someone read each file before copying code.
- **Function bodies** for SAQUET, ECTEL23, QGEval, YAKE, the GPL repos and all the T5 repos. Their tags rest on READMEs, imports, excerpts or search results.
- **Pi 5:** run scripts, `device/run_v2.sh` and `setup_pi.sh`. Only the cited lines and the summary JSON's memory and empty-rate fields were read.
- **L2Q:** topic planner and exports beyond their outlines, and seed-sweep outputs. Whether the LLM verifier ran in the sweep was not traced.
- **QGEval scoring guide:** only the Fluency and Clarity rows were retrieved. Fetch Table 7 before finalising the sheet.
- **Licences of papers marked "not checked"**, syllapy's bundled data, and textstat's dependencies (pyphen, nltk).
- **Not confirmed elsewhere:** whether `llama_main` offers constrained output or token probabilities. `vithonch/Question-Generation` appeared in search, but no commit feed could be read, so it is excluded.
