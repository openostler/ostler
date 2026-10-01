"""Single source of truth for module detection across every Discovery 2 bus.

Both the capture parser (:mod:`d2diag.sniff.capture`) and the live LID store
(:mod:`d2diag.sniff.decoder`) need to know which ECU a stretch of sniffed bytes
belongs to. Each used to keep its own two-entry fast-init table (Td5 + SLABS). This
module unifies detection for all the buses the NanoCom touches, so adding a module
means editing one table:

- **Fast init** — addressed StartCommunication ``81 <addr> F7 81`` (Td5 ``0x13``,
  SLABS ``0x29``). An init to an address we do not recognise is tagged
  ``unknown:0xNN`` rather than dropped, so a scan still surfaces it (cruise, HEVAC,
  IDM, the ``0x18`` responder).
- **Addressed modules** — the airbag (TRW SPS, ``0x5B``) keeps ISO 14230 addressed
  framing for every message (``82 5B F7 …`` request, ``F7 5B …`` response), unlike
  the unaddressed session frames Td5/SLABS/BCU switch to.
- **EAT autobox** — the Bosch gearbox speaks a proprietary ``72``-framed protocol
  with an XOR checksum (request), and a ``72 <len> 60 …`` response marker.
- **ACE** — the Lucas roll-control streams bulk blocks whose leading bytes come in
  pairs (``67 67``, ``04 04``, ``07 07`` …).
- **BCU** — the Valeo body unit runs the same unaddressed KWP framing as Td5/SLABS
  (so its 5-baud slow init is invisible in a hex log), but the EKA identifier
  ``21 CC`` / ``3B CC`` is unique to it and gives a conservative signal.

The protocol facts here are drawn from ``references/protocol_state_handoff.md`` and
``src/d2diag/sniff/library.py`` (the ``KNOWN`` facts). Detection is a hint, not proof:
when a capture carries an operator marker (``>>> screen bcu/inputs``) the importer
trusts the marker over the heuristic.
"""
from __future__ import annotations

TESTER = 0xF7  # tester source address the NanoCom/our tools use (0xF7)

# Diagnostic addresses we have a name for. Fast- and slow-init modules share the map;
# an address not here becomes ``unknown:0xNN`` so a scan never silently drops it.
FAST_INIT_ADDRESSES = {0x13: "td5", 0x29: "slabs"}
SLOW_INIT_ADDRESSES = {0x40: "bcu", 0x5B: "airbag"}
ADDRESS_NAMES = {**FAST_INIT_ADDRESSES, **SLOW_INIT_ADDRESSES}

# ACE bulk blocks lead with a doubled byte (protocol, not a sampling artefact — see
# protocol_state_handoff.md). These pairs are distinctive enough to tag the stream.
_ACE_PAIRS = {(0x67, 0x67), (0x04, 0x04), (0x07, 0x07), (0xE0, 0xE0), (0xF0, 0xF0)}

# BCU EKA identifier — no other module uses 0xCC, so `21 CC`/`3B CC` means BCU.
_BCU_EKA = {(0x21, 0xCC), (0x3B, 0xCC)}


def name_for_address(addr: int) -> str:
    """Module name for a diagnostic address, or ``unknown:0xNN`` when unrecognised."""
    return ADDRESS_NAMES.get(addr, f"unknown:0x{addr:02x}")


def _find(seq: "list[int]", sub: "tuple[int, ...]") -> int:
    """Index of the first occurrence of ``sub`` in ``seq``, or -1."""
    n = len(sub)
    for i in range(len(seq) - n + 1):
        if tuple(seq[i : i + n]) == sub:
            return i
    return -1


def fast_init_signal(b: "list[int]") -> "tuple[str, int] | None":
    """An addressed StartCommunication (``81 <addr> F7 81``) in ``b`` → (module, addr)."""
    for i in range(len(b) - 3):
        if b[i] == 0x81 and b[i + 2] == TESTER and b[i + 3] == 0x81:
            addr = b[i + 1]
            return name_for_address(addr), addr
    return None


def _airbag_signal(b: "list[int]") -> bool:
    """Addressed framing at 0x5B: request ``82 5B F7`` or response ``F7 5B``."""
    return _find(b, (0x82, 0x5B, TESTER)) >= 0 or _find(b, (TESTER, 0x5B)) >= 0


def _eat_signal(b: "list[int]") -> bool:
    """EAT autobox `72` framing: an XOR-closed request, or a `72 <len> 60` response.

    A request is ``72 <bytes…> <cs>`` where ``cs`` is the XOR of everything before it
    (verified against ``72 05 04 00 73`` and ``72 04 05 73``). The response marker is
    ``72 <len> 60 …`` (the ``60`` byte), whose trailing checksum is not XOR and is not
    validated here — the ``60`` at offset +2 is signal enough.
    """
    n = len(b)
    for i in range(n):
        if b[i] != 0x72:
            continue
        if i + 2 < n and b[i + 2] == 0x60:  # response marker `72 <len> 60 …`
            return True
        # XOR-closed request: find a window 72..cs whose running XOR hits zero.
        acc = 0
        for j in range(i, min(n, i + 16)):
            acc ^= b[j]
            if j > i + 1 and acc == 0:  # at least 72 <b> <cs>
                return True
    return False


def _ace_signal(b: "list[int]") -> bool:
    return any(_find(b, pair) >= 0 for pair in _ACE_PAIRS)


def _bcu_signal(b: "list[int]") -> bool:
    return any(_find(b, pair) >= 0 for pair in _BCU_EKA)


def scan(b: "list[int]") -> "list[tuple[str, str]]":
    """Every module signal found in one sniffed byte line, as ``(module, how)``.

    May be empty (no recognisable init/framing on this line) or hold several. Order is
    the order signals are checked; a caller that tracks a single active module takes the
    last entry so the most recent init wins.
    """
    out: "list[tuple[str, str]]" = []
    fi = fast_init_signal(b)
    if fi is not None:
        module, addr = fi
        out.append((module, f"fast-init 0x{addr:02x}"))
    if _airbag_signal(b):
        out.append(("airbag", "addressed 0x5b"))
    if _eat_signal(b):
        out.append(("autobox", "72-framed"))
    if _ace_signal(b):
        out.append(("ace", "bulk pairs"))
    if _bcu_signal(b):
        out.append(("bcu", "eka 21/3b cc"))
    return out


class ModuleTracker:
    """Tracks the active module across a sniffed byte stream, line by line.

    Replaces the ad-hoc ``_INIT`` / ``_INIT_SIGS`` dicts that ``capture.py`` and
    ``decoder.py`` each carried. ``feed`` updates and returns the current module; it
    stays put on lines with no signal (the module keeps talking between inits).

    Authority matters. A real init event — fast init or the airbag's addressed framing —
    is authoritative and always switches the active module (this reproduces the old
    Td5/SLABS behaviour exactly). The ``72``/ACE/EKA content hints are weaker: a stray
    ``0x72`` data byte in a Td5 frame must not flip the module to the gearbox. So a
    content hint only *seeds* the module when none has been established yet (a capture
    that starts mid-session on a non-fast-init module), and never overrides an init.
    """

    def __init__(self) -> None:
        self.module: "str | None" = None

    def feed(self, b: "list[int]") -> "str | None":
        fi = fast_init_signal(b)
        if fi is not None:
            self.module = fi[0]
        elif _airbag_signal(b):
            self.module = "airbag"
        elif self.module is None:
            if _eat_signal(b):
                self.module = "autobox"
            elif _ace_signal(b):
                self.module = "ace"
            elif _bcu_signal(b):
                self.module = "bcu"
        return self.module
