# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GPS fix sources: a USB NMEA receiver, a mock that drives the demo loop, and a file replay.

Every source exposes ``start()``, ``stop()``, ``latest() -> Fix | None`` and ``src``.
``open_gps(spec)`` builds one from a ``--gps`` value. pyserial is imported lazily inside
``GpsReader`` so the rest of the package (and the tests) never need it.
"""
from __future__ import annotations

import glob
import os
import threading
import time
from dataclasses import replace
from typing import Callable

from .nmea import Fix, FixMerger, parse
from .route import PERIOD_S, demo_route

UBLOX_VID = 0x1546
# USB-serial bridges that are never a GPS here: the KKL cable or the ESP32 tap.
_NOT_GPS_VIDS = {0x0403, 0x10C4, 0x1A86, 0x303A, 0x067B}
_PROBE_S = 3.0  # an unrecognised ttyACM must speak valid NMEA within this long


def _usb_candidates() -> "list[tuple[str, bool]]":
    """``[(port, sure)]`` best first; ``sure`` = identified as u-blox (else must prove NMEA)."""
    out: "list[tuple[str, bool]]" = []
    seen: "set[str]" = set()

    def add(p: str, sure: bool) -> None:
        real = os.path.realpath(p)
        if real not in seen:
            seen.add(real)
            out.append((p, sure))

    for p in sorted(glob.glob("/dev/serial/by-id/*")):
        if "u-blox" in p.lower() or "ublox" in p.lower():
            add(p, True)
    skip: "set[str]" = set()
    try:
        from serial.tools import list_ports  # type: ignore[import-not-found]

        for info in list_ports.comports():
            vid = getattr(info, "vid", None)
            if vid == UBLOX_VID:
                add(info.device, True)
            elif vid in _NOT_GPS_VIDS:
                skip.add(os.path.realpath(info.device))
    except Exception:  # noqa: BLE001 — no pyserial or enumeration failed: globs suffice
        pass
    for p in sorted(glob.glob("/dev/ttyACM*")):
        if os.path.realpath(p) not in skip:
            add(p, False)
    return out


class _Base:
    src = ""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest: "Fix | None" = None
        self._stop = threading.Event()
        self._thread: "threading.Thread | None" = None

    def latest(self) -> "Fix | None":
        with self._lock:
            return self._latest

    def _set(self, fix: "Fix | None") -> None:
        if fix is not None:
            fix = replace(fix, src=self.src)
        with self._lock:
            self._latest = fix

    def start(self) -> None:  # pragma: no cover — overridden
        pass

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t is not None and t is not threading.current_thread():
            t.join(timeout=2.0)
        self._thread = None


class GpsReader(_Base):
    """A USB NMEA receiver on a daemon thread that keeps the latest merged fix.

    ``port="auto"`` probes ``/dev/serial/by-id/*u-blox*``, then pyserial's port list for
    VID ``1546``, then ``/dev/ttyACM*`` (a ttyACM that is not a known u-blox must send a
    valid NMEA sentence within 3 s). With no device ``start()`` returns quietly and
    ``latest()`` stays None. Read errors close the port and retry every 2 s.
    """

    src = "usb"

    def __init__(self, port: str = "auto", baud: int = 115200,
                 candidates: "Callable[[], list] | None" = None) -> None:
        super().__init__()
        self.port = port
        self.baud = baud
        self._candidates = candidates or _usb_candidates
        self.device: "str | None" = None

    def start(self) -> None:
        if self._thread is not None:
            return
        if self.port and self.port != "auto":
            cands = [(self.port, True)]
        else:
            try:
                cands = self._candidates()
            except Exception:  # noqa: BLE001 — never fail the server over a GPS probe
                cands = []
        if not cands:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(cands,),
                                        name="gps-reader", daemon=True)
        self._thread.start()

    def _open(self, port: str):
        import serial  # type: ignore[import-not-found]  # lazily: pyserial is optional here

        return serial.Serial(port, self.baud, timeout=0.5)

    def _run(self, cands: "list[tuple[str, bool]]") -> None:
        chosen: "str | None" = None
        if self.port and self.port != "auto":
            chosen = self.port  # an explicit port: keep retrying it even if absent now
            cands = []
        for port, sure in cands:  # pick the first that opens (and speaks NMEA if unsure)
            if self._stop.is_set():
                return
            try:
                ser = self._open(port)
            except Exception:  # noqa: BLE001
                continue
            if sure or self._speaks_nmea(ser):
                chosen = port
                self._pump(ser)
                break
            try:
                ser.close()
            except Exception:  # noqa: BLE001
                pass
        if chosen is None:
            return
        self.device = chosen
        if not cands:  # explicit port: first attempt now
            try:
                self._pump(self._open(chosen))
            except Exception:  # noqa: BLE001
                pass
        while not self._stop.wait(2.0):  # reconnect loop after a read error/unplug
            try:
                ser = self._open(chosen)
            except Exception:  # noqa: BLE001
                continue
            self._pump(ser)

    def _speaks_nmea(self, ser) -> bool:
        deadline = time.monotonic() + _PROBE_S
        while time.monotonic() < deadline and not self._stop.is_set():
            try:
                line = ser.readline()
            except Exception:  # noqa: BLE001
                return False
            if line and parse(line) is not None:
                return True
        return False

    def _pump(self, ser) -> None:
        merger = FixMerger()
        try:
            while not self._stop.is_set():
                line = ser.readline()
                if not line:
                    continue
                d = parse(line)
                if d is not None:
                    self._set(merger.feed(d, time.monotonic()))
        except Exception:  # noqa: BLE001 — unplugged or I/O error: reconnect
            pass
        finally:
            try:
                ser.close()
            except Exception:  # noqa: BLE001
                pass


class MockGps(_Base):
    """Drives the synthetic demo loop in real time, looping every lap. Deterministic:
    the fix is a pure function of the time since ``start()``. ``route(t) -> dict`` with
    lat, lon, speed_kmh, heading, alt_m (default: ``route.demo_route``)."""

    src = "mock"

    def __init__(self, route: "Callable[[float], dict] | None" = None,
                 mono: "Callable[[], float]" = time.monotonic,
                 clock: "Callable[[], float]" = time.time,
                 period_s: float = PERIOD_S) -> None:
        super().__init__()
        self.route = route or demo_route
        self._mono = mono
        self._clock = clock
        self.period_s = period_s
        self._t0: "float | None" = None

    def start(self) -> None:
        if self._t0 is None:
            self._t0 = self._mono()

    def stop(self) -> None:
        self._t0 = None

    def latest(self) -> "Fix | None":
        if self._t0 is None:
            return None
        m = self._mono()
        p = self.route((m - self._t0) % self.period_s)
        return Fix(utc_ms=int(round(self._clock() * 1000)),
                   lat=round(p["lat"], 7), lon=round(p["lon"], 7),
                   speed_kmh=round(p["speed_kmh"], 2), heading=round(p["heading"], 1),
                   alt_m=round(p.get("alt_m", 0.0), 1), sats=11, hdop=0.8, fix=True,
                   mono=m, src=self.src)


def read_fixes(path: str) -> "list[tuple[int | None, Fix]]":
    """Every merged epoch in an ``.nmea`` file as ``[(tod_ms, Fix)]`` (one per epoch, the
    complete merge of its sentences). Invalid lines are skipped."""
    merger = FixMerger()
    out: "list[tuple[int | None, Fix]]" = []
    cur_tod: "object" = object()
    with open(path, "r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            d = parse(line)
            if d is None:
                continue
            tod = d.get("tod_ms", cur_tod)
            fix = merger.feed(d, 0.0)
            if out and tod == cur_tod:
                out[-1] = (out[-1][0], fix)
            else:
                out.append((d.get("tod_ms"), fix))
                cur_tod = tod
    return out


class ReplayGps(_Base):
    """Replays an ``.nmea`` file on a daemon thread, paced by the sentence times divided
    by ``rate`` (``rate=10`` → 10× real time); loops when ``loop`` is true."""

    src = "replay"

    def __init__(self, path: str, loop: bool = True, rate: float = 1.0) -> None:
        super().__init__()
        self.path = path
        self.loop = loop
        self.rate = max(rate, 1e-6)
        self.epochs = 0  # epochs published so far (tests)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="gps-replay", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        fixes = read_fixes(self.path)
        if not fixes:
            return
        while not self._stop.is_set():
            prev_tod = None
            for tod, fix in fixes:
                if prev_tod is not None and tod is not None:
                    dt = ((tod - prev_tod) % 86_400_000) / 1000.0
                    if self._stop.wait(min(dt, 5.0) / self.rate):
                        return
                elif self._stop.is_set():
                    return
                prev_tod = tod if tod is not None else prev_tod
                self._set(replace(fix, mono=time.monotonic()))
                self.epochs += 1
            if not self.loop:
                return


def open_gps(spec: "str | None"):
    """A source for a ``--gps`` value: ``auto`` | ``none`` | ``mock`` | ``<path>``.

    ``none`` (or empty) → None. A path to an existing regular file is replayed; any other
    path is opened as a serial port. The source is not started.
    """
    s = (spec or "none").strip()
    low = s.lower()
    if low in ("none", "off", ""):
        return None
    if low == "auto":
        return GpsReader("auto")
    if low == "mock":
        return MockGps()
    if os.path.isfile(s):
        return ReplayGps(s)
    return GpsReader(s)
