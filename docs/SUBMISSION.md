# Submission sheet: the five mandatory deliverables

*Problem Statement 1, AI for Inclusive Education. Every number here comes from a saved run, with the device and date.
Rows marked TO MEASURE are filled in on the Raspberry Pi on the day. Last updated 13 Nov 2026.*

## 1. Learning barrier, learner group, and how the PoC addresses it

**Barrier.** A student studying a textbook passage alone has no timely, understandable way to check whether they
understood it, and nobody to correct them when they did not. In a school without internet there is no online tutor,
search or AI app to fall back on, and the teacher has a whole class.

**Learner group.** Class 6-10 students in low-connectivity government schools, self-studying from English or
bilingual textbooks.

**How the PoC addresses it.** A small box with no internet turns any 150-300 word passage into:
1. a short summary in simpler words, each sentence checked against the passage sentence it came from;
2. at least three quiz questions whose answers are taken from the passage by code, never invented by the model,
   and where every answer shows the exact passage sentence that proves it.

A question is shown only if it passes rule checks *and* the model, given just that sentence, answers it with the
same key. Anything that fails is held back with its reason, and code-built fill-in-the-blank questions guarantee
the minimum of three.

*Planned extension (not part of the mandatory core): the retention engine in `src/sakshi/retention/` adds
misconception diagnosis and a spaced-revision plan on top of the same quiz.*

## 2. One passage, an approved lightweight model, ExecuTorch, locally

| | |
|---|---|
| Model | Qwen3-0.6B (instruct, thinking mode off), Apache 2.0. Organisers confirmed no model restriction; their suggestion Qwen2.5-0.5B-Instruct also runs (see below) |
| Conversion | `optimum-cli export executorch --model Qwen/Qwen3-0.6B --task text-generation --recipe xnnpack --use_custom_sdpa --use_custom_kv_cache --qlinear 8da4w --qembedding 8w --max_seq_len 1024` (4-bit weights, 8-bit dynamic activations, XNNPACK) |
| Runtime | ExecuTorch 1.5.1 `TextLLMRunner`, Python, on the device |
| Command | `python -m sakshi run PASSAGE --backend executorch --model model.pte --tokenizer tokenizer.json` |

Older ARM chips without the dot-product instructions (Cortex-A53, e.g. the Arduino UNO Q) cannot load the custom
attention kernels; for them the model is converted without `--use_custom_sdpa --use_custom_kv_cache`. The code
picks the right kernels automatically.

Memory choice: the model reserves memory for its whole context limit up front. Our longest call needs ~600 tokens,
so we export with a 1,024-token limit instead of the default 2,048: peak memory fell from 2.49 GB to 1.67 GB on the
Mac, same speed, identical answers on 8 test passages.

## 3. Short summary and at least three relevant questions, in the terminal

`python -m sakshi run PASSAGE ...` prints, on one screen: the summary, the quiz (options, answer, and the passage
sentence that proves it), then the run card. `python -m sakshi study RUN` replays it as an interactive quiz.

## 4. No cloud inference; time, model, size, memory

- **Offline evidence:** `bash scripts/prove_offline.sh TAG` (no default route, DNS, ping and HTTPS all fail).
  Arduino UNO Q, 13 Nov: `RESULT: no route out` (`results/uno-q-offline/offline_evidence.txt` on the board).
- The run card is printed after every run and written to `*_metrics.json`.

| Device | Model file | Total time | Reading (prefill) | Writing (decode) | Peak memory | Notes |
|---|---|---|---|---|---|---|
| **Raspberry Pi 5, 8 GB** (Debian 13, Python 3.13, ExecuTorch 1.5.1) | 469 MB (GURU-0.6B, 4-bit) + 469 MB (Qwen3-0.6B for the summary) | **57.9 s** for summary + 3 questions (load 3.0 s, summary 14.2 s, quiz 40.7 s); 86 s for 4 questions; 147 s before stopping each call when its answer is complete | 122 tok/s | 12.1 tok/s | 1.48 GB one model; 2.7 GB with both models loaded | 14 Nov, Wi-Fi on for SSH (offline proof to be run at the venue with Wi-Fi off); hit 84 C and throttled (0xe0008): use a fan |
| Arduino UNO Q (Cortex-A53, 4 GB) | 470 MB (portable, 1k) | 3347 s (56 min) | 9.8 tok/s | 0.37 tok/s | 1.7 GB | network OFF; 21 calls; no custom kernels on this chip, so writing is very slow; same questions word for word as on the Mac |
| Apple M4 Mac (development) | 469 MB | 20.4 s | 826 tok/s | 95 tok/s | 1.7 GB | 32 model calls, 4817 tokens in, 1376 out; 1,024-token export (the 2,048 default peaked at 2.5 GB) |

Peak memory is the whole Python process (it includes torch), so it overstates the model alone.

## 5. Impact explanation, with one concrete example from the supplied passage

*Template: replace the example with one from the organisers' passage on the day.*

A student reads the passage about rust alone, in a school with no internet. Sakshi asks
"Which structure is repainted to protect it?". If the student picks "metal", it does not just say "wrong": it shows
the passage sentence "In 1999, a town in our district repainted its old iron bridge to protect it." and asks again
from that sentence. The student finds the answer in their own textbook, in seconds, with no teacher and no
connection. Because every answer is tied to a passage sentence, the tool cannot teach a "fact" the passage does not
contain, which matters most for the student who cannot yet tell the difference.

## What is not claimed

No student has used it; no learning gain is claimed. English only. Question quality is limited at 0.6B parameters:
many model-written questions are held back and replaced by fill-in-the-blank questions (fine-tuning is the planned
fix).
