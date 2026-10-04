"""Channel names, units and groups for session files and exports (ADR-0009).

Session files use the signal store names (``rpm``, ``coolant_temp``) and ``GPS_*``.
Exports use AiM-style names via ``export_name``: known channels map to their AiM name,
``GPS_*`` pass through, anything else becomes ``Title_Case``.
"""
from __future__ import annotations

import json
from pathlib import Path

GPS_CHANNELS = ("GPS_Latitude", "GPS_Longitude", "GPS_Speed", "GPS_Heading",
                "GPS_Altitude", "GPS_Nsat", "GPS_HDOP")
TEXT_CHANNELS = ("module", "faults")
TIME_CHANNELS = ("Interval", "Utc")

UNITS = {
    "Interval": "ms", "Utc": "ms",
    "GPS_Latitude": "deg", "GPS_Longitude": "deg", "GPS_Speed": "km/h",
    "GPS_Heading": "deg", "GPS_Altitude": "m", "GPS_Nsat": "", "GPS_HDOP": "",
    "module": "", "faults": "",
}

_EXPORT = {
    "Interval": "Time",
    "rpm": "RPM",
    "speed": "Speed",
    "coolant_temp": "Water_Temp",
    "air_temp": "Intake_Air_Temp",
    "ext_temp": "Ambient_Temp",
    "fuel_temp": "Fuel_Temp",
    "battery": "Battery",
    "battery_direct": "Battery_Direct",
    "manifold_press": "MAP",
    "ambient_press_1": "Baro",
    "accel_pedal_pct": "Throttle_Pedal",
    "injection_qty": "Fuel_Quantity",
    "driver_demand": "Driver_Demand",
    "maf": "MAF",
    "egr_pos": "EGR_Position",
    "wastegate_pos": "Wastegate_Position",
    "wheel_speed_fl": "Wheel_Speed_FL",
    "wheel_speed_fr": "Wheel_Speed_FR",
    "wheel_speed_rl": "Wheel_Speed_RL",
    "wheel_speed_rr": "Wheel_Speed_RR",
    "module": "Module",
    "faults": "Faults",
}


def export_name(name: str) -> str:
    """AiM-style export name: ``rpm`` → ``RPM``, ``coolant_temp`` → ``Water_Temp``,
    ``GPS_*`` unchanged, unknown ``foo_bar`` → ``Foo_Bar``."""
    if name in _EXPORT:
        return _EXPORT[name]
    if name.startswith("GPS_"):
        return name
    parts = [p for p in name.replace("-", "_").replace(" ", "_").split("_") if p]
    return "_".join(p[:1].upper() + p[1:] for p in parts) or name


_GROUPS: "dict[str, str] | None" = None


def _store_groups() -> "dict[str, str]":
    """name → group (lower case) from the signal store JSON files, first one wins."""
    global _GROUPS
    if _GROUPS is None:
        groups: "dict[str, str]" = {}
        root = Path(__file__).resolve().parent.parent / "signals"
        for p in sorted(root.glob("*.json")):
            try:
                recs = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for r in recs if isinstance(recs, list) else []:
                if isinstance(r, dict) and r.get("name") and r.get("group"):
                    groups.setdefault(r["name"], str(r["group"]).lower())
        _GROUPS = groups
    return _GROUPS


def group_for(name: str) -> str:
    """The channel's group for ``meta.channels``: ``gps``, ``text`` or the store group."""
    if name.startswith("GPS_"):
        return "gps"
    if name in TEXT_CHANNELS:
        return "text"
    return _store_groups().get(name, "")
