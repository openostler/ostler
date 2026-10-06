# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NodeSource end to end (NodeSource spec P1, §5, §8, §10, §13): a simulated node and the
Brain's feed on the fake broker, the server's snapshot and connection states, the
contracts (OpenAPI ``Snapshot``, AsyncAPI node payloads) and the safety rules (the Brain
never touches the car, never subscribes to request topics, publishes nothing)."""
from __future__ import annotations

import ast
import json
import pathlib
import time

import pytest

from openostler.mqtt import codec
from openostler.web.node_source import NodeFeed, NodeSource, node_sources, parse_mqtt_url
from openostler.web.server import DiagServer
from tests.fake_broker import FakeBroker
from tests.fake_node import VID, FakeNode, case, load, vss_messages

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "openostler"


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return cond()


class Rig:
    """A broker, a simulated node and a server on NodeSource (fake pack modules)."""

    def __init__(self, tmp_path, *, modules=("alpha", "beta"), acl=None, lookup=None,
                 backoff=None):
        self.broker = FakeBroker(acl=acl).start()
        self.node = FakeNode(self.broker.host, self.broker.port)
        self.logs = []
        self.feed = NodeFeed(VID, self.broker.host, self.broker.port, client_id="t-nodesource",
                             pack_id="fake", lookup=lookup, log=self.logs.append)
        if backoff:
            self.feed.client._backoff = backoff
        self.srv = DiagServer(host="127.0.0.1", port=0, source=node_sources(self.feed, list(modules)),
                              active=modules[0], csv_dir=str(tmp_path), record_sessions=False,
                              geocoder=None)

    def start(self):
        self.feed.start()
        assert wait_for(lambda: self.feed.connected and "t-nodesource" in self.broker.connected_clients())
        assert wait_for(lambda: any(isinstance(p, codec.Subscribe) for c, p in self.broker.received
                                    if c == "t-nodesource"))
        return self

    def sync(self):
        """Wait until everything the node sent has reached the Brain."""
        self.node.client.publish("sync/x", b"", qos=1)
        time.sleep(0.05)

    def poll(self):
        return self.srv.poll_once()

    def close(self):
        self.srv.stop()
        self.srv.server_close()
        self.feed.stop()
        try:
            self.node.stop()
        except OSError:
            pass
        self.broker.stop()


@pytest.fixture
def rig(tmp_path):
    from openostler.pack import use_pack
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK):
        r = Rig(tmp_path)
        yield r
        r.close()


def alpha(node, value, t_us, name="alpha_speed", leaf="Vehicle.Powertrain.CombustionEngine.Speed",
          c="proven", **kw):
    node.send_vss(leaf, value, name=name, source="kline-diag/alpha/21 01", t_us=t_us, c=c,
                  unit="rpm", **kw)


# ---- states (§10) ---------------------------------------------------------------------- #
def test_waiting_for_the_node_then_connected(rig):
    rig.start()
    snap = rig.poll()
    assert (snap["status"], snap["conn"], snap["source_kind"]) == ("connecting", "connecting", "node")
    assert snap["node"]["device"] is None and snap["node"]["broker"]["connected"] is True
    rig.node.connect()
    rig.node.send(case("awake"))
    alpha(rig.node, 900, 2_000_000)
    rig.sync()
    snap = rig.poll()
    assert (snap["status"], snap["conn"]) == ("connected", "connected")
    sig = snap["signals"]["alpha_speed"]
    assert sig["v"] == 900.0 and not sig["stale"] and sig["src"] == "node/kline-diag/alpha/21 01"
    assert snap["node"]["status"] == "online" and snap["node"]["power"]["state"] == "awake"
    assert snap["faults"] == [] and snap["faults_note"] == "not read by the node yet"
    assert "vss" in snap and "Vehicle.Powertrain.CombustionEngine.Speed" in snap["vss"]


def test_retained_values_rebuild_the_state_and_stay_last_known(rig):
    rig.node.connect()
    rig.node.send(case("awake"))
    alpha(rig.node, 750, 3_000_000, ts="2026-10-06T10:00:00.000Z")
    rig.node.send(case("held"))  # QoS 1 after the values: they are stored
    rig.start()
    rig.sync()
    snap = rig.poll()
    assert snap["status"] == "connected" and snap["stale"] is True  # online, nothing live
    sig = snap["signals"]["alpha_speed"]
    assert sig["v"] == 750.0 and sig["stale"] is True and sig["age_s"] > 0
    assert snap["node"]["last_seen_utc"] is None


def test_asleep_waking_offline_and_values_are_never_zeroed(rig):
    rig.start()
    rig.node.connect()
    alpha(rig.node, 1234, 1_000_000)
    for state, status, conn in (("asleep", "asleep", "disconnected"),
                                ("waking", "connecting", "connecting"),
                                ("awake", "connected", "connected")):
        rig.node.send(case(state))
        rig.sync()
        snap = rig.poll()
        assert (snap["status"], snap["conn"]) == (status, conn), state
        assert snap["signals"]["alpha_speed"]["v"] == 1234.0
    rig.node.client.abort()  # a network loss: the broker publishes the node's will
    assert wait_for(lambda: rig.poll()["status"] == "error")
    snap = rig.poll()
    assert snap["conn"] == "lost" and snap["error"] == "Node offline"
    assert snap["node"]["status"] == "offline" and snap["signals"]["alpha_speed"]["v"] == 1234.0


def test_broker_down_then_back(tmp_path):
    from openostler.pack import use_pack
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK):
        r = Rig(tmp_path, backoff=(0.05, 0.2)).start()
        try:
            r.node.connect()
            alpha(r.node, 5, 1_000_000)
            r.sync()
            port = r.broker.port
            r.broker.stop()
            assert wait_for(lambda: r.poll()["status"] == "broker-down")
            snap = r.poll()
            assert snap["conn"] == "lost" and snap["error"] == "Brain cannot reach the broker"
            assert snap["signals"]["alpha_speed"]["v"] == 5.0  # kept with its age
            # a new broker on the same port: the feed reconnects and resubscribes
            time.sleep(0.3)
            with FakeBroker(port=port):
                assert wait_for(lambda: r.feed.connected, timeout=5)
                assert r.poll()["status"] == "connecting"  # no status from the node yet
        finally:
            r.close()


def test_battery_v_from_the_selected_vss_path(rig):
    rig.start()
    rig.node.connect()
    rig.node.send(case("awake"))
    rig.node.send_vss("Vehicle.LowVoltageBattery.CurrentVoltage", 13.9, name="sup_v",
                      source="kline-diag/beta/21 44", t_us=1_000_000, unit="V")
    rig.sync()
    assert rig.poll()["battery_v"] == 13.9


def test_selecting_a_module_only_filters_the_view(rig):
    rig.start()
    rig.node.connect()
    rig.node.send(case("awake"))
    alpha(rig.node, 1, 1_000_000)
    rig.node.send_vss("lr_d2.beta.b_field", 2, name="b_field", source="kline-diag/beta/21 02",
                      t_us=1_100_000)
    rig.sync()
    assert set(rig.poll()["signals"]) == {"alpha_speed"}
    assert rig.srv._select("beta")["ok"]
    assert set(rig.poll()["signals"]) == {"b_field"}
    assert rig.feed.connected  # the module switch did not touch the feed


def test_confidence_from_the_brains_store(tmp_path):
    from openostler.pack import use_pack
    from openostler.web.node_source import store_lookup
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK):
        r = Rig(tmp_path, lookup=store_lookup()).start()
        try:
            r.node.connect()
            r.node.send(case("awake"))
            alpha(r.node, 99999, 1_000_000)                       # proven in the store
            r.node.send_vss("fake.alpha.alpha_temp", 30, name="alpha_temp", c="proven",
                            source="kline-diag/alpha/21 02", t_us=1_000_000)  # candidate there
            r.sync()
            sigs = r.poll()["signals"]
            assert sigs["alpha_speed"]["c"] == "proven" and sigs["alpha_speed"]["s"] == "suspect"
            assert sigs["alpha_temp"]["c"] == "candidate"
            assert any("alpha.alpha_temp" in m and "pack store says candidate" in m for m in r.logs)
        finally:
            r.close()


# ---- the contracts ------------------------------------------------------------------- #
def _snapshot_validator():
    pytest.importorskip("yaml")
    from tests.test_api_contracts import OPENAPI, _load, _response_pointer, _validator

    doc = _load(OPENAPI)
    return _validator(doc, _response_pointer(doc, "/snapshot", "get", "200")), doc


def test_every_node_state_validates_against_the_openapi_snapshot(rig):
    v, _doc = _snapshot_validator()
    rig.start()
    snaps = [rig.poll()]
    rig.node.connect()
    for name in ("awake", "asleep", "waking", "awake"):
        rig.node.send(case(name))
        alpha(rig.node, 10, 1_000_000, state="idle")
        rig.node.send_vss("Vehicle.Nope", 1, name="x", source="kline-diag/alpha/21 09", t_us=1)
        rig.sync()
        snaps.append(rig.poll())
    rig.node.client.abort()
    assert wait_for(lambda: rig.poll()["status"] == "error")
    snaps.append(rig.poll())
    for snap in snaps:
        errors = list(v.iter_errors(json.loads(json.dumps(snap))))
        assert not errors, (snap["status"], [e.message for e in errors[:3]])


def test_node_payloads_match_the_asyncapi_schemas():
    pytest.importorskip("yaml")
    import jsonschema

    from tests.test_api_contracts import ASYNCAPI, OPENAPI, _load, _validator

    asy = _load(ASYNCAPI)
    msgs = asy["components"]["messages"]
    vss_v = jsonschema.Draft202012Validator(msgs["nodeVss"]["payload"])
    power_v = _validator(_load(OPENAPI), "/components/schemas/NodePower")
    status_v = jsonschema.Draft202012Validator(msgs["nodeStatus"]["payload"])
    for name in ("td5-vectors.jsonl", "slabs-vectors.jsonl", "status-power.jsonl"):
        for m in load(name):
            kind = m["topic"].split("/")[4]
            if kind == "vss":
                body = json.loads(m["payload"])
                assert not list(vss_v.iter_errors(body)), m["topic"]
                assert "boot" in body
            elif kind == "power":
                assert not list(power_v.iter_errors(json.loads(m["payload"]))), m["topic"]
            elif kind == "status":
                assert not list(status_v.iter_errors(m["payload"].decode())), m["topic"]
    for chan, sub in (("nodeStatus", "status"), ("nodePower", "power"), ("nodeVss", "vss/{leaf}")):
        assert asy["channels"][chan]["address"] == "ostler/v1/{vid}/{device}/" + sub
    assert asy["servers"]["brain-broker"]["protocolVersion"] == "5"


# ---- safety ---------------------------------------------------------------------------- #
_BUS = {"transport", "kline", "kwp2000", "can", "session", "ports", "faultscan", "modscan", "obd",
        "serial", "sniff", "commands"}


@pytest.mark.parametrize("path", sorted((SRC / "mqtt").glob("*.py")) + sorted((SRC / "node").glob("*.py"))
                         + [SRC / "web" / "node_source.py"], ids=lambda p: p.name)
def test_no_node_source_path_reaches_a_car_bus(path):
    """Spec §13: no NodeSource code path opens a serial port or calls a transport."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
        for mod in mods:
            parts = set(mod.split("."))
            assert not (parts & _BUS), f"{path.name} imports {mod}"


