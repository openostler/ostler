# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The ``ui_layouts`` store (drive-modes spec §7.8, §8.3; DM2): the key, resolution order
(user → car → pack → generated), validation on write, the Before reset snapshot with its
7 days, held changes (R7) and the selected Drive mode per display."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from openostler.layout_store import (
    SNAPSHOT_TTL_S,
    LayoutRejected,
    LayoutStore,
    check_selection,
    driver_facing,
)

ROOT = Path(__file__).resolve().parents[1]
PRESET = json.loads((ROOT / "ui/src/drive/presets/dashboard.json").read_text(encoding="utf-8"))


def user_mode(lid: str = "user.my-dash", name: str = "My dash") -> dict:
    """A user's copy of the Dashboard preset: a full copy with its base reference."""
    doc = json.loads(json.dumps(PRESET))
    doc.update(id=lid, name=name, base={"preset": "ostler.dashboard", "version": 1})
    doc.pop("version", None)
    return doc


class Clock:
    def __init__(self, t: float = 1_800_000_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def store(tmp_path, clock):
    s = LayoutStore(str(tmp_path / "settings.sqlite"), clock=clock)
    yield s
    s.close()


def test_tables_and_schema_version(store):
    db = sqlite3.connect(store.db_path)
    names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"ui_layouts", "ui_layout_snapshots", "ui_layouts_held", "ui_drive_selection"} <= names
    assert db.execute("PRAGMA user_version").fetchone()[0] == 1
    db.close()


def test_a_newer_schema_is_refused_not_rebuilt(tmp_path):
    path = tmp_path / "settings.sqlite"
    db = sqlite3.connect(path)
    db.execute("PRAGMA user_version=99")
    db.close()
    with pytest.raises(RuntimeError, match="newer"):
        LayoutStore(str(path))


def test_put_get_and_rev(store):
    doc = user_mode()
    a = store.put("v1", "car", "hu7", doc)
    assert a["source"] == "car" and a["profile"] == "car" and a["rev"] == 1 and a["layout"] == doc
    assert a["updated_utc"].endswith("Z") and a["etag"].startswith('"')
    doc2 = {**doc, "name": "Renamed"}
    b = store.put("v1", "car", "hu7", doc2)
    assert b["rev"] == 2 and b["etag"] != a["etag"] and b["layout"]["name"] == "Renamed"


def test_the_key_separates_vehicle_profile_class_kind_and_id(store):
    store.put("v1", "car", "hu7", user_mode())
    assert store.resolve("v2", "car", "hu7", "drive_mode", "user.my-dash")["source"] == "generated"
    assert store.resolve("v1", "car", "hu9", "drive_mode", "user.my-dash")["source"] == "generated"
    assert store.resolve("v1", "car", "hu7", "home", "user.my-dash")["source"] == "generated"
    assert store.resolve("v1", "car", "hu7", "drive_mode", "user.other")["source"] == "generated"


def test_resolution_order_user_then_car_then_pack_then_generated(store):
    lid = "ostler.dashboard"
    pack_doc = {**user_mode(lid, "Pack dash")}
    gen = store.resolve("v1", "alice", "hu7", "drive_mode", lid)
    assert gen["source"] == "generated" and gen["layout"] is None and gen["etag"] == '"generated"'
    assert store.resolve("v1", "alice", "hu7", "drive_mode", lid, [pack_doc])["source"] == "pack"
    store.put("v1", "car", "hu7", user_mode(lid, "Car dash"))
    r = store.resolve("v1", "alice", "hu7", "drive_mode", lid, [pack_doc])
    assert (r["source"], r["profile"], r["layout"]["name"]) == ("car", "car", "Car dash")
    store.put("v1", "alice", "hu7", user_mode(lid, "Alice dash"))
    r = store.resolve("v1", "alice", "hu7", "drive_mode", lid, [pack_doc])
    assert (r["source"], r["profile"], r["layout"]["name"]) == ("user", "alice", "Alice dash")
    # another user still sees the car's
    assert store.resolve("v1", "bob", "hu7", "drive_mode", lid)["layout"]["name"] == "Car dash"
    # a pack document for another class does not resolve here
    assert store.resolve("v1", "bob", "hu5", "drive_mode", lid,
                         [{**pack_doc, "classes": {"hu7": pack_doc["classes"]["hu7"]}}])["source"] == "generated"


