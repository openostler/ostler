---
title: "Designer brief — Phone & Comms add-on: calls, message cards, widgets, pairing, bridge, Messages and settings"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md]
summary: >
  Page content for the remaining indexed Phone & Comms screens (incoming call and in call
  through the shell's one `call` template, the message alert card for SMS, iMessage and bridged
  messengers, the Favourites, Phone pane and Recent calls widgets, pairing a phone with numeric
  comparison and the hands-free choice, and the companion app's Android notification bridge
  setup) plus two new screens the spec defines: the Messages tab (sender and app, first line
  opt-in) and the Phone settings tab. States, driving rules, rate limits and components.
---

# Phone & Comms, part b: calls, messages, widgets and setup

Example numbers and names in quotes are label formats, not data.

Part a: [60-apps-phone-a.md](60-apps-phone-a.md). One call session is owned by the shell
for Phone and Social ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C1, [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)); one alert pipeline with shared rate limits
([Phone & Comms §8](../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared)).

**Phone app setup flow** (runs after install; the framework pages are in the 90-appframe files).

| Step | Screen | The user does | Can fail · recovery |
|---|---|---|---|
| 1 | phone-pairing | pairs the phone, checks six digits, picks the hands-free owner | not discoverable: "Try again"; legacy PIN refused |
| 2 | phone-contacts (consent sheet) | allows or skips reading the phonebook | skipped: Ostler contacts and favourites only |
| 3 | phone-favourites | picks up to six favourites (Contact Picker on the phone) | none: the Moving list says "No favourites" |
| 4 | phone-bridge-setup (on Android) | turns on the message bridge, or skips | iPhone: skipped with the iPhone note |

### phone-incoming — Incoming call and in call  [Existing]
- **Owner:** app:phone
- **Purpose:** ring, answer and control a call; the shell's `call` template while driving.
- **Opens from → goes to:** an HFP ring, a Social call, a dial → in call → End returns to the
  previous view or the Drive home page.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving
  (incoming and in call); hu7 Night Parked (full call screen); hu7 Deep night Moving.
- **Content (top to bottom):**
  1. Incoming: name ≤ 30 characters ("Sam", "Unknown", "WhatsApp call"), label "mobile", link
     badge "Phone"; **Answer** and **Decline** (two 76 px targets); voice "answer"/"decline".
  2. In call (Moving): name, state ("On hold"), timer "04:12"; **Mute · End · Audio**
     (car ↔ phone), or **Swap** when a second call is held.
  3. Call waiting: the second call takes the template, **Hold & answer · Decline**; never a
     stacked card.
  4. Parked full screen adds: DTMF keypad, Hold, Swap, audio route list, contact name line.
  5. After a drive: "Missed calls (2)" Card at the next Parked.
- **States:** loading "Connecting…" · error "Call dropped" · Parked: full screen · Idling and
  Moving: `call` template · Passenger view: unchanged template.
