# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SQLite session index (spec 2026-10-06-logs-at-scale §3)."""

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")

import json
import os
import sqlite3
import time


from openostler.logbook import index as idxmod
from openostler.logbook.index import SessionIndex
from openostler.logbook.store import SessionStore
from d2diag.synth import DEMO_IDS

DAY_MS = 86_400_000
BASE_MS = 1_767_225_600_000  # 2026-01-01T00:00:00Z
MODULES = (["motor"], ["slabs"], ["motor", "slabs"], [])
PLACES = ("near Okehampton, Devon", "Highland, Scotland", "near Glencoe, Highland",
          "Cumbria, England")


def _iso(ms: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def _write(root, i: int, start_ms: int, **extra) -> str:
    sid = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(start_ms // 1000))
    if i >= 0:
        sid = f"{sid}-{i}" if extra.pop("suffix", False) else sid
    d = root / sid
    d.mkdir(parents=True, exist_ok=True)
    meta = {"id": sid, "start_utc": _iso(start_ms), "end_utc": _iso(start_ms + 600_000),
            "duration_s": 600, "rows": 10, "parts": [], "modules": MODULES[i % 4],
            "channels": [], "has_gps": True, "distance_km": round((i % 50) * 1.5, 2),
            "max_speed_kmh": 80.0, "bbox": None, "start_pos": None, "end_pos": None,
            "synthetic": False, "recording": False, "source": "live",
            "place_start": {"label": PLACES[i % 4], "source": "geonames"},
            "place_end": None, "place": {"label": PLACES[i % 4], "source": "geonames"}}
    meta.update(extra)
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return sid


@pytest.fixture(scope="module")
def big(tmp_path_factory):
    """2000 recorded sessions, ~4 h apart (some sharing a start time), plus the demos."""
    root = tmp_path_factory.mktemp("big") / "sessions"
    ids = []
    for i in range(2000):
        start = BASE_MS + (i // 2) * 4 * 3_600_000  # pairs share a start → id tiebreak
        ids.append(_write(root, i, start, suffix=(i % 2 == 1)))
    note_dir = root / ids[1234]
    (note_dir / "notes.jsonl").write_text(json.dumps(
        {"id": "aaaaaaaa", "t": 1000, "t_end": None, "text": "Clunk from the rear axle",
         "tags": [], "kind": "note", "source": "retro", "created": "2026-01-01T00:00:00Z",
         "edited": None, "capture": None}) + "\n", encoding="utf-8")
    meta = json.loads((root / ids[77] / "meta.json").read_text())
    meta.update(name="Glen Coe run", description="Hill climb with the trailer")
    (root / ids[77] / "meta.json").write_text(json.dumps(meta))
    store = SessionStore(str(root))
    db = str(root.parent / "index.sqlite")
    t0 = time.perf_counter()
    ix = SessionIndex(db, store)
    build_s = time.perf_counter() - t0
    return {"root": root, "store": store, "ix": ix, "ids": ids, "db": db, "build_s": build_s}


def _all(ix, **kw):
    out, before = [], None
    while True:
        p = ix.page(before=before, **kw)
        out += p["sessions"]
        if not p["next"]:
            return out
        before = p["next"]


def test_first_page_fast_and_ordered(big):
    ix = big["ix"]
    assert ix.count() == 2002
    t0 = time.perf_counter()
    p = ix.page()
    assert time.perf_counter() - t0 < 0.1
    assert len(p["sessions"]) == 50 and p["next"]
    keys = [(idxmod._iso_ms(m["start_utc"]), m["id"]) for m in p["sessions"]]
    assert keys == sorted(keys, reverse=True)
    start_ms, sid = p["next"].split(":", 1)
    assert (int(start_ms), sid) == keys[-1]


def test_paging_is_stable_and_complete(big):
    ix = big["ix"]
    got = _all(ix, limit=137)
    ids = [m["id"] for m in got]
    assert len(ids) == len(set(ids)) == 2002
    keys = [(idxmod._iso_ms(m["start_utc"]), m["id"]) for m in got]
    assert keys == sorted(keys, reverse=True)
    # inserting a newer session does not shift later pages (keyset paging)
    p1 = ix.page(limit=10)
    new = _write(big["root"], 0, BASE_MS + 5000 * DAY_MS)
    ix.sync(new)
    p2 = ix.page(limit=10, before=p1["next"])
    assert p2["sessions"][0]["id"] == _all(ix)[11]["id"]
    big["store"].delete(new)  # this store has no index attached: sync it by hand
    ix.sync(new)
    assert ix.count() == 2002


def test_limit_bounds_and_bad_values(big):
    ix = big["ix"]
    assert len(ix.page(limit=5000)["sessions"]) == 200
    assert len(ix.page(limit=0)["sessions"]) == 1
    for kw in ({"limit": "x"}, {"before": "nope"}, {"frm": "2026-13-45"}, {"min_km": "far"}):
        with pytest.raises(ValueError):
            ix.page(**kw)


def test_search_name_description_place_notes(big):
    ix, ids = big["ix"], big["ids"]
    assert [m["id"] for m in ix.page(q="glen coe")["sessions"]] == [ids[77]]
    assert [m["id"] for m in ix.page(q="trail")["sessions"]] == [ids[77]]  # prefix
    assert [m["id"] for m in ix.page(q="clunk axle")["sessions"]] == [ids[1234]]
    devon = _all(ix, q="Okehampton")
    assert len(devon) == 501 and all("Okehampton" in m["place"]["label"] for m in devon)
    assert ix.page(q="zzzz")["sessions"] == []
    assert ix.page(q='"; DROP TABLE sessions; --')["sessions"] == []
    assert ix.count() == 2002


def test_search_like_fallback(big, tmp_path, monkeypatch):
    monkeypatch.setattr(SessionIndex, "_fts_available", staticmethod(lambda: False))
    ix = SessionIndex(str(tmp_path / "like.sqlite"), big["store"])
    assert ix.fts is False
    assert [m["id"] for m in ix.page(q="hill trailer")["sessions"]] == [big["ids"][77]]
    assert [m["id"] for m in ix.page(q="clunk")["sessions"]] == [big["ids"][1234]]
    assert len(_all(ix, q="okehampton")) == 501  # + Demo log 2
    ix.close()


def test_filters(big):
    ix, ids = big["ix"], big["ids"]
    jan = _all(ix, frm="2026-01-01", to="2026-01-31")
    assert jan and all(m["start_utc"].startswith("2026-01") for m in jan)
    assert len(jan) == 31 * 6 * 2  # 6 start times a day, 2 sessions each
    one_day = _all(ix, frm="2026-01-05", to="2026-01-05")
    assert {m["start_utc"][:10] for m in one_day} == {"2026-01-05"}
    slabs = _all(ix, module="slabs")
    assert len(slabs) == 1000 + 2 and all("slabs" in m["modules"] for m in slabs)  # + both demo logs
    td5 = _all(ix, module="td5")  # legacy "motor" rows are stored canonical (td5)
    assert td5 and all("td5" in m["modules"] and "motor" not in m["modules"] for m in td5)
    assert [m["id"] for m in _all(ix, module="motor")] == [m["id"] for m in td5]  # alias
    noted = _all(ix, has_notes=True)
    assert {m["id"] for m in noted} == {ids[1234], *DEMO_IDS}
    assert all(m["note_count"] > 0 for m in noted)
    far = _all(ix, min_km=70)
    assert far and all(m["distance_km"] >= 70 for m in far)
    pub = _all(ix, public=True)
    assert [m["id"] for m in pub] == list(DEMO_IDS)
    both = _all(ix, q="okehampton", module="motor", min_km=1)
    assert both and all(m["distance_km"] >= 1 and "td5" in m["modules"] for m in both)


def test_before_accepts_dates_for_the_scrubber(big):
    ix = big["ix"]
    p = ix.page(before="2026-02-01", limit=3)
    assert all(m["start_utc"] < "2026-02-01" for m in p["sessions"])
    assert p["sessions"][0]["start_utc"].startswith("2026-01-31")
    assert ix.page(before=str(BASE_MS), limit=3)["sessions"] == []  # only older: none


def test_histogram_month_and_day(big):
    ix = big["ix"]
    h = ix.histogram()
    assert h["group"] == "month"
    keys = [b["key"] for b in h["buckets"]]
    assert keys == sorted(keys, reverse=True) and "2026-01" in keys
    assert sum(b["count"] for b in h["buckets"]) == 2002
    jan = next(b for b in h["buckets"] if b["key"] == "2026-01")
    assert jan["count"] == 372
    assert jan["km"] == round(sum(m["distance_km"] for m in _all(ix, frm="2026-01-01",
                                                                  to="2026-01-31")), 2)
    d = ix.histogram("day", year=2026)
    assert d["group"] == "day" and d["buckets"][-1] == {"key": "2026-01-01", "count": 12,
                                                        "km": d["buckets"][-1]["km"]}
    assert all(b["key"].startswith("2026-") for b in d["buckets"])
    pub = ix.histogram(public=True)
    assert pub["buckets"] == [{"key": "2026-10", "count": 2,
                               "km": round(sum(m["distance_km"] for m in _all(ix, public=True)),
                                           2)}]
    with pytest.raises(ValueError):
        ix.histogram("week")


def test_store_wiring_sync_update_notes_delete(tmp_path):
    root = tmp_path / "sessions"
    sid = _write(root, 0, BASE_MS)
    store = SessionStore(str(root), index_path=str(tmp_path / "ix.sqlite"))
    ix = store.index
    assert ix.count() == 3
    store.update_meta(sid, name="Moor run", description="Windy")
    assert [m["id"] for m in ix.page(q="moor run")["sessions"]] == [sid]
    assert ix.page(q="windy")["sessions"][0]["description"] == "Windy"
    n = store.add_note(sid, 1000, "brake squeal")
    assert [m["id"] for m in ix.page(q="squeal")["sessions"]] == [sid]
    assert ix.page(has_notes=True, q="windy")["sessions"][0]["note_count"] == 1
    store.edit_note(sid, n["id"], text="brake judder")
    assert ix.page(q="squeal")["sessions"] == []
    store.delete_note(sid, n["id"])
    assert ix.page(q="judder")["sessions"] == []
    store.set_place(sid, "start", "Postbridge, Devon")
    assert [m["id"] for m in ix.page(q="postbridge")["sessions"]] == [sid]
    store.delete(sid)
    assert ix.count() == 2


def test_recorder_on_change_keeps_index_current(tmp_path):
    from openostler.logbook.recorder import SessionRecorder
    store = SessionStore(str(tmp_path / "sessions"), index_path=str(tmp_path / "ix.sqlite"))
    t = {"t": 0.0}
    rec = SessionRecorder(str(tmp_path / "sessions"), clock=lambda: 1_791_277_200 + t["t"],
                          mono=lambda: t["t"], min_free_bytes=0, on_change=store.sync)
    rec.feed({"conn": "connected", "signals": {"rpm": {"v": 800}}}, None)
    sid = rec.status()["session"]
    assert store.index.page(limit=1)["sessions"][0]["recording"] is True
    t["t"] = 1.0
    rec.note("live clunk")
    assert [m["id"] for m in store.index.page(q="clunk")["sessions"]] == [sid]
    rec.close()
    assert store.index.page(limit=1)["sessions"][0]["recording"] is False


def test_rebuild_reconcile_and_schema_change(tmp_path):
    root = tmp_path / "sessions"
    a = _write(root, 0, BASE_MS)
    db = str(tmp_path / "ix.sqlite")
    store = SessionStore(str(root), demo_root=None)
    ix = SessionIndex(db, store)
    assert ix.count() == 1
    b = _write(root, 1, BASE_MS + DAY_MS)  # behind the store's back
    ix.close()
    ix = SessionIndex(db, store)  # reconcile on open
    assert ix.count() == 2
    import shutil
    shutil.rmtree(root / a)
    assert ix.reconcile() == 1 and [m["id"] for m in ix.page()["sessions"]] == [b]
    ix.close()
    con = sqlite3.connect(db)
    con.execute("PRAGMA user_version=999")
    con.execute("DELETE FROM sessions")
    con.commit()
    con.close()
    ix = SessionIndex(db, store)  # schema differs → rebuilt
    assert ix.count() == 1
    assert ix.rebuild() == 1
    jm = sqlite3.connect(db).execute("PRAGMA journal_mode").fetchone()[0]
    assert jm == "wal"
    ix.close()
    os.remove(db)
    ix = SessionIndex(db, store)  # missing → rebuilt
    assert ix.count() == 1
    ix.close()
    with open(db, "wb") as fh:  # corrupt → recreated
        fh.write(b"not a database" * 100)
    for suffix in ("-wal", "-shm"):
        if os.path.exists(db + suffix):
            os.remove(db + suffix)
    ix = SessionIndex(db, store)
    assert ix.count() == 1
    ix.close()


def test_index_fills_missing_place_names(tmp_path):
    root = tmp_path / "sessions"
    sid = _write(root, 0, BASE_MS, start_pos=[-3.966, 50.627], end_pos=[-3.966, 50.627])
    meta = json.loads((root / sid / "meta.json").read_text())
    for k in ("place_start", "place_end", "place"):
        meta.pop(k)
    (root / sid / "meta.json").write_text(json.dumps(meta))
    ix = SessionIndex(str(tmp_path / "ix.sqlite"), SessionStore(str(root), demo_root=None))
    m = ix.page()["sessions"][0]
    assert "Devon" in m["place"]["label"] and m["place"]["source"] == "geonames"
    assert "place_start" in json.loads((root / sid / "meta.json").read_text())
    assert [x["id"] for x in ix.page(q="devon")["sessions"]] == [sid]
    ix.close()
