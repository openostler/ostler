---
title: "Designer brief 80-m — Projection (Android Auto, CarPlay), climate and pack vehicle settings"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-platform-direction-design.md, references/research/canbus_headunit.md, references/research/driver_distraction_rules.md]
summary: >
  The last head-unit features. Projection (app:projection) covers Android Auto and CarPlay:
  setup, the projected session inside the OS frame, and settings. It says plainly that both
  need certification and licences Ostler does not hold, so every projection screen is
  Proposed with open legal questions. The climate page is the approved climate device page;
  on the Discovery 2 it shows a "not available on this car" state, because the climate panel
  is not on the diagnostic line. Vehicle settings from packs is one OS page where a vehicle
  pack offers car settings; for the D2 it shows the SLABS rear ride heights read only and
  sends service procedures to Diagnostics.
---

# 80-m — Projection, climate and pack vehicle settings

Shared rules are in [80-a](80-hu-a-overview.md).

## Projection: the honest position

Android Auto and CarPlay are the phone makers' own systems. A head unit that shows them must
be **certified**: Android Auto receivers go through Google's partner programme and CarPlay
receivers need Apple's licence, an authentication chip and certification
([head-unit research B5][ch-b5]). Ostler has neither. Open receivers exist (a Pi Android Auto
receiver built on openauto and aasdk) but are not certified and break when the protocol
changes ([head-unit research B7][ch-b7]). Plug-in adapters carry their own licensed chip and
turn the session into a stream another app can draw. The platform direction says CarPlay and
Android Auto come "via a wireless dongle" on a head unit, and that the head unit keeps them
([platform direction][pd]). So every projection screen is **Proposed** and must not ship
until the owner answers the legal questions below.

### projection-setup — Projection: setup  [Proposed]
- **Why the app needs it:** the owner asks for parity with aftermarket units, which all
  offer Android Auto and CarPlay.
- **Purpose:** choose how projection reaches the screen and connect a phone.
- **Owner:** app:projection
- **Opens from → goes to:** first open of Projection; `projection-settings`. Goes to
  `projection-session`.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night step 1; hu7 Night
  connected.
- **Content (steps):**
  1. A plain Card first: "Android Auto and CarPlay need certified hardware. Ostler is not
     certified. Projection works only through an adapter you buy, or through your existing
     head unit." **I understand** to continue.
  2. **How:** choice list: **Keep my head unit for projection** (recommended; Ostler steps
     aside, no projection screen in Ostler) · **USB projection adapter on the Brain** ("The
     adapter does the licensed part; Ostler shows its picture").
  3. **Adapter check:** "Adapter found · supports CarPlay and Android Auto" or "Not found".
  4. **Connect a phone:** plug in or pair the phone as the adapter asks; status "Connected ·
     Pixel 8 · Android Auto".
  5. **Done**.
- **States:** no adapter; adapter firmware unknown ("This adapter isn't tested"); phone
  refused. Moving: locked view.
- **Safety and driving rules:** Parked only.
- **Components:** StepProgress (new component), Card, ListRow, Chip (status), Button.
- **Spec refs:** [head-unit research B5][ch-b5] · [head-unit research B7][ch-b7] ·
  [platform direction][pd].
- **Open questions:** see "Legal questions" below.

### projection-session — Projection: running session  [Proposed]
- **Why the app needs it:** the projected screen must sit inside Ostler's frame so the
  safety items stay visible.
- **Purpose:** show the projected Android Auto or CarPlay screen.
- **Owner:** app:projection (session); os (frame, strip, alerts)
- **Opens from → goes to:** `audio-sources` → Projection; the projection app shortcut;
  phone connected (if "open on connect" is on). The dock's Home or Back leaves to the
  Ostler home page; the session keeps running for audio.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night Parked; huwide
  Night with the projection in two thirds and the Drive tiles in one third.
- **Content (top to bottom):** 1. OS strip on top (telltale, Security, Link, clock). 2. The
  projected picture, scaled to the main area at the adapter's resolution (800×480 or
  1280×720), letterboxed on `bg`. 3. A small OS **Ostler** button in the dock to return.
  4. HU-wide: one third keeps an Ostler Drive home page (≤ 6 tiles while Moving).
- **States:** connecting: "Connecting to Pixel 8…"; adapter lost: "Projection stopped" and
  audio falls back to the last source; reverse: the camera pre-empts (when the fast path
  exists); a red telltale: the OS `alert_card` draws over the projection.
- **Safety and driving rules:** the projected picture is a video stream Ostler cannot
  inspect; under Ostler's rules that is video on a driver-facing display. **Until the legal
  and safety review clears it, projection is Parked only** and pauses to its audio while
  Moving ([UI §12.1][ui-12.1], [research reg 109][dd-4.2]). The OS strip, telltale and
  alerts can never be covered.
- **Components:** Chip (status), Button, locked view.
- **Spec refs:** [UI §12.1][ui-12.1] · [head-unit research B5][ch-b5].
- **Open questions:** may a certified phone UI, shown through a licensed adapter, count as a
  driver-safe template while Moving?

