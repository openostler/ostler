# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pi IMU input (ADR-0010; spec §3). Core: never imports web; stdlib only.

Contract:
* ``lsm6ds.Lsm6ds(bus=1, addr=None)``: probes 0x6A/0x6B WHO_AM_I over ``/dev/i2c-<bus>``
  with ``fcntl.ioctl(fd, I2C_SLAVE)``; ±4 g, ODR 104 Hz; ``read() -> (ax, ay, az)`` m/s².
* ``reader.ImuReader(source, hz)``: thread; ``latest()``/``drain() -> [(epoch_ms, ax, ay, az)]``.
* ``reader.MockImu(hz)``: deterministic synthetic motion (follows the mock GPS route).
* ``reader.open_imu(spec)``: ``auto | none | mock`` → source or None (``auto`` without a
  device → None, with a reason available via ``reader.last_reason``).
"""
