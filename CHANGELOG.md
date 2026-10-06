---
title: "Changelog"
area: root
status: stable
version: 1.0
updated: 2026-10-06
summary: >
  Notable changes to the Ostler platform in Keep a Changelog 1.1.0 form: the Unreleased U0 repo-hygiene work (REUSE, PEP 639, SECURITY.md, supply-chain CI, ruff/mypy/pre-commit) plus a brief history reconstructed from git, and the versioning policy (SemVer 0.y.z, integer PACK_API_VERSION, VSS pin in vss/VERSION).
---

# Changelog

All notable changes to the Ostler platform (`openostler`) are recorded here. The format
follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Vehicle packs keep
their own changelogs.

## Versioning

- **The platform follows [Semantic Versioning](https://semver.org/).** It stays on
  `0.y.z` until the pack API is frozen: until then a minor bump (`0.y`) may break packs or
  the HTTP API, and a patch bump (`0.y.z`) does not. The version lives in
  `pyproject.toml`; release tags are `v<version>` and must match it.
- **The HTTP/SSE API version is the platform version** (`info.version` in
  `api/openapi.yaml` and `api/asyncapi.yaml`). While on `0.y.z`, a field, parameter or
  route of the API is removed or renamed only after one minor release in which it is
  marked deprecated (OpenAPI `deprecated: true` with `x-ostler-removed-in`, a *Deprecated*
  entry here, and RFC 9745 `Deprecation`/`Link` headers on the responses that carry it).
  Additions can come in any release. Status-code and error-body corrections are listed
  under *Changed*.
- **`PACK_API_VERSION`** (`src/openostler/pack.py`) is an integer major. It changes only
  when the `VehiclePack` contract breaks, and the platform refuses a pack built for
  another value.
- **The COVESA VSS pin** (ADR-0016) is recorded in `vss/VERSION`; changing it is listed
  here.
- Releases carry SBOMs and build provenance ([SECURITY.md](SECURITY.md)).

## [Unreleased]

### Security
- `--public` (and `DiagServer(public=True)`) now refuses to start without an admin
  password: without one every admin route, including signal-store write-back and
  `/capture`, was open on a public bind.
- `POST /community/consent` and `/community/contribute` are refused in public mode, and
  `/community/contribute` (sent from the admin Coverage Map) now needs admin auth.

### Added
- **NodeSource, phase P3: Network page data (backend only)**
  ([spec](specs/2026-10-06-node-source-design.md) v0.5 §11, §16; ADR-0037, ADR-0040). The
  feed also subscribes, read-only, to each device's retained capability `manifest` and its
  role claims `role/#`; `node/cluster.py` builds the cluster view. **`GET /cluster`** (new,
  additive; refused on the public server) returns one row per device seen (kind, variant,
  model, board, firmware and manifest `etag`, "reached via" from the manifest's `links`,
  status, the whole ADR-0040 power record, last seen, its claims) and one row per
  single-holder role (holder, term, since, candidates in the role's order, the last change
  of holder a live message caused). Claims from a device that is offline or asleep, not
  declared by its manifest, not eligible (the brain for the parked broker; an add-on
  module failing ADR-0037 Amendment 14) or not checkable are void and flagged; two gate
  claims on one bus leave it with no holder and an alert; a bus read without a gate shows
  "No gate for this bus". The view is `stale`, never emptied, while the broker is down.
  **The serial source refuses to start beside a node that holds the K-line gate** (owner
  answer 7): `tools/dashboard.py --serial … --mqtt URL` reads the vehicle's retained claims
  and manifests once and refuses when a node claims, or by its manifest is wired to, a
  K-line gate; it also refuses when the broker cannot be checked. Snapshots gain
  `device_info` and `node.fw`/`node.etag`; `status: asleep` from the node's own `status`
  topic (ADR-0037 Amendment 8) now reads as asleep. Node sessions' `meta.json` gains
  `device_info` (firmware and manifest `etag` per device; changes are `node_manifest`
  events). `api/openapi.yaml` (`/cluster`, `Cluster`, `NodeManifest`, `RoleClaim`) and
  `api/asyncapi.yaml` (channels `nodeManifest`, `nodeRole`, `nodeRoleScoped`) follow; no new
  SSE event (spec §8). The firmware publishes no manifest or claims yet: the tests use the
  hand-written `tests/fixtures/node/cluster.jsonl`. No UI view: the Network page comes
  after U1.
- **NodeSource, phase P2: recording and the raw tap**
  ([spec](specs/2026-10-06-node-source-design.md) v0.4 §7, §16; ADR-0032, ADR-0036). A node
  source now records sessions (`tools/dashboard.py --source node` and
  `tests/e2e_server.py --node` record; the D2 cable path is unchanged). Sessions follow the
  node (`logbook/node.py`): one opens only with the node `online`, `awake` or `held`, and a
  live value, so values retained at subscribe time never open or fill one; `status:
  asleep` ends it at once (`end_reason: node_asleep`); `offline` or a lost broker pauses it
  and the 300 s idle rule ends it. Stale values are never written; `vss` readings add the
  columns `<path>` (the selected source) and `<path>@<device>`; identity paths (VIN,
  serials, `VehicleIdentification`) are never written; `Utc` follows the node's synced
  clock (`time_unsynced` in `events.jsonl` otherwise). Node sessions' `meta.json` adds
  `source: "node"`, `devices`, `pack` `{id, version}`, `tap` and `end_reason`
  (`schemas/session-meta.schema.json`). **Raw tap:** while a session is open a second
  connection (`<id>-tap`, session expiry 60 s, clean start per run, resumed on reconnects)
  subscribes to `tap/+/meta` and `tap/+/data` and unsubscribes when it ends (owner answer
  9: no rolling buffer); `logbook/tap.py` writes each batch to
  `<session>/tap/<tap session>.otap`, fsynced at most once a second, logs `seq` gaps
  (`tap_gap`, never filled), skips redeliveries and counts `overflow` events. The
  Brain-side identity check (`node/tap.py`, the node's rule: framed `5A`/`49` replies keep
  service and option then the 8-byte placeholder, unframed runs holding those bytes are
  replaced, CAN ISO-TP identity messages blanked, per-byte records dropped when a scrub is
  due): a header with `scrub: off` is kept unscrubbed only when this install's
  `OSTLER_RECORD_IDENTITY` is set (environment only), and a node that said `on` is
  re-checked. **`GET /sessions/<id>/export?fmt=pcapng`** (`logbook/pcapng.py`, stdlib):
  K-line as `LINKTYPE_USER0`, CAN as `LINKTYPE_CAN_SOCKETCAN`, events as `LINKTYPE_USER1`,
  the node's `t_us` as timestamps, `seq` gaps as comments and drop counts; unframed records
  dropped and identity replies scrubbed whatever the setting. The snapshot's `node.tap` is
  `{session, state, batches}` while subscribed (else null); the replay screen offers "Raw
  tap (pcapng)" for a session with a tap. `api/openapi.yaml` (`NodeTap`, `SessionTap`,
  `SessionMeta` node fields, the `pcapng` format) and `api/asyncapi.yaml` (the tap meta and
  data channels) document them; node sessions replay read-only like any other.
