---
title: "Designer brief 80-a — head-unit apps: the feature map and the shared rules"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-06-platform-direction-design.md, references/research/driver_distraction_rules.md, references/research/canbus_headunit.md, references/research/hardware.md]
summary: >
  First of the head-unit apps brief (80-a to 80-m). The owner's direction of 2026-10-07 says
  Ostler must do everything a modern aftermarket head unit does. This file maps every standard
  head-unit page and feature (Android units, Pioneer, Kenwood, Alpine) to the Ostler app that
  owns it: Radio, Audio, Media, Camera, Clock and Weather (starter widget pack), Voice,
  projection (not built), steering-wheel controls, climate, pack vehicle settings and system
  sounds. It sets the rules every head-unit
  app shares: the `media` Moving template, Parked-only long lists and video, the audio path
  from the Brain, who owns what (app or OS), and which screens the approved head-unit apps
  spec covers (New) and which stay Proposed. It lists the files that follow.
---

# 80-a — Head-unit apps: feature map and shared rules

Files in this set: **80-a** feature map and rules · [80-b](80-hu-b-radio.md) Radio pages ·
[80-c](80-hu-c-radio-setup.md) Radio setup and settings · [80-d](80-hu-d-audio.md) Audio:
sources, EQ, balance · [80-e](80-hu-e-audio-tuning.md) Audio: crossover, time alignment,
subwoofer, volume rules, system sounds · [80-f](80-hu-f-audio-setup.md) Audio setup and
settings · [80-g](80-hu-g-media.md) Media pages and the Moving template ·
[80-h](80-hu-h-media-setup.md) Media setup, integrations, settings ·
[80-i](80-hu-i-camera.md) Camera pages · [80-j](80-hu-j-camera-setup.md) Camera setup and
settings · [80-k](80-hu-k-clock-weather.md) Clock and Weather ·
[80-l](80-hu-l-voice-swc.md) Voice and steering-wheel controls ·
[80-m](80-hu-m-projection-vehicle.md) Projection, climate, pack vehicle settings.

## Why most screens here are New

The approved UI spec listed media, CarPlay and Android Auto, radio and wheel controls as
**non-goals** that "stay on a media head unit" ([UI §1][ui-1]); the platform direction says
"keep a head unit for media" ([platform direction][pd]). The owner reversed that on
2026-10-07 (ADR-0046) and approved the **head-unit apps spec**, which maps every standard
head-unit page to an app ([head-unit apps §2][hu-2]). Screens that spec covers are **New**.
Still **Proposed**: projection, which is **not built** (decided, item 38): owners keep a
projection-capable head unit beside Ostler ([head-unit apps §11][hu-11]); and the pages
the spec leaves out, each block says why. Already approved before: the `media` Moving
template ([UI §12.1][ui-12.1]), the now-playing widget ([Drive modes §5.6][dm-5.6],
[Drive modes §9][dm-9]), the `camera_live` template ([App model §4.4][am-4.4]) and the
climate device page ([UI §6][ui-6]).

**Two install shapes.** Every head-unit app asks once, in its setup flow, which shape the car
has: **"Ostler is the head unit"** (the Brain makes the sound, tunes the radio and draws the
cameras) or **"Ostler sits beside my head unit"** (the old unit keeps media; Ostler shows
now playing where it can and hides the rest). "Ostler is the head unit" is offered, never
the default (decided, item 55). This mirrors Phone's "Ostler is the hands-free" choice
([Phone §3][pc-3]).

## Feature map: every standard head-unit page, mapped to an app

