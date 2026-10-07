---
title: "Designer brief — Vehicles & Map add-on: convoy layer, ride ask, card editor, Seen by and relay link"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md]
summary: >
  Page content for the Vehicles & Map screens that the approved spec describes but the index
  does not yet hold: the convoy layer of an active ride (Parked map with leader and sweep
  badges, and the head-unit Moving render with plain markers only), the ask-at-start sheet
  "Share live position with this ride until it ends?", the editor for my own garage card
  (curated fields, photo metadata stripping, per-audience ticks), the "Seen by" audit of my
  shares, and the later relay link for viewers without Ostler (at most 24 h). Each block gives
  content, states, driving rules and components.
---

# Vehicles & Map, part b: convoys, asking, editing and audit

Example numbers and names in quotes are label formats, not data.

Part a: [60-apps-map-a.md](60-apps-map-a.md).

### vehicles-convoy — Convoy layer (ride map)  [New]
- **Owner:** app:map
- **Purpose:** during an active ride, show members, leader, sweep and the meeting point.
- **Opens from → goes to:** social-rides "Open map"; vehicles-map when a ride is live; the
  Convoy / Ride Drive home page (Moving).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  Moving (plain markers, leader tile); hu7 Night Parked; phone Night.
- **Content (top to bottom):**
  1. Parked: member pins with names, **Leader** and **Sweep** badges, a meeting-point flag,
     the shared route line (if the leader shared one).
  2. Parked sheet: "Peak District ride · 5 of 6 heard", rows with distance to me, to leader, to
     sweep, age and link badge.
  3. Moving (`map` template): own puck and route; members as **plain markers** (no names,
     avatars, photos or plates), at most 6; one `tiles` value "Leader 1.2 km"; a second
     optional "Sweep 0.4 km".
  4. Ride end: "Ride ended · positions deleted" toast.
- **States:** loading: "Waiting for members" · offline: markers fade as retained positions
  expire; "via LoRa ±3 km" discs off a ride's private channel · Parked: full · Idling: full with
  Park evidence · Moving: as item 3 · Passenger view: unchanged (Open on phone).
