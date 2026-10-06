---
title: "CAN-bus scanners and head-unit integrations — interfaces, protocols, CAN-box emulation and in-car display paths (Oct 2026)"
area: references
status: stable
version: 1.1
updated: 2026-10-06
depends_on: [references/research/hardware.md, references/research/ui/head_unit_ui.md]
summary: >
  Surveys CAN adapters (STN/ELM, WiCAN, gs_usb, Pi HATs, ESP32), their APIs (SocketCAN, slcan, GVRET, can327, ISO-TP/UDS, J2534) and scanner UIs, and how aftermarket Android head units take vehicle data from CAN-box decoders over a 38400-baud UART (Raise 0x2E, Hiworld 0x5A A5). Recommends a frame-level `CanLink` beside the byte-level `Transport` (SocketCAN first), a Raise-protocol ESP32 CAN-box emulator fed from Ostler (not from vehicle CAN), and the order kiosk PWA → CAN-box emulator → launcher, with Android Auto, CarPlay and AAOS apps as hard-limited or deferred.
---

# CAN-bus scanners and head-unit integrations (October 2026)

> **Update (2026-10-06, ADR-0032/0033):** in production the car's buses are spoken by the
> ESP32 **node**, whose transmit gate is the only path to the car; the Pi is the optional
> **brain**, and the Pi-side CAN interfaces below become lab/dev links. The guardian is a
> node hardware variant, and the alarm is no longer described as notify-only.

**Scope.** This extends [hardware.md](hardware.md) (the kit), [landscape.md](landscape.md) §6, §11
and §12 (project lists), [ui/head_unit_ui.md](ui/head_unit_ui.md) (layout and distraction rules), and the
platform spec's "Displays are thin clients". It does not repeat them. **(U)** means unverified: bench-test it
before relying on it. Refs in `[x]` are listed at the end, one URL each. Licence checks were made on
2026-10-05 against each repo's root licence file.

**One fact frames everything.** The reference car (D2 Td5) has **no comfort CAN**. Its diagnostics are
K-line ([hardware.md](hardware.md), "Risks"). Every CAN feature below serves later cars, our **private
add-on bus**, or a head unit, never the D2's own wiring.

---

## Part A — CAN scanners and interfaces

### A1. Adapters

| Adapter | Host link / API | Raw CAN sniffing | Listen-only | Openness | Ostler role |
|---|---|---|---|---|---|
| **OBDLink MX+/CX/EX** (STN chips) | Classic BT 3.0 (MX+) [S2]; USB (EX); BLE (CX) (U); ELM327 AT plus the **ST** command set [S1] | Yes, via monitor commands. Filters are `STFPA`-style. Firmware fixed "BUFFER FULL" on busy buses [S3] | **Yes.** `STCMM` sets the CAN monitoring mode, and the default is 0, "receive only – no CAN ACKs" [S1] | Closed firmware; documented command set [S1] | Best **ELM-class** adapter. `STPX` sends an arbitrary header + data with an expected response count and timeout [S1]. MS-CAN and SW-CAN are supported [S2]. |
| **Vgate vLinker** (FS/MC+/FD+) | BT/BLE/USB; ELM327, ELM329 **and STN** instruction sets; 2 KB buffer, up to 230.4 kbit/s UART [S4] | Partial (U) | U | Closed, own chip [S4] | Cheap STN-compatible fallback. Treat its ST support as (U). |
| **ELM327 clones** ("v1.5", "v2.1") | BT/Wi-Fi/USB serial | Monitor mode aborts with "BUFFER FULL" when its UART buffer fills [K1] | Clones hard-code silent monitoring ON. `AT CSM` is unsupported, and RTR frames are dropped [K1] | Closed, often pirated firmware | OBD-II request/response only. Never use one for bus analysis. |
| **WiCAN / WiCAN Pro** (MeatPi, ESP32-C3 / S3) | Wi-Fi/BLE/USB. Protocols: `slcan`, `realdash66`, `savvycan` (GVRET), `elm327`, `auto_pid`. Default TCP port **3333** [W2] | Yes (slcan/GVRET) | **Yes.** `can_mode` is `normal` or `silent`, and the **default is `normal`** [W2] | **GPL-3** [W1] | OBD front end in the kit. On a vehicle bus, set `silent`. |
| **Macchina M2 / A0** | A0: ESP32 Wi-Fi/BLE, ships preloaded with SavvyCAN support, $89 [M1] | Yes | Firmware-defined | Open firmware [M1]; Macchina-J2534 has **no licence** ([landscape.md](landscape.md)) | Reference only |
| **CANable / candleLight / CANtact** (gs_usb) | USB; the mainline `gs_usb` driver gives SocketCAN; python-can supports gs_usb and CANtact [P1] | Yes, at full rate | `ip link … listen-only on` [K2] | candleLight_fw and cantact-fw are **MIT** [L1] | **Cheapest reliable bench sniffer** for the Pi or a laptop |
| **PCAN / Kvaser** | Vendor APIs; python-can backends [P1] | Yes | Yes | Closed | Reference only. Support comes free through python-can. |
| **Pi CAN HATs** | SocketCAN over SPI | MCP2515: **two RX buffers**, so frames drop when more than two arrive per service cycle [E1]. Users report overrun counts rising [E2] | Yes [K2] | — | The CarPiHAT uses an **MCP2515** (original-board wiki [E3]; PRO 5 same chip, U). Fine for the **private 250 kbit/s add-on bus**. For 500 kbit/s vehicle sniffing, use gs_usb or an MCP2518FD HAT. |
| **MCP2518FD HATs** (Waveshare 2-CH FD, PiCAN-FD) | `mcp251xfd` driver; CAN-FD | Deep FIFOs | Yes | — | Choose this if Pi-side vehicle CAN or CAN-FD matters. Some users report bring-up trouble, so bench-test it [E2]. |
| **ESP32-CAN-X2 / ESP32 TWAI** | Our firmware: GVRET via ESP32RET (MIT [L1]), slcan, or our own line protocol | Yes. TWAI has a listen-only mode (U) | Yes (U) | ESP32RET is MIT [L1] | **Bridge and emulator node** (A5, B3) |
| **comma panda** | USB; CAN + CAN-FD on an STM32H7 [C1] | Yes | Boots with **no output**: TX is allowed only after a vehicle safety model is set, and tx/rx hooks enforce it [C1] | **MIT** [L1] | **Reference for TX gating** (A4) |

