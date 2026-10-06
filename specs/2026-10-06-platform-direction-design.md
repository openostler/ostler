---
title: "Platform direction — from D2 Td5 tool to open vehicle platform (diagnostics · logger · telemetry · tracker/alarm) — design"
area: specs
status: draft
version: 0.5
updated: 2026-10-06
depends_on: [SCOPE.md, CONSTITUTION.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, references/research/platform.md, references/research/hardware.md, references/research/ovms.md, specs/2026-10-02-vehicle-integration-roadmap-design.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md]
summary: >
  Draft for owner review. Grows the project into an open, local-first vehicle platform: core (comms + interpretation) + declarative vehicle packs + opt-in integrations, an always-on ESP32 guardian with Linux on demand, add-on modules on an IP automotive-Ethernet backbone (ADR-0027), MQTT/HA with OVMS and OwnTracks compatibility, a notify-only alarm, a five-destination IA, and a phased plan with anti-bloat guardrails; D2 Td5 stays the reference pack. No implementation until approved.
---

# Platform direction — design (draft)

**Status:** draft for owner review. Nothing here gets built until this spec is approved and
each phase has its own spec.

The evidence is in `references/research/`:
- [landscape](../references/research/landscape.md)
- [OVMS](../references/research/ovms.md)
- [hardware](../references/research/hardware.md)
- [platform](../references/research/platform.md)
- [feature backlog](../references/research/features_backlog.md)

## Goal

An open, **local-first** platform for vehicles: diagnostics, a data logger and telemetry,
a GPS tracker and an alarm, integrated with Home Assistant over MQTT. It should work for
the Discovery 2 today, other Land Rovers next, and OBD-II/CAN vehicles after that.

Since v0.5 this sits inside a wider frame, the **smart-home-like ecosystem**
([GOALS.md](../GOALS.md), [ADR-0027](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)):
- a **base hardware pack** interfaces with the car and carries diagnostics and telemetry;
- **add-on modules** join over standard IP networking on an automotive-Ethernet backbone.

The research found that an open K-line/ICE telematics node, open Land Rover body-system
diagnostics, an open car alarm and a PWA-first car UI are all unclaimed.

## Principles

1. **D2 Td5 stays the reference pack** and the conformance fixture.
   The platform grows around it and never at its expense.
2. **Three layers:**
   - **core**: comms and interpretation;
   - **vehicle packs**: declarative data plus small code hooks;
   - **integrations**: consumers and add-ons, all opt-in.

   Import tests enforce the boundaries between them.
3. **Local-first and private by default.**
   Location and audio stay on the device unless the owner opts in (ADR-0009/0010).
   Cloud APIs die, so we never depend on one.
4. **Safety travels with the action.**
   Every path — UI, MQTT, HA, schedules — goes through the same gate.
   Remote paths get read-only actions only.
   The alarm notifies and never actuates.
5. **Dev-kit hardware now, our own hardware later.**
   Hardware-abstraction layers keep the switch to our own boards cheap.

## Decisions proposed

