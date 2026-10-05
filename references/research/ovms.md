---
title: "OVMS (Open Vehicle Monitoring System) v2 + v3 — deep dive and interop plan"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/landscape.md]
summary: >
  What OVMS v2/v3 are (hardware, firmware components, metrics, poller, events, scripting, web UI, MQTT v3 topics, power management, ~48 vehicle modules, licences), why we don't adopt it as our supervisor, and what we copy and interoperate with instead (OVMS-compatible MQTT topics, metric names, per-state polling, events, staged power-down).
---

# OVMS v2 + v3: deep dive and interop plan

## TL;DR

- **v3 is mature and active.** Last tag 3.3.006 (May 2026), commits into October 2026.
- **Hardware:** an ESP32 module with 3× CAN and a SIM7600 4G/GNSS modem, about £235 with 4G.
- **No general K-line support.** The only K-line code reads TPMS IDs on the Tesla Roadster, over an optional £25 TJA1027 board on UART2 (GPIO33/32).
- **Licence:** OVMS's own code is MIT. The firmware binary also links mongoose (GPLv2/commercial), wolfSSL (GPLv2) and wolfSSH (GPLv3), so AGPL code can't ship inside it.
- **Verdict:**
  - **Don't** adopt it as our supervisor.
  - **Buy one kit** as a reference and interop test rig.
  - **Speak its MQTT topic layout** from our node.
  - **Copy its design ideas.**

## Generation 2 (legacy)

