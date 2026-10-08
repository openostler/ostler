---
title: "Designer brief 45-e — widget setup pages (1 of 3): gauges, graph, multi-value tile, warning lights, ride height and G-meter"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  First of three files with one setup page per widget in the starter set. Each page sits in
  the shared setup frame (45-d) that the OS draws from the widget's settings schema, and
  lists the widget's styles, data source, options, preview example and Moving behaviour.
  This file covers the analogue, digital, bar and sweep gauges, the graph (sparkline and
  history), the multi-value tile, the warning lights (the fault telltale widget, a safety
  item), the SLABS ride height and the G-meter, all with real Discovery 2 Td5 and SLABS
  signals, ranges and confidence words. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 45-e — Widget setup pages: gauges and vehicle data

Back to [45-a](45-launcher-a.md). **Shared rules for 45-e, 45-f and 45-g.** Every page here
is the setup frame (`drive-widget-settings`, [45-d](45-launcher-d.md)) filled from the
widget's settings schema: the OS draws it; the widget's app may add one custom page behind
**More settings**. Each page opens from the widget picker or **Settings** on a placed widget,
and **Save** returns to edit mode. All are Park to edit on a driver-facing display and show
the locked view while Moving (40-drive-b; [Drive modes §8.1][dm-8.1] R1); the "Moving"
state below describes the **widget's render** in a Drive page, which the frame previews under
**While driving**. Colours follow the theme tokens; status colours (ISO 2575) appear only out
of range, always with their word. **Owner** is the OS for every setup page; "Widget from"
names the app that ships the widget.

### widget-setup-gauge-analogue — Analogue gauge  [New]
- **Purpose:** a 240° arc gauge for one number. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: Coolant 88 °C on the arc, band 80–100 °C. 2. **Look:** Calm arc
  (default), Ticks and numerals, Needle (a static needle stepped ≤ 4 Hz). 3. **Data:**
  Coolant · Engine (Td5) · proven; range −20–120 °C; Warning 105–112, Critical from 112.
  4. **Options:** Show min and max marks (off); Peak hold for this trip (off, Parked only).
  5. **Sizes:** small, medium, hero.
- **States:** "Not in this session" (SLABS holds the K-line); "—" when missing; stale grey with
  age. Moving: one tile; digits ≥ 56 px; arc steps, never glides.
- **Safety and driving rules:** no glow and no accent on the value in the default look; peak hold hidden while Moving
  ([visual §8][vds-8], [Drive modes §4.3][dm-4.3]).
- **Components:** Gauge, Segmented, stepper (new).
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [visual §8][vds-8].
- **Open questions:** **Decided ([launcher §9][lw-9]):** the starter Analogue gauge offers
  needle or fill; a needle is static and stepped at ≤ 4 Hz.

### widget-setup-gauge-digital — Digital gauge  [New]
- **Purpose:** a big number with unit and label (the StatTile). Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: Battery 13.9 V. 2. **Look:** Number, Number with kicker, Hero
  (one per page). 3. **Data:** Battery · Engine (Td5) or SLABS · proven; range 10–16 V;
  Warning below 12.4 or above 14.8, Critical below 11.5. 4. **Options:** Decimals 1; Show the
  source word ("Td5", "SLABS", "GPS"). 5. **Sizes:** small, medium, hero.
- **States:** candidate signals (EGR %) carry the dashed underline and "candidate"; "—" when
  missing. Moving: one tile.
- **Safety and driving rules:** a number never clips: it drops one type step
  ([visual §4][vds-4]).
- **Components:** StatTile, HeroStat, Segmented.
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [visual §8][vds-8].
- **Open questions:** none.

### widget-setup-gauge-bar — Bar gauge  [New]
- **Purpose:** a straight bar with the normal band, for side gauges. Widget from: Starter
  widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: Turbo pressure 1.2 bar, band 0.9–2.3. 2. **Look:** Horizontal,
  Vertical. 3. **Data:** Turbo pressure · Engine (Td5) · proven; range 0.8–2.6 bar.
  4. **Options:** Show the number (on). 5. **Sizes:** small, medium.
- **States:** as the digital gauge. Moving: one tile.
- **Safety and driving rules:** as the analogue gauge.
- **Components:** Gauge (bar variant), Segmented.
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [Drive modes §5.2][dm-5.2].
- **Open questions:** none.

### widget-setup-gauge-sweep — Sweep gauge  [New]
- **Purpose:** a stepped segment sweep, the Dashboard preset's RPM. Widget from: Starter
  widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: RPM 1850, 10 segments. 2. **Look:** Straight, Curved. 3. **Data:**
  RPM · Engine (Td5) · proven; range 0–4800 rpm; normal 650–4200; Warning from 4200.
  4. **Options:** Segments 8 · 10 · 12. 5. **Sizes:** small, medium, wide.
- **States:** "Not in this session" in a SLABS session. Moving: one tile; segments step at
  ≤ 4 Hz with hysteresis.
- **Safety and driving rules:** no shift-light flashing; colour only on level change
  ([Drive modes §4.3][dm-4.3]).
- **Components:** Gauge (sweep variant, new).
- **Spec refs:** [Drive modes §5.2][dm-5.2] · [Drive modes §4.3][dm-4.3].
- **Open questions:** none.

