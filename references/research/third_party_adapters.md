---
title: "Third-party adapters — ELM327, STN/OBDLink, vLinker, KKL cables, SocketCAN dongles, WiCAN, J2534 and the hosts that drive them (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/canbus_headunit.md, references/research/hardware.md, references/research/ui/obd_apps.md, references/research/obd_telematics_apps.md, references/research/ovms.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, specs/2026-10-06-canlink-isotp-design.md, specs/2026-10-06-j1979-service-layer-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-06-node-source-design.md]
summary: >
  What off-the-shelf scanners can and cannot do as Ostler data sources, checked live on 2026-10-07. Covers the ELM327 command set and versions (from the v2.2 datasheet's version table) and how to tell clones apart (v1.5 never existed; v1.4b firmware copied; missing CSM, AMC, CTM, IB12; two-byte command limits; ACKs while "monitoring"; BUFFER FULL), STN11xx/21xx/22xx and OBDLink MX+/LX/EX/CX (ST commands, STCMM, STIFI custom fast init, one-byte KWP headers, BLE vs Classic, MFi), vLinker, Veepeak, WiCAN and WiCAN Pro, KKL/FTDI cables (break-based fast init, the Linux 360-baud clamp, the 16 ms latency timer), gs_usb, slcan, PCAN, Kvaser, Macchina, can327 and J2534. Records what the platform already has (slcan, GVRET, SocketCAN, python-can, the KKL SerialTransport, ObdRequestLink, the Python TxGate). Answers the D2 question: the Td5 and SLABS speak unaddressed one-byte-header KWP2000, which a genuine ELM327 cannot send, an STN documents (candidate, bench it), and a KKL cable already does (proven). Gives a feature-by-adapter matrix against the Ostler node, host limits (Web Bluetooth BLE-only and Chromium-only, Web Serial over RFCOMM on Android from Chrome 137, iOS BLE or MFi only, BlueZ RFCOMM in the Python stdlib), a known-good list with what is verifiable, and clone tests.
---

# Third-party adapters as data sources (October 2026)

**Scope.** The owner asked for support of off-the-shelf scanners beside the Ostler node. This note
gathers the facts; the design is in
[the source-adapters spec](../../specs/2026-10-07-source-adapters-design.md). It extends
[canbus_headunit.md](canbus_headunit.md) (Part A: CAN adapters, APIs, the "ELM is an
`ObdRequestLink`" finding), [hardware.md](hardware.md) (the kit, WiCAN Pro as a CAN-only board
profile) and [ui/obd_apps.md](ui/obd_apps.md) (how Torque, Car Scanner, FORScan and others connect)
and does not repeat them. **(U)** marks a claim not verified against a datasheet, source or bench:
bench-test it before relying on it. Refs in `[x]` are listed at the end; all were read on 2026-10-07.

## 1. What the platform already has

A grep of `src/`, `specs/` and `decisions/` shows most of the plumbing exists. Adapters are a new
*source* on top of links we already have, not a new comms core.

| Piece | Where | State |
|---|---|---|
| `Transport` byte pipe; `SerialTransport` for a KKL/FTDI cable at 10400 8N1, with fast init by UART break on Linux and 5-baud init by bit-banged break | `transport/serial_transport.py` | Built; the D2 pack's proven dev path |
| Serial port auto-detection preferring FTDI, CH340, CP210x and "kkl" names, never a u-blox GPS | `ports.py` | Built |
| `CanLink` with backends SocketCAN (stdlib `AF_CAN`), slcan (serial or TCP, the WiCAN on 3333), GVRET, python-can (PCAN, Kvaser, Vector; optional `[can]` extra) | `can/` | Built ([CanLink spec](../../specs/2026-10-06-canlink-isotp-design.md) §3) |
| `LinkCaps` that report an unverifiable listen-only as `"requested"` | `can/link.py` | Built |
| The Python `TxGate` (rate, Tier 0 exception, allowlist + Parked + grant, the "never" list) | `can/gate.py` | Built; the lab reference of the node's C gate |
| `ObdRequestLink` protocol, pacing, Mode 08 and 04 guards | `obd/link.py` | Built; ELM/STN adapter is "later" ([J1979 spec](../../specs/2026-10-06-j1979-service-layer-design.md) §2.1, "ELM: limited") |
| `DataSource` with `source_kind` and `touches_car` | `web/sources.py` | Built; `NodeSource` sets `touches_car = False` |
| Serial source refuses to start when a node holds the K-line gate | `web/node_source.py` | Built (NodeSource spec §15 Q7) |
| ELM327/STN `ObdRequestLink`, BLE transport, adapter detection, clone checks, phone transports, J2534 | — | **Not built.** Out of scope in the CanLink spec §13 |

ADR-0020 already decided the shape: an ELM/STN is an `ObdRequestLink` (request → response), not
a `CanLink`; `can327` can turn an ELM into a degraded SocketCAN device; J2534 comes last.

## 2. ELM327: versions, commands and clones

### 2.1 The genuine part

- Elm Electronics' ELM327 is a PIC18F-based interpreter (the datasheet references the
  PIC18F2480 family) [E1]. Elm Electronics closed in June 2022 [E2]; no new genuine stock is made.
