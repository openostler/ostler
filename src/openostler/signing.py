# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Transmit grants: the Brain's Ed25519 JWS (module-bus spec v1.3 §10; ADR-0041).

A grant is a JWS compact token (RFC 7515) signed with Ed25519 (``alg: EdDSA``, RFC 8037),
at most :data:`MAX_TOKEN_BYTES` bytes. Its protected header is **exactly**
``{"alg":"EdDSA","kid":"<kid>"}``; any other member, or another ``alg``, is
``grant_invalid``. Its payload is ``{v: 1, node, vid, bus, action, tier, origin, challenge,
ttl_ms, req, boot, rh}``, where ``rh`` is the unpadded base64url SHA-256 of the canonical
JSON (the manifest ``etag`` rules: keys sorted at every level, no whitespace, UTF-8) of
``{action, params, role, target, user}`` from the request, so a relay cannot change the
parameters under a valid grant.

Two halves:

- **Stdlib** (always importable): :func:`canonical_json`, :func:`request_hash`,
  :func:`grant_claims` (checks the claims), :func:`split_token` and :func:`check_header`
  (the pinned header), the base64url helpers.
- **Signing and verification** need the optional extra ``openostler[signing]`` (the
  ``cryptography`` package, ADR-0041), imported lazily, only when a key is made, a grant
  is signed or verified. Without it :func:`sign_grant` raises :class:`SigningUnavailable`
  ("Signing not installed on the Brain"): the Brain mints nothing and a grant must come
  from a paired phone; nothing fails open. :func:`verify_grant` without it raises too, and
  :func:`jws_grant_verifier` refuses every token (fail closed).

The Brain signs only in answer to a node's ``challenge`` outcome, after the user's
confirmation (or, for a relayed queued Tier 1 request, after re-checking the user's role,
the category and ``expires_at``); this module never pre-signs and sends nothing (the
requests are NodeSource P4). Its private key is made on the Brain on first use, kept
owner-readable only and never exported (:class:`BrainKey`); its public key reaches a node's
trust store only by pairing or adoption.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Callable, Mapping, Optional

ALG = "EdDSA"
GRANT_VERSION = 1
MAX_TOKEN_BYTES = 640          # spec §10, owner answer 1
MAX_TTL_MS = 10_000            # spec §10, §15
TIERS = (0, 1, 2, 3)           # Tier 4 never verifies (spec §10)
ORIGINS = ("local", "remote")
RH_FIELDS = ("action", "params", "role", "target", "user")
CLAIMS = ("v", "node", "vid", "bus", "action", "tier", "origin", "challenge", "ttl_ms",
          "req", "boot", "rh")
NOT_INSTALLED = ("Signing not installed on the Brain (install openostler[signing]); "
                 "a grant must come from a paired phone")


class SigningUnavailable(RuntimeError):
    """The optional extra ``openostler[signing]`` is not installed (ADR-0041 §6)."""

    def __init__(self, message: str = NOT_INSTALLED) -> None:
        super().__init__(message)


class GrantInvalid(ValueError):
    """A token that fails the header, the signature or the key (``grant_invalid``)."""


# ---------------------------------------------------------------- stdlib half -------- #
def b64url(data: bytes) -> str:
    """Unpadded base64url (RFC 7515 §2)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    """Unpadded base64url → bytes; raises ValueError on padding or a foreign character."""
    if not isinstance(text, str) or "=" in text or any(
            c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            for c in text):
        raise ValueError("not unpadded base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def canonical_json(obj) -> bytes:
    """The canonical JSON of the manifest ``etag`` rules (module-bus spec §7.1): keys sorted
    at every level, no whitespace, UTF-8 (non-ASCII kept as is)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def request_hash(request: Mapping) -> str:
    """``rh``: unpadded base64url SHA-256 of the canonical JSON of ``{action, params, role,
    target, user}`` from an ``act`` request (spec §10). A missing field hashes as null;
    ``params`` defaults to ``{}``."""
    body = {k: request.get(k) for k in RH_FIELDS}
    if body["params"] is None:
        body["params"] = {}
    return b64url(hashlib.sha256(canonical_json(body)).digest())


def grant_claims(*, node: str, vid: str, bus: str, action: str, tier: int, origin: str,
                 challenge: str, ttl_ms: int, req: str, boot: int, rh: str) -> dict:
    """The grant payload (spec §10), checked: strings non-empty, ``tier`` 0–3, ``origin``
    local or remote, ``ttl_ms`` 1–10 000, ``boot`` ≥ 0, ``challenge`` and ``rh`` base64url.
    Raises ValueError."""
    claims = {"v": GRANT_VERSION, "node": node, "vid": vid, "bus": bus, "action": action,
              "tier": tier, "origin": origin, "challenge": challenge, "ttl_ms": ttl_ms,
              "req": req, "boot": boot, "rh": rh}
    check_claims(claims)
    return claims


