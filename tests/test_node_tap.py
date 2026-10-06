# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The raw tap on the Brain (NodeSource spec §7, §13, P2): the record codec against the
firmware's fixtures, the identity scrub re-checked on the Brain (ADR-0036), the ``.otap``
writer (gaps, duplicates, overflow) and the pcapng export (a tap fixture round-trips with
its ``seq`` gaps reported, and a ``1A`` reply leaves only the placeholder)."""
from __future__ import annotations

import json
import os
import struct

import pytest

from openostler.logbook.pcapng import (LINKTYPE_CAN_SOCKETCAN, LINKTYPE_USER0, LINKTYPE_USER1,
                                       to_pcapng)
from openostler.logbook.tap import (RECORD_IDENTITY_ENV, TapRecorder,
                                    identity_recording_enabled, read_tap)
from openostler.node import tap as T
from openostler.node.messages import parse_tap_rest, tap_subscriptions
from tests.fake_node import VID, tap_messages, time_event

SESSION = "01M48AFR80CDXA0ZQ1XBS3VHSS"
OTHER = "01M48AFR80CDXA0ZQ1XBS3VHST"
# A Td5 ReadEcuIdentification exchange (synthetic, no real identity): the request 1A 9B
# (sent by the node's gate) and its positive reply 5A 9B with made-up bytes.
REQ = bytes([0x02, 0x1A, 0x9B, 0xB7])
REPLY = bytes([0x08, 0x5A, 0x9B]) + b"FAKEID" + bytes([0x00])
SECRET = b"FAKEID"


def rec(seq, payload, *, t_us=None, proto=T.PROTO_KLINE_MSG, d=T.DIR_RX, flags=0, typ=T.TYPE_DATA,
        bus=0):
    return T.TapRecord(t_us if t_us is not None else 1_000_000 + seq * 1000, seq, typ, bus, d,
                       proto, flags, bytes(payload))


def batch(*records) -> bytes:
    return b"".join(T.encode_record(r) for r in records)


def header(scrub="on", session=SESSION, boot=7, buses=None) -> bytes:
    return json.dumps({"v": 1, "session": session, "node": "node", "boot_id": boot,
                       "buses": buses or [{"idx": 0, "bus_id": "kline-diag", "proto": "kline",
                                           "baud": 10400}],
                       "clock": {"source": "sntp", "synced": True}, "scrub": scrub,
                       "filters": [], "records": ["kline_msg", "time"],
                       "started": "2026-10-06T10:00:00.000Z"}).encode()


def props(first_seq, content_type=T.CONTENT_TYPE) -> dict:
    """A batch's MQTT 5 properties as the node sets them (module-bus spec §8)."""
    out = {"user_property": [["first_seq", str(first_seq)]]}
    if content_type is not None:
        out["content_type"] = content_type
    return out


FIXTURES = ("td5-vectors.jsonl", "slabs-vectors.jsonl", "slabs-vectors-no-priority.jsonl",
            "lifecycle.jsonl", "gate-conflict.jsonl")


# ---- codec ----------------------------------------------------------------------------- #
def test_fixture_batches_round_trip_through_the_codec():
    msgs = tap_messages()
    meta = [m for m in msgs if m["topic"].endswith("/meta")]
    data = [m for m in msgs if m["topic"].endswith("/data")]
    assert len(meta) == 1 and meta[0]["retain"] and data and not any(m["retain"] for m in data)
    h = T.parse_header(meta[0]["payload"])
    assert h["scrub"] == "on" and h["boot_id"] == 7 and T.valid_session(h["session"])
    seqs, records = [], []
    for m in data:
        batch_records, trailing = T.parse_records(m["payload"])
        assert trailing == 0 and batch_records
        assert b"".join(T.encode_record(r) for r in batch_records) == m["payload"]
        records += batch_records
    seqs = [r.seq for r in records]
    assert seqs == list(range(len(seqs)))   # the node numbers every record, no gap
    # data: kline_msg records; events: only the clock's time marks (firmware 5971323)
    marks = [r for r in records if r.is_event]
    assert marks and all(T.is_time_event(r) and r.bus == 0xFF and r.proto == 0
                         and r.flags == 0 for r in marks)
    assert all(r.proto == T.PROTO_KLINE_MSG and r.type == T.TYPE_DATA
               for r in records if not r.is_event)
    # a mark precedes every synced record by less than a second (raw-tap amendment)
    last = None
    for r in records:
        if T.is_time_event(r):
            last = r.t_us
        elif not r.flags & T.FLAG_UNSYNCED:
            assert last is not None and 0 <= r.t_us - last < 1_000_000, r.seq


