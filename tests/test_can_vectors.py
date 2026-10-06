# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The shared CAN vectors (tests/vectors/can/, CanLink spec §7.1) against the Python
reference: ISO-TP segmentation, reassembly, FC, STmin and transmit outcomes, and the
TxGate decisions (T4, T5, T8, T17). The node's C port runs the same files (ADR-0032)."""
from __future__ import annotations

import json
import math
import pathlib
from collections import deque

import pytest

from openostler.can.frame import CanFrame
from openostler.can.gate import TIER0, AllowEntry, ProbeGrant, TxGate, TxGrant
from openostler.can.isotp import (
    IsoTpChannel,
    IsoTpError,
    Reassembler,
    fc_bytes,
    segment,
    stmin_seconds,
)
from openostler.can.link import CanLink, LinkCaps, TxRefused

_VEC = pathlib.Path(__file__).parent / "vectors" / "can"
KINDS = {"isotp", "gate"}


def _b(s: str) -> bytes:
    return bytes.fromhex(s)


def _h(b: bytes) -> str:
    return bytes(b).hex(" ").upper()


def _doc(kind: str) -> dict:
    for p in sorted(_VEC.glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert doc["format"] == "ostler-can-vectors/1"
        if doc["kind"] == kind:
            return doc
    raise AssertionError(f"no vectors of kind {kind}")


def _cases(kind: str, op: "str | None" = None):
    cases = [c for c in _doc(kind)["cases"] if op is None or c.get("op") == op]
    assert cases, (kind, op)
    return [pytest.param(c, id=c["id"]) for c in cases]


def test_every_vector_file_has_a_known_kind():
    files = list(_VEC.glob("*.json"))
    assert files
    for p in files:
        assert json.loads(p.read_text(encoding="utf-8"))["kind"] in KINDS, p.name


# ------------------------------------------------------------------- ISO-TP -- #

@pytest.mark.parametrize("case", _cases("isotp", "segment"))
def test_segment_vectors(case):
    pad = int(case["pad"], 16) if case["pad"] is not None else None
    if "error" in case["expect"]:
        with pytest.raises(IsoTpError) as ei:
            segment(bytes(case["payload_len"]), pad)
        assert ei.value.code == case["expect"]["error"]
        return
    assert [_h(f) for f in segment(_b(case["payload"]), pad)] == case["expect"]["frames"]


@pytest.mark.parametrize("case", _cases("isotp", "reassemble"))
def test_reassemble_vectors(case):
    a = Reassembler(case["bs"])
    got = []
    for f in case["frames"]:
        ev, val = a.feed(_b(f))
        got.append([ev, _h(val) if isinstance(val, bytes) else val])
    assert got == case["expect"]["events"]


@pytest.mark.parametrize("case", _cases("isotp", "fc"))
def test_fc_vectors(case):
    assert _h(fc_bytes(case["status"], case["bs"], case["stmin"], int(case["pad"], 16))) == \
        case["expect"]["frame"]


@pytest.mark.parametrize("case", _cases("isotp", "stmin"))
def test_stmin_vectors(case):
    for byte, secs in case["values"].items():
        assert math.isclose(stmin_seconds(int(byte, 16)), secs, abs_tol=1e-9), byte


class _ScriptLink(CanLink):
    """Hands the scripted FC frames to the sender, one per wait, on a virtual clock."""

    caps = LinkCaps(kind="vector")

    def __init__(self, fcs) -> None:
        self.t = 0.0
        super().__init__(gate=TxGate(clock=lambda: self.t), clock=lambda: self.t)
        self.fcs = deque(CanFrame(0x7E8, False, _b(f)) for f in fcs)
        self.sent: "list[bytes]" = []

    def _hw_open(self, bitrate, *, listen_only, one_shot) -> None: ...
    def _hw_close(self) -> None: ...
    def set_filters(self, filters) -> None: ...
    def flush_rx(self) -> int: return 0

    def _hw_send(self, frame) -> None:
        self.sent.append(frame.data)

    def _hw_recv(self, timeout):
        if self.fcs:
            return self.fcs.popleft()
        self.t += timeout or 0.0
        return None


@pytest.mark.parametrize("case", _cases("isotp", "transmit"))
def test_transmit_vectors(case):
    link = _ScriptLink(case["fcs"])
    link.gate._entries = [AllowEntry(0x7E0, "vector_tx", 1, data="xx xx 22")]
    link.gate.driving_state = lambda: "parked"
    link.open(500_000)
    link.confirm_rate("declared")
    sleeps: "list[float]" = []

    def sleep(s: float) -> None:
        sleeps.append(s)
        link.t += s
    ch = IsoTpChannel(link, 0x7E0, 0x7E8, clock=link.clock, sleep=sleep)
    pad = int(case["pad"], 16)
    assert pad == ch.params.pad
    grant = link.gate.issue("vector_tx", 1)
    result = "ok"
    try:
        ch.send(_b(case["payload"]), grant=grant)
    except IsoTpError as exc:
        result = exc.code
    assert result == case["expect"]["result"]
    assert [_h(f) for f in link.sent] == case["expect"]["frames"]


# --------------------------------------------------------------------- gate -- #

def _frame(d: dict) -> CanFrame:
    return CanFrame(int(d["id"], 16), d["ext"], _b(d["data"]))


def _token(g: dict) -> str:
    """A grant's stand-in token: the C runner signs with a test key (``bad``: a broken
    signature; ``unknown_key``: a key outside the trust store)."""
    return "test:" + g.get("signature", "valid")


def _test_verifier(grant: TxGrant) -> str:
    """The fake verifier: only a grant 'signed' by the test key is valid."""
    return "ok" if grant.token == "test:valid" else "invalid"


@pytest.mark.parametrize("case", _cases("gate"))
def test_gate_vectors(case):
    defaults = _doc("gate")["defaults"]
    clock = {"t": 0.0}
    state = {"v": None}
    gate = TxGate(case.get("allowlist", ()), clock=lambda: clock["t"],
                  driving_state=lambda: state["v"],
                  allow_remote=case.get("allow_remote", defaults["allow_remote"]),
                  tier0_min_gap=defaults["tier0_min_gap"], fc_window=defaults["fc_window"],
                  sweep_window=defaults["sweep_window"], grant_verifier=_test_verifier)
    grants: "dict[str, object]" = {}
    for name, g in case.get("grants", {}).items():
        if g.get("forged"):
            grants[name] = TxGrant(g["action"], g["tier"], 1e9, "forged", g["origin"],
                                   _token(g))
            continue
        clock["t"] = g["at"]
        if "expect_mint" in g:
            with pytest.raises(TxRefused) as ei:
                gate.issue(g["action"], g["tier"], origin=g["origin"], ttl=g["ttl"],
                           token=_token(g))
            assert ei.value.code == g["expect_mint"]
            continue
        grants[name] = gate.issue(g["action"], g["tier"], origin=g["origin"], ttl=g["ttl"],
                                  token=_token(g))
    for name, p in case.get("probes", {}).items():
        clock["t"], state["v"] = p["at"], p["driving_state"]
        if "expect_mint" in p:
            with pytest.raises(TxRefused) as ei:
                gate.probe_grant()
            assert ei.value.code == p["expect_mint"]
            continue
        grants[name] = gate.probe_grant()
    for i, step in enumerate(case["steps"]):
        clock["t"], state["v"] = step["t"], step["driving_state"]
        fr = _frame(step["frame"])
        if "probe" in step:
            pg = grants[step["probe"]]
            assert isinstance(pg, ProbeGrant)
            d = gate.decide_probe(fr, pg, one_shot=step["one_shot"], commit=True)
        else:
            g = step["grant"]
            grant = TIER0 if g == "tier0" else None if g is None else grants[g]
            d = gate.decide(fr, grant, rate_ok=step.get("rate_ok", defaults["rate_ok"]),
                            link_kind=step.get("link_kind", defaults["link_kind"]),
                            commit=True)
        e = step["expect"]
        assert (d.allowed, d.reason) == (e["allowed"], e["reason"]), (case["id"], i)
        if "action" in e:
            assert d.action == e["action"]
