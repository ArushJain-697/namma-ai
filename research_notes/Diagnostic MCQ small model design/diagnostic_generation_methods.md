# Diagnostic MCQ and Misconception-Based Distractor Generation with (Small) Language Models

Scope note: Almost all of the strongest quantitative work comes from one research line (UMass Amherst ML4Ed group + Eedi) on one dataset (~1.4K–1.9K Eedi middle-school math MCQs, ages 10–13). The smallest model in any of these generation papers is 7–8B. No paper I found evaluates a ~0.6B model on *generating* diagnostic distractors; the only sub-1B evidence is (a) a 0.5B model *answering* MCQs wrongly in student-like ways and (b) a 0.5B model winning an efficiency prize for misconception *retrieval*. Everything about 0.6B generation below is inference.

## 1. Key papers, model sizes, and results (what works, with numbers)

### Takeaway
The methods that beat prompted GPT-4-class models all use an explicit textual error/misconception as an intermediate variable (error -> distractor), plus either a learned ranker, preference optimization (DPO) for error-distractor consistency, or a cycle-consistency filter. A fine-tuned 7–8B model with these tricks matches or edges out prompted GPT-4o on distractor-match metrics; but every paper reports that LLM distractors remain less plausible than human ones and that "anticipating real student errors" is the hard part.

### Cited Findings

**Feng et al., NAACL Findings 2024 — "Exploring Automated Distractor Generation for Math MCQs via LLMs" (baseline study)**
- Methods: kNN in-context (3 nearest MCQs as examples via MPNet embeddings), zero-shot CoT with GPT-4 (generate a student's erroneous steps, then the distractor), rule-based GPT-4 (choose from 44 hand-written error explanations), fine-tuned ChatGPT and Mistral-7B, and a sampling baseline — [arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Results (Exact / Partial / Proportional match vs human distractors, %): kNN-ChatGPT 10.95 / 73.85 / 38.52; CoT-GPT-4 4.24 / 65.02 / 30.39; Rule-based GPT-4 4.95 / 57.95 / 27.21; FT-ChatGPT 2.83 / 57.95 / 25.32; FT-Mistral-7B 1.77 / 52.30 / 22.50; sampling baseline 0.00 / 10.25 / 3.65. kNN with random (not nearest) examples dropped to 2.12 / 54.77 / 23.56 — [arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Human eval (1–5): validity LLM 3.28 vs human 3.99; plausibility LLM 2.68 vs human 3.72 (both significant; plausibility gap larger) — [arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Conclusion: LLMs "can generate some mathematically valid distractors" but are "less adept at anticipating common errors or misconceptions among real students" — [arXiv abstract](https://arxiv.org/abs/2404.02124)

**Scarlatos et al., BEA 2024 — Overgenerate-and-rank**
- Base LLM generates 10 candidates; a ranker (trained with DPO to predict how often real students select each distractor, using per-option selection rates from ~4,000 responses per question on ~1.4K Eedi MCQs) keeps the top 3. Baselines: random 3 of the pool ("Rand-3") and asking for exactly 3 ("Only-3") — [arXiv 2405.05144](https://arxiv.org/abs/2405.05144); [ACL Anthology 2024.bea-1.19](https://preview.aclanthology.org/setup/2024.bea-1.19)
- Ranking lifts a fine-tuned Mistral-7B "to a similar level as GPT-4 with CoT prompting"; teachers still preferred human-authored distractors — [arXiv 2405.05144](https://arxiv.org/abs/2405.05144)

**Fernandez, Scarlatos, Woodhead, Lan, EMNLP 2024 — DiVERT (Distractor generation with Variational Errors Represented as Text)**
- Dataset: 1,434 Eedi MCQs x 3 distractors (4,302 pairs), ~3,601 with teacher-written error labels; test 144 questions. Base model: MetaMath-Mistral 7B, with separate LLMs for error prior, distractor generator, and error identifier — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)
- Proportional match @10: DiVERT 63.24 vs GPT-4o kNN 60.19, GPT-4o zero-shot CoT 50.00, fine-tuned error-then-distractor CoT ("DisSearch-ED CoT") 62.83. At @3, GPT-4o kNN leads: 49.63 vs DiVERT 42.87 (authors attribute this to kNN copying from near-duplicate training questions). Note: abstract says "outperforms" GPT-4o; body is closer to "on par" — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)
- Ablation: removing variational training drops Prop@10 68.75 -> 64.81 — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)
- Human rating of error descriptions (1–5, two teachers, 180 errors): human 3.23, DiVERT 3.07 (n.s. vs human, p=0.36), GPT-4o 2.56 (significantly worse, p<0.01). Inter-annotator r = 0.33 — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)
- Text errors beat latent vectors: authors tried latent error vectors and found them uninterpretable and less effective — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)
- Base LLMs without supervised warm-up produce low-quality errors — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)

