---
title: "Designer brief 40-d — edit-mode safety for the widget picker, icon picker, name editor, dock editor and strip editor, and the Reset confirm"
area: references
status: draft
version: 0.4
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-visual-design-system-design.md, references/research/ha_integrations_dashboards.md]
summary: >
  Fourth shell brief file, revised for the owner's Android-style direction. The launcher
  brief (45-launcher) now owns the look and flow of edit mode, the widget picker gallery,
  each widget's setup page and the wizards; this file keeps only what the OS enforces on
  those screens: Park to edit, safety items that cannot be removed, the dock's app-drawer
  anchor, text-entry limits and the per-class chip budget. It covers the widget picker and a
  approved "By signal" tab, the icon picker, the name editor, the dock editor (was the rail
  editor), the strip editor in full (the strip stays in this area) and the Reset to default
  and Discard changes confirms with the 7-day "Undo reset". Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 40-d — Edit-mode safety, strip editor and Reset

Back to [40-a](40-drive-a.md) for the terms and the file list. The launcher brief
(45-launcher files) draws edit mode, drag and resize, the widget picker gallery, widget setup
pages and the wizards; the blocks below give only the OS rules those screens must show.
Every screen here is an editor: Parked only on a head unit (or Idling with Park evidence);
while Moving the gesture shows `shell-park-to-edit` and these routes show
`shell-locked-view` ([Drive modes §8.1][dm-8.1] R1). Phone, desktop and passenger-only
displays may edit at any time.

### shell-widget-picker — Widget picker (OS rules)  [Existing]
- **Purpose:** choose a widget for a Home page or a Drive home page, or replace one.
- **Owner:** os
- **Opens from → goes to:** **+** in edit mode, **Replace with…**; then the widget's setup
  page. Gallery look and groups: see 45-launcher.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (passenger-side sheet, 520 px, no blur); phone Night.
- **Content the OS requires:** 1. Widgets come only from installed apps' `contributes.widgets`
  (for example the starter widget pack's Signal tile, Gauge and Hero; Social "Push to talk";
  Phone "Favourites"). 2. An app installed but not enabled: greyed, "Enable in App info".
  3. When the target is a Drive home page's Moving slot: widgets whose `moving` is false say
  "Parked only"; the media widget without a media app says "Needs a media app".
- **States:** Parked: full. Moving: locked view with Open on phone.
- **Safety and driving rules:** never offers anything that would break the Moving limits for
  the slot ([Drive modes §7.7][dm-7.7], [app model §15.2][am-15.2]).
- **Components:** Sheet, ListRow, Chip (sizes).
- **Spec refs:** [Drive modes §7.2][dm-7.2] · [app model §15.1][am-15.1].
- **Open questions:** **Decided (item 47):** the gallery has two tabs, By app and By signal
  ([launcher §7.1][lw-7.1]).

### shell-widget-picker-by-signal — Widget picker "By signal" tab  [New]
- **Purpose:** pick a signal first, then a suggested widget.
- **Owner:** os
- **Opens from → goes to:** the picker's tab bar **By app · By signal**; layout in 45-launcher.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content:** signals grouped by system with confidence words, as `drive-signal-picker`
  ([40-h](40-drive-h.md)): Engine (Td5) RPM, Speed, Coolant, Turbo pressure; SLABS Height
  left and right (raw), Transfer box low range; GPS Speed, Heading, Altitude.
- **States:** as the picker. **Safety and driving rules:** as the picker.
- **Components:** Segmented (tabs), ListRow.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [HA research][r-ha] · [launcher §7.1][lw-7.1].
- **Open questions:** **Decided (item 47):** the "By signal" tab is approved, beside By app.

### shell-icon-picker — Icon picker (OS rules)  [New]
- **Purpose:** re-icon an item from Material Symbols, an icon pack, emoji or the user's SVG.
- **Owner:** os
- **Opens from → goes to:** **Icon** in the item sheet; the icon-pack choice of the theme
  wizard is in 45-launcher.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (76 px grid), phone Day (48 px grid).
- **Content:** search; **Current** and **Default** pinned; theme groups of the curated
  Material Symbols catalogue (about 300), then **All symbols**, **Icon packs**, **Emoji** and
  **Upload SVG**; **Use default**.
- **States:** Parked: full. Moving: never on a head unit.
- **Safety and driving rules:** an uploaded SVG is sanitised (no scripts or URLs); a safety
  item's icon may be changed only under the Drive-mode render check ([Drive modes §7.6][dm-7.6];
  openness round).
- **Components:** Sheet, icon grid (new component), Button.
- **Spec refs:** [Drive modes §7.6][dm-7.6] · [visual §6][vds-6].
- **Open questions:** **Decided (item 49):** an icon pack is a glyph set mapped to Material
  Symbols names; safety icons never change ([launcher §11][lw-11]). *Amended (openness
  round): safety icons may be restyled under the render check.*

### shell-name-edit — Name editor (OS rules)  [New]
- **Purpose:** rename an item, safely for every screen size it shows on.
- **Owner:** os
- **Opens from → goes to:** **Name** in the item sheet; home-page and dashboard names.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night with keyboard; the refusal state.
- **Content:** field (`dir="auto"`), counter "7 of 12" (dock and strip) or "of 30" (widgets,
  pages, dashboards), **Save**, **Cancel**, **Use default name** ("Default: Trips").
