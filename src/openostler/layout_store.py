# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The Brain's ``ui_layouts`` store (drive-modes spec §8.3, DM2). Core: stdlib only, never
imports web.

Contract:
* ``LayoutStore(db_path, clock=time.time)``: one SQLite file in the state directory
  (``<state dir>/settings.sqlite``, the settings store; never ``auth.db``). WAL +
  ``synchronous=NORMAL``, one connection behind a lock, like the session index.
* **Key:** vehicle (``vid``) × profile (a user id, or ``car`` for the head unit's kiosk
  session, accounts spec §14.7 S4) × layout class × kind (``drive_mode``, ``home``,
  ``rail``, ``strip``) × layout id. A row holds one ``ostler.layout/1`` document, stored as
  a full copy with its ``base`` reference (§8.3, Decision 3), never as a patch.
* **Resolution** (:meth:`resolve`): the profile's row → the ``car`` profile's row (the
  owner's default for this car) → the pack's document (tier 2: a ``layouts`` list in the
  pack's UI manifest) → ``generated`` (tier 1: the shell's own presets and generated
  defaults, which live in the shell, so the layout is ``None`` here). Each answer names its
  ``source``: ``user``, ``car``, ``pack`` or ``generated``.
* :meth:`put` validates with :mod:`openostler.layouts` and refuses (:class:`LayoutRejected`)
  a document that fails, that lacks ``base``, or whose ``kind``/``id`` or classes do not
  match the key. Writes bump ``rev``; the ETag is a hash of the stored document.
* **Reset and Undo reset** (§7.8): :meth:`delete` (one layout) and :meth:`reset` (every
  layout of a kind, or all) first keep what they remove as the key's single **Before
  reset** snapshot (vid × profile × class), which :meth:`undo_reset` restores for
  ``SNAPSHOT_TTL_S`` (7 days); a newer reset replaces it.
* **Held changes** (R7): :meth:`hold` keeps a write made elsewhere for a driver-facing class
  while the car is not Parked; :meth:`apply_held` runs them in order at the next Parked.
* **The selected Drive mode per display** (§8.3): :meth:`selection` / :meth:`set_selection`
  keyed by vid × profile × display id × layout class: ``{mode, faces, rotation}``.

The Park-to-edit rule (R1) and the requesting class are the server's (``web/server.py``);
this module stores what it is given.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time

from .layouts import KINDS, limits, validate_layout

SCHEMA_VERSION = 1
SNAPSHOT_TTL_S = 7 * 24 * 3600
CAR = "car"
SOURCES = ("user", "car", "pack", "generated")
# A profile is "car" or a user id (accounts spec §14.12); a display id names one screen.
PROFILE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
DISPLAY_RE = PROFILE_RE
LAYOUT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
MAX_ROTATION = 4
MAX_FACES = 3


class LayoutRejected(ValueError):
    """A write the store refuses: a stable ``rule`` code, words, and the validator's issues."""

    def __init__(self, rule: str, message: str, errors=(), warnings=()) -> None:
        super().__init__(message)
        self.rule = rule
        self.message = message
        self.errors = list(errors)
        self.warnings = list(warnings)


def layout_classes() -> "tuple[str, ...]":
    return tuple(limits()["classes"])


def driver_facing(cls: "str | None") -> bool:
    """Whether a layout class is treated as driver-facing for Park to edit: the classes
    whose faces carry a Moving section (the head units and the phone, ``moving_required``
    in ``layout_limits.json``). An unknown or missing class fails closed (True)."""
    c = limits()["classes"].get(cls or "")
    return True if c is None else bool(c["moving_required"])


def etag_of(doc: "dict | None", source: str) -> str:
    if doc is None:
        return f'"{source}"'
    blob = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return '"' + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20] + '"'


def _utc(ms: "int | None") -> "str | None":
    if ms is None:
        return None
    ms = int(ms)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def _issue(i) -> dict:
    out = {"rule": i.rule, "message": i.message}
    for k in ("cls", "face", "slot"):
        v = getattr(i, k)
        if v is not None:
            out["class" if k == "cls" else k] = v
    return out


