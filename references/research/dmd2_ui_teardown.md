---
title: "DMD2 UI teardown: screen by screen, remote-control model, and what Ostler should borrow"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, references/research/ui/head_unit_ui.md, references/research/driver_distraction_rules.md, references/research/app_teardown_speedometer.md, references/research/addons_catalogue.md, ui/src/screens/Drive.tsx, ui/src/shell/Shell.tsx, ui/src/shell/Nav.tsx, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md]
summary: >
  A screen-by-screen UI teardown of DMD2, the Android moto and 4x4 navigation dashboard (docs,
  site renders and 22 documentation screenshots, checked 2026-10-07). It covers the shell
  (status bar, three-part bottom menu, speedo), the two Home row grids and the full-screen
  cluster, map overlay cards and their placement mode, the turn card, the GPX recorder, the
  roadbook, Devices cards, settings and profiles, night themes, target sizes and the T865X
  hardware. Its core lesson is the remote-control model: every screen is driveable from a
  joystick, two buttons and a zoom rocker, through focus zones, a long-press "menu focus" and a
  long-press action menu. Each item is compared with Ostler's Drive mode, layouts as data (UI
  spec §12.3), templates (§12.1), Trips (§12.2) and the visual spec, and the note proposes a
  D-pad input model for the shell, then Copy, Avoid and Decide.
---

# DMD2 UI teardown, mapped onto Ostler

DMD2 ("Drive Mode Dashboard 2", Thork Racing, Portugal) is an Android navigation dashboard for
adventure motorcycles and 4x4s. It runs on phones and as the launcher of DMD's own rugged tablets
(T665, T865, T865X). This note is the UI half of the DMD research: how each screen is built and
driven, and what Ostler's shell should take from it. Feature lists, the Hub and sharing are in the
sibling notes of this research round. Captures are in the scratchpad, not the repo; colours and
sizes below were read off 1280 × 800 documentation screenshots by eye and are approximate.

**Ostler today** (read 2026-10-07): `ui/src/screens/Drive.tsx` renders the pack layout's
`layout.drive` view as a flat `StatTile` grid, or a pack-registered view, with no heading in Drive
mode (§12.3 already applied). `ui/src/shell/` has layout classes (HU-5 to desktop), the strip,
a five-destination rail or bar and Drive mode as an overlay. Input is touch and mouse only: the
only keyboard handling is `Escape` on sheets and the glossary, a scrubber, and inline edit; there
is no focus model, no spatial navigation, no remote or steering-wheel input, and the focus ring is
the browser default `:focus-visible` (2 px, `--ic-blue`).

## 1. The shell: three bands

