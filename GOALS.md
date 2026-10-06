---
title: "Goals — what Ostler is for and where it is going next"
area: root
status: stable
version: 2.0
updated: 2026-10-06
depends_on: [SCOPE.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, references/vision.md]
summary: >
  The short, canonical statement of Ostler's goals: the tagline ("an open, smart-home-like ecosystem for your car; it reads your car's diagnostics and live data, then grows with add-ons"), the mission (a base hardware pack turns the car you already have into a connected IoT platform with diagnostics and telemetry at the core; add-on modules join over IP on an automotive-Ethernet backbone with one VSS-named, MQTT-style message model; Home Assistant and the wider IoT world), the principles, the hard lines and non-goals, what is base and what is add-on, and the near-term vehicle and phase roadmap. The long-term picture is in references/vision.md.
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
car.** A base hardware pack interfaces with the vehicle you already have and turns its
existing systems into a connected IoT platform, with diagnostics and telemetry at the
core. Add-on modules then join over standard networking, the way devices join a smart
home: the alarm/guardian, cameras, relay boxes, sensors and displays. Every device speaks
IP on an automotive-Ethernet backbone (10BASE-T1S for modules, faster Ethernet for
cameras), and they all use the same VSS-named, MQTT-style messages. So modules are
interchangeable, and they integrate with Home Assistant and the wider IoT world.

- **We are making a Home Assistant for cars, not reinventing the wheel.** "Smart-home-like"
  is an analogy, not a claim to be a smart-home product: one open hub that understands many
  vehicles through community-maintained vehicle packs and many devices through one module
  contract, built on open standards and open projects.
- **It runs on hardware you own**, and your data stays with you.
- **Two networks, never mixed.** The car's own buses (K-line, CAN, I/K-Bus, OBD-II) are
  interfaced at the edge by the base pack, never replaced, and nothing on our network
  reaches them except through the platform's safety gate. "Standard networking everywhere"
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
2. **Open standards first** ([ADR-0017](decisions/adr-0017-open-standards-first.md)).
   Prefer an open standard, spec or format over a bespoke one, adopted as files and
   conventions rather than heavy frameworks. COVESA VSS (6.1) is the canonical signal
   namespace, **decided** ([ADR-0016](decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)),
   with OVMS, Home Assistant and OBDb names generated as aliases. Also: OBDb-compatible pack
   data, JSON Schema, OpenAPI/AsyncAPI, MQTT with Home Assistant discovery, OwnTracks,
   Traccar OsmAnd, SocketCAN (listen-only by default,
   [ADR-0020](decisions/adr-0020-can-links-listen-only-by-default.md),
   [ADR-0023](decisions/adr-0023-passive-can-bitrate-detection.md)), ISO 9141-2/14230
   profiles ([ADR-0022](decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md)),
   ISO-TP, REUSE/SPDX, SBOMs, WCAG 2.2 AA.
3. **Safety travels with the action.** One server-side gate serves every path (UI, MQTT,
   Home Assistant, schedules, AI clients). Remote paths get read-only actions only (plus
   arming the software alarm). The UI only adds friction; it never is the gate.
4. **Data honesty.** Every field is `proven` (verified against a car) or `candidate`.
   A missing value is never zero, an unscanned system is never OK, and stale data looks
   stale. Imports never rise above `candidate`.
5. **Three layers, enforced.** Core (comms + interpretation), vehicle packs (declarative
   data + small code hooks), integrations (opt-in consumers and add-ons). The platform
   never imports a pack; import tests enforce it.
