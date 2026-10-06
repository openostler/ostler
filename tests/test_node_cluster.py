# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The cluster view (NodeSource spec §11, §14 P3; ADR-0037, ADR-0040): manifests and role
claims into the device table, holders, candidates and void claims, the gate rules, handovers
seen live only, ``GET /cluster`` against the OpenAPI contract, firmware and manifest
``etag`` in node session meta, and the serial source's refusal beside a node that holds the
K-line gate (owner answer 7). The manifests and claims are hand-written fixtures
(``tests/fixtures/node/cluster.jsonl``): the firmware publishes neither yet."""
from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.error
import urllib.request

import pytest

from openostler.logbook.recorder import SessionRecorder
from openostler.node import cluster as cl
from openostler.node.messages import parse_claim, parse_manifest, parse_role_rest
from openostler.node.table import DeviceTable
from openostler.web.node_source import (NodeFeed, check_serial_beside_node, node_sources,
                                        probe_cluster)
from openostler.web.server import DiagServer
from tests.fake_broker import FakeBroker
from tests.fake_node import VID, FakeNode, case, cluster_messages, load

pytestmark = pytest.mark.fake_pack

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = f"ostler/v1/{VID}/"


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return cond()


class Feeder:
    """A device table fed message by message on a fake clock."""

    def __init__(self):
        self.t = DeviceTable(VID)
        self.n = 0

    def msg(self, topic, payload, retain=True):
        self.n += 1
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload).encode()
        elif isinstance(payload, str):
            payload = payload.encode()
        return self.t.ingest(topic if topic.startswith("ostler/") else BASE + topic, payload,
                             retain, float(self.n), 1_791_300_000.0 + self.n)

    def case(self, name, retain=None):
        for m in cluster_messages(name):
            self.msg(m["topic"], m["payload"], m["retain"] if retain is None else retain)
        return self

    def view(self):
        return self.t.cluster()


def role(view, r, scope=None):
    return next(x for x in view["roles"] if x["role"] == r and x["scope"] == scope)


def device(view, d):
    return next(x for x in view["devices"] if x["id"] == d)


def manifest(dev_id, **kw):
    return {"schema": 1, "id": dev_id, "fw": "1.0.0", "etag": f"e-{dev_id}", **kw}


# ---- payloads -------------------------------------------------------------------------- #
def test_manifest_and_claim_payloads():
    m = parse_manifest(b'{"id":"n","roles":{"x":1},"memory":[1],"fw":3,"priority":"hi",'
                       b'"transmit":[{"bus_id":"kline-diag"}]}')
    assert m == {"id": "n", "transmit": [{"bus_id": "kline-diag"}]}  # wrong types dropped
    assert parse_manifest(b"[1]") is None and parse_manifest(b"x") is None
    assert parse_role_rest("gate/kline-diag") == ("gate", "kline-diag")
    assert parse_role_rest("pbroker") == ("pbroker", None)
    assert parse_role_rest("") is None and parse_role_rest("a/b/c") is None
    assert parse_role_rest("gate/") is None
    assert parse_claim(b"") == {}  # a release
    assert parse_claim(b"nope") is None
    c = parse_claim(b'{"role":"time","term":-1,"priority":true,"since":5,"reason":"r"}')
    assert c == {"role": "time", "scope": None, "term": 0, "priority": None, "since": None,
                 "reason": "r"}


def test_the_cluster_fixture_and_its_manifests_follow_the_contracts():
    import jsonschema
    from tests.test_api_contracts import ASYNCAPI, OPENAPI, _load, _validator

    msgs = _load(ASYNCAPI)["components"]["messages"]
    assert msgs["nodeManifest"]["payload"]["$ref"].endswith("/NodeManifest")
    assert msgs["nodeRoleClaim"]["payload"]["$ref"].endswith("/RoleClaim")
    doc = _load(OPENAPI)
    man_v = _validator(doc, "/components/schemas/NodeManifest")
    claim_v = _validator(doc, "/components/schemas/RoleClaim")
    power_v = _validator(doc, "/components/schemas/NodePower")
    status_v = jsonschema.Draft202012Validator(msgs["nodeStatus"]["payload"])
    kinds = set()
    for m in load("cluster.jsonl"):
        kind = m["topic"].split("/")[4]
        kinds.add(kind)
        if not m["payload"]:
            continue  # a release clears the retained claim
        if kind == "manifest":
            body = json.loads(m["payload"])
            assert not list(man_v.iter_errors(body)), m["topic"]
            assert body["id"] == m["topic"].split("/")[3] and len(body["etag"]) == 64
        elif kind == "role":
            assert not list(claim_v.iter_errors(json.loads(m["payload"]))), m["topic"]
        elif kind == "power":
            assert not list(power_v.iter_errors(json.loads(m["payload"]))), m["topic"]
        elif kind == "status":
            assert not list(status_v.iter_errors(m["payload"].decode())), m["topic"]
    assert kinds == {"manifest", "role", "power", "status"}
    asy = _load(ASYNCAPI)
    assert asy["channels"]["nodeManifest"]["address"] == "ostler/v1/{vid}/{device}/manifest"
    assert asy["channels"]["nodeRole"]["address"] == "ostler/v1/{vid}/{device}/role/{role}"
    assert asy["channels"]["nodeRoleScoped"]["address"] == \
        "ostler/v1/{vid}/{device}/role/{role}/{scope}"
    for op in ("receiveNodeManifest", "receiveNodeRole", "receiveNodeRoleScoped"):
        assert asy["operations"][op]["x-ostler-consumer"] == "brain"
        assert asy["operations"][op]["bindings"]["mqtt"]["qos"] == 1


# ---- holders, candidates, void claims -------------------------------------------------- #
def test_the_base_cluster_holders_and_candidates():
    v = Feeder().case("cluster").view()
    assert [d["id"] for d in v["devices"]] == ["brain", "engbay", "guardian", "node", "relay1"]
    assert [(r["role"], r["scope"]) for r in v["roles"]] == [
        ("gate", "kline-diag"), ("pbroker", None), ("time", None), ("plca", "t1s0"),
        ("uplink", None)]
    gate = role(v, "gate", "kline-diag")
    assert (gate["holder"], gate["term"], gate["hands_over"]) == ("node", 1, False)
    pb = role(v, "pbroker")
    assert (pb["holder"], pb["term"], pb["reason"]) == ("node", 3, "node healthy 60 s")
    # node → guardian → eligible module (ADR-0037 §2, Amendment 13); the check_in sensor
    # node is never a candidate and its claim is void (Amendment 14)
    assert [c["device"] for c in pb["candidates"]] == ["node", "guardian", "relay1"]
    eng = next(c for c in pb["claims"] if c["device"] == "engbay")
    assert eng["void"] and eng["flags"] == ["not_eligible"]
    assert [a["code"] for a in v["alerts"]] == ["void_claim"]
    assert role(v, "uplink")["holder"] == "brain"
    assert role(v, "time")["holder"] == "node"
    plca = role(v, "plca", "t1s0")
    assert plca["no_holder"] and plca["holder"] is None and plca["candidates"][0]["device"] == "node"
    assert all(r["last_handover"] is None for r in v["roles"])  # stored claims are no handover


def test_a_device_row_is_the_peer_view_shape():
    v = Feeder().case("cluster").view()
    node = device(v, "node")
    assert (node["kind"], node["variant"], node["class"]) == ("node", "diag-port", "node")
    assert node["board"] == "esp32-s3-devkitc" and node["fw"] == "0.1.0"
    assert len(node["etag"]) == 64 and node["manifest_utc"].endswith("Z")
    assert node["links"] == [{"kind": "wifi", "via": "brain"}]
    assert node["power"]["state"] == "awake" and node["power"]["class"] == "always"
    assert node["since"] == node["power"]["since"]
    assert node["last_seen_utc"] is None  # stored messages only: never "seen" live
    assert node["transmit"] == [{"bus_id": "kline-diag"}]
    assert node["memory"] == {"psram_kb": 8192}
    assert {c["role"] for c in node["claims"]} == {"gate", "pbroker", "time"}
    assert device(v, "guardian")["class"] == "guardian"
    assert device(v, "engbay")["class"] == "module"  # a sensor node is an add-on module
    assert device(v, "brain")["class"] == "brain"


def test_two_gate_claims_on_one_bus_leave_no_holder_and_an_alert():
    v = Feeder().case("cluster").case("gate_conflict").view()
    gate = role(v, "gate", "kline-diag")
    assert gate["holder"] is None and gate["conflict"] and gate["no_holder"]
    assert all("conflict" in c["flags"] for c in gate["claims"])
    alert = next(a for a in v["alerts"] if a["code"] == "gate_conflict")
    assert alert["devices"] == ["node", "node2"] and "both refuse to transmit" in alert["message"]


def test_a_sleeping_or_offline_holders_claims_are_void():
    f = Feeder().case("cluster")
    f.msg("node/status", "offline")
    v = f.view()
    gate = role(v, "gate", "kline-diag")
    assert gate["holder"] is None and gate["claims"][0]["flags"] == ["offline"]
    assert role(v, "pbroker")["holder"] is None  # the module's claim is void too
    f.msg("node/status", "asleep")
    assert role(f.view(), "time")["claims"][0]["flags"] == ["asleep"]
    f.msg("node/status", "online")
    f.msg("node/power", {"state": "asleep", "since": None})
    assert role(f.view(), "time")["claims"][0]["flags"] == ["asleep"]


def test_undeclared_unmanifested_and_ineligible_claims_are_void():
    f = Feeder()
    f.msg("x/status", "online")
    f.msg("x/role/time", {"role": "time", "term": 1})          # no manifest: cannot check
    f.msg("b/manifest", manifest("b", kind="brain", roles=[{"role": "pbroker"}]))
    f.msg("b/role/pbroker", {"role": "pbroker", "term": 9})     # the brain never holds it
    f.msg("g/manifest", manifest("g", kind="node", variant="guardian", roles=[]))
    f.msg("g/role/gate/kline-diag", {"role": "gate", "scope": "kline-diag", "term": 1})
    f.msg("g/role/time", {"role": "pbroker", "term": 1})         # payload names another role
    v = f.view()
    flags = {(c["device"], r["role"]): c["flags"] for r in v["roles"] for c in r["claims"]}
    assert flags[("x", "time")] == ["no_manifest"]
    assert flags[("b", "pbroker")] == ["not_eligible"]
    assert flags[("g", "gate")] == ["not_declared"]   # a gate needs transmit on its bus
    assert flags[("g", "time")] == ["mismatch", "not_declared"]
    assert all(r["holder"] is None for r in v["roles"])
    assert {a["code"] for a in v["alerts"]} == {"void_claim"}


def test_add_on_modules_as_the_last_parked_broker_fallback():
    """ADR-0037 Amendment 18's simulated cluster: only add-on modules."""
    f = Feeder()
    mods = {"a": dict(power={"class": "always"}, memory={"psram_kb": 8192}, mc=5, prio=1),
            "b": dict(power={"class": "always"}, memory={"psram_kb": 2048}, mc=5, prio=1),
            "c": dict(power={"class": "check_in"}, memory={"psram_kb": 8192}, mc=5, prio=9),
            "d": dict(power={"class": "always"}, memory={}, mc=5, prio=9),
            "e": dict(power={"class": "always"}, memory={"psram_kb": 4096}, mc=6, prio=9)}
    for dev, m in mods.items():
        f.msg(f"{dev}/status", "online")
        f.msg(f"{dev}/manifest", manifest(dev, kind="module", power=m["power"], memory=m["memory"],
                                          priority=m["prio"],
                                          roles=[{"role": "pbroker", "max_clients": m["mc"]}]))
    pb = role(f.view(), "pbroker")
    assert [c["device"] for c in pb["candidates"]] == ["a", "b"]  # equal priority: lowest id
    for dev in "cde":
        assert cl.eligibility(f.t._devices[dev].manifest, "pbroker", None), dev
    # c and d claim it: both void and flagged; a guardian outranks every module
    f.msg("c/role/pbroker", {"role": "pbroker", "term": 1})
    f.msg("d/role/pbroker", {"role": "pbroker", "term": 1})
    f.msg("g/status", "online")
    f.msg("g/manifest", manifest("g", kind="node", variant="guardian", priority=0,
                                 roles=[{"role": "pbroker"}]))
    pb = role(f.view(), "pbroker")
    assert pb["holder"] is None and all(c["void"] for c in pb["claims"])
    assert [c["device"] for c in pb["candidates"]] == ["g", "a", "b"]