def check_key(profile: str, cls: str, kind: "str | None" = None, lid: "str | None" = None) -> None:
    """Raise :class:`ValueError` for a malformed key part."""
    if not PROFILE_RE.match(profile or ""):
        raise ValueError(f"bad profile: {profile!r} (car or a user id)")
    if cls not in limits()["classes"]:
        raise ValueError(f"unknown layout class: {cls!r}")
    if kind is not None and kind not in KINDS:
        raise ValueError(f"unknown layout kind: {kind!r} ({', '.join(KINDS)})")
    if lid is not None and not LAYOUT_ID_RE.match(lid):
        raise ValueError(f"bad layout id: {lid!r}")


def check_document(doc: object, cls: str, kind: str, lid: str, raw_size: "int | None" = None):
    """Validate a document for the key → the validator's report; raise
    :class:`LayoutRejected` when it is refused."""
    report = validate_layout(doc, raw_size=raw_size)
    warnings = [_issue(i) for i in report.warnings]
    if not report.ok:
        errs = [_issue(i) for i in report.errors]
        raise LayoutRejected("layout_invalid", report.errors[0].message, errs, warnings)
    assert isinstance(doc, dict)
    if doc.get("kind") != kind or doc.get("id") != lid:
        raise LayoutRejected("layout_key", f"The document is {doc.get('kind')}/{doc.get('id')}, "
                             f"not {kind}/{lid}", warnings=warnings)
    if cls not in doc.get("classes", {}):
        raise LayoutRejected("layout_class", f"The document has no {cls} layout", warnings=warnings)
    base = doc.get("base")
    if not (isinstance(base, dict) and isinstance(base.get("preset"), str) and base["preset"]
            and isinstance(base.get("version"), int) and not isinstance(base["version"], bool)
            and base["version"] >= 1):
        raise LayoutRejected("base_missing", "A stored layout needs base {preset, version}: "
                             "what it was made from, the Reset target", warnings=warnings)
    return report


