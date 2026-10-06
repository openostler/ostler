# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The MQTT 5.0 packet codec (OASIS MQTT Version 5.0, 2019), stdlib only.

Exactly the subset the NodeSource spec uses (specs/2026-10-06-node-source-design.md §12):
CONNECT (with a will and properties), CONNACK, PUBLISH at QoS 0 and 1 with properties,
PUBACK, SUBSCRIBE (with No Local, Retain As Published and Retain Handling), SUBACK,
UNSUBSCRIBE, UNSUBACK, PINGREQ, PINGRESP and DISCONNECT with a reason code. No QoS 2
(PUBREC/PUBREL/PUBCOMP) and no AUTH: a packet of those types is a protocol error here.

Both directions are encoded and decoded, so one codec serves the client and the in-process
fake broker in ``tests/fake_broker.py``. Pure functions on bytes; no sockets.

Properties are plain dicts keyed by snake_case names (``message_expiry_interval``,
``session_expiry_interval`` …). The two that may repeat are lists: ``user_property`` holds
``(name, value)`` pairs and ``subscription_identifier`` holds ints.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

PROTOCOL_NAME = "MQTT"
PROTOCOL_LEVEL = 5
MAX_REMAINING = 268_435_455  # four varint bytes (§1.5.5)

# Packet types (§2.1.2).
CONNECT, CONNACK, PUBLISH, PUBACK = 1, 2, 3, 4
PUBREC, PUBREL, PUBCOMP = 5, 6, 7
SUBSCRIBE, SUBACK, UNSUBSCRIBE, UNSUBACK = 8, 9, 10, 11
PINGREQ, PINGRESP, DISCONNECT, AUTH = 12, 13, 14, 15

# Reason codes used here (§2.4).
SUCCESS = 0x00
GRANTED_QOS_1 = 0x01
DISCONNECT_WITH_WILL = 0x04
NO_MATCHING_SUBSCRIBERS = 0x10
UNSPECIFIED_ERROR = 0x80
MALFORMED_PACKET = 0x81
PROTOCOL_ERROR = 0x82
NOT_AUTHORIZED = 0x87
SERVER_SHUTTING_DOWN = 0x8B
KEEP_ALIVE_TIMEOUT = 0x8D
SESSION_TAKEN_OVER = 0x8E
TOPIC_FILTER_INVALID = 0x8F
TOPIC_NAME_INVALID = 0x90
QOS_NOT_SUPPORTED = 0x9B


class MqttError(Exception):
    """An MQTT failure with its reason code (``code``)."""

    def __init__(self, message: str, code: int = UNSPECIFIED_ERROR) -> None:
        super().__init__(message)
        self.code = code


class MalformedPacket(MqttError, ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message, MALFORMED_PACKET)


class ProtocolError(MqttError):
    def __init__(self, message: str) -> None:
        super().__init__(message, PROTOCOL_ERROR)


# ---- primitive data types (§1.5) ------------------------------------------------------ #
def encode_varint(n: int) -> bytes:
    if not 0 <= n <= MAX_REMAINING:
        raise ValueError(f"variable byte integer out of range: {n}")
    out = bytearray()
    while True:
        byte, n = n % 128, n // 128
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out)


def decode_varint(buf: bytes, pos: int = 0) -> "tuple[int, int]":
    """``(value, next_pos)``; raises MalformedPacket on more than four bytes or a cut."""
    value, mult = 0, 1
    for i in range(4):
        if pos + i >= len(buf):
            raise MalformedPacket("truncated variable byte integer")
        b = buf[pos + i]
        value += (b & 0x7F) * mult
        if not b & 0x80:
            return value, pos + i + 1
        mult *= 128
    raise MalformedPacket("variable byte integer longer than four bytes")


def _u16(n: int) -> bytes:
    return struct.pack(">H", n)


def _u32(n: int) -> bytes:
    return struct.pack(">I", n)


def encode_str(s: str) -> bytes:
    raw = s.encode("utf-8")
    if "\x00" in s:
        raise ValueError("UTF-8 strings must not contain U+0000 (§1.5.4)")
    if len(raw) > 0xFFFF:
        raise ValueError("string longer than 65535 bytes")
    return _u16(len(raw)) + raw


def encode_bin(b: bytes) -> bytes:
    if len(b) > 0xFFFF:
        raise ValueError("binary data longer than 65535 bytes")
    return _u16(len(b)) + bytes(b)


