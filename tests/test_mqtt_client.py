# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The stdlib MQTT 5 client against the in-process fake broker (NodeSource spec §5, §12,
§13): subscription options, retained and live delivery, QoS 1, wills, keep-alive,
reconnect with back-off, the ACL, session expiry and mTLS."""
from __future__ import annotations

import shutil
import socket
import ssl
import subprocess
import threading
import time

import pytest

from openostler.mqtt import StdlibMqttClient, SubOptions, Will, codec, tls_context
from openostler.mqtt.codec import MqttError, PacketReader
from tests.fake_broker import FakeBroker, filter_covers


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return cond()


class Inbox:
    def __init__(self, client):
        self.msgs = []
        client.on_message = self.msgs.append

    def topics(self):
        return [(m.topic, m.payload, m.retain) for m in self.msgs]


@pytest.fixture
def broker():
    b = FakeBroker().start()
    yield b
    b.stop()


def client(broker, cid, **kw):
    c = StdlibMqttClient(cid, timeout=2.0, **kw)
    c.connect(broker.host, broker.port)
    return c


def test_connect_subscribe_and_qos1_publish(broker):
    a, b = client(broker, "a"), client(broker, "b")
    inbox = Inbox(b)
    assert b.subscribe([SubOptions("x/#", qos=1)]) == [1]
    assert b.subscribe([SubOptions("y", qos=0)]) == [0]
    assert a.publish("x/1", b"one", qos=1) == codec.SUCCESS
    assert a.publish("z", b"nobody", qos=1) == codec.NO_MATCHING_SUBSCRIBERS
    a.publish("y", b"two", qos=0)
    assert wait_for(lambda: len(inbox.msgs) == 2)
    assert [(m.topic, m.qos) for m in inbox.msgs] == [("x/1", 1), ("y", 0)]
    # the client acked the QoS 1 delivery
    assert wait_for(lambda: any(cid == "b" and isinstance(p, codec.Puback)
                                for cid, p in broker.received))
    a.disconnect()
    b.disconnect()


def test_retained_at_subscribe_vs_live_with_rap_off(broker):
    """Retain As Published off: a stored value at subscribe time carries the retain flag, a
    live retained publish arrives with it cleared (spec §4, §6.4)."""
    node = client(broker, "node")
    node.publish("s/status", b"online", qos=1, retain=True)
    brain = client(broker, "brain")
    inbox = Inbox(brain)
    brain.subscribe([SubOptions("s/+", qos=1, retain_as_published=False)])
    assert wait_for(lambda: len(inbox.msgs) == 1)
    node.publish("s/status", b"still", qos=1, retain=True)
    assert wait_for(lambda: len(inbox.msgs) == 2)
    assert inbox.topics() == [("s/status", b"online", True), ("s/status", b"still", False)]
    # with Retain As Published on, the live flag is kept
    other = client(broker, "rap")
    rap = Inbox(other)
    other.subscribe([SubOptions("s/+", qos=1, retain_as_published=True, retain_handling=2)])
    node.publish("s/status", b"again", qos=1, retain=True)
    assert wait_for(lambda: len(rap.msgs) == 1)
    assert rap.topics() == [("s/status", b"again", True)]  # handling 2: no stored copy first


def test_no_local_and_retain_handling(broker):
    c = client(broker, "c")
    inbox = Inbox(c)
    broker.inject("r/t", b"stored", retain=True)
    c.subscribe([SubOptions("r/#", no_local=True, retain_handling=1)])
    assert wait_for(lambda: len(inbox.msgs) == 1)
    c.subscribe([SubOptions("r/#", no_local=True, retain_handling=1)])  # not new: no copy
    c.publish("r/t", b"mine")                                           # No Local: not back
    broker.inject("r/t", b"theirs")
    assert wait_for(lambda: len(inbox.msgs) == 2)
    time.sleep(0.1)
    assert [m.payload for m in inbox.msgs] == [b"stored", b"theirs"]
    broker.inject("r/t", b"", retain=True)  # an empty retained payload deletes
    assert "r/t" not in broker.retained


def test_will_on_network_loss_not_on_clean_disconnect(broker):
    watcher = client(broker, "w")
    inbox = Inbox(watcher)
    watcher.subscribe([SubOptions("n/+/status", qos=1)])
    will = Will("n/a/status", b"offline", qos=1, retain=True)
    a = client(broker, "a", will=will)
    a.abort()
    assert wait_for(lambda: [m.payload for m in inbox.msgs] == [b"offline"])
    assert broker.retained["n/a/status"][0].payload == b"offline"
    b = client(broker, "b", will=Will("n/b/status", b"offline", qos=1, retain=True))
    b.disconnect()
    time.sleep(0.2)
    assert [m.topic for m in inbox.msgs] == ["n/a/status"]
    c = client(broker, "c", will=Will("n/c/status", b"offline", qos=1, retain=True))
    c.disconnect(codec.DISCONNECT_WITH_WILL)
    assert wait_for(lambda: [m.topic for m in inbox.msgs] == ["n/a/status", "n/c/status"])


def test_client_sends_pings_and_honours_server_keep_alive():
    with FakeBroker(server_keep_alive=1) as b:
        c = StdlibMqttClient("k", keep_alive=60, timeout=2.0)
        ack = c.connect(b.host, b.port)
        assert ack.properties["server_keep_alive"] == 1
        assert wait_for(lambda: sum(isinstance(p, codec.Pingreq) for _, p in b.received) >= 2,
                        timeout=4.0)
        assert c.connected
        c.disconnect()


def test_client_drops_a_silent_broker():
    """No PINGRESP within 1.5 × keep-alive: the connection is dropped."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    held = []

    def mute():
        s, _ = srv.accept()
        held.append(s)
        r = PacketReader()
        while not r.feed(s.recv(4096)):
            pass
        s.sendall(codec.encode(codec.Connack()))  # then never answers again

    threading.Thread(target=mute, daemon=True).start()
    c = StdlibMqttClient("m", keep_alive=1, timeout=2.0)
    reasons = []
    c.on_disconnect = reasons.append
    c.connect("127.0.0.1", port)
    assert wait_for(lambda: not c.connected, timeout=5.0)
    # ``connected`` drops before ``on_disconnect`` runs on the reader thread.
    assert wait_for(lambda: reasons, timeout=2.0)
    assert "keep-alive" in reasons[0]
    srv.close()


