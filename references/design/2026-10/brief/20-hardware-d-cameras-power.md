---
title: "Designer brief: hardware (d) — cameras (add, preview, home pages) and power (sleep, wake, battery guard, schedules)"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, references/research/power_states.md, references/research/hardware.md]
summary: >
  Covers adding a camera (found on the network or entered by address, named, given a role:
  reverse, front, underbody, cabin, dash or other), the camera page with a preview that runs
  only when Parked, and assigning a driving camera to a Drive home page through the camera_live
  template, while cabin, dash and other cameras never show on a driver-facing display while
  Idling or Moving. Then power: the Network Power page (energy ledger against the 10 mA
  budget, battery floors 12.2, 12.0 and 11.8 V as the battery guard, the node's parked-ready
  and parked-deep modes, per-device power, remote-wake quota, wake log) and the scheduled
  wake list and editor from ADR-0040.
---

# Hardware brief (d): cameras and power

Shared rules are in [file (a)](20-hardware-a-devices.md#rules-every-hardware-page-follows).
Cameras need the Brain (its recorder runs there); on Ostler Diagnostics alone camera pages
are absent.

### hw-camera-add — Add a camera  [New]
- **Owner:** os (device setup); viewing is app:camera
- **Purpose:** add a camera and give it a role.
- **Opens from → goes to:** `hw-add-device` → Camera. Goes to `hw-camera`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night, tablet Night.
- **Content (top to bottom):** 1. "Found on the car network" ListRows (name, address,
  "reached via Wi-Fi" or "Ethernet"). 2. **Enter address** (text field; Parked only). 3. Name
  field. 4. **Role** Segmented or list: Reverse, Front, Underbody, Cabin, Dash, Other, each with
  one line ("Reverse: shown when reversing, as an aid only"). 5. **Preview** (still frame
  then live, Parked only). 6. **Add camera** (primary).
- **States:** Brain asleep ("Needs the Brain" card with Wake); none found ("No cameras on
  the car network"); stream fails ("Camera found but no video"); Moving locked view.
- **Safety and driving rules:** Parked only for text entry and preview; local links only.
- **Components:** ListRow, Segmented, Card, Button, camera preview (`camera_live` drawn Parked).
- **Spec refs:** [UI §6][ui6] (Cameras row), [App model §4.4][am44] · [head-unit apps §6][hu-6].

### hw-camera — Camera page: preview, role and home pages  [New]
- **Owner:** os (device setup); viewing is app:camera, drawn in the 80-hu-* files
- **Purpose:** check a camera, set where it may appear, and see its power and storage.
- **Opens from → goes to:** Network → Devices → a camera; `hw-camera-add`. Goes to
  `drive-mode-editor` (Existing) to place it, Security → Clips.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked with preview, hu7 Night-dim Moving (locked), phone Day.
- **Content (top to bottom):**
  1. **Preview** (Parked only): one live stream in a Card, 16:9, with "Live" word; replaced by
     a still and "Preview when parked" otherwise.
  2. **Role** row (Reverse, Front, Underbody, Cabin, Dash, Other) with **Change**.
  3. **Where it can appear** card, built from the role:
     - Reverse: "Drive mode `camera_live` while reversing, as an aid. It does not take over
       the screen yet."
     - Front, Underbody: "Drive mode `camera_live` below 10 km/h."
     - Cabin, Dash, Other: "Parked only on driver-facing screens."
  4. **Use on a home page**: ListRows of Drive home pages with a free cell ("Off-road ·
     Tilt"), each opening the widget setup (45-launcher-* files) with the camera widget from app:camera; device-slot
     chip "Live camera" toggle for the strip.
  5. **Recording** row ("Recording · Accessories") linking to Security → Clips.
  6. **Power and storage**: power word, "Feed switched by Ostler Diagnostics", boot time,
     clips used on the Brain.
- **States:** off ("Camera off · powers on with the Brain"); stream lost (grey still with
  age); Brain asleep (Needs the Brain); Moving locked view; Passenger view never shows a
  non-driving camera.
- **Safety and driving rules:** no video on a driver-facing display while Idling or Moving
  except a driving camera in the `camera_live` template within its speed limit; never in a
  call; Passenger view adds no camera beyond driving cameras ([UI §12.1][ui121]). Placing a
  widget is Park to edit ([Drive modes §8.1][dm81]).
- **Components:** Card, ListRow, Chip (status), Button, `camera_live` template.
- **Spec refs:** [UI §6][ui6], [UI §12.1][ui121], [App model §4.4][am44],
  [Drive modes §8.1][dm81].
- **Open questions:** reverse pre-emption waits for a fast reverse signal; the D2 has none
  on K-line yet, so "Reverse" shows only when placed on a home page.

### hw-power — Network → Power: sleep, wake and battery guard  [New]
- **Owner:** os
- **Purpose:** show what keeps the car's devices awake, what that costs, and the battery
  guard that refuses wakes.
- **Opens from → goes to:** Network → Power card; the Link chip sheet; a refused wake's
  reason. Goes to `hw-power-schedule`, device pages, `hw-device-logs`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  tablet Night, phone Night, hu7 Night.
- **Content (top to bottom):**
  1. **Battery guard** card: 12 V now (resting or charging word), and the three floors as
     rows: "12.2 V · no scheduled or background wakes", "12.0 V · no Brain wakes; an awake
     Brain shuts down", "11.8 V · node goes to deep sleep, alarm inputs only". The floor in
     force carries the warn or alarm word.
  2. **Today's energy** card: used against the daily budget ("‹mAh› of 240 mAh · 10 mA
     average"), a DistributionBars of cost by device; **Change budget** (owner, Parked).
  3. **Node parked mode** row: "Parked-ready (first 72 h)" or "Parked-deep · wakes on wire
     and timer only · phone cannot reach it".
  4. **Devices** table: state, class (always, wakeable, check-in, none), wake path, est.
     current, lease holders, **Wake** where allowed.
  5. **Remote wake** card: switch "Allow remote wake" (owner), quota "‹n› of 6 remote wakes
     left today", rate limits as text.
  6. **Scheduled wakes** row → `hw-power-schedule`.
  7. **Wake log** ListRows: who, what, when, why, cost, outcome ("Refused · Battery 11.9 V").
- **States:** over budget ("Scheduled and background wakes paused until tomorrow; yours will
  ask first"); stuck wake wire (alarm: "Wake wire stuck · masked"); a device that did not
  sleep ("Measured ‹mA›; switched off"); Diagnostics-only (no Brain rows); remote read-only
  except Wake.
- **Safety and driving rules:** a wake never carries a grant and never bypasses a gate; the
  alarm never waits for the Brain ([ADR-0040 §8][a40-8]). Settings are Parked only.
- **Components:** Card, ListRow, Chip (status), DistributionBars, StatTile, Button, Segmented.
- **Spec refs:** [UI §3.8][ui38], [ADR-0040 §2][a40-2], [ADR-0040 §4][a40-4],
  [ADR-0040 §7][a40-7].

### hw-power-schedule — Scheduled wakes  [New]
- **Owner:** os
- **Purpose:** list and edit the wakes that run on a timer, with their battery cost.
- **Opens from → goes to:** `hw-power` → Scheduled wakes. Add or edit opens a Sheet.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night, tablet Day.
- **Content (top to bottom):** 1. ListRows: target device, days and time, hold ("keeps it
  awake up to ‹min› min"), purpose (Sync, Update window, Check-in), estimated cost ("Brain ≈
  30 mAh per 5 min"), switch. 2. **Check-ins** section: Guardian and check-in modules with
  their interval ("checks in ≈ 6 min"). 3. **Add schedule** → Sheet: target (only devices with
  a clock), days, time, hold, purpose, cost line, **Save**, **Cancel**.
- **States:** empty ("No scheduled wakes"); refused last run ("Skipped: battery 12.1 V" or
  "over budget"); Brain-only car ("Wakes from its power board clock").
- **Safety and driving rules:** scheduled wakes are refused below 12.2 V and over budget;
  Parked only to edit; local only.
- **Components:** ListRow, Sheet, Segmented, Button, Card.
- **Spec refs:** [ADR-0040 §3][a40-3], [ADR-0040 §4][a40-4], [ADR-0039][a39].
- **Open questions:** schedule limits per device are not set in ADR-0040 beyond the lease
  maximum ("schedule as set"); the owner should cap the hold.

[a39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[a40-2]: ../../../../decisions/adr-0040-power-states-and-wake.md#2-states-per-device-type
[a40-3]: ../../../../decisions/adr-0040-power-states-and-wake.md#3-wake-sources
[a40-4]: ../../../../decisions/adr-0040-power-states-and-wake.md#4-wake-requests
[a40-7]: ../../../../decisions/adr-0040-power-states-and-wake.md#7-what-people-see
[a40-8]: ../../../../decisions/adr-0040-power-states-and-wake.md#8-safety
[am44]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui38]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[hu-6]: ../../../../specs/2026-10-07-head-unit-apps-design.md#6-camera