| Head-unit page or feature (aftermarket units) | Ostler app | Screens (this brief) |
|---|---|---|
| FM and AM tuner, band switch, frequency dial | app:radio | `radio-now-playing`, `radio-tune` |
| DAB+ tuner, service list, ensembles | app:radio | `radio-stations`, `radio-now-playing` |
| Station list with logos | app:radio | `radio-stations` |
| RDS: PS name, RadioText, PTY, TA, AF | app:radio | `radio-now-playing`, `radio-settings` |
| DAB DLS text and slideshow (SLS) | app:radio | `radio-dab-slideshow` (Parked) |
| Presets (memory buttons) | app:radio | `radio-presets` |
| Seek, scan, manual tune | app:radio | `radio-tune` |
| Traffic announcement interrupt | app:radio + OS alert pipeline | `radio-ta-alert` |
| Tuner hardware, antenna | app:radio | `radio-setup-tuner`, `radio-setup-antenna` |
| Source button (Radio, USB, Bluetooth, AUX) | app:audio | `audio-sources` |
| Graphic EQ (10 to 31 bands) with presets | app:audio | `audio-eq-graphic`, `audio-eq-presets` |
| Parametric EQ | app:audio | `audio-eq-parametric` |
| Loudness, bass boost, tone | app:audio | `audio-sound` |
| Balance and fade with a car diagram | app:audio | `audio-balance-fade` |
| Crossover (high-pass, low-pass per channel) | app:audio | `audio-crossover` |
| Time alignment by listening position | app:audio | `audio-time-alignment` |
| Subwoofer level, phase, crossover | app:audio | `audio-subwoofer` |
| DSP or amplifier setup | app:audio | `audio-setup-output`, `audio-setup-channels` |
| Speed-dependent volume, beeps, ducking | app:audio | `audio-volume-rules` |
| Key beeps, chimes, alert sounds | os | `audio-system-sounds` |
| Now playing (USB, SD, network) | app:media | `media-now-playing` |
| File browser (USB stick, SD card, network share) | app:media | `media-browse` |
| Queue, shuffle, repeat | app:media | `media-queue` |
| Bluetooth audio (A2DP) with track info (AVRCP) | app:media | `media-bluetooth` |
| Video player (Parked) | app:media | `media-video` |
| Streaming services | integrations used by app:media | `media-integrations`, `media-integration-setup` |
| Media in a Drive home page or split screen | OS template, app data | `media-moving` |
| Reverse camera on the reverse wire | app:camera (template is OS) | `camera-reverse` |
| Parking guidelines (static or dynamic) | app:camera | `camera-setup-guidelines` |
| Parking sensor overlay | app:camera | `camera-reverse` (where a sensor exists) |
| Front and underbody cameras (off-road) | app:camera | `camera-offroad` |
| Multi-camera view (360-style grid) | app:camera | `camera-multi` (Parked) |
| Dashcam and recording | app:camera | `camera-dashcam` |
| Clock, alarm, timer | app:widgets-starter (item 53) | `clock-page`, `clock-alarm-ring` |
| Weather | app:widgets-starter (item 53) | `weather-page` |
| Voice assistant, push-to-talk | app:voice (local-first, item 54) | `voice-assistant` |
| Steering-wheel control learning | os (input) | `swc-adapter`, `swc-learn`, `swc-assign` |
| Android Auto and CarPlay | not built (item 38): keep a projection head unit | `projection-setup` (information only) |
| Climate screen | os template, pack or device data | `climate-panel` |
| Car settings (doors, lights, suspension) | a Car app, later (item 40); pack data | `vehicle-settings-pack` |
| Phone (hands-free, contacts) | app:phone | Phone pages exist (`phone-page` and siblings) |
| Navigation | app:navigation | Navigation pages exist (`nav-page` and siblings) |
| Launcher, wallpaper, widgets, themes | os | the launcher brief (45-launcher files) |
| App store | os (the Store, a system app) | the Store brief (70-store files) |
| Factory settings, CAN-box car model | os | outside these apps; CAN-box emulator is a device |

Every app also has an **App info** page in system Settings (the app framework brief,
90-appframe files). Each file here gives the app's **setup flow** (first run) and its
**settings** page, and lists the widgets it adds to the launcher's widget picker gallery.

## Shared rules for every head-unit app

1. **Moving uses the OS's `media` template** for Radio, Media and Bluetooth audio: title and
   artist ≤ 30 characters each, static artwork, play or pause, skip, volume; browsing only as
   one `short_list` of ≤ 6 rows; no lyrics, no video, no scrolling text
   ([UI §12.1][ui-12.1]). The app supplies data; the OS draws it. Every task ends back on
   the Drive home page within 3 screens.
