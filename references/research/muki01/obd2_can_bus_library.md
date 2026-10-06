---
title: "muki01 OBD2_CAN_Bus_Library: audit and feature inventory"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/canbus_headunit.md]
summary: >
  An end-to-end audit of muki01/OBD2_CAN_Bus_Library (ESP32 TWAI, OBD-II over ISO 15765-4, single-frame only): GPL-3.0 since 2026-10-03, but the identical source is MIT at 3dfba62. It covers Mode 01/02 (96 PIDs), 03/07, 04, the support bitmaps and an untested Mode 09. It has no ISO-TP, no listen-only mode, first-ECU-only replies and several decode and memory bugs, so Ostler takes facts and test ideas from it (clean-room against J1979 and OBDb SAEJ1979), not code.
---

# muki01 OBD2_CAN_Bus_Library: audit and feature inventory

Source: <https://github.com/muki01/OBD2_CAN_Bus_Library>, read in full at `58d69ce`
(2026-10-04). It has 63 commits. The only code is `src/OBD2_CanBus.{h,cpp}` (121 + 728
lines), plus seven example sketches, an Arduino-CLI compile CI and community files.
The paired firmware `muki01/OBD2_CAN_Bus_Reader` (`29fece7`) was read briefly.

## 1. What it is

| | |
|---|---|
| Purpose | Arduino library: OBD-II over CAN (ISO 15765-4) on the **ESP32's built-in TWAI controller** plus a TJA1050/SN65HVD230 transceiver. ESP32 only (`<driver/twai.h>`), although `library.properties` says `architectures=*` |
| Size | One class, `OBD2_CanBus`, with about 35 public methods |
| Activity | Created 2025-07-03. Code work ran from July to September 2025. 2025-12-27 brought a small refactor, and 2026-01-01 added the CI. The 2026-07 to 2026-10 commits touch only the README and the licence. `library.properties` is at 1.0.1. Low and maintenance-only |
| Tests | **None.** CI only compiles the examples for `esp32:esp32:esp32`. The library is symlinked as `OBD2_KLine`, a copy-paste leftover. No unit tests, fixtures or replay |
| Hardware | ESP32 TWAI only. **No MCP2515**, MCP2518FD, SJA1000 or slcan. No CAN-FD |
| Related | `OBD2_CAN_Bus_Reader`, a GPL-3.0 firmware with a Wi-Fi web dashboard, **re-embeds the same code** as `CAN.ino` rather than using the library. `OBD2_KLine_Library` (GPL-3.0) is the K-line sibling. "OBD2 Diagnostic UI" is the web dashboard shared by both readers |

**Licence verdict.**
- The root `LICENSE` has been **GPL-3.0** since `b2f0c4e` (2026-10-03). The README offers a
  commercial licence on request. No file has a per-file header or SPDX tag.
- Before that commit the licence was **MIT** ("Copyright (c) 2025 Muksin Muksin"), from
  the initial commit `a366781` up to and including `3dfba62` (2026-07-10).
- `git diff 3dfba62 HEAD -- src examples library.properties` is **empty**. Every line of
  code and every example is therefore available under MIT from `3dfba62`, and that grant
  cannot be withdrawn.
- **For Ostler:** code may be ported from the `3dfba62` snapshot with the MIT notice and
  `(c)` line kept (pin the SHA in `THIRD_PARTY_LICENSES.md`). Never port from HEAD under
  GPL-3: ADR-0019 (c) keeps GPL-3 out of core because it breaks the commercial dual
  licence.
- **In practice there is nothing worth porting.** The PID formulas are SAE J1979 facts that
  OBDb SAEJ1979 already carries under CC BY-SA. The C++ is ESP-IDF/Arduino-bound and has
  the bugs listed in §3–4. Treat it as **facts-only, clean-room**.
- `OBD2_CAN_Bus_Reader` is GPL-3.0 at HEAD; its MIT history was not checked. Use facts
  only.

## 2. Architecture and API

A single stateful class with fixed-size internal buffers and Arduino `String` results.
It runs one request at a time and blocks until a reply or a timeout.

