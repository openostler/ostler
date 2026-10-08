---
title: "Designer brief 40-i — alerts and calls: message card, reply list, voice reply, other alert cards, alert settings and the call template"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-community-hub-design.md, references/research/message_alerts_android_auto.md, references/research/driver_distraction_rules.md]
summary: >
  Alerts and calls brief file. It gives the message-reply flow step list, then the approved
  message alert card (sender and app with Play and Reply, its burst, group, long-message,
  legal-fallback and "Sent" variants, and the opt-in first-line preview only for messages that
  arrive while Parked), the reply short list with canned replies, the new voice-reply
  read-back screen with Send and Cancel, the other alert cards (alarm, maintenance due at trip
  start or end, convoy, navigation off route, missed calls, community), the alert settings
  page, and the shared call template: incoming, in call, push-to-talk, group and call waiting. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 40-i — Alerts and calls

Back to [40-a](40-drive-a.md) for the file list. One OS alert pipeline serves every app
(Social, Phone, Map …); the OS draws every card, never the app
([Social §13][soc-13] C2).

**Flow: answer a message while Moving (≤ 3 screens, ending in Drive mode).**

| Step | Screen | User does | Can fail · recovery |
|---|---|---|---|
| 1 | `alert-message` | sees sender and app; taps **Play** or **Reply**, or ignores it (leaves after 8 s) | nothing chosen · message stays unread, count on the strip |
| 2 | `alert-reply-list` | taps a canned reply (sends) or **Speak a reply** | send fails · "Not sent · will retry", unread kept |
| 3 | `alert-voice-reply` | speaks; hears it read back; **Send** or **Cancel** (Cancel focused) | no speech heard · "Didn't catch that" with **Try again** / Cancel |
| end | `alert-message` "Sent" (2 s) → Drive mode | — | — |

### alert-message — Message alert card  [Existing]
- **Purpose:** tell the driver a message arrived without showing its text.
- **Owner:** os
- **Opens from → goes to:** a new message from any messaging app (Social, Phone); **Play** reads it
  aloud; **Reply** → `alert-reply-list`; `back`, a swipe or 8 s dismiss it.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving
  over the Dashboard cluster; hu5 Night-dim Moving; hu7 Night Parked with the preview; phone
  Night.
