"""Command registry: every module action the dashboard can send, with its status and safety.

The single source of truth for **what an action is** (ADR-0008,
specs/2026-10-05-ui-overhaul-design.md):

* ``status``:
  * ``verified``: run against the car and confirmed;
  * ``experimental``: implemented but unproven on the car;
  * ``planned``: known from the NanoCom, not wired, never runnable.
* ``safety``:
  * ``read``: reads only;
  * ``actuator``: a short output test;
  * ``service``: a multi-step or latched procedure;
  * ``gated``: never sent by this project (security, coding, airbag, calibration writes).
* ``confirm``: the friction the UI applies. ``none``; ``preconditions`` (a checklist the
  user ticks); ``typed`` (the user types the item name).

The server refuses unknown, gated, planned and (without ``trust=experimental``)
experimental actions; the catalog (:mod:`openostler.catalog`) derives each menu item's status
from the actions it links to. The rows themselves come from the active vehicle pack
(``VehiclePack.actions``); :func:`registry` indexes them per pack. Data only: no I/O, no
web imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field

STATUSES = ("verified", "experimental", "planned")
SAFETIES = ("read", "actuator", "service", "gated")
CONFIRMS = ("none", "preconditions", "typed")

# Preconditions shown before an actuator or service action (the UI ticks them off).
STATIONARY = ("Vehicle stationary, handbrake on", "Ignition on", "Nobody under or beside the car")


@dataclass(frozen=True)
class Command:
    action: str                 # the /command action string (module-scoped)
    module: str                 # canonical (store) module id of the vehicle pack
    label: str
    status: str = "experimental"
    safety: str = "actuator"
    confirm: str = "preconditions"
    preconditions: "tuple[str, ...]" = field(default=STATIONARY)
    stop: "str | None" = None   # action that ends a latched test (shown on the banner)
    ref: str = ""               # the K-line request, for reference

    def as_dict(self) -> dict:
        d = {"action": self.action, "label": self.label, "status": self.status,
             "safety": self.safety, "confirm": self.confirm,
             "preconditions": list(self.preconditions), "ref": self.ref}
        if self.stop:
            d["stop"] = self.stop
        return d


# The registry of the active vehicle pack, built once per pack: {id(pack): (pack, registry)}.
# The pack object is held so its id cannot be reused while the entry lives.
_REGISTRIES: "dict[int, tuple[object, dict[tuple[str, str], Command]]]" = {}


def registry() -> "dict[tuple[str, str], Command]":
    """``{(module, action): Command}`` for the active vehicle pack's actions (cached per
    pack; the same dict object is returned on every call for that pack)."""
    from .pack import active_pack

    pack = active_pack()
    hit = _REGISTRIES.get(id(pack))
    if hit is None or hit[0] is not pack:
        hit = (pack, {(c.module, c.action): c for c in pack.actions})
        _REGISTRIES[id(pack)] = hit
    return hit[1]


def __getattr__(name: str):
    # ``REGISTRY`` stays reachable for old callers: the active pack's registry().
    if name == "REGISTRY":
        return registry()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get(module: str, action: str) -> "Command | None":
    """The registered command for a store module + action, or None."""
    return registry().get((module, action))


def for_module(module: str) -> "list[Command]":
    """The active pack's actions for a store module, in pack order."""
    from .pack import active_pack

    return [c for c in active_pack().actions if c.module == module]


def refusal(module: str, action: str, trust: str = "", public: bool = False) -> "str | None":
    """Why the server must refuse this action (None = allowed). Pure policy, no I/O.

    Only *module* actions are judged here; server-level actions (select_module, csv,
    connect, read_block, clear_faults …) are not module commands and return None.
    """
    c = get(module, action)
    if c is None:
        return None
    if c.safety == "gated":
        return f"{c.label} is gated: never sent by this project"
    if c.status == "planned":
        return f"{c.label} is not implemented yet"
    if public and c.safety in ("actuator", "service"):
        return "actuator and service actions are disabled on the public server"
    if c.status == "experimental" and trust != "experimental":
        return f"{c.label} is experimental: enable Experimental mode to run it"
    return None
