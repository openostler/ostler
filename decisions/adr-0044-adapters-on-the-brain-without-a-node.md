---
title: "ADR-0044 — Adapters on the Brain without a node: a soft-gated exception to \"the Brain never touches the car\""
area: decisions
status: locked
version: 1.0
updated: 2026-10-07
depends_on: [CONSTITUTION.md, specs/2026-10-07-source-adapters-design.md, references/research/third_party_adapters.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-node-source-design.md]
summary: >
  Accepted: approved by the owner on 2026-10-07 ("approve all", DMD round; decision list items 62–69). The Brain may host a third-party adapter (ELM327 and clones, STN/OBDLink, KKL cables, SocketCAN and slcan dongles, WiCAN) only for a vehicle that has no Ostler node, as the source-adapters spec §3 describes. The adapter is driven through the soft gate, the platform's own Python TxGate run in the process that owns the adapter, under the adapter rules R1–R10: read-only by default; clear codes only when Parked or Idling is evidenced from the bus, never the airbag; actuator tests, procedures and allowlisted frames only after a per-vehicle, per-adapter owner opt-in, Parked, local, never on a clone or over Wi-Fi; Tier 4 never; nothing above Tier 0 while Moving or with unknown speed; no transmit to find the bus unless Parked; rate limits; local only, with no remote path, token, MCP client or the remote-control override; listen-only shown as verified or not; identity data scrubbed. One tester per bus: beside a node an adapter is passive only, and before a K-line init it listens for 3 s and refuses if another tool is active. Amends the CONSTITUTION's two lines ("the brain never touches the car", "the node transmit gate is the only path to the car") and ADR-0032 §2–§3 with this exception; laptop and phone hosts need no exception. ADR-0039's rejection of raw serial over the network stands.
---

# ADR-0044 — Adapters on the Brain without a node

- **Date:** 2026-10-07
- **Status:** accepted. Approved by the owner on 2026-10-07 ("approve all", DMD round;
  decision list items 62–69, the
  [source adapters spec](../specs/2026-10-07-source-adapters-design.md) decisions 1–11). It is
  the "new ADR" that spec's §3 asks for. **Amends** the
  [CONSTITUTION](../CONSTITUTION.md) (two Safety and Layering lines) and
  [ADR-0032](adr-0032-one-node-optional-brain.md) §2–§3 (dated amendment there); it
  supersedes neither. Evidence:
  [third-party adapters research](../references/research/third_party_adapters.md).

## Context

- The owner asked for off-the-shelf scanners (ELM327 over Bluetooth Classic, BLE, Wi-Fi and
  USB; OBDLink/STN; USB K-line cables; SocketCAN dongles; J2534 later) as Ostler data
  sources, with honest limits against the node and safety rules where there is no hardware
  gate.
- Ostler is node-first. The CONSTITUTION says "the brain never touches the car" and "the node
  transmit gate is the only path to the car" (ADR-0032 §2–§3). Those lines exist so that no
  device can bypass the node's gate.
- With **no node** in the vehicle there is no gate to bypass. Without an exception, a Brain
  owner with an ELM adapter gets nothing from the Brain, while the same adapter already works
  on a laptop (the KKL dev path) and is planned on the phone.
- Most of the plumbing exists in core: the `CanLink`s (SocketCAN, slcan, GVRET, python-can),
  the KKL `SerialTransport`, the `ObdRequestLink` with pacing and the Python `TxGate`, with the
  shared gate vectors (spec §1).
- A general-purpose host has no driving-state sensor of its own and cannot offer a Stop that
  survives a host crash, so any soft gate must be stricter than the node's.

## Decision drivers

- Never weaken the node's position: where a node exists, it stays the only path to the car.
- Let a user try Ostler, read a second car or work in a garage with no node, on every host
  they own, the Brain included.
- One gate implementation, checked by the same shared vectors on every tier.
- Honest limits shown in the UI, with no nagging.

## Decision

1. **The exception.** The Brain may host a third-party adapter **only for a vehicle with no
   node**. "No node" means: no node manifest, no node gate claim on any of the vehicle's buses
   seen through NodeSource, and no node registered for the vehicle in the garage. When a node
   appears, the adapter falls back to passive (item 4) at once. Laptop and phone hosts were
   already outside the rule (the rule names the Brain) and need no exception.
2. **The soft gate.** The adapter is driven only through the **soft gate**: the platform's
   Python `TxGate`, run in the process that owns the adapter (on the phone, its C build in
   WebAssembly), extended to ELM/STN and K-line requests and checked by the same shared gate
   vectors as the node's gate. It is labelled "Soft gate" wherever the adapter is shown.