def test_term_then_priority_decides_and_the_loser_is_superseded():
    f = Feeder().case("cluster")
    f.case("guardian_takes_pbroker")  # stored: term 4 beats the node's term 3
    pb = role(f.view(), "pbroker")
    assert pb["holder"] == "guardian" and pb["term"] == 4
    assert next(c for c in pb["claims"] if c["device"] == "node")["flags"] == ["superseded"]
    assert pb["last_handover"] is None  # a stored claim is never a handover


def test_handovers_are_recorded_from_live_claims_only():
    f = Feeder().case("cluster")
    f.case("guardian_takes_pbroker", retain=False)  # live: the guardian takes over
    h = role(f.view(), "pbroker")["last_handover"]
    assert (h["from"], h["to"], h["term"], h["reason"]) == ("node", "guardian", 4,
                                                            "node in parked-deep")
    assert h["at_utc"].endswith("Z")
    f.msg("guardian/role/pbroker", "", retain=False)  # released live: back to the node's claim
    h = role(f.view(), "pbroker")["last_handover"]
    assert (h["from"], h["to"], h["reason"]) == ("guardian", "node", "guardian released")
    f.case("node_asleep", retain=False)  # the node sleeps cleanly and clears its claims
    v = f.view()
    assert role(v, "pbroker")["holder"] is None
    h = role(v, "pbroker")["last_handover"]
    assert (h["from"], h["to"], h["reason"]) == ("node", None, "node asleep")
    assert role(v, "time")["last_handover"]["reason"] == "node asleep"
    f.msg("guardian/role/pbroker", {"role": "pbroker", "term": 5, "reason": "takeover"},
          retain=False)
    h = role(f.view(), "pbroker")["last_handover"]
    assert (h["from"], h["to"], h["term"], h["reason"]) == (None, "guardian", 5, "takeover")
    gate = role(v, "gate", "kline-diag")  # a gate never hands over: void while asleep
    assert gate["holder"] is None and gate["claims"][0]["flags"] == ["asleep"]
    # the bus just has no gate while its node sleeps (ADR-0037 Amendment 9)
    assert (gate["last_handover"]["to"], gate["last_handover"]["reason"]) == (None, "node asleep")


