# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Scripted J1979 cars for the obd tests: a two-ECU CAN car and a petrol K-line car.

No VIN literal sits in the tree: :func:`make_vin` builds one at test time from parts
(ADR-0036, spec §9), so the scrub checks need no allowlist.
"""
from __future__ import annotations

import json
import pathlib

from openostler.obd.pids import PidTable
from openostler.testing import FakeObdLink

PIDS = pathlib.Path(__file__).parent / "fixtures" / "j1979" / "pids.json"
GOLDEN = pathlib.Path(__file__).parent / "fixtures" / "j1979" / "golden"


def table() -> PidTable:
    return PidTable.from_records(json.loads(PIDS.read_text(encoding="utf-8")))


def make_vin() -> str:
    """A 17-character VIN assembled from parts (not a real vehicle's)."""
    return "".join(["ZZ", "Z", "".join(str((i * 7 + 3) % 10) for i in range(14))])


def bm(block: int, pids) -> str:
    """The 4-byte support bitmap of ``block`` for ``pids`` as spaced hex."""
    v = 0
    for p in pids:
        if block < p <= block + 0x20:
            v |= 1 << (32 - (p - block))
    return v.to_bytes(4, "big").hex(" ").upper()


def chain(mode: int, pids, prefix: str = "") -> dict:
    """Bitmap replies for every block a set of supported ``pids`` needs."""
    out = {}
    pids = set(pids)
    block = 0
    while True:
        req = f"{mode:02X} {block:02X}" + (" 00" if mode == 2 else "")
        rep = f"{mode + 0x40:02X} {block:02X} " + ("00 " if mode == 2 else "") + bm(block, pids)
        out[req] = rep
        if block + 0x20 not in pids or block + 0x20 > 0xE0:
            return out
        block += 0x20


def ascii_hex(s: "str | bytes") -> str:
    b = s.encode("ascii") if isinstance(s, str) else s
    return b.hex(" ").upper()


ENGINE_01 = {0x01, 0x04, 0x05, 0x0C, 0x0D, 0x1C, 0x20, 0x21, 0x31, 0x40, 0x41, 0x51}
TRANS_01 = {0x01, 0x05, 0x0D}
CALID_1 = b"OSTLERCAL0001".ljust(16, b"\0")
NAME_ECM = b"ECM\0-" + b"EngineControl".ljust(15, b"\0")
NAME_TCM = b"TCM\0-" + b"TransControl".ljust(15, b"\0")


def can_two_ecu(vin: "str | None" = None, **extra) -> FakeObdLink:
    """7E8 (engine) and 7E9 (transmission) on 11-bit CAN."""
    vin = vin or make_vin()
    e8 = {**chain(1, ENGINE_01), **chain(2, {0x02, 0x05, 0x0C}), **chain(6, {0x01}),
          **chain(9, {0x02, 0x04, 0x06, 0x0A}),
          "0A": "4A 00",
          "01 1C": "41 1C 06", "01 51": "41 51 01",
          "01 01": "41 01 83 27 65 06", "01 41": "41 41 00 07 65 04",
          "01 31": "41 31 00 64",
          "01 0C 0D": "41 0C 1A F8 0D 32", "01 0D": "41 0D 32",
          "03": "43 02 01 33 03 00", "07": "47 01 01 71",
          "09 04": "49 04 01 " + ascii_hex(CALID_1),
          "09 06": "49 06 01 12 34 56 78",
          "09 0A": "49 0A 01 " + ascii_hex(NAME_ECM),
          "09 02": "49 02 01 " + ascii_hex(vin),
          "02 02 00": "42 02 00 01 33",
          "02 05 00 0C 00": "42 05 00 5A 0C 00 1A F8",
          "06 01": "46 01 01 0A 0B B0 0B 70 0B C2",
          "04": "44"}
    e9 = {**chain(1, TRANS_01), **chain(9, {0x0A}),
          "09 0A": "49 0A 01 " + ascii_hex(NAME_TCM),
          "01 01": "41 01 00 04 00 00",
          "01 0D": "41 0D 31", "01 0C 0D": "41 0D 31",
          "03": "43 01 07 00", "07": "47 01 01 71",
          "02 02 00": "42 02 00 00 00",
          "04": "44"}
    for ecu, table_ in extra.items():
        {"e8": e8, "e9": e9}[ecu].update(table_)
    return FakeObdLink({"7E8": e8, "7E9": e9}, flavor="can11")


def kline_petrol(vin: "str | None" = None) -> FakeObdLink:
    """A petrol ISO 9141-2 car with one ECU (source byte 10), single-PID requests and
    multi-message Mode 03 and Mode 09 replies."""
    vin = vin or make_vin()
    padded = b"\0\0\0" + vin.encode("ascii")
    vin_msgs = [f"49 02 {i + 1:02X} " + ascii_hex(padded[4 * i:4 * i + 4]) for i in range(5)]
    cal_msgs = [f"49 04 {i + 1:02X} " + ascii_hex(CALID_1[4 * i:4 * i + 4]) for i in range(4)]
    e10 = {**chain(1, {0x01, 0x05, 0x0C, 0x0D, 0x1C, 0x20, 0x21}), **chain(2, {0x02, 0x05}),
           **chain(9, {0x01, 0x02, 0x03, 0x04, 0x05, 0x06}),
           "01 05": "41 05 5A", "01 0C": "41 0C 1A F8", "01 0D": "41 0D 32",
           "01 1C": "41 1C 06", "01 01": "41 01 82 07 65 04",
           "03": ["43 01 33 01 34 03 00", "43 01 70 00 00 00 00"],
           "07": "47 00 00 00 00 00 00",
           "09 01": "49 01 01 05", "09 02": vin_msgs,
           "09 03": "49 03 01 04", "09 04": cal_msgs,
           "09 05": "49 05 01 01", "09 06": "49 06 01 DE AD BE EF",
           "06 00": "46 00 80 00 00 00", "06 01": "46 01 00 12 34",
           "02 02 00": "42 02 00 01 33", "02 05 00": "42 05 00 5A",
           "04": "44"}
    return FakeObdLink({"10": e10}, flavor="iso9141")
