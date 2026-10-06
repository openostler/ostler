# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""An in-process MQTT 5 broker for tests, on the platform's own codec (NodeSource spec §13).

Listens on 127.0.0.1 (plain TCP, or TLS with an ``ssl_context``) and implements what the
node, the Brain and the later role (ADR-0037) and wake (ADR-0040) harnesses need:

- retained messages (an empty retained payload deletes), delivered at subscribe time with
  the retain flag set, per Retain Handling (0 always, 1 new subscriptions only, 2 never);
- live routing with No Local and Retain As Published, QoS 0 and 1 (the lower of the
  publish and the subscription), PUBACK;
- wills: published when a connection ends without a normal DISCONNECT (network loss,
  keep-alive timeout, takeover, DISCONNECT 0x04), discarded on a normal one;
- keep-alive (1.5 × the client's), session expiry and message expiry on a controllable
  clock (``clock=``; call :meth:`FakeBroker.tick`, or let the background ticker do it);
- an ACL table ``{client_id: {"read": [filters], "write": [filters]}}``: a SUBSCRIBE outside
  the read filters gets 0x87, a PUBLISH outside the write filters is refused (PUBACK 0x87
  at QoS 1, dropped at QoS 0). Clients not in the table are allowed everything unless
  ``default_deny`` is set.

Not here: QoS 2, will delay, shared subscriptions, topic aliases, AUTH.
"""
from __future__ import annotations

import socket
import ssl
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from openostler.mqtt import codec
from openostler.mqtt.client import _recv_when_ready
from openostler.mqtt.codec import (Connack, Connect, Disconnect, PacketReader, Pingreq,
                                   Pingresp, Puback, Publish, Suback, Subscribe, SubOptions,
                                   Unsuback, Unsubscribe, topic_matches)


def filter_covers(allowed: str, flt: str) -> bool:
    """Is every topic ``flt`` can match also matched by ``allowed``? (ACL check)"""
    a, f = allowed.split("/"), flt.split("/")
    for i, level in enumerate(a):
        if level == "#":
            return True
        if i >= len(f):
            return False
        if f[i] == "#":
            return False
        if level == "+":
            continue
        if f[i] == "+" or f[i] != level:
            return False
    return len(a) == len(f)


@dataclass
class _Session:
    client_id: str
    subs: "dict[str, SubOptions]" = field(default_factory=dict)
    expiry: int = 0
    conn: "Optional[_Conn]" = None
    gone_at: "float | None" = None
    queue: "list[tuple[Publish, float]]" = field(default_factory=list)


class _Conn:
    def __init__(self, broker: "FakeBroker", sock) -> None:
        self.broker, self.sock = broker, sock
        self.lock = threading.Lock()
        self.client_id: "str | None" = None
        self.will: "codec.Will | None" = None
        self.keep_alive = 0
        self.last_rx = broker.clock()
        self.closed = False
        self.pid = 0

    def send(self, pkt) -> None:
        with self.lock:
            if self.closed:
                return
            try:
                self.sock.sendall(codec.encode(pkt))
            except OSError:
                pass

    def next_pid(self) -> int:
        with self.lock:
            self.pid = self.pid % 0xFFFF + 1
            return self.pid


class FakeBroker:
    def __init__(self, *, clock: Callable[[], float] = time.monotonic,
                 acl: "dict | None" = None, default_deny: bool = False,
                 ssl_context: "ssl.SSLContext | None" = None, server_keep_alive: "int | None" = None,
                 ticker: bool = True, port: int = 0) -> None:
        self.clock = clock
        self.acl = acl or {}
        self.default_deny = default_deny
        self.ssl_context = ssl_context
        self.server_keep_alive = server_keep_alive
        self.retained: "dict[str, tuple[Publish, float]]" = {}
        self.sessions: "dict[str, _Session]" = {}
        self.received: "list[tuple[str, object]]" = []  # (client id, packet) for assertions
        self.refused: "list[tuple[str, str, str]]" = []  # (client id, verb, topic)
        self._lock = threading.RLock()
        self._ticker = ticker
        self._stop = threading.Event()
        self._srv: "socket.socket | None" = None
        self.host, self.port = "127.0.0.1", port

    # ---- lifecycle ------------------------------------------------------------------- #
    def start(self) -> "FakeBroker":
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(16)
        srv.settimeout(0.2)
        self._srv = srv
        self.port = srv.getsockname()[1]
        threading.Thread(target=self._accept, daemon=True).start()
        if self._ticker:
            threading.Thread(target=self._tick_loop, daemon=True).start()
        return self

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            conns = [s.conn for s in self.sessions.values() if s.conn is not None]
        for c in conns:
            self._close(c, will=False)
        if self._srv is not None:
            try:
                self._srv.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._srv.close()

    def __enter__(self) -> "FakeBroker":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                sock, _ = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            threading.Thread(target=self._serve, args=(sock,), daemon=True).start()

    def _tick_loop(self) -> None:
        while not self._stop.wait(0.05):
            self.tick()

    # ---- test controls --------------------------------------------------------------- #
    def connected_clients(self) -> "list[str]":
        with self._lock:
            return sorted(cid for cid, s in self.sessions.items() if s.conn is not None)

    def kill(self, client_id: str) -> None:
        """Drop a client's connection as a network loss would (its will is published)."""
        with self._lock:
            s = self.sessions.get(client_id)
            conn = s.conn if s else None
        if conn is not None:
            self._close(conn, will=True)

    def inject(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False,
               properties: "dict | None" = None) -> None:
        """Publish as if a (trusted) client had, without a connection."""
        self._route(None, Publish(topic, payload, qos, retain, properties=dict(properties or {})))

    def tick(self) -> None:
        now = self.clock()
        expired = []
        with self._lock:
            for s in list(self.sessions.values()):
                c = s.conn
                if c is not None and c.keep_alive and now - c.last_rx > 1.5 * c.keep_alive:
                    expired.append(c)
                elif c is None and s.gone_at is not None and now - s.gone_at >= s.expiry:
                    del self.sessions[s.client_id]
            for t, (_p, at) in list(self.retained.items()):
                if self._expired(_p, at, now):
                    del self.retained[t]
        for c in expired:
            c.send(Disconnect(codec.KEEP_ALIVE_TIMEOUT))
            self._close(c, will=True)

    # ---- ACL ----------------------------------------------------------------------- #
    def _may(self, client_id: "str | None", verb: str, topic_or_filter: str) -> bool:
        if client_id is None:
            return True
        entry = self.acl.get(client_id)
        if entry is None:
            return not self.default_deny
        pats = entry.get(verb, [])
        if verb == "read":
            return any(filter_covers(p, topic_or_filter) for p in pats)
        return any(topic_matches(p, topic_or_filter) for p in pats)

    # ---- connections ------------------------------------------------------------------ #
    def _serve(self, sock) -> None:
        if self.ssl_context is not None:
            try:
                sock = self.ssl_context.wrap_socket(sock, server_side=True)
            except (ssl.SSLError, OSError):
                sock.close()
                return
        conn = _Conn(self, sock)
        reader = PacketReader()
        sock.settimeout(0.2)
        try:
            while not conn.closed and not self._stop.is_set():
                data = _recv_when_ready(sock, conn.lock, 0.2)
                if data is None:
                    continue
                if not data:
                    break
                conn.last_rx = self.clock()
                for pkt in reader.feed(data):
                    cid = pkt.client_id if isinstance(pkt, Connect) else conn.client_id
                    self.received.append((cid or "", pkt))
                    if not self._handle(conn, pkt):
                        return
        except (OSError, ValueError, codec.MqttError):
            pass
        if not conn.closed:
            self._close(conn, will=True)

    def _handle(self, conn: _Conn, pkt) -> bool:
        if conn.client_id is None and not isinstance(pkt, Connect):
            self._close(conn, will=False)
            return False
        if isinstance(pkt, Connect):
            return self._connect(conn, pkt)
        if isinstance(pkt, Subscribe):
            self._subscribe(conn, pkt)
        elif isinstance(pkt, Unsubscribe):
            with self._lock:
                s = self.sessions.get(conn.client_id)
                codes = [0 if s and s.subs.pop(f, None) else 0x11 for f in pkt.topic_filters]
            conn.send(Unsuback(pkt.packet_id, codes))
        elif isinstance(pkt, Publish):
            if not self._may(conn.client_id, "write", pkt.topic):
                self.refused.append((conn.client_id, "write", pkt.topic))
                if pkt.qos:
                    conn.send(Puback(pkt.packet_id, codec.NOT_AUTHORIZED))
                return True
            n = self._route(conn, pkt)
            if pkt.qos:
                conn.send(Puback(pkt.packet_id,
                                 codec.SUCCESS if n else codec.NO_MATCHING_SUBSCRIBERS))
        elif isinstance(pkt, Pingreq):
            conn.send(Pingresp())
        elif isinstance(pkt, Disconnect):
            self._close(conn, will=pkt.reason_code == codec.DISCONNECT_WITH_WILL)
            return False
        return True

    def _connect(self, conn: _Conn, pkt: Connect) -> bool:
        conn.client_id, conn.will, conn.keep_alive = pkt.client_id, pkt.will, pkt.keep_alive
        props = {}
        if self.server_keep_alive is not None:
            conn.keep_alive = self.server_keep_alive
            props["server_keep_alive"] = self.server_keep_alive
        with self._lock:
            old = self.sessions.get(pkt.client_id)
        if old is not None and old.conn is not None:
            old.conn.send(Disconnect(codec.SESSION_TAKEN_OVER))
            self._close(old.conn, will=True)
        with self._lock:
            old = self.sessions.get(pkt.client_id)
            present = old is not None and not pkt.clean_start
            s = old if present else _Session(pkt.client_id)
            s.expiry = int(pkt.properties.get("session_expiry_interval", 0))
            s.conn, s.gone_at = conn, None
            self.sessions[pkt.client_id] = s
            queued, s.queue = s.queue, []
        conn.send(Connack(codec.SUCCESS, present, props))
        now = self.clock()
        for p, at in queued:
            self._deliver(conn, p, at, now, retain=False)
        return True

    def _subscribe(self, conn: _Conn, pkt: Subscribe) -> None:
        codes, deliver = [], []
        with self._lock:
            s = self.sessions[conn.client_id]
            for sub in pkt.subscriptions:
                if not codec.valid_topic_filter(sub.topic_filter):
                    codes.append(codec.TOPIC_FILTER_INVALID)
                    continue
                if not self._may(conn.client_id, "read", sub.topic_filter):
                    self.refused.append((conn.client_id, "read", sub.topic_filter))
                    codes.append(codec.NOT_AUTHORIZED)
                    continue
                new = sub.topic_filter not in s.subs
                s.subs[sub.topic_filter] = sub
                codes.append(min(sub.qos, 1))
                if sub.retain_handling == 0 or (sub.retain_handling == 1 and new):
                    for topic, (p, at) in sorted(self.retained.items()):
                        if topic_matches(sub.topic_filter, topic):
                            deliver.append((p, at, sub))
        conn.send(Suback(pkt.packet_id, codes))
        now = self.clock()
        for p, at, sub in deliver:
            self._deliver(conn, p, at, now, retain=True, qos=min(p.qos, sub.qos, 1))

    @staticmethod
    def _expired(p: Publish, at: float, now: float) -> bool:
        exp = p.properties.get("message_expiry_interval")
        return exp is not None and now - at >= exp

    def _deliver(self, conn: _Conn, p: Publish, at: float, now: float, *, retain: bool,
                 qos: "int | None" = None) -> None:
        if self._expired(p, at, now):
            return
        props = dict(p.properties)
        if "message_expiry_interval" in props:
            props["message_expiry_interval"] = max(0, int(props["message_expiry_interval"]
                                                          - (now - at)))
        q = p.qos if qos is None else qos
        conn.send(Publish(p.topic, p.payload, q, retain, False,
                          conn.next_pid() if q else None, props))

    def _route(self, sender: "_Conn | None", pkt: Publish) -> int:
        now = self.clock()
        stored = Publish(pkt.topic, pkt.payload, pkt.qos, False, properties=dict(pkt.properties))
        targets = []
        with self._lock:
            if pkt.retain:
                if pkt.payload:
                    self.retained[pkt.topic] = (stored, now)
                else:
                    self.retained.pop(pkt.topic, None)
            for s in self.sessions.values():
                best = None
                for flt, sub in s.subs.items():
                    if not topic_matches(flt, pkt.topic):
                        continue
                    if sub.no_local and sender is not None and s.client_id == sender.client_id:
                        continue
                    if best is None or sub.qos > best.qos:
                        best = sub
                if best is None:
                    continue
                q = min(pkt.qos, best.qos, 1)
                if s.conn is None:
                    if q and s.expiry:
                        s.queue.append((stored, now))
                    continue
                targets.append((s.conn, q, pkt.retain and best.retain_as_published))
        for conn, q, ret in targets:
            self._deliver(conn, stored, now, now, retain=ret, qos=q)
        return len(targets)

    def _close(self, conn: _Conn, *, will: bool) -> None:
        with conn.lock:
            if conn.closed:
                return
            conn.closed = True
        try:
            conn.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.sock.close()
        with self._lock:
            s = self.sessions.get(conn.client_id or "")
            if s is not None and s.conn is conn:
                s.conn, s.gone_at = None, self.clock()
                if not s.expiry:
                    del self.sessions[s.client_id]
        if will and conn.will is not None:
            w = conn.will
            self._route(None, Publish(w.topic, w.payload, w.qos, w.retain,
                                      properties=dict(w.properties)))


__all__ = ["FakeBroker", "filter_covers"]
