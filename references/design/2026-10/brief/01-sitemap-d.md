---
title: "Designer brief — sitemap (d): phone, desktop, companion app, Community web and the driving-state matrix"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-drive-modes-and-editing-design.md]
summary: >
  The last part of the sitemap. What differs on the phone or tablet browser (bottom dock,
  fewer strip chips, the Moving banner and the per-trip passenger prompt), the desktop
  (side dock with labels, panes, editing any screen's home pages), the companion phone app
  (OS served by the Brain, the bundled OS with the node alone, native pairing, permissions,
  approvals and notifications), the Ostler Community web routes and a device's own page. It
  ends with the matrix of what each driving state hides on each surface, for the OS and for
  apps.
---

# Sitemap (d): other surfaces and driving states

## 1. Phone or tablet browser

- **Frame:** strip with Worst telltale, Link, REC (with Trips), Security (with Security) and
  Mark; the **dock at the bottom** with five slots; home pages and the app drawer as on the
  head unit, in the phone grid (4 × 6 cells). No Drive button: Drive mode opens from the
  page chip on a dashboard page.
- **Extra pages** (phone, tablet, desktop only): `accounts-s2` Sign in, `accounts-s3`
  Passkeys, `accounts-s5` Users and roles, `accounts-s6` Signed-in devices, `accounts-s7`
  Contacts, `accounts-s8` Sharing with View as…, `accounts-s10` Safety contacts.
- **Editing another screen:** the launcher's edit bar has "Editing for: this screen ▾", so a
  phone can edit the head unit's home pages; a change for a display that is Moving waits
  for its next Parked ([Drive modes §7.1][dm-7.1]).
- **While Moving:** `shell-phone-moving-banner`; app pages that are not driving-related ask
  "I'm a passenger" once per trip, then stay view-only ([UI §12.1][ui-12.1]).
- **Remote path:** read-only; action buttons say "Only on the car's own network"
  (`ia-error-permission`).

## 2. Desktop

- Dock at the side with labels; two or three panes; denser type when Parked.
- The place for long work: home-page and dashboard building, widget setup with a typed VSS
  path, Decode lab (service mode), accounts and sharing, Trips Export all, the Store.
- Never driver-facing unless the owner declares it; no Moving lock.

## 3. Companion phone app

One store app per platform ([app model §7.1][am-7.1], [§14.3][am-14.3]).

- **With a Brain or Ostler Cloud:** the app shows the OS the server serves, as the phone
  browser, plus native features.
- **With the node alone (Ostler Diagnostics flavour):** the bundled OS with the preinstalled
  apps, talking to the node over Bluetooth or its Wi-Fi. No "Needs the Brain" prompts. In
  deep sleep: "Node asleep (deep) · wakes on ignition, door or motion · last seen 3 h"
  ([UI §3.8][ui-3.8]).
- **Native pages:** connect and pair `setup-app-connect`; permissions at setup
  `setup-app-permissions` and at the moment of use `ia-permission-prompt`; approve a Tier
  2–3 action `diagnose-phone-approve`; OS push notifications that open the matching route;
  the Phone app's notification bridge `phone-bridge-setup`; receiving a page from the car
  `ia-open-on-phone`; Moving banner `shell-phone-moving-banner`.
- Store apps install into the companion only when the build includes them or they are
  declarative; no downloaded code runs inside the native app.

## 4. Ostler Community web

A closed website run by Ostler (Owner: app:community on the server side); no driving rules.

| Route | Page |
|---|---|
| `/` | `hub-web-p1` Discover |
| `/t/<id>`, `/r/<id>` | `hub-web-p2` Shared trip or route |
| `/forum/t/<id>` (help) | `hub-web-p3` Help thread |
| `/g/<slug>` | `hub-web-p4` Group or club |
| `/e/<id>/live`, `/ride/<token>` | `hub-web-p5` Live ride |
| `/e/<id>` | `hub-web-p6` Event |
| `/u/<handle>` | `hub-web-p7` Profile |
| `/me/…` | `hub-web-p8` Publish, `hub-web-p9` My shares |
| `/forum`, `/forum/<make>/<model>` | `hub-web-p10` Forum |
| `/forum/t/<id>` | `hub-web-p11` Thread |
| `/dev/<project>` | `hub-web-p12` Vehicle project |
| `/decode/<id>` | `hub-web-p13` Decode card |
| `/wiki/<path>` | `hub-web-p14` Wiki page |

## 5. A device's own page

Each device serves a small page outside the OS: `device-local-page`, with a read-only list
of its peers ([UI §3.7][ui-3.7]). Firmware updates go through `hw-firmware-update`.

## 6. What each driving state hides

States: [UI §3.5][ui-3.5] as amended by [§12.1][ui-12.1]. "Locked" means the page is
replaced by `shell-locked-view` ("Available when parked" + Open on phone). Passenger view
unlocks only vehicle state, own location and route, and driving cameras.

| Page or group | Parked | Idling | Moving (head unit) | Passenger view (head unit) | Phone while Moving |
|---|---|---|---|---|---|
| Strip, Mark, telltale sheet (OS) | full | full | full; telltale as `telltale_list` | full | full |
| Home page 1 (OS) | full | full | not shown; Drive mode opens | not offered | banner |
| Dashboard pages (OS) | full grid | full grid | Moving section only, ≤ 6 tiles | full grid if every widget qualifies | banner |
| Page chip, Drive menu (OS) | full, "Edit dashboards…" | full | switch and ≤ 6 rows | as Moving | full |
| Dock, app drawer (OS) | full | full | hidden in Drive mode; drawer locked | never | full |
| Edit mode, widget picker and setup, wizards (OS) | full | with Park evidence | "Park to edit" only | never | allowed; held for a moving display |
| System Settings, Store | full | text entry with Park evidence | locked | never | "I'm a passenger" |
| Alerts, calls, turn cards (OS templates) | full | full | templates only | templates only | OS notifications |
| Confirms and wizards, Tier 1–3 (OS) | full | Tier 1 Maintenance with Park evidence | locked; the gate refuses | never | local approval, stationary |
| Diagnostics pages | full | reading; Maintenance with Park evidence | locked | vehicle state only | read; actions need stationary |
| Trips pages | full | full; share and export with Park evidence | locked | own route only | "I'm a passenger" |
| Security pages | full | full | arming only; clips locked | state and own location | full; disarm needs Parked |
| Maintenance, Social, Map, Phone pages, Community | full | with Park evidence | locked; templates only | never | "I'm a passenger" |
| Navigation pages | full | with Park evidence | `map` template, turn card | own route | "I'm a passenger" |
| Radio, Audio, Media | full | full | `media` template | `media` template | full |
| Camera | full | driving cameras only | `camera_live` driving cameras only | driving cameras | allowed |
| Decode lab, service mode | service mode | service mode | refused; exits | never | refused |
| Text fields, keypads | full | with Park evidence | none | none | allowed |

[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[am-14.3]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-3.7]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
