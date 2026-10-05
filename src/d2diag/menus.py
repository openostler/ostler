"""Module menu registry: every function per module, from the active vehicle pack (ADR-0008).

The menus themselves are pack data (``VehiclePack.menus``: ``{module id: [group, …]}`` in
display order). Each group (``id``, ``page``, ``cat``, optional ``parent`` and ``nanocom``)
holds items that link a signal-store field (``sig``), registry actions (``actions``) or,
when unlinked, carry a hand ``status``. :mod:`d2diag.catalog` derives each item's status
and safety from those links and serves ``/catalog``; the admin Map tab keeps its legacy
shape through :func:`d2diag.catalog.legacy_menu`.

``MENUS`` is resolved on access (module ``__getattr__``), never at import time, so tests
can switch the active pack.
"""
from __future__ import annotations

from .pack import active_pack, canonical_module


def menus() -> "dict[str, list]":
    """The active pack's menus mapping (``{module id: [group, …]}``)."""
    return active_pack().menus


def menu_for(module: str) -> "list":
    """The menu groups of a module id or alias (``[]`` for an unknown module)."""
    return active_pack().menus.get(canonical_module(module), [])


def __getattr__(name: str):
    if name == "MENUS":
        return active_pack().menus
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
