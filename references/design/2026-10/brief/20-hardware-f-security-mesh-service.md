---
title: "Designer brief: hardware (f) — alarm sensors and arming, tracker, remote start, mesh radios and service mode"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-02-gps-tracker-alarm-design.md, specs/2026-10-02-remote-start-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-kline-profiles-detection-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0040-power-states-and-wake.md, references/research/platform.md, references/research/hardware.md]
summary: >
  Covers alarm setup under Security (sensors from the node and Guardian manifests with
  status and strength, arming that follows the car's own alarm or the app, the alert path
  that works with the Brain off and no internet, remote disarm rules, no outputs), a
  proposed time-boxed walk test, and tracker settings (parked receiver, check-ins, node-loss
  alert, location kept on the device). Says how the specs treat remote start and fob
  disarm: drafts that need their own ADR, so no screen and no placeholder this round. Then
  mesh radios (Meshtastic first, MeshCore second, a convoy Wi-Fi mesh later): read and alerts
  only, coarse positions off by default. Ends with service mode's frame and badge.
---

# Hardware brief (f): security sensors, mesh and service mode

Shared rules are in [file (a)](20-hardware-a-devices.md#rules-every-hardware-page-follows).
The Security app (app:security; `security`, Existing) shows alarm state, events and the tracker
map; these screens are its setup pages.

### hw-alarm-setup — Security → Alarm setup  [New]
- **Owner:** app:security
- **Purpose:** see which sensors guard the car, how it arms and how alerts reach you.
- **Opens from → goes to:** Security → Alarm setup; `hw-install-done`. Goes to
  `hw-alarm-walk-test`, `hw-tracker`, device pages.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):**
  1. State line: "Disarmed", "Armed", "Alerting" or "Tamper", icon plus word.
  2. **Sensors** list, one ListRow each, only for hardware present: Ignition, Car's alarm
     siren, Doors, Bonnet, Tilt (IMU), Shock (IMU), GPS movement, Tamper (Guardian: power
     loss, battery disconnect, node removed). Each shows status (OK, No signal, Fault),
     strength ("Strong" or "Weak · notice only"), last event, and a switch. Thresholds read
     "starting value · tuned on the car" (for example tilt "> 3° for 10 s").
  3. **Arming** card: "Follows the car's alarm (lock with the fob)" when that tap is fitted;
     "Arm from Ostler"; entry delay; "Arming works while driving; disarming only when
     parked".
  4. **Alerts reach you** card: "Paired phone (local)", "SMS from Ostler Guardian", "Your
     notify address"; line "Works with the Brain off and no internet".
  5. **Remote** card: "Disarm remotely: allowed for people with Security, with a fresh
     passkey each time; every remote disarm is logged and you are told" (item 60); "Never
     over a mesh".
  6. **Outputs** text: "Ostler Diagnostics and Guardian have no siren or immobiliser outputs.
     Those need a future I/O module and their own decision."
  7. **Walk test** (secondary).
- **States:** no Guardian (no tamper or backup cell rows); sensor no signal (warn); armed
  (settings read only until disarmed); offline (age banner); Moving locked view except the
  `arm` template from the Drive menu.
- **Safety and driving rules:** Security category: arming allowed while Moving, disarming
  Parked only ([ADR-0033 §1][a33-1]); remote paths read plus arm and disarm, audited
  ([ADR-0033 §6][a33-6]); a mesh never arms or disarms ([ADR-0038][a38]). The alarm never
  waits for the Brain ([ADR-0033 §7][a33-7]). Alarm alerts are not removable.
- **Components:** ListRow, Card, Chip (status), Segmented, Button.
- **Spec refs:** [UI §6][ui6] (Alarm row), [ADR-0032][a32], [ADR-0033 §7][a33-7],
  [Tracker and alarm spec: signal taps][ga-taps] (draft), [platform research §4][pr4].
- **Open questions:** **Decided (item 65):** the BCU wires for door, bonnet and siren are
  first car checks; until the owner confirms them on the car, those rows are absent on the
  D2.

