---
title: "Social add-on — messaging, push-to-talk, calls and camera sharing over the internet and meshes — design"
area: specs
status: stable
version: 0.4
updated: 2026-10-07
depends_on: [references/research/phone_comms.md, specs/2026-10-07-phone-comms-addon-design.md, references/research/social_group_drive_apps.md, references/research/mesh_transports.md, references/research/calls_video_camera_sharing.md, references/research/accounts_social_login.md, references/research/driver_distraction_rules.md, references/research/message_alerts_android_auto.md, references/research/mesh_networking.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-module-bus-messages-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all"). The Social add-on (`ostler-app-social`, its own repo) gives people in cars and on bikes 1:1, group and ride-channel messaging, push-to-talk first, then voice and video calls, and later live camera sharing. It reads contacts, groups, rides and the data-class permission registry from core accounts and sharing and stores no permissions of its own. One Social link router sends each message class over the best allowed link (internet, Wi-Fi mesh, HaLow, LoRa; alerts on every link) with one envelope and de-duplication; live media run as WebRTC through a self-hosted LiveKit room (relay or a brain) with our own token issuer, never through MQTT. Driver rules: audio only on head units while Moving through the `call` template, video only Parked or on passenger devices, no message content on a driver screen. Cameras get their own time-boxed, live-only, audited `camera` grant. WhatsApp and Facebook only through share links and the share sheet; Matrix only as later interop. Phases S1–S4 and owner decisions. v0.3 adds a proposed amendment (2026-10-07, DMD round), not yet approved: message alerts on driver screens show sender and app with Play and Reply (voice or up to five canned replies), an opt-in first-line preview only for messages that arrive while parked, and rate limits, replacing the approved "Message from name" with Play / Later. v0.4 adds a second proposed amendment (§13, DMD round), not yet approved: the comms overlap with the draft Phone & Comms add-on — one shell-owned call session and comms chip (phone calls pause PTT, call waiting instead of stacked cards), one alert pipeline whose message rate limits count across Social, SMS and bridged messengers, one favourites list, one local call log, and auto-reply only for Ostler messages.
---

# Social add-on — design

**Status: approved by the owner on 2026-10-07 ("approve all"), v0.2; v0.3 and v0.4 add proposed amendments (§12, §13) awaiting the owner.** Nothing here is built before the app model's UA phase
and the accounts phases it depends on (§11). It is a design for the optional add-on
`ostler-app-social` (ADR-0034, ADR-0042 "Ecosystem: small core, add-ons are the product",
accepted). The research is linked, not repeated:
[social and group-ride apps](../references/research/social_group_drive_apps.md),
[mesh transports](../references/research/mesh_transports.md),
[calls, video and cameras](../references/research/calls_video_camera_sharing.md),
[accounts and social login](../references/research/accounts_social_login.md),
[driver-distraction rules](../references/research/driver_distraction_rules.md),
[mesh networking](../references/research/mesh_networking.md).

## 1. Purpose and non-goals

**Purpose.** Let a few people who drive or ride together talk to each other: text, push-to-talk
(PTT) on the move, calls when stopped or as passengers, and later a look through each other's
cameras, over whatever link exists: the internet, a convoy Wi-Fi mesh, a HaLow camp link or LoRa.
It must be useful with **two people and no server** (research: social apps that need a big
network die).

**Non-goals.**
- No feed, likes, followers, public directory, ads, tracking or analytics (ADR-0029 §9).
- No permissions of its own: who sees what is core accounts and sharing (§3).
- No map: other people's vehicles on a map are **Vehicles & Map** (`ostler-app-vehicles`);
  Social only links to it.
- No vehicle actions. Social declares none in its manifest; no message, call or camera request
  ever commands the car (ADR-0033 §6, ADR-0038 §2).
- No scraping of, or login to, WhatsApp or Facebook; no contact upload (§9).
- No live voice over LoRa, no continuous calls or video over UK/EU HaLow (§6).
- Not a replacement for helmet intercoms: audio routes to them over the phone's Bluetooth.

## 2. Where it sits in the shell

Social is a first-party optional app (app-model §3 row "Social"), bundled into the phone build
(app-model §7.1: first-party, no runtime code). Its contributions:

| Slot | What | Driving rule |
|---|---|---|
| **More → Social** page (a new `more:social` slot, added by platform change; app-model §4.2, §14.7) | Tabs: **Chats** (1:1, groups, ride channels), **Calls** (history, local only), **Rides** (live ride panel: members, talk, link badges), **Cameras** (S4) | Parked or passenger only; while Moving the page is replaced by the templates below |
| **Home card** | active ride (name, members heard, time left), unread count, ongoing call | Moving: hidden; the strip chip carries it |
| **Strip chip** (one, shown only while a ride or call is active) | "Ride: Peak · PTT" or "Call · 04:12"; tap opens the call/PTT sheet | Always allowed; the sheet is the `call` template while Moving |
| **Alert cards** | incoming call, new message, peer alert, "being viewed" | `alert_card` / `call` while Moving (§8) |
| `sheet:link` rows | the router's ranked links ("Internet · Wi-Fi mesh 2 hops · LoRa") | read-only |

Social is **not** a sixth destination (UI spec §3.4 caps five). Whether the strip chip is new or
folds into the visibility chip core defines is Decision 3.

## 3. Contacts, friends, groups and rides

Social **consumes** the model in the
[accounts and sharing spec](2026-10-06-accounts-sharing-design.md), including its
§14 "Amendment (2026-10-07), approved" (contacts and groups as first-class objects, the one
data-class registry with audiences me / person / group / household / public-later, ghost on by
default, invite links, QR and short codes). It does not redefine any of them. What Social adds:

- **A channel per conversation:** a 1:1 channel per contact pair, a channel per group, and a
  **ride channel** per ride (accounts spec §6) that opens at ride start and closes at ride end.
  Members auto-join the ride channel and its PTT room (the Cardo/Sena "no call setup" lesson).
- **Who may reach me:** a per-user setting over the registry's audiences (default: contacts may
  message; contacts and ride members may call). Strangers can't reach anyone; there is no
  directory.
