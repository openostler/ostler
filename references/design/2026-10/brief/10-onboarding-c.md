---
title: "Designer brief 10-c — onboarding: add a vehicle, choose the source, pair a node, use an adapter, first contact with the car"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-06-module-bus-messages-design.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md]
summary: >
  Third onboarding brief file: the car half of setup. Add vehicle (choose an installed pack
  such as the Land Rover Discovery 2 Td5 or Generic OBD-II, or detect it from the car; no
  VIN entry, because the VIN stays in the car), name the vehicle and its driver side, choose
  how Ostler reaches the car (an Ostler Diagnostics node, an adapter the user already owns,
  or not yet), pair or adopt a node with a physical press and set its uplink, the
  onboarding additions to the Existing adapter connect and verdict screens, and the first
  contact check that walks the connection ladder, identifies the car and runs the first
  read-only scan, Parked only.
---

# 10-c — Vehicle, source, node, adapter and first contact

### setup-vehicle-add — Add vehicle  [New]
- **Owner:** os
- **Purpose:** tell Ostler which vehicle pack to use, or let it detect the car.
- **Opens from → goes to:** F1 step 5; F5 step 4; Settings → Vehicles → **Add vehicle**. →
  `setup-vehicle-name`. "Detect from the car" defers the choice to `setup-first-contact`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day; hu5 Night.
- **Content (top to bottom):**
  1. Title "Which car is this?"; line "Ostler reads your car with a vehicle pack."
  2. ListRow `search` **Detect from the car** "Needs the node or an adapter, and the car
     parked" (identification order: read identity, decode in memory, match pack detection,
     ask only what changes the topology, fall back; [UI §4.4][ui-4.4]).
  3. **Installed packs** (only installed packs; nothing deferred is shown):
     - `directions_car` **Land Rover Discovery 2 · Td5** meta "K-line · 6 systems: TD5
       (engine), SLABS (ABS + air suspension), BCU, ACE, EAT, SRS"; Chip "Best with a node".
     - `directions_car` **Generic OBD-II** meta "Any car with an OBD-II port · one system ·
       engine and emissions"; Chip "Fallback".
  4. ListRow `help` **My car isn't listed** → Sheet: "Use Generic OBD-II" (if the car has an
     OBD-II port) or "Help decode it" (opens the Decode lab app in service mode, if installed;
     [UI §8.2][ui-8.2]).
  5. Card (info): `lock` "Ostler never asks for your VIN. If the car reports it, Ostler
     reads it in memory to recognise the car and keeps only a masked form like SAL…****."
- **States:** loading: rows skeleton. No packs installed: Card `warn` "No vehicle pack
  installed" + the install hint naming the D2 pack and Generic OBD-II. Second vehicle: a
  line "Adding a car does not disconnect the current one until you switch" ([UI §4.1][ui-4.1]).
  Offline: works. Moving / unknown: locked view.
- **Safety and driving rules:** Parked only on driver-facing displays; detection is
  probing and runs only Parked ([K-line §2][kl-2]).
- **Components:** SetupStepper (new), ListRow, Chip (status), Card, Sheet.
- **Spec refs:** [Packs §2.1][vp-2.1] · [Packs §2.7][vp-2.7] · [UI §4.4][ui-4.4] ·
  [UI §8.2][ui-8.2] · [ADR-0036][adr-36].
- **Open questions:** vehicle packs are integrations hosted by the Store app (`70-store-*`); should
  this step offer **Get more packs** there, or list only installed packs?

### setup-vehicle-name — Name this car  [New]
- **Owner:** os
- **Purpose:** the garage entry: nickname, driver side, optional photo and plate.
- **Opens from → goes to:** `setup-vehicle-add` → here → `setup-source`. Settings → Vehicles edits
  the same fields later.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with the keyboard; phone Day.
- **Content (top to bottom):**
  1. **Nickname** field, prefilled "Discovery 2 Td5", caption "Shown on the strip when you
     have more than one car."
  2. **Driver side** Segmented "Right-hand drive · Left-hand drive" (the pack's default; the
     dock moves to that side on wide head units, [UI §3.3][ui-3.3]); a small preview of the dock position.
  3. **Photo** (optional) Button **Add photo**, caption "Location data is removed from the
     photo."
  4. **Number plate** (optional), caption "Private. Shared only if you choose to later."
  5. Button **Continue**.
