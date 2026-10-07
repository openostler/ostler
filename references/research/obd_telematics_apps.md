---
title: "OBD and telematics apps — Drive mode, trips, extension and business models (RealDash deep dive, Automatic and Dash post-mortems)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/ui/obd_apps.md, references/research/ui/app_model.md, references/research/ui/head_unit_ui.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-05-session-logbook-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md]
summary: >
  Goes beyond ui/obd_apps.md (diagnostic UI) to how Torque Pro, Car Scanner, OBD Fusion, OVMS Connect, DashCommand, RealDash, AutoZen and the dead Automatic and Dash handle the screen while driving, trips and post-trip review, plugins and add-ons, export and sharing, and money. RealDash is studied as the Drive-mode reference: inputs bound to gauges with normal/warning/critical levels, triggers and actions, community dashboards, CAN XML channel files, two-tier trips versus datalogs, and why it has no CarPlay or Android Auto. Ends with Styling and Copy / Avoid / Decide for Drive mode and Trips.
---

# OBD and telematics apps: Drive mode, trips, add-ons and money (October 2026)

## Scope and method

- [ui/obd_apps.md](ui/obd_apps.md) already covers these apps' **diagnostic UI**: connection, garage,
  DTCs, readiness, custom PIDs, module lists, paywalls. This note does not repeat that. It covers
  what the owner's ecosystem direction needs: the **screen while driving**, **trips and post-trip
  review**, **extension models**, **export and sharing**, **business models**, and what killed the
  two best-known consumer telematics products.
- Facts were checked live on 2026-10-07 (store listings, vendor sites, the RealDash Discourse forum
  read through its JSON API, the Unlicense RealDash-extras repo, press archives). Store text is
  vendor marketing. Items marked *(unverified)* could not be confirmed.
- CarPlay and Android for Cars template rules are in [ui/app_model.md](ui/app_model.md); NHTSA
  numbers and the lockout table are in [ui/head_unit_ui.md](ui/head_unit_ui.md). Not repeated here.

## At a glance

| App | Status (Oct 2026) | While driving | Trips and review | Export / share | Extension model | Money |
|---|---|---|---|---|---|---|
| **Torque Pro** | Android only; last update Feb 2025 | Custom dial dashboards, HUD | GPS + OBD log, Track Recorder video overlay | CSV, live **HTTP upload** to any URL (HA used it) | Separate plugin APKs (Advanced EX per make, Track Recorder) | ~$5 one-off; plugins paid |
| **Car Scanner** | Active; 4.8★ (33K) on iOS | Dashboard builder, HUD; CarPlay per forum reports *(not in listing)* | Trip computer, CSV logs, replay with map | CSV | Per-make connection profiles (built in) | Free + ads; Pro $3.99–7.99 incl. lifetime; collects ad identifiers |
| **OBD Fusion** | Active; v7.4.0 (Jul 2026) | Gauges on phone; **CarPlay list only**, it states gauges are not allowed | Multiple trip meters, trip stats page, GPS map plotted by parameter | CSV, iCloud, Dropbox, shareable reports, dashboard import/export | Paid per-make enhanced packs ($14.99) | ~$10 + packs |
| **DashCommand** | Stale; last iOS build Feb 2023 | Skinned dashboards, skidpad, track map, **inclinometer** | Log + playback, 0–60, ¼ mile | Skins shared as files | **DashXL editor on Windows**, community skins | $9.99 + vehicle packs $9.99 |
| **OVMS Connect** | Active; v2.3.4 | None in-car (no CarPlay/Watch) | New **timeline of charges, trips and parking** with SoC loss | Own MQTT broker; no cloud | Command shortcuts pinned to dashboard | $3.99 one-off, "no data collected" |
| **RealDash** | Active; v2.7.1 (23 Sep 2026); 3.7★ on iOS | Full-screen game-engine dashboards; voice commands | Trips (few values, ~1 Hz) **and** datalogs (all inputs); playback as a data source | CSV, MSL; My RealDash cloud sync | XML channel files, RealDash CAN protocol, community dashboards | Full version $5.99, dashboards $1.99–5.99, My RealDash €24/yr, manufacturer licence |
| **AutoZen** | Active; Android only; 1M+ installs | **Driving launcher**: nav, media, messages read aloud, speed cameras, split screen | None | None | Android widgets inside the launcher | Free; premium €5.99/yr or €17.99 lifetime (2020 prices) |
| **Automatic** | **Dead 28 May 2020** | Adapter **chirped** on hard brake, hard acceleration, > 70 mph | Trip timeline with cost per trip, parking spot | App gallery + developer API, IFTTT | Third-party app gallery (20+ apps at launch) | Hardware $80–130, Pro with 5 yr 3G; later subscription |
| **Dash** | **Gone** (company listed inactive) *(shutdown date unverified)* | Audio alerts, gamified | Automatic drive history, driver score | Chassis API (2014) | Developer API, OEM assistant integrations | Free app; fleet (Dash XL) and anonymised analytics (Dash IQ), insurer pilots |

