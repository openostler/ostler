# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The server side of K-line detection (spec K-line profiles §2, §6, §7): the Parked gate
for probes (``detect_protocol``, ``module_scan``), no probe on connect, re-init of a known
profile in every state, the profile remembered per vid, and the module_scan tool's gate.
Fakes only (FakeKLineEcu, FakeClock, the fake pack)."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from openostler.kline.memory import MEMORY_FILE, ProfileMemory
from openostler.kline.profiles import BUILTIN
from openostler.web.kline_cmds import PARKED_ONLY
from openostler.web.kline_source import KLineLinkSource
from tests.fakes import (
    FakeClock,
    FakeIso9141Ecu,
    FakeKLineEcu,
    kwp_fast_reply,
)

pytestmark = pytest.mark.fake_pack

VID = "testcar1"


@pytest.fixture(autouse=True)
def _vid(monkeypatch):
    monkeypatch.setenv("OSTLER_VEHICLE_ID", VID)


def _source(ecu, profile=None, origin="pack", clock=None):
    clock = clock or FakeClock()
    src = KLineLinkSource("auto", name="alpha", profile=profile, origin=origin,
                          transport_factory=lambda port, prof: ecu,
                          clock=clock, sleep=clock.sleep, wall=lambda: 1_790_000_000.0)
    return src, clock


def _server(tmp_path, src, **kw):
    from openostler.web.server import DiagServer

    kw.setdefault("geocoder", None)
    return DiagServer({"alpha": src}, host="127.0.0.1", port=0, csv_dir=str(tmp_path),
                      record_sessions=False, **kw)


def _moving_gps(kmh=50.0):
    return SimpleNamespace(latest=lambda: SimpleNamespace(speed_kmh=kmh, fix=True,
                                                          snapshot=lambda: {}),
                           src="test", start=lambda: None, stop=lambda: None)


def _cmd(srv, action, **params):
    """Run a queued command the way the poll thread does."""
    why, code = srv._refusal(action, params)
    if why:
        return {"ok": False, "error": why, "code": code}
    holder = {"result": None, "event": SimpleNamespace(set=lambda: None)}
    srv._commands.put(({"action": action, "params": params}, holder))
    srv._drain_commands()
    return holder["result"]


