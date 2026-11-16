# Proposal draft: Sakshi

**Namma AI Hackathon, Problem Statement 1: AI for Inclusive Education**
*Draft v1, 4 Nov 2026, from Master Bible v1.3. Due 6 Nov. The organisers have not said what a proposal must contain or how long it may be (bible question 4), so this is one page of plain prose that can be cut down. Everything in `[BRACKETS]` is a blank only you can fill. Nothing here quotes a number we produced, because none exists yet.*

**Team:** [names, college or organisation, and the college nomination if this is a student team] · **Team Leader (the only one who registers):** [name]

---

## The barrier and the learner

Many Class 6-8 students can read a passage without understanding it. When they study on their own there is no timely way to check, because the teacher has a whole class and, in a school with no internet, no online help or AI tutor is within reach. We focus on **Class 6-8 students in English or bilingual sections of Karnataka government schools**, where a large share of schools have no internet. [CITE: the share of Karnataka government schools without internet, from the primary source (UDISE+). A news report of 18,007 of 48,527 schools online, about 63% not, is our lead but **we have not read the primary source**. Do not submit the figure until you have.] [OPTIONAL, ONLY IF TRUE: one sentence from a teacher or student you spoke to.]

## What we will build

On one Raspberry Pi, with no connection, a student gives Sakshi a 150-300 word passage and gets a **short summary in simple words** and **at least three questions**. When a student answers, right or wrong, Sakshi shows the **exact sentence in the passage that holds the answer**, and if they missed it, asks one more question from that same sentence. It runs a small language model (Llama 3.2 1B, **subject to the organisers' approved list**) through ExecuTorch on the Pi. Terminal output is enough for the brief; we do not build a chatbot, a custom app or a platform.

## The failure we design against

Small language models write fluent questions whose answers can come from the model's own memory, not the passage. A student studying alone is the person least able to spot that, and may be told they are wrong when they are right. So **the model never writes the answer key.** Code picks the answer and the sentence that proves it; the model only writes the wording of the question and simplifies each summary sentence, one sentence at a time, and every summary sentence is checked against its own source sentence. No witness, no question; no witness, no summary sentence. Items that fail the checks are withheld, with the reason shown, and are never silently dropped.

## What we will show and report

- It runs with **no cloud inference**, with saved evidence that the machine has no route out.
- The brief's measurements: **approximate inference time, the model used, model size and memory**, printed after every run and written to a file by a script.
- How well the design holds up: we plan to test small models on passages built so that one fact differs from what a model "remembers", and report how often an ordinary one-call quiz generator follows its memory against how often ours follows the passage. **We will report the result whichever way it comes out, including if the effect is small.** [Keep this bullet only if you are comfortable promising it before the measurement exists.]

## How it could be used (a proposal, not a finding)

A teacher loads the week's passages once on a shared Raspberry Pi. Students take turns in a study or library period; the Pi can also serve the quiz to shared phones over its own Wi-Fi with no internet. [DEPLOYMENT: a priced bill of materials with a source for each price (Pi, cooler, power bank, card), or **leave cost out**. We have not priced anything. "Affordable" is the brief's word and needs a number.] Whether schools have shared phones or tablets is unknown to us.

## What we have not tested

No students have used it. We do not claim learning gains; whether it helps is a question for a pilot. It supports English only in this version, and asks mainly recall-level questions on purpose, because a key that cannot be invented matters more here than depth. A passing check means "passed the rules and shows its source sentence", not "correct": the output is a draft that a teacher can check in seconds by reading one sentence.

## Why ExecuTorch on Arm

It is the brief. It also fits the setting: a fixed-size model exported ahead of time needs no download step in a school with no connection. We will report what we measure on the Pi, with the conditions, and say plainly if an optimisation turned out not to matter.

---

### Before you submit (blanks and checks)

- [ ] Team names, organisation, nomination, Team Leader.
- [ ] **The internet share:** read the primary source (UDISE+) and cite it, or delete the figure. *The harvest files you gave me do not contain the source for it or for the quizzing-with-feedback evidence, so I could not cite either.*
- [ ] Remove or keep the "we plan to test" bullet.
- [ ] Cost: priced bill of materials, or leave it out.
- [ ] Organisers' answers on word limit and required sections (bible question 4); trim to fit.
- [ ] One real teacher or student sentence, or leave the hook out.
- [ ] No claim of learning gains, "first", or any number of ours.