def test_broker_drops_a_silent_client_and_publishes_its_will():
    clock = {"t": 0.0}
    with FakeBroker(clock=lambda: clock["t"], ticker=False) as b:
        w = client(b, "w", keep_alive=0)  # the watcher itself never times out
        inbox = Inbox(w)
        w.subscribe([SubOptions("st")])
        raw = socket.create_connection((b.host, b.port))
        raw.sendall(codec.encode(codec.Connect("silent", keep_alive=10,
                                               will=Will("st", b"offline"))))
        assert wait_for(lambda: "silent" in b.connected_clients())
        clock["t"] = 14.0
        b.tick()
        assert "silent" in b.connected_clients()
        clock["t"] = 15.1  # past 1.5 × 10 s
        b.tick()
        assert wait_for(lambda: [m.payload for m in inbox.msgs] == [b"offline"])
        raw.close()


def test_connack_refusal_raises_with_the_reason():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def refuse():
        s, _ = srv.accept()
        s.recv(4096)
        s.sendall(codec.encode(codec.Connack(codec.NOT_AUTHORIZED)))
        s.close()

    threading.Thread(target=refuse, daemon=True).start()
    with pytest.raises(MqttError) as e:
        StdlibMqttClient("r", timeout=2.0).connect("127.0.0.1", srv.getsockname()[1])
    assert e.value.code == codec.NOT_AUTHORIZED
    srv.close()


def test_reconnects_with_backoff_and_resubscribes():
    b = FakeBroker().start()
    port = b.port
    c = StdlibMqttClient("brain", timeout=1.0, backoff=(0.05, 0.4))
    connects = []
    inbox = Inbox(c)

    def on_connect(ack):
        c.subscribe([SubOptions("v/#")])
        connects.append(ack)

    c.on_connect = on_connect
    c.start(b.host, port)
    assert wait_for(lambda: len(connects) == 1)
    b.kill("brain")
    assert wait_for(lambda: len(connects) == 2)
    b.inject("v/x", b"after")
    assert wait_for(lambda: [m.payload for m in inbox.msgs] == [b"after"])
    b.stop()
    assert wait_for(lambda: not c.connected)
    time.sleep(0.3)
    assert c.last_error and "Refused" in c.last_error
    c.stop()
    assert not c.connected


def test_backoff_is_jittered_and_capped():
    import random

    c = StdlibMqttClient("b", rng=random.Random(1))
    delay, seen = 1.0, []
    for _ in range(8):
        wait, nxt = c.next_backoff(delay)
        assert delay / 2 <= wait <= delay
        seen.append(nxt)
        delay = nxt
    assert seen == [2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0, 30.0]


def test_acl_refuses_reads_and_writes_outside_the_table():
    acl = {"brain": {"read": ["ostler/v1/v/+/status", "ostler/v1/v/+/vss/+"],
                     "write": ["ostler/v1/v/brain/act/+"]}}
    with FakeBroker(acl=acl, default_deny=True) as b:
        c = client(b, "brain")
        codes = c.subscribe([SubOptions("ostler/v1/v/+/status"), SubOptions("ostler/v1/v/#"),
                             SubOptions("ostler/v1/v/node/lab/req"),
                             SubOptions("ostler/v1/v/other/act/+")])
        assert codes == [0, codec.NOT_AUTHORIZED, codec.NOT_AUTHORIZED, codec.NOT_AUTHORIZED]
        assert c.publish("ostler/v1/v/node/vss/Vehicle.Speed", b"1", qos=1) == codec.NOT_AUTHORIZED
        assert c.publish("ostler/v1/v/brain/act/01J", b"{}", qos=1) == codec.NO_MATCHING_SUBSCRIBERS