# ---- the Parked gate ------------------------------------------------------------ #
def test_detect_refused_without_the_server_flag(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    srv = _server(tmp_path, _source(ecu)[0])
    res = _cmd(srv, "detect_protocol", confirm_parked=True)
    assert res["ok"] is False and PARKED_ONLY in res["error"] and "--kline-detect" in res["error"]
    assert ecu.sent == [] and ecu.inits == []


def test_detect_refused_without_confirm_parked(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    srv = _server(tmp_path, _source(ecu)[0], kline_detect=True)
    for params in ({}, {"confirm_parked": False}, {"confirm_parked": "yes"}):
        res = _cmd(srv, "detect_protocol", **params)
        assert res["ok"] is False and "confirm" in res["error"]
    assert ecu.sent == []


def test_detect_refused_with_gps_speed(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    srv = _server(tmp_path, _source(ecu)[0], kline_detect=True, gps=_moving_gps(50.0))
    res = _cmd(srv, "detect_protocol", confirm_parked=True)
    assert res["ok"] is False and "GPS speed 50 km/h" in res["error"]
    assert ecu.sent == []


def test_detect_refused_with_a_speed_signal(tmp_path):
    srv = _server(tmp_path, _source(FakeKLineEcu())[0], kline_detect=True)
    srv.latest = {**srv.latest, "signals": {"speed": {"v": 12.0, "u": "km/h"}}}
    why = srv.refusal("detect_protocol", {"confirm_parked": True})
    assert why and "speed" in why


def test_slow_gps_is_not_motion(tmp_path):
    srv = _server(tmp_path, _source(FakeKLineEcu())[0], kline_detect=True,
                  gps=_moving_gps(1.0))
    assert srv.refusal("detect_protocol", {"confirm_parked": True}) is None


def test_detect_allowed_when_parked_and_remembered(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0xE9, 0x8F))
    src, _ = _source(ecu)
    srv = _server(tmp_path, src, kline_detect=True)
    assert src.needs_detect
    res = _cmd(srv, "detect_protocol", confirm_parked=True)
    assert res["ok"] is True and res["outcome"] == "ok"
    assert res["link"]["origin"] == "detected" and res["link"]["key_bytes"] == "E9 8F"
    snap = srv.poll_once()
    assert snap["status"] == "connected" and snap["link"]["profile"] == "kwp2000_fast"
    stored = json.loads((tmp_path / MEMORY_FILE).read_text(encoding="utf-8"))
    assert list(stored) == [VID]                               # keyed by the vid
    assert set(stored[VID]) == {"profile", "key_bytes", "address", "detected_utc"}
    assert stored[VID]["profile"] == "kwp2000_fast" and stored[VID]["key_bytes"] == "E9 8F"
    assert "vin" not in json.dumps(stored).lower()


def test_detect_on_a_source_with_a_known_profile_is_refused(tmp_path):
    from tests.fake_pack import FAKE_PACK

    srv = _server(tmp_path, FAKE_PACK.sources("auto")["alpha"], kline_detect=True)
    res = _cmd(srv, "detect_protocol", confirm_parked=True)
    assert res["ok"] is False and "known K-line profile" in res["error"]


# ---- no probe on connect; re-init of a known profile -------------------------------- #
def test_no_probe_on_connect(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(), slow_init_reply=b"\x55\x08\x08\xf7\xcc")
    src, _ = _source(ecu)
    srv = _server(tmp_path, src, kline_detect=True)
    for _ in range(5):
        snap = srv.poll_once()
    assert snap["status"] == "needs-detect" and snap["conn"] == "disconnected"
    assert snap["link"] is None
    assert ecu.sent == [] and ecu.inits == []


def test_reinit_of_a_known_profile_is_not_refused_while_moving(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    src, _ = _source(ecu, profile=BUILTIN["kwp2000_fast"], origin="pack")
    srv = _server(tmp_path, src, gps=_moving_gps(80.0))
    snap = srv.poll_once()
    assert snap["status"] == "connected" and snap["link"]["origin"] == "pack"
    assert ecu.inits == ["fast"]


def test_backoff_doubles_and_caps(tmp_path):
    ecu = FakeKLineEcu()                                   # silent
    src, clock = _source(ecu, profile=BUILTIN["kwp2000_fast"], origin="pack")
    delays = []
    for _ in range(8):
        src.poll()
        delays.append(round(src._next_try - clock.now(), 3))
        clock.advance(delays[-1])
    assert delays == [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0]
    assert set(ecu.inits) == {"fast"}                      # never the other init method


def test_reinit_uses_only_the_profiles_own_init(tmp_path):
    ecu = FakeIso9141Ecu()
    src, clock = _source(ecu, profile=BUILTIN["kwp2000_fast"], origin="pack")
    for _ in range(3):
        src.poll()
        clock.advance(31.0)
    assert ecu.inits == ["fast"] * 3


# ---- remembered per vid --------------------------------------------------------------- #
def _remember(tmp_path, profile="kwp2000_fast", kb=b"\xe9\x8f"):
    ProfileMemory(str(tmp_path)).put(VID, BUILTIN[profile], kb, when=1_790_000_000.0)


def test_restart_while_moving_reinits_from_the_remembered_profile(tmp_path):
    _remember(tmp_path)
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0xE9, 0x8F),
                       slow_init_reply=b"\x55\x08\x08\xf7\xcc")
    src, _ = _source(ecu)
    srv = _server(tmp_path, src, gps=_moving_gps(90.0))   # no --kline-detect either
    assert src.origin == "remembered"
    snap = srv.poll_once()
    assert snap["status"] == "connected" and snap["link"]["origin"] == "remembered"
    assert snap["link"]["key_bytes"] == "E9 8F"
    assert ecu.inits == ["fast"]                          # its own init, nothing else
    assert ecu.sent[0] == bytes.fromhex("C133F18166")


def test_three_failed_reinits_drop_to_needs_detect_without_probing(tmp_path):
    _remember(tmp_path)
    ecu = FakeKLineEcu(slow_init_reply=b"\x55\x08\x08\xf7\xcc")   # fast init silent
    src, clock = _source(ecu)
    srv = _server(tmp_path, src)
    statuses = []
    for _ in range(6):
        statuses.append(srv.poll_once()["status"])
        clock.advance(31.0)
    assert statuses[:2] == ["error", "error"] and statuses[2:] == ["needs-detect"] * 4
    assert ecu.inits == ["fast"] * 3                      # never a 5-baud probe
    assert src.needs_detect


def test_different_key_bytes_end_the_session_and_count_as_a_failure(tmp_path):
    _remember(tmp_path, kb=b"\xe9\x8f")
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0x57, 0x8F))     # another car
    src, clock = _source(ecu)
    srv = _server(tmp_path, src)
    snap = srv.poll_once()
    assert snap["status"] == "error" and "differ" in snap["error"]
    assert bytes.fromhex("C133F18267") in ecu.sent        # ended at once (82, functional)
    assert src._failures == 1 and not src.needs_detect
    for _ in range(2):
        clock.advance(31.0)
        srv.poll_once()
    assert src.needs_detect