### widget-setup-graph — Graph (sparkline and history)  [New]
- **Purpose:** a value over time. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap on the
  placed graph opens Trips' replay at that time.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: Coolant over the last 10 minutes. 2. **Look:** Sparkline, Area
  line with axis. 3. **Data:** any number signal, up to three series (Injector 1–3 balance,
  normal −4 to 4). 4. **Options:** Window 1 min · 10 min · This trip; Show the normal band.
  5. **Sizes:** medium, wide, hero.
- **States:** gaps where the system was not in session, drawn as breaks, never as zero.
  Moving: **Parked only**: in a Moving section it is absent; the frame says so.
- **Safety and driving rules:** no sparkline or animation while Moving
  ([Drive modes §4.3][dm-4.3]); at most three series ([visual §3.3][vds-3.3]).
- **Components:** Sparkline, Area line, Segmented.
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [visual §8][vds-8].
- **Open questions:** none.

### widget-setup-multi-value — Multi-value tile  [New]
- **Purpose:** two to four small values in one tile, or one status line. Widget from:
  Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: "Coolant 88 °C · 13.9 V". 2. **Look:** Status line (one line),
  Grid 2×2. 3. **Data:** up to four signals, each with a short label (≤ 12). 4. **Sizes:**
  medium, wide.
- **States:** a missing value shows "—" in its place. Moving: the status line as the
  `value` template (two values, ≤ 30 characters, counts as two tiles); the 2×2 grid is
  Parked only.
- **Safety and driving rules:** [Drive modes §4.3][dm-4.3] `value` limits.
- **Components:** StatTile (compact), Segmented.
- **Spec refs:** [Drive modes §5.7][dm-5.7] · [Drive modes §4.3][dm-4.3].
- **Open questions:** none.

### widget-setup-warning-lights — Warning lights (telltales)  [New]
- **Purpose:** the warnings widget: current and logged faults per system. A **safety
  item**. Widget from: System (drawn by the OS).
- **Owner:** os
- **Opens from → goes to:** **Settings** on the placed widget (it cannot be added twice or
  removed); a tap on the widget opens the fault sheet (40-drive-a).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: "2 faults · Engine (Td5) P0403 EGR throttle · SLABS RF wheel
  sensor low". 2. **Look:** List, Icons only (ISO glyphs with counts). 3. **Options:** Show
  logged faults (on); Systems shown: All. 4. **Sizes:** medium, wide (not small).
  No Label, Icon or Colours rows.
- **States:** "No faults" with `ok`; "SLABS not in this session; last read 14:02". Moving:
  not in a layout: the strip chip and `telltale_list` carry faults while driving.
- **Safety and driving rules:** cannot be removed, hidden or covered; may move, resize and be
  restyled under the render check ([Drive modes §8.1][dm-8.1] R3).
- **Components:** Card (tone), ListRow, Chip (status).
- **Spec refs:** [Drive modes §7.2][dm-7.2] · [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

### widget-setup-ride-height — Ride height (SLABS)  [New]
- **Purpose:** rear left and right air-suspension heights from SLABS. Widget from: Starter
  widgets (needs the D2 pack).
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens
  Diagnostics → SLABS (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: a rear view of the D2 with two bars, "Left 148 · Right 151
  (raw)". 2. **Look:** Rear view, Two numbers. 3. **Data:** Height left (raw) and Height
  right (raw) · SLABS · proven; range 0–255; normal 135–165. 4. **Options:** Show the
  difference (on). 5. **Sizes:** medium, hero.
- **States:** "Not in this session · read by SLABS" while the Td5 holds the K-line; raw
  units, never shown as mm. Moving: Parked only by default (it needs a SLABS session).
- **Safety and driving rules:** reading only; no levelling action from the widget.
- **Components:** Gauge (bar), illustration (new: vehicle rear outline in `text-2`).
- **Spec refs:** [Drive modes §5.2][dm-5.2] · [Drive modes §5.5][dm-5.5].
- **Open questions:** raw counts until a millimetre scale is proven.

### widget-setup-g-meter — G-meter  [New]
- **Purpose:** lateral and longitudinal g from the node's IMU. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: a dot in a circle, "0.12 g". 2. **Look:** Circle, Two numbers.
  3. **Data:** node IMU (levelled) · candidate. 4. **Options:** Scale 0.5 g · 1 g; Peak
  ring for this trip. 5. **Sizes:** small, medium.
- **States:** "Needs the node's IMU"; "Level the IMU first" until calibrated. Moving:
  **Parked only** (Passenger view may show it).
- **Safety and driving rules:** not a driving score; no ranking ([UI §12.2][ui-12.2]).
- **Components:** Gauge (g-circle variant, new).
- **Spec refs:** [Drive modes §5.2][dm-5.2] · [UI §12.1][ui-12.1].
- **Open questions:** none.

<!-- links -->
[dm-4.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#42-field-rules
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#52-dashboard-realdash-style-cluster
[dm-5.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[dm-5.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#57-minimal--night
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[vds-3.3]: ../../../../specs/2026-10-07-visual-design-system-design.md#33-data-ramps-and-chart-colours-datatokensjson
[vds-4]: ../../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[lw-9]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#9-the-starter-catalogue
