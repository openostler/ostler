---
title: "Goals — what Ostler is for and where it is going"
area: root
status: stable
version: 1.4
updated: 2026-10-06
depends_on: [SCOPE.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md]
summary: >
  The canonical statement of Ostler's full goals: an open, local-first, smart-home-like automotive ecosystem. A base hardware pack interfaces with the car you already have (diagnostics and telemetry at the core); add-on modules (guardian alarm and tracker, cameras, relay boxes, sensors, displays) join over standard IP networking on an automotive-Ethernet backbone with one VSS/MQTT message model, and the car integrates with Home Assistant and the wider IoT world. Starts with the Land Rover Discovery 2 and grows to any car. Covers mission, principles, audience, pillars, vehicle and hardware roadmaps, repo map, business model, phases, hard lines, success measures and open questions.
---

# Goals

This is the one place that says what Ostler is for and where it is going. The detail lives
in the [direction spec](specs/2026-10-06-platform-direction-design.md) and the
[UI architecture spec](specs/2026-10-06-ui-architecture-design.md) (the direction spec is a
**draft**; the UI spec is **approved**, ADR-0018), the ADRs in [decisions/](decisions/CLAUDE.md) and the research in
[references/research/](references/research/platform.md). Where this file and those
disagree, they win; fix this file. The hard rules are in [CONSTITUTION.md](CONSTITUTION.md).

## 1. Mission and positioning

> **Ostler: an open, smart-home-like ecosystem for your car. It connects the car you
> already have, then lets you add on.**

**Ostler is an open, local-first automotive ecosystem: a smart-home-like platform for the
car you already have.**
- **A base hardware pack** connects to the vehicle's own wiring and buses, alongside them
  and never in their place. It makes the car's existing systems connected, with
  **diagnostics and telemetry at the core**.
- **Add-on modules** then join over standard networking, the way devices join a smart home:
  the guardian (alarm and tracker), cameras, relay boxes, sensors, buttons and displays.
- **Every Ostler device speaks IP** on an automotive-Ethernet backbone: 10BASE-T1S for
  modules, faster Ethernet for cameras, Wi-Fi or USB for screens.
- **They share one message model**: VSS-named MQTT messages, found by standard discovery.
  So modules are interchangeable, third parties can build them, and the car integrates with
  Home Assistant and the wider IoT world.
- **It runs on hardware you own**, and your data stays with you.

"Smart-home-like" is an analogy, not a claim to be a smart-home product. In smart-home
terms, the comparison is *the Home Assistant of the automotive world*: one open hub that
understands many vehicles through community-maintained definitions (vehicle packs) and
many devices through one module contract. The architecture is
[ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md), which builds on
[ADR-0026](decisions/adr-0026-module-bus-10base-t1s.md); the research is in
[ecosystem_architecture.md](references/research/ecosystem_architecture.md).

**Two networks, never mixed.**
- **The car's own buses** (K-line, CAN, I/K-Bus, OBD-II) are interfaced at the edge by the
  base pack. They are never replaced, and nothing on our network reaches them except
  through the platform's safety gate.
- **"Standard networking everywhere"** applies to *our* ecosystem.

It starts with the Land Rover Discovery 2 Td5, which talks K-line rather than CAN, and
grows from there. The core mission stays narrow ([SCOPE.md](SCOPE.md)):
**communication with the car and interpretation of its data.** Everything else, add-on
modules included, builds on that.