@pytest.mark.parametrize("name", FIXTURES)
def test_the_header_lists_the_record_kinds_and_every_batch_is_labelled(name):
    """Raw-tap amendment of 2026-10-06: the header's ``records`` is an array of the kinds a
    batch may hold, ``["kline_msg", "time"]``, and every kind met is listed; each batch
    carries the content type ``application/vnd.ostler.tap.v1`` and ``first_seq``, the
    ``seq`` of its first record (module-bus spec §8)."""
    msgs = tap_messages(name)
    (meta,) = [m for m in msgs if m["topic"].endswith("/meta")]
    h = T.parse_header(meta["payload"])
    assert h["records"] == ["kline_msg", "time"] == json.loads(meta["payload"])["records"]
    assert "properties" not in meta
    kinds = set()
    for m in msgs:
        if not m["topic"].endswith("/data"):
            continue
        records, trailing = T.parse_records(m["payload"])
        assert records and not trailing
        info = T.batch_properties(m["properties"])
        assert info == {"content_type": T.CONTENT_TYPE, "content_type_ok": True,
                        "first_seq": records[0].seq, "first_seq_sent": True}
        kinds |= {"time" if T.is_time_event(r) else "kline_msg"
                  if r.proto == T.PROTO_KLINE_MSG and not r.is_event else f"other {r}"
                  for r in records}
    assert kinds <= set(h["records"]) and "kline_msg" in kinds


def test_the_tap_channels_match_the_asyncapi_document():
    """``api/asyncapi.yaml``: the header schema (``records`` an array) validates every
    fixture header; the batch message names the content type and the ``first_seq`` user
    property, and every fixture batch's properties fit them."""
    pytest.importorskip("yaml")
    import jsonschema

    from tests.test_api_contracts import ASYNCAPI, _load

    msgs = _load(ASYNCAPI)["components"]["messages"]
    meta_v = jsonschema.Draft202012Validator(msgs["nodeTapMeta"]["payload"])
    assert msgs["nodeTapMeta"]["payload"]["properties"]["records"]["type"] == "array"
    data = msgs["nodeTapData"]
    assert data["contentType"] == T.CONTENT_TYPE
    assert data["bindings"]["mqtt"]["contentType"] == T.CONTENT_TYPE
    head_v = jsonschema.Draft202012Validator(data["headers"])
    assert not list(meta_v.iter_errors(msgs["nodeTapMeta"]["examples"][0]["payload"]))
    for name in FIXTURES:
        for m in tap_messages(name):
            if m["topic"].endswith("/meta"):
                assert not list(meta_v.iter_errors(json.loads(m["payload"]))), name
            else:
                assert m["properties"]["content_type"] == data["contentType"]
                assert not list(head_v.iter_errors(dict(m["properties"]["user_property"])))


def test_header_records_and_batch_properties_are_read_tolerantly():
    base = json.loads(header())
    assert T.parse_header(json.dumps({**base, "records": "kline_msg"}).encode())["records"] == [
        "kline_msg"]                                       # the first firmware's string
    assert "records" not in T.parse_header(json.dumps({**base, "records": [1]}).encode())
    assert "records" not in T.parse_header(json.dumps({k: v for k, v in base.items()
                                                       if k != "records"}).encode())
    assert T.batch_properties(None) == {"content_type": None, "content_type_ok": None,
                                        "first_seq": None, "first_seq_sent": False}
    assert T.batch_properties({"content_type": "text/plain"})["content_type_ok"] is False
    for bad in ("-1", "01", "x", "4294967296", 7):
        got = T.batch_properties({"user_property": [("first_seq", bad)]})
        assert got["first_seq"] is None and got["first_seq_sent"], bad
    got = T.batch_properties({"user_property": [("other", "1"), ("first_seq", "4294967295")]})
    assert got["first_seq"] == 0xFFFFFFFF


