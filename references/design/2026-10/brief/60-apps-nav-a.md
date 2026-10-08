---
title: "Designer brief — Navigation add-on: turn card, off route, Navigation page, planner, library and roadbook"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-navigation-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-trip-sharing-design.md]
summary: >
  Page content for the six indexed Navigation screens: the turn card drawn in the shell's `map`
  template while Moving (arrow, stepped distance, road name, then-preview, lanes, one ETA value,
  NAV or TRACK badge, the optional speed-limit roundel), the off-route card with its 8-second
  countdown and Reroute focused, the Navigation page (search, destinations, profiles), the
  Parked planner, the GPX library with follow-a-track modes, and the roadbook view. Every
  label, state and driving rule, with components. Search results, the route preview, map
  regions and saved places are in part b. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# Navigation, part a: guidance, library and planner

Example numbers and names in quotes are label formats, not data.

Navigation (`ostler-app-navigation`) routes on the Brain and guides on each display from the
whole route. It needs a Brain and an installed map region. It declares no car actions
([Navigation §1](../../../../specs/2026-10-07-navigation-addon-design.md#1-scope-and-boundaries)). Part b: [60-apps-nav-b.md](60-apps-nav-b.md).

### nav-turn-card — Turn card  [Existing]
- **Owner:** app:navigation
- **Purpose:** the next manoeuvre while driving, inside the shell's `map` template.
- **Opens from → goes to:** starting a route (nav-route-preview "Start") or "Start on head
  unit" from the planner → arrival "You have arrived" → the Drive home page.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  Moving; hu7 Deep night Moving; hu5 Night-dim Moving; phone Night Moving.
- **Content (top to bottom):**
  1. Turn card on `surface-glass`: Material arrow (`turn_left`, `roundabout_right`,
     `fork_right`, `straight`), distance in type-num-xl stepped ("500 m", "350 m", "40 m"),
     road or exit ≤ 30 characters ("A6 Bakewell").
  2. Then-preview (only when the next manoeuvre is ≤ 300 m after): small arrow + "then 120 m".
  3. Lane arrows where tagged (≤ 6 lanes; usable `text-1`, others `text-3`).
  4. Badge `NAV` (routed) or `TRACK` (following a line), icon + word.
  5. ETA value, one at a time: "17:40" or "32 min"; tap or `ok` flips it.
  6. Beside the map: one `tiles` value "Distance to go 24 km".
  7. Optional speed-limit roundel (opt-in): "50"; the speed tile takes the `warn` tint above
     limit + tolerance. No sound, no red.
  8. Map: own puck, route line, priority waypoints on an amber line.
- **States:** loading "Calculating…" · off your maps: Card "Off your maps: install Wales",
  guidance continues on the cached route · Brain unreachable: "Needs the Brain" for reroute,
  guidance continues · Moving: as above · Parked: same card plus the full Navigation page
  behind it.
- **Safety and driving rules:** no search, list, pan or text entry while Moving; no
  animation (glow and gradient are the theme's choice, under the render check); speed-limit state never logged or scored ([Navigation §5.2](../../../../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre), [Navigation §5.5](../../../../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default),
  [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** map template, StatTile (distance to go), Chip (NAV/TRACK), Card.
- **Spec refs:** [Navigation §5.2](../../../../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre) · [Navigation §5.5](../../../../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44) · [UI §13.5](../../../../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence)

### nav-off-route — Off route card  [Existing]
- **Owner:** app:navigation
- **Purpose:** offer a reroute after leaving the route, auto-confirming after 8 s.
- **Opens from → goes to:** off-route detection → Reroute (new route) or Keep route.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  Moving; phone Night Moving.
- **Content (top to bottom):** 1. `alert_card`: icon `alt_route`, line 1 "Off route", line 2
  "Rerouting in 8 s" (seconds as text, 1 Hz, no bar). 2. Buttons **Reroute** (focused) · **Keep
  route**. 3. Failure line once: "No new route, keeping the old one".
- **States:** Moving: as above · Parked: same card · Brain unreachable: "Needs the Brain".
- **Safety and driving rules:** auto-confirm is allowed only because rerouting is not a car
  action ([Navigation §5.3](../../../../specs/2026-10-07-navigation-addon-design.md#53-off-route-and-reroute), [Shell input §7](../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns)).
- **Components:** alert_card, Button.
- **Spec refs:** [Navigation §5.3](../../../../specs/2026-10-07-navigation-addon-design.md#53-off-route-and-reroute) · [Shell input §7](../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns)

### nav-page — Navigation page  [Existing]
- **Owner:** app:navigation
- **Purpose:** search, destinations, profiles and recent places (Parked).
- **Opens from → goes to:** app drawer → Navigation (slot `more:navigation`), a dock pin, the Home
  card "Navigate home" → nav-search, nav-route-preview, nav-library, nav-planner, nav-places.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked (map with side sheet on the passenger side); phone Night and Day.
- **Content (top to bottom):**
  1. Search field "Where to?" (accepts places, addresses, coordinates, Plus Codes, pasted map
     links).
  2. Quick rows: Home, Work (from Settings → Places), saved places, recent destinations (≤ 20,
     "Clear").
  3. Profile Chips: Fast · Scenic · Unpaved friendly · Off-road / 4x4; Avoid Toggles:
     motorways, tolls, ferries, unpaved.
  4. Rows: Library · Planner · Saved places · Map regions.
  5. Card "Check local access rules. Map data may be incomplete."
- **States:** no region: "Install a map region" Card → nav-regions · no Brain: "Needs the
  Brain" · Parked: full · Idling: with Park evidence, else as Moving · Moving: locked view
  "Available when parked" + Open on phone; the turn card is the Moving view.
- **Safety and driving rules:** search and lists Parked only ([Navigation §5.6](../../../../specs/2026-10-07-navigation-addon-design.md#56-drive-menu-rows)).
- **Components:** ListRow, Chip (profile), Toggle, Card.
- **Spec refs:** [Navigation §4](../../../../specs/2026-10-07-navigation-addon-design.md#4-profiles) · [Navigation §6.4](../../../../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois) · [Navigation §3](../../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) · [Navigation §9](../../../../specs/2026-10-07-navigation-addon-design.md#9-manifest-sketch)

### nav-planner — Planner  [Existing]
- **Owner:** app:navigation
- **Purpose:** plan a route or track by stops and anchors, Parked or at a desk.
- **Opens from → goes to:** Navigation → Planner; library "Edit" → Save to library, Start on
  head unit.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** desktop
  Night; tablet Night; hu9 Night Parked.
- **Content (top to bottom):**
  1. Map with stops and anchors; tap or long-press to add (Parked).
  2. Sheet: stops list with drag handles, profile per section, "Snap to road" Toggle.
  3. Tools: Cut, Merge, Reduce points, Route ↔ Track, Undo, Redo.
  4. Route info: distance, ascent, surface split, off-road %.
  5. Buttons "Save to library" and **Start on head unit**.
- **States:** empty: "Tap the map to add a stop" · loading: "Routing…" · error: "No route
  between these points" · Parked: full · Idling: locked · Moving: locked view.
- **Safety and driving rules:** Parked only on driver-facing displays ([Navigation §6.5](../../../../specs/2026-10-07-navigation-addon-design.md#65-planner-parked)).
- **Components:** Sheet over map, ListRow (stops, drag), Button, Toggle.
- **Spec refs:** [Navigation §6.5](../../../../specs/2026-10-07-navigation-addon-design.md#65-planner-parked)

### nav-library — GPX library and follow a track  [Existing]
- **Owner:** app:navigation
- **Purpose:** my plans, imported files, curated routes and Trips recordings, and following one.
- **Opens from → goes to:** Navigation → Library → a file → Follow (turn card in TRACK or NAV)
  or Edit (planner) or Share (hub P8, trips-share-sheet levels for trip-derived routes).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night; desktop Night.
- **Content (top to bottom):**
  1. Folders and tags; virtual folder "My trips".
  2. Rows: name, distance, ascent, surface split, "% ridden", show-on-map Toggle, colour dot.
  3. File detail: Segmented **Turns · Line · Hybrid**, "Start from nearest point", "Reverse".
  4. Buttons: Import (GPX, KML, GeoJSON, TCX), Export GPX, **Export library**.
- **States:** empty: "Import a GPX file or save a plan" · import error: "This file couldn't be
  read" · Parked: full · Idling: with Park evidence · Moving: locked view.
- **Safety and driving rules:** off-track alert > 30 m for 3 fixes as an `alert_card`
  ([Navigation §6.3](../../../../specs/2026-10-07-navigation-addon-design.md#63-follow-a-track)).
- **Components:** ListRow (folders, tags), Segmented (Turns / Line / Hybrid), Button.
- **Spec refs:** [Navigation §6.1](../../../../specs/2026-10-07-navigation-addon-design.md#61-library) · [Navigation §6.2](../../../../specs/2026-10-07-navigation-addon-design.md#62-import-and-export) · [Navigation §6.3](../../../../specs/2026-10-07-navigation-addon-design.md#63-follow-a-track)

### nav-roadbook — Roadbook view (N4)  [Existing]
- **Owner:** app:navigation
- **Purpose:** a rally-style roadbook from a route's manoeuvres.
- **Opens from → goes to:** library file → "Roadbook"; while Moving it renders through
  templates only.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; hu7 Night-dim Moving (CAP and partials as tiles).
- **Content (top to bottom):** 1. Rows: number "12/48", tulip diagram, partial "1.35 km", total
  "18.20 km", CAP "214°", note. 2. Trip-meter nudge Buttons "−0.01 · +0.01". 3. Moving:
  `tiles` CAP 214°, partial 0.42 km; the tulip as the `map` template's next manoeuvre.
- **States:** empty: "Generate from a route" · Parked: full · Moving: templates only.
- **Safety and driving rules:** no dedicated roadbook template without a platform proposal
  ([Navigation §6.6](../../../../specs/2026-10-07-navigation-addon-design.md#66-roadbook-view-n4)).
- **Components:** ListRow (tulip rows), StatTile.
- **Spec refs:** [Navigation §6.6](../../../../specs/2026-10-07-navigation-addon-design.md#66-roadbook-view-n4)
