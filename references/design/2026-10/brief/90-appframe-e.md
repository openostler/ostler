---
title: "Designer brief: App framework (part E): Integrations, discovery and permission sheets"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, references/research/ha_integrations_dashboards.md]
summary: >
  Part E of the app-framework brief. The Integrations page, in Home Assistant's devices and
  services style: discovered entries with Add and Ignore, entries that need attention, and
  configured entries such as the Discovery 2 pack and the LubeLogger bridge. The entry
  detail page lists the entry's devices (the car, its systems, the node) and signals with
  proven and candidate counts, with Configure, Reload, Disable and Remove. The New device
  found notice says what the OS found and never adds it by itself. The runtime permission
  sheets ask at the moment of use for location, phone, microphone and camera, and for the
  right to ask for car actions by ADR-0033 category and tier. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# App framework brief, part E: Integrations, discovery, permission sheets

Rules and terms: [part A](90-appframe-a.md); the setup flows these pages start:
[part C](90-appframe-c.md), [part D](90-appframe-d.md).

### app-integrations — Integrations  [New]
- **Owner:** os
- **Purpose:** list integration entries: discovered, needing attention, configured.
- **Opens from → goes to:** `app-list`'s Integrations row (one list, item 56); the
  discovery notice; Settings search. Rows → `app-integration-entry`;
  **Add** → the integration's flow (`app-flow-discovered`); **Add integration** → the
  Store's integrations shelf (`70-store-*`) or an installed, unset integration's flow.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the lock), tablet Night (grid).
- **Content (top to bottom):**
  1. Title "Integrations"; search field; Button **Add integration** (primary).
  2. **Discovered** (only when non-empty), Cards with an `accent-soft` edge: icon, "Found:
     Land Rover Discovery 2 (Td5)" meta "On the node's K-line", Buttons **Add** and
     **Ignore**. Other examples: "Found: an Ostler node nearby · Bluetooth"; "Found: a USB
     K-line cable on this computer"; "The Climate node suggests the Climate app".
  3. **Needs attention**, Cards in `warn-bg` or `alarm-bg` with icon and word: "LubeLogger
     bridge · Key refused" **Sign in again**; "Discovery 2 (Td5) · Node not reachable"
     **Details**; "Discovery 2 (Td5) · Set-up not finished" **Continue**.
  4. **Configured**, one Card per integration (two columns on tablet, three on desktop):
     icon, name, Chip (Vehicle pack, Bridge, Source), meta "1 car · 6 systems" or "Synced
     ‹time› ago", and a source line from the entry: "Node · local, live" or "Adapter ·
     local, polled".
  5. Footer link "Ignored (‹n›)" → the ignored discoveries, each with **Add**.
- **States:** empty: "Nothing connected yet. Add your car to start." with **Add
  integration**; loading; offline: Brain-held entries "Needs the Brain"; no vehicle:
  vehicle-pack cards read "No car uses this pack"; not owner: read-only, Add hidden;
  Moving: the Settings lock; Passenger: not offered.
- **Safety and driving rules:** the Settings lock; a found thing is never added without a
  person's **Add** ([HA integrations §5][ha-5] C2); adding is an owner operation, local.
- **Components:** Card (tone, tappable), Chip, Button, search field (new).
- **Spec refs:** [ADR-0042][adr-42] HA direction item 98 · [HA integrations §1][ha-1] ·
  [HA integrations §4.1][ha-4.1] · [HA integrations §5][ha-5] (C1, C2, C14) ·
  [UI §6][ui-6] · [app UI model §6][ua-6].
- **Open questions:** **Decided (item 56):** one Apps list with integrations labelled; this
  page opens from that list's Integrations row, not from a separate tab.

### app-integration-entry — Integration entry  [New]
- **Owner:** os
- **Purpose:** one entry's devices, signals, source and controls.
- **Opens from → goes to:** `app-integrations` rows; App info of a vehicle pack
  (**Integration entry**). Devices → Diagnose's system page (`diagnose-system`) or the
  device page (`network-device`); **Configure** → `app-options-flow`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, tablet Night.
