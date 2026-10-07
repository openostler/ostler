---
title: "Phone and comms in the car — dialer, contacts, Bluetooth hands-free on the Brain, companion-app limits on Android and iOS, and third-party messengers (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/driver_distraction_rules.md, references/research/message_alerts_android_auto.md, references/research/calls_video_camera_sharing.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-social-addon-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0032-one-node-optional-brain.md]
summary: >
  Live research (2026-10-07) for the owner's ask to widen the proposed `ostler-app-phone` into a dialer with contacts, calls and message bridging. Two paths. (a) The companion phone app: Android lets a non-default-dialer app place calls and read contacts, but answering or ending other apps' calls needs the default-dialer role (full InCallService, keypad, emergency falls back to the system dialer) or a companion-device "watch"/"glasses" association we do not qualify for; call logs are Play-restricted to default handlers; READ_CONTACTS needs a Play declaration for apps targeting Android 17 (enforced 27 January 2027) unless the Contact Picker suffices. iOS apps cannot place silently, answer, end or list other apps' calls or read the call log. (b) The Brain as a Bluetooth hands-free unit: PipeWire's native backend enables the HFP HF role by default and, from PipeWire 1.4 (Debian/Raspberry Pi OS Trixie ships 1.4.2), exposes an oFono-like telephony D-Bus API (dial, answer, hang up, hold, caller line and name); Collabora is moving HFP call control into BlueZ during 2026. BlueZ obexd gives PBAP (phonebook, call history) and MAP (iPhone MAP 1.4 supports notifications, replies and composing). The Pi 5's onboard radio carries HFP without extra HCI commands. A phone normally routes call audio to one hands-free device at a time, so the head unit and the Brain should not both own HFP. VoIP calls reach HFP only if the app registers with Telecom or CallKit, and car kits often show "unknown" for them. Android messages can be bridged with NotificationListenerService and RemoteInput (OTP content redacted since Android 15; sideloaded builds hit restricted settings); iOS offers ANCS (title, message, positive/negative actions, no reply) and, in the EU only, iOS 26.x notification forwarding to one accessory. WhatsApp and Signal forbid or do not tolerate unofficial clients; Telegram allows its API under strict terms. Recommends HFP on the Brain as the main call path on both platforms, the Android bridge for messages, and no unofficial messenger libraries.
---

# Phone and comms in the car (October 2026)

**Question (owner, 2026-10-07):** widen the proposed `ostler-app-phone` (phone mirroring) or
propose a separate `ostler-app-dialer`, covering a dialer (keypad, recents, favourites),
one contacts view, two connection paths (the companion phone app; the Brain as a Bluetooth
hands-free kit), WhatsApp/Signal/Telegram/Messenger calls and messages, iOS limits and
widgets. What does each platform really allow?

Builds on [driver-distraction rules](driver_distraction_rules.md) and
[message alerts](message_alerts_android_auto.md) and does not repeat them. Not legal advice.
All sources checked 2026-10-07; **(U)** marks a point not verified today (bench or later check).

## 1. The two paths at a glance

