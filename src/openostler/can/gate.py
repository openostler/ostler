# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Transmit gating (CanLink spec §7): ``TxGate``, the pack allowlist and ``TxGrant``.

Every frame any :meth:`CanLink.send` emits passes :meth:`TxGate.check`:

1. **Rate** confirmed or declared, else ``RateNotConfirmed`` (ADR-0023).
2. **Never** (before anything else may pass): a link of kind ``mqtt``; a grant minted for
   a remote path without the install override (ADR-0033 §6); a Tier 4 UDS service
   (``27 2E 2F 31 3B 11 14 28 85``); OBD Mode 08 (J1979 spec §5).
3. **Tier 0** in every driving state (ADR-0020 as amended): a single-frame read (OBD
   ``01 02 03 06 07 09 0A``; UDS ``22 19 3E``) on a diagnostic request id (``7DF``,
   ``7E0``–``7E7``, ``18DB33F1``, ``18DAxxF1``), at most one per ``tier0_min_gap`` per id;
   or a flow-control frame for a reply to such a request (the FC window). The sweep guard
   (owner, 2026-10-06): while not Parked, a functional ``3E`` and a physical ``3E`` to a
   third distinct ECU within ``sweep_window`` are refused (``sweep_not_parked``).
4. **Everything else** needs all three: a matching **allowlist** entry, the driving state
   in the entry's ``states`` (default Parked; re-read at send time) and a valid
   **TxGrant** for the entry's action and tier, short-lived and single-use. The grant
   passes the injected ``grant_verifier`` first (``grant_invalid``: bad signature or
   unknown key; the default accepts only the lab's unsigned in-process grants).

The exact order of the checks, and so which refusal code wins, is listed in
``tests/vectors/can/README.md``; the node's C port mirrors it.

The silent-bus probe (spec §4) has its own check: :meth:`TxGate.probe_grant` (Parked
only) and :meth:`TxGate.check_probe` (one-shot capable link, the exact ``7DF 02 01 00``
frame, Parked re-read, single use).

This Python gate is the lab/reference (spec §7.1): the production gate is the node's C
``TxGate``; the shared vectors in ``tests/vectors/can/gate.json`` check both.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from .frame import CanFrame
from .link import RateNotConfirmed, TxRefused

log = logging.getLogger("openostler.can.gate")

PARKED, IDLING, MOVING = "parked", "idling", "moving"
DRIVING_STATES = (PARKED, IDLING, MOVING)
OBD_READS = frozenset({0x01, 0x02, 0x03, 0x06, 0x07, 0x09, 0x0A})
UDS_READS = frozenset({0x22, 0x19, 0x3E})
TIER4_UDS = frozenset({0x27, 0x2E, 0x2F, 0x31, 0x3B, 0x11, 0x14, 0x28, 0x85})
MODE_NEVER = 0x08
REMOTE_OVERRIDE_ENV = "OSTLER_ALLOW_REMOTE_CONTROL"
_TRUE = frozenset({"1", "true", "yes", "on"})

FUNC_11, FUNC_29 = 0x7DF, 0x18DB33F1
FUNCTIONAL = frozenset({(FUNC_11, False), (FUNC_29, True)})
TESTER_PRESENT = 0x3E
GRANT_OK, GRANT_INVALID = "ok", "invalid"


class Tier0:
    """The marker grant for Tier 0 diagnostic reads and their flow control."""

    _inst: "Tier0 | None" = None

    def __new__(cls) -> "Tier0":
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self) -> str:
        return "TIER0"


TIER0 = Tier0()


@dataclass(frozen=True)
class TxGrant:
    """Minted by the server gate (in the lab, :meth:`TxGate.issue`) for one action and
    tier; short-lived and single-use. On the node it becomes a signed token (§7.1), carried
    in ``token`` and checked by the gate's injected ``grant_verifier``."""

    action: str
    tier: int
    expires: float
    nonce: str
    origin: str = "local"           # "local" | "remote"
    token: str = ""                 # the signed token (§7.1); "" = an unsigned lab grant


def accept_unsigned(grant: TxGrant) -> str:
    """The default grant verifier: the lab's unsigned in-process grants (no token) pass;
    a grant carrying a token this gate cannot check is ``invalid`` (fail closed)."""
    return GRANT_OK if not grant.token else GRANT_INVALID


@dataclass(frozen=True)
class ProbeGrant:
    """Permission for one silent-bus probe frame; minted only while Parked."""

    nonce: str
    issued: float


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reason: str                     # "tier0" | "fc" | "allowlist" | "probe" | a refusal code
    action: "str | None" = None


