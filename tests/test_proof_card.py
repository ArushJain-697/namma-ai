import csv
import json
import os
import subprocess
import sys

import pytest
from cf_fixtures import cases
from conftest import ROOT, SAMPLE, sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.cf_eval import evaluate
from sakshi.pipeline import prepare
from sakshi.proof import render_card

PASSAGES = {"rust": sample_passage()}
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def fill(path, col_prefix, values):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    col = next(k for k in rows[0] if k.startswith(col_prefix))
    for r, v in zip(rows, values):
        r[col] = v
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def test_proof_card_caveat_first_numbers_match_and_missing_says_not_measured():
    m = evaluate(cases(), StubBackend(baseline="memory"), StubBackend(), gate_override=True)
    card = render_card(m)
    body = card.splitlines()
    assert body[0] == "SAKSHI PROOF CARD" and any(l.startswith("CAVEAT FIRST:") for l in body)
    assert "SIMULATED" in body[1] and "stub" in card  # a stub card must never look like a real result
    dev = m["splits"]["dev"]["A_targeted"]
    assert f"{dev['memory_count']} of {dev['n']}" in card and "by construction" in card
    assert "Held-out (never filtered" in card and "not measured" in render_card(None)
    assert "Counterfactual Passage Test: not measured" in render_card(None)
    assert "Not tested: learning gains" in card


def run_script(*args, cwd=ROOT):
    return subprocess.run([sys.executable, *args], cwd=cwd, env=ENV, capture_output=True, text=True, timeout=120)


def write_cases(d):
    from cf_fixtures import cases as cs
    for c in cs():
        (d / f"{c.id}.txt").write_text(c.passage)
        (d / f"{c.id}.json").write_text(json.dumps({"planted": {"sentence_idx": c.sentence_idx, "passage_value": c.passage_value,
            "memory_value": c.memory_value, "type": c.type}, "split": c.split}))


def test_scripts_end_to_end(tmp_path):
    d = tmp_path / "cf"
    d.mkdir()
    write_cases(d)
    r = run_script("scripts/trap_check.py", "--cases", str(d), "--allow-short")
    assert r.returncode == 0 and "GO: 2 of 2" in r.stdout and (d / "kept_dev.json").exists(), r.stdout + r.stderr
    r = run_script("scripts/trap_check.py", "--cases", str(d), "--allow-short", "--stub-baseline", "passage", "--out", str(tmp_path / "k.json"))
    assert "NO-GO" in r.stdout
    out = tmp_path / "m.json"
    r = run_script("scripts/counterfactual_eval.py", "--cases", str(d), "--kept", str(d / "kept_dev.json"), "--allow-short",
                   "--out", str(out), "--d-sheet", str(tmp_path / "d.csv"))
    assert r.returncode == 0 and "CAVEAT FIRST" in r.stdout and out.exists(), r.stdout + r.stderr
    r = run_script("scripts/proof_card.py", "--cf", str(out))
    assert r.returncode == 0 and "SAKSHI PROOF CARD" in r.stdout


def test_scripts_refuse_invalid_cases(tmp_path):
    d = tmp_path / "cf"
    d.mkdir()
    write_cases(d)
    j = json.loads((d / "boil.json").read_text())
    j["planted"]["passage_value"] = "95 degrees"
    (d / "boil.json").write_text(json.dumps(j))
    r = run_script("scripts/trap_check.py", "--cases", str(d), "--allow-short")
    assert r.returncode == 2 and "INVALID boil" in r.stdout


def test_real_backend_card_has_no_simulated_banner():
    m = evaluate(cases(), StubBackend(), StubBackend(), gate_override=True)
    m["backends"] = {"baseline": {"name": "executorch:llama.pte"}, "sakshi": {"name": "executorch:llama.pte"}}
    card = render_card(m)
    assert "SIMULATED" not in card and "Produced with: executorch:llama.pte" in card
