"""Simulated data sources — TEST SCAFFOLDING ONLY (ADR-0011: no demo mode in the product).

The former product ``MockDataSource`` & co. live here now. The unit tests import them, and
tests/e2e_server.py serves the UI with them (Playwright, UI dev without a car). Nothing
under src/ imports this module. Every simulated value is synthetic; nothing here is a
car reading.

* FakeTd5Source(gps=None) — a Td5 with moving values, one active + one logged fault.
* FakeSlabsSource(gps=None) — SLABS heights/wheel speeds + the baseline's two faults.
* FakeInfoSource(module, faults=None, signal_gen=None) — a "connected" info module
  (airbag/ACE/EAT/BCU) with a seeded fault list.
* fake_bcu_signals(tick) — scripted BCU body states (all candidate).
* fake_read_block(module, values, lids) — LID blocks laid out from the signal store.
* fake_fault_report(port) — the "read all fault codes" report (RDL 016 baseline).
* FakeGps — the synthetic GPS loop (d2diag.gps.reader.MockGps).
* fake_modules(gps=None) — {module: source} for a DiagServer, as the dashboard
  builds it for the car.
"""
from __future__ import annotations

import math
import random
from typing import Callable

from d2diag.signals import load_signals
from d2diag.web.sources import (  # private helpers of the real sources (thin, tests only)
    TD5_ACTIONS,
    _SLABS_ACTUATORS,
    DataSource,
    _parse_lids,
    _security_message,
    _sig,
    _slabs_faults_flat,
    _slabs_sig,
)


def _gps_speed(gps) -> "float | None":
    """Speed (km/h) of an optional GPS source's latest fix, for the fakes to follow.
    None when there is no source, no fix yet, or the source misbehaves (never fails a poll)."""
    if gps is None:
        return None
    try:
        fix = gps.latest()
    except Exception:  # noqa: BLE001
        return None
    v = getattr(fix, "speed_kmh", None) if fix is not None else None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return max(0.0, float(v))


class FakeTd5Source(DataSource):
    """Simulated car for UI dev: reasonable, moving values + one active fault."""

    name = "td5"
    store_module = "td5"
    simulated = True  # the server does not write connection-log lines for it

    _ACTIVE_FAULT = "inlet air temp. circuit (Current)"
    _LOGGED_FAULT = "air flow circuit (Logged Low)"

    def __init__(self, gps=None) -> None:
        self._t = 0.0
        self._coolant = 20.0  # cold start, warming up
        self._faults = [self._LOGGED_FAULT, self._ACTIVE_FAULT]
        self._cleared_ticks = 0  # >0 = just cleared, faults temporarily gone
        # Optional GPS source (gps.reader.MockGps …): when it has a speed, the mock
        # "drives" along with it so mock `speed` ≈ GPS speed in recorded sessions.
        self._gps = gps
        self._last_signals: "dict" = {}  # last poll, for the mock read_block

    def poll(self) -> "dict":
        self._t += 1
        gps_speed = _gps_speed(self._gps)
        if gps_speed is not None:
            # follow the GPS: a plausible rpm for the speed (≈ 4th/5th gear), boost on load
            speed = gps_speed
            rpm = 780 + speed * 24 + random.uniform(-30, 30) if speed > 1 else (
                800 + random.uniform(-40, 60))
            revving = speed > 1
        else:
            # idle with a little variation, and a "throttle blip" pulse now and then
            revving = (int(self._t) % 30) in (10, 11, 12, 13)
            base = 2200 if revving else 800
            rpm = base + random.uniform(-40, 60)
            speed = max(0.0, (rpm - 800) / 45) if revving else 0.0
        self._coolant = min(88.0, self._coolant + 0.15)  # creeps towards working temp
        manifold = 1.0 + (0.25 if revving else 0.0) + random.uniform(-0.01, 0.01)
        signals = {
            "rpm": rpm,
            "speed": speed,
            "battery": 14.1 + random.uniform(-0.15, 0.15),
            "coolant_temp": self._coolant,
            "air_temp": 120.0,  # locked → mirrors the IAT fault on the real car
            "fuel_temp": self._coolant - 6 + random.uniform(-1, 1),
            "manifold_press": manifold,
            "ambient_press_1": 1.01,
            # Fuel economy (L/100km) so the Drive tab preview shows L/mil; live values
            # come from the real fuel computer in Td5DataSource.
            "economy": 8.2 + random.uniform(-0.4, 0.4),
            "trip_economy": 7.9 + random.uniform(-0.1, 0.1),
            "lifetime_economy": 8.5 + random.uniform(-0.05, 0.05),
            "rpm_error": random.uniform(-8, 8),
            "balance_1": random.uniform(-4, 4),
            "balance_2": random.uniform(-4, 4),
            "balance_3": random.uniform(-4, 4),
            "balance_4": random.uniform(-4, 4),
            "balance_5": random.uniform(-4, 4),
        }
        # After clearing, the list is empty for a few polls, then the ACTIVE
        # fault returns (still faulty) — demonstrates "clear and see if it comes back".
        if self._cleared_ticks > 0:
            self._cleared_ticks -= 1
            if self._cleared_ticks == 0:
                self._faults = [self._ACTIVE_FAULT]
        self._last_signals = _sig(signals)
        return {
            "status": "connected",
            "source": self.name,
            "signals": self._last_signals,
            "faults": list(self._faults),
        }

    def command(self, action: str, params: "dict | None" = None) -> "dict":
        if action == "read_block":
            if not self._last_signals:
                self.poll()
            return _fake_read_block_cmd("td5", self._last_signals, params)
        if action == "clear_faults":
            self._faults = []
            self._cleared_ticks = 4  # empty for ~4 polls, then the active fault returns
            return {"ok": True, "message": "Fault codes cleared (simulated)"}
        if action in TD5_ACTIONS:
            return _fake_td5_action(action)
        return {"ok": False, "error": f"unknown command: {action}"}

    def menu_map(self) -> "list":
        from d2diag.td5.menu import TD5_MENU
        return TD5_MENU


