# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The widened identity scrub (trip-sharing spec §8; R1–R4; ADR-0036).

The synthetic-VIN injection of spec §8.4 runs on the **firmware's recorded tap fixture**
(``td5-vectors.jsonl``) recorded through the product's ``SessionRecorder`` with the install
option on (identity stored unscrubbed on the device, ADR-0036 §3), plus CAN frames shaped
as the shared ISO-TP vectors segment them. The VIN is assembled at run time
(:func:`tests.share_fixtures.synthetic_vin`): no VIN literal is committed. It is injected
as a Mode 09 reply, a ``62 F1 90`` multi-frame reply (a first frame and two consecutive
frames), a KWP ``5A 90`` reply, a declared broadcast frame and an undeclared broadcast
frame; the first four are scrubbed, the last blocks the share naming the frame."""
from __future__ import annotations

import dataclasses
import io
import zipfile

import pytest

from openostler.logbook.share import ShareBlocked, ShareOptions, build_share
from openostler.logbook.share.capture import read_candump, read_pcapng, socketcan_to_tap
from openostler.logbook.share.scrub import isotp_messages, scrub_records
from openostler.logbook.tap import read_tap
from openostler.node import tap as T
from openostler.node.identity import (PLACEHOLDER, IdentityTable, is_placeholder,
                                      kline_frame_ok, placeholder)
from openostler.pack import active_identity_table, use_pack
from tests.fake_pack import FAKE_PACK
from tests.share_fixtures import (can, fixture_tap, isotp_frames, kline, kwp,
                                  record_node_session, synthetic_vin)

pytestmark = pytest.mark.fake_pack

BROADCAST = 0x3E0
UNDECLARED = 0x3E1


def _vin() -> bytes:
    return synthetic_vin().encode("ascii")


def identity_records(vin: bytes, *, undeclared: bool = False) -> "list[T.TapRecord]":
    """The injected records, at times inside the fixture's span (1.35 s to 19 s)."""
    t = 6_000_000
    out = [
        # K-line (bus 0): KWP ReadEcuIdentification 1A 90 → 5A 90 <VIN>
        kline(t, kwp(b"\x1a\x90"), tx=True), kline(t + 30_000, kwp(b"\x5a\x90" + vin)),
        # SecurityAccess seed and key, then the bare "access granted"
        kline(t + 60_000, kwp(b"\x27\x01"), tx=True),
        kline(t + 90_000, kwp(b"\x67\x01\x12\x34")),
        kline(t + 120_000, kwp(b"\x27\x02\x56\x78"), tx=True),
        kline(t + 150_000, kwp(b"\x67\x02\x34")),
        # UDS ECU serial over K-line
        kline(t + 180_000, kwp(b"\x62\xf1\x8c" + b"SN0042")),
        # an unframed run and a per-byte record (dropped, R4)
        kline(t + 210_000, b"\x01\x49\x33", flags=T.FLAG_UNFRAMED),
        kline(t + 220_000, b"\x5a", proto=T.PROTO_KLINE_BYTE),
    ]
    # CAN (bus 1): Mode 09 VIN on 7E8 (FF + 2 CF) with its request and flow control
    t = 8_000_000
    out.append(can(t, 0x7DF, [0x02, 0x09, 0x02, 0x55, 0x55, 0x55, 0x55, 0x55], tx=True))
    ff, *cfs = isotp_frames(b"\x49\x02\x01" + vin)
    out.append(can(t + 10_000, 0x7E8, ff))
    out.append(can(t + 12_000, 0x7E0, [0x30, 0x00, 0x00, 0x55, 0x55, 0x55, 0x55, 0x55], tx=True))
    out += [can(t + 14_000 + i * 1000, 0x7E8, f) for i, f in enumerate(cfs)]
    # UDS 62 F1 90 on 7E9: a first frame and two consecutive frames
    ff, *cfs = isotp_frames(b"\x62\xf1\x90" + vin)
    assert len(cfs) == 2
    out.append(can(t + 30_000, 0x7E9, ff))
    out += [can(t + 32_000 + i * 1000, 0x7E9, f) for i, f in enumerate(cfs)]
    # an ordinary reply that must stay byte for byte
    out.append(can(t + 40_000, 0x7E8, [0x04, 0x41, 0x0C, 0x1A, 0xF8, 0x55, 0x55, 0x55]))
    # a broadcast frame that spells the VIN over three frames (a mux byte first)
    for cid in (BROADCAST,) + ((UNDECLARED,) if undeclared else ()):
        for i in range(3):
            chunk = vin[i * 7:(i + 1) * 7]
            out.append(can(t + 50_000 + i * 100_000 + (cid & 1) * 1000, cid,
                           list(bytes([i]) + chunk + b"\x00" * (7 - len(chunk)))))
    return out


