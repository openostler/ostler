# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remove device, the parts without a socket (module-bus spec v1.3 §7.2, §13; ADR-0037
Amendments 21; UI spec §3.7 plan note v0.11).

The owner removes a device on a local link; the Brain then

1. records it in its **revocation list** (``removed_devices.json`` in the state
   directory): from then on the Brain ignores that device's messages under the vehicle id,
   so a device that comes back unpaired is never shown as a claimant or holder by this
   Brain, and an install hook can drop its certificate and ACL entry on the broker host;
2. purges its retained topics ``ostler/v1/<vid>/<device>/#`` on the broker it controls,
   as a **broker-host operation** (``web/node_source.py``: a separate broker-host client
   publishes an empty retained message to each retained topic it finds).

This module holds the revocation list and the pure helpers. It never touches a car bus.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
from typing import Callable, Optional

from .messages import PREFIX, check_vid

REGISTRY_FILE = "removed_devices.json"
_DEVICE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def check_device(device: object) -> str:
    """A device id that is one topic level (no ``/``, ``+``, ``#``); raises ValueError."""
    if not isinstance(device, str) or not _DEVICE.match(device):
        raise ValueError(f"not a device id: {device!r}")
    return device


def device_filter(vid: str, device: str) -> str:
    """``ostler/v1/<vid>/<device>/#``: every topic of one device."""
    return f"{PREFIX}/{check_vid(vid)}/{check_device(device)}/#"


def gate_buses(cluster: dict, device: str) -> "list[str]":
    """The buses whose gate ``device`` claims in a cluster view (``GET /cluster``): what
    becomes writable by the gate holder once it is removed (the confirmation names them)."""
    out: "set[str]" = set()
    for row in cluster.get("devices", []):
        if row.get("id") != device:
            continue
        for c in row.get("claims", []) or []:
            if c.get("role") == "gate" and c.get("scope"):
                out.add(str(c["scope"]))
    return sorted(out)


class RemovedRegistry:
    """The Brain's revocation list: ``{vid: {device: {removed_utc, by, topics_purged}}}``
    in one JSON file, rewritten atomically. A missing or unreadable file is an empty list
    (and an unreadable one is kept aside, never overwritten silently)."""

    def __init__(self, path: str, *, wall: Callable[[], float] = time.time) -> None:
        self.path = path
        self._wall = wall

    def load(self) -> "dict[str, dict[str, dict]]":
        try:
            with open(self.path, encoding="utf-8") as f:
                doc = json.load(f)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            return {}
        return doc if isinstance(doc, dict) else {}

    def devices(self, vid: str) -> "list[str]":
        return sorted((self.load().get(vid) or {}).keys())

    def add(self, vid: str, device: str, *, by: "str | None" = None,
            topics_purged: "Optional[list[str]]" = None) -> dict:
        doc = self.load()
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self._wall())) + "Z"
        rec = {"removed_utc": stamp, "by": by, "topics_purged": list(topics_purged or [])}
        doc.setdefault(vid, {})[device] = rec
        self._write(doc)
        return rec

    def update(self, vid: str, device: str, **fields) -> None:
        doc = self.load()
        if device in (doc.get(vid) or {}):
            doc[vid][device].update(fields)
            self._write(doc)

    def readmit(self, vid: str, device: str) -> bool:
        """Drop ``device`` from the list (it was paired again). True when it was there."""
        doc = self.load()
        if device not in (doc.get(vid) or {}):
            return False
        del doc[vid][device]
        self._write(doc)
        return True

    def _write(self, doc: dict) -> None:
        d = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(doc, f, indent=2, sort_keys=True)
                f.write("\n")
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


__all__ = ["REGISTRY_FILE", "RemovedRegistry", "check_device", "device_filter", "gate_buses"]
