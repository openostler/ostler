---
title: "Direction — Ostler as an open diagnostic and logging platform with an open vehicle-data feed (VISS), not an OS: synthesis of the October 2026 direction round, with the owner's approved decision list"
area: references
status: stable
version: 1.1
updated: 2026-10-08
depends_on: [references/research/direction_feed_standards.md, references/research/direction_host_platforms.md, references/research/direction_headunit_ecosystem.md, references/research/direction_repo_audit.md, references/research/direction_positioning.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md]
summary: >
  Approved by the owner on 2026-10-08 ("I agree with everything", with changes). Ostler is an open diagnostic and logging platform with an open vehicle-data feed, not an operating system; this returns to the original build. Full COVESA VISS v3 over our VSS tree is the core protocol on every hop that carries vehicle signals (node to gateway, Brain to apps, gateway to apps), over VISS's own transports (WebSocket first); the internal MQTT module bus and the SSE /events snapshot become legacy, and MQTT is only an external output through the gateway app's External MQTT menu. The node stays the only write path. Apps: a required gateway app (connections, gate client, driving state, alerts, the permissions controller, the feed and a normal ~1 Hz feed widget); Diagnostics with Decode lab merged; Trips; Security; Maintenance; and separate add-on apps (friends' live map, Social, the Meshtastic/MeshCore mesh). No widget apps; live views stay inside the apps; the launcher is parked. One shared app template (Kotlin shell, VISS client, theme-pack loader). Output bridges (RealDash, ELM327 emulation, CAN-box emulation, Home Assistant, OVMS) are read-only views. 37 approved decisions; ADR-0049, ADR-0050 and ADR-0051 record them.
---

# Direction: a diagnostic and logging platform with an open feed, not an OS

**Approved by the owner on 2026-10-08** ("I agree with everything"), with changes that this
version folds in: no widget apps, the gateway app, Decode lab merged into Diagnostics,
Maintenance and the add-ons as separate apps, the launcher parked, full VISS v3 as the core
protocol with MQTT external only, the gateway's permissions controller, cameras and meshes in
the feed, one shared app template and read-only output bridges. The decisions are recorded in
[ADR-0049](../../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md),
[ADR-0050](../../decisions/adr-0050-kotlin-for-the-android-app-tier.md) (Kotlin) and
[ADR-0051](../../decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md) (VISS v3
everywhere). The research behind it:

| Note | Question |
|---|---|
| [Feed standards](direction_feed_standards.md) | which standard every app's feed should follow |
| [Host platforms](direction_host_platforms.md) | how apps get the feed and draw widgets on each host |
| [Head-unit ecosystem](direction_headunit_ecosystem.md) | what owners already use, and whether a launcher adds value |
| [Repo audit](direction_repo_audit.md) | what we keep, re-target or drop, and the rewrite cost |
| [Positioning](direction_positioning.md) | what Ostler should be, against its precedents |

## 1. The problem

The owner shared a chat about the Dudu7 head unit whose rule is "don't build an operating
system inside an operating system". The repo audit confirms it. ADR-0046 makes Ostler an
empty OS with its own launcher, Store, app runtime and theme engine, all inside one web
app. The fatal flaws, with evidence in the audit:

1. **The third-party app wall.** One web app cannot host Waze, Spotify or Home Assistant.
   Owners on Android head units want all three beside Ostler.
2. **Audio focus.** Since Android 12 the system manages audio focus between apps. Our "OS"
   would be one app and could never duck Spotify or a navigation prompt.
3. **No home for the services on Android.** The recorder, accounts and app backends are
   Python on the Brain. Without a Brain, an Android phone or head unit has nowhere to run
   them.
4. **The size of the OS.** A launcher, a Store, an app runtime and a skin engine are more
   than one owner with agents can build and keep working.

Serious, not fatal: one WebView crash takes everything down; a Store that downloads code
into a phone app breaks store rules; Android widgets cannot be live gauges.

**The good news.** Almost all of the ADR-0046 OS is unbuilt: the launcher, Store, runtime
and theme engine exist only as specs. What is built is the part that survives: about
27,700 lines of Python services, the node firmware with its C decoder and C gate, the D2
pack, VSS and the module bus. Changing direction costs specs, not code
([repo audit](direction_repo_audit.md)).

## 2. The recommendation (approved)

**Ostler is an open diagnostic and logging platform with an open vehicle-data feed (VISS).**
It is not an OS. This is a return to the original build: the live app today is a diagnostic
and logging platform.

1. **The feed is full COVESA VISS v3** over the **VSS** tree we already use (ADR-0016). VISS
   is the core protocol, not a profile beside our own API: every hop that carries vehicle
   signals speaks it (node to gateway, Brain to apps, gateway to apps), over VISS's own
   transports, WebSocket first, then gRPC or HTTP where they fit. We follow the industry so
   we do not become our own thing ([ADR-0051](../../decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md)).
   - The internal MQTT module bus and the bespoke SSE `/events` snapshot become **legacy**
     and are migrated over time.
   - **MQTT is the external cap only:** the gateway app's External MQTT menu publishes to an
     outside broker (Home Assistant discovery, OVMS topics and others).
2. **The node, unchanged.** It is the only path to the car's buses and its gate decides every
   write. It also supplies what head units lack: ignition state and decoded data
   ([ecosystem](direction_headunit_ecosystem.md) §3).
3. **The gateway app, required on each Android phone or head unit.** It configures the
   connections (node, Brain, adapters, pairing), holds the gate client, driving state and
   alerts, runs the **permissions controller** (§3) and serves the feed. It answers
   ADR-0042's objection to separate apps: the lockouts, the gate client and the sign-in live
   once, in this app. It also carries a **normal feed widget**: a standard Android widget
   updated at about 1 Hz.
4. **The apps**, each a separate Android app that asks the gateway for access:
   - **Diagnostics, with Decode lab merged in**, as in the old D2 app, where they go hand in
     hand;
   - **Trips** (logging);
   - **Security**;
   - **Maintenance**, a separate app;
   - **add-ons as completely separate apps:** the live map of friends' vehicles, Social, and
     the Meshtastic and MeshCore mesh.

   There are **no widget apps**. Live views (gauges, live data) stay inside the apps.
5. **The launcher is optional and parked** until the two-head-unit bench test (decision 23).
   ADR-0048 is parked.
6. **The Brain becomes optional.** Node plus phone, or node plus head unit, is a complete
   product. The Brain stays for people who want a box: long recording, cameras, Home
   Assistant and the web console.
7. **One shared app template:** a Kotlin shell, a VISS client and a theme-pack loader, so
   every Ostler app follows the active theme set in the gateway app.
8. **Output bridges, so Ostler works with everything:** a RealDash TCP stream, ELM327/OBD
   emulation (Bluetooth or Wi-Fi), CAN-box emulation (Raise, Simple Soft), and Home
   Assistant and OVMS through External MQTT. All are **read-only views**: nothing coming back
   from them reaches the car except through the gate.
9. **SDKs:** an Android VISS client library under a permissive licence first, then web and
   Python. Third-party apps use the same feed as ours.

**How the apps are built: the cheap way first.** Each app is the shared Kotlin shell (its
own process, notifications, services) around our existing React pages in a WebView, with
screens moved to native only where it pays
([ADR-0050](../../decisions/adr-0050-kotlin-for-the-android-app-tier.md)). The audit costs
this at about 2–4 months for Diagnostics, Trips and Security, against 6–9 months for a fully
native rewrite and 6–10 months to finish the web OS.

**What we keep from the earlier plan:**
- the React UI, as the Brain's web console and as pages inside the apps;
- the designer brief, re-scoped to per-app screens (the launcher, Store and app-frame
  screens are dropped);
- the theme work, re-targeted (§4);
- the app repos that still apply, as Android projects (decision 28).

**What we drop or park:** the empty OS (ADR-0046's launcher, dock, drawer, app runtime and
our own audio focus), the in-app Store as a way to ship code, widget apps, the Android
launcher (ADR-0048, parked), and own Radio, Audio, Media, Camera, Navigation and Phone apps,
which Android and the head unit already do (decisions 15 and 28).

## 3. The standard in more detail

| Part | Decision | Source |
|---|---|---|
| Data model | VSS 6.1 tree, plus the `Vehicle.Ostler.*` overlay | ADR-0016 |
| Protocol | Full VISS v3 on every hop that carries vehicle signals: `get`, `set`, `subscribe`, `unsubscribe`, metadata; values `{value, ts}` plus optional `c`, `stale`, `src`, `unit` | ADR-0051; [feed standards](direction_feed_standards.md) §3 |
| Transports | VISS WebSocket first (subprotocol `VISSv3`, `wss` on the LAN, found by mDNS `_ostler-feed._tcp`); VISS gRPC and HTTP where they fit; on a USB serial link the same VISS messages, framed | ADR-0051 |
| Android | Apps get a token from the gateway (identity: package name and signing key), then speak VISS to it over a loopback WebSocket | ADR-0051; feed standards §5 |
| Access | The gateway's permissions controller issues a VISS access token limited to the app's switched-on toggles; the VISS server refuses anything else | §3.1 below |
| Writes | Requests only: VISS `set` on actuator and `Vehicle.Ostler.*` action paths, mapped to ADR-0033 categories and tiers; the gateway confirms risky ones on its own screen; the node gate decides; Tier 4 never | ADR-0033, ADR-0051 |
| Cameras | Listed in VISS metadata, each entry pointing to an RTSP or WebRTC stream | decision 34 |
| Meshes | Meshtastic and MeshCore are transports and bridges for the feed, not separate protocols | ADR-0038, decision 34 |
| External | MQTT only through the gateway's External MQTT menu: Home Assistant discovery, OVMS topics, others | decision 33 |
| Legacy | The MQTT module bus (`api/asyncapi.yaml`) and SSE `/events`, migrated over time | ADR-0051 |
| Versioning | VISS subprotocol, `Server.Support.Ostler.Profile`, the VSS pin | feed standards §8 |

### 3.1 The permissions controller

- **Identity:** every app asks the gateway first. On Android it is identified by package
  name and signing key; on the network, by an access request the owner approves.
- **Per-app toggles,** for example "Engine and speed (read)", "Location", "Faults (read)",
  "Clear faults", "Actuator tests". Reads map to ADR-0029 data classes; writes map to
  ADR-0033 categories and tiers.
- **Token:** the gateway issues a VISS access token limited to what is switched on, and the
  VISS server refuses anything else.
- **Writes are only requests:** the gateway confirms risky ones on its own screen and the
  node gate decides. Tier 4 is impossible regardless.
- **Cautious defaults:** a new app gets basic-signal reads only.
- **Revoke any time,** with a per-app access log.

Signal K is the precedent and the warning: an open data standard plus a reference server
plus apps worked for boats, but its written spec stalled while the server defined the
behaviour. So the spec (in `ostler-feed`, decision 29) and the gateway app ship together,
with conformance tests.

### 3.2 Gateway roles and sync

The gateway job is the same wherever it runs: the node link, the VISS server, the
permissions controller and External MQTT. Two hosts can do it.

- **On the Brain,** the Python service does the gateway job. Apps on the network make
  access requests, and its settings live in the Brain's web console.
- **On Android,** the gateway app does it.

Which one is the server depends on how the device is connected:

| Connection | Server | The Android gateway app |
|---|---|---|
| Android straight to a node | the Android gateway app | is the server |
| Android to a Brain | the Brain | is a client: it forwards requests from apps on that device to the Brain |

- **One server per node.** Only one server owns a node at a time.
- **One permission set, synced.** The server holds the permissions and enforces them. The
  Android gateway apps and the cloud view show and edit that same set. Turning a
  permission off on the Android app turns it off on the Brain, and the same goes for the
  cloud view.
- **Open: failover.** What happens when the Brain drops out mid-drive (does the Android
  gateway take over the node, and how is the permission set handed over and merged back)
  is open. Feed spec v0.1 records it as an open item.

## 4. Theming, kept and re-targeted

The owner likes the theming. Without a web OS it lives in three places:

1. **A token pack** (the 22 built-in themes from the design bundle, as data) loaded by the
   shared app template. The gateway app holds the active theme, so every Ostler app follows
   it. "Follow system colours" (Material You) is an option.
2. **Gauge styles:** gauge faces, needles and dial layouts as options on in-app gauges and
   the feed widget, bound to VSS paths so they work in any vehicle (RealDash's channel-file
   problem avoided).
3. **Skins for the Ostler apps' own pages** (the WebView pages can still take CSS against
   the documented hooks), plus a launcher skin if a launcher is ever built.

