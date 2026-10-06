# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Read side of the logbook: list, meta, columnar replay data, delete, export (ADR-0009),
plus events, notes, audio and capture labels (ADR-0010).

``SessionStore(root, demo_root=<the active pack's demo sessions>)`` merges the recorded
sessions under ``root`` with the committed synthetic demo session(s). ``public=True`` hides
every non-synthetic session (``KeyError`` as if unknown). Demo and synthetic sessions cannot be deleted, and
their notes are read-only (``PermissionError``); every note write is refused in public
mode. Audio is never available in public mode (``KeyError``).

ADR-0011 (spec 2026-10-06-logs-at-scale): ``SessionStore(root, demo_root, index_path=None)``
attaches a ``SessionIndex`` (``self.index``) that is synced on every change made through
the store (``update_meta``, ``set_place``, note writes, ``delete``) and by ``sync(sid)``,
which the recorder's ``on_change`` calls when a session opens or closes. Meta carries
``name``, ``description``, ``place_start``/``place_end``/``place`` and a computed
``note_count``.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import shutil
import time

from . import channels as ch
from . import export as _export
from .audio import mime_for, track_file
from . import demo as _demo_pkg
from . import places as _places
from .notes import NoteLog, read_notes
from .recorder import (MIN_FREE_BYTES, _read_meta, parse_header, rotate_sessions,
                       write_json_atomic)

_SAFE_ID = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,63}$")
MAX_TRACK = 5000
LIVE_GRACE_S = 90.0  # a "recording" meta newer than this is the live session
MAX_NAME = 80
MAX_DESCRIPTION = 2000
_UNSET = object()
_PACK = object()  # SessionStore default: the active vehicle pack's demo sessions
_PLACE_WHICH = {"start": "place_start", "place_start": "place_start",
                "end": "place_end", "place_end": "place_end"}

_EXPORTS = {
    "csv": (_export.to_csv, "text/csv; charset=utf-8", "csv"),
    "vbo": (_export.to_vbo, "text/plain; charset=utf-8", "vbo"),
    "gpx": (_export.to_gpx, "application/gpx+xml", "gpx"),
    "notes": (_export.notes_csv, "text/csv; charset=utf-8", "notes.csv"),
}


def _canonical(mid) -> str:
    """A module id or legacy alias (``motor``) → the active pack's canonical id. Applied
    on READ only: files on disk are never rewritten."""
    from ..pack import canonical_module

    m = str(mid or "")
    return (canonical_module(m) or m) if m else m


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
    # acceleration samples are written at their own (earlier) timestamps: restore time
    # order (stable, so rows with equal times keep their written order)
    rows.sort(key=lambda r: r["Interval"])
    return cols, rows


