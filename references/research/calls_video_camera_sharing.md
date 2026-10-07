---
title: "Calls, video and camera sharing — voice, video, push-to-talk and shared cameras over the internet and off-grid meshes"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0040-power-states-and-wake.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, references/research/mesh_networking.md, references/research/addons_catalogue.md, references/research/features_backlog.md]
summary: >
  Live research (2026-10-07) for the Social add-on's voice calls, video calls, push-to-talk and later sharing of car or phone cameras, over the internet and over off-grid meshes. Covers WebRTC basics (ICE, STUN, TURN; mobile CGNAT pushes roughly a fifth of sessions onto TURN), SFUs (LiveKit Apache-2.0, mediasoup ISC, Pion MIT, Janus GPL-3.0, Jitsi Apache-2.0), Matrix and Element Call (MatrixRTC on LiveKit; Element's parts AGPL-3.0 dual-licensed), SIP (Linphone AGPL/GPL dual, baresip BSD), Mumble (BSD-3) and PTT patterns (Zello, Cardo DMC, Sena Mesh), codecs (Opus 6 kbit/s and up with 1.5's DRED and NoLACE, Codec2 450–3200 bit/s LGPL-2.1, H.264/VP8/AV1), mesh budgets (EU HaLow 1 MHz and duty-cycle limits; LoRa cannot carry live voice; LXST is non-commercial), driver-distraction law (UK Reg 109 and 110, Highway Code 149, NHTSA), camera restreaming (go2rtc, MediaMTX; Pi 5 has no H.264 encoder) and dashcam privacy (ICO, EDPB 3/2019, Ryneš). Recommends LiveKit plus our own token service, go2rtc for cameras, audio-only while Moving, and a separate `camera` share scope.
---

# Calls, video and camera sharing

Research for the **Social** add-on ([addons catalogue](addons_catalogue.md),
[ADR-0029](../../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md),
[accounts spec §6](../../specs/2026-10-06-accounts-sharing-design.md)). It covers the call and camera
transport only; who may see what is the accounts/sharing permission system. Facts were checked live on
**2026-10-07**. **(U)** = unverified; **(est.)** = our arithmetic or a rule of thumb, not a measurement.
Sources are paraphrased, never copied, and listed in §11. The mesh layer itself is in
[mesh_networking.md](mesh_networking.md) and not repeated here.

## 1. What the owner asked for, and the short answer

| Want | Over the internet | Over an IP mesh (Wi-Fi, batman-adv/Babel, HaLow) | Over LoRa (Meshtastic, MeshCore) |
|---|---|---|---|
| Voice call (1:1, group) | yes: WebRTC, Opus | yes, same stack with a local SFU on a brain | **no live voice** (§6) |
| Push-to-talk / convoy intercom | yes | yes; the best off-grid fit | short Codec2 **voice notes**, store-and-forward, maybe |
| Video call | yes; **never on a driver-visible screen while Moving** (§7) | 2.4/5 GHz Wi-Fi mesh yes; EU HaLow **no** (§6) | no |
| Share a car or phone camera | yes: go2rtc → WebRTC, permissioned (§8) | Wi-Fi mesh yes; EU HaLow stills only | no (a text alert at most) |

**Recommended stack** (§10): **LiveKit** (Apache-2.0) as the SFU and TURN, with **our own token issuer**
bound to Ostler accounts and shares; browser WebRTC in the PWA; **go2rtc** (MIT) on the brain for cameras;
Opus everywhere for voice; Matrix/Element Call as an **optional interop** later, never in core.

## 2. WebRTC in five lines

- **ICE** gathers candidates (local, server-reflexive via **STUN**, relayed via **TURN**) and picks a
  working pair; DTLS-SRTP encrypts media hop by hop. Signalling is ours to choose (HTTPS/WebSocket).
- **NAT is the problem in cars.** Phones and in-car LTE routers sit behind carrier-grade NAT, which often
  maps a new external port per destination, so STUN-learned addresses don't work for the peer. Vendors
  of TURN services report roughly **15–25 %** of consumer sessions needing TURN, higher on locked-down
  mobile carriers, and close to all for IoT boxes behind CGNAT (vendor blogs, not studies: **(U)**).
  **Plan for TURN on every car-to-car call** over cellular; relay bandwidth is the cost driver.
- **TURN over TLS on 443** gets through hotel and corporate Wi-Fi; LiveKit embeds a TURN server with
  this option; **coturn** (BSD-3) is the standalone choice.
- **P2P mesh calls** (each sends to each) are fine for 2–3 people; beyond that an **SFU** (forwards,
  does not mix) saves the car's uplink: each car uploads once.
- **WHIP** (RFC 9725, March 2025) standardises WebRTC ingest over one HTTP POST; **WHEP** (playback)
  is still a draft. Both matter for cameras (§8): a camera or go2rtc can push into an SFU with WHIP.
- **E2EE through an SFU** uses insertable streams (frame encryption); LiveKit supports it on self-host
  at no cost, so a relay we run never sees media.

## 3. Servers compared

| Project | Licence | Shape | Fit for Ostler |
|---|---|---|---|
| **LiveKit server** | Apache-2.0 | Go SFU on Pion; rooms, JWT auth, simulcast/SVC, embedded TURN, E2EE, WHIP ingress; v1.13.3 (July 2026) | **Best fit.** One binary on the brain (local/mesh) and on the Ostler Cloud relay. Permissive, so core stays dual-licensable (ADR-0012). Apache-2.0 client SDKs (JS, Swift, Kotlin) (U: SDK licences per repo not re-checked) |
| **mediasoup** | ISC | C++ worker with Node/Rust API; a library, no signalling or rooms | Good but we'd build the server. Pick only if LiveKit's model fights us |
| **Pion** | MIT | Go WebRTC stack (v4) | Building block (LiveKit uses it); useful for a tiny brain-side peer (camera bridge, PTT bot) |
| **Janus** | GPL-3.0 | C gateway with plugins (SIP, streaming, AudioBridge mixing) | GPL-3 allowed by ADR-0025 only as a marked module; no reason to choose it over LiveKit |
| **Jitsi Meet / Videobridge** | Apache-2.0 | Full meetings product (Prosody XMPP, Jicofo, JVB) | Heavy (Java, several services); meeting UX, not car UX. Reference only |
| **coturn** | BSD-3 | STUN/TURN | Use if TURN must run apart from LiveKit |
| **Mumble** (murmur) | BSD-3 | Low-latency Opus voice, channels, PTT, positional audio; 1.5.x | Proven off-grid convoy voice; desktop clients only, Android via **Mumla** (GPL-3, third party) (§5) |

## 4. Matrix, Element Call and SIP

- **MatrixRTC + Element Call.** Matrix calling has moved from legacy 1:1 and Jitsi widgets to MatrixRTC;
  Element Call uses **LiveKit** as the media backend (MSC4195) and runs standalone, as a widget inside
  Element Web/Element X, or as an experimental React component. Self-host needs a homeserver, LiveKit,
  the **MatrixRTC Authorization Service** (`lk-jwt-service`, Go; turns a Matrix OpenID token into a
  LiveKit JWT) and a TLS proxy. Element Call and lk-jwt-service are **AGPL-3.0 dual-licensed by
  Element**; we could not relicense them commercially (ADR-0012), so they may only run as a **separate
  service**, never inside core. A Rust re-implementation of the JWT service exists (licence **(U)**).
- **Light homeservers** for a brain: **Continuwuity** and **Tuwunel** (both Apache-2.0, Rust,
  Conduit lineage) target small boxes including a Pi; Synapse (AGPL) is heavy.
- **What Matrix buys:** federation, chat history, E2EE rooms, many existing clients. **What it costs:**
  another identity system beside Ostler accounts (ADR-0029 rejects third-party login), a homeserver per
  group, and chat semantics we don't otherwise need for "talk to the convoy". The useful observation:
  **if Matrix is chosen for messaging, MatrixRTC already runs on LiveKit**, so a LiveKit SFU we deploy
  now is reusable either way.
- **SIP.** Linphone/liblinphone is GPL/AGPL with a paid licence (Belledonne); baresip is BSD-3. SIP
  suits bridging to a phone line or a club's PBX; it adds nothing for PWA-to-PWA calls and NAT is no
  easier. Keep as an interop idea (Asterisk/FreeSWITCH bridge), not the base.

## 5. Push-to-talk and intercom patterns (copy the UX, not the code)

| System | How it works | Lesson for a convoy |
|---|---|---|
| **Zello** | Phone walkie-talkie over its servers; channels; encoder bitrate chosen by both ends' link, about 12 kbit/s on 2G up to 45 kbit/s on Wi-Fi; closed | Half-duplex PTT tolerates bad links and is far less distracting than open calls; adapt bitrate per listener |
| **Cardo DMC** | Proprietary self-healing mesh between helmets; up to 15 riders; claimed ~1.6 km rider-to-rider, testers see ~0.9–1.2 km | Riders drop and rejoin without anyone pressing anything: **auto-rejoin, no call setup** |
| **Sena Mesh 2.0** | Same idea; **Group Mesh** up to 24, **Open Mesh** "unlimited" on a channel; ~2 km claimed | Two modes: a private group, and an open channel for events |
| **Mumble** | Server-based channels, PTT or voice activity, Opus, positional audio | Works entirely on a LAN/mesh; nothing needs the internet |

Copy: **one big PTT button** (or a steering-wheel or handlebar button through an add-on input), a
channel = the ride (accounts spec §6), auto-join when the ride starts and leave at ride end, ducking of
music and navigation, a short roger beep, and "who's talking" as one line of text. **Interop with
helmet intercoms** is Bluetooth: the phone's audio goes to the helmet as a call or as media; a
PWA's WebRTC audio usually routes like a call on Android and iOS (U: route and HFP behaviour per OS not
tested).

