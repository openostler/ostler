---
title: "Head-unit apps — every standard head-unit page mapped to an Ostler app: Radio, Audio, Media, Camera, Phone, Navigation, vehicle settings, steering-wheel controls, clock and weather, voice, projection and climate, with UX outlines, hardware and open legal points — design"
area: specs
status: stable
version: 0.3
updated: 2026-10-07
depends_on: [decisions/adr-0045-ux-first.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, references/research/canbus_headunit.md, references/research/driver_distraction_rules.md, references/research/hardware.md, GOALS.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all", OS round; decision list items 36–40, 54 and 55), v0.2; every decision answered as recommended. Maps every page a head unit has to an Ostler app or to the OS, with a UX outline, hardware options, v1 or later, and open legal points. Two setups: the Brain as the head-unit computer (Ostler owns the audio path) or an aftermarket Android head unit used as a display (its own radio and projection stay). Radio (FM, AM, DAB+, RDS and DLS, slideshow, presets, seek and scan, service following, traffic announcements; tuners as device integrations: an Si468x-based HAT or module, or a USB SDR dongle), Audio (EQ, balance and fade, loudness, volume limits, speed-dependent volume, crossover and time alignment Parked and owner-only, a software DSP on the Brain or an external DSP, USB or I2S DACs, source switching through the OS's audio focus), Media (local and USB, Bluetooth A2DP and AVRCP shared with Phone & Comms, internet radio and podcasts later, streaming services an open legal point, video Parked or passenger-only), Camera (reverse trigger from a pack signal or a 12 V input, static and steering-angle guidelines, other views Parked only), Phone and Navigation (their approved specs), a Car app for pack-declared comfort settings, steering-wheel control learning in the OS, clock and weather, an on-device voice assistant later (a spoken yes never confirms a gated action), projection not built, with the certification and licensing limits stated plainly, and climate where a pack or device supports it. Audio focus priorities, phases HU0–HU5, tests and decisions. Amended 2026-10-07 (openness round, ADR-0047): front and side road cameras may show while Moving under an owner speed setting (reg 109(c)), cabin views stay Parked only, and uncertified projection receivers and unofficial streaming clients may be sideloaded as community items.
---

# Head-unit apps — design

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("this should
> be an open system", then "apply the loosenings";
> [ADR-0047](../decisions/adr-0047-openness-round.md)):** road-facing front and side camera
> views may show while Moving (UK reg 109(c) allows a view of the road next to the vehicle),
> through `camera_live`, whose speed limit is an owner setting (default 10 km/h); cabin views
> and dashcam playback stay Parked only (§6). Uncertified projection receivers (§11) and
> unofficial streaming clients (§5) may be sideloaded as community items at the owner's risk;
> the Store catalogue still does not list them and Ostler does not build them. No video on a
> driver-facing display while Moving is unchanged.

**Status:** approved by the owner on 2026-10-07 ("approve all", OS round; decision list
items 36–40, 54 and 55), v0.2. Every app here starts with a UX brief
([ADR-0045](../decisions/adr-0045-ux-first.md)). It depends on
[ADR-0046](../decisions/adr-0046-empty-os-every-app-an-add-on.md), which removes
GOALS' non-goal "Rebuilding media: CarPlay/Android Auto, radio, amplifier and wheel controls
stay on a media head unit" ([GOALS](../GOALS.md) §3) and adding projection receivers as the
non-goal instead (applied to GOALS on 2026-10-07). Templates, the gate and the lockouts are unchanged
([UI spec §12.1](2026-10-06-ui-architecture-design.md)).

## 1. Context and the two setups

The owner (2026-10-07): a radio app (DAB, with an equaliser that connects to a DAC), and every
standard page a head unit has, all replicated. Earlier research advised keeping the head unit
for radio and projection and running Ostler beside it
([CAN-bus and head-unit research](../references/research/canbus_headunit.md) §B4–§B7). Both
setups stay supported:

| Setup | What drives the speakers | What the head-unit apps do |
|---|---|---|
| **A. Ostler head unit** | the Brain, through a DAC (and a DSP) to the amplifier | everything in this spec |
| **B. Android head unit as a display** | the head unit's own tuner, media and amplifier | Ostler's Radio and Audio apps are not offered (the hardware is closed); Media, Camera, Phone and Navigation work as far as the head unit's audio and inputs allow; projection stays on the head unit |

## 2. Every standard page, mapped

| Head-unit page | Ostler | Repo | v1 or later |
|---|---|---|---|
| Home / launcher | OS launcher | `ostler` | v1 ([launcher](2026-10-07-launcher-and-widgets-design.md)) |
| Radio | Radio app + tuner integration | `ostler-app-radio`, `ostler-integration-<tuner>` | v1 (one tuner path, Decision 1) |
| Audio settings | Audio app | `ostler-app-audio` | v1 (EQ, balance, fade, limits); crossover and time alignment later |
| Music (USB, local, Bluetooth) | Media app | `ostler-app-media` | v1 |
| Streaming | Media app | `ostler-app-media` | later; services an open legal point |
| Phone | Phone app (Phone & Comms) | `ostler-app-phone` | per [its spec](2026-10-07-phone-comms-addon-design.md) |
| Navigation | Navigation app | `ostler-app-navigation` | per [its spec](2026-10-07-navigation-addon-design.md) |
| Reverse camera | OS reverse view + Camera app | `ostler`, `ostler-app-camera` | v1 |
| Other cameras, dashcam | Camera app | `ostler-app-camera` | later |
| Car settings | Car app | `ostler-app-car` | later (needs packs that declare settings) |
| Climate | Climate app | `ostler-app-climate` | later |
| Steering-wheel controls | OS input | `ostler` | v1 for pack and HID sources; resistor ladders later |
| Clock | starter widget + OS time | `ostler-widgets-starter` | v1 |
| Weather | Weather app | `ostler-app-weather` | later |
| Voice assistant | Voice app | `ostler-app-voice` | later |
| Projection (Android Auto, CarPlay) | open (§11) | — | not planned |
| Video player | Media app, Parked or passenger-only displays | `ostler-app-media` | later |
| Settings (display, Bluetooth, Wi-Fi, sound, system) | OS system Settings | `ostler` | v1 |
| App store | OS Store | `ostler` | v1 ([Store](2026-10-07-store-design.md)) |
| Tyre pressures | a TPMS integration (add-on module) | `ostler-integration-tpms` | later |

## 3. Radio

**UX outline.**
- **Now playing:** station name, band, signal quality; on DAB+ the DLS text and the
  slideshow, on FM the RDS name and RadioText (all Parked); a preset row (≤ 6 per page of
  presets); seek back and forward; band switch (FM, AM, DAB+).
- **Stations:** DAB+ services A–Z, FM by frequency or name; a programme-type filter (Parked);
  **Rescan** (Parked).
- **Service following:** the same station on FM when DAB+ fades (DAB linkage or the RDS
  programme id), on by default with a small "FM" word when it switches.
- **Traffic announcements:** off by default; when on, an announcement takes audio focus as
  `alert` (§13) and shows a small chip, never a card with text.
- **While Moving:** the `media` template: station name as the title (≤ 30), the DL Plus artist
  and title as the second line (≤ 30, static, never scrolling), a static station logo,
  seek as skip, volume; presets through a `short_list` (≤ 6). No slideshow, no raw DLS or
  RadioText, no station list.
- **Widgets:** Radio (launcher §9). **Drive menu rows:** next preset, previous preset, band.

**Hardware (tuners are `device` integrations, app UI model §6).**

| Option | How it connects | For | Against |
|---|---|---|---|
| **Si468x-based HAT or module** (Si468x family; variants differ in DAB, FM and AM support) | SPI or I2C control; I2S audio to the DAC | DAB+ decoded in the chip, low CPU, good FM and RDS | needs the vendor's firmware images loaded at each boot (redistribution terms to check); fewer boards on sale |
| **USB SDR dongle** (RTL2832U class) | USB; decoding in software on the Brain | cheap, common | CPU load on a Pi; AM needs direct sampling or an upconverter; a software DAB+ decoder and its licence (ADR-0025) |
| **Our own tuner module** (later) | the module bus for control, I2S or analogue audio | fits the module contract | a hardware project |

DAB+ needs a Band III antenna (an active one needs bias power); FM and AM use the car's
antenna through an adapter.

**Open legal points.** HE-AAC decoding (DAB+) in software may fall under a patent pool
licence (a chip that decodes in hardware avoids it); the Si468x firmware's redistribution
terms; selling tuner hardware brings radio-equipment conformity (CE, UKCA); recording
broadcasts is not offered.

## 4. Audio

**UX outline.**
- **Sound:** EQ (a 10-band graphic EQ, or a parametric EQ with up to 10 bands, Parked),
  presets (sound or EQ preset objects; switchable while Moving through a `short_list`),
  loudness, bass and treble shortcuts.
- **Balance and fade:** a 2D pad (Parked) and listening positions (Driver, Front, All) as a
  `short_list` while Moving.
- **Volume:** a start-up volume cap, a maximum, **speed-dependent volume** (`Vehicle.Speed`
  from the VSS stream), per-source trims.
- **Speakers (owner role, Parked, with a warning):** outputs and their roles (front left,
  tweeter, sub …), **crossover** (high-pass and low-pass, slope), **time alignment** (per
  output delay from distances in cm), sub level and phase. Speaker-safe limits per role (a
  tweeter output refuses a high-pass under its safe limit without a second confirm).
- **Sources:** the active source comes from the OS's audio focus (Radio, Media, Phone,
  Navigation prompts, alerts); a source list to switch by hand.

