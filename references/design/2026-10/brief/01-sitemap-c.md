---
title: "Designer brief — sitemap (c): the Apps tree"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, references/design/2026-10/screens.json]
summary: >
  The Apps half of the sitemap: one subtree per app, each with its owner name, its pages by
  screen ID, its setup flow, its settings, its widgets and shortcuts for home pages, and
  what it shows while Moving through the OS templates. Covers Diagnostics, Trips, Security,
  Maintenance, Social, Map, Navigation, Phone, Radio, Audio, Media, Camera, Decode lab,
  Community, the Store and the starter widget pack, plus the frame every app shares: App
  info, setup flow and options pages in system Settings.
---

# Sitemap (c): the Apps tree

Under the owner's direction of 2026-10-07 every feature outside the OS is an app in its own
repo, installed from the Store. Each subtree below lists: **pages** (screen IDs), **setup**
(what runs on first open), **settings** (the app's own options pages), **home** (widgets and
shortcuts it adds to home pages) and **Moving** (what the OS draws for it while Moving).

## 0. What every app has

- **App info** in system Settings: version, permissions (data classes, signals, actions with
  their category and tier), storage, notifications, **Open**, **Disable**, **Uninstall**
  (`settings-addon-detail`, `settings-addon-logs`; the full frame is `90-appframe-*`).
- **A setup flow** on first open (`setup-addon-first-run`), and **options pages** reached from
  the app's own menu and from App info (`90-appframe-*`). Backend-only apps (integrations,
  vehicle packs) have only a setup page; widget packs have only widgets.
- **Pages** open from the app drawer, the dock or a home shortcut; every page declares a
  driving rule, and a page without one is locked while Moving ([UI §12.1][ui-12.1]).
- **Actions** reach the car only through the OS gate and its confirm sheets
  ([02-global-patterns-b](02-global-patterns-b.md)).

## 1. Diagnostics (Owner: app:diagnostics)

- **Pages:** `diagnose-systems` (identity bar, Scan all, Engine, SLABS, Airbag, BCU, ACE,
  Auto gearbox) → `diagnose-system` → `diagnose-overview` · `diagnose-faults` →
  `diagnose-fault` → `diagnose-clear-result`, `diagnose-fault-history` · `live-browser` →
  `live-signal`, `live-chart`, `live-picker` · `live-vehicle-slabs`, `live-vehicle-body`,
  `live-vehicle-airbag`, `live-vehicle-eat` · `diagnose-tests` → `diagnose-active-test` ·
  `diagnose-procedures` → `diagnose-procedure-start` → `diagnose-procedure-step` →
  `diagnose-procedure-end` · `diagnose-settings` · `diagnose-scan-report`.
- **Help flow:** `help-flow` → `diagnose-help-recipe` → `diagnose-help-level` →
  `diagnose-help-preview` → `diagnose-help-sent`.
- **Confirms (OS):** `diagnose-confirm`, `diagnose-phone-approve`.
- **Setup:** needs a vehicle pack (an integration from the Store, for example the
  Discovery 2 pack) and a source (`setup-source`, `adapter-connect`); without a pack,
  `ia-empty-vehicle`.
- **Home:** "Faults" widget (count by system), "Scan all" shortcut; signal tiles come from
  the starter widget pack. **Moving:** faults reach the driver only through the OS telltale.

## 2. Trips (Owner: app:trips)

- **Pages:** `trips-list` → `trips-detail` → `trips-playback` · tabs `trips-statistics`,
  `trips-records` · `trips-export-all` · `trips-recording`, `trips-recording-options` ·
  `trips-mark-note`, `trips-notes`, `trips-flag-sheet` · `trips-delete` ·
  `trips-replay-diagnose` · share: `trips-share-sheet` → `trips-share-preview`,
  `trips-share-history`.
- **Setup:** none beyond location consent (`ia-permission-prompt` on the phone).
- **Settings:** recording options; places come from the OS (`places`).
- **Home:** last-trip widget, trip figures; the REC chip is drawn by the OS.
- **Moving:** nothing beyond Mark and the REC chip; every page locked.

## 3. Security (Owner: app:security)

