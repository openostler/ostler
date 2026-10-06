# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``LoggingCanLink`` (CanLink spec §8, T13): JSONL and candump capture with the VIN
scrubbed across FF and CFs (ADR-0036). No hardware."""
from __future__ import annotations

import json
import re

from openostler.can import CanObdRequestLink, LoggingCanLink, TxGate
from tests.fake_can import FakeCanBus, FakeCanLink, FakeObdEcu
from tests.obd_fakes import ascii_hex, make_vin

CANDUMP = re.compile(r"^\(\d+\.\d{6}\) can0 ([0-9A-F]{3}|[0-9A-F]{8})#([0-9A-F]*)$")


def test_t13_vin_absent_from_jsonl_and_candump(tmp_path):
    vin = make_vin()
    bus = FakeCanBus()
    FakeObdEcu(bus, 0x7E8, {"09 02": "49 02 01 " + ascii_hex(vin), "01 0D": "41 0D 32"})
    inner = FakeCanLink(bus, gate=TxGate(clock=bus.now))
    jl, cd = tmp_path / "cap.jsonl", tmp_path / "cap.candump"
    link = LoggingCanLink(inner, jsonl=jl, candump=cd, wall=lambda: 1_700_000_000.5)
    link.open(500_000)
    link.confirm_rate("declared")
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)
    assert obd.request(b"\x09\x02")["7E8"].messages[0][3:] == vin.encode()
    obd.request(b"\x01\x0D")
    link.close()
    jtext, ctext = jl.read_text(), cd.read_text()
    vin_hex = vin.encode().hex()
    for text in (jtext, ctext):
        flat = text.replace(" ", "").lower()
        assert vin not in text and vin_hex not in flat
        for i in range(0, 14, 3):                              # no 3-char run of it either
            assert vin[i:i + 3].encode().hex() not in flat
    rows = [json.loads(line) for line in jtext.splitlines()]
    assert {r["dir"] for r in rows} == {"rx", "tx"}
    vin_rows = [r for r in rows if r["id"] == "7E8" and "redacted" in r["data"]]
    assert len(vin_rows) == 3                                  # FF + 2 CFs
    assert all(r["data"] == "<redacted 8 bytes>" for r in vin_rows)
    fc = [r for r in rows if r["dir"] == "tx" and r["data"].startswith("30 00 00")]
    assert fc and fc[0]["id"] == "7E0"                         # our FC is kept
    assert any(r["data"].startswith("03 41 0D 32") for r in rows)   # other replies kept
    lines = ctext.splitlines()
    assert all(CANDUMP.match(line) for line in lines)          # candump stays parseable
    assert sum(1 for line in lines if line.endswith("7E8#0000000000000000")) == 3
    assert set(rows[0]) == {"ts", "dir", "id", "ext", "dlc", "data", "err"}


def test_logging_link_delegates_and_logs_error_frames(tmp_path):
    bus = FakeCanBus(250_000)
    bus.periodic(0x100, period=0.01, count=1)
    inner = FakeCanLink(bus)
    link = LoggingCanLink(inner, jsonl=tmp_path / "e.jsonl", candump=tmp_path / "e.log")
    link.open(500_000)
    assert link.state == "listening" and link.caps is inner.caps
    fr = link.recv(0.05)
    assert fr is not None and fr.error
    link.close()
    row = json.loads((tmp_path / "e.jsonl").read_text().splitlines()[0])
    assert row["err"] is True and row["id"] == "ERR"
    assert "20000000#" in (tmp_path / "e.log").read_text()
