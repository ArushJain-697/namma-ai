# Gemini Deep Research prompts (6)

Paste each one into Gemini Deep Research separately. When each report is done, export it (PDF or copy the text)
and drop it into the chat so Claude can pull out what to use. Every prompt asks for links and real numbers, so
nothing gets built on guesses.

Shared context (already inside each prompt): a student team, a hackathon on 14 Nov 2026 run by Arm + NASSCOM +
IIIT Bangalore. The task: on a Raspberry Pi 5 (8 GB), offline, using ExecuTorch, take a 150-300 word school passage
and output a short summary plus at least 3 good quiz questions, reporting time, model, size and memory. We use
Qwen3-0.6B (4-bit, ExecuTorch, XNNPACK), and our twist is diagnostic multiple-choice questions where every wrong
option is a known student misconception.

---

## 1. Edge-AI hackathon winners: what won and why

```
I'm on a student team competing tomorrow in an edge-AI hackathon run by Arm, NASSCOM and IIIT Bangalore. The task:
build an offline learning assistant on a Raspberry Pi 5 with ExecuTorch that turns a school passage into a summary
and quiz questions, and reports speed, model size and memory.

Research winning projects from edge-AI / on-device AI hackathons and competitions from 2023 to 2026, especially:
Arm-sponsored hackathons and challenges, ExecuTorch or PyTorch on-device events, Raspberry Pi AI competitions,
Hackster.io and Edge Impulse contests, Qualcomm / NVIDIA Jetson edge AI challenges, TinyML challenges, Smart India
Hackathon and NASSCOM / Indian government edtech and offline-AI problem statements, and any offline education or
"AI for low-connectivity" hackathons.

For each winning or finalist project give: event, year, project name, what it did, hardware, model and runtime,
the numbers they reported (latency, tokens/s, memory, accuracy), how they demoed it, and what judges said they
liked. Then summarise the patterns: what winning teams consistently did in the demo, the numbers they showed, the
"wow" moment, and common mistakes that lost. Also find any published judging criteria/rubrics for Arm or NASSCOM
hackathons and their weights.

Output: a table of projects with source links and dates, then a list of 10 concrete things we should do in a
3-minute demo tomorrow, each backed by an example. Mark anything you could not verify from a primary source.
```

## 2. Small language models on Raspberry Pi 5: real speed and memory numbers

```
I need measured, sourced benchmarks for running small language models (0.3B to 3B parameters) on a Raspberry Pi 5
(4 or 8 GB, Cortex-A76), offline, published 2024-2026.

Cover every runtime people use: ExecuTorch (XNNPACK, KleidiAI), llama.cpp / GGUF, Ollama, MLC-LLM, LiteRT-LM
(MediaPipe), ONNX Runtime GenAI, and any others. Models: Qwen3-0.6B, Qwen3-1.7B, Qwen2.5-0.5B/1.5B, Llama 3.2 1B/3B,
Gemma 3 1B / Gemma 4, SmolLM2/3, Phi, TinyLlama.

For each result give: model, quantization (4-bit, 8-bit, group size), runtime and version, threads, prompt
processing (prefill) tokens/s, generation (decode) tokens/s, peak RAM, model file size, cooling, and the link.
Then: (a) which runtime is fastest on a Pi 5 for a 0.6B model and by how much; (b) every known trick to speed up
ExecuTorch specifically on Raspberry Pi / Cortex-A76 (export flags, max_seq_len, quantization schemes, KleidiAI,
thread count, CPU governor, memory mapping, KV-cache reuse, prompt caching, speculative or lookup decoding); (c) any
known ExecuTorch slowness or bugs on aarch64 Linux and their workarounds; (d) thermal throttling effects and fixes.

Output: one benchmark table with links, then a ranked list of tricks with the measured speed-up each gave.
Separate verified numbers from claims.
```

## 3. Getting tiny models (under 3B) to write good multiple-choice questions

