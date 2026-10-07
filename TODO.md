---
title: "TODO — Ostler platform"
area: root
status: draft
version: 2.7
updated: 2026-10-07
summary: >
  Platform code and infrastructure to-do list: repo-split follow-ups (org move, PyPI, PACK_REF to main, UI composition root), comms-glitch tagging, packaging, retiring the legacy dashboard pages, NodeSource P4, the Network page UI after U1 and follow-ups, the module-bus build follow-ups from the owner's answers of 2026-10-06 (firmware, platform, pack, bench), the ecosystem build order approved on 2026-10-07 (Drive-mode fit, V1–V3 visual, U2 lockouts with a legal check, Trips, NodeSource P4, add-on repos) with its mesh and media bench items, data-hub ideas. Vehicle work lives in each pack.
---

# TODO — Ostler platform

Updated 2026-10-07. Check off when done.

> **Scope:** this repo is the platform. Vehicle work (decoding modules, car tests, fault
> data) lives in the vehicle packs: for the Discovery 2, the
> [ostler-pack-lr-d2](https://github.com/openostler/ostler-pack-lr-d2) repo and its
> `TODO.md` and `references/test_plan.md`.

## Ecosystem build order (approved by the owner on 2026-10-07)

The owner approved the ecosystem round on 2026-10-07 ("approve all"):
[ADR-0042](decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md), the
[UI spec §12](specs/2026-10-06-ui-architecture-design.md), the
[visual design system](specs/2026-10-07-visual-design-system-design.md), the
[app-model §14](specs/2026-10-06-app-model-design.md) and
[accounts §14](specs/2026-10-06-accounts-sharing-design.md) amendments, and the add-on specs.
Build in this order:

- [ ] **1. Drive-mode fit fix** (UI spec §12.3): the HU-5 800×480 layout class, Drive mode on
      one screen at every head-unit class, and the Playwright no-scroll assert at 800×480,
      1024×600, 1280×720, 1280×480, 1920×720 and 393×852. Lands first, before U2.
- [ ] **2. Visual V1–V3** (visual spec §11): V1 tokens (Night default, Day, Night dim, Deep
      night; cyan accent; violet speed ramp), self-hosted Figtree and maps (Ostler Night/Day
      on Brain-served PMTiles, OpenFreeMap fallback, `--bg` offline; ADR-0009 amendment);
      V2 the component kit; V3 pages; stylelint and Playwright gates. All before U2 build work.
- [ ] **3. U2 lockouts** (UI spec §12.1): driver-facing displays, Park evidence for Idling,
      Passenger view (reg 109 content only, per trip, 15 min, logged locally), Open on phone,
      the six new templates with their limits, task depth ≤ 3, the "Using Ostler while
      driving" page.
- [ ] **Legal check before U2 ships** (UI spec §12.1, a gate): a UK road-traffic lawyer's
      opinion on Construction and Use regulation 109 (LCD head units and Passenger view),
      recorded in `references/`; until then U2 ships Open on phone only, with no head-unit
      override and no phone override. A **product-liability opinion** (EU Product Liability
      Directive 2024/2853) before any hardware sales.
- [ ] **4. Trips** (UI spec §12.2): Logs renamed Trips with `logs` routes aliased and the
      `/sessions` API unchanged; the trip summary index; trip list, map-first trip detail,
      playback, Statistics, Records and gated Sprints; End trip now, Exclude from stats,
      Export all; no score.
- [ ] **5. NodeSource P4** (below).
- [ ] **6. Add-on repos** (ADR-0034 amendment of 2026-10-07): create `ostler-app-social`,
      `ostler-app-vehicles` and `ostler-app-maintenance` from their specs, and later
      `ostler-app-lubelogger` (after Maintenance M2). New slots `more:social`,
      `more:vehicles` and `home:card` (app-model §14.7) and the pack contract's optional
      `maintenance.json` (ADR-0013 amendment) come with them.

*Bench (ADR-0038 amendment of 2026-10-07, before Social phase S3):*
- [ ] **UK/EU HaLow pair** (camp access point, car client): range at 25 mW, airtime against
      the 2.8 % client budget, delivery of text, PTT bursts, voice notes and stills.
- [ ] **Two-car batman-adv over 802.11s pair** on 2.4 GHz, each Brain routing, Babel at the
      edge: range and throughput at 1 and 2 hops, call latency and loss, no mDNS or
      broadcast into a car segment.
- [ ] **LiveKit on a Pi 5 Brain**: CPU and memory for a 6-member voice room and a 2-member
      video room with go2rtc passthrough.
- [ ] **Link handover**: a live call between internet and the Wi-Fi mesh, and a text
      falling back to LoRa.
- [ ] **MeshCore beside Meshtastic** on the same boards with the same scripted traffic.

## Repo split follow-ups (ADR-0015)

- [ ] Create the `openostler` GitHub org (ADR-0014 checklist) and push this repo as
      `openostler/ostler`; update the URLs in `pyproject.toml`, `README.md`,
      `mac/install.sh` and the geocoder User-Agent if the name differs.
- [x] Switch CI and the Dockerfile default from the pack's `split-pack` branch to `main`.
- [ ] Ship the D2 pack's docs (`references/`, `docs/`) inside its wheel, so a `git+`/PyPI
      install also fills the Docs tab; until then CI and Docker install a source checkout.
- [ ] Publish `openostler` to PyPI (placeholder 0.0.1 first) so packs can depend on it
      without a git URL; then drop `--no-deps` from the pack installs.
- [ ] **UI composition root:** `ui/src/main.tsx` imports `./vehicles/lr_d2` (the D2
      views ship built into the platform UI). Decide how packs ship UI views (a pack
      bundle loaded via `/pack`, or an npm `@ostler/*` package) and move `lr_d2` out.
- [ ] Split `tests/test_logbook.py` and `tests/test_web.py` into platform tests on
      `FAKE_PACK` plus thin `needs_pack` integration tests, so more of the platform is
      covered without the D2 pack.
- [ ] Rename the `D2DIAG_ADMIN_PW` / `D2DIAG_ENDPOINT` environment variables (keep the
      old names as fallbacks for one release) and the Pi's `d2diag.service` unit.
- [ ] Move `server/` (community endpoint) into the private `ostler-cloud` repo with its
      history (it was left out of this repo at the split).

## UI shell (U1 follow-ups, [UI spec](specs/2026-10-06-ui-architecture-design.md) §10)

- [x] **`driver_side` in the pack layout:** `schemas/layout.schema.json` allows
      `driver_side` (`"left" | "right"`), the rail follows it (the kiosk flag overrides;
      absent means left), and the D2 pack declares `"right"` (RHD) in its own PR.
- [x] **The page title:** `ui/index.html` reads `<title>Ostler</title>`, the Web App
      Manifest's name (a vitest keeps them in step); `tests/test_web.py` and the e2e smoke
      test assert it. The legacy `/legacy/v2` page keeps its old title.
- [ ] **Head-unit type sizes for content:** the shell uses the 76 px targets and 24 px gap
      on head units, but today's screens keep their phone-sized text; the 32/24 px type and
      driver-safe templates arrive with U2's lockouts.
- [ ] **Logs year heatmap:** its 10 px day cells are exempt from WCAG 2.5.8 only because the
      Dates filter does the same job; the axe scan excludes `.logs-heat-grid`. Consider
      larger cells on head units.
- [ ] **Phone strip:** at 393 px the Mark chip shows its flag without the word (its
      accessible name keeps "Mark"); revisit if the strip gets room.

## Code / offline

- [ ] **Distinguish comms glitches from real sensor faults.** Signals that share a LID
      are read in one request, so a bad read corrupts them together; a single bad signal
      whose LID-mates are valid is a real per-channel fault. Tag snapshots and CSV rows
      with a `comms_glitch` marker when a whole LID reads bad, and have the analysis
      classify junk as comms vs sensor (cross-checking the ECU's own DTC).
- [ ] **Retire the legacy pages** `web/dashboard.html` / `dashboard_v2.html` (served at
      `/legacy/*`) once the React UI's parity is confirmed in the car.
- [ ] **PyInstaller distribution** (.app/.exe) for non-technical users.
- [ ] **CAN on the Pi image** ([CanLink spec](specs/2026-10-06-canlink-isotp-design.md)
      §3, §12): add `AmbientCapabilities=CAP_NET_ADMIN` to `openostler.service` so
      `CanIfControl` can run `ip link set can0 …`; note `modprobe can-isotp` (optional,
      for `KernelIsoTpChannel`).
- [x] **CI job with `vcan`** so the `needs_vcan` tests run instead of skipping: the `vcan`
      job in `.github/workflows/ci.yml` (`OSTLER_REQUIRE_VCAN=1`).
- [ ] **Wire the CAN path into the server** (after U2/U4): the link chip (mode, rate,
      `listen_only: "requested"`), the connection ladder's Bus rung from `DetectResult`,
      `RateMemory` under the state dir, the server gate minting `TxGrant`s, and the pack
      `vehicle.json` schema referencing `can-tx-allowlist.schema.json#/$defs/transport`.

## NodeSource ([spec](specs/2026-10-06-node-source-design.md))

P1 (read-only ingest), P2 (recording and raw tap) and the P3 backend (Network page data)
are built. Open:

- [x] **P2 recording and raw tap:** sessions driven by the node's `status` and `power`
      (end at once on `asleep`, `end_reason: node_asleep`), `vss` columns (`<path>` and
      `<path>@<device>`), `tap/+/meta` and `tap/+/data` (session expiry 60 s), the
      `.otap` files and `meta.json` `tap`, the Brain-side scrub check, `fmt=pcapng`, the
      `node.tap` snapshot field.
- [x] **Tap time to UTC:** the firmware emits `time` events (0426ea5, CBOR `{t_us, utc_ns,
      source, err_us}`); `node/tap.py` `TimeMap` maps `t_us` linearly between marks and the
      pcapng export stamps UTC (a tap without marks keeps the node clock); `meta.json` `tap`
      counts `time_marks`. Rows and tap records stay linked by `t_us`.
- [x] **Tap batch properties** (module-bus spec §8; firmware 5971323): `NodeFeed` hands
      each batch's MQTT 5 properties to the tap writer, which refuses another content type,
      reads an unlabelled batch as v1 and cross-checks `first_seq` with the first record
      (`refused`, `unlabelled`, `first_seq_mismatch` in `meta.json` `tap`); the header's
      `records` is read as an array; `tests/fake_node.py` sends the fixtures' properties.
- [ ] **Parked periods and alarm events** in the logbook from the node's `power` and alarm
      topics (ADR-0010 amendment; spec §7 "in a later spec").
- [x] **Firmware and manifest `etag` in node session meta:** `meta.json` `device_info`
      `{device: {fw, etag}}` and `node_manifest` events (P3).
- [x] **P3 Network page data (backend):** `manifest` and `role/#` subscriptions, the
      device and role table (`node/cluster.py`) with the power record and last seen, void
      claims flagged, gate conflicts, handovers from live messages, `GET /cluster`
      (OpenAPI `Cluster`), the AsyncAPI channels `nodeManifest`, `nodeRole`,
      `nodeRoleScoped`, `device_info` and `node.fw`/`etag` in the snapshot.
- [x] **Serial source refuses beside a gate-holding node** (owner answer 7):
      `tools/dashboard.py --serial … --mqtt URL` checks the vehicle's claims and manifests
      once and refuses (also when the broker cannot be checked).
- [ ] **Network page UI — after U1.** The Network core app (UI spec §3.7, §3.8; app-model
      spec §12, §13.2) renders `GET /cluster`: the Devices section with the Power column,
      the Roles section ("No holder", "No gate for this bus", void and conflict flags),
      the stale banner, and the device page's peer view (same row shape). Nothing in the
      new UI is built before U1 (UI spec §10); `ui/src/api/schemas.ts` gains `Cluster`,
      `device_info` and `node.fw`/`etag` then (Zod strips them today).
- [x] **Firmware: publish the manifest and role claims** (`ostler-firmware` 0426ea5): the
      node publishes its manifest, the gate claim and its release, and `asleep`; the tests
      read them from `tests/fixtures/node/lifecycle.jsonl` and the vector runs.
      `cluster.jsonl` keeps only what the node cannot publish (other devices, a second gate
      claim, vehicle roles held by the node).
- [x] **Firmware: the second gate claim** (`ostler-firmware` 5971323, ADR-0037 §5): the
      node reports `gate_conflict` in its manifest's `problems`; the cluster view shows it
      (gate row `conflict`, no holder, alert `by: "manifest"`), tested with the real
      `gate-conflict.jsonl`; the unset-priority test uses the real
      `slabs-vectors-no-priority.jsonl`; every `power` record carries the parked class.
- [x] **Owner decision: which claims silence a gate holder** (module-bus spec v1.3 §17
      item 13, 2026-10-06): the firmware's rule is adopted (any claim on its gate bus
      silences it), gate claims never expire, and a stale one is cleared only by the
      owner's Remove device (§7.2). Follow-ups below under Module-bus messages.
- [x] **Serial refusal while running:** decided (owner, 2026-10-06, spec §15 second
      round): it stays a start-time check when `--mqtt` is given; no change now. A node
      that appears later, or a lab laptop with no broker, is still not seen.
- [ ] **§6.5 with the manifest:** the manifest's `primary` device and the owner's priority in
      the selection (the pack's primary *field* is in since 2026-10-07), and its signal `rate` (sensor-detection §7 `rate_hz`) instead of the EMA
      interval. The node now publishes `priority` (when set) but no `signals`, `primary` or
      `rate_hz` yet (firmware 5971323).
- [ ] **Energy ledger and floors** on the Network page's Power section (UI spec §3.8;
      app-model §13.2): the arbiter publishes no ledger yet (ADR-0040 §4.4; P4 / firmware).
- [ ] **P4 requests:** `act/<id>`, wake requests, lab requests, outcomes in the snapshot,
      the `/command` codes (`gate_refused`, `no_gate`, `node_asleep`, `expired`,
      `state_changed`, `grant_locked`); until then module actions on a node source answer
      503. No longer blocked on grants: the owner's answers (module-bus spec v1.3 §9–§11)
      and ADR-0041 settle the flow.
- [ ] **GNSS selection (ADR-0032 A4)** with the shared vectors run by the C firmware and
      the server; until then GNSS paths use the generic §6.5 rule.
- [ ] **Broker discovery by mDNS** (`_ostler-mod._tcp`, ADR-0027 §6); today `--mqtt` is
      required.
- [x] **Firmware topic collision:** the node publishes two modules' readings of one VSS
      path (the D2 battery voltage from the Td5 and SLABS) on one retained topic, so only
      the last survives as a stored value. NodeSource keeps both live (keyed by source).
      Decided (module-bus spec v1.3 §6, owner answer 9): one primary module per VSS path,
      the other under its pack leaf; built in firmware a65c44d and pack 507ef88, fixtures
      copied 2026-10-07.
- [ ] **Regenerate the firmware fixtures** (`td5-vectors`, `slabs-vectors`,
      `slabs-vectors-no-priority`, `lifecycle`, `gate-conflict`, `wire-conflict`, `off` in
      `tests/fixtures/node/`) from the firmware's `node-fixtures` target whenever its
      payloads change (last copied from `ostler-firmware` a65c44d).
- [ ] **UI: the `off` power state.** The Brain accepts `power.state: off` and the snapshot
      reads `asleep`; the strip's power badge (`ui/src/shell/strip.ts` `powerNote`) has no
      word for `off` yet ("Off"), and the Network page will need one.
- [ ] **UI states of §10** ("Node asleep · wakes on …", "Node offline", "Waiting for the
      node", "Node not reading <module>", "before restart"): the snapshot carries them. U1
      shows the node's power state as a badge in the strip's Link chip (Asleep, Waking…,
      Kept awake, Shutting down, Off, Offline; Off wins over Offline); the "wakes on …" detail and the other states
      are still open.
- [x] **Mosquitto conformance in CI:** the `broker` job installs Mosquitto on the runner
      and runs the `needs_broker` tests with `OSTLER_REQUIRE_BROKER=1`, mTLS and the ACL
      included.
- [ ] Unit conversion to VSS units happens at U3 for the node and serial paths alike.

## Module-bus messages ([spec](specs/2026-10-06-module-bus-messages-design.md))

- [x] **Open questions §17** answered by the owner on 2026-10-06 (spec v1.3, §17 "Owner
      answers"): the challenge exchange, grants for queued Tier 1 actions, `tap/ctl` and
      `lab/` details, bridge patterns, the parked allow-list, `off` and shutdown, events and
      the alarm state, `faults/<pack>.<module>`, one primary module per VSS path, TXT keys,
      the CAN fallback (deferred to U5), the mesh bridge, gate claims, check-in timings;
      the Brain's signing extra is ADR-0041.
- [x] **`grant_invalid`** in the platform's Python gate and the shared CAN vectors (owner,
      2026-10-06), so both report the same code as the node; the signed-token case `T8n`
      (header, size, boot, challenge, `rh`) runs with real tokens under `[signing]`.
- [x] **`power.state: off`** is accepted by `node/messages.py` `parse_power` (ADR-0040 §1);
      each device publishes its own `off` and the power owner reports `feeds` (spec v1.3 §5);
      the UI shows it as the **Off** badge.
- [ ] **AsyncAPI and OpenAPI** follow the spec as channels are built. Done (2026-10-07):
      `event/`, `faults/`, `power.feeds`, `tap/ctl`, `lab/req`, `lab/resp` (documented,
      sent from P4), the events feed and SSE, the Remove device route. Open with P4:
      `act/` (with the `challenge` outcome), `wake/`, the grant refusals (`grant_locked`).

**Build follow-ups from the owner's answers (spec v1.3, 2026-10-06).**

*Firmware (`ostler-firmware`):*
- [ ] **`power.feeds`** for the Brain's switched supply (built, not used yet: a65c44d), and
      the `shutdown` act sent to the Brain (only to the device it feeds); the node's own cut adds `power` `off` and
      `status` `asleep` before a reason-0x00 disconnect (spec §4, §5, §11).
- [ ] **`faults/<pack>.<module>` and `event/<name>` topics** (retained whole list; QoS 1
      events with `id` and severity; `event/alarm.triggered`, `event/gate.conflict`,
      `event/fault.new`) (spec §6.1, §6.2).
- [x] **K-line echo mismatch and foreign traffic before init** as `gate_conflict`
      `by: "bus"`, released by owner acknowledgement or 10 min quiet (spec §7.2; bench for
      false positives).
- [ ] **Grant challenge**: the `challenge` outcome after gate steps 1–11, the pinned header,
      `boot` and `rh`, `grant_locked`, RNG only after the radio is up; vendor the optional
      `monocypher-ed25519` part (not core `crypto_eddsa_*`) (spec §10; node-can §6).
- [x] **mDNS TXT** (built, not advertised yet; firmware a65c44d): `txtvers=1`, `var`, `md`, `fw`, `pr`, `roles`, `etag`; no `mf` or `cv`
      (spec §14).
- [x] **Primary module**: publish `vss/<VSS path>` only from the pack's primary field, the
      other module under its pack leaf (spec §6; firmware a65c44d, fixtures copied).
- [x] **`lab/req` de-duplication** by `id` (last 16) and its ≤ 10 s expiry (spec §8).
- [x] **`tap/ctl` `session`** field (`{op, session, buses?, filters?}`; repeated start and
      unknown stop are no-ops) (spec §8).
- [ ] **Parked broker allow-list** adds `act/+`, `event/+`, `faults/+`; excludes `tap/#`
      and `lab/#` (spec §12); Remove device's broker-local purge on the parked broker
      (spec §13).

*Platform (this repo):*
- [x] **Primary selection**: `Signal.primary`, `signals.primary_fields`/`primary_problems`,
      the schema allows the key; selection prefers a usable primary source for a shared
      VSS path (absent marker: the earlier rule) (spec §6; NodeSource §6.5).
- [x] **`faults/` and `event/` parsing** in NodeSource (subscriptions at QoS 1, snapshot
      `faults` and `faults_read` from the whole list, "read, none" vs "not read", events
      de-duplicated by `id` into `GET /cluster/events` and its SSE stream) (spec §6.1, §6.2).
- [ ] **The logbook's alarm and node events** (spec §6.1; ADR-0010 amendment): record the
      events feed and alarm-state changes in node sessions.
- [ ] **`Vehicle.Ostler.Diagnostics.DtcCount`** derived on the Brain from the fault lists
      (spec §6.2).
- [x] **Alarm metric**: `Vehicle.Ostler.Security.Alarm.State` in `vss/ostler.vspec`
      (string enum via `allowed`, OVMS `v.e.alarm`, HA `ha_domain: alarm_control_panel`;
      ADR-0016 Amendments), `metrics.json` regenerated; subscribed at QoS 1.
- [x] **Remove device API** on the Brain: `POST /cluster/remove` (owner = admin until
      accounts, local link only, one confirmation), the Brain's revocation list, the
      install's revoke hook, the broker-host purge of `ostler/v1/<vid>/<device>/#`
      (`docs/brain_broker.md` for the limits) (spec §7.2, §13).
- [ ] **Remove device: the broker host's revoke hook** in the Brain image (drop the
      device's ACL entry, revoke its certificate at the local CA) and the Network page's
      action and one-tap remedy (UI spec §3.7) after U1.
- [x] **Signing extra and helper** (ADR-0041): `signing` and `passkeys` extras in
      `pyproject.toml` with one shared `cryptography` requirement; `openostler.signing`
      (canonical JSON, `rh`, the pinned header, the compact JWS, `BrainKey` made on first
      use, `jws_grant_verifier`); RFC 8032 and RFC 8037 vectors; `gate.json` case `T8n`
      (`rh` mismatch, extra header member, other alg, size, wrong `boot`, other challenge);
      `THIRD_PARTY_LICENSES.md` entry; CI installs `[signing]`.
- [ ] **`grant_locked` lock-out vectors**: the Python reference gate has no requester, so
      the lock-out (3 × `grant_invalid` in 60 s, spec §10) waits for the node's `act`
      gate model in P4; add its shared cases then.
- [x] **Bridge config**: inbound `+/act/+`, `+/event/+`, `+/faults/+`; `lab/resp` not
      bridged; `try_private`, MQTT 5 bridge protocol (templates in `docs/brain_broker.md`;
      spec §12). The Brain's echo guard for its own `act`/`wake` arrives with P4.

*Pack (the Discovery 2 pack):*
- [x] **Primary marker** in the signal store for a VSS path decoded by two modules (the D2
      battery voltage: Td5 primary; pack 507ef88).

*Bench:*
- [ ] **Mosquitto bridge property pass-through**: whether the Brain's Mosquitto bridge and
      the ESP-IDF port forward MQTT 5 properties (Message Expiry, Correlation Data,
      Response Topic, user properties such as `first_seq`) and count expiry without SNTP;
      and whether the parked broker (ESP-IDF Mosquitto port) supports **retained-message
      expiry** (for `in/position/<peer>`) (spec §12, §16).

## Roadmap — data-hub direction (not scheduled)

The architecture is already hub-shaped (`DataSource` + the signal store as a normalized
name/unit/confidence model + SSE). North star: a SignalK-inspired vehicle data hub, built
one reversible step at a time. See
[specs/2026-10-06-platform-direction-design.md](specs/2026-10-06-platform-direction-design.md).

- [ ] **Phone GPS** as a second source (zero hardware).
- [ ] **MQTT source-bus** on the Pi as the internal spine; SSE stays for the browser.
- [ ] **K-line as its own ESP32 node** (ostler-firmware), publishing signals.
- [ ] **A time-series store** fed from the raw/CSV/JSONL logs.

## Method lessons

- **Never lock an experiment to one variant before the question is settled.**
- **Mix the order**, so you do not measure the attempt number.
- **Don't run conditions as separate time blocks**, or you measure the clock.
- **Measure what you claim to measure.**
