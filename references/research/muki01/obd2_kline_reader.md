---
title: "muki01 OBD2_K-line_Reader and OBD2_KLine_Library: audit and feature inventory"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/landscape.md]
summary: >
  An end-to-end audit of muki01/OBD2_K-line_Reader (ESP32/ESP8266/AVR firmware: ISO 9141-2 and KWP2000 slow/fast init, J1979 modes 01/02/03/04/07/09, a Wi-Fi WebSocket dashboard) and its companion OBD2_KLine_Library v2 (adds KW1281, BMW DS2, Opel KW82 and a per-protocol timing table). The reader is GPL-3.0 since 2026-10-03 but its code is MIT at 91ae045; the library's current code carries non-commercial headers and is facts-only. Ostler's KWP2000 stack is more robust; the library's protocol breadth, profile-as-data design and the reader's J1979 scope are what we take, clean-room.
---

# muki01 OBD2_K-line_Reader and OBD2_KLine_Library: audit and feature inventory

Sources, read in full: reader `f8a09aa` and library `2906123` (both 2026-10-04, `--depth 50`;
library 2.0.0), including the decompressed `WebServer_Code/data/*.gz` UI, the six schematics
and the issue list (web page). Sibling: [obd2_can_bus_library.md](obd2_can_bus_library.md).

## 1. What it is

| | Reader (`OBD2_K-line_Reader`) | Library (`OBD2_KLine_Library`) |
|---|---|---|
| Purpose | Ready-to-flash scan-tool firmware with two builds. `Basic_Code` targets the serial monitor on AVR/ESP32. `WebServer_Code` targets ESP32/ESP8266 and adds a Wi-Fi AP/STA dashboard, WebSocket, REST and OTA | An Arduino library with a layered API: `KLine_Core` (bytes, pins, P-timings, init pulses), `KLine_Protocol` (framing, checksum, handshakes), `KLine_Functions`, and opt-in `ecus/OBD2_Standard` |
| Size | `K_Line.ino` (651–674 lines), `Functions.ino`, `PIDs.h` (136), `WEB_SERVER.ino` (274), `SPIFFS.ino`. UI: `index.html` (100 kB), `script.js` (26 kB), `errorCodes.js` (999 P-codes `P0000–P0999`) | `KLine_Protocol.cpp` (984), `OBD2_KLine_Core.cpp` (479), `OBD2_Standard.cpp` (423), six examples |
| Activity | Copyright 2023–2026. Protocol work ran to 2026-01-27 (`clearEcho(len)`, timing renames), the web UI and battery EMA landed in 2026-02, OTA in 2026-07. Since then only README and licence changes. 24 issues are visible, most open and unanswered | v1.x (2025-12 to 2026-01) had String protocol names. v2.0.0 (2026-08-26/30) rewrote the code into layers with KW1281/DS2/KW82. Arduino-CLI compile CI only |
| Tests | None | None. CI only compiles the examples |
| Closed parts | The UI source is in a separate repo (`OBD2-Diagnostic-UI`) and ships here as a build | ECU files for Simtec 71, ME7.5, M1.5.5, BMS 46 and EDC15VM+ are "available on request" and **not published** |

**Licence verdicts.**
- **Reader.** **MIT** ("Copyright (c) 2023 Muksin Muksin") up to `91ae045` (2026-10-01);
  **GPL-3.0** since `aef63b4` (2026-10-03), with a commercial licence offered. No file has
  a header. The last code change was `e0cb395` (2026-07-07), so every `.ino`/`.h` and the
  `data/` build are MIT at `91ae045`, irrevocably. Port only from that SHA with the
  notice, never from HEAD (ADR-0019 (c) keeps GPL-3 out of core).