**Hardware and engine.**
- **DACs:** USB Audio Class 2 DACs (no driver on Linux) and I2S DAC HATs. Active crossovers
  need a multichannel output (a multichannel USB interface).
- **DSP:** v1 is a software DSP on the Brain (a PipeWire filter chain or a dedicated DSP
  engine; the choice and its licence go through ADR-0025 in the app's spec). An external DSP
  board is a later `device` integration with its own control protocol.
- Presets are **sound or EQ preset** objects (app UI model §9) and travel as files.

**Safety.** Volume ramps, never a jump to full; alerts and calls duck media (§13); speaker
settings are Parked and owner-only.

## 5. Media

**UX outline.**
- **Library:** local and USB storage (USB mounted read-only), by artist, album, folder and
  playlist; artwork; gapless playback; indexing in the background, Parked.
- **Bluetooth audio:** the Brain as an A2DP sink with AVRCP control (metadata, play, pause,
  skip), sharing the adapter and the paired phone with Phone & Comms' hands-free service; one
  pairing covers both.
- **Streaming (later):** internet radio and podcasts (opt-in outbound paths, app UI model
  §10); AirPlay and UPnP renderers; streaming services are an open legal point. Unofficial
  clients for commercial services are not built or listed, but may be sideloaded as community
  items with a terms warning (Store §8; *amended 2026-10-07, openness round*).
- **While Moving:** the `media` template (title and artist ≤ 30 each, static artwork,
  play, pause, skip, volume) and a `short_list` for one level of browsing (recent,
  playlists). No search, no long lists.
- **Video (later):** Parked only, or on a passenger-only display declared by the owner; never
  on a driver-facing display while Moving (UI spec §12.1).

**Open legal points.** Unofficial clients for commercial streaming services may break their
terms; some audio codecs still carry patent licences in some markets; Bluetooth codecs beyond
SBC may need licences.

## 6. Camera

**UX outline.**
- **Reverse view (system, ADR-0046 §2):** opens on reverse, above everything but a red alarm;
  `camera_live` while Moving below the owner's limit (default 10 km/h); closes a set time after
  leaving reverse.
- **Reverse trigger:** a pack signal (reverse gear or reverse lamp) from the node, or a 12 V
  reverse wire into a node or I/O-module input. Where the head unit has its own camera input
  (setup B), that fast path stays the reverse view ([research §B4](../references/research/canbus_headunit.md)).
- **Guidelines:** static lines calibrated at setup (0.5 m, 1 m, 2 m), or dynamic lines from
  the steering angle when the pack provides it.
- **Other views:** road-facing **front and side** views may also show while Moving as
  `camera_live`, below the owner's speed setting (UK reg 109(c); *amended 2026-10-07,
  openness round*); **cabin** views, 360 and dashcam clips stay Parked only.
