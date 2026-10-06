# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The CAN path of the comms core (specs/2026-10-06-canlink-isotp-design.md, ADR-0020,
ADR-0023): a frame-level :class:`CanLink` beside the byte ``Transport``, listen-only by
default; passive bitrate detection; our own pure-Python ISO-TP; the transmit gate; and the
J1979 adapter :class:`CanObdRequestLink`.

Stdlib only (plus pyserial for serial slcan/GVRET). ``pycan`` (python-can) is imported
only by its own module, with the optional ``[can]`` extra. This Python code is the
lab/reference; production CAN I/O and the production gate are the node's TWAI and C
``TxGate`` (spec §7.1, ADR-0032), checked by the shared vectors in ``tests/vectors/can/``.
"""
from .detect import DetectResult, RateMemory, detect
from .frame import CanFrame
from .gate import TIER0, AllowEntry, GateDecision, ProbeGrant, TxGate, TxGrant
from .isotp import (
    IsoTpChannel,
    IsoTpError,
    IsoTpMux,
    IsoTpParams,
    IsoTpSniffer,
    IsoTpTimeout,
    KernelIsoTpChannel,
)
from .link import (
    ACTIVE,
    CLOSED,
    CONFIRMED,
    LISTENING,
    CanError,
    CanLink,
    LinkCaps,
    OneShotResult,
    RateNotConfirmed,
    TxRefused,
)
from .logging_link import LoggingCanLink
from .obd import CanObdRequestLink

__all__ = [
    "CanFrame", "CanLink", "LinkCaps", "OneShotResult", "CanError", "TxRefused",
    "RateNotConfirmed", "CLOSED", "LISTENING", "CONFIRMED", "ACTIVE", "TxGate", "TxGrant",
    "ProbeGrant", "AllowEntry", "GateDecision", "TIER0", "detect", "DetectResult",
    "RateMemory", "IsoTpParams", "IsoTpChannel", "IsoTpMux", "IsoTpSniffer",
    "KernelIsoTpChannel", "IsoTpError", "IsoTpTimeout", "LoggingCanLink",
    "CanObdRequestLink",
]