| Group | Methods | Notes |
|---|---|---|
| Setup | `OBD2_CanBus(rx, tx)`, `setDebug(Stream&)`, `setProtocol("Automatic"\|"11b500"\|"29b500"\|"11b250"\|"29b250")`, `setReadTimeout(ms)` (default 200) | `setProtocol` tears the driver down |
| Connect | `initOBD2()`, `testConnection()`, `initTWAI()`, `stopTWAI()` | Auto-detect tries 11b250 → 29b250 → 11b500 → 29b500 and sends `01 00` on each |
| Raw | `writeData(mode, pid)`, `writeRawData(canMessage)`, `readData()`, `compareData(canMessage)` | `canMessage{id, rtr, ide, length, data[8]}`; `compareData` matches the last reply against an expected frame |
| Live / freeze | `getPID(mode, pid)`, `getLiveData(pid)`, `getFreezeFrame(pid)` → `float` | Error sentinels `-1` (no reply), `-2` (wrong PID), `-4` (unknown PID) are **in-band floats** |
| DTC | `readStoredDTCs()`, `readPendingDTCs()`, `readDTCs(mode)`, `getStoredDTC(i)`, `getPendingDTC(i)`, `clearDTC()` | 32-slot `String` buffers |
| Vehicle info | `getVehicleInfo(pid)` for `02` VIN, `04` CALID and `06` CVN | Marked `//Not Tested` in the source |
| Support scan | `readSupportedData(mode)` plus wrappers for 01, 02, 05, 06, 08 and 09; `getSupportedData(mode, i)` | Walks the `00/20/40/60/80` bitmaps |
| Link health | `updateConnectionStatus(bool)` | Three missed replies → `stopTWAI()`, "connection lost"; the next `initOBD2()` re-detects |

**Examples:** GetLiveData, GetFreezeFrame, ReadDTC, ClearDTC (clears in `setup()` with no
prompt), GetVehicleInfo, GetSupportedPIDs, TestAll. **Reader firmware:** a Wi-Fi AP or STA
with an async web server and WebSocket JSON. A page-driven poll loop reads only what the
open page needs: DTCs every 1 s, the user's "desired" live PIDs, distance with MIL on, and
freeze frame when DTCs exist. It adds battery voltage from an ADC (16× oversampling plus
an EMA with α 0.01), buzzer and LED cues, SPIFFS settings and an OTA handler.
`GET /api/clearDTCs` clears DTCs with **no confirmation and no state gate**.

## 3. CAN and ISO-TP details

| Topic | What the code does | Verdict |
|---|---|---|
| Controller | ESP32 TWAI; `TWAI_MODE_NORMAL`; `TWAI_FILTER_CONFIG_ACCEPT_ALL`; RX queue 60, TX queue 10; the driver is installed and uninstalled for every protocol trial | No `TWAI_MODE_LISTEN_ONLY`, no hardware filter, no alerts, and no bus-off or error-counter handling |
| Bitrates | 250 and 500 kbit/s, which are the ISO 15765-4 set | Fine. **Probing transmits at a guessed bitrate in normal mode, 250k first.** On a 500k vehicle bus this injects error frames. ISO 15765-4 says to detect the rate passively first. This breaks ADR-0020 |
| IDs | 11-bit `0x7DF` (functional); 29-bit `0x18DB33F1` (functional) | Functional addressing only; **no physical request** (`0x7E0`–`0x7E7`, `0x18DA xx F1`) |
| Accepted replies | `0x7E8`, `0x18DAF110` and `0x18DAF111` only | **First matching frame wins.** `0x7E9`–`0x7EF` and other 29-bit sources are dropped. Late replies from a second ECU stay in the queue and can be read as the answer to the *next* request, because the queue is never flushed before a request |
| Request frame | `[len, mode, pid, 0…]`, DLC 8, padded with `0x00`. Length 1 for 03/04/07, 3 for 02/05 (frame 0), else 2 | Acceptable. ISO 15765-4 allows any padding; `0x55`/`0xAA` are common |
| ISO-TP | **None.** The library never parses a First Frame or Consecutive Frames and never sends a Flow Control (`0x30`) | Mode 09 VIN and CALID, more than 2 DTCs, and multi-PID requests cannot work |
| Timing | One timeout (default 200 ms) per frame; TX blocks up to 1 s | No P2/P2* handling, no NRC `0x78`, no inter-request spacing |
| Multi-ECU | Not supported (see accepted replies) | Ostler needs per-ECU replies to enumerate systems (`vehicle_data_model.md` §detect) |

