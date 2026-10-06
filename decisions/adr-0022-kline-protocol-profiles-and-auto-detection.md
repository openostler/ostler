---
title: "ADR-0022 — K-line protocol profiles and auto-detection"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [references/research/muki01/README.md, references/research/muki01/obd2_kline_reader.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, CONSTITUTION.md]
summary: >
  K-line protocols become data: a profile record in a planned src/openostler/kline/profiles.py holds baud, parity, framing (ISO 9141-2 68 6A F1 or KWP length-byte formats), checksum, header and length mode, P1–P4 and W1–W5, idle and keep-alive interval, with the init method (fast, 5-baud, none) as its own field; packs override. Auto-detection tries KWP fast init, then 5-baud 0x33, classifies by key bytes and verifies the inverted address. Manufacturer protocols are never auto-probed. Probing an unknown car is Parked-only; re-initialising a known profile is allowed in every state. Keep-alive and an 82 release are required. The 5-baud address goes out 8N1 (the 2026-08-04 fix); the ISO wording stays open.
---

# ADR-0022 — K-line protocol profiles and auto-detection

> **Amended by [ADR-0032](adr-0032-one-node-optional-brain.md), 2026-10-06:** the KKL cable path becomes dev-only; production K-line runs on the node, and the server tests also become node tests through shared vectors (see Amendments).

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06; proposal (i) of the
  [muki01 synthesis §d](../references/research/muki01/README.md#d-adrs-needed))

## Context

- The platform's K-line stack (`kline/`, `kwp2000/`, `transport/`) is shaped by one car:
  the D2 pack's Td5 modules, all KWP2000, each with a known address and init. `generic_obd2`
  (U4) over a KKL cable must talk to cars we have never seen: ISO 9141-2, KWP2000 slow
  init, KWP2000 fast init.
- The [muki01 K-line audit](../references/research/muki01/obd2_kline_reader.md) found a
  good design idea (one data row per protocol, the init method as a separate axis) wrapped
  in unsafe habits: no keep-alive and no `82` on exit, a 5.5 s idle before every init,
  even parity on 5-baud addresses, and auto-detection that ignores the KWP key bytes.
- An init pulse on a bus where another tester, or a still-open session, is talking can
  break that session. On an unknown car we cannot know that no one else is there.

## Decision drivers

- One K-line code path for the D2 pack and `generic_obd2`, with no per-car branches.
- No probe on an unknown car while it is being driven.
- Keep what the car has already proven: the 8N1 5-baud fix, `tolerant=True`, `82` release.
- Vehicle specifics live in packs; the platform stays generic.

## Decision

**Profiles are data.** A planned `src/openostler/kline/profiles.py` holds one record per
protocol, with these fields:
- line: baud, serial format and parity, 5-baud address parity (default none);
- framing: ISO 9141-2 (`68 6A F1` requests, `48 6B xx` replies, no length byte) or the
  KWP2000 length-byte formats (length in the format byte, or a separate length byte;
  with or without address bytes); checksum (sum-mod-256, XOR, complement);
- timing: P1–P4, W1–W5, the pre-init idle, and the keep-alive interval and request;
- **init method as its own field:** `fast`, `5baud` (with the address) or `none`.

The platform ships generic profiles only (ISO 9141-2, KWP2000 slow, KWP2000 fast).
**Packs override** any field in their `vehicle.json` `transport` block. The D2 pack
declares its profiles and never auto-probes. Manufacturer framings (VAG KW1281, BMW DS2,
Opel KW82, Honda) are profiles that a **pack declares**; they are never auto-probed.

**Auto-detection** (`kline.detect()`, for a car with no pack profile):
1. W5 idle (≥ 300 ms), then **KWP2000 fast init** (`C1 33 F1 81 66`), tolerating a glitch
   byte and an unaddressed `03 C1 …` reply. A positive reply gives KWP2000 fast.
2. Else **5-baud `0x33`**. Read `55 KW1 KW2`, send ~KW2, and **verify the inverted
   address** (`0xCC`); a wrong or missing echo is a failed init, not a guess.
3. **Classify by key bytes:** KW1 == KW2 (`08 08`, `94 94`) → ISO 9141-2; otherwise
   KWP2000, and **decode the KWP key-byte bits** (header and length formats, normal or
   extended timing) into the session's profile instead of assuming them.
4. The result is shown on the Link sheet. A manual override exists only in Developer,
   under service mode.

**Driving state.** **Probing an unknown car is Parked-only.** Re-initialising a profile
that is already known (pack-declared, or detected earlier in this connection) after a link
drop is allowed **in every driving state**, like ADR-0020's Tier 0 exception, with backoff.
A long idle (P3max) is used only after an abandoned session, never before every init.

**Session discipline** (required for every profile):
- **Keep-alive:** TesterPresent `3E` on KWP2000 (packs may narrow it, e.g. the D2's bare
  `3E` for SLABS); a `01 00` request on ISO 9141-2, which has no TesterPresent. It goes
  out within the profile's interval whenever nothing else has, well inside P3max.
- **Release:** StopCommunication `82` on exit, module switch and error paths
  (`EcuSession.release()`). ISO 9141-2 has no `82`; the tester stops and waits P3max.

**5-baud address parity.** The address byte goes out **8N1: eight data bits, no parity
bit set**. This keeps the 2026-08-04 fix (`slow_init_bits`) that stopped `0x29` going
out as `0xA9`. A manufacturer profile may name a parity only with a car result behind it.
The ISO wording ("7 bits + odd parity") stays **open**, recorded in the D2 pack's
init-timing notes; changing the default needs a car result and a new ADR.

## Confirmation

- `FakeKLineEcu` tests: detection order (fast, then 5-baud); classification for `08 08`,
  `94 94` and a KWP key-byte pair; a bad inverted address fails; KW1281/DS2/KW82 are
  never sent by `detect()`.
- Fixture: `0x29` goes out 8N1 (not `0xA9`); `0x33` is unchanged.
- A session idle for 10 s still gets keep-alive inside P3max, and `82` on close.
- Server tests: `detect()` is refused unless Parked; re-init of a known profile is not.

## Consequences

- A new spec, "K-line profiles and detection", comes before U4 (`generic_obd2` over KKL).
- The D2 pack's timing constants move into its declared profile.

## Alternatives considered

- **Profiles as code classes per protocol.** Rejected: packs could not override a field.
- **5-baud first, as the muki01 reader does.** Rejected: a 2 s init where fast init takes
  100 ms, and KWP ECUs are the common case.
- **Auto-probe manufacturer protocols too.** Rejected: unknown frames on an unknown car.

## Amendments (2026-10-06)

Recorded with the node/brain direction
([ADR-0032](adr-0032-one-node-optional-brain.md)); the profile model and the detection
rules above stand.

- **The KKL cable is dev-only.** It stays for the lab, bench work and the Python reference
  tests.
- **Production K-line runs on the node.** The node's portable C link layer reads the same
  profiles (in the `schemas/kline-profile.schema.json` form), applies the same detection
  order and the same Parked-only probing rule, and its gate is the only path to the car
  ([K-line spec §8.1](../specs/2026-10-06-kline-profiles-detection-design.md#81-the-node-path-adr-0032)).
- **The server tests become node tests too.** The Confirmation cases (detection order,
  classification, the 8N1 address, Parked-only `detect()`, re-init without probing) become
  shared test vectors, seeded from the golden tests, run in CI against both the C build and
  the Python reference.
