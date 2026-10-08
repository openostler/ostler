---
title: "Designer brief 45-b — launcher: the app drawer, the app menu, folders and app shortcuts"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Second launcher brief file. It covers the app drawer (re-expressing the existing More
  screen as an Android-style alphabetical grid with search and category tabs), the app menu
  that a long-press on any app icon opens (app shortcuts, App info, Add to home, Add to dock,
  Hide, Uninstall), folders on home pages and in the dock, and the app shortcut picker that
  puts an app's shortcut, such as Diagnostics "Read faults" or Trips "Last trip", on a home
  page. Shortcuts open Parked views only and never act on the car by themselves. Examples
  use the apps of a full Discovery 2 install. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 45-b — App drawer, app menu, folders and app shortcuts

Back to [45-a](45-launcher-a.md) for the terms and the file list. The OS rules for the
drawer (anchors, Edit layout and Reset layout rows) are in 40-drive-c; this file draws the
look and the gestures.

### more — App drawer  [Existing]
- **Purpose:** every installed app in one A-to-Z grid with search: Android's "All apps".
- **Owner:** os
- **Opens from → goes to:** the App drawer dock slot; on phone also a swipe up from the
  home page; D-pad `menu` → drawer. A tap opens the app; a long-press opens
  `launcher-app-menu`; **Hidden apps** opens `shell-hidden-pages` (40-drive-c); **Settings**
  opens system Settings; **Store** opens the Store app (70-store files).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (full sheet); phone Day; hu7 Night (passenger-side panel, 4 columns); hu7
  Night-dim Moving (driving-apps list); huwide Night.
