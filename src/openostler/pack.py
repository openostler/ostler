# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The VehiclePack contract: everything vehicle-specific, behind one object (ADR-0013).

The platform (comms core, catalog, commands, logbook, server) is generic. A *vehicle
pack* supplies the modules, their data stores, actions, menus, fault readers, sniff
detection, demo data, docs and the UI layout. Platform code asks :func:`active_pack` for
them and never imports a pack directly.

Pack resolution (:func:`active_pack`, cached, always lazy, never at import time):

1. a pack set with :func:`set_active_pack` / :func:`use_pack` (tests) wins;
2. otherwise the ``openostler.vehicle`` entry points (legacy ``ostler.vehicle`` also read): ``OSTLER_VEHICLE`` picks one by name (or
   names a ``module:attr`` directly); without it there must be exactly one;
3. with no entry point at all, a :class:`NoVehiclePackError` that names the group and
   how to install a pack (the Phase 0 built-in fallback was removed at the repo split,
   ADR-0015).

See ``specs/2026-10-06-phase0-vehiclepack-decoupling-design.md`` §1. This module never
imports a vehicle pack by name.
"""
from __future__ import annotations

import contextlib
import importlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Iterator, Mapping, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover
    from .commands import Command
    from .kline.profiles import KLineProfile

PACK_API_VERSION = 1
ENTRY_POINT_GROUP = "openostler.vehicle"
# Read too, for one release: the group name used before ADR-0014.
LEGACY_ENTRY_POINT_GROUPS = ("ostler.vehicle",)
ENV_VAR = "OSTLER_VEHICLE"
# Shown when no pack is installed: the reference pack and how to install it.
INSTALL_HINT = ('pip install "d2diag @ git+https://github.com/openostler/ostler-pack-lr-d2" '
                '(the Land Rover Discovery 2 pack), or any package registering an '
                f'"{ENTRY_POINT_GROUP}" entry point')


class NoVehiclePackError(LookupError):
    """No vehicle pack is installed (no ``openostler.vehicle`` entry point)."""


# ------------------------------------------------------------------ contract -- #

@dataclass(frozen=True)
class ModuleSpec:
    """One ECU of the vehicle. ``id`` is canonical: it is the store id
    (``signals/<id>.json``, ``dtc/<id>.json``) and ``Command.module``."""

    id: str
    name: str                                   # display name, e.g. "TD5 (engine)"
    address: Optional[int] = None               # K-line diagnostic address (0x13)
    init: str = "none"                          # "fast" | "slow" | "none" (proprietary/unknown)
    keygen: Optional[Callable[[int, int], bytes]] = None   # seed (hi, lo) → key bytes
    aliases: Tuple[str, ...] = ()               # legacy ids accepted on read ("motor")
    live: bool = True                           # False → an InfoDataSource (no live reader)
    fault_label: str = ""                       # faultscan row label ("TD5")
    # K-line profile overrides (spec K-line profiles §1): any KLineProfile field, a nested
    # "timing" mapping, or "base" naming another built-in. Empty → the built-in for
    # ``init``. The future pack manifest's ``transport`` block carries the same keys.
    kline: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}),
                                     hash=False, compare=False)

    def kline_profile(self) -> "KLineProfile | None":
        """This module's K-line profile: the base from ``init`` (``fast`` →
        ``kwp2000_fast``, ``slow`` → ``kwp2000_slow``, ``none`` → no profile),
        ``init_address``/``target`` from ``address``, then :attr:`kline`; named after
        the module id. Raises ValueError for an invalid override."""
        from .kline.profiles import profile_for_module

        return profile_for_module(self.id, self.address, self.init, self.kline)


@dataclass(frozen=True)
class FaultReader:
    """One row of "read all fault codes". ``read(real_port)`` owns establish/release.
    ``note`` goes on the row; ``error_note`` (default: ``note``) on an error row."""

    label: str
    read: Callable[[str], "list[str]"]
    note: str = ""
    error_note: Optional[str] = None


@dataclass(frozen=True)
class Detector:
    """A sniff detector: ``match(bytes_line)`` → this line belongs to ``module``."""

    module: str
    how: str
    match: Callable[["list[int]"], bool]


@dataclass(frozen=True)
class SniffSpec:
    fast_init: Mapping[int, str]
    slow_init: Mapping[int, str]
    extra_scan: Tuple[int, ...] = ()            # modscan DEFAULT_SLOW extras
    authoritative: Tuple[Detector, ...] = ()    # always switch the active module
    hints: Tuple[Detector, ...] = ()            # seed only when no module is known yet
    tester: int = 0xF7
    importers: Mapping[str, Callable] = field(default_factory=dict)


@dataclass(frozen=True)
class DemoSpec:
    sessions_dir: Path                          # committed synthetic sessions
    # Test-only: a sniff log the test server (tests/e2e_server.py --replay) loops into the
    # Decode tab. The product never replays it; it reads only a live sniffer (ADR-0011).
    sniff_log: Optional[Path] = None
    generate: Optional[Callable[[str], "list[str]"]] = None   # generate(root) → [session id]


@dataclass(frozen=True)
class DocSource:
    path: Path
    group: str
    title: Optional[str] = None
    recursive: bool = False
    exclude: frozenset = frozenset()
    optional: bool = False                      # a missing path is skipped silently


@dataclass(frozen=True)
class VehiclePack:
    id: str
    name: str
    api_version: int
    modules: Tuple[ModuleSpec, ...]
    default_module: str
    # sources(port, *, raw_log_dir=None, state_dir=None) → {module id: DataSource},
    # in ``modules`` order.
    sources: Callable[..., "dict[str, Any]"]
    signals_dir: Path
    dtc_dir: Path
    actions: Tuple["Command", ...]
    menus: Mapping[str, list]
    unlinked_ok: Mapping[str, frozenset]
    derived_fields: Mapping[str, Mapping[str, dict]]
    writable_signal_modules: Tuple[str, ...]
    module_command_prefixes: Tuple[str, ...]
    faultscan: Tuple[FaultReader, ...]
    faultscan_unimplemented: Tuple[Tuple[str, str], ...]
    sniff: SniffSpec
    demo: Optional[DemoSpec]
    docs: Tuple[DocSource, ...]
    layout: Mapping[str, Any]                   # the UI manifest (``layout.json``)
    root: Path                                  # repo/data root for relative paths

    def module(self, mid: "str | None") -> "ModuleSpec | None":
        """The module for an id or alias (case-insensitive), or None."""
        cid = self.canonical(mid)
        for m in self.modules:
            if m.id == cid:
                return m
        return None

    def module_ids(self) -> "list[str]":
        return [m.id for m in self.modules]

    def aliases(self) -> "dict[str, str]":
        """``{legacy alias: canonical id}``."""
        return {a.lower(): m.id for m in self.modules for a in m.aliases}

    def canonical(self, mid: "str | None") -> "str | None":
        """Canonical id for ``mid``: lower-cased, an alias mapped to its id. An unknown id
        is returned unchanged; ``None`` stays ``None``."""
        if mid is None:
            return None
        key = str(mid).strip().lower()
        if key in self.module_ids():
            return key
        alias = self.aliases().get(key)
        if alias is not None:
            return alias
        return mid

    def manifest(self) -> dict:
        """The ``GET /pack`` body."""
        return {
            "id": self.id,
            "name": self.name,
            "api_version": self.api_version,
            "default_module": self.default_module,
            "modules": [{"id": m.id, "name": m.name, "aliases": list(m.aliases), "live": m.live}
                        for m in self.modules],
            "aliases": self.aliases(),
            "layout": dict(self.layout),
        }


# -------------------------------------------------------------------- loader -- #

_override: "VehiclePack | None" = None
_cached: "VehiclePack | None" = None


def _entry_points() -> list:
    """The ``openostler.vehicle`` entry points (plus the legacy ``ostler.vehicle`` group),
    de-duplicated (Python 3.9+)."""
    from importlib import metadata

    eps = metadata.entry_points()
    found = []
    for group in (ENTRY_POINT_GROUP, *LEGACY_ENTRY_POINT_GROUPS):
        if hasattr(eps, "select"):         # Python 3.10+
            found += list(eps.select(group=group))
        else:                              # Python 3.9: a dict of group → entry points
            found += list(eps.get(group, ()))
    out, seen = [], set()
    for ep in found:
        key = (ep.name, ep.value)
        if key not in seen:
            seen.add(key)
            out.append(ep)
    return out


def _load_ref(ref: str):
    """Load a ``module:attr`` reference."""
    mod_name, _, attr = ref.partition(":")
    obj = importlib.import_module(mod_name)
    for part in (attr.split(".") if attr else []):
        obj = getattr(obj, part)
    return obj


def _check(pack, where: str) -> VehiclePack:
    if not isinstance(pack, VehiclePack):
        raise TypeError(f"{where} is not a VehiclePack (got {type(pack).__name__})")
    if pack.api_version != PACK_API_VERSION:
        raise RuntimeError(f"{where}: pack api_version {pack.api_version} != "
                           f"platform {PACK_API_VERSION}")
    return pack


def _resolve() -> VehiclePack:
    eps = _entry_points()
    want = os.environ.get(ENV_VAR, "").strip()
    if want:
        for ep in eps:
            if ep.name == want:
                return _check(ep.load(), f"entry point {ep.name!r}")
        if ":" in want:
            return _check(_load_ref(want), f"{ENV_VAR}={want!r}")
        names = ", ".join(sorted(ep.name for ep in eps)) or "none"
        raise LookupError(f"{ENV_VAR}={want!r} names no {ENTRY_POINT_GROUP!r} entry point "
                          f"(installed: {names})")
    if len(eps) == 1:
        return _check(eps[0].load(), f"entry point {eps[0].name!r}")
    if len(eps) > 1:
        names = ", ".join(sorted(f"{ep.name} ({ep.value})" for ep in eps))
        raise RuntimeError(f"several {ENTRY_POINT_GROUP!r} vehicle packs are installed: {names}; "
                           f"set {ENV_VAR} to pick one")
    raise NoVehiclePackError(
        f"no vehicle pack installed: no {ENTRY_POINT_GROUP!r} entry point found. "
        f"Install one, e.g. {INSTALL_HINT}; or set {ENV_VAR}=module:attr")


_resolving = False


def active_pack() -> VehiclePack:
    """The vehicle pack in use (resolved on first call, then cached)."""
    global _cached, _resolving
    if _override is not None:
        return _override
    if _cached is None:
        if _resolving:
            raise RuntimeError(
                "vehicle pack resolution re-entered: building a pack must not import code "
                "that reads a store at import time (keep such members lazy)")
        _resolving = True
        try:
            _cached = _resolve()
        finally:
            _resolving = False
    return _cached


def set_active_pack(pack: "VehiclePack | None") -> None:
    """Force a pack (tests); ``None`` restores normal resolution and drops the cache."""
    global _override, _cached
    _override = pack
    _cached = None


@contextlib.contextmanager
def use_pack(pack: VehiclePack) -> Iterator[VehiclePack]:
    """Run a block with ``pack`` active, restoring the previous state afterwards."""
    global _override, _cached
    prev_override, prev_cached = _override, _cached
    _override = pack
    try:
        yield pack
    finally:
        _override, _cached = prev_override, prev_cached


def canonical_module(mid: "str | None") -> "str | None":
    """``active_pack().canonical(mid)``: a legacy alias → its canonical module id."""
    return active_pack().canonical(mid)


__all__ = [
    "PACK_API_VERSION", "ENTRY_POINT_GROUP", "LEGACY_ENTRY_POINT_GROUPS", "ENV_VAR",
    "NoVehiclePackError", "ModuleSpec", "FaultReader", "Detector",
    "SniffSpec", "DemoSpec", "DocSource", "VehiclePack", "active_pack", "set_active_pack",
    "use_pack", "canonical_module",
]
