---
title: "Designer brief 85-b — Security app: events, event detail, clips and alarm alert cards"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-02-gps-tracker-alarm-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0009-session-logbook-and-location.md]
summary: >
  Second Security app file (app:security). The event list with filters for tamper, door,
  tilt, battery, movement, geofence and tow events, plus arm and disarm audit rows; the
  event detail with what was sensed, where, which device raised it and how the alert went
  out; the clip viewer for events that have camera footage (Parked only, needs the Brain);
  and the alarm alert card, which the OS draws through its alert pipeline as a safety item
  that cannot be removed, with its Parked, Moving and Passenger forms.
---

# 85-b — Security app: events, clips and alarm alerts

Main page and words: [85-a](85-security-a-main.md). Events are stored on the node or
Guardian first, so the list works with the Brain asleep; clips need the Brain.

## Event kinds (one icon and title each)

| Kind | Icon | Title example | Source | Severity |
|---|---|---|---|---|
| Tamper | `warning` | "Guardian power lost" · "Battery disconnected" · "Node removed" | Guardian | alarm |
| Door / bonnet | `door_open` | "Driver's door opened" · "Bonnet opened" | BCU tap (when fitted) | alarm when armed |
| Tilt | `screen_rotation_alt` | "Tilt > 3° for 10 s" (jacking, towing) | IMU | alarm when armed |
| Shock | `vibration` | "Knock detected · strong" | IMU | warn, or alarm when repeated |
| Movement | `near_me` | "Moved 120 m with ignition off" | GPS | alarm when armed |
| Geofence | `fence` | "Left Home" · "Entered Work" | GPS | per geofence |
| Tow | `rv_hookup` | "Moving with ignition off · 32 km/h" | GPS + IMU | alarm |
| Battery | `battery_alert` | "12 V low · 12.1 V" · "Guardian cell 15 %" | node, Guardian | warn |
| Ignition | `key` | "Ignition on while armed" | node | alarm |
| Audit | `history` | "Armed by you · head unit" · "Disarmed remotely · phone, relay" | app | info |
| Channel | `sms_failed` | "SMS not delivered" | Guardian modem | warn |

Thresholds always carry "starting value · tuned on the car" (from `hw-alarm-setup`).

### security-events — Events  [New]
- **Owner:** app:security
- **Purpose:** every alarm, sensor, geofence and audit event, newest first.
- **Opens from → goes to:** `security` → **All events**; the last-event widget; Trips' **All
  events** timeline (filtered to Security). Goes to `security-event-detail`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; tablet Night (list and detail side by side); hu7 Night.
- **Content (top to bottom):**
  1. Filter Chips (multi-select): All · Alarms · Tamper · Doors · Tilt and shock · Movement
     and tow · Geofence · Battery · Arm and disarm.
  2. Range Segmented: Today · 7 days · 30 days.
  3. Day-grouped ListRows: icon, title, time, source ("Guardian IMU", "GPS", "you, phone"),
     a status Chip (Open, Cleared, Info), and a `videocam` mark when a clip exists.
  4. An open alarm sits pinned at the top in an `alarm-bg` Card until disarmed.
- **States:** empty ("No events yet. Armed periods and alerts show here."); loading
  (Skeleton rows); offline (cached list with "Last synced 6 min ago"); node asleep (list from
  the last check-in, age shown); Parked and Idling full; Moving: page locked (the
  `shell-locked-view` card "Available when parked" with Open on phone); Passenger: head-unit
  Passenger view not offered (event text is not a reg 109 class); phone "I'm a passenger"
  reads it.
- **Safety and driving rules:** no event detail, list or clip while Moving on a driver-facing
  display ([UI §12.1][ui-121]); alarm events reach the driver only as `alert_card`s.
- **Components:** Chip (filter), Segmented, ListRow, Card (alarm tone), Empty state,
  Skeleton.
- **Spec refs:** [UI §6][ui-6] (Alarm row: "events (filtered Logs)") · [UI §12.2][ui-122].
- **Open questions:** how long are events kept on the Guardian when no Brain collects them?

### security-event-detail — Event  [New]
- **Owner:** app:security
- **Purpose:** what happened, where, what was sent and to whom.
- **Opens from → goes to:** `security-events`; an alarm alert card (Parked); a phone push.
  Goes to `security-clip`, `security-tracker`, `security-disarm-sheet`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (alarm event); phone Day (geofence event); hu7 Night.
- **Content (top to bottom):**
  1. Header: icon, title "Moved 120 m with ignition off", time "02:16:04", status Chip.
  2. **What was sensed**: rows "Tilt 4.2° for 12 s · threshold 3° (starting value)", "GPS
     speed 9 km/h · fix ±8 m", "Ignition off", "Alarm state Armed since 22:10".
  3. **Where**: small Map with the position and, for movement, the trail from start to now.
     "Only you can see this."
  4. **Raised by**: "Ostler Guardian · IMU and GNSS", link to its device page.
  5. **Alert sent**: one row per channel with result: "Paired phone · local · delivered
     02:16:06", "SMS · delivered 02:16:09", "Notify address · failed (no answer)".
  6. **Clip** (only with cameras and a Brain): thumbnail still, "Rear camera · 30 s", → 
     `security-clip`.
  7. Actions: **Disarm** (Parked, if still alerting) · **Open tracker** · **Mark as
     checked**.
  8. Audit events show instead: who, which device, which link ("phone, relay"), and for
     remote disarms "Owner told 07:42".
