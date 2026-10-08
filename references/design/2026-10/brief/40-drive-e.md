---
title: "Designer brief 40-e — Drive home pages, part 1: Diagnostic, Dashboard, Map and Minimal"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-navigation-addon-design.md]
summary: >
  First Drive home-page brief file. Drive home pages sit in one flat carousel and each preset
  only adds pages to it (45-launcher-a). It sets what every Drive home page shares (the Drive
  strip per class, the Moving template and its limits, honest value states, and the map from
  VSS paths to the Discovery 2 Td5 and SLABS signals), then gives one block per page: Tiles
  and the Parked System view (Diagnostic preset), Cluster and Map (Dashboard preset), Map
  (Map preset) and Minimal (Minimal / Night preset). Each block lists the widgets and
  bindings per class as the shipped preset files hold them, the Moving grid and placement,
  and the Parked extras the spec allows. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 40-e — Drive home pages, part 1

Back to [40-a](40-drive-a.md) for the conventions and the file list. Pages continue in
[40-f](40-drive-f.md); the switcher and Drive menu are in [40-g](40-drive-g.md).

## What every Drive home page shares

**Terms.** Drive home pages sit in **one flat carousel** with page dots (model:
[45-launcher-a](45-launcher-a.md)). A former Drive mode is now a **preset**: it only **adds
pages** to that row (Dashboard adds "Cluster" and "Map"). Swipe or `left`/`right` moves to
the next page; the Drive page chip cycles the rotation and opens the flat page list. Each
block below is one page; the Moving rules hold per page.

**Frame.** The Drive home page is full screen: the strip on top, the dock on the driver's side (right
on the D2), no page heading. Rows share the height (`grid-auto-rows: 1fr`); nothing scrolls.
Content areas: HU-5 720 × 432, HU-7 928 × 544, HU-9/10 1168 × 656, HU-wide 1808 × 656, phone
about 393 × 730 ([Drive modes §4.4][dm-4.4]).

**Drive strip (draw this per class; chip word = the current page's name).** Phone: Back · Drive page chip ·
telltale · Security (with a node) · Mark. HU-5: Back · Drive page chip · telltale · Security or
Link · Clock · Mark. HU-7 adds Link. HU-9/10 adds 12 V. HU-wide adds REC and the device slot.
The telltale chip appears only while a fault is active (as the live strip does).

**Moving template (every page).** Only the page's Moving section renders: ≤ 6 tiles (a hero
counts as one; a `value` line counts as two), panes ≤ 2 on HU-5, HU-7 and phone and ≤ 3 on
HU-9/10 and HU-wide, one of each kind (`map`, `media`, `call`). Digits ≥ 56 px
(`type-num-xl`: 64 px HU-5/7, 72 px HU-9/10 and HU-wide), labels ≥ 24 px, refresh ≤ 4 Hz,
no tween (an rpm bar steps), no sparkline, no animation except the red alarm pulse (glow is the theme's choice, under the render check).
Minimum tile and pane: HU-5 208 × 176 and 340 × 300; HU-7 280 × 240 and 440 × 360; HU-9/10
260 × 290 and 540 × 420; HU-wide 280 × 290 and 560 × 560; phone 170 × 200 and 361 × 300.
Overlay tiles on a map pane hug its corners on `surface-glass`
([Drive modes §4.3][dm-4.3], [UI §12.1][ui-12.1]).

**States for every page.** Parked and Idling (with Park evidence): the full Parked grid.
Moving: the Moving section. Passenger view: the full grid only if every widget is vehicle
state, own location or a driving camera, still without animation. Unknown speed: as Moving.
Values: live in `text-1`; stale in `text-3` with the word "stale"; missing "—" with the
reason in words: "Not available on this car", "Not in this session · Read by Engine (Td5)",
"Needs GPS", "No GPS fix", "Needs the node's IMU", "No value yet"; `candidate` figures carry a
dashed underline. A tile out of range turns `warn` or `alarm` with its word ("High").
**Draw first** for every page: hu7 Night-dim Moving, hu7 Night Parked, hu5 Night-dim Moving,
huwide Night-dim Moving, phone Night Moving, phone Day Parked.

**D2 signals behind the VSS paths** (pack signal store, confidence in brackets):

| VSS path in the preset | Td5 session | SLABS session | Else |
|---|---|---|---|
| `Vehicle.Speed` | `speed` km/h (proven) | not in session | GPS speed, labelled "GPS" |
| `…CombustionEngine.Speed` (rpm) | `rpm` (proven; normal 650–4200) | "Not in this session" | — |
| `…EngineCoolant.Temperature` | `coolant_temp` °C (proven; normal 80–100) | "Not in this session" | — |
| `…CombustionEngine.MAP` (boost) | `manifold_press` bar (proven; normal 0.9–2.3) | "Not in this session" | — |
| `Vehicle.LowVoltageBattery.CurrentVoltage` | `battery` V (proven) | `battery` V (proven) | node 12 V |
| `…Transmission.IsLowRangeEngaged` | "Not in this session" | `transfer_low` (proven) | — |
| `Vehicle.Ostler.Chassis.RideHeight.RearLeftRaw` / `RearRightRaw` | — | `height_left` / `height_right` raw (proven; normal 135–165) | — |
| `…FuelSystem.RelativeLevel` | "Not available on this car" | same | — |
| `Vehicle.Orientation.Pitch` / `Roll` | "Needs the node's IMU" | same | — |
| `…CurrentLocation.Altitude` / `Heading` | GPS | GPS | "Needs GPS" |

### drive-diagnostic-tiles — Diagnostic · Tiles  [Existing]
- **Purpose:** today's Drive screen as one page: the six tiles of the system in session.
- **Owner:** app:diagnostics
- **Opens from → goes to:** the page "Tiles" (icon `stethoscope`), which the
  Diagnostic preset adds; the next page is the System page (Parked only).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** as above,
  plus a critical-coolant variant on hu7 Night-dim Moving.
- **Content (Td5 session, from the pack's Drive view):** 1. **Boost** (`manifold_press`,
  bar, 2 decimals, gauge). 2. **Coolant** (`coolant_temp`, °C, gauge). 3. **Battery** (V, 1
  decimal). 4. **Intake air** (`air_temp`, °C). 5. **Fuel now** (`economy`, L/mil,
  `candidate`). 6. **Trip** (`trip_economy`, L/mil, `candidate`).
- **Grids:** HU-5 and HU-7 3 × 2; HU-9/10 4 × 2 (Boost, Coolant, Battery, Intake / Fuel now,
  Trip); HU-wide 6 × 1 tall tiles; phone 2 × 3. Parked uses the same six on the finer grid.
- **Moving:** all six tiles (`tiles`), exactly at the limit.
- **States:** SLABS or BCU in session: the page shows that system's car view (see the System
  page). No session: every tile "Not in this session". As the shared states above.