2. **Long lists are Parked only.** The full station list, the file browser, the queue and
   search are Parked (or Idling with Park evidence, [UI §3.5][ui-3.5]). While Moving they
   become a `short_list` of ≤ 6 rows (presets, recent, favourites), one level deep.
3. **No video on driver-facing screens** except a driving camera in `camera_live` within its
   speed limit. Video files, DAB slideshows, album art that changes faster than a track, and
   projection video are Parked only ([UI §12.1][ui-12.1]; research
   [reg 109][dd-4.2], [NHTSA lockouts][dd-3.2]).
4. **No typing while Moving.** Station search, Wi-Fi share passwords, names: Parked only.
5. **Settings are Park to edit** on driver-facing displays. Volume, source and preset
   recall are allowed while Moving because they are equipment state ([UI §12.1][ui-12.1]).
6. **Safety stays with the OS.** The fault telltale, alarm alerts, the strip, More (the app
   drawer) and the Moving templates sit above every app. A camera or projection view never
   covers a red telltale; the OS draws an `alert_card` over it.
7. **Audio priority (OS mixer):** reverse-camera chime and red alarms > calls > navigation
   voice > traffic announcement > message read-out > media and radio > key beeps. The Audio
   app sets levels; the OS order cannot be changed by an app.
8. **Calm visuals:** tokens only, Material Symbols only, no glow on head units at night, no
   gradients or blur on head units, motion only for sheets and tab changes
   ([visual §1][vds-1], [visual §5][vds-5], [visual §6][vds-6]). Spectrum analysers and
   animated VU meters are Parked only and never glow.
9. **Honest hardware.** Each app shows only what the fitted hardware can do. The D2 has no
   CAN, no steering-angle sensor and no wheel buttons on the K-line, so dynamic guidelines and
   learned wheel keys depend on add-on hardware and say so in plain words.

## The audio path (draw once, reuse in setup)

A diagram card used by `audio-setup-output`: **Sources** (Radio tuner, Media files,
Bluetooth phone, Navigation voice, Phone calls, System sounds) → **Brain mixer** (priority
and ducking, rule 7) → **Audio processing** (EQ, crossover, time alignment; on the Brain or
an external DSP) → **Output device** (CarPiHAT PRO 5's DAC, an I²S DAC HAT, a USB DAC, or a
DSP over USB or Bluetooth) → **Amplifier** → **Speakers** (front left and right, rear left
and right, subwoofer). The hardware research lists the CarPiHAT PRO 5 as the dev-kit car
power board, with a DAC ([hardware research][hw]).

## Open questions (whole set)

1. **Decided (item 53):** Clock and Weather are part of the starter widget pack; their
   pages have the owner `app:widgets-starter`. `app:voice` stays an app (item 54);
   `app:projection` does not exist, since projection is not built (item 38).
2. **Decided (item 54):** voice control is allowed; the input spec's non-goal is lifted,
   and the assistant is local-first, later.
3. **Decided (item 55):** "Ostler is the head unit" is offered, not the default.

[ui-1]: ../../../../specs/2026-10-06-ui-architecture-design.md#1-context-and-goals
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-5.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[si-1]: ../../../../specs/2026-10-07-shell-input-design.md#1-goals-and-non-goals
[pc-3]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#3-architecture
[pd]: ../../../../specs/2026-10-06-platform-direction-design.md#displays-are-thin-clients-cameras-live-on-our-infrastructure
[dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[dd-3.2]: ../../../research/driver_distraction_rules.md#32-numbers-and-lockouts
[hw]: ../../../research/hardware.md#development-kit-recommended-parts-250-plus-the-pi
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[hu-2]: ../../../../specs/2026-10-07-head-unit-apps-design.md#2-every-standard-page-mapped
[hu-11]: ../../../../specs/2026-10-07-head-unit-apps-design.md#11-projection-android-auto-carplay-open