class _Reader:
    """A cursor over one packet's bytes (after the fixed header)."""

    def __init__(self, buf: bytes) -> None:
        self.buf, self.pos = buf, 0

    def left(self) -> int:
        return len(self.buf) - self.pos

    def take(self, n: int) -> bytes:
        if self.pos + n > len(self.buf):
            raise MalformedPacket("packet shorter than its fields")
        out = self.buf[self.pos:self.pos + n]
        self.pos += n
        return out

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return struct.unpack(">H", self.take(2))[0]

    def u32(self) -> int:
        return struct.unpack(">I", self.take(4))[0]

    def varint(self) -> int:
        value, self.pos = decode_varint(self.buf, self.pos)
        return value

    def bin(self) -> bytes:
        return self.take(self.u16())

    def str(self) -> str:
        raw = self.bin()
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise MalformedPacket("invalid UTF-8 string") from None
        if "\x00" in s:
            raise MalformedPacket("UTF-8 string contains U+0000")
        return s

    def rest(self) -> bytes:
        return self.take(self.left())


# ---- properties (§2.2.2) -------------------------------------------------------------- #
_BYTE, _U16, _U32, _VARINT, _STR, _BIN, _PAIR = range(7)
PROPERTIES = {
    0x01: ("payload_format_indicator", _BYTE),
    0x02: ("message_expiry_interval", _U32),
    0x03: ("content_type", _STR),
    0x08: ("response_topic", _STR),
    0x09: ("correlation_data", _BIN),
    0x0B: ("subscription_identifier", _VARINT),
    0x11: ("session_expiry_interval", _U32),
    0x12: ("assigned_client_identifier", _STR),
    0x13: ("server_keep_alive", _U16),
    0x15: ("authentication_method", _STR),
    0x16: ("authentication_data", _BIN),
    0x17: ("request_problem_information", _BYTE),
    0x18: ("will_delay_interval", _U32),
    0x19: ("request_response_information", _BYTE),
    0x1A: ("response_information", _STR),
    0x1C: ("server_reference", _STR),
    0x1F: ("reason_string", _STR),
    0x21: ("receive_maximum", _U16),
    0x22: ("topic_alias_maximum", _U16),
    0x23: ("topic_alias", _U16),
    0x24: ("maximum_qos", _BYTE),
    0x25: ("retain_available", _BYTE),
    0x26: ("user_property", _PAIR),
    0x27: ("maximum_packet_size", _U32),
    0x28: ("wildcard_subscription_available", _BYTE),
    0x29: ("subscription_identifier_available", _BYTE),
    0x2A: ("shared_subscription_available", _BYTE),
}
_PROP_ID = {name: (pid, kind) for pid, (name, kind) in PROPERTIES.items()}
_REPEATABLE = {"user_property", "subscription_identifier"}


def encode_properties(props: "dict | None") -> bytes:
    body = bytearray()
    for name, value in (props or {}).items():
        if name not in _PROP_ID:
            raise ValueError(f"unknown MQTT 5 property: {name}")
        pid, kind = _PROP_ID[name]
        values = value if name in _REPEATABLE else [value]
        for v in values:
            body += encode_varint(pid)
            if kind == _BYTE:
                body.append(int(v))
            elif kind == _U16:
                body += _u16(int(v))
            elif kind == _U32:
                body += _u32(int(v))
            elif kind == _VARINT:
                body += encode_varint(int(v))
            elif kind == _STR:
                body += encode_str(v)
            elif kind == _BIN:
                body += encode_bin(v)
            else:
                k, val = v
                body += encode_str(k) + encode_str(val)
    return encode_varint(len(body)) + bytes(body)


def _decode_properties(r: _Reader) -> dict:
    length = r.varint()
    end = r.pos + length
    if end > len(r.buf):
        raise MalformedPacket("property length past the packet end")
    props: dict = {}
    while r.pos < end:
        pid = r.varint()
        if pid not in PROPERTIES:
            raise MalformedPacket(f"unknown property identifier 0x{pid:02x}")
        name, kind = PROPERTIES[pid]
        if kind == _BYTE:
            v = r.u8()
        elif kind == _U16:
            v = r.u16()
        elif kind == _U32:
            v = r.u32()
        elif kind == _VARINT:
            v = r.varint()
        elif kind == _STR:
            v = r.str()
        elif kind == _BIN:
            v = r.bin()
        else:
            v = (r.str(), r.str())
        if name in _REPEATABLE:
            props.setdefault(name, []).append(v)
        elif name in props:
            raise ProtocolError(f"property {name} included twice")
        else:
            props[name] = v
    if r.pos != end:
        raise MalformedPacket("property length mismatch")
    return props


