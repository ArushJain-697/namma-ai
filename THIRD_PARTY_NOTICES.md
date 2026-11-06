# Third-party notices and provenance

*As of 4 Nov 2026. Read each licence in full before shipping; this file records what we use and what we have and have not verified.*

## Code in this repository
All source under `src/`, `scripts/`, `tests/` and `web/` was written for this project. **No third-party source code has been copied into it.**

## Ideas we credit (no code or text copied)
- **LENTERA** (MIT, Copyright 2025 Fengkie Junis): the idea of small, plain-language summarisation prompts that keep numbers and names. Our prompts are our own wording. If wording is ever copied closely, keep its MIT notice.
- **Toddle AI** (MIT): the principle of code computing facts and the model only explaining them.
- Prior work on knowledge conflict / context faithfulness (Xie et al. 2023, arXiv 2305.13300, and related), for the counterfactual-passage idea. **Read from search snippets only, not yet read in full.**

## Runtime dependencies (installed by the user, not vendored)
| Package | Used for | Licence |
|---|---|---|
| `executorch` 1.5.1 | the on-device runner | BSD-3 (per its package metadata; confirm in the wheel's LICENSE) |
| `torch`, `numpy`, `tqdm`, `typing_extensions` | imported by the ExecuTorch runner | see each package's own licence file |
| `pytest` (development only) | tests | MIT |
| `qrcode` (optional, development only) | printing QR cards | see package |

## Model weights
- **Llama 3.2 1B Instruct** (community SpinQuant `.pte`): governed by **Meta's Llama 3.2 Community Licence**, which is not MIT or BSD. **UNVERIFIED: we have not read Meta's licence page.** It likely requires a "Built with Llama" notice and has an acceptable-use policy. Do not redistribute the `.pte` from this repository; link to it. Build map ticket 8h.

## Test and sample data
`data/passages/rust_ordinary.txt` and everything under `data/counterfactual/` are original text written for this project. NCERT text is **not** used.
