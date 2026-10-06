---
title: "ADR-0038 — Mesh: car-to-car and off-grid"
area: decisions
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [references/research/mesh_networking.md, references/research/addons_catalogue.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Proposed, pending owner answers. No mesh inside the car: the in-car network stays routed T1S/Ethernet. A mesh only links car to car, to a base or camp, or off-grid, as its own subnet or non-IP network joined at the brain or a gateway, and it is always a remote path: Read and alerts go out, messages and peer positions come in as data, and nothing from a mesh ever commands the car. First a Meshtastic-compatible LoRa add-on (any owner radio, then our own board on stock Meshtastic firmware) behind a thin GPL-3 VSS bridge with no actions, strict broker ACLs, rate limits and privacy defaults (position sharing opt-in, coarse by default, private channel, no VIN or vehicle id). Mesh identities stay separate from Ostler device keys, pairing keys and passkeys. MeshCore and Reticulum/LXMF are bench-tested as the richer car-to-car layer for the social app; Styrene and Ratspeak stay references; Babel, not batman-adv, if a Wi-Fi IP mesh is ever wanted.
---

# ADR-0038 — Mesh: car-to-car and off-grid

- **Date:** 2026-10-06
- **Status:** proposed (draft for the owner; nothing here is accepted until the open
  questions are answered). Builds on
  [ADR-0027](adr-0027-ip-everywhere-ecosystem-architecture.md) and
  [ADR-0033](adr-0033-action-categories-and-approvals.md); evidence in the
  [mesh research](../references/research/mesh_networking.md).

## Context

- The add-ons catalogue and the vision list LoRa/Meshtastic convoy messaging and a
  batman-adv/802.11s convoy mesh, with no decision on where a mesh sits or what it may do.
- The owner (2026-10-06) fixed the placement: the in-car network stays routed T1S and
  Ethernet with no mesh; a mesh is only for car-to-car, a base or camp, or off-grid, as its
  own subnet bridged at the brain or a gateway. The lean: a Meshtastic-compatible LoRa
  add-on first for reach, behind a thin VSS bridge (position, alarm state, alerts in and
  out), and the Reticulum family as the richer layer for the social app (ADR-0029 §9).
- Live checks (research §2–§3): Meshtastic is GPL-3.0 with the largest radio base;
  MeshCore is MIT with learned routes; Reticulum's licence is MIT plus use restrictions and
  its author has stepped back; Styrene is a young solo platform with remote shell and
  reboot; Ratspeak is an AGPL client on Reticulum, not a new protocol; batman-adv floods L2
  broadcast and cannot run on an ESP32.

## Decision drivers

- No new path to the car: the node gate (ADR-0032) stays the only one, and a mesh is
  remote (ADR-0033 §6).
- Reach with radios people already own (bikers, overlanders, clubs).
- Privacy by default for location (ADR-0029 §8); no VIN anywhere (ADR-0036).
- Core and node firmware stay commercially licensable (ADR-0012, ADR-0025).
- Low power, off-grid, no internet needed.

## Decision (proposed)

**1. Placement.** No mesh inside the car. A mesh is its own subnet (IP meshes) or its own
non-IP network (LoRa), joined to the car network only at the brain or a gateway, behind the
same firewall as an uplink. No L2 bridging into a car segment; no mDNS reflection onto a
mesh.

**2. A mesh is a remote path, Read and alerts only.**
- Out: position, alarm state and owner-selected alerts. In: text, peer positions and peer
  alerts, recorded and shown as untrusted data.
- The bridge declares **no actions** in its manifest. The broker ACL lets it publish only
  under its own `in/` and `state/` topics and never to an action, grant or command topic.
- Remote alarm arm and disarm (ADR-0033 §6 as amended) is **not** offered over a mesh, and
  `OSTLER_ALLOW_REMOTE_CONTROL` does not open mesh paths (open question 3).

**3. First: a Meshtastic-compatible LoRa add-on.**
- Step one: any Meshtastic radio the owner has, over USB serial, BLE or TCP, bridged on the
  brain (or the phone app on Ostler Lite).
- Step two: our own LoRa add-on running **stock Meshtastic firmware**, joined to the node or
  brain over UART or T1S, so it works with the community's radios.
- The bridge is a **separate GPL-3 program or pack** (it uses the GPL-3 protobufs);
  core, the C decoder and the node firmware never link Meshtastic code (ADR-0025).
- Branding follows Meshtastic's trademark rules ("works with Meshtastic"; no mark on the
  hardware without a licence).

