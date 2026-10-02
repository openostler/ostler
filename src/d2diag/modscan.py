"""Read-only address scan — who answers on the K-line, and how.

Before the NanoCom rental we want to know which of the *asserted-only* modules (cruise
control, HEVAC, instrument pack, IDM, the ``0x18`` responder) are actually present on
pin 7, so the capture checklist doesn't waste rental time on ghosts. This walks a list of
diagnostic addresses, tries the matching init, and records the key bytes of whoever
answers.

**It is read-only by construction.** It only ever sends an init (fast init's addressed
StartCommunication, or a 5-baud slow init) and then ``StopCommunication`` (``82``) to
release the link — never a ReadDataByLocalId, SecurityAccess or any write. Every probe
ends with a release, per ``CONSTITUTION.md`` (the K-line is a shared bus; a session left
open answers ``7F 81 10`` to the next module). A quiet settle between addresses lets a
module's link die before the next init.
"""
from __future__ import annotations

import time
from typing import Callable

from .kline.kline import KLineError
from .kwp2000.kwp2000 import KWP2000, KWP2000Error
from .sniff.modules import FAST_INIT_ADDRESSES, SLOW_INIT_ADDRESSES, name_for_address


class AddressScanner:
    """Walks addresses on one KWP2000 link, retargeting it per probe. Read-only."""

    def __init__(self, kwp: KWP2000,
                 sleep: Callable[[float], None] = time.sleep,
                 settle: float = 2.0,
                 progress: "Callable[[str], None] | None" = None) -> None:
        self._kwp = kwp
        self._k = kwp._k
        self._sleep = sleep
        self._settle = settle
        self._progress = progress

    def _say(self, msg: str) -> None:
        if self._progress is not None:
            self._progress(msg)

    def _release(self) -> None:
        """StopCommunication (best-effort) — the only thing we send besides init."""
        try:
            self._kwp.stop_communication()
        except (KLineError, KWP2000Error):
            pass  # a silent bus / no open link is the normal case

    def probe_fast(self, addr: int) -> "dict":
        """Fast-init StartCommunication to ``addr``. Records key bytes or 'silent'."""
        self._say(f"fast init 0x{addr:02x}")
        self._k._target = addr
        result = {"address": f"0x{addr:02x}", "init": "fast",
                  "module": name_for_address(addr)}
        try:
            data = self._kwp.start_communication(tolerant=True)
            result.update(status="responded", keybytes=bytes(data).hex(" "))
        except (KLineError, KWP2000Error) as exc:
            result.update(status="silent", error=f"{type(exc).__name__}")
        finally:
            self._release()
        return result

    def probe_slow(self, addr: int) -> "dict":
        """5-baud slow init to ``addr``. Records key bytes or 'silent'."""
        self._say(f"5-baud slow init 0x{addr:02x}")
        self._k._target = addr
        result = {"address": f"0x{addr:02x}", "init": "slow",
                  "module": name_for_address(addr)}
        try:
            kw = self._kwp.slow_init(addr)
            result.update(status="responded", keybytes=f"{kw[0]:02x} {kw[1]:02x}")
        except (KLineError, KWP2000Error) as exc:
            result.update(status="silent", error=f"{type(exc).__name__}")
        finally:
            self._release()
        return result

    def scan(self, fast: "list[int]", slow: "list[int]") -> "list[dict]":
        """Probe each address, settling between probes. → ordered result rows."""
        rows: "list[dict]" = []
        probes = [("fast", a) for a in fast] + [("slow", a) for a in slow]
        for i, (init, addr) in enumerate(probes):
            rows.append(self.probe_fast(addr) if init == "fast" else self.probe_slow(addr))
            if i + 1 < len(probes):
                self._say(f"settling {self._settle:.0f}s")
                self._sleep(self._settle)  # let the link die before the next init
        return rows


# Default address plan for a Td5 Discovery 2: the proven modules plus every asserted-only
# address we want to confirm or rule out (cruise/HEVAC/IDM/instrument pack live here, and
# the 0x18 responder that answered a 5-baud wake). Unknown addresses are reported as
# `unknown:0xNN` by name_for_address, never dropped.
DEFAULT_FAST = sorted(FAST_INIT_ADDRESSES)                         # 0x13, 0x29
DEFAULT_SLOW = sorted(set(SLOW_INIT_ADDRESSES) | {0x18, 0x5A})     # 0x18, 0x40, 0x5a, 0x5b


def render_table(rows: "list[dict]") -> str:
    """A compact text table of scan results."""
    out = ["address  init  module          status     keybytes/err"]
    for r in rows:
        detail = r.get("keybytes") or r.get("error") or ""
        out.append(f"{r['address']:<8} {r['init']:<5} {r['module']:<15} "
                   f"{r['status']:<10} {detail}")
    return "\n".join(out) + "\n"
