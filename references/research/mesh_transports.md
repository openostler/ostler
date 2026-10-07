---
title: "Mesh transports — Meshtastic, MeshCore, batman-adv and long-range Wi-Fi (HaLow, 2.4/5 GHz, 802.11s) for Social and Vehicles & Map"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/mesh_networking.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0010-replay-notes-audio-motion.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, references/research/addons_catalogue.md, references/research/connectivity_uplink.md]
summary: >
  Live research (2026-10-07, R11) building on the mesh note and accepted ADR-0038, after the owner widened the mesh to Meshtastic, MeshCore and B.A.T.M.A.N. over long-range Wi-Fi with calls, video calls and later camera sharing. Finds that in the UK/EU LoRa carries text, positions, small telemetry and alerts only (10 % duty cycle, ~0.1–2 kbit/s average); Wi-Fi HaLow is held to 1 MHz channels, 25 mW, 10 % (access point) and 2.8 % (client) duty cycle and Morse Micro does not support 802.11s on its EU parts, so EU HaLow is a car-to-camp link for messages, voice notes and stills, not a mesh and not a call path; only 2.4/5 GHz Wi-Fi (802.11s plus batman-adv inside the mesh subnet) and the internet carry live voice, video and camera streams. Proposes one Social link router (internet, then Wi-Fi mesh, then HaLow, then LoRa) with per-message-class rules, a shared message envelope, and a concrete amendment to ADR-0038 (MeshCore as a second bridge, batman-adv allowed inside the mesh subnet, new data classes, router topics, consent for calls and cameras).
---

# Mesh transports for Social and Vehicles & Map

This note **extends** the [mesh research](mesh_networking.md) and
[ADR-0038](../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md); it does not repeat
their licence, activity or per-project notes. New owner direction (2026-10-07): the mesh
"won't be just Meshtastic, but also MeshCore and B.A.T.M.A.N. with long-range WiFi", and
Social should do calls, video calls and, later, camera sharing. Facts were checked live on
**2026-10-07**. **(U)** = unverified; **(E)** = our engineering estimate, to be measured in
the ADR-0038 bench test. Sources are paraphrased and listed in §9.

## 1. What changed since ADR-0038

1. **The owner now wants live media**, not only text, positions and alerts. That is a
   question of bit rate and regulation, not of mesh software: §2 shows which links can
   carry it at all in the UK and EU.
2. **Wi-Fi HaLow is not a mesh in Europe.** Morse Micro (the main HaLow chip vendor) said
   in July 2026 that its HaLowLink 2 ships in an EU version but **802.11s mesh is not
   supported in the EU at all**, citing too little bandwidth. The EU band is 863–868 MHz
   with 1 MHz channels, 25 mW e.r.p., ≤ 10 % duty cycle for access points and ≤ 2.8 % for
   every other device (EU Decision 2022/180, band 84). HaLow in the UK/EU is therefore an
   **access-point-to-client link** (car to camp, car to house), not car-to-car mesh.
3. **HaLow on mainline Linux is new.** The `mm81x` driver (Morse Micro, station and AP only)
   was merged into the kernel in mid-2026; hostapd S1G support was still an RFC being
   rebased in August 2026. Morse's own GPL-2.0 `morse_driver` and OpenWrt fork carry mesh,
   IBSS and batman-adv today. Production use means Morse's OpenWrt fork or a HaLowLink-type
   box, not a stock Pi kernel, for at least another year **(E)**.
4. **Reticulum's voice layer is not usable by us.** LXST (Reticulum's real-time voice and
   signal stream, 0.5.4 on 2026-10-01) is licensed **CC BY-NC-ND 4.0**: no commercial use,
   no derivatives, and its README calls every API unstable. RNS itself moved to 1.5.7
   (2026-10-05) under the Reticulum License already analysed. This strengthens ADR-0038 §7:
   Reticulum stays reference-only.
5. **The owner's "B.A.T.M.A.N." matches current practice.** Open-source HaLow MANET kits
   (openMANET on a Raspberry Pi with a Seeed HaLow HAT) run batman-adv over 802.11s and
   expose one flat LAN to phones and push-to-talk apps, in the US 915 MHz band.