# ---- topics (§4.7) -------------------------------------------------------------------- #
def valid_topic_name(topic: str) -> bool:
    """A PUBLISH topic: non-empty, no wildcards, no U+0000."""
    return bool(topic) and "+" not in topic and "#" not in topic and "\x00" not in topic


def valid_topic_filter(flt: str) -> bool:
    """``#`` only as the whole last level, ``+`` only as a whole level."""
    if not flt or "\x00" in flt:
        return False
    levels = flt.split("/")
    for i, level in enumerate(levels):
        if "#" in level and (level != "#" or i != len(levels) - 1):
            return False
        if "+" in level and level != "+":
            return False
    return True


def topic_matches(flt: str, topic: str) -> bool:
    """Does ``topic`` match the filter ``flt``? Wildcards never match a ``$`` topic's first
    level (§4.7.2)."""
    f, t = flt.split("/"), topic.split("/")
    if t[0].startswith("$") and f[0] in ("+", "#"):
        return False
    for i, level in enumerate(f):
        if level == "#":
            return True
        if i >= len(t):
            return False
        if level != "+" and level != t[i]:
            return False
    return len(f) == len(t)


# ---- packets ------------------------------------------------------------------------ #
@dataclass
class Will:
    topic: str
    payload: bytes
    qos: int = 0
    retain: bool = False
    properties: dict = field(default_factory=dict)


@dataclass
class Connect:
    client_id: str
    keep_alive: int = 60
    clean_start: bool = True
    properties: dict = field(default_factory=dict)
    will: "Will | None" = None
    username: "str | None" = None
    password: "bytes | None" = None
    type = CONNECT


@dataclass
class Connack:
    reason_code: int = SUCCESS
    session_present: bool = False
    properties: dict = field(default_factory=dict)
    type = CONNACK


@dataclass
class Publish:
    topic: str
    payload: bytes = b""
    qos: int = 0
    retain: bool = False
    dup: bool = False
    packet_id: "int | None" = None
    properties: dict = field(default_factory=dict)
    type = PUBLISH


@dataclass
class Puback:
    packet_id: int
    reason_code: int = SUCCESS
    properties: dict = field(default_factory=dict)
    type = PUBACK


@dataclass
class SubOptions:
    """One topic filter of a SUBSCRIBE with its MQTT 5 options (§3.8.3.1)."""

    topic_filter: str
    qos: int = 0
    no_local: bool = False
    retain_as_published: bool = False
    retain_handling: int = 0

    def byte(self) -> int:
        if self.qos not in (0, 1, 2) or self.retain_handling not in (0, 1, 2):
            raise ValueError("invalid subscription options")
        return (self.qos | (0x04 if self.no_local else 0)
                | (0x08 if self.retain_as_published else 0) | (self.retain_handling << 4))


@dataclass
class Subscribe:
    packet_id: int
    subscriptions: "list[SubOptions]"
    properties: dict = field(default_factory=dict)
    type = SUBSCRIBE


@dataclass
class Suback:
    packet_id: int
    reason_codes: "list[int]"
    properties: dict = field(default_factory=dict)
    type = SUBACK


@dataclass
class Unsubscribe:
    packet_id: int
    topic_filters: "list[str]"
    properties: dict = field(default_factory=dict)
    type = UNSUBSCRIBE


@dataclass
class Unsuback:
    packet_id: int
    reason_codes: "list[int]"
    properties: dict = field(default_factory=dict)
    type = UNSUBACK


@dataclass
class Pingreq:
    type = PINGREQ


@dataclass
class Pingresp:
    type = PINGRESP


@dataclass
class Disconnect:
    reason_code: int = SUCCESS
    properties: dict = field(default_factory=dict)
    type = DISCONNECT


def _fixed(ptype: int, flags: int, body: bytes) -> bytes:
    return bytes([(ptype << 4) | flags]) + encode_varint(len(body)) + body


def _check_qos01(qos: int) -> None:
    if qos not in (0, 1):
        raise ValueError("this codec supports QoS 0 and 1 only")


