import json
import os
import subprocess
import sys

import pytest
from cf_fixtures import cases
from conftest import ROOT
from sakshi.backends.stub import StubBackend
from sakshi.villain import NotAVillain, build_villain, render

C = cases()[0]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def test_villain_built_only_from_a_real_baseline_failure():
    v = build_villain(C, StubBackend(baseline="memory"), StubBackend(), gate_override=True)
    assert v["baseline"]["class"] == "memory" and v["sakshi"]["class"] == "passage" and v["label"] == "SAVED RUN"
    with pytest.raises(NotAVillain, match="cannot be a saved villain"):
        build_villain(C, StubBackend(baseline="passage"), StubBackend(), gate_override=True)  # a failure can't be staged


def test_stub_villain_is_marked_simulated_everywhere():
    v = build_villain(C, StubBackend(baseline="memory"), StubBackend(), gate_override=True)
    assert v["simulated"] is True and "SIMULATED" in render(v).splitlines()[0]
    assert "SAVED RUN" in render(v) and "not a live run" in render(v)


def test_render_shows_memory_vs_passage_and_witness():
    t = render(build_villain(C, StubBackend(baseline="memory"), StubBackend(), gate_override=True))
    assert "100 degrees Celsius" in t and "90 degrees Celsius" in t and "Witness:" in t and "MEMORY" in t


def test_cli_villain_and_script(tmp_path):
    d = tmp_path / "cf"
    d.mkdir()
    for c in cases():
        (d / f"{c.id}.txt").write_text(c.passage)
        (d / f"{c.id}.json").write_text(json.dumps({"planted": {"sentence_idx": c.sentence_idx, "passage_value": c.passage_value,
                                                                 "memory_value": c.memory_value, "type": c.type}, "split": c.split}))
    out = tmp_path / "v.json"
    r = subprocess.run([sys.executable, "scripts/save_villain.py", "--cases", str(d), "--out", str(out), "--allow-short"],
                       cwd=ROOT, env=ENV, capture_output=True, text=True)
    assert r.returncode == 0 and out.exists() and "SAVED RUN" in r.stdout, r.stdout + r.stderr
    shown = subprocess.run([sys.executable, "-m", "sakshi", "villain", str(out)], cwd=ROOT, env=ENV, capture_output=True, text=True)
    assert shown.returncode == 0 and "SIMULATED" in shown.stdout
    r = subprocess.run([sys.executable, "scripts/save_villain.py", "--cases", str(d), "--out", str(tmp_path / "x.json"),
                        "--allow-short", "--stub-baseline", "passage"], cwd=ROOT, env=ENV, capture_output=True, text=True)
    assert r.returncode != 0 and not (tmp_path / "x.json").exists() and "NO-GO" in r.stderr
