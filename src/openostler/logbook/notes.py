# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Per-session notes (ADR-0010; spec 2026-10-05-replay-notes-capture §2). Core: never imports web.

Contract:
* ``NoteLog(session_dir)``: ``list() -> [note]`` (sorted by t, revisions resolved),
  ``add(t, text="", tags=(), kind="note", source="retro", t_end=None, capture=None) -> note``,
  ``edit(nid, **fields) -> note`` (KeyError if unknown), ``delete(nid)``.
  Storage ``notes.jsonl``: append-only revision log; the last line per id wins;
  ``{"id", "deleted": true}`` removes. Ids are 8 hex chars.
* ``read_notes(session_dir) -> [note]`` for exports.

A note is ``{id, t, t_end, text, tags, kind, source, created, edited, capture}`` (``t_end``,
``edited`` and ``capture`` are null when unset). Bad input raises ``ValueError``.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time

NOTES_FILE = "notes.jsonl"
KINDS = ("mark", "note", "capture")
SOURCES = ("live", "retro")
MAX_TEXT = 2000
MAX_TAGS = 16
_ID_RE = re.compile(r"^[0-9a-f]{8}$")
_EDITABLE = ("text", "tags", "t", "t_end")

_locks: "dict[str, threading.Lock]" = {}
_locks_guard = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(os.path.abspath(path), threading.Lock())


def _now_iso(clock=time.time) -> str:
    ms = int(round(clock() * 1000))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def _ms(v, name: str) -> int:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v < 0:
        raise ValueError(f"{name} must be a non-negative number of session ms")
    return int(round(v))


def _tags(tags) -> "list[str]":
    if tags is None:
        return []
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, (list, tuple)):
        raise ValueError("tags must be a list of strings")
    out: "list[str]" = []
    for x in tags:
        x = str(x).strip()[:32]
        if x and x not in out:
            out.append(x)
    return out[:MAX_TAGS]


def _capture(cap) -> "dict | None":
    if cap is None:
        return None
    if not isinstance(cap, dict):
        raise ValueError("capture must be an object {module, lid, raw, value}")
    return {k: "" if cap.get(k) is None else str(cap.get(k))[:200]
            for k in ("module", "lid", "raw", "value")}


def _read_lines(path: str) -> "list[dict]":
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    lines = text.split("\n")
    if not text.endswith("\n"):
        lines = lines[:-1]  # a truncated last line (power cut) is ignored
    for ln in lines:
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("id"), str):
            out.append(obj)
    return out


def _resolve(lines: "list[dict]") -> "dict[str, dict]":
    notes: "dict[str, dict]" = {}
    for obj in lines:
        if obj.get("deleted"):
            notes.pop(obj["id"], None)
        else:
            notes[obj["id"]] = obj
    return notes


def _sorted(notes) -> "list[dict]":
    return sorted(notes, key=lambda n: (n.get("t") or 0, n.get("created") or "", n["id"]))


def read_notes(session_dir: str) -> "list[dict]":
    """Every live note in ``session_dir``, sorted by ``t`` (for exports and the API)."""
    return _sorted(_resolve(_read_lines(os.path.join(session_dir, NOTES_FILE))).values())


class NoteLog:
    """The ``notes.jsonl`` revision log of one session directory."""

    def __init__(self, session_dir: str, clock=time.time, fsync=os.fsync) -> None:
        self.dir = str(session_dir)
        self.path = os.path.join(self.dir, NOTES_FILE)
        self._clock = clock
        self._fsync = fsync

    def _append(self, obj: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
            fh.flush()
            try:
                self._fsync(fh.fileno())
            except OSError:
                pass

    def _current(self) -> "dict[str, dict]":
        return _resolve(_read_lines(self.path))

    def list(self) -> "list[dict]":
        return _sorted(self._current().values())

    def get(self, nid: str) -> dict:
        note = self._current().get(nid)
        if note is None:
            raise KeyError(nid)
        return note

    def add(self, t, text: str = "", tags=(), kind: str = "note", source: str = "retro",
            t_end=None, capture=None, nid: "str | None" = None,
            created: "str | None" = None) -> dict:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {', '.join(KINDS)}")
        if source not in SOURCES:
            raise ValueError(f"source must be one of {', '.join(SOURCES)}")
        t = _ms(t, "t")
        t_end = None if t_end is None else _ms(t_end, "t_end")
        if t_end is not None and t_end < t:
            raise ValueError("t_end must not be before t")
        if nid is not None and not _ID_RE.match(nid):
            raise ValueError("note ids are 8 hex digits")
        with _lock_for(self.path):
            os.makedirs(self.dir, exist_ok=True)
            existing = self._current()
            while nid is None or nid in existing:
                nid = secrets.token_hex(4)
            note = {"id": nid, "t": t, "t_end": t_end,
                    "text": str(text or "")[:MAX_TEXT], "tags": _tags(tags), "kind": kind,
                    "source": source, "created": created or _now_iso(self._clock),
                    "edited": None,
                    "capture": _capture(capture) if kind == "capture" or capture else None}
            self._append(note)
        return note

    def edit(self, nid: str, **fields) -> dict:
        unknown = [k for k in fields if k not in _EDITABLE]
        if unknown:
            raise ValueError(f"cannot edit {', '.join(sorted(unknown))}")
        with _lock_for(self.path):
            cur = self._current().get(nid)
            if cur is None:
                raise KeyError(nid)
            note = dict(cur)
            if "text" in fields:
                note["text"] = str(fields["text"] or "")[:MAX_TEXT]
            if "tags" in fields:
                note["tags"] = _tags(fields["tags"])
            if "t" in fields:
                note["t"] = _ms(fields["t"], "t")
            if "t_end" in fields:
                note["t_end"] = None if fields["t_end"] is None else _ms(fields["t_end"], "t_end")
            if note.get("t_end") is not None and note["t_end"] < note["t"]:
                raise ValueError("t_end must not be before t")
            note["edited"] = _now_iso(self._clock)
            self._append(note)
        return note

    def delete(self, nid: str) -> None:
        with _lock_for(self.path):
            if nid not in self._current():
                raise KeyError(nid)
            self._append({"id": nid, "deleted": True})


__all__ = ["NoteLog", "read_notes", "NOTES_FILE", "KINDS"]
