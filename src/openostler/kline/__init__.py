# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The K-line layer: frame formats, checksums, fast and 5-baud init, timeouts and retries,
protocol profiles (``profiles``), key-byte classification (``keywords``), ISO 9141-2
framing (``frame_iso9141``) and auto-detection (``detect``)."""
from .frame import (
    TD5_ECU_ADDRESS,
    TESTER_ADDRESS,
    ChecksumError,
    DecodedFrame,
    FrameError,
    checksum,
    decode,
    encode,
)
from .kline import (
    KLine,
    KLineError,
    KLineTimeout,
    SlowInitReply,
    SlowInitUnconfirmed,
    parse_slow_init_reply,
)
from .profiles import BUILTIN, KLineProfile, Timing

__all__ = [
    "KLine",
    "KLineError",
    "KLineTimeout",
    "SlowInitReply",
    "SlowInitUnconfirmed",
    "parse_slow_init_reply",
    "KLineProfile",
    "Timing",
    "BUILTIN",
    "DecodedFrame",
    "FrameError",
    "ChecksumError",
    "checksum",
    "encode",
    "decode",
    "TESTER_ADDRESS",
    "TD5_ECU_ADDRESS",
]
