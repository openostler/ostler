# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``ostler share verify`` (trip-sharing spec §9.3, §16 "Verifier"): one failing bundle per
check, each failing with its check and rule; exit code 2 for an unreadable or wrong-format
file; the writer never emits a failing bundle. Failing bundles are made by tampering with a
verified one built from the recorded node fixture (``tests/share_fixtures.py``); the VIN
is assembled at run time."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile

import pytest

from openostler.logbook.share import (OwnerContext, ShareBlocked, ShareOptions, build_share,
                                      verify_bundle, verify_bytes)
from openostler.logbook.share import bundle as bmod
from openostler.logbook.share.capture import EventPacket, Packet, cbor_t_us, write_pcapng
from openostler.logbook.share.zones import PrivacyZone
from openostler.node.identity import IdentityTable
from tests.share_fixtures import (can, grid_drive, isotp_frames, kwp, record_node_session,
                                  synthetic_vin, write_gps_session)

pytestmark = pytest.mark.fake_pack


@pytest.fixture(scope="module")
def l3(tmp_path_factory):
    sess = record_node_session(str(tmp_path_factory.mktemp("node")))
    return build_share(sess, ShareOptions("L3", audience="person"))


@pytest.fixture(scope="module")
def l1(tmp_path_factory):
    sess = write_gps_session(str(tmp_path_factory.mktemp("gps")), grid_drive())
    return build_share(sess, ShareOptions("L1"))


def unzip(data: bytes) -> dict:
    zf = zipfile.ZipFile(io.BytesIO(data))
    return {n: zf.read(n) for n in zf.namelist()}


def rezip(files: dict, *, rehash: bool = True, edit=None, date_time=None,
          names=None) -> bytes:
    """A tampered copy: ``files`` (None removes), the hashes recomputed unless ``rehash``
    is False, ``edit(share)`` applied to share.json."""
    files = {k: v for k, v in files.items() if v is not None}
    share = json.loads(files["share.json"])
    if rehash:
        share["files"] = [{"path": n, "sha256": hashlib.sha256(b).hexdigest(),
                           "bytes": len(b), "kind": "tap" if n.startswith("tap/") else
                           next((f["kind"] for f in share["files"] if f["path"] == n), "data")}
                          for n, b in sorted(files.items()) if n != "share.json"]
    if edit:
        edit(share)
    files["share.json"] = json.dumps(share).encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names or sorted(files):
            zf.writestr(zipfile.ZipInfo(n, date_time=date_time or (1980, 1, 1, 0, 0, 0)),
                        files[n])
    return buf.getvalue()


def checks(res) -> set:
    return {(f.check, f.rule) for f in res.failures}


def test_the_untampered_bundles_pass(l3, l1):
    for b in (l3, l1):
        res = verify_bytes(b.data)
        assert res.ok and res.exit_code == 0 and res.level == b.manifest["level"]
        assert rezip(unzip(b.data)) and verify_bytes(rezip(unzip(b.data))).ok


# ---- check 1: files, hashes, paths, entry times ----------------------------------------- #
def test_check1_an_unlisted_file(l3):
    files = unzip(l3.data)
    data = rezip(dict(files, **{"notes.jsonl": b"{}\n"}), rehash=False)
    res = verify_bytes(data)
    assert (1, "R16") in checks(res) and res.exit_code == 1


def test_check1_a_hash_mismatch_and_a_missing_file(l3):
    files = unzip(l3.data)
    res = verify_bytes(rezip(dict(files, **{"README.txt": b"changed\n"}), rehash=False))
    assert any(f.check == 1 and "hash" in f.detail for f in res.failures)
    res = verify_bytes(rezip(dict(files, **{"README.txt": None}), rehash=False))
    assert any(f.check == 1 and "missing" in f.detail for f in res.failures)


def test_check1_an_unknown_path_and_a_wrong_entry_time(l3):
    files = unzip(l3.data)
    res = verify_bytes(rezip(dict(files, **{"extra/hello.txt": b"hi\n"})))
    assert any(f.check == 1 and f.detail == "unknown path" for f in res.failures)
    res = verify_bytes(rezip(files, date_time=(2026, 10, 7, 9, 30, 0)))
    assert (1, "R9") in checks(res)
    res = verify_bytes(rezip(files, names=sorted(files, reverse=True)))
    assert any("sorted" in f.detail for f in res.failures)


# ---- check 2: identity (R1–R3) ---------------------------------------------------------- #
def test_check2_a_vin_pattern_in_any_file(l3):
    files = unzip(l3.data)
    trip = json.loads(files["trip.json"])
    trip["note"] = "chassis " + synthetic_vin()
    res = verify_bytes(rezip(dict(files, **{"trip.json": json.dumps(trip).encode()})))
    assert (2, "R3") in checks(res)
    assert any(f.file == "trip.json" and "note" in f.detail for f in res.failures)


def _tap(packets, proto="kline", events=()):
    return write_pcapng(0, proto, packets, list(events), "test")