- **Content (top to bottom):**
  1. **Search** field "Search apps" (Parked only on HU; on phone always). Results show apps,
     then app shortcuts ("Read faults · Diagnostics"), then settings rows ("Units ·
     Settings").
  2. **Tabs** (Segmented): **All** · **Car** · **Media** · **Tools**. Categories come from
     each app's manifest; with fewer than eight apps the tabs are hidden.
  3. **Suggested row** (optional, off by default): the four apps used most on this display.
  4. **Grid A to Z**: App icon + name, 4 columns on phone, 4 on HU-7, 6 on HU-wide. A full
     D2 install: Audio, Camera, Community, Decode lab, Diagnostics, Maintenance, Map, Media,
     Navigation, Phone, Radio, Security, Social, Store, Settings, Trips. A letter index
     on the passenger edge on phone.
  5. Footer rows that never hide: **Hidden apps (2)**, **Edit layout**, **Reset layout**
     (40-drive-c owns their rules).
- **States:** bare OS: Settings and Store only, and a card "Your car has no apps yet ·
  Open Store". Loading: icon skeletons. App updating: a ring on its icon, "Updating".
  App stopped: icon greyed, "Stopped · App info". Offline: Store row says "Offline".
  Parked: full. Moving (HU): a `short_list` of up to six driving apps (default Media, Radio,
  Phone, Navigation, Map, Diagnostics), each opening its Moving view; nothing else, no greyed
  rows ([launcher §5.2][lw-5.2]). Passenger: phone shows the Moving banner over the drawer.
- **Safety and driving rules:** the drawer is a default anchor: movable, renamable,
  re-iconable, hideable while the recovery path stays ([Drive modes §8.1][dm-8.1] R9–R11). An app locked by the driving state
  still shows and opens its locked view. Settings and Store are system apps, always in the drawer
  and never hidden (item 57). No text entry while Moving.
- **Components:** Sheet (phone full height), App icon (new), Segmented (tabs), text field
  (search), ListRow (footer).
- **Spec refs:** [UI §3.4][ui-3.4] · [UI §12.4][ui-12.4] · [Drive modes §7.7][dm-7.7] ·
  [Drive modes §7.8][dm-7.8] · [launcher §5.2][lw-5.2] · [app UI model §10][ua-10].
- **Open questions:** (1) **Decided ([app UI model §10][ua-10]):** categories come from the
  manifest's `contributes.drawer.category`. (2) Suggested row: keep or drop?

### launcher-app-menu — App menu (long-press an app icon)  [New]
- **Purpose:** quick actions for one app, from the drawer, a home page or the dock.
- **Owner:** os
- **Opens from → goes to:** long-press 600 ms (or a long `ok`) on an app icon. Rows go to
  the app's shortcut route, App info (90-appframe files), the home page with the icon
  placed, the dock editor, or the uninstall confirm.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night over the drawer; hu7 Night over a home page.
- **Content:** a popup Card next to the icon (phone) or a passenger-side Sheet (HU):
  1. Header: icon, app name, a one-line state ("Diagnostics · 2 faults").
  2. **App shortcuts** (up to four, from the app's manifest): Diagnostics "Read faults",
     "Live data", "Scan all"; Trips "Last trip", "Start a mark"; Map "Where I parked". Each
     row has a drag handle: drag it to a home page to place it (`launcher-shortcut-picker`).
  3. **Add to home**, **Add to dock**, **Hide**, **App info** (`info`), **Uninstall**
     (absent for system apps such as Settings and the Store; on the phone it disables a
     bundled app and deletes its data, item 11; a confirm Sheet with Cancel focused:
     "Uninstall Social? Its widgets and shortcuts leave your home pages.").
- **States:** Parked: full. Moving (HU): the long-press shows "Park to edit"; no menu.
  Offline: Uninstall still works locally; "Updates when back online". App stopped: only
  App info and Uninstall.
- **Safety and driving rules:** an edit, so Park to edit on HU ([Drive modes §8.1][dm-8.1]
  R1). Uninstalling the Security app is refused while the car is armed (item 62), and never
  removes the alarm chip while a node is fitted (40-drive-a). Shortcuts never start a car action without the action's own confirm.
- **Components:** Card (popup), Sheet, ListRow (drag handle), Button (danger for Uninstall).
- **Spec refs:** [Drive modes §7.7][dm-7.7] · [app model §15][am-15] · [UI §7][ui-7] · [launcher §5.2][lw-5.2] · [launcher §5.3][lw-5.3] · [app UI model §2][ua-2].
- **Open questions:** **Decided ([app UI model §2][ua-2]):** apps declare static shortcuts
  in `contributes.shortcuts` and may publish up to four dynamic ones.

### launcher-folder — Folder  [New]
- **Purpose:** group app icons and shortcuts under one icon on a home page or in the dock.
- **Owner:** os
- **Opens from → goes to:** drop one app icon onto another in edit mode creates "Folder";
  a tap opens it as a Card over the page; a tap on an app inside opens it; Back closes.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night open folder; hu7 Night open folder; hu7 Night folder in the dock.
- **Content:**
  1. Closed: a 2×2 cluster of the first four icons on `surface-2`, label below.
  2. Open: a Card on `surface-2`, `radius-lg`; title field (≤ 30 characters, default from the
     apps' category, for example "Car"); a grid of up to 12 items.
  3. In edit mode: drag items in and out; drag the last item out removes the folder.
- **States:** empty is impossible (the folder goes with its last item). Moving (HU): a
  folder in the dock opens as a `short_list` of its driving items, or is hidden if it has
  none; folders are never in a Moving section. Rename: Parked only.
- **Safety and driving rules:** a folder can never hold the App drawer slot or a safety
  widget; renaming is text entry, Parked only ([UI §12.1][ui-12.1]).
- **Components:** Folder icon (new), Card, text field.
- **Spec refs:** [Drive modes §7.6][dm-7.6] · [Drive modes §8.1][dm-8.1] · [launcher §5.4][lw-5.4].
- **Open questions:** **Decided ([launcher §13][lw-13]):** `ostler.layout/2` has a `folder`
  item.

### launcher-shortcut-picker — App shortcuts on a home page  [New]
- **Purpose:** place one app shortcut, like Android's long-press shortcuts, as an icon on a
  home page or in the dock.
- **Owner:** os
- **Opens from → goes to:** drag a shortcut row from `launcher-app-menu`; the widget picker's
  "App shortcuts" group; the App shortcut widget (`widget-setup-app-shortcut`, 45-g). The
  placed shortcut opens that app route.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night picker; phone Night placed shortcut.
- **Content:**
  1. A list grouped by app: icon, shortcut name, one line ("Opens Diagnostics → Faults"):
     Diagnostics "Read faults", "Live data · Engine (Td5)", "SLABS ride height"; Trips
     "Last trip", "Export all"; Maintenance "Log fuel"; Navigation "Go home"; Phone "Call
     Sam" (a favourite).
  2. Placed: the app icon with a small shortcut glyph badge and the shortcut name.
- **States:** app uninstalled: the shortcut is removed with it. Route needs a node: a tap
  opens the page with "Needs the node". Moving (HU): a placed shortcut opens its target's
  Moving view; one whose target has none is not drawn.
- **Safety and driving rules:** a shortcut is navigation only: it opens a page and never
  starts an action (a "Clear faults" shortcut opens Diagnostics, where the confirm sheet
  still applies; [UI §7][ui-7], [Drive modes §8.1][dm-8.1] R6).
- **Components:** ListRow, App icon with shortcut badge (new variant), Sheet.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [app model §15][am-15] · [launcher §5.3][lw-5.3].
- **Open questions:** **Decided ([launcher §5.3][lw-5.3]):** a shortcut may sit in a Moving
  section as one tile only when its target has a Moving view; otherwise it is refused there.

<!-- links -->
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-7.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#77-hide-replace-and-reachability-v02
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[lw-5.2]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#52-the-drawer
[ua-10]: ../../../../specs/2026-10-07-app-ui-model-design.md#10-manifest-schema-2
[lw-5.3]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#53-app-shortcuts
[ua-2]: ../../../../specs/2026-10-07-app-ui-model-design.md#2-what-an-app-contributes
[lw-5.4]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#54-folders
[lw-13]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#13-the-format-ostlerlayout2-and-migration