@pytest.mark.parametrize("name", FIXTURES)
def test_the_firmware_time_events_decode_and_map_to_utc(name):
    """The node's ``time`` events (code 6, CBOR ``{t_us, utc_ns, source, err_us}``; raw-tap
    amendment of 2026-10-06): every one decodes, maps its own instant, and the fixture's
    wall clock (from 2026-10-06T10:00:00Z, advancing with the fake bus) comes back."""
    records = [r for m in tap_messages(name) if m["topic"].endswith("/data")
               for r in T.parse_records(m["payload"])[0]]
    marks = [r for r in records if T.is_time_event(r)]
    assert marks
    for r in marks:
        ev = T.parse_time_event(r.payload)
        assert ev is not None and ev["t_us"] == r.t_us and ev["source"] == "sntp"
        assert ev["err_us"] is None  # SNTP on ESP-IDF gives no estimate
        assert list(T.parse_time_event(r.payload)) == ["t_us", "utc_ns", "source", "err_us"]
    tm = T.TimeMap(records)
    assert len(tm) == len({r.t_us for r in marks}) and tm.sources == ["sntp"]
    t0 = 1_791_280_800 * 10**9   # 2026-10-06T10:00:00Z
    for r in marks:
        assert tm.utc_ns(r.t_us) == T.parse_time_event(r.payload)["utc_ns"]
    utcs = [tm.utc_ns(r.t_us) for r in records]
    assert utcs == sorted(utcs) and t0 <= utcs[0] < t0 + 60 * 10**9


def test_time_event_payloads_are_checked():
    good = bytes.fromhex("a4") + b"\x64t_us\x1a\x00\x0f\x42\x40" + b"\x66utc_ns\x1b" + \
        (1_791_280_800 * 10**9).to_bytes(8, "big") + b"\x66source\x64sntp\x66err_us\x19\x01\xf4"
    assert T.parse_time_event(good) == {"t_us": 1_000_000, "utc_ns": 1_791_280_800 * 10**9,
                                        "source": "sntp", "err_us": 500}
    assert T.parse_time_event(b"") is None
    assert T.parse_time_event(b"\x80") is None                       # an array
    assert T.parse_time_event(good[:-3]) is None                     # truncated
    assert T.parse_time_event(b"\xa1\x64t_us\x01") is None           # no utc_ns
    assert T.parse_time_event(b"\xbf\xff") is None                    # indefinite length
    neg = b"\xa2\x64t_us\x20\x66utc_ns\x01"                           # t_us -1
    assert T.parse_time_event(neg) is None
    extra = b"\xa3\x64t_us\x01\x66utc_ns\x02\x63new\xf5"            # unknown key kept out
    assert T.parse_time_event(extra) == {"t_us": 1, "utc_ns": 2, "source": None, "err_us": None}


def _mark(seq, t_us, utc_ns, *, cbor_t_us=None):
    body = time_event(t_us if cbor_t_us is None else cbor_t_us, utc_ns)
    return rec(seq, body, t_us=t_us, typ=T.TYPE_EVENT, d=T.EV_TIME, bus=0xFF, proto=0)


def test_the_test_encoder_writes_the_firmware_bytes():
    """``tests/fake_node.py`` ``time_event`` (used to re-stamp a looping node's tap) writes
    the node's exact bytes: four keys in order, shortest-form heads, ``err_us`` null."""
    marks = [r for m in tap_messages("lifecycle.jsonl") if m["topic"].endswith("/data")
             for r in T.parse_records(m["payload"])[0] if T.is_time_event(r)]
    assert marks and all(time_event(r.t_us, T.parse_time_event(r.payload)["utc_ns"]) == r.payload
                         for r in marks)


def test_the_time_map_is_linear_between_marks_and_holds_the_offset_outside():
    U = 1_791_280_800 * 10**9
    tm = T.TimeMap([_mark(0, 1_000_000, U), rec(1, REQ, t_us=1_500_000),
                    _mark(2, 2_000_000, U + 1_000_100_000),      # the node clock ran 100 µs slow
                    _mark(3, 3_000_000, U + 7, cbor_t_us=5)])    # its CBOR t_us disagrees: unused
    assert len(tm) == 2
    assert tm.utc_ns(1_000_000) == U and tm.utc_ns(2_000_000) == U + 1_000_100_000
    assert tm.utc_ns(1_500_000) == U + 500_050_000                # linear between marks
    assert tm.utc_ns(500_000) == U - 500_000_000                  # before: first mark's offset
    assert tm.utc_ns(2_500_000) == U + 1_500_100_000              # after: last mark's offset
    assert not T.TimeMap([rec(0, REQ)]) and T.TimeMap([]).utc_ns(5) is None


def test_a_truncated_batch_keeps_only_whole_records():
    b = batch(rec(0, REQ), rec(1, REPLY))
    records, trailing = T.parse_records(b[:-3])
    assert [r.seq for r in records] == [0] and trailing == len(b) - 3 - (20 + len(REQ))


def test_header_validation():
    assert T.parse_header(b"not json") is None
    assert T.parse_header(b'{"v": 2}') is None
    assert T.parse_header(header("maybe"))["scrub"] is None  # unknown: the Brain scrubs