class LayoutStore:
    def __init__(self, db_path: str, clock=time.time) -> None:
        self.db_path = str(db_path)
        self.clock = clock
        self._lock = threading.RLock()
        self._db = self._open()

    # ---- setup ---- #
    def _connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        db = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        return db

    def _open(self) -> sqlite3.Connection:
        db = self._connect()
        ver = db.execute("PRAGMA user_version").fetchone()[0]
        if ver > SCHEMA_VERSION:
            db.close()
            raise RuntimeError(f"{self.db_path}: settings schema {ver} is newer than this "
                               f"Ostler ({SCHEMA_VERSION})")
        # User data, never a cache: tables are only ever created or migrated, not rebuilt.
        db.execute(
            "CREATE TABLE IF NOT EXISTS ui_layouts (vid TEXT NOT NULL, profile TEXT NOT NULL, "
            "cls TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL, doc TEXT NOT NULL, "
            "base_preset TEXT, base_version INTEGER, rev INTEGER NOT NULL, "
            "updated_ms INTEGER NOT NULL, PRIMARY KEY (vid, profile, cls, kind, id))")
        db.execute(
            "CREATE TABLE IF NOT EXISTS ui_layout_snapshots (vid TEXT NOT NULL, "
            "profile TEXT NOT NULL, cls TEXT NOT NULL, taken_ms INTEGER NOT NULL, "
            "scope TEXT NOT NULL, rows TEXT NOT NULL, PRIMARY KEY (vid, profile, cls))")
        db.execute(
            "CREATE TABLE IF NOT EXISTS ui_layouts_held (seq INTEGER PRIMARY KEY AUTOINCREMENT, "
            "vid TEXT NOT NULL, profile TEXT NOT NULL, cls TEXT NOT NULL, op TEXT NOT NULL, "
            "kind TEXT, id TEXT, doc TEXT, requested_ms INTEGER NOT NULL)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS ui_drive_selection (vid TEXT NOT NULL, "
            "profile TEXT NOT NULL, display TEXT NOT NULL, cls TEXT NOT NULL, "
            "state TEXT NOT NULL, updated_ms INTEGER NOT NULL, "
            "PRIMARY KEY (vid, profile, display, cls))")
        db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        return db

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def _now_ms(self) -> int:
        return int(round(self.clock() * 1000))

    # ---- reading ---- #
    def _row(self, vid: str, profile: str, cls: str, kind: str, lid: str) -> "dict | None":
        r = self._db.execute(
            "SELECT doc, rev, updated_ms FROM ui_layouts WHERE vid=? AND profile=? AND cls=? "
            "AND kind=? AND id=?", (vid, profile, cls, kind, lid)).fetchone()
        if r is None:
            return None
        return {"doc": json.loads(r[0]), "rev": r[1], "updated_ms": r[2]}

    @staticmethod
    def _pack_doc(pack_layouts, cls: str, kind: str, lid: str) -> "dict | None":
        for doc in pack_layouts or ():
            if (isinstance(doc, dict) and doc.get("kind") == kind and doc.get("id") == lid
                    and cls in (doc.get("classes") or {})):
                return doc
        return None

    def _answer(self, profile: str, source: str, found_in: "str | None", doc, row) -> dict:
        return {"source": source, "profile": found_in, "layout": doc,
                "rev": row["rev"] if row else None,
                "updated_utc": _utc(row["updated_ms"]) if row else None,
                "etag": etag_of(doc, source)}

    def resolve(self, vid: str, profile: str, cls: str, kind: str, lid: str,
                pack_layouts=()) -> dict:
        """The layout this display shows and where it came from: ``{source, profile,
        layout, rev, updated_utc, etag}`` (``layout`` is None for ``generated``)."""
        with self._lock:
            for p, source in ((profile, "user" if profile != CAR else "car"), (CAR, "car")):
                row = self._row(vid, p, cls, kind, lid)
                if row is not None:
                    return self._answer(profile, source, p, row["doc"], row)
                if p == CAR:
                    break
        doc = self._pack_doc(pack_layouts, cls, kind, lid)
        if doc is not None:
            return self._answer(profile, "pack", None, doc, None)
        return self._answer(profile, "generated", None, None, None)

    def list(self, vid: str, profile: str, cls: str, kind: "str | None" = None,
             pack_layouts=()) -> "list[dict]":
        """Every layout visible at this key, resolved: ``[{kind, id, ...resolve()}]`` in kind
        then id order. Generated defaults are not listed (the shell knows its own)."""
        keys: "set[tuple[str, str]]" = set()
        with self._lock:
            q = ("SELECT DISTINCT kind, id FROM ui_layouts WHERE vid=? AND cls=? AND "
                 "profile IN (?, ?)")
            args: list = [vid, cls, profile, CAR]
            if kind:
                q += " AND kind=?"
                args.append(kind)
            keys |= {(k, i) for k, i in self._db.execute(q, args).fetchall()}
        for doc in pack_layouts or ():
            if (isinstance(doc, dict) and cls in (doc.get("classes") or {})
                    and (not kind or doc.get("kind") == kind)):
                keys.add((doc.get("kind"), doc.get("id")))
        out = []
        for k, i in sorted(keys):
            out.append({"kind": k, "id": i, **self.resolve(vid, profile, cls, k, i, pack_layouts)})
        return out

    # ---- writing ---- #
    def put(self, vid: str, profile: str, cls: str, doc: dict, raw_size: "int | None" = None) -> dict:
        """Validate and store ``doc`` at its own kind and id → the stored row's answer
        (with the validator's ``warnings``)."""
        check_key(profile, cls)
        kind, lid = (doc.get("kind"), doc.get("id")) if isinstance(doc, dict) else (None, None)
        report = check_document(doc, cls, str(kind), str(lid), raw_size)
        self._write(vid, profile, cls, doc)
        ans = self.resolve(vid, profile, cls, kind, lid)
        ans["warnings"] = [_issue(i) for i in report.warnings]
        return ans

    def _write(self, vid: str, profile: str, cls: str, doc: dict) -> None:
        base = doc.get("base") or {}
        now = self._now_ms()
        with self._lock:
            self._db.execute(
                "INSERT INTO ui_layouts (vid, profile, cls, kind, id, doc, base_preset, "
                "base_version, rev, updated_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?) "
                "ON CONFLICT (vid, profile, cls, kind, id) DO UPDATE SET doc=excluded.doc, "
                "base_preset=excluded.base_preset, base_version=excluded.base_version, "
                "rev=ui_layouts.rev + 1, updated_ms=excluded.updated_ms",
                (vid, profile, cls, doc["kind"], doc["id"],
                 json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
                 base.get("preset"), base.get("version"), now))

    def _snapshot(self, vid: str, profile: str, cls: str, where: str, args: tuple,
                  scope: str) -> int:
        """Keep the rows a reset removes as the key's one Before reset snapshot, then
        remove them → how many. Nothing removed leaves the old snapshot as it was."""
        rows = self._db.execute(
            f"SELECT kind, id, doc, rev, updated_ms FROM ui_layouts WHERE {where}", args).fetchall()
        if not rows:
            return 0
        kept = [{"kind": k, "id": i, "doc": json.loads(d), "rev": r, "updated_ms": u}
                for k, i, d, r, u in rows]
        self._db.execute("BEGIN")
        try:
            self._db.execute(
                "INSERT OR REPLACE INTO ui_layout_snapshots (vid, profile, cls, taken_ms, "
                "scope, rows) VALUES (?, ?, ?, ?, ?, ?)",
                (vid, profile, cls, self._now_ms(), scope, json.dumps(kept, ensure_ascii=False)))
            self._db.execute(f"DELETE FROM ui_layouts WHERE {where}", args)
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise
        return len(rows)

    def delete(self, vid: str, profile: str, cls: str, kind: str, lid: str) -> bool:
        """Revert one layout to what lies beneath it (car, pack or generated: its base);
        the removed copy becomes the Before reset snapshot. False when none was stored."""
        check_key(profile, cls, kind, lid)
        with self._lock:
            return self._snapshot(
                vid, profile, cls, "vid=? AND profile=? AND cls=? AND kind=? AND id=?",
                (vid, profile, cls, kind, lid), f"{kind}/{lid}") > 0

    def reset(self, vid: str, profile: str, cls: str, kind: "str | None" = None) -> int:
        """Reset layout (§7.8): this surface (``kind``) or everything on this screen (all
        kinds) for this profile, vehicle and class → layouts removed. Presets and other
        profiles are untouched."""
        check_key(profile, cls, kind)
        where, args = "vid=? AND profile=? AND cls=?", (vid, profile, cls)
        if kind:
            where, args = where + " AND kind=?", args + (kind,)
        with self._lock:
            return self._snapshot(vid, profile, cls, where, args, kind or "all")

    def snapshot(self, vid: str, profile: str, cls: str) -> "dict | None":
        """The Before reset snapshot's summary, or None (none, or older than 7 days)."""
        with self._lock:
            r = self._db.execute(
                "SELECT taken_ms, scope, rows FROM ui_layout_snapshots WHERE vid=? AND "
                "profile=? AND cls=?", (vid, profile, cls)).fetchone()
        if r is None or self._now_ms() - r[0] > SNAPSHOT_TTL_S * 1000:
            return None
        rows = json.loads(r[2])
        return {"taken_utc": _utc(r[0]), "expires_utc": _utc(r[0] + SNAPSHOT_TTL_S * 1000),
                "scope": r[1], "layouts": [{"kind": x["kind"], "id": x["id"]} for x in rows]}

    def undo_reset(self, vid: str, profile: str, cls: str) -> int:
        """Restore the Before reset snapshot (within 7 days) over whatever is stored at
        those keys now, then drop it → layouts restored (0: nothing to undo)."""
        check_key(profile, cls)
        with self._lock:
            r = self._db.execute(
                "SELECT taken_ms, rows FROM ui_layout_snapshots WHERE vid=? AND profile=? "
                "AND cls=?", (vid, profile, cls)).fetchone()
            if r is None:
                return 0
            self._db.execute("DELETE FROM ui_layout_snapshots WHERE vid=? AND profile=? AND "
                             "cls=?", (vid, profile, cls))
            if self._now_ms() - r[0] > SNAPSHOT_TTL_S * 1000:
                return 0
            rows = json.loads(r[1])
            for x in rows:
                self._write(vid, profile, cls, x["doc"])
            return len(rows)

    def prune(self) -> int:
        """Drop snapshots older than 7 days → how many."""
        cutoff = self._now_ms() - SNAPSHOT_TTL_S * 1000
        with self._lock:
            return self._db.execute("DELETE FROM ui_layout_snapshots WHERE taken_ms < ?",
                                    (cutoff,)).rowcount

    # ---- held changes (R7) ---- #
    def hold(self, vid: str, profile: str, cls: str, op: str, kind: "str | None" = None,
             lid: "str | None" = None, doc: "dict | None" = None) -> int:
        """Keep a write for a driver-facing class until its next Parked → its sequence
        number. ``op``: ``put`` (a validated ``doc``), ``delete``, ``reset``, ``undo_reset``."""
        if op not in ("put", "delete", "reset", "undo_reset"):
            raise ValueError(f"unknown held op {op!r}")
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO ui_layouts_held (vid, profile, cls, op, kind, id, doc, "
                "requested_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (vid, profile, cls, op, kind, lid,
                 json.dumps(doc, ensure_ascii=False) if doc is not None else None,
                 self._now_ms()))
            return int(cur.lastrowid)

    def held(self, vid: str, profile: str, cls: str) -> "list[dict]":
        with self._lock:
            rows = self._db.execute(
                "SELECT seq, op, kind, id, requested_ms FROM ui_layouts_held WHERE vid=? AND "
                "profile=? AND cls=? ORDER BY seq", (vid, profile, cls)).fetchall()
        return [{"seq": s, "op": o, "kind": k, "id": i, "requested_utc": _utc(t)}
                for s, o, k, i, t in rows]

    def apply_held(self) -> int:
        """Run every held write in order (called at Parked) → how many ran. A held write
        that fails now (e.g. a newer validator) is dropped, never retried forever."""
        with self._lock:
            rows = self._db.execute(
                "SELECT seq, vid, profile, cls, op, kind, id, doc FROM ui_layouts_held "
                "ORDER BY seq").fetchall()
            n = 0
            for seq, vid, profile, cls, op, kind, lid, doc in rows:
                self._db.execute("DELETE FROM ui_layouts_held WHERE seq=?", (seq,))
                try:
                    if op == "put":
                        self.put(vid, profile, cls, json.loads(doc))
                    elif op == "delete":
                        self.delete(vid, profile, cls, kind, lid)
                    elif op == "reset":
                        self.reset(vid, profile, cls, kind)
                    else:
                        self.undo_reset(vid, profile, cls)
                    n += 1
                except (ValueError, LayoutRejected):
                    continue
            return n

    # ---- the selected Drive mode per display ---- #
    def selection(self, vid: str, profile: str, display: str, cls: str) -> "dict | None":
        """``{mode, faces, rotation, updated_utc}`` or None."""
        with self._lock:
            r = self._db.execute(
                "SELECT state, updated_ms FROM ui_drive_selection WHERE vid=? AND profile=? "
                "AND display=? AND cls=?", (vid, profile, display, cls)).fetchone()
        if r is None:
            return None
        return {**json.loads(r[0]), "updated_utc": _utc(r[1])}

    def set_selection(self, vid: str, profile: str, display: str, cls: str, state: dict) -> dict:
        """Store a checked selection (:func:`check_selection`) → :meth:`selection`."""
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO ui_drive_selection (vid, profile, display, cls, state, "
                "updated_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (vid, profile, display, cls, json.dumps(state, separators=(",", ":")),
                 self._now_ms()))
        return self.selection(vid, profile, display, cls) or {}


