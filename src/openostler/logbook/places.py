# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Session place names (ADR-0011; spec 2026-10-06-logs-at-scale §2). Core: never imports web.

The meta fields ``place_start`` / ``place_end`` are ``{label, source}`` (``source`` is
``"geonames"`` offline, ``"osm"`` after enrichment, which keeps the offline label as
``label_offline``); ``place`` is ``place_start``, else ``place_end``. ``geo.offline`` is
imported lazily: when it (or its data file) is unavailable, ``places_for`` returns None
and the caller leaves the fields unset so a later pass can fill them.
"""
from __future__ import annotations

PLACE_KEYS = ("place_start", "place_end", "place")


class PlacesUnavailable(RuntimeError):
    """The offline gazetteer (``geo.offline``) cannot be used."""


def _label_fn():
    try:
        from ..geo import offline  # noqa: PLC0415 — lazy: the gazetteer loads on demand
    except Exception as exc:  # noqa: BLE001
        raise PlacesUnavailable(str(exc)) from None
    fn = getattr(offline, "label", None)
    if not callable(fn):
        raise PlacesUnavailable("geo.offline.label is missing")
    return fn


def offline_place(pos) -> "dict | None":
    """``[lon, lat]`` → ``{label, source: "geonames"}`` or None (no position, at sea).
    Raises ``PlacesUnavailable`` when the gazetteer cannot be used."""
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return None
    try:
        lon, lat = float(pos[0]), float(pos[1])
    except (TypeError, ValueError):
        return None
    fn = _label_fn()
    try:
        hit = fn(lat, lon)
    except Exception as exc:  # noqa: BLE001 — e.g. places.tsv.gz not built yet
        raise PlacesUnavailable(f"{type(exc).__name__}: {exc}") from None
    if not isinstance(hit, dict) or not hit.get("label"):
        return None
    return {"label": str(hit["label"]), "source": str(hit.get("source") or "geonames")}


def places_for(start_pos, end_pos) -> "dict | None":
    """``{place_start, place_end, place}`` for the given positions, or None when the
    gazetteer is unavailable (leave the meta untouched then)."""
    try:
        start = offline_place(start_pos)
        end = offline_place(end_pos)
    except PlacesUnavailable:
        return None
    return {"place_start": start, "place_end": end, "place": start or end}


def combined(meta: dict) -> "dict | None":
    """The ``place`` value implied by ``place_start``/``place_end``."""
    return meta.get("place_start") or meta.get("place_end") or None


__all__ = ["PLACE_KEYS", "PlacesUnavailable", "offline_place", "places_for", "combined"]