- **States:** "Too long for this screen: phone" (class named), Save disabled. Moving: locked.
- **Safety and driving rules:** text entry Parked only; control and bidi-override characters
  stripped ([Drive modes §7.6][dm-7.6]).
- **Components:** text input, Button.
- **Spec refs:** [Drive modes §7.6][dm-7.6].
- **Open questions:** none.

### shell-rail-editor — Dock editor (was the rail editor)  [Existing]
- **Purpose:** choose and order the dock's slots (phone 5, HU-5 and HU-7 5, HU-9/10 6,
  HU-wide 7, tablet and desktop 7; decided, item 17).
- **Owner:** os
- **Opens from → goes to:** long-press on the dock; the Dock tab of edit mode; app drawer →
  Edit layout → Dock. Drag and drop look: 45-launcher.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (dock at the side, right on the D2); phone Night (dock at the bottom).
- **Content the OS requires:** 1. The class's slots; the **Home** and **app drawer** slots
  marked "Always in the dock" (anchors, item 16). 2. Any app, shortcut or folder in the
  others (pinned apps: Diagnostics, Trips, Security, Social, Map …). 3. No Drive button: it
  is retired (item 16). 4. Pinning with every slot full asks "The dock is full. Which one
  moves to the app drawer?" (the anchors are not offered).
- **States:** Parked: full. Moving: "Park to edit" 3 s. Error: "The app drawer must stay in
  the dock".
- **Safety and driving rules:** the class's slot cap; Home and the drawer exactly once; whatever leaves the
  dock stays in the app drawer; Home stays the landing page and root of Back; a pinned app
  keeps its driving rule ([Drive modes §7.3][dm-7.3]).
- **Components:** ListRow (drag handle), Button, Sheet.
- **Spec refs:** [Drive modes §7.3][dm-7.3] · [UI §15.2][ui-15.2] · [launcher §5.1][lw-5.1].
- **Open questions:** none.

### shell-strip-editor — Strip editor  [New]
- **Purpose:** order, show, hide, rename and re-icon strip chips, per class and context.
- **Owner:** os
- **Opens from → goes to:** long-press anywhere on the strip, or the Strip tab of edit mode;
  **Done** saves.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Drive context; phone Night normal context (budget full).
- **Content:**
  1. Context switch **Normal · Drive**.
  2. The strip in place, one row, same height, chips with drag handles; drop on a chip swaps.
  3. Counter "6 of 7 chips" (budgets: phone 5, HU-5 6, HU-7 7, HU-9/10 8, HU-wide, tablet
     and desktop 10).
  4. **Hidden** shelf below: hidden chips (for example Link, REC) with **Show**.
  5. Tags on chips: "Safety" (telltale, Security), "Always in Drive" (Back, Drive page chip).
  6. Device slot choice (climate or camera) links to Settings.
- **D-pad:** `ok` picks a chip, `left`/`right` move it, `ok` drops.
- **States:** budget full: extra chips fold into the overflow chip. Parked: full. Moving: "Park
  to edit". Error: "The fault telltale can move but can't be removed".
- **Safety and driving rules:** the strip stays one row with an overflow chip; safety chips
  count first and cannot be hidden; anchors may be hidden while the recovery path stays; apps
  may add status-only chips ([Drive modes §7.5][dm-7.5]; openness round).
- **Components:** Chip (with handle), Segmented, ListRow (Hidden shelf).
- **Spec refs:** [Drive modes §7.5][dm-7.5] · [Drive modes §4.5][dm-4.5] ·
  [shell input §14][si-14].
- **Open questions:** none.

### shell-reset-confirm — Reset to default / Discard changes  [Existing]
- **Purpose:** restore defaults safely, or throw away an unsaved edit.
- **Owner:** os
- **Opens from → goes to:** app drawer → Reset layout, the connection sheet's Reset layout
  row, edit mode's **Reset**; `back` in edit mode with nothing picked opens Discard. After a
  reset, **Undo reset** sits in the same row for 7 days.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  (Cancel focused); phone Day; the Undo reset row.
- **Content (Reset):** 1. Title "Reset layout?". 2. Scope: **This surface** (the dock, the
  strip, Home or the Drive carousel), **Everything on this screen** (dock,
  strip, Home, every Drive home page and its order, overrides and hidden items for this
  class); below, **All screen sizes**. 3. "Presets are not changed. You can undo this for 7
  days." 4. **Cancel** (focused) and **Reset**.
- **Content (Discard):** "Discard changes?" with **Cancel** (focused) and **Discard**.
- **States:** after reset: "Undo reset · until *date*". Moving on a head unit: "Park to
  edit". Error: server refusal in words.
- **Safety and driving rules:** Cancel focused; `ok` within 500 ms of opening is ignored
  ([shell input §7][si-7]); Reset is an edit, so Parked only on HU.
- **Components:** Sheet, Button (Cancel focused), Chip ("All screen sizes").
- **Spec refs:** [Drive modes §7.8][dm-7.8] · [shell input §7][si-7].
- **Open questions:** none.

[am-15.1]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.2]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#45-rail-strip-and-overrides-v02
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-7.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-7.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#75-strip-v02
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-7.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#77-hide-replace-and-reachability-v02
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[r-ha]: ../../../research/ha_integrations_dashboards.md#decide-recommendations-for-the-owner
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[lw-7.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#71-the-picker-gallery
[lw-11]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#11-the-theme-wizard
[lw-5.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#51-the-dock