## 4. Services and PIDs, against OBDb SAEJ1979

**Services implemented.** `01` live (96 PIDs) · `02` freeze frame (same table, frame 0
only) · `03` stored and `07` pending DTCs · `04` clear · `09` `02/04/06` (broken, see
below) · support bitmaps for `01/02/05/06/08/09`. Constants are defined for `05` and `0A`
but no reader exists. Mode `06` test results are not decoded, only listed as supported.
Mode `08` only reads the support bitmap and never sends a control request. **No UDS**,
no manufacturer PIDs or DIDs, and no J1979-2 (OBDonUDS, `22 F4xx`).

**Defects that matter for anyone reusing the facts:**

| # | Where | Defect |
|---|---|---|
| D1 | `readDTCs` | The loop `for (i=0; i<len; i+=2)` indexes `data[2+i*2]`, a **4-byte stride**, so every second DTC is skipped and the read can run past `data[7]`. The J1979 CAN count byte after `0x43` is not handled. Their own example `07 43 01 70 01 34 00 00` returns `P0170` and drops `01 34` |
| D2 | `getVehicleInfo` | It sends no Flow Control and does a single `readData()`, then reads `data[i+3+j*8]` up to index 39 of an **8-byte array** (an out-of-bounds read). VIN and CALID cannot work on a real ECU. CALID and CVN counts come from `data[3]` of a different reply |
| D3 | `readSupportedData` | It writes up to 160 supported-PID entries into **32-entry arrays** (a buffer overflow on any ECU with more than 32 PIDs, which is most of them). `pidIndex` desyncs if a group gets no reply |
| D4 | `getPID` | Sentinels `-1/-2/-4` collide with valid negatives: fuel trims, timing advance and torque (`A−125`) |
| D5 | PID `23` | Uses `÷10`. J1979 and OBDb say `×10` kPa |
| D6 | PIDs `32`, `54` | Decoded as unsigned. Both are **signed** (OBDb `sign: true`) |
| D7 | PID `50` | Returns `A`. It should be `A×10` g/s |
| D8 | PIDs `14–1B`, `24–2B`, `34–3B`, `08/09`, `55–58`, `4F`, `01`, `03`, `13`, `1D` | Only byte A or the first field is returned. STFT per sensor, wideband V and mA, banks 3/4, the max-value fields, **readiness bytes B–D** and fuel system 2 are all lost. PID `01` is returned raw (MIL plus count, undecoded) |
| D9 | Freeze frame PID `02` | Returns `A` only. The DTC that stored the frame is two bytes |
| D10 | `readDTCs(invalid)` | Returns `-1` through a `uint8_t`, which reads as 255 |

**Coverage diff** against `OBDb/SAEJ1979` `signalsets/v3/default.json` (103 commands, 294
signals, Mode 01 only, header `7E0`):
- **Has, OBDb lacks:** `16 17 1A 1B` (O2 voltage, sensors 3/4/7/8) and `25–2B`, `35–3B`
  (wideband sensors 2–8). All are standard J1979 PIDs that OBDb has not listed. Their
  formulas (`A/200` V; `(256A+B)/32768` λ) are J1979 facts. Add them to our
  `generic_obd2` table from the J1979 text, citing the standard and not this repo.
- **OBDb has, they lack:** `64–72` and `7F` (torque, MAF/ECT/IAT multi-sensor, EGR, boost,
  wastegate, run-time support), `84` (manifold surface temperature), `8D 8E`, `9A` (hybrid),
  `9D 9E 9F`, `A2` (cylinder fuel rate), **`A6` odometer**, `AA` (speed limiter), `B2`
  (battery SOH), `D2 D3`. They also lack every multi-field signal (see D8).
- **Agreements:** the other 78 shared PIDs use the same scale and offset as OBDb.
- **OBDb data to double-check** while importing (not their bug): `24` `O2S11_VOLT div:
  8196` (J1979 implies 8192) and `5D` `add: -38665` (J1979: `(256A+B)/128 − 210`).
- **Not in OBDb at all:** Modes 02/03/04/06/07/09/0A. Ostler must write these in its own
  J1979 service layer anyway.

## 5. Against Ostler's plans

