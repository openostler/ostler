---
title: "Designer brief 85-c — Security app: tracker, trail, geofences and tow or theft mode"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-02-gps-tracker-alarm-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md]
summary: >
  Third Security app file (app:security). The tracker: live location of the parked car for
  the owner only (location stays on the device unless shared), fix age and source, Locate
  now with honest wake timing, and who can see it. The trail of a movement while armed. The
  geofence list and the add or edit page (circle on the map, name, alert on leave or enter,
  when armed or always). Tow and theft mode: a proposed page that speeds up check-ins and
  keeps a live trail when the car is moved without the key, and a transport mode the owner
  sets for ferries, recovery trucks and garages.
---

# 85-c — Security app: tracker and geofences

Main page: [85-a](85-security-a-main.md). Receiver and check-in settings are on `hw-tracker`
in [20-hardware-f](20-hardware-f-security-mesh-service.md). Positions come from the
Guardian's GNSS (1 Hz, its own SIM) or, without a Guardian, the node's GPS
([ADR-0032 A][a32a]). Map styles: Ostler Night and Day, `--bg` offline ([visual §7][vds-7]).

### security-tracker — Where's my car  [New]
- **Owner:** app:security
- **Purpose:** the parked car's position for the owner, with how fresh it is.
- **Opens from → goes to:** `security` map; the tracker mini-map widget; the "Find my car"
  shortcut; a movement or tow event. Goes to `security-trail`, `security-geofences`,
  `security-tow-mode`, `hw-tracker`, Accounts sharing.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night; phone Day; tablet Night (map with side panel).