def test_tap_topics():
    assert tap_subscriptions(VID) == [(f"ostler/v1/{VID}/+/tap/+/meta", 1),
                                      (f"ostler/v1/{VID}/+/tap/+/data", 1)]
    assert parse_tap_rest(f"{SESSION}/data") == (SESSION, "data")
    assert parse_tap_rest("ctl") is None and parse_tap_rest(f"{SESSION}/ctl") is None
    assert not T.valid_session("../../etc") and not T.valid_session(SESSION.lower())


# ---- the scrub (the node's rule, ADR-0036) --------------------------------------------- #
@pytest.mark.parametrize("msg, unframed, want, hit", [
    (REPLY, False, bytes([0x5A, 0x9B]) + T.PLACEHOLDER, True),             # length-prefixed
    (bytes([0x88, 0xF1, 0x13, 0x49, 0x02, 0x01]) + b"FAKEVIN", False,      # addressed (Mode 09)
     bytes([0x49, 0x02]) + T.PLACEHOLDER, True),
    (bytes([0x80, 0xF1, 0x13, 0x03, 0x5A, 0x80, 0x01]), False,             # addr + length byte
     bytes([0x5A, 0x80]) + T.PLACEHOLDER, True),
    (bytes([0x04, 0x61, 0x49, 0x5A, 0x10]), False, bytes([0x04, 0x61, 0x49, 0x5A, 0x10]), False),
    (bytes([0x01, 0x49, 0x33]), True, T.PLACEHOLDER, True),                # unframed run
    (bytes([0x01, 0x02, 0x33]), True, bytes([0x01, 0x02, 0x33]), False),
])
def test_scrub_kline_follows_the_node(msg, unframed, want, hit):
    assert T.scrub_kline(msg, unframed) == (want, hit)


def test_identity_scrub_keeps_node_scrubbed_records_and_drops_what_it_cannot_check():
    s = T.IdentityScrub()
    done = rec(0, bytes([0x5A, 0x9B]) + T.PLACEHOLDER, flags=T.FLAG_SCRUBBED)
    assert s.check(done) == done
    assert s.check(rec(1, b"\x5a", proto=T.PROTO_KLINE_BYTE)) is None
    assert s.check(rec(2, b"\x00", proto=9)) is None
    ev = rec(3, b"\xa0", typ=T.TYPE_EVENT, d=T.EV_OVERFLOW, bus=0xFF)
    assert s.check(ev) == ev
    out = s.check(rec(4, REPLY))
    assert out.payload == bytes([0x5A, 0x9B]) + T.PLACEHOLDER and out.flags & T.FLAG_SCRUBBED
    assert (s.scrubbed, s.dropped) == (1, 2)


def _can(seq, can_id, data, ext=False, bus=0):
    cid = can_id | (0x80000000 if ext else 0)
    return rec(seq, cid.to_bytes(4, "little") + bytes([len(data)]) + bytes(data),
               proto=T.PROTO_CAN, bus=bus)


def test_identity_scrub_follows_can_isotp():
    s = T.IdentityScrub()
    single = s.check(_can(0, 0x7E8, [0x06, 0x62, 0xF1, 0x8C, 0x41, 0x42, 0x43, 0x00]))
    assert single.payload[5:] == T.PLACEHOLDER and single.flags & T.FLAG_SCRUBBED
    first = s.check(_can(1, 0x7E8, [0x10, 0x14, 0x49, 0x02, 0x01, 0x46, 0x41, 0x4B]))
    cf1 = s.check(_can(2, 0x7E8, [0x21, 0x45, 0x56, 0x49, 0x4E, 0x31, 0x32, 0x33]))
    cf2 = s.check(_can(3, 0x7E8, [0x22, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x30]))
    after = s.check(_can(4, 0x7E8, [0x23, 0x00]))   # message consumed: a stray CF passes
    assert all(r.payload[5:] == T.PLACEHOLDER for r in (first, cf1, cf2))
    assert after.flags & T.FLAG_SCRUBBED == 0
    rpm = _can(5, 0x7E8, [0x04, 0x41, 0x0C, 0x1A, 0xF8, 0, 0, 0])
    assert s.check(rpm) == rpm


def test_exports_drop_unframed_and_scrub_whatever_the_setting():
    records = [rec(0, REQ, d=T.DIR_TX_ECHO, flags=T.FLAG_GATE), rec(1, REPLY),
               rec(2, bytes([0x01, 0x02]), flags=T.FLAG_UNFRAMED)]
    out = T.export_records(records)
    assert [r.seq for r in out] == [0, 1]
    assert SECRET not in b"".join(r.payload for r in out)