3. **The adapter rules** (spec §7), stricter than the node's:
   - **R1 Read-only by default:** Tier 0 reads only (OBD services `01 02 03 06 07 09 0A`, UDS
     `22 19` and a physical `3E` on CAN and ISO-TP; OBD over ISO 9141/KWP and pack-declared
     read recipes on K-line). Mode 08 never.
   - **R2 Clear codes** under ADR-0033 §5 with no opt-in, **only when Parked or Idling is
     evidenced from the bus**; the airbag/SRS never.
   - **R3 Opt-in for more:** actuator tests (Tier 2), procedures (Tier 3) and pack-allowlisted
     frames only after the **owner** switches on "Adapter actions" **for this vehicle and this
     adapter identity**, after a warning naming what a node would add; local-only, audited,
     badged while on, off by default; every ADR-0033 rule still applies; refused on a clone or
     an unknown verdict and over Wi-Fi adapters.
   - **R4 Tier 4 never** (coding, flashing, writes).
   - **R5 Nothing above Tier 0 while Moving or with unknown speed;** speed is re-read from the
     bus before every frame of an action, and a reading older than 1 s stops it.
   - **R6 No transmit to find the bus unless Parked:** no automatic protocol search (`ATSP0`),
     probe or wrong-rate frame while not Parked (ADR-0022, ADR-0023).
   - **R7 Rate limits:** the shared pacer (one request in flight, ADR-0020 pacing) plus a
     per-adapter ceiling.
   - **R8 Local only:** adapter actions start only from the host's own UI on a local link. No
     remote path, share, token, MCP client, Home Assistant or MQTT can start one, and
     `OSTLER_ALLOW_REMOTE_CONTROL` does not extend to adapters. An AI client's accept never
     counts.
   - **R9 Listen-only shown as verified or not:** `true` only when the device confirms it;
     ELM `CSM1` without readback is "requested"; clones are "unsupported".
   - **R10 Identity data** scrubbed on the host at write time (ADR-0036).
4. **One tester per bus** (spec §7.2). K-line stays one module at a time; before the first
   init the adapter **listens for 3 s and refuses** if it sees foreign traffic. **Beside a
   node** an adapter is **passive only** (verified listen-only CAN sniffing; no K-line access;
   no OBD requests). An adapter holding a session on a host on the car LAN publishes a gate
   claim with `"reason": "adapter"` and `"gate": "soft"`, so a node arriving later reports
   `gate_conflict` and the Network page shows "Adapter on this bus".
5. **Clones** are detected by command tests (spec §5) and allowed for Tier 0 reads and R2
   clears only, with a "Clone: read-only" chip.
6. **Unchanged.** ADR-0039's rejection of raw serial over the network stands: the Brain hosts
   an adapter it is attached to (USB, Bluetooth, or a Wi-Fi adapter it connects to directly)
   whose interpreter owns the bus timing; raw K-line bytes are never tunnelled over Bluetooth or
   the network (research §7). The KKL cable stays the dev path for the D2 node
   work; adapters become a supported product path for reads. The node stays the product for
   the alarm, geofence, Brain wake, 12 V watch, signed grants, the raw tap with MCU timestamps
   and K-line on cars no adapter can reach.

## Confirmation

- The shared gate vectors run against the soft gate unchanged, plus the adapter cases of spec
  §12: R1 reads in every state; R2 clear Parked, Idling, Moving, unknown; R3 without opt-in,
  with opt-in on a clone, on Wi-Fi, while Moving; R4 Tier 4; R6 `ATSP0` while not Parked; R8 a
  remote origin with the override on (refused).
- Coexistence tests: a node's gate claim or manifest makes a Brain-hosted adapter passive;
  foreign K-line traffic before init refuses the init; the adapter's own claim is published
  and released.
- A layering test: `openostler.adapters` imports nothing from `web` or any pack.
- Bench: the D2's OBDLink MX+ or EX session (decision list item 68) records whether an STN chip
  can reach the Td5 and SLABS; until then the D2 stays KKL- and node-only for those modules.

## Consequences

- The CONSTITUTION's two lines gain the exception, citing this ADR (v1.7).
- ADR-0032 gains a dated amendment to §2–§3.
- Core gains `openostler/adapters/` (ADR-0034: stays in `ostler`; BLE behind an optional
  `[ble]` extra, which the source-adapters spec's A3 phase introduces with its own extras
  entry); `source_kind: "adapter"` joins the snapshot.
- The Brain's threat model (U5) covers a Brain that drives a bus through the soft gate.

## Alternatives considered

- **Laptop and phone only; the Brain stays car-free with no exception.** Not chosen: a Brain
  owner with an adapter would get nothing, and with no node there is no gate to protect.
- **No actions at all through adapters.** Not chosen: clearing codes is a standard OBD
  service, and actuator tests stay behind a per-vehicle, per-adapter owner opt-in.
- **Refuse clones entirely.** Not chosen: it loses most cheap-adapter users; clones read and
  clear only.
- **Rely on the start-time refusal only** (no 3 s listen, no claims). Not chosen: a second
  tool on a splitter would collide on the shared bus.

## Relation to other ADRs

- **ADR-0032:** §2–§3 amended (dated amendment there); everything else stands.
- **ADR-0033:** every category, tier and confirmation rule applies to adapter actions; R8 is
  stricter than its remote rule.
- **ADR-0020, ADR-0022, ADR-0023:** pacing, profiles and passive detection apply; R6 adds the
  Parked condition for any transmit to find the bus.
- **ADR-0034:** adapter support stays in `ostler`; J2534 later as `ostler-adapter-j2534`.
- **ADR-0036:** identity scrub applies on every adapter link.
- **ADR-0039:** the raw-serial-over-network rejection stands.
- **ADR-0042:** adapter support is core (its DMD-round amendment).

## Changelog

- 2026-10-07 — v1.0, accepted: approved by the owner on 2026-10-07 ("approve all", DMD
  round), from the source-adapters spec §3 and §7.
