---
title: "Designer brief 45-c — launcher: the launcher menu, edit mode, the item popup and widget resize"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Third launcher brief file: editing the home pages the Android way. It covers the launcher
  menu that a long-press on empty space opens (Wallpaper & style, Widgets, Home settings,
  Build dashboards, Edit pages), edit mode itself (re-expressing shell-home-edit: drag, drop
  to swap, drag to the screen edge to make a new page, delete an empty page, the edit bar,
  undo), the popup that a long-press on a widget or icon opens (Remove, Settings, Resize,
  App info) and the resize frame with handles on touch screens and a size button on head
  units. Every editor is Park to edit on a driver-facing display.
---

# 45-c — Launcher menu, edit mode, item popup and resize

Back to [45-a](45-launcher-a.md) for the terms. The OS rules that edit mode must show
(Park to edit, safety items, the item sheet, the Reset confirm) are in 40-drive-b, 40-drive-c
and 40-drive-d; this file draws the launcher look and flow.

**Park to edit, once for this file.** On a driver-facing display, every screen here needs
Parked (or Idling with Park evidence). While Moving, a long-press shows only the "Park to
edit" toast for 3 s (`shell-park-to-edit`, 40-drive-b); entering Moving while editing keeps
the draft and offers "Finish editing when parked" ([Drive modes §8.1][dm-8.1] R1,
[Drive modes §7.1][dm-7.1]). Phones, desktops and passenger-only screens may edit at any time;
a change for a Moving display applies at its next Parked (R7).

### launcher-menu — Launcher menu (long-press empty space)  [Proposed]
- **Why the app needs it:** Android's long-press on empty space is the one way into
  wallpaper, widgets and home settings; the approved spec opens edit mode directly and has
  no place for the theme wizard or the dashboard builder.
- **Purpose:** the small menu that leads to every launcher setting.
- **Owner:** os
- **Opens from → goes to:** long-press 600 ms on an empty cell, the page dots or the empty
  part of the dock; a long `ok` on an empty focused cell. Rows go to the theme wizard
  (`launcher-theme`, 45-j), the widget picker (`shell-widget-picker`, 45-d), Home settings
  (`launcher-home-settings`, 45-k), the dashboard builder (`launcher-builder-apps`, 45-i),
  the home pages list (`drive-modes-list`, 45-h) or edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (popup at the finger); hu7 Night (passenger-side card); phone Day.
- **Content:** a popup Card with five rows, icon + word: **Wallpaper & style** `palette` ·
  **Widgets** `widgets` · **Home settings** `settings` · **Build dashboards**
  `dashboard_customize` · **Edit pages** `view_carousel`. The page behind enters edit mode
  (cell outlines) at the same time, so dragging works straight away.
- **States:** Parked: full. Moving: never shown on HU ("Park to edit"). Lock car layouts on
  and not the owner: only Wallpaper & style is offered greyed, with "Only the owner can edit
  this screen".
- **Safety and driving rules:** this menu and edit mode are always reachable (R10); no row
  is hideable.
- **Components:** Card (popup), ListRow.
- **Spec refs:** [Drive modes §7.1][dm-7.1] · [Drive modes §8.1][dm-8.1].
- **Open questions:** should Reset layout also be a row here? It is already in the edit bar,
  the app drawer and the Connection sheet.

### shell-home-edit — Edit mode  [Existing]
- **Purpose:** arrange widgets, shortcuts, folders and pages: drag, drop, resize, remove and
  add pages, Android style.
- **Owner:** os
- **Opens from → goes to:** the launcher menu; long-press on a widget or icon (that item
  picked up); app drawer → **Edit layout** (D-pad way in). **Done** saves and returns to the
  page; **Cancel** asks "Discard changes?" with Cancel focused.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with a gauge being dragged to the right edge; phone Night with the new empty page;
  phone Day; desktop Night editing the HU-7 class.
- **Content (top to bottom):**
  1. **Edit bar** (top of the page area, never in the strip): **Done**, **Cancel**, **Undo**,
     **Redo**, **Preview** (Parked and Moving side by side, `drive-mode-preview`, 45-h),
     **Reset**; tabs **Home pages · Dock · Strip**; on phone and desktop "Editing for: this
     screen" `expand_more` (HU-5, HU-7, HU-9/10, HU-wide, phone, tablet).
  2. **The page, shrunk to 88 %** with cell outlines and the neighbouring pages peeking at
     both edges, so the user sees where a drag can go.
  3. **Each item:** a frame and a drag handle `drag_indicator`; widgets also show the resize
     frame (`launcher-widget-resize`). Safety items show a small `lock` glyph and no remove.
  4. **Drag:** snaps to cells; dropping on an occupied cell **swaps**; dropping one app icon on
     another makes a folder; dragging to the left or right edge for 600 ms moves to the next
     page; dragging past the last page **creates a new page** (a dashed outline "New page").
  5. **Remove target** at the top while dragging: "Remove" `close` (for apps on a page:
     "Remove from home", never uninstall). Dropping a safety item there bounces it back with
     "Safety item: can move, can't be removed".
  6. **Empty page**: a centred **Delete page** `delete` button; a page with items has none
     (the user removes items first).
  7. **Add** `add` in the bar → `shell-widget-picker`.
  8. **Page dots** stay visible; the Drive marker `speed` under each page in the Drive
     rotation.
