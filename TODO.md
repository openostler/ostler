---
title: "TODO — Ostler platform"
area: root
status: draft
version: 2.3
updated: 2026-10-06
summary: >
  Platform code and infrastructure to-do list: repo-split follow-ups (org move, PyPI, PACK_REF to main, UI composition root), comms-glitch tagging, packaging, retiring the legacy dashboard pages, NodeSource P4, the Network page UI after U1 and follow-ups, data-hub ideas. Vehicle work lives in each pack.
---

# TODO — Ostler platform

Updated 2026-10-06. Check off when done.

> **Scope:** this repo is the platform. Vehicle work (decoding modules, car tests, fault
> data) lives in the vehicle packs: for the Discovery 2, the
> [discovery2-diag](https://github.com/JamesWrightDavid/discovery2-diag) repo and its
> `TODO.md` and `references/test_plan.md`.

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

- [ ] **`driver_side` in the pack layout:** the rail follows `layout.driver_side`
      (`"left" | "right"`); the D2 pack's `layout.json` should say `"right"` (RHD), and
      `schemas/layout.schema.json` must allow the key first. Until then the rail is on the
      left unless the kiosk flag says `side=right`.
- [ ] **The page title:** `ui/index.html` still reads `<title>D2 Diag</title>` because
      `tests/test_web.py` asserts it; rename it to Ostler (the manifest's name) together
      with those server tests.
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
- [ ] **Tap time to UTC:** the pcapng export stamps the node's `t_us` (µs since boot); map
      it to UTC from the tap's `time` events (raw-tap §2.4, CBOR) once the node emits them
      (decode lab, spec §14).
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
- [ ] **Firmware: publish the manifest and role claims** (`ostler-firmware`): the node
      publishes no `manifest` and no `role/…` claims yet, and no `asleep` status; the P3
      tests use the hand-written `tests/fixtures/node/cluster.jsonl`. When it does,
      regenerate the fixture from a host-test dump. The manifest topic name and the claim
      payload are for the module-bus message spec (spec §4).
- [ ] **Serial refusal while running:** the check runs at start only, and only with
      `--mqtt`; a node that appears later (or a lab laptop with no broker) is not seen.
      Decide whether a serial source keeps a watch on the broker, or a Brain install
      remembers the vehicle's gate holder.
- [ ] **§6.5 with the manifest:** the manifest's `primary` and the owner's priority in the
      selection, and its signal `rate` (sensor-detection §7 `rate_hz`) instead of the EMA
      interval. Waits for the firmware's manifest to fix the field shapes.
- [ ] **Energy ledger and floors** on the Network page's Power section (UI spec §3.8;
      app-model §13.2): the arbiter publishes no ledger yet (ADR-0040 §4.4; P4 / firmware).
- [ ] **P4 requests:** `act/<id>`, wake requests, lab requests, outcomes in the snapshot,
      the `/command` codes (`gate_refused`, `no_gate`, `node_asleep`, `expired`,
      `state_changed`); until then module actions on a node source answer 503.
- [ ] **GNSS selection (ADR-0032 A4)** with the shared vectors run by the C firmware and
      the server; until then GNSS paths use the generic §6.5 rule.
- [ ] **Broker discovery by mDNS** (`_ostler-mod._tcp`, ADR-0027 §6); today `--mqtt` is
      required.
- [ ] **Firmware topic collision:** the node publishes two modules' readings of one VSS
      path (the D2 battery voltage from the Td5 and SLABS) on one retained topic, so only
      the last survives as a stored value. NodeSource keeps both live (keyed by source);
      the module-bus message spec should decide the topic shape.
- [ ] **Regenerate `tests/fixtures/node/*.jsonl`** from the firmware's `node-fixtures`
      target whenever its payloads change (copied from `ostler-firmware` ceb4cc7).
- [ ] **UI states of §10** ("Node asleep · wakes on …", "Node offline", "Waiting for the
      node", "Node not reading <module>", "before restart"): the snapshot carries them. U1
      shows the node's power state as a badge in the strip's Link chip (Asleep, Waking…,
      Kept awake, Shutting down, Offline); the "wakes on …" detail and the other states
      are still open.
- [x] **Mosquitto conformance in CI:** the `broker` job installs Mosquitto on the runner
      and runs the `needs_broker` tests with `OSTLER_REQUIRE_BROKER=1`, mTLS and the ACL
      included.
- [ ] Unit conversion to VSS units happens at U3 for the node and serial paths alike.

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
