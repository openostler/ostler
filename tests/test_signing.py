# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The Brain's grant signing (ADR-0041; module-bus spec v1.3 §10): the stdlib half always,
the Ed25519 half with the ``[signing]`` extra (``needs_signing``; required in CI), and a
subprocess proving that core and the server load without ``cryptography`` and that minting
then says "not installed". The shared gate vectors with real tokens are in
``tests/test_can_vectors.py``."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import subprocess
import sys
import textwrap

import pytest

from openostler import signing as sg

# RFC 8037 Appendix A.1 (the Ed25519 key) and A.4 (the JWS of "Example of Ed25519 signing").
RFC8037_D = "nWGxne_9WmC6hEr0kuwsxERJxWl7MmkZcDusAxyuf2A"
RFC8037_X = "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"
RFC8037_THUMBPRINT = "kPrK_qmxVWaYVA9wwBF6Iuo3vVzz7TxHCTwXBygrS4k"     # A.3
RFC8037_JWS = ("eyJhbGciOiJFZERTQSJ9.RXhhbXBsZSBvZiBFZDI1NTE5IHNpZ25pbmc."
               "hgyY0il_MGCjP0JzlnLWG1PPOt7-09PGcvMg3AIbQR6dWbhijcNR4ki4iylGjg5BhVsPt9g7sVvpAr_MuM0KAg")
# RFC 8032 §7.1, TEST 1 and TEST 2: (secret key, public key, message, signature).
RFC8032 = [
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
]
REQUEST = {"id": "01J9ZK4Y6W8R3V5T7N2M1QXCDE", "target": "node", "action": "obd_clear",
           "params": {"ecus": ["7E0"], "b": 1}, "category": "maintenance", "tier": 1,
           "user": "owner-1", "role": "owner", "transport": "local", "origin": "local",
           "need": "challenge"}
CHALLENGE = {"id": REQUEST["id"], "state": "challenge", "challenge": "AAECAwQFBgcICQoLDA0ODw",
             "boot": 2734, "t_us": 123456, "ttl_ms": 8000}


# ---------------------------------------------------------------- stdlib half -------- #
def test_canonical_json_follows_the_etag_rules():
    assert sg.canonical_json({"b": [1, {"z": 1, "a": "é"}], "a": None}) == \
        '{"a":null,"b":[1,{"a":"é","z":1}]}'.encode()


def test_rh_is_the_sha256_of_the_five_request_fields():
    body = {k: REQUEST[k] for k in ("action", "params", "role", "target", "user")}
    want = base64.urlsafe_b64encode(hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).digest()
    ).rstrip(b"=").decode()
    assert sg.request_hash(REQUEST) == want and len(want) == 43
    # any other field may change; the five may not
    assert sg.request_hash({**REQUEST, "tier": 3, "need": None}) == want
    assert sg.request_hash({**REQUEST, "params": {"ecus": ["7E1"], "b": 1}}) != want


def test_the_claims_are_checked():
    c = sg.claims_for_challenge(REQUEST, CHALLENGE, node="node", vid="d2-bench",
                                bus="kline-diag")
    assert list(c) == list(sg.CLAIMS) and c["boot"] == 2734 and c["ttl_ms"] == 8000
    assert c["req"] == REQUEST["id"] and c["rh"] == sg.request_hash(REQUEST)
    for bad in ({"tier": 4}, {"ttl_ms": 10_001}, {"origin": "cloud"}, {"boot": -1},
                {"challenge": "not base64!"}, {"node": ""}):
        with pytest.raises(ValueError):
            sg.check_claims({**c, **bad})
    with pytest.raises(ValueError):
        sg.check_claims({**c, "extra": 1})
    with pytest.raises(ValueError):  # an outcome for another request
        sg.claims_for_challenge(REQUEST, {**CHALLENGE, "id": "x"}, node="n", vid="v", bus="b")


