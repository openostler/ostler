# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The server's connection state machine (snapshot `conn`), disconnect/connect/set_port,
the latched-test banner (`active_test`) and the other snapshot additions
(specs/2026-10-05-ui-overhaul-design.md, "Snapshot additions" and "Connection UX")."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")


import threading


from openostler import ports
from openostler.web.server import CONN_STATES, DiagServer
from d2diag.sources import Td5DataSource
from openostler.web.sources import DataSource
from tests.fake_sources import FakeTd5Source, FakeSlabsSource


class _Scripted(DataSource):
    """A live-like source whose polls follow a script: "ok" → connected, "fail" → error.
    The last entry repeats. Records disconnect()/set_port() calls."""

    name = "td5"
    store_module = "td5"

    def __init__(self, script, progress=False):
        self.script = list(script)
        self.progress = progress
        self.polls = 0
        self.calls: "list" = []

    def poll(self):
        step = self.script[min(self.polls, len(self.script) - 1)]
        self.polls += 1
        if self.progress and self.on_progress:
            self.on_progress("sending init (try 1/3)")
        if step == "ok":
            return {"status": "connected", "source": self.name, "faults": [],
                    "signals": {"battery": {"v": 13.8, "u": "V", "s": "ok", "c": "proven"}}}
        return {"status": "error", "source": self.name, "signals": {}, "faults": [],
                "error": "KWP2000Error: no answer"}

    def disconnect(self):
        self.calls.append("disconnect")

    def set_port(self, spec):
        self.calls.append(("set_port", spec))

    def command(self, action, params=None):
        self.calls.append(action)
        return {"ok": True, "message": action}


@pytest.fixture
def make_server(tmp_path):
    made = []

    def _make(source=None, **kw):
        kw.setdefault("csv_dir", str(tmp_path))
        srv = DiagServer(source, host="127.0.0.1", port=0, **kw)
        made.append(srv)
        return srv

    yield _make
    for srv in made:
        srv.server_close()


def _cmd(srv, action, **params):
    """Run one command through the poll-thread path (queue + drain), without a poller."""
    why = srv.refusal(action, params)
    if why:
        return {"ok": False, "error": why}
    holder = {"result": None, "event": threading.Event()}
    srv._commands.put(({"action": action, "params": params}, holder))
    srv._drain_commands()
    return holder["result"]


# ---- conn transitions ------------------------------------------------------ #
def test_lost_then_reconnecting_then_connected(make_server):
    srv = make_server(_Scripted(["ok", "fail", "fail", "fail", "ok"]))
    assert srv.latest["conn"] == "connecting"
    seen = [srv.poll_once()["conn"] for _ in range(5)]
    assert seen == ["connected", "lost", "reconnecting", "reconnecting", "connected"]
    assert set(seen) <= set(CONN_STATES)


def test_legacy_status_field_is_unchanged(make_server):
    srv = make_server(_Scripted(["ok", "fail"]))
    assert srv.poll_once()["status"] == "connected"
    snap = srv.poll_once()
    assert snap["status"] == "error" and snap["conn"] == "lost"


def test_never_connected_is_error_and_stays_error_while_retrying(make_server):
    srv = make_server(_Scripted(["fail", "fail", "ok"], progress=True))
    assert srv.poll_once()["conn"] == "error"
    srv._connect_progress("opening the cable")      # a retry's establishment phase
    assert srv.latest["conn"] == "error"            # no flicker back to "connecting"
    assert srv.poll_once()["conn"] == "error"
    assert srv.poll_once()["conn"] == "connected"


def test_establishing_after_a_loss_reads_reconnecting(make_server):
    srv = make_server(_Scripted(["ok", "fail"]))
    srv.poll_once()
    srv.poll_once()                                  # lost
    srv._connect_progress("sending init (try 1/3)")
    assert srv.latest["conn"] == "reconnecting"
    assert srv.latest["status"] == "connecting"      # legacy field as before


def test_aborted_establishment_keeps_conn(make_server):
    src = _Scripted(["ok"])
    srv = make_server(src)
    srv.poll_once()
    src.poll = lambda: {"status": "error", "source": "td5", "signals": {}, "faults": [],
                        "error": "ConnectAborted: aborted by a queued command"}
    assert srv.poll_once()["conn"] == "connected"


def test_module_switch_restarts_the_state_machine(make_server):
    a, b = _Scripted(["ok", "fail"]), _Scripted(["fail"])
    srv = make_server({"td5": a, "slabs": b}, active="td5")
    srv.poll_once()
    assert _cmd(srv, "select_module", module="slabs")["ok"]
    assert srv.latest["conn"] == "connecting"
    assert srv.poll_once()["conn"] == "error"        # slabs never answered: error, not lost


# ---- disconnect / connect / set_port -------------------------------------- #
def test_disconnect_releases_and_pauses_polling(make_server):
    src = _Scripted(["ok"])
    srv = make_server(src)
    srv.poll_once()
    r = _cmd(srv, "disconnect")
    assert r["ok"] and r["conn"] == "disconnected"
    assert src.calls == ["disconnect"]               # release() via the source
    polls = src.polls
    snap = srv.poll_once()
    assert src.polls == polls                        # the source is not touched while paused
    assert snap["conn"] == "disconnected" and snap["status"] == "disconnected"
    assert snap["signals"] == {}
    # module actions are refused while disconnected; server commands still run
    assert not _cmd(srv, "clear_faults")["ok"]
    assert "connect" in srv.refusal("clear_faults")
    assert _cmd(srv, "connect")["conn"] == "connecting"
    assert srv.poll_once()["conn"] == "connected"