- **CI `broker` job.** Installs Mosquitto (and `openssl`) on the runner and runs the
  `needs_broker` tests with `OSTLER_REQUIRE_BROKER=1`, so they cannot pass by skipping:
  retained and will handling, a resumed 60 s session delivering queued QoS 1 (the tap's
  shape), and NodeSource over mTLS against the spec §5 ACL (`tap/ctl` never delivered, no
  client certificate refused).
- **NodeSource, phase P1: read-only ingest of the node's MQTT messages**
  ([spec](specs/2026-10-06-node-source-design.md) v0.3; ADR-0032). New core packages, stdlib
  only (no new dependency, ADR-0035): `src/openostler/mqtt/` (an MQTT 5 codec for both
  directions and `StdlibMqttClient` behind the `MqttClient` interface: CONNECT with a will
  and session expiry, SUBSCRIBE with No Local, Retain As Published and Retain Handling,
  QoS 0/1, keep-alive with the broker's Server Keep Alive, reconnect with jittered back-off
  1 s doubling to 30 s, TLS 1.2+ with a client certificate) and `src/openostler/node/` (the
  device table: per-signal staleness on the node's own clock, retained-at-subscribe values
  shown as last known, reboots from the payload's `boot` id or, without one, `t_us` going
  backwards, confidence never raised against the Brain's pack store, unknown VSS paths
  flagged, VIN-shaped `vid`s refused, selection for a VSS path from several sources).
  `web/node_source.py`: `NodeFeed` (one read-only connection: `status`, `power`, `vss/+`)
  and one `NodeSource` per pack module; `tools/dashboard.py --source node --mqtt
  mqtts://… --mqtt-ca/--mqtt-cert/--mqtt-key` (plain `mqtt://` only with
  `--mqtt-insecure-lab`; `--serial` and `--source node` exclude each other; a node source
  records no sessions until P2). Snapshot fields (additive): `source_kind` on every
  snapshot, and for a node source `node`, `vss`, `devices`, `faults_note`, the statuses
  `asleep` and `broker-down`, and per-signal `m`, `m_unknown`, `label`, `raw`, `ts_utc`,
  `age_s`, `stale`, `src`, `before_restart`; `battery_v` falls back to the selected
  `Vehicle.LowVoltageBattery.CurrentVoltage`. `api/openapi.yaml` (`NodeState`,
  `NodePower`, `VssReading`) and `api/asyncapi.yaml` (the `brain-broker` server and the
  node's `status`, `power` and `vss` channels) document them. With a node source the server
  refuses `read_all_faults`, `set_port` and the probes (409, the Brain never touches the
  car) and module actions answer 503 until P4. Tests: codec conformance, the client on an
  in-process fake broker (`tests/fake_broker.py`: retained, wills, keep-alive, session and
  message expiry, ACL, mTLS), the firmware's host-test fixtures
  (`tests/fixtures/node/`, `ostler-firmware` ceb4cc7), the OpenAPI snapshot and AsyncAPI
  payload contracts, safety (no bus import, read-only subscriptions, nothing published),
  an optional `needs_broker` Mosquitto test, and the UI fixture `snapshot-node.json`. The
  UI never draws a node's stale value as live. The D2 pack is untouched.
- **CI `vcan` job.** Loads `vcan` (from `linux-modules-extra` if needed) and, when the
  runner kernel has it, `can-isotp`, brings up `vcan0` and runs the `needs_vcan` tests:
  `SocketCanLink` round-trip and a new `KernelIsoTpChannel` round-trip against a kernel
  ISO-TP ECU socket. `OSTLER_REQUIRE_VCAN=1` (and `OSTLER_REQUIRE_CAN_ISOTP=1`, set only
  when `can-isotp` loads) turns their skips into failures, so the job cannot pass by
  skipping. ([CanLink spec](specs/2026-10-06-canlink-isotp-design.md) §9.)
- **CAN path: CanLink, passive bitrate detection, ISO-TP and the transmit gate**
  ([spec](specs/2026-10-06-canlink-isotp-design.md), first step, fakes only; ADR-0020,
  ADR-0023). New core package `src/openostler/can/`: a frame-level `CanLink` beside
  `Transport` that opens listen-only on every backend (SocketCAN on stdlib `AF_CAN` with
  `CanIfControl` over iproute2, slcan over serial or TCP for the WiCAN Pro, GVRET, and
  python-can only through the new optional `[can]` extra), and whose `send()` raises
  `RateNotConfirmed` until the rate is confirmed or declared. `can.detect()` listens at
  500k then 250k, accepts after 20 clean frames, then sends one `01 00` (11- or 29-bit);
  a silent bus gets one Parked-only one-shot probe per rate, 500k then 250k, stopping at
  the first error frame. Our own pure-Python ISO-TP (`IsoTpChannel`, `IsoTpMux` collecting
  one message per ECU until P2 or P2*, `IsoTpSniffer`, optional kernel
  `KernelIsoTpChannel`); `TxGate` (Tier 0 reads and their FCs in any state, otherwise a
  pack allowlist entry, the entry's driving state and a single-use `TxGrant`; Tier 4,
  Mode 08, MQTT links and remote grants without the install override never pass);
  `CanObdRequestLink` so `J1979` runs over CAN (functional `7DF`/`18DB33F1`, multi-ECU
  `7E8`–`7EF`/`18DAF1xx`); `LoggingCanLink` (JSONL and candump, VIN scrubbed across FF and
  CFs); `ports.list_can_interfaces()`; `schemas/can-tx-allowlist.schema.json`. Tests T1–T17
  on a virtual-clock fake bus (`tests/fake_can.py`), T16 differential against can-isotp
  (dev-only), and shared vectors for the node's C port in `tests/vectors/can/`. This
  Python code is the lab/reference; production CAN I/O and the production gate are the
  node's (ADR-0032). The D2 pack is untouched.
- **J1979 (OBD-II) service layer**
  ([spec](specs/2026-10-06-j1979-service-layer-design.md), first step, fakes only).
  `src/openostler/obd/` is a stdlib-only, transport-agnostic layer: `J1979` over an
  `ObdRequestLink` that returns every responder keyed by ECU (no first-reply-wins),
  shared pacing (one request in flight, 50 ms per ECU, the `0x21` back-off) and typed
  per-ECU results (`ok`, `negative`, `malformed`, `no_reply`; late frames dropped and
  counted). Per-ECU chained support bitmaps for modes 01, 02, 06 and 09 and a `0A` probe
  feed `supported()` → `SupportReport` (never the VIN); Mode 01/02 values from a pack's
  store records with `x-obd` (`PidTable`; multi-PID walks stop at an unknown length);
  P/C/B/U DTCs for 03/07/0A with the CAN count-mismatch fallback and warning; freeze frame
  with its trigger DTC; readiness and `Vehicle.Ostler.Diagnostics.*`; Mode 06 (CAN scaled
  through `obd/uas.json`, K-line raw); Mode 09 CALID, CVN and ECU name, with the VIN handed
  only to an `on_vin` callback and identity scrub patterns (ADR-0036). Mode 08 is never
  sent. Mode 04 is a Tier 1 Maintenance action (`obd/clear.py`, ADR-0033): Parked or
  Idling, local links unless `OSTLER_ALLOW_REMOTE_CONTROL`, one confirmation with a
  safety-system warning, read-only (SRS) ECUs never sent `04`, an automatic logbook
  snapshot first (no snapshot, no clear), honest per-ECU NRC `0x22` text, a re-read and an
  audit entry for every attempt and refusal; no server route mints a grant yet (U2). The
  K-line adapter is `kline/obd_link.py` (ISO 9141-2 and KWP2000); shipped fakes are in
  `openostler.testing`. Shared test vectors for the later C port are in
  `tests/vectors/j1979/`. The signal store gains the `s8` and `u32` kinds.
- **K-line profiles and detection** (ADR-0022,
  [spec](specs/2026-10-06-kline-profiles-detection-design.md), migration step 1).
  `kline/profiles.py` makes K-line protocols data: a frozen `KLineProfile` (framing,
  header and length modes, checksum, P1–P4 and W1–W5, idles, keep-alive, release, init
  method) with the generic built-ins `iso9141_2`, `kwp2000_slow` and `kwp2000_fast`,
  validated by `resolve()`; packs override through the new `ModuleSpec.kline` mapping
  (`ModuleSpec.kline_profile()`), checked by `schemas/kline-profile.schema.json`.
  `kline.detect.detect()` listens for W5, tries functional fast init, then 5-baud `0x33`
  with a required inverted address, and classifies the key bytes (`kline/keywords.py`).
  ISO 9141-2 framing (`kline/frame_iso9141.py`, `kline/iso9141.py`), P3min, keep-alive
  (`EcuSession.keepalive_if_due()`, a server `source.tick()` between polls), release and
  abandoned-session rules, `KLine.from_profile`/`KWP2000.from_profile`,
  `KLine.slow_init_reply()` and `parse_slow_init_reply()`. A generic
  `web/kline_source.py::KLineLinkSource` reports `needs-detect` without a profile and
  remembers a detected profile per `vid` (`<state dir>/kline_profiles.json`, never a VIN).
  Existing constructors are unchanged, so the D2 pack runs as before.
- **Probing is Parked-only.** New queued commands `detect_protocol` and `module_scan` are
  refused unless the server runs with `--kline-detect`, the request carries
  `params.confirm_parked: true` and nothing shows motion (interim until U2);
  `--kline-profile NAME` overrides the profile for the process; `tools/module_scan.py`
  refuses to start without `--confirm-parked` or a "yes" at its prompt.
- The snapshot gains `link` (the K-line link: profile, protocol, init, origin, address,
  key bytes, timing, since; null when a source has none) and the status `needs-detect`
  (OpenAPI `KLineLink`, Zod `KLineLink`, fixture `snapshot-kline.json`).
- U0 repo hygiene (standards research §8.1 items 7–13, ADR-0017):
  - REUSE 3.3 compliance: `LICENSES/` with the canonical licence texts, `REUSE.toml`
    for docs, data, generated and binary files, and SPDX headers on source files;
    `reuse lint` in CI and pre-commit.
  - [SECURITY.md](SECURITY.md): private vulnerability reporting, scope, a 14-day
    acknowledgement target, supported versions, coordinated disclosure, CRA and PSTI
    readiness, and the hard safety lines for testing against vehicles.
  - Supply-chain CI: Dependabot (pip, npm, GitHub Actions, Docker; weekly), an OpenSSF
    Scorecard workflow, and a release workflow that builds the sdist and wheel, writes
    CycloneDX and SPDX SBOMs and attests build provenance.
  - Developer tooling: ruff (`[tool.ruff]`, CI step), mypy configuration (not enforced
    yet) and `.pre-commit-config.yaml`.
  - This changelog and the versioning policy above.
- THIRD_PARTY_LICENSES.md lists the UI libraries bundled in the committed build (React,
  zod, MapLibre GL JS).
- RFC 3339 UTC timestamps and GeoJSON traces on the wire
  ([API consistency spec](specs/2026-10-06-api-consistency-design.md) §4-§5, ADR-0017),
  next to the fields they replace:
  - the snapshot's `ts_utc`, `recording.since_utc` and `active_test.since_utc`;
  - `GET /sessions/{id}/data`: `t0_utc` (the instant of session ms 0) and `trace`, a
    GeoJSON LineString Feature with `properties.t_ms`;
  - `POST /sessions/{id}/audio?start_utc=` (wins over `start`);
  - `GET /sessions/{id}/export?fmt=geojson`: an RFC 7946 FeatureCollection with the
    track (`coordTimes`, `t_ms`) and a Point per note;
  - `openostler.timefmt.rfc3339_utc()`, the one formatter for wire timestamps;
  - `labeled_captures.jsonl` rows are written with an RFC 3339 UTC `t` (older rows keep
    their local time and are read as unknown).

### Changed
- **CAN `TxGate`: `grant_invalid` and the `3E` sweep guard**
  ([CanLink spec](specs/2026-10-06-canlink-isotp-design.md) v0.6 §7; owner, 2026-10-06,
  platform first so the node's C gate can match). New refusal `grant_invalid` for a grant
  with a bad signature or unknown key, distinct from `grant_used`: `TxGate` takes an
  injectable `grant_verifier` (checked after `no_grant`, before `grant_used`; one that
  raises fails closed), `TxGrant` gains an optional `token`, and the default verifier
  accepts the lab's unsigned in-process grants as before. Only a physical `3E` is now a
  Tier 0 read in every driving state: while not Parked a functional `3E` (`7DF`,
  `18DB33F1`) and a `3E` to a third distinct ECU within 5 s are refused as
  `sweep_not_parked`; Parked is unchanged and the per-id rate limit stays. New gate vectors
  T8j–T8m; the vectors README documents the exact check order for the C port. The D2 pack
  is untouched (it has no CAN).
- `EcuSession.tester_present()` sends the session profile's `keepalive` frame (`3E 01`, or
  a bare `3E`) when the session has a profile with one; without a profile, or with
  `keepalive: null`, the legacy `3E <_keepalive_sub>` applies as before (K-line profiles
  spec §4.1, migration step 2). Same bytes for every existing caller; the D2 pack now
  declares its modules' K-line behaviour as `ModuleSpec.kline` overrides.
- HTTP API errors and statuses follow one table
  ([API consistency spec](specs/2026-10-06-api-consistency-design.md) §1-§2). This is a
  behaviour change for clients that key on the status; the UI reads the body whatever
  the status and is unaffected:
  - every API error body is the envelope `{ok: false, error, code?}` (`ErrorReply`), with
    a stable `code` (`bad_request`, `auth_required`, `public_mode`, `read_only`,
    `not_found`, `not_recording`, `disconnected`, `community_off`, `conflict`,
    `too_large`, `internal`, `car_refused`, `car_timeout`, `unavailable`, `no_match`);
    admin API routes send it with their 401 (app pages keep a bodiless 401);
  - `POST /command`: a public-mode refusal is 403 (was 400); `split_session` while not
    recording, `disconnected — connect first` and shutdown not enabled are 409; no
    session recorder is 503; an ECU negative response is 502 `car_refused` (with `nrc`)
    and a poll-thread timeout 504 `car_timeout`; `delete_session` of a synthetic session
    is 403, of an unknown one 404, of the open one 409;
  - `POST /calib` and `/automap` failures are 400 (`no_match` when no raw field fits;
    they were 200), a `/capture` write failure is 500 (was 200), a `/signal` store
    write failure 500 (was 400), community disabled 409 (was 400), and an `OSError`
    reading a session's data or export 500 (was 400);
  - a community contribution queued offline answers 202 with `ok: true, queued: true`
    (was 200 with `ok: false`); the Coverage Map toast says "saved, will send later";
  - a body that is not a JSON object is 400 on every JSON route.
- The UI reads only the new wire fields (API consistency spec §8 step 3): the recording
  card and Logs use `since_utc`/`ts_utc` (`ui/src/lib/time.ts` parses RFC 3339), replay
  takes its clock from `t0_utc` and synthesises `ts_utc`, the map and cursor read the
  GeoJSON `trace`, phone audio sends `start_utc`, and the export menu offers GeoJSON.
- `pyproject.toml` uses PEP 639 licence metadata (`license = "AGPL-3.0-or-later"`,
  `license-files`) and needs `setuptools>=77` to build.
- Every GitHub Action is pinned to a full commit SHA; workflows default to
  `permissions: contents: read`.

### Deprecated
- Removed in 0.2.0 (API consistency spec §6): the snapshot's `ts`, `recording.since`
  and `active_test.since` (epoch seconds; use the `_utc` fields), `SessionData.utc`
  (use `t0_utc` + `t`), `SessionData.track` (use `trace`) and the audio `start` query
  (use `start_utc`). `/snapshot`, `/events` and `/sessions/{id}/data` send
  `Deprecation: @1791244800` (2026-10-06) and `Link: <…/CHANGELOG.md>; rel="deprecation"`.

### Fixed
- A query string no longer turns an exact route into a 404 (`/snapshot?x`, `/events?x`,
  `POST /command?x` …): every route matches the path without its query.
- An unknown route, a missing `/doc` or static file and a method the server lacks
  answered the stdlib HTML error page; they answer the JSON envelope now. An unknown
  browser page (`Accept` prefers HTML, no file extension) gets the app shell, whose new
  not-found view keeps deep links working after a reload.
- `POST /calib` with an unparsable `lid` dropped the connection; it is a 400.
- Trivial lint findings (unused imports and variables, redundant arguments); no
  behaviour change.

## [0.0.1] - 2026-10-05

The only version so far; it was never tagged. In brief, from the git history:

### Added
- 2026-10-05: decisions ADR-0016 to ADR-0021 (COVESA VSS as the canonical signal
  namespace, open standards first, UI architecture, reuse from OVMS and OBDb, CAN links
  listen-only by default, local HTTPS on the device); UI architecture spec approved
  (v0.2); constitution 1.4 and GOALS 1.1.
- 2026-10-05: research notes on open standards, CAN interfaces and head units, OVMS
  reuse, and the head-unit-first UI architecture (7 notes and a draft spec).
- 2026-10-05: Settings → Version, which shows the platform and pack versions and
  commits (`GET /version`).
- 2026-10-05: Phase 0 (ADR-0013): the `VehiclePack` contract, canonical module ids,
  `/pack`, a data-driven UI, the fake pack and layering guards.
- 2026-10-05: Ostler handles (ADR-0014) and TRADEMARKS.md.
- 2026-09-30 to 2026-10-05: the Vibes as Code docs layer (ADR-0001), the Vite + React +
  TypeScript UI (ADR-0004), the always-on session logbook with GPS and map replay
  (ADR-0009), and replay notes, audio, motion and flags (ADR-0010).
- 2026-07-21 to 2026-09: the Discovery 2 Td5 diagnostics project this grew from: K-line
  transport, fast and slow init, KWP2000, Td5 and SLABS module layers, the live
  dashboard, sniffing and mapping tools, and the ESP32 K-line node.

### Changed
- 2026-10-05: repo split executed (ADR-0015). This repository became the
  vehicle-agnostic platform; the package was renamed `d2diag` → `openostler`, and the
  Discovery 2 specifics moved to the `d2diag` pack, which CI and Docker install from its
  repository.
- 2026-10-05: relicensed from MIT to AGPL-3.0-or-later for code and CC BY-SA 4.0 for
  vehicle data, with a CLA (ADR-0012). Earlier releases stay MIT; leijoma's MIT-licensed
  work stays credited.

[Unreleased]: https://github.com/openostler/ostler/commits/main
[0.0.1]: https://github.com/openostler/ostler/commits/93dc12d
