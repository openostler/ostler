# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``ostler.layout/1`` (drive-modes spec §4, §5, §8.2, §10; DM1).

The server validator (``openostler.layouts``) against the shared cases in
``tests/fixtures/layouts/cases.json`` (the shell's ``ui/src/drive/validate.test.ts`` runs the
same cases), the JSON Schema on the same documents, and the seven shipped presets
(``ui/src/drive/presets/*.json``) for every layout class.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from openostler import layouts
from openostler.layouts import graphemes, validate_bytes, validate_layout

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/layouts/cases.json").read_text(encoding="utf-8"))["cases"]
PRESETS = sorted((ROOT / "ui/src/drive/presets").glob("*.json"))
CLASSES = ("hu5", "hu7", "hu9", "huwide", "phone", "tablet", "desktop")
DRIVING = ("hu5", "hu7", "hu9", "huwide", "phone")


def _schema_errors(doc) -> list:
    jsonschema = pytest.importorskip("jsonschema", reason="dev-only: pip install -e '.[dev]'")
    schema = json.loads((ROOT / "schemas/ostler-layout.schema.json").read_text(encoding="utf-8"))
    return list(jsonschema.Draft202012Validator(schema).iter_errors(doc))


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_shared_cases(case):
    r = validate_layout(case["doc"])
    assert r.rules() == case["errors"], [(i.rule, i.message) for i in r.errors]
    assert set(case["warnings"]) <= {i.rule for i in r.warnings}
    assert r.ok == (not case["errors"])


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_shared_cases_against_the_json_schema(case):
    assert (not _schema_errors(case["doc"])) == case["schema_ok"]


def test_every_moving_rule_has_a_case():
    """Each strict Moving rule (§4.3) is exercised by a refused case."""
    refused = {r for c in CASES for r in c["errors"]}
    for rule in ("moving.too_many_tiles", "moving.too_many_panes", "moving.duplicate_pane", "moving.parked_only",
                 "moving.sparkline", "moving.animation", "moving.refresh", "moving.tile_too_small",
                 "moving.pane_too_small", "moving.missing", "moving.hidden", "moving.overlap"):
        assert rule in refused, rule


def test_type_floors_refuse_a_class_below_56_px_digits_or_24_px_labels(monkeypatch):
    lim = json.loads(layouts.LIMITS_FILE.read_text(encoding="utf-8"))
    good = next(c["doc"] for c in CASES if c["name"] == "valid three tiles on HU-7")
    assert validate_layout(good).ok
    for key, value in (("digits", 48), ("label", 20)):
        patched = json.loads(json.dumps(lim))
        patched["classes"]["hu7"]["type"][key] = value
        monkeypatch.setattr(layouts, "limits", lambda p=patched: p)
        assert "moving.type_floor" in validate_layout(good).rules(), key
    assert lim["moving"]["digits_floor_px"] == 56 and lim["moving"]["label_floor_px"] == 24
    for cls, c in lim["classes"].items():
        assert c["type"]["digits"] >= 56 and c["type"]["label"] >= 24, cls


def test_unknown_paths_are_warnings_and_known_ones_are_quiet():
    good = next(c["doc"] for c in CASES if c["name"] == "valid three tiles on HU-7")
    doc = json.loads(json.dumps(good))
    doc["classes"]["hu7"][0]["widgets"][0]["bind"] = {"path": "Vehicle.Ostler.Nothing.Here"}
    r = validate_layout(doc)
    assert r.ok and [i.rule for i in r.warnings] == ["path.unknown"]
    assert not validate_layout(good).warnings


def test_size_limit_and_bad_json():
    assert validate_bytes(b"x" * (256 * 1024 + 1)).rules() == ["size.too_big"]
    assert validate_bytes(b"{nope").rules() == ["schema"]
    good = next(c["doc"] for c in CASES if c["name"] == "valid three tiles on HU-7")
    assert validate_bytes(json.dumps(good).encode()).ok


def test_graphemes_count_user_perceived_characters():
    assert graphemes("Coolant") == 7
    assert graphemes("é") == 1
    assert graphemes("\U0001F468‍\U0001F469") == 1  # a ZWJ sequence


# ---- the seven presets (§5) ------------------------------------------------------------ #

def test_seven_presets_ship():
    assert [p.stem for p in PRESETS] == ["convoy", "dashboard", "diagnostic", "map", "minimal", "offroad", "split"]


@pytest.mark.parametrize("path", PRESETS, ids=[p.stem for p in PRESETS])
def test_presets_validate_for_every_class(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert not _schema_errors(doc)
    r = validate_layout(doc, raw_size=path.stat().st_size)
    assert r.ok, [(i.rule, i.cls, i.face, i.message) for i in r.errors]
    assert doc["id"] == f"ostler.{path.stem}" and doc["license"] == "CC-BY-SA-4.0"
    assert sorted(doc["classes"]) == sorted(CLASSES)
    for cls in DRIVING:
        for face in doc["classes"][cls]:
            assert "moving" in face, (cls, face["face"])
    # nothing identifying (§4.2): a pack hint at most, never a vid, VIN or plate
    assert set(doc.get("vehicle_hint", {})) <= {"pack"}
    text = path.read_text(encoding="utf-8")
    for word in ('"vid"', '"vin"', '"plate"'):
        assert word not in text.lower()


def test_hidden_presets_say_what_they_need():
    """Split / Media needs a media source and Convoy an active ride (§5.4, §5.6, §6)."""
    by_id = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in PRESETS}
    assert by_id["split"]["requires"]["capabilities"] == ["media_source"]
    assert by_id["convoy"]["requires"]["capabilities"] == ["ride_active"]
    for pid in ("dashboard", "diagnostic", "map", "minimal", "offroad"):
        assert "capabilities" not in by_id[pid].get("requires", {}), pid


def test_presets_bind_vss_paths_or_the_pack_drive_view():
    """Presets name no pack signal (layering: the platform names no pack); the Diagnostic
    preset reads the pack's own Drive view by position."""
    for p in PRESETS:
        doc = json.loads(p.read_text(encoding="utf-8"))
        for faces in doc["classes"].values():
            for face in faces:
                for w in face["widgets"]:
                    binds = [w[k] for k in ("bind", "bind2") if k in w] + [v["bind"] for v in w.get("values", [])]
                    for b in binds:
                        assert set(b) in ({"path"}, {"drive_tile"}), (p.stem, b)


def test_pack_manifest_lists_the_vss_paths_each_module_publishes():
    """``GET /pack`` ``metrics`` lets a Drive mode tell "Not in this session" from "Not
    available on this car" (§4.2)."""
    from tests.fake_pack import FAKE_PACK

    metrics = FAKE_PACK.manifest()["metrics"]
    module_ids = {m.id for m in FAKE_PACK.modules}
    assert isinstance(metrics, dict)
    for path, modules in metrics.items():
        assert path.startswith("Vehicle.") and modules and set(modules) <= module_ids