def _fake_td5_action(action: str) -> "dict":
    """Demo replies for the Td5 module actions (never touches a bus)."""
    if action == "security_status":
        return {"ok": True, "message": _security_message(0x03) + " (simulated)",
                "raw": "c0 03", "status": 0x03}
    if action == "read_identity":
        # Synthetic values only: no real VIN exists here either.
        return {"ok": True, "message": "ECU identity (simulated)", "identity": {
            "part_no": "NNN000130", "vin_masked": "*************0000",
            "build_date": "2002-11-14", "software_no": "NNW500140",
            "id_9b": "01", "id_9c": "01",
            "candidate_fields": ["vin_masked", "build_date", "software_no"]}}
    if action.startswith("injector_"):
        return {"ok": True, "message": f"Injector {action[len('injector_'):]} pulse (simulated)"}
    return {"ok": True, "message": f"Output test: {action[len('output_'):]} (simulated)"}


class FakeInfoSource(DataSource):
    """A simulated info module (airbag/ACE/EAT/BCU): connected with a seeded fault list
    so the UI is browsable (Faults, clear-and-return). signal_gen (tick → signals) lets
    the vehicle-view pages animate; its values are all tagged candidate."""

    simulated = True

    def __init__(self, module: str, faults: "list[str] | None" = None,
                 signal_gen: "Callable[[int], dict] | None" = None) -> None:
        self.name = module
        self.store_module = module
        self._seed = list(faults or [])
        self._faults = list(self._seed)
        self._cleared = 0
        self._signal_gen = signal_gen
        self._tick = 0

    def poll(self) -> "dict":
        # After a clear, the list is empty for a few polls, then the seed returns
        # (mirrors "clear and see if it comes back", like the other fakes).
        if self._cleared > 0:
            self._cleared -= 1
            if self._cleared == 0:
                self._faults = list(self._seed)
        self._tick += 1
        signals = self._signal_gen(self._tick) if self._signal_gen else {}
        return {"status": "connected", "source": self.name, "signals": signals,
                "faults": list(self._faults)}

    def command(self, action: str, params: "dict | None" = None) -> "dict":
        if action == "clear_faults":
            self._faults = []
            self._cleared = 4
            return {"ok": True, "message": f"Fault codes cleared (simulated {self.name})"}
        return {"ok": False, "error": f"unknown command: {action}"}


def _flag(v: bool) -> "dict":
    """A boolean body state as a snapshot signal. Confidence is always 'candidate' — these
    are demo/mock states or NanoCom-known fields, never a proven decode."""
    return {"v": 1 if v else 0, "u": "", "s": None, "c": "candidate"}