def test_check2_an_unscrubbed_identity_reply_and_seed_key_on_k_line(l3):
    files = unzip(l3.data)
    for msg in (kwp(b"\x5a\x9b" + b"ABC123"), kwp(b"\x67\x01\x12\x34"),
                kwp(b"\x62\xf1\x8c" + b"SN0042")):
        res = verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": _tap([Packet(10, msg)])})))
        assert (2, "R1") in checks(res), msg


def test_check2_an_unscrubbed_multi_frame_message_inside_reassembled_iso_tp(l3):
    files = unzip(l3.data)
    vin = synthetic_vin().encode()
    frames = isotp_frames(b"\x62\xf1\x90" + vin)
    # the VIN split across frames: no single frame holds 17 VIN characters
    pk = [Packet(10 + i, can(0, 0x7E8, f).payload) for i, f in enumerate(frames)]
    res = verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": _tap(pk, "can")})))
    assert (2, "R2") in checks(res)
    assert any("ISO-TP message" in f.detail for f in res.failures if f.rule == "R3")


def test_check2_a_declared_service_from_the_pack(l3):
    files = unzip(l3.data)
    msg = kwp(b"\x61\x9a\x01\x02\x03")
    data = rezip(dict(files, **{"tap/bus0.pcapng": _tap([Packet(10, msg)])}))
    assert verify_bytes(data).ok
    table = IdentityTable.platform().with_declaration({"local_ids": [{"service": "21",
                                                                      "id": "9A"}]})
    assert (2, "R1") in checks(verify_bytes(data, table=table))


# ---- check 3: unframed (R4) ------------------------------------------------------------- #
def test_check3_an_unframed_record_or_an_unparsable_tap(l3):
    files = unzip(l3.data)
    res = verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": _tap([Packet(10, b"\x01\x02\x33")])})))
    assert (3, "R4") in checks(res)
    res = verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": b"\x00" * 40})))
    assert (3, "R4") in checks(res)


# ---- check 4: location ------------------------------------------------------------------ #
def test_check4_gps_with_location_none(l3):
    files = unzip(l3.data)
    lines = files["data.csv"].decode().split("\n")
    lines[0] += ',"GPS_Latitude"|"deg"|0'
    lines = [lines[0]] + [ln + ",53.2" if ln else ln for ln in lines[1:]]
    res = verify_bytes(rezip(dict(files, **{"data.csv": "\n".join(lines).encode()})))
    assert (4, "R8") in checks(res)
    trip = json.loads(files["trip.json"])
    trip["start_pos"] = [-1.6, 53.2]
    res = verify_bytes(rezip(dict(files, **{"trip.json": json.dumps(trip).encode()})))
    assert (4, "R8") in checks(res)


def test_check4_a_point_timestamp_in_a_route(l1):
    files = unzip(l1.data)
    gpx = files["track.gpx"].decode().replace("</trkpt>", "<time>x</time></trkpt>", 1)
    res = verify_bytes(rezip(dict(files, **{"track.gpx": gpx.encode()})))
    assert (4, "R7") in checks(res)


def test_check4_a_route_fix_inside_a_zone_on_the_owners_device(l1):
    files = unzip(l1.data)
    geo = json.loads(files["track.geojson"])
    lon, lat = geo["features"][0]["geometry"]["coordinates"][0][1]
    zone = PrivacyZone("z", "Friend", lat, lon, 500, 0.0, 0.0)
    assert verify_bytes(l1.data).ok                                   # not knowable elsewhere
    res = verify_bytes(l1.data, owner=OwnerContext(zones=[zone]))
    assert (4, "R5") in checks(res)
    res = verify_bytes(l1.data, owner=OwnerContext(hidden_fixes=[(lat, lon)]))
    assert any("ends trim" in f.detail for f in res.failures)


# ---- check 5: time ---------------------------------------------------------------------- #
def test_check5_a_date_or_time_outside_relative_time(l3):
    files = unzip(l3.data)
    ev = files["events.jsonl"] + b'{"t": 1, "type": "note", "when": "2026-10-06"}\n'
    assert (5, "R9") in checks(verify_bytes(rezip(dict(files, **{"events.jsonl": ev}))))
    ev = files["events.jsonl"] + b'{"t": 1, "type": "x", "utc": 5}\n'
    assert (5, "R9") in checks(verify_bytes(rezip(dict(files, **{"events.jsonl": ev}))))
    ev = files["events.jsonl"] + b'{"t": 1, "type": "x", "tap": "01M48AFR80CDXA0ZQ1XBS3VHSS"}\n'
    assert (5, "R10") in checks(verify_bytes(rezip(dict(files, **{"events.jsonl": ev}))))


