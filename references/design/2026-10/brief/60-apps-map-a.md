---
title: "Designer brief — Vehicles & Map add-on: live map, vehicles list, garage card, visibility and sharing"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-trip-sharing-design.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md]
summary: >
  Page content for the five indexed Vehicles & Map screens: the full-screen live map with
  other people's vehicles built into it (pins with heading, age ring and source, coarse discs,
  the bottom sheet), the vehicles list (Mine, Shared with me, groups; Hidden for ghosted
  owners), the garage card of a shared vehicle with View as…, the visibility sheet (ghost by
  default; visible for 1 h, 24 h or until I go ghost) and the per-friend, group and field
  sharing sheet with the live-trip options. Gives driving rules (no other vehicles on a head
  unit while Moving except opted-in convoy markers), states and components.
---

# Vehicles & Map, part a: browse other people's vehicles on the live map

Example numbers and names in quotes are label formats, not data.

Vehicles & Map (`ostler-app-vehicles`) is one feature: browsing the vehicles friends and
groups share with you, with the map built into it. It opens on the map; the list is its
bottom sheet ([Vehicles & Map §3](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles)). It stores no permissions: who sees what comes from the OS
registry ([Accounts §14](../../../../specs/2026-10-06-accounts-sharing-design.md#14-amendment-2026-10-07-approved-one-permission-model-and-the-shell-screens)). New screens (convoy, ride ask, card editor, Seen by, relay link) are in
[60-apps-map-b.md](60-apps-map-b.md).

### vehicles-map — Vehicles & Map: live map  [Existing]
- **Owner:** app:map
- **Purpose:** see my vehicles and every vehicle I may see on one full-screen dark map.
- **Opens from → goes to:** app drawer → Vehicles & Map (slot `more:vehicles`), a dock pin, the Home
  "nearby" card → pin tap → half sheet on that vehicle → full sheet vehicles-garage-card;
  visibility chip → vehicles-visibility.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked with the side sheet on the passenger side (left on the RHD
  D2); hu7 Night-dim Moving (own position only, or convoy markers).
- **Content (top to bottom):**
  1. Full-bleed Ostler Night map (Day in Day theme); attribution as a collapsed `info` control.
  2. Floating top-left: visibility chip "Ghost" (neutral) or "Visible to Peak District ride ·
     1 h 20 m left" (accent, live countdown).
  3. Pins (new component **VehiclePin**): silhouette (car, bike, truck, van) in a round badge,
     heading arrow when moving, **age ring** (fresh < 2 min, ageing < 15 min, stale < 1 h, then
     dashed "last seen"); label under pin "Sam's Discovery · updated 4 min ago · via LoRa ±3
     km". Coarse positions draw a soft disc with no pin point; place-name positions snap to
     the place label.
  4. My own vehicle puck (accent, the only live accent on the map).
  5. Bottom sheet: **peek** "3 vehicles visible to you" + my visibility chip; **half** the
     list (vehicles-list); **full** the garage card.
  6. Floating "Locate me" and layer Buttons on `surface-glass`.
- **States:** empty: "No one shares a vehicle with you yet · Invite a friend" · loading: map
  with a spinner chip "Fetching shares…" · error: "Couldn't reach 2 vehicles" chip · offline:
  map uses the `bg` fallback with pucks only; peers marked "Offline since 14:10" · no vehicle:
  shared vehicles still show · Parked: full · Idling: full with Park evidence · Moving (head
  unit): `map` template, own position and route only; with an opted-in ride, plain convoy
  markers (≤ 6) and a leader distance tile · Passenger view: never unlocked; "Open on phone".
- **Safety and driving rules:** other vehicles are non-driving content; never on a
  driver-facing screen while Moving except plain convoy markers ([Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving), [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)); no
  speed traces of other people, no leaderboard ([Vehicles & Map §3](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles)).
- **Components:** Sheet over map, VehiclePin, Chip (visibility, age), Button, map template.
- **Spec refs:** [Vehicles & Map §3](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles) · [Vehicles & Map §6.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#62-routes-and-precision) · [Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving) · [Visual §7](../../../../specs/2026-10-07-visual-design-system-design.md#7-maps) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)
- **Open questions:** should the HU-wide class keep the map in the secondary pane while
  Moving, or only full-screen in a Drive home page?

### vehicles-list — Vehicles list  [Existing]
- **Owner:** app:map
- **Purpose:** the list behind the map: Mine, Shared with me (per person) and per group.
- **Opens from → goes to:** the map sheet at half; a row → vehicles-garage-card; "Share mine"
  → vehicles-share.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night (half sheet); hu7 Night Parked (side sheet).
- **Content (top to bottom):**
  1. Segmented: Mine · Shared with me · Groups.
  2. Rows (ListRow): photo or silhouette, nickname ("Sam's Discovery"), owner name, status
     word (Driving, Parked, Offline since …, **Hidden**), place at the granted precision
     ("Near Bakewell"), age line "updated 4 min ago · via LoRa".
  3. "Hidden" rows show no position at all, never a stale pin as current.
- **States:** empty per tab ("Nothing shared with you yet") · loading: skeleton rows · error:
  per-row "Couldn't reach" · offline: "Offline since …" · Parked: full · Idling: full with Park
  evidence · Moving: not shown on a head unit · Passenger: Open on phone.
- **Safety and driving rules:** list locked while Moving ([Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving)); data held in memory only,
  revocation removes the row on next render ([Vehicles & Map §2.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#21-vehicles-list)).
- **Components:** Segmented, ListRow, Chip (status, age).
- **Spec refs:** [Vehicles & Map §2.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#21-vehicles-list) · [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)

### vehicles-garage-card — Garage card and View as…  [Existing]
- **Owner:** app:map
- **Purpose:** the face of a shared vehicle (owner-curated fields), and my own card previewed
  as a chosen person sees it.
- **Opens from → goes to:** a list row or pin (full sheet); my vehicle's "View as…" →
  picker of contact, group or household → the same card rendered through `/peer/v1`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked; desktop Night.
- **Content (top to bottom):**
  1. Photo (EXIF stripped) or silhouette; nickname; make, model, year ("Land Rover
     Discovery 2 Td5 · 2002"); owner name.
  2. Mods and "about" text; mileage band "150–200k km" (only if granted); plate hidden unless
     ticked; never a VIN, masked or not.
  3. Live stats (≤ 6 StatTiles, only through a `live` grant): e.g. Coolant 88 °C, Turbo
     pressure 1.2 bar, RPM —, with age and "stale" in grey; missing values as "—".
  4. Faults (if granted): "2 faults · Warning" or codes ("P0403 EGR inlet throttle").
  5. Trips (if granted): last trip summary row.
  6. Footer: "Seen by" (my own card only) and "View as…" Button.
- **States:** empty fields hidden · loading · error: "Couldn't reach Sam's Discovery" · offline:
  "Offline since 14:10", stale values grey · Parked: full · Moving: not shown on a head unit.
- **Safety and driving rules:** only granted classes are fetched ([Vehicles & Map §2.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle)); View as… is the
  real server filter, not an imitation ([Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) S8).
- **Components:** Card, StatTile (≤ 6), ListRow, Chip, Button.
- **Spec refs:** [Vehicles & Map §2.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle) · [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [ADR-0036](../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md)

### vehicles-visibility — Visibility sheet  [Existing]
- **Owner:** app:map
- **Purpose:** go ghost in one tap, or become visible for a chosen time.
- **Opens from → goes to:** the visibility chip (strip, map, Social header) → share-visible-summary
  (before turning visible) → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving (go ghost only); phone Night; hu7 Night Parked.
- **Content (top to bottom):**
  1. State line: "You are a ghost: no one sees your presence, location or live values." or
     "Visible to Peak District ride · 1 h 20 m left".
  2. When visible: one big Button **Go ghost**.
  3. When ghost: "Become visible for" Segmented **1 h · 24 h · Until I go ghost**, then
     "See what each audience will see" (share-visible-summary), then **Become visible**.
  4. Caption: "Ghost never ends by itself. Messaging and calls still work."
- **States:** loading · error: "Not saved · Retry" · Parked: full · Moving (driver-facing):
  only **Go ghost** is offered; becoming visible says "Park, or use your phone".
- **Safety and driving rules:** timers move only toward ghost; going ghost is always one tap
  ([Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode), [Vehicles & Map §4](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#4-ghost-mode-and-the-visibility-sheet)).
- **Components:** Sheet, Segmented, Button, Chip.
- **Spec refs:** [Vehicles & Map §4](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#4-ghost-mode-and-the-visibility-sheet) · [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode) · [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs)

### vehicles-share — Per-friend, group and field sharing  [Existing]
- **Owner:** app:map
- **Purpose:** edit what one person or group may see of my vehicle, and the live-trip options.
- **Opens from → goes to:** vehicles-list "Share mine"; trips-share-sheet "Share live" (a trip
  still recording) → accounts-s8 for the full matrix.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):**
  1. Audience row: "Sam" / "Peak 4x4 club" / "This ride" (share-audience-picker).
  2. Class rows with a detail picker each: Presence (on/off) · Location (None · Coarse ±3 km ·
     Place · Precise · Live; Precise and Live say "ends within 24 h") · Vehicle card (Basic ·
     With plate) · Live values (pick up to 6 signals, e.g. Coolant, Turbo pressure, Battery)
     · Trips (Summary · Full) · Faults (On).
  3. Duration first: "1 h · End of trip · End of day · Until I stop" (where allowed).
  4. **Share live options** (live location only): Trail window (None, 1, 3, 6, 12, 24 h, Whole
     trip); Delay (0–6 h); Show speed (off); Show values (off).
  5. Button "Save"; caption "Ghost still hides live classes."
- **States:** loading · error · Parked: full · Idling: with Park evidence, else as Moving ·
  Moving: locked view "Available when parked" + Open on phone.
- **Safety and driving rules:** precise and live always end within 24 h; nobody can raise my
  precision ([Accounts §14.5](../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it)); enforcement is at the source ([Vehicles & Map §5](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#5-per-friend-group-and-field-sharing)).
- **Components:** Sheet, ListRow, Segmented (trail window, delay), Toggle (show speed, show
  values), Button.
- **Spec refs:** [Vehicles & Map §5](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#5-per-friend-group-and-field-sharing) · [Accounts §15.3](../../../../specs/2026-10-06-accounts-sharing-design.md#153-live-trip-grant-options-changes-142-used-by-vehicles--map) · [Trip sharing §12](../../../../specs/2026-10-07-trip-sharing-design.md#12-live-trips)
