# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Recording from a node (NodeSource spec §7, §9 replay, §10, §13; P2): sessions driven by
the node's status and power, live values only, ``vss`` columns, the node's clock, the
identity rule, the raw tap subscribed only while a session records, the pcapng export and
read-only replay. Unit tests feed the recorder snapshots; the end-to-end tests run a
simulated node, the fake broker, NodeFeed and the server."""
from __future__ import annotations

import calendar
import json
import os
import time
import urllib.error
import urllib.request

import pytest

from openostler.logbook import recorder as recmod
from openostler.logbook.recorder import SessionRecorder
from openostler.logbook.store import SessionStore, read_rows
from openostler.logbook.tap import read_tap
from openostler.mqtt import StdlibMqttClient, codec
from openostler.node.tap import TimeMap, is_time_event
from openostler.web.node_source import NodeFeed, node_sources
from openostler.web.server import DiagServer
from tests.fake_broker import FakeBroker
from tests.fake_node import VID, FakeNode, case, tap_messages
from tests.test_node_tap import read_pcapng

pytestmark = pytest.mark.fake_pack

SPEED = "Vehicle.Powertrain.CombustionEngine.Speed"
T0 = calendar.timegm((2026, 10, 6, 10, 0, 0)) + 0.0


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return cond()


# ---- snapshots ------------------------------------------------------------------------- #
def sig(v, *, stale=False, ts=None, age=0.1, u="rpm", c="proven"):
    return {"v": v, "u": u, "s": None, "c": c, "ts_utc": ts, "age_s": age, "stale": stale,
            "src": "node/kline-diag/alpha/21 01"}


def vssr(value, sources, *, stale=False, unit="rpm"):
    return {"sel": next(iter(sources)), "value": value, "unit": unit, "ts_utc": None,
            "age_s": 0.1, "stale": stale, "c": "proven",
            "sources": {k: {"v": v, "u": unit, "ts_utc": None, "age_s": a, "stale": st, "c": "proven"}
                        for k, (v, a, st) in sources.items()}}


def snap(signals=None, vss=None, *, status="connected", conn=None, node_status="online",
         power="awake", devices=("node",)):
    return {"source_kind": "node", "status": status,
            "conn": conn or {"connected": "connected", "asleep": "disconnected",
                             "error": "lost", "connecting": "connecting"}.get(status, "lost"),
            "module": "alpha", "signals": signals or {}, "vss": vss or {}, "faults": [],
            "node": {"device": "node", "status": node_status,
                     "power": {"state": power} if power else None},
            "devices": list(devices)}


class Clock:
    def __init__(self):
        self.m = 100.0

    def wall(self):
        return T0 + self.m

    def mono(self):
        return self.m


@pytest.fixture
def rec(tmp_path):
    c = Clock()
    r = SessionRecorder(str(tmp_path / "sessions"), clock=c.wall, mono=c.mono, vid="bench-1",
                        min_free_bytes=0, fsync=lambda _fd: None, record_identity=False)
    r.clk = c
    yield r
    r.close()


def meta_of(r, sid):
    with open(os.path.join(r.root, sid, "meta.json"), encoding="utf-8") as fh:
        return json.load(fh)


def events_of(r, sid):
    with open(os.path.join(r.root, sid, "events.jsonl"), encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def rows_of(r, sid):
    return read_rows(os.path.join(r.root, sid), meta_of(r, sid))


def _schema_errors(meta):
    import jsonschema

    root = os.path.join(os.path.dirname(__file__), "..", "schemas", "session-meta.schema.json")
    with open(root, encoding="utf-8") as fh:
        schema = json.load(fh)
    return [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(meta)]


# ---- opening rules ---------------------------------------------------------------------- #
def test_stored_values_never_open_a_session(rec):
    """Values retained at subscribe time are last known values: online and awake with only
    stale values opens nothing (and writes no row)."""
    rec.feed(snap({"alpha_speed": sig(750, stale=True, age=None)}))
    rec.feed(snap(vss={SPEED: vssr(750, {"node/kline-diag/alpha/21 01": (750, None, True)},
                                   stale=True)}))
    assert rec.session_id is None and not os.path.isdir(rec.root) or not os.listdir(rec.root)


@pytest.mark.parametrize("kw", [dict(power=None), dict(power="waking", status="connecting"),
                                dict(power="shutting_down"), dict(node_status="offline", status="error"),
                                dict(status="asleep", power="asleep")])
def test_a_session_opens_only_online_awake_or_held_with_live_values(rec, kw):
    rec.feed(snap({"alpha_speed": sig(900)}, **kw))
    assert rec.session_id is None


@pytest.mark.parametrize("power", ["awake", "held"])
def test_live_values_from_an_awake_or_held_node_open_a_session(rec, power):
    rec.feed(snap({"alpha_speed": sig(900)}, power=power))
    assert rec.session_id is not None and rec.status()["state"] == "recording"


# ---- rows ----------------------------------------------------------------------------- #
def test_rows_hold_live_values_and_vss_columns_only(rec):
    s = snap({"alpha_speed": sig(900), "alpha_temp": sig(80, stale=True, u="°C")},
             {SPEED: vssr(900, {"node/kline-diag/alpha/21 01": (900, 0.1, False),
                                "guardian/imu": (905, 0.3, False)}),
              "Vehicle.Speed": vssr(12, {"guardian/gnss": (12, 0.2, False),
                                         "ublox/gnss": (11, 3.0, True)}, unit="km/h"),
              "Vehicle.Body.Lights.IsBrakeOn": vssr(1, {"node/x": (1, 9.0, True)}, stale=True,
                                                    unit="")},
             devices=("node", "guardian", "ublox"))
    rec.feed(s)
    rec.clk.m += 0.5
    rec.feed(snap({"alpha_speed": sig(950)}))
    sid = rec.session_id
    rec.close()
    _cols, rows = rows_of(rec, sid)
    assert rows[0]["alpha_speed"] == 900 and "alpha_temp" not in rows[0]
    assert rows[0][SPEED] == 900 and rows[0][f"{SPEED}@node"] == 900
    assert rows[0][f"{SPEED}@guardian"] == 905
    assert rows[0]["Vehicle.Speed"] == 12 and rows[0]["Vehicle.Speed@guardian"] == 12
    assert "Vehicle.Speed@ublox" not in rows[0]              # its only reading was stale
    assert not [k for k in rows[0] if k.startswith("Vehicle.Body")]
    assert rows[1]["alpha_speed"] == 950 and SPEED not in rows[1]
    meta = meta_of(rec, sid)
    chans = {c["name"]: c for c in meta["channels"]}
    assert "alpha_temp" not in chans
    assert chans["Vehicle.Speed@guardian"]["units"] == "km/h"
    assert chans[SPEED]["group"] == "vss" and chans[SPEED]["c"] == "candidate"
    assert meta["devices"] == ["guardian", "node", "ublox"]


def test_a_poll_with_nothing_live_writes_no_row(rec):
    rec.feed(snap({"alpha_speed": sig(900)}))
    rec.clk.m += 0.5
    rec.feed(snap({"alpha_speed": sig(900, stale=True)}))   # online, not reading alpha
    sid = rec.session_id
    assert rec.status()["state"] == "recording"
    rec.close()
    assert len(rows_of(rec, sid)[1]) == 1


def test_identity_paths_are_never_written(rec):
    rec.feed(snap({"alpha_speed": sig(1), "vin_check": sig(7)},
                  {"Vehicle.VehicleIdentification.VIN": vssr(3, {"node/x": (3, 0.1, False)}),
                   "Vehicle.Ostler.Ecu.SerialNumber": vssr(4, {"node/x": (4, 0.1, False)})}))
    sid = rec.session_id
    rec.close()
    cols = [c for c, _u, _r in rows_of(rec, sid)[0]]
    assert "alpha_speed" in cols
    assert not [c for c in cols if "Identification" in c or "Serial" in c or "vin" in c]


def test_the_same_values_give_the_same_columns_as_a_cable_source(tmp_path):
    """Spec §13: the recorder writes the same columns for a node as for a cable source."""
    out = {}
    for kind in ("serial", "node"):
        c = Clock()
        r = SessionRecorder(str(tmp_path / kind), clock=c.wall, mono=c.mono, vid="bench-1",
                            min_free_bytes=0, fsync=lambda _fd: None)
        s = snap({"alpha_speed": sig(900), "alpha_temp": sig(81, u="°C")})
        if kind == "serial":
            s = {"status": "connected", "conn": "connected", "module": "alpha", "faults": [],
                 "signals": {"alpha_speed": {"v": 900, "u": "rpm", "s": None, "c": "proven"},
                             "alpha_temp": {"v": 81, "u": "°C", "s": None, "c": "proven"}}}
        r.feed(s)
        sid = r.session_id
        r.close()
        cols, rows = read_rows(os.path.join(r.root, sid), json.load(
            open(os.path.join(r.root, sid, "meta.json"), encoding="utf-8")))
        out[kind] = ([(n, u) for n, u, _rate in cols], rows[0])
    assert out["node"][0] == out["serial"][0]
    assert {k: v for k, v in out["node"][1].items() if k != "Utc"} == \
        {k: v for k, v in out["serial"][1].items() if k != "Utc"}


def test_a_cable_session_meta_is_unchanged(rec):
    """No behaviour change for a serial source: no node fields, and per-signal flags are
    not read."""
    rec.feed({"status": "connected", "conn": "connected", "module": "alpha", "faults": [],
              "stale": True, "signals": {"alpha_speed": {"v": 9, "u": "rpm", "stale": True}}})
    sid = rec.session_id
    rec.close()
    meta = meta_of(rec, sid)
    assert meta["source"] == "live"
    assert not {"devices", "device_info", "pack", "tap", "end_reason"} & set(meta)
    assert rows_of(rec, sid)[1][0]["alpha_speed"] == 9


# ---- time ------------------------------------------------------------------------------ #
def test_utc_follows_the_nodes_synced_clock(rec):
    rec.feed(snap({"alpha_speed": sig(900, ts="2026-10-06T09:00:00.000Z", age=0.5)}))
    rec.clk.m += 0.5
    rec.feed(snap({"alpha_speed": sig(901)}))           # the node lost its clock
    sid = rec.session_id
    rec.close()
    rows = rows_of(rec, sid)[1]
    want = (calendar.timegm((2026, 10, 6, 9, 0, 0)) + 0.5) * 1000
    assert rows[0]["Utc"] == pytest.approx(want, abs=1)
    assert rows[1]["Utc"] == pytest.approx(rec.clk.wall() * 1000, abs=1)
    types = [e["type"] for e in events_of(rec, sid)]
    assert types.count("time_unsynced") == 1


def test_an_unsynced_node_is_noted_once(rec):
    for v in (1, 2, 3):
        rec.feed(snap({"alpha_speed": sig(v)}))
        rec.clk.m += 0.5
    sid = rec.session_id
    rec.close()
    assert [e for e in events_of(rec, sid) if e["type"] == "time_unsynced"] == [
        {"t": 0, "type": "time_unsynced", "utc_from": "brain"}]


# ---- ending rules ---------------------------------------------------------------------- #
def test_a_clean_sleep_ends_the_session_at_once(rec):
    rec.feed(snap({"alpha_speed": sig(900)}))
    sid = rec.session_id
    rec.clk.m += 1
    rec.feed(snap({"alpha_speed": sig(900, stale=True)}, status="asleep", power="asleep"))
    assert rec.session_id is None
    meta = meta_of(rec, sid)
    assert meta["end_reason"] == "node_asleep" and meta["recording"] is False
    assert meta["source"] == "node" and meta["devices"] == ["node"]
    assert meta["pack"]["id"] == "fake" and "version" in meta["pack"]
    assert meta["tap"] == []
    assert not _schema_errors(meta)
    assert {"t": 1000, "type": "status", "status": "asleep"} in events_of(rec, sid)
    # waking again opens a new session
    rec.clk.m += 5
    rec.feed(snap({"alpha_speed": sig(800)}))
    assert rec.session_id not in (None, sid)


@pytest.mark.parametrize("kw", [dict(status="error", node_status="offline"),
                                dict(status="broker-down")])
def test_offline_or_a_lost_broker_pauses_and_the_idle_rule_ends(rec, kw):
    rec.feed(snap({"alpha_speed": sig(900)}))
    sid = rec.session_id
    rec.clk.m += 1
    rec.feed(snap({"alpha_speed": sig(901, stale=True)}, **kw))
    assert rec.status()["state"] == "paused"
    rec.clk.m += recmod.IDLE_S - 2
    rec.feed(snap({"alpha_speed": sig(901, stale=True)}, **kw))
    assert rec.session_id == sid
    rec.clk.m += 2
    rec.feed(snap({"alpha_speed": sig(901, stale=True)}, **kw))
    assert rec.session_id is None
    meta = meta_of(rec, sid)
    assert meta["end_reason"] == "idle" and meta["rows"] == 1
    assert not _schema_errors(meta)


def test_close_and_split_name_their_reason(rec):
    rec.feed(snap({"alpha_speed": sig(900)}))
    first = rec.split()
    rec.feed(snap({"alpha_speed": sig(901)}))
    rec.close()
    metas = {m["id"]: m for m in (meta_of(rec, d) for d in os.listdir(rec.root))}
    assert metas[first]["end_reason"] == "closed" and metas[first]["source"] == "node"
    assert [m["end_reason"] for k, m in metas.items() if k != first] == ["split"]


# ---- the tap in the recorder ----------------------------------------------------------- #
def test_tap_is_written_only_while_a_node_session_is_open(rec):
    msgs = tap_messages()
    meta_msg = next(m for m in msgs if m["topic"].endswith("/meta"))
    data = [m for m in msgs if m["topic"].endswith("/data")]
    session = meta_msg["topic"].split("/")[5]
    assert rec.tap_message("node", session, "data", data[0]["payload"]) == 0  # nothing open
    rec.feed(snap({"alpha_speed": sig(900)}))
    sid = rec.session_id
    rec.tap_message("node", session, "meta", meta_msg["payload"])
    n = rec.tap_message("node", session, "data", data[1]["payload"])
    assert n > 0 and meta_of(rec, sid)["tap"][0]["records"] == n   # listed at once
    n += rec.tap_message("node", session, "data", data[2]["payload"])
    rec.feed(snap(status="asleep", power="asleep"))
    assert rec.tap_message("node", session, "data", data[3]["payload"]) == 0
    meta = meta_of(rec, sid)
    (t,) = meta["tap"]
    assert t["session"] == session and t["scrub"] == "on" and t["records"] == n
    assert t["boot_id"] == 7 and t["gaps"] == 0 and not _schema_errors(meta)
    assert os.path.getsize(os.path.join(rec.root, sid, t["file"])) == t["bytes"]
    assert "tap_start" in [e["type"] for e in events_of(rec, sid)]


def test_a_cable_session_takes_no_tap(rec):
    rec.feed({"status": "connected", "conn": "connected", "module": "alpha", "faults": [],
              "signals": {"alpha_speed": {"v": 9}}})
    assert rec.tap_message("node", "01M48AFR80CDXA0ZQ1XBS3VHSS", "data", b"\x00" * 20) == 0


# ---- end to end: the node, the broker, the feed, the server ----------------------------- #
class RecRig:
    """A recording server on NodeSource (fake pack modules), with the fast tap back-off."""

    def __init__(self, tmp_path, acl=None):
        self.broker = FakeBroker(acl=acl).start()
        self.node = FakeNode(self.broker.host, self.broker.port)
        self.logs = []
        self.feed = NodeFeed(VID, self.broker.host, self.broker.port, client_id="t-nodesource",
                             pack_id="fake", log=self.logs.append,
                             tap_client=lambda: StdlibMqttClient(
                                 "t-nodesource-tap", keep_alive=10, clean_start=True,
                                 session_expiry=60, backoff=(0.05, 0.2)))
        self.sessions = str(tmp_path / "sessions")
        self.srv = DiagServer(host="127.0.0.1", port=0,
                              source=node_sources(self.feed, ["alpha", "beta"]), active="alpha",
                              csv_dir=str(tmp_path), sessions_dir=self.sessions, geocoder=None)
        self.srv._recorder.record_identity = False
        self.feed.start()
        assert wait_for(lambda: self.feed.connected)
        self.node.connect()

    def tick(self):
        snap = self.srv.poll_once()
        self.srv.record_poll()
        return {**snap, **self.srv.latest}

    def sync(self):
        self.node.client.publish("sync/x", b"", qos=1)
        time.sleep(0.05)

    def live(self, v, t_us):
        self.node.send_vss(SPEED, v, name="alpha_speed", source="kline-diag/alpha/21 01",
                           t_us=t_us, unit="rpm")

    def received(self, cid, kind):
        return [p for c, p in list(self.broker.received) if c == cid and isinstance(p, kind)]

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
def rr(tmp_path):
    r = RecRig(tmp_path)
    yield r
    r.close()


def _tap_split():
    msgs = tap_messages()
    meta = next(m for m in msgs if m["topic"].endswith("/meta"))
    return meta, [m for m in msgs if m["topic"].endswith("/data")], meta["topic"].split("/")[5]


def test_the_tap_follows_the_recorded_session_end_to_end(rr):
    meta, data, session = _tap_split()
    rr.node.send(meta)                            # retained before anything records
    rr.node.send(data[0])                         # a batch with no session: never kept
    rr.node.send(case("awake"))
    rr.live(900, 2_000_000)
    rr.sync()
    assert not rr.feed.tap_running
    snap = rr.tick()
    sid = snap["recording"]["session"]
    assert sid and rr.feed.tap_running
    assert wait_for(lambda: rr.received("t-nodesource-tap", codec.Subscribe))
    (conn,) = rr.received("t-nodesource-tap", codec.Connect)
    assert conn.clean_start and conn.properties["session_expiry_interval"] == 60
    subs = [s for p in rr.received("t-nodesource-tap", codec.Subscribe) for s in p.subscriptions]
    assert [(s.topic_filter, s.qos) for s in subs] == [
        (f"ostler/v1/{VID}/+/tap/+/meta", 1), (f"ostler/v1/{VID}/+/tap/+/data", 1)]
    assert all(s.no_local and not s.retain_as_published for s in subs)
    time.sleep(0.1)                               # the retained header arrives
    for m in data[1:4]:
        rr.node.send(m)
    rr.sync()
    snap = rr.tick()
    assert snap["node"]["tap"] == {"session": session, "state": "receiving", "batches": 3}
    from tests.test_node_source import _snapshot_validator
    assert not list(_snapshot_validator()[0].iter_errors(json.loads(json.dumps(snap))))
    rr.node.send(case("asleep"))
    rr.sync()
    snap = rr.tick()
    assert snap["status"] == "asleep" and snap["recording"] is None
    assert snap["node"]["tap"] is None and not rr.feed.tap_running
    assert wait_for(lambda: rr.received("t-nodesource-tap", codec.Unsubscribe))
    assert wait_for(lambda: "t-nodesource-tap" not in rr.broker.connected_clients())
    rr.node.send(data[4])                         # after the session: not recorded
    rr.sync()
    store = SessionStore(rr.sessions)
    m = store.meta(sid)
    assert m["end_reason"] == "node_asleep" and m["source"] == "node"
    (t,) = m["tap"]
    want = sum(len(d["payload"]) for d in data[1:4])
    assert t["session"] == session and t["bytes"] == want and t["gaps"] == 0
    assert t["scrub"] == "on" and t["seq_first"] > 0
    # the Brain published nothing on either connection
    assert not rr.received("t-nodesource", codec.Publish)
    assert not rr.received("t-nodesource-tap", codec.Publish)


def test_a_short_brain_hiccup_loses_no_tap_batch(rr):
    """Spec §4: the tap subscription's 60 s session keeps QoS 1 batches across a dropped
    connection; the reconnect resumes it (no clean start)."""
    meta, data, session = _tap_split()
    rr.node.send(meta)
    rr.node.send(case("awake"))
    rr.live(900, 2_000_000)
    rr.sync()
    sid = rr.tick()["recording"]["session"]
    assert wait_for(lambda: rr.received("t-nodesource-tap", codec.Subscribe))
    time.sleep(0.05)
    rr.node.send(data[0])
    rr.broker.kill("t-nodesource-tap")            # a network loss
    rr.node.send(data[1])                         # queued by the broker meanwhile
    assert wait_for(lambda: len(rr.received("t-nodesource-tap", codec.Connect)) == 2)
    assert rr.received("t-nodesource-tap", codec.Connect)[1].clean_start is False
    rr.node.send(data[2])
    rr.sync()
    assert wait_for(lambda: rr.feed.tap_batches >= 3)
    rr.srv.close_recorder()
    t = SessionStore(rr.sessions).meta(sid)["tap"][0]
    assert t["gaps"] == 0 and t["bytes"] == sum(len(d["payload"]) for d in data[:3])


def test_the_spec_acl_covers_the_tap_and_refuses_tap_ctl(tmp_path):
    acl = {"t-nodesource": {"read": [f"ostler/v1/{VID}/+/status", f"ostler/v1/{VID}/+/power",
                                     f"ostler/v1/{VID}/+/vss/+", f"ostler/v1/{VID}/+/manifest",
                                     f"ostler/v1/{VID}/+/role/#"], "write": []},
           "t-nodesource-tap": {"read": [f"ostler/v1/{VID}/+/tap/+/meta",
                                         f"ostler/v1/{VID}/+/tap/+/data"], "write": []},
           "node": {"read": [], "write": [f"ostler/v1/{VID}/node/#", "sync/x"]}}
    r = RecRig(tmp_path, acl=acl)
    try:
        r.node.send(case("awake"))
        r.live(900, 2_000_000)
        r.sync()
        r.tick()
        assert wait_for(lambda: r.received("t-nodesource-tap", codec.Subscribe))
        time.sleep(0.05)
        assert r.broker.refused == []
        tap = r.feed._tap
        assert tap.subscribe([codec.SubOptions(f"ostler/v1/{VID}/node/tap/ctl")]) == [
            codec.NOT_AUTHORIZED]
    finally:
        r.close()


def _get(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=5) as resp:
            return resp.status, resp.headers.get("Content-Type"), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type"), exc.read()


def test_replay_and_pcapng_export_of_a_node_session(rr):
    """Spec §14: a node session replays like any other (read-only: the feed and the broker
    see nothing) and exports its tap as pcapng; a session without a tap answers 400."""
    import threading

    meta, data, session = _tap_split()
    rr.node.send(meta)
    rr.node.send(case("awake"))
    rr.live(900, 2_000_000)
    rr.sync()
    sid = rr.tick()["recording"]["session"]
    assert wait_for(lambda: rr.received("t-nodesource-tap", codec.Subscribe))
    time.sleep(0.05)
    for m in data[:2]:
        rr.node.send(m)
    rr.live(950, 2_500_000)
    rr.sync()
    rr.tick()
    rr.node.send(case("asleep"))
    rr.sync()
    rr.tick()
    threading.Thread(target=rr.srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{rr.srv.server_address[1]}"
    before = len(rr.broker.received)
    try:
        status, _ct, body = _get(base, f"/sessions/{sid}")
        m = json.loads(body)
        assert status == 200 and m["source"] == "node" and m["tap"][0]["session"] == session
        status, _ct, body = _get(base, f"/sessions/{sid}/data?ch=alpha_speed,{SPEED}")
        d = json.loads(body)
        assert status == 200 and [v for v in d["ch"]["alpha_speed"] if v is not None] == [900, 950]
        assert [v for v in d["ch"][SPEED] if v is not None] == [900, 950]
        status, ctype, body = _get(base, f"/sessions/{sid}/export?fmt=pcapng")
        assert status == 200 and ctype == "application/x-pcapng"
        pc = read_pcapng(body)
        assert len(pc["packets"]) == sum(m["records"] for m in [m["tap"][0]])
        status, _ct, body = _get(base, f"/sessions/{sid}/export?fmt=csv")
        assert status == 200 and b"Vehicle.Powertrain" in body
    finally:
        rr.srv.shutdown()
    # replay touched no MQTT connection
    assert not [p for c, p in rr.broker.received[before:]
                if c.startswith("t-nodesource") and isinstance(p, (codec.Publish, codec.Subscribe))]


def test_a_session_without_a_tap_has_no_pcapng(rec, tmp_path):
    rec.feed({"status": "connected", "conn": "connected", "module": "alpha", "faults": [],
              "signals": {"alpha_speed": {"v": 9}}})
    sid = rec.session_id
    rec.close()
    with pytest.raises(ValueError, match="no raw tap"):
        SessionStore(rec.root).export(sid, "pcapng")


def test_the_simulated_nodes_looping_tap_records_without_gaps(rr):
    """``tests/e2e_server.py --node``: the looping simulated node renumbers its fixture tap,
    so a recorded session gets a gap-free tap from it."""
    rr.node.send(case("awake"))
    rr.live(900, 2_000_000)
    rr.sync()
    sid = rr.tick()["recording"]["session"]
    assert wait_for(lambda: rr.received("t-nodesource-tap", codec.Subscribe))
    time.sleep(0.05)
    tap = tap_messages()
    seq = rr.node._send_tap(tap, 0)
    assert rr.node._send_tap(tap, seq) == 2 * seq
    rr.sync()
    assert wait_for(lambda: rr.feed.tap_batches == 2 * (len(tap) - 1))
    rr.srv.close_recorder()
    t = SessionStore(rr.sessions).meta(sid)["tap"][0]
    assert (t["seq_first"], t["seq_last"], t["gaps"], t["records"]) == (0, 2 * seq - 1, 0, 2 * seq)
    # its time events are re-stamped for the new t_us, so every mark is used: UTC now
    store = SessionStore(rr.sessions)
    ((entry, records),) = read_tap(os.path.join(rr.sessions, sid), store.meta(sid))
    marks = [r for r in records if is_time_event(r)]
    assert t["time_marks"] == len(marks) > 0 and len(TimeMap(records)) == len(marks)
    assert abs(TimeMap(records).utc_ns(records[-1].t_us) / 1e9 - time.time()) < 60