- **Content:** 1. App icon (from the app's manifest). 2. Line 1 the sender, ≤ 30
  characters, cut with "…": "Sam"; group or ride: "Sam · Peak ride". 3. Line 2 the app:
  "Social"; burst: "Social · 3 new". 4. **Play** (`play_arrow`, focused first) and **Reply**
  (`reply`). Placed at the bottom of the content area on the passenger side.
- **Variants:** **first-line preview** (owner opt-in, off by default): only for a message
  that arrived while Parked (or Idling with Park evidence once the legal opinion allows),
  line 2 shows the first line ≤ 30 characters, attachments as "Photo", "Voice note",
  "Location", links as "Link"; it reverts to the app name the moment the car moves. **Long
  message** (over 280 characters): Play announces "Sam sent a long message" with **Play all**
  and **Stop**. **Legal fallback**: line 1 "New message". **Sent** for 2 s after a reply.
- **States:** Moving: sender and app only, never text, images, avatars or previews, preview
  setting included. Parked: same card, preview if opted in. Passenger-only display: never a
  preview. Rate limits: one card on screen; one per conversation per 2 minutes; three per 10
  minutes overall, then only the unread count on the comms chip and Home; group messages
  (other than the ride channel) count only unless allowed. A card waits behind a red
  telltale, the reverse camera, the call template or a manoeuvre prompt and is dropped to the
  count after 2 minutes. One short chime per card.
- **Safety and driving rules:** `alert_card`: icon + ≤ 2 lines of ≤ 30 characters, ≤ 2
  buttons; takes focus on its safest button; shell-drawn and never removable
  ([UI §12.1][ui-12.1], [UI §14][ui-14]).
- **Components:** `alert_card`, Button (Play, Reply). Tokens `type-body` (≥ 24 px), focus
  ring, no glow (default look).
- **Spec refs:** [UI §12.1][ui-12.1] · [UI §14][ui-14] · [Social §12][soc-12] ·
  [Phone & Comms §8][pc-8] · [research §2][r-ma-2].
- **Open questions:** none (approved 2026-10-07).

### alert-reply-list — Reply list  [Existing]
- **Purpose:** reply in one tap or by voice.
- **Owner:** os
- **Opens from → goes to:** **Reply** on a message card; a canned reply sends and returns to
  the card ("Sent"); **Speak a reply** → `alert-voice-reply`; `back` → Drive mode.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving.
- **Content (`short_list`, ≤ 6 rows, ≤ 30 characters):** 1. **Speak a reply** (`mic`). 2.
  The user's canned replies, default: "Driving, will reply later", "On my way", "Running
  late", "OK, thanks", "Call you when I stop".
- **States:** empty canned list: only Speak a reply. Sending: row shows "Sending…". Moving:
  as above; canned replies cannot be edited. Parked: same list; **Edit replies** link to
  `alert-settings`.
- **Safety and driving rules:** one level; a canned reply is a normal outbound message, never
  an action ([UI §12.1][ui-12.1]).
- **Components:** `short_list`, Button.
- **Spec refs:** [UI §14][ui-14] · [Social §12][soc-12].
- **Open questions:** none.

### alert-voice-reply — Speak a reply and read-back  [New]
- **Purpose:** reply by voice with no transcript on screen.
- **Owner:** os
- **Opens from → goes to:** **Speak a reply**; **Send** → "Sent" → Drive mode; **Cancel** →
  Drive mode.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving
  (listening, then read-back).
- **Content:** 1. Listening: `mic` with the word "Listening…" and a seconds count as text
  ("12 s of 30 s"); no waveform animation. 2. Voice note path (default): the clip is sent as
  a voice note (≤ 30 s). 3. On-device speech to text (where available): the shell reads the
  text back aloud; screen shows only "Send this reply?" with **Send** and **Cancel** (Cancel
  focused). Never the transcript while Moving.
- **States:** nothing heard: "Didn't catch that" with **Try again** and **Cancel**. Parked:
  the transcript may show. No microphone: the row is absent from the reply list.
- **Safety and driving rules:** no transcript text while Moving (as the Automotive
  `NO_VOICE_TRANSCRIPTION` restriction); task ends in Drive mode ([UI §12.1][ui-12.1]).
- **Components:** `alert_card` (two buttons), Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [Social §12][soc-12] · [research §3][r-ma-3].
- **Open questions:** none.

### alert-other — Other alert cards  [Existing]
- **Purpose:** every non-message alert in the one card shape.
- **Owner:** os
- **Opens from → goes to:** the raising feature; buttons as listed; `back` dismisses where a
  dismiss is allowed.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving
  (alarm, off route); hu7 Night Parked (maintenance at trip end).
- **Content (each icon + ≤ 2 lines of ≤ 30 characters, ≤ 2 buttons):**
  1. **Security alerting** (safety item): `shield` in `alarm`, "Alarm: alerting", "Motion
     detected"; **Open** (Parked) or **Mark** (Moving). Pulses; never removable.
  2. **Maintenance due** (only at trip start or end, never mid-drive): `build` "Oil service
     due in 300 km", "Maintenance"; **Open** (Parked), **OK**.
  3. **Convoy:** `groups` "Convoy: a member stopped", "Map"; **OK**. No names.
  4. **Off route** (Navigation): "Off route · rerouting in 8 s" with **Reroute** (focused) and
     **Keep route**; seconds count as text, no bar; the focused choice applies at zero.
  5. **Missed calls** at the next Parked: "Missed calls (2)", "Phone"; **Open**.
  6. **Community** (Parked only): "2 replies on your help request", "Community"; **Open**.
- **States:** Moving: one card at a time; a red telltale or the reverse camera holds the
  others. Parked: same shape. Reduced motion: the alarm pulse becomes a static ring.
- **Safety and driving rules:** only navigation and display choices may count down and
  auto-apply; nothing that reaches the gate ([shell input §7][si-7]).
- **Components:** `alert_card`. Status tokens with icon and word.
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1] · [Maintenance §8][mg-8] ·
  [Vehicles & Map §7][vm-7] · [Navigation §5.3][nav-5.3] · [Phone & Comms §8][pc-8] ·
  [Community §15.2][hub-15.2].
