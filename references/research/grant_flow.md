---
title: "Grant flow — the challenge exchange, queued actions and epochs for grants, leases and claims"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [specs/2026-10-06-module-bus-messages-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0040-power-states-and-wake.md, specs/2026-10-06-node-source-design.md]
summary: >
  Live research (2026-10-06) for the module-bus spec's open questions 1 and 2 and input to 13. Prior art: UDS SecurityAccess 0x27 and Authentication 0x29 (seed or challenge, proof of ownership, attempt limits; 0x29 unlocks a session rather than one action), AUTOSAR SecOC freshness counters, Matter timed invoke and message-counter windows, WebAuthn (challenges of at least 16 random bytes), Tesla's vehicle-command protocol (wake first, then sign with a vehicle-clock expiry of 5 s by default, epoch per boot, sliding counter window; nothing is signed for later delivery), OVMS v3 and Home Assistant (broker-authenticated commands, never retained, message expiry). Token formats compared for Ed25519 on the node: JWS (~470 bytes), PASETO v4.public (~460), COSE_Sign1/CWT (~220, needs CBOR), raw bytes (~160); Monocypher's optional Ed25519 verifies RFC 8032 signatures. Recommends keeping the approved JWS, adding a `challenge` outcome state on the existing `act/<id>` topic instead of a sub-topic, binding the token to the request (`rh`) and the node's `boot`, a strict header; queued actions hold no grant and get a fresh challenge at delivery, signed by the requester or the Brain; and, for item 13, claims as self-expiring MQTT 5 leases with a `boot` field, since fencing tokens cannot apply to a car bus.
---

# Grant flow: challenge exchange, queued actions, epochs

Research for the [module-bus message spec](../../specs/2026-10-06-module-bus-messages-design.md)
§17 items 1 and 2, with input to item 13. Facts were checked live on 2026-10-06 unless marked
**(U)** (unverified, or needs the bench). Concepts only: no specification text or code is
reused.

## 0. What is already fixed

- The **grant format is owner-approved** (spec §10; firmware `docs/specs/node-can.md` §6 and
  §11 answer 1): a node-issued 16-byte challenge, kept at most 30 s, 16 outstanding, and a
  JWS compact Ed25519 token `{v, node, vid, bus, action, tier, origin, challenge, ttl_ms,
  req}` with `ttl_ms` ≤ 10 000, checked on the node's monotonic clock. Minter keys enter
  only by pairing or adoption. What is open is the exchange, not the format.
- **Queued actions carry no authority** and are re-checked at execution; only Tier 0–1 is
  queued, default expiry 120 s, max 600 s (ADR-0040 §5 items 4–5; spec §9).
- **Car actions run on the node gate, never needing the Brain** (ADR-0040 §5.3), so a Tier 1
  car action is queued only while the node sleeps, until its check-in (§5.6): 30 min timer
  wakes with a 60 s window in the firmware's car profile.
- **The gate never hands over** (ADR-0037 §1); `term` orders the movable roles only.
- No Ed25519 code exists yet: the Python `TxGrant` fails closed on any token
  (`src/openostler/can/gate.py`); the firmware vendors no crypto library.

## 1. Prior art

### Challenge–response on vehicles

- **UDS SecurityAccess 0x27** (ISO 14229-1): the tester asks for a seed with an odd
  sub-function and answers with a key on the next even one; the server limits failed attempts
  and enforces a delay (NRC 0x35 invalid key, 0x36 attempts exceeded, 0x37 delay not
  expired). Seeds are often only 32 bits and the key algorithms proprietary [Wikipedia UDS;
  pyudskit docs].
