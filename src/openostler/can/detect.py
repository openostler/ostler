# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Passive CAN bitrate and ID-width detection (ADR-0023, CanLink spec §4).

:func:`detect` never transmits at an unconfirmed rate:

1. A **declared** rate (pack ``transport`` block, or a manual choice in service mode)
   opens listen-only and is confirmed with no detection and no probe.
2. **Listen** at each rate of ``[remembered, 500k, 250k]`` (deduplicated) for up to 2 s;
   any error frame or RX error-counter growth rejects the rate; **20 clean frames**
   confirm it. The ID widths seen are recorded.
3. **Then one request**: a single functional ``01 00`` on ``7DF`` if 11-bit traffic was
   seen, else on ``18DB33F1``; with no reply, the other width once.
4. **Silent bus**: refused unless Parked. Per rate (500k, then 250k automatically, owner
   Q9) one one-shot ``7DF 02 01 00``; an ACK with no error confirms; the first error frame
   stops detection; the driving state is re-read before each probe. A link without
   ``one_shot`` refuses the probe.
5. **Noisy bus** (frames, never 20 clean): listen-only, ``"bitrate not confirmed"``.

A confirmed rate is remembered per ``vid`` (:class:`RateMemory`), never per VIN.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .frame import CanFrame, pad
from .gate import TxGate
from .isotp import IsoTpMux, IsoTpParams
from .link import CanLink, TxRefused
from .obd import FUNC_11, FUNC_29, ecu_key, fc_id_for, is_reply_id

RATES = (500_000, 250_000)
CLEAN_FRAMES = 20
LISTEN_WINDOW = 2.0
NOT_CONFIRMED = "bitrate not confirmed"


@dataclass
class DetectResult:
    rate: "int | None" = None
    widths: "frozenset[int]" = frozenset()
    source: "str | None" = None          # detected | declared | probe
    frames: int = 0
    errors: int = 0
    ecus: "Tuple[str, ...]" = ()
    reason: "str | None" = None
    log: "List[dict]" = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.rate is not None

    def to_dict(self) -> dict:
        return {"rate": self.rate, "widths": sorted(self.widths), "source": self.source,
                "frames": self.frames, "errors": self.errors, "ecus": list(self.ecus),
                "reason": self.reason}


def _listen(link: CanLink, rate: int, window: float, need: int) -> "Tuple[bool, int, int, set]":
    """Listen-only at ``rate``. → ``(clean, frames, errors, widths)``."""
    link.open(rate, listen_only=True)
    start = link.clock()
    base = link.error_counters()
    frames = errors = 0
    widths: set = set()
    while True:
        left = start + window - link.clock()
        if left <= 0:
            return (False, frames, errors, widths)
        fr = link.recv(left)
        if fr is None:
            continue
        if fr.error:
            return (False, frames, errors + 1, widths)
        cnt = link.error_counters()
        if base is not None and cnt is not None and cnt[1] > base[1]:
            return (False, frames, errors + 1, widths)
        frames += 1
        widths.add(29 if fr.extended else 11)
        if frames >= need:
            return (True, frames, errors, widths)


def _one_request(link: CanLink, extended: bool, params: IsoTpParams) -> "Tuple[str, ...]":
    mux = IsoTpMux(link, extended=extended, reply_ok=lambda i: is_reply_id(i, extended),
                   fc_id_for=lambda i: fc_id_for(i, extended), params=params)
    got = mux.request(b"\x01\x00", FUNC_29 if extended else FUNC_11)
    return tuple(ecu_key(i, extended) for i in sorted(got)
                 if got[i][:2] == b"\x41\x00")


