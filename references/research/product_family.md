---
title: "Product family — Ostler Diagnostics, Guardian and Brain; reference boards, node link, raw tap, uplinks, setup and wake"
area: references
status: stable
version: 1.1
updated: 2026-10-06
depends_on: [decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0037-role-holders-and-handover.md, references/research/hardware.md, references/research/connectivity_uplink.md, references/research/node_sensors.md, references/research/power_states.md, references/research/canbus_headunit.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  Live research (2026-10-06) behind ADR-0039 (accepted 2026-10-06) for the owner's naming and setup direction. Family: Ostler Diagnostics (the OBD-port node, standalone with a phone or linked to a Brain), Ostler Guardian (hidden node variant) and Ostler Brain; "node" stays the internal term. Reference boards: the MeatPi WiCAN Pro (ESP32-S3, $89, GPL-3 firmware, schematic published) reaches K-line only through an STN-compatible interpreter IC over a UART, so it fits CAN and generic OBD but not the Td5 gate or a byte-timed raw tap; a K-line Diagnostics board needs an L9637-class transceiver on an ESP32-S3 UART. Node-to-Brain link: USB-NCM (ESP32-S3 full-speed device via esp_tinyusb; cdc_ncm in Raspberry Pi OS, Windows 10 1903+ inbox) near the Brain, 10BASE-T1S elsewhere, same IP/MQTT either way; the S3 has one OTG port, so a USB-linked node cannot also host a 4G dongle. Raw tap: MCU-timestamped records batched over MQTT 5, scrubbed on the node, recorded on the Brain, with lab send-requests through the node gate. Standalone uplink: the official 4G module by default; dongles by class (PPP/AT, ECM, RNDIS on ESP32-S3; Espressif's tested list) with a tested-dongle list. Setup mode: AP + BLE Improv, helper steps pair → uplink → pack → first scan; Brain adoption. Brain-only wake: the Brain's power board (ignition, RTC), no separate buddy. u-blox on the Diagnostics node.
---

# Product family: Diagnostics, Guardian and Brain