### A2. Protocols and APIs

| Layer | What it is | Notes for Ostler |
|---|---|---|
| **SocketCAN** | Linux network devices. `CAN_RAW` with 0..n filters; `CAN_RAW_FD_FRAMES` (off by default) for FD; `listen-only` set over netlink [K2] | stdlib `socket.AF_CAN`, so no dependency ([platform.md](platform.md) §2) |
| **Kernel ISO-TP** (`CAN_ISOTP`) | ISO 15765-2 as a socket. Works on classic CAN and CAN-FD (`tx_dl` > 8 for FD) [K3] | The default transport for UDS on the Pi |
| **can327** | A kernel line discipline that makes an **ELM327 into a SocketCAN device** (`ldattach … 30 /dev/ttyUSB0`). It is best effort and half duplex, adequate for request/response OBD and monitoring [K1] | Lets ELM users run the SocketCAN path unchanged, but only as a "degraded" link |
| **slcan / LAWICEL** | ASCII CAN over serial. python-can's `slcan` accepts raw TCP sockets and RFC2217 URLs as well as tty paths [P2] | **The WiCAN Pro reaches python-can over TCP 3333 with no extra code** [W2][P2] |
| **GVRET** | SavvyCAN's binary serial/TCP protocol. ESP32RET implements it over USB and Wi-Fi, with a LAWICEL subset [G1] | The ESP32 node speaks it, so SavvyCAN works for free |
| **RealDash CAN** | Frames tagged `44 33 22 11`, then a 32-bit LE id and 8 data bytes. Text frames use `55 33 22 11` [RD] | An export target ([landscape.md](landscape.md) row "RealDash-extras", Unlicense) |
| **ELM327 / STN** | AT commands (`ATSP`, `ATSH`, `ATMA`) plus the ST extensions (`STPX`, `STCMM`, `STCFCPA` flow-control pairs) [S1] | A request-level driver, not a frame driver (A5) |
| **J2534 pass-thru** | A Windows DLL API. Open efforts: Macchina-J2534 (no licence), GenericDiagnosticTool [J1], dschultzca/j2534 (Linux) [J2] | **Low priority** (already ranked last in [platform.md](platform.md)) |
| **python-can / can-isotp / udsoncan** | python-can is **LGPL-3**; python-can-isotp and udsoncan are **MIT** [L1] | Optional extras, for Mac/Windows dongles and for UDS services |
| **CAN-FD readiness** | The kernel ISO-TP, MCP2518FD, panda and gs_usb paths handle FD [K3][C1]. The MCP2515 and ELM/STN do not | Keep `dlc` up to 64 in our frame type from day one |

### A3. How scanner software presents CAN (patterns to borrow, not code)

