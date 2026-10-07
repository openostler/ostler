---
title: "Designer brief: App framework (part G): uninstall and the developer view"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Part G of the app-framework brief. The uninstall confirm says, in plain rows, what data
  is deleted and what is kept, offers Export first in an open format (the exit guarantee),
  says which widgets and dock slots go, and has variants for a vehicle pack (recordings
  stay), an integration and a system app (never uninstalled). The developer view of an app
  shows its manifest as read-only JSON with the registry's checks beside it, its
  contributions (slots, widgets, actions with category and tier, views with driving rules),
  a Reload button and a live log, in service mode and Parked only. It ends with the area's
  open questions.
---

# App framework brief, part G: uninstall and developer view

Rules and terms: [part A](90-appframe-a.md).

### app-uninstall — Uninstall  [Proposed]
- **Owner:** os
- **Why the app needs it:** apps now hold real data (service records, trips); the exit
  guarantee says every app that keeps user data exports it in an open format, so uninstall
  must offer that first and be plain about what goes.
- **Purpose:** confirm removal, after showing what is deleted and kept and offering export.
- **Opens from → goes to:** App info **Uninstall**; Storage **Clear data** (same sheet,
  title "Clear Maintenance data?"); an integration entry **Remove** → done → `app-list`
  with a toast and **Undo** for 10 s where the data is kept.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night.
- **Content (top to bottom),** example **Maintenance**:
  1. Title "Uninstall Maintenance?"
  2. **Deleted** (rows with `delete` icon): "‹n› service records, ‹n› reminders, ‹n› fuel
     logs, ‹n› documents and their attachments"; "Its settings and notification choices".
  3. **Kept** (rows with `check` icon): "Your car and its trips (Trips keeps them)";
     "Odometer readings from the car".
  4. **Also removed**: "‹n› widgets on 2 home pages"; "Its dock slot (the slot stays, empty)";
     "Its link with the LubeLogger bridge (the bridge stops)".
  5. Card with `download`: **Export first** → the app's export bundle ("zip: records,
     CSVs, all attachments, a printable history"), then back here with "Exported ‹time›".
  6. Switch **Keep my data on the Brain** "Reinstall picks it up. Uses ‹size›."
  7. Buttons **Cancel** (focused) and **Uninstall** (danger).
- **Variants:**
  - **Vehicle pack** (Discovery 2): "Remove Land Rover Discovery 2 (Td5)?"; Kept: "Trips and
    recordings of the Discovery 2 Td5 (they open in replay)"; Deleted: "Live pages, system
    list and fault names for this car"; a `warn` line "Diagnostics will show 'Vehicle pack
    missing' for this car" (`ia-error-pack-missing`).
  - **Integration** (LubeLogger bridge): "Nothing is deleted from your LubeLogger server.";
    the key is wiped from the Brain.
  - **System app** (Settings, Store, the launcher): no Uninstall; App info shows "Part of
    the OS".
  - **An app with a running action** (a SLABS test): blocked, "Stop the test first".
- **States:** exporting (`ia-long-job`); export failed: Uninstall still possible, with
  "Export failed. Uninstall anyway?"; uninstalling (progress); not owner: never opens;
  remote path: "Local links only"; Moving: the Settings lock.
- **Safety and driving rules:** owner, local link, Parked ([UI §12.4][ui-12.4]); Cancel
  focused; uninstalling never removes the fault telltale, alarm alerts or the Moving
  templates, which the OS draws ([Drive modes §8.1][dm-8.1] R3); undo where data is kept
  (`ia-destructive-undo`).
- **Components:** Sheet, ListRow, Card, Switch (new), Button (danger).
- **Spec refs:** [App model §14][am-14] (14.6 exit guarantee) · [App model §5][am-5] ·
  [Drive modes §7.7][dm-7.7] · [UI §12.4][ui-12.4].