def test_the_install_option_is_read_from_the_environment_only():
    assert identity_recording_enabled({}) is False
    assert identity_recording_enabled({RECORD_IDENTITY_ENV: "0"}) is False
    assert identity_recording_enabled({RECORD_IDENTITY_ENV: "1"}) is True


# ---- the .otap writer ------------------------------------------------------------------ #
class Events(list):
    def __call__(self, etype, fields):
        self.append((etype, fields))

    def types(self):
        return [t for t, _ in self]


def _writer(tmp_path, **kw):
    ev = Events()
    clock = {"m": 0.0}
    syncs = []
    w = TapRecorder(str(tmp_path), emit=ev, mono=lambda: clock["m"], fsync=syncs.append, **kw)
    return w, ev, clock, syncs


def _otap(tmp_path, name=SESSION):
    return T.parse_records((tmp_path / "tap" / f"{name}.otap").read_bytes())[0]


def test_writer_appends_records_and_lists_the_file(tmp_path):
    w, ev, clock, syncs = _writer(tmp_path)
    w.header("node", SESSION, header("on"))
    assert w.batch("node", SESSION, batch(rec(5, REQ, d=T.DIR_TX_ECHO, flags=T.FLAG_GATE))) == 1
    clock["m"] = 0.5
    w.batch("node", SESSION, batch(rec(6, bytes([0x04, 0x61, 0x09, 0x03, 0x0C]))))
    assert len(syncs) == 1          # fsync at most once a second
    clock["m"] = 1.5
    w.batch("node", SESSION, batch(rec(7, bytes([0x03, 0x61, 0x0D, 0x49]))))
    assert len(syncs) == 2
    w.close()
    got = _otap(tmp_path)
    assert [r.seq for r in got] == [5, 6, 7] and got[0].flags & T.FLAG_GATE
    (e,) = w.entries()
    assert e["session"] == SESSION and e["device"] == "node" and e["file"] == f"tap/{SESSION}.otap"
    assert (e["scrub"], e["boot_id"], e["seq_first"], e["seq_last"]) == ("on", 7, 5, 7)
    assert (e["records"], e["gaps"], e["lost"], e["overflow"]) == (3, 0, 0, 0)
    assert e["buses"][0]["bus_id"] == "kline-diag"
    assert ev.types() == ["tap_start"]


def test_writer_checks_the_batch_properties(tmp_path):
    """Module-bus spec §8: a batch with another content type is refused whole (its records
    then read as a gap); one without a content type or ``first_seq`` is read as v1 and
    counted ``unlabelled`` (logged once); a ``first_seq`` that disagrees with the first
    record is logged and counted, the records' own ``seq`` kept; a batch with no whole
    record reports a gap up to its ``first_seq``; no properties (not from MQTT): no check."""
    w, ev, _c, _s = _writer(tmp_path)
    w.header("node", SESSION, header("on"))
    assert w.batch("node", SESSION, batch(rec(0, REQ), rec(1, REQ)), props(0)) == 2
    assert w.batch("node", SESSION, batch(rec(2, REQ)), props(2, "application/json")) == 0
    assert w.batch("node", SESSION, batch(rec(3, REQ)), props(3)) == 1        # gap: 2
    assert w.batch("node", SESSION, batch(rec(4, REQ)), props(4, None)) == 1   # no type
    assert w.batch("node", SESSION, batch(rec(5, REQ)), {"content_type": T.CONTENT_TYPE}) == 1
    assert w.batch("node", SESSION, batch(rec(6, REQ)), props(9)) == 1         # mismatch
    assert w.batch("node", SESSION, b"\x00" * 7, props(10)) == 0              # no record
    assert w.batch("node", SESSION, batch(rec(10, REQ)), props(10)) == 1
    assert w.batch("node", SESSION, batch(rec(11, REQ))) == 1                  # unchecked
    (e,) = w.entries()
    assert (e["refused"], e["unlabelled"], e["first_seq_mismatch"]) == (1, 2, 1)
    assert (e["gaps"], e["lost"], e["records"]) == (2, 4, 8)
    errors = [f["error"] for t, f in ev if t == "tap_error"]
    assert len(errors) == 4
    assert "content type 'application/json' is not application/vnd.ostler.tap.v1" in errors[0]
    assert "content type" in errors[1] and "read as v1" in errors[1]   # logged once
    assert "first_seq 9 does not match the batch's first record (seq 6)" in errors[2]
    assert "trailing bytes" in errors[3]
    gaps = [(f["from"], f["to"]) for t, f in ev if t == "tap_gap"]
    assert gaps == [(2, 2), (7, 9)]
    w.close()
    assert [r.seq for r in _otap(tmp_path)] == [0, 1, 3, 4, 5, 6, 10, 11]


