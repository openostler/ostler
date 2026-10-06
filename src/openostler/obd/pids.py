# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``PidTable``: the PID formulas, read as data from a pack's signal store (spec §3).

The platform ships no PID table. A pack (``generic_obd2``) imports the formulas into its
store, and each OBD record carries ``x-obd {service, pid, len?, freq?}``. Records are
grouped by ``(service, pid)``; a PID's **response length** is ``x-obd.len`` or else the
largest ``offset + width`` of its fields. Offsets count from data byte A (the byte after
the PID). Values decode through :meth:`openostler.signals.Signal.decode`, so a multi-field
PID yields every field and signed kinds stay signed. Signals bind to
``(service, pid, signal name)``, never to an array index (muki01 fixture 11).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from ..signals import _WIDTH, Signal, _record_to_signal


def _hexint(v) -> int:
    return int(v, 16) if isinstance(v, str) else int(v)


@dataclass(frozen=True)
class PidEntry:
    service: int
    pid: int
    length: "int | None"
    signals: "Tuple[Signal, ...]"
    metrics: "Tuple[Optional[str], ...]" = ()


class PidTable:
    """PID records keyed by ``(service, pid)``. Mode 02 (freeze frame) reuses Mode 01's
    records when the store has none of its own."""

    def __init__(self, entries: "Dict[Tuple[int, int], PidEntry]") -> None:
        self._entries = dict(entries)

    @classmethod
    def from_records(cls, records: "Iterable[dict]") -> "PidTable":
        """Build from raw store records; records without ``x-obd`` are ignored."""
        groups: "Dict[Tuple[int, int], list]" = {}
        lengths: "Dict[Tuple[int, int], int]" = {}
        for r in records:
            xo = r.get("x-obd")
            if not xo:
                continue
            key = (_hexint(xo.get("service", 1)), _hexint(xo.get("pid", r["lid"])))
            groups.setdefault(key, []).append(_record_to_signal(r))
            if xo.get("len") is not None:
                lengths[key] = int(xo["len"])
        entries = {}
        for key, sigs in groups.items():
            length = lengths.get(key)
            if length is None:
                length = max(s.offset + _WIDTH.get(s.kind, 2) for s in sigs)
            entries[key] = PidEntry(key[0], key[1], length, tuple(sigs),
                                    tuple(s.metric for s in sigs))
        return cls(entries)

    # The spec names it ``from_signals``: the pack's store records are its signals.
    from_signals = from_records

    def entry(self, service: int, pid: int) -> "PidEntry | None":
        e = self._entries.get((service, pid))
        if e is None and service == 0x02:
            e = self._entries.get((0x01, pid))
        return e

    def length(self, service: int, pid: int) -> "int | None":
        e = self.entry(service, pid)
        return e.length if e is not None else None

    def pids(self, service: int = 0x01) -> "frozenset[int]":
        return frozenset(p for (s, p) in self._entries if s == service)

    def __len__(self) -> int:
        return len(self._entries)


__all__ = ["PidTable", "PidEntry"]
