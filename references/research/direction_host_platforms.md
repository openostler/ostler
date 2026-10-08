---
title: "Host platforms for native Ostler apps: feed, widgets and limits per host"
area: references
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, references/research/canbus_headunit.md, references/research/driver_distraction_rules.md, references/research/power_states.md, specs/2026-10-07-head-unit-apps-design.md, specs/2026-10-07-launcher-and-widgets-design.md]
summary: >
  Recommendation: v1 hosts are stock aftermarket Android head units (Android 10 to 13 FYT and
  UIS7870 units) and Android phones (Android 10+), served by one native "Ostler Vehicle" app.
  It holds the only link to the node (Wi-Fi or BLE, USB later) in a connectedDevice foreground
  service, and gives other apps a documented local feed: a bound AIDL service plus a loopback
  WebSocket with a token. Widgets are AppWidgets built with Glance for glanceable values at
  about 1 Hz at most. Live gauges at 5 to 10 Hz need an activity, a split-screen pane or a
  floating overlay, never widget updates. Head units force-stop third-party apps on ACC off, so
  plan for cold restarts. Android Auto allows no dashboard app; its phone-widget support
  (announced May 2026, not shipped by 8 October 2026) is the one projection opening to watch.
  AAOS, LineageOS, Waydroid, iOS and a PWA come later.
---

# Host platforms for native Ostler apps

**Question.** On each host, how does a native app get a live vehicle feed and draw widgets,
and what limits apply? The owner chose Android head units and Android phones first, so this
goes deepest there. Web facts were checked on 2026-10-08. **(U)** marks a claim that is not
verified. The head-unit hardware facts build on [canbus_headunit.md](canbus_headunit.md).

## Recommendation

1. **v1 hosts: stock Android head units and Android phones.** Same APKs on both. Minimum SDK
   29 (Android 10), because FYT UIS7862 units still ship Android 10 [F1 in canbus_headunit].
2. **One feed owner per device.** An "Ostler Vehicle" app holds the only link to the node or
   Brain, in a foreground service of type `connectedDevice` [A3]. Every other Ostler app, and
   any third-party app the owner allows, reads from it. This is the "standard" the owner asked
   for: the same local API on a head unit and on a phone.
3. **The local feed contract has two doors.**
   - A bound **AIDL service** with a signature-or-owner-granted permission, for Ostler apps
     and widgets (fast, no network, works on every Android).
   - A **loopback WebSocket** (127.0.0.1, token in a ContentProvider the owner grants), carrying
     the same VSS paths ([ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)).
     It also serves WebView apps, Waydroid and a later Linux host unchanged.
   - Not broadcast intents: implicit broadcasts do not reach manifest receivers since Android 8,
     and they are slow and public.
4. **Widgets are for glances, not gauges.** AppWidgets (Glance) show values that change about
   once a second or slower: fuel, coolant, faults, trip, node status. Anything faster lives in
   an activity (full screen or a split-screen pane) or an opt-in floating overlay.
5. **Survive the head unit's kill.** Assume a force-stop on every ACC off. Recover on the next
   wake by a launcher auto-start, a user-granted whitelist entry, or the owner opening the app
   once. Never depend on `BOOT_COMPLETED` alone.
6. **No own launcher in v1.** Stock launchers on most units host AppWidgets, and some UIS7870
   firmware blocks a custom default launcher. Keep ADR-0048 (web app as launcher) parked;
   revisit a native launcher only if bench tests show stock hosts fail.
7. **Later hosts, in order:** Android Auto widgets (if Google opens them to our widget), iOS,
   LineageOS on Pi 5, Linux plus Waydroid, AAOS last. A PWA stays the zero-install fallback.

## The host matrix

