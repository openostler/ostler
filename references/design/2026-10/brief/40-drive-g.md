---
title: "Designer brief 40-g — Drive page chip and flat page list, Drive menu, Exit to Home while Moving, dusk suggestion, and OS rules for the page list and page editor"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-navigation-addon-design.md]
summary: >
  Drive control brief file, revised for the owner's Android-style direction: Drive home pages
  sit in one flat carousel with page dots, and presets only add pages to it (model in
  45-launcher-a). It keeps the safety and D-pad rules of the Drive page chip and its flat page
  list (tap cycles a rotation of up to four pages, long-press lists up to six, "Edit pages…"
  only when Parked), the Drive menu (up to six driver-safe rows, as built today and as the
  spec grows it, with app rows), the "Exit to Home" row, hidden while Moving (owner
  decision item 46), the one-time dusk suggestion for the Minimal page, and the
  OS rules for the Drive page list and page editor.
---

# 40-g — Page chip, Drive menu, page list and editor rules

Back to [40-a](40-drive-a.md) for the terms and the file list. The carousel model is in
[45-launcher-a](45-launcher-a.md); the pages are in
[40-e](40-drive-e.md) and [40-f](40-drive-f.md).

### drive-switcher — Drive page chip and flat page list (Moving and D-pad rules)  [Existing]
- **Purpose:** switch Drive home pages safely at speed. The chip, the flat page list and the
  page dots are drawn in [45-launcher-a](45-launcher-a.md); this block keeps the OS rules.
- **Owner:** os
- **Opens from → goes to:** the `drive_mode` chip in the Drive strip. Tap (or short `ok`) →
  next page in the one-tap cycle (at most 4 pages, item 45); long-press 600 ms (or long `ok`) → the flat page list; a row
  picks; **Edit pages…** → `drive-modes-list` (Parked only). A swipe or `left`/`right` moves
  to the neighbouring page in the one row.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving with the chip focused after `back`.
- **Content the OS requires:** 1. Chip word = the current page's name ("Cluster"), ≥ 48 px
  tall, 76 px target on HU; an anchor, never hidden, may sit anywhere in the strip. 2. Flat
  list (one flat row of pages, item 45) as a `short_list`: ≤ 6 rows, one level, names ≤ 30 characters, current page ticked,
  the rotation first (default HU: Cluster, Map, Tiles, Minimal). 3. **Edit pages…** only when
  Parked.
- **States:** Moving: tap cycles with no toast and no animation; the list has no Edit row
  (absent, not greyed). A page whose needs fail (Convoy pages with no ride, Split with no
  media app) is skipped by the chip, the swipe and the list. The current page is remembered
  per display, profile and vehicle; nothing switches by itself.
- **Safety and driving rules:** switching is allowed in any state and not logged in the trip;
  editing is Parked only ([Drive modes §6][dm-6], R1). While Moving `back` with nothing open
  moves focus to this chip wherever it sits ([shell input §14][si-14]).
- **Components:** Chip, `short_list` (ListRow ≤ 30 characters, tick).
- **Spec refs:** [Drive modes §6][dm-6] · [Drive modes §5.9][dm-5.9] · [UI §15.1][ui-15.1] ·
  [shell input §6][si-6].
- **Open questions:** the same block appears in 45-launcher-a; the brief link in the screen
  index should point to 45-launcher-a for the look and here for the rules.

### drive-menu — Drive menu  [Existing]
- **Purpose:** the driver-safe actions in Drive mode, reachable by `ok` with a D-pad.
- **Owner:** os
- **Opens from → goes to:** `ok` or `menu` in Drive mode with focus in the page; a row acts
  and closes; **Back to Drive** or `back` closes.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving (as built today); hu7 Night-dim Moving (spec rows with Navigation).
- **Content (as built today):** 1. **Mark** (`flag`; only while a recording can take one).
  2. **Drive page** with the current page on the right ("Cluster") → the flat page list. 3. **Exit
  to Home** (`home`; Parked only, hidden while Moving, see `drive-exit-home-moving`). 4. **Back to Drive** (`close`).
- **Content (spec default, as features arrive):** **Mark**, **Mute alerts** (state "On"),
  media **Play/Pause** and **Skip** (with a media source), **Climate** setpoint (Comfort;
  opens the `setpoint` template), **Arm** (Security; never disarm; state "Armed"), **Back to
  Drive**. App rows: Navigation **Mute voice**, **Skip to next point**, **End navigation**;
  Phone **Favourites** (a `short_list`).
- **Rules for rows:** ≤ 6 rows, one level, label plus state ≤ 30 characters (state ≤ 12, cut
  with "…"); with more candidates the first six of the display's order (set Parked only); no
  row that would need a confirm sheet while Moving.
- **States:** Moving: as above; a first tap focuses a row, a second activates. Parked: same
  rows; the order is editable Parked. No apps: OS rows only.
- **Safety and driving rules:** `short_list` limits ([UI §12.1][ui-12.1]); task ≤ 3 screens,
  ending in Drive mode.
