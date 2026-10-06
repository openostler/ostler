# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The server and the logbook run on a second, fake vehicle pack (Phase 0 spec §6).

Everything here goes through ``tests/fake_pack.py::FAKE_PACK`` (modules ``alpha`` with the
legacy alias ``a``, and ``beta``): nothing names a Discovery 2 module, so a green run proves
the platform asks the active pack instead of hard-coding the car.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request

import pytest

from openostler.pack import use_pack
from tests.fake_pack import FAKE_PACK


@pytest.fixture
def fake_pack():
    with use_pack(FAKE_PACK) as pack:
        yield pack


def _get(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _post(base, action, **params):
    req = urllib.request.Request(
        base + "/command", data=json.dumps({"action": action, "params": params}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


@pytest.fixture
def served(fake_pack, tmp_path):
    from openostler.web.server import DiagServer

    srv = DiagServer(fake_pack.sources("auto"), host="127.0.0.1", port=0,
                     poll_interval=0.05, stream_interval=0.05, csv_dir=str(tmp_path),
                     menus=fake_pack.menus, geocoder=None)
    srv.start_polling()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.1)
    try:
        yield srv, f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        srv.stop()
        srv.server_close()


# ---- server ------------------------------------------------------------------ #

def test_pack_endpoint_is_the_active_manifest(served):
    srv, base = served
    code, body = _get(base, "/pack")
    assert code == 200 and body == json.loads(json.dumps(FAKE_PACK.manifest()))
    assert body["id"] == "fake" and body["default_module"] == "alpha"
    assert body["aliases"] == {"a": "alpha"}
    assert [m["id"] for m in body["modules"]] == ["alpha", "beta"]


def test_server_defaults_to_the_pack_default_module(served):
    srv, base = served
    assert srv._active == "alpha" and srv.store_module() == "alpha"
    assert list(srv._modules) == ["alpha", "beta"]


def test_fields_resolve_an_alias_and_merge_derived_fields(served):
    _, base = served
    code, by_alias = _get(base, "/fields?module=a")
    assert code == 200 and by_alias["module"] == "alpha"
    names = {f["name"] for f in by_alias["fields"]}
    assert {"alpha_speed", "alpha_temp", "alpha_rate"} <= names
    rate = next(f for f in by_alias["fields"] if f["name"] == "alpha_rate")
    assert rate["derived"] is True and rate["unit"] == "/s"
    assert _get(base, "/fields?module=alpha")[1] == by_alias
    assert _get(base, "/fields")[1] == by_alias           # no ?module= → the pack default
    code, faults = _get(base, "/faults?module=A")
    assert code == 200 and faults["module"] == "alpha"


def test_select_module_by_alias(served):
    srv, base = served
    code, body = _post(base, "select_module", module="beta")
    assert code == 200 and body["ok"] and srv._active == "beta"
    code, body = _post(base, "select_module", module="a")   # the alias selects alpha
    assert code == 200 and body["ok"] and body["module"] == "alpha"
    assert srv._active == "alpha"
    code, body = _post(base, "select_module", module="gamma")
    assert body["ok"] is False and "unknown module" in body["error"]


def test_command_gate_uses_the_pack_registry(served):
    srv, base = served
    code, body = _post(base, "zap")                       # registered, gated
    assert code >= 400 and body["ok"] is False and "gated" in body["error"]
    code, body = _post(base, "zap_now")                   # a pack command prefix, unregistered
    assert code >= 400 and "unknown action for alpha" in body["error"]
    for _ in range(50):                                   # wait for the first poll (connected)
        if srv.latest.get("status") == "connected":
            break
        time.sleep(0.05)
    code, body = _post(base, "ping")                      # verified/read → reaches the source
    assert code == 200 and body["ok"] and body["message"] == "pong"


def test_signal_upsert_is_limited_to_the_pack_writable_modules(fake_pack, tmp_path,
                                                               monkeypatch):
    from openostler import signals
    from openostler.web.server import _signal_upsert, _signals_list

    (tmp_path / "alpha.json").write_text(
        (fake_pack.signals_dir / "alpha.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(signals, "_DIR", tmp_path)
    rec = {"name": "alpha_new", "lid": "20", "offset": 0, "kind": "u8", "unit": "x"}
    assert _signal_upsert({"module": "beta", "record": rec})["ok"] is False
    out = _signal_upsert({"module": "A", "record": rec})   # alias → alpha (writable)
    assert out["ok"] and out["module"] == "alpha"
    assert "alpha_new" in {r["name"] for r in _signals_list("a")["signals"]}
    assert _signals_list("beta")["signals"] == []


# ---- logbook ---------------------------------------------------------------- #

def _record(root, module):
    from openostler.logbook.recorder import SessionRecorder

    clock = {"t": 1_790_000_000.0, "m": 50.0}
    rec = SessionRecorder(str(root), clock=lambda: clock["t"], mono=lambda: clock["m"],
                          source="live")
    for i in range(4):
        rec.feed({"conn": "connected", "status": "connected", "module": module,
                  "signals": {"alpha_speed": {"v": 10.0 + i, "u": "km/h"}}, "faults": []},
                 None)
        clock["t"] += 0.5
        clock["m"] += 0.5
    sid = rec.status()["session"]
    rec.close()
    return sid


def test_recorder_writes_canonical_ids(fake_pack, tmp_path):
    from openostler.logbook.store import SessionStore

    sid = _record(tmp_path / "s", "a")
    raw = json.loads((tmp_path / "s" / sid / "meta.json").read_text(encoding="utf-8"))
    assert raw["modules"] == ["alpha"]
    events = (tmp_path / "s" / sid / "events.jsonl").read_text(encoding="utf-8")
    assert '"module":"alpha"' in events and '"module":"a"' not in events
    store = SessionStore(str(tmp_path / "s"))            # the fake pack ships no demo
    assert store.demo_root is None
    assert store.data(sid, ["alpha_speed"])["text"]["module"] == ["alpha"] * 4


def test_legacy_alias_on_disk_is_normalised_on_read_only(fake_pack, tmp_path):
    from openostler.logbook.store import SessionStore

    sid = _record(tmp_path / "s", "alpha")
    d = tmp_path / "s" / sid
    for p in [d / "meta.json", d / "events.jsonl", *d.glob("data*.csv")]:
        p.write_text(p.read_text(encoding="utf-8").replace('"alpha"', '"a"')
                     .replace(",alpha,", ",a,"), encoding="utf-8")
    before = {p.name: p.read_bytes() for p in d.iterdir()}
    assert b'"a"' in before["meta.json"]

    store = SessionStore(str(tmp_path / "s"), index_path=str(tmp_path / "ix.sqlite"))
    assert store.meta(sid)["modules"] == ["alpha"]
    assert [e["module"] for e in store.events(sid) if "module" in e] == ["alpha"]
    assert set(store.data(sid, ["alpha_speed"])["text"]["module"]) == {"alpha"}
    ix = store.index
    ix.rebuild()
    for want in ("alpha", "a", "A"):
        rows = ix.page(module=want)["sessions"]
        assert [m["id"] for m in rows] == [sid], want
        assert rows[0]["modules"] == ["alpha"]
    assert ix.page(module="beta")["sessions"] == []
    assert {p.name: p.read_bytes() for p in d.iterdir() if p.name in before} == before
    ix.close()


def test_channel_groups_come_from_the_pack_store(fake_pack):
    from openostler.logbook import channels

    assert channels.group_for("alpha_speed") == channels._store_records()["alpha_speed"] \
        .get("group", "").lower()
    assert "alpha_speed" in channels._store_records()
    from openostler import signals

    assert os.path.samefile(signals._dir(), fake_pack.signals_dir)
