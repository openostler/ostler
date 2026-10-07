---
title: "Message alerts on a driver screen — Android Auto, Android for Cars, CarPlay and AAOS behaviour, and whether a one-line preview is lawful (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/driver_distraction_rules.md, references/research/ui/head_unit_ui.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md]
summary: >
  Live research (2026-10-07) for the owner's ask to copy Android Auto's message alerts on the driver's head unit: sender and app, Play (read aloud), Reply (voice or canned), plus an owner opt-in one-line preview, default off. Android Auto shows a heads-up card with sender and app and reads messages aloud; its preview setting ("Show first line of conversations", lately reported as "Show first line of messages") is documented in older guides as showing one line only if the car is stopped when the message arrives, while a September 2026 guide reports it on by default, so name, default and motion rule are not settled from Google's own pages. Android for Cars apps get MessagingStyle with a no-UI voice reply and mark-as-read; AAOS's restrictions engine blocks text messages and voice transcripts while moving; CarPlay never shows message content and Siri announces it; NHTSA locks out reading messages; UK reg 109 does not list messages at all. Recommends sender and app plus Play and Reply while Moving, canned replies from a short list, and the opt-in preview only while Parked or Idling with Park evidence, never while Moving unless a UK legal opinion clears it.
---

# Message alerts on a driver screen (October 2026)

**Question (owner, 2026-10-07):** "Message alerts: copy Android Auto. On the driver's head unit
while Moving, the `alert_card` shows the sender and app, with Play (read aloud) and Reply
(voice, or a canned reply). Add an owner opt-in to show a one-line first-line preview. Default
stays off." What do Android Auto and the other platforms really do, and is a one-line preview
lawful or advised?

Builds on [driver-distraction rules](driver_distraction_rules.md) (reg 109, ESoP, NHTSA, the
template limits) and does not repeat it. Not legal advice. All sources checked 2026-10-07.

## 1. What the platforms do

| Platform | On screen while driving | Read aloud | Reply | Preview setting |
|---|---|---|---|---|
| **Android Auto** (projection) | heads-up card: sender, app icon; missed messages as tiles and in the notification centre [AA1] | tap the card, or ask Google's voice assistant, which can also summarise a burst of messages [AA1][AA4] | tap **Reply**, dictate; the assistant repeats the reply and asks before sending [AA1]; AI-suggested replies and actions (share ETA, call) on the card since Feb 2024 [AA5] | **"Show first line of conversations"**: shows one line "as long as you're stopped when they arrive" (2023 guide) [AA2]; a September 2026 guide calls it **"Show first line of messages"**, says it is **on by default** and recommends turning it off for passengers' privacy [AA3]. Also "Show conversations", "Show group conversations", message chime [AA2][AA6] |
| **Android for Cars apps** (notification messaging) | Android Auto draws the UI from the app's `MessagingStyle`; the app draws nothing [AC1] | the host reads each message aloud [AC1] | a reply `Action` with `SEMANTIC_ACTION_REPLY`, `setShowsUserInterface(false)` and one `RemoteInput`; Android Auto fills it from voice transcription [AC1] | none for the app; the host decides |
| **Android for Cars apps** (templated messaging) | `ConversationItem` rows with built-in Play, Mark as read and Reply [AC2] | built in | built in | — |
| **Car app quality** | short-form messaging only, peer-to-peer only (MF-4, MF-5); notify only when relevant ("a new message has arrived" is the good example, IN-1); no animation (SA-1); buttons respond ≤ 2 s (DR-1) [AC3] | — | the user can reply (MF-3) | — |
| **Android Automotive** (restrictions engine) | Moving default sets `NO_TEXT_MESSAGE` ("No Text Message (SMS, email, conversational, etc.)") and limits strings; `NO_VOICE_TRANSCRIPTION` ("No text transcription (live or leave behind) of voice can be shown") exists for OEMs [AO1][A1 in the rules note] | — | voice | — |
| **CarPlay** | Developer Guide: never show message content [C2 in the rules note]; Messages can be hidden from CarPlay ("Show in CarPlay") [CP3] | **Announce Messages** (Settings → Notifications → Announce Notifications → CarPlay): Siri plays a tone, says the sender and reads the message; a long message gets only "X sent you a message" [CP1] | Siri listens after the announcement, reads the reply back and asks to send; "Reply Without Confirmation" skips the read-back [CP2] | none on the car screen |
| **iPhone Driving Focus** | silences or limits notifications; turns on with CarPlay [CP4] | Siri can read replies | **Auto-Reply** to No One, Recents, Favourites or All Contacts with an editable message; a sender can break through by sending "urgent" [CP4] | — |