- **Safety and driving rules:** ≤ 3 buttons, no photo, no keypad, no video while Moving
  ([Phone & Comms §6.2](../../../../specs/2026-10-07-phone-comms-addon-design.md#62-in-call-call-template-while-moving-ui-121-app-model-145), [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)); every phone call shows while Moving unless "Only favourites ring
  while driving" is on ([Phone & Comms §6.1](../../../../specs/2026-10-07-phone-comms-addon-design.md#61-incoming)).
- **Components:** call template, Button, Card (missed calls).
- **Spec refs:** [Phone & Comms §6.1](../../../../specs/2026-10-07-phone-comms-addon-design.md#61-incoming) · [Phone & Comms §6.2](../../../../specs/2026-10-07-phone-comms-addon-design.md#62-in-call-call-template-while-moving-ui-121-app-model-145) · [Phone & Comms §6.4](../../../../specs/2026-10-07-phone-comms-addon-design.md#64-messenger-calls-whatsapp-signal-telegram-messenger) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)

### phone-message-card — Message card (SMS, iMessage, bridge)  [Existing]
- **Owner:** app:phone
- **Purpose:** tell the driver a message came, with Play and Reply, never the text while Moving.
- **Opens from → goes to:** MAP or bridge notification → card → Play (read aloud) or Reply →
  `short_list` (Speak a reply, up to five canned) → "Sent" 2 s → back to the Drive home page.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving;
  hu7 Night Parked with first-line preview on; hu7 Night-dim Moving Reply list.
- **Content (top to bottom):**
  1. Icon of the app; line 1 sender ≤ 30 ("Sam", "Sam · Peak ride"); line 2 the real app
     ("Messages", "WhatsApp", "Social · 3 new").
  2. Buttons **Play** · **Reply** (Reply only when the messenger exposes a reply action).
  3. Reply list: "Speak a reply", then "Driving, will reply later", "On my way", "Running
     late", "OK, thanks", "Call you when I stop".
  4. Opt-in preview (Parked arrival only): line 2 becomes "Running 10 min late…" (≤ 30), and
     reverts to the app name once Moving.
- **States:** Moving: as above, leaves after 8 s or Back · Parked: preview if opted in ·
  rate-limited: no card, the comms chip and Home show the count.
- **Safety and driving rules:** one card at a time, one per conversation per 2 min, three per
  10 min across Social and Phone; never over a red telltale, the reverse camera, the `call`
  template or a manoeuvre prompt ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44), [Phone & Comms §8](../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared)).
- **Components:** alert_card, short_list (Reply).
- **Spec refs:** [Phone & Comms §7.1](../../../../specs/2026-10-07-phone-comms-addon-design.md#71-sms-and-imessage-map-both-platforms) · [Phone & Comms §7.2](../../../../specs/2026-10-07-phone-comms-addon-design.md#72-android-notification-bridge-opt-in) · [Phone & Comms §8](../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared) · [UI §14](../../../../specs/2026-10-06-ui-architecture-design.md#14-amendment-2026-10-07-dmd-round-approved-message-alerts-amends-121-alert_card-and-the-u2-legal-check) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap)

### phone-widgets — Phone widgets  [Existing]
- **Owner:** app:phone
- **Purpose:** the Favourites tile, the Phone pane and Recent calls for home pages and Drive.
- **Opens from → goes to:** the widget picker (shell-widget-picker) → placed on Home or in a
  Drive home page; taps route through the shell (a favourite starts a call).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  Moving (Favourites `short_list`, Phone pane idle); hu7 Night Parked; phone Night.
- **Content (top to bottom):**
  1. **Favourites** (medium, wide): rows name + source glyph; settings "Rows 1–6".
  2. **Phone pane** (wide, Drive): idle shows "Sam's Pixel · 78 % · 4 bars" and a voice-dial
     Button; in a call it becomes the `call` template.
  3. **Recent calls** (medium, wide, Home only): last 3 calls; Moving: "Available when parked".
  4. Comms chip (strip, shell-owned): battery, signal, or "Call · 04:12".
- **States:** no phone: "No phone connected" · Parked: Parked views · Moving: templates only.
- **Safety and driving rules:** `short_list` counts as a pane; ≤ 4 Hz refresh ([App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)).
- **Components:** short_list, call template, ListRow, Chip (comms).
- **Spec refs:** [Phone & Comms §12](../../../../specs/2026-10-07-phone-comms-addon-design.md#12-widgets-and-drive-menu-app-model-15-contract) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots) · [Drive modes §4.3](../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping)

### phone-pairing — Pair a phone  [Existing]
- **Owner:** app:phone
- **Purpose:** pair a phone with the Brain securely and choose who is the hands-free.
- **Opens from → goes to:** Phone → Settings → "Pair a phone"; the no-phone Card → phone-page.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone · tablet. **Draw first:** hu7 Night
  Parked (each step); phone Night.
- **Content (top to bottom):**
  1. Step 1: "Open Bluetooth on your phone and choose 'Ostler'". Countdown Chip "Discoverable
     for 1:58".
  2. Step 2: six digits in a Card ("482 913"), "Do these match your phone?" **Yes, pair** ·
     **No**.
  3. Step 3: Segmented "Ostler is the hands-free" (default) · "My head unit is the hands-free".
  4. Step 4: "Paired to you (owner)". Rows of paired phones with "Forget"; "Forget all phones".
- **States:** timeout: "Not discoverable any more · Try again" · legacy PIN refused: "This
  phone uses an old pairing method Ostler doesn't accept" · Parked: full · Idling: with Park
  evidence, else as Moving · Moving: locked view.
- **Safety and driving rules:** Parked only, owner or driver role, 2-minute window, numeric
  comparison only ([Phone & Comms §13](../../../../specs/2026-10-07-phone-comms-addon-design.md#13-security)).
- **Components:** Sheet, Card (six digits), Segmented, Button, Chip (countdown).
- **Spec refs:** [Phone & Comms §13](../../../../specs/2026-10-07-phone-comms-addon-design.md#13-security) · [Phone & Comms §3.2](../../../../specs/2026-10-07-phone-comms-addon-design.md#32-ostler-hfp-on-the-brain-path-b)

### phone-bridge-setup — Companion: notification bridge setup (Android)  [Existing]
- **Owner:** app:phone
- **Purpose:** on the phone, turn on the opt-in bridge that brings messenger alerts to the car.
- **Opens from → goes to:** companion app → Phone & Comms → "Messages from other apps" →
  Android notification access → back here → per-app allow list.
- **Layout classes:** phone. **Draw first:** phone Night and Day.
- **Content (top to bottom):**
  1. Card "What Ostler reads": "Sender name, the newest message, the app, whether you can
     reply. No photos, stickers or attachments. Nothing leaves your phone and car."
  2. Button "Open Android notification access" (sideloaded builds add "Allow restricted
     settings" steps).
  3. Allow list (empty by default), suggested rows with Toggles: WhatsApp, Signal, Telegram,
     Messenger, Google Messages.
  4. Note: "Only conversations are bridged. Ostler's own messages never go through here."
- **States:** access off: Card + Button · on: list · Moving: phone Moving banner; settings
  readable.
- **Safety and driving rules:** opt-in, Parked on the phone; replies only through the app's own
  reply action ([Phone & Comms §7.2](../../../../specs/2026-10-07-phone-comms-addon-design.md#72-android-notification-bridge-opt-in)).
- **Components:** Card, ListRow (Toggle), Button.
- **Spec refs:** [Phone & Comms §7.2](../../../../specs/2026-10-07-phone-comms-addon-design.md#72-android-notification-bridge-opt-in) · [Phone & Comms §3.3](../../../../specs/2026-10-07-phone-comms-addon-design.md#33-the-companion-bridge-path-a) · [Phone & Comms §9](../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy)

### phone-messages — Phone: Messages tab  [New]
- **Owner:** app:phone
- **Purpose:** recent SMS, iMessage and bridged messages by sender and app, for reading Parked.
- **Opens from → goes to:** Phone → Messages → a row → Play, Reply (`short_list` or keyboard
  Parked) or "Open on phone".
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; hu7 Night-dim Moving (locked frame).
- **Content (top to bottom):** 1. Rows: app icon, sender, app name, time, unread dot; first
  line only if the opt-in is on. 2. Row actions: Play · Reply. 3. Caption: "Messages stay in
  the Brain's memory for 10 minutes or until played."
- **States:** empty: "No new messages" · iPhone: "Messages only" note · Parked: full · Moving:
  locked; alerts arrive as cards.
- **Safety and driving rules:** bodies never written to disk ([Phone & Comms §7.1](../../../../specs/2026-10-07-phone-comms-addon-design.md#71-sms-and-imessage-map-both-platforms)).
- **Components:** ListRow, Button.
- **Spec refs:** [Phone & Comms §7.1](../../../../specs/2026-10-07-phone-comms-addon-design.md#71-sms-and-imessage-map-both-platforms) · [Phone & Comms §10](../../../../specs/2026-10-07-phone-comms-addon-design.md#10-ui-per-layout-class-and-driving-state)

### phone-settings — Phone: Settings tab  [New]
- **Owner:** app:phone
- **Purpose:** paired phones, hands-free owner, who rings, alerts and data.
- **Opens from → goes to:** Phone → Settings → phone-pairing, phone-bridge-setup (on the phone).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; desktop Night.
- **Content (top to bottom):**
  1. Paired phones: name, owner user, hands-free owner, "Forget".
  2. "Pair a phone" Button.
  3. "Only favourites ring while driving" Toggle (off; others go to voicemail).
  4. Alerts: "Phone" filter per app, "Show first line of messages when parked" (off).
  5. Data: "Export favourites and call log", "Delete call log".
- **States:** Parked: full · Idling: with Park evidence · Moving: locked view.
- **Safety and driving rules:** settings changed Parked only ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** ListRow, Toggle, Button.
- **Spec refs:** [Phone & Comms §6.1](../../../../specs/2026-10-07-phone-comms-addon-design.md#61-incoming) · [Phone & Comms §8](../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared) · [Phone & Comms §9](../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy) · [Phone & Comms §13](../../../../specs/2026-10-07-phone-comms-addon-design.md#13-security)
