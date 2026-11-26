# Third-party notices

## Code
All source under `src/`, `scripts/`, `pi/`, `train/`, `tests/` and `web/` was written for this project. No third-party
source code is copied into it. Ideas credited: LENTERA (MIT) for plain-language summary prompts that keep numbers and
names; Toddle AI (MIT) for code computing facts while the model only explains them; Eedi's diagnostic questions for
the idea that every wrong option should reveal a misconception.

## Models
| Model | Use | Licence |
|---|---|---|
| Qwen3-0.6B (Qwen team) | base of GURU-0.6B; summary and self-check | Apache 2.0 |
| BAAI/bge-small-en-v1.5 | misconception shortlist (embedding) | MIT |
| cross-encoder/nli-MiniLM2-L6-H768 | misconception rerank (NLI) | Apache 2.0 |
| RapidOCR, PP-OCRv5 mobile models | reading a photographed page | Apache 2.0 |

## Training data
| Dataset | Licence | Note |
|---|---|---|
| SciQ (allenai/sciq) | CC BY-NC 3.0 | non-commercial |
| RACE (middle school) | research use | non-commercial research |
| Teacher dataset (`data/dataset_v2`, `data/dataset_opus`, `data/gemini_clean`) | ours, subject to provider terms | written by Anthropic Claude (Opus/Sonnet) and Google Gemini for our passages, graded against our rubric. Using model output to train another model is governed by each provider's terms of service; check them before any commercial use. |

**RACE redistribution:** several files under `data/` contain RACE passage text. RACE is released for non-commercial research and its terms may not allow redistribution; if that is confirmed, those rows must be removed from the repo and its history. Because of SciQ and RACE, the GURU-0.6B weights are for research and education, not commercial use.

## Runtime libraries
ExecuTorch 1.5.1 (BSD-3), PyTorch (BSD-3), py-fsrs (MIT), sentence-transformers (Apache 2.0), tokenizers (Apache 2.0),
NumPy (BSD-3), Pillow (MIT-CMU), OpenCV (Apache 2.0), gpiozero (BSD-3), pytest (MIT). Check each package's own
licence file before redistributing.

The Qwen3 (Apache 2.0) and bge-small (MIT) licence texts must ship next to the weights in every release; see `MODEL_CARD.md`.
