"""The saved villain for the demo (build map T33): one REAL baseline failure, kept as evidence.

Integrity rule: a villain can only be built from a case where the baseline actually answered from memory. If it did
not, building refuses, so a failure can never be staged. The saved file says SAVED RUN, and says SIMULATED if a stub
produced it, so it cannot be mistaken for a live or real result.
"""
from __future__ import annotations

import json
import time

from .cf_eval import evaluate_case
from .counterfactual import Case


class NotAVillain(Exception):
    pass


def build_villain(case: Case, baseline_backend, sakshi_backend, gate_override: bool = False) -> dict:
    rec = evaluate_case(case, baseline_backend, sakshi_backend, gate_override)
    t = rec["targeted"]
    if t["class"] != "memory":
        raise NotAVillain(f"the baseline's answer was classed {t['class']!r}, not 'memory': this case does not show the "
                          "trap, so it cannot be a saved villain. Pick another case (scripts/trap_check.py lists them).")
    s = rec["sakshi"]
    b_info, s_info = baseline_backend.info(), sakshi_backend.info()
    return {"label": "SAVED RUN", "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "case": case.id,
            "simulated": any(str(i.get("name", "")).startswith("stub") for i in (b_info, s_info)),
            "passage": case.passage, "planted_sentence": case.sentence, "passage_value": case.passage_value,
            "memory_value": case.memory_value,
            "baseline": {"question": t["question"], "answer": t["answer"], "class": t["class"], "backend": b_info},
            "sakshi": {"stem": (s["item"] or {}).get("stem"), "key": (s["item"] or {}).get("key"),
                       "witness": (s["item"] or {}).get("witness"), "class": s["class"], "backend": s_info}}


def render(v: dict) -> str:
    out = []
    if v.get("simulated"):
        out.append("*** SIMULATED: produced with a stub model, NOT a real result. Do not show this as evidence. ***")
    out += [f"{v['label']}: chosen BECAUSE the baseline failed on it; this is not a live run ({v['created']}).", "",
            f"The passage says:   {v['planted_sentence']}", "",
            "A quiz generator that writes the question AND the answer in one go:",
            f"  Q: {v['baseline']['question']}",
            f"  A: {v['baseline']['answer']}      <- from the model's MEMORY ({v['memory_value']}), not the passage ({v['passage_value']})", "",
            "Sakshi: code picks the answer from the passage; the model only words the question:",
            f"  Q: {v['sakshi']['stem']}",
            f"  A: {v['sakshi']['key']}      <- from the passage",
            f"  Witness: \"{v['sakshi']['witness']}\""]
    return "\n".join(out)


def save(v: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(v, f, indent=2, ensure_ascii=False)