## Per app — what is new beyond ui/obd_apps.md

### Torque Pro
- **Live web upload:** a "Upload to web-server" setting posts every logged PID to a URL you choose.
  Home Assistant's `torque` integration consumed it; HA now marks it legacy and community-maintained
  ([HA torque](https://www.home-assistant.io/integrations/torque/)). ABRP also accepted Torque data.
  This is the earliest "get the car's data into other apps" hook in the consumer space, and it
  shows the cost of an ad-hoc format: every receiver re-implements it and it rots.
- **Plugins are separate apps** that bind to Torque over Android IPC; the paid **Track Recorder**
  overlays OBD, GPS and accelerometer data on video with a map inset, up to three USB cameras
  ([Track Recorder listing](https://cafebazaar.ir/app/org.prowl.recorder?l=en)).

### Car Scanner
- Owners report it on CarPlay ([ranger6g forum](https://www.ranger6g.com/forum/threads/obd2-info-displayed-in-carplay.19234));
  the US listing does not mention it. A recurring forum point: OBD apps poll every few seconds,
  so CarPlay values feel laggy. The **privacy label** lists identifiers for advertising, the
  opposite of our stance ([App Store](https://apps.apple.com/us/app/car-scanner-elm-obd2/id1259933623)).

### OBD Fusion
- The cleanest statement of the CarPlay limit: vital values appear as a **list**, dashboards
  cannot. Trips: multiple trip meters, an improved Trip Statistics page (Jul 2026), parameters
  plotted on a GPS map, EV energy cost. Export to CSV, iCloud and Dropbox; reports are shareable
  ([App Store](https://apps.apple.com/us/app/obd-fusion/id650684932)).

### DashCommand (Palmer Performance)
- Dashboards are **skins built in a free Windows editor (DashXL)** and traded as files; the app
  ships portrait and landscape skin sets with buttons to move between pages. Skidpad, track map
  and **inclinometer work without OBD** (phone sensors only) ([Palmer](https://www.palmerperformance.com/products/dashcommand/iphone/index.php)).
  An inclinometer is a natural D2 off-road tile. Reviews call the look dated; updates stopped 2023
  ([App Store](https://apps.apple.com/us/app/dashcommand-obd-ii-gauges/id321293183)).

### OVMS Connect
- One-off price, no cloud, credentials on device, and a 2026 **timeline** mixing trips, charges and
  parked periods with state-of-charge lost while parked ([App Store](https://apps.apple.com/app/id6747955064)).
  That is the same shape as our Logs/Trips timeline (UI spec §3.4).

### AutoZen
- Not an OBD app: a **driving launcher** for Android phones ("Cockpit", "Coolwalk" split, Map and
  Speedometer layouts; AutoZen or native Android widgets; messages read aloud with voice reply;
  speed-camera alerts; weather) ([autozenapp.com](https://autozenapp.com/), checked 2026-10-07).
  The launcher-as-default, return-to-app and auto-play features are the paid tier
  ([Xataka](https://www.xatakandroid.com/aplicaciones-android/autozen-alternativa-a-android-auto-que-evita-distracciones-coche)).
  Lesson: the most-installed "drive screen" here wins on **media, messages and navigation**, not
  gauges. Our Drive mode must leave room for a map and a media strip, or users will leave it for
  CarPlay.

## RealDash deep dive (the Drive-mode reference)

### Model
RealDash (Napko, Finland; built on a game engine) has one clean data model:
**inputs → gauges → levels → triggers/actions**.
- **Inputs** are named values in categories ("Engine/ECU Inputs", "ECU Specific", GPS, phone,
  dummies). Built-in inputs have numeric **targetIds** (RPM = 37), a fixed shared vocabulary so a
  dashboard works on any ECU. Our VSS paths ([ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)) play the same role.
- **Gauges** (needle, bar, text, image, map, video, music…) bind one input and have **Range,
  Warning Level and Critical Level** (min/max pairs). Every visual property (colour, opacity,
  blend) can differ per level, so an indicator is an image at near-zero opacity in Normal that
  appears in Warning ([levels manual](https://www.realdash.net/manuals/using_normal_warning_and_critical_levels.php),
  [indicator manual](https://www.realdash.net/manuals/make_an_indicator.php)). Levels are also
  set **per vehicle profile** ([ui/obd_apps.md](ui/obd_apps.md#realdash-android-ios-windows)).
- **Triggers → actions**: value conditions fire actions (fade layers, change dummy variables,
  start video recording, write a CAN frame, reset lap timer). Premium dashboards use hidden
  buttons and dummy variables to switch modes; the developer admits they are too complex to learn
  from ([forum 5573](https://forum.realdash.net/t/5573)).

### Editor and screens
- Edit mode on the device itself: Add Gauge, Input & Values, Look'n Feel. Dashboards built on a
  tablet distort on a 1024×600 head unit; the fix was a hidden `[NOSCALE]` flag, later an option
  ([forum 635](https://forum.realdash.net/t/635)). **Lesson: layouts must be authored per layout
  class**, not scaled.
- Premium dashboards copy OEM clusters (Virtual Cockpit, Alfa 4C-inspired "Hot Tub", S2000, F40)
  and use a **two-page pattern**: page 1 is the cluster with **tap-to-cycle centre views**
  (Classic / Simple / Map, or boost, fuel, g-force, music, map); page 2 is a "centre console" with
  music, navigation, trip, colour settings, read/clear codes and datalogging
  ([gallery](https://www.realdash.net/gallery.php)).
- **Data Multicast** links several RealDash instances on one LAN (host plus clients, chosen inputs
  only) so one screen can steer another ([manual](https://www.realdash.net/manuals/datamulticast.php)).
  Our MQTT/node model already does this better ([ADR-0027](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md)).

### Channel files and the RealDash CAN protocol (public domain)
- **CAN XML** ([description file](https://github.com/janimm/RealDash-extras/blob/master/RealDash-CAN/realdash-can-description-file.md)):
  `<RealDashCAN version="2"><frames baseId>` → `<frame id endianness signed size readOnly timeout writeInterval>`
  → `<value targetId|name offset length startbit bitcount conversion units endianness>`. Notable:
  **composite ids** (`0x3E8:5533,0,2`, a multiplexor read from the payload), a per-frame
  **timeout** that drops values to "offline" so gauges do not stick, and **`readOnly`** so a bad
  action cannot transmit. `name` instead of `targetId` creates an ECU-specific input, but then
  dashboards that use it need the same XML: the vocabulary problem in one sentence.
- **RealDash CAN** ([protocol](https://github.com/janimm/RealDash-extras/blob/master/RealDash-CAN/realdash-can-protocol.md)):
  `44 33 22 11` + LE id + 8 bytes; `66 33 22 1x` CAN-FD-sized with CRC32; `55` text frames; `67`
  config frames; RealDash can send SET VALUE frames back. Adapters such as WiCAN speak it natively
  ([canbus_headunit.md](canbus_headunit.md)). Licence: Unlicense, so we may emit it.
- OBD-II polling uses the separate `init`/`rotation` XML already noted in [ui/obd_apps.md](ui/obd_apps.md).

### Trips versus datalogs, and post-trip review
- RealDash keeps **two tiers**: *trips* save a few values about once a second because road trips
  last hours; *datalogs* save every chosen input for analysis. The developer steers racing users
  to datalogs ([forum 1081](https://forum.realdash.net/t/1081)). Playback works by choosing
  **Datalog Playback as the data source**, so any dashboard replays a log ([forum 4292](https://forum.realdash.net/t/4292)).
- Users asked in 2021 for exactly what the owner likes in Speedometer: **speed-coloured map
  trace, jump to max speed, variable playback speed, gauges during playback, trip compare**. The
  developer said "build it in your own dashboard" ([forum 1081](https://forum.realdash.net/t/1081)).
  In 2024 the built-in viewer was frozen in favour of a **web log viewer** in My RealDash
  ([forum 5903](https://forum.realdash.net/t/5903)). Trips export as CSV only (users wanted GPX).
- Choosing which inputs to log lives in app settings, not the XML, so teams cannot copy it between
  devices ([forum 5458](https://forum.realdash.net/t/5458)).

### Community dashboards and money
- **Community Dashboards** (2022): upload from the editor to my.realdash.net, add name and
  description, share with all, with named users, or (manufacturers) with invited customers. Shared
  dashboards are **unlocked and editable** unless derived from a premium one
  ([forum 1240](https://forum.realdash.net/t/1240)).
- Purchases cannot cross app stores, so **My RealDash** (€24/yr) exists to unlock all platforms and
  sync trips, datalogs, dashboards and settings ([forum 1567](https://forum.realdash.net/t/1567),
  [my.realdash.net](https://my.realdash.net)). The **Manufacturer licence** buys commercial use,
  a custom build with a default dashboard, preset connections, hidden settings and one custom
  protocol; "Unlimited" removes RealDash branding ([forum 1029](https://forum.realdash.net/t/1029)).
  Hardware makers (ECUs, CAN boxes) market "works with RealDash": the integration *is* the channel.
- Internet is used for map tiles, speed limits, the gallery and licence checks; it runs offline
  but must check in now and then ([FAQ](https://www.realdash.net/faq.php)).

### CarPlay and Android Auto: why not
- The developer tested both: their APIs admit templated categories, and a full-screen real-time
  game-engine app is not one; Android Auto's navigation surface was then capped near 10 Hz
  ([forum 868](https://forum.realdash.net/t/868), [forum 467](https://forum.realdash.net/t/467)).
  Apple **refused** a submission ([forum 3371](https://forum.realdash.net/t/3371)). Users instead
  run RealDash on **aftermarket Android head units** or jailbreak CarBridge. Supporting another
  projection target was "yet another version" for a tiny team with a dozen builds already.
- Takeaway for Ostler: our Drive mode is a **PWA on the head unit or a dedicated screen**, the
  same place RealDash users ended up. CarPlay/AA are for alerts and lists, never gauges.

## Automatic and Dash: what they did and why they died

**Automatic** (2013–2020). A BLE OBD dongle plus phone app: trip log with fuel cost per trip,
check-engine decoding, parking spot, crash alert with a call-back service, teen-driver geofences,
and **audio chirps** for hard braking, hard acceleration and > 70 mph, the only live feedback;
reviewers found the acceleration chirp fired on almost every start ([Engadget review](https://www.engadget.com/2013-11-26-automatic-link-review.html),
[Android Police](https://www.androidpolice.com/2014/04/30/automatic-link-review-the-one-nag-whose-yammering-might-actually-improve-your-driving/)).
In 2015 it opened an **App Gallery and developer API** (IFTTT, Expensify, Nest, Pebble at launch)
([TechCrunch](https://techcrunch.com/2015/05/19/automatic-launches-its-sdk-turning-the-car-into-an-app-platform/amp/)).
The 2016 Pro adapter had 5 years of 3G built in for $129.95 ([MacRumors](https://macrumors.com/2016/08/17/new-automatic-pro-car-adapter)).
SiriusXM bought it in 2017 (~$100M). It shut on 28 May 2020: crash alerts, location sharing and
roadside help stopped that night, "Log in with Automatic" and third-party apps a month later;
buyers got pro-rata rebates ([SlashGear](https://www.slashgear.com/automatic-labs-connected-car-dongle-shutdown-iot-siriusxm-01618989/),
[9to5Mac](https://9to5mac.com/2020/05/01/automatic-labs-shutting-down/)). COVID was the stated
reason; observers pointed at the parent's cost-cutting and at carmakers bundling their own
connected services. Whether users could bulk-export history before the end *(unverified)*.

**Dash** (Dash Labs, NYC, 2012–). A free Android then iOS app on any Bluetooth ELM327, sold as a
"Fitbit for cars": automatic drive history, **driver score and friends leaderboard**, check-engine
explanations, gas prices, find-my-car, audio alerts ([TechCrunch 2014](https://techcrunch.com/2014/01/25/dashs-smart-driving-app-a-fitbit-for-cars-arrives-on-android/)).
The **Chassis API** (2014) exposed fuel, efficiency, hard braking and speeding to developers
([TechCrunch](https://techcrunch.com/?p=1065480)). With ~300K drivers it pivoted to **Dash XL**
(small-fleet ELD) and **Dash IQ** (anonymised analytics for agencies), plus insurer pilots
([TechCrunch 2015](https://techcrunch.com/2015/11/30/smart-driving-app-dash-expands-into-the-trucking-and-analytics-business/)).
It raised a small crowdfunded round in 2018 and is now listed inactive; the app is gone from the
stores *(exact end date unverified)*.

**Lessons**
1. **A cloud you do not own is a kill switch.** Safety features (crash alert) and every
   integration died the same night. Our local-first ADR-0009 is the answer; it must also hold for
   add-ons that reach the internet.
2. **Free app + data resale is a trust trap.** Dash's road to revenue ran through insurers and
   analytics. Ostler's ghost-mode default and "location never leaves the device by default"
   are a feature to state loudly.
3. **Scores and chirps are crude.** Thresholds without context (hills, towing, a Td5 merging) nag;
   leaderboards reward the wrong thing. Keep raw facts private, make any score opt-in.
4. **Platforms die when the anchor product dies.** Automatic's gallery had no life without
   Automatic's servers. Our add-ons talk to the local API, so they survive us.
5. **Plain trip value wins**: cost per trip, where I parked, what the light means. These were the
   most-praised features and need no cloud.

## Cross-cutting patterns

**While driving.** Three answers exist: (a) *phone/tablet dashboards* in the driver's view, with no
safety model (Torque, Car Scanner, RealDash, DashCommand); (b) *projection* limited to lists and
templates (OBD Fusion and Car Scanner on CarPlay); (c) *launcher* that hides the phone behind big
media, nav and message tiles (AutoZen). Only (c) thinks about distraction, and none of them lock
anything when moving. Ostler's server-enforced Moving state ([UI spec §3.5](../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode))
is ahead of the whole field.

**Trips.** Everyone splits *summaries* from *logs*: OBD Fusion trip meters vs logs, RealDash trips
vs datalogs, Automatic and OVMS Connect timelines. Review is weak everywhere except new
single-purpose apps: replay is "play the log back into the dashboard" (RealDash) or a CSV.
Speed-coloured traces, max-speed jump, sprint records and trip compare are user requests nobody
in this set ships well. Our logbook replay ([session logbook spec](../../specs/2026-10-05-session-logbook-design.md#ui))
already has the coloured trace and transport bar.

**Extension models.** Separate plugin apps (Torque), paid per-make packs (OBD Fusion, DashCommand),
data files (RealDash XML, Torque CSV, DashXL skins), an app gallery on a cloud API (Automatic,
Dash), and a white-label build (RealDash manufacturer). Data-file extensions outlived the rest.

**Sharing and export.** CSV is universal; GPX is surprisingly rare (RealDash users ask for it);
live push to a URL (Torque) or MQTT (OVMS) is the only real-time path. Dashboards share as files
(DashCommand, OBD Fusion) or via a vendor cloud (RealDash).

**Business models.** One-off (Torque, OVMS Connect, DashCommand), freemium + ads (Car Scanner),
paid app + packs (OBD Fusion), subscription for cross-platform sync (RealDash), hardware-led
(Automatic), data and fleet (Dash). The two that needed a server to function are the two that died.

The owner's Speedometer reference (App Store id6759611784) now lists as **"Odo: Speedometer,
Drive & Ride"** with convoys, friend comparison boards and **route privacy that hides trip end
points when sharing**; premium $7.99/mo, $29.99/yr, $39.99 lifetime (listing checked 2026-10-07;
prices differ from the brief's). Hiding endpoints is a pattern worth taking for Vehicles & Map.

## Styling

| App | Look | Borrow? |
|---|---|---|
| RealDash | Dark, game-quality, OEM-replica clusters, animated needles, glow; colour driven by level | **Yes**: dark-first, level-driven colour as the only state signal, tap-to-cycle centre tile, two-page cluster/console idea |
| AutoZen | Dark map, large rounded tiles, Coolwalk-style split (map + media + widgets), Space Grotesk / Inter on the site | **Yes**: split layout on wide head units, big media strip |
| OBD Fusion | iOS-native, clean lists and simple dials | Lists and settings look |
| Car Scanner | Flat but dense, ad banners | No |
| Torque / DashCommand | Skeuomorphic chrome dials, 2012-era skins | No |
| Automatic | White cards, one map per trip, cost in big type | Trip card: map thumbnail + 3 numbers |
| Odo/Speedometer | Dark full-bleed maps, speed-coloured trace, rounded dark cards, cyan accent, ranked lists | **Yes**: Trips and statistics look |

What to take: **one dark theme first** (light for the phone in daylight), a **single accent** plus
the four status colours from [ADR-0008](../../decisions/adr-0008-unified-status-vocabulary.md),
**tabular numerals** at ≥ 56 px in Drive tiles, units smaller and dimmer than the value, and no
bevels, chrome or fake glass. Colour changes only when a level changes, as RealDash does, so
colour always means something. Maps full-bleed and dark in both Drive mode and Trips.

## Copy / Avoid / Decide for Ostler

### Copy
| # | Pattern | From | Maps to |
|---|---|---|---|
| C1 | Gauge levels **normal / warning / critical** bound per vehicle, every tile property keyed to the level | RealDash | UI spec §3.5 Drive mode; app-model §4.4 `tiles` template |
| C2 | A **shared input vocabulary** so layouts are portable (RealDash targetIds) | RealDash | VSS paths, [ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md) |
| C3 | Per-signal **timeout → offline** and **readOnly** by default in any frame map | RealDash CAN XML | [ADR-0020](../../decisions/adr-0020-can-links-listen-only-by-default.md); stale styling |
| C4 | **Replay = feed the recording into the same views** (playback as a data source) | RealDash | Logbook spec PlaybackContext; Trips |
| C5 | **Two tiers**: a trip summary always (≈1 Hz, hours long) and a full recording | RealDash, OBD Fusion | [ADR-0009](../../decisions/adr-0009-session-logbook-and-location.md); [logs-at-scale](../../specs/2026-10-06-logs-at-scale-design.md) |
| C6 | Timeline mixing trips, parked periods and charges, with what changed while parked | OVMS Connect | UI spec §3.4 Logs/Trips |
| C7 | Trip card: map thumbnail, distance, time, **cost per trip**, where parked | Automatic | Trips + Maintenance & Garage add-on |
| C8 | Phone-sensor tiles that need no ECU: **inclinometer**, g-meter | DashCommand | Drive tile set; D2 off-road |
| C9 | Split Drive layout on wide screens: tiles + map + media strip | AutoZen | UI spec §3.1 layout classes HU-wide |
| C10 | Hide trip end points when sharing | Odo | [ADR-0029](../../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) sharing |

### Avoid
| # | Anti-pattern | Seen in | Why / our rule |
|---|---|---|---|
| A1 | Any feature that stops working when a vendor server goes | Automatic, Dash, RealDash licence checks | ADR-0009 local-first; add-ons use the local API |
| A2 | Selling or "partnering" driving data, insurer scores | Dash | Ghost mode default; ADR-0029, [ADR-0036](../../decisions/adr-0036-vin-and-identity-data-in-recordings.md) |
| A3 | Scaling one free-form layout across screens | RealDash `[NOSCALE]` | Author per layout class |
| A4 | Free-form pixel dashboards on the driver's screen while moving | RealDash, Torque | App-model §4.4: templates only while Moving |
| A5 | Dashboards that write to the bus through triggers | RealDash SET VALUE, actions | [ADR-0033](../../decisions/adr-0033-action-categories-and-approvals.md): layouts are Read only |
| A6 | Nagging threshold chirps with no context | Automatic | Alerts only for real warnings |
| A7 | Log-channel choice stored in app settings, not in data | RealDash | Recording profile is a file in the garage |
| A8 | Ads and ad identifiers | Car Scanner | Never |
| A9 | Paywalled cross-device sync | RealDash | Sync is ours over local links / optional Brain |

### Decide (recommendations for the owner)
1. **Drive layouts as data.** A *Drive layout* is a file: per layout class, a grid of tiles, each
   bound to a VSS path with range and normal/warning/critical levels, plus optional map and media
   panes. While Moving on the driver's head unit the shell renders it through the `tiles`
   template only; free-form RealDash-style layouts are allowed Parked/Idling, on a passenger or
   cluster screen, or under the "I'm a passenger" override. *Recommend: approve; no pixel editor in
   v1, a grid editor Parked only.*
2. **Trips = two tiers.** Every connected period yields a *Trip* (summary index at ≈1 Hz: route,
   time at speed, max speed, sprints, fuel, faults) and keeps the full recording behind it; Trips
   (the renamed Logs) lists trips first and opens recordings for analysis. *Recommend: approve,
   built on the existing logbook, no second format.*
3. **Community layouts.** Share Drive layouts and recording profiles as plain files under
   CC BY-SA ([ADR-0012](../../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md)),
   importable by file or link, with an optional catalogue repo later; no Ostler account server.
   *Recommend: approve.*
4. **RealDash CAN out.** Ship a read-only **RealDash CAN (`44`/`66`) stream and channel-XML
   export** as an Integrations add-on, so the existing RealDash dashboards and users can sit on top
   of Ostler; ignore incoming SET VALUE. *Recommend: approve as add-on, after U2.*
5. **CarPlay / Android Auto.** Do not build gauges for projection. If a companion comes, it shows
   the shell's alert card, a ≤ 6 row value list and trip status within the platform templates.
   *Recommend: defer; the head-unit PWA is the drive surface, as it became for RealDash users.*
6. **Scores and leaderboards.** No driving score in core. Trips show neutral facts (time at
   speed, hard-brake count, sprints) privately; any score or leaderboard lives only in the Social
   add-on, opt-in per friend or group, never exportable to insurers. *Recommend: approve.*
7. **Exit guarantee.** Trips offers **Export all** (CSV, GPX, VBO per ADR-0009) on one screen, and
   no feature in core depends on an Ostler-run server. *Recommend: approve as a hard rule in the
   app-model spec §8.*

## Sources (all checked 2026-10-07)

RealDash: [App Store](https://apps.apple.com/us/app/realdash/id1088758424) · [realdash.net](https://www.realdash.net/) ·
[FAQ](https://www.realdash.net/faq.php) · [gallery](https://www.realdash.net/gallery.php) ·
[RealDash-extras](https://github.com/janimm/RealDash-extras) (Unlicense) · forum threads linked inline ·
[release 2.7.1](https://forum.realdash.net/t/11288).
Others: [OBD Fusion](https://apps.apple.com/us/app/obd-fusion/id650684932) ·
[Car Scanner](https://apps.apple.com/us/app/car-scanner-elm-obd2/id1259933623) ·
[DashCommand](https://apps.apple.com/us/app/dashcommand-obd-ii-gauges/id321293183) ·
[OVMS Connect](https://apps.apple.com/app/id6747955064) · [AutoZen](https://autozenapp.com/) ·
[AutoZen on apppricinglab](https://apppricinglab.com/app/google_play/com.zenthek.autozen) ·
[Odo / Speedometer](https://apps.apple.com/us/app/id6759611784) ·
[HA torque](https://www.home-assistant.io/integrations/torque/) · Automatic and Dash press links inline.