## 2. Links compared (UK/EU rules unless marked)

| | **Meshtastic** (LoRa) | **MeshCore** (LoRa) | **HaLow EU** (802.11ah, 863–868 MHz) | **Wi-Fi 2.4 GHz mesh** (802.11s + batman-adv) | **Wi-Fi 5 GHz mesh / directional** | **Reticulum** (any link) |
|---|---|---|---|---|---|---|
| **PHY rate** | 0.18–21.9 kbit/s by preset; default LongFast 1.07 kbit/s | EU/UK narrow preset 62.5 kHz, SF7–9: ≈ 1.6–2.7 kbit/s (computed) | 1 MHz only: ≈ 0.15–4 Mbit/s (MCS10 to 256-QAM) | 802.11n/ax, tens of Mbit/s at short range | Tens to hundreds of Mbit/s; directional links km at line of sight | As the carrier (≈ 5 bit/s up) |
| **Usable average** | 10 % hourly duty cycle (869.4–869.65 MHz sub-band): ≈ 0.1 kbit/s per node at LongFast **(E)** | Same sub-band and duty cycle: ≈ 0.15–0.27 kbit/s **(E)** | Client 2.8 % (≈ 100 s of airtime an hour); AP 10 %: ≈ 10–100 kbit/s client, ≈ 30–400 kbit/s AP averaged over the hour **(E)** | No duty cycle; halves per hop on one channel | No duty cycle; DFS rules (below) | As the carrier |
| **Range in vehicles** | Several km car to car, 10 km+ to a hill repeater **(E)** | Same radios, similar | US trials: 2 Mbit/s at 15.9 km LoS, 1–1.5 Mbit/s UDP at 2 km (902–928 MHz, up to 1 W, wider channels). EU at 25 mW and 1 MHz: hundreds of m to low km **(E, U)** | Omni car roof: ≈ 200–800 m LoS **(E)** | Omni similar; a directional antenna at camp: km **(E)** | As the carrier |
| **Latency** | Seconds per hop; 3 hops ≈ 5–15 s **(E)** | Similar first flood, faster on learned paths **(E)** | Tens of ms per hop, but duty cycle throttles | ≈ 2–10 ms per hop, roughly doubling per hop | As 2.4 GHz | LXST claims < 10 ms on fast links |
| **Hardware and cost** | ESP32/nRF52 boards ≈ £20–60 **(E)** | Same boards, MeshCore firmware | HaLowLink 2: €126, pair €217 (Jan 2026, EU import extra); HaLow modules on ESP32 and Pi HATs; most cheap dongles are US-band only | Travel router or brain Wi-Fi, ≈ £40–150 **(E)** | Outdoor CPE ≈ £50–150 a pair **(E)** | A Pi brain; an RNode for LoRa |
| **Power** | Tens of mA receive, ≈ 100 mA+ transmit; nRF52 sleeps well | Same | Low (built for battery IoT; target wake schedules) | 1–3 W per radio, always on **(E)** | 3–8 W per CPE **(E)** | As the carrier |
| **Licence** | GPL-3.0 (see mesh note) | MIT firmware; official apps closed | `morse_driver` GPL-2.0; mainline `mm81x` GPL | batman-adv GPL-2.0 kernel module; babeld MIT | As 2.4 GHz | Reticulum License; LXST CC BY-NC-ND |
| **Maturity** | Mature, largest base | Young, fast-growing | Chips mature; Linux upstream brand new; EU kit just arriving | Mature (Freifunk, OpenWrt) | Mature | Bus factor one |
| **Mesh?** | Yes (managed flood) | Yes (learned paths) | **No in EU** (AP–client only); yes elsewhere | Yes | Mesh or point to point | Yes |

**Regulation notes (UK, EU).**

- **LoRa 868:** Meshtastic's EU preset sits in 869.4–869.65 MHz (higher power, 10 % duty
  cycle). The duty cycle is per transmitter per hour: a busy convoy channel runs out of
  airtime, which is why ADR-0038's rate limits drop positions before alerts.