- **SavvyCAN:** GVRET natively, any Qt SerialBus driver (socketcan, Vector, PEAK), many log formats including Wireshark socketcan PCAP [G2]; bit-change "flip" view and DBC overlay (U).
- **cabana** (comma; the web version is archived, the Qt version lives in openpilot) [C2]: an ID list with **per-byte change heat**, a bit painter against a DBC, plots synced to video and the route timeline. Closest model for our Decode mode.
- **Wireshark:** `can`, `iso15765` and `uds` dissectors on live SocketCAN capture [WS], so UDS decode needs no code from us.
- **BUSMASTER / CANalyzer** (reference) [VX]: trace window (fixed/scrolling), signal graphs, an interactive TX generator, logging triggers.
- **WiCAN web UI** [W1][W5]: normal/silent and protocol pickers; AutoPID vehicle profiles that turn PIDs into named values; MQTT; an **official Home Assistant integration** (HTTP pull). MQTT topics are `wican/<id>/can/rx|tx|status` with JSON frames `{"bus":"0","type":"rx","ts":…,"frame":[{"id":123,"dlc":8,"extd":false,"data":[…]}]}` [W3]. **Anything published to `…/can/tx` is transmitted**; the docs say plain MQTT is unencrypted, so local broker only [W4].
- **OBDLink apps / RealDash:** gauge-first over ELM/STN or RealDash CAN; users see named values, not frames ([ui/obd_apps.md](ui/obd_apps.md)).

**Borrow for Decode mode:** cabana's byte heat and bit painter, SavvyCAN's flip view, a mandatory
"**listen-only**" badge, and a WiCAN-style named-value layer (AutoPID ≈ our pack signals).

### A4. Safety rules for CAN (extends CONSTITUTION and UI spec §7)

