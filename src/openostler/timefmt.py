# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Wire timestamps: RFC 3339 date-times in UTC with a ``Z`` suffix, millisecond precision
(ADR-0017; specs/2026-10-06-api-consistency-design.md §4). Stdlib only.

Every wall-clock instant the platform puts on the wire or in a new file goes through
:func:`rfc3339_utc`, e.g. ``2026-10-05T09:00:00.000Z``.
"""
from __future__ import annotations

import time


def rfc3339_utc(epoch_s: float) -> str:
    """Seconds since the Unix epoch → ``YYYY-MM-DDTHH:MM:SS.mmmZ`` (rounded to the ms)."""
    ms = int(round(float(epoch_s) * 1000.0))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def rfc3339_utc_ms(epoch_ms: float) -> str:
    """Milliseconds since the Unix epoch → the same format (CSV ``Utc`` columns)."""
    ms = int(round(float(epoch_ms)))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def now_utc() -> str:
    """The current instant."""
    return rfc3339_utc(time.time())