6. **Anti-bloat guardrails** ([direction spec](specs/2026-10-06-platform-direction-design.md#guardrails)):
   - *Rule of two:* no new abstraction until a second pack (or device, or vehicle) needs it.
   - *Core only shrinks:* new features land as packs or integrations.
   - *An ADR first* for a new top-level destination, a new outbound data path or a new
     runtime dependency. Five destinations is a hard cap.
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

- **Nothing writes to a car without the gates.** Coding and security writes are listed
  for honesty and never runnable; clears, actuator tests and procedures are confirmed,
  Parked-only and logged. Airbag/SRS is read-only by construction.
- **No blind or spoofed frames.** Probing an unknown K-line car is Parked-only (ADR-0022); no
  CAN frame at an unconfirmed bitrate (ADR-0023); body buses are passive by default and we
  never transmit as a module present in the car (ADR-0024).
- **No EKA, key or immobiliser programming in any default path.** It is gated and opt-in
  only, through the safety gates: the D2 pack keeps EKA read/set behind its gate (the pack's
  ADR-0007). No other SecurityAccess or replayed sniffed write beyond what a module needs for
  diagnostic reads (e.g. the Td5 seed-key unlock) without its own ADR.
- **The VIN is never logged, recorded, put in fixtures or uploaded.** It is decoded in
  memory; only a masked form and a device-local fingerprint are kept. Raw captures are
  never committed.
- **Local-first and private by default.** No cloud dependency; every outbound path is
  opt-in.
- **The alarm is notify-only.** It never actuates the car; it sits alongside the OEM alarm
  and is not a Thatcham-rated product.
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

## 4. Base and add-ons

Ostler is sold and built as a **base pack** plus **add-on modules**, like a smart-home hub
and its devices. Detail: [vision §4](references/vision.md#4-hardware-path) and the
[add-ons catalogue](references/research/addons_catalogue.md).

| | What | Tag |
|---|---|---|
| **Base pack** | A **Linux computer** (Raspberry Pi now, our own board later) and an always-on **ESP32 "buddy"** (wake and Pi power, read-only bus listening while parked, basic notify-only alarm, a small parked MQTT broker, optional 4G; no SIM by default, any uplink works; [ADR-0028](decisions/adr-0028-base-hardware-connectivity-and-remote-access.md)). Vehicle interface (K-line, CAN, OBD-II, ignition and 12 V sense), the network (T1S port, camera Ethernet, Wi-Fi AP, GNSS) and the software: diagnostics, logbook and telemetry, decode pipeline, broker, discovery, the one UI | core |
| **Add-on modules** | The **guardian** (always-on alarm and gateway: own battery, LTE and IoT SIM, tracker, notify-only alarm; may host the parked broker), relay box, sensor and button nodes, gauges, cameras, displays and head unit; then LoRa/Meshtastic, Wi-Fi HaLow, B.A.T.M.A.N. mesh, TPMS, GNSS/RTK, power, trailer, bike modules and anything else that implements the module contract | add-on |
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
| | [ADR-0028](decisions/adr-0028-base-hardware-connectivity-and-remote-access.md) (base hardware, connectivity, remote access) and [ADR-0031](decisions/adr-0031-generic-obd2-pack-in-platform.md) (`generic_obd2` in the platform) locked; [ADR-0029](decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) (accounts, garage, sharing, social) and [ADR-0030](decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md) (AI-native: MCP server, pack-authoring skill) in draft | **Done** / draft |
| | U0 seams: `vid` on sessions, optional VSS `metric` on signals, `vss/` overlay and generated `metrics.json`, JSON Schemas, OpenAPI/AsyncAPI | Next |
| | U1 shell: layout classes, status strip, rail/bottom bar, five destinations, Drive mode | Planned |
| | U2 driving state and server-enforced lockouts; U3 generated capability manifest, Scan all | Planned |
| **1 — Integrations** | Opt-in, read-only MQTT/HA, OVMS topics, OwnTracks, Traccar OsmAnd, ntfy | Planned |
| **2 — Guardian** | Firmware: tracker and notify-only alarm; Security destination (U5: devices, cameras) | Planned |
| **3 — Universal** | `generic_obd2` pack (U4: generated views, local VIN decode, unknown-vehicle banner) | Planned |
| **4 — Add-on modules** | The module-bus message spec and module contract; relay box, sensor/button nodes and head-unit CAN/OBD emulator on the module bus (T1S; CAN as fallback) | Planned |
| **U6 / U7** | Garage with a second real vehicle; decode evidence, fixtures, scrub CI, OBDb import/export, Decode mode | Waits on a second vehicle / may move earlier |
| **Moonshots** | Remote OEM disarm, remote start, ODX import (user-owned files only), cloud fleet, Web Bluetooth, CAN intrusion check, our own ROM or display hardware | Each needs its own ADR and gate |

## Where the detail lives

- Long term: [vision](references/vision.md), [add-ons catalogue](references/research/addons_catalogue.md).
- Direction: [platform direction](specs/2026-10-06-platform-direction-design.md),
  [UI architecture](specs/2026-10-06-ui-architecture-design.md); decisions in
  [decisions/](decisions/CLAUDE.md); research in [references/research/](references/research/platform.md)
  ([landscape](references/research/landscape.md), [hardware](references/research/hardware.md),
  [feature backlog](references/research/features_backlog.md)).
- Rules and scope: [CONSTITUTION.md](CONSTITUTION.md), [SCOPE.md](SCOPE.md),
  [TRADEMARKS.md](TRADEMARKS.md).

## Changelog

- 2026-10-06: v2.0, split in two. New tagline and the owner's mission paragraph; the base
  pack is a Linux computer plus an ESP32 buddy and the guardian is an add-on; principle 9
  (standalone modules). Gaps, peers, audience, pillars, hardware path, repo map, business
  model, success measures and open questions moved to [vision](references/vision.md).
  Hard lines unchanged, now §3 (were §10).
- 2026-10-06: v1.4, smart-home-like framing and tagline; pillars regrouped into base pack,
  add-ons, networking and integrations; Phase 4 becomes add-on modules (ADR-0026, ADR-0027).
