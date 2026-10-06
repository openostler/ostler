# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""A detected K-line profile, remembered per vehicle (spec K-line profiles §2, owner Q5).

``<state dir>/kline_profiles.json`` maps a ``vid`` (the U0 local vehicle id, never a VIN)
to the profile ``detect()`` confirmed for it::

    {"3f9a1c07": {"profile": "kwp2000_fast", "key_bytes": "E9 8F", "address": "0x33",
                  "detected_utc": "2026-10-06T09:00:00Z"}}

On the next connect for that vid the link starts from it (``origin: "remembered"``), so a
reboot while driving re-inits without probing. Nothing else is stored: no VIN and no
identity read from the car. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time

from .keywords import classify, profile_from
from .profiles import BUILTIN, KLineProfile

MEMORY_FILE = "kline_profiles.json"
_VID_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,63}$")
_KEYS = ("profile", "key_bytes", "address", "detected_utc")
_lock = threading.Lock()


def _utc(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def _hex_bytes(text: "str | None") -> "bytes | None":
    if not text:
        return None
    try:
        return bytes.fromhex(str(text).replace(" ", ""))
    except ValueError:
        return None


class ProfileMemory:
    """The remembered profiles in one state directory."""

    def __init__(self, state_dir: str) -> None:
        self.path = os.path.join(os.path.abspath(str(state_dir)), MEMORY_FILE)

    def _read(self) -> dict:
        try:
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, data: dict) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = f"{self.path}.{os.getpid()}.{secrets.token_hex(3)}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, self.path)

    def get(self, vid: str) -> "dict | None":
        """The stored entry for ``vid`` (only the known keys), or None."""
        entry = self._read().get(vid)
        if not isinstance(entry, dict) or entry.get("profile") not in BUILTIN:
            return None
        return {k: entry.get(k) for k in _KEYS}

    def put(self, vid: str, profile: KLineProfile, key_bytes: "bytes | None",
            when: "float | None" = None) -> dict:
        """Store (or replace) the detected profile for ``vid``. Only generic built-ins are
        remembered: a detected profile always is one."""
        if not _VID_RE.match(str(vid)):
            raise ValueError(f"invalid vid {vid!r}")
        base = profile.name if profile.name in BUILTIN else None
        if base is None:
            raise ValueError(f"only a detected built-in profile is remembered, not {profile.name!r}")
        entry = {"profile": base,
                 "key_bytes": bytes(key_bytes).hex(" ").upper() if key_bytes else None,
                 "address": f"0x{profile.init_address:02x}",
                 "detected_utc": _utc(time.time() if when is None else when)}
        with _lock:
            data = self._read()
            data[str(vid)] = entry
            self._write(data)
        return entry

    def forget(self, vid: str) -> bool:
        """Drop the entry for ``vid`` (Developer). → True when there was one."""
        with _lock:
            data = self._read()
            if vid not in data:
                return False
            del data[vid]
            self._write(data)
        return True


def profile_from_entry(entry: dict) -> "tuple[KLineProfile, bytes | None]":
    """Rebuild the session profile and the expected key bytes from a stored entry: the
    built-in, with the header, length and timing its key bytes decode to."""
    name = entry["profile"]
    kb = _hex_bytes(entry.get("key_bytes"))
    base = BUILTIN[name]
    if kb is not None and len(kb) == 2 and base.framing == "kwp2000":
        method = "fast" if base.init == "fast" else "5baud"
        return profile_from(classify(kb[0], kb[1], method), base), kb
    return base, kb


__all__ = ["MEMORY_FILE", "ProfileMemory", "profile_from_entry"]