The theme engine spec's six-layer skin engine is parked; its token schema, theme options,
safety render check, protected surfaces and required parts carry over. Safety colours stay
restylable under the render check (decision 18).

## 5. Interop

The output bridges of decision 36, in order of value for cost
([ecosystem](direction_headunit_ecosystem.md) §6). All are read-only views of the feed:

1. **RealDash output:** its CAN-over-TCP protocol is public; one channel file gives every
   RealDash dashboard the car's data.
2. **Home Assistant and OVMS** through the gateway's External MQTT menu.
3. **CAN-box emulation** (Raise, Simple Soft), so the head unit's own screens show doors and
   reverse.
4. **ELM327/OBD emulation** over Bluetooth or Wi-Fi, so any OBD app reads the feed.
5. **Torque as an input** for OBD-only cars.

## 6. Risks

- **Sleep and wake on head units.** They force-stop apps 20–30 s after ignition off;
  stopped apps miss `BOOT_COMPLETED`. Every wake is a cold start; per-unit setup guidance
  is needed. Bench test on two units first.
- **Widgets are slow by design.** About 1 Hz pushed from a running service; no live gauges
  on the home screen.
- **Play policy:** foreground-service declarations with a video; developer verification,
  which also covers sideloaded apps, from 2027.
- **Signal K's trap:** a spec that lags the implementation. Conformance tests from day one.
- **A new language (Kotlin)** for one owner with agents; the hybrid route limits it to the
  shells.
