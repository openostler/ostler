---
title: "Designer brief: Settings (part F): the Apps section and offline maps"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Part F of the Settings brief, revised for the Android-style OS direction. The Apps section of
  system Settings lists the installed apps; each row opens that app's App info page, drawn by
  the app-framework area, and "Get more apps" opens the Store, drawn by the Store area. The
  earlier app detail, app log and Integrations pages are folded into App info and the
  Store and are no longer screens here. The file still briefs the Existing offline map regions
  page, now owned by the Map app.
---

# Settings brief, part F: Apps and Maps

Tree, shared rules and the Settings lock: [part A](30-settings-a.md).

## Apps (pointers only)

- **Owner:** os. Settings → Apps is one list of every installed app, integrations included
  and labelled "Integration" (a backend-only app with just a setup page, as in Home
  Assistant); decided, item 56.
- **Each row** opens the app's **App info** page (the app-framework area, `90-appframe-*`):
  version and publisher, permissions and data classes it reads ([Accounts §14.1][acc-14.1]),
  the car actions it may request with category and tier ([app model §4.2][am-4.2]),
  notifications, storage, enable or disable, update, uninstall, the app's log, and "Open app
  settings". An app's own settings pages live in that app's area, not here.
- **Get more apps** opens the **Store** (`70-store-*`): apps, integrations, vehicle packs,
  widget, theme and icon packs, wallpapers and dashboard presets.
- **Rules kept from the specs:** installing, enabling and removing are owner operations on
  local links, Parked only ([UI §12.4][ui-12.4]); a manifest's action list only narrows, and
  every request still passes the node's gate ([ADR-0033][adr-0033]); new data classes start as
  "only me" and in ghost; safety stays with the OS, so no app can remove a safety item or
  relax a Moving template.
- **Retired IDs:** `settings-addon-detail`, `settings-addon-logs` and `settings-integrations`
  are dropped (no other file links them); their content is App info's and the Store's.
- **Open question:** may the owner switch off one data class for an app without disabling
  the app? (For App info to answer.)

### maps-regions — Maps: offline regions  [Existing]
- **Owner:** app:map
- **Purpose:** install, update and remove offline map regions on the Brain.
- **Opens from → goes to:** the Map app's settings (Settings → Apps → Map → App info →
  Open app settings); the "Off your maps: install ‹region›" card;
  Storage. Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Free space line: "‹free› free on the Brain".
  2. **Installed**: one row per region (for example "Great Britain"), size, data date, an
     update badge and **Update**; "…" → Remove (removes map, routing, search and elevation).
  3. **Add a region**: a searchable list (Parked only), each with its size; the download shows
     progress and "Waits for Wi-Fi" on a metered uplink.
  4. **Map theme** row → Display (Follow app · Day · Night · High contrast).
  5. Attribution: "© OpenStreetMap contributors".
- **States:** empty ("No offline maps. Online maps work while connected."); downloading;
  error ("Not enough space. Free ‹size›."); offline (Add hidden); without the Navigation
  app, regions hold the map only; Parked full; Moving: the Settings lock.
- **Safety and driving rules:** the Settings lock; downloads never start while Moving.
- **Components:** ListRow (size, date, Update), Button, progress bar (new), search field.
- **Spec refs:** [Navigation §3][nav-3], [visual §7][vds-7].
- **Open questions:** none.

<!-- refs -->
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[adr-0033]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[nav-3]: ../../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