| Host | Feed transport into the app | Widget surface | Live rate achievable | Background limits | Store rules | What Ostler ships |
|---|---|---|---|---|---|---|
| **Aftermarket Android head unit** (FYT UIS7862/7870, DuduOS, Teyes and similar) | Node or Brain over Wi-Fi (MQTT/WebSocket); BLE GATT; USB CDC serial later. Vendor MCU/CAN-box data only via undocumented system apps | Stock vendor launcher (AppWidgets mostly supported (U per unit)); third-party car launchers; split-screen | Activity or overlay: 10 Hz+. AppWidget: about 1 Hz practical | Third-party apps force-stopped about 20 to 30 s after ACC off; whitelists need factory menu or root; fast-boot resume skips `BOOT_COMPLETED` | Play Store usually present (not always certified); free sideloading | Vehicle app (FGS), app suite, Glance widgets, optional overlay, setup guide per unit family |
| **Android phone** | BLE to node; Wi-Fi to node AP or Brain; Bluetooth Classic SPP to ELM-type adapters; USB OTG | Any launcher's AppWidgets; Glance | Activity: 10 Hz+. Widget: about 1 Hz while the app's service runs | Battery optimisation and vendor killers; FGS needs a visible notification; Android 15 blocks some FGS types from `BOOT_COMPLETED` | Play FGS declaration with video; no special OBD policy | Same APKs; phone layouts; companion-device pairing |
| **Android Auto** (projection) | The phone app's own feed | Car App Library templates only; phone AppWidgets "this year" (not shipped by 8 Oct 2026) | Templates: refresh on change, task quota of 5 templates | Runs from the phone app | Categories only (media, communication, navigation, POI, IoT, weather, parked video and games); review before production | Nothing in v1; test a POI or IoT slice; watch car widgets |
| **Android Automotive OS** (Google built-in) | VHAL gives car data to OEM-approved apps; our node only via network | No third-party widgets on most builds (U) | Templates only | OEM-controlled | Play AAOS track, category review, no sideloading on production cars (U, OEM-dependent) | Nothing in v1 |
| **LineageOS on Pi 5 or x86** | Same as phone, plus local USB/UART to the node | Trebuchet launcher hosts AppWidgets | As phone | Owner controls; no vendor killer | Unofficial builds; GApps optional | Same APKs; image notes |
| **Linux plus Waydroid** | Linux service to Android app over the `waydroid0` bridge or adb forward | Android launcher inside Waydroid (full-UI mode) | As phone, minus GPU overhead (U) | Container lifecycle | No Play certification; sideload | Same APKs; a bridge doc |
| **iOS** (later) | BLE only for adapters (or MFi Classic); Wi-Fi to node | WidgetKit; Live Activities; both also on CarPlay Dashboard | Widget: about 40 to 70 reloads a day. Live Activity: event-driven | Suspended in background; BLE wakes only on events | App Store review; CarPlay needs an entitlement per category | A Swift app later; Live Activity for a drive |
| **Web / PWA** | WebSocket to Brain; Web Serial over Bluetooth RFCOMM on Android Chrome; nothing on iOS Safari | None (no widget API) | Foreground only, 10 Hz+ | Dies when hidden | None | The current web UI as fallback |

## Evidence

### 1. Stock aftermarket Android head units

**Hardware and Android version.**
- FYT units (Joying, Mekede, Junsun, Teyes and others) run Android 10 on UIS7862, often
  badged higher; newer UIS7862S sheets claim Android 13 with 4 to 8 GB RAM [HW1]. Details and
  sources are in [canbus_headunit.md §B1](canbus_headunit.md).
- UIS7870 units (DUDU7, Mekede M-series): Android 13 on DuduOS, up to 12 GB RAM and 512 GB
  UFS; owners report a store present; an Android 14 update was promised, not confirmed [HW2][HW3].
- Teyes CC4 listings name a Qualcomm SM6226 with Android 13 or 14 claims, 6 to 8 GB RAM; the
  listings conflict [HW4] (U).
- **Consequence:** target Android 10 to 13. These units will not get Android 15 to 17
  behaviour changes, but our phone builds will.

**Launchers and AppWidgets.**
- Stock launchers are vendor-made; widgets are a launcher feature, and AGAMA, Car Launcher Pro
  and CarWebGuru all host widgets [L1]. Whether each stock launcher hosts third-party
  AppWidgets is per unit (U); a bench item.
