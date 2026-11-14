# GURU: an offline study buddy that turns a passage into a summary and a self-check quiz
*Namma AI Hackathon, Problem 1 (AI for Inclusive Education), 14 Nov 2026. Fill the [brackets] with Pi numbers and the organiser's passage.*

## Learning barrier and learner
Students in Class 6-10 in low-connectivity regions cannot ask an online tutor or search when they are stuck, and a textbook passage
gives them no way to check whether they understood it. **GURU** runs fully offline on a Raspberry Pi 5 (no cloud AI at any step).

## What it does (the PoC)
1. Takes one passage (150-300 words).
2. Prints a short, plain-English summary. [state how the summary is produced]
3. Prints at least three multiple-choice questions. Each is built in two short model calls:
   - **Call 1 (question + answer):** a "why / how / what happens" question and its correct answer, from one key sentence.
   - **Call 2 (wrong options):** three options that a real student could believe, sampled twice, de-duplicated, and
     rejected if they repeat, copy the answer, or give the answer away by length. Options are shuffled.
4. Optional: after the student picks, the supporting sentence from the passage is shown.

## Model and technical facts
| Item | Value |
|---|---|
| Base model | Qwen3-0.6B (596 M params: 440 M transformer + 156 M embedding) [confirm it is on the approved list] |
| Adaptation | LoRA fine-tune (rank 16, 1 epoch, lr 5e-5) on teacher-written quiz data, merged into the base model |
| Runtime | ExecuTorch on Raspberry Pi 5 (8 GB), no network |
| Precision | **8-bit weights** (quality-neutral in our simulation); 4-bit shown as an optional eco mode |
| Model size | ~596 MB (8-bit) / ~404 MB (4-bit g32) [calculated; replace with the .pte file size] |
| Peak RAM | [measure: /usr/bin/time -v]; expected well under 1 GB |
| Time per question | [measure] prefill [ ] ms, decode [ ] tok/s, total [ ] s |
| Power / energy | [measure: PMIC] [ ] W, [ ] J per question |

## What we measured (honestly)
- Two-call pipeline vs a single-call pipeline, on 40 unseen passages, blind read of 12 pairs: 8 vs 3 good questions.
  Correct answer is the longest option in 6% of questions (was 15%).
- Wrong options: in a blind read of 20 sets, teacher-written options were all good (20/20); the model's were good in 10/20.
  The main failure is an option that is also correct, so we show only filtered questions and say so.
- Quantization: 4-bit weights cost about +0.13 held-out loss, 8-bit about +0.006 (simulated). That is why we ship 8-bit.
- Not measured yet: everything on the Pi itself.

## Impact example (use the organiser's passage)
Passage: [paste one sentence]. Question the model wrote: [paste, after a human check]. Why it helps: a student who picks
[wrong option] holds the misconception that [what it reveals]; the shown sentence [paste] corrects it, with no internet and no tutor.

## Limits we state up front
Strict blind read of 60 generated questions on unseen passages (a question counts as good only if the answer is supported by
the text, no second option is also correct, and the wrong options are clearly wrong): about 40-55% were fully sound.
Rule-based picking of the best 3 of 6 candidates did not clearly help (picked 8/15 vs rejected 6/15), so we do not claim it.
**Design answer: teacher in the loop.** GURU proposes several candidate questions and the teacher approves or edits three,
which is how the tool would be used in a real classroom (the repo's `edit` command). Some generated options can be weak or
arguably correct; a teacher should review before graded use. No multilingual support,
no accounts, no cloud. Source and results: [GitHub link].