- **Setup flow:** find cameras, pick the reverse camera, calibrate guidelines, test the
  trigger.

**Hardware.** IP cameras (RTSP or ONVIF, Ethernet or PoE, ADR-0027), USB UVC cameras, and
analogue or AHD cameras through a capture dongle; latency is measured on the bench (HU0).

**Open legal points.** Dashcam and cabin recording (data protection when people are filmed,
local rules, audio consent; recording stays opt-in and on the device, ADR-0010).

## 7. Phone and Navigation

Both have approved specs: [Phone & Comms](2026-10-07-phone-comms-addon-design.md) (dialer,
contacts, recents, messages, hands-free through the Brain) and
[Navigation](2026-10-07-navigation-addon-design.md) (routing on the Brain, guidance through
the `map` template, voice). They become apps under ADR-0046 unchanged; the call session and
audio focus are the OS's (§13).

## 8. Car settings from packs

A **Car** app (`ostler-app-car`) shows the comfort settings a pack declares for its systems
(for example auto-lock, lights or mirror folding), each an action through the gate with its
category and tier copied from the capability manifest (ADR-0033). Comfort changes may run
while Moving only through a driver-safe template the pack declares (`setpoint` or a toggle);
everything else is Parked. Diagnostics keeps the full technical settings list; the Car app
shows the owner-facing subset. Later, as packs declare settings.

