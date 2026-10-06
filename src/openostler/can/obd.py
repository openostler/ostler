# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The CAN :class:`~openostler.obd.link.ObdRequestLink` adapter (CanLink spec §5, J1979
spec §1–§2).

| | Functional | Physical | Replies | FC to |
|---|---|---|---|---|
| 11-bit | ``7DF`` | ``7E0``–``7E7`` | ``7E8``–``7EF`` | reply id − 8 |
| 29-bit | ``18DB33F1`` | ``18DAxxF1`` | ``18DAF1xx`` | ``18DAxxF1`` |

:meth:`CanObdRequestLink.request` flushes RX, sends one padded single frame (DLC 8, pad
``0x55`` by default) through the link's ``TxGate`` as Tier 0, and lets the
:class:`~openostler.can.isotp.IsoTpMux` collect one message per responding ECU until P2
(or P2* after ``7F xx 78``). Keys are ``"7E8"`` or ``"18DAF110"``. Pacing, the late-frame
drop and the typed results are the shared logic in ``obd/link.py``. A request that is not
a Tier 0 read (Mode 04) needs a ``TxGrant`` from ``grant_for``; functional requests are
always single frames, and Mode 08 is refused like on every adapter.
"""
from __future__ import annotations

from typing import Callable, Dict, Optional

from ..obd.link import EcuReply, ObdError, guard_payload
from .gate import OBD_READS, TIER0
from .isotp import IsoTpMux, IsoTpParams
from .link import CanLink

FUNC_11, FUNC_29 = 0x7DF, 0x18DB33F1


def is_reply_id(can_id: int, extended: bool) -> bool:
    if extended:
        return (can_id & 0x1FFFFF00) == 0x18DAF100
    return 0x7E8 <= can_id <= 0x7EF


def fc_id_for(can_id: int, extended: bool) -> int:
    """The id our FC (and a physical request) goes to for a reply id."""
    if extended:
        return 0x18DA00F1 | ((can_id & 0xFF) << 8)
    return can_id - 8


def ecu_key(can_id: int, extended: bool) -> str:
    return f"{can_id:08X}" if extended else f"{can_id:03X}"


def physical_id(target: str, extended: bool) -> int:
    """``"7E8"`` → ``0x7E0``; ``"18DAF110"`` → ``0x18DA10F1``."""
    rid = int(target, 16)
    if not is_reply_id(rid, extended):
        raise ObdError(f"not an OBD reply address for this link: {target!r}")
    return fc_id_for(rid, extended)


class CanObdRequestLink:
    """An :class:`ObdRequestLink` over a :class:`CanLink` with a confirmed rate."""

    def __init__(self, link: CanLink, *, extended: bool = False,
                 params: "IsoTpParams | None" = None,
                 grant_for: "Optional[Callable[[bytes, int], object]]" = None,
                 clock: "Optional[Callable[[], float]]" = None,
                 sleep: "Optional[Callable[[float], None]]" = None) -> None:
        self.link = link
        self.extended = extended
        self.flavor = "can29" if extended else "can11"
        self.params = params or IsoTpParams()
        self.grant_for = grant_for
        self.mux = IsoTpMux(link, extended=extended,
                            reply_ok=lambda i: is_reply_id(i, extended),
                            fc_id_for=lambda i: fc_id_for(i, extended),
                            params=self.params, clock=clock, sleep=sleep)

    @property
    def dropped(self) -> int:
        return self.mux.dropped

    def request(self, payload: bytes, *, target: "str | None" = None,
                expect_messages: "int | None" = None,
                timeout: "float | None" = None) -> "Dict[str, EcuReply]":
        payload = bytes(payload)
        guard_payload(payload, allow_clear=True)
        if target is None and len(payload) > 7:
            raise ObdError("a functional request is always a single frame (≤ 7 bytes)")
        tx = (FUNC_29 if self.extended else FUNC_11) if target is None \
            else physical_id(target, self.extended)
        grant: object = TIER0
        if payload[0] not in OBD_READS:
            grant = self.grant_for(payload, tx) if self.grant_for is not None else None
        rid = int(target, 16) if target is not None else None
        got = self.mux.request(payload, tx, grant=grant, target=rid, timeout=timeout)
        out = {ecu_key(i, self.extended): EcuReply(ecu_key(i, self.extended), (m,))
               for i, m in sorted(got.items())}
        if target is not None:
            out = {e: r for e, r in out.items() if e == target.upper()}
        return out


__all__ = ["CanObdRequestLink", "is_reply_id", "fc_id_for", "ecu_key", "physical_id",
           "FUNC_11", "FUNC_29"]
