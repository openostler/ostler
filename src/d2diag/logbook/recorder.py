"""Always-on session recording (ADR-0009, specs/2026-10-05-session-logbook-design.md).

``SessionRecorder.feed(snapshot, gps)`` is called once per poll. A session opens when
``conn`` first becomes ``connected`` or GPS speed goes above 3 km/h, and ends after
``IDLE_S`` with no connected poll and GPS speed below 3 km/h (or no GPS), or on
``close()``. Each session is a directory ``<root>/<id>/`` with RaceCapture-style CSV parts
and an atomically rewritten ``meta.json``. Only ``signals``, ``faults``, ``module`` and GPS
are recorded — never the VIN or any identity read.
"""
from __future__ import annotations

import calendar
import csv
import io
import json
import math
import os
import re
import shutil
import threading
import time
from typing import Callable

from . import channels as ch

IDLE_S = 300.0          # end after this long idle
MOVING_KMH = 3.0        # GPS speed that counts as moving
FSYNC_S = 1.0           # fsync the data file at most this often
META_S = 30.0           # rewrite meta.json this often while recording
PART_S = 3600.0         # split parts hourly
GPS_MIN_S = 0.095       # GPS rows capped at 10 Hz
GPS_RATE_HZ = 10
DEFAULT_RATE_HZ = 2
MIN_FREE_BYTES = 200 * 1024 * 1024
JITTER_KMH = 1.0        # GPS segments slower than this don't add distance (stationary jitter)

# Signal names that would be identity reads: never recorded even if a source put one in.
_IDENTITY = re.compile(r"(^|_)(vin|eka|ident|identity|serial|part_?no|part_number)($|_)",
                       re.IGNORECASE)
_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z(-[0-9]+)?$")


# ---------------------------------------------------------------- helpers -- #

def fmt_num(v: float, dp: int = 6) -> str:
    """A plain decimal (no exponent, trailing zeros stripped)."""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    s = f"{v:.{dp}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def iso_utc(epoch_s: float) -> str:
    """Epoch seconds → ``2026-10-05T09:00:00.000Z``."""
    ms = int(round(epoch_s * 1000))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def header_cell(name: str, units: str, rate: int) -> str:
    return f'"{name}"|"{units}"|{rate}'


_CELL_RE = re.compile(r'"([^"]*)"\|"([^"]*)"\|([0-9.]+)')


def parse_header(line: str) -> "list[tuple[str, str, float]]":
    """A header row → ``[(name, units, rate_hz)]``."""
    return [(n, u, float(r)) for n, u, r in _CELL_RE.findall(line)]


