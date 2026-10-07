---
title: "Designer brief 45-f — widget setup pages (2 of 3): map, compass and incline, trip computer, fuel and range, service due, alarm status, camera, clock and date"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Second file of widget setup pages, each in the shared OS-drawn setup frame (45-d). It
  covers the map (from the Map app), compass and incline for off-road use, the trip computer
  (Trips), fuel and range (honest about the D2 having no decoded fuel level), service due
  (Maintenance), alarm status (a safety item drawn by the OS), a camera (Camera app, Parked
  only on driver-facing screens), the clock and the date. Each block gives styles, data,
  options, a real Discovery 2 example and how the widget renders while Moving.
---

# 45-f — Widget setup pages: place, trip, car care and time

Back to [45-a](45-launcher-a.md); shared rules in [45-e](45-launcher-e.md).

### widget-setup-map — Map  [New]
- **Purpose:** own position, trail and route on the Ostler Night or Day map. Widget from:
  Map app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap on the
  placed map (Parked) opens the Map app.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render with the speed overlay; phone Day.
- **Content:** 1. Preview: puck, trail, attribution `info` control. 2. **Look:** Heading up,
  North up. 3. **Data:** Trail This trip · Off; Layers from installed apps: Route
  (Navigation), Convoy markers (Map, opted-in ride only). 4. **Overlays:** up to three tiles
  (Speed 64 km/h, Altitude 312 m, Heading 214° SW). 5. **Sizes:** wide, hero.
- **States:** "Needs GPS"; offline basemap falls back to `bg`, trace and puck. Moving: the
  `map` pane; overlays count against the six tiles; no panning or search.
- **Safety and driving rules:** no names, avatars or plates on the map while Moving; rules in
  40-drive-h (`drive-widget-settings-map`) ([UI §12.1][ui-12.1]).
- **Components:** Map, Segmented, ListRow.
- **Spec refs:** [Drive modes §5.3][dm-5.3] · [visual §7][vds-7] · [UI §13.5][ui-13.5].
- **Open questions:** none.

### widget-setup-compass-incline — Compass and incline  [New]
- **Purpose:** heading, pitch and roll for off-road driving. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render (Tilt page); phone Day.
- **Content:** 1. Preview: side and rear D2 silhouettes, "Pitch 4° · Roll 12°", "214° SW".
  2. **Look:** Pitch, Roll, Pitch and roll, Compass. 3. **Data:** Pitch and Roll · node IMU
  · candidate; Heading · GPS. 4. **Options:** Warning roll from 25°, Critical from 30°;
  Zero here (Parked on level ground). 5. **Sizes:** small, medium, hero.
- **States:** "Needs the node's IMU"; heading frozen below 3 km/h with "stale". Moving: one
  tile per value; the silhouette steps ≤ 4 Hz.
- **Safety and driving rules:** tilt is an aid, not a safety limit; label "Estimate".
- **Components:** Inclinometer (new), Compass (new), stepper.
- **Spec refs:** [Drive modes §5.5][dm-5.5] · [Drive modes §4.2][dm-4.2].
- **Open questions:** none.

### widget-setup-trip-computer — Trip computer  [New]
- **Purpose:** this trip's distance, time and average speed. Widget from: Trips app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens the
  trip in Trips.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: "Trip 42 km · 0:51 · avg 49 km/h". 2. **Look:** Grid, One line.
  3. **Data:** pick up to four: Distance, Time, Average speed, Max altitude, Fuel economy
  (candidate). 4. **Options:** Since: This trip · Today · Reset by hand. 5. **Sizes:**
  small, medium, wide.
- **States:** "Not recording" when Trips is paused. Moving: up to two values as `value` or
  tiles.
- **Safety and driving rules:** neutral facts only: no score or speed ranking
  ([UI §12.2][ui-12.2]).
- **Components:** StatTile, Segmented.
- **Spec refs:** [Drive modes §9][dm-9] · [UI §12.2][ui-12.2].
- **Open questions:** none.