def test_the_header_is_pinned():
    assert sg.header_bytes("k1") == b'{"alg":"EdDSA","kid":"k1"}'
    assert sg.check_header(sg.b64url(b'{"alg":"EdDSA","kid":"k1"}')) == "k1"
    for hdr in ({"alg": "EdDSA"}, {"alg": "none", "kid": "k1"}, {"alg": "ES256", "kid": "k1"},
                {"alg": "EdDSA", "kid": "k1", "jwk": {}}, {"alg": "EdDSA", "kid": "k1", "b64": False},
                {"alg": "EdDSA", "kid": "k1", "crit": ["b64"]}, {"alg": "EdDSA", "kid": ""}):
        with pytest.raises(sg.GrantInvalid):
            sg.check_header(sg.b64url(json.dumps(hdr).encode()))
    with pytest.raises(sg.GrantInvalid):
        sg.split_token("a." * 400 + "b")
    with pytest.raises(sg.GrantInvalid):
        sg.split_token("a.b")


def test_core_and_the_server_load_without_cryptography():
    """ADR-0041 Confirmation: with ``cryptography`` unimportable, ``openostler``, its server
    and the signing module load, and minting says "not installed" (fail closed)."""
    code = textwrap.dedent("""
        import sys
        class Block:
            def find_spec(self, name, path=None, target=None):
                if name == "cryptography" or name.startswith("cryptography."):
                    raise ImportError("blocked for the test")
        sys.meta_path.insert(0, Block())
        import openostler, openostler.web.server, openostler.web.node_source
        from openostler import signing
        from openostler.can.gate import TxGrant
        assert not signing.signing_available()
        try:
            signing.sign_grant({}, b"x" * 32, "kid")
        except ValueError:
            pass  # the claims are checked first
        claims = signing.grant_claims(node="n", vid="v", bus="b", action="a", tier=1,
                                      origin="local", challenge="AAAA", ttl_ms=1000,
                                      req="r", boot=1, rh="AAAA")
        try:
            signing.sign_grant(claims, b"x" * 32, "kid")
            raise SystemExit("signed without the extra")
        except signing.SigningUnavailable as exc:
            assert "Signing not installed on the Brain" in str(exc)
        v = signing.jws_grant_verifier({}, node="n", vid="v", bus="b", boot=1)
        assert v(TxGrant("a", 1, 1e9, "n", token="x.y.z")) == "invalid"
        assert signing.brain_key("/nonexistent") is None
        assert not any(m.startswith("cryptography") for m in sys.modules)
        print("ok")
    """)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)})
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "ok"


# ---------------------------------------------------------------- the extra ---------- #
needs_signing = pytest.mark.needs_signing


@needs_signing
@pytest.mark.parametrize("sk,pk,msg,sig", RFC8032)
def test_rfc8032_vectors(sk, pk, msg, sig):
    from cryptography.hazmat.primitives.asymmetric import ed25519

    key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(sk))
    assert sg.public_bytes(key).hex() == pk
    assert key.sign(bytes.fromhex(msg)).hex() == sig      # the library signs as RFC 8032
    if not msg:
        return  # a JWS with an empty payload is never a grant (split_token refuses it)
    # and a JWS made by the helper verifies under the vector's public key
    tok = sg.sign_jws(bytes.fromhex(msg), key, header=b'{"alg":"EdDSA"}')
    assert sg.verify_jws(tok, bytes.fromhex(pk)) == bytes.fromhex(msg)


@needs_signing
def test_rfc8037_jws_example_and_thumbprint():
    from cryptography.hazmat.primitives.asymmetric import ed25519

    key = ed25519.Ed25519PrivateKey.from_private_bytes(sg.b64url_decode(RFC8037_D))
    assert sg.public_jwk(key) == {"crv": "Ed25519", "kty": "OKP", "x": RFC8037_X}
    assert sg.key_id(key) == RFC8037_THUMBPRINT
    assert sg.sign_jws(b"Example of Ed25519 signing", key, header=b'{"alg":"EdDSA"}') == \
        RFC8037_JWS
    assert sg.verify_jws(RFC8037_JWS, sg.b64url_decode(RFC8037_X)) == \
        b"Example of Ed25519 signing"


