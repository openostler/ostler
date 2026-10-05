---
title: "Goals — what Ostler is for and where it is going"
area: root
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [SCOPE.md]
summary: >
  The canonical statement of Ostler's full goals: an open, local-first vehicle platform (diagnostics, logging and telemetry, tracker and notify-only alarm, add-on devices, cameras, thin-client displays, MQTT/Home Assistant) that starts with the Land Rover Discovery 2 and grows to any car. Covers mission, principles, audience, pillars, vehicle and hardware roadmaps, repo map, business model, phases with what is done, hard lines, success measures and open questions.
---

# Goals

This is the one place that says what Ostler is for and where it is going. The detail lives
in the [direction spec](specs/2026-10-06-platform-direction-design.md) and the
[UI architecture spec](specs/2026-10-06-ui-architecture-design.md) (both **drafts** for
owner review), the ADRs in [decisions/](decisions/CLAUDE.md) and the research in
[references/research/](references/research/platform.md). Where this file and those
disagree, they win; fix this file. The hard rules are in [CONSTITUTION.md](CONSTITUTION.md).

## 1. Mission and positioning

**Ostler is an open, local-first platform for vehicles: diagnostics, a data logger with
telemetry, a GPS tracker and a notify-only alarm, add-on devices and cameras, shown on any
screen and integrated with Home Assistant over MQTT.** The ambition is to be *the Home
Assistant of the automotive world*: one open hub that understands many vehicles through
community-maintained definitions (vehicle packs), runs on hardware you own, and keeps your
data with you.

It starts with the Land Rover Discovery 2 Td5, which talks K-line rather than CAN, and
grows from there. The core mission stays narrow ([SCOPE.md](SCOPE.md)):
**communication with the car and interpretation of its data.** Everything else is a
consumer of that.

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

**Peers we interoperate with rather than replace:** OVMS (we speak its MQTT topic tree),
OBDb (we share CC BY-SA signal data), OwnTracks and Traccar (location), Home Assistant,
jlr-scanner (Discovery 3/4), WiCAN (hardware front end). See [ovms.md](references/research/ovms.md).

## 2. Principles

1. **Local-first and private by default.** Everything works with no cloud. Location and
   audio stay on the device unless the owner opts in (ADR-0009, ADR-0010). Every outbound
   path is opt-in and off by default. Cloud APIs die, so we never depend on one.
2. **Open standards wherever they exist.** COVESA VSS paths as the canonical signal
   namespace, with OVMS, Home Assistant and OBDb names generated as aliases (owner
   direction; proposed in the UI spec §5.6, to be locked by an ADR). OBDb-compatible pack
   data, MQTT with Home Assistant discovery, OwnTracks, Traccar OsmAnd, SocketCAN, ISO-TP.
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
- **Companies** that want the code under a commercial licence, and **customers** of
  official Ostler hardware and Ostler Cloud.

## 4. Product pillars

