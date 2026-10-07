---
title: "Designer brief: hardware (c) — Brain setup and health, GPS fix and sky view, IMU mounting and levelling"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-05-replay-notes-capture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, references/research/hardware.md, references/research/node_sensors.md]
summary: >
  Covers the Ostler Brain's own page (power board and ignition lease, clean shutdown and
  boot timeouts, battery floors, storage, temperature, its link to the node, and the Wi-Fi
  and hotspot uplinks that open the existing Network sections), the GPS page (both
  receivers, which one is selected and why, fix type, satellites, accuracy, fix age, the time
  source, a proposed sky view, position disagreement, and location privacy), the IMU page
  (detected chip, mounting orientation, live specific force and candidate tilt) and the
  proposed calibrate-while-still levelling flow with its step list. All are Parked pages;
  remote paths read only.
---

# Hardware brief (c): Brain, GPS and IMU

Shared rules are in [file (a)](20-hardware-a-devices.md#rules-every-hardware-page-follows).

### hw-brain — Ostler Brain: setup and health  [New]
- **Owner:** os
- **Purpose:** the Brain's device page, with what matters for a computer in a car: power,
  heat, storage and its links.
- **Opens from → goes to:** Network → Devices → Ostler Brain (a `network-device` with these
  sections). Goes to `hw-power`, `hw-brain-update`, `hw-device-logs`, Network → Uplinks
  (`network`, Existing).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu9 Night, phone Day, phone Night with the Brain asleep.
- **Content (top to bottom):**
  1. Header: "Ostler Brain", power chip ("Awake · kept awake by ignition until ignition off
     + 10 min"), last seen.
  2. **Power** card: "Power board · ignition sense OK"; "Shuts down cleanly; cut after 60 s if
     it hangs"; "Boot timeout 60 s · after two failed boots today, wakes need a local
     request"; floors "12.0 V: no Brain wakes, an awake Brain shuts down" ([ADR-0040][a40-4]).
  3. **Storage** card: system ("read-only"), logbook and clips used of total, map regions
     size; warn at a set fill level with "Free space" → Trips export or Maps regions.
  4. **Temperature** card: board °C now and today's maximum; warn word when the board slows
     itself ("Running slower to cool down").
  5. **Link to the node** card: "USB link · Ostler Diagnostics online" or "T1S segment 1 ·
     PLCA coordinator: Ostler Diagnostics"; "Brain never talks to the car itself".
  6. **Network** card: Wi-Fi client ("Phone hotspot", "Home Wi-Fi") and the Brain's own
     access point for displays and phones, each with signal; "Uplink manager: Ostler Brain";
     **Open Uplinks** → `network`.
  7. **Services** ListRows with status words: broker, recorder, map tiles, camera recorder.
  8. Actions: **Logs**, **Update**, **Restart**.
- **States:** asleep (from the node's retained data: "Brain asleep · wakes on ignition,
  phone or schedule · last seen 3 h"; Wake per [UI §3.8][ui38]); waking ("Waking Brain · 12 s");
  failed boot ("Brain failed to start; locked for 1 h"); no Brain fitted (page absent;
  Diagnostics-only product); Brain-only car (no node: "Wakes from its power board: ignition
  and schedule only. No remote wake or parked alarm." ([ADR-0039][a39])).
- **Safety and driving rules:** while Moving the Brain is held by the ignition lease and no
  wake prompt appears; the page is a locked view. Remote: read-only, Wake under quota.
- **Components:** Card, StatTile, ListRow, Chip (status), Button.
- **Spec refs:** [UI §3.8][ui38], [App model §13][am13], [ADR-0040 §2][a40-2],
  [ADR-0039][a39], [ADR-0028][a28].
- **Open questions:** storage and temperature readings are not in any manifest yet; the warn
  thresholds need numbers from the bench (cabin heat 60–80 °C, [hardware research][hw-r]).

### hw-gps — GPS: fix, accuracy and sky view  [New]
- **Owner:** os
- **Purpose:** show whether the car knows where it is, from which receiver, and how well.
- **Opens from → goes to:** a GPS item row under a device; Security's fix age; Trips "No
  GPS" notice. Goes to the device page of each receiver.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Day.
- **Content (top to bottom):**
  1. **Selected source** HeroStat-sized line: "Using u-blox on Ostler Diagnostics" or
     "Using Guardian (lower rate)" with the reason word ("Parked, ignition off").
  2. Per receiver, a Card: name ("u-blox · 10 Hz", "Guardian GNSS · 1 Hz"), fix type (No
     fix, 2D, 3D, Dead reckoning), satellites used, horizontal accuracy (m), speed accuracy,
     fix age, rate, antenna ("Active antenna · on" or "off while parked").
  3. **Sky view** (proposed element): a SkyPlot of satellites by direction and elevation,
     each dot labelled by constellation letter and signal word, never colour alone.
  4. **Time** row: "Time source: Ostler Diagnostics · GNSS with PPS" or "Unsynced".
  5. **Checks**: "Position disagreement" event (warn) with time; "Speed check · wheel vs
     GPS ratio" (Read).
  6. Small own-position map (Ostler Night or Day), Parked only.
- **States:** no fix ("Searching · ‹n› satellites seen"); last fix kept with its age, never
  re-dated; receiver absent (card not drawn); u-blox powered down while parked; remote
  viewer without location sharing: fix type and accuracy only, no map or coordinates.
- **Safety and driving rules:** location stays on the device unless shared
  ([ADR-0009][a09]); Moving locked view.
- **Components:** HeroStat, Card, StatTile, SkyPlot (new component), Chip (status), Sheet
  over map (small map), ListRow.
- **Spec refs:** [ADR-0032 A][a32a], [ADR-0039][a39], [ADR-0037][a37], [UI §3.5][ui35].
- **Open questions:** the sky view needs per-satellite data that the node does not publish
  yet; approve it as a module-bus addition or drop the element.

### hw-imu — IMU: mounting and readings  [New]
- **Owner:** os
- **Purpose:** show the IMU's state and whether its tilt can be trusted.
- **Opens from → goes to:** an IMU item row; the Off-road Tilt tile's "Needs the node's IMU"
  card; `hw-install-done`. Goes to `hw-imu-calibrate`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night, hu7 Night.
- **Content (top to bottom):** 1. Chip and origin ("Detected · I²C"), status word.
  2. **Mounting** card: "Forward is the device's ‹axis›", "Up is ‹axis›", "Screwed down"
  tick; **Change** (Parked). 3. **Live** StatTiles: specific force on three axes (g); pitch
  and roll in degrees marked `candidate`, shown only below 0.1 g ("Moving too much to
  show tilt"). 4. **Levelled** row: "Levelled 14:02 · method: still" or "Not levelled".
  5. **Level now** (primary) → `hw-imu-calibrate`. 6. On a Guardian: "Alarm tilt baseline is
  taken each time you arm" (text).
- **States:** not levelled (tilt tiles show "Level the IMU first"); absent (page not
  reachable; the tile says "Needs the node's IMU"); fault; asleep (grey with age).
- **Safety and driving rules:** Read only; Moving locked view.
- **Components:** Card, StatTile (candidate state), Chip, Button.
- **Spec refs:** [Drive modes §5.5][dm55], [ADR-0032 B][a32b], [node sensors §7][nsr7].

## Level the IMU: step list

| # | Screen | The user does | What can fail | Recovery |
|---|---|---|---|---|
| 1 | `hw-imu-calibrate` (Prepare) | parks on level ground, engine off, doors shut, gets out or sits still | not Parked; engine running | "Park and switch the engine off" |
| 2 | `hw-imu-calibrate` (Mounting) | confirms forward and up axes | axes not set | defaults from the board profile |
| 3 | `hw-imu-calibrate` (Hold still) | waits 10 s | movement detected | "Movement detected. Start again." |
| 4 | `hw-imu-calibrate` (Result) | saves or discards | far from level | "The car is tilted ‹deg›°. Save anyway or move the car." |

### hw-imu-calibrate — Level the IMU (calibrate while still)  [Proposed]
- **Owner:** os
- **Why the app needs it:** tilt on the Off-road preset is derived from the levelled
  gravity vector; without a guided, still capture the levelling matrix is wrong or missing.
- **Purpose:** capture the levelling matrix while the car is still.
- **Opens from → goes to:** `hw-imu` → Level now; `hw-install-done`. Back to `hw-imu`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night (four frames, one per step).
- **Content (top to bottom):** Stepper "1 of 4" … "4 of 4". Step 1: checklist rows
  (Parked, engine off, doors shut, nobody moving). Step 2: two Segmented controls, Forward
  axis and Up axis, with a simple device outline showing arrows. Step 3: "Hold still ·
  ‹seconds› s" in text (no animated ring), and a stability word ("Still" or "Moving").
  Step 4: result rows "Pitch 0.0° · Roll 0.0° (candidate)", "Method: still", **Save**
  (primary) and **Discard**.
- **States:** movement (step 3 restarts); device asleep ("Wake Ostler Diagnostics first");
  remote (hidden).
- **Safety and driving rules:** Parked with the engine off; local links only. It writes
  only our own device's settings, never the car.
- **Components:** Stepper (new component), Segmented, Card, StatTile, Button.
- **Spec refs:** [Replay and notes capture][rn] (`accel_cal` matrix and method),
  [Drive modes §5.5][dm55].

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[a28]: ../../../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[a32a]: ../../../../decisions/adr-0032-one-node-optional-brain.md#a-gps-split-two-receivers-two-jobs
[a32b]: ../../../../decisions/adr-0032-one-node-optional-brain.md#b-sensor-detection-one-firmware-manifest-from-hardware
[a37]: ../../../../decisions/adr-0037-role-holders-and-handover.md#2-the-roles
[a39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[a40-2]: ../../../../decisions/adr-0040-power-states-and-wake.md#2-states-per-device-type
[a40-4]: ../../../../decisions/adr-0040-power-states-and-wake.md#4-wake-requests
[am13]: ../../../../specs/2026-10-06-app-model-design.md#13-power-states-wake-and-queued-actions-accepted-2026-10-06
[dm55]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[hw-r]: ../../../research/hardware.md#risks
[nsr7]: ../../../research/node_sensors.md#7-placement
[rn]: ../../../../specs/2026-10-05-replay-notes-capture-design.md
[ui35]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui38]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
