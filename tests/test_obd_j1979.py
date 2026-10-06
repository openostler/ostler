# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The J1979 service layer against scripted links (spec §2, §4, §6, §7; fixtures F3–F5,
F9–F15 and the golden SupportReports). No hardware."""
from __future__ import annotations

import json
import logging

import pytest

from openostler.obd import J1979, Pacer
from openostler.obd import diagnostics as diag
from openostler.obd.link import EcuReply, PacedLink, classify
from openostler.testing import FakeObdLink
from tests.obd_fakes import GOLDEN, bm, can_two_ecu, chain, kline_petrol, make_vin, table


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: "list[float]" = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += s


def _j(link, **kw) -> J1979:
    c = _Clock()
    return J1979(link, table(), pacer=Pacer(clock=c, sleep=c.sleep), clock=c, **kw)


# ---------------------------------------------------------------- discovery -- #

def test_f3_160_bit_chain_and_a_partial_ecu():
    e8_pids = {0x01, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xA6, 0x0C, 0x5C, 0x7F, 0x9D}
    e8 = chain(1, e8_pids)
    assert len(e8) == 6                        # 00 20 40 60 80 A0: 160+ bits, no array
    e9 = {"01 00": "41 00 " + bm(0, {0x05, 0x20}), "01 20": "41 20 " + bm(0x20, {0x33, 0x40})}
    j = _j(FakeObdLink({"7E8": e8, "7E9": e9}))
    rep = j.supported()
    assert rep.ecus["7E8"].modes[1] == frozenset(e8_pids)
    assert rep.ecus["7E8"].partial == ()
    assert rep.ecus["7E9"].modes[1] == frozenset({0x05, 0x20, 0x33, 0x40})   # no index drift
    assert rep.ecus["7E9"].partial == (1,)


def test_golden_support_reports():
    for name, link in (("support_can_two_ecu", can_two_ecu()),
                       ("support_kline_petrol", kline_petrol())):
        rep = _j(link).supported().to_dict()
        golden = json.loads((GOLDEN / f"{name}.json").read_text(encoding="utf-8"))
        assert rep == golden, name
        assert make_vin() not in json.dumps(rep)
        assert not any(p.startswith(b"\x09\x02") for p in link.payloads())  # no VIN read


# ------------------------------------------------------------------- values -- #

def test_f4_two_ecus_keyed_by_address():
    j = _j(can_two_ecu())
    j.supported()
    r = j.read_pids([0x0C, 0x0D])
    assert r.get(0x0D, "vehicle_speed", "7E8").value == 50.0
    assert r.get(0x0D, "vehicle_speed", "7E9").value == 49.0
    assert r.get(0x0C, "engine_speed", "7E8").value == 1726.0
    assert r.get(0x0C, "engine_speed", "7E9") is None          # absent, never zero
    assert r.get(0x0C, "engine_speed", "7E8").metric == "Vehicle.Powertrain.CombustionEngine.Speed"
    assert all(v.confidence == "candidate" for v in r.values)


def test_kline_reads_one_pid_per_request():
    link = kline_petrol()
    j = _j(link)
    j.supported()
    link.sent.clear()
    r = j.read_pids([0x05, 0x0C, 0x0D, 0x0F])                 # 0F unsupported → skipped
    assert [p for p, _t in link.sent] == [b"\x01\x05", b"\x01\x0C", b"\x01\x0D"]
    assert r.get(0x05, "coolant_temp", "10").value == 50.0


def test_f5_late_frame_is_dropped_and_counted():
    link = FakeObdLink({"7E8": {"01 0C": "41 0C 1A F8", "01 0D": "41 0D 32"}},
                       late={"01 0C": [("7E9", "41 0C 00 00")]})
    j = _j(link)
    assert j.read_pids([0x0C]).get(0x0C, "engine_speed").value == 1726.0
    r = j.read_pids([0x0D])
    assert [(v.ecu, v.pid) for v in r.values] == [("7E8", 0x0D)]
    assert j.dropped == 1


def test_negative_and_no_reply_are_typed():
    link = FakeObdLink({"7E8": {"01 0D": "7F 01 12"}, "7E9": {}})
    res, dropped = classify(b"\x01\x0D", link.request(b"\x01\x0D"), ("7E8", "7E9"))
    assert res["7E8"].status == "negative" and res["7E8"].nrc == 0x12
    assert res["7E9"].status == "no_reply" and dropped == 0
    r = _j(link).read_pids([0x0D], ecu="7E8")
    assert not r.values and r.errors[0].status == "negative" and r.errors[0].nrc == 0x12


# ------------------------------------------------------------- DTC and freeze -- #

def test_dtcs_per_ecu_and_kline_multi_message():
    j = _j(can_two_ecu())
    j.supported()
    res = j.read_dtcs("stored")
    assert res.codes("7E8") == ["P0133", "P0300"] and res.codes("7E9") == ["P0700"]
    assert j.read_dtcs("pending").codes() == ["P0171", "P0171"]
    # 0A: only 7E8 answered the probe; nothing stored → a read with no codes
    assert j.read_dtcs("permanent").reads[0].dtcs == ()
    k = _j(kline_petrol())
    assert k.read_dtcs("stored").codes() == ["P0133", "P0134", "P0300", "P0170"]


def test_f9_freeze_frame_trigger_and_values():
    j = _j(can_two_ecu())
    j.supported()
    ff = j.read_freeze_frame("7E8")
    assert ff.trigger.code == "P0133" and ff.stored
    assert {(v.pid, v.signal, v.value) for v in ff.values} == {
        (0x05, "coolant_temp", 50.0), (0x0C, "engine_speed", 1726.0)}
    assert all(v.mode == 0x02 for v in ff.values)
    none = j.read_freeze_frame("7E9")
    assert none.trigger is None and not none.stored and none.values == ()
    k = _j(kline_petrol())                         # no report: the 02 chain is walked
    kf = k.read_freeze_frame("10")
    assert kf.trigger.code == "P0133" and [v.value for v in kf.values] == [50.0]


# ---------------------------------------------------- readiness, diagnostics -- #

def test_f10_readiness_and_diagnostics_leaves():
    j = _j(can_two_ecu())
    j.supported()
    rd = j.read_readiness()
    assert rd["7E8"].mil is True and rd["7E8"].dtc_count == 3
    assert rd["7E9"].incomplete == []
    d41 = j.read_readiness(0x41)["7E8"]
    assert d41.mil is None and d41.incomplete == ["evap"]
    d = j.diagnostics()
    assert d.values == {
        diag.MIL_ON: True, diag.DTC_COUNT: 3, diag.IS_READINESS_COMPLETE: False,
        diag.READINESS_INCOMPLETE_COUNT: 2, diag.PENDING_DTC_COUNT: 1,
        diag.DISTANCE_SINCE_DTC_CLEAR: 100_000.0}
    assert d.sources[diag.PENDING_DTC_COUNT] == {"7E8": 1, "7E9": 1}
    assert d.sources[diag.MIL_ON] == {"7E8": True, "7E9": False}


def test_diagnostics_distance_without_an_engine_ecu_takes_the_largest():
    d = diag.derive({}, None, {"7EA": 1000.0, "7EB": 2500.0})
    assert d.values == {diag.DISTANCE_SINCE_DTC_CLEAR: 2500.0}
    assert diag.derive({}).values == {}       # no input → absent, never zero


# ------------------------------------------------------------------ Mode 06 -- #

def test_f15_mode06_can_and_kline_raw():
    j = _j(can_two_ecu())
    j.supported()
    m = j.read_monitor_tests()
    assert len(m.tests) == 1 and m.tests[0].passed and m.tests[0].unit == "mV"
    k = _j(kline_petrol())
    k.supported()
    km = k.read_monitor_tests()
    assert km.tests == () and km.raw[0].data == bytes.fromhex("001234")
    assert km.raw[0].confidence == "candidate"


# ---------------------------------------------------------- Mode 09 and VIN -- #

def test_f11_identity_can_and_kline_counts():
    vin = make_vin()
    got: "list[str]" = []
    j = _j(can_two_ecu(vin))
    j.supported()
    ident = j.read_identity(got.append)
    assert got == [vin] and ident.vin_delivered
    assert ident.ecus["7E8"].calid == ("OSTLERCAL0001",)
    assert ident.ecus["7E8"].cvn == ("12345678",)
    assert ident.ecus["7E9"].name == {"acronym": "TCM", "name": "TransControl"}
    link = kline_petrol(vin)
    k = _j(link)
    k.supported()
    got.clear()
    kid = k.read_identity(got.append)
    assert got == [vin] and kid.ecus["10"].calid == ("OSTLERCAL0001",)
    assert kid.ecus["10"].cvn == ("DEADBEEF",)
    # the K-line message counts (09 01/03/05) are passed down as expect_messages
    sent = dict(zip(link.payloads(), link.expects))
    assert sent[b"\x09\x02"] == 5 and sent[b"\x09\x04"] == 4 and sent[b"\x09\x06"] == 1


def test_f12_vin_never_in_results_reprs_logs_or_exceptions(caplog):
    vin = make_vin()
    vin_hex = vin.encode().hex()
    caplog.set_level(logging.DEBUG)
    j = _j(can_two_ecu(vin))
    rep = j.supported()
    ident = j.read_identity(lambda v: None)
    for obj in (rep, rep.to_dict(), ident, j, ident.ecus):
        text = repr(obj) + str(obj)
        assert vin not in text and vin_hex not in text.replace(" ", "").lower()
    # a failing callback's text (which may quote the VIN) never surfaces
    def boom(v: str) -> None:
        raise ValueError(f"bad vin {v}")
    with pytest.raises(Exception) as ei:
        j.read_identity(boom)
    err = ei.value
    assert vin not in str(err) and vin not in repr(err)
    assert err.__cause__ is None and err.__suppress_context__
    assert vin not in caplog.text
    # an EcuStatus never prints its messages
    link = can_two_ecu(vin)
    st, _ = classify(b"\x09\x02", link.request(b"\x09\x02"))
    assert vin not in repr(st) and vin_hex not in repr(st).lower()


def test_malformed_vin_is_reported_without_bytes():
    j = _j(FakeObdLink({"7E8": {"09 02": "49 02 01 41 42 43"}}))
    got: "list[str]" = []
    ident = j.read_identity(got.append)
    assert got == [] and not ident.vin_delivered
    assert [(e.pid, e.status, e.reason) for e in ident.errors if e.pid == 2] == \
        [(0x02, "malformed", "vin_format")]


# ------------------------------------------------------------------- pacing -- #

def test_pacing_50ms_per_ecu_and_busy_backoff():
    c = _Clock()
    calls: "list[float]" = []

    class Busy:
        flavor = "can11"

        def request(self, payload, *, target=None, expect_messages=None, timeout=None):
            calls.append(c.t)
            if len(calls) <= 3:
                return {"7E8": EcuReply("7E8", (b"\x7F\x01\x21",))}
            return {"7E8": EcuReply("7E8", (b"\x41\x0D\x32",))}

    link = PacedLink(Busy(), Pacer(clock=c, sleep=c.sleep))
    out = link.request(b"\x01\x0D")
    assert out["7E8"].messages == (b"\x41\x0D\x32",)
    assert c.sleeps == [0.05, 0.1, 0.2]
    gaps = [b - a for a, b in zip(calls, calls[1:])]
    assert all(g >= 0.05 - 1e-9 for g in gaps)
    assert len(calls) == 4                         # first try + 50, 100, 200 ms back-off
    assert pytest.approx(calls[-1] - calls[0], abs=1e-9) == 0.05 + 0.10 + 0.20


# --------------------------------------------------------------- the store -- #

def test_store_gains_s8_and_u32_kinds():
    from openostler.signals import Signal

    assert Signal("x", 0x01, 0, kind="s8").decode(b"\xFF") == -1.0
    assert Signal("x", 0x01, 0, kind="s8").decode(b"\x7F") == 127.0
    s = Signal("odo", 0xA6, 0, kind="u32", scale=0.1)
    assert s.fits(b"\x00\x01\xE2\x40") and not s.fits(b"\x00\x01\xE2")
    assert s.decode(b"\x00\x01\xE2\x40") == pytest.approx(12345.6)


def test_pid_fixture_is_a_valid_store_file():
    jsonschema = pytest.importorskip("jsonschema")
    from tests.obd_fakes import PIDS

    root = PIDS.parents[3] / "schemas" / "signal-store.schema.json"
    jsonschema.validate(json.loads(PIDS.read_text(encoding="utf-8")),
                        json.loads(root.read_text(encoding="utf-8")))


def test_pid_table_lengths_and_mode02_fallback():
    t = table()
    assert t.length(0x01, 0x24) == 4 and t.length(0x01, 0x0C) == 2
    assert t.entry(0x02, 0x05) is t.entry(0x01, 0x05)
    assert t.length(0x01, 0x7E) is None and 0x0C in t.pids()
