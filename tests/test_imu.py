# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pi IMU: the LSM6DS driver against a fake i2c-dev fd, the mock IMU and the reader
(ADR-0010; replay-notes-capture spec §3)."""
import struct

import pytest

from openostler.imu import lsm6ds, reader
from openostler.imu.lsm6ds import Lsm6ds
from openostler.imu.reader import ImuReader, MockImu, open_imu
from openostler.logbook.motion import G, to_vehicle


class FakeBus:
    """/dev/i2c-1 with devices {addr: {reg: value}}; write(reg) sets the pointer,
    write(reg, val) writes, read(n) reads n registers from the pointer (auto-increment)."""

    def __init__(self, devices):
        self.devices = devices
        self.addr = None
        self.ptr = 0
        self.writes = []
        self.opened = []
        self.closed = False

    def install(self, monkeypatch):
        monkeypatch.setattr(lsm6ds.os, "open", self.open)
        monkeypatch.setattr(lsm6ds.os, "read", self.read)
        monkeypatch.setattr(lsm6ds.os, "write", self.write)
        monkeypatch.setattr(lsm6ds.os, "close", self.close)
        monkeypatch.setattr(lsm6ds.fcntl, "ioctl", self.ioctl)

    def open(self, path, flags):
        self.opened.append(path)
        if path != "/dev/i2c-1":
            raise FileNotFoundError(2, "No such file or directory")
        return 42

    def close(self, fd):
        self.closed = True

    def ioctl(self, fd, req, arg):
        assert fd == 42 and req == 0x0703
        self.addr = arg
        return 0

    def _dev(self):
        if self.addr not in self.devices:
            raise OSError(121, "Remote I/O error")
        return self.devices[self.addr]

    def write(self, fd, data):
        dev = self._dev()
        self.ptr = data[0]
        if len(data) == 2:
            dev[data[0]] = data[1]
            self.writes.append((self.addr, data[0], data[1]))
        return len(data)

    def read(self, fd, n):
        dev = self._dev()
        out = bytes(dev.get(self.ptr + i, 0) for i in range(n))
        self.ptr += n
        return out


def _regs(who, xyz=(0, 0, 8197)):
    regs = {0x0F: who}
    for i, b in enumerate(struct.pack("<hhh", *xyz)):
        regs[0x28 + i] = b
    return regs


def test_probe_configure_and_read(monkeypatch):
    bus = FakeBus({0x6B: _regs(0x6C, (4098, -2049, 8197))})
    bus.install(monkeypatch)
    imu = Lsm6ds()
    assert imu.addr == 0x6B and imu.chip == "LSM6DSOX"
    assert (0x6B, 0x10, 0x48) in bus.writes  # CTRL1_XL: 104 Hz, ±4 g
    assert (0x6B, 0x12, 0x44) in bus.writes  # CTRL3_C: BDU + auto-increment
    ax, ay, az = imu.read()
    assert ax == pytest.approx(4098 * 0.122e-3 * G)
    assert ay == pytest.approx(-2049 * 0.122e-3 * G)
    assert az == pytest.approx(G, rel=1e-3)  # 8197 LSB ≈ 1 g at ±4 g
    imu.close()
    assert bus.closed


def test_ds3trc_at_0x6a(monkeypatch):
    FakeBus({0x6A: _regs(0x6A)}).install(monkeypatch)
    assert Lsm6ds().chip == "LSM6DS3TR-C"


def test_wrong_chip_or_no_bus(monkeypatch):
    bus = FakeBus({0x6A: _regs(0x33)})
    bus.install(monkeypatch)
    with pytest.raises(OSError, match="no LSM6DS"):
        Lsm6ds()
    assert bus.closed
    with pytest.raises(OSError, match="i2c-7"):
        Lsm6ds(bus=7)


def test_open_imu_specs(monkeypatch):
    FakeBus({}).install(monkeypatch)
    assert open_imu("none") is None
    assert open_imu("auto") is None and "no LSM6DS" in reader.last_reason
    assert isinstance(open_imu("mock"), MockImu)
    assert open_imu("bogus") is None and "unknown" in reader.last_reason
    FakeBus({0x6A: _regs(0x6C)}).install(monkeypatch)
    assert isinstance(open_imu("auto"), Lsm6ds) and reader.last_reason is None


def test_mock_imu_deterministic_and_vehicle_aligned():
    m = MockImu()
    assert m.read(100.0) == MockImu().read(100.0)
    il, lt, vt = to_vehicle(m.read(30.0))   # pulling away (speed 0 → 50 between 20–45 s)
    assert il > 0.03
    il, lt, vt = to_vehicle(m.read(118.0))  # braking to the first stop
    assert il < -0.05
    assert to_vehicle(m.read(10.0)) == pytest.approx((0, 0, 0), abs=1e-4)  # parked
    assert max(abs(to_vehicle(m.read(t))[1]) for t in range(180, 330, 2)) > 0.05  # cornering


def test_reader_buffers_and_drains():
    class Src:
        def __init__(self):
            self.n = 0

        def read(self):
            self.n += 1
            if self.n == 2:
                raise OSError("bus glitch")
            return (0.0, 0.0, G)

    t = {"v": 1000.0}
    r = ImuReader(Src(), hz=25, clock=lambda: t["v"])
    for _ in range(3):
        r.poll_once()
        t["v"] += 0.04
    assert r.errors == 1 and "bus glitch" in r.error
    out = r.drain()
    assert [s[0] for s in out] == [1000000, 1000080] and out[0][1:] == (0.0, 0.0, G)
    assert r.drain() == [] and r.latest()[0] == 1000080


def test_reader_thread_runs_and_stops():
    r = ImuReader(MockImu(), hz=50)
    r.start()
    import time
    deadline = time.monotonic() + 2.0
    while not r.latest() and time.monotonic() < deadline:
        time.sleep(0.01)
    r.stop()
    assert r.latest() is not None and len(r.drain()) >= 1