- **Safety and driving rules:** the driver must have opted in for this ride; ≤ 6 markers;
  convoy positions are deleted at ride end and never written to the logbook ([Vehicles & Map §6.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#61-rides),
  [Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving), [ADR-0038](../../../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md) amendment item 10).
- **Components:** map template, VehiclePin, StatTile (leader distance), Sheet over map, Chip.
- **Spec refs:** [Vehicles & Map §6.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#61-rides) · [Vehicles & Map §6.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#62-routes-and-precision) · [Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving) · [Drive modes §5.4](../../../../specs/2026-10-07-drive-modes-and-editing-design.md#54-convoy--ride) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)

### vehicles-ride-ask — "Share live position with this ride?"  [New]
- **Owner:** app:map
- **Purpose:** ask at the moment of use, when a ride starts, before any live position flows.
- **Opens from → goes to:** social-ride-new "Start ride", joining a ride from an invite →
  social-rides.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night;
  hu7 Night Parked.
- **Content (top to bottom):** 1. Title "Share live position with Peak District ride until it
  ends?" 2. Lines: "Members see where you are while the ride lasts (ends 18:00, at most 24 h).
  It stops at ride end on every link. You can go ghost at any time." 3. "Also share" Toggles:
  Speed (off), Values (off; picks ≤ 6 signals). 4. Buttons **Share until the ride ends** and
  **Not now** (Not now focused).
- **States:** Parked: full · Moving: waits; the ride runs with talk only until answered on the
  phone or Parked · ghost on: the sheet says "You're a ghost. Sharing starts only when you
  become visible."
- **Safety and driving rules:** a live grant always ends at ride end or 24 h ([Accounts §14.5](../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it));
  asked, never assumed ([Vehicles & Map §5](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#5-per-friend-group-and-field-sharing)).
- **Components:** Sheet, Toggle, Button.
- **Spec refs:** [Vehicles & Map §5](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#5-per-friend-group-and-field-sharing) · [Vehicles & Map §6.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#61-rides) · [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)

### vehicles-card-editor — My garage card editor  [New]
- **Owner:** app:map
- **Purpose:** choose which curated fields my vehicle's card has and who sees each.
- **Opens from → goes to:** my vehicle's card "Edit card"; the Garage page → vehicle →
  vehicles-garage-card "View as…".
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; desktop Night.
- **Content (top to bottom):**
  1. Photo: "Add photo" → "Location and camera details are removed and the image is
     re-encoded on this device before anyone sees it."
  2. Fields: Nickname, Make, Model, Year, Body type (drives the silhouette), Mods and
     equipment (list), About (≤ 280 characters), Mileage band (picker, e.g. "150–200k km").
  3. Plate: field plus "Show plate to" ticks per audience (none by default); caption "Never
     on a map or over a mesh."
  4. Line "Your VIN is never shown on a card, not even masked."
  5. Per-field ticks per audience (contacts, groups) in a small table on tablet and desktop.
  6. Buttons "Preview as…" and "Save".
- **States:** empty: silhouette only · loading · error: "Photo couldn't be processed" ·
  Parked: full · Idling: with Park evidence · Moving: locked view.
- **Safety and driving rules:** no field is read from identity data; text entry Parked
  ([Vehicles & Map §2.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle), [ADR-0036](../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md)).
- **Components:** Card, ListRow, Toggle, Button, Sheet.
- **Spec refs:** [Vehicles & Map §1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#1-scope-and-boundaries) · [Vehicles & Map §2.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle) · [Accounts §14.1](../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry)

### vehicles-seen-by — "Seen by" (my shares' audit)  [New]
- **Owner:** app:map
- **Purpose:** show the owner who pulled what from my vehicle, and when.
- **Opens from → goes to:** my garage card footer; map sheet when visible → accounts-s8 (the
  full audit).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; desktop Night.
- **Content (top to bottom):** 1. Filter chips: Today · 7 days · All. 2. Rows: who ("Sam"),
  class ("Location · coarse"), path ("Relay", "Wi-Fi mesh"), time, coarse size. 3. Per row
  "Revoke Sam's access".
- **States:** empty: "No one has looked yet" · loading · offline: local audit still shows ·
  Parked: full · Moving: locked view.
- **Safety and driving rules:** revoke takes effect at the next pull ([Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)).
- **Components:** Chip, ListRow, Button.
- **Spec refs:** [Vehicles & Map §3](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles) · [Accounts §5.3](../../../../specs/2026-10-06-accounts-sharing-design.md#53-share-levels-and-privacy) · [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs)

### vehicles-relay-link — Relay link for viewers without Ostler (V5)  [New]
- **Owner:** app:map
- **Purpose:** later phase: a browser page showing my position, ETA and route so far to
  someone without Ostler, for at most 24 h.
- **Opens from → goes to:** vehicles-share "Send a link" (V5) → the viewer's browser page;
  "Revoke" from accounts-s8.
- **Layout classes:** phone · desktop. **Draw first:** phone Night and Day (the viewer page);
  phone Night (the owner's sheet).
- **Content (top to bottom):**
  1. Owner sheet: duration (1 h, End of trip, 24 h max), "Show ETA" Toggle, "Copy link",
     "Share", warning line "Anyone with the link can see your position until it ends."
  2. Viewer page: full-bleed map, title pill "Live · ends 18:00", own puck, route so far, ETA
     "Arrives 17:40"; no vehicle data, no name beyond a display name.
  3. Ended page: "This link has ended. No position is shown."
- **States:** loading · expired · revoked (same as ended) · ghost on: link ends at once.
- **Safety and driving rules:** ≤ 24 h, revocable, audited, ended by ghost ([Vehicles & Map §8](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#8-viewers-without-ostler-later)).
- **Components:** Sheet, Button, Sheet over map, Chip (countdown).
- **Spec refs:** [Vehicles & Map §8](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#8-viewers-without-ostler-later) · [Vehicles & Map §11](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#11-phases) · [Accounts §15.2](../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142)
- **Open questions:** V5 needs an ADR-0029 §7 amendment; draw it now or wait?

### vehicles-setup — Vehicles & Map: first setup  [New]
- **Owner:** app:map
- **Purpose:** the Map app's own setup flow after install.
- **Opens from → goes to:** the app framework's install step or first open → vehicles-card-editor
  (optional) → vehicles-map.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):** 1. "See the vehicles friends share with you, on one map."
  2. "You start as a ghost. Nobody sees your car until you choose." 3. "Make your card" (or
  "Later") → vehicles-card-editor. 4. "Show convoy markers on the car screen while driving in a
  ride?" Toggle (off; plain markers only). 5. Done → map.
- **States:** no shares yet: map opens empty with "Invite a friend" · Moving: locked view.
- **Safety and driving rules:** convoy markers are an opt-in per ride as well ([Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving)).
- **Components:** Sheet, Toggle, Button.
- **Spec refs:** [Vehicles & Map §4](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#4-ghost-mode-and-the-visibility-sheet) · [Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving) · [Vehicles & Map §2.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle)

### vehicles-settings — Vehicles & Map: settings  [New]
- **Owner:** app:map
- **Purpose:** the Map app's own settings page.
- **Opens from → goes to:** map "…" → Settings; the app's App info page (90-appframe files).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked.
- **Content (top to bottom):** 1. "My card" → vehicles-card-editor. 2. "Who sees what" →
  accounts-s8 (the OS owns grants). 3. "Convoy markers while driving" Toggle (off). 4. "Pin
  labels": Name and age · Age only. 5. "Units": follow system · km · miles. 6. "Seen by" →
  vehicles-seen-by. 7. "Clear cached positions now" (memory only; caption says so).
- **States:** Parked: full · Idling: with Park evidence · Moving: locked view.
- **Safety and driving rules:** the app stores no permissions; links go to the OS ([Vehicles & Map §1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#1-scope-and-boundaries)).
- **Components:** ListRow, Toggle, Segmented, Button.
- **Spec refs:** [Vehicles & Map §1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#1-scope-and-boundaries) · [Vehicles & Map §5](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#5-per-friend-group-and-field-sharing) · [Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving)