def test_the_brain_subscribes_read_only_and_publishes_nothing(rig):
    rig.start()
    rig.node.connect()
    alpha(rig.node, 1, 1)
    rig.sync()
    rig.poll()
    mine = [p for c, p in rig.broker.received if c == "t-nodesource"]
    filters = [s.topic_filter for p in mine if isinstance(p, codec.Subscribe) for s in p.subscriptions]
    assert filters == [f"ostler/v1/{VID}/+/status", f"ostler/v1/{VID}/+/power",
                       f"ostler/v1/{VID}/+/vss/+", f"ostler/v1/{VID}/+/manifest",
                       f"ostler/v1/{VID}/+/role/#"]
    opts = [s for p in mine if isinstance(p, codec.Subscribe) for s in p.subscriptions]
    assert all(s.no_local and not s.retain_as_published and s.retain_handling == 0 for s in opts)
    assert not [p for p in mine if isinstance(p, codec.Publish)]
    connect = next(p for p in mine if isinstance(p, codec.Connect))
    assert connect.clean_start and connect.properties.get("session_expiry_interval", 0) == 0
    assert connect.will is None and connect.username is None and connect.password is None


def test_the_spec_acl_grants_exactly_the_p1_reads(tmp_path):
    """Spec §5's per-device ACL: read the §4 filters of its own vid; write only its own
    request topics (P4). The P1 and P3 subscriptions all pass it."""
    from openostler.pack import use_pack
    from tests.fake_pack import FAKE_PACK

    acl = {"t-nodesource": {"read": [f"ostler/v1/{VID}/+/status", f"ostler/v1/{VID}/+/power",
                                     f"ostler/v1/{VID}/+/vss/+", f"ostler/v1/{VID}/+/manifest",
                                     f"ostler/v1/{VID}/+/role/#"],
                            "write": [f"ostler/v1/{VID}/brain/act/+"]},
           "node": {"read": [], "write": [f"ostler/v1/{VID}/node/#", "sync/x"]}}
    with use_pack(FAKE_PACK):
        r = Rig(tmp_path, acl=acl).start()
        try:
            r.node.connect()
            r.node.send(case("awake"))
            alpha(r.node, 3, 1)
            r.sync()
            assert r.feed.refused == [] and r.broker.refused == []
            assert r.poll()["signals"]["alpha_speed"]["v"] == 3.0
            # another vehicle's or a request topic is refused by that ACL
            assert r.feed.client.subscribe([codec.SubOptions(f"ostler/v1/{VID}/node/lab/req"),
                                            codec.SubOptions("ostler/v1/other/+/vss/+")]) == \
                [codec.NOT_AUTHORIZED, codec.NOT_AUTHORIZED]
        finally:
            r.close()


