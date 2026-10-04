"""Read side of the logbook: list, meta, columnar replay data, delete, export (ADR-0009).

``SessionStore(root, demo_root=DEMO_ROOT)`` merges the recorded sessions under ``root``
with the committed synthetic demo session(s). ``public=True`` hides every non-synthetic
session (``KeyError`` as if unknown). Demo and synthetic sessions cannot be deleted.
"""
from __future__ import annotations

import csv
import math
import os
import re
import shutil
import time

from . import channels as ch
from . import export as _export
from .demo import DEMO_ROOT
from .recorder import MIN_FREE_BYTES, _read_meta, parse_header, rotate_sessions

_SAFE_ID = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,63}$")
MAX_TRACK = 5000
LIVE_GRACE_S = 90.0  # a "recording" meta newer than this is the live session

_EXPORTS = {
    "csv": (_export.to_csv, "text/csv; charset=utf-8", "csv"),
    "vbo": (_export.to_vbo, "text/plain; charset=utf-8", "vbo"),
    "gpx": (_export.to_gpx, "application/gpx+xml", "gpx"),
}


# ------------------------------------------------------------------ reading -- #

def _num(cell: str) -> "float | int | None":
    if cell == "":
        return None
    try:
        f = float(cell)
    except ValueError:
        return None
    if not math.isfinite(f):
        return None
    return int(f) if f.is_integer() and "." not in cell else f


