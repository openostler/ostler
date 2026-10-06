# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Mode 04 as a Tier 1 Maintenance action, made safe (spec §5, ADR-0033 §5, CONSTITUTION).

This module holds the clear policy the server gate (U2) and, later, the node gate apply:

- :func:`plan` names the ECUs and codes, builds the **one confirmation** text, adds the
  **safety-system warning** (airbag/SRS, ABS, brakes) and leaves out ECUs a pack marks
  read-only (airbag/SRS is read-only by construction: never sent ``04``).
- :class:`ClearGate` checks the driving state (**Parked or Idling**, never Moving), the
  role (Maintenance: Owner, Driver and Mechanic; never Viewer or the unsigned kiosk), the
  link (**local only** unless the install override ``OSTLER_ALLOW_REMOTE_CONTROL``, read
  once from the environment at start and never settable afterwards) and the confirmation,
  then mints a short-lived, single-use :class:`ClearGrant`. Every refusal is audited.

:meth:`openostler.obd.J1979.clear_dtcs` redeems the grant, writes the automatic snapshot
and the audit entry, sends ``04`` and re-reads. Until U2 wires a route, nothing in the
server mints a grant, so no clear can run from the app.
"""
from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Mapping, Optional, Tuple

from .decode import DtcRead
from .link import ObdError

PARKED, IDLING, MOVING = "parked", "idling", "moving"
CLEAR_STATES = frozenset({PARKED, IDLING})
LOCAL_LINKS = frozenset({"head_unit", "lan", "node_ap", "ble"})
MAINTENANCE_ROLES = frozenset({"owner", "driver", "mechanic"})
REMOTE_OVERRIDE_ENV = "OSTLER_ALLOW_REMOTE_CONTROL"
_TRUE = frozenset({"1", "true", "yes", "on"})

CATEGORY = "maintenance"
TIER = 1

SAFETY_WARNING = ("Some of these codes come from a safety system (airbag, ABS or brakes). "
                  "The fault may still be present, and the system may not work as intended "
                  "until it is repaired.")
NRC22_MESSAGE = ("{name} refused: conditions not correct (the engine is probably running). "
                 "Switch the engine off, leave the ignition on, and try again.")
PERMANENT_NOTE = ("Permanent codes stay until the ECU's own monitor confirms the repair over "
                  "later drive cycles; a clear cannot remove them.")


class ClearRefused(ObdError):
    """The clear was refused. ``code`` is machine-readable; the message is user text."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ClearContext:
    """Who asks, from where, in which driving state (re-checked at redemption)."""

    user: "str | None"              # signed-in user; None for the head-unit kiosk session
    role: str                       # owner | driver | mechanic | viewer | kiosk
    device: str
    link: str                       # head_unit | lan | node_ap | ble, or a remote path
    driving_state: str              # parked | idling | moving
    categories: "frozenset[str] | None" = None   # explicit grants narrow the role default

    def to_dict(self) -> dict:
        return {"user": self.user, "role": self.role, "device": self.device,
                "link": self.link, "driving_state": self.driving_state}


@dataclass(frozen=True)
class ClearPlan:
    ecus: "Tuple[str, ...]"                 # ECUs that will be cleared
    read_only: "Tuple[str, ...]"            # ECUs never sent 04 (SRS, by construction)
    codes: "Dict[str, Tuple[str, ...]]"     # stored and pending codes per ECU to clear
    safety: "Tuple[str, ...]"               # codes or ECUs that trigger the warning
    confirmation: str
    warning: "str | None" = None

    @property
    def code_count(self) -> int:
        return sum(len(c) for c in self.codes.values())

    def to_dict(self) -> dict:
        return {"ecus": list(self.ecus), "read_only": list(self.read_only),
                "codes": {e: list(c) for e, c in self.codes.items()},
                "safety": list(self.safety), "confirmation": self.confirmation,
                "warning": self.warning}


def is_safety_code(code: str) -> bool:
    """A code from a safety system by its J2012 category: chassis ``C`` codes (ABS, brakes,
    stability, steering) and body ``B00xx`` codes (restraints / airbag)."""
    return code[:1] == "C" or code[:3] == "B00"


