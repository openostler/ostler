---
title: "Feature backlog from the research — tagged core / add-on / moonshot"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/platform.md, references/research/landscape.md]
summary: >
  Ideas the research surfaced, each tagged core / add-on / moonshot with the open-source project to build on: TPMS via rtl_433, Meshtastic convoy tracking, GoPro telemetry sync, dashcam ingest, log-format import/export, OVMS/OwnTracks interop, CAN intrusion detection, camera streaming, lap timing, and more. A parking lot, not a commitment — each needs a spec.
---

# Feature backlog from the research

This is a parking lot, not a commitment. Each item needs a spec (and an ADR if it adds an
outbound data path, a tab or a dependency) before any code. The platform guardrails apply
([platform.md](platform.md) §6).

**Tags:**

| Tag | Meaning |
|---|---|
| **core** | Strengthens the reason the product exists: diagnostics, logging, honest data |
| **add-on** | Optional integration or module that is off by default |
| **moonshot** | Large, risky, or needs hardware we don't have yet |

| # | Feature | Tag | Builds on (licence) | Notes |
|---|---|---|---|---|
| 1 | **Speak OVMS v3 MQTT topics** | add-on | Topic layout reimplemented from [ovms.md](ovms.md) | The ovms-home-assistant integration and OVMS Connect then work with our node. Cheap and high value. |
| 2 | **OwnTracks location JSON** | add-on | OwnTracks protocol | Dawarich, Reitti and HA's OwnTracks integration then work. Location is opt-in (ADR-0009). |
| 3 | **Traccar OsmAnd upload with backfill** | add-on | Traccar (Apache) | Replays the logbook when coverage returns |
| 4 | **ntfy / Telegram / SMS notifier ladder** | add-on | ntfy, Telegram Bot API, modem AT commands | Owned by the guardian |
| 5 | **TPMS** (pressure and temperature per wheel, slow-leak flag) | add-on | rtl_433 (Pi + RTL-SDR) / rtl_433_ESP (CC1101) (GPL, ✓ since ADR-0012) | Sensor IDs also give a "known vehicle" fingerprint. Feeds automatic flags. |
| 6 | **Meshtastic convoy tracking** off-grid | add-on | Meshtastic firmware / python (GPL-3 ✓) | Positions without cell coverage, relayed to HA through OwnTracks once back online. Good for overlanding. |
| 7 | **Camera streams in the PWA** | add-on | go2rtc / MediaMTX (MIT), ESP32-CAM_MJPEG2SD (AGPL ✓) | Wi-Fi cameras; alarm-triggered clips |
| 8 | **Dashcam ingest** (BlackVue / Viofo / Tesla) | add-on | blackclue (Apache), tesla_dashcam (Apache), dashcamigo (AGPL ✓) | GPS and G-force from clips attached to flags and alarm events |
| 9 | **GoPro / action-camera sync** | add-on | gpmf-parser (Apache), gopro-telemetry (MIT), OpenGoPro BLE (MIT) | Starts recording at a lap or alarm; merges GPMF data into replay; aligned by GPS time |
| 10 | **Log import**: AiM XRK, MoTeC .ld, RaceCapture, TunerStudio .mlg | core | TrackDataAnalysis (MIT), motec-i2 (MIT), mlg-converter (MIT) | Lets users switch to us, and compare data across tools |
| 11 | **Log export**: MoTeC .ld, RaceChrono BLE, RealDash CAN | core | ldparser (GPL ✓), RaceChrono BLE spec, RealDash-extras (Unlicense) | Users keep their favourite dash or analysis app |
| 12 | **Lap / segment timing** with start-finish lines and delta | add-on | Turf.js (MIT), DovesLapTimer (GPL-3 ✓), TUMFTM track DB (LGPL) | Fast-F1-style delta plots ([UX ref](https://github.com/theOehrly/Fast-F1)) |
| 13 | **Spoken callouts** (flags, faults, lap delta) | add-on | CrewChief (MIT) as UX reference | Uses the phone's text-to-speech in the PWA |
| 14 | **Time-limited location share link** | add-on | Hauk (Apache) as reference | "Where's the Land Rover" link that expires |
| 15 | **CAN intrusion check** (unknown IDs, timing anomalies) as an alarm trigger | moonshot | ICSim (GPL ✓), CAN-MIRGU dataset | Only once we're on CAN cars |
| 16 | **`generic_obd2` pack** | core | OBDb SAEJ1979 (CC BY-SA), mdabrowski1990/uds (MIT) | Proves the platform is universal ([platform.md](platform.md) §2) |
| 17 | **Rover 14CUX / MEMS packs** | add-on | libcomm14cux, librosco (GPL-3 ✓) | Classic Range Rover and Rover V8 owners |
| 18 | **Discovery 3/4 collaboration** | core | jlr-scanner (AGPL ✓) | Shared vehicle packs rather than a rewrite |
| 19 | **Discover undocumented LR ECUs** | core (developer) | CaringCaribou (GPL-3 ✓) | Scans which services and IDs an ECU answers, read-only |
| 20 | **Web Bluetooth path to the PWA** | moonshot | esp32-isotp-ble-bridge (MIT), niro-spy pattern | Phone talks to an ESP32 bridge directly, with no Pi |
| 21 | **SignalK-style data model** | core (design) | SignalK (Apache) | Its path/metadata scheme is a model for our metric namespace |
| 22 | **Head-unit CAN-box emulator module** | add-on | esp32-canbox-nissan (MIT), canbox (⚠️ reference only) | Old car → new head unit (the "CAN/OBD emulator" module) |
| 23 | **Relay-box module** on the private CAN bus | add-on | Waveshare 8DI-8RO-C, ESPHome | Outputs are gated like any other action |
| 24 | **ODX import** | moonshot | odxtools (MIT), OpenSOVD (Apache) | Only from files the user owns; never shipped (DMCA lesson) |
| 25 | **Cloud** (hosted sync, fleet, remote access) | moonshot | — | Funding route (ADR-0012). Fully AGPL or open-core: still an open question. |
| 26 | **Display as thin client**: the PWA in kiosk mode on any tablet, phone or head-unit browser | core | Existing PWA | The owner's direction (direction spec v0.2). No CAN-box work needed. |
| 27 | **Ostler Android launcher**: auto-start, camera view on reverse, CarPlay/AA via a wireless dongle (Carlinkit-type) | add-on | — | About 90% of a custom head unit. A custom ROM only if the launcher hits real limits. |
| 28 | **Camera system**: dashcam, parking/alarm clips, reversing, underbody; go2rtc + Frigate (Pi 5 AI HAT) | add-on | go2rtc (MIT), Frigate (MIT), ESP32-CAM_MJPEG2SD (AGPL ✓) | Constraints: reverse latency vs Pi boot, a pre-event buffer while parked, wired cameras for continuous recording |
| 29 | **Gauge display module**: an ESP32-S3 round/bar screen for always-visible coolant, boost, EAT temperature, flags and alarm state | add-on | Waveshare / LilyGO touch displays (£30–60) | Optional, alongside the main screen |
