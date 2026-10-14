---
title: "Head-unit experiments log — what was tried on disco-n95, what worked, what not to repeat"
area: references
status: draft
version: 0.1
updated: 2026-10-14
depends_on: [references/research/aaos_x86_head_unit.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, references/research/hardware.md]
summary: >
  Experiment log for the owner's own Discovery 2 head unit (not an Ostler product; GOALS.md keeps an OS and launcher as non-goals, ADR-0049). Goal set by the owner on 2026-10-14: Google's car Maps (Maps for Android Automotive) plus Waze on an Android we control, fed by Ostler over VISS. Result on 2026-10-14: car Maps runs with live map data and turn-by-turn on LineageOS 20 GAPPS in Waydroid on the x86 N95, after a first-run flag flip; Waze installs through Aurora Store and runs under libhoudini (owner checked). Records every setup tried (Google AAOS emulator image, Cuttlefish AOSP 17 with transplanted car or phone Google apps, Waydroid LineageOS, SnappMaps), the dead ends with their causes (the self-built AAOS image fails at Play Services' device key, not because of x86; forcing an x86-only ABI list breaks ARM apps; Play keeps a stale device profile), the working recipes and scripts, the hardware findings (VIM3 4 GB too small, Pi 5 has no suspend, N95 supports S3, aosp_rpi5_car exists as source only, Snapp's public layer is AOSP plus SnappMaps) and open questions.
---

# Head-unit experiments log (disco-n95, October 2026)

**Why this exists.** The owner asked on 2026-10-14 for a record of what has been tried, so the
same ground is not covered twice. It is a log for the owner's own Discovery 2 head unit, not an
Ostler product: [GOALS.md](../../GOALS.md) keeps an OS, launcher and own media apps as
non-goals ([ADR-0049](../../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md)),
and Ostler's part is the vehicle-data feed (VISS v3) into whatever screen the car has. The
Cuttlefish measurements are in [aaos_x86_head_unit.md](aaos_x86_head_unit.md). Everything
here was run on disco-n95 (Intel N95, 16 GB, Debian 13) on 2026-10-14 unless marked **(U)**.

## 1. Goal

Set by the owner on 2026-10-14 ("put this as a goal"):

> **The D2 head unit runs Google's car Maps (Maps for Android Automotive) and Waze on an
> Android we control, with Ostler feeding it vehicle data over VISS.**

Owner's preferences recorded along the way:

- Google apps in general are no longer a requirement ("lets forget them, we'll go with waze");
  car Maps is wanted because it works (section 3).
- A gauge cluster on its own screen is still wanted.
- Lane guidance (Polestar 4 / Google "live lane guidance" style) is an interest; any lane help
  stays **guidance and warnings**; steering assistance would need its own ADR and safety case.
- Architecture (ARM vs x86, VM vs container vs phone Android) is **undecided** (section 6).

**Status (2026-10-14):** both work on LineageOS 20 in Waydroid on x86: car Maps (section 3) and Waze under libhoudini ARM translation (section 5).

## 2. Setups tried