| Need | (a) Companion phone app, Android | (a) Companion phone app, iOS | (b) Brain as hands-free (HFP HF) + PBAP/MAP |
|---|---|---|---|
| Place a call | yes: `ACTION_CALL` / `TelecomManager.placeCall` with `CALL_PHONE` (U: not re-read today) | only via `tel:` URL, which iOS confirms on the phone (U) | yes: `Dial` over HFP (`ATD`) [P3] |
| Answer, reject, end any call | only as **default dialer** (full `InCallService`) [A3] or a CDM watch/glasses companion [A5]; `acceptRingingCall`/`endCall` deprecated in API 29 [A4] | **no**: CallKit is for an app's own VoIP calls [I3] | yes: `Answer`, `Hangup`, hold, three-way [P3] |
| Caller number and name | default dialer only | no | number by `+CLIP`; name from the phone's phonebook via PBAP, or the `+CLIP` alpha field when the phone sends it (U per phone) [P3][P10] |
| Call audio in the car | stays on the phone (or on whatever it routes to) | same | **in the car**: SCO to the Brain, then to the amp or head unit [P1][P6] |
| Contacts | Contact Picker (no permission) or `READ_CONTACTS` with a Play declaration from Android 17 [A8][A9] | Contacts framework with permission (U: limited-access mode) | **PBAP 1.2** phonebook pull; iPhone supports it [I1][P10] |
| Recent calls | Call Log only for the default Phone or Assistant handler [A7] | no API (U) | PBAP call-history folders (U per phone) |
| SMS | default SMS app only (Play) [A7] | no | **MAP**; iPhone MAP 1.4: notify, reply, compose, browse, mark read [I1][I4] |
| Third-party messages | **NotificationListenerService** + `RemoteInput` reply [A6][A10] | ANCS (read-only + two actions) [I2]; EU-only forwarding (iOS 26.3+) [I5][I6] | no (HFP/MAP carry calls and SMS/iMessage only) |
| VoIP calls (WhatsApp, Signal…) | visible only if the app uses Telecom | visible only if the app uses CallKit | ring through **if** the app uses Telecom/CallKit; name often missing (§5) |

**Reading.** For calls, path (b) is the only one that works the same on Android and iOS, gets
call audio into the car and needs no default-dialer role. Path (a) is still needed for an
Android notification bridge, for picking favourites without a broad contacts permission and
for status when the Brain is absent.

## 2. Path (b): the Brain as a hands-free unit

### 2.1 Linux stack (Raspberry Pi OS Bookworm/Trixie)
- **PipeWire + WirePlumber, native backend (recommended).** WirePlumber's default
  `bluez5.roles` is `[ a2dp_sink a2dp_source bap_sink bap_source hfp_hf hfp_ag ]`: the HF
  role is on by default; `bluez5.hfphsp-backend` defaults to `native` (others: `ofono`,
  `hsphfpd`, `any`, `none`) [P1][P2]. **Telephony:** PipeWire 1.4 (≥ 1.3.82) exposes an
  "oFono-like" D-Bus API, `org.pipewire.Telephony` at `/org/pipewire/Telephony`, when a phone
  is paired: `Dial`, `Answer`, `Hangup`, `HoldAndAnswer`, `ReleaseAndAnswer`, `SwapCalls`,
  `SendTones`, with line identification and name on call objects; "there is no user interface
  for it (yet)" [P3].
- **Direction of travel.** Collabora (24 Nov 2025) is "moving parts of the HFP implementation
  from PipeWire into BlueZ, which will eventually deprecate the 'telephony' support in
  PipeWire", building one call-control API for HFP and LE Audio's Call Control Profile, with
  SIG qualification targeted "within 2026" [P4]. → keep our call control behind an adapter.
- **Versions.** Debian 13 Trixie (base of Raspberry Pi OS Trixie, autumn 2025) ships PipeWire
  1.4.2 and WirePlumber 0.5.8 [P5], so the telephony API is in the distribution. Bookworm's
  PipeWire predates 1.3.82 (U: 0.3.65), so Bookworm needs backports or oFono.
- **oFono** remains a fallback: PipeWire's `ofono` backend hands HFP to oFono over D-Bus [P1];
  oFono's Handsfree API exposes `EchoCancelingNoiseReduction`, which sends `AT+NREC=0` [P9].
- **Codecs.** CVSD (narrowband) always; **mSBC** wideband when kernel and controller support
  it, auto-detected, forced with `bluez5.enable-msbc` [P2]. **LC3-SWB** (HFP 1.9, super-
  wideband) exists in the spec; Linux support was reported experimental and off by default in
  early 2025 (U) [P11]. Plan CVSD/mSBC; treat LC3-SWB as a bench bonus.