def check_selection(body: object) -> dict:
    """A selected-mode body ``{mode, faces?, rotation?}`` → the clean state; ValueError."""
    if not isinstance(body, dict):
        raise ValueError("body must be an object {mode, faces?, rotation?}")
    mode = body.get("mode")
    if not isinstance(mode, str) or not LAYOUT_ID_RE.match(mode):
        raise ValueError("mode must be a layout id")
    out: dict = {"mode": mode}
    faces = body.get("faces")
    if faces is not None:
        if not isinstance(faces, dict) or len(faces) > 64 or not all(
                isinstance(k, str) and LAYOUT_ID_RE.match(k) and isinstance(v, int)
                and not isinstance(v, bool) and 0 <= v < MAX_FACES for k, v in faces.items()):
            raise ValueError("faces maps a layout id to a face index 0-2")
        out["faces"] = dict(faces)
    rotation = body.get("rotation")
    if rotation is not None:
        if not (isinstance(rotation, list) and len(rotation) <= MAX_ROTATION
                and all(isinstance(x, str) and LAYOUT_ID_RE.match(x) for x in rotation)
                and len(set(rotation)) == len(rotation)):
            raise ValueError(f"rotation lists at most {MAX_ROTATION} layout ids, once each")
        out["rotation"] = list(rotation)
    return out


__all__ = ["CAR", "SCHEMA_VERSION", "SNAPSHOT_TTL_S", "SOURCES", "LayoutRejected", "LayoutStore",
           "check_document", "check_key", "check_selection", "driver_facing", "etag_of",
           "layout_classes"]