def test_a_reconnect_forgets_claims_and_manifests_until_the_retained_copies_return():
    f = Feeder().case("cluster")
    f.t.forget_liveness()
    v = f.view()
    assert all(d["claims"] == [] and d["fw"] is None for d in v["devices"])
    assert role(v, "pbroker")["holder"] is None
    f.case("cluster")
    assert role(f.view(), "pbroker")["holder"] == "node"
    assert role(f.view(), "pbroker")["last_handover"] is None


def test_a_bus_read_without_a_gate_shows_no_gate_and_device_info():
    f = Feeder()
    f.msg("node/status", "online")
    f.msg("vss/Vehicle.Speed".join(["node/", ""]),
          {"value": 1, "unit": "km/h", "ts": None, "t_us": 1, "source": "can-body/abs/7e0",
           "name": "speed", "c": "candidate"}, retain=False)
    v = f.view()
    gate = role(v, "gate", "can-body")
    assert gate["no_holder"] and gate["candidates"] == [] and gate["claims"] == []
    assert device(v, "node")["last_seen_utc"] is not None
    assert f.t.device_info() == {}
    f.msg("node/manifest", manifest("node", kind="node"))
    assert f.t.device_info() == {"node": {"fw": "1.0.0", "etag": "e-node"}}
    f.msg("node/manifest", "")  # cleared: the device was removed
    assert f.t.device_info() == {}


