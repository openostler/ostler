# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``FakeObdLink``: a scripted :class:`~openostler.obd.link.ObdRequestLink` with several
ECUs (J1979 spec §9). Each ECU maps a request payload to its reply:

- ``bytes``: one whole service message;
- a ``list``/``tuple`` of bytes: several messages (a K-line multi-message reply);
- a ``callable(count) -> bytes | list | None``: scripted per call (``count`` from 0);
- ``None`` or a missing key: the ECU stays silent.

A functional request (``target=None``) reaches every ECU; a physical one only its target.
``late`` queues ``(ecu, message)`` pairs delivered with the *next* request, the way a slow
ECU's reply lands after the tester moved on (fixture F5). ``sent`` records every request.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

from ..obd.link import EcuReply, guard_payload

Reply = Union[bytes, "list[bytes]", "tuple[bytes, ...]", Callable[[int], object], None]


def _hex(s: "bytes | str") -> bytes:
    return bytes.fromhex(s) if isinstance(s, str) else bytes(s)


class FakeObdLink:
    def __init__(self, ecus: "Dict[str, Dict[bytes | str, Reply]]", flavor: str = "can11",
                 late: "Optional[Dict[bytes | str, List[Tuple[str, bytes | str]]]]" = None) -> None:
        self.flavor = flavor
        self._ecus = {e: {_hex(k): v for k, v in table.items()} for e, table in ecus.items()}
        self._late = {_hex(k): [(e, _hex(m)) for e, m in v] for k, v in (late or {}).items()}
        self._queued: "List[Tuple[str, bytes]]" = []
        self._counts: "Dict[Tuple[str, bytes], int]" = {}
        self.sent: "List[Tuple[bytes, Optional[str]]]" = []
        self.expects: "List[Optional[int]]" = []      # expect_messages per request

    def request(self, payload: bytes, *, target: "str | None" = None,
                expect_messages: "int | None" = None,
                timeout: "float | None" = None) -> "Dict[str, EcuReply]":
        payload = bytes(payload)
        guard_payload(payload, allow_clear=True)   # adapters refuse Mode 08 too
        self.sent.append((payload, target))
        self.expects.append(expect_messages)
        out: "Dict[str, List[bytes]]" = {}
        for ecu, msg in self._queued:
            out.setdefault(ecu, []).append(msg)
        self._queued = list(self._late.pop(payload, []))
        for ecu, table in self._ecus.items():
            if target is not None and ecu != target:
                continue
            reply = table.get(payload)
            if callable(reply):
                n = self._counts.get((ecu, payload), 0)
                self._counts[(ecu, payload)] = n + 1
                reply = reply(n)
            if reply is None:
                continue
            msgs = [_hex(m) for m in reply] if isinstance(reply, (list, tuple)) else [_hex(reply)]
            out.setdefault(ecu, []).extend(msgs)
        return {e: EcuReply(e, tuple(m)) for e, m in out.items()}

    def payloads(self) -> "List[bytes]":
        return [p for p, _t in self.sent]


__all__ = ["FakeObdLink"]
