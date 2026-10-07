---
title: "Designer brief: vehicle and diagnostics (D) — live data, signal detail, charts and vehicle views"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-05-replay-notes-capture-design.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-03-vehicle-view-suite-design.md]
summary: >
  Fourth file of the vehicle and diagnostics brief. It covers live data on the Discovery 2
  Td5: the signal browser (the module's Live or Inputs area) with search, pack groups,
  proven and candidate badges, units and the Attention filter; a proposed signal detail page
  with its graph, normal band, limits and evidence; the multi-signal live chart and its
  channel picker; and the vehicle view suite from the draft vehicle-view spec, proposed as
  four pages on one shared silhouette: Body (BCU), SLABS ride heights and wheels, SRS airbag
  zones and the EAT gearbox, each honest about what is not yet decoded.
---

# Vehicle and diagnostics brief (D): live data and vehicle views

**Signal groups** (pack `layout.json` order): Engine · Temperatures · Fuelling · Pressures ·
Accelerator · Ride height · Wheels · Electrical · Inputs · Other. **Real signals to draw:**
TD5 RPM (rpm, limits 0–4800), Speed (km/h), Battery (V, 11.5–15.5), Coolant (°C, −40–105),
Intake air (°C), Fuel (°C), Turbo pressure (bar, 0.8–2.6), Injection (mg/stroke), Injector 1–5
(balance, −12–12), Pedal track 1–3 (V), Accelerator pedal (%), EGR and Wastegate (%,
`candidate`), Air flow (kg/hr, `candidate`), External temp (`candidate`); SLABS Height left and
right (raw, `proven`), Wheel speed FL/FR/RL/RR and ABS sensor (`candidate`), Centre diff lock
and Transfer box low range (`proven`).

### live-browser — Signal browser (Live or Inputs area)  [New]
- **Purpose:** every live signal of the module in session, findable, grouped and honest.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-system → Inputs; diagnose-fault related rows → live-signal (a row), live-chart (Chart selected), trips-recording (Recording now).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night (TD5, two columns), phone Night and Day, hu7 Night-dim Idling.
- **Content (top to bottom):**
  1. **Search** field "Search signals" (label, unit or name; Parked or Idling with Park evidence only on head units).
  2. Filter Segmented: **All · Attention 1 · Unverified** (Attention = out of the normal band; Unverified = `candidate`).
  3. Group sections with sticky kickers in pack order; each SignalRow (new component): label ("Turbo pressure"), value in tabular numerals with unit ("1.42 bar", a sample value for the frame), a RangeBar of the normal band for numbers, a state word for bits ("Centre diff lock · disengaged"), a `candidate` Chip (dashed underline on the value), stale grey with age.
  4. Row long-press or checkbox: **Select for chart** (up to 3) → bottom action bar "Chart 2 selected".
  5. **From NanoCom — not yet decoded** section at the end: menu items with no decode, `untranscribed` Chip, "Help decode it".
- **States:** loading: skeleton rows. Not connected: last values stale grey with age, "Connect to see live values". Module not in session: "Not in this session" on every row. No signal ("NO DATA"): "—", never 0. Moving: locked view (the Drive home pages are the live surface while Moving). Replay: values at the cursor in replay styling, not live.
- **Safety and driving rules:** read only; the search field is text entry (Parked only on head units, [UI §3.5][ui-3.5]).
- **Components:** TextField (new component), Segmented, SignalRow (new component), RangeBar (kit), Chip, StatTile.
- **Spec refs:** [UI §4.2][ui-4.2] · [UI §5.1][ui-5.1] · [UI §5.3][ui-5.3] · [Visual §8][vds-8].

### live-signal — Signal detail  [Proposed]
- **Why the app needs it:** the browser shows one line per signal; owners need one place for a signal's live graph, range, confidence and evidence.
- **Purpose:** one signal, live, with its graph and the reasons to trust it.
- **Owner:** app:diagnostics
- **Opens from → goes to:** live-browser row; diagnose-overview stat tile; diagnose-fault related row → live-chart (Add to chart), decode-lab (Help decode, service mode).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (Coolant), hu9 Night (Turbo pressure), phone Day.
- **Content (top to bottom):**
  1. HeroStat: kicker "Coolant · TD5", value and "°C", caption "updated 0.5 s ago".
  2. **Gauge** (240° arc) with the normal band in `band` ticks; out of range the arc and number turn `warn` or `alarm` with the word.
  3. **Last 5 minutes** area line (2 px, `series-mono`; live point `accent`), gaps as gaps; Segmented 1 min · 5 min · Session.
  4. Facts rows: Unit "°C"; Normal band; Limits "−40 to 105"; Confidence Chip `proven` with evidence ("21 1A@0 · verified against the car"); VSS path in mono "Vehicle.Powertrain.CombustionEngine.EngineCoolant.Temperature"; source "TD5 · K-line".
  5. **Related faults** (`5.2` coolant temp. circuit) and **Related signals** (Coolant sensor V).
  6. Actions: **Add to chart**, **Mark** (when recording), **Help decode it** (`candidate` only).
- **States:** `candidate`: a `warn`-free info Card "Not confirmed on a car yet" plus the reason (External temp: "the sensor is not fitted on every car"). Stale and missing as the browser. Moving: locked.
- **Safety and driving rules:** read only.
- **Components:** HeroStat, Gauge, Area line, Segmented, ListRow, Chip, Button.
- **Spec refs:** [UI §5.1][ui-5.1] · [UI §8.3][ui-8.3] · [Visual §8][vds-8].

### live-chart — Live multi-signal chart  [New]
- **Purpose:** up to three signals on one time axis, live, with marks.
- **Owner:** app:diagnostics
- **Opens from → goes to:** live-browser selection; live-signal Add to chart → live-picker (change a lane), trips-recording (Open in Trips), trips-mark-note (Mark).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu9 Night (RPM, Turbo pressure, Injection), phone Night landscape and portrait.
- **Content (top to bottom):**
  1. Lane chips: one per signal with series colour (`series-1…3`), value and unit; tap → live-picker; × removes.
  2. Stacked lanes (dense Canvas chart), shared crosshair, newest at the right; out-of-band spans shaded.
  3. Time window Segmented: 30 s · 2 min · 10 min. **Pause** freezes the view (recording continues).
  4. Footer: "Recording · 14 min" with **Mark** and **Open in Trips**, or "Not recording — connect to the car".
- **States:** a lane from another module: "Not in this session" lane. Empty: "Pick up to 3 signals". Moving: locked. Replay: follows the replay cursor.
- **Safety and driving rules:** read only; categorical series never with status colours ([Visual §3.3][vds-3.3]).
- **Components:** Chart (Canvas lanes, existing), Chip, Segmented, Button.
- **Spec refs:** [Replay §7][rn-7] · [Session logbook UI][sl-ui] · [Visual §8][vds-8].

### live-picker — Channel picker sheet  [New]
- **Purpose:** choose a signal for a chart lane or a trace.
- **Owner:** app:diagnostics
- **Opens from → goes to:** live-chart lane chip; trips-detail chart picker; trips-playback trace A or B → back with the choice.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone Night bottom sheet, hu9 Night side sheet.
- **Content (top to bottom):** 1. Search. 2. **Pinned** chips (defaults: Speed, RPM, Accelerator pedal, LateralAcc) and **Recent**. 3. Collapsible groups: GPS/Motion, Engine, Fuelling, Temperatures, Electrical, Switches, Chassis/SLABS, Accelerometer, Other. 4. Rows: label, unit, confidence Chip, pin toggle.
- **States:** a signal not recorded in this trip: greyed, "Not in this recording". Moving: locked.
- **Safety and driving rules:** search is text entry, Parked only on head units.
- **Components:** Sheet, TextField (new component), Chip, ListRow.
- **Spec refs:** [Replay §5][rn-5].

## The vehicle view suite (draft spec, so every page here is Proposed)

One shared top-down Discovery 2 silhouette, **VehicleBase** (new component), with named zones
(doors, bonnet, tailgate, four corners and lamps, windscreen, cabin, seats). A zone is active,
inactive or absent; absent reads **"Awaiting mapping"** with a dashed outline, never a made-up
state ([vehicle views: decisions][vv-dec], [architecture][vv-arch]). The draft's mock animation
is not drawn: there is no demo mode (ADR-0011). Calm instrument: neutral when healthy, status
colour with icon and word only when abnormal. All four open from diagnose-overview and are Parked
pages; while Moving they are locked (the Off-road preset home page is a separate design, `40-drive-*`).

### live-vehicle-slabs — SLABS vehicle view  [Proposed]
- **Why the app needs it:** the SLABS page in today's UI (`SlabsCar`) is loved but sits outside the kit; the suite moves it onto the shared base.
- **Purpose:** ride heights, wheels and drivetrain switches on the car's outline.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-overview (SLABS) → live-signal (a zone), diagnose-faults (a corner with a fault).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu9 Night, phone Night, phone Day.
- **Content (top to bottom):** 1. Silhouette with four wheel overlays: Wheel speed and ABS sensor V (`candidate`). 2. Rear Height left and right (raw counts, `proven`) beside the rear axle. 3. Chips under the car: Centre diff lock, Transfer box low range, Reverse gear, Neutral gear, Door open. 4. Battery and ECU supply. 5. A corner with a logged fault (`3.4` right front wheel speed sensor) wears the `warn` edge and word.
- **States:** module not in session: whole view stale grey, "Move session here". Moving: locked.
- **Safety and driving rules:** read only; output tests stay in diagnose-tests ([vehicle views: out of scope][vv-out]).
- **Components:** VehicleBase (new component), Chip, StatTile.
- **Spec refs:** [vehicle views: later slices][vv-later] · [UI §4.2][ui-4.2].

### live-vehicle-body — Body (BCU) vehicle view  [Proposed]
- **Why the app needs it:** lamps, doors and windows read best on the car, and it is the first slice of the draft spec.
- **Purpose:** body inputs on the silhouette.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-overview (BCU) → help-flow (Help decode it).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu9 Night, phone Night.
- **Content (top to bottom):** 1. Zones for doors (driver, passenger), bonnet, tailgate; lamps (side, dipped, main beam, front and rear fog, indicators, hazard, brake, reverse); windows front left and right; front and rear wiper; heated screen; ignition position and battery readouts. **Today every zone reads "Awaiting mapping"**: the BCU hides its inputs until security access, so nothing is decoded; a banner says so with **Help decode it**.
- **States:** not in session: stale grey with "Move session here"; never animated. Moving: locked.
- **Safety and driving rules:** read only; no output tests from this page ([vehicle views: out of scope][vv-out]).
- **Components:** VehicleBase (new component), Card (info), Button.
- **Spec refs:** [vehicle views: Body page][vv-body].

### live-vehicle-airbag — SRS airbag vehicle view  [Proposed]
- **Why the app needs it:** airbag faults name places in the car; drawing them there is clearer than a code list.
- **Purpose:** read-only fault status per airbag and pretensioner zone.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-overview (SRS) → diagnose-fault.
- **Layout classes:** phone · tablet · desktop · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):** 1. Zones: driver's airbag, passenger's airbag, left and right pretensioner, driver's and passenger's side airbag, crash sensors. 2. A zone with a fault wears its status word and code (`022` left-hand seat-belt pretensioner circuit, open circuit). 3. Footer: "Read only by construction. No clear, no tests."
- **States:** faults not read: "Read faults to fill the zones". Offline: last read with age. Moving: locked.
- **Safety and driving rules:** read only; no Clear offered for SRS ([ADR-0033 §5][adr33-5]).
- **Components:** VehicleBase (new component), Chip.
- **Spec refs:** [vehicle views: later slices][vv-later].