def test_list_merges_profile_car_and_pack(store):
    store.put("v1", "car", "hu7", user_mode("user.a", "A"))
    store.put("v1", "alice", "hu7", user_mode("user.b", "B"))
    store.put("v1", "alice", "hu7", user_mode("user.a", "A for Alice"))
    pack_doc = user_mode("pack.c", "C")
    rows = store.list("v1", "alice", "hu7", pack_layouts=[pack_doc])
    assert [(r["id"], r["source"]) for r in rows] == [
        ("pack.c", "pack"), ("user.a", "user"), ("user.b", "user")]
    assert [r["id"] for r in store.list("v1", "bob", "hu7")] == ["user.a"]
    assert store.list("v1", "alice", "hu7", kind="home") == []


@pytest.mark.parametrize("mutate,rule", [
    (lambda d: d["classes"]["hu7"][0]["moving"]["show"].extend(["x1"]), "layout_invalid"),
    (lambda d: d.pop("base"), "base_missing"),
    (lambda d: d.update(base={"preset": "ostler.dashboard"}), "base_missing"),
    (lambda d: d.update(format="ostler.layout/2"), "layout_invalid"),
    (lambda d: d["classes"].pop("hu7"), "layout_class"),
])
def test_put_refuses_with_the_validators_errors(store, mutate, rule):
    doc = user_mode()
    mutate(doc)
    with pytest.raises(LayoutRejected) as exc:
        store.put("v1", "car", "hu7", doc)
    assert exc.value.rule == rule
    if rule == "layout_invalid":
        assert exc.value.errors and {"rule", "message"} <= set(exc.value.errors[0])
    assert store.list("v1", "car", "hu7") == []


def test_seven_tiles_while_moving_are_refused_with_the_class_named(store):
    doc = user_mode()
    face = doc["classes"]["hu7"][0]
    extra = [{"slot": f"t{i}", "widget": "ostler.tile", "at": [0, 0], "size": "small",
              "bind": {"path": "Vehicle.Speed"}} for i in range(7)]
    face["widgets"] += extra
    face["moving"] = {"show": [w["slot"] for w in extra], "grid": {"cols": 7, "rows": 1},
                      "place": {w["slot"]: [i, 0, 1, 1] for i, w in enumerate(extra)}}
    with pytest.raises(LayoutRejected) as exc:
        store.put("v1", "car", "hu7", doc)
    rules = {e["rule"] for e in exc.value.errors}
    assert "moving.too_many_tiles" in rules
    assert any(e.get("class") == "hu7" for e in exc.value.errors)


def test_delete_reverts_to_the_base_and_keeps_a_snapshot(store, clock):
    lid = "ostler.dashboard"
    store.put("v1", "car", "hu7", user_mode(lid, "Mine"))
    assert store.delete("v1", "car", "hu7", "drive_mode", lid) is True
    assert store.resolve("v1", "car", "hu7", "drive_mode", lid)["source"] == "generated"
    snap = store.snapshot("v1", "car", "hu7")
    assert snap["scope"] == f"drive_mode/{lid}" and snap["layouts"] == [{"kind": "drive_mode", "id": lid}]
    assert store.delete("v1", "car", "hu7", "drive_mode", lid) is False  # nothing stored
    assert store.snapshot("v1", "car", "hu7") is not None  # an empty delete keeps it
    assert store.undo_reset("v1", "car", "hu7") == 1
    assert store.resolve("v1", "car", "hu7", "drive_mode", lid)["layout"]["name"] == "Mine"
    assert store.snapshot("v1", "car", "hu7") is None


def test_reset_scopes_and_the_one_snapshot(store):
    store.put("v1", "car", "hu7", user_mode("user.a", "A"))
    store.put("v1", "car", "hu7", user_mode("user.b", "B"))
    store.put("v1", "car", "hu9", user_mode("user.a", "A9"))
    store.put("v1", "alice", "hu7", user_mode("user.a", "Alice"))
    assert store.reset("v1", "car", "hu7", "home") == 0
    assert store.reset("v1", "car", "hu7") == 2
    assert store.list("v1", "car", "hu7") == []
    # only this profile and class: hu9 and alice keep theirs
    assert [r["id"] for r in store.list("v1", "car", "hu9")] == ["user.a"]
    assert store.resolve("v1", "alice", "hu7", "drive_mode", "user.a")["source"] == "user"
    snap = store.snapshot("v1", "car", "hu7")
    assert snap["scope"] == "all" and len(snap["layouts"]) == 2
    # an edit after the reset is overwritten by Undo reset at the snapshot's keys only
    store.put("v1", "car", "hu7", user_mode("user.a", "A2"))
    store.put("v1", "car", "hu7", user_mode("user.c", "C"))
    assert store.undo_reset("v1", "car", "hu7") == 2
    names = {r["id"]: r["layout"]["name"] for r in store.list("v1", "car", "hu7")}
    assert names == {"user.a": "A", "user.b": "B", "user.c": "C"}
    assert store.undo_reset("v1", "car", "hu7") == 0


