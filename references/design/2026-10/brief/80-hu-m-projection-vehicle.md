---
title: "Designer brief 80-m — Projection (Android Auto, CarPlay), climate and pack vehicle settings"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-platform-direction-design.md, references/research/canbus_headunit.md, references/research/driver_distraction_rules.md]
summary: >
  The last head-unit features. Projection (Android Auto, CarPlay) is not built (owner
  decision item 38): owners keep a projection-capable head unit beside Ostler, so the
  projection blocks are one information page plus two "do not draw" records, all Proposed.
  The climate page is the approved climate device page;
  on the Discovery 2 it shows a "not available on this car" state, because the climate panel
  is not on the diagnostic line. Vehicle settings from packs is one OS page where a vehicle
  pack offers car settings; for the D2 it shows the SLABS rear ride heights read only and
  sends service procedures to Diagnostics.
---

# 80-m — Projection, climate and pack vehicle settings

Shared rules are in [80-a](80-hu-a-overview.md).

## Projection: not built (decided, item 38)

Android Auto and CarPlay are the phone makers' own systems. A head unit that shows them must
be **certified**: Android Auto receivers go through Google's partner programme and CarPlay
receivers need Apple's licence, an authentication chip and certification
([head-unit research B5][ch-b5]). Open receivers are not certified and break when the
protocol changes ([head-unit research B7][ch-b7]). The owner decided on 2026-10-07 that
**Ostler does not build projection**: owners who want it keep a projection-capable head unit
beside Ostler (setup B), and the Store lists no uncertified receivers
([head-unit apps §11][hu-11]). So no projection session or settings screen exists; the only
page is an information page, and the blocks below stay **Proposed** for that reason.

### projection-setup — Projection: not built (information page)  [Proposed]
- **Why it exists:** owners will search for Android Auto and CarPlay; the OS answers
  plainly instead of showing nothing. **Why Proposed:** projection is not built (item 38),
  and no approved spec draws this page.
- **Purpose:** say that Ostler does not do projection, and how to keep it.
- **Owner:** os
- **Opens from → goes to:** the app drawer's search ("Android Auto", "CarPlay",
  "projection"); the Store's search. Back.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night.
- **Content:** one Card: icon `phone_android`, title "Android Auto and CarPlay", text
  "Ostler doesn't include phone projection. It needs certified hardware. Keep a head unit
  that has it, and run Ostler beside it." A link **How Ostler sits beside a head unit**
  (the "beside my head unit" install shape, `audio-setup-shape`). No adapter path, no
  setup steps, no controls.
- **States:** none special. Moving: locked view (a Parked page).
- **Safety and driving rules:** nothing here connects a phone or shows a projected picture.
- **Components:** Card, ListRow (link).
- **Spec refs:** [head-unit apps §11][hu-11] · [head-unit research B5][ch-b5] ·
  [head-unit research B7][ch-b7].
- **Open questions:** **Decided (item 38):** projection is not built; no uncertified
  receiver, not even as a sideload-only developer item.

### projection-session — Projection: running session  [Proposed]
- **Not built (item 38): do not draw.** Ostler shows no projected picture; the projection
  head unit keeps the session. The record stays only so the screen ID resolves.
- **Owner:** os
- **Spec refs:** [head-unit apps §11][hu-11].
- **Open questions:** **Decided (item 38):** no projected picture in Ostler, Parked or
  Moving.

### projection-settings — Projection settings  [Proposed]
- **Not built (item 38): do not draw.** There is no projection app to set up.
- **Owner:** os
- **Spec refs:** [head-unit apps §11][hu-11].
- **Open questions:** **Decided (item 38):** none left; the legal questions of the earlier
  draft fall away with the decision.

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
  settings come from the vehicle pack (an integration). **Why still Proposed:** the
  head-unit apps spec puts these in a **Car** app, later, once two packs declare settings
  (decided, item 40; [head-unit apps §8][hu-8]).
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
- **Open questions:** **Decided (item 40, [head-unit apps §8][hu-8]):** a Car app
  (`ostler-app-car`), later, shows the owner-facing subset; Diagnostics keeps the full
  technical settings list.

[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[ch-b5]: ../../../research/canbus_headunit.md#b5-android-auto-and-carplay-what-a-third-party-app-may-do
[ch-b7]: ../../../research/canbus_headunit.md#b7-open-head-unit-projects
[hu-11]: ../../../../specs/2026-10-07-head-unit-apps-design.md#11-projection-android-auto-carplay-open
[hu-8]: ../../../../specs/2026-10-07-head-unit-apps-design.md#8-car-settings-from-packs