def test_unknown_roles_and_bad_payloads_are_reported_once():
    logs = []
    t = DeviceTable(VID, log=logs.append)
    assert not t.ingest(BASE + "n/role/king", b"{}", True, 1, 1)
    assert not t.ingest(BASE + "n/role/king", b"{}", True, 2, 2)
    assert not t.ingest(BASE + "n/role/time", b"[", True, 3, 3)
    assert not t.ingest(BASE + "n/manifest", b"[1]", True, 4, 4)
    assert len(logs) == 3


# ---- the serial-source rule (owner answer 7) ------------------------------------------- #
def test_kline_gate_holders_by_claim_or_by_manifest():
    v = Feeder().case("cluster").view()
    assert cl.kline_gate_holders(v) == [{"device": "node", "bus_id": "kline-diag",
                                         "by": "claim", "status": "online"}]
    assert "node (kline-diag, by its claim, status online)" in cl.serial_refusal(v)
    f = Feeder().case("node_asleep")  # asleep, claims cleared, but wired by its manifest
    f.msg("node/manifest", manifest("node", kind="node", transmit=[{"bus_id": "kline-diag"}]))
    assert cl.kline_gate_holders(f.view())[0]["by"] == "manifest"
    can = Feeder()
    can.msg("n/manifest", manifest("n", kind="node", transmit=[{"bus_id": "can-body"}]))
    assert cl.kline_gate_holders(can.view()) == [] and cl.serial_refusal(can.view()) is None
    assert cl.serial_refusal(Feeder().view()) is None


