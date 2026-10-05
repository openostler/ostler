"""IMU sample sources and the polling thread (ADR-0010; spec §3). Stdlib only.

``ImuReader(source, hz)`` polls ``source.read() -> (ax, ay, az)`` (m/s², specific force) on
a daemon thread and buffers ``(epoch_ms, ax, ay, az)``; the server drains it once per poll
into ``SessionRecorder.feed_accel(samples, "imu")``. ``MockImu`` is a deterministic
vehicle-aligned IMU (x forward, y left, z up) following the synthetic demo route.
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from typing import Callable

from ..gps.route import PERIOD_S, demo_route

G = 9.80665
RATES = (10, 25, 50)
last_reason: "str | None" = None


class MockImu:
    """Synthetic specific force along the mock GPS loop: x = dv/dt, y = −v·dψ/dt (left
    positive), z = g, plus a small deterministic road ripple. ``read(t=None)``: ``t`` is
    seconds into the lap (default: since construction, via ``mono``)."""

    src = "mock"
    chip = "mock"

    def __init__(self, hz: float = 25, mono: Callable[[], float] = time.monotonic) -> None:
        self.hz = hz
        self._mono = mono
        self._t0 = mono()

    def at(self, t: float) -> "tuple[float, float, float]":
        dt = 0.25
        a, b = demo_route(t - dt), demo_route(t + dt)
        v = (a["speed_kmh"] + b["speed_kmh"]) / 2 / 3.6
        lon = (b["speed_kmh"] - a["speed_kmh"]) / 3.6 / (2 * dt)
        dpsi = ((b["heading"] - a["heading"] + 180.0) % 360.0) - 180.0
        lat = -v * math.radians(dpsi) / (2 * dt) if v > 0.8 else 0.0
        ripple = 0.15 * math.sin(t * 11.0) * min(1.0, v / 10.0)
        return round(lon, 4), round(lat, 4), round(G + ripple, 4)

    def read(self, t: "float | None" = None) -> "tuple[float, float, float]":
        if t is None:
            t = (self._mono() - self._t0) % PERIOD_S
        return self.at(t)

    def close(self) -> None:
        pass


class ImuReader:
    """Polls ``source`` at ``hz`` on a daemon thread. ``drain()`` returns and clears the
    buffered samples; ``latest()`` the newest. A read error is counted and stored in
    ``error``; reading continues (the bus may recover)."""

    def __init__(self, source, hz: float = 25, clock: Callable[[], float] = time.time,
                 maxlen: int = 3000) -> None:
        self.source = source
        self.hz = float(hz)
        self._clock = clock
        self._buf: "deque[tuple[int, float, float, float]]" = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: "threading.Thread | None" = None
        self._latest: "tuple[int, float, float, float] | None" = None
        self.errors = 0
        self.error: "str | None" = None

    def set_hz(self, hz: float) -> None:
        self.hz = float(hz)

    def poll_once(self) -> "tuple[int, float, float, float] | None":
        try:
            ax, ay, az = self.source.read()
        except Exception as exc:  # noqa: BLE001
            self.errors += 1
            self.error = f"{type(exc).__name__}: {exc}"
            return None
        s = (int(round(self._clock() * 1000)), float(ax), float(ay), float(az))
        with self._lock:
            self._buf.append(s)
            self._latest = s
        return s

    def _run(self) -> None:
        nxt = time.monotonic()
        while not self._stop.is_set():
            self.poll_once()
            nxt += 1.0 / max(1.0, self.hz)
            delay = nxt - time.monotonic()
            if delay < -1.0:
                nxt = time.monotonic()
                delay = 0
            self._stop.wait(max(0.0, delay))

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="imu")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t, self._thread = self._thread, None
        if t is not None and t is not threading.current_thread():
            t.join(timeout=2.0)
        close = getattr(self.source, "close", None)
        if close:
            try:
                close()
            except Exception:  # noqa: BLE001
                pass

    def latest(self) -> "tuple[int, float, float, float] | None":
        with self._lock:
            return self._latest

    def drain(self) -> "list[tuple[int, float, float, float]]":
        with self._lock:
            out = list(self._buf)
            self._buf.clear()
        return out


def open_imu(spec: "str | None", hz: float = 25):
    """A sample source for ``--imu``: ``none`` → None; ``mock`` → ``MockImu``; ``auto`` →
    an ``Lsm6ds`` on /dev/i2c-1, or None with ``reader.last_reason`` saying why."""
    global last_reason
    s = (spec or "none").strip().lower()
    last_reason = None
    if s in ("none", "off", ""):
        last_reason = "disabled (--imu none)"
        return None
    if s == "mock":
        return MockImu(hz)
    if s == "auto":
        from .lsm6ds import Lsm6ds
        try:
            return Lsm6ds()
        except OSError as exc:
            last_reason = str(exc) or type(exc).__name__
            return None
        except Exception as exc:  # noqa: BLE001 — never fell the server over an IMU
            last_reason = f"{type(exc).__name__}: {exc}"
            return None
    last_reason = f"unknown --imu value: {spec!r} (auto | none | mock)"
    return None


__all__ = ["ImuReader", "MockImu", "open_imu", "RATES"]