### hw-alarm-walk-test — Alarm walk test  [Proposed]
- **Owner:** app:security
- **Why the app needs it:** an owner must prove each tap and threshold after fitting, without
  sending real alerts to everyone on the list.
- **Purpose:** a 5-minute test where triggers are ticked on screen and logged.
- **Opens from → goes to:** `hw-alarm-setup` → Walk test. Back to setup.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night (the owner walks round the car with it).
- **Content:** 1. "Test mode · ‹mm:ss› left", **Stop**. 2. ListRows with an instruction and
  a tick: "Open the driver's door", "Open the bonnet", "Rock the car", "Turn the ignition on".
  3. Result: "4 of 4 heard".
- **States:** a sensor not heard ("Not heard · check the tap"); time out ends the test;
  armed alerts resume at once.
- **Safety and driving rules:** owner only, local only, Parked; the Security chip reads
  "Testing" for the whole test; Tamper still alerts during a test.
- **Components:** ListRow, Chip (status), Button, Card.
- **Spec refs:** [ADR-0033 §7][a33-7], [platform research §4][pr4].

### hw-tracker — Tracker settings  [New]
- **Owner:** app:security
- **Purpose:** set how the parked car reports where it is, and who may see it.
- **Opens from → goes to:** `hw-alarm-setup` → Tracker; Security's tracker map. Goes to
  `hw-gps`, Accounts S8 sharing.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone Day.
