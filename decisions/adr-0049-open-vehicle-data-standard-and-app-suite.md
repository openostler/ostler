---
title: "ADR-0049 — Ostler is an open diagnostic and logging platform with an open vehicle-data feed (VISS), not an operating system: a gateway app and separate apps"
area: decisions
status: locked
version: 1.2
updated: 2026-10-08
depends_on: [references/research/direction_standard_not_os.md, references/research/direction_feed_standards.md, references/research/direction_host_platforms.md, references/research/direction_headunit_ecosystem.md, references/research/direction_repo_audit.md, references/research/direction_positioning.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0048-ostler-as-an-android-launcher.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md]
summary: >
  Accepted: approved by the owner on 2026-10-08 ("I agree with everything", with changes; direction decisions 1–37). Ostler is an open diagnostic and logging platform with an open vehicle-data feed, not an operating system; this returns to the original build. Full COVESA VISS v3 over VSS is the core protocol on every signal hop (ADR-0051), and MQTT is an external output only. The node stays the only path to the car. On each Android phone or head unit a required gateway app configures connections (node, Brain, adapters, pairing), holds the gate client, driving state and alerts, runs the permissions controller (per-app toggles, a scoped VISS access token, writes only as requests, cautious defaults, revoke with an access log), serves the feed and carries a normal ~1 Hz feed widget. The other apps are separate: Diagnostics with Decode lab merged, Trips, Security, Maintenance, and add-ons (friends' live map, Social, the Meshtastic/MeshCore mesh). No widget apps; live views stay in the apps. One shared app template (ADR-0050). Cameras sit in the feed's metadata; meshes are transports. Read-only output bridges: RealDash, ELM327 emulation, CAN-box emulation, Home Assistant and OVMS. The launcher is parked (ADR-0048). The Brain is optional. Supersedes ADR-0046's OS boundary (its safety list and hard lines stay) and ADR-0042's one-app rule. Amended v1.2 (owner, 2026-10-08): one Ostler app (Home, Diagnose, Logs, Map, More, Drive mode) with the gateway inside it; the screen line "Ostler arranges, Android runs" (split screen, picture-in-picture, floating gauge, later a home-screen mode; never own media, navigation, phone, audio focus, hosted apps or app store); Android Automotive as reference and a parked track.
---

# ADR-0049 — A diagnostic and logging platform with an open vehicle-data feed

> **Amended 2026-10-08 (v1.2, owner): one Ostler app, and the screen line.**
>
> - **One app.** The owner wants one app to diagnose the car and to drive with, on a phone
>   or on an Android head unit. Item 6 changes: Home, Diagnose (with Decode lab), Logs (was
>   Trips), Map (the telemetry map) and More, plus Drive mode, are **one Ostler app**, the
>   same on phone and head unit. The gateway job (item 4: connections, permissions
>   controller, the VISS feed, External MQTT, the feed widget) runs inside that app as its
>   service; other apps still reach the feed only through it. Maintenance, Security and the
>   add-ons (friends' map, Social, mesh) stay separate apps or entries under More.
> - **The screen line: "Ostler arranges, Android runs."** Ostler may show its own screens,
>   work in split screen and picture-in-picture, offer a small floating gauge over other apps
>   (Drive mode rules apply), and later a home-screen mode with a now-playing card (media
>   sessions), other apps' widgets and a dock. Ostler **never** builds its own media player,
>   radio, navigation or phone, never manages audio focus, never hosts other apps inside
>   itself and never runs an app store. Spotify, Waze and Android Auto stay the real apps.
> - **Launcher:** still parked (item 10). If it returns, it is that home-screen mode inside
>   the Ostler app, not a separate launcher, decided after the two-head-unit bench test.
> - **Android Automotive** is the reference architecture and a parked track (direction note
>   §3.3): a VISS→VHAL bridge and an Ostler reference build on a Raspberry Pi, after the
>   bench test. VISS stays the core.

- **Date:** 2026-10-08
- **Status:** accepted. Approved by the owner on 2026-10-08 ("I agree with everything"),
  with changes that this text includes. The
  [direction note](../references/research/direction_standard_not_os.md) holds the evidence
  and the 37 approved decisions (§8).
- **Supersedes in part:** [ADR-0046](adr-0046-empty-os-every-app-an-add-on.md) (the OS
  boundary: launcher, dock, drawer, app runtime, Store as code distribution, own audio
  focus; its safety list and hard lines stay) and
  [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) (one app per store).
- **Parks:** [ADR-0048](adr-0048-ostler-as-an-android-launcher.md) (Ostler as an Android
  launcher) until the two-head-unit bench test.
- **Amends:** [ADR-0034](adr-0034-repo-boundaries.md) (repos),
  [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (USB serial head-unit
  link). **With:** [ADR-0050](adr-0050-kotlin-for-the-android-app-tier.md) (Kotlin) and
  [ADR-0051](adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md) (VISS v3 everywhere).

## Context

- ADR-0046 builds an operating system inside one web app. On Android it cannot host other
  apps, cannot manage audio focus (the system does since Android 12), has nowhere to run
  the Python services without a Brain, and is larger than one owner can maintain.
- Almost all of that OS is unbuilt. The built parts (node, gate, decoders, packs, VSS, the
  Python services) are the durable value.
- The live app today is a diagnostic and logging platform. The owner wants to return to
  that, with an open feed that every app reads the same way, and to "follow the industry so
  we do not become our own thing".
- The owner chose Android head units and Android phones as the first hosts.

## Decision drivers

- Safety and the gate never depend on which apps are installed.
- One feed, one standard, for our apps and everyone else's.
- Owners keep the apps they already use (Waze, Spotify, Home Assistant, RealDash).
- What one owner with agents can build and keep working.

## Decision

1. **What Ostler is.** An open diagnostic and logging platform with an open vehicle-data
   feed (VISS). Not an OS.
2. **The feed is full VISS v3 over VSS** on every hop that carries vehicle signals: node to
   gateway, Brain to apps, gateway to apps. WebSocket first, then gRPC or HTTP where they
   fit. The internal MQTT module bus and the SSE `/events` snapshot become legacy. MQTT is
   the external cap only. Detail: [ADR-0051](adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md).
3. **The node** stays the only path to the car's buses, and its gate decides every write
   (ADR-0044's adapter exception unchanged).
4. **The gateway app** is required on each Android phone or head unit. It:
   - configures connections: the node, the Brain, adapters, pairing;
   - holds the gate client, driving state and alerts, and the alarm path;
   - runs the **permissions controller** (item 5);
   - serves the feed;
   - has an **External MQTT** menu that publishes to an outside broker (Home Assistant
     discovery, OVMS topics and others);
   - carries the **normal feed widget**: a standard Android widget at about 1 Hz.

   The Brain's Python service can do the same gateway job. Android straight to a node is
   the server; Android to a Brain is a client that forwards requests, and the Brain is the
   server. One permission set, held by the server, is synced to the Android gateways and
   the cloud view; Brain failover is open (ADR-0051 item 9).

   ADR-0046 §2's safety list ("safety is never an app") now lives in the node and the
   gateway app, which cannot be left out.
5. **The permissions controller.**
   - **Identity:** every app asks the gateway first. On Android it is identified by package
     name and signing key; on the network, by an access request the owner approves.
   - **Per-app toggles,** such as "Engine and speed (read)", "Location", "Faults (read)",
     "Clear faults", "Actuator tests". Reads map to ADR-0029 data classes; writes map to
     ADR-0033 categories and tiers.
   - The gateway issues a **VISS access token** limited to what is switched on; the VISS
     server refuses anything else.
   - **Writes are only requests:** the gateway confirms risky ones on its own screen, and
     the node gate decides. Tier 4 is impossible regardless.
   - **Cautious defaults:** a new app gets basic-signal reads only.
   - **Revoke any time,** with a per-app access log.
6. **The apps** (amended in v1.2: Diagnostics, Logs and Map are now one Ostler app with
   the gateway inside; see the note at the top) are separate Android apps:
   - **Diagnostics, with Decode lab merged in**, as in the old D2 app;
   - **Trips** (logging);
   - **Security**;
   - **Maintenance**, a separate app;
   - **add-ons as completely separate apps:** the live map of friends' vehicles, Social,
     and the Meshtastic and MeshCore mesh.

   There are **no widget apps**. Live views stay inside the apps. Radio, Audio, Media,
   Camera, Navigation and Phone apps are dropped: Android and the head unit already do them.
7. **One shared app template:** a Kotlin shell, a VISS client and a theme-pack loader. Every
   Ostler app follows the active theme set in the gateway app. Apps are built the hybrid
   way: the shell around our React pages in a WebView, native where it pays
   ([ADR-0050](adr-0050-kotlin-for-the-android-app-tier.md)).
8. **Cameras and meshes are in the feed.** Cameras are listed in VISS metadata, each
   pointing to an RTSP or WebRTC stream. Meshtastic and MeshCore are transports and bridges
   for the feed (ADR-0038).
9. **Output bridges, read-only:** a RealDash TCP stream, ELM327/OBD emulation (Bluetooth or
   Wi-Fi), CAN-box emulation (Raise, Simple Soft), and Home Assistant and OVMS through
   External MQTT. They are views of the feed. Nothing coming back from them reaches the car
   except through the gate.
10. **The launcher is optional and parked** until two head units have been bench-tested for
    sleep, the feed widget and the USB link (direction decision 23). ADR-0048 is parked.
11. **The Brain is optional.** Node plus phone, or node plus head unit, is a complete
    product. The Brain keeps long recording, cameras, Home Assistant and the web console.
12. **Theming** is re-targeted to token packs, gauge styles and app skins through the shared
    template. The six-layer skin engine is parked; safety colours stay restylable under the
    render check.
13. **Links and hosts:** Android 10 minimum; the head unit reaches the node over USB serial
    first, phones over BLE, Wi-Fi as fallback (amends ADR-0039).
14. **Distribution:** Play Store, F-Droid and direct APK. No Store of our own for code; the
    Store spec becomes a catalogue of packs and themes as data.
15. **The spec** lives in a spec repo, `ostler-feed`, with conformance tests, and ships with
    the gateway app. Licences: the spec CC BY-SA, client SDKs Apache 2.0, the gateway app AGPL.

## What stays

The node and its gate, the C decoder, packs, VSS, the Python services on the Brain, accounts
and sharing, ADR-0046's safety list and hard lines, the openness round, and UX first for our
own apps (a short brief per app before building).

## Confirmation

- Conformance tests in `ostler-feed` run against the gateway app and the Brain.
- A permissions test: an app with only basic reads gets refused on every other path, and a
  write request without its toggle never reaches the node.
- The two-head-unit bench test reports on sleep and wake, the feed widget and the USB link
  before app work starts.

## Consequences

- ADR-0046 and ADR-0042 carry dated supersession notes; ADR-0048 is parked.
- ADR-0034 gains the repo changes: `ostler-app-decode-lab` merges into
  `ostler-app-diagnostics`; Radio, Audio, Media, Camera, Navigation and Phone repos are
  archived; `ostler-feed` is added.
- The app-model, app UI model and Store specs are superseded in part; the launcher spec is
  parked; the head-unit apps spec drops Radio, Media, Phone and Navigation; the theme engine
  spec is re-scoped.
- The designer brief and `screens.json` are re-scoped to per-app screens (a follow-up).
- GOALS, SCOPE and README carry the new mission.

## Alternatives considered

- **Keep the web OS (ADR-0046).** Rejected: four fatal flaws in the research.
- **A VISS profile beside our own API.** Rejected by the owner: full VISS everywhere.
- **Widget apps (a Dash app with widget packs).** Rejected: one normal feed widget; live
  views in the apps.
- **Fully native apps from the start.** Kept as the end state; the hybrid route ships
  sooner.
- **Our own launcher now.** Parked until the bench test.

## Changelog

- 2026-10-08 — v0.1, proposed: drafted from the direction research round.
- 2026-10-08 — v1.0, accepted: approved by the owner ("I agree with everything", with
  changes): diagnostic and logging platform; VISS v3 core and MQTT external (ADR-0051); the
  gateway app and its permissions controller; the app list with Decode lab in Diagnostics
  and no widget apps; the shared template (ADR-0050); cameras, meshes and output bridges;
  launcher parked.
- 2026-10-08 — v1.1: item 4 notes the gateway roles and sync (ADR-0051 item 9, direction
  decisions 38–40).
- 2026-10-08 — v1.2, amended by the owner: one Ostler app (item 6) with the gateway inside
  it; the screen line ("Ostler arranges, Android runs") and its never list; launcher still
  parked, as a home-screen mode of the app if it returns; Android Automotive as the
  reference and a parked track.
