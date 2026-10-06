# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``CanFrame``: one classic CAN frame (CanLink spec §1). Stdlib only.

``data`` holds at most 8 bytes; 64 is reserved for CAN-FD (out of scope, spec §13).
An error frame (``error=True``) carries the controller's error report, not bus data.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_STD_ID = 0x7FF
MAX_EXT_ID = 0x1FFFFFFF


@dataclass(frozen=True)
class CanFrame:
    id: int
    extended: bool = False
    data: bytes = b""
    dlc: "int | None" = None        # defaults to len(data)
    ts: float = 0.0
    error: bool = False
    fd: bool = False
    channel: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", bytes(self.data))
        if self.dlc is None:
            object.__setattr__(self, "dlc", len(self.data))
        limit = 64 if self.fd else 8
        if len(self.data) > limit:
            raise ValueError(f"CAN frame data is {len(self.data)} bytes (max {limit})")
        if not self.error:
            top = MAX_EXT_ID if self.extended else MAX_STD_ID
            if not 0 <= self.id <= top:
                raise ValueError(f"CAN id 0x{self.id:X} out of range for "
                                 f"{'29' if self.extended else '11'}-bit")

    @property
    def id_text(self) -> str:
        """``"7E8"`` for 11-bit ids, ``"18DAF110"`` for 29-bit ids (the ECU key format)."""
        return f"{self.id:08X}" if self.extended else f"{self.id:03X}"

    def hex(self) -> str:
        return self.data.hex().upper()

    def __repr__(self) -> str:
        kind = " ERR" if self.error else ""
        return f"CanFrame({self.id_text}#{self.hex()}{kind})"


def id_text(can_id: int, extended: bool) -> str:
    return f"{can_id:08X}" if extended else f"{can_id:03X}"


def pad(data: bytes, byte: int = 0x55, length: int = 8) -> bytes:
    """Pad ``data`` to ``length`` bytes (ISO 15765-4 asks DLC 8 of test equipment)."""
    data = bytes(data)
    return data + bytes([byte]) * (length - len(data)) if len(data) < length else data


__all__ = ["CanFrame", "id_text", "pad", "MAX_STD_ID", "MAX_EXT_ID"]
