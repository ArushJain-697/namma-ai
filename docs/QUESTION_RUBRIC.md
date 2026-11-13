# Quiz question rubric

One rubric for everything: the teacher prompt (Opus writes training data by it), the grader (Sonnet scores every
question by it), and the final evaluation (`results/question_quality.md`). The 20 worked examples are in
`data/gold_questions.jsonl`.

Setting: a Class 6-10 student in India reads a 150-300 word passage, then answers 3-4 multiple-choice questions on
a Raspberry Pi, offline. Each question has 4 options and exactly one correct answer.

## Hard rules (a question that breaks any of these is rejected)

| id | rule |
|----|------|
| H1 | **Understanding, not word-spotting.** The question asks *why / how / what happens if / which explains / which example shows / what is the difference / what would change*. A student who only searches the passage for a matching phrase should not be able to answer it. At most 1 in 4 questions of a passage may be plain recall. |
| H2 | **No fill-in-the-blank**, no "according to the passage, which is true", no "which of the following statements is correct" with four unrelated facts. The question has one clear focus. |
| H3 | **Exactly one correct answer, provable from the passage.** The evidence sentence (copied word for word from the passage) proves it. A careful reader would agree; nothing in the passage supports a second option. |
| H4 | **Three wrong options a real student could believe.** Each comes from a real misconception (ideally one from `data/misconceptions/library.jsonl` for the topic) or a real reading mistake (mixing up cause and effect, picking a nearby name or number, over-generalising). Each is clearly wrong *by the passage*. No silly or joke options. |
| H5 | **No giveaways.** Never "all/none of the above", "both A and B". The correct option is not the longest, not the only one that copies passage wording, not the only grammatical fit, not the only one with a hedge ("usually", "can"). All four options have the same grammar and style and similar length (within about 4 words of each other). |
| H6 | **No answer leak.** The question does not contain the key words of the correct option. |
| H7 | **Simple English for Class 6-10.** Question at most 25 words, each option at most 12 words. No double negatives, no "NOT" questions. |
| H8 | **A one-line explanation** (at most 25 words) that tells the student why the answer is right, in their language, using the passage. |

## Soft qualities (decide the 1-5 score)

- The question targets the most important idea of its sentence, not a side detail.
- Wrong options are diagnostic: a teacher who sees which one a student chose learns *what the student believes*.
- The question can be answered from the passage alone (no outside knowledge needed), but rewards having understood it.
- Questions on one passage test different ideas from different sentences.

## Score

- **5** excellent: all hard rules pass, every distractor maps to a clear misconception, a teacher would use it as is.
- **4** good: all hard rules pass, small polish possible (one slightly weak distractor, slightly long wording).
- **3** usable: a hard rule is borderline (e.g. close to recall, one implausible distractor).
- **2** weak: breaks a hard rule (recall dressed up, a giveaway, a vague answer).
- **1** bad: wrong or two correct answers, broken, fill-in-the-blank, not about the passage.

Training data keeps only score >= 4 with all hard rules passing, and the code checks in `src/sakshi/diagnostic.py`
(`check_quiz_item`) passing.

## Good vs bad, side by side

Passage sentence: *"A sharp knife cuts better than a blunt one because the same force acts on a much smaller area,
so the pressure is greater."*

Bad (word-spotting / fill-in-the-blank): "A sharp knife cuts better because the same force acts on a smaller ____."
Bad (giveaway): options "Because pressure is greater when the same force acts on a smaller area" / "It is sharp" /
"Heavy" / "None of the above".

Good: **Why does a sharp knife cut better than a blunt one?**
- It puts the same force on a smaller area  ✅
- It is heavier than a blunt knife  (believes cutting depends on weight)
- It is made of a stronger metal  (believes material, not area, decides)
- It moves faster through the food  (confuses pressure with speed)

Explanation: Same force on a smaller area means more pressure, so the sharp edge cuts easily.
