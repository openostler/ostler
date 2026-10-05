---
title: "Platform direction — from D2 Td5 tool to open vehicle platform (diagnostics · logger · telemetry · tracker/alarm) — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [SCOPE.md, CONSTITUTION.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, references/research/platform.md, references/research/hardware.md, references/research/ovms.md, specs/2026-10-02-vehicle-integration-roadmap-design.md]
summary: >
  Draft for owner review. Grows the project into an open, local-first vehicle platform: core (comms + interpretation) + declarative vehicle packs + opt-in integrations, an always-on ESP32 guardian with Linux on demand, MQTT/HA with OVMS and OwnTracks compatibility, a notify-only alarm, a five-destination IA, and a phased plan with anti-bloat guardrails; D2 Td5 stays the reference pack. No implementation until approved.
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
| Hardware | An ESP32-S3 LTE/GNSS **guardian** on its own 18650 owns the alarm, tracker, wake, the 12 V watchdog and Pi power. A Pi 5 with a CarPiHAT PRO 5 is the Linux brain, powered on demand. A 10 Hz u-blox handles logging. KKL stays for K-line. A private CAN bus carries add-on modules. Cameras use Wi-Fi. | hardware.md |
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
| 4 | CAN add-ons: relay box and head-unit/OBD emulator. |
| Moonshot | Remote OEM disarm, remote start, ODX import, cloud fleet. Each needs its own ADR and gate. |

## Guardrails

- **Rule of two:** add no new abstraction until a second pack needs it.
- **Core only shrinks:** new features land as packs or integrations, not in core.
- **Some changes need an ADR first:** a new top-level destination, a new outbound data path, or a new runtime dependency.
- **The D2 pack's coverage is protected:** CI fails if it regresses.

## Open questions for the owner

1. Is the cloud fully AGPL (Nabu Casa style), or a separate proprietary service (open core)? See ADR-0012.
2. Does the alarm stay strictly notify-only for the first release? Proposed: yes.
3. Is "Map" an acceptable stand-in for the Security slot when no guardian is fitted?
4. When is the right time to rename the project, and what is the name to trademark?

## Changelog

- 2026-10-06: v0.1, a draft from the October 2026 research pass.
