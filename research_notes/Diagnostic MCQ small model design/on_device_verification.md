# On-device verification of model-generated MCQs (Raspberry Pi 5, CPU-only, offline)

Scope: cheap checks that a generated MCQ is safe to show a student. Three properties are checked: (1) the keyed answer is correct per the source passage, (2) no distractor is also correct, (3) the item is well-formed. Target: Pi 5 (4x Cortex-A76, 8 GB) running Qwen3-0.6B via ExecuTorch at the same time. The project's passages are short English Class-8 science texts (e.g. `data/passages/eval/passages.jsonl`, "phy_friction"), so English-only verifier models are acceptable.

Overall ranking, by value per millisecond (justified in the sections below):
1. **Pure-code structural checks.** Near-zero cost. Catch most well-formedness flaws and some key and distractor errors (duplicates, a distractor equal to the key, "all/none of the above", longest-option cue, a key not grounded in the passage).
2. **Small NLI cross-encoder (DeBERTa-v3-xsmall/small) run over passage sentences for every option.** The only cheap method that directly tests "distractor is also true per passage". Expected around 30-80 ms per pair on a Pi 5 (inferred, not measured).
3. **Independent extractive QA model (tinyroberta-squad2 / DistilBERT-SQuAD).** A second, architecturally different answerer for the key. About 80-200 ms per question (inferred).
4. **Blind answer-back with Qwen3-0.6B** (choose among the shuffled options without seeing the key). Cheap to implement but the slowest, because it needs a full prompt prefill. Its errors are correlated with the generator's. Use it only as a tie-breaker.
5. **Qwen3-0.6B as a free-form "judge" of item quality.** Not recommended. Measured agreement with humans is at chance (κ = 0.00 on writing flaws).

---

## 1. Small NLI / entailment cross-encoders: accuracy, size, ARM latency, runtimes, use for QA/distractor checking

### Takeaway
Small DeBERTa-v3 NLI cross-encoders (xsmall: 70.8M params; small: ~0.1B) reach about 87-88% MNLI-mismatched accuracy. They are the best cheap tool for checking that the key is entailed by the passage and that no distractor is. Prior work shows that NLI verification of QA answers works but is not reliable enough alone: it is best combined with QA-model confidence, and it fails on subtle wording. No published Pi 5 latency exists for these exact models. Extrapolating from a DistilBERT benchmark on a Raspberry Pi (~81 ms per forward pass with ExecuTorch+XNNPACK) suggests a few tens of ms per premise-hypothesis pair for xsmall.

