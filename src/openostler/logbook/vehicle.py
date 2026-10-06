"""The local vehicle id (``vid``, UI spec §4.1, U0). Core: stdlib only, never imports web.

A ``vid`` names one vehicle, not a pack: two Discovery 2s share the pack ``lr_d2`` but
have two vids. Until the garage (U6) exists there is one local vehicle, kept in
``<state dir>/vehicle.json`` (``logs/vehicle.json``, next to ``logs/sessions/``):

    {"vid": "3f9a1c07", "pack": "lr_d2", "created_utc": "2026-10-06T09:00:00.000Z"}

* The file is created once, atomically and only if absent (two processes racing both end
  up with the first one's vid), and read on every later start. It holds no VIN or any
  other identity read from the car.
* ``OSTLER_VEHICLE_ID`` overrides the vid (a valid id: letters, digits, ``_`` and ``-``,
  at most 64 characters); the file is left as it is.
* If the state directory cannot be written, a random vid is kept in memory for the life
  of the process (never written), so recording still works.

The recorder stamps ``vid`` into every new session's ``meta.json``; the store reads a
legacy session without one as the local vid, on read only (files are never rewritten).
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time

VEHICLE_FILE = "vehicle.json"
ENV_VID = "OSTLER_VEHICLE_ID"
VID_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,63}$")
_UNSET = object()
_lock = threading.Lock()
_memory: "dict[str, dict]" = {}   # state dir → an unpersisted record (unwritable dir)


def new_vid() -> str:
    """A short random vehicle id: 8 lowercase hex characters."""
    return secrets.token_hex(4)


def state_dir_for(sessions_root: str) -> str:
    """The state directory of a sessions root: its parent (``logs/sessions`` → ``logs``)."""
    root = os.path.abspath(str(sessions_root).rstrip("/\\") or ".")
    return os.path.dirname(root) or root


def _iso_now(clock) -> str:
    ms = int(round(clock() * 1000))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def _active_pack_id() -> "str | None":
    try:
        from ..pack import active_pack

        return active_pack().id
    except Exception:  # noqa: BLE001 — no pack installed: the record still gets a vid
        return None


def _read(path: str) -> "dict | None":
    try:
        with open(path, "r", encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError):
        return None
    if isinstance(rec, dict) and isinstance(rec.get("vid"), str) and VID_RE.match(rec["vid"]):
        return rec
    return None


def _create(path: str, rec: dict) -> None:
    """Write ``rec`` to ``path`` only if ``path`` does not exist (atomic, no overwrite)."""
    tmp = f"{path}.{os.getpid()}.{secrets.token_hex(3)}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
        fh.write("\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    try:
        try:
            os.link(tmp, path)            # fails with FileExistsError if another won
        except FileExistsError:
            pass
        except OSError:                   # no hard links on this filesystem
            if not os.path.exists(path):
                os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def ensure_vehicle(state_dir: str, pack=_UNSET, clock=time.time) -> dict:
    """The local vehicle record from ``<state_dir>/vehicle.json``, created on first use.
    ``pack`` (default: the active pack's id, or None) is written only at creation. An
    invalid file is replaced; a valid one is never rewritten."""
    state_dir = os.path.abspath(str(state_dir))
    path = os.path.join(state_dir, VEHICLE_FILE)
    rec = _read(path)
    if rec is not None:
        return rec
    with _lock:
        rec = _read(path)
        if rec is not None:
            return rec
        if state_dir in _memory:
            return _memory[state_dir]
        new = {"vid": new_vid(), "pack": _active_pack_id() if pack is _UNSET else pack,
               "created_utc": _iso_now(clock)}
        try:
            os.makedirs(state_dir, exist_ok=True)
            if os.path.exists(path):      # present but invalid: start it over
                os.remove(path)
            _create(path, new)
        except OSError:
            _memory[state_dir] = new
            return new
        return _read(path) or new


def env_vid() -> "str | None":
    """``OSTLER_VEHICLE_ID`` when set to a valid vid, else None."""
    v = os.environ.get(ENV_VID, "").strip()
    return v if v and VID_RE.match(v) else None


def local_vid(state_dir: str) -> str:
    """The vid of this device's vehicle: ``OSTLER_VEHICLE_ID`` if set, else the vid in
    ``<state_dir>/vehicle.json`` (created on first use)."""
    return env_vid() or ensure_vehicle(state_dir)["vid"]


__all__ = ["VEHICLE_FILE", "ENV_VID", "VID_RE", "new_vid", "state_dir_for",
           "ensure_vehicle", "env_vid", "local_vid"]