DECLARING = dataclasses.replace(FAKE_PACK, identity={
    "broadcast_frames": [{"bus": "can-diag", "can_id": "3E0"}]})


def _files(b) -> dict:
    zf = zipfile.ZipFile(io.BytesIO(b.data))
    return {n: zf.read(n) for n in zf.namelist()}


@pytest.fixture
def injected(tmp_path):
    return record_node_session(str(tmp_path / "sessions"), identity_records(_vin()))


def test_the_store_holds_the_identity_with_the_install_option_on(injected):
    """The precondition: with the option on the device keeps the raw bytes (ADR-0036 §3)."""
    from openostler.logbook.recorder import _read_meta

    meta = _read_meta(injected + "/meta.json")
    raw = b"".join(r.payload for _e, recs in read_tap(injected, meta) for r in recs)
    assert _vin() in raw


@pytest.mark.parametrize("level", ["L3", "L4"])
def test_the_vin_injection_is_scrubbed_everywhere_and_every_other_byte_kept(injected, level):
    vin = _vin()
    with use_pack(DECLARING):
        b = build_share(injected, ShareOptions(level, audience="person"))
    files = _files(b)
    assert {"tap/bus0.pcapng", "tap/bus1.pcapng", "tap/bus1.candump", "data.csv"} <= set(files)
    for name, body in files.items():
        assert vin not in body, name
        assert vin[:9] not in body and vin[8:] not in body, name
    # K-line: the scrubbed frames keep header, service and option, length and a checksum
    k = read_pcapng(files["tap/bus0.pcapng"])
    msgs = [p for _i, _t, p in k.packets if _i == 0]
    assert all(kline_frame_ok(m) for m in msgs)
    reply = next(m for m in msgs if m[1:3] == b"\x5a\x90")
    assert reply[0] == 2 + 17 and reply[3:-1] == placeholder(17)
    seed = next(m for m in msgs if m[1:3] == b"\x67\x01")
    key = next(m for m in msgs if m[1:3] == b"\x27\x02")
    assert is_placeholder(seed[3:-1]) and is_placeholder(key[3:-1])
    assert kwp(b"\x27\x01") in msgs                          # a bare seed request stays
    assert kwp(b"\x67\x02" + PLACEHOLDER[:1]) in msgs        # data after the sub-function
    serial = next(m for m in msgs if m[1:4] == b"\x62\xf1\x8c")
    assert is_placeholder(serial[4:-1])
    # every fixture K-line message is there unchanged; unframed and per-byte records gone
    _s, _h, fixture = fixture_tap()
    originals = {r.payload for r in fixture if r.type == T.TYPE_DATA}
    assert originals <= set(msgs)
    assert b"\x01\x49\x33" not in msgs and b"\x5a" not in msgs
    # CAN: PCI bytes and lengths kept, data placeholdered, other frames byte for byte
    c = read_pcapng(files["tap/bus1.pcapng"])
    frames = [socketcan_to_tap(p) for _i, _t, p in c.packets if _i == 0]
    dump = read_candump(files["tap/bus1.candump"].decode())
    assert [(cid, d) for _t, _if, cid, _e, d in dump] == \
        [(int.from_bytes(f[0:4], "little") & 0x7FF, f[5:]) for f in frames]
    by_id = {}
    for f in frames:
        by_id.setdefault(int.from_bytes(f[0:4], "little"), []).append(f[5:])
    msgs09 = isotp_messages([(i, 0x7E8, d) for i, d in enumerate(by_id[0x7E8])])
    vin09 = next(m for m in msgs09 if m.data[:2] == b"\x49\x02")
    assert len(vin09.parts) == 3 and vin09.complete
    assert vin09.data[:2] == b"\x49\x02" and is_placeholder(bytes(vin09.data[2:]))
    assert [d[0] for d in by_id[0x7E8][:3]] == [0x10, 0x21, 0x22]     # PCI kept
    assert bytes([0x04, 0x41, 0x0C, 0x1A, 0xF8, 0x55, 0x55, 0x55]) in by_id[0x7E8]
    (uds,) = isotp_messages([(i, 0x7E9, d) for i, d in enumerate(by_id[0x7E9])])
    assert uds.data[:3] == b"\x62\xf1\x90" and is_placeholder(bytes(uds.data[3:]))
    assert by_id[0x7E0] == [bytes([0x30, 0x00, 0x00, 0x55, 0x55, 0x55, 0x55, 0x55])]
    assert all(is_placeholder(d) for d in by_id[BROADCAST])
    # the redaction record counts it all
    red = {(r["rule"], r["detail"]): r["count"] for r in b.manifest["redactions"]}
    by_rule = {}
    for (rule, _d), n in red.items():
        by_rule[rule] = by_rule.get(rule, 0) + n
    assert by_rule["R1"] >= 4 + 3          # 5A 90, seed, key, serial; 3 broadcast frames
    assert by_rule["R2"] == 6              # two FF + two CF each
    assert by_rule["R4"] == 2


