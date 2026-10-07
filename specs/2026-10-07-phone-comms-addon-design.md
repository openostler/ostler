---
title: "Phone & Comms add-on — dialer, contacts, Bluetooth hands-free on the Brain, companion bridge and phone notifications — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/phone_comms.md, references/research/driver_distraction_rules.md, references/research/message_alerts_android_auto.md, references/research/calls_video_camera_sharing.md, docs/feature_map_dmd.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-module-bus-messages-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Draft for the owner (DMD round, 2026-10-07). Recommends widening the proposed `ostler-app-phone` (phone mirroring) into one Phone & Comms add-on rather than a separate `ostler-app-dialer`: dialer (keypad Parked only; while Moving voice dial, a favourites `short_list` of at most six and the audio-only `call` template), one contacts view combining Ostler contacts and phone contacts badged by source, recents, and phone notifications. Calls run mainly through the Brain acting as a Bluetooth hands-free unit (HFP HF via PipeWire's native backend and its telephony D-Bus API on Raspberry Pi OS Trixie, behind an adapter for BlueZ's coming call control; PBAP for the phonebook and call history, MAP for SMS and iMessage), which works the same for Android and iPhone and puts call audio in the car; the companion phone app adds the Contact Picker for favourites and, on Android only, an opt-in notification bridge (NotificationListenerService, MessagingStyle, the messenger's own RemoteInput for replies) whose alerts share the shell's one alert pipeline and rate limits with Social. WhatsApp, Signal, Telegram and Messenger calls ring through only where the app hands them to the phone's calling stack; no unofficial messenger libraries; Telegram native only via TDLib later, Matrix through Social. Phone contacts and bridged messages never leave the user's in-car devices and are not persisted by default. Phases PH0–PH4, tests and owner decisions; a matching proposed amendment to the Social spec settles the shared call session, alert pipeline, favourites and call log.
---

# Phone & Comms add-on — design (draft)

