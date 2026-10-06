---
title: "ADR-0028 — Base hardware, connectivity and remote access (Pi + ESP32 buddy, guardian add-on, uplinks, parked broker, remote tiers)"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [references/research/connectivity_uplink.md, references/research/ecosystem_architecture.md, references/research/hardware.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md]
summary: >
  Owner answers of 2026-10-06. The base is the Pi plus an always-on ESP32 "buddy" (wake, Pi power, bus listening while parked, basic alarm, parked MQTT broker); the guardian is an add-on (always-on alarm and gateway). The base has no internet of its own: it uses existing in-car Wi-Fi, a phone hotspot, home Wi-Fi or any USB 3G/4G dongle, with Starlink, a high-speed gateway and guardian LTE as options; the owner selects a source or a priority failover, with per-source metering and data-cap alerts. Broker: Espressif's Mosquitto port on the buddy for a small parked set, full Mosquitto on the Pi when awake, bridged by the Pi. Remote access tiers: LAN only by default, Tailscale opt-in, an Ostler Cloud product (never the only option), HA Cloud through Home Assistant. Each module has its own web page; Improv Wi-Fi provisioning; IANA registration of `_ostler-mod._tcp` drafted; standard security; local-first.
---

# ADR-0028 — Base hardware, connectivity and remote access

> **Superseded in part by [ADR-0032](adr-0032-one-node-optional-brain.md) (§1–§2, §4–§5, §16), 2026-10-06:** §1 base definition (the node replaces the buddy; the guardian is a node variant), §2 power states (node wakes and cleanly shuts down the brain with a timeout), and all "buddy" wording (read "node"); §9's IANA request is submitted at module contract v1, unregistered in development.

