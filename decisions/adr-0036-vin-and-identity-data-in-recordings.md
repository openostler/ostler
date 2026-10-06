---
title: "ADR-0036 — VIN and identity data in recordings: off by default, never leaves the device"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0032-one-node-optional-brain.md]
summary: >
  Owner answer of 2026-10-06. Recording the VIN and other identity replies (OBD Mode 09, ECU identification reads) in raw recordings becomes an install-level option for security decoding work, off by default. When off, identity replies are scrubbed at write time to a fixed placeholder and every other raw byte is kept. When on, identity data still never leaves the device: never uploaded, shared, contributed, put in fixtures or committed. The hard line changes from "the VIN is never logged or recorded" to "never recorded by default; never leaves the device". Amends ADR-0010's identity-read line and the matching CONSTITUTION and GOALS hard lines; ADR-0018 Q7 (garage keeps an HMAC fingerprint and masked VIN only) is unchanged.
---

# ADR-0036 — VIN and identity data in recordings

> **Amended by [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), 2026-10-06:** the Diagnostics node scrubs identity data in its raw tap too, before it leaves the node. See [Amendments (product family)](#amendments-2026-10-06-product-family).

- **Date:** 2026-10-06
- **Status:** accepted (owner answer, 2026-10-06). **Amends**
  [ADR-0010](adr-0010-replay-notes-audio-motion.md) ("Identity reads never store their
  values") and the VIN hard lines in CONSTITUTION and GOALS. Leaves
  [ADR-0018](adr-0018-ui-architecture-decisions.md) Q7 unchanged.

## Context

- ADR-0009 and ADR-0010 say the VIN and identity reads are never recorded. GOALS and the
  constitution carry the same hard line.
- [ADR-0032](adr-0032-one-node-optional-brain.md) keeps raw bytes alongside decoded values
  in recordings, so re-decoding is possible later. Identity replies are part of those bytes.
- Security decoding work (immobiliser, seed-key and ECU identification) sometimes needs the
  real identity replies in context. Scrubbing them always makes that work impossible on
  one's own car.
- The VIN and ECU serials identify a vehicle and through it a person. They must not reach
  anyone else.

## Decision drivers

- Privacy by default: an ordinary install never stores identity data.
- Owners doing security research on their own car can opt in, on their own device.
- Nothing identifying ever leaves the device, whatever the setting.
- Raw recordings stay byte-faithful for everything that is not identity data.

## Decision

**1. An option, off by default.** Recording the VIN and identity replies (OBD Mode 09
VIN and calibration IDs, ECU identification reads and similar) in raw recordings is an
**install-level option**, set in local install configuration. It is **off by default**. It
cannot be set remotely, through the cloud, through an MCP client or by a pack.

**2. When off: scrub at write.** Identity replies are replaced by a **fixed placeholder**
when the recording is written, before anything touches storage. Every other raw byte is
kept. Packs declare which services and identifiers are identity data; the platform applies
the scrub.

**3. When on: still never leaves the device.** Identity data is never uploaded, shared,
contributed, put in fixtures or committed. Exports, community contributions, shares, cloud
sync and support bundles scrub it with the same placeholder, whatever the setting.

**4. The hard line becomes:** the VIN and identity data are **never recorded by default, and
never leave the device**. This replaces "the VIN is never logged or recorded" in ADR-0010,
CONSTITUTION and GOALS (those files are amended by their owners).

**5. Unchanged:** the garage keeps an HMAC fingerprint and a masked VIN only (ADR-0018 Q7);
`<vid>` is never the VIN (ADR-0027 §5); command events are still logged without payloads
(ADR-0010). Raw car captures are still never committed.

## Confirmation

- A test that, with the default settings, a session recording that saw a Mode 09 VIN reply
  and an ECU identification reply holds only the placeholder in their place, and the other
  raw bytes unchanged.
- A test that the option is read only from local install configuration: setting it through
  the API, MQTT, the cloud bridge, an MCP client or a pack is refused.
- A test that, with the option on, every export, contribution, share and fixture path
  produces output with no VIN and no identity reply.
- The privacy capture in ADR-0028's Confirmation still shows no VIN on any uplink.

## Consequences

- The logbook writer gains a scrub step and packs gain an identity-data declaration.
- The ADR-0018 test that no full VIN reaches the garage, logs or fixtures holds by default;
  with the option on, it holds for the garage, fixtures and everything that leaves the device.
- CONSTITUTION and GOALS change their VIN wording; ADR-0010 carries an amendment banner.

## Alternatives considered

- **Never record identity data (the old rule).** Rejected: it blocks security decoding on the
  owner's own car and breaks raw-byte fidelity for no gain once the data stays local.
- **Record by default.** Rejected: privacy by default.
- **Hash identity replies instead of a placeholder.** Rejected: a VIN has little entropy and
  a hash can be reversed by search; a fixed placeholder leaks nothing.

## Amendments (2026-10-06, product family)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (accepted with the owner's answers of 2026-10-06). The decision text above is
unchanged; where this entry differs, it wins.

1. **The node scrubs the raw tap** (§2). The Diagnostics node frames K-line and ISO-TP
   messages before it emits its raw tap, so it applies the pack's identity declarations **on
   the node**: identity replies are replaced with the fixed placeholder and flagged
   `scrubbed` before they leave the node, unless the install-level option is on. With the
   option on, unscrubbed bytes go only to the paired hub over the in-car link, and every
   export still scrubs (§3). Bytes the node cannot frame are marked `unframed` and dropped
   from exports (ADR-0039 §3).
