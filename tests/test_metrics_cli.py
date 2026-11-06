import os
import subprocess
import sys

from conftest import ROOT, SAMPLE, sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.metrics import (capture_env, metrics_dict, network_status, peak_rss_mb, run_card, throttle_status,
                            write_metrics)
from sakshi.pipeline import prepare

ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def test_network_status_default_route_detection(tmp_path):
    header = "Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT\n"
    off = tmp_path / "off"
    off.write_text(header + "wlan0\t002A0A0A\t00000000\t0001\t0\t0\t600\t00FFFFFF\t0\t0\t0\n")
    on = tmp_path / "on"
    on.write_text(header + "eth0\t00000000\t0101A8C0\t0003\t0\t0\t100\t00000000\t0\t0\t0\n")
    assert network_status(str(off))["status"].startswith("OFF") and network_status(str(off))["default_route"] is False
    r = network_status(str(on))
    assert r["default_route"] is True and r["status"].startswith("ON") and "eth0" in r["status"]
    assert network_status(str(tmp_path / "missing"))["known"] is False


def test_peak_memory_is_positive_and_plausible():
    assert 1 < peak_rss_mb() < 100_000


def test_throttle_is_none_off_a_pi():
    assert throttle_status() is None or isinstance(throttle_status(), dict)


def test_run_card_has_the_four_required_lines():
    run = prepare(sample_passage(), StubBackend())
    card = run_card(run)
    for label in ("Model:", "Model size:", "Peak memory:", "Time:"):
        assert label in card
    assert "network:" in card and "stub:faithful" in card


def test_run_card_names_the_runner_for_memory_and_handles_missing_env():
    run = prepare(sample_passage(), StubBackend())
    assert "this process" in run_card(run)
    run.env = {}
    assert "not recorded" in run_card(run)


def test_metrics_json_written_and_complete(tmp_path):
    run = prepare(sample_passage(), StubBackend())
    p = tmp_path / "m.json"
    write_metrics(run, str(p))
    import json
    d = json.loads(p.read_text())
    assert {"backend", "timings", "counts", "env", "gate"} <= set(d) and d["counts"]["green"] >= 3
    assert metrics_dict(run)["summary_words"] == run.summary["word_count"]


def cli(*args, stdin=None):
    return subprocess.run([sys.executable, "-m", "sakshi", *args], cwd=ROOT, env=ENV, input=stdin,
                          capture_output=True, text=True, timeout=60)


def test_cli_check(tmp_path):
    assert "OK: 224 words" in cli("check", str(SAMPLE)).stdout
    short = tmp_path / "s.txt"
    short.write_text("Too short.")
    r = cli("check", str(short))
    assert r.returncode == 1 and "REJECTED" in r.stdout


def test_cli_prepare_report_study_end_to_end(tmp_path):
    out, met = tmp_path / "run.json", tmp_path / "m.json"
    r = cli("prepare", str(SAMPLE), "--out", str(out), "--metrics", str(met))
    assert r.returncode == 0, r.stderr
    assert out.exists() and met.exists() and "Peak memory:" in r.stdout and "green" in r.stdout
    rep = cli("report", str(out))
    assert rep.returncode == 0 and "checked by rules, not by a person" in rep.stdout and "witness:" in rep.stdout
    st = cli("study", str(out), stdin="zzz\n" * 40)
    assert st.returncode == 0 and "Not quite. Read this sentence again" in st.stdout and "Worth rereading:" in st.stdout


def test_cli_prepare_rejects_a_short_passage(tmp_path):
    short = tmp_path / "s.txt"
    short.write_text("Too short.")
    r = cli("prepare", str(short), "--out", str(tmp_path / "x.json"))
    assert r.returncode == 1 and not (tmp_path / "x.json").exists()


def test_cli_executorch_needs_model_and_tokenizer(tmp_path):
    r = cli("prepare", str(SAMPLE), "--out", str(tmp_path / "x.json"), "--backend", "executorch")
    assert r.returncode != 0 and "needs --model and --tokenizer" in r.stderr and "Traceback" not in r.stderr


def test_cli_executorch_problems_are_clear_messages_not_tracebacks(tmp_path):
    gone = cli("prepare", str(SAMPLE), "--out", str(tmp_path / "x.json"), "--backend", "executorch",
               "--model", str(tmp_path / "no.pte"), "--tokenizer", str(tmp_path / "no.model"))
    assert gone.returncode != 0 and "file not found" in gone.stderr and "Traceback" not in gone.stderr
    m, tk = tmp_path / "m.pte", tmp_path / "tok.model"
    m.write_bytes(b"x")
    tk.write_bytes(b"x")
    r = cli("prepare", str(SAMPLE), "--out", str(tmp_path / "x.json"), "--backend", "executorch",
            "--model", str(m), "--tokenizer", str(tk))
    # Either the runner is not installed (ImportError message) or the fake file is rejected (RuntimeError message)
    assert r.returncode != 0 and "ExecuTorch backend is not available" in r.stderr and "Traceback" not in r.stderr


def test_cli_survives_a_closed_pipe(tmp_path):
    out = tmp_path / "run.json"
    assert cli("prepare", str(SAMPLE), "--out", str(out)).returncode == 0
    p = subprocess.Popen([sys.executable, "-m", "sakshi", "report", str(out)], cwd=ROOT, env=ENV,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p.stdout.readline()
    p.stdout.close()  # the reader leaves, like `| head -1`
    err = p.stderr.read()
    assert p.wait(timeout=30) == 0 and "Traceback" not in err
