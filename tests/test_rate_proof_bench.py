import csv
import json
import os
import subprocess
import sys

import pytest
from cf_fixtures import cases
from conftest import ROOT, SAMPLE, sample_passage
from sakshi import bench, rate_tools as rt
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


def test_stem_sheet_build_and_incomplete_verdict(tmp_path):
    p = str(tmp_path / "s.csv")
    n = rt.build_stem_sheet(StubBackend(), PASSAGES, p, n=20)
    assert 1 <= n <= 20
    r = rt.score_stems(p)
    assert r["rated"] == 0 and r["verdict"].startswith("INCOMPLETE")


@pytest.mark.parametrize("usable,expect", [(12, "GO"), (7, "MARGINAL"), (3, "NO-GO")])
def test_stem_verdict_thresholds(tmp_path, usable, expect):
    p = tmp_path / "s.csv"
    rows = [["c%d" % i, "w", "a", "q?", "GREEN", "", "usable" if i < usable else "nonsense"] for i in range(20)]
    rt.write_sheet(str(p), ["case_id", "witness", "answer", "generated_question", "tier", "auto_reasons", "rating (x)"], rows)
    r = rt.score_stems(str(p))
    assert r["rated"] == 20 and r["verdict"].startswith(expect), r


def test_unknown_and_blank_ratings_are_reported_not_ignored(tmp_path):
    p = tmp_path / "s.csv"
    rt.write_sheet(str(p), ["case_id", "rating (x)"], [["a", "usable"], ["b", ""], ["c", "great"]])
    r = rt.score_stems(str(p))
    assert r["rated"] == 1 and r["blank"] == 1 and r["unknown_ratings"] == ["great"]


def test_stem_cases_round_robin_across_passages():
    two = {"a": sample_passage(), "b": sample_passage()}
    cs = rt.build_stem_cases(two, n=4)
    assert [c["passage"] for c in cs] == ["a", "b", "a", "b"]


def test_summary_sheet_has_both_arms_and_scores_by_arm(tmp_path):
    p = str(tmp_path / "m.csv")
    assert rt.build_summary_sheet(StubBackend(), PASSAGES, p) == 2
    fill(p, "rating_faithful", ["yes", "no"])
    fill(p, "rating_understandable", ["mostly", "yes"])
    r = rt.score_summaries(p)
    assert r["witnessed"]["faithful_share"] == 1.0 and r["whole_passage"]["faithful_share"] == 0.0
    assert r["witnessed"]["understandable_share"] == 1.0 and "faithful first" in r["rule"]


def test_relevance_sheet_flags_top3_trivial(tmp_path):
    p = str(tmp_path / "r.csv")
    n = rt.build_relevance_sheet(PASSAGES, p)
    assert n >= 3
    fill(p, "rating", ["key_idea"] * n)
    ok = rt.score_relevance(p)
    assert ok["passes"] and ok["key_idea_share"] == 1.0
    fill(p, "rating", ["trivial"] + ["key_idea"] * (n - 1))
    bad = rt.score_relevance(p)
    assert not bad["passes"] and len(bad["top3_trivial_violations"]) == 1


def test_ablation_c_skips_fallback_and_red(tmp_path):
    run = prepare(sample_passage(), StubBackend())
    rows = rt.ablation_c_rows(run)
    assert rows and all("_____" in r["cloze_stem"] and r["cloze_leaks"] is False for r in rows)
    red = prepare(sample_passage(), StubBackend("leak"))
    assert rt.ablation_c_rows(red) == []  # every model stem failed; only fallback cloze items remain
    p = str(tmp_path / "c.csv")
    n = rt.build_ablation_c_sheet(run, p)
    fill(p, "rating", ["model"] * n)
    assert rt.score_ablation_c(p)["model_better_share"] == 1.0


def test_percentile_and_bench_with_stub():
    assert bench.percentile([], 50) is None and bench.percentile([5], 95) == 5
    assert bench.percentile([1, 2, 3, 4], 50) == 2
    b = bench.bench(sample_passage(), StubBackend(), runs=2)
    assert b["runs"] == 2 and b["warmup_run_discarded"] and b["total_s"]["n"] == 2
    assert b["model_calls_per_run"]["median"] > 0 and "not a true p95" in b["note"]
    assert "Total time per passage" in bench.render(b)


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
    r = run_script("scripts/rate.py", "stems", "build", "--passages", str(ROOT / "data/passages"), "--out", str(tmp_path / "st.csv"))
    assert r.returncode == 0 and "wrote" in r.stdout
    r = run_script("scripts/rate.py", "stems", "score", str(tmp_path / "st.csv"))
    assert "INCOMPLETE" in r.stdout
    r = run_script("scripts/pi_bench.py", "--runs", "1", "--out", str(tmp_path / "b.json"))
    assert r.returncode == 0 and "Total time per passage" in r.stdout and (tmp_path / "b.json").exists(), r.stderr


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