def test_an_undeclared_broadcast_vin_blocks_the_share_naming_the_frame(tmp_path):
    sess = record_node_session(str(tmp_path), identity_records(_vin(), undeclared=True))
    with use_pack(DECLARING), pytest.raises(ShareBlocked) as exc:
        build_share(sess, ShareOptions("L3", audience="person"))
    fails = exc.value.failures
    assert fails and all(f.check == 2 and f.rule == "R3" for f in fails)
    assert {f.file for f in fails} == {"tap/bus1.pcapng", "tap/bus1.candump"}
    assert all(f"CAN id {UNDECLARED:X}" in f.detail and "frame" in f.detail for f in fails)


def test_without_the_declaration_the_broadcast_frame_blocks_too(injected):
    with pytest.raises(ShareBlocked, match="3E0"):
        build_share(injected, ShareOptions("L3", audience="person"))


def test_a_session_the_brain_scrubbed_at_write_shares_with_its_flags_kept(tmp_path):
    """The default install (option off): the Brain scrubbed at write; the share keeps the
    node's or Brain's ``scrubbed`` records as they are and adds nothing back."""
    sess = record_node_session(str(tmp_path), identity_records(_vin()), record_identity=False)
    with use_pack(DECLARING):
        b = build_share(sess, ShareOptions("L3", audience="person"))
    assert all(_vin() not in body for body in _files(b).values())
    assert any(r["detail"].startswith("records already scrubbed") for r in b.manifest["redactions"])


# ---- the scrubber's units ------------------------------------------------------------------- #
def _recs(*frames, bus=1):
    return [can(i * 1000, cid, d, bus=bus) for i, (cid, d) in enumerate(frames)]


def test_identity_is_decided_on_the_reassembled_message():
    """A CAN FD first frame with the 32-bit length escape pushes the service past the
    bytes a naive first-frame check reads; reassembly still finds it."""
    vin = _vin()
    msg = b"\x62\xf1\x90" + vin
    ff = [0x10, 0x00] + list(len(msg).to_bytes(4, "big")) + list(msg[:2])
    rest = msg[2:]
    cfs = [[0x20 | ((i + 1) & 0xF)] + list(rest[i * 7:(i + 1) * 7]) for i in range(3)]
    out, counts = scrub_records(_recs((0x7E8, ff), *[(0x7E8, c) for c in cfs]),
                                IdentityTable.platform())
    (m,) = isotp_messages([(i, 0, r.payload[5:]) for i, r in enumerate(out)])
    assert m.complete and m.data[:3] == b"\x62\xf1\x90" and is_placeholder(bytes(m.data[3:]))
    assert counts.isotp_frames == 4
    assert out[0].payload[5:] == bytes(ff)          # the FF holds only the kept 62 F1
    assert all(r.flags & T.FLAG_SCRUBBED for r in out[1:])
    # the node's streaming check cannot see it
    assert T.IdentityScrub().check(_recs((0x7E8, ff))[0]).flags & T.FLAG_SCRUBBED == 0