def test_check5_an_absolute_capture_timestamp_or_a_time_mark(l3):
    files = unzip(l3.data)
    good = kwp(b"\x61\x09\x03\x0c")
    tap = _tap([Packet(1_791_280_800 * 10**6, good)])
    assert (5, "R9") in checks(verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": tap}))))
    real_mark = bytes([6]) + b"\xa2\x64t_us\x01\x66utc_ns\x02"
    tap = _tap([Packet(10, good)], events=[EventPacket(10, 6, real_mark[1:])])
    assert (5, "R9") in checks(verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": tap}))))
    tap = _tap([Packet(10, good)], events=[EventPacket(10, 6, cbor_t_us(10))])
    assert verify_bytes(rezip(dict(files, **{"tap/bus0.pcapng": tap}))).ok


def test_check5_l0_and_l1_are_day_basis_only(l1):
    res = verify_bytes(rezip(unzip(l1.data), edit=lambda s: s.update(time_basis="relative")))
    assert (5, "R9") in checks(res)


# ---- check 6: network identity (R14) ---------------------------------------------------- #
@pytest.mark.parametrize("text", ["peer at 10.0.0.7", "mac 00:1A:2B:3C:4D:5E",
                                  "Authorization: Bearer abcdefghij0123",
                                  "fp AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99",
                                  "host car.tail9.ts.net", "-----BEGIN PUBLIC KEY-----",
                                  "addr fe80::1ff:fe23:4567:890a"])
def test_check6_network_identity_anywhere(l3, text):
    files = unzip(l3.data)
    readme = files["README.txt"] + text.encode() + b"\n"
    assert (6, "R14") in checks(verify_bytes(rezip(dict(files, **{"README.txt": readme}))))


def test_check6_a_declared_key_that_is_not_redacted(l3):
    files = unzip(l3.data)
    trip = json.loads(files["trip.json"])
    trip["ssid"] = "HomeNet"
    assert (6, "R14") in checks(verify_bytes(rezip(dict(files, **{"trip.json": json.dumps(trip).encode()}))))


# ---- check 7: level content ------------------------------------------------------------- #
def test_check7_level_content(l3, l1):
    files = unzip(l3.data)
    res = verify_bytes(rezip(files, edit=lambda s: s.update(level="L2")))
    assert any(f.check == 7 and f.file == "tap/bus0.pcapng" for f in res.failures)
    res = verify_bytes(rezip(dict(files, **{"diag/versions.json": b"{}\n"})))
    assert any(f.check == 7 and f.file == "diag/versions.json" for f in res.failures)
    res = verify_bytes(rezip(files, edit=lambda s: s.update(level="L0", time_basis="day")))
    assert any(f.check == 7 and f.file == "data.csv" for f in res.failures)
    res = verify_bytes(rezip(dict(unzip(l1.data), **{"track.gpx": None, "track.geojson": None}),
                             edit=lambda s: s.update(location="none")))
    assert (7, "R16") in checks(res)


# ---- check 8: share.json ---------------------------------------------------------------- #
@pytest.mark.parametrize("edit", [
    lambda s: s.update(vin="placeholder"),
    lambda s: s["vehicle"].update(vin_hmac="00"),
    lambda s: s.update(device_id="node"),
    lambda s: s.update(user_id="u1"),
    lambda s: s.update(signature="x"),
    lambda s: s.update(colour="green"),
    lambda s: s.update(id="NOT-HEX"),
    lambda s: s.pop("redactions"),
    lambda s: s["licence"].update(derived_data="CC-BY-SA-4.0"),
])
def test_check8_a_forbidden_unknown_or_malformed_field(l3, edit):
    res = verify_bytes(rezip(unzip(l3.data), edit=edit))
    assert (8, "R16") in checks(res) and res.exit_code == 1


# ---- exit 2 ----------------------------------------------------------------------------- #
def test_exit_2_for_unreadable_or_other_formats(l3, tmp_path):
    assert verify_bytes(b"plain text").exit_code == 2
    no_manifest = io.BytesIO()
    with zipfile.ZipFile(no_manifest, "w") as zf:
        zf.writestr("README.txt", "x")
    assert verify_bytes(no_manifest.getvalue()).exit_code == 2
    for fmt in ("ostler.share/2", "other/1", None):
        res = verify_bytes(rezip(unzip(l3.data), edit=lambda s, f=fmt: s.update(format=f)))
        assert res.exit_code == 2 and not res.ok
    assert verify_bundle(str(tmp_path / "nope.zip")).exit_code == 2
    assert json.loads(json.dumps(verify_bytes(b"x").to_json()))["exit_code"] == 2


# ---- the writer gate -------------------------------------------------------------------- #
def test_the_writer_never_emits_a_bundle_that_fails(tmp_path, monkeypatch):
    sess = write_gps_session(str(tmp_path), grid_drive())
    real = bmod.zip_bytes

    def leaky(files):
        files = dict(files)
        files["README.txt"] = files["README.txt"] + b"relay at 192.168.0.9\n"
        return real(files)

    monkeypatch.setattr(bmod, "zip_bytes", leaky)
    with pytest.raises(ShareBlocked) as exc:
        build_share(sess, ShareOptions("L0"))
    assert {(f.check, f.rule) for f in exc.value.failures} >= {(6, "R14")}