def test_filter_covers():
    assert filter_covers("a/+/c", "a/b/c") and filter_covers("a/#", "a/+/c")
    assert not filter_covers("a/+/c", "a/#") and not filter_covers("a/+", "a/+/c")
    assert filter_covers("a/+", "a/+") and not filter_covers("a/b", "a/+")


def test_session_expiry_queues_qos1_while_away():
    """The tap subscription's 60 s session (spec §4): QoS 1 messages wait for the client."""
    clock = {"t": 0.0}
    with FakeBroker(clock=lambda: clock["t"], ticker=False) as b:
        c = StdlibMqttClient("tap", clean_start=False, session_expiry=60, timeout=2.0)
        c.connect(b.host, b.port)
        c.subscribe([SubOptions("t/data", qos=1)])
        c.abort()
        assert wait_for(lambda: "tap" not in b.connected_clients())
        b.inject("t/data", b"batch", qos=1)
        c2 = StdlibMqttClient("tap", clean_start=False, session_expiry=60, timeout=2.0)
        inbox = Inbox(c2)
        ack = c2.connect(b.host, b.port)
        assert ack.session_present
        assert wait_for(lambda: [m.payload for m in inbox.msgs] == [b"batch"])
        c2.abort()
        assert wait_for(lambda: "tap" not in b.connected_clients())
        clock["t"] = 61.0
        b.tick()
        assert "tap" not in b.sessions  # expired


def test_message_expiry_on_retained():
    clock = {"t": 0.0}
    with FakeBroker(clock=lambda: clock["t"], ticker=False) as b:
        b.inject("w/req", b"x", qos=1, retain=True, properties={"message_expiry_interval": 120})
        clock["t"] = 30.0
        c = client(b, "c")
        inbox = Inbox(c)
        c.subscribe([SubOptions("w/#", qos=1)])
        assert wait_for(lambda: len(inbox.msgs) == 1)
        assert inbox.msgs[0].properties["message_expiry_interval"] == 90
        clock["t"] = 121.0
        b.tick()
        assert "w/req" not in b.retained


# ---- mTLS ---------------------------------------------------------------------------- #
def _openssl(*args, cwd):
    subprocess.run(["openssl", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture(scope="module")
def pki(tmp_path_factory):
    if shutil.which("openssl") is None:
        pytest.skip("openssl is not installed")
    d = tmp_path_factory.mktemp("pki")
    _openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2", "-subj", "/CN=test-ca",
             "-keyout", "ca.key", "-out", "ca.pem", cwd=d)
    for name, ext in (("server", "subjectAltName=DNS:localhost,IP:127.0.0.1"),
                      ("brain", "extendedKeyUsage=clientAuth")):
        _openssl("req", "-newkey", "rsa:2048", "-nodes", "-subj", f"/CN={name}",
                 "-keyout", f"{name}.key", "-out", f"{name}.csr", cwd=d)
        (d / f"{name}.ext").write_text(ext + "\n")
        _openssl("x509", "-req", "-in", f"{name}.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
                 "-CAcreateserial", "-days", "2", "-extfile", f"{name}.ext",
                 "-out", f"{name}.pem", cwd=d)
    return d


def _server_ctx(pki):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(pki / "server.pem", pki / "server.key")
    ctx.load_verify_locations(pki / "ca.pem")
    ctx.verify_mode = ssl.CERT_REQUIRED  # mTLS: no client certificate, no connection
    return ctx


def test_mtls_connects_with_a_client_certificate(pki):
    with FakeBroker(ssl_context=_server_ctx(pki)) as b:
        ctx = tls_context(str(pki / "ca.pem"), str(pki / "brain.pem"), str(pki / "brain.key"))
        assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2
        c = StdlibMqttClient("brain-nodesource", ssl_context=ctx, server_hostname="localhost",
                             timeout=3.0)
        inbox = Inbox(c)
        c.connect(b.host, b.port)
        c.subscribe([SubOptions("a")])
        b.inject("a", b"over tls")
        assert wait_for(lambda: [m.payload for m in inbox.msgs] == [b"over tls"])
        c.disconnect()


def test_mtls_refuses_a_client_without_a_certificate(pki):
    with FakeBroker(ssl_context=_server_ctx(pki)) as b:
        c = StdlibMqttClient("anon", ssl_context=tls_context(str(pki / "ca.pem")),
                             server_hostname="localhost", timeout=2.0)
        with pytest.raises((OSError, MqttError)):
            c.connect(b.host, b.port)


def test_tls_refuses_a_broker_signed_by_another_ca(pki, tmp_path):
    _openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2", "-subj", "/CN=other",
             "-keyout", "o.key", "-out", "other.pem", cwd=tmp_path)
    with FakeBroker(ssl_context=_server_ctx(pki)) as b:
        ctx = tls_context(str(tmp_path / "other.pem"), str(pki / "brain.pem"), str(pki / "brain.key"))
        with pytest.raises(ssl.SSLError):
            StdlibMqttClient("x", ssl_context=ctx, server_hostname="localhost",
                             timeout=2.0).connect(b.host, b.port)