def encode(p) -> bytes:
    """One packet → its wire bytes."""
    t = p.type
    if t == CONNECT:
        flags = 0x02 if p.clean_start else 0
        if p.will is not None:
            _check_qos01(p.will.qos)
            flags |= 0x04 | (p.will.qos << 3) | (0x20 if p.will.retain else 0)
        if p.username is not None:
            flags |= 0x80
        if p.password is not None:
            flags |= 0x40
        body = (encode_str(PROTOCOL_NAME) + bytes([PROTOCOL_LEVEL, flags]) + _u16(p.keep_alive)
                + encode_properties(p.properties) + encode_str(p.client_id))
        if p.will is not None:
            body += (encode_properties(p.will.properties) + encode_str(p.will.topic)
                     + encode_bin(p.will.payload))
        if p.username is not None:
            body += encode_str(p.username)
        if p.password is not None:
            body += encode_bin(p.password)
        return _fixed(CONNECT, 0, body)
    if t == CONNACK:
        return _fixed(CONNACK, 0, bytes([1 if p.session_present else 0, p.reason_code])
                      + encode_properties(p.properties))
    if t == PUBLISH:
        _check_qos01(p.qos)
        if not valid_topic_name(p.topic):
            raise ValueError(f"invalid topic name: {p.topic!r}")
        body = encode_str(p.topic)
        if p.qos:
            if not p.packet_id:
                raise ValueError("QoS 1 PUBLISH needs a packet id")
            body += _u16(p.packet_id)
        body += encode_properties(p.properties) + bytes(p.payload)
        flags = (0x08 if p.dup else 0) | (p.qos << 1) | (0x01 if p.retain else 0)
        return _fixed(PUBLISH, flags, body)
    if t == PUBACK:
        body = _u16(p.packet_id)
        if p.reason_code != SUCCESS or p.properties:
            body += bytes([p.reason_code])
            if p.properties:
                body += encode_properties(p.properties)
        return _fixed(PUBACK, 0, body)
    if t == SUBSCRIBE:
        if not p.subscriptions:
            raise ValueError("SUBSCRIBE needs at least one filter")
        body = _u16(p.packet_id) + encode_properties(p.properties)
        for s in p.subscriptions:
            body += encode_str(s.topic_filter) + bytes([s.byte()])
        return _fixed(SUBSCRIBE, 0x02, body)
    if t in (SUBACK, UNSUBACK):
        return _fixed(t, 0, _u16(p.packet_id) + encode_properties(p.properties)
                      + bytes(p.reason_codes))
    if t == UNSUBSCRIBE:
        body = _u16(p.packet_id) + encode_properties(p.properties)
        for f in p.topic_filters:
            body += encode_str(f)
        return _fixed(UNSUBSCRIBE, 0x02, body)
    if t in (PINGREQ, PINGRESP):
        return _fixed(t, 0, b"")
    if t == DISCONNECT:
        if p.reason_code == SUCCESS and not p.properties:
            return _fixed(DISCONNECT, 0, b"")
        return _fixed(DISCONNECT, 0, bytes([p.reason_code]) + encode_properties(p.properties))
    raise ValueError(f"cannot encode packet type {t}")


_REQUIRED_FLAGS = {SUBSCRIBE: 0x02, UNSUBSCRIBE: 0x02}


