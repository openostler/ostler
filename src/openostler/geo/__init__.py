# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Place names for sessions (ADR-0011; spec 2026-10-06-logs-at-scale §2). Core: never imports web.

Contract:
* ``offline.label(lat, lon) -> {"label", "town", "region", "country", "dist_km",
  "source": "geonames"} | None`` — nearest town within a population-scaled reach
  (≥50k 25 km, ≥5k 15 km, ≥1k 8 km, else 3 km; largest qualifying wins), "Town, Region"
  within 1 km, "near Town, Region" within reach, else "Region, Country" (admin2→admin1 of the
  nearest point), "Country" within 100 km, else None. Data: ``places.tsv.gz`` (GeoNames
  cities1000, CC BY 4.0) built by ``tools/build_places.py``; loaded lazily once.
* ``nominatim.Enricher(url, cache_path, user_agent=USER_AGENT)``: ``start()``, ``stop()``,
  ``submit(key, lat, lon, callback(key, label_or_None))``, ``cached(lat, lon) -> str | None``;
  ≤1 request/s, cache keyed by lat/lon rounded to 3 dp, backoff 60 s → 1 h; ``url=None`` = off.
* ``ATTRIBUTION`` — "Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)".
"""

from . import nominatim, offline  # noqa: E402  (offline data loads lazily on first label())
from .nominatim import USER_AGENT, Enricher  # noqa: E402
from .offline import label  # noqa: E402

ATTRIBUTION = "Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)"

__all__ = ["ATTRIBUTION", "Enricher", "USER_AGENT", "label", "nominatim", "offline"]