- **Migrating the bus.** The node firmware and NodeSource speak MQTT today; the move to VISS
  is staged, with both running side by side until each consumer has moved (ADR-0051).

## 7. What changes in the repo

Applied on 2026-10-08 with the owner's approval:

- [ADR-0049](../../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md) is
  accepted. It supersedes ADR-0046's OS boundary (keeping its safety list and hard lines)
  and ADR-0042's one-app rule, and parks ADR-0048.
- [ADR-0050](../../decisions/adr-0050-kotlin-for-the-android-app-tier.md) adds Kotlin for
  the Android app tier (amends ADR-0035).
- [ADR-0051](../../decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md) makes
  VISS v3 the core protocol and MQTT external only (amends ADR-0026, ADR-0027 and the
  module-bus spec).
- ADR-0039 gains the USB serial head-unit link; ADR-0034 the repo changes.
- The app-model, app UI model and Store specs are superseded in part (the Store becomes a
  catalogue of packs and themes as data); the launcher spec is parked; the head-unit apps
  spec drops Radio, Media, Phone and Navigation; the theme engine spec is re-scoped (§4).
- GOALS, SCOPE and README carry the new mission.

Follow-ups, not in this round: the designer brief and `screens.json` re-scoped to per-app
screens; the `ostler-feed` spec repo; the migration spec for the legacy bus; code.