- **Content (top to bottom),** example the Discovery 2 entry:
  1. Header: "Land Rover Discovery 2 (Td5)", Chip **Vehicle pack**, status Chip `ok`
     "Working" (or `warn` "Not reachable"); car "Discovery 2 Td5".
  2. **Source** row: "Ostler Diagnostics node ‹name› · K-line · local, live"; **Change**
     → Reconfigure.
  3. **Devices**: the node (`memory`) "via USB"; then systems, each "via the node": TD5
     (engine), SLABS (ABS + air suspension), BCU, ACE ("Not fitted"), EAT, SRS, each with
     its status Chip from the Scan vocabulary (`OK`, `Faults 2`, `No response`).
  4. **Signals**: per system "TD5: 45 signals" and "SLABS: 18 signals, wheel speeds
     candidate"; "Not supported yet" for BCU. → the signal list in Diagnostics.
  5. **Actions it brings**: "SLABS: 4 verified tests, 5 procedures; TD5: 14 experimental
     tests"; "Tier 4 rows listed for honesty."
  6. Buttons **Configure**, **Reload** (secondary), **Disable**, **Remove** (danger →
     `app-uninstall`, integration variant).
- **Variants:** the LubeLogger bridge: Source row reads "‹address› · API key · polled";
  Devices absent; Signals reads "Sends: odometer, engine hours"; Actions "None".