- **States:** empty nickname → the pack name is used. Moving: locked view.
- **Safety and driving rules:** text entry Parked only. No VIN field, ever ([ADR-0036][adr-36]).
- **Components:** SetupStepper (new), text field, Segmented, Button.
- **Spec refs:** [UI §4.1][ui-4.1] · [Accounts §14.1 (`vehicle_card`)][acc-14.1] ·
  [Accounts §14.7 S1][acc-14.7].
- **Open questions:** none.

### setup-source — How Ostler reaches the car  [New]
- **Owner:** os
- **Purpose:** pick the source: an Ostler Diagnostics node (the product path), an adapter
  the user already has, or later.
- **Opens from → goes to:** `setup-vehicle-name`; the Link chip sheet "No adapter" row. →
  `setup-node-pair`, `adapter-connect`, or **Not now** → the next step.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. Title "How will Ostler reach the car?"
  2. Card `memory` **Ostler Diagnostics node** "Plugs into the diagnostic port. Reads every
     system, runs the alarm and wakes the Brain." Chip "1 found nearby" when an unpaired node
     advertises. Link "Fitting the node" goes to the hardware pages (`20-hardware-*`).
  3. Card `cable` **An adapter I already have** "ELM327, OBDLink, a USB K-line cable or a
     CAN interface. Reads and clears codes. No alarm or wake." For the D2: second line "Td5
     and SLABS need K-line timing. Adapter support on this car is not tested yet."
  4. ListRow **Not now** "You can browse, but nothing will show live values."
- **States:** a node already serves this car → the adapter Card is disabled with "This car
  has a node. An adapter would only listen here." ([ADR-0044][adr-44] item 4). Phone browser
  without the app → adapter Card reads "Needs the Ostler app or a computer". Laptop host →
  node Card reads "Needs a Brain or the phone app". Moving: locked view.
- **Safety and driving rules:** the node's gate is the only path to the car; the Brain
  hosts an adapter only for a vehicle with no node ([ADR-0044][adr-44]).
- **Components:** SetupStepper (new), Card, Chip (status), ListRow.
- **Spec refs:** [Adapters §3][sa-3] · [Adapters §9][sa-9] · [ADR-0044][adr-44] ·
  [UI §4.5][ui-4.5].
- **Open questions:** none.

### setup-node-pair — Pair an Ostler Diagnostics node  [New]
- **Owner:** os
- **Purpose:** bring a node (or Guardian) into this Ostler with a physical press: the Brain
  adopts it, or, with no Brain, the phone pairs with it and becomes its owner.
- **Opens from → goes to:** `setup-source`; F5 step 2; Settings → Network → **Pair a device**.
  → `setup-node-uplink` (no Brain, or the user asks) or `setup-first-contact`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (Brain adopts); phone Night (no Brain); phone Day.
- **Content (top to bottom), Brain variant:**
  1. Title "Pair a node"; line "The node must be in setup mode: new, reset, or after a long
     press. In setup mode it sends nothing to the car."
  2. **Nearby, not paired** list: ListRow `memory` "Ostler Diagnostics" or `shield`
     "Ostler Guardian", its name, "Reached via USB" (or Ethernet, Wi-Fi), Button **Pair**.
  3. After **Pair**: a large prompt "Press the button on the node now", a countdown ring and
     **Cancel** (focused).
  4. Done: `check_circle` "Paired" and what it brings, read from its capability manifest:
     Chips "K-line · kline-diag", "GPS", "Alarm", "12 V watch" (absent sensors never appear).
     Line "This Brain can now sign approvals for it."
