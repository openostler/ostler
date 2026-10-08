---
title: "Designer brief 40-c — Home, the app drawer, Hidden apps, edit-mode safety rules and the item sheet"
area: references
status: draft
version: 0.4
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-shell-input-design.md]
summary: >
  Third shell brief file, revised for the owner's Android-style direction. It covers Home
  (the first home page: a widget grid with the Discovery 2 Td5 vehicle card, the warnings
  card that can move but never go, the last trip from the Trips app, the Drive widget, app
  cards and the empty-state card that points to the Store), the app drawer (was More: every
  app not in the dock, Settings, and the Edit layout and Reset layout rows that cannot be
  hidden), Hidden apps, the OS rules for Home edit mode (the launcher brief, 45-launcher,
  draws edit mode itself) and the item sheet's safety-item and anchor variants. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 40-c — Home, app drawer and edit-mode rules

Back to [40-a](40-drive-a.md) for the terms and the file list.

### home — Home  [Existing]
- **Purpose:** the landing page and the root of Back: the car's state at a glance and a way
  into the Drive home pages. In the new direction it is the first home page of the launcher.
- **Owner:** os
- **Opens from → goes to:** app start when Parked and not armed; Back from anywhere. Widgets
  open their apps (Diagnostics, Trips, Security, Maintenance …).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (with `bg-glow`) and Day; hu7 Night Parked; huwide Night; hu5 Night.
- **Content (default widgets for a full install; a bare OS shows only the OS widgets):**
  1. **Warnings card** (OS safety widget): a tone card only when abnormal, for example
     `error` "2 faults · Engine (Td5)" with "Open faults"; healthy, a quiet "No faults" line.
  2. **Vehicle card:** the owner's vehicle name and "Land Rover Discovery 2 · Td5"; one
     HeroStat by role (battery "13.9 V" Parked, or coolant "88 °C" when warm); a 3-column stat
     grid in role order: speed, rpm, coolant, battery, fuel (the D2 has no fuel level, so the
     tile is the "Fuel now" economy figure in L/mil, marked `candidate`), then **Boost**
     ("1.2 bar", from `manifold_press`). Values outside the session read "Not in this
     session · Read by Engine (Td5)", never 0.
  3. **Security alert card** (OS safety widget, only with a node and the Security app).
  4. **Last trip** (Trips app widget): static dark map thumbnail, title, date, duration and
     distance (`type-num-l`).
  5. **Car battery** card on the phone only (the phone strip has no 12 V chip).
  6. **App cards** when installed: Maintenance "Oil service due in 300 km", a Social ride
     card, Community replies, Navigation "Navigate home".
  7. **Empty-state card** (no optional app installed): "Track maintenance", "Share drives
     with friends", **Open the Store**; dismissible, not a widget.
  8. Unknown-vehicle banner: "Help decode it".
- **Grid per class:** HU-5 and HU-7 4 × 4 cells; HU-9/10 vehicle card 40 % plus 2 × 2;
  HU-wide the vehicle pane (520 px) is always on, so Home omits the vehicle card; phone 4
  columns. Drag, resize and adding pages: 45-launcher.
- **States:** empty: vehicle card plus the empty-state card. Loading: skeletons. Offline: last
  values grey with age. No vehicle: "Add a vehicle". Brain asleep: drawn from the node's
  retained data. Parked, Idling: full. Moving: head units land on the Drive home pages; the
  phone shows the Moving banner.
- **Safety and driving rules:** the warnings card and the Security alert card may move,
  resize and be restyled, never removed, hidden or covered ([Drive modes §7.2][dm-7.2]); the
  empty-state card never shows on a head unit while Moving ([UI §12.4][ui-12.4]).
- **Components:** Card, Card (tone), HeroStat, StatTile.
- **Spec refs:** [UI §3.4][ui-3.4] · [UI §5.4][ui-5.4] · [UI §12.4][ui-12.4] ·
  [Drive modes §7.2][dm-7.2] · [visual §10][vds-10] · [app model §15.4][am-15.4].
- **Open questions:** **Decided (item 16):** the Drive button is retired, so Home has no
  Drive widget; the launcher migration drops it ([launcher §13][lw-13]). The "Home" title
  goes as visual §10 says.

### more — App drawer (was More)  [Existing]
- **Purpose:** every installed app not in the dock, plus Settings, in one place.
- **Owner:** os
- **Opens from → goes to:** the app-drawer dock slot (always present); `menu` → the drawer
  with the D-pad; an app opens its page; Settings opens system Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day; hu7 Night Parked; hu7 Night-dim Moving (locked).