def is_diag_request_id(can_id: int, extended: bool) -> bool:
    """A Tier 0 diagnostic request id: ``7DF``/``7E0``–``7E7`` or ``18DB33F1``/``18DAxxF1``."""
    if extended:
        return can_id == FUNC_29 or (can_id & 0x1FFF00FF) == 0x18DA00F1
    return can_id == FUNC_11 or 0x7E0 <= can_id <= 0x7E7


def frame_service(data: bytes) -> "int | None":
    """The service byte of an ISO-TP SF or FF, else None."""
    if not data:
        return None
    pci = data[0] >> 4
    if pci == 0 and 1 <= (data[0] & 0x0F) <= 7 and len(data) >= 2:
        return data[1]
    if pci == 1 and len(data) >= 3:
        return data[2]
    return None


def remote_override_from_env(env: "Mapping[str, str] | None" = None) -> bool:
    env = os.environ if env is None else env
    return str(env.get(REMOTE_OVERRIDE_ENV, "")).strip().lower() in _TRUE


@dataclass(frozen=True)
class AllowEntry:
    """One pack allowlist entry (``schemas/can-tx-allowlist.schema.json``)."""

    id: int
    action: str
    tier: int
    extended: bool = False
    data: str = ""                          # spaced hex with "xx" wildcards; "" = any
    dlc: "int | None" = None
    bus: str = "obd"
    max_rate_hz: "float | None" = None
    states: "Tuple[str, ...]" = (PARKED,)

    @classmethod
    def from_dict(cls, d: Mapping) -> "AllowEntry":
        cid = d["id"]
        states = tuple(d.get("states") or (PARKED,))
        if MOVING in states:
            raise ValueError("an allowlist entry never allows Moving (ADR-0020)")
        if int(d["tier"]) >= 4:
            raise ValueError("Tier 4 needs its own ADR; no allowlist entry may declare it")
        return cls(int(cid, 16) if isinstance(cid, str) else int(cid), str(d["action"]),
                   int(d["tier"]), bool(d.get("extended", False)), str(d.get("data", "")),
                   d.get("dlc"), str(d.get("bus", "obd")), d.get("max_rate_hz"), states)

    def matches(self, frame: CanFrame, bus: str = "obd") -> bool:
        if frame.id != self.id or frame.extended != self.extended or bus != self.bus:
            return False
        if self.dlc is not None and frame.dlc != self.dlc:
            return False
        pat = self.data.split()
        if len(pat) > len(frame.data):
            return False
        return all(p.lower() == "xx" or int(p, 16) == b for p, b in zip(pat, frame.data))


