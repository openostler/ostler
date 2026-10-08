---
title: "Direction research: a standard vehicle feed for every app (head unit and phone)"
area: references
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-app-model-design.md, api/openapi.yaml, api/asyncapi.yaml, references/research/ecosystem_architecture.md, references/research/standards.md, references/research/obd_telematics_apps.md, references/research/ovms.md]
summary: >
  Recommendation: the "Ostler feed" should be a small profile of COVESA VISS 3.2 over the VSS
  tree we already pin, not a new protocol. It has two bindings. On Android, one host app
  (the node link) serves VISS JSON messages through a bound service with an AIDL interface,
  plus a thin client library. On the LAN, the Brain or node serves VISS over secure
  WebSocket, found by mDNS. Phones reach the car through the host app, never over raw
  Bluetooth. Reads and subscriptions follow VISS. Writes do not: the profile has one
  Ostler action method that hands off to ADR-0033 and the node gate, and it never carries a
  grant. Pairing and access copy Signal K's access-request model, with tokens scoped by
  category and data class. The module bus stays internal, and MQTT, Home Assistant and OVMS
  stay exports. KUKSA, the Vehicle HAL, Torque and RealDash are references or adapters.
---

# A standard vehicle feed for every app

## Recommendation

**Adopt VISS, profile it small, and bind it to Android.** The feed is "VISS 3.2 on VSS
6.1, Ostler profile 1": a named subset of COVESA VISS plus two bindings and one extension.
We define only what VISS leaves open: an Android binding, discovery, pairing, the action
hand-off and four optional data-point fields.

| Layer | Choice | We define |
|---|---|---|
| Names | COVESA VSS 6.1 plus `Vehicle.Ostler.*` ([ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)) | nothing new |
| Messages | VISS 3.2 Core JSON: `get`, `subscribe`, `unsubscribe`, subscription events, signal discovery, `Server` tree | the subset (below) and four optional data-point fields |
| Android binding | a bound service, AIDL carrying unaltered VISS JSON strings, plus `ostler-feed-android` (a small client library) | the AIDL file, the permission and the consent flow |
| LAN binding | VISS over `wss` with the `VISSv3` subprotocol, as the spec defines it | the mDNS service type and TXT keys |
| Phone ↔ car | the Ostler host app holds the BLE or Wi-Fi link to the node and re-serves the feed through the Android binding | nothing for third parties |
| Writes | **no VISS `set` on car paths**; one `ostler.action` request that the host turns into an ADR-0033 action | the method, its outcomes and the hand-off to the approval UI |
| Access | VISS `authorization` JWTs, issued after a Signal K-style access request that the owner approves | scopes = ADR-0033 categories + ADR-0029 data classes |
| Versioning | VISS subprotocol, `Server` tree feature names, VSS pin, AIDL `getVersion()` | `Server.Support.Ostler.Profile` |

**Transports per host.**