### Cited Findings
- cross-encoder/nli-deberta-v3-xsmall: SNLI-test 91.64, MNLI-mismatched 87.77. 70.8M parameters. Labels in order `['contradiction','entailment','neutral']`. Fine-tuned from microsoft/deberta-v3-xsmall on SNLI+MultiNLI, Apache-2.0. The model page carries an ONNX tag. — [HF model card](https://huggingface.co/cross-encoder/nli-deberta-v3-xsmall)
- cross-encoder/nli-deberta-v3-small: SNLI-test 91.65, MNLI-mismatched 87.55 (no better than xsmall). About 0.1B params. ONNX tag present. — [HF model card](https://huggingface.co/cross-encoder/nli-deberta-v3-small)
- A two-class (entailment vs not-entailment) DeBERTa-v3-xsmall trained on MNLI+FEVER+ANLI+LingNLI reports 0.925 / 0.922 on MNLI matched/mismatched. This is not directly comparable to the 3-way numbers, but the binary setup matches the verification use case. — [HF: MoritzLaurer/DeBERTa-v3-xsmall-mnli-fever-anli-ling-binary](https://huggingface.co/MoritzLaurer/DeBERTa-v3-xsmall-mnli-fever-anli-ling-binary)
- tasksource/deberta-small-long-nli: built on deberta-v3-small and trained on a large multi-task NLI mix that oversamples long-context NLI (ConTRoL, doc-nli). It is suited to long-context NLI. An ONNX export exists as onnx-community/deberta-small-long-nli. Third-party listings give ~142M params and a 1680-token context; these are unverified against the official card. — [HF model card](https://huggingface.co/tasksource/deberta-small-long-nli); [Mixpeek listing of ONNX version](https://mixpeek.com/model/onnx-community/deberta-small-long-nli)
- NLI as a QA-answer verifier (Chen et al., 2021, "Can NLI Models Verify QA Systems' Predictions?"):
  - Method: convert question plus answer into a declarative hypothesis, then test entailment against the (decontextualized) source sentence.
  - Gains: at 20% coverage, selective-QA F1 rose from 81.6 to 87.1. Combining NLI with QA-model posteriors works best, and NLI alone performs poorly.
  - Off-the-shelf MNLI accepts 82.5% of answerable and rejects 78.5% of unanswerable SQuAD 2.0 questions, so the error rate is about 20% each way.
  - Conversion and decontextualization errors are under 10% of total errors. "Wrong/insufficient context" errors are 10-40% depending on dataset.
  - NLI struggles most on SQuAD-adv-style subtle changes.
  - Their converter and decontextualizer were T5-3B and the verifier RoBERTa-large, all far too big for the Pi.
  - [ar5iv: arXiv 2104.08731](https://ar5iv.labs.arxiv.org/html/2104.08731)
- QA2D (Demszky et al., 2018): if A correctly answers Q about passage P, then (P, declarative(Q,A)) is an entailed NLI pair. Their learned converter's declaratives exactly match human gold 45-57% of the time (BLEU 73-83). — [arXiv 1809.02922](https://arxiv.org/pdf/1809.02922)
- NLI filtering of distractors has been used directly in DG pipelines. Dutulescu et al. (AIED 2024) use NLI to remove distractors that are implications or synonyms of, or equivalent to, the correct answer. I could not access the full text for thresholds or error rates. — [ERIC record](https://searchworks.jioinstitute.edu.in/articles/eric__ED655793); [survey arXiv 2402.01512](https://arxiv.org/pdf/2402.01512)
- Latency reference on a Raspberry Pi (Arm's official ExecuTorch-on-Arm course), DistilBERT (66M, 6 layers × 768 hidden), example results:
  - PyTorch eager: 190.75 ms mean.
  - ExecuTorch with XNNPACK: 80.94 ms mean (p50 80.82, max 82.45).
  - ExecuTorch with portable kernels: 20,699.95 ms (a single run).
  - The page does not state the Pi model, sequence length, thread count, or precision, and calls these "example" numbers.
  - [Arm Learn: DistilBERT benchmark results](https://learn.arm.com/courses/executorch-on-arm/compare-transformer-inference/evaluate-an-encoder-based-transformer-deployment/view-the-distilbert-benchmark-results/)
- Encoder models can be exported to ExecuTorch. Arm's course exports and lowers DistilBERT to XNNPACK (`.pte`), and Optimum-ExecuTorch lists `text-classification` among export tasks with XNNPACK as the default recipe. — [Arm Learn: export/lower DistilBERT](https://learn.arm.com/courses/executorch-on-arm/compare-transformer-inference/evaluate-an-encoder-based-transformer-deployment/export-lower-and-benchmark-distilbert-with-executorch-and-xnnpack/); [HF optimum-executorch export guide](https://huggingface.co/docs/optimum-executorch/guides/export)
- INT8 on a Cortex-A76 with ONNX Runtime's CPU provider made ResNet-50 about 1.83× faster (~145 → 79 ms). On a Cortex-A53, which has no dot-product instructions, INT8 was slower. — [arXiv 2609.16085](https://arxiv.org/pdf/2609.16085)
- An ONNX Runtime GitHub issue reports latency problems with BERT-style cross-encoder (reranker) ONNX models. I did not read it in detail; check it before relying on ORT for cross-encoders. — [onnxruntime #19494](https://github.com/microsoft/onnxruntime/issues/19494)

### Inferences
- **Model choice: xsmall over small.** Accuracy is the same (87.8 vs 87.6 MNLI-mm). xsmall's compute is much lower (12 layers × 384 hidden versus small's 6 layers × 768); most of xsmall's 70.8M params are the 128k-vocab embedding table, which costs memory but little compute.
- **Estimated xsmall latency.** Per-layer FLOPs scale with hidden², so xsmall is roughly half of DistilBERT's compute: about 30-60 ms per pair at 128 tokens on 2-4 A76 cores in FP32. DeBERTa's disentangled attention adds overhead, so the real number may be higher. This is an estimate and must be benchmarked.
- **Memory.** About 280 MB FP32, or about 75 MB with INT8 dynamic quantization. That fits easily beside a ~470 MB Qwen3-0.6B model.
- **Runtime.** ONNX Runtime (aarch64 wheel, INT8 dynamic quantization) is the lowest-risk way to run it on the Pi; ONNX exports already exist. ExecuTorch is plausible because DistilBERT lowers cleanly. However, I found no evidence that DeBERTa-v3's relative-position attention exports cleanly through `torch.export` and XNNPACK; treat this as a risk. A BERT/MiniLM-architecture NLI model is the safer ExecuTorch fallback.
- **Hypothesis construction must be cheap.** A T5 converter is too big for the Pi. Options:
  - (a) Template: "Q? A." or a fill-in of a cloze stem. Chen et al. note that appending the answer to a complex question is what their converter often learned anyway.
  - (b) Have Qwen3-0.6B emit a one-sentence "answer statement" for each option at generation time, so it is produced alongside the item and needs no extra call.
- **Premise selection.** Short Class-8 passages (~150-300 tokens) can be fed whole, avoiding Chen et al.'s "insufficient context" errors. For longer passages, use the top-2/3 sentences by lexical overlap. Take the max entailment over sentence windows for the key and the max entailment over windows for each distractor.
- **Expected error rates.** With MNLI-level NLI used alone, roughly 15-20% error each way on answer verification is a reasonable prior (from the Chen et al. SQuAD 2.0 numbers). This is why NLI should be combined with an extractive-QA signal and code checks, not used as a lone gate.

### Gaps
- No published Pi 5 / Cortex-A76 latency for any DeBERTa-v3 NLI cross-encoder, MiniLM-NLI, or tasksource model. No published INT8 accuracy drop for these specific models. Both must be measured locally.
- Unconfirmed whether DeBERTa-v3 exports to ExecuTorch/XNNPACK without unsupported ops.
- No paper found that reports NLI false-accept/false-reject rates specifically for MCQ distractors (the Dutulescu full text was inaccessible).
- MiniLM-based NLI cross-encoders (e.g. cross-encoder/nli-MiniLM2-L6-H768) were not verified in this pass. From memory they score slightly lower than DeBERTa-v3-xsmall, but I have no citation.

---

## 2. Extractive QA models as an independent answerer

### Takeaway
A distilled SQuAD model gives an independent, deterministic second opinion on the key. It is a different architecture and training data from the generator, so its errors are less correlated. Candidates are tinyroberta-squad2 (82.0 F1 on SQuAD 2.0, can abstain) and DistilBERT-SQuAD (87.0 F1 on SQuAD 1.1, 65M params). Expect roughly one DistilBERT-class forward pass (~80 ms on a Pi with XNNPACK) per question for short passages. Roundtrip-consistency filtering with an extractive QA model is an established technique for synthetic QA.

### Cited Findings
- deepset/tinyroberta-squad2: distilled from roberta-base-squad2, with "comparable prediction quality" at about twice the speed of the base model. SQuAD 2.0 validation EM 78.86 / F1 82.04 (older card revision: 78.69 / 81.92). A third-party listing gives ~81.5M params (not on the official card). SQuAD 2.0 training means it can output "no answer". — [HF model card](https://huggingface.co/deepset/tinyroberta-squad2); [PromptLayer listing](https://www.promptlayer.com/models/tinyroberta-squad2)
- distilbert-base-cased-distilled-squad: SQuAD v1.1 dev EM 79.6 / F1 ~87.0, 65.2M params. English-only, trained on SQuAD v1.1 only (no unanswerable class), and the card warns of biased answers. — [HF model card](https://huggingface.co/distilbert/distilbert-base-cased-distilled-squad)
- Roundtrip consistency (Alberti et al., ACL 2019): generate (Q, A) from context, then run an extractive QA model on (context, Q). Keep the item only if the predicted span equals the original answer. This gave significant gains when pretraining on the filtered synthetic data for SQuAD2/NQ. A noted limitation is that strict span matching rejects valid paraphrases. — [ACL Anthology P19-1620](https://aclanthology.org/P19-1620/); [emergentmind summary](https://api.emergentmind.com/topics/roundtrip-consistency-filtering)
- In Chen et al. (2021), the best verifier combined NLI with QA-model posteriors rather than using either alone. — [ar5iv: arXiv 2104.08731](https://ar5iv.labs.arxiv.org/html/2104.08731)
- DistilBERT on a Raspberry Pi via ExecuTorch+XNNPACK: ~81 ms mean per forward pass (example figure, sequence length unstated). — [Arm Learn](https://learn.arm.com/courses/executorch-on-arm/compare-transformer-inference/evaluate-an-encoder-based-transformer-deployment/view-the-distilbert-benchmark-results/)

### Inferences
- **How to use it with MCQs.** Run QA on (passage, stem). Compare the predicted span to each option by token-F1 or a char-overlap ratio. The key should be the best-matching option, and the match should be clearly better than any distractor's.
- **Disagreement means review, not proof.** If QA selects a span that best matches a distractor, the item is suspect: either the key is wrong or the distractor is also correct.
- **Abstention.** If the QA model abstains (tinyroberta "no answer") or has low confidence, the question may not be answerable from the passage.
- **Limits.** Extractive QA only works for factoid and span-type questions. It is weak on "why/how" and inference items, which are common in the project's "cause-effect" style passages. For those, NLI is the better signal, so weight QA lower when the predicted span is long or the stem starts with why/how.
- **Model choice.** tinyroberta-squad2 is preferred over DistilBERT-SQuAD1.1 because it can abstain. Both are about 65-82M params (~250-330 MB FP32, ~80 MB INT8).
- **Estimated latency.** For a 300-token passage plus stem, about 100-200 ms FP32 on 2-4 A76 cores (scaled from the 81 ms DistilBERT figure; unverified).

### Gaps
- No measured Pi 5 latency for tinyroberta-squad2 or DistilBERT-SQuAD on QA-length (300-384 token) inputs.
- No study found that measures extractive-QA disagreement as a detector of wrong keys or multiple-correct distractors in *MCQs* specifically (as opposed to span QA).

---

## 3. Self-consistency and answer-back checks with the same small LLM

### Takeaway
Answer-back ("round-trip") filtering with the generating model is cheap to implement. Evidence that it improves quality is mixed: it helped on one dataset and not another, even with GPT-4. Its main weakness is correlated errors: a model is systematically worse at catching its own mistakes. Qwen3-0.6B in particular measured at chance as an MCQ-flaw judge. Variants that reduce correlation are: blind choice among shuffled options with the key hidden, answering from the whole passage, paraphrased stems, and choices-only probes. Treat these as weak secondary signals.

### Cited Findings
- Round-trip filtration (GPT-4):
  - Method: after generating Q and A, give Q back with the context but without A. Keep the pair only if the new answer matches. The authors say this "improves precision at the potential expense of some recall".
  - Results: on CovidQA, one-shot data plus round-trip filtering gave the best EM/F1. On PolicyQA (12k+ examples), unfiltered one-shot data was best (+1.6 EM / +1.5 F1 over baseline) and outperformed the filtered variant.
  - [arXiv 2309.12426](https://arxiv.org/pdf/2309.12426)
- ESGenius (2025) discards MCQs whose evaluator answer is unstable across rounds, which is a consistency filter. — [arXiv 2506.01646](https://arxiv.org/pdf/2506.01646)
- Self-correction blind spot: across 14 open-source non-reasoning models, the average blind-spot rate was 64.5%. Models fix identical errors when shown as external input but not in their own output. Appending "Wait" reduced blind spots by 89.3%, suggesting the capability exists but is not triggered. — [arXiv 2507.02778](https://arxiv.org/abs/2507.02778)
- LLMs often cannot self-correct reasoning without external feedback (Huang et al., ICLR 2024). — [arXiv 2310.01798](https://arxiv.org/abs/2310.01798). *Flag: cited from prior knowledge; not re-fetched in this session.*
- **Qwen3-0.6B as an MCQ-flaw judge (BenchMarker, Balepur et al., 2026):**
  - On in-domain writing-flaw detection: accuracy 0.73, F1 0.05, Cohen's κ 0.00. This is no better than the trivial "Always Not Flawed" baseline (accuracy 0.74).
  - Out-of-domain (human exams): accuracy 0.90, F1 0.06, κ 0.02.
  - Shortcut detection: accuracy 0.71, κ 0.39.
  - Qwen3-1.7B is only slightly better on writing flaws (κ 0.16).
  - Best judges: GPT-5 (writing κ 0.50) and the SAQUET hybrid toolkit (out-of-domain κ 0.48).
  - [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)
- BenchMarker also finds that LLM-written distractors (MMLU-Pro) are more often *correct when they should be incorrect* (10% → 22%) and less plausible (7% → 17%). Example: key "zero" with a generated distractor "does not change". — [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)
- Choices-only accuracy, where the model answers from the options without the stem, is a known shortcut probe. BenchMarker warns that on its own it overestimates flaws. — [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)

### Inferences
- **The MMLU-Pro "zero" vs "does not change" example is exactly the failure to catch.** LLMs generate paraphrase-equivalent distractors, and the same LLM will not notice them. NLI (option-vs-option entailment) and code-level normalization are better suited to catch this than answer-back.
- **Variants that reduce shared error,** cheapest first:
  - (a) **Blind MCQ pick.** Present the passage, stem, and *shuffled* options (key hidden) and read logits over the option letters (1 forward pass, no decoding). Disagreement with the key flags the item. Agreement is weak evidence because the error is correlated.
  - (b) **Position-swap.** Repeat (a) with a second shuffle. Instability flags ambiguity or multiple correct answers. This doubles the cost.
  - (c) **Paraphrased stem.** Reduces surface-cue reuse but needs a decode step, so it is expensive on the Pi.
  - (d) **Whole-passage answering vs evidence-sentence answering.** Useful when the generator was conditioned on a single sentence.
- **Use the option-letter probability margin.** Use p(key) − max p(distractor) from (a) as a continuous feature rather than a hard pass/fail.
- **Never use Qwen3-0.6B as a free-form judge** ("is this question well-formed?"). The BenchMarker numbers show it is at chance.

### Gaps
- No study found that measures blind answer-back with a sub-1B model as an MCQ filter (false accept/false reject rates).
- No measured Pi 5 prefill throughput for Qwen3-0.6B in this project. The project's docs list 9.8 tok/s prefill on a Cortex-A53 (Arduino UNO Q) and 854 tok/s on an M4 Mac; the A76 with dot-product instructions should be several times faster than the A53, but the number is unknown. This is the dominant latency term for any LLM-based check.

---

## 4. Pure-code checks

### Takeaway
Rule-based item-writing-flaw (IWF) detection is cheap, interpretable, and in one study beat GPT-4 against human labels. Both rules and GPT-4 were poor on "more than one correct answer" and "logical cues", which is why semantic checks (layers 2-3) are still needed. Per-question cost on a Pi is a few milliseconds without spaCy and tens of ms with a small spaCy pipeline.

### Cited Findings
- Moore et al. (2023): a rule-based detector for 19 IWFs on 200 student MCQs.
  - Agreement: matched 90.87% of human labels (Hamming loss 0.09) vs GPT-4 at 78.89% (0.21). Exact-match across all 19 criteria was only 15% (rule) and 12% (GPT-4).
  - Bias: rules over-flagged (mean 2.1 flaws/question vs human 1.6). GPT-4 over-flagged more (4.2).
  - Acceptable/unacceptable verdict (≥2 flaws = unacceptable): rules agreed with humans on 65% of questions.
  - Per-flaw: rules had high F1 for "longest option correct" and "true/false question", which are easy length and keyword checks. Both methods matched humans on "none of the above" and "negative worded". Both were poor on "logical cues" and "more than one correct".
  - [arXiv 2307.08161](https://arxiv.org/pdf/2307.08161) ([code](https://github.com/StevenJamesMoore/ECTEL23/blob/main/IWF.ipynb))
- The 19 IWFs: ambiguous/unclear info, implausible distractors, none of the above, longest option correct, gratuitous info, true/false question, convergence cues, logical cues, all of the above, fill-in-blank, absolute terms, word repeats (stem↔key), unfocused stem, complex/K-type, grammatical cues (options not parallel with stem), lost sequence (numeric/chronological order), vague terms, more than one correct, negative worded. Implementation methods:
  - String/keyword rules for most flaws.
  - POS/NER for word repeats and grammatical cues.
  - A CoLA-trained RoBERTa classifier for ambiguity.
  - GPT-4 for "more than one correct".
  - [arXiv 2307.08161](https://arxiv.org/pdf/2307.08161)
- SAQUET (Moore et al., 2024), a rules + NLP + selective-LLM toolkit, reports 94.13% label accuracy and 38% exact match (per a 2026 review; not verified against the original). In BenchMarker it scored out-of-domain κ 0.48 and in-domain κ 0.28. — [AIME-Con 2026 WIP review](https://aclanthology.org/2026.aimecon-wip.58.pdf); [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)
- Kalpakchi & Boye (2021) stand-alone filters, as summarized by the BEA 2025 survey: the fraction of MCQs with two or more identical distractors, and the fraction where a distractor matches the correct answer. The survey notes these "could actually be implemented within a DG model itself". — [BEA 2025 survey, ACL Anthology 2025.bea-1.5](https://aclanthology.org/2025.bea-1.5)
- Embedding cosine similarity of a distractor to the key is used as "plausibility". The survey warns it may reward distractors "too close to the correct answer" and that this is rarely validated against student data. — [BEA 2025 survey](https://aclanthology.org/2025.bea-1.5)

### Inferences
Recommended code checks for this project, all under 10 ms in Python:
- **Normalization and duplicates.** Lowercase, strip punctuation and articles, lemmatize optionally. Reject if any two options are identical after normalization, or if token-Jaccard ≥ 0.8. Flag for review if one option is a substring of another.
- **Key grounding.** At least one passage sentence should contain ≥ 60-70% of the key's content words (stopwords removed, light stemming). For cloze or factoid keys, require an exact or near-exact span. Pick the "evidence sentence" as the one with maximum overlap with the stem's content words *plus* the key. If the stem keywords and the key are in different sentences that are far apart, flag it.
- **Distractor-not-asserted.** If a distractor's content words appear in the evidence sentence in the same syntactic slot as the key, it may also be correct. This is a heuristic pre-filter for NLI, not a verdict. Distractors that appear in the passage are *fine* (good distractors often do); what matters is whether the passage asserts them as the answer to the stem, which NLI decides.
- **Negation handling.**
  - Detect negated stems ("NOT", "EXCEPT", "which is false"). Either reject them (IWF "negative worded"; risky for low-literacy learners) or invert the NLI logic for those items.
  - Detect negation mismatch between the key and the evidence sentence (`not`, `never`, `no`, `cannot`, `-n't`, antonym prefixes). Bag-of-words overlap ignores this, so route such items to NLI.
- **Homogeneity.**
  - Length: flag if the key is the uniquely longest option and is ≥ 1.5× the median distractor length (IWF "longest option correct").
  - Type: all options should share a coarse type (number vs word vs phrase). With spaCy small (optional), check that all options share the head POS.
  - Numbers: options should share the same unit.
- **Banned patterns.** "all of the above", "none of the above", "both A and B", absolute terms ("always", "never") only in distractors, vague terms, and stem-key word repeats (a stem content word that appears in the key but in no distractor).
- **Form.** The stem ends with "?" or a blank. There are exactly N options and one key index. No option is empty. The stem is answerable without options (no "Which of the following is true?" with unrelated options).

Expected value: these catch most well-formedness flaws and the trivial key/distractor errors. On their own they will *not* reliably catch a semantically correct distractor (Moore et al.'s rules were poor on "more than one correct").

### Gaps
- No published Pi timings for spaCy `en_core_web_sm`. Assumed ~5-20 ms for a short MCQ, unmeasured.
- No published per-flaw precision/recall for Moore's rules was extracted (the table did not parse cleanly); only the qualitative per-flaw summary above.

---

## 5. Evidence on false-positive / false-negative rates for automatic MCQ quality filtering

### Takeaway
The field has few validated error-rate numbers. The BEA 2025 survey states that most static (content-only) distractor metrics are not validated against real student responses. The best available numbers come from:
- IWF rule detection: ~91% label agreement, but only 65% agreement on accept/reject.
- LLM judges: GPT-5 κ ≈ 0.5; Qwen3-0.6B κ ≈ 0.
- NLI answer verification: ~80% accept on answerable / ~79% reject on unanswerable SQuAD 2.0.

Error rates of generated items themselves are substantial (e.g. 36% flagged in one clinical study), which justifies a strict, reject-on-doubt policy.

### Cited Findings
- BEA 2025 survey (Benedetto, Taslimipoor, Buttery):
  - Proposes a taxonomy: traditional distractor analysis (student data), AI-based dynamic (QA models as student proxies), and static approaches (comparative / stand-alone / learned).
  - Static approaches "should be validated (but often are not)". The AI-based dynamic approaches using QA models as student proxies are likewise "rarely" validated.
  - Only 15 of 40 automated-evaluation papers evaluate distractors as a *set*. The survey argues set-level evaluation is needed, which matters for catching "two correct options".
  - Learned "faithfulness" checkers exist: Qu et al. (2024) train a model to predict whether a distractor is actually a correct answer; Raina et al. (2023) train a key-vs-distractor classifier validated on Cambridge student data.
  - [ACL Anthology 2025.bea-1.5](https://aclanthology.org/2025.bea-1.5)
- Rule-based IWF vs human:
  - 90.87% label agreement (GPT-4: 78.89%).
  - 65% accept/reject agreement (GPT-4: 62%).
  - Both over-flag, i.e. produce false positives: means of 2.1 (rules) and 4.2 (GPT-4) flaws per question vs 1.6 (human).
  - [arXiv 2307.08161](https://arxiv.org/pdf/2307.08161)
- Crowdworkers disagree with experts on MCQ quality 25% of the time (cited by BenchMarker from Moore et al. 2023a), so "ground truth" is itself noisy. — [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)
- Off-the-shelf MNLI verifier on SQuAD 2.0: 82.5% acceptance of answerable and 78.5% rejection of unanswerable items. — [ar5iv: arXiv 2104.08731](https://ar5iv.labs.arxiv.org/html/2104.08731)
- Base rates of bad generated items:
  - In a 2025 clinical MCQ study, 64% of AI-generated items were unanimously judged correct and 36% were flagged for issues including multiple correct answers or a wrong key (reported via search summary; not read in full). — [JMIR Formative 2025](https://formative.jmir.org/2025/1/e75607)
  - In a UK public-health MCQ pipeline, an LLM error detector flagged ~44% of items in an early version and ~8% after pipeline improvements (search summary). — [arXiv 2505.06046](https://arxiv.org/pdf/2505.06046)
  - GoldenSwag's automated filtering reduced multiple-correct items 18% → 4% but increased grammar inconsistencies 68% → 79%. — [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)

### Inferences
- **The cost asymmetry favors false positives.** A wrong-key item shown to a student is worse than discarding a good item, because the on-device generator can simply regenerate. Set thresholds so the false-accept rate is low and accept a 20-40% rejection rate.
- **Expect high false-positive rates from any single cheap check.** Rules over-flag, NLI has ~20% error each way, and extractive QA misses non-factoid items. Combine signals and regenerate rather than trying to make any one check precise.
- **Calibrate on local data.** Validate thresholds on a hand-labelled set of ~200 project-generated items (the project already has `data/passages/eval/` and `results/eval_qwen3_base/`). The survey's main criticism is unvalidated metrics.

### Gaps
- No public dataset of *small-LLM-generated* MCQs with labels for wrong key or multiple correct, so no reliable base rate for Qwen3-0.6B items.
- No end-to-end FP/FN numbers for a layered NLI+QA+rules filter on MCQs. That would be novel measurement for this project.

---

## 6. Recommended layered design, thresholds, fallbacks, and Pi 5 latency budget

### Takeaway
Run cheap deterministic gates first and expensive model gates only on survivors:
- **L0:** code checks.
- **L1:** NLI cross-encoder over the key and every distractor (core safety gate).
- **L2:** extractive QA cross-check (factoid stems only).
- **L3 (optional):** blind Qwen3-0.6B pick from shuffled options.

On any hard failure, regenerate rather than repair, and fall back to a pre-verified item bank after N failed attempts. The estimated added latency is ~0.3-0.8 s per question for L0-L2 and several more seconds if L3 is used. All of these are inferences and need Pi 5 benchmarks.

### Cited Findings (design inputs)
- NLI plus QA-confidence beats either alone for answer verification. — [ar5iv: arXiv 2104.08731](https://ar5iv.labs.arxiv.org/html/2104.08731)
- Roundtrip extractive-QA consistency is an established synthetic-QA filter. — [ACL P19-1620](https://aclanthology.org/P19-1620/)
- Rules are the most accurate cheap IWF detector, but weak on "more than one correct". — [arXiv 2307.08161](https://arxiv.org/pdf/2307.08161)
- Qwen3-0.6B is at chance as a flaw judge. — [arXiv 2602.06221](https://www.arxiv.org/pdf/2602.06221)
- DistilBERT-class encoder: ~81 ms per forward pass on a Raspberry Pi with ExecuTorch+XNNPACK (example figure). — [Arm Learn](https://learn.arm.com/courses/executorch-on-arm/compare-transformer-inference/evaluate-an-encoder-based-transformer-deployment/view-the-distilbert-benchmark-results/)
- INT8 roughly 1.3-1.8× faster than FP32 on Cortex-A76 for CNNs under ONNX Runtime. — [arXiv 2609.16085](https://arxiv.org/pdf/2609.16085); [arXiv 2607.23227](https://arxiv.org/pdf/2607.23227)

### Inferences (proposed design; thresholds are starting points to calibrate on a local labelled set)

**L0 — Structural / code (≈ 1-20 ms).** Hard reject on:
- the wrong number of options;
- duplicate or normalized-equal options, or token-Jaccard ≥ 0.8 between any two options;
- a distractor equal to or containing the key;
- "all/none of the above";
- an un-grounded key (< 0.6 content-word overlap with every passage sentence, for factoid items);
- a negated stem (unless the item type explicitly allows it).

Soft flag (lowers the score, triggers L3) on: longest-option cue, length ratio > 1.5×, mixed option types or units, absolute or vague terms only in distractors, stem-key word repeat, negation mismatch between key and evidence sentence.

**L1 — NLI over all options (core safety gate).**
- Model: DeBERTa-v3-xsmall NLI (prefer a binary entailment model). Runtime: ONNX Runtime with INT8 dynamic quantization, or ExecuTorch if export works.
- Premise: the whole passage if ≤ ~350 tokens; otherwise the top-3 sentence windows by overlap with the stem.
- Hypotheses: one statement per option ("stem + option" template, or the generator emits the statement).
- Pass rule:
  - P(entail | key) ≥ 0.7, and
  - for every distractor, P(entail | d) ≤ 0.3, and
  - P(entail | key) − max_d P(entail | d) ≥ 0.4.
- Plus option-vs-option paraphrase check: if NLI(key ⇒ d) and NLI(d ⇒ key) are both ≥ 0.7, then d is equivalent to the key, so reject. This catches the "zero" vs "does not change" case.
- Cost: 4 option hypotheses + 3 pairwise checks ≈ 7 pairs (×3 if windowed), batched. Estimated ~0.2-0.5 s on 2-3 A76 cores while the LLM is idle.

**L2 — Extractive QA cross-check (factoid stems only; skip for why/how).**
- tinyroberta-squad2 on (passage, stem).
- Pass: the predicted span's best-matching option is the key (token-F1 ≥ 0.5) and outscores every distractor by ≥ 0.2 F1.
- If QA abstains or picks a distractor, set a "disagree" flag. Disagree plus a borderline L1 result means reject; disagree plus a strong L1 result means send to L3.
- Cost: ~0.1-0.2 s (estimated).

**L3 — Blind LLM pick (tie-breaker only, run for flagged items).**
- Qwen3-0.6B gets the passage, stem, and options shuffled, without the key, and its option-letter logits are read with no decoding.
- Reject if argmax ≠ key, or if p(key) − max p(d) < 0.2.
- Optionally run a second shuffle and reject if unstable.
- Cost: dominated by prefill of ~300-450 tokens. On a Pi 5 this is unmeasured; it is likely a few seconds per pass, and it competes with generation for the same cores. Run it only on the ~10-30% of items that were flagged.

**Decision and fallbacks.**
- Any L0 hard fail or any L1 fail: regenerate (up to 2-3 attempts, ideally with a different seed or evidence sentence).
- After that, serve a pre-verified item from a bank built offline. Build the bank with the same pipeline plus a bigger offline model or human review.
- Log every rejection with its reason, so that thresholds can be re-calibrated.
- Prefer "rather show nothing than a wrong-key item": the cost asymmetry is described in section 5.

**Memory budget.** NLI-xsmall INT8 (~75-100 MB) plus tinyroberta INT8 (~80-100 MB) plus runtime overhead is roughly 0.3-0.5 GB extra. This fits within 8 GB alongside Qwen3-0.6B, whose project-measured peak memory is 1.7-2.5 GB.

**Total added latency per question (estimated, Pi 5):**
- L0 + L1 + L2: ~0.3-0.8 s.
- With L3 on flagged items only, the amortized total is ~1-2 s.
- Running verification while the student reads the previous question hides most of it.

**Calibration plan.**
- Label ~200 Qwen3-generated items from `data/passages/eval/` for wrong key, multiple correct, and ill-formed.
- Sweep the L1 thresholds to hit a ≤ 2-3% false-accept rate on wrong-key or multiple-correct items, and report the resulting rejection rate.
- Benchmark L1/L2 p50/p95 on the Pi 5 at 2 and 4 threads, with the LLM loaded.

### Gaps
- All Pi 5 latency figures above are extrapolations from a single DistilBERT example benchmark of unstated configuration. None are measured on the target.
- The thresholds (0.7 / 0.3 / 0.4 / 0.5 / 0.2) are engineering starting points, not values from the literature. No source reports optimal thresholds for MCQ verification with small NLI models.
- The effect of running encoder inference at the same time as Qwen3-0.6B ExecuTorch inference on the same 4 cores (contention, thermal throttling) is unknown.
