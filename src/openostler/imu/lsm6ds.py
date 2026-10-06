# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""LSM6DSOX / LSM6DS3TR-C accelerometer over Linux i2c-dev (ADR-0010). Stdlib only.

The part is probed at 0x6A then 0x6B on ``/dev/i2c-<bus>`` (``fcntl.ioctl(fd, I2C_SLAVE)``),
identified by ``WHO_AM_I`` (0x0F: 0x6C = LSM6DSOX, 0x6A = LSM6DS3TR-C, 0x69 = LSM6DS3), then
set to 104 Hz ODR and ±4 g. ``read()`` returns ``(ax, ay, az)`` in m/s² as specific force
(+1 g on the axis pointing up at rest), the same convention as the browser's
``accelerationIncludingGravity``. Mount the board x forward, y left, z up for the identity
calibration. Candidate until T-32 runs on the car.
"""
from __future__ import annotations

import fcntl
import os
import struct

I2C_SLAVE = 0x0703
ADDRESSES = (0x6A, 0x6B)
WHO_AM_I = 0x0F
CHIPS = {0x6C: "LSM6DSOX", 0x6A: "LSM6DS3TR-C", 0x69: "LSM6DS3"}
CTRL1_XL = 0x10
CTRL3_C = 0x12
OUTX_L_A = 0x28
CTRL1_XL_104HZ_4G = 0x48  # ODR_XL = 0100 (104 Hz), FS_XL = 10 (±4 g)
CTRL3_C_BDU_INC = 0x44    # BDU (block data update) + IF_INC (register auto-increment)
MG_PER_LSB = 0.122        # ±4 g sensitivity
G = 9.80665
SCALE = MG_PER_LSB / 1000.0 * G  # LSB → m/s²


class ImuError(OSError):
    pass


class Lsm6ds:
    """One LSM6DS-family accelerometer. ``ImuError`` (an ``OSError``) when absent."""

    def __init__(self, bus: int = 1, addr: "int | None" = None) -> None:
        self.dev = f"/dev/i2c-{int(bus)}"
        self.fd: "int | None" = None
        self.addr: "int | None" = None
        self.chip: "str | None" = None
        try:
            self.fd = os.open(self.dev, os.O_RDWR)
        except OSError as exc:
            raise ImuError(f"{self.dev}: {exc.strerror or exc}") from exc
        tried = (addr,) if addr is not None else ADDRESSES
        try:
            for a in tried:
                who = self._probe(a)
                if who in CHIPS:
                    self.addr, self.chip = a, CHIPS[who]
                    break
            if self.addr is None:
                raise ImuError(f"no LSM6DS accelerometer on {self.dev} "
                               f"(tried {', '.join(hex(a) for a in tried)})")
            self._write(CTRL3_C, CTRL3_C_BDU_INC)
            self._write(CTRL1_XL, CTRL1_XL_104HZ_4G)
        except Exception:
            self.close()
            raise

    def _select(self, addr: int) -> None:
        fcntl.ioctl(self.fd, I2C_SLAVE, addr)

    def _probe(self, addr: int) -> "int | None":
        try:
            self._select(addr)
            return self._read(WHO_AM_I, 1)[0]
        except OSError:
            return None

    def _write(self, reg: int, value: int) -> None:
        os.write(self.fd, bytes((reg, value & 0xFF)))

    def _read(self, reg: int, n: int) -> bytes:
        os.write(self.fd, bytes((reg,)))
        data = os.read(self.fd, n)
        if len(data) != n:
            raise ImuError(f"short read from {hex(reg)}: {len(data)}/{n} bytes")
        return data

    def read(self) -> "tuple[float, float, float]":
        if self.fd is None:
            raise ImuError("closed")
        x, y, z = struct.unpack("<hhh", self._read(OUTX_L_A, 6))
        return x * SCALE, y * SCALE, z * SCALE

    def close(self) -> None:
        fd, self.fd = self.fd, None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


__all__ = ["Lsm6ds", "ImuError", "I2C_SLAVE", "SCALE"]