def detect(link: CanLink, *, declared: "int | None" = None,
           remembered: "int | None" = None, driving_state: "Optional[Callable[[], object]]" = None,
           request: bool = True, window: float = LISTEN_WINDOW, need: int = CLEAN_FRAMES,
           declared_widths: "frozenset[int] | None" = None,
           params: "IsoTpParams | None" = None) -> DetectResult:
    """Detect the bitrate on ``link`` (closed or open) and leave it open, listen-only, at
    the confirmed rate; or listen-only at 500k with ``reason`` set when none is."""
    params = params or IsoTpParams()
    res = DetectResult()
    gate = link._gate()
    if driving_state is not None:
        gate.driving_state = driving_state
    if declared is not None:
        link.open(declared, listen_only=True)
        link.confirm_rate("declared", declared_widths or frozenset({11}))
        res.rate, res.source, res.widths = declared, "declared", link.id_widths
        res.log.append({"step": "declared", "rate": declared})
        return res
    order: List[int] = []
    for r in (remembered, *RATES):
        if r and r not in order:
            order.append(r)
    seen_any = False
    for rate in order:
        clean, n, e, widths = _listen(link, rate, window, need)
        res.frames += n
        res.errors += e
        seen_any = seen_any or n > 0 or e > 0
        res.log.append({"step": "listen", "rate": rate, "frames": n, "errors": e,
                        "clean": clean})
        if clean:
            link.confirm_rate("detected", frozenset(widths))
            res.rate, res.source, res.widths = rate, "detected", frozenset(widths)
            if request:
                res.ecus = _request_both(link, widths, params, res)
                link.end_session()              # back to listen-only after the one request
            return res
    if seen_any:
        res.reason = NOT_CONFIRMED
        link.open(order[0], listen_only=True)
        return res
    return _silent_bus(link, gate, params, res)


def _request_both(link: CanLink, widths: set, params: IsoTpParams,
                  res: DetectResult) -> "Tuple[str, ...]":
    order = (False, True) if 11 in widths or not widths else (True, False)
    for extended in order:
        try:
            ecus = _one_request(link, extended, params)
        except TxRefused as exc:
            res.log.append({"step": "request", "refused": exc.code})
            return ()
        res.log.append({"step": "request", "width": 29 if extended else 11,
                        "ecus": list(ecus)})
        if ecus:
            link.confirm_rate(link.rate_source, frozenset(widths) | {29 if extended else 11})
            res.widths = link.id_widths
            return ecus
    return ()


def _silent_bus(link: CanLink, gate: TxGate, params: IsoTpParams,
                res: DetectResult) -> DetectResult:
    res.reason = NOT_CONFIRMED
    if not link.caps.one_shot:
        link.open(RATES[0], listen_only=True)
        res.log.append({"step": "probe", "refused": "no_one_shot"})
        res.reason = f"{NOT_CONFIRMED}: silent bus and the adapter has no one-shot mode"
        return res
    frame = CanFrame(FUNC_11, False, pad(b"\x02\x01\x00", params.pad))
    for rate in RATES:
        link.open(rate, listen_only=True)
        try:
            probe = gate.probe_grant()          # re-reads the driving state each time
            out = link.send_oneshot(frame, probe=probe)
        except TxRefused as exc:
            res.log.append({"step": "probe", "rate": rate, "refused": exc.code})
            res.reason = f"{NOT_CONFIRMED}: the silent-bus probe needs the vehicle Parked" \
                if exc.code == "not_parked" else f"{NOT_CONFIRMED}: probe refused ({exc.code})"
            return res
        res.log.append({"step": "probe", "rate": rate, "acked": out.acked, "error": out.error})
        if out.error:
            res.errors += 1
            return res                           # the first error frame stops detection
        if out.acked:
            link.confirm_rate("probe", frozenset({11}))
            res.rate, res.source, res.widths, res.reason = rate, "probe", frozenset({11}), None
            res.ecus = tuple(sorted({f.id_text for f in out.replies
                                     if not f.error and is_reply_id(f.id, f.extended)}))
            return res
    link.open(RATES[0], listen_only=True)
    return res


class RateMemory:
    """The confirmed rate per ``vid`` in ``<state dir>/can_rates.json`` (never a VIN). A
    remembered rate only sets the listening order."""

    def __init__(self, path: "str | Path") -> None:
        self.path = Path(path)

    def _load(self) -> Dict[str, dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def get(self, vid: str) -> "int | None":
        rec = self._load().get(vid)
        return int(rec["rate"]) if isinstance(rec, dict) and rec.get("rate") else None

    def remember(self, vid: str, result: DetectResult) -> None:
        if not result.ok or result.source == "declared":
            return
        doc = self._load()
        doc[vid] = {"rate": result.rate, "widths": sorted(result.widths)}
        tmp = self.path.with_suffix(".tmp")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)


__all__ = ["detect", "DetectResult", "RateMemory", "RATES", "CLEAN_FRAMES",
           "LISTEN_WINDOW", "NOT_CONFIRMED"]
