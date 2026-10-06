# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``TxGate`` details beyond the shared vectors (CanLink spec §7, T8): the install
override, the allowlist schema and parser, per-entry rate limits, audit and logging, and
the kernel ISO-TP channel's open-time gate. No hardware."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from openostler.can import CanFrame, KernelIsoTpChannel, TxGate, TxRefused
from openostler.can.frame import pad
from openostler.can.gate import AllowEntry, is_diag_request_id, load_allowlist
from tests.fake_can import FakeCanBus, FakeCanLink

SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "can-tx-allowlist.schema.json"
EXAMPLE = [
    {"id": "7DF", "data": "01 04", "action": "obd_clear", "tier": 1,
     "category": "maintenance", "states": ["parked", "idling"]},
    {"id": "7E0", "data": "02 10 01", "action": "uds_session_sweep", "tier": 1},
    {"id": "18DA10F1", "extended": True, "dlc": 8, "data": "02 3E xx", "max_rate_hz": 2,
     "action": "tester_present_sweep", "tier": 1, "bus": "obd", "x-note": "discovery"},
]


def test_diag_ids():
    assert is_diag_request_id(0x7DF, False) and is_diag_request_id(0x7E7, False)
    assert not is_diag_request_id(0x7E8, False) and not is_diag_request_id(0x7DF, True)
    assert is_diag_request_id(0x18DB33F1, True) and is_diag_request_id(0x18DA17F1, True)
    assert not is_diag_request_id(0x18DAF117, True)


def test_allowlist_schema_and_parser():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(EXAMPLE, schema)
    for bad in ({"id": "7DF", "action": "x", "tier": 4},
                {"id": "7DF", "action": "x", "tier": 1, "states": ["moving"]},
                {"id": "7DF", "action": "x", "tier": 1, "data": "01 0"},
                {"id": "7DF", "action": "x", "tier": 1, "rate": 5}):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate([bad], schema)
    jsonschema.validate({"bus": "can", "bitrate": 500000, "id_width": 11},
                        {**schema["$defs"]["transport"], "$defs": schema["$defs"]})
    entries = load_allowlist(EXAMPLE)
    assert entries[0].states == ("parked", "idling") and entries[2].extended
    with pytest.raises(ValueError):
        AllowEntry.from_dict({"id": "7DF", "action": "x", "tier": 1, "states": ["moving"]})
    with pytest.raises(ValueError):
        AllowEntry.from_dict({"id": "7DF", "action": "x", "tier": 4})


def test_entry_matching_with_wildcards_and_dlc():
    e = AllowEntry.from_dict(EXAMPLE[2])
    assert e.matches(CanFrame(0x18DA10F1, True, pad(b"\x02\x3E\x80")))
    assert not e.matches(CanFrame(0x18DA10F1, True, b"\x02\x3E\x80"))       # DLC 3, not 8
    assert not e.matches(CanFrame(0x18DA10F1, True, pad(b"\x02\x3F\x80")))
    assert not e.matches(CanFrame(0x18DA10F1, True, pad(b"\x02\x3E\x80")), bus="body")


def test_entry_rate_limit():
    t = {"v": 0.0}
    gate = TxGate([{"id": "7E0", "data": "02 10 01", "action": "sweep", "tier": 1,
                    "max_rate_hz": 2}], clock=lambda: t["v"], driving_state=lambda: "parked")
    fr = CanFrame(0x7E0, False, pad(b"\x02\x10\x01"))
    gate.check(fr, gate.issue("sweep", 1), rate_ok=True)
    t["v"] = 0.2
    with pytest.raises(TxRefused) as ei:
        gate.check(fr, gate.issue("sweep", 1), rate_ok=True)
    assert ei.value.code == "entry_rate"
    t["v"] = 0.6
    gate.check(fr, gate.issue("sweep", 1), rate_ok=True)


def test_remote_override_is_read_once_and_fixed(monkeypatch):
    monkeypatch.setenv("OSTLER_ALLOW_REMOTE_CONTROL", "1")
    on = TxGate()
    monkeypatch.setenv("OSTLER_ALLOW_REMOTE_CONTROL", "0")
    off = TxGate()
    assert on.issue("a", 1, origin="remote").origin == "remote"
    with pytest.raises(TxRefused) as ei:
        off.issue("a", 1, origin="remote")
    assert ei.value.code == "remote"
    with pytest.raises(AttributeError):
        off.allow_remote = True
    with pytest.raises(TxRefused):
        off.issue("code", 4)                                   # Tier 4 needs an ADR


def test_refusals_and_permits_are_audited_and_logged(caplog):
    caplog.set_level(logging.INFO, logger="openostler.can.gate")
    audit: "list[dict]" = []
    gate = TxGate(EXAMPLE[:1], clock=lambda: 1.0, driving_state=lambda: "parked",
                  audit=audit.append)
    clear = CanFrame(0x7DF, False, pad(b"\x01\x04"))
    with pytest.raises(TxRefused):
        gate.check(clear, rate_ok=True)
    gate.check(clear, gate.issue("obd_clear", 1), rate_ok=True)
    gate.check(CanFrame(0x7DF, False, pad(b"\x02\x01\x00")), rate_ok=True)   # Tier 0: no log
    assert [(a["outcome"], a.get("reason"), a.get("action")) for a in audit] == [
        ("refused", "no_grant", None), ("permitted", None, "obd_clear")]
    assert "refused: no_grant" in caplog.text and "action=obd_clear" in caplog.text


class _Sock:
    def __init__(self, *args) -> None:
        self.args, self.opts, self.bound, self.sent = args, [], None, []

    def setsockopt(self, *a) -> None:
        self.opts.append(a)

    def bind(self, addr) -> None:
        self.bound = addr

    def send(self, data) -> None:
        self.sent.append(bytes(data))


def test_kernel_isotp_open_and_send_pass_the_gate(monkeypatch):
    import socket

    monkeypatch.setattr(socket, "CAN_ISOTP", 6, raising=False)
    monkeypatch.setattr(socket, "AF_CAN", 29, raising=False)
    bus = FakeCanBus()
    link = FakeCanLink(bus, gate=TxGate(clock=bus.now))
    link.open(500_000)
    with pytest.raises(TxRefused):                             # rate not confirmed
        KernelIsoTpChannel(link, 0x7E0, 0x7E8, sock_factory=_Sock)
    link.confirm_rate("declared")
    ch = KernelIsoTpChannel(link, 0x7E0, 0x7E8, sock_factory=_Sock)
    assert ch.sock.bound == ("can0", 0x7E8, 0x7E0)
    ch.send(b"\x22\xF1\x90")
    assert ch.sock.sent == [b"\x22\xF1\x90"]
    with pytest.raises(TxRefused):
        ch.send(b"\x2E\xF1\x90\x00")                           # Tier 4 never
    with pytest.raises(TxRefused) as ei:
        KernelIsoTpChannel(link, 0x700, 0x708, sock_factory=_Sock)
    assert ei.value.code == "not_allowlisted"
    sniff = KernelIsoTpChannel(link, 0x700, 0x708, listen=True, sock_factory=_Sock)
    with pytest.raises(TxRefused):
        sniff.send(b"\x01")
    ext = KernelIsoTpChannel(link, 0x18DA10F1, 0x18DAF110, extended=True, sock_factory=_Sock)
    assert ext.sock.bound == ("can0", 0x18DAF110 | 0x80000000, 0x18DA10F1 | 0x80000000)