def read_events(path: str) -> "list[dict]":
    """``events.jsonl`` of a session directory; a truncated or malformed line is skipped."""
    try:
        with open(os.path.join(path, "events.jsonl"), "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    lines = text.split("\n")
    if not text.endswith("\n"):
        lines = lines[:-1]
    out = []
    for ln in lines:
        if not ln.strip():
            continue
        try:
            ev = json.loads(ln)
        except ValueError:
            continue
        if isinstance(ev, dict) and isinstance(ev.get("type"), str) \
                and isinstance(ev.get("t"), (int, float)):
            ev.pop("trust", None)
            if isinstance(ev.get("module"), str) and ev["module"]:
                ev["module"] = _canonical(ev["module"])   # legacy alias → canonical id
            out.append(ev)
    return out


def _complete_meta(meta: dict) -> dict:
    """Fill the ADR-0010 fields older sessions lack (channel c/limits/group, audio,
    accel_cal), so every reader sees one shape."""
    chans = []
    for c in meta.get("channels") or []:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        c = dict(c)
        name = str(c["name"])
        if "group" not in c or (ch.is_accel(name) and c.get("group") != "accel"):
            c["group"] = ch.group_for(name)
        c.setdefault("c", ch.confidence_for(name))
        c.setdefault("limits", ch.limits_for(name))
        chans.append(c)
    meta = {**meta, "channels": chans}
    if isinstance(meta.get("modules"), list):
        mods: "list" = []
        for m in meta["modules"]:
            c = _canonical(m) if isinstance(m, str) else m
            if c not in mods:
                mods.append(c)
        meta["modules"] = mods                    # legacy alias → canonical id, on read
    meta.setdefault("audio", [])
    meta.setdefault("accel_cal", None)
    meta.setdefault("name", None)
    meta.setdefault("description", None)
    for k in _places.PLACE_KEYS:
        meta.setdefault(k, None)
    return meta


def _clean_text(v, cap: int, single_line: bool) -> "str | None":
    """Trimmed text capped at ``cap`` characters; empty → None. ``ValueError`` for a
    non-string."""
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("must be a string or null")
    v = " ".join(v.split()) if single_line else v.replace("\r\n", "\n").strip()
    v = v[:cap].strip()
    return v or None


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
                    max_points: int, idx: "list | None" = None) -> "tuple[list, list, dict]":
    """Reduce to ≤ ``max_points`` samples: per bucket two samples (first and last time of
    the bucket) carrying each channel's min and max in the order they occurred. ``idx``
    (a list) receives the source row index of each output sample."""
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
        if idx is not None:
            idx += [lo, hi - 1]
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
    def __init__(self, root: str, demo_root: "str | None" = _PACK,  # type: ignore[assignment]
                 index_path: "str | None" = None) -> None:
        if demo_root is _PACK:
            demo_root = _demo_pkg.demo_root()
        self.root = str(root)
        self.demo_root = str(demo_root) if demo_root else None
        self.index = None
        if index_path:
            from .index import SessionIndex  # noqa: PLC0415 — index imports store lazily
            self.index = SessionIndex(index_path, self)

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

    def session_dirs(self) -> "dict[str, tuple[str, bool]]":
        """Every session: id → (directory, is_demo) (for the index)."""
        return self._dirs()

    def _locate(self, sid: str) -> "tuple[str, bool] | None":
        """One session's (path, is_demo) by direct lookup (no directory scan)."""
        if not isinstance(sid, str) or not _SAFE_ID.match(sid):
            return None
        for base, demo in ((self.root, False), (self.demo_root, True)):
            if base and os.path.isfile(os.path.join(base, sid, "meta.json")):
                return os.path.join(base, sid), demo
        return None

    @staticmethod
    def _load(path: str, demo: bool, public: bool, sid: str) -> dict:
        meta = _read_meta(os.path.join(path, "meta.json"))
        if meta is None:
            raise KeyError(sid)
        if demo:
            meta = {**meta, "synthetic": True, "source": meta.get("source") or "demo",
                    "recording": False}
        if public and not meta.get("synthetic"):
            raise KeyError(sid)
        meta = _complete_meta(meta)
        meta["note_count"] = len(read_notes(path))
        return meta

    def _resolve(self, sid: str, public: bool) -> "tuple[str, bool, dict]":
        hit = self._locate(sid)
        if hit is None:
            raise KeyError(sid)
        path, demo = hit
        return path, demo, self._load(path, demo, public, sid)

    def _sync(self, sid: str) -> None:
        if self.index is not None:
            try:
                self.index.sync(sid)
            except Exception:  # noqa: BLE001 — the index is a cache; never fail a write
                pass

    def sync(self, sid: str) -> None:
        """Re-index one session (missing → removed). The recorder's ``on_change``."""
        self._sync(sid)

    # ---- API ---- #

    def list(self, public: bool = False) -> "list[dict]":
        """Every session's meta, newest first; public → synthetic sessions only."""
        out = []
        for sid, (path, demo) in self._dirs().items():
            try:
                out.append(self._load(path, demo, public, sid))
            except KeyError:
                continue
        out.sort(key=lambda m: (str(m.get("start_utc") or ""), str(m.get("id"))), reverse=True)
        return out

    def meta(self, sid: str, public: bool = False) -> dict:
        return self._resolve(sid, public)[2]

    def _writable(self, sid: str, public: bool) -> "tuple[str, dict]":
        if public:
            raise PermissionError("sessions are read-only in public mode")
        path, demo, meta = self._resolve(sid, False)
        if demo or meta.get("synthetic") or meta.get("source") == "demo":
            raise PermissionError("demo and synthetic sessions are read-only")
        return path, meta

    def update_meta(self, sid: str, name=_UNSET, description=_UNSET,
                    public: bool = False) -> dict:
        """Set ``name`` (≤80 chars, whitespace collapsed) and/or ``description`` (≤2000
        chars, trimmed); empty → null; an omitted field is unchanged. Returns the new
        meta. ``KeyError`` (unknown), ``PermissionError`` (public mode, demo/synthetic),
        ``ValueError`` (not a string or null)."""
        path, _ = self._writable(sid, public)
        changes = {}
        if name is not _UNSET:
            changes["name"] = _clean_text(name, MAX_NAME, True)
        if description is not _UNSET:
            changes["description"] = _clean_text(description, MAX_DESCRIPTION, False)
        if changes:
            self._patch_meta(path, sid, changes)
            self._sync(sid)
        return self.meta(sid)

    def _patch_meta(self, path: str, sid: str, changes: dict) -> dict:
        p = os.path.join(path, "meta.json")
        raw = _read_meta(p)
        if raw is None:
            raise KeyError(sid)
        raw.update(changes)
        write_json_atomic(p, raw)
        return raw

    def set_place(self, sid: str, which: str, label: str, source: str = "osm") -> dict:
        """Enrichment hook: replace ``place_start`` (``which`` "start") or ``place_end``
        ("end") with ``{label, source, label_offline}`` (the offline label is kept) and
        recompute ``place``. Demo sessions are committed files (``PermissionError``)."""
        key = _PLACE_WHICH.get(which)
        if key is None:
            raise ValueError("which must be 'start' or 'end'")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("label must be a non-empty string")
        hit = self._locate(sid)
        if hit is None:
            raise KeyError(sid)
        path, demo = hit
        if demo:
            raise PermissionError("demo sessions are read-only")
        raw = _read_meta(os.path.join(path, "meta.json"))
        if raw is None:
            raise KeyError(sid)
        old = raw.get(key) if isinstance(raw.get(key), dict) else {}
        offline = old.get("label_offline") or (
            old.get("label") if old.get("source", "geonames") == "geonames" else None)
        new = {"label": " ".join(label.split())[:200], "source": str(source or "osm"),
               "label_offline": offline}
        raw[key] = new
        raw["place"] = _places.combined(raw)
        self._patch_meta(path, sid, {key: new, "place": raw["place"]})
        self._sync(sid)
        return self.meta(sid)

    def ensure_places(self, sid: str) -> bool:
        """Write the offline place names of a recorded session that has none yet (older
        sessions). True when the meta changed. Demo sessions carry theirs committed."""
        hit = self._locate(sid)
        if hit is None or hit[1]:
            return False
        path = hit[0]
        raw = _read_meta(os.path.join(path, "meta.json"))
        if raw is None or "place_start" in raw or raw.get("recording"):
            return False
        found = _places.places_for(raw.get("start_pos"), raw.get("end_pos"))
        if found is None:  # gazetteer unavailable: try again on a later pass
            return False
        try:
            self._patch_meta(path, sid, found)
        except OSError:
            return False
        return True

    def rows(self, sid: str, public: bool = False) -> "tuple[dict, list[dict]]":
        """(meta, rows as dicts) for exports and tools."""
        path, _, meta = self._resolve(sid, public)
        return meta, read_rows(path, meta)[1]

    def data(self, sid: str, channels=None, max_points: int = 2000,
             public: bool = False) -> dict:
        """Columnar replay data (spec ``/data``). ``channels``: names (list or comma
        string); default every numeric channel. Unknown channels are omitted. ``text`` holds
        the ``faults`` and ``module`` text channels aligned with ``t`` (the value at each
        output sample's source row; null when empty)."""
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
        src = list(range(len(t)))
        if decimated:
            src = []
            t, utc, series = _minmax_buckets(t, utc, series, max_points, src)
        text = {k: [rows[i].get(k) or None for i in src] for k in ("faults", "module")}
        text["module"] = [_canonical(m) if m else m for m in text["module"]]
        return {"id": meta["id"], "t": t, "utc": utc, "ch": series, "text": text,
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
        if self.index is not None:
            try:
                self.index.remove(sid)
            except Exception:  # noqa: BLE001
                pass

    def export(self, sid: str, fmt: str, public: bool = False) -> "tuple[str, str, bytes]":
        """``(filename, content_type, body)`` for ``fmt`` in csv | vbo | gpx | notes."""
        fmt = (fmt or "").lower()
        if fmt not in _EXPORTS:
            raise ValueError(f"unknown export format: {fmt!r}")
        path, _, meta = self._resolve(sid, public)
        notes = read_notes(path)
        fn, ctype, ext = _EXPORTS[fmt]
        if fmt == "notes":
            body = fn(notes, meta)
        else:
            body = fn(read_rows(path, meta)[1], meta, notes=notes)
        return f"{meta['id']}.{ext}", ctype, body.encode("utf-8")

    # ---- events and notes (ADR-0010) ---- #

    def events(self, sid: str, public: bool = False) -> "list[dict]":
        """The session's events stream (``GET /sessions/<id>/events``)."""
        path, _, _ = self._resolve(sid, public)
        return read_events(path)

    def notes(self, sid: str, public: bool = False) -> "list[dict]":
        """The session's notes, sorted by ``t`` (``GET /sessions/<id>/notes``)."""
        path, _, _ = self._resolve(sid, public)
        return read_notes(path)

    def _note_log(self, sid: str, public: bool) -> NoteLog:
        if public:
            raise PermissionError("notes are read-only in public mode")
        path, demo, meta = self._resolve(sid, False)
        if demo or meta.get("synthetic") or meta.get("source") == "demo":
            raise PermissionError("synthetic sessions are read-only")
        return NoteLog(path)

    def add_note(self, sid: str, t, text: str = "", tags=(), kind: str = "note",
                 source: str = "retro", t_end=None, capture=None,
                 public: bool = False) -> dict:
        """Add a note. ``KeyError`` (unknown session), ``PermissionError`` (public mode or
        a synthetic session), ``ValueError`` (bad fields)."""
        note = self._note_log(sid, public).add(t, text=text, tags=tags, kind=kind,
                                               source=source, t_end=t_end, capture=capture)
        self._sync(sid)
        return note

    def edit_note(self, sid: str, nid: str, public: bool = False, **fields) -> dict:
        """Change any of ``text, tags, t, t_end``; ``KeyError`` for an unknown note."""
        note = self._note_log(sid, public).edit(nid, **fields)
        self._sync(sid)
        return note

    def delete_note(self, sid: str, nid: str, public: bool = False) -> None:
        self._note_log(sid, public).delete(nid)
        self._sync(sid)

    # ---- audio (ADR-0010; never public) ---- #

    def audio_path(self, sid: str, track: str, public: bool = False) -> str:
        """The file of an audio track (serve it with ``audio.mime_for(path)`` and Range
        support). ``KeyError`` in public mode, for an unknown session or track."""
        if public:
            raise KeyError(track)
        path, _, _ = self._resolve(sid, False)
        f = track_file(path, track)
        if f is None:
            raise KeyError(track)
        return f

    @staticmethod
    def audio_mime(path: str) -> str:
        return mime_for(path)

    # ---- capture labels (admin) ---- #

    def captures(self, module: "str | None" = None,
                 labeled_path: "str | None" = None) -> "list[dict]":
        """Capture labels for the Decode solver: every ``capture`` note of every session
        (``t``/``session`` set) plus the rows of ``logs/labeled_captures.jsonl``
        (``labeled_path``; ``t``/``session`` null). ``module`` filters by canonical id (a
        legacy alias matches its module); rows carry canonical ids. Admin only: never call
        it for a public request."""
        def norm(m) -> str:
            return _canonical(str(m or "").lower())

        want = norm(module) if module else None
        out: "list[dict]" = []
        for sid, (path, _demo) in sorted(self._dirs().items()):
            for n in read_notes(path):
                cap = n.get("capture")
                if n.get("kind") != "capture" or not isinstance(cap, dict):
                    continue
                if want and norm(cap.get("module")) != want:
                    continue
                out.append({"module": _canonical(cap.get("module")),
                            "lid": str(cap.get("lid") or ""), "raw": str(cap.get("raw") or ""),
                            "value": str(cap.get("value") or ""), "t": n.get("t"),
                            "session": sid})
        if labeled_path:
            try:
                with open(labeled_path, "r", encoding="utf-8") as fh:
                    lines = fh.read().split("\n")
            except OSError:
                lines = []
            for ln in lines:
                try:
                    r = json.loads(ln) if ln.strip() else None
                except ValueError:
                    continue
                if not isinstance(r, dict) or not r.get("lid"):
                    continue
                if want and norm(r.get("module")) != want:
                    continue
                value = r.get("value", r.get("text"))
                out.append({"module": _canonical(r.get("module")), "lid": str(r.get("lid")),
                            "raw": str(r.get("raw") or ""),
                            "value": "" if value is None else str(value),
                            "t": None, "session": None})
        return out

    def rotate(self, min_free_bytes: int = MIN_FREE_BYTES, usage=shutil.disk_usage,
               keep=()) -> "list[str]":
        """Delete the oldest non-synthetic recorded sessions until ``min_free_bytes`` free."""
        gone = rotate_sessions(self.root, min_free_bytes, usage=usage, keep=keep)
        for sid in gone:
            self._sync(sid)
        return gone


__all__ = ["SessionStore", "read_part", "read_rows", "read_events", "rdp", "reduce_track"]
