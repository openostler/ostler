# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Classify a K-line ECU by its key bytes (ADR-0022, spec K-line profiles §2 step 4). Pure.

* ``KW1 == KW2`` (``08 08``, ``94 94``) → ISO 9141-2.
* Otherwise KWP2000 (ISO 14230-2): ``KB2`` is ``0x8F`` and ``KB1`` describes the header
  and length formats and the timing set. KB1 carries odd parity in bit 7; bits 0–6 are:

  ======  =====  ==========================================================
  bit 0   AL0    length in the format byte supported
  bit 1   AL1    a separate length byte supported
  bit 2   HB0    a one-byte header (no addresses) supported
  bit 3   HB1    a header with target and source supported
  bit 4   TP0    timing set: TP1 TP0 = ``01`` normal, ``10`` extended
  bit 5   TP1
  bit 6          always set
  ======  =====  ==========================================================

  So ``E9 8F`` (KB1 ``0x69`` after the parity bit) is AL0, HB1, extended timing; and the
  key word ``(KB2 & 0x7F) << 7 | (KB1 & 0x7F)`` falls in ISO 14230's 2000–2031 range.
  The header chosen is HB1 → ``functional`` (to ``0x33``, the OBD convention), else
  HB0 → ``none``; the length is AL0 → ``format``, else AL1 → ``separate``.
* Odd key bytes (bad parity, ``KB2 != 0x8F``, a TP of ``00`` or ``11``) are reported in
  :attr:`Classification.odd` and the KWP defaults stay (functional header, format length,
  normal timing); classification does not fail on them.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Optional

from .profiles import BUILTIN, KLineProfile

KB2_KWP2000 = 0x8F


def odd_parity_ok(byte: int) -> bool:
    """True when ``byte`` (bit 7 = parity) has an odd number of set bits."""
    return bin(byte & 0xFF).count("1") % 2 == 1


@dataclass(frozen=True)
class Classification:
    """What the key bytes say about the ECU."""

    profile: str                    # a BUILTIN name: iso9141_2, kwp2000_slow, kwp2000_fast
    protocol: str                   # "iso9141_2" | "kwp2000"
    header: str                     # profile.header to use
    length: str                     # profile.length to use
    timing_set: str                 # "normal" | "extended"
    bits: "dict[str, bool]"         # decoded KB1 bits (AL0, AL1, HB0, HB1, TP0, TP1); {} for 9141
    key_word: Optional[int] = None  # the ISO 14230 key word (2000–2031 when well formed)
    odd: Optional[str] = None       # why the key bytes were odd (defaults kept), or None

    def as_log(self) -> dict:
        """The fields of the ``classified`` connection-log event."""
        out = {"profile": self.profile, "protocol": self.protocol, "header": self.header,
               "length": self.length, "timing": self.timing_set,
               "bits": ",".join(k for k, v in self.bits.items() if v) or "-"}
        if self.key_word is not None:
            out["key_word"] = self.key_word
        if self.odd:
            out["odd"] = self.odd
        return out


def decode_kb1(kb1: int) -> "dict[str, bool]":
    """The KB1 bits (bits 0–5) by their ISO 14230-2 names."""
    return {"AL0": bool(kb1 & 0x01), "AL1": bool(kb1 & 0x02), "HB0": bool(kb1 & 0x04),
            "HB1": bool(kb1 & 0x08), "TP0": bool(kb1 & 0x10), "TP1": bool(kb1 & 0x20)}


def classify(kw1: int, kw2: int, method: str) -> Classification:
    """Classify the key bytes from an init. ``method`` is ``"fast"`` or ``"5baud"``.

    ISO 9141-2 is only possible after a 5-baud init; a fast init that answered ``C1`` is
    KWP2000 whatever the key bytes."""
    kw1 &= 0xFF
    kw2 &= 0xFF
    if method == "5baud" and kw1 == kw2:
        return Classification(profile="iso9141_2", protocol="iso9141_2", header="iso9141",
                              length="none", timing_set="normal", bits={})
    name = "kwp2000_fast" if method == "fast" else "kwp2000_slow"
    bits = decode_kb1(kw1)
    odd: "list[str]" = []
    if not odd_parity_ok(kw1):
        odd.append(f"KB1 0x{kw1:02X} fails odd parity")
    if kw2 != KB2_KWP2000:
        odd.append(f"KB2 0x{kw2:02X} is not 0x8F")
    tp = (bits["TP1"], bits["TP0"])
    if tp not in ((False, True), (True, False)):
        odd.append(f"TP {int(tp[0])}{int(tp[1])} is not 01 or 10")
    key_word = ((kw2 & 0x7F) << 7) | (kw1 & 0x7F)
    if odd:
        return Classification(profile=name, protocol="kwp2000", header="functional",
                              length="format", timing_set="normal", bits=bits,
                              key_word=key_word, odd="odd key bytes: " + "; ".join(odd))
    header = "functional" if bits["HB1"] else ("none" if bits["HB0"] else "functional")
    length = "format" if bits["AL0"] else ("separate" if bits["AL1"] else "format")
    timing = "extended" if bits["TP1"] else "normal"
    return Classification(profile=name, protocol="kwp2000", header=header, length=length,
                          timing_set=timing, bits=bits, key_word=key_word)


def profile_from(c: Classification, base: "KLineProfile | None" = None) -> KLineProfile:
    """The session profile for a classification: the built-in (or ``base``) with the
    decoded header, length and timing set filled in."""
    p = base if base is not None else BUILTIN[c.profile]
    if c.protocol == "iso9141_2":
        return p
    return dataclasses.replace(p, header=c.header, length=c.length, timing_set=c.timing_set)


__all__ = ["Classification", "classify", "decode_kb1", "odd_parity_ok", "profile_from",
           "KB2_KWP2000"]