def test_writer_logs_gaps_skips_duplicates_and_counts_overflow(tmp_path):
    w, ev, _c, _s = _writer(tmp_path)
    w.header("node", SESSION, header("on"))
    w.batch("node", SESSION, batch(rec(0, REQ), rec(1, REQ)))
    w.batch("node", SESSION, batch(rec(1, REQ), rec(4, REQ)))     # a redelivery, then a gap
    w.batch("node", SESSION, batch(rec(5, b"\x02\x00", typ=T.TYPE_EVENT, d=T.EV_OVERFLOW,
                                        bus=0xFF)))
    w.close()
    assert [r.seq for r in _otap(tmp_path)] == [0, 1, 4, 5]
    gap = next(f for t, f in ev if t == "tap_gap")
    assert (gap["from"], gap["to"], gap["lost"]) == (2, 3, 2)
    e = w.entries()[0]
    assert (e["gaps"], e["lost"], e["overflow"]) == (1, 2, 1)
    assert "tap_overflow" in ev.types()


def test_brain_rechecks_a_node_that_said_it_scrubbed(tmp_path):
    w, ev, _c, _s = _writer(tmp_path)
    w.header("node", SESSION, header("on"))
    w.batch("node", SESSION, batch(rec(0, REQ), rec(1, REPLY)))
    w.close()
    data = (tmp_path / "tap" / f"{SESSION}.otap").read_bytes()
    assert SECRET not in data and T.PLACEHOLDER in data
    assert any(t == "tap_scrub" and f.get("missed") for t, f in ev)
    assert w.entries()[0]["brain_scrubbed"] == 1


@pytest.mark.parametrize("node_scrub", ["off", None])
def test_scrub_off_is_accepted_only_with_the_brains_own_option(tmp_path, node_scrub):
    """ADR-0036: a header with ``scrub: off`` (or none at all) is recorded unscrubbed only
    when this install's option is on; otherwise the Brain scrubs."""
    for record_identity, leaks in ((False, False), (True, True)):
        d = tmp_path / str(record_identity)
        w, ev, _c, _s = _writer(d, record_identity=record_identity)
        if node_scrub:
            w.header("node", SESSION, header(node_scrub))
        w.batch("node", SESSION, batch(rec(0, REPLY),
                                       rec(1, b"\x5a\x01", proto=T.PROTO_KLINE_BYTE)))
        w.close()
        data = (d / "tap" / f"{SESSION}.otap").read_bytes()
        assert (SECRET in data) is leaks
        e = w.entries()[0]
        if record_identity:
            assert e["scrub"] in ("off", "unknown") and e["records"] == 2
        else:
            assert e["scrub"] == "brain" and e["records"] == 1 and e["brain_dropped"] == 1
            assert any(t == "tap_scrub" and f["by"] == "brain" for t, f in ev)


def test_a_session_id_that_is_not_a_ulid_never_names_a_file(tmp_path):
    w, ev, _c, _s = _writer(tmp_path)
    assert w.batch("node", "..", batch(rec(0, REQ))) == 0
    assert w.batch("node", "../../x", batch(rec(0, REQ))) == 0
    assert not (tmp_path / "tap").exists() and "tap_error" in ev.types()


def test_two_devices_with_one_session_id_get_their_own_files(tmp_path):
    w, _ev, _c, _s = _writer(tmp_path)
    w.batch("node", SESSION, batch(rec(0, REQ)))
    w.batch("guardian/x", SESSION, batch(rec(0, REQ)))
    w.close()
    files = sorted(os.listdir(tmp_path / "tap"))
    assert files == [f"{SESSION}-guardian_x.otap", f"{SESSION}.otap"]


