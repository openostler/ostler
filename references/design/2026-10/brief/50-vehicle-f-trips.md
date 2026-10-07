---
title: "Designer brief: vehicle and diagnostics (F) — Trips list, trip detail, playback, statistics, records and export"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-logs-at-scale-design.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  Sixth file of the vehicle and diagnostics brief. It gives full page content for the six
  existing Trips app screens (the recordings list at scale with search, filters, month
  scrubber, heatmap and the All events timeline; the map-first trip detail with its sheet,
  stat grid, time-at-speed donut and signal chart; playback with the scrubber; the
  Statistics tab; Records and Sprints with the honest "Needs fast GPS" state; and Export
  all). Frames draw from the two committed synthetic demo logs of the D2 pack, which are
  the product's only demo, so no invented trips are needed.
---

# Vehicle and diagnostics brief (F): Trips

**Data for frames.** Use the D2 pack's two committed synthetic sessions (ADR-0011: replaying
them is the demo; they carry a `demo` chip and are read-only):
- **Demo log 1**: "Highland, Scotland", 12 min, 11.21 km, max 92 km/h, modules TD5 then SLABS;
  notes "Rough idle after the junction", "Full-throttle climb: boost and coolant look fine",
  "ABS pump test while stopped, pump audible".
- **Demo log 2**: "near Okehampton, Devon", 7 min, 2.63 km, max 45 km/h, SLABS only; faults
  `3.4` right front wheel speed sensor (Logged) and `10.4` shuttle valve switch (Current); notes
  "Raise then lower left while parked…", "Front-right wheel speed drops out on the rough ground…".

On the Td5, road speed is usually GPS speed, because a SLABS session holds K-line; each figure
names its speed source ([UI §12.2][ui-12.2]). No score anywhere: neutral facts only.

