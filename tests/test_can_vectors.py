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
    signature; ``unknown_key``: a key outside the trust store) and applies the ``token``
    perturbations; here they are spelled into the stand-in."""
    extra = "".join(f"|{k}={v}" for k, v in sorted((g.get("token") or {}).items()))
    return "test:" + g.get("signature", "valid") + extra


def _test_verifier(grant: TxGrant) -> str:
    """The fake verifier: only a grant 'signed' by the test key is valid; the token
    perturbations answer as ``openostler.signing.jws_grant_verifier`` does."""
    head, *pert = grant.token.split("|")
    pert = dict(p.split("=", 1) for p in pert)
    if head != "test:valid" or "header" in pert or "size" in pert:
        return "invalid"
    if "boot" in pert:
        return "expired"
    if "challenge" in pert:
        return "used"
    if "rh" in pert:
        return "mismatch"
    return "ok"


# Real tokens (the [signing] extra): the gate's grants are bound to one request; the
# runner signs the token answering each grant's challenge with a test key in the trust
# store, as the node's C runner does.
VEC_NODE, VEC_VID, VEC_BUS, VEC_BOOT = "vec-node", "vec", "obd", 7
VEC_REQUEST = {"action": "obd_clear", "params": {}, "role": "owner", "target": VEC_NODE,
               "user": "vector"}


class _Signer:
    def __init__(self) -> None:
        from openostler import signing
        from cryptography.hazmat.primitives.asymmetric import ed25519

        self.signing = signing
        self.key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
        self.other = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
        self.kid = signing.key_id(self.key)
        self.trust = {self.kid: self.key.public_key()}

    def rh(self, action: str, params: "dict | None" = None) -> str:
        return self.signing.request_hash({**VEC_REQUEST, "action": action,
                                          "params": params or {}})

    def token(self, g: dict, nonce: str, req: str) -> str:
        sg = self.signing
        pert = g.get("token") or {}
        claims = {"v": 1, "node": VEC_NODE, "vid": VEC_VID, "bus": VEC_BUS,
                  "action": g["action"], "tier": g["tier"], "origin": g["origin"],
                  "challenge": nonce if pert.get("challenge") != "other" else sg.b64url(b"x" * 16),
                  "ttl_ms": min(int(g.get("ttl", 10) * 1000), sg.MAX_TTL_MS), "req": req,
                  "boot": VEC_BOOT + (1 if pert.get("boot") == "other" else 0),
                  "rh": self.rh(g["action"], {"x": 1} if pert.get("rh") == "other" else None)}
        if pert.get("size") == "over_640":
            claims["req"] = "r" * 600
        key = self.other if g.get("signature") == "unknown_key" else self.key
        header = None
        if pert.get("header") == "extra_member":
            header = json.dumps({"alg": "EdDSA", "kid": self.kid, "jwk": sg.public_jwk(key)},
                                separators=(",", ":")).encode()
        elif pert.get("header") == "other_alg":
            header = json.dumps({"alg": "ES256", "kid": self.kid}, separators=(",", ":")).encode()
        tok = sg.sign_jws(sg.canonical_json(claims), key, self.kid, header=header)
        if g.get("signature") == "bad":
            h, pl, sig = tok.split(".")
            raw = bytearray(sg.b64url_decode(sig))
            raw[0] ^= 0x01
            tok = f"{h}.{pl}.{sg.b64url(bytes(raw))}"
        return tok


def _run_gate_case(case, signer: "_Signer | None") -> None:
    from dataclasses import replace

    defaults = _doc("gate")["defaults"]
    clock = {"t": 0.0}
    state = {"v": None}
    if signer is None:
        verifier = _test_verifier
    else:
        verifier = signer.signing.jws_grant_verifier(signer.trust, node=VEC_NODE, vid=VEC_VID,
                                                     bus=VEC_BUS, boot=VEC_BOOT)
    gate = TxGate(case.get("allowlist", ()), clock=lambda: clock["t"],
                  driving_state=lambda: state["v"],
                  allow_remote=case.get("allow_remote", defaults["allow_remote"]),
                  tier0_min_gap=defaults["tier0_min_gap"], fc_window=defaults["fc_window"],
                  sweep_window=defaults["sweep_window"], grant_verifier=verifier)
    grants: "dict[str, object]" = {}
    for name, g in case.get("grants", {}).items():
        req = f"req-{name}"
        if g.get("forged"):
            tok = signer.token(g, "forged", req) if signer else _token(g)
            grants[name] = TxGrant(g["action"], g["tier"], 1e9, "forged", g["origin"], tok,
                                   req, signer.rh(g["action"]) if signer else "")
            continue
        clock["t"] = g["at"]
        if "expect_mint" in g:
            with pytest.raises(TxRefused) as ei:
                gate.issue(g["action"], g["tier"], origin=g["origin"], ttl=g["ttl"],
                           token=_token(g))
            assert ei.value.code == g["expect_mint"]
            continue
        if signer is None:
            grants[name] = gate.issue(g["action"], g["tier"], origin=g["origin"], ttl=g["ttl"],
                                      token=_token(g))
        else:  # the challenge first, then the token answering it (spec §10)
            issued = gate.issue(g["action"], g["tier"], origin=g["origin"], ttl=g["ttl"],
                                req=req, rh=signer.rh(g["action"]))
            grants[name] = replace(issued, token=signer.token(g, issued.nonce, req))
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


@pytest.mark.parametrize("case", _cases("gate"))
def test_gate_vectors(case):
    _run_gate_case(case, None)


@pytest.mark.needs_signing
@pytest.mark.parametrize("case", _cases("gate"))
def test_gate_vectors_with_signed_tokens(case):
    """The same vectors with real Ed25519 JWS tokens and ``jws_grant_verifier`` (ADR-0041
    Confirmation: the helper's tokens pass the shared grant vectors)."""
    _run_gate_case(case, _Signer())