## 8. Decisions (approved 2026-10-08)

The owner approved every item on 2026-10-08 ("I agree with everything"). Items marked
*revised* follow the owner's changes; 31–37 were added from them. The alternatives are kept
as history.

**What Ostler is**
1. **Direction:** an open diagnostic and logging platform with an open vehicle-data feed,
   one gateway app plus separate apps, no launcher, built the hybrid way. *Approved,
   revised.* *alt:* keep the web OS.
2. **Mission:** "an open diagnostic and logging platform with an open vehicle-data feed
   (VISS)". *Approved, revised.* *alt:* rewrite it together.
3. **Supersede ADR-0046's OS boundary and ADR-0042's one-app rule** with ADR-0049, keeping
   ADR-0046's safety list and hard lines. *Approved.* *alt:* amend them in place.

**The standard**
4. **Full VISS v3 is the core protocol** over VSS, not a profile beside our own API
   (ADR-0051). *Approved, revised.* *alt:* our own JSON over MQTT.
5. **Android:** apps get a scoped token from the gateway (package name and signing key),
   then speak VISS over a loopback WebSocket. *Approved, revised.* *alt:* a typed AIDL API.
6. **LAN and every other hop:** VISS over `wss` with mDNS, gRPC or HTTP where they fit; MQTT
   is external only. *Approved, revised.* *alt:* MQTT 5 for apps too.