## 9. Steering-wheel control learning (OS)

Input is a system service ([ShellInput](2026-10-07-shell-input-design.md); ADR-0046 §1).
Sources: buttons a pack decodes from a car bus (read-only), HID remotes, and later analogue
**resistor-ladder** buttons read by an I/O module's ADC. **Learning** (Settings → Input,
Parked): press each button, the OS records its code or voltage band, then pick an intent
(`up`, `down`, `ok`, `back`, `volume_up`, `volume_down`, `next`, `previous`, `ptt`, `voice`,
`mute`). Ostler never sends button presses to the car.

## 10. Clock, weather and voice

- **Clock:** the OS time service (the best clock source, GPS first) and the starter Clock
  widget.
- **Weather (later):** `ostler-app-weather`, an opt-in outbound path to an open-data weather
  service; coarse location by default; offline it shows the last forecast with its age; the
  widget's Moving form is `value` (temperature and one word). Official warnings stay in the
  Alerts app.
- **Voice assistant (later):** `ostler-app-voice`, **on the device only** by default (wake
  word, speech to text, intents, the OS voice to answer). Intents are limited to driver-safe
  ones (play a station, call a favourite, navigate to a place, next page, Mark). **A spoken
  "yes" never counts as a confirmation for a gated action**, as an AI client's accept never
  does. Needs a microphone with echo cancellation. Engines and licences go in its own spec.

## 11. Projection (Android Auto, CarPlay): not built

Stated plainly:

- **Android Auto as a receiver** is licensed by Google to head-unit makers whose units pass
  its certification. Open receivers exist but are not certified, break when the phone app
  changes, and may conflict with Google's terms
  ([research §B7](../references/research/canbus_headunit.md)).
- **CarPlay as a receiver** needs Apple's licensing programme for accessory makers and an
  authentication chip. An open project cannot ship it.
- **Wireless dongles** turn a head unit's wired projection into wireless; they do not add
  projection to a Brain.