def write_json_atomic(path: str, obj: dict) -> None:
    """Write JSON to a temp file in the same directory, fsync, then rename over ``path``."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def _read_meta(path: str) -> "dict | None":
    try:
        with open(path, "r", encoding="utf-8") as fh:
            m = json.load(fh)
        return m if isinstance(m, dict) else None
    except (OSError, ValueError):
        return None


def rotate_sessions(root: str, min_free_bytes: int = MIN_FREE_BYTES,
                    usage: Callable = shutil.disk_usage, keep=()) -> "list[str]":
    """Delete the oldest non-synthetic sessions under ``root`` until free space is at
    least ``min_free_bytes``. Sessions in ``keep`` (the one recording) are never deleted.
    Returns the deleted ids, oldest first."""
    deleted: "list[str]" = []
    if not os.path.isdir(root):
        return deleted
    ids = sorted(d for d in os.listdir(root) if _ID_RE.match(d) and d not in keep
                 and os.path.isdir(os.path.join(root, d)))
    for sid in ids:
        try:
            if usage(root).free >= min_free_bytes:
                break
        except OSError:
            break
        meta = _read_meta(os.path.join(root, sid, "meta.json")) or {}
        if meta.get("synthetic") or meta.get("source") == "demo":
            continue
        shutil.rmtree(os.path.join(root, sid), ignore_errors=True)
        deleted.append(sid)
    return deleted


def _num_value(v) -> "float | int | None":
    if isinstance(v, dict):
        v = v.get("v")
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)) and math.isfinite(v):
        return v
    return None


# ---------------------------------------------------------------- session -- #

class _Session:
    def __init__(self, sid: str, path: str, start_s: float, start_m: float) -> None:
        self.id, self.dir = sid, path
        self.start_s, self.start_m = start_s, start_m
        self.parts: "list[str]" = []
        self.fh: "io.TextIOWrapper | None" = None
        self.columns: "list[str]" = []
        self.units: "dict[str, str]" = {}
        self.signals: "list[str]" = []
        self.rows = 0
        self.part_start_m = start_m
        self.last_sync_m = -math.inf
        self.last_meta_m = start_m
        self.last_conn_m = start_m
        self.last_move_m = start_m
        self.last_fix_mono: "float | None" = None
        self.last_gps_m = -math.inf
        self.utc_offset: "float | None" = None
        self.modules: "list[str]" = []
        self.has_gps = False
        self.dist_m = 0.0
        self.max_speed: "float | None" = None
        self.bbox: "list[float] | None" = None
        self.start_pos: "list[float] | None" = None
        self.end_pos: "list[float] | None" = None
        self.last_pt: "tuple[float, float] | None" = None
        self.end_s: "float | None" = None
        self.end_m: "float | None" = None


class SessionRecorder:
    """Records every connected (or moving) period as a session under ``root``.

    ``clock`` (epoch s) and ``mono`` (monotonic s) are injectable for tests. Extra keyword
    arguments: ``source`` (default: the snapshot's ``mode``, else ``live``), ``synthetic``,
    ``poll_hz`` (header rate hint; otherwise estimated from the feed cadence, default 2),
    ``trust_clock`` (fill ``Utc`` from ``clock`` until a GPS fix gives time),
    ``min_free_bytes`` (rotation threshold; 0 disables) and ``fsync`` (the function used
    for data-file syncs).
    """

    def __init__(self, root: str, clock: Callable[[], float] = time.time,
                 mono: Callable[[], float] = time.monotonic, *, source: "str | None" = None,
                 synthetic: bool = False, poll_hz: "float | None" = None,
                 trust_clock: bool = True, min_free_bytes: int = MIN_FREE_BYTES,
                 fsync: Callable[[int], None] = os.fsync) -> None:
        self.root = str(root)
        self._clock, self._mono = clock, mono
        self.source, self.synthetic = source, synthetic
        self.poll_hz, self.trust_clock = poll_hz, trust_clock
        self.min_free_bytes = min_free_bytes
        self._fsync = fsync
        self.fsyncs = 0
        self._lock = threading.Lock()
        self._s: "_Session | None" = None
        self._src: str = source or "live"
        self._last_feed_m: "float | None" = None
        self._dt_ema: "float | None" = None
        self._recover()

    # ---- public ------------------------------------------------------- #

    def feed(self, snapshot: "dict | None", gps=None) -> None:
        """One poll: maybe open a session, write a row, maybe end it."""
        with self._lock:
            now, m = self._clock(), self._mono()
            self._note_cadence(m)
            snap = snapshot or {}
            conn = snap.get("conn")
            connected = (conn == "connected") if conn is not None else (
                snap.get("status") == "connected")
            fix = gps if (gps is not None and getattr(gps, "fix", False)
                          and gps.lat is not None and gps.lon is not None) else None
            speed = fix.speed_kmh if fix is not None else None
            s = self._s
            if s is None:
                if not (connected or (speed is not None and speed > MOVING_KMH)):
                    return
                s = self._open(now, m, snap)
            if connected:
                s.last_conn_m = m
            if speed is not None and speed >= MOVING_KMH:
                s.last_move_m = m
            self._row(s, now, m, snap if connected else None, fix)
            if m - max(s.last_conn_m, s.last_move_m) >= IDLE_S:
                self._end(s, now, m)
            elif m - s.last_meta_m >= META_S:
                self._write_meta(s, m)

    def close(self) -> None:
        """End the open session (server shutdown)."""
        with self._lock:
            if self._s is not None:
                self._end(self._s, self._clock(), self._mono())

    def status(self) -> "dict | None":
        """The snapshot ``recording`` field: ``{session, since, rows}`` or None."""
        s = self._s
        return None if s is None else {"session": s.id, "since": s.start_s, "rows": s.rows}

    # ---- internals ---------------------------------------------------- #

    def _note_cadence(self, m: float) -> None:
        if self._last_feed_m is not None:
            dt = m - self._last_feed_m
            if 0 < dt < 10:
                self._dt_ema = dt if self._dt_ema is None else 0.8 * self._dt_ema + 0.2 * dt
        self._last_feed_m = m

    def _rate(self) -> int:
        if self.poll_hz:
            return max(1, int(round(self.poll_hz)))
        if self._dt_ema:
            return max(1, min(50, int(round(1.0 / self._dt_ema))))
        return DEFAULT_RATE_HZ

    def _recover(self) -> None:
        """Mark sessions left ``recording`` by a crash as ended."""
        if not os.path.isdir(self.root):
            return
        for sid in os.listdir(self.root):
            p = os.path.join(self.root, sid, "meta.json")
            meta = _read_meta(p) if _ID_RE.match(sid) else None
            if meta and meta.get("recording"):
                meta["recording"] = False
                if not meta.get("end_utc"):
                    try:
                        start = calendar.timegm(time.strptime(meta["start_utc"][:19],
                                                              "%Y-%m-%dT%H:%M:%S"))
                        meta["end_utc"] = iso_utc(start + float(meta.get("duration_s") or 0))
                    except (KeyError, ValueError, TypeError, OverflowError):
                        pass
                try:
                    write_json_atomic(p, meta)
                except OSError:
                    pass

    def _open(self, now: float, m: float, snap: dict) -> _Session:
        os.makedirs(self.root, exist_ok=True)
        if self.min_free_bytes:
            try:
                rotate_sessions(self.root, self.min_free_bytes)
            except OSError:
                pass
        base = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
        sid, n = base, 0
        while os.path.exists(os.path.join(self.root, sid)):
            n += 1
            sid = f"{base}-{n}"
        path = os.path.join(self.root, sid)
        os.makedirs(path)
        mode = snap.get("mode")
        self._src = self.source or (mode if mode in ("mock", "live", "demo") else "live")
        s = _Session(sid, path, now, m)
        s.columns = [*ch.TIME_CHANNELS, *ch.GPS_CHANNELS, *ch.TEXT_CHANNELS]
        s.units = {c: ch.UNITS.get(c, "") for c in s.columns}
        self._new_part(s, m)
        self._s = s
        self._write_meta(s, m)
        return s

    def _part_name(self, idx: int) -> str:
        return "data.csv" if idx == 0 else f"data-{idx}.csv"

    def _new_part(self, s: _Session, m: float) -> None:
        if s.fh is not None:  # close the current part; data.csv → data-0.csv on first split
            self._sync(s, m, force=True)
            s.fh.close()
            s.fh = None
            if s.parts == ["data.csv"]:
                os.replace(os.path.join(s.dir, "data.csv"), os.path.join(s.dir, "data-0.csv"))
                s.parts = ["data-0.csv"]
        name = "data.csv" if not s.parts else f"data-{len(s.parts)}.csv"
        s.parts.append(name)
        s.fh = open(os.path.join(s.dir, name), "w", encoding="utf-8", newline="")
        rate = self._rate()
        cells = []
        for c in s.columns:
            r = (10 if c in ch.TIME_CHANNELS else GPS_RATE_HZ if c.startswith("GPS_") else rate)
            cells.append(header_cell(c, s.units.get(c, ""), r))
        s.fh.write(",".join(cells) + "\n")
        s.part_start_m = m
        s.last_sync_m = -math.inf

    def _sync(self, s: _Session, m: float, force: bool = False) -> None:
        if s.fh is None:
            return
        if force or m - s.last_sync_m >= FSYNC_S:
            s.fh.flush()
            try:
                self._fsync(s.fh.fileno())
            except OSError:
                pass
            self.fsyncs += 1
            s.last_sync_m = m

    def _row(self, s: _Session, now: float, m: float, snap: "dict | None",
             fix) -> None:
        vals: "dict[str, str]" = {}
        new_signals: "list[str]" = []
        if snap is not None:
            for name, sv in (snap.get("signals") or {}).items():
                if not isinstance(name, str) or _IDENTITY.search(name):
                    continue
                v = _num_value(sv)
                if v is None:
                    continue
                if name not in s.signals:
                    new_signals.append(name)
                    unit = sv.get("u") if isinstance(sv, dict) else None
                    s.units[name] = str(unit) if unit else ch.UNITS.get(name, "")
                vals[name] = fmt_num(v)
                if name == "speed":
                    s.max_speed = v if s.max_speed is None else max(s.max_speed, v)
            module = snap.get("module")
            if isinstance(module, str) and module:
                vals["module"] = module
                if module not in s.modules:
                    s.modules.append(module)
            faults = snap.get("faults")
            if isinstance(faults, list):
                vals["faults"] = "; ".join(str(f) for f in faults)
        if fix is not None and fix.mono != s.last_fix_mono and m - s.last_gps_m >= GPS_MIN_S:
            s.last_fix_mono, s.last_gps_m = fix.mono, m
            if fix.utc_ms is not None:
                s.utc_offset = fix.utc_ms - (fix.mono if fix.mono else m) * 1000.0
            self._gps_vals(s, fix, vals)
        if not vals:
            return
        if new_signals:
            s.signals.extend(new_signals)
            s.columns = [*ch.TIME_CHANNELS, *ch.GPS_CHANNELS, *s.signals, *ch.TEXT_CHANNELS]
        if new_signals and s.rows > 0 or m - s.part_start_m >= PART_S:
            self._new_part(s, m)
            self._write_meta(s, m)
        elif new_signals:  # nothing written yet: rewrite this part's header in place
            s.fh.seek(0)
            s.fh.truncate()
            s.parts.pop()
            fh, s.fh = s.fh, None
            fh.close()
            self._new_part(s, m)
        if s.utc_offset is not None:
            utc = str(int(round(m * 1000.0 + s.utc_offset)))
        elif self.trust_clock:
            utc = str(int(round(now * 1000.0)))
        else:
            utc = ""
        vals["Interval"] = str(int(round((m - s.start_m) * 1000.0)))
        vals["Utc"] = utc
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerow([vals.get(c, "") for c in s.columns])
        s.fh.write(buf.getvalue())
        s.rows += 1
        self._sync(s, m)

    def _gps_vals(self, s: _Session, fix, vals: dict) -> None:
        lat, lon = float(fix.lat), float(fix.lon)
        vals["GPS_Latitude"] = fmt_num(lat, 7)
        vals["GPS_Longitude"] = fmt_num(lon, 7)
        if fix.speed_kmh is not None:
            vals["GPS_Speed"] = fmt_num(fix.speed_kmh, 2)
            s.max_speed = (fix.speed_kmh if s.max_speed is None
                           else max(s.max_speed, fix.speed_kmh))
        if fix.heading is not None:
            vals["GPS_Heading"] = fmt_num(fix.heading, 1)
        if fix.alt_m is not None:
            vals["GPS_Altitude"] = fmt_num(fix.alt_m, 1)
        if fix.sats is not None:
            vals["GPS_Nsat"] = fmt_num(int(fix.sats))
        if fix.hdop is not None:
            vals["GPS_HDOP"] = fmt_num(fix.hdop, 2)
        s.has_gps = True
        if s.last_pt is not None and (fix.speed_kmh is None or fix.speed_kmh >= JITTER_KMH):
            s.dist_m += haversine_m(s.last_pt[0], s.last_pt[1], lat, lon)
        s.last_pt = (lat, lon)
        if s.bbox is None:
            s.bbox = [lon, lat, lon, lat]
        else:
            b = s.bbox
            s.bbox = [min(b[0], lon), min(b[1], lat), max(b[2], lon), max(b[3], lat)]
        pos = [round(lon, 3), round(lat, 3)]
        if s.start_pos is None:
            s.start_pos = pos
        s.end_pos = pos

    def _meta(self, s: _Session, m: float) -> dict:
        recording = s.end_s is None
        dur = (m if recording else s.end_m) - s.start_m
        numeric = [c for c in s.columns if c not in ch.TIME_CHANNELS
                   and c not in ch.TEXT_CHANNELS and (s.has_gps or not c.startswith("GPS_"))]
        return {
            "id": s.id,
            "start_utc": iso_utc(s.start_s),
            "end_utc": None if recording else iso_utc(s.end_s),
            "duration_s": int(round(max(0.0, dur))),
            "rows": s.rows,
            "parts": list(s.parts),
            "modules": list(s.modules),
            "channels": [{"name": c, "units": s.units.get(c, ""), "group": ch.group_for(c)}
                         for c in numeric],
            "has_gps": s.has_gps,
            "distance_km": round(s.dist_m / 1000.0, 2),
            "max_speed_kmh": None if s.max_speed is None else round(float(s.max_speed), 1),
            "bbox": None if s.bbox is None else [round(x, 5) for x in s.bbox],
            "start_pos": s.start_pos,
            "end_pos": s.end_pos,
            "synthetic": bool(self.synthetic),
            "recording": recording,
            "source": self._src,
        }

    def _write_meta(self, s: _Session, m: float) -> None:
        try:
            write_json_atomic(os.path.join(s.dir, "meta.json"), self._meta(s, m))
        except OSError:
            pass
        s.last_meta_m = m

    def _end(self, s: _Session, now: float, m: float) -> None:
        if s.fh is not None:
            self._sync(s, m, force=True)
            s.fh.close()
            s.fh = None
        s.end_s, s.end_m = now, m
        self._s = None
        if s.rows == 0 or (not s.signals and not s.has_gps):
            # no signal value and no GPS fix (e.g. a server restart): leave no empty session
            shutil.rmtree(s.dir, ignore_errors=True)
            return
        self._write_meta(s, m)