- **Content, phone variant (Ostler Diagnostics alone):** steps 1–3 over Bluetooth, or the
  node's own Wi-Fi with the per-device password on its label (Button **Scan the label**).
  After the press the phone holds the owner's pairing keys: S1's name field and recovery
  line appear here ("Lost the phone? Hold the node's button with the ignition on to pair a
  new owner. Old phones are removed; your data stays.").
- **States:** none found → "No node in setup mode" + "Hold its button for setup mode".
  Timed out → **Try again**. Already owned by someone else → "This node has an owner.
  Ask them to add you." Moving: locked view (pairing is Parked; the press is at the car).
- **Safety and driving rules:** no silent takeover: adoption needs the owner here and a
  press on the device ([ADR-0039 §7][adr-39]); keys enter the node only by pairing
  ([Module bus §10][mb-10]); pairing is an owner operation on a local link ([UI §3.7][ui-3.7]).
- **Components:** SetupStepper (new), ListRow, Button, countdown ring (as `shell-brain-wake`),
  Chip (status), Card.
- **Spec refs:** [ADR-0039 §7][adr-39] · [Module bus §14][mb-14] · [Accounts §14.10][acc-14.10]
  · [UI §3.7][ui-3.7].
- **Open questions:** the press timeout is a firmware bench value; draw 60 s.

### setup-node-uplink — The node's internet  [New]
- **Owner:** os
- **Purpose:** give a node a way out when it has no Brain, or a fallback when the Brain
  sleeps.
- **Opens from → goes to:** `setup-node-pair` (phone variant) → `setup-vehicle-add`; Settings →
  Network → the node's page → **Uplink**.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night.
- **Content (top to bottom):** 1. Title "How should the node reach the internet?"
  2. ListRows: `wifi` **Wi-Fi** (the networks it sees: car, phone hotspot, home), `sim_card`
  **4G** (only when the module is fitted; SIM status), `usb` **USB 4G stick** (only when one
  is attached), **No internet** "Works in the car with your phone; no remote alerts".
  3. With a Brain: line "The Brain manages the uplink. The node's is a fallback while the
  Brain sleeps." 4. Button **Continue**.
- **States:** wrong Wi-Fi password → inline error; no SIM → "No SIM found". Moving: locked.
- **Safety and driving rules:** Wi-Fi password entry is Parked only on head units.
- **Components:** ListRow, Segmented, text field, Chip (status), Button.
- **Spec refs:** [ADR-0039 §5–§7][adr-39] · [UI §3.7 (uplinks)][ui-3.7].
- **Open questions:** none.

### adapter-connect — Use an adapter  [Existing]
- **Owner:** os
- **Onboarding additions only.** Reached from `setup-source`; returns to
  `adapter-verdict` then `setup-first-contact`. Above the transport list a line names the
  vehicle being set up ("For Discovery 2 Td5"). For a K-line vehicle the list puts **USB
  K-line cable** first, marked "Developer path" ([ADR-0044][adr-44] item 6). Detection steps
  3–6 show "Waiting for Parked" until the car is parked, ignition on, engine off.
- **Spec refs:** [Adapters §9][sa-9] · [Adapters §5][sa-5] · [Adapters §6][sa-6].

### adapter-verdict — Adapter verdict  [Existing]
- **Owner:** os
- **Onboarding additions only.** Under the chips ("Clone: read-only", "ELM: limited",
  "Listen-only: requested", "Soft gate"), one line on what a node adds ("A node adds the
  alarm, wake and an independent gate") with a link to the hardware pages; no nagging. Button
  **Continue** → `setup-first-contact`. "Adapter actions" stay off; they are switched on later
  on the vehicle's page (`adapter-soft-gate`).
- **Spec refs:** [Adapters §5][sa-5] · [Adapters §7][sa-7] · [Adapters §9][sa-9].

### setup-first-contact — First contact with the car  [New]
- **Owner:** os (the first scan in §5 is drawn by app:diagnostics)
- **Purpose:** prove the whole chain once, Parked: source → bus → ECU session → data
  flowing, identify the car, and save a first read-only scan.
- **Opens from → goes to:** after pairing or the adapter verdict; the Link chip sheet
  "Check the connection". → `setup-display` (head unit) or the next step; the report opens in the
  Trips app when it is installed.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night running; hu7 Night done; phone Day; hu7 Night-dim Moving (refused).
- **Content (top to bottom):**
  1. **Before we start** checklist (ticks the user confirms; evidence from the bus replaces a
     tick when it exists): "Parked, handbrake on", "Ignition on", "Engine off", "No other
     tester plugged in". Button **Start check**.
  2. **Ladder** progress rows (as `adapter-connect`), each with state and time: "Node" or
     "Adapter" → "Bus: listening for other testers (3 s)" → "Bus: K-line init" → "ECU session:
     TD5 (engine)" → "Data flowing". SLABS adds "Waiting for the bus to go quiet".
  3. **Live proof**: three StatTiles from the first values read, for the D2 "RPM", "Coolant",
     "Battery", each with unit and confidence; missing shows "—".
  4. **This car**: "Land Rover Discovery 2 · Td5" with how it matched ("pack detection on
     K-line"); the masked VIN only if the car reported one.
  5. **First scan** (Read, Tier 0): one row per system with the honest states `Not scanned` ·
     `Scanning` · `OK` · `Faults n` · `No response` · `Not fitted` · `Not supported yet`; K-line
     runs one system at a time with **Stop**. Line "Report saved." The scan runs only when the Diagnostics app is installed;
     without it this section reads "Install the Diagnostics app to scan systems."
  6. Buttons **Continue** (primary), **Open the report** (secondary).
- **States and recovery:** bus busy → "Another tester is on the K-line. Unplug it and try
  again." ECU refused → "Turn the ignition off and on, then try again." No ECU → "No answer
  from the engine. Is the ignition on?" Init failed → **Try again** (a remembered profile is
  kept per vehicle). Detection mismatch → "This looks like Generic OBD-II, not a Discovery 2.
  Use it?" Offline (Brain asleep): `shell-brain-wake`. Moving or speed unknown: refused with
  "Park to run the first check", nothing sent. Idling: refused (engine must be off).
- **Safety and driving rules:** probing and module sweeps run only Parked ([K-line §2][kl-2]);
  adapters never search for the bus unless Parked (R6) and listen 3 s first
  ([Adapters §7][sa-7], [§7.2][sa-7.2]); the scan is Tier 0, read only.
- **Components:** SetupStepper (new), progress rows, StatTile, Card, ListRow, Button.
- **Spec refs:** [UI §4.3][ui-4.3] · [UI §4.4][ui-4.4] · [UI §4.5][ui-4.5] ·
  [ADR-0039 §7 (first scan)][adr-39] · [K-line §2][kl-2] · [Adapters §7.2][sa-7.2].
- **Open questions:** should the first scan be skippable (it takes a minute or more on six
  K-line systems)? The brief offers **Skip scan** after "Data flowing".

[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[acc-14.10]: ../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery
[vp-2.1]: ../../../../specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md#21-repo-placement
[vp-2.7]: ../../../../specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md#27-identity-and-vin
[sa-3]: ../../../../specs/2026-10-07-source-adapters-design.md#3-where-adapters-sit-with-the-node-first-rules
[sa-5]: ../../../../specs/2026-10-07-source-adapters-design.md#5-detection-and-clone-checks
[sa-6]: ../../../../specs/2026-10-07-source-adapters-design.md#6-hosts-and-transports
[sa-7]: ../../../../specs/2026-10-07-source-adapters-design.md#7-safety-with-no-hardware-gate
[sa-7.2]: ../../../../specs/2026-10-07-source-adapters-design.md#72-one-tester-per-bus
[sa-9]: ../../../../specs/2026-10-07-source-adapters-design.md#9-ui-summary-detail-in-u-phase-specs
[kl-2]: ../../../../specs/2026-10-06-kline-profiles-detection-design.md#2-klinedetect-srcopenostlerklinedetectpy
[mb-10]: ../../../../specs/2026-10-06-module-bus-messages-design.md#10-transmit-grants-owner-approved-firmware-node-can-6-owner-answers-12-of-2026-10-06
[mb-14]: ../../../../specs/2026-10-06-module-bus-messages-design.md#14-discovery-and-mdns-txt-keys-adr-0027-6-adr-0037-33-adr-0039-7
[ui-3.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#33-driver-side-rail-versus-bottom-bar
[ui-3.7]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-4.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-8.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#82-generic_obd2-and-unknown-vehicle--help-decode-it
[adr-36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md#decision
[adr-39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[adr-44]: ../../../../decisions/adr-0044-adapters-on-the-brain-without-a-node.md#decision
