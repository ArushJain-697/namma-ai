import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

import pytest
from conftest import ROOT, sample_passage
from sakshi.backends.stub import StubBackend
from sakshi.pipeline import prepare
from sakshi.resident import MAX_SOCKET_PATH, ResidentClient, ResidentServer, probe_network

ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


@pytest.fixture
def sock_path():
    d = tempfile.mkdtemp(prefix="sk", dir="/tmp")
    yield os.path.join(d, "m.sock")
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def server(sock_path):
    srv = ResidentServer(StubBackend(), sock_path)
    srv.start()
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.close()


def test_ping_info_generate_roundtrip(server, sock_path):
    c = ResidentClient(sock_path)
    assert c.ping() and c.info()["name"] == "stub:faithful" and c.info()["resident_socket"] == sock_path
    r = c.generate("p", task="simplify", payload={"sentence": "Iron rusts."})
    assert r.text == "Iron rusts." and r.new_tokens == 2
    c.close()


def test_pipeline_through_the_socket_matches_direct_run(server, sock_path):
    c = ResidentClient(sock_path)
    via = prepare(sample_passage(), c)
    direct = prepare(sample_passage(), StubBackend())
    assert [(i.stem, i.key, i.options, i.tier) for i in via.items] == [(i.stem, i.key, i.options, i.tier) for i in direct.items]
    assert via.backend["resident_socket"] == sock_path
    c.close()


def test_several_clients_at_once_are_serialised_safely(server, sock_path):
    results, errors = [], []

    def work(n):
        try:
            c = ResidentClient(sock_path)
            for k in range(5):
                results.append(c.generate("p", task="simplify", payload={"sentence": f"Sentence {n} {k}."}).text)
            c.close()
        except Exception as e:  # pragma: no cover
            errors.append(e)

    ts = [threading.Thread(target=work, args=(n,)) for n in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors and len(results) == 20 and len(set(results)) == 20


def test_bad_requests_do_not_kill_the_process(server, sock_path):
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock_path)
    f = s.makefile("rwb")
    for raw in (b"not json\n", b'{"op":"nope"}\n', b'{"op":"generate"}\n'):
        f.write(raw)
        f.flush()
        assert json.loads(f.readline())["ok"] is False
    f.write(b'{"op":"ping"}\n')
    f.flush()
    assert json.loads(f.readline())["ok"] is True  # still alive after three bad requests
    s.close()


def test_shutdown_op_stops_the_server(sock_path):
    srv = ResidentServer(StubBackend(), sock_path)
    srv.start()
    t = threading.Thread(target=srv.serve_forever)
    t.start()
    c = ResidentClient(sock_path)
    c.shutdown()
    t.join(timeout=5)
    assert not t.is_alive() and not os.path.exists(sock_path)


def test_socket_path_too_long_is_a_clear_error():
    with pytest.raises(ValueError, match="too long"):
        ResidentServer(StubBackend(), "/tmp/" + "x" * (MAX_SOCKET_PATH + 5))


def test_probe_reports_this_machine_honestly():
    p = probe_network(timeout=0.3)
    assert p["interfaces"] and "tcp_probe_1.1.1.1:53" in p
    assert p["isolated"] is False  # the test runner has a network interface


def can_unshare():
    return subprocess.run(["unshare", "-n", "true"], capture_output=True).returncode == 0


def start_resident(sock_path, isolated):
    cmd = ([ "unshare", "-n"] if isolated else []) + [sys.executable, "-m", "sakshi", "resident", "--socket", sock_path]
    proc = subprocess.Popen(cmd, cwd=ROOT, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line = proc.stdout.readline()
    assert line.startswith("ready"), line + proc.stderr.read()
    return proc


@pytest.mark.skipif(not can_unshare(), reason="needs permission for `unshare -n`")
def test_model_process_in_an_empty_network_namespace_is_reachable_and_isolated(sock_path):
    proc = start_resident(sock_path, isolated=True)
    try:
        c = ResidentClient(sock_path)  # this client is OUTSIDE the namespace
        probe = c.probe_network()
        assert probe["isolated"] is True, probe
        assert set(probe["interfaces"]) <= {"lo"} and probe["default_route"] is False
        assert probe["tcp_probe_1.1.1.1:53"].startswith("failed")
        run = prepare(sample_passage(), c)  # the whole pipeline works through the socket
        assert run.counts["green"] >= 3
        c.shutdown()
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.mark.skipif(not can_unshare(), reason="needs permission for `unshare -n`")
def test_control_run_without_isolation_is_NOT_reported_isolated(sock_path):
    """The probe must be able to say 'not isolated', or the isolated result above proves nothing."""
    proc = start_resident(sock_path, isolated=False)
    try:
        c = ResidentClient(sock_path)
        probe = c.probe_network()
        assert probe["isolated"] is False and len(probe["interfaces"]) > 1 or probe["default_route"] is True
        c.shutdown()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