def decode_body(first: int, body: bytes):
    """The packet for a fixed-header first byte and its body (after the length)."""
    t, flags = first >> 4, first & 0x0F
    if t != PUBLISH and flags != _REQUIRED_FLAGS.get(t, 0):
        raise MalformedPacket(f"reserved flags 0x{flags:x} set on packet type {t}")
    r = _Reader(body)
    if t == CONNECT:
        if r.str() != PROTOCOL_NAME:
            raise ProtocolError("not MQTT")
        level = r.u8()
        if level != PROTOCOL_LEVEL:
            raise MqttError(f"unsupported protocol level {level}", 0x84)
        cf = r.u8()
        if cf & 0x01:
            raise MalformedPacket("reserved connect flag set")
        keep_alive = r.u16()
        props = _decode_properties(r)
        client_id = r.str()
        will = None
        if cf & 0x04:
            wprops = _decode_properties(r)
            wtopic = r.str()
            will = Will(wtopic, r.bin(), qos=(cf >> 3) & 0x03, retain=bool(cf & 0x20),
                        properties=wprops)
            if will.qos > 1:
                raise MqttError("will QoS 2 is not supported", QOS_NOT_SUPPORTED)
        elif cf & 0x38:
            raise MalformedPacket("will QoS/retain set without a will")
        username = r.str() if cf & 0x80 else None
        password = r.bin() if cf & 0x40 else None
        return Connect(client_id, keep_alive, bool(cf & 0x02), props, will, username, password)
    if t == CONNACK:
        ack = r.u8()
        if ack & 0xFE:
            raise MalformedPacket("reserved CONNACK flags set")
        code = r.u8()
        return Connack(code, bool(ack & 0x01), _decode_properties(r) if r.left() else {})
    if t == PUBLISH:
        qos = (flags >> 1) & 0x03
        if qos == 3:
            raise MalformedPacket("PUBLISH QoS 3")
        if qos == 2:
            raise MqttError("QoS 2 is not supported", QOS_NOT_SUPPORTED)
        topic = r.str()
        pid = r.u16() if qos else None
        props = _decode_properties(r)
        if not topic and "topic_alias" not in props:
            raise ProtocolError("empty topic without a topic alias")
        return Publish(topic, r.rest(), qos, bool(flags & 0x01), bool(flags & 0x08), pid, props)
    if t == PUBACK:
        pid = r.u16()
        code = r.u8() if r.left() else SUCCESS
        return Puback(pid, code, _decode_properties(r) if r.left() else {})
    if t == SUBSCRIBE:
        pid = r.u16()
        props = _decode_properties(r)
        subs = []
        while r.left():
            flt = r.str()
            opt = r.u8()
            if opt & 0xC0 or (opt & 0x03) == 3 or (opt >> 4) & 0x03 == 3:
                raise MalformedPacket("invalid subscription options")
            subs.append(SubOptions(flt, opt & 0x03, bool(opt & 0x04), bool(opt & 0x08),
                                   (opt >> 4) & 0x03))
        if not subs:
            raise ProtocolError("SUBSCRIBE with no filters")
        return Subscribe(pid, subs, props)
    if t in (SUBACK, UNSUBACK):
        pid = r.u16()
        props = _decode_properties(r)
        cls = Suback if t == SUBACK else Unsuback
        return cls(pid, list(r.rest()), props)
    if t == UNSUBSCRIBE:
        pid = r.u16()
        props = _decode_properties(r)
        filters = []
        while r.left():
            filters.append(r.str())
        if not filters:
            raise ProtocolError("UNSUBSCRIBE with no filters")
        return Unsubscribe(pid, filters, props)
    if t in (PINGREQ, PINGRESP):
        if body:
            raise MalformedPacket("PING with a body")
        return Pingreq() if t == PINGREQ else Pingresp()
    if t == DISCONNECT:
        code = r.u8() if r.left() else SUCCESS
        return Disconnect(code, _decode_properties(r) if r.left() else {})
    raise ProtocolError(f"unsupported packet type {t}")


def decode(data: bytes):
    """One whole packet (fixed header included) → the packet; trailing bytes are an error."""
    if not data:
        raise MalformedPacket("empty packet")
    length, pos = decode_varint(data, 1)
    if pos + length != len(data):
        raise MalformedPacket("remaining length does not match the packet")
    return decode_body(data[0], data[pos:])


class PacketReader:
    """Incremental stream splitter: ``feed(bytes)`` returns the whole packets received."""

    def __init__(self, max_packet: int = MAX_REMAINING) -> None:
        self._buf = bytearray()
        self.max_packet = max_packet

    def feed(self, data: bytes) -> list:
        self._buf += data
        out = []
        while len(self._buf) >= 2:
            try:
                length, pos = decode_varint(bytes(self._buf[:5]), 1)
            except MalformedPacket:
                if len(self._buf) < 5:
                    break  # the length is still arriving
                raise
            if length > self.max_packet:
                raise MqttError("packet too large", 0x95)
            if len(self._buf) < pos + length:
                break
            first, body = self._buf[0], bytes(self._buf[pos:pos + length])
            del self._buf[:pos + length]
            out.append(decode_body(first, body))
        return out


__all__ = [
    "Connack", "Connect", "Disconnect", "MalformedPacket", "MqttError", "PacketReader",
    "Pingreq", "Pingresp", "ProtocolError", "Puback", "Publish", "Suback", "SubOptions",
    "Subscribe", "Unsuback", "Unsubscribe", "Will", "decode", "encode", "topic_matches",
    "valid_topic_filter", "valid_topic_name",
]