- The datasheet's version table [E1, pp. 91–92] gives what each version added. The ones that matter
  for detection:

| Version | Added (selected) |
|---|---|
| v1.0 | the base set: `MA`, `SH`, `SP`, `ST`, `CF`/`CM`, `WM`, `IIA`, `KW0/1` |
| v1.2 | four-byte KWP headers, adaptive timing, J1939, RS-232 up to 500 kbit/s (`BRD`) |
| v1.3 | `CRA`, `RTR`, `S0/S1`, `STOPPED` on searches |
| v1.4 | `FI` (manual fast init), `IB48`, `IGN`, `LP`, `SI`, `SS`, `TA`, `CEA`; manual ISO/KWP initiation |
| v1.4a, v1.5 | **never made** |
| v1.4b | `CSM0/CSM1` (active or passive CAN monitoring), `JHF`, `JTM` |
| v2.0 | 512-byte RS-232 TX buffer, Activity Monitor `AMC`/`AMT` |
| v2.1 | `CTM1/CTM5`; handles `7F xx 78` response-pending; blocks sends on a CAN bitrate mismatch |
| v2.2 | `IB12`, `IB15`, `CER`, `IFR4/5/6` |
| v2.3 | extra filtering, RS-232 noise tolerance [E2] |

- **KWP headers.** `ATSH` sets three header bytes for ISO 14230; the ELM327 inserts the length in
  the first byte, or adds a fourth length byte when that byte's low nibble is 0 [E1, p. 25]. There is
  **no one-byte (no-address) header mode**. Fast init (`ATSP5`, `ATFI`) uses fixed timing; `ATIIA`
  changes the 5-baud init address only [E1, pp. 18–19]. `ATWM` sets the periodic keep-alive, which
  the chip transmits by itself while a protocol is open (default `C1 33 F1 3E` for KWP) [E1, p. 25].
- **Monitoring throughput.** The CAN engine keeps up with a 40 %-loaded 500 kbit/s bus; the RS-232
  side does not. Per 11-bit frame the send time is about 5.2 ms at 38.4 kbit/s, 1.7 ms at
  115.2 kbit/s and 0.4 ms at 500 kbit/s; with headers on, spaces and linefeeds off [E1, p. 75].
  A 500 kbit/s bus at 40 % load carries a frame about every 354 µs, so a 38.4 kbit/s Bluetooth
  link sees under 10 % of it and 115.2 kbit/s about 20 % before **`BUFFER FULL`** stops the monitor
  and returns to the prompt [E1, pp. 75–76]. Filters (`CRA`, `CF`/`CM`) are the only cure.
- **Silent monitoring.** From v1.4b `CSM1` makes monitoring passive (no ACKs) [E1].

### 2.2 Clones

- Pirated firmware: Elm did not enable copy protection on v1.4 parts, so clones run copied v1.4(b)
  code and **report later version numbers** ("v1.5", "v2.1") while keeping v1.4's limits [E2].
- Reported defects [E3][K1]: about half the original commands answer `?` (for example `ATPP2ASV38`,
  `ATR1`); some clones **read no more than two bytes of a command string**, so a longer request
  (multi-PID or a UDS DID) is silently truncated; **no `CSM`**, so a monitoring clone ACKs frames,
  and immediately after sending a frame it is in "receive reply" mode and ACKs everything [K1];
  RTR frames are dropped or cannot be sent; bitrates only as 500 kbit/s divided by n [K1].