- A long-term UIS7870 review reports a custom launcher cannot be set as default and split-screen
  is unreliable [HW5]. Other users report units reverting to the stock launcher on each start
  [L1]. **So shipping our own launcher is fragile on exactly the hosts we chose.**

**Background killers, sleep and wake.**
- On ACC off the firmware starts a countdown of about 20 to 30 s, then force-stops third-party
  apps. A force-stopped app gets no implicit broadcasts, including `BOOT_COMPLETED`, until the
  user or another app starts it [K1].
- Whitelists exist but are not app-reachable: FYT `/oem/app/pwctl_config.xml` (removed in
  recent firmware; the "FYT Factory" tool is the no-root route), Junsun `qb_list.xml`,
  Microntek's `MTCManager`/`HCTManagerService`, Reglink files under `/system/etc/` (root) [K1][K2].
  Some non-FYT UIS7862S units offer a sleep whitelist in factory settings [K3].
- MediaTek units add DuraSpeed, a separate background killer [K1].
- ACC wake broadcasts are vendor-specific and unreliable: `com.fyt.boot.ACCON`/`ACCOFF`
  (reported to work only on Android 7 and below), `com.microntek.startApp`, `com.cayboy.action.ACC_ON`
  [K1][K4].
- FYT factory settings choose sleep or power-off after ACC off [canbus_headunit.md §B1].
- **Plan:** (a) a setup page that walks the owner through the unit's whitelist or "keep alive"
  setting where one exists; (b) recommend a launcher auto-start rule (AGAMA can start apps on
  boot [K4]); (c) treat every wake as a cold start that reconnects in under 2 s; (d) never hold
  state only in memory.

**MCU, CAN-box and steering-wheel data.**
- No vendor SDK is published. FYT's `com.syu.ms` owns the MCU link; `com.syu.canbus` binds
  `com.syu.ms.toolkit`. Third-party access is reverse engineering [MC1][canbus_headunit.md §B1].
- Older Microntek units broadcast `com.microntek.sync` with a 20-byte `syncdata` array that one
  developer decoded into speed, revs, voltage and temperature [MC2] (U on current firmware).
- Steering-wheel keys reach apps as standard media keys through MediaSession when the unit
  forwards them; FytHWOneKey maps hardware keys to any app or intent on FYT [canbus_headunit.md].
- **For the Discovery 2 this barely matters:** the car has no comfort CAN, so the CAN box has
  little to say. Ostler's own node is the feed. Use the head unit's CAN-box UART only in the
  other direction, via the planned CAN-box emulator [canbus_headunit.md §B3].

**Installing apps.** Play Store is usually present but not always Play-certified (U); APK
sideloading is free. Distribute through Play for phones and as a signed APK or F-Droid-style
repo for head units without Play.

### 2. Android phones

**AppWidgets and Glance.**
- `updatePeriodMillis` has a 30-minute floor; WorkManager allows about 15 minutes; pushing
  updates while the app is awake has no documented cap [W1][W2].
- A Glance session keeps composing for about 45 s after `provideContent`, extended by
  interactions and updates; data observed inside the composition recomposes and re-sends
  RemoteViews [W3].
- Every update is a cross-process RemoteViews send that the launcher inflates and applies.
  `partiallyUpdateAppWidget` merges changes and is cheaper [W1]. Bitmaps and icons in one
  RemoteViews must fit 1.5 screens of memory; from Android 17 this throws [W4].
- No documented rate limit exists, but there is also no frame clock: a needle at 10 Hz means
  10 full IPC round trips a second per widget, plus launcher layout. Treat **1 Hz as the
  ceiling** for widget values (U: bench it on a UIS7862 unit).
- Launchers may stop listening for widget updates when they are not in front (AOSP Launcher3
  defers updates while paused) (U); harmless, because the widget is not visible then.
- Android 15 added `RemoteViews.DrawInstructions` for Remote Compose payloads [W5]. Host
  support is new and absent on Android 10 to 13 head units, so it is not a v1 tool.