- **HaLow:** EU band 84 (863–868 MHz): channel > 600 kHz and ≤ 1 MHz, 25 mW e.r.p., ≤ 10 %
  (network access points) or ≤ 2.8 % (others), with spectrum-access techniques. The UK
  regulates this under IR2030; Morse Micro says its chips and driver meet the UK power and
  duty-cycle rules. Whether the UK interface requirement is identical to band 84 is
  **(U)**. **Never import US HaLow kit:** 902–928 MHz overlaps UK/EU mobile and railway
  bands; using it here is unlawful.
- **5 GHz:** in the UK, 5470–5725 MHz allows 1 W e.i.r.p. outdoors with DFS and TPC
  **(U, from memory, not rechecked)**; 5725–5850 MHz Wi-Fi is 200 mW with no fixed outdoor
  use, and since 29 April 2026 fixed wireless access there is licence-exempt at 4 W with
  DFS and TPC (fixed links, so a camp mast, not a moving car). **DFS matters in a moving
  car:** a radar hit forces a channel change with a listen period of about a minute **(E)**,
  so a moving mesh should use 2.4 GHz or non-DFS channels; directional 5 GHz is for a
  parked camp or a car-to-home shot.
- **2.4 GHz:** 100 mW e.i.r.p.; crowded but legal everywhere and DFS-free.

## 3. What each link can carry

Media bit rates used (codec facts live, overheads **(E)**): Codec2 0.45–3.2 kbit/s;
AMR-NB 4.75–12.2; Opus voice ≈ 6–32 kbit/s, plus ≈ 16 kbit/s of IP/UDP/RTP overhead at
50 packets a second; a video call ≈ 0.3–1.5 Mbit/s; a 720p camera stream ≈ 1–4 Mbit/s.

| Message class | Internet | Wi-Fi mesh 2.4/5 GHz (1–2 hops) | HaLow EU (AP–client) | Meshtastic | MeshCore | Reticulum |
|---|---|---|---|---|---|---|
| Text | ✓ | ✓ | ✓ | ✓ (≈ 200 B) | ✓ (≈ 150 B) | ✓ (LXMF, store and forward) |
| Position | ✓ | ✓ | ✓ | ✓ (precision per channel) | ✓ (in adverts, user-triggered) | ✓ |
| Telemetry (opted-in stats) | ✓ | ✓ | ✓ | a few values, minutes apart | a few values, on request | ✓ |
| Alert (alarm, breakdown) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Voice note (async) | ✓ | ✓ | ✓ | marginal: a 3 s clip took minutes in a 2026 study; Voicetastic chunks Codec2/Opus | marginal **(U)** | ✓ over IP; LoRa slow |
| Voice call (live) | ✓ | ✓ | **only with 100–200 ms Codec2/Opus packets, short range** (20 ms packets cost ≈ 5–10 % airtime, over the 2.8 % client cap) **(E)** | ✗ | ✗ | IP ✓ (LXST, licence blocks us); LoRa ✗ in EU |
| Video call | ✓ | ✓ (1–2 hops, moving: low resolution) | ✗ | ✗ | ✗ | ✗ for us |
| Camera stream (live) | ✓ | ✓ parked or slow; drops with hops | **stills only** (a JPEG every few minutes) | ✗ | ✗ | ✗ |
| Photo or clip | ✓ | ✓ | small photos, budgeted | ✗ | ✗ | IP only |

The plain conclusion: **live voice, video and cameras need IP at Wi-Fi rates** (internet or
a 2.4/5 GHz mesh). HaLow in Europe is a messaging and stills link with a long reach. LoRa
is the always-there safety net for text, positions and alerts.

## 4. Per-transport notes (new facts only)

- **Meshtastic.** Nothing in this round changes ADR-0038 §3. Voice over Meshtastic exists
  only as third-party push-to-talk messages (Voicetastic: codec-agnostic, chunked, with
  forward error correction, clips of about 12–27 s); not live calls. Treat as **(U)** add-on
  material, not ours.
- **MeshCore.** The EU/UK community preset is 869.525 or 869.618 MHz, 62.5 kHz bandwidth,
  SF 7–9: a little faster than Meshtastic LongFast with less flooding, but group channels
  still flood. A second LoRa bridge is cheap because the radio boards are the same; the
  companion protocol is still marked in development (mesh note §3.4).