def read_part(path: str) -> "tuple[list[tuple[str, str, float]], list[dict]]":
    """One CSV part → (header cells, rows as dicts). A last line without its newline
    (truncated by a power cut) and any row with the wrong cell count are ignored."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
    except OSError:
        return [], []
    if not text:
        return [], []
    lines = text.split("\n")
    if not text.endswith("\n"):
        lines = lines[:-1]  # truncated last line
    if not lines:
        return [], []
    header = parse_header(lines[0])
    names = [h[0] for h in header]
    rows: "list[dict]" = []
    body = [ln for ln in lines[1:] if ln]
    for cells in csv.reader(body):
        if len(cells) != len(names):
            continue
        r: dict = {}
        ok = True
        for name, cell in zip(names, cells):
            if cell == "":
                continue
            if name in ch.TEXT_CHANNELS:
                r[name] = cell
                continue
            v = _num(cell)
            if v is None:
                ok = False
                break
            r[name] = v
        if ok and "Interval" in r:
            rows.append(r)
    return header, rows


def _part_paths(path: str, meta: dict) -> "list[str]":
    parts = [p for p in meta.get("parts") or [] if isinstance(p, str)
             and re.match(r"^data(-[0-9]+)?\.csv$", p)]
    if parts and all(os.path.exists(os.path.join(path, p)) for p in parts):
        return [os.path.join(path, p) for p in parts]
    found = [f for f in os.listdir(path) if re.match(r"^data(-[0-9]+)?\.csv$", f)]
    found.sort(key=lambda f: -1 if f == "data.csv" else int(f[5:-4]))
    return [os.path.join(path, f) for f in found]


def read_rows(path: str, meta: dict) -> "tuple[list[tuple[str, str, float]], list[dict]]":
    """All parts of a session directory → (union of header cells, rows in order)."""
    cols: "list[tuple[str, str, float]]" = []
    seen: "set[str]" = set()
    rows: "list[dict]" = []
    for p in _part_paths(path, meta):
        header, part_rows = read_part(p)
        for h in header:
            if h[0] not in seen:
                seen.add(h[0])
                cols.append(h)
        rows.extend(part_rows)
    return cols, rows


# --------------------------------------------------------------- reduction -- #

def rdp(points: "list[list[float]]", epsilon: float) -> "list[list[float]]":
    """Ramer–Douglas–Peucker over ``[lon, lat, t]`` (planar, lon scaled by cos(lat)).
    Iterative, so long tracks never hit the recursion limit."""
    n = len(points)
    if n < 3 or epsilon <= 0:
        return list(points)
    k = math.cos(math.radians(sum(p[1] for p in points) / n))
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = points[a][0] * k, points[a][1]
        bx, by = points[b][0] * k, points[b][1]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        best, idx = -1.0, -1
        for i in range(a + 1, b):
            px, py = points[i][0] * k, points[i][1]
            if norm == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * px - dx * py + bx * ay - by * ax) / norm
            if d > best:
                best, idx = d, i
        if idx >= 0 and best > epsilon:
            keep[idx] = True
            stack.append((a, idx))
            stack.append((idx, b))
    return [p for p, f in zip(points, keep) if f]


def reduce_track(points: "list[list[float]]", limit: int = MAX_TRACK) -> "list[list[float]]":
    """Every point up to ``limit``; beyond, RDP with the smallest tolerance that fits."""
    if len(points) <= limit:
        return points
    lo, hi = 0.0, 1e-3
    while len(rdp(points, hi)) > limit and hi < 10:
        hi *= 4
    best = rdp(points, hi)
    for _ in range(18):
        mid = (lo + hi) / 2
        r = rdp(points, mid)
        if len(r) > limit:
            lo = mid
        else:
            hi, best = mid, r
    return best


def _minmax_buckets(t: "list", utc: "list", cols: "dict[str, list]",
                    max_points: int) -> "tuple[list, list, dict]":
    """Reduce to ≤ ``max_points`` samples: per bucket two samples (first and last time of
    the bucket) carrying each channel's min and max in the order they occurred."""
    n = len(t)
    buckets = max(1, max_points // 2)
    out_t: list = []
    out_u: list = []
    out_c: "dict[str, list]" = {k: [] for k in cols}
    for b in range(buckets):
        lo, hi = (b * n) // buckets, ((b + 1) * n) // buckets
        if hi <= lo:
            continue
        out_t += [t[lo], t[hi - 1]]
        out_u += [utc[lo], utc[hi - 1]]
        for k, vals in cols.items():
            imin = imax = None
            for i in range(lo, hi):
                v = vals[i]
                if v is None:
                    continue
                if imin is None or v < vals[imin]:
                    imin = i
                if imax is None or v > vals[imax]:
                    imax = i
            if imin is None:
                out_c[k] += [None, None]
            else:
                first, second = sorted((imin, imax))
                out_c[k] += [vals[first], vals[second]]
    return out_t, out_u, out_c


# -------------------------------------------------------------------- store -- #

class SessionStore:
    def __init__(self, root: str, demo_root: "str | None" = DEMO_ROOT) -> None:
        self.root = str(root)
        self.demo_root = str(demo_root) if demo_root else None

    # ---- lookup ---- #

    def _dirs(self) -> "dict[str, tuple[str, bool]]":
        """id → (path, is_demo). Recorded sessions win over a demo with the same id."""
        out: "dict[str, tuple[str, bool]]" = {}
        for base, demo in ((self.demo_root, True), (self.root, False)):
            if not base or not os.path.isdir(base):
                continue
            for d in os.listdir(base):
                p = os.path.join(base, d)
                if _SAFE_ID.match(d) and os.path.isfile(os.path.join(p, "meta.json")):
                    out[d] = (p, demo)
        return out

    def _resolve(self, sid: str, public: bool) -> "tuple[str, bool, dict]":
        if not isinstance(sid, str) or not _SAFE_ID.match(sid):
            raise KeyError(sid)
        hit = self._dirs().get(sid)
        if hit is None:
            raise KeyError(sid)
        path, demo = hit
        meta = _read_meta(os.path.join(path, "meta.json"))
        if meta is None:
            raise KeyError(sid)
        if demo:
            meta = {**meta, "synthetic": True, "source": meta.get("source") or "demo",
                    "recording": False}
        if public and not meta.get("synthetic"):
            raise KeyError(sid)
        return path, demo, meta

    # ---- API ---- #

    def list(self, public: bool = False) -> "list[dict]":
        """Every session's meta, newest first; public → synthetic sessions only."""
        out = []
        for sid in self._dirs():
            try:
                out.append(self._resolve(sid, public)[2])
            except KeyError:
                continue
        out.sort(key=lambda m: (str(m.get("start_utc") or ""), str(m.get("id"))), reverse=True)
        return out

    def meta(self, sid: str, public: bool = False) -> dict:
        return self._resolve(sid, public)[2]

    def rows(self, sid: str, public: bool = False) -> "tuple[dict, list[dict]]":
        """(meta, rows as dicts) for exports and tools."""
        path, _, meta = self._resolve(sid, public)
        return meta, read_rows(path, meta)[1]

    def data(self, sid: str, channels=None, max_points: int = 2000,
             public: bool = False) -> dict:
        """Columnar replay data (spec ``/data``). ``channels``: names (list or comma
        string); default every numeric channel. Unknown channels are omitted."""
        path, _, meta = self._resolve(sid, public)
        cols, rows = read_rows(path, meta)
        numeric = [c[0] for c in cols if c[0] not in ch.TIME_CHANNELS
                   and c[0] not in ch.TEXT_CHANNELS]
        if isinstance(channels, str):
            channels = [c for c in channels.split(",") if c]
        want = numeric if not channels else [c for c in channels if c in numeric]
        t = [r["Interval"] for r in rows]
        utc = [r.get("Utc") for r in rows]
        series = {k: [r.get(k) for r in rows] for k in want}
        track = [[r["GPS_Longitude"], r["GPS_Latitude"], r["Interval"]] for r in rows
                 if r.get("GPS_Latitude") is not None and r.get("GPS_Longitude") is not None]
        max_points = max(2, int(max_points or 2000))
        decimated = len(t) > max_points
        if decimated:
            t, utc, series = _minmax_buckets(t, utc, series, max_points)
        return {"id": meta["id"], "t": t, "utc": utc, "ch": series,
                "track": reduce_track(track), "decimated": decimated}

    def delete(self, sid: str) -> None:
        """Delete a recorded session. Raises KeyError (unknown) or PermissionError (demo,
        synthetic, or the session being recorded right now)."""
        path, demo, meta = self._resolve(sid, False)
        if demo or meta.get("synthetic") or meta.get("source") == "demo":
            raise PermissionError("demo and synthetic sessions are read-only")
        if meta.get("recording"):
            try:
                age = time.time() - os.path.getmtime(os.path.join(path, "meta.json"))
            except OSError:
                age = math.inf
            if age < LIVE_GRACE_S:
                raise PermissionError("session is being recorded")
        shutil.rmtree(path)

    def export(self, sid: str, fmt: str, public: bool = False) -> "tuple[str, str, bytes]":
        """``(filename, content_type, body)`` for ``fmt`` in csv | vbo | gpx."""
        fmt = (fmt or "").lower()
        if fmt not in _EXPORTS:
            raise ValueError(f"unknown export format: {fmt!r}")
        meta, rows = self.rows(sid, public)
        fn, ctype, ext = _EXPORTS[fmt]
        return f"{meta['id']}.{ext}", ctype, fn(rows, meta).encode("utf-8")

    def rotate(self, min_free_bytes: int = MIN_FREE_BYTES, usage=shutil.disk_usage,
               keep=()) -> "list[str]":
        """Delete the oldest non-synthetic recorded sessions until ``min_free_bytes`` free."""
        return rotate_sessions(self.root, min_free_bytes, usage=usage, keep=keep)


__all__ = ["SessionStore", "read_part", "read_rows", "rdp", "reduce_track"]
