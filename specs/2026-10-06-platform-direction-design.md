---
title: "Platform direction — from D2 Td5 tool to open vehicle platform (diagnostics · logger · telemetry · tracker/alarm) — design"
area: specs
status: draft
version: 0.6
updated: 2026-10-06
depends_on: [decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, SCOPE.md, CONSTITUTION.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, references/research/platform.md, references/research/hardware.md, references/research/ovms.md, specs/2026-10-02-vehicle-integration-roadmap-design.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md]
summary: >
  Draft for owner review. Grows the project into an open, local-first vehicle platform: core (comms + interpretation) + declarative vehicle packs + opt-in integrations, built on one ESP32 node that owns the car and power (Ostler Lite) with an optional Pi brain for compute (Ostler; ADR-0032), add-on modules on an IP automotive-Ethernet backbone (ADR-0027), MQTT/HA with OVMS and OwnTracks compatibility, an alarm owned by the node (the guardian is an output-free node variant; outputs later via an I/O module, ADR-0033), one app as cloud, brain and phone (PWA in Capacitor), a five-destination IA, a repo map per ADR-0034, and a phased plan with anti-bloat guardrails; D2 Td5 stays the reference pack. No implementation until approved.
---

# Platform direction — design (draft)

**Status:** draft for owner review. Nothing here gets built until this spec is approved and
each phase has its own spec. v0.6 (2026-10-06) reframes it around one node and an optional
brain ([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md)), action categories and
approvals ([ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)) and the repo
boundaries ([ADR-0034](../decisions/adr-0034-repo-boundaries.md)).

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
- the **node** (an ESP32) interfaces with the car and carries diagnostics, telemetry, GPS
  and the basic alarm; on its own it is **Ostler Lite**, used through the phone app or
  Ostler Cloud and fully usable offline with a phone;
- an optional **brain** (a Pi) adds compute and network for the full **Ostler**: the local
  app, add-on routing, cameras, big logbooks, replay, analysis and the decode lab. Upgrading
  is plugging in a brain; the car side does not change ([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md));
- **add-on modules** join over standard IP networking on an automotive-Ethernet backbone, on
  either tier.

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
   Every path — UI, MQTT, HA, schedules, the phone — ends at the same gate on the node, the
   only path to the car. Roles grant action categories, each capped by its tier; a paired
   phone may approve Tier 2–3 over local links. Remote paths are read-only unless the
   install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is set (ADR-0033).
   The alarm path never depends on the brain or the internet.
5. **Dev-kit hardware now, our own hardware later.**
   Hardware-abstraction layers keep the switch to our own boards cheap.

## Decisions proposed

