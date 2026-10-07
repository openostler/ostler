# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The module-bus spec v1.3 platform follow-ups on the Brain (TODO.md "Module-bus
messages"): the ``faults/<pack>.<module>`` whole lists in the snapshot, the
``event/<name>`` feed and its SSE stream, the alarm state, the pack's ``primary`` marker in
selection, ``power.feeds`` and the ``system`` shutdown order, the wire conflict
(``by: "bus"``), and the owner's Remove device (``POST /cluster/remove``) on the fake
broker. The real Mosquitto run is in ``tests/test_mqtt_mosquitto.py``."""
from __future__ import annotations

import base64
import http.client
import json
import threading
import time

import pytest

from openostler.node import cluster as cl
from openostler.node.messages import (FAULT_STATUSES, SYSTEM_CATEGORY, feed_states,
                                      parse_event, parse_faults, parse_faults_rest,
                                      parse_power, parse_shutdown, role_grantable)
from openostler.node.removal import RemovedRegistry, device_filter, gate_buses
from openostler.node.select import select
from openostler.node.table import DeviceTable
from openostler.web.node_source import NodeFeed, fault_lines, node_sources
from openostler.web.server import DiagServer, is_local_link
from tests.fake_broker import FakeBroker
from tests.fake_node import VID, FakeNode, case, load

BASE = f"ostler/v1/{VID}"


@pytest.fixture
def fake_pack():
    from openostler.pack import use_pack
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK):
        yield FAKE_PACK


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return cond()


def faults_body(status="ok", faults=(), **kw):
    return json.dumps({"module": "alpha", "status": status, "faults": list(faults),
                       "ts": "2026-10-06T10:00:00.000Z", "t_us": 1000, "boot": 7,
                       "source": "kline-diag/alpha/18 00", **kw}).encode()


def event_body(eid="01J9ZK4Y6W8R3V5T7N2M1QXCDE", **kw):
    return json.dumps({"id": eid, "name": "alarm.triggered", "class": "security",
                       "severity": "alarm", "ts": None, "t_us": 5, "boot": 7, "cause": "door",
                       **kw}).encode()


# ---- payloads --------------------------------------------------------------------------- #
def test_fault_lists_parse_whole_and_honestly():
    assert parse_faults_rest("lr_d2.td5") == ("lr_d2", "td5")
    assert parse_faults_rest("obd.7E8") == ("obd", "7E8")
    for bad in ("td5", ".td5", "lr_d2.", "a.b/c", ""):
        assert parse_faults_rest(bad) is None
    assert parse_faults(b"") == {}                         # cleared: not read again
    assert parse_faults(b"[]") is None and parse_faults(faults_body("maybe")) is None
    rec = parse_faults(faults_body("faults", [{"code": "P0101", "text": "MAF", "c": "proven"},
                                             {"code": "x", "c": "certain"}, {"text": "no code"}]))
    assert rec["faults"] == [{"code": "P0101", "c": "proven", "text": "MAF"},
                             {"code": "x", "c": "candidate"}]  # never raised
    assert set(FAULT_STATUSES) == {"ok", "faults", "error", "unimplemented"}


def test_events_parse_and_need_an_id():
    ev = parse_event("alarm.triggered", event_body())
    assert ev["id"] and ev["severity"] == "alarm" and ev["cause"] == "door" and ev["ts"] is None
    assert parse_event("alarm.triggered", event_body(severity="panic"))["severity"] is None
    assert parse_event("alarm.triggered", json.dumps({"name": "x"}).encode()) is None
    assert parse_event("Alarm/Triggered", event_body()) is None
    # the firmware's own event (a65c44d)
    line = next(d for d in load("wire-conflict.jsonl") if "/event/" in d["topic"])
    ev = parse_event(line["topic"].rsplit("/", 1)[1], line["payload"])
    assert (ev["name"], ev["class"], ev["severity"], ev["cause"]) == \
        ("gate.conflict", "gate", "warning", "bus")
    assert line["properties"] == {"message_expiry_interval": 3600} and line["qos"] == 1


def test_power_feeds_and_the_system_shutdown_order():
    rec = parse_power(json.dumps({"state": "awake", "feeds": [
        {"target": "brain", "state": "off", "since": "2026-10-06T10:00:00.000Z"},
        {"target": "relay", "state": "dimmed"}, "x", {"state": "on"}]}).encode())
    assert rec["feeds"] == [{"target": "brain", "state": "off",
                             "since": "2026-10-06T10:00:00.000Z"}]
    assert "feeds" not in parse_power(b'{"state":"awake","feeds":"brain"}')
    assert feed_states({"node": rec, "relay1": {"feeds": [
        {"target": "brain", "state": "on", "since": None}]}})["brain"]["state"] == "off"
    # the node's own off (firmware a65c44d)
    off = [d for d in load("off.jsonl") if d["topic"].endswith("/power")]
    assert [parse_power(d["payload"])["state"] for d in off][:2] == ["awake", "off"]
    order = {"id": "01J9", "target": "brain", "action": "shutdown",
             "params": {"timeout_s": 60, "reason": "ignition off"}, "category": "system",
             "tier": 0}
    got = parse_shutdown(json.dumps(order).encode())
    assert got["params"] == {"timeout_s": 60, "reason": "ignition off"}
    assert parse_shutdown(json.dumps({**order, "category": "maintenance"}).encode()) is None
    assert parse_shutdown(json.dumps({**order, "tier": 1}).encode()) is None
    assert SYSTEM_CATEGORY == "system" and not role_grantable("system")
    assert role_grantable("maintenance")


# ---- the device table ------------------------------------------------------------------- #
class T:
    def __init__(self, **kw):
        self.now, self.wall = 100.0, 1_791_000_000.0
        self.table = DeviceTable(VID, pack_id="fake", **kw)

    def put(self, topic, payload, retain=False):
        return self.table.ingest(f"{BASE}/{topic}", payload, retain, self.now, self.wall)


def test_the_faults_topic_feeds_the_module_and_absent_is_not_read():
    t = T()
    assert t.table.faults_for("alpha") is None
    assert t.put("node/faults/fake.alpha", faults_body(), retain=True)
    got = t.table.faults_for("alpha")
    assert got["status"] == "ok" and got["faults"] == [] and got["last_known"] is True
    assert fault_lines(got) == ([], None)                  # read, none
    t.put("node/faults/fake.alpha", faults_body("faults", [
        {"code": "P0101", "text": "MAF circuit", "state": "Logged", "c": "proven"}]))
    got = t.table.faults_for("alpha")
    assert got["last_known"] is False and got["topic_module"] == "fake.alpha"
    assert fault_lines(got) == (["P0101 MAF circuit (Logged)"], None)
    t.put("node/faults/fake.alpha", faults_body("error", note="no answer"))
    assert fault_lines(t.table.faults_for("alpha"))[1] == "no answer"
    t.put("node/faults/fake.alpha", b"")                    # cleared
    assert t.table.faults_for("alpha") is None
    assert fault_lines(None) == ([], "not read by the node yet")
    assert not t.put("node/faults/lr_d2.alpha", faults_body())   # another pack: ignored
    assert not t.put("node/faults/alpha", faults_body())


def test_events_are_deduplicated_by_id_and_numbered():
    t = T()
    assert t.put("node/event/alarm.triggered", event_body("A"))
    assert t.put("node/event/alarm.triggered", event_body("A"))      # a QoS 1 redelivery
    assert t.put("guardian/event/alarm.triggered", event_body("B"))
    evs = t.table.events()
    assert [(e["seq"], e["id"], e["device"]) for e in evs] == [(1, "A", "node"),
                                                               (2, "B", "guardian")]
    assert t.table.duplicate_events == 1 and t.table.events(after=1)[0]["id"] == "B"
    assert evs[0]["received_utc"].endswith("Z") and evs[0]["retained"] is False
    assert t.table.wait_events(2, 0.01) is False and t.table.wait_events(1, 0.01) is True


def test_primary_wins_selection_only_while_usable():
    prim = {"Vehicle.LowVoltageBattery.CurrentVoltage": ("beta", "battery")}
    t = T(primary=prim.get)
    path = "Vehicle.LowVoltageBattery.CurrentVoltage"

    def put(module, value, t_us):
        t.put(f"node/vss/{path}", json.dumps({
            "value": value, "unit": "V", "ts": None, "t_us": t_us, "boot": 7,
            "source": f"kline-diag/{module}/21 10", "name": "battery", "c": "proven"}).encode())

    put("alpha", 13.0, 1_000_000)
    put("beta", 13.9, 1_000_000)
    put("alpha", 13.1, 1_500_000)                           # alpha is fresher
    v = t.table.view("alpha", t.now, t.wall)["vss"][path]
    assert v["sel"] == "node/kline-diag/beta/21 10" and v["value"] == 13.9
    assert v["sources"]["node/kline-diag/beta/21 10"]["primary"] is True
    assert "primary" not in v["sources"]["node/kline-diag/alpha/21 10"]
    # without the marker: today's rule (the freshest)
    t2 = T()
    t2.table._primary = lambda p: None
    assert select([{"device": "n", "src": "a", "stale": False, "age_s": 0.1,
                    "pack_decoded": True},
                   {"device": "n", "src": "b", "stale": False, "age_s": 0.5,
                    "pack_decoded": True, "primary": True}])["src"] == "b"
    assert select([{"device": "n", "src": "a", "stale": False, "age_s": 0.1,
                    "pack_decoded": True},
                   {"device": "n", "src": "b", "stale": True, "age_s": 9.0,
                    "pack_decoded": True, "primary": True}])["src"] == "a"


def test_the_alarm_state_label_comes_from_the_allowed_values():
    from openostler.metrics import metric_info
    from openostler.node.messages import ALARM_STATE, subscriptions
    from openostler.web.node_source import _allowed_values

    info = metric_info(ALARM_STATE)
    assert info["allowed"] == ["DISARMED", "ARMING", "ARMED", "TRIGGERED"]
    assert info["aliases"] == {"ovms": "v.e.alarm", "ha_domain": "alarm_control_panel"}
    assert (f"{BASE}/+/vss/{ALARM_STATE}", 1) in subscriptions(VID)   # QoS 1, spec §6
    t = T(allowed=_allowed_values)
    t.put(f"guardian/vss/{ALARM_STATE}", json.dumps({
        "value": 2, "unit": "", "ts": None, "t_us": 9, "boot": 1,
        "source": "guardian/alarm", "c": "proven"}).encode(), retain=True)
    sig = t.table.view(None, t.now, t.wall)["vss"][ALARM_STATE]["sources"]
    assert list(sig.values())[0]["v"] == 2
    t.put(f"guardian/vss/{ALARM_STATE}", json.dumps({
        "value": 3, "unit": "", "ts": None, "t_us": 10, "boot": 1, "state": "TRIGGERED",
        "source": "guardian/alarm", "c": "proven"}).encode())
    dev = t.table._devices["guardian"]
    r = next(iter(dev.readings.values()))
    assert t.table._signal(dev, r, t.now, t.wall)["label"] == "TRIGGERED"
    t.put(f"guardian/vss/{ALARM_STATE}", json.dumps({
        "value": 1, "unit": "", "ts": None, "t_us": 11, "boot": 1,
        "source": "guardian/alarm", "c": "proven"}).encode())
    r = next(iter(dev.readings.values()))
    assert t.table._signal(dev, r, t.now, t.wall)["label"] == "ARMING"


def test_feeds_show_in_the_view_and_the_cluster():
    t = T()
    t.put("node/status", b"online", retain=True)
    t.put("node/power", json.dumps({"state": "awake", "feeds": [
        {"target": "brain", "state": "off", "since": "2026-10-06T10:00:00.000Z"}]}).encode())
    t.put("brain/status", b"offline")
    rows = {d["id"]: d for d in t.table.cluster()["devices"]}
    assert rows["brain"]["feed"] == {"owner": "node", "state": "off",
                                     "since": "2026-10-06T10:00:00.000Z"}
    assert rows["node"]["feed"] is None


def test_the_wire_conflict_is_labelled_by_bus():
    t = T()
    for d in load("wire-conflict.jsonl"):
        if "/manifest" in d["topic"] and b'"by":"bus"' in d["payload"]:
            t.put(d["topic"].split(f"{BASE}/", 1)[1], d["payload"], retain=True)
            break
    t.put("node/status", b"online", retain=True)
    view = t.table.cluster()
    alert = next(a for a in view["alerts"] if a["code"] == "gate_conflict")
    assert alert["by"] == "bus" and alert["devices"] == ["node"] and alert["claimants"] == []
    gate = next(r for r in view["roles"] if r["role"] == "gate")
    assert gate["conflict"] is True and gate["holder"] is None
    # both kinds in one manifest: claims entry first, then bus
    m = {"items": [{"id": "kline", "bus": "kline-diag"}], "transmit": [{"bus_id": "kline-diag"}],
         "problems": [{"code": "gate_conflict", "item": "kline"},
                      {"by": "bus", "code": "gate_conflict", "item": "kline"}]}
    assert cl.reported_gate_conflict_kinds(m) == [("kline-diag", "manifest"),
                                                  ("kline-diag", "bus")]
    assert cl.reported_gate_conflicts(m) == ["kline-diag"]


def test_the_firmware_fixtures_v13():
    """The node's v1.3 dumps (a65c44d): SLABS publishes the battery on its pack leaf, the
    Td5 on the VSS path; gate-conflict.jsonl now carries its event."""
    slabs = [d["topic"] for d in load("slabs-vectors.jsonl")]
    assert f"{BASE}/node/vss/lr_d2.slabs.battery" in slabs
    assert f"{BASE}/node/vss/Vehicle.LowVoltageBattery.CurrentVoltage" not in slabs
    td5 = [d["topic"] for d in load("td5-vectors.jsonl")]
    assert f"{BASE}/node/vss/Vehicle.LowVoltageBattery.CurrentVoltage" in td5
    ev = [d for d in load("gate-conflict.jsonl") if "/event/" in d["topic"]]
    assert len(ev) == 1 and json.loads(ev[0]["payload"])["cause"] == "claims"
    t = T()
    for d in load("gate-conflict.jsonl") + load("wire-conflict.jsonl"):
        t.put(d["topic"].split(f"{BASE}/", 1)[1], d["payload"], retain=d["retain"])
    assert [e["cause"] for e in t.table.events()] == ["claims", "bus"]


# ---- the pack's primary marker ----------------------------------------------------------- #
def test_primary_problems_in_a_store(tmp_path, monkeypatch):
    from openostler import signals

    rec = {"lid": "10", "offset": 0, "kind": "u16", "scale": 0.001, "unit": "V",
           "metric": "Vehicle.LowVoltageBattery.CurrentVoltage", "confidence": "proven"}
    (tmp_path / "a.json").write_text(json.dumps([{**rec, "name": "battery", "primary": True},
                                                 {**rec, "name": "battery", "length": 8}]))
    (tmp_path / "b.json").write_text(json.dumps([{**rec, "name": "battery", "primary": True}]))
    (tmp_path / "c.json").write_text(json.dumps([{**rec, "name": "x", "primary": True,
                                                  "metric": None}]))
    monkeypatch.setattr(signals, "_DIR", tmp_path)
    signals._CACHE.clear()
    try:
        probs = signals.primary_problems(["a", "b", "c"])
        assert any("more than one primary" in p for p in probs)
        assert any("a.battery: primary on some of its records" in p for p in probs)
        assert any("c.x: primary without a metric" in p for p in probs)
        assert signals.primary_fields(["a", "b"]) == {
            "Vehicle.LowVoltageBattery.CurrentVoltage": ("a", "battery")}
        assert signals.load_signals("a")[0].primary is True
        assert signals.load_signals("a")[1].primary is False
        # upsert writes it only as true
        signals.upsert_field("b", {**rec, "name": "y", "lid": "11", "primary": False,
                                   "metric": None})
        assert "primary" not in json.loads((tmp_path / "b.json").read_text())[-1]
    finally:
        signals._CACHE.clear()


@pytest.mark.needs_pack
def test_the_d2_pack_marks_the_td5_battery_primary():
    from openostler import signals
    from openostler.pack import active_pack

    mods = active_pack().module_ids()
    assert signals.primary_problems(mods) == []
    prim = signals.primary_fields(mods)
    if prim:  # the pack's marker (d2diag 507ef88); absent on an older pack: today's rule
        assert prim["Vehicle.LowVoltageBattery.CurrentVoltage"] == ("td5", "battery")


# ---- Remove device, events and faults over HTTP ------------------------------------------ #
def test_local_links():
    for ip in ("127.0.0.1", "::1", "10.1.2.3", "172.20.0.5", "192.168.4.1", "169.254.9.9",
               "fe80::1%eth0", "fd12::5", "::ffff:192.168.1.2"):
        assert is_local_link(ip, {}), ip
    for ip in ("100.101.102.103", "fd7a:115c:a1e0::1", "8.8.8.8", "2001:db8::1", None, "x"):
        assert not is_local_link(ip, {}), ip
    assert not is_local_link("127.0.0.1", {"X-Forwarded-For": "8.8.8.8"})
    assert not is_local_link("127.0.0.1", {"Tailscale-User-Login": "a@b"})


class Rig:
    def __init__(self, tmp_path, *, admin=None, public=False, acl=None):
        self.broker = FakeBroker(acl=acl).start()
        self.node = FakeNode(self.broker.host, self.broker.port)
        self.feed = NodeFeed(VID, self.broker.host, self.broker.port, client_id="t-nodesource",
                             pack_id="fake", log=lambda _m: None)
        self.state = tmp_path / "state"
        self.revoked = []
        self.srv = DiagServer(host="127.0.0.1", port=0, source=node_sources(self.feed, ["alpha"]),
                              active="alpha", csv_dir=str(tmp_path), record_sessions=False,
                              geocoder=None, public=public, admin_password=admin,
                              state_dir=str(self.state),
                              device_revoker=lambda vid, dev: self.revoked.append((vid, dev))
                              or "revoked")
        self.srv.event_keepalive = 0.2
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.feed.start()
        assert wait_for(lambda: self.feed.subscribed_at is not None)
        self.node.connect()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        data = json.dumps(body).encode() if body is not None else None
        conn.request(method, path, body=data, headers={"Content-Type": "application/json",
                                                       **(headers or {})})
        r = conn.getresponse()
        out = (r.status, json.loads(r.read() or b"null"))
        conn.close()
        return out

    def close(self):
        self.srv.stop()
        self.srv.shutdown()
        self.srv.server_close()
        self.feed.stop()
        try:
            self.node.stop()
        except OSError:
            pass
        self.broker.stop()


def _validator(path, method, status):
    from tests.test_api_contracts import OPENAPI, _load, _response_pointer
    from tests.test_api_contracts import _validator as v

    doc = _load(OPENAPI)
    return v(doc, _response_pointer(doc, path, method, status))


def _node_state(r):
    for m in (case("online"), case("awake")):
        r.node.send(m)
    r.node.client.publish(f"{BASE}/node/manifest", json.dumps({
        "schema": 1, "id": "node", "kind": "node", "transmit": [{"bus_id": "kline-diag"}],
        "items": [{"id": "kline", "kind": "kline", "bus": "kline-diag", "status": "ok"}]
    }).encode(), 1, True)
    r.node.client.publish(f"{BASE}/node/role/gate/kline-diag", json.dumps({
        "role": "gate", "scope": "kline-diag", "term": 1, "priority": 10, "since": None,
        "reason": "wired"}).encode(), 1, True)
    r.node.send_vss("Vehicle.Speed", 12, name="alpha_speed", source="kline-diag/alpha/21 01",
                    t_us=1000)
    r.node.client.publish(f"{BASE}/node/faults/fake.alpha", faults_body(), 1, True)


def test_faults_and_events_reach_the_snapshot_and_the_feed(tmp_path, fake_pack):
    r = Rig(tmp_path)
    try:
        _node_state(r)
        r.node.client.publish(f"{BASE}/node/faults/fake.alpha", faults_body("faults", [
            {"code": "P0101", "text": "MAF", "c": "proven"}]), 1, True)
        for _ in range(2):  # a redelivery: one event
            r.node.client.publish(f"{BASE}/node/event/alarm.triggered", event_body("E1"), 1,
                                  False, properties={"message_expiry_interval": 3600})
        assert wait_for(lambda: r.feed.table.faults_for("alpha") is not None
                        and r.feed.table.faults_for("alpha")["status"] == "faults"
                        and r.feed.table.last_event_seq() == 1)
        snap = r.srv.poll_once()
        assert snap["faults"] == ["P0101 MAF"] and "faults_note" not in snap
        assert snap["faults_read"]["device"] == "node"
        code, body = r.call("GET", "/cluster/events?after=0")
        assert code == 200 and [e["id"] for e in body["events"]] == ["E1"]
        assert not list(_validator("/cluster/events", "get", "200").iter_errors(body))
        assert r.call("GET", "/cluster/events?after=x")[0] == 400
        # the SSE stream: the backlog, then a live one
        conn = http.client.HTTPConnection("127.0.0.1", r.srv.server_address[1], timeout=5)
        conn.request("GET", "/cluster/events/stream", headers={"Last-Event-ID": "0"})
        resp = conn.getresponse()
        assert resp.status == 200 and resp.getheader("Content-Type") == "text/event-stream"
        assert resp.readline() == b"id: 1\n" and resp.readline() == b"event: node_event\n"
        assert json.loads(resp.readline()[6:])["id"] == "E1"
        resp.readline()
        r.node.client.publish(f"{BASE}/node/event/fault.new", event_body("E2", name="fault.new",
                                                                         severity="warning"), 1)
        lines = []
        while not lines or not lines[-1].startswith(b"data:"):
            line = resp.readline()
            if line.startswith((b"id:", b"data:")):
                lines.append(line)
        assert lines == [b"id: 2\n", lines[-1]] and json.loads(lines[-1][6:])["id"] == "E2"
        conn.close()
    finally:
        r.close()


def test_remove_device_purges_and_forgets(tmp_path, fake_pack):
    r = Rig(tmp_path)
    try:
        _node_state(r)
        assert wait_for(lambda: "node" in r.feed.table.devices()
                        and len(r.feed.table.device_topics("node")) >= 5)
        assert r.call("POST", "/cluster/remove", {"device": "node"})[0] == 400  # no confirm
        assert r.call("POST", "/cluster/remove", {"device": "a/b", "confirm": True})[0] == 400
        assert r.call("POST", "/cluster/remove", {"device": "ghost", "confirm": True})[0] == 404
        code, body = r.call("POST", "/cluster/remove", {"device": "node", "confirm": True},
                            {"X-Forwarded-For": "100.64.1.1"})
        assert (code, body["code"]) == (403, "not_local")
        code, body = r.call("POST", "/cluster/remove", {"device": "node", "confirm": True})
        assert code == 200, body
        assert not list(_validator("/cluster/remove", "post", "200").iter_errors(body))
        assert body["buses"] == ["kline-diag"] and body["refused"] == [] and \
            body["remaining"] == []
        assert f"{BASE}/node/role/gate/kline-diag" in body["purged"]
        assert f"{BASE}/node/faults/fake.alpha" in body["purged"]
        assert body["revoked"] == {"brain": True, "broker": "revoked"}
        assert r.revoked == [(VID, "node")]
        assert not [t for t in r.broker.retained if t.startswith(f"{BASE}/node/")]
        assert "node" not in r.feed.table.devices()
        # it comes back: ignored by this Brain (and by the broker's ACL once revoked there)
        r.node.client.publish(f"{BASE}/node/status", b"online", 1, True)
        time.sleep(0.2)
        assert "node" not in r.feed.table.devices()
        reg = RemovedRegistry(str(r.state / "removed_devices.json"))
        assert reg.devices(VID) == ["node"] and reg.load()[VID]["node"]["topics_purged"]
        # a restarted Brain keeps ignoring it
        feed2 = NodeFeed(VID, r.broker.host, r.broker.port, client_id="t2", pack_id="fake")
        srv2 = DiagServer(host="127.0.0.1", port=0, source=node_sources(feed2, ["alpha"]),
                          active="alpha", csv_dir=str(tmp_path), record_sessions=False,
                          geocoder=None, state_dir=str(r.state))
        assert feed2.table.removed_devices() == ["node"]
        srv2.server_close()
    finally:
        r.close()


def test_remove_device_reports_a_refused_purge(tmp_path, fake_pack):
    acl = {"t-nodesource-host": {"read": [f"{BASE}/#"], "write": []}}
    r = Rig(tmp_path, acl=acl)
    try:
        _node_state(r)
        assert wait_for(lambda: len(r.feed.table.device_topics("node")) >= 5)
        code, body = r.call("POST", "/cluster/remove", {"device": "node", "confirm": True})
        assert (code, body["code"]) == (503, "unavailable") and body["purged"] == []
        assert f"{BASE}/node/status" in body["refused"] and body["remaining"]
    finally:
        r.close()


def test_remove_device_is_for_the_owner_only(tmp_path, fake_pack):
    r = Rig(tmp_path, admin="pw")
    try:
        _node_state(r)
        code, body = r.call("POST", "/cluster/remove", {"device": "node", "confirm": True})
        assert (code, body["code"]) == (401, "auth_required")
        auth = "Basic " + base64.b64encode(b"owner:pw").decode()
        code, _ = r.call("POST", "/cluster/remove", {"device": "node", "confirm": True},
                         {"Authorization": auth, "Forwarded": "for=8.8.8.8"})
        assert code == 403
    finally:
        r.close()
    r = Rig(tmp_path, admin="pw", public=True)
    try:
        assert r.call("POST", "/cluster/remove", {"device": "node", "confirm": True})[0] == 403
        assert r.call("GET", "/cluster/events")[0] == 403
    finally:
        r.close()


def test_helpers():
    assert device_filter(VID, "node") == f"{BASE}/node/#"
    with pytest.raises(ValueError):
        device_filter(VID, "+")
    view = {"devices": [{"id": "node", "claims": [{"role": "gate", "scope": "kline-diag"},
                                                  {"role": "time", "scope": None}]}]}
    assert gate_buses(view, "node") == ["kline-diag"] and gate_buses(view, "x") == []
