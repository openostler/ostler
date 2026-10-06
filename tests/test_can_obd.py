# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""J1979 over CAN: ``CanObdRequestLink`` on the fake bus (CanLink spec §5, T15; J1979
spec fixtures F1c, F3–F5, F11 and the golden two-ECU SupportReport, now over ISO-TP).
No hardware."""
from __future__ import annotations

import json

import pytest

from openostler.can import CanObdRequestLink, TxGate, TxRefused
from openostler.can.obd import ecu_key, fc_id_for, physical_id
from openostler.obd import J1979, Pacer
from openostler.obd import clear as clr
from openostler.obd.link import ForbiddenService, ObdError
from tests.fake_can import FakeCanBus, FakeCanLink, FakeObdEcu
from tests.obd_fakes import GOLDEN, bm, can_two_ecu, chain, make_vin, table

CLEAR_ENTRY = {"id": "7DF", "data": "01 04", "action": "obd_clear", "tier": 1,
               "states": ["parked", "idling"]}


def _rig(ecus: dict, *, extended=False, state="moving", allowlist=(), ecu_kw=None):
    bus = FakeCanBus()
    for rid, responses in ecus.items():
        FakeObdEcu(bus, rid, responses, extended=extended, **(ecu_kw or {}).get(rid, {}))
    st = {"v": state}
    gate = TxGate(allowlist, clock=bus.now, driving_state=lambda: st["v"])
    link = FakeCanLink(bus, gate=gate)
    link.open(500_000)
    link.confirm_rate("declared", frozenset({29 if extended else 11}))
    return bus, link, st


def _j(bus, obd) -> J1979:
    return J1979(obd, table(), pacer=Pacer(clock=bus.now, sleep=bus.sleep), clock=bus.now)


def _from_fake(fake) -> dict:
    """The scripted tables of a ``FakeObdLink`` as FakeObdEcu responses keyed by id."""
    return {int(e, 16): {k: v for k, v in t.items()} for e, t in fake._ecus.items()}


def test_addressing_helpers():
    assert fc_id_for(0x7E8, False) == 0x7E0 and fc_id_for(0x18DAF110, True) == 0x18DA10F1
    assert physical_id("7E9", False) == 0x7E1 and physical_id("18DAF117", True) == 0x18DA17F1
    assert ecu_key(0x18DAF110, True) == "18DAF110" and ecu_key(0x7E8, False) == "7E8"
    with pytest.raises(ObdError):
        physical_id("7E0", False)


def test_t15_golden_support_report_over_isotp():
    vin = make_vin()
    bus, link, _st = _rig(_from_fake(can_two_ecu(vin)))
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)
    rep = _j(bus, obd).supported().to_dict()
    golden = json.loads((GOLDEN / "support_can_two_ecu.json").read_text(encoding="utf-8"))
    assert rep == golden
    assert vin not in json.dumps(rep)
    multi = [f for _t, n, f in bus.transmitted if n == "tester" and f.data[0] == 0x30]
    assert multi and all(f.id in (0x7E0, 0x7E1) for f in multi)   # FCs for the long replies


def test_t15_f1c_five_codes_over_ff_cf():
    bus, link, _st = _rig({0x7E8: {"03": "43 05 01 70 01 34 03 00 41 23 C1 00"}})
    j = _j(bus, CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep))
    assert j.read_dtcs("stored").codes() == ["P0170", "P0134", "P0300", "C0123", "U0100"]
    frames = [f.data for _t, _n, f in bus.transmitted if f.id == 0x7E8]
    assert frames[0][:2] == b"\x10\x0C" and frames[1][0] == 0x21   # really FF + CF


def test_t15_f3_160_bit_chain_and_a_partial_ecu():
    e8_pids = {0x01, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xA6, 0x0C, 0x5C, 0x7F, 0x9D}
    e9 = {"01 00": "41 00 " + bm(0, {0x05, 0x20}), "01 20": "41 20 " + bm(0x20, {0x33, 0x40})}
    bus, link, _st = _rig({0x7E8: chain(1, e8_pids), 0x7E9: e9})
    rep = _j(bus, CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)).supported()
    assert rep.ecus["7E8"].modes[1] == frozenset(e8_pids)
    assert rep.ecus["7E9"].modes[1] == frozenset({0x05, 0x20, 0x33, 0x40})
    assert rep.ecus["7E9"].partial == (1,)


def test_t15_f4_two_ecus_keyed_by_address():
    bus, link, _st = _rig({0x7E8: {"01 0C 0D": "41 0C 1A F8 0D 32"},
                           0x7E9: {"01 0C 0D": "41 0D 31"}}, ecu_kw={0x7E9: {"delay": 0.02}})
    r = _j(bus, CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)).read_pids([0x0C, 0x0D])
    assert r.get(0x0D, "vehicle_speed", "7E8").value == 50.0
    assert r.get(0x0D, "vehicle_speed", "7E9").value == 49.0
    assert r.get(0x0C, "engine_speed", "7E9") is None


def test_t15_f5_late_frame_is_dropped_and_counted():
    bus, link, _st = _rig({0x7E8: {"01 0C": "41 0C 1A F8", "01 0D": "41 0D 32"},
                           0x7E9: {"01 0C": "41 0C 00 00"}},
                          ecu_kw={0x7E9: {"late": {"01 0C": 0.120}}})
    j = _j(bus, CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep))
    assert [v.ecu for v in j.read_pids([0x0C]).values] == ["7E8"]
    r = j.read_pids([0x0D])                    # 7E9's late 41 0C lands in this window
    assert [(v.ecu, v.pid) for v in r.values] == [("7E8", 0x0D)]
    assert j.dropped == 1


def test_t15_f11_vin_over_ff_cf_fc_reaches_on_vin_only():
    vin = make_vin()
    bus, link, _st = _rig(_from_fake(can_two_ecu(vin)))
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)
    j = _j(bus, obd)
    j.supported()
    got: "list[str]" = []
    ident = j.read_identity(got.append)
    assert got == [vin] and ident.vin_delivered
    assert ident.ecus["7E8"].calid == ("OSTLERCAL0001",)
    assert ident.ecus["7E8"].cvn == ("12345678",)
    assert ident.ecus["7E9"].name == {"acronym": "TCM", "name": "TransControl"}
    assert vin not in repr(ident) and vin not in repr(j)


def test_29_bit_addressing():
    bus, link, _st = _rig({0x18DAF110: {"01 0D": "41 0D 32"},
                           0x18DAF118: {"01 0D": "41 0D 31"}}, extended=True)
    obd = CanObdRequestLink(link, extended=True, clock=bus.now, sleep=bus.sleep)
    assert obd.flavor == "can29"
    out = obd.request(b"\x01\x0D")
    assert {e: r.messages for e, r in out.items()} == {"18DAF110": (b"\x41\x0D\x32",),
                                                      "18DAF118": (b"\x41\x0D\x31",)}
    first = bus.tester_frames()[0][1]
    assert first.extended and first.id == 0x18DB33F1 and first.dlc == 8
    phys = obd.request(b"\x01\x0D", target="18DAF118")
    assert list(phys) == ["18DAF118"] and bus.tester_frames()[-1][1].id == 0x18DA18F1


def test_requests_are_padded_single_frames_and_guards_hold():
    bus, link, _st = _rig({0x7E8: {"01 0D": "41 0D 32"}})
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)
    obd.request(b"\x01\x0D")
    assert bus.tester_frames()[0][1].data == bytes.fromhex("02010D5555555555")
    with pytest.raises(ForbiddenService):
        obd.request(b"\x08\x00")
    with pytest.raises(ObdError):
        obd.request(b"\x01\x0C\x0D\x05\x0F\x11\x2F\x31")       # functional > 7 bytes
    assert len(bus.tester_frames()) == 1


def _clear_car(state: str, *, grant_for: bool = True):
    fake = _from_fake(can_two_ecu())
    bus, link, st = _rig(fake, state=state, allowlist=[CLEAR_ENTRY])
    gate = link.gate

    def mint(payload: bytes, tx: int):
        return gate.issue("obd_clear", 1)                     # the server gate (lab)
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep,
                            grant_for=mint if grant_for else None)
    j = _j(bus, obd)
    j.supported()
    cg = clr.ClearGate(clock=bus.now, allow_remote=False)
    reads = [*j.read_dtcs("stored").reads, *j.read_dtcs("pending").reads]
    p = clr.plan(reads, ecus=j.ecus())
    ctx = clr.ClearContext("alice", "driver", "head-unit", "head_unit", state)
    return bus, link, st, j, cg, cg.authorize(ctx, p, confirmed=True)


def test_mode04_over_can_needs_the_allowlist_and_a_tx_grant():
    bus, link, _st, j, cg, grant = _clear_car("parked")
    res = j.clear_dtcs(grant, gate=cg, snapshot_sink=lambda snap: "session#1")
    assert set(res.cleared) == {"7E8", "7E9"}
    fours = [f for _t, f in bus.tester_frames() if f.data[:2] == b"\x01\x04"]
    assert len(fours) == 1 and fours[0].id == 0x7DF


def test_mode04_over_can_without_a_tx_grant_is_refused_on_the_bus():
    bus, link, _st, j, cg, grant = _clear_car("parked", grant_for=False)
    with pytest.raises(TxRefused) as ei:
        j.clear_dtcs(grant, gate=cg, snapshot_sink=lambda snap: "session#1")
    assert ei.value.code == "no_grant"
    assert not [f for _t, f in bus.tester_frames() if f.data[:2] == b"\x01\x04"]