**4. The thin VSS bridge** (research §5) is specified in the module-bus message spec:
topics, a compact Ostler payload with a plain-text fallback, and rate limits (position
10 min parked, 2 min moving, never under 60 s; alarm state on change; alerts debounced per
class; hop limit 3; duty cycle obeyed, position dropped before alerts).

**5. Privacy defaults.** Position sharing **off** until opted in per channel; when on,
**coarse** (about ±3 km) unless a live ride raises it; positions never on the public default
channel; a private channel with a random key; no VIN, `<vid>`, plate or account name in any
mesh field; the radio's own MQTT uplink off; nothing relayed from the mesh to the internet
unless opted in.

**6. Identity separation.** A mesh identity (Meshtastic node key, MeshCore key, RNS
identity) is never derived from, stored as, or used as an Ostler device certificate, pairing
key or passkey (ADR-0029, ADR-0032 §12), and no mesh platform's single root secret (for
example Styrene's) may hold ours. Pairing a radio with the bridge is a local physical step.

**7. The richer car-to-car layer** for groups, rides and convoys (ADR-0029 P4) is chosen by
a bench test of **MeshCore** and **Reticulum/LXMF** (as an unmodified program on the brain).
**Styrene** and **Ratspeak** stay references until their provenance and maturity settle;
any fleet-ops feature (remote exec, reboot, config push) is off or absent on every Ostler
device.

**8. Wi-Fi IP mesh**, only if a use appears: **Babel** on the brain or a travel router, its
own routed subnet. batman-adv only behind the same routed edge, never bridged.

## Bench-test plan (richer layer)

Two cars or a car and a camp, 2–4 LoRa boards of one model per stack, EU868:
- the same scripted traffic (position every 2 min, ten texts, five alerts) over 1, 2 and 3
  hops, in a town and on an open trail;
- measure delivery rate, latency, airtime and duty-cycle hits, and current draw parked;
- check the bridge ACL refuses any publish outside `in/` and `state/` on every stack;
- check that no field on air carries a VIN, `<vid>` or precise position when coarse is set;
- for Reticulum: rnsd on a Pi brain with an RNode; for MeshCore: companion firmware over
  USB; Meshtastic as the baseline.

## Confirmation

- **Paper check:** no spec or doc proposes a mesh inside the car, a mesh path to an action,
  or mesh code in core or the node firmware.
- **Bridge tests (fake radio):** the manifest has no actions; the broker refuses the
  bridge's publishes outside its own topics; an inbound text shaped like a command executes
  nothing; position is off by default and coarse when first enabled; no VIN or `<vid>` in
  any outbound frame; rate limits hold under an alert storm.
- **Gate matrix (ADR-0033):** the mesh transport is refused for every category above Read,
  with the install override on or off.
- **Licence check:** `reuse lint` shows the bridge as GPL-3 and core never imports it.
- **Bench:** the plan above, with results in a reference note before the richer layer is
  chosen.

## Consequences

- The module-bus message spec gains the mesh bridge topics and the mesh transport value.
- The add-ons catalogue's LoRa and mesh rows point here; the vision's batman-adv line is
  replaced by Babel-if-needed.
- The UI's links view shows mesh links (UI spec §3.7, proposed Network page) with airtime and
  peers heard.
- A GPL-3 pack or program joins the excluded list for the commercial build.

## Alternatives considered

- **A mesh inside the car.** Rejected by the owner: routed T1S/Ethernet stays.
- **batman-adv as the convoy mesh.** Not chosen: L2 floods mDNS and broadcast, needs a
  bigger MTU, Linux only; Babel keeps the routed model.
- **Reticulum first.** Not chosen: far fewer radios in people's hands, a restrictive licence
  and an absent maintainer; kept for the richer layer.
- **Meshtastic code inside the node firmware.** Rejected: GPL-3 in the node would break the
  commercial build, and a mesh does not belong next to the gate.
- **Our own LoRa protocol.** Rejected: no interop with radios people own (ADR-0017).

## Open questions (owner)

1. Is the LoRa add-on Meshtastic-compatible first, as proposed, or MeshCore first?
2. Which of Reticulum/LXMF, Styrene and Ratspeak (and MeshCore) to bench-test for the
   richer layer? Proposed: MeshCore and Reticulum/LXMF only.
3. Should remote arming (never disarming) ever be allowed over a mesh, for example from a
   camp base? Proposed: no.
4. On Ostler Lite, may the node itself be the mesh gateway (alarm alerts to a camp with no
   brain and no phone), given the placement says "brain or gateway"?
5. Is the Reticulum License's no-AI-training clause acceptable alongside our MCP server and
   AI tooling (ADR-0030), even when run as a separate program?
