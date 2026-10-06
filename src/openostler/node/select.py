# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selection, not fusion, for one VSS path published by several sources (NodeSource spec
§6.5, the P1 subset).

The rule: a usable (not stale) reading beats a stale one; then the pack-decoded bus value;
then the freshest; ties go to the lowest device id, then the lowest source tag. With
nothing usable the freshest stale reading is shown (still marked stale), never a zero.

Not yet here: the manifest's ``primary`` device and the owner's priority (they arrive with
the manifest, P3) and the ADR-0032 A4 GNSS algorithm with its shared vectors (TODO.md);
until then GNSS paths use the same generic rule. A selected value is for display and
recording only: no gate uses it (ADR-0032 A5).
"""
from __future__ import annotations

from typing import Iterable, Optional


def select(candidates: "Iterable[dict]") -> "Optional[dict]":
    """Pick one candidate. Each is ``{device, src, stale, age_s, pack_decoded}``
    (``age_s`` None = unknown)."""
    def key(c: dict):
        age = c.get("age_s")
        return (bool(c.get("stale")), not c.get("pack_decoded"),
                age is None, age if age is not None else 0.0,
                str(c.get("device")), str(c.get("src")))

    best = None
    for c in candidates:
        if best is None or key(c) < key(best):
            best = c
    return best


__all__ = ["select"]
