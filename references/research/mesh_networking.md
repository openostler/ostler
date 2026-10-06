---
title: "Mesh networking — car-to-car, base/camp and off-grid (batman-adv, Babel, Meshtastic, MeshCore, Reticulum, Styrene, Ratspeak)"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [decisions/adr-0017-open-standards-first.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, references/research/addons_catalogue.md, references/research/ecosystem_architecture.md]
summary: >
  Live research (2026-10-06) behind draft ADR-0038. Placement is fixed by the owner: the in-car network stays routed T1S/Ethernet with no mesh; a mesh only links car to car, to a base or camp, or off-grid, as its own subnet bridged at the brain or gateway, and it is always a remote path (Read and alerts only). Compares batman-adv/802.11s (GPL-2.0 kernel module, L2, MTU and broadcast cost, Linux only), Babel (RFC 8966, babeld MIT, routed), Meshtastic (GPL-3.0 firmware and protobufs, largest LoRa user base, managed flooding, ESP32/nRF52, serial/BLE/TCP protobuf API and MQTT), MeshCore (MIT firmware, learned paths, repeaters only relay, closed official apps), Reticulum and LXMF ("Reticulum License": MIT plus no-harm and no-AI-training clauses; Python; author stepped back, GitHub is a mirror), Styrene (MIT Rust RNS/LXMF stack, solo, fleet exec/reboot over LXMF, one root secret) and Ratspeak (AGPL-3.0, built on Reticulum, not a new protocol; alpha). Recommends a Meshtastic-compatible LoRa add-on first behind a thin GPL-3 VSS bridge, Babel rather than batman-adv if a Wi-Fi IP mesh is ever wanted, and bench tests of MeshCore and the Reticulum family for the richer social layer. Includes a bridge sketch with topics, rate limits and privacy defaults.
---

# Mesh networking: car-to-car, base/camp and off-grid

Research for [ADR-0038](../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md) (accepted 2026-10-06).
Facts were checked live on **2026-10-06** from each project's repository (licence file,
last commit, latest tag) and docs. **(U)** means unverified. Nothing here is copied from
the sources; it is paraphrased with links.

## 1. Placement (owner, 2026-10-06; not reopened here)

- **Inside the car there is no mesh.** The in-car network stays the routed T1S and Ethernet
  design of [ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md) and
  [ADR-0027](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md).
- **A mesh links outward only:** car to car (convoys, group rides), car to a base or camp,
  and off-grid groups. It is **its own subnet or its own non-IP network**, joined to the
  car at the brain or a gateway, firewalled like any uplink.
- **A mesh is a remote path** ([ADR-0033 §6](../../decisions/adr-0033-action-categories-and-approvals.md)):
  Read and alerts go out, messages and peer positions come in as data. **No command from a
  mesh ever reaches the car.** Remote arm and disarm (the ADR-0033 amendment) is not offered
  over a mesh at all in this proposal (see ADR-0038 open questions).

## 2. Comparison