| Band | DMD2 | Ostler equivalent | Gap or lesson |
|---|---|---|---|
| **Top status bar** (~45 px at 1280 × 800) | Device battery %, **GPS precision in metres** (green good, orange fair, red poor, a grey crosshair and "---" with no fix), weather and temperature, Online (cloud icon), clock. Read-only, evenly spaced | Strip §3.2: vehicle, worst telltale, link, REC, security, device slot, 12 V, clock, Mark; chips open sheets | Ostler's strip is richer and actionable. DMD's GPS-accuracy readout is worth one idea: show fix quality where speed comes from GPS (the Td5 in a SLABS session, §3.5) |
| **Bottom menu, section 1** | Four section buttons: Home, Map, Devices, Roadbook; Map cannot be hidden, the others can. Active = cyan underline (landscape) or a raised dome (portrait). Home carries a red count badge (notifications) | Rail §3.3 (driver's side) with five destinations plus Drive on head units | Bottom placement costs height on a 600 px screen (we chose the rail, rightly). Copy hiding unused sections only as "an area with no items disappears", which we already have |
| **Bottom menu, section 2: the speedo** | A fixed centre slot (30/40/30): speed-limit roundel, big speed digits that turn **orange within 10 km/h of the limit and red above it**, then an alert zone (speed cameras, waypoint proximity, off-track, TPMS). Per section it can show speed, trip distance, altitude, bearing, rpm, coolant or TPMS instead. **Tap opens the Trip view** | None in the shell; speed lives in Drive tiles | A strip "value slot" is tempting; see Decide 4 |
| **Bottom menu, section 3** | Context buttons for the active section (Map: quick actions, search, GPX, an assignable shortcut; Roadbook: tracks, files, settings, theme) plus the **Quick Menu** (chevron): rider profile, Settings, Keep Background, Shutdown | More destination and sheets | DMD mixes context actions into the nav bar. Ostler keeps context actions in the page; do not copy |
| **Content** | Up to three equal panels landscape, two portrait; settings "cascade" open to the right of the panel that owns them | HU-wide panes; HU-9/10 list + detail | Same idea; our classes are authored per size |

Recording state shows as a **dot on a bottom-menu button** (red recording, yellow paused): the
equivalent of our REC chip.

## 2. Screen by screen

| Screen | What it shows and how it works | Ostler comparison | Ostler home |
|---|---|---|---|
| **Home 1 / Home 2** (row grid) | Two layouts, each **three stacked rows** chosen from 16 row types (app shortcuts, favourite locations, media, "useful indicators", GPS dashboard with compass and pitch/roll, trip info, odometer with Trip A/B, profile switcher, OBD2 sensors, TPMS, Power Box, fuel range, action cameras, last notifications, weather, speedometer). Rows are full-width cards with a tinted gradient each; a map fills the rest. One tap or remote up/down swaps Home 1 and 2 | Home §5.4 is built from roles, not user rows; Drive mode is the glanceable view | Core shell (Home cards); row types map to role tiles and device cards |
| **Home/Map dividers** | A main divider snaps the Home panel to 1, 2 or 3 rows' width, with the map taking the rest; a second "strip" divider overlays 0 to 3 rows of the *other* Home above the map. Dividers fade to a short grey bar after ~10 s | §12.3 allows an optional `map` pane on HU-9/10 and HU-wide, fixed by the layout | Core Drive layout: a `split` with snap positions (Copy 5) |
| **Full-screen minimal** | A car-cluster view: a big speed ring in the centre (neutral grey arc, white digits, "KM/H" caption), Trip card left (distance, riding, total), Weather right, Altitude and Heading below, "Exit full screen" pill. Device cards balance themselves on both sides of the ring; in landscape a corner button swaps the ring for the map | This *is* Ostler Drive mode, almost exactly: calm neutral arc, one hero, labelled tiles, no glow | Core Drive mode. Copy the auto-balance (§4) |
| **Map** | Full map with floating dark rounded cards: follow button (bearing-up, 3D, north-up; panning drops to Free), group button with "0/2", trip distance, altitude, "next POI along track" card (fuel: 634 m then 930 m, View All, Along track), zoom ±, scale bar, road-surface pill ("Track · Grade 2 · Dirt"), record/pause/note buttons, online-layers button with a badge | §12.3 map-first; `map` template while Moving: own position, route, next manoeuvre; no free panning | Navigation is a new add-on (Decide 1); overlays are tiles over the map pane |
| **Overlay placement mode** | Map Settings → Position Elements: a bottom banner "Indicator Placement Mode · tap an indicator for its options · drag to reposition" with **Auto Arrange** and **Done**. Positions are saved **per orientation** and **per device, not synced** with the profile ("a phone layout does not fit a dashboard unit"). A master "Hide all map overlays" switch | Our layouts are authored per layout class and edited as a per-vehicle diff, Parked only, grid not pixels | Core Drive layout editor (Copy 4) |
| **Turn card** | Top-right: a **dark-red** manoeuvre box (white arrow in a dark disc, "Turn left", 153 m in large digits), "then ↗ 153 m", optional **lane arrows**, route name with Options, a thin progress line, a NAV/GPX badge, distance to end and ETA (tap toggles ETA and time left), then next via point and next waypoint with distance and time | The `map` template allows "next manoeuvre" but nobody draws it yet | New `ostler-app-navigation` |
| **Off-route dialog** | Three choices (rejoin the line ahead, skip to next point, do not reroute) with a **countdown bar that auto-confirms** the highlighted option after 5–30 s | Nothing yet | Navigation add-on; the auto-confirm pattern is fine for routing, never for car actions (Avoid 3) |
| **Trip view** (tap the speedo) | Distance, travel time, stopped time, average speed for the current trip; Trip A/B in the odometer row | Trips §12.2 has the full model; Drive has no trip tiles | Core Trips: a `trip.current` summary as Drive tile signals (Copy 9) |
| **GPX recorder** | Left panel: a red "● RECORDING" title, a 2-column stat grid (travel time, stop time, distance, average and max speed, tracks, waypoints), four large coloured buttons: **PAUSE** (orange), **FINISH** (green), **NEW TRACK** and **ADD WAYPOINT** (cyan); My Recordings below; map right. Auto-record starts on movement with an "ignore if distance below" threshold; the save dialog asks vehicle type, difficulty and off-road % (all optional) | Trips: recording is automatic and always on; **End trip now** and Mark; no pause (ADR-0011) | Core Trips. Copy the short-trip threshold and optional ride tags (Copy 9, 10); Avoid pause |
| **Roadbook** | Left: TOTAL (big), **CAP to follow** (big cyan arrow, 216°, heading 34°), waypoint 8/442, hazard and speed-limit cells. Right: a paper roll of tulips in rows: big partial distance, pink delta, row number, tulip drawing, yellow cap; the current row has a green tint. Remote: scroll the roll, nudge total/partial up or down, reset, invert paper (night), play/pause odo, mini-map. Chrono: tap start/stop, hold to reset | Nothing; FIA/OpenRally roadbooks are for rally-raid and navigation events | Not needed now; a later phase of the navigation add-on if the owner wants overland events |
| **Devices** | Live cards: OBD2 (rpm bar segmented blue → amber → red, three **tap-to-reassign** gauge cells, a red check-engine button that opens read/clear DTCs), fuel simulator (range bar, reset), Power Box (six ON/OFF switch tiles, ON = cyan fill), cameras, TPMS. Order set with up/down arrows in the bar | Home device cards (§6) and Diagnose; our D2 has far more than an ELM327 dongle | Core Home cards; outputs only through the gate (ADR-0033) |
| **Remote menu** | Long-press button 2 opens a right-hand panel: a vertical **family rail** of colour-coded icons with item counts (Navigation orange, Safety red, Save magenta, Map cyan, Media violet, System grey, Devices green, Trip teal), and a list grouped under coloured headers; each row is icon, label and state ("On", "Off", "Idle"). The **focused row is filled cyan with a 3 px white ring** and enlarged. Up/down moves rows and wraps; left/right jumps families; button 1 confirms; zoom also moves. By touch, the first tap previews and the second confirms | Nothing | Core shell: the Drive menu (§5, Decide 2) |
| **Remote menu settings** | Same panel: "Select · Confirm turns on/off · Left/Right reorders"; families as coloured headed bars with ▲ ▼ and an ON pill; items indented under them; saved per profile | — | Core shell, Parked only |
| **Remote controller settings** | Tabs: Global (long press only), Menus/Dialogs/Apps, Home view, Map view, Roadbook view, Advanced. Each row binds a function ("Previous left widget", "Next right widget", "Enter / select widget", "Cancel / unselect", "Map zoom in") to an **Android key code** (21, 22, 20, 19, 66, 111, 136: the D-pad, Enter, Escape and a function key). A **"Test remote keys"** game ticks each key until "ALL KEYS OK" | Nothing | Core shell input bindings; the key test on the device page (§3.7) |
| **Quick menu** | A centred dark modal over a dimmed map: rider-profile avatar, Settings, Keep Background, Shutdown (orange power icon) | More, About | Not needed |
| **Global settings** | Theme (Light, Dark, Auto system, **Auto light sensor**), display scale, font, orientation lock, units per quantity, voice and media volumes, background activities, per-app notification filter, visible sections, "Menu speedo" content per section | More → Preferences; units already per quantity | Core Preferences |
| **Rider profiles** | Up to six (Enduro, Adventure, Rally, 4x4, SSV, Touring), each with Home layouts, devices, map settings, quick actions, track styles, settings, odometers; synced to the Hub except overlay positions | Garage per vehicle; per-vehicle layout diff | Core Garage; Avoid a second "profile" concept |

## 3. Layout editing and widget configuration, against §12.3

DMD2 has **three different editors**, one per surface: Home row slots (accordion per slot, pick a
row type, "duplicate picks swap"), map overlay placement (free drag, per orientation, Auto
Arrange), and OBD/device gauge cells (tap a cell, pick a sensor). The Home editor is the best of
them: each slot is an accordion; each choice is a list row with an icon, a bold name, a one-line
grey description ("Compass, heading, pitch/roll sensors") and a check on the current choice
(selected row filled `#0b5a80`-ish blue). Picking a row type that is already used elsewhere
**swaps** the two, so a layout is never invalid and needs no "remove" step.

Ostler's §12.3 is already the stronger model (one file, a grid per layout class, signal bindings
with normal/warning/critical bands, Parked-only editing, a per-vehicle diff, ≤ 6 tiles while
Moving). What it lacks, and DMD has: **slot-first editing** (pick a slot, then pick from a
described list, with swap on duplicate), **auto-arrange** as the escape hatch (for us: "reset to
the role default"), **overlays on the map pane** as a first-class region, and **a second layout
one press away** (Home 1/2). Do not copy free pixel drag: §12.3 rejected a pixel editor, and DMD's
own docs concede that dragged positions do not travel between devices. Per-class grids solve that
by construction.

## 4. Drive mode against DMD's cluster view

| Point | DMD full-screen minimal | Ostler Drive (`Drive.tsx`, §12.3) | Take |
|---|---|---|---|
| Hero | One ring, speed | No hero; equal tiles | Allow a **hero tile** (1 of the ≤ 6) spanning two cells, `type-hero`; the default from roles is speed when known, else rpm |
| Balance | Cards distributed left and right of the ring automatically | Flat grid in pack order | Role-ordered auto-placement around the hero, tested per class |
| Map | Corner button swaps ring and map (landscape) | Optional `map` pane by layout | A Drive layout may name two **faces** (tiles, map) switched by one press or D-pad left/right; both are Moving templates |
| Exit | "Exit full screen" pill in content | Back chip in the strip | Ours is better (no content chrome) |
| Neutral ring | Grey track, white digits | Calm gauges, neutral arcs (visual spec §1.4) | Same rule, confirmed |

## 5. The remote-control model, and a D-pad model for Ostler's shell

**How DMD2 does it** (docs "remote controller", "remote menu", Remote 2/4 manuals, FAQ, checked
2026-10-07):

1. **Hardware**: Remote 1–4 and the BMW Sync Box (DMD's own; Remote 4 straps to a 4x4 steering
   wheel): a 360° joystick (multi-sensitivity on cable), **Button A** (follow toggle, or confirm in
   a menu), **Button B** (online layer, or cancel), a two-way rocker (zoom). Generic HID remotes and
   keyboards also work, with bindings to key codes.
2. **Bindings are per context**: a Global set (press or long-press only, **never key repeat**:
   "menu focus" and "cancel/back/close"), a Menus/Dialogs set (up, down, left, right, confirm), and
   one set per base view (Home: previous/next left widget, previous/next right widget, select,
   unselect; Map: pan, zoom, follow, layer, quick save location; Roadbook: roll, nudge, reset).
3. **Focus is layered**: base view → overlay (menu or dialog) takes the keys while open → a
   long-press moves focus to the **bottom menu**, where left/right walks sections and back returns.
4. **Repeat only where harmless**: pan, zoom and roll repeat; confirm and global keys do not. An
   option makes **panning require a long press**, and panning shows a **centre target** so
   "navigate here" and "save" act on it. Remote use suspends auto-zoom.
5. **The remote menu** (long-press button 2) is the one place every at-speed action lives, in
   colour families, reorderable and switchable per profile; **double-tap any button** binds one menu
   action directly. Generic remotes get no menu (no long-press cancel to hang it on) and a
   long-press touch lock instead.
6. **Touch and remote share selection**: in the menu a first tap selects (shows the focus ring), a
   second confirms; so the same visual state serves both inputs.
7. **A key-test game** proves every binding before a ride.

**Proposal: `ShellInput`, a D-pad input model for the shell** (core platform, a UI-spec
amendment; small, no new dependency):

- **Intents, not keys.** The shell defines eight intents: `up`, `down`, `left`, `right`, `ok`,
  `back`, `menu` (long-press `back` or a dedicated key) and `mark`; plus optional `zoom_in`,
  `zoom_out`, `ptt`. Sources map to intents: the keyboard (arrows, Enter, Escape, `+`/`-`, `M`),
  HID remotes (they arrive as the same key events in the browser, as DMD's key codes 19–22, 66 and
  111 show), the Gamepad API where present, and **device input events** from the node: a pack's
  steering-wheel buttons (the BMW `mfl` `SteeringWheelButton` metric, vehicle-packs spec §3.5),
  the "Dash buttons and keypads" add-on (catalogue) or a handlebar remote. Input events are
  read-only events, not car actions (ADR-0033); an intent can only do what a tap could.
- **Focus zones.** `strip`, `rail`, `main` and `sheet`; a sheet or dialog traps focus until `back`.
  Inside a zone, arrows move to the **nearest focusable in that direction** (geometric spatial
  navigation over `[data-focus]` elements, as TV platforms do); leaving the zone's edge moves to the
  neighbouring zone. `menu` jumps to the rail (DMD's "bottom menu focus"); `back` closes a sheet,
  then leaves a zone, then goes up one route level, and never exits Drive mode while Moving.
- **Drive mode.** With no actionable tiles, Drive mode is mostly not focusable: `left`/`right`
  switch layout faces (tiles, map), `up`/`down` zoom the map face, `ok` opens the **Drive menu**,
  `mark` marks. Unbound keys do nothing; nothing scrolls.
- **The Drive menu** is DMD's remote menu cut to our templates: a `short_list` of ≤ 6 rows, one
  level, ≤ 30 characters each, only driver-safe items (Mark, mute alerts, climate setpoint, media
  play/pause/skip, Security arming, Back to Drive), with the rail of families only when Parked
  (Decide 2). Rows show state on the right ("On", "Armed"), as DMD does.
- **Repeat and long-press rules.** Repeat only for `up`/`down`/`left`/`right` in lists, scrubbers
  and the map; `ok`, `back`, `menu` and `mark` never repeat. Long press = 600 ms. Every action that
  reaches the gate keeps its confirm sheet; the confirm button is **not** pre-focused for Tier 1+
  actions (Cancel is), so a double press cannot approve. No countdown auto-confirm for car actions.
- **Focus visuals** (visual spec §5, new tokens): `focus-ring` 3 px `accent` outside the element
  plus `accent-soft` fill, 2 px `bg` gap so it reads on any surface; on head units 4 px. Focus is
  shown only after a non-pointer intent (`:focus-visible`) and never uses glow, so it is legal while
  Moving. The focused item never changes size (DMD enlarges it; on a 600 px screen that reflows).
- **Bindings UI** (More → Network → the input device's page, §3.7): a table of intent → key with
  "press the key now" capture, per display, not synced (DMD's overlay lesson), Parked only, and a
  **Test buttons** check that ticks each intent. Defaults need no setup: arrows, Enter, Escape.
- **Where it lives**: `ui/src/shell/input.ts` (intent mapping, long-press, repeat), a `useFocusZone`
  hook, `data-focus` on kit components (Button, ListRow, Segmented, chips, rail items), and an
  `input` event on the existing WebSocket for node-sourced buttons.
- **Tests**: Playwright drives every destination and Drive mode by keyboard only at each layout
  class; asserts focus is always visible and never lost (`document.activeElement` inside a zone),
  no trap outside sheets, `back` always reaches Home or Drive in ≤ 3 presses, Tier 1+ confirm sheets
  open with Cancel focused, and keys do nothing in Drive mode beyond the listed intents. This also
  closes most of WCAG 2.1.1 (keyboard) for desktop users at no extra cost.

## 6. Night and day, colour

DMD2: app theme Light, Dark, Auto (system) or **Auto (light sensor)**, which also darkens in
tunnels; the map has its **own theme** (follow app, light, dark, light-sensor) plus a **High
contrast** toggle for glare; the roadbook has its own day/night (invert paper). Notably, every
documentation screenshot shows **dark chrome over a light map**: in daylight, glare beats
consistency. Status colours are loud (red turn card, saturated orange and red GPS readouts).

Ostler (visual spec §1, §3.1, §7): Night by default, Night dim on head units after dusk, Deep
night (OLED), Day; Auto by sun or headlights on head units; Ostler Night and Day map styles.
Take two things: a **light-sensor input** for Auto where the head unit or a sensor pod has one
(tunnels, multi-storey car parks), with hysteresis so it does not flicker; and a **map theme that
may differ from the app theme** with a high-contrast Day map for direct sun (Decide 3). Keep our
calm status use; DMD's red turn card is navigation emphasis, not a status, and we would draw the
manoeuvre in `text-1` on `surface-glass` with the arrow large.

## 7. Glove-friendly targets and the hardware

Measured on 1280 × 800 screenshots of the 8" T865 (≈ 189 ppi, so 1 px ≈ 0.13 mm): bottom-menu
buttons ~72 px (≈ 9.7 mm), remote-menu rows ~58 px (≈ 7.8 mm) with 8 px gaps, recorder buttons
~184 × 62 px (≈ 8.3 mm tall), zoom buttons ~70 × 60 px. There is **no glove mode**: DMD's answer to
gloves is the remote, plus a **touch lock** for rain (a hardware button or a long-press disables
touch so drops do not press). Ostler's 76 px head-unit target (≈ 11 mm on a 7" 1024 × 600) is
already larger; keep it. Take the touch lock for any display that can be wet or used with gloves
(motorcycles, open 4x4s): a strip chip that disables touch, with the D-pad still live (Copy 7).

**Hardware UI** (T865/T865X manual): 8" 1280 × 800 (our HU-9/10 class), 1300 nits on the X,
IP67, −20 to 60 °C; three programmable buttons P1–P3 plus volume and power; DMD2 can be the
Android launcher; **Auto Off** on power loss, inactivity or a trigger wire; actions on cradle insert
and removal. The device UI is the app UI; the extras are buttons and power. For Ostler: power and
wake belong to ADR-0040 (the node switches the display); P-buttons are just more intent sources;
"launcher" is the kiosk flag on a head unit. Not needed: our own tablet.

## 8. Tracks, routes, guidance and stats against Trips

| DMD2 | Ostler | Home |
|---|---|---|
| GPX manager: many files, show/hide/invert each, colour, width, opacity, arrows, "route repair" | Trips shows our own recordings; no imported tracks | Navigation add-on (import, follow); Vehicles & Map for shared routes |
| Recorder live stats (travel/stop time, distance, average, max, elevation, tracks, waypoints) | Trip detail stats grid (§12.2) after the fact; nothing live | Core Trips: a live "Recording now" card already planned; expose its figures as signals for Drive tiles |
| Pause / Finish / New track / Add waypoint | No pause; End trip now; Mark | Core Trips, as decided |
| Save dialog: vehicle type, difficulty, off-road % | Notes; no tags | Social add-on when a trip is shared to a hub (discovery metadata); core keeps a free note |
| Auto-record on movement, ignore below a distance | Trips start on a trigger | Core Trips: drop or merge trips below a minimum distance (U: check the recorder's current rule) |
| Turn card, lanes, then-preview, ETA toggle, off-route choices, voice | `map` template allows next manoeuvre | New `ostler-app-navigation` (routing engine, guidance, GPX follow, voice) |
| Next POI along track (fuel 634 m) | — | Navigation add-on |
| Roadbook, CAP, chrono | — | Not needed now |

## 9. Styling

- **Palette**: near-black navy chrome (status and bottom bars, panels ~`#12141c`–`#1c1f2b`),
  dark-grey rounded overlay cards (~`#2a2d38`, radius ~12 px, no border), one **cyan accent**
  (~`#00b4f0`) for active tab underline, selection fill, links ("View All", "OPTIONS") and ON
  switches; status in saturated orange, red and green; colour-coded families (orange, red,
  magenta, cyan, violet, grey, green, teal). Light, busy OSM-style topo map by default.
- **Type**: a wide, squared display face for numbers and labels (Good-Times-like, all caps in
  buttons) with a plain sans for captions in newer screens (the cluster view); big numerals with a
  small unit; tabular figures in recorder stats.
- **Shape**: rounded rectangles everywhere, pill buttons, round map buttons (follow, group,
  layers); subtle gradients per Home row; no hairlines; dim scrim behind modals.
- **Density**: high; up to seven cards over the map at once. The newer cluster view is calmer and
  much closer to our visual spec.
- **Versus Ostler**: same dark-first, one-accent, rounded, no-border direction (visual spec §1).
  We differ on purpose in: accent never on values or status, no per-row gradients, no glow while
  Moving, map dark by default, and far fewer overlays while Moving.

## 10. Feature → Ostler home (UI features)

| Feature | Home | Why |
|---|---|---|
| D-pad/remote input, focus zones, Drive menu, bindings, key test | **Core shell** (platform) | Every app must be driveable; templates are shell-owned |
| Steering-wheel buttons as input | Core shell + vehicle packs | Pack maps metrics to intents (bmw spec §3.5) |
| Handlebar/dash remotes, keypads | "Dash buttons and keypads" add-on (catalogue) | Hardware add-on emitting input events |
| Slot editor with swap, auto-arrange, map overlays, faces, split | **Core Drive layout** (§12.3) | Layouts are core data |
| Hero tile and auto-balance | Core Drive | Glanceability |
| Trip A/B counters, live trip figures as tiles | Core Trips | Data already recorded |
| Light-sensor Auto theme; map theme and high-contrast map | Core shell + visual tokens | Theme is shell-owned |
| Touch lock | Core shell | Safety on wet or gloved displays |
| GPS precision readout | Core shell (strip, conditional) | Data honesty on GPS speed |
| Turn-by-turn, GPX follow, off-route, POI along route, speed-limit sign | **New `ostler-app-navigation`** | Large, optional, routing data and voice |
| Roadbook | Not needed now (later navigation phase) | Rally niche |
| Ride tags (difficulty, off-road %) | Social add-on | Discovery metadata on shared trips |
| Notifications mirroring, app shortcuts, launcher | Not needed | Phone and OS duties; distraction risk |
| Rider profiles | Not needed (garage per vehicle) | Avoid two concepts |

## 11. Copy / Avoid / Decide for Ostler

**Copy**
1. **A D-pad input model in the shell** (§5): intents, focus zones, long-press `menu` to the rail,
   repeat only for movement, Cancel pre-focused on gated confirms. A UI-spec amendment (§3, new
   §3.9), core; it also gives keyboard accessibility on desktop.
2. **The Drive menu**: one long press opens a `short_list` of driver-safe actions with state on the
   right; families and reorder only when Parked; per display.
3. **Input bindings with a key test** on the device page (§3.7), per display, not synced.
4. **Slot-first layout editing with swap on duplicate**, a described list per slot, and "Reset to
   role default" as auto-arrange (§12.3, Parked only).
5. **Faces and a split in Drive layouts**: tiles and map faces switched by one press; a snap split
   (1/2/3 columns) on HU-9/10 and HU-wide; map overlays as tiles counted in the ≤ 6 budget.
6. **A hero tile** and role-ordered auto-balance around it, as in DMD's cluster view.
7. **Touch lock** chip on head units, D-pad still live.
8. **Light-sensor Auto** with hysteresis where a sensor exists (visual spec §1.1).
9. **Live trip figures and Trip A/B** as signals for Drive tiles, from core Trips.
10. **A minimum-distance rule** so GPS drift does not create trips (core Trips, ADR-0011 spirit).

**Avoid**
1. **Free pixel drag** of overlays: positions do not travel between screens (DMD admits it);
   per-class grids do.
2. **Context actions inside the nav bar** (DMD section 3): the rail holds only destinations (§3.3).
3. **Countdown auto-confirm** for anything that reaches the gate; fine only for routing choices.
4. **A large, many-family menu while Moving**: DMD's eight families of many rows break our
   `short_list` (≤ 6, one level) and ≤ 3-screen rules (§12.1).
5. **Enlarging the focused item** (reflow on small screens) and colour-only focus.
6. **Notification and message preview mirroring** on a driver-facing display (DMD mirrors call and
   message previews; §12.1 forbids message content while Moving).
7. **Pause recording** (ADR-0011; End trip now and Exclude cover it).
8. **Feature-gating basic input on paid tiers** (DMD charges for generic remotes): input is core
   and free.

**Decide** (each with a recommendation)
1. **Navigation as an add-on?** DMD's centre is turn-by-turn and GPX following; Ostler has none.
   *Recommend:* yes, a new `ostler-app-navigation` add-on (routing engine on the Brain, offline
   tiles from the visual spec, guidance through the `map` template's "next manoeuvre"), after U2;
   core keeps only the template slot.
2. **Drive menu scope while Moving.** *Recommend:* one level, ≤ 6 rows, fixed driver-safe
   actions (Mark, mute alerts, climate setpoint, media, arming, Back to Drive); families,
   reordering and other actions Parked only. Not chosen: DMD's full family rail at speed.
3. **Map theme independent of app theme, with a high-contrast Day map?** *Recommend:* yes, a
   "Map: follow app / Day / Night / High contrast" setting, default follow app; the high-contrast
   Day style generated from `map.tokens.json` like the others (visual spec §7).
4. **A strip value slot** (DMD's speedo: speed or rpm in the shell while browsing).
   *Recommend:* no for v1; Drive mode is one press away and HU-wide has the vehicle pane; revisit
   if Parked browsing with the engine running proves common.
5. **Live speed-limit sign and over-limit tint** (DMD turns speed orange then red).
   *Recommend:* only in the navigation add-on, sign plus a `warn` tint on the speed tile, never
   logged or scored (Trips "no score", §12.2); off by default.
6. **Who owns input bindings: display or user?** *Recommend:* the display (install config), since
   remotes are physical; a signed-in user's preference never changes a driver-facing display's
   bindings while Moving.
7. **Ship the D-pad model in U2 or later?** *Recommend:* U2, alongside lockouts: the Drive menu
   and keyboard tests are cheap, and a head unit without touch-safe input is the gap DMD shows us.

## Sources (all checked 2026-10-07)

- Product page: https://www.dmdnavigation.com/dmd2-app/ and its renders (`/assets/images/dmd2app/`).
- Docs (DMD2 "next"): https://docs.dmdnavigation.com/dmdnext/ and its pages `app-structure`,
  `home`, `map`, `map-settings`, `map-navigation`, `map-gpx-recording`, `roadbook`, `devices`,
  `remote-menu`, `global-settings`; screenshots under `/assets/img/dmdnext/`.
- Remote controller: https://docs.dmdnavigation.com/documentation/remote-controller/ (settings and
  key-code screenshots); Remote 2 and Remote 4 manuals under
  https://docs.dmdnavigation.com/devicemanuals/; third-party remote FAQ under
  https://docs.dmdnavigation.com/faq/.
- Hardware: https://docs.dmdnavigation.com/devicemanuals/T865/; T865X 1300 nits and T665 800 nits
  from DMD and reseller listings (search, 2026-10-07).
- YouTube (titles and descriptions only): DMD2 Tutorial #1 and #2 (home, status bar, remote),
  "DMD School lesson 2", BarButtons and SilverFox C2 mapping videos.
- Not verified (U): Play Store figures (the listing did not load); the exact display typeface;
  colours and sizes (read by eye from screenshots).
