---
title: "ADR-0020 — CAN links: listen-only by default"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [references/research/canbus_headunit.md, references/research/hardware.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0002-layered-stdlib-core.md]
summary: >
  CAN gets a frame-level CanLink interface beside the byte-level Transport, with SocketCAN first (stdlib AF_CAN, vcan in CI). Every vehicle bus is listen-only by default. Transmitting needs a pack-declared allowlist plus Parked plus the server gate; the only standing exception is Tier 0 diagnostic read requests on the diagnostic IDs. MQTT is never bridged to vehicle CAN. ELM/STN adapters are an ObdRequestLink, not a CanLink.
---

# ADR-0020 — CAN links: listen-only by default

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06; from the CAN and head-unit research)

## Context

- `src/openostler/transport/` defines `Transport` as a **raw byte pipe**
  (`SerialTransport`, `EspTransport`, `LoggingTransport`). That fits K-line, where framing
  lives above it. CAN is frame-based; pushing frames through a byte pipe makes every
  layer re-frame them ([CAN research A5](../references/research/canbus_headunit.md)).
- The D2 has no comfort CAN. CAN serves later cars (`generic_obd2`, CAN/UDS packs), our
  private add-on bus and head-unit emulation.
- Cheap tools transmit by default: WiCAN ships in normal mode and transmits anything
  published to `…/can/tx`; ELM clones mishandle monitor mode.

## Decision drivers

- No accidental frame on a vehicle bus, ever.
- One frame interface for many adapters, with CI on `vcan` and no hardware.
- No new runtime dependency (ADR-0002).

## Decision

**A frame-level `CanLink` sits beside `Transport`**, which stays for byte links.
- `CanLink`: open/close · send(frame) · recv(timeout) · set_filters · `listen_only` ·
  bitrate · fd · capabilities `{tx, fd, timestamps, max_rate}`.
- Order: **1 `SocketCanLink`** (stdlib `socket.AF_CAN`; CarPiHAT, gs_usb, can327, `vcan`
  in CI) · 2 slcan/GVRET for our ESP32 nodes and WiCAN Pro over TCP · 3 python-can
  backends as an optional extra · J2534 last.
- `IsoTpChannel` uses kernel `CAN_ISOTP` on SocketCAN, userspace can-isotp (MIT) elsewhere.
- **ELM327/STN is an `ObdRequestLink`**, not a `CanLink` (request → response; shown as
  "ELM: limited").
- `LoggingCanLink` keeps the JSONL capture discipline and also writes candump format.
- `MqttCanLink` is **read-only ingest**; its transmit is never implemented.

**Listen-only is the default on every vehicle bus** (SocketCAN `listen-only on`, STN
`STCMM 0`, WiCAN `silent`). The UI shows the mode on the link chip.

**Transmit on a vehicle bus needs all three:**
1. a **pack-declared allowlist** entry (ID, DLC, rate);
2. **Parked** driving state;
3. the **server-side gate** with the action's safety tier (ADR-0018).

The one standing exception is **Tier 0 diagnostic read requests** on the diagnostic IDs
(e.g. `0x7DF`/`0x7E0`–`0x7E7`; OBD `01`/`09`, UDS `22`/`19`/`3E`): allowed in every state,
one request in flight, ≥ 50 ms between polls per ECU, backing off on NRC `0x21`/`0x78`.
Discovery sweeps stay Parked-only and use the read-only service list of UI spec §8.1.

**Never bridge MQTT to vehicle CAN.** No remote path transmits on a vehicle bus; WiCAN
`can/tx` stays disabled or inert under `silent`.

**Never touch safety-critical wiring.** Vehicle buses are reached through the OBD port;
no splicing into airbag, ABS or EPS. The private add-on bus is physically separate; its
traffic follows the device rules (ADR-0018), not this allowlist.

**The CAN-box emulator** (planned add-on) talks UART to the head unit and is fed from
Ostler; its vehicle-CAN port, if fitted, is hard-set listen-only.

## Confirmation

- Tests on `vcan`: a `SocketCanLink` opens listen-only unless an allowlisted, Parked,
  gated transmit is requested; a non-allowlisted frame is refused; `MqttCanLink.send`
  raises.
- Server tests: CAN transmit refused while Moving or over a remote path.

## Consequences

- The first CAN work (U4 `generic_obd2` over SocketCAN, or the first CAN pack) needs a
  spec that adds `CanLink` and the pack allowlist schema.
- A listen-only node does not ACK, so a two-node bench bus shows errors; documented.

## Alternatives considered

- **Frames through the byte `Transport`.** Rejected: every layer would re-frame.
- **python-can as a core dependency.** Rejected: ADR-0002; it stays an optional extra.
- **Transmit by default, as WiCAN does.** Rejected: unsafe and invisible to the user.