- **States:** loading; position missing ("No fix at the time"); clip pending ("Clip saving…
  Needs the Brain"); Brain asleep with a clip ("Needs the Brain · Wake"; remote requests show
  the wake sheet, [UI §3.8][ui-38]); Moving: locked; Viewer role: no position unless shared.
- **Safety and driving rules:** Parked only on driver-facing displays; the position stays on
  the device unless shared ([ADR-0009][a09]); every alert row is honest about failures.
- **Components:** ListRow, Chip (status), Map, Card, Button.
- **Spec refs:** [ADR-0033 §7][a33-7] · [tracker spec: signal taps][ga-taps] (draft).
- **Open questions:** none.

### security-clip — Event clip  [New]
- **Owner:** app:security (footage from app:camera)
- **Purpose:** watch the camera footage around an event, parked.
- **Opens from → goes to:** `security-event-detail` → Clip. Back to the event.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night; tablet Night; hu9 Night Parked.
- **Content (top to bottom):**
  1. Video frame with camera name "Rear" and the event time marked on a Scrubber.
  2. Camera Segmented when several: Front · Rear · Cabin.
  3. Rows: "Recorded 02:15:50 – 02:16:20 · kept 30 days", **Save to Trips**, **Share…** (a
     share sheet; never public by default), **Delete** (danger, with undo).
- **States:** loading ("Waking the Brain…" with progress, then buffering); no camera
  (absent); camera offline at the time ("No footage: camera was off"); Brain absent: page
  absent; Moving: never plays, locked view.
- **Safety and driving rules:** no video on any driver-facing display while Moving,
  Passenger view included; clip playback is Parked only ([UI §6][ui-6],
  [UI §12.1][ui-121]). Waking cameras happens after the alert has gone out, best effort
  ([ADR-0040 §8][a40-8]).
- **Components:** video frame (new component, as in 45-launcher-f), Scrubber, Segmented,
  ListRow, Button (danger).
- **Spec refs:** [UI §6][ui-6] (Cameras row: "Security → Clips (Parked)") ·
  [ADR-0040 §3][a40-3].
- **Open questions:** clip retention default (30 days is a placeholder).

### security-alert-card — Alarm alert card  [New]
- **Owner:** os (drawn by the OS alert pipeline; data from app:security)
- **Purpose:** tell whoever is at a screen that the alarm went off, in a form that can't be
  hidden.
- **Opens from → goes to:** raised by the alert pipeline on every screen of every display
  when an alarm-class event arrives. Tap (Parked) → `security-event-detail`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; hu7 Night-dim Moving; phone Night (in-app banner form).
- **Content (top to bottom):**
  1. Icon `e911_emergency` and word "Alarm" in the `alarm` tone (the only pulse; a static
     ring with reduced motion).
  2. Line 1 (≤ 30 characters): "Driver's door opened".
  3. Line 2 (≤ 30 characters): "02:14 · Discovery" (the car's name, never the VIN or plate).
  4. Buttons (≤ 2): Parked: **Open** and **Disarm**; Moving: **Open on phone** and
     **Dismiss** (the event stays open in the app).
- **States:** Parked full; Idling as Parked except Disarm ("Park to disarm"); Moving: the
  `alert_card` template only, no map, no clip, no Disarm; Passenger view: the same card;
  several events: one card with a count "Alarm · 3 events"; Tamper uses `warning` with the
  word "Tamper"; Testing (walk test) shows "Test · Driver's door" in `warn`, never `alarm`;
  OS with the Security app uninstalled and a node fitted: the OS still raises the card, and
  Open goes to the device page.
- **Safety and driving rules:** a safety item: it moves, never goes; no layout, app or
  setting can remove, cover, rename or recolour it ([Drive modes §8.1 R3][dm-81]); one card
  at a time, it never covers a red telltale or the reverse camera; it is not rate-limited
  like message cards. Alarm alerts never wait for the Brain ([ADR-0033 §7][a33-7]).
- **Components:** `alert_card` (shell template), Button.
- **Spec refs:** [UI §12.1][ui-121] (`alert_card` limits) · [Drive modes §8.1][dm-81] ·
  [UI §15.2][ui-152].
- **Open questions:** should an alarm card sound a chime while Moving, or stay silent with
  only the phone ringing?

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md#decision
[a33-7]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths
[a40-3]: ../../../../decisions/adr-0040-power-states-and-wake.md#3-wake-sources
[a40-8]: ../../../../decisions/adr-0040-power-states-and-wake.md#8-safety
[dm-81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ga-taps]: ../../../../specs/2026-10-02-gps-tracker-alarm-design.md#read-side--alarmsecurity-via-signal-taps
[ui-38]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-122]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-152]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