## 6. Codecs and what each link can carry

| Codec | Rate | Notes |
|---|---|---|
| **Opus** (RFC 6716, BSD) | 6–510 kbit/s; speech good at 12–24, usable at 6–8 | libopus 1.5 (2024) adds **DRED** (about a second of redundancy for 12–32 kbit/s extra), deep PLC, and **LACE/NoLACE** enhancement down to 6 kbit/s wideband. Mandatory in WebRTC |
| **Codec2** (LGPL-2.1) | 3200, 2400, 1600, 1400, 1300, 1200, 700, 450 bit/s | Radio-grade speech; FreeDV uses it; several FreeDV modes are now unmaintained. Not in browsers: needs WASM or a native peer |
| **H.264** | ~0.3–0.6 Mbit/s for 360p, 1–2.5 for 720p (est.) | Universal hardware decode. **Pi 5 has no H.264 encoder**; libx264 does 1080p30 low-latency on ~60 % of one core. Pi 4 has one |
| **VP8** | similar to H.264 | WebRTC baseline; software only on Pi |
| **AV1** | ~30–50 % below H.264 at low rates (est.) | Best at very low bitrates and with SVC; encode is costly without hardware, so it suits phones, not the brain (U: per-phone support) |

**Link budgets** (est. unless cited):

