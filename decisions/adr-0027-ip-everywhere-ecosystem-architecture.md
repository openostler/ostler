---
title: "ADR-0027 — IP everywhere: the ecosystem architecture (base pack, add-on modules, automotive-Ethernet backbone)"
area: decisions
status: locked
version: 1.6
updated: 2026-10-06
depends_on: [references/research/ecosystem_architecture.md, references/research/connectivity_uplink.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0024-body-bus-links-passive-by-default.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Builds on ADR-0026. Ostler is a smart-home-like ecosystem: a base hardware pack interfaces with the car and add-on modules join over standard networking. Every Ostler device speaks IP on an automotive-Ethernet backbone: 10BASE-T1S for modules, standard Ethernet (12 V or PoE) for cameras now and 100BASE-T1 only for our own camera hardware, Wi-Fi or USB for displays. The Pi routes between segments. One message model (VSS-named MQTT 5, ADR-0016/0017), mDNS/DNS-SD discovery, dual-stack addressing, NTP from GNSS (PTP later), a security baseline (per-node identity, mTLS device certificates, MQTT 5 authentication with per-device ACLs, no trust from bus membership, no default passwords; ADR-0026 as amended) and one module contract (a manifest with VSS signals and safety-tiered actions; DevicePack adapters for foreign devices). The car's buses stay at the edge. CAN and the wake wire stay as the fallback. Matter is reached through a bridge, never inside modules (a long-term goal). Amended by the owner on 2026-10-06 (ADR-0028): the base is the Pi plus an always-on ESP32 buddy and the guardian is an add-on; uplinks are existing in-car Wi-Fi, hotspots or any USB dongle, with selection, failover and metering; a parked broker on the buddy bridged to the Pi's Mosquitto; security is standard practice (TLS/mTLS, MQTT auth and ACLs, passkeys or passwords for people) rather than a custom envelope; modules host their own web pages. Amended again on 2026-10-06 (networking answers, ADR-0037/0038): Matter via Home Assistant and Matterbridge until at scale, with alarm disarm allowed and Comfort switches only with the install override; NTP runs on the time-role holder; PLCA IDs live in each device's install configuration; mesh and Matter are remote paths.
---

# ADR-0027 — IP everywhere: the ecosystem architecture

> **Superseded in part by [ADR-0032](adr-0032-one-node-optional-brain.md) (§1–§2, §5), 2026-10-06:** the Amendments' "Base and guardian" entry (node replaces the buddy; the guardian is a node variant) and §9's "one server gate" wording for car-touching actions (that gate is on the node).
> **Superseded in part by [ADR-0033](adr-0033-action-categories-and-approvals.md) (§6–§7), 2026-10-06:** the "notify-only alarm" line and "Tier ≥ 2 not reachable from any remote path" (phone approval over local links; install override).
> **Amended 2026-10-06 (networking answers, [ADR-0037](adr-0037-role-holders-and-handover.md), [ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md)):** §12 Matter is a bridge through Home Assistant and Matterbridge, certified only at scale, with alarm disarm allowed and Comfort switches only with the install override; §3/§7 NTP runs on the time-role holder; §4 PLCA IDs live in each device's install configuration; mesh and Matter are remote paths. See [Amendments (networking answers)](#amendments-2026-10-06-networking-answers).
> **Amended 2026-10-06 (product family, [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md)):** §2's segments gain the node link (USB-NCM, its own subnet); §5's topics gain `tap/` and `lab/`. See [Amendments (product family)](#amendments-2026-10-06-product-family).
> **Amended 2026-10-06 (Brain rename, [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)):** read "Ostler Hub" and "Hub" (the product, also "hub" for the box) as "Ostler Brain" and "Brain". See [Amendments (Brain rename)](#amendments-2026-10-06-brain-rename).

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06; from the
  [ecosystem research](../references/research/ecosystem_architecture.md)). **Builds on
  [ADR-0026](adr-0026-module-bus-10base-t1s.md)**, which stays the module-bus decision.
  Amended by the owner on 2026-10-06 together with
  [ADR-0028](adr-0028-base-hardware-connectivity-and-remote-access.md): base hardware,
  uplinks, broker placement, security and Matter (see
  [Amendments](#amendments-2026-10-06-owner-answers)).

## Context

- **The owner's direction (2026-10-06).** The goal is "an entire automotive ecosystem like a
  smart house but for cars based on 10base-t1s".
  - At its core is the diagnostic and telemetry system on a **base hardware pack** that
    interfaces with the car and "makes it IOT".
  - **Add-ons** (alarm module, cameras, relay boxes) join it, and "everything should already
    use standard networking routing etc.", with "more standardization and greater
    intercompatibility".
- **ADR-0026** chose 10BASE-T1S for our modules and one VSS/MQTT-style message model. It left
  open the rest of the network:
  - cameras;
  - displays;
  - routing;
  - addressing;
  - discovery;
  - time;
  - the device contract.
- **Cameras cannot share T1S.** It is 10 Mbit/s and shared, and one camera stream takes
  several Mbit/s. Retail 100BASE-T1 cameras do not exist at hobby prices: a media converter
  costs $260–325 per link. Standard Ethernet costs a few pounds per camera
  ([research §1.2](../references/research/ecosystem_architecture.md#12-cameras-100base-t1-against-standard-ethernet-or-poe-live-prices)).
- **Matter** allows Ethernet. But it has no vehicle device type, it costs $7,500 a year plus
  $3,000 per product to certify, and its fabric lives in the home, not the car
  ([research §2.1](../references/research/ecosystem_architecture.md#21-matter)).

## Decision drivers

- One network model and one message model from the Pi to the smallest module, so modules,
  including third-party ones, are interchangeable.
- Interoperability with the smart-home world (Home Assistant first) without per-device glue.
- Open, royalty-free standards (ADR-0017). No certification gate on every module.
- The hard lines hold:
  - notify-only alarm;
  - gated writes;
  - no MQTT path to a vehicle bus;
  - VIN never logged;
  - local-first;
  - alarm-critical links on a wire.
- The ADR-0002 runtime stays: network services are OS packages or separate processes, not
  Python dependencies.

## Decision

**1. IP everywhere is the architectural principle.**
- Every Ostler device (base pack, modules, cameras, displays) is an IP host on one in-car
  network built on an automotive-Ethernet backbone.
- Firmware and server code address hosts and topics, never physical layers.

**2. Segments.**

| Segment | Physical layer |
|---|---|
| **Modules** | 10BASE-T1S with PLCA (ADR-0026) |
| **Cameras** | Standard Ethernet now (100BASE-TX/GbE), with 12 V on separate wires by default and PoE where a camera needs it. **100BASE-T1** only when we build our own camera hardware |
| **Displays and phones** | Wi-Fi from the Pi's access point, or USB tethering |
| **Uplinks** | ~~LTE or home Wi-Fi, opt-in~~ Amended: existing in-car Wi-Fi, a phone hotspot, home Wi-Fi or any USB 3G/4G dongle; Starlink, a high-speed gateway and guardian LTE as options; owner-selected or priority failover, with metering (ADR-0028). Outbound data stays opt-in |

Video never crosses the T1S segment.

**3. The Pi is the router and gateway.**
- Each segment is its own routed subnet and IPv6 /64. The Pi does not bridge them.
- The Pi firewalls between segments: cameras and clients cannot open connections to modules.
- It runs the MQTT broker, the discovery proxy, NTP and the local CA. *Amended:* the Pi's
  broker serves while the Pi is awake; a parked broker on the base's always-on ESP32 buddy
  serves a minimal set and is bridged by the Pi (ADR-0028 §5).
- These are OS services, not Python dependencies.

**4. Addressing.**
- Dual stack: IPv6 link-local plus a per-vehicle ULA prefix by SLAAC, and IPv4 by DHCP from a
  per-vehicle random RFC 1918 block.
- Hosts are found by name (mDNS), never by a hard-coded address.
- PLCA node IDs are assigned by the coordinator at pairing. A new node joins in CSMA/CD mode
  first.

**5. One message model** (ADR-0016, ADR-0017, ADR-0026).
- **MQTT 5**, with VSS-named topics under `ostler/v1/<vid>/<device>/…` and JSON payloads
  carrying value, RFC 3339 timestamp and confidence.
- Home Assistant discovery, the OVMS tree, OwnTracks and any VISS or Matter view are
  **generated at the edge** from this one model.
- `<vid>` is never the VIN.

**6. Discovery.**
- mDNS/DNS-SD (RFC 6762/6763), with an RFC 8766 discovery proxy across segments.
- Modules advertise an Ostler module service; the Pi advertises the broker.
- Cameras are found by ONVIF and driven over RTSP.

**7. Time.**
- NTP (chrony) on the Pi, disciplined by GNSS and its PPS, for every segment.
- PTP/gPTP (802.1AS) only when a feature needs sub-millisecond alignment, after the
  multidrop T1S support matures.

**8. Security baseline.**
- **Per-node identity:** a key generated on the device and a certificate from the Pi's local CA
  (the ADR-0021 trust question).
- **Pairing:** the owner confirms it physically (a button, or a setup code). There are no
  default passwords (UK PSTI).
- **The broker:** mTLS with per-node ACLs.
- ~~ADR-0026's end-to-end envelope still applies (per-node key, counter, MAC) to commands
  and alarm-critical messages on every transport.~~ *Amended:* standard network security
  replaces a custom envelope on IP transports: TLS/mTLS with device certificates, MQTT 5
  authentication with per-device ACLs, no trust from bus membership, and passkeys (WebAuthn)
  or passwords for people. The CAN fallback's equivalent is open (ADR-0026 as amended).
- MACsec on T1S is left to the **U5 threat model**.

**9. The module contract.**
- Every add-on declares itself in a **module manifest**: one JSON Schema, the same shape as a
  `capabilities.devices` entry (UI spec §6). It holds:
  - identity and contract version;
  - class, links and power profile;
  - VSS-named signals with units and confidence;
  - actions with safety tier, `comfort` (ADR-0018), Parked-only and remote flags;
  - events, UI slots, and OTA fields.
- `alarm_critical` requires a wired link.
- Every action passes **the one server gate**. Modules never define safety; they declare it,
  and the server enforces it.
- Native modules publish their manifest (retained) themselves.
- Foreign devices (ONVIF cameras, the HEVAC API) get an **adapter in a DevicePack**
  (`openostler.device`).
- A conformance kit makes third-party modules possible under "works with Ostler".

**10. The car's buses stay at the edge.**
- K-line, vehicle CAN, I/K-Bus and OBD-II are interfaced only by the base pack's front ends,
  under ADR-0020, ADR-0022 and ADR-0024.
- They are never replaced and never bridged onto our network. No module and no MQTT topic
  reaches a vehicle bus except through the platform's gate.

**11. The fallback stays (ADR-0026).**
- CAN and Wi-Fi remain the dev-kit transports.
- CAN or the separate wake wire carries µA-wake nodes until a bench proves T1S sleep and wake.
- Wi-Fi never carries alarm-critical links.

**12. Matter.**
- Modules do not implement Matter. A Matter bridge is a **long-term goal** (owner,
  2026-10-06).
- The car reaches Matter ecosystems through a **bridge**: Home Assistant with an open-source
  bridge today, and possibly a native, opt-in, read-only bridge on the Pi later.
- Certification is decided only if hardware sales justify it.
- *Amended 2026-10-06: see [Amendments (networking answers)](#amendments-2026-10-06-networking-answers), Matter.*

## Confirmation

- **A paper check now.** No spec or doc proposes a "private CAN bus" as the primary add-on
  transport, video on T1S, or a module-to-vehicle-bus path.
  The direction spec, GOALS and the hardware research are updated with this ADR.
- **On the T1S bench** ([bench plan](../references/t1s_bench_plan.md)), with the Pi routing
  between segments, all of the following pass:
  - a fresh module, never configured, appears in the UI and in Home Assistant within
    **60 s** of pairing, with no address typed anywhere;
  - a camera stream on the Ethernet segment adds **no** traffic to the T1S segment
    (interface counters);
  - an unauthenticated or replayed command is rejected;
  - a Tier ≥ 2 action is not reachable from MQTT, HA or any remote path;
  - a module's `state` messages carry VSS paths that resolve in `metrics.json`;
  - module and Pi clocks agree within **10 ms** over NTP.
- **The conformance kit** validates every manifest in CI against the module-manifest schema
  once the module-bus message spec lands.

## Consequences

- A **module-bus message spec** comes before any firmware (it was already required by
  ADR-0026). It covers:
  - the topic tree;
  - the manifest schema;
  - ~~the authentication envelope~~ certificates, ACLs and the CAN-fallback authentication
    (ADR-0026 as amended);
  - the CAN mapping;
  - ~~where the broker lives while parked~~ the parked topic set and bridge patterns
    (placement decided in ADR-0028).
- The DevicePack contract is designed with it.
- The base pack needs a router configuration: systemd-networkd, nftables, chrony, Mosquitto
  and an mDNS proxy, carried as OS configuration in the deploy tooling. *Amended:* uplinks
  are managed by NetworkManager and ModemManager with vnStat metering (ADR-0028); which
  manager owns the internal segments is settled in that configuration work.
- Cameras are bought, not built, until the camera segment's own hardware is justified. The
  direction spec's camera constraints (latency, pre-event buffer) stay open.
- The phrase "private CAN bus" leaves the plans. Phase 4 becomes "add-on modules on the module
  bus".

## Alternatives considered

- **A private CAN bus for all add-ons** (the earlier hardware research). Rejected as the
  primary transport (ADR-0026). Kept as the fallback.
- **Bridging all segments into one L2 network.** Rejected: camera and discovery multicast
  would flood T1S, and there would be no firewall between device classes.
- **100BASE-T1 cameras now.** Rejected on cost (about $300 a link off the shelf) and supply.
  Kept for our own hardware.
- **Matter inside every module.** Rejected: no home controller in a moving car, a cost per
  product, and no vehicle device type.
- **SOME/IP or DDS as the message model.** Rejected: OEM SOA with no smart-home path, and
  heavier on an ESP32. Reference only.
- **KUKSA databroker or LwM2M in the core.** Rejected: a second broker or server against
  ADR-0002. Either may come later as a bridge.

## Amendments (2026-10-06, owner answers)

The owner answered the open questions on the day this ADR was accepted. The details are in
[ADR-0028](adr-0028-base-hardware-connectivity-and-remote-access.md) and the
[connectivity research](../references/research/connectivity_uplink.md); the statements
above are marked where they changed.

- **Base and guardian.** The base hardware pack is the Pi plus an always-on **ESP32 buddy**
  (wake, Pi power, bus listening while parked, basic alarm). The **guardian is an add-on**:
  the always-on alarm system and gateway. The buddy is the base's always-powered node.
- **Uplinks** (§2). The base has no internet of its own. It uses existing in-car Wi-Fi, a
  phone hotspot, home Wi-Fi or any USB 3G/4G dongle, with Starlink, a high-speed gateway and
  guardian LTE as options. The owner selects a source or a priority failover, and each
  source can carry a metered flag and a data budget with alerts.
- **Broker placement** (§3, Consequences). Espressif's Mosquitto port on the buddy hosts a
  parked minimal set; Mosquitto on the Pi is the full broker when awake and bridges to it.
  Always-on (EV) mode keeps the Pi broker up.
- **Security** (§8). Standard practice instead of a custom bus scheme: TLS/mTLS for devices,
  MQTT 5 authentication with per-device ACLs, no trust from bus membership, and passkeys
  (WebAuthn) or passwords for people (accounts in ADR-0029). ADR-0026's per-node key,
  counter and MAC envelope is dropped (ADR-0026 as amended). Per-node identity, physical
  pairing and no default passwords stand.
- **Discovery** (§6). `_ostler-mod._tcp` is to be registered with IANA; the draft request is
  in the connectivity research §6, for the owner to submit.
- **Displays and Wi-Fi** (§2). The Pi's access point and a Wi-Fi client share one radio on one
  channel. Every module also hosts its own small web page and can work on its own; Wi-Fi
  modules are provisioned with Improv Wi-Fi, with a captive-portal fallback.
- **Remote access.** LAN only by default; Tailscale opt-in; an Ostler Cloud product that is
  never the only option; Home Assistant Cloud through Home Assistant. Every remote path
  passes the same server gate.
- **Matter** (§12). A bridge is a long-term goal; modules still do not implement Matter.
- **Node and brain (later, 2026-10-06).** The "Base and guardian" entry above and §9's
  "one server gate" for car-touching actions are superseded in part by
  [ADR-0032](adr-0032-one-node-optional-brain.md): the ESP32 node replaces the buddy and
  holds the only transmit gate; the guardian is a node variant.

## Amendments (2026-10-06, networking answers)

Accepted by the owner on 2026-10-06 with the answers to the networking questions
([ADR-0037](adr-0037-role-holders-and-handover.md),
[ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md)). Question numbers in brackets are the
owner's numbering for that day. The decision text above is unchanged; where these entries
differ, they win.

### Matter, bridge only (§12; owner Q6, Q7)

*Evidence: live checks of 2026-10-06 ([CSA membership](https://csa-iot.org/become-member/),
[esp-matter](https://github.com/espressif/esp-matter),
[Matterbridge](https://github.com/Luligu/matterbridge)).*

- **Until we are at scale: a bridge we do not certify** (owner Q6). Home Assistant picks up
  our MQTT discovery, and Matterbridge (Apache-2.0, 3.10.12 on 2026-10-02) or the community
  Home Assistant Matter Hub add-on (original archived January 2026, a fork continues; U)
  re-exposes it to Matter controllers. Nothing in our code speaks Matter.
- **A certified Ostler bridge only "once we're huge"**, that is at scale: on the brain, a
  separate process (matter.js or connectedhomeip, Apache-2.0). Live costs for that decision:
  Adopter **$7,500 a year** and **$3,000 per product** ($2,500 per derivative); Participant
  $21,500 a year with $2,000 per product ($1,500 derivative); Promoter $112,500 a year plus
  initiation; Associate free but only white-labels a certified product ($2,500 plus $500 a
  year). Test-lab fees are extra (U). Matter 1.6 shipped on 2026-06-17.
- **Exposed entities, each declaring category and tier (ADR-0033)** (owner Q7):

  | Entity | Category, tier | Matter mapping (U where no exact type) |
  |---|---|---|
  | Battery voltage; EV charge | Read, 0 | Power Source cluster on a bridged endpoint |
  | Fuel level | Read, 0 | No fitting cluster (U); omitted until one exists |
  | Cabin temperature | Read, 0 | Temperature sensor |
  | "Car is home" | Read, 0 | Occupancy or contact sensor |
  | Alarm state | Read, 0 | Contact or boolean state; no alarm-panel type (U) |
  | Arm and disarm the software alarm | Security, 1 | On/off switch; disarm Parked only, audited and notified to the owner |
  | Preheat, aux heater | Comfort, 1 | On/off switch, **only with the install override** |

- **Every command goes through the node gate** (ADR-0032), which re-checks role, category,
  tier, driving state and transport. **Matter is a remote path** (ADR-0033 §6 as amended):
  Read plus arming and **disarming** the software alarm, consistent with over-the-air
  disarm (ADR-0033 §6 amendment); preheat and aux-heater switches are refused unless
  `OSTLER_ALLOW_REMOTE_CONTROL` is set on the node; nothing above Tier 1 is ever exposed, and
  Tier 2+ never runs over Matter, override or not. A Matter fabric has no per-user identity,
  so the bridge acts under one owner-issued token with a narrowed role.
- **Never** for the in-car module bus or the car-to-car mesh
  ([ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md)).
- **Native Matter add-on modules** (Espressif ESP-Matter SDK, Apache-2.0, release v1.6
  with v1.7 on main) stay a later option for home-side devices only, each certified as its
  own product.

### Time (§3, §7)

- **NTP runs on the time-role holder** ([ADR-0037](adr-0037-role-holders-and-handover.md)
  §2), not always on the Pi: the device with the best clock (GNSS, with PPS where wired)
  serves NTP/SNTP to every segment, and the role hands over when that device is lost.
  chrony on the brain stays the implementation when the brain holds the role; which device
  carries the 10 Hz u-blox is pending (product-family research; ADR-0032 Amendments).

### PLCA IDs (§4)

- **PLCA node IDs live in each device's install configuration.** They are still assigned at
  pairing, and the full ID table for a segment is stored in the signed install
  configuration of every device on it, so a standby (the guardian alongside the node,
  ADR-0026 Amendment 8) can take over as coordinator without the brain.

### Remote paths (§5, §12)

- **Mesh and Matter are remote paths** under ADR-0033 §6: a mesh carries Read and alerts
  only (ADR-0038 §2); Matter carries Read plus alarm arming and disarming, and Comfort only
  with the install override (above). Neither is a local link, whatever radio it rides on.

## Amendments (2026-10-06, product family)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (accepted with the owner's answers of 2026-10-06). The decision text above is
unchanged; where these entries differ, they win.

- **Segments (§2, §3).** The table gains **Node link: USB-NCM** (CDC-NCM, ECM fallback), a
  point-to-point link between a Diagnostics node and a hub within a USB cable of it. It is
  **its own routed subnet** and IPv6 /64, like every segment (§3); 10BASE-T1S stays the node
  link when the hub is elsewhere (ADR-0026 Amendment 9).
- **Topics (§5).** Beside the VSS topics, the node publishes its raw tap on
  `ostler/v1/<vid>/<node>/tap/<session>/data` (binary batches, never retained) with the
  session header retained on `…/tap/<session>/meta`, and takes lab send-requests on
  `…/<node>/lab/req`, answering on `…/<node>/lab/resp` (ADR-0039 §3). Both use the same
  broker, mTLS and per-device ACLs.

## Amendments (2026-10-06, Brain rename)

- **Names.** Read "Ostler Hub" and "Hub" above (and "hub" where it means our compute box) as
  "Ostler Brain" and "Brain" ([ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)). The decision text and the Amendments above are
  unchanged.