**Decision (owner, 2026-10-07):** Ostler does not build projection receivers. Owners who want projection
keep a projection-capable head unit (setup B) with Ostler beside it. Ostler's own thin
companions inside Android Auto and CarPlay stay as ADR-0042 decision 2 says. The Store does
not list uncertified receivers. *Amended 2026-10-07 (openness round):* an uncertified community
receiver may be sideloaded as a developer item, with a warning that it is uncertified
(decision 4's alternative, adopted as an option; Store §8).

## 12. Climate

Where a pack declares climate signals and actions, or an add-on device (such as the owner's
separate HEVAC controller) offers them, a **Climate** app (`ostler-app-climate`) shows them:
the `setpoint` template while Moving (Comfort category, ADR-0033), a full page Parked. GOALS'
non-goal "HEVAC control inside the platform" stands: the app talks to such a device only as an
add-on device. Later.

## 13. Audio focus (OS)

One owner of the speakers (ADR-0046 §1). Priority, highest first: **alarm** (siren or alarm
tone, never ducked) → **call** (media paused) → **navigation prompt** (media ducked) →
**alert read-out** (message Play, traffic announcement; media ducked) → **media** (Radio,
Media, Bluetooth). Apps request focus through the SDK (`permissions.audio`); the OS decides.

## 14. Phases

| Phase | Ships | Needs |
|---|---|---|
| **HU0** | UX briefs for Radio, Audio, Media, Camera; bench: one tuner per option, one USB and one I2S DAC, A2DP beside the hands-free service, camera latency | ADR-0045 |
| **HU1** | Audio focus in the OS; Media (local, USB, Bluetooth); Audio (EQ, balance, fade, volume limits, speed volume) on recorded fixtures, then wired | HU0, UA3 |
| **HU2** | Radio with the chosen tuner path; service following; the Radio widget | HU1 |
| **HU3** | Reverse view and trigger, guidelines, Camera setup | HU0 |
| **HU4** | Crossover and time alignment (multichannel); resistor-ladder learning (I/O module); Weather | HU1 |
| **HU5** | Streaming, video for passengers, Car and Climate apps, Voice | per spec |

## 15. Tests

- **Moving:** Radio, Media and Audio render only `media` and `short_list` while Moving; no
  DLS, RadioText, slideshow, list over 6 rows or text over 30 characters; video never renders
  on a driver-facing display.
- **Audio focus:** a call pauses media; a navigation prompt ducks it; an alarm tone is never
  ducked; two apps asking for media focus get one.
- **Speakers:** crossover and time-alignment writes are refused while Moving and for a
  non-owner; a tweeter high-pass under its safe limit needs a second confirm.
- **Camera:** a reverse fixture opens the reverse view within the latency target on the
  bench; the reverse view shows above any page and below a red alarm.
- **Voice:** a spoken confirm never satisfies a gated action (gate test).
- **Projection:** nothing in the Store catalogue or the OS offers a projection receiver; a
  sideloaded one carries the Sideloaded badge and the uncertified warning.
- **Cameras while Moving:** a front or side road view renders as `camera_live` below the owner's
  speed setting; a cabin view is refused while Moving.

## 16. Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", OS round; decision list items
36–40, 54 and 55). Each recommendation below is the decision; each alternative was not chosen.

1. **First tuner path?** Recommend: an Si468x-based HAT or module (DAB+ in hardware).
   Alternative: a USB SDR dongle first.
2. **Software DSP on the Brain in v1?** Recommend: yes; external DSP later. Alternative: an
   external DSP board only.
3. **Crossover and time alignment in v1?** Recommend: later (HU4, multichannel hardware).
   Alternative: v1 with a stereo-only limit.
4. **Projection?** Recommend: not built; keep a projection head unit beside Ostler.
   Alternative: allow an uncertified community receiver as a sideload-only developer item.
5. **Streaming services?** Recommend: internet radio, podcasts, AirPlay and UPnP only; no
   unofficial clients for commercial services. Alternative: list them as community items.
6. **Car and Climate apps?** Recommend: later, once two packs declare settings (rule of two).
   Alternative: build the Car app on the D2 alone now.
7. **Weather separate from Alerts?** Recommend: separate apps. Alternative: one app.
8. **Traffic announcements default?** Recommend: off. Alternative: on.

## Changelog

- 2026-10-07: v0.1, first draft from the owner's direction of 2026-10-07, for ADR-0046.
- 2026-10-07: v0.2, approved by the owner on 2026-10-07 ("approve all", OS round; decision
  list items 36–40, 54 and 55): every decision answered as recommended (alternatives not chosen).
- 2026-10-07: v0.3, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", [ADR-0047](../decisions/adr-0047-openness-round.md)): front and side road
  cameras while Moving under an owner speed setting; sideloaded community projection receivers
  and streaming clients (decisions 4–5's alternatives as options).
