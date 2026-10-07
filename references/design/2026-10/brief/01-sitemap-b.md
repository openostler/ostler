---
title: "Designer brief — sitemap (b): the OS tree and the product flavours"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, references/design/2026-10/screens.json]
summary: >
  The OS half of the sitemap: every page the operating system owns, by screen ID. The
  launcher (Home and dashboard pages, edit mode, widget picker and widget setup, the
  dashboard and theme wizards), the dock, the app drawer, the status strip and its sheets,
  the Connection sheet, the shell-drawn overlays (alerts, calls, locked view, Passenger view,
  service mode), system Settings with every page, the Store, and first-run setup on the head
  unit, browser and companion app. It ends with the product flavours as preinstalled app
  sets: Ostler Diagnostics, Ostler Guardian and Ostler Brain.
---

# Sitemap (b): the OS tree and the product flavours

Every item below has **Owner: os**; the Store is a system app (decided, item 28). IDs are the blocks in each area's file; a file pattern
without an ID (`45-launcher-*`, `70-store-*`, `90-appframe-*`) means the next wave draws it.
Legend: **(L)** locked while Moving on a driver-facing display, **(T)** drawn as a Moving
template, **(S)** service mode only.

## 1. The OS tree

- **Launcher** ([01-sitemap-a §3](01-sitemap-a.md#3-home-pages-the-launcher), `45-launcher-*`)
  - Home page 1: `home` (vehicle widget, warnings widget, Security alert widget, shortcuts).
  - Dashboard pages (presets from the starter widget pack): `drive-dashboard-cluster`,
    `drive-dashboard-map`, `drive-diagnostic-tiles`, `drive-diagnostic-system` (Parked
    page only), `drive-map-map`, `drive-convoy-map-ptt`, `drive-convoy-ride`,
    `drive-offroad-tilt`, `drive-offroad-trail`, `drive-offroad-open-slabs`,
    `drive-split-split`, `drive-minimal-minimal`.
  - Drive mode (T): `drive-switcher` (the page chip), `drive-menu`, `drive-dusk-suggest`,
    `drive-exit-home-moving`.
  - Edit mode (L, Park to edit): `shell-home-edit`, `shell-item-sheet`, `shell-icon-picker`,
    `shell-name-edit`, `shell-reset-confirm`, `shell-park-to-edit`.
  - Widget picker gallery and widget setup (L): `shell-widget-picker`,
    `shell-widget-picker-by-signal`, `drive-widget-settings`, `drive-signal-picker`,
    `drive-widget-settings-map`, `drive-widget-settings-addon`.
  - Dashboards list and builder (L): `drive-modes-list`, `drive-mode-editor`,
    `drive-mode-preview`, `drive-layout-import`, `drive-layout-import-error`,
    `drive-update-from-preset`; the dashboard builder wizard and the theme wizard
    (`45-launcher-*`).
- **Dock:** `shell-rail` (the dock); dock editor `shell-rail-editor` (L).
- **App drawer:** `more` (the drawer); `shell-hidden-pages` (Hidden apps); the long-press
  menu on an app icon (`45-launcher-*`).
- **Status strip:** `shell-strip`; strip editor `shell-strip-editor` (L).
  - Sheets: `shell-telltale-sheet` (T) · `shell-connection-sheet` → `adapter-connect`,
    `adapter-verdict`, `adapter-soft-gate` · `shell-vehicle-switcher` (L) · `accounts-s4`
    profile switcher (L) · `accounts-s9` visibility · `shell-brain-wake`.
- **Overlays the OS draws for every app:** `alert-message` → `alert-reply-list`,
  `alert-voice-reply` · `alert-other` · `call-template` (T) · `shell-locked-view` ·
  `ia-open-on-phone` · `shell-passenger-view` · `shell-phone-moving-banner` ·
  `shell-service-mode` (S) · toasts `ia-toast` · permission prompts `ia-permission-prompt`.
- **System Settings** (`settings-root`, L): one app, Park to edit.
  - Display: `preferences`, `settings-units-region`; theme wizard (`45-launcher-*`).
  - Notifications: `settings-notifications`, `alert-settings`.
  - Driving: `settings-driving`, `shell-driving-page`.
  - Privacy: `settings-privacy`, `settings-data-classes`, `settings-location`,
    `settings-usage-reports`, `settings-export-data`, `settings-delete-data`.
  - Sharing and places: `settings-sharing-defaults`, `accounts-s8`, `places`.
  - Users and accounts: `settings-profiles`, `settings-hu-pin`, `settings-account`,
    `accounts-s3`, `accounts-s5`, `accounts-s6`, `accounts-s7`, `accounts-s10`,
    `settings-ostler-link`.
  - Apps (one list, integrations labelled, decided item 56): App info per app
    `settings-addon-detail`, `settings-addon-logs`; integrations and vehicle packs
    `settings-integrations`; app setup and options flows (`90-appframe-*`).
  - Vehicles: `garage`, `setup-vehicle-add`, `setup-vehicle-name`.
  - Network and devices: `network`, `network-device`, `hw-add-device`, `hw-device-logs`,
    `hw-device-restart`, `device-local-page`, `hw-brain`, `hw-gps`, `hw-imu`,
    `hw-imu-calibrate`, `hw-power`, `hw-power-schedule`, `hw-mesh-radios`,
    `hw-mesh-radio`, `phone-pairing`; display buttons `shell-buttons`,
    `hw-buttons-key-test`; install guides `hw-install-pick`, `hw-install-wiring`,
    `hw-install-power`, `hw-install-heard`, `hw-install-test-read`, `hw-install-done`.
  - Maps: `maps-regions`.
  - Storage, recording and backups: `settings-storage`, `settings-recording`,
    `settings-backups`, `settings-restore`.
  - Updates: `settings-updates`, `hw-brain-update`, `hw-firmware-update`,
    `ia-update-available`.
  - Developer: `settings-developer`, `settings-api-tokens`, `settings-token-create`,
    `settings-connected-apps`, `settings-platform-logs`.
  - About: `settings-about`, `settings-licences`, `settings-legal`,
    `settings-report-problem`.
  - Reset: `settings-reset`, `settings-factory-reset`.
- **Store** (a system app, Owner: os, in every flavour and never removed; L): `addons-catalogue` becomes the Store's Installed tab; apps,
  integrations, vehicle packs, widget packs, themes, icon packs, wallpapers and dashboard
  presets (`70-store-*`).
- **First run** (`10-onboarding-*`):
  - Head unit or browser: `setup-welcome` → `setup-prefs` → `setup-trust` → `accounts-s1`
    → `setup-vehicle-add` → `setup-vehicle-name` → `setup-source` → `setup-node-pair`,
    `setup-node-uplink` or `adapter-connect` → `adapter-verdict` → `setup-first-contact` →
    `setup-display` → `setup-people` → `setup-car-profile` → apps for the flavour
    (`setup-addon-first-run`) → dashboard builder wizard (`45-launcher-*`) →
    `setup-summary` → Home with `setup-checklist`.
  - Companion app: `setup-app-connect` → `setup-app-permissions` → `accounts-s2` or
    `setup-invite-accept`; TVs and second screens `setup-device-code`.
  - Later: `setup-backup`, `setup-restore`, `setup-add-brain`, `setup-move-brain`.
- **OS-wide states** ([02-global-patterns-a](02-global-patterns-a.md),
  [-b](02-global-patterns-b.md), [-c](02-global-patterns-c.md)): `ia-empty-state`,
  `ia-loading`, `ia-error-node-offline`, `ia-error-pack-missing`, `ia-error-bus-silent`,
  `ia-error-adapter-clone`, `ia-error-permission`, `ia-offline-banner`, `ia-long-job`,
  `ia-destructive-undo`, `ia-empty-vehicle`.

## 2. What the OS keeps, whatever is installed

The fault telltale (strip chip, warnings widget, telltale sheet), alarm alerts (when the
Security app is installed), the Moving templates and their limits, Park to edit, the locked
view, Passenger view and the service-mode frame. No app can remove, cover, rename or
recolour them ([Drive modes §8.1 R3][dm-8.1]). The dock's App drawer button, Settings and
the Store are always reachable.

## 3. Flavours (preinstalled sets)

A flavour is the OS plus a preinstalled set of apps ([ADR-0039][adr-39] names the
products). Any flavour can add apps from the Store later.

| Flavour | Hardware | Preinstalled apps | Default dock | Home page 1 |
|---|---|---|---|---|
| **Ostler Diagnostics** | the OBD-port node plus the companion phone app (no Brain) | Diagnostics, Trips, Security, starter widgets, default theme | Home · Diagnostics · Trips · Settings · App drawer | vehicle widget, warnings widget, Battery and Coolant tiles, last trip |
| **Ostler Guardian** | the guardian node (GPS, alarm, IMU), phone app | Security and its widgets, default theme | Security · Settings · App drawer | Security alert widget (armed state, last fix), warnings widget |
| **Ostler Brain** | node and Brain, head unit | Diagnostics, Trips, Security, Map, Media, Audio, starter widgets, default theme; Camera when a camera is found; Radio when a tuner is found | Home · Diagnostics · Trips · Security · App drawer | vehicle widget, warnings, last trip; dashboards Dashboard and Diagnostic |

The sets are decided (items 11 and 41), and so are the Guardian dock (item 42) and Ostler
Brain as a third named flavour (item 43). On the phone, "Uninstall" disables a bundled app
and deletes its data (item 11). "Ostler is the head unit" (Radio, Audio, Media as the audio
path) is offered at first run, not the default (item 55).

- **Diagnostics flavour notes:** with the node alone there is no Brain, so Brain-only views
  are absent (no "Needs the Brain" cards); the node in deep sleep shows "Node asleep (deep)"
  ([UI §3.8][ui-3.8]). The Security app is preinstalled; its strip chip shows only once a
  node with alarm inputs is paired.
- **Guardian flavour notes:** no Diagnostics app, so the Link chip's ladder stops at the
  node; Home's vehicle widget shows 12 V and the last fix only. Adding Diagnostics from the
  Store turns it into a full diagnostic install.
- The first-run step "apps for the flavour" shows the preinstalled set ticked and a few
  Store suggestions unticked.

## Open questions

1. **Decided (item 43):** Ostler Brain is a third named flavour, with the app set of item 11.
2. **Decided (item 42):** Guardian's dock is Security · Settings · App drawer; Settings is
   in the dock and also in the drawer (item 57).

[adr-39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
