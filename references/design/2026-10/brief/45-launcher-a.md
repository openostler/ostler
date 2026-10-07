---
title: "Designer brief 45-a — launcher: the model, home pages, the Drive carousel, the dock and the dock editor"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  First of the launcher and widgets brief files (45-a to 45-k), written for the owner's
  Android-style direction: Ostler's launcher works like a phone launcher adapted to cars. It
  sets the terms (home pages in one flat carousel, the dock, the app drawer, widgets, app
  shortcuts, folders) and the file list, then gives the blocks for the home pages carousel
  (grid per layout class, page dots, default page, wallpaper layer), the Drive carousel of
  home pages on a head unit with its page chip and flat page list (re-expressing
  drive-switcher), the dock (re-expressing shell-rail: bottom on phones, driver side on head
  units) and the dock editor (shell-rail-editor). Examples use the Discovery 2 Td5 pack.
---

# 45-a — The launcher model, home pages, Drive carousel and dock

**Files in this set.** **45-a** model, home pages, Drive carousel, dock ·
[45-b](45-launcher-b.md) app drawer, app menu, folders, app shortcuts ·
[45-c](45-launcher-c.md) edit mode, launcher menu, item popup, resize ·
[45-d](45-launcher-d.md) widget picker and the widget setup frame ·
[45-e](45-launcher-e.md), [45-f](45-launcher-f.md), [45-g](45-launcher-g.md) one setup page
per starter widget · [45-h](45-launcher-h.md) home pages list, page editor, preview,
import, presets · [45-i](45-launcher-i.md) dashboard builder wizard ·
[45-j](45-launcher-j.md) and [45-k](45-launcher-k.md) theme wizard and Home settings.

**Who owns what.** The launcher is part of the OS (owner `os`). It draws the home pages,
dock, app drawer, edit mode, widget picker, widget setup frame, presets and both wizards.
Apps supply widgets, shortcuts and their own App info and setup flows (the `90-appframe-*`
files). The status strip, alerts, Park to edit, the locked view and the Moving templates
stay in the 40-drive files (40-drive-a to 40-drive-i); this set links them by file name only
and never changes a safety rule.

**Conventions.** The D2 is right-hand drive, so the dock sits on the **right** of a head
unit; draw a left-hand-drive frame only where noted. "HU" means every head-unit class.
Head units are always driver-facing ([UI §12.1][ui-12.1]). Phones are passenger devices
(Moving banner, not lockout). Approved specs still say rail, More, Drive mode and face; the
owner's direction of 2026-10-07 renames them dock, app drawer, Drive carousel and home page.

## The launcher model in one page

| Android launcher | Ostler launcher | Was (approved specs) |
|---|---|---|
| Home screen pages | **Home pages**: one flat carousel of grid pages; page 1 is Home | Home, Drive modes, faces |
| Hotseat | **Dock**: five slots, bottom on phone, driver side on HU | Rail, phone bottom bar |
| All apps | **App drawer** (always in the dock) | More |
| Widgets and widget picker | Widgets from apps, placed by the user | Home and Drive widgets |
| Widget configure activity | **Widget setup page**: drawn by the OS from the widget's settings schema, plus an optional custom page from the widget's app | Widget settings sheet |
| Long-press shortcuts | **App shortcuts** (Parked views only) | — |
| Wallpaper & style | **Theme wizard** | Preferences → Theme |
| — (car only) | **Drive carousel**: the home pages marked "In Drive", shown through the Moving templates | Drive modes and the switcher |

**One flat carousel replaces the page-set model.** There is a single row of home pages
with dots. A preset or the dashboard builder **adds pages to that row**; it does not make a
named set. The Drive page chip opens a **flat page list**, like Android's overview of home
pages. 40-drive-e, 40-drive-f and 40-drive-g still describe named page sets with a
two-level chip (sets, then pages); the manager reconciles 40-drive-g with this file.

### launcher-home-pages — Home pages carousel  [New]
- **Purpose:** the main surface: a swipeable row of grid pages holding widgets, app
  shortcuts and folders over a wallpaper.
