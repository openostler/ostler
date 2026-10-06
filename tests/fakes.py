# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test helper: a half-duplex ECU simulator at the Transport level.

Echoes every frame sent (like a real K-line) and queues a preprogrammed response
when a known request is sent. Lets the whole K-Line layer be tested without hardware.

A response (the value in ``responses``) may be either **static bytes** (the same
response every time — backward compatible) or **scripted**: a ``list``/``tuple`` of
bytes (one response per call, the last one repeats) or a ``callable(count) -> bytes``.
That lets a differential read yield DIFFERENT values between read #1 and read #2.
"""
from __future__ import annotations

from openostler.transport.base import Transport


def _as_response(v):
    """Normalize a response value into a callable(count) -> bytes."""
    if callable(v):
        return v
    if isinstance(v, (list, tuple)):
        seq = [bytes(x) for x in v]
        return lambda n, _seq=seq: _seq[min(n, len(_seq) - 1)]
    b = bytes(v)
    return lambda n, _b=b: _b


class FakeKLineEcu(Transport):
    """``slow_init_reply``: the raw bytes a 5-baud init returns (default ``55 E9 8F``, the
    airbag in the sniff; ``b""`` = silent). ``fast_reply``: the reply burst to the
    functional OBD fast init ``C1 33 F1 81 66``. ``bus_chatter``: bytes already on the line
    (another tester), seen by the first read. ``inits`` records ``"fast"``/``"5baud"``."""

    def __init__(self, responses: "dict | None" = None, corrupt: bool = False,
                 slow_init_reply: bytes = b"\x55\xe9\x8f", fast_reply: "bytes | None" = None,
                 bus_chatter: bytes = b"") -> None:
        self._rx = bytearray(bus_chatter)
        self._responses = {bytes(k): _as_response(v) for k, v in (responses or {}).items()}
        self._counts: "dict[bytes, int]" = {}
        self._corrupt = corrupt
        self.breaks: "list[float]" = []
        self.sent: "list[bytes]" = []
        self.slow_init_reply = bytes(slow_init_reply)
        self.inits: "list[str]" = []
        self.slow_addresses: "list[int]" = []
        if fast_reply is not None:
            self._responses[OBD_FAST_INIT] = _as_response(fast_reply)

    def open(self) -> None:
        self._is_open = True

    def close(self) -> None:
        self._is_open = False

    def send(self, data: bytes) -> int:
        data = bytes(data)
        self.sent.append(data)
        self._rx.extend(data)  # echo (half-duplex)
        fn = self._responses.get(data)
        if fn is not None:
            n = self._counts.get(data, 0)
            self._counts[data] = n + 1
            resp = bytes(fn(n))
            if self._corrupt:
                resp = resp[:-1] + bytes([resp[-1] ^ 0xFF])  # broken checksum
            self._rx.extend(resp)
        return len(data)

    def receive(self, size: int = 1, timeout: "float | None" = None) -> bytes:
        out = bytes(self._rx[:size])
        del self._rx[: len(out)]
        return out

    # low-level serial hooks that the K-Line layer uses
    def send_break(self, duration: float = 0.025) -> None:
        self.breaks.append(duration)
        self.inits.append("fast")

    def reset_input_buffer(self) -> None:
        self._rx.clear()

    # 5-baud slow-init hooks (airbag 0x5B): return keyword bytes 55 KW1 KW2
    def slow_init(self, address: int) -> bytes:
        self.slow_init_addr = address
        self.slow_addresses.append(address)
        self.inits.append("5baud")
        return self.slow_init_reply  # sync + KW1 + KW2 [+ ~KW2 echo + ~address]

    def parse_slow_init(self, raw: bytes):
        i = raw.find(0x55)
        return (raw[i + 1], raw[i + 2]) if i >= 0 and len(raw) >= i + 3 else None


# The functional OBD fast init (C1 33 F1 81 66) and its reply from a KWP2000 ECU at 0x10.
OBD_FAST_INIT = bytes.fromhex("C133F18166")


def kwp_fast_reply(kb1: int = 0xE9, kb2: int = 0x8F) -> bytes:
    """``83 F1 10 C1 KB1 KB2 cs``: a positive StartCommunication with key bytes."""
    body = bytes([0x83, 0xF1, 0x10, 0xC1, kb1, kb2])
    return body + bytes([sum(body) & 0xFF])


def slow_reply(kw1: int, kw2: int, address: int = 0x33, echo: bool = True) -> bytes:
    """A complete 5-baud reply: ``55 KW1 KW2 [~KW2 echo] ~address``."""
    out = bytes([0x55, kw1, kw2])
    if echo:
        out += bytes([(~kw2) & 0xFF])
    return out + bytes([(~address) & 0xFF])


def iso9141_reply(ecu: int, data: bytes) -> bytes:
    """``48 6B <ecu> data cs``."""
    body = bytes([0x48, 0x6B, ecu]) + bytes(data)
    return body + bytes([sum(body) & 0xFF])


class FakeIso9141Ecu(FakeKLineEcu):
    """An ISO 9141-2 car: silent to fast init, ``55 08 08`` and ``~0x33 = CC`` on 5-baud,
    ``48 6B 10 …`` replies (the keep-alive ``01 00`` answers ``41 00 …``)."""

    def __init__(self, responses: "dict | None" = None, kw: int = 0x08, **kwargs) -> None:
        base = {bytes.fromhex("686AF10100C4"): iso9141_reply(0x10, b"\x41\x00\xbe\x1f\xa8\x13")}
        base.update(responses or {})
        kwargs.setdefault("slow_init_reply", slow_reply(kw, kw))
        super().__init__(base, **kwargs)


class FakeKwpSlowEcu(FakeKLineEcu):
    """A KWP2000 car that answers only 5-baud: ``55 E9 8F``, then ``~0x33``."""

    def __init__(self, responses: "dict | None" = None, kb1: int = 0xE9, **kwargs) -> None:
        kwargs.setdefault("slow_init_reply", slow_reply(kb1, 0x8F))
        super().__init__(responses, **kwargs)


class FakeClock:
    """A monotonic clock whose ``sleep`` advances time instantly (timing tests never
    sleep). ``sleeps`` records every requested sleep."""

    def __init__(self, start: float = 1000.0) -> None:
        self.t = float(start)
        self.sleeps: "list[float]" = []

    def now(self) -> float:
        return self.t

    __call__ = now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        if seconds > 0:
            self.t += seconds

    def advance(self, seconds: float) -> None:
        self.t += seconds