- **D-pad:** arrows move focus; `ok` picks up (focus ring doubles); arrows move cell by cell
  and across page edges; `ok` drops; `menu` opens the item popup; `back` cancels a move.
- **States:** saving: "Saving…" on Done; error: "Couldn't save. Your draft is kept."
  Offline: the draft is kept on the device. Editing another class: banner "Applies when the
  car is parked" when that display is Moving. A page with a Drive marker whose Moving section
  breaks a rule: a `warn` chip on its dot, "Fix for driving first" on Done. Moving: never
  shown on HU.
- **Safety and driving rules:** no jiggle and no motion beyond the drag itself; 76 px
  targets on HU; undo holds 50 steps; the draft autosaves; the live layout changes only on
  Done ([Drive modes §7.1][dm-7.1], [Drive modes §8.2][dm-8.2]).
- **Components:** Edit frame (new component), Button (Done, Cancel, Undo, Redo, Preview,
  Reset), Segmented (tabs, class picker), Page dots (new), Remove target (new component).
- **Spec refs:** [Drive modes §7.1][dm-7.1] · [Drive modes §7.2][dm-7.2] ·
  [UI §15.2][ui-15.2] · [shell input §14][si-14].
- **Open questions:** the spec says "no corner drag"; this brief adds handles on touch
  screens only (see `launcher-widget-resize`). Approve?

### launcher-item-popup — Item popup (long-press a widget or icon)  [Proposed]
- **Why the app needs it:** Android shows a small popup on long-press with Remove, App info
  and widget settings; the spec's item sheet holds the same rows but needs a second tap.
- **Purpose:** the fast actions on one placed item while it is picked up.
- **Owner:** os
- **Opens from → goes to:** long-press on a placed widget, shortcut or folder (Parked);
  `menu` on a focused item in edit mode. Rows go to the widget setup page (45-d), App info
  (90-appframe files), the item sheet (`shell-item-sheet`, 40-drive-c) or remove.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night on a gauge; hu7 Night on the warnings widget (safety variant).
- **Content:** a popup Card above the item (phone) or beside it on the passenger side (HU):
  1. **Settings** `tune` (widgets) → its setup page.
  2. **Resize** `open_in_full` → the resize frame.
  3. **Remove** `close` (absent for safety items).
  4. **App info** `info` → the widget's app ("Gauge · Starter widgets").
  5. **More…** → the item sheet (Icon, Name, Replace with…, Use defaults).
  Safety variant: Resize and More only, plus the line "Safety item: can move, can't be
  removed".
- **States:** widget stopped: Settings is replaced by **Restart widget**. Moving: never shown
  on HU.
- **Safety and driving rules:** as edit mode; safety items lose Remove, Icon and Name
  ([Drive modes §8.1][dm-8.1] R3).
- **Components:** Card (popup), ListRow.
- **Spec refs:** [Drive modes §7.1][dm-7.1] · [Drive modes §7.7][dm-7.7].
- **Open questions:** none.

### launcher-widget-resize — Widget resize frame  [Proposed]
- **Why the app needs it:** the owner asked for resize handles like Android; the approved
  spec resizes by a size button only, for gloves and 76 px targets.
- **Purpose:** change a widget's size within the sizes it supports.
- **Owner:** os
- **Opens from → goes to:** **Resize** in the item popup; selecting a widget in edit mode.
  Tapping outside or **Done** keeps the size.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night with handles; hu7 Night with the size button; desktop Night.
- **Content:**
  1. **Touch screens other than HU** (phone, tablet, desktop): an `accent` frame with four
     round handles (24 px drawn, 48 px hit) mid-edge; dragging snaps to the next supported
     size only (small 1×1, medium 2×1, wide 3×1, hero 2×2, [Drive modes §4.2][dm-4.2]).
  2. **Head units and D-pad:** a **Size** button on the frame that cycles small → medium →
     wide → hero, 76 px target; the current size word shows under it ("Medium").
  3. A live preview of the widget at the new size; a number that does not fit drops one type
     step, never clips.
  4. A size the widget does not support is skipped; neighbours are pushed or swapped, never
     overlapped.
- **States:** no room on the page: "No room for wide here" and the size stays. A Drive page's
  Moving section that would break: a `warn` line "Too big for the Moving section on HU-5".
  Moving: never shown on HU.
- **Safety and driving rules:** Moving tiles keep their per-class minimums
  ([Drive modes §4.4][dm-4.4], §8.1 R5).
- **Components:** Edit frame (new), Button (Size), Chip (size word).
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [Drive modes §4.4][dm-4.4] ·
  [Drive modes §7.1][dm-7.1].
- **Open questions:** approve handles on phone, tablet and desktop while head units keep the
  size button.

<!-- links -->
[dm-4.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#42-field-rules
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#77-hide-replace-and-reachability-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