@needs_signing
def test_a_grant_round_trips_and_every_tampering_is_invalid(tmp_path):
    key = sg.BrainKey.load_or_create(str(tmp_path / "k.pem"))
    claims = sg.claims_for_challenge(REQUEST, CHALLENGE, node="node", vid="d2-bench",
                                     bus="kline-diag")
    tok = key.sign(claims)
    assert len(tok) <= sg.MAX_TOKEN_BYTES
    h, p, s = tok.split(".")
    assert sg.b64url_decode(h) == f'{{"alg":"EdDSA","kid":"{key.kid}"}}'.encode()
    assert sg.b64url_decode(p) == sg.canonical_json(claims)
    trust = {key.kid: key.public_bytes()}
    assert sg.verify_grant(tok, trust) == claims
    other = sg.BrainKey.load_or_create(str(tmp_path / "other.pem"))
    forged_payload = sg.b64url(sg.canonical_json({**claims, "tier": 2}))
    for bad in (f"{h}.{forged_payload}.{s}",                      # payload changed
                other.sign(claims),                                # unknown key
                tok[:-2] + ("AA" if not tok.endswith("AA") else "BA")):  # signature
        with pytest.raises(sg.GrantInvalid):
            sg.verify_grant(bad, trust)
    # a header with an extra member, validly signed, is still refused
    jwk_hdr = json.dumps({"alg": "EdDSA", "kid": key.kid, "jwk": key.public_jwk()},
                         separators=(",", ":")).encode()
    with pytest.raises(sg.GrantInvalid):
        sg.verify_grant(sg.sign_jws(sg.canonical_json(claims), key._key, header=jwk_hdr), trust)
    with pytest.raises(ValueError):  # the cap
        sg.sign_grant({**claims, "req": "r" * 600}, key._key, key.kid)


@needs_signing
def test_the_brain_key_is_made_once_and_owner_readable(tmp_path):
    path = tmp_path / "state" / "brain-grant-ed25519.pem"
    k1 = sg.brain_key(str(path.parent))
    assert k1 is not None and path.exists()
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    k2 = sg.BrainKey.load_or_create(str(path))
    assert k1.kid == k2.kid and k1.public_bytes() == k2.public_bytes()
    assert "PRIVATE" not in repr(k1) and k1.kid in repr(k1)
    assert set(k1.public_jwk()) == {"crv", "kty", "x", "kid"}


@needs_signing
def test_the_reference_gate_verifier_checks_binding():
    from dataclasses import replace

    from openostler.can.gate import TxGate

    key = sg.BrainKey(bytes(range(32)))
    gate = TxGate()
    rh = sg.request_hash(REQUEST)
    g = gate.issue("obd_clear", 1, req=REQUEST["id"], rh=rh)
    claims = sg.grant_claims(node="node", vid="d2-bench", bus="kline-diag", action="obd_clear",
                             tier=1, origin="local", challenge=g.nonce, ttl_ms=10_000,
                             req=REQUEST["id"], boot=5, rh=rh)
    verify = sg.jws_grant_verifier({key.kid: key.public_bytes()}, node="node",
                                   vid="d2-bench", bus="kline-diag", boot=lambda: 5)
    assert verify(replace(g, token=key.sign(claims))) == "ok"
    assert verify(replace(g, token=key.sign({**claims, "bus": "can-hs"}))) == "invalid"
    assert verify(replace(g, token=key.sign({**claims, "boot": 6}))) == "expired"
    assert verify(replace(g, token=key.sign({**claims, "challenge": "AAAA"}))) == "used"
    assert verify(replace(g, token=key.sign({**claims, "rh": "AAAA"}))) == "mismatch"
    assert verify(replace(g, token=key.sign({**claims, "req": "other"}))) == "mismatch"
    assert verify(replace(g, token="")) == "invalid"