def check_claims(claims: Mapping) -> None:
    """Raise ValueError unless ``claims`` is a well-formed v1 grant payload."""
    if set(claims) != set(CLAIMS):
        raise ValueError(f"grant claims must be exactly {CLAIMS}")
    if claims["v"] != GRANT_VERSION:
        raise ValueError("grant payload v must be 1")
    for k in ("node", "vid", "bus", "action", "req", "challenge", "rh"):
        if not isinstance(claims[k], str) or not claims[k]:
            raise ValueError(f"grant claim {k} must be a non-empty string")
    for k in ("challenge", "rh"):
        b64url_decode(claims[k])
    if not _is_int(claims["tier"]) or claims["tier"] not in TIERS:
        raise ValueError("grant tier must be 0-3 (Tier 4 never verifies)")
    if claims["origin"] not in ORIGINS:
        raise ValueError("grant origin must be local or remote")
    if not _is_int(claims["ttl_ms"]) or not 0 < claims["ttl_ms"] <= MAX_TTL_MS:
        raise ValueError(f"grant ttl_ms must be 1-{MAX_TTL_MS}")
    if not _is_int(claims["boot"]) or claims["boot"] < 0:
        raise ValueError("grant boot must be a non-negative integer")


def claims_for_challenge(request: Mapping, challenge: Mapping, *, node: str, vid: str,
                         bus: str, ttl_ms: "int | None" = None) -> dict:
    """The claims answering a node's ``challenge`` outcome (spec §10) for an ``act``
    request: ``req`` is the request id, ``boot`` and ``challenge`` the outcome's, ``ttl_ms``
    at most the outcome's, ``rh`` the request's hash."""
    if challenge.get("state") != "challenge" or challenge.get("id") != request.get("id"):
        raise ValueError("not a challenge outcome for this request")
    offered = int(challenge.get("ttl_ms") or MAX_TTL_MS)
    return grant_claims(node=node, vid=vid, bus=bus, action=request["action"],
                        tier=int(request["tier"]), origin=request.get("origin") or "local",
                        challenge=challenge["challenge"],
                        ttl_ms=min(offered, ttl_ms or offered, MAX_TTL_MS),
                        req=request["id"], boot=int(challenge["boot"]),
                        rh=request_hash(request))


def header_bytes(kid: str) -> bytes:
    """The pinned protected header ``{"alg":"EdDSA","kid":"<kid>"}``, exactly."""
    if not isinstance(kid, str) or not kid:
        raise ValueError("kid must be a non-empty string")
    return json.dumps({"alg": ALG, "kid": kid}, separators=(",", ":")).encode("utf-8")


def split_token(token: str) -> "tuple[str, str, str]":
    """``header.payload.signature`` (the base64url parts); raises GrantInvalid on the
    shape or the size."""
    if not isinstance(token, str) or len(token.encode("ascii", "replace")) > MAX_TOKEN_BYTES:
        raise GrantInvalid(f"token missing or longer than {MAX_TOKEN_BYTES} bytes")
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise GrantInvalid("not a JWS compact serialisation")
    return parts[0], parts[1], parts[2]


