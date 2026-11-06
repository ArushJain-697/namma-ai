import json
import os
import re
import shutil
import subprocess
import threading
import urllib.error
import urllib.request

import pytest
from conftest import ROOT, sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.pipeline import prepare
from sakshi.qr import wifi_string
from sakshi.serve import RoomCounts, WEB_DIR, build_quiz_payload, make_server

# Only three numbers in the passage, so a number answer has too few wrong options and becomes a typed (short-answer) item.
TYPED = ("The school has 120 students and every student reads daily. Each class has 30 students in it. "
         "The library holds 450 books for all the students. Students borrow books from the library every week.")


def serve(run, **kw):
    srv, counts = make_server(run, "127.0.0.1", 0, **kw)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, counts, f"http://127.0.0.1:{srv.server_address[1]}/"


def get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read(), r.headers


def post(url, data: bytes):
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def test_payload_has_only_visible_items_with_witness_and_reserve():
    run = prepare(sample_passage(), StubBackend())
    p = build_quiz_payload(run)
    assert p["items"] and all(i["witness"] and i["tier"] == "GREEN" for i in p["items"])
    assert len(p["passage_sentences"]) == 16 and p["summary"] and "trust the passage" in p["header"]
    assert any(i["reserve"] for i in p["items"])
    red = prepare(sample_passage(), StubBackend("leak"))
    assert all(i["stem"].startswith("Fill in the blank") for i in build_quiz_payload(red)["items"])  # RED never reaches a phone


def test_endpoints_and_anonymous_counts():
    srv, counts, url = serve(prepare(sample_passage(), StubBackend()))
    try:
        st, body, hd = get(url)
        assert st == 200 and b"Sakshi study aid" in body and hd["Cache-Control"] == "no-store"
        assert json.loads(get(url + "quiz.json")[1])["items"]
        assert get(url + "healthz")[1] == b"ok"
        assert post(url + "miss", json.dumps({"sentence": 3}).encode()) == 204
        assert post(url + "miss", json.dumps({"sentence": 3}).encode()) == 204
        assert json.loads(get(url + "room")[1]) == {"misses_by_sentence": {"3": 2}}
        for bad in (b"not json", json.dumps({"sentence": 999}).encode(), json.dumps({"sentence": "x"}).encode(), b"{}"):
            assert post(url + "miss", bad) == 400
        assert counts.snapshot() == {"3": 2}  # bad posts counted nothing
        with pytest.raises(urllib.error.HTTPError) as e:
            get(url + "nope")
        assert e.value.code == 404
    finally:
        srv.shutdown()


def test_default_bind_is_all_interfaces_so_phones_can_reach_it():
    import inspect
    from sakshi import serve as m
    assert inspect.signature(m.make_server).parameters["host"].default == "0.0.0.0"


def test_page_has_no_external_resources():
    html = open(os.path.join(WEB_DIR, "index.html"), encoding="utf-8").read()
    assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", html)
    assert "cdn" not in html.lower() and "googleapis" not in html and "<link" not in html
    assert "fetch(\"/quiz.json\"" in html and "innerHTML" not in html  # no HTML injection from quiz text


def test_wifi_string_escapes_special_characters():
    assert wifi_string("Sakshi", "pass1234") == "WIFI:T:WPA;S:Sakshi;P:pass1234;;"
    assert wifi_string("a;b", 'p:"w,d\\') == r'WIFI:T:WPA;S:a\;b;P:p\:\"w\,d\\;;'  # ; : , " and backslash are escaped


def test_qr_script_writes_two_svgs(tmp_path):
    pytest.importorskip("qrcode")
    import sys
    r = subprocess.run([sys.executable, "scripts/make_qr_cards.py", "--ssid", "Sakshi", "--password", "pass1234", "--out", str(tmp_path)],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0 and (tmp_path / "join_wifi.svg").read_text().startswith(("<?xml", "<svg")), r.stderr
    assert "WIFI:T:WPA;S:Sakshi;P:pass1234;;" in r.stdout


def have_browser():
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
    return r.returncode == 0


def drive(url):
    r = subprocess.run(["node", str(ROOT / "tests" / "e2e_phone.js"), url], capture_output=True, text=True, timeout=120,
                       cwd=str(ROOT), env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()})
    line = next((l for l in r.stdout.splitlines() if l.startswith(("RESULT ", "FAILED "))), "")
    assert line.startswith("RESULT "), r.stdout + r.stderr
    return json.loads(line[len("RESULT "):])


@pytest.mark.skipif(not have_browser(), reason="needs node and playwright")
@pytest.mark.parametrize("name,run_fn", [
    ("options", lambda: prepare(sample_passage(), StubBackend())),
    ("typed", lambda: prepare(TYPED, StubBackend(), gate_override=True)),
])
def test_phone_page_in_a_real_browser(name, run_fn):
    run = run_fn()
    if name == "typed":
        assert any(i.options is None for i in run.items if i.tier == "GREEN"), "fixture must exercise the typed-answer path"
    srv, counts, url = serve(run)
    try:
        r = drive(url)
    finally:
        srv.shutdown()
    assert r["external"] == [] and r["errors"] == []  # works offline: every request stayed on the Pi
    assert r["firstVerdict"].startswith("Not quite. Read this sentence again")
    assert r["firstWitnessShown"] and r["firstAnswerShown"]
    assert r["hitCount"] == 1 and r["hitText"].strip() == r["firstWitness"]  # exactly the witness sentence is highlighted
    assert all(v == "Correct" for v in r["verdicts"])  # typed "OXYGEN." and clicked answers both mark right
    if r["reserveUsable"]:
        assert r["rereadMessage"] and r["retryStemIsReserve"] and r["retryAsked"] == 1  # asks again from the same sentence
    else:  # the backup question's answer was already revealed elsewhere: never reuse it, send the student back to the sentence
        assert r["retryAsked"] == 0 and r["skippedShown"]
    assert re.match(rf"You got {r['n'] - 1} of {r['n']}\.", r["score"]) and f"sentence {r['firstWitnessIdx'] + 1}" in r["reread"]
    assert r["summaryShown"] and r["hitAfterEnd"] == 0
    assert r["room"]["misses_by_sentence"].get(str(r["firstWitnessIdx"] + 1), 0) >= 1  # the miss was counted, anonymously
    assert r["reserveUsable"] == (name == "options")  # the two fixtures exercise both Reread Loop paths
    if name == "options":
        assert r["optionsDisabled"] and r["optionsDisabled"] >= 3  # buttons lock after answering
    else:
        assert r["typed"] >= 1