1. **Listen-only is the default on any vehicle bus:** SocketCAN `listen-only on` [K2], STN `STCMM 0` [S1], WiCAN `silent` [W2]. WiCAN ships in **normal** (ACKs and can transmit) [W2], so our setup must flip it and show the mode. A listen-only node does not ACK, so a two-node bench bus will show sender errors; that is expected.
2. **Transmit gating, panda-style** [C1]: TX on a vehicle bus needs a pack-declared allowlist (ID, DLC, rate), Parked state and the server-side gate. The only default exception is diagnostic requests (UDS over ISO-TP to 0x7DF/0x7E0), Parked only.
3. **Bus-load limits:** one diagnostic request in flight; ≥ 50 ms between periodic polls per ECU; back off on NRC 0x21/0x78; rate-limit in firmware, not just in Python.
4. **Never touch safety-critical buses** (powertrain, chassis, ADAS, a gateway's private side): read-only through the OBD port; never splice into airbag, ABS or EPS wiring. The private add-on bus stays physically separate ([hardware.md](hardware.md), "Buses").
5. **No remote TX** (no MQTT → vehicle CAN path): keep WiCAN `can/tx` disabled, or inert under `silent`.

### A5. Abstraction: does "SocketCAN-first `Transport` + ELM/STN + WiCAN over TCP/MQTT" fit?

**What exists today** (`src/openostler/transport/`):
- `Transport` is a **raw byte pipe** (`open/close/send/receive`).
- `SerialTransport` (KKL) and `EspTransport` (an ESP32 K-line bridge with a fused `INIT <frame>` command) implement it.
- `LoggingTransport` wraps either one.

This is right for K-line, where framing and timing live above it. **CAN is frame-based**, so forcing frames through a byte pipe would make every layer re-frame them.

**Recommendation:**
- Keep `Transport` for byte links.
- Add a **sibling frame-level interface**, plus two adapters above it:

```
CanLink (abstract): open/close · send(frame) · recv(timeout) · set_filters([...]) · listen_only: bool
                    bitrate · fd: bool · capabilities {tx, fd, timestamps, max_rate}
  SocketCanLink     AF_CAN CAN_RAW; covers CarPiHAT, gs_usb, MCP2518FD, can327-ELM, vcan (CI)
  SlcanTcpLink      WiCAN Pro / ESP32 over TCP 3333 (or python-can slcan "socket://" [P2])
  GvretLink         ESP32-CAN-X2 running ESP32RET-compatible firmware (USB or Wi-Fi) [G1]
  MqttCanLink       read-only ingest of wican/<id>/can/rx JSON [W3]; TX never implemented
IsoTpChannel        kernel CAN_ISOTP on SocketCanLink [K3]; userspace can-isotp (MIT) on others
ObdRequestLink      ELM327/STN: request/response at the AT/STPX level [S1] (it does ISO-TP internally)
LoggingCanLink      the same JSONL capture discipline as LoggingTransport; also writes candump format
```

- **ELM/STN is not a `CanLink`.** It is an `ObdRequestLink`. The protocol layer asks for "service + data → response" and does not see frames. can327 can promote an ELM to a degraded `SocketCanLink` [K1].
- **MQTT is telemetry, not a link.** WiCAN's MQTT and HA paths are for when the brain is off, through the node's parked broker, as **read-only** ingest.
- **Plugin registration** follows the existing plan (`d2diag.transport` entry points, [platform.md](platform.md) §2).

**Interface priority:**
1. **SocketCAN.** One driver covers the CarPiHAT (private bus), gs_usb (sniffing), can327, and `vcan` for CI.
2. **ESP32 node via slcan/GVRET.** Our own add-ons and the ESP32-CAN-X2. SavvyCAN works for free.
3. **WiCAN Pro over TCP slcan** (same code as 2), plus read-only MQTT ingest.
4. **STN/ELM327 `ObdRequestLink`.** For the `generic_obd2` pack. Its UI shows "ELM: limited".
5. **python-can backends** (PCAN, Kvaser, Vector), optional, for desktop users.
6. **J2534** last.

---

## Part B — Head-unit integrations

### B1. Aftermarket Android head units

- **Platforms.** **FYT** is the most-modded platform; Joying, Mekede, Junsun, Teyes, Atoto and others build
  on it [F1]. It runs Android 10 on UIS7862, often badged as a "fake" Android 11+ [F1]; newer UIS7862S listings
  claim Android 13 [F8]. The Teyes CC3 2K is UIS7862, Android 10, 1920×1200 [F7]. Topway (TS10/TS18) and
  Microntek (MTCx) are separate platforms with their own MCUs and canbus apps (U).
- **Launchers.** Stock launchers are vendor-made. AGAMA, CarWebGuru and FCC are closed-source with in-app
  purchases, offering widget grids, OBD widgets and logos [L2]: **layout references only**.
- **Modding without root.** FYT units accept USB-stick "flashable" mod zips that replace APKs and run scripts,
  keeping the user's apps [F2]; FytHWOneKey (GPL-3) maps hardware keys to any package or intent [F1]. That is
  how a kiosk or Ostler launcher gets installed and bound to a key.
- **ACC behaviour.** FYT "Factory settings" (PIN) offers **sleep vs power-off after ACC off**, including a long
  sleep, so apps resume instead of cold-booting [F5][F6]; a cold boot needs the kiosk's start-on-boot.
- **System car-info API (FYT).** `com.syu.ms` owns the MCU link; `com.syu.canbus` binds the
  `com.syu.ms.toolkit` intent, whose `getRemoteModule()` exposes module interfaces. Third-party access is
  community reverse engineering, and hooking needs Magisk + LSPosed [F3]. **Don't build on it**; make the
  head unit's *own* canbus UI show our data (B3).

### B2. CAN-box decoders: how head units get vehicle data

**The physical link.** A CAN box sits between the car's CAN and the head unit's harness:
- it gives the head unit **ACC power-on, illumination, reverse and camera power**;
- it sends **vehicle state over UART at 38400 8N1, 5 V TTL** [HU3][HU4][HU2];
- the user picks the matching box and car in the head unit's canbus settings, for example "Toyota RAV4" [HU2].

| Protocol family | Sync | Baud | Evidence | Licence of the evidence |
|---|---|---|---|---|
| **Raise / RZC** (睿志诚) | `0x2E` | 38400 | VW protocol v1.4 translated to English [HU3]; RAV4/Camry protocol v2.21 PDF in the same repo | Repo **MIT** [L1]. **The vendor PDFs are not ours to redistribute**; use them as facts only |
| **Hiworld** | `0x5A 0xA5` | 38400 / 115200 | canbox-core lists handshake 0x24, climate 0x31/0x32, trip 0x33–0x35, radar 0x22–0x24, doors 0x02/0x25, TPMS 0x38/0x39, angle 0x26, SWC 0x11 [HU1] | README claims MIT/Apache but **no LICENSE file**, so facts only. It is AI-assisted (`AGENTS.md`), so verify everything on the bench |
| **Bagoo** | `0xFD` / `0xD5` | 38400 | Baseline only [HU1] | as above |
| **Simple Soft** | `0xAA 0x55` | 38400 | "planned" [HU1] | as above (U) |
| **Oudi** (BMW NBT Evo) | ? | 38400 | Emulated by smartgauges/canbox [HU4] | **No licence**, facts only |
| **XinPu, Binary/BNR** | — | — | No open documentation found | — |

**Raise frame** [HU3]:
- `2E | DataType | Len | Data… | Checksum`, where `Checksum = (DataType+Len+ΣData) XOR 0xFF`.
- The receiver ACKs with the single byte `FF` (`F0` = NACK) **within 10 ms**.
- If no ACK arrives within 100 ms, the sender retransmits, up to 3 times, then stops.

**Raise data, box → head unit** [HU3]: `0x14` backlight 0–255 · `0x16` speed (u16 LE / 16 km/h) ·
`0x20` SWC key + state (VOL±, `>`/`<`, TEL, MUTE, SRC, MIC; released/pressed/held) · `0x21` climate (AC,
recirc, AUTO, DUAL, fan 0–7, vents, 18–26 °C in 0.5° steps, LO/HI, seat heat) · `0x22`/`0x23` rear/front
radar, 4 zones 0–10 · `0x24` reverse / P-or-handbrake / lights bits · `0x25` park-assist · `0x26` steering
angle · `0x27` amplifier · `0x30` version · `0x41` body/doors.

**Raise commands, head unit → box:** `0x81` start/end, `0x90` request a type, `0xA0` amplifier control,
`0xC0–C4` source, tuner, media and volume OSD (for an OEM cluster), `0xC6` radar volume [HU3].

**Other open work:**
- VwRaiseCanbox (Raise VW) [HU5] and JunsunPSARemote [HU6] are **GPL-3**: compatible with our AGPL, but prefer clean-room.
- esp32-canbox-nissan (**MIT**) emits the RAV4 protocol from an ESP32-C3 + SN65HVD230 over GPIO5/6 [HU2]:
  - steering angle 200 ms, RPM 333 ms, speed 500 ms;
  - its README says the protocol docs are "scarce" and still being reverse-engineered.
- canbox-core's delta and rate tiers are a good model [HU1]: events in under 10 ms; angle, speed and RPM at 5–10 Hz; doors at a 1 Hz keepalive; TPMS and trip on change or every 30 s. Together they keep a 38400-baud link mostly idle.

### B3. The Ostler CAN-box emulator (planned add-on)

**Goal:** any CAN-box-capable head unit shows Ostler data (speed, doors, reverse, climate, trip, radar, TPMS) on its **own native screens**, with no app on the head unit.

- **Data source.** The D2 has no comfort CAN, so the input is **Ostler**, not vehicle CAN: node signals
  (K-line SLABS speed, `reverse_gear`, `side_lights`), the HEVAC add-on and the node's opto inputs, over
  the **private CAN bus** (preferred: works while the Pi boots) or Wi-Fi/MQTT. On CAN cars a pack may also
  decode comfort CAN **read-only** through a listen-only TWAI.
- **Hardware.** ESP32-CAN-X2 ([hardware.md](hardware.md)): port 1 on the private bus, port 2 listen-only on
  vehicle CAN where one exists; UART to the head unit's canbox connector through a 3.3 V ↔ 5 V level shifter;
  high-side outputs for **REVERSE, ILL, ACC** where the harness lacks them [HU1]. The original CAN box stays
  out of circuit, except where it powers the camera [HU2].
- **Firmware layering** (canbox-core's shape, written clean-room): private-bus/MQTT → canonical
  `vehicle_state` → delta cache with rate tiers → protocol vtable (Raise first) → UART framer with ACK/retry.
  A **Linux build on `vcan` + pty** for CI [HU1], and a **head-unit simulator** in tests that checks the
  checksum, ACK timing and retry.
- **Safety.** The UART goes only to the head unit; it **never transmits on vehicle CAN** (that port is
  hard-set listen-only); downlink commands (climate touches, `0xA0` amp) reach only **our** HEVAC/amp devices.
- **Profile choice.** Pick the head-unit car profile whose native screens show most: Raise VW (PQ) gives
  climate, radar, doors, SWC, speed, backlight [HU3]; Raise RAV4 adds RPM, fuel and trip [HU2].

### B4. Steering wheel, reverse, cameras, amplifier

- **SWC.** Head units "learn" analogue resistor-ladder buttons on **KEY1/KEY2/GND** [SW1].
  - The emulator can instead send `0x20` key codes from any source (for example a private-bus button node) [HU3].
  - Ostler could also act as a ladder (a digital potentiometer), but that is (U).
- **Reverse trigger.**
  - A 12 V REV wire switches the head unit to camera input and often powers the camera [RV1].
  - Where a CAN box reports reverse, **don't also wire REV from the box**; forum reports warn of damage [RV1].
  - `0x24` bit 0 carries reverse over UART [HU3].
  - The **head unit's MCU-driven camera path is the fast path** the platform spec asks for: it works while the Pi is still booting.
  - So: a direct analogue/AHD camera → head unit for reversing, and our go2rtc cameras for everything else.
- **AHD/CVBS inputs.** Current head units take CVBS or AHD 720p/1080p rear cameras, with the format chosen in settings (U: model-dependent). Steering-angle guidelines need `0x26` [HU3][HU2].
- **Amplifier/DSP.** Raise defines `0x27` amp status and `0xA0` amp control [HU3]. A future Ostler DSP node could speak it. Otherwise the head unit's own DSP stays in charge.

### B5. Android Auto and CarPlay: what a third-party app may do

- **Android Auto / AAOS categories** [AA1]: templated navigation, POI, **IoT**, weather, media; parked-only
  (AAOS) video, games, browsers. "Apps outside these categories are NOT allowed." **There is no diagnostics
  or vehicle-data category.**
- **IoT** = "take actions on connected devices", e.g. enabling home security systems [AA2]. Arming our
  alarm (on the node or its guardian variant) or flagging a Mark *might* qualify; that depends on review (U).
- **Car hardware API** [AA3] gives the app the **car's** speed, energy and mileage
  (`com.google.android.gms.permission.CAR_SPEED`, …): car → app, so useless for showing *our* data.
- **CarPlay** [CP1][CP2]: audio, video (parked), messaging/VoIP, navigation, EV charging, fuelling, parking,
  public safety, quick food ordering, voice, **driving task**, widgets; each needs an Apple entitlement.
  "Driving task" covers controlling car accessories and driving/road status, so a slim Ostler status/Mark app
  could apply (entitlement U). CarPlay Ultra's gauges and climate are **OEM-only**
  ([ui/head_unit_ui.md](ui/head_unit_ui.md) [C3]).
- **Wireless dongles:** Carlinkit/Ottocast make wired CarPlay/AA wireless; "AI box" variants run a full
  Android over the CarPlay link [DG1]. On an aftermarket unit they hang off its USB and its ZLink/AutoKit-style
  app (U). **Keep them for media**, as the platform spec says.

### B6. Android Automotive OS (native app)

- VHAL is the property interface (AIDL from Android 13) [AA5]. The **AAOS emulator** sets VHAL values such
  as speed under Extended controls → Car data [AA4]; custom properties can be described in JSON [AA6].
- **Our cars are not AAOS**; aftermarket units are phone-AOSP builds (B1), and AAOS Play has the same
  category rules, with browsers parked-only [AA1]. **Verdict:** an AAOS app comes last; use the emulator only to
  test the PWA and Car App Library templates.

### B7. Open head-unit projects

| Project | Status | Licence |
|---|---|---|
| **OpenAuto Pro** (BlueWave) | Vendor gone with no source released. A community revival repo was archived on 2026-02-27 [OA1] | Closed |
| **Crankshaft** | Still pushed in 2026, slow. A Pi Android Auto receiver via openauto/aasdk; not certified by Google [OA2] | GPL-3 |
| **AGL** | UCB 17 adds Pi 5 support. Flutter IVI demo with HVAC and media screens [AGL1] | Mixed / Apache |

**Lesson:** a Pi-based Android Auto receiver is fragile because protocol changes break it. Keep the head unit for CarPlay/AA, and Ostler as a PWA beside it.

### B8. Displays as thin clients (practical notes)

- **Kiosk.**
  - Fully Kiosk Browser: kiosk/fullscreen lock, start on boot, JS + REST + **MQTT** APIs, screen on/off; PLUS licence €8.90/device [FK].
  - Its MQTT API lets the Pi switch the screen or URL on ignition and reverse.
  - Alternative: a tiny Ostler WebView app (our launcher seed), which avoids a closed dependency.
  - The WebView version on FYT units may lag behind Chrome (U); test CSS `dvh` and container queries.
- **Start on ignition.** Set "sleep after ACC off" (B1) so the kiosk resumes. On a cold boot, use the kiosk's start-on-boot, or an FYT key binding [F1].
- **DPI.** Use the spec's `?display=headunit` flag ([ui/head_unit_ui.md](ui/head_unit_ui.md)). Record each test unit's `devicePixelRatio` and CSS viewport (U).
- **Network topology** (U, all bench items):
  1. **Pi as a Wi-Fi AP, head unit as client.** Simplest. But the head unit loses phone-hotspot internet, because units usually have one Wi-Fi radio.
  2. **Head unit as hotspot, Pi joins.** Keeps one network, but the hotspot must be enabled on every resume.
  3. **USB:** the Pi 5 USB-C port in gadget mode (ECM/RNDIS) into the head unit's USB host. Wired, with no radio conflict, if the unit's kernel has `cdc_ether`.
  4. **USB-Ethernet dongle** on the head unit.

  Prefer 3, then 1. Serve over plain HTTP on a private subnet with a fixed host name.

---

## Recommendations

**Interfaces (priority):** 1 SocketCAN `CanLink` · 2 ESP32 slcan/GVRET · 3 WiCAN Pro over TCP slcan +
read-only MQTT ingest · 4 STN/ELM `ObdRequestLink` · 5 python-can extras · 6 J2534. Listen-only on every
vehicle bus; TX only through the pack allowlist + Parked + the node's transmit gate (ADR-0032; SocketCAN/slcan on the Pi become lab/dev links).

**Head-unit path:**
1. **Kiosk PWA now**, as the spec already says. Fully Kiosk or a minimal WebView wrapper, with "sleep after ACC" so it resumes.
2. **CAN-box emulator (Raise)** next. It is cheap (one ESP32, a level shifter) and puts speed, doors, reverse and climate on the native screens of almost any CAN-box-capable head unit, with no app, while the Pi boots. Reverse stays on the head unit's own camera path.
3. **Ostler launcher** (WebView host + reverse/ACC handling + key binding) only once kiosk limits bite.
4. **A CarPlay "driving task" / AA IoT micro-app** (arm, Mark, worst telltale) only if the entitlement or review is granted.
5. **AAOS app** last.

**Test head units:** (1) the owner's current unit; (2) one **FYT UIS7862** unit (e.g. Joying or Mekede,
9–10" 1280×720), with the largest mod community [F1][F2]; (3) a **Teyes CC3** as a popular second firmware
[F7]; (4) the AAOS emulator and desktop Chrome at 1024×600, 1280×720 and 1920×720.

**Emulator protocols, in order:** (1) **Raise VW (0x2E)**, which has the best open spec: speed, reverse/lights,
doors, climate, SWC, backlight [HU3]; (2) the **Raise RAV4 variant** for RPM, fuel, trip, angle [HU2];
(3) **Hiworld (0x5A A5)** for TPMS and a richer trip [HU1]; (4) Simple Soft, Oudi and others on demand.

**Hard limits:** no diagnostics category on Android Auto/AAOS [AA1]; a CarPlay entitlement per category
[CP1]; CarPlay Ultra and VHAL vehicle data are OEM/AAOS-only; the FYT car-info API is undocumented and needs
root to hook [F3]; vendor protocol PDFs and canbus APKs are never copied (**facts only, clean-room, attributed**).

**Bench tests for `references/test_plan.md` (owner to add):** CarPiHAT PRO 5 CAN chip and its drop rate at
500 kbit/s; WiCAN `silent` against `can/tx`; Raise ACK timing on the owner's unit; FYT sleep/resume with the
kiosk; the unit's `cdc_ether` USB tethering.

## Sources

- [S1] OBDLink Family Reference & Programming Manual: https://www.scantool.net/scantool/downloads/682/obdlink_frpm_f.pdf
- [S2] OBDLink MX+: https://www.obdlink.com/products/obdlink-mxp/
- [S3] OBDLink MX firmware notes: https://www.scantool.net/updates/obdlink_mx
- [S4] vLinker FD+ listing (retailer, indicative): https://bltv.de/products/vgate-vlinker-fd-obd2-bluetooth-adapter-diagnostic-code-read/223674854/
- [K1] can327 ELM327 SocketCAN driver: https://docs.kernel.org/networking/device_drivers/can/can327.html
- [K2] SocketCAN: https://www.kernel.org/doc/html/latest/networking/can.html
- [K3] Kernel ISO-TP: https://docs.kernel.org/networking/iso15765-2.html
- [W1] WiCAN firmware (GPL-3): https://github.com/meatpiHQ/wican-fw
- [W2] WiCAN defaults and protocol switch: https://github.com/meatpiHQ/wican-fw/blob/main/main/config_server.c
- [W3] WiCAN MQTT JSON format: https://github.com/meatpiHQ/wican-fw/blob/main/main/mqtt.c
- [W4] WiCAN MQTT docs: https://meatpihq.github.io/wican-fw/config/mqtt
- [W5] WiCAN HA integration: https://www.crowdsupply.com/meatpi-electronics/wican-pro/updates/new-official-home-assistant-integration
- [M1] Macchina A0: https://www.macchina.cc/catalog/a0-boards/a0-under-dash
- [J1] GenericDiagnosticTool: https://github.com/jakka351/GenericDiagnosticTool
- [J2] Linux J2534: https://github.com/dschultzca/j2534
- [P1] python-can interfaces: https://python-can.readthedocs.io/en/stable/interfaces.html
- [P2] python-can slcan (TCP/RFC2217 URLs): https://python-can.readthedocs.io/en/main/interfaces/slcan.html
- [L1] Licence files checked: https://github.com/candle-usb/candleLight_fw · https://github.com/linklayer/cantact-fw · https://github.com/collin80/ESP32RET · https://github.com/commaai/panda · https://github.com/commaai/cabana · https://github.com/hardbyte/python-can · https://github.com/pylessard/python-can-isotp · https://github.com/pylessard/python-udsoncan · https://github.com/aerodomigue/esp32-canbox-nissan
- [C1] panda safety model: https://github.com/commaai/panda
- [C2] cabana: https://github.com/commaai/openpilot/tree/master/tools/cabana
- [E1] MCP2515 two-buffer limit: https://esphome.io/components/canbus/mcp2515/
- [E2] MCP2515 overruns / MCP2518FD bring-up: https://community.victronenergy.com/t/rpi-4-venusos-3-73-waveshare-can-hat-mcp251xfd-not-working/59426
- [E3] CarPiHAT wiki (MCP2515): https://github.com/gecko242/CarPiHat/wiki/Quick-Start-Guide
- [G1] ESP32RET / GVRET: https://github.com/collin80/ESP32RET ; https://github.com/collin80/SavvyCAN/discussions/941
- [G2] SavvyCAN: https://github.com/collin80/SavvyCAN
- [WS] Wireshark dissectors: https://www.wireshark.org/docs/dfref/c/can.html ; https://www.wireshark.org/docs/dfref/i/iso15765.html ; https://www.wireshark.org/docs/dfref/u/uds.html
- [VX] CANalyzer: https://www.vector.com/int/en/products/products-a-z/software/canalyzer/
- [RD] RealDash CAN protocol: https://github.com/janimm/RealDash-extras
- [HU1] canbox-core: https://github.com/fazerxlo/canbox-core
- [HU2] esp32-canbox-nissan (MIT): https://github.com/aerodomigue/esp32-canbox-nissan
- [HU3] Raise VW protocol v1.4 (English notes): https://github.com/aerodomigue/esp32-canbox-nissan/tree/master/docs/protocols/raise-vw-polo
- [HU4] smartgauges canbox: https://github.com/smartgauges/canbox
- [HU5] VwRaiseCanbox (GPL-3): https://github.com/icarome/VwRaiseCanbox
- [HU6] JunsunPSARemote (GPL-3): https://github.com/morcibacsi/JunsunPSARemote
- [F1] FytHWOneKey (brand list, Android versions): https://github.com/hvdwolf/FytHWOneKey
- [F2] FYT uis7862 no-root mods: https://github.com/hvdwolf/FYTuis7862BinRepo
- [F3] FYT canbus API (com.syu.ms): https://xdaforums.com/t/reading-changing-canbus-api-for-new-car.4517195/
- [F5] FYT sleep/power-off setting: https://www.rrsport.co.uk/forum/post603548.html
- [F6] Power off vs sleep: https://forum.android-headunits.com/viewtopic.php?t=23
- [F7] Teyes CC3 2K spec: https://e-katalog.kz/TEYES-CC3-2K-4PLUS32GB-UNIVERSAL-10INCH.htm
- [F8] UIS7862S Android 13 spec sheet: https://p.globalsources.com/IMAGES/PDT/SPEC/536/K1225341536.pdf
- [L2] Head-unit launchers: https://android-headunits.com/android-head-unit-launcher/ ; https://android-headunits.com/fcc-car-launcher/
- [SW1] KEY1/KEY2 SWC learning: https://android-headunits.com/what-are-key1-key2-and-gnd-for-android-headunit/
- [RV1] Reverse wiring with CAN boxes: https://www.t6forum.com/threads/android-head-unit-audio-tech-direct-reverse-wiring-again.63847/latest ; https://911uk.com/porsche/reversing-camera-with-aliexpress-headunit-how-do-i-wire-this-up.135929/?amp=1
- [FK] Fully Kiosk Browser: https://www.fully-kiosk.com/
- [AA1] Android for Cars categories: https://developer.android.com/training/cars/apps
- [AA2] IoT apps: https://developer.android.com/training/cars/apps/iot
- [AA3] Car hardware API: https://developer.android.com/training/cars/apps/library/car-hardware-api
- [AA4] AAOS emulator: https://developer.android.com/training/cars/testing/emulator
- [AA5] VHAL: https://source.android.com/docs/automotive/vhal
- [AA6] Extend VHAL in emulator: https://source.android.com/docs/automotive/start/avd/extend-vhal-properties
- [CP1] CarPlay categories and entitlement: https://developer.apple.com/carplay/
- [CP2] CarPlay driving-task apps (WWDC22): https://developer.apple.com/videos/play/wwdc2022/10016/
- [DG1] Wireless adapters and AI boxes: https://www.carplaylife.com/feature/best-wireless-adapters-to-convert-wired-carplay-into-wireless-android-auto-in-2026/
- [OA1] OpenAuto Pro community (archived): https://github.com/mrmees/openauto-pro-community
- [OA2] Crankshaft: https://github.com/opencardev/crankshaft
- [AGL1] AGL Flutter IVI on Pi 5: https://verygood.ventures/blog/vgv-builds-new-automotive-grade-linux-flutter-demo/