1. **Android, same device (head unit or phone): a bound service.** A single Ostler host app
   (the "node link" system service of [ADR-0046](../../decisions/adr-0046-empty-os-every-app-an-add-on.md))
   exports `IOstlerFeed`. Its methods are `int getVersion()`,
   `String request(String vissJson)`, `void open(IOstlerFeedListener l)` and
   `void close()`, and the listener has `onMessage(String vissJson)`. Strings carry
   unaltered VISS messages, which the VISS transport text allows for any transport
   ([VISS 3.2 Transport §1](https://raw.githack.com/COVESA/vehicle-information-service-specification/v3.2/spec/VISSv3.2_Transport.html)).
   A **read-only `ContentProvider`** (`content://tech.ostler.feed/snapshot/<VSS path>`,
   with `ContentObserver` change notifications) serves AppWidgets and automation tools,
   which cannot hold a live binding. In-process apps (the host's own screens) call the
   same library directly.
2. **LAN to a Brain or node: VISS over secure WebSocket.** The Brain serves it beside its
   HTTP API, from the same snapshot the SSE stream uses. A node may serve it later on
   Ostler Diagnostics alone. TLS trust follows ADR-0021 (local HTTPS). VISS requires
   `wss` and the `VISSv3` subprotocol, with default port 6443.
3. **MQTT is not the app feed.** The module bus (`ostler/v1/<vid>/<device>/…`) stays the
   internal bus, with per-device mTLS and ACLs. Home Assistant discovery and the OVMS tree
   stay **exports**, generated as today. VISS-over-MQTT (`VID/Vehicle` request topics) is
   for cloud relays, and we do not need it now.
4. **Bluetooth to a phone.** It is not a public binding. The node's BLE link carries the
   host app's own traffic (pairing, approvals, grants, as today). Third-party phone apps
   bind to the host app on the phone. This keeps one BLE central, one pairing and one gate
   path.

**Discovery.** mDNS/DNS-SD service `_ostler-feed._tcp` (unregistered until profile 1 is
frozen, like `_ostler-mod._tcp`), with TXT `txtvers=1`, `proto=VISSv3`, `profile=1`,
`vss=6.1`, `path=/viss` and `pr=0|1` (paired). There is no VIN, no `vid` and no owner name
in TXT. On Android, apps find the host by package (a `<queries>` entry), not mDNS.

**Auth and pairing.**
- **Android:** the service is guarded by a custom permission `tech.ostler.permission.FEED`,
  but the real gate is the host's own consent. On the first `open()`, the host reads the
  caller's UID, package and signing-certificate SHA-256 and shows **"Allow <app> to read
  the car?"**, listing the categories and data classes the app's manifest asks for. The
  decision is pinned to the package and certificate, and revocable in Settings. Google
  rates `normal` and `dangerous` custom permissions as weak protection
  ([Android custom-permission risks](https://developer.android.com/privacy-and-security/risks/custom-permissions)),
  and a `signature` permission would shut out third parties.
- **LAN:** a client POSTs an access request (Signal K's model:
  [access requests](https://signalk.org/specification/1.7.0/doc/access_requests.html)).
  The owner approves it on the head unit or a paired phone, and the Brain issues a JWT.
  The client puts it in VISS's `authorization` field. The token's claims list the
  categories (Read by default), data classes (`location` only if granted), `vid` scope and
  expiry. We implement only the client-to-server part of VISS access control, which is the
  only mandatory part; the Access Grant Token and Access Token servers, the purpose lists
  and the consent framework are not needed in a car with one owner.
- Remote paths (Tailscale, cloud) stay read-only per ADR-0033 §6.

**Read and subscribe.**
- Supported: `get` (single tree, wildcard paths filter), `subscribe` with the `change`
  (with a minimum interval) and `timebased` filters, `unsubscribe`, signal discovery
  (metadata), and the `Server` capability tree.
- Not in profile 1: `history`, `curvelog`, `range`, file transfer and compression. Logs
  stay on the Logs API.
- **Data point:** VISS `{"value": "<string>", "ts": "<RFC 3339>"}`. VISS carries numbers
  as strings, unlike our module bus, so the library converts. Optional Ostler members are
  `c` (`proven` or `candidate`, never raised), `stale` (bool), `src`
  (`<device>/<source>`) and `unit` when it differs from the VSS unit. They are declared as
  the `Ostler` feature in the `Server` tree so strict clients know about them.
- Units are always the VSS unit. Values are never fabricated: a missing signal is VISS
  404 `unavailable_data` (CONSTITUTION data honesty), and a stale one keeps its old `ts`.
- The profile serves only VSS and reviewed `Vehicle.Ostler.*` paths; pack-private fields
  (`<pack>.<module>.<field>`) stay inside Ostler apps (open question 4).

**Actions and writes.**
- VISS `set` on any car-bus or add-on actuator path is refused (`403`, reason
  `use_ostler_action`). Signal K hit this problem: it found its generic v1 write ("PUT")
  "vague and confusing", with plugins overwriting related paths, and moved to operation
  APIs ([Signal K developer notes](https://demo.signalk.org/documentation/Developing.html)).
- `{"action": "ostler.action", "id": "<manifest action id>", "params": {…},
  "requestId": …}` returns a handle and then outcomes in the module-bus shape (`accepted`,
  `refused`, `running`, `done`, `expired`, `state_changed`, `failed`).
- The host evaluates ADR-0033's one rule. Tier 0–1 in a granted category runs without a
  prompt where ADR-0033 allows it. Tier 2–3 return `needs_approval` with an Android intent
  (or a URL on the LAN) that opens **the host's** approval UI. The app never sees a
  challenge or a grant, and the node gate re-checks everything at execution (module-bus
  §9–§10). Tier 4 is always refused.
- Remote, MQTT and Home Assistant paths never reach Tier 2+ (ADR-0033 Amendments).

**Versioning.**
- Wire: the VISS subprotocol (`VISSv3`) on WebSocket; `getVersion()` on AIDL, where methods
  are only ever appended (Torque's AIDL followed the same rule for a decade).
- Profile: `Server.Support.Ostler.Profile = "1"`; additive members only within a major.
- Names: the VSS pin (`vss=6.1` in TXT, and the tree version node, which VISS says is
  never access-controlled); a pin bump is its own PR, as ADR-0016 requires.
- The library uses SemVer; an app declares `"feed": "^1"` in its manifest.

**How a third-party app uses it (Android).**
1. Add `ostler-feed-android` (Apache-licensed, so closed apps can use it; open question 2)
   and a `<queries><package android:name="tech.ostler.link"/></queries>` entry.
2. `OstlerFeed.connect(context)`, which binds the service, triggers consent and returns
   the `Server` tree.
3. `feed.subscribe(listOf("Vehicle.Speed", "Vehicle.Powertrain.CombustionEngine.ECT"),
   minIntervalMs = 200) { dp -> … }`.
4. Widgets read the `ContentProvider` snapshot in `onUpdate`.
5. Optional: `feed.action("security.arm")`, which opens Ostler's approval sheet if needed.
6. With no host app installed, the library offers the Play Store or F-Droid link. On a LAN
   (desktop or Linux), apps use any WebSocket VISS client.

## Evidence

### What the repo already has

- **VSS is adopted and pinned** ([ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)).
  `metrics.json` is generated from `vss/ostler.vspec` and already carries the OVMS and
  Home Assistant aliases. The feed needs no new namespace.
- **ADR-0017 already chose VISS's payload shape** (`{value, ts}`) as reference-only and put
  Velocitas on the avoid list ([ADR-0017](../../decisions/adr-0017-open-standards-first.md)).
  The ecosystem research rated VISS v3 ADOPT-LATER as "the external vehicle-data API
  shape" and KUKSA reference-only
  ([ecosystem §2](ecosystem_architecture.md)). This note says "later" is now: an
  external app feed is exactly the client it waited for. That is a new outbound data path,
  so it needs its own ADR (ADR-0017 rule).
- **The module bus is internal by design.** Its rules are own-topics-only ACLs, mTLS per
  device, retained `vss/<leaf>` at QoS 0, and requests on the requester's own topics with
  grants minted only by paired keys
  ([module-bus spec §2, §9, §10, §13](../../specs/2026-10-06-module-bus-messages-design.md)).
  Third-party apps on that bus would need certificates and ACL rows each. A VISS edge on
  the Brain or host is the right seam.
- **The app SDK already promises a VISS-shaped `signals.subscribe`**, returning
  `{value, ts, confidence, stale}`, and an `actions.request` where "the app never sees a
  grant" ([app-model §6](../../specs/2026-10-06-app-model-design.md)). The Android binding
  is the native form of that same contract.
- **`api/asyncapi.yaml`** documents the SSE snapshot stream and the node channels. A
  `viss` channel would sit beside them, with the Data Point schema shared by `$ref`.
- **ADR-0033** gives the categories, tiers, roles, the kiosk session (Read and Comfort
  only) and the local and remote rules that the action method must call, not copy
  ([ADR-0033](../../decisions/adr-0033-action-categories-and-approvals.md)).

### COVESA VISS (v2, v3.0 to v3.2)

- **Status.** Latest is **v3.2** (repo merge 2026-09-22), which is backwards compatible with
  v3.0 and adds "forests" of trees through the Hierarchical Information Model (HIM).
  Mozilla Public License 2.0. The maintainers are from Ford and ETRI, and the W3C group closed in February
  2024, so the work is now at COVESA
  ([repo README](https://github.com/COVESA/vehicle-information-service-specification)).
  AUTOSAR's Automotive API Gateway (R24-11) is based on VISS v2 (same README), so it has
  OEM weight.
- **Transports.** v1 was WebSocket only; v2 added HTTP, MQTT and access control; v3 added
  gRPC and "simplified addition of other transport protocols by placing the normative
  requirement on the message payload only". v3.2 lists HTTP, WebSocket, gRPC, Unix domain
  sockets and MQTT ([Transport](https://raw.githack.com/COVESA/vehicle-information-service-specification/v3.2/spec/VISSv3.2_Transport.html)).
  WebSocket must be `wss` with subprotocol `VISSv3` and default port 6443. MQTT wraps
  requests as `{"topic", "request"}` on `VID/Vehicle`. A UDS socket file is named in the
  `Server` tree. **An AIDL binding that carries the unaltered JSON fits the rule.**
- **Messages** ([Core](https://raw.githack.com/COVESA/vehicle-information-service-specification/v3.2/spec/VISSv3.2_Core.html)):
  Read and Update are mandatory and Subscribe is optional. Filters are paths, history,
  timebased, range, change, curvelog and metadata. A data point is `{value, ts}` with the
  **value as a string**. Errors are `{number, reason, description}`. The `Server` tree
  declares optional features and extensions.
- **Access control** is OAuth-inspired. An Access Grant Token server authenticates a role;
  an Access Token server issues tokens for a **purpose**; consent is optional. The roles
  are users (OEM, Dealer, Independent, Owner, Driver, Passenger), applications (OEM, Third
  Party) and devices (Vehicle, Nomadic, Cloud). Only the client-to-server part is
  mandatory, so a JWT in `authorization` is conformant (Core, Access Control Model).
- **Fit:** good for reads and subscriptions. It is weak for writes: `set` writes a value
  and has no notion of tiers, confirmation, driving state or a gate. Hence the action
  extension.
- **Reference server:** COVESA `vissr` (tags up to v3.2.1), written in Go. We read it and do
  not ship it (ADR-0002); the Brain's VISS edge is a small stdlib-plus-asyncio handler over
  the snapshot.

### Eclipse KUKSA.val databroker

- A Rust VSS server under the Apache 2.0 licence, "<4 MB statically compiled". It serves gRPC
  `kuksa.val.v2` (v1 is deprecated) and a **subset of VISS v2 over WebSocket** (port 8090,
  `--enable-viss`), with JWT authorization by public key. The latest tag is 0.7.1
  (2026-08-26) ([repo](https://github.com/eclipse-kuksa/kuksa-databroker), user guide).
- **Android SDK:** `org.eclipse.kuksa:kuksa-sdk` on Maven Central, Apache 2.0 licence, latest tag
  v0.2.3 (2026-09-24). It connects over a gRPC `ManagedChannel` to a databroker
  ([repo](https://github.com/eclipse-kuksa/kuksa-android-sdk)). That means a network
  socket, not Android IPC, and a gRPC dependency in every app.
- **Verdict: reference-only, plus an optional adapter.** It proves VSS + JWT + VISS-subset
  works. Its VISS v2 subset could be a conformance peer for our endpoint. Running it on
  the Brain still breaks ADR-0002; a KUKSA-to-Ostler bridge stays a possible add-on
  ([ecosystem §2](ecosystem_architecture.md) also notes a 2026 crash CVE).

### Eclipse SDV and Velocitas

- Velocitas is a template and SDK for containerised "vehicle apps" on KUKSA. It had one
  project release (0.1.0, 2023), the Python SDK is "in alpha", and its last commit was in
  July 2025. The Eclipse metrics page shows 4 commits by 2 people in 12 months
  ([Velocitas](https://eclipse.dev/velocitas/), [metrics](https://metrics.eclipse.org/projects/automotive.velocitas/)).
- **Verdict: avoid** (unchanged from ADR-0017). It targets OEM container platforms, not
  Android head units.

### Android Vehicle HAL and the Car API

- `CarPropertyManager` and the Vehicle HAL exist **only on Android Automotive OS**.
  Aftermarket head units (the Dudu7 class in the owner's chat) run ordinary Android with a
  vendor MCU service, not AAOS. Feeding a VHAL needs the system image, which we do not own.
- **Permission model:** non-system apps reach the VHAL only through the car service with
  a permission. `CAR_SPEED` is `dangerous` (a runtime prompt, in the location group);
  `CAR_MILEAGE` and vendor extensions are `signature|privileged`
  ([AOSP vehicle system isolation](https://source.android.com/docs/automotive/security/vehicle_system_isolation)).
  The Car App Library's `CarHardwareManager` exposes a few values (speed, energy level,
  model, mileage) on Android Auto and AAOS, each with its own permission
  ([Car hardware APIs](https://developer.android.com/training/cars/apps/library/car-hardware-api)).
- **Verdict: reference-only now; an adapter later.** Copy its ideas: per-property
  permissions, a status on every value (`STATUS_SUCCESS` or unimplemented), "don't assume
  data is available". If Ostler ever runs on an AAOS build, an adapter maps VSS to
  `VehiclePropertyIds`.

### Android IPC patterns for a local feed

| Pattern | Good for | Limits |
|---|---|---|
| **Bound service + AIDL** | live subscriptions with callbacks, caller identity (`Binder.getCallingUid`), request and response | the caller must bind; Android 11+ needs a `<queries>` entry for the host package ([package visibility](https://developer.android.com/training/package-visibility/declaring)) |
| **ContentProvider** | snapshots, widgets, automation tools, `ContentObserver` change notifications, URI grants | poor for 10–50 Hz streams |
| **Broadcast intents** | coarse events (Torque's `OBD_CONNECTED`, `ALARM_TRIGGERED`) | implicit broadcasts are restricted since Android 8; anyone can listen; no back-pressure |
| **Messenger** | simple one-way messages | no typed contract |

**Choice:** AIDL for live data and actions, a ContentProvider for snapshots, and at most
two broadcasts (`FEED_AVAILABLE`, `FEED_GONE`), which carry no values.

### Torque Pro's plugin API (the de facto Android OBD feed)

- `org.prowl.torque.remote.ITorqueService` is one AIDL file at
  [torque-bhp.com/api/ITorqueService.aidl](https://torque-bhp.com/api/ITorqueService.aidl).
  It has `getVersion()` ("will increment each time the API is revised"),
  `listAllPIDs()`, `getPIDValues(String[])` and `getPIDInformation(...)`, plus methods
  that **write**: `sendPIDData` (plugins add PIDs), `sendCommandGetResponse(header,
  command)` (raw OBD modes 01–0A, 21–23, anything else with "full permissions") and
  `requestExclusiveLock` on the adapter. Broadcasts announce connection, lifecycle and
  alarms ([plugin wiki](https://wiki.torque-bhp.com/view/PluginDocumentation)).
- **What worked:** one versioned AIDL file and append-only methods; plugins as separate
  APKs; a whole ecosystem (TorqueScan, Track Recorder, per-make "Advanced" plugins).
- **What didn't:** names are PIDs (`0x0c`, `0xff1001`), not meanings; there is no
  timestamp per value (only `getPIDUpdateTime`); there is no auth beyond a settings
  checkbox; and raw bus access goes to any plugin with "full permissions". Its live web
  upload format "rots" ([telematics research](obd_telematics_apps.md)).
- **For us:** copy the shape (one AIDL, append-only, `getVersion`). Never copy the raw
  command path: the node gate and ADR-0033 forbid it.

### RealDash CAN input

- A byte-stream framing (`44 33 22 11` + LE id + 8 bytes; `66 33 22` frames up to 64 bytes
  with CRC32; text frames; `SET VALUE` frames back to the device), mapped to channels by
  a user XML file. Unlicense ([protocol](https://github.com/janimm/RealDash-extras/blob/master/RealDash-CAN/realdash-can-protocol.md)).
  It travels over serial, Bluetooth or TCP to an address the user enters
  ([canbus research](canbus_headunit.md); WiCAN serves it).
- **For us:** an **export adapter** (a Brain or host app TCP port that speaks RealDash CAN
  from VSS values with a generated XML) so RealDash users get Ostler data. RealDash's
  `SET VALUE` frames are **refused** (no writes from a dash). It is not a model for the
  feed: it has frames, not meanings.

### OVMS v3 MQTT

- `ovms/<user>/<vehicle>/metric/v/b/soc` with one retained topic per metric, and
  `client/<cid>/command/<id>` → `response/<id>` carrying shell-style command strings
  ([OVMS research](ovms.md)).
- **For us:** it stays the opt-in alias **export** (ADR-0017, ADR-0016's reverse map). Its
  command channel shows the risk of free-text commands over MQTT: our MQTT exports stay
  below Tier 2.

### Home Assistant MQTT discovery

- `homeassistant/device/<id>/config` with required `dev` and `o` blocks and a `cmps` map;
  a birth message on `homeassistant/status`; availability from a will. HA now advises
  sending configs on the birth message rather than retaining them, to avoid "ghost
  entities" ([HA MQTT](https://www.home-assistant.io/integrations/mqtt/)).
- **For us:** unchanged. It is an export generated from `metrics.json`, not an app feed.
  Republish on birth.

### MQTT 5

- The module bus needs MQTT 5's wills, expiry, Correlation Data and Response Topic
  ([module-bus §2](../../specs/2026-10-06-module-bus-messages-design.md)).
- As an **app** feed it is worse than VISS. Every app needs a broker account and an ACL;
  subscriptions are topic filters with no rate or change filter; there is no standard
  read or metadata call; and Android apps would carry an MQTT client and keep a socket
  open. VISS's MQTT mapping exists for cloud relays.

### Signal K (the marine precedent)

- **What it is:** an open data model (JSON Schema; docs CC BY-SA, code Apache 2.0), a
  reference server (Node.js), and apps as server plugins and web apps installed from the
  server's own catalogue. Discovery uses `_signalk-http._tcp` and `_signalk-ws._tcp` with
  TXT `txtvers`, `roles`, `self`, `swname` and `swvers`
  ([connection](https://signalk.org/specification/1.7.0/doc/connection.html)).
  Streaming uses deltas over WebSocket with `subscribe` by context and path, plus a "full"
  model for first load
  ([subscriptions](https://signalk.org/specification/1.7.0/doc/subscription_protocol.html)).
  Devices get tokens by an access request that an admin approves
  ([access requests](https://signalk.org/specification/1.7.0/doc/access_requests.html)).
- **What worked:**
  - **A reference server people can install** on hardware they already own. Victron ships
    a Signal K server in "Venus OS Large" on its GX devices
    ([Victron](https://www.victronenergy.com/live/venus-os:large)).
  - Chart apps (iSailor, Navionics, Aqua Map) read its Wi-Fi feed, so its value came
    from **bridging the old buses** (NMEA 0183 and 2000) into one JSON model apps could
    read. That is our position with K-line and CAN.
  - The access-request flow fits a headless device and an owner on a phone.
  - mDNS discovery with versioned TXT keys.
  - SI units everywhere and metadata (display names, zones) beside values.
- **What didn't:**
  - **The written spec stalled while the server moved on.** Spec 1.7.0 came out in April
    2022 and 1.7.1 in March 2023; nothing followed until **1.8.0 in February 2026** (git
    tags of [SignalK/specification](https://github.com/SignalK/specification)). Meanwhile
    server v2 added modular REST APIs, so behaviour came to be defined by the server, not
    the spec.
  - **Generic writes failed.** The v2 docs say related paths must change together, several
    plugins could write the same paths and make the model invalid, and the v1 PUT model
    was "vague and confusing". v2 moved to operation APIs (course, resources, history)
    whose paths "should not be updated directly by any other plugin"
    ([developer notes](https://demo.signalk.org/documentation/Developing.html)).
  - **Its own tree, not a shared one,** so mainstream instrument makers kept their own
    buses. Signal K reached apps through Wi-Fi bridges more than through native support
    (Victron's own page says it gives no support for solutions built on it).
- **Lessons we take:**
  1. Ship the feed and a reference host together, versioned together, and keep the spec
     conformance-tested against the host (as `test_api_contracts.py` does for OpenAPI).
  2. Writes are operations with owners, never generic path writes.
  3. Use a shared tree (VSS) and a shared protocol (VISS) so we are not the only
     implementation.
  4. Copy the access-request UX and mDNS TXT discipline.

### Standards scorecard

| Candidate | Verdict for the feed | Role |
|---|---|---|
| COVESA VSS 6.1 | **ADOPT** (already) | names, units, metadata |
| COVESA VISS 3.2 | **ADOPT as a profile** | message layer: get, subscribe, discovery, errors, server tree |
| VISS over WebSocket | **ADOPT** | the LAN binding |
| VISS over MQTT, gRPC, HTTP | later or no | cloud relay only if needed |
| Android bound service + AIDL | **ADOPT** (our binding) | on-device feed |
| Android ContentProvider | **ADOPT** (snapshot) | widgets, automation |
| mDNS / DNS-SD | **ADOPT** (already) | `_ostler-feed._tcp` |
| JWT (RFC 7519) | **ADOPT** | VISS `authorization` |
| KUKSA databroker and Android SDK | REFERENCE, optional adapter | conformance peer |
| Velocitas | AVOID | — |
| AAOS VHAL / CarPropertyManager | REFERENCE, AAOS adapter later | — |
| Torque plugin AIDL | REFERENCE (shape), optional import adapter | — |
| RealDash CAN | EXPORT adapter | read-only out |
| OVMS v3 MQTT, HA discovery | EXPORT (already) | — |
| MQTT 5 | internal bus (already); not the app feed | — |
| Signal K | REFERENCE (precedent) | UX and lessons |

## Open questions for the owner

1. **Adopt VISS as the external feed now (an ADR superseding ADR-0017's reference-only
   line)?** *Recommended: yes.* A new outbound data path needs an ADR anyway, and VISS 3.2
   lets us bind it to Android without inventing messages.
2. **Licence of the client library and AIDL file.** *Recommended: the Apache 2.0 licence for
   `ostler-feed-android` and the profile text*, so closed-source apps (Waze-class, RealDash)
   can adopt it. The host app stays under the project's AGPL licence.
3. **Which app hosts the feed on Android?** *Recommended: one small system-like host
   ("Ostler Link") that owns the node connection, consent and approvals.* Every other
   Ostler app, first-party included, is a feed client like any third party.
4. **Expose pack-private fields?** *Recommended: no in profile 1.* Only VSS and reviewed
   `Vehicle.Ostler.*` paths. That forces meanings into the overlay, as ADR-0016 intends.
5. **Third-party actions at all in profile 1?** *Recommended: yes, but only through
   `ostler.action`, with Tier 2+ always handed to the host's approval UI*, and Comfort and
   Security only for apps granted those categories.
6. **VISS numbers as strings.** *Recommended: follow VISS exactly on the wire.* The
   library returns typed values, and the module bus keeps numbers.
7. **Propose the Android binding upstream to COVESA?** *Recommended: yes, after it runs in
   one car.* It fits VISS's "any transport carrying the unaltered payload" rule, and it
   would make the binding a standard rather than ours.
8. **Run a KUKSA conformance check in CI?** *Recommended: later.* Use the KUKSA VISS
   subset as a second implementation to test against once the endpoint exists.