- **Owner:** os
- **Opens from → goes to:** the dock's Home slot; Back from any app (Home is the root of
  Back, [shell input §4.3][si-4.3]); landing when Parked. A widget opens its app's page; an
  app icon opens the app; long-press opens edit mode (`shell-home-edit`, 45-c) or Park to
  edit (40-drive-b); on a head unit entering Moving switches to the Drive carousel
  (`drive-switcher`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night page 2 (Cluster); hu7 Night page 1 (Home); phone Day page 1; phone Night;
  huwide Night (three panes); hu5 Night.
- **Content (top to bottom):**
  1. Status strip (40-drive-a).
  2. **Grid** of the page. Default cells: HU-5 6×4, HU-7 6×4, HU-9/10 8×4, HU-wide 12×4,
     phone 4×6, tablet and desktop 8×6 ([Drive modes §4.4][dm-4.4]); Home settings may
     choose a larger cell size (45-k). Widgets on `surface-1` cards; app shortcuts as an icon
     with a label ≤ 12 graphemes; folders as a 2×2 icon cluster.
  3. **Page dots** under the grid, one per page, current dot in `accent`; the default page
     wears a small `home` glyph instead of a dot. On HU the dots sit on the passenger side of
     the bottom edge. Tap a dot to jump; long-press a dot opens the home pages list.
  4. **Wallpaper layer** behind everything (45-j); never behind text without a card.
  5. **Dock** (`shell-rail`, below).
- **Default pages for a full install on the D2 (from the presets, [Drive modes §5][dm-5]):**
  1 **Home** (warnings widget, vehicle card "Discovery 2 · Td5 · last seen 14:02", last
  trip, Diagnostics shortcut "Read faults"), 2 **Cluster** (Speed hero 64 km/h, RPM 1850,
  Coolant 88 °C, Turbo pressure 1.2 bar, Battery 13.9 V), 3 **Map** (map, speed, Altitude
  312 m, Heading 214° SW), 4 **Tiles** (Diagnostic: Boost, Coolant, Battery, Intake air,
  Fuel now, Trip), 5 **Minimal**, then Off-road **Tilt** and **Trail** once picked.
- **Gestures:** swipe left/right or D-pad `left`/`right` moves one page, wrapping; the
  default page is where Home lands. No page animation on HU beyond the tab-change motion;
  none while Moving ([visual §5][vds-5]).
- **States:** empty page: "Long-press to add widgets" with an `add` button (Parked).
  Loading: card skeletons. Error: a widget that crashed shows "Widget stopped". Offline:
  values stale grey with their age. No vehicle: vehicle widgets read "No car yet · Add a car"
  and gauges "—". Bare OS (no apps): Home holds the warnings widget, a clock and a card
  "Get apps in the Store". Parked: full grid. Idling: full grid. Moving (HU): replaced by
  the Drive carousel. Passenger: phone shows the Moving banner. Locked: Lock car layouts on
  means edit gestures say "Only the owner can edit this screen".
- **Safety and driving rules:** the warnings widget (fault telltale) and, with the Security
  app and a node, the alarm status widget are on page 1 by default and can move between
  pages or resize, never go ([Drive modes §8.1][dm-8.1] R3). Long-press always opens edit
  mode or "Park to edit" (R10).
- **Components:** Card, StatTile, HeroStat, Gauge, Page dots (new component), App icon (new
  component: 48 px glyph tile on phone, 76 px target on HU, label below), Folder icon (new
  component).
- **Spec refs:** [Drive modes §4.4][dm-4.4] · [Drive modes §7.2][dm-7.2] ·
  [UI §15.2][ui-15.2] · [UI §5.4][ui-5.4] · [visual §8][vds-8].
- **Open questions:** (1) Should Home (page 1) be removable when another page is the
  default? Recommend no: it is the root of Back. (2) Wrap-around paging, or stop at the ends?

### drive-switcher — Drive carousel page chip and flat page list  [Existing]
- **Purpose:** in Drive mode, switch between the home pages marked "In Drive" with one tap,
  a swipe or the flat page list.
- **Owner:** os
- **Opens from → goes to:** the page chip in the Drive strip (40-drive-a); a swipe or D-pad
  `left`/`right` on the page; a long-press (600 ms) or long `ok` on the chip opens the page
  list; a row switches page; **Edit pages…** (Parked only) opens `drive-modes-list` (45-h).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving with the list open; hu7 Night Parked list; huwide Night-dim Moving;
  phone Day.
- **Content:**
  1. **Page chip:** the page's icon and name, for example `dashboard` "Cluster"; ≥ 48 px
     tall, 76 px target on HU. Tap: next page in the Drive rotation (≤ 4 pages). No toast,
     no animation.
  2. **Flat page list** (`short_list`): up to six rows, one level, names ≤ 30 characters,
     the current page ticked, the rotation first: "Cluster", "Map", "Tiles", "Minimal",
     "Tilt", "Trail". One tap picks.
  3. Parked only, a last row **Edit pages…**; while Moving the row is absent, not greyed.
- **States:** a page whose needs fail (a Convoy page without an active ride, Split without
  a media app) is hidden from the chip and the list, never shown broken. Parked: list adds
  Edit pages. Moving: tap cycles, list ≤ 6. Passenger view: as Moving. Offline: pages still
  switch; values stale.
- **Safety and driving rules:** switching is allowed in any state; editing is Park to edit
  ([Drive modes §6][dm-6], [Drive modes §8.1][dm-8.1] R1, R9: the chip is an anchor, never
  hidden). Nothing switches by itself while Moving.
- **Components:** Chip, `short_list` (ListRow ≤ 30 characters, tick).
- **Spec refs:** [Drive modes §6][dm-6] · [UI §15.1][ui-15.1] · [shell input §6][si-6] ·
  [shell input §14][si-14].
- **Open questions:** the spec's two levels (modes, then faces) become one flat row; this
  changes Drive modes §6 and 40-drive-g. Confirm the rotation cap of 4 for one-tap cycling.

### shell-rail — Dock  [Existing]
- **Purpose:** five pinned slots that are always on screen: the Android hotseat.
- **Owner:** os
- **Opens from → goes to:** always present outside full-screen Drive on a phone; a slot
  opens its app or Home; the app-drawer slot opens `more` (45-b); the HU **Drive** button
  opens the Drive carousel; long-press opens the dock editor.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (right side); hu7 Night-dim Moving; phone Night and Day; huwide Night;
  desktop Night (side, with labels); hu7 Night left-hand drive.
- **Content:**
  1. Five slots, default **Home** `home` · **Diagnostics** `stethoscope` · **Trips**
     `history` · **Security** `shield` · **App drawer** `apps`. A flavour with fewer apps
     shows fewer (Guardian: Home · Security · App drawer).
  2. Each slot: icon, label ≤ 12 graphemes; active slot wears the `accent-soft` pill.
  3. A slot may hold a folder (for example "Car" with Diagnostics and Trips) or an app
     shortcut ("Read faults").
  4. HU only, outside the five: **Drive** button `speed`, at the end by default.
- **Position:** phone bottom, a floating pill, 72 px + safe area. Head units on the
  driver's side (80 HU-5, 96 HU-7, 112 HU-9/10 and HU-wide). Tablet and desktop: bottom or
  side, set in Home settings (45-k).
- **States:** Parked: full. Moving (HU): the dock stays on the driver's side; slots that
  open a page with no Moving template open the locked view (40-drive-b). Bare OS: Home and
  App drawer only.
- **Safety and driving rules:** the app drawer is in the dock exactly once, never removed
  ([Drive modes §7.3][dm-7.3], §8.1 R9); a pinned app keeps its own driving rule.
- **Components:** TabBar (dock), App icon (new component), Folder icon (new component).
- **Spec refs:** [UI §3.3][ui-3.3] · [UI §3.4][ui-3.4] · [Drive modes §7.3][dm-7.3] ·
  [visual §8][vds-8].
- **Open questions:** should the HU Drive button become a sixth dock item or stay outside?

### shell-rail-editor — Dock editor  [Existing]
- **Purpose:** choose and order the dock's slots, Android style: drag icons in and out.
- **Owner:** os
- **Opens from → goes to:** long-press on the dock; in edit mode, dragging an app icon onto
  the dock; Home settings → Dock. **Done** returns to the home page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with an icon being dragged; phone Night; desktop Night.
- **Content:**
  1. The dock with five outlined slots and drag handles; the App drawer slot carries the
     line "Always in the dock" in its item sheet.
  2. A tray below (phone) or on the passenger side (HU): **Apps you can pin**, A to Z.
  3. Drag an app onto a slot to pin; onto an occupied slot to swap; drag a slot off the
     dock to unpin (it stays in the app drawer).
  4. Drop one app onto another in the dock to make a folder (45-b).
  5. HU: **Drive button** row: Start · End, Hide.
  6. D-pad: `ok` picks, `up`/`down` moves, `ok` drops, `back` cancels.
- **States:** dock full: "The dock is full. Which one moves to the app drawer?" (the
  drawer is not offered). Error: "The app drawer must stay in the dock". Moving: "Park to
  edit" (40-drive-b).
- **Safety and driving rules:** five-slot cap; the drawer exactly once; unpinning never
  uninstalls ([Drive modes §7.3][dm-7.3], §8.1 R1, R11).
- **Components:** App icon, ListRow (drag handle), Sheet, Button.
- **Spec refs:** [Drive modes §7.3][dm-7.3] · [UI §15.2][ui-15.2] · [Drive modes §7.6][dm-7.6].
- **Open questions:** none.

<!-- links -->
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#5-the-seven-presets
[dm-6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#6-the-switcher
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[si-4.3]: ../../../../specs/2026-10-07-shell-input-design.md#43-back-and-menu
[si-6]: ../../../../specs/2026-10-07-shell-input-design.md#6-drive-mode
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-15.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#151-drive-modes-changes-123
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[ui-3.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#33-driver-side-rail-versus-bottom-bar
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