def check_header(header_b64: str) -> str:
    """The ``kid`` of a protected header that is exactly ``{"alg":"EdDSA","kid":…}``
    (any other member such as ``jwk``, ``jku``, ``x5u``, ``x5c``, ``crit`` or ``b64``, or
    another ``alg``, is ``grant_invalid``)."""
    try:
        hdr = json.loads(b64url_decode(header_b64).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise GrantInvalid("unreadable header") from None
    if not isinstance(hdr, dict) or set(hdr) != {"alg", "kid"} or hdr["alg"] != ALG:
        raise GrantInvalid("the header must be exactly {alg: EdDSA, kid}")
    if not isinstance(hdr["kid"], str) or not hdr["kid"]:
        raise GrantInvalid("the header's kid must be a non-empty string")
    return hdr["kid"]


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


# --------------------------------------------------------- the optional extra -------- #
def signing_available() -> bool:
    """True when ``cryptography`` (the ``[signing]`` extra) can be imported."""
    try:
        _ed25519()
    except SigningUnavailable:
        return False
    return True


def _ed25519():
    """``cryptography``'s Ed25519 module, imported lazily (ADR-0041 §2)."""
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError:
        raise SigningUnavailable() from None
    return ed25519


def _private_key(key):
    ed = _ed25519()
    if isinstance(key, ed.Ed25519PrivateKey):
        return key
    if isinstance(key, (bytes, bytearray)) and len(key) == 32:
        return ed.Ed25519PrivateKey.from_private_bytes(bytes(key))
    raise TypeError("an Ed25519 private key (or its 32 raw bytes) is needed")


def _public_key(key):
    ed = _ed25519()
    if isinstance(key, ed.Ed25519PublicKey):
        return key
    if isinstance(key, ed.Ed25519PrivateKey):
        return key.public_key()
    if isinstance(key, (bytes, bytearray)) and len(key) == 32:
        return ed.Ed25519PublicKey.from_public_bytes(bytes(key))
    raise TypeError("an Ed25519 public key (or its 32 raw bytes) is needed")


def public_bytes(key) -> bytes:
    """The 32 raw bytes of an Ed25519 public key (from a public or private key object;
    32 raw bytes are read as a public key)."""
    pub = _public_key(key)  # raises SigningUnavailable without the extra
    from cryptography.hazmat.primitives import serialization

    return pub.public_bytes(serialization.Encoding.Raw,
                                         serialization.PublicFormat.Raw)


def public_jwk(key) -> dict:
    """The public key as an RFC 8037 OKP JWK ``{kty, crv, x}`` (a key object, or a public
    key's 32 raw bytes)."""
    return {"crv": "Ed25519", "kty": "OKP", "x": b64url(public_bytes(key))}


def key_id(key) -> str:
    """The key's ``kid``: its RFC 7638 JWK thumbprint (SHA-256, base64url) over the
    required members ``crv``, ``kty``, ``x`` in that order."""
    return b64url(hashlib.sha256(canonical_json(public_jwk(key))).digest())


def sign_jws(payload: bytes, private_key, kid: "str | None" = None, *,
             header: "bytes | None" = None) -> str:
    """A compact JWS over ``payload`` (RFC 7515 §7.1) signed with Ed25519. The header is
    the pinned one for ``kid`` unless raw ``header`` bytes are given (test vectors only)."""
    key = _private_key(private_key)
    hdr = header if header is not None else header_bytes(kid or "")
    signing_input = f"{b64url(hdr)}.{b64url(payload)}".encode("ascii")
    return f"{signing_input.decode('ascii')}.{b64url(key.sign(signing_input))}"


def sign_grant(claims: Mapping, private_key, kid: str) -> str:
    """The grant token: the checked ``claims`` (:func:`grant_claims`) as canonical JSON,
    signed with the pinned header. Raises :class:`SigningUnavailable` without the extra,
    ValueError on bad claims or a token over :data:`MAX_TOKEN_BYTES`."""
    check_claims(claims)
    _ed25519()  # say "not installed" before anything else
    token = sign_jws(canonical_json(dict(claims)), private_key, kid)
    if len(token) > MAX_TOKEN_BYTES:
        raise ValueError(f"the grant token is {len(token)} bytes (max {MAX_TOKEN_BYTES})")
    return token


def verify_jws(token: str, public_key) -> bytes:
    """The payload bytes of a compact EdDSA JWS whose signature ``public_key`` verifies
    (over the ASCII signing input, before anything is parsed); raises GrantInvalid. The
    header is not checked here (see :func:`verify_grant`)."""
    from cryptography.exceptions import InvalidSignature

    h, p, sig = split_token(token)
    try:
        raw_sig = b64url_decode(sig)
        _public_key(public_key).verify(raw_sig, f"{h}.{p}".encode("ascii"))
        return b64url_decode(p)
    except (InvalidSignature, ValueError) as exc:
        raise GrantInvalid("bad signature") from exc


def verify_grant(token: str, trust_store: "Mapping[str, object]") -> dict:
    """Check a grant token as the node does first (spec §10): the size, the pinned header,
    a ``kid`` in ``trust_store`` (``{kid: public key or its 32 raw bytes}``) and the
    signature over the signing input, *then* parse the payload and check its shape.
    Returns the claims; raises GrantInvalid (``grant_invalid``) or
    :class:`SigningUnavailable` without the extra. The caller checks the claims against
    its own node, vehicle, bus, boot, challenge, clock and request."""
    _ed25519()
    h, _p, _s = split_token(token)
    kid = check_header(h)
    if kid not in trust_store:
        raise GrantInvalid("unknown key")
    payload = verify_jws(token, trust_store[kid])
    try:
        claims = json.loads(payload.decode("utf-8"))
        if not isinstance(claims, dict):
            raise ValueError("not an object")
        check_claims(claims)
    except (ValueError, UnicodeDecodeError) as exc:
        raise GrantInvalid(f"bad payload: {exc}") from None
    return claims


def jws_grant_verifier(trust_store: "Mapping[str, object]", *, node: str, vid: str,
                       bus: str, boot: "int | Callable[[], int]",
                       request_hash_for: "Callable[[object], str | None] | None" = None,
                       ) -> "Callable[[object], str]":
    """A ``grant_verifier`` for the Python reference gate (``openostler.can.gate.TxGate``)
    that checks real tokens. For a ``TxGrant`` it answers, in the spec §10 order:

    - ``invalid``: no token, a bad size, header, signature or unknown ``kid``, a bad
      payload, or a token for another ``node``, ``vid`` or ``bus``;
    - ``expired``: the token's ``boot`` is not this gate's (before the challenge lookup);
    - ``used``: the token answers another challenge than this grant's (its ``nonce``);
    - ``mismatch``: its ``action``, ``tier``, ``origin``, ``req`` or ``rh`` differ from the
      grant's (``rh`` from ``request_hash_for(grant)`` when given, else the grant's ``rh``);
    - ``ok`` otherwise.

    Without the extra every token is ``invalid`` (fail closed)."""
    from .can.gate import (GRANT_EXPIRED, GRANT_INVALID, GRANT_MISMATCH, GRANT_OK,
                           GRANT_USED)

    def current_boot() -> int:
        return boot() if callable(boot) else boot

    def verify(grant) -> str:
        token = getattr(grant, "token", "")
        if not token:
            return GRANT_INVALID
        try:
            c = verify_grant(token, trust_store)
        except (GrantInvalid, SigningUnavailable):
            return GRANT_INVALID
        if (c["node"], c["vid"], c["bus"]) != (node, vid, bus):
            return GRANT_INVALID
        if c["boot"] != current_boot():
            return GRANT_EXPIRED
        if c["challenge"] != grant.nonce:
            return GRANT_USED
        want_rh = request_hash_for(grant) if request_hash_for else getattr(grant, "rh", "")
        if (c["action"], c["tier"], c["origin"]) != (grant.action, grant.tier, grant.origin) \
                or (getattr(grant, "req", "") and c["req"] != grant.req) \
                or (want_rh and c["rh"] != want_rh):
            return GRANT_MISMATCH
        return GRANT_OK

    return verify


class BrainKey:
    """The Brain's Ed25519 signing key (ADR-0041 §5): made on first use, stored as an
    unencrypted PKCS#8 PEM readable by the owner only (mode 0600), never exported, never
    logged. ``kid`` is its RFC 7638 thumbprint; :meth:`public_jwk` is what pairing hands
    to a node's trust store."""

    def __init__(self, private_key) -> None:
        self._key = _private_key(private_key)

    @classmethod
    def load_or_create(cls, path: str) -> "BrainKey":
        ed = _ed25519()  # raises SigningUnavailable without the extra
        from cryptography.hazmat.primitives import serialization

        try:
            with open(path, "rb") as f:
                key = serialization.load_pem_private_key(f.read(), password=None)
            if not isinstance(key, ed.Ed25519PrivateKey):
                raise ValueError(f"{path}: not an Ed25519 key")
            return cls(key)
        except FileNotFoundError:
            pass
        key = ed.Ed25519PrivateKey.generate()
        pem = key.private_bytes(serialization.Encoding.PEM,
                                serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(pem)
        return cls(key)

    @property
    def kid(self) -> str:
        return key_id(self._key)

    def public_jwk(self) -> dict:
        return {**public_jwk(self._key), "kid": self.kid}

    def public_bytes(self) -> bytes:
        return public_bytes(self._key)

    def sign(self, claims: Mapping) -> str:
        """A grant token for ``claims`` under this key's ``kid``."""
        return sign_grant(claims, self._key, self.kid)

    def __repr__(self) -> str:  # never the private key
        return f"BrainKey(kid={self.kid!r})"


def brain_key(state_dir: str, name: str = "brain-grant-ed25519.pem") -> "Optional[BrainKey]":
    """The Brain's key under ``state_dir``, made on first use; None without the extra."""
    try:
        return BrainKey.load_or_create(os.path.join(state_dir, name))
    except SigningUnavailable:
        return None


__all__ = ["ALG", "BrainKey", "CLAIMS", "GrantInvalid", "MAX_TOKEN_BYTES", "MAX_TTL_MS",
           "NOT_INSTALLED", "RH_FIELDS", "SigningUnavailable", "b64url", "b64url_decode",
           "brain_key", "canonical_json", "check_claims", "check_header",
           "claims_for_challenge", "grant_claims", "header_bytes", "jws_grant_verifier",
           "key_id", "public_bytes", "public_jwk", "request_hash", "sign_grant", "sign_jws",
           "signing_available", "split_token", "verify_grant", "verify_jws"]
