"""SQLite session index (spec 2026-10-06-logs-at-scale §3). Core: never imports web.

Contract:
* ``SessionIndex(db_path, store)``: ``sync(sid)``, ``remove(sid)``, ``rebuild()``,
  ``page(limit=50, before=None, q=None, frm=None, to=None, module=None, has_notes=False,
  min_km=None, public=False) -> {"sessions": [meta], "next": cursor | None}``,
  ``histogram(group="month", year=None, public=False) -> {"group", "buckets": [{key, count, km}]}``.
  Keyset order: start_ms DESC, id DESC; cursor "<start_ms>:<id>". FTS5 when available, else LIKE.
  WAL + synchronous=NORMAL; rebuilt from meta.json files when missing or schema changes.

Details:
* The index is a cache of the store: ``meta_json`` holds ``SessionStore.meta(sid)`` (with
  ``note_count``), so a page never touches the session directories. ``reconcile()`` (run on
  open and at most every ``reconcile_s`` seconds by ``page``/``histogram``) picks up
  sessions added, changed or deleted behind the store's back (e.g. disk rotation).
* ``q`` is split into words; every word must prefix-match (FTS5) or substring-match
  (``LIKE``) one of name, description, place, place_end or the note texts.
* ``before`` is a cursor ``"<start_ms>:<id>"``, a bare ``"<start_ms>"`` or an ISO date or
  datetime (the scrubber's "end of that month"): sessions strictly older are returned.
  ``frm``/``to`` are ISO dates (UTC days, both inclusive) or datetimes. ``module`` matches
  a module id or a legacy alias of it (both canonicalised by the vehicle pack; rows store
  canonical ids). Bad values raise ``ValueError``.
* ``histogram`` buckets are newest first; ``group="day"`` with ``year`` keeps that year.
  It accepts the same filters as ``page`` (keyword arguments).
* Thread-safe: one connection guarded by a lock (``check_same_thread=False``).
"""
from __future__ import annotations

import calendar
import json
import os
import re
import sqlite3
import threading
import time

SCHEMA_VERSION = 2   # 2: module ids stored canonical (legacy aliases normalised)
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
RECONCILE_S = 60.0
_WORD = re.compile(r"\w+", re.UNICODE)
_COLS = ("id", "start_ms", "end_ms", "duration_s", "distance_km", "max_speed_kmh", "modules",
         "place", "place_end", "name", "description", "note_count", "has_gps", "synthetic",
         "recording", "notes", "sig", "meta_json")
_FTS_COLS = ("name", "description", "place", "place_end", "notes")


def _canonical(mid: str) -> str:
    """A module id or legacy alias → the active vehicle pack's canonical id."""
    from ..pack import canonical_module

    return canonical_module(mid) or mid


def _canonical_modules(mods) -> "list[str]":
    """``meta.modules`` with every id canonical, de-duplicated, order kept."""
    out: "list[str]" = []
    for m in mods or []:
        c = _canonical(str(m))
        if c not in out:
            out.append(c)
    return out


