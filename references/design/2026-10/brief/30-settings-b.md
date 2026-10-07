---
title: "Designer brief: Settings (part B): alerts, notifications and driving rules"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Part B of the Settings brief. It covers how alerts reach the driver and the owner: the
  Existing message alert settings page (canned replies, the opt-in first-line preview that is
  off by default and shows only for messages that arrive while Parked, group alerts, the
  "I'm driving" auto-reply and the fixed rate limits shown read-only); a New
  Notifications page (per-app alert filters for Social and Phone, push to the owner's phone,
  quiet hours, and critical alerts that can never be muted); and a New Driving rules page that
  explains what changes while Moving, shows the Passenger view record, the passenger-only
  display declaration and the Phone option "Only favourites ring while driving".
---

# Settings brief, part B: Alerts, Notifications, Driving rules

Tree, shared rules and the Settings lock: [part A](30-settings-a.md).

### alert-settings — Message alerts  [Existing]
- **Owner:** os (the alert pipeline); the per-app Phone filter may move to app:phone
- **Purpose:** how message alerts from any app (Social, Phone & Comms) behave in the car.
- **Opens from → goes to:** Settings → Alerts; the "…" of a message `alert_card` when Parked;
  the Phone app's settings (app:phone). Goes to the canned-reply editor (an inline list) and Notifications.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the Settings lock).
- **Content (top to bottom):**
  1. **Replies while driving**: the canned list, up to five rows, each ≤ 30 characters, plain
     text: "Driving, will reply later", "On my way", "Running late", "OK, thanks", "Call you
     when I stop". Each row: drag handle, text, edit, delete. "Add reply" (hidden at five);
     "Reset to defaults". Caption: "Speak a reply is always first in the list."
  2. **Preview**: Switch "Show first line of messages when parked", **off by default**.
     Caption: "Only for messages that arrive while the car is parked. Never while driving,
     never pictures. The line goes back to the app name as soon as you drive."
  3. **Group messages**: Switch "Alert for group messages", off by default. Caption: "When
     off, group messages only raise the unread count. Your active ride channel always alerts."
  4. **"I'm driving" auto-reply** (Social messages only): Segmented "No one · Ride members ·
     Favourites · All contacts" (default Ride members and Favourites); text ≤ 60 characters;
     caption "Once per conversation per trip. Other apps use your phone's own driving mode."
  5. **Limits while driving** (read-only Card, no controls): "One message card at a time · One
     per conversation every 2 minutes · Three every 10 minutes, then only the count · Never
     over a red warning, the reverse camera, a call or a turn prompt."
  6. Row "Which apps can alert" → Notifications.
- **States:** empty (no replies: "Only Speak a reply will be offered"); loading; error on save;
  no app that raises messages ("Install Social or Phone & Comms to get message alerts",
  link to Apps); Parked full; Idling: editing needs Park evidence; Moving: the Settings
  lock; locked (Car profile): read-only, "Sign in to change your replies".
- **Safety and driving rules:** canned replies and the preview are changed Parked only; the
  preview never shows while Moving or on a passenger-only display; until the U2 legal opinion
  is recorded the preview shows only when Parked, not Idling ([UI §12.1][ui-12.1]); the
  limits are fixed and have no control ([UI §14][ui-14]).
- **Components:** ListRow (drag handle), Switch (new, part A), Segmented, Card, Button, text
  field (Parked only).
- **Spec refs:** [UI §12.1][ui-12.1], [UI §14][ui-14], [Social §12][soc-12],
  [Phone & Comms §8][pc-8].
- **Open questions:** none beyond the U2 legal check.

### settings-notifications — Notifications, quiet hours and critical alerts  [New]
- **Owner:** os
- **Purpose:** which sources may alert, where (car, phone), when, and which never go quiet.
- **Opens from → goes to:** Settings → Alerts → "Which apps can alert"; Settings root. Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the Settings lock).
- **Content (top to bottom):**
  1. **Critical alerts** (Card in the `alarm-bg` tone, no controls): "Always on: alarm and
     Security alerts, red warnings from the car, safety contacts' SOS. They sound through
     quiet hours and can't be turned off." Rows list each with its fixed icon and word.
  2. **In the car**, per app, one row per notification channel the app declares, each with
     a Switch and a meta line (the `alarm` and `critical` channels are the OS's): Social (Chats,
     Rides), Phone & Comms (Messages; then one row per bridged app such as "WhatsApp",
     "Signal" when the bridge is on), Maintenance & Garage ("Service due"), Ostler Community
     ("Replies to your help threads"), Vehicles & Map ("Convoy"). Only installed apps show.
  3. **On my phone** (push through the companion app): Alarm (locked on), "Car left a
     geofence", "Service due", "Trip shared with you", "Low 12 V battery ‹V›". Each a Switch.
  4. **Quiet hours**: Switch; From ‹time› To ‹time›; days chips "Mon … Sun"; caption "Quiet
     hours hold phone push and in-car chimes for non-critical alerts. They never mute critical
     alerts."
  5. **Missed while driving**: read-only caption "Missed calls become one card when you park."
