# Dataset plan: passage -> summary + diagnostic MCQs with misconception-tagged distractors (Indian Class 6-10 science and social studies, built in one day)

Research date: 2026-11-13. About 15 search/fetch calls. Citation note: claims marked **[prior knowledge, not re-fetched]** come from well-known papers or licence pages that I did not open again in this session. The report writer should either verify them or keep the flag. Every other claim is cited to a page that came back in this session's searches.

## 1. How many examples does a sub-1B model need for a narrow structured generation task, and does diversity beat volume?

### Takeaway
No paper I found measures this exact setting (a sub-1B model, a few thousand examples, a structured JSON task). The closest evidence (LIMA, s1, LIMO, Deita, and studies of small-model distillation) all point the same way: roughly 1k-3k carefully chosen, diverse, high-quality examples are enough to teach format and behaviour. Small students also learn better from shorter, simpler teacher outputs than from long ones. So ~2,000 well-filtered, topic-diverse examples is a reasonable target. Diversity across topics, misconception types and passage styles matters more than adding near-duplicate volume.

### Cited Findings
- On SLMs trained on TinyStories, varying dataset size and duplication rate showed that "training data quality plays a more significant role in the overall performance of SLMs". This is a pretraining study, not a fine-tuning one. — [Sajith & Kathala, arXiv 2411.15821](https://arxiv.org/abs/2411.15821)
- A CIKM 2025 SmaLLEXT workshop paper describes the pipeline this project would use: a teacher model generates data, rule-based validators filter it, and a compact student is fine-tuned by distillation. It notes that conventional approaches "require thousands of labeled examples". I did not confirm its exact counts. — [CEUR-WS Vol-4200 keynote](https://ceur-ws.org/Vol-4200/keynote2.pdf)
- A 2026 paper, "The Quality-Utility Paradox", reports that high-reward traces from strong models are not always the most useful data for small models. I only saw an aggregator summary and did not verify it on arXiv. — [deeppaper summary of arXiv 2606.16152](https://arxiv.deeppaper.ai/papers/2606.16152v1)
- LIMA: 1,000 curated prompt/response pairs were enough to align a 65B model's output style ("superficial alignment hypothesis"), showing that quality and diversity can substitute for volume. **[prior knowledge, not re-fetched]** — [arXiv 2305.11206](https://arxiv.org/abs/2305.11206)
- s1 (about 1,000 curated reasoning examples) and LIMO (about 800 examples) chose small sets for difficulty, diversity and quality, and they beat much larger SFT sets on reasoning. These results are for 32B students. **[prior knowledge, not re-fetched]** — [s1, arXiv 2501.19393](https://arxiv.org/abs/2501.19393); [LIMO, arXiv 2502.03387](https://arxiv.org/abs/2502.03387)
- "Small Models Struggle to Learn from Strong Reasoners" (Feb 2025) found that students of about 3B parameters or fewer do not reliably benefit from long chain-of-thought or from distillation off the strongest teachers. Shorter CoT, or a mix of long and short ("Mix Distillation"), worked better. **[prior knowledge, not re-fetched]** — [arXiv 2502.12143](https://arxiv.org/abs/2502.12143)
- Deita selected instruction data by complexity, quality and diversity scores. About 6k selected examples matched or beat training on far larger pools. **[prior knowledge, not re-fetched]** — [arXiv 2312.15685](https://arxiv.org/abs/2312.15685)

### Inferences
- For Qwen3-0.6B (the repo's current base, per the latest commit), the hard parts of this task are output-schema adherence and passage-grounded distractor writing, not deep reasoning. Format usually locks in within a few hundred examples. More examples mainly buy topic and misconception coverage. Target ~2,000 accepted training examples, with ~300 held out.
- Keep teacher outputs short. Do not train the 0.6B student on long teacher "thinking". Train it on the final JSON, with at most a one-line rationale per distractor. This follows the Small-Models-Struggle finding.
- Prefer diversity: spread the ~2,000 examples across roughly 150-250 NCERT-aligned topics × 2 subjects × 5 grades, with several passage styles (expository, narrative/historical, data/table description). Cap examples per topic at about 10-15 rather than generating 50 per topic.
- A practical stopping rule: train at 500, 1,000 and 2,000 examples and plot validation schema-validity and judge scores. If the curve flattens between 1k and 2k, spend the rest of the day on diversity and filtering, not volume.

### Gaps
- I found no 2024-2026 paper that measures data-size scaling for sub-1B models on structured educational generation (MCQ/JSON). The numbers above are extrapolated from larger-model or pretraining studies.
- I could not verify the 2026 "Quality-Utility Paradox" paper from its primary source.

## 2. Passage sources and licences usable in a public GitHub repo

### Takeaway
Use permissively licensed real text (OpenStax CC BY, FineWeb-Edu ODC-By, Simple English Wikipedia CC BY-SA, ARC CC BY-SA) plus teacher-written synthetic passages on NCERT syllabus topics. Do not redistribute NCERT textbook text. NCERT allows personal and reference use but prohibits republication. Training on NCERT text for a non-commercial hackathon is legally untested; the safe route is to use NCERT only as a topic list and syllabus outline. SciQ is non-commercial (CC BY-NC 3.0). OpenBookQA's licence is unclear.

### Cited Findings
- **NCERT:** NCERT's textbook page says copies may be downloaded and used as textbooks or for reference, but republication is strictly prohibited, and hosting the books on a website is barred. (This is from the search summary; the direct fetch of ncert.nic.in/textbook.php failed with a socket error.) — [search summary citing NCERT pages; NCERT press release](https://ncert.nic.in/pdf/announcement/notices/NCERT_Press_Release_book_sst.pdf)
- A June 2026 NCERT notice states that "unauthorised printing, reproduction, distribution and digital circulation" is punishable under the Copyright Act, 1957. Permission requests go to the Publication Division (secy.ncert@nic.in), and there is no standard licence form. — [Careers360](https://news.careers360.com/ncert-warns-publishers-against-copyright-infringement-of-school-textbooks-educational-materials); [NewsOnAir](https://newsonair.gov.in/the-ncert-issues-advisory-warning-against-copyright-infringement)
- **SciQ:** CC BY-NC 3.0 Unported. Most questions include a "support" paragraph that gives evidence for the correct answer. — [allenai/sciq dataset card](https://huggingface.co/datasets/allenai/sciq/blob/main/README.md); [BigBio SciQ](https://huggingface.co/datasets/bigbio/sciq/blob/main/README.md)
- **ARC (ai2_arc):** the card metadata says cc-by-sa-4.0, but an older dataset_infos.json has an empty licence field. — [ai2_arc README](https://huggingface.co/datasets/allenai/ai2_arc/blob/main/README.md?code=true); [dataset_infos.json](https://huggingface.co/datasets/allenai/ai2_arc/blob/refs%2Fpr%2F1/dataset_infos.json)
- **OpenBookQA:** the current README lists the licence as "unknown". An HF discussion notes that the GitHub repo's licence covers the code but not the data. Treat it as unverified. — [openbookqa README](https://huggingface.co/datasets/allenai/openbookqa/blame/main/README.md); [discussion #7](https://huggingface.co/datasets/allenai/openbookqa/discussions/7)
- **FineWeb-Edu:** ODC-By 1.0 (attribution, and subject to Common Crawl terms of use). It is web text filtered by an educational-quality classifier. **[prior knowledge, not re-fetched; the search returned nothing]** — [HuggingFaceFW/fineweb-edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu)
- **OpenStax:** textbooks are CC BY 4.0 (some titles are CC BY-NC-SA, so check each book). The US middle and high school science content (e.g. Biology, Chemistry: Atoms First, Physics) maps reasonably well to Class 9-10. **[prior knowledge, not re-fetched]** — [OpenStax licensing](https://openstax.org/license)
- **Simple English Wikipedia:** CC BY-SA 4.0. Derivatives must be ShareAlike, which matters if passages are redistributed in the repo. **[prior knowledge, not re-fetched]** — [Wikipedia copyright](https://simple.wikipedia.org/wiki/Wikipedia:Copyrights)
- **CK-12:** FlexBooks have mostly been CC BY-NC 3.0 (non-commercial) with additional CK-12 terms. **[prior knowledge, not re-fetched; verify]** — [CK-12 terms](https://www.ck12.org/about/terms-of-use/)

### Inferences
- **Recommended mix (about 2,300 passages before filtering):**
  - ~50% teacher-written synthetic passages (120-250 words) generated from an NCERT topic list. Chapter titles and learning outcomes are facts and syllabus structure, not copied expression. Synthetic passages are the only scalable source of India-specific social studies content: Indian history, the Constitution, Indian geography, the economy.
  - ~25% OpenStax / Simple Wikipedia excerpts, chunked and kept with attribution.
  - ~15% FineWeb-Edu passages filtered by keyword to science and social-studies topics at a school reading level.
  - ~10% SciQ support paragraphs and ARC-style science text. Mark SciQ-derived rows as CC BY-NC and keep them in a separate shard, so the repo's licence stays clean if it is ever reused commercially.
- **Synthetic vs real text.** Synthetic passages are easy to align to the NCERT syllabus, controllable in reading level and length, carry no licence risk, and work for social studies. Their downsides are hallucination risk (especially dates and names in history), stylistic homogeneity (a 0.6B student may overfit to the teacher's prose), and a test distribution that differs from what users will actually paste in (OCR'd textbook pages, notes). Real text has varied style, realistic noise and verified facts, but it has licence constraints and a Western curriculum bias in OpenStax/SciQ.
- **Mitigation:** vary the persona and style prompt per synthetic passage (textbook, teacher's notes, story, newspaper-for-kids); fact-check passages with a second model; and include some noisy, real-world-like text such as short OCR-style or bullet-note passages.
- **Repo hygiene:** commit only generated passages and permissively licensed excerpts, with a `source` and `licence` field on every row. Never commit NCERT PDFs or verbatim NCERT text. For the hackathon demo, users can paste their own NCERT pages at inference time; that is personal or reference use and is not redistribution.
- Training on NCERT text for a non-commercial hackathon is not settled under Indian copyright law. I found no NCERT text-and-data-mining exception or licence. The low-risk option is to not train on verbatim NCERT text.

### Gaps
- I could not fetch the NCERT textbook page directly to quote its notice; the wording above comes from the search summary.
- I found no Indian legal guidance on whether ML training on copyrighted textbooks counts as fair dealing under s.52 of the Copyright Act, 1957.
- I did not re-fetch the licences for FineWeb-Edu, OpenStax, Simple Wikipedia or CK-12 in this session.

## 3. Misconception sources and how to compile a misconception library

### Takeaway
No ready-made, openly licensed misconception library exists for Indian Class 6-10 science or social studies. The fastest route is to have the teacher model draft a library of about 300-600 misconceptions keyed to NCERT topics, seeded from the published literature: AAAS/BSCS item-bank misconception statements (paraphrased, not copied), HBCSE papers, and standard science-misconception reviews. Then spot-check it by hand. Eedi data is maths-only, so it is useful as a schema reference but not as content.

### Cited Findings
- **AAAS Project 2061 item bank:** more than 1,000 free items built around specific misconceptions. It now lives at BSCS (assess.bscs.org/science), with the original terms of use kept. I could not read the terms text. — [BSCS Science Assessment](https://assess.bscs.org/science/); [AAAS news](https://www.aaas.org/news/aaas-testing-web-site-probes-students-misconceptions-about-science)
- Project 2061's approach emphasises "precise alignment of items to the science ideas being tested and the identification of students' misconceptions". — [AAAS](https://www.aaas.org/news/us-students-and-science-aaas-testing-gives-new-insight-what-they-know-and-their-misconceptions)
- **HBCSE:** Savita Ladage's slides on student misconceptions in chemistry describe diagnostic tests that combine recall questions with questions about unfamiliar chemical situations. — [HBCSE chemistry PDF](https://chem.hbcse.tifr.res.in/wp-content/uploads/2016/08/Students%E2%80%99-Misconceptions-in-chemistry.pdf)
- An arXiv survey of Indian secondary students' astronomy misconceptions exists. I did not read it, and the ID comes from a search snippet. — [arXiv 2406.12308](https://arxiv.org/html/2406.12308v1)
- A 2019 review counted 33 physics, 12 chemistry and 15 biology concepts that mainly cause misconceptions (not India-specific). — [JPII review](https://journal.unnes.ac.id/nju/jpii/article/download/18649/9371)
- **Eedi "Mining Misconceptions in Mathematics" (Kaggle):** the task was matching each distractor to a misconception description. The licence was not visible in search results. An HF re-upload claims Apache-2.0, but its provenance is unclear. — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions); [HF eedi_data](https://huggingface.co/datasets/Roy2358/eedi_data/blob/main/README.md)
- **Kaggle "MAP – Charting Student Math Misunderstandings" (2025):** more than 52,000 student explanations across 15 maths questions, grades 4-8, from Eedi and NAEP, with misconception codes. Top MAP@3 was above 0.94. — [The Learning Agency case study](https://the-learning-agency.com/the-cutting-ed/article/case-study-math-misconceptions-competition); [Crossley et al., AIME-Con 2026](https://aclanthology.org/2026.aimecon-main.33/)
- Kaggle competition data terms are set per competition and usually restrict use to the competition. — [Agile Scientific](https://agilescientific.com/blog/2021/1/18/openness-is-a-two-way-street)
- **Social studies:** I found no peer-reviewed Indian study of Class 6-10 social-science misconceptions. Results were news reports about textbook errors and anecdotal blogs. — [search: Taylor & Francis chapter on history teaching by rote](https://www.taylorfrancis.com/chapters/edit/10.4324/9780203204078-20/case-archaeology-informal-school-curricula-india-neelima-dahiya)

### Inferences
- **Library schema (one JSON row per misconception):**
  ```json
  {"id":"SCI-PHY-FORCE-003","subject":"science","strand":"physics","topic":"force_and_pressure",
   "ncert_grades":[8,9],"statement":"A moving object needs a continuous force to keep moving",
   "correct_conception":"An object keeps moving at constant velocity unless a net force acts (inertia)",
   "error_type":"overgeneralisation|everyday_language|surface_feature|confusion_of_terms|chronology|causal_simplification|scale",
   "trigger_cues":["push","keeps moving","stops"],"source":"literature:AAAS-paraphrase|HBCSE|teacher_generated",
   "confidence":"lit_supported|plausible"}
  ```
- **One-day compilation recipe (about 2 hours):**
  1. Take the NCERT chapter list for Classes 6-10 in science and social science as topic keys (titles only).
  2. Ask the teacher, per chapter, for 3-6 well-documented student misconceptions with an `error_type` and, for science, a literature hint.
  3. Deduplicate with embeddings.
  4. Hand-review about 10%.
  5. Mark science items whose concepts match AAAS/HBCSE/review topics as `lit_supported`; mark the rest, including all social studies, as `plausible`.
- **Social studies error types differ from science:** chronology/anachronism, presentism, conflating institutions (Parliament vs Supreme Court), map/scale and direction errors, single-cause explanations, and confusing similar terms (e.g. monsoon vs rainfall, federal vs unitary). Generate these from a taxonomy rather than from literature, and label them `plausible`.
- Do not copy AAAS item text into the repo until the BSCS terms are read. Paraphrased misconception statements are ideas, not expression, so they are lower risk.

### Gaps
- I could not read the AAAS/BSCS terms of use or the licence text for either Eedi Kaggle competition.
- I did not locate HBCSE's published diagnostic-test item banks (e.g. its "Std VIII" studies) or their reuse terms.
- I found no concept inventories aligned to the Indian curriculum.

## 4. Teacher prompt design and teacher model choice and cost

### Takeaway
2024-2026 evidence shows LLM distractors are plausible but often fail to match real student errors. The design that helps is to have the teacher solve first, name a specific misconception, and only then write the distractor that misconception would produce, with an explanation per option. Overgenerate (e.g. 5-6 distractors) and keep the best 3. At 2026 list prices, ~2,500 passages × ~1,500 output tokens costs roughly $2 on DeepSeek, about $40 on Gemini 3.5 Flash, about $70 on GPT-5.4, and about $120 on Claude Opus-class models, before batch discounts. Pricing sources are aggregators and disagree.

### Cited Findings
- LLM distractors approach human ones in validity but "do not necessarily reflect common errors or misconceptions among real students". — [Feng et al., arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Overgenerate-and-rank improves distractors, but they still trail human-authored ones on reflecting misconceptions. — [Scarlatos et al., arXiv 2405.05144](https://arxiv.org/html/2405.05144v2)
- LLM-assigned probabilities correlate moderately with how often students choose each distractor. — [arXiv 2502.15140](https://arxiv.org/abs/2502.15140)
- A pairwise ranker trained on which distractor students prefer gives more plausible distractors and higher item discrimination. — [Lee, Kim & Jo, arXiv 2501.13125](https://arxiv.org/html/2501.13125v3)
- Grounding distractor generation in misconceptions drawn from concept maps was assessed with experts and students. — [arXiv 2505.02850](https://arxiv.org/html/2505.02850v1)
- LLM reasoning traces for distractor generation typically solve the problem correctly first, then articulate and simulate several possible misconceptions. — [Zengaffinen et al., arXiv 2603.15547](https://arxiv.org/html/2603.15547v1)
- **Pricing (2026 aggregators; verify on vendor pages):** GPT-5 nano $0.05/$0.40 per M input/output; GPT-5.4 $2.50/$15; Gemini 3.5 Flash $1.50/$9; Gemini 3.1 Flash-Lite $0.25/$1.50; DeepSeek V3.2 $0.14/$0.28; Claude Opus 4.8 $5/$25; Claude Fable 5 $10/$50. Sources conflict on model names and dates. — [BenchLM pricing](https://benchlm.ai/llm-pricing); [fungies.io 2026 comparison](https://fungies.io/llm-api-pricing-comparison-2026-openai-claude-gemini-deepseek/); [CloudZero](https://www.cloudzero.com/blog/llm-api-pricing-comparison/)

### Inferences
- **Prompt structure (one call per passage, structured JSON output):**
  1. **Persona:** an experienced CBSE Class {g} {subject} teacher who writes diagnostic (not summative) items, together with a misconception researcher.
  2. **Inputs:** the passage, grade, subject, and the top 5-8 misconceptions retrieved from the library for this topic (by embedding similarity).
  3. **Steps, in this order:**
     - (a) a summary of 3-5 sentences at the grade's reading level, using only passage facts;
     - (b) select 2-3 testable key ideas, each with the passage sentence that supports it (quote the span);
     - (c) for each idea, write the stem and the correct answer, and cite the supporting span;
     - (d) for each distractor, *first* name the misconception id or a new misconception statement and the error_type, *then* write the distractor that a student holding that misconception would choose;
     - (e) give a one-sentence explanation for every option (why right, or what misconception leads there and what the correct idea is);
     - (f) self-check: is any distractor also defensible from the passage? Is the answer guessable without the passage?
  4. **Constraints:** 4 options; options of similar length and grammatical form; no "all/none of the above"; no negated stems; Indian context and units (₹, km, Indian place names); the answer position is randomised afterwards in code, not by the model.
- **Student training target:** drop the teacher's (b) and (f) scratch work. Keep the summary and items, a `misconception_id`/`misconception` per distractor, and short explanations. This keeps student outputs short, in line with the Small-Models-Struggle evidence.
- **Overgenerate:** ask for 5 candidate distractors per item and let the judge pass keep the 3 most plausible, non-overlapping ones (overgenerate-and-rank).
- **Cost arithmetic (assumptions: ~2,000 input tokens per call for system prompt, passage and misconception list; 1,500 output tokens; 2,500 calls → 5M input / 3.75M output):**
  - DeepSeek V3.2: ≈ $0.7 + $1.05 ≈ **$2**
  - Gemini 3.1 Flash-Lite: ≈ $1.25 + $5.6 ≈ **$7**
  - Gemini 3.5 Flash: ≈ $7.5 + $33.75 ≈ **$41**
  - GPT-5.4: ≈ $12.5 + $56 ≈ **$69**
  - Claude Opus 4.8: ≈ $25 + $94 ≈ **$119**
  - Add about 30-50% for the passage-generation pass (synthetic passages of ~300 output tokens each, which is small) and the judge pass (about 2,500 × 2,500 input + 300 output). Prompt caching of the system prompt and batch APIs (commonly about 50% off) reduce totals.
  - The whole dataset fits in roughly $10-$250 depending on the teacher.
- **Model choice:** use one strong frontier model as the generator for the highest-value part (distractor and misconception writing). Optionally use a *different-family* model as judge, which reduces self-preference bias. DeepSeek works as a cheap second opinion or for passage generation. For a public repo, check each provider's terms on using outputs to train models; OpenAI, Anthropic and Google have historically restricted training *competing* models, and a 0.6B tutor is generally not that, but verify.
- **Throughput:** 2,500 calls at about 10-30 parallel requests finish in under an hour on most providers' standard tiers, so the "one day" budget is dominated by prompt iteration and review, not generation.

### Gaps
- I did not fetch the official 2026 vendor pricing pages. Aggregator figures conflict, and some model names (e.g. "Claude Opus 5.5", "GPT-6") could not be cross-checked.
- I found no 2025-2026 head-to-head benchmark of frontier teachers on misconception-aligned distractor quality for science or social studies.
- I did not verify provider ToS clauses on using outputs for training in this session.

## 5. Automatic filtering pipeline and typical rejection rates

### Takeaway
Use a layered filter: (1) schema and rules, (2) answerability, where the key must be supported by the passage (NLI and/or an LLM answering with the passage), (3) uniqueness, where no distractor is also entailed, (4) a closed-book guessability check, (5) an LLM-judge rubric, and (6) MinHash dedup plus a reading-level check. I found no published rejection-rate figures for this exact pipeline. Plan for roughly 20-40% loss and overgenerate by about 1.4×.

### Cited Findings
- MQAG measures answerability as the effective number of options (the entropy of the answer distribution) and rejects questions above a threshold, because "not all generated questions are of high quality". — [MQAG, arXiv 2301.12307](https://arxiv.org/pdf/2301.12307)
- ORQA rejects questions that two LLMs answer correctly closed-book, treating them as too easy, then aligns to human annotations. — [ORQA, arXiv 2609.12366](https://arxiv.org/pdf/2609.12366)
- An LLM failing to answer an item signals quality issues. This method identified nearly 30% of the items later rejected using student response data, which is a recall figure, not a rejection rate. — [VitalSource research](https://research.vitalsource.com/publications/exploring-large-language-models-for-evaluating-automatically-generated-questions)
- Rule-based MCQ filters drop items for poor grammar, a wrong predicted answer, distractors of the wrong entity type, duplicates, or more than one correct option. — [arXiv 2309.15004](https://arxiv.org/pdf/2309.15004)
- Exam-generation work says raw generation "is insufficient" and applies filters for length, incorrectness and self-containment. — [arXiv 2405.13622](https://arxiv.org/pdf/2405.13622)

### Inferences
- **Pipeline (in order; cheapest first):**
  1. **Schema/rules:** valid JSON; exactly 4 unique options; key ∈ options; option length ratio ≤ 2.5×; no "all/none of the above"; summary 40-120 words; the cited evidence span is a literal substring of the passage.
  2. **Answerability (key supported):** run an NLI cross-encoder, e.g. `cross-encoder/nli-deberta-v3-base` (or `-large`), with premise = the evidence span or full passage and hypothesis = the stem + key rewritten as a statement. Require P(entail) ≥ 0.7. Also have a small LLM answer the MCQ *with* the passage, and reject if it disagrees with the key.
  3. **Distractor-also-correct:** run the same NLI on each distractor statement; reject or regenerate the item if any distractor has P(entail) ≥ 0.5. Also reject if the LLM's answer distribution is near-uniform between the key and one distractor (an MQAG-style entropy check).
  4. **Guessability (closed-book):** answer without the passage. Items that a small model gets right closed-book are not necessarily bad, since the questions are diagnostic, but flag items where options give away the answer (e.g. the key is longest, or it repeats stem words).
  5. **LLM-judge rubric** (different-family model, 1-5 per criterion, keep if all ≥ 3 and mean ≥ 4):
     - grade appropriateness
     - factual correctness of the passage and summary
     - stem clarity
     - distractor plausibility
     - distractor ↔ misconception match (does a student holding misconception X plausibly pick this?)
     - explanation correctness
     - Indian-context fit
  6. **Dedup:** MinHash LSH (e.g. `datasketch`, 5-gram shingles, Jaccard ≥ 0.7) on passages and on stems. Also use embedding near-dup removal (cosine ≥ 0.92) for synthetic passages, which tend to paraphrase each other.
  7. **Reading level:** Flesch-Kincaid grade (`textstat`) within about grade ±2 of the target. Use loose bounds, because FK is calibrated on US English.
- **Rough loss budget (my estimate, not sourced):** rules 3-8%; answerability 5-15%; distractor-also-correct 5-15%; judge 10-20%. The cumulative loss is about 25-40%, so generate about 3,000-3,300 candidate items/passages to keep about 2,000-2,300.
- Log every rejection reason. The rejection-reason distribution is itself a useful hackathon artefact and helps tune prompts within the day.
- Hand-review a stratified sample of about 100 accepted and 50 rejected items to estimate filter precision and recall.

### Gaps
- I found no published rejection rates for answerability or NLI filtering of LLM-generated school MCQs; the percentages above are estimates.
- I did not verify current NLI cross-encoder model IDs or benchmark scores on Hugging Face in this session.

## 6. Keeping a held-out evaluation set clean

### Takeaway
Split by topic (chapter), not by example. Keep held-out passages from separate sources and prompts. Dedup across splits with MinHash and embeddings before any training.

### Cited Findings
- I found no source specific to this question in this session. The general practice of decontaminating with n-gram/MinHash overlap is described in the filtering papers above, e.g. duplicate removal in [arXiv 2309.15004](https://arxiv.org/pdf/2309.15004).

### Inferences
- **Topic-disjoint split:** before generating anything, set aside about 10-15% of NCERT chapters per subject and grade (e.g. 1-2 chapters per class per subject) as eval-only. No training passages, synthetic or real, may be generated or retrieved for those chapters.
- **Source-disjoint split:** also hold out one real-text source slice (e.g. specific OpenStax sections or a FineWeb-Edu shard) to test generalisation to non-synthetic prose. The repo already contains `data/passages/eval/` and `results/eval_qwen3_base/` from git status; reuse these as the frozen eval and record their hashes.
- **Misconception leakage:** misconceptions can recur in both splits, since that is the skill being tested. Also track a held-out subset of about 15% of library misconception ids that never appear in training, to measure generalisation to unseen misconceptions.
- **Decontamination:** MinHash (Jaccard ≥ 0.5 at 5-grams, stricter than within-train dedup) and embedding cosine ≥ 0.85 between every train passage or stem and every eval passage or stem. Drop the *train* side on a hit.
- **Generation hygiene:** generate eval items with a different teacher prompt seed and, ideally, a different teacher model than the training data. That keeps the student from being rewarded for imitating one teacher's stylistic tics.
- **Human gold:** hand-check the eval set (about 150-300 items) for correctness. It is small enough to review in 1-2 hours and makes it the trustworthy anchor.
- Freeze the eval set (commit plus a SHA256 manifest) before looking at any training results.

### Gaps
- I found no 2025-2026 paper on leakage control for synthetic educational QA datasets specifically.