def plan(reads: "Iterable[DtcRead]", *, ecus: "Iterable[str]" = (),
         names: "Optional[Mapping[str, str]]" = None,
         safety_ecus: "Iterable[str]" = (), read_only_ecus: "Iterable[str]" = ()) -> ClearPlan:
    """Build the clear plan and its single confirmation (spec §5.1–5.2).

    ``reads`` are the current 03/07/0A reads; ``ecus`` adds ECUs known from discovery that
    reported no codes (a clear still resets their readiness). ``safety_ecus`` and
    ``read_only_ecus`` come from the pack's tags."""
    names = dict(names or {})
    ro = set(read_only_ecus)
    safety_tags = set(safety_ecus)
    codes: "Dict[str, list]" = {}
    permanent = 0
    reads = list(reads)
    for r in reads:
        if r.ecu in ro:
            continue
        if r.kind == "permanent":
            permanent += len(r.dtcs)
            codes.setdefault(r.ecu, [])
            continue
        lst = codes.setdefault(r.ecu, [])
        for d in r.dtcs:
            if d.code not in lst:
                lst.append(d.code)
    for e in ecus:
        if e not in ro:
            codes.setdefault(e, [])
    targets = tuple(sorted(codes))
    safety = sorted({c for e in targets for c in codes[e] if is_safety_code(c)}
                    | {e for e in targets if e in safety_tags})
    n = sum(len(v) for v in codes.values())
    who = ", ".join(names.get(e, f"ECU {e}") for e in targets) or "no ECU"
    text = (f"Clear {n} code{'s' if n != 1 else ''} ({who})? Freeze frames and readiness "
            "monitors will be reset; permanent codes stay. A snapshot is saved to the "
            "logbook first.")
    if permanent:
        text += f" {permanent} permanent code{'s' if permanent != 1 else ''} will remain."
    # Every read-only ECU the pack names is listed, present or not: with any listed, the
    # clear goes out physically per ECU, so a functional 04 can never reach one.
    return ClearPlan(targets, tuple(sorted(ro)),
                     {e: tuple(codes[e]) for e in targets}, tuple(safety), text,
                     SAFETY_WARNING if safety else None)


@dataclass(frozen=True)
class ClearGrant:
    """Short-lived and single-use; minted only by :meth:`ClearGate.authorize`."""

    id: str
    plan: ClearPlan
    context: ClearContext
    issued: float
    expires: float
    category: str = CATEGORY
    tier: int = TIER


def remote_override_from_env(env: "Mapping[str, str] | None" = None) -> bool:
    env = os.environ if env is None else env
    return str(env.get(REMOTE_OVERRIDE_ENV, "")).strip().lower() in _TRUE