**Foreground services.**
- `connectedDevice` covers Bluetooth, USB and network links to external devices. It needs
  `FOREGROUND_SERVICE_CONNECTED_DEVICE` plus one of: a Bluetooth runtime permission, USB
  permission, or `CHANGE_NETWORK_STATE`/`CHANGE_WIFI_STATE` [A3].
- Android 15 caps `dataSync` at 6 hours per 24 and bars `dataSync` and some other types from
  `BOOT_COMPLETED`; `connectedDevice` has no stated time cap [A3][A4]. **Use connectedDevice,
  never dataSync, for the live link.** Use `location` only if the app itself records GPS.
- Google suggests the companion device manager for continuous transfer to a device in range
  [A3]; on phones, pair the node as a companion device so the app is kept alive near the car.
- Play Console needs a declaration per FGS type: description, user impact, and a video;
  `connectedDevice` lists "cars" as an example [P1].
- Android 17 restricts background audio focus and playback for all apps [A5]; only matters if
  a background Ostler app speaks alerts.

**Bluetooth and USB OBD.** Classic SPP (ELM327 clones) works on Android but not iOS; BLE
adapters work on both [I3]. USB OTG serial works through `UsbManager` with user permission.
For Ostler the main link is our node, not an ELM adapter.

**Play policy for OBD and vehicle apps.** No OBD-specific policy found; Torque, Car Scanner and
others are listed. The live rules are the FGS declaration, Bluetooth and location permission
declarations, and the Device and Network Abuse policy [P1]. Any feature that writes to the car
should be described plainly in the listing (our CONSTITUTION's transmit gate helps).

### 3. Android Auto (phone projection)

- Supported categories: media, communication (messaging notifications, templated messaging and
  calling, both labs), navigation, POI, IoT, weather, and parked video, games and browsers [AA1].
  "Parking and charging" folded into POI in 2022. There is **no dashboard, gauge, diagnostics
  or vehicle-data category**, and apps "must not include features outside the app types
  intended for cars" [AA1].
- Templates only. A task may show at most five templates; same-type content refreshes do not
  count [AA2]. Navigation apps get a drawing surface, but a gauge app posing as navigation
  would fail review.
- Car App Library apps must come from a trusted source; Android Auto's "unknown sources"
  option covers media, messaging and parked apps only [AA3]. Play internal testing has **no**
  car review, closed testing a non-blocking one, production a blocking one [AA4]. So a private
  template app can reach the owner's own phone through internal testing.
- **New: widgets.** In May 2026 Google said phone widgets will come to Android Auto "this
  year", with cars with Google built-in later, alongside a full-display redesign and parked
  video for phones on Android 17 [AA5][AA6]. Google's own lead said it is unclear whether all
  phone widgets or a limited selection will be allowed [AA7]. As of the 17.9 stable rollout in
  early October 2026, widgets had not shipped [AA8]. If they open to any glanceable widget, an
  Ostler Glance widget would appear on Android Auto with no extra work; plan for it, do not
  depend on it.

### 4. Android Automotive OS

- Apps come only through Play on cars with Google built-in, on a dedicated AAOS track, with
  category review for media and templated apps; communication apps are not supported [AA4].
- Same category list as Android Auto, plus parked video, games and browsers [AA1].
- Car data reaches apps through VHAL properties that the OEM exposes, mostly to its own apps
  [canbus_headunit.md §B6]. Sideloading on production cars depends on the OEM and is often
  locked (U).
- Our target cars (a Discovery 2 and similar) will never run AAOS. Verdict: last.

### 5. LineageOS on Pi 5 or x86

- KonstaKANG lists LineageOS 20 to 23.2 (Android 13 to 16) and AOSP up to Android 17 for the
  Pi 5; 22.2 had hardware graphics (V3D, OpenGL, Vulkan) and H.265 decode [LO1][LO2].
  Unofficial and single-maintainer.
- Bliss OS for x86: stable on Android 11 and 12, Android 13 in beta, with and without GApps
  [LO3]. No confirmed Android 14+ build found (U).
- Boot is about 30 s versus 10 to 12 s for Linux (chat claim, U); no vendor killer; standard
  launchers host widgets. Good for a DIY Brain-with-screen; not for v1.

### 6. Linux plus Waydroid

- Waydroid runs Android 13 (community builds up to 16) in an LXC container; multi-window mode
  opens each app as a Linux window; 1.6.0 (November 2025) always shows the Android launcher in
  multi-window mode and no longer auto-connects adb [WD1][WD2].
- The container gets a bridged Ethernet link through the host [WD3]. A Linux-side Ostler
  service can be reached from Android at the host's bridge address, or the app can reach
  loopback only if the service is bound to the bridge (U on Pi 5).
- **AppWidgets live only inside the Android launcher.** In multi-window mode there is no Linux
  home screen for them (U). Pi 5 needs a kernel with binder support (U).
- Useful later because the loopback WebSocket door in the Recommendation works unchanged.

### 7. iOS (later)

- WidgetKit: a frequently viewed widget gets about 40 to 70 reloads a day, roughly every 15 to
  60 minutes; reloads while the app is in the foreground do not count [I1].
- Live Activities: push budget undocumented; high-priority pushes spend it;
  `NSSupportsLiveActivitiesFrequentUpdates` helps but users can turn it off [I2]. Local
  updates from a running app are possible while it has background time.
- Background Bluetooth: `bluetooth-central` lets iOS wake the app on BLE events; it can still
  be terminated; state restoration relaunches it only on discovery, connection or notification
  [I3]. Classic SPP needs MFi adapters (OBDLink MX+, vLinker FS/MS) [I3].
- CarPlay: audio, video (parked), messaging and VoIP, navigation, EV charging, fuelling,
  parking, public safety, quick food ordering, voice-based conversational and driving task.
  Small widgets and Live Activities appear on CarPlay Dashboard automatically unless marked
  not suitable [I4]. Driving task needs an entitlement and may fit a slim status app (U).
- **Best iOS shape:** a Live Activity for "drive in progress" (fuel, temp, faults) that also
  shows on CarPlay, plus a small widget for parked status.

### 8. The web (PWA)

- Chrome on Android ships Web Serial over Bluetooth RFCOMM for paired devices; WebView does
  not get it; no Web Bluetooth or Web Serial on iOS Safari [WB1][WB2].
- No widget API, and a hidden tab stops. Keep the existing web UI as the zero-install and
  desktop fallback, served by the Brain.

## Platform traps

1. **Widget update rate.** `updatePeriodMillis` floors at 30 minutes; WorkManager at about 15.
   Only a running process can push faster, and each push is a full or partial RemoteViews IPC.
   Options for live gauges:
   - **An activity** in a split-screen pane: real rendering at the display rate. Best on
     large head-unit screens.
   - **A floating overlay** (`SYSTEM_ALERT_WINDOW`, owner-granted): a small always-on-top
     gauge over any app. Opt-in, Parked-safe defaults, respects driver-distraction rules
     ([driver_distraction_rules.md](driver_distraction_rules.md)).
   - **Our own launcher with its own host**: it could embed our views directly, but some
     units block custom launchers. Not v1.
   - **Collection widgets** (`notifyAppWidgetViewDataChanged`) do not help: they refresh list
     data, not frames.
   - **Host-animated views** (`Chronometer`, `TextClock`, progress bars) tick without updates
     but cannot follow live data.
2. **Force-stop on ACC off.** Third-party services die every time the car is switched off;
   `BOOT_COMPLETED` never arrives to a stopped app.
3. **Fake Android versions.** A unit badged "Android 13" may run Android 10; check
   `Build.VERSION.SDK_INT` and record it per test unit.
4. **One Wi-Fi radio.** A head unit on the node's AP loses phone-hotspot internet
   ([canbus_headunit.md §B8](canbus_headunit.md)). Prefer BLE or USB for the feed on units that
   need hotspot internet.
5. **Android 15 FGS rules.** `dataSync` is capped and cannot start at boot; use
   `connectedDevice`.
6. **Play FGS declaration** needs a video per type; plan it before the first release.
7. **Android Auto categories.** No gauge app. A "navigation" or "IoT" app smuggling a
   dashboard will be rejected at production review.
8. **Bitmap-heavy widgets** (rendered gauge images) hit the 1.5-screen memory limit and, from
   Android 17, throw [W4].
9. **Glance session expiry.** Composition stops about 45 s after the last trigger; a widget
   that relies on observing a flow must be kicked by `update()` from the service [W3].
10. **Undocumented vendor APIs** (`com.syu.*`, `com.microntek.*`) change between firmware; never
    a v1 dependency.
11. **Waydroid widgets** are invisible on the Linux desktop in multi-window mode (U).
12. **iOS cannot keep a live feed in the background.** Plan iOS around Live Activities and
    events, not polling.

## Minimum viable host set for v1

- **Android phone, Android 10+** (Pixel-class and one aggressive vendor such as Xiaomi or
  Samsung for battery killers).
- **One FYT UIS7862 head unit** (Android 10, the floor) and **one UIS7870 unit** (Android 13,
  DuduOS), plus the owner's current unit.
- Not in v1: Android Auto, AAOS, iOS, LineageOS, Waydroid. The web UI remains as fallback.

## Open questions for the owner

1. **Do we ship our own launcher in v1?** Recommended: no. Ship apps with widgets; the stock
   launcher hosts them. Revisit after bench tests.
2. **Which feed doors do third-party apps get?** Recommended: AIDL for Ostler apps; the
   loopback WebSocket opened to third parties only after the owner approves each app.
3. **Floating overlay for live gauges?** Recommended: yes, opt-in, one small overlay app,
   with the driver-distraction defaults from the existing rules research.
4. **Distribution for head units without Play?** Recommended: Play for phones; a signed APK
   repo (F-Droid format) for head units.
5. **Minimum Android version?** Recommended: Android 10 (SDK 29).
6. **Android Auto widgets?** Recommended: design Glance widgets to pass car-widget rules
   (large text, no scrolling, glanceable) so they are ready if Google opens the surface.
7. **iOS shape?** Recommended: a Live Activity first, widgets second, CarPlay driving-task
   entitlement only if a slim status app is wanted.

## Sources

- [HW1] UIS7862S spec sheet: https://p.globalsources.com/IMAGES/PDT/SPEC/536/K1225341536.pdf
- [HW2] DUDU7 owner thread (T6 Forum): https://www.t6forum.com/threads/mekede-dudu7-12-512gb-for-vw-transporter-2020-headunit-chat.55921/
- [HW3] DUDU7 thread (DIYMA): https://www.diymobileaudio.com/threads/dudu7-game-changer-android-headunit.470412/
- [HW4] Teyes CC4 listing: https://shopping.truda.io/product/navigatie-auto-teyes-cc4-saab-9-3-2007-2014-664gb-95-qled-octa-core-27ghz-android-4g-bluetooth-51-dsp
- [HW5] UIS7870 long-term review (XDA): https://xdaforums.com/t/uis7870-head-unit-fast-hardware-frustrating-software.4742575/
- [L1] Head-unit launchers: https://android-headunits.com/android-head-unit-launcher/
- [K1] HeadUnit Revived auto-start guide: https://gist.github.com/andrecuellar/3c39b4f1bdc03a5c4e97336217f13c38
- [K2] JunsunSleepConfigurator: https://xdaforums.com/t/junsunsleepconfigurator.4459019/
- [K3] QF001 / ROCO K706 UIS7862S thread: https://xdaforums.com/t/general-discussion-qf001-roco-k706-head-units-with-uis-7862s-not-fyt-based-read-first-post-first.4525675/
- [K4] Tasker after head-unit sleep: https://xdaforums.com/t/solution-start-tasker-after-head-unit-sleep.4102439/
- [MC1] FYT canbus API: https://xdaforums.com/t/reading-changing-canbus-api-for-new-car.4517195/
- [MC2] Reading vehicle data on Microntek: https://xdaforums.com/t/reading-vechicle-sensor-data-in-android-app-canbus-input.3670024/
- [W1] Advanced widgets: https://developer.android.com/develop/ui/views/appwidgets/advanced
- [W2] Glance widgets: https://developer.android.com/develop/ui/compose/glance/glance-app-widget
- [W3] GlanceAppWidget reference: https://developer.android.com/reference/kotlin/androidx/glance/appwidget/GlanceAppWidget
- [W4] AppWidgetManager reference: https://developer.android.com/reference/android/appwidget/AppWidgetManager
- [W5] RemoteViews.DrawInstructions: https://developer.android.com/reference/android/widget/RemoteViews.DrawInstructions
- [A3] Foreground service types: https://developer.android.com/develop/background-work/services/fgs/service-types
- [A4] FGS timeouts (Android 15): https://developer.android.com/develop/background-work/services/fg-service-timeout
- [A5] Android 17 behaviour changes: https://developer.android.com/about/versions/17/behavior-changes-all
- [P1] Play FGS requirements: https://support.google.com/googleplay/android-developer/answer/13392821
- [AA1] Car app quality: https://developer.android.com/docs/quality-guidelines/car-app-quality
- [AA2] Template restrictions: https://developer.android.com/training/cars/apps/library/template-restrictions
- [AA3] Testing (unknown sources): https://developer.android.com/training/cars/testing
- [AA4] Distribute to cars: https://developer.android.com/training/cars/distribute
- [AA5] Android for Cars blog, May 2026: https://android-developers.googleblog.com/2026/05/android-for-cars-unifying-platforms-premium-experiences.html
- [AA6] Android Auto redesign: https://9to5google.com/2026/05/12/android-auto-redesign-widgets-new-update/
- [AA7] Android Auto widgets at I/O 2026: https://www.androidauthority.com/android-auto-google-io-2026-features-material-3-widgets-video-apps-3665474/
- [AA8] Android Auto 17.9 stable without widgets: https://speedme.ru/en/posts/id82139-android-auto-17-9-reaches-stable-rollout-but-google-s-big-redesign-is-still-missing
- [LO1] KonstaKANG Pi 5 builds: https://konstakang.com/devices/rpi5/
- [LO2] LineageOS 22.2 for Pi 5: https://konstakang.com/devices/rpi5/LineageOS22/
- [LO3] Bliss OS overview: https://en.linuxadictos.com/What-is-bliss-os-and-how-to-install-it-on-your-pc.html
- [WD1] Waydroid 1.6.0: https://ubuntuhandbook.org/index.php/2025/11/waydroid-1-6-0-forward-notifications-to-desktop/
- [WD2] Waydroid adb: https://docs.waydro.id/faq/using-adb-with-waydroid
- [WD3] Waydroid overview: https://pbxscience.com/waydroid-running-android-natively-on-linux-what-it-is-how-it-works-and-what-you-should-know/
- [I1] Keeping a widget up to date: https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date
- [I2] Live Activity push budget (forum): https://developer.apple.com/forums/thread/731715
- [I3] Core Bluetooth background: https://developer.apple.com/library/archive/documentation/NetworkingInternetWeb/Conceptual/CoreBluetooth_concepts/CoreBluetoothBackgroundProcessingForIOSApps/PerformingTasksWhileYourAppIsInTheBackground.html ; adapters: https://www.obdautodoctor.com/help/articles/supported-obd-adapters/
- [I4] CarPlay: https://developer.apple.com/carplay/
- [WB1] Web Serial over Bluetooth on Android: https://groups.google.com/a/chromium.org/g/blink-dev/c/BqUGCcurReE/m/XbuAYkRxEQAJ
- [WB2] WebKit Web Bluetooth bug: https://bugs.webkit.org/show_bug.cgi?id=101034