### widget-setup-fuel-range — Fuel and range  [New]
- **Purpose:** what the car and the fuel log can honestly say about fuel. Widget from:
  Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; **Log fuel**
  opens Maintenance (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: "Fuel level · Not available on this car", "Fuel now · candidate",
  "Range · estimated from your fuel log". 2. **Look:** Card, One line. 3. **Data:** Fuel
  now and Trip economy · Engine (Td5) · candidate; range from Maintenance's full-to-full
  economy and distance since the last fill (estimated). 4. **Sizes:** medium, wide.
- **States:** no Maintenance app: range "Needs Maintenance". Moving: one `value` line
  ("Range ≈ 310 km est.").
- **Safety and driving rules:** estimates always labelled; never a fake gauge.
- **Components:** StatTile, Card.
- **Spec refs:** [Maintenance §5][mg-5] · [UI §5.4][ui-5.4] · [launcher §9][lw-9].
- **Open questions:** **Decided ([launcher §9][lw-9]):** keep it as the starter pack's Fuel
  widget; it shows only what the pack or the fuel log can honestly say.

### widget-setup-service-due — Service due  [New]
- **Purpose:** the next maintenance item for this car. Widget from: Maintenance app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens the
  item in Maintenance.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: "Oil and filter · due in 640 km" with a band pill.
  2. **Options:** Show: Next item · Next three. 3. **Sizes:** medium, wide.
- **States:** "Nothing due"; "No service history yet · Add one". Moving: **Parked only**
  (reminders reach the driver only at trip start or end).
- **Safety and driving rules:** [Maintenance §8][mg-8].
- **Components:** Card, Chip (band).
- **Spec refs:** [Maintenance §8][mg-8] · [Drive modes §9][dm-9].
- **Open questions:** none.

### widget-setup-alarm-status — Alarm status  [New]
- **Purpose:** armed state and the last alarm event: the Security alert card. A **safety
  item** while a node is fitted. Widget from: System (data from the Security app).
- **Owner:** os
- **Opens from → goes to:** **Settings** on the placed widget; a tap opens the Security app.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day alerting.
- **Content:** 1. Preview: "Armed · last event 02:14 door opened". 2. **Look:** Card, Compact.
  3. **Sizes:** medium, wide. No Label, Icon or Colours rows.
- **States:** "Disarmed", "Armed", "Alerting" in `alarm`; no node: the widget is an
  ordinary one and may be removed. Moving: not in a layout; alarms reach the driver as an
  `alert_card`.
- **Safety and driving rules:** with a node: cannot be removed, renamed or recoloured
  ([Drive modes §8.1][dm-8.1] R3).
- **Components:** Card (tone), Chip (status).
- **Spec refs:** [Drive modes §7.2][dm-7.2] · [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

### widget-setup-camera — Camera  [New]
- **Purpose:** a live view from a fitted camera. Widget from: Camera app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens the
  Camera app (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup Parked; hu7 Night-dim Moving render (reversing camera only).
- **Content:** 1. Preview: a still frame with the camera name "Rear". 2. **Data:** Camera:
  Rear · Front · Tow hitch (from the Camera app). 3. **Options:** Show guide lines.
  4. **Sizes:** medium, wide, hero.
- **States:** "Camera offline"; "Needs the Camera app". Moving: **Parked only** on
  driver-facing screens, except a driving camera through `camera_live` where the Camera app
  declares it (reverse gear from SLABS).
- **Safety and driving rules:** no video on driver-facing screens while Moving, Passenger view
  included ([UI §12.1][ui-12.1]).
- **Components:** Card, video frame (new component), Segmented.
- **Spec refs:** [Drive modes §9][dm-9] · [UI §12.1][ui-12.1].
- **Open questions:** none.

### widget-setup-clock — Clock  [New]
- **Purpose:** the time, big. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: "14:32". 2. **Look:** Digital, Analogue (still hands, minute
  steps). 3. **Options:** 24-hour follows Settings; Show seconds (off; Parked only).
  4. **Sizes:** small, medium, hero.
- **States:** no time source yet: "—:—". Moving: one tile.
- **Safety and driving rules:** no seconds while Moving.
- **Components:** HeroStat, Segmented.
- **Spec refs:** [Drive modes §9][dm-9].
- **Open questions:** none.

### widget-setup-date — Date  [Proposed]
- **Why the app needs it:** the clock widget has no date; Android launchers ship one.
- **Purpose:** today's date. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day; hu7 Night.
- **Content:** 1. Preview: "Wed 7 Oct". 2. **Look:** Short, Long ("Wednesday 7 October").
  3. **Sizes:** small, medium.
- **States:** none special. Moving: one tile (short form).
- **Safety and driving rules:** ≤ 30 characters.
- **Components:** StatTile.
- **Spec refs:** [Drive modes §4.3][dm-4.3].
- **Open questions:** the starter catalogue ([launcher §9][lw-9]) gives the Clock widget a
  date option and has no separate Date widget; keep this block only if the owner wants both.

<!-- links -->
[dm-4.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#42-field-rules
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#53-map
[dm-5.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[mg-5]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#5-fuel-economy
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-13.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
[lw-9]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#9-the-starter-catalogue
