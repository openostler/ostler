---
title: "Designer brief — sitemap (a): surfaces and the navigation model"
area: references
status: draft
version: 0.4
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-app-model-design.md, references/design/2026-10/screens.json]
summary: >
  The first part of the sitemap, under the owner's Android-style direction of 2026-10-07:
  Ostler is an operating system and everything else is an app. It lists the surfaces (head
  unit as the Brain's kiosk, phone or tablet browser, desktop, the companion phone app, the
  Ostler Community web, a device's own page) and the navigation model they share: home
  pages in a carousel (dashboards are home pages; Drive mode swipes between them), the dock,
  the app drawer, the status strip, the Connection sheet, Back and the home root, landing
  rules, deep links and the Moving rules the OS enforces for every app. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# Sitemap (a): surfaces and the navigation model

**The model in one line.** Ostler is an Android-style OS for the car: a launcher with home
pages, a dock and an app drawer; a status strip; system Settings; a Store. Everything else
(Diagnostics, Trips, Security, Map, Phone …) is an app with its own pages, setup flow and
settings. Safety stays with the OS, never with an app.

The other parts: the OS tree and flavours in [01-sitemap-b](01-sitemap-b.md), the Apps tree
in [01-sitemap-c](01-sitemap-c.md), other surfaces and the driving-state matrix in
[01-sitemap-d](01-sitemap-d.md).

## 1. Surfaces

| Surface | Layout classes | Who uses it | How it reaches the car |
|---|---|---|---|
| **Head unit** (the Brain's kiosk browser) | hu5, hu7, hu9, huwide | the driver; always **driver-facing** ([UI §12.1][ui-12.1]) | the Brain at `localhost`, which talks to the node; starts in the kiosk profile "Car" (Read and Comfort only, [UI §7.1][ui-7.1]) |
| **Phone or tablet browser** | phone, tablet | owner, family, passengers, mechanic | the Brain over the car's Wi-Fi or LAN; remote paths are read-only ([UI §7.2][ui-7.2]) |
| **Desktop browser** | desktop | owner at home or in the workshop | as the phone; long editing, Decode lab, accounts |
| **Companion phone app** | phone (tablet) | owner and drivers | the OS served by the Brain or Ostler Cloud; with the node alone, its bundled OS and apps over Bluetooth or the node's Wi-Fi ([app model §7.1][am-7.1]) |
| **Ostler Community web** | phone, tablet, desktop | anyone with a hub account | never; a website run by Ostler |
| **A device's own page** | phone, tablet, desktop | owner, installer | the device itself (`device-local-page`) |

A tablet or desktop is driver-facing only if the owner declares it in the install
configuration. A phone is a passenger device: it shows the Moving banner rather than locking.

## 2. The frame

The OS draws three things on every surface; apps draw only inside the page area.

| Class | Status strip | Dock | Page area |
|---|---|---|---|
| HU-5 800×480 | top, 48 | driver side, 80 | 720×432 |
| HU-7 1024×600 | top, 56 | driver side, 96 | 928×544 |
| HU-9/10 1280×720 | top, 64 | driver side, 112 | 1168×656 |
| HU-wide 1920×720 | top, 64 | driver side, 112 | 1808×656 (a page may hold three panes) |
| Phone ~393×852 | top, 48 | bottom, 72 + safe area | ~393×730 |
| Tablet, desktop | top, 56 | bottom or side (user's choice), 88 | per page |

Sizes are the UI spec's shell sizes ([UI §3.1][ui-3.1], [§12.3][ui-12.3]); the dock takes
the rail's place. On head units the dock sits on the driver's side (right-hand drive for
the D2); sheets open on the passenger side.

## 3. Home pages (the launcher)

- **Home pages are a horizontal carousel** of grid pages. Page 1 is **Home** (the landing
  page and the root of Back). Every other page is a dashboard: what the specs called a
  Drive mode or a face is now a home page ([Drive modes §5][dm-5]).
- **Page indicator dots** under the grid show where you are; swipe or D-pad `left`/`right`
  moves between pages, wrapping.
- **Each page is a grid** per layout class (HU-7 6×4 cells, phone 4×6 …; [Drive modes
  §4.4][dm-4.4]). It holds **widgets**, **app shortcuts** and **folders**, over the
  **wallpaper layer**.
- **Editing like Android:** long-press an empty cell (or the strip) opens edit mode; drag
  to move; drop on a widget to swap; resize with handles; drag to the screen edge to add a
  page; **+** opens the widget picker gallery. Edit mode is **Park to edit** on a
  driver-facing display ([Drive modes §8.1 R1][dm-8.1]).
- **Preset dashboards** (from the starter widget pack and apps): Dashboard, Diagnostic, Map,
  Convoy / Ride, Off-road (D2), Split / Media, Minimal / Night. A **dashboard builder
  wizard** runs at first setup and any time from the launcher menu; a **theme wizard** sets
  wallpaper, colours, icon pack and gauge style. Both are drawn in `45-launcher-*`.
- **Safety widgets cannot be removed:** the warnings widget (fault telltale) and, with the
  Security app, the Security alert widget can move and resize, never go
  ([Drive modes §8.1 R3][dm-8.1]).

## 4. Drive mode (the Moving presentation of the home pages)

- On a driver-facing head unit, entering Moving switches the launcher to **Drive mode**:
  full screen, the dock hidden, the strip adding **Back** and the **page chip** (the
  current dashboard's name; it was the Drive-mode chip, `drive-switcher`).
- The home pages are **one flat row** (decided, item 45). A long swipe or `left`/`right`
  moves between the driving pages; a tap on the page chip cycles at most **4**; a long press
  on the page chip lists at most **6** as a `short_list`. `ok` opens the **Drive menu**
  (`drive-menu`).
- Each dashboard shows only its **Moving section** through the OS templates: ≤ 6 tiles,
  map, media and call panes, no animation ([Drive modes §4.3][dm-4.3]). An app cannot draw
  its own view here; the OS draws the template from the app's data.
- Home itself is not shown while Moving; the last dashboard used on that display opens.

## 5. The dock

- **Slots per class** (decided, item 17): phone 5, HU-5 and HU-7 5, HU-9/10 6, HU-wide 7,
  tablet and desktop 7, anchors included. Default on a five-slot class: **Home ·
  Diagnostics · Trips · Security · App drawer**, or the flavour's own set
  ([01-sitemap-b §3](01-sitemap-b.md#3-flavours-preinstalled-sets)).
- Any app, shortcut or widget can take a slot, and the user may add slots. **Home** and the
  **App drawer** are default anchors: they can move, be renamed, re-iconed and hidden while
  the recovery path stays (item 16 as amended in the openness round; [launcher §5.1][lw-5.1]).
- Long labels are ellipsised; the active item wears the `accent-soft` pill.
- The head-unit **Drive** button is retired (item 16): Moving shows Drive mode by itself.

## 6. The app drawer

- A grid of every installed app, A to Z, with search on top. An app the driving state locks
  still shows, and opens its locked view.
- **Settings** and **Store** are system apps, always present and never hidden. A
  **Hidden apps** link ends the grid (`shell-hidden-pages`, which was More → Hidden pages).
- Long-press an app icon: **App info** (in system Settings, `90-appframe-*`), **Add to
  home**, **Add to dock**, **Hide**.
- The old More rows **Edit layout** and **Reset layout** move to the launcher menu (long
  press on an empty cell) and stay in Settings → Display and the Connection sheet
  ([Drive modes §7.8][dm-7.8]).

## 7. Status strip and Connection sheet (OS)

- The strip is one row with an overflow chip; chips ≥ 48 px, icon + word, each opens a sheet
  (`shell-strip`). OS chips: Vehicle (more than one), Worst telltale, Link, Clock, 12 V,
  Mark; the profile chip "Car" and the visibility chip. Apps may add status-only chips
  (openness round); otherwise the OS itself
  shows REC while the Trips app records, Security when the Security app has a node, and the
  ride or call chip while a call is active.
- The **Connection sheet** (`shell-connection-sheet`) opens from the Link chip and by itself
  when the link drops: the connection ladder, the Brain's power state, queued actions,
  **Use an adapter** and **Reset layout** ([UI §4.5][ui-4.5]).

## 8. Back, home root, landing and deep links

- **Back** closes a sheet, then leaves an engaged control, then goes up one level inside the
  app, then returns to the home page. From any screen, Back reaches Home or Drive mode in
  **≤ 3 presses** ([shell input §4.3][si-4.3]). In Drive mode while Moving, Back never
  leaves Drive mode; it moves focus to the page chip.
- **Landing:** Drive mode when Moving (head units); the Security app when Parked and armed;
  the Diagnostics app in service mode; otherwise Home ([UI §3.4][ui-3.4]).
- **Deep links** name an app and one of its routes (`diagnostics.faults`, `trips.trip`),
  never a path. A link to a page the driving state locks opens the locked view
  (`shell-locked-view`), which offers **Open on phone** (`ia-open-on-phone`).

## 9. Moving rules the OS enforces for every app

On a driver-facing display while Moving: only OS templates; no text entry; no video; no
message text; no other people on the map except plain convoy markers; tasks ≤ 3 screens
ending in Drive mode; every app page not declared driver-safe shows the locked view;
Passenger view unlocks only vehicle state, own route and driving cameras ([UI §12.1][ui-12.1]).
Edit mode, widget setup, app setup flows, the Store and Settings are Park to edit.

[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#5-the-seven-presets
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[lw-5.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#51-the-dock
[si-4.3]: ../../../../specs/2026-10-07-shell-input-design.md#43-back-and-menu
[ui-3.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#31-layout-classes
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#123-drive-mode-changes-31-35-53-54-10-u1-and-its-test