def _iso_ms(s) -> "int | None":
    """``2026-10-05T09:00:00.000Z`` (or a prefix down to a date) → epoch ms."""
    if not isinstance(s, str) or len(s) < 10:
        return None
    s = s.strip()
    try:
        if len(s) == 10:
            return calendar.timegm(time.strptime(s, "%Y-%m-%d")) * 1000
        base = calendar.timegm(time.strptime(s[:19].replace(" ", "T"), "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None
    ms = 0
    m = re.match(r"\.(\d{1,3})", s[19:])
    if m:
        ms = int(m.group(1).ljust(3, "0"))
    return base * 1000 + ms


def _date_bound(v, end: bool) -> "int | None":
    """An ISO date/datetime filter bound → epoch ms; ``to`` dates include the whole day."""
    if v is None or v == "":
        return None
    ms = _iso_ms(str(v))
    if ms is None:
        raise ValueError(f"bad date: {v!r}")
    if end and len(str(v).strip()) == 10:
        return ms + 86_400_000  # exclusive
    return ms + (1 if end else 0)


def _parse_before(before) -> "tuple[int, str] | None":
    if before is None or before == "":
        return None
    b = str(before).strip()
    m = re.fullmatch(r"(-?\d+)(?::(.*))?", b)
    if m:
        return int(m.group(1)), m.group(2) or ""
    ms = _iso_ms(b)
    if ms is None:
        raise ValueError(f"bad cursor: {before!r}")
    return ms, ""


def _truthy(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() not in ("", "0", "false", "no", "off")
    return bool(v)


def _place_label(p) -> "str | None":
    return str(p["label"]) if isinstance(p, dict) and p.get("label") else None


def _fts_query(words: "list[str]") -> str:
    return " ".join('"' + w.replace('"', '""') + '"*' for w in words)


def _like(w: str) -> str:
    return "%" + w.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


class SessionIndex:
    def __init__(self, db_path: str, store, reconcile_s: float = RECONCILE_S) -> None:
        self.db_path = str(db_path)
        self.store = store
        self.reconcile_s = reconcile_s
        self._lock = threading.RLock()
        self._last_reconcile = -1e18
        self.fts = False
        self._db = self._open()

    # ---- setup ---- #

    @staticmethod
    def _fts_available() -> bool:
        try:
            c = sqlite3.connect(":memory:")
            c.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
            c.close()
            return True
        except sqlite3.Error:
            return False

    def _connect(self) -> sqlite3.Connection:
        d = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(d, exist_ok=True)
        db = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        return db

    def _open(self) -> sqlite3.Connection:
        fts = self._fts_available()
        existed = os.path.exists(self.db_path)
        try:
            db = self._connect()
            ver = db.execute("PRAGMA user_version").fetchone()[0]
            has_fts = db.execute("SELECT count(*) FROM sqlite_master WHERE name="
                                 "'sessions_fts'").fetchone()[0] > 0
        except sqlite3.DatabaseError:  # corrupt: start over
            for suffix in ("", "-wal", "-shm"):
                try:
                    os.remove(self.db_path + suffix)
                except OSError:
                    pass
            db, ver, has_fts, existed = self._connect(), 0, False, False
        self.fts = fts
        with self._lock:
            self._db = db
            if not existed or ver != SCHEMA_VERSION or has_fts != fts:
                self._create()
                self.rebuild()
            else:
                self.reconcile()
        return db

    def _create(self) -> None:
        db = self._db
        db.execute("DROP TABLE IF EXISTS sessions")
        db.execute("DROP TABLE IF EXISTS sessions_fts")
        db.execute(
            "CREATE TABLE sessions (id TEXT PRIMARY KEY, start_ms INTEGER NOT NULL, "
            "end_ms INTEGER, duration_s REAL, distance_km REAL, max_speed_kmh REAL, "
            "modules TEXT, place TEXT, place_end TEXT, name TEXT, description TEXT, "
            "note_count INTEGER NOT NULL DEFAULT 0, has_gps INTEGER, synthetic INTEGER, "
            "recording INTEGER, notes TEXT, sig TEXT, meta_json TEXT NOT NULL)")
        db.execute("CREATE INDEX sessions_order ON sessions (start_ms DESC, id DESC)")
        db.execute("CREATE INDEX sessions_public ON sessions "
                   "(synthetic, start_ms DESC, id DESC)")
        if self.fts:
            db.execute("CREATE VIRTUAL TABLE sessions_fts USING fts5(id UNINDEXED, name, "
                       "description, place, place_end, notes, "
                       "tokenize='unicode61 remove_diacritics 2')")
        db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

    def close(self) -> None:
        with self._lock:
            try:
                self._db.close()
            except sqlite3.Error:
                pass

    # ---- writing ---- #

    @staticmethod
    def _sig(path: str) -> str:
        out = []
        for f in ("meta.json", "notes.jsonl"):
            try:
                st = os.stat(os.path.join(path, f))
                out.append(f"{st.st_mtime_ns}/{st.st_size}")
            except OSError:
                out.append("-")
        return ":".join(out)

    def _row(self, sid: str) -> "tuple | None":
        try:
            self.store.ensure_places(sid)
        except Exception:  # noqa: BLE001 — place names are best-effort
            pass
        try:
            meta = self.store.meta(sid)
            notes = self.store.notes(sid)
        except KeyError:
            return None
        hit = self.store._locate(sid)
        sig = self._sig(hit[0]) if hit else ""
        start = _iso_ms(meta.get("start_utc"))
        if start is None:
            return None
        modules = _canonical_modules(meta.get("modules"))
        meta = {**meta, "modules": modules} if "modules" in meta else meta
        note_text = "\n".join(str(n.get("text") or "") for n in notes if n.get("text"))
        return (sid, start, _iso_ms(meta.get("end_utc")), meta.get("duration_s"),
                float(meta.get("distance_km") or 0.0), meta.get("max_speed_kmh"),
                json.dumps(modules),
                _place_label(meta.get("place")), _place_label(meta.get("place_end")),
                meta.get("name"), meta.get("description"), int(meta.get("note_count") or 0),
                int(bool(meta.get("has_gps"))), int(bool(meta.get("synthetic"))),
                int(bool(meta.get("recording"))), note_text, sig,
                json.dumps(meta, ensure_ascii=False, separators=(",", ":")))

    def _put(self, row: tuple) -> None:
        db = self._db
        db.execute(f"INSERT OR REPLACE INTO sessions ({','.join(_COLS)}) VALUES "
                   f"({','.join('?' * len(_COLS))})", row)
        if self.fts:
            db.execute("DELETE FROM sessions_fts WHERE id = ?", (row[0],))
            d = dict(zip(_COLS, row))
            db.execute("INSERT INTO sessions_fts (id, name, description, place, place_end, "
                       "notes) VALUES (?, ?, ?, ?, ?, ?)",
                       (row[0], *(d[c] or "" for c in _FTS_COLS)))

    def _delete(self, sid: str) -> None:
        self._db.execute("DELETE FROM sessions WHERE id = ?", (sid,))
        if self.fts:
            self._db.execute("DELETE FROM sessions_fts WHERE id = ?", (sid,))

    def sync(self, sid: str) -> None:
        """(Re-)index one session from the store; a session that is gone is removed."""
        row = self._row(sid)
        with self._lock:
            self._db.execute("BEGIN")
            try:
                if row is None:
                    self._delete(sid)
                else:
                    self._put(row)
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise

    def remove(self, sid: str) -> None:
        with self._lock:
            self._delete(sid)

    def rebuild(self) -> int:
        """Re-index every session from the store; returns the count."""
        rows = [r for r in (self._row(sid) for sid in self.store.session_dirs()) if r]
        with self._lock:
            db = self._db
            db.execute("BEGIN")
            try:
                db.execute("DELETE FROM sessions")
                if self.fts:
                    db.execute("DELETE FROM sessions_fts")
                for r in rows:
                    self._put(r)
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
            self._last_reconcile = time.monotonic()
        return len(rows)

    def reconcile(self) -> int:
        """Sync sessions whose files changed, appeared or vanished; returns the count."""
        disk = self.store.session_dirs()
        with self._lock:
            known = dict(self._db.execute("SELECT id, sig FROM sessions").fetchall())
        todo = [sid for sid, (path, _demo) in disk.items()
                if known.get(sid) != self._sig(path)]
        gone = [sid for sid in known if sid not in disk]
        for sid in todo:
            self.sync(sid)
        with self._lock:
            for sid in gone:
                self._delete(sid)
            self._last_reconcile = time.monotonic()
        return len(todo) + len(gone)

    def _maybe_reconcile(self) -> None:
        if time.monotonic() - self._last_reconcile >= self.reconcile_s:
            try:
                self.reconcile()
            except (OSError, sqlite3.Error):
                pass

    # ---- reading ---- #

    def _where(self, q=None, frm=None, to=None, module=None, has_notes=False, min_km=None,
               public=False) -> "tuple[list[str], list]":
        where: "list[str]" = []
        args: list = []
        if _truthy(public):
            where.append("synthetic = 1")
        lo, hi = _date_bound(frm, False), _date_bound(to, True)
        if lo is not None:
            where.append("start_ms >= ?")
            args.append(lo)
        if hi is not None:
            where.append("start_ms < ?")
            args.append(hi)
        if module:
            where.append("modules LIKE ? ESCAPE '\\'")
            args.append(_like(json.dumps(_canonical(str(module)))))
        if _truthy(has_notes):
            where.append("note_count > 0")
        if min_km not in (None, ""):
            try:
                km = float(min_km)
            except (TypeError, ValueError):
                raise ValueError(f"bad min_km: {min_km!r}") from None
            where.append("distance_km >= ?")
            args.append(km)
        words = _WORD.findall(str(q)) if q else []
        if words:
            if self.fts:
                where.append("id IN (SELECT id FROM sessions_fts WHERE sessions_fts MATCH ?)")
                args.append(_fts_query(words))
            else:
                for w in words:
                    where.append("(" + " OR ".join(f"{c} LIKE ? ESCAPE '\\'"
                                                   for c in _FTS_COLS) + ")")
                    args += [_like(w)] * len(_FTS_COLS)
        return where, args

    def page(self, limit=DEFAULT_LIMIT, before=None, q=None, frm=None, to=None, module=None,
             has_notes=False, min_km=None, public=False) -> dict:
        """One page of metas, newest first, and the cursor of the next page (or None)."""
        try:
            limit = int(limit) if limit not in (None, "") else DEFAULT_LIMIT
        except (TypeError, ValueError):
            raise ValueError(f"bad limit: {limit!r}") from None
        limit = max(1, min(MAX_LIMIT, limit))
        where, args = self._where(q, frm, to, module, has_notes, min_km, public)
        cur = _parse_before(before)
        if cur is not None:
            where.append("(start_ms < ? OR (start_ms = ? AND id < ?))")
            args += [cur[0], cur[0], cur[1]]
        sql = ("SELECT start_ms, id, meta_json FROM sessions"
               + (" WHERE " + " AND ".join(where) if where else "")
               + " ORDER BY start_ms DESC, id DESC LIMIT ?")
        self._maybe_reconcile()
        with self._lock:
            rows = self._db.execute(sql, [*args, limit + 1]).fetchall()
        more = len(rows) > limit
        rows = rows[:limit]
        nxt = f"{rows[-1][0]}:{rows[-1][1]}" if more and rows else None
        return {"sessions": [json.loads(r[2]) for r in rows], "next": nxt}

    def histogram(self, group: str = "month", year=None, public=False, **filters) -> dict:
        """Session count and km per month (``YYYY-MM``) or day (``YYYY-MM-DD``)."""
        if group not in ("month", "day"):
            raise ValueError("group must be 'month' or 'day'")
        fmt = "%Y-%m" if group == "month" else "%Y-%m-%d"
        where, args = self._where(public=public, **filters)
        if year not in (None, ""):
            try:
                y = int(year)
            except (TypeError, ValueError):
                raise ValueError(f"bad year: {year!r}") from None
            where.append("start_ms >= ? AND start_ms < ?")
            args += [calendar.timegm((y, 1, 1, 0, 0, 0)) * 1000,
                     calendar.timegm((y + 1, 1, 1, 0, 0, 0)) * 1000]
        key = f"strftime('{fmt}', start_ms / 1000, 'unixepoch')"
        sql = (f"SELECT {key} AS k, count(*), coalesce(sum(distance_km), 0) FROM sessions"
               + (" WHERE " + " AND ".join(where) if where else "")
               + " GROUP BY k ORDER BY k DESC")
        self._maybe_reconcile()
        with self._lock:
            rows = self._db.execute(sql, args).fetchall()
        return {"group": group, "buckets": [{"key": k, "count": int(n), "km": round(km, 2)}
                                            for k, n, km in rows]}

    def count(self, public=False) -> int:
        with self._lock:
            return self._db.execute("SELECT count(*) FROM sessions" + (
                " WHERE synthetic = 1" if public else "")).fetchone()[0]


__all__ = ["SessionIndex", "SCHEMA_VERSION"]