| Area | Proposal | Detail |
|---|---|---|
| Vehicle model | Per-vehicle **packs**: `vehicle.json` plus `ecus/*.json` (transport, protocol, per-state polls, signals with `metric`, actions with safety), `dtc/` and `hooks.py`. Imports OBDb and DBC; exports Torque CSV. Packs are licensed CC BY-SA. | platform.md §1 |
| Repo | One monorepo split into `core/`, `vehicles/` and `integrations/`. Plugins are found through stdlib entry points. **No fork.** Rename only after a second pack exists. | platform.md §2 |
| Hardware | An ESP32-S3 **node** owns the car and power: K-line and CAN I/O, decoding to VSS, the transmit gate (the only path to the car), GPS, optional 4G, the basic alarm, the 12 V watchdog, a parked MQTT broker and switching the brain's power. The **guardian** is a hardware variant of the node on the same firmware (backup battery, tamper, IMU, better antennas, optional 4G; hidden; no outputs) that replaces the node or sits alongside it. A Pi 5 is the optional **brain**, woken by the node on ignition, a phone or cloud request, an alarm, a schedule or EV always-on, and shut down cleanly with a timeout. A 10 Hz u-blox can add logging accuracy. The KKL cable is dev-only. **Add-on modules join an IP network on an automotive-Ethernet backbone**: 10BASE-T1S for modules, standard Ethernet (12 V or PoE) for cameras, Wi-Fi/USB for displays, with the brain routing between segments. Our own CAN (separate wires, never the vehicle's CAN) is the dev-kit and µA-wake fallback. | hardware.md, [ADR-0026](../decisions/adr-0026-module-bus-10base-t1s.md), [ADR-0027](../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md), [ADR-0032](../decisions/adr-0032-one-node-optional-brain.md) |
| MQTT | Native HA device discovery, plus an **OVMS v3-compatible topic tree**, plus **OwnTracks** location. Two availability topics, **node** and **brain** (the brain's goes offline whenever the node powers it down). Stdlib client. | platform.md §3, ovms.md |
| Alarm | A state machine: arming, armed, notice/pending, triggered, alerting, tamper. It arms when the OEM alarm locks; strong triggers act at once and weak triggers need corroboration (IMU motion with the ignition off as tow or theft). Notifications escalate HA → ntfy → Telegram → SMS. **The node owns it**, and node → notification works with the brain off and no cloud (a tested rule). The **guardian variant** is the alarm-grade node and has **no outputs**. Alarm outputs (siren, triggering the car's native alarm, immobiliser) come later through a separate I/O module, each with its own ADR; the former "notify-only" rule is dropped (ADR-0033). | platform.md §4, [ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md) |
| App | One app codebase in three places: Ostler Cloud, the brain, and the phone as a PWA packaged with Capacitor (for BLE and local Wi-Fi to the node, especially on iOS). The phone-to-node link is core now. | [ADR-0032](../decisions/adr-0032-one-node-optional-brain.md) |
| IA | `Home · Diagnose · Logs · Security · More`. Drive is a full-screen mode rather than a tab, and Analysis is the session detail view. Five tabs is a hard cap. | platform.md §5 |
| HEVAC | Moves **out of scope**: a separate ESP32 project that we only talk to. It supersedes spec #3 of the integration roadmap. | — |
| Licence | AGPL-3.0-or-later plus a commercial licence; CC BY-SA 4.0 for data; a CLA. | ADR-0012 |

## Phases

Each phase gets its own spec and tests.

| Phase | Scope |
|---|---|
| 0 | Extract the pack schema in place, with no behaviour change. Add layering tests. Introduce the new IA. |
| 1 | Opt-in, read-only integrations: MQTT/HA, OVMS topics, OwnTracks, Traccar OsmAnd, ntfy. |
| 2 | **Node firmware (one firmware, all variants)**: K-line/CAN link and gate, tracker, alarm and notifications with the brain off, the capability manifest per hardware variant, brain wake and shutdown. The Security destination appears. |
| 3 | The `generic_obd2` pack, which proves the platform is universal. |
| 4 | Add-on modules on the module bus (T1S, CAN as fallback): our own relay boards (an ADR per switching function), sensor/button nodes, head-unit/OBD emulator; the module contract and DevicePack. |
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
2. ~~The alarm is notify-only.~~ **Changed 2026-10-06 (ADR-0033):** alarm outputs may be
   real (siren, the car's native alarm, immobiliser), but only through a future I/O module
   with its own design and an ADR per car-switching function, never on the guardian.
   Remote start and OEM disarm stay moonshots, each with its own ADR and gate.
3. ~~The Security slot shows "Map" when no guardian is fitted.~~ **Changed 2026-10-06:**
   Security is present with any node, since every node has GPS and a basic alarm.
4. **The working brand is "Ostler"** (ostler.tech; handles `openostler`, npm `@ostler`, Bluesky `@ostler.tech` — ADR-0014), pending an official UKIPO/EUIPO search in classes
   9, 12, 38 and 42. Naming research is in ADR-0013.

## Displays are thin clients; cameras live on our infrastructure

The owner's direction:

- **All the hardware and intelligence is ours.** The node and its variants, the brain, the
  cameras and the recording are all our infrastructure.
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
2. **Pre-event footage while parked.** When an alarm makes the node wake the brain,
   recording starts about 20 s late. Cameras therefore need their own **pre-event
   buffer** that covers the node-wakes-brain delay: SD-card IP cams, ESP32-CAM_MJPEG2SD
   (AGPL), or a parking-mode dashcam. The alternative is a brain left running while armed,
   which costs battery.
3. **Wired cameras for continuous recording.** Use standard Ethernet RTSP cameras on the
   camera segment (12 V or PoE; ADR-0027), CSI or USB. ESP32 cams are fine for snapshots
   only. Cameras never go on the T1S module segment.
4. **Pi 5 load.** It can record 2–4 RTSP streams without transcoding. Detection needs an
   AI HAT (Hailo) or a Coral.

## Repository map (ADR-0013, ADR-0034)

Split only when the toolchain, licence, release cadence or contributors differ
([ADR-0034](../decisions/adr-0034-repo-boundaries.md)).

| Repo | Visibility, licence | Role |
|---|---|---|
| `openostler/ostler` | public, AGPL + commercial | The one platform repo: server, the Python lab and reference link layer, high-level features, **the main UI** (not split out), contracts and `generic_obd2` |
| `openostler/ostler-firmware` | public, AGPL | First-class now: the portable C decoder, the link layer and gate, every node variant, keygen plugins. The D2 pack's `esp32/kline_node` moves here when the repo is created |
| `ostler-pack-<x>` (the D2 pack is `discovery2-diag`) | public, AGPL code + CC BY-SA data | Vehicle packs |
| `openostler/ostler-cloud` | **private, closed** | Ostler Cloud |
| Later | — | `ostler-hardware` (CERN-OHL-S) when PCB work starts; the module contract and conformance kit at contract v1; `ostler-android` |
| HEVAC | owner's separate project | Not part of this platform |

**Sequence:**

1. Decouple in place behind a `VehiclePack` interface (Phase 0, done).
2. Split the repos, preserving history (done, ADR-0015).
3. Create `ostler-firmware` now; the cloud repo when that work starts; the others at their
   trigger.

## Changelog

- 2026-10-06: v0.1, a draft from the October 2026 research pass.
- 2026-10-06: v0.2, owner answers (closed cloud, notify-only alarm, Map slot, working name Ostler); displays as thin clients with cameras on our infrastructure; repository map.
- 2026-10-06: v0.3, handles per ADR-0014 (GitHub org and Python package `openostler`).
- 2026-10-06: v0.4, the IA row is refined by the [UI architecture design](2026-10-06-ui-architecture-design.md) (draft); no decision here changes.
- 2026-10-06: v0.5, the ecosystem frame (ADR-0027): the "private CAN bus for add-ons" is replaced by an IP automotive-Ethernet backbone (T1S modules, Ethernet/PoE cameras, Wi-Fi/USB displays, the Pi routing); CAN becomes the dev-kit and µA-wake fallback; Phase 4 is renamed "add-on modules on the module bus".
- 2026-10-06: v0.6, reframed to one node and an optional brain (ADR-0032): summary and
  goal (Ostler Lite and Ostler); the hardware row (the node owns the car and power, the
  guardian is an output-free node variant, the brain is woken and shut down by the node,
  KKL dev-only); MQTT availability topics node and brain; the alarm owned by the node,
  notify-only dropped and outputs only via a future I/O module (ADR-0033); safety principle
  and owner answers 2–3 updated (local-only control with the install override; Security
  present with any node); a new App row (PWA in Capacitor); Phase 2 is node firmware for
  every variant; cameras need a pre-event buffer for the node-wakes-brain delay; the repo
  map follows ADR-0034; buddy, base pack and guardian-add-on wording replaced by node.