- **Repo:** [Open-Vehicle-Monitoring-System](https://github.com/openvehicles/Open-Vehicle-Monitoring-System). MIT, dormant since 2021.
- **Module:** a PIC18F2680 with a SIMCOM GSM modem.
- **Server:** [Open-Vehicle-Server](https://github.com/openvehicles/Open-Vehicle-Server), Perl, still active.
  - Ports: 6867/6870 for the v2 protocol (plain/TLS), 6868/6869 for HTTP(S).
  - Plugins: ApiV2, ApiHttp, Mqapi, Push (APNS/GCM/EXPO/mail) and others.
- **The v2 "MP" protocol:**
  - **Login:** `MP-C 0 <token> <digest> <vehicleid>`.
  - **Encryption:** HMAC-MD5 session key, then RC4 and base64 per line.
  - **"Paranoid" mode:** an end-to-end layer.
  - **Message codes:** S/D/L/F/V/T/W/Y/X/Z/P/C/A/G/H.
  - **Commands:** about 40 numeric ones.
  - **Topology:** apps and car both connect outbound to the server.
  - **Fit for us:** the messages are EV-shaped (SOC, charging), so an ICE D2 would map onto them poorly.
- **Apps:**
  - [Android](https://github.com/openvehicles/Open-Vehicle-Android) (MIT).
  - iOS "Open Vehicles" (v2).
  - "OVMS Connect" (iOS, third-party, pure MQTT/v3).

## Generation 3

[Repo](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3): 863★, 7.5k commits. Maintainer Michael Balzer; founder Mark Webb-Johnson.

### Hardware (v3.3)

| Area | Details |
|---|---|
| Processor | ESP32-WROVER, 16 MB flash, 4 MB PSRAM |
| CAN | CAN1 = ESP32 TWAI; CAN2/3 = MCP2515 (optional SWCAN board) |
| Connectors | DB9, with pin 1 = K-line on boards from July 2018 on; DA26 DIAG/expansion; internal header GEP1–7 (EXP1/2 = GPIO32/33); microSD; USB |
| Modem | SIM7600G 4G + GNSS |
| I/O expander | MAX7317, which drives modem power, the switched 12 V output (BTS452R, ~0.65–0.9 A) and CAN1 enable; 6 user ports |
| Deep-sleep draw | ~8–9 mA (100–250 mW); ~1 mA fully shut down |

**Prices** ([OpenEnergyMonitor shop](https://shop.openenergymonitor.com/ovms/)):

| Item | Price |
|---|---|
| 4G system | £235.19 |
| Wi-Fi-only system | £191.99 |
| [K-line board](https://docs.openvehicles.com/en/latest/userguide/kline.html) | £25.13 |

### Firmware components

ESP-IDF C++, under `vehicle/OVMS.V3/components/`:
- **CAN:** can, esp32can, mcp2515, swcan, canopen, dbc, retools, obd2ecu (OVMS acting as an OBD2 ECU, e.g. for a HUD).
- **Vehicle and polling:** poller, vehicle.
- **Connectivity:** ovms_cellular, simcom, ovms_location (geofences), ovms_server_v2/v3, ovms_webserver (mongoose), ovms_ota, ovms_plugins, pushover.
- **Scripting:** ovms_script (Duktape).
- **Power:** powermgmt, ext12v.
- **Consoles:** console_ssh, console_telnet.
- **Other:** ovms_tpms, sdcard.

### Metrics

[Docs](https://docs.openvehicles.com/en/latest/userguide/metrics.html). Typed, unit-aware and staleness-tracked; some survive a reboot.

| Prefix | Covers |
|---|---|
| `m.*` | Module |
| `s.*` | Server |
| `v.b.*` | Battery, including `v.b.12v.voltage` |
| `v.c.*` | Charge |
| `v.d.*` | Doors |
| `v.e.*` | Environment |
| `v.g.*` | Generator |
| `v.i.*` | Inverter |
| `v.m.*` | Motor |
| `v.p.*` | Position: latitude, longitude, speed, altitude, odometer |
| `v.t.*` | Tyres |
| `x<veh>.*` | Vehicle-specific |

### Poller

[API docs](https://docs.openvehicles.com/en/latest/components/poller/docs/API.html)
- **Poll list:** `poll_pid_t {txid, rxid, type, pid, polltime[state], pollbus, protocol}`.
  - Four vehicle states, each with its own poll interval.
  - `PollSetState(n)` switches state.
- **Transports:** ISO-TP (std/extadr/extframe) and VW TP2.0. **CAN only.**
- **Services:** UDS/OBD read/write, IO control, DTC read/clear, memory read.
- **Newer API:** `PollSeriesEntry`, one-shot series, throttling, tracing.

### Events

[Docs](https://docs.openvehicles.com/en/latest/userguide/events.html)
- **Vehicle:** `vehicle.on/off/awake/asleep/locked/unlocked`, `vehicle.gear.*`, `vehicle.charge.*`.
- **12 V:** `vehicle.alert.12v.on/off/shutdown`, `vehicle.aux.12v.*`.
- **Location:** `location.enter.<name>` / `location.leave.<name>`, `location.alert.flatbed.moved`.
- **Network and server:** `network.up/down`, `server.v3.connected`.
- **Timers:** `ticker.1/60/300/3600`.
- **System and power:** `system.start/shutdown`, `powermgmt.wifi.off`, `powermgmt.modem.off`, `powermgmt.ovms.shutdown`.
- **Notifications:** `notify.<type>.<subtype>`.
- **Scripts per event:** drop-in scripts in `/store/events/<event>/` run when that event fires.

### Scripting, web UI, OTA, notifications

- **Scripting** ([docs](https://docs.openvehicles.com/en/latest/userguide/scripting.html)):
  - Duktape JavaScript (ES5.1) with a 512 KB–1 MB heap; `ovmsmain.js` runs at boot.
  - Script objects: OvmsMetrics, Events, Command, Vehicle, Config, Location, Notify, PubSub, HTTP, VFS.
  - There is a plugin store.
- **Web UI:**
  - Built on mongoose, Bootstrap 3, jQuery and Highcharts.
  - Pages load by AJAX into `#main`; metrics arrive over a websocket.
  - Page and hook plugins can be installed from the UI.
- **OTA:** two 7 MB slots that validate before switching; firmware served from `api.openvehicles.com`. No signing seen.
- **Notifications:**
  - Types: info, alert, error, data, stream.
  - Dotted subtypes (`usr.*` for custom).
  - Channels (v2, v3, web, pushover) each filter by subtype.

### MQTT ("server v3")

**Prefix:** `ovms/<user>/<vehicleid>/`

| Topic | Purpose |
|---|---|
| `metric/v/b/soc` | One topic per metric (dots → slashes); retained, QoS 0 |
| `event` | Events |
| `notify/{info,alert,error}/<subtype>` | Notifications, QoS 1 |
| `notify/data/<subtype>/<id>/<age>` | Data notifications |
| `metric/s/v3/connected` | Last will (online/offline) |
| `client/<cid>/active` | Client announces itself |
| `client/<cid>/command/<id>` → `client/<cid>/response/<id>` | Commands and replies |
| `client/+/request/metric\|config` | Requests for metrics or config |

**Update rate per state:** `updatetime.connected`, `.idle`, `.on`, `.awake`, `.charging`, plus `.sendall` and `.keepalive`.

**Home Assistant:** no native discovery. The community [ovms-home-assistant](https://github.com/enoch85/ovms-home-assistant) integration (HACS) subscribes to these topics.

### Power management

- **Staged power-down (on by default):**

  | Step | Default delay |
  |---|---|
  | Wi-Fi off | 24 h |
  | Modem off | 96 h |
  | 12 V shutdown | 30 min |

  Each step raises an event.
- **12 V checks:**
  - Reference 12.6 V; alert at 1.6 V below it.
  - When the 12 V is low it shuts down, wakes every 60 s and re-checks.
- **No hardware wake sources:** it has no CAN-activity or motion wake.

## Vehicle modules

About 48 `vehicle_*` components. Almost all are EVs, plus generic OBD-II (CAN), DBC-driven, GPS-track-only, demo and none.

- **BMW:** i3
- **Chevrolet / Opel:** Bolt / Ampera-e; Volt / Ampera
- **BYD:** Atto 3
- **Cadillac / Chevrolet ICE:** CTS (2nd gen), CT5, C6 Corvette
- **Energica:** motorbikes
- **Fiat:** 500e, e-Doblò
- **Hyundai / Kia:** Ioniq 5 / EV6, Ioniq (pre-facelift), e-Niro / Kona / Ioniq FL, Soul EV
- **Jaguar:** I-Pace
- **Maple:** 60S
- **Maxus:** eDeliver 3, Euniq 5 / Euniq 6, T90 EV
- **Mercedes:** B250e
- **MG:** ZS EV / MG5
- **Mini:** Cooper SE
- **Mitsubishi / Citroën / Peugeot:** i-MiEV / C-Zero / iOn
- **Nissan:** Leaf / e-NV200
- **NIU:** GT EVO
- **Renault:** Twizy, Zoe phases 1 and 2
- **smart:** ED gen 3, EQ 453
- **Subaru:** Solterra
- **Tesla:** Model 3, Model S, Roadster
- **Think:** City
- **Toyota:** bZ4X, e-TNGA, RAV4 EV
- **VW group:** e-Golf, e-Up / Mii / Citigo
- **EV conversions:** ZEVA BMS, ZombieVerter VCU

**No K-line-era ICE vehicles.**

## Assessment for us

**1. OVMS as our always-on supervisor, with a D2 Td5 module?**

Technically possible:
- The TJA1027 K-line board puts DB9 pin 1 on UART2.
- Td5 runs at 10,400 baud on that UART.
- Fast init: switch TX to GPIO for 25 ms low / 25 ms high, then reattach the UART.
- It needs a custom OBD-pin-7 → DB9-pin-1 cable.

But the fit is poor:
- The poller has no K-line transport.
- GPIO32/33 are shared with the SWCAN board.
- The D2 has no CAN, which is OVMS's main strength.
- Cost is £235 per unit; enclosure is not waterproof.
- Classic ESP32, with no IMU and no Linux power control.
- Deep sleep is 100–250 mW, against our target of <10 mW.
- The GPL-2 libraries in the binary block AGPL code from shipping inside it.

**Decision: no.**

**2. Interoperate instead:**
- Our node publishes **the OVMS v3 MQTT topic layout** next to native HA discovery: retained metrics, `client/<cid>/command/<id>`, `event` and `notify/*`.
- That gets ovms-home-assistant and OVMS Connect working with us for free, and lets us read a real OVMS unit's topics unchanged.
- Implementing the v2 protocol is a stretch goal at most (weak crypto, EV-shaped messages).

**3. Design ideas to copy:**
- **Metric names:**
  - reuse the OVMS tree where it applies (`v.p.*`, `v.b.12v.voltage`, `v.e.*`, `v.t.*`);
  - `xd2.*` for Td5-specific values;
  - typed units and staleness tracking.
- **Per-state poll tables** (`polltime[state]`), as the model for vehicle-pack polls.
- **Dotted events**, with drop-in handlers.
- **Staged power-down** with an event at each step.
- **Notification type and subtype**, filtered per channel.
- **MQTT:** retained metrics with a last-will "connected" flag; update rate set per vehicle state.

**4. Licence:** MIT code may be copied into AGPL with its notice kept. Mongoose and wolfSSL/wolfSSH code must not be (GPL-2-only). Reimplementing the protocols and topic layout is fine. A separate OVMS box talking to us over MQTT is not a combined work.

**Action:** buy one OVMS v3.3 kit plus the K-line board (~£260) as a reference rig. It lets us test the MQTT interop and, optionally, prototype Td5 fast-init on its UART2.

## Sources

**Repos and shop**
- [OVMS3 repo](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3)
- [OEM shop](https://shop.openenergymonitor.com/ovms/)
- [ovmsdev list](https://lists.openvehicles.com/archives/list/ovmsdev@lists.openvehicles.com/)

**Docs**
- [Docs index](https://docs.openvehicles.com/en/latest/)
- [Protocol v2](https://docs.openvehicles.com/en/latest/protocol_v2/index.html)
- [Home Assistant](https://docs.openvehicles.com/en/latest/userguide/homeassistant.html)
- [EGPIO](https://docs.openvehicles.com/en/latest/userguide/egpio.html)
- [OTA](https://docs.openvehicles.com/en/latest/userguide/ota.html)
- [Notifications](https://docs.openvehicles.com/en/latest/userguide/notifications.html)

**Source files read:**
- `vehicle_teslaroadster.cpp`
- `powermgmt.cpp`
- `vehicle.cpp`
- `ovms_server_v3.cpp`
- `vehicle_poller.h`
- `components/mongoose/LICENSE`
