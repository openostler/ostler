---
title: "Designer brief: App framework (part B): the App info pages"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md, references/research/ha_architecture_addons.md]
summary: >
  Part B of the app-framework brief: the pages behind each App info row. Permissions and
  data lists the data classes an app reads (with a Switch where a class is optional), the
  OS permissions it holds and the car actions it may ask for with their category, tier and
  while-moving rule. Notifications lists the app's channels, Android-style, with critical
  alerts fixed on. Storage and cache, Power use on the Brain, Open by default (the links
  and files the app opens), Widgets and shortcuts (with Add to home), Version and source
  (update, changelog, licence, publisher, channel) and the App log complete the set.
---

# App framework brief, part B: App info pages

Rules, terms and the Apps list: [part A](90-appframe-a.md). Every page here is a Settings
page: the Settings lock applies while Moving, edits are owner operations on local links,
other roles see read-only rows marked "Owner only". The example app is **Diagnostics**
unless a block says otherwise. Each page opens from its row on `app-info`; Back returns there.

### app-info-permissions — Permissions and data  [New]
- **Owner:** os
- **Purpose:** what this app reads, what it may ask the OS for, and which car actions it
  may request.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the lock).
- **Content (top to bottom):**
  1. **Data it reads** (data classes, [Accounts §14.1][acc-14.1]): one ListRow per class
     with its name and one line: `faults` "Fault codes, freeze frames, readiness",
     `live` "Live values from the car". Required classes show the word "Needed" and no
     Switch; optional classes show a Switch, for example Maintenance's `maintenance`
     "With costs" detail. Caption: "Who else sees this data is set in Sharing" → `accounts-s8`.
  2. **Data it adds** (`contributes.data_classes`): "None" or each class with "Starts
     visible to you only" ([Accounts §14.3][acc-14.3]).
  3. **OS permissions:** ListRows with a Switch each, only those the manifest names:
     Notifications; Wake the Brain "When you tap something that needs it"
     (`permissions.wake: interactive`); Location, Microphone, Camera, Calls for apps that
     ask. Background wake reads "First-party apps only" ([App model §13][am-13]).
  4. **Car actions it may ask for** ([ADR-0033][adr-33] §1): grouped by category, each
     group with its tier and while-moving rule, rows from the pack's actions:
     **Maintenance** · Tier 1 · "Parked or idling": Clear fault codes (TD5, SLABS).
     **Actuator tests** · Tier 2 · "Parked only": SLABS Compressor, Exhaust valve, Buzzer,
     ABS pump (verified); TD5 Fuel pump, Glow plugs (Experimental).
     **Procedures** · Tier 3 · "Parked only": SLABS Power bleed, Modulator bleed.
     **Coding** · Tier 4: "Listed for honesty. Ostler never runs these."
     A group Switch "Allow asking" (from `app-permission-car`); caption "Your role still
     decides, and every action asks you first."
  5. **Network hosts:** one row per declared host, each an outbound path with a Switch that
     starts off until the owner allows it (decided, item 25).
  6. **Hardware:** only for `device` integrations from first-party or verified publishers,
     naming the device; never a car bus (item 26).
  7. **Works on:** Chips Head unit, Phone, Desktop (its `hosts`).
- **States:** no permissions: "This app reads nothing and asks for nothing"; a required
  class switched off by sharing rules: the app's pages say why; not owner: read-only;
  Moving: the Settings lock.
- **Safety and driving rules:** a Switch here only narrows; it never raises a role or
  share, and every action still meets its confirm and the node's gate ([ADR-0033][adr-33]
  §3); the VIN is never a class.
- **Components:** ListRow, Switch (new), Chip, Card (group), Badge "Experimental".
- **Spec refs:** [App model §4.2][am-4.2] · [App model §14][am-14] (14.4) ·
  [Accounts §14.1][acc-14.1] · [ADR-0033][adr-33] · [UI §7.1][ui-7.1] · [app UI model §8][ua-8].
- **Open questions:** may a user switch off a required class (the app then stops), or only
  optional ones? The brief draws only optional ones with a Switch.

### app-info-notifications — Notifications  [New]
- **Owner:** os
- **Purpose:** switch an app's notification channels on or off, per place.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night.
- **Content (top to bottom),** example **Maintenance**:
  1. Master Switch "Allow notifications".
  2. **Channels** (declared by the app), one ListRow each: name, one line, a Switch, and
     where it may show as Chips **In the car** · **On phone**: "Service due" (both),
     "Fault suggests a service" (both), "Document expires" (phone).
  3. **Critical (set by the OS)** Card, no controls: "Fault warnings and alarm alerts are
     not this app's. They always show." → `settings-notifications`.
  4. Caption: "In the car, reminders show only at the start or end of a trip."
