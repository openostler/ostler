---
title: "Ecosystem architecture — IP everywhere, standard discovery and a module contract"
area: references
status: stable
version: 1.1
updated: 2026-10-06
depends_on: [references/research/connectivity_uplink.md, references/research/t1s_module_bus.md, references/research/hardware.md, references/research/standards.md, references/research/platform.md, references/research/canbus_headunit.md, decisions/adr-0026-module-bus-10base-t1s.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Live research (October 2026) behind ADR-0027: Ostler as a smart-home-like automotive ecosystem with IP on every device. Network segments (10BASE-T1S for modules, standard Ethernet or PoE cameras now and 100BASE-T1 only for our own camera hardware, Wi-Fi/USB for displays) with live part and product prices; the Pi as router; dual-stack addressing; NTP from GNSS, PTP later; zero-config with mDNS/DNS-SD. A verdict per standard: MQTT 5 with HA discovery and a VSS topic tree, Matter (reach it through a bridge, never inside modules; costs), VISS/KUKSA, SOME/IP and DDS, LwM2M, SUIT/MCUboot, mTLS and MACsec. Product taxonomy (base pack = Pi plus an always-on ESP32 buddy; the guardian and others are add-ons), the module contract, and comparisons with smart-home ecosystems and zonal E/E architectures. Uplinks, the parked broker, remote access and provisioning moved to the connectivity research (ADR-0028).
---

# Ecosystem architecture

Research for [ADR-0027](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md),
which builds on [ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md) (the module
bus). It broadens the module bus into one network for the whole ecosystem. Uplinks, the
parked broker, remote access and provisioning are in the
[connectivity research](connectivity_uplink.md) (ADR-0028, owner answers of 2026-10-06). Prices were checked
live in **October 2026**, are per unit and exclude VAT unless stated. **(U)** means unverified,
so confirm it before relying on it.

**The idea (owner, 2026-10-06).** Ostler works like a smart home, but for a car. A **base
hardware pack** interfaces with the car you already have. Its diagnostics and telemetry
make the car's existing systems connected. **Add-on modules** (alarm/guardian, cameras,
relay boxes, sensors, displays) then join over **standard networking**. Three limits
apply:
- "Standard networking everywhere" covers **our** ecosystem. The car's own buses (K-line,
  CAN, I/K-Bus) are interfaced at the edge by the base pack and are never replaced
  (ADR-0020, ADR-0022, ADR-0024).
- Cameras cannot share a T1S segment, which carries 10 Mbit/s shared between all nodes.
- Low-power wake over T1S is unproven, so CAN or a wake wire stays as the fallback (ADR-0026).

## 1. Network architecture

### 1.1 Segments: one IP network, several physical layers

| Segment | Physical layer | Who is on it | Why |
|---|---|---|---|
| **Module segment** | 10BASE-T1S, PLCA, multidrop (ADR-0026) | guardian, relay box, sensor/button nodes, HEVAC controller, gauges | one pair for up to 8+ nodes on 25 m; about $5 per node; bounded access latency ([T1S research](t1s_module_bus.md)) |
| **Camera segment** | standard Ethernet now (100BASE-TX/GbE, 12 V or PoE); 100BASE-T1 only for our own cameras later | IP cameras | one 5 MP H.265 stream is several Mbit/s (U), so a single camera would consume most of a 10 Mbit/s T1S segment |
| **Client segment** | Wi-Fi access point on the Pi; USB tethering (NCM/RNDIS) | head unit, phones, tablets, laptops | displays are thin clients of the PWA ([direction spec](../../specs/2026-10-06-platform-direction-design.md)) |
| **Uplinks** | existing in-car Wi-Fi, phone hotspot, home Wi-Fi, any USB 3G/4G dongle; Starlink, a high-speed gateway, guardian LTE as options ([connectivity §3](connectivity_uplink.md#3-uplinks-sources-selection-failover-and-metering)) | cloud (opt-in), Home Assistant | the base has no SIM; outbound is opt-in and off by default |
| **Fallback / dev kit** | CAN (module mapping per ADR-0026), Wi-Fi for convenience modules | µA-wake nodes, dev boards | ADR-0026; never Wi-Fi for alarm-critical links |
| **Car buses (edge only)** | K-line, vehicle CAN, I/K-Bus, OBD-II | the car's ECUs | spoken by the base pack's front ends under ADR-0020/0022/0024; never bridged to our network |

### 1.2 Cameras: 100BASE-T1 against standard Ethernet or PoE (live prices)

| Item | Price | Source |
|---|---|---|
| TI **DP83TC812** 100BASE-T1 PHY (TC10 sleep) | $2.44 (1), $1.60 (100), $1.44 (1k); 792 in stock | [LCSC](https://www.lcsc.com/product-detail/C3225810.html) |
| NXP **TJA1103** 100BASE-T1 PHY | $2.82 (1), $1.73 (100); **0 in stock, next 2027-07-05**, 39-week lead | [DigiKey](https://www.digikey.com/en/products/result?keywords=TJA1103BHN) |
| Microchip **LAN8770** 100BASE-T1 PHY | $3.75 (1), $3.23 (750) | [Future](https://futureelectronics.com/p/semiconductors--comm-products--switch/lan8770r-i-5kx-microchip-5178200) |
| Microchip **LAN9370** switch (4 × 100BASE-T1 + 1 MAC) | $8.96 (1), $7.21 (100); 1,123 in stock, 23-week lead | [DigiKey](https://www.digikey.com/en/products/detail/microchip-technology/LAN9370-I-KCX/16915502) |
| NXP **SJA1110** TSN switch | $33.18 (10+), $22.12 (1k+); others $11.85 at 1k (U) | [Dasenic](https://dasenic.com/product/nxp-usa-inc-sja1110del0y-8117298) |
| 100BASE-T1 ↔ 100BASE-TX media converter | $260–325 each (innomaker $288.99; Mach Systems €260) | [Newegg](https://www.newegg.com/p/0XP-06K4-00345), [Mach Systems](https://shop.machsystems.cz/product/100base-t1-media-converter/) |
| Retail 100BASE-T1 camera | **none found at hobby prices**; automotive camera modules are OEM/Tier-1 parts | search, Oct 2026 |
| **Reolink RLC-510A** PoE IP camera (5 MP, RTSP, NTP, microSD, 802.3af **or 12 V DC**, IPv4) | ≈ £47 | [Reolink](https://reolink.com/gb/product/rlc-510a/), [PriceRunner](https://www.pricerunner.com/pl/589-3200231522/Surveillance-Cameras/Reolink-RLC-510A-Compare-Prices) |
| TP-Link **LS1005G** 5-port GbE switch, 5 V 0.6 A, 3.7 W | £8–18 | [RS](https://uk.rs-online.com/web/p/network-switches/2753530), [Inside Tech](https://inside-tech.co.uk/networking/tp-link-litewave-ls1005g-5-port-10-100-1000mbps-gigabit-desktop-network-switch/) |
| 12 V-input PoE switch, 4–5 ports (built-in boost) | $140–163 (LINOVISION); from $42.80 (U) | [Newegg](https://www.newegg.com/p/pl?d=12v+input+poe+switch), [Newegg Business](https://www.neweggbusiness.com/p/9B-0XP-06WS-00275) |

**Network cost per camera node** (camera excluded):

| Path | Per camera | Notes |
|---|---|---|
| **A. Ethernet + 12 V on separate wires** (camera fed from a fused, regulated 12 V) | **≈ £3–5** (a quarter of a £13 switch plus a buck converter) | cheapest; no 48 V in the car; needs a camera that takes 12 V DC |
| **B. PoE (802.3af)** from a 12 V-input PoE switch | **≈ $35–40 a port** | one cable per camera; boost converter losses while parked |
| **C. 100BASE-T1, off the shelf** | **≈ $260–325** (a media converter per link) | no retail T1 cameras, so it means a converter at each camera |
| **D. 100BASE-T1, our own hardware** | **≈ $4–5 of silicon** (one PHY plus a quarter of a LAN9370) | needs our own camera board (image sensor, ISP, MAC), EMC work and automotive connectors: a hardware project |

**Recommendation.**
- Use **standard Ethernet cameras now**: path A by default, path B where a camera only
  takes PoE.
- **100BASE-T1 only arrives with our own camera hardware** (path D), with a LAN937x-class
  switch on the Pi side.
- Because everything is IP, changing the physical layer changes no software.
- SD-card IP cameras also solve the "pre-event buffer while parked" constraint in the
  direction spec.
- Use automotive-grade connectors (for example M12) in the camera harness (U).

### 1.3 The Pi as router and gateway

- **The Pi routes between segments; it does not bridge them.** Each segment is its own
  subnet and IPv6 /64.
- Reasons for routing:
  - camera multicast and broadcast (ONVIF WS-Discovery, ARP storms) never reach the 10 Mbit/s
    T1S segment;
  - a firewall between segments: cameras and clients cannot open connections to modules, and
    modules talk only to the broker and the Pi's services;
  - one place to apply QoS.
- **Interfaces on a Pi 5:**
  - T1S through a LAN8651 on SPI ([T1S research §5](t1s_module_bus.md));
  - cameras on the on-board GbE port to a small switch;
  - clients on the on-board Wi-Fi in AP mode, or USB gadget/tethering;
  - a second Ethernet port if needed, e.g. an RTL8153 USB adapter at about $10–16
    ([ZimaSpace](https://shop.zimaspace.com/products/usb-3-0-type-a-to-rj45-ethernet-adapter)).
- All of this is OS configuration (systemd-networkd, nftables, an mDNS proxy), **not Python
  dependencies**, so ADR-0002 is untouched.
- **The car's buses stay behind the vehicle-interface front ends.** Nothing on any IP segment
  can address a car ECU except through the platform's server gate (ADR-0020: no MQTT → vehicle CAN).

### 1.4 Addressing

- **IPv6 link-local** works with zero configuration on every segment.
- The Pi announces a **ULA prefix per vehicle** (RFC 4193, random 40-bit global ID), one /64
  per segment, by router advertisement. Nodes use SLAAC.
- Matter, mDNS and newer stacks all prefer IPv6.
- **IPv4 with DHCP from the Pi on every segment as well (dual stack).** Cheap cameras are
  IPv4-first; the RLC-510A lists IPv4 only
  ([Reolink](https://reolink.com/gb/product/rlc-510a/)). ESP-IDF's lwIP does both.
- Use a per-vehicle random RFC 1918 block, so it does not collide with a home LAN when the Pi
  joins home Wi-Fi.
- **Names, not addresses.** Everything is found by mDNS name (`<device>.local`). Nothing
  hard-codes an address.
- **PLCA node IDs are not zero-config.** Classic PLCA needs a unique ID set before a node joins.
  Dynamic PLCA is in IEEE 802.3da, but its silicon is not on the market (U)
  ([802.3da D-PLCA baseline](https://www.ieee802.org/3/da/public/0321/beruto_3da_01_031721_dplca_baseline.pdf)).
  The PLCA FAQ allows "assignment by the means of a higher-level protocol running on top of
  plain CSMA/CD"
  ([IEEE PLCA FAQ](https://www.ieee802.org/3/cg/public/July2018/PLCA%20FAQ.pdf)).
- **So:** a new module joins in CSMA/CD mode. At pairing, the coordinator assigns it a node ID,
  which it stores, and it then switches to PLCA. The bench plan should check how one CSMA/CD
  node behaves on a PLCA segment (U).

### 1.5 Time sync

- **NTP (chrony) on the Pi, disciplined by the u-blox GNSS and its PPS**, serving every segment.
  ESP32 SNTP and IP cameras (the RLC-510A lists NTP) need nothing more.
  Millisecond-level time is enough for logs, events and clip alignment.
- **PTP / gPTP (IEEE 802.1AS): ADOPT-LATER.**
  - The LAN865x timestamps on the MDI to work around PLCA's variable delay.
  - But 802.1AS "clearly defines" only full-duplex links, and multidrop T1S "requires software
    workarounds… until the standards are adapted"
    ([Microchip LAN865x PTP note](https://onlinedocs.microchip.com/oxy/GUID-7A87AF7C-8456-416F-A89B-41F172C54117-en-US-10/GUID-83EB345A-B543-4669-9CB5-9B4FB597FF94.html),
    [WSTS 2025](https://wsts.atis.org/wp-content/uploads/2025/04/WSTS2025_802.1AS-Time-Synchronization-Over-Half-Duplex-Ethernet-Links_AlonRegev_FINAL.pdf)).
  - Adopt it only when a feature needs sub-millisecond alignment, such as sensor fusion or a
    360° stitch.

### 1.6 QoS and TSN (brief)

- PLCA already bounds access on the module segment (≈ 2.5 ms worst case at 3 nodes,
  [T1S research §2](t1s_module_bus.md)), and routing keeps video off it.
- On the Pi, mark alarm and command traffic with DSCP (EF/CS5) and shape uplinks with
  `tc` (U: values set in the module-bus spec).
- MQTT QoS 1 for commands and alarm events, QoS 0 for telemetry.
- **TSN** (802.1Qbv and similar): **REFERENCE-ONLY**. It is what OEM switches such as the
  SJA1110 provide ([NXP](https://www.nxp.com/company/about-nxp/newsroom/NW-AUTOMOTIVE-ETHERNET-SWITCH)).
  We have no hard-real-time control loops.

### 1.7 Zero-config: what "plug in a module" means

1. **Link.** The node gets an IPv6 link-local address, a DHCPv4 lease and a SLAAC address
   (on T1S it first joins in CSMA/CD mode, §1.4).
2. **Announce.** The node advertises `_ostler-mod._tcp` by mDNS/DNS-SD. The TXT record holds
   the contract version, the model, the firmware version and whether the node is paired.
   The Pi advertises `_mqtt._tcp` / `_secure-mqtt._tcp` (IANA names, ports 1883/8883).
   - mDNS is RFC 6762 and DNS-SD is RFC 6763 ([RFC 6763](https://www.rfc-editor.org/rfc/rfc6763)).
   - Across routed segments the Pi runs an **RFC 8766 discovery proxy** (or an avahi
     reflector on dev kits) ([RFC 8766](https://www.rfc-editor.org/rfc/rfc8766.html)).
   - Our service name is to be registered with IANA; the draft request is in
     [connectivity §6](connectivity_uplink.md#6-draft-iana-service-name-registration-the-owner-submits).
3. **Pair.** The owner confirms the pairing on the Pi: a button press on the module within a
   window, or a QR/setup code (the Matter pattern). The Pi issues a per-node certificate and
   broker credentials, and assigns the PLCA ID. Nothing has a default password (UK PSTI).
4. **Describe.** The node publishes its **module manifest** (§3.2), retained. The platform adds
   it to `capabilities.devices` (UI spec §6) and generates Home Assistant discovery from it.
5. **Run.** Telemetry flows on VSS-named topics, and commands go only through the server gate.
   Last-will messages mark the node offline.

## 2. Standards for discovery and interop: verdicts

| Standard | Verdict | Use |
|---|---|---|
| **mDNS / DNS-SD** (RFC 6762/6763, RFC 8766 proxy) | **ADOPT** | Zero-config discovery of modules, the broker, the Pi's web UI and cameras; the same mechanism that Matter and HA use |
| **MQTT 5** (OASIS) | **ADOPT** inside the car; 3.1.1 stays acceptable at the HA edge | **The in-car message bus.** We need v5 features: response topic and correlation data for commands, message expiry (stale data looks stale), user properties (confidence), reason codes. ESP-MQTT supports v5 and mutual TLS ([ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/api-reference/protocols/mqtt.html)). The broker is Mosquitto on the Pi while awake (an OS package and a separate process, so ADR-0002 holds); Espressif's ESP-IDF Mosquitto port on the always-on buddy hosts a parked minimal set, bridged by the Pi ([connectivity §2](connectivity_uplink.md#2-mqtt-broker-on-the-always-on-esp32-feasibility)) |
| **VSS topic scheme** (ADR-0016) | **ADOPT** | `ostler/v1/<vid>/<device>/…` with VSS paths (§3.3). HA discovery and the OVMS tree are generated aliases at the edge, never the internal names |
| **Home Assistant MQTT device discovery** | **ADOPT** (U5) | One `homeassistant/device/<id>/config` per module, with `dev`, `o` and `cmps` blocks ([HA](https://www.home-assistant.io/integrations/mqtt/)), generated from the module manifest. HA sees the car and each module as devices, with read-only buttons only |
| **Matter**, add-on modules as Matter devices | **AVOID** | See §2.1 |
| **Matter**, a bridge exposing the car to Matter controllers | **ADOPT-LATER** (a long-term goal, owner 2026-10-06), opt-in, read-only | See §2.1 |
| **COVESA VISS v3** (WebSocket, HTTP, MQTT, gRPC; RC published 2025-01-31) | **ADOPT-LATER** as the external vehicle-data API shape | Our topics and payloads already follow VSS paths and VISS-like `{value, ts}` ([COVESA](https://covesa.global/covesa-viss-version-3-0-release-candidate/), [transport](https://raw.githack.com/COVESA/vehicle-information-service-specification/main/spec/VISSv3.0_Transport.html)). A conformant endpoint is a bridge, added when a client needs it (standards.md §8.3) |
| **Eclipse KUKSA databroker** (gRPC, `kuksa.val.v2`, 0.6.x) | **REFERENCE-ONLY**; an optional bridge package later | A Rust broker beside ours goes against ADR-0002; CVE-2026-13699 (a 0.6.1 panic) shows it is still young ([OpenCVE](https://app.opencve.io/cve/CVE-2026-13699)) |
| **SOME/IP** (AUTOSAR; the spec is being opened by Technica and KPIT, January 2026) | **REFERENCE-ONLY** | OEM ECU-to-ECU SOA. Its open stacks are vsomeip (MPL-2.0) and Eclipse SommR (Apache-2.0). It solves a problem we do not have and is invisible to the smart-home world ([announcement](https://themachinemaker.com/news/technica-engineering-and-kpit-open-some-ip-specification-to-advance-automotive-ethernet-innovation/), [SommR](https://projects.eclipse.org/projects/automotive.sommr)) |
| **DDS / Zenoh** | **REFERENCE-ONLY** | Broker-less pub/sub with rich QoS, strong in ROS 2 and AUTOSAR AP ([middleware comparison](https://arxiv.org/html/2505.02734v2)). Heavier on an ESP32 and with no HA path. Revisit Zenoh only if the broker becomes a bottleneck |
| **LwM2M 1.2** | **AVOID** (as in standards.md) | Needs its own server and object model. Borrow the Firmware Update object's state fields (object 5) for our OTA status topic |
| **SUIT** (RFC 9019 architecture, RFC 9124 information model; manifest draft-37, June 2026) | **REFERENCE-ONLY** now; ADOPT-LATER when the RFC is published | Shape our OTA manifest fields on it ([draft](https://datatracker.ietf.org/doc/html/draft-ietf-suit-manifest-37)) |
| **MCUboot / ESP-IDF secure boot v2 + signed OTA** | **ADOPT-LATER** (first hardware) | Signed images, rollback and an update log (the R156 lesson), served over HTTPS by the Pi |
| **ONVIF Profile S/T + RTSP** | **ADOPT** for cameras | ONVIF discovery and stream URIs, then go2rtc; Profiles S and T are current ([ONVIF](https://www.onvif.org/profiles/)) |
| **mTLS for MQTT, a per-node X.509 identity** | **ADOPT** | See §2.2 |
| **IEEE 802.1AE MACsec (+ 802.1X MKA) on T1S** | **ADOPT-LATER**; the U5 threat model decides | See §2.2 |

### 2.1 Matter

- **Transport.** Matter runs over IP on Wi-Fi, Thread **and Ethernet**: "you have the choice
  of various network transport options, including Wi-Fi, Thread, and Ethernet"
  ([CSA](https://csa-iot.org/certification/why-certify/)). ESP32-S-series parts need an external
  Ethernet controller ([Espressif](https://www.espressif.com/en/solutions/device-connectivity/esp-matter-solution)).
  So T1S is technically possible: it is Ethernet, IPv6 and mDNS (U, untested).
- **Device types.**
  - Matter 1.4 and 1.5 cover what a car module could map to: contact, occupancy, temperature
    and light sensors, plugs and switches (≈ relays), door lock, and EVSE. EVSE is the
    charger, not a vehicle.
  - Matter 1.5 (2025-11-20) adds **cameras** over Wi-Fi, PoE or Ethernet, with WebRTC streaming
    ([TechSpot](https://www.techspot.com/news/110350-matter-15-adds-universal-camera-standard-now-big.html),
    [GRL](https://www.graniteriverlabs.com/en-us/technical-blog/matter-1.5-cameras-closures-energy)).
  - There is **no vehicle device type** and **no alarm-panel device type** (U)
    ([device types](https://handbook.buildwithmatter.com/how-it-works/device-types/)).
- **Cost** ([CSA membership](https://csa-iot.org/become-member/)): Adopter **$7,500 a year**
  (Participant $21,500, Promoter $112,500) plus **$3,000 per product** ($2,500 derivative;
  $2,000 for Participants) plus test-lab fees. Associates ($0) can only white-label a
  certified product ($2,500 plus $500 a year). Uncertified devices commission with warnings,
  or not at all, depending on the controller
  ([Nordic DevZone](https://devzone.nordicsemi.com/f/nordic-q-a/126780/matter-examples-device-attestation)).
- **Fabric reality.** A Matter fabric belongs to a home's controllers. A car leaves home, and
  in-car modules would have no controller on the road.
- **Bridges.** A Matter bridge exposes non-Matter devices as endpoints
  ([Nordic](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/protocols/matter/overview/bridge.html)).
  **Matterbridge** (Apache-2.0, on matter.js) already re-exposes Home Assistant entities to
  other Matter ecosystems ([GitHub](https://github.com/Luligu/matterbridge)).
- **Verdict.**
  - **Modules do not speak Matter.** Inside the car they speak MQTT. It costs nothing per
    module, works with no home controller, and HA discovery already covers it.
  - **Reach Matter through a bridge.** Today that is HA → Matterbridge: zero cost to us,
    opt-in.
  - A **native Matter bridge on the Pi** is an ADOPT-LATER for when it is at home on Wi-Fi. It
    would be read-only, plus the software alarm's arm state if a fitting device type exists.
    It runs as a separate process (connectedhomeip/matter.js are Apache-2.0), so ADR-0002
    holds.
  - Certify only if hardware sales justify $7,500 a year plus $3,000 per product.
  - A **Matter 1.5 camera** could later be ingested like an ONVIF one (REFERENCE).

### 2.2 Security baseline

- **Per-node identity.**
  - Each module generates its key pair on the device; on the ESP32-S3 it is protected by
    flash encryption and secure boot (U: confirm on the guardian).
  - At pairing the Pi's local CA signs it. This is the same per-device CA question as ADR-0021.
- **mTLS to the broker** (port 8883). Per-node ACLs let a module publish only under its own
  subtree and subscribe only to its own command topics. Telemetry consumers are
  read-only.
- **Standard practice, not a custom envelope** (owner, 2026-10-06): mTLS with device
  certificates, MQTT 5 authentication with per-device ACLs, and passkeys (WebAuthn) or
  passwords for people (ADR-0029). No trust from bus membership. The CAN fallback's
  equivalent is open (ADR-0026 as amended).
- **MACsec on T1S.**
  - It is shown working in research: Technica's CRESEC project ran T1S with PLCA, AES-GCM
    MACsec, 802.1X MKA and gPTP across four nodes, August 2026
    ([AEEmobility](https://aeemobility.de/english-content/secure-ip-solution-for-zonal-vehicle-architectures/)).
  - None of our MAC-PHYs offers it in hardware (U). Linux has software MACsec, and no ESP-IDF
    support was found (U).
  - It is a U5 threat-model item, not a baseline.
- **No universal default passwords**, a vulnerability policy and a stated update period
  (UK PSTI, EU CRA; [standards.md §5](standards.md)).

## 3. Product taxonomy and the module contract

### 3.1 Products

| Product | Contents | Tag |
|---|---|---|
| **Base hardware pack** (the core) | Linux brain: Pi 5 + CarPiHAT now, our CM5/i.MX93 board later, woken on demand (always-on optional for EVs). **ESP32 buddy** (always on): wake and Pi power, read-only bus listening while parked, basic alarm, the parked broker, the PLCA coordinator while parked; no SIM of its own (ADR-0028). **Vehicle interface**: K-line (L9637-class), 2 × CAN (listen-only by default), OBD-II harness, optional body-bus front end, ignition and 12 V sense. **Network**: T1S port (LAN8651, the PLCA coordinator while awake), an Ethernet port for cameras, a Wi-Fi AP for displays, GNSS for time and logging. **Software**: diagnostics, logbook and telemetry, broker, discovery proxy, local CA, HA/MQTT integration | core |
| **Guardian** (alarm and tracker) | The always-on alarm system and gateway: ESP32-S3 with LTE and GNSS on its own cell; a **notify-only** alarm with escalation; works with 12 V cut; a CAN or wake-wire fallback | add-on |
| **Relay box** | Switched outputs; each channel declares a tier (default Tier 2, Parked-only, never remote; UI spec §6) | add-on |
| **Sensor and button nodes** | Door/bonnet/tilt/temperature inputs, panel buttons; read-only signals and events | add-on |
| **HEVAC controller** | The owner's separate project; joins through the contract; `comfort` actions | add-on (external) |
| **Cameras** | Standard ONVIF/RTSP IP cameras on the camera segment through a DevicePack adapter; our own cameras later | add-on |
| **Displays** | Head unit, phones and tablets as PWA clients; the Ostler Android launcher later | core / add-on |
| **Third-party modules** | Anything that implements the contract and passes the conformance kit ("works with Ostler", [TRADEMARKS.md](../../TRADEMARKS.md)) | add-on |

### 3.2 The module contract (a device-side twin of the vehicle-pack contract)

A **module manifest** is JSON validated by a planned `schemas/module-manifest.schema.json`. It
has the same shape as a `capabilities.devices` entry in the
[UI spec §6](../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices):

- **Identity:** `id`, `vendor`, `model`, `hw`, `fw`, `contract` (an integer major), and a
  certificate fingerprint. Never a VIN.
- **Class and links:**
  - `class` is one of guardian, relay, sensor, button, climate, camera, display, other;
  - `links` lists t1s, ethernet, wifi or can;
  - `power` is always_on, switched or wake_capable;
  - `alarm_critical: true` requires a wired link (ADR-0026).
- **Signals:** VSS paths (ADR-0016; our extensions under `Vehicle.Ostler.*`), units verbatim,
  rate, `expire_after`, and confidence (`proven`/`candidate`).
- **Actions:**
  - `id` and `tier` (UI spec §7);
  - `comfort` only if the action never reaches a vehicle ECU or bus (ADR-0018);
  - `parked_only`, `remote` (false by default), interlocks, and whether the device enforces
    it too.
  - Every action passes the **one server gate**. Modules accept commands only from an
    authenticated broker client whose ACL allows them (mTLS, MQTT 5 auth).
- **Events:** names and payloads (e.g. `alarm.triggered`, `button.pressed`).
- **UI slots:** one strip slot and one page at most (UI spec §6). Views come from a
  DevicePack, never from the module.
- **OTA:** image type, signing-key id and update channel (SUIT-shaped fields).
- **Delivery:**
  - A native module publishes its manifest retained on
    `ostler/v1/<vid>/<device>/manifest` and points at it from its mDNS TXT record.
  - A device that cannot describe itself (an ONVIF camera, the HEVAC API) gets an **adapter**
    in a **DevicePack** (`openostler.device` entry point; UI spec §6, triggered by the
    second device). This is the Zigbee2MQTT converter pattern.
- **Conformance kit:**
  - schema validation and a simulated broker;
  - gate tests: no Tier ≥ 2 action is reachable remotely, and an unauthenticated command is
    rejected;
  - an offline test that a stale value is flagged.

### 3.3 Topic tree (proposal for the module-bus message spec)

```
ostler/v1/<vid>/<device>/manifest              retained JSON manifest
ostler/v1/<vid>/<device>/status                retained online|offline (LWT)
ostler/v1/<vid>/<device>/state/<VSS/path>      {"v":…, "ts":"RFC 3339", "c":"proven|candidate"}; MQTT 5 expiry
ostler/v1/<vid>/<device>/event/<name>          events
ostler/v1/<vid>/<device>/cmd/<action>          ACL-restricted (mTLS client); response topic + correlation data
ostler/v1/<vid>/<device>/ota                   LwM2M-object-5-style state
```

`<vid>` is the device-local vehicle handle (ADR-0018), never the VIN. `<vid>=vehicle` with
`<device>=base` carries the car's own signals from the base pack. HA discovery and the OVMS
tree are generated from this tree.

## 4. Comparisons

**Smart-home ecosystems, and what we borrow:**
- **Matter**: one data model, IP on any link, setup-code commissioning, per-device
  attestation, bridges. *Borrow* the setup-code pairing, per-device certificates and the
  bridge pattern; *not* a certification gate for every module.
- **Home Assistant integrations**: one device-plus-entity registry; MQTT discovery lets a
  device describe itself. *Borrow* the registry shape, `expire_after`, availability and
  self-description.
- **Zigbee2MQTT**: a per-model **converter database** maps vendor devices onto one MQTT model
  plus HA discovery
  ([Zigbee2MQTT](https://zigbee2mqtt.io/guide/usage/integrations/home_assistant.html)).
  *Borrow:* adapters for foreign devices (cameras, HEVAC) live in DevicePacks; native modules
  need none.

**Zonal E/E architectures.**
- **How OEMs do it.** A central compute unit links over multi-gigabit Ethernet to **zonal
  controllers**, which switch and gateway the legacy CAN/LIN in their area; **10BASE-T1S**
  connects the edge nodes
  ([ADI](https://www.analog.com/en/resources/analog-dialogue/articles/how-10base-t1s-ethernet-simplifies-zonal-architectures.html)),
  down to "software-less" endpoints such as the Microchip LAN866x for LEDs, audio and
  actuators
  ([Electropages](https://www.electropages.com/2025/11/advancing-zonal-architecture-10base-t1s-endpoints-delivers-smarter-remote-connectivity)).
- **The mapping.** The **Pi** is the central compute; the base pack's **vehicle interface** is
  a zonal controller's legacy gateway, but receive-first and gated; the **T1S segments** are
  the edge; the **buddy** is the always-on body controller and the **guardian** the add-on
  telematics and alarm controller.
- **The difference.** OEMs replace the car's buses; we sit beside them and never replace them.
- **Later.** A larger vehicle (van, overlander) may want a **zone hub** module: a T1S
  coordinator plus a small switch per area. That is a later product, not a new architecture.

## 5. Risks and open points

1. The T1S driver maturity and coordinator-loss behaviour are covered by the
   [bench plan](../t1s_bench_plan.md). Add a test for a CSMA/CD node joining a PLCA segment.
2. **Where the broker lives while parked:** decided in ADR-0028 (buddy, bridged).
3. Pi Wi-Fi as an AP and a client at once: one radio, one channel (ADR-0028); bench it (U).
4. A CA and key-rotation design (ADR-0021) and MACsec are U5 threat-model items; the IANA
   request is drafted ([connectivity §6](connectivity_uplink.md#6-draft-iana-service-name-registration-the-owner-submits)).
5. Matter certification cost against the benefit, if official hardware ships a native
   bridge.