### live-vehicle-eat — EAT gearbox vehicle view  [Proposed]
- **Why the app needs it:** the gearbox has many pressures and switches that read best as a diagram.
- **Purpose:** selector, speeds, oil temperature and pressures for the automatic gearbox.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-overview (EAT) → help-flow (Help decode it).
- **Layout classes:** phone · tablet · desktop · hu9 · huwide. **Draw first:** hu9 Night, phone Night.
- **Content (top to bottom):** 1. P R N D selector. 2. Gear switches W X Y Z and the High/Low range switch. 3. Turbine and output speed, oil temperature, pressures. **Today every value reads "Not supported yet"**: the EAT data block is not decoded.
- **States:** as the other views; never animated. Moving: locked.
- **Safety and driving rules:** read only.
- **Components:** VehicleBase (new component), StatTile.
- **Spec refs:** [vehicle views: later slices][vv-later].
- **Open questions:** should the vehicle view spec (draft) be approved before these four pages are designed, and do they live under Diagnose Overview as drawn here (the draft says the Drive tab)?

[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-4.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#42-vehicle--systems--function-areas
[ui-5.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#51-shape
[ui-5.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#53-three-rendering-tiers
[ui-8.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#83-data-evidence-fixtures-and-scrub
[vds-3.3]: ../../../../specs/2026-10-07-visual-design-system-design.md#33-data-ramps-and-chart-colours-datatokensjson
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[adr33-5]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#5-clearing-fault-codes-made-safe
[rn-5]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#5-recording-ui-notes-ui-and-the-replay-map
[rn-7]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#7-analysis-tab-and-rewind-v11
[sl-ui]: ../../../../specs/2026-10-05-session-logbook-design.md#ui
[vv-dec]: ../../../../specs/2026-10-03-vehicle-view-suite-design.md#decisions-locked
[vv-body]: ../../../../specs/2026-10-03-vehicle-view-suite-design.md#body-bcu-page--the-first-slice
[vv-later]: ../../../../specs/2026-10-03-vehicle-view-suite-design.md#later-slices-same-base
[vv-arch]: ../../../../specs/2026-10-03-vehicle-view-suite-design.md#architecture
[vv-out]: ../../../../specs/2026-10-03-vehicle-view-suite-design.md#out-of-scope
