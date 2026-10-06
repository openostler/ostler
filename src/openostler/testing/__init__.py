# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Shipped test fakes (packs spec §2.9, J1979 spec §1), stdlib only, for the platform's
and the packs' tests. Never used at runtime."""
from .obd import FakeObdLink

__all__ = ["FakeObdLink"]
