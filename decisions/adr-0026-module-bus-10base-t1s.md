---
title: "ADR-0026 — Module bus: 10BASE-T1S, with CAN and Wi-Fi as fallback"
area: decisions
status: locked
version: 1.2
updated: 2026-10-06
depends_on: [references/research/t1s_module_bus.md, references/t1s_bench_plan.md, references/research/hardware.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0024-body-bus-links-passive-by-default.md]
summary: >
  Two network tiers: IP for the computer tier (Pi, head unit, phones, cameras, cloud) and 10BASE-T1S (IEEE 802.3cg, PLCA) for our own module bus once we build hardware, on the Microchip LAN8651 SPI MAC-PHY. CAN or Wi-Fi are the dev-kit and fallback module transports; CAN stays for nodes that must sleep at µA and wake on the bus until T1S wake is proven. One transport-agnostic message model: VSS-named, MQTT-style topics. The car's own buses are out of scope. No Wi-Fi for alarm-critical links. Security is standard practice, amended by the owner on 2026-10-06: every module authenticates with TLS/mTLS and a device certificate, MQTT 5 authentication with per-device ACLs, no trust from bus membership, no default passwords; people sign in with passkeys (WebAuthn) or passwords; the µA CAN fallback's equivalent is open. Bench boards come from another supplier, and Ethernet or Wi-Fi may stand in as a prototype backbone, but T1S is confirmed only by the T1S bench plan's pass/fail criteria.
---

# ADR-0026 — Module bus: 10BASE-T1S, with CAN and Wi-Fi as fallback

