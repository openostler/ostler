# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NodeSource: the Brain reads the car through the node's MQTT messages (NodeSource spec,
phase P1: read-only ingest).

- :class:`NodeFeed` owns one MQTT 5 connection (``openostler.mqtt``) to the Brain's broker
  (or, in the lab, the node's), subscribes read-only to ``status``, ``power`` and ``vss/+``
  of one ``vid`` (spec §4: No Local on, Retain As Published off, Retain Handling 0, clean
  start with session expiry 0) and fills a :class:`~openostler.node.DeviceTable` from the
  MQTT thread. It reconnects with jittered back-off (1 s doubling to 30 s).
- :class:`NodeSource` is a :class:`DataSource` per pack module over one shared feed:
  ``poll()`` builds the snapshot from the table under its lock and never blocks.
  Selecting a module only filters the view; the node keeps its own rotation.

The Brain never touches the car (ADR-0032): nothing here opens a serial port, imports a
transport or publishes a request (requests are P4). It is read-only: it publishes nothing.
"""
from __future__ import annotations

import socket
import sys
import threading
import time
from typing import Callable, Optional

from ..mqtt import MqttClient, StdlibMqttClient, SubOptions
from ..node import FAULTS_NOTE, DeviceTable, check_vid, subscriptions
from .sources import DataSource

KEEP_ALIVE_S = 10
MQTT_PORT, MQTTS_PORT = 1883, 8883

# Spec §10: snapshot status → conn.
_CONN_FOR = {"broker-down": "lost", "connecting": "connecting", "error": "lost",
             "asleep": "disconnected", "connected": "connected"}


def parse_mqtt_url(url: str) -> "tuple[str, str, int]":
    """``mqtt[s]://host[:port]`` → ``(scheme, host, port)``; raises ValueError."""
    scheme, sep, rest = (url or "").partition("://")
    if not sep or scheme not in ("mqtt", "mqtts") or not rest:
        raise ValueError(f"expected mqtts://host[:port] (or mqtt:// for a lab broker): {url!r}")
    rest = rest.rstrip("/")
    if rest.startswith("["):  # [IPv6]:port
        host, _, port = rest[1:].partition("]")
        port = port.lstrip(":")
    else:
        host, _, port = rest.rpartition(":") if rest.count(":") == 1 else (rest, "", "")
    if not host or "/" in host:
        raise ValueError(f"no broker host in {url!r}")
    return scheme, host, int(port) if port else (MQTTS_PORT if scheme == "mqtts" else MQTT_PORT)


def store_lookup() -> "Callable[[str, str], Optional[tuple]]":
    """``(module, field) → (confidence, limits)`` from the Brain's installed pack store.
    Confidence is the lowest of the field's records (a field with reply-length layouts may
    have several), so the store never raises the node's level."""
    from ..signals import load_signals

    cache: "dict[str, dict]" = {}

    def lookup(module: str, name: str):
        if module not in cache:
            table: dict = {}
            try:
                for s in load_signals(module):
                    c, lim = table.get(s.name, (None, None))
                    conf = ("proven" if s.confidence == "proven" and c in (None, "proven")
                            else "candidate")
                    table[s.name] = (conf, lim if lim is not None else s.limits)
            except (OSError, ValueError, KeyError, LookupError):
                table = {}
            cache[module] = table
        return cache[module].get(name)

    return lookup


class NodeFeed:
    """One read-only MQTT connection and the device table it fills."""

    def __init__(self, vid: str, host: str, port: int, *,
                 client: "MqttClient | None" = None, client_id: "str | None" = None,
                 ssl_context=None, pack_id: "str | None" = None,
                 lookup=None, canonical=None, is_known=None,
                 clock: Callable[[], float] = time.monotonic,
                 wall: Callable[[], float] = time.time,
                 log: "Callable[[str], None] | None" = None) -> None:
        self.vid = check_vid(vid)
        self.host, self.port = host, port
        self._clock, self._wall = clock, wall
        self.log = log or (lambda msg: print(f"node: {msg}", file=sys.stderr))
        self.table = DeviceTable(self.vid, pack_id=pack_id, lookup=lookup,
                                 canonical=canonical, is_known=is_known,
                                 log=lambda m: self.log(m))
        if client is None:
            cid = client_id or f"{socket.gethostname().split('.')[0]}-nodesource"
            client = StdlibMqttClient(cid, keep_alive=KEEP_ALIVE_S, clean_start=True,
                                      session_expiry=0, ssl_context=ssl_context)
        self.client = client
        self.refused: "list[str]" = []
        self.attempted = False  # a connection was tried (so "down" means down, not "starting")
        self._lock = threading.Lock()
        client.on_message = self._on_message
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        start = getattr(self.client, "start", None)
        if start is None:
            raise TypeError("the MQTT client cannot run in the background")
        start(self.host, self.port)

    def stop(self) -> None:
        stop = getattr(self.client, "stop", None)
        if stop is not None:
            stop()
        else:
            self.client.disconnect()

    def subscription_options(self) -> "list[SubOptions]":
        # No Local on; Retain As Published off so a retain flag means "stored value sent at
        # subscribe time"; Retain Handling 0 so every (re)subscribe rebuilds the state.
        return [SubOptions(f, qos, no_local=True, retain_as_published=False, retain_handling=0)
                for f, qos in subscriptions(self.vid)]

    def _on_connect(self, _ack) -> None:
        self.attempted = True
        # Clean start: the retained topics rebuild each device's status and power; until
        # they arrive nothing from before the reconnect is taken as current. Values stay,
        # with their age.
        self.table.forget_liveness()
        subs = self.subscription_options()
        codes = self.client.subscribe(subs)
        refused = [s.topic_filter for s, c in zip(subs, codes) if c >= 0x80]
        with self._lock:
            self.refused = refused
        for f in refused:
            self.log(f"the broker refused the subscription {f} (check the ACL, spec §5)")
        self.log(f"connected to {self.host}:{self.port}, subscribed to vehicle {self.vid}")

    def _on_disconnect(self, reason: str) -> None:
        self.attempted = True
        self.log(f"broker connection lost: {reason}")

    def _on_message(self, pkt) -> None:
        self.table.ingest(pkt.topic, pkt.payload, pkt.retain, self._clock(), self._wall())

    @property
    def connected(self) -> bool:
        return bool(self.client.connected)

    def broker(self) -> dict:
        return {"connected": self.connected, "host": f"{self.host}:{self.port}"}

    def is_down(self) -> bool:
        if self.connected:
            return False
        return self.attempted or getattr(self.client, "last_error", None) is not None

    def view(self, module: "str | None") -> dict:
        return self.table.view(module, self._clock(), self._wall())


class NodeSource(DataSource):
    """One pack module's view of the node feed (spec §6, §10)."""

    source_kind = "node"
    touches_car = False  # never: the node reads the car (ADR-0032)

    def __init__(self, feed: NodeFeed, module: str) -> None:
        self.feed = feed
        self.name = module
        self.store_module = module
        self._last_status = "connecting"

    def is_connected(self) -> bool:
        return self._last_status == "connected"

    def conn_for(self, status: "str | None") -> "str | None":
        """The snapshot ``conn`` for this source's ``status`` (spec §10)."""
        return _CONN_FOR.get(status or "")

    def poll(self) -> dict:
        view = self.feed.view(self.name)
        dev = view["device"]
        broker = self.feed.broker()
        node = None
        if dev is not None:
            node = {**dev, "broker": broker, "tap": None}
        snap = {"source": self.name, "source_kind": "node", "signals": view["signals"],
                "vss": view["vss"], "faults": [], "faults_note": FAULTS_NOTE,
                "node": node or {"device": None, "status": None, "power": None, "boot": None,
                                 "last_seen_utc": None, "broker": broker, "tap": None},
                "devices": view["devices"]}
        state = ((dev or {}).get("power") or {}).get("state")
        if not broker["connected"]:
            snap["status"] = "broker-down" if self.feed.is_down() else "connecting"
            if snap["status"] == "broker-down":
                snap["error"] = "Brain cannot reach the broker"
        elif dev is None or dev.get("status") is None:
            snap["status"] = "connecting"
            snap["connect_phase"] = "waiting for the node"
        elif dev["status"] == "offline":
            snap["status"] = "error"
            snap["error"] = "Node offline"
        elif state == "asleep":
            snap["status"] = "asleep"
        elif state == "waking":
            snap["status"] = "connecting"
            snap["connect_phase"] = "waking"
        else:
            snap["status"] = "connected"
        if snap["status"] == "connected":
            live = [s for s in snap["signals"].values() if not s.get("stale")]
            if not live:
                snap["stale"] = True  # online, but not reading this module right now
        self._last_status = snap["status"]
        return snap

    def command(self, action: str, params: "dict | None" = None) -> dict:
        return {"ok": False, "code": "unavailable",
                "error": "the node takes no requests yet (read-only ingest; requests to the "
                         "node's gate come later)"}


def node_sources(feed: NodeFeed, modules: "list[str]") -> "dict[str, NodeSource]":
    """One :class:`NodeSource` per pack module, all over ``feed``."""
    return {m: NodeSource(feed, m) for m in modules}


def build_feed(url: str, vid: str, *, ca: "str | None" = None, cert: "str | None" = None,
               key: "str | None" = None, insecure_lab: bool = False,
               client_id: "str | None" = None, log=None) -> NodeFeed:
    """A feed for the active pack from a broker URL. ``mqtts://`` needs the CA and the
    client certificate and key (mTLS, spec §5; no passwords). Plain ``mqtt://`` is for a
    lab or test broker only and must be asked for with ``insecure_lab``."""
    from ..metrics import is_known
    from ..mqtt import tls_context
    from ..pack import active_pack

    scheme, host, port = parse_mqtt_url(url)
    ctx = None
    if scheme == "mqtts":
        if not (ca and cert and key):
            raise ValueError("mqtts:// needs --mqtt-ca, --mqtt-cert and --mqtt-key (mTLS)")
        ctx = tls_context(ca, cert, key)
    elif not insecure_lab:
        raise ValueError("plain mqtt:// is for a lab broker only: pass --mqtt-insecure-lab, "
                         "or use mqtts:// with a client certificate")
    pack = active_pack()
    return NodeFeed(vid, host, port, client_id=client_id, ssl_context=ctx, pack_id=pack.id,
                    lookup=store_lookup(), canonical=pack.canonical, is_known=is_known,
                    log=log)


__all__ = ["NodeFeed", "NodeSource", "build_feed", "node_sources", "parse_mqtt_url",
           "store_lookup"]