- **Safety and driving rules:** the economy figures stay marked `candidate`
  ([UI §5.4][ui-5.4]); no sparkline while Moving.
- **Components:** StatTile, Gauge (240° arc, `band` normal range, neutral in range).
- **Spec refs:** [Drive modes §5.1][dm-5.1] · [Drive modes §5.8][dm-5.8] ·
  [Drive modes §4.3][dm-4.3] · [UI §12.3][ui-12.3].
- **Open questions:** none.

### drive-diagnostic-system — Diagnostic · System view (Parked page)  [Existing]
- **Purpose:** the pack's picture of the module in session, Parked only.
- **Owner:** app:diagnostics
- **Opens from → goes to:** `right` from the Tiles page when Parked.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked (SLABS), huwide Night Parked, phone Day.
- **Content (SLABS session):** 1. A top-down Discovery outline labelled "FRONT". 2. At each
  wheel (FL, FR, RL, RR): wheel speed (raw, `candidate`) and ABS sensor voltage ("V",
  `candidate`, normal 2.0–2.4 V); a wheel turns `alarm` when out of range. 3. Caption "wheel
  order unconfirmed". 4. **Height left** and **Height right** (raw, normal 135–165, with a
  range bar). BCU session: the body view (doors, switches by group). Td5: none (the page is
  absent).
- **States:** Parked and Idling: shown. Moving: the page is absent (not greyed);
  `left`/`right` stay on Tiles.
- **Safety and driving rules:** not a template view, so never while Moving
  ([Drive modes §5.8][dm-5.8]).
- **Components:** StatTile, range bar, vehicle diagram (new component: top-down outline).
- **Spec refs:** [Drive modes §5.1][dm-5.1] · [Drive modes §5.8][dm-5.8].
- **Open questions:** the live Drive code draws the SLABS car view in place of the Tiles page
  in any driving state; the spec makes it a Parked-only page. The designs follow the spec.

### drive-dashboard-cluster — Dashboard · Cluster  [Existing]
- **Purpose:** the head-unit default: speed first, engine health around it.
- **Owner:** os
- **Opens from → goes to:** the page "Cluster" (icon `dashboard`); the Dashboard preset
  adds it and "Map" on HU-5, HU-7 and HU-9/10 by default; the next page is Dashboard · Map.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** as above.
- **Content (this page, added by preset `ostler.dashboard`):** **Speed** hero (`Vehicle.Speed`, km/h, arc on
  HU-7, 0–160), **Coolant** bar (warning 105–112 °C, critical ≥ 112 °C), **Boost** bar
  (`MAP`), **Battery** bar (1 decimal), **Engine** bar (rpm, stepped). HU-wide adds **Fuel**
  (`RelativeLevel`, reads "Not available on this car" on the D2).
- **Moving placement:** HU-5 and HU-7 3 × 2: Coolant · Speed hero (tall, centre) · Boost /
  Battery · Engine. HU-9/10 4 × 2 with a 2 × 2 hero centre. HU-wide 6 × 2: Coolant, Boost,
  hero, Battery / Engine (wide), Fuel (wide). Phone 2 × 3: hero speed across / Engine,
  Coolant / Boost, Battery. Five tiles (six on HU-wide).