- **Content (top to bottom):**
  1. Full-height Map: the car's puck (silhouette marker), an accuracy circle, geofence
     outlines, the phone's own position if the phone shares it with the app.
  2. Sheet over map (collapsed): "Parked at Home · last fix 3 min ago · ±8 m"; source "Guardian
     GNSS · 1 Hz · own SIM"; 12 V "12.6 V".
  3. Buttons: **Locate now** · **Directions** (opens the Navigation app if installed, else
     the phone's maps app with the position, after a confirm "This sends the position to
     ‹app›") · **Share…** (Accounts sharing, owner's choice).
  4. Expanded sheet: **Trail** row "Since armed: no movement" or "Moved 2.3 km · 02:16–02:31"
     → `security-trail`; **Geofences** row "2 · Home, Work" → `security-geofences`;
     **Tow and theft mode** row → `security-tow-mode`; **Who can see this**: "Only you" or
     the share list with expiry.
- **States:** no fix ("No fix since 18:03 · last known position shown in grey");
  Locate now running ("Asking the Guardian… it checks in by its modem; this can take a
  while" with Cancel; the time is measured on the bench, [ADR-0040 §4][a40-4]); node in
  parked-deep without a Guardian ("Node asleep (deep) · position from 3 h ago"); offline
  (cached, aged); no node (Empty state with **Pair a node**); Viewer or share without
  location: "Location isn't shared with you"; Moving (owner in the car): the head unit
  shows the Map app or the `map` template, not this page; on the phone, Moving banner.
- **Safety and driving rules:** **live location is for the owner only**; anyone else sees it
  only through a share the owner makes, with precise and live expiring within 24 h
  ([ADR-0009][a09], [Accounts §14.5][acc-145]); lists round ends to about 100 m. Locate now is
  Read, so it works on remote paths; a remote wake counts against the quota
  ([ADR-0033 §6][a33-6]).
- **Components:** Map, Sheet over map, Button, ListRow, Chip (fix age), Empty state.
- **Spec refs:** [UI §6][ui-6] (Tracker row) · [UI §3.4][ui-34] · [ADR-0009][a09] ·
  [tracker spec: GPS][ga-gps] (draft).
- **Open questions:** should Directions be offered at all on a theft event, or only "Share
  with police" through a time-boxed share?

### security-trail — Movement trail  [Proposed]
- **Owner:** app:security
- **Why the app needs it:** after a theft or tow alert the owner needs the path and times,
  not just the last dot; Trips records drives, but not a car moved while armed and keyless.
- **Purpose:** the path the car took while armed, with times and speeds.
- **Opens from → goes to:** `security-tracker` → Trail; a movement or tow event. Back.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night; tablet Night.
- **Content (top to bottom):**
  1. Map with the trace in the speed ramp, start and latest markers, check-in dots.
  2. Summary: "2.3 km · 02:16 → 02:31 · max 48 km/h · ignition off".
  3. Point list (ListRows): time, place name if known, speed, fix accuracy.
  4. **Export GPX** (stays on this device unless the owner sends it) and **Share live with…**
     (a time-boxed share, Accounts sharing).
- **States:** single fix only ("One position so far; more as the Guardian checks in");
  gaps ("No fix 02:20–02:24"); loading; offline (cached).
- **Safety and driving rules:** Parked only on driver-facing displays; location rules as
  `security-tracker`.
- **Components:** Map, ListRow, Button, StatTile.
- **Spec refs:** [ADR-0009][a09] · [UI §6][ui-6].
- **Open questions:** keep the trail with the event, or also save it to Trips as a parked
  period?

### security-geofences — Geofences  [New]
- **Owner:** app:security
- **Purpose:** places that raise an alert when the car leaves or arrives.
- **Opens from → goes to:** `security-tracker` → Geofences; `security-settings`. Goes to
  `security-geofence-edit`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night; tablet Day.
- **Content (top to bottom):**
  1. Map with every geofence circle and its name.
  2. ListRows: name ("Home"), size ("radius 150 m"), rule ("Alert on leave · when armed"), a
     Toggle on or off.
  3. **Add geofence** (primary).
  4. Line: "Geofences stay on the Guardian and this car. Places from Settings → Places can be
     used." (OS `places`).
- **States:** empty ("No geofences. Add Home so you know if the car leaves it."); loading;
  offline (edits saved when the node is back, "Waiting to sync"); Moving: locked.
- **Safety and driving rules:** Parked to edit on driver-facing displays; geofences are
  location data and never leave the device unless shared ([ADR-0009][a09]).
- **Components:** Map, ListRow, Toggle, Button, Empty state.
- **Spec refs:** [UI §3.4][ui-34] (Security: "geofences") · [ADR-0032 A][a32a] (geofences on
  the Guardian's modem GNSS).
- **Open questions:** does a geofence check run on the Guardian (works with the Brain off)
  or on the Brain? This brief assumes the Guardian.

### security-geofence-edit — Add or edit a geofence  [New]
- **Owner:** app:security
- **Purpose:** draw one geofence and say when it alerts.
- **Opens from → goes to:** `security-geofences` → Add or a row. Back with Save.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night; phone Day.
- **Content (top to bottom):**
  1. Map with a centre pin (drag, or **Use car's position** / **Use a saved place**) and a
     circle.
  2. Radius Segmented: 100 m · 250 m · 500 m · 1 km (starting values; GNSS error at 1 Hz
     makes smaller circles noisy).
  3. Name Text field (≤ 30 characters), "Home".
  4. **Alert when**: Leaves · Arrives · Both.
  5. **Active**: When armed · Always.
  6. Buttons **Delete** (danger, edit only, with undo), **Cancel**, **Save** (primary).
- **States:** no fix ("Car position unknown · drop the pin by hand"); validation ("Name it",
  "Too small for GPS accuracy"); saving; Moving: locked.
- **Safety and driving rules:** typing is Parked only; Park to edit ([UI §12.1][ui-121]).
- **Components:** Map, Segmented, Text field, Button.
- **Spec refs:** [UI §3.4][ui-34] · [ADR-0032 A][a32a].
- **Open questions:** polygon geofences, or circles only in v1?

### security-tow-mode — Tow and theft mode  [Proposed]
- **Owner:** app:security
- **Why the app needs it:** a car on a recovery truck or ferry sets off tilt and movement
  alerts every time, and a stolen car needs faster position reports than a parked one; no
  spec covers either.
- **Purpose:** two modes. **Theft mode** starts by itself when the armed car moves without
  ignition; **Transport mode** is set by the owner to expect movement.
- **Opens from → goes to:** `security-tracker`; a tow event's detail; `security-settings`.
  Back.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night theft mode active; phone Day transport mode setup.
- **Content (top to bottom):**
  1. **Theft mode** Card (`alarm` tone when active): "Active since 02:16 · car moving with
     ignition off". Rows: "Position every 1 min (starting value) while moving", "Uses Guardian
     data: 3 MB so far", "Ends when you disarm or mark it found". Buttons **Share live with…**
     (time-boxed share) and **Mark as found**.
  2. **Theft mode settings** (inactive): Toggle "Start theft mode when the car moves while
     armed" (on); report interval Segmented 30 s · 1 min · 5 min with the data and battery
     cost line.
  3. **Transport mode** Card: "Expect the car to move without its key" with duration
     Segmented 2 h · 6 h · 24 h and **Start**. While on: "Tilt and movement alerts paused
     until 18:00 · Tamper still alerts" and **End now**.
- **States:** theft mode active (pinned on `security` and in the strip chip as "Alerting");
  no Guardian (node only: "Reports stop if the node goes to deep sleep"); no SIM uplink
  ("Needs the Guardian's SIM or another uplink"); offline; Moving (owner driving): transport
  mode can't start while Moving (Parked to set).
- **Safety and driving rules:** transport mode is a Security change, so Parked and a signed-in
  user with Security; it never pauses Tamper or the alert path ([ADR-0033 §7][a33-7]);
  report rate respects the 12 V floors ([ADR-0040 §4][a40-4]); sharing live location is the
  owner's explicit act ([ADR-0009][a09]).
- **Components:** Card (tone), Toggle, Segmented, Button, ListRow.
- **Spec refs:** [ADR-0040 §4][a40-4] · [ADR-0033 §7][a33-7] · [tracker spec: GPS][ga-gps].
- **Open questions:** is "Share live with police" a named audience, or just a link share?

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md#decision
[a32a]: ../../../../decisions/adr-0032-one-node-optional-brain.md#a-gps-split-two-receivers-two-jobs
[a33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[a33-7]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths
[a40-4]: ../../../../decisions/adr-0040-power-states-and-wake.md#4-wake-requests
[acc-145]: ../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it
[ga-gps]: ../../../../specs/2026-10-02-gps-tracker-alarm-design.md#gps--reporting
[ui-34]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