- **States:** app has no channels: "This app doesn't send notifications"; master off:
  channels greyed; no paired phone: "On phone" Chips read "Pair a phone"; Moving: the lock.
- **Safety and driving rules:** an app cannot declare a critical channel; message text
  never shows while Moving, whatever the channel ([UI §12.1][ui-12.1]).
- **Components:** Switch (new), ListRow, Chip, Card (tone).
- **Spec refs:** [App model §14][am-14] (14.4 `notify`) ·
  [Maintenance §8][mg-8] · [UI §12.1][ui-12.1] · [app UI model §7][ua-7].
- **Open questions:** **Decided ([app UI model §7][ua-7]):** apps declare channels in
  `contributes.notifications.channels`; `alarm` and `critical` are reserved for the OS (item
  24).

### app-info-storage — Storage and cache  [New]
- **Owner:** os
- **Purpose:** how much the app keeps, and clearing its cache or data safely.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom),** example **Maintenance**: 1. Bar of the Brain's disk with
  this app's share in `series-1`. 2. Rows: "App" ‹size›, "Your data" ‹size› ("‹n› service
  records, ‹n› documents"), "Cache" ‹size›. 3. Buttons **Clear cache** (secondary) and
  **Clear data** (danger) → the same sheet as `app-uninstall` (data deleted, **Export
  first**). 4. Link "All storage" → `settings-storage`.
- **States:** empty cache: Clear cache disabled; offline: "Needs the Brain"; Moving: lock.
- **Safety and driving rules:** Clear data needs the export offer first ([App model §14][am-14]
  14.6, exit guarantee); Cancel focused.
- **Components:** progress bar (new), ListRow, Button (danger), Sheet.
- **Spec refs:** [App model §6][am-6] (`storage`) · [App model §14][am-14] (14.6) · [app UI model §8][ua-8].
- **Open questions:** none.

### app-info-power — Power use on the Brain  [Proposed]
- **Owner:** os
- **Why the app needs it:** the Brain runs from the car's battery; an app that wakes it or
  holds it awake costs 12 V charge, and the owner should see which.
- **Purpose:** show the app's wakes, holds and load, and the switch for its wake permission.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Summary word **Low · Medium · High** with icon. 2.
  "Woke the Brain ‹n› times this week", each from a tap ("interactive"). 3. "Kept the Brain
  awake ‹time› (views open)". 4. "Share of the Brain's time while awake: ‹%›" (estimated).
  5. Switch **May wake the Brain** (`permissions.wake`). 6. Link → `hw-power`.
- **States:** no wake permission: rows 2 and 5 read "Never wakes the Brain"; Ostler
  Diagnostics alone (no Brain): page absent; figures estimated: the word "estimated".
- **Safety and driving rules:** alarm paths never depend on the Brain, so no app's power
  setting touches them ([ADR-0033][adr-33] §7, [ADR-0040][adr-40]).
- **Components:** StatTile, ListRow, Switch (new).
- **Spec refs:** [App model §13][am-13] · [UI §3.8][ui-3.8] · [ADR-0040][adr-40].
- **Open questions:** per-app attribution of Brain time is new: measure it, or show wakes
  and holds only?

### app-info-defaults — Open by default  [Proposed]
- **Owner:** os
- **Why the app needs it:** the direction makes Navigation, Trips and others separate apps
  that can open the same kind of link or file; the owner picks which one does.
- **Purpose:** the links and files this app opens, and whether it is the default.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Switch "Open supported links in this app". 2. List of
  what it handles, each with "Default" or **Set as default**. Examples from three apps:
  Navigation "GPX tracks (.gpx)", Trips "Shared trip links", Diagnostics "Fault links". 3.
  Link "Pages it adds" (its `more:*` pages and routes). 4. **Clear defaults**.
- **States:** handles nothing: "This app doesn't open links or files"; head units: page
  read-only (no file opening there).
- **Safety and driving rules:** opening a link never skips the target page's own driving
  rule.
- **Components:** ListRow, Switch (new), Button.
- **Spec refs:** [App model §6][am-6] (`nav`, route names) · [Drive modes §8.4][dm-8.4].
- **Open questions:** do apps declare link and file handlers in the manifest (new field)?

