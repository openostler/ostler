# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""JSON Schemas for the platform's file formats (ADR-0017, specs/2026-10-06-u0-seams-design.md §A).

Every schema in ``schemas/`` is a valid JSON Schema 2020-12 document with an ``$id`` under
``https://ostler.tech/schemas/``. The tests validate the fake pack's store and layout, the
Discovery 2 pack's (``needs_pack``), a freshly recorded session's ``meta.json`` and
``vehicle.json``. ``jsonschema`` is dev-only.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema", reason="dev-only: pip install -e '.[dev]'")

from openostler.logbook import vehicle
from openostler.logbook.recorder import SessionRecorder
from tests.fake_pack import FAKE_PACK

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"
NAMES = ("signal-store", "layout", "vehicle", "session-meta")


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def _validate(name: str, doc) -> None:
    cls = jsonschema.Draft202012Validator
    cls(_schema(name), format_checker=cls.FORMAT_CHECKER).validate(doc)


def _errors(name: str, doc) -> list:
    return list(jsonschema.Draft202012Validator(_schema(name)).iter_errors(doc))


@pytest.mark.parametrize("name", NAMES)
def test_schema_is_valid_2020_12(name):
    s = _schema(name)
    assert s["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert s["$id"] == f"https://ostler.tech/schemas/{name}.schema.json"
    jsonschema.Draft202012Validator.check_schema(s)


def test_every_schema_file_is_listed():
    assert sorted(p.name for p in SCHEMAS.glob("*.schema.json")) == \
        sorted(f"{n}.schema.json" for n in NAMES)


# ---- signal store and layout --------------------------------------------------------- #

def test_fake_pack_store_and_layout_validate():
    files = sorted(Path(FAKE_PACK.signals_dir).glob("*.json"))
    assert files
    for f in files:
        _validate("signal-store", json.loads(f.read_text(encoding="utf-8")))
    _validate("layout", dict(FAKE_PACK.layout))


def test_signal_store_schema_rejects_bad_records():
    ok = {"name": "rpm", "lid": "09", "offset": 0}
    assert not _errors("signal-store", [ok])
    assert not _errors("signal-store", [{**ok, "metric": "Vehicle.Speed", "x-note": 1}])
    for bad in ({**ok, "metric": "Speed"}, {**ok, "confidence": "maybe"}, {**ok, "kind": "f32"},
                {**ok, "surprise": True}, {"name": "rpm", "lid": "09"}):
        assert _errors("signal-store", [bad]), bad


@pytest.mark.needs_pack
def test_d2_pack_store_and_layout_validate():
    pytest.importorskip("d2diag")
    from openostler.pack import active_pack

    pack = active_pack()
    files = sorted(Path(pack.signals_dir).glob("*.json"))
    assert files
    for f in files:
        _validate("signal-store", json.loads(f.read_text(encoding="utf-8")))
    _validate("layout", dict(pack.layout))


# ---- session meta and vehicle.json --------------------------------------------------- #

@pytest.mark.fake_pack
def test_fresh_session_meta_and_vehicle_json_validate(tmp_path, monkeypatch):
    monkeypatch.delenv(vehicle.ENV_VID, raising=False)
    t = {"s": 0.0}
    rec = SessionRecorder(str(tmp_path / "sessions"), clock=lambda: 1791277200.0 + t["s"],
                          mono=lambda: 10.0 + t["s"], min_free_bytes=0)
    for i in range(3):
        t["s"] = float(i)
        rec.feed({"conn": "connected", "module": "alpha", "mode": "live", "faults": [],
                  "signals": {"alpha_speed": {"v": 900.0 + i, "u": "rpm"}}}, None)
    sid = rec.session_id
    live = json.loads((tmp_path / "sessions" / sid / "meta.json").read_text(encoding="utf-8"))
    _validate("session-meta", live)
    rec.close()
    done = json.loads((tmp_path / "sessions" / sid / "meta.json").read_text(encoding="utf-8"))
    _validate("session-meta", done)
    assert done["vid"] and done["end_utc"].endswith("Z")
    _validate("vehicle", json.loads((tmp_path / "vehicle.json").read_text(encoding="utf-8")))


def test_session_meta_schema_requires_utc_z():
    meta = {"id": "20261006T090000Z", "start_utc": "2026-10-06T09:00:00.000+01:00",
            "end_utc": None, "duration_s": 0, "rows": 0, "parts": [], "modules": [],
            "channels": [], "has_gps": False, "distance_km": 0.0, "max_speed_kmh": None,
            "bbox": None, "start_pos": None, "end_pos": None, "synthetic": False,
            "recording": True, "source": "live"}
    assert _errors("session-meta", meta)
    assert not _errors("session-meta", {**meta, "start_utc": "2026-10-06T09:00:00.000Z"})


def test_vehicle_schema_rejects_a_vin_field():
    rec = {"vid": "3f9a1c07", "pack": "lr_d2", "created_utc": "2026-10-06T09:00:00.000Z"}
    assert not _errors("vehicle", rec)
    assert _errors("vehicle", {**rec, "vin": "not-allowed"})
