# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The shared J1979 vectors (tests/vectors/j1979/, spec §9–§10.1) against the Python
reference decoders. The future C link layer runs the same files (ADR-0032)."""
from __future__ import annotations

import json
import math
import pathlib

import pytest

from openostler.obd import clear as clr
from openostler.obd import decode as dec
from openostler.obd.pids import PidTable

_VEC = pathlib.Path(__file__).parent / "vectors" / "j1979"
_PIDS = pathlib.Path(__file__).parent / "fixtures" / "j1979" / "pids.json"
TABLE = PidTable.from_records(json.loads(_PIDS.read_text(encoding="utf-8")))


def _b(s: str) -> bytes:
    return bytes.fromhex(s)


def _h(s: str) -> int:
    return int(s, 16)


def _cases(decoder: str):
    out = []
    for p in sorted(_VEC.glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert doc["format"] == "ostler-j1979-vectors/1"
        if doc["decoder"] == decoder:
            out += [pytest.param(c, id=f"{p.stem}:{c['id']}") for c in doc["cases"]]
    assert out, f"no vectors for {decoder}"
    return out


def _close(a, b) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, rel_tol=0, abs_tol=1e-6)


def test_every_vector_file_has_a_known_decoder():
    known = {"dtc", "bitmap", "pids", "freeze_trigger", "readiness", "mode06", "mode09",
             "clear_gate"}
    for p in _VEC.glob("*.json"):
        assert json.loads(p.read_text(encoding="utf-8"))["decoder"] in known, p.name


@pytest.mark.parametrize("case", _cases("dtc"))
def test_dtc_vectors(case):
    msgs = tuple(_b(m) for m in case["messages"])
    r = dec.decode_dtcs(case["flavor"], _h(case["mode"]), msgs, case["ecu"])
    assert r.kind == case["expect"]["kind"]
    assert r.codes == case["expect"]["codes"]
    assert list(r.warnings) == case["expect"]["warnings"]
    assert all(d.ecu == case["ecu"] for d in r.dtcs)


@pytest.mark.parametrize("case", _cases("bitmap"))
def test_bitmap_vectors(case):
    block = _h(case["block"])
    pids = dec.bitmap_pids(block, _b(case["data"]))
    assert sorted(pids) == [_h(p) for p in case["expect"]["pids"]]
    assert dec.bitmap_chains(block, pids) is case["expect"]["chains"]


@pytest.mark.parametrize("case", _cases("pids"))
def test_pid_vectors(case):
    mode = _h(case["mode"])
    values, errors = dec.walk_pids(TABLE, mode, _b(case["message"]), case["ecu"], 0.0)
    got = [(f"{v.pid:02X}", v.signal, v.unit) for v in values]
    want = [(e["pid"], e["signal"], e["unit"]) for e in case["expect"]["values"]]
    assert got == want
    for v, e in zip(values, case["expect"]["values"]):
        assert _close(v.value, e["value"]), (v.signal, v.value, e["value"])
        assert v.ecu == case["ecu"] and v.mode == mode
    assert [(f"{e.pid:02X}", e.status, e.reason) for e in errors] == \
        [(e["pid"], e["status"], e["reason"]) for e in case["expect"]["errors"]]


@pytest.mark.parametrize("case", _cases("freeze_trigger"))
def test_freeze_trigger_vectors(case):
    t = dec.decode_freeze_trigger(_b(case["message"])[3:5], case["ecu"])
    assert (t.code if t else None) == case["expect"]["trigger"]


@pytest.mark.parametrize("case", _cases("readiness"))
def test_readiness_vectors(case):
    msg = _b(case["message"])
    r = dec.decode_readiness(msg[2:6], case["ecu"], _h(case["pid"]))
    e = case["expect"]
    assert (r.mil, r.dtc_count, r.ignition) == (e["mil"], e["dtc_count"], e["ignition"])
    assert {n: [m.supported, m.complete] for n, m in r.monitors.items()} == e["monitors"]
    assert r.incomplete == e["incomplete"]


@pytest.mark.parametrize("case", _cases("mode06"))
def test_mode06_vectors(case):
    tests, errors = dec.decode_mode06_can(_b(case["message"]), case["ecu"])
    assert errors == case["expect"]["errors"]
    assert len(tests) == len(case["expect"]["tests"])
    for t, e in zip(tests, case["expect"]["tests"]):
        assert (f"{t.mid:02X}", f"{t.tid:02X}", f"{t.uasid:02X}") == (e["mid"], e["tid"], e["uasid"])
        assert _close(t.value, e["value"]) and _close(t.min, e["min"]) and _close(t.max, e["max"])
        assert (t.unit, t.passed, t.warning) == (e["unit"], e["passed"], e["warning"])


@pytest.mark.parametrize("case", _cases("mode09"))
def test_mode09_vectors(case):
    msgs = tuple(_b(m) for m in case["messages"])
    if "count_message" in case:
        assert dec.info_count(_b(case["count_message"])) == len(msgs)
    payload = dec.info_payload(case["flavor"], msgs)
    e = case["expect"]
    if "calid" in e:
        assert dec.calid_strings(payload) == e["calid"]
    if "cvn" in e:
        assert dec.cvn_strings(payload) == e["cvn"]
    if "name" in e:
        assert dec.ecu_name(payload) == e["name"]


@pytest.mark.parametrize("case", _cases("clear_gate"))
def test_clear_gate_vectors(case):
    reads = [dec.DtcRead(r["ecu"], r["kind"], tuple(
        dec.Dtc(c, "", r["ecu"], r["kind"]) for c in r["codes"])) for r in case["reads"]]
    p = clr.plan(reads, read_only_ecus=case["read_only_ecus"])
    ctx = clr.ClearContext(**case["context"])
    audit: list = []
    gate = clr.ClearGate(clock=lambda: 0.0, audit=audit.append,
                         allow_remote=case["allow_remote"])
    e = case["expect"]
    if e["allowed"]:
        g = gate.authorize(ctx, p, confirmed=case["confirmed"])
        assert g.plan is p and g.category == "maintenance" and g.tier == 1
        assert not audit
    else:
        with pytest.raises(clr.ClearRefused) as ei:
            gate.authorize(ctx, p, confirmed=case["confirmed"])
        assert ei.value.code == e["reason"]
        assert audit and audit[-1]["outcome"] == "refused" and audit[-1]["reason"] == e["reason"]
    if "warning" in e:
        assert (p.warning is not None) is e["warning"]
    if "ecus" in e:
        assert list(p.ecus) == e["ecus"]