- **batman-adv over 802.11s.** The owner's choice is defensible **inside the mesh subnet**:
  roaming phones and multicast push-to-talk see one LAN, and openMANET-style kits work out of
  the box. Its known costs (L2 floods, a 1532-byte MTU, mDNS noise; mesh note §3.1) stay
  inside the mesh subnet if each brain **routes** between the car and the mesh and reflects
  nothing. Use `BATMAN_V` (throughput metric) on modern drivers **(E)**.
- **Babel (contrast).** Babel keeps every car its own subnet and is the right tool to join
  **several** meshes or links (convoy mesh, camp HaLow, home uplink) into one routed
  network; it is less convenient for a flat phone LAN. Both can coexist: batman-adv inside
  the convoy mesh, Babel across the brain's routed edge.
- **HaLow.** EU parts: HaLowLink 2 EU version, MM8108 modules from partners, ESP-IDF
  component for ESP32 hosts (addons catalogue §6). Use it as the **car-to-camp or car-to-
  house uplink** of the addons catalogue row, joined like any uplink (connectivity note),
  with the camp end as the access point (10 % budget) and the car as the client (2.8 %).
- **Reticulum.** Briefly: the best protocol for store-and-forward over mixed links, but its
  licence, its voice layer's NC-ND licence and its absent maintainer keep it a reference.
  Copy its ideas (one envelope across many links, announce-based reachability), not code.

## 5. Proposal: one Social link router

### 5.1 Shape

- **Link bridges stay devices** (module-bus spec §16): `mesh-<n>` for each LoRa radio
  (Meshtastic now, MeshCore next). IP links (internet via the relay or Tailscale, the Wi-Fi
  mesh, HaLow) need no bridge: they are interfaces on the brain or phone, and the Network
  app reports them as links.
- **A Social router** runs with the Social app's back end on the Brain (or inside the phone
  app on Ostler Diagnostics alone). It owns the outbound queue, picks a link per message,
  de-duplicates inbound copies, and is the only thing Social and Vehicles & Map read.
- **One envelope on every link:** `{id (ULID), class, from (peer key fingerprint), to (peer
  or group), sent_at, expires_at, seq?, body}`. On LoRa the envelope is the compact Ostler
  payload ADR-0038 §4 already plans, with a plain-text fallback for non-Ostler radios. The
  same `id` on two links is one message.
- **Peer identity** is the Ostler account and device key of ADR-0029. A peer's mesh node
  ids (Meshtastic node, MeshCore key) are bound to it by a signed binding exchanged over IP
  or by QR, never derived from it (ADR-0038 §6 holds).

### 5.2 Link order and per-class rules

Default order: **internet → Wi-Fi mesh → HaLow → LoRa (MeshCore or Meshtastic, whichever
reaches the peer)**. A link qualifies for a class only if its live estimate (from
`state/link`: rate, RTT, duty budget left, peer heard) meets the class's need.

| Class | Links allowed | Rule | Expiry | If no link qualifies |
|---|---|---|---|---|
| `alert` | all | **Multi-path:** send on every available link; receivers de-duplicate | 24 h | queue; retry when a link appears |
| `text` | all | Best single link; on no delivery report in 30 s (IP) or 5 min (LoRa) **(E)**, try the next | 24 h | queue |
| `position` | all | Best link only; rate and precision per link: LoRa coarse (≈ ±3 km) unless a live ride raises it; IP links follow the share's precision | 10 min (LoRa), 1 min (IP) | drop, never queue |
| `telemetry` | IP links; LoRa only an owner-picked set of ≤ 4 values | Latest value wins | 10 min | drop |
| `voice_note` | IP, HaLow; LoRa off by default | Opus on IP; Codec2 ≤ 10 s on HaLow | 24 h | offer text instead |
| `call_voice` | internet, Wi-Fi mesh; HaLow only in a "radio call" mode with long packets | Needs RTT < 300 ms and ≥ 2× codec rate **(E)** | live | degrade to voice note, then text |
| `call_video` | internet, Wi-Fi mesh | Needs ≥ 500 kbit/s and RTT < 300 ms **(E)**; downgrades to voice when the link falls | live | degrade to `call_voice` |
| `camera` | internet, Wi-Fi mesh; HaLow stills | Only from a `video` share (ADR-0029) and with local consent (§6) | live | stills, or nothing |
| `sync` (ride summaries, photos) | internet, Wi-Fi mesh, HaLow when idle | Lowest priority, metered | days | wait |