### trips-list — Trips list  [Existing]
- **Purpose:** every recording of the vehicle, findable at scale.
- **Owner:** app:trips
- **Opens from → goes to:** dock or app drawer → Trips; the Last trip widget; strip REC chip; Rewind → trips-detail, trips-recording (card), trips-statistics and trips-records (tabs), trips-export-all, trips-share-sheet (row "…").
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night and Day, hu9 Night, desktop Night.
- **Content (top to bottom):**
  1. Tabs: **Trips · Statistics · Records** (Segmented).
  2. **Recording now · 14 min** Card (accent live dot): modules, sources, **Mark**, **End trip now**; when the car disconnects it reads "Paused — no connection" and hides Mark ([Logs at scale §1][ls-1]).
  3. Search "Search trips, places and notes"; filter Chips: vehicle, dates, module, has notes, minimum distance; **All events** toggle.
  4. "This year" day heatmap strip; a tap filters to that day.
  5. Sticky year and month headers; one row per trip: mini dark map (Ostler Night, trace in the speed ramp), "Highland, Scotland" (or the trip's name), start time, distance "11.2 km", duration "12 min", max speed "92 km/h · GPS", module names, note count, badges (`demo`, "Excluded", "Shared 2× · 1 active").
  6. Right-edge **month scrubber** (drag to jump); infinite scroll.
  7. All events on: the timeline also shows parked periods, alarm events, faults ("3.4 · SLABS"), notes and scan reports.
  8. Footer attribution: "Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)".
- **States:** empty: "No trips yet. Recording starts when the car connects." plus the demo logs. Loading: skeleton rows with grey map tiles. Offline: list from the local index; maps fall back to `bg` with the trace. Brain asleep: "Needs the Brain" Card with **Wake** (full Trips lives on the Brain). Idling: full. Moving: locked view with Open on phone. Passenger: not unlockable.
- **Safety and driving rules:** Parked-only on driver-facing head units ([UI §12.1][ui-12.1]); End trip now Parked or Idling only.
- **Components:** ListRow (mini dark map), Card (Recording now), Chip, Segmented, TextField (new component), MonthScrubber (new component), YearHeatmap (new component).
- **Spec refs:** [UI §12.2][ui-12.2] · [Visual §9][vds-9] · [Logs at scale §5][ls-5] · [Session logbook UI][sl-ui].

### trips-detail — Trip detail (map + sheet)  [Existing]
- **Purpose:** one trip as a map with its facts in a sheet.
- **Owner:** app:trips
- **Opens from → goes to:** a trips-list row; Rewind → trips-playback, trips-share-sheet, help-flow (Get help), trips-delete, live-picker (chart signal), diagnose-fault (a fault seen).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (peek and half), hu9 Night (map right, side sheet left on the RHD D2), phone Day.
- **Content (top to bottom):**
  1. Full-bleed map: violet trace with casing, start and end markers, attribution as a collapsed info control; floating chrome: back, date, **Share**, **Export**, "…".
  2. **Peek:** HeroStat distance "11.2 km" (or max speed) and a Scrubber with Material transport icons.
  3. **Half:** itinerary (start and end place and time); 3 × 3 stat grid: distance, average speed, max speed (sustained best beside it) / duration, idle, moving / elevation gain, stops, average moving speed; time-at-speed Donut in six speed-ramp bands with **Time / Distance** Segmented; DistributionBars.
  4. **Full:** speed over time area line with a picker for any recorded signal (RPM, Coolant, Turbo pressure, LateralAcc), gaps as gaps; **Faults seen** ("10.4 shuttle valve switch · Current"); notes; **Exclude from stats** toggle; **Export** (CSV, GPX, VBO); **Delete**; "About this trip" collapsed (name and description, editable inline).
- **States:** no GPS (K-line only): no map; the sheet becomes the page with "No location in this trip". Loading: map fallback `bg` with skeleton sheet. Demo log: read-only (no Delete, no name edit). Moving: locked view.
- **Safety and driving rules:** Parked only on head units; map-first, sheet on the passenger side ([UI §12.3][ui-12.3]).
- **Components:** Sheet over map, HeroStat, StatTile, Donut, Segmented, DistributionBars, Area line, Scrubber, Button, Chip.
- **Spec refs:** [UI §12.2][ui-12.2] · [UI §12.3][ui-12.3] · [Visual §10][vds-10].

### trips-playback — Trip playback  [Existing]
- **Purpose:** replay a trip on the map with a readout, at speed.
- **Owner:** app:trips
- **Opens from → goes to:** trips-detail play; Rewind (opens the newest trip at its end, paused) → trips-notes, trips-flag-sheet, trips-mark-note (retro mark), trips-replay-diagnose (whole-app replay), help-flow (marked range).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night, desktop Night.
- **Content (top to bottom):**
  1. Map with the trace stepped in the speed ramp, casing, legend; heading arrow; heading-up or north-up toggle; trace A and optional trace B as a parallel lane (channel picker re-colours).
  2. Collapsed sheet readout: speed hero, altitude, g, distance.
  3. **Scrubber** with note ticks (accent) and flag ticks (`warn`/`alarm`, range flags as short bars), the chip above the thumb for the note or flag at the cursor; ±10 s; **1× · 2× · 4× · 8×**; play/pause; **Jump to max speed**; while following a live trip "Latest".
  4. Clearly replay: the Link chip becomes "Replay · Exit to live", `main` has an amber edge.
- **States:** recording in progress: follows the end; scrubbing drops follow. Loading: "Loading trip…" in the chip place. Moving: locked (replay scrubbing is locked).
- **Safety and driving rules:** replay is read only; actions refuse with "Replay — read only" ([Replay §4][rn-4]).
- **Components:** Scrubber, Chip (speeds), HeroStat, Sheet over map, Legend.
- **Spec refs:** [UI §12.2][ui-12.2] · [Visual §8][vds-8] · [Replay §4][rn-4] · [Replay §8][rn-8].

### trips-statistics — Statistics tab  [Existing]
- **Purpose:** totals and records over a period, neutral facts only.
- **Owner:** app:trips
- **Opens from → goes to:** trips-list tab → trips-detail (a record), trips-records.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night, phone Day.
- **Content (top to bottom):** 1. Filters: vehicle, period (month, year, all). 2. All-time HeroStat: max speed with place and date, sustained best beside it. 3. Totals grid: distance, trips, total time, moving, idle, average distance, average duration, average speed, longest trip. 4. Speed distribution (trips by max-speed band, speed ramp). 5. Records rows (max speed, sustained best, longest trip, highest point). 6. Calendar: year heatmap and month calendar. 7. "2 trips excluded" line.
- **States:** too few trips: figures show "—" with "Needs more trips". Moving: locked.
- **Safety and driving rules:** no driving score, no speed ranking ([UI §12.2][ui-12.2]).
- **Components:** HeroStat, StatTile, DistributionBars, YearHeatmap (new component), Chip.
- **Spec refs:** [UI §12.2][ui-12.2].

### trips-records — Records and Sprints  [Existing]
- **Purpose:** best times per sprint band, only where the data can support them.
- **Owner:** app:trips
- **Opens from → goes to:** trips-list tab → trips-detail.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (the D2's honest state), hu9 Night.
- **Content (top to bottom):** 1. One Card per band: 0 → 60, 0 → 80, 0 → 100 km/h (mph equivalents per unit), custom. 2. Ranked rows: rank numeral in a `surface-3` disc, time, delta to best, peak speed, date. 3. On the D2 today every band reads **"Needs fast GPS"** with no time: sprints need ≥ 10 Hz speed or a calibrated IMU.
- **States:** no eligible trips as above; Moving: locked.
- **Safety and driving rules:** facts only; medals are numerals, not colours ([Visual §6][vds-6]).
- **Components:** Card, ListRow (rank, time, delta).
- **Spec refs:** [UI §12.2][ui-12.2] · [Visual §6][vds-6].

### trips-export-all — Export all  [Existing]
- **Purpose:** every trip out of Ostler in open formats, offline.
- **Owner:** app:trips
- **Opens from → goes to:** trips-list "…"; system Settings → Privacy → back with a saved archive.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night.
- **Content (top to bottom):** 1. "Export all trips" with the real count and size ("<n> trips · <size>"). 2. Formats checked: CSV, GPX, VBO, plus "Trip summary index (CSV)". 3. **Include notes** toggle (notes export as their own CSV). 4. **Export** (primary); progress "Packing <i> of <n>"; then **Save** or **Share**. 5. Line: "No Ostler server is needed. Your files stay yours."
- **States:** not enough space: "Needs <size> free". Brain asleep: Wake first. Idling without Park evidence, Moving: locked.
- **Safety and driving rules:** exit guarantee ([App model §14][am-14]).
- **Components:** Card, Checkbox (new component), Toggle (new component), Button, progress row.
- **Spec refs:** [UI §12.2][ui-12.2] · [App model §14.6][am-14].

[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-12.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#123-drive-mode-changes-31-35-53-54-10-u1-and-its-test
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[vds-10]: ../../../../specs/2026-10-07-visual-design-system-design.md#10-before-and-after
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[rn-4]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#4-whole-app-replay-ui
[rn-8]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#8-rewind-to-the-end-automatic-flags-the-flag-manager-and--in-replay-v13
[sl-ui]: ../../../../specs/2026-10-05-session-logbook-design.md#ui
[ls-1]: ../../../../specs/2026-10-06-logs-at-scale-design.md#1-record-only-while-connected
[ls-5]: ../../../../specs/2026-10-06-logs-at-scale-design.md#5-ui
[vds-9]: ../../../../specs/2026-10-07-visual-design-system-design.md#9-enforcement
