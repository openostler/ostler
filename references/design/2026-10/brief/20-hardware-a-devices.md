---
title: "Designer brief: hardware (a) — the Devices list, device pages, logs, restart and the device's own page"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md]
summary: >
  First of six hardware brief files (screen prefix hw-). It sets the rules every hardware
  page shares (driving states, remote paths read-only, honest power words, the node gate as
  the only path to the car) and covers the Devices list inside Settings → Network (node,
  Guardian, Brain, displays, adapters, GPS and IMU items, cameras, remotes, phones, mesh
  radios), the device page with its health (signal, temperature, storage, uptime, power,
  firmware) and its actions (Logs, Restart, Remove device), the Add a device chooser that
  routes to install guides or to onboarding's pairing wizard, and the firmware-served
  device page with its read-only peers. Later files: install guides (b), Brain, GPS and IMU
  (c), cameras and power (d), updates and buttons (e), security, mesh and service mode (f).
---

# Hardware brief (a): Devices and device pages

The hardware area is everything a person fits, wires, checks, updates or removes. Six files:
**(a)** this one; **(b)** [node install guides](20-hardware-b-install.md); **(c)**
[Brain, GPS and IMU](20-hardware-c-brain-gps-imu.md); **(d)**
[cameras and power](20-hardware-d-cameras-power.md); **(e)**
[updates and buttons](20-hardware-e-updates-input.md); **(f)**
[security, mesh and service mode](20-hardware-f-security-mesh-service.md). The first-run
pairing wizard belongs to onboarding (`10-onboarding-*`); these pages start after a device
is paired, or hand over to that wizard.

## Who owns these screens (direction of 2026-10-07)

Ostler is an Android-style OS. Devices, the Brain, node install, GPS, IMU, power, updates,
buttons, service mode and the device pages of cameras and mesh radios are **system** screens
(`Owner: os`), reached from system Settings → Network in the app drawer. The alarm, tracker
and walk test belong to the Security app (`app:security`). Viewing cameras is the Camera app
(`app:camera`, 80-hu-* files); using a mesh radio is the Social app (`app:social`). Safety
rules stay with the OS whatever the owner.

## Rules every hardware page follows

Example values in this brief are written as ‹placeholders› or quoted from a spec; the
designer draws real values from the pack's signal store, never invented numbers.


1. **Words for products.** Ostler Diagnostics (the OBD-port node), Ostler Guardian (hidden,
   battery-backed, no outputs), Ostler Brain (compute; never touches the car where a node
   exists) ([ADR-0039][a39]). The node gate is the only path to the car; an adapter talks to
   the car only when no node is fitted, through the soft gate ([ADR-0044][a44]).
2. **Driving states.** Network and its device pages are Parked and Idling pages. Idling needs
   Park evidence for text entry and changes. While Moving a driver-facing display shows the
   locked view, "Available when parked", with **Open on phone** ([UI §3.7][ui37],
   [UI §12.1][ui121]). A phone keeps reading with the Moving banner; its actions keep the
   stationary check.
3. **Remote paths are read-only.** Over Tailscale or the Ostler Cloud relay, every page shows
   the banner "Viewing remotely · read-only". Only **Wake** stays, under the remote quota.
   Remove device, Restart, Update, Calibrate, bindings and install steps are hidden, not
   greyed ([ADR-0033 §6][a33-6], [UI §3.7][ui37]). A mesh path shows nothing to act on.
4. **Power words, icon plus word:** Awake, Asleep (last seen and how it wakes), Waking…
   (seconds against the expected time), Kept awake (by whom, until when), Shutting down,
   Off, and Offline (amber, only for an unexpected loss) ([UI §3.8][ui38]). Asleep keeps last
   values in stale grey with their age, never zero.
5. **Honest items.** A sensor item shows its origin (board, detected, harness, config) and
   status: OK, Absent, Fault, No signal, Refused, Unverified ([ADR-0032 B][a32b],
   [NodeSource §16][ns16]). Absent hardware draws nothing; a declared but silent input says
   "No signal".
6. **No demo data.** Every value on these pages comes from a real device. Before one is
   paired the page shows its empty state, never sample rows ([ADR-0011][a11]).