def test_bus_commands_are_refused_and_module_actions_unavailable(rig):
    rig.start()
    rig.srv.start_polling()
    for action in ("read_all_faults", "set_port", "detect_protocol", "module_scan"):
        res = rig.srv.enqueue_command({"action": action, "params": {"port": "auto"}})
        assert res["ok"] is False and res["code"] == "conflict", action
        assert "never touches the car" in res["error"]
    res = rig.srv.enqueue_command({"action": "read_block", "params": {"lids": ["01"]}}, timeout=3)
    assert res == {"ok": False, "code": "unavailable", "error": res["error"]}


def test_a_vin_shaped_vid_is_refused():
    with pytest.raises(ValueError):
        NodeFeed("SALLTGM88YA123456", "127.0.0.1", 1)


@pytest.mark.parametrize("url, want", [
    ("mqtts://brain.local", ("mqtts", "brain.local", 8883)),
    ("mqtts://brain.local:8884/", ("mqtts", "brain.local", 8884)),
    ("mqtt://127.0.0.1", ("mqtt", "127.0.0.1", 1883)),
    ("mqtts://[::1]:8883", ("mqtts", "::1", 8883)),
])
def test_parse_mqtt_url(url, want):
    assert parse_mqtt_url(url) == want


@pytest.mark.parametrize("url", ["", "http://x", "mqtts://", "brain.local:8883"])
def test_parse_mqtt_url_refuses(url):
    with pytest.raises(ValueError):
        parse_mqtt_url(url)