def fake_bcu_signals(tick: int) -> "dict":
    """Demo-only BCU body states for the vehicle-view Body page (simulated).

    A gentle scripted scene: ignition on, dipped beams, indicators blinking, a door that opens
    now and then, wipers sweeping. Names match the Body page's zone→signal map in the UI's
    layout.ts. Every value is tagged 'candidate' so it is never read as a proven measurement.
    """
    blink = (tick // 2) % 2 == 0          # ~1 Hz indicator blink
    door_open = (tick % 40) in range(6, 14)  # driver door opens briefly, periodically
    wiping = (tick % 20) < 6
    sig = {
        # doors / openings
        "door_driver": _flag(door_open),
        "door_passenger": _flag(False),
        "bonnet": _flag(False),
        "tailgate": _flag(False),
        # lamps
        "side_lights": _flag(True),
        "dipped": _flag(True),
        "main_beam": _flag(False),
        "front_fog": _flag(False),
        "rear_fog": _flag(False),
        "indicator_left": _flag(blink),
        "indicator_right": _flag(False),
        "hazard": _flag(False),
        "brake_light": _flag((tick % 16) < 3),
        "reverse_light": _flag(False),
        # windows / wash-wipe / heated screen
        "window_front_left": _flag(False),
        "window_front_right": _flag(False),
        "wiper_front": _flag(wiping),
        "wiper_rear": _flag(False),
        "heated_screen": _flag(False),
        # supply (numeric)
        "battery": {"v": round(12.6 + 0.1 * math.sin(tick / 9), 2), "u": "V", "s": "ok", "c": "candidate"},
        "ignition_pos": {"v": 2, "u": "", "s": None, "c": "candidate"},
    }
    return sig


# Integer range per store field kind (for encoding a mock value back into raw bytes).
_KIND_RANGE = {"u8": (0, 0xFF), "u16": (0, 0xFFFF), "u16le": (0, 0xFFFF),
               "s16": (-0x8000, 0x7FFF), "s16le": (-0x8000, 0x7FFF)}


def _encode_field(buf: bytearray, sig, value: float) -> None:
    """Write ``value`` into ``buf`` the way ``Signal.decode`` reads it back."""
    if sig.kind == "bit":
        mask = 1 << (sig.bit or 0)
        if value:
            buf[sig.offset] |= mask
        else:
            buf[sig.offset] &= ~mask & 0xFF
        return
    lo, hi = _KIND_RANGE.get(sig.kind, (0, 0xFFFF))
    raw = int(round((float(value) - sig.bias) / (sig.scale or 1.0)))
    raw = max(lo, min(hi, raw)) & (0xFF if sig.kind == "u8" else 0xFFFF)
    if sig.kind == "u8":
        buf[sig.offset] = raw
    elif sig.kind.endswith("le"):
        buf[sig.offset], buf[sig.offset + 1] = raw & 0xFF, raw >> 8
    else:
        buf[sig.offset], buf[sig.offset + 1] = raw >> 8, raw & 0xFF


def fake_read_block(module: str, values: "dict[str, float]", lids: "list[int]") -> "dict[str, str]":
    """Deterministic mock LID blocks built from the signal store and the mock values.

    For every requested LID with store fields, a data block is laid out from the fields'
    offsets/kinds (the longest reply-length variant when a LID has several) and each field
    is encoded from ``values`` (the last mock poll; a field the mock does not simulate reads
    as raw 0). A LID the store does not know is skipped, as a real ECU would refuse it.
    Returns ``{lidhex: hex}`` like the live ``read_block``. Mock only: never a car value."""
    width = {"u8": 1, "bit": 1}
    by_lid: "dict[int, list]" = {}
    for sig in load_signals(module):
        by_lid.setdefault(sig.lid, []).append(sig)
    out: "dict[str, str]" = {}
    for lid in lids:
        sigs = by_lid.get(lid)
        if not sigs:
            continue
        lengths = [s.length for s in sigs if s.length is not None]
        length = max(lengths) if lengths else None
        use = [s for s in sigs if s.length is None or s.length == length]
        size = max([s.offset + width.get(s.kind, 2) for s in use] + [length or 0])
        buf = bytearray(size)
        for sig in use:
            v = values.get(sig.name)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            _encode_field(buf, sig, v)
        out[f"{lid:02x}"] = bytes(buf).hex()
    return out


def _fake_read_block_cmd(module: str, signals: "dict", params: "dict | None") -> "dict":
    try:
        lids = _parse_lids(params)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    values = {k: (s.get("v") if isinstance(s, dict) else s) for k, s in (signals or {}).items()}
    return {"ok": True, "raws": fake_read_block(module, values, lids), "simulated": True}


class FakeSlabsSource(DataSource):
    """Simulated SLABS for UI dev: moving heights + the baseline's two logged faults."""

    name = "slabs"
    store_module = "slabs"
    simulated = True

    def __init__(self, gps=None) -> None:
        self._t = 0.0
        self._gps = gps  # optional GPS source: wheel speeds follow its speed (see poll)
        self._faults = {
            "logged": [
                "right front wheel speed sensor — output too low",
                "shuttle valve switch — electrical failure",
            ],
            "current": [],
        }
        self._cleared = 0
        self._last_signals: "dict" = {}  # last poll, for the mock read_block

    def poll(self) -> "dict":
        self._t += 1
        hl = 143 + 2 * math.sin(self._t / 10)
        hr = 157 + 2 * math.cos(self._t / 12)
        vals = {
            "height_left": hl, "height_right": hr,
            "height_left_mm": hl * 1.4, "height_right_mm": hr * 1.4,
        }
        # Wheel speed raw (~124 at rest, scale unknown on the car). With a GPS the mock
        # adds the GPS km/h so the wheels visibly move with the drive — illustrative only.
        moving = _gps_speed(self._gps) or 0.0
        for w in ("fl", "fr", "rl", "rr"):  # wheel: speed + sensor voltage
            vals[f"wheel_speed_{w}"] = 124.0 + moving
            vals[f"abs_sensor_{w}"] = round(2.3 + random.uniform(-0.05, 0.05), 2)
        signals = _slabs_sig(vals)
        self._last_signals = signals
        if self._cleared > 0:
            self._cleared -= 1
            if self._cleared == 0:
                self._faults = {"logged": [], "current": []}
        return {"status": "connected", "source": self.name,
                "signals": signals, "faults": _slabs_faults_flat(self._faults)}

    def command(self, action: str, params: "dict | None" = None) -> "dict":
        if action == "read_block":
            if not self._last_signals:
                self.poll()
            return _fake_read_block_cmd("slabs", self._last_signals, params)
        if action == "clear_faults":
            self._faults = {"logged": [], "current": []}
            self._cleared = 4
            return {"ok": True, "message": "Fault codes cleared (simulated)"}
        if action in _SLABS_ACTUATORS:
            return {"ok": True, "message": f"{_SLABS_ACTUATORS[action]} (simulated)"}
        return {"ok": False, "error": f"unknown command: {action}"}

    def menu_map(self) -> "list":
        from d2diag.slabs.menu import SLABS_MENU
        return SLABS_MENU


def fake_fault_report(port: str = "auto", sleep=None) -> "list[dict]":
    """The "read all fault codes" report without a car (the RDL 016 baseline), in the shape
    of d2diag.faultscan.read_all."""
    from d2diag.faultscan import _row as row
    from d2diag.faultscan import unimplemented_rows

    rows = [
        row("TD5", []),
        row("SLABS", ["right front wheel speed sensor — output too low (Logged)",
                      "shuttle valve switch — electrical failure (Logged)"]),
        row("Airbag", ["004: airbag warning lamp — open circuit intermittent",
                       "022: open circuit intermittent"], note="experimental"),
    ]
    return rows + unimplemented_rows()


def FakeGps():  # noqa: N802 — reads like a class at the call site
    """The synthetic GPS loop (Rannoch Moor demo route), as --gps mock used to give."""
    from d2diag.gps.reader import MockGps

    return MockGps()


def fake_modules(gps=None) -> "dict[str, DataSource]":
    """{module: source} like the dashboard builds for the car, all simulated."""
    return {
        "motor": FakeTd5Source(gps=gps),
        "slabs": FakeSlabsSource(gps=gps),
        "airbag": FakeInfoSource("airbag", faults=[
            "004: airbag warning lamp — open circuit intermittent",
            "022: open circuit intermittent"]),
        "ace": FakeInfoSource("ace"),
        "autobox": FakeInfoSource("autobox"),
        "bcu": FakeInfoSource("bcu", signal_gen=fake_bcu_signals),
    }
