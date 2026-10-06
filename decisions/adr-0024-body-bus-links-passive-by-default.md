---
title: "ADR-0024 — Body-bus links (BMW I/K-Bus): passive by default"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [references/research/muki01/bmw_ibus_kbus.md, references/research/muki01/README.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  BMW I/K-Bus and similar single-wire body buses use a byte Transport plus a framer (9600 8E1, XOR, resync), not a CanLink, and are passive by default. Transmit needs a pack allowlist on (src, dst, cmd, data mask, rate), Parked and the server gate; nothing transmits from a remote path. No spoofing of modules present in the car; 0x3F only for allowlisted jobs; CD-changer emulation only when no changer answers. A rate-limited exception for IKE odometer and time requests. TX hardware senses idle, compares its echo and retries a bounded number of times. Standing automations are pre-authorised once in service mode. Alarm triggers stay read-only; lock and unlock wait on the U5 threat model. Bus decodes live in packs (bmw_e first).
---

# ADR-0024 — Body-bus links (BMW I/K-Bus): passive by default

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06; proposal (iii) of the
  [muki01 synthesis §d](../references/research/muki01/README.md#d-adrs-needed))

## Context

- The [BMW I/K-Bus audit](../references/research/muki01/bmw_ibus_kbus.md) found a
  single-wire, multi-master body bus (9600 baud 8E1, `SRC LEN DST DATA CHK`, XOR) with no
  arbitration and no ACK. Every frame names its source, so any node can pose as any module.
- The audited firmware sends any table frame over an unauthenticated `/api/cmd` with no
  driving-state check, moves lights and windows on key-fob events, and transmits without
  reading back its echo or retrying.
- ADR-0020's principle covers every vehicle bus, but its allowlist (ID, DLC, rate) and its
  Tier 0 exception are CAN-specific.

## Decision drivers

- No frame on a body bus unless a pack allows it, the car is Parked and the gate agrees.
- Never impersonate a module the car relies on.
- Vehicle data in packs; the platform stays generic.

## Decision

**Link shape.** A body bus is a byte **`Transport`** plus a **framer** (9600 8E1, XOR
checksum, 1-byte resync after a bad checksum, LEN 3–36, TX at most 32 bytes), **not a
`CanLink`**. The framer starts in the `bmw_e` pack and moves to the platform when a second
body-bus pack needs it (rule of two). **Decoded vehicle data** (module addresses, message
meanings, I/K-Bus commands) **lives in packs only**; `bmw_e` (read-only) is the first.
The link is **passive by default**; the reference hardware is an RX-only opto tap.

**Transmit needs all of:**
1. a **pack allowlist** entry keyed on `(src, dst, cmd, data mask, rate)`;
2. **Parked**;
3. the **server gate** with the action's tier (ADR-0018).

**Nothing transmits from a remote path.**

**No spoofing.** Never transmit with the source address of a module present in the car:
GM `00`, EWS `44`, IKE `80`, steering wheel (MFL) `50`, radio `68`. The diagnostic
address **`0x3F`** is used only for allowlisted IO jobs. **CD-changer (`0x18`) emulation**
runs only when no real changer answers the radio's polls, checked at each bus wake.

**Read-request exception** (like ADR-0020's Tier 0): the IKE **odometer (`16`)** and
**time (`41`)** requests may go out in every driving state, from a source no module in the
car uses, one in flight, at most one per command every 10 s, with backoff when IKE does
not answer. The audit's time request uses the radio's `68`; it is not copied as is.

**Transmit hardware** must sense bus idle (SEN/STA, ≥ 1.5 ms) before each frame,
**compare its echo** (read back its own frame), and **retry a bounded number of times**
(at most 3, with backoff), then give up and log. Opto or LIN parts without idle sensing
are RX-only.

**Standing automations** (welcome lights, goodbye, follow-me-home) fit neither the
`comfort` class (they write to a vehicle bus) nor per-action confirmation (no one is at
the screen). Each is a fixed sequence of allowlisted frames, **pre-authorised once in
service mode**, run **only when Parked**, **rate-limited**, and **logged frame by frame**.
A pack update that changes the sequence voids the authorisation; a remote path can never
trigger one.

**Alarm.** Triggers from body-bus events (door, boot or bonnet open, unlock without our
disarm, key in, ignition, bus wake) are **read-only**; the alarm stays **notify-only**.

**Lock and unlock** (GM jobs) stay listed and disabled until the **U5 threat model**.
Window and sunroof jobs also need an occupant-present confirm (pinch risk).

## Confirmation

- `FakeIbus` tests: resync after a bad checksum; LEN outside 3–36 dropped; TX over 32
  bytes refused; a collision is detected by echo compare and retried at most 3 times.
- Server tests: a body-bus frame is refused while Moving, from a remote path, off the
  allowlist, or with a present module's source address; CDC emulation is refused while a
  changer answers; IKE requests respect the rate limit.
- An automation is refused when not pre-authorised or not Parked; every frame is logged.

## Consequences

- A spec for the framer, `FakeIbus` and the capture kind comes first (read-only), then the
  `bmw_e` pack; transmit work waits for this ADR's gates and U5.

## Alternatives considered

- **Reuse `CanLink`.** Rejected: no IDs, no arbitration, byte-level framing.
- **Treat automations as `comfort`.** Rejected: ADR-0018 Q4 bars `comfort` from vehicle buses.