### app-info-provides — Widgets and shortcuts  [New]
- **Owner:** os
- **Purpose:** list every widget and shortcut the app offers, with where each is placed.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** 1. **Widgets** (`contributes.widgets`): a preview tile, title
  and description ≤ 60 characters, size Chips (small · medium · wide · hero), where it may
  go (Chips Home · Drive), its Moving behaviour ("While moving: tiles" or "Parked only"),
  "Placed on ‹n› pages", Button **Add to home** → widget setup (`45-launcher-*`). Example
  Diagnostics: Fault count, Live gauge (Coolant, Turbo pressure), Module status, Scan all.
  2. **Shortcuts**: "Scan all" (Parked), "SLABS faults"; **Add to home**, **Add to dock**.
- **States:** none provided: "This app adds no widgets or shortcuts"; app disabled: buttons
  disabled; Moving: the lock.
- **Safety and driving rules:** placing is editing: Park to edit ([Drive modes §8.1][dm-8.1]
  R1); a widget whose Moving rule is "Parked only" cannot go in a Moving section.
- **Components:** Card (preview), Chip, ListRow, Button.
- **Spec refs:** [App model §15][am-15] (15.1–15.2) · [Drive modes §7.2][dm-7.2] ·
  [Drive modes §9][dm-9] · [app UI model §2][ua-2].
- **Open questions:** **Decided ([app UI model §2][ua-2]):** shortcuts are declared in
  `contributes.shortcuts`, with up to four dynamic ones from the SDK.

### app-info-version — Version and source  [New]
- **Owner:** os
- **Purpose:** version, update, changelog, licence, source and publisher.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** 1. "Version ‹version›"; "Works with Ostler ‹range›"; if newer:
  Card "‹new version› available · ‹size›" with **Update** (primary) and "What's new".
  2. **Changelog**: the last three releases, one line each. 3. **Channel** Segmented
  "Stable · Beta". 4. **Publisher** "openostler", Chip "First party" (or "Part of the OS",
  "Community"); "Signed by ‹publisher›" with a `verified` icon. 5. **Licence** row → the
  licence text. 6. **Source** row → the repository page (outside link).
- **States:** up to date; updating (progress, "Waits for Wi-Fi" on a metered uplink);
  update failed: "Kept ‹version›. Try again"; Moving: the lock.
- **Safety and driving rules:** nothing updates while Moving; an update never applies
  mid-drive ([HA architecture §3.3][haa-3.3] copied).
- **Components:** ListRow, Card, Button, Segmented, Chip.
- **Spec refs:** [App model §7][am-7] · [App model §4.2][am-4.2] ·
  [HA architecture §3.3][haa-3.3] · [app UI model §8][ua-8].
- **Open questions:** **Decided ([app UI model §8][ua-8]):** the channel is set per app, in
  its App info under Version and updates.

### app-info-logs — App log  [New]
- **Owner:** os
- **Purpose:** the app's errors, stops and the car actions it asked for.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Filter Chips **All · Errors · Actions asked**. 2. Rows,
  newest first: time, level icon and word, one line ("App stopped in the Faults page",
  "Asked: Clear fault codes · SLABS · you approved · 2 of 3 cleared"). 3. **Export log**
  (text file, no VIN, no location unless the row is a location row the user may see).
- **States:** empty "Nothing logged"; offline "Needs the Brain"; Moving: the lock.
- **Safety and driving rules:** the log is read-only; audit rows cannot be deleted here.
- **Components:** ListRow (mono time), Chip, Button.
- **Spec refs:** [App model §5][am-5] · [App model §6][am-6] (`X-Ostler-App`) · [app UI model §8][ua-8].
- **Open questions:** none.

<!-- refs -->
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[acc-14.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-40]: ../../../../decisions/adr-0040-power-states-and-wake.md
[am-13]: ../../../../specs/2026-10-06-app-model-design.md#13-power-states-wake-and-queued-actions-accepted-2026-10-06
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[am-6]: ../../../../specs/2026-10-06-app-model-design.md#6-the-shell--app-api
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[haa-3.3]: ../../../../references/research/ha_architecture_addons.md#33-backups-updates-channels
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ua-8]: ../../../../specs/2026-10-07-app-ui-model-design.md#8-system-settings-and-the-app-info-page
[ua-7]: ../../../../specs/2026-10-07-app-ui-model-design.md#7-notification-channels
[ua-2]: ../../../../specs/2026-10-07-app-ui-model-design.md#2-what-an-app-contributes
