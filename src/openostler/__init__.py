# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Ostler — the open vehicle platform (OpenOstler).

The vehicle-agnostic layers, built bottom-up:

    Transport  →  K-Line  →  KWP2000  →  session  →  signals / logbook  →  web

Everything vehicle-specific comes from a *vehicle pack* resolved through
:func:`openostler.pack.active_pack` (entry-point group ``openostler.vehicle``, ADR-0013,
ADR-0014). The platform never imports a pack. See README.
"""
__version__ = "0.0.1"