def test_detect_replaces_the_remembered_entry(tmp_path):
    _remember(tmp_path, "kwp2000_fast", b"\xe9\x8f")
    ecu = FakeIso9141Ecu()
    src, _ = _source(ecu)
    srv = _server(tmp_path, src, kline_detect=True)
    src._profile = None                                    # e.g. after three failures
    res = _cmd(srv, "detect_protocol", confirm_parked=True)
    assert res["ok"] and res["link"]["protocol"] == "iso9141_2"
    assert ProfileMemory(str(tmp_path)).get(VID)["profile"] == "iso9141_2"
    assert ProfileMemory(str(tmp_path)).forget(VID) is True


def test_override_flag_sets_the_profile(tmp_path):
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    src, _ = _source(ecu)
    srv = _server(tmp_path, src, kline_profile="kwp2000_fast")
    assert src.origin == "override"
    assert srv.poll_once()["link"]["origin"] == "override"
    with pytest.raises(ValueError, match="unknown profile"):
        _server(tmp_path, _source(ecu)[0], kline_profile="kw1281")


def test_iso9141_link_keepalive_from_tick(tmp_path):
    ecu = FakeIso9141Ecu()
    src, clock = _source(ecu, profile=BUILTIN["iso9141_2"], origin="pack")
    assert src.poll()["status"] == "connected"
    n = len(ecu.sent)
    clock.advance(2.5)
    src.tick()
    assert ecu.sent[n:] == [bytes.fromhex("686AF10100C4")]
    src.disconnect()
    assert ecu.sent[-1] == bytes.fromhex("686AF10100C4")  # ISO 9141: no release frame


# ---- module-scan sweeps are probing ------------------------------------------------- #
def test_module_scan_refused_without_the_gate(tmp_path):
    calls = []
    srv = _server(tmp_path, _source(FakeKLineEcu())[0],
                  module_scan=lambda port, fast, slow: calls.append((fast, slow)) or [])
    res = _cmd(srv, "module_scan", confirm_parked=True)
    assert res["ok"] is False and PARKED_ONLY in res["error"] and calls == []


def test_module_scan_allowed_with_the_gate(tmp_path):
    calls = []
    rows = [{"address": "0x10", "init": "fast", "module": "alpha", "status": "silent"}]
    srv = _server(tmp_path, _source(FakeKLineEcu())[0], kline_detect=True,
                  module_scan=lambda port, fast, slow: calls.append((fast, slow)) or rows)
    res = _cmd(srv, "module_scan", confirm_parked=True, fast=["10"], slow=[0x30])
    assert res == {"ok": True, "scan": rows} and calls == [([0x10], [0x30])]
    moving = _server(tmp_path, _source(FakeKLineEcu())[0], kline_detect=True,
                     gps=_moving_gps(20.0), module_scan=lambda *a: calls.append(a) or [])
    assert _cmd(moving, "module_scan", confirm_parked=True)["ok"] is False
    assert len(calls) == 1


def _tool():
    path = Path(__file__).resolve().parents[1] / "tools" / "module_scan.py"
    spec = importlib.util.spec_from_file_location("module_scan_tool", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_module_scan_tool_refuses_without_confirm_parked(monkeypatch, capsys):
    tool = _tool()
    opened = []
    monkeypatch.setattr(tool, "SerialTransport", lambda *a, **k: opened.append(a))
    monkeypatch.setattr(tool, "EspTransport", lambda *a, **k: opened.append(a))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False, raising=False)
    assert tool.main(["/dev/null-port", "--esp"]) == 2
    assert opened == [] and "Parked" in capsys.readouterr().err


def test_module_scan_tool_confirmation():
    tool = _tool()
    assert tool.confirm_parked(True, interactive=False) is True
    assert tool.confirm_parked(False, interactive=False) is False
    assert tool.confirm_parked(False, ask=lambda _q: "yes", interactive=True) is True
    assert tool.confirm_parked(False, ask=lambda _q: "", interactive=True) is False


def test_vid_comes_from_the_state_dir_not_the_car(tmp_path, monkeypatch):
    monkeypatch.delenv("OSTLER_VEHICLE_ID")
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    src, _ = _source(ecu)
    _server(tmp_path, src, kline_detect=True)
    vid = json.loads((tmp_path / "vehicle.json").read_text(encoding="utf-8"))["vid"]
    assert src._vid == vid and os.path.exists(tmp_path / "vehicle.json")


def test_module_switch_never_shows_the_previous_link(tmp_path):
    from openostler.web.server import DiagServer
    from tests.fake_pack import FAKE_PACK

    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply())
    src, _ = _source(ecu, profile=BUILTIN["kwp2000_fast"])
    srv = DiagServer({"alpha": src, "beta": FAKE_PACK.sources("auto")["beta"]},
                     host="127.0.0.1", port=0, csv_dir=str(tmp_path), record_sessions=False,
                     geocoder=None)
    assert srv.poll_once()["link"]["profile"] == "kwp2000_fast"
    srv._select("beta")
    assert srv.latest["link"] is None
    assert bytes.fromhex("C133F18267") in ecu.sent         # the link was released (82)
