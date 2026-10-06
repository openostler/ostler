# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Basic mode — read fault codes from all modules sequentially.

K-line is a shared bus → one module at a time: establish → read faults → close, then
the next. Returns a normalized report ``[{module, status, faults, note}]`` where
``status`` ∈ ``ok`` (no faults) / ``faults`` / ``error`` (could not read) /
``unimplemented`` (no reading comms class yet).

Generic: the readers come from the active vehicle pack (``VehiclePack.faultscan``, one
:class:`openostler.pack.FaultReader` per readable module, each owning its establish/release),
and the rows without a reader from ``VehiclePack.faultscan_unimplemented``.
"""
from __future__ import annotations

import time
from typing import Callable

from .pack import active_pack

# Quiet gap between modules: let the bus go idle before the next init.
_GAP = 0.5


def _row(module: str, faults: "list[str]", *, note: str = "") -> "dict":
    return {"module": module, "status": "faults" if faults else "ok",
            "faults": faults, "note": note}


def _err(module: str, exc: "Exception", *, note: str = "") -> "dict":
    return {"module": module, "status": "error", "faults": [],
            "error": f"{type(exc).__name__}: {exc}", "note": note}


def unimplemented_rows() -> "list[dict]":
    """The modules without a reading comms class, as ``unimplemented`` report rows."""
    return [{"module": name, "status": "unimplemented", "faults": [], "note": note}
            for name, note in active_pack().faultscan_unimplemented]


def read_all(port: str = "auto",
             sleep: "Callable[[float], None]" = time.sleep) -> "list[dict]":
    """Read fault codes from all modules on the car (live only: ADR-0011, no demo mode)."""
    return _live_report(port, sleep) + unimplemented_rows()


def _live_report(port: str, sleep: "Callable[[float], None]") -> "list[dict]":
    from . import ports

    readers = active_pack().faultscan
    try:
        real_port = ports.resolve_serial_port(port)
    except FileNotFoundError as exc:
        # no cable → mark every readable module as unread, same cause
        return [_err(r.label, exc) for r in readers]

    rows = []
    for i, reader in enumerate(readers):
        try:
            rows.append(_row(reader.label, list(reader.read(real_port)), note=reader.note))
        except Exception as exc:  # noqa: BLE001 — one module failing must not stop the scan
            note = reader.error_note if reader.error_note is not None else reader.note
            rows.append(_err(reader.label, exc, note=note))
        if i + 1 < len(readers):
            sleep(_GAP)  # let the bus go quiet between modules
    return rows