**Status: draft for the owner (DMD round, 2026-10-07).** Nothing is built. Evidence:
[phone and comms research](../references/research/phone_comms.md) (cited as *research §n*),
[driver-distraction rules](../references/research/driver_distraction_rules.md),
[message alerts](../references/research/message_alerts_android_auto.md). It turns the
[DMD feature map](../docs/feature_map_dmd.md)'s "Needs spec: phone add-on" rows (Phone Link,
ANCS, notification filter, last notifications) into a design, and the overlap with Social is
settled in the [Social spec's proposed amendment §13](2026-10-07-social-addon-design.md#13-proposed-amendment-2026-10-07-dmd-round-comms-overlap).

## 1. Scope and non-goals

**Owner's ask (2026-10-07):** widen `ostler-app-phone` or propose `ostler-app-dialer`; a
dialer (keypad, recents, favourites; keypad only when Parked; while Moving voice dial, a
favourites `short_list` of ≤ 6 and the audio-only `call` template); one contacts view of
Ostler and phone contacts badged by source, phone contacts read with permission, kept on the
device, never uploaded or synced; two connection paths; messenger calls and messages; widgets.

**In scope.** Phone calls (cellular, and VoIP calls the phone exposes) answered, placed and
controlled from car screens; contacts; recents; favourites; SMS/iMessage via MAP; Android
notification bridge for messengers; phone status (battery, signal) on the strip; widgets and
Drive-menu rows.

**Non-goals.**
- Not a calling service: Ostler-to-Ostler calls, PTT and rides stay in **Social**; Phone hands
  an Ostler contact's call to Social (§6.3).
- No phone-screen mirroring or projection (no Android Auto/CarPlay receiver; ADR-0042 leave-out).
- No unofficial WhatsApp, Signal or Messenger clients or libraries (research §4).
- No call recording, ever (ADR-0010); no voicemail transcription; no message storage.
- No upload or sync of phone contacts, call history or messages to Ostler Cloud, a relay,
  another user or another vehicle.
- No vehicle actions (ADR-0033): the manifest declares none.
- Not the default dialer or SMS app on any phone (research §3.1).

## 2. Repo recommendation: widen `ostler-app-phone`

**Recommend one add-on, `ostler-app-phone`, named "Phone" in the shell**, covering mirroring
(notifications, last notifications), the dialer, contacts and recents. Reasons:
- **One connection layer.** The dialer and mirroring use the same two paths: the Brain's
  Bluetooth link to the phone (HFP, PBAP, MAP) and the companion bridge. Two add-ons would
  both need the phone pairing, the same Brain service and the same consent screens.
- **One alert source.** Incoming calls, SMS and bridged messages are one stream that must share
  the shell's alert pipeline and rate limits (§8); splitting them puts the arbitration
  between two add-ons of ours.
- **ADR-0034's split test** (toolchain, licence, cadence, contributors) gives no reason to
  split: same licence, same platform contributors (Bluetooth on the Brain, native on phones).
- DMD itself ships "Phone Link" as one feature.

**Alternative:** `ostler-app-dialer` (dialer, contacts, recents, HFP) plus `ostler-app-phone`
(notifications only). Cleaner names, but two add-ons that must both be enabled for a normal
"phone in the car" and that both need the Brain's Bluetooth service. Decision 1.

**What lives where** (ADR-0034, app-model §7.1 and §14.3):

| Part | Repo | Runs on |
|---|---|---|
| Phone add-on UI (views, widgets, manifest) | `ostler-app-phone` (AGPL-3.0-or-later) | bundled into the Brain's shell and the phone build |
| `ostler-hfp` service (HFP HF, PBAP, MAP adapter; §3.2) | `ostler-app-phone`, packaged for the Brain | Brain (separate process; talks D-Bus to PipeWire and BlueZ) |
| Companion bridge (Contact Picker, notification listener, status) | source in `ostler-app-phone`, compiled into the **one store app** as a native plugin | the user's phone; native features stay fixed in the binary (app-model §14.3) |

## 3. Architecture

### 3.1 Two paths and the fallback ladder

```
            ┌───────────── (b) Bluetooth: HFP HF + PBAP + MAP ─────────────┐
 Phone ─────┤                                                              ├──► Brain: ostler-hfp ──► shell (call session, alerts) ──► displays
            └── (a) companion bridge over the paired local link (HTTPS) ───┘        └─► audio: AEC ─► DAC/USB ─► amp or head-unit AUX
```

| Feature | Primary | Fallback | Last resort |
|---|---|---|---|
| Ring, answer, reject, end, mute, call audio in car | **(b) HFP on the Brain** (Android and iOS) | head unit owns HFP: Phone shows call state from (a) on Android, nothing on iOS | phone's own UI |
| Place a call | (b) `Dial` | (a) Android `ACTION_CALL` (audio stays where the phone routes it) | — |
| Phonebook | (b) PBAP pull (with consent) | (a) Contact Picker favourites | Ostler contacts only |
| Recents | (b) PBAP call history | Ostler's own local call log (calls handled through the car) | — |
| SMS / iMessage | (b) MAP (iPhone needs "Show Notifications") | — | — |
| Messenger messages | (a) **Android bridge** (opt-in) | iOS: none in v1; ANCS later (§7.3) | — |
| Phone battery, signal | (b) HFP indicators | (a) bridge status | — |

**Without a Brain** (Ostler Diagnostics alone) there is no car-side Bluetooth: Phone offers
only Parked views on the phone itself, which add nothing to the phone's own dialer, so the
add-on requires a Brain (`requires.devices: [{kind: "brain"}]`; Decision 3).

### 3.2 `ostler-hfp` on the Brain (path b)

- **Stack:** Raspberry Pi OS **Trixie** baseline (PipeWire 1.4.2, WirePlumber 0.5.8),
  **PipeWire native HFP backend** with role `hfp_hf` (on by default) and its
  **`org.pipewire.Telephony`** D-Bus API for dial, answer, hang up, hold, swap, DTMF, line and
  name (research §2.1). BlueZ obexd for PBAP and MAP (research §2.2). `ostler-hfp` is the only
  client of these and hides them behind an **adapter** (`TelephonyBackend`: `pipewire`,
  `bluez_cc` when BlueZ's unified call control lands, `ofono` for Bookworm or as fallback),
  so the move Collabora announced is a backend swap, not a redesign. Decision 2.
- **Codecs:** CVSD always, mSBC where the controller supports it; LC3-SWB only after a bench
  pass (research §2.1).
- **Radio:** the Pi 5's onboard Bluetooth first; a listed USB dongle if the bench shows
  Wi-Fi/Bluetooth coexistence dropouts while the Brain is also a hotspot (research §2.1).
- **Audio:** SCO → PipeWire `module-echo-cancel` (WebRTC AEC) → Brain output (I²S DAC or USB
  audio) → the amp or the head unit's AUX; a cabin mic near the driver → AEC → SCO.
  `ostler-hfp` sends `AT+NREC=0` so the phone's own echo cancelling does not double up.
  Media and navigation voice are ducked during a call. The install wizard plays a test call
  loop (Parked) to set mic gain and AEC delay. No audio is written to disk (ADR-0010).
- **One hands-free owner per phone** (research §2.4): at pairing the owner chooses **"Ostler
  is the hands-free"** (Brain HFP + PBAP + MAP) or **"My head unit is the hands-free"** (the
  Brain connects PBAP and MAP only, if the phone allows it, and never HFP; calls are shown
  from the Android bridge or not at all). Decision 4.
- **MQTT** (module-bus §16 practice; device `phone`, own prefix only; no command topics):

| Topic (`ostler/v1/<vid>/…`) | Content |
|---|---|
| `phone/state/link` | per paired phone: connected profiles, owner user id, hands-free owner, battery %, signal bars, roaming (retained) |
| `phone/state/call` | ringing, dialling, active, held; duration; label **class only** ("contact", "unknown", "app") (retained, expiry) |

  **Names, numbers, phonebook entries and message bodies never go on the broker**; the shell
  gets them from `ostler-hfp` over the authenticated local API for the signed-in user, in
  memory (§9).

### 3.3 The companion bridge (path a)

A native plugin in the one store app, enabled per feature by the user:

| Feature | Android | iOS |
|---|---|---|
| Pick favourites from the phone's contacts | **Contact Picker** (no permission; one contact per pick) | `CNContactPickerViewController` (no permission for a pick) (U) |
| Notification bridge | `NotificationListenerService` (opt-in; §7) | not in v1 |
| Place a call when HFP is not available | `ACTION_CALL` with `CALL_PHONE` | `tel:` URL, confirmed on the phone |
| Call state when the head unit owns HFP | `TelephonyCallback` call state only (no number without `READ_CALL_LOG`) (U) | `CXCallObserver` state only |

The bridge talks only to the paired Brain origin over local HTTPS (ADR-0021; app-model §7.1
risk "native bridge exposure"), never through the relay. **Not used:** the default-dialer role,
`READ_CALL_LOG`, SMS permissions, companion-device watch/glasses profiles, `READ_CONTACTS` in
the store build (research §3.1; Decision 6).

## 4. Dialer

| View | Parked | Idling | Moving (driver-facing display) |
|---|---|---|---|
| **Keypad** | yes | **no**, as asked (Decision 9 offers Idling with Park evidence) | **no** (AAOS "no dialpad"; NHTSA text-entry lockout) |
| **Favourites** | grid/list, edit, reorder | read and call | **`short_list` ≤ 6** rows, name ≤ 30 characters, source badge as a glyph; tap → confirm-free call (the call itself is the feedback) |
| **Recents** | full list, filter, call back | read and call | **not shown** as a list; the Drive menu offers **Call back last** (one row) |
| **Contacts** (§5) | search, browse, call | browse, no search text | **no**; voice dial instead |
| **Voice dial** | yes | yes | yes: the shell's voice ("Call Sam mobile"); results read aloud; > 1 match → `short_list` ≤ 6; never a transcript on screen |
| **In call** | full call screen (keypad for DTMF, hold, swap, audio route) | `call` template | **`call` template** (§6) |

- **Voice dial** uses the shell's speech input (ShellInput's `ptt`/voice intent); speech
  recognition runs on the Brain or device; Phone supplies the grammar (favourites, contacts
  names) in memory. "Call *name*" with one match reads back "Calling Sam, mobile" and dials
  after 2 s unless **Cancel** (focused) is pressed.
