# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Fresh ids per bundle (trip-sharing spec §7, R10).

Every id that is stable across shares or encodes a time is replaced: the session id by
``s-`` and 16 random base32 characters, tap files by ``tap/bus<N>``, node devices and boot
ids by ``node-1``, ``boot-1`` … in order of first appearance, the vehicle id by
``vehicle-1``, user ids by ``driver``, ``driver-2`` …; relay ids, peer key fingerprints and
hub ids are dropped. The bundle id is 128 random bits, never derived from any of them.

:class:`IdMap` keeps the mapping from the new ids back to the real ones. It is returned to
the owner's device only (the share's audit entry), never written into a bundle.
"""
from __future__ import annotations

import base64
import secrets
from typing import Dict, Optional


def bundle_id() -> str:
    """128-bit CSPRNG id, 32 lower-case hex characters."""
    return secrets.token_hex(16)


def session_id() -> str:
    """``s-`` + 16 random base32 characters (lower case)."""
    return "s-" + base64.b32encode(secrets.token_bytes(10)).decode("ascii").lower()


def file_tag() -> str:
    """8 random characters for ``ostler-share-<tag>.zip``."""
    return base64.b32encode(secrets.token_bytes(5)).decode("ascii").lower()


class IdMap:
    """New id → real id, per kind, minted in order of first appearance."""

    PREFIX = {"device": "node", "boot": "boot", "vid": "vehicle", "user": "driver"}

    def __init__(self) -> None:
        self._fwd: "Dict[str, Dict[str, str]]" = {}
        self.session: Optional[str] = None
        self.source_session: Optional[str] = None

    def mint_session(self, real: "str | None") -> str:
        self.session, self.source_session = session_id(), real
        return self.session

    def get(self, kind: str, real) -> str:
        """The new id for a real one (minted on first use)."""
        key = str(real)
        table = self._fwd.setdefault(kind, {})
        if key not in table:
            n = len(table) + 1
            prefix = self.PREFIX.get(kind, kind)
            table[key] = prefix if (kind == "user" and n == 1) else f"{prefix}-{n}"
        return table[key]

    def owner_record(self) -> dict:
        """What the owner's audit entry keeps: ``{session: {new: real}, device: {...}}``."""
        out: dict = {}
        if self.session is not None:
            out["session"] = {self.session: self.source_session}
        for kind, table in self._fwd.items():
            out[kind] = {new: real for real, new in table.items()}
        return out


__all__ = ["IdMap", "bundle_id", "file_tag", "session_id"]
