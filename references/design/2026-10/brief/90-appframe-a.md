---
title: "Designer brief: App framework (part A): rules, the Apps list and App info"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, references/research/ha_integrations_dashboards.md, references/research/ha_architecture_addons.md]
summary: >
  Part A of the app-framework brief: the OS pages and templates every app uses, modelled on
  Android's App info and Home Assistant's config flows. It sets the terms (app, integration,
  pack, system app), the rules every app-framework page shares (the Settings lock while
  Moving, owner-only operations on local links, the OS keeps safety), and the file map for
  parts A to G. It briefs the Apps list in system Settings, drawn in two variants because
  the owner has not settled whether integrations sit with apps or on their own tab; the App
  info page per app (open, disable, uninstall, force stop, and rows into every sub-page);
  and the force stop and disable sheets.
---

# App framework brief, part A: rules, Apps list, App info

Parts: **A** (this file) · [B: App info pages](90-appframe-b.md) ·
[C: setup and options flow templates](90-appframe-c.md) ·
[D: three worked setup flows](90-appframe-d.md) ·
[E: Integrations, discovery, permission sheets](90-appframe-e.md) ·
[F: pack pages and app errors](90-appframe-f.md) ·
[G: uninstall and the developer view](90-appframe-g.md).
Process and the hard constraints: [design hand-off README](../README.md).

## 1. What this area is

Ostler is an Android-style OS. The OS ships no feature apps; Diagnostics, Trips, Security,
Maintenance, Map, Radio and the rest are **apps** from the Store. This area draws the OS
pages every app passes through: where it is listed, its **App info** page, the **setup
flow** it runs once and the **options flow** it runs later, the **permission sheets** it
raises, and the pages for things that are not apps (widget, theme, icon and wallpaper packs,
dashboard and sound presets). An app's own settings pages live in that app's area.

**Terms** (owner direction 2026-10-07; [ADR-0042][adr-42] HA direction item 98):

| Word | Meaning | Example |
|---|---|---|
| **App** | software that adds features and pages | Diagnostics, Maintenance, Radio |
| **Integration** | an app with no pages of its own, only a setup page; it connects Ostler to a car or a service | the LubeLogger bridge, an MQTT bridge |
| **Vehicle pack** | an integration that teaches Ostler one kind of car | Land Rover Discovery 2 (Td5), `lr_d2` |
| **System app** | part of the OS, always present, never uninstalled | Settings, Store, the launcher |
| **Pack** | content with no code: widgets, themes, icons, wallpapers, presets | the starter widget pack |

## 2. Rules every page in this area shares

- **The Settings lock.** App info, the Apps list, Integrations and every flow are Settings
  pages. On a head unit while Moving, or Idling without Park evidence, they show the
  locked view (`shell-locked-view`): "Available when parked" and **Open on phone**.
  Passenger view is never offered here ([UI §12.1][ui-12.1]).
- **Owner operations, local links.** Installing, enabling, disabling, uninstalling and
  setting up an app are owner operations on a local link, Parked on head units
  ([UI §12.4][ui-12.4], [App model §14][am-14]). Other roles see the same pages read-only
  with a `lock` icon and "Owner only". Over a remote path every button reads "Local links
  only".
- **The OS keeps safety.** No app setting, permission or flow can remove, hide or relax the
  fault telltale, alarm alerts, the Moving templates, Park to edit or a confirm sheet
  ([Drive modes §8.1][dm-8.1] R3, [App model §15][am-15] 15.8). Disabling or uninstalling
  an app never removes a safety item: the OS draws them itself.
- **Apps draw no approvals.** Every confirm and permission sheet here is drawn by the OS,
  over the app, in OS style ([App model §8][am-8]).
- **The gate decides.** A permission an app holds only narrows; every car action still
  passes the node's gate, which re-checks role, category, tier, transport and Parked
  ([ADR-0033][adr-33] §3).
- **Honest states and real data.** Example rows use the Discovery 2 Td5 pack. Live values
  are written ‹like this›; draw them with neutral sample text, never a fake reading.
- **Look.** Lists of ListRow on `surface-1` Cards; one primary Button per screen; head units
  use 76 px rows and ≥ 18 px type; no glow on head units ([visual §1][vds-1],
  [visual §8][vds-8]). Shared new components: **Switch** (from the Settings brief) and
  **SetupStepper** (from the onboarding brief).

## 3. Screens in this file

| Screen id | Name | Tag | Owner |
|---|---|---|---|
| `app-list` | Apps (Settings → Apps), two variants | Proposed | os |
| `app-info` | App info | Proposed | os |
| `app-info-actions` | Force stop and Disable sheets | Proposed | os |

### app-list — Apps  [Proposed]
- **Owner:** os
- **Why the app needs it:** Ostler is now an OS whose features are all apps, so system
  Settings needs one list of what is installed, as Android's Settings → Apps; the approved
  catalogue (More → Add-ons) becomes the Store's Installed tab.