Research for the owner's direction of 2026-10-06 on naming and setup. Decision:
[ADR-0039](../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md) (accepted
2026-10-06 with the owner's answers). It builds on
[ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md) (one node, optional brain),
which this renames and does not re-decide. Facts were checked live on **2026-10-06**; **(U)**
marks what is unverified or needs the bench. Sources are paraphrased.

## 1. The family

| Product (public name) | Internal term | Hardware | Owns |
|---|---|---|---|
| **Ostler Diagnostics** (was "Ostler Lite") | node, diag-port variant | ESP32-S3 (PSRAM) at the OBD port: K-line and CAN front ends, 12 V and ignition sense, a 10 Hz u-blox, optional 4G module or a USB 4G dongle | The car: bus I/O, decode to VSS, **the transmit gate**, the raw tap, timing; the parked broker; brain power and wake (ADR-0032 §2, §4) |
| **Ostler Guardian** | node, guardian variant | Same firmware; hidden, backup cell, IMU, tamper, modem GNSS, 4G; **no outputs** | Tracking and alarm triggers; standby parked broker and time source (ADR-0037, proposed) |
| **Ostler Brain** (was "Ostler Hub", and before that "Ostler" with a brain) | brain | Pi 5 class Linux box with a power board | Compute and network: the full app, logbook, replay, the Python decode lab, uplink manager, local CA; **never touches the car** |

- **Standalone:** a Diagnostics node and a phone. The node records, serves its own page and
  the phone app (BLE or its AP), and brings its own uplink if any (§5).
- **With a Brain:** plug a Diagnostics node into a Brain (USB-NCM or T1S, §3). The Brain adds the
  full app, the lab and its uplink; nothing changes on the car side (ADR-0032 §1).
- **Brain-only:** a Brain with no Diagnostics node (cameras, logging, a third-party OBD adapter on
  the lab path). It has no gate and no parked broker; it needs its own wake source (§8).
- "Node" stays the term in code, topics, manifests and ADRs (`kind: node`, `variant:
  diag-port|guardian|sensor`); only public names change. The app-model `product` value
  `lite` becomes `diagnostics` (decided, ADR-0039).
- **Hardware-agnostic:** the firmware selects a board profile at build or by NVS `board_id`
  (ADR-0032 Amendments B, firmware `docs/specs/sensor-detection.md`),
  so any board that meets §2's minimum can be a Diagnostics node.

## 2. Reference-board survey

**Minimum for a K-line Diagnostics node:** ESP32-S3 with PSRAM; a K-line transceiver
(L9637/MC33290/Si9241 class) on an S3 UART so the node owns init timing, keep-alive and
per-byte timestamps; one or two CAN transceivers on TWAI; 12 V input with load-dump
protection; ignition sense; a brain-power output. Muki01's reader shows the transceiver
circuits ([muki01 notes](muki01/obd2_kline_reader.md)).

| Board | MCU | CAN | K-line path | Licence and openness | Verdict |
|---|---|---|---|---|---|
| **MeatPi WiCAN Pro** ($89; Crowd Supply pre-order ships about 28 Dec 2026) | ESP32-S3-WROOM-1-N16R8 (16 MB flash, 8 MB PSRAM) | 3 CAN protocols + single-wire CAN | ISO 9141-2 and ISO 14230 slow/fast **through an OBD interpreter IC**: the firmware drives it with ELM327/STN AT commands over a UART at 2 Mbaud (`STSLCS`, `ATPP`), resets it by GPIO and flashes it with a closed image (`main/obd_fw/V2.3.x`). The ESP32 does not see K-line bytes | Firmware GPL-3.0 ([wican-fw](https://github.com/meatpiHQ/wican-fw), `wican-pro` branch, last commit 5 Sep 2026); schematic v1.51 published as PDF; PCB files (U) | **CAN and generic OBD candidate. Not for the Td5 gate or the raw tap:** init timing, keep-alive and P-timings live in the interpreter, there are no per-byte timestamps, and LR-specific fast init with seed-key is untested through STN commands (U). Its USB-C has a Type-C CC controller (WUSB3801) and a 5 V/1.5 A host port, useful for a dongle (U: data roles) |
| **Freematics ONE+ B/H** | ESP32 + an OBD/GNSS co-processor | CAN | KWP2000 fast and 5-baud via the co-processor | Arduino libraries open; co-processor closed | Same problem as WiCAN: K-line hidden behind a co-processor |
| **Macchina A0** | ESP32 (classic) | CAN | none | open firmware | CAN only |
| **Macchina M2** | SAM3X | CAN | 2× K-line/LIN | open | Direct K-line, but not ESP32; reference only |
| **OVMS v3.3** | ESP32 | 3× CAN | separate K-line board | MIT firmware | Reference and interop rig ([ovms](ovms.md)) |
| **Our dev build:** ESP32-S3 DevKitC-1 (N16R8) + L9637D-class + SN65HVD230 | ESP32-S3 | TWAI | direct UART | ours | **The K-line reference for now**; the D2's existing K-line node circuit carries over. L9637D is obsolete; MC33290 and Si9241 are the live alternatives (check LIN parts' dominant timeout, which cuts a 200 ms 5-baud bit) |

**Recommendation:** the reference Diagnostics board for K-line cars is an ESP32-S3 with a
discrete K-line transceiver (dev build now, our own board later, [hardware](hardware.md#path-to-our-own-hardware)).
The WiCAN Pro is a supported **CAN-only board profile** (generic OBD on CAN, J1939, sniffing
in `silent` mode), with our firmware on it; its interpreter may serve generic K-line OBD
reads (Read only, Tier 0), never gated K-line writes. Reusing WiCAN code means GPL-3 rules
under ADR-0025 (whole, in a marked module); writing our own board profile avoids that.

## 3. The node-to-Brain link

| Link | When | Physical | Strengths | Limits |
|---|---|---|---|---|
| **USB-NCM** (CDC-NCM; ECM fallback) | Brain within a USB cable of the port (under the dash, behind a seat) | One USB cable | No network setup: the Brain sees a NIC; one cable carries data and can supply 5 V; Improv serial works on the same port before the network is up | Full speed only on the ESP32-S3 (12 Mbit/s wire, a few Mbit/s real, U); cable ≤ 5 m; not automotive-grade; uses the S3's **only** OTG port |
| **10BASE-T1S** (ADR-0026) | Brain elsewhere in the car | One twisted pair, multidrop | Automotive, 25 m, other modules share the segment; PLCA | LAN8651 SPI MAC-PHY per node; T1S bench plan still to pass |
| **Ethernet** (SPI W5500 on the S3, which has no EMAC) | Bench, prototypes | RJ45 | Cheap, known | Not automotive; four wires |
| Wi-Fi | Fallback only | radio | no wiring | not for alarm-critical links (ADR-0026) |

- **ESP32-S3 USB device NCM:** Espressif's `tusb_ncm` example (ESP-IDF, esp_tinyusb on
  TinyUSB) runs on ESP32-S2/S3/P4 and presents the board as an NCM Ethernet-over-USB device;
  TinyUSB's netdev class also offers ECM and RNDIS. No throughput is published (U: bench;
  Espressif's FS host figures in §5 suggest 5–8 Mbit/s).
- **Hosts:** Raspberry Pi kernels build `CONFIG_USB_NET_CDC_NCM=m` (bcm2711 and bcm2712
  defconfigs, rpi-6.12.y), and `usbnet` is built in; Windows 10 1903+ and 11 ship an inbox
  NCM host (Windows 10 may need the driver picked by hand); macOS (U).
- **Addressing:** the USB link is its own routed subnet (ADR-0027 §3): IPv6 link-local plus
  the vehicle ULA /64, IPv4 by DHCP from the Brain; mDNS finds `_ostler-mod._tcp` on it.
- **Same everywhere:** IP, MQTT 5, mTLS, the VSS topics and the raw-tap topics are identical
  on USB, T1S and Ethernet (ADR-0027 §1).
- **Power:** the node is always powered from the car (OBD pin 16 or the harness). The Brain's
  VBUS may be ORed in as a second feed but never relied on: the node must wake the Brain, and a
  cut Brain has no VBUS (ADR-0032 §4). Pi 5 ports supply 600 mA in total, 1.6 A with a 5 A
  supply or `usb_max_current_enable=1`; a node (S3 Wi-Fi peaks about 350 mA, u-blox about
  30 mA, U) fits, a 4G dongle on the same feed does not.
- **One OTG port:** a USB-linked node is a USB device and cannot host a dongle at the same
  time; it uses the Brain's uplink or its own 4G module (§5–§6). The ESP32-P4 has two OTG
  controllers but no radio (later option, U).

**Recommendation:** USB-NCM for the bench and for hubs fitted near the port; T1S as the
product link otherwise; Ethernet for prototypes. Raw serial over the network stays rejected
(K-line init timing; it would move the gate to the brain).

## 4. Raw tap

The Diagnostics node gives two outputs: **decoded VSS** (as today) and a **raw frame stream**
timestamped on the MCU, for sniffing and the decode lab. The Brain records it and runs the
Python lab; the Brain **asks** the node to transmit, and never transmits itself.

**Record** (byte layout in the firmware draft, `docs/specs/raw-tap.md`):

| Field | Meaning |
|---|---|
| `t_us` | MCU monotonic µs since boot (64-bit), taken at the UART RX interrupt or TWAI RX; a per-session `boot_id` disambiguates restarts |
| `seq` | per-session counter; a gap means loss |
| `bus` | index into the session header's `bus_id` list (`kline-diag`, `can-hs`, …) |
| `dir` | `rx`, `tx_echo` (our own byte read back on the single-wire K-line, or TWAI self-reception) |
| `proto` | `kline_byte`, `kline_msg`, `can`, `can_fd` |
| `flags` | origin (`gate` for node-sent, `bus` for foreign), framing or CRC error, scrubbed |
| bytes | the data (CAN: id + DLC + data) |

**Events** in the same stream: `init` (method, address, the 5-baud or fast-init pattern with
its measured timing, result, keyword bytes), `keepalive`, `gate` (grant verified or refused,
with the reason, never the payload of a refused write), `session` (start/stop, filters),
`overflow` (dropped count), `time` (a pair `t_us` ↔ shared UTC, once a second), `link`.

**Time:** the node's clock is disciplined by the u-blox PPS where present (ADR-0032
amendment A3); `time` records let the Brain map `t_us` to UTC linearly between marks; without
sync the session is `time: unsynced` and is merged by order only.

**Rates:** K-line at 10 400 baud is under 1.1 kB/s of bytes, so per-byte records cost about
15 kB/s. A 500 kbit/s CAN bus at full load carries about 4 000 frames/s, about 100 kB/s
(0.8 Mbit/s) of records. Both fit USB FS and T1S. Per-byte timestamp precision depends on
the UART FIFO threshold (set to 1 byte for K-line; about 10–50 µs expected, U); edge capture
on the RX pin is the fallback.

**Buffering:** a PSRAM ring (proposed 2 MB, about 20 s of a saturated CAN bus) absorbs link
stalls; on overflow the oldest records go and an `overflow` event says how many.

**Transport, recommended: MQTT 5 with batching.** Batches of records (100 ms or 8 kB, whichever
first) as binary payloads on `ostler/v1/<vid>/<node>/tap/<session>/data`, QoS 1, never
retained, with MQTT 5 content type `application/vnd.ostler.tap.v1`; the session header is
retained on `…/tap/<session>/meta`. It reuses the broker, mTLS, per-device ACLs and bridges
(ADR-0026/0027), so nothing new is exposed. Per-record MQTT messages are rejected (overhead,
broker load). A separate TCP or WebSocket stream from the node is the fallback if the bench
shows the broker cannot keep a saturated CAN bus for 10 minutes without loss.

**Recording on the Brain:** the recorder subscribes, checks `seq`, writes the session into the
logbook beside decoded values (ADR-0032 §9), and exports to **pcapng** (CAN as SocketCAN
link type; K-line as a user link type with our record header) so Wireshark and candump-style
tools read it (ADR-0017).

**Identity scrub (ADR-0036):** the node frames K-line and ISO-TP messages before it emits
them, so it applies the pack's identity declarations (for example KWP `1A`, OBD `09 02`, UDS
`22 F190`) **on the node**, replacing the reply data with the fixed placeholder and setting
the `scrubbed` flag, unless the install-level option is on. With the option on, unscrubbed
bytes go only to the paired Brain over the in-car link and every export still scrubs. Bytes the
node cannot frame (an unknown foreign tool) are marked `unframed`; an export with unframed
segments drops them (decided, ADR-0039; the rest of the session still exports).

**Send-requests:** the Brain publishes a request on `…/<node>/lab/req` with a grant; the node's
gate classifies the service (read services on the pack's allowlist run as Read, Tier 0, in
service mode; anything else takes its tier and needs a matching grant; unknown services are
refused), serializes it with its own polling, and answers on `…/lab/resp`. Sniffed write
sequences are never replayed (CONSTITUTION). The gate never hands over (ADR-0037).

## 5. Standalone uplink

**Default: the official 4G module** on the Diagnostics board (SIM7670-class Cat-1, the same
modem family as the guardian, an IoT SIM): always on, no USB port used, known current.

**Bring your own USB dongle** (ESP32-S3 as USB host, Espressif esp-iot-solution):

| Class | ESP32-S3 driver | Status | Notes |
|---|---|---|---|
| Modem with PPP and AT over CDC-ACM | `iot_usbh_modem` (v2.2.0; dual interface: PPP data + AT) | supported | Slowest; signal and SIM via AT |
| ECM module or stick | `iot_usbh_ecm` | supported | Tested on S3: ML302, EC800E-CN, EC801E-CN, YM310, MC610-EU, Lierda NT26; ML307R and AIR720 SL fail on S2/S3 (endpoint size above 64 bytes at full speed); also CH397A, RTL8152B, NX7202D Ethernet adapters |
| RNDIS module or stick | `iot_usbh_rndis` | supported | Same module list, plus ML307R and AIR720 SL; S3 with softAP sharing measured 5.8 Mbit/s up, 7.9 Mbit/s down; some need an AT command to auto-dial |
| NCM sticks (some HiLink firmware) | none listed | (U) | Bench |
| QMI/MBIM modem-mode sticks | none | Brain only | ModemManager on the Brain (ADR-0028 §3) |

- Consumer HiLink sticks (Huawei E3372h class) present RNDIS or ECM depending on firmware;
  none is on Espressif's list (U: bench). Several listed modules are China-band parts; for the
  UK and EU, MC610-EU is the listed candidate (U: bands).
- Dongles draw bursts of 1–2 A at 5 V (U); the board needs a 5 V/2 A USB-A rail.
- A **tested-dongle list** lives in the firmware repo (skeleton in the firmware draft):
  model, firmware, class, VID:PID, bands, S3 status, Brain status, AT setup, peak and parked
  current, throughput, tester and date.

## 6. Uplink with a Brain

The Brain holds the **uplink manager** role (ADR-0037 §2, brain → node): it runs the owner's
Auto or pinned order over its own sources and offers a routed default to the node. The
node's own 4G module or Wi-Fi becomes one more source in the Brain's list, and the node's
fallback when the Brain sleeps. A **USB-linked** node has no dongle (§3), so its uplink while
the Brain sleeps is Wi-Fi or its 4G module; a **T1S-linked** node may keep a dongle. A guardian
alongside keeps its SIM for the alarm path.

## 7. Setup mode and the setup helper

**Setup mode** starts on first boot, after a factory reset, or by a long press. The node
raises a **Wi-Fi AP** (per-device SSID and a per-device password on the label and its QR,
never a shared default) and **BLE with Improv**; Improv serial also runs on the USB port. It
times out (proposed 15 min, re-entered only physically), offers no car actions and transmits
nothing on any car bus.

**Helper steps** (a core flow in the Network app, on the phone, the Brain or the node's page):

1. **Pair and set the owner.** Improv's physical authorisation (button press) or the label
   QR; the phone creates the owner's pairing key (standalone, ADR-0032 §12) or the Brain's CA
   issues the node certificate (with a Brain, ADR-0027 §8). The first person is the Owner.
2. **Uplink.** Improv scan and send Wi-Fi settings; or a detected dongle or the 4G module (APN,
   metered flag, budget); or "through the Brain".
3. **Pack.** Suggest one from the K-line profile or CAN detection (Parked only, ADR-0022/0023)
   or let the owner pick; install signed pack JSON (ADR-0032 risks).
4. **First scan.** Scan all (Read, Tier 0) with honest states (UI spec §4.3), snapshotted to the
   logbook.

Improv's post-provisioning **redirect URL** hands the browser to the node's page for steps
2–4. ESP-IDF unified provisioning (BLE or SoftAP, security 2 with SRP6a, custom endpoints,
about 110 kB for BLE) stays reference, as in ADR-0028 §7.

**The Brain adopts discovered devices:** unpaired devices advertise `_ostler-mod._tcp` with
`pr=0` and show as "nearby" on the Network page (UI spec §3.7). Adopting needs the owner on
the Brain and a physical press on the device (or, for a node already owned standalone, approval
from the owner's paired phone); the Brain's CA then issues the certificate and the roles follow
the owner's order (ADR-0037). There is no silent takeover.

## 8. Brain-only wake source

With a Diagnostics node, the node wakes the Brain and runs the parked broker (ADR-0032 §4).
Without one:

| Option | Wake sources | Parked draw | Notes |
|---|---|---|---|
| **Pi 5 alone** | power button (J2 header) from halt or standby; RTC `wakealarm` | about 3 mA halted with `POWER_OFF_ON_HALT=1`, `WAKE_ON_GPIO=0` (Raspberry Pi docs) | An ignition opto across J2 works, but a press while running asks for shutdown (U: design) |
| **CarPiHAT PRO 5** (£110) | 12 V ignition-switched, Pi-controlled latch and safe shutdown | under 1 mA off | Ignition only (U: other inputs as wake) |
| **Witty Pi 5 HAT+** (RP2350) | RTC schedule; VIN voltage thresholds (6–30 V in, up to 5 A out); temperature | about 0.7 mA itself, 2.5–3 mA with a Pi on I²C | A charging-voltage threshold can stand in for "engine running" (U) |
| **Sixfab Power Management HAT** | RTC schedule, MCU-controlled soft shutdown | (U) | Wake pins documented for the Pi 4 only |
| A small buddy MCU | anything | 1–5 mA | Re-creates the retired buddy |

**Recommendation:** no separate buddy. A Brain-only box takes its wake from its **power
board** (ignition plus an RTC schedule plus a low-voltage cut); it has no remote wake, no
parked broker and no alarm, which matches having no node. Anyone who wants those adds a
Diagnostics node or a **Guardian**, which is already the small always-on device and can wake
the Brain. Wake semantics are in ADR-0040 ([power states](power_states.md)).

## 9. u-blox placement (resolved the pending GPS question)

| Placement | For | Against |
|---|---|---|
| **Diagnostics node** | Present in standalone and Brain setups; gives the gate its own fast speed source; makes the node the best clock (PPS) for the raw-tap timestamps | Antenna cable from under the dash to the dash top |
| Brain (USB u-blox) | Easy on the bench | Absent standalone; asleep while parked; the gate must not trust a speed from another device |
| Guardian | Hidden antenna | 1 Hz modem GNSS already covers security; adds parked drain |

**Recommendation:** the 10 Hz u-blox sits on the **Diagnostics node** (as ADR-0032's
Amendments A1 proposed; decided by ADR-0039 §9); a USB u-blox on the Brain is the Brain-only option and the bench path;
the guardian keeps its modem GNSS and takes a u-blox on I²C only when it replaces the node.

## 10. Open questions

1. ~~"Ostler Hub" or "Ostler Brain" as the public name; `lite` → `diagnostics`.~~ **Decided
   (ADR-0039):** Ostler Hub at first, then **Ostler Brain** (ADR-0039 Amendments,
   2026-10-06); `lite` → `diagnostics`.
2. WiCAN Pro: confirm from schematic v1.51 that K-line reaches only the interpreter, and its
   USB-C data roles (still a bench item, ADR-0039 Confirmation).
3. ~~Raw-tap export of unframed bytes.~~ **Decided (ADR-0039):** dropped from exports.
4. MQTT batching values: **100 ms / 8 kB decided** (ADR-0039); the PSRAM ring size is still a
   bench item.
5. ~~Default USB-link power.~~ **Decided (ADR-0039):** data-only by default.

## Sources

- MeatPi WiCAN Pro product page, [Crowd Supply](https://www.crowdsupply.com/meatpi-electronics/wican-pro) (read 2026-10-06); [CNX Software](https://www.cnx-software.com/2024/08/22/wican-pro-esp32-s3-powered-obd-scanner-for-vehicle-diagnostics-with-smart-home-integration/) (2024-08-22); [wican-fw](https://github.com/meatpiHQ/wican-fw) source, `wican-pro` branch (`main/obd.c`, `main/hw_config.h`, `main/obd_fw/`), read 2026-10-06.
- [Freematics ONE+ Model B](https://freematics.com/products/freematics-one-plus-model-b/); [Macchina A0](https://www.sparkfun.com/macchina-a0-obd-ii-development-module.html) (2026-10-06).
- Espressif [tusb_ncm example](https://github.com/espressif/esp-idf/tree/master/examples/peripherals/usb/device/tusb_ncm); [USB host solutions](https://docs.espressif.com/projects/esp-iot-solution/en/latest/usb/usb_overview/usb_host_solutions.html); [ECM host](https://docs.espressif.com/projects/esp-iot-solution/en/latest/usb/usb_host/usb_ecm.html); [RNDIS host](https://docs.espressif.com/projects/esp-iot-solution/en/latest/usb/usb_host/usb_rndis.html); [iot_usbh_modem](https://components.espressif.com/components/espressif/iot_usbh_modem); [ESP-IDF provisioning](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/provisioning/provisioning.html) (2026-10-06).
- Raspberry Pi kernel defconfigs, [rpi-6.12.y](https://github.com/raspberrypi/linux/tree/rpi-6.12.y/arch/arm64/configs); [Pi documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) (power button, RTC wake, 3 mA halted); [USB power on Pi 5 white paper](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-009856-WP-1-USB%20Power%20delivery%20on%20Raspberry%20Pi%205.pdf) (2026-10-06).
- Microsoft [NCM driver](https://github.com/microsoft/NCM-Driver-for-Windows) and [Q&A on Windows 10/11 NCM](https://learn.microsoft.com/en-us/answers/questions/1531925/difference-in-usb-ncm-class-driver-behavior-for-wi) (2026-10-06).
- [Improv BLE spec v2.4](https://www.improv-wifi.com/ble/) (2026-10-06).
- [CarPiHAT PRO 5](https://thepihut.com/products/carpihat-pro-5-car-interface-dac-for-raspberry-pi-5); [Witty Pi 5 HAT+](https://www.uugear.com/product/witty-pi-5/) and [CNX Software](https://www.cnx-software.com/2026/01/19/witty-pi-5-hat-a-raspberry-pi-rp2350-based-power-scheduler-with-time-temperature-and-voltage-based-triggers/) (2026-01-19); [Sixfab Power Management HAT](https://docs.sixfab.com/docs/raspberry-pi-power-management-ups-hat-introduction) (2026-10-06).

## Changelog

- 2026-10-06 — v0.1, first draft for ADR-0039.
- 2026-10-06 — v1.0, ADR-0039 accepted: decided points marked in §1, §4, §9 and §10;
  "Ostler Lite" kept only where it says what was renamed.
- 2026-10-06 — v1.1, ADR-0039 amended: "Ostler Hub" renamed **Ostler Brain**; "hub" (our
  compute box) reads "Brain" throughout, including the §3, §6 and §8 headings.