@pytest.fixture
def fake_pack():
    from openostler.pack import use_pack
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK):
        yield


def test_the_serial_source_refuses_beside_a_gate_holding_node(fake_pack):
    with FakeBroker() as broker:
        url = f"mqtt://{broker.host}:{broker.port}"
        assert check_serial_beside_node(url, VID, insecure_lab=True, client_id="t",
                                        log=lambda _m: None) is None
        for m in cluster_messages():
            broker.inject(m["topic"], m["payload"], m["qos"], m["retain"])
        why = check_serial_beside_node(url, VID, insecure_lab=True, client_id="t",
                                       log=lambda _m: None)
        assert why and "holds the K-line transmit gate" in why and "node (kline-diag" in why
        # the check reads under its own client id (never takes over a running NodeSource)
        assert "t-check" in {c for c, _p in broker.received}
        assert wait_for(lambda: "t-check" not in broker.connected_clients())  # and disconnects
        with pytest.raises(ValueError):  # plain mqtt:// needs the lab flag
            check_serial_beside_node(url, VID, client_id="t")
        # another vehicle's node does not count
        assert check_serial_beside_node(url, "other-car", insecure_lab=True, client_id="t",
                                        log=lambda _m: None) is None


def test_the_check_fails_closed_when_the_broker_does_not_answer(fake_pack):
    import socket

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    feed = NodeFeed(VID, "127.0.0.1", port, client_id="t-check", log=lambda _m: None)
    with pytest.raises(ConnectionError):
        probe_cluster(feed, timeout=0.3)


def test_the_dashboard_wires_the_refusal():
    src = (ROOT / "tools" / "dashboard.py").read_text(encoding="utf-8")
    assert 'args.source == "serial" and args.mqtt' in src
    assert "check_serial_beside_node(" in src and "the serial source refuses to start" in src
    assert "does not start unchecked" in src  # fails closed


# ---- GET /cluster end to end ----------------------------------------------------------- #
class Rig:
    def __init__(self, tmp_path, *, public=False):
        self.broker = FakeBroker().start()
        self.node = FakeNode(self.broker.host, self.broker.port)
        self.feed = NodeFeed(VID, self.broker.host, self.broker.port, client_id="t-nodesource",
                             pack_id="fake", log=lambda _m: None)
        self.srv = DiagServer(host="127.0.0.1", port=0, source=node_sources(self.feed, ["alpha"]),
                              active="alpha", csv_dir=str(tmp_path), record_sessions=False,
                              geocoder=None, public=public, admin_password="pw" if public else None)
        import threading

        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.feed.start()
        assert wait_for(lambda: self.feed.subscribed_at is not None)
        self.node.connect()

    def get(self, path):
        url = f"http://127.0.0.1:{self.srv.server_address[1]}{path}"
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.feed.stop()
        try:
            self.node.stop()
        except OSError:
            pass
        self.broker.stop()


def _cluster_validator():
    from tests.test_api_contracts import OPENAPI, _load, _response_pointer, _validator

    doc = _load(OPENAPI)
    return _validator(doc, _response_pointer(doc, "/cluster", "get", "200"))