### projection-settings — Projection settings  [Proposed]
- **Why the app needs it:** adapter, auto-start and audio choices need one home.
- **Purpose:** the Projection app's options.
- **Owner:** app:projection
- **Opens from → goes to:** App info → Settings; `projection-session` (Parked) → Settings.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night.
- **Content (top to bottom):** 1. Adapter row and firmware. 2. **Open when a phone connects**
  Toggle (off). 3. **Calls through** Segmented: Projection · Ostler Phone app (one hands-free
  owner, as the Phone app requires). 4. **Resolution** Segmented. 5. Known phones with
  **Forget**.
- **States:** Moving: locked view.
- **Safety and driving rules:** Park to edit.
- **Components:** ListRow, Toggle (new component), Segmented, Button.
- **Spec refs:** [Phone §3][pc-3].
- **Open questions:** none beyond the legal list.

**Projection widgets:** **Projection shortcut** (size small; options: icon and name; opens
the session, Parked only until cleared).

**Legal questions for the owner (projection):** (1) Is shipping an open, uncertified Android
Auto receiver allowed under Google's terms, and is it wise given protocol breaks? (2) May a
third-party display show a licensed adapter's CarPlay or Android Auto picture? (3) Can the
UI use the names "Android Auto" and "CarPlay", or must it say "phone projection"? (4) Does
showing it while Moving fit UK reg 109 on a screen Ostler does not control? (5) Product
liability under the EU directive once hardware is sold ([UI §12.1][ui-12.1] legal check).

### climate-panel — Climate (device page; "not available" on the D2)  [New]
- **Purpose:** show and set the cabin climate where a climate device or pack supports it.
- **Owner:** os (device page and `setpoint` template); filled by a climate device or pack
- **Opens from → goes to:** the climate strip chip (only when a device exists); app drawer
  → Settings → Network → Climate; the climate widget. Back.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  "not available on this car" (the D2 frame); hu7 Night-dim Moving `setpoint` with a device.
- **Content (top to bottom), with a climate device:** 1. Setpoint "21.5 °C" with − and +.
  2. Fan 0–7, A/C Toggle, Recirculate Toggle, vents Segmented (face, feet, screen). 3. Cabin
  temperature reading.
- **Content on the Discovery 2 (no climate source):** one Card: icon `ac_unit`, "Climate
  isn't available on this car", line "The Discovery 2's climate panel is not on the
  diagnostic line. A separate climate device could add it later." No controls, no greyed
  sliders.
- **States:** device offline: "Climate device offline". Moving: one `setpoint` (temperature
  ± and one toggle), allowed while Moving as an add-on device action on our own device.
- **Safety and driving rules:** setpoints never write to a car ECU; they pass the gate as
  `add-on device` actions, local only ([UI §6][ui-6]); with no device nothing renders except
  this page's honest state.
- **Components:** Card, `setpoint` template, Button, Toggle (new component), Segmented.
- **Spec refs:** [UI §6][ui-6] · [App model §4.4][am-4.4].
- **Open questions:** should the D2 frame appear at all, or should the page simply not exist
  when no climate source is fitted (UI §6 says nothing renders)? Recommend: no strip chip or
  widget, but the app drawer search for "climate" lands here.

### vehicle-settings-pack — Vehicle settings from packs  [Proposed]
- **Why the app needs it:** aftermarket units have a "car settings" page; in Ostler those
  settings come from the vehicle pack (an integration).
- **Purpose:** show the settings and car functions a vehicle pack offers, in one place.
- **Owner:** os (page frame from the integration loader); content from the `lr_d2` pack
- **Opens from → goes to:** system Settings → Vehicle; the vehicle's App info. Goes to the
  Diagnostics app's SLABS pages by name (the SLABS vehicle view `live-vehicle-slabs`,
  Procedures `diagnose-procedures`) in the 50-vehicle brief.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; phone Day.
- **Content (top to bottom), for Land Rover Discovery 2 Td5:**
  1. **Suspension (SLABS)** Card: "Rear self-levelling" with live **Height left** and
     **Height right** (raw counts, proven), and the line "The Discovery 2 levels the rear
     on its own. There are no driver lift or lower controls."
  2. "Stored height" row: "Not read yet" (a different source, not decoded).
  3. "SLABS settings": "Not decoded yet · help decode" → Decode lab by name.
  4. **Service procedures** → Diagnostics Procedures: "Raise or lower a corner" (Tier 3,
     Parked only); "Store target heights" is listed there for honesty and never sent.
  5. Other packs add their own cards here; nothing renders for a function a pack lacks.
- **States:** no SLABS session: heights stale grey with "Open SLABS" (the Td5 session moves
  first). No pack: "No vehicle pack · set one up". Moving: read only heights as a `value`;
  every control is locked.
- **Safety and driving rules:** this page never writes to the car; procedures keep their
  tiers, confirms and the Parked rule in the Diagnostics app ([UI §7][ui-7]).
- **Components:** Card, StatTile, ListRow, Button.
- **Spec refs:** [UI §7][ui-7] · [UI §6][ui-6].
- **Open questions:** should this page live in system Settings or in the Diagnostics app?

[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[pc-3]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#3-architecture
[pd]: ../../../../specs/2026-10-06-platform-direction-design.md#displays-are-thin-clients-cameras-live-on-our-infrastructure
[dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[ch-b5]: ../../../research/canbus_headunit.md#b5-android-auto-and-carplay-what-a-third-party-app-may-do
[ch-b7]: ../../../research/canbus_headunit.md#b7-open-head-unit-projects