| # | Setup | Result | Keep? |
|---|---|---|---|
| 1 | Google's "Android Automotive with Google Play x86_64" API 35 image in the Android Emulator (AVD `car`) | **Works**: car Maps, cluster nav, Play. Locked user build (`ro.debuggable=0`), forced cluster, SDK-licence image | Reference only |
| 2 | Cuttlefish `aosp_cf_x86_64_auto-userdebug` Android 17 (CP2A.260605.016) + Google's car apps copied in (car Play Services GmsCoreAuto 26.18.33, MapsCarPrebuilt 26.04.270002.E, car Play Store, car Assistant, templates host, GSF, WebView) | Boots after fixes, Maps draws UI but **gets no data**: Play Services device key fails | Dead end |
| 3 | Cuttlefish + **phone** Play Services (Android 17 APEX) + car flavours of the rest (`gmix-setup.sh`) | Same device-key failure | Dead end |
| 4 | Waydroid LineageOS 20 GAPPS (Android 13, `20.0-20260927-GAPPS-waydroid_x86_64`) | **Works**: phone Play Services, Play Store, native Intel GPU, ~19 s boot | **Yes** |
| 5 | #4 + car Maps APK from #1 | **Works**: map data, search, routing, turn-by-turn (section 3) | **Yes** |
| 6 | #4 + libhoudini ARM translation + Aurora Store → Waze 5.25.0.1 (arm64) | **Runs** (owner checked, 2026-10-14) | **Yes** |
| 7 | SnappMaps (Snapp Automotive's open OSM app) on Cuttlefish | Works (OSM map, opens on Munich) | Curiosity |
| 8 | sway + Waydroid multi-window tiling (Maps / Spotify / Clock) | Works; freeform windows were rejected by the owner as poor | Option |

## 3. Working recipe: car Maps on LineageOS (Waydroid)

1. Waydroid LineageOS 20 GAPPS, running (`/home/ostler/cf/run-lineage.sh`, unit `ostler-lineage`).
2. Install the car Maps APK over phone Maps (same package `com.google.android.apps.maps`;
   `-d` allows the version downgrade):
   `adb install -r -d ~/gcar-extract/overlay/product/priv-app/MapsCarPrebuilt/MapsCarPrebuilt.apk`.
   The APK is x86_64-native and needs no translation.
3. Grant location: `pm grant com.google.android.apps.maps android.permission.ACCESS_FINE_LOCATION`
   (and COARSE, BACKGROUND).
4. Launch once, then clear the first-run lock. Car Maps shows "Welcome… turn on your vehicle's
   location and review your privacy controls" and stays offline while protobuf field 7 of
   `files/car/shared/privacy_settings.pb` is `1` (NOT_FINISHED). With Maps stopped, write
   `08 07 10 02 18 01 28 02 38 02` (field 7 = `2`). In Waydroid the file is on the host at
   `~/.local/share/waydroid/data/data/com.google.android.apps.maps/files/car/shared/`.
   A backup of the original is at `~/privacy_settings.pb.bak`.
5. Set a location (Waydroid has no GPS): `/home/ostler/cf/waydroid-gps.sh [lat lon]`
   (default Eastry, 51.2465, 1.3087). It uses Android's test providers for gps, network and
   fused, and lasts until the Waydroid session restarts.

**Why it works here and not on Cuttlefish:** LineageOS GAPPS carries working phone Play
Services, and car Maps runs on top of it. Not yet checked **(U)**: sign-in (the community
report says car Maps on phone Android works without signing in), voice, and the cluster turn
card (phone Android has no cluster API).

## 4. Dead ends — do not repeat

| Tried | What happened | Cause |
|---|---|---|
| Google car apps on a self-built AAOS image (#2, #3) | Play Services: "Exception while requesting key", "Device key file not found"; Maps: "ConsentManager.API is not available", no network requests | Device identity: a test-keys AOSP build is not a Google-recognised device. **Not** x86: Google's own x86_64 image (#1) works on the same box, and the transplanted apps were x86 builds |
| Forcing `ro.product.cpu.abilist` to x86_64 only on Cuttlefish (to fix ARM Chrome) | Broke Waze and most ARM apps; reverted in all four build.prop files | The image relies on ARM translation for Play apps |
| Re-checking Play after an ABI change | Play still says "Your device isn't compatible with this version" for Waze | Play keeps the old device profile server-side; clearing Play Store data did not refresh it. Use Aurora Store instead |
| Removing the cluster from the Google emulator image (`hw.display6.*`) | Emulator segfaults; runtime `multidisplay del 6` breaks the layout | Emulator limitation |
| `adb install` on Cuttlefish with Play Protect on | Install hangs on an on-screen "scan this app?" prompt | Set `settings put global verifier_verify_adb_installs 0` first |
| Spoofing a certified device fingerprint or attestation | Declined | Not a route we take |
| Sideloading AAOS "into Waydroid" | Not possible as is | Waydroid needs a LineageOS image built for it; no AAOS Waydroid image exists (section 6) |

Fixes that were needed on Cuttlefish, in case it is revisited: gfxstream needs
`EGL_PLATFORM=surfaceless` plus libegl-dev/libgles-dev; privapp boot loop →
`ro.control_privapp_permissions=log`; Play installs need a bigger data disk
(`--data_policy=always_create --blank_data_image_mb=24576`); GcarSetup crash-loops without
platform-signed permissions (disable it); start `cvd` detached with `setsid`.

## 5. Other findings

- **Vehicle data into AAOS works.** The host sets climate, gear and RPM in the Cuttlefish VHAL
  (`/home/ostler/cf/vhal-inject.sh`); this is the Ostler → AAOS path.
- **ARM apps on x86.** Cuttlefish's image has Google's translator built in. Waydroid had none
  (`x86_64,x86`) until libhoudini was installed with casualsnek/waydroid_script
  (`/opt/waydroid_script`, `main.py install libhoudini`; undo with `uninstall libhoudini`).
  The ABI list is now `x86_64,x86,arm64-v8a,armeabi-v7a,armeabi`.
- **Snapp Automotive.** Their public GitHub layer is AOSP AAOS plus SnappMaps, a skip-setup
  provision app, overlays and a boot animation; SnappOS itself is the private
  `vendor/*/non_public` layer. They already publish an x86_64 emulator target
  (`sdk_car_snapp_x86_64`). The VIM3 kit images (Android 12–15) are the public layer, not SnappOS.
- **Hardware.**
  - VIM3 Pro: A311D, 4 GB maximum, too small for a daily head unit (Cuttlefish AAOS used ~4.4 GB).
  - Raspberry Pi 5: KonstaKANG publishes tablet AOSP 16/17 images (non-commercial licence)
    with optional GApps; AAOS exists only as the source target `aosp_rpi5_car`
    (raspberry-vanilla, Android 16/17: CAN HAL, default VHAL, EVS). The Pi 5 has **no suspend**.
  - RK3588: strongest ARM per pound; no AAOS build found; suspend patchy on mainline **(U)**.
  - The N95 supports S3 (`/sys/power/mem_sleep` = `deep`); box draw in S3 not yet measured.
  - No off-the-shelf N-series box combines CAN and ignition sensing; the rugged in-vehicle
    lines that have both use older Atom or Core chips.
- **Power while parked.** About 35 Ah usable: 5 W left running flattens it in about 3 days;
  1 W in about 2 weeks. ARM phone-class SoCs sleep at milliwatts. Plan: the head unit sleeps
  with ACC and the Guardian wakes it over a wake wire through the relay module, then cuts power
  after a few days ([ADR-0040](../../decisions/adr-0040-power-states-and-wake.md)).

## 6. Open questions

- **Architecture.** x86 Linux host + Android (Waydroid now; an AAOS-for-Waydroid build later)
  vs an ARM board running Android natively. ARM avoids translation and sleeps better on
  phone-class SoCs; x86 keeps the Linux host, mainline drivers and S3. Waze runs under translation on
  x86, so the remaining input is an S3 power measurement.
- **AAOS for Waydroid.** LineageOS's Waydroid target plus the AAOS car layer and an
  Ostler-fed VHAL. Nobody publishes one **(U)**; needs the big build machine.
- **Cluster.** Its own screen drawn from VISS, with a small Android app passing the nav turn
  card. **(U)** what car Maps exposes on phone Android without the cluster API.
- **Rear and passenger screens.** Headrest tablets with an Ostler app; nothing may go in the
  passenger airbag's deployment path.
- **Lane advisor.** Camera + NPU lane detection (openpilot's vision model is a candidate)
  plus OSM `turn:lanes`, warnings only.

## 7. Files on disco-n95

| Path | What |
|---|---|
| `/home/ostler/cf/run-lineage.sh`, `run-sway.sh`, `car-layout.sh`, `car-fit.sh` | LineageOS on HDMI, full screen or tiled |
| `/home/ostler/cf/waydroid-gps.sh` | Fixed location in Waydroid |
| `/home/ostler/cf/run-stream.sh` | wayvnc + noVNC remote view on :6080 |
| `/home/ostler/cf/cf-up.sh`, `cf-up-mix.sh`, `cfadb.sh`, `gcar-setup.sh`, `gmix-setup.sh`, `gcar-grant.sh` | Cuttlefish and the Google-app transplant |
| `/home/ostler/cf/vhal-inject.sh` | Host → AAOS VHAL values |
| `/home/ostler/cf/run-car.sh` | Google AAOS emulator image on HDMI |
| `/home/ostler/gcar-extract/`, `/home/ostler/gphone-extract/` | Apps and configs extracted from Google's images |
| `/home/ostler/snapp-public/`, `/home/ostler/aurora/` | SnappMaps, Aurora Store APKs |

## Sources

- Bench runs on disco-n95, 2026-10-14 (session log).
- Snapp Automotive GitHub: https://github.com/snappautomotive (device_snappautomotive_vim3 wiki,
  firmware-local_manifest, firmware-device_snappautomotive_common, firmware-device_snappautomotive_emulator)
- raspberry-vanilla Pi 5 device tree: https://github.com/raspberry-vanilla/android_device_brcm_rpi5
- KonstaKANG Pi 5 builds: https://konstakang.com/devices/rpi5/AOSP16/
- waydroid_script: https://github.com/casualsnek/waydroid_script
- Google AAOS SDV announcement (March 2026): https://android-developers.googleblog.com/2026/03/Beyond-Infotainment-Extending-Android-Automotive-OS-for-Software-defined-Vehicles.html
- Polestar 4 live lane guidance: https://www.autoevolution.com/news/polestar-4-is-the-first-car-to-adopt-the-new-google-maps-ai-driven-live-lane-guidance-260411.html
