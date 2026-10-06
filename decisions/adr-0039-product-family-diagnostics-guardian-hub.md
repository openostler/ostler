---
title: "ADR-0039 — Product family: Ostler Diagnostics, Guardian and Hub (raw tap, USB-IP link, setup mode, uplinks, hub-only wake, u-blox placement)"
area: decisions
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [references/research/product_family.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0037-role-holders-and-handover.md, references/research/hardware.md, references/research/connectivity_uplink.md, references/research/power_states.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  Proposed, from the owner's direction of 2026-10-06. Renames ADR-0032's tiers: "Ostler Lite" becomes Ostler Diagnostics (the OBD-port node, standalone with a phone or plugged into a hub), and the brain product becomes Ostler Hub; with Ostler Guardian they form the family; "node" and "brain" stay the internal terms; the architecture of ADR-0032 stands. Records: hardware-agnostic boards (WiCAN Pro as a CAN-only board profile, since its K-line sits behind an interpreter IC; a discrete K-line transceiver for K-line cars); two node outputs, decoded VSS and an MCU-timestamped raw tap batched over MQTT 5, scrubbed on the node, recorded on the hub, with lab send-requests through the node gate; raw serial over the network rejected; the node-to-hub link is USB-NCM near the hub or 10BASE-T1S elsewhere, same IP and topics; standalone uplink is the official 4G module, Wi-Fi or a USB dongle from a tested list; with a hub the hub is uplink manager; setup mode is a Wi-Fi AP plus BLE Improv with a helper (pair and owner, uplink, pack, first scan) and hub adoption; a hub-only box wakes from its power board, with no separate buddy; the 10 Hz u-blox sits on the Diagnostics node. Lists the "Lite" wording sweep, bench tests and open questions.
---

# ADR-0039 — Product family: Ostler Diagnostics, Guardian and Hub

- **Date:** 2026-10-06
- **Status:** proposed (draft for the owner; nothing here is accepted until the open
  questions are answered). **Supersedes in part**
  [ADR-0032](adr-0032-one-node-optional-brain.md) §1 (the names "Ostler Lite" and "Ostler"
  only; the architecture stands) and, if accepted, amends ADR-0026, ADR-0027 and ADR-0028
  (see [Relation to other ADRs](#relation-to-other-adrs)). Evidence:
  [product family research](../references/research/product_family.md).

## Context

- The owner (2026-10-06): rename "Ostler Lite" to **Ostler Diagnostics**, the OBD-port node,
  standalone with a phone or plugged into a brain or hub. The family is **Ostler Diagnostics,
  Ostler Guardian and Ostler Hub/Brain**; "node" stays the internal term. It is
  hardware-agnostic, with the MeatPi WiCAN Pro as a candidate reference board (check
  K-line). Standalone it uses a USB 4G dongle (keep a tested list) or Wi-Fi; with a hub it uses
  the hub's or the guardian's uplink (the uplink-manager role). Setup mode is a Wi-Fi AP and
  BLE with a setup helper (Improv/SoftAP per ADR-0028): pair and set the owner, pick an uplink,
  choose a pack, first scan. Sniffing uses a timestamped raw-frame tap to the hub; the gate and
  timing stay on the node.
- Also agreed: **raw serial over the network is rejected** (K-line init timing; it would move
  the gate to the brain). The node gives two outputs, decoded VSS and a raw stream timestamped
  on the MCU; the hub records it and runs the Python lab; the hub **asks** the node to send and
  never sends itself. The link is USB carrying IP near the hub, or T1S/Ethernet when the hub
  is elsewhere, with the same IP/MQTT and topics either way. A hub-only box still needs a wake
  source.
- ADR-0032 §1 named the tiers "Ostler Lite" and "Ostler"; ADR-0032's proposed amendment left
  the u-blox placement open.

## Decision drivers

- Names people understand: what the box does, not a tier.
- The gate, init timing and keep-alive stay on the node (ADR-0032 §2, CONSTITUTION).
- One message model on every link (ADR-0027 §1, §5); no new trust (ADR-0026).
- Privacy by default: identity data is scrubbed before it leaves the node (ADR-0036).
- Setup works with a phone alone, offline, with no default passwords (ADR-0028 §8).
- Reuse open standards and Espressif components (ADR-0017, ADR-0025).

## Decision

**1. Product names.**

| Public name | Internal term | What it is |
|---|---|---|
| **Ostler Diagnostics** | node (`variant: diag-port`) | The OBD-port node: car I/O, decode to VSS, the transmit gate, the raw tap, timing, parked broker, hub power and wake. Standalone with a phone, or plugged into a hub |
| **Ostler Guardian** | node (`variant: guardian`) | ADR-0032 §5 unchanged: hidden, battery-backed, no outputs |
| **Ostler Hub** | brain | ADR-0032 §3 unchanged: compute and network, never touches the car |

"Node" and "brain" stay the terms in code, topics, manifests and ADRs. ADR-0032 §1's table
reads "Ostler Diagnostics" for "Ostler Lite" and "Ostler Diagnostics + Ostler Hub" for
"Ostler". Public name of the hub: open question 1.

**2. Hardware-agnostic, with board profiles.** Any board meeting the minimum (ESP32-S3 with
PSRAM; a K-line transceiver on an S3 UART for K-line cars; TWAI CAN; protected 12 V input;
ignition sense; a brain-power output) is a Diagnostics node through a board profile (ADR-0032
proposed amendment B). The **WiCAN Pro** is a **CAN-only board profile**: its K-line goes
through an STN-compatible interpreter IC, so the node cannot own K-line timing or timestamp
bytes on it; generic K-line OBD reads through the interpreter may be offered as Read, Tier 0,
never gated K-line transmits. The K-line reference is an ESP32-S3 with a discrete
transceiver (dev build now, our own board later).

**3. Two outputs: decoded VSS and the raw tap.**
- Raw tap records carry an MCU monotonic µs timestamp (mapped to shared UTC by periodic time
  records), a sequence number, bus id, direction, protocol, flags and bytes, plus events for
  init, keep-alive, gate decisions, overflow, time and link.
- Transport: **MQTT 5 with batching** (binary batches on
  `ostler/v1/<vid>/<node>/tap/<session>/data`, session header retained on `…/meta`), over the
  same broker, mTLS and ACLs. A separate TCP stream is the fallback only if the bench fails.
- The node buffers in a PSRAM ring and reports losses. The hub records into the logbook and
  exports pcapng.
- **Identity scrub on the node** (ADR-0036 §2): the node frames messages before emitting and
  replaces declared identity replies with the placeholder unless the install-level option is
  on; exports always scrub.
- **Send-requests:** the hub asks on `…/lab/req` with a grant; the node gate classifies,
  serializes and answers on `…/lab/resp`. The hub never transmits; the gate never hands over.
- **Rejected:** raw serial (or K-line bytes) tunnelled over the network to a hub-side driver.

**4. The node-to-hub link.** **USB-NCM** (CDC-NCM, ECM fallback; ESP32-S3 device via
esp_tinyusb) when the hub is within a USB cable of the port; **10BASE-T1S** (ADR-0026) when
the hub is elsewhere; Ethernet on prototypes. IP, MQTT, VSS and raw-tap topics are identical on
each. The USB link is its own routed subnet (ADR-0027 §3). The node is always powered from the
car; hub VBUS is never its only feed. A USB-linked node cannot host a dongle (one OTG port).

**5. Standalone uplink.** Default: the **official 4G module** on the Diagnostics board (an IoT
SIM). Also Wi-Fi (car, hotspot, home). Also a **USB 4G dongle** by class: PPP/AT over CDC-ACM
(`iot_usbh_modem`), ECM (`iot_usbh_ecm`) or RNDIS (`iot_usbh_rndis`); QMI/MBIM sticks only on a
hub. A **tested-dongle list** in the firmware repo records what works.

**6. Uplink with a hub.** The hub holds the uplink-manager role (ADR-0037, brain → node); the
node's 4G module or Wi-Fi is one more source in the owner's order and the node's fallback when
the hub sleeps. A guardian keeps its SIM for the alarm path.

**7. Setup mode and helper.** First boot, factory reset or a long press starts setup mode:
a Wi-Fi AP with a per-device password (label and QR), BLE Improv, and Improv serial on USB. It
times out, offers no car actions and transmits nothing to the car. The helper (Network core
app) runs: **pair and set the owner** (physical authorisation) → **uplink** → **pack** (detected
Parked only, or chosen; signed) → **first scan** (Read, Tier 0, snapshotted). Improv's redirect
URL hands over to the node page. **The hub adopts** devices advertising `_ostler-mod._tcp` with
`pr=0`, with the owner on the hub and a physical press on the device (or the owner's paired
phone for a node already owned); then its CA issues the certificate. No silent takeover.

**8. Hub-only wake.** A hub with no Diagnostics node wakes from its **power board**: ignition
(for example CarPiHAT PRO 5), an RTC schedule (Pi 5 `wakealarm`, Witty Pi 5) and a
low-voltage cut. It has no remote wake, parked broker or alarm. There is **no separate
buddy**: a Diagnostics node or a Guardian adds those. Wake semantics: [ADR-0040](adr-0040-power-states-and-wake.md) (draft).

**9. u-blox placement (resolves ADR-0032's pending question, proposed).** The 10 Hz u-blox
sits on the **Diagnostics node** (ADR-0032 amendment A1 as proposed); a USB u-blox on the hub
is the hub-only and bench option; the guardian keeps its 1 Hz modem GNSS.

## Wording sweep (rename "Lite" later; files not edited here)

Checked by `grep -w Lite` on 2026-10-06 (third-party product names such as "VCDS-Lite" and
"FORScan Lite" in `references/research/ui/` are excluded):

| File | Lines |
|---|---|
| `README.md` | 9, 39 |
| `GOALS.md` | 9, 30, 144, 152, 204 |
| `decisions/CLAUDE.md` | 18, 25, 36 (and an entry for this ADR) |
| `decisions/adr-0014-ostler-handles.md` | 14, 104 (product family amendment) |
| `decisions/adr-0018-ui-architecture-decisions.md` | 104 |
| `decisions/adr-0021-local-https-on-the-device.md` | 14, 72 |
| `decisions/adr-0026-module-bus-10base-t1s.md` | 14, 155 |
| `decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md` | 9, 57, 100, 127, 128, 155, 159 |
| `decisions/adr-0032-one-node-optional-brain.md` | 2, 9, 50, 115, 121, 128, 219, 240 (banner pointing here) |
| `decisions/adr-0037-role-holders-and-handover.md` | 67, 218 |
| `decisions/adr-0038-mesh-car-to-car-and-off-grid.md` | 62, 147 |
| `references/vision.md` | 9, 106, 118, 162, 234, 302, 305 |
| `references/research/addons_catalogue.md` | 9, 21, 119, 176 |
| `references/research/connectivity_uplink.md` | 44, 180 |
| `references/research/ecosystem_architecture.md` | 9, 272 |
| `references/research/features_backlog.md` | 53 |
| `references/research/hardware.md` | 157, 158 |
| `references/research/power_states.md` | 197 (another researcher's draft) |
| `specs/2026-10-06-accounts-sharing-design.md` | 9, 44, 47, 208, 339, 349 |
| `specs/2026-10-06-app-model-design.md` | 9, 124, 247, 250, 352, 439, 493 (working tree; 439 and the changelog shift come from the [ADR-0040](adr-0040-power-states-and-wake.md) amendment in progress); the `product` value `lite` at 93 and 377 |
| `specs/2026-10-06-kline-profiles-detection-design.md` | 9, 323, 377 |
| `specs/2026-10-06-platform-direction-design.md` | 9, 36, 185 |
| `specs/2026-10-06-ui-architecture-design.md` | 186, 254, 258 (254 and 258 from the [ADR-0040](adr-0040-power-states-and-wake.md) amendment in progress) |
| `INDEX.md` | regenerated by `build_index.py`, never hand-edited |

`ostler-firmware` has no "Lite" mentions. Line numbers drift: re-run the grep when the sweep is done. Accepted ADRs get a banner, not an edit.

## Confirmation

**Simulated (no hardware):**
- Raw-tap codec: records and events round-trip; `seq` gaps and `overflow` are detected;
  `t_us` maps to UTC between `time` marks; pcapng export opens in Wireshark (CAN) and keeps
  every K-line byte and gap.
- Scrub: with defaults, a session containing a KWP `1A` reply and an OBD `09 02` reply carries
  only the placeholder and the `scrubbed` flag; with the option on, every export still scrubs.
- Send-requests: an unknown service, a write without a matching grant, and any request while
  Moving are refused by the gate model; a read on the allowlist passes.
- Setup: a node in setup mode refuses every car action; no shared default credential exists
  in any image.

**Bench:**
- **USB-NCM:** an ESP32-S3 node enumerates as NCM on Raspberry Pi OS (Pi 5) with no driver
  install, gets addresses and is found by mDNS; sustained throughput recorded (target ≥ 4 Mbit/s).
- **Raw tap load:** a saturated 500 kbit/s CAN bus for 10 minutes, over USB-NCM and over T1S
  (or Ethernet stand-in), reaches the hub recorder with no `seq` gap; K-line init and a
  seed-key session on the D2 show per-byte timestamps within ±50 µs of a logic analyser (U).
- **Gate:** a lab read requested from the hub runs on the node with the node's own timing and
  keep-alive; pulling the link mid-session leaves the node's session and gate state intact.
- **Dongles:** each list entry passes attach, connect, 10-minute transfer and reconnect after a
  node reboot on the ESP32-S3; current measured.
- **Setup:** a fresh node completes the helper from Chrome over BLE Improv and from iOS Safari
  over the AP; the hub adopts it with a physical press.
- **Hub-only wake:** ignition and an RTC alarm each boot a Pi 5 hub; parked draw measured.
- **WiCAN Pro:** the schematic confirms K-line reaches only the interpreter, or our K-line
  profile runs on it after all (then §2 is revisited).

## Consequences

- ADR-0032 gains a "renamed by ADR-0039" banner; the wording sweep above runs as one change by
  the files' owners.
- The module-bus message spec gains the `tap/` and `lab/` topics, the batch content type and the
  session header; the capability manifest gains `tap` (buses, protocols, max rate) and `links`.
- `ostler-firmware` gains `docs/specs/raw-tap.md` (format, USB-NCM link, setup mode, dongle list).
- The UI spec's Network page lists USB among "reached via", and the helper becomes a Network-app
  flow; the platform gains a raw-tap recorder and pcapng exporter beside the logbook.
- The hardware research's WiCAN Pro rows change from "always-on K-line" to "CAN-only profile".

## Alternatives considered

- **Raw serial over the network** (RFC 2217 or a TCP UART): rejected; K-line init and P-timings
  break over a network, and the gate would move off the node.
- **One MQTT message per frame:** rejected; overhead and broker load at CAN rates.
- **A separate TCP stream as the default:** rejected for v1; a second protocol, port and trust
  path. Kept as the fallback.
- **Scrub on the hub at write:** rejected; scrubbing on the node keeps identity bytes off the
  link by default.
- **WiCAN Pro as the K-line reference:** rejected; the interpreter owns timing.
- **A buddy MCU for hub-only boxes:** rejected; the Guardian already is the small always-on
  device, and power boards cover ignition and schedule.
- **u-blox on the hub:** rejected as the default; absent standalone and asleep when parked.

## Relation to other ADRs

- **ADR-0032:** §1 names superseded; §3's "Link: … Ethernet, USB or UART on dev kits" becomes
  USB-NCM as a product link and UART dropped; §2, §4–§16 stand.
- **ADR-0026:** adds USB-NCM as a point-to-point node-to-hub link beside T1S (an amendment).
- **ADR-0027:** §2's segment table gains "Node link: USB-NCM, its own subnet"; §5's topics gain
  `tap/` and `lab/`.
- **ADR-0028:** §3 dongles now also on the node (by class); §7 provisioning gains the helper and
  adoption; "buddy" stays retired for hub-only boxes.
- **ADR-0036:** applied on the node for the raw tap; unchanged otherwise.
- **ADR-0037:** the uplink-manager row stands; a USB-linked node has no dongle.

## Open questions for the owner

1. **Ostler Hub or Ostler Brain** as the public name? And `lite` → `diagnostics` in the
   app-model `product` value?
2. Accept MQTT 5 batching for the raw tap (100 ms / 8 kB), with TCP only as a fallback?
3. Raw-tap bytes the node cannot frame (a foreign tool's unknown protocol): drop them from
   exports, or never export such sessions?
4. Default USB power: data-only, or hub VBUS ORed in as a second feed?
5. Is the official 4G module on every Diagnostics board, or a fitted option?
6. Accept "no buddy" for hub-only boxes (power board wake, Guardian for remote wake)?
7. Accept the u-blox on the Diagnostics node, closing ADR-0032's GPS question?
