# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The ``ostler.share/1`` bundle (trip-sharing spec §3, §6, §7, §9, §16): the files of each
level, time handling, fresh ids, policy refusals, ``share.json`` against its schema, the
L4 ``diag/`` files and the ``ostler share`` command. Sessions: the recorded
``legacy_session_motor`` fixture, a node session recorded from the firmware's tap fixture
and a **synthetic** GPS trip (``tests/share_fixtures.py``)."""
from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import jsonschema
import pytest

from openostler import cli
from openostler.logbook.recorder import _read_meta
from openostler.logbook.share import (ShareBlocked, ShareOptions, ShareRefused, build_share,
                                      verify_bytes, write_share)
from openostler.logbook.share.capture import read_pcapng
from openostler.logbook.share.verify import ZIP_TIME
from tests.share_fixtures import grid_drive, record_node_session, synthetic_vin, write_gps_session

pytestmark = pytest.mark.fake_pack

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMA = json.loads((Path(__file__).parents[1] / "schemas" / "share.schema.json").read_text())
BASE = {"README.txt", "share.json", "trip.json"}
DIAG = {"diag/versions.json", "diag/modules.json", "diag/manifests.json",
        "diag/link_stats.json"}


def files_of(b) -> dict:
    zf = zipfile.ZipFile(io.BytesIO(b.data))
    return {n: zf.read(n) for n in zf.namelist()}


def schema_errors(doc) -> list:
    return [e.message for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(doc)]


@pytest.fixture
def gps(tmp_path):
    return write_gps_session(str(tmp_path / "gps"), grid_drive())


@pytest.fixture
def node(tmp_path):
    return record_node_session(str(tmp_path / "node"))


@pytest.fixture
def legacy(tmp_path):
    src = FIXTURES / "legacy_session_motor" / "20260528T202640Z"
    dst = tmp_path / "legacy" / src.name
    shutil.copytree(src, dst)
    return str(dst)


# ---- levels ------------------------------------------------------------------------------ #
@pytest.mark.parametrize("level, kw, want", [
    ("L0", {}, BASE),
    ("L1", {}, BASE | {"track.gpx", "track.geojson"}),
    ("L2", {"audience": "person"}, BASE | {"data.csv", "faults.json"}),
    ("L2", {"audience": "person", "route": True},
     BASE | {"data.csv", "faults.json", "track.gpx", "track.geojson"}),
    ("L3", {"audience": "person"}, BASE | {"data.csv", "faults.json", "events.jsonl"}),
    ("L4", {"audience": "maintainers"},
     BASE | {"data.csv", "faults.json", "events.jsonl"} | DIAG),
])
def test_each_level_holds_exactly_its_files(gps, level, kw, want):
    b = build_share(gps, ShareOptions(level, **kw))
    assert set(files_of(b)) == want
    assert b.verify.ok and b.manifest["level"] == level
    assert not schema_errors(b.manifest)


def test_a_node_session_at_l3_and_l4_carries_the_scrubbed_tap(node):
    for level in ("L3", "L4"):
        names = set(files_of(build_share(node, ShareOptions(level, audience="person"))))
        assert "tap/bus0.pcapng" in names and not any(n.endswith(".candump") for n in names)


@pytest.mark.parametrize("level", ["L0", "L1", "L2", "L3", "L4"])
def test_the_recorded_fixture_session_shares_at_every_level_it_may(legacy, level):
    opts = ShareOptions(level, audience="person")
    if level == "L1":         # 240 m recorded: under 1 km, a card only
        with pytest.raises(ShareRefused, match="under 1 km"):
            build_share(legacy, opts)
        return
    b = build_share(legacy, opts)
    assert b.verify.ok and not schema_errors(b.manifest)
    # the recording is never changed (every rule works on a copy)
    assert _read_meta(legacy + "/meta.json")["id"] == "20260528T202640Z"


def test_l2_without_a_route_has_no_location_anywhere(gps):
    b = build_share(gps, ShareOptions("L2", audience="person", signals=["speed", "rpm"]))
    files = files_of(b)
    header = files["data.csv"].decode().split("\n")[0]
    assert re.findall(r'"([^"]+)"\|"[^"]*"\|', header) == ["Interval", "speed", "rpm"]
    blob = b"".join(files.values()).decode()
    for word in ("GPS_", "Utc", "Latitude", "Longitude", "Altitude", "Heading", "region"):
        assert word not in blob
    assert b.manifest["location"] == "none" and b.manifest["signals"] == ["speed", "rpm"]


def test_l2_with_the_route_ticked_keeps_point_times_out_of_data_csv(gps):
    files = files_of(build_share(gps, ShareOptions("L2", audience="group", route=True)))
    assert "GPS_" not in files["data.csv"].decode()
    assert "<time" not in files["track.gpx"].decode()


def test_l3_with_location_to_one_named_person_keeps_trimmed_gps_rows(gps):
    b = build_share(gps, ShareOptions("L3", audience="person", recipient="Sam", route=True))
    csv_text = files_of(b)["data.csv"].decode()
    assert "GPS_Latitude" in csv_text and "Utc" not in csv_text
    first = csv_text.split("\n")[1]
    assert 0 <= float(first.split(",")[0]) < 1000      # t = 0 at the first visible sample
    assert b.manifest["location"] == "route"


# ---- time (§6, R9) ---------------------------------------------------------------------- #
_DATE = re.compile(rb"(19|20)\d\d-[01]\d-[0-3]\d")


@pytest.mark.parametrize("level", ["L2", "L3", "L4"])
def test_relative_bundles_hold_no_date_or_time_but_the_fixed_zip_time(node, level):
    b = build_share(node, ShareOptions(level, audience="person"))
    files = files_of(b)
    for name, body in files.items():
        if name != "share.json":
            assert not _DATE.search(body), name
    for info in zipfile.ZipFile(io.BytesIO(b.data)).infolist():
        assert info.date_time == ZIP_TIME
    if level != "L2":
        cap = read_pcapng(files["tap/bus0.pcapng"])
        assert cap.packets and all(t < 600 * 10**6 for _i, t, _d in cap.packets)
        events = [d for i, _t, d in cap.packets if i == 1]
        assert events and all(b"utc_ns" not in d for d in events)
    assert b.manifest["time_basis"] == "relative"


def test_l0_and_l1_carry_the_day_only(gps):
    trip = json.loads(files_of(build_share(gps, ShareOptions("L1")))["trip.json"])
    assert trip["day"] == "2026-10-06" and "start_s" not in trip


@pytest.mark.parametrize("kw", [
    {"path": "file", "audience": "person", "recipient": "Sam"},
    {"path": "relay", "audience": "helpers"},
    {"path": "hub", "audience": "person", "recipient": "Sam"},
    {"path": "pack_issue", "audience": "maintainers"},
    {"path": "relay", "audience": "person"},                       # no named recipient
    {"path": "relay", "audience": "person", "recipient": "Sam", "public_destination": True},
])
def test_keep_real_time_is_refused_except_by_relay_to_one_named_person(gps, kw):
    with pytest.raises(ShareRefused, match="real date"):
        build_share(gps, ShareOptions("L3", keep_real_time=True, **kw))


def test_keep_real_time_by_relay_to_one_named_person(node):
    b = build_share(node, ShareOptions("L3", audience="person", recipient="Sam", path="relay",
                                       keep_real_time=True))
    assert b.manifest["time_basis"] == "real"
    assert "Utc" in files_of(b)["data.csv"].decode().split("\n")[0]


def test_public_destinations_force_no_location_and_relative_time(gps):
    b = build_share(gps, ShareOptions("L3", audience="maintainers", path="pack_issue"))
    assert b.manifest["location"] == "none" and b.manifest["time_basis"] == "relative"


# ---- ids (§7, R10) ---------------------------------------------------------------------- #
def test_no_source_id_reaches_a_bundle_and_two_bundles_share_none(node):
    meta = _read_meta(node + "/meta.json")
    a = build_share(node, ShareOptions("L4", audience="person"))
    b = build_share(node, ShareOptions("L4", audience="person"))
    tap = meta["tap"][0]
    secret = [meta["id"], meta["vid"], tap["session"], tap["device"] + "\"",
              "@" + tap["device"] + "\"", f'"boot_id": {tap["boot_id"]}']
    for bundle in (a, b):
        blob = b"".join(files_of(bundle).values()).decode("utf-8", "replace")
        for s in secret:
            assert s not in blob, s
        assert not re.search(r"[0-9A-HJKMNP-TV-Z]{26}", blob)       # no ULID
        assert "Vehicle.Speed@node-1" in files_of(bundle)["data.csv"].decode()
    ta, tb = json.loads(files_of(a)["trip.json"]), json.loads(files_of(b)["trip.json"])
    assert ta["session"] != tb["session"] and re.fullmatch(r"s-[a-z2-7]{16}", ta["session"])
    assert a.manifest["id"] != b.manifest["id"] and a.name != b.name
    assert re.fullmatch(r"ostler-share-[a-z2-7]{8}\.zip", a.name)
    # the owner's map leads back to the source, and only the owner has it
    assert a.id_map["session"] == {ta["session"]: meta["id"]}
    assert a.id_map["device"] == {"node-1": tap["device"]}
    assert a.id_map["vid"] == {"vehicle-1": meta["vid"]}


def test_bundles_are_not_signed(gps):
    b = build_share(gps, ShareOptions("L1"))
    blob = json.dumps(b.manifest)
    for word in ("signature", "kid", "brain", "jws", "key_id"):
        assert word not in blob.lower()


# ---- policy (§3, §10; ADR-0043) -------------------------------------------------------- #
@pytest.mark.parametrize("opts, msg", [
    (ShareOptions("L3", audience="person", path="grant"), "never a grant"),
    (ShareOptions("L4", audience="maintainers", path="grant"), "never a grant"),
    (ShareOptions("L2", audience="link"), "never goes to a link"),
    (ShareOptions("L2", audience="public"), "never goes to a link"),
    (ShareOptions("L3", audience="group"), "one named person"),
    (ShareOptions("L4", audience="public"), "one named person"),
    (ShareOptions("L3", audience="helpers", route=True), "location only to one named person"),
    (ShareOptions("L3", audience="person", route=True), "location only to one named person"),
    (ShareOptions("L1", route=True), "L1 tick"),
    (ShareOptions("L5"), "unknown level"),
    (ShareOptions("L1", ends_m=150), "floor"),
])
def test_refusals(gps, opts, msg):
    with pytest.raises(Exception, match=msg):
        build_share(gps, opts)


def test_contribution_consent_is_off_by_default(gps):
    b = build_share(gps, ShareOptions("L3", audience="maintainers", credit="Sam"))
    assert b.manifest["contribution_consent"] is False
    assert b.manifest["licence"] == {"derived_data": None} and b.manifest["credit"] is None
    c = build_share(gps, ShareOptions("L3", audience="maintainers", contribution_consent=True,
                                      credit="Sam", request={"kind": "decode",
                                                             "question": "fuel temp?"}))
    assert c.manifest["licence"] == {"derived_data": "CC-BY-SA-4.0"}
    assert c.manifest["credit"] == "Sam" and c.manifest["request"]["kind"] == "decode"
    assert not schema_errors(c.manifest)
    assert schema_errors(dict(c.manifest, contribution_consent=False))


def test_the_vehicle_card_shows_nickname_and_plate_only_when_ticked(gps):
    v = {"make": "Land Rover", "model": "Discovery", "year": 2002, "engine": "Td5",
         "nickname": "Big Green", "plate": "AB12 CDE"}
    b = build_share(gps, ShareOptions("L0", vehicle=v))
    blob = b"".join(files_of(b).values()).decode()
    assert "Big Green" not in blob and "AB12" not in blob and "Td5" in blob
    b = build_share(gps, ShareOptions("L0", vehicle=v, show_nickname=True, show_plate=True))
    assert b.manifest["vehicle"]["plate"] == "AB12 CDE"
    assert json.loads(files_of(b)["trip.json"])["vehicle"]["nickname"] == "Big Green"


def test_a_vin_in_the_card_text_blocks_the_share(gps):
    with pytest.raises(ShareBlocked) as exc:
        build_share(gps, ShareOptions("L0", vehicle={"nickname": "car " + synthetic_vin()},
                                      show_nickname=True))
    assert {f.check for f in exc.value.failures} == {2}
    assert {f.file for f in exc.value.failures} >= {"trip.json", "share.json"}


# ---- L4 (§9.1, R14) --------------------------------------------------------------------- #
def test_l4_diag_redacts_network_identity(node):
    log = ("10:00:01 mqtt connected to 192.168.1.20:8883 as brain.tail1234.ts.net\n"
           "wifi aa:bb:cc:dd:ee:ff ssid in use; Authorization: Bearer abcdefghijkl123\n")
    cfg = {"mqtt": {"host": "brain.local", "token": "s3cret"}, "wifi": {"ssid": "Home"},
           "poll_hz": 2}
    b = build_share(node, ShareOptions("L4", audience="maintainers", log_tail=log, config=cfg))
    files = files_of(b)
    assert DIAG | {"diag/log_tail.txt", "diag/config.json"} <= set(files)
    tail = files["diag/log_tail.txt"].decode()
    for leak in ("192.168", "aa:bb", "tail1234", "abcdefghijkl", "10:00:01"):
        assert leak not in tail
    conf = json.loads(files["diag/config.json"])
    assert conf == {"mqtt": {"host": "**REDACTED**", "token": "**REDACTED**"},
                    "wifi": {"ssid": "**REDACTED**"}, "poll_hz": 2}
    assert any(r["rule"] == "R14" for r in b.manifest["redactions"])
    manifests = json.loads(files["diag/manifests.json"])
    assert manifests == {"devices": [{"device": "node-1", "fw": None}]} or \
        all(d["device"].startswith("node-") for d in manifests["devices"])


# ---- the command (§9.3) ----------------------------------------------------------------- #
def test_ostler_share_build_and_verify(node, tmp_path, capsys):
    out = tmp_path / "out"
    rc = cli.main(["share", "build", "--session", node, "--level", "L3", "--audience",
                   "person", "--out", str(out), "--state-dir", str(tmp_path / "state")])
    path = capsys.readouterr().out.strip()
    assert rc == 0 and Path(path).parent == out
    audit = (tmp_path / "state" / "share_audit.jsonl").read_text().splitlines()
    assert json.loads(audit[0])["id_map"]["device"] == {"node-1": "node"}
    assert (tmp_path / "state" / "share_audit.jsonl").stat().st_mode & 0o077 == 0
    assert cli.main(["share", "verify", path]) == 0
    assert "passed (L3)" in capsys.readouterr().out
    assert cli.main(["share", "verify", path, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["passed"] is True
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    assert cli.main(["share", "verify", str(bad)]) == 2
    assert cli.main(["share", "verify", str(tmp_path / "missing.zip")]) == 2
    rc = cli.main(["share", "build", "--session", node, "--level", "L3", "--audience",
                   "group", "--out", str(out)])
    assert rc == 1 and "refused" in capsys.readouterr().err


def test_write_share_never_overwrites(gps, tmp_path):
    b = build_share(gps, ShareOptions("L0"))
    p = write_share(b, str(tmp_path))
    assert Path(p).read_bytes() == b.data and verify_bytes(b.data).ok
    with pytest.raises(FileExistsError):
        write_share(b, str(tmp_path))