| Link | Usable rate | Voice | Video |
|---|---|---|---|
| 4G/5G via TURN | 1–20 Mbit/s up, variable | yes | yes, simulcast with a low layer |
| 2.4/5 GHz Wi-Fi mesh (batman-adv or Babel), few hops | several Mbit/s, halving per hop | yes | yes, 360–720p |
| HaLow, US (1–8 MHz) | up to ~32 Mbit/s near, ~2 Mbit/s at 16 km (Morse Micro) | yes | yes; a 3 km video call was demonstrated |
| **HaLow, UK/EU (863–868 MHz)** | five **1 MHz** channels, ≤ ~4.4 Mbit/s PHY; reported duty-cycle limits around 10 % per hour for an AP and 2.8 % for a client (U: depends on the mode under ETSI EN 300 220) | **PTT bursts only**; continuous calls would exhaust a client's airtime | **stills only** (a JPEG every few seconds) |
| LoRa, sub-GHz (Meshtastic/MeshCore) | ~0.3–22 kbit/s and duty-cycle limited | **no**; even Meshtastic's own audio module needs 2.4 GHz | no |
| LoRa 2.4 GHz (SX1280) | a few kbit/s | Meshtastic's **experimental** audio module: Codec2 (700B default), PTT GPIO, I2S mic/speaker, two LilyGo boards only | no |