```
Research how to make a very small language model (0.5B to 3B parameters, ideally Qwen3-0.6B) generate good
multiple-choice quiz questions from a short school passage: questions that test understanding (why/how), exactly
one correct answer, and three plausible wrong options. Focus on 2023-2026 papers, repos and blog posts with numbers.

Cover: (1) fine-tuning / distillation recipes that worked for question generation and distractor generation with
small models (LoRA settings, dataset size, teacher model, data format, epochs), with before/after quality numbers;
(2) public datasets usable for training (RACE, SciQ, OpenBookQA, EduQG, NCERT-based sets, Indian school question
banks) and their licences; (3) prompting and pipeline tricks for small models (one question per call, generating
answer first then distractors, constrained output, self-verification, overgenerate-and-filter) with measured
effects; (4) how to automatically check that the answer key is right and the wrong options are wrong (and the
measured accuracy of those checks); (5) how papers evaluate question quality (human rubrics, LLM-as-judge) and what
scores small models reach compared with GPT-4-class models.

Output: a table of methods with model size, data, result numbers and links, then a recommended recipe for a 0.6B
model with about 2,000 high-quality teacher-written examples, and what quality we should realistically expect.
```

## 4. Misconception-based wrong answers: Eedi and Kaggle winning solutions

```
Research diagnostic multiple-choice questions where each wrong option maps to a student misconception, and how
AI systems find or generate those wrong options.

1. The Kaggle competition "Eedi - Mining Misconceptions in Mathematics" (2024): the top 10 solutions in detail -
   model types and sizes, retrieval vs reranking setup, embedding models, fine-tuning data, synthetic data, scores
   (MAP@25), and which tricks gave the biggest gains. Also any small-model (under 2B) solutions and their scores.
2. Eedi's own research and blog posts on misconceptions, distractor generation with LLMs, and what they found works.
3. Papers on misconception-aware distractor generation (e.g. DiVERT, MISTAKE, and anything newer), with model sizes
   and results, especially anything working with small models.
4. Other education Kaggle competitions where small models won or did well (e.g. LLM Science Exam) and their tricks.

Output: for each solution or paper, the method, model sizes, numbers and link; then a short list of techniques
that could run on a Raspberry Pi with a 0.6B model plus small helper models (embeddings, rerankers) to pick or
write misconception-based wrong options.
```

## 5. Offline AI for education in India: impact evidence and numbers for the pitch

```
I need sourced facts for a 3-minute hackathon pitch about an offline AI quiz tutor for Class 6-10 students in India
that runs on a Raspberry Pi without internet.

Find, with primary sources (government reports, ASER, UDISE+, PARAKH Rashtriya Sarvekshan, NCERT, NITI Aayog,
World Bank, UNESCO, J-PAL, peer-reviewed studies), the latest numbers on: schools without internet or computers
(government vs private, rural vs urban); learning levels in reading comprehension and science for Class 6-10;
pupil-teacher ratios and single-teacher schools; electricity access in schools; cost of devices like Raspberry Pi
in India. Also find evidence on what works: measured learning gains from formative assessment, diagnostic questions
and personalised practice (e.g. Mindspark, TaRL, Eedi, adaptive learning RCTs), and existing offline/low-bandwidth
edtech in India (DIKSHA offline, Google Read Along, Khan Academy Lite, Kolibri, others) and what they lack.

Output: a table of facts (number, what it means, year, exact source link, whether primary). Then the 5 strongest
facts for a hook, and a competitor table: product, offline?, what it does, what it lacks compared with a diagnostic
quiz that shows which misconception a student holds.
```

## 6. Impressing Arm and ExecuTorch judges: Arm-specific optimisation and profiling

```
I'm presenting a project to Arm engineers: a small language model (Qwen3-0.6B) running with PyTorch ExecuTorch on a
Raspberry Pi 5 (Cortex-A76). Research what Arm and the ExecuTorch team showcase and value, so we can show real
Arm-specific engineering, from 2024-2026 sources.

Cover: (1) Arm Learning Paths and official tutorials for LLMs on Raspberry Pi / Arm CPUs with ExecuTorch, llama.cpp,
KleidiAI - exact steps, flags and reported numbers; (2) KleidiAI micro-kernels: which CPU features they use (dotprod,
i8mm, SVE, SME), which apply to Cortex-A76, and measured speed-ups; (3) ExecuTorch export best practices for Qwen /
Llama on Arm CPU (quantization schemes like 8da4w, group size, custom SDPA and KV cache ops, max_seq_len, shared
embeddings), and known issues; (4) how to profile ExecuTorch on device (ETDump, Inspector, devtools) and show a
per-operator time breakdown; (5) Arm's published messaging on edge AI (efficiency, privacy, offline, cost) and any
statements by Arm about what they look for in hackathon or developer-challenge projects; (6) examples of student or
startup projects Arm highlighted on its blogs or social media.

Output: a checklist of Arm-specific things we can show in 3 minutes (with the command or tool for each), a list of
the exact numbers judges will expect us to report, and links for everything.
```
