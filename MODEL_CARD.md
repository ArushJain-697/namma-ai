# GURU-0.6B model card

**Base:** Qwen/Qwen3-0.6B (Apache 2.0). **Adapters:** v1 LoRA, then a two-job LoRA (Job Q: question + answer; Job W: three wrong answers), merged.
**Export:** ExecuTorch 1.5.1, 8da4w (8-bit dynamic activations, 4-bit weights), 469 MiB, XNNPACK on Arm CPU.
**Stop tokens:** the runner must stop on both `<|im_end|>` (151645) and `<|endoftext|>` (151643).

## Intended use
Offline summaries and diagnostic multiple-choice questions on school-syllabus passages (English), for research and education.
Not for commercial use (training data licences below). Not for grading students or any high-stakes decision.

## Training data
SciQ (CC BY-NC 3.0), RACE middle-school (non-commercial research), and teacher data written by Anthropic Claude and Google Gemini for our passages and filtered by a rubric grader (1,794 graded, 1,039 kept).

## Evaluation: what is and isn't measured
- Held-out losses in the README come from a validation set that overlapped the earlier v1 validation set (200 of 310 rows), and checkpoints were selected on that same set, so they are optimistic. Run-to-run seed noise is about 0.02–0.04. Only the 4-bit quantization cost (~0.13) is clearly larger than that noise.
- The quality of the shipped **4-bit** pipeline has not been measured end to end. Quality numbers come from bf16 or simulated-quantization runs.
- The test passages were also used during development, so they are not a clean test set.

## Known limitations
Can write questions whose answer is not supported by the passage; wrong options may be implausible or accidentally correct; English only; small model, so expect factual slips. Every question shows its source sentence so a teacher can check it.

## Licences that must ship with the weights
Qwen3 Apache-2.0 `LICENSE`, BAAI bge-small-en-v1.5 MIT licence, cross-encoder/nli-MiniLM2-L6-H768 Apache-2.0. See `THIRD_PARTY_NOTICES.md`.
