# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The Brain's view of the nodes (specs/2026-10-06-node-source-design.md §3, §6, §10).

- :mod:`.messages`: node topics and payloads (status, power, VSS values), the P1
  subscription set and the VIN-shaped ``vid`` refusal.
- :mod:`.table`: the device table: staleness per signal, reboot detection, confidence
  never raised, range status from the Brain's pack store.
- :mod:`.select`: selection for one VSS path published by several sources.
- :mod:`.cluster`: the cluster view (devices, power, last seen, role holders and void
  claims; ADR-0037) and the serial-source rule beside a gate-holding node (P3).
- :mod:`.tap`: the raw-tap codec (headers, binary records) and the Brain-side identity
  scrub (ADR-0036).

Core layer, stdlib only, pure and clock-injected: no sockets here (the MQTT connection is
``web/node_source.py``'s), no ``web`` import, and no path to a car bus (ADR-0032).
"""
from .cluster import kline_gate_holders, serial_refusal
from .messages import (Topic, VssValue, check_vid, parse_claim, parse_manifest, parse_power,
                       parse_role_rest, parse_status, parse_tap_rest, parse_topic, parse_vss,
                       subscriptions, tap_subscriptions, vin_shaped)
from .select import select
from .table import FAULTS_NOTE, DeviceTable, lower_confidence, range_status

__all__ = [
    "FAULTS_NOTE", "DeviceTable", "Topic", "VssValue", "check_vid", "kline_gate_holders",
    "lower_confidence", "parse_claim", "parse_manifest", "parse_power", "parse_role_rest",
    "parse_status", "parse_tap_rest", "parse_topic", "parse_vss", "range_status", "select",
    "serial_refusal", "subscriptions", "tap_subscriptions", "vin_shaped",
]