> **Amended by [ADR-0032](adr-0032-one-node-optional-brain.md) and [ADR-0033](adr-0033-action-categories-and-approvals.md), 2026-10-06:** the PLCA coordinator is the node, Lite trust comes from pairing with the broker on the node, and the guardian is a node variant (see Amendments 3–7).

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06; from the
  [T1S research](../references/research/t1s_module_bus.md)). Amended by the owner on
  2026-10-06: security and bench sourcing (see [Amendments](#amendments-2026-10-06)).

## Context

- Ostler's add-on modules (relay box, sensors, buttons, HEVAC controller, the guardian)
  need a wired bus. The [hardware research](../references/research/hardware.md) proposed a
  private CAN bus bridged to MQTT by the guardian; that is research, not an ADR.
- 10BASE-T1S is single-pair, multidrop Ethernet: 10 Mbit/s half duplex, PLCA, at least
  8 nodes on 25 m. SPI MAC-PHYs cost about $4–6 and have drivers in mainline Linux (6.12+),
  ESP-IDF and Zephyr. So IP, and with it MQTT, reach every module without a gateway
  ([T1S research §1–5](../references/research/t1s_module_bus.md)).
- T1S sleep/wake (OPEN Alliance TC10) exists in silicon but in no driver we would use, and
  it wakes every node. CAN selective wake (ISO 11898-2:2016) is proven at under 64 µA
  ([§6](../references/research/t1s_module_bus.md#6-wake-and-sleep)).
- ADR-0016 makes VSS the canonical name of a meaning; ADR-0017 adopts MQTT.

## Decision drivers

- One message model and one software stack from the Pi to the smallest module.
- Alarm-critical links must work with the Pi off and with no radio.
- Parked drain in µA for anything that must wake the car's electronics.
- Open standards first (ADR-0017); buy dev kits now, build hardware later.

## Decision

**Two tiers.**
1. **Computer tier: IP** (Ethernet, Wi-Fi, LTE) for the Pi, head unit, phones, cameras and
   cloud.
2. **Module tier: 10BASE-T1S** (IEEE 802.3cg, PLCA on) for **our own module bus once we
   build hardware**. Reference part: **Microchip LAN8651** SPI MAC-PHY for Pi and ESP32-S3
   nodes; LAN867x PHYs only on MCUs with an EMAC. OA TC6 MAC-PHYs from other vendors
   (onsemi, TI, ADI) are second sources. The PLCA coordinator (node 0) is an
   always-powered node, normally the guardian.

**One transport-agnostic message model.** Every module message is a **VSS-named,
MQTT-style topic** with a JSON payload (ADR-0016, ADR-0017). On T1S and Wi-Fi it is MQTT
over IP. On CAN it is a compact, generated mapping of the same topics; the bridge is
mechanical and holds no meaning of its own. Firmware and server code name topics, never
transports.

**CAN or Wi-Fi are the dev-kit and fallback module transports.** **CAN stays for any
node that must sleep at µA and wake on the bus** until the bench plan proves T1S
sleep/wake. The harness carries a **separate wake wire** beside the T1S pair, so a
sleeping node can be woken without depending on TC10.

**The car's own buses are out of scope.** K-line, vehicle CAN and I/K-Bus are spoken as
the car provides them, under ADR-0020, ADR-0022 and ADR-0024; the module bus never shares
wires with them, and nothing bridges module-bus topics onto a vehicle bus.

**Never rely on Wi-Fi for alarm-critical links.** Alarm inputs, the guardian's wake of
the Pi and siren or immobiliser outputs use a wire (T1S, CAN, the wake wire or a GPIO).
Wi-Fi may carry convenience and telemetry only.

**Security: standard practice, not a bus-specific scheme** (amended 2026-10-06). The
module bus is physically reachable by anyone in the car, so being on it earns no trust.
- **Every module authenticates** with TLS (mTLS) using a **device certificate**, whatever
  the IP transport (T1S, Ethernet, Wi-Fi). A node with no valid certificate gets no
  connection.
- **The broker uses MQTT 5 authentication with per-device ACLs:** each module may publish
  and subscribe only to its own topics; commands and alarm messages are accepted only from
  an authenticated client whose ACL allows them.
- **No trust from bus membership alone**, for telemetry as much as for commands, and **no
  default passwords**; any password is set by the owner at pairing.
- **People authenticate with passkeys (WebAuthn) or passwords**, through the user accounts
  of [ADR-0029](adr-0029-accounts-multi-vehicle-sharing-and-social.md). Modules use certificates, never a person's credentials.
- **Open: the µA CAN fallback nodes** cannot run TLS. They need an equivalent, for example
  a gateway that terminates TLS for them and authenticates their CAN frames (key, counter
  and MAC per frame). This is not decided; until it is, no actuator command or alarm-arm
  change is accepted from a CAN-only node, and the **U5 threat model** settles it along
  with replay, provisioning and MACsec on T1S.

## Confirmation

The [T1S bench plan](../references/t1s_bench_plan.md) passes, on a 3-node bench, every
criterion it lists, in particular:
- PLCA access latency p99 ≤ 1 ms and jitter ≤ 0.5 ms for 200-byte frames;
  goodput ≥ 6 Mbit/s summed;
- MQTT round trip p99 ≤ 10 ms, no loss over 1 hour;
- ESP32-S3 node asleep ≤ 200 µA on its 3.3 V rail, with the MAC-PHY rail switched off
  (wake-wire design);
- wake by the wake wire to the first MQTT message ≤ 500 ms, 100/100;
- through a 12 V → 6 V, 40 ms dip: no reboot of any node, link back ≤ 100 ms, no
  duplicated command;
- 25 m segment with all three nodes, zero CRC errors over 10 minutes.

The T1S part of this decision is confirmed when those pass; **T1S for µA wake nodes**
needs its own bench pass (TC10 in a driver) before CAN is dropped for them.

**A prototype backbone does not confirm T1S** (amended 2026-10-06). Where T1S parts are
unavailable, modules may be prototyped on 100BASE-TX Ethernet or Wi-Fi. That is valid for
firmware, the message model, MQTT and security work, because the message model is
transport-agnostic. The T1S-specific measurements (PLCA latency and jitter, the cranking
dip, cable length and EMC) still have to pass on T1S hardware before T1S is confirmed. A
Wi-Fi prototype stays on the bench: it never carries an alarm-critical link in a car.

## Consequences

- A spec for the module-bus message mapping (topic tree, CAN mapping, certificates and
  ACLs, the CAN-fallback authentication) comes before any firmware; `asyncapi.yaml` gains
  the MQTT channels at U5.
- The Pi kernel needs `oa_tc6`, `microchip_t1s` and `lan865x` built as modules plus an
  overlay; we carry them until Pi OS enables them.
- Each module board costs about £3 more than a CAN node.
- Every module needs a device certificate and a provisioning step at pairing, and the Pi
  runs a local CA (the ADR-0021 trust question) and an MQTT 5 broker with ACLs.
- Bench ESP32 boards are bought from another supplier than the out-of-stock one; the bench
  plan lists the substitutes.

## Alternatives considered

- **CAN only.** Rejected for the module tier: needs a gateway and a second message
  encoding; 0.5 Mbit/s. Kept as fallback and for µA wake.
- **Wi-Fi only.** Rejected: not for alarm-critical links; drain and coexistence.
- **10BASE-T1L or 100BASE-T1.** Rejected: point-to-point, so a switch per branch.
- **RS-485/Modbus.** Rejected: no IP, bespoke framing.
- **Custom bus signing with trusted-local telemetry** (the first text of this ADR: per-node
  key, counter and MAC over commands and alarms, telemetry trusted until U5). Replaced on
  2026-10-06 by standard TLS/mTLS, MQTT 5 auth and ACLs, at the owner's direction; a
  per-frame MAC survives only as one option for the CAN fallback.

## Amendments (2026-10-06)

The owner amended this ADR on the day it was accepted:
1. **Security.** The custom signing envelope and the trusted-local telemetry rule are
   dropped for standard practice: TLS/mTLS device certificates, MQTT 5 authentication with
   per-device ACLs, no trust from bus membership, no default passwords, passkeys
   (WebAuthn) or passwords for people (ADR-0029). The CAN fallback's equivalent is open.
2. **Bench parts.** ESP32 boards come from another supplier; when T1S parts cannot be had,
   an Ethernet or Wi-Fi backbone may stand in for prototyping. T1S is still confirmed only
   by the T1S measurements of the bench plan.

Later on 2026-10-06, with the node/brain direction
([ADR-0032](adr-0032-one-node-optional-brain.md),
[ADR-0033](adr-0033-action-categories-and-approvals.md)):
3. **PLCA coordinator.** The always-powered PLCA coordinator (node 0) is **the node**, or
   the guardian variant when it replaces the plain node.
4. **Lite trust.** On Ostler Lite (no brain) the node holds the MQTT broker, and trust
   comes from pairing; there is no Pi CA. With a brain fitted, its broker bridges to the
   node's.
5. **Alarm-critical links work with the Pi off.** The driver "alarm-critical links must
   work with the Pi off and with no radio" is elevated to ADR-0033's tested rule: node →
   notification works with the brain off and no cloud, checked by a confirmation test.
6. **The guardian is a node variant, not an add-on module.** It is the same firmware on
   security-built hardware (ADR-0032), so it is not counted among the add-on modules in
   the Context.
7. **Wake.** "The guardian's wake of the Pi" now reads **the node wakes the brain**; that
   wake still uses a wire, never Wi-Fi.