@dataclass
class TxGate:
    allowlist: "Iterable[AllowEntry | Mapping]" = ()
    driving_state: "Optional[Callable[[], Optional[str]]]" = None
    clock: Callable[[], float] = time.monotonic
    allow_remote: "bool | None" = None
    audit: "Optional[Callable[[dict], object]]" = None
    tier0_min_gap: float = 0.050
    fc_window: float = 5.5          # P2* plus margin: FCs follow a Tier 0 request this long
    grant_ttl: float = 10.0
    sweep_window: float = 5.0       # a 3E to a third distinct ECU within this, not Parked
    grant_verifier: Callable[[TxGrant], str] = accept_unsigned
    _entries: "List[AllowEntry]" = field(default_factory=list, repr=False)
    _issued: "Dict[str, TxGrant]" = field(default_factory=dict, repr=False)
    _probes: "Dict[str, ProbeGrant]" = field(default_factory=dict, repr=False)
    _last0: "Dict[Tuple[int, bool], float]" = field(default_factory=dict, repr=False)
    _last_entry: "Dict[int, float]" = field(default_factory=dict, repr=False)
    _fc_until: "Dict[object, float]" = field(default_factory=dict, repr=False)
    _tx_open: "Dict[Tuple[int, bool], Tuple[int, str]]" = field(default_factory=dict, repr=False)
    _last3e: "Dict[Tuple[int, bool], float]" = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._entries = [e if isinstance(e, AllowEntry) else AllowEntry.from_dict(e)
                         for e in self.allowlist]
        if self.allow_remote is None:
            self.allow_remote = remote_override_from_env()
        object.__setattr__(self, "_remote", bool(self.allow_remote))

    def __setattr__(self, name, value) -> None:
        if name in ("allow_remote", "_remote") and "_remote" in self.__dict__:
            raise AttributeError("the remote-control override is install-level and fixed")
        super().__setattr__(name, value)

    # ---- driving state ---------------------------------------------------- #
    def state(self) -> str:
        """The driving state now; anything unknown counts as Moving (UI spec §3.5)."""
        s = self.driving_state() if self.driving_state is not None else None
        return s if s in DRIVING_STATES else MOVING

    # ---- grants ----------------------------------------------------------- #
    def issue(self, action: str, tier: int, *, origin: str = "local",
              ttl: "float | None" = None, token: str = "") -> TxGrant:
        """Mint a grant (the lab stand-in for the server gate). A remote path gets none
        unless the install override is on; Tier 4 never."""
        if tier >= 4:
            raise TxRefused("tier4", "Tier 4 needs its own ADR")
        if origin != "local" and not self._remote:  # type: ignore[attr-defined]
            raise TxRefused("remote", "no grant is minted for a remote path")
        g = TxGrant(action, int(tier), self.clock() + (self.grant_ttl if ttl is None else ttl),
                    secrets.token_hex(8), origin, token)
        self._issued[g.nonce] = g
        return g

    def probe_grant(self) -> ProbeGrant:
        if self.state() != PARKED:
            self._refused("not_parked", None, "probe")
            raise TxRefused("not_parked", "the silent-bus probe needs the vehicle Parked")
        p = ProbeGrant(secrets.token_hex(8), self.clock())
        self._probes[p.nonce] = p
        return p

    # ---- the check -------------------------------------------------------- #
    def check(self, frame: CanFrame, grant=TIER0, *, rate_ok: bool,
              link_kind: str = "", bus: str = "obd") -> GateDecision:
        d = self.decide(frame, grant, rate_ok=rate_ok, link_kind=link_kind, bus=bus,
                        commit=True)
        if not d.allowed:
            if d.reason == "rate_not_confirmed":
                raise RateNotConfirmed()
            raise TxRefused(d.reason, f"transmit refused: {d.reason}")
        return d

    def decide(self, frame: CanFrame, grant=TIER0, *, rate_ok: bool, link_kind: str = "",
               bus: str = "obd", commit: bool = False) -> GateDecision:
        now = self.clock()
        d = self._decide(frame, grant, rate_ok, link_kind, bus, now, commit)
        if not d.allowed:
            self._refused(d.reason, frame, "send")
        elif d.reason == "allowlist":
            log.info("can tx permitted: %s action=%s", frame.id_text, d.action)
            self._emit({"outcome": "permitted", "id": frame.id_text, "action": d.action})
        return d

    def _decide(self, frame, grant, rate_ok, link_kind, bus, now, commit) -> GateDecision:
        key = (frame.id, frame.extended)
        if not rate_ok:
            return GateDecision(False, "rate_not_confirmed")
        if link_kind == "mqtt":
            return GateDecision(False, "mqtt_link")
        if isinstance(grant, TxGrant) and grant.origin != "local" and not self._remote:  # type: ignore[attr-defined]
            return GateDecision(False, "remote")
        svc = frame_service(frame.data)
        if svc in TIER4_UDS:
            return GateDecision(False, "tier4_service")
        if svc == MODE_NEVER:
            return GateDecision(False, "mode08")
        pci = frame.data[0] >> 4 if frame.data else -1
        diag = is_diag_request_id(frame.id, frame.extended)
        # ---- Tier 0 ---- #
        if diag and pci == 3 and self._fc_open(frame, now):
            return GateDecision(True, "fc")
        if diag and pci == 0 and svc in (OBD_READS | UDS_READS):
            if svc == TESTER_PRESENT and self._sweep(key, now):
                return GateDecision(False, "sweep_not_parked")
            last = self._last0.get(key)
            if last is not None and now - last < self.tier0_min_gap - 1e-9:
                return GateDecision(False, "rate_limited")
            if commit:
                self._last0[key] = now
                if svc == TESTER_PRESENT and key not in FUNCTIONAL:
                    self._last3e = {k: t for k, t in self._last3e.items()
                                    if now - t < self.sweep_window}
                    self._last3e[key] = now
                self._open_fc(frame, now)
            return GateDecision(True, "tier0")
        # ---- a consecutive frame of a message the gate already permitted ---- #
        if pci == 2 and key in self._tx_open:
            left, action = self._tx_open[key]
            if commit:
                left -= 7
                if left <= 0:
                    del self._tx_open[key]
                else:
                    self._tx_open[key] = (left, action)
            return GateDecision(True, "allowlist", action)
        # ---- allowlist + driving state + grant ---- #
        entry = next((e for e in self._entries if e.matches(frame, bus)), None)
        if entry is None:
            return GateDecision(False, "not_allowlisted")
        if self.state() not in entry.states:
            return GateDecision(False, "driving_state")
        if not isinstance(grant, TxGrant):
            return GateDecision(False, "no_grant")
        if not self._grant_valid(grant):
            return GateDecision(False, "grant_invalid")
        mine = self._issued.get(grant.nonce)
        if mine is None or mine != grant:
            return GateDecision(False, "grant_used")
        if now > grant.expires:
            return GateDecision(False, "grant_expired")
        if grant.action != entry.action or grant.tier != entry.tier:
            return GateDecision(False, "grant_mismatch")
        if entry.max_rate_hz:
            last = self._last_entry.get(id(entry))
            if last is not None and now - last < 1.0 / entry.max_rate_hz - 1e-9:
                return GateDecision(False, "entry_rate")
        if commit:
            del self._issued[grant.nonce]
            self._last_entry[id(entry)] = now
            if pci == 1 and len(frame.data) >= 2:
                total = ((frame.data[0] & 0x0F) << 8) | frame.data[1]
                self._tx_open[key] = (total - 6, entry.action)
            if diag:
                self._open_fc(frame, now)
        return GateDecision(True, "allowlist", entry.action)

    def check_probe(self, frame: CanFrame, probe, *, one_shot: bool,
                    link_kind: str = "") -> GateDecision:
        d = self.decide_probe(frame, probe, one_shot=one_shot, link_kind=link_kind, commit=True)
        if not d.allowed:
            raise TxRefused(d.reason, f"probe refused: {d.reason}")
        return d

    def decide_probe(self, frame: CanFrame, probe, *, one_shot: bool, link_kind: str = "",
                     commit: bool = False) -> GateDecision:
        if link_kind == "mqtt":
            d = GateDecision(False, "mqtt_link")
        elif not one_shot:
            d = GateDecision(False, "no_one_shot")
        elif not isinstance(probe, ProbeGrant) or self._probes.get(probe.nonce) != probe:
            d = GateDecision(False, "probe_used")
        elif self.state() != PARKED:
            d = GateDecision(False, "not_parked")
        elif (frame.id, frame.extended) != (FUNC_11, False) or frame.data[:3] != b"\x02\x01\x00" \
                or frame.dlc != 8:
            d = GateDecision(False, "probe_frame")
        else:
            d = GateDecision(True, "probe")
        if commit and isinstance(probe, ProbeGrant):
            self._probes.pop(probe.nonce, None)     # single use, whatever the outcome
        if not d.allowed:
            self._refused(d.reason, frame, "probe")
        return d

    def _grant_valid(self, grant: TxGrant) -> bool:
        try:
            return self.grant_verifier(grant) == GRANT_OK
        except Exception:                   # a verifier that fails, refuses (fail closed)
            log.exception("can grant verifier failed")
            return False

    # ---- the sweep guard -------------------------------------------------- #
    def _sweep(self, key: "Tuple[int, bool]", now: float) -> bool:
        """True when a ``3E`` on ``key`` would be a sweep while not Parked: a functional
        ``3E``, or a physical one while permitted physical ``3E`` frames to two *other*
        ECU ids fall within ``sweep_window`` (so this would be the third distinct ECU;
        owner, 2026-10-06). Physical ``3E`` frames permitted while Parked count too."""
        if self.state() == PARKED:
            return False
        if key in FUNCTIONAL:
            return True
        others = sum(1 for k, t in self._last3e.items()
                     if k != key and now - t < self.sweep_window - 1e-9)
        return others >= 2

    # ---- the FC window ---------------------------------------------------- #
    def _open_fc(self, frame: CanFrame, now: float) -> None:
        key: object = (frame.id, frame.extended)
        if frame.id == FUNC_11 and not frame.extended:
            key = "func11"
        elif frame.id == FUNC_29 and frame.extended:
            key = "func29"
        self._fc_until[key] = now + self.fc_window

    def _fc_open(self, frame: CanFrame, now: float) -> bool:
        def alive(k: object) -> bool:
            return self._fc_until.get(k, -1.0) >= now
        if alive((frame.id, frame.extended)):
            return True
        if frame.extended:
            return frame.id != FUNC_29 and alive("func29")
        return frame.id != FUNC_11 and alive("func11")

    # ---- logging ---------------------------------------------------------- #
    def _refused(self, reason: str, frame: "CanFrame | None", what: str) -> None:
        ident = frame.id_text if frame is not None else None
        log.info("can %s refused: %s (%s)", what, reason, ident)
        self._emit({"outcome": "refused", "what": what, "reason": reason, "id": ident})

    def _emit(self, entry: dict) -> None:
        if self.audit is not None:
            self.audit({"type": "can_tx", "t": self.clock(), **entry})


def load_allowlist(doc: "Iterable[Mapping]") -> "List[AllowEntry]":
    """Parse a pack's ``can.tx_allowlist`` (validated against the schema in CI)."""
    return [AllowEntry.from_dict(d) for d in doc]


__all__ = ["TxGate", "TxGrant", "ProbeGrant", "Tier0", "TIER0", "AllowEntry",
           "GateDecision", "load_allowlist", "is_diag_request_id", "frame_service",
           "remote_override_from_env", "accept_unsigned", "PARKED", "IDLING", "MOVING",
           "OBD_READS", "UDS_READS", "TIER4_UDS", "FUNC_11", "FUNC_29", "TESTER_PRESENT",
           "GRANT_OK", "GRANT_INVALID"]
