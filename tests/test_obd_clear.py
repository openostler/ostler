# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Mode 04 made safe (spec §5, ADR-0033 §5; fixtures F16–F16d) and the Mode 08 / Mode 04
guards (F17)."""
from __future__ import annotations

import ast
import pathlib

import pytest

from openostler.obd import J1979, Pacer
from openostler.obd import clear as clr
from openostler.obd.link import ForbiddenService, PacedLink
from openostler.testing import FakeObdLink
from tests.obd_fakes import can_two_ecu, kline_petrol, make_vin, table

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "openostler"


def _ctx(**kw) -> clr.ClearContext:
    base = dict(user="alice", role="driver", device="head-unit", link="head_unit",
                driving_state="parked")
    base.update(kw)
    return clr.ClearContext(**base)


class _Car:
    """A J1979 on the two-ECU CAN fake, a gate and recording sinks."""

    def __init__(self, link=None, *, allow_remote=False, sink_ok=True, read_only=()):
        self.t = 100.0
        self.link = link or can_two_ecu()
        self.j = J1979(self.link, table(), pacer=Pacer(clock=self.clock, sleep=self.sleep),
                       clock=self.clock)
        self.j.supported()
        self.audit: "list[dict]" = []
        self.snaps: "list[dict]" = []
        self.sent_at_snapshot: "list[bytes]" = []
        self.gate = clr.ClearGate(clock=self.clock, audit=self.audit.append,
                                  allow_remote=allow_remote)
        self.sink_ok = sink_ok
        self.read_only = read_only

    def clock(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += s

    def sink(self, snap: dict):
        self.sent_at_snapshot = list(self.link.payloads())
        if self.sink_ok is None:
            return None
        if not self.sink_ok:
            raise OSError("disk full")
        self.snaps.append(snap)
        return "session-1#42"

    def plan(self, **kw) -> clr.ClearPlan:
        reads = [*self.j.read_dtcs("stored").reads, *self.j.read_dtcs("pending").reads]
        return clr.plan(reads, ecus=self.j.ecus(), read_only_ecus=self.read_only, **kw)

    def grant(self, **ctx) -> clr.ClearGrant:
        return self.gate.authorize(_ctx(**ctx), self.plan(), confirmed=True)

    def clear(self, grant, **kw):
        self.link.sent.clear()
        return self.j.clear_dtcs(grant, gate=self.gate, snapshot_sink=self.sink, **kw)

    def fours(self):
        return [(p, t) for p, t in self.link.sent if p[:1] == b"\x04"]


# ---------------------------------------------------------------------- F16 -- #

def test_f16_refused_without_a_grant():
    car = _Car()
    with pytest.raises(clr.ClearRefused) as ei:
        car.clear(None)
    assert ei.value.code == "no_grant"
    assert car.fours() == [] and car.snaps == []
    assert car.audit[-1]["outcome"] == "refused" and car.audit[-1]["reason"] == "no_grant"


def test_f16_one_functional_04_then_reread():
    car = _Car()
    res = car.clear(car.grant())
    assert car.fours() == [(b"\x04", None)]                   # one functional request
    sent = car.link.payloads()
    after = sent[sent.index(b"\x04") + 1:]
    for p in (b"\x03", b"\x07", b"\x0A", b"\x01\x01"):
        assert p in after                                     # re-read 03, 07, 0A, PID 01
    assert res.cleared == ("7E8", "7E9") and res.snapshot == "session-1#42"


def test_f16_grant_is_single_use_and_short_lived():
    car = _Car()
    g = car.grant()
    car.clear(g)
    with pytest.raises(clr.ClearRefused) as ei:
        car.clear(g)
    assert ei.value.code == "grant_used"
    g2 = car.grant()
    car.t += 61
    with pytest.raises(clr.ClearRefused) as ei:
        car.clear(g2)
    assert ei.value.code == "grant_expired" and car.fours() == []
    forged = clr.ClearGrant("x", g2.plan, g2.context, car.t, car.t + 60)
    with pytest.raises(clr.ClearRefused):
        car.clear(forged)


# --------------------------------------------------------------------- F16a -- #

def test_f16a_snapshot_written_before_04():
    car = _Car()
    car.clear(car.grant())
    assert b"\x04" not in car.sent_at_snapshot
    snap = car.snaps[0]
    assert snap["codes"]["stored"] == {"7E8": ["P0133", "P0300"], "7E9": ["P0700"]}
    assert snap["codes"]["pending"] == {"7E8": ["P0171"], "7E9": ["P0171"]}
    assert "permanent" in snap["codes"]
    assert snap["freeze_frames"]["7E8"]["trigger"] == "P0133"
    assert snap["readiness"]["7E8"]["mil"] is True
    assert not any(p[:2] == b"\x09\x02" for p in car.sent_at_snapshot)   # no identity
    assert make_vin() not in repr(snap)


@pytest.mark.parametrize("sink_ok", [False, None])
def test_f16a_failed_snapshot_blocks_the_clear(sink_ok):
    car = _Car(sink_ok=sink_ok)
    with pytest.raises(clr.ClearRefused) as ei:
        car.clear(car.grant())
    assert ei.value.code == "snapshot_failed" and car.fours() == []
    assert car.audit[-1]["outcome"] == "blocked"


def test_recorder_sinks():
    class Rec:
        session_id = "S1"

        def __init__(self, ok):
            self.ok, self.events = ok, []

        def event(self, etype, **f):
            self.events.append((etype, f))
            return {"t": 7, "type": etype} if self.ok else None

    r = Rec(True)
    assert clr.recorder_snapshot_sink(r)({"codes": {}}) == "S1#7"
    clr.recorder_audit_sink(r)({"type": "obd_clear", "t": 1, "outcome": "sent"})
    assert r.events[-1] == ("obd_clear_audit", {"outcome": "sent"})
    with pytest.raises(Exception):
        clr.recorder_snapshot_sink(Rec(False))({})


# --------------------------------------------------------------------- F16b -- #

@pytest.mark.parametrize("state", ["parked", "idling"])
def test_f16b_parked_and_idling_granted(state):
    car = _Car()
    res = car.clear(car.grant(driving_state=state), driving_state=state)
    assert res.cleared


def test_f16b_moving_refused_at_gate_and_at_redemption():
    car = _Car()
    with pytest.raises(clr.ClearRefused) as ei:
        car.grant(driving_state="moving")
    assert ei.value.code == "moving"
    g = car.grant(driving_state="parked")
    with pytest.raises(clr.ClearRefused) as ei:
        car.clear(g, driving_state=lambda: "moving")          # the node re-check
    assert ei.value.code == "moving" and car.fours() == []
    assert car.audit[-1]["stage"] == "redeem"


def test_f16b_idling_nrc22_shown_per_ecu():
    car = _Car(can_two_ecu(e8={"04": "7F 04 22"}))
    res = car.clear(car.grant(driving_state="idling"), driving_state="idling",
                    names={"7E9": "The transmission ECU"})
    by = {o.ecu: o for o in res.outcomes}
    assert by["7E8"].status == "negative" and by["7E8"].nrc == 0x22
    assert by["7E8"].message.startswith("The engine ECU refused")
    assert "Switch the engine off" in by["7E8"].message
    assert by["7E9"].status == "cleared"
    assert car.audit[-1]["results"] == {"7E8": "nrc 0x22", "7E9": "cleared"}


def test_permanent_codes_are_explained():
    car = _Car(can_two_ecu(e8={"0A": "4A 01 01 33"}))
    res = car.clear(car.grant())
    assert clr.PERMANENT_NOTE in res.notes


# --------------------------------------------------------------------- F16c -- #

def test_f16c_safety_warning_on_the_single_confirmation():
    car = _Car(can_two_ecu(e9={"03": "43 01 40 35"}))     # C0035, a chassis (ABS) code
    p = car.plan()
    assert p.warning == clr.SAFETY_WARNING and "C0035" in p.safety
    assert p.confirmation.startswith("Clear 5 codes (ECU 7E8, ECU 7E9)?")
    assert "snapshot is saved to the logbook first" in p.confirmation
    plain = _Car().plan()
    assert plain.warning is None and plain.safety == ()
    tagged = clr.plan(_Car().j.read_dtcs("stored").reads, safety_ecus=["7E9"])
    assert tagged.warning is not None and tagged.safety == ("7E9",)


def test_f16c_srs_read_only_ecu_never_gets_04():
    car = _Car(can_two_ecu(e9={"03": "43 01 80 01"}), read_only=("7E9",))
    p = car.plan()
    assert p.ecus == ("7E8",) and p.read_only == ("7E9",)
    res = car.clear(car.grant())
    assert car.fours() == [(b"\x04", "7E8")]                # physical, never functional
    assert res.cleared == ("7E8",)
    # a read-only ECU with no codes (or not yet seen) still forces physical requests
    assert clr.plan([], ecus=["7E8"], read_only_ecus=["7EA"]).read_only == ("7EA",)


# --------------------------------------------------------------------- F16d -- #

def test_f16d_audit_entry_per_attempt():
    car = _Car()
    car.clear(car.grant(user="bob", device="phone-7", driving_state="idling"),
              driving_state="idling")
    a = car.audit[-1]
    assert a["type"] == "obd_clear" and a["outcome"] == "sent"
    assert (a["user"], a["device"], a["driving_state"]) == ("bob", "phone-7", "idling")
    assert a["ecus"] == ["7E8", "7E9"]
    assert a["codes"] == {"7E8": ["P0133", "P0300", "P0171"], "7E9": ["P0700", "P0171"]}
    assert a["results"] == {"7E8": "cleared", "7E9": "cleared"}
    assert a["snapshot"] == "session-1#42" and "after" in a


@pytest.mark.parametrize("ctx, code", [
    ({"link": "tailscale"}, "remote"), ({"role": "viewer"}, "role"),
    ({"user": None, "role": "kiosk"}, "not_signed_in"), ({"driving_state": "moving"}, "moving")])
def test_f16d_gate_refusals_are_audited(ctx, code):
    car = _Car()
    with pytest.raises(clr.ClearRefused) as ei:
        car.grant(**ctx)
    assert ei.value.code == code
    a = car.audit[-1]
    assert (a["outcome"], a["stage"], a["reason"]) == ("refused", "gate", code)
    assert a["ecus"] == ["7E8", "7E9"] and "user" in a and "device" in a


def test_f16d_remote_override_from_install_env_only(monkeypatch):
    monkeypatch.delenv(clr.REMOTE_OVERRIDE_ENV, raising=False)
    assert clr.ClearGate().remote_allowed is False
    monkeypatch.setenv(clr.REMOTE_OVERRIDE_ENV, "1")
    gate = clr.ClearGate()
    assert gate.remote_allowed is True
    car = _Car(allow_remote=True)
    assert car.clear(car.grant(link="cloud")).cleared
    with pytest.raises(AttributeError):
        car.gate.allow_remote = False                      # never settable afterwards
    off = _Car(allow_remote=False)
    with pytest.raises(AttributeError):
        off.gate.allow_remote = True


def test_categories_narrow_the_role():
    car = _Car()
    with pytest.raises(clr.ClearRefused):
        car.grant(categories=frozenset({"read"}))
    assert car.grant(role="viewer", categories=frozenset({"maintenance"}))


# ---------------------------------------------------------------------- F17 -- #

def _exercise(j: J1979) -> None:
    j.supported()
    j.read_pids(range(0x100))
    for k in ("stored", "pending", "permanent"):
        j.read_dtcs(k)
    for e in j.ecus():
        j.read_freeze_frame(e)
    j.read_readiness()
    j.read_readiness(0x41)
    j.diagnostics()
    j.read_monitor_tests()
    j.read_identity(lambda v: None)
    j.snapshot()


@pytest.mark.parametrize("make", [can_two_ecu, kline_petrol])
def test_f17_no_read_path_sends_mode_08_or_04(make):
    link = make()
    _exercise(J1979(link, table(), pacer=Pacer(sleep=lambda s: None)))
    assert link.sent
    assert not [p for p, _t in link.sent if p[0] in (0x08, 0x04)]


def test_f17_guards_refuse_mode_08_everywhere_and_04_outside_clear():
    j = J1979(can_two_ecu(), table(), pacer=Pacer(sleep=lambda s: None))
    for payload in (b"\x08\x00", b"\x08\x01\x00", b"\x04"):
        with pytest.raises(ForbiddenService):
            j._request(payload)
    link = FakeObdLink({"7E8": {"08 00": "48 00 00 00 00 00"}})
    with pytest.raises(ForbiddenService):
        link.request(b"\x08\x00")
    paced = PacedLink(can_two_ecu(), Pacer(sleep=lambda s: None))
    with pytest.raises(ForbiddenService):
        paced.request(b"\x04")
    with pytest.raises(ForbiddenService):
        paced.request(b"\x08\x00", allow_clear=True)


def _byte_literal_starts(node) -> "int | None":
    """The first byte of a bytes literal, ``bytes([...])`` or ``bytes.fromhex("..")``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, bytes) and node.value:
        return node.value[0]
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id == "bytes" and node.args:
            a = node.args[0]
            if isinstance(a, (ast.List, ast.Tuple)) and a.elts and \
                    isinstance(a.elts[0], ast.Constant) and isinstance(a.elts[0].value, int):
                return a.elts[0].value
        if isinstance(fn, ast.Attribute) and fn.attr == "fromhex" and node.args and \
                isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            h = node.args[0].value.replace(" ", "")
            return int(h[:2], 16) if len(h) >= 2 else None
    return None


def test_f17_no_platform_source_builds_an_08_or_a_stray_04_request():
    """Static guard: no platform file builds a request starting ``08``; a bare ``04``
    request is built only in ``obd/j1979.py`` (``clear_dtcs``)."""
    for path in sorted(_SRC.rglob("*.py")):
        rel = path.relative_to(_SRC).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            first = _byte_literal_starts(node)
            if first is None:
                continue
            if rel.startswith(("obd/", "kline/obd_link", "testing/")):
                assert first != 0x08, f"{rel}:{node.lineno} builds a Mode 08 request"
            if rel.startswith("obd/") and first == 0x04 and isinstance(node, ast.Constant):
                assert rel == "obd/j1979.py" and node.value == b"\x04", \
                    f"{rel}:{node.lineno} builds a Mode 04 request"
