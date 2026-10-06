# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ISO 9141-2 framing (spec K-line profiles §3). Pure.

Requests are ``68 6A F1 <data 1–7> <cs>``; replies are ``48 6B <ecu> <data…> <cs>``. There
is no length byte, so a reply burst is cut at each ``48 6B`` where the preceding
segment's checksum (sum mod 256) verifies. Multi-frame and multi-ECU bursts therefore
come back as separate frames, each with the address of the ECU that sent it, and header
bytes are never read as data (the muki01 audit's fake-DTC bug).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

REQUEST_HEADER = b"\x68\x6A\xF1"
REPLY_PREFIX = b"\x48\x6B"
MIN_FRAME = 4      # 48 6B <ecu> <cs>
MAX_FRAME = 11     # 48 6B <ecu> <7 data bytes> <cs>


class Iso9141FrameError(ValueError):
    """A request that cannot be framed."""


@dataclass(frozen=True)
class Iso9141Frame:
    ecu: int          # the replying ECU's address (third header byte)
    data: bytes       # the data bytes (mode/service first)
    raw: bytes        # the whole frame, header and checksum included


def _sum8(data: bytes) -> int:
    return sum(data) & 0xFF


def encode(data: bytes, header: bytes = REQUEST_HEADER) -> bytes:
    """``header + data + sum8``; ``data`` is 1–7 bytes. ``01 00`` → ``68 6A F1 01 00 C4``."""
    data = bytes(data)
    if not 1 <= len(data) <= 7:
        raise Iso9141FrameError(f"ISO 9141-2 data must be 1–7 bytes, got {len(data)}")
    body = bytes(header) + data
    return body + bytes([_sum8(body)])


def _verifies(seg: bytes) -> bool:
    return (MIN_FRAME <= len(seg) <= MAX_FRAME and seg[:2] == REPLY_PREFIX
            and _sum8(seg[:-1]) == seg[-1])


def strip_echo(burst: bytes, sent: "bytes | None") -> bytes:
    """Remove our own exact echo (the first occurrence of ``sent``) from ``burst``."""
    if not sent:
        return bytes(burst)
    i = bytes(burst).find(bytes(sent))
    if i < 0:
        return bytes(burst)
    return bytes(burst[:i]) + bytes(burst[i + len(sent):])


def split(burst: bytes, sent: "bytes | None" = None,
          on_drop: "Optional[Callable[[bytes], None]]" = None) -> "list[Iso9141Frame]":
    """Cut a raw reply burst into verified frames.

    ``sent`` (our request) is stripped first. Each frame starts at ``48 6B`` and ends where
    its checksum verifies: preferably right before the next ``48 6B`` or at the end of the
    burst, otherwise at the first length (4–11 bytes) that verifies. A segment that never
    verifies (noise, a damaged frame) is dropped and passed to ``on_drop``."""
    b = strip_echo(burst, sent)
    starts = [i for i in range(len(b) - 1) if b[i:i + 2] == REPLY_PREFIX]
    frames: "list[Iso9141Frame]" = []
    if not starts:
        if b and on_drop is not None:
            on_drop(b)
        return frames
    if starts[0] > 0 and on_drop is not None:
        on_drop(b[:starts[0]])
    i: "int | None" = starts[0]
    while i is not None:
        later = [s for s in starts if s > i]
        end: "int | None" = None
        for cand in later + [len(b)]:
            if cand - i > MAX_FRAME:
                break
            if _verifies(b[i:cand]):
                end = cand
                break
        if end is None:  # trailing noise after the frame: the first length that verifies
            for n in range(MIN_FRAME, MAX_FRAME + 1):
                if i + n <= len(b) and _verifies(b[i:i + n]):
                    end = i + n
                    break
        if end is None:
            nxt = later[0] if later else len(b)
            if on_drop is not None:
                on_drop(b[i:nxt])
            i = later[0] if later else None
            continue
        seg = b[i:end]
        frames.append(Iso9141Frame(ecu=seg[2], data=bytes(seg[3:-1]), raw=bytes(seg)))
        nxt_starts = [s for s in starts if s >= end]
        if end < len(b) and (not nxt_starts or nxt_starts[0] > end) and on_drop is not None:
            on_drop(b[end:nxt_starts[0] if nxt_starts else len(b)])
        i = nxt_starts[0] if nxt_starts else None
    return frames


__all__ = ["REQUEST_HEADER", "REPLY_PREFIX", "Iso9141Frame", "Iso9141FrameError", "encode",
           "split", "strip_echo"]