- **Pages:** `security` (alarm, events, tracker map) · setup `hw-alarm-setup` →
  `hw-alarm-walk-test` · `hw-tracker`.
- **Home:** the Security alert widget (a safety widget: moves, never goes).
- **Moving:** arming through the Drive menu; alarm alerts as OS `alert_card`s.

## 4. Maintenance (Owner: app:maintenance)

- **Pages:** `maint-home` → tabs `maint-due`, `maint-timeline`, `maint-costs`, `maint-fuel`,
  `maint-documents` · `maint-add-record` · head-unit Due view `maint-kiosk`.
- **Setup:** the service schedule for the vehicle. **Home:** service-due widget.
- **Moving:** only the trip start and end alert.

## 5. Social (Owner: app:social)

- **Pages:** `social-chats`, `social-calls`, `social-rides`, `social-cameras`.
- **Setup:** account link and contacts (`accounts-s7`). **Home:** ride status, PTT widget.
- **Moving:** message alerts and the `call` template drawn by the OS; the ride chip.

## 6. Map (Owner: app:map)

- **Pages:** `vehicles-map`, `vehicles-list`, `vehicles-garage-card`, `vehicles-visibility`,
  `vehicles-share`. **Home:** convoy distance widget, map widget.
- **Moving:** own position and opted-in convoy markers only, through the `map` template.

## 7. Navigation (Owner: app:navigation)

- **Pages:** `nav-page`, `nav-planner`, `nav-library`, `nav-roadbook`; offline regions extend
  `maps-regions`. **Home:** next manoeuvre and ETA widget; Drive menu rows.
- **Moving:** `nav-turn-card` and `nav-off-route` through the `map` and `alert_card`
  templates.

## 8. Phone (Owner: app:phone)

- **Pages:** `phone-page` → `phone-dialer`, `phone-favourites`, `phone-recents`,
  `phone-contacts` · calls `phone-incoming` · `phone-message-card`.
- **Setup:** `phone-pairing`; on Android the companion's `phone-bridge-setup`.
- **Home:** `phone-widgets`. **Moving:** `call` template, Favourites as a `short_list`.

## 9. Radio, Audio, Media (Owner: app:radio, app:audio, app:media)

- Tuner and presets (radio), equaliser and sources (audio), library and now playing
  (media): drawn in `80-hu-*`. **Moving:** the `media` template only.

## 10. Camera (Owner: app:camera)

- **Pages:** `hw-camera-add`, `hw-camera`; live views in `80-hu-*`.
- **Moving:** `camera_live` for driving cameras (reverse, low-speed) only.

## 11. Decode lab (Owner: app:decode-lab)

- **Pages (S, service mode):** `decode-lab` → `decode-sniff`, `decode-candidates`,
  `decode-correlate`, `decode-label`, `decode-verify`, `decode-contribute`,
  `decode-coverage`. **Moving:** refused; the app exits.

## 12. Community (Owner: app:community)

- **In the OS:** `hub-shell` (tabs Discover · Forum · Help · Mine, plus Wiki links); hub
  account link at setup. **Home:** replies and events card (hidden while Moving).
- **On the web** (no OS, no driving rules): `hub-web-p1` Discover · `p2` Shared trip ·
  `p3` Help thread · `p4` Group or club · `p5` Live ride · `p6` Event · `p7` Profile ·
  `p8` Publish · `p9` My shares · `p10` Forum · `p11` Thread · `p12` Vehicle project ·
  `p13` Decode card · `p14` Wiki page ([hub §15.1][hub-15.1]).

## 13. Store (Owner: app:store)

- Home, categories (apps, integrations and vehicle packs, widget packs, themes, icon packs,
  wallpapers, dashboard presets), item page, installing, Installed (`addons-catalogue`),
  updates: drawn in `70-store-*`. Installing is an owner operation on local links, Parked.

## 14. Starter widgets (Owner: app:widgets-starter)

- No pages. Widgets: signal tile, gauge, hero number, binary chip, enum text, sparkline
  (Parked only), inclinometer, compass, altitude, clock, vehicle card; the seven preset
  dashboards ([Drive modes §9][dm-9]). Widget setup pages are the OS's
  (`drive-widget-settings`).

[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[hub-15.1]: ../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