Live media never touch MQTT: calls and camera streams run as WebRTC (or plain RTP) directly
between phones or brains over the chosen IP link, with signalling carried by the router.
Only call **state** (ringing, in call, via which link) reaches the car broker for the UI.

### 5.3 Vehicles & Map

The map's peer layer merges positions from every source by peer: freshest wins, and each
dot shows its source and age ("via LoRa, 4 min, ±3 km"). Ghost mode (the default) means the
router sends **no** `position` or `telemetry` on any link; positions from others still
display. Stats shown for other vehicles come only from `telemetry` they chose to share.

### 5.4 Mapping to ADR-0038 topics

| Today (module-bus spec §16) | Proposed |
|---|---|
| `mesh-<n>/in/text`, `in/alert` | Unchanged topics; payload gains `id`, `class` and `via` (`meshtastic`, `meshcore`) so the router can de-duplicate |
| `mesh-<n>/in/position/<peer>` | Unchanged; `<peer>` is the radio's node id, mapped to an Ostler peer by the router's binding table; payload gains `precision_m` |
| `mesh-<n>/state/link` | Gains `rate_bps`, `duty_left_pct`, `rtt_ms?` so the router can rank links |
| Bridge subscribes `vss/Vehicle.CurrentLocation.*`, the alarm state and `event/+` directly | Kept as **standalone mode** (no router installed). With Social installed, the bridge instead subscribes **`social/out/<bridge>/#`**, published by the router on its own topic (the requester-owned pattern of `act/<id>`) |
| — | New, the router's own device `social`: `social/inbox/<class>` (merged, de-duplicated inbound), `social/state/links` (ranked links), `social/state/call` (call state for the UI) |

No new topic is a command topic; the router publishes only under `social/` and bridges
still publish only under their own `in/`, `state/`, `status`, `power` and `manifest`.

## 6. Safety, privacy and ADR-0033

- **Still a remote path.** A convoy Wi-Fi mesh and HaLow are **remote**, even though they
  are IP and fast: only the car's own head unit, in-car LAN and the node's own links are
  local (ADR-0033 §6). Gate transport value stays `mesh` for every mesh kind, with a new
  audit field `via` (`meshtastic`, `meshcore`, `wifi-mesh`, `halow`).
- **Calls and cameras are not actions on the car.** Voice and video calls are phone or
  brain media between people. Starting a camera stream for a peer is a **Read** of the
  `video` data class: it needs a share that grants `video` (ADR-0029) **and** a tap by
  someone in the car each time (or a time-boxed "share my dash camera for this ride");
  a peer can never silently open a camera or a microphone.
- **Audio rule.** ADR-0010 and ADR-0029 keep cabin audio recordings on the device and never
  in a share. A live call is not a recording: the router never records calls, and nothing
  from a call enters a session log. That needs saying in the amendment so the two rules
  don't collide.
- **Driving.** On the head unit while moving: calls audio-only through the driver-safe
  call template; video calls and camera views only when parked or with the "I'm a
  passenger" override (lockout proposal); no text entry.

## 7. Proposed amendment to ADR-0038 (accepted; for owner approval)

**Amendments (2026-10-07, mesh transports).** The decision text above stands except:

1. **§3, §7 — MeshCore.** MeshCore becomes the **second LoRa bridge** (`mesh-<n>` with
   `via: meshcore`, its own repo `ostler-bridge-meshcore`, MIT), built after the Meshtastic
   bridge and the bench test. Styrene, Ratspeak and Reticulum (including LXST, CC BY-NC-ND)
   stay references only.
2. **§8 — Wi-Fi mesh.** A Wi-Fi IP mesh becomes a planned add-on (calls, video, camera
   sharing). **Inside the mesh subnet, batman-adv over 802.11s is allowed** (owner choice);
   every brain routes between its car and the mesh, never bridges, reflects no mDNS, and
   needs a 1532-byte mesh MTU. **Babel** joins several meshes and links at the routed edge.
   Moving meshes use 2.4 GHz or non-DFS channels.