def test_an_unreassemblable_message_is_scrubbed_to_the_next_first_or_single_frame():
    frames = [(0x7E8, [0x10, 0x14, 0x41, 0x00, 0xBE, 0x3F, 0xA8, 0x13]),   # not identity
              (0x7E8, [0x21, 1, 2, 3, 4, 5, 6, 7]),
              (0x7E8, [0x23, 8, 9, 10, 11, 12, 13, 14]),                    # SN 3: lost 2
              (0x7E8, [0x24, 15, 16, 17, 18, 19, 20, 21]),
              (0x7E0, [0x30, 0x00, 0x00, 0, 0, 0, 0, 0]),                   # FC stays
              (0x7E8, [0x03, 0x41, 0x0D, 0x32, 0x55, 0x55, 0x55, 0x55])]    # SF stays
    recs = _recs(*frames)
    out, counts = scrub_records(recs, IdentityTable.platform())
    datas = [r.payload[5:] for r in out]
    assert [d[0] for d in datas] == [f[1][0] for f in frames]             # PCI kept
    assert all(set(d[1 if d[0] >> 4 == 2 else 2:]) <= set(PLACEHOLDER) for d in datas[:4])
    assert datas[4:] == [bytes(f[1]) for f in frames[4:]]
    assert counts.isotp_frames == 4


def test_seed_and_key_are_scrubbed_on_can_too():
    out, counts = scrub_records(_recs((0x7E8, [0x04, 0x67, 0x01, 0xAB, 0xCD, 0, 0, 0]),
                                      (0x7E0, [0x02, 0x27, 0x01, 0, 0, 0, 0, 0])),
                                IdentityTable.platform())
    assert out[0].payload[5:9] == bytes([0x04, 0x67, 0x01]) + PLACEHOLDER[:1]
    assert out[1].payload[5:] == bytes([0x02, 0x27, 0x01, 0, 0, 0, 0, 0])
    assert counts.identity == 1


# ---- the one table, widened ----------------------------------------------------------------- #
@pytest.mark.parametrize("data, keep", [
    (b"\x5a\x90abc", 2), (b"\x49\x02\x01abc", 2), (b"\x62\xf1\x90abc", 3),
    (b"\x62\xf1\x8cabc", 3), (b"\x67\x01\x12\x34", 2), (b"\x27\x02\x56\x78", 2),
    (b"\x67\x02", 0), (b"\x27\x01", 0), (b"\x62\xf4\x05\x10", 0), (b"\x61\x09\x03\x0c", 0),
])
def test_the_platform_list(data, keep):
    assert IdentityTable.platform().match(data) == keep


def test_pack_declarations_add_to_the_table_and_reach_every_path():
    pack = dataclasses.replace(FAKE_PACK, identity={
        "services": ["1B"], "dids": ["F18A"], "local_ids": [{"service": "21", "id": "9A"}],
        "diag_ids": ["6F1"], "seed_key": True})
    with use_pack(pack):
        table = active_identity_table()
    assert table.match(b"\x5b\x01\x02") == 2                 # 1B declared by its request
    assert table.match(b"\x62\xf1\x8a\x01") == 3
    assert table.match(b"\x61\x9a\x01\x02") == 2 and table.match(b"\x61\x9b\x01") == 0
    assert table.is_diagnostic_id(0x6F1, False) and not table.is_diagnostic_id(0x6F2, False)
    assert IdentityTable.platform().match(b"\x61\x9a\x01") == 0
    # the recorder's streaming scrub (and so the pcapng export) uses the same table
    msg = kwp(b"\x61\x9a\x01\x02\x03")
    assert T.scrub_kline(msg, False, table) == (b"\x61\x9a" + PLACEHOLDER, True)
    assert T.scrub_kline(msg, False) == (msg, False)


def test_the_node_rule_widens_to_uds_seed_key_and_iso9141_on_k_line():
    vin = _vin()
    assert T.scrub_kline(kwp(b"\x62\xf1\x90" + vin), False) == (b"\x62\xf1\x90" + PLACEHOLDER, True)
    assert T.scrub_kline(kwp(b"\x67\x01\x12\x34"), False)[1] is True
    assert T.scrub_kline(kwp(b"\x67\x02\x34"), False)[1] is True     # data after the sub-function
    assert T.scrub_kline(kwp(b"\x67\x02"), False)[1] is False
    iso = bytes([0x48, 0x6B, 0x10, 0x49, 0x02, 0x01]) + vin[:4]
    iso += bytes([sum(iso) & 0xFF])
    assert T.scrub_kline(iso, False) == (b"\x49\x02" + PLACEHOLDER, True)
    assert T.scrub_kline(b"\x01\x67\x33", True) == (PLACEHOLDER, True)   # unframed run
