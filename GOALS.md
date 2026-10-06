---
title: "Goals — what Ostler is for and where it is going next"
area: root
status: stable
version: 2.2
updated: 2026-10-06
depends_on: [SCOPE.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, references/vision.md]
summary: >
  The short, canonical statement of Ostler's goals: the tagline ("an open, smart-home-like ecosystem for your car; it reads your car's diagnostics and live data, then grows with add-ons"), the mission and product family (Ostler Diagnostics, a diagnostic node that works alone and offline with a phone; Ostler Hub, the brain it plugs into; Ostler Guardian, the hidden node variant; add-on modules on either, joining over IP with one VSS-named, MQTT-style message model; Home Assistant and the wider IoT world), the principles (the node gate is the only path to the car), the hard lines and non-goals, the product line table (Ostler Diagnostics, Ostler Hub, Ostler Guardian, sensor nodes, add-on modules), and the near-term vehicle and phase roadmap. The long-term picture is in references/vision.md.
---

# Goals

What Ostler is for and what comes next. The long term is in
**[references/vision.md](references/vision.md)**; the detail is in the
[direction spec](specs/2026-10-06-platform-direction-design.md) (draft), the
[UI spec](specs/2026-10-06-ui-architecture-design.md) (approved, ADR-0018), the
[ADRs](decisions/CLAUDE.md) and the [research](references/research/platform.md). Where they
disagree with this file, they win. The hard rules are in [CONSTITUTION.md](CONSTITUTION.md).

## 1. Tagline and mission

> **Ostler: an open, smart-home-like ecosystem for your car. It reads your car's
> diagnostics and live data, then grows with add-ons.**

**Ostler is an open, local-first automotive ecosystem: a smart-home-like platform for your
car.** A diagnostic **node** interfaces with the vehicle you already have and turns its
systems into a connected IoT platform, with diagnostics and telemetry at the core
([ADR-0032](decisions/adr-0032-one-node-optional-brain.md),
[ADR-0039](decisions/adr-0039-product-family-diagnostics-guardian-hub.md); "node" and
"brain" stay the internal terms). **Ostler Diagnostics** is the node at the OBD port
(optional 4G): tracking, alarm basics, live data and faults through the phone app or Ostler
Cloud; it works fully offline with a phone and is never cloud-only. **Ostler Diagnostics +
Hub** adds **Ostler Hub**, the brain (a Linux computer): the full local app, add-on
routing, cameras, big logbooks, replay, analysis and the decode lab; upgrading is plugging
in a hub, and the car side is unchanged. **Ostler Guardian** is the hidden node variant. Add-on
modules join either tier the way devices join a smart home: cameras, sensor nodes, I/O
and relay modules, displays. Every device speaks IP (10BASE-T1S for modules, faster
Ethernet for cameras) and the same VSS-named, MQTT-style messages, so modules are
interchangeable and integrate with Home Assistant and the wider IoT world.

- **We are making a Home Assistant for cars, not reinventing the wheel.** "Smart-home-like"
  is an analogy, not a claim to be a smart-home product: one open hub that understands many
  vehicles through community-maintained vehicle packs and many devices through one module
  contract, built on open standards and open projects.
- **It runs on hardware you own**, and your data stays with you.
- **Two networks, never mixed.** The car's own buses (K-line, CAN, I/K-Bus, OBD-II) are
  interfaced at the edge by the node, never replaced, and nothing on our network reaches
  them except through the node's transmit gate. "Standard networking everywhere"
  applies to *our* ecosystem. Displays use Wi-Fi or USB.
- **The core mission stays narrow** ([SCOPE.md](SCOPE.md)): communication with the car and
  interpretation of its data. Everything else, add-on modules included, builds on that.
- It starts with the **Land Rover Discovery 2 Td5**, which talks K-line rather than CAN,
  and grows to any car.

