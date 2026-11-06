# Counterfactual passages

Each case is a 150-300 word passage in which **one fact differs from what a language model "remembers"**, so the case
exposes whether an answer follows the passage or the model's memory. Format and rules: see `sakshi/counterfactual.py`.

```
<id>.txt    the passage
<id>.json   {"planted": {"sentence_idx": 5, "passage_value": "90 degrees Celsius",
                         "memory_value": "100 degrees Celsius", "type": "number"},
             "split": "dev" | "heldout", "note": "..."}
```
`sentence_idx` is 0-based as `sakshi.text.split_sentences` splits it. Files whose names start with `_` are ignored
(`_example_boiling.*` shows the format; `_template.json` is a blank).

## Writing good cases
- The planted sentence must contain the passage value; it must NOT contain the memory value.
- Prefer the memory value to appear NOWHERE in the passage (otherwise a plain "is the answer in the passage?" check
  would not catch a memory answer; `scripts/trap_check.py` prints a note when that happens).
- True-but-surprising facts work well (boiling point at altitude), and so do local facts a model cannot know
  (a year, a name, a month in a village story).
- Aim for 16-20 cases: half `dev`, half `heldout`. **The held-out half is written and kept by ONE person who never
  tunes prompts or weights; nobody else looks at it until the final run.**

## Workflow
```
python scripts/trap_check.py --cases data/counterfactual [backend args]     # validates; dev half only; writes kept_dev.json
python scripts/counterfactual_eval.py --cases data/counterfactual --kept data/counterfactual/kept_dev.json [backend args]
python scripts/proof_card.py
```
The dev half is filtered to facts that really trap the baseline; the held-out half is NEVER filtered.