- **Ghost costs nothing here.** Ghost mode hides `presence` and `location` (and stops outbound
  `position` and `telemetry` on every link, §6), but messaging, PTT and calls keep working
  (research: Waze's invisible mode punished privacy). Presence ("in a ride", "online") is the
  registry's `presence` class, so ghost hides it.
- **Safety contacts** (start, end and alert notices for a ride) use core's notify-via; Social
  only sends the ride's events. Only my own SOS or crash alert sends a precise position to my
  safety contacts; nobody can raise another's precision.

## 4. Messaging

- **Kinds:** text, voice notes, photos (S2+), locations (a pin, at the precision the share
  allows), and **canned "I'm driving" auto-reply** while Moving.
- **Delivery ticks** (sent, delivered, read where the peer allows) per link, as Meshtastic does.
- **Storage:** on each participant's device only (brain, or the phone on Ostler Diagnostics
  alone); the relay holds sealed envelopes until delivery, at most 7 days. Retention default
  90 days, ride channels 30 days after ride end; per-chat delete.
- **Security:** every envelope is signed by the sender's device key (ADR-0029); bodies are
  end-to-end encrypted on IP links (Decision 6 picks the scheme). On LoRa the bridge's private
  channel key applies (ADR-0038 §5); the UI marks LoRa messages "radio-encrypted".
- **Never in a message:** VIN, `<vid>`, plate or account name in any mesh field (ADR-0036,
  ADR-0038 §5). Inbound content is untrusted data; a message shaped like a command runs nothing.

## 5. Push-to-talk, voice calls and video calls

**PTT first.** One big PTT button per ride and group (half-duplex, floor control, a short roger
beep, music and navigation ducked, "who's talking" as one line). A **hardware PTT button**
(steering wheel, handlebar, a sensor-node input) arrives as a device input event the shell maps
to PTT; it is not a car action. On IP links PTT is a live audio track in the ride's LiveKit room;
on HaLow it degrades to **PTT bursts** (short clips, §6); on LoRa it is unavailable.

**Voice calls** (S2): 1:1 and group. 1:1 may go peer-to-peer with TURN fallback; groups use the
SFU. **Video calls** (S2, after voice): Parked, or on a passenger device; downgrade to voice when
the link falls (§6).

**Driving rules** (app-model §4.4 as amended; driver-distraction rules §7):

