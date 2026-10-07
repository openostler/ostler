---
title: "Designer brief: Store (part B): item detail, versions, install sheet and installing"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, references/research/ha_architecture_addons.md, references/research/ha_companion_community.md]
summary: >
  Part B of the Store brief: one item's page and how it gets installed. The item detail shows
  screenshots per layout class, what the item adds (pages, widgets, setup), its permissions
  and data classes in plain words, the vehicles it supports, licence and source link,
  publisher and verified key, the "Works with Ostler" mark, version history, size and the
  install button. The version history sheet lists changelogs. The install sheet reviews
  access, data classes and where the item runs (Brain, phone, node) with the "Runs on the
  Brain" label for container add-ons. The installing screen shows progress, failure and
  retry, then "Set up now", which starts the app's own setup flow.
---

# Store brief, part B: item detail and install

Parts: [A: rules, home, browse](70-store-a-home-browse.md) · **B** (this file) ·
[C: updates and My library](70-store-c-updates-library.md) ·
[D: publisher, report, offline, sideload](70-store-d-publisher-sideload.md).
The Store's shared rules (Moving, owner only, phone limits, no votes) are in part A §3.

### store-item — Item detail  [New]
- **Owner:** os
- **Purpose:** one item's page: what it is, what it adds, what it reads, who made it, and
  the install button.
- **Opens from → goes to:** any StoreItemCard or row (`store-home`, `store-category`,
  `store-search`, `store-publisher`, `addons-catalogue`); a device that suggests an app
  ([app model §7][am-7]); a deep link `store.item?id=…`. Goes to `store-install-sheet`,
  `store-item-versions`, `store-publisher`, `store-report`, the app's App info
  (`90-appframe-*`, when installed).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day (Maintenance & Garage), hu7 Night (Ostler pack for Land Rover
  Discovery 2), desktop Night (Navigation, "Runs on the Brain"), hu7 Night dim Moving (lock).
- **Content (top to bottom),** example the **Ostler pack for Land Rover Discovery 2**:
  1. **Header:** icon, name, publisher line "openostler" with a `verified` icon and
     "Verified key", kind Chip "Integration · Vehicle pack", review level Chip "First
     party" (System, First party, Verified publisher, Community or Sideloaded, item 30),
     Chips "Open source" and "Works offline". No stars and no review text (item 33). Example App header: "Maintenance & Garage · openostler · App".
  2. **Main button** (primary, one per screen): **Install** · **Update** · **Open** ·
     **Install when parked** (phone, car Moving) · **Ask the owner** (not owner) ·
     disabled with the reason ("Needs a camera", "Needs Ostler ‹x.y›", "Needs the Brain").
     Under it: size ("‹size› download · ‹size› on the Brain") and "Installs on your Brain"
     when the user is on the phone app.
  3. **Screenshots**, a carousel with a Segmented above it for the layout class: "Phone ·
     Head unit · Wide · Desktop" (only the classes the item supports; the current class
     first). Tapping opens a full-screen viewer (still images only).
  4. **What it adds** (ListRows with icons):
     - Pages: for an app, its pages by name ("Services", "Reminders", "Fuel").
     - Widgets: "Adds 3 widgets: Next service, Fuel economy, Costs this year".
     - Dashboards: "Adds 1 dashboard: Off-road (D2)".
     - For the D2 pack: "Modules: Td5 engine, SLABS, BCU, airbag; ACE and autobox in
       progress", "Signals: ‹n› proven, ‹n› candidate", "Actions: ‹n› verified".
     - Setup: "Asks you a few questions after install" or "No setup".
  5. **What it can see and do** (plain words, the same rows as the install sheet):
     - Data classes, each with icon and one line from the registry ([Accounts
       §14.1][acc-14.1]): "Live signals from the car", "Fault codes", "Trips",
       "Location", "Service records and costs".
     - "May ask the car to": each action in words with its category, for example
       "Run the SLABS level test · Service · needs your approval" ([ADR-0033][adr-33]).
       Line under it: "The car checks every request itself."
     - Other: "Notifications", "Wake the Brain", "Internet: none" or "Internet: talks to
       ‹host›".
  6. **Where it runs:** Chips "Brain", "Phone", "Head unit", "Node", and the **Runs on the
     Brain** label for container add-ons with one line: "Runs as a service on your Brain.
     Uses up to ‹memory›. Stops when the Brain sleeps."
  7. **Vehicles supported:** "Land Rover Discovery 2 Td5"; or "Any car" (apps reading only
     generic signals); with a status per vehicle from the pack's vocabulary ("verified on
     a car", "candidate"). A line "Your car: supported" or "Your car: not listed" (`warn`).
  8. **Works with Ostler** mark (when it applies), with "What this means" → a sheet listing
     the criteria (works fully offline, reads only through the car's checks, no VIN leaves
     the device, published update path) ([HA companion research §8][ha-comm-8]).
  9. **About:** description; "Version ‹x.y.z› · Updated ‹date›" → `store-item-versions`
     ("What's new" first lines inline); licence in words ("Open source: AGPL", or "Data:
     CC BY-SA") with **View source** (opens the repo link in the browser; on head units,
     a QR code); "Needs Ostler ‹range›".
  10. **Publisher:** row → `store-publisher`; key fingerprint short form "Key ‹8 chars›".
  11. Footer: **Report this item** (→ `store-report`), and when installed: **App info**
      (→ `90-appframe-*`), **Uninstall** (→ `store-uninstall`).