- **Content (top to bottom):**
  1. **Apps:** every installed app not in the dock, each with its (or the user's) icon and
     name: for example Security (if not pinned), Maintenance, Social, Map, Navigation,
     Phone, Media, Community, Store; then **Hidden apps** (count) → `shell-hidden-pages`.
  2. **Settings**, the Settings app, always in the drawer (decided, item 57) (system Settings: Garage, Network, Places, Integrations, Privacy, App info
     per app, About with the version line; the 90-appframe files draw App info).
  3. **Edit layout** (cannot be hidden; the D-pad way into edit mode).
  4. **Reset layout** (cannot be hidden, moved out or renamed) → `shell-reset-confirm`;
     "Undo reset" here for 7 days after a reset.
- **States:** bare OS: only Settings, Store, Edit layout and Reset layout. Parked: full.
  Moving on a head unit: a `short_list` of ≤ 6 driving apps ([launcher §5.2][lw-5.2]);
  Edit and Reset say "Park to edit".
- **Safety and driving rules:** the drawer is a default anchor: it can be moved, renamed,
  re-iconed and hidden while the recovery path stays ([Drive modes §8.1][dm-8.1] R9–R11).
- **Components:** ListRow or app-icon grid (45-launcher decides). Material Symbols.
- **Spec refs:** [UI §3.4][ui-3.4] · [UI §12.4][ui-12.4] · [UI §13.4][ui-13.4] ·
  [Drive modes §7.3][dm-7.3] · [Drive modes §7.8][dm-7.8].
- **Open questions:** Phone & Comms §8 names "More → Settings → Alerts"; recommend Settings →
  Alerts.

### shell-hidden-pages — Hidden apps (was More → Hidden pages)  [New]
- **Purpose:** apps the user hid from the drawer, so nothing becomes unreachable.
- **Owner:** os
- **Opens from → goes to:** app drawer → Hidden apps; a row opens the app; **Show in drawer**
  moves it back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content:** title "Hidden apps"; one row per app: icon, name, **Show in drawer**; note
  "Hidden apps stay installed. To turn one off, open its App info."; empty "No hidden apps".
- **States:** Parked: full. Moving: locked view.
- **Safety and driving rules:** an edit: Park to edit on a head unit.
- **Components:** ListRow, Button.
- **Spec refs:** [Drive modes §7.7][dm-7.7] · [app model §15.8][am-15.8].
- **Open questions:** none.

### shell-home-edit — Home edit mode (OS rules)  [Existing]
- **Purpose:** the OS rules that edit mode must show; the look, drag and resize, page adding
  by dragging to the edge and the edit bar are drawn in the 45-launcher files.
- **Owner:** os
- **Opens from → goes to:** long-press 600 ms on an empty area or a widget, a long `ok` on a
  focused widget, or app drawer → Edit layout.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** the
  safety variants on hu7 Night.
- **Content the OS requires:** 1. Safety widgets (warnings card, Security alert card) show no
  remove control and say "Safety item: can move, can't be removed". 2. **Reset** is always in
  the edit bar. 3. Editing another class from a phone or desktop while that display is Moving
  shows "Applies when the car is parked". 4. D-pad: `ok` picks up (ring doubles), arrows
  move, `ok` drops (swap on occupied), `back` cancels; `back` with nothing picked asks
  "Discard changes?" with Cancel focused. 5. No jiggle or motion; resize by button on HU
  (76 px targets).
- **States:** Parked: full. Idling: with Park evidence. Moving: never on a head unit
  (`shell-park-to-edit`).
- **Safety and driving rules:** the draft autosaves; the live layout changes only on Done
  ([Drive modes §7.1][dm-7.1], [shell input §14][si-14]).
- **Components:** see 45-launcher.
- **Spec refs:** [Drive modes §7.1][dm-7.1] · [Drive modes §7.2][dm-7.2] · [UI §15.2][ui-15.2].
- **Open questions:** none.

### shell-item-sheet — Item sheet: safety and anchor variants  [New]
- **Purpose:** the per-item sheet in edit mode (Move, Size, Icon, Name, Hide or Remove,
  Replace with…, Settings, Use defaults); its general look is in 45-launcher, its OS
  variants are here.
- **Owner:** os
- **Opens from → goes to:** selecting an item in edit mode, or `menu` on a focused item;
  rows go to `shell-icon-picker`, `shell-name-edit`, the widget picker or the widget setup page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night safety item (warnings card); phone Day app-drawer anchor.
- **Content the OS requires:** rows that do not apply are absent, not greyed. **Safety item**
  (telltale chip, Security chip, warnings card, Security alert card): only Move (and Size for
  cards) plus "Safety item: can move, can't be removed". **Anchor** (app drawer, Back, Drive
  page chip): Move, Icon, Name (not for the Drive page chip, whose word is the page name),
  Use defaults; no Hide. A custom name shows "Custom name · default Trips" with **Use
  default name**.
- **States:** Moving: never open on a head unit. Error: "The fault telltale can move but
  can't be removed".
- **Safety and driving rules:** safety items never take icon, name or hide overrides
  ([Drive modes §4.5][dm-4.5], [Drive modes §8.1][dm-8.1] R3, R9).
- **Components:** Sheet, ListRow.
- **Spec refs:** [Drive modes §7.1][dm-7.1] · [Drive modes §7.7][dm-7.7] ·
  [app model §15.8][am-15.8].
- **Open questions:** none.

[am-15.4]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.8]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#45-rail-strip-and-overrides-v02
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-7.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#77-hide-replace-and-reachability-v02
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-13.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[vds-10]: ../../../../specs/2026-10-07-visual-design-system-design.md#10-before-and-after
[lw-13]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#13-the-format-ostlerlayout2-and-migration
[lw-5.2]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#52-the-drawer