| | batman-adv / 802.11s | Babel | Meshtastic | MeshCore | Reticulum + LXMF | Styrene | Ratspeak |
|---|---|---|---|---|---|---|---|
| **Kind** | L2 Wi-Fi IP mesh | L3 routing protocol | LoRa text, position, telemetry mesh | LoRa mesh, lighter | Crypto network stack over any link; LXMF messaging | Platform on RNS/LXMF (Rust) | Client and MCU firmware on RNS/LXMF |
| **Licence (current file)** | GPL-2.0 (kernel module) | MIT (babeld); RFC 8966 | GPL-3.0 (firmware, protobufs, Python lib) | MIT (firmware); official apps and T-Deck firmware closed | "Reticulum License": MIT plus two use restrictions; RNode firmware GPL-3.0; protocol public domain | MIT (styrene-rs, identity); Apache-2.0 (nex); Python daemon archived | AGPL-3.0-or-later |
| **ADR-0025 verdict** | Run as an OS program only; no code reuse (GPL-2.0-only) | Free to use | Separate program, or a marked GPL-3 module/pack | Copy freely | Separate unmodified program only; never in core | Reference and bench only until provenance is clear | Separate program, or a marked AGPL module; never core |
| **Activity (live)** | v2026.3, 2026-08-31 | babeld 1.14, 2026-06-20 | 2.8.1 alpha 2026-09-28; 2.7.26 beta 2026-06-23; commits today | repeater 1.17.1, 2026-08-14; 3,800+ stars | RNS 1.5.5, 2026-09-29; mirror only, no support | styrene-rs last commit 2026-09-03; 1,119 commits | rsReticulum 2026-09-17; rsDeck 2.0.2 beta |
| **Maturity** | Mature (Freifunk, OpenWrt) | Mature, IETF standard | Mature, very large user base | Young but fast-growing | Mature protocol, bus factor one | Early, solo, not audited | Alpha |
| **Runs on ESP32?** | No (Linux) | No known port (U) | Yes (ESP32, nRF52, RP2040, Linux) | Yes (ESP32, nRF52, RP2040) | Python needs Linux/Android; RNode firmware on ESP32 is a radio, not a stack; microReticulum (Apache-2.0) is a partial C++ port | Rust "constrained hardware" target claimed; ESP32 not confirmed (U) | Yes: T-Deck Plus, Cardputer Adv, T-Pager (ESP32-S3 handhelds) |
| **Interop with radios people own** | Wi-Fi only | Any IP link | Best: most off-the-shelf LoRa handhelds ship it | Same radios, different firmware; no Meshtastic interop | RNode-flashed LoRa boards; no Meshtastic interop | RNS-compatible (claimed) | RNS-compatible (claimed), no Meshtastic interop |
| **Routing, congestion** | Floods broadcast and multicast (mDNS) across the mesh; ≥1532 B MTU or slow fragmentation | Distance-vector; multicast stays per link | Managed flooding, hop limit 3 (max 7); next-hop for DMs since 2.6; intervals scale above 40 nodes; EU868 10 % duty cycle | Flood once, then the learned path; only repeaters relay; channels always flood; up to 64 hops | Announce-based path discovery; works from ~5 bit/s with a 500 B MTU | As RNS | As RNS; LoRa presets ~0.3–22 kbit/s, default ~1 kbit/s |
| **Privacy, metadata** | Plain L2; MACs visible | IP addresses visible | Default channel key is public; node IDs and positions broadcast; per-channel position precision; PKI DMs | Signed adverts with name and position (user-triggered) | No source address in packets (initiator anonymity) | One root secret links all keys (no anonymity by design) | As RNS |
| **Identity fit** | None (use our certs on top) | None | Own node key; never ours | Own key pair | Own RNS identity | Single root secret: must never hold ours | Own RNS identity |
| **Power** | Wi-Fi radio always on (high) | As the link | Low (LoRa); radio sleeps well on nRF52 | Low | Low on LoRa | As RNS | Low on LoRa |
| **Thin VSS bridge?** | IP: MQTT as usual | IP: MQTT as usual | Yes: serial/BLE/TCP protobuf API or MQTT JSON | Yes: companion protocol (BLE/USB/Wi-Fi) or KISS | Yes on the brain (Python rnsd + LXMF) | Heavier: a platform | Heavier: an app |

## 3. Per-project notes

### 3.1 batman-adv and 802.11s (L2 Wi-Fi IP mesh)

