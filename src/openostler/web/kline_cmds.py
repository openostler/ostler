# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The server side of K-line profiles and detection (spec K-line profiles §2, §6).

A mixin for :class:`~openostler.web.server.DiagServer` that holds:

* **the Parked gate for probing.** ``detect_protocol`` (auto-detection) and
  ``module_scan`` (an init sweep across addresses) are probes of a car whose protocol is
  not known, so they run only when Parked. Until the U2 driving state exists (interim,
  owner Q3, 2026-10-06) that means: the server was started with ``--kline-detect``, the
  request carries ``params.confirm_parked: true`` (the UI asks "Vehicle parked?"), and
  there is no evidence of motion (a GPS fix at 3 km/h or more, or a speed signal above
  0). Re-initialising a known profile is not a probe and is never gated here.
* **the remembered profile per vehicle** (``<state dir>/kline_profiles.json``, keyed by
  the U0 ``vid``, never a VIN) and the ``--kline-profile NAME`` process override, wired
  into every source that supports them (:class:`~.kline_source.KLineLinkSource`).
* **the snapshot ``link``** (null for a source with no K-line link to report).
"""
from __future__ import annotations

import time

PARKED_ONLY = "probing an unknown car is allowed only when Parked"
PROBE_COMMANDS = frozenset({"detect_protocol", "module_scan"})
GPS_MOVING_KMH = 3.0
# Snapshot signal names that carry road speed (a pack's speed signal).
SPEED_SIGNALS = ("speed", "vehicle_speed")


def _num(v) -> "float | None":
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


class KLineCommandsMixin:
    """Mixed into DiagServer; uses its ``gps``, ``latest``, ``_engine``, ``source``,
    ``_release_source``, ``_scan_port`` and ``_conn_log``."""

    _kline_detect: bool = False
    _module_scan = None

    def _init_kline(self, *, kline_detect: bool, kline_profile: "str | None",
                    state_dir: "str | None", module_scan) -> None:
        """Wire the probe flag, the process override and the remembered profiles."""
        self._kline_detect = bool(kline_detect)
        self._module_scan = module_scan
        override = None
        if kline_profile:
            from ..kline.profiles import BUILTIN

            if kline_profile not in BUILTIN:
                raise ValueError(f"--kline-profile: unknown profile {kline_profile!r} "
                                 f"(built-ins: {', '.join(sorted(BUILTIN))})")
            override = BUILTIN[kline_profile]
        memory = vid = None
        for src in self._all_sources():
            if hasattr(src, "on_event"):
                src.on_event = self._kline_event
            if override is not None and hasattr(src, "set_override"):
                src.set_override(override)
            if hasattr(src, "attach_memory"):
                if memory is None:
                    from ..kline.memory import ProfileMemory
                    from ..logbook.vehicle import local_vid, state_dir_for

                    sd = state_dir or state_dir_for(self._sessions_dir)
                    memory, vid = ProfileMemory(sd), local_vid(sd)
                src.attach_memory(memory, vid)

    def _kline_event(self, kind: str, **fields) -> None:
        """A K-line link event → one connection-log line (no payload beyond init bytes:
        detection reads no VIN)."""
        parts = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
        self._conn_log(f"kline {kind}: {parts}".rstrip())

    # ---- the Parked gate ------------------------------------------------- #
    def _motion_evidence(self) -> "str | None":
        """Why the car may be moving, or None. Unknown speed is not motion here (the
        interim gate relies on the confirmation; U2 owns the head-unit rule)."""
        fix = self._gps_fix()
        speed = _num(getattr(fix, "speed_kmh", None)) if fix is not None else None
        if speed is not None and getattr(fix, "fix", True) and speed >= GPS_MOVING_KMH:
            return f"GPS speed {speed:.0f} km/h"
        sig = (self.latest or {}).get("signals") or {}
        for name in SPEED_SIGNALS:
            v = _num((sig.get(name) or {}).get("v")) if isinstance(sig.get(name), dict) else None
            if v is not None and v > 0:
                return f"speed signal {name} = {v:g}"
        eng = self._engine
        if eng and time.monotonic() - eng.get("t", 0) < 60:
            v = _num(eng.get("speed"))
            if v is not None and v > 0:
                return f"engine speed {v:g} km/h"
        return None

    def _probe_refusal(self, params: "dict | None") -> "str | None":
        """Why a probe (``detect_protocol``, ``module_scan``) must not run now, or None."""
        if not self._kline_detect:
            return f"{PARKED_ONLY} (start the server with --kline-detect to allow it)"
        if (params or {}).get("confirm_parked") is not True:
            return f"{PARKED_ONLY}: confirm the vehicle is parked (params.confirm_parked)"
        moving = self._motion_evidence()
        if moving:
            return f"{PARKED_ONLY}: {moving}"
        return None

    def _refuse_probe(self, action: str, why: str) -> dict:
        self._conn_log(f"kline refused: {action}: {why}")
        return {"ok": False, "error": why}

    # ---- the commands (poll thread) --------------------------------------- #
    def _detect_protocol(self, params: dict) -> dict:
        why = self._probe_refusal(params)   # re-checked on the poll thread
        if why:
            return self._refuse_probe("detect_protocol", why)
        fn = getattr(self.source, "detect_protocol", None)
        if fn is None:
            return {"ok": False, "code": "bad_request",
                    "error": f"{self.source.name} has a known K-line profile; detection is "
                             "only for a car without one"}
        self._conn_log("kline detect: start (parked confirmed)")
        res = fn(params)
        self._conn_log(f"kline detect: {res.get('outcome')} {res.get('error') or ''}".rstrip())
        if res.get("ok"):
            self._restart_conn()
        return res

    def _run_module_scan(self, params: dict) -> dict:
        """A read-only init sweep (fast and 5-baud across addresses) — Parked only."""
        why = self._probe_refusal(params)
        if why:
            return self._refuse_probe("module_scan", why)
        self._release_source()
        fast = params.get("fast")
        slow = params.get("slow")
        try:
            fast = [int(a, 16) if isinstance(a, str) else int(a) for a in fast] \
                if fast is not None else None
            slow = [int(a, 16) if isinstance(a, str) else int(a) for a in slow] \
                if slow is not None else None
        except (TypeError, ValueError):
            return {"ok": False, "code": "bad_request",
                    "error": "fast/slow must be lists of addresses (hex strings or ints)"}
        scan = self._module_scan or _live_module_scan
        try:
            rows = scan(self._scan_port, fast, slow)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return {"ok": True, "scan": rows}

    def _kline_link_for(self, snap: dict) -> "dict | None":
        """The snapshot ``link``: always the active source's :meth:`kline_link` (so a
        module switch never shows the previous source's link)."""
        fn = getattr(self.source, "kline_link", None)
        if fn is None:
            return None
        try:
            return fn()
        except Exception:  # noqa: BLE001
            return None

    def _tick_source(self) -> None:
        """Between polls: let the active source send a due keep-alive (``tick()``)."""
        tick = getattr(self.source, "tick", None)
        if tick is None:
            return
        try:
            tick()
        except Exception:  # noqa: BLE001 — a keep-alive must never fell the poll loop
            pass


def _live_module_scan(port_spec: str, fast, slow) -> "list[dict]":
    """The real sweep over the K-line cable (lazy imports: pyserial)."""
    from ..kline import KLine
    from ..kwp2000 import KWP2000
    from ..modscan import AddressScanner, default_fast, default_slow
    from ..ports import resolve_serial_port
    from ..transport import SerialTransport

    port = resolve_serial_port(port_spec)
    kwp = KWP2000(KLine(SerialTransport(port, timeout=1.0)), tolerant=True)
    kwp.open()
    try:
        scanner = AddressScanner(kwp)
        return scanner.scan(default_fast() if fast is None else fast,
                            default_slow() if slow is None else slow)
    finally:
        kwp.close()


__all__ = ["KLineCommandsMixin", "PARKED_ONLY", "PROBE_COMMANDS"]
