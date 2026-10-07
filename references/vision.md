---
title: "Vision — where Ostler is going in the long term"
area: references
status: draft
version: 1.5
updated: 2026-10-07
depends_on: [GOALS.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, references/research/ecosystem_architecture.md, references/research/addons_catalogue.md]
summary: >
  The long-term half of the goals, split out of GOALS.md (v2.0 keeps the short half): the gaps Ostler fills and the peers it works with, who it is for, the product pillars, the hardware path (one ESP32 diagnostic node with an optional brain: Ostler Diagnostics is the node, standalone with a phone; Ostler Brain is the brain it plugs into; Ostler Guardian is a hidden node hardware variant with no outputs; sensor nodes and other modules as add-ons, each with its own web page), the add-on vision (a Meshtastic-compatible LoRa add-on first, Wi-Fi HaLow, Babel if a Wi-Fi IP mesh is wanted, and more), a multi-vehicle garage, sharing and a social layer, connectivity and remote access (any modem, Starlink, failover, Tailscale, Ostler Cloud, HA Cloud), a Matter bridge, AI-native access through an MCP server behind the same gates, the repo and product map, the business model, success measures and open questions. Decisions: ADR-0028 to ADR-0040.
---

# Vision

[GOALS.md](../GOALS.md) holds the tagline, the mission, the principles, the hard lines and
the near-term roadmap. This file holds the long-term picture. Nothing here is a commitment:
each item needs its own spec, and the hard lines in GOALS.md and
[CONSTITUTION.md](../CONSTITUTION.md) bind every one of them. Where this file and an ADR or
spec disagree, the ADR or spec wins.

ADRs turn parts of this into decisions: [ADR-0028](../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md) (connectivity and remote access; its base-hardware part superseded by ADR-0032), [ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) (accounts, garage, sharing, social), [ADR-0030](../decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md) (MCP server and pack-authoring skill), [ADR-0031](../decisions/adr-0031-generic-obd2-pack-in-platform.md) (`generic_obd2` in the platform),
[ADR-0032](../decisions/adr-0032-one-node-optional-brain.md) (one node, optional brain), [ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md) (action categories and approvals), [ADR-0034](../decisions/adr-0034-repo-boundaries.md) (repo boundaries), [ADR-0035](../decisions/adr-0035-languages-by-tier.md) (languages by tier) and [ADR-0036](../decisions/adr-0036-vin-and-identity-data-in-recordings.md) (VIN and identity data).

## 1. Why Ostler exists

**We are making a Home Assistant for cars, not reinventing the wheel.** We reuse open
standards and open projects wherever they exist, and build only what nobody owns.