def test_build_feed_needs_mtls_or_an_explicit_lab_flag():
    from openostler.pack import use_pack
    from openostler.web.node_source import build_feed
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK):
        with pytest.raises(ValueError, match="mTLS"):
            build_feed("mqtts://brain.local", VID)
        with pytest.raises(ValueError, match="lab"):
            build_feed("mqtt://127.0.0.1", VID)
        feed = build_feed("mqtt://127.0.0.1:1", VID, insecure_lab=True, client_id="x")
        assert feed.client.ssl_context is None and feed.table.pack_id == "fake"


def test_the_dashboard_keeps_the_cable_and_the_node_apart(monkeypatch, capsys):
    import sys

    from openostler.pack import use_pack
    from tests.fake_pack import FAKE_PACK

    sys.path.insert(0, str(ROOT))
    from tools import dashboard

    with use_pack(FAKE_PACK):
        for argv in (["--source", "node", "--serial", "/dev/ttyUSB0", "--mqtt", "mqtts://b"],
                     ["--source", "node"],
                     ["--source", "node", "--mqtt", "mqtt://127.0.0.1"]):
            monkeypatch.setattr(sys, "argv", ["dashboard.py", *argv])
            with pytest.raises(SystemExit) as e:
                dashboard.main()
            assert e.value.code == 2, argv
    err = capsys.readouterr().err
    assert "exclude each other" in err and "needs --mqtt" in err and "lab broker" in err


