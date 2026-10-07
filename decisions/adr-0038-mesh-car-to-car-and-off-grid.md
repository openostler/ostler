---
title: "ADR-0038 — Mesh: car-to-car and off-grid"
area: decisions
status: locked
version: 1.5
updated: 2026-10-07
depends_on: [references/research/mesh_networking.md, references/research/addons_catalogue.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, references/research/mesh_transports.md, references/research/calls_video_camera_sharing.md, specs/2026-10-07-social-addon-design.md]
summary: >
  Accepted by the owner on 2026-10-06. No mesh inside the car: the in-car network stays routed T1S/Ethernet. A mesh only links car to car, to a base or camp, or off-grid, as its own subnet or non-IP network joined at the brain or a gateway, and it is always a remote path: Read and alerts go out, messages and peer positions come in as data, and nothing from a mesh ever commands the car. First a Meshtastic-compatible LoRa add-on (any owner radio, then our own board on stock Meshtastic firmware) behind a thin GPL-3 VSS bridge with no actions, strict broker ACLs, rate limits and privacy defaults (position sharing opt-in, coarse by default, private channel, no VIN or vehicle id). Mesh identities stay separate from Ostler device keys, pairing keys and passkeys. A richer car-to-car mesh (MeshCore, Reticulum/LXMF, Styrene, Ratspeak) is a later goal or add-on, bench-tested then; until then all four are references only, Reticulum included; Babel, not batman-adv, if a Wi-Fi IP mesh is ever wanted. Amended 2026-10-06 (owner, module-bus answers): the bridge's broker ACL also covers its own status (with its will), power and manifest, like any device; over the radio nothing is retained or retried; its in-car topics get per-topic QoS, retain and expiry. Amendment 2026-10-07, approved by the owner on 2026-10-07 ("approve all"): MeshCore as the second LoRa bridge; batman-adv over 802.11s allowed inside a convoy Wi-Fi mesh, routed at each brain with Babel at the edge; UK/EU HaLow is a car-to-camp uplink, not a mesh; live voice, video and camera streams only over a Wi-Fi IP mesh between ride members, never over HaLow, LoRa or MQTT; router topics and payload fields; ghost and camera consent; inbound mesh positions kept only as expiring retained state, never written to the logbook (narrows §2); bench additions (UK/EU HaLow pair, two-car batman-adv pair, LiveKit on a Pi 5, handover, MeshCore beside Meshtastic).
---

# ADR-0038 — Mesh: car-to-car and off-grid