- **UDS Authentication 0x29** (added in ISO 14229-1:2020): certificate exchange (APCE), with
  sub-functions to request a server challenge (0x05) and to verify proof of ownership of the
  certificate's key (0x03, 0x06, 0x07). Once authenticated, a session role is unlocked;
  critics note that nothing binds later requests to the authenticated party unless session
  keys are derived and used [udsoncan source; Embedded Computing Design, "New UDS
  Authentication"]. **Lesson:** bind the proof to one action, not to a session. The approved
  per-action grant already does.
- **AUTOSAR SecOC**: each secured PDU carries a truncated MAC and, in profiles 1 and 3, a
  truncated freshness value from a monotonic counter kept by a Freshness Manager; profile 2
  has no freshness at all. Truncation forces a counter resynchronisation scheme [AUTOSAR PRS
  SecOcProtocol R20-11; CINNAMON, arXiv 2111.12026]. **Lesson:** counters suit high-rate
  streams between ECUs that share keys; they need persistent state on both sides, which a
  one-shot challenge does not.
- **Tesla vehicle-command** (`teslamotors/vehicle-command` a4b43c1, 2026-09-25): the client
  fetches session info `(epoch, clock time, counter)`; the epoch is 16 random bytes made at
  verifier start; `expires_at` is in seconds on the *vehicle's* clock, default lifetime
  **5 s** (`internal/dispatcher/session.go`); counters rise within an epoch, with a 32-wide
  sliding window. A forged wall clock can shorten but never extend a command's life
  (`internal/authentication/verifier.go`). The client **wakes the car first** (Fleet API or
  BLE RKE wake) and signs after; nothing is signed for later delivery [protocol.md, source].

### Smart-home and web practice

- **Matter timed invoke**: for sensitive commands (door locks) the client first sends a
  Timed Request with a short window (examples use a few seconds), then the Invoke must
  arrive inside it, which defeats intercept-and-delay attacks. CASE sessions add 32-bit
  message counters with a 32-wide duplicate window [nRF Connect Matter interaction model;
  connectedhomeip `TimedHandler.h`, `PeerMessageCounter.h`]. Sleepy (LIT) devices are
  reached after they check in; commands are not signed ahead.
- **WebAuthn**: challenges must be generated by the relying party with enough entropy and
  should be at least 16 bytes; the human acts *after* the challenge, which is why ceremony
  timeouts run to minutes (its examples use 300 s) [W3C WebAuthn Level 3, security
  considerations on challenges]. Here the human confirms *before* asking for the challenge,
  so 10 s suffices.
- **Home Assistant MQTT**: command topics must not be retained (a retained "open" replays at
  reconnect); `message_expiry_interval` bounds how long queued or retained messages wait at
  the broker [home-assistant.io MQTT switch docs].
- **OVMS v3**: commands go to `<prefix>/client/<client>/command/<id>` and answers come back
  on `…/response/<id>`, authenticated only by the broker login; there is no per-command
  signature or expiry [openvehicles.com forum and docs]. Our requester-owned `act/<id>` with
  correlation data is the same shape, plus a grant.
- **Fencing tokens** (Kleppmann, 2016): a lease or lock is safe only if the *resource*
  rejects operations carrying an older, monotonically increasing token, because a paused
  holder cannot know its lease has lapsed [martin.kleppmann.com].

### Token formats for Ed25519 on the node

Sizes for the spec's payload plus `boot` and `rh` (§2), computed locally:

| Format | Size | Node parsing | Notes |
|---|---|---|---|
| **JWS compact, `EdDSA`** (RFC 7515, RFC 8037) | ~470 B | verify over the ASCII `header.payload`; base64url-decode the signature and payload; `ojson` | approved; `alg` and `kid` in a header that must be pinned |
| **PASETO v4.public** | ~460 B | base64url, PAE (length-prefixed concatenation), JSON | no algorithm choice in the token; `kid` goes in the footer; no IETF RFC (draft-paragon-paseto-rfc) |
| **COSE_Sign1 / CWT** (RFC 9052, RFC 8392) | ~220 B | CBOR decode; rebuild `Sig_structure` | smallest standard; needs a CBOR reader on the node and a COSE library on the Brain and phones |
| **Raw signed byte string** | ~160 B | fixed offsets | smallest; a bespoke format every client must re-implement and version |

- Ed25519 hashes the message with SHA-512; at a few hundred bytes the signature check
  dominates; the format changes parsing cost only. Software verify takes about **28 ms on
  an ESP32 at 240 MHz** and **132 ms on an ESP32-C3** (CycloneCRYPTO) [Oryx Embedded
  benchmarks]; Monocypher on the ESP32-S3 is **(U)**.
- **Monocypher 4.0.x** (CC0 or BSD-2-Clause, under 2 000 lines, no libc dependency): its
  core `crypto_eddsa_*` uses **BLAKE2b, not Ed25519**; RFC 8032 Ed25519 is the optional
  `monocypher-ed25519` part (`crypto_ed25519_check`) [monocypher.org manual].
  Vendor the optional file and test RFC 8032 vectors, or every token fails.
- **Randomness:** `esp_random()` is a true RNG on the ESP32-S3 only while Wi-Fi or BT is on,
  or after `bootloader_random_enable()`; otherwise it is pseudo-random [ESP-IDF random
  docs]: never draw a challenge before the radio is up.

## 2. Q1 — the challenge exchange

**Manager's recommendation.** The requester publishes `act/<id>` with `"need":"challenge"`;
the node answers on its `act/<id>/challenge` with `{nonce, t_us, expires_us}`; the token
signs `nonce‖action‖tier‖expires_us`, base64url.

**Recommendation: confirm the request half, change the reply topic and the token.**

1. **Reply on the existing outcome topic, as a new state.** `act/<id>/challenge` is one level
   deeper than `+/act/+`, which the node, NodeSource, the ACLs (§13) and the bridge
   question (§17 item 4) all use; it would need `act/#` everywhere. An outcome state
   `challenge` on `<node>/act/<id>` needs no topic, ACL or subscription change and keeps
   Correlation Data working. This is Matter's timed request and UDS 0x29's challenge
   request folded into the action's own exchange.
2. **Run the cheap gate steps first.** The node checks everything before the grant checks
   (node-can §5 steps 1–11, the driving state and origin included) and issues a
   challenge only if they pass, so a refused action wastes no challenge slot and the user
   hears the real reason at once (as UDS answers a seed only when conditions allow).
3. **Keep the approved JWS**, not a raw `nonce‖action‖tier‖expires_us` string: the format
   is owner-approved, standard on the Brain and phones, and the size and parse cost are
   small beside the 28–130 ms verify. Expiry stays `ttl_ms` relative to the node's own
   challenge time; an absolute `expires_us` adds nothing the node does not already hold.
4. **Bind the token to the request and the boot.** Today `params`, `user` and `role` are not
   signed, so a relaying Brain or a broker-side attacker could change the DTC set or the
   actuator values under a valid grant. Add `rh` and `boot` (below).
5. **Pin the header** so no `alg` or key confusion is possible (RFC 8725 practice), and
   rate-limit failures as UDS does.

**Proposed wording for spec §10** (replacing "Challenge first" and extending "Token"):

> - **Challenge exchange.** A requester that needs a grant publishes its `act/<id>` request
>   (§9) without `grant` and with `"need": "challenge"`. The executing node runs every gate
>   step before the grant checks; if one fails it answers `refused` with that reason and
>   issues nothing. Otherwise it answers on its outcome topic
>   `ostler/v1/<vid>/<node>/act/<id>` with `{id, state: "challenge", challenge, boot, t_us,
>   ttl_ms}`, QoS 1, Correlation Data `id`, Message Expiry 10 s: `challenge` is 16 bytes
>   from the hardware RNG with the radio on, as unpadded base64url (22 characters); `boot`
>   and `t_us` are the node's at issue; `ttl_ms` is the lifetime it will honour (≤ 10 000).
>   The node records the challenge with the request id, action, tier and `rh`, keeps at
>   most 16 outstanding (at most 4 per requester) and forgets each after 30 s.
> - The requester then republishes `act/<id>` with the same `id` and body and `grant` set.
>   A request whose `id` has no outstanding challenge is `grant_used`; one whose action,
>   tier or `rh` differs from the recorded ones is `grant_mismatch`. A Tier 1+ request with
>   neither `grant` nor `need` is `no_grant`. Over BLE or the node's AP the same JSON
>   travels as the reply.
> - **Token header** is exactly `{"alg":"EdDSA","kid":"<kid>"}`; any other member (`jwk`,
>   `jku`, `x5u`, `x5c`, `crit`, `b64`) or another `alg` is `grant_invalid`. The token is at
>   most 640 bytes. The signature is checked over the ASCII signing input (RFC 7515 §5.1)
>   before the payload is parsed.
> - **Token payload** adds `boot` (the challenge's) and `rh`: the unpadded base64url SHA-256
>   of the canonical JSON (the manifest `etag` rules, §7.1) of `{action, params, role,
>   target, user}` from the request. A `boot` other than the node's is `grant_expired`, checked
>   before the challenge lookup; a wrong `rh` is `grant_mismatch`.
> - Three `grant_invalid` refusals from one requester within 60 s make the node refuse
>   that requester's challenges for 60 s (`grant_locked`), as UDS NRC 0x36/0x37 do.

**UI order.** The phone or Brain shows the confirmation first, then asks for the challenge
and signs at once, so the human is never inside the 10 s window (the reverse of WebAuthn).

**Confidence:** high for the outcome-state topic and the request binding; medium for the
attempt limits (values to bench).

**Risks.** A Tier 1 action now costs two round trips (QoS 1 each) plus a 28–130 ms verify;
fine for Tier 1–3 but worth measuring over BLE. A requester that republishes before the
challenge arrives races itself (the node answers `grant_used`; clients must wait for the
`challenge` outcome). `rh` needs one canonical-JSON routine in C, Python and the phone app;
the manifest `etag` already needs it in C and Python.

## 3. Q2 — queued Tier 1 actions and grants

**Manager's recommendation.** A queued action holds no grant; at delivery the node issues a
fresh challenge and the Brain or phone signs it then; Tier 1 cannot be queued while the
signer is offline (it expires instead).

**Prior art says the same.** Tesla wakes the car, then fetches fresh session state and signs
with a 5 s life; Matter reaches a sleepy device after its check-in, then runs a timed
interaction; Home Assistant never retains commands and bounds their wait with message
expiry. None of them signs a command for later delivery. ADR-0040 §5.4 already says queued
actions carry no authority.

**Recommendation: confirm, with three refinements.**

- **Who signs at delivery.** The requester if it is online; otherwise the paired Brain, for
  a Tier 1 request it relayed, after re-checking the user's role, the category and
  `expires_at` at that moment. The Brain is already a minter; a phone-originated request
  queued through it gets a Brain signature and the audit names both. A phone that sent the
  request directly (BLE, AP) and left is not covered: the request expires.
- **Don't offer what cannot run.** The node's car profile checks in every 30 min, while the
  longest queue is 10 min: most queued car actions would expire unseen. The UI reads the
  node's `power.next_checkin` and offers to queue only when the check-in falls before the
  latest allowed `expires_at`; otherwise it says when the node next checks in.
- **A grant inside a queued request is dropped**, logged, and never verified later; its
  challenge cannot outlive 10 s anyway.

**Proposed wording for spec §9** (after "Rules carried"):

> - **Queued requests and grants.** A queued request (ADR-0040 §5) holds no grant; one
>   that carries a `grant` has it dropped and logged. At delivery the executing gate
>   re-checks the request and, if it needs a grant, answers `challenge` (§10). The
>   requester signs it if it is online; otherwise the paired Brain may sign it for a Tier 1
>   request it relayed, after re-checking the user's role and `expires_at`, with `origin`
>   the original request's. If no grant arrives within the challenge's `ttl_ms` the node
>   issues one more challenge at most every 30 s until `expires_at`, then drops the request
>   as `expired`. A client offers to queue a request for a `check_in` target only when the
>   target's `next_checkin` is before the latest allowed `expires_at`.

**Alternative rejected for now: pre-signed deferred grants.** A minter could sign
`{counter, not_after_utc}` ahead, with the node keeping a per-key counter in NVS (SecOC- and
Tesla-style). It needs a synced clock at delivery, an NVS write per grant and a counter
resynchronisation story, and it turns a 10 s authority into a 10 min one. Revisit only if
owners need Tier 1 car actions queued while every minter is away.

**Confidence:** high (it restates ADR-0040 §5 with the prior art behind it); medium for
the Brain-as-signer rule, which is the owner's call.

**Risks.** If the node holds a persistent MQTT session while asleep, QoS 1 requests can be
delivered after wake without passing through the parked-broker holder's queue; the node
must still apply `expires_at` (MQTT 5 expiry is decremented by the broker, [MQTT-3.3.2-6],
so it agrees). The Brain signing for an absent phone user widens the Brain's role; the U5
threat model should cover it.

## 4. Input to Q13 — epochs and fencing for grants, leases and claims

- **Grants need no separate epoch.** The node's `boot` plus its monotonic `t_us` already
  play Tesla's `(epoch, clock time)`; the single-use challenge replaces a counter, so the
  node keeps no per-key state across boots. Putting `boot` in the challenge and the token
  (§2) gives a precise refusal after a reboot and guards against a challenge repeated by
  a weak RNG at early boot.
- **Leases need no fencing.** A stale lease only keeps a device awake longer, the safe
  direction; the arbiter decides on its own clock and `until` is for display.
- **Claims cannot be fenced at the resource.** Fencing works only when the resource checks
  the token; a K-line or CAN bus checks nothing, and a device wired to it but cut off from
  the broker is not stopped by any MQTT message. The firmware's fail-silent rule is the
  only protection that holds there, so **keep it** (confirm the manager).
- **Make claims self-expiring leases** instead of relying only on an owner clear: publish
  every claim with an MQTT 5 Message Expiry (proposal: republish every 60 s, expiry
  180 s). When a retained message expires the broker discards it and the topic has no
  retained message (MQTT 5 §3.3.1.3, [MQTT-3.3.2-5]), so a claim from a removed or crashed
  device vanishes by itself within 3 min and the silenced gate resumes; the owner's clear
  action stays for an immediate fix. Add the claimant's `boot` to the claim payload so a
  consumer can tell a claim from a previous life. `term` stays the order for movable roles,
  where consumers, not a bus, apply it.
- **(U)** Retained-message expiry in the ESP-IDF Mosquitto port used for the parked broker
  must be confirmed on the bench; upstream Mosquitto 2 implements it.

**Proposed wording for spec §7.2** (as a §17 item 13 option): "Claims are published with an
MQTT 5 Message Expiry of 180 s and republished every 60 s, and carry the claimant's
`boot`; an expired claim is gone from the broker. A gate holder stays listen-only while any
other claim on its bus is present (the firmware's rule); the Network page lets the owner
clear a claim at once."

**Confidence:** medium (the MQTT semantics are certain; the timings and the port's support
are not).

## Conflicts with ADRs/specs

- `specs/2026-10-06-module-bus-messages-design.md` §9 → outcome states gain `challenge`;
  the queued-request rule above; §10 → exchange, header pin, `boot`, `rh`, attempt limit,
  `grant_locked`; §3 table unchanged (same topic); §15 → challenge per-requester cap and
  lock-out values; §7.2 and §17 item 13 → claim expiry and `boot` (additive, §18).
- `ostler-firmware` `docs/specs/node-can.md` §6 → challenge issued after steps 1–11 and
  reported as an `act` outcome; token payload `boot` and `rh`; vendor
  `monocypher-ed25519` (not core `crypto_eddsa_*`).
- `decisions/adr-0037-role-holders-and-handover.md` §3 → the claim payload gains `boot`
  and a message expiry (additive; the ADR lists the payload).
- `decisions/adr-0040-power-states-and-wake.md` §5 → no conflict; adds who signs at
  delivery and the check-in guard.
- `tests/vectors/can/gate.json` and `src/openostler/can/gate.py` (`TxGrant`) → new
  vectors: `rh` mismatch, extra header member, wrong `boot`, lock-out.
- `CONSTITUTION.md` (dependencies) → the Brain must *sign* Ed25519, which stdlib cannot;
  it needs an optional extra or an ADR (the named `[passkeys]` extra is not yet in
  `pyproject.toml`).

## Open points for the owner

1. May the Brain sign a delivery-time grant for a queued Tier 1 request a phone made, or
   must the requester itself sign (stricter; more expiries)?
2. Should a client refuse to queue a car action when the node's next check-in is past the
   10 min maximum, or should the node's check-in interval shorten while requests wait?
3. Adopt self-expiring claims (180 s) for item 13, or keep claims permanent and rely only
   on the owner's clear action?
4. Which Python Ed25519 library the Brain uses for minting (an optional extra or an ADR).

## Sources (all checked 2026-10-06)

- Tesla: https://github.com/teslamotors/vehicle-command (`pkg/protocol/protocol.md`, a4b43c1)
- Matter: https://nrfconnectdocs.nordicsemi.com/addons/ncs-matter/latest/matter/overview/int_model.html ;
  connectedhomeip `src/app/TimedHandler.h`, `src/transport/PeerMessageCounter.h`
- WebAuthn: https://www.w3.org/TR/webauthn-3/ ; MQTT 5: https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html
- Home Assistant: https://www.home-assistant.io/integrations/switch.mqtt/ ; OVMS: https://www.openvehicles.com/node/2869
- UDS: https://en.wikipedia.org/wiki/Unified_Diagnostic_Services ; https://udsoncan.readthedocs.io/en/latest/_modules/udsoncan/services/Authentication.html ;
  https://embeddedcomputing.com/application/automotive/new-uds-authentication-enhanced-security-familiar-challenges
- SecOC: https://www.autosar.org/fileadmin/standards/R20-11/FO/AUTOSAR_PRS_SecOcProtocol.pdf ; https://arxiv.org/pdf/2111.12026
- JOSE/COSE/PASETO: https://www.rfc-editor.org/rfc/rfc8037.html ; https://www.rfc-editor.org/rfc/rfc8725.html ;
  RFC 9052, RFC 8392 ; https://datatracker.ietf.org/doc/draft-paragon-paseto-rfc/
- Monocypher: https://monocypher.org/manual/ed25519 ; Oryx benchmarks: https://www.oryx-embedded.com/benchmark/espressif/crypto-esp32.html
- ESP-IDF RNG: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/system/random.html
- Fencing: https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