**The gaps nobody owns** ([landscape](research/landscape.md#gaps-nobody-owns-and-that-suit-us)):

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
jlr-scanner (Discovery 3/4), WiCAN (hardware front end). See [ovms.md](research/ovms.md).
We also **reuse their data** ([ADR-0019](../decisions/adr-0019-reuse-from-ovms-and-obdb.md)):
OBDb is the primary source for polled signals, and every OVMS vehicle and command is
imported where the licence allows, with commands disabled behind the safety gates and a
human review gate on the importer. Reuse is pragmatic
([ADR-0025](../decisions/adr-0025-reuse-and-licences-pragmatic.md)): any idea may be
reimplemented; GPL-3 code goes only into marked GPL-3 modules or packs.

## 2. Who it is for

- **Owners of older vehicles** that modern apps ignore, starting with K-line Land Rovers,
  who want dealer-level insight from a small node and their phone.
- **Home Assistant and self-hosting people** who want their car as a first-class device:
  sensors, location, alarm events and notifications on their own server.
- **DIY mechanics** who need honest fault reads, live data and guarded actuator tests.
- **Overlanders, off-roaders and bikers** who log drives, track off-grid, ride or drive in
  groups and add their own modules (relays, cameras, gauges, mesh radios).
- **Decoders and contributors** who reverse-engineer vehicles and want a pipeline that
  turns captures into verified, shareable packs.
- **Module makers** who want to build add-ons against an open contract and have them work
  with every Ostler car.
- **Companies** that want the code under a commercial licence, and **customers** of
  official Ostler hardware and Ostler Cloud.

## 3. Product pillars

| Part | Pillar | Goal | Tag | Status |
|---|---|---|---|---|
| **Node** | **Vehicle interface** | Front ends for the car's own buses (K-line, CAN, OBD-II, body buses), receive-first and gated (ADR-0020, ADR-0022, ADR-0024), all transmits through the node gate (ADR-0032); one `VehiclePack` per vehicle, decoded on the node by the C decoder from pack JSON | core | K-line on the D2 working; CAN/OBD-II planned |
| **Node / brain** | **Diagnostics** | Per vehicle → systems → function areas (Faults · Live · Tests · Procedures · Settings), a whole-car **Scan all** with honest states and a saved report, five safety tiers with action categories (ADR-0033) | core | D2 working on K-line; generic OBD-II and CAN/UDS planned |
| **Node / brain** | **Logging and telemetry** | Session logbook with replay, GPS and place names, notes, audio, IMU, flags; CSV, VBO and GPX export; the car's signals published live as VSS-named telemetry; later log formats (MoTeC, AiM, RaceChrono, RealDash) and lap timing | core / add-on | Logbook, replay and exports shipped; live MQTT, formats and lap timing planned |
| **Brain** | **Decode pipeline** | A read-only path from any unknown car to a pack with verified signals: connect → identify → inventory → baseline → capture → correlate → label → verify → package → contribute; a Decode mode in the app | core (developer) | Sniff, automap and catalog exist; pipeline is UI phase U7 |
| **Node variant** | **Guardian: tracking and alarm** | The node firmware on hidden, battery-backed hardware (tamper, IMU, better antennas, GPS, optional 4G and IoT SIM), with **no outputs**: tracker, geofences, alarm triggers (strong/weak, tamper, tow/theft from IMU + ignition off), notifications escalating HA → ntfy → Telegram → SMS that work with the brain off and no cloud (ADR-0033) | core variant | Designed (Phase 2 node firmware); not built |
| **Add-on modules** | **I/O, sensors, buttons, gauges** | A future I/O / relay module (alarm outputs, accessories; an ADR per car-switching function), sensor nodes (fast tacho, EGT, boost/oil, wideband AFR, accelerometers; read-only isolated taps), button nodes, gauge display, head-unit CAN/OBD emulator; HEVAC (the owner's separate project) joins through the same contract | add-on | Phase 4; not built |
| **Add-on modules** | **Cameras** | One camera system for dashcam, parking/alarm clips, reversing and underbody: standard ONVIF/RTSP IP cameras on the camera segment, streamed through go2rtc (optionally Frigate) into the same timeline. **Future:** our own cameras (100BASE-T1) and 360° surround view (ADR-0018) | add-on | Designed; constraints open (§11) |
| **Add-on modules** | **Displays / head unit** | Displays are thin clients: the PWA on any screen, **head-unit first**, then an Ostler Android launcher, then possibly our own ROM or display hardware | core / add-on | PWA shipped (phone-first today); head-unit layout is UI phase U1 |
| **Standard networking** | **IP backbone** | **10BASE-T1S** for modules, standard Ethernet (12 V or PoE) for cameras now and 100BASE-T1 for our own cameras later, Wi-Fi/USB for displays; the brain routes and firewalls between segments (the node is the hub when it is off); CAN and a wake wire as the dev-kit and µA-wake fallback ([ADR-0026](../decisions/adr-0026-module-bus-10base-t1s.md), [ADR-0027](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)) | core | Decided; T1S bench planned ([bench plan](t1s_bench_plan.md)) |
| **Standard networking** | **Discovery, messages, security** | mDNS/DNS-SD zero-config; MQTT 5 with a VSS topic tree; NTP from GNSS; per-node identity, mTLS and authenticated commands; no default passwords | core | Decided; module-bus message spec next |
| **Standard networking** | **Module contract** | One module manifest (identity, VSS signals, safety-tiered actions, events, UI slots, OTA) so modules are interchangeable and third-party modules are possible; DevicePack adapters for foreign devices; a conformance kit | core | Designed (ADR-0027, UI spec §6); spec with the module-bus message spec |
| **Integrations** | **Home Assistant and the IoT world** | Opt-in MQTT with Home Assistant device discovery, an OVMS v3-compatible topic tree, OwnTracks, Traccar OsmAnd, ntfy; Matter ecosystems reached through a bridge (Read, alarm arming and disarming; Comfort switches only with the install override), never inside modules | add-on | Phase 1; not built |
| **Integrations** | **Community data** | Packs as CC BY-SA data, OBDb-compatible, with evidence and fixtures; opt-in anonymous contribution; upstreaming to OBDb | core | D2 data is CC BY-SA; evidence/fixtures planned |

**One UI for every vehicle** ties the pillars together: the UI is generated from a
per-vehicle **capability manifest** (systems, signals with VSS paths, DTC sources,
safety-tiered actions, devices, views), with five destinations
(`Home · Diagnose · Logs · Security/Map · More`; Security is present with any node), Drive as a full-screen mode,
Parked/Idling/Moving lockouts enforced by the server, and a **garage** for more than one
vehicle. Screens never test a vehicle type
([UI spec](../specs/2026-10-06-ui-architecture-design.md)).

**HEVAC (climate control)** is a separate ESP32 project owned by the owner. Ostler only
talks to it, as an add-on device; it is not part of this platform.

## 4. Hardware path

Ostler hardware is **one diagnostic node with an optional brain**, plus **add-on
modules**, like a smart-home hub and its devices
([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md); names:
[ADR-0039](../decisions/adr-0039-product-family-diagnostics-guardian-hub.md);
[ecosystem research §3](research/ecosystem_architecture.md#3-product-taxonomy-and-the-module-contract)).

- **Ostler Diagnostics: the node** (the core product, at the OBD port). An always-on ESP32-S3 node owns the car
  and power: K-line/CAN I/O, decoding to VSS with the portable C decoder and pack JSON,
  the **transmit gate (the only path to the car)**, GPS, optional 4G (an official fitted
  module or a USB dongle; each device may have its own IoT SIM), a small parked MQTT broker, basic alarm, and
  switching the brain's power. It hosts its own web page and talks to the phone app (a
  PWA in a native wrapper such as Capacitor) over BLE or its Wi-Fi AP. It works fully
  offline with a phone; Ostler Cloud is optional, never required.
- **Ostler Brain** (sold as Ostler Diagnostics + Brain). A **brain** (the Pi now) adds compute and network: the full
  local app, add-on routing, cameras, big logbooks, replay, analysis, the decode lab and a
  local CA. It never touches the car (except, with no node fitted, through a third-party adapter behind a stricter software gate, [ADR-0044](../decisions/adr-0044-adapters-on-the-brain-without-a-node.md)); it consumes the node's VSS messages over IP (USB-NCM near
  the Brain, T1S elsewhere, Ethernet on prototypes). The node wakes it (ignition, a phone or cloud request,
  an alarm needing cameras, a schedule), orders a clean shutdown with a timeout, and
  serves the car alone again when it is off. Upgrading from Ostler Diagnostics is plugging in a Brain.
- **Ostler Guardian: a node hardware variant**, same firmware, built for security: own backup
  battery, tamper sensing, IMU, better antennas, GPS, optional 4G. It is fitted hidden,
  away from the diagnostic port, either replacing the plain node or alongside it as a
  battery-backed tracker that alerts if the node is ripped out. It has **no outputs**;
  each variant publishes a capability manifest and its web page shows only what it has.
- **Add-on modules:** sensor nodes, a future I/O / relay module, button nodes, gauge
  display, cameras and displays, and many more
  ([add-ons catalogue](research/addons_catalogue.md)); third-party modules join through the
  module contract. Each module, on either tier, hosts a small web page with its basic
  controls and keeps working on its own; joined to Ostler, it shows up in the main UI and
  in Home Assistant.
- **Network** ([ADR-0026](../decisions/adr-0026-module-bus-10base-t1s.md),
  [ADR-0027](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)): **10BASE-T1S**
  for modules (4-wire harness: 12 V, ground, the T1S pair, optional wake wire); standard
  Ethernet with 12 V or PoE for cameras; Wi-Fi/USB for displays; the brain routes between
  segments. CAN stays for dev kits and µA-wake nodes until T1S wake is proven
  ([bench plan](t1s_bench_plan.md)).
- **Now: a development kit, no custom PCBs** ([hardware research](research/hardware.md)):
  an ESP32-S3 node (PSRAM) with a K-line transceiver; a LilyGO T-SIM7670G-S3 with an IMU
  breakout as the guardian-variant prototype; Raspberry Pi 5 with a CarPiHAT PRO 5 as the
  brain, power-switched by the node; a 10 Hz u-blox; the KKL cable for development only;
  WiCAN Pro as a later OBD front end; ESP32-S3 boards with a LAN8651 Click for T1S modules
  (Waveshare and Autosport Labs ESP32 boards for CAN fallback); off-the-shelf ONVIF/RTSP
  IP cameras behind a small switch. Target parked draw: about 1–4 mA (unverified).
- **Later: our own boards** for hardware sales, once the software settles: a **node
  board** (ESP32-S3, CAN and K-line transceivers, ignition/opto front end, GNSS, optional
  4G) with a **guardian variant** (backup battery and charger, IMU, tamper), a separate
  **brain board** (CM5 or NXP i.MX93, a LAN8651, the camera Ethernet port), T1S module
  boards, and possibly our own 100BASE-T1 cameras with a LAN937x-class switch. Firmware
  and drivers carry over through the hardware-abstraction layers. Fallbacks, not plans:
  AutoPi-class closed boxes.

## 5. Add-ons: anything you can think of

Sensor nodes, cameras, I/O and relay modules and displays are the start. The module contract is
open, so the list is open too. Some directions:

- **Long-range links:** a convoy mesh that is **Meshtastic-compatible first** (a LoRa
  add-on for messages, positions and alerts off-grid, for overlanders and bikers), with
  **Babel if a Wi-Fi IP mesh is wanted** between cars or at camp; Wi-Fi HaLow for a
  long-range link back to home. A mesh is a remote path, Read and alerts only, and a richer
  car-to-car mesh (MeshCore, Reticulum and others) is a later add-on
  ([ADR-0038](../decisions/adr-0038-mesh-car-to-car-and-off-grid.md)).
- **Vehicle extras:** TPMS, GNSS/RTK, winch and light control, dash buttons and keypads,
  a trailer module, a weather station, leisure battery and solar monitoring, fridge and
  camper kit, EV charger integration.
- **Motorbikes:** an Ostler Diagnostics node with the phone as the screen, or a guardian-variant node.

The [add-ons catalogue](research/addons_catalogue.md) lists each idea with its transport,
the standards it should use and a phase.

## 6. Many vehicles, many people

- **A multi-vehicle garage.** The car you are in is the default. Ostler detects other
  vehicles it knows (your others, a friend's) and lets you switch between them.
- **Sharing with permission levels.** Invite family or friends to a vehicle with a role
  (owner, driver, viewer, or a time-boxed mechanic/guest); roles grant action categories,
  each capped by its safety tier. Phone approval of Tier 2–3 works over local links only;
  remote paths are read-only unless the install-level `OSTLER_ALLOW_REMOTE_CONTROL`
  override is set ([ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)).
  The hard lines never become a permission.
- **A social layer.** Groups and rides for bikers, convoys for overlanders and clubs:
  shared routes, live positions within the group, meet-ups. Basic features are built in,
  the way a music service builds its own sharing, and integrations reach WhatsApp,
  Facebook and similar services. Each such outbound path is opt-in, off by default and
  needs its own ADR.

[ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) (accepted) designs accounts, roles, the garage, sharing and social.

## 7. Connectivity and remote access

- **Any uplink, no SIM needed by default:** the car's or head unit's Wi-Fi, a phone
  hotspot, home Wi-Fi when parked, any 3G/4G USB dongle, an OpenWrt high-speed gateway,
  **Starlink**, or the node's optional 4G (each device may have its own IoT SIM; devices on the car LAN can share uplinks). The owner picks **Auto** (a priority
  list with failover) or pins one source, and each source is **metered** with data-cap
  alerts.
- **Remote access in tiers:** LAN only by default → **Tailscale** (opt-in) → **Ostler
  Cloud**, a product (an outbound tunnel, hosted sync, fleet), never the only option and
  never a dependency → **Home Assistant Cloud** through Home Assistant.
- Every outbound path stays opt-in and off by default.

[ADR-0028](../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md) decides the uplinks, failover, metering and the remote-access tiers
(LAN only by default, Tailscale opt-in, Ostler Cloud, HA Cloud through Home Assistant);
ADR-0032 replaces its base-hardware part. Ostler Cloud merges every device and serves the
whole app remotely, but in the car the brain (or phone) merges the same data locally, so
the alarm path and the in-car app never depend on the internet.

## 8. The wider smart home

- **Home Assistant first:** MQTT with HA discovery, then whatever HA adds.
- **A Matter bridge**, so Matter ecosystems see the car. It is a bridge only, never inside
  modules: through Home Assistant and Matterbridge until Ostler is at scale, and a certified
  Ostler bridge only then (about $7,500 a year plus $3,000 per product). Its entities: Read
  values (battery, charge, cabin temperature, "car is home", alarm state), arming and
  disarming the software alarm (disarm Parked only, audited and notified), and preheat or
  aux-heater switches **only with the install override**
  ([ADR-0027 Amendments](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md#amendments-2026-10-06-networking-answers)).

## 9. AI-native

- **An MCP server** lets AI clients read the car and help diagnose it. Every call passes
  through the same safety gates as the UI and ends at the node gate; an "accept" inside an
  AI client never counts as a confirmation (ADR-0033).
- **A pack-authoring skill** helps contributors turn captures and documents into a vehicle
  pack, through the decode pipeline and its human review gates; imports never rise above
  `candidate`.

[ADR-0030](../decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md) (accepted) designs both. [ADR-0031](../decisions/adr-0031-generic-obd2-pack-in-platform.md) ships `generic_obd2` inside the platform repo.

## 10. Repo, product map and business model

| Repo / product | Visibility, licence | Role |
|---|---|---|
| [`openostler/ostler`](https://github.com/openostler/ostler) | public; AGPL + commercial | Platform: comms core, `VehiclePack` contract, logbook/replay, integrations, web server, **the main UI** |
| [`openostler/ostler-pack-lr-d2`](https://github.com/openostler/ostler-pack-lr-d2) (`d2diag`) | public; AGPL code + CC BY-SA data | Ostler pack for Land Rover Discovery 2: the reference pack and conformance fixture |
| `openostler/ostler-firmware` | public; AGPL | First-class now: the C decoder, the link layer, every node variant (diagnostic node, guardian), keygen plugins, add-on module firmware, shared HAL ([ADR-0034](../decisions/adr-0034-repo-boundaries.md)) |
| Module contract repo | public | The module contract and conformance kit, split out at contract v1 |
| `openostler/ostler-cloud` | **private, closed** | Ostler Cloud; speaks only a documented MQTT/HTTPS protocol and never imports platform code |
| `ostler-hardware`, `ostler-android` | later; hardware CERN-OHL-S | Our own board designs (node and guardian variant, brain, modules), started at PCB time; the Ostler Android launcher |
| HEVAC | owner's separate project | Not part of the platform |

Brand split ([ADR-0014](../decisions/adr-0014-ostler-handles.md)): **Ostler** is the product
family (Ostler Diagnostics, Ostler Brain, Ostler Guardian, Ostler Cloud; ADR-0039); **OpenOstler** is the open code and
community. Packs are "Ostler pack *for* <vehicle>"; vehicle makers' marks are never part of
our brand ([TRADEMARKS.md](../TRADEMARKS.md)).

- **Funding:** official hardware sales (Ostler Diagnostics, Ostler Brain, Ostler Guardian and add-on modules), a closed-source
  **Ostler Cloud** subscription (hosted sync, fleet, remote access), and a **commercial
  licence** for closed or embedded use
  ([ADR-0012](../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md),
  [ADR-0013](../decisions/adr-0013-repo-split-and-vehicle-pack-contract.md)).
- **Code:** AGPL-3.0-or-later, so hosted modified copies must share source.
- **Vehicle data:** CC BY-SA 4.0, the same as OBDb, so packs can flow both ways.
- **Contributions:** under a CLA, which is what makes the commercial licence possible.
- **Name:** "Ostler" and "OpenOstler" are trademarks; a UK filing is pending.
- **The open product must stand alone:** the cloud is a convenience, never a dependency.

## 11. Success measures and open questions

**Success measures** (proposed, not yet adopted as targets):

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
- **Footprint:** core Python stays stdlib + pyserial (optional extras aside, and the
  native decoder via `ctypes`); parked draw within the measured budget; core does not
  grow per vehicle.
- **Community:** packs and verified signals contributed by people other than the
  maintainer, including upstream to OBDb.

**Open questions:**

- ~~Whether `docs/` (and `references/`) are licensed CC BY-SA 4.0 like the data.~~ Decided
  2026-10-06: docs stay under the code licence (AGPL-3.0-or-later); vehicle data stays
  CC BY-SA 4.0.
- ~~Whether the guardian ships inside the base pack or only as an add-on.~~ Owner,
  2026-10-06: the guardian is an add-on with an ESP32 buddy in the base pack (ADR-0028).
  Superseded the same day by ADR-0032: no separate buddy; the node takes the PLCA
  coordinator, brain power and parked broker roles, and the guardian is a node hardware
  variant.
- CRA role and legal advice before the first hardware sale.
- The trust setup for local HTTPS on the brain (per-device CA or ACME DNS;
  [ADR-0021](../decisions/adr-0021-local-https-on-the-device.md)).
- How packs ship UI views separately from the platform build ([TODO.md](../TODO.md)).
- Reverse-camera latency against Pi boot time, and a pre-event buffer while parked.
- The documented device ↔ cloud protocol, and whether a non-stdlib MQTT client is worth
  an ADR.
- The SoC for our own brain board (CM5 or i.MX93), and the node ↔ brain power logic
  (unverified; on the bench plan).
- ESP32-S3 memory for the node (PSRAM required), signed pack updates without a reflash,
  and phone ↔ node connectivity (ADR-0032 risks).
- The official UKIPO/EUIPO trademark search before announcing.
- ~~Where the MQTT broker lives while parked.~~ On the node, bridged by the brain when awake
  ([ADR-0028](../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md)). Still open: the module-bus message spec
  ([ADR-0027](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)).
- ~~Whether official hardware ships a native Matter bridge, and so pays for certification.~~
  Only at scale; until then Home Assistant and Matterbridge (ADR-0027 Amendments).
- How a standalone module's own web page is secured (no default passwords, ADR-0027) and
  how it hands over to the main UI once joined. With no brain, trust comes from phone
  pairing keys (no Pi CA).

## Changelog

- 2026-10-07: v1.5, the ADR-0044 exception (adapters on the Brain only with no node fitted) added to the Brain's "never touches the car" line.
- 2026-10-06: v1.4, product name per the ADR-0039 amendment: "Ostler Hub" is now **Ostler Brain**; "hub" (our compute box) reads "Brain".
- 2026-10-06: v1.3, product family renamed (ADR-0039): Ostler Diagnostics (was Ostler Lite),
  Ostler Hub (the brain) and Ostler Guardian; the node links to the hub by USB-NCM or T1S;
  4G is a fitted module or a USB dongle.

- 2026-10-06: v1.2, owner's networking answers (ADR-0037, ADR-0038, ADR-0027 Amendments):
  the convoy mesh is Meshtastic-compatible first, Babel if a Wi-Fi IP mesh is wanted, and a
  richer mesh later; the Matter bridge goes through HA and Matterbridge until at scale, with
  the entity set (Read, alarm arm and disarm, preheat and aux heater only with the install
  override); the Matter open question is answered.
- 2026-10-06: v1.1, node/brain direction (ADR-0032 to ADR-0036): the buddy is gone; Ostler
  Lite is the node alone and Ostler is node plus brain; the guardian is a hidden node
  hardware variant with no outputs; KKL is dev-only; dev kit and own boards reframed (node
  board with a guardian variant, separate brain board); firmware repo first-class, module
  contract repo at v1, ostler-hardware at PCB time; brand family adds Ostler Lite;
  remote-path rule per ADR-0033; footprint measure restated; ADR-0029/0030 accepted.

- 2026-10-06: v1.0, split out of GOALS.md v1.4 into v2.0 (gaps, peers, audience, pillars, hardware
  path, repo map, business model, success measures, open questions) and extended with the
  owner's long-term direction: the base pack as a Linux computer plus an ESP32 buddy, the
  guardian as an add-on, standalone module web pages, the add-on vision, the garage,
  sharing and social, connectivity, Matter and AI-native access.