- **DTMF** while Moving: not offered (it is a keypad); "Press 1" menus wait for Parked, or use
  the phone.
- **Emergency:** "Call 999/112" is always a Parked keypad entry and a voice phrase; it dials
  through HFP like any call. Ostler never claims to be an emergency dialler; Crash SOS is a
  separate core spec.

## 5. Contacts: one view, two sources

- **Ostler contacts** come from core accounts (accounts §14.6): display name, groups, peer
  key; **no phone numbers** (accounts §14.6 rule kept). Calling one hands off to Social (§6.3).
- **Phone contacts** come from the phone: PBAP pull over (b) after a consent sheet ("Let Ostler
  read *Sam's Pixel*'s contacts in this car? They stay on this Brain while the phone is
  connected and are never uploaded."), or single picks over (a).
- **One list**, sorted by name, each row badged **Ostler**, **Phone** or both. A local
  **link** (owner taps "Same person") joins an Ostler contact and a phone contact into one row;
  the link is a local record on that Brain for that user, never synced, never inferred
  automatically (Ostler contacts have no numbers to match).
- **Storage** (Decision 5): the PBAP phonebook is held **in memory per connected phone and
  user**, rebuilt on each connection, wiped on disconnect, Brain shutdown or the user signing
  out; no file, no backup, no export, no MCP or SDK exposure beyond the Phone add-on's own
  views. **Favourites** are the one persisted item: name, the chosen number (or the Ostler
  contact ref), source, order; per user, on the Brain; included in the user's data export
  (app-model §14.6 exit guarantee) and deleted with the user.
- **Per user, per phone.** A phonebook is visible only to the signed-in user who paired that
  phone; a second driver's phone is a separate source; a guest never sees the owner's
  phonebook. The head unit's signed-in user decides which phone's contacts show.
- **Registry:** Phone registers the data classes `phone_contacts` and `call_history`
  (`contributes.data_classes`, accounts §14.1), both **audience `me` only, not shareable**
  (no audience above `me` may be set); they start in ghost like every class.

## 6. Calls

### 6.1 Incoming
1. HFP rings → `ostler-hfp` resolves the number against the in-memory phonebook and favourites.
2. The shell's **call session** (Social amendment §13 C1) raises the `call` template: name
   (or number, or "Unknown", or "WhatsApp call" when the label is an app), ≤ 30 characters,
   no photo; **Answer / Decline**; voice "answer" / "decline". A steering-wheel or keypad
   button mapped by ShellInput to `ok`/`back` answers/declines.
3. While Moving, every phone call is shown (the phone rings in-band regardless; hiding the card
   would leave a ringing phone with no control). Owner option "Only favourites ring while
   driving" **declines** others to voicemail with `AT+CHUP`, off by default (Decision 11).

### 6.2 In call (`call` template while Moving; UI §12.1, app-model §14.5)
Name, timer, state ("On hold"), link badge "Phone"; three buttons: **Mute**, **End**, and
**Audio** (car ↔ phone) or **Swap** when a second call is held. No keypad, no contact card,
no video. Call waiting: the second call takes the template with **Hold & answer / Decline**
(HFP `HoldAndAnswer`), never a stacked card.

### 6.3 Ostler contacts
A favourite or contact with only an Ostler source calls through **Social** (`ostler-app-social`
voice call, Social §5), via the shell's call session; if Social is not enabled the row reads
"Needs Social" (Parked) and is hidden while Moving.

### 6.4 Messenger calls (WhatsApp, Signal, Telegram, Messenger)
- They ring in the car **only if** the messenger hands the call to the phone's calling stack
  (Android Telecom/Core-Telecom; iOS CallKit), which then exposes it over HFP like a phone
  call (research §5). Answer, decline, end and mute work as for phone calls where the phone
  honours them; the name is often missing, shown as "Unknown" or the app name.
- Where the app does not, the call rings on the phone only; audio may still route over SCO.
  Phone never tries to answer such calls through notification actions.
- Bench matrix (PH1 exit): four messengers × Pixel, Samsung, iPhone × ring, name, answer,
  decline, end, audio route. The "Using Ostler while driving" page lists what works.

### 6.5 Call log
Calls handled through the car are logged locally by the shell's call session (Social
amendment §13 C4): direction, label, number (phone calls) or contact ref (Ostler calls),
start, duration, source; per user; 90-day retention; never uploaded; exportable by the user.
Recents shows PBAP history (phone's own, in memory) merged with this log, de-duplicated by
time and number.

## 7. Messages

### 7.1 SMS and iMessage (MAP, both platforms)
MAP notifications arrive at `ostler-hfp`; the shell's message `alert_card` follows the UI spec
§12.1 as amended by §14 (sender + app "Messages", Play, Reply; voice reply or a canned reply
sent with MAP `PushMessage`; first-line preview only for messages that arrive while Parked,
opt-in, off by default). Bodies stay in memory until read aloud or 10 minutes, whichever is
first; never written to disk.

### 7.2 Android notification bridge (opt-in)
- **Turn on (Parked, on the phone):** the companion app explains what it reads, then opens
  Android's notification-access screen. Sideloaded builds also need "Allow restricted settings"
  (research §3.1); the store build does not.
- **Per-app allow list**, empty by default, suggested: WhatsApp, Signal, Telegram, Messenger,
  Google Messages. Only notifications with **`MessagingStyle`** (conversations) are bridged;
  everything else is dropped on the phone. The Ostler app's own notifications are never
  bridged (Social reaches the car directly).
- **What crosses to the Brain:** app id and name, conversation key (hashed on the phone),
  sender display name, the newest message text, message count, whether a reply action with a
  `RemoteInput` exists, whether it is a group. No images, avatars, stickers, attachments or
  links (attachments named only). OTP-redacted content stays redacted (Android 15).
- **Reply:** Reply → Speak a reply or a canned reply (UI §14, the one shared list) → the bridge
  fills the messenger's own `RemoteInput` and fires its reply `PendingIntent`, then fires
  mark-as-read if present (the Android Auto path; research §3.1). If the notification has no
  reply action, Reply is not offered.
- **No auto-reply** into third-party apps (Social amendment §13 C5): the phone's own Driving
  mode does that; Telegram's terms forbid acting without the user's knowledge.
- **Retention:** bridged text lives in the Brain's memory only, until played, dismissed or 10
  minutes; the phone keeps nothing beyond Android's own notification.
- **Play policy:** notification access is a promoted core feature in the listing, with a
  prominent in-app disclosure; content is never logged, analysed or transmitted beyond the
  paired Brain (research §3.1). Decision 7.

### 7.3 iOS
v1: calls, contacts, recents and Messages through HFP, PBAP and MAP only. **ANCS** (sender and
app, plus the phone's positive/negative actions, no reply; research §3.2) is a later phase
(PH4) for "sender + app" alerts from other apps; the EU notification-forwarding interface is
watched, not planned. The Phone page says plainly: "On iPhone, Ostler shows calls and Messages;
other apps' messages stay on your phone." Decision 8.

### 7.4 Native integrations
- **Matrix:** only through Social's later Matrix bridge (Social §9).
- **Telegram:** v1 via the Android bridge only. A native **TDLib** client (own `api_id`, full
  compliance with the Telegram API Terms, user login on the phone, no actions without consent)
  is a possible separate integration add-on later, not in Phone. The Bot API stays Social's
  "notify via" route. Decision 10.
- **WhatsApp, Signal, Messenger:** bridge and HFP only; never a native client.

## 8. Alerts and rate limits (shared)

Every Phone alert enters the **shell's one alert pipeline** (Social amendment §13 C2):
incoming and waiting calls go to the call session (they are not message cards and are not
rate-limited); SMS, iMessage and bridged messages are message `alert_card`s under UI §14's
rules, with the rate limits counted **across all add-ons**: one card on screen; one per
conversation per 2 minutes (conversation = source + conversation key); three message cards per
10 minutes overall, then only the unread count on the strip chip and Home; group conversations
count only unless allowed; never over a red telltale, the reverse camera, the `call` template
or a manoeuvre prompt. A "Phone" filter per app sits beside Social's in More → Settings →
Alerts. Missed calls while Moving become one "Missed calls (2)" card at the next Parked.

## 9. Data and privacy

In the style of ADR-0009 ("stays on the device") and ADR-0036 ("never leaves the device"):
- **Phone contacts, phone call history and message bodies never leave the user's in-car
  devices** (the phone and the Brain); never Ostler Cloud, a relay, a mesh, MQTT, a share, a
  trip, a session log, a bundle, an MCP tool reply or analytics. Held in memory; wiped on
  disconnect (contacts) or after 10 minutes (bodies).
- **Persisted, local, per user:** favourites, the hands-free choice per phone, contact links,
  the app allow list, the Ostler call log (§6.5; 90 days). All exportable and deletable.
- **Never:** call audio or voicemail recorded (ADR-0010); phone numbers attached to Ostler
  contacts or sent to peers (accounts §14.6); VIN, `<vid>` or plate in any Phone record
  (ADR-0036).
- **Trips and logs:** a call adds no event to a trip unless the user marks one; the session
  logbook records nothing about calls.
- **Remote paths** (relay, Tailscale, mesh; ADR-0033 §6): none of Phone's views or data are
  served remotely; Phone views refuse non-local origins.

## 10. UI per layout class and driving state

| Surface | Parked | Idling | Moving |
|---|---|---|---|
| Head unit (driver-facing) | **More → Phone** page (`more:phone`): Favourites, Recents, Contacts, Keypad, Messages (sender + app; first line opt-in), Settings | as Parked, but no keypad; contact search only with Park evidence | Drive mode only; `call` template; message `alert_card`; Favourites `short_list` via widget or Drive menu; voice dial |
| Head unit passenger view | — | — | nothing beyond the templates (Phone is not reg 109 content); **Open on phone** |
| Phone (companion) | Phone settings, bridge, pairing, consent; the phone's own dialer for calls | same | Moving banner; the phone's own UI |
| Rear / passenger-only display | full Phone page for the **signed-in user of that display only**; never the driver's phonebook unless the driver signs in there | same | same |
| Desktop / browser | settings, favourites, export | — | — |
| Bike (phone in mount) | Phone is not used; the OS dialer and helmet intercom handle calls | — | — |

Strip: a **phone chip** (battery, signal, "Sam's Pixel") is folded into Social's comms chip
(Social amendment §13 C1); during a call the chip shows "Call · 04:12".

## 11. Templates used

`call` (incoming, in call, waiting), `alert_card` (messages, missed calls), `short_list`
(favourites, voice-dial matches, Reply list), all with UI §12.1 limits; no new template.
Task depth ≤ 3 ending in Drive mode: Favourites → call (2); card → Reply → sent (3).

## 12. Widgets and Drive menu (app-model §15 contract)

```jsonc
"contributes": {
  "slots": ["more:phone"],
  "widgets": [
    { "id": "favourites", "title": "Favourites", "surfaces": ["home", "drive"],
      "sizes": ["medium", "wide"], "view": "favourites_widget", "data": ["phone_contacts"],
      "moving": { "template": "short_list" },          // needs app-model §15.2 to admit short_list (Decision 12)
      "settings": { "type": "object", "properties": { "rows": { "type": "number", "minimum": 1, "maximum": 6 } } } },
    { "id": "recents", "title": "Recent calls", "surfaces": ["home"], "sizes": ["medium", "wide"],
      "view": "recents_widget", "data": ["call_history"], "moving": false },
    { "id": "call", "title": "Phone", "surfaces": ["drive"], "sizes": ["wide"],
      "view": "call_widget", "data": [], "moving": { "template": "call" } } ],
  "drive_menu": ["voice_dial", "favourites", "call_back_last", "mute_call"],
  "data_classes": ["phone_contacts", "call_history"]
}
```

- **Home:** Favourites (dialer favourites), Recent calls (Parked view; "Available when parked"
  in a Moving section).
- **Drive:** Favourites tile (`short_list` ≤ 6 while Moving) and the Phone pane (`call`
  template; idle shows phone name, battery and signal, and a voice-dial button).
- **Drive menu rows:** voice dial, favourites, call back last, mute (in call).
- `more:phone` is a new slot by platform change (app-model §15.4 pattern), pinnable to the rail.

## 13. Security

- **Pairing the Brain:** only from More → Phone → **Pair a phone**, Parked, by a signed-in
  user with the owner or driver role; the Brain is **discoverable for 2 minutes** and otherwise
  never. Secure Simple Pairing **numeric comparison**: the six digits show on the head unit and
  the phone; legacy PIN pairing is refused. Each pairing binds the phone to that Ostler user.
- **Bluetooth hardening:** BlueZ with only the HFP HF, PBAP client, MAP client and A2DP sink
  roles the owner enabled; no OBEX push server, no PAN, no SPP; unknown devices auto-rejected;
  pairings listed and removable in More → Phone; "Forget all phones" on user deletion and
  factory reset.
- **Companion bridge:** mutual auth to the paired Brain (device key, ADR-0029), local HTTPS
  (ADR-0021), refuses relay and mesh origins; bridged payloads are untrusted data, a message
  shaped like a command runs nothing.
- **Gate:** no Phone feature is a car action (ADR-0033); voice dial and canned replies are
  communication, not actions, so the gate does not apply, but they keep the driving-state rules.
- **Power:** a parked, asleep Brain is not woken for calls (ADR-0040); Phone works while the
  Brain is awake.

## 14. Phases

| Phase | Scope | Needs |
|---|---|---|
| **PH0 Bench** | Pi 5 + Trixie: HFP HF with PipeWire telephony, mSBC, AEC, mic, audio to amp/AUX; PBAP and MAP with a Pixel, a Samsung and an iPhone; head unit + Brain coexistence; messenger call matrix | hardware; no UI |
| **PH1 Calls** | pairing, `ostler-hfp`, `call` template via the shell call session, favourites (manual + Contact Picker), voice dial, call log, More → Phone, widgets | U2 lockouts and templates; Social amendment C1, C4; app-model §15 |
| **PH2 Contacts and recents** | PBAP phonebook with consent, combined contacts view, source badges, links, recents | accounts §14.6; registry classes |
| **PH3 Messages** | MAP SMS/iMessage alerts and replies; Android notification bridge (allow list, MessagingStyle, RemoteInput) | UI §14 approved (M1–M4); Social amendment C2, C5 |
| **PH4 Later** | iOS ANCS sender + app alerts; LC3-SWB; optional TDLib integration add-on (separate) | bench; owner decisions 8, 10 |

## 15. Tests (outline)

- No phone contact, number, call-history row or message body appears on MQTT, in a trip, a
  session log, a share bundle, an export of another user, an MCP reply or any network request
  to a non-local origin (fixture phonebook with canary names).
- PBAP data disappears from memory on disconnect and sign-out; a second user never sees the
  first user's phonebook.
- While Moving on a driver-facing display: no keypad, no contacts list, no recents list; the
  favourites `short_list` has ≤ 6 rows of ≤ 30 characters; no message text; the `call`
  template has ≤ 3 buttons and no photo.
- Idling: keypad locked (with or without Park evidence, unless Decision 9's alternative is chosen).
- Rate limits hold across Social and Phone sources together (three per 10 minutes total).
- Bridged reply fires the messenger's own `RemoteInput`; no reply is offered without one; no
  auto-reply is ever sent into a third-party app.
- Pairing refused while Moving, outside the 2-minute window, or with legacy PIN.
- A bridged message shaped like a command runs nothing; Phone declares no actions.
- `TelephonyBackend` contract tests run against fakes of the PipeWire, BlueZ and oFono APIs.
- Licence notices list BlueZ (GPL-2.0, separate process), PipeWire (MIT) and the WebRTC AEC
  (BSD-3) as used; no GPL code linked into the add-on (U: confirm per dependency).

## 16. Open questions

1. Does the Pi 5 onboard radio hold HFP + Wi-Fi hotspot under load? (PH0)
2. Which head units allow PBAP/MAP to the Brain while they own HFP? (PH0)
3. iPhone with two HFP kits connected: which takes the call? (PH0)
4. Voice dial on the Brain: which on-device recogniser fits a Pi 5 (no cloud by default)?
   (with ShellInput; no model names in docs)
5. Whether a car Brain may use the EU notification-forwarding interface on iOS.

## Changelog

- 2026-10-07: v0.1, draft (DMD round): one `ostler-app-phone` (mirroring + dialer + contacts),
  HFP HF on the Brain as the main call path, companion bridge, Android notification bridge,
  iOS limits, widgets, privacy, phases PH0–PH4; Social overlap in Social amendment §13.

## Decisions for the owner

1. **Repo** — widen `ostler-app-phone` into one Phone & Comms add-on (mirroring, dialer,
   contacts, recents, messages)? *Recommend:* yes. *Alternative:* a separate
   `ostler-app-dialer` beside a notifications-only `ostler-app-phone`.
2. **HFP stack** — PipeWire native HFP HF with its telephony D-Bus API on Raspberry Pi OS
   Trixie, behind a `TelephonyBackend` adapter ready for BlueZ's call control; BlueZ obexd for
   PBAP/MAP? *Recommend:* yes. *Alternative:* oFono as the HF stack (works on Bookworm, older
   and less maintained).
3. **Main call path and Brain requirement** — the Brain as hands-free for both Android and
   iPhone; the companion bridge only for picks, Android messages and status; Phone requires a
   Brain? *Recommend:* yes. *Alternative:* companion-first on Android (no car audio; needs
   intrusive permissions), Brain only for iPhone.
4. **Hands-free owner** — one per phone, chosen at pairing ("Ostler" or "my head unit")?
   *Recommend:* yes. *Alternative:* let both connect HFP and let the phone pick.
5. **Phone contacts storage** — in memory per connection, wiped on disconnect; only favourites
   persisted locally? *Recommend:* yes. *Alternative:* an opt-in encrypted on-Brain cache for
   faster start, still never synced.
6. **Android contacts access** — Contact Picker for favourites and PBAP for the full list, no
   `READ_CONTACTS` in the store build? *Recommend:* yes (Play's Android 17 policy, enforced
   27 January 2027). *Alternative:* `READ_CONTACTS` with a Play declaration for a full list
   without the Brain.
7. **Android notification bridge** — opt-in, per-app allow list, `MessagingStyle` only, reply
   through the messenger's own `RemoteInput`, bodies in Brain memory only, shared rate
   limits? *Recommend:* yes, in PH3. *Alternative:* no bridge; SMS via MAP only.
8. **iOS** — calls, contacts, recents and Messages via HFP/PBAP/MAP only in v1; ANCS sender +
   app alerts later (PH4)? *Recommend:* yes. *Alternative:* ANCS in PH3 alongside the Android
   bridge.
9. **Keypad** — Parked only, as asked, never Idling or Moving? *Recommend:* yes.
   *Alternative:* also Idling with Park evidence (the UI §12.1 text-entry rule).
10. **Native messenger integrations** — none in Phone; Matrix through Social; Telegram TDLib
    only as a later separate integration under Telegram's terms; never WhatsApp, Signal or
    Messenger libraries? *Recommend:* yes. *Alternative:* Telegram TDLib inside Phone in PH4.
11. **Who rings while Moving** — every phone call shows; an off-by-default "only favourites
    ring while driving" declines others to voicemail? *Recommend:* yes. *Alternative:* apply
    Social's favourites-only rule to phone calls by default.
12. **Favourites widget while Moving** — admit `short_list` to app-model §15.2's widget
    `moving` set (platform change)? *Recommend:* yes. *Alternative:* the widget is Parked only
    and favourites reach Moving only through the Drive menu row.
13. **Phases** — PH0 bench, PH1 calls, PH2 contacts, PH3 messages, PH4 later? *Recommend:*
    yes, all after U2 and Social S1. *Alternative:* PH3 messages before PH2 contacts.
14. **Pairing security** — Parked only, 2-minute discoverable window, numeric comparison, no
    legacy PIN, per-user binding? *Recommend:* yes. *Alternative:* discoverable whenever the
    ignition is on and More → Phone is open.
