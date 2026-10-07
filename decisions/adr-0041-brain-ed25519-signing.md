---
title: "ADR-0041 — The Brain signs transmit grants with Ed25519 through the optional `openostler[signing]` extra"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [CONSTITUTION.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0040-power-states-and-wake.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-accounts-sharing-design.md, references/research/grant_flow.md]
summary: >
  Accepted by the owner on 2026-10-06. The Brain is a grant minter (module-bus spec §10) and, since the owner's answers of the same day, may sign a queued Tier 1 request it relayed at delivery time, so its Python code must make Ed25519 signatures. The standard library cannot (hashlib and ssl have no Ed25519 signing), so the Brain signs with the `cryptography` package, installed only through a new optional extra `openostler[signing]`. Core stays stdlib plus pyserial. The extra shares one pinned `cryptography` requirement with `[passkeys]`, which the CONSTITUTION already names and the accounts spec already ties to `cryptography`; one library serves both, and the CONSTITUTION's list of extras gains `[signing]`. One helper builds the canonical JSON, `rh`, the pinned header and the compact JWS, imported lazily. Without the extra the Brain mints nothing and says so; grants then come from a paired phone. The private key is made on the Brain and never leaves it; its public key enters a node's trust store only by pairing or adoption. Confirmation by RFC 8032 and RFC 8037 vectors, a round trip against the node's verifier vectors, and a test that core imports nothing from the extra.
---

# ADR-0041 — The Brain signs transmit grants with Ed25519

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06, with the
  [module-bus spec's owner answers](../specs/2026-10-06-module-bus-messages-design.md#17-owner-answers-2026-10-06)).
  Applies the dependency rule of the CONSTITUTION and
  [ADR-0035](adr-0035-languages-by-tier.md) ("a new runtime dependency still needs an
  ADR"). Evidence: [grant flow research](../references/research/grant_flow.md).

## Context

- The owner-approved transmit grant (module-bus spec §10) is a JWS compact token signed
  with **Ed25519** (`alg: EdDSA`, RFC 8037) by a paired minter: the **Brain** or a paired
  **phone**. Since the owner's answers of 2026-10-06 the Brain also signs **at delivery
  time** for a queued Tier 1 request it relayed when the requester is offline (spec §9,
  owner answer 2).
- **Python's standard library cannot sign Ed25519.** `hashlib` has SHA-2 but no
  signatures, and `ssl` signs only inside a TLS handshake. The platform's `TxGrant` path
  therefore fails closed on any token today (`src/openostler/can/gate.py`).
- The CONSTITUTION keeps **core Python stdlib plus pyserial** and lists the optional extras
  `[passkeys]`, `[mcp]` and `[can]`; a new runtime dependency needs an ADR. The accounts
  spec (§2.2, owner Q1) already ties `[passkeys]` to the **`cryptography`** package
  (packaged by Debian as `python3-cryptography`), but `pyproject.toml` defines none of
  `[passkeys]` or `[mcp]` yet; only `[can]` and `dev` exist.
- Hand-written Ed25519 is out of the question for a key that authorises car-bus writes.

## Decision drivers

- Core stays stdlib plus pyserial; a Pi with no signing need installs nothing new.
- One cryptographic library for the platform, not one per feature.
- A library maintained, audited and packaged by Debian, with a permissive licence that
  fits AGPL-3.0-or-later and the commercial licence (ADR-0012, ADR-0025).
- The node's checks decide; the Brain's signature only proves who asked (ADR-0037 §1).

## Decision

1. **`cryptography` signs on the Brain**, through its Ed25519 API
   (`Ed25519PrivateKey.sign`). Licence: Apache-2.0 or BSD-3-Clause. No other signing
   library (PyNaCl, pure-Python Ed25519) is added.
2. **A new optional extra, `openostler[signing]`**, carries it. Core never imports it at
   module load: the signing helper imports `cryptography` lazily, as `openostler.can.pycan`
   does with python-can.
3. **Reconciled with `[passkeys]`.** Both extras name the **same** `cryptography`
   requirement with one floor (set when `pyproject.toml` gains them, no lower than the
   version Debian stable packages, so `python3-cryptography` satisfies it on a Pi).
   Installing either brings the one library; nothing else differs. The CONSTITUTION's list
   of optional extras becomes `[passkeys]`, `[signing]`, `[mcp]` and `[can]`. A Brain
   image installs `[signing]` by default; a lab laptop need not.
4. **One helper** builds the grant exactly as spec §10 says: the canonical JSON (the
   manifest `etag` rules) and `rh`, the header exactly `{"alg":"EdDSA","kid":"<kid>"}`,
   the payload `{v, node, vid, bus, action, tier, origin, challenge, ttl_ms, req, boot,
   rh}`, the compact serialisation, and the 640-byte cap. It signs only in answer to a
   node's `challenge` outcome, after the user's confirmation (or, for a relayed queued
   Tier 1 request, after re-checking the user's role, the category and `expires_at`). It
   never pre-signs.
5. **Keys.** The Brain generates its Ed25519 key on first use; the private key stays on
   the Brain (owner-readable only, never exported, never in a log, backup or fixture).
   Its public key enters a node's trust store only by pairing or adoption (spec §10).
6. **Without the extra** the Brain mints nothing: a request that needs a Brain grant is
   refused with a clear reason ("Signing not installed on the Brain"), and grants come
   from a paired phone. Nothing fails open.
7. **Verification** on the Brain (the Python reference gate, `TxGrant`) may use the same
   extra; without it the reference gate keeps failing closed, as today. The node verifies
   in C (node-can §6), independent of this ADR.

## Confirmation

- Pytest (skipped without the extra, required in CI): RFC 8032 Ed25519 test vectors and
  RFC 8037's EdDSA JWS example round-trip through the helper; the helper's tokens pass the
  shared grant vectors (`tests/vectors/can/gate.json`, extended for `rh`, the pinned
  header and `boot`) that the node's verifier also runs.
- A test imports `openostler` and its server with `cryptography` absent and checks that
  nothing fails to load and that grant minting reports "not installed".
- The supply-chain CI (SBOM, licence scan) lists `cryptography` only under the extras.

## Consequences

- `pyproject.toml` gains `signing` and `passkeys` extras with the one shared requirement
  (a platform build item, not done by this ADR).
- The CONSTITUTION's extras list gains `[signing]`.
- The Brain's role widens: it may sign for an absent phone user's relayed Tier 1 request;
  the U5 threat model covers that (grant flow research §3).
- `THIRD_PARTY_LICENSES.md` gains a `cryptography` entry when the extra lands.

## Alternatives considered

- **PyNaCl (libsodium).** Rejected: a second crypto library beside the one passkeys need.
- **A pure-Python Ed25519.** Rejected: slow, not constant-time, thinly maintained.
- **Sign on the node, or phones only.** Rejected: a relayed queued Tier 1 request would
  expire whenever the phone that made it has left (owner answer 2 lets the Brain sign).
- **A core dependency.** Rejected: every install would carry it, against the stdlib rule.

## Relation to other ADRs

- **ADR-0035:** applies its "optional extras" rule; the language split is unchanged.
- **ADR-0029 / accounts spec:** `[passkeys]` keeps its meaning; it now shares its one
  `cryptography` requirement with `[signing]`.
- **ADR-0033, ADR-0040:** unchanged; the Brain's signing at delivery follows the module-bus
  spec §9 and ADR-0040 §5 (queued requests carry no authority until signed at delivery).