def test_the_snapshot_lasts_seven_days(store, clock):
    store.put("v1", "car", "hu7", user_mode())
    store.reset("v1", "car", "hu7")
    clock.t += SNAPSHOT_TTL_S - 1
    assert store.snapshot("v1", "car", "hu7") is not None
    clock.t += 2
    assert store.snapshot("v1", "car", "hu7") is None
    assert store.undo_reset("v1", "car", "hu7") == 0
    assert store.list("v1", "car", "hu7") == []
    store.put("v1", "car", "hu7", user_mode())
    store.reset("v1", "car", "hu7")
    clock.t += SNAPSHOT_TTL_S + 1
    assert store.prune() == 1


def test_held_changes_apply_in_order(store):
    doc = user_mode("user.a", "A")
    store.hold("v1", "car", "hu7", "put", "drive_mode", "user.a", doc)
    store.hold("v1", "car", "hu7", "put", "drive_mode", "user.b", user_mode("user.b", "B"))
    store.hold("v1", "car", "hu7", "delete", "drive_mode", "user.b")
    assert [h["op"] for h in store.held("v1", "car", "hu7")] == ["put", "put", "delete"]
    assert store.list("v1", "car", "hu7") == []  # nothing changes until Parked
    assert store.apply_held() == 3
    assert [r["id"] for r in store.list("v1", "car", "hu7")] == ["user.a"]
    assert store.held("v1", "car", "hu7") == []


def test_a_held_write_that_no_longer_validates_is_dropped(store):
    bad = user_mode()
    bad.pop("base")
    store.hold("v1", "car", "hu7", "put", "drive_mode", "user.my-dash", bad)
    assert store.apply_held() == 0 and store.held("v1", "car", "hu7") == []
    with pytest.raises(ValueError):
        store.hold("v1", "car", "hu7", "rename")


def test_selection_per_display_profile_vehicle_and_class(store):
    assert store.selection("v1", "car", "headunit", "hu7") is None
    s = store.set_selection("v1", "car", "headunit", "hu7",
                            check_selection({"mode": "ostler.map", "faces": {"ostler.map": 0}}))
    assert s["mode"] == "ostler.map" and s["updated_utc"].endswith("Z")
    assert store.selection("v1", "car", "headunit", "hu9") is None
    assert store.selection("v1", "car", "kitchen", "hu7") is None
    assert store.selection("v1", "alice", "headunit", "hu7") is None
    assert store.selection("v2", "car", "headunit", "hu7") is None


@pytest.mark.parametrize("body", [
    None, [], {}, {"mode": "Not An Id"}, {"mode": "ostler.map", "faces": {"ostler.map": 3}},
    {"mode": "ostler.map", "faces": {"ostler.map": True}},
    {"mode": "ostler.map", "rotation": ["a", "b", "c", "d", "e"]},
    {"mode": "ostler.map", "rotation": ["a", "a"]},
])
def test_selection_bodies_are_checked(body):
    with pytest.raises(ValueError):
        check_selection(body)


def test_driver_facing_classes_fail_closed():
    for cls in ("hu5", "hu7", "hu9", "huwide", "phone", None, "", "kitchen"):
        assert driver_facing(cls), cls
    for cls in ("tablet", "desktop"):
        assert not driver_facing(cls), cls


def test_bad_keys_are_refused(store):
    with pytest.raises(ValueError):
        store.put("v1", "Car!", "hu7", user_mode())
    with pytest.raises(ValueError):
        store.put("v1", "car", "hu11", user_mode())
    with pytest.raises(ValueError):
        store.reset("v1", "car", "hu7", "dashboard")
