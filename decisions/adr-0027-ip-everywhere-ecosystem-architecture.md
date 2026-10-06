---
title: "ADR-0027 — IP everywhere: the ecosystem architecture (base pack, add-on modules, automotive-Ethernet backbone)"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [references/research/ecosystem_architecture.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0024-body-bus-links-passive-by-default.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Builds on ADR-0026. Ostler is a smart-home-like ecosystem: a base hardware pack interfaces with the car and add-on modules join over standard networking. Every Ostler device speaks IP on an automotive-Ethernet backbone: 10BASE-T1S for modules, standard Ethernet (12 V or PoE) for cameras now and 100BASE-T1 only for our own camera hardware, Wi-Fi or USB for displays. The Pi routes between segments. One message model (VSS-named MQTT 5, ADR-0016/0017), mDNS/DNS-SD discovery, dual-stack addressing, NTP from GNSS (PTP later), a security baseline (per-node identity, mTLS, ADR-0026's command envelope, no default passwords) and one module contract (a manifest with VSS signals and safety-tiered actions; DevicePack adapters for foreign devices). The car's buses stay at the edge. CAN and the wake wire stay as the fallback. Matter is reached through a bridge, never inside modules.
---

# ADR-0027 — IP everywhere: the ecosystem architecture

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06; from the
  [ecosystem research](../references/research/ecosystem_architecture.md)). **Builds on
  [ADR-0026](adr-0026-module-bus-10base-t1s.md)**, which stays the module-bus decision.

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
| **Uplinks** | LTE or home Wi-Fi, opt-in |

Video never crosses the T1S segment.

**3. The Pi is the router and gateway.**
- Each segment is its own routed subnet and IPv6 /64. The Pi does not bridge them.
- The Pi firewalls between segments: cameras and clients cannot open connections to modules.
- It runs the MQTT broker, the discovery proxy, NTP and the local CA.
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
- **ADR-0026's end-to-end envelope still applies** (per-node key, counter, MAC) to commands
  and alarm-critical messages on every transport.
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
- Modules do not implement Matter.
- The car reaches Matter ecosystems through a **bridge**: Home Assistant with an open-source
  bridge today, and possibly a native, opt-in, read-only bridge on the Pi later.
- Certification is decided only if hardware sales justify it.

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
  - the authentication envelope;
  - the CAN mapping;
  - where the broker lives while parked.
- The DevicePack contract is designed with it.
- The base pack needs a router configuration: systemd-networkd, nftables, chrony, Mosquitto
  and an mDNS proxy, carried as OS configuration in the deploy tooling.
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
