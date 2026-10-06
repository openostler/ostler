"""The vehicle id seam (UI spec §4.1, specs/2026-10-06-u0-seams-design.md §A).

``logs/vehicle.json`` holds the local ``vid``; new sessions carry it; a legacy session
without one reads as the local vid (never rewritten); ``OSTLER_VEHICLE_ID`` overrides it;
the session index (schema 3) stores it.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from openostler.logbook import index as idxmod
from openostler.logbook import vehicle
from openostler.logbook.index import SessionIndex
from openostler.logbook.recorder import SessionRecorder
from openostler.logbook.store import SessionStore

pytestmark = pytest.mark.fake_pack

LEGACY = Path(__file__).resolve().parent / "fixtures" / "legacy_session_motor"
LEGACY_ID = "20260528T202640Z"
T0 = 1791277200.0  # 2026-10-06T09:00:00Z


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    monkeypatch.delenv(vehicle.ENV_VID, raising=False)


def _record(sessions: Path, **kw) -> dict:
    """Open one session (connected poll) and return its meta.json as written."""
    t = {"s": 0.0}
    rec = SessionRecorder(str(sessions), clock=lambda: T0 + t["s"], mono=lambda: 50.0 + t["s"],
                          min_free_bytes=0, **kw)
    rec.feed({"conn": "connected", "module": "alpha", "mode": "live", "faults": [],
              "signals": {"alpha_speed": {"v": 900.0, "u": "rpm"}}}, None)
    t["s"] = 1.0
    rec.feed({"conn": "connected", "module": "alpha", "mode": "live", "faults": [],
              "signals": {"alpha_speed": {"v": 910.0, "u": "rpm"}}}, None)
    sid = rec.session_id
    rec.close()
    return json.loads((sessions / sid / "meta.json").read_text(encoding="utf-8"))


def test_vehicle_json_is_created_once_and_stable_across_restarts(tmp_path):
    first = vehicle.ensure_vehicle(str(tmp_path), pack="lr_d2", clock=lambda: T0)
    assert vehicle.VID_RE.match(first["vid"]) and len(first["vid"]) == 8
    assert first == {"vid": first["vid"], "pack": "lr_d2",
                     "created_utc": "2026-10-06T09:00:00.000Z"}
    raw = (tmp_path / "vehicle.json").read_bytes()
    again = vehicle.ensure_vehicle(str(tmp_path), pack="other", clock=lambda: T0 + 99)
    assert again == first
    assert (tmp_path / "vehicle.json").read_bytes() == raw     # never rewritten
    assert vehicle.local_vid(str(tmp_path)) == first["vid"]


def test_vehicle_json_records_the_active_pack(tmp_path):
    rec = vehicle.ensure_vehicle(str(tmp_path))
    assert rec["pack"] == "fake"


def test_new_session_has_the_local_vid(tmp_path):
    meta = _record(tmp_path / "sessions")
    want = json.loads((tmp_path / "vehicle.json").read_text(encoding="utf-8"))["vid"]
    assert meta["vid"] == want
    # a restart (new recorder) keeps the same vid
    assert _record(tmp_path / "sessions")["vid"] == want


def test_explicit_vid_and_synthetic_sessions(tmp_path):
    assert _record(tmp_path / "a", vid="d2-green")["vid"] == "d2-green"
    synth = _record(tmp_path / "b", synthetic=True)
    assert "vid" not in synth                       # demo logs stay byte-stable
    assert not (tmp_path / "vehicle.json").exists()


def test_env_override(tmp_path, monkeypatch):
    vehicle.ensure_vehicle(str(tmp_path))
    raw = (tmp_path / "vehicle.json").read_bytes()
    monkeypatch.setenv(vehicle.ENV_VID, "garage-1")
    assert _record(tmp_path / "sessions")["vid"] == "garage-1"
    assert (tmp_path / "vehicle.json").read_bytes() == raw
    store = SessionStore(str(tmp_path / "sessions"), demo_root=None)
    assert store.vid == "garage-1"
    monkeypatch.setenv(vehicle.ENV_VID, "not a vid!")   # invalid: ignored
    assert vehicle.local_vid(str(tmp_path)) == json.loads(raw)["vid"]


def test_legacy_session_reads_as_the_local_vid_and_is_never_rewritten(tmp_path):
    root = tmp_path / "sessions"
    shutil.copytree(LEGACY, root)
    before = {p.name: p.read_bytes() for p in (root / LEGACY_ID).iterdir()}
    assert "vid" not in json.loads(before["meta.json"])
    local = vehicle.local_vid(str(tmp_path))
    store = SessionStore(str(root), demo_root=None)
    assert store.meta(LEGACY_ID)["vid"] == local
    assert [m["vid"] for m in store.list()] == [local]
    idx = SessionIndex(str(tmp_path / "index.sqlite"), store)
    assert idx.page()["sessions"][0]["vid"] == local
    idx.close()
    after = {p.name: p.read_bytes() for p in (root / LEGACY_ID).iterdir()}
    assert after == before


def test_index_schema_3_rebuilds_an_older_index(tmp_path):
    assert idxmod.SCHEMA_VERSION == 3
    root = tmp_path / "sessions"
    shutil.copytree(LEGACY, root)
    db_path = tmp_path / "index.sqlite"
    con = sqlite3.connect(db_path)   # a schema-2 index: no vid column
    con.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, start_ms INTEGER NOT NULL, "
                "meta_json TEXT NOT NULL, sig TEXT)")
    con.execute("INSERT INTO sessions VALUES ('stale', 0, '{}', '')")
    con.execute("PRAGMA user_version=2")
    con.commit()
    con.close()
    store = SessionStore(str(root), demo_root=None, vid="abc12345")
    idx = SessionIndex(str(db_path), store)
    con = sqlite3.connect(db_path)
    try:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 3
        cols = [r[1] for r in con.execute("PRAGMA table_info(sessions)")]
        assert "vid" in cols
        assert con.execute("SELECT id, vid FROM sessions").fetchall() == [(LEGACY_ID, "abc12345")]
    finally:
        con.close()
        idx.close()


def test_unwritable_state_dir_keeps_a_stable_in_memory_vid(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    state = str(blocker / "logs")          # a path under a regular file: cannot be created
    a = vehicle.local_vid(state)
    assert vehicle.VID_RE.match(a) and vehicle.local_vid(state) == a