def test_node_source_is_a_data_source():
    from openostler.web.sources import DataSource

    assert issubclass(NodeSource, DataSource)
    assert NodeSource.source_kind == "node" and NodeSource.touches_car is False
    assert DataSource.source_kind == "serial" and DataSource.touches_car is True


# ---- the Discovery 2 pack and the firmware's fixtures --------------------------------- #
@pytest.mark.needs_pack
def test_d2_fixtures_through_the_broker(tmp_path):
    """The UI's data from the firmware's vector runs, through the fake broker: every SLABS
    and Td5 field the node published arrives under its pack name with the node's value."""
    pytest.importorskip("d2diag")
    from openostler.metrics import is_known
    from openostler.pack import active_pack
    from openostler.web.node_source import store_lookup

    pack = active_pack()
    assert pack.id == "lr_d2"
    with FakeBroker() as b:
        node = FakeNode(b.host, b.port).connect()
        logs = []
        feed = NodeFeed(VID, b.host, b.port, client_id="d2-nodesource", pack_id=pack.id,
                        lookup=store_lookup(), canonical=pack.canonical, is_known=is_known,
                        log=logs.append)
        feed.start()
        assert wait_for(lambda: feed.connected)
        time.sleep(0.1)
        node.send(case("awake"))
        last = {}
        for m in vss_messages():
            node.send(m)
            body = json.loads(m["payload"])
            last[(body["source"].split("/")[1], body["name"])] = body
        node.client.publish("sync/x", b"", qos=1)
        time.sleep(0.1)
        srcs = node_sources(feed, pack.module_ids())
        srv = DiagServer(host="127.0.0.1", port=0, source=srcs, active="slabs",
                         csv_dir=str(tmp_path), record_sessions=False, geocoder=None)
        try:
            for module in ("td5", "slabs"):
                assert srv._select(module)["ok"]
                snap = srv.poll_once()
                assert snap["status"] == "connected" and snap["source_kind"] == "node"
                want = {n: b for (mod, n), b in last.items() if mod == module}
                assert set(snap["signals"]) == set(want)
                for name, body in want.items():
                    sig = snap["signals"][name]
                    assert sig["v"] == float(body["value"]) and sig["u"] == body["unit"]
                    assert sig["c"] in ("proven", "candidate")
                    if body["c"] == "candidate":
                        assert sig["c"] == "candidate"  # never raised
            assert not [m for m in logs if "names pack" in m]  # the node uses lr_d2 now
            assert not [m for m in logs if "unknown VSS path" in m]
        finally:
            srv.server_close()
            feed.stop()
            node.stop()