| Pillar | Goal | Tag | Status |
|---|---|---|---|
| **Diagnostics** | Per vehicle → systems → function areas (Faults · Live · Tests · Procedures · Settings), a whole-car **Scan all** with honest states and a saved report, five safety tiers | core | D2 working on K-line; generic OBD-II and CAN/UDS planned |
| **Logging and telemetry** | Session logbook with replay, GPS and place names, notes, audio, IMU, flags; CSV, VBO and GPX export; later log import/export (MoTeC, AiM, RaceChrono, RealDash) and lap timing | core / add-on | Logbook, replay and exports shipped; formats and lap timing in backlog |
| **Tracker and alarm** | An always-on ESP32 guardian with its own battery and IoT SIM: tracker, geofences, a **notify-only** alarm (strong/weak triggers, tamper), notifications escalating HA → ntfy → Telegram → SMS | add-on | Designed (Phase 2); not built |
| **Add-on devices** | Modules on a **private CAN bus** (never the vehicle's): relay box, head-unit CAN/OBD emulator, gauge display; devices register into UI slots through a `DevicePack` contract | add-on | Phase 4; not built |
| **Cameras** | One camera system for dashcam, parking/alarm clips, reversing and underbody (360 later), streamed through go2rtc (optionally Frigate) into the same timeline, on our own infrastructure | add-on | Designed; constraints open (§10) |
| **Displays / head unit** | Displays are thin clients: the PWA on any screen, **head-unit first**, then an Ostler Android launcher, then possibly our own ROM or display hardware | core / add-on | PWA shipped (phone-first today); head-unit layout is UI phase U1 |
| **Integrations** | Opt-in MQTT with Home Assistant discovery, an OVMS v3-compatible topic tree, OwnTracks, Traccar OsmAnd, ntfy; a stdlib MQTT client | add-on | Phase 1; not built |
| **Decode pipeline** | A read-only path from any unknown car to a pack with verified signals: connect → identify → inventory → baseline → capture → correlate → label → verify → package → contribute; a Decode mode in the app | core (developer) | Sniff, automap and catalog exist; pipeline is UI phase U7 |
| **Community data** | Packs as CC BY-SA data, OBDb-compatible, with evidence and fixtures; opt-in anonymous contribution; upstreaming to OBDb | core | D2 data is CC BY-SA; evidence/fixtures planned |

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

- **Now — development kit, no custom PCBs** ([hardware research](references/research/hardware.md)):
  Raspberry Pi 5 with a CarPiHAT PRO 5 as the Linux "brain", powered on demand; an
  ESP32-S3 LTE/GNSS **guardian** (e.g. LilyGO T-SIM7670G-S3) on its own 18650 with an IoT
  SIM; a 10 Hz u-blox for logging; the KKL cable for K-line; WiCAN Pro as a later OBD front
  end; Waveshare and Autosport Labs ESP32 boards for add-ons. Target parked draw from the
  car battery: about 1–4 mA (unverified).
- **Later — our own boards** for hardware sales, once the software settles: one board
  combining a CM5 (or NXP i.MX93), an ESP32-S3, a SIM7670 modem, CAN and K-line
  transceivers, an ignition/opto front end and a cell charger. Firmware and drivers carry
  over through the hardware-abstraction layers. Fallbacks, not plans: AutoPi-class closed
  boxes.

## 7. Repo and product map

| Repo / product | Visibility, licence | Role |
|---|---|---|
| [`openostler/ostler`](https://github.com/openostler/ostler) (this repo) | public; AGPL + commercial | Platform: comms core, `VehiclePack` contract, logbook/replay, integrations, web server, **the main UI** |
| [`discovery2-diag`](https://github.com/JamesWrightDavid/discovery2-diag) (`d2diag`) | public; AGPL code + CC BY-SA data | Ostler pack for Land Rover Discovery 2: the reference pack and conformance fixture |
| `openostler/ostler-firmware` | public; AGPL | ESP32 guardian, add-on modules, shared HAL, private-CAN protocol (created when that work starts) |
| `openostler/ostler-cloud` | **private, closed** | Ostler Cloud; speaks only a documented MQTT/HTTPS protocol and never imports platform code |
| `ostler-hardware`, `ostler-android` | later; hardware CERN-OHL-S | Our own board designs; the Ostler Android launcher |
| HEVAC | owner's separate project | Not part of the platform |

Brand split ([ADR-0014](decisions/adr-0014-ostler-handles.md)): **Ostler** is the product
family (Ostler Cloud, Ostler Guardian, Ostler Node); **OpenOstler** is the open code and
community. Packs are "Ostler pack *for* <vehicle>"; vehicle makers' marks are never part
of our brand ([TRADEMARKS.md](TRADEMARKS.md)).

## 8. Business model and licensing

- **Funding:** official hardware sales, a closed-source **Ostler Cloud** subscription
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
| | UI research (seven notes) and the UI architecture draft | **Done** ([research](references/research/ui/)) |
| | U0 seams: `vid` on sessions, optional VSS `metric` on signals, `metrics.json` | Next |
| | U1 shell: layout classes, status strip, rail/bottom bar, five destinations, Drive mode | Planned |
| | U2 driving state and server-enforced lockouts; U3 generated capability manifest, Scan all | Planned |
| **1 — Integrations** | Opt-in, read-only MQTT/HA, OVMS topics, OwnTracks, Traccar OsmAnd, ntfy | Planned |
| **2 — Guardian** | Firmware: tracker and notify-only alarm; Security destination (U5: devices, cameras) | Planned |
| **3 — Universal** | `generic_obd2` pack (U4: generated views, local VIN decode, unknown-vehicle banner) | Planned |
| **4 — CAN add-ons** | Relay box, head-unit CAN/OBD emulator over the private CAN bus | Planned |
| **U6 / U7** | Garage with a second real vehicle; decode evidence, fixtures, scrub CI, OBDb import/export, Decode mode | Waits on a second vehicle / may move earlier |
| **Moonshots** | Remote OEM disarm, remote start, ODX import (user-owned files only), cloud fleet, Web Bluetooth, CAN intrusion check, our own ROM or display hardware | Each needs its own ADR and gate |

## 10. Non-goals and hard lines

**Hard lines** (also in [CONSTITUTION.md](CONSTITUTION.md) and the UI spec §7):

- **Nothing writes to a car without the gates.** Coding and security writes are listed
  for honesty and never runnable; clears, actuator tests and procedures are confirmed,
  Parked-only and logged. Airbag/SRS is read-only by construction.
- **No EKA, key or immobiliser programming** in any product path, and no SecurityAccess
  or replayed sniffed write beyond what a module needs for diagnostic reads (e.g. the Td5
  seed-key unlock) without its own ADR.
- **The VIN is never logged, recorded, put in fixtures or uploaded.** It is decoded in
  memory; only a masked form and a device-local fingerprint are kept. Raw captures are
  never committed.
- **Local-first and private by default.** No cloud dependency; every outbound path is
  opt-in.
- **The alarm is notify-only.** It never actuates the car; it sits alongside the OEM alarm
  and is not a Thatcham-rated product.
- **No converted dealer databases** (the OpenVehicleDiag DMCA lesson), and no
  non-commercial or unlicensed code.
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
- **Footprint:** zero runtime dependencies above pyserial; parked draw within the
  measured budget; core does not grow per vehicle.
- **Community:** packs and verified signals contributed by people other than the
  maintainer, including upstream to OBDb.

## 12. Open questions

- Lock VSS as the canonical namespace with an ADR (UI spec Q1); the rest of the UI spec's
  owner questions (§11) are open while it is a draft.
- A `comfort` safety class for our own devices (HEVAC setpoints, camera switching)
  allowed while Moving (UI spec Q4).
- How packs ship UI views separately from the platform build ([TODO.md](TODO.md)).
- Reverse-camera latency against Pi boot time, and a pre-event buffer while parked.
- The documented device ↔ cloud protocol, and whether a non-stdlib MQTT client is worth
  an ADR.
- The SoC for our own board (CM5 or i.MX93), and the guardian ↔ Pi power logic (unverified).
- The official UKIPO/EUIPO trademark search before announcing.
- How the D2 pack's gated BCU security research (its ADR-0007) sits with the "no key
  programming" line.

## Where the detail lives

- Direction: [platform direction](specs/2026-10-06-platform-direction-design.md),
  [UI architecture](specs/2026-10-06-ui-architecture-design.md).
- Decisions: [ADR-0012 licence](decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md),
  [ADR-0013 repo split and pack contract](decisions/adr-0013-repo-split-and-vehicle-pack-contract.md),
  [ADR-0014 handles](decisions/adr-0014-ostler-handles.md),
  [ADR-0015 split executed](decisions/adr-0015-repo-split-executed.md).
- Research: [landscape](references/research/landscape.md), [OVMS](references/research/ovms.md),
  [hardware](references/research/hardware.md), [platform](references/research/platform.md),
  [feature backlog](references/research/features_backlog.md), [UI notes](references/research/ui/).
- Rules and scope: [CONSTITUTION.md](CONSTITUTION.md), [SCOPE.md](SCOPE.md),
  [TRADEMARKS.md](TRADEMARKS.md).