- **Link layer.** ADR-0020 calls for a frame-level `CanLink` with listen-only by default and
  `IsoTpChannel` (kernel `CAN_ISOTP`, userspace can-isotp MIT elsewhere). Today Ostler
  has neither; `src/openostler/transport/` has byte `Transport`s only. muki01's library is
  the ADR's **anti-pattern**: normal mode, transmit-probing at guessed bitrates, accept-all
  filters, no ISO-TP. Its one useful link idea is the protocol matrix
  `{11,29} × {250,500}` with fixed functional IDs. Ostler should detect the bitrate
  **listen-only first** (count valid frames per rate), then send one Tier 0 `01 00`.
- **Request discipline.** ADR-0020 Tier 0 sets one request in flight, ≥ 50 ms per ECU and
  backoff on NRC `0x21`/`0x78`. The library has the first rule only by accident (blocking)
  and lacks the rest. Ostler's `kwp2000.py` already handles `0x78` (`_resolve_pending`),
  and that logic carries over to a CAN `ObdService`.
- **Multi-ECU.** Ostler's detect flow (`vehicle_data_model.md`) enumerates `7E8`–`7EF` from
  the functional `01 00` reply. The library does not.
- **Data.** ADR-0019 makes OBDb the primary polled-data source for `generic_obd2`; this repo
  adds nothing beyond the 18 PIDs above. VSS (ADR-0016): `vss/ostler.vspec` already has
  `Vehicle.Ostler.Diagnostics.{IsMilOn, DtcCount, PendingDtcCount, IsReadinessComplete,
  ReadinessIncompleteCount}`. Those need full PID `01` decoding (D8), which the library
  skips.
- **Safety.** Mode 04 is a **Tier 1 "clear"** action (UI spec §7: Parked, one confirm, offer
  a report first, re-read to verify). Both the ClearDTC example and the Reader's
  `GET /api/clearDTCs` are what Ostler forbids: a clear on a GET, ungated, unconfirmed and
  remote-capable.
- **Privacy.** `getVehicleInfo(0x02)` returns the VIN in clear text and the debug stream
  prints every frame. Ostler's rule (`decode_pipeline.md` §1.3) is local decode only:
  never log the VIN and redact Mode 09 `02` in captures.
- **Firmware.** The Reader's ESP32 + transceiver + ADC-battery design matches
  `ostler-firmware` ESP32 nodes. The ADC EMA and the "page-driven polling" (poll only what
  is on screen) are good ideas. Ostler's equivalent is the per-state `rate` in the
  manifest plus demand-driven subscription.

## 6. Feature inventory

Tiers: read = Tier 0, clear = Tier 1 (ADR-0018 / UI spec §7). Reuse: "facts" = clean-room
from J1979 and OBDb. The `3dfba62` MIT snapshot would allow a port, but none is
recommended.