> **Amended by [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), 2026-10-06:** read "Ostler Lite" or "Lite" as "Ostler Diagnostics" (the family is Ostler Diagnostics, Ostler Guardian and Ostler Hub). See [Amendments (product family)](#amendments-2026-10-06-product-family).
> **Amended 2026-10-06 (Brain rename, [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)):** read "Ostler Hub" and "Hub" (the product, also "hub" for the box) as "Ostler Brain" and "Brain". See [Amendments (Brain rename)](#amendments-2026-10-06-brain-rename).
> **Amended 2026-10-06 (owner, module-bus answers):** the bridge's ACL also lets it publish its own `status`, `power` and `manifest`; QoS and retain per topic. See [Amendments (bridge ACL)](#amendments-2026-10-06-bridge-acl).
> **Amended 2026-10-07 (mesh transports), approved by the owner on 2026-10-07 ("approve all"):** MeshCore, a Wi-Fi mesh with batman-adv inside it, HaLow as an uplink, live media between ride members over Wi-Fi only; inbound mesh positions kept only as expiring retained state, never written to the logbook (§2 narrowed). See [Amendment (2026-10-07), approved](#amendment-2026-10-07-approved).

- **Date:** 2026-10-06
- **Status:** accepted (owner answers, 2026-10-06; see
  [Amendments](#amendments-2026-10-06-owner-answers)). Builds on
  [ADR-0027](adr-0027-ip-everywhere-ecosystem-architecture.md) and
  [ADR-0033](adr-0033-action-categories-and-approvals.md); evidence in the
  [mesh research](../references/research/mesh_networking.md).

## Context

- The add-ons catalogue and the vision list LoRa/Meshtastic convoy messaging and a
  batman-adv/802.11s convoy mesh, with no decision on where a mesh sits or what it may do.
- The owner (2026-10-06) fixed the placement: the in-car network stays routed T1S and
  Ethernet with no mesh; a mesh is only for car-to-car, a base or camp, or off-grid, as its
  own subnet bridged at the brain or a gateway. The lean: a Meshtastic-compatible LoRa
  add-on first for reach, behind a thin VSS bridge (position, alarm state, alerts in and
  out), and the Reticulum family as the richer layer for the social app (ADR-0029 §9).
- Live checks (research §2–§3): Meshtastic is GPL-3.0 with the largest radio base;
  MeshCore is MIT with learned routes; Reticulum's licence is MIT plus use restrictions and
  its author has stepped back; Styrene is a young solo platform with remote shell and
  reboot; Ratspeak is an AGPL client on Reticulum, not a new protocol; batman-adv floods L2
  broadcast and cannot run on an ESP32.

## Decision drivers

- No new path to the car: the node gate (ADR-0032) stays the only one, and a mesh is
  remote (ADR-0033 §6).
- Reach with radios people already own (bikers, overlanders, clubs).
- Privacy by default for location (ADR-0029 §8); no VIN anywhere (ADR-0036).
- Core and node firmware stay commercially licensable (ADR-0012, ADR-0025).
- Low power, off-grid, no internet needed.

## Decision

**1. Placement.** No mesh inside the car. A mesh is its own subnet (IP meshes) or its own
non-IP network (LoRa), joined to the car network only at the brain or a gateway, behind the
same firewall as an uplink. No L2 bridging into a car segment; no mDNS reflection onto a
mesh.

**2. A mesh is a remote path, Read and alerts only.**
- Out: position, alarm state and owner-selected alerts. In: text, peer positions and peer
  alerts, recorded and shown as untrusted data.
- The bridge declares **no actions** in its manifest. The broker ACL lets it publish only
  under its own `in/` and `state/` topics and never to an action, grant or command topic.
- Remote alarm arm and disarm (ADR-0033 §6 as amended) is **not** offered over a mesh, and
  `OSTLER_ALLOW_REMOTE_CONTROL` does not open mesh paths: nothing above Read and alerts,
  with the override on or off (ADR-0033 Amendments of 2026-10-06).

**3. First: a Meshtastic-compatible LoRa add-on.**
- Step one: any Meshtastic radio the owner has, over USB serial, BLE or TCP, bridged on the
  brain (or the phone app on Ostler Lite).
- Step two: our own LoRa add-on running **stock Meshtastic firmware**, joined to the node or
  brain over UART or T1S, so it works with the community's radios.
- The bridge is a **separate GPL-3 program or pack** (it uses the GPL-3 protobufs);
  core, the C decoder and the node firmware never link Meshtastic code (ADR-0025).
- Branding follows Meshtastic's trademark rules ("works with Meshtastic"; no mark on the
  hardware without a licence).

**4. The thin VSS bridge** (research §5) is specified in the module-bus message spec:
topics, a compact Ostler payload with a plain-text fallback, and rate limits (position
10 min parked, 2 min moving, never under 60 s; alarm state on change; alerts debounced per
class; hop limit 3; duty cycle obeyed, position dropped before alerts).

**5. Privacy defaults.** Position sharing **off** until opted in per channel; when on,
**coarse** (about ±3 km) unless a live ride raises it; positions never on the public default
channel; a private channel with a random key; no VIN, `<vid>`, plate or account name in any
mesh field; the radio's own MQTT uplink off; nothing relayed from the mesh to the internet
unless opted in.

**6. Identity separation.** A mesh identity (Meshtastic node key, MeshCore key, RNS
identity) is never derived from, stored as, or used as an Ostler device certificate, pairing
key or passkey (ADR-0029, ADR-0032 §12), and no mesh platform's single root secret (for
example Styrene's) may hold ours. Pairing a radio with the bridge is a local physical step.

**7. The richer car-to-car layer** for groups, rides and convoys (ADR-0029 P4) is a
**later goal or add-on**. When it is taken up, a bench test of **MeshCore**,
**Reticulum/LXMF**, **Styrene** and **Ratspeak** chooses it (the plan below). Until then all
four are **references only**: nothing in Ostler runs or bundles them, **Reticulum
included**. Any fleet-ops feature (remote exec, reboot, config push) is off or absent on
every Ostler device.

**8. Wi-Fi IP mesh**, only if a use appears: **Babel** on the brain or a travel router, its
own routed subnet. batman-adv only behind the same routed edge, never bridged.

## Bench-test plan (richer layer, later)

Two cars or a car and a camp, 2–4 LoRa boards of one model per stack, EU868:
- the same scripted traffic (position every 2 min, ten texts, five alerts) over 1, 2 and 3
  hops, in a town and on an open trail;
- measure delivery rate, latency, airtime and duty-cycle hits, and current draw parked;
- check the bridge ACL refuses any publish outside `in/` and `state/` on every stack;
- check that no field on air carries a VIN, `<vid>` or precise position when coarse is set;
- for Reticulum: rnsd on a Pi brain with an RNode; for MeshCore: companion firmware over
  USB; Meshtastic as the baseline.

## Confirmation

- **Paper check:** no spec or doc proposes a mesh inside the car, a mesh path to an action,
  or mesh code in core or the node firmware.
- **Bridge tests (fake radio):** the manifest has no actions; the broker refuses the
  bridge's publishes outside its own topics; an inbound text shaped like a command executes
  nothing; position is off by default and coarse when first enabled; no VIN or `<vid>` in
  any outbound frame; rate limits hold under an alert storm.
- **Gate matrix (ADR-0033):** the mesh transport is refused for every category above Read,
  with the install override on or off.
- **Licence check:** `reuse lint` shows the bridge as GPL-3 and core never imports it.
- **Bench (later):** the plan above, with results in a reference note before the richer
  layer is chosen.

## Consequences

- The module-bus message spec gains the mesh bridge topics and the mesh transport value.
  *Note (2026-10-06):* written as the [module-bus message spec](../specs/2026-10-06-module-bus-messages-design.md) (§9, §16).
- The add-ons catalogue's LoRa and mesh rows point here; the vision's batman-adv line is
  replaced by Babel-if-needed.
- The UI's links view shows mesh links (UI spec §3.7, the Network page) with airtime and
  peers heard.
- The GPL-3 bridge has its own marked repo, `ostler-bridge-meshtastic`
  (GPL-3.0-or-later; ADR-0034 Amendments).
- A GPL-3 pack or program joins the excluded list for the commercial build.

## Alternatives considered

- **A mesh inside the car.** Rejected by the owner: routed T1S/Ethernet stays.
- **batman-adv as the convoy mesh.** Not chosen: L2 floods mDNS and broadcast, needs a
  bigger MTU, Linux only; Babel keeps the routed model.
- **Reticulum first.** Not chosen: far fewer radios in people's hands, a restrictive licence
  and an absent maintainer; a reference only, kept for the later richer layer.
- **Meshtastic code inside the node firmware.** Rejected: GPL-3 in the node would break the
  commercial build, and a mesh does not belong next to the gate.
- **Our own LoRa protocol.** Rejected: no interop with radios people own (ADR-0017).

## Amendments (2026-10-06, owner answers)

The owner answered on 2026-10-06 and accepted this ADR; the text above already reads this
way. Question numbers in brackets are the owner's numbering for the networking questions of
that day.

1. **LoRa add-on first** (owner Q4: yes). The LoRa add-on is **Meshtastic-compatible first**,
   and the bridge is a **separate GPL-3 program** (§3), in its own marked repo
   `ostler-bridge-meshtastic` (ADR-0034 Amendments).
2. **Richer mesh** (owner Q5). Bench tests of MeshCore, Reticulum/LXMF, Styrene and Ratspeak
   are a **later goal or add-on**; until then all four are kept as references (§7).
3. **Reticulum is reference-only.** Nothing runs or bundles it now, so its licence's
   use restrictions (the no-AI-training clause beside our MCP server, ADR-0030) are
   reviewed only if the richer layer is taken up.
4. **A mesh is a remote path** (§2; ADR-0033 Amendments of 2026-10-06): Read and alerts
   only; never Tier 2+, and no arming or disarming over a mesh, with the install override on
   or off.
5. **Still open, not blocking:** whether, on Ostler Lite, the node itself may be the mesh
   gateway (alarm alerts to a camp with no brain and no phone); until decided, the bridge
   runs on the brain or the phone app (§3).

## Amendments (2026-10-06, product family)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (accepted with the owner's answers of 2026-10-06). The decision text and the
Amendments above are unchanged.

- **Names.** Read "Ostler Lite" and "Lite" above as "Ostler Diagnostics" (the OBD-port node, standalone with a phone), and "Ostler" where it names the tier with a brain as "Ostler Diagnostics + Ostler Hub". "Node" and "brain" stay the internal terms.

## Amendments (2026-10-06, Brain rename)

- **Names.** Read "Ostler Hub" and "Hub" above (and "hub" where it means our compute box) as
  "Ostler Brain" and "Brain" ([ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)). The decision text and the Amendments above are
  unchanged.

## Amendments (2026-10-06, bridge ACL)

Recorded with the owner's answers of 2026-10-06 to the
[module-bus message spec](../specs/2026-10-06-module-bus-messages-design.md#17-owner-answers-2026-10-06)
(item 12; evidence: [MQTT topic practice](../references/research/mqtt_topic_practice.md)
Q12). The decision text and the Amendments above are unchanged; where these entries differ,
they win.

- **ACL** (§2). Besides its own `in/` and `state/` topics, the bridge publishes its own
  `status` (with its will), `power` and `manifest` like any device. It still never
  publishes `role/#`, `vss/+`, `act/+`, `wake/+` or `event/+`, nor any action, grant or
  command topic, and still declares no actions.
- **QoS and retain** (§4). Over the radio nothing is retained and nothing is retried, except
  that alarm-state packets to paired Ostler peers ask for an acknowledgement. In the car:
  `in/text` and `in/alert` QoS 1, not retained, with an expiry; `in/position/<peer>`
  retained with an expiry, so a peer's last position fades; `state/link` QoS 0, retained
  (values in the spec, §16).
- **What it forwards** (§2, §4). The alarm state is the reading
  `Vehicle.Ostler.Security.Alarm.State` (ADR-0016 Amendments) and alerts are `event/<name>`
  messages chosen by an owner allowlist of class and severity.

## Changelog

- 2026-10-07: v1.4, adds the Proposed amendment (2026-10-07, mesh transports) below for owner
  approval; the accepted text above is unchanged.
- 2026-10-07: v1.5, the amendment is approved by the owner on 2026-10-07 ("approve all"),
  renamed "Amendment (2026-10-07), approved"; its decisions answered as recommended; item 10
  narrows §2 so inbound mesh positions are kept only as expiring retained state and never
  written to the logbook (Vehicles & Map spec decision 6); the bench additions join the
  bench-test plan, before Social phase S3.

## Amendment (2026-10-07), approved

**Status: approved by the owner on 2026-10-07 ("approve all").** Text from the
[mesh transports research §7](../references/research/mesh_transports.md#7-proposed-amendment-to-adr-0038-accepted-for-owner-approval),
reconciled with [calls, video and camera sharing](../references/research/calls_video_camera_sharing.md)
§6–§8, the [Social add-on spec](../specs/2026-10-07-social-addon-design.md) §6–§7 and the
[Vehicles & Map add-on spec](../specs/2026-10-07-vehicles-and-map-addon-design.md) §6.2. The
decision text above stands except as follows; where these entries differ, they win.

1. **§3, §7 — MeshCore.** MeshCore becomes the **second LoRa bridge** (`mesh-<n>` with
   `via: meshcore`; own repo `ostler-bridge-meshcore`, MIT), built after the Meshtastic bridge
   and the bench test. Styrene, Ratspeak and Reticulum (with its voice layer LXST, CC BY-NC-ND)
   stay references only.
2. **§8 — Wi-Fi mesh.** A convoy Wi-Fi IP mesh becomes a planned add-on (Social calls, video and
   camera sharing). **Inside the mesh subnet, batman-adv over 802.11s is allowed** (`BATMAN_V`,
   1532-byte mesh MTU). Every brain **routes** between its car and the mesh, never bridges, and
   reflects no mDNS; **Babel** runs at each brain's routed edge to join several meshes and links
   (convoy mesh, camp uplink, home). Moving meshes use 2.4 GHz or non-DFS 5 GHz channels;
   directional 5 GHz is for a parked camp. This replaces "Babel, not batman-adv".
3. **New §8a — HaLow.** In the UK and EU, HaLow (863–868 MHz: 1 MHz channels, 25 mW e.r.p.,
   ≤ 10 % duty cycle for the access point, ≤ 2.8 % for clients) is an **access-point-to-client
   uplink** (camp or house as the access point, the car as the client), **not a car-to-car
   mesh**. It carries text, positions, alerts, voice notes, PTT bursts and stills; no continuous
   calls and no video. EU-band hardware only; never 902–928 MHz kit. A HaLow mesh elsewhere is
   out of scope.
4. **§2 — what crosses.** Out, beyond position, alarm state and alerts: Social content (text,
   voice notes, PTT) and the data classes a share grants (telemetry; camera under a `camera`
   grant), on links whose class rules allow them (Social spec §6). **Live voice, video and
   camera streams cross only a 2.4/5 GHz Wi-Fi IP mesh, only between members of the same ride**,
   as WebRTC through a LiveKit room hosted on a brain; never over HaLow, LoRa or MQTT. LoRa
   carries text, positions, alerts and at most four owner-picked telemetry values; Codec2 voice
   notes over LoRa wait for the Meshtastic bridge and the bench. In: Social content and peer
   data, shown and stored as untrusted. **Calls are never recorded** and nothing from a call
   enters a session log (written beside ADR-0010's cabin-audio rule). **Still nothing above
   Read; no arming, disarming, camera control or other action over any mesh**, with the install
   override on or off.
5. **§4 — topics.** `in/` payloads gain `id`, `class` and `via` (`meshtastic`, `meshcore`);
   positions gain `precision_m`; `state/link` gains `rate_bps`, `duty_left_pct` and `rtt_ms`.
   The Social router is a device `social` publishing only `social/inbox/<class>`,
   `social/state/links`, `social/state/call` and `social/out/<bridge>/#`; with Social installed a
   bridge subscribes to `social/out/<bridge>/#`, and its direct VSS subscriptions remain as
   **standalone mode**. None is a command topic; media never cross the broker, only call state.
6. **§5 — privacy.** Ghost mode (no outbound `position` or `telemetry`) is the default on every
   link; position precision is per link and per share. A camera or microphone is never opened
   from outside without a local tap or a live, time-boxed `camera` grant; a "being viewed" badge
   shows on the car and every view is audited. Viewing is Read; recording, pan/tilt/zoom, IR,
   talk-back and waking a camera stay local.
7. **§6 — identity.** Peers are Ostler identities (ADR-0029); a peer's mesh node ids are bound
   to them by a signed binding exchanged over IP or by QR, never derived from them.
8. **Driving (cross-reference).** Mesh calls follow the same screen rules as any call: audio
   only through the `call` template on a driver-facing head unit while Moving, and video never
   on a driver-facing screen (Social spec §5).
9. **Gate.** The gate's transport value stays `mesh` for every mesh kind, with a new audit field
   `via` (`meshtastic`, `meshcore`, `wifi-mesh`, `halow`).
10. **§2 — inbound positions are not recorded.** §2's "In: … peer positions … recorded and
    shown as untrusted data" is narrowed for positions: a peer position received over any
    mesh is kept **only as expiring retained state** (the retained `in/position/<peer>`
    message with its expiry, module-bus spec §16) and is **never written to the logbook**
    or a session; it fades from the map when it expires, and ride end deletes it. Inbound
    text and alerts stay as §2 says. Source:
    [Vehicles & Map spec](../specs/2026-10-07-vehicles-and-map-addon-design.md) §6.2 and its
    decision 6.

**Confirmation additions.** The gate matrix's `mesh` row gains `via` and is refused above Read
for every value; an inbound call or camera request from a peer starts nothing without the local
tap or a live grant; ghost mode emits no `position` or `telemetry` on any link; one `alert` sent
on three links appears once in `social/inbox/alert`; no audio or video bytes on the broker; a
non-ride peer on the Wi-Fi mesh cannot join a ride's media room.

**Bench additions** (to the plan above; approved, run before Social phase S3):
- a **HaLow EU pair** (camp access point, car client): range at 25 mW, airtime used against the
  2.8 % client budget, delivery of text, PTT bursts, voice notes and stills;
- a **two-car 802.11s/batman-adv pair** on 2.4 GHz, each brain routing, Babel at the edge: range
  and throughput at 1 and 2 hops parked and moving, call latency and loss, and that no mDNS or
  broadcast crosses into a car segment;
- **LiveKit on a Pi 5 brain**: CPU and memory for a 6-member voice room and a 2-member video
  room with go2rtc passthrough;
- **handover** of a live call between internet and the Wi-Fi mesh, and a text falling back to
  LoRa;
- **MeshCore beside Meshtastic** on the same boards with the same scripted traffic.

### Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **MeshCore** — the second LoRa bridge after Meshtastic and the bench test, MIT, own repo? *Recommend:* yes. *Alternative:* Meshtastic only.
2. **batman-adv inside the convoy Wi-Fi mesh** — 802.11s, routed at each brain, Babel at the edge? *Recommend:* yes. *Alternative:* Babel only, each car its own subnet (accepted §8 as is).
3. **HaLow in the UK/EU** — a car-to-camp/house uplink for messages, PTT bursts, voice notes and stills, not a mesh? *Recommend:* yes, EU-band kit only. *Alternative:* leave HaLow out until a UK/EU mesh mode exists.
4. **Live media over a mesh** — voice, video and camera streams only over a 2.4/5 GHz Wi-Fi mesh between ride members, never HaLow, LoRa or MQTT? *Recommend:* yes. *Alternative:* any contact on the mesh, not only ride members.
5. **Calls never recorded** — stated beside ADR-0010's audio rule? *Recommend:* yes. *Alternative:* allow a local recording with every party's consent.
6. **Topics and payload fields** of item 5, with standalone mode kept for bridges? *Recommend:* yes. *Alternative:* bridges keep subscribing to VSS directly and the router only reads `in/`.
7. **LoRa voice notes** — Codec2 clips deferred until the bridge ships and the bench? *Recommend:* yes. *Alternative:* allow them in the first router release.
8. **Bench additions** — HaLow EU pair, two-car batman-adv pair, LiveKit on a Pi 5, handover, MeshCore? *Recommend:* yes, before S3 of the Social spec. *Alternative:* bench only the LoRa stacks now.