- **Open questions:** the community spec gives head units no alert card, only a Home card and
  a count; confirm the Parked card or drop it.

### alert-settings — Message alert settings  [Existing]
- **Purpose:** the owner's and each user's message-alert choices, edited Parked.
- **Owner:** os
- **Opens from → goes to:** Settings → Alerts (see the open question in
  [40-c](40-drive-c.md)); **Edit replies** from the reply list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day; hu7 Night Parked.
- **Content:** 1. **Canned replies**: up to five rows, each ≤ 30 characters with a counter,
  reorder, delete, **Add reply**, **Restore defaults**. 2. **Show first line of messages when
  parked** (off by default) with the line "Never shown while moving." 3. **Alert for group
  messages** (off by default; the active ride channel always alerts). 4. **"I'm driving"
  auto-reply**: Off · Ride members · Favourites · All contacts (default favourites and ride
  members), text ≤ 60 characters. 5. Per-app filters (Social, Phone).
- **States:** Parked: full. Idling: edits need Park evidence. Moving: locked view.
- **Safety and driving rules:** text entry Parked only; links and placeholders are refused in
  canned replies ([UI §12.1][ui-12.1]).
- **Components:** ListRow, Segmented, switch, Button.
- **Spec refs:** [UI §14][ui-14] · [Social §12][soc-12] · [Phone & Comms §8][pc-8].
- **Open questions:** none.

### call-template — Call template (incoming, in call, PTT, call waiting)  [Existing]
- **Purpose:** the one shell-drawn surface for every audio call and push-to-talk channel.
- **Owner:** os
- **Opens from → goes to:** the OS call session (requested by the Phone or Social app); the comms
  chip reopens it; ends back in Drive mode or where the user was.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving
  incoming, in call and call waiting; hu5 Night-dim Moving in call; phone Night.
- **Content:**
  1. **Incoming:** name ≤ 30 (or the number, "Unknown", or "WhatsApp call"), no photo, link
     badge ("Phone" or "Social"), **Answer** (`call`) and **Decline** (`call_end`).
  2. **In call:** name, timer "04:12", state ("On hold"), **Mute** (`mic_off`), **End**, and
     **Audio** (car or phone) or **Swap** when a second call is held.
  3. **Call waiting:** the second call takes the template: "Sam · calling", **Hold & answer**
     and **Decline**; never a stacked card.
  4. **PTT:** **Hold to talk**, "who's talking" as one name, **Mute**, **End**; a group shows
     a count ("5 in ride"), not a list; during a phone call it reads "Ride: on hold".
- **States:** Moving: ≤ 3 buttons ≥ 76 px, audio only. Parked: same template; video only on
  displays that are not driver-facing. Ended: "Call ended" for 2 s. Missed while Moving: one
  card at the next Parked.
- **Safety and driving rules:** never video or message text on a driver-facing display,
  Passenger view included; a message card never covers it ([UI §12.1][ui-12.1],
  [app model §14.5][am-14.5]).
- **Components:** call template, Button. Status tokens; focus ring.
- **Spec refs:** [UI §12.1][ui-12.1] · [app model §15.5][am-15.5] · [Social §13][soc-13] ·
  [Phone & Comms §6.1][pc-6.1] · [Phone & Comms §6.2][pc-6.2].
- **Open questions:** none.

[am-14.5]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-15.5]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[hub-15.2]: ../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[nav-5.3]: ../../../../specs/2026-10-07-navigation-addon-design.md#53-off-route-and-reroute
[pc-6.1]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#61-incoming
[pc-6.2]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#62-in-call-call-template-while-moving-ui-121-app-model-145
[pc-8]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared
[r-ma-2]: ../../../research/message_alerts_android_auto.md#2-is-a-one-line-preview-lawful-or-advised
[r-ma-3]: ../../../research/message_alerts_android_auto.md#3-copy--avoid--decide-for-ostler
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[soc-12]: ../../../../specs/2026-10-07-social-addon-design.md#12-amendment-2026-10-07-dmd-round-approved-message-alerts-while-moving
[soc-13]: ../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-14]: ../../../../specs/2026-10-06-ui-architecture-design.md#14-amendment-2026-10-07-dmd-round-approved-message-alerts-amends-121-alert_card-and-the-u2-legal-check
[vm-7]: ../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving
