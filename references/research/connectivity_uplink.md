---
title: "Connectivity, uplinks and remote access — node and brain, parked broker, provisioning"
area: references
status: stable
version: 1.2
updated: 2026-10-06
depends_on: [references/research/ecosystem_architecture.md, references/research/hardware.md, references/research/t1s_module_bus.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md]
summary: >
  Live research (October 2026) behind ADR-0028, updated for ADR-0032/0033: one always-on ESP32 node (no separate buddy) with an optional Pi brain; the guardian is a hidden node hardware variant; 4G on the node is an official fitted option with a per-device IoT SIM, or a USB dongle by class (PPP/AT, ECM, RNDIS; one OTG port, so not on a USB-linked node; ADR-0039). Can the node host the parked MQTT broker? (Espressif's Mosquitto port: yes for a small TLS set, with caveats; Arduino brokers: no.) Uplinks: existing in-car Wi-Fi, phone hotspot, any USB 3G/4G dongle (HiLink/ECM/NCM/RNDIS or QMI/MBIM via ModemManager), Starlink Mini (12–48 V, 25–40 W, local gRPC status API), node or guardian-variant 4G; selection, priority failover with NetworkManager, data metering with vnstat. Remote access: LAN-only default, Tailscale (BSD-3, headscale, ESP32 MicroLink), an Ostler Cloud relay on the Nabu Casa end-to-end model, HA Cloud via Home Assistant; WireGuard/Nebula/ZeroTier licences. Wi-Fi AP+client on one radio, per-module web UIs, Improv Wi-Fi provisioning, and the drafted IANA `_ostler-mod._tcp` request (used unregistered in development, submitted at module contract v1).
---

# Connectivity, uplinks and remote access

Research for [ADR-0028](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md).
It extends the [ecosystem research](ecosystem_architecture.md) (ADR-0027) with the owner's
answers of 2026-10-06. Sources were checked live in **October 2026**. **(U)** means
unverified, so confirm it on the bench before relying on it.

> **Update (2026-10-06, ADR-0032/0033):** there is no separate "buddy": the ESP32
> **node** replaces it and also owns K-line/CAN I/O, decoding, the transmit gate and GPS
> (read "buddy" in older notes as the node; this note now says node). The Pi is the
> optional **brain** and never touches the car. The guardian is a **node hardware
> variant** (same firmware, hidden, backup battery, tamper, IMU, no outputs), not a
> separate add-on. 4G on the node is an **official option**, and each device may have its
> own IoT SIM; devices on the car LAN can share uplinks. Remote paths stay read-only
> unless the install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is set (ADR-0033). The
> IANA name is used unregistered during development and submitted at module contract v1.

**The owner's frame.** "We're making a Home Assistant for cars, not reinventing the wheel."
So every choice below prefers what ESP32 projects, home routers and Home Assistant already
do.

## 1. Node, brain and power states

| Part | Role | Always on? |
|---|---|---|
| **Brain (Pi)**, optional | Server, PWA, full local app, full MQTT broker, router, uplink manager; never touches the car | No: woken on demand by the node (default); optional "always-on" for EVs |
| **ESP32 node** (ESP32-S3 with PSRAM; replaces the "buddy") | The car side: K-line/CAN I/O, decoding to VSS, the transmit gate (the only path to the car), GPS; wake decisions and brain power, basic alarm inputs (doors, motion, 12 V), the parked MQTT broker (§2), the T1S PLCA coordinator, optional 4G | Yes (µA–mA budget) |
| **Guardian** (node hardware variant) | Same firmware, fitted hidden: own backup battery, tamper, IMU, better antennas, GPS, optional 4G; tracker and alarm triggers with escalation, survives a cut 12 V feed; **no outputs** | Yes, on its own cell |

- This changes the [hardware research](hardware.md) split, where the guardian owned
  wake and Pi power. The node is the always-on ESP32, so a car without a guardian variant
  still wakes, still sees doors and motion, and still has a broker while parked; with no
  brain (Ostler Diagnostics alone) the node is the whole system.
- **Power states.** *Asleep* (Pi cut, node on); *woken* (ignition, an alarm input, a
  schedule, a button, or a remote request arriving through any uplink the node or guardian
  holds); *awake/driving* (Pi on); *always-on* (an owner setting meant for EVs, whose DC-DC
  keeps the 12 V battery up; the node still cuts the Pi if 12 V falls below a floor).
  A halted Pi 5 still draws about 50 mA unless fully cut ([hardware.md](hardware.md)).
  These words now map to the power states of
  [ADR-0040](../../decisions/adr-0040-power-states-and-wake.md) §1 (off, asleep, waking,
  awake, held), with the node's parked-ready and parked-deep modes.

## 2. MQTT broker on the always-on ESP32: feasibility

### 2.1 Candidates

| Broker | Protocol | TLS | Retained / will | Clients | Verdict |
|---|---|---|---|---|---|
| **Espressif `espressif/mosquitto`** (ESP-IDF component, Mosquitto 2.0.20 core, v2.0.20~9 on the registry, Oct 2026) | Mosquitto core, so MQTT 3.1.1 and 5 expected (U: not stated in the port's docs) | Yes, one listener: TCP **or** TLS via ESP-TLS | In-memory only; no persistence file documented (U) | Tested with 5 at once; heap ≈ 2 kB at start plus ≈ 4 kB per plain client | **Use it** for the parked set |
| **PicoMQTT** (Arduino) | 3.1.1 | No | Broker ignores retained and will; QoS 0 | Not stated | Reject |
| **sMQTTBroker** (Arduino) | 3.1.1, QoS 0 | No | Not documented | Not stated | Reject |
| **TinyMqtt** (Arduino) | 3.1.1, QoS 0 | Only via a modified fork | Not documented | Not stated | Reject |
| **EmbeddedMqttBroker** (Arduino) | 3.1.1 | No (U) | No (U) | Not stated | Reject |

Sources: Espressif's port announcement (2025-05-28) gives about 60 kB of flash, at least 5 kB
of stack, about 2 kB of heap at start and about 4 kB per client, TLS through ESP-TLS, a single
listener, and a bridged-brokers example between two ESP32s
([Espressif blog](https://developer.espressif.com/blog/2025/05/esp-idf-mosquitto-port/),
[component registry](https://components.espressif.com/components/espressif/mosquitto),
[esp-protocols](https://github.com/espressif/esp-protocols/tree/master/components/mosquitto)).
The port is configured by a struct passed to `mosq_broker_run()`, not a config file, so
Mosquitto's password file, ACL file and plugins are not there yet (U).
PicoMQTT, sMQTTBroker and TinyMqtt are all MQTT 3.1.1 with QoS 0
([CNX, 2023-04](https://www.cnx-software.com/2023/04/18/picomqtt-an-mqtt-client-broker-library-for-esp8266-and-esp32/),
[Hackster comparison](https://www.hackster.io/highvoltages/esp32-as-an-mqtt-broker-a-comparison-of-two-libraries-6dedf3),
[sMQTTBroker](https://www.arduinolibraries.info/libraries/s-mqtt-broker)).

### 2.2 TLS cost on the ESP32-S3

- mbedTLS on an ESP32-S3 uses about **37 kB of heap** for one server-authenticated HTTPS
  client with default buffers (16 kB in, 4 kB out); a handshake alone needs about 25–30 kB
  ([ESP-TLS docs](https://docs.espressif.com/projects/esp-idf/zh_CN/v5.1/esp32s3/api-reference/protocols/esp_tls.html)).
- **Five mTLS clients ≈ 150–200 kB of heap** at the peaks (U). That fits only with PSRAM
  (mbedTLS can allocate there) and dynamic buffers. So **the node must be an ESP32-S3 with
  PSRAM** (U: confirm the module).
- TLS adds about 14% latency and 31% packet size on ESP32 MQTT in one 2025 study
  ([JAIC](https://jurnal.polibatam.ac.id/index.php/JAIC/article/view/13355)): fine for a
  parked set.

### 2.3 Verdict: a two-broker design

- **The node runs the Espressif Mosquitto port for the parked minimal set**: alarm events,
  `status` (LWT), wake requests, the guardian and the few wake-capable nodes, the node's own
  signals. TLS listener only; at most about 5 clients (U: bench it).
- **The Pi runs full Mosquitto** (OS package) for everything once awake: telemetry,
  cameras' metadata, HA discovery, bridges out.
- **Bridging.** When the Pi wakes, *its* Mosquitto opens a bridge to the node (`connection`,
  `topic … both` on the parked topic patterns only, `remote_clientid`, TLS options) so the
  full broker sees parked events and history, and parked nodes see commands that the server
  gate approved
  ([Mosquitto bridge docs](https://docs.cedalo.com/mosquitto/2.8/broker/Mosquitto%20Manual/Bridges/mosquitto-mqtt-bridge)).
  The Pi is the bridge client, because the ESP32 port has no bridge configuration surface (U).
- **Retained state does not survive a node reboot** (U). Parked nodes republish their
  manifest and status on reconnect; the Pi treats the node broker as a relay, not a store.
- **Auth and ACLs.** Mosquitto-on-Pi: mTLS plus `acl_file` per device. The node: mTLS with
  client certificates from the local CA and a fixed, compiled-in topic allow-list per role,
  until the port gains ACL hooks (U).
- **EV always-on.** The Pi broker is the only broker that matters; the node broker stays up
  but idle, bridged.
- **Fallback, in order** if the bench fails (no MQTT 5, heap, stability):
  1. **No parked broker.** Parked nodes signal the node over the wake wire or CAN
     (ADR-0026); the node wakes the Pi and republishes the event on the Pi's broker.
  2. **The guardian hosts the parked broker** when fitted (same port, bigger power budget).
  3. **Pi always-on** for owners who accept the drain.

## 3. Uplinks: sources, selection, failover and metering

### 3.1 Sources

| Source | How it reaches Ostler | Metered by default | Notes |
|---|---|---|---|
| **Head-unit Wi-Fi / car Wi-Fi hotspot** | Pi Wi-Fi as a client | Unknown → ask | Many modern head units and OEM telematics boxes offer a hotspot |
| **Phone hotspot** | Pi Wi-Fi client, or USB tethering (NCM/RNDIS) | Yes | Phones mark it metered themselves |
| **Home Wi-Fi when parked** | Pi (or node) Wi-Fi client | No | The cheapest bulk path: uploads, OTA, logbook sync |
| **USB 3G/4G/5G dongle on the Pi** | HiLink-style: the stick is its own router and shows as an Ethernet NIC (`cdc_ether`/`rndis_host`/NCM) with DHCP. Or modem mode: QMI (`qmi_wwan`) / MBIM (`cdc_mbim`) driven by ModemManager | Yes | HiLink "just works" (double NAT, little control); QMI/MBIM gives signal, SIM and SMS. PPP is the slow legacy path ([FOSDEM 2014](https://archive.fosdem.org/2014/schedule/event/deviot10/), [Netgate forum](https://forum.netgate.com/topic/129994/qmi-mbim-ncm-rndis-protocols)) |
| **4G on the node** (official fitted option) | A per-device IoT SIM in a Cat-1 modem (e.g. SIM7670-class, as on the guardian variant), fitted on the Diagnostics board (ADR-0039 §5) | Yes | Always on; uses no USB port |
| **USB 4G dongle on the node** | ESP32-S3 USB host, by class: PPP and AT over CDC-ACM (`iot_usbh_modem`, Cat-1/Cat-4, NAPT to share the link), ECM (`iot_usbh_ecm`) or RNDIS (`iot_usbh_rndis`); QMI/MBIM sticks only on the Pi. A tested-dongle list lives in the firmware repo ([product family §5](product_family.md#5-standalone-uplink)) | Yes | Listed modules include A7670E and EC20; slow (USB full speed) but always on ([Espressif](https://components.espressif.com/components/espressif/iot_usbh_modem)). **One OTG port:** a node linked to the hub by USB-NCM is a USB device and cannot host a dongle at the same time (ADR-0039 §4) |
| **Guardian-variant 4G** | The guardian variant's SIM7670G Cat-1, its own IoT SIM | Yes | Alarm-grade: own battery, works with 12 V cut |
| **High-speed gateway** (option) | An OpenWrt 4G/5G router as an Ethernet WAN; it can run **mwan3** itself (up to 250 WANs, failover and balancing) ([OpenWrt](https://openwrt.org/docs/guide-user/network/wan/multiwan/mwan3)) | Per its SIM | For vans and overlanders; the Pi sees one Ethernet uplink |
| **Starlink Mini** (integration) | Ethernet or Wi-Fi WAN; status from its local gRPC API | No (but power-hungry) | See §3.4 |

### 3.2 Selection and failover on the Pi

- **NetworkManager + ModemManager** (Pi OS default) cover it: a profile per source with
  `ipv4/ipv6.route-metric` (lower wins), `connection.autoconnect-priority`, and
  `connection.metered` (yes / no / unknown, guessed when unknown); NM replaces the default
  route when the preferred link drops and can test reachability with a connectivity-check
  URI ([nm-settings](https://manpages.debian.org/bullseye/network-manager/nm-settings-nmcli.5.en.html),
  [Digi failover guide](https://www.digi.com/resources/documentation/digidocs/embedded/dey/4.0/cc6ul/yocto-network-failover_r)).
- **Ostler's policy layer** is a thin owner-facing list on top: **Auto** (priority order
  with failover) or a **pinned** source; per-source metered flag; per-source budget. It writes
  NM profiles; it does not route packets itself. Connectivity checks point at a
  self-hosted or owner-chosen URL, never a tracking endpoint, and are off unless an uplink is
  enabled.
- **systemd-networkd** is the alternative for the internal segments (ADR-0027); two managers
  on one host must not both claim an interface (U: the router-config spec picks one).
- **mwan3** needs OpenWrt; it belongs in the optional high-speed gateway, not on the Pi.

### 3.3 Metering and data caps

- **vnStat** keeps 5-minute, hourly, daily and monthly totals per interface and has
  `--alert` to test a monthly (or daily) limit, with an exit code for scripts
  ([vnstat man page](https://humdi.net/vnstat/man/vnstat.html)).
- Ostler reads the totals per uplink, compares them with the owner's budget and billing day,
  and publishes `Vehicle.Ostler.Connectivity.*` signals (U: names in the overlay).
- **Alerts at 50/80/100%**, and at 100% on a metered source: stop bulk traffic (logbook
  upload, OTA, camera clips, map tiles), keep alarm notifications and remote status. The owner
  can override.
- On the node and guardian, count bytes from `esp_netif`/the modem driver and report them
  when the Pi wakes (U).

### 3.4 Starlink

- **Starlink Mini:** DC input 12–48 V, about 25–40 W average, about 15 W idle, start-up peaks
  near 60 W; on a car's 12 V many installers boost to about 18+ V for reliability
  ([Outcamp guide](https://outcamp.com.au/blogs/news/guide-to-powering-starlink-mini-from-your-vehicle-using-a-12-volt-power-supply),
  [Bluetti](https://www.bluettipower.com/blogs/knowledge/starlink-mini-power-consumption)) (U).
  It cannot stay on while parked off the starter battery.
- **Local status API:** the dish serves unauthenticated gRPC at `192.168.100.1:9200`
  (state, obstruction, latency, throughput, power) with no cloud account
  ([starlink-grpc-tools](https://github.com/sparky8512/starlink-grpc-tools)); Home Assistant
  has a core Starlink integration on the same API
  ([HA](https://www.home-assistant.io/integrations/starlink/)).
- **Integration:** a DevicePack adapter reads the status into VSS-named signals; its power
  feed is a relay-box channel (Tier 2, Parked-only rules apply to switching it, ADR-0018);
  the dish's location sharing stays off unless the owner enables it.

### 3.5 Where cellular lives: trade-off

| Placement | Speed | Works with Pi off | Works with 12 V cut | Cost | Use |
|---|---|---|---|---|---|
| **Pi + USB dongle** | High (Cat-4+, 5G) | No | No | Dongle + SIM | Driving, bulk sync |
| **Node + 4G** (fitted option, or a USB dongle on a node not linked by USB) | Low (Cat-1/PPP) | Yes | No | Option + IoT SIM | Ostler Diagnostics alone, alarm notifications, remote wake |
| **Guardian variant + 4G** | Low (Cat-1) | Yes | Yes | Variant + IoT SIM | Alarm-grade, tracker |
| **Phone/head-unit Wi-Fi** | Medium–high | No | No | None | Default "no SIM" setup |

## 4. Remote access

| Tier | What | Licence / terms | Verdict |
|---|---|---|---|
| **0. LAN only** | The UI on the in-car network | — | **Default** |
| **1. Tailscale** | `tailscaled` on the Pi; the owner's tailnet (Personal plan: six users, unlimited user devices since 2026-04-08) or **headscale** (BSD-3, v0.29.1, June 2026) | Client BSD-3-Clause (`tailscaled`, CLI, `tsnet`); macOS/iOS/Windows GUI wrappers closed | **Supported, opt-in** |
| **2. Ostler Cloud** | Our hosted relay and account portal | Closed service, documented protocol | **Product, never the only path** |
| **3. HA Cloud** | Nabu Casa remote UI reaches HA, which sees the car over MQTT | Nabu Casa subscription | **Compatible through HA** |

Sources: [tailscale/tailscale](https://github.com/tailscale/tailscale),
[tsnet](https://pkg.go.dev/tailscale.com/tsnet@v1.44.3),
[headscale](https://wz-it.com/en/knowledge/remote-access/what-is-headscale/),
[Tailscale free plan](https://costbench.com/software/business-vpn/tailscale/free-plan).

- **Tailscale.** "Add support, or leave it to people" meets in the middle: the deploy tool
  installs the distro package on opt-in, the UI shows tailnet status, and the web server
  binds to the tailnet interface with the same auth. `tsnet` embedding is possible under
  BSD-3 but adds Go to the stack against ADR-0002; the OS package is enough.
  **Funnel** publishes a service to the public internet (ports 443/8443/10000, TLS only,
  unpublished bandwidth limits) and is **not** recommended for a car
  ([Funnel docs](https://tailscale.com/kb/1223/tailscale-funnel)).
- **Tailscale on ESP32.** **MicroLink** (MIT) is a Tailscale-protocol stack for ESP32
  (ts2021 control, WireGuard data plane, DERP, STUN, Wi-Fi + 4G failover); about 85–123 kB
  of static SRAM, PSRAM recommended
  ([MicroLink](https://github.com/CamM2325/microlink),
  [registry fork](https://components.espressif.com/components/fugo101/microlink/versions/3.2.0/readme));
  an **esphome-tailscale** component also exists
  ([GitHub](https://github.com/Csontikka/esphome-tailscale)). Third-party and young:
  **REFERENCE** for the node and its variants, not in the default build.
- **Alternatives.** Plain **WireGuard** (kernel GPL-2.0, in every Linux): the base of an
  Ostler Cloud relay. **Nebula** (MIT, needs your own lighthouse): reference. **ZeroTier**
  (BSL until v1.16; since August 2025 core MPL-2.0, controller source-available): avoid as a
  default ([ZeroTier changelog](https://docs.zerotier.com/changelog/2025/08/21/zt1-v1.16.0),
  [Nebula](https://metadata.ftp-master.debian.org/changelogs/main/n/nebula/stable_copyright)).
- **Ostler Cloud, modelled on HA Cloud.** Nabu Casa's remote UI gives each instance a
  unique hostname; the cloud's **SniTun** proxy routes by TLS SNI over a multiplexed
  outbound tunnel, so TLS ends on the instance and the relay never sees plaintext
  ([Nabu Casa support](https://support.nabucasa.com/hc/en-us/articles/26510075061021)).
  Ostler Cloud does the same for the Pi's UI (outbound tunnel, end-to-end TLS with the
  device's own certificate), plus an **MQTT bridge** from the Pi's Mosquitto to a cloud
  broker for opt-in state and notifications while the Pi sleeps (the node or guardian
  bridges a minimal set). A per-car WireGuard tunnel is the alternative transport. Account
  portal: add a car, see status, manage uplinks and budgets.
- **HA Cloud.** Ostler already publishes HA discovery (ADR-0027); whoever runs HA with Nabu
  Casa gets remote access to the car's entities through HA, read-only by default (the
  ADR-0033 remote rule applies).

## 5. Wi-Fi, per-module web UIs and provisioning

- **AP + client on one radio.** The Pi's Broadcom chip lists `#{managed} ≤ 1, #{AP} ≤ 1,
  #channels ≤ 1`: both work at once but **on one channel**, the client's
  ([RaspAP AP-STA](https://docs.raspap.com/features-experimental/ap-sta/)); some driver
  versions drop the client when the AP starts (U: bench). The ESP32 is the same: in APSTA the
  soft-AP follows the station's channel, briefly dropping its clients
  ([esp32.com](https://esp32.com/viewtopic.php?p=8462)). Accept it; a USB Wi-Fi adapter is the
  escape hatch.
- **Every module has its own small web page** (status, basic controls, network, pairing,
  OTA) like IP cameras and ESP32 relay boards, and works standalone. Its controls obey the
  same tiers and categories; anything above Tier 1 on a module's page needs the owner's
  credentials and the module's own interlocks (U5).
- **Provisioning standard: Improv Wi-Fi** (an Open Home Foundation open standard over BLE and
  serial; HA and ESPHome use it; a browser button over Web Bluetooth or Web Serial)
  ([Improv](https://www.improv-wifi.com/), [ESPHome](https://esphome.io/components/improv_serial.html)),
  **with a SoftAP captive-portal fallback** for browsers without Web Bluetooth (iOS Safari).
  ESP-IDF unified provisioning (SoftAP/BLE, about 110 kB for BLE) needs Espressif's apps, and
  WiFiManager is Arduino-only: **REFERENCE**
  ([ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32/api-reference/provisioning/provisioning.html)).
  Wired T1S modules skip Wi-Fi provisioning and pair as in ADR-0027 §1.7.

## 6. Draft IANA service-name registration (the owner submits)

During development `_ostler-mod._tcp` is used **unregistered**; the owner submits this
drafted request when the module contract reaches v1. Through IANA's
[service name and port form](https://www.iana.org/form/ports-services)
(RFC 6335; "service name only", no port). Approval takes 1–2 months.

| Field | Draft |
|---|---|
| Assignee / contact | Project maintainer, OpenOstler (name and e-mail filled in at submission) |
| Resources required | Service name only |
| Transport | TCP |
| Service name | `ostler-mod` (10 characters; limit 15) |
| Description | Ostler vehicle add-on module: announces an in-vehicle device that joins an Ostler node or brain over IP (automotive Ethernet or Wi-Fi) for pairing and MQTT messaging |
| Reference | A public spec URL in the platform repo (the module-bus message spec, once published) |
| Defined TXT keys | `cv` contract version (integer); `md` model; `fw` firmware version; `pr` paired (0/1); `mf` manifest topic. Final names in the module-bus spec |
| Broadcast / multicast | No; discovery uses mDNS (RFC 6762) only |
| Versioning | `cv` TXT key; the MQTT topic tree carries `v1` |
| Security | Pairing confirmed physically by the owner; mTLS with per-device certificates from the vehicle's local CA; MQTT 5 authentication and ACLs; no default passwords |
| Status | Under development (used unregistered until contract v1); open-source reference implementation |

## 7. Open points

1. Bench the node broker: MQTT 5, five mTLS clients on PSRAM, 24 h stability, bridge
   behaviour on Pi wake and sleep (ADR-0028 Confirmation).
2. ~~Whether the buddy is the PLCA coordinator.~~ The node is the PLCA coordinator
   (ADR-0032); open: which device coordinates when a guardian variant sits alongside it.
3. Passkeys are bound to a hostname (WebAuthn RP ID): `.local`, the tailnet name and an
   Ostler Cloud name each need their own registration, or a related-origins setup (U).
4. Which manager owns which interface on the Pi (NetworkManager against systemd-networkd).
