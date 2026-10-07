---
title: "Designer brief 85-e — Security app: widgets, shortcuts and Drive menu row"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0009-session-logbook-and-location.md]
summary: >
  Fifth Security app file (app:security). Lists the four widgets Security brings to the
  widget picker gallery and their setup options, each drawn in the OS widget setup frame:
  alarm status (a safety item the OS draws; its setup page is in 45-launcher-f and is only
  cross-referenced here), the arm button (Parked only, always through the arm or disarm
  confirm), last event, and the tracker mini-map (owner only). Also the app shortcuts (Arm
  now, Find my car, Events) and the Drive menu row that arms through the `arm` template while
  Moving. Each block gives looks, data, options, sizes and the Moving render.
---

# 85-e — Security app: widgets and shortcuts

Main page: [85-a](85-security-a-main.md). The widget picker, edit mode and the shared setup
frame are the launcher's (45-launcher-d and 45-launcher-e). Widgets declare `moving` in the
manifest; the OS draws the Moving form ([Drive modes §9][dm-9]). Each app ships its own data
widgets (decided, item 52), so Security ships the ones below. The arm, last event and
tracker widgets stay Proposed: no approved spec lists them beyond the starter catalogue's
Alarm status ([launcher §9][lw-9]).

## What Security contributes

| Item | Kind | Picker group | Moving | Screen |
|---|---|---|---|---|
| Alarm status | widget (drawn by the OS; data from Security) | System | not in a layout; alarms come as `alert_card` | `widget-setup-alarm-status` in 45-launcher-f |
| Arm button | widget | Security | not shown (Parked only) | `security-widget-arm` |
| Last event | widget | Security | not shown | `security-widget-last-event` |
| Tracker mini-map | widget | Security | not shown | `security-widget-tracker-map` |
| Arm now | app shortcut | — | opens the `arm` template | — |
| Find my car | app shortcut | — | locked view | → `security-tracker` |
| Events | app shortcut | — | locked view | → `security-events` |
| Arm | Drive menu row (`contributes.drive_menu`) | — | `short_list` row → `arm` template | → `security-arm-sheet` short form |

**Alarm status (not redrawn here).** Its setup page is `widget-setup-alarm-status` in
45-launcher-f: Look Card or Compact, sizes medium and wide, no Label, Icon or Colour rows,
and it can't be removed while a node is fitted. Security adds only the data it shows:
state word, "since 22:10", and the last alarm-class event. Uninstalling Security leaves the
OS widget in place, fed by the node directly ([Drive modes §8.1 R3][dm-81]).

### security-widget-arm — Arm button widget  [Proposed]
- **Owner:** app:security (drawn in the OS widget setup frame)
- **Why the app needs it:** owners want one-tap arming from a home page, as on a key fob;
  no spec lists an arm widget, only the `arm` template.
- **Purpose:** arm (and optionally disarm) from a home page, always through the confirm.
- **Opens from → goes to:** the widget picker (Security group) or **Settings** on the placed
  widget → Save to edit mode. A tap on the placed widget opens `security-arm-sheet` or
  `security-disarm-sheet`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night setup; phone Day placed (armed); hu7 Night placed (disarmed).
- **Content (top to bottom):**
  1. Preview: a round button with `shield` and "Arm", or "Armed · tap to disarm".
  2. **Look:** Button · Button with state line.
  3. **Options:** Show disarm: Off (arm only) · On; Exit delay: Use the app's setting · 0 s ·
     30 s; Car (in a multi-car garage): Discovery.
  4. **Sizes:** small, medium.
- **States:** disarmed ("Arm"); arming ("Arming · 30 s"); armed ("Armed"; with Show disarm
  off, the tap opens `security`); alerting (the button turns to "Alarm · Open", `alarm`);
  node asleep ("Arms at next check-in"); signed out ("Sign in to arm"); no node (widget
  shows "No node" and may be removed); **Moving: not shown** in the layout (the OS leaves the
  cell empty; arming while Moving is through the Drive menu row).
- **Safety and driving rules:** Parked only; never arms or disarms on one tap: the confirm
  sheet always opens with Cancel focused ([Drive modes §8.1 R6][dm-81],
  [ADR-0033 §1][a33-1]); disarm Parked only.
- **Components:** Widget frame, Button, Segmented, Toggle.
- **Spec refs:** [App model §4.4][am-44] (`arm`) · [Drive modes §9][dm-9] ·
  [App model §15][am-15].
- **Open questions:** should the widget be allowed on head-unit home pages at all, given
  the Drive menu row?

### security-widget-last-event — Last event widget  [Proposed]
- **Owner:** app:security (drawn in the OS widget setup frame)
- **Why the app needs it:** the alarm status widget shows only the last alarm; owners also
  want the last geofence, battery or audit event at a glance.
- **Purpose:** the newest Security event of the kinds the owner picks.
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens
  `security-event-detail`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night setup; phone Day placed.
- **Content (top to bottom):**
  1. Preview: "`fence` Left Home · 08:12" with an age "2 h ago".
  2. **Look:** One line · Card with up to 3 events.
  3. **Data:** kinds as Chips: Alarms · Tamper · Movement and tow · Geofence · Battery · Arm and
     disarm (default all but Arm and disarm).
  4. **Sizes:** medium, wide.
- **States:** none yet ("No events"); offline (aged, grey); Viewer role (no positions, kinds
  limited to what they may read); **Moving: not shown**.
- **Safety and driving rules:** Parked only on driver-facing displays (event text is not a
  driving class, [UI §12.1][ui-121]).
- **Components:** Widget frame, ListRow, Chip (filter), Segmented.
- **Spec refs:** [Drive modes §9][dm-9] · [UI §6][ui-6].
- **Open questions:** none.

### security-widget-tracker-map — Tracker mini-map widget  [Proposed]
- **Owner:** app:security (drawn in the OS widget setup frame)
- **Why the app needs it:** "where did I park, is it still there" is the Guardian owner's
  most common question; the Map app's widget shows the moving car, not the parked one.
- **Purpose:** the parked car's last position and fix age.
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens
  `security-tracker`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night placed; phone Day placed; phone Night setup.
- **Content (top to bottom):**
  1. Preview: a small Ostler Night map with the puck and "Home · 3 min ago".
  2. **Look:** Map · Map with address line.
  3. **Options:** Show geofences: On · Off; Zoom: Street · Area.
  4. **Sizes:** medium, wide.
- **States:** no fix ("No fix yet"); stale (puck grey, "6 h ago"); offline (no tiles: `--bg`
  with the puck, [visual §7][vds-7]); someone else's profile on a shared head unit: "Only the
  owner can see the car's location" unless shared; **Moving: not shown** (the Map app's
  `map` template covers the moving car).
- **Safety and driving rules:** owner only, or people the owner shared location with
  ([ADR-0009][a09]); no names or plates on the map.
- **Components:** Widget frame, Map, Segmented, Toggle.
- **Spec refs:** [ADR-0009][a09] · [visual §7][vds-7] · [Drive modes §9][dm-9].
- **Open questions:** none.

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md#decision
[a33-1]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#1-categories-beside-tiers
[am-44]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
[lw-9]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#9-the-starter-catalogue
