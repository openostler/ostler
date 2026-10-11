---
title: "Gateway settings — the gateway owns all hardware and connections; car profiles, this-gateway settings and account sync; automatic car selection — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-11
depends_on: [decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, references/design/2026-10/brief/00-structure.md]
summary: >
  Draft for the owner (agreed in discussion on 2026-10-11). The gateway owns all hardware and connections; apps only ever talk to the gateway, and any gateway-capable device runs it (Brain, the Android gateway app, a node for live data, or a temporary gateway in the browser built from the same code). Settings sit at three levels: account (garage, sharing, backups; synced and optional), car profile (one per car: identity, devices and buses, recording, alerts, app permissions, outputs, layouts, sharing; held by the car's gateway and synced) and this gateway (role, network, storage, power, updates; one device). A Brain is in practice one car's gateway; a phone gateway carries several car profiles. The car is selected automatically from detection (VIN or pack fingerprint), with "New car found" for an unknown car and a manual switch. One server per car at a time: a phone that sees a car whose Brain is running becomes its client. Lists the gateway's settings sections and the open questions.
---

# Gateway settings — design

**Status: draft, v0.1, for the owner's approval.** Agreed in discussion on 2026-10-11. It fills
in the gateway side of [ADR-0052](../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md)
§6 and uses [ADR-0053](../decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md) for
detection.

## 1. The rule

- **The gateway owns all hardware and connections:** nodes, dongles, buses, the Brain link,
  pairing, detection, permissions and outputs.
- **Apps only ever talk to the gateway,** over VISS
  ([ADR-0051](../decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md)). No app opens a
  USB, Bluetooth or bus connection of its own.
- **Any gateway-capable device runs it:** the Brain; the Android gateway app; a node, for live
  data only; or a temporary gateway inside a browser page (WebUSB or Web Bluetooth), built from
  the same gateway code, so even the browser-only mode follows this rule.
- **All hardware setup lives in the gateway's settings.** Each app keeps its own settings plus
  the small Shared section (ADR-0052 §6).

## 2. Three levels of settings

| Level | Lives | Holds |
|---|---|---|
| **Account** (optional, synced) | the cloud, cached on every gateway | the garage list, sharing, backups |
| **Car profile** (one per car) | the car's gateway, synced to the account | identity, devices and buses, recording, alerts, app permissions, outputs, layouts, driver side, sharing |
| **This gateway** (one per device) | that device only | role, network, storage, power, updates |

- **Without an account,** car profiles live on the gateway that made them; export and import
  move them.
- **A Brain** is fitted in one car, so in practice it is that car's gateway and holds one
  profile (more only if the owner moves it).
- **A phone gateway** travels between cars and holds a profile for each.

## 3. Choosing the car

- **Automatic:** when the gateway connects, detection (ADR-0053) reads the VIN or matches a pack
  fingerprint (for example the Td5 engine computer's ID) and selects that car's profile.
- **Unknown car:** a "New car found" notice offers to set up a profile. Nothing is recorded or
  shared for it until the owner says yes.
- **Manual switch** at any time, from the vehicle chip every app shows (ADR-0052 §6).
- **Connected and viewing:** the connected car follows the hardware. History apps may view
  another car from the garage, labelled "Viewing: … · not connected". Live data and any action
  that changes a car always follow the connected car.
- **One server per car** ([ADR-0051](../decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md)
  item 9): if a phone gateway sees a car whose Brain is running, the phone becomes the Brain's
  client and the car's settings stay on the Brain.

## 4. The gateway's settings sections

1. **Cars** — the garage, then the selected car:
   - **Identity:** name, VIN, pack, photo, driver side.
   - **Devices:** nodes and dongles bound to this car, the buses, "one tester per bus", the
     opt-in for actuator tests (ADR-0053; [ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)).
   - **Recording:** what is logged and how long it is kept.
   - **Alerts:** what counts as warning, caution or notice, and where alerts go.
   - **Apps and permissions:** what each app may see and change on this car, the access log,
     revoke. Per car, so a friend's car can be read-only.
   - **Outputs:** Home Assistant topics, RealDash and the other bridges, for this car.
   - **Layouts:** this car's saved MFD layouts and automatic switching.
   - **Sharing:** who else can see this car
     ([ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md)).
2. **This gateway:**
   - **Role:** standalone, or client of a car's Brain.
   - **Network:** the per-car HTTPS name, Wi-Fi, remote access.
   - **Storage, power** (sleep, coming back after ignition on), **updates.**
3. **Display** (shared by every app): units, theme, text size, light and dark.
4. **Account and sync:** sign in, devices, backup, export and import of car profiles.
5. **About:** version, the gateway's own health check, send diagnostic logs.

While moving, settings can be browsed but not changed ("Park to change").

## 5. Open questions

1. **Permissions per car or per app?** Recommend per car, with "same as my other cars" as the
   default when a new car is added.
2. **Display per device or per account?** Recommend per account with a per-device override (a
   head unit may want a larger text size than the phone).
3. **Car profiles without an account:** export and import only, or local-network sync between
   the owner's gateways? Recommend export and import first.

## Changelog

- 0.1 (2026-10-11): first draft from the owner's discussion of the gateway's role and settings.