Architecture: [ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md) on
[ADR-0026](decisions/adr-0026-module-bus-10base-t1s.md), researched in
[ecosystem_architecture.md](references/research/ecosystem_architecture.md). The gaps Ostler
fills and its peers: [vision §1](references/vision.md#1-why-ostler-exists).

## 2. Principles

1. **Local-first and private by default.** Everything works with no cloud. Location and
   audio stay on the device unless the owner opts in (ADR-0009, ADR-0010). Every outbound
   path is opt-in and off by default. Cloud APIs die, so we never depend on one.
2. **Open standards first** ([ADR-0017](decisions/adr-0017-open-standards-first.md)),
   adopted as files and conventions rather than heavy frameworks. COVESA VSS (6.1) is the
   canonical signal namespace ([ADR-0016](decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)),
   with OVMS, Home Assistant and OBDb names as aliases. Also: OBDb-compatible pack data,
   JSON Schema, OpenAPI/AsyncAPI, MQTT with HA discovery, OwnTracks, Traccar OsmAnd,
   SocketCAN (listen-only by default, [ADR-0020](decisions/adr-0020-can-links-listen-only-by-default.md),
   [ADR-0023](decisions/adr-0023-passive-can-bitrate-detection.md)), ISO 9141-2/14230
   profiles ([ADR-0022](decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md)), ISO-TP, REUSE/SPDX, SBOMs, WCAG 2.2 AA.
3. **Safety travels with the action; the node gate is the only path to the car**
   (ADR-0032). Every path (UI, phone, MQTT, Home Assistant, schedules, AI clients) ends at
   the node's transmit gate, which verifies grants a brain or phone mints. Phone approval
   of Tier 2–3 works over local links only; remote paths are read-only unless the
   install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is set (off by default, never set
   remotely; [ADR-0033](decisions/adr-0033-action-categories-and-approvals.md)). The UI
   only adds friction; it never is the gate.
4. **Data honesty.** Every field is `proven` (verified against a car) or `candidate`.
   A missing value is never zero, an unscanned system is never OK, and stale data looks
   stale. Imports never rise above `candidate`.
5. **Three layers, enforced.** Core (comms + interpretation), vehicle packs (declarative
   data + small code hooks), integrations (opt-in consumers and add-ons). The platform
   never imports a pack; import tests enforce it.
6. **Anti-bloat guardrails** ([direction spec](specs/2026-10-06-platform-direction-design.md#guardrails)):
   - *Rule of two:* no new abstraction until a second pack (or device, or vehicle) needs it.
   - *Core only shrinks:* new features land as packs or integrations.
   - *An ADR first* for a new top-level destination, a new outbound data path, a new
     runtime dependency or a new language
     ([ADR-0035](decisions/adr-0035-languages-by-tier.md)). Five destinations is a hard cap.
   - *The D2 pack's coverage is protected:* CI fails if it regresses.
   - Every idea is tagged **core**, **add-on** or **moonshot**
     ([feature backlog](references/research/features_backlog.md)); add-ons are off by
     default, moonshots each need their own ADR and gate.
7. **Off-the-shelf hardware now, our own later**, behind hardware-abstraction layers.
8. **IP everywhere, one message model** ([ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)).
   Every Ostler device is an IP host. It is found by mDNS/DNS-SD, speaks VSS-named MQTT 5,
   and declares its signals and safety-tiered actions in one module manifest. Firmware and
   server code name topics, never physical layers. The car's buses stay at the edge.
9. **Every module stands on its own.** Like an IP camera or an ESP32 project, each module
   hosts a small web page with its basic controls and works independently; joined to
   Ostler, it appears in the main UI and in Home Assistant.

## 3. Non-goals and hard lines

**Hard lines** (also in [CONSTITUTION.md](CONSTITUTION.md) and the UI spec §7):

- **Nothing writes to a car without the node gate.** Coding and security writes are listed
  for honesty and never runnable; actuator tests and procedures are confirmed, Parked-only
  and logged; clearing codes means snapshot first, parked or idling, one confirmation, an
  extra warning for safety systems, audited (ADR-0033). An accept inside an AI client
  never counts. Airbag/SRS is read-only by construction.
- **No blind or spoofed frames.** Probing an unknown K-line car is Parked-only (ADR-0022); no
  CAN frame at an unconfirmed bitrate (ADR-0023); body buses are passive by default and we
  never transmit as a module present in the car (ADR-0024).
- **No EKA, key or immobiliser programming in any default path.** It is gated and opt-in
  only, through the safety gates: the D2 pack keeps EKA read/set behind its gate (the pack's
  ADR-0007). No other SecurityAccess or replayed sniffed write beyond what a module needs for
  diagnostic reads (e.g. the Td5 seed-key unlock) without its own ADR.
- **VIN and identity data are never recorded by default and never leave the device**
  ([ADR-0036](decisions/adr-0036-vin-and-identity-data-in-recordings.md)): recording is an
  opt-in for security decoding; never uploaded, shared, contributed, put in fixtures or
  committed. Raw captures are never committed.
- **Local-first and private by default.** No cloud dependency; every outbound path is
  opt-in.
- **Alarm paths never depend on the brain or the internet** (tested). Not Thatcham-rated;
  alarm outputs (siren, native alarm, immobiliser) come only through a future I/O / relay
  module with an ADR per car-switching function (ADR-0033; no notify-only line).
- **No converted dealer databases** (the OpenVehicleDiag DMCA lesson), no non-commercial,
  unlicensed or GPL-2.0-only code, and no copied fault-code descriptions (ADR-0025).
- **No vehicle maker's marks in our brand.**

**Non-goals:**

- Rebuilding media: CarPlay/Android Auto, radio, amplifier and wheel controls stay on a
  media head unit.
- HEVAC control inside the platform (a separate project).
- A remote layout server, runtime- or model-composed screens, or user-arranged dashboards
  (maybe later, as a diff over the generated views).
- Features without a spec, or add-ons that are on by default.

## 4. Product line and add-ons

Ostler is sold and built as a **node** (Ostler Diagnostics) or **node + brain** (Ostler
Diagnostics + Hub), plus **add-on modules** on either, like a smart-home hub and its devices. Detail:
[vision §4](references/vision.md#4-hardware-path), the
[add-ons catalogue](references/research/addons_catalogue.md) and
[ADR-0032](decisions/adr-0032-one-node-optional-brain.md) and
[ADR-0039](decisions/adr-0039-product-family-diagnostics-guardian-hub.md) (names).

| | What | Tag |
|---|---|---|
| **Ostler Diagnostics** | The ESP32 diagnostic **node** at the OBD port: K-line/CAN I/O, decoding to VSS, the transmit gate, GPS, optional 4G (a fitted module or a USB dongle; each device may have its own IoT SIM), a parked MQTT broker, basic alarm, its own web page; the phone app (PWA in a native wrapper) over BLE or the node's Wi-Fi AP, or Ostler Cloud | core |
| **Ostler Hub** | The **brain** (Raspberry Pi now, our own board later) that the node powers and wakes (linked by USB or T1S): the full local app, add-on routing, cameras, big logbooks, replay, analysis, the decode lab | core |
| **Ostler Guardian** | The same node firmware on security hardware: backup battery, tamper sensing, IMU, better antennas, GPS, optional 4G. Fitted hidden; **no outputs** | core variant |
| **Sensor nodes** | Fast tacho, EGT, boost/oil pressure and temperature, wideband AFR, extra accelerometers; read-only, isolated taps; readings are source-tagged VSS signals | add-on |
| **Add-on modules** | Cameras, buttons, gauges, displays and head unit, a future **I/O / relay module** (alarm outputs and switching, an ADR per car-switching function); then LoRa/Meshtastic, Wi-Fi HaLow, mesh, TPMS, GNSS/RTK, power, trailer and anything that implements the module contract | add-on |
| **Integrations** | Opt-in MQTT with Home Assistant discovery, OVMS topics, OwnTracks, Traccar, ntfy; Matter through a bridge later; community data with OBDb | add-on / core |

**One UI for every vehicle**, generated from capability manifests, with a garage
([UI spec](specs/2026-10-06-ui-architecture-design.md), [vision §3](references/vision.md#3-product-pillars)).
HEVAC is the owner's separate ESP32 project; Ostler only talks to it as an add-on device.

## 5. Near-term roadmap

**Vehicles:**

| Step | Vehicles | How |
|---|---|---|
| 1 | **Land Rover Discovery 2 Td5** (reference pack) | K-line, KWP2000, seed-key, six modules; [discovery2-diag](https://github.com/JamesWrightDavid/discovery2-diag) |
| 2 | **Other Land Rover and Rover** | e.g. P38, classic Range Rover / Rover V8 (14CUX, MEMS via libcomm14cux/librosco), Discovery 3/4 in collaboration with jlr-scanner |
| 3 | **Any OBD-II car** | the `generic_obd2` pack (ELM327 / SocketCAN, OBDb SAEJ1979 data), selected when no pack matches; proves the platform is universal |
| 4 | **Modern CAN / UDS** | ISO-TP, UDS `22`/`19`, passive CAN via DBC; systems grouped by domain when there are more than twelve |
| 5 | **Pre-OBD and older cars** | manual selection or K-line probes, packs built through the decode pipeline |

Order beyond step 3 is indicative, not committed. Each new pack gets its own spec.

**Phases:** direction phases 0–4 ([spec](specs/2026-10-06-platform-direction-design.md#phases)) and
UI phases U0–U7 ([UI spec §10](specs/2026-10-06-ui-architecture-design.md#10-phased-migration))
combined: U0–U3 in Phase 0, U5 in Phase 2, U4 in Phase 3. Each step gets its own spec.

| Phase | Scope | Status |
|---|---|---|
| **0 — Decouple** | `VehiclePack` contract, D2 behind it, layering tests ([Phase 0 spec](specs/2026-10-06-phase0-vehiclepack-decoupling-design.md)); repo split into platform `openostler` + pack `d2diag`, history kept ([ADR-0015](decisions/adr-0015-repo-split-executed.md)); homelab dev server (Docker/Dokploy, platform + pack at `PACK_REF`); version tracker (`GET /version`, Settings → Version) | **Done** |
| | Research and decisions: UI (seven notes, UI spec approved, ADR-0018, [research](references/research/ui/)); standards, CAN/head-unit, OVMS reuse (ADR-0016 to ADR-0021); muki01 K-line, CAN, BMW I/K-Bus, diagnostic UI (ADR-0022 to ADR-0025, [synthesis](references/research/muki01/README.md)); [T1S](references/research/t1s_module_bus.md) (ADR-0026) and [ecosystem](references/research/ecosystem_architecture.md) (ADR-0027) | **Done** |
| | [ADR-0028](decisions/adr-0028-base-hardware-connectivity-and-remote-access.md) (connectivity, remote access), [ADR-0031](decisions/adr-0031-generic-obd2-pack-in-platform.md) (`generic_obd2` in the platform), [ADR-0029](decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) (accounts, garage, sharing, social) and [ADR-0030](decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md) (MCP server, pack-authoring skill) accepted; ADR-0032 to ADR-0036 (node/brain, action categories, repo boundaries, languages, VIN data) | **Done** |
| | U0 seams: `vid` on sessions, optional VSS `metric` on signals, `vss/` overlay and generated `metrics.json`, JSON Schemas, OpenAPI/AsyncAPI | Next |
| | U1 shell: layout classes, status strip, rail/bottom bar, five destinations, Drive mode | Planned |
| | U2 driving state and server-enforced lockouts; U3 generated capability manifest, Scan all | Planned |
| **1 — Integrations** | Opt-in, read-only MQTT/HA, OVMS topics, OwnTracks, Traccar OsmAnd, ntfy | Planned |
| **2 — Node firmware** | One firmware, all variants (diagnostic node, guardian): C decoder from pack JSON, transmit gate, tracker and alarm basics, capability manifest; Security destination (U5: devices, cameras) | Planned |
| **3 — Universal** | `generic_obd2` pack (U4: generated views, local VIN decode, unknown-vehicle banner) | Planned |
| **4 — Add-on modules** | The module-bus message spec and module contract; I/O / relay module, sensor/button nodes and head-unit CAN/OBD emulator on the module bus (T1S; CAN as fallback) | Planned |
| **U6 / U7** | Garage with a second real vehicle; decode evidence, fixtures, scrub CI, OBDb import/export, Decode mode | Waits on a second vehicle / may move earlier |
| **Moonshots** | Remote OEM disarm, remote start, ODX import (user-owned files only), cloud fleet, CAN intrusion check, our own ROM or display hardware | Each needs its own ADR and gate |

## Where the detail lives

- Long term: [vision](references/vision.md), [add-ons catalogue](references/research/addons_catalogue.md).
- Direction: [platform direction](specs/2026-10-06-platform-direction-design.md), [UI architecture](specs/2026-10-06-ui-architecture-design.md), [decisions/](decisions/CLAUDE.md); research in [references/research/](references/research/platform.md) ([landscape](references/research/landscape.md), [hardware](references/research/hardware.md), [feature backlog](references/research/features_backlog.md)).
- Rules and scope: [CONSTITUTION.md](CONSTITUTION.md), [SCOPE.md](SCOPE.md), [TRADEMARKS.md](TRADEMARKS.md).

## Changelog

- 2026-10-06: v2.2, product family renamed (ADR-0039): Ostler Diagnostics (was Ostler Lite),
  Ostler Hub (the brain; was "Ostler (full)") and Ostler Guardian; the §4 table and the
  mission paragraph follow.

- 2026-10-06: v2.1, node/brain direction (ADR-0032 to ADR-0036): Ostler Lite and Ostler
  product line; new §4 table; node gate and ADR-0033 remote rule in principle 3; hard
  lines (notify-only removed, clear codes, VIN); ADR-0035 in the ADR-first rule; Phase 2
  node firmware; ADR-0029/0030 accepted; Web Bluetooth off the moonshot list.

- 2026-10-06: v2.0, split in two. New tagline and the owner's mission paragraph; the base
  pack is a Linux computer plus an ESP32 buddy and the guardian is an add-on; principle 9
  (standalone modules). Gaps, peers, audience, pillars, hardware path, repo map, business
  model, success measures and open questions moved to [vision](references/vision.md).
  Hard lines unchanged, now §3 (were §10).
- 2026-10-06: v1.4, smart-home-like framing and tagline; pillars regrouped into base pack,
  add-ons, networking and integrations; Phase 4 becomes add-on modules (ADR-0026, ADR-0027).