| Screen | Parked | Idling | Moving |
|---|---|---|---|
| Driver-facing head unit | full UI | `call` template, audio only; text entry only with Park evidence (handbrake or neutral) | **`call` template, audio only**: incoming = name + Accept / Decline + voice answer; in call = Mute / End / PTT. No video, no chat text, no list over six |
| Head-unit passenger view (core's lockout) | — | — | driving-related content only, so Social shows nothing beyond the `call` template; "Open on phone" hands off |
| Phone or rear screen with "I'm a passenger" (per trip, logged, re-prompted) | full | full | full Social, video included |
| Bike (phone in a mount) | full | audio + PTT | audio + PTT only |

**Video is never shown on a driver-facing screen while Idling or Moving, override or not**
(UK reg 109). Incoming calls while Moving ring only from ride members and favourites; others go
to missed calls with a callback card at the next stop (Decision 5).

**The `call` template** is a new shell template (by platform proposal; limits from
driver-distraction §7.2): caller name ≤ 30 characters, at most three targets of ≥ 76 px
(Accept/Decline, or Mute/End/PTT), call timer, link badge; no avatar photo, no text, no video.

## 6. The link router and per-class rules

Social runs the **Social link router** of [mesh transports §5](../references/research/mesh_transports.md)
on the brain (or inside the phone app on Ostler Diagnostics alone). It owns the outbound queue,
picks a link per message, de-duplicates inbound copies by envelope `id`, and is the only thing
Social and Vehicles & Map read. Link order: **internet → Wi-Fi mesh (batman-adv over 802.11s,
routed at each brain, Babel at the edge) → HaLow (UK/EU: car-to-camp uplink, not a mesh) →
LoRa (Meshtastic, then MeshCore)**. Every mesh is a remote path (ADR-0033 §6): Read and alerts
only.

**Envelope:** `{id (ULID), class, from (peer key fingerprint), to (peer, group or ride),
sent_at, expires_at, seq?, body}`; on LoRa, the compact payload of ADR-0038 §4 with a plain-text
fallback.

| Class | Links | Rule | If no link qualifies |
|---|---|---|---|
| `alert` | all | **multi-path**, receivers de-duplicate; 24 h expiry | queue |
| `text` | all | best single link; next link after 30 s (IP) or 5 min (LoRa) without a delivery report | queue (24 h) |
| `position` | all | best link; precision per link and per share; ghost sends none | drop |
| `telemetry` | IP; LoRa ≤ 4 owner-picked values | latest wins; ghost sends none | drop |
| `voice_note` / PTT burst | IP, HaLow (Codec2 or low-rate Opus, ≤ 10 s); LoRa off (later, Decision 9) | store and forward | offer text |
| `call_voice` | internet, Wi-Fi mesh | RTT < 300 ms, ≥ 2× codec rate | degrade to voice note, then text |
| `call_video` | internet, Wi-Fi mesh | ≥ 500 kbit/s, RTT < 300 ms | degrade to `call_voice` |
| `camera` | internet, Wi-Fi mesh; HaLow stills | only under a `camera` grant (§7) | stills, or nothing |
| `sync` (summaries, photos) | internet, Wi-Fi mesh, HaLow when idle | lowest priority, metered | wait |

Over a mesh, live voice, video and camera streams run **only between members of the same ride**
(ADR-0038 amendment of 2026-10-07, approved). The thresholds are estimates for the bench.

**MQTT topics** (module-bus spec §16, ADR-0038 amendment of 2026-10-07 item 5). The router is a device
`social` that publishes only under its own prefix; no new topic is a command topic:

| Topic (`ostler/v1/<vid>/…`) | Content |
|---|---|
| `social/inbox/<class>` | merged, de-duplicated inbound (QoS 1, not retained, with expiry) |
| `social/state/links` | ranked links with `rate_bps`, `rtt_ms`, `duty_left_pct`, peers heard (retained) |
| `social/state/call` | call or PTT state for the UI: ringing, in call, talking, via which link (retained, expiry) |
| `social/out/<bridge>/#` | outbound for one LoRa bridge, which subscribes to it instead of VSS directly |
| `mesh-<n>/in/*` (bridges) | payloads gain `id`, `class`, `via` (`meshtastic`, `meshcore`), `precision_m` on positions |
| `mesh-<n>/state/link` | gains `rate_bps`, `duty_left_pct`, `rtt_ms?` |

**Media never touch MQTT.** Calls and camera streams are WebRTC between phones, brains and the
SFU; only call **state** reaches the car broker.

## 7. Camera sharing (S4)

- A **`camera` grant**, never implied by `view` or `view+logs`: per camera (front, rear,
  interior separately), per contact, group or ride, **time-boxed** (default this ride or 1 h,
  at most 24 h; interior never open-ended), **live only** (no recording or scrub-back for the
  viewer; the UI says a viewer can still screen-record). It is the registry's `video` class at
  camera granularity; core defines it (Decision 4).
- **Ghost by default:** no camera is shared until the owner turns one on, with a local tap or a
  time-boxed ride share; a peer can never silently open a camera or a microphone.
- **"Being viewed by N"** badge on the car's head unit and the owner's phone while anyone
  watches. Every view is an **audit** entry (who, which camera, start, end, coarse bytes).
- **Viewing is Read** (ADR-0033 §1). Start/stop recording, pan/tilt/zoom, IR, talk-back through
  a car speaker and waking a camera are **not** Read: local only (or remote with the install
  override, never over a mesh); waking counts against the ADR-0040 quota.
- **Interior cameras and camera audio** are off by default; sharing an interior camera asks the
  occupants at the head unit each trip. No camera audio is shared by default (ADR-0010).
- **Clip export for posting** requires on-device face and plate blur and strips location per
  the share (later, with the Cameras add-on).
- On the driver-facing head unit, a shared camera from another car is never shown while
  Idling or Moving; one's own driving cameras follow the existing `camera_live` template.

## 8. Driving, privacy and compliance

- **Driver screens** (driver-distraction §7.1 #10): while Moving a message alert reads
  "Message from Sam" with **Play** (read aloud) and **Later**; never message content, photos or
  avatars. Reply by PTT voice note or the "I'm driving" auto-reply; no keyboard and no canned
  list. Task depth ≤ 3, ending back in Drive mode. Unknown speed counts as Moving.
- **ADR-0009:** location stays on the device unless a share grants it; Social sends positions
  only through the router under the registry's rules, time-limited when precise (≤ 24 h).
- **ADR-0010:** calls are **never recorded** by Ostler and nothing from a call enters a session
  log; a live call is not a cabin recording, and the two rules don't collide.
- **ADR-0033:** no actions; mesh and relay are remote paths; camera control stays local.
- **ADR-0036:** no VIN, its HMAC or a plate in any message, card, envelope or mesh field.
- **Audit (local):** camera views, share grants used by Social, the call log (who, when,
  duration, link), the passenger-override log (core's, local only). Message contents are not
  audited.
- **Offline:** two phones on one LAN, or two brains on a Wi-Fi mesh, need no internet: a brain
  hosts the ride's LiveKit room and token issuer; LoRa carries text, positions and alerts; the
  queue holds the rest. Peers find the room by the ride invite, not mDNS reflection.
- **Power:** a parked car's brain is not woken for a call by default; "wake for calls from
  group X" is an owner opt-in within the ADR-0040 quota (Decision 8).

## 9. Media stack and integrations

| Layer | Choice | Licence |
|---|---|---|
| SFU and TURN | **LiveKit server**, self-hosted on the Ostler Cloud relay and optionally a brain (lead car or camp box); embedded TURN, TURN-TLS on 443; E2EE (insertable streams) so the relay never sees media | Apache-2.0, run as a separate binary |
| Tokens | **our own token issuer** in Social's back end: LiveKit JWTs minted from an Ostler session or share; room = 1:1 pair, group or ride; grants = publish audio / video, subscribe camera X | ours |
| Client | browser WebRTC + LiveKit JS SDK in the PWA and phone build | Apache-2.0 |
| Voice | **Opus** 16–24 kbit/s, DTX, DRED where supported, 8 kbit/s floor; **Codec2** only for HaLow/LoRa voice notes (WASM or a brain-side encoder) | BSD; LGPL-2.1 as a marked library |
| Cameras | **go2rtc** on the brain → WHIP into the LiveKit room; MediaMTX as fallback; no transcoding on a Pi 5 | MIT |

**Integrations** (accounts spec §7, ADR-0029 §9):
- **Invite through WhatsApp or anything else** via the Web Share API share sheet or
  `wa.me/?text=` click-to-chat carrying the invite link; the secret stays in the URL fragment,
  so a link preview never sees it.
- **Share out** ride summaries and trip cards as images with a link (WhatsApp, Telegram,
  Signal, Facebook's share dialog via Ostler Cloud's app id); user-initiated only.
- **Notify via** the owner's own webhook or bot (Discord, Telegram, ntfy, Home Assistant) for
  ride start, end and alerts, per-destination opt-in.
- **Not done:** reading WhatsApp or Facebook chats, groups or friends; contact upload; the
  WhatsApp Business API or posting to pages (only ever via Ostler Cloud, if at all).
- **Social login** is core's (accounts spec): at most an optional Ostler Cloud OIDC broker that
  links to a local user; never friend discovery.
- **Matrix** is later interop only: a separate bridge service mapping a group to a Matrix room,
  and Element Call (AGPL, Element's) as a separate service, never in the add-on. Mumble or SIP
  bridges only if a club asks.

## 10. Phases

| Phase | Scope | Needs |
|---|---|---|
| **S1 Messaging + PTT** | chats (1:1, group, ride), voice notes, PTT in ride rooms over the internet (relay, Tailscale) and LAN; LiveKit on the relay; token issuer; `alert_card`, strip chip, Home card, More → Social | accounts contacts/groups/rides; app model UA; `alert_card` template; U2 lockouts |
| **S2 Calls** | voice calls, then video calls; `call` template; call log; Bluetooth/intercom bench | S1; `call` template; legal check of passenger view |
| **S3 Mesh bridges** | the full router; Wi-Fi mesh with LiveKit on a brain; Meshtastic bridge via `social/out/…`; HaLow uplink; then MeshCore | ADR-0038 amendment approved; bench results |
| **S4 Cameras** | `camera` grant, go2rtc WHIP, badge, audit, interior consent, blur on export | S2; Cameras add-on; `camera` class in core's registry |

**Tests (outline):** a message shaped like a command runs nothing; ghost emits no `position` or
`telemetry` on any link; one `alert` on three links appears once in `social/inbox/alert`; an
inbound call or camera request starts nothing without a local tap or a live grant; the driving
matrix (screen × state) never renders video or message text on a driver-facing head unit while
Idling or Moving; LiveKit tokens refuse rooms and grants outside the share; no media bytes on
the broker; no VIN, `<vid>` or plate in any envelope.

## 11. Open questions

1. iOS and Android background audio: can the phone build keep PTT alive with the screen off, and
   how do calls route to car Bluetooth and helmet intercoms without CallKit or Telecom? (bench)
2. Group size limits: SFU on a Pi 5 brain, and LoRa channel airtime for rides over ~10 members.
3. Where the token issuer runs for a relay room when no member's brain is online (phone-signed
   requests checked by the relay?).
4. Peer identity binding of mesh node ids: QR at the meet-up, or over IP before the ride.

## 12. Proposed amendment (2026-10-07, DMD round): message alerts while Moving

*Proposed, not approved. Changes the §8 "Driver screens" bullet and one §10 test, extends §4's
auto-reply and widens Decision 5 from calls to calls and message alerts. Until the owner
answers Decisions A1–A4 at the end, §8 and Decision 5 stand as approved. Evidence:
[message alerts research](../references/research/message_alerts_android_auto.md) (Android Auto,
Android for Cars, CarPlay, AAOS, the legal reading) and
[driver-distraction rules](../references/research/driver_distraction_rules.md) §4.2, §7.1 #10.
The shell-wide rule (every add-on's message alerts, the `alert_card` row, the U2 legal check
and tests) is a matching proposed amendment to the
[UI architecture spec](2026-10-06-ui-architecture-design.md) §12.1; where they differ, the UI
spec wins.*

**Owner's ask (2026-10-07):** "Message alerts: copy Android Auto. On the driver's head unit
while Moving, the `alert_card` shows the sender and app, with Play (read aloud) and Reply
(voice, or a canned reply). Add an owner opt-in to show a one-line first-line preview. Default
stays off."

**Old rule, the alternative:** while Moving a message alert reads "Message from Sam" with
**Play** and **Later**; never content; reply by PTT voice note or the "I'm driving" auto-reply;
no keyboard and **no canned list** (§8, approved 2026-10-07).

**Proposed §8 "Driver screens" bullet** (replaces the approved one):

> - **Driver screens** (driver-distraction §7.1 #10; UI spec §12.1 as amended). While Moving a
>   message alert is an `alert_card` with **the sender** ("Sam", or "Sam · Peak ride"; ≤ 30
>   characters) and **the app** ("Social", or "Social · 3 new"), and two buttons:
>   - **Play** reads it aloud (a message over 280 characters is announced first as "Sam sent
>     a long message"); attachments are named, never shown.
>   - **Reply** opens a `short_list`: **Speak a reply** (a voice note ≤ 30 s, or on-device
>     dictation read back with Send / Cancel and never shown as text while Moving), then up to
>     **five canned replies** (default "Driving, will reply later", "On my way", "Running
>     late", "OK, thanks", "Call you when I stop"; each ≤ 30 characters, plain text, edited
>     Parked only; one tap sends a normal signed, sealed message).
>   - No Later button: the card leaves after 8 s or on Back, and the message stays unread.
>   - **First-line preview**, an owner opt-in per user, **off by default** ("Show first line
>     of messages when parked"): for a message that arrives while Parked, or Idling with Park
>     evidence, line 2 shows its first line (plain text, ≤ 30 characters, "…" on overflow,
>     "Photo", "Voice note", "Location" or "Link" for non-text); it reverts to the app name as
>     soon as the vehicle moves. Never while Moving, never on a passenger-only display, never
>     images, avatars or stickers.
>   - **Rate limits:** one card at a time; one per conversation per 2 minutes; three message
>     cards per 10 minutes, then only the strip chip and Home unread count; groups other than
>     the active ride channel raise the count only ("Alert for group messages", default off);
>     never over a red telltale, the reverse camera, the `call` template or a navigation
>     manoeuvre prompt.
>   - Task depth ≤ 3, ending back in Drive mode. Unknown speed counts as Moving. If the U2
>     legal opinion objects to names, line 1 reads "New message".

**§4 addition:** the "I'm driving" auto-reply gains Driving Focus's scope setting (research
§1): reply to **no one, ride members, favourites or all contacts** (default favourites and ride
members), its text editable Parked only (≤ 60 characters), at most once per conversation per
trip.

**§10 test change:** "never renders video or message text on a driver-facing head unit while
Idling or Moving" reads "… while Moving, or Idling without Park evidence (and, until the U2
legal opinion, while Idling at all)". Add: with the preview on, a message that arrives while
Moving renders no text on a driver-facing display; a message that arrived while Parked loses
its preview when the vehicle moves; canned replies cannot be edited while Moving; the rate
limits hold; a canned reply is a message, never an action.

**Proposed Decision 5** (replaces the approved one): **Calls and message alerts while
Moving** — audio only via the `call` template, only ride members and favourites ring; message
alerts show sender and app with Play and Reply (voice or canned), an opt-in first-line preview
only for messages that arrive while parked, and the rate limits above? *Recommend:* yes.
*Alternative:* the approved Decision 5 for calls, with the approved §8 message alert
("Message from *name*", Play / Later, no canned list).

## 13. Proposed amendment (2026-10-07, DMD round): comms overlap

*Proposed, not approved. Settles where Social and the proposed
[Phone & Comms add-on](2026-10-07-phone-comms-addon-design.md) (`ostler-app-phone`, draft)
meet: the `call` session, the strip chip, one alert pipeline and one rate limit, favourites,
the call log and auto-reply; and (C6, reconcile revision) where Social meets
[Ostler Community](2026-10-07-community-hub-design.md) (draft v0.2). It changes §2's strip-chip row, §5's "Incoming calls while
Moving" sentence and §8's audit list only where noted; everything else stands. Until the owner
answers Decisions C1–C6 at the end, §1–§12 stand as approved or proposed. Evidence:
[phone and comms research](../references/research/phone_comms.md),
[message alerts](../references/research/message_alerts_android_auto.md).*

**C1 — One call session, owned by the shell.** The `call` template shows one call or PTT
channel (UI §12.1, app-model §14.5), so the shell, not an add-on, owns a single **call
session** that Social and Phone request through the SDK (a platform proposal with the Phone
spec: `calls.request({source, label, kind: "phone"|"ostler"|"ptt"})`, `calls.state`,
`calls.end`). Rules:
- At most one active `call` template; a second ringing call takes the template as **call
  waiting** (Hold & answer / Decline), never a stacked card.
- **Priority:** an incoming or active phone call (HFP) or Social voice call **pauses PTT**: the
  ride room is muted both ways for this member and the chip reads "Ride: on hold"; PTT bursts
  queue as voice notes (§6) and play after the call. A PTT press during a call does nothing.
- A Social call and a phone call are equal: whichever is active stays; the other is offered as
  call waiting (Social: hold the WebRTC track; phone: HFP hold).
- **Audio:** one audio focus; media and navigation voice duck for any call; the Brain's AEC
  (Phone §3.2) serves Social calls on head units too.
- **Strip chip:** §2's ride/call chip becomes the shell's **comms chip**, shown while a ride,
  a call or a connected phone is active: "Ride: Peak · PTT", "Call · 04:12", or the phone's
  battery and signal. Still one chip, still opens the `call` template while Moving.

**C2 — One alert pipeline, one rate limit.** Message alerts from Social, from Phone's MAP
(SMS/iMessage) and from Phone's Android notification bridge all enter the shell's one alert
queue under the UI spec §14 rules, and the §12 limits are counted **across every source**: one
message card on screen, one per conversation per 2 minutes (conversation key = source app +
conversation), **three message cards per 10 minutes in total**, then counts only; group rules
per source ("Alert for group messages" applies to Social groups and bridged group chats
alike). Calls are not message cards and are not rate-limited. Line 2 of a card names the real
app ("Social", "Messages", "WhatsApp"). Social's own messages never pass through Phone's
bridge (the bridge ignores the Ostler app's notifications), so nothing is shown twice.

**C3 — Favourites, one list.** "Favourites" in §5 (who rings while Moving) and in Phone's
dialer are **one per-user list** mixing Ostler contacts (a flag on the core contact, accounts
§14.6) and phone contacts (Phone's local favourites), ordered by the user; the Moving
`short_list` shows the first six. §5's rule "only ride members and favourites ring" keeps
applying to **Social calls**; phone calls follow Phone Decision 11 (all shown by default),
because the handset rings in-band whatever the car shows.

**C4 — One local call log.** The shell's call session writes one local log entry per call it
hosts (direction, source, label, contact ref or number, start, duration, link), per user,
90 days, never uploaded, exportable. §2's **Calls** tab is the Ostler-source view of it and
Phone's Recents the merged view; §8's audit "the call log" now means this log. Audio is never
recorded (ADR-0010).

**C5 — Auto-reply stays inside Ostler.** §4's "I'm driving" auto-reply (and §12's scoped
version) answers **Ostler messages only**. Canned replies (UI §14) are one shared list used by
Social and by Phone for MAP and bridged replies, but each reply is a single user tap or a
spoken reply; nothing is ever sent automatically into WhatsApp, Signal, Telegram, Messenger or
SMS (Telegram's API terms forbid acting without the user's knowledge; the phone's own driving
mode can auto-reply there).

**C6 — Social is the only messenger; links out to the forum (reconcile revision).** Ostler
Community has **no direct messages** (community hub spec v0.2 §9 and its test "no route exists
for user-to-user messages"), so Social is the one place Ostler users message each other; the
hub's notifications (replies, solved, events) are not chat and arrive through the hub add-on's
Home card, never as Social messages. Social **may link out** to hub content: a message may
carry a forum thread, help thread, wiki page or route link, shown as a plain link card (title
≤ 30 characters, "Ostler Community", no preview fetched until tapped, Parked only to open);
opening it goes to More → Community when `ostler-app-hub` is enabled, else the browser. A link
grants nothing: a help thread's attachment still needs the owner to name the helper (hub §8).
Social never posts into the hub, and the hub never reads Social conversations.

**§10 test additions:** a phone call pauses PTT and resumes it after; two calls never render
two `call` templates; four messages from Social and WhatsApp in 10 minutes give three cards
and one count; no Ostler message appears twice when the bridge is on; auto-reply never targets
a non-Ostler source; a hub link in a message fetches nothing until tapped and opens no
attachment for a recipient who is not a named helper.

## Changelog

- 2026-10-07: v0.1, first draft (Social add-on; reconciles the mesh transports and calls notes).
- 2026-10-07: v0.2, approved by the owner on 2026-10-07 ("approve all"): every decision
  answered as recommended (alternatives not chosen); the `more:social` slot is added to
  app-model §4.2 (§14.7); ADR-0038's mesh amendment approved with it.
- 2026-10-07: v0.3, proposed amendment (DMD round) §12, not approved: message alerts while
  Moving show sender and app with Play and Reply (voice or up to five canned replies), an
  opt-in first-line preview only for messages that arrive while parked, rate limits, a scoped
  auto-reply and a widened Decision 5; Decisions A1–A4 at the end. §8 and Decision 5 stand
  until answered.
- 2026-10-07: v0.4, proposed amendment (DMD round) §13, not approved: comms overlap with the
  draft Phone & Comms add-on (one shell-owned call session and comms chip, one alert pipeline
  with rate limits counted across sources, one favourites list, one local call log, auto-reply
  only for Ostler messages); Decisions C1–C5 at the end. Revised in place the same day
  (cross-spec reconcile): C6, Ostler Community has no direct messages, so Social is the only
  messenger and may link out to forum threads; Decision C6 added.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **Scope** — is Social messaging, PTT, calls and later cameras, with no feed or map? *Recommend:* yes. *Alternative:* add a group feed of ride summaries now (accounts spec §6).
2. **Placement** — More → Social page plus Home card, strip chip and alert cards? *Recommend:* yes, with a new `more:social` slot by platform proposal. *Alternative:* make Social a destination in place of one of the five.
3. **Strip chip** — a separate ride/call chip shown only while active? *Recommend:* yes. *Alternative:* fold ride and call state into core's visibility chip.
4. **Camera grant** — a separate `camera` grant (the registry's `video` class per camera), time-boxed, live only, ghost by default, badge and audit? *Recommend:* yes, defined in core's registry. *Alternative:* a plain `video` class without per-camera grants.
5. **Calls while Moving** — audio only via the `call` template; only ride members and favourites ring? *Recommend:* yes. *Alternative:* everyone allowed to call me rings.
6. **Message encryption** — per-recipient sealing with device keys for 1:1 and groups up to ~24, MLS (RFC 9420) later? *Recommend:* yes. *Alternative:* MLS from S1.
7. **Media stack** — LiveKit self-hosted on the relay and optionally a brain, our own token issuer, go2rtc for cameras, Matrix only as later interop? *Recommend:* yes. *Alternative:* Matrix with Element Call as the base.
8. **Waking a parked car for calls** — off by default, opt-in per group within the ADR-0040 quota? *Recommend:* yes. *Alternative:* never wake for calls.
9. **LoRa voice notes** — Codec2 voice notes over LoRa? *Recommend:* defer until the Meshtastic bridge ships and the bench shows the airtime. *Alternative:* build them in S3.
10. **Phases** — S1 messaging + PTT (internet/LAN), S2 calls, S3 mesh bridges, S4 cameras? *Recommend:* yes. *Alternative:* bring the mesh (S3) before calls for off-road groups.

## Decisions for the owner (proposed amendment, 2026-10-07, DMD round)

Open. Each has a recommendation and the alternative; the approved rule is the alternative
where one exists.

1. **A1 — Message card while Moving** — sender and app with **Play** and **Reply**, as Android
   Auto and CarPlay do, names covered by the U2 legal check with "New message" as the
   fallback? *Recommend:* yes. *Alternative:* the approved rule, "Message from *name*" with
   Play / Later, never content.
2. **A2 — Canned replies** — Reply opens a `short_list` with Speak a reply plus up to five
   owner-editable canned replies (≤ 30 characters, edited Parked only, one tap sends)?
   *Recommend:* yes. *Alternative:* the approved rule, voice note and the "I'm driving"
   auto-reply only, no canned list.
3. **A3 — First-line preview** — owner opt-in, default off, one line ≤ 30 characters, only for
   messages that arrive while Parked or Idling with Park evidence (Parked only until the U2
   legal opinion), reverting when the vehicle moves, never on a passenger-only display, never
   images? *Recommend:* yes (Android Auto's documented "stopped when they arrive" rule,
   tightened). *Alternative:* the owner's literal ask, a preview while Moving, released only if
   the U2 reg 109 opinion explicitly clears it (every other rule we track forbids it).
4. **A4 — Rate limits and auto-reply scope** — one card at a time, one per conversation per
   2 minutes, three per 10 minutes, non-ride groups as a count only; auto-reply to favourites
   and ride members by default? *Recommend:* yes. *Alternative:* a card for every message, and
   auto-reply to all contacts.

## Decisions for the owner (proposed amendment §13, 2026-10-07, DMD round: comms overlap)

Open. Each has a recommendation and the alternative.

1. **C1 — Call session** — one shell-owned call session for Social and Phone (one `call`
   template, call waiting, phone and Social calls pause PTT, one comms chip)? *Recommend:* yes,
   as a platform proposal with the Phone spec. *Alternative:* each add-on raises its own `call`
   template and the shell shows the newest.
2. **C2 — One alert pipeline and shared rate limits** — message cards from every source count
   against one budget (one per conversation per 2 min, three per 10 min in total)?
   *Recommend:* yes. *Alternative:* the §12 limits per add-on (up to three cards per add-on
   per 10 minutes).
3. **C3 — Favourites** — one per-user favourites list across Ostler and phone contacts, first
   six in the Moving `short_list`; §5's favourites-only ringing stays for Social calls?
   *Recommend:* yes. *Alternative:* separate Social and Phone favourites.
4. **C4 — Call log** — one local log written by the shell's call session, with Social's Calls
   tab and Phone's Recents as views? *Recommend:* yes. *Alternative:* each add-on keeps its own
   log; no merged recents.
5. **C5 — Auto-reply scope** — "I'm driving" auto-reply for Ostler messages only; canned
   replies shared but always one tap; never automatic into third-party apps or SMS?
   *Recommend:* yes. *Alternative:* allow auto-reply to SMS via MAP for favourites.
6. **C6 — Social and Ostler Community** — Social is the only Ostler messenger (the hub has no
   direct messages) and may link out to forum threads, help threads, wiki pages and routes as
   plain link cards that open More → Community or the browser; neither reads or posts into the
   other? *Recommend:* yes. *Alternative:* the hub adds its own direct messages between members
   (two messengers, and a closed operator holding private messages).
