---
title: "Direction: what Ostler should be (standard and apps, empty OS, or a hybrid)"
area: references
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, GOALS.md, specs/2026-10-06-app-model-design.md, references/research/ha_companion_community.md, references/research/canbus_headunit.md, references/research/obd_telematics_apps.md, references/research/ovms.md]
summary: >
  Recommends option A, built the Home Assistant companion way: Ostler becomes an open
  vehicle-data standard (VSS names, one MQTT/WebSocket wire format, one Android binding),
  a node that stays the only write path, an "Ostler" service app on the phone or head unit
  that holds pairing, the gate client, driving state and safety alerts, permissive SDKs
  (Android first), and three or four first-party native apps with AppWidgets and a shared
  token pack. No launcher now; an "Ostler Home" app only if users ask. The Brain becomes
  optional (recorder, cameras, Home Assistant, decode lab). Keep the React UI as the Brain's
  console and as embedded pages for heavy screens. Drop Radio, Media, Phone and Navigation:
  Waze and Spotify already win there. Compares precedents (Signal K, Home Assistant, OVMS,
  Torque, RealDash, comma, Nova), Play policy, hardware, business and cost.
---

# Direction: what Ostler should be

## Recommendation

**Choose A, with two pieces of B kept.** Ostler should be:

1. **An open standard** for how any app gets a car's data: VSS signal names (ADR-0016), one
   network wire format (MQTT 5 and a WebSocket form, aligned with COVESA's VISS data model),
   and one **Android binding** (a bound service and a content provider) so every app on a
   phone or head unit reads the feed the same way.
2. **A reference node** (unchanged): the only path to the car's buses, behind the transmit
   gate.
3. **A reference data service**, shipped as the **Ostler app** on Android. It pairs with the
   node, holds the gate client, driving state, alerts and the alarm path, records, and
   serves the standard to other apps. It is the Android equivalent of the Home Assistant
   companion app plus the "Google Play services" of the suite: every Ostler app needs it.
   The same service runs on the optional **Brain** (Python, as today) for people who want a
   box.
4. **Permissive SDKs**, Android (Kotlin) first, then web/JS and Python; Linux and iOS later.
5. **A small suite of first-party native apps**, each with its own widgets: Diagnostics,
   Dash (gauges and widget packs), Trips, and Security once Guardian ships. Not fifteen apps.
6. **No launcher now.** Our widgets live on whatever launcher the phone or head unit already
   has. An "Ostler Home" app is built only if users ask for it, and then it is just another
   app.

**What we keep from B:** the React UI survives as (a) the Brain's web console for laptops
and desktops and (b) embedded pages inside the native apps for screens that are heavy and
already written (Diagnostics' module views, the decode lab). This is exactly how the Home
Assistant Android app works: a native shell with native widgets, sensors and notifications
around the web frontend.

**What we drop from B:** the empty OS, our own Store, our own app runtime, our own audio
focus, the dock and drawer, the OSML/CSS skin engine, and the head-unit Radio, Media,
Phone and Navigation apps. Android, Spotify, Waze and the head unit's own apps already do
those, better than one owner can.

ADR-0046 (accepted 2026-10-07) and ADR-0042's "no separate Android apps" rule would need a
superseding ADR. ADR-0042 rejected separate apps because they "cannot share one lockout,
one gate client or one sign-in"; the Ostler service app answers that: the lockout, the gate
client and the sign-in live once, in the service, and other apps bind to it.

### Recommended mission statement

> Ostler is an open way to get your car's data into the apps you already use, safely. A
> small node in the car is the only path to its buses and guards every write. The Ostler
> service, on your phone, your head unit or an optional Brain, turns that feed into one
> standard stream of VSS-named signals that any app reads the same way. We publish the
> standard and permissive SDKs, starting with Android, and build a few first-party apps,
> diagnostics, trips, gauges and security, with widgets and shared themes, that sit beside
> Waze, Spotify and Home Assistant instead of replacing them. It starts with the Land Rover
> Discovery 2, grows through community vehicle packs, works offline, and is paid for by
> hardware and an optional cloud link, never by locking up your data.

## Positioning table

| | **A: standard + service + SDKs + native apps** (recommended) | **B: web empty OS** (ADR-0046) | **C: hybrid** (web OS on the Brain, native service and widgets on Android) |
|---|---|---|---|
| **One-line pitch** | "Your car's data in any app" | "An operating system for your car" | "An OS on the Brain, a companion on the phone" |
| **D2 and classic owners** | Good: node + phone app is a complete product | Good if they fit a screen; heavy for a phone-only owner | Good, but two UIs to learn |
| **Tinkerers** | Best: an SDK and a documented feed, any language | Good: web apps, but only inside our runtime | Good |
| **Head-unit owners** | Best: our widgets beside Waze and Spotify on the stock launcher | Weak: must replace the launcher to be useful; cannot host third-party APKs | Medium: widgets yes, the OS only on the Brain's screen |
| **Phone-only users** | Best: the Play Store app they expect | Weak: one Capacitor app with an app-in-app inside | Good |
| **Fleets** | Good: standard feed, node to cloud MQTT, any fleet app | Medium | Good |
| **Hardware needed** | Node only. Service runs on the phone or head unit. Brain optional | Node + Brain for the full OS; phone is a lesser host | Node + Brain for the OS; node + phone for widgets |
| **Distribution** | Play Store per app, GitHub releases, F-Droid flavour | One app per store; our own Store inside | Both |
| **Play policy exposure** | Normal OBD-app exposure (foreground service, Bluetooth, location) | Same, plus app-in-app scrutiny and, as a launcher, QUERY_ALL_PACKAGES | Same as A |
| **Third parties** | Write ordinary Android apps against an open API; can sell them | Must write apps for our runtime only | Both, split |
| **Business** | Node hardware, cloud link, "Works with Ostler" | Same, plus Store control | Same as A |
| **Safety** | Node gate is the only write path; service owns confirm sheets; display lockouts cannot reach third-party apps | Node gate; the OS can lock every surface it draws | As A on Android |
| **Cost, one owner + agents** | Medium: Kotlin, Compose, Glance; reuse the React pages | High: an OS, Store, runtime, theme engine, plus head-unit apps | Highest: both |
| **Main loss** | ADR-0046's whole-screen control; the deep skin engine | Coexistence with real Android apps | Focus |
| **Main gain** | Coexistence, crash isolation, native audio focus, Play reach, an ecosystem others can join | One look, one lockout everywhere | Hedges the bet |

## Evidence: precedents

| Project | Shape | Who owns the data | How funded | Lesson for Ostler |
|---|---|---|---|---|
| **Signal K** (marine) | Open spec (JSON over WebSocket and REST, spec CC BY-SA, code Apache), reference servers in Node and Java, plugins and webapps installed from the server's Appstore, third-party clients such as WilhelmSK on iOS [1][2][3][4] | The standard; any server or app | Volunteer; apps sell on their own | **The closest model.** A standard plus a reference server let a paid third-party app (WilhelmSK) exist. Its Appstore lives in the server, not on the phone, and needs a restart after installs [3]. Publish the spec separately from the server. |
| **Home Assistant** | Hub plus integrations; a companion app, not a launcher. The Android app offers home-screen widgets (entity state, action, media player, template) [5][6], device sensors that are mostly off by default and update every 15 minutes [7], a minimal flavour with no Google services on GitHub and F-Droid [8], and Android Auto and AAOS screens in the IoT category [9][10] | The hub | Nabu Casa cloud subscription, hardware, foundation (see [ha_companion_community](ha_companion_community.md)) | **Copy the companion pattern exactly**: native widgets, sensors, notifications and car screens around a web frontend. HA never built a launcher. Widgets update every 30 minutes by default and need extra grants for real time [5]. |
| **OVMS** | Open module (about USD 99, ESP32, CAN, modem, GPS), open firmware, MQTT, OVMS Connect app, free public servers or your own broker; describes itself as a hobbyist project [11][12] | The module and the user's broker | Hardware sales, cheap paid app | Proves node + MQTT + apps works for a niche. Also its limit: one official app and no SDK for others. See [ovms](ovms.md). |
| **Torque Pro** | Paid app that owns the adapter and the data; plugins bind to it through an AIDL service (`ITorqueService`) [13]; brand plugins extend PIDs and do not run alone [14]; an Android Auto front end needs Torque Pro installed [15] | The app | One-off sale | An app-owned data service with an AIDL plugin API created a small plugin ecosystem. Ostler's Android binding is the same idea, but open and documented. |
| **RealDash** | App that owns the data; free to try, full-version purchase and an optional My RealDash subscription; custom hardware via its own open CAN protocol [16] | The app | Purchase plus subscription | Users pay for good dashboards; an open input protocol lets DIY hardware in. Ostler should feed RealDash, not fight it (RealDash CAN out is already an integration). See [obd_telematics_apps](obd_telematics_apps.md). |
| **comma / openpilot** | Hardware (comma four, USD 999, from November 2025) plus open software; optional comma prime (about USD 24 a month) for data, storage and remote access [17][18] | The device and comma's cloud | Hardware and subscription | Open software sells hardware. The paid service is convenience, never the driving feature. Matches ADR-0013. |
| **Eclipse KUKSA** | VSS databroker (gRPC), an Android SDK and a demo companion app on F-Droid [19] | The broker | Industry consortium | A VSS server plus an Android SDK already exists; reuse ideas and stay compatible where cheap. Do not invent a new signal model. |
| **Waze, Spotify on head units** | Ordinary Android apps on aftermarket head units, beside the vendor launcher | Each app | Their own | Users expect these. A web app-in-app cannot host them (the chat's "third-party app wall"). Any plan must coexist with them. |
| **AOSP launcher market** | Nova, one of the most popular launchers, was bought in 2022, then lost its staff, then its founder in September 2025; development stopped and open-sourcing was cancelled [20]. Car launchers (AGAMA, FCC) are small one-person products; Nova is often used on head units because it hosts any widget [21][22] | The user | Mostly one-off sales | A launcher is a maintenance burden with little money in it. Widgets work on any launcher. Don't make the launcher the product. |

## Evidence: the questions

### Hardware: is the Brain still needed?

No, not for the core product. ADR-0032 already says the node alone, with a phone, is a
complete product offline, and that the phone may mint gate grants that the node verifies.
Under A, the data service runs:

- **on a phone**, linked to the node by BLE (or the node's Wi-Fi AP), as ADR-0032 already
  plans;
- **on an Android head unit**, linked by USB (power and data, no Wi-Fi conflict with a
  phone hotspot), with Wi-Fi as a fallback. Android has no stock USB-NCM support on most
  devices, so the Android USB link is likely a CDC serial framing of the same MQTT messages.
  ADR-0039 named USB-NCM as the product link and kept serial dev-only, so this needs a
  decision (Open question 6);
- **on the Brain**, for people who want an always-on box: the long recorder, cameras, Home
  Assistant, many nodes, the decode lab and the web console.

The node keeps the parked broker and recording when the head unit is off (ADR-0040), so
losing the head unit's power at ACC off loses nothing important.

### Distribution and Play policy

- OBD apps are ordinary on Play (Torque, Car Scanner, OBD Fusion, RealDash). There is no
  OBD-specific ban.
- A service app that keeps a link to the node must declare a **foreground service type**
  (here `connectedDevice`) in the manifest and in Play Console, with a description, the user
  impact if deferred and a demo video [23].
- Trip logging in the background needs the background-location declaration. A vehicle
  alarm wanting full-screen alerts meets Play's limits on full-screen intents [23]; plan
  heads-up notifications and the phone alarm path instead.
- A **launcher** meets extra friction: QUERY_ALL_PACKAGES is allowed only when broad app
  visibility is core [24], and launchers are named as not being accessibility tools [25].
  Apps without a launcher avoid both.
- **Developer verification:** from 30 September 2026 apps on certified devices in Brazil,
  Indonesia, Singapore and Thailand must come from registered, verified developers, even
  when sideloaded (ADB and an "advanced flow" excepted), and Google plans the same worldwide
  in 2027 [26][27]. So register as a verified developer whatever the store. F-Droid's
  re-signing model is under strain from this [28]; ship a GitHub-release flavour too, as HA
  does [8].
- Android Auto: only a few categories, including IoT, are allowed, with narrow templates
  [10]. HA's car screens are the pattern: alerts, a few actions, no live gauges.

### Openness and community

A works like Signal K and HA: third parties build normal Android apps against a public API,
can sell them, and need nothing from us but the SDK. The SDK must be permissively licensed
so closed apps can use it; the platform stays AGPL. B forces third parties into our runtime
and our Store, which no head-unit or phone developer is used to, and the phone app may not
download code anyway (app-model §7.1). Day-one value matters: bridges (Home Assistant MQTT
discovery, RealDash CAN, Torque-style broadcast) let existing apps show Ostler data before
anyone writes against the SDK.

### Business (ADR-0013)

Unchanged in kind, easier in practice: node hardware sales (OVMS, comma), an optional paid
cloud link for remote access and backup (Nabu Casa, comma prime), and the Ostler-run hub.
A Play Store presence is the best shop window for the hardware. A "Works with Ostler"
programme for third-party apps and adapters is possible later (HA charges partners). B's
Store control adds little revenue and a lot of policy risk.

### Safety

The node gate stays the only write path. Under A:

- Third-party apps read through the standard. **Writes are requests** to the Ostler
  service, which shows its own confirm sheet (not the caller's), mints the grant, and the
  node decides. A malicious app can ask; it cannot act.
- Driving state, telltales and alarm alerts live in the Ostler service (notifications,
  a warnings widget), so "safety is never an app" (ADR-0046 §2) maps to "safety is in the
  one required app".
- **Loss:** we cannot lock another app's screen while Moving. B could lock every surface
  it drew, but only its own; it could not lock Waze either. The real guard is the node.

### Cost and time for one owner with agents

- A: one Kotlin service with a versioned AIDL interface, one SDK, three or four Compose
  apps with Glance widgets, embedded React pages for the heavy screens. The protocol
  already exists (MQTT topics, VSS). Months, not years.
- B: an OS shell, Store, app runtime, permission system, theme engine with XML layouts,
  plus Radio, Audio, Media, Phone, Camera and Navigation apps. The launcher spec, Store spec
  and head-unit apps spec alone are each a product. Years, and it competes with Android.
- C: both.

### The launcher

**Stance: apps and widgets first; no launcher now.** Reasons: the stock head-unit launcher
already hosts widgets and often ties into the unit's own radio, settings and CAN box
([canbus_headunit](canbus_headunit.md)); third-party car launchers exist and host widgets
[21][22]; launchers carry Play friction [24][25] and upkeep (Nova [20]). Revisit if users
ask. If built, "Ostler Home" is one more app in the suite, an AppWidgetHost with a car
layout, never the place where features live.

### Theming without a web OS

- **A shared token pack:** one design-token file (colours per mode, type, shape, gauge
  faces) compiled by the SDK into a Compose theme. Every Ostler app applies it.
- **One active theme across apps:** the Ostler service exposes the chosen theme, so
  switching it in one place restyles every Ostler app and widget.
- **Material You:** on Android 12+ phones that support dynamic colour, offer "follow
  system colours" [29]; many head units lack it, so the token pack is the default.
- **Widget packs as AppWidgets:** gauge faces and layouts ship as widget styles inside Dash.
  Widgets are RemoteViews, so custom gauges are drawn as bitmaps or simple layouts, and full
  updates are costly [30]; keep widgets to slow-changing values and use the Dash app in
  split screen for fast gauges.
- **Safety colours fixed** in the token pack, as now.
- The theme-engine spec's OSML layouts and free-form CSS stay only for the embedded web
  pages and the Brain console, or are parked.

## What is lost and what is gained

**Lost:** ADR-0046's single, fully themed screen; a Store we control; screen lockouts over
third-party apps; the iOS story for now (iOS cannot run a background service the same way);
the plan to replace the head unit's media; a big share of the 2026-10-07 specs.

**Gained:** coexistence with Waze, Spotify and Home Assistant; native audio focus and
MediaSession for free; crash isolation per app; Play Store reach; a feed others can build on;
a smaller job for one owner; the Brain made truly optional.

## Top risks of the recommended option

1. **Head units kill or freeze background services** (sleep at ACC off, aggressive task
   killers). Mitigation: the node records while parked; the service reconnects on boot and
   on USB attach; test on a cheap head unit first.
2. **Play policy friction:** foreground-service declarations, background location,
   full-screen intent limits, and worldwide developer verification in 2027 [23][26].
   Mitigation: declare early, keep a GitHub-release flavour, register as verified.
3. **Nobody builds against the standard.** Torque's plugins stayed small; Signal K took
   years. Mitigation: bridges to HA, RealDash and MQTT from day one; first-party apps are
   real users of the SDK.
4. **Version skew between the service and many apps.** Mitigation: few apps, a versioned
   AIDL interface with capability flags, one release train.
5. **Display safety cannot be enforced on other apps.** Mitigation: the node gate decides
   every write; Moving rules in the SDK; a "Works with Ostler" check later.
6. **AppWidget limits** make live gauges on the home screen poor [30]. Mitigation: widgets
   for state, the Dash app for live gauges.
7. **Re-plan churn:** ADR-0046 was approved one day ago. Mitigation: one superseding ADR
   that says what stays (VSS, the node, packs, the gate, accounts, recorder) and what goes.

## Open questions for the owner

1. **Supersede ADR-0046 and ADR-0042's "one app" rule with a new ADR for option A?**
   Recommended: yes, in one ADR, listing what is kept.
2. **What is the standard called and what is in it?** Recommended: "Ostler Vehicle API", a
   profile of VSS with the existing MQTT 5 topics, a WebSocket form aligned with VISS, and
   an Android binding; published as its own spec repo under a share-alike licence, with
   permissive SDKs.
3. **Which first-party apps first?** Recommended: Ostler (service, pairing, settings,
   alerts), Diagnostics, Dash; Trips next; Security when Guardian ships.
4. **Do Radio, Audio, Media, Phone, Camera and Navigation stay?** Recommended: no. Restore
   the GOALS non-goal; feed Waze, Spotify and the head unit's apps instead.
5. **Is the Brain still a product?** Recommended: yes, optional, for the recorder, cameras,
   Home Assistant and the decode lab; not needed for v1.
6. **Head-unit link to the node?** Recommended: USB first (a serial framing of the same
   messages, since Android lacks USB-NCM on most units), BLE for phones, Wi-Fi AP as
   fallback; amend ADR-0039 for this one local link.
7. **Build a launcher?** Recommended: no; revisit when users ask, as an "Ostler Home" app.
8. **Keep the theme-engine spec?** Recommended: park it; write a short spec for the token
   pack, the shared active theme and widget styles.
9. **Can third-party apps request writes?** Recommended: yes, only as requests that the
   Ostler service confirms in its own UI and the node gate decides; Tier 4 never.
10. **Keep the React UI?** Recommended: yes, as the Brain console and as embedded pages for
    Diagnostics and the decode lab; no new web-shell work.

## Sources

1. Signal K specification: https://signalk.org/specification/1.7.0/doc/
2. Signal K server: https://github.com/SignalK/signalk-server
3. Signal K server configuration and Appstore: https://unpkg.com/signalk-server@2.13.5/docs/built/setup/configuration.html
4. WilhelmSK server setup: https://github.com/sbender9/wilhelmsk-node-server-setup
5. HA Android widgets: https://companion.home-assistant.io/docs/integrations/android-widgets
6. HA Android gallery: https://companion.home-assistant.io/docs/gallery/android
7. HA sensors: https://companion.home-assistant.io/docs/core/sensors
8. HA Android flavours: https://companion.home-assistant.io/docs/core/android-flavors
9. HA Android Auto: https://companion.home-assistant.io/docs/android-auto/
10. Android for Cars, other app types: https://developer.android.com/design/ui/cars/guides/app-types/other-apps
11. OVMS introduction: https://docs.openvehicles.com/en/latest/introduction.html
12. OVMS Connect: https://apps.apple.com/app/id6747955064
13. Torque plugin AIDL thread: https://www.b4x.com/android/forum/threads/nearly-empty-xml-when-creating-lib-from-aidl-file.44471/latest
14. MUT for Torque plugin listing: https://apkcombo.com/mut-for-torque-v2/com.xkaixrezza.mutiiv2/
15. AA Torque: https://github.com/agronick/aa-torque
16. RealDash listing: https://apps.apple.com/us/app/-/id1088758424
17. comma four: https://blog.comma.ai/comma-four/
18. openpilot: https://en.wikipedia.org/wiki/Openpilot
19. KUKSA Companion App: https://f-droid.org/packages/org.eclipse.kuksa.companion/
20. Nova Launcher shutting down: https://9to5google.com/2025/09/08/nova-launcher-shutting-down/
21. Head-unit launchers: https://android-headunits.com/android-head-unit-launcher/
22. Head-unit widgets: https://android-headunits.com/desktop-wallpaper-and-widgets/
23. Play foreground service and full-screen intent requirements: https://support.google.com/googleplay/android-developer/answer/13392821
24. Play QUERY_ALL_PACKAGES policy: https://support.google.com/googleplay/android-developer/answer/10158779
25. Play Accessibility API policy: https://support.google.com/googleplay/android-developer/answer/10964491
26. Android developer verification guide: https://developer.android.com/developer-verification/guides
27. Developer verification timeline: https://support.google.com/android-developer-console/answer/16650243
28. F-Droid 2.0 and developer verification (secondary): https://pinggy.io/blog/f_droid_2_0_android_developer_verification/
29. Material You on more devices: https://android-developers.googleblog.com/2022/02/material-you-coming-to-more-android.html
30. Advanced widgets (updates): https://developer.android.com/develop/ui/views/appwidgets/advanced

Repo context: [ADR-0046](../../decisions/adr-0046-empty-os-every-app-an-add-on.md),
[ADR-0042](../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md),
[ADR-0013](../../decisions/adr-0013-repo-split-and-vehicle-pack-contract.md),
[ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md),
[ADR-0039](../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md),
[ADR-0044](../../decisions/adr-0044-adapters-on-the-brain-without-a-node.md),
[GOALS](../../GOALS.md), [app model](../../specs/2026-10-06-app-model-design.md).