- **Purpose:** every installed app, integration and vehicle pack, each row opening App info.
- **Opens from → goes to:** Settings → Apps; the app drawer's long-press **App info** goes
  past it. Rows → `app-info`; **Get more apps** → the Store (`70-store-*`); the
  Integrations row (variant A) → `app-integrations`. Back → Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day for both variants; hu7 Night (variant A); hu7 Night dim Moving (the
  Settings lock); tablet Night (list 360 px left, App info right).
- **Content (top to bottom):**
  1. Title "Apps"; search field "Search apps" (Parked only on head units).
  2. Sort and filter bar: Segmented **Name · Recently used · Size**; filter Chips
     **All · Enabled · Disabled · Needs attention**; Switch **Show system apps** (off:
     Settings, Store and the launcher are hidden from the list, never from the drawer).
  3. **Needs attention** group, only when non-empty: one ListRow per app with a status
     Chip: "Needs update" (`warn`), "Stopped" (`alarm`), "Set-up not finished" (`warn`),
     "Not available on this car" (`text-2`).
  4. **Variant A, one list (ADR-0042 item 98):** one group "Installed", A to Z. Each row:
     the app's icon (Material Symbols), name, one meta line ("‹version› · ‹size› on the
     Brain"), a kind Chip **App**, **Integration** or **Vehicle pack**, and a chevron.
     Example rows: Diagnostics (App), Trips (App), Security (App), Maintenance (App),
     Land Rover Discovery 2 (Td5) (Vehicle pack, meta "1 car · TD5, SLABS, BCU, ACE, EAT,
     SRS"), LubeLogger bridge (Integration, meta "Set-up not finished"). A last row
     **Integrations** "Discovered, errors and devices" → `app-integrations`.
  5. **Variant B, two tabs (Home Assistant's split):** a TabBar **Apps · Integrations**.
     Apps holds feature apps only; Integrations holds vehicle packs and bridges and is the
     `app-integrations` page itself, with its Discovered row on top.
  6. Footer: Button **Get more apps** (secondary) → the Store.
- **States:** loading (row skeletons); empty, flavour with no apps: "No apps yet. The OS
  still shows faults and alarms." with **Open the Store**; offline: rows read from the
  Brain show "Needs the Brain"; no vehicle: vehicle packs show "No car uses this pack";
  Parked full; Idling as Parked with Park evidence; Moving: the Settings lock; Passenger:
  not offered; locked (signed out): not shown.
- **Safety and driving rules:** the Settings lock ([UI §12.1][ui-12.1]); search is text
  entry, Parked only.
- **Components:** ListRow, Chip (kind, status), Segmented, Switch (new), search field (new),
  TabBar (variant B), Button.
- **Spec refs:** [App model §14][am-14] (14.1–14.2) · [UI §12.4][ui-12.4] ·
  [ADR-0042][adr-42] HA direction item 98 · [HA integrations §4.2][ha-4.2] ·
  [HA integrations §5][ha-5] (C1, Decide 2).
- **Open questions:** one list with a kind label (variant A, as ADR-0042 item 98 reads) or
  separate Apps and Integrations tabs (variant B, as the HA research recommends)? Draw both.

### app-info — App info  [Proposed]
- **Owner:** os
- **Why the app needs it:** each app needs one OS page that says what it is, what it may
  touch and how to stop or remove it, the same for every app (Android's App info).
- **Purpose:** one page per installed app: actions, access, notifications, storage, power,
  version, logs, links, widgets.
- **Opens from → goes to:** `app-list` rows; long-press an app icon in the app drawer or a
  dock slot → **App info**; an app's overflow menu → **App info**; error cards
  (`app-error-*`). Rows → the B-part pages; **Open** → the app; **App settings** → the
  app's own settings (its area, for example `diagnose-app-settings`). Back → where it
  came from.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the lock), tablet Night (two panes).
- **Content (top to bottom),** example **Diagnostics**:
  1. **Header:** icon (64 px phone, 96 px head unit), name "Diagnostics", publisher line
     "openostler · First party", Chips **App** and "‹version›".
  2. **Action row** of four Buttons with icon and word: **Open** (`open_in_new`),
     **Disable** (`block`), **Uninstall** (`delete`), **Force stop** (`dangerous`).
     System apps show **Disable** and **Uninstall** disabled with "Part of the OS".
  3. **Status line** when needed (Card in a tone): "Stopped · ‹time›" (`alarm-bg`),
     "Update available" (`warn-bg`), "Set-up not finished · Continue set-up" (`warn-bg`).
  4. **App settings** ListRow (`tune`) "Settings inside the app" → the app's own page.
  5. **Permissions and data** ListRow (`shield_person`) meta "Reads faults, live data ·
     may ask for 3 kinds of car action" → `app-info-permissions`.
  6. **Notifications** (`notifications`) meta "3 of 4 channels on" → `app-info-notifications`.
  7. **Storage and cache** (`storage`) meta "‹size› on the Brain" → `app-info-storage`.
  8. **Power use** (`battery_charging_full`) meta "Low · woke the Brain ‹n› times this
     week" → `app-info-power`.
  9. **Open by default** (`link`) meta "Opens fault links" → `app-info-defaults`.
  10. **Widgets and shortcuts** (`widgets`) meta "4 widgets · 2 shortcuts" →
      `app-info-provides`.
  11. **Version and source** (`info`) meta "‹version› · licence · publisher" →
      `app-info-version`.
  12. **App log** (`receipt_long`) meta "Last error: none" → `app-info-logs`.
  13. **Set up again** (`restart_alt`) → the app's setup flow (`app-flow-*`), when it has one;
      **Configure** (`settings_suggest`) → its options flow (`app-options-flow`).
  14. Footer, small `text-3`: "Installed ‹date› · Kind: App · Trust: First party".
- **Variants:** an **Integration** (LubeLogger bridge): no **Open** (it has no pages);
  **Configure** promoted under the header; Widgets row absent. A **Vehicle pack**
  (Discovery 2): no **Open**; rows **Cars using this pack** "Discovery 2 Td5" and
  **Integration entry** → `app-integration-entry`. A **system app** (Settings): only
  Notifications, Storage, Version and App log.
- **States:** loading; disabled app: header greyed, Chip "Disabled", **Enable** replaces
  Disable, other rows read-only; not owner: action row hidden, rows read-only with
  "Owner only"; offline: Brain-held rows "Needs the Brain"; remote path: "Local links
  only" on every button; not available on this car: Card "Not available on this car" with
  the reason (`app-error-incompatible`); Moving: the Settings lock; Passenger: not offered.
- **Safety and driving rules:** the Settings lock; owner and local link for the action row
  ([UI §12.4][ui-12.4]); disabling Diagnostics leaves the fault telltale and its sheet in
  place, drawn by the OS ([Drive modes §8.1][dm-8.1] R3).
- **Components:** ListRow, Button (with icon), Chip (kind, version, status), Card (tone).
- **Spec refs:** [App model §5][am-5] (lifecycle) · [App model §4.2][am-4.2] ·
  [App model §14][am-14] · [App model §15][am-15] 15.8 · [UI §12.4][ui-12.4].
- **Open questions:** should **Force stop** exist at all for bundled apps, which run in the
  shell's realm (it would reload the app's views, not kill a process)? The brief draws it
  as "Stop and reload".

### app-info-actions — Force stop and Disable sheets  [Proposed]
- **Owner:** os
- **Why the app needs it:** stopping or turning off an app changes what the home pages and
  dock show, so the owner sees the effect before it happens.
- **Purpose:** confirm Force stop, Disable and Enable.
- **Opens from → goes to:** `app-info` action row → the sheet → back to `app-info` with a
  toast. Uninstall has its own sheet (`app-uninstall`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):**
  1. **Force stop** sheet: title "Stop Diagnostics?"; line "Its pages and widgets reload.
     A scan in progress stops; nothing already sent to the car is undone."; Buttons
     **Cancel** (focused) and **Stop** (danger).
  2. **Disable** sheet: title "Turn off Diagnostics?"; what changes, as ListRows: "Its 4
     widgets on 2 home pages show 'App turned off'", "Its dock slot keeps its place, greyed",
     "Its notifications stop"; what stays, with a `shield` icon: "Fault warnings and the
     telltale stay: the OS shows them"; Buttons **Cancel** (focused) and **Turn off**.
  3. **Enable**: no sheet; a toast "Diagnostics turned on".
- **States:** a Tier 2 test or Tier 3 procedure running in this app: both sheets say "Stop
  the SLABS pump test first" and offer only **Go to test**; not owner: never opens.
- **Safety and driving rules:** Cancel focused; a running action is stopped only through
  its own Stop (ActiveTestBanner), never by disabling the app.
- **Components:** Sheet, ListRow, Button (danger), toast (`ia-toast`).
- **Spec refs:** [App model §5][am-5] · [App model §15][am-15] 15.6 and 15.8 ·
  [UI §7][ui-7].
- **Open questions:** none.

<!-- refs -->
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-42]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md#home-assistant-direction-decision-list-items-97101-accepted-direction
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[am-8]: ../../../../specs/2026-10-06-app-model-design.md#8-explicit-non-goals-and-hard-lines
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ha-4.2]: ../../../../references/research/ha_integrations_dashboards.md#42-integrations-versus-add-ons
[ha-5]: ../../../../references/research/ha_integrations_dashboards.md#5-copy--avoid--decide-for-ostler
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
