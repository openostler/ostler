# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""MQTT 5 for the Brain, stdlib only (specs/2026-10-06-node-source-design.md §12).

- :mod:`.codec`: the packet codec (both directions; the test fake broker uses it too).
- :mod:`.client`: the :class:`MqttClient` interface and :class:`StdlibMqttClient`.

Core layer: imports nothing from ``web`` (``tests/test_layering.py``) and adds no runtime
dependency (ADR-0035; owner answer 1).
"""
from .client import MqttClient, StdlibMqttClient, tls_context
from .codec import (Connack, MqttError, Publish, SubOptions, Will, topic_matches,
                    valid_topic_filter, valid_topic_name)

__all__ = [
    "Connack", "MqttClient", "MqttError", "Publish", "StdlibMqttClient", "SubOptions", "Will",
    "tls_context", "topic_matches", "valid_topic_filter", "valid_topic_name",
]
