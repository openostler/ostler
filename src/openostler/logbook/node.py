# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""What the session recorder reads from a node snapshot (NodeSource spec §7, §10).

A snapshot with ``source_kind: "node"`` comes from ``web/node_source.py``. The rules:

- **Open** a session only when the node is ``online``, its ``power.state`` is ``awake`` or
  ``held`` and at least one value is live (not stale): stored values delivered at
  subscribe time are last known values and never open, or fill, a session.
- **End** at once when the node sleeps cleanly (``status: asleep``, ``end_reason:
  node_asleep``); ``offline`` (its will) or a lost broker only pauses the session, and the
  300 s idle rule ends it (ADR-0011; owner answer 8).
- **Rows** carry live values only: a signal or VSS reading marked ``stale`` is never
  written. ``vss`` paths add a merged column ``<path>`` (the selected source) and one
  column per device ``<path>@<device>`` (ADR-0032 A4 records every receiver and the merged
  stream). Identity paths are never written.
- **Utc** is the node's wall clock when it is synced (a live reading's ``ts_utc`` plus its
  age on the node's clock), else the Brain's (``time_unsynced`` in ``events.jsonl``).
"""
from __future__ import annotations

import math
import re

from ..node.table import parse_utc

RECORD_POWER = ("awake", "held")
# A VSS path segment that names identity data (the recorder's name rule, plus the VSS
# ``VehicleIdentification`` branch: VIN, WMI and the like).
_IDENTITY_SEGMENT = re.compile(r"(^|_)(vin|eka|ident|identity|serial|part_?no|part_number)($|_)"
                               r"|identification", re.IGNORECASE)


def is_node(snap: "dict | None") -> bool:
    return isinstance(snap, dict) and snap.get("source_kind") == "node"


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)) and math.isfinite(v):
        return v
    return None


def is_live(sv) -> bool:
    """A signal or VSS reading that may be written as a row value."""
    return isinstance(sv, dict) and sv.get("stale") is not True


def has_live(snap: dict) -> bool:
    sigs = snap.get("signals") or {}
    if any(is_live(sv) and _num(sv.get("v")) is not None for sv in sigs.values()):
        return True
    return any(is_live(r) and _num(r.get("value")) is not None
               for r in (snap.get("vss") or {}).values())


def may_open(snap: dict) -> bool:
    """The node rule for opening a session (spec §7)."""
    node = snap.get("node") or {}
    state = (node.get("power") or {}).get("state")
    return (snap.get("status") == "connected" and node.get("status") == "online"
            and state in RECORD_POWER and has_live(snap))


def asleep(snap: dict) -> bool:
    return snap.get("status") == "asleep"


def identity_path(path: str) -> bool:
    """A VSS path (or column) naming identity data; camel case is split first
    (``SerialNumber`` → ``Serial_Number``), acronyms kept (``VIN``)."""
    return any(_IDENTITY_SEGMENT.search(re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", seg))
               for seg in re.split(r"[./@]", path or "") if seg)


def vss_values(snap: dict) -> "dict[str, tuple[float, str]]":
    """``{column: (value, unit)}`` for the live VSS readings: ``<path>`` from the selected
    source and ``<path>@<device>`` per device (the freshest live source of that device)."""
    out: "dict[str, tuple[float, str]]" = {}
    for path, r in sorted((snap.get("vss") or {}).items()):
        if not isinstance(path, str) or not isinstance(r, dict) or identity_path(path):
            continue
        unit = str(r.get("unit") or "")
        v = _num(r.get("value"))
        if is_live(r) and v is not None:
            out[path] = (v, unit)
        best: "dict[str, tuple[float, float, str]]" = {}
        for src, s in sorted((r.get("sources") or {}).items()):
            sv = _num((s or {}).get("v"))
            if not is_live(s) or sv is None:
                continue
            device = str(src).split("/", 1)[0]
            age = s.get("age_s")
            age = float(age) if isinstance(age, (int, float)) else math.inf
            if device not in best or age < best[device][1]:
                best[device] = (sv, age, str(s.get("u") or unit))
        for device, (sv, _age, u) in best.items():
            out[f"{path}@{device}"] = (sv, u)
    return out


def node_utc_ms(snap: dict) -> "float | None":
    """The node's wall clock now (epoch ms): the freshest live reading with a ``ts_utc``
    plus its age on the node's clock; None when no live reading has one (unsynced)."""
    best = None
    readings = list((snap.get("signals") or {}).values()) + list((snap.get("vss") or {}).values())
    for r in readings:
        if not is_live(r):
            continue
        t = parse_utc(r.get("ts_utc")) if isinstance(r.get("ts_utc"), str) else None
        age = r.get("age_s")
        if t is None or not isinstance(age, (int, float)):
            continue
        if best is None or age < best[1]:
            best = (t + float(age), float(age))
    return None if best is None else best[0] * 1000.0


def pack_info() -> "dict | None":
    """``{id, version}`` of the active vehicle pack (ADR-0010 amendment: a session records
    which pack decoded it); ``version`` is its distribution's, or None."""
    try:
        from ..pack import _entry_points, active_pack

        pack = active_pack()
    except Exception:  # noqa: BLE001 — no pack must never stop recording
        return None
    version = None
    try:
        for ep in _entry_points():
            dist = getattr(ep, "dist", None)
            if ep.name == pack.id and dist is not None:
                version = dist.version
                break
    except Exception:  # noqa: BLE001
        version = None
    return {"id": pack.id, "version": version}


__all__ = ["RECORD_POWER", "asleep", "has_live", "identity_path", "is_live", "is_node",
           "may_open", "node_utc_ms", "pack_info", "vss_values"]
