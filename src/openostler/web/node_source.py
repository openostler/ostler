# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NodeSource: the Brain reads the car through the node's MQTT messages (NodeSource spec,
phases P1 read-only ingest, P2 recording and raw tap, P3 Network page data).

- :class:`NodeFeed` owns one MQTT 5 connection (``openostler.mqtt``) to the Brain's broker
  (or, in the lab, the node's), subscribes read-only to ``status``, ``power``, ``vss/+``,
  ``manifest`` and ``role/#`` of one ``vid`` (spec §4: No Local on, Retain As Published
  off, Retain Handling 0, clean start with session expiry 0) and fills a
  :class:`~openostler.node.DeviceTable` from the MQTT thread. It reconnects with jittered
  back-off (1 s doubling to 30 s). :meth:`NodeFeed.cluster` is ``GET /cluster`` (spec §11).
- :class:`NodeSource` is a :class:`DataSource` per pack module over one shared feed:
  ``poll()`` builds the snapshot from the table under its lock and never blocks.
  Selecting a module only filters the view; the node keeps its own rotation.
- **The raw tap (P2).** While a session records, :meth:`NodeFeed.start_tap` opens a second
  connection (client id ``<id>-tap``, session expiry 60 s so a short Brain hiccup does not
  lose QoS 1 batches; clean start on each new run, resumed on reconnects) subscribed to
  ``tap/+/meta`` and ``tap/+/data``, and hands every message, with its MQTT 5 properties
  (a batch's content type and ``first_seq``, module-bus spec §8), to the recorder's sink;
  :meth:`NodeFeed.stop_tap` unsubscribes and closes it when the session ends (owner
  answer 9: no rolling buffer).
- **Faults and events (module-bus spec v1.3 §6.1, §6.2).** The read set includes
  ``faults/+`` and ``event/+`` at QoS 1 (and the alarm state at QoS 1, §6): the snapshot's
  ``faults`` come from the node's retained whole list (an absent topic is "not read"),
  and events are de-duplicated by ``id`` into a feed (``GET /cluster/events`` and its SSE
  stream).
- **Remove device (spec §7.2, §13).** :meth:`NodeFeed.remove_device` is the Brain's
  broker-host operation: it records the device as removed (the Brain ignores it from then
  on) and, over a separate broker-host connection (client id ``<id>-host``, its own
  credentials), publishes an empty retained message to each retained topic of
  ``ostler/v1/<vid>/<device>/#`` it has seen or finds there, then checks that none is
  left. The read connection never publishes.
- **The serial-source rule (P3, owner answer 7).** :func:`check_serial_beside_node` reads
  the vehicle's retained manifests and role claims once (:func:`probe_cluster`); a K-line
  cable source refuses to start when a node holds, or is wired to, the K-line gate.

The Brain never touches the car (ADR-0032): nothing here opens a serial port, imports a
transport or publishes a request (requests are P4). The read and tap connections publish
nothing; only Remove device's broker-host connection does, and only empty retained
messages under the removed device's own topics.
"""
from __future__ import annotations

import socket
import sys
import threading
import time
from typing import Callable, Optional

from ..mqtt import MqttClient, StdlibMqttClient, SubOptions
from ..node import (FAULTS_NOTE, DeviceTable, check_vid, parse_tap_rest, parse_topic,
                    serial_refusal, subscriptions, tap_subscriptions)
from ..node.removal import check_device, device_filter, gate_buses
from ..node.table import RETAINED_KINDS, utc
from .sources import DataSource

KEEP_ALIVE_S = 10
TAP_SESSION_EXPIRY_S = 60  # spec §4: a short Brain hiccup does not lose tap batches
TAP_RECEIVING_S = 5.0      # a batch within this long: the tap is "receiving"
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


def _allowed_values(path: str) -> "Optional[list]":
    """A VSS path's allowed values (metrics.json), e.g. the alarm state's four labels."""
    from ..metrics import metric_info

    allowed = (metric_info(path) or {}).get("allowed")
    return allowed if isinstance(allowed, list) else None


def store_primaries(modules: "list[str]") -> "Callable[[str], Optional[tuple]]":
    """``VSS path → (module, field)`` the Brain's installed pack store marks ``primary``
    (module-bus spec v1.3 §6), read once on first use; None for a path with no marker.
    A store the Brain cannot read marks nothing (the generic selection rule applies)."""
    from ..signals import primary_fields

    cache: "dict[str, tuple[str, str]] | None" = None

    def lookup(path: str):
        nonlocal cache
        if cache is None:
            try:
                cache = primary_fields(list(modules))
            except (OSError, ValueError, KeyError, LookupError):
                cache = {}
        return cache.get(path)

    return lookup


class NodeFeed:
    """One read-only MQTT connection and the device table it fills."""

    def __init__(self, vid: str, host: str, port: int, *,
                 client: "MqttClient | None" = None, client_id: "str | None" = None,
                 ssl_context=None, pack_id: "str | None" = None,
                 lookup=None, canonical=None, is_known=None,
                 clock: Callable[[], float] = time.monotonic,
                 wall: Callable[[], float] = time.time,
                 log: "Callable[[str], None] | None" = None,
                 tap_client: "Callable[[], MqttClient] | None" = None,
                 primary=None,
                 host_client: "Callable[[], MqttClient] | None" = None,
                 host_ssl_context=None) -> None:
        self.vid = check_vid(vid)
        self.host, self.port = host, port
        self._clock, self._wall = clock, wall
        self.log = log or (lambda msg: print(f"node: {msg}", file=sys.stderr))
        self.table = DeviceTable(self.vid, pack_id=pack_id, lookup=lookup,
                                 canonical=canonical, is_known=is_known,
                                 log=lambda m: self.log(m), primary=primary,
                                 allowed=_allowed_values)
        cid = client_id or getattr(client, "client_id", None) or \
            f"{socket.gethostname().split('.')[0]}-nodesource"
        if client is None:
            client = StdlibMqttClient(cid, keep_alive=KEEP_ALIVE_S, clean_start=True,
                                      session_expiry=0, ssl_context=ssl_context)
        self.client = client
        # The tap connection (P2): built per recorded session.
        self._tap_factory = tap_client or (lambda: StdlibMqttClient(
            f"{cid}-tap", keep_alive=KEEP_ALIVE_S, clean_start=True,
            session_expiry=TAP_SESSION_EXPIRY_S, ssl_context=ssl_context))
        # Remove device's broker-host connection (spec §13): built per removal, with its
        # own credentials when the install gives them (the broker's ACL grants that
        # identity the vehicle's topics), else the read identity's TLS context.
        self._host_factory = host_client or (lambda: StdlibMqttClient(
            f"{cid}-host", keep_alive=KEEP_ALIVE_S, clean_start=True, session_expiry=0,
            ssl_context=host_ssl_context if host_ssl_context is not None else ssl_context,
            timeout=5.0))
        self._remove_lock = threading.Lock()
        self._tap: "MqttClient | None" = None
        self._tap_sink: "Callable[[str, str, str, bytes, dict], object] | None" = None
        self._tap_session: "str | None" = None
        self._tap_last_rx: "float | None" = None
        self.tap_batches = 0
        self.refused: "list[str]" = []
        self.attempted = False  # a connection was tried (so "down" means down, not "starting")
        self.subscribed_at: "float | None" = None  # the read set's SUBACK (this connection)
        self.last_msg: "float | None" = None
        self._last_msg_wall: "float | None" = None
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
        self.stop_tap(wait=True)
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
            self.subscribed_at = self._clock()
        for f in refused:
            self.log(f"the broker refused the subscription {f} (check the ACL, spec §5)")
        self.log(f"connected to {self.host}:{self.port}, subscribed to vehicle {self.vid}")

    def _on_disconnect(self, reason: str) -> None:
        self.attempted = True
        with self._lock:
            self.subscribed_at = None
        self.log(f"broker connection lost: {reason}")

    def _on_message(self, pkt) -> None:
        now, wall = self._clock(), self._wall()
        self.last_msg, self._last_msg_wall = now, wall
        self.table.ingest(pkt.topic, pkt.payload, pkt.retain, now, wall)

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

    def device_info(self) -> "dict[str, dict]":
        return self.table.device_info()

    def cluster(self) -> dict:
        """``GET /cluster`` (spec §11): the devices, their power and last seen, the role
        holders and void claims, as built from what they publish. ``stale`` while the
        broker is not connected (the view is then read-only and shows its age, UI spec
        §3.7); ``as_of_utc`` is the last message's arrival."""
        view = self.table.cluster()
        broker = self.broker()
        return {"vid": self.vid, "source_kind": "node", "built_utc": utc(self._wall()),
                "as_of_utc": utc(self._last_msg_wall) if self._last_msg_wall else None,
                "stale": not broker["connected"], "broker": broker, **view}

    # ---- events (module-bus spec §6.1) ----------------------------------------------- #
    def events(self, after: int = 0, limit: int = 200) -> dict:
        """``GET /cluster/events``: the de-duplicated events feed, oldest first, with the
        cursor to ask for newer ones (``after``)."""
        evs = self.table.events(after, limit)
        return {"vid": self.vid, "events": evs,
                "last_seq": self.table.last_event_seq(),
                "duplicates": self.table.duplicate_events,
                "stale": not self.connected}

    def wait_events(self, after: int, timeout: float) -> bool:
        return self.table.wait_events(after, timeout)

    # ---- Remove device (module-bus spec §7.2, §13) ---------------------------------- #
    def load_removed(self, devices: "list[str]") -> None:
        """Devices removed earlier (the Brain's revocation list): ignored from now on."""
        for d in devices:
            self.table.remove_device(d)

    def remove_device(self, device: str, *, settle: float = 0.5, settle_max: float = 3.0,
                      sleep: Callable[[float], None] = time.sleep) -> dict:
        """The broker-host purge for one removed device. The caller has checked the owner,
        the local link and the confirmation, and recorded the revocation. Returns ``{device,
        topics, purged, refused, remaining, buses, error?}``:

        - ``topics``: every retained topic purged or tried (seen by this feed, plus those
          the broker-host connection finds under ``<device>/#``);
        - ``refused``: topics whose empty retained publish the broker refused (its ACL);
        - ``remaining``: retained topics still there after the purge (re-read);
        - ``buses``: the gate buses its claims held (writable again by their holder).

        Limits: only this broker; a device still connected may republish (its certificate
        and ACL entry are revoked by the broker host, outside this call); retained topics
        the broker-host identity may not read are found only if this feed saw them."""
        check_device(device)
        with self._remove_lock:
            buses = gate_buses(self.table.cluster(), device)
            seen = self.table.remove_device(device)
            out: dict = {"device": device, "topics": [], "purged": [], "refused": [],
                         "remaining": [], "buses": buses}
            client = self._host_factory()
            found: "dict[str, bytes]" = {}
            lock = threading.Lock()
            last = {"t": time.monotonic()}

            def on_message(pkt) -> None:
                with lock:  # a stored copy, or a live one meanwhile (the latest wins)
                    found[pkt.topic] = pkt.payload
                    last["t"] = time.monotonic()

            client.on_message = on_message
            flt = device_filter(self.vid, device)
            try:
                client.connect(self.host, self.port)
            except Exception as exc:  # noqa: BLE001 — reported, never raised
                out["topics"] = seen
                out["error"] = f"cannot reach the broker as its host ({exc})"
                return out
            try:
                self._collect(client, flt, found, lock, last, settle, settle_max, sleep)
                with lock:
                    listed = {t for t, pl in found.items() if pl and _retained_kind(t)}
                topics = sorted(set(seen) | listed)
                out["topics"] = topics
                for t in topics:
                    try:
                        code = client.publish(t, b"", qos=1, retain=True)
                    except Exception as exc:  # noqa: BLE001
                        out["refused"].append(t)
                        out.setdefault("error", f"publish failed ({exc})")
                        continue
                    (out["refused"] if code >= 0x80 else out["purged"]).append(t)
                # Re-read: a fresh subscription delivers what is still retained.
                with lock:
                    found.clear()
                try:
                    client.unsubscribe([flt])
                except Exception:  # noqa: BLE001
                    pass
                self._collect(client, flt, found, lock, last, settle, settle_max, sleep)
                with lock:
                    out["remaining"] = sorted(t for t, pl in found.items() if pl)
            except Exception as exc:  # noqa: BLE001
                out.setdefault("error", f"broker-host purge failed ({exc})")
            finally:
                try:
                    client.disconnect()
                except Exception:  # noqa: BLE001
                    pass
            self.log(f"removed device {device}: purged {len(out['purged'])} retained topic(s)"
                     + (f", {len(out['refused'])} refused" if out["refused"] else "")
                     + (f", {len(out['remaining'])} left" if out["remaining"] else ""))
            return out

    @staticmethod
    def _collect(client, flt, found, lock, last, settle, settle_max, sleep) -> None:
        """Subscribe ``flt`` (QoS 1, Retain Handling 0) and wait until the retained copies
        stop arriving (``settle`` s quiet, at most ``settle_max`` s)."""
        with lock:
            last["t"] = time.monotonic()
        codes = client.subscribe([SubOptions(flt, 1, no_local=True, retain_as_published=True,
                                             retain_handling=0)])
        if codes and codes[0] >= 0x80:
            return  # the host identity may not read: only what the feed saw is purged
        start = time.monotonic()
        while time.monotonic() - start < settle_max:
            with lock:
                quiet = time.monotonic() - last["t"]
            if quiet >= settle:
                break
            sleep(0.02)

    # ---- the raw tap (P2) ------------------------------------------------------------ #
    def tap_subscription_options(self) -> "list[SubOptions]":
        return [SubOptions(f, qos, no_local=True, retain_as_published=False, retain_handling=0)
                for f, qos in tap_subscriptions(self.vid)]

    @property
    def tap_running(self) -> bool:
        return self._tap is not None

    def start_tap(self, sink: "Callable[[str, str, str, bytes, dict], object]") -> bool:
        """Subscribe to the raw tap and hand each message to ``sink(device, session, part,
        payload, properties)`` (``part`` is ``meta`` or ``data``; ``properties`` the
        publish's MQTT 5 properties, where a batch's content type and ``first_seq`` are,
        module-bus spec §8). Idempotent; never blocks (the connection is made in the
        background). True when it started now."""
        with self._lock:
            self._tap_sink = sink
            if self._tap is not None:
                return False
            client = self._tap_factory()
            self._tap = client
            self._tap_session, self._tap_last_rx = None, None
        client.on_message = self._on_tap_message
        client.on_connect = lambda _ack, c=client: self._on_tap_connect(c)
        client.on_disconnect = lambda reason: self.log(f"tap connection lost: {reason}")
        start = getattr(client, "start", None)
        if start is None:
            raise TypeError("the MQTT client cannot run in the background")
        start(self.host, self.port)
        self.log("raw tap: subscribing (a session is recording)")
        return True

    def stop_tap(self, wait: bool = False) -> bool:
        """Unsubscribe from the raw tap and close its connection (the session ended). The
        teardown runs in the background unless ``wait``. True when a tap was running."""
        with self._lock:
            client, self._tap, self._tap_sink = self._tap, None, None
        if client is None:
            return False

        def teardown() -> None:
            try:
                if client.connected:
                    unsub = getattr(client, "unsubscribe", None)
                    if unsub is not None:
                        unsub([s.topic_filter for s in self.tap_subscription_options()])
            except Exception:  # noqa: BLE001 — the broker expires the session in 60 s anyway
                pass
            stop = getattr(client, "stop", None)
            try:
                if stop is not None:
                    stop()
                else:
                    client.disconnect()
            except Exception:  # noqa: BLE001
                pass

        if wait:
            teardown()
        else:
            threading.Thread(target=teardown, name="nodesource-tap-stop", daemon=True).start()
        self.log("raw tap: unsubscribed (no session is recording)")
        return True

    def _on_tap_connect(self, client) -> None:
        # A new run starts clean; a reconnect within it resumes the 60 s session so QoS 1
        # batches queued meanwhile are delivered.
        if hasattr(client, "clean_start"):
            client.clean_start = False
        subs = self.tap_subscription_options()
        codes = client.subscribe(subs)
        for sub, code in zip(subs, codes):
            if code >= 0x80:
                self.log(f"the broker refused the subscription {sub.topic_filter} "
                         "(check the ACL, spec §5)")

    def _on_tap_message(self, pkt) -> None:
        t = parse_topic(pkt.topic)
        if t is None or t.vid != self.vid or not t.device or t.kind != "tap":
            return
        rest = parse_tap_rest(t.rest)
        if rest is None:
            return
        session, part = rest
        with self._lock:
            sink = self._tap_sink
            if part == "data":
                self.tap_batches += 1
                self._tap_session, self._tap_last_rx = session, self._clock()
        if sink is not None:
            props = dict(getattr(pkt, "properties", None) or {})
            sink(t.device, session, part, pkt.payload, props)

    def tap_state(self) -> "dict | None":
        """Snapshot ``node.tap``: null when the tap is not subscribed (no session is
        recording); else ``{session, state, batches}`` with ``state`` ``connecting``,
        ``waiting`` (subscribed, no batch lately) or ``receiving``."""
        with self._lock:
            client = self._tap
            if client is None:
                return None
            session, last = self._tap_session, self._tap_last_rx
            batches = self.tap_batches
        if not client.connected:
            state = "connecting"
        elif last is not None and self._clock() - last <= TAP_RECEIVING_S:
            state = "receiving"
        else:
            state = "waiting"
        return {"session": session, "state": state, "batches": batches}


_FAULT_NOTES = {"error": "the node's fault read failed",
                "unimplemented": "the node does not read faults on this module"}


def fault_lines(read: "dict | None") -> "tuple[list[str], str | None]":
    """The snapshot's ``faults`` (one line per code, as the cable sources show them) and
    ``faults_note`` from a node's fault list (module-bus spec §6.2): no list is "not read"
    (:data:`FAULTS_NOTE`); ``ok`` with none is read, none (no note); ``error`` and
    ``unimplemented`` say so (the node's ``note`` when it sent one)."""
    if read is None:
        return [], FAULTS_NOTE
    lines = []
    for f in read["faults"]:
        text = f.get("text")
        line = f"{f['code']} {text}" if text and text != f["code"] else f["code"]
        if f.get("state"):
            line += f" ({f['state']})"
        lines.append(line)
    if read["status"] in _FAULT_NOTES:
        return lines, read.get("note") or _FAULT_NOTES[read["status"]]
    return lines, None


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
        tap = self.feed.tap_state()
        if dev is not None:
            node = {**dev, "broker": broker, "tap": tap}
        read = self.feed.table.faults_for(self.name, prefer=(dev or {}).get("device"))
        faults, note = fault_lines(read)
        snap = {"source": self.name, "source_kind": "node", "signals": view["signals"],
                "vss": view["vss"], "faults": faults, "faults_read": read,
                "node": node or {"device": None, "status": None, "feed": None, "power": None,
                                 "boot": None,
                                 "last_seen_utc": None, "fw": None, "etag": None,
                                 "broker": broker, "tap": tap},
                "devices": view["devices"], "device_info": self.feed.device_info()}
        if note is not None:
            snap["faults_note"] = note
        state = ((dev or {}).get("power") or {}).get("state")
        if not broker["connected"]:
            snap["status"] = "broker-down" if self.feed.is_down() else "connecting"
            if snap["status"] == "broker-down":
                snap["error"] = "Brain cannot reach the broker"
        elif dev is None or dev.get("status") is None:
            snap["status"] = "connecting"
            snap["connect_phase"] = "waiting for the node"
        elif dev["status"] == "offline" and (dev.get("feed") or {}).get("state") == "off":
            # its feed owner cut its supply (module-bus spec v1.3 §5): off, not a loss
            snap["status"] = "asleep"
        elif dev["status"] == "offline":
            snap["status"] = "error"
            snap["error"] = "Node offline"
        elif dev["status"] == "asleep" or state in ("asleep", "off"):
            # a clean sleep (ADR-0037 Amendment 8, ADR-0040 §1); ``off`` (no supply, from its
            # power owner) is not running either, and is no unexpected loss
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


def _retained_kind(topic: str) -> bool:
    """A topic of a kind a device publishes retained (spec §3), or a tap header."""
    t = parse_topic(topic)
    if t is None:
        return False
    return t.kind in RETAINED_KINDS or (t.kind == "tap" and t.rest.endswith("/meta"))


def node_sources(feed: NodeFeed, modules: "list[str]") -> "dict[str, NodeSource]":
    """One :class:`NodeSource` per pack module, all over ``feed``."""
    return {m: NodeSource(feed, m) for m in modules}


def probe_cluster(feed: NodeFeed, *, timeout: float = 5.0, quiet: float = 0.3,
                  settle_max: float = 2.0, sleep: Callable[[float], None] = time.sleep,
                  clock: Callable[[], float] = time.monotonic) -> dict:
    """Connect ``feed`` once, wait for its read set's SUBACK and for the retained messages
    to stop arriving (``quiet`` s without one, at most ``settle_max`` s), and return its
    cluster view; the connection is closed again. Raises ConnectionError when the broker
    does not answer within ``timeout``."""
    feed.start()
    try:
        end = clock() + timeout
        while feed.subscribed_at is None:
            if clock() > end:
                err = getattr(feed.client, "last_error", None)
                raise ConnectionError(f"no answer from the broker {feed.host}:{feed.port}"
                                      + (f" ({err})" if err else ""))
            sleep(0.02)
        start = clock()
        while clock() - start < settle_max:
            last = max(feed.subscribed_at or 0.0, feed.last_msg or 0.0)
            if clock() - last >= quiet:
                break
            sleep(0.02)
        return feed.cluster()
    finally:
        feed.stop()


def check_serial_beside_node(url: str, vid: str, **kw) -> "str | None":
    """Owner answer 7: the reason a serial (K-line cable) source must not start on vehicle
    ``vid``, or None. Reads the vehicle's retained manifests and role claims once over the
    broker at ``url`` (the :func:`build_feed` options; client id ``<id>-check`` so a
    running NodeSource is never taken over). Raises ValueError or OSError
    (ConnectionError) when it cannot check."""
    probe = kw.pop("probe", probe_cluster)
    cid = kw.pop("client_id", None) or f"{socket.gethostname().split('.')[0]}-nodesource"
    feed = build_feed(url, vid, client_id=f"{cid}-check", **kw)
    return serial_refusal(probe(feed))


def build_feed(url: str, vid: str, *, ca: "str | None" = None, cert: "str | None" = None,
               key: "str | None" = None, insecure_lab: bool = False,
               client_id: "str | None" = None, log=None,
               host_cert: "str | None" = None, host_key: "str | None" = None) -> NodeFeed:
    """A feed for the active pack from a broker URL. ``mqtts://`` needs the CA and the
    client certificate and key (mTLS, spec §5; no passwords). Plain ``mqtt://`` is for a
    lab or test broker only and must be asked for with ``insecure_lab``. ``host_cert`` and
    ``host_key`` are the broker host's own identity for Remove device's purge (module-bus
    spec §13); without them the purge uses the read identity, which a production ACL
    refuses (the refusal is reported)."""
    from ..metrics import is_known
    from ..mqtt import tls_context
    from ..pack import active_pack

    scheme, host, port = parse_mqtt_url(url)
    ctx = host_ctx = None
    if bool(host_cert) != bool(host_key):
        raise ValueError("the broker-host identity needs both --mqtt-host-cert and "
                         "--mqtt-host-key")
    if scheme == "mqtts":
        if not (ca and cert and key):
            raise ValueError("mqtts:// needs --mqtt-ca, --mqtt-cert and --mqtt-key (mTLS)")
        ctx = tls_context(ca, cert, key)
        if host_cert and host_key:
            host_ctx = tls_context(ca, host_cert, host_key)
    elif not insecure_lab:
        raise ValueError("plain mqtt:// is for a lab broker only: pass --mqtt-insecure-lab, "
                         "or use mqtts:// with a client certificate")
    pack = active_pack()
    return NodeFeed(vid, host, port, client_id=client_id, ssl_context=ctx, pack_id=pack.id,
                    lookup=store_lookup(), canonical=pack.canonical, is_known=is_known,
                    log=log, primary=store_primaries(pack.module_ids()),
                    host_ssl_context=host_ctx)


__all__ = ["NodeFeed", "NodeSource", "build_feed", "check_serial_beside_node", "fault_lines",
           "node_sources",
           "parse_mqtt_url", "probe_cluster", "store_lookup", "store_primaries"]