### network — Settings → Network: Devices and power sections  [Existing]
- **Owner:** os
- **Purpose:** one list of every device in this car's cluster, with health and power, and
  the way in to each device page.
- **Opens from → goes to:** Settings → Network (system Settings, from the app drawer); the Link chip sheet's "Devices" row; Home device
  cards. Goes to `network-device`, `hw-add-device`, `hw-power`, `hw-mesh-radios`; Uplinks,
  Remote access and Certificates sections stay as in the Network spec.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Day, phone Night with a remote banner.
- **Content (top to bottom):**
  1. Title "Network", age banner when the host's inputs are stale ("Cluster view 3 min old ·
     read-only").
  2. **Devices** section, one ListRow per device: icon, name ("Ostler Diagnostics",
     "Ostler Guardian", "Ostler Brain", "Head unit (driver)", "Rear camera"), kind and
     variant, power chip (word), reached via ("USB", "T1S segment 1", "Wi-Fi", "BLE through
     phone"), last seen, chevron. Grouped: **Car side** (node, Guardian, adapters),
     **Compute and displays** (Brain, head units, phones as displays), **Sensors and
     cameras** (GPS receivers, IMU, cameras, add-on modules), **Radios** (mesh bridges).
  3. Under the node row, item sub-rows: "K-line (kline-diag) · OK", "GPS u-blox · 3D fix",
     "IMU · Unverified". Tap opens `hw-gps` or `hw-imu`.
  4. An adapter row only for a vehicle with no node: kind and verdict chip ("ELM: limited",
     "Clone: read-only", "Soft gate"), opening `adapter-verdict`.
  5. Phones: a single row "Paired phones (2)" linking to Accounts S6 (`accounts-s6`).
  6. **Power** summary card: today's energy against the budget ("‹used› of 240 mAh"), the
     floor in force, node parked mode (Ready or Deep); "Open Power" → `hw-power`.
  7. Button **Add a device** (primary) → `hw-add-device`.
- **States:** empty (no node, no Brain: "No devices yet" with **Add a device**); loading
  (skeleton rows); error ("Cannot build the cluster view" and Retry); offline (stale banner,
  read-only); no vehicle (Network still lists the Brain and displays); Parked and Idling
  full; Moving locked view; Passenger: not offered (not reg 109 content); locked (Viewer:
  read-only, no Add).
- **Safety and driving rules:** nothing here approves a car action ([UI §3.7][ui37]). Remote:
  read-only plus Wake. A lost role holder shows only as a row in the Link chip sheet while
  Moving, never a new chip.
- **Components:** ListRow, Chip (status: power word), Card, Button, Sheet (age banner as a
  tone Card).
- **Spec refs:** [UI §3.7][ui37], [UI §3.8][ui38], [App model §12][am12],
  [App model §13][am13], [Adapters §9][sa9].
- **Open questions:** should phones appear as full device rows or only as the Accounts S6
  link? (This brief assumes the link.)

### network-device — Device page: detail, health and actions  [Existing]
- **Owner:** os
- **Purpose:** everything about one device: identity, health, power, items, and the few
  owner actions that act on the device itself (never on the car).
- **Opens from → goes to:** a Devices row; the device's own page via "Open in Ostler". Goes
  to `hw-device-logs`, `hw-device-restart`, the Remove confirm sheet, `shell-buttons` (displays),
  `hw-brain` (Brain), `hw-gps`, `hw-imu`, `hw-camera`, `hw-mesh-radio`, `hw-firmware-update`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (node), phone Day (Guardian), hu9 Night (head-unit display with Buttons).
- **Content (top to bottom):**
  1. Header: icon, name (rename Parked only), kind and variant ("Ostler Diagnostics ·
     diag-port"), power chip, "Last seen 14:02".
  2. **Health** stat grid (StatTile): Signal ("Wi-Fi · ‹RSSI› dBm", "BLE", "USB link"), Temperature
     (board, °C), Storage (Brain and cameras: used of total), Uptime, 12 V at the device
     (node), Est. current ("‹mA› · parked-ready"). Missing reads "—".
  3. **Power** card: state, class ("Wakeable · wake wire"), next check-in, leases (holder,
     until), **Wake** where the role allows ([UI §3.8][ui38]).
  4. **Items** list (from the capability manifest): bus items ("K-line kline-diag · OK ·
     gate held"), sensors with origin and status, outputs listed as "Refused" on boards that
     allow none ([ADR-0032 B][a32b]).
  5. **Roles held:** "Transmit gate (kline-diag)", "Parked broker", "Time source" with since
     and term ([ADR-0037][a37]).
  6. **Identity:** model, board, firmware version, manifest etag (short), addresses, mDNS
     name, certificate expiry and fingerprint.
  7. **Add-on app sections** contributed through `network:device:<id>`.
  8. Display devices only: "Driver-facing" or "Passenger-only (set in the install
     configuration)" as read-only text, **Display settings** → onboarding's `setup-display`,
     and **Buttons** → `shell-buttons`.
  9. Actions row: **Logs**, **Update firmware**, **Restart**, **Remove device** (danger).
- **States:** asleep (values grey with age, "Node asleep · wakes on ignition, door or motion ·
  last seen 3 h"); waking; offline (amber); off; unverified items; loading; error. Remote:
  banner, only Wake. Moving: locked view.
- **Safety and driving rules:** Remove device is owner-only, local links only, with one
  confirm that names what changes: "Remove Node 2? It is unpaired and its retained data is
  deleted. K-line (kline-diag) becomes writable by Node 1." A gate conflict seen on the wire
  shows **Acknowledge** instead ([UI §3.7][ui37]). Confirm sheets open with Cancel focused
  ([Shell input §7][si7]).
- **Components:** StatTile, Card, ListRow, Chip (status), Button (danger: Remove device;
  Acknowledge), Sheet (confirm).
- **Spec refs:** [UI §3.7][ui37], [UI §3.8][ui38], [App model §12][am12],
  [NodeSource §10][ns10], [Shell input §8][si8].
- **Open questions:** temperature, storage and uptime are not yet in the manifest or the
  `power` record; they need a `health` field in the module-bus spec.

### hw-device-logs — Device logs  [Proposed]
- **Owner:** os
- **Why the app needs it:** a person fitting hardware needs to see why a device refused an
  init, a wake or a sensor; today only `connection.log` on the Brain holds that.
- **Purpose:** a read-only, filterable list of one device's recent events.
- **Opens from → goes to:** `network-device` → Logs. Back to the device page.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** tablet
  Night, phone Day.
- **Content (top to bottom):** 1. Filter chips: All, Bus, Power, Gate, Sensors, Errors.
  2. ListRow per event: time, level icon and word, one line, for example "fast-init td5 ·
  refused · bus-busy", "wake brain · refused · Battery 11.9 V", "gate · listen-only ·
  claim by Node 2". 3. **Export** (text file) and **Copy**.
- **States:** empty ("No events since 09:12"); loading; asleep (cached lines with age);
  remote read-only (no Export to the phone's files over remote).
- **Safety and driving rules:** read only; Moving locked view. No VIN or identity replies in
  any line ([ADR-0036][a36]).
- **Components:** Chip (filter), ListRow, Button.
- **Spec refs:** [K-line profiles §6][kl6] (logged events), [ADR-0040 §4.4][a40-4]
  (refusal reasons).
- **Open questions:** retention per device; whether the node keeps a ring of events in PSRAM.

### hw-device-restart — Restart confirm  [Proposed]
- **Owner:** os
- **Why the app needs it:** a stuck sensor or link is often fixed by a reboot, and the owner
  needs one honest way to do it that never interrupts a car session.
- **Purpose:** restart one device, saying what stops while it does.
- **Opens from → goes to:** `network-device` → Restart. Back to the device page, which shows
  Waking… then Awake.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content:** Sheet title "Restart Ostler Diagnostics?"; body lists effects: "Live data
  stops for about 20 s. The K-line session ends. The alarm keeps running on the Guardian." (the
  last line only when a Guardian is fitted); buttons **Cancel** (focused) and **Restart**.
- **States:** refused ("Not while moving", "Not during an active test"); restarting
  (progress words with elapsed seconds); failed ("No reply after 60 s", Logs link).
- **Safety and driving rules:** Parked only for the node and Guardian; local links only.
  Refused while an ActiveTestBanner is up or a procedure runs.
- **Components:** Sheet (confirm), Button (Cancel, primary Restart).
- **Spec refs:** [UI §3.5][ui35], [ADR-0033 §6][a33-6].

### hw-add-device — Add a device  [New]
- **Owner:** os
- **Purpose:** one chooser for anything a person fits, routing to the right guide.
- **Opens from → goes to:** Network → Add a device; Home "Fit a node" card; the adapter
  connect sheet's "what a node adds" line. Goes to onboarding's `setup-node-pair` (node,
  Guardian) or `setup-add-brain` (Brain), the install guides (`hw-install-pick`),
  `adapter-connect`, `hw-camera-add`, `hw-mesh-radios`, or `shell-buttons` (a remote).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night, hu7 Night.
- **Content:** title "Add a device"; ListRows with icon, name and one line: "Ostler
  Diagnostics · plugs into the diagnostic port", "Ostler Guardian · hidden tracker and alarm",
  "Ostler Brain · logs, cameras, replay", "Camera", "Remote or gamepad", "Mesh radio · works
  with Meshtastic", "Third-party adapter · only when no node is fitted", "Nearby devices"
  (unpaired Ostler devices seen as "nearby", no data).
- **States:** a node already fitted greys "Third-party adapter" with "Beside a node an
  adapter is listen-only"; remote: whole page hidden (pairing is local only).
- **Safety and driving rules:** pairing needs a physical press on the device and the owner
  ([ADR-0039][a39]); Moving locked view.
- **Components:** ListRow, Card.
- **Spec refs:** [UI §3.7][ui37], [ADR-0039][a39], [Adapters §9][sa9].

### device-local-page — The device's own web page  [Existing]
- **Owner:** os
- **Purpose:** the page each device serves itself, with no Brain or app, generated from its
  own manifest, with a read-only **Network** (peers) section.
- **Opens from → goes to:** the node's setup Wi-Fi or its address; "Open device page" in
  Network. Goes to peers' own pages; "Open in Ostler" deep-links to `network-device`.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night, desktop Day.
- **Content:** 1. Header: device name, variant, firmware, power word. 2. Its own sections
  from the manifest (a diag-port node: diagnostics and security; a Guardian: tracking, IMU,
  tamper, arm state, no diagnostics). 3. **Network**: peers seen by mDNS and on its broker,
  each with variant, firmware, health, roles claimed and a link. 4. "Open in Ostler" when a
  full-app host is reachable.
- **States:** setup mode (the AP is up; the page offers only the pairing hand-over, no car
  actions); no peers ("No other Ostler devices seen"); peer asleep (age).
- **Safety and driving rules:** it never acts on a peer; each control declares category and
  tier and is checked by this device's gate ([App model §12][am12]).
- **Components:** ListRow, Chip (status). Firmware-served: tokens compiled in, no shell.
- **Spec refs:** [UI §3.7][ui37], [App model §12][am12], [ADR-0039][a39].

[a11]: ../../../../decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md
[a32b]: ../../../../decisions/adr-0032-one-node-optional-brain.md#b-sensor-detection-one-firmware-manifest-from-hardware
[a33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[a36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[a37]: ../../../../decisions/adr-0037-role-holders-and-handover.md#2-the-roles
[a39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[a40-4]: ../../../../decisions/adr-0040-power-states-and-wake.md#4-wake-requests
[a44]: ../../../../decisions/adr-0044-adapters-on-the-brain-without-a-node.md#decision
[am12]: ../../../../specs/2026-10-06-app-model-design.md#12-the-network-app-and-device-pages-accepted-2026-10-06
[am13]: ../../../../specs/2026-10-06-app-model-design.md#13-power-states-wake-and-queued-actions-accepted-2026-10-06
[kl6]: ../../../../specs/2026-10-06-kline-profiles-detection-design.md#6-api-and-integration
[ns10]: ../../../../specs/2026-10-06-node-source-design.md#10-offline-asleep-and-stale-states
[ns16]: ../../../../specs/2026-10-06-node-source-design.md#16-as-built
[sa9]: ../../../../specs/2026-10-07-source-adapters-design.md#9-ui-summary-detail-in-u-phase-specs
[si7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[si8]: ../../../../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test
[ui35]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui37]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui38]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
