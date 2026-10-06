# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The SAE J1979 (OBD-II) service layer, shared by K-line and CAN
(specs/2026-10-06-j1979-service-layer-design.md).

Stdlib-only and transport-agnostic: it talks to an :class:`ObdRequestLink` (the K-line
adapter is :class:`openostler.kline.obd_link.KLineObdLink`) and imports nothing from
``kline``, ``kwp2000`` or ``can``. PID formulas come from a pack's store
(:class:`PidTable`); the platform ships none. Mode 08 is never sent, and Mode 04 runs only
through :meth:`J1979.clear_dtcs` with a :class:`ClearGrant`. This Python layer is the
lab/reference; the production link layer moves to the node in C later, checked by the
shared vectors in ``tests/vectors/j1979/`` (ADR-0032).
"""
from .clear import ClearContext, ClearGate, ClearGrant, ClearPlan, ClearRefused, plan
from .decode import Dtc, DtcRead, MonitorTest, PidError, PidValue, Readiness
from .diagnostics import Diagnostics, derive
from .j1979 import (
    ClearOutcome,
    ClearResult,
    DtcResult,
    EcuIdentity,
    EcuSupport,
    FreezeFrame,
    Identity,
    J1979,
    MonitorResult,
    PidRead,
    RawMonitorTest,
    SupportReport,
)
from .link import EcuReply, EcuStatus, ForbiddenService, ObdError, ObdRequestLink, Pacer
from .pids import PidTable

__all__ = [
    "J1979", "ObdRequestLink", "EcuReply", "EcuStatus", "Pacer", "ObdError",
    "ForbiddenService", "PidTable", "PidValue", "PidError", "PidRead", "Dtc", "DtcRead",
    "DtcResult", "Readiness", "FreezeFrame", "MonitorTest", "MonitorResult",
    "RawMonitorTest", "Identity", "EcuIdentity", "SupportReport", "EcuSupport",
    "Diagnostics", "derive", "ClearContext", "ClearGate", "ClearGrant", "ClearPlan",
    "ClearRefused", "ClearOutcome", "ClearResult", "plan",
]