@dataclass
class ClearGate:
    """The clear policy (spec §5.1). ``allow_remote`` is fixed when the gate is built (from
    the environment or install config by default); there is no setter."""

    clock: Callable[[], float] = time.time
    ttl: float = 60.0
    audit: "Optional[Callable[[dict], object]]" = None
    allow_remote: "bool | None" = None
    _issued: "Dict[str, ClearGrant]" = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.allow_remote is None:
            self.allow_remote = remote_override_from_env()
        object.__setattr__(self, "_allow_remote", bool(self.allow_remote))

    def __setattr__(self, name, value) -> None:
        if name in ("allow_remote", "_allow_remote") and "_allow_remote" in self.__dict__:
            raise AttributeError("the remote-control override is install-level and fixed")
        super().__setattr__(name, value)

    @property
    def remote_allowed(self) -> bool:
        return self._allow_remote  # type: ignore[attr-defined]

    def check(self, ctx: ClearContext, plan_: ClearPlan, *, confirmed: bool) -> None:
        """Raise :class:`ClearRefused` when a rule fails (no audit; see authorize)."""
        if ctx.driving_state not in CLEAR_STATES:
            raise ClearRefused("moving", "Clearing codes needs the car parked or idling.")
        if not ctx.user or ctx.role == "kiosk":
            raise ClearRefused("not_signed_in", "Sign in to clear codes.")
        cats = ctx.categories
        allowed = (CATEGORY in cats) if cats is not None else ctx.role in MAINTENANCE_ROLES
        if not allowed:
            raise ClearRefused("role", "Your role does not allow clearing codes.")
        if ctx.link not in LOCAL_LINKS and not self.remote_allowed:
            raise ClearRefused("remote", "Codes can be cleared only over a local link "
                                         "(the head unit, the in-car network, the node's "
                                         "Wi-Fi or Bluetooth).")
        if not plan_.ecus:
            raise ClearRefused("read_only", "No ECU can be cleared (read-only systems "
                                            "are never cleared).")
        if not confirmed:
            raise ClearRefused("unconfirmed", "Clearing codes needs one confirmation.")

    def authorize(self, ctx: ClearContext, plan_: ClearPlan, *,
                  confirmed: bool) -> ClearGrant:
        """Check every rule and mint a grant, or audit the refusal and raise."""
        try:
            self.check(ctx, plan_, confirmed=confirmed)
        except ClearRefused as exc:
            self._audit({"outcome": "refused", "stage": "gate", "reason": exc.code,
                         **ctx.to_dict(), "ecus": list(plan_.ecus),
                         "codes": {e: list(c) for e, c in plan_.codes.items()}})
            raise
        now = self.clock()
        g = ClearGrant(secrets.token_hex(8), plan_, ctx, now, now + self.ttl)
        self._issued[g.id] = g
        return g

    def redeem(self, grant: "ClearGrant | None", *,
               driving_state: "str | None" = None) -> ClearGrant:
        """Verify and consume a grant at execution (the node re-check). Raises
        :class:`ClearRefused` (the caller audits it)."""
        if grant is None or not isinstance(grant, ClearGrant):
            raise ClearRefused("no_grant", "Clearing codes needs a grant from the gate.")
        mine = self._issued.pop(grant.id, None)
        if mine is None or mine is not grant:
            raise ClearRefused("grant_used", "This clear was already used or not issued here.")
        if self.clock() > grant.expires:
            raise ClearRefused("grant_expired", "The confirmation expired; confirm again.")
        state = driving_state if driving_state is not None else grant.context.driving_state
        if state not in CLEAR_STATES:
            raise ClearRefused("moving", "Clearing codes needs the car parked or idling.")
        if grant.context.link not in LOCAL_LINKS and not self.remote_allowed:
            raise ClearRefused("remote", "Codes can be cleared only over a local link.")
        return grant

    def _audit(self, entry: dict) -> None:
        if self.audit is not None:
            self.audit({"type": "obd_clear", "t": self.clock(), **entry})


# --------------------------------------------------------- logbook adapters -- #

def recorder_snapshot_sink(recorder) -> "Callable[[dict], str]":
    """A snapshot sink over a ``SessionRecorder``: writes a ``obd_before_clear`` event and
    returns a link (``<session id>#<event t>``). Raises when nothing was written, which
    blocks the clear (spec §5.3)."""
    def sink(snapshot: dict) -> str:
        line = recorder.event("obd_before_clear", **snapshot)
        if not line:
            raise ObdError("no logbook session is recording")
        return f"{recorder.session_id}#{line.get('t')}"
    return sink


def recorder_audit_sink(recorder) -> "Callable[[dict], object]":
    """An audit sink over a ``SessionRecorder`` (``obd_clear_audit`` events)."""
    def sink(entry: dict) -> object:
        fields = {k: v for k, v in entry.items() if k not in ("type", "t")}
        return recorder.event("obd_clear_audit", **fields)
    return sink


__all__ = ["PARKED", "IDLING", "MOVING", "LOCAL_LINKS", "MAINTENANCE_ROLES",
           "REMOTE_OVERRIDE_ENV", "SAFETY_WARNING", "NRC22_MESSAGE", "PERMANENT_NOTE",
           "ClearRefused", "ClearContext", "ClearPlan", "ClearGrant", "ClearGate", "plan",
           "is_safety_code", "remote_override_from_env", "recorder_snapshot_sink",
           "recorder_audit_sink", "CATEGORY", "TIER"]
