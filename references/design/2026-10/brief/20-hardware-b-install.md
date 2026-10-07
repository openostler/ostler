---
title: "Designer brief: hardware (b) — node install guides per bus (OBD port, D2 K-line, CAN, Brain link)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-02-hardware-platform-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-02-canbus-and-fast-signals-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, references/research/hardware.md, references/research/node_sensors.md]
summary: >
  The node install guide as one guided wizard with a variant per bus: plug into the OBD port
  (any car), the Land Rover Discovery 2 K-line (Td5 and SLABS on pin 7, with the BCU and
  airbag on the same wire), CAN (listen-only, passive bit-rate detection), the Brain link
  (USB or 10BASE-T1S where its ADR allows), and a wired-in Guardian. Every variant has the
  same six steps: pick the guide, wiring diagram cards, a fuse and power check, a "bus heard"
  check that transmits nothing, a test read through the node gate, and a finish summary.
  Gives the step list with what can fail and the recovery, then one block per step screen.
  All steps are Parked only; the guide is Proposed because no approved spec draws it.
---

# Hardware brief (b): node install guides

**Why the app needs it (Proposed):** the approved ADRs fix what a node may do on each bus,
but nothing tells a person how to fit one, prove the power is right or prove the car is
heard. Without a guide the first failure looks like a broken product. Onboarding's pairing
wizard (`10-onboarding-*`) pairs the device and sets the owner; this guide runs before it
(physical fitting) and after it (verify). It never pairs and never sets roles.

**Who and when.** Owner or a signed-in driver, on a phone, tablet, desktop or a Parked head
unit. Every step is **Parked only**: speed 0 for over 5 s and the engine off, with the
ignition on for the test read ([UI §3.5][ui35]). While Moving the guide shows the locked
view and resumes at the same step when Parked. Over a remote path the guide is hidden.

## The flow

| # | Screen | The user does | What can fail | Recovery |
|---|---|---|---|---|
| 1 | `hw-install-pick` | confirms the guide the vehicle pack suggests (D2 → K-line) or picks another | no vehicle chosen | "Choose your vehicle first" → Garage |
| 2 | `hw-install-wiring` | follows the diagram cards, ticks each card | wrong pins, missing ground | the card's "Check" line; Back |
| 3 | `hw-install-power` | turns the ignition on; the node measures 12 V and ignition | no 12 V, low battery, no ignition sense | fuse card; charge the battery; ignition card |
| 4 | `hw-install-heard` | waits while the node only listens | bus busy (another tool), silent bus, no bit rate | unplug the other tool; ignition on; Parked one-shot probe (CAN) |
| 5 | `hw-install-test-read` | taps **Read now**; sees live values | ECU refused, no reply, wrong car | ignition cycle; wait and retry as the pack says; re-pick the guide |
| 6 | `hw-install-done` | reads the summary; goes to GPS, IMU or alarm setup | — | — |

Variants (same six screens, different cards and checks):

| Variant | Wiring | Power check | Bus heard | Test read |
|---|---|---|---|---|
| **OBD port** (any car) | OBD socket: pin 16 battery +12 V, pins 4 and 5 ground, pin 7 K-line, pins 6 and 14 CAN | 12 V at pin 16; engine-running sense (> 13.2 V) | K-line quiet for 300 ms; CAN passive rate | detected protocol, then generic reads |
| **K-line: Land Rover Discovery 2 Td5** | pin 7 shared by Td5 (`0x13`), SLABS (`0x29`), BCU (`0x40`), airbag (`0x5B`); pins 4, 5, 16 | as above; ignition on | 300 ms quiet, no other tester | Td5 RPM, battery, coolant; then SLABS ride heights |
| **CAN** | OBD pins 6 (CAN high), 14 (CAN low), or a listen-only tap; never add termination to the car's bus | as above | listen-only at 500, then 250 kbit/s; 20 clean frames | one `01 00` once the rate is confirmed |
| **Brain link** | USB cable node → Brain (data only) or 10BASE-T1S pair | Brain power board: ignition sense, clean shutdown | Brain sees the node (status online) | a retained value arrives at the Brain |
| **Guardian, wired in** | constant 12 V, ground, ignition sense, door and OEM alarm taps through optocouplers | own cell charge, constant feed | Guardian heard on the broker | GNSS fix and IMU reading |

### hw-install-pick — Pick an install guide  [Proposed]
- **Owner:** os
- **Purpose:** choose the right guide for this car and device.
- **Opens from → goes to:** `hw-add-device`; Home "Fit a node" card; the "Fitting the node"
  link in onboarding's `setup-node-pair`. Goes to `hw-install-wiring`; after the guide,
  an unpaired device goes on to `setup-node-pair`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night (Parked).
- **Content (top to bottom):** 1. Stepper "1 of 6". 2. Vehicle line: "Land Rover Discovery
  2 Td5 · from the vehicle pack". 3. **Suggested** card: "K-line on pin 7 · Td5 and SLABS",
  with "The D2 has no CAN on its diagnostic socket". 4. Other guides as ListRows: OBD port,
  CAN, Brain link, Guardian wired in. 5. Device line: "Fitting: Ostler Diagnostics" (or
  Guardian, or Brain). 6. **Start** (primary).
