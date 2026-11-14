# Misconception mapping, the Kaggle-Eedi way (handoff for any Claude session)

*Written 14 Nov 2026, ~00:30, hackathon day. If you are a fresh Claude session: read this file, then
`docs/JUDGE_BRIEF.md` (decisions + numbers so far). Research first, measure everything, record numbers in
JUDGE_BRIEF. Never invent numbers.*

## The task
Our fine-tuned Qwen3-0.6B writes multiple-choice questions on the Raspberry Pi, but its wrong options carry **no
label** saying which student misconception each one represents. The retention engine (`src/sakshi/retention/`:
Bayesian diagnosis, BKT, prerequisite graph, FSRS) needs that label: "student picked option C -> they probably hold
misconception X -> show X's fix and schedule X for revision".

So: **given (passage sentence, question, one wrong option) -> return the misconception id from our graph
(`data/misconceptions/library.jsonl`, ~3,400-3,800 misconceptions over ~225-250 topics), or ABSTAIN.**
This is exactly the Kaggle competition "Eedi - Mining Misconceptions in Mathematics" (2024): question + wrong
answer -> misconception, metric MAP@25.

## What the winners did (sources: Gemini Deep Research report "AI Misconception Distractor Generation", 13 Nov;
Kaggle write-ups linked there)
- **Retrieve-and-rerank.** Stage 1: a bi-encoder (embedding model) retrieves the top-k candidate misconceptions.
  Stage 2: a reranker scores each (query, candidate) pair and orders them.
- **Contrastive fine-tuning of the retriever** on labelled (question + wrong answer -> misconception) pairs, with
  **hard negatives** (similar but wrong misconceptions). 1st place used Qwen-14B retrievers + 10k synthetic pairs;
  9th place reported the retriever jumping a lot with synthetic data (public LB 0.447 without it).
- **LLM-written "why a student would pick this" rationales** as extra reranker input (1st place used Claude offline).
- Post-processing priors for unseen misconceptions (3rd place "magic boost").
Our constraint: it must run on a Pi CPU, so we use the same ARCHITECTURE with small models (33M embedder, small
cross-encoder), exported to ExecuTorch. Judge line: "the architecture that won the Eedi Kaggle competition,
scaled down to run offline on a Raspberry Pi".

## What already exists (do not rebuild)
- `src/sakshi/mapper.py`: `Mapper` with topic shortlist (BM25 + embeddings), `score_sentence`, NLI rerank features,
  `option_consistency` (round-trip check). Encoders: `TorchEncoders` (Mac) and `PteEncoders` (device, ExecuTorch).
- Exported helpers: `models/helpers/embed` (bge-small-en-v1.5, 133 MB .pte) and `models/helpers/nli`
  (cross-encoder nli-deberta-v3-xsmall, 329 MB .pte), ~12 ms per pair on the Mac. Export: `scripts/export_helpers.py`.
- Precomputed library vectors: `data/misconceptions/index/{BAAI_bge-small-en-v1.5,pte_bge-small-en-v1.5}.npz`
  (rebuilt 13 Nov for 3,391 misconceptions; rebuild if the library grows: constructing `Mapper` rebuilds it).
- Retriever fine-tuning script: `train/finetune_retriever.py` (sentence-transformers, MultipleNegativesRankingLoss,
  same-topic hard negatives). NOTE: it trains on (evidence sentence -> misconception) from the OLD Gemini dataset;
  it must be adapted to the new labelled pairs below.
- Evaluation script: `scripts/eval_mapping.py` (AP@25, keywords vs mapper). Adapt it to the new pairs.
- Topic matching: 39/40 test passages to the right topic (`scripts/check_library_match.py`).

## The labelled data we now have (the key asset)
Teacher questions (Claude Opus/Sonnet, 13 Nov), graded by Sonnet: every wrong option has a misconception id.
- Location (not in git): `/Users/arushjain/Documents/opus-work/namma-ai/data/dataset_v2/raw/*.json` (401
  passages) + `.../grades.jsonl` (2,773 graded). Each raw file: `passage`, `job.topic_id`, `response.items[]` with
  `evidence`, `q`, `options` (correct first), `wrong: [{misconception: "<id>", why: "<student reasoning>"}, ...]`.