**What "copy Android Auto" means in practice.** The card (sender, app, Play, Reply), voice
reply with a spoken read-back before sending, and a preview that is off for privacy and, in the
best-documented version, appears only when the car is stopped when the message arrives. What
Android Auto does **not** document is a typed canned-reply list on the card; its quick
responses are AI suggestions and its "I'm driving" reply belongs to the phone (Driving mode,
Focus). Canned replies are therefore our own choice, closest to iPhone's Auto-Reply text and
Android Auto's one-tap suggestions.

**Unsettled facts.** Google's help pages fetched today ([AA1], [AC1]) describe reading and
replying but do not name the preview setting, its default or its motion rule; both names and
both defaults come from third-party guides [AA2][AA3][AA6]. Treat "stopped when it arrives"
as the documented behaviour and "on by default" as a recent report, both unverified against
Google.

## 2. Is a one-line preview lawful or advised?

| Rule | Sender and app | One-line preview while Moving | Preview while stopped |
|---|---|---|---|
| **UK reg 109** (binding on the driver) | not in classes (a)–(d); a sender name is non-driving information. Low risk in practice (every projection system shows it), but untested | **not in (a)–(d)**: the driver commits the offence whoever enabled it | still "driving" while stopped in traffic (rules note §3.3, §4.3); lawful only when **parked** |
| **NHTSA per se lockouts** (voluntary) | allowed (a notification, not reading) | **locked out**: "reading text from … messages" | NHTSA's "driving" includes idling unless in Park or handbrake + neutral + < 5 mph |
| **ESoP I/III** (recommendation) | fine as a short, driver-paced alert | non-driving visual text; should be off or unseen | fine once stopped (with a few seconds' delay) |
| **CarPlay** | allowed | **forbidden** (never show message content) | forbidden on the car screen |
| **AAOS default** | allowed | **blocked** (`NO_TEXT_MESSAGE`) | allowed when Parked; Idling default blocks only video |
| **Android Auto** | shown | shown only if stopped on arrival [AA2] (or, per [AA3], possibly whenever on) | shown, opt-in |

**Reading.** A preview shown to the driver while Moving fails every rule we track except one
reading of Android Auto, and under reg 109 the owner's opt-in does not help the driver. A
preview shown only when the car is **parked** (or Idling with Park evidence, the stricter test
the UI spec already uses for text entry) is lawful and matches Android Auto's documented
behaviour. Sender and app while Moving is what every platform does; it remains a reg 109 grey
area that the U2 legal check should cover, with "New message · Social" as the fallback.

## 3. Copy / Avoid / Decide for Ostler

### Copy
- **Sender + app + Play + Reply** on the card (Android Auto, CarPlay); the app icon from the
  add-on's manifest → UI spec §12.1 `alert_card`.
- **Play = read aloud by the shell's voice**, never shown as text; a long message announced as
  "Sam sent a long message" first, as Siri does → Social §8.
- **Voice reply with a spoken read-back and Send / Cancel**, no transcript on screen (Android
  Auto, Siri; AAOS `NO_VOICE_TRANSCRIPTION`) → UI spec §12.1, Social §8.
- **Preview off by default, opt-in, shown only if stopped when the message arrives** (Android
  Auto [AA2]), tightened to Parked or Idling with Park evidence → UI spec §12.1.
- **Driving Focus–style auto-reply** with an editable text and a per-audience scope (already
  Social §4) → Social §8.
- **Separate switch for group conversations** (Android Auto) → Social §8 (ride channel on,
  other groups as a count).

### Avoid
- **Any message text on a driver-facing display while Moving**, opt-in or not (reg 109, NHTSA,
  CarPlay, AAOS) → UI spec §12.1.
- **Showing a dictated reply as text** while Moving (AAOS transcription restriction).
- **AI summaries or suggested replies** generated from message bodies on the Brain: needs a
  model and reads content; not in v1 (and no model names in docs).
- **Images, avatars, stickers, link previews** in any alert (NHTSA images lockout) → UI spec
  §12.1.
- **One card per message** in a busy group (Android Auto groups them; quality MF-2) → rate
  limit and coalesce.

### Decide (recommendations for the owner)
1. **Card while Moving.** Recommend sender name and app with **Play** and **Reply**, replacing
   the approved "Message from *name*" with **Play / Later**. Alternative: keep the approved
   rule. Maps to UI spec §12.1, Social §8 and Decision 5.
2. **Canned replies.** Recommend a fixed-length list of up to six owner-editable replies (edited
   Parked only), sent with one tap from a `short_list`. Alternative: voice and PTT only, no list
   (the approved Social §8).
3. **Preview.** Recommend an owner opt-in, default off, one line ≤ 30 characters, shown only
   when the message arrives while Parked or Idling with Park evidence, and replaced by "New
   message" once Moving. Alternative: the owner's literal ask, a preview while Moving, released
   only if the U2 legal opinion explicitly clears it.
4. **Legal check.** Recommend adding sender-and-app while Moving and the stopped-only preview
   to the U2 reg 109 opinion. Alternative: ship sender-and-app on platform precedent alone.

## Sources (all checked 2026-10-07)

- [AA1] Android Auto Help, "Send and receive messages": https://support.google.com/androidauto/answer/6348317?hl=en-GB
- [AA2] MakeUseOf, "7 Important Android Auto Settings You Should Tweak" (updated 16 July 2023): https://www.makeuseof.com/tag/android-auto-tweaks/
- [AA3] Pocket-lint, "5 settings every new Android Auto user needs to change" (25 September 2026): https://www.pocket-lint.com/settings-every-new-android-auto-user-needs-to-change-asap/
- [AA4] Google blog, Android Auto voice assistant tips (20 November 2025): https://blog.google/products/android/ (the post titled for Android Auto voice-assistant tips)
- [AA5] TechCrunch, "Android Auto is getting new AI-powered features, including suggested replies and actions" (17 January 2024): https://techcrunch.com/2024/01/17/android-auto-is-getting-new-ai-powered-features-including-suggested-replies-and-actions/
- [AA6] TWiT, "Android Auto not reading texts or taking voice commands" (13 May 2026): https://twit.tv/posts/tech/android-auto-not-reading-texts-or-taking-voice-commands-heres-what-do
- [AC1] Android Developers, "Extend messaging notifications to Android Auto" (updated 2026-09-23): https://developer.android.com/training/cars/communication/notification-messaging
- [AC2] Android Developers, "Templated messaging experiences" (updated 2026-09-08): https://developer.android.com/training/cars/communication/templated-messaging
- [AC3] Car app quality guidelines (September 2026): https://developer.android.com/docs/quality-guidelines/car-app-quality
- [AO1] `CarUxRestrictions` reference: https://developer.android.com/reference/android/car/drivingstate/CarUxRestrictions
- [CP1] Apple Support, "Use CarPlay with your iPhone" (14 March 2025): https://support.apple.com/en-gb/108415
- [CP2] Apple Support, "Announce Notifications with Siri" (Reply Without Confirmation): https://support.apple.com/102536
- [CP3] Guiding Tech, "How to remove message notifications from Apple CarPlay" (27 August 2024): https://www.guidingtech.com/how-to-remove-message-notifications-from-apple-carplay
- [CP4] Apple Support, "Use Driving Focus on your iPhone" (13 April 2026): https://support.apple.com/en-gb/108384
- Rules, template limits, reg 109, NHTSA and ESoP sources: [driver-distraction rules](driver_distraction_rules.md#sources-all-checked-2026-10-07).