3. **New §8a — HaLow.** In the UK/EU, HaLow is an access-point-to-client **uplink** (camp or
   house), not a car-to-car mesh: 1 MHz, 25 mW, ≤ 10 % / ≤ 2.8 % duty cycle. Only EU-band
   hardware; never 902–928 MHz kit.
4. **§2 — what crosses.** Out, beyond position, alarm state and alerts: Social content
   (text, voice notes, call media) and the data classes a share grants (telemetry, `video`)
   on links whose class rules allow them. In: Social content and peer data, shown and
   recorded as untrusted (calls excepted: never recorded). **Still nothing above Read; no
   arming, disarming or action over any mesh**, with the install override on or off.
5. **§4 — topics.** Add `id`, `class`, `via` to `in/` payloads; `rate_bps`, `duty_left_pct`,
   `rtt_ms` to `state/link`; the router's `social/out/<bridge>/#`, `social/inbox/<class>`,
   `social/state/links` and `social/state/call`; the bridges' direct subscriptions become
   standalone mode.
6. **§5 — privacy.** Ghost mode (no outbound position or telemetry) is the default on every
   link; position precision is per link; a camera or microphone is never opened from
   outside without a local tap or a time-boxed ride share.
7. **§6 — identity.** Peers are Ostler identities; mesh node ids are bound to them by a
   signed binding, never derived.

Confirmation additions: the gate matrix's `mesh` row gains `via`; a test that an inbound
`call` or `camera` request from a peer starts nothing without the local tap; a test that
ghost mode emits no `position` on any link; a router test that one `alert` sent on three
links appears once in `social/inbox/alert`.

## 8. Copy / Avoid / Decide for Ostler