- **Library.** MIT from `f08eec9` (2025-09-06) to v1.1.0 (`2becca2^`). From `2becca2`
  (2026-06-26) a custom **"Source-Available, non-commercial"** licence. The root `LICENSE`
  says **GPL-3.0** since `678e7f1` (2026-10-03), **but `KLine_Functions.cpp`,
  `OBD2_Standard.cpp` and the core/protocol headers still say "DUAL-LICENSED …
  COMMERCIAL: Mandatory paid license"**. The v2 code (KW1281, DS2, KW82, profile table)
  never existed under a clean licence: **facts-only, clean-room**. The MIT v1.1.0 tree has
  only ISO 9141/14230, a sniffer, and Honda CR-V 2003 / Opel Vectra B 2001 tables.
- **D2 vendored copy** (`discovery2-diag/references/muki01_OBD2_K-line_Reader/`) is
  `Basic_Code` at **`a1946a7` (2025-09-24), MIT**, byte-identical bar a trailing newline.
  Its README is wrong twice: the repo is not "removed from GitHub", and the PlatformIO
  link points at the **library**, not the reader.
- **Dealer lineage:** none seen. PID formulas are SAE J1979 facts. The DTC text has
  unknown provenance, so do not copy it. The Opel/Honda tables look like sniffs with
  unstated provenance: facts only, gated.

## 2. Architecture

**Reader.** A single-threaded `loop()`: `initOBD2()` while disconnected, else `obdTask()`,
then a WebSocket JSON push every 100 ms. `obdTask` is **page-driven**: the browser sends
`page0…page6` and only that page is polled (selected PIDs on Live, DTCs every 1 s on most
pages, freeze frame only when DTCs exist, speed only on page 4, vehicle info on page 5).
State is global (`resultBuffer[64]`, `String storedDTCBuffer[32]`, `supported*[32]`);
settings are key=value in SPIFFS. Three consecutive read timeouts mean link lost, then a
re-init.

**Library v2.** The protocol is a **data row** (`OBD2ProtocolConfig`): name, baud, serial
config, checksum type, verify flag, init type, init parity, init address, header
bytes, address index in the header, length mode (`None` / `SeparateByte` / `InHeader`),
length mask, length-includes-frame, P1–P4, W1–W4 and wake-up delay. The init method is
an orthogonal axis (`Init_5Baud | Init_Fast | Init_Ping | Init_None`). There are three
write levels: `writeData` (header, length and checksum added), `writeRawData` (checksum
only) and `sendBytes` (verbatim). There are three read framers: gap-delimited
`readData`, KW1281 `readBlock`, and a KW82 sliding-window `readPacket`. Errors are
in-band (`float` −1/−2/−4, `uint8_t` 0).

## 3. Protocols in depth

