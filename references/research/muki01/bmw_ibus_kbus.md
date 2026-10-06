---
title: "muki01 BMW_IBus_KBus: BMW I/K-Bus audit, feature inventory and body-bus fit"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/canbus_headunit.md]
summary: >
  An end-to-end audit of muki01/BMW_IBus_KBus (E46 K-Bus firmware for Arduino and ESP32, with about 117 checksum-correct frames, a phone web UI, key-fob light automations, bus-wake power gating and TH3122/opto/MCP2025 interfaces) and of its companion library. It is GPL-3.0 since 2026-10-03, but the identical code is MIT at 6213cc6 (firmware) and 87b58c6 (library). The library core appears to derive from an older third-party IbusSerial, and the history once held NavCoder and BMW training PDFs, so Ostler takes facts only. Recommends a passive I/K-Bus link over the byte Transport, a read-only BMW E-series pack, alarm triggers, and a new ADR before any body-bus transmit.
---

# muki01 BMW_IBus_KBus: BMW I/K-Bus audit and body-bus fit

Read in full: <https://github.com/muki01/BMW_IBus_KBus> at `2853acd` (2026-10-04, 43
commits) and its library <https://github.com/muki01/BMW_IBus_KBus_Library> at `8b23383`
(2026-10-05, 17 commits): every sketch, header, schematic, README, CI file and template,
plus the photos and screenshots. Cross-references were checked only for
facts and licence: `kmalinich/node-bmw-client` and `tedsalmon/BlueBus`. Search-API access was
blocked, so the other projects in §5.3 are named from memory (U).

## 1. What it is

| | |
|---|---|
| Purpose | "Control your classic BMW from your phone". The firmware sends BMW **K-Bus** frames to the light module (LCM), the body module (GM5/ZKE) and the windows, and reacts to key-fob events |
| Code | `Codes/E46_KBus_ESP32/` (ESP32: Wi-Fi AP + web UI, 5 files), `Codes/E46_KBus_Code/` (AVR: key-fob light automations), `Codes/Basic_Code/` (bus reader). `E46_Codes.h` (30 KB) is a table of about 117 frames and is duplicated in both firmware folders |
| Library | `BMW_IBus_KBus.{h,cpp}` (receive FSM, XOR checksum, idle-gated transmit, sleep), `IbusRingBuffer`, `BMW_IBus_KBus_Modules.h` (about 57 I/K-Bus and 25 D-Bus addresses), and 3 examples |
| Activity | Created 2023-12. Docs were dumped in 2024-02/03. The in-repo library came in 2025-08. On **2026-10-02** it was rewritten as a firmware project, and on 2026-10-03 relicensed. The ESP32 build is marked **"experimental … not yet verified in a vehicle"**. The library claims Nano and ESP32 were tested in an E46 |
| Tests | None. CI compiles the sketches with arduino-cli (Nano, Mega, Uno, ESP32) |
| Cars | Written and verified on an **E46**. The README says the bus is shared by E38, E39, E53 (I + K), E46, E83 and E85 (K only), and that "messages may differ" |

**Licence verdict.**
- **Firmware repo.** `LICENSE` was **MIT** ("(c) 2023 Muksin Muksin") from `1e16a8b` up to
  `6213cc6` (2026-10-02). It has been **GPL-3.0** since `6b5424d` (2026-10-03), with a
  commercial licence offered on request. `git diff 6213cc6 HEAD -- Codes` is **empty**, so
  all the code is available under MIT at `6213cc6`.
- **Library.** MIT ("(c) 2025") until `87b58c6`, GPL-3.0 since `b3cffb8`; `src/` is
  unchanged since the MIT snapshot. No file has a per-file header or SPDX tag.
- **Provenance caveat.** The library core (`FIND_SOURCE…BAD_CHECKSUM` FSM, Timer2
  `OCR2A = 94` "≈1.5 ms", "Arduino / Melexis") matches the long-circulating Arduino
  `IbusSerial` code by a third party (U: Ian Hollingsworth's IbusSerial; its licence is
  unclear). muki01's MIT grant may not cover that upstream authorship.