- **States:** loading: skeleton header and carousel. Error: "Can't load this item · Retry".
  Offline: bundled items show in full; an online-only item shows "Needs the internet to
  install". Installed: main button **Open**, Chip "Installed ‹version›". Update waiting:
  **Update** plus "What's new". Doesn't fit: main button disabled with the reason; the page
  still reads in full. No vehicle: "Vehicles supported" shows without "Your car". Moving
  (head unit): locked view + **Open on phone**. Moving (phone): Moving banner, **Install
  when parked**. Locked (not owner): **Ask the owner** (sends a request to the owners'
  phones). Developer item outside service mode: "Shown in service mode only".
- **Safety and driving rules:** no install while Moving; no video in the carousel; actions
  are described, never run, from this page ([UI §12.1][ui-12.1], [ADR-0033][adr-33]).
- **Components:** Button, Chip (status, kind), Segmented (layout class), new component
  **ScreenshotCarousel**, ListRow, Card, Sheet (Works with Ostler criteria), QR (existing
  pattern from Open on phone).
- **Spec refs:** [app model §4.1–4.2][am-4.2] (manifest: `requires`, `hosts`, `actions`,
  `permissions.data`, `source`), [app model §15][am-15] (widgets), [Accounts §14.1][acc-14.1],
  [ADR-0013][adr-13] (pack contract and licences), [HA research §3][ha-arch-3] · [Store §3][st-3] · [Store §6.1][st-6.1] · [Store §6.2][st-6.2].
- **Open questions:** **Decided ([Store §6.2][st-6.2]):** Works with Ostler marks hardware
  and also apps and integrations, against written criteria, and is free for now (item 35).
  **Decided ([Store §5][st-5], [§6.1][st-6.1]):** "Verified key" means a Verified publisher:
  identity checked and a registered key that signs every release.

### store-item-versions — Version history  [New]
- **Owner:** os
- **Purpose:** every released version of one item, with its changelog and permission changes.
- **Opens from → goes to:** `store-item` → Version line or "What's new"; `store-updates`
  row; `addons-catalogue` row menu. Goes to `store-rollback` (installed items only).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (sheet), hu7 Night (side sheet on the passenger side).
