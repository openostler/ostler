# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Passive bitrate and ID-width detection (ADR-0023, CanLink spec §4; tests T1–T3, T5–T7,
T17) on the fake bus. No hardware."""
from __future__ import annotations

from openostler.can import LinkCaps, RateMemory, TxGate, detect
from openostler.can.detect import NOT_CONFIRMED
from openostler.can.link import CONFIRMED, LISTENING
from openostler.can.slcan import SlcanLink
from tests.fake_can import FakeCanBus, FakeCanLink, FakeObdEcu, FakeSlcanDevice

R0100 = "41 00 BE 1F A8 13"


def _rig(rate=500_000, *, traffic=True, ext=False, ecu=True, caps=None, state="moving"):
    bus = FakeCanBus(rate)
    if traffic:
        bus.periodic(0x18FEF100 if ext else 0x100, period=0.010, extended=ext)
    if ecu:
        FakeObdEcu(bus, 0x18DAF110 if ext else 0x7E8, {"01 00": R0100}, extended=ext)
    st = {"v": state}
    gate = TxGate(clock=bus.now, driving_state=lambda: st["v"])
    link = FakeCanLink(bus, gate=gate, caps=caps)
    return bus, link, st


def test_t1_500k_locks_after_20_clean_frames_and_sends_nothing_before():
    bus, link, _st = _rig()
    res = detect(link)
    assert res.ok and res.rate == 500_000 and res.source == "detected"
    assert res.frames == 20 and res.errors == 0 and res.widths == frozenset({11})
    assert res.ecus == ("7E8",)
    sent = bus.tester_frames()
    assert len(sent) == 1                                   # the one 01 00, nothing before
    t_lock = sent[0][0]
    assert sent[0][1].id == 0x7DF and sent[0][1].data[:3] == b"\x02\x01\x00"
    heard = [ts for ts, who, _f in bus.transmitted if who == "traffic" and ts < t_lock]
    assert len(heard) >= 20                                 # the 20 clean frames came first
    assert link.opens[0] == (500_000, True, False)          # listen-only, error reporting on
    assert link.state == CONFIRMED and link.listen_only     # back to listen-only afterwards


def test_t2_error_frame_at_500k_moves_to_250k():
    bus, link, _st = _rig(250_000)
    res = detect(link)
    assert res.rate == 250_000 and res.source == "detected"
    assert [s["rate"] for s in res.log if s["step"] == "listen"] == [500_000, 250_000]
    assert res.log[0]["errors"] == 1 and not res.log[0]["clean"]
    assert len(bus.tester_frames()) == 1 and link.bitrate == 250_000


def test_t3_29_bit_only_traffic_gets_18db33f1():
    bus, link, _st = _rig(ext=True)
    res = detect(link)
    assert res.widths == frozenset({29}) and res.ecus == ("18DAF110",)
    first = bus.tester_frames()[0][1]
    assert first.extended and first.id == 0x18DB33F1


def test_no_reply_tries_the_other_width_once():
    bus = FakeCanBus(500_000)
    bus.periodic(0x100, period=0.010)
    FakeObdEcu(bus, 0x18DAF110, {"01 00": R0100}, extended=True)
    link = FakeCanLink(bus, gate=TxGate(clock=bus.now))
    res = detect(link)
    ids = [f.id for _t, f in bus.tester_frames()]
    assert ids == [0x7DF, 0x18DB33F1]
    assert res.ecus == ("18DAF110",) and res.widths == frozenset({11, 29})


def test_t5_silent_bus_refused_unless_parked():
    bus, link, _st = _rig(traffic=False, state="moving")
    res = detect(link)
    assert not res.ok and "Parked" in res.reason and res.reason.startswith(NOT_CONFIRMED)
    assert bus.tester_frames() == [] and all(not one for _r, _lo, one in link.opens)
    assert link.state == LISTENING and link.listen_only
    unknown = _rig(traffic=False, state=None)[1]            # unknown counts as Moving
    assert not detect(unknown).ok


def test_t5_silent_bus_parked_probes_one_shot_and_confirms():
    bus, link, _st = _rig(traffic=False, state="parked")
    res = detect(link)
    assert res.ok and res.rate == 500_000 and res.source == "probe"
    assert res.ecus == ("7E8",)
    oneshots = [o for o in link.opens if o[2]]
    assert oneshots == [(500_000, False, True)]             # one frame, one-shot, at 500k
    assert len(bus.tester_frames()) == 1
    assert link.opens[-1] == (500_000, True, False) and link.rate_source == "probe"


def test_t5_empty_bus_one_probe_per_rate_then_not_confirmed():
    bus, link, _st = _rig(traffic=False, ecu=False, state="parked")
    res = detect(link)
    assert not res.ok and res.reason == NOT_CONFIRMED
    assert [o for o in link.opens if o[2]] == [(500_000, False, True), (250_000, False, True)]
    assert link.listen_only and link.opens[-1][1] is True


def test_t5_first_error_frame_stops_detection():
    bus, link, _st = _rig(250_000, traffic=False, state="parked")
    res = detect(link)
    assert not res.ok and res.reason == NOT_CONFIRMED and res.errors == 1
    assert [o for o in link.opens if o[2]] == [(500_000, False, True)]   # no 250k probe
    assert link.listen_only and link.opens[-1] == (500_000, True, False)


def test_t5_no_one_shot_capability_refuses_the_probe():
    caps = LinkCaps(kind="fake", one_shot=False)
    bus, link, _st = _rig(traffic=False, state="parked", caps=caps)
    res = detect(link)
    assert not res.ok and "one-shot" in res.reason
    assert bus.tester_frames() == [] and all(not o[2] for o in link.opens)


def test_t17_moving_before_the_250k_probe_refuses_it():
    bus, link, st = _rig(traffic=False, ecu=False, state="parked")
    orig = link._hw_oneshot

    def oneshot(frame, timeout):
        out = orig(frame, timeout)
        st["v"] = "moving"                     # the car drives off after the 500k probe
        return out
    link._hw_oneshot = oneshot
    res = detect(link)
    assert not res.ok and "Parked" in res.reason
    assert [o for o in link.opens if o[2]] == [(500_000, False, True)]
    assert res.log[-1] == {"step": "probe", "rate": 250_000, "refused": "not_parked"}
    assert link.listen_only


def test_t6_declared_rate_skips_detection_and_probe():
    bus, link, _st = _rig(traffic=False, ecu=False, state="parked")
    res = detect(link, declared=250_000, declared_widths=frozenset({29}))
    assert res.ok and res.rate == 250_000 and res.source == "declared"
    assert link.opens == [(250_000, True, False)] and bus.tester_frames() == []
    assert link.rate_confirmed and link.rate_source == "declared"
    assert link.id_widths == frozenset({29})


def test_t7_slcan_flags_only_reject_the_rate():
    bus = FakeCanBus(250_000)
    bus.periodic(0x100, period=0.010)
    FakeObdEcu(bus, 0x7E8, {"01 00": R0100})
    dev = FakeSlcanDevice(bus)
    link = SlcanLink(dev, gate=TxGate(clock=bus.now), clock=bus.now)
    assert link.caps.error_frames == "flags" and link.caps.listen_only is True
    res = detect(link)
    listen = [s for s in res.log if s["step"] == "listen"]
    assert listen[0]["rate"] == 500_000 and listen[0]["errors"] == 1 and listen[0]["frames"] == 0
    assert res.rate == 250_000 and res.ecus == ("7E8",)
    assert "S6" in dev.commands and "S5" in dev.commands and "F" in dev.commands
    assert dev.commands.index("L") < dev.commands.index("S5")       # opened listen-only first


def test_noisy_bus_stays_listen_only_and_unconfirmed():
    bus, link, _st = _rig(state="parked")
    for i in range(1, 60):
        bus.error_at(i * 0.1)
    res = detect(link)
    assert not res.ok and res.reason == NOT_CONFIRMED
    assert bus.tester_frames() == [] and link.listen_only and not link.rate_confirmed


def test_remembered_rate_only_sets_the_order(tmp_path):
    bus, link, _st = _rig(250_000)
    res = detect(link, remembered=250_000)
    assert [s["rate"] for s in res.log if s["step"] == "listen"] == [250_000]
    mem = RateMemory(tmp_path / "can_rates.json")
    mem.remember("vid-1", res)
    assert mem.get("vid-1") == 250_000 and mem.get("other") is None
    assert "vid-1" in (tmp_path / "can_rates.json").read_text()
    declared = detect(_rig()[1], declared=500_000)
    mem.remember("vid-2", declared)                          # a declared rate is not learnt
    assert mem.get("vid-2") is None
