---
title: "The Android head-unit ecosystem today — car launchers, gauge apps, vendor stacks, owner complaints, and where Ostler fits"
area: references
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-head-unit-apps-design.md, references/research/canbus_headunit.md, references/research/obd_telematics_apps.md, references/research/ui/obd_apps.md, references/research/ui/head_unit_ui.md]
summary: >
  Recommendation: don't build a launcher now. Car launchers are a crowded, cheap, mature market (AGAMA 5m+ installs, CarWebGuru 1m+, Car Launcher Pro, FCC, vendor launchers such as the DUDU one, an open-source OpenLauncher), and owners pick their own. What nobody offers is an open, local, multi-vehicle decode with a gated write path, served to any app the same way. Build that as one Ostler vehicle-feed service on Android (a bound service plus a snapshot provider, VSS names, permissioned), with native apps and AppWidgets that work in any launcher. Torque's plugin interface is the precedent: it grew an ecosystem of widgets and Android Auto front ends. Interoperate outward: RealDash (its public CAN-over-TCP protocol plus one published channel file), Home Assistant over MQTT, the Raise CAN-box path, and Torque as an input. Reconsider a thin launcher only if widgets prove too slow or apps die on sleep.
---

# The Android head-unit ecosystem today, and where Ostler fits

**Question.** What does the Android head-unit world look like in October 2026, where does
Ostler fit, and does Ostler need its own launcher? This note feeds the direction round that
followed [ADR-0046](../../decisions/adr-0046-empty-os-every-app-an-add-on.md) and the owner's
"perhaps just apps, each with its own widgets". It builds on
[canbus_headunit.md](canbus_headunit.md) (CAN boxes, FYT internals),
[obd_telematics_apps.md](obd_telematics_apps.md) (RealDash deep dive) and
[ui/obd_apps.md](ui/obd_apps.md) (diagnostic UI); it does not repeat them.

Store figures were read from the UK Google Play listings on 2026-10-08. **(U)** marks a claim
I could not verify from a primary source.

## Recommendation

1. **No Ostler launcher for now.** Ship native apps that each publish AppWidgets and work
   inside whatever launcher the owner already uses (vendor stock, AGAMA, CarWebGuru, FCC,
   Car Launcher Pro, Lawnchair). The launcher market is crowded, cheap (one-off £0–14) and
   personal. Vendor launchers also carry the CAN-box screens, the radio and the car settings,
   which we cannot replace on a closed unit. A launcher would cost a lot and add little that
   is ours.