- **Content:** 1. "Parked receiver: Guardian GNSS · 1 Hz" (or the node's when no Guardian).
  2. Check-in interval and its cost. 3. "Alert if the node is removed while armed" switch.
  4. **Location sharing**: "Only on this car unless you share it", link to sharing.
  5. Guardian uplink: "Own SIM · data used this month".
- **States:** no fix (last fix with age); no Guardian (node rows only; "parked-deep stops
  reporting"); remote viewer without sharing sees no position.
- **Safety and driving rules:** location stays on the device unless shared
  ([ADR-0009][a09]); Parked to edit.
- **Components:** ListRow, Card, Segmented, Button.
- **Spec refs:** [UI §6][ui6] (Tracker row), [ADR-0032 A][a32a], [ADR-0040 §2][a40-2].

## Remote start and fob disarm: not designed this round

The [remote start spec][rs] is a draft and calls itself the highest-risk feature: a
transponder-present immobiliser bypass, relays on the ignition harness, mandatory
interlocks (transmission safe, handbrake, bonnet), and fail-secure shutdown. It **needs its
own ADR and a safety review before any wiring** ([remote start: gating][rs-g]); GOALS lists
it as a moonshot. The fob-press remote disarm of the [tracker and alarm spec][ga-d] is also a
draft needing its own ADR. So: **no screen, no menu row and no "coming soon" placeholder.**
What does exist is the software alarm's arm and disarm (above). If remote start is ever
approved it is a car-switching output, so it can never be a remote action by default:
remote paths stay read-only unless `OSTLER_ALLOW_REMOTE_CONTROL` is set on the node, and
never over Home Assistant, MQTT, Matter or a mesh at Tier 2 or above ([ADR-0033 §6][a33-6]).

### hw-mesh-radios — Mesh radios  [New]
- **Owner:** os (the radio devices); using them is app:social
- **Purpose:** list the radios that link this car to other cars, a camp or a base.
- **Opens from → goes to:** Network → Radios; `hw-add-device` → Mesh radio. Goes to
  `hw-mesh-radio`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** tablet
  Night, phone Night.
- **Content:** 1. Banner: "A mesh is a remote path. It carries readings and alerts only.
  Nothing from a mesh can control this car." 2. ListRows: radio name, "works with
  Meshtastic" or MeshCore, connected by (USB, BLE, network), bridge runs on (Brain or phone),
  link state, peers heard, airtime used. 3. **Add a radio** (a local, physical step).
- **States:** none ("No radios"); bridge stopped; Brain asleep (bridge on the phone, or
  "Needs the Brain"); Moving locked view.
- **Safety and driving rules:** no actions in the bridge; no remote arm or disarm over a
  mesh, with or without the install override ([ADR-0038][a38]).
- **Components:** ListRow, Card (banner), Chip (status), Button.
- **Spec refs:** [ADR-0038][a38], [ADR-0038 amendment][a38-a], [UI §3.7][ui37].

### hw-mesh-radio — Mesh radio page  [New]
- **Owner:** os (the radio device); using it is app:social
- **Purpose:** set what one radio sends and show what it hears.
- **Opens from → goes to:** `hw-mesh-radios`. Back.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night.
- **Content:** 1. Channel: "Private · random key" (never the public default for positions).
  2. **Position sharing**: off by default; when on, "Coarse (about ±3 km)" unless a live ride
  raises it; rates as text ("every 10 min parked, 2 min moving, never under 60 s").
  3. **What goes out**: alarm state on change; alerts chosen by class and severity.
  4. **Peers heard**: name, last heard, position age (positions fade and are never stored
  in Trips), "Untrusted data". 5. Airtime and duty cycle used. 6. Lines "Radio's own
  internet uplink: off", "Mesh key is separate from your Ostler keys". 7. **Remove radio**.
- **States:** no peers; duty-cycle limit reached ("Positions paused; alerts still go").
- **Safety and driving rules:** no VIN, vehicle id, plate or account name in any mesh field;
  Parked to edit; remote read-only.
- **Components:** ListRow, Segmented, Card, Chip, Button (danger).
- **Spec refs:** [ADR-0038][a38], [ADR-0038 amendment][a38-a].

### shell-service-mode — Service mode frame and strip badge  [Existing]
- **Owner:** os
- **Purpose:** the admin and Experimental state for fitting and decoding work, unmissable
  while on.
- **Opens from → goes to:** long-press on the version line in Settings → About, then the server
  password. Exits from the badge, or by itself when Moving.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (Diagnose with the frame), phone Day.
- **Content:** a thick frame round the viewport (`line-strong` with the warn hue and the word
  "Service mode" in the strip badge); Experimental items appear; Developer shows Decode mode,
  the K-line profile override, module scan (Parked only), "Forget remembered profile" and
  the init log; Diagnose is the landing screen.
- **States:** entering (password sheet, Cancel focused); on; refused while Moving ("Not while
  moving"); auto-exit on Moving (toast "Service mode ended: vehicle moving").
- **Safety and driving rules:** refused and exits when Moving; the frame and badge are drawn
  by the shell and cannot be hidden ([UI §3.5][ui35], [Drive modes §8.1][dm81]).
- **Components:** Chip (badge), Sheet (password), frame (shell).
- **Spec refs:** [UI §3.5][ui35], [Drive modes §8.1][dm81], [K-line profiles §2][kl2].

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[a32]: ../../../../decisions/adr-0032-one-node-optional-brain.md#decision
[a32a]: ../../../../decisions/adr-0032-one-node-optional-brain.md#a-gps-split-two-receivers-two-jobs
[a33-1]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#1-categories-beside-tiers
[a33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[a33-7]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths
[a38]: ../../../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md#decision
[a38-a]: ../../../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md#amendment-2026-10-07-approved
[a40-2]: ../../../../decisions/adr-0040-power-states-and-wake.md#2-states-per-device-type
[dm81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ga-d]: ../../../../specs/2026-10-02-gps-tracker-alarm-design.md#remote-disarm--emulate-a-paired-fob-no-crypto-re
[ga-taps]: ../../../../specs/2026-10-02-gps-tracker-alarm-design.md#read-side--alarmsecurity-via-signal-taps
[kl2]: ../../../../specs/2026-10-06-kline-profiles-detection-design.md#2-klinedetect-srcopenostlerklinedetectpy
[pr4]: ../../../research/platform.md#4-alarm-and-tracker
[rs]: ../../../../specs/2026-10-02-remote-start-design.md
[rs-g]: ../../../../specs/2026-10-02-remote-start-design.md#gating
[ui6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui35]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui37]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
