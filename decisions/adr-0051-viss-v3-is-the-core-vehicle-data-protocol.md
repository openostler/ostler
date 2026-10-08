---
title: "ADR-0051 — VISS v3 is the core vehicle-data protocol on every signal hop; MQTT is external only; the gateway's permissions controller fronts VISS access control; the node gate stays the write authority"
area: decisions
status: locked
version: 1.1
updated: 2026-10-08
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-node-source-design.md, references/research/direction_feed_standards.md, references/research/direction_standard_not_os.md]
summary: >
  Accepted: approved by the owner on 2026-10-08 (direction decisions 4–7, 31–34 and 36: "follow the industry so we do not become our own thing"). Full COVESA VISS v3 over the VSS tree is the core protocol on every hop that carries vehicle signals: node to gateway, Brain to apps, gateway to apps. It uses VISS's own transports, WebSocket first, then gRPC or HTTP where they fit; on a USB serial link the same messages are framed. The internal MQTT module bus (api/asyncapi.yaml, the module-bus spec) and the bespoke SSE /events snapshot become legacy and are migrated in stages, side by side, with deprecation per the changelog policy. MQTT is the external cap only: the gateway app's External MQTT menu publishes to an outside broker (Home Assistant discovery, OVMS topics, others). The gateway's permissions controller is the VISS access-control front end: identity by package and signing key or an owner-approved access request, per-app toggles mapped to ADR-0029 data classes and ADR-0033 categories and tiers, a scoped VISS access token, cautious defaults, revoke with an access log. A VISS set is only a request; the gateway confirms risky ones and the node gate decides; Tier 4 never. Cameras appear as VISS metadata pointing to RTSP or WebRTC; Meshtastic and MeshCore are transports. The gateway job (node link, VISS server, permissions, External MQTT) runs on the Android gateway app or the Brain: Android straight to a node is the server; Android to a Brain is a client that forwards requests; one server per node; one permission set held by the server and synced to the Android gateways and the cloud view; Brain failover mid-drive is open. Amends ADR-0026 and ADR-0027 (the MQTT message model) and the module-bus spec.
---

# ADR-0051 — VISS v3 is the core vehicle-data protocol

- **Date:** 2026-10-08
- **Status:** accepted. Approved by the owner on 2026-10-08 ("I agree with everything", with
  the change "full VISS v3+ is the core protocol … follow the industry so we do not become
  our own thing"; [direction note](../references/research/direction_standard_not_os.md)
  decisions 4–7, 31–34 and 36). Part of
  [ADR-0049](adr-0049-open-vehicle-data-standard-and-app-suite.md). **Amends**
  [ADR-0026](adr-0026-module-bus-10base-t1s.md) (the MQTT-style message model),
  [ADR-0027](adr-0027-ip-everywhere-ecosystem-architecture.md) §5 (MQTT 5 as the one message
  model) and the [module-bus spec](../specs/2026-10-06-module-bus-messages-design.md); each
  carries a dated note. Evidence:
  [feed standards](../references/research/direction_feed_standards.md).

## Context

- Today the node publishes VSS-named MQTT 5 topics to the Brain (ADR-0026, ADR-0027 §5, the
  module-bus spec), and the Brain pushes a whole snapshot to its UI over SSE `/events`
  (`api/asyncapi.yaml`). Both are our own designs.
- COVESA VISS v3 is the industry's protocol for reading, subscribing to and setting VSS
  signals, with its own transports and access control. We already use the VSS tree
  (ADR-0016).
- ADR-0049 adds a gateway app on each Android device and third-party apps that read the
  same feed. A bespoke protocol on any hop would make each of them learn two.

## Decision drivers

- Follow the industry standard on every signal hop, not a profile beside our own API.
- One access-control model for every app, ours or not.
- Keep the node gate as the only authority over writes.
- Migrate without breaking the node, NodeSource or the UI on the way.

## Decision

1. **VISS v3 on every signal hop.** Node to gateway, node to Brain, Brain to apps and
   gateway to apps all speak VISS v3 (`get`, `set`, `subscribe`, `unsubscribe`, metadata)
   over the VSS tree plus the `Vehicle.Ostler.*` overlay.
2. **VISS's own transports.** WebSocket first (`wss` on the LAN, subprotocol `VISSv3`,
   found by mDNS); gRPC and HTTP where they fit. On Android, apps reach the gateway over a
   loopback WebSocket. On a USB serial link (the head unit, ADR-0039) the same VISS JSON
   messages are framed on the line; the feed spec fixes the framing. The physical choices of
   ADR-0026 (T1S, CAN fallback, Wi-Fi) stand; on CAN the fallback becomes a compact,
   generated mapping of VISS paths.
3. **MQTT is external only.** The gateway app's **External MQTT** menu publishes to an
   outside broker the owner names: Home Assistant discovery, OVMS topics and others (the
   ADR-0017 exports). Nothing inside Ostler depends on MQTT once the migration ends.
4. **Legacy:** the internal MQTT module bus (`api/asyncapi.yaml`, the module-bus spec) and
   the SSE `/events` snapshot are legacy. They keep working until the migration (item 8)
   retires them.