7. **Writes only as requests** through the gateway and its own confirmation, decided by the
   node gate. *Approved.* *alt:* no third-party writes at all.
8. **Licences:** the spec CC BY-SA, the client SDKs Apache 2.0, the gateway app AGPL.
   *Approved.* *alt:* everything AGPL.
9. **Offer the Android binding to COVESA** once it works. *Approved.* *alt:* keep it ours.

**Apps and hosts**
10. **First hosts:** Android head units and Android phones, minimum Android 10. *Approved.*
    *alt:* Android 12 minimum.
11. **One required gateway app:** connections (node, Brain, adapters, pairing), the gate
    client, driving state, alerts, the permissions controller and the feed. *Approved,
    revised.* *alt:* each app talks to the node itself.
12. **Apps:** the gateway app; Diagnostics with Decode lab merged; Trips; Security;
    Maintenance as a separate app; add-ons (friends' live map, Social, the Meshtastic and
    MeshCore mesh) as completely separate apps. No widget apps. *Approved, revised.* *alt:*
    Diagnostics only first.
13. **Build the hybrid way:** Kotlin shells around our React pages, native where it pays.
    *Approved.* *alt:* fully native (Jetpack Compose) from the start.
14. **Kotlin ADR** under ADR-0035 (ADR-0050). *Approved.* *alt:* a cross-platform toolkit
    (Flutter or React Native).
15. **Drop own Radio, Media, Phone and Navigation apps;** feed Waze, Spotify and the head
    unit's apps instead. *Approved.* *alt:* keep them on the roadmap.
16. **Launcher optional and parked** until the bench test (decision 23); ADR-0048 parked.
    *Approved, revised.* *alt:* build "Ostler Home" now.
17. **A normal feed widget** at about 1 Hz in the gateway app; live views stay inside the
    apps; no widget apps. *Approved, revised.* *alt:* a Dash app with widget packs.

**Theming and design**
18. **Safety colours:** restylable under the render check, as the openness round decided.
    *Approved.* *alt:* fixed again in native apps.
19. **Theme work re-targeted** to token packs, gauge styles and app skins through the shared
    template (§4); the six-layer skin engine parked. *Approved.* *alt:* keep the full skin
    engine for the WebView pages.
20. **Re-scope the brief** to per-app screens; drop the launcher, Store and app-frame
    screens. *Approved.* *alt:* keep the full brief for later.

**Hardware**
21. **The Brain is optional,** not needed for v1. *Approved.* *alt:* the Brain stays
    required.
22. **Head-unit link to the node:** USB serial first, BLE for phones, Wi-Fi as fallback;
    amend ADR-0039. *Approved.* *alt:* Wi-Fi only.
23. **Bench test two head units** (one FYT UIS7862, one UIS7870 such as a Dudu7) for sleep,
    the feed widget and the USB link before building. *Approved.* *alt:* build first.

**Interop and distribution**
24. **RealDash output first,** then Home Assistant, then CAN-box emulation. *Approved.*
    *alt:* Home Assistant first.
