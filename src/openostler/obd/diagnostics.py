# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``Vehicle.Ostler.Diagnostics.*`` derivation (spec §6).

These leaves combine services and ECUs, so they are derived here rather than read from a
store record. Each ECU's value keeps its source tag (``sources``); the leaf takes the
aggregate. Pure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional

from .decode import DtcRead, Readiness

ROOT = "Vehicle.Ostler.Diagnostics"
MIL_ON = f"{ROOT}.MilOn"
DTC_COUNT = f"{ROOT}.DtcCount"
PENDING_DTC_COUNT = f"{ROOT}.PendingDtcCount"
IS_READINESS_COMPLETE = f"{ROOT}.IsReadinessComplete"
READINESS_INCOMPLETE_COUNT = f"{ROOT}.ReadinessIncompleteCount"
DISTANCE_SINCE_DTC_CLEAR = f"{ROOT}.DistanceSinceDtcClear"

# The engine ECU's address per flavour: CAN 11-bit 7E8, 29-bit 18DAF110, K-line 10.
ENGINE_ECUS = ("7E8", "18DAF110", "10")


@dataclass(frozen=True)
class Diagnostics:
    values: "Dict[str, object]" = field(default_factory=dict)
    sources: "Dict[str, Dict[str, object]]" = field(default_factory=dict)


def derive(readiness: "Mapping[str, Readiness]",
           pending: "Optional[Iterable[DtcRead]]" = None,
           distance_m: "Optional[Mapping[str, float]]" = None) -> Diagnostics:
    """Aggregate per-ECU results into the Diagnostics leaves.

    ``readiness`` is PID 01 per ECU; ``pending`` the Mode 07 reads; ``distance_m`` PID
    ``31`` per ECU in metres (open question 2's draft: the engine ECU, otherwise the largest
    value). A leaf with no input is absent, never zero."""
    vals: "Dict[str, object]" = {}
    src: "Dict[str, Dict[str, object]]" = {}
    rd = {e: r for e, r in readiness.items() if r.mil is not None}
    if rd:
        src[MIL_ON] = {e: r.mil for e, r in rd.items()}
        vals[MIL_ON] = any(r.mil for r in rd.values())
        src[DTC_COUNT] = {e: r.dtc_count for e, r in rd.items()}
        vals[DTC_COUNT] = sum(int(r.dtc_count or 0) for r in rd.values())
        supported: "set[str]" = set()
        incomplete: "set[str]" = set()
        for r in rd.values():
            for name, m in r.monitors.items():
                if m.supported:
                    supported.add(name)
                    if not m.complete:
                        incomplete.add(name)
        src[READINESS_INCOMPLETE_COUNT] = {e: len(r.incomplete) for e, r in rd.items()}
        vals[IS_READINESS_COMPLETE] = not incomplete
        vals[READINESS_INCOMPLETE_COUNT] = len(incomplete)
        src[IS_READINESS_COMPLETE] = {e: not r.incomplete for e, r in rd.items()}
    if pending is not None:
        reads = list(pending)
        src[PENDING_DTC_COUNT] = {r.ecu: len(r.dtcs) for r in reads}
        vals[PENDING_DTC_COUNT] = len({d.code for r in reads for d in r.dtcs})
    if distance_m:
        metres = {e: float(v) for e, v in distance_m.items()}
        src[DISTANCE_SINCE_DTC_CLEAR] = metres
        engine = next((e for e in ENGINE_ECUS if e in metres), None)
        vals[DISTANCE_SINCE_DTC_CLEAR] = metres[engine] if engine else max(metres.values())
    return Diagnostics(vals, src)


__all__ = ["derive", "Diagnostics", "ENGINE_ECUS", "MIL_ON", "DTC_COUNT",
           "PENDING_DTC_COUNT", "IS_READINESS_COMPLETE", "READINESS_INCOMPLETE_COUNT",
           "DISTANCE_SINCE_DTC_CLEAR"]
