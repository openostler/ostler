# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Per-trip sharing, phase TS1: the redaction pipeline, the widened identity scrub, the
``ostler.share/1`` bundle writer and ``ostler share verify``
(specs/2026-10-07-trip-sharing-design.md; ADR-0043, ADR-0036). Core: never imports ``web``.

- :func:`build_share` (``bundle.py``): one recorded session at one level (L0–L4) → a
  verified in-memory bundle; :func:`write_share` saves it (the File path).
- :func:`verify_bytes` / :func:`verify_bundle` (``verify.py``): the eight checks, exit codes
  0, 1 and 2.
- ``trace.py`` (ends trim, privacy zones, stats, simplification), ``zones.py`` (privacy
  zones with their fixed offsets), ``scrub.py`` (the tap scrub with ISO-TP reassembly),
  ``detect.py`` (VIN pattern and network identity), ``capture.py`` (pcapng and candump),
  ``ids.py`` (fresh ids and the owner's map).
"""
from __future__ import annotations

from .bundle import (ShareBlocked, ShareBundle, ShareOptions, ShareRefused, build_share,
                     check_policy, write_share)
from .verify import FORMAT, OwnerContext, VerifyResult, verify_bundle, verify_bytes
from .zones import PrivacyZone, ZoneStore

__all__ = ["FORMAT", "OwnerContext", "PrivacyZone", "ShareBlocked", "ShareBundle", "ShareOptions",
           "ShareRefused", "VerifyResult", "ZoneStore", "build_share", "check_policy",
           "verify_bundle", "verify_bytes", "write_share"]