- **States:** no vehicle ("Choose your vehicle first"); unknown vehicle (OBD port suggested,
  "We'll detect the bus when Parked"); a node already verified ("Installed and verified
  14:02 · Run again"); Moving locked view.
- **Safety and driving rules:** Parked only; nothing is sent to the car on this screen.
- **Components:** Stepper (new component), Card, ListRow, Button.
- **Spec refs:** [K-line profiles §2][kl2], [ADR-0039][a39].

### hw-install-wiring — Wiring diagram cards  [Proposed]
- **Owner:** os
- **Purpose:** show exactly which pins and wires connect, one card at a time.
- **Opens from → goes to:** `hw-install-pick` → `hw-install-power`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Day (in the footwell), tablet Night.
- **Content (top to bottom):** 1. Stepper "2 of 6". 2. Wiring diagram cards, swiped or
  stepped, each with a line drawing (token strokes, no photos), a title, 2–3 short lines and
  a tick box "Done":
  - **D2 card 1 "The diagnostic socket":** socket face with pins 4, 5, 7, 16 marked;
    "Pin 7 is the K-line. Every module on this car shares it." Location: "Find the socket
    under the dash" (exact place not yet recorded for the D2).
  - **D2 card 2 "One tester at a time":** "Unplug any other scan tool. The K-line carries
    one session at a time."
  - **D2 card 3 "Modules on pin 7":** a short list: Engine Td5 `0x13` fast init · SLABS
    `0x29` fast init · BCU `0x40` 5-baud · Airbag `0x5B` (read only).
  - **DIY card "K-line front end"** (shown only for a self-built node): transceiver on a
    UART, 510 Ω–1 kΩ pull-up to 12 V, diode on the supply pin; "proven on this car".
  - **CAN card:** pins 6 and 14; "Ostler only listens. Do not add a terminating resistor
    to the car's bus."
  - **Brain link card:** "USB: one cable, data only; the node keeps its own car feed" or
    "T1S: one twisted pair; pending its bench test".
  - **Guardian card:** constant 12 V with fuse, ground, ignition sense, door and alarm taps
    "through optocouplers only; taps never load the car's wiring"; "screw it down so the
    IMU reads real tilt".
  3. **Next** (enabled when every card is ticked), **Back**.
- **States:** a card ticked shows a check icon and word; Moving locked view; offline still
  works (cards ship in the app).
- **Safety and driving rules:** taps are read-only and isolated ([ADR-0032 B][a32b]); CAN is
  listen-only by default ([ADR-0020][a20]).
- **Components:** WiringDiagramCard (new component), Stepper (new component), Button.
- **Spec refs:** [Hardware platform: K-line front end][hp-k] (draft), [Node sensors §7][nsr7],
  [ADR-0039][a39].
- **Open questions:** the D2 socket location and its fuse number are not recorded; the
  owner should confirm them on the car before the cards ship.

### hw-install-power — Fuse and power check  [Proposed]
- **Owner:** os
- **Purpose:** prove the node has a good feed, sees the ignition and will not flatten the
  battery.
- **Opens from → goes to:** `hw-install-wiring` → `hw-install-heard`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** 1. Stepper "3 of 6". 2. Check rows, each with a status word:
  "12 V at the node · ‹volts› V · OK"; "Ignition · On · OK" (from the ignition input or the
  engine-running rule); "Battery floors · 12.2 / 12.0 / 11.8 V" (text, from
  [ADR-0040 §4.4][a40-4]); for Brain link "Brain power board · ignition sense OK"; for a
  Guardian "Own cell · charging". 3. If a check fails, a tone Card with the fix: "No 12 V at
  pin 16. Check the fuse for the diagnostic socket, then the connector." 4. **Next**.
- **States:** waiting ("Turn the ignition on"); low battery ("‹volts› V: below 12.2 V.
  Scheduled wakes will be refused. Charge the battery before going on."); no device reply
  (asleep or not powered).
- **Safety and driving rules:** Parked only; reads only.
- **Components:** ListRow (check row), Card (tone), StatTile, Stepper.
- **Spec refs:** [ADR-0040 §3][a40-3], [ADR-0040 §4][a40-4],
  [Hardware platform: power domains][hp-p] (draft).

### hw-install-heard — Bus heard  [Proposed]
- **Owner:** os
- **Purpose:** prove the node hears the bus before it ever transmits.
- **Opens from → goes to:** `hw-install-power` → `hw-install-test-read`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Day.
- **Content (top to bottom):** 1. Stepper "4 of 6". 2. One progress row per check, stepped
  (no animation): **K-line**: "Listening 300 ms · line quiet · no other tester"; the item
  "K-line (kline-diag) · Unverified" until the first init. **CAN**: "Listening at 500 kbit/s
  · ‹frames› clean frames", then "Heard: 500 kbit/s · 11-bit IDs". **Brain link**: "Brain
  sees Ostler Diagnostics · online". **Guardian**: "Guardian online on the broker".
  3. Result Card. 4. **Next**.
- **States:** bus busy ("Another tool is talking on the K-line. Unplug it and try again.");
  silent CAN ("No frames. Turn the ignition on." then a Parked-only **Probe once** button,
  one one-shot frame per rate, stopping at the first error frame); error frames ("Wrong
  wiring or bit rate"); never "OK" without a heard frame.
- **Safety and driving rules:** this step transmits nothing on K-line; on CAN only the
  ADR-0023 one-shot probe, Parked only, after a tap ([ADR-0023][a23]).
- **Components:** progress rows (ListRow with status), Card (tone), Button, Stepper.
- **Spec refs:** [K-line profiles §2][kl2], [ADR-0023][a23], [NodeSource §10][ns10].

### hw-install-test-read — Test read  [Proposed]
- **Owner:** os
- **Purpose:** prove a real read end to end, through the node gate, with honest values.
  Onboarding's `setup-first-contact` does this once at first run; this step is the
  re-runnable check after any fitting change.
- **Opens from → goes to:** `hw-install-heard` → `hw-install-done`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content (top to bottom):** 1. Stepper "5 of 6". 2. Line "Ignition on, engine off".
  3. **Read now** (primary). 4. Per module, a Card with a status chip and StatTiles:
  **Engine (Td5)**: RPM (`21 09`), Battery (`21 10`), Coolant (`21 1A`), each with unit and
  a "proven" mark. **SLABS** (after the Td5 session is released): Left and right ride height
  (`21 54`). Generic OBD: supported PIDs, then RPM and coolant. Brain link: "Live from the
  node". 5. Line "Init log" (fast-init, key bytes) as a collapsed row for service mode.
- **States:** reading (per module progress words); Td5 values with "Not in this session"
  while SLABS holds the bus; ECU refused ("Turn the ignition off and on, then retry");
  SLABS slow ("SLABS can take up to three tries"); different car ("Key bytes differ from
  this vehicle"); missing values "—", never 0.
- **Safety and driving rules:** Tier 0 reads only, through the node gate; a single
  pack-declared init is not a probe; an unknown car's detection is Parked only
  ([K-line profiles §2][kl2]). Nothing is cleared or actuated here.
- **Components:** StatTile, Card, Chip (status), Button, Stepper.
- **Spec refs:** [K-line profiles §1][kl1], [K-line profiles §8.1][kl81], [UI §3.5][ui35].

### hw-install-done — Installed and verified  [Proposed]
- **Owner:** os
- **Purpose:** close the guide with a record and the next useful setups.
- **Opens from → goes to:** `hw-install-test-read`. Goes to `hw-gps`, `hw-imu-calibrate`,
  `hw-alarm-setup`, Home.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night.
- **Content:** 1. Title "Installed and verified". 2. Summary rows: device, bus, protocol
  ("KWP2000 fast · remembered for this vehicle"), power ("12 V OK"), time. 3. Next-step
  ListRows: "Check GPS fix", "Level the IMU", "Set up the alarm". 4. **Done**.
- **States:** partial ("Td5 OK · SLABS not answering", with **Retry SLABS**).
- **Safety and driving rules:** the result is stored with the vehicle id, never the VIN
  ([ADR-0036][a36]).
- **Components:** ListRow, Card, Button.
- **Spec refs:** [K-line profiles §2][kl2] (remembered profile).

[a20]: ../../../../decisions/adr-0020-can-links-listen-only-by-default.md
[a23]: ../../../../decisions/adr-0023-passive-can-bitrate-detection.md
[a32b]: ../../../../decisions/adr-0032-one-node-optional-brain.md#b-sensor-detection-one-firmware-manifest-from-hardware
[a36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[a39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[a40-3]: ../../../../decisions/adr-0040-power-states-and-wake.md#3-wake-sources
[a40-4]: ../../../../decisions/adr-0040-power-states-and-wake.md#4-wake-requests
[hp-k]: ../../../../specs/2026-10-02-hardware-platform-design.md#k-line-front-end-reused-proven
[hp-p]: ../../../../specs/2026-10-02-hardware-platform-design.md#two-power-domains-the-battery-rule
[kl1]: ../../../../specs/2026-10-06-kline-profiles-detection-design.md#1-the-profile-schema-srcopenostlerklineprofilespy
[kl2]: ../../../../specs/2026-10-06-kline-profiles-detection-design.md#2-klinedetect-srcopenostlerklinedetectpy
[kl81]: ../../../../specs/2026-10-06-kline-profiles-detection-design.md#81-the-node-path-adr-0032
[ns10]: ../../../../specs/2026-10-06-node-source-design.md#10-offline-asleep-and-stale-states
[nsr7]: ../../../research/node_sensors.md#7-placement
[ui35]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
