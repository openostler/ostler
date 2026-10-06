# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Channel names, units and groups for session files and exports (ADR-0009).

Session files use the signal store names (``rpm``, ``coolant_temp``) and ``GPS_*``.
Exports use AiM-style names via ``export_name``: known channels map to their AiM name,
``GPS_*`` pass through, anything else becomes ``Title_Case``.
"""
from __future__ import annotations

import json

GPS_CHANNELS = ("GPS_Latitude", "GPS_Longitude", "GPS_Speed", "GPS_Heading",
                "GPS_Altitude", "GPS_Nsat", "GPS_HDOP")
GPS_ACCEL_CHANNELS = ("GPS_LonAcc", "GPS_LatAcc")  # GPS-derived acceleration (g)
ACCEL_RAW_CHANNELS = ("Acc_X", "Acc_Y", "Acc_Z")  # sensor frame, m/s²
ACCEL_VEHICLE_CHANNELS = ("InlineAcc", "LateralAcc", "VerticalAcc")  # vehicle frame, g
ACCEL_CHANNELS = ACCEL_RAW_CHANNELS + ACCEL_VEHICLE_CHANNELS
TEXT_CHANNELS = ("module", "faults")
TIME_CHANNELS = ("Interval", "Utc")

UNITS = {
    "Interval": "ms", "Utc": "ms",
    "GPS_Latitude": "deg", "GPS_Longitude": "deg", "GPS_Speed": "km/h",
    "GPS_Heading": "deg", "GPS_Altitude": "m", "GPS_Nsat": "", "GPS_HDOP": "",
    "GPS_LonAcc": "g", "GPS_LatAcc": "g",
    "Acc_X": "m/s²", "Acc_Y": "m/s²", "Acc_Z": "m/s²",
    "InlineAcc": "g", "LateralAcc": "g", "VerticalAcc": "g",
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


_STORE: "dict[str, dict] | None" = None
_STORE_KEY: "tuple | None" = None


def _store_records() -> "dict[str, dict]":
    """name → its signal store record, read once per store directory. A name in several
    modules (``battery``) takes the record of the module listed first by the vehicle pack
    (``pack.modules`` order), then any other store file in name order."""
    global _STORE, _STORE_KEY
    from .. import signals
    from ..pack import active_pack

    pack = active_pack()
    root = signals._dir()
    key = (str(root), id(pack))
    if _STORE is None or _STORE_KEY != key:
        recs_by_name: "dict[str, dict]" = {}
        order = {m: i for i, m in enumerate(pack.module_ids())}
        for p in sorted(root.glob("*.json"),
                        key=lambda q: (order.get(q.stem, len(order)), q.name)):
            try:
                recs = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for r in recs if isinstance(recs, list) else []:
                if isinstance(r, dict) and r.get("name"):
                    recs_by_name.setdefault(str(r["name"]), r)
        _STORE, _STORE_KEY = recs_by_name, key
    return _STORE


def _store_groups() -> "dict[str, str]":
    """name → group (lower case) from the signal store JSON files, first one wins."""
    return {n: str(r["group"]).lower() for n, r in _store_records().items() if r.get("group")}


def is_accel(name: str) -> bool:
    return name in ACCEL_CHANNELS or name in GPS_ACCEL_CHANNELS


def group_for(name: str) -> str:
    """The channel's group for ``meta.channels``: ``accel`` (every acceleration channel,
    GPS-derived too), ``gps``, ``text`` or the store group (lower case)."""
    if is_accel(name):
        return "accel"
    if name.startswith("GPS_"):
        return "gps"
    if name in TEXT_CHANNELS:
        return "text"
    rec = _store_records().get(name) or {}
    return str(rec.get("group") or "").lower()


def confidence_for(name: str) -> "str | None":
    """``proven``/``candidate`` from the signal store; None for GPS, acceleration and text
    channels (not ECU data). A signal missing from the store is ``candidate``."""
    if name.startswith("GPS_") or is_accel(name) or name in TEXT_CHANNELS \
            or name in TIME_CHANNELS:
        return None
    rec = _store_records().get(name)
    c = (rec or {}).get("confidence")
    if c in ("belagt", "proven"):
        return "proven"
    return "candidate"


def limits_for(name: str) -> "list[float] | None":
    """The store's alarm ``limits`` ``[lo, hi]``, or None."""
    lim = (_store_records().get(name) or {}).get("limits")
    if isinstance(lim, (list, tuple)) and len(lim) == 2 and all(
            isinstance(x, (int, float)) and not isinstance(x, bool) for x in lim):
        return [lim[0], lim[1]]
    return None