def test_disconnect_over_the_poll_thread(make_server):
    srv = make_server(_Scripted(["ok"]), poll_interval=0.02, stream_interval=0.02)
    srv.start_polling()
    try:
        assert srv.enqueue_command({"action": "disconnect"}, timeout=2)["ok"]
        assert srv.latest["conn"] == "disconnected"
        assert srv.enqueue_command({"action": "connect"}, timeout=2)["ok"]
        for _ in range(100):
            if srv.latest["conn"] == "connected":
                break
            threading.Event().wait(0.02)
        assert srv.latest["conn"] == "connected"
    finally:
        srv.stop()


def test_set_port_repoints_every_live_source_and_reconnects(make_server):
    td5_live, slabs_live = Td5DataSource("auto"), _Scripted(["ok"])
    srv = make_server({"td5": td5_live, "slabs": slabs_live}, active="slabs")
    srv.poll_once()
    _cmd(srv, "disconnect")
    r = _cmd(srv, "set_port", port="/dev/ttyUSB7")
    assert r["ok"] and r["port"] == "/dev/ttyUSB7"
    assert td5_live._port == "/dev/ttyUSB7"
    assert ("set_port", "/dev/ttyUSB7") in slabs_live.calls
    assert srv.latest["port"]["spec"] == "/dev/ttyUSB7"
    assert srv.latest["port"]["resolved"] == "/dev/ttyUSB7"   # explicit path passes through
    assert srv.latest["conn"] == "connecting"                  # set_port also resumes polling
    assert srv.poll_once()["conn"] == "connected"
    assert _cmd(srv, "set_port", port="auto")["ok"]
    assert not _cmd(srv, "set_port", port="")["ok"]
    assert not _cmd(srv, "set_port", port="/dev/tty.usbserial-1")["ok"]   # macOS: cu.* only


# ---- snapshot additions ---------------------------------------------------- #
def test_snapshot_carries_ts_battery_port_and_active_test(make_server):
    srv = make_server(FakeTd5Source())
    snap = srv.poll_once()
    assert isinstance(snap["ts"], float) and snap["ts"] > 1e9
    assert 13.0 < snap["battery_v"] < 15.0                    # mock Td5 battery
    assert set(snap["port"]) == {"spec", "resolved", "candidates"}
    assert snap["port"]["spec"] == "auto" and isinstance(snap["port"]["candidates"], list)
    assert snap["active_test"] is None and snap["conn"] == "connected"


def test_battery_v_is_null_without_a_battery_signal(make_server):
    srv = make_server(FakeSlabsSource())
    assert srv.poll_once()["battery_v"] is None


# ---- active_test ----------------------------------------------------------- #
def _recording_slabs():
    src = FakeSlabsSource()
    sent = []
    orig = src.command

    def command(action, params=None):
        sent.append(action)
        return orig(action, params)

    src.command = command  # type: ignore[method-assign]
    return src, sent


def test_latched_test_sets_and_clears_the_banner(make_server):
    src, sent = _recording_slabs()
    srv = make_server(src)
    assert _cmd(srv, "pump_on")["ok"]
    test = srv.poll_once()["active_test"]
    assert test["action"] == "pump_on" and test["stop"] == "pump_off"
    assert test["label"] and test["since"] > 1e9
    assert _cmd(srv, "buzzer")["ok"]                          # a non-latched test leaves it
    assert srv.poll_once()["active_test"]["action"] == "pump_on"
    assert _cmd(srv, "pump_off")["ok"]
    assert srv.poll_once()["active_test"] is None


def test_module_switch_stops_a_latched_test_first(make_server):
    slabs, sent = _recording_slabs()
    srv = make_server({"slabs": slabs, "td5": FakeTd5Source()}, active="slabs")
    assert _cmd(srv, "bleed_power_on")["ok"]
    assert srv.latest["active_test"]["stop"] == "bleed_power_off"
    assert _cmd(srv, "select_module", module="td5")["ok"]
    assert sent[-1] == "bleed_power_off"                      # sent before the switch
    assert srv.latest["active_test"] is None


def test_disconnect_stops_a_latched_test(make_server):
    slabs, sent = _recording_slabs()
    srv = make_server(slabs)
    _cmd(srv, "pump_on")
    _cmd(srv, "disconnect")
    assert sent == ["pump_on", "pump_off"]
    assert srv.latest["active_test"] is None


# ---- ports ----------------------------------------------------------------- #
def test_list_serial_ports_orders_by_id_first_and_skips_mac_tty(monkeypatch):
    fake = {
        "/dev/serial/by-id/*": ["/dev/serial/by-id/usb-Prolific-port0",
                                "/dev/serial/by-id/usb-FTDI_FT232R-if00-port0"],
        "/dev/ttyUSB*": ["/dev/ttyUSB0"],
        "/dev/ttyACM*": ["/dev/ttyACM0"],
        "/dev/cu.usbserial-*": ["/dev/cu.usbserial-1"],
    }
    monkeypatch.setattr(ports.glob, "glob", lambda pat: list(fake.get(pat, [])))
    got = ports.list_serial_ports()
    assert got[0] == "/dev/serial/by-id/usb-FTDI_FT232R-if00-port0"   # known KKL chip first
    assert {"/dev/ttyUSB0", "/dev/ttyACM0", "/dev/cu.usbserial-1"} <= set(got)
    assert len(got) == len(set(got))
    assert not any(p.startswith("/dev/tty.") for p in got)


def test_list_serial_ports_empty_without_a_cable(monkeypatch):
    monkeypatch.setattr(ports.glob, "glob", lambda pat: [])
    import sys
    monkeypatch.setitem(sys.modules, "serial.tools", None)    # no pyserial enumeration
    assert ports.list_serial_ports() == []