- Hardware gaps (U, widely reported, not verified here): many cheap boards omit the K-line
  transceiver or the J1850 parts, so `ATSP3`–`5` fail on K-line cars; Bluetooth modules fixed at
  38.4 kbit/s; Wi-Fi units that are a fixed TCP endpoint (often `192.168.0.10:35000`) with the
  phone losing its uplink while joined.
- **Protocol search transmits.** `ATSP0` (automatic) sends a request on each protocol in turn,
  including CAN at bitrates that may be wrong for the bus; v2.1 added a frequency check that blocks
  sends on a mismatch [E1], clones lack it (U). A wrong-rate CAN transmit makes error frames on a
  live bus: exactly what ADR-0023 forbids outside a Parked probe.

### 2.3 Detecting a clone (tests for the spec)

Run on connect, with the vehicle Parked for anything that touches the bus:

1. **Identity strings:** `ATI`, `AT@1`; `STI`, `STDI`, `STMFR` for STN parts [S1]; vLinker answers
   both sets (U). "v1.5" or "v1.4a" means clone at once (never made [E1]).
2. **Version-gated command battery** (offline, no bus traffic): for the claimed version send one
   command introduced at or before it (`CSM1` ≥ v1.4b, `AMC` ≥ v2.0, `CTM1` ≥ v2.1, `IB12` ≥ v2.2)
   and expect `OK` or a value, never `?`. A claimed v2.1 that rejects `AMC` is a clone.
3. **Command-length test** (Parked, ignition on): a four-byte multi-PID request `01 00 20 40`
   on a CAN car must return all three support bitmaps in one reply; a reply for `00` alone, or
   `?`, shows a clone that truncates commands [E3].
4. **Monitor test** (Parked, CAN cars only, filters off, 10 s): count frames before `BUFFER FULL`;
   record frames per second. This sets the adapter's sniff rating, never a pass/fail on its own.
5. **Latency test:** median and p95 of `0100` round trips over 20 requests (Bluetooth Classic,
   BLE and Wi-Fi differ by tens of ms).
6. **K-line presence** (Parked, only when the vehicle profile says K-line): `ATSP3`/`ATSP5` must
   reach `BUS INIT: ...OK`, else the board has no usable K-line.