def test_get_cluster_validates_and_follows_the_node(tmp_path, fake_pack):
    r = Rig(tmp_path)
    try:
        for m in cluster_messages():
            if m["topic"].split("/")[3] != "node":
                r.broker.inject(m["topic"], m["payload"], m["qos"], m["retain"])
            else:
                r.node.send(m)
        assert wait_for(lambda: len(r.feed.cluster()["devices"]) == 5
                        and role(r.feed.cluster(), "gate", "kline-diag")["holder"] == "node")
        code, body = r.get("/cluster?x=1")
        assert code == 200
        errors = list(_cluster_validator().iter_errors(body))
        assert not errors, [e.message for e in errors[:5]]
        assert body["vid"] == VID and body["source_kind"] == "node" and body["stale"] is False
        assert body["broker"]["connected"] and body["as_of_utc"].endswith("Z")
        assert device(body, "node")["last_seen_utc"]  # live messages from the node
        # the node sleeps cleanly: its claims go, the snapshot says asleep
        for m in cluster_messages("node_asleep"):
            r.node.send(m)
        assert wait_for(lambda: role(r.feed.cluster(), "pbroker")["holder"] is None)
        assert r.srv.poll_once()["status"] == "asleep"
        snap = r.srv.poll_once()
        assert snap["node"]["fw"] == "0.1.0" and snap["device_info"]["relay1"]["fw"] == "0.2.0"
        # the broker goes away: the view is stale (last known), never emptied
        r.broker.stop()
        assert wait_for(lambda: r.get("/cluster")[1]["stale"] is True)
        code, body = r.get("/cluster")
        assert len(body["devices"]) == 5 and not list(_cluster_validator().iter_errors(body))
    finally:
        r.close()


def test_get_cluster_is_refused_in_public_mode(tmp_path, fake_pack):
    r = Rig(tmp_path, public=True)
    try:
        code, body = r.get("/cluster")
        assert code == 403 and body == {"ok": False, "error": "not available in public mode",
                                        "code": "public_mode"}
    finally:
        r.close()


def test_get_cluster_with_a_cable_source_is_empty_and_says_why(tmp_path, fake_pack):
    from tests.fake_pack import FAKE_PACK

    srv = DiagServer(host="127.0.0.1", port=0, source=FAKE_PACK.sources("auto"),
                     csv_dir=str(tmp_path), record_sessions=False, geocoder=None)
    try:
        body = srv.cluster()
        assert body["devices"] == [] and body["roles"] == [] and "no node source" in body["note"]
        assert body["source_kind"] == "serial"
        assert not list(_cluster_validator().iter_errors(body))
    finally:
        srv.server_close()


# ---- session meta: firmware and manifest etag (spec §7) -------------------------------- #
def test_node_session_meta_records_firmware_and_manifest_etag(tmp_path):
    from tests.test_node_recording import Clock, _schema_errors, events_of, meta_of, sig, snap

    c = Clock()
    rec = SessionRecorder(str(tmp_path / "sessions"), clock=c.wall, mono=c.mono, vid="bench-1",
                          min_free_bytes=0, fsync=lambda _fd: None, record_identity=False)
    rec.clk = c
    try:
        s = snap({"alpha_speed": sig(900)})
        rec.feed({**s, "device_info": {"node": {"fw": "0.1.0", "etag": "aa"}}})
        sid = rec.session_id
        c.m += 1
        rec.feed({**s, "device_info": {"node": {"fw": "0.1.0", "etag": "aa"},
                                       "relay1": {"fw": "0.2.0", "etag": None}}})
        c.m += 1
        rec.feed({**s, "device_info": {"node": {"fw": "0.1.1", "etag": "bb"}}})
        rec.close()
        meta = meta_of(rec, sid)
        assert meta["device_info"] == {"node": {"fw": "0.1.1", "etag": "bb"},
                                       "relay1": {"fw": "0.2.0", "etag": None}}
        assert not _schema_errors(meta)
        ev = [(e["device"], e["fw"], e["etag"]) for e in events_of(rec, sid)
              if e["type"] == "node_manifest"]
        assert ev == [("node", "0.1.0", "aa"), ("relay1", "0.2.0", None), ("node", "0.1.1", "bb")]
    finally:
        rec.close()


def test_the_e2e_node_server_serves_a_cluster():
    src = (ROOT / "tests" / "e2e_server.py").read_text(encoding="utf-8")
    assert "cluster_messages()" in src
    assert case("online")["payload"] == b"online"
    assert os.path.exists(ROOT / "tests" / "fixtures" / "node" / "cluster.jsonl")