5. **The permissions controller is the VISS access-control front end.**
   - Every app asks the gateway first. On Android it is identified by package name and
     signing key; on the network, by an access request the owner approves. On the Brain,
     its accounts service (ADR-0029 scoped tokens) plays the same role for LAN clients.
   - Per-app toggles map reads to ADR-0029 **data classes** and writes to ADR-0033
     **categories and tiers**.
   - The gateway issues a **VISS access token** scoped to the switched-on toggles. The VISS
     server refuses every path and operation outside it.
   - **Cautious defaults:** a new app gets basic-signal reads only. The owner can revoke
     any app at any time; each app has an access log.
6. **The node gate stays the write authority.** A VISS `set` (on an actuator path or a
   `Vehicle.Ostler.*` action path such as clear faults or an actuator test) is only a
   request. The gateway confirms risky ones on its own screen; the node gate then checks
   tier, category, driving state and grant as today (ADR-0033, the grant format of the
   module-bus spec §10). Tier 4 is impossible regardless. Remote and bridge paths stay
   read-only unless ADR-0033's install override is set; ADR-0044's adapter rules stand.
7. **Cameras and meshes.** Cameras are listed in VISS metadata, each entry pointing to an
   RTSP or WebRTC stream; video never travels inside VISS. Meshtastic and MeshCore are
   transports and bridges for VISS messages (ADR-0038).
8. **Migration outline** (a migration spec gives the detail, spec first):
   - **V0 Spec:** the VISS profile, token format and USB framing in `ostler-feed`, with
     conformance tests.
   - **V1 Brain:** a VISS WebSocket server beside SSE `/events`, fed from the same
     snapshot; the UI moves to a VISS client; `/events` is marked deprecated under the
     changelog policy.
   - **V2 Gateway:** the gateway app serves VISS to apps and speaks VISS to the node.
   - **V3 Node:** the node serves VISS to the Brain; NodeSource moves; the MQTT `vss/`
     topics go legacy. Non-signal bus messages (role claims, grants, power, wake, raw tap,
     lab) move or stay per the migration spec.
   - **V4 Retire:** the internal broker and SSE `/events` are removed after one minor
     release of deprecation. External MQTT stays.

9. **Gateway roles and sync** (owner, 2026-10-08; direction decisions 38–40):
   - **The same job on two hosts.** The Brain's Python service does the gateway job as the
     Android gateway app does: the node link, the VISS server, the permissions controller
     and External MQTT. On the Brain, apps on the network make access requests and the
     settings live in the web console.
   - **Who is the server.** Android straight to a node: the Android gateway app is the
     server. Android to a Brain: the Brain is the server, and the Android gateway app is a
     client that forwards requests from apps on that device.
   - **One server per node.** Only one server owns a node at a time.
   - **One permission set, synced.** The server holds and enforces it. The Android gateway
     apps, the Brain console and the cloud view show and edit the same set: a permission
     turned off on the Android app is off on the Brain, and likewise from the cloud.
   - **Open: failover.** If the Brain drops out mid-drive, whether and how the Android
     gateway takes over the node, and how the permission set is handed over and merged
     back, is open. Ostler Feed spec v0.1 carries it as an open item.

## Confirmation

- `ostler-feed` conformance tests pass against the Brain, the gateway app and the node.
- A token test: a request outside the token's toggles is refused on every transport.
- A write test: a `set` without the toggle never reaches the node; with it, a Tier 2+ set
  waits for the gateway's confirmation and still meets the node gate; Tier 4 is refused.
- During V1–V3 both paths run, and the shared gate vectors pass on both.
- A sync test: a permission turned off on an Android gateway client is refused on the
  Brain server, and the cloud view shows it off.

## Consequences

- ADR-0026 and ADR-0027 keep their transports, security baseline (TLS/mTLS, device
  certificates) and discovery; their MQTT message model becomes legacy.
- The module-bus spec is legacy for vehicle signals once V3 lands; its grant format and
  gate rules carry over.
- `api/asyncapi.yaml` and SSE `/events` gain deprecation under the changelog policy at V1.
- ADR-0017's MQTT row (Home Assistant discovery, OVMS, OwnTracks) is unchanged: these were
  always exports.

## Alternatives considered

- **A VISS profile beside our own API and MQTT bus.** Rejected by the owner: two protocols
  for every developer to learn.
- **MQTT 5 for apps too.** Rejected: not the industry's vehicle-signal protocol; no
  standard access control per signal.
- **A big-bang switch.** Rejected: the node and NodeSource work today; staged migration
  keeps them working.

## Relation to other ADRs

- **ADR-0016:** the VSS tree and overlay stay the names.
- **ADR-0026, ADR-0027:** message model amended; transports and security stand.
- **ADR-0029, ADR-0033:** toggles map to their data classes, categories and tiers.
- **ADR-0037:** role holders stay; how claims are carried is set in the migration spec.
- **ADR-0039:** the USB serial head-unit link carries VISS.
- **ADR-0049, ADR-0050:** the gateway app and the template's VISS client.

## Changelog

- 2026-10-08 — v1.0, accepted: approved by the owner on 2026-10-08 (direction decisions
  4–7, 31–34 and 36).
- 2026-10-08 — v1.1: item 9 added, gateway roles and sync (owner, 2026-10-08): the Brain
  does the same gateway job; Android direct to a node is the server, via a Brain a client;
  one server per node; one synced permission set; Brain failover open.
