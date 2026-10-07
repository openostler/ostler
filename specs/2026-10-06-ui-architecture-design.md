---
title: "UI architecture — one head-unit-first UI for every vehicle, many vehicles and add-on devices — design"
area: specs
status: stable
version: 0.15
updated: 2026-10-07
depends_on: [specs/2026-10-06-platform-direction-design.md, CONSTITUTION.md, references/research/platform.md, references/research/ui/obd_apps.md, references/research/ui/diag_tools.md, references/research/ui/vehicle_data_model.md, references/research/ui/head_unit_ui.md, references/research/ui/generated_ui.md, references/research/ui/ovms_ui.md, references/research/ui/decode_pipeline.md, references/research/standards.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0023-passive-can-bitrate-detection.md, specs/2026-10-06-app-model-design.md, references/research/ui/app_model.md, references/research/driver_distraction_rules.md, references/research/app_teardown_speedometer.md, references/research/obd_telematics_apps.md, references/research/ui_audit_current.md, references/research/visual_design_direction.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-06-logs-at-scale-design.md, specs/2026-10-07-trip-sharing-design.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, references/research/trip_and_log_sharing.md]
summary: >
  Approved by the owner on 2026-10-06 (ADR-0016, ADR-0018). One UI generated from a per-vehicle capability manifest: head-unit-first layout classes with a driver-side rail and a persistent status strip, five destinations with Drive as a mode, Parked/Idling/Moving lockouts, a garage with an active-vehicle switcher, a vehicle → systems → function-areas tree that collapses for one-ECU cars, add-on devices (alarm, climate, cameras, tracker, relay box) that register into slots, five safety tiers with action categories as a second axis (ADR-0033) and an add-on device render class for our own add-ons, VSS canonical signal paths (VSS 6.1), an open-standards plan per phase, a read-only decode pipeline with a generic OBD-II fallback, and a phased migration that starts with cheap seams. Amended for the node/brain direction (ADR-0032, ADR-0033): the landing screen follows the driving state, Security is present with any node, Maintenance runs Parked or Idling, phones approve Tier 2–3 over local links, and cross-vehicle replay switches pack and manifest. Amended (v0.5) with the app model: one shell, features as apps declared by a manifest, core apps in the platform repo, optional apps from their own repos, never separate PWAs, nothing built before U1. Amended (v0.7) with the owner's networking answers: the Network core app absorbs More → Devices (one page for devices, links, role holders, uplinks, remote access and pairing; a read-only peer view on every device's own page; ADR-0037, ADR-0038), and the device manifest gains `board`, `roles`, `transmit` and `items` with `origin` and `status`; the signal's Home Assistant entity category is renamed `ha_category`. Amended (v0.8) with the owner's power-state and product-family answers (ADR-0039, ADR-0040): §3.8 is accepted (one power state per device with honest Asleep, Waking and Kept awake badges, the Brain's state and queued actions in the Link chip, a brain-wake confirmation for remote requests only, queued actions with expiry and Cancel, a Power column and section on the Network page, "Needs the Brain" cards, manifest fields `power`, `runs_on`, `needs_brain`, `queueable`, `expires_max_s`); USB joins "reached via"; "Lite" reads Ostler Diagnostics. Amended (v0.9) with the owner's answers of 2026-10-06 (ADR-0039 and ADR-0037 Amendments): the brain product is Ostler Brain (was Hub), so the cards read "Needs the Brain"; device entries gain `memory` (`psram_kb`) and a `pbroker` role entry may carry `max_clients`, so an always-on add-on module can be the last parked-broker fallback. v0.11 (plan notes, 2026-10-06; the module-bus spec's owner answers): the Network page gains the owner action Remove device, the only way to clear a stale transmit-gate claim; an approval is confirmed first and the grant challenged and signed after; a queued action is offered only when the target checks in before it would expire. v0.12–v0.13 (§12, amendment of 2026-10-07, approved by the owner on 2026-10-07 ("approve all"); §12): U2 lockouts (driver-facing means any screen the driver can see or reach, Idling needs Park evidence, a per-trip head-unit Passenger view limited to UK reg 109 content with Open on phone for the rest, six new Moving templates with limits, task depth ≤ 3, a "Using Ostler while driving" page, a legal check before U2 ships); Logs renamed Trips with aliased routes, a two-tier trip summary index over the full recording, trip list, map-first trip detail, playback, Statistics, Records and gated Sprints, End trip now, Exclude from stats, Export all and no score; Drive layouts as data (RealDash model), one-screen Drive mode at every head-unit class with a new HU-5 800×480 class; the Add-ons catalogue at More → Add-ons with an empty-state Home card. v0.15: the DMD-round amendments §13–§15 (v0.14), approved by the owner on 2026-10-07 ("approve all", DMD round): §13 the Trips share sheet (audience first, an L0–L4 level ladder in plain language, a "what they will see" preview rendered from the real output, expiry and link controls, privacy-zone notes), "Get help with this fault" in Diagnose, "Ask for help decoding" in Decode lab, More → Places for privacy zones and the ends trim, and a map-theme setting independent of the app theme; §14 message alerts, applied into §12.1 (sender and app with Play and Reply, up to five canned replies, an opt-in first-line preview only for messages that arrive while parked, rate limits, three legal-check questions); §15 Drive modes and editing (several Drive modes with a strip chip and faces, Dashboard the head-unit default, everything editable with safety items that move but never go, More always in the five-slot rail, Park to edit, Reset layout always reachable).
---

# UI architecture — design

**Status:** approved by the owner on 2026-10-06; the answers are in §11 and locked by
[ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md) and
[ADR-0018](../decisions/adr-0018-ui-architecture-decisions.md). Each migration phase (§10) still
gets its own spec. It refines the IA row of the
[platform direction](2026-10-06-platform-direction-design.md) and changes none of its decisions.
The evidence is the seven notes in [`references/research/ui/`](../references/research/ui/), listed
in `depends_on`. **Amended on 2026-10-06 (v0.4)** for the node/brain direction
([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md)) and action categories and
approvals ([ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)); the spec
stays approved and the changes are listed in the changelog. **Amended on 2026-10-06 (v0.5)**
with the app model (§3.6, [app-model spec](2026-10-06-app-model-design.md), draft).
**Amended on 2026-10-06 (v0.7)** with the owner's networking answers: §3.7 (Network page,
peer view and cluster view), the manifest fields of §5.1 and the device pages of §6
([ADR-0037](../decisions/adr-0037-role-holders-and-handover.md),
[ADR-0038](../decisions/adr-0038-mesh-car-to-car-and-off-grid.md)).
**Amended on 2026-10-06 (v0.8)** with the owner's power-state and product-family answers:
§3.8 (asleep, waking and queued actions) is accepted
([ADR-0040](../decisions/adr-0040-power-states-and-wake.md),
[ADR-0039](../decisions/adr-0039-product-family-diagnostics-guardian-hub.md)).
**Amended on 2026-10-06 (v0.9)** with the owner's Brain rename and parked-broker answers: the
brain product is **Ostler Brain** (was Hub; ADR-0039 Amendments), and §5.1's device entries
gain `memory` and a `pbroker` role's `max_clients` (ADR-0037 Amendments); the spec stays
approved.
**Amendment of 2026-10-07 (v0.12), approved by the owner on 2026-10-07 ("approve all")
(v0.13)** in §12: U2 lockouts and Passenger view, Logs renamed Trips, Drive layouts as data
with a new HU-5 class, and the Add-ons catalogue. Where §12 differs from §1–§11, §12 wins;
the spec stays approved.
**Amendments of 2026-10-07 (DMD round, v0.14), approved by the owner on 2026-10-07 ("approve
all", DMD round) (v0.15):**
[§13](#13-amendment-2026-10-07-dmd-round-approved-sharing-screens-places-and-map-theme) adds
the per-trip share sheet, the help entry points in Diagnose and Decode lab, More → Places and a
map-theme setting; §14 changes the message alerts (applied into §12.1); §15 adds Drive modes
and editing. Where §13–§15 differ from §1–§12, they win; the spec stays approved.

## 1. Context and goals

**Today.** `ui/src/App.tsx` is one 900 px column: a 56 px header with up to seven controls and a
bottom bar of eight public tabs (Drive, Faults, Inputs, Outputs, Settings, Utilities, Logs,
Analysis) plus three admin tabs (`ui/src/screens/registry.ts`). It knows one pack (`GET /pack`, a
process-wide `active_pack()`) shaped as the D2 `layout.json`, with custom views via
`ui/src/vehicles/registry.ts`. Nothing reads speed or gear, and faults pop up as a modal.

**Goals (the owner's brief).** (1) Every vehicle: generic OBD-II (one ECU), multi-ECU K-line cars
like the D2, modern CAN/UDS, pre-OBD, with no vehicle-type checks in screens. (2) More than one
vehicle, with a garage and a switcher. (3) The node's alarm (the guardian variant for hidden security; alarm outputs only later via an I/O module, ADR-0033), the AC/HEVAC controller
(a separate ESP32 project we only talk to), cameras, the tracker and the relay box, without clutter.
(4) Head-unit first, still good on phone, tablet and desktop. (5) Generated UI evaluated, not
assumed (§5.3). (6) A dev pipeline for detecting and decoding cars (§8).

**Non-goals.** Media, CarPlay/Android Auto, radio and wheel controls stay on a media head unit
(direction spec). No new write path to any car. No cloud dependency.

## 2. Principles

1. **Generate from the manifest.** Render what the capability manifest (§5) declares, nothing else;
   screens never name a pack, module, device or vehicle type.
2. **Collapse a level with one member** (vehicle, system, camera). Data and URLs keep every level.
3. **Honest states.** A missing value is never zero, an unscanned system is never OK, `candidate`
   and stale look different, and nothing unsupported is greyed out as if it were for sale.
4. **Head-unit first.** Design at 1024×600 (76 px targets, 24 px gaps, 32/24 px text, the 2 s / 12 s
   glance rules), then relax for phone and desktop. Driving state gates the UI, not discipline.
5. **Safety travels with the action.** The server enforces tier, driving state and remote rules on
   every path; the UI only adds friction.
6. **The rule of two.** Generated tier with `generic_obd2`, `DevicePack` with the second device,
   garage with a second real vehicle; until then only cheap seams.
7. **Calm instrument.** ISO 2575 colours for telltales only, a word with every icon, motion only for
   red alarms, night dark automatically.

## 3. Information architecture

### 3.1 Layout classes

Chosen by aspect and height, not width alone; a kiosk flag (`?display=headunit&side=left|right`)
overrides detection because head-unit browsers report odd DPIs. The 900 px cap stays only on phone.
On phones the same app ships as a PWA packaged in a native wrapper (Capacitor) for Bluetooth and
local Wi-Fi to the node, especially on iOS (ADR-0032); the layout classes are unchanged.

| Class | Trigger | Shell (px) | Content area |
|---|---|---|---|
| **HU-7** 1024×600 | landscape, height ≤ 640 | rail 96 · strip 56 | 928×544: Home 2×2 cards; Drive mode 3×2 tiles, values ≥ 56 px |
| **HU-9/10** 1280×720 | landscape, height ≤ 800 | rail 112 · strip 64 | 1168×656: Home = vehicle card 40 % + 2×2; Diagnose = list 380 + detail |
| **HU-wide** 1920×720 | aspect ≥ 2.4 | rail 112 · strip 64 | vehicle pane 520 (always on) · main 768 · secondary 520 (camera, mini-timeline); a page widens main over secondary |
| **Phone** 360–430 × 780–930 | portrait, width < 600 | strip 48 · bottom bar 72 + safe area | ~393×730, one column; Drive mode 2×3 tiles |
| **Tablet** | width ≥ 600, height > 800 | rail 88 · strip 56 | two panes (list 360 + detail) |
| **Desktop** | width ≥ 1200, fine pointer | rail 88 with labels · strip 56 | two or three panes; denser type when Parked |

### 3.2 The persistent status strip

One row, never scrolls. Each chip is ≥ 48 px tall, pairs icon and word, and opens a sheet. Left to
right by severity:

| # | Chip | Content |
|---|---|---|
| 1 | **Vehicle** | active vehicle name; only when the garage holds > 1 vehicle (§4.1) |
| 2 | **Worst telltale** | highest active warning, ISO colour, count; replaces the fault modal while Moving |
| 3 | **Link** | connection-ladder rung + the system holding the ECU session (§4.5) |
| 4 | **REC** | logging state; tap → Logs |
| 5 | **Security** | Disarmed / Armed / Alerting, or the tracker fix in Map mode (§6) |
| 6 | **Device slot** | climate setpoint + fan, or a live-camera chip; one on HU-7/phone, two on HU-wide |
| 7 | **12 V** | from the vehicle, else the node |
| 8 | **Clock** | |
| 9 | **Mark** | one-tap flag, the one action safe at any speed |

The phone keeps chips 2–5 and 9; the rest move to Home cards. Module select moves to Diagnose,
Rewind to Logs, the cog to More. Service mode and replay add a strip badge.

### 3.3 Driver-side rail versus bottom bar

Landscape classes use a **vertical rail on the driver's side**: wide-screen production systems keep
status and controls nearest the driver, and a bottom bar wastes the short axis of a 600 px screen.
The side comes from the vehicle's `driver_side` (the D2 is RHD), with the kiosk flag as override.
Until the garage holds it per vehicle (§4.1, U6), it is the pack layout's `driver_side`
(`"left" | "right"`, `schemas/layout.schema.json`); absent means left.
Portrait uses a **bottom bar** for thumb reach (five items at 72–86 px fit 393 px). The rail holds
only the five destinations, plus a Drive-mode button on head units, so it never scrolls.

### 3.4 Five destinations

`Home · Diagnose · Logs · Security (Map) · More`, a hard cap of five (direction spec). Destinations
register into the shell with `slot`, `order`, `requires` and `trust`, as OVMS pages do, so the nav
is built, not hard-coded.

| Destination | Contents | From today |
|---|---|---|
| **Home** | Zero-layer cards (§5.4): vehicle card (silhouette + health), role tiles, warnings, last trip, parked security/location, device cards, the "unknown vehicle" banner, a large **Drive** button | Drive's health strip |
| **Diagnose** | Identity bar · **Scan all** · system list (§4.2) · per system **Overview · Faults · Live · Tests · Procedures · Settings** · fault → related live data and tests | Faults, Inputs, Outputs, Settings, Utilities, ModuleSelect |
| **Logs** | One timeline: drives, parked periods, alarm events, faults, notes, scan reports. **Analysis** is the session detail; replay and Rewind live here | Logs, Analysis, Rewind |
| **Security** | Alarm state, events, tracker map, geofences, clips (Parked only). Present with any node: every node has GPS and a basic alarm; the guardian variant adds tamper and IMU | — |
| **More** | Garage, **Network** (devices and device pages, links, role holders, uplinks, remote access, pairing; §3.7), Integrations (MQTT/HA, OVMS, OwnTracks), Preferences, Privacy, **Developer** (Decode mode, Label, Coverage, Docs), About (service-mode entry) | cog, admin tabs |

The D2 keeps its NanoCom words as **pack labels** over the canonical areas (Live → Inputs, Tests →
Outputs, Procedures → Utilities). An area with no items disappears; one the pack declares but has
not mapped stays visible as `untranscribed`.

**Landing screen follows the driving state** (amendment 2026-10-06). The five destinations stay;
only the screen the app opens on changes: **Drive mode when Moving**, **Security when Parked and
armed**, **Diagnose in service mode**, otherwise Home. A manual choice holds until the state
changes.

### 3.5 Drive mode, driving states and service mode

**Drive mode** is full-screen, not a tab: role tiles plus pack extras, the strip and a back target.
It opens from Home, and automatically on entering Moving on head-unit classes.

**Driving state** is computed by the platform, so the server can enforce it, from vehicle speed (any
system in session), then GPS speed (the node's GPS, a guardian variant or a u-blox), then proven gear/handbrake signals.

| State | Rule | Allowed | Locked ("Available when parked") |
|---|---|---|---|
| **Parked** | speed 0 for > 5 s and engine off, or handbrake/neutral where known | everything its tier allows | — |
| **Idling** | engine running, speed 0 | reading, Logs, cameras, text entry; **Maintenance** (Tier 1: clear codes, reset service interval; ADR-0033); Comfort and Security arming; Tier 2 only if the action declares `engine_running_ok` | other Tier 1 actions, Tiers 3, 4; video other than cameras |
| **Moving** | > 5 km/h for > 2 s; leave below 2 km/h for 3 s | Drive mode, telltale sheet (≤ 30 characters a line), Mark, reverse/low-speed camera, climate setpoints, Comfort actions (driver-safe UI) and Security arming (ADR-0033) | Tiers 1–4 other than Comfort and arming, text entry, Docs, Analysis, replay scrubbing, clip playback, system switching, Decode and service mode (auto-exit), lists > 6 items or > 2 levels |

**Unknown speed** counts as Moving on head-unit classes. A phone is a passenger device we cannot
verify: reading stays open and actions keep today's "vehicle stationary" precondition. The server
re-checks the state from the node on every action, whichever device asked. K-line
carries one session at a time, so in a SLABS session the Td5 speed is absent and GPS covers it.

**Service mode** merges admin and Experimental: a long-press on the version line in More → About
plus the server password; while on, a thick coloured frame round the viewport, a strip badge,
Experimental items and Decode mode. It is refused, and exits, when Moving.

### 3.6 One shell, apps by manifest (amendment 2026-10-06, v0.5)

The UI is **one shell** (launcher, status strip, driving states and landing, auth, the data
stream, the app registry, the safety-gate client and every approval surface) that hosts
features as **apps declared by a manifest**: requirements against the capability manifest,
slot contributions, the actions they use with category and tier, a driving rule per view
(while Moving only shell-drawn templates) and hosts. **Core apps** (Diagnose, Logs, Security,
Network, plus Decode lab in service mode, §8.4) stay in the platform repo and fill the
destinations above; **optional apps** (Cameras, Social, add-on module apps) may ship from their own repos, bundled at
build time or declarative-only. Apps are **never separate PWAs**, never draw approvals and never
reach the car except through the gate (§7). **Nothing is built before U1**; U1 only leaves the
seams. Detail and open questions: [app-model spec](2026-10-06-app-model-design.md) (draft);
evidence: [app model research](../references/research/ui/app_model.md).

### 3.7 Network page, peer view and cluster view (accepted 2026-10-06)

*Accepted by the owner on 2026-10-06 (v0.7): Network is a core app that absorbs More →
Devices. Roles and handover:
[ADR-0037](../decisions/adr-0037-role-holders-and-handover.md); mesh links:
[ADR-0038](../decisions/adr-0038-mesh-car-to-car-and-off-grid.md); evidence:
[cluster view research](../references/research/cluster_view.md).*

**More → Devices is now More → Network.** One page for the whole cluster, filled by the
Network core app (app-model spec §3), with these sections:

| Section | Shows | Source |
|---|---|---|
| **Devices** | every paired device: name, kind and variant (node, guardian, brain, add-on), model, firmware and manifest `etag`, IPv6/IPv4 addresses and mDNS name, "reached via" (USB, T1S segment, Ethernet, Wi-Fi, BLE through the phone), health and last seen, an **Open device page** link; tap → the device page (More → Network → *device*, formerly More → Devices → *device*, with add-on app contributions) | retained manifests and `status` (ADR-0037 §3) |
| **Transports and links** | T1S segments (PLCA on, coordinator, node count, CRC errors), Ethernet, Wi-Fi (AP clients, RSSI), BLE, LoRa or other mesh links (ADR-0038; a mesh is its own subnet or network and a remote path, Read and alerts only), CAN fallback; health per link | device link counters |
| **Roles** | each single-holder role (transmit gate per bus, parked broker, time source, PLCA coordinator per segment, uplink manager): holder, since, term, candidates in order, last handover and why; "No holder" in amber, "No gate for this bus" where it applies | role claims (ADR-0037) |
| **Uplinks and metering** | sources, Auto or pinned, failover order, metered flag, budget and usage (ADR-0028 §3–4) | uplink policy API, byte counters |
| **Remote access** | the tiers in use (LAN, Tailscale, Ostler Cloud, HA Cloud) and the "Remote control enabled" badge (ADR-0033 §6) | install config, read-only |
| **Certificates and pairing** | device certificates (issuer, expiry, fingerprint), pairing a new device, revoking one, nearby unpaired Ostler devices shown as "nearby" with no data (ADR-0029 §6) | local CA or pairing store |

- **Data is decentralised; the view is built.** Any full-app host (brain, cloud, phone)
  builds the cluster from each device's published manifest, status and role claims; no
  device holds a master list. The brain builds it in the car, the phone builds it on Ostler
  Diagnostics alone (through the node's peer table over BLE or the AP), the cloud builds it remotely from the
  opt-in bridge.
- **Authority is not.** Nothing on this page approves a car action. Pairing, revoking and
  uplink changes are owner-role operations on the device that holds them; car actions stay
  in their destinations and are checked by the gate that executes them (§7, ADR-0033 §3).
  Over a remote path the page is read-only (ADR-0033 §6).
- **Honest states.** A device not heard from shows its age, never "OK"; when the host's
  inputs are stale the whole view is read-only with an age banner (research §1).
- **Driving state.** Parked and Idling: full. Moving: locked ("Available when parked"); a
  lost role holder appears only as a row in the Link chip's sheet (§3.2), never as a new chip.

**Every device's own page shows its peers.** The local web page each device hosts
(ADR-0028 §7, ADR-0032 §6) gains a small, read-only **Network** section: the peers it sees
by mDNS (`_ostler-mod._tcp`) and on its broker, each with variant, firmware, health and the
roles it claims, and a link to that peer's own page. Opening a hidden guardian's page shows
the diagnostic node, the relay box, the brain and so on. It never acts on a peer; each peer's
own page acts under its own gate. Shape: one shared `peers` view (a subset of the Network
page's Devices and Roles rows), served by the firmware; the
[app-model spec §12](2026-10-06-app-model-design.md#12-the-network-app-and-device-pages-accepted-2026-10-06)
sets how it relates to the shell (it stays outside the app model).

**Plan note (v0.11, 2026-10-06): Remove device.** With the owner's answers to the
[module-bus message spec](2026-10-06-module-bus-messages-design.md#17-owner-answers-2026-10-06)
(item 13), a stale transmit-gate claim never expires: any claim on a gate's bus keeps the
gate listen-only until it is released. Each device page in Network therefore gets an
owner-only **Remove device** action, on local links only (never over a remote path). One
confirmation names what changes: "Remove Node 2? It is unpaired and its retained data is
deleted. K-line (kline-diag) becomes writable by Node 1." Removal revokes the device and
purges its retained topics on every broker (spec §7.2, §13). The Roles section makes the
remedy one tap where it applies: "Gate silenced by Node 2's claim · Remove Node 2". A gate
conflict seen on the wire (`by: "bus"`) shows **Acknowledge** instead. On Ostler
Diagnostics alone the phone app offers the same action over BLE or the node's AP. Not built
yet: the Network page UI and the Brain's remove API are open TODO items.

**Changes made (v0.7):** §3.4's More row reads "Network" for "Devices"; §6's "More → Devices"
pages are "More → Network → *device*"; the capability manifest (§5.1) gains `board`, `roles`,
`transmit` per bus and `items` with `origin` and `status` (ADR-0037 Consequences, ADR-0032
Amendments B).

### 3.8 Asleep, waking and queued actions (accepted 2026-10-06)

*Accepted by the owner on 2026-10-06 (v0.8). Decision:
[ADR-0040](../decisions/adr-0040-power-states-and-wake.md); product names:
[ADR-0039](../decisions/adr-0039-product-family-diagnostics-guardian-hub.md); evidence:
[power states research](../references/research/power_states.md).*

**Words and badges.** Every device shows one power state from its retained `power` topic,
always icon plus word: **Awake**, **Asleep** (with last seen and how it wakes: "wakes on
wire", "checks in ≈ 6 min"), **Waking…** (elapsed seconds against the expected time),
**Kept awake** (by whom, until when), **Shutting down**, **Off**, and **Offline** (amber,
only for an unexpected loss; **Off** is the power owner's report for a cut device, so a device
that is off and unreachable reads Off, never Offline — note of 2026-10-06, as built in the
Link chip). An asleep device keeps its last values in stale grey with their
age, never zero and never "Unavailable" (§2 honest states).

**Status strip (no new chip).** The brain's state lives in the **Link** chip (§3.2):
"Brain asleep" as a rung note, "Waking Brain · 12 s" with a progress ring, and a small count when
actions are queued ("1 queued"). Its sheet lists queued actions (name, target, expires at,
**Cancel**), the leases this user holds, and refused wakes with their reason. Security and
the alarm never wait for the brain, so the Security chip is unaffected.

**Confirmations.** Drawn by the shell only (app-model spec §2).
- **Waking a module** (`needs_brain: false`, ADR-0040 §5): no extra confirm; the button shows
  "Waking Relay box…" then the action's own tier friction (§7).
- **Waking the brain:** **remote** requests show a sheet, "This needs the Brain. Wake it? About
  30 s · uses about 30 mAh (today: 180 mAh left) · battery 12.5 V", with **Wake and run**,
  **Cancel** and the quota ("2 of 6 remote wakes left today"); it cannot be skipped. Local
  requests wake the Brain without a sheet, showing "Waking Brain…" on the button (ADR-0040 §7). A
  "Don't ask again" choice is stored per user and device and honoured on local links only, so
  it never removes the remote sheet.
- **Tier 2–3:** wake first, then the normal approval (§7.2); approvals never queue.
- **Refusals are honest:** "Brain not woken: battery 11.9 V", "Brain failed to start; locked for
  1 h", "Limit reached: 6 wakes this hour".

**Queued actions.** The button reads "Queued · runs when the Brain is ready · expires 14:35 ·
Cancel". *Plan note (v0.11, module-bus spec §9, owner answer 2):* the shell offers to queue
an action for a `check_in` target only when the target's `power.next_checkin` comes before
the latest allowed expiry; otherwise it says when the target next checks in and offers
nothing to queue. Outcomes: Done; **Expired**; Cancelled; Refused by *device* (the executing gate's
reason); **State changed** (the driving state moved; ADR-0040 §5). Check-in targets say
"Runs when Relay box next checks in (≤ 10 min)".

**Network page (§3.7).** The Devices section gains a **Power** column: state, class (always,
wakeable, check-in, none), wake path, estimated current, lease holders and a **Wake** button
where the user's role allows it. A **Power** section adds today's energy ledger against the
budget, the 12 V floors in force, the node's parked mode (ready or deep) and a wake log (who
woke what, when, why, cost, outcome). Read-only over remote paths except Wake under the quota.

**Landing and brain-only views.** With the brain asleep, Home and Security render from the
node's retained data. A view that needs the brain (full Logs, replay, clips) shows a "Needs
the Brain" card with **Wake** instead of disappearing; on Ostler Diagnostics alone (no Brain
fitted) it is absent, as today. While Moving the brain is held by the ignition lease, so no wake prompt
appears in Drive mode.

**Phone and Diagnostics standalone.** With Ostler Diagnostics alone the phone talks to the
node only; no Brain prompt exists. When the node is in **parked-deep** the phone cannot reach it (no BLE or AP): the app
says "Node asleep (deep) · wakes on ignition, door or motion · last seen 3 h" from cached or
cloud data, and offers nothing else.

**Manifest (§5.1):** each `devices` entry gains
`"power": {"class": "wakeable", "wake_paths": ["wake_wire"], "parked_ma": 0.2}`; each
`actions` entry gains `"runs_on": "relay1"`, `"needs_brain": false`, `"queueable": true` and
`"expires_max_s": 600` (Tier 2+ is never `queueable`).

## 4. The vehicle model in the UI

### 4.1 Garage and active-vehicle switcher

- **A vehicle id (`vid`) that is not the pack id**, since two D2s share one pack. `garage.json`
  (state dir) holds `active` and per vehicle: `vid`, `pack`, name, `driver_side`, transport,
  attached devices, units and a VIN **fingerprint** (§4.4).
- **One active vehicle** in the UI, remembered per client as a convenience; the server's
  `garage.active` is the truth. Inactive vehicles show a last-known summary with its age.
- **One live link per port.** Activating B on a port held by A stops A's sources first (released on
  K-line); K-line traffic is never interleaved.
- **Switcher:** the strip's Vehicle chip opens a sheet of vehicle cards; More → Garage edits them.
  With one vehicle neither appears. Every session carries `vid` from U0.
- **Replay across vehicles (U6, amendment 2026-10-06).** Whole-app replay stays
  ([ADR-0010](../decisions/adr-0010-replay-notes-audio-motion.md)). Replaying another vehicle's
  session switches the UI to that session's pack and capability manifest, and switches back to
  the active vehicle on exit; the active vehicle and its live link are untouched. Every session
  records its **pack id, pack version and manifest `etag`**, so replay renders what was recorded.
  Logs replay covers drives, **parked periods and alarm events** alike.

### 4.2 Vehicle → systems → function areas

Vehicle (garage) → Diagnose: identity bar · Scan all · Systems → *System* → Overview · Faults ·
Live · Tests · Procedures · Settings, plus fault → related live items and tests. Collapse rules:

| Live systems | Behaviour | Example |
|---|---|---|
| **1** | No system level: Diagnose opens on the function areas, the system name is a subtitle. Several OBD responders (7E8/7E9) are a **source tag** on each code or value | generic OBD-II, one-ECU pre-OBD |
| **2–12** | A flat list with a status chip and fault count per row; the list pane beside detail on head units, a list screen plus a compact "current system" switcher on phones | the D2 (6), most K-line cars |
| **> 12** | Grouped by domain (powertrain, chassis, body, comfort, safety), fault-free groups collapsed, search; topology only if the pack declares bus wiring | modern CAN/UDS |

The rule lives in one place: `multiSystem = systems.filter(s => s.live).length > 1`. On K-line there
is no gateway, so the pack lists plausible systems per variant and the user may mark a probed one
**Not fitted**.

### 4.3 Scan all and its honest states

One vocabulary across scan, system list and reports: `Not scanned` · `Scanning` · `OK` · `Faults n`
· `No response` · `Not fitted` · `Not supported yet`, each with its age; the last two separate
"absent from the car" from "absent from the tool". K-line scans run one system at a time (establish
→ read → release) with per-row progress and Stop. A scan saves a **report** to Logs (identity
masked, every row, codes with freeze frame, key values **with confidence**, every action), paired
before/after repair and exported as HTML and JSON; uploads are opt-in.

### 4.4 Identification and fallbacks

Tried in order, stopping at the first confident match:

1. **Read identity:** OBD Mode 09 VIN, CALID, ECU names; UDS `F187`/`F189`; KWP `1A`.
2. **Decode the VIN on the device,** in memory, against a bundled WMI/model-year table. Only `{make,
   model_year, region}` and a masked form (`SAL…****`) leave that function. The VIN is **never
   recorded by default and never leaves the device** (an opt-in for security decoding work keeps
   identity replies in raw recordings on the device only; ADR-0036): never logged in clear,
   put in fixtures or uploaded; the garage keeps an HMAC under a
   device-local secret to recognise the car again. Online lookups (e.g. NHTSA vPIC) are opt-in and
   masked.
3. **Match pack `detection`:** WMI + year, CALID/ECU-name or `F187` patterns, K-line probes.
4. **Ask only what changes the topology** (make → model → engine/gearbox/options), never a protocol
   list.
5. **Fall back** to `generic_obd2` on an OBD car, or "choose your vehicle / start a pack".

### 4.5 The connection ladder

`No adapter → Adapter (type, quality hint) → Bus (K-line init / CAN bitrate / ELM protocol) → ECU
session: <system> → Data flowing`, plus 12 V. The chip shows the highest rung and the session
holder; the sheet names the failed rung and what to try. Values go stale-grey when a rung drops.
Launch auto-connects with the active vehicle's adapter.

## 5. Capability manifest

### 5.1 Shape

Data the UI renders. `GET /pack` grows into it; later `GET /vehicles/<vid>/capabilities` (`etag`).

```jsonc
{ "schema": 1,
  "vehicle": { "vid": "d2-green", "pack": "lr_d2", "name": "Discovery 2 Td5", "variant": "D2a",
               "identity": { "source": "kwp_1a|obd_09|manual", "vin_masked": "SAL…****" } },
  "systems": [ { "id": "td5", "name": "Engine (Td5)", "category": "powertrain", "live": true,
                 "transport": { "bus": "kline", "init": "fast", "address": "0x13", "protocol": "kwp2000" },
                 "areas": { "live": "Inputs", "tests": "Outputs", "procedures": "Utilities" } } ],
  "signals": [ { "id": "td5.coolant_temp", "system": "td5", "group": "Temperatures",
                 "metric": "Vehicle.Powertrain.CombustionEngine.EngineCoolant.Temperature",
                 "class": "temperature", "unit": "Celsius", "dec": 0, "span": [-40, 130],
                 "normal": [80, 100], "confidence": "proven", "ha_category": "primary",
                 "rate": { "parked": 0, "ignition": 1, "driving": 5 } } ],
  "dtc_sources": [ { "id": "td5", "system": "td5", "kind": "kwp_18", "clear_action": "td5.clear_faults" } ],
  "actions": [ { "id": "slabs.compressor", "system": "slabs", "safety": "actuator", "tier": 2,
                 "confirm": "preconditions", "status": "verified", "states": ["parked"], "remote": false } ],
  "devices": [ { "id": "node", "kind": "node", "variant": "diag-port", "transport": "mqtt",
                 "board": "esp32-s3-devkitc", "memory": { "psram_kb": 8192 },
                 "roles": [ { "role": "pbroker", "max_clients": 5 }, { "role": "plca", "scope": "t1s0" } ],
                 "transmit": [ { "bus_id": "kline-diag" } ],
                 "items": [ { "id": "imu", "kind": "imu", "origin": "detected", "status": "ok" },
                            { "id": "tacho", "kind": "pulse", "origin": "config", "status": "no_signal" } ],
                 "signals": ["node.alarm.state", "node.gps.fix"], "actions": ["node.arm"],
                 "slots": { "strip": "security", "destination": "security" } } ],
  "views": [ { "id": "body", "slot": "home", "type": "lr_d2/body" } ], "x": { "util_lids": [] } }
```

Rules: **field config lives on the signal** (`dec`, `class`, `span`, `normal`, `limits`), so views
list only ids. **`confidence` stays two-valued** (CONSTITUTION): a J1979 decode is `candidate` per
car until a car result exists. **`class`/`ha_category` borrow Home Assistant's `device_class` and
entity categories** (`diagnostic` collapses by default); the field is `ha_category`, not
`category`, so it never collides with an action's `category` (ADR-0033). A system's
`category` (`powertrain`, …) is its domain group (§4.2). **Device entries** (§6) carry the
hardware facts the Network page shows: `board` (the compiled-in board profile), `roles` (roles
the device can hold, with scope; ADR-0037 §2; a `pbroker` entry may carry `max_clients`, the
mTLS sessions its parked broker admits, at most 5 until the bench proves more), `memory`
(`psram_kb`, the PSRAM fitted, from the board profile; an add-on module is a parked-broker
candidate only when it lists `pbroker`, its `power.class` is `always` and `psram_kb` ≥ 2048,
ADR-0037 Amendments 13–14), `transmit` (the car buses whose transmit gate it
holds, by `bus_id`) and `items` (each sensor, receiver or I/O point, with `origin` = `board`,
`detected`, `harness` or `config` and `status` = `ok`, `absent`, `fault`, `no_signal`,
`unverified` or `refused`; ADR-0032 Amendments B1; *2026-10-06: `unverified` added, as the
node publishes it for its K-line item until an init succeeds (sensor-detection §2); it is
drawn as "Not verified yet", neither ok nor a fault*). **Unknown types degrade** to a generated
tile; `schema` is versioned. **D2-only leftovers stay under `x`.** **`unit` is a key copied verbatim from
the pinned VSS 6.1 `units.yaml`** (`Celsius`, `km/h`, `kPa`), checked by a test (ADR-0016).

### 5.2 Generated by the platform from the pack

Packs do not hand-write the manifest. The platform builds it from `ModuleSpec` (systems), the signal
store (signals), `dtc/` and `FaultReader`s (DTC sources), `Command`s (actions), `layout.json`
(views) and a short `vehicle.json`. `generic_obd2` builds the same shape **at connect time** from
the support bitmaps and Mode 09: the first need for a re-fetchable manifest.

### 5.3 Three rendering tiers

Generated UI is adopted, bounded. Each **slot** (`home`, `drive`, `system:<id>`, `security`,
`device:<id>`, `more`) is filled by one pure function:

1. **Generated:** `generateViews(caps, slot)`. A system page is its signals by `group`, card by
   `class` (number → tile, gauge with `span`; binary → chip; enum → text), actions by tier, DTCs
   from `dtc_sources`. Home and Drive come from roles (§5.4).
2. **Pack-declared:** a `views` entry **replaces** the generated view for its slot (no merge, so it
   stays predictable). This generalises today's `layout.drive`.
3. **Custom component:** `type: "<pack>/<kind>"` via the existing `registerViews`; with nothing
   registered, the slot falls back to tier 1.

All three emit plain view data into one renderer, so `generateViews()` is snapshot-tested without
React. **Not adopted:** a remote layout server, runtime-composed or model-composed screens, and
user-arranged dashboards; the last may come later as a per-vehicle diff over tiers 1–3, never a
fork.

### 5.4 Home built from roles

Roles in fixed order: **speed, rpm, coolant, battery, fuel**, then **health** (MIL/DTC count,
readiness where it exists), then up to N pack extras (the D2 boost tile). Per role the best source
of that `metric` wins: vehicle over add-on, `proven` over `candidate`, fresh over stale, then
manifest order. Registry fallbacks: fuel → range → consumption; speed → wheel speeds → GPS. No
source shows "Not available on this car", never zero. The D2 has no decoded fuel level, so Home uses
the derived economy figure, marked `candidate`.

### 5.5 The OVMS lesson

OVMS solved generic-versus-specific inside the module (one metric tree, a page registry with a
vehicle menu) but never sent capabilities over the wire: its capabilities message is a stub and the
Android app branches on `car_type` dozens of times, so users meet "unsupported operation" ([OVMS UI
§6](../references/research/ui/ovms_ui.md)). Therefore **capabilities reach the UI as data, and
screens never test a vehicle type.** The literal guard (`ui/src/vehicles/literalGuard.test.ts`)
extends to "no pack, module or device ids outside `ui/src/vehicles/`". We also copy OVMS's opt-in
shared page templates (ECU list, live table, 12 V monitor, TPMS) and named hook slots (header, body,
footer on every page).

### 5.6 Canonical signal namespace (decided: ADR-0016)

[Vehicle data model](../references/research/ui/vehicle_data_model.md) makes VSS paths canonical;
[generated UI](../references/research/ui/generated_ui.md) and [platform
research](../references/research/platform.md) prefer OVMS names. **Decided: the `metric` value is a
COVESA VSS path, and OVMS, Home Assistant and OBDb names are generated aliases** in one platform
registry (`metrics.json`: VSS unit, display units, OVMS alias, HA `device_class`/`state_class`, OBDb
`suggestedMetric`, default span, Home role). Extensions live in a small overlay `Vehicle.Ostler.*`
(MIL, DTC count, readiness, ride-height counts); pack-private fields need no metric.

**Why:** the canonical tree must name every meaning on every vehicle class. OVMS is EV-shaped, with
no names for fuel level or much of the body, so ICE and pre-OBD cars would live in `x*` prefixes.
VSS covers powertrain, body and cabin, is maintained and OEM-backed, and its 6.0 removal of the
one-to-one OBD branch matches our "one meaning, many sources" model. **OVMS compatibility is kept:**
the OVMS topic tree is generated from the alias column. Drivers never see the long paths (the UI
keys on roles). Vendored `.vspec` files stay MPL-2.0. **Locked by
[ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md):** VSS pinned to 6.1; the
overlay `vss/ostler.vspec` is the single source; `src/openostler/metrics.json` is generated with
vss-tools (dev-only) and checked in CI; the OVMS alias table comes from OVMS `metrics_standard`
([OVMS reuse §6](../references/research/ovms_reuse.md)); QUDT, not UCUM; the extension branch is
`Vehicle.Ostler.*` (decided).

## 6. Add-on devices

A device is an entry in `capabilities.devices` with its own signals, actions and views, ids prefixed
by the device id (`node.armed`, `hevac.set_temp`). Devices contribute to **slots** and never
edit a pack layout; each kind may claim one strip slot and one destination or More → Network → *device* page (§3.7).
Device actions pass the same gate (§7). **The node and its variants come first**, each through the
**capability manifest its hardware publishes at boot** (ADR-0032): a diagnostic-port node declares
diagnostics and security; a hidden guardian variant declares tracking, IMU, tamper and arm state and
no diagnostics; absent sensors never appear. Every control in a node or add-on manifest declares
its category and tier (ADR-0033). **The second add-on device (HEVAC) triggers a `DevicePack` entry
point** (`openostler.device`) mirroring `VehiclePack`.

| Device | Strip | Home card | Page | Actions and gating |
|---|---|---|---|---|
| **Alarm** (every node; the guardian variant adds tamper, IMU and a backup battery) | Security: Disarmed / Armed / Alerting / Tamper | parked: state + last event | **Security**: state, events (filtered Logs), map | Security category: arming allowed while Moving, disarming Parked only. The node and guardian have no outputs; sirens, the car's native alarm or an immobiliser come only through a future I/O module, each with its own ADR (ADR-0033). Notifications work with the brain off and no cloud. Remote: reads plus arming and disarming the software alarm (audited, owner notified), per ADR-0033 §6; more only with the install override (§7) |
| **AC / HEVAC** (separate ESP32, its own API) | climate chip: setpoint + fan; HU-wide may add a bottom climate strip | cabin/ambient temps | More → Network → Climate | setpoints are `add-on device` actions (Comfort category) on our own device, not car writes (ADR-0018); allowed while Moving; local only (§7) |
| **Cameras** (go2rtc) | live-camera chip; REC shared | last clip (Parked) | Security → Clips (Parked); HU-wide secondary pane | reverse pre-empts the screen **only once a fast path exists**, assist-only until then; underbody/front live below 10 km/h; no playback unless Parked. **Future:** 360° surround view as another camera kind under the same rules (owner note, ADR-0018; own spec) |
| **Tracker** (every node; better antennas on the guardian variant) | in the Security chip (fix age) | location when parked (opt-in) | Security / Map | read-only; location stays on the device unless opted in (ADR-0009) |
| **Relay boards** (our own, later) | none by default | user-pinned channels | More → Network → Relays | each channel declares its category (Accessories) and tier, default Tier 2, Parked only, local only; interlocks on the device and the node gate; every car function a board switches needs its own ADR first |

With no add-on fitted nothing renders for it: no empty cards or greyed slots. Security is always present, because every node has GPS and a basic alarm.

**`add-on device` render class (ADR-0018, renamed by ADR-0033).** Formerly the `comfort` class;
renamed so it does not clash with the Comfort action category (§7); the manifest value is
`addon_device`. A device action may declare it only if it never writes to a vehicle ECU or bus (HEVAC setpoints, camera
switching). Such actions are allowed while Moving, are local only by default, and still pass
the gate. Anything that reaches the vehicle keeps
the tiers in §7. CAN transmit rules are in
[ADR-0020](../decisions/adr-0020-can-links-listen-only-by-default.md).

## 7. Safety gating tiers

The tier is derived by the platform from the existing `safety` vocabulary (`read | actuator |
service | gated`) and `confirm` levels in `commands.py`, never typed by a pack. One server gate
serves every path; the UI only renders friction.

| Tier | From | Examples | Gate | States |
|---|---|---|---|---|
| **0 Read** | `read` | codes, live data, ident, readiness | none; stale-grey on link loss | all |
| **1 Clear** | action flagged `clears` | clear DTCs (KWP `14`, OBD `04`), reset service interval | an **automatic snapshot** of codes, freeze frames and readiness to the logbook first; one confirm naming system and consequence ("Clear 3 codes from SLABS? Freeze frames will be lost"); an **extra warning for safety systems** (airbag, ABS, brakes) in the same confirm; re-read to verify; an **audit entry** (who cleared what); NRC `0x22` shown honestly | Parked or Idling for Maintenance |
| **2 Actuate** | `actuator` | lamps, relays, compressor, injector test | precondition checklist from live data, else ticked; ActiveTestBanner with Stop; auto-timeout; leaving stops it | Parked (Idling if `engine_running_ok`) |
| **3 Procedure** | `service` | bleed, height calibration, adaptive reset | step wizard, preconditions re-checked each step, 12 V floor, abort anywhere; typed confirm | Parked |
| **4 Code** | `gated` | coding, security access, airbag or calibration writes | **listed for honesty, never runnable;** the server refuses | none |

### 7.1 Action categories, the second axis (ADR-0033)

Tiers keep setting the safety rules (confirmations, parked-only, moving lockouts). **Roles grant
categories**, and each category is capped by its tier:

| Category | Examples | Tier | While Moving |
|---|---|---|---|
| **Read** | live data, faults, logs, location | 0 | allowed |
| **Comfort** | AC/heater, seat heaters, lights, windows, aux heater | 1 | allowed (driver-safe UI) |
| **Security** | arm/disarm, locks, find my car | 1 | arming allowed; disarming Parked only |
| **Accessories** | relay outputs, spotlights, winch, camera recording | 1–2, set per add-on | per add-on |
| **Maintenance** | clear codes, reset service interval | 1 | Parked or Idling only |
| **Actuator tests** | injector, wastegate, SLABS pump | 2 | Parked only |
| **Procedures** | bleeding, calibrations, adaptation resets | 3 | Parked only |
| **Coding** | ECU writes | 4 | disabled until each has its own ADR |

| Default role | Categories |
|---|---|
| **Owner** | all, up to Tier 3 |
| **Driver** | Read, Comfort, Security, Maintenance (+ Accessories if granted); no actuator tests |
| **Viewer** | Read only; location only if shared |
| **Mechanic** | Read, Maintenance, Actuator tests, Procedures; time-boxed |

The **head-unit kiosk session** (no sign-in) gets **Read and Comfort** only; clearing codes needs a
signed-in driver. Each add-on and node variant declares the category and tier of every control in
its manifest. **Drivers may clear codes**: clearing is made safe rather than restricted (the Tier 1
row above; [J1979 spec §5](2026-10-06-j1979-service-layer-design.md#5-mode-04-clear-dtcs-is-a-tier-1-maintenance-action)).

### 7.2 Phone approval and remote paths (ADR-0033)

- **Phones can approve Tier 2–3** when the phone is a paired device of a user whose role grants the
  category. Approval runs over **local links only** (the node's Wi-Fi AP, BLE, the in-car LAN).
  Parked-only rules and the re-checks still apply on the node gate; Stop is on the phone; an
  "accept" inside an AI client never counts.
- **Confirm, then sign** (plan note v0.11; module-bus spec §10, owner answer 1). For a Tier
  1+ action that reaches a car bus the shell shows the confirmation (or approval) first;
  only after the user confirms does the phone or Brain ask the node for a grant challenge
  and sign it at once, so the person is never inside the grant's 10 s window. The node
  runs its cheap checks before it issues a challenge, so a refusal ("Not while moving")
  shows straight after the confirmation. A queued action holds no grant; it is signed when
  it is delivered (module-bus spec §9).
- **Remote paths** (Tailscale, cloud relay) are **read-only by default**. The install-level
  override `OSTLER_ALLOW_REMOTE_CONTROL` (environment or install config, default off, never
  settable remotely) allows remote control for developers while the threat model matures.

**Constitution rules unchanged:** nothing writes to the car without these gates; Airbag/SRS is
read-only by construction; no SecurityAccess, coding or write is sent, and no sniffed write
replayed, without its own ADR; actuator tests are documented as stationary with ignition on. Also:
remote paths are read-only unless the install override is set (§7.2); Tiers 1–3 are refused while
Moving (except Comfort and arming, §7.1) or below the "ECU session" rung; `candidate`/`experimental` status shows on the button and in the
confirm; buttons name the action; every Tier 1+ action is logged with before/after values. A write
tier with backup and diff would need its own ADR. **Imported actions** (OVMS, ADR-0019) keep their
tier, are `experimental` and `remote: false`, and run only in service mode, Parked, with a per-action
confirmation; imported Tier 4 writes stay disabled until their own ADR.

## 8. Decode pipeline and Decode mode

### 8.1 Stages

Detail: [decode pipeline §6](../references/research/ui/decode_pipeline.md). All read-only.

| # | Stage | Output |
|---|---|---|
| S0 | **Connect:** listen-only bitrate probe, ELM/OBD auto-detect, pack probes | `link.json` |
| S1 | **Identify:** local VIN decode, CALID/ECU names, KWP `1A`, pack `detection` | a pack, or `generic_obd2` + "unknown vehicle" |
| S2 | **Inventory:** read-only ECU sweep (modscan, UDS `3E`/`10 01`, passive CAN ID census) | `ecus.json`, identity redacted |
| S3 | **Baseline:** supported PIDs and DTCs | a working dashboard on day one |
| S4 | **Capture:** reference-tool sniff with markers, differential toggles, or drive-and-correlate against OBD/GPS/IMU | scrubbed `trace.json` |
| S5 | **Correlate:** `automap`, clean-room bit-flip segmentation, lagged correlation | proposals with R² and lag |
| S6 | **Label:** name, `metric`, unit, map via `upsert_field` | field, `candidate` |
| S7 | **Verify:** distinct readings, fixture, second car, review | `proven` with evidence |
| S8 | **Package:** `ostler pack new` skeleton → full pack; OBDb/DBC export | installable pack |
| S9 | **Contribute:** opt-in anonymous readings or a PR bundle | shared data |

Sweeps send only `3E`, `10 01`, `22`, `19`, `1A`, `21` and inits, never `27`, `2E`, `2F`, `30`,
`31`, `3B`, `11`, `14`, `28`/`85` or fuzzing; ignition on, engine off, Parked, rate-limited,
stopping on a burst of negative responses; K-line always releases.

### 8.2 `generic_obd2` and "unknown vehicle — help decode it"

`generic_obd2` is a real pack behind the same contract, selected when no pack's detection matches.
It imports the OBDb SAEJ1979 signalset as attributed data, speaks J1979 and J1979-2 (UDS), builds
its manifest at connect time, and ends today's `NoVehiclePackError` dead end. Home then shows a
dismissible banner, **"Unknown vehicle — help decode it"**, with the coarse identity and the number
of ECUs that answered without a definition; it offers a cached OBDb make/model overlay (all
`candidate`) and opens Decode mode at Scan. On a non-OBD car it leads to "choose your vehicle /
start a pack".

### 8.3 Data, evidence, fixtures and scrub

- **OBDb-compatible with an `x-ostler` block.** The store stays the source of truth (ADR-0003) but
  each field becomes OBDb-expressible (`hdr`/`rax`/`cmd`/`proto`/`freq`,
  `fmt{bix,len,mul,div,add,map,unit}`, `path`, `suggestedMetric`); `confidence`, `evidence`, ranges
  and safety sit in `x-ostler`, which OBDb tooling ignores. OBDb `freq` is in seconds (correcting
  platform.md). CC BY-SA 4.0 data can go upstream.
- **Evidence.** `evidence {source, readings, distinct, r2, cars, fixtures, reviewer}`. `candidate` =
  one solver or importer hit (imports never go higher). `proven` = ≥ 2 distinct readings at R² ≥
  0.999 against a reference, ≥ 1 committed fixture from a real capture, and a second person's
  review.
- **Fixtures.** Labelled captures become OBDb-style YAML (`response` → `expected_values`); `pytest`
  decodes every one, and a failure demotes the field.
- **Scrub** runs before any fixture commit, export or upload: it strips VIN (Mode 09 `02`, UDS
  `F190`, KWP `1A 87/90`), serials (`F18C`), EKA codes and seed/key pairs, and coarsens GPS, time
  and odometer. CI fails on a VIN pattern or identity DID under `tests/`.

### 8.4 Decode mode in the UI

In **More → Developer**, behind service mode, refused while Moving: **Detect → Scan → Sniff →
Correlate → Label → Verify → Contribute**, growing today's admin Decode and Label tabs. Sniff is a
byte grid with a bit-flip heat map; Verify shows the evidence checklist; Contribute previews the
exact JSON before anything leaves. `CoverageMap` stays the progress view. It ships as
**Decode lab**, a core app in the platform repo shown only in service mode (owner, 2026-10-06;
[app-model spec](2026-10-06-app-model-design.md) §3).

## 9. Comparison

Production systems are evidence only ([head-unit UI §2](../references/research/ui/head_unit_ui.md)).

| Aspect | Ostler today | Proposed | Tesla | Polestar (AAOS) | OVMS | Dealer tools |
|---|---|---|---|---|---|---|
| Navigation | 8 bottom tabs + 3 admin | 5 destinations, rail or bar | car column + bottom dock | facet rail + 4 home tiles | Main · Tools · `<Vehicle>` · Config | vehicle → system → function |
| Persistent status | unordered header chips | severity-ordered strip | status column + top bar | status bar + climate bar | none | VCI/battery bar |
| Many ECUs | header module select | list pane; collapses at 1, groups > 12 | hidden | hidden | hidden (metrics) | system list / topology |
| Many vehicles | no | garage + switcher | app picker | profiles, one car | app spinner | VIN per session |
| Generated UI | no (D2 layout) | 3 tiers from a manifest | no (one fleet) | property-driven controls | metric widgets; apps hard-code | "only supported functions" |
| Driving lockout | none | Parked/Idling/Moving, server-enforced | yes | CarUxRestrictions | no | n/a |
| Service mode | `/admin` + banner | hidden entry + frame, exits on Moving | hidden + code + red frame | developer settings | per-page password | dealer login |
| Climate | none | device chip + page | bottom bar | climate bar | on/off + schedule | n/a |
| Security / cameras | none | Security; clips Parked only | sentry icon + parked viewer | OEM app | notifications | n/a |
| Data honesty | verified/candidate | + scan states + evidence | none shown | none shown | staleness | Not scanned / No response |
| Capabilities as data | `/pack` + `/catalog` | versioned manifest | closed | VHAL config | stubbed | closed DB |
| Local-first | yes | yes; VIN never leaves | cloud app | cloud services | own server | often cloud |

## 10. Phased migration

Each phase is small, testable and shippable, with its own spec. U0–U3 sit in the direction spec's
Phase 0, U5 in its Phase 2, U4 in its Phase 3.

| Phase | Ships | Test |
|---|---|---|
| **U0 Seams** | `vid` on every logbook session (old logs migrate to one vid); optional `metric` (VSS path) on store records via `upsert_field`; `metrics.json` common set; the D2 pack fills its set | unit tests; D2 coverage unchanged; no UI change |
| **U1 Shell** | layout classes, strip, rail / bottom bar, five destinations holding today's screens (§3.4), Drive mode, module select into Diagnose, fault modal → telltale; the app-model seams ([app-model spec §9](2026-10-06-app-model-design.md#9-migration-not-before-u1-the-seams-u1-leaves)) | Playwright at 1024×600, 1280×720, 1920×720, 393×852; target-size asserts |
| **U2 Driving state** | platform driving state (vehicle → GPS), UI lockouts, server refusal of Tiers 1–3 while Moving, service mode with frame | Moving fixture locks actions, text and video; server tests |
| **U3 Manifest** | Python-generated capabilities (D2 on tiers 2+3), field config onto signals, derived tiers, Scan all with seven states and reports; the visible-signals poll subscription (rule below) | golden manifests for D2 and the fake pack; scan-state tests; a test that every recorded channel is still polled with no screen open |
| **U4 Second pack** | `generic_obd2`, `generateViews()` (tier 1), single-system collapse, connect-time manifest, local VIN decode, unknown-vehicle banner | view snapshots; ELM fake; a test that no VIN reaches logs |
| **U5 Devices** | the node and its variants in `devices` from their capability manifests, Security destination and chip; HEVAC then extracts `DevicePack`; cameras | device fake; "no device, no chrome" tests |
| **U6 Garage** | `garage.json`, `VehicleSession` per vid, `/vehicles/<vid>/…` (old routes alias the active vid), switcher, Garage page; replay of another vehicle's session switches pack and manifest (§4.1) | two fake vehicles on one port, never interleaved; replay enters and exits another vehicle's manifest |
| **U7 Decode** | evidence block, `fixtures`, `scrub` CI (D2 proven fields first), OBDb import/export, then Decode-mode screens | fixture and scrub CI |

**Polling rule (U3).** The recording set is the baseline: every recorded channel is always
polled, so whole-app recording and replay never starve. The visible-signals subscription only
**raises** the priority or rate of what is on screen; it never removes a recorded channel. Signals
that are neither recorded nor visible may be dropped, which is where the K-line saving comes from.

U6 waits for a real second vehicle and `DevicePack` for the second device. U7's fixtures and scrub
may move earlier if the owner wants evidence before the second pack.

### 10.1 Standards per phase

Policy: [ADR-0017](../decisions/adr-0017-open-standards-first.md). The artefacts and verdicts live in
[standards §8](../references/research/standards.md#8-adoption-plan); each phase spec cites them.

| Phase | Standards that land with it |
|---|---|
| **U0** | `vss/` (VERSION 6.1, upstream, `ostler.vspec`) and the generated `metrics.json` (ADR-0016); `schemas/` in JSON Schema 2020-12 (store, layout, vehicle, capabilities); `api/openapi.yaml` 3.1 and `api/asyncapi.yaml` 3.0; RFC 3339 UTC timestamps; REUSE/SPDX, SBOM, SECURITY.md, Scorecard and Dependabot as the repo-wide items |
| **U1** | WCAG 2.2 AA with WAI-ARIA APG and an axe scan per layout class; W3C design tokens (`ui/tokens/*.tokens.json`); Material Symbols SVG subset; Web App Manifest; `Intl` (CLDR) for units |
| **U2** | NHTSA / Android for Cars numbers as normative; ASVS L1 on the gate; refusals in the OpenAPI error schema |
| **U3** | `capabilities.schema.json`, VISS-shaped datapoints `{value, ts}`, `etag`; golden manifests checked by pytest and vitest |
| **U4** | OBDb SAEJ1979 import (ADR-0019); J1979 / J1979-2 as references; local VIN decode under GDPR minimisation; SocketCAN `CanLink` if CAN is used (ADR-0020). **Needs** K-line profiles and auto-detection ([ADR-0022](../decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md)) for the KKL path and passive CAN bitrate detection ([ADR-0023](../decisions/adr-0023-passive-can-bitrate-detection.md)) for the CAN path |
| **U5** | **Needs the threat model first** (STRIDE + ASVS L2, `references/threat_model.md`); MQTT 3.1.1 with HA discovery, the OVMS alias tree, OwnTracks, Traccar OsmAnd, CloudEvents; AsyncAPI MQTT channels |
| **U6** | `garage.schema.json`; SOVD as a naming reference for `/vehicles/<vid>/…`; HMAC VIN fingerprint |
| **U7** | OBDb-compatible export; DBC import via cantools (dev-only); OVMS import behind the review gate (ADR-0019); REUSE on fixtures |

Triggered, not phased: service workers once the local-HTTPS trust setup ships (ADR-0021); ICU MessageFormat with a second
locale; MQTT 5 and OpenAPI 3.2 when tools support them.

## 11. Decisions (2026-10-06)

The owner answered every question; Q1 with "yes Covesa … try and use standard and open frameworks
where possible", Q2–Q11 with "yes" to each recommendation. Q1 is
[ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md) (with the policy in
[ADR-0017](../decisions/adr-0017-open-standards-first.md)); Q2–Q11 are
[ADR-0018](../decisions/adr-0018-ui-architecture-decisions.md).

| # | Question | Decision |
|---|---|---|
| 1 | Canonical namespace | COVESA VSS 6.1 paths; OVMS/HA/OBDb names are generated aliases (§5.6, ADR-0016) |
| 2 | Function-area names | Canonical areas with pack labels; the D2 still reads Inputs/Outputs/Utilities |
| 3 | Rail side | The vehicle's `driver_side` (right for the D2); the kiosk flag overrides |
| 4 | `comfort` class | Yes, only for our own add-ons that never write to a vehicle ECU (§6); car actions keep the five tiers. *Renamed the `add-on device` render class by ADR-0033 (2026-10-06)* |
| 5 | Unknown speed | Moving on head units; on phones reading stays open, actions keep the stationary precondition. *Amended by ADR-0033: a paired phone may approve Tier 2–3 over local links (§7.2)* |
| 6 | Generated UI scope | The three tiers; user-arranged dashboards deferred; no remote layout server or composed screens |
| 7 | VIN in the garage | HMAC fingerprint and masked form only, never the full VIN |
| 8 | Service-mode entry | Long-press plus password; `/admin` kept on desktop for one release |
| 9 | Reverse pre-emption | Only after the fast path exists; assist-only until then. 360° cameras are a future item (§6) |
| 10 | U4 / U5 order | Guardian (U5) first; `generateViews()` only with `generic_obd2`. *Amended by ADR-0032: the guardian is a node variant; U5 starts with the node and its variants* |
| 11 | Write/coding tier | Tier 4 non-runnable; any write path needs its own ADR |

Related: reuse from OVMS and OBDb is [ADR-0019](../decisions/adr-0019-reuse-from-ovms-and-obdb.md);
CAN links are listen-only by default ([ADR-0020](../decisions/adr-0020-can-links-listen-only-by-default.md)).

**Also decided on 2026-10-06:** the extension branch is `Vehicle.Ostler.*` (ADR-0016); the Pi serves
local HTTPS so phones get service workers ([ADR-0021](../decisions/adr-0021-local-https-on-the-device.md));
all OVMS vehicles and commands are imported, with commands disabled behind the gates (ADR-0019);
EKA read/set stays in the D2 pack, gated and opt-in (GOALS §3).

**Still open:** whether `docs/` is CC BY-SA; CRA legal advice before the first sale.

## 12. Amendment (2026-10-07), approved: U2 lockouts, Trips and Drive layouts

*Drafted on 2026-10-07 (v0.12) and approved by the owner on 2026-10-07 ("approve all")
(v0.13); the answers are in **Decisions for the owner** at the end of this spec, each
recommendation adopted and each alternative not chosen. Each subsection names the sections
of §1–§11 it changes; where they differ, §12 wins. Evidence:
[driver-distraction rules](../references/research/driver_distraction_rules.md),
[Speedometer/Odo teardown](../references/research/app_teardown_speedometer.md),
[OBD and telematics apps](../references/research/obd_telematics_apps.md),
[current UI audit](../references/research/ui_audit_current.md) and
[visual design direction](../references/research/visual_design_direction.md). Framing:
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) "Ecosystem: small core, add-ons are the product" (accepted), where Trips is core and
Social, Vehicles & Map and Maintenance & Garage are add-ons. Visual values belong to the
[visual design system spec](2026-10-07-visual-design-system-design.md) (approved); this section
names tokens only. Tiers, the gate, action categories (§7) and the five-destination cap are
unchanged.*

### 12.1 U2 lockouts (changes §3.5, §10 U2, §10.1 U2; app-model §4.4)

**Stance.** The owner proposed strict driver-safe templates on the driver-facing head unit
while Moving, guidelines plus review elsewhere, and a Waze-style per-trip "I'm a passenger"
override (re-prompted, no "always", logged, view-only, car actions still through the gate).
**Decided (owner, 2026-10-07), with one adjustment from the research:** UK Construction and Use regulation
109 makes non-driving content on any screen the driver can see unlawful while moving, whoever
asked for it (research §4.2), and the one centre-screen passenger unlock that shipped (Tesla
Passenger Play) drew a federal investigation and was withdrawn (§5). So the head-unit
**Passenger view** unlocks driving-related content only (vehicle state, own route and
location, driving cameras), and everything else goes **Open on phone**, where the full
"I'm a passenger" override applies. **Not chosen (the owner's original):** the head-unit
override unlocks all viewing. Decision 1.

**§3.5 wording** (research §8.1, with Logs read as Trips). Replace the Idling row's rule with:

> **Idling** — engine running, speed 0. Reading, Trips, cameras and Security arming are
> allowed. **Text entry, Maintenance and Tier 2 `engine_running_ok` actions also need Park
> evidence:** handbrake on, or neutral (sensed, or inferred from engine speed ÷ wheel speed),
> for > 3 s. Without it, Idling uses the Moving rules for those items. Non-driving visuals
> return 3 s after entering Idling or Parked.

Add after "Unknown speed":

> **Driver-facing displays.** Every head-unit layout class is driver-facing. A display counts
> as passenger-only only when an owner declares it in the install configuration as out of the
> driver's sight and reach (for example a rear-seat tablet); no user setting, app or API can
> change this while Moving. The phone stays a passenger device (above).

> **Passenger view (per trip).** On a driver-facing display, while Moving, a locked view may
> offer **Passenger view** only if every item in it is vehicle state, own location and route,
> or a driving camera (UK reg 109 classes). It never unlocks video other than driving cameras,
> clip playback, replay or animation, Docs, other people's vehicles, messages or social
> content, text entry, or any action; tiers and the gate are unchanged. Opening it asks once,
> "Are you a passenger? The driver must not use this while driving", with **I'm a passenger**
> and **Cancel**; there is no "always" and no setting to skip the question. Passenger view
> shows a persistent "Passenger view" badge and frame and a one-tap **Back to Drive**. It ends
> on Parked, ignition off, a new trip, unknown speed, reverse, service mode, any red telltale
> or 15 minutes, whichever comes first, and asks again next time. The server holds the state
> per trip and display and records each grant (time, trip, display, user if signed in) in the
> trip's local log; the record is shown to the owner, kept with the trip and never shared or
> uploaded. Every locked view also offers **Open on phone**, which sends the view to a paired
> phone; this is the preferred passenger path.

In short: "driver-facing" means any screen the driver can see or reach; only an owner install
setting marks a screen passenger-only; Idling needs Park evidence; Passenger view is scoped to
reg 109 content, per trip, re-prompted, timed out at 15 minutes, ended by the listed exits,
logged locally and view-only.

**The phone (the "Open on phone" target).** Guidelines plus review, as today: while Moving the
phone shows the Moving banner, and non-driving views (Trips analysis, Social, Vehicles & Map,
Docs) ask "I'm a passenger" once per trip, re-prompt after a stop or a new trip, have no
"always", are logged locally like the head-unit grant and stay view-only; car actions keep the
gate's stationary checks (§3.5, §7). Holding the phone is the driver's legal problem (UK reg
110), not a product rule (research §4.3).

**Rules that travel with the stance.**
- **Calls** are audio only while Moving on any driver-facing display; video is never shown on
  a driver-facing display, Passenger view included.
- **Message alerts** (every add-on, not only Social). On a driver-facing display while
  Moving, a message `alert_card` shows **line 1: sender name** (the contact's display name,
  ≤ 30 characters, cut on a character boundary with "…"; a group or ride message reads
  "*name* · *group*" within the same 30) and **line 2: the app** (the raising add-on's
  manifest name and icon, for example "Social"; a burst reads "Social · 3 new"). It has two
  buttons, **Play** and **Reply**, and no Later button: the card leaves after 8 s, or on
  Back or a swipe, and the message stays unread. Never message text, images, avatars,
  stickers, link previews or attachments while Moving, the preview setting included.
  - **Play** reads the message aloud through the shell's voice, never as text; a message
    over 280 characters is announced as "*name* sent a long message" with **Play all** and
    **Stop**. Attachments are named, not shown ("a photo", "a voice note", "a location").
  - **Reply** opens one `short_list`: row 1 **Speak a reply**, then up to five canned
    replies. *Speak a reply* records a voice note (≤ 30 s, PTT-style; Social §5); where the
    device has on-device speech-to-text it may send text instead, read back aloud with
    **Send** and **Cancel** (Cancel focused) and never shown as a transcript while Moving
    (AAOS `NO_VOICE_TRANSCRIPTION`). A canned reply sends on one tap and the card shows
    "Sent" for 2 s. The task is ≤ 3 screens (card → list → sent) and ends back in Drive mode.
  - **Canned replies:** default set "Driving, will reply later", "On my way", "Running late",
    "OK, thanks", "Call you when I stop". At most **five**, each ≤ **30 characters**, plain
    text (no links, no placeholders in v1), per user, edited **Parked only** in More →
    Settings; an empty list leaves only *Speak a reply*. A canned reply is a normal outbound
    message (signed, sealed; Social §4), never an action.
  - **First-line preview (owner opt-in, default off).** One setting per user, "Show first
    line of messages when parked", changed Parked only. When on, and the message **arrives
    while Parked, or Idling with Park evidence** (§12.1 Idling rule), line 2 shows the first
    line of the text instead of the app: plain text, ≤ **30 characters** after stripping
    line breaks and markup, "…" on overflow, attachments as "Photo", "Voice note",
    "Location", links as "Link", never auto-scrolling. The moment the vehicle is Moving the
    line reverts to the app name. It never shows on a passenger-only display (a shared rear
    screen; the recipient reads on their own phone), never while Moving, and never images.
    The phone follows its own OS notification settings, not this one.
  - **Rate limits while Moving:** one message card on screen at a time; a newer message in
    the same conversation updates the card's count instead of stacking; at most one card per
    conversation per 2 minutes and three message cards per 10 minutes overall, beyond which
    messages only raise the unread count on the strip chip and the Home card; group
    messages other than the active ride channel raise the count only (owner setting "Alert
    for group messages", default off). A message card never covers a red telltale, the
    reverse camera, the `call` template or a navigation manoeuvre prompt; it waits until
    they clear and is dropped to the count if it is more than 2 minutes old. One short chime
    per card at most.
  - **Legal fallback:** if the U2 opinion objects to names on a driver-visible screen, line
    1 reads "New message" and line 2 the app; Play and Reply are unchanged.
  *(Approved on 2026-10-07, DMD round, from §14; this bullet replaced "Add-on alerts never show
  message content". History: the earlier rule, approved the same day, read: a Social message
  `alert_card` reads "Message from *name*" (name ≤ 30 characters) with **Play** (read aloud)
  and **Later**, or the alert is audio only, binding every add-on.)*
- **Other vehicles on the head-unit map:** none while Moving, except members of an active
  convoy the owner opted into, drawn as plain markers with no names, avatars or photos (reg
  109 (b) covers your own vehicle; Decision 5). Who may be seen at all comes from the core
  data-class registry with ghost on by default (accounts and sharing spec); the `map` template
  only draws what it is given.
- **Social surfaces** ([Social add-on spec](2026-10-07-social-addon-design.md), approved): Social contributes a `more:social` slot (a
  More → Social page, not a destination, so the five-destination cap holds; locked while
  Moving like the rest of More) and a **ride/call strip chip** shown only while a ride or call
  is active, which opens the `call` template while Moving. Neither adds a template or unlocks
  anything.
- **Fail closed:** a view with no `moving` rule, or a missing restriction config, is fully
  locked (AAOS default; app-model §4.2 already says "missing = false").
- **Server state:** apps can neither set nor read "unlocked"; they render what the shell
  allows.

**Templates and limits** (changes §3.5's Moving row and app-model §4.4). The existing
five (`telltale_list`, `value`, `setpoint`, `camera_live`, `arm`, as app-model §4.4) plus:

| Template | Limit while Moving on a driver-facing display | Source |
|---|---|---|
| `map` | own position, route, next manoeuvre; no other vehicles' names, avatars or photos (convoy markers only, above); no free panning or search | reg 109 (b)(d); NHTSA map exception |
| `media` | title and artist ≤ 30 characters each, static artwork, play/pause/skip/volume; no lyrics, no video, no browsing beyond a `short_list` | CarPlay audio rule; reg 109 (a) as equipment state (our reading) |
| `tiles` | ≤ 6 tiles, ≥ 56 px digits, display refresh ≤ 4 Hz with hysteresis, no animated needles except red alarms | Android grid 6; SA-1 |
| `alert_card` | one card, icon + ≤ 2 lines of ≤ 30 characters, ≤ 2 buttons; never message content while Moving (a message alert is sender name + app with **Play** / **Reply**; the opt-in first-line preview appears only for messages that arrive while Parked or Idling with Park evidence); ≤ 3 message cards per 10 minutes, one per conversation per 2 minutes (§14, approved 2026-10-07; earlier: "Message from *name*" with Play / Later) | CarPlay alert; NHTSA reading lockout; Android Auto message card and "show first line" (stopped only) |
| `short_list` | ≤ 6 rows, one level, ≤ 30 characters a row, driver-paced scroll only | Android list 6; ESoP I |
| `call` | one audio call or push-to-talk channel; name ≤ 30 characters, no photo; state and timer; ≤ 3 buttons (for example answer, decline or end, mute); never video or message text (as app-model §14.5 defines it) | CarPlay communication; NHTSA images and text lockouts |

Every task on a head unit while Moving is **≤ 3 screens** and ends back in Drive mode
(CarPlay Driving Task depth, tighter than Android's 5 because Drive mode is the root); §3.5's
"lists > 6 items or > 2 levels" reads "beyond the template limits or deeper than 3 screens".
"≤ 30 characters a line" is **our** limit, not NHTSA's (corrected in
[head-unit UI research §1](../references/research/ui/head_unit_ui.md)), with the AAOS
120-character string cap as the ceiling. **New templates are added only by a platform
proposal** (spec, owner approval, limits that cite their source, tests). Moving templates use
no glow, gradient or animation (visual research, Avoid 2).

**"Using Ostler while driving" page** (ESoP principle IV; a U2 deliverable in More → About and
the docs, linked from the passenger prompt). First lines, from research §8.3:

> Ostler's driver-safe screens are Drive mode, telltales, Mark, the own-car map, media
> controls, climate setpoints, arming and the reverse camera. Everything else is for use when
> parked, or by a passenger on their own phone. Passenger view on the car screen is for a
> passenger only; using it while driving may be an offence (in the UK, Construction and Use
> regulation 109) and is your responsibility.

**Legal check before U2 ships (a gate).** U2 may build and test every lockout, but Passenger
view and the phone override are not released until a UK road-traffic lawyer's short opinion
on reg 109's application to LCD head units and on Passenger view is recorded in
`references/`. The same opinion covers message alerts (§14, approved 2026-10-07): (i) whether
a sender name and app name on a driver-visible screen while moving falls outside reg 109
(fallback: "New message" and the app); (ii) whether the opt-in first-line preview is lawful
for a message that arrives while Idling with Park evidence, or only when Parked (until the
opinion is recorded, the preview shows only when Parked); and, only if the owner had chosen
Decision M3's alternative (not chosen), (iii) whether any preview may show while moving
(without a clear yes, it never ships). A product-liability opinion on the EU Product Liability Directive 2024/2853
(software is a product from 9 December 2026) is due before hardware sales start. Without the
first opinion, U2 ships with no head-unit override at all, only **Open on phone**.

**§10 U2 row reads.** *Ships:* platform driving state (vehicle → GPS) with Park evidence
for Idling, driver-facing displays, Passenger view with its exits and local log, Open on
phone, the six new templates with their limits, server refusal of Tiers 1–3 while Moving,
service mode with frame, the "Using Ostler while driving" page. *Test:* the Moving fixture
locks actions, text and video; Passenger view is refused for a view that declares a
non-driving data class; each exit and the 15-minute timeout end it; no "always" exists in the
DOM or settings; an alert card carries no message text; the head-unit map shows no other
vehicle except opted-in convoy markers; Idling without Park evidence locks text entry and
Maintenance; a message `alert_card` carries no message text while Moving with the preview
setting on or off; the preview appears only for a message that arrived while Parked (or
Idling with Park evidence once cleared) and reverts on Moving; it never renders on a
passenger-only display; the Reply list has ≤ 6 rows of ≤ 30 characters and canned replies
can't be edited while Moving; the rate limits hold (one per conversation per 2 min, three per
10 min); no transcript text renders while Moving (§14); server tests. **§10.1 U2 reads:** NHTSA 2 s / 12 s glance criteria and the
per se lockout list, the Android for Cars and CarPlay template limits above, ESoP
(2008/653/EC) principles I, III and IV, and UK reg 109 as the content rule; "≤ 30 characters"
cited as ours; ASVS L1 on the gate; refusals in the OpenAPI error schema.

### 12.2 Logs → Trips (changes §3.2, §3.4, §3.5, §3.6, §3.8, §4.1, §4.3, §6, §10)

**Rename everywhere in the UI plan.** The destination, its core app and every UI string read
**Trips** (was Logs). §3.4's destinations read `Home · Diagnose · Trips · Security (Map) ·
More`; §3.2's REC chip opens Trips and Rewind moves to Trips; §3.5's Idling row reads Trips;
§3.6's core apps are Diagnose, Trips, Security and Network; §3.8's brain-only views read "full
Trips, replay, clips"; §4.1 reads "Trips replay"; §4.3's scan report saves to Trips; §6's Alarm
page shows "events (filtered Trips)". **Routes stay compatible:** the destination id becomes `trips`
and the core app id `ostler.trips` (matching ADR-0042 and app-model §14.2); route
names become `trips`, `trips.trip`, `trips.stats` and `trips.records`; `logs` and
`logs.analysis` stay as aliases of `trips` and `trips.trip` for at least one release, so
`goTo()` callers, links and bookmarks keep working. **The API is unchanged:** a trip is an
ADR-0009 session and `/sessions…` keeps its shape (logs-at-scale spec §3); a `/trips` alias may
come with the summary index. Statistics and Records are tabs inside Trips, not a sixth
destination. The Speedometer/Odo trip features fold in here (teardown §5).

**Two tiers** (RealDash's trips versus datalogs; telematics research Decide 2):
1. **Trip summary index:** one row per trip in the existing session index (logs-at-scale §3),
   extended with route (simplified track and `bbox`), distance, duration, moving and idle time,
   stops, elevation gain, maximum, average and average-moving speed, sustained best (fastest
   30 s average), time at speed per band (time and distance), sprints when eligible, fault
   codes seen, peak g, places, `vid`, `excluded` and `ended_by` (`auto` or `user`). It is
   computed when a trip ends and can always be rebuilt from the recording; each figure records
   its speed source (ECU or GPS) and rate.
2. **Full recording behind it:** the ADR-0009 session, unchanged, which playback and analysis
   open. No second format.

**Screens** (drawn from teardown §3; all parked-only on driver-facing head units, §12.1):

| View | Contents |
|---|---|
| **Trip list** | Grouped by day. Each row: a **mini dark map** of the route (Ostler Night style, trace in the speed ramp) beside start → end places, start time, distance, duration and max speed; an "Excluded" badge where set. A "Recording now · N min" card with **End trip now**. Filters (vehicle, dates, search) and an **All events** toggle that shows today's timeline (parked periods, alarm events, faults, notes, scan reports) |
| **Trip detail** | A **full-screen dark map** with floating chrome (back, date, share and export, "…") and a sheet (`surface-glass`, `radius-xl`; bottom sheet with peek, half and full on phone; a side sheet on the passenger side in landscape). In the sheet: the itinerary (start and end place and time); a **3 × 3 stats grid** (distance, average speed, max speed / duration, idle, moving / elevation gain, stops, average moving speed) with sustained best beside max speed; the **time-at-speed donut** in the six speed-ramp bands of the user's unit with a **Time / Distance** toggle; **speed over time** with a picker for **any recorded VSS signal** (rpm, coolant, boost, g …), gaps drawn as gaps; faults seen; **Exclude from stats**, Export (CSV, GPX, VBO) and Delete; the prose description folded into "About this trip" |
| **Playback** | The same map with the trace stepped in the speed ramp, a casing and a legend; heading arrow; heading-up or north-up; the sheet collapses to a readout (speed hero, altitude, g, distance), a **scrubber**, ±10 s, **1× / 2× / 4× / 8×**, play/pause and **Jump to max speed**; the channel picker re-colours the trace (existing) |
| **Statistics tab** | An **all-time hero** (max speed with place and date, sustained best beside it); a **totals grid** (distance, trips, total time, moving, idle, average distance, average duration, average speed, longest trip); a **speed distribution** (trips by max-speed band, speed ramp); **Records** (max speed, sustained best, longest trip, highest point) and **Sprints**; a **calendar**: the year heatmap plus a month calendar. Filters: vehicle and period. Excluded trips are never counted and their number is shown |
| **Records → Sprints** | One card per band (0 → 60, 0 → 80, 0 → 100 km/h, mph equivalents, custom); ranked rows with rank badge, time, delta to the best, peak speed and date |

**Data per view** (✔ have, ◐ compute from recordings, ✘ new; teardown §4–§5):

| View | ✔ Have | ◐ Compute from recordings | ✘ New |
|---|---|---|---|
| Trip list | places, start time, distance, duration, max speed (session index); "Recording now" card | mini-map route from the track (cached simplified line) | **End trip now** (recorder control); `excluded` badge |
| Trip detail | distance, duration, max speed; places; speed and channel chart (`/data`, min/max decimation); peak g (`motion.py`); delete; per-trip export | average, moving, idle, stops, elevation gain, average moving (`GPS_Speed`, `GPS_Altitude`, `Interval`); sustained best; time at speed by time and distance; faults seen (`faults` channel) | dark basemap (visual spec); **Exclude from stats** (`excluded` column, `PATCH /sessions/<id>`); full-screen chart page |
| Playback | speed-coloured trace, scrubber, ±10 s, 1–8× (`PlaybackContext`, `Transport`), heading arrow, channel picker | jump to max speed (max-speed row index); heading-up | bottom- or side-sheet layout over a full-bleed dark map |
| Statistics | year heatmap (`YearHeatmap`, histogram API); `max_speed_kmh` per trip | all-time hero, totals, speed distribution, records, month calendar (aggregates over the index) | the tab itself; vehicle and period filters over the index |
| Sprints | — | — | sprint detection, ranked per band (needs ≥ 10 Hz speed or IMU, below) |
| Export all | per-trip CSV, GPX, VBO export | — | one-screen **Export all** archive plus the index as CSV |

**Sprint gating.** A sprint is computed only when the trip has ≥ 10 Hz speed (the u-blox GNSS,
ADR-0039) or a calibrated IMU in session; otherwise Records shows the band with **"Needs fast
GPS"** and no time. A 1 Hz max speed is shown with sustained best beside it and labelled by its
source (data honesty, ADR-0006; teardown Avoid 4). On the Td5, road speed is usually GPS speed
because a SLABS session holds K-line (§3.5).

**End trip now and Exclude from stats; no pause.** Recording stays automatic and always on
(ADR-0011). **End trip now** closes the current trip; the next starts on the usual trigger.
**Exclude from stats** (a tow, a test drive, a passenger ride) keeps the trip in the list with a
badge but leaves it out of Statistics, Records and Sprints; it is reversible. Neither is a car
action; on a driver-facing head unit both are available Parked or Idling only.

**Export all** is a hard rule: one screen in Trips exports every trip as CSV, GPX and VBO
(ADR-0009 formats) in one archive, plus the summary index as CSV, offline and with no
Ostler-run server (telematics research Decide 7).

**No score.** Core Trips shows neutral facts only: no driving score, no speed ranking, no
speed-limit violation history (teardown Avoid 3). Any score or board lives in the Social
add-on, opt-in per friend or group, and never ranks speed.

### 12.3 Drive mode (changes §3.1, §3.5, §5.3, §5.4, §10 U1 and its test)

**Layouts as data** (the RealDash model; telematics research, RealDash deep dive and Decide 1).
A **Drive layout** is a file with one grid per layout class (authored per class, never scaled):
rows × columns of tiles, each bound to one VSS path (ADR-0016) with a range and **normal /
warning / critical** levels, taken from the signal's `normal` and `limits` (§5.1) and
overridable per vehicle; tile colour changes only when the level changes; optional `map` and
`media` panes on classes with room (HU-9/10, HU-wide). The default layout is generated from
roles (§5.4, tier 1); a pack may declare one (tier 2); a user edits a per-vehicle diff in a grid
editor, Parked only, with no pixel editor in v1 (this is §5.3's "user-arranged dashboards …
later as a per-vehicle diff"). Layouts are Read only: no triggers, no writes (ADR-0033).
**While Moving on a driver-facing display a layout renders only through `tiles` (≤ 6), `map`
and `media`**; a layout with more tiles shows the first six in role order and the rest when
Parked. Tiles use calm gauges, tabular numerals and values ≥ 56 px (visual spec: the hero and
gauge tokens), with no glow while Moving.

**One screen at every head-unit class** (UI audit P1 and D6). Drive mode has no page heading;
Back moves into the strip; the fault banner folds into the worst-telltale chip; rows are sized
by the remaining height (`grid-auto-rows: 1fr`), never by content. §3.1 gains a class, since
800×480 is common on cheap Android head units and today falls into HU-7:

| Class | Trigger | Shell (px) | Content area |
|---|---|---|---|
| **HU-5** 800×480 | landscape, height ≤ 520, aspect < 2.4 | rail 80 · strip 48 | 720×432: Home 2×2 cards; Drive mode 3×2 tiles, values ≥ 56 px; the strip keeps chips 2–5, 9 and the clock |

1280×480 (aspect 2.67) stays HU-wide and becomes a test size. **Test** (added to §10 U1 as a
fix, before U2): Playwright asserts that `main` does not scroll in Drive mode at 800×480,
1024×600, 1280×720, 1280×480, 1920×720 and 393×852, that every tile (a critical one included)
is inside the viewport, and the target-size asserts at HU-5.

**Map-first Analysis** (UI audit D2). Trip detail and playback put the map first: about
**55 % of the height on a phone**, with the sheet's peek above the fold, and the **left half in
landscape** with the sheet on the right; on a head unit (Parked) the sheet sits on the
passenger side (visual research §9), so on a right-hand-drive car the map takes the right half.
The map style follows the theme (Ostler Night or Day; OpenFreeMap dark or positron as the
online fallback), the offline fallback takes the `bg` token instead of a fixed light grey, and
`cooperativeGestures` is on wherever the page scrolls. ADR-0009's basemap rule is amended
to match ([ADR-0009 amendment, 2026-10-07](../decisions/adr-0009-session-logbook-and-location.md#amendment-2026-10-07));
the session-logbook spec's replay layout follows this section.

### 12.4 Add-ons catalogue placement (changes §3.4's More and Home rows)

ADR-0042 (accepted) and app-model §14.2 add a Home Assistant-style **Add-ons catalogue**
(Installed and Available tabs; cards labelled Core, Add-on or Developer) that replaces More →
Apps. This spec has no Settings page (More holds Preferences), so the catalogue lives at
**More → Add-ons, the top entry of More**, above Garage, Network, Integrations, Preferences,
Privacy, Developer and About. Like the rest of More it is locked while Moving on a
driver-facing display; installing or removing an add-on is an owner operation on local links
(§7.2). **Home** gains an **empty-state card**: when no optional add-on is installed, one
dismissible card suggests a few (for example Maintenance & Garage, Vehicles & Map) and opens
More → Add-ons; it never appears while Moving and never replaces a warning or vehicle card.

### 12.5 Visual design system (changes §2 principle 7)

The [visual design system spec](2026-10-07-visual-design-system-design.md) (approved
2026-10-07) owns every visual value. §2 principle 7 reads: **Calm instrument.** ISO 2575
colours for telltales only, a word with every icon, gauges neutral in range with a status
colour and word only out of range, motion only for red alarms, **at most one glowing element
per screen and none on head units at night or in Drive mode**, and night dark by default
(Night, with Day equal and Auto available). Minimum text sizes are 12 px on a phone, 18 px on
a Parked head unit and 24 px in Moving templates (visual spec §4). The visual migration (V1
tokens, font and maps; V2 component kit; V3 pages) lands before U2 build work; the Drive-mode
fit fix (§12.3) may land first.

## 13. Amendment (2026-10-07, DMD round), approved: sharing screens, Places and map theme

*Approved by the owner on 2026-10-07 ("approve all", DMD round), v0.15; the answers are in
**Decisions for the owner (DMD round, 2026-10-07)** at the end of this spec. Each subsection
changes the sections it names. Behaviour, rules and tests are in the
approved [per-trip sharing spec](2026-10-07-trip-sharing-design.md) and
[ADR-0043](../decisions/adr-0043-gps-and-logs-in-shared-trips.md) (accepted); evidence in
[trip and log sharing](../references/research/trip_and_log_sharing.md) §10 (styling) and
[DMD Hub features](../references/research/dmd_hub_features.md) §2.2 and §3. Tokens only; visual
values belong to the [visual design system spec](2026-10-07-visual-design-system-design.md).*

### 13.1 The Trips share sheet (changes §12.2's trip detail "share and export")

Opened from the trip detail's share button, a trip row's "…" menu or a marked range in
playback. A trip still recording offers only **Share live**, which hands over to Vehicles &
Map (live grant options: trail window, delay, show speed, show values; accounts §15.3). The
sheet is `surface-glass`, full height on phone; **Parked only on a driver-facing display**
(§12.1); a phone may share at any time.

1. **Audience first.** Me · a contact · a group (a hub club is a group) · household · anyone
   with the link · publish to Ostler Community · get help (named helpers, on an Ostler
   Community help thread or directly, or a pack's maintainers). Levels the audience cannot take are greyed with the
   reason ("Full logs go to named people only", "Telemetry is never public").
2. **Level ladder.** Five stacked rows, L0 at the top, the entry point's default
   pre-selected (Trips: L0; Diagnose: L4; Decode lab: L3). Each row has chips for what it adds
   (map, chart, raw, wrench) and one plain-language line:

   | Row | Plain-language description |
   |---|---|
   | **L0 Card** | "A card with the day, the area, distance and time. No map." |
   | **L1 Route** | "The card plus your route on a map. The first and last 500 m and your private places are hidden. No times on the route." |
   | **L2 Telemetry** | "Chosen readings (speed, revs, temperatures…) as charts, with times counted from the start. No map unless you add the route." |
   | **L3 Full log** | "Everything the car's computers said on this trip, so someone can help decode it. Your VIN and serial numbers are removed. Goes to named people only." |
   | **L4 Diagnostics** | "Fault codes, freeze frames and module information, so someone can help find a fault. Goes to named people only." |

   The L3 and L4 rows use the warning token; L0–L2 do not.
3. **Options for the chosen level:** signal picker (L2); include the route (L2–L4, refused
   for public destinations); shareable notes; plate; show max speed (off for link and public);
   keep real date and time (L3–L4, one named person only, naming them).
4. **"What they will see."** The preview fills the sheet and is rendered from the produced
   output through the same filter the recipient gets (S8 View as…), not an imitation: the
   map in the map theme (§13.5) with hidden ends drawn as a **dashed fade to the `bg` token,
   never a circle** (a circle shows where a zone is), the recipient's stats, and for L3–L4 the
   **redaction report** as a chip row ("VIN ×3", "Ends 500 m", "2 zones", "Relative time",
   "No GPS"); tapping a chip explains the rule; a hex before-and-after view of scrubbed frames
   on the owner's device only, mono face, scrubbed bytes in the muted token. A verifier fail
   replaces Send with the rule that failed and what to do next.
5. **Expiry and link controls.** Durations first (1 h · end of day · 7 days · 30 days · until
   I stop, where the class allows); **More options**: Locked or Download, available from,
   access until, number of people, downloads each. The state (Pending, Active, Full, Expired,
   Revoked) and the expiry show as a countdown chip in the visibility-chip style. On file and
   public pack-issue paths the sentence **"This can't be taken back once sent"** appears in the
   warning token, as text, not small print.
6. **Privacy zones.** A line under the preview: "Hidden: first and last 500 m, 2 private
   places · Edit in Places", linking to More → Places (§13.4).
7. **Send** names the path: Share · Copy link · Save file · Send to helper · **Ask on Ostler
   Community** (a Help thread on the one official, Ostler-run hub; the open client encrypts
   any L3/L4 attachment end to end and the hub stores ciphertext only; community hub spec
   v0.2 §8; shown only when `ostler-app-hub` is enabled and linked). Afterwards the
   trip row's "…" shows "Shared 2× · 1 active", which opens the trip's share history; the
   audit also sits in Settings → Sharing (S8).

### 13.2 "Get help with this fault" (Diagnose; changes §3.4's Diagnose row)

On a fault's detail and on a module page, a secondary action **Get help with this fault**
opens the help flow (sharing spec §13) with L4 pre-selected, the fault code, module, freeze
frame and vehicle fields filled in, and a symptoms box. Its send paths are Send to helper and
**Ask on Ostler Community** (a Help thread on the official hub with vehicle chips and fault
codes filled, attachment encrypted end to end; community hub spec v0.2 §8, §15.2); without
`ostler-app-hub` only the direct paths show. It never clears or changes anything on the car;
Parked only on a driver-facing display.

### 13.3 "Ask for help decoding" (Decode lab; changes §8.4)

In Sniff and Label, on a signal or a frame, **Ask for help decoding** opens the help flow with
L3 pre-selected and the time range set to the marked window, and sends by creating a **Help
thread on Ostler Community** (the closed, Ostler-run hub; the L3 attachment is encrypted end
to end by the open client, so the hub stores ciphertext only), linked to the vehicle project
if one exists (community hub spec v0.2 §8, §10); without the hub add-on it falls back to Send
to helper or Save file. **Run a recipe** imports a
helper's recipe (signals, modules, steps; never actions) and walks the owner through the
recording with ⚑ marks. The contribution consent (CC BY-SA 4.0 for derived data only, off by
default) sits in the sheet beside Contribute's JSON preview.

### 13.4 More → Places (changes §3.4's More row and §12.4's order)

A new **Places** entry in More, after Network: saved places that are **privacy zones** (Home,
Work, others), each with a radius (500 m · 1 km · 1.5 km · 2 km; Home defaults to 1 km), and
the **ends trim** for every shared trip (a slider from 200 m to 1.5 km, default 500 m, floor
200 m). The owner's own map shows each zone at its offset centre with a plain note: "Your place
is somewhere inside this circle, not at its centre. Sharing many routes near one place still
narrows it down." Trips, Social, Vehicles & Map and `ostler-app-hub` read Places through the
shell API. More's order becomes Add-ons, Garage, Network, **Places**, Integrations,
Preferences, Privacy, Developer, About.

### 13.5 Map theme independent of the app theme (changes §12.3's map-style sentence)

**More → Preferences → Map theme: Follow app (default) · Day · Night · High contrast.** Every
map (Trips, playback, Security, the Vehicles & Map pane, the share preview, navigation) uses
it; "Follow app" keeps today's rule (§12.3). A head unit in Drive mode at night uses Night
unless the user chose High contrast. The High-contrast map style is a follow-up for the visual
design system spec, which defines none today.

## 14. Amendment (2026-10-07, DMD round), approved: message alerts (amends §12.1 `alert_card` and the U2 legal check)

*Approved by the owner on 2026-10-07 ("approve all", DMD round; decision list items 57–61),
v0.15, and **applied into §12.1**: the bullet "Add-on alerts never show message content" is
replaced by the **Message alerts** bullet, the `alert_card` row of the template table, "Legal
check before U2 ships" and the §10 U2 *Test* list carry the new text, so §12.1 is the single
source and this section is the record of the change. Decisions M1–M4 (end of this spec, DMD
round list) are answered as recommended. Evidence:
[message alerts research](../references/research/message_alerts_android_auto.md) and
[driver-distraction rules](../references/research/driver_distraction_rules.md) §4.2, §7.1 #10.
Matching change: [Social add-on spec](2026-10-07-social-addon-design.md) §12 (approved), which
replaces its §8 "Driver screens" bullet and Decision 5.*

**The change (owner's ask, 2026-10-07).** "Copy Android Auto": while Moving, a message
`alert_card` on a driver-facing display shows the **sender and the app**, with **Play** (read
aloud) and **Reply** (voice, or one of up to five canned replies, each ≤ 30 characters, edited
Parked only), and the owner may opt in to a one-line first-line preview, off by default, shown
only for messages that arrive while Parked (or Idling with Park evidence once the legal opinion
clears it); rate limits of one card at a time, one per conversation per 2 minutes and three per
10 minutes. **Old rule, the alternative (not chosen):** "Message from *name*" with **Play** and
**Later**, never content (§12.1 as approved earlier on 2026-10-07; kept there as history).

**Where it now lives:** §12.1 "Rules that travel with the stance" (**Message alerts**), §12.1
template table (`alert_card`), §12.1 "Legal check before U2 ships" (questions i–iii) and the
§10 U2 row's *Test* list.

## 15. Amendment (2026-10-07, DMD round), approved: Drive modes and editing

*Approved by the owner on 2026-10-07 ("approve all", DMD round; decision list items 47–56 and
86–91), v0.15. Where it differs from §1–§13, it wins. It changes §3.2 (a new strip chip; a user-ordered strip), §3.4 (rail slots, labels and
icons), §5.3 (user-arranged dashboards) and §12.3 (one Drive layout becomes several modes);
tiers, the gate, the templates and their limits (§12.1) and the five-slot cap are unchanged. Design:
[Drive modes and editing](2026-10-07-drive-modes-and-editing-design.md) (approved); widget
contract: [app-model §15](2026-10-06-app-model-design.md) (approved); input:
[shell input](2026-10-07-shell-input-design.md) (approved). Evidence:
[OBD and telematics apps](../references/research/obd_telematics_apps.md) (RealDash, AutoZen),
[DMD2 UI teardown](../references/research/dmd2_ui_teardown.md) §2–§5. Owner's ask: "the
current Drive mode is too diagnostic", and an Android-style editable UI; revised the same day
for the owner's "the entire UI is editable, with no fixed icons" (the locked Home and More rail
slots and the locked core strip chips are gone; guardrails below).*

### 15.1 Drive modes (changes §12.3)

- **Several modes, each a §12.3 Drive layout as data**, in one versioned file format
  (`ostler.layout/1`), authored per layout class, tiles bound to VSS paths with range,
  normal/warning/critical levels, units and gauge style, plus `map`, `media` and `ptt` (the
  `call` template) panes. A mode holds **1–3 faces** per class, switched by D-pad
  `left`/`right` or a swipe (shell input §6). Each face carries an explicit **Moving
  section** that is validated strictly against §12.1 (≤ 6 tiles, panes, type floors, no
  animation); a layout whose Moving section breaks a limit cannot be saved or imported.
- **Presets** (CC BY-SA 4.0, in the platform): **Diagnostic** (today's pack tiles),
  **Dashboard** (speed hero, rpm sweep, side gauges; the head-unit default),
  **Map**, **Convoy / Ride** (needs Social), **Off-road** (D2 hint; tilt needs the node IMU
  derivation, low range and diff lock need a SLABS session), **Split / Media** (needs a media
  source add-on; three columns on HU-wide) and **Minimal / Night**.
- **Switcher (changes §3.2).** A new core chip **Drive mode**, shown only in Drive mode (by
  default after Back; the user may move or re-icon it, never remove it), on every class (phone and HU-5 included): a tap cycles a rotation of ≤ 4 modes, a long
  press lists ≤ 6 as a `short_list`. Switching is allowed while Moving; the mode is remembered
  per display, profile and vehicle; nothing switches by itself while Moving.
- §12.3's "a user edits a per-vehicle diff in a grid editor, Parked only" reads: **a user edits
  modes in a slot-first grid editor, Parked only on a driver-facing display, stored per vehicle,
  layout class and profile with a `base` reference to the preset or pack layout it came
  from**; there is still no pixel editor.

### 15.2 Editing (changes §3.4 and §5.3)

- **Park to edit.** On any driver-facing display, editing Home, the rail and Drive modes needs
  Parked (or Idling with Park evidence); the server refuses the write otherwise and the UI says
  "Park to edit". Changes made elsewhere for a display that is Moving apply at its next Parked.
- **Everything is editable.** Rail items (Home included), the strip's chip order and
  visibility, Home widgets, Drive tiles and add-on pages can be moved, resized (where they have
  sizes), **re-iconed** from a curated **Material Symbols** catalogue (§2 principle 7's one
  icon set; no emoji or images), **renamed** (plain text, ≤ 12 graphemes on the rail and strip,
  ≤ 30 elsewhere, refused rather than clipped if too wide for any class), **hidden** or
  **replaced** in place. Defaults are i18n keys; a custom name is literal text that keeps its
  language, with **Use default name** to return to the translated default; the accessible name
  is the custom name with the default as its description.
- **Edit mode is always one gesture away:** a long press on the strip or on any empty area
  opens edit mode on every page and class (on a head unit while Moving: "Park to edit"); no
  layout can turn this off.
- **Home** gains an edit mode (drag with swap, small/medium/wide, remove, replace, a widget
  picker of core and add-on widgets, undo, **Reset to default**). §5.3's "user-arranged
  dashboards … later" becomes this, over the generated or pack default.
- **Rail (changes §3.4).** Still five slots and no locked slot: any core destination (**Home
  included**) or **pinned add-on page** (any `more:*` page) in any slot and order; **More is
  always one of the five**, movable, renamable and re-iconable, never removed. Whatever is not
  in the rail is under More → Pages (hidden add-on pages under More → Hidden pages), so nothing
  is unreachable; landing rules and deep links do not depend on the rail, and Home stays the
  default landing page and the root of `back`. A pinned page keeps its driving rule. The
  head-unit Drive button stays outside the cap and may move, be re-iconed, renamed or hidden.
- **Strip (changes §3.2).** The order is the user's (default: today's), per class and for the
  normal and Drive strips; ordinary chips may be hidden, renamed and re-iconed within a
  per-class chip budget so the strip never scrolls; add-ons add no chips. Shell input lands on
  the Drive-mode chip **by id**, so the switcher and focus zones work in any order.
- **Safety items move, never go:** the **fault telltale** (strip chip and Home warnings card),
  **alarm alerts** (the Security chip while a node is present, the Security alert card,
  `alert_card`) and **the Moving templates and their limits**; their icons, words and colours
  stay fixed. **Anchors** are never removed: More, and in Drive mode Back and the Drive-mode
  chip. `alert_card`, the fault sheet, the Passenger-view and service-mode frames and badges
  stay shell-drawn outside any layout. One validator on the client and the server refuses any
  write or import that removes or hides a safety item or More.
- **Reset layout is always reachable:** a non-hideable row in More, a row in the Connection
  sheet (which also opens by itself when the link drops) and the edit bar; scopes this surface,
  this screen, all screen sizes; Cancel focused; a 7-day "Undo reset" snapshot.
- **Files.** Modes, Home, rail and strip layouts export and import as `.ostler-layout.json`
  (file, link, QR, Web Share), scrubbed of vehicle and user identity; custom names and icons
  travel with them.

### 15.3 Tests (adds to §10 U2)

Playwright at 800×480, 1024×600, 1280×720, 1280×480, 1920×720 and 393×852: the Drive-mode
chip cycles and lists modes and is remembered; with the Moving fixture no edit bar appears and
the edit routes are refused; for every face of every preset `main` does not scroll, ≤ 6 tiles
render, digits ≥ 56 px and nothing glows or animates; the safety items and More survive any
edit or import (writes that remove them are refused by the server); after a randomised edit
sequence, a long press on the strip and on an empty area still opens edit mode, Reset layout is
in More and the Connection sheet, every page opens from More, and `back` reaches Home in ≤ 3
presses; with shuffled strip orders the strip does not overflow and the D-pad lands on the
Drive-mode chip wherever it sits; names over their limit or too wide for a class are refused.

### 15.4 Decisions for the owner (this amendment)

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each recommendation
below is the decision; each alternative was not chosen.

1. **Several Drive modes with a strip chip?** Recommend: yes, as §15.1, Dashboard the default
   on head units. Alternative: one Drive layout as §12.3 has it, with Diagnostic as the default.
2. **Modes and faces as two levels?** Recommend: yes (chip for modes, `left`/`right` for
   faces). Alternative: one level, `left`/`right` cycling modes.
3. **How editable are the rail and strip? (revised)** Recommend: everything editable (move,
   re-icon, rename, hide, replace), with More always in the five-slot rail, safety items
   movable but never removed, Back and the Drive-mode chip always in the Drive strip, long
   press on the strip or an empty area always opening edit mode, and Reset layout in More and
   the Connection sheet. Alternative: the first draft's Home and More locked, three free middle
   rail slots and fixed core strip chips.
4. **Edits stored as a full copy with a `base` reference?** Recommend: yes, with Reset and
   "Update from preset". Alternative: a JSON Merge Patch over the base, as §12.3's "diff"
   literally says.
5. **Safety items: move only, or also re-icon and rename?** Recommend: move (and resize the
   cards) only; icons, words and colours fixed for recognition at a glance. Alternative: allow
   re-icon and rename, colour and status word fixed.
6. **Keep the five-slot cap?** Recommend: yes, More plus four free slots, the rest one tap
   away under More → Pages. Alternative: up to six on HU-9/10 and HU-wide only.

## Notes on sources

- **python-OBD licence (conflict resolved).** Checked 2026-10-05: PyPI metadata says `GPL-2.0-only`
  and the README "GNU GPL v2", but the `obd/__init__.py` header says "version 2 … or (at your
  option) any later version". They disagree, so we take the conservative reading ADR-0012
  requires, GPL-2.0-only. Either way: ideas only, no code.
- **URLs from the generated-UI note** came from prior knowledge. Checked 2026-10-05: reachable are the
  HA strategy and entity docs, OVMS web-framework docs, Android `VehiclePropertyIds`, Grafana
  overrides, rjsf, Adaptive Cards, the Tesla Fleet API and VSS docs; **broken** are the Signal K
  `latest` data-model page (the 1.7.0 page works) and the OVMS app guide; **unverified** (GitHub
  unreachable here) are KIP, OBDb SAEJ1979/`.schemas` and the Signal K repo. No decision rests on
  them.

## Changelog

- 2026-10-06: v0.1, first draft from the seven UI research notes; resolves the namespace (VSS
  canonical) and python-OBD licence conflicts.
- 2026-10-06: v0.2, approved. §11 becomes the owner's decisions (ADR-0016, ADR-0018; also ADR-0017,
  ADR-0019, ADR-0020); §10.1 adds the standards plan per phase; §5.1 unit fixed to the VSS 6.1 key
  `Celsius`; §5.6 locked by ADR-0016; §6 adds the `comfort` class and 360° cameras as a future item; §7 adds imported actions (ADR-0019);
  local HTTPS decided (ADR-0021).
- 2026-10-06: v0.3. §10 adds the U3 polling rule: the recording set is always polled, and the
  visible-signals subscription only raises priority or rate, never removes a recorded channel;
  §10.1 notes that U4 needs ADR-0022 (K-line profiles and detection) and ADR-0023 (passive CAN
  bitrate detection).
- 2026-10-06: v0.4, amendment for the node/brain direction (stays approved; ADR-0032, ADR-0033).
  §7.1 adds action categories as a second axis to tiers, default roles and the kiosk session
  (Read + Comfort); the Tier 1 row runs Parked or Idling for Maintenance with an automatic
  snapshot, a safety-system warning and an audit entry; §3.5 lets Idling permit Maintenance and
  Moving permit Comfort and arming; §7.2 adds phone approval of Tier 2–3 over local links and the
  `OSTLER_ALLOW_REMOTE_CONTROL` install override, replacing "remote is Tier 0"; §3.4 adds the
  landing screen that follows the driving state and makes Security present with any node (no more
  "Map when no guardian"); §4.1 adds cross-vehicle replay (pack and manifest switch, sessions
  record pack id, version and manifest `etag`, parked periods and alarm events); §4.4 VIN wording
  per ADR-0036; §5.1 and §6 bring in the node and its variants through a per-hardware capability
  manifest, GPS and 12 V from the node, relay boards as our own later boards with an ADR per
  switching function, and the `comfort` render class renamed `add-on device`; §3.1 notes the phone
  app packaged with Capacitor; §11 Q4, Q5 and Q10 annotated.
- 2026-10-06: v0.5, amendment for the app model (stays approved). §3.6 adds one shell with
  features as apps declared by a manifest, core apps (Diagnose, Logs, Security, Network) in the
  platform repo, optional apps from their own repos, no separate PWAs and nothing built before
  U1; §10's U1 row leaves the app-model seams. Detail in the draft
  [app-model spec](2026-10-06-app-model-design.md).
- 2026-10-06: v0.6 (stays approved). §8.4 and §3.6: Decode lab is a core app in the platform
  repo, shown only in service mode (owner answer to app-model spec Q5).
- 2026-10-06: proposed amendment, pending owner answers (no version change; nothing above
  is changed): §3.7 renames More → Devices to a Network page (devices, transports and link
  health, role holders, uplinks and metering, remote access, certificates and pairing), adds
  a read-only peer view to every device's own page, and builds the cluster view from each
  device's published manifest (ADR-0037, proposed).
- 2026-10-06: v0.7, owner's networking answers (stays approved; ADR-0037, ADR-0038). §3.7 is
  accepted: Network is a core app that absorbs More → Devices (devices and device pages,
  transports and link health, role holders, uplinks and metering, remote access,
  certificates and pairing), every device's own page gains a read-only peer view, and the
  cluster view is built from each device's published manifest; §3.4's More row and §6's
  device pages read Network; §5.1's device entries gain `board`, `roles`, `transmit` and
  `items` (with `origin` and `status`), and the signal's Home Assistant entity category is
  renamed `ha_category` so it never collides with ADR-0033's action `category`.
- 2026-10-06: proposed amendment, pending owner answers (no version change; nothing above
  is changed): §3.8 adds power states and badges (asleep is not offline), the brain's state
  and queued actions in the Link chip, wake confirmations with cost, queued actions with
  expiry and Cancel, a Power column and section on the Network page, "Needs the hub" cards,
  the phone-standalone case and manifest fields `power`, `runs_on`, `needs_brain`,
  `queueable` (ADR-0040, proposed).
- 2026-10-06: v0.8, owner's power-state and product-family answers (stays approved;
  ADR-0039, ADR-0040). §3.8 is accepted: power states and badges (asleep is not offline), the
  hub's state and queued actions in the Link chip, a brain-wake confirmation sheet for remote
  requests only (local wakes do not ask; "Don't ask again" is stored per user and device and
  honoured on local links only), queued actions with expiry and Cancel, a Power column and
  section on the Network page, "Needs the hub" cards, the phone-standalone case and manifest
  fields `power`, `runs_on`, `needs_brain`, `queueable` and `expires_max_s`. §3.7's "reached
  via" gains USB (the USB-NCM node link, ADR-0039 §4). "Lite" reads Ostler Diagnostics.
- 2026-10-06: v0.9, owner's Brain rename and parked-broker answers (stays approved; ADR-0039
  and ADR-0037 Amendments). The brain product is **Ostler Brain** (was Hub): §3.8's chip,
  sheet, refusal and card texts read "Brain" ("Brain asleep", "Waking Brain", "This needs
  the Brain", "Needs the Brain"). §5.1's device entries gain `memory` (`psram_kb`), and a
  `pbroker` role entry may carry `max_clients` (at most 5 until the bench), so an always-on
  add-on module with at least 2 MB of PSRAM can be the last parked-broker fallback.
- 2026-10-06: as built, U1 Shell (no decision changed; the spec stays v0.9). Built in
  `ui/src/shell/` and `ui/src/destinations/`: the six layout classes and the kiosk flag,
  the strip as chip descriptors (worst telltale, Link with the system in session and the
  node's power badge from §3.8, REC, 12 V, clock, Mark; the phone keeps 2–5 and 9), the
  rail or bottom bar from a destination registry, Home / Diagnose / Logs / More holding
  today's screens, Drive mode, module select into Diagnose (list pane on HU-9/10, HU-wide,
  tablet, desktop; compact switcher on HU-7 and phone), the fault modal replaced by the
  telltale, and the app-model §9 seams; tokens, Material Symbols, the manifest and `Intl`
  per §10.1. Deferred by design: driving state and every lockout (U2; until then the state
  is "unknown", landing is Home and the server gate decides), the Vehicle chip (U6),
  Security and the device slot (registered, hidden until a node manifest, U5), Overview
  and Scan all (U3), the Brain's state in the Link chip (no data yet), Network (later),
  `driver_side` in the pack layout (rail on the left until the pack declares it).
  Playwright covers 1024×600, 1280×720, 1920×720 and 393×852 with target-size asserts and
  an axe WCAG 2.2 AA scan per class.
- 2026-10-06: v0.10, §5.1 item `status` gains `unverified` (the node's K-line item until an
  init succeeds; `ostler-firmware` 0426ea5, sensor-detection §2).
- 2026-10-06: as built, U1 follow-ups (owner's approval of 2026-10-06; no decision changed,
  the spec stays v0.10). §3.3: `schemas/layout.schema.json` gains `driver_side`
  (`"left" | "right"`) and the shell reads it from the pack layout (the kiosk flag still
  overrides; absent means left); the D2 pack declares `"right"`. §3.8: the Link chip's power
  badge gains **Off**, the word already in the badge list, with the note that Off wins over
  Offline because the power owner reports it. The page title reads **Ostler** (was "D2 Diag"),
  the Web App Manifest's name.
- 2026-10-06: v0.11, plan notes from the owner's answers to the module-bus message spec
  (v1.3 §17): §3.7 the owner action **Remove device** on a device page (local links only,
  one confirmation naming the bus that becomes writable; the only way to clear a stale gate
  claim) and the one-tap remedy in Roles; §3.8 queue offered only when the target checks in
  before the expiry; §7.2 confirm first, then challenge and sign. Not built yet.
- 2026-10-07: v0.12, proposed amendment, pending the owner's answers (nothing in §1–§11 is
  changed): §12.1 U2 lockouts (driver-facing displays, Park evidence for Idling, per-trip
  Passenger view limited to UK reg 109 content, Open on phone, calls audio only, no message
  content in alerts, no other vehicles on the head-unit map except opted-in convoy markers,
  templates `map`, `media`, `tiles`, `alert_card`, `short_list` and `call` with limits, task
  depth ≤ 3, the "Using Ostler while driving" page, a legal check before U2 ships, §10 and
  §10.1 U2 rows); §12.2 Logs → Trips (aliased routes, unchanged API, two-tier summary index,
  trip list, trip detail, playback, Statistics, Records and Sprints with a data table per
  view, sprint gating, End trip now, Exclude from stats, Export all, no score); §12.3 Drive
  layouts as data, one-screen Drive mode with an HU-5 800×480 class and a no-scroll
  Playwright assert, map-first Analysis; §12.4 the Add-ons catalogue at More → Add-ons (top
  of More) and an empty-state Home card suggesting add-ons.
- 2026-10-07: v0.13, **§12 approved by the owner on 2026-10-07 ("approve all")**: §12 renamed
  "Amendment (2026-10-07), approved"; its subsections now change the sections they name;
  every "Decisions for the owner" item answered as recommended (alternatives not chosen);
  ADR-0042 and the visual design system and Social specs cited as approved; ADR-0009's
  basemap rule amended to match §12.3 (Ostler Night/Day on Brain-served PMTiles,
  OpenFreeMap online fallback, `bg` offline); §12.5 amends §2 principle 7 for the visual
  spec's glow budget and calm gauges. Build order: the Drive-mode fit fix (HU-5 and
  the no-scroll assert), V1 visual, the U2 lockouts, Trips.
- 2026-10-07: v0.14, proposed amendment (DMD round), awaiting the owner's answers (nothing in
  §1–§12 is changed): §13 adds the Trips share sheet (audience first, the L0–L4 ladder in plain
  language, a preview rendered from the real output with a redaction report, expiry and link
  controls, a privacy-zone line), "Get help with this fault" in Diagnose, "Ask for help
  decoding" and Run a recipe in Decode lab, More → Places for privacy zones and the ends trim,
  and a map theme independent of the app theme.
- 2026-10-07: proposed amendment (DMD round) "message alerts": sender + app with Play /
  Reply, canned replies, opt-in stopped-only first-line preview, rate limits, legal-check
  items (Decisions M1–M4); the approved §12.1 rule stands until answered.
- 2026-10-07: v0.14, **proposed amendment §15 (DMD round), Drive modes and editing**, pending the owner: several Drive modes as layouts with faces and a strict Moving section, seven presets, a Drive-mode strip chip (tap cycles, long press lists), Park to edit enforced by the server, Home edit mode with a widget picker, rail pins for add-on pages within the five slots, non-removable safety items, layout files; decisions 1–4 (drive-modes spec; app-model §15).
- 2026-10-07: proposed amendment §13 revised in place (DMD round, cross-spec reconcile with community hub spec v0.2): the share sheet's and Diagnose → Get help's hub send path reads "Ask on Ostler Community"; Decode lab → Ask for help decoding creates a Help thread on the closed, Ostler-run hub with end-to-end encrypted attachments; DMD decision 4 revised.
- 2026-10-07: proposed amendment §15 revised (DMD round) for the owner's "the entire UI is editable, with no fixed icons": no locked rail slots (More anchored but movable), a user-ordered strip with safety chips that move but never go, re-icon from Material Symbols and rename with limits and i18n, hide and replace with More → Pages, edit mode by long press on the strip or any empty area, Reset layout in More and the Connection sheet; §15.3 tests extended; §15.4 decision 3 revised, decisions 5–6 added.
- 2026-10-07: v0.15, **§13–§15 approved by the owner on 2026-10-07 ("approve all", DMD
  round)**: renamed "Amendment (2026-10-07, DMD round), approved"; every DMD-round decision
  (1–6, M1–M4, §15.4's 1–6) answered as recommended (alternatives not chosen); §14's message
  alerts applied into §12.1 (the Message alerts bullet replaces "Add-on alerts never show
  message content", the `alert_card` row, the legal-check questions and the U2 tests), with
  the earlier rule kept as history; Dashboard is the head-unit default; the trip-sharing,
  Drive-modes, ShellInput and app-model §15 specs and ADR-0043 cited as approved.

## Decisions for the owner (amendment of 2026-10-07)

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **Head-unit passenger override: what may it unlock?** Recommend: Passenger view for
   driving-related content only (vehicle state, own route and location, driving cameras),
   everything else via Open on phone with the full phone override (§12.1). Alternative: the
   owner's original, where the head-unit override unlocks all viewing.
2. **Should Idling need Park evidence for text entry, Maintenance and `engine_running_ok`?**
   Recommend: yes, handbrake or neutral (sensed or inferred) for > 3 s, else Moving rules.
   Alternative: keep Idling as §3.5 has it.
3. **Passenger view end conditions?** Recommend: 15 minutes plus Parked, ignition off, new
   trip, unknown speed, reverse, service mode and any red telltale. Alternative: those exits
   with no timeout.
4. **Where does the override log live?** Recommend: local only, owner-visible, kept with the
   trip, never synced unless the owner exports the trip. Alternative: no log at all.
5. **Other vehicles on the head-unit map while Moving?** Recommend: none, except opted-in
   convoy members of an active group as plain markers. Alternative: none at all.
6. **Moving template set?** Recommend: the existing five plus `map`, `media`, `tiles`,
   `alert_card`, `short_list` and `call` with the §12.1 limits, task depth ≤ 3, new templates
   only by platform proposal. Alternative: the existing five only until a companion app forces
   more.
7. **Legal gate for U2?** Recommend: Passenger view and the phone override are not released
   until a UK road-traffic opinion on reg 109 is recorded (Open on phone only until then), and a
   product-liability opinion before hardware sales. Alternative: ship them with the warning
   page and no opinion.
8. **Rename Logs to Trips?** Recommend: yes, everywhere in the UI, with `logs` routes aliased
   and the `/sessions` API unchanged. Alternative: keep "Logs" and add Trips as a tab inside it.
9. **Where do Statistics and Records live?** Recommend: tabs inside Trips, keeping five
   destinations. Alternative: a sixth destination, breaking the cap.
10. **Sprints before fast GNSS?** Recommend: only with ≥ 10 Hz speed or a calibrated IMU,
    "Needs fast GPS" otherwise. Alternative: show 1 Hz sprints labelled as estimates.
11. **Trip controls?** Recommend: End trip now and Exclude from stats, no pause. Alternative:
    add a manual pause as Odo has.
12. **Drive layouts?** Recommend: layouts as data per layout class with VSS-bound tiles and
    normal/warning/critical levels, a grid editor Parked only, no pixel editor in v1.
    Alternative: pack-declared and generated layouts only, no user editing.
13. **Add HU-5 (800×480) and the no-scroll Drive assert?** Recommend: yes, as the first fix,
    before U2. Alternative: let 800×480 fall into HU-7 with fewer tiles.
14. **Map-first Analysis?** Recommend: yes, about 55 % of the height on phone and half the
    width in landscape with the sheet on the passenger side. Alternative: keep the map as a
    card above the analysis.
15. **Where does the Add-ons catalogue live?** Recommend: More → Add-ons as the top entry of
    More, plus a dismissible empty-state Home card suggesting add-ons. Alternative: a sixth
    rail item or a separate Settings page (breaks the five-destination cap or adds a page).

## Decisions for the owner (DMD round, 2026-10-07)

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each recommendation
below is the decision; each alternative was not chosen.

1. **Audience before level in the share sheet?** Recommend: yes, with levels the audience
   cannot take greyed and explained. Alternative: level first, audience second (Strava's
   order).
2. **The five-row ladder with the plain-language lines in §13.1?** Recommend: yes, warning
   token from L3. Alternative: three simple choices (Card, Route, Help) with L2–L4 behind
   "More".
3. **Preview rendered from the real output, with hidden ends as a dashed fade (never a
   circle) and a redaction report?** Recommend: yes. Alternative: a list of what is removed
   and no rendered preview (cheaper, but not proof).
4. **"Get help with this fault" in Diagnose and "Ask for help decoding" in Decode lab?
   (revised, reconcile)** Recommend: yes, Parked only, never changing anything on the car;
   their hub send path reads "Ask on Ostler Community" and creates a Help thread on the one
   official hub with end-to-end encrypted attachments (Decode lab's always does when the hub
   add-on is on). Alternative: one help entry in Trips only.
5. **Privacy zones at More → Places, after Network?** Recommend: yes, one definition read by
   every app. Alternative: inside More → Privacy (one entry fewer, harder to find).
6. **A map theme independent of the app theme (Follow app, Day, Night, High contrast)?**
   Recommend: yes, Follow app by default. Alternative: maps always follow the app theme.

Message alerts (§14):

M1. **Message card while Moving: sender and app with Play / Reply?** Recommend: yes (Android
    Auto, CarPlay), names under the U2 legal check with "New message" as the fallback.
    Alternative: the earlier rule, "Message from *name*" with Play / Later.
M2. **Canned replies?** Recommend: Reply opens a `short_list` with Speak a reply plus up to
    five owner-editable canned replies (≤ 30 characters, edited Parked only, one tap sends).
    Alternative: voice note and the "I'm driving" auto-reply only, no list (Social §8 as first approved).
M3. **First-line preview?** Recommend: owner opt-in, default off, one line ≤ 30 characters,
    only for messages that arrive while Parked or Idling with Park evidence (Parked only
    until the legal opinion), never while Moving, never on a passenger-only display, never
    images. Alternative: the owner's literal ask, a preview while Moving, released only if the
    U2 opinion explicitly clears it.
M4. **Rate limits?** Recommend: one card at a time, one per conversation per 2 minutes, three
    per 10 minutes, groups other than the ride as a count only, never over safety surfaces.
    Alternative: one card per message with no cap.

Drive modes and editing (§15): see §15.4, decisions 1–6 (decision 3 revised for "the entire
UI is editable, with no fixed icons"; decisions 5–6 added), all answered as recommended.
