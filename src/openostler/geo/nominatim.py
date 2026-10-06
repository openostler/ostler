# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Online place-name enrichment via OSM Nominatim (ADR-0011; spec 2026-10-06-logs-at-scale §2).

``Enricher`` is one daemon thread draining one queue, within the Nominatim usage policy:
at most one request per second, a custom User-Agent, every answer cached permanently
(``cache_path``, JSON, written atomically, keyed by lat/lon rounded to 3 dp), and an
endpoint that can be turned off (``url=None`` or ``"off"``). Failures back off
exponentially from 60 s to 1 h; while offline, items wait in the queue.

Only the rounded point is sent, and only when enabled. ``fetch``, ``clock`` and ``sleep``
are injectable so tests never touch the network or the wall clock.
"""
from __future__ import annotations

import collections
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from typing import Callable, Optional

try:
    from importlib.metadata import version as _pkg_version
    _VERSION = _pkg_version("openostler")
except Exception:  # not installed (running from a checkout)
    _VERSION = "dev"

USER_AGENT = f"openostler/{_VERSION} (+https://github.com/openostler/ostler)"
DEFAULT_URL = "https://nominatim.openstreetmap.org"
TIMEOUT_S = 10
MIN_INTERVAL_S = 1.0
BACKOFF_MIN_S = 60.0
BACKOFF_MAX_S = 3600.0
_SETTLEMENT = ("city", "town", "village", "hamlet")

Callback = Callable[[str, Optional[str]], None]


def cache_key(lat: float, lon: float) -> str:
    return f"{float(lat):.3f},{float(lon):.3f}"


def label_from_address(doc: dict) -> Optional[str]:
    """Build a label from a ``format=jsonv2`` reverse answer (``None`` when it has no address)."""
    addr = (doc or {}).get("address") or {}
    area = addr.get("county") or addr.get("state")
    for key in _SETTLEMENT:
        if addr.get(key):
            return ", ".join(x for x in (addr[key], area) if x)
    parts = [x for x in (area, addr.get("country")) if x]
    return ", ".join(parts) or None


def _http_fetch(url: str, headers: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class Enricher:
    def __init__(self, url: Optional[str], cache_path: str, user_agent: str = USER_AGENT, *,
                 fetch: Optional[Callable[[str, dict, float], dict]] = None,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Optional[Callable[[float], None]] = None):
        self.url = None if url in (None, "", "off") else str(url).rstrip("/")
        self.cache_path = cache_path
        self.user_agent = user_agent
        self._fetch = fetch or _http_fetch
        self._clock = clock
        self._sleep = sleep or self._wait
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._queue: "collections.deque[tuple]" = collections.deque()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._next_at = 0.0   # earliest clock() for the next request
        self._backoff = 0.0   # current failure backoff (0 = healthy)
        self._cache = self._load_cache()

    # -- public API ---------------------------------------------------------------
    @property
    def enabled(self) -> bool:
        return self.url is not None

    def start(self) -> "Enricher":
        if self.enabled and self._thread is None:
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="geo-enricher", daemon=True)
            self._thread.start()
        return self

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        with self._cv:
            self._cv.notify_all()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None

    def cached(self, lat: float, lon: float) -> Optional[str]:
        with self._lock:
            return self._cache.get(cache_key(lat, lon))

    def submit(self, key: str, lat: float, lon: float, callback: Callback) -> None:
        """Resolve ``(lat, lon)`` and call ``callback(key, label_or_None)``: at once on a cache
        hit or when disabled, else later from the worker thread."""
        ck = cache_key(lat, lon)
        with self._lock:
            hit = ck in self._cache
            label = self._cache.get(ck)
            if not hit and self.enabled:
                self._queue.append((key, float(lat), float(lon), callback))
                self._cv.notify()
                return
        _safe_call(callback, key, label)

    def pending(self) -> int:
        with self._lock:
            return len(self._queue)

    # -- worker -------------------------------------------------------------------
    def _wait(self, seconds: float) -> None:
        self._stop.wait(max(0.0, seconds))

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._cv:
                while not self._queue and not self._stop.is_set():
                    self._cv.wait(1.0)
            if self._stop.is_set():
                return
            self.step()

    def step(self) -> bool:
        """Process the head of the queue once (waiting for the rate limit / backoff first).
        Returns True when an item was resolved, False when it failed and stays queued or
        the queue was empty."""
        with self._lock:
            if not self._queue:
                return False
            key, lat, lon, cb = self._queue[0]
            ck = cache_key(lat, lon)
            if ck in self._cache:  # resolved meanwhile (a duplicate point)
                self._queue.popleft()
                label = self._cache[ck]
                hit = True
            else:
                hit = False
        if hit:
            _safe_call(cb, key, label)
            return True

        delay = self._next_at - self._clock()
        if delay > 0:
            self._sleep(delay)
            if self._stop.is_set():
                return False
        qlat, qlon = ck.split(",")
        query = urllib.parse.urlencode({"format": "jsonv2", "lat": qlat, "lon": qlon,
                                        "zoom": 10, "addressdetails": 1})
        try:
            doc = self._fetch(f"{self.url}/reverse?{query}",
                              {"User-Agent": self.user_agent, "Accept": "application/json"},
                              TIMEOUT_S)
            label = label_from_address(doc if isinstance(doc, dict) else {})
        except Exception:
            self._backoff = min(BACKOFF_MAX_S, max(BACKOFF_MIN_S, self._backoff * 2))
            self._next_at = self._clock() + self._backoff
            return False
        self._backoff = 0.0
        self._next_at = self._clock() + MIN_INTERVAL_S
        with self._lock:
            self._cache[ck] = label
            # Drain every queued item for the same rounded point.
            done = [it for it in self._queue if cache_key(it[1], it[2]) == ck]
            self._queue = collections.deque(it for it in self._queue if cache_key(it[1], it[2]) != ck)
            snapshot = dict(self._cache)
        self._save_cache(snapshot)
        for k, _, _, c in done:
            _safe_call(c, k, label)
        return True

    @property
    def backoff_s(self) -> float:
        return self._backoff

    # -- cache --------------------------------------------------------------------
    def _load_cache(self) -> dict:
        try:
            with open(self.cache_path, encoding="utf-8") as fh:
                data = json.load(fh)
            return {str(k): (v if isinstance(v, str) else None) for k, v in data.items()} \
                if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_cache(self, data: dict) -> None:
        try:
            folder = os.path.dirname(os.path.abspath(self.cache_path))
            os.makedirs(folder, exist_ok=True)
            tmp = f"{self.cache_path}.{os.getpid()}.{threading.get_ident()}.tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, sort_keys=True, indent=0)
            os.replace(tmp, self.cache_path)
        except OSError:
            pass  # the in-memory cache still serves this run


def _safe_call(cb: Callback, key: str, label: Optional[str]) -> None:
    try:
        cb(key, label)
    except Exception:
        pass  # a consumer bug must not kill the worker