| feature | where in their code | Ostler has it? | where it lands | safety tier | reuse | effort |
|---|---|---|---|---|---|---|
| ESP32 TWAI driver bring-up (pins, queues, timing) | `initTWAI`, `stopTWAI` | no | ostler-firmware (ESP32 CAN node, slcan/GVRET to `CanLink`) | read | facts | S |
| Listen-only mode | absent (normal mode only) | no (ADR-0020 plans it) | platform `CanLink` (`listen_only=True` default) + firmware `TWAI_MODE_LISTEN_ONLY` | read | n/a | S |
| Bitrate/ID-width auto-detect `{11,29}×{250,500}` | `initOBD2`, `testConnection` | no | platform `CanLink` detect: **passive** rate sniff, then one `01 00` probe; U4 | read | facts (redesigned) | M |
| Manual protocol override | `setProtocol` | no | platform link config; UI More › Devices link chip, U4 | read | facts | S |
| Functional request 0x7DF / 0x18DB33F1 | `writeData` | no | platform `IsoTp`/`ObdService` | read | facts (ISO 15765-4) | S |
| Physical addressing 0x7E0–7 / 0x18DAxxF1 | absent | no | platform `IsoTp` | read | facts | S |
| Reply-ID filter (0x7E8, 0x18DAF110/11) | `readData` | no | platform `CanLink.set_filters` (all `7E8–7EF`, `18DAF1xx`) | read | facts | S |
| Multi-ECU replies | absent (first frame wins) | no | platform `ObdService` collects per ECU; Diagnose system list, U4 | read | n/a | M |
| ISO-TP FF/CF/FC | absent | no | platform `IsoTpChannel` (kernel `CAN_ISOTP`; can-isotp MIT) | read | n/a | M |
| Raw frame send and expected-frame compare | `writeRawData`, `compareData` | partly (K-line raw only) | platform `CanLink.send` behind the allowlist; More › Developer, U7 | code (TX outside the allowlist) | facts | S |
| Frame debug trace to a stream | `setDebug`, `debugPrint*` | yes (`LoggingTransport` JSONL) | platform `LoggingCanLink` (JSONL + candump) | read | n/a | S |
| Link-lost after 3 timeouts | `updateConnectionStatus` | partly (K-line keepalive) | platform `ObdService` health → status strip link chip, U1/U4 | read | facts | S |
| Configurable read timeout | `setReadTimeout` | yes (K-line) | platform `IsoTp` P2/P2* config | read | n/a | S |
| Mode 01 live PIDs (96, single-value) | `getPID` | no | generic_obd2 pack (OBDb SAEJ1979 import); Home/Diagnose › Live, U4 | read | facts (OBDb is the source) | M |
| Extra O2 PIDs `16 17 1A 1B 25–2B 35–3B` | `getPID` | no | generic_obd2 pack overlay (from J1979; offer upstream to OBDb) | read | facts | S |
| Multi-field PIDs (STFT per sensor, banks 3/4, wideband V/mA) | missing (D8) | no | generic_obd2 pack (OBDb has them) | read | n/a | S |
| PID 01 MIL / DTC count / readiness decode | raw `A` only | partly (VSS leaves exist) | generic_obd2 + `Vehicle.Ostler.Diagnostics.*`; Home health card, U4 | read | facts | S |
| Mode 02 freeze frame (frame 0) | `getFreezeFrame` | no | generic_obd2; logbook event on Logs, fault → snapshot on Diagnose, U4 | read | facts | M |
| Freeze-frame trigger DTC (PID 02) | wrong (D9) | no | generic_obd2 | read | facts | S |
| Mode 03 stored DTCs | `readStoredDTCs` (buggy, D1) | no (KWP DTCs only) | platform J1979 service + generic_obd2 `dtc_sources: obd_03`; Diagnose › Faults, U4 | read | facts | S |
| Mode 07 pending DTCs | `readPendingDTCs` | no | as above, `obd_07`; `PendingDtcCount` | read | facts | S |
| Mode 0A permanent DTCs | constant only | no | as above, `obd_0a` | read | facts | S |
| DTC 2-byte → `P/C/B/U` + 4 hex decode | `decodeDTC` | partly (`dtc/` meaning store; no J1979 decoder) | platform `dtc` J1979 decoder + generic meanings table | read | facts (SAE J2012) | S |
| Mode 04 clear DTCs | `clearDTC`, ClearDTC example, Reader `GET /api/clearDTCs` | partly (KWP `14` gated) | generic_obd2 action `clears`; Diagnose › Faults, Parked + confirm + report-first + re-read; U2/U4 | **clear** | facts | S |
| Mode 09 VIN | `getVehicleInfo(0x02)` (broken, D2) | partly (KWP identity, redaction) | platform service + local VIN decode (never logged); Diagnose identity bar, U4 | read | facts | S |
| Mode 09 CALID / CVN | `getVehicleInfo(0x04/0x06)` | no | generic_obd2 identity / fingerprint (`decode_pipeline.md` S1); U4/U7 | read | facts | S |
| Mode 09 ECU name (`0A`), IPT (`08/0B`) | absent | no | generic_obd2; system names in Diagnose, U4 | read | n/a | S |
| Support bitmaps `00/20/…` for 01/02/06/08/09 | `readSupportedData` (D3) | no | platform `ObdService.supported()`; manifest generation (`generateViews()`), U3/U4 | read | facts | S |
| Mode 06 on-board test results | bitmap only | no | generic_obd2 (MID/TID tables); Diagnose › Tests, U4+ | read | n/a | M |
| Mode 05 O2 tests | constant only (non-CAN) | no | skip on CAN; K-line ISO 9141 generic pack later | read | n/a | S |
| Mode 08 control | bitmap only | no | listed only, Tier 2+ under its own review | actuate | n/a | n/a |
| Engineering-unit floats with in-band errors | `getPID` | n/a | **do not copy**: Ostler returns typed value + status | read | n/a | n/a |
| Page-driven polling (poll only what is shown) | Reader `obdTask` | partly (rate per driving state) | platform poll scheduler + UI subscriptions, U3/U4 | read | facts | M |
| Battery voltage via ADC (16× oversample + EMA) | Reader `readBatteryVoltage` | partly (PID 42 planned) | ostler-firmware node metric → `Vehicle.LowVoltageBattery.CurrentVoltage`, U5 | read | facts | S |
| Wi-Fi web dashboard + WebSocket JSON | Reader `WEB_SERVER.ino` | yes (React UI, SSE) | n/a | read | none | n/a |
| OTA / SPIFFS settings | Reader | partly (firmware plan) | ostler-firmware | code | facts | M |
| Vehicle-report issue form (make/model/year/protocol) | `.github/ISSUE_TEMPLATE/vehicle_report.yml` | no | Ostler repo issue form for generic_obd2 coverage, U4/U7 | n/a | facts (idea) | S |
| Compile-only CI for examples | `arduino-ci.yml` | n/a (pytest + vcan) | ostler-firmware CI (compile + host tests) | n/a | facts | S |