- **Components:** `short_list`, ListRow (state text ≤ 12 characters).
- **Spec refs:** [shell input §6][si-6] · [app model §15.3][am-15.3] · [Navigation §5.6][nav-5.6].
- **Open questions:** **Decided (item 46):** the Exit to Home row is hidden while Moving.

### drive-exit-home-moving — "Exit to Home" while Moving  [New]
- **Purpose:** define what happens when the driver tries to leave Drive mode at speed.
- **Owner:** os
- **Opens from → goes to:** Drive menu **Exit to Home** (Parked only) → Home. While Moving
  there is no way to Home: the strip's Back chip only focuses the Drive page chip.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim Moving (the
  Drive menu without the row); hu7 Night Parked (the menu with the row).
- **Content:** **Row hidden while Moving.** The Drive menu lists its other rows only; the
  row is absent, not greyed. Parked, the row opens Home.
- **States:** Parked: the row exists and opens Home. Moving: the row is absent.
- **Safety and driving rules:** stays within the templates and the 3-screen task depth
  ([UI §12.1][ui-12.1]); `back` never leaves Drive mode while Moving ([shell input §4.3][si-4.3]).
- **Components:** `short_list` row.
- **Spec refs:** [shell input §6][si-6] · [shell input §4.3][si-4.3] · [UI §3.4][ui-3.4] · [launcher §4.3][lw-4.3].
- **Open questions:** **Decided (item 46):** hide the row while Moving (option A).

### drive-dusk-suggest — Minimal / Night suggested at dusk  [New]
- **Purpose:** offer the calm night page once at dusk, never switching by itself.
- **Owner:** os
- **Opens from → goes to:** dusk (Auto theme turns dark) while a page other than Minimal is shown;
  **Switch** → Minimal / Night; **Not now** dismisses for this trip.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night Parked; hu7
  Night-dim Moving.
- **Content:** `alert_card`: icon `bedtime`, line 1 "It's getting dark", line 2 "Try
  Minimal / Night?", buttons **Switch** and **Not now** (Not now focused).
- **States:** shown once per trip; never if Minimal is already active or not in the user's
  pages.
- **Safety and driving rules:** `alert_card` limits; switching pages is allowed while Moving;
  never applied automatically ([Drive modes §6][dm-6], Decision 6).
- **Components:** `alert_card`, Button.
- **Spec refs:** [Drive modes §6][dm-6] · [Drive modes §5.7][dm-5.7].
- **Open questions:** suggest it Parked only (at the next stop after dusk), or also as an
  alert card while Moving? Recommend Parked only.

### drive-modes-list — Drive page list (OS rules)  [Existing]
- **Purpose:** manage Drive home pages and the rotation; the list's look, adding pages by
  dragging to the edge and the dashboard builder wizard are in the 45-launcher files.
- **Owner:** os
- **Opens from → goes to:** **Edit pages…** in the chip's list; app drawer → Edit layout →
  Drive; Share → `drive-layout-import`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked.
- **Content the OS requires:** the rotation holds ≤ 4 pages; a preset only adds pages
  to the one row, and its pages can be hidden; pages that need an app say so ("Needs the Social app", "Needs a media app", "Only
  during a ride"); **Update from preset** appears when a preset is newer.
- **States:** Moving: locked view with Open on phone.
- **Safety and driving rules:** R1 Park to edit ([Drive modes §8.1][dm-8.1]).
- **Components:** see 45-launcher.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §8.4][dm-8.4].
- **Open questions:** none.

### drive-mode-editor — Drive page editor (OS rules)  [Existing]
- **Purpose:** the OS rules that keep every edited Drive page drivable; grid, drag and
  resize are drawn in 45-launcher.
- **Owner:** os
- **Opens from → goes to:** a page in the list or long-press on a Drive page (Parked); a
  widget → its setup page (`drive-widget-settings`); **Preview** → `drive-mode-preview`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (Dashboard · Cluster) showing the Moving strip.
- **Content the OS requires:** 1. A **Moving strip** under the grid: the widgets shown while
  Moving, in order, drag to reorder, `push_pin` to add or remove; counter "Moving: 5 of 6
  tiles, 0 of 2 panes". 2. Widgets with `moving: false` marked "Parked only". 3. **Save**
  runs the validator; a failure says "Fix for driving first" and names the class and rule.
- **States:** saving, saved, refused. Moving: locked view.
- **Safety and driving rules:** a saved page is always drivable; validator and renderer share
  one implementation ([Drive modes §8.2][dm-8.2]).
- **Components:** Chip (Moving counter), ListRow (Moving strip).
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §8.2][dm-8.2].
- **Open questions:** none.

[am-15.3]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-5.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#57-minimal--night
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[dm-6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#6-the-switcher
[dm-7.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[dm-8.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[nav-5.6]: ../../../../specs/2026-10-07-navigation-addon-design.md#56-drive-menu-rows
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[si-4.3]: ../../../../specs/2026-10-07-shell-input-design.md#43-back-and-menu
[si-6]: ../../../../specs/2026-10-07-shell-input-design.md#6-drive-mode
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-15.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#151-drive-modes-changes-123
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[lw-4.3]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#43-drive-mode-is-the-carousel-while-moving