**Copy**
- **One envelope, many links, de-duplicate by id** (Reticulum's idea, our code) →
  Social router, §5; ADR-0038 amendment item 5.
- **Multi-path for alerts, best-single-link for everything else** → §5.2; module-bus spec
  §16.
- **openMANET's layout**: batman-adv over 802.11s inside the mesh, a Pi brain per node,
  phones on a local AP → ADR-0038 amendment item 2.
- **Source and age on every peer dot** ("via LoRa, 4 min") → Vehicles & Map; UI spec.
- **Graceful degrade** video → voice → voice note → text → app model / Social spec.

**Avoid**
- **Promising video or calls over LoRa or EU HaLow.** The regulation forbids the airtime;
  say so in the UI (link badge shows what is possible now).
- **US-band HaLow (902–928 MHz) or US-firmware LoRa** in the UK/EU.
- **LXST or any Reticulum code** in anything we ship (CC BY-NC-ND; Reticulum License).
- **Bridging batman-adv into a car segment** or reflecting mDNS onto the mesh (ADR-0038 §1).
- **DFS channels for a moving mesh.**
- **Media over MQTT.** The car broker carries call state, never audio or video.

**Decide (recommendations for the owner)**
1. **D1 — MeshCore as the second LoRa bridge** after Meshtastic and the bench test, MIT,
   own repo. *Recommend: yes.*
2. **D2 — batman-adv inside the convoy Wi-Fi mesh** (802.11s, `BATMAN_V`), routed at each
   brain, Babel at the edge to join meshes. *Recommend: yes; amend ADR-0038 §8 as in §7.*
3. **D3 — HaLow is a car-to-camp/house uplink in the UK/EU, not a mesh**, EU-band kit only,
   messages, voice notes and stills only. *Recommend: yes; new §8a.*
4. **D4 — Live voice, video and camera streams only over the internet or a 2.4/5 GHz Wi-Fi
   mesh**, WebRTC between phones or brains, never through MQTT. *Recommend: yes.*
5. **D5 — The Social router and per-class rules of §5.2** (link order internet → Wi-Fi
   mesh → HaLow → LoRa; alerts multi-path) as the starting design for a Social spec.
   *Recommend: yes; write `specs/…-social-transports-design.md` before code.*
6. **D6 — Camera and microphone consent:** a peer can view a camera only with a `video`
   share **and** a local tap or a time-boxed ride share; calls are never recorded, and
   that is written beside the ADR-0010 audio rule. *Recommend: yes.*
7. **D7 — Approve the ADR-0038 amendment text of §7** as written. *Recommend: yes, after
   D1–D6.*
8. **D8 — Bench additions:** add a HaLow EU pair (camp AP, car client) and a two-car
   802.11s/batman-adv pair to the ADR-0038 bench plan; measure range, airtime against the
   2.8 % budget, call quality and handover between links. *Recommend: yes.*

## 9. Sources (checked 2026-10-07)

- Morse Micro forum, 802.11s on HaLowLink (EU version exists; no 802.11s in the EU):
  <https://community.morsemicro.com/t/802-11s-support-on-halowlink-hardware/1859>
- Morse Micro forum, UK compatibility (chips meet UK power and duty cycle; Region 2 filter
  on older kit): <https://community.morsemicro.com/t/halowlink-1-device-uk-compatibility/514>
- EU Decision 2022/180, band 84 and bands 46a–47b:
  <https://lawplayer.com/eu/act/32022D0180>
- HaLowLink 2 in Europe (limits, price, Jan 2026):
  <https://www.igorslab.de/en/wi-fi-halow-with-kilometer-range-why-the-new-gl-inet-halowlink-2-is-reaching-its-limits-in-europe/>
- MM8108 rates: <https://www.cnx-software.com/2025/01/14/morse-micro-mm8108-wifi-halow-soc-supports-up-to-43-33-mbps-transfer-rate-improves-range-and-power-efficiency/>
- `morse_driver` (GPL-2.0, AP/STA/mesh/IBSS): <https://github.com/MorseMicro/morse_driver>
- hostapd S1G RFC and the merged kernel driver (Aug 2026):
  <https://lists.infradead.org/pipermail/hostap/2026-August/045423.html>;
  `mm81x` patches: <https://lkml.iu.edu/2606.3/04258.html>
- Morse 802.11s app note: <https://docs.morsemicro.com/application-notes/appnote-32-how-to-configure-802.11s-mesh>
- HaLow field results (US band): <https://www.wi-fi.org/node/38884>,
  <https://www.techradar.com/pro/groundbreaking-wireless-tech-that-can-run-on-coin-batteries-for-months-hits-new-milestone-halow-achieves-10-mile-range-in-latest-test>
- Heltec HaLow dongle V2 (902–928 MHz, ≈ €71):
  <https://store.rokland.com/collections/new-arrivals/products/heltec-wi-fi-halow-dongle-v2-802-11ah-long-range-wireless-network-bridge>
- openMANET (HaLow + batman-adv over 802.11s): <https://github.com/OpenMANET/docs>,
  <https://hamradio.my/openmanet-raspberry-pi-wifi-halow-manet-radio/>
- Meshtastic presets and EU duty cycle: <https://meshtastic.org/docs/overview/radio-settings/>
- MeshCore radio layer and EU preset: <https://wiki.eastmesh.au/meshcore/radio-layer/>
- Voicetastic protocol: <https://github.com/voicetastic/voicetastic-core/wiki/Voice-Protocol>;
  voice over Meshtastic study (2026): <https://rda.sliit.lk/items/c234e29f-0298-4835-92ea-da388e6cc73a/full>
- LXST (CC BY-NC-ND 4.0, 0.5.4): <https://pypi.org/project/lxst/>; RNS 1.5.7:
  <https://pypi.org/project/rns/>
- Codec 2 modes: <https://en.wikipedia.org/wiki/Codec_2>
- Ofcom 5.8 GHz Wi-Fi and FWA exemption (2026):
  <https://www.ispreview.co.uk/?p=43642>,
  <https://www.ofcom.org.uk/siteassets/resources/documents/spectrum/business-radio-licences/guidance-for-licence-exempt-operation.pdf>
- Mesh throughput per hop (batman-adv, Babel): <https://www.mdpi.com/2673-4001/5/4/51>,
  <https://battlemesh-test-docs.readthedocs.io/v8/1-the-mesh-of-death-adversity.html>

## Changelog

- 2026-10-07: v0.1, transports for Social and Vehicles & Map; ADR-0038 amendment proposal.