- batman-adv is a Linux kernel module (GPL-2.0, latest tag v2026.3 on 2026-08-31) that makes
  the whole mesh look like one switch; it runs over 802.11s, ad-hoc or wired links and is
  packaged for OpenWrt ([kernel docs](https://kernel.org/doc/Documentation/networking/batman-adv.rst),
  [mirror](https://github.com/open-mesh-mirror/batman-adv)).
- **MTU:** its header pushes a 1500-byte frame to about 1528–1532 bytes; drivers that cannot
  raise the MTU fall back to fragmentation, which is slow and loss-prone
  ([fragmentation](https://open-mesh.org/projects/batman-adv/wiki/Fragmentation)).
- **Noise:** as one L2 domain it carries every car's broadcast and multicast, including
  mDNS, which is exactly what ADR-0027 rejected for the in-car network. If used, it must
  be a **separate subnet**, routed and firewalled at the brain, with no mDNS reflection.
- **ESP32 cannot run it.** Espressif's own ESP-WIFI-MESH is a different, tree-shaped
  mesh and does not interoperate with 802.11s (U on any current bridge).
- Licence: we would only run the OS's kernel module, never combine its code (ADR-0025).

### 3.2 Babel (routed)

- Babel is a distance-vector protocol for wired and wireless meshes, standardised as
  RFC 8966. The reference daemon babeld is MIT-licensed, last released as 1.14 on
  2026-06-20 ([repo](https://github.com/jech/babeld)), and is in OpenWrt.
- It keeps the routed model of ADR-0027: each car stays its own subnet and announces a
  prefix; multicast stays on its link. It runs over plain 802.11s mesh points or ad-hoc
  Wi-Fi without batman-adv.
- **Verdict:** if a Wi-Fi IP mesh between cars or to a base is ever wanted (shared uplink,
  bulk sync at camp), prefer Babel over batman-adv. Linux only (brain or a travel router).

### 3.3 Meshtastic

- **Licence:** firmware, protobufs and the Python library are all GPL-3.0 (live licence
  files). **Trademark:** the name may be used secondary to our own brand with a link and a
  non-affiliation note; using it on hardware or enclosures needs a written licence; the
  "M-PWRD" mark is offered for community projects ([legal](https://meshtastic.org/docs/legal/licensing-and-trademark/)).
- **Activity:** commits on the day of this check; 2.8.1 is an alpha (2026-09-28, release
  notes mention packet signing); 2.7.26 is the latest beta (2026-06-23).
- **Hardware:** ESP32, nRF52, RP2040/RP2350 and Linux; the largest base of off-the-shelf
  LoRa radios (T-Beam, Heltec, RAK, T-Deck and others). JSON over MQTT is ESP32-only.
- **Routing:** managed flooding with a hop limit of 3 by default and 7 at most; next-hop
  routing for direct messages since 2.6; position and telemetry intervals stretch once a
  mesh has more than 40 nodes; EU868 radios stop at the 10 % hourly duty cycle
  ([algorithm](https://meshtastic.org/docs/overview/mesh-algo/),
  [LoRa config](https://meshtastic.org/docs/configuration/radio/lora/)). Busy public meshes
  congest; a convoy should use its own channel.
- **Privacy:** the default primary channel uses a publicly known key; positions are per
  channel from 0 (off) to 32 bits (full), with 13 bits about ±3 km and 16 bits about 364 m
  ([channels](https://meshtastic.org/docs/configuration/radio/channels/)). The public MQTT
  server is zero-hop and caps position precision.
- **APIs for a thin bridge:** ToRadio/FromRadio protobufs over serial/USB, BLE or TCP
  (port 4403), framed with two start bytes and a length; a `want_config_id` handshake
  downloads the node database ([client API](https://meshtastic.org/docs/development/device/client-api/)).
  Or MQTT: uplink and downlink per channel, protobuf or JSON topics under `msh/…`
  ([MQTT](https://meshtastic.org/docs/software/integrations/mqtt/)).
- **Fit:** best reach for bikers and off-roaders, who already own these radios. Code built
  from the protobufs is GPL-3, so the bridge is a separate GPL-3 program or pack.

### 3.4 MeshCore

- **Licence:** MIT ([repo](https://github.com/meshcore-dev/MeshCore)). Its FAQ says the
  firmware is open except the T-Deck firmware and the official mobile apps; the T-Deck
  build sells a registration key for extras.
- **Routing:** the first message floods; the delivery report carries the path, which the
  sender stores and embeds next time, so only the named repeaters relay. Group channels
  always flood; repeater owners can cap flood hops. Companion devices never repeat. Up to
  64 hops with one-byte path hashes (fewer with longer hashes, from 1.14).
- **APIs:** a companion protocol over BLE, USB or Wi-Fi (marked as still in development,
  2026-03) with JS and Python libraries, and a KISS modem mode.
- **Fit:** less airtime than Meshtastic and a clean licence, but a smaller user base and
  no interop with Meshtastic. Repeaters can be managed remotely over LoRa: any Ostler
  build must leave that off.

### 3.5 Reticulum (RNS) and LXMF

- **Licence (checked):** no longer plain MIT. The current LICENSE in both RNS and LXMF is
  the **"Reticulum License"**: MIT terms plus two restrictions: no use in a system able to
  purposefully harm people, and no use in building AI or machine-learning training data.
  The README says the protocol itself was dedicated to the public domain in 2016. RNode
  firmware is GPL-3.0. Not an OSI licence: under ADR-0025 we run it as a separate,
  unmodified program and never put it in core or the commercial build.
- **Project state:** the GitHub repo is now a **public mirror**; the author has stepped
  back from all public support, with occasional releases (RNS 1.5.5 on 2026-09-29, LXMF
  1.2.0). Bus factor of one.
- **Upstream's stance on ports:** both READMEs warn that machine-generated
  reimplementations derived from the RNS code or docs are, in the author's view,
  infringing, and that licence grants they claim are void. That makes the provenance of
  third-party ports a **doubtful-grant** question under ADR-0025 until checked.
- **Runtime:** Python 3 on Linux, macOS, Windows, Android (Termux) and OpenWrt; RNode
  boards (ESP32, nRF52 and others) are radios driven by a host. microReticulum is an
  Apache-2.0 C++ port for ESP32 and nRF52 with transport but no LXMF yet
  ([repo](https://github.com/attermann/microReticulum)).
- **Strengths:** works from about 5 bit/s with a 500-byte MTU, end-to-end encryption, no
  source addresses, store-and-forward messaging (LXMF). The richest fit for a social layer
  between brains and phones; not for the node.

### 3.6 Styrene

- A **solo** platform on RNS/LXMF ([site](https://mesh.styrene.io),
  [org](https://github.com/styrene-lab)): the Rust stack styrene-rs (MIT, 1,119 commits,
  last 2026-09-03, "not yet independently audited"), styrene-identity (MIT, 0.3.2), nex
  (Apache-2.0; package manager and cold-start provisioning for NixOS and nix-darwin) and
  NixOS edge configurations. The Python daemon styrened was archived on 2026-05-20.
- **Lineage:** its UPSTREAM note traces code to earlier Rust RNS and LXMF ports; see the
  upstream stance in §3.5.
- **Fleet ops:** `styrene fleet exec` runs shell commands and `fleet reboot` reboots nodes
  over LXMF, authorised by the operator's Ed25519 identity and an RBAC policy
  ([fleet guide](https://github.com/styrene-lab/styrene-rs)). On anything Ostler ships this
  must be compiled out or unreachable: a mesh is a remote path and a shell is far beyond
  Read.
- **Identity:** one 32-byte root secret derives every key (Git, SSH, TLS, agents) by HKDF;
  the project notes derived keys are linked and give no anonymity. Our device keys,
  pairing keys and passkeys (ADR-0029, ADR-0032) must never be derived from, or stored as,
  a Styrene root.
- **Overlap:** NixOS images and nex overlap our brain image and containers (ADR-0032
  §11); we would not adopt them. At most styrene-rs runs as a container on the brain.

### 3.7 Ratspeak

- **Not a new protocol.** Its site and repos describe a client for Reticulum and LXMF
  (with LXST for voice) on desktop, Android and iOS (TestFlight), and firmware for the
  T-Deck Plus (rsDeck), Cardputer Adv (rsCardputer) and T-Pager (U: firmware repo not
  checked) ([org](https://github.com/ratspeak), [site](https://ratspeak.org)). The
  "transport-agnostic" claim is Reticulum's own property.
- **Licence:** AGPL-3.0-or-later. **Maturity:** alpha; rsReticulum is a from-scratch Rust
  RNS (416 commits) pinned to RNS 1.4.2, interface support alpha, outside PRs paused;
  rsDeck 2.0.2 is beta and T-Deck-Plus-only.
- **LoRa:** rsDeck presets span about 0.34–22 kbit/s, default about 1 kbit/s. No routing
  claims beyond RNS; **no Meshtastic interop**.
- **On our nodes?** The MCU firmware targets specific ESP32-S3 handhelds. Putting AGPL code
  in node firmware would break the commercial build (ADR-0012); a separate add-on or a
  user's own handheld is the only fit.

## 4. Recommendation

1. **First: a Meshtastic-compatible LoRa add-on** for reach (bikers, overlanders, camps),
   behind a **thin VSS bridge** (§5). Step one uses any radio the owner already has (USB,
   BLE or TCP); step two is our own add-on with stock Meshtastic firmware on a LoRa board
   joined to the node over UART or T1S. The bridge is a separate GPL-3 program or pack;
   core and the node firmware never link Meshtastic code. Name it "works with Meshtastic"
   per the trademark rules.
2. **Richer car-to-car layer (social app, ADR-0029 P4):** bench-test **MeshCore** (MIT,
   learned routes) and **Reticulum/LXMF** (run as an unmodified program on the brain).
   Treat **Styrene** and **Ratspeak** as references until their provenance and maturity
   settle; neither is a dependency.
3. **Wi-Fi IP mesh:** only if a use appears (shared uplink, camp sync): **Babel** on the
   brain or a travel router, its own subnet. batman-adv only behind the same routed edge.
4. **Never:** a mesh inside the car, mesh code in the node's gate firmware, or any mesh
   input reaching an action topic.

## 5. VSS bridge sketch (for the module-bus message spec)

The bridge is an add-on device under the module contract (ADR-0027 §9), id `mesh-<n>`.
Its manifest declares only Read outputs and data inputs; **no actions**.

| Direction | Topic (MQTT 5 in the car) | Content | Mesh side (Meshtastic) |
|---|---|---|---|
| Out | subscribes `ostler/v1/<vid>/<node>/state/Vehicle.CurrentLocation.*` | Latitude, longitude, heading, speed | Position packet on the Ostler channel, at the channel's precision |
| Out | subscribes the Security alarm-state signal (named in the message spec) | Armed, disarmed, triggered, with cause | Short text, plus a compact private-app payload for Ostler peers |
| Out | subscribes `ostler/v1/<vid>/+/event/alert` with an owner-chosen allowlist | Alert class, severity, time | Short text ("Ostler: tilt alarm 14:02") |
| In | publishes `ostler/v1/<vid>/mesh-1/in/text` | Peer id, channel, text, time, SNR | Text messages |
| In | publishes `ostler/v1/<vid>/mesh-1/in/position/<peer>` | Peer position as received | Position packets |
| In | publishes `ostler/v1/<vid>/mesh-1/in/alert` | A peer's alert, tagged untrusted | Ostler private-app alerts |
| Health | `ostler/v1/<vid>/mesh-1/state/link` | Radio, channel utilisation, airtime, peers heard | Device telemetry |

- **Broker ACL:** the bridge may publish only under its own `mesh-<n>/in/` and `state/`
  topics; it may never publish to any action, grant or command topic. Inbound data is shown
  and recorded, never parsed as a request.
- **Rate limits (defaults):** position every 10 min parked and 2 min moving, never below
  60 s, and only on change; alarm state on change, at most one per 30 s; alerts debounced
  per class (one per 5 min, ten per hour); hop limit 3; the bridge also obeys the radio's
  duty-cycle limit and drops position before alerts.
- **Privacy defaults:** position sharing **off** until the owner opts in per channel;
  when on, **coarse** (13 bits, about ±3 km) unless a live ride raises it, mirroring
  ADR-0029 §8; never the default public channel for positions (a private channel with a
  random key); no VIN, `<vid>`, plate or account name in any mesh field; the radio's own
  MQTT uplink off; nothing from the mesh forwarded to the internet unless opted in.
- **Identity:** the radio's node key is the mesh identity. It is never derived from, or
  used as, an Ostler device key, pairing key or passkey. Pairing a radio with the bridge is
  a local physical step (USB, or BLE with a PIN), like any add-on.

## 6. Sources

Live repository checks on 2026-10-06 (licence file, last commit, latest tag):
[meshtastic/firmware](https://github.com/meshtastic/firmware),
[meshtastic/protobufs](https://github.com/meshtastic/protobufs),
[meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore),
[markqvist/Reticulum](https://github.com/markqvist/Reticulum),
[markqvist/LXMF](https://github.com/markqvist/LXMF),
[markqvist/RNode_Firmware](https://github.com/markqvist/RNode_Firmware),
[jech/babeld](https://github.com/jech/babeld),
[open-mesh-mirror/batman-adv](https://github.com/open-mesh-mirror/batman-adv),
[styrene-lab](https://github.com/styrene-lab), [ratspeak](https://github.com/ratspeak),
[attermann/microReticulum](https://github.com/attermann/microReticulum). Docs as linked in §3.

## Changelog

- 2026-10-06: v0.1, first comparison and recommendation for draft ADR-0038.