25. **Distribution:** Play Store plus F-Droid plus direct APK; register as a verified
    developer. *Approved.* *alt:* direct APK only.
26. **No Store of our own** for code; the Store spec becomes a catalogue of packs and themes
    as data. *Approved.* *alt:* drop the Store spec entirely.

**Housekeeping**
27. **PR #65:** merge it now with a note that the theme engine is re-scoped by ADR-0049.
    *Approved.* *alt:* rebase it on ADR-0049 first.
28. **The app repos:** keep Diagnostics (Decode lab merged into it), Trips, Security,
    Maintenance, Map, Social and Community as future Android projects; archive Radio, Audio,
    Media, Camera, Navigation and Phone; keep the widget (feed widget layouts and gauge
    styles), theme and catalogue repos as data repos. *Approved, revised.* *alt:* archive
    everything except the first three apps.
29. **A spec repo** `ostler-feed` for the VISS profile, with conformance tests. *Approved.*
    *alt:* keep it in `ostler`.
30. **UX first still applies** to the gateway app and the first apps: a short brief per app
    before building. *Approved.* *alt:* build the gateway app straight from the feed spec.

**Added from the owner's changes (approved 2026-10-08)**
31. **The gateway's permissions controller** (§3.1): identity first, per-app toggles mapped
    to ADR-0029 data classes and ADR-0033 categories and tiers, a scoped VISS access token,
    writes as requests, cautious defaults, revoke any time with a per-app access log.
32. **VISS v3 on every signal hop** (node to gateway, Brain to apps, gateway to apps); the
    MQTT module bus and SSE `/events` are legacy and migrated over time (ADR-0051).
33. **External MQTT:** a menu in the gateway app publishes to an outside broker for Home
    Assistant discovery, OVMS topics and others; MQTT is external only.
34. **Cameras and meshes in the feed:** cameras listed in VISS metadata, pointing to RTSP or
    WebRTC streams; Meshtastic and MeshCore as transports and bridges.
35. **One shared app template** (Kotlin shell, VISS client, theme-pack loader), so every
    Ostler app follows the active theme from the gateway app (ADR-0050).
36. **Output bridges:** RealDash TCP stream, ELM327/OBD emulation (Bluetooth or Wi-Fi),
    CAN-box emulation (Raise, Simple Soft), Home Assistant and OVMS via External MQTT. All
    are read-only views; nothing coming back from them reaches the car except through the
    gate.
37. **The normal feed widget:** a standard Android widget at about 1 Hz, from the gateway
    app; live views stay inside the apps; no widget apps.
38. **The gateway job runs on the Brain too:** the Brain's Python service does the same job
    as the Android gateway app (node link, VISS server, permissions, External MQTT); apps
    on the network make access requests; settings live in the web console (§3.2).
39. **Who is the server:** Android straight to a node, the Android gateway app is the
    server; Android to a Brain, the Brain is the server and the Android gateway is a client
    that forwards requests from apps on that device. One server owns a node at a time.
40. **Everything is synced:** one permission set, held and enforced by the server and
    shown and edited the same from the Android gateway apps, the Brain console and the
    cloud view. Failover when the Brain drops out mid-drive is open, for Feed spec v0.1.

## Changelog

- 2026-10-08 — v0.1, draft: synthesis of the five direction notes with 30 owner decisions.
- 2026-10-08 — v1.0, approved by the owner ("I agree with everything", with changes): §2
  and §3 rewritten (diagnostic and logging platform, VISS v3 as the core on every hop, MQTT
  external only, the gateway app and its permissions controller, the app list, no widget
  apps, launcher parked); §4, §5 and §7 updated; decisions 1–30 approved, items 1, 2, 4–6,
  11, 12, 16, 17 and 28 revised; decisions 31–37 added.
- 2026-10-08 — v1.1: §3.2 gateway roles and sync added (owner, 2026-10-08): the Brain does
  the same gateway job; Android direct to a node is the server, via a Brain a client; one
  synced permission set; decisions 38–40; Brain failover open.