**The gaps nobody owns** ([landscape](references/research/landscape.md#gaps-nobody-owns-and-that-suit-us)),
which are why Ostler exists:

1. K-line-first open vehicle definitions (KWP2000, ISO 9141, Td5, DS2, KW1281), with init
   sequences, seed-key handling and test vectors. OBDb, opendbc and WiCAN all assume CAN.
2. Open diagnostics for Land Rover pre-CAN body systems (SLABS, BeCM, EAT, HEVAC). The
   NanoCom-class tools are closed.
3. An open ICE / K-line telematics node: tracker, alarm, logger and diagnostics in one box.
   OVMS covers EVs on CAN.
4. An open car alarm / security module with Home Assistant alerts and camera triggers.
5. A PWA-first car UI with live data, replay and maps. Everything else is Qt or Android.
6. One log format and exporter (MoTeC .ld, RaceChrono, VBO, RealDash) with synced audio
   and IMU.
7. A documented, permissively licensed head-unit CAN-box protocol.
8. An open, IP-based add-on ecosystem for cars: modules from anyone, one contract, no
   certification gate.

**Peers we interoperate with rather than replace:** OVMS (we speak its MQTT topic tree),
OBDb (we share CC BY-SA signal data), OwnTracks and Traccar (location), Home Assistant,
jlr-scanner (Discovery 3/4), WiCAN (hardware front end). See [ovms.md](references/research/ovms.md).
We also **reuse their data** ([ADR-0019](decisions/adr-0019-reuse-from-ovms-and-obdb.md)): OBDb is
the primary source for polled signals, and every OVMS vehicle and command is imported where the
licence allows, with commands disabled behind the safety gates and a human review gate on the
importer. Reuse is pragmatic ([ADR-0025](decisions/adr-0025-reuse-and-licences-pragmatic.md)):
any idea may be reimplemented; GPL-3 code goes only into marked GPL-3 modules or packs.

## 2. Principles

1. **Local-first and private by default.** Everything works with no cloud. Location and
   audio stay on the device unless the owner opts in (ADR-0009, ADR-0010). Every outbound
   path is opt-in and off by default. Cloud APIs die, so we never depend on one.
2. **Open standards first** ([ADR-0017](decisions/adr-0017-open-standards-first.md)).
   Prefer an open standard, spec or format over a bespoke one, adopted as files and
   conventions rather than heavy frameworks. COVESA VSS (6.1) is the canonical signal
   namespace, **decided** ([ADR-0016](decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)),
   with OVMS, Home Assistant and OBDb names generated as aliases. OBDb-compatible pack data,
   JSON Schema, OpenAPI/AsyncAPI, MQTT with Home Assistant discovery, OwnTracks, Traccar
   OsmAnd, SocketCAN (listen-only by default, [ADR-0020](decisions/adr-0020-can-links-listen-only-by-default.md),
   [ADR-0023](decisions/adr-0023-passive-can-bitrate-detection.md)), ISO 9141-2/14230 profiles ([ADR-0022](decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md)), ISO-TP, REUSE/SPDX, SBOMs, WCAG 2.2 AA.
3. **Safety travels with the action.** One server-side gate serves every path (UI, MQTT,
   Home Assistant, schedules). Remote paths get read-only actions only (plus arming the
   software alarm). The UI only adds friction; it never is the gate.
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

## 3. Who it is for

- **Owners of older vehicles** that modern apps ignore, starting with K-line Land Rovers,
  who want dealer-level insight from a cheap cable and a Raspberry Pi.
- **Home Assistant and self-hosting people** who want their car as a first-class device:
  sensors, location, alarm events and notifications on their own server.
- **DIY mechanics** who need honest fault reads, live data and guarded actuator tests.
- **Overlanders and enthusiasts** who log drives, track off-grid and add their own
  modules (relays, cameras, gauges).
- **Decoders and contributors** who reverse-engineer vehicles and want a pipeline that
  turns captures into verified, shareable packs.
- **Module makers** who want to build add-ons (sensors, relays, displays) against an open
  contract and have them work with every Ostler car.
- **Companies** that want the code under a commercial licence, and **customers** of
  official Ostler hardware and Ostler Cloud.

## 4. Product pillars

The pillars group into four parts: the **base hardware pack** (diagnostics and telemetry
core), **add-on modules**, **standard networking**, and **integrations**.

| Part | Pillar | Goal | Tag | Status |
|---|---|---|---|---|
| **Base pack** | **Vehicle interface** | Front ends for the car's own buses (K-line, CAN, OBD-II, body buses), receive-first and gated (ADR-0020, ADR-0022, ADR-0024); one `VehiclePack` per vehicle | core | K-line on the D2 working; CAN/OBD-II planned |
| **Base pack** | **Diagnostics** | Per vehicle → systems → function areas (Faults · Live · Tests · Procedures · Settings), a whole-car **Scan all** with honest states and a saved report, five safety tiers | core | D2 working on K-line; generic OBD-II and CAN/UDS planned |
| **Base pack** | **Logging and telemetry** | Session logbook with replay, GPS and place names, notes, audio, IMU, flags; CSV, VBO and GPX export; the car's signals published live as VSS-named telemetry; later log formats (MoTeC, AiM, RaceChrono, RealDash) and lap timing | core / add-on | Logbook, replay and exports shipped; live MQTT, formats and lap timing planned |
| **Base pack** | **Decode pipeline** | A read-only path from any unknown car to a pack with verified signals: connect → identify → inventory → baseline → capture → correlate → label → verify → package → contribute; a Decode mode in the app | core (developer) | Sniff, automap and catalog exist; pipeline is UI phase U7 |
| **Add-on modules** | **Guardian: tracker and alarm** | An always-on ESP32 guardian with its own battery and IoT SIM: tracker, geofences, a **notify-only** alarm (strong/weak triggers, tamper), notifications escalating HA → ntfy → Telegram → SMS; the module bus's always-on coordinator | add-on | Designed (Phase 2); not built |
| **Add-on modules** | **Relays, sensors, buttons, gauges** | Modules on the module bus: relay box (each channel tiered, Parked-only, never remote), sensor and button nodes, gauge display, head-unit CAN/OBD emulator; HEVAC (the owner's separate project) joins through the same contract | add-on | Phase 4; not built |
| **Add-on modules** | **Cameras** | One camera system for dashcam, parking/alarm clips, reversing and underbody: standard ONVIF/RTSP IP cameras on the camera segment, streamed through go2rtc (optionally Frigate) into the same timeline. **Future:** our own cameras (100BASE-T1) and 360° surround view (ADR-0018) | add-on | Designed; constraints open (§12) |
| **Add-on modules** | **Displays / head unit** | Displays are thin clients: the PWA on any screen, **head-unit first**, then an Ostler Android launcher, then possibly our own ROM or display hardware | core / add-on | PWA shipped (phone-first today); head-unit layout is UI phase U1 |
| **Standard networking** | **IP backbone** | Every device speaks IP: **10BASE-T1S** for modules, standard Ethernet (12 V or PoE) for cameras now and 100BASE-T1 for our own cameras later, Wi-Fi/USB for displays; the Pi routes and firewalls between segments; CAN and a wake wire as the dev-kit and µA-wake fallback ([ADR-0026](decisions/adr-0026-module-bus-10base-t1s.md), [ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)) | core | Decided; T1S bench planned ([bench plan](references/t1s_bench_plan.md)) |
| **Standard networking** | **Discovery, messages, security** | mDNS/DNS-SD zero-config; MQTT 5 with a VSS topic tree; NTP from GNSS; per-node identity, mTLS and authenticated commands; no default passwords | core | Decided; module-bus message spec next |
| **Standard networking** | **Module contract** | One module manifest (identity, VSS signals, safety-tiered actions, events, UI slots, OTA) so modules are interchangeable and third-party modules are possible; DevicePack adapters for foreign devices; a conformance kit | core | Designed (ADR-0027, UI spec §6); spec with the module-bus message spec |
| **Integrations** | **Home Assistant and the IoT world** | Opt-in MQTT with Home Assistant device discovery, an OVMS v3-compatible topic tree, OwnTracks, Traccar OsmAnd, ntfy; Matter ecosystems reached through a bridge (read-only), never inside modules | add-on | Phase 1; not built |
| **Integrations** | **Community data** | Packs as CC BY-SA data, OBDb-compatible, with evidence and fixtures; opt-in anonymous contribution; upstreaming to OBDb | core | D2 data is CC BY-SA; evidence/fixtures planned |

**One UI for every vehicle** ties the pillars together: the UI is generated from a
per-vehicle **capability manifest** (systems, signals with VSS paths, DTC sources,
safety-tiered actions, devices, views), with five destinations
(`Home · Diagnose · Logs · Security/Map · More`), Drive as a full-screen mode,
Parked/Idling/Moving lockouts enforced by the server, and a **garage** for more than one
vehicle. Screens never test a vehicle type ([UI spec](specs/2026-10-06-ui-architecture-design.md)).

**HEVAC (climate control)** is a separate ESP32 project owned by the owner. Ostler only
talks to it, as an add-on device; it is not part of this platform.

## 5. Vehicle roadmap

| Step | Vehicles | How |
|---|---|---|
| 1 | **Land Rover Discovery 2 Td5** (reference pack) | K-line, KWP2000, seed-key, six modules; [discovery2-diag](https://github.com/JamesWrightDavid/discovery2-diag) |
| 2 | **Other Land Rover and Rover** | e.g. P38, classic Range Rover / Rover V8 (14CUX, MEMS via libcomm14cux/librosco), Discovery 3/4 in collaboration with jlr-scanner |
| 3 | **Any OBD-II car** | the `generic_obd2` pack (ELM327 / SocketCAN, OBDb SAEJ1979 data), selected when no pack matches; proves the platform is universal |
| 4 | **Modern CAN / UDS** | ISO-TP, UDS `22`/`19`, passive CAN via DBC; systems grouped by domain when there are more than twelve |
| 5 | **Pre-OBD and older cars** | manual selection or K-line probes, packs built through the decode pipeline |

Order beyond step 3 is indicative, not committed. Each new pack gets its own spec.

## 6. Hardware path

Ostler hardware is sold as a **base pack** plus **add-on modules**, like a smart-home hub
and its devices ([ecosystem research §3](references/research/ecosystem_architecture.md#3-product-taxonomy-and-the-module-contract)).

- **Base hardware pack** (the core product): the Linux brain; the **vehicle interface**
  (K-line, CAN and OBD-II front ends, ignition and 12 V sense); the **network** (a T1S port,
  the PLCA coordinator while awake; an Ethernet port for cameras; a Wi-Fi access point for
  displays; GNSS for time and logging); and the software (diagnostics, logbook and
  telemetry, broker, discovery, a local CA).
- **Add-on modules:** guardian (alarm and tracker), relay box, sensor and button nodes,
  gauge display, cameras and displays; third-party modules through the module contract.
- **Network** ([ADR-0026](decisions/adr-0026-module-bus-10base-t1s.md),
  [ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)): **10BASE-T1S** for
  modules (4-wire harness: 12 V, ground, the T1S pair, optional wake wire); standard
  Ethernet with 12 V or PoE for cameras; Wi-Fi/USB for displays; the Pi routes between
  segments. CAN stays for dev kits and µA-wake nodes until T1S wake is proven
  ([bench plan](references/t1s_bench_plan.md)).
- **Now — development kit, no custom PCBs** ([hardware research](references/research/hardware.md)):
  Raspberry Pi 5 with a CarPiHAT PRO 5, powered on demand; an ESP32-S3 LTE/GNSS **guardian**
  (e.g. LilyGO T-SIM7670G-S3) on its own 18650 with an IoT SIM; a 10 Hz u-blox; the KKL
  cable; WiCAN Pro as a later OBD front end; ESP32-S3 boards with a LAN8651 Click for T1S
  modules (Waveshare and Autosport Labs ESP32 boards for CAN fallback); off-the-shelf
  ONVIF/RTSP IP cameras behind a small switch. Target parked draw: about 1–4 mA
  (unverified).
- **Later — our own boards** for hardware sales, once the software settles: a base-pack
  board (CM5 or NXP i.MX93, CAN and K-line transceivers, a LAN8651, an ignition/opto front
  end, the camera Ethernet port), a guardian board (ESP32-S3, SIM7670, cell charger), T1S
  module boards, and possibly our own 100BASE-T1 cameras with a LAN937x-class switch.
  Firmware and drivers carry over through the hardware-abstraction layers. Fallbacks, not
  plans: AutoPi-class closed boxes.

## 7. Repo and product map

| Repo / product | Visibility, licence | Role |
|---|---|---|
| [`openostler/ostler`](https://github.com/openostler/ostler) (this repo) | public; AGPL + commercial | Platform: comms core, `VehiclePack` contract, logbook/replay, integrations, web server, **the main UI** |
| [`discovery2-diag`](https://github.com/JamesWrightDavid/discovery2-diag) (`d2diag`) | public; AGPL code + CC BY-SA data | Ostler pack for Land Rover Discovery 2: the reference pack and conformance fixture |
| `openostler/ostler-firmware` | public; AGPL | ESP32 guardian, add-on modules, shared HAL, the module-bus protocol and module contract (created when that work starts) |
| `openostler/ostler-cloud` | **private, closed** | Ostler Cloud; speaks only a documented MQTT/HTTPS protocol and never imports platform code |
| `ostler-hardware`, `ostler-android` | later; hardware CERN-OHL-S | Our own board designs (base pack, guardian, modules); the Ostler Android launcher |
| HEVAC | owner's separate project | Not part of the platform |

Brand split ([ADR-0014](decisions/adr-0014-ostler-handles.md)): **Ostler** is the product
family (Ostler Cloud, Ostler Guardian, Ostler Node); **OpenOstler** is the open code and
community. Packs are "Ostler pack *for* <vehicle>"; vehicle makers' marks are never part
of our brand ([TRADEMARKS.md](TRADEMARKS.md)).

## 8. Business model and licensing

- **Funding:** official hardware sales (the base pack and add-on modules), a closed-source **Ostler Cloud** subscription
  (hosted sync, fleet, remote access), and a **commercial licence** for closed or embedded
  use ([ADR-0012](decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md),
  [ADR-0013](decisions/adr-0013-repo-split-and-vehicle-pack-contract.md)).
- **Code:** AGPL-3.0-or-later, so hosted modified copies must share source.
- **Vehicle data:** CC BY-SA 4.0, the same as OBDb, so packs can flow both ways.
- **Contributions:** under a CLA, which is what makes the commercial licence possible.
- **Name:** "Ostler" and "OpenOstler" are trademarks; a UK filing is pending.
- **The open product must stand alone:** the cloud is a convenience, never a dependency.

## 9. Phases

Direction phases 0–4 ([direction spec](specs/2026-10-06-platform-direction-design.md#phases))
and UI phases U0–U7 ([UI spec §10](specs/2026-10-06-ui-architecture-design.md#10-phased-migration))
combined. U0–U3 sit in Phase 0, U5 in Phase 2, U4 in Phase 3. Each step gets its own spec.

| Phase | Scope | Status |
|---|---|---|
| **0 — Decouple** | `VehiclePack` contract; D2 behind it; layering tests | **Done** ([Phase 0 spec](specs/2026-10-06-phase0-vehiclepack-decoupling-design.md)) |
| | Repo split: platform `openostler` + pack `d2diag`, history kept | **Done** ([ADR-0015](decisions/adr-0015-repo-split-executed.md)) |
| | Homelab dev server (Docker/Dokploy, platform + pack at `PACK_REF`) | **Done** |
| | Version tracker: platform and pack versions and commits (`GET /version`, Settings → Version) | **Done** |
| | UI research (seven notes) and the UI architecture spec, approved | **Done** ([research](references/research/ui/), ADR-0018) |
| | Standards, CAN/head-unit and OVMS-reuse research; ADR-0016 to ADR-0021 | **Done** |
| | muki01 research (K-line, CAN, BMW I/K-Bus, diagnostic UI); ADR-0022 to ADR-0025 | **Done** ([synthesis](references/research/muki01/README.md)) |
| | T1S research, ADR-0026 (module bus); ecosystem research, ADR-0027 (IP everywhere) | **Done** ([T1S](references/research/t1s_module_bus.md), [ecosystem](references/research/ecosystem_architecture.md)) |
| | U0 seams: `vid` on sessions, optional VSS `metric` on signals, `vss/` overlay and generated `metrics.json`, JSON Schemas, OpenAPI/AsyncAPI | Next |
| | U1 shell: layout classes, status strip, rail/bottom bar, five destinations, Drive mode | Planned |
| | U2 driving state and server-enforced lockouts; U3 generated capability manifest, Scan all | Planned |
| **1 — Integrations** | Opt-in, read-only MQTT/HA, OVMS topics, OwnTracks, Traccar OsmAnd, ntfy | Planned |
| **2 — Guardian** | Firmware: tracker and notify-only alarm; Security destination (U5: devices, cameras) | Planned |
| **3 — Universal** | `generic_obd2` pack (U4: generated views, local VIN decode, unknown-vehicle banner) | Planned |
| **4 — Add-on modules** | The module-bus message spec and module contract; relay box, sensor/button nodes and head-unit CAN/OBD emulator on the module bus (T1S; CAN as fallback) | Planned |
| **U6 / U7** | Garage with a second real vehicle; decode evidence, fixtures, scrub CI, OBDb import/export, Decode mode | Waits on a second vehicle / may move earlier |
| **Moonshots** | Remote OEM disarm, remote start, ODX import (user-owned files only), cloud fleet, Web Bluetooth, CAN intrusion check, our own ROM or display hardware | Each needs its own ADR and gate |

## 10. Non-goals and hard lines

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

## 11. Success measures

Proposed, not yet adopted as targets:

- **Coverage:** the D2 pack's proven-field count only grows, and CI enforces it.
- **Universality:** a second, different pack (`generic_obd2`) runs on the same UI with no
  vehicle-type checks in screens.
- **Honesty:** every displayed value carries its confidence; no VIN pattern in tests,
  logs or uploads (CI-checked).
- **Interop:** our node works with ovms-home-assistant, Home Assistant discovery and
  OwnTracks consumers unchanged; packs round-trip with OBDb.
- **Ecosystem:** a new module appears in the UI and in Home Assistant within a minute of
  pairing, with no address typed; a module from someone other than the maintainer passes
  the conformance kit.
- **Footprint:** zero runtime dependencies above pyserial; parked draw within the
  measured budget; core does not grow per vehicle.
- **Community:** packs and verified signals contributed by people other than the
  maintainer, including upstream to OBDb.

## 12. Open questions

- ~~Whether `docs/` (and `references/`) are licensed CC BY-SA 4.0 like the data; REUSE needs
  an answer.~~ Decided 2026-10-06: docs stay under the code licence (AGPL-3.0-or-later);
  vehicle data stays CC BY-SA 4.0.
- CRA role and legal advice before the first hardware sale.
- The trust setup for local HTTPS on the Pi (per-device CA or ACME DNS;
  [ADR-0021](decisions/adr-0021-local-https-on-the-device.md)).
- How packs ship UI views separately from the platform build ([TODO.md](TODO.md)).
- Reverse-camera latency against Pi boot time, and a pre-event buffer while parked.
- The documented device ↔ cloud protocol, and whether a non-stdlib MQTT client is worth
  an ADR.
- The SoC for our own board (CM5 or i.MX93), and the guardian ↔ Pi power logic (unverified).
- The official UKIPO/EUIPO trademark search before announcing.
- Whether the guardian ships inside the base pack or only as an add-on (it is the always-on
  PLCA coordinator and the Pi's power manager when fitted).
- Where the MQTT broker lives while parked (the Pi is off), and the module-bus message spec
  ([ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)).
- Whether official hardware ships a native Matter bridge, and so pays for certification
  (about $7,500 a year plus $3,000 per product).

## Where the detail lives

- Direction: [platform direction](specs/2026-10-06-platform-direction-design.md),
  [UI architecture](specs/2026-10-06-ui-architecture-design.md).
- Decisions: [ADR-0012 licence](decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md),
  [ADR-0013 repo split and pack contract](decisions/adr-0013-repo-split-and-vehicle-pack-contract.md),
  [ADR-0014 handles](decisions/adr-0014-ostler-handles.md),
  [ADR-0015 split executed](decisions/adr-0015-repo-split-executed.md),
  [ADR-0016 VSS](decisions/adr-0016-covesa-vss-canonical-signal-namespace.md),
  [ADR-0017 open standards](decisions/adr-0017-open-standards-first.md),
  [ADR-0018 UI decisions](decisions/adr-0018-ui-architecture-decisions.md),
  [ADR-0019 OVMS/OBDb reuse](decisions/adr-0019-reuse-from-ovms-and-obdb.md),
  [ADR-0020 CAN links](decisions/adr-0020-can-links-listen-only-by-default.md),
  [ADR-0021 local HTTPS](decisions/adr-0021-local-https-on-the-device.md),
  [ADR-0022 K-line profiles](decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md),
  [ADR-0023 CAN bitrate](decisions/adr-0023-passive-can-bitrate-detection.md),
  [ADR-0024 body buses](decisions/adr-0024-body-bus-links-passive-by-default.md),
  [ADR-0025 reuse](decisions/adr-0025-reuse-and-licences-pragmatic.md),
  [ADR-0026 module bus](decisions/adr-0026-module-bus-10base-t1s.md),
  [ADR-0027 IP-everywhere ecosystem](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md).
- Research: [landscape](references/research/landscape.md), [OVMS](references/research/ovms.md),
  [OVMS reuse](references/research/ovms_reuse.md), [muki01](references/research/muki01/README.md), [standards](references/research/standards.md),
  [CAN and head units](references/research/canbus_headunit.md),
  [hardware](references/research/hardware.md), [platform](references/research/platform.md),
  [T1S module bus](references/research/t1s_module_bus.md),
  [ecosystem architecture](references/research/ecosystem_architecture.md),
  [feature backlog](references/research/features_backlog.md), [UI notes](references/research/ui/).
- Rules and scope: [CONSTITUTION.md](CONSTITUTION.md), [SCOPE.md](SCOPE.md),
  [TRADEMARKS.md](TRADEMARKS.md).

## Changelog

- 2026-10-06: v1.4, the smart-home-like ecosystem framing and tagline lead the mission
  ("the Home Assistant of the automotive world" moves to a comparison). The pillars are
  regrouped into base pack, add-on modules, standard networking and integrations. The
  hardware path sells a base pack plus add-on modules on an IP backbone (ADR-0026,
  ADR-0027). Phase 4 becomes add-on modules on the module bus.
