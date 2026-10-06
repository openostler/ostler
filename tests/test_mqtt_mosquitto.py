# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Conformance of the stdlib MQTT 5 client against a real Mosquitto (NodeSource spec §12,
§13: the fallback to paho is taken only if this fails). Marked ``needs_broker``: it runs
where a ``mosquitto`` binary is installed and is skipped otherwise; with
``OSTLER_REQUIRE_BROKER=1`` (the CI ``broker`` job) a missing binary fails instead, so
that job can never pass by skipping."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time

import pytest

from openostler.mqtt import StdlibMqttClient, SubOptions, Will, codec

pytestmark = pytest.mark.needs_broker
REQUIRE_ENV = "OSTLER_REQUIRE_BROKER"


def mosquitto_binary() -> "str | None":
    """``mosquitto`` on PATH, or the Debian/Ubuntu package's ``/usr/sbin/mosquitto``."""
    found = shutil.which("mosquitto")
    if found is None and os.access("/usr/sbin/mosquitto", os.X_OK):
        found = "/usr/sbin/mosquitto"
    return found


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def mosquitto(tmp_path_factory):
    binary = mosquitto_binary()
    if binary is None:
        if os.environ.get(REQUIRE_ENV, "").strip() not in ("", "0"):
            pytest.fail(f"{REQUIRE_ENV} is set but there is no mosquitto binary")
        pytest.skip("needs a mosquitto binary (Mosquitto 2.x)")
    port = _free_port()
    conf = tmp_path_factory.mktemp("mosq") / "m.conf"
    conf.write_text(f"listener {port} 127.0.0.1\nallow_anonymous true\npersistence false\n")
    proc = subprocess.Popen([binary, "-c", str(conf)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    end = time.monotonic() + 5
    while time.monotonic() < end:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
    yield ("127.0.0.1", port)
    proc.terminate()
    proc.wait(timeout=5)


def _wait(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not cond():
        time.sleep(0.01)
    return cond()


def test_retained_flags_no_local_and_qos1(mosquitto):
    host, port = mosquitto
    node = StdlibMqttClient("conf-node", timeout=3)
    node.connect(host, port)
    node.publish("conf/v/node/status", b"online", qos=1, retain=True)
    brain = StdlibMqttClient("conf-brain", timeout=3)
    got = []
    brain.on_message = got.append
    brain.connect(host, port)
    assert brain.subscribe([SubOptions("conf/v/+/status", qos=1, no_local=True)]) == [1]
    assert _wait(lambda: len(got) == 1) and got[0].retain is True
    node.publish("conf/v/node/status", b"again", qos=1, retain=True)
    assert _wait(lambda: len(got) == 2) and got[1].retain is False and got[1].qos == 1
    brain.publish("conf/v/brain/status", b"self", qos=1)
    time.sleep(0.2)
    assert len(got) == 2  # No Local
    node.publish("conf/v/node/status", b"", qos=1, retain=True)  # clean up
    node.disconnect()
    brain.disconnect()


def test_will_on_abort(mosquitto):
    host, port = mosquitto
    watcher = StdlibMqttClient("conf-w", timeout=3)
    got = []
    watcher.on_message = got.append
    watcher.connect(host, port)
    watcher.subscribe([SubOptions("conf/w/+/status", qos=1)])
    n = StdlibMqttClient("conf-n", timeout=3,
                         will=Will("conf/w/n/status", b"offline", qos=1, retain=True))
    n.connect(host, port)
    n.abort()
    assert _wait(lambda: [m.payload for m in got] == [b"offline"])
    watcher.publish("conf/w/n/status", b"", qos=1, retain=True)
    watcher.disconnect(codec.SUCCESS)


def test_a_resumed_session_delivers_queued_qos1(mosquitto):
    """The tap connection's shape (spec §4, P2): session expiry 60 s and a resume without
    clean start deliver the QoS 1 batches published while it was away; an unsubscribe
    then a normal disconnect leaves nothing queued for the next clean start."""
    host, port = mosquitto
    topic = "conf/t/node/tap/01M48AFR80CDXA0ZQ1XBS3VHSS/data"
    node = StdlibMqttClient("conf-tap-node", timeout=3)
    node.connect(host, port)
    got = []
    tap = StdlibMqttClient("conf-tap", timeout=3, clean_start=True, session_expiry=60)
    tap.on_message = got.append
    tap.connect(host, port)
    assert tap.subscribe([SubOptions("conf/t/+/tap/+/data", qos=1, no_local=True)]) == [1]
    node.publish(topic, b"\x01", qos=1)
    assert _wait(lambda: [m.payload for m in got] == [b"\x01"])
    tap.abort()                                   # a network loss
    node.publish(topic, b"\x02", qos=1)           # queued by the broker
    tap.clean_start = False
    ack = tap.connect(host, port)
    assert ack.session_present is True
    assert _wait(lambda: [m.payload for m in got] == [b"\x01", b"\x02"])
    assert all(m.qos == 1 and not m.retain for m in got)
    tap.unsubscribe(["conf/t/+/tap/+/data"])
    tap.disconnect()
    node.publish(topic, b"\x03", qos=1)
    fresh = StdlibMqttClient("conf-tap", timeout=3, clean_start=True, session_expiry=60)
    later = []
    fresh.on_message = later.append
    assert fresh.connect(host, port).session_present is False
    time.sleep(0.3)
    assert later == []
    fresh.disconnect()
    node.disconnect()


# ---- mTLS and the per-device ACL (spec §5) ------------------------------------------- #
ACL_VID = "d2-bench"


def _openssl(*args, cwd):
    subprocess.run(["openssl", *args], cwd=cwd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def _issue(d, name, cn, san=None):
    """An EC key and a certificate for ``cn`` signed by the test CA in ``d``."""
    _openssl("req", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
             "-subj", f"/CN={cn}", "-keyout", f"{name}.key", "-out", f"{name}.csr", cwd=d)
    ext = d / f"{name}.ext"
    ext.write_text(f"subjectAltName={san}\n" if san else "basicConstraints=CA:FALSE\n")
    _openssl("x509", "-req", "-in", f"{name}.csr", "-CA", "ca.crt", "-CAkey", "ca.key",
             "-CAcreateserial", "-out", f"{name}.crt", "-days", "1", "-extfile", ext.name, cwd=d)
    return str(d / f"{name}.crt"), str(d / f"{name}.key")


@pytest.fixture(scope="module")
def mosquitto_tls(tmp_path_factory):
    binary = mosquitto_binary()
    missing = None if binary else "there is no mosquitto binary"
    if shutil.which("openssl") is None:
        missing = "there is no openssl binary (to make the test certificates)"
    if missing:
        if os.environ.get(REQUIRE_ENV, "").strip() not in ("", "0"):
            pytest.fail(f"{REQUIRE_ENV} is set but {missing}")
        pytest.skip(missing)
    d = tmp_path_factory.mktemp("mosq-tls")
    _openssl("req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
             "-nodes", "-subj", "/CN=ostler-test-ca", "-keyout", "ca.key", "-out", "ca.crt",
             "-days", "1", cwd=d)
    server = _issue(d, "server", "localhost", san="IP:127.0.0.1")
    certs = {"ca": str(d / "ca.crt"), "brain": _issue(d, "brain", "t-nodesource"),
             "node": _issue(d, "node", "node")}
    acl = d / "acl"
    acl.write_text(
        "user t-nodesource\n" + "".join(
            f"topic read ostler/v1/{ACL_VID}/+/{t}\n"
            for t in ("status", "power", "vss/+", "tap/+/meta", "tap/+/data"))
        + f"\nuser node\ntopic readwrite ostler/v1/{ACL_VID}/node/#\n")
    port = _free_port()
    conf = d / "m.conf"
    # Started as root (a container), Mosquitto drops to the "mosquitto" user, which cannot
    # read the test's private files: stay root there.
    root = "user root\n" if hasattr(os, "geteuid") and os.geteuid() == 0 else ""
    conf.write_text(f"{root}per_listener_settings false\nlistener {port} 127.0.0.1\n"
                    f"cafile {d / 'ca.crt'}\ncertfile {server[0]}\nkeyfile {server[1]}\n"
                    "require_certificate true\nuse_identity_as_username true\n"
                    f"acl_file {acl}\npersistence false\n")
    proc = subprocess.Popen([binary, "-c", str(conf)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    end = time.monotonic() + 5
    while time.monotonic() < end:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
    yield ("127.0.0.1", port, certs)
    proc.terminate()
    proc.wait(timeout=5)


def test_mtls_acl_and_the_tap_subscription(mosquitto_tls):
    """NodeSource over mTLS on a real Mosquitto with the spec §5 ACL: the read set and the
    tap filters are granted, ``tap/ctl`` and other vehicles are refused, the will and the
    retained state arrive, and a client with no certificate cannot connect."""
    from openostler.mqtt import tls_context
    from openostler.web.node_source import NodeFeed

    host, port, certs = mosquitto_tls
    node = StdlibMqttClient("node", timeout=3, ssl_context=tls_context(certs["ca"], *certs["node"]),
                            will=Will(f"ostler/v1/{ACL_VID}/node/status", b"offline", 1, True))
    node.connect(host, port)
    node.publish(f"ostler/v1/{ACL_VID}/node/status", b"online", 1, True)
    node.publish(f"ostler/v1/{ACL_VID}/node/power",
                 b'{"state":"awake","since_us":1,"class":"always"}', 1, True)
    logs, taps = [], []
    feed = NodeFeed(ACL_VID, host, port, client_id="t-nodesource",
                    ssl_context=tls_context(certs["ca"], *certs["brain"]), log=logs.append)
    feed.start()
    try:
        assert _wait(lambda: feed.connected, 5)
        assert _wait(lambda: feed.view(None)["device"] is not None
                     and feed.view(None)["device"]["status"] == "online", 3)
        assert feed.refused == []
        feed.start_tap(lambda *a: taps.append(a))
        assert _wait(lambda: feed.tap_state()["state"] != "connecting", 5)
        session = "01M48AFR80CDXA0ZQ1XBS3VHSS"
        node.publish(f"ostler/v1/{ACL_VID}/node/tap/{session}/data", b"\x00" * 20, 1)
        assert _wait(lambda: [a[:3] for a in taps] == [("node", session, "data")])
        assert not [m for m in logs if "refused" in m]
        # Outside the read set nothing is delivered (Mosquitto grants the SUBSCRIBE and
        # filters delivery; the fake broker refuses it with 0x87): tap/ctl is never read.
        probe_got = []
        probe = StdlibMqttClient("t-nodesource-probe", timeout=3,
                                 ssl_context=tls_context(certs["ca"], *certs["brain"]))
        probe.on_message = probe_got.append
        probe.connect(host, port)
        codes = probe.subscribe([SubOptions(f"ostler/v1/{ACL_VID}/node/tap/ctl", qos=1),
                                 SubOptions(f"ostler/v1/{ACL_VID}/+/status", qos=1)])
        assert all(c in (1, 0x87) for c in codes)
        node.publish(f"ostler/v1/{ACL_VID}/node/tap/ctl", b"start", 1)
        assert _wait(lambda: [m.topic for m in probe_got] == [f"ostler/v1/{ACL_VID}/node/status"])
        time.sleep(0.3)
        assert [m.topic for m in probe_got] == [f"ostler/v1/{ACL_VID}/node/status"]
        probe.disconnect()
        node.abort()                                   # the will: offline
        assert _wait(lambda: feed.view(None)["device"]["status"] == "offline", 5)
    finally:
        feed.stop()
    anon = StdlibMqttClient("anon", timeout=3, ssl_context=tls_context(certs["ca"]))
    with pytest.raises((OSError, codec.MqttError)):
        anon.connect(host, port)
