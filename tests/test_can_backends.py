# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The CanLink backends (CanLink spec §3) on fakes: SocketCAN framing, iproute2 control and
a fake raw socket; slcan; GVRET; python-can through a stand-in module; and
``ports.list_can_interfaces``. ``needs_vcan`` tests use a real ``vcan0`` when present."""
from __future__ import annotations

import json
import os
import socket
import struct
import sys
import types
from collections import deque

import pytest

from openostler.can import CanFrame, KernelIsoTpChannel, TxGate
from openostler.can import gvret, slcan, socketcan
from openostler.can.frame import pad
from openostler.can.link import CanError
from openostler.ports import list_can_interfaces

REQ = CanFrame(0x7DF, False, pad(b"\x02\x01\x00"))


# ---------------------------------------------------------------- SocketCAN -- #

def test_socketcan_frame_packing():
    raw = socketcan.pack_frame(CanFrame(0x18DAF110, True, b"\x01\x02"))
    assert len(raw) == 16 and struct.unpack("=I", raw[:4])[0] == 0x18DAF110 | 0x80000000
    back = socketcan.unpack_frame(raw)
    assert (back.id, back.extended, back.data) == (0x18DAF110, True, b"\x01\x02")
    err = struct.pack("=IB3x8s", 0x20000000 | 0x204, 8, bytes([0, 0, 0, 0, 0, 0, 12, 136]))
    e = socketcan.unpack_frame(err)
    assert e.error and e.data[7] == 136
    assert socketcan.pack_filters([(0x7E8, 0x7F8, False)]) == struct.pack(
        "=II", 0x7E8, 0x7F8 | 0x80000000)


class _Ip:
    """``ip`` stand-in: answers ``-details -json link show`` and records the rest."""

    def __init__(self, info: dict) -> None:
        self.info, self.calls = info, []

    def __call__(self, argv):
        self.calls.append(argv)
        out = json.dumps([{"ifname": "can0", "linkinfo": self.info}]) if "-json" in argv else ""
        return types.SimpleNamespace(stdout=out)


def test_ifcontrol_caps_and_configure():
    can = _Ip({"info_kind": "can", "info_data": {
        "ctrlmode_supported": ["LISTEN-ONLY", "ONE-SHOT", "BERR-REPORTING"],
        "berr_counter": {"tx": 3, "rx": 9}}})
    ifc = socketcan.CanIfControl("can0", run=can)
    caps = ifc.caps()
    assert caps.listen_only is True and caps.one_shot and caps.set_bitrate and caps.err_counters
    ifc.configure(500_000, listen_only=True, one_shot=False)
    assert can.calls[-3:] == [
        ["ip", "link", "set", "can0", "down"],
        ["ip", "link", "set", "can0", "type", "can", "bitrate", "500000", "listen-only", "on",
         "one-shot", "off", "berr-reporting", "on", "restart-ms", "0"],
        ["ip", "link", "set", "can0", "up"]]
    assert ifc.error_counters() == (3, 9)
    mcp = socketcan.CanIfControl("can0", run=_Ip({"info_kind": "can", "info_data": {
        "ctrlmode_supported": ["LISTEN-ONLY"]}})).caps()
    assert mcp.listen_only is True and not mcp.one_shot          # no one-shot: probe refused
    vcan = socketcan.CanIfControl("vcan0", run=_Ip({"info_kind": "vcan"})).caps()
    assert not vcan.set_bitrate and vcan.listen_only is False

    def missing(argv):
        raise FileNotFoundError("ip")
    none = socketcan.CanIfControl("can0", run=missing).caps()
    assert not none.set_bitrate and not none.one_shot


class _RawSock:
    def __init__(self, *args) -> None:
        self.rx: "deque[tuple[bytes, int]]" = deque()
        self.sent: "list[bytes]" = []
        self.opts: "list[tuple]" = []
        self.bound = None
        self.echo = False

    def setsockopt(self, level, opt, val) -> None:
        self.opts.append((level, opt, val))

    def bind(self, addr) -> None:
        self.bound = addr

    def send(self, raw: bytes) -> None:
        self.sent.append(raw)
        if self.echo:
            self.rx.append((raw, socketcan.MSG_CONFIRM))

    def recvmsg(self, n):
        raw, flags = self.rx.popleft()
        return raw, [], flags, None

    def close(self) -> None:
        pass


def _sock_link(info: dict):
    socks: "list[_RawSock]" = []

    def factory(*a):
        s = _RawSock(*a)
        socks.append(s)
        return s
    ip = _Ip(info)
    link = socketcan.SocketCanLink("can0", ifcontrol=socketcan.CanIfControl("can0", run=ip),
                                   sock_factory=factory, gate=TxGate(driving_state=lambda: "parked"))
    link._select = lambda r, w, x, t: (r if socks and socks[-1].rx else [], [], [])
    return link, socks, ip


def test_socketcan_link_listen_only_open_recv_send_and_one_shot(monkeypatch):
    monkeypatch.setattr(socket, "AF_CAN", 29, raising=False)
    info = {"info_kind": "can", "info_data": {"ctrlmode_supported": ["LISTEN-ONLY", "ONE-SHOT"]}}
    link, socks, ip = _sock_link(info)
    link.open(500_000)
    assert "listen-only" in ip.calls[-2] and ip.calls[-2][ip.calls[-2].index("listen-only") + 1] == "on"
    s = socks[-1]
    assert s.bound == ("can0",)
    assert (socketcan.SOL_CAN_RAW, socketcan.CAN_RAW_ERR_FILTER,
            struct.pack("=I", socketcan.CAN_ERR_MASK)) in s.opts
    s.rx.append((socketcan.pack_frame(CanFrame(0x100, False, b"\x01")), 0))
    assert link.recv(0.1).data == b"\x01" and link.recv(0.0) is None
    link.confirm_rate("detected")
    link.send(REQ)                                   # goes active: listen-only off first
    assert ip.calls[-2][ip.calls[-2].index("listen-only") + 1] == "off"
    assert socks[-1].sent[-1] == socketcan.pack_frame(REQ)
    # the one-shot probe: an own-message confirm with no error frame is the ACK
    link.close()
    link.open(500_000)
    probe = link.gate.probe_grant()
    socks_before = len(socks)
    orig = link._hw_open

    def hw_open(bitrate, *, listen_only, one_shot):
        orig(bitrate, listen_only=listen_only, one_shot=one_shot)
        socks[-1].echo = one_shot
    link._hw_open = hw_open
    out = link.send_oneshot(REQ, probe=probe, timeout=0.0)
    assert out.acked and not out.error and len(socks) > socks_before
    assert any("one-shot" in c and c[c.index("one-shot") + 1] == "on" for c in ip.calls)
    assert ip.calls[-2][ip.calls[-2].index("listen-only") + 1] == "on"   # back to listen-only


def _need(missing: "str | None", env: str) -> None:
    """Skip when ``missing`` names an absent prerequisite; with ``env`` set (the CI ``vcan``
    job) fail instead, so that job can never pass by skipping."""
    if missing is None:
        return
    if os.environ.get(env, "").strip() not in ("", "0"):
        pytest.fail(f"{env} is set but {missing}")
    pytest.skip(missing)


def _need_vcan0() -> None:
    _need(None if "vcan0" in list_can_interfaces() else "there is no vcan0 on this runner",
          "OSTLER_REQUIRE_VCAN")


@pytest.mark.needs_vcan
def test_vcan_roundtrip():
    _need_vcan0()
    a = socketcan.SocketCanLink("vcan0", gate=TxGate())
    b = socketcan.SocketCanLink("vcan0")
    a.open(None)
    b.open(None)
    assert not a.caps.set_bitrate                     # vcan: the rate must be declared
    a.confirm_rate("declared")
    a.send(REQ)
    got = b.recv(1.0)
    assert got is not None and got.id == 0x7DF and got.data == REQ.data
    a.close()
    b.close()


@pytest.mark.needs_vcan
def test_vcan_kernel_isotp_roundtrip():
    """``KernelIsoTpChannel`` on ``vcan0`` against a kernel ``CAN_ISOTP`` ECU socket: a
    single-frame request out, a multi-frame reply back (the kernel sends the FC)."""
    _need_vcan0()
    try:
        socket.socket(socket.AF_CAN, socket.SOCK_DGRAM, socket.CAN_ISOTP).close()
        missing = None
    except (AttributeError, OSError) as e:
        missing = f"kernel CAN_ISOTP is unavailable (modprobe can-isotp): {e}"
    _need(missing, "OSTLER_REQUIRE_CAN_ISOTP")
    link = socketcan.SocketCanLink("vcan0", gate=TxGate())
    link.open(None)
    link.confirm_rate("declared")
    ecu = socket.socket(socket.AF_CAN, socket.SOCK_DGRAM, socket.CAN_ISOTP)
    ecu.bind(("vcan0", 0x7E0, 0x7E8))                 # rx the tester's 7E0, tx 7E8
    ecu.settimeout(2.0)
    ch = KernelIsoTpChannel(link, 0x7E0, 0x7E8)
    try:
        ch.send(b"\x01\x00")
        assert ecu.recv(4095) == b"\x01\x00"
        reply = b"\x41\x00" + bytes(range(1, 19))      # 20 bytes: FF + CFs
        ecu.send(reply)
        assert ch.recv(2.0) == reply
    finally:
        ch.close()
        ecu.close()
        link.close()


def test_list_can_interfaces(tmp_path):
    for name, kind in (("can0", "280"), ("eth0", "1"), ("vcan0", "280"), ("bad", "x")):
        (tmp_path / name).mkdir()
        (tmp_path / name / "type").write_text(kind + "\n")
    assert list_can_interfaces(str(tmp_path)) == ["can0", "vcan0"]
    assert list_can_interfaces(str(tmp_path / "none")) == []


# -------------------------------------------------------------------- slcan -- #

class _Stream:
    """A scripted slcan adapter: answers every command with CR, frames on demand."""

    def __init__(self) -> None:
        self.written = b""
        self.out = b""

    def write(self, data: bytes) -> None:
        self.written += data
        for line in data.split(b"\r")[:-1]:
            if line == b"F":
                self.out += b"F00\r"
            elif line[:1] in (b"t", b"T"):
                self.out += b"z\r"
            elif line == b"S9":
                self.out += b"\x07"
            else:
                self.out += b"\r"

    def read(self, timeout: float) -> bytes:
        data, self.out = self.out, b""
        return data


def test_slcan_encode_decode():
    assert slcan.encode_frame(REQ) == b"t7DF80201005555555555\r"
    assert slcan.encode_frame(CanFrame(0x18DB33F1, True, b"\x02\x01\x00")) == \
        b"T18DB33F13020100\r"
    fr = slcan.decode_line("t7E8806410000000000001A2B")      # with a Z1 timestamp
    assert fr.id == 0x7E8 and fr.data == bytes.fromhex("0641000000000000")
    assert slcan.decode_line("T18DAF1103410D32").extended
    assert slcan.decode_line("t7E89") is None and slcan.decode_line("x") is None


def test_slcan_link_opens_listen_only_and_reports_the_wican_honestly():
    st = _Stream()
    link = slcan.SlcanLink(st, gate=TxGate(), poll_flags=False)
    link.open(500_000)
    assert st.written == b"C\rS6\rZ1\rL\r" and link.caps.kind == "slcan"
    st.out += b"t1002AABB\rF80\r"
    assert link.recv(0.01).data == b"\xAA\xBB"
    link.poll_flags = True
    assert link.recv(0.01).error                               # F80: bus error
    link.confirm_rate("declared")
    st.written = b""
    link.send(REQ)
    assert st.written == b"C\rS6\rZ1\rO\rt7DF80201005555555555\r"   # O (normal) only now
    wican = slcan.SlcanLink(_Stream(), tcp=True, gate=TxGate())
    assert wican.caps.kind == "slcan-tcp" and wican.caps.listen_only == "requested"
    with pytest.raises(CanError):
        wican.open(33_333)
    bad = slcan.SlcanLink(_Stream())
    bad.stream.write = lambda d: _Stream.write(bad.stream, d.replace(b"S6", b"S9"))
    with pytest.raises(CanError):
        bad.open(500_000)


# -------------------------------------------------------------------- GVRET -- #

def test_gvret_wire_format():
    setup = gvret.setup_bus(500_000, listen_only=True)
    assert setup[:2] == b"\xF1\x05"
    word = struct.unpack("<I", setup[2:6])[0]
    assert word & 0xFFFFF == 500_000 and word & 0xE0000000 == 0xE0000000
    assert struct.unpack("<I", gvret.setup_bus(250_000, listen_only=False)[2:6])[0] \
        & 0x20000000 == 0
    assert gvret.build_frame(CanFrame(0x7DF, False, b"\x02\x01\x00")) == \
        b"\xF1\x00\xDF\x07\x00\x00\x00\x03\x02\x01\x00\x00"
    dev = (b"\x00\xF1\x00" + struct.pack("<II", 1_500_000, 0x7E8) + b"\x03\x41\x0D\x32\x00"
           + b"\xF1\x09\xDE\xAD"
           + b"\xF1\x00" + struct.pack("<II", 2, 0x18DAF110 | 0x80000000) + b"\x12\x01\x02\x00"
           + b"\xF1\x00\x01")
    items, tail = gvret.parse(dev)
    assert items[0][0] == "frame" and items[0][1].data == b"\x41\x0D\x32"
    assert items[0][1].ts == 1.5 and items[1] == ("keepalive",)
    assert items[2][1].extended and items[2][1].id == 0x18DAF110 and items[2][1].channel == "can1"
    assert tail == b"\xF1\x00\x01"


def test_gvret_link_open_listen_only_and_keepalive():
    st = _Stream()
    st.write = lambda d: setattr(st, "written", st.written + d)
    link = gvret.GvretLink(st, gate=TxGate())
    link.open(500_000)
    assert st.written.startswith(b"\xE7\xE7\xF1\x05")
    assert struct.unpack("<I", st.written[4:8])[0] & 0x20000000
    st.out = b"\xF1\x00" + struct.pack("<II", 0, 0x7E8) + b"\x01\x41\x00"
    assert link.recv(0.01).data == b"\x41"
    assert b"\xF1\x09" in st.written                          # keep-alive sent
    assert not link.caps.error_frames and not link.caps.one_shot
    link.confirm_rate("declared")
    link.send(REQ)
    assert st.written.endswith(gvret.build_frame(REQ))


# --------------------------------------------------------------- python-can -- #

def test_python_can_is_optional_and_lazy(monkeypatch):
    from openostler.can import pycan

    monkeypatch.setitem(sys.modules, "can", None)
    with pytest.raises(CanError) as ei:
        pycan.PythonCanLink("pcan", "PCAN_USBBUS1")
    assert "openostler[can]" in str(ei.value)

    class Msg:
        def __init__(self, arbitration_id, is_extended_id, data, timestamp=0.0,
                     is_error_frame=False) -> None:
            self.arbitration_id, self.is_extended_id, self.data = arbitration_id, is_extended_id, data
            self.timestamp, self.is_error_frame = timestamp, is_error_frame

    class Bus:
        def __init__(self, **kw) -> None:
            self.kw, self.sent, self.rx, self._state = kw, [], deque(), None

        @property
        def state(self):
            return self._state

        @state.setter
        def state(self, v):
            if kw_passive_unsupported and v == "PASSIVE":
                raise NotImplementedError
            self._state = v

        def recv(self, timeout):
            return self.rx.popleft() if self.rx else None

        def send(self, m):
            self.sent.append(m)

        def set_filters(self, f):
            self.filters = f

        def shutdown(self):
            pass

    fake = types.SimpleNamespace(Bus=Bus, Message=Msg,
                                 BusState=types.SimpleNamespace(PASSIVE="PASSIVE", ACTIVE="ACTIVE"))
    monkeypatch.setitem(sys.modules, "can", fake)
    kw_passive_unsupported = False
    link = pycan.PythonCanLink("pcan", "PCAN_USBBUS1", gate=TxGate())
    link.open(500_000)
    assert link.bus.kw["bitrate"] == 500_000 and link.bus.state == "PASSIVE"
    link.bus.rx.append(Msg(0x7E8, False, b"\x41"))
    assert link.recv(0.0).id == 0x7E8
    link.confirm_rate("declared")
    link.send(REQ)
    assert link.bus.state == "ACTIVE" and link.bus.sent[-1].arbitration_id == 0x7DF
    kw_passive_unsupported = True
    other = pycan.PythonCanLink("kvaser", "0", gate=TxGate())
    other.open(500_000)
    assert other.caps.tx is False                              # no listen-only → no TX
