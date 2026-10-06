# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""A generic K-line link source: a profile-driven link with detection (spec §2, §6).

The building block of a pack-less K-line source (U4's ``generic_obd2`` adds J1979 on top).
It holds a :class:`~openostler.kline.profiles.KLineProfile` and its ``origin``:

* ``pack`` / ``override`` / ``detected`` / ``remembered`` → it (re-)inits that profile's
  own init only, in every driving state, with backoff 1, 2, 4, 8 … capped at 30 s;
* no profile → status ``needs-detect``: it sends nothing until the server's gated
  ``detect_protocol`` command (Parked only) runs :func:`openostler.kline.detect.detect`.

A profile confirmed by detection is remembered per ``vid``. A remembered profile whose
init fails three times, or whose key bytes differ from the stored ones (another car on the
same vid), drops the source back to ``needs-detect``; it never probes on its own.
"""
from __future__ import annotations

import time
from typing import Callable

from ..kline.detect import detect, kline_link
from ..kline.iso9141 import Iso9141Session
from ..kline.keywords import classify, profile_from
from ..kline.kline import KLine
from ..kline.memory import ProfileMemory, profile_from_entry
from ..kline.profiles import KLineProfile
from ..kwp2000.kwp2000 import KWP2000
from ..session import EcuSession
from .sources import DataSource, _transport

BACKOFF_CAP = 30.0
MAX_REMEMBERED_FAILURES = 3


class KeyBytesMismatch(Exception):
    """The ECU's key bytes differ from the remembered ones (a different car)."""


class KLineLinkSource(DataSource):
    source_kind = "kline"  # the generic K-line link source (snapshot ``source_kind``)

    def __init__(self, port: str = "auto", *, name: str = "kline",
                 profile: "KLineProfile | None" = None, origin: str = "pack",
                 transport_factory: "Callable | None" = None,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: "Callable[[float], None] | None" = None,
                 wall: Callable[[], float] = time.time,
                 backoff_cap: float = BACKOFF_CAP) -> None:
        self.name = name
        self.store_module = name
        self._port = port
        self._profile = profile
        self._origin = origin if profile is not None else None
        self._expected_kb: "bytes | None" = None
        self._key_bytes: "bytes | None" = None
        self._factory = transport_factory or self._serial
        self._clock = clock
        self._sleep_fn = sleep
        self._wall = wall
        self._backoff_cap = backoff_cap
        self._kline: "KLine | None" = None
        self._session = None
        self._since: "float | None" = None
        self._failures = 0
        self._next_try = 0.0
        self._memory: "ProfileMemory | None" = None
        self._vid: "str | None" = None
        self.on_event: "Callable[..., None] | None" = None   # the server's connection log
        self.events: "list[tuple[str, dict]]" = []           # recent link events (tests)

    # ---- wiring ---------------------------------------------------------- #
    def _serial(self, port: str, profile: "KLineProfile | None"):
        from ..ports import resolve_serial_port

        return _transport(resolve_serial_port(port), None, profile)

    def _sleep(self, seconds: float) -> None:
        if self._sleep_fn is not None:
            self._sleep_fn(seconds)
        else:
            (self.on_sleep or time.sleep)(seconds)

    def _event(self, kind: str, **fields) -> None:
        self.events.append((kind, fields))
        del self.events[:-200]
        if self.on_event is not None:
            try:
                self.on_event(kind, **fields)
            except Exception:  # noqa: BLE001
                pass

    def attach_memory(self, memory: ProfileMemory, vid: str) -> None:
        """Remember detections under ``vid``; with no pack or override profile, start from
        a remembered one (``origin: "remembered"``)."""
        self._memory, self._vid = memory, vid
        if self._profile is not None:
            return
        entry = memory.get(vid)
        if entry is None:
            return
        profile, kb = profile_from_entry(entry)
        self._profile, self._origin, self._expected_kb = profile, "remembered", kb
        self._event("remembered", profile=profile.name, key_bytes=entry.get("key_bytes"))

    def set_override(self, profile: KLineProfile) -> None:
        """``--kline-profile NAME``: use this profile for the process (``origin: override``)."""
        self._release()
        self._profile, self._origin, self._expected_kb = profile, "override", None
        self._failures, self._next_try = 0, 0.0

    @property
    def needs_detect(self) -> bool:
        return self._profile is None

    @property
    def origin(self) -> "str | None":
        return self._origin

    def is_connected(self) -> bool:
        return self._session is not None

    def set_port(self, spec: str) -> None:
        self._release()
        self._port = spec

    def kline_link(self) -> "dict | None":
        """The snapshot ``link`` (null while there is no open link)."""
        if self._session is None or self._profile is None or self._origin is None:
            return None
        return kline_link(self._profile, origin=self._origin, method=self._profile.init,
                          key_bytes=self._key_bytes, since=self._since)

    # ---- link lifecycle --------------------------------------------------- #
    def _ensure_kline(self) -> KLine:
        assert self._profile is not None
        if self._kline is None:
            t = self._factory(self._port, self._profile)
            k = KLine.from_profile(t, self._profile, clock=self._clock, sleep=self._sleep,
                                   on_event=self._event)
            k.open()
            self._kline = k
        else:
            self._kline.use_profile(self._profile)
        return self._kline

    def _open_session(self) -> None:
        p = self._profile
        assert p is not None
        k = self._ensure_kline()
        kb: "bytes | None" = None
        if p.framing == "iso9141":
            reply = k.slow_init_reply()
            kb = bytes([reply.kw1, reply.kw2])
            session = Iso9141Session(k)
        else:
            kwp = KWP2000.from_profile(k, p)
            session = EcuSession(kwp, p)
            if p.init == "fast":
                target = p.init_address if p.init_address != p.target else None
                burst = kwp.start_communication(tolerant=True, functional=p.init_functional,
                                                target=target)
                kb = bytes(burst[1:3]) if len(burst) >= 3 else None
            elif p.init == "5baud":
                reply = k.slow_init_reply()
                kb = bytes([reply.kw1, reply.kw2])
        if (p.framing == "kwp2000" and "auto" in (p.header, p.length) and kb is not None
                and len(kb) == 2 and p.init != "none"):
            # "auto": the header, length and timing set come from the key bytes.
            p = profile_from(classify(kb[0], kb[1], "fast" if p.init == "fast" else "5baud"), p)
            self._profile = p
            k.use_profile(p)
            session = EcuSession(KWP2000.from_profile(k, p), p)
        if self._expected_kb is not None and kb != self._expected_kb:
            self._session = session
            self._release()
            raise KeyBytesMismatch(
                f"key bytes {kb.hex(' ').upper() if kb else 'none'} differ from the "
                f"remembered {self._expected_kb.hex(' ').upper()}: a different car?")
        self._session, self._key_bytes = session, kb
        self._since = self._wall()
        self._failures, self._next_try = 0, 0.0
        self._event("connected", profile=p.name, origin=self._origin,
                    key_bytes=kb.hex(" ").upper() if kb else None)

    def _fail(self, exc: Exception) -> None:
        self._failures += 1
        delay = min(self._backoff_cap, 2.0 ** (self._failures - 1))
        self._next_try = self._clock() + delay
        self._event("init-failed", error=f"{type(exc).__name__}: {exc}",
                    failures=self._failures, backoff=delay)
        if self._origin == "remembered" and self._failures >= MAX_REMEMBERED_FAILURES:
            self._event("needs-detect",
                        reason=f"remembered profile failed {self._failures} times")
            self._drop_link()
            self._profile, self._origin, self._expected_kb = None, None, None
            self._failures, self._next_try = 0, 0.0

    def _release(self) -> None:
        """End the session (KWP: ``82``; ISO 9141: nothing, the session is abandoned)."""
        s = self._session
        self._session = None
        if s is None:
            return
        try:
            if isinstance(s, EcuSession):
                s.end_session()
            else:
                s.release()
        except Exception:  # noqa: BLE001 — best effort on a dying link
            pass

    def _drop_link(self) -> None:
        self._release()
        k, self._kline = self._kline, None
        if k is not None:
            try:
                k.close()
            except Exception:  # noqa: BLE001
                pass

    def disconnect(self) -> None:
        self._drop_link()

    # ---- DataSource ------------------------------------------------------- #
    def _snap(self, status: str, error: "str | None" = None) -> dict:
        out = {"status": status, "source": self.name, "signals": {}, "faults": [],
               "link": self.kline_link()}
        if error:
            out["error"] = error
        return out

    def poll(self) -> dict:
        if self._profile is None:
            return self._snap("needs-detect", "no K-line profile for this car: run protocol "
                                              "detection while parked")
        if self._session is None:
            wait = self._next_try - self._clock()
            if wait > 0:
                return self._snap("connecting", f"re-init in {wait:.0f} s")
            try:
                self._open_session()
            except Exception as exc:  # noqa: BLE001
                if "ConnectAborted" in type(exc).__name__:
                    raise
                self._fail(exc)
                if self._profile is None:
                    return self._snap("needs-detect", f"{type(exc).__name__}: {exc}")
                return self._snap("error", f"{type(exc).__name__}: {exc}")
        self.tick()
        return self._snap("connected")

    def tick(self) -> None:
        """Keep-alive between polls (the server calls it); never raises."""
        s = self._session
        if s is None:
            return
        try:
            s.keepalive_if_due()
        except Exception:  # noqa: BLE001
            pass

    def detect_protocol(self, params: "dict | None" = None) -> dict:
        """Run detection (the server has checked the Parked gate). On success the link
        stays open on the detected profile, which is remembered for this vid."""
        self._drop_link()
        try:
            t = self._factory(self._port, None)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "outcome": "init-failed", "error": f"{type(exc).__name__}: {exc}"}
        res = detect(t, clock=self._clock, sleep=self._sleep, on_event=self._event,
                     wall=self._wall)
        if not res.ok:
            try:
                t.close()
            except Exception:  # noqa: BLE001
                pass
            return {"ok": False, "outcome": res.outcome, "error": res.error}
        p = res.profile
        assert p is not None and res.kline is not None
        self._kline = res.kline
        self._profile, self._origin, self._expected_kb = p, "detected", None
        self._key_bytes, self._since = res.key_bytes, res.since
        self._failures, self._next_try = 0, 0.0
        if p.framing == "iso9141":
            self._session = Iso9141Session(res.kline)
        else:
            self._session = EcuSession(KWP2000.from_profile(res.kline, p), p)
        if self._memory is not None and self._vid:
            try:
                self._memory.put(self._vid, p, res.key_bytes, when=res.since)
            except (OSError, ValueError) as exc:
                self._event("remember-failed", error=f"{type(exc).__name__}: {exc}")
        return {"ok": True, "outcome": "ok", "link": self.kline_link(),
                "message": f"detected {p.name}"}


__all__ = ["KLineLinkSource", "KeyBytesMismatch"]
