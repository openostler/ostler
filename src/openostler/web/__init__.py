# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web dashboard for real-time diagnostics (HTTP + SSE, stdlib).

`sources` holds the generic data-source boundary (``DataSource``, ``InfoDataSource``); the
vehicle pack supplies the car's readers (``active_pack().sources(...)``). `server` serves
the dashboard and streams snapshots via Server-Sent Events. There is no demo mode
(ADR-0011): simulated sources live only in ``tests/fake_sources.py``.
"""
from .sources import DataSource, InfoDataSource

__all__ = ["DataSource", "InfoDataSource"]