- **Parked extras the spec allows (not in the preset yet):** g-meter (node IMU), trip
  figures, economy, ride height; draw as a variant on hu7 Night Parked.
- **States:** SLABS session: Coolant, Boost and Engine read "Not in this session · Read by
  Engine (Td5)", speed from GPS labelled "GPS". Critical coolant: tile in `alarm` + "High".
- **Safety and driving rules:** the hero never glows; the rpm bar steps ≤ 4 Hz.
- **Components:** HeroStat, Gauge (240° arc), StatTile (bar style). Tokens `type-hero`,
  `type-num-xl`, `band`.
- **Spec refs:** [Drive modes §5.2][dm-5.2] · [Drive modes §5.9][dm-5.9] ·
  [UI §15.1][ui-15.1].
- **Open questions:** the spec sketches six Moving tiles (with a fourth side gauge); the
  preset ships five on most classes because the D2 has no fuel level. Keep five.

### drive-dashboard-map — Dashboard · Map with speed overlay  [Existing]
- **Purpose:** the Dashboard's second page: the own-car map with speed.
- **Owner:** os
- **Opens from → goes to:** the second page the Dashboard preset adds, next to Cluster.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** as above.
- **Content:** 1. **Map** pane full page (Ostler Night or Day, heading up, the trip's trail,
  cyan puck). 2. **Speed** overlay tile top-left (driver side away from the dock). 3.
  Collapsed attribution control (`info`).
- **Moving:** `map` + 1 tile. `up`/`down` zoom in steps; no panning, no search.
- **States:** no fix: "No GPS fix" over the map; no GPS: "Needs GPS"; offline basemap: `bg`
  with the trail and puck only.
- **Safety and driving rules:** own position and route only ([UI §12.1][ui-12.1]).
- **Components:** map template, StatTile (overlay on `surface-glass`).
- **Spec refs:** [Drive modes §5.2][dm-5.2] · [Drive modes §5.8][dm-5.8] · [visual §7][vds-7].
- **Open questions:** none.

### drive-map-map — Map · Map  [Existing]
- **Purpose:** a full-screen dark map with speed and two stats.
- **Owner:** app:map
- **Opens from → goes to:** the page "Map" (icon `map`); the Map preset adds this one page.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** as above,
  plus hu9 Night-dim Moving with the Navigation next-manoeuvre tile.
- **Content (this page, added by preset `ostler.map`):** **Map** pane; overlays **Speed** (km/h), **Altitude**
  (`CurrentLocation.Altitude`, m, labelled "GPS"), **Heading** (compass, for example "214°
  SW"; "stale" below a crawl). With the Navigation app: a **Next** tile ("Next · 300 m")
  and ETA in place of a stat. With an opted-in convoy: plain markers, no names.
- **Moving placement:** map fills the grid; Speed top-left, Altitude bottom-left, Heading
  bottom-right (HU-9/10 and HU-wide use wider overlay tiles). `map` + 3 tiles.
- **States:** as Dashboard · Map.
- **Safety and driving rules:** no other vehicles except opted-in convoy markers; no free
  panning; next manoeuvre only from the Navigation app ([Drive modes §5.3][dm-5.3]).
- **Components:** map template, StatTile (overlay), compass tile.
- **Spec refs:** [Drive modes §5.3][dm-5.3] · [Navigation §5.2][nav-5.2] · [visual §7][vds-7].
- **Open questions:** none.

### drive-minimal-minimal — Minimal / Night · Minimal  [Existing]
- **Purpose:** a calm screen for night driving: huge speed and one status line.
- **Owner:** os
- **Opens from → goes to:** the page "Minimal" (icon `bedtime`); the Minimal / Night preset
  adds this one page.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim and Deep night Moving; phone Night.
- **Content:** 1. **Speed** hero, centred, at the class's `type-hero` (96 px HU-7, 120 px
  HU-9/10 and HU-wide, 64 px phone) with "km/h". 2. **Status** line (`value`, two values,
  ≤ 30 characters): "Coolant 88 °C · 13.9 V".
- **Moving:** 1 hero + 1 `value` line = 3 tiles' budget.
- **States:** theme hint Night dim: darkens to Night dim when the theme is Auto and it is
  dark; never brightens. SLABS session: line "Coolant — · 13.9 V" with "Not in this session".
- **Safety and driving rules:** as every page.
- **Components:** HeroStat, value line (new component: one line, two values).
- **Spec refs:** [Drive modes §5.7][dm-5.7] · [visual §3.1][vds-3.1].
- **Open questions:** none.

[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-5.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#51-diagnostic-todays-six-tiles
[dm-5.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#52-dashboard-realdash-style-cluster
[dm-5.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#53-map
[dm-5.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#57-minimal--night
[dm-5.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#58-faces-per-preset
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[nav-5.2]: ../../../../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#123-drive-mode-changes-31-35-53-54-10-u1-and-its-test
[ui-15.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#151-drive-modes-changes-123
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
