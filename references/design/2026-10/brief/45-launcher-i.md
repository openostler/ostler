---
title: "Designer brief 45-i — launcher: the dashboard builder wizard"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Sixth launcher brief file: the dashboard builder wizard, which runs as a step of first
  setup and at any time later from the launcher menu, for example after adding apps. Its
  five steps are: pick the car and its apps, pick the display, choose templates (presets),
  review the pages, and apply with undo. The file gives the step table with what can fail
  and how to recover, then one block per step, using the Discovery 2 Td5 and its SLABS
  session limits as the example. The result is pages added to the one flat carousel.
---

# 45-i — Dashboard builder wizard

Back to [45-a](45-launcher-a.md). First setup calls this wizard as a step (10-onboarding-a,
step 11); afterwards it opens from **Build dashboards** in the launcher menu or the home
pages list. It uses the **SetupStepper** frame (new component, 10-onboarding-a) and is Park
to edit on a driver-facing display ([Drive modes §8.1][dm-8.1] R1). It never removes a page
by itself: it adds pages or, on **Replace my pages**, keeps the old ones for Undo.

**Why the app needs it (all five steps are Proposed).** The owner asked for a wizard that
builds dashboards at setup and after new apps; the approved specs have only per-class
default rotations ([Drive modes §5.9][dm-5.9]).

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `launcher-builder-apps` | picks the car and which apps' widgets to use | no car → "Build with GPS and app widgets only" or **Add a car**; an app not installed → **Get in Store** |
| 2 | `launcher-builder-display` | picks the display it is for | the display is Moving → "Applies when the car is parked" |
| 3 | `launcher-builder-templates` | ticks presets | a preset needs a missing app → greyed with **Get**; none ticked → **Next** disabled |
| 4 | `launcher-builder-review` | checks the pages, Parked and Moving | a page breaks a Moving rule → shown with the fix; **Fix it for me** drops the extra tile |
| 5 | `launcher-builder-done` | applies; may **Undo** | save fails → "Couldn't save. Nothing changed." **Try again** |

### launcher-builder-apps — Builder step 1: car and apps  [Proposed]
- **Why the app needs it:** see the line above the table.
- **Purpose:** choose whose data the pages show.
- **Owner:** os
- **Opens from → goes to:** **Build dashboards**; setup step 11. **Next** → step 2.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content:** 1. SetupStepper "Step 1 of 5 · Car and apps". 2. **Car:** one card per garage
  vehicle; "Discovery 2 · Td5" ticked, with "Engine (Td5) and SLABS · one at a time on
  K-line". 3. **Apps with widgets**, ticks: Diagnostics, Trips, Map, Navigation, Media,
  Phone, Social, Maintenance, Camera; each with its widget count. 4. **Get more apps** →
  Store.
- **States:** no car: the card "No car yet" with **Add a car** and **Continue without**.
  Loading: skeletons. Offline: Store link greyed. Moving: locked view.
- **Safety and driving rules:** Park to edit.
- **Components:** SetupStepper (new), Card, ListRow (tick), Button.
- **Spec refs:** [Drive modes §5.9][dm-5.9] · [app model §15][am-15].
- **Open questions:** none.

### launcher-builder-display — Builder step 2: display  [Proposed]
- **Why the app needs it:** see the line above the table.
- **Purpose:** pick the screen the pages are built for; each class is authored, never scaled.
- **Owner:** os
- **Opens from → goes to:** step 1. **Next** → step 3; **Back** → step 1.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; desktop Night.
- **Content:** 1. Stepper "Step 2 of 5 · Display". 2. Cards for each known display: "Dash
  screen · HU-7 · 1024 × 600 · driver-facing", "Rear screen · tablet · passengers only",
  "This phone". 3. **Dock position** for wide head units: Side (default) · Bottom.
- **States:** a display that is Moving: banner "Applies when the car is parked". Moving
  (this screen): locked view.
- **Safety and driving rules:** a driver-facing display gets a Moving section on every In
  Drive page ([UI §12.1][ui-12.1]).
- **Components:** SetupStepper, Card, Segmented.
- **Spec refs:** [UI §3.1][ui-3.1] · [Drive modes §4.4][dm-4.4].
- **Open questions:** none.

### launcher-builder-templates — Builder step 3: templates  [Proposed]
- **Why the app needs it:** see the line above the table.
- **Purpose:** tick the preset dashboards to add, in carousel order.
- **Owner:** os
- **Opens from → goes to:** step 2. **Next** → step 4.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Night.
- **Content:** 1. Stepper "Step 3 of 5 · Templates". 2. The preset cards of
  `launcher-presets` (45-h) with ticks; suggested for this car: Dashboard, Map, Diagnostic,
  Off-road D2, Minimal / Night (the per-class defaults); Convoy needs Social; Split needs a
  media app. 3. **How to add:** Add to my pages (default) · Replace my pages (old pages kept
  for Undo).
- **States:** none ticked: **Next** disabled with "Pick at least one". Moving: locked view.
- **Safety and driving rules:** Park to edit.
- **Components:** SetupStepper, Card (tick), Segmented.
- **Spec refs:** [Drive modes §5][dm-5] · [Drive modes §5.9][dm-5.9].
- **Open questions:** none.

### launcher-builder-review — Builder step 4: review the pages  [Proposed]
- **Why the app needs it:** see the line above the table.
- **Purpose:** see the carousel that will result, with what shows while driving.
- **Owner:** os
- **Opens from → goes to:** step 3. **Apply** → step 5; a page opens its preview.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content:** 1. Stepper "Step 4 of 5 · Review". 2. Page thumbnails in order: Home, Cluster,
  Map, Tiles, Minimal, Tilt, Trail, each with an **In Drive** switch and drag handle.
  3. **Drive rotation:** the first four In Drive pages. 4. **Data notes:** "RPM and Coolant
  read 'Not in this session' while SLABS is in session"; "Pitch and roll need the node's
  IMU". 5. Any failed rule in words with **Fix it for me**.
- **States:** all pass: `ok` "Ready for driving". Moving: locked view.
- **Safety and driving rules:** Apply is refused while any In Drive page fails
  ([Drive modes §8.2][dm-8.2]).
- **Components:** SetupStepper, Page thumbnail (new), switch, ListRow.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §8.2][dm-8.2].
- **Open questions:** none.

### launcher-builder-done — Builder step 5: applied, with Undo  [Proposed]
- **Why the app needs it:** see the line above the table.
- **Purpose:** confirm the change and offer a way back.
- **Owner:** os
- **Opens from → goes to:** step 4. **Go to my pages** → the first new page; **Undo** →
  the carousel as it was; **Change the theme** → the theme wizard (45-j) in setup.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content:** 1. `check` "7 pages ready". 2. Thumbnails of the new pages. 3. **Undo**
  (available here and in the home pages list for 7 days as "Undo dashboard builder").
- **States:** saving: "Saving…"; error: "Couldn't save. Nothing changed." **Try again**.
- **Safety and driving rules:** the change applies to a Moving display at its next Parked
  (R7).
- **Components:** SetupStepper, Page thumbnail, Button.
- **Spec refs:** [Drive modes §7.8][dm-7.8] · [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

<!-- links -->
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#5-the-seven-presets
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[dm-7.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-3.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#31-layout-classes