# ---- pcapng ------------------------------------------------------------------------------ #
def read_pcapng(data: bytes) -> dict:
    """A minimal pcapng reader (little-endian, one section) for the round trip."""
    out = {"ifaces": [], "packets": [], "drops": {}, "shb_comment": None}
    off = 0
    while off < len(data):
        btype, total = struct.unpack_from("<II", data, off)
        assert total % 4 == 0 and struct.unpack_from("<I", data, off + total - 4)[0] == total
        body = data[off + 8:off + total - 4]
        if btype == 0x0A0D0D0A:
            magic, major, minor, _ = struct.unpack_from("<IHHq", body)
            assert (magic, major, minor) == (0x1A2B3C4D, 1, 0)
            out["shb_comment"] = _opts(body[16:]).get(1, [b""])[0].decode()
        elif btype == 1:
            linktype, _r, _snap = struct.unpack_from("<HHI", body)
            o = _opts(body[8:])
            out["ifaces"].append({"linktype": linktype, "name": o[2][0].decode(),
                                  "tsresol": o[9][0][0]})
        elif btype == 6:
            iface, hi, lo, cap, orig = struct.unpack_from("<IIIII", body)
            pkt = body[20:20 + cap]
            o = _opts(body[20 + cap + (-cap % 4):])
            out["packets"].append({"iface": iface, "t_us": (hi << 32) | lo, "data": pkt,
                                   "orig": orig,
                                   "flags": struct.unpack("<I", o[2][0])[0] if 2 in o else None,
                                   "comments": [c.decode() for c in o.get(1, [])]})
        elif btype == 5:
            iface = struct.unpack_from("<I", body)[0]
            o = _opts(body[12:])
            out["drops"][iface] = struct.unpack("<Q", o[5][0])[0]
        off += total
    return out


def _opts(b: bytes) -> dict:
    o, off = {}, 0
    while off + 4 <= len(b):
        code, ln = struct.unpack_from("<HH", b, off)
        if code == 0:
            break
        o.setdefault(code, []).append(b[off + 4:off + 4 + ln])
        off += 4 + ln + (-ln % 4)
    return o


