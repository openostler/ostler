"""Command registry: every module action the dashboard can send, with its status and safety.

The single source of truth for **what an action is** (ADR-0008,
specs/2026-10-05-ui-overhaul-design.md):

* ``status``:
  * ``verified``: run against the car and confirmed;
  * ``experimental``: implemented but unproven on the car;
  * ``planned``: known from the NanoCom, not wired, never runnable.
* ``safety``:
  * ``read``: reads only;
  * ``actuator``: a short output test;
  * ``service``: a multi-step or latched procedure;
  * ``gated``: never sent by this project (security, coding, airbag, calibration writes).
* ``confirm``: the friction the UI applies. ``none``; ``preconditions`` (a checklist the
  user ticks); ``typed`` (the user types the item name).

The server refuses unknown, gated, planned and (without ``trust=experimental``)
experimental actions; the catalog (:mod:`d2diag.catalog`) derives each menu item's status
from the actions it links to. Data only: no I/O, no web imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field

STATUSES = ("verified", "experimental", "planned")
SAFETIES = ("read", "actuator", "service", "gated")
CONFIRMS = ("none", "preconditions", "typed")

# Preconditions shown before an actuator or service action (the UI ticks them off).
STATIONARY = ("Vehicle stationary, handbrake on", "Ignition on", "Nobody under or beside the car")
ENGINE_OFF = STATIONARY + ("Engine off",)
BRAKES = STATIONARY + ("Brake bleed in progress (fluid topped up, bleed nipples ready)",)


@dataclass(frozen=True)
class Command:
    action: str                 # the /command action string (module-scoped)
    module: str                 # store module: td5 | slabs | bcu | ace | autobox | airbag
    label: str
    status: str = "experimental"
    safety: str = "actuator"
    confirm: str = "preconditions"
    preconditions: "tuple[str, ...]" = field(default=STATIONARY)
    stop: "str | None" = None   # action that ends a latched test (shown on the banner)
    ref: str = ""               # the K-line request, for reference

    def as_dict(self) -> dict:
        d = {"action": self.action, "label": self.label, "status": self.status,
             "safety": self.safety, "confirm": self.confirm,
             "preconditions": list(self.preconditions), "ref": self.ref}
        if self.stop:
            d["stop"] = self.stop
        return d


def _td5_out(action: str, label: str, ref: str, **kw) -> Command:
    return Command(action, "td5", label, ref=ref, preconditions=ENGINE_OFF, **kw)


_ALL: "list[Command]" = [
    # ---- Td5: outputs (IOControl 30 xx), injector click (31 C2 0n) — experimental ----
    _td5_out("output_fuel_pump", "Fuel pump", "30 A1 FF"),
    _td5_out("output_mil_lamp", "MIL lamp", "30 A2 FF", confirm="none"),
    _td5_out("output_ac_clutch", "A/C clutch", "30 A3 FF"),
    _td5_out("output_ac_fan", "A/C fan", "30 A4 FF"),
    _td5_out("output_glow_plugs", "Glow plugs", "30 B3 FF"),
    _td5_out("output_rev_counter", "Rev counter", "30 B7 FF", confirm="none"),
    _td5_out("output_temp_gauge", "Temp gauge", "30 BA FF", confirm="none"),
    _td5_out("output_egr_throttle", "EGR throttle", "30 BD FF 00 FA 13 88"),
    _td5_out("output_wastegate", "Wastegate modulator", "30 BE FF 00 0A 13 88"),
    *[_td5_out(f"injector_{n}", f"Injector {n} click", f"31 C2 0{n}") for n in range(1, 6)],
    # ---- Td5: utilities ----
    Command("security_status", "td5", "Get security status", safety="read", confirm="preconditions",
            preconditions=("Ignition on",), ref="31 C0 → 33 C0 (read-only)"),
    Command("read_identity", "td5", "Read ECU identity", safety="read", confirm="none",
            preconditions=(), ref="1A 87 / 1A 9A / 1A 9B / 1A 9C (VIN never logged)"),
    Command("learn_security_code", "td5", "Learn security code", status="planned", safety="gated",
            confirm="typed", ref="never sent (immobiliser state change)"),
    # ---- SLABS: outputs (simple tests) — verified on RDL 016 ----
    Command("buzzer", "slabs", "Buzzer test", status="verified", confirm="none", ref="31 31 0A"),
    Command("compressor", "slabs", "Compressor test", status="verified", ref="31 30 28"),
    Command("exhaust", "slabs", "Exhaust valve test", status="verified", ref="31 2F 28"),
    Command("pump_on", "slabs", "ABS pump on", status="verified", stop="pump_off", ref="31 25 08 FA"),
    Command("pump_off", "slabs", "ABS pump off", status="verified", confirm="none", preconditions=(),
            ref="31 25 02 FA"),
    # ---- SLABS: utilities — bleed and height (service) ----
    *[Command(f"wheel_{c}", "slabs", f"Wheel test {c.upper()}", status="verified", safety="service",
              ref=r) for c, r in (("fl", "31 22 11 0C"), ("fr", "31 22 10 03"),
                                  ("rl", "31 22 13 C0"), ("rr", "31 22 12 30"))],
    Command("bleed_power_on", "slabs", "Power bleed — start", status="verified", safety="service",
            preconditions=BRAKES, stop="bleed_power_off", ref="31 22 04 00 49 C4"),
    Command("bleed_power_off", "slabs", "Power bleed — stop", status="verified", safety="service",
            confirm="none", preconditions=(), ref="31 22 04 00 40 00"),
    Command("bleed_module", "slabs", "Modulator bleed (4 steps)", status="verified", safety="service",
            preconditions=BRAKES, ref="31 22 11..14"),
    *[Command(f"{d}_{s}", "slabs", f"{d.capitalize()} {s} corner", status="verified", safety="service",
              ref=r) for d, s, r in (("raise", "left", "31 33 28"), ("raise", "right", "31 34 28"),
                                    ("lower", "left", "31 35 28"), ("lower", "right", "31 36 28"))],
    Command("store_heights", "slabs", "Store target heights", status="planned", safety="gated",
            confirm="typed", ref="writes calibration — needs its own ADR"),
    # ---- BCU (all security functions gated by ADR-0007) ----
    Command("eka_read", "bcu", "Read EKA code", status="planned", safety="gated", confirm="typed",
            ref="21 CC behind SecurityAccess (ADR-0007)"),
    Command("eka_set", "bcu", "Set EKA code", status="planned", safety="gated", confirm="typed",
            ref="3B CC — never sent"),
    Command("key_program", "bcu", "Key programming", status="planned", safety="gated", confirm="typed",
            ref="never sent"),
    # ---- ACE / autobox: known from the NanoCom, not wired ----
    Command("ace_calibrate_1", "ace", "Calibrate accelerometer 1", status="planned", safety="gated",
            confirm="typed", ref="15 15 FF — writes calibration"),
    Command("ace_calibrate_2", "ace", "Calibrate accelerometer 2", status="planned", safety="gated",
            confirm="typed", ref="16 16 FF — writes calibration"),
    Command("ace_set_calibrated", "ace", "Set calibrated", status="planned", safety="gated",
            confirm="typed", ref="10 10 00 — reported to lock up ACE ECUs"),
    Command("ace_bleed", "ace", "Oil bleed (3 steps)", status="planned", safety="service", ref="not captured"),
    Command("autobox_reset_adaptives", "autobox", "Reset adaptive values", status="planned",
            safety="service", ref="72 06 83 FF 07 08 FF (undecoded)"),
]

REGISTRY: "dict[tuple[str, str], Command]" = {(c.module, c.action): c for c in _ALL}


def get(module: str, action: str) -> "Command | None":
    """The registered command for a store module + action, or None."""
    return REGISTRY.get((module, action))


def for_module(module: str) -> "list[Command]":
    return [c for c in _ALL if c.module == module]


def refusal(module: str, action: str, trust: str = "", public: bool = False) -> "str | None":
    """Why the server must refuse this action (None = allowed). Pure policy, no I/O.

    Only *module* actions are judged here; server-level actions (select_module, csv,
    connect, read_block, clear_faults …) are not module commands and return None.
    """
    c = get(module, action)
    if c is None:
        return None
    if c.safety == "gated":
        return f"{c.label} is gated: never sent by this project"
    if c.status == "planned":
        return f"{c.label} is not implemented yet"
    if public and c.safety in ("actuator", "service"):
        return "actuator and service actions are disabled on the public server"
    if c.status == "experimental" and trust != "experimental":
        return f"{c.label} is experimental: enable Experimental mode to run it"
    return None