- **States:** reloading ("Reloading… live values pause"); not reachable (`warn` Card with
  the connection ladder's rung, link to the Connection sheet); offline; not owner:
  read-only; Moving: the Settings lock.
- **Safety and driving rules:** Reload pauses reads only; it never stops a running test
  (that has its own Stop); remove asks first.
- **Components:** ListRow, Chip (status), Card, Button.
- **Spec refs:** [HA integrations §4.1][ha-4.1] · [UI §4.3][ui-4.3] · [UI §4.5][ui-4.5] ·
  [UI §5.1][ui-5.1] · [app UI model §6][ua-6].
- **Open questions:** none.

### app-discovered — New device found  [New]
- **Owner:** os
- **Purpose:** tell the owner, quietly, that something new was found, and offer to add it.
- **Opens from → goes to:** the OS raises it → **Add** → `app-flow-discovered`; **Later** →
  stays in Integrations → Discovered; **Ignore** → the ignored list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (home page card), phone Night (notification and card).
- **Content (top to bottom):** a home-page card (OS-drawn, dismissible) and, on a paired
  phone, a notification: 1. Icon by kind (`directions_car`, `memory`, `cable`, `videocam`,
  `radio`). 2. Title ≤ 30 characters: "New car found", "Ostler node nearby", "Camera
  found", "Radio receiver found". 3. One line: "Looks like a Land Rover Discovery 2 (Td5)".
  4. Buttons **Add** and **Later**; overflow **Ignore**.
- **States:** several finds: one card "3 new devices found" → Integrations; the matching
  app not installed: **Get ‹app›**; not owner: shown as "Ask the owner to add it", no
  buttons; Moving: not shown, held until Parked; Passenger: not shown.
- **Safety and driving rules:** never on a head unit while Moving; never adds anything by
  itself ([App model §7][am-7]: nothing auto-installs); never covers a warning card.
- **Components:** Card (home card), notification (phone), Button.
- **Spec refs:** [App model §7][am-7] · [App model §14][am-14] (14.7 `home:card`) ·
  [Adapters §5][sa-5] · [UI §4.4][ui-4.4] · [app UI model §4.4][ua-4.4].
- **Open questions:** should the OS also show a strip chip for finds? The brief says no
  (apps may add status-only chips since the openness round; finds are not urgent).

### app-permission-request — Permission request sheet  [Proposed]
- **Owner:** os
- **Why the app needs it:** apps ask the OS for location, phone, microphone and camera
  through the SDK at the moment of use; the OS must explain and ask in one style.
- **Purpose:** ask once, at the moment of need, for one permission for one app.
- **Opens from → goes to:** an app's first use of the feature → this sheet → (on a phone)
  the phone OS prompt (`ia-permission-prompt`) → back to the app; **Don't allow** → the
  app's degraded state.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day (location, microphone), hu7 Night (camera).
- **Content (top to bottom):** 1. App icon and name over the permission icon. 2. Title:
  "Allow Trips to use this car's location?"; "Allow Phone to make and take calls?"; "Allow
  Social to use the microphone?"; "Allow Camera to show the reverse camera?". 3. Why, from
  the app (≤ 2 lines). 4. What the OS guarantees, fixed text per kind: location "Location
  stays on this Ostler unless you share it."; microphone "Only while you hold to talk or
  speak a reply. Never recorded unless you choose."; camera "Live view only. Video never
  shows on the driver's screen while moving."; phone "Calls are audio only in the car."
  5. Choices: **While using the app** (primary), **Only this time**, **Don't allow**.
- **States:** denied earlier: the app shows a Card "Location is off for Trips · App info";
  not owner: a user may allow for themself only where the data is their own (their
  location in a trip); remote path: not offered; Moving: never shown on a head unit, the
  request waits for Parked.
- **Safety and driving rules:** no "Always" for camera or microphone; interior cameras need
  occupant consent at the head unit ([Accounts §14.1][acc-14.1] `video`); `audio` is never
  shareable (`max_audience: me`).
- **Components:** Sheet, Button, ListRow (choices).
- **Spec refs:** [App model §14][am-14] (14.3–14.4) · [Accounts §14.1][acc-14.1] ·
  [ADR-0009][adr-9] · [UI §12.1][ui-12.1].
- **Open questions:** none.

### app-permission-car — Allow an app to ask for car actions  [Proposed]
- **Owner:** os
- **Why the app needs it:** an app lists the car actions it may request, by ADR-0033
  category and tier; the owner should approve each category the first time it is used,
  not only at install.
- **Purpose:** let the owner allow an app to ask for one category of car action.
- **Opens from → goes to:** the app's first request in a category → this sheet → the
  action's own confirm sheet (`diagnose-confirm`) → the gate. **Don't allow** → refusal.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content (top to bottom):** 1. "Allow Diagnostics to ask for **Actuator tests**?"
  2. Rows: "Tier 2 · Parked only"; "For example: SLABS Compressor, Exhaust valve"; "Each
  test still asks you first and shows Stop." 3. Who: "Users whose role allows Actuator
  tests (Owner, Mechanic)." 4. **Allow** (primary), **Don't allow**, Cancel focused on
  head units. Variants: **Maintenance** "Tier 1 · Parked or idling · Clear fault codes";
  **Procedures** "Tier 3 · Parked only · Power bleed"; **Comfort** "Tier 1 · allowed
  while moving, driver-safe"; **Coding**: never asked, "Ostler never runs these".
- **States:** not owner: "Ask the owner to allow this"; remote path: refused ("Local links
  only"); Moving: not shown, and the request is refused with "Park to allow".
- **Safety and driving rules:** this only narrows; role, share, token, transport, driving
  state and the confirm still apply, and the node's gate re-checks ([ADR-0033][adr-33] §3,
  §6); an accept from a chat assistant never counts.
- **Components:** Sheet, ListRow, Chip (tier), Button.
- **Spec refs:** [ADR-0033][adr-33] §1–§3, §6 · [UI §7.1][ui-7.1] ·
  [App model §4.2][am-4.2].
- **Open questions:** is a per-category grant at first use wanted, or is the install-time
  review (`setup-app-access`) enough?

<!-- refs -->
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-42]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md#home-assistant-direction-decision-list-items-97101-accepted-direction
[adr-9]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[ha-1]: ../../../../references/research/ha_integrations_dashboards.md#1-ha-integrations-as-of-october-2026
[ha-4.1]: ../../../../references/research/ha_integrations_dashboards.md#41-entities-devices-and-areas
[ha-5]: ../../../../references/research/ha_integrations_dashboards.md#5-copy--avoid--decide-for-ostler
[sa-5]: ../../../../specs/2026-10-07-source-adapters-design.md#5-detection-and-clone-checks
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-5.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#51-shape
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ua-6]: ../../../../specs/2026-10-07-app-ui-model-design.md#6-backend-only-apps-integrations
[ua-4.4]: ../../../../specs/2026-10-07-app-ui-model-design.md#44-rules