def test_a_tap_fixture_round_trips_to_pcapng_with_its_gaps_reported(tmp_path):
    """Spec §14 P2 done-when: the firmware's Td5 tap, one batch lost in transit, through
    the writer and out as pcapng: every record that arrived is a packet with its bytes and
    time, the loss is a comment and an interface drop count."""
    msgs = tap_messages()
    meta = next(m for m in msgs if m["topic"].endswith("/meta"))
    data = [m for m in msgs if m["topic"].endswith("/data")]
    session = meta["topic"].split("/")[5]
    w, ev, _c, _s = _writer(tmp_path)
    w.header("node", session, meta["payload"])
    lost_batch = data[3]
    for m in data:
        if m is not lost_batch:
            w.batch("node", session, m["payload"])
    w.close()
    lost = [r.seq for r in T.parse_records(lost_batch["payload"])[0]]
    entry = w.entries()[0]
    assert entry["gaps"] == 1 and entry["lost"] == len(lost)
    (gap,) = [f for t, f in ev if t == "tap_gap"]
    assert (gap["from"], gap["to"]) == (lost[0], lost[-1])
    taps = read_tap(str(tmp_path), {"tap": w.entries()})
    pc = read_pcapng(to_pcapng(taps, {"id": "20261006T100000Z"}))
    # the node's time events are on an events interface, opened by the first mark
    assert pc["ifaces"] == [{"linktype": LINKTYPE_USER1, "name": "node events", "tsresol": 6},
                            {"linktype": LINKTYPE_USER0, "name": "kline-diag", "tsresol": 6}]
    assert "Timestamps are UTC, mapped from each node's time events" in pc["shb_comment"]
    want = [r for m in data if m is not lost_batch for r in T.parse_records(m["payload"])[0]]
    tm = T.TimeMap(want)
    assert tm
    assert [p["data"] for p in pc["packets"]] == [r.payload for r in want]
    # UTC in µs since the epoch, from the marks that arrived (2026-10-06T10:00Z onwards)
    assert [p["t_us"] for p in pc["packets"]] == [tm.utc_ns(r.t_us) // 1000 for r in want]
    assert pc["packets"][0]["t_us"] // 10**6 - 1_791_280_800 in range(0, 60)
    assert [p["flags"] for p in pc["packets"]] == [
        None if r.is_event else 2 if r.dir == T.DIR_TX_ECHO else 1 for r in want]
    mark = next(p for p in pc["packets"] if p["flags"] is None)
    assert any(c.startswith("time mark: t_us ") and "2026-10-06T10:00:" in c and
               c.endswith(", sntp)") for c in mark["comments"])
    after = next(p for p in pc["packets"] if f"seq {lost[-1] + 1}" in p["comments"]
                 or f"event 6 seq {lost[-1] + 1}" in p["comments"])
    assert f"seq gap: records {lost[0]}..{lost[-1]} lost ({len(lost)})" in after["comments"]
    assert sum(pc["drops"].values()) == len(lost)


def test_a_tap_without_time_events_keeps_the_node_clock(tmp_path):
    """No ``time`` event (a node without a clock, or an older firmware): the export keeps
    ``t_us`` as before and says so on the interface."""
    w, _ev, _c, _s = _writer(tmp_path)
    w.header("node", SESSION, header())
    w.batch("node", SESSION, batch(rec(0, REQ, flags=T.FLAG_UNSYNCED), rec(1, REPLY[:3])))
    w.close()
    pc = read_pcapng(to_pcapng(read_tap(str(tmp_path), {"tap": w.entries()}), {"id": "x"}))
    assert [p["t_us"] for p in pc["packets"]] == [1_000_000, 1_001_000]
    assert not any("extrapolated" in c for p in pc["packets"] for c in p["comments"])
    assert w.entries()[0]["time_marks"] == 0


def test_unsynced_records_before_the_first_mark_are_extrapolated_and_say_so(tmp_path):
    U = 1_791_280_800 * 10**9
    w, _ev, _c, _s = _writer(tmp_path)
    w.header("node", SESSION, header())
    w.batch("node", SESSION, batch(rec(0, REQ, t_us=500_000, flags=T.FLAG_UNSYNCED),
                                   _mark(1, 1_000_000, U), rec(2, REQ, t_us=1_250_000)))
    w.close()
    assert w.entries()[0]["time_marks"] == 1
    pc = read_pcapng(to_pcapng(read_tap(str(tmp_path), {"tap": w.entries()}), {"id": "x"}))
    assert [p["t_us"] for p in pc["packets"]] == [U // 1000 - 500_000, U // 1000,
                                                 U // 1000 + 250_000]
    assert "recorded before the node's clock was set: UTC extrapolated" in \
        pc["packets"][0]["comments"]
    assert all("UTC extrapolated" not in c for c in pc["packets"][2]["comments"])


def test_a_1a_reply_exports_with_only_the_placeholder(tmp_path):
    """Spec §13: even with identity recording on (so the ``.otap`` holds the bytes on this
    device), the export carries only the placeholder and no unframed record."""
    w, _ev, _c, _s = _writer(tmp_path, record_identity=True)
    w.header("node", SESSION, header("off"))
    w.batch("node", SESSION, batch(rec(0, REQ, d=T.DIR_TX_ECHO, flags=T.FLAG_GATE), rec(1, REPLY),
                                   rec(2, bytes([0x5A, 0x01]), flags=T.FLAG_UNFRAMED),
                                   rec(3, bytes([0x04, 0x61, 0x09, 0x03, 0x0C]))))
    w.close()
    assert SECRET in (tmp_path / "tap" / f"{SESSION}.otap").read_bytes()  # local only
    body = to_pcapng(read_tap(str(tmp_path), {"tap": w.entries()}), {"id": "x"})
    assert SECRET not in body
    pc = read_pcapng(body)
    datas = [p["data"] for p in pc["packets"]]
    assert datas == [REQ, bytes([0x5A, 0x9B]) + T.PLACEHOLDER, bytes([0x04, 0x61, 0x09, 0x03, 0x0C])]
    assert "identity data scrubbed" in pc["packets"][1]["comments"]
    assert "sent by the node's gate" in pc["packets"][0]["comments"]
    assert pc["drops"] == {0: 0}  # a dropped unframed record is not a loss


def test_pcapng_can_and_events_interfaces():
    bus = [{"idx": 0, "bus_id": "kline-diag", "proto": "kline"},
           {"idx": 1, "bus_id": "can-hs", "proto": "can"}]
    records = [rec(0, REQ), _can(1, 0x7E8, [0x04, 0x41, 0x0C, 0x1A, 0xF8], bus=1),
               rec(2, b"\xa1\x01\x02", typ=T.TYPE_EVENT, d=T.EV_OVERFLOW, bus=0xFF)]
    entry = {"session": SESSION, "device": "node", "buses": bus}
    pc = read_pcapng(to_pcapng([(entry, records)], {"id": "x"}))
    assert [i["linktype"] for i in pc["ifaces"]] == [LINKTYPE_USER0, LINKTYPE_CAN_SOCKETCAN,
                                                    LINKTYPE_USER1]
    assert [i["name"] for i in pc["ifaces"]] == ["kline-diag", "can-hs", "node events"]
    can = pc["packets"][1]["data"]
    assert can[:8] == struct.pack(">IBBBB", 0x7E8, 5, 0, 0, 0) and can[8:] == bytes(
        [0x04, 0x41, 0x0C, 0x1A, 0xF8])
    assert pc["packets"][2]["data"] == b"\xa1\x01\x02" and pc["packets"][2]["flags"] is None


def test_no_tap_no_pcapng():
    with pytest.raises(ValueError):
        to_pcapng([], {"id": "x"})