The verdict (genuine, compatible, limited, clone, unknown) downgrades capabilities; it never
upgrades a capability we could not verify (CanLink spec §2's rule). An "ELM327 Identifier"-style
battery of about 114 commands exists in a closed Android app [E4]; ours is short and data-driven.

## 3. STN chips and OBDLink adapters

- **Chips.** STN11xx, STN21xx and STN22xx share one command set: ELM327 AT commands plus the
  **ST** set [S1][S4]. The FRPM Rev E (2025-03-28) lists the OBDLink MX+ (STN2255/STN2256), EX
  (STN2230–2232), LX (STN1155) and the obsolete MX Wi-Fi (STN1152); the stand-alone STN1110,
  STN1170, STN2100 and STN2120 ICs are now marked obsolete [S1].
- **Commands that matter to us** [S1]:
  - `STPX h:…, d:…, t:…, r:…` sends an arbitrary message with its own header, timeout and expected
    reply count; messages up to 4 kB on MX+/EX/STN21xx, 2 kB on LX and STN11xx.
  - **`ATSH` on ISO 14230 accepts 1-, 2-, 3- or 4-byte headers**; a format byte with A1A0 = 00 and
    non-zero length bits is a one-byte header (no address bytes). This is the format the Td5 and
    SLABS use (§6).
  - **`STIFI low_ms, high_ms, message`** performs a custom ISO fast init with any init message,
    header and check byte included (default `25, 25, C133F18166`).
  - `STIIAP`, `STITW` set 5-baud init address parity and the W-timings; `STIP4` sets P4.
  - **`STCMM 0|1|2`**: CAN monitor mode; **0 = receive only, no ACKs (default)**, 1 = normal node,
    2 = also frames with errors. `STMA`/`STM` monitor; `STCAF`, `STCFCPA` for addressing and flow
    control; `STCSEGR/T` reassembles or segments ISO-TP in the chip; `STPPMA` periodic messages.
  - `STVR` battery voltage; `STSLPAS`/`STSLx` sleep control; `STBR` up to 2 Mbit/s on UART parts.
- **STN2120 RAM is "over five times" the nearest competitor's**, which "virtually eliminates"
  buffer overflows [S4]; earlier OBDLink firmware fixed `BUFFER FULL` on busy buses
  ([canbus_headunit.md](canbus_headunit.md) [S3]).
- **Products** [S2][S3][S5]:

| Model | Link | iOS | Notes |
|---|---|---|---|
| **MX+** | Bluetooth 3.0 Classic | yes, **MFi** | all OBD-II protocols plus MS-CAN and SW-CAN |
| **LX** | Bluetooth 3.0 Classic | no | no MS-CAN/SW-CAN |
| **EX** | USB only | no | MS-CAN; FTDI-class USB serial (U) |
| **CX** | **BLE only** (v5.1) | yes | HS-CAN and K-line pins; "optimized for BMW", not GM, Ford or some pre-2008 FCA; max MTU 247; Android default MTU 23 means 20-byte writes must be chunked; no queued writes; bonding window 5 min after power-on |

## 4. Other ELM-class adapters

- **Vgate vLinker** (MC+ BLE, FS USB, FD/FD+): own MIC331x-class chip claiming ELM327, ELM329
  and STN instruction sets [V1][V2]; FS lists up to 3 Mbit/s, 4128-byte requests and an 8 kB
  buffer [V1]. Retail listings only; treat its ST-command support as **(U)** and run the clone
  battery on it like any other.
- **Veepeak** (OBDCheck BLE, BLE+, Mini Wi-Fi, Mini BT): BLE models work with iOS, Mini BT is
  Android only [V3]. Chip and firmware are not published (U); run the battery.
- **WiCAN (ESP32-C3) and WiCAN Pro (ESP32-S3)** [W1][W2]: open firmware (GPL-3), protocols
  `slcan`, RealDash 66, SavvyCAN/GVRET, ELM327 emulation and AutoPID with MQTT and Home Assistant;
  TCP port 3333; **ships in `normal` (transmitting) CAN mode**. The Pro adds an STN-compatible
  interpreter IC for K-line and J1850, so (ADR-0039 §2) its K-line is interpreter-owned: generic
  K-line OBD reads at most, never our gated K-line. Already supported through `SlcanLink` over TCP
  ([CanLink spec](../../specs/2026-10-06-canlink-isotp-design.md) §10).
- **Macchina M2 / A0** [M1]: M2 is an open SAM3X board with two CAN, two LIN/K-line, J1850 and
  SW-CAN, Arduino-programmable and used with SavvyCAN; A0 is an ESP32 CAN dongle. Its J2534 code
  has no licence ([landscape.md](landscape.md)). A good open K-line bench tool, not a consumer adapter.

## 5. Raw links: KKL cables and SocketCAN dongles

### 5.1 KKL / FTDI "VAG-COM" cables

- A KKL cable is a **passive level shifter**: USB-UART (FTDI FT232R, CH340 or CP210x) plus a
  K-line transceiver, with no protocol logic. The host does init, framing, timing and checksums,
  which is why VAG and Td5 tools that need raw mode require one and cannot use an ELM [F2].
- **Fast init (25 ms low, 25 ms high)** is done in our code either by a UART break or by sending
  `0x00` at about 360 baud. On Linux the `ftdi_sio` driver clamps 360 baud, giving a 2 ms pulse
  and no wake-up; the OS-timed break gave 26 ms and `C1` first time (measured in the D2,
  2026-08-21; `serial_transport.py`). macOS handles 360 baud. CH340 and CP210x break behaviour is
  (U).
- **5-baud init** is a bit-banged break at 200 ms per bit; scheduler jitter is tolerable at 5 baud.
- **Latency timer:** FTDI parts hold a non-full RX buffer up to **16 ms by default** before sending
  it to the host; on Linux it is set in `/sys/bus/usb-serial/devices/ttyUSBx/latency_timer`, and it
  can revert to 16 on reconnect [F1]. With 16 ms the host misses P2/P3 windows and every host
  timestamp is smeared by up to 16 ms; set 1 ms on open.
- **Half duplex:** the cable echoes every byte sent; the K-line layer discards the echo
  (`tolerant=True`, Constitution protocol rules).
- **K+DCAN cables** (BMW INPA style) are FTDI cables with a K-line/D-CAN switch on a modem line (U);
  as a K-line cable they behave the same.

### 5.2 SocketCAN dongles

- **CANable / candleLight / CANtact (gs_usb)**: mainline `gs_usb` driver, MIT firmware, full-rate
  sniffing, `ip link … listen-only on` verifiable; the cheapest reliable bench sniffer
  ([canbus_headunit.md](canbus_headunit.md) A1). The CANable's alternative slcan firmware is a
  serial line protocol with millisecond `Z1` timestamps and only `F` status flags for errors (our
  `SlcanLink` reports `error_frames: "flags"`).
- **PCAN-USB**: mainline `peak_usb` driver since Linux 3.4; its hardware timestamps are passed up
  without drift correction (PEAK's own package corrects drift) [P2]. **Kvaser**: mainline
  `kvaser_usb`; Kvaser's own release notes record a fixed bug where an interface stayed in
  listen-only [P3]. On macOS and Windows both work only through vendor libraries and python-can
  (our optional `[can]` extra).
- **can327**: a kernel line discipline turning an ELM327 into a SocketCAN device; half duplex,
  frames lost at `BUFFER FULL`, clones ACK while monitoring, RTR limits; "suits simple
  request-response protocols … and monitoring broadcast messages" [K1]. A degraded path, labelled
  as such.

### 5.3 J2534 pass-thru

The API is specified for 32-bit Windows DLLs; some vendors ship 64-bit or Linux builds [J1]. Open
efforts: GenericDiagnosticTool (Windows tool) [J2], a Rust crate [J3], Qt's PassThruCAN plugin
[J4], dschultzca/j2534 for Linux ([canbus_headunit.md](canbus_headunit.md) [J2]). J2534 tools are
mostly bought for reflashing (Tier 4 for us, disabled). Value to Ostler: low until a Windows mechanic
user asks; keep it last, as ADR-0020 does.

## 6. The Discovery 2 question: can a third-party adapter read the D2?

The D2 pack's own profiles
([`kline_profiles.py`](https://github.com/openostler/ostler-pack-lr-d2/blob/main/src/d2diag/kline_profiles.py),
[protocol state](https://github.com/openostler/ostler-pack-lr-d2/blob/main/references/protocol_state_handoff.md)):
Td5 fast init `81 13 F7 81 0C` → `C1 57 8F`, then **unaddressed frames** (`header: none`, length in
the format byte, for example `02 3E 01 41`) with tester address `F7`; SLABS functional fast init at
`0x29` with a long silent period before init and the same unaddressed frames; BCU (`0x40`) and
airbag (`0x5B`) 5-baud slow init, the airbag with addressed frames `82 5B F7 …`.

| Module | KKL/FTDI cable | Genuine ELM327 | Clone ELM327 | STN (OBDLink) | WiCAN Pro | Ostler node |
|---|---|---|---|---|---|---|
| **Td5** (fast init, 1-byte headers, seed-key) | **Proven** (the dev path) | **No**: no 1-byte header; fixed init message | No | **Candidate**: `STIFI 25,25,8113F7810C` then a 1-byte `ATSH`; keep-alive and P3 by host; bench it | No (interpreter; ADR-0039 §2) | Production path |
| **SLABS** (functional fast init, silent period, bare `3E`) | **Proven** | No | No | Candidate, as Td5; the 28 s quiet period and init tolerances are the risk | No | Production path |
| **Airbag** (5-baud `0x5B`, addressed `82 5B F7`) | Proven reads | Plausible: `ATSP4`, `ATIIA 5B`, `ATSH 82 5B F7`, `ATTA F7`, `ATKW0` (U) | Unlikely (truncation, missing commands) | Plausible (U) | Read at most | Production path |
| **BCU** (5-baud `0x40`) | Proven init; live data not yet decoded | As airbag (U) | Unlikely | Plausible (U) | Read at most | Production path |

So: **a KKL/FTDI cable is the only proven third-party path for the D2**, and it is the one the
platform already drives. An STN adapter is worth one bench session (owner test plan item); a
genuine ELM327 can at most reach the 5-baud modules; clones should be refused for D2 manufacturer
protocols. Seed-key needs nothing from the adapter (the host computes the key), but Td5 security
and output services stay pack- and tier-gated whatever the adapter.

## 7. Hosts and transports

| Host | USB serial | BT Classic (SPP/RFCOMM) | BLE | Wi-Fi TCP | SocketCAN | Notes |
|---|---|---|---|---|---|---|
| **Brain (Pi, Linux)** | pyserial | **stdlib** `socket.AF_BLUETOOTH, BTPROTO_RFCOMM` after BlueZ pairing [Y1] | needs a library: `bleak` (MIT) over BlueZ D-Bus [Y2] | stdlib | stdlib `AF_CAN` | Everything; but ADR-0032 says the Brain never touches the car (spec §3) |
| **Laptop, Linux** | yes | yes (as Brain) | `bleak` | yes | yes | The lab |
| **Laptop, macOS** | `/dev/cu.*` | a paired SPP device appears as `/dev/cu.*` (U on current macOS) | `bleak` (CoreBluetooth) | yes | no (python-can vendor libs for PCAN/Kvaser) | Constitution: never `/dev/tty.*` |
| **Laptop, Windows** | COM ports | virtual COM port after pairing | `bleak` (WinRT) | yes | no (python-can) | Only host for J2534 DLLs |
| **Phone app, Android** (Capacitor wrapper, ADR-0032 §11) | USB OTG serial via a native plugin (U) | native SPP via a plugin (U) | native BLE plugin (U) | yes | no | All ELM-class adapters |
| **Phone app, iOS** | no | **only MFi accessories** through the External Accessory framework; plain SPP impossible [C1] | yes | yes | no | MX+ via MFi needs the accessory maker's app approval (U) |
| **Browser, Chrome/Edge desktop** | Web Serial | Web Serial to paired RFCOMM services [B3] | Web Bluetooth (GATT only) [B1] | no raw TCP | no | No install; Chromium only |
| **Browser, Chrome Android** | no (USB serial pending) [B2] | **Web Serial over RFCOMM from Chrome 137** [B2] | Web Bluetooth | no | no | |
| **Safari (macOS, iOS), Firefox** | no | no | **no Web Bluetooth** [B1] | no | no | Use the app |

Points that follow:
- **Web Bluetooth is BLE (GATT) only, never Classic** [B1]; with Web Serial's RFCOMM support
  [B2][B3], a Chromium browser covers BLE and paired Classic adapters, but no browser on iOS does.
- **iOS sees BLE, Wi-Fi and MFi adapters only** [C1]; the common Classic ELM clone is useless on an
  iPhone.
- **BLE needs chunking** to the negotiated MTU (20-byte writes at Android's default 23) [S3]; there
  is no standard ELM-over-BLE GATT profile (each vendor uses its own service UUIDs, U), so the
  known-good list must carry them.
- Our K-line timing rules (fast init, P3, the SLABS quiet period) need a **wired KKL or an
  interpreter that owns timing**. Raw K-line bytes over Bluetooth or the network are rejected for the
  same reason ADR-0039 rejected raw serial over the network.

## 8. Feature × adapter matrix (against the Ostler node)

Bus load figures are for a 500 kbit/s bus at 40 % load (about 2,800 frames/s, [E1]); "host ts" means
the timestamp is taken by the host on receipt.

| Adapter | Live OBD PIDs | DTC read / clear | Raw CAN sniff | K-line manufacturer (D2) | UDS / ISO-TP | Transmit / actions | Wake, sleep, power | Buses | Timestamps |
|---|---|---|---|---|---|---|---|---|---|
| **Ostler node** (Diagnostics) | yes, node-decoded | yes; clear via gate (ADR-0033 §5) | full rate, TWAI listen-only, MCU µs | **yes** (production) | own ISO-TP, Tier 0 reads, more by grant | **hardware gate on the node**, signed grants | sleeps, wakes Brain, 12 V floors (ADR-0040) | K-line + CAN (+ more per board) | MCU µs, mapped to UTC |
| **KKL/FTDI cable** | K-line OBD only (ISO 9141, KWP) | yes (host) | — | **yes, proven** | KWP2000 only | host soft gate | none; host-powered USB | 1 K-line | host ts after FTDI latency (set 1 ms) |
| **ELM327 genuine v2.x** | yes, all OBD protocols | yes | filtered only; ~20 % of a 40 % bus at 115.2k before `BUFFER FULL`; passive with `CSM1` | 5-baud modules at most (U) | in-chip ISO-TP; single request/reply; `ATH1` keys by ECU | soft gate; chip auto-sends keep-alives | low-power mode via pin/`LP`; no wake output | 1 active protocol | host ts only |
| **ELM327 clone** ("v1.5"/"v2.1") | yes, slower; multi-PID may truncate | read yes; clear (U, verify) | poor: under 10 % at 38.4k; **ACKs while monitoring** | no | short requests only | read-only recommended | often no sleep; drains battery (U) | 1 | host ts |
| **STN / OBDLink MX+, EX, LX, CX** | yes, fast | yes | good; `STCMM 0` passive; big buffers; BT/BLE caps the rate | **candidate** (1-byte headers, `STIFI`) | `STPX`, `STCSEGR/T`, flow-control pairs | soft gate | `STSL*` sleep, `STVR` voltage | 1 at a time; MS-CAN/SW-CAN on MX+ | host ts (U: any chip timestamp option) |
| **vLinker / Veepeak** | yes | yes | (U) | (U) vLinker's ST claim | (U) | soft gate | (U) | 1 | host ts |
| **WiCAN / WiCAN Pro** | yes (ELM emulation, AutoPID) | yes | yes, slcan/GVRET over Wi-Fi; **ships transmitting**, set `silent` | Pro: interpreter reads only | via host ISO-TP on slcan | soft gate; never its MQTT `can/tx` | own sleep on voltage (U) | 1 CAN | device ms (slcan) or µs (GVRET) |
| **gs_usb (CANable/candleLight)** | via our ISO-TP | yes | **full rate**, verifiable listen-only | — | host ISO-TP, kernel `CAN_ISOTP` | soft gate | none | 1 CAN (2 on some) | kernel, hardware where firmware supports it (U) |
| **slcan firmware dongles** | via our ISO-TP | yes | ok at moderate load; errors as flags | — | host ISO-TP | soft gate | none | 1 | device ms |
| **PCAN-USB / Kvaser** | via our ISO-TP | yes | full rate | — | host ISO-TP | soft gate | none | 1–2 | hardware (PCAN without drift correction in mainline) |
| **can327 (ELM as SocketCAN)** | yes, degraded | yes | best effort, half duplex | — | kernel ISO-TP over a half-duplex link | soft gate | none | 1 | host ts |
| **Macchina M2** | firmware-defined | firmware-defined | yes (SavvyCAN) | possible (own K-line), bench only | firmware-defined | soft gate | firmware | 2 CAN + 2 K-line | device |
| **J2534** | yes | yes | vendor-dependent | vendor-dependent | yes | soft gate; reflash disabled (Tier 4) | none | vendor | vendor |

What no third-party adapter gives: **a hardware gate in the car**, the **raw tap with MCU
timestamps** and identity scrub at the source (ADR-0039 §3), **always-on** functions (alarm,
geofence, wake of the Brain, 12 V watchdog; ADR-0040), and the node's K-line on any profile.

## 9. Known-good list (what is verifiable today)

Nothing below has been bench-tested by the project. "Documented" means the vendor's own document
says so; "in use" means our code already drives that class.

| Adapter | Chip / firmware | Status | Evidence |
|---|---|---|---|
| FTDI FT232R KKL ("VAG-COM 409.1") | FTDI, passive | **in use, car-proven on the D2** | D2 pack logs 2026-08 (`serial_transport.py` notes) |
| OBDLink MX+ | STN2255/2256 | documented: all OBD-II, MS-CAN, SW-CAN, iOS (MFi) | [S1][S2][S5] |
| OBDLink EX | STN2230–2232 | documented: USB, MS-CAN | [S1][S2] |
| OBDLink CX | STN, BLE 5.1 | documented: BLE only, HS-CAN + K-line pins, not GM/Ford | [S2][S3] |
| OBDLink LX | STN1155 | documented: Classic BT, no iOS | [S1][S2] |
| CANable / candleLight (gs_usb) | candleLight_fw (MIT) | in use as `SocketCanLink` class | [canbus_headunit.md](canbus_headunit.md) |
| WiCAN Pro | wican-fw (GPL-3) | in use as `SlcanLink` TCP class; set `silent` | [W1][W2] |
| PCAN-USB, Kvaser | mainline drivers | in use via SocketCAN or python-can | [P2][P3] |
| vLinker MC+/FS, Veepeak BLE | undisclosed | **unverified**: run the clone battery | [V1][V3] |
| Any "ELM327 v1.5/v2.1" | copied v1.4(b) | **not recommended** | [E2][E3][K1] |

The list belongs in data (the spec proposes `adapters.json` with tested firmware, date and
evidence per entry), filled by owner bench runs and by community reports with logs.

## 10. Styling and Copy / Avoid / Decide

**Copy.** Car Scanner's per-make connection profiles and its adapter setup pages
([ui/obd_apps.md](ui/obd_apps.md)); OBDLink's honest per-model compatibility table [S2]; the kernel's
plain statement of can327's limits [K1]; WiCAN's visible normal/silent switch.

**Avoid.** Silent protocol search on a moving car; hiding that a clone is a clone; treating
"listen-only requested" as listen-only; relaying raw K-line bytes over Bluetooth or the network;
promising iPhone support for Classic adapters.

**Decide** (in the spec): where adapters may run given "the Brain never touches the car"; a software
gate's limits; core or add-on packaging; whether clones are refused or read-only.

## Sources (read 2026-10-07)

- [E1] ELM327 datasheet (ELM327DSK, firmware v2.2): https://www.elmelectronics.com/wp-content/uploads/2017/01/ELM327DS.pdf
- [E2] ELM327, Wikipedia (versions, clones, company closure): https://en.wikipedia.org/wiki/ELM327
- [E3] FORScan forum, known problems with clones: https://forum.forscan.org/viewtopic.php?p=5601
- [E4] ELM327 Identifier (closed app, command battery): https://www.bluestacks.com/campaign/com.applagapp.elm327identifier/it
- [K1] can327 kernel documentation: https://docs.kernel.org/networking/device_drivers/can/can327.html
- [S1] OBDLink Family Reference and Programming Manual, Rev E (2025-03-28): https://www.scantool.net/scantool/downloads/682/obdlink_frpm_f.pdf
- [S2] OBDLink adapter compatibility: https://support.obdlink.com/support/solutions/articles/43000713351
- [S3] OBDLink CX adapter notes: https://support.scantool.net/support/solutions/articles/43000746707-obdlink-cx-adapter-notes
- [S4] STN2120 product page: https://obdsol.com/solutions/chips/stn2120
- [S5] OBDLink MX+ product page (MFi): https://scantool.net/obdlink-mxp/
- [V1] vLinker FS listing (indicative): https://manuals.plus/asin/B0DJSYGZ58
- [V2] vLinker MC+ retailer listing (indicative): https://www.empik.com/vgate-vlinker-mc-4-0-interfejs-bimmercode-forscan,p1624850943,motoryzacja-p
- [V3] Veepeak BLE+ vs BLE comparison (indicative): https://obdplanet.com/veepeak-obdcheck-ble-plus-vs-ble/
- [W1] WiCAN firmware: https://github.com/meatpiHQ/wican-fw
- [W2] WiCAN Pro: https://www.crowdsupply.com/meatpi-electronics/wican-pro
- [M1] Macchina M2 hardware: https://github.com/macchina/m2-hardware
- [F1] FTDI Linux USB latency: https://granitedevices.com/wiki/FTDI_Linux_USB_latency
- [F2] KKL vs ELM327 (raw mode), elektroda: https://www.elektroda.com/rtvforum/topic2848768.html
- [P2] PEAK-System Linux drivers: https://www.peak-system.com/fileadmin/media/linux/index.php
- [P3] Kvaser SocketCAN driver release notes: https://pim.kvaser.com/var/assets/Product_Resources/7330130982192/1.23.358/releasenote-socketcan_kvaser_drivers.txt
- [J1] Quantex J2534 overview: https://quantexlab.com/de/develop/j2534.html
- [J2] GenericDiagnosticTool: https://github.com/jakka351/GenericDiagnosticTool
- [J3] j2534 Rust crate: https://docs.rs/j2534
- [J4] Qt PassThruCAN plugin: https://doc.qt.io/qtforpython-6/overviews/qtserialbus-passthrucan-overview.html
- [B1] Web Bluetooth API (MDN): https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API ; browser support summary: https://www.beaconzone.co.uk/blog/browser-support-for-web-bluetooth/
- [B2] Chromium intent to ship, Web Serial over Bluetooth on Android (M137): https://groups.google.com/a/chromium.org/g/blink-dev/c/BqUGCcurReE/m/XbuAYkRxEQAJ
- [B3] Chromium intent to ship, Web Serial for Bluetooth RFCOMM: https://groups.google.com/a/chromium.org/g/blink-dev/c/P4YwDCcvdvs/m/CHbyTu_gAAAJ
- [C1] Car Scanner, choosing an adapter (iOS: BLE, Wi-Fi, MFi only): https://www.carscanner.info/?p=40
- [Y1] Python `socket` (AF_BLUETOOTH, BTPROTO_RFCOMM): https://docs.python.org/3/library/socket.html
- [Y2] bleak (MIT, cross-platform BLE): https://github.com/hbldh/bleak
