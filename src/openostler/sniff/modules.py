# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Single source of truth for module detection across every sniffed bus.

Both the capture parser (:mod:`openostler.sniff.capture`) and the live LID store
(:mod:`openostler.sniff.decoder`) need to know which ECU a stretch of sniffed bytes
belongs to. Detection is generic; the facts come from the active vehicle pack's
:class:`openostler.pack.SniffSpec` (or an explicit ``spec``):

- **Fast init** — an addressed StartCommunication ``81 <addr> <tester> 81``. The address
  is named from ``spec.fast_init``/``spec.slow_init``; one we do not recognise is tagged
  ``unknown:0xNN`` rather than dropped, so a scan still surfaces it.
- **Authoritative detectors** (``spec.authoritative``) — framing that proves the module
  (e.g. a module that keeps addressed framing for every message).
- **Hints** (``spec.hints``) — content patterns that suggest a module but can also occur
  as data bytes elsewhere.

Detection is a hint, not proof: when a capture carries an operator marker
(``>>> screen <module>/inputs``) the importer trusts the marker over the heuristic.

The pack's address maps are re-exported lazily as ``TESTER``, ``FAST_INIT_ADDRESSES``,
``SLOW_INIT_ADDRESSES`` and ``ADDRESS_NAMES`` (module ``__getattr__``, never at import).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..pack import SniffSpec


def _spec(spec: "SniffSpec | None") -> "SniffSpec":
    if spec is not None:
        return spec
    from ..pack import active_pack

    return active_pack().sniff


def address_names(spec: "SniffSpec | None" = None) -> "dict[int, str]":
    """``{address: module}`` for every fast- and slow-init address the spec names."""
    s = _spec(spec)
    return {**s.fast_init, **s.slow_init}


def name_for_address(addr: int, spec: "SniffSpec | None" = None) -> str:
    """Module name for a diagnostic address, or ``unknown:0xNN`` when unrecognised."""
    return address_names(spec).get(addr, f"unknown:0x{addr:02x}")


def _find(seq: "list[int]", sub: "tuple[int, ...]") -> int:
    """Index of the first occurrence of ``sub`` in ``seq``, or -1."""
    n = len(sub)
    for i in range(len(seq) - n + 1):
        if tuple(seq[i : i + n]) == sub:
            return i
    return -1


def fast_init_signal(b: "list[int]", spec: "SniffSpec | None" = None) -> "tuple[str, int] | None":
    """An addressed StartCommunication (``81 <addr> <tester> 81``) in ``b`` → (module, addr)."""
    s = _spec(spec)
    for i in range(len(b) - 3):
        if b[i] == 0x81 and b[i + 2] == s.tester and b[i + 3] == 0x81:
            addr = b[i + 1]
            return name_for_address(addr, s), addr
    return None


def scan(b: "list[int]", spec: "SniffSpec | None" = None) -> "list[tuple[str, str]]":
    """Every module signal found in one sniffed byte line, as ``(module, how)``.

    May be empty (no recognisable init/framing on this line) or hold several. Order is
    the order signals are checked (fast init, authoritative detectors, hints); a caller
    that tracks a single active module takes the last entry so the most recent init wins.
    """
    s = _spec(spec)
    out: "list[tuple[str, str]]" = []
    fi = fast_init_signal(b, s)
    if fi is not None:
        module, addr = fi
        out.append((module, f"fast-init 0x{addr:02x}"))
    for det in tuple(s.authoritative) + tuple(s.hints):
        if det.match(b):
            out.append((det.module, det.how))
    return out


class ModuleTracker:
    """Tracks the active module across a sniffed byte stream, line by line.

    ``feed`` updates and returns the current module; it stays put on lines with no
    signal (the module keeps talking between inits).

    Authority matters. A real init event — fast init or an authoritative detector — always
    switches the active module. Content hints are weaker: a stray data byte that looks
    like another module's framing must not flip the module. So a hint only *seeds* the
    module when none has been established yet (a capture that starts mid-session on a
    non-fast-init module), and never overrides an init. Among several matches the first
    detector in spec order wins.
    """

    def __init__(self, spec: "SniffSpec | None" = None) -> None:
        self.module: "str | None" = None
        self._spec = _spec(spec)

    def feed(self, b: "list[int]") -> "str | None":
        s = self._spec
        fi = fast_init_signal(b, s)
        if fi is not None:
            self.module = fi[0]
            return self.module
        for det in s.authoritative:
            if det.match(b):
                self.module = det.module
                return self.module
        if self.module is None:
            for det in s.hints:
                if det.match(b):
                    self.module = det.module
                    break
        return self.module


def __getattr__(name: str):
    # The active pack's address facts, for old importers (resolved on access, not import).
    if name == "TESTER":
        return _spec(None).tester
    if name == "FAST_INIT_ADDRESSES":
        return dict(_spec(None).fast_init)
    if name == "SLOW_INIT_ADDRESSES":
        return dict(_spec(None).slow_init)
    if name == "ADDRESS_NAMES":
        return address_names()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
