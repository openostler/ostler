# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""A small MQTT 5 client on the stdlib (NodeSource spec §5, §12, owner answer 1).

:class:`MqttClient` is the interface NodeSource is written against (connect, subscribe,
publish, on_message), so a paho adapter can be added later without touching NodeSource
(the spec's fallback, under its own ADR). :class:`StdlibMqttClient` implements it with
``socket``, ``ssl`` and ``threading``:

- CONNECT with clean start, a session expiry, a will and the keep-alive; CONNACK refusals
  raise :class:`~openostler.mqtt.codec.MqttError` with the broker's reason code.
- SUBSCRIBE with the MQTT 5 options (No Local, Retain As Published, Retain Handling) and
  waits for SUBACK; PUBLISH at QoS 0 and 1 (waits for PUBACK); incoming QoS 1 is acked
  after ``on_message`` returns.
- Keep-alive: PINGREQ when nothing was sent for the keep-alive (the broker's Server Keep
  Alive wins); no answer within 1.5 × keep-alive drops the connection, as a broker would.
- :meth:`StdlibMqttClient.start` runs a supervisor thread that reconnects with jittered
  back-off (1 s doubling to 30 s, spec §5) and calls ``on_connect`` after every CONNACK so
  the caller resubscribes (clean start: the retained topics rebuild the state).
- TLS 1.2+ with a client certificate through :func:`tls_context` (ADR-0021, ADR-0027 §8).

No QoS 2, no AUTH, no topic aliases (none of §4–§9 use them).
"""
from __future__ import annotations

import abc
import random
import select
import socket
import ssl
import threading
import time
from typing import Callable, Optional

from . import codec
from .codec import (Connack, Connect, Disconnect, MqttError, PacketReader, Pingreq, Puback,
                    Publish, Suback, Subscribe, SubOptions, Unsuback, Unsubscribe, Will)

BACKOFF_FIRST_S = 1.0
BACKOFF_MAX_S = 30.0


def tls_context(ca_file: str, cert_file: "str | None" = None,
                key_file: "str | None" = None) -> ssl.SSLContext:
    """A TLS 1.2+ client context that verifies the broker against ``ca_file`` (the Brain's
    local CA) and presents a client certificate when one is given (mTLS)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_verify_locations(cafile=ca_file)
    if cert_file:
        ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    return ctx


class MqttClient(abc.ABC):
    """What NodeSource needs from an MQTT 5 client. Callbacks run on the client's thread:

    - ``on_message(Publish)`` for every PUBLISH received (``retain`` set means a stored
      value delivered at subscribe time when Retain As Published is off);
    - ``on_connect(Connack)`` after every successful CONNACK (subscribe here);
    - ``on_disconnect(reason: str)`` when a connection ends.
    """

    on_message: "Optional[Callable[[Publish], None]]" = None
    on_connect: "Optional[Callable[[Connack], None]]" = None
    on_disconnect: "Optional[Callable[[str], None]]" = None

    @abc.abstractmethod
    def connect(self, host: str, port: int) -> Connack:
        """Open one connection (blocking until CONNACK)."""

    @abc.abstractmethod
    def subscribe(self, subscriptions: "list[SubOptions]",
                  properties: "dict | None" = None) -> "list[int]":
        """Subscribe and return the SUBACK reason codes (one per filter)."""

    @abc.abstractmethod
    def publish(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False,
                properties: "dict | None" = None) -> int:
        """Publish; QoS 1 returns the PUBACK reason code, QoS 0 returns 0."""

    @abc.abstractmethod
    def disconnect(self, reason_code: int = codec.SUCCESS) -> None:
        """Send DISCONNECT and close (a normal disconnect discards the will)."""

    @property
    @abc.abstractmethod
    def connected(self) -> bool:
        """Is a connection up right now?"""


class StdlibMqttClient(MqttClient):
    def __init__(self, client_id: str, *, keep_alive: int = 10, clean_start: bool = True,
                 session_expiry: int = 0, will: "Will | None" = None,
                 ssl_context: "ssl.SSLContext | None" = None,
                 server_hostname: "str | None" = None, timeout: float = 5.0,
                 clock: Callable[[], float] = time.monotonic,
                 backoff: "tuple[float, float]" = (BACKOFF_FIRST_S, BACKOFF_MAX_S),
                 rng: "random.Random | None" = None) -> None:
        self.client_id = client_id
        self.keep_alive = keep_alive
        self.clean_start = clean_start
        self.session_expiry = session_expiry
        self.will = will
        self.ssl_context = ssl_context
        self.server_hostname = server_hostname
        self.timeout = timeout
        self._clock = clock
        self._backoff = backoff
        self._rng = rng or random.Random()
        self._sock: "socket.socket | None" = None
        # One lock around every socket read and write: an SSL socket must not read in one
        # thread while another writes (OpenSSL's SSL object is not safe for that).
        self._io_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._pending: "dict[int, list]" = {}  # packet id → [Event, result]
        self._next_pid = 0
        self._reader: "threading.Thread | None" = None
        self._supervisor: "threading.Thread | None" = None
        self._stop = threading.Event()
        self._down = threading.Event()
        self._down.set()
        self._last_sent = 0.0
        self._ping_at: "float | None" = None
        self._ka = keep_alive  # effective keep-alive (Server Keep Alive wins)
        self.last_error: "str | None" = None
        self.connack: "Connack | None" = None

    # ---- connection ----------------------------------------------------------------- #
    @property
    def connected(self) -> bool:
        return not self._down.is_set()

    def connect(self, host: str, port: int) -> Connack:
        raw = socket.create_connection((host, port), timeout=self.timeout)
        try:
            sock = raw
            if self.ssl_context is not None:
                sock = self.ssl_context.wrap_socket(
                    raw, server_hostname=self.server_hostname or host)
            props = {"session_expiry_interval": self.session_expiry} if self.session_expiry else {}
            pkt = Connect(self.client_id, self.keep_alive, self.clean_start, props, self.will)
            sock.sendall(codec.encode(pkt))
            reader = PacketReader()
            sock.settimeout(self.timeout)
            packets: list = []
            while not packets:
                data = sock.recv(4096)
                if not data:
                    raise MqttError("the broker closed the connection before CONNACK")
                packets = reader.feed(data)
            ack = packets[0]
            if not isinstance(ack, Connack):
                raise MqttError(f"expected CONNACK, got packet type {ack.type}",
                                codec.PROTOCOL_ERROR)
            if ack.reason_code >= 0x80:
                raise MqttError(f"connection refused (reason 0x{ack.reason_code:02x})",
                                ack.reason_code)
        except BaseException:
            raw.close()
            raise
        self._ka = int(ack.properties.get("server_keep_alive", self.keep_alive))
        self._sock = sock
        self._last_sent = self._clock()
        self._ping_at = None
        self.connack = ack
        self.last_error = None
        self._down.clear()
        self._reader = threading.Thread(target=self._read_loop, args=(sock, reader, packets[1:]),
                                        name=f"mqtt-{self.client_id}", daemon=True)
        self._reader.start()
        return ack

    def disconnect(self, reason_code: int = codec.SUCCESS) -> None:
        sock = self._sock
        if sock is not None and self.connected:
            try:
                self._send(Disconnect(reason_code))
            except OSError:
                pass
        self._drop("disconnected by the client")

    def abort(self) -> None:
        """Drop the connection without DISCONNECT (a network loss: the will fires)."""
        self._drop("aborted")

    # ---- supervision and reconnect ------------------------------------------------ #
    def start(self, host: str, port: int) -> None:
        """Connect in the background and keep reconnecting until :meth:`stop`."""
        if self._supervisor is not None and self._supervisor.is_alive():
            return
        self._stop.clear()
        self._supervisor = threading.Thread(target=self._supervise, args=(host, port),
                                            name=f"mqtt-sup-{self.client_id}", daemon=True)
        self._supervisor.start()

    def stop(self) -> None:
        self._stop.set()
        self.disconnect()
        if self._supervisor is not None and self._supervisor is not threading.current_thread():
            self._supervisor.join(timeout=self.timeout + 1.0)

    def next_backoff(self, delay: float) -> "tuple[float, float]":
        """``(wait, next_delay)``: a jittered wait in ``[delay/2, delay]``, doubling up to the
        maximum (spec §5: 1 s doubling to 30 s)."""
        wait = self._rng.uniform(delay / 2.0, delay)
        return wait, min(delay * 2.0, self._backoff[1])

    def _supervise(self, host: str, port: int) -> None:
        delay = self._backoff[0]
        while not self._stop.is_set():
            try:
                ack = self.connect(host, port)
            except (OSError, MqttError) as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
            else:
                delay = self._backoff[0]
                cb = self.on_connect
                if cb is not None:
                    try:
                        cb(ack)
                    except Exception as exc:  # noqa: BLE001 — a callback never kills the link
                        self.last_error = f"on_connect: {type(exc).__name__}: {exc}"
                while not self._stop.is_set() and not self._down.wait(0.2):
                    pass
                if self._stop.is_set():
                    break
            wait, delay = self.next_backoff(delay)
            self._stop.wait(wait)

    # ---- requests ------------------------------------------------------------------ #
    def _pid(self) -> int:
        with self._state_lock:
            for _ in range(0xFFFF):
                self._next_pid = self._next_pid % 0xFFFF + 1
                if self._next_pid not in self._pending:
                    self._pending[self._next_pid] = [threading.Event(), None]
                    return self._next_pid
        raise MqttError("no free packet identifier")

    def _await(self, pid: int):
        ev, _ = self._pending[pid]
        ok = ev.wait(self.timeout)
        with self._state_lock:
            slot = self._pending.pop(pid, None)
        if not ok or slot is None or slot[1] is None:
            raise MqttError("no acknowledgement from the broker" if not ok
                            else "connection lost while waiting")
        return slot[1]

    def subscribe(self, subscriptions: "list[SubOptions]",
                  properties: "dict | None" = None) -> "list[int]":
        for s in subscriptions:
            if not codec.valid_topic_filter(s.topic_filter):
                raise ValueError(f"invalid topic filter: {s.topic_filter!r}")
        pid = self._pid()
        try:
            self._send(Subscribe(pid, list(subscriptions), dict(properties or {})))
        except OSError:
            self._pending.pop(pid, None)
            raise
        ack = self._await(pid)
        return list(ack.reason_codes)

    def unsubscribe(self, topic_filters: "list[str]") -> "list[int]":
        pid = self._pid()
        self._send(Unsubscribe(pid, list(topic_filters)))
        return list(self._await(pid).reason_codes)

    def publish(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False,
                properties: "dict | None" = None) -> int:
        if qos == 0:
            self._send(Publish(topic, bytes(payload), 0, retain, properties=dict(properties or {})))
            return 0
        pid = self._pid()
        self._send(Publish(topic, bytes(payload), qos, retain, packet_id=pid,
                           properties=dict(properties or {})))
        return self._await(pid).reason_code

    # ---- I/O ----------------------------------------------------------------------- #
    def _send(self, pkt) -> None:
        sock = self._sock
        if sock is None or self._down.is_set():
            raise OSError("not connected")
        data = codec.encode(pkt)
        with self._io_lock:
            sock.sendall(data)
            self._last_sent = self._clock()

    def _drop(self, reason: str) -> None:
        with self._state_lock:
            sock, self._sock = self._sock, None
            was_up = not self._down.is_set()
            self._down.set()
            pending = list(self._pending.values())
        for ev, _ in pending:
            ev.set()  # waiters see no result → "connection lost"
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
        if was_up:
            self.last_error = reason if reason != "disconnected by the client" else None
            cb = self.on_disconnect
            if cb is not None:
                try:
                    cb(reason)
                except Exception:  # noqa: BLE001
                    pass

    def _keepalive_due(self) -> "str | None":
        if not self._ka:
            return None
        now = self._clock()
        if self._ping_at is not None and now - self._ping_at > 1.5 * self._ka:
            return "keep-alive timeout (no PINGRESP)"
        if self._ping_at is None and now - self._last_sent >= self._ka:
            self._ping_at = now
            self._send(Pingreq())
        return None

    def _read_loop(self, sock, reader: PacketReader, early: list) -> None:
        tick = min(1.0, max(0.05, self._ka / 4.0)) if self._ka else 1.0
        try:
            sock.settimeout(tick)
        except OSError:
            return
        reason = "connection closed by the broker"
        try:
            for pkt in early:
                self._dispatch(pkt)
            while not self._down.is_set():
                data = _recv_when_ready(sock, self._io_lock, tick)
                if data is None:
                    why = self._keepalive_due()
                    if why:
                        reason = why
                        break
                    continue
                if not data:
                    break
                for pkt in reader.feed(data):
                    if isinstance(pkt, Disconnect):
                        reason = f"the broker disconnected (reason 0x{pkt.reason_code:02x})"
                        raise _Stop
                    self._dispatch(pkt)
                self._keepalive_due()
        except _Stop:
            pass
        except MqttError as exc:
            reason = f"protocol error: {exc}"
            try:
                self._send(Disconnect(exc.code))
            except OSError:
                pass
        except (OSError, ValueError) as exc:  # ValueError: the socket was closed under us
            reason = f"{type(exc).__name__}: {exc}"
        if self._sock is sock:
            self._drop(reason)

    def _dispatch(self, pkt) -> None:
        if isinstance(pkt, Publish):
            cb = self.on_message
            if cb is not None:
                try:
                    cb(pkt)
                except Exception as exc:  # noqa: BLE001 — a bad message never drops the link
                    self.last_error = f"on_message: {type(exc).__name__}: {exc}"
            if pkt.qos == 1 and pkt.packet_id:
                self._send(Puback(pkt.packet_id))
        elif isinstance(pkt, (Suback, Puback, Unsuback)):
            with self._state_lock:
                slot = self._pending.get(pkt.packet_id)
                if slot is not None:
                    slot[1] = pkt
                    slot[0].set()
        elif pkt.type == codec.PINGRESP:
            self._ping_at = None
        else:
            raise codec.ProtocolError(f"unexpected packet type {pkt.type} from the broker")


class _Stop(Exception):
    pass


def _recv_when_ready(sock, lock: threading.Lock, wait: float) -> "bytes | None":
    """Wait (without the lock) until the socket is readable, then read under the lock so
    no write runs at the same time. None when nothing arrived in ``wait`` seconds."""
    pending = getattr(sock, "pending", None)
    if not (pending is not None and pending()):
        if not select.select([sock], [], [], wait)[0]:
            return None
    with lock:
        try:
            return sock.recv(65536)
        except (socket.timeout, ssl.SSLWantReadError):
            return None


__all__ = ["BACKOFF_FIRST_S", "BACKOFF_MAX_S", "MqttClient", "StdlibMqttClient", "tls_context"]