**Parikh et al., BEA 2025 — LookAlike (error-distractor consistency via DPO)**
- MetaMath-Mistral 7B + LoRA. Model overgenerates 3 distractors and 3 errors per training item each epoch; outputs not matching ground truth become DPO "rejected" samples (self-generated inconsistent outputs as negatives). Alternates SFT and DPO per epoch/batch rather than a combined loss; preference data recomputed each epoch — [arXiv 2505.01903](https://arxiv.org/html/2505.01903v2)
- Results (CV): distractor exact match / error accuracy (GPT-4o-mini judge): SFT 44.76 / 46.68; DiVERT 45.64 / 47.72; DPO-GT 51.44 / 57.02; LookAlike 51.56 / 57.18. Human-rated error consistency: ground truth 0.812, LookAlike 0.587, SFT 0.400 — [arXiv 2505.01903](https://arxiv.org/html/2505.01903v2)
- No GPT-4o baseline and no small-model (<7B) results; generalization to unseen topics untested — [arXiv 2505.01903](https://arxiv.org/html/2505.01903v2)

**Ross & Andreas, Oct 2025 — MISTAKE (cycle-consistency for modeling incorrect student thinking)**
- Llama-3.1-8B-Instruct + LoRA (rank 8), 4 iterations; Eedi data, 1,857 questions. Cycle: sample wrong answer -> infer misconception -> simulate answer from that misconception -> keep/upweight if simulated answer equals original; drop examples where simulated answer equals the correct answer — [arXiv 2510.11502](https://arxiv.org/html/2510.11502v1)
- Student simulation accuracy: Llama base 40.83% -> 44.43% (best variant); GPT-4.1 66.3%, GPT-4o 64.1%, GPT-3.5-turbo 40.6% — [arXiv 2510.11502](https://arxiv.org/html/2510.11502v1)
- Misconception inference MAP@25: 0.178 -> 0.204; GPT-4.1 0.271, GPT-4o 0.259 — [arXiv 2510.11502](https://arxiv.org/html/2510.11502v1)
- Distractor precision (validation): unconditional sampling 22.56% -> cycle-consistent simulation 37.14% (+64.6% rel.). The filter also helps frontier models: GPT-4o 0.427 -> 0.497, GPT-4.1 0.447 -> 0.490 — [arXiv 2510.11502](https://arxiv.org/html/2510.11502v1)

**"Can LLMs model incorrect student reasoning" line**
- Liu et al. 2023 ("Novice Learner and Expert Tutor"): LLMs answer correctly easily but struggle to (1) produce the wrong answer matching a specified misconception and (2) identify the misconception behind a given wrong answer — [arXiv 2310.02439](https://arxiv.org/pdf/2310.02439)
- Sonkar et al. 2024 ("LLM-based Cognitive Models of Students with Misconceptions"): models trained on misconception examples learn to replicate errors, but this training reduces correct problem-solving, especially where the misconception does not apply (synthetic algebra data, MalAlgoPy) — [arXiv 2410.12294](https://arxiv.org/abs/2410.12294v1)
- "Do LLMs Make Mistakes Like Students?" (2025): 3,202 four-option MCQs, 6 subjects, models 0.5B–72B (Qwen-2.5, LLaMA 3.1/3.2). When wrong, Qwen-0.5B picked the most common student distractor 51.6% of the time (index-based scoring) vs 59.3% for Qwen-72B; correlation of model option probabilities with student choice rates only 0.28–0.37. Authors suggest small models could be a cheap source of plausible distractors, paired with human review — [arXiv 2502.15140](https://arxiv.org/html/2502.15140v1)

**Concept-map-based generation (Scaria et al., 2025)**
- Hierarchical concept map of high-school physics (OpenStax-aligned) with common misconceptions listed per subtopic node; relevant map sections retrieved as structured context for question + distractor generation — [arXiv 2505.02850](https://arxiv.org/html/2505.02850v2)
- Expert review: 75.20% of items met all quality criteria vs ~37% for base-LLM and plain-RAG baselines. Student testing: guess success rate 28.05% vs 37.10% for baselines (lower = distractors more effective) — [arXiv 2505.02850 search summary](https://arxiv.org/abs/2505.02850v1)

**Eedi "Mining Misconceptions in Mathematics" Kaggle competition (2024–25)**
- Task: given question + distractor, rank misconception descriptions from a library; many test misconceptions unseen in training. Metric MAP@25 — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions); MAP@25 naming from [search summary of Eedi/Kaggle pages](https://eedi.com/blog/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- 1st (Raja Biswas): two-stage retrieve-and-rerank; retrieval with two Qwen models trained with LoRA + contrastive learning on ~10k synthetic + 1.8k real examples; Claude-generated short student rationales used in reranking — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- 2nd: CoT with Qwen2.5 to reason about each distractor, synthetic misconception augmentation, listwise reranking of top 25, post-training quantization — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- 3rd: Qwen2.5-14B embeddings for retrieval, Qwen2.5-32B reranker, QLoRA, plus a score scaling factor for unseen misconceptions — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- Efficiency prize 1st: Qwen2.5-0.5B base, prefix caching, synthetic data from Claude 3.5 / GPT-4o, SLERP merge of 6 models each trained ~2.5h on an RTX 4080. Efficiency 2nd: all-MiniLM-L6-v2 (22.7M params) un-finetuned; enriching misconceptions with Qwen2.5-32B-generated explanations "significantly improved retrieval" — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- Score levels (secondary sources, unverified): a silver-medal write-up reports public 0.54 / private 0.50 — [ecosyste.ms GitHub listing](https://awesome.ecosyste.ms/projects/github.com%2Fdaoyuanli2816%2Fkaggle-eedi-mining-misconceptions-in-mathematics-silver-medal); a 13th-place Qwen2.5-72B reranker reported private 0.561 / public 0.578 — [Kaggle discussion (via search snippet)](https://kaggle.com/c/eedi-mining-misconceptions-in-mathematics/discussion/551651). A Japanese write-up says a top team ran 14B/32B everywhere and 72B only on low-confidence cases — [zenn.dev](https://zenn.dev/mkj/articles/1f374627377474)

### Inferences
- The consistent recipe across DiVERT, LookAlike, MISTAKE and the concept-map paper: make the misconception an explicit text variable, generate the distractor *from* it, then check that the distractor and misconception actually correspond (ranker, DPO, or cycle check).
- For retrieval, a tiny model can be competitive (0.5B / 22M efficiency winners), but accuracy leaders used 14B–72B rerankers. For on-device 0.6B, retrieval from a curated library is the part most likely to work well; free-form misconception invention is the part least likely to.
- Prompted-only 7B models do poorly (FT-Mistral-7B 22.5% proportional vs 38.5% for kNN-ChatGPT); a 0.6B prompted model should be expected to be worse still unless given retrieved exemplars and a misconception list.

### Gaps
- No paper found evaluating 0.5–1B models on distractor *generation*; all generation results are 7B+.
- Exact 1st-place Kaggle MAP@25 not confirmed from a primary source.
- Model used in the concept-map paper not confirmed in my reading.
- All math results are on one dataset (Eedi, UK middle school); transfer to other subjects/curricula (e.g., Indian state syllabi) is untested.

## 2. What makes a distractor diagnostic; failure modes; automatic metrics

### Takeaway
A diagnostic distractor is one that a real student with a specific misconception would produce, mapped one-to-one to that misconception (so a wrong pick reveals the gap). The dominant LLM failure modes are inconsistency between stated error and distractor, generic or implausible errors, and template copying; surface-level item-writing cues (length, etc.) are a known concern but I found no strong quantitative source in this domain.

### Cited Findings
- Concept-map approach ties each wrong option to a specific misconception so a wrong answer identifies the student's gap — [arXiv 2505.02850](https://arxiv.org/html/2505.02850v2)
- Biggest DiVERT limitation: the distractor generator often produces distractors inconsistent with the stated error (e.g., "divides only the denominator" error yielding a non-matching value); some generated errors are implausible for students ("Subtracts instead of divides"); GPT-4o errors often are not what real students do and sometimes describe a correct method as an error — [arXiv 2406.19356](https://arxiv.org/html/2406.19356v2)
- LookAlike failure modes: inconsistent distractor (error "finds 13%" -> distractor 12 instead of the consistent 5.2); overly generic errors ("Does not understand the term factor"); DPO without SFT regularization makes errors longer and out-of-distribution; template overfitting (copies errors from similar training items) — [arXiv 2505.01903](https://arxiv.org/html/2505.01903v2)
- Valid-but-unrealistic distractors (e.g., 648 and 2163 for the cube root of 216); exact matches mostly come from near-duplicate in-context examples; invalid/repeated outputs occur; human distractors themselves sometimes weak placeholders, which corrupts match metrics — [arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Correct-answer leakage: MISTAKE explicitly drops simulated "errors" that equal the correct answer — [arXiv 2510.11502](https://arxiv.org/html/2510.11502v1)
- Item-writing-flaw rubrics (19-rule education rubric) used by LLM judges for auditing MCQs; repairs can introduce implausible distractors — [BenchMarker arXiv 2602.06221 (search summary)](https://www.arxiv.org/pdf/2602.06221)
- Automatic metrics in use:
  - Exact / Partial / Proportional match @k vs human distractors — [Feng et al.](https://arxiv.org/html/2404.02124v3), [DiVERT](https://arxiv.org/html/2406.19356v2)
  - Predicted student selection rate (ranker trained on real response distributions) — [Scarlatos 2024](https://arxiv.org/abs/2405.05144)
  - LLM-as-judge equivalence of error descriptions (GPT-4o-mini) — [LookAlike](https://arxiv.org/html/2505.01903v2)
  - MAP@25 for misconception retrieval/inference — [MISTAKE](https://arxiv.org/html/2510.11502v1)
  - Cycle consistency (misconception -> answer -> misconception) — [MISTAKE](https://arxiv.org/html/2510.11502v1)
  - Student-facing: guess success rate — [concept-map paper](https://arxiv.org/abs/2505.02850v1); LLM solve rate on items (GPT-4 solved kNN-distractor items 71% vs 72.5% human) — [Feng et al.](https://arxiv.org/html/2404.02124v3)
  - Correlation of model option probabilities with student choice rates — [arXiv 2502.15140](https://arxiv.org/html/2502.15140v1)

### Inferences
- For math, two programmatic checks catch the most common failures cheaply and deterministically: (1) distractor != correct answer (numerically, after normalization), and (2) re-executing the stated misconception (as a rule or simulated computation) reproduces the distractor value. Both map directly to the documented failure modes.
- "One misconception per option" plus "no duplicate misconception across options" should be enforced in the schema/validator, since generic errors that "fit many distractors" were a named failure.

### Gaps
- No quantitative source found on length cues / longest-option bias or "surface perturbation" distractors specifically for LLM-generated math MCQs. Treat as standard item-writing guidance, not evidence-backed here.
- Homogeneity (options of similar form/magnitude) not measured in any paper I read.

## 3. Staged pipeline vs single-call generation (quality and token cost)

### Takeaway
Evidence favours decomposition: error-first then distractor (DiVERT/LookAlike), overgenerate-then-rank, and multi-stage prompting all beat single-shot generation. But direct staged-vs-single comparisons are scarce and use large models; no source quantifies token cost.

### Cited Findings
- Multi-stage prompting (paraphrase -> keywords -> question -> distractors) beat single-prompt MCQ generation on automated distractor metrics with text-davinci-003 / GPT-4; human eval covered question quality, not distractors — [Maity et al. 2024, arXiv 2401.07098](https://arxiv.org/abs/2401.07098v1)
- Overgenerate-10-rank-to-3 improved alignment with human distractors over "Only-3" single-pass generation, bringing Mistral-7B to GPT-4-CoT level — [Scarlatos 2024](https://arxiv.org/abs/2405.05144)
- Error-then-distractor variants (DisSearch-ED CoT 62.83, DiVERT 63.24 Prop@10) outperform GPT-4o zero-shot CoT (50.00) — [DiVERT](https://arxiv.org/html/2406.19356v2)
- Cycle-consistency filtering raised distractor precision from 22.56% to 37.14% for an 8B model — [MISTAKE](https://arxiv.org/html/2510.11502v1)
- Kaggle winners universally used a two-stage retrieve -> rerank pipeline — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- Accuracy-cost tradeoff precedent: a top Kaggle team ran 14B/32B everywhere and 72B only on low-confidence cases — [zenn.dev](https://zenn.dev/mkj/articles/1f374627377474)

### Inferences
- For a 0.6B model, each stage should be a short, narrow call with a small output (one field or a short list), because small models degrade on long multi-part outputs. Staging also lets deterministic code (retrieval, numeric checks) replace model calls for whole stages, which is likely the biggest token saving.
- Overgenerate-and-rank is token-expensive (~3x candidates) but can be made cheap on-device if candidates are short numeric/text answers and ranking is done by a deterministic validator + misconception-library match rather than a second LLM.

### Gaps
- No study found that compares staged vs single-call for sub-1B models, or that reports token/latency cost of either approach. This needs local measurement.

## 4. JSON field ordering: reasoning/misconception before distractor?

### Takeaway
Within distractor research, every strong method conditions the distractor on the error text generated first (a structural "reasoning-first"), and the error->distractor ordering has empirical support versus direct generation. For JSON field order per se, evidence is weak and mixed; peer-reviewed work shows strict format constraints (JSON mode) can hurt reasoning.

### Cited Findings
- DiVERT/LookAlike generate distractor conditioned on error text; error-first fine-tuned CoT (62.83) and DiVERT (63.24) beat GPT-4o zero-shot CoT (50.00) at Prop@10 — [DiVERT](https://arxiv.org/html/2406.19356v2); LookAlike did not run an explicit error-first vs distractor-first ablation — [LookAlike](https://arxiv.org/html/2505.01903v2)
- In Feng et al., including feedback text as a reasoning step in kNN prompts slightly improved exact match (10.95 vs 9.54), though the comparison changes several factors at once — [arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Tam et al. (EMNLP 2024 Industry): format restrictions significantly degrade reasoning; stricter constraints hurt more; JSON mode worst in most reasoning tasks, followed by format-restricting instructions, then NL-then-convert, then plain NL. Tested on GPT-3.5-turbo, LLaMA-3-8B-Instruct, Gemma-2-9B-Instruct; classification tasks can benefit — [arXiv 2408.02442](https://arxiv.org/html/2408.02442v3); [ACL Anthology](https://aclanthology.org/2024.emnlp-industry.91.pdf)
- Under constrained decoding, keys are emitted in schema order, so an answer field placed before reasoning is committed before any reasoning — [DEV Community (practitioner)](https://dev.to/ji_ai/why-json-schema-field-order-breaks-structured-output-accuracy-2985)
- Practitioner experiment: reasoning-first schema helped strict accuracy under constrained decoding — [DEV Community](https://dev.to/vaibhav_mittal_ac22a2c5d6/structured-output-fixed-my-json-and-cut-math-accuracy-by-18-points-jm5); contradicted by a pydantic-evals experiment on GPT models finding minimal difference — [CO/AI](https://contact.getcoai.com/?p=72123)

### Inferences
- Order fields as: misconception (id/text) -> short "student working" -> distractor value -> feedback. This mirrors the error->distractor conditioning that the literature supports, and the "student working" step is what makes the distractor computable/checkable.
- Keep the JSON tiny per call (or generate in plain lines and parse) to limit the format-restriction penalty Tam et al. report, which is likely larger for a 0.6B model.

### Gaps
- No peer-reviewed study on JSON key ordering specifically for distractor generation or for sub-1B models.

## 5. Retrieved misconceptions (curated library) vs model-invented

### Takeaway
Mixed but leaning toward curated libraries when coverage is good: curated misconception context gave a large quality jump in the concept-map study, and retrieval is where small models are proven competitive. However, simply handing GPT-4 a short generic error list did not beat example-based prompting, because coverage was poor and LLMs are bad at picking which errors are common.

### Cited Findings
- Concept-map with per-node misconception lists: 75.20% items meeting all criteria vs ~37% for base LLM and plain RAG — [arXiv 2505.02850](https://arxiv.org/abs/2505.02850v1)
- Rule-based GPT-4 with 44 hand-written errors (4.95 exact) did not beat kNN (10.95) or CoT; selecting relevant errors only slightly beat random same-topic errors (4.95 vs 1.06 exact); authors blame incomplete coverage and LLMs' weak sense of which errors are common — [arXiv 2404.02124](https://arxiv.org/html/2404.02124v3)
- Model-invented errors: GPT-4o-invented error descriptions rated 2.56/5 vs human 3.23; a fine-tuned 7B (DiVERT) reached 3.07 — [DiVERT](https://arxiv.org/html/2406.19356v2)
- Retrieval works at small scale: Qwen2.5-0.5B ensemble and even un-finetuned MiniLM (22.7M) won efficiency prizes for misconception retrieval; enriching misconception descriptions with LLM-generated explanations significantly improved retrieval; unseen misconceptions needed score calibration — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)
- Synthetic training data (10k synthetic + 1.8k real) was used by the winner to cover the library — [Eedi blog](https://www.eedi.com/news/from-wrong-answers-to-real-insights-how-we-used-a-kaggle-challenge-to-map-student-misconceptions)

### Inferences
- Best design for a 0.6B model: a curated, topic-indexed misconception library (with a one-line explanation and ideally a worked example/rule per misconception) retrieved by embedding similarity to the concept, with the model only *applying* a chosen misconception to the question. Allow model-invented misconceptions only as a flagged fallback when library coverage is empty.
- The Feng et al. negative result is about coverage and selection, so the library should be fine-grained (per concept/subtopic) and carry real prevalence signals if available.

### Gaps
- No head-to-head study of library retrieval vs invention with the same generator on the same items.

## 6. Generating student-facing feedback per wrong option

### Takeaway
Feedback should be generated per (question, correct answer, distractor, misconception) tuple, scored on a rubric gated by correctness; DPO on rubric-annotated pairs improved correctness for a Llama-2 model.

### Cited Findings
- Scarlatos et al. 2024: inputs are question, correct answer, solution explanation, incorrect answer -> feedback message. Rubric with five binary aspects; score is 0 if feedback is incorrect, otherwise +0.2 per aspect met; aspects include Correct, Revealing (does not give away the answer), and Suggestion (actionable guidance). GPT-4 annotations build DPO preference pairs; Llama 2 base; reported significant gains in correctness and alignment. Code: github.com/umass-ml4ed/feedback-gen-dpo — [arXiv 2403.01304](https://arxiv.org/pdf/2403.01304); [NSF PAR](https://par.nsf.gov//servlets/purl/10520824)
- Hard negatives built from mismatched feedback (feedback for a different distractor) were used as extra rejected samples — [Moonlight review (secondary)](https://www.themoonlight.io/review/improving-the-validity-of-automatically-generated-feedback-via-reinforcement-learning)

### Inferences
- Since the misconception is already explicit per option, feedback for a 0.6B model can be templated: name the likely misconception, point to the step where it goes wrong, give a hint, do not state the correct answer. A deterministic check can enforce "not revealing" (feedback must not contain the correct value).
- Mismatched-feedback negatives map to a cheap validator: feedback must reference its own option's misconception, not another option's.

### Gaps
- Exact numeric gains from the feedback DPO paper were not extracted; no sub-1B feedback results found.

## Recommended design for a 0.6B model (inference, synthesized from above)

Stages (each a short call or deterministic step):
1. Concept selection (deterministic from curriculum / concept graph).
2. Misconception retrieval (deterministic embedding retrieval over curated library, top-k per concept; LLM-enriched descriptions). Optional 0.6B rerank.
3. Question + correct answer generation (small call), then verify correct answer by recomputation/solver where possible.
4. For each retrieved misconception: 0.6B call "apply this misconception to this question" -> student working -> distractor value. Overgenerate (e.g., 5–6 misconceptions) for 3 slots.
5. Validate per option: distractor != correct answer; distractors distinct; misconception distinct per option; cycle/recompute check (re-derive misconception from distractor, or execute misconception rule) — keep consistent ones, rank by library prevalence.
6. Feedback per kept option: short call or template; enforce "does not reveal correct answer".

Proposed JSON (field order = generation order; reasoning before values):

```json
{
  "concept_id": "frac.add.unlike_denominators",
  "stem": "What is 1/2 + 1/3?",
  "correct": { "working": "LCD 6: 3/6 + 2/6", "answer": "5/6" },
  "options": [
    {
      "misconception_id": "M-FRAC-ADD-ACROSS",
      "misconception": "Adds numerators and adds denominators",
      "student_working": "1+1=2, 2+3=5",
      "distractor": "2/5",
      "feedback": "It looks like you added the bottoms too. Denominators tell the size of the pieces; make them the same first.",
      "source": "library"
    }
  ],
  "checks": { "distractors_unique": true, "none_equal_correct": true, "misconceptions_unique": true, "cycle_consistent": [true] }
}
```

`source` is "library" or "invented" (invented gets flagged for review). `checks` is filled by code, not the model.