- **Content (top to bottom):**
  1. Title "Version history · ‹item›"; Chip on the installed row "Installed".
  2. One expandable ListRow per version: version, date, channel Chip ("Stable", "Beta");
     expanded: the changelog as plain bullets; a `warn` line when the version **asks for
     more** ("Now reads Location"); a line when it is a **breaking** version ("Needs you to
     update by hand", [HA research §3.3][ha-arch-3.3]). For the D2 pack, changelog lines
     read like "SLABS: front-left height now proven".
  3. On an older version row (installed items): **Roll back to this version** (owner).
- **States:** loading; offline (only versions on the Brain: the installed one and the kept
  previous one); Moving and locked: as `store-item`.
- **Safety and driving rules:** as `store-item`.
- **Components:** Sheet, ListRow (expandable), Chip, Button.
- **Spec refs:** [app model §7][am-7] (SemVer, releases), [HA research §3.3][ha-arch-3.3] · [Store §3][st-3] · [Store §9][st-9].
- **Open questions:** should beta channels exist for all items, or apps and packs only?

### store-install-sheet — Install: review access  [New]
- **Owner:** os
- **Purpose:** the last check before installing: access, data classes, where it runs.
- **Opens from → goes to:** `store-item` **Install**; `store-updates` when an update asks
  for more; `store-sideload`. **Install** → `store-installing`; **Cancel** → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, desktop Day.
- **Content (top to bottom),** example **Navigation**:
  1. Icon, name, publisher with `verified` icon, version, kind Chip, Chip "Runs on the Brain".
  2. **Needs:** "The Brain · ‹size› free on the Brain · an offline map region".
  3. **Reads** (data classes in words): "Location: your position and routes"; "Live
     signals: speed and heading". Caption: "New data it creates is visible to you only
     until you share it."
  4. **May ask the car to:** "Nothing" (Navigation) or the action list with categories.
  5. **Where it runs:** "Brain: routing service (runs as a service, up to ‹memory›)",
     "Head unit and phone: the map and guidance pages". For an integration (D2 pack):
     "Node and Brain: reads the Td5 engine, SLABS, BCU and airbag over the diagnostic
     link". For a theme: "Every display. Contains no code."
  6. **Internet:** "None after install", or one row per declared host ("Talks to ‹host›"),
     each a switch that starts off; the owner turns each one on (item 25).
  7. **Licence:** "Open source · AGPL · View source", or for a closed item "Not open
     source" (`warn` tone, word and icon).
  8. Buttons **Install** (primary) and **Cancel** (focused on head units).
- **States:** requirement not met: **Install** disabled with the reason. Not owner: the
  sheet shows **Ask the owner** in place of Install. Moving: the sheet closes into the
  locked view (head unit) or turns its button into **Install when parked** (phone).
  Offline: works for bundled items and files. Update asking for more: a top `warn` line
  "This update asks for more: Location".
- **Safety and driving rules:** owner only, local link only, Parked on head units
  ([UI §12.4][ui-12.4], [§7.2][ui-7.2]); the sheet never lets an item set its own audience
  or skip a confirm ([app model §8][am-8]).
- **Components:** Sheet, new component **AccessReview** (shared with `setup-app-access`),
  Chip, ListRow, Button.
- **Spec refs:** [app model §4.2][am-4.2], [app model §14.4][am-14] (data-class registry),
  [Accounts §14.1][acc-14.1], [HA research §5][ha-arch-5] (container refusals) and §8
  (readable permission summary, not a score) · [Store §3][st-3] · [app UI model §10][ua-10].
- **Open questions:** merge this with `setup-app-access` into one screen ID?

### store-installing — Installing  [New]
- **Owner:** os
- **Purpose:** show the install's progress, failure and retry, then hand over to the app's
  setup.
- **Opens from → goes to:** `store-install-sheet` **Install**; the queue card on
  `store-home`. Goes to the app's setup flow (`90-appframe-*`, the first step by name),
  `store-item`, or Home.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (progress), phone Night (failed), hu7 Night (done with **Set up now**).
- **Content (top to bottom):**
  1. Icon and name; a progress bar with the step in words: "Downloading ‹n› of ‹size›" →
     "Checking the signature" → "Installing on the Brain" → "Starting" (container items)
     → "Done".
  2. Line: "You can leave this page. Installs pause if the car moves."
  3. **Done:** Card `ok` "‹Item› is installed" with **Set up now** (primary) and **Later**;
     for items with no setup: **Open** (apps), **Use this theme** (themes), **Add this
     dashboard** (dashboards, opens the launcher at the new home page).
  4. **Failed:** Card `alarm` with icon and word: "Download stopped. Check the connection",
     "The signature doesn't match. Not installed", "Not enough space on the Brain. Free
     ‹size›", "Needs Ostler ‹x.y›". Buttons **Retry** and **Cancel**; "Details" opens the
     log lines.
  5. **Paused:** Card `warn` "Paused while driving. Continues when you park."
- **States:** in progress; done; failed; paused (Moving); waiting for Wi-Fi ("Waits for
  Wi-Fi: you are on mobile data", [ADR-0028][adr-28]); offline mid-download ("Offline ·
  continues when connected"). Moving (head unit): the locked view; the install shows
  "Paused" when you park and return. Locked: never reached by non-owners.
- **Safety and driving rules:** an install never starts or finishes while Moving; **Set up
  now** is Park to edit; a bad signature is never overridable here (only Developer mode's
  sideload, part D).
- **Components:** progress bar (new, shared with `maps-regions`), Card (tone), Button,
  ListRow.
- **Spec refs:** [app model §5][am-5] (lifecycle), [app model §7][am-7] (signing),
  [UI §12.4][ui-12.4] · [Store §3][st-3] · [Store §9][st-9].
- **Open questions:** none.

<!-- refs -->
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[adr-13]: ../../../../decisions/adr-0013-repo-split-and-vehicle-pack-contract.md
[adr-28]: ../../../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[am-8]: ../../../../specs/2026-10-06-app-model-design.md#8-explicit-non-goals-and-hard-lines
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[ha-arch-3]: ../../../research/ha_architecture_addons.md#3-apps-formerly-add-ons-and-the-store
[ha-arch-3.3]: ../../../research/ha_architecture_addons.md#33-backups-updates-channels
[ha-arch-5]: ../../../research/ha_architecture_addons.md#5-how-a-container-that-never-touches-the-car-fits-ostlers-gate
[ha-comm-8]: ../../../research/ha_companion_community.md#8-mapping-to-ostler
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[st-3]: ../../../../specs/2026-10-07-store-design.md#3-the-store-app
[st-6.1]: ../../../../specs/2026-10-07-store-design.md#61-review-levels
[st-6.2]: ../../../../specs/2026-10-07-store-design.md#62-works-with-ostler
[st-5]: ../../../../specs/2026-10-07-store-design.md#5-the-catalogue-and-signing
[st-9]: ../../../../specs/2026-10-07-store-design.md#9-updates
[ua-10]: ../../../../specs/2026-10-07-app-ui-model-design.md#10-manifest-schema-2