- **Date:** 2026-10-06
- **Status:** accepted (owner answers, 2026-10-06; from the
  [connectivity research](../references/research/connectivity_uplink.md)). Builds on
  [ADR-0027](adr-0027-ip-everywhere-ecosystem-architecture.md) and amends its uplink,
  broker-placement and product-split statements (recorded in ADR-0027's Amendments).

## Context

- ADR-0027 left open where the MQTT broker lives while parked, and listed uplinks only as
  "LTE or home Wi-Fi, opt-in". The [hardware research](../references/research/hardware.md)
  and GOALS put the always-on role, LTE and Pi power control in the **guardian**, and asked
  whether the guardian ships in the base.
- **The owner's answers (2026-10-06):**
  - The guardian is an **add-on**. The **base** is the Linux computer (Pi) plus an ESP32
    **buddy** that does the wake-up and talks to the buses, and supports basic alarm features.
  - The base has **no internet of its own**. It uses networks already in the car (head-unit
    or car Wi-Fi, a phone hotspot) and works with **any 3G/4G USB dongle**. The guardian is the
    always-on alarm and gateway. Also wanted: a high-speed gateway option, **Starlink** as an
    integration, **selecting** the internet source or **failover**, and **connection
    metering** for data caps.
  - Remote access: support **Tailscale** (or leave it to people); an **Ostler Cloud** gateway
    is a product, a simple way to manage cars and get them online, but **not the only
    option**; **Home Assistant Cloud** compatibility.
  - The Pi is woken on demand by default; EVs may want **always-on**. Run the **MQTT broker on
    the always-on buddy**, alongside the possible 4G dongle (feasibility researched).
  - Register `_ostler-mod._tcp` with IANA; a **Matter bridge** is a long-term goal; Wi-Fi
    **AP and client on one radio**; every module hosts **its own small web UI** and works on
    its own; provisioning like other ESP32 projects. "We're making a Home Assistant for cars,
    not reinventing the wheel."
  - **Security is standard network practice**: TLS/mTLS for devices, MQTT authentication and
    ACLs, passkeys (WebAuthn) or passwords for people (also in ADR-0026 as amended).

## Decision drivers

- A useful base without a SIM, a subscription or the guardian.
- Local-first: everything works offline; nothing leaves the device without owner opt-in.
- Reuse what routers, ESP32 projects and Home Assistant already do (ADR-0017).
- Parked drain stays in the buddy's budget unless the owner chooses always-on.
- The hard lines hold: no write to the car without the gates; the VIN is never logged or
  uploaded; remote actions pass the same server tier gates; no MQTT path to a vehicle bus.

## Decision

**1. Base hardware = Pi + ESP32 buddy; the guardian is an add-on.**

| Part | Owns |
|---|---|
| **Pi** (Linux) | Server and PWA, diagnostics, full MQTT broker, router, uplink manager, local CA |
| **Buddy** (ESP32-S3 with PSRAM) | Pi power and wake decisions; read-only bus listening while parked (ADR-0020/0024); basic alarm inputs (doors, motion, 12 V) with notify-only alerts over whatever uplink exists; the parked broker; byte metering of its own uplink; an optional 4G module |
| **Guardian** (add-on) | The always-on alarm system and gateway: own cell, LTE and GNSS, tracker, escalation, works with 12 V cut |

The buddy is the base's always-powered node, so it takes the PLCA coordinator role that
ADR-0026 gives "an always-powered node" while parked (open point: hand-over when a guardian
is fitted).

**2. Power states.** *Asleep* (default parked: Pi cut, buddy on); *woken* by ignition, an
alarm input, a schedule, a button or a remote request arriving through any uplink;
*awake*; and an owner setting **always-on** (meant for EVs) in which the Pi stays up and the
buddy still cuts it below a 12 V floor.

**3. Uplinks.** The base brings none of its own. Supported sources:
- existing **in-car Wi-Fi** (head unit, OEM hotspot), a **phone hotspot** (Wi-Fi or USB
  tethering), **home Wi-Fi** when parked;
- **any USB 3G/4G/5G dongle** on the Pi: HiLink-style sticks that appear as an Ethernet NIC
  (ECM/NCM/RNDIS) work with no setup; QMI/MBIM modems through ModemManager;
- options: a **4G module on the buddy** (always-on, slow, PPP), **guardian LTE**, a
  **high-speed gateway** (an OpenWrt 4G/5G router as an Ethernet WAN) and **Starlink**
  (a DevicePack adapter on its local status API; its power feed is a gated relay channel).

**4. Selection, failover and metering.**
- The owner chooses **Auto** (a priority list with failover) or **pins** one source.
  Ostler writes NetworkManager/ModemManager profiles (route metric, autoconnect priority,
  metered flag); it does not route packets itself.
- Each source has a **metered** flag and an optional **monthly budget** and billing day.
  Usage comes from vnStat on the Pi and from byte counters on the buddy and guardian.
- **Alerts at 50/80/100%.** At 100% on a metered source, bulk traffic stops (uploads, OTA,
  clips, tiles); alarm notifications and remote status continue. The owner can override.
- Cellular placement is the owner's trade-off
  ([research §3.5](../references/research/connectivity_uplink.md#35-where-cellular-lives-trade-off)):
  Pi dongle for speed, buddy module for always-on notifications, guardian for alarm grade.

**5. Broker placement.**
- **The buddy runs Espressif's ESP-IDF Mosquitto port** for a **parked minimal set**
  (status/LWT, alarm events, wake requests, the guardian and wake-capable nodes): a TLS
  listener only, about five clients.
- **The Pi runs full Mosquitto** whenever it is awake and is the broker for everything else.
  On waking, the Pi's Mosquitto **bridges** to the buddy on the parked topic patterns only.
- In always-on mode the Pi broker serves everything; the buddy broker stays bridged.
- **Fallback** if the bench fails: parked nodes signal the buddy by wake wire or CAN and the
  buddy wakes the Pi and republishes; or the guardian hosts the parked broker; or always-on.

**6. Remote access tiers** (each opt-in, each passing the same server gate; remote paths
get read-only actions plus arming the software alarm, as in GOALS, and Tier ≥ 2 stays
unreachable remotely, ADR-0027 Confirmation):
- **0. LAN only** — the default.
- **1. Tailscale** — supported as an opt-in OS package on the Pi (BSD-3 client; the owner's
  tailnet or a self-hosted headscale). Not Funnel. Ostler embeds nothing.
- **2. Ostler Cloud** — a product: an outbound tunnel with **end-to-end TLS** to the device
  (the Nabu Casa SniTun model), an MQTT bridge for opt-in state and notifications, and a
  portal to manage cars and uplinks. Never required; the open product stands alone.
- **3. HA Cloud** — through Home Assistant: the car's HA discovery entities reach Nabu Casa's
  remote UI. Read-only buttons only.
- No tier carries a write to the car: writes stay behind the local gates (Parked, explicit
  confirmation, ADR-0020/0024), and nothing remote reaches a vehicle bus.

**7. Local web UIs and provisioning.**
- Wi-Fi **AP and client run on one radio** (same channel) on the Pi and on ESP32 modules.
- Every module (buddy and guardian included) hosts **its own small web page** with status,
  basic controls, network and pairing, and works standalone. Its controls obey the same
  tiers and the module's own interlocks.
- Wi-Fi provisioning uses **Improv Wi-Fi** (BLE and serial), with a **SoftAP captive portal**
  fallback. Wired modules pair as in ADR-0027 §1.7.

**8. Standard security.** Devices: TLS/mTLS with per-device certificates from the vehicle's
local CA (ADR-0021). Brokers: MQTT authentication and per-device ACLs. People: passkeys
(WebAuthn) or passwords set by the owner; no default passwords. Remote tiers add no new
trust: they carry the same HTTPS and MQTT authentication.

**9. Discovery registration.** `_ostler-mod._tcp` is registered with IANA (service name
only). The draft request is in the
[research §6](../references/research/connectivity_uplink.md#6-draft-iana-service-name-registration-the-owner-submits);
the owner submits it.

**10. Matter.** A Matter bridge is a **long-term goal** (unchanged path: through HA today,
a native opt-in bridge later, ADR-0027 §12).

**11. Local-first and privacy.** Everything above works with no uplink. Joining a network
does not make anything leave the device: telemetry, location, cloud bridges and remote
access are each off until the owner enables them. `<vid>` and every uplink, tunnel and
cloud payload exclude the VIN.

## Consequences

- The base bill of materials gains an ESP32-S3 (with PSRAM) buddy; the guardian moves fully
  to the add-on list. GOALS and the hardware research need the same split (follow-up by
  their owners).
- The module-bus message spec gains: the parked topic set, the bridge patterns, the buddy's
  compiled ACL and the wake-and-republish fallback.
- The router-configuration work adds NetworkManager/ModemManager uplink profiles, vnStat,
  an uplink policy API in the server, and Connectivity signals in the VSS overlay.
- Firmware gains a shared "module web page" and Improv component.
- Ostler Cloud's protocol is documented: the SNI tunnel and the MQTT bridge topics.

## Alternatives considered

- **Guardian in the base.** Rejected by the owner: a base without a SIM or second battery
  is cheaper; the guardian is for those who want alarm-grade.
- **A built-in modem in the base.** Rejected: people already have hotspots, car Wi-Fi and
  dongles; a SIM in the base forces a subscription.
- **Broker only on the Pi.** Rejected as the default: nothing to publish to while parked
  unless the Pi stays on. Kept for always-on mode.
- **Arduino ESP32 brokers** (PicoMQTT, sMQTTBroker, TinyMqtt). Rejected: MQTT 3.1.1, QoS 0,
  no TLS, no retained/will in some.
- **mwan3 on the Pi.** Rejected: OpenWrt-only. Kept inside the optional gateway.
- **Tailscale Funnel, ZeroTier as default, or embedding `tsnet`.** Rejected: public exposure;
  licence mix; Go in the stack against ADR-0002.
- **Ostler Cloud as the only remote path.** Rejected by the owner and by GOALS.
- **ESP-IDF unified provisioning or WiFiManager as the standard.** Reference only: vendor app
  or Arduino-only.

## Confirmation

On the bench, with the dev kit (Pi, buddy board, one T1S or Wi-Fi module):
- **Parked broker:** five mTLS clients on the buddy for 24 h with no reboot or leak; MQTT 5
  CONNECT accepted (else the fallback applies); a parked alarm event reaches the Pi broker
  within **5 s** of the Pi waking, via the bridge.
- **Wake:** a remote wake request through a phone hotspot and through a buddy 4G module brings
  the Pi to a served UI within the wake budget set in the module-bus spec.
- **Failover:** with Auto, pulling the preferred uplink moves the default route to the next
  one within **30 s**, and back when it returns.
- **Metering:** a test budget triggers the 80% and 100% alerts; at 100% on a metered link an
  OTA download is refused and an alarm notification still goes out.
- **Remote access:** with Tailscale enabled the UI is reachable on the tailnet with the same
  login; with it disabled nothing listens beyond the LAN. A Tier ≥ 2 action is refused on
  every remote tier.
- **Privacy:** a capture on each uplink during a session shows no VIN and no outbound traffic
  until an opt-in is set.
- **Wi-Fi:** the Pi keeps its AP clients while joining a hotspot (same channel), or the bench
  records that a second radio is needed.
- **Provisioning:** a fresh ESP32 module joins Wi-Fi by Improv over BLE from Chrome, and by the
  captive portal from iOS Safari.
</content>
</invoke>
<invoke name="Bash">
<parameter name="command">cd /home/user/ostler && grep -n "Tier\|remote" decisions/adr-0018-ui-architecture-decisions.md | head -20