- **Pi 5 radio.** On a Pi 5, SCO audio works over the transport "without issuing HCI
  commands" (Pi Zero needs vendor HCI commands) [P6]; a Pi head-unit project reports the Pi 5's
  onboard module "works with both HFP and A2DP" [P7]. Wi-Fi/Bluetooth coexistence on the
  combo chip under load (Brain hotspot + HFP) is untested (U) → a USB Bluetooth dongle is the
  bench fallback; not every dongle carries HFP audio [P8b].

### 2.2 Phonebook and messages (BlueZ obexd)
`org.bluez.obex.Client1.CreateSession(target="pbap"|"map")`, then `PhonebookAccess1`
(select phonebook, list, pull vCards) and `MessageAccess1` (folders, list, get, push,
notifications) [P10]. iPhone supports **PBAP 1.2** and **MAP 1.4** ("incoming notifications,
replies, message composition, inbox browsing, read status") [I1]; a car kit receives new
messages only when the per-device **"Show Notifications"** switch is on (Settings → Bluetooth →
ⓘ) [I4]. MAP on iPhone carries Messages (SMS/iMessage), not third-party apps (U).

### 2.3 Audio, echo and noise
- HF devices are expected to do their own echo cancelling; the HF may tell the phone to switch
  its own off with `AT+NREC=0` for the session [P9] (avoids double processing).
- PipeWire's `module-echo-cancel` (default `libspa-aec-webrtc`) creates echo-cancel source and
  sink nodes [P8]. Route: phone SCO → AEC sink → Brain audio out (I²S DAC or USB) → amp or
  head-unit AUX; cabin mic (USB or I²S array, near the driver) → AEC source → SCO.
- Duck media and navigation voice during a call (WirePlumber policy) and mute the Social PTT
  room (Social amendment).

### 2.4 One phone, two hands-free devices
- Phones connect to several audio devices but play call audio to **one** at a time; Android's
  developer option "Maximum connected Bluetooth audio devices" goes up to 5 [A13]. iPhone
  behaviour with two HFP kits (U, bench).
- AOSP's own IVI notes that the default Dialer does not handle multiple simultaneous HFP
  connections without customisation [A12] (that is the car side, not the phone).
- **Consequence:** an aftermarket Android head unit that is itself a hands-free kit and the
  Brain would compete for the call. Pick one hands-free owner per phone at setup. Non-audio
  profiles (PBAP, MAP) can still go to the Brain when the head unit owns HFP (U per head unit).

## 3. Path (a): the companion phone app

### 3.1 Android
- **Default dialer role** (`RoleManager.ROLE_DIALER`): the app must handle `ACTION_DIAL` (a
  keypad), fully implement `InCallService` with incoming and ongoing call UI, never return a
  null binding (Telecom falls back to the preloaded dialer); **emergency calls always use the
  preloaded dialer** [A3]. Becoming the phone's dialer to power a car screen is heavy and
  intrusive; not recommended.
- **Companion device profiles** (`watch`, `glasses`) grant phone, SMS, contacts and "managing
  ongoing calls", for devices with a screen showing notifications or caller info [A5]. Ostler
  is neither; claiming a watch profile would misrepresent the device. Not used.
- **Self-managed VoIP:** Telecom documents Bluetooth integration for self-managed
  `ConnectionService` calls ("visible on and controllable via bluetooth devices (e.g. car head
  units and headsets)") [A1]; Core-Telecom lists Bluetooth headsets and Android Auto as remote
  surfaces that answer and end calls through the app's callbacks [A2]. Whether a given
  messenger uses it is per app (§5).
- **Contacts:** Play's Contacts Permissions policy (announced 15 April 2026): apps targeting
  Android 17 may request `READ_CONTACTS` only if the Contact Picker is insufficient, with a
  Play Console declaration [A8]; pre-review from 27 October 2026, enforcement **27 January
  2027**; the picker returns the chosen contact (or one property) with no persistent access
  [A9].
- **Call log and SMS** permission groups are for the default Phone, SMS or Assistant handler
  only [A7].
- **Notification bridge:** `NotificationListenerService` sees posted notifications; a
  messenger's `MessagingStyle` reply action carries a `RemoteInput` precisely "to let other
  apps provide reply text" (that is how Android Auto replies) [A6]. Since Android 15, OTP
  content is redacted for untrusted listeners [A10]; since Android 13, a **sideloaded** app
  cannot enable notification access until the user taps "Allow restricted settings" [A11].
  Play has no notification-listener declaration form, but the general rule applies: request
  only what a promoted core feature needs, with consent [A7].

### 3.2 iOS
- **CallKit** gives an app's own VoIP calls the system UI and coordinates with other call apps;
  `CXCallObserver` sees call state [I3]. It cannot answer, end or place another app's or the
  carrier's calls, and there is no call-log API (U).
- **ANCS** (BLE, authorised and bonded): attributes AppIdentifier, Title, Subtitle, Message,
  MessageSize, Date, Positive/NegativeActionLabel; actions are chosen by the phone (for example
  answer/decline an incoming call); **no reply text** [I2]. Each accessory needs the user's
  "Share System Notifications" switch (iOS 13+) [I7].
- **EU only:** iOS 26.3 lets third-party accessories receive and react to notifications, **one
  accessory at a time**, turning off Apple Watch notifications [I5]; iOS 26.5 widens it to
  replies and Live Activities, data use for ads, profiling or model training forbidden [I6].
  Wearable-oriented; whether a car Brain may use it is (U).

## 4. Messengers: what is allowed

| Service | Official integration route | Unofficial clients |
|---|---|---|
| **WhatsApp** | none for personal accounts (Business API is for businesses); its own Android Auto/CarPlay support [M5] | terms forbid accessing the service "through automated or other means" in unauthorised ways [M1]; users of third-party apps have been banned [M2] |
| **Signal** | none | the service does not accept third-party clients on its servers (LibreSignal precedent) [M4] |
| **Messenger** | none for personal chats | Meta terms as WhatsApp (U) |
| **Telegram** | **Bot API** (bots only) and **TDLib** client with your own `api_id`, under the API Terms: no actions "without the user's knowledge and consent", no tampering with read status or typing, no AI training on data; breach → API access cut in 10 days and store removal requests [M3] | allowed only as a terms-compliant client |
| **Matrix** | open protocol and SDKs (Social §9 already plans it as later interop) | n/a |

## 5. Calls from messengers over HFP

- **Android:** a VoIP call reaches the car's HFP only if the messenger registers it with
  Telecom (self-managed or managed) [A1][A2]. User reports for WhatsApp through car Bluetooth:
  "caller unknown" on the car display and steering-wheel answer not working, varying by phone,
  app version and car [M6] (U: forum reports, not tested).
- **iOS:** CallKit calls are presented to Bluetooth hands-free devices and CarPlay like phone
  calls (Apple's CallKit purpose; vendor docs) [I3][M7]; the name shown is the app's handle (U).
- **What HFP exposes for any call:** ringing (`RING`, call-setup indicators), number (`+CLIP`),
  answer (`ATA`), reject/end (`AT+CHUP`), mic mute is local to the HF; name only if the phone
  sends one or PBAP resolves the number [P3]. For VoIP the number is often absent, so expect
  "Unknown" or the app name.
- **Bench before promising:** WhatsApp, Signal, Telegram, Messenger on a current Pixel, a
  Samsung and an iPhone: rings on the Brain? name? answer and reject from the Brain? audio route?

## 6. Copy / Avoid / Decide for Ostler

### Copy
- **Hands-free on the Brain via HFP** (every car kit does it): one path for both OSes, real call
  audio in the car → Phone spec §3.
- **PBAP for the phonebook, MAP for SMS/iMessage**, read with consent and kept local → Phone §5.
- **Android Auto's message model:** `MessagingStyle` sender and conversation, reply through the
  messenger's own `RemoteInput`, mark-as-read action [A6] → Phone §7.
- **Contact Picker** for favourites instead of a broad contacts permission [A9] → Phone §5.

### Avoid
- **Becoming the default dialer** or posing as a watch companion to control calls [A3][A5].
- **Unofficial WhatsApp, Signal or Messenger libraries** (bans, terms) [M1][M2][M4].
- **Both the head unit and the Brain owning HFP** for one phone (§2.4).
- **Showing notification text on driver screens** (rules and message-alerts notes) and keeping
  bridged message bodies anywhere but memory.
- **Relying on LC3-SWB or on VoIP caller names** before the bench.

### Decide (recommendations; mapped to the Phone spec's Decisions)
1. One `ostler-app-phone` covering mirroring, dialer and contacts. Alternative: separate
   `ostler-app-dialer`.
2. PipeWire native HFP + its telephony API behind an adapter, Trixie baseline; move to BlueZ's
   call control when it lands. Alternative: oFono.
3. Android notification bridge, opt-in per app. Alternative: SMS via MAP only.
4. iOS: calls, contacts and Messages via HFP/PBAP/MAP only; ANCS later. Alternative: ANCS now.
5. Telegram natively only through TDLib under its terms, later; Matrix through Social.
   Alternative: Telegram only via the Android bridge, never native.

## Sources (all checked 2026-10-07)

- [P1] WirePlumber 0.5.17, Bluetooth configuration: https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html
- [P2] pipewire-props(7), PipeWire 1.6.9 (Debian testing): https://manpages.debian.org/testing/pipewire-bin/pipewire-props.7.en.html
- [P3] G. Kiagiadakis, "Introducing Bluetooth telephony support in PipeWire" (20 Feb 2025): https://gkiagia.gr/2025-02-20-pipewire-telephony/
- [P4] Collabora, "Implementing Bluetooth LE Audio & Auracast on Linux systems" (24 Nov 2025): https://www.collabora.com/news-and-blog/blog/2025/11/24/implementing-bluetooth-le-audio-and-auracast-on-linux-systems/
- [P5] Collabora, "Debian Trixie, the 2025 flavor release": https://www.collabora.com/news-and-blog/news-and-events/debian-trixie-the-2025-flavor-release.html
- [P6] "Raspberry Bluetooth audio routing" (10 Apr 2026): https://www.sefod.eu/posts/raspberry_bluetooth_audio_routing/
- [P7] Hudiy community, "Onboard Bluetooth" (11 Oct 2025): https://hudiy.eu/community/viewtopic.php?p=527
- [P8] PipeWire, echo-cancel module: https://docs.pipewire.org/page_module_echo_cancel.html
- [P8b] ArchWiki, Bluetooth headset (adapter caveats; search summary, page blocked today): https://wiki.archlinux.org/title/Bluetooth_headset
- [P9] oFono Handsfree API, echo cancelling and noise reduction (`AT+NREC`): https://gitea.sysmocom.de/sysmocom/ofono/commits/branch/master/doc/handsfree-api.txt
- [P10] BlueZ OBEX D-Bus API, PhonebookAccess and MessageAccess: https://manpages.opensuse.org/Tumbleweed/bluez/org.bluez.obex.PhonebookAccess.5.en.html ; https://manpages.opensuse.org/Leap-16.0/bluez/org.bluez.obex.MessageAccess.5.en.html
- [P11] LC3 (codec), HFP 1.9 LC3-SWB: https://en.wikipedia.org/wiki/LC3_(codec)
- [A1] Android, `ConnectionService` reference (self-managed, Bluetooth integration): https://developer.android.com/reference/android/telecom/ConnectionService
- [A2] Android, Core-Telecom (updated 2026-05-29): https://developer.android.com/develop/connectivity/telecom/voip-app/telecom
- [A3] Android, `InCallService` reference (default dialer requirements): https://developer.android.com/reference/android/telecom/InCallService
- [A4] Android API diff 29, `TelecomManager` (deprecations): https://developer.android.com/sdk/api_diff/29/changes/android.telecom.TelecomManager
- [A5] AOSP, Companion device profiles (updated 2026-07-13): https://source.android.com/docs/core/connect/companion-device-profile
- [A6] Android for Cars, "Extend messaging notifications to Android Auto": https://developer.android.com/training/cars/communication/notification-messaging
- [A7] Google Play, "Permissions and APIs that Access Sensitive Information": https://support.google.com/googleplay/android-developer/answer/16558241?hl=en
- [A8] Google Play, April 2026 policy preview (Contacts): https://support.google.com/googleplay/android-developer/answer/16909972
- [A9] Capawesome, "Capacitor and the Google Play contacts policy" (25 Sep 2026): https://capawesome.io/blog/capacitor-google-play-contacts-policy-2027/
- [A10] Android Authority, Android 15 sensitive notifications: https://www.androidauthority.com/android-15-sensitive-notifications-3416414
- [A11] Esper, Android 13 restricted settings for sideloaded apps: https://www.esper.io/blog/android-13-sideloading-restriction-harder-malware-abuse-accessibility-apis
- [A12] AOSP, Automotive IVI Bluetooth connectivity: https://source.android.com/docs/automotive/ivi_connectivity
- [A13] Android Police, multiple Bluetooth audio devices (7 Mar 2018): https://www.androidpolice.com/2018/03/07/android-p-feature-spotlight-5-bluetooth-audio-devices-can-connected-simultaneously-via-new-developer-option/
- [I1] Apple, Bluetooth profiles that iOS and iPadOS support (31 Oct 2023): https://support.apple.com/HT204387
- [I2] Apple, ANCS specification: https://developer.apple.com/library/content/documentation/CoreBluetooth/Reference/AppleNotificationCenterServiceSpecification/Specification/Specification.html
- [I3] Apple, CallKit: https://developer.apple.com/documentation/callkit
- [I4] Audi technical service bulletin on iPhone MAP and "Show Notifications" (NHTSA archive, 2019): https://static.nhtsa.gov/odi/tsbs/2019/MC-10165969-9999.pdf
- [I5] MacRumors, iOS 26.3 DMA pairing and notification forwarding (22 Dec 2025): https://macrumors.com/2025/12/22/ios-26-3-dma-airpods-pairing
- [I6] heise, third-party wearables in the EU, iOS 26.5 (1 Apr 2026): https://heise.de/-11243346
- [I7] Fitbit community, iOS 13 "Share System Notifications": https://community.fitbit.com/t5/iOS-App/Stopped-seeing-notifications-after-updating-to-iOS-13/m-p/3777821/highlight/true
- [M1] WhatsApp Terms of Service: https://www.whatsapp.com/legal/terms-of-service
- [M2] TechCrunch, WhatsApp bans users of third-party apps: https://techcrunch.com/?p=1108388
- [M3] Telegram API Terms of Service: https://core.telegram.org/api/terms
- [M4] "Signal Messenger: Embrace, extend, extinguish" (quotes Signal on LibreSignal): https://iczelia.net/posts/signal-embrace-extinguish/
- [M5] "How to add WhatsApp to Android Auto" (Aug 2026): https://blog.aahacks.com/whatsapp-android-auto/
- [M6] User reports, WhatsApp calls over car Bluetooth: https://vwcaliforniaclub.com/threads/answering-a-whattsapp-call.48244/ ; https://www.mavericktruckclub.com/forum/threads/receiving-a-whatsapp-phone-call.27250/
- [M7] RST Software, CallKit and Bluetooth/CarPlay: https://www.rst.software/blog/callkit-ios
