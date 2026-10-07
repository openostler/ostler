---
title: "Designer brief: Settings (part C): privacy and data"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-logs-at-scale-design.md, specs/2026-10-07-phone-comms-addon-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md]
summary: >
  Part C of the Settings brief: Privacy and data. A New Privacy and data hub (from the UI
  spec's More → Privacy row) leads to a Proposed plain-language view of the data-class
  registry (each class, its precision ladder, its cap, and which apps read it), a Proposed
  Location page (location stays on the device, place names offline or online, the GPS
  source), the Existing ghost chip and sheet, a Proposed usage and crash reports opt-in that is
  off by default, a Proposed Export my data page built on the exit guarantee, and a Proposed
  Delete my data flow. The VIN never appears and never leaves the car on any of them.
---

# Settings brief, part C: Privacy and data

Tree, shared rules and the Settings lock: [part A](30-settings-a.md).

### settings-privacy — Privacy and data  [New]
- **Owner:** os
- **Purpose:** one page that says what Ostler keeps, where, and who can see it.
- **Opens from → goes to:** Settings → Privacy and data (the UI spec's More → Privacy).
  Goes to data classes, Location, Ghost (`accounts-s9`), Sharing (`accounts-s8`), Places,
  Usage reports, Export, Delete, and per-app access (App info, `90-appframe-*`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the Settings lock).
- **Content (top to bottom):**
  1. **Promise** Card (no controls): "Your data stays on this car's devices unless you share
     it. Your location is never sent anywhere unless you share it. The VIN never leaves the
     car. There is no demo data and no advertising."
  2. **Visibility**: the ghost state as a row, "Ghost · nobody sees you live" or "Visible to
     ‹audience› · ‹time left›", → the ghost sheet.
  3. Rows: "What can be shared" (data classes); "Who sees what" (Sharing); "Location";
     "Places and privacy zones" (`places`); "App access" (one line per installed app:
     "Social reads presence, location (live)"); "Usage and crash reports" (meta: "Off").
  4. **Your data**: "Export my data", "Delete my data" (danger text).
  5. **Never shared** (read-only list): "VIN and identity replies · raw captures · audio and
     voice notes · private notes · phone contacts, call history and message text."
- **States:** loading; offline ("Needs the Brain" on rows served by the Brain); Ostler
  Diagnostics alone (rows that need the Brain hidden, with one caption); Parked full; Moving:
  the Settings lock, except that going ghost stays one tap from the strip chip; locked
  (Car profile): read-only.
- **Safety and driving rules:** the Settings lock; becoming visible waits for Parked or the
  phone ([Accounts §14.7][acc-14.7] S9).
- **Components:** Card, ListRow, Chip (status, for the visibility state).
- **Spec refs:** [UI §3.4][ui-3.4], [Accounts §14.1][acc-14.1], [Accounts §14.3][acc-14.3],
  [Accounts §5.3][acc-5.3], [ADR-0009][adr-0009], [ADR-0036][adr-0036],
  [Phone & Comms §9][pc-9].
- **Open questions:** none.

### settings-data-classes — What can be shared  [Proposed]
- **Owner:** os
- **Purpose:** the data-class registry in plain words.
- **Why proposed:** the registry decides every share and every app's reach
  ([Accounts §14.1][acc-14.1]) but no screen lists it; owners need it to understand grants,
  ghost and app access.
- **Opens from → goes to:** Privacy and data → What can be shared; a class chip on an
  app card. Goes to the class detail (a sheet) and Sharing (`accounts-s8`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, tablet Night (list and detail), hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Caption: "Everything starts as 'only me'. Live classes hide when you go ghost."
  2. One ListRow per class: icon, name, one line, and chips "Live" and "Sensitive" where they
     apply. System rows: Presence ("online, driving, parked, in a ride"), Vehicle card ("make,
     model, year, nickname, photo; plate only if ticked"), Location ("none · coarse · place ·
     route · precise · live"), Live signals ("readings such as RPM, boost, coolant"), Trips
     ("summary · full"), Faults ("codes, freeze frames, readiness"), Notes ("only notes you
     mark shareable"), Maintenance ("off by default; never in a preset"), Video ("one named
     camera, live only"), Audio ("never leaves you"). Then one group per app that
     registers classes, named "‹app›.‹class›".
  3. **Class detail** sheet: what it covers; the precision ladder as a stepped row; the
     longest a grant may last ("Precise and live: 24 hours at most, always"); the widest
     audience ("Audio: only you"); who has a grant now (count, → Sharing); which apps read
     it.
- **States:** loading; error; Parked full; Moving: the Settings lock; locked: read-only (the
  page has no controls besides links).
- **Safety and driving rules:** read-only; the VIN, raw captures and Decode evidence are not
  classes and never appear as rows ([Accounts §14.1][acc-14.1]).
- **Components:** ListRow, Chip, Sheet, a ladder row (new component: 2–6 stepped segments,
  read-only, the current maximum in `accent-soft`).
- **Spec refs:** [Accounts §14.1][acc-14.1], [Accounts §14.5][acc-14.5],
  [Accounts §15.1][acc-15.1], [Accounts §15.2][acc-15.2], [app model §14][am-14].
- **Open questions:** show this page, or fold it into Sharing (S8) as a "Classes" tab?

### settings-location — Location  [Proposed]
- **Owner:** os
- **Purpose:** where position comes from, and what is done with it on the device.
- **Why proposed:** place-name lookup has an online switch today only as a server flag
  ([logs at scale §2][las-2]); the owner needs to see it, and the location promise, in one
  place.
- **Opens from → goes to:** Privacy and data → Location. Goes to Places, Ghost and Sharing.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Promise line: "Location stays on this car's devices unless you share it."
  2. **Source** (read-only): "Node GPS · ‹fix state›" or "u-blox GNSS · 10 Hz"; on the D2 a
     caption "Road speed usually comes from GPS, because a SLABS session holds the K-line."
  3. **Place names**: Segmented "On this device only · Also look up online". Caption for
     online: "Sends rounded positions to OpenStreetMap's Nominatim to name places. Off keeps
     the built-in names." Attribution line "Place names © OpenStreetMap contributors ·
     GeoNames".
  4. **Phone location** (companion app): row showing the OS permission ("While using the
     app"), → the phone's settings.
  5. Rows: "Places and privacy zones", "Ghost", "Who sees my location" (Sharing filtered to
     the location class).
- **States:** no GPS ("No position source. Trips record without a map."); offline (online
  lookup waits; caption "Names will update when online"); Parked full; Moving: the lock.
- **Safety and driving rules:** the Settings lock; no setting here shares location; sharing
  is only by grant ([Accounts §14.2][acc-14.2]).
- **Components:** ListRow, Segmented, Card.
- **Spec refs:** [ADR-0009][adr-0009], [logs at scale §2][las-2], [Accounts §14.5][acc-14.5],
  [UI §13.4][ui-13.4].
- **Open questions:** should online place names default to off on new installs?

### settings-usage-reports — Usage and crash reports  [Proposed]
- **Owner:** os
- **Purpose:** the owner's opt-in to send Ostler anonymous crash reports and the existing
  anonymous decode traces; **off by default**.
- **Why proposed:** today's Preferences already has "Share anonymous traces" (unmapped bits,
  no VIN, no location); crash reports have no home and no consent screen.
- **Opens from → goes to:** Privacy and data → Usage and crash reports. Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Switch "Share anonymous decode traces" (off): "Raw fault blocks and unmapped bits. No
     VIN, no location, no identifiers. Licensed for the community's decode work."
  2. Switch "Send crash reports" (off): "When Ostler stops with an error, send the error and
     versions. No trips, no location, no messages, no car identity."
  3. Row "See what was sent" → a list of past sends with date and size.
  4. Caption: "There is no tracking and no advertising. Nothing is sent unless one of these
     is on."
- **States:** empty list ("Nothing sent"); offline (queued, "Will send when online");
  Parked full; Moving: the lock; locked: read-only, owner only.
- **Safety and driving rules:** owner only; never includes phone data ([Phone & Comms
  §9][pc-9]) or identity ([ADR-0036][adr-0036]).
- **Components:** Switch (new), ListRow, Card.
- **Spec refs:** [ADR-0036][adr-0036], [Phone & Comms §9][pc-9], [Accounts §6][acc-6].
- **Open questions:** does the owner want any usage analytics at all, or crash reports only?

### settings-export-data — Export my data  [Proposed]
- **Owner:** os
- **Purpose:** take everything out in open formats, offline, with no Ostler server.
- **Why proposed:** the exit guarantee ([app model §14][am-14] §14.6) is a hard rule, but
  only Trips has an export screen.
- **Opens from → goes to:** Privacy and data → Export my data. Goes to Trips → Export all
  (`trips-export-all`) for the trip archive, and to the file save.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Checklist rows with sizes: Trips (CSV, GPX, VBO and the index), Notes, Places, Layouts
     (`.ostler-layout.json`), Contacts and groups, App data (one row each, in the app's
     open format), Settings.
  2. Destination Segmented "This device · USB drive · Phone (share sheet)".
  3. Button "Export" (primary); progress bar; result "Saved ‹file› · ‹size›".
  4. Caption: "The VIN and identity data are replaced with a placeholder in every export."
- **States:** empty (nothing to export); loading sizes; error (disk full: "Not enough space
  on the USB drive"); progress; offline (works offline); Parked full; Moving: the lock.
- **Safety and driving rules:** owner sees all users' data; others export their own only;
  identity scrub on every export ([ADR-0036][adr-0036] §3).
- **Components:** ListRow (checkbox), Segmented, Button, progress bar (new component).
- **Spec refs:** [app model §14][am-14], [UI §12.2][ui-12.2], [Drive modes §8.4][dm-8.4],
  [ADR-0036][adr-0036].
- **Open questions:** none.

### settings-delete-data — Delete my data  [Proposed]
- **Owner:** os
- **Purpose:** delete one user's data, or chosen kinds of data, for good.
- **Why proposed:** owners may "delete data" ([Accounts §3.1][acc-3.1]) but no screen does it
  short of a factory reset.
- **Opens from → goes to:** Privacy and data → Delete my data. Steps: 1 choose what (Trips
  before ‹date›, Notes, Contacts, App data, Everything of mine); 2 review ("‹n› trips,
  ‹size›; shares of these trips stop"); 3 confirm (type "DELETE", Parked only, Cancel
  focused); 4 done. Failure: the Brain is asleep, "Needs the Brain", nothing deleted.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):** as the steps; a warning Card "This can't be undone. Export
  first?" with a link to Export.
- **States:** empty; loading; error; Parked full; Moving: the lock; locked: owner only for
  other users' data.
- **Safety and driving rules:** typed confirm; Parked only; trips of a deleted user keep
  "former user" ([Accounts §14.7][acc-14.7] S5).
- **Components:** ListRow (checkbox), Card (warning tone), Button (danger), Sheet.
- **Spec refs:** [Accounts §3.1][acc-3.1], [Accounts §14.7][acc-14.7].
- **Open questions:** keep a 7-day undo like Reset layout, or delete at once?

<!-- refs -->
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[acc-14.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#142-audiences-and-grants
[acc-14.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode
[acc-14.5]: ../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[acc-15.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#151-a-route-detail-on-the-location-ladder-changes-141-and-145
[acc-15.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142
[acc-3.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#31-roles
[acc-5.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#53-share-levels-and-privacy
[acc-6]: ../../../../specs/2026-10-06-accounts-sharing-design.md#6-social-long-term-all-opt-in
[adr-0009]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[adr-0036]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-8.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[las-2]: ../../../../specs/2026-10-06-logs-at-scale-design.md#online-enrichment
[pc-9]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-13.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