| Area | Proposal | Detail |
|---|---|---|
| Vehicle model | Per-vehicle **packs**: `vehicle.json` plus `ecus/*.json` (transport, protocol, per-state polls, signals with `metric`, actions with safety), `dtc/` and `hooks.py`. Imports OBDb and DBC; exports Torque CSV. Packs are licensed CC BY-SA. | platform.md §1 |
| Repo | One monorepo split into `core/`, `vehicles/` and `integrations/`. Plugins are found through stdlib entry points. **No fork.** Rename only after a second pack exists. | platform.md §2 |
| Hardware | An ESP32-S3 LTE/GNSS **guardian** on its own 18650 owns the alarm, tracker, wake, the 12 V watchdog and Pi power. A Pi 5 with a CarPiHAT PRO 5 is the Linux brain, powered on demand. A 10 Hz u-blox handles logging. KKL stays for K-line. **Add-on modules join an IP network on an automotive-Ethernet backbone**: 10BASE-T1S for modules, standard Ethernet (12 V or PoE) for cameras, Wi-Fi/USB for displays, with the Pi routing between segments. Our own CAN (separate wires, never the vehicle's CAN) is the dev-kit and µA-wake fallback. | hardware.md, [ADR-0026](../decisions/adr-0026-module-bus-10base-t1s.md), [ADR-0027](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md) |
| MQTT | Native HA device discovery, plus an **OVMS v3-compatible topic tree**, plus **OwnTracks** location. Two availability topics, brain and tracker. Stdlib client. | platform.md §3, ovms.md |
| Alarm | A notify-only state machine: arming, armed, notice/pending, triggered, alerting, tamper. It arms when the OEM alarm locks; strong triggers act at once and weak triggers need corroboration. Notifications escalate HA → ntfy → Telegram → SMS. The guardian owns it. | platform.md §4 |
| IA | `Home · Diagnose · Logs · Security · More`. Drive is a full-screen mode rather than a tab, and Analysis is the session detail view. Five tabs is a hard cap. | platform.md §5 |
| HEVAC | Moves **out of scope**: a separate ESP32 project that we only talk to. It supersedes spec #3 of the integration roadmap. | — |
| Licence | AGPL-3.0-or-later plus a commercial licence; CC BY-SA 4.0 for data; a CLA. | ADR-0012 |

## Phases

Each phase gets its own spec and tests.

| Phase | Scope |
|---|---|
| 0 | Extract the pack schema in place, with no behaviour change. Add layering tests. Introduce the new IA. |
| 1 | Opt-in, read-only integrations: MQTT/HA, OVMS topics, OwnTracks, Traccar OsmAnd, ntfy. |
| 2 | Guardian firmware: tracker and notify-only alarm. The Security destination appears. |
| 3 | The `generic_obd2` pack, which proves the platform is universal. |
| 4 | Add-on modules on the module bus (T1S, CAN as fallback): relay box, sensor/button nodes, head-unit/OBD emulator; the module contract and DevicePack. |
| Moonshot | Remote OEM disarm, remote start, ODX import, cloud fleet. Each needs its own ADR and gate. |

## Guardrails

- **Rule of two:** add no new abstraction until a second pack needs it.
- **Core only shrinks:** new features land as packs or integrations, not in core.
- **Some changes need an ADR first:** a new top-level destination, a new outbound data path, or a new runtime dependency.
- **The D2 pack's coverage is protected:** CI fails if it regresses.

## Owner answers (2026-10-06)

1. **The cloud is closed source.** It is the revenue stream, so it lives in a private
   `ostler-cloud` repo. It speaks only a documented MQTT/HTTPS protocol to the open device
   side and never imports platform code. That boundary keeps AGPL code and closed code
   separate (ADR-0013).
2. **The alarm is notify-only.** Actuation (OEM disarm, immobiliser, remote start) stays a
   moonshot, and each item needs its own ADR and gate.
3. **The Security slot shows "Map"** when no guardian is fitted.
4. **The working brand is "Ostler"** (ostler.tech; handles `openostler`, npm `@ostler`, Bluesky `@ostler.tech` — ADR-0014), pending an official UKIPO/EUIPO search in classes
   9, 12, 38 and 42. Naming research is in ADR-0013.

## Displays are thin clients; cameras live on our infrastructure

The owner's direction:

- **All the hardware and intelligence is ours.** The Pi, the guardian, the cameras and the
  recording are all our infrastructure.
- **Any screen is a view of the PWA.** That covers a phone, a tablet, or the current
  Android head unit's browser in kiosk mode. No CAN-box work is needed for this.
- **One camera system does every job.** Dashcam, parking/alarm clips, reversing and
  underbody views all come from the same cameras. They stream through go2rtc, optionally
  with Frigate detection on a Pi 5 AI HAT, into the same Logs and flags timeline. A locked
  head unit's own cameras are not duplicated.
- **The path:**
  1. Kiosk PWA now.
  2. An Ostler Android launcher: auto-start, a camera view on reverse, and CarPlay/AA via
     a wireless dongle.
  3. Only if the launcher hits real limits: our own ROM (AOSP/LineageOS) or our own
     display hardware.
- **Keep a head unit for media** if CarPlay, radio, the amplifier and steering-wheel
  controls are wanted. Nobody should rebuild those.

**Constraints to resolve before relying on cameras:**

1. **Reverse-camera latency and Pi boot time** (about 15–20 s on demand). Reversing must
   be instant. Either keep a direct path from camera to screen, or keep the Pi up while
   the ignition is on, ready before reverse is selected. Until then, treat it as
   assist-only.
2. **Pre-event footage while parked.** An alarm that wakes the Pi starts recording about
   20 s late. Cameras therefore need their own pre-record buffer: SD-card IP cams,
   ESP32-CAM_MJPEG2SD (AGPL), or a parking-mode dashcam. The alternative is a Pi left
   running while armed, which costs battery.
3. **Wired cameras for continuous recording.** Use standard Ethernet RTSP cameras on the
   camera segment (12 V or PoE; ADR-0027), CSI or USB. ESP32 cams are fine for snapshots
   only. Cameras never go on the T1S module segment.
4. **Pi 5 load.** It can record 2–4 RTSP streams without transcoding. Detection needs an
   AI HAT (Hailo) or a Coral.

## Repository map (ADR-0013)

| Repo | Visibility, licence | Role |
|---|---|---|
| `openostler/ostler` (new) | public, AGPL + commercial | Platform: core comms, snapshot contract, VehiclePack SDK, logbook/replay, integrations, web server, **the main UI** |
| `discovery2-diag` (this repo) | public, AGPL code + CC BY-SA data | Becomes the **Land Rover Discovery 2 pack** |
| `openostler/ostler-firmware` (new) | public, AGPL | ESP32 guardian and add-on modules (module bus, module contract) |
| `openostler/ostler-cloud` (new) | **private, closed** | Ostler Cloud |
| Later | — | `ostler-hardware` (CERN-OHL-S) and `ostler-android` |
| HEVAC | owner's separate project | Not part of this platform |

**Sequence:**

1. Decouple in place behind a `VehiclePack` interface. This is Phase 0 and needs its own
   spec.
2. Split the repos, preserving history.
3. Create the firmware and cloud repos when that work starts.

## Changelog

- 2026-10-06: v0.1, a draft from the October 2026 research pass.
- 2026-10-06: v0.2, owner answers (closed cloud, notify-only alarm, Map slot, working name Ostler); displays as thin clients with cameras on our infrastructure; repository map.
- 2026-10-06: v0.3, handles per ADR-0014 (GitHub org and Python package `openostler`).
- 2026-10-06: v0.4, the IA row is refined by the [UI architecture design](2026-10-06-ui-architecture-design.md) (draft); no decision here changes.
- 2026-10-06: v0.5, the ecosystem frame (ADR-0027): the "private CAN bus for add-ons" is replaced by an IP automotive-Ethernet backbone (T1S modules, Ethernet/PoE cameras, Wi-Fi/USB displays, the Pi routing); CAN becomes the dev-kit and µA-wake fallback; Phase 4 is renamed "add-on modules on the module bus".