## 7. Recommendations

1. **Licence:** treat the repo as facts-only. Record in `THIRD_PARTY_LICENSES.md` notes
   that it was MIT to `3dfba62` and GPL-3.0 from `b2f0c4e`, and that no code was taken.
2. **Build the CAN path from ADR-0020, not from this library.** Add `SocketCanLink`
   (listen-only default), then `IsoTpChannel` (kernel), then a J1979 `ObdService` with
   functional broadcast, per-ECU collection, physical follow-ups, Flow Control, P2/P2*,
   NRC `0x78`/`0x21` backoff and ≥ 50 ms spacing.
3. **Passive bitrate detection.** Before any transmit, open listen-only at 500k, then 250k,
   and accept the rate with clean frames and no error counters. Only then send `01 00`.
   On a quiet bus (gateway OBD ports), probe 500k first with a single frame, Parked only.
   Write this as a spec item; it refines ADR-0020's Tier 0 exception.
4. **J1979 service layer test vectors.** Turn each defect D1–D10 into a pytest fixture so
   our decoder is proven where theirs fails: a DTC reply with a count byte and 3+ DTCs
   (multi-frame), a VIN over FF/CF/FC, a 0x7E8 + 0x7E9 double reply, signed PID `32`/`54`,
   PID `23 ×10`, `50 ×10`, and more than 32 supported PIDs.
5. **generic_obd2 data:** import OBDb SAEJ1979 (ADR-0019). Add the 18 standard O2 PIDs
   OBDb lacks from J1979 as `candidate`, check OBDb's `24` (8196) and `5D` (−38665)
   entries, and contribute fixes upstream.
6. **Mode 04** ships only as a Tier 1 `clears` action: Parked, one confirm naming the
   consequence (readiness and freeze frames lost), offer a report first, and re-read
   03/07/01 after. Never on GET and never remote.
7. **VIN:** decode Mode 09 `02` locally and redact it in `LoggingCanLink` and the trace, as
   for KWP `1A`.
8. **Firmware:** an ESP32 TWAI node in `ostler-firmware` exposes slcan/GVRET to `CanLink`
   with `TWAI_MODE_LISTEN_ONLY` as the boot default and TX enabled only by a signed host
   command. It reuses the ADC-EMA battery idea.
9. **Do not adopt:** in-band float error codes, the accept-all filter, transmit-probing, or
   first-frame-wins reply matching.

**ADR candidates.** (a) No new ADR is needed for licence handling; ADR-0019 (c) already
covers GPL-3. (b) **Passive bitrate detection before the first Tier 0 probe** should be
an amendment or follow-up to ADR-0020, because its Tier 0 exception currently allows a
diagnostic request in every state with no rule about an unknown bitrate. (c) Mode 04
classification is already settled (UI spec §7 Tier 1); confirm that `generic_obd2`
inherits it in the U4 spec.
