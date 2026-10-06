# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""K-line protocol auto-detection for a car with no profile (ADR-0022, spec §2).

:func:`detect` is at most one fast init and one 5-baud init, in that order:

1. **Listen first.** Hold the line idle for W5 and read RX. Any byte means another tester
   or an open session: ``bus-busy``, nothing is sent.
2. **Fast init** ``C1 33 F1 81 66`` (functional), tolerant of a glitch byte and an
   unaddressed ``03 C1 …`` reply. ``C1 KB1 KB2`` → KWP2000 fast. A negative reply
   (``7F 81 …``) is ``ecu-refused`` and stops detection: no 5-baud follows (an ignition
   cycle is the remedy).
3. **5-baud 0x33** after another W5: ``55 KW1 KW2``, ``~KW2``, then the inverted address
   ``0xCC``. A missing or wrong ``~address`` is ``init-failed``; no ``55`` is ``no-ecu``.
4. **Classify** the key bytes (:mod:`.keywords`).

It never sends a manufacturer protocol (KW1281, DS2, KW82, Honda) and reads no VIN.
Running it is a *probe*: callers gate it to Parked (the server's ``detect_protocol``).
On success the returned :class:`DetectResult` holds the open link (``kline``), already
switched to the detected profile.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..transport.base import Transport
from .keywords import Classification, classify, profile_from
from .kline import KLine, KLineError, KLineTimeout, SlowInitUnconfirmed
from .profiles import BUILTIN, KLineProfile

FUNCTIONAL_OBD_ADDRESS = 0x33
OUTCOMES = ("ok", "bus-busy", "ecu-refused", "init-failed", "no-ecu")


@dataclass
class DetectResult:
    outcome: str                                # one of OUTCOMES
    profile: Optional[KLineProfile] = None      # the detected session profile (ok only)
    key_bytes: Optional[bytes] = None           # KB1 KB2 / KW1 KW2
    method: Optional[str] = None                # "fast" | "5baud"
    classification: Optional[Classification] = None
    log: "list[dict]" = field(default_factory=list)
    error: Optional[str] = None
    kline: Optional[KLine] = None               # the open link (ok only)
    since: Optional[float] = None               # epoch s of the detection

    @property
    def ok(self) -> bool:
        return self.outcome == "ok"

    @property
    def link(self) -> "dict | None":
        """The snapshot ``link`` object for this detection (``origin: "detected"``)."""
        if not self.ok or self.profile is None:
            return None
        return kline_link(self.profile, origin="detected", method=self.method,
                          key_bytes=self.key_bytes, since=self.since)


def kline_link(profile: KLineProfile, *, origin: str, method: "str | None" = None,
               key_bytes: "bytes | None" = None, since: "float | None" = None) -> dict:
    """The snapshot ``link`` object (spec §6) for a K-line link on ``profile``."""
    init = method or profile.init
    return {
        "bus": "kline",
        "profile": profile.name,
        "protocol": profile.protocol,
        "init": init,
        "origin": origin,
        "address": f"0x{profile.init_address:02x}",
        "key_bytes": bytes(key_bytes).hex(" ").upper() if key_bytes else None,
        "timing": profile.timing_set if profile.framing == "kwp2000" else None,
        "since": since,
    }


def detect(transport: Transport, *, clock: Callable[[], float] = time.monotonic,
           sleep: Callable[[float], None] = time.sleep,
           on_event: "Callable[..., None] | None" = None,
           wall: Callable[[], float] = time.time) -> DetectResult:
    """Detect the K-line protocol of the ECU at the functional OBD address (spec §2)."""
    log: "list[dict]" = []

    def ev(kind: str, **fields) -> None:
        log.append({"event": kind, **fields})
        if on_event is not None:
            try:
                on_event(kind, **fields)
            except Exception:  # noqa: BLE001 — a log hook must never break detection
                pass

    if not getattr(transport, "is_open", True):
        transport.open()
    w5 = BUILTIN["kwp2000_fast"].timing.w5

    # 1. Listen first: any byte on the line during W5 → someone else is talking.
    sleep(w5)
    try:
        rx = transport.receive(256, timeout=0.0)
    except Exception:  # noqa: BLE001 — a read error is not traffic
        rx = b""
    if rx:
        ev("listen", busy=True, rx=bytes(rx).hex(" "))
        ev("refused", reason="bus-busy")
        return DetectResult("bus-busy", log=log,
                            error="bus busy: traffic on the K-line before any init")
    ev("listen", busy=False, seconds=w5)

    # 2. KWP2000 fast init, functional to 0x33. The listen above was the W5.
    k = KLine.from_profile(transport, BUILTIN["kwp2000_fast"], init_idle=0.0,
                           clock=clock, sleep=sleep, on_event=ev)
    try:
        burst = k.fast_init_tolerant(functional=True)
    except KLineTimeout as exc:
        raw = k.last_burst
        if b"\x7f\x81" in raw:
            ev("refused", reason="ecu-refused", burst=raw.hex(" "))
            return DetectResult("ecu-refused", method="fast", log=log,
                                error="the ECU refused StartCommunication (7F 81): "
                                      "cycle the ignition before trying again")
        fast_error = str(exc)
    except KLineError as exc:  # the transport cannot do fast init: go on to 5-baud
        fast_error = str(exc)
    else:
        kb = bytes(burst[1:3])
        if len(kb) == 2:
            c = classify(kb[0], kb[1], "fast")
        else:  # C1 without key bytes: KWP2000 with the defaults
            c = Classification(profile="kwp2000_fast", protocol="kwp2000",
                               header="functional", length="format", timing_set="normal",
                               bits={}, odd="odd key bytes: missing after C1")
            kb = None
        return _found(k, c, kb, "fast", log, ev, wall)

    # 3. 5-baud 0x33, after another W5.
    ev("fast-init-silent", error=fast_error)
    sleep(w5)
    k = KLine.from_profile(transport, BUILTIN["kwp2000_slow"], init_idle=0.0,
                           clock=clock, sleep=sleep, on_event=ev)
    try:
        reply = k.slow_init_reply(FUNCTIONAL_OBD_ADDRESS)
    except SlowInitUnconfirmed as exc:
        return DetectResult("init-failed", method="5baud", log=log, error=str(exc))
    except KLineTimeout as exc:
        return DetectResult("no-ecu", method="5baud", log=log,
                            error=f"no ECU answered fast or 5-baud init ({exc})")
    except KLineError as exc:
        return DetectResult("init-failed", method="5baud", log=log, error=str(exc))
    c = classify(reply.kw1, reply.kw2, "5baud")
    return _found(k, c, bytes([reply.kw1, reply.kw2]), "5baud", log, ev, wall)


def _found(k: KLine, c: Classification, kb: "bytes | None", method: str,
           log: "list[dict]", ev, wall) -> DetectResult:
    profile = profile_from(c)   # the built-ins already target 0x33 (functional OBD)
    k.use_profile(profile)
    ev("classified", method=method, key_bytes=kb.hex(" ").upper() if kb else None,
       **c.as_log())
    return DetectResult("ok", profile=profile, key_bytes=kb, method=method,
                        classification=c, log=log, kline=k, since=wall())


__all__ = ["DetectResult", "OUTCOMES", "detect", "kline_link", "FUNCTIONAL_OBD_ADDRESS"]
