---
title: "ADR-0023 — Passive CAN bitrate detection before the first request"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0020-can-links-listen-only-by-default.md, references/research/muki01/obd2_can_bus_library.md, references/research/muki01/README.md, references/research/canbus_headunit.md]
summary: >
  Amends ADR-0020 (does not supersede it): the Tier 0 diagnostic read exception applies only once the bus bitrate is confirmed. Detection is passive: listen-only at 500 kbit/s, then 250 kbit/s, accepting a rate after 20 clean frames with no error frame; only then one 01 00. On a silent bus, one one-shot probe per rate, Parked only, stopping at the first error frame. A pack-declared bitrate skips detection. Never guess-transmit at an unconfirmed rate. Covers 11-bit and 29-bit IDs (functional 7DF and 18DB33F1).
---

# ADR-0023 — Passive CAN bitrate detection before the first request

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06; proposal (ii) of the
  [muki01 synthesis §d](../references/research/muki01/README.md#d-adrs-needed)).
  **Amends** [ADR-0020](adr-0020-can-links-listen-only-by-default.md); does not supersede it.

## Context

- ADR-0020 allows Tier 0 diagnostic read requests in every driving state. It says nothing
  about a bus whose bitrate is unknown, which is the normal case for `generic_obd2` (U4).
- A frame sent at the wrong bitrate is noise to every node: they raise error frames, and a
  powertrain bus at speed takes the hit. The
  [muki01 CAN library](../references/research/muki01/obd2_can_bus_library.md) does exactly
  this: normal mode, transmit-probing `{11, 29} × {250, 500}`, 250k first.
- ISO 15765-4 legislated OBD uses 500 or 250 kbit/s, with 11-bit or 29-bit IDs.
- A listen-only controller never transmits, not even an error flag or an ACK, so listening
  at a wrong rate cannot disturb the bus.

## Decision drivers

- No frame on a vehicle bus at a rate we have not confirmed.
- A quick connect on a busy bus; a safe one on a silent (gatewayed) OBD port.
- One rule for SocketCAN, slcan/GVRET and our ESP32 TWAI node.

## Decision

**The ADR-0020 Tier 0 exception applies only once the bitrate is confirmed.** Until then
the link is listen-only, whatever the driving state.

**Passive detection** (every driving state):
1. Open listen-only at **500 kbit/s**, with error reporting on (SocketCAN
   `berr-reporting on`, `CAN_ERR_MASK`), for up to 2 s.
2. **Accept the rate after 20 clean frames**: 20 valid frames with no error frame and no
   growth in the RX error counter. Any error frame rejects that rate for this attempt.
3. Else the same at **250 kbit/s**.
4. Learn the ID width from the traffic (11-bit, 29-bit or both).

**Why 20.** At the wrong rate (a 2× ratio) almost every frame fails bit stuffing, form or
CRC-15, so even one valid frame by chance is unlikely and 20 in a row is negligible; the
count also outvotes a single glitch on a noisy tap. A powertrain bus at 500k carries
hundreds of frames a second, so 20 arrive in tens of milliseconds; a sparse body bus
(10–50 frames/s) still confirms within the 2 s window. Fewer would accept a spurious
decode; more would only slow a sparse bus.

**Then one request.** Once the rate is confirmed, send **one functional `01 00`**: on
`0x7DF` if 11-bit traffic was seen (replies `0x7E8`–`0x7EF`), on `0x18DB33F1` if only
29-bit (replies `0x18DAF1xx`). With no reply, the other width may be tried once as an
ordinary Tier 0 request. Flush RX before each request; collect replies per ECU.

**Silent bus** (no frames at either rate, e.g. a gateway OBD port): **Parked only**. One
probe per rate, 500k first, sent **one-shot** (no automatic retransmission) on `0x7DF`.
An ACK with no error frame confirms the rate. **The first error frame stops detection**:
the link returns to listen-only and reports "bitrate not confirmed"; the user may retry
(still Parked) or set the rate in Developer under service mode.

**A bitrate the pack declares skips detection**, as does a manual choice in service mode.
A rate remembered for the same vehicle only sets the listening order.

**Never guess-transmit at an unconfirmed rate.** This is the muki01 anti-pattern, and the
`CanLink` API makes it impossible: `send()` raises until the rate is confirmed or declared.
The Tier 0 diagnostic IDs in ADR-0020 now name both widths: `0x7DF`/`0x7E0`–`0x7E7` and
`0x18DB33F1`/`0x18DAxxF1`.

## Confirmation

- On `vcan`, detection sends zero frames before it locks a rate.
- Fakes: 20 clean frames at 500k lock 500k; an error frame at 500k moves to 250k;
  a 29-bit-only bus gets `0x18DB33F1`.
- A silent-bus probe is refused unless Parked, is one-shot, and stops at the first error
  frame; a pack-declared rate skips detection.

## Consequences

- The "CanLink, passive detect and ISO-TP" spec (U4) carries the detail; ADR-0020's text
  stands as amended here.
- `CanLink` gains a `rate_confirmed` state and a one-shot send.

## Alternatives considered

- **Probe by transmitting, as ISO 15765-4 tools often do.** Rejected: unsafe at speed.
- **Accept after one frame.** Rejected: too easy to accept a wrong rate on noise.