- **History hazards.** Until `0393491` the repo shipped `Programs/BMW NavCoder v2.9.183
  Full Version.zip` (proprietary software), BMW training-style PDFs ("BMW BUS
  Information", "Introduction to Bus Systems", "E46 Bus Network"), HackTheIBus printouts and
  community `.xls` code lists. **None of these was opened, and none may be used**: they are
  dealer/OEM lineage or of unknown licence. `E46_Codes.h` may have been compiled partly from
  those lists.
- **For Ostler: facts only, clean-room.** Byte values and protocol behaviour are facts. We
  re-verify them on a car and store them in pack data (CC BY-SA). No C++ is worth porting,
  because the Python framer is about 40 lines. If anything is ever ported, port it from
  `6213cc6`/`87b58c6` with the MIT notice, never from HEAD (ADR-0019 keeps GPL-3 out of core).

## 2. The I/K-Bus protocol

**Physical layer.**
- A single wire with a ground return, idling recessive at battery voltage and driven low
  by open-collector senders: LIN-like, but older and with no master. The UART runs at
  **9600 baud, 8E1**; one byte is 11 bit times (about 1.15 ms). It sleeps with the car,
  and any traffic wakes it.
- **K-Bus** carries body modules (GM/ZKE, LCM, IKE, IHKA, seats, mirrors, RLS). **I-Bus**
  carries infotainment on E38/E39/E53 (radio, nav/GT, BMBT, MID, phone, CDC, DSP). E46,
  E83 and E85 put everything on the K-Bus.
- The **IKE gateways** to the diagnostic **D-Bus**, which runs DS2 at 9600 8E1 on the
  diagnostic connector. The **I/K-Bus is not on the OBD-II port**.

**Frame.** `SRC LEN DST DATA… CHK`.
- `LEN` counts the bytes after itself (`DST` and `CHK` included); `CHK` is the XOR of
  every byte before it; the first data byte is the command or message type.
- Example: `50 04 68 32 11 1F`, where the steering wheel (MFL) tells the radio "volume up".
- Broadcast addresses: `0xBF` (global, "ALL"), `0xFF` (local, used by "device ready"
  `02 01` announcements) and `0xE7` (multicast to displays).
- The library accepts `LEN` 3–36. I checked all 117 reference frames in `E46_Codes.h` with
  a script: **0 checksum errors, 0 length errors**.

**Receive.**
- A byte FSM: source → length (sanity 3..0x24, else drop one byte) → wait for `LEN+2`
  bytes → XOR check; on a bad checksum it drops one byte and re-syncs. An optional source
  allowlist (`setSourceFilter`) discards other frames before the handler.

**Transmit and collisions.**
- There is no bit arbitration and no ACK. The TH3122 **SEN/STA** pin goes high whenever
  the bus is active.
- The library starts a 1.5 ms timer on every SEN/STA falling edge (Timer2 on AVR,
  `micros()` elsewhere). Only after 1.5 ms of idle is `clearToSend` set.
- It sends at most one queued frame every 10 ms. Frames over 32 bytes are dropped.
- **Weaknesses:** SEN/STA is checked only before the first byte; it does **not read back
  its own echo** (no collision detection) and does **not retry** (a frame is silently
  dropped if the bus is busy). The opto and MCP2025 circuits have no SEN/STA, so no
  collision avoidance at all.
- Robust senders in other projects add an echo compare and bounded retries (U).

**Power.**
- `sleep()` pulls the transceiver's **EN** low after N s with no valid frame; the TH3122
  shuts its 5 V regulator off and the MCU loses power. Bus traffic powers it back up.
- On ESP32 the 5 V pin drives a buck converter's **EN** instead. If the board is still
  alive 3 s after shutdown, the firmware concludes it is on USB and stays on.

## 3. The decoded message set

The repo **decodes only** the GM key-fob frame. Everything else is a send table or a
reference list. "Use" gives the Ostler fit: R = passive read, A = alarm, H = head unit,
T = transmit (gated).

| Src → Dst | Cmd / data | Example (with CHK) | Meaning (per repo; verify per car) | In repo | Use |
|---|---|---|---|---|---|
| 00 GM → BF | `72 xx` | `00 04 BF 72 12 DB` / `…22 EB` / `…06 CF` | Key fob lock / unlock / release (`16`/`26` also listed as lock/unlock "button") | **decoded** (triggers automations) | R, A |
| 44 EWS → BF | `74 ss kk` | `44 05 BF 74 04 00 8E` / `…00 FF 75` | Key inserted (kk = key number) / removed | listed | R, A |
| 80 IKE → BF | `11 ss` | `80 04 BF 11 00 2A` / `01` / `03` | Ignition off / KL-R (pos 1) / KL-15 (pos 2) | listed | R, A |
| BF → 80 IKE | `16` | `BF 03 80 16 2A` | Request odometer (reply `17`, not decoded) | listed | T (Tier 0 request) |
| 68 RAD → 80 | `41 01 01` | `68 05 80 41 01 01 AC` | Request time from IKE | listed | T (Tier 0) |
| 3B GT → 80 | `41 10 0A` / `41 09 20` / `41 09 08` | `3B 05 80 41 10 0A E5` | OBC: reset average speed; speed limit = current speed / off | listed | T |
| 50 MFL → 68 / C8 / B0 | `32 1x`, `3B 02`, `3B 80` | `50 04 68 32 11 1F` | Wheel volume ± (radio or phone), R/T, send/end, voice hold | listed | R, H |
| 68 RAD ↔ 18 CDC | `01` poll; `02 0x` ready; `38 cc pp` control; `39 …` status | `68 05 18 38 03 00 4E` | CD stop/pause/play, disc 1–6 (`06 n`), seek (`0A`), select (`07`); CDC status replies | listed | H (CDC emulation, T) |
| 68 RAD → 6A DSP | `32 xy`, `36 xx` | `68 04 6A 32 11 25` | Volume steps 1–3 ±; source CD/tuner/off; DSP functions | listed | R, H |
| C8 TEL → E7 | `2C ss` | `C8 04 E7 2C 05 02` | Phone status LEDs: incoming, on, hands-free, active call | listed | R, H |
| 68 RAD → FF | `3B 00` | `68 04 FF 3B 00 A8` | "No button / go to radio", which the author is unsure of | listed | — |
| 3F DIA → 00 GM | `0C nn 01` | `3F 05 00 0C 34 01 03` | GM5 IO job (diagnostic activation): about 30 lines: dome light, lock, hard-lock, driver door, trunk ×3, 8 window steps, 2 sunroof steps, wipers, washer, hazards, interior dim, alarm LED | **sent** (web UI) | T (actuate) |
| 3F DIA → BF / D0 LCM | `0C` + 8 or 12 bytes of IO bitmap | `3F 0B BF 0C 00 00 00 00 7A 48 0A 06 B9` | LCM lamp job: parking, low, main, fog, turn, brake, hazard, follow-me-home, goodbye; all off goes to `D0` | **sent** (web UI + automations) | T (actuate) |

**Not in the repo:** the messages a passive Ostler pack needs most. Their facts are in MIT
`node-bmw-client` (`modules/IKE.js`, `GM.js`, `LCM.js`), to be re-verified on a car: IKE
`13` sensor status (handbrake, oil, reverse); IKE `17` odometer (24-bit LE km); IKE `18`
speed (×2 km/h) and RPM (×100); IKE `19` outside and coolant temperature (signed °C); IKE
`24` OBC values (range, consumption, average speed); GM `7A` door/window/sunroof/boot/bonnet
open plus a locked bit; GM `76` crash/alarm; LCM `5B` lamp-on and lamp-fault bitmaps;
display text (IKE `1A`/`23`, MID/GT `21`/`23`/`A5`); BMBT `48` buttons.

## 4. Hardware

| Interface | Parts | Pins (μC side) | Notes |
|---|---|---|---|
| **TH3122.4 / ELMOS 10026B** (main) | 1N4148 into VS; 47 µF; 10 Ω + 100 pF on BUS; 1 µF on VCC | TXD→RX, RXD←TX, **SEN/STA**, **EN**, 5 V out | BMW-style bus transceiver with an on-chip 5 V regulator, bus-activity output and enable/sleep. The TH3122 is legacy; Elmos 10026B is the drop-in |
| **PC817 opto pair** | 2× PC817, BC547, 1N4007, 2k/470/1k/470/10k | RX, TX | RX opto from bus to μC; TX opto + BC547 pulls the bus low. **The RX half alone is a hardware listen-only tap.** No SEN/STA |
| **MCP2025 LIN** | 1N4148 | TXD, RXD, LWAKE | Compact, with a regulator. No SEN/STA or EN, so no collision avoidance and no sleep. Check the pin mapping against the datasheet |

- **Pins.** Arduino: D0/D1 bus (shares USB; unplug to flash), D3 SEN/STA, D4 EN, D13 LED,
  D7/D8 debug. ESP32: GPIO16/17 (UART2), 4 SEN/STA, 5 EN, 2 LED. It needs a **5 V → 3.3 V shift**
  on TXD and SEN/STA, and a 12 V buck with EN driven by the TH3122's 5 V output.
- **E46 tap points (photos):**
  - the boot CD-changer plug **X18180**: K-Bus white/red/yellow, +12 V red/green, ground
    brown;
  - the K-Bus junction comb above the glovebox fuse box;
  - the radio harness.
- **Web UI (ESP32).** It runs as an AP `BMW-E46` at `192.168.4.1`, and `static_assert`
  refuses to compile without a ≥ 8-character password. It is a single page with three tabs:
  **Control** (grouped buttons generated from `Commands.h`, sleep countdown, "Stay awake");
  **Monitor** (last 20 frames, newest first, module names from a JS map); **Settings**
  (key-fob toggle, sleep after 10–3600 s, web-awake 30–3600 s, "Sleep now"; stored in NVS).
- **REST API:** `GET /api/commands`, `GET /api/state` and `POST /api/cmd|settings|awake|sleep`.
  **`/api/cmd` sends any table frame with no authentication beyond the Wi-Fi PSK and no
  driving-state check.** You can switch the lights off or move windows at speed.
- **Automations (both builds).**
  *Welcome:* unlock → parking lights + indicators; a second unlock within 14.5 s adds the
  fogs. *Goodbye:* lock → lights for 2 s, then all off. *Follow-me-home:* lock twice within
  4 s while locked. All three **transmit autonomously** on a bus event, with no user at the UI.

## 5. Comparison with Ostler and fit options

### 5.1 Where Ostler stands
- **Transport.** It is a byte pipe (`SerialTransport`, `EspTransport`, `LoggingTransport`),
  with framing above it. CAN gets a frame-level `CanLink` (ADR-0020).
- **I/K-Bus fits the byte `Transport`.** pyserial does 9600 8E1, so the work is an
  `IbusFramer` above it, much as KWP2000 sits above K-line. A `CanLink` is not needed.
- **The D2 pack is K-line and has no body bus.** The I/K-Bus serves a future BMW E-series
  pack, the **L322 Range Rover 2002–05** (BMW-era electronics with I/K-Bus (U); a natural
  Land Rover follow-on), and Mini R50 (partial, U).
- **ADR-0020's principle covers every vehicle bus:** listen-only by default, and transmit
  only with allowlist + Parked + server gate. Its allowlist schema (ID, DLC, rate) and its
  Tier 0 exception, however, are CAN-specific.
- **Safety tiers apply** (UI spec §7): GM and LCM IO jobs are **Tier 2 actuate**.
  `comfort` cannot apply, because they write to a vehicle bus (ADR-0018).

### 5.2 Fit options
- **(a) Passive I/K-Bus link and decoder: yes, first.**
  `IbusFramer` (FSM + XOR + resync + length sanity) over `SerialTransport` (USB-UART + opto
  RX-only tap, or a TH3122 with TX tied recessive) or `EspTransport` (a firmware RX mode).
  It emits `IbusFrame{ts, src, len, dst, cmd, data, chk_ok}` into JSONL plus raw hex. Tests
  use a `FakeIbus` with the 117 checked frames as golden vectors; the source filter
  becomes a capture filter.
- **(b) BMW E-series pack: yes, read-only first.** Signal map onto VSS 6.1 leaves (all
  present in `vss_leaves.json`):

  | Source | VSS leaf |
  |---|---|
  | GM `7A` | `Cabin.Door.Row{1,2}.{DriverSide,PassengerSide}.IsOpen`, `….Window.IsOpen`, `Body.Trunk.Rear.IsOpen`, `Body.Hood.IsOpen`, `Cabin.Door.*.IsLocked`, `Cabin.Light.IsDomeOn` |
  | LCM `5B` | `Body.Lights.{Beam.Low,Beam.High,Fog.Front,Fog.Rear,Parking,Backup,LicensePlate}.IsOn` and `.IsDefect`, `Brake.IsActive`, `Hazard.IsSignaling`, `DirectionIndicator.{Left,Right}.IsSignaling` |
  | IKE `17` | `TraveledDistance` |
  | IKE `18` | `Speed`, `Powertrain.CombustionEngine.Speed` |
  | IKE `19` | `Exterior.AirTemperature`, `Powertrain.CombustionEngine.EngineCoolant.Temperature` |
  | IKE `24` | `Powertrain.FuelSystem.Range` / `InstantConsumption` |
  | IKE `11` | `LowVoltageSystemState` (OFF/ACC/ON/START) |
  | DSP `32` | `Cabin.Infotainment.Media.Volume` |

  Key-fob, key-in and MFL button **events** need `Vehicle.Ostler.Body.KeyFobEvent`,
  `….KeyPresent` and `Vehicle.Ostler.Cabin.SteeringWheelButton` in `vss/ostler.vspec`.
  Every field starts as `candidate`.
- **(c) Alarm triggers: yes, high value.**
  Triggers while armed: GM `7A` door/boot/bonnet open, `72` unlock without our disarm, EWS
  `74` key in, IKE `11` ignition on, and **any bus wake**. The TH3122 EN/wake design draws
  only transceiver sleep current until the body bus wakes, which fits the guardian's power
  budget. Optional Tier 2 indicators: the GM `4E` "clown-nose" LED (armed) and the LCM 3 s
  hazard flash (locate). Both are gated and never remote; the alarm stays notify-only.
- **(d) Head-unit integration: read yes, transmit later.**
  - **Read:** MFL buttons (`32`/`3B`) as head-unit input for Drive mode (U1/U2), plus
    the radio, DSP and phone state.
  - **Transmit, behind an ADR:**
    - **CDC emulation**: answer the radio's `01` polls as `18` and announce `02 01`, so the
      factory radio's CD keys drive Ostler. This is legitimate only when no real CDC
      answers;
    - **display text injection** to IKE, MID or GT (`1A`/`23`/`21`/`A5`; facts from
      node-bmw-client).
  - Never send MFL or GM *event* frames: spoofing another module's events is forbidden.
- **(e) Sniffing and decoding tooling: yes.**
  An I/K-Bus capture kind in `sniff/` with module naming (address table → pack data),
  per-(src, cmd) byte change heat, and the existing `>>> screen`/`value` markers for
  "press the button, mark it" labelling. Every frame names its src/dst/cmd, so ECU
  attribution is free, unlike multi-ECU K-line.

### 5.3 Related open projects (cross-reference only)
| Project | Licence | Use |
|---|---|---|
| `kmalinich/node-bmw-client` (Node, active 2026-09) | **MIT** | The best open decode reference for IKE, GM, LCM, EWS, MID and BMBT. Facts, or port with the notice |
| `tedsalmon/BlueBus` (PIC firmware + hardware, active 2026-09) | BSD-3-style "BlueBus License" + **no-profit clause on hardware** | A mature I/K-Bus CDC/BMBT/MID emulator. Facts only; do not copy the hardware |
| `piersholt/walter` (Ruby) | GPL-3.0 | Facts only |
| ibusduino, `bmw-ibus` (Python), NavCoder notes, HackTheIBus wiki | U / proprietary (NavCoder) / unclear | NavCoder and dealer material: **never**. The rest: unverified facts only |

## 6. Feature inventory

Tiers: read / clear / actuate / procedure / code. **Every row that transmits on the car
bus is at least actuate and gated per ADR-0020** (pack allowlist + Parked + server gate,
never remote). "Facts" means facts-only clean-room. Every source is the MIT snapshot.

| Feature | Where in their code | Ostler has it? | Where it lands | Tier | Reuse | Effort |
|---|---|---|---|---|---|---|
| 9600 8E1 frame FSM, XOR check, 1-byte resync | lib `BMW_IBus_KBus.cpp` `readIbus()` | no | platform: `IbusFramer` over byte `Transport` | read | facts | S |
| Length sanity 3–36, max 32-byte TX | `readIbus()`, `sendIbusPacket()` | no | platform | read | facts | S |
| Source allowlist before the handler | `setSourceFilter()` | partly (sniff filters) | platform capture filter | read | facts | S |
| XOR checksum build/append | `write(…, addChecksum)` | no (KWP uses a sum) | platform | — | facts | S |
| SEN/STA idle ≥ 1.5 ms before TX; 10 ms frame gap | `startTimer`, `updateClearToSend`, Timer2 ISR | no | ostler-firmware body-bus node (+ echo verify, retry) | actuate | facts | M |
| Bus-wake power gating (EN low → MCU off; traffic → on) | `sleep()`, ESP32 `goToSleep()` | partly (guardian sleeps on its own cell) | ostler-firmware / alarm node | read | facts | M |
| "Still powered after 3 s → bench, stay on" | ESP32 `goToSleep()` | no | ostler-firmware | — | facts | S |
| Module address table (I/K + D-Bus) | lib `BMW_IBus_KBus_Modules.h` | no | BMW pack data | read | facts | S |
| Hex debug dump: good, bad, discarded | `printDebugMessage()` | yes (`LoggingTransport` JSONL) | platform | read | — | S |
| Key-fob lock/unlock/release decode (GM `72`) | `E46_KBus_Code.ino` `packetHandler` | no | BMW pack + alarm | read | facts | S |
| Key in/out (EWS `74`) | `E46_Codes.h` | no | BMW pack + alarm | read | facts | S |
| Ignition state (IKE `11`) | `E46_Codes.h` | no | BMW pack → `LowVoltageSystemState`; alarm | read | facts | S |
| Steering-wheel buttons (MFL `32`/`3B`) | `E46_Codes.h` | no | BMW pack → UI U1/U2 Drive input | read | facts | S |
| Radio/DSP/phone state (`6A`, `C8→E7`) | `E46_Codes.h` | no | BMW pack; UI U1 media chip | read | facts | S |
| Odometer / time requests (IKE `16`, `41 01`) | `E46_Codes.h` | no | BMW pack poll (needs the ADR's Tier 0 exception) | read (transmits) | facts | S |
| Doors/lids/locks, lamps, odometer, speed, temps, OBC (`7A`, `5B`, `17`–`19`, `24`) | **absent** (node-bmw-client) | no | BMW pack; VSS per §5.2 | read | facts / MIT | M |
| LCM lamp IO jobs (park, low, fog, hazard, turn, brake, follow-me-home, goodbye, off) | `E46_Codes.h` Lights; `Commands.h` | no | BMW pack actions; UI U3 | actuate | facts | M |
| GM5 lock/unlock/hard-lock/driver-door/trunk | `E46_Codes.h` Doors; `Commands.h` | no | BMW pack; never remote; threat model (U5) | actuate | facts | M |
| Window and sunroof "a piece" steps | `E46_Codes.h` Windows/Sunroof | no | BMW pack; Parked, occupant-present confirm (pinch risk) | actuate | facts | M |
| Interior light, wipers, washer | `E46_Codes.h` | no | BMW pack | actuate | facts | S |
| Alarm LED 3 s ("clown nose") / LCM hazard 3 s | `CLOWN_FLASH`, `Hazard_LCM_3s` | no | alarm (armed indicator / locate), U5 | actuate | facts | S |
| OBC average-speed reset / speed-limit set | `AvgSpeedDelete`, `SpeedLimit*` | no | BMW pack | clear / actuate | facts | S |
| CD-changer emulation (poll reply, announce, `38`/`39`) | `E46_Codes.h` CD section | no | BMW pack + head-unit device (U5) | actuate | facts (+ BlueBus/node facts) | L |
| Display text injection (IKE/MID/GT) | **absent** | no | head-unit integration (U5+) | actuate | facts / MIT | M |
| Key-fob automations (welcome 2-stage 14.5 s, goodbye 2 s, follow-me-home ×2 in 4 s) | `packetHandler` in both firmware builds | no | BMW pack "standing automation" (needs ADR) | actuate (autonomous TX) | facts | M |
| Command table → grouped buttons | `Commands.h`, `/api/commands`, `WebPage.h` | yes (manifest, generated UI) | UI U3 | — | — | — |
| Bus monitor: last 20 frames with module names | `logPacket`, `/api/state`, JS `MODULES` | partly (K-line sniff/capture) | UI U7 Decode | read | facts | S |
| Sleep countdown, "Stay awake", "Sleep now" | `WebPage.h`, `/api/awake`, `/api/sleep` | no | UI U5 Devices (device power chip) | — | facts | S |
| Settings in NVS (timers, feature toggle) | `Preferences` in the ESP32 sketch | partly | ostler-firmware | — | facts | S |
| No default Wi-Fi password (`static_assert`) | `Config.h` | partly (ADR-0021 local HTTPS) | ostler-firmware build rule | — | facts (pattern) | S |
| Unauthenticated `/api/cmd`, no driving-state gate | ESP32 `handleCommand()` | n/a (anti-pattern) | **do not adopt**; server gate already exists | — | — | — |
| Bus reader sketch | `Basic_Code.ino` | partly (ESP32 K-line RX tap) | ostler-firmware RX-only mode | read | facts | S |
| TH3122 / Elmos 10026B, PC817 opto, MCP2025 interfaces | `Schematics/*.png` | no | hardware: ostler-firmware body-bus node (opto RX-only default) | read | facts (redraw) | M |
| E46 tap points (X18180, junction comb, radio) | README + `images/` | no | BMW pack hardware doc | — | facts (own photos) | S |
| Arduino-CLI compile CI | `.github/workflows/build.yml` | partly (pytest; firmware CI U) | ostler-firmware CI | — | facts | S |
| Vehicle-report issue form (model/year/verified) | `.github/ISSUE_TEMPLATE/vehicle_report.yml` | partly (community opt-in) | UI U7 Contribute | — | facts | S |
| Volume increment lookup | `VOL_INCREMENT` (unused upstream) | no | skip | — | — | — |

## 7. Recommendations

1. **Adopt (a) and (e) now, read-only:** a spec for `IbusFramer` + `FakeIbus` over the
   byte `Transport`, the I/K-Bus capture kind and module naming. Pure stdlib, no hardware
   in CI; the 117 checked frames become re-derived test vectors.
2. **Then a read-only `bmw_e` pack (b) and alarm triggers (c).** Map signals onto the VSS
   leaves in §5.2 and add three `Vehicle.Ostler.*` event leaves. Car-test each field to
   `proven`. Add the L322 as a candidate second body-bus car (U).
3. **Hardware default: an RX-only opto tap.** The ostler-firmware body-bus node uses the
   PC817 RX half, or a TH3122 with RXD tied recessive. A transmit-capable variant
   (TH3122/10026B with SEN/STA) comes only with the ADR below.
4. **A new ADR is needed: "Body-bus links (BMW I/K-Bus): passive by default".** ADR-0020's
   rule covers it in principle, but its schema and exception are CAN-specific. It should fix:
   - (i) a byte `Transport` + framer, not a `CanLink`; (ii) a pack allowlist keyed on
     `(src, dst, cmd, data mask, rate)`;
   - (iii) **no spoofing**: never transmit with the source address of a module present in
     the car (GM `00`, EWS `44`, IKE `80`, MFL `50`, RAD `68`); `3F` only for allowlisted IO
     jobs; emulate a device such as CDC `18` only once no real one answers;
   - (iv) a rate-limited Tier 0 exception for IKE requests (`16`, `41`); (v) TX hardware
     with SEN/STA idle, echo compare and bounded retries; (vi) no transmit from remote
     paths, and lock/unlock only after the U5 threat model;
   - (vii) **standing automations** (welcome lights and the like): pre-authorised once,
     Parked only, rate-limited, every frame logged. This fits neither ADR-0018 `comfort`
     nor per-action confirmation, so it needs its own decision.
5. **Never use** the repo-history NavCoder zip, the BMW training PDFs or the community
   `.xls` lists. Treat `E46_Codes.h` as unverified facts of mixed lineage and verify every
   action frame on a car before it enters a pack.