- Converted good questions (score >= 4) also in `data/dataset_opus/train.jsonl` with `wrong_misconceptions`.
- Expect ~2,700-3,000 (wrong option -> misconception) pairs from graded >= 3 questions; the `why` text is a free
  "student rationale" (the 1st-place trick).
- Check ids exist in the CURRENT library (the graph grew; ids are stable but verify) and drop `null`s.

## Plan (in order; stop and report numbers after each step)
1. **Build pairs**: query = `"{question} Wrong answer: {option}"` (optionally + evidence sentence), label = the
   misconception id; keep `why` as a rationale field. **Split by passage** (never the same passage in train and
   test): ~80/20. Also keep the topic id for the shortlist.
2. **Baseline evaluation (no training)**: rank all misconceptions of the passage's top-3 topics with (a) the current
   embedder, (b) embedder + NLI rerank. Report recall@1, recall@5, MAP@25 on the test split. This is the first
   honest number.
3. **Fine-tune the retriever** (Kaggle recipe, scaled down): bge-small-en-v1.5, MultipleNegativesRankingLoss,
   positives = the labelled misconception (statement + fix text), hard negatives = other misconceptions of the same
   topic, 1-3 epochs, a few minutes on the Mac. Re-evaluate on the same test split. Keep it only if it beats the
   baseline.
4. **Reranker**: compare the current NLI cross-encoder vs a small cross-encoder fine-tuned on the same pairs
   (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2` with binary labels and hard negatives). Keep whichever measures
   better; CPU cost matters (Pi: keep top-k <= 5 per option).
5. **Abstain threshold**: pick the score threshold on the train split so precision of shown labels >= ~80%; below
   it, the option gets no misconception (retention just marks the concept wrong). Report coverage vs precision.
6. **Export** the winners with `scripts/export_helpers.py --embed <path>` and check `.pte` vs PyTorch outputs; rebuild
   the library index for the new embedder; time it per option on the Mac (and on the Pi on the day).
7. **Integrate**: after the quiz model writes a question, run the mapper on each wrong option, store
   `misconception` per option, then the retention engine: wrong answer -> show the misconception's `fix` text
   ("You might think X. Actually Y" = refutation text, g ~ 0.41, Tippett 2010) and schedule it as its own FSRS card.
8. **Record** every number (baseline vs fine-tuned recall@1/@5/MAP@25, threshold, coverage, latency) in
   `docs/JUDGE_BRIEF.md`.

## Rules
- Test split by passage; never tune on the test split; report both splits.
- The 40 eval passages (`data/passages/eval/`) and `data/dataset/test_passages.jsonl` are frozen.
- Commit only when the human asks. Never commit `.env`, `models/`, `.venv*`, `out/`.
- Research before building anything new (the human's standing rule): show sources with numbers.

## Context: where the project is (14 Nov, ~00:30)
- Quiz model: version 1 (SciQ+RACE, Mac) = 30% "sensible", key right 82% on 40 test passages (blind Sonnet grade).
  Final model is being trained on a teammate's RTX 4080 from `~/Downloads/final-training.zip` (starts from version 1,
  + 905 graded teacher why/how questions + 300 RACE). When his `trained-adapter.zip` arrives: merge
  Qwen3-0.6B + `out/qwen3-0.6b-mcq/adapter` (v1) + his adapter, export to ExecuTorch with `--max_seq_len 1024`
  (see `train/README.md`), run `scripts/backup_quiz.py generate --variants ft --model <dir>` then `judge` then
  `report`, compare with v1.
- Pi kit: `~/Documents/pi-kit` (install.sh / test.sh / CHECKLIST.md); event board is a Raspberry Pi 5 8 GB.