**Physical/byte layer (both).** UART 10400 8N1; init pulses are bit-banged on the TX GPIO
with the UART detached (`Serial.end()` → `digitalWrite`). **Echo:** `clearEcho(n)` reads
exactly *n* bytes (100 or 200 ms per-byte timeout) without comparing them, so collisions go
undetected. **P4** = 5 ms, none after the last byte. **P1:** end of response by gap, 60 ms
in the reader and 20 ms in the library, so a multi-ECU or multi-frame burst is **one
buffer** in the reader; the library's VIN read loops `readData()` per frame. **P2** =
1000 ms (far above ISO's 50 ms). **P3:** the library waits 57 ms after the last response
before every send; the reader relies on its 60 ms gap.

**ISO 9141-2 and KWP2000 slow init (5 baud).**
- **Pre-init idle:** 5.5 s line-high before *every* attempt, so a previous session times
  out (P3max 5 s), instead of ISO W5 ≥ 300 ms.
- **Address:** `0x33` at 200 ms/bit, start + 7 data bits LSB-first + parity + stop. The
  reader computes **even** parity; the library uses `Parity_Even` for 9141/14230 and
  `Parity_Odd` for KW1281/KW82. For `0x33` (four 1-bits) bit 7 = 0, equal to Ostler's 8N1
  `slow_init_bits`. For addresses with an odd number of 1-bits, even parity sets bit 7:
  exactly the bug Ostler removed on 2026-08-04 after `0x29`→`0xA9` failed. Record it as a
  known divergence; the ISO wording ("7 bits + odd parity") stays open in the D2
  init-timing slab.
- **Handshake:** read `55 KW1 KW2` with a 30 ms gap; ~KW2 goes out when the gap closes
  (no explicit W4, but it lands inside 25–50 ms). The reader expects `0xCC` (= ~0x33);
  the **library accepts any reply**.
- **Classification:** `KW1 == KW2` means ISO 9141-2 (08 08 / 94 94), otherwise KWP2000
  (for example 8F E9). The KWP key-byte bits are **not decoded**.

**KWP2000 fast init.** The line goes 25 ms low then 25 ms high (`delay()`, so ±1 ms on
the ESP32 loop core). Then `C1 33 F1 81 66` is sent, functional to 0x33 from tester
0xF1. Success means `resultBuffer[3] == 0xC1`, which assumes a 3-byte-header reply
`83 F1 11 C1 8F EF C4`. Key bytes are ignored. There is no tolerance for glitch bytes
before the reply, and no support for an unaddressed `03 C1 …` reply. Ostler's
`fast_init_tolerant` handles both. Auto-detect order: **reader** tries 5-baud first, then
fast. **Library** tries fast first, then one keyword-classified 5-baud round.

**Framing and checksums.**
- **ISO 9141-2:** `68 6A F1` (the reader uses `69 6A F1` for modes 02/05; check against
  J1979), no length byte, sum-mod-256; replies `48 6B <ecu>`. **KWP2000:** `Cx 33 F1`,
  length in the low 6 bits, sum-mod-256; no `0x80`+length form; physical `8x <addr> F1`
  only via the library's `setHeader`. The reader **never verifies reply checksums**
  (fixed offsets); the library does, except during the handshake.
- **KW1281 (lib):** 9600 baud, 5-baud 0x01 odd parity; blocks `len cnt data… 03`, every
  byte but the last acknowledged with its complement; counter tracked. No VAG group or
  fault service is published.
- **BMW DS2 (lib):** 9600 **8E1**, no init (a "ping" `12 04 00 cs`), DME 0x12, length
  byte counts the whole frame, XOR checksum.
- **Opel KW82 (lib):** 4800 baud, 5-baud 0x60 odd parity. The ECU streams one answer
  forever; a request changes which one. Frame `[N][payload][marker][cs]`,
  `cs = sum(first N bytes)` (marker excluded), read by a sliding window that asks "does a
  valid frame end here?" per byte (locks on from all 35 offsets, per the source).
- **Two's complement:** Honda's K-line format in the MIT v1.1 example, `20 05 00 02 D9`.

**Keep-alive.** There is **none**: no `3E` TesterPresent and no `82`
StopCommunication on exit or on a protocol change. The session stays alive only through
continuous polling. A Live page with no selected PIDs goes silent, and the link then drops
and re-inits after 5.5 s. **Auto protocol detection** covers 9141 / 14230-slow /
14230-fast only (KW1281/DS2/KW82 must be selected by hand). It is runtime-selectable and
persisted.

**Sniffer/emulator (lib).** `read5baud()` decodes a 5-baud address by sampling RX every
200 ms after a >100 ms low start bit, and reports parity. The MIT-era `Sniffer.ino`
dumps gap-framed bursts. The Honda/Opel sketches are **ECU simulators**: they compare the
request with a table and reply with a canned frame. In the Opel table a fast-init pulse
appears as a leading `0x00` byte (`00 81 11 F1 81`). That is a useful sniff signature.

## 4. Services and PIDs

| Mode | Reader | Library | Notes and defects |
|---|---|---|---|
| 01 live | ~95 PIDs `01–63` → `float` | same | **Partial formulas:** `14–1B` use A/200 only (STFT B ignored), `24–2B`/`34–3B` use the ratio only, `4F`/`50` use A only (`50` should be ×10), `23` is /10 (J1979 says ×10, a 100× error), and `32`/`54` are unsigned (they are signed). `01` returns A only, so **no readiness-monitor decode** (B/C/D are dropped). Sentinels −1/−2/−4 collide with real negatives (trims, −40 °C, timing) |
| 02 freeze frame | frame 0 only; on DTC presence | same | `02 02` (the DTC that stored the frame) is returned as A only; it is 2 bytes |
| 03 / 07 DTCs | parse pairs from offset 4 until `00 00` | same | One gap-framed burst holds several 3-DTC frames, so with 4+ DTCs **the next frame's header bytes decode as fake DTCs**. Multi-ECU replies merge |
| 04 clear | `clearDTCs()`; `GET /api/clearDTCs`; WS `clear_dtc`; one UI tap | `clearDTCs()` | **Ungated, unconfirmed, unauthenticated, works on GET**, and offers no re-read or report-first |
| 05 / 06 / 08 | support bitmap only | same | Mode 08 bitmap only; no control is exposed |
| 09 | VIN `02` (fixed 5 frames, fixed offsets), CALID `04` and CVN `06`, with the frame count read from `03`/`05` | VIN reads one frame per `readData` | The non-CAN message-count PIDs `03`/`05` are a correct J1979 detail. The VIN is shown in clear and printed to debug |
| 0A | constant only | constant only | none |
| Support bitmaps | `00/20/40/60/80` chained on the bit for the next block | same | **Overflow:** up to 160 supported IDs are written into 32-byte arrays |
| DTC format | `decodeDTC`: 2 bits → P/C/B/U, 2 bits + 3 nibbles | same | Correct J2012 two-byte form |
| DTC text | `errorCodes.js`: 999 entries `P0000–P0999` only (the README claims P/C/B/U) | none | Provenance unknown, so not taken |

Other defects: the reader's page 2 emits `liveDataMappings[32]` (PID `23`) as "Distance
with MIL on" (it should be index 30, PID `21`); `desiredLiveData[i]` has no bound check on
`/pidSelect`; and String-keyed protocol settings mean a typo silently disables headers.
The pre-2026-01 code (the D2 vendored copy) built headers from `selectedProtocol`, so in
**Automatic mode it sent frames without a header**. Upstream fixed this by switching to
`connectedProtocol`. That is the main correctness delta in the vendored copy.

## 5. Hardware

**Interfaces (six schematics, identical in both repos).**
- **Discrete transistor:** 2× BC547, 10 k bases, 510 Ω K pull-up; RX from a 10 k/3 k
  divider off pin 7 (3.3 V; R6 = 5.3 k for 5 V). No ESD, clamp or reverse-polarity
  protection; every "VCC" label is the 12 V net.
- **LM393/LM2903:** RX compares K against a 12 V/2 divider (5.6 k pull-up); TX drives K
  through an open-collector output with a 1 k pull-up.
- **L9637D:** VS pin 7 via 1N4148, 100 nF, 510 Ω pull-up, LI (pin 8) open. It matches the
  D2 `hardware/README.md`, which adds a 0.5 W pull-up and TVS/series R that muki01 lacks.
- **MC33290:** VBB from pin 16 with no diode, CEN to VDD. **Si9241AEY:** CS and FAULT
  unconnected. **SN65HVDA195 (LIN):** EN floating, NWAKE to GND as drawn; LIN parts
  usually have a TXD-dominant timeout that can cut a 200 ms 5-baud bit. Check the
  datasheets for all three.

**Boards and pins.** ESP32-S3/C3/C6: UART1 RX GPIO10 / TX GPIO11, LED 6, buzzer 8,
battery ADC 1 (GPIO10/11 are flash pins on a classic WROOM). ESP8266: UART0 (GPIO3/1),
so no debug output. AVR Uno/Nano: AltSoftSerial D8/D9.

**Power** is a buck converter from pin 16. **Battery** is a 47 k/10 k divider with
`analogReadMilliVolts` ×16 oversampling and an EMA with α = 0.01 (×1.017 calibration).
The UI colours it green above 12.6 V, yellow from 12.0 V and red below. The README
pictures three custom PCBs (ESP32-C3 and ESP32-S3 OBD dongles in printed enclosures,
sponsored by PCBWay). No design files are published.

**Displays/UI.** No TFT/OLED. The web build is an AP "OBD2 Master" with **default password
`12345678`** (STA fallback in 3 s) serving a gzipped SPA: splash, link and vehicle icons, Main
(battery), Live, Error Codes (+Clear), Freeze Frame, a 0–100 km/h timer (browser
`setInterval`, started by the speed PID), Vehicle Info and Settings (theme, protocol, PID
picker, Wi-Fi, OTA). **OTA upload is unauthenticated** (`POST /firmwareUpdate`). Buzzer
melodies mark events. A BLE build (GATT "SPEED/RPM" query) was removed 2026-02-22 unfinished.

**Coverage.** There is no tested-vehicle list. The README marks the three protocols
"✅ Tested". The sample output is from an ISO 9141-2 car. The issues report failures
or questions for a 2006 VW on KWP fast init (`81 10 F1`: L9637D and BC547 both failed;
unresolved), a Mercedes A180D, Nissan Consult 2 (not supported), an Arduino Leonardo,
and generic "no protocol matched". The library reports ~8–9 (9141) and ~9–10 (14230)
responses/s.

## 6. Comparison with Ostler

**What we have.** `kline/frame.py` does KWP2000 framing (physical, functional,
unaddressed, `0x80`+length) with checksum verification; `KLine.read_frame` resyncs on
glitch bytes. `converse`/`_burst_read` are the muki01-style tolerant bursts. Fast init is
precision-timed and measured (`last_pulse`), and `fast_init_tolerant` skips the echo
before looking for `C1`. Slow init (8N1, ~KW2, ~addr) is in `SerialTransport` and ESP32
`klineSlowInit`. `kwp2000.py` has the NRC table, `0x78`, SecurityAccess, IO control and
routines; `EcuSession` sends TesterPresent and releases with `82`; `modscan` is a
read-only sweep; `LoggingTransport` writes JSONL. The D2 ESP32 node has L9637D,
GPIO16/17, W5 300 ms, an INIT/SLOWINIT/TX bridge, Influx logging, raw capture, LittleFS
spill, password-gated OTA and WireGuard.

**Better there.** Protocol breadth (ISO 9141-2, KW1281, DS2, KW82); the protocol profile
as a data row with init type as a separate axis; keyword classification and a
three-protocol auto-detect; a complete (if buggy) J1979 01–0A layer with bitmaps, non-CAN
mode 09 counts, VIN, CALID and CVN; P3-min enforcement; a 5-baud receiver and ECU
simulators; multi-board ports, six cheap interfaces, a battery EMA and page-driven polling.

**Better here.** Checksum-verified reads with resync; measured init timings and
echo-skipping `C1` detection; keep-alive and `82` release; typed errors; tier gating of
clear and actuate (CONSTITUTION, ADR-0018/0019) versus a GET clear and open OTA; VIN
masking; tests against `FakeKLineEcu` and replay; correct 8N1 slow-init addresses; a clear
licence.

## 7. Feature inventory

Tiers: read = Tier 0, clear = Tier 1, actuate = Tier 2+ (ADR-0018/0019). "port (MIT)" means
port from reader `91ae045` only, keeping the notice. "facts" means clean-room from
ISO 9141-2/14230, SAE J1979/J2012 and OBDb.

| feature | where in their code | Ostler has it? | where it lands | safety tier | reuse | effort |
|---|---|---|---|---|---|---|
| 5-baud slow init (bit-bang, 200 ms/bit) | `send5baud`; lib `KLine_Core::send5baud` | yes (8N1) | platform `transport` + ostler-firmware; keep 8N1, add per-profile parity option for KW1281/KW82 | read | facts | S |
| Keyword read + ~KW2 + ~addr check | `initOBD2`; lib `trySlowInit` | yes | platform `kline`: return `(KW1, KW2, confirmed)`; reject when ~addr ≠ expected | read | facts | S |
| Keyword → protocol classification (KW1==KW2 → 9141) and KWP key-byte decode | `initOBD2`; lib `trySlowInit` | no | platform `kline.keywords` (decode KWP format/timing bits too) | read | facts | S |
| Fast init 25/25 ms + `C1 33 F1 81` functional | `initOBD2`; lib `tryFastInit` | yes (more robust) | n/a | read | n/a | n/a |
| Pre-init idle (they 5.5 s, we W5 0.3 s) | `initOBD2`; lib `wakeUpDelay` | partly | platform `KLine.init_idle` per profile; long idle after a failed or abandoned session | read | facts | S |
| Auto-detect 9141 / 14230-slow / 14230-fast | `initOBD2`; lib `connect` | no | platform `kline.detect()` used by generic_obd2 connect; U4 status-strip link chip | read | facts | M |
| Manual protocol override, persisted | `/protocolOptions`, `settings.conf` | partly (pack-fixed) | platform link config; More › Devices, U4 | read | facts | S |
| Protocol profile table (baud, parity, checksum, header, length mode, P1–P4, W1–W4) | lib `OBD2ProtocolConfig` | no | platform `kline/profiles.py` as data; pack overrides in `vehicle.json` `transport` | read | facts (design idea) | M |
| ISO 9141-2 framing `68 6A F1` / `48 6B xx`, no length | `writeData` | no | platform `kline/frame_iso9141.py` | read | facts | S |
| P4 5 ms, exact-length echo, reply checksum (lib), link-lost after 3 misses | `writeData`, `clearEcho(n)`, `updateConnectionStatus` | yes (all, plus echo compare) | n/a | read | n/a | n/a |
| P3-min wait before each request | lib `sendBytes` | partly (poll pacing) | platform `KLine._send` guard | read | facts | S |
| Keep-alive (TesterPresent) | absent | yes | n/a; add a generic_obd2 idle `01 00` keep-alive for 9141 | read | n/a | S |
| KW1281 block protocol (ack-by-complement, counter) | lib `writeBlock`/`readBlock` | no | platform `kline/kw1281.py`; future VAG pack; U7 | read (+ later actuate) | facts; cross-check kw1281test (MIT) | M |
| BMW DS2 (9600 8E1, XOR, whole-frame length) | lib `DS2_CONFIG`, `buildFrame` | no | platform `kline` profile + framing; future BMW pack; U7 | read | facts | S |
| Opel KW82 streaming + sliding-window framer | lib `readPacket` | no | platform `kline/stream.py`; future Opel pack | read | facts | M |
| Honda two's-complement frames | lib v1.1 Honda example (MIT) | no | platform checksum enum; future Honda pack | read | facts | S |
| Custom framing / raw send at three levels | lib `writeData`/`writeRawData`/`sendBytes` | partly | platform raw send behind the allowlist; More › Developer, U7 | code | facts | S |
| 5-baud receive decoder (sniff the init address) | lib `read5baud` | no | platform `sniff` (`ModuleTracker` init signature) + ostler-firmware RX tap | read | facts | S |
| Fast-init-as-`0x00` sniff signature | lib v1.1 Opel table | partly | platform `sniff` init detector | read | facts | S |
| ECU simulator (request → canned reply) | lib v1.1 Honda/Opel sketches | yes (`FakeKLineEcu`) | tests/fakes; add a 9141/J1979 fake for generic_obd2 | read | facts | S |
| Mode 01 live PIDs | `getPID` | no | generic_obd2 pack (OBDb SAEJ1979 import); Diagnose › Live, Home, U4 | read | facts (OBDb) | M |
| PID 01 MIL / DTC count / readiness monitors | A only | partly (VSS leaves) | generic_obd2 → `Vehicle.Ostler.Diagnostics.*`; Home health card, U4 | read | facts | S |
| Support bitmaps 01/02/05/06/08/09 (chained) | `readSupportedData` | no | platform J1979 `supported()`; drives `generateViews()`, U3/U4 | read | facts | S |
| Page-driven polling (poll what is shown) | `obdTask` `page` | partly (rate per state) | platform poll scheduler + UI subscriptions, U3/U4 | read | facts | M |
| User PID picker | `/pidSelect`, Settings | partly (dashboards deferred) | UI Diagnose › Live chooser, U4 | read | facts | S |
| Mode 02 freeze frame (frame 0, `02 02` DTC) | `getPID(read_FreezeFrame)` | no | generic_obd2; fault → snapshot on Diagnose, logbook event, U4 | read | facts | M |
| Mode 03/07 DTCs (multi-frame, multi-ECU) | `readDTCs` (buggy) | no (KWP `18` only) | platform J1979 service + generic_obd2 `dtc_sources`; Diagnose › Faults, U4 | read | facts | S |
| Mode 0A permanent DTCs | constant | no | as above (CAN cars mostly) | read | facts | S |
| DTC two-byte → P/C/B/U decode | `decodeDTC` | partly | platform `dtc` J2012 decoder | read | facts | S |
| DTC description table | `errorCodes.js` | partly (pack meanings) | generic meanings from an open source with known licence; not this file | read | none | M |
| Mode 04 clear | `clearDTCs`, `GET /api/clearDTCs`, WS `clear_dtc` | partly (KWP `14` gated) | generic_obd2 `clears` action: Parked, confirm, report-first, re-read; U2/U4 | **clear** | facts | S |
| Mode 05 O2 test results (non-CAN) | bitmap only | no | generic_obd2 (9141/KWP only); Diagnose › Tests, U4+ | read | facts | M |
| Mode 06 on-board tests | bitmap only | no | generic_obd2 MID/TID; Diagnose › Tests, U4+ | read | facts | M |
| Mode 08 control | bitmap only | no | listed only; its own review | actuate | n/a | n/a |
| Mode 09 VIN (local decode, never logged) | `getVehicleInfo(02)` | partly (KWP ident, redaction) | platform J1979 + local VIN decode; Diagnose identity bar, U4 | read | facts | S |
| Mode 09 CALID/CVN with non-CAN count PIDs `03`/`05` | `getVehicleInfo(04/06)` | no | generic_obd2 identity + fingerprint (`decode_pipeline.md`); U4/U7 | read | facts | S |
| Opel KWP `30 xx 07` actuator list (fuel pump, coils, MIL, injector cut…) | lib v1.1 Opel table | no | future Opel pack, disabled behind Experimental + Parked + confirm (ADR-0019) | **actuate** | facts | S |
| Manufacturer ECU files (Simtec 71, ME7.5, EDC15…) | unpublished | no | none (closed) | n/a | none | n/a |
| Battery voltage ADC (16× + EMA) | `readBatteryVoltage` | partly | ostler-firmware node → `Vehicle.LowVoltageBattery.CurrentVoltage`; status strip, U5 | read | facts | S |
| 0–100 km/h timer | UI `script.js` speed test | no | UI Drive/Logs "performance" from timestamped speed samples (server-side, interpolated); Moving lockout U2; low priority | read | facts | S |
| Wi-Fi AP/STA fallback, WebSocket JSON push, SPIFFS settings | `initWiFi`, `sendDataToServer`, `SPIFFS.ino` | yes (Pi SSE; node multi-SSID + NVS) | n/a | read | n/a | n/a |
| OTA firmware + filesystem upload | `/firmwareUpdate` | yes (password-gated) | ostler-firmware: signed images only | code | facts | M |
| Buzzer/LED status melodies | `Functions.ino` | no | ostler-firmware status LED (optional) | read | facts | S |
| Six interface schematics | `Schematics/` | partly (L9637D) | ostler-firmware hardware docs: L9637D/MC33290 primary, add TVS + series R | n/a | facts | S |
| Multi-MCU ports (AVR, ESP8266, S3/C3/C6) | `#ifdef` blocks | no | ostler-firmware targets ESP32-S3 only (hardware.md) | n/a | none | n/a |
| Vehicle-report issue form | `.github/ISSUE_TEMPLATE/vehicle_report.yml` | no | Ostler issue form (protocol, keywords, PIDs supported) | n/a | facts | S |

## 8. Recommendations

1. **Licence records.** In `THIRD_PARTY_LICENSES.md` (platform, and the D2 pack's
   existing entry), note: the reader is MIT to `91ae045` and GPL-3.0 from `aef63b4`; the
   vendored copy is `a1946a7` (MIT); the library is facts-only (non-commercial headers,
   conflicting GPL-3.0 root). Correct the vendored README (the repo is not removed, and
   the link points at the library). Update the `landscape.md` row, which still reads
   "MIT reader".
2. **K-line profiles as data** (spec first, clean-room): `kline/profiles.py`, one record
   per protocol (9141-2, KWP slow/fast, KW1281, DS2, KW82, Honda) with baud, serial
   format, address parity, checksum, header, length mode, P1–P4, W1–W5 and idle; init
   method as a separate field; packs override in `transport` (`vehicle_data_model.md`).
3. **ISO 9141-2 framing + `kline.detect()`** for generic_obd2: fast init first where a
   KWP ECU is known, else 5-baud; classify by keywords, decode KWP key bytes, verify
   ~addr, keep alive (`01 00` on 9141, `3E` on KWP), release with `82`.
4. **J1979 service layer** shared by CAN (sibling note) and K-line, with pytest vectors
   built from this audit's defects: multi-frame 03 with 4+ DTCs, a merged multi-ECU
   burst, a 160-bit support chain, signed `32`/`54`, `23 ×10`, `50 ×10`, `02 02` as
   2 bytes, VIN with message count `09 01`, CALID/CVN counts `09 03`/`09 05`.
5. **Mode 04** only as the Tier 1 `clears` action (Parked, confirm, report-first,
   re-read). Never on GET, never over an unauthenticated socket.
6. **Firmware:** keep the D2 node design (L9637D, 510 Ω 0.5 W pull-up, TVS); add a
   `read5baud`-style passive init decoder and the battery EMA. Reject the open AP
   password, unauthenticated OTA, and LIN transceivers without a dominant-timeout check.
7. **Manufacturer protocols** (KW1281, DS2, KW82, Honda) land as platform framing in U7,
   each with a real or simulated ECU fixture; cross-check KW1281 against kw1281test (MIT).
8. **D2 pack:** nothing new for the Td5. Upstream fixes since the vendored snapshot
   (header from the *connected* protocol, exact-length echo, no trailing P4) are already
   in our stack; cite the parity divergence in the D2 init-timing slab.
9. **Do not copy:** in-band float errors, fixed-offset parsing without checksum checks,
   the 5.5 s idle before every attempt (it slows reconnects), or the unsourced
   `errorCodes.js`.

**ADR candidates.** (a) **K-line protocol profiles and auto-detect** need an ADR or an
ADR-0020 companion: the probe order, the rule that a 5-baud or fast-init probe on an
unknown car is a Tier 0 action allowed only Parked, and the profile schema. (b)
**Manufacturer K-line protocols** (KW1281/DS2/KW82) enter as read-only framing; their
actuator services (for example Opel `30 xx 07`) inherit ADR-0019's disabled-by-default
gating, so no new ADR unless writes are planned. (c) **Licence handling** is covered by
ADR-0019 (c); add one line: "non-commercial or conflicting-header sources are facts-only".