- **Open questions:** default of **Keep my data on the Brain**: on (Android's "keep app
  data" choice) or off (a clean removal)? The brief draws it off.

### app-dev-view — Developer view of an app  [Proposed]
- **Owner:** os
- **Why the app needs it:** app and pack authors need to see what the registry made of a
  manifest, reload a build and read its log without a terminal; HA shows manifests and
  diagnostics the same way.
- **Purpose:** inspect an app's manifest and contributions, reload it, watch its log.
- **Opens from → goes to:** App info overflow **Developer view** (only in service mode);
  Settings → Developer → Apps. Back → App info. Links → `app-info-logs`, Decode lab (for
  a pack's signals, if installed).
- **Layout classes:** tablet · desktop · phone · hu9 · huwide. **Draw first:** desktop
  Night, tablet Night, phone Night.
- **Content (top to bottom):**
  1. Service-mode frame around the viewport (OS-drawn). Header: app name, id
     "ostler.maintenance", Chips "‹version›", "Kind: App", "Trust: First party".
  2. Tabs (TabBar): **Manifest · Contributes · Checks · Log**.
  3. **Manifest:** the `ostler-app.json` as read-only mono JSON with line numbers, folding,
     and a **Copy** Button; fields the registry assigned (`trust`, `kind`) marked "set by
     Ostler".
  4. **Contributes:** tables, one per kind: slots (`more:*` page, `home:card`); widgets (id,
     sizes, surfaces, Moving template or "Parked only", `refresh_hz`); actions (id,
     category, tier, `runs_on`, `queueable`), example for Diagnostics:
     "slabs.compressor · Actuator tests · Tier 2 · node · not queueable"; views with their
     driving rules ("due · parked full · moving false"); data classes read and added.
  5. **Checks:** the registry's results as rows with status Chips: `ok` "Shell range ^1.0
     matches"; `ok` "Actions match the capability manifest"; `warn` "Widget 'due' asks for
     more data than the app"; `alarm` "View 'list' names a Moving template not in the set".
  6. **Log:** live tail, level filter Chips, **Pause**, **Export**.
  7. Buttons **Reload app** (secondary; development builds and side-loaded apps only) and
     **Validate again**.
- **States:** not in service mode: page absent; reload in progress ("Reloading… widgets
  show their placeholders"); manifest refused: Checks first, app shows "Not loaded"; head
  units: Parked only; Moving: service mode exits, so the page closes with the locked view.
- **Safety and driving rules:** service mode is refused and exits while Moving
  ([UI §3.5][ui-3.5]); this view shows and reloads only: it cannot edit a manifest,
  change a category or tier, or run an action ([ADR-0033][adr-33] manifest test).
- **Components:** TabBar, CodeBlock (new component: read-only mono JSON on `surface-2`
  with line numbers and folding), ListRow, Chip (status), Button.
- **Spec refs:** [App model §4.1][am-4.1] · [App model §4.2][am-4.2] ·
  [App model §10][am-10] · [App model §13][am-13] (13.1) · [UI §3.5][ui-3.5].
- **Open questions:** should the developer view also be reachable outside service mode on
  desktop, for pack authors working on a laptop with no car?

## Open questions for this area (all parts)

1. **Apps and integrations:** one list with a kind label, or separate tabs (`app-list`,
   `app-integrations`)? Both are drawn.
2. **New manifest fields** for these pages, each a platform change: `setup_flow`,
   `notification_channels`, `shortcuts`, link and file handlers.
3. **Force stop** for bundled apps: keep as "Stop and reload", or drop it?
4. **Data classes:** a Switch only for optional classes, or for required ones too?
5. **Car action permission** at first use per category (`app-permission-car`), or the
   install-time review only?
6. **Power figures** per app on the Brain: measured, or wakes and holds only?
7. **Theme and icon packs:** may a theme change the accent hue; may an icon pack ship its
   own drawings (the brief says no: Material Symbols only)?
8. **Wallpapers** never behind a Moving template or Drive page: confirm.
9. **Uninstall:** "Keep my data on the Brain" on or off by default?
10. **Owner names** for integrations in the screen index: the D2 pack and the LubeLogger
    bridge have no `app:` name, so their pages are owned by `os`; add names?
11. **Developer view** outside service mode on desktop?

<!-- refs -->
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[am-10]: ../../../../specs/2026-10-06-app-model-design.md#10-tests
[am-13]: ../../../../specs/2026-10-06-app-model-design.md#13-power-states-wake-and-queued-actions-accepted-2026-10-06
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-4.1]: ../../../../specs/2026-10-06-app-model-design.md#41-shape
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[dm-7.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#77-hide-replace-and-reachability-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