- **Codec2 voice notes over sub-GHz LoRa** (est.): 5 s at 700 bit/s ≈ 440 bytes ≈ 2–3 Meshtastic packets
  (U: ~230-byte payload). Feasible as rare store-and-forward "voice texts" within duty cycle; never a call.
- **LXST** (Reticulum's voice transport: Opus ~4.5–96 kbit/s, Codec2 700–3200 bit/s) is **CC BY-NC-ND
  4.0** — non-commercial, no derivatives — and self-described as unstable. **Avoid** in any product
  path; references only, consistent with ADR-0038 §7.

## 7. Calls in a moving car: what is allowed

- **UK.** Regulation 110 bans hand-held use of a phone or interactive device for any purpose while
  driving (tightened March 2022); hands-free calls with the device in a cradle are legal. Highway Code
  rule 149 still requires **proper control**, and hands-free use can be prosecuted after a crash.
  **Regulation 109** forbids a driver-visible screen showing anything other than vehicle state,
  location, help seeing the road or navigation: **a video call on a driver-visible head unit is
  unlawful while driving**, hands-free or not.
- **US (NHTSA visual-manual guidelines, voluntary):** glances ≤ 2 s, ≤ 12 s total per task; video
  calling, text entry, and display of messages and web pages disabled unless parked.
- **Platforms agree:** Android for Cars allows **audio-only** VoIP calling apps through its templates
  and the Telecom call APIs; CarPlay communication apps are audio via CallKit (U: entitlement details).
- **For Ostler:** on a head-unit layout class while **Moving**: audio only; incoming call = a card with
  name, **Accept / Decline** (two big targets) and voice answer; in call = **Mute / End / PTT**; no
  video tile, no chat text, no contact list over six (UI spec §3.5, app-model §4.4). The **"I'm a
  passenger" override cannot unlock video on the driver-facing head unit** — Reg 109 is about what the
  driver can see, not who asked. Passengers use their own phone or a rear screen, which may show video.
- **Bikes:** audio only, PTT preferred, with the phone in a mount (accounts spec §6).

## 8. Camera sharing

**Pipeline.** Cameras (dashcam, reversing, underbody, interior, a phone) → **go2rtc** (MIT; RTSP,
ONVIF, RTMP, MJPEG, HomeKit in; WebRTC, MSE, HLS, MP4, RTSP out; WHIP/WHEP; two-way audio) on the brain,
already the catalogue choice ([addons catalogue](addons_catalogue.md), backlog #7 and #28). Locally the
PWA plays WebRTC straight from go2rtc. For **sharing with friends**, go2rtc (or the camera) pushes the
stream into the **LiveKit room** by WHIP, so the same SFU, TURN, tokens, E2EE and audit serve calls and
cameras: one permission path, no second exposed port. **MediaMTX** (MIT; RTSP, WebRTC, SRT, HLS, RTMP,
Media-over-QUIC; internal users, HTTP or **JWT** auth; Pi camera native) is the alternative if go2rtc's
auth proves too thin. **Never transcode on a Pi 5**: buy cameras that encode H.264 themselves and pass
through; let the SFU's simulcast or a low second stream serve weak links.

**Permissions (fits ADR-0033 and the accounts spec).**
- **Viewing a camera is Read** (ADR-0033 §1), so it is allowed on remote paths (§6) without the
  override. **Everything that changes the camera is not Read**: start/stop recording (Accessories),
  pan/tilt/zoom, IR light, **talk-back through a car speaker** and **waking** a sleeping camera
  (ADR-0040 wake quota). Those stay local, or remote only with `OSTLER_ALLOW_REMOTE_CONTROL`.
- **A new share scope `camera`**, never implied by `view` or `view+logs` (accounts spec §5.3):
  per **camera** (front, rear, interior listed separately), per **friend or group**, **time-boxed**
  (default: this ride, or 1 hour; no "forever" for interior), **live only** (viewers get no
  recording or scrub-back; a viewer can still screen-record, so the UI says so).
- **Ghost mode** (the default) shares no camera. Turning on a share shows a **"being viewed by N"**
  badge on the car's head unit and phone, and every view is an audit entry (who, which camera, start,
  end, coarse bytes), like other pulls.
- **Interior cameras and audio** are the most sensitive: off by default, a per-trip consent prompt to
  occupants at the head unit when shared, and **no camera audio shared by default** — consistent with
  ADR-0010 (cabin audio stays on the device) and the ICO's in-vehicle guidance (audio off by default).
- **Mesh:** ADR-0038 §2 lists what goes out over a mesh (position, alarm state, chosen alerts); a
  camera stream is not on it, so **video over a Wi-Fi IP mesh needs an ADR-0038 amendment**; over
  LoRa never.

**Privacy law (UK/EU), plainly.**
- The ICO treats a dashcam used **purely personally** as outside UK GDPR (no fee); a dashcam used for
  work is not domestic. Its home-CCTV advice still applies as good practice: capture no more than
  needed, delete routinely, blur where possible, honour objections.
- The EU reads the household exemption **narrowly**: in *Ryneš* (C-212/13) a camera covering public
  space fell outside it, and EDPB Guidelines 3/2019 follow that. Commentators note the ICO's line is
  looser and the UK position is unsettled. **Publishing** footage (social media) almost certainly
  leaves the exemption.
- So: **live sharing to named friends** is the least-risk shape; **clip export for posting** should
  offer automatic **face and plate blur** (a later Frigate or on-phone detector), strip location per
  the share and add no VIN. Ostler as software is not the controller of a user's footage when it is
  local-first and E2EE through our relay (U: legal reading, not advice).

## 9. Where it sits in Ostler

- **App:** Social is an optional app (app-model §3, §7), declaring no vehicle actions for calls.
  A call is people talking, not a car action, so ADR-0033 categories don't gate it; driving state does.
- **Identity:** LiveKit JWTs are minted by **our** token issuer from an Ostler session or share (ADR-0029,
  accounts spec §2.4), with room = ride, group or 1:1 pair and grants = publish audio / publish video /
  subscribe camera X. No Matrix or third-party login needed. (lk-jwt-service's idea, reimplemented;
  ADR-0025.)
- **Placement:** a LiveKit instance on the **Ostler Cloud relay** for internet calls (ADR-0028), and
  optionally on a **brain** for off-grid groups on a Wi-Fi mesh (the convoy's lead car or the camp
  box hosts the room; others find it by the ride's invite, not mDNS reflection, ADR-0038 §1).
  1:1 calls may go P2P with TURN fallback; groups use the SFU.
- **Power:** a parked car's brain is not woken for an incoming call by default; an owner may allow
  "wake for calls from group X" within ADR-0040's quota (U: cost of an always-listening LTE path).

## 10. Recommended stack (licences)

| Layer | Pick | Licence | Why |
|---|---|---|---|
| Media server and TURN | LiveKit server (embedded TURN; coturn only if needed) | Apache-2.0 (coturn BSD-3) | Permissive, one binary, E2EE, WHIP ingress, used by MatrixRTC |
| Client | Browser WebRTC in the PWA + LiveKit JS SDK | Apache-2.0 (U) | No separate app; same code on head unit and phone |
| Auth | Our own token issuer | ours (AGPL/dual) | One permission system |
| Voice codec | Opus, 16–24 kbit/s, DTX on, DRED where supported; 8 kbit/s floor on weak links | BSD | Mandatory in WebRTC, robust |
| Off-grid voice | The same LiveKit on a brain; Mumble only for interop with existing groups | Apache-2.0; BSD-3 | Nothing needs the internet |
| LoRa | Codec2 voice notes later, via the GPL-3 Meshtastic bridge (ADR-0038 §3) | LGPL-2.1 | Only bursts are possible |
| Cameras | go2rtc → WHIP into LiveKit; MediaMTX as fallback | MIT | Already chosen for local cameras |
| Interop later | Element Call/MatrixRTC as a separate service; SIP via baresip or a PBX | AGPL (Element), BSD-3 | Kept out of core |
| Avoid | LXST (CC BY-NC-ND), Janus (GPL-3, no gain), Zello/Cardo/Sena (closed) | — | Licence or lock-in |

## 11. Sources (checked 2026-10-07)

- LiveKit: [server releases on pkg.go.dev](https://pkg.go.dev/github.com/livekit/livekit-server@v1.13.3),
  [E2EE](https://docs.livekit.io/home/client/tracks/encryption), [self-hosting](https://docs.livekit.io/transport/self-hosting/deployment/).
- Matrix: [Element Call](https://github.com/element-hq/element-call), [lk-jwt-service](https://github.com/element-hq/lk-jwt-service),
  [This Week in Matrix 2026-06-19](https://matrix.org/blog/2026/06/19/this-week-in-matrix-2026-06-19/),
  [Continuwuity](https://www.linuxlinks.com/continuwuity-community-driven-matrix-homeserver/), [Tuwunel package](https://pkgs.alpinelinux.org/package/edge/testing/aarch64/tuwunel).
- SFUs and TURN: [mediasoup](https://github.com/versatica/mediasoup), [Pion](https://github.com/pion/webrtc),
  [Janus](https://github.com/meetecho/janus-gateway), [Jitsi Meet](https://github.com/jitsi/jitsi-meet), [coturn](https://github.com/coturn/coturn/),
  [TURN share on mobile (vendor blog)](https://www.expressturn.com/blog/webrtc-calls-fail-on-mobile-networks), [WHIP RFC 9725](https://www.rfc-editor.org/rfc/rfc9725).
- Voice: [Mumble](https://en.wikipedia.org/wiki/Mumble_(software)), [Mumla](https://apt.izzysoft.de/fdroid/index/apk/se.lublin.mumla?repo=main),
  [Linphone docs](https://linphone.org/releases/docs/liblinphone/5.1/c), [Zello bandwidth](https://support.zello.com/zw/how-much-data-bandwidth-does-the-app-use),
  [Cardo vs Sena](https://blog.rad.eu/en/cardo-or-sena-which-intercom-suits-me-best/), [Packtalk Pro vs 60S](https://itsbetterontheroad.com/?p=23284).
- Codecs: [libopus 1.5](https://opus-codec.org/release/stable/2024/03/04/libopus-1_5.html), [Codec 2](https://en.wikipedia.org/wiki/Codec_2),
  [Pi 5 H.264 whitepaper](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf).
- Mesh: [Meshtastic audio module guide](https://openelab.io/fr/blogs/getting-started/meshtastic-guide-audio-module-setup-guide),
  [LXST](https://github.com/markqvist/LXST), [HaLow in Europe (Igor's Lab)](https://www.igorslab.de/en/wi-fi-halow-with-kilometer-range-why-the-new-gl-inet-halowlink-2-is-reaching-its-limits-in-europe/),
  [HaLow video call demo](https://www.morsemicro.com/2024/01/24/morse-micro-pushes-wi-fi-to-the-limits-with-a-two-mile-wi-fi-halow-video-call-demo/),
  [HaLow 16 km trial](https://www.techradar.com/pro/groundbreaking-wireless-tech-that-can-run-on-coin-batteries-for-months-hits-new-milestone-halow-achieves-10-mile-range-in-latest-test).
- Driving: [Reg 109 (1986)](https://www.legislation.gov.uk/uksi/1986/1078/regulation/109/made?view=plain), [2022 amendment](https://www.legislation.gov.uk/uksi/2022/81/regulation/3/made),
  [Rule 149 memorandum](https://assets.publishing.service.gov.uk/media/62053d3cd3bf7f3148fe3ecc/explanatory-memorandum-to-the-revision-of-the-highway-code-rule-149-about-using-mobile-phones-while-driving.pdf),
  [NHTSA guidelines](https://www.nhtsa.gov/sites/nhtsa.gov/files/strickland-distraction_guidelines_03122012.pdf),
  [Android for Cars communication apps](https://developers.google.com/cars/design/create-apps/app-types/communication).
- Cameras and privacy: [go2rtc](https://github.com/AlexxIT/go2rtc), [MediaMTX](https://github.com/bluenviron/mediamtx),
  [ICO surveillance in vehicles](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/cctv-and-video-surveillance/guidance-on-video-surveillance-including-cctv/additional-considerations-for-technologies-other-than-cctv/surveillance-in-vehicles/),
  [ICO home CCTV](https://ico.org.uk/your-data-matters/domestic-cctv-systems-guidance-for-people-using-cctv/),
  [ICO dashcams for small business](https://ico.org.uk/for-organisations/advice-for-small-organisations/cctv-and-dashcams/dashcams-and-uk-gdpr-what-small-businesses-need-to-know/),
  [EDPB Guidelines 3/2019](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201903_video_devices_en.pdf),
  [Dashcams and domestic purposes (commentary)](https://informationrightsandwrongs.com/2021/02/06/dashcams-and-domestic-purposes/).

## 12. Copy / Avoid / Decide for Ostler

**Copy**
- **LiveKit's room-and-token model**, with tokens minted from our accounts and shares → ADR-0029,
  accounts spec §2.4 and §5.
- **Intercom UX** from Cardo/Sena/Zello: auto-join the ride channel, auto-rejoin, one PTT button,
  ducking → accounts spec §6 (rides), app-model §4.4 (templates).
- **Android for Cars' audio-only calling rule** while Moving → UI spec §3.5, app-model §4.4.
- **go2rtc → WHIP → SFU** for camera sharing, one permission path for calls and cameras →
  addons catalogue (Cameras), features backlog #7/#28.
- **Opus with DTX and DRED**; Codec2 only for LoRa voice notes → ADR-0038 §3 bridge.
- **ICO practice**: audio off by default, routine deletion, blur on export → ADR-0010, accounts spec §5.3.

**Avoid**
- **LXST and anything non-commercial** in a product path → ADR-0025, ADR-0038 §7.
- **Embedding Element Call or lk-jwt-service in core** (AGPL owned by Element; breaks dual licensing)
  → ADR-0012.
- **Video on any driver-visible screen while Moving**, passenger override included → UI spec §3.5.
- **Transcoding on the Pi 5** (no H.264 encoder) → hardware spec, addons catalogue.
- **Live calls over sub-GHz LoRa or EU HaLow**; promise PTT bursts and stills there at most → ADR-0038.
- **Closed PTT services** (Zello) or proprietary helmet meshes as dependencies → ADR-0017.
- **Treating camera viewing as covered by `view`** → accounts spec §5.3.

**Decide** (recommendation in bold)
1. **Calls transport:** LiveKit (Apache-2.0) self-hosted on the Ostler Cloud relay and optionally on a
   brain, with our own token issuer; Matrix only as later interop. → **Approve**; record in an
   ADR-0029 amendment or a Social spec.
2. **Driving rule:** on head-unit layout classes while Moving, calls are audio only (call card with
   Accept/Decline, Mute/End/PTT); the "I'm a passenger" override never unlocks video on the
   driver-facing screen; video only Parked or on passenger devices. → **Approve**; add a `call`
   driver-safe template to app-model §4.4 by platform change.
3. **Camera share scope:** a separate `camera` scope per camera, per friend or group, time-boxed
   (default this ride or 1 h; interior never open-ended), live only, ghost by default, "being viewed"
   badge, every view audited; camera audio not shared by default. → **Approve**; amend accounts spec §5.3.
4. **Camera actions stay off remote paths:** viewing is Read; recording, PTZ, IR, talk-back and waking a
   camera are Accessories (or ADR-0040 wakes) and local unless the install override is on. → **Approve**;
   note under ADR-0033 §1/§6.
5. **Mesh scope:** amend ADR-0038 §2 to allow live voice and camera streams over a Wi-Fi IP mesh
   (2.4/5 GHz, US HaLow) between ride members only, still no actions; EU HaLow carries PTT and stills;
   LoRa carries Codec2 voice notes at most. → **Approve the amendment; Codec2 voice notes deferred**
   until the Meshtastic bridge ships.
6. **Off-grid voice server:** the same LiveKit on a brain (lead car or camp box) rather than adding
   Mumble; Mumble only as an interop bridge if a club asks. → **Approve**.
7. **Clip export blur:** posting a clip outside Ostler requires the face/plate-blur step (on-device),
   with location stripped per the share. → **Approve as the rule; build later** with the camera add-on.
8. **Car hands-free integration:** the PWA cannot register with CallKit/Android Telecom, so calls play
   as media/communication audio, not native car calls; native integration waits for the thin
   CarPlay/Android Auto companions. → **Accept the PWA limit for now; bench-test Bluetooth routing
   in a car and on a helmet intercom** (test plan item).