2. **Make the standard the product.** Build one **Ostler vehicle-feed service** on Android
   that owns the link to the node (or adapter). Every app, ours or anyone's, reads the car
   from it the same way on a head unit or a phone:
   - a **bound service** (an AIDL interface) for live subscriptions to VSS paths
     ([ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md));
   - a **content provider** for snapshots, so widgets can read the latest values cheaply;
   - an optional **LAN socket** (MQTT or WebSocket) for non-Android clients;
   - **Android permissions** mapped to Ostler data classes. Writes go only through the
     approval path of [ADR-0033](../../decisions/adr-0033-action-categories-and-approvals.md),
     never through a plain call.

   Torque's plugin interface proves the shape works: one service, many small apps on top
   (see [Torque Pro](#torque-pro-the-precedent-for-a-feed-standard)).
3. **Interoperate outward rather than compete on gauges.** In order of value for effort:
   - **RealDash output:** speak its public CAN protocol over TCP and publish one channel file
     that maps Ostler signals;
   - **Home Assistant:** MQTT discovery from the Brain or the phone;
   - **CAN-box emulation:** the Raise path already planned in
     [canbus_headunit.md](canbus_headunit.md), which puts data on the head unit's own screens;
   - **Torque as an input** for generic OBD cars when no node is present.
4. **Keep the theme engine, but aim it at our own apps and widgets.** Themes are data packs
   shared through a gallery, as RealDash dashboards and Torque theme zips are. We cannot skin
   other people's launchers, and should not try.
5. **Re-open the launcher question only on evidence.** Two triggers would justify a thin
   launcher, ideally a contribution to or fork of an open one rather than a new one:
   - widgets in third-party hosts are too slow or freeze after sleep on test units;
   - the feed service is killed on sleep and only the home app survives.

## Evidence

### 1. The hardware and vendor landscape

- **Platforms.** Most aftermarket units are built on a few platforms. **FYT** (Unisoc UIS7862
  and UIS8581, sold as Joying, Mekede, Teyes, Atoto, Junsun, Navifly and more) is the most
  modded. Others are Microntek (MTCx), Rockchip PX5 and PX6, MTK 8227L and Allwinner. The
  brand list comes from
  [FytHWOneKey](https://github.com/hvdwolf/FytHWOneKey) and the platform list from the
  [FCC launcher listing](https://apkcombo.com/fcc-car-launcher/ru.speedfire.flycontrolcenter/).
- **Vendor OSes.** The higher end now ships a skinned vendor OS with its own launcher. Mekede
  and DUDUAUTO ship **DuduOS** with a "DUDU launcher", multi-desktop layouts, split screen and
  OTA updates (from the owner's shared chat; vendor claims, **(U)**). DuduOS is tied to newer
  DUDU hardware: an owner notes the older Mekede M7 "does not have the latest OS"
  ([T6 forum](https://t6forum.com/threads/mekede-dudu7-12-512gb-for-vw-transporter-2020-headunit-chat.55921)).
  I found no source showing that the DUDU launcher runs on other units. Dasaita's **Vivid**
  ships both as an APK launcher and as a ROM layer that cannot be uninstalled
  ([android-headunits.com](https://android-headunits.com/what-is-vivid-os/)).
- **Full Android with the Play Store** is now normal. A DUDU7 owner confirms
  "100% native Android 13 with store"
  ([T6 forum](https://t6forum.com/threads/mekede-dudu7-12-512gb-for-vw-transporter-2020-headunit-chat.55921)).
  So native APKs, AppWidgets and multi-window all work on these units. That is the premise of
  the shift away from a web app-within-an-app.

### 2. Car launchers

| Launcher | Install base · rating · last update | Widgets | Theming | Price | Data plugins |
|---|---|---|---|---|---|
| **AGAMA** (altercars) | 5m+ · 4.4★ (46.9k) · 17 Sept 2026 [AG1] | Own widgets only: GPS speedo, music, navigator, compass, weather, an auto-switching centre widget [AG2] | "Light" and "Expert" colour modes, car logos, day/night by sunrise [AG2]; **no theme sharing** (a reviewer asks for it [AG1]) | 30-day trial, then a one-off licence [AG1] | None; reads music and navigation from Android notifications [AG2] |
| **CarWebGuru** (SoftArt) | 1m+ · 3.0★ (9.16k) · 16 Jul 2026 [CW1] | Own widgets **plus system (Android) widgets** [CW1] | Many themes, import and export of desktops, car image, split screen [CW1] | In-app purchases | None found |
| **Car Launcher Pro** (Apps LabDev) | 100k+ · 4.4★ (44k) · 3 Sept 2026 [CL1] | Trip computer, speed, map, music; some Android widgets "don't appear" [CL1] | Themes are extra purchases on top of Pro [CL1] | **£13.99** paid [CL1] | None |
| **FCC Car Launcher** | (U) | Built "around widget concept": player, OBD2 widget, minimap, TPMS via plugin [FC1] | Fully configurable; skins on XDA [FC1] | Free plus premium | OBD2 widget and TPMS plugin; source not documented [FC1] |
| **Vivid** (Dasaita, XDA) | (U) | Landscape-first, split screen [VV1] | Day/night by time zone [VV1] | Bundled | None found |
| **DUDU launcher** (DuduOS) | Bundled with DUDU units | Multi-desktop, PiP (vendor claims, **(U)**) | Themes switched by headlights, time or GPS (**(U)**) | Bundled | Vendor CAN box only (**(U)**) |
| **FYT stock launchers** | Bundled | Vendor car-info, radio and CAN-box widgets | Vendor themes | Bundled | `com.syu.ms` / `com.syu.canbus`, undocumented, root to hook ([canbus_headunit.md](canbus_headunit.md)) |
| **OpenLauncher** (dw2lam) | GitHub, 170★, v0.0.5 [OL1] | Drag-and-drop grid: music, FM radio (direct tuner control on szchoiceway units), speedo, trip, vitals, compass [OL1] | Day/night modes, accents; a "universal theming engine" on the roadmap [OL1] | Free, permissive licence | None yet |
| **Nova / Lawnchair** (general launchers) | Nova stopped in Sept 2025 [NV1]; Lawnchair 15 still beta in 2026 [LC1] | Full AppWidgetHost | Icon packs | Free | None |

**What this says.**
- The market is mature, actively updated and cheap. Two closed launchers
  (AGAMA, CarWebGuru) have over 6 million installs between them.
- **No launcher has a vehicle-data plugin standard.** Data comes from GPS, from Android
  notifications and media sessions, or from the vendor's own CAN box.
- Theme sharing is weak everywhere: no gallery, extra paid themes, users asking to share.
- An open-source car launcher already exists (OpenLauncher, permissive licence, young). If we
  ever need a launcher, contributing a feed-aware widget to it beats starting another.
- General launchers on head units are fragile: Nova's developer stopped work in September
  2025 [NV1].

### 3. OBD and gauge apps

The UI and business side is covered in [obd_telematics_apps.md](obd_telematics_apps.md). This
section looks only at how each app exposes data to other apps and how gauges are themed.

| App | Install base · rating · last update | Data out to other apps | Gauge theming and sharing |
|---|---|---|---|
| **Torque Pro** | 1m+ · 3.4★ (81.3k) · **3 Feb 2025** · £2.95 [TQ1] | **Plugin AIDL** (`org.prowl.torque.remote.ITorqueService`) [TQ2][TQ3]; broadcast intents (`ALARM_TRIGGERED`, OBD connected or disconnected, `REQUEST_TORQUE_QUIT`) usable from Tasker [TQ2]; HTTP upload to any URL ([obd_telematics_apps.md](obd_telematics_apps.md)) | Theme zips of PNG dial faces in `.torque/themeDir`, or the in-app theme server [TQ4] |
| **RealDash** | Active (v2.7.1, Sep 2026, per [obd_telematics_apps.md](obd_telematics_apps.md)) | Data Multicast between RealDash instances; CSV logs; no general Android API found | Dashboard editor; **Community Dashboards** gallery; paid dashboards ([obd_telematics_apps.md](obd_telematics_apps.md)) |
| **Car Scanner** | 10m+ · 4.7★ (364k) · 20 Jul 2026 [CS1] | None found for live data to other apps (U) | Dashboard builder, HUD mode |
| **OBD Fusion** | Active (Jul 2026) | CSV, dashboard import and export | Paid per-make packs |
| **DashCommand** | Stale (2023) | Skin files | DashXL editor on Windows |

**RealDash inputs (the one we can feed today).** RealDash reads CAN data through its public
**RealDash CAN** protocol: frame tag `44 33 22 11`, a 32-bit little-endian id and 8 data
bytes; the `66` frame carries larger payloads with a CRC
([protocol](https://github.com/janimm/RealDash-extras/blob/master/RealDash-CAN/realdash-can-protocol.md)).
It runs over serial, Bluetooth or TCP, and an XML channel file says what the bytes mean.
Adapters such as WiCAN speak it natively ([canbus_headunit.md](canbus_headunit.md)).

**The decode gap, in one forum post.** On 2026-08-29 a RealDash user posted a **paid bounty**
for someone to write a channel file for a 2007 Chrysler Pacifica (turn signals, gear and
other body data) because "standard OBD2 … does not natively transmit" them
([RealDash forum 11113](https://forum.realdash.net/t/11113)). Every gauge app has the same
gap: per-make decode is a paid pack (OBD Fusion), a paid plugin (Torque) or a hand-written
file (RealDash). Nobody shares one open decode across apps.

### Torque Pro: the precedent for a feed standard

- Torque exposes a bound service through an AIDL file. Plugins are separate APKs that bind to
  it and read PID values ([Torque wiki](https://wiki.torque-bhp.com/view/PluginDocumentation);
  [B4X thread](https://www.b4x.com/android/forum/threads/nearly-empty-xml-when-creating-lib-from-aidl-file.44471/latest)).
- A small ecosystem grew on it:
  - **Widgets for Torque** puts Torque dials on any home screen. Its listing warns that some
    launchers update the widget slowly ([listing](https://www.bluestacks.com/campaign/org.prowl.torquewidget/en)).
  - **aa-torque** is an Android Auto dashboard built only on Torque's data, with about 500
    GitHub stars ([gittrend](https://gittrend.io/repo/agronick/aa-torque)).
  - Others include TorqueScan, shift lights, and Home Assistant's (now legacy) Torque sensor.
- **Why it stalled.** It is closed and has no versioned public spec, so the AIDL is passed
  around in forum threads. It speaks OBD PIDs, not a vehicle model. It has had **no update
  since February 2025** [TQ1]. Reviewers complain that it "refuses to quit" and fights other
  apps for the adapter [TQ1].
- **Lesson for Ostler.** The bound-service pattern is right, and the ecosystem will come if
  the interface is easy. Ostler should do the same thing openly: a published, versioned AIDL
  with VSS paths, permissions and data classes, plus a client library. It must also share
  the adapter politely instead of grabbing it.

### 4. What owners complain about

From store reviews, forums and installer guides. Reddit and 4PDA did not return usable
results through search or their APIs in this session, so their themes are **(U)**.

- **Apps and widgets break after sleep.**
  - Media apps lose album art and controls after the unit sleeps; one owner suspects USB
    storage detaches during sleep
    ([Poweramp forum](https://forum.powerampapp.com/topic/24417-no-album-art-track-progress-lost-after-returning-from-sleep-android-car-head-unit)).
  - Installers advise switching "sleep" to "power off after ACC off" to fix projection
    ([CJ Industries](https://cj-industries-help.groovehq.com/help/needing-to-restart-unit-to-use-carplay-slash-android-auto)).
  - A generic Android widget can stop updating after the device sleeps
    ([B4X](https://b4x.com/android/forum/threads/how-to-keep-a-widget-alive-always.167391)).
- **Slow boot.**
  - Cold boot takes 10–15 s on fast units and over 45 s on slow quad-cores.
  - Fast resume works only if the unit sleeps rather than powers off, and on some units only
    for about 3 minutes
    ([android-headunits.com](https://android-headunits.com/android-headunit-boot-time/)).
- **Launcher bugs and paywalls.**
  - CarWebGuru: an update broke music playback until the app was set up again [CW1].
  - CarWebGuru's own listing warns that on MTK 8227L units "there are problems with
    interception of audio focus" [CW1].
  - Car Launcher Pro is "buggy when running apps in split screen mode, often kicking them to
    the background" [CL1].
  - AGAMA's brightness control works only on its own screen, and its music integration is
    "hit and miss" [AG1].
- **CAN data gaps.** A DUDU7 owner reports the CAN integration was "instant", but later
  lights and indicators did not work, parking distances did not show and night mode did not
  switch with the lights
  ([T6 forum](https://t6forum.com/threads/mekede-dudu7-12-512gb-for-vw-transporter-2020-headunit-chat.55921)).
  The CAN box decodes what its firmware knows, and nothing more.
- **Gauge apps.** Torque fights other apps for the adapter, and cheap ELM clones fail
  [TQ1]. Body signals cost money or a bounty ([RealDash forum 11113](https://forum.realdash.net/t/11113)).

### 5. What the vendor stack exposes, and whether apps can read it

- **The CAN box → MCU → Android path.** It is detailed in
  [canbus_headunit.md](canbus_headunit.md). The CAN box (Raise, Hiworld, Simple Soft and
  others) sends speed, doors, reverse, lights, climate, radar and steering-wheel keys over a
  38400-baud UART to the MCU. The vendor's canbus app draws its own screens from that data.
- **Third-party access is closed.**
  - FYT's `com.syu.ms` and `com.syu.canbus` services are undocumented, and hooking them needs
    root plus LSPosed ([canbus_headunit.md](canbus_headunit.md)).
  - **ACC broadcasts are system-only from Android 8.** FytHWOneKey states that "Acc On does
    certainly not work on Android 8.x and higher" for apps without the system signature
    ([FytHWOneKey](https://github.com/hvdwolf/FytHWOneKey)).
  - So a normal app cannot reliably learn ignition state from the head unit. Ostler's node
    already knows it, which is another reason the feed should come from the node and not the
    head unit.
- **Steering-wheel learning** lives in the vendor settings. Apps receive standard media keys,
  so an app that exposes a proper `MediaSession` gets steering-wheel control for free.
- **The reverse trigger** is handled by the MCU on its own fast camera path, and should stay
  there ([canbus_headunit.md](canbus_headunit.md)).
- **Google's car data APIs** do not help on aftermarket units. The Car App Library's
  `CarHardwareManager` gives speed, mileage and energy level only inside Android Auto or
  Android Automotive
  ([Android developers](https://developer.android.com/training/cars/apps/library/car-hardware-api)).
  A head unit running plain Android has no equivalent. **That empty slot is where the Ostler
  feed fits.**
- **Home Assistant's companion app** now offers more Android Auto sensors, such as speed and
  remaining range ([HA blog, July 2025](https://home-assistant.io/blog/2025/07/23/companion-app-for-android)).
  These come from Android Auto, not from the car's buses.

### 6. Android constraints on the apps-plus-widgets shape

- **AppWidgets are not gauges.** A `RemoteViews` widget has a 30-minute minimum for scheduled
  updates. Faster updates must be pushed by the app
  ([Android developers](https://developer.android.com/guide/topics/appwidgets/advanced);
  [AOSP commit](https://android.googlesource.com/platform/frameworks/base/+/851da84%5E%21/)).
  Some hosts render pushed updates slowly (the Widgets for Torque warning).
  - **Design rule:** widgets show glanceable state (temperatures, faults, fuel, trip), pushed
    on change and rate-limited to about 1 Hz.
  - Live gauges belong in a full-screen or split-screen app.
- **Starting at boot.** Apps targeting Android 15 may not start `dataSync`, `mediaPlayback`,
  `camera`, `microphone`, `phoneCall` or `mediaProjection` foreground services from
  `BOOT_COMPLETED`. A `dataSync` service is also capped at 6 hours a day
  ([Android 15 changes](https://developer.android.com/about/versions/15/changes/foreground-service-types)).
  The feed service should therefore use the **`connectedDevice`** type, which is allowed at
  boot. To verify on target units: (U).
- **Sleep kills.** Vendor firmware is known to kill background apps on ACC off (forum
  pattern; FYT key names **(U)**). The home app is the last process the system kills. **This
  is the strongest argument for a launcher.** We should test it before accepting it.
- **Multi-window** is standard from Android 12L. A split-screen "gauges plus navigation" pair
  needs no launcher of ours: owners already pair apps in vendor launchers and in CarWebGuru
  [CW1].

### 7. How themes and dashboards are shared: precedents

- **RealDash.** Dashboards are made in an in-app editor and uploaded to a Community
  Dashboards gallery. Paid dashboards cost $1.99–5.99. Channel files are separate XML, so a
  dashboard only works with a matching channel file ("the vocabulary problem"). Details in
  [obd_telematics_apps.md](obd_telematics_apps.md).
- **Torque.** A theme is a zip of PNG dial faces and needles copied into `.torque/themeDir`,
  or installed from an in-app theme server. Owners swap day and night themes with Tasker
  [TQ4].
- **Launchers.** Sharing is weak. AGAMA has no sharing (users ask for it), Car Launcher Pro
  sells themes one by one, and FCC skins circulate on XDA [AG1][CL1][FC1].
- **What to copy:**
  1. A theme is **data only**: tokens, images and fonts, never code.
  2. Themes are shared in a gallery with previews.
  3. Day and night variants live in the same pack.
  4. Dashboards bind to **VSS paths**, not to adapter-specific channels. Any Ostler dashboard
     then works on any car whose pack provides the signals. RealDash cannot do this.

## Where Ostler adds value that these don't

| Ostler offers | Nearest existing thing | Gap it fills |
|---|---|---|
| **Open, local decode** in vehicle packs, with signals shared as data | RealDash XML files, Torque per-make plugins, OBD Fusion packs | Decode is closed, paid or a bounty, and each file works in one app only |
| **Multi-vehicle and multi-protocol** (K-line D2, CAN, OBD-II) behind one model | Each gauge app re-implements its own adapters | One feed for every app and every car |
| **A gated write path** (approvals, action categories) | Car Scanner and OBDeleven coding, Torque PID writes; all ungated | Safe actuation that others can call without bypassing it |
| **A shared standard** (VSS names, a versioned AIDL, MQTT topics) | Torque's closed AIDL; AA and AAOS `CarHardwareManager` (not on aftermarket units) | The empty slot for vehicle data on plain Android |
| **Ignition and sleep state from the node** | Vendor ACC broadcasts (system apps only) | Apps can start and stop with the car |
| **Owner-held recordings and trips** | RealDash's paid cloud; Torque's HTTP upload | Local by default, shareable on the owner's terms |

## Launcher, or apps plus widgets?

| | Apps + widgets in any launcher | Own launcher |
|---|---|---|
| Fits what owners already run | **Yes**: keeps their vendor launcher, CAN-box screens and settings | Replaces a launcher they chose or paid for |
| Cost to build and maintain | Low: widgets plus one feed service | High: home role, drawer, widget host, icon packs, store policy, old WebViews (ADR-0048 risks) |
| Live gauges | In an app, full screen or split | Same; a launcher does not change this |
| Survives sleep | Depends on vendor firmware **(test)** | Home app usually survives |
| Theming | Our apps and widgets only | The whole home screen |
| Phones | Same apps and widgets, unchanged | Few people replace their phone launcher for a car app |

**Verdict.** Apps plus widgets are enough for v1. The one real advantage of a launcher,
surviving sleep, is a firmware question. Answer it with a test on two units before building
anything.

## Who to interoperate with

1. **RealDash (output, first).** Emit RealDash CAN `44` frames over TCP from the Brain or
   the phone feed, using synthetic ids that carry decoded values. Publish one Ostler channel
   file. Every RealDash dashboard then gets D2 data with no change to RealDash. Low effort,
   and it reaches the community that pays bounties for decode.
2. **Home Assistant (output).** Use MQTT discovery, following [mqtt_topic_practice.md](mqtt_topic_practice.md). That puts the car in the owner's home dashboards and automations.
3. **CAN-box emulation (output to the head unit's own screens).** This is already the
   planned Raise path ([canbus_headunit.md](canbus_headunit.md)).
4. **Torque (input, for generic OBD cars).** Bind to Torque's service as a source adapter
   when an owner has Torque and no node. As a further option, accept Torque's HTTP upload on
   the Brain. **Do not** emulate an ELM327 to feed Torque: it costs a lot and Torque is
   stale.
5. **Launchers (no integration needed).** Our AppWidgets appear in AGAMA's and CarWebGuru's
   widget pickers and in vendor launchers. Test that list on real units.
6. **OpenLauncher (optional, later).** If a launcher is ever wanted, offer a feed-aware
   widget or plugin upstream instead of writing our own.

## Competitor table (short)

| Product | Kind | Open | Local | Multi-vehicle decode | Write path | Data out to other apps | Price |
|---|---|---|---|---|---|---|---|
| AGAMA | Launcher | No | Yes | No | No | No | Trial, then one-off |
| CarWebGuru | Launcher | No | Yes | No | No | No | In-app |
| Car Launcher Pro | Launcher | No | Yes | No | No | No | £13.99 |
| DUDU / FYT stock | Vendor launcher + CAN box | No | Yes | CAN-box firmware only | Some (climate via box) | Closed | Bundled |
| OpenLauncher | Launcher | Yes | Yes | No | No | No | Free |
| Torque Pro | Gauges + diagnostics | No | Yes | OBD + paid plugins | Ungated | **AIDL plugins**, HTTP upload | £2.95 |
| RealDash | Dashboards | Protocol public, app closed | Yes (cloud optional) | Per-car XML | Limited (SET VALUE) | Multicast to RealDash only | Paid + €24/yr cloud |
| Car Scanner | Diagnostics + gauges | No | Yes | Per-make profiles | Coding, ungated | None found | Free + Pro |
| Home Assistant | Home hub | Yes | Yes | Not a decoder | Its own approvals | MQTT, API | Free |
| **Ostler** | Feed + apps | **Yes** | **Yes** | **Packs (VSS)** | **Gated** | **AIDL, provider, MQTT, RealDash** | Open |

## Open questions for the owner

1. **Ship an Ostler launcher in v1?** *Recommended: no.* Ship apps, widgets and the feed
   service. Keep ADR-0048 as proposed but parked, and re-open it only if the sleep test fails.
2. **Should the Android feed's public interface be a published standard others may
   implement?** *Recommended: yes.* Publish a versioned AIDL plus a client library under a
   permissive licence, with VSS paths and Ostler data classes. The decode packs keep their own
   licences.
3. **Should third-party apps be able to request writes through the feed?** *Recommended:
   yes, but only as a request that the Ostler approval UI must confirm.* There is no silent
   write API.
4. **Is RealDash output the first interop target?** *Recommended: yes*, with Home Assistant
   MQTT second. Torque only as an input.
5. **Which units should the sleep and widget tests use?** *Recommended:* the owner's current
   unit plus one FYT UIS7862 unit (as in [canbus_headunit.md](canbus_headunit.md)). Test:
   - widget refresh in the stock launcher, AGAMA and CarWebGuru;
   - feed-service survival over 10 minutes and 12 hours of ACC-off sleep;
   - cold-boot time to first data.
6. **Should the theme engine also style hosted third-party widgets?** *Recommended: no.*
   Style only Ostler apps and widgets. Material You colour seeding on Android 12+ is enough
   to blend in with other launchers.

## Sources

- [AG1] AGAMA Car Launcher, Google Play (UK), read 2026-10-08: https://play.google.com/store/apps/details?id=altergames.carlauncher
- [AG2] AGAMA instructions: http://altercars.ru/agama/instructions/en.html
- [CW1] CarWebGuru Car Launcher, Google Play (UK), read 2026-10-08: https://play.google.com/store/apps/details?id=com.softartstudio.carwebguru
- [CL1] Car Launcher Pro, Google Play (UK), read 2026-10-08: https://play.google.com/store/apps/details?id=com.autolauncher.motorcar
- [FC1] FCC Car Launcher listing: https://apkcombo.com/fcc-car-launcher/ru.speedfire.flycontrolcenter/
- [VV1] What is Vivid OS: https://android-headunits.com/what-is-vivid-os/
- [OL1] OpenLauncher for car head units: https://github.com/dw2lam/openlauncher
- [NV1] Nova Launcher shutting down: https://www.androidauthority.com/open-thread-nova-launcher-is-shutting-down-3595684/
- [LC1] Lawnchair 15 Beta 2: https://alternativeto.net/news/2025/12/lawnchair-15-beta-2-adds-home-screen-infinite-scrolling-new-search-provider-and-more/
- [TQ1] Torque Pro, Google Play (UK), read 2026-10-08: https://play.google.com/store/apps/details?id=org.prowl.torque
- [TQ2] Torque plugin documentation: https://wiki.torque-bhp.com/view/PluginDocumentation
- [TQ3] ITorqueService AIDL discussion: https://www.b4x.com/android/forum/threads/nearly-empty-xml-when-creating-lib-from-aidl-file.44471/latest
- [TQ4] Torque theme install (Mazdaspeed forum): https://mazdas247.com/forum/t/mazdaspeed-torque-app-theme.123826511
- [CS1] Car Scanner ELM OBD2, Google Play (UK), read 2026-10-08: https://play.google.com/store/apps/details?id=com.ovz.carscanner
- RealDash CAN protocol: https://github.com/janimm/RealDash-extras/blob/master/RealDash-CAN/realdash-can-protocol.md
- RealDash bounty thread (2026-08-29): https://forum.realdash.net/t/11113
- aa-torque: https://gittrend.io/repo/agronick/aa-torque
- Widgets for Torque: https://www.bluestacks.com/campaign/org.prowl.torquewidget/en
- FytHWOneKey: https://github.com/hvdwolf/FytHWOneKey
- DUDU7 owner thread: https://t6forum.com/threads/mekede-dudu7-12-512gb-for-vw-transporter-2020-headunit-chat.55921
- Head-unit boot time: https://android-headunits.com/android-headunit-boot-time/
- Poweramp after sleep: https://forum.powerampapp.com/topic/24417-no-album-art-track-progress-lost-after-returning-from-sleep-android-car-head-unit
- CJ Industries sleep setting: https://cj-industries-help.groovehq.com/help/needing-to-restart-unit-to-use-carplay-slash-android-auto
- Widget update limits: https://developer.android.com/guide/topics/appwidgets/advanced
- Android 15 foreground service types: https://developer.android.com/about/versions/15/changes/foreground-service-types
- Car hardware APIs: https://developer.android.com/training/cars/apps/library/car-hardware-api
- Home Assistant companion app, July 2025: https://home-assistant.io/blog/2025/07/23/companion-app-for-android