- **States:** empty (no app that alerts: only Critical alerts and On my phone); loading;
  no paired phone ("Pair a phone to get push alerts", link to Network pairing); offline
  ("Needs the Brain" on the phone section); Parked full; Moving: the Settings lock.
- **Safety and driving rules:** critical alerts cannot be removed, muted or re-iconed
  ([Drive modes §8.1][dm-8.1] R3); alarm paths work with the Brain asleep
  ([ADR-0033][adr-0033] §7), so the alarm row shows "Works even when the Brain is asleep";
  the rate limits of [UI §12.1][ui-12.1] apply across every source.
- **Components:** Card (tone), ListRow, Switch (new), Chip (days), time picker (new
  component: two Segmented wheels, Parked only).
- **Spec refs:** [Phone & Comms §8][pc-8], [UI §12.1][ui-12.1], [Accounts §14.5][acc-14.5]
  (SOS), [Drive modes §8.1][dm-8.1] · [app UI model §7][ua-7] · [app UI model §8][ua-8].
- **Open questions:** does Ostler ask for the iOS critical-alert entitlement for the alarm?
  Should quiet hours also hold in-car message cards, or phone push only?

### settings-driving — Driving rules  [New]
- **Owner:** os
- **Purpose:** say plainly what changes while Moving, and hold the few owner choices that the
  rules allow.
- **Opens from → goes to:** Settings → Driving rules; the passenger prompt's "Learn more";
  the locked view's "Why?". Goes to "Using Ostler while driving" (`shell-driving-page`),
  the Phone page's settings and Display.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the Settings lock).
- **Content (top to bottom):**
  1. **This display** (read-only): "Driver-facing" or "Passenger-only (set at install)", with
     the caption "Only the install configuration can mark a screen passenger-only. No setting
     here can change it." For the D2's head unit: "Driver-facing · right-hand drive".
  2. **What changes while driving** (read-only Card): "Drive mode, warnings, Mark, your own
     map, media, climate, arming and the reverse camera stay. Everything else waits until you
     park, or a passenger can use their own phone. No typing. Message alerts show who and
     which app, never the text." Link "Using Ostler while driving".
  3. **Passenger view** (read-only): "Asked every trip. There is no 'always' and no way to
     skip the question. Ends when you park, after 15 minutes, on a red warning or in
     reverse." Then **Passenger view record**: the local log, newest first, each row "‹date
     time› · ‹trip› · ‹display› · ‹user or Car›". Caption "Kept with the trip on this device.
     Never shared or uploaded." Owner sees all rows; others see their own.
  4. **Calls while driving** (the Phone app's setting, app:phone; shown here as a shortcut):
     Switch "Only favourites ring while driving" (**off by
     default**; Phone & Comms). Caption: "Other calls go to voicemail. Every call still shows
     while it rings if this is off."
  5. **Landing**: read-only "Drive mode opens when you start driving."
  6. Row "Message alerts" → `alert-settings`.
- **States:** empty record ("No Passenger view used yet"); loading; no Phone app (row 4
  hidden, with "Install Phone & Comms to manage calls"); Parked full; Moving: the Settings
  lock (this page is not reg 109 content); locked (Car profile): read-only.
- **Safety and driving rules:** no row may unlock anything while Moving; no "always" option
  exists anywhere on the page or in the DOM ([UI §12.1][ui-12.1]); the Passenger view record
  is local only; the favourites option is the owner's (Phone decision 11).
- **Components:** Card, ListRow, Switch (new), a log list (ListRow with meta).
- **Spec refs:** [UI §3.5][ui-3.5], [UI §12.1][ui-12.1], [Phone & Comms §6.1][pc-6.1],
  [Drive modes §8.1][dm-8.1].
- **Open questions:** should "Only favourites ring" also cover Social calls (ride members
  already ring), or stay Phone only as the spec says?

<!-- refs -->
[acc-14.5]: ../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it
[adr-0033]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[pc-6.1]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#61-incoming
[pc-8]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared
[soc-12]: ../../../../specs/2026-10-07-social-addon-design.md#12-amendment-2026-10-07-dmd-round-approved-message-alerts-while-moving
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-14]: ../../../../specs/2026-10-06-ui-architecture-design.md#14-amendment-2026-10-07-dmd-round-approved-message-alerts-amends-121-alert_card-and-the-u2-legal-check
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ua-7]: ../../../../specs/2026-10-07-app-ui-model-design.md#7-notification-channels
[ua-8]: ../../../../specs/2026-10-07-app-ui-model-design.md#8-system-settings-and-the-app-info-page
