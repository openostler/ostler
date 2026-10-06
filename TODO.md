---
title: "TODO — Ostler platform"
area: root
status: draft
version: 2.1
updated: 2026-10-06
summary: >
  Platform code and infrastructure to-do list: repo-split follow-ups (org move, PyPI, PACK_REF to main, UI composition root), comms-glitch tagging, packaging, retiring the legacy dashboard pages, NodeSource phases P2–P4 and follow-ups, data-hub ideas. Vehicle work lives in each pack.
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
      for `KernelIsoTpChannel`). Add a CI job that loads `vcan` so the `needs_vcan` tests
      run instead of skipping.
- [ ] **Wire the CAN path into the server** (after U2/U4): the link chip (mode, rate,
      `listen_only: "requested"`), the connection ladder's Bus rung from `DetectResult`,
      `RateMemory` under the state dir, the server gate minting `TxGrant`s, and the pack
      `vehicle.json` schema referencing `can-tx-allowlist.schema.json#/$defs/transport`.

## NodeSource ([spec](specs/2026-10-06-node-source-design.md))

P1 (read-only ingest) is built. Open:

- [ ] **P2 recording and raw tap:** sessions driven by the node's `status` and `power`
      (end at once on `asleep`, `end_reason: node_asleep`), `vss` columns (`<path>` and
      `<path>@<device>`), `tap/+/meta` and `tap/+/data` (session expiry 60 s), the
      `.otap` files and `meta.json` `tap`, the Brain-side scrub check, `fmt=pcapng`, the
      `node.tap` snapshot field. Until then `--source node` records no sessions.
- [ ] **P3 Network page:** `manifest` and `role/#` subscriptions, `GET /cluster`, the role
      table. With the role claims, a **serial source refuses to start when the vehicle's
      node holds the `kline-diag` gate** (owner answer 7); P1 has no gate claim to read,
      so today only `--serial` together with `--source node` is refused. The manifest's
      `primary` and the owner's priority join the §6.5 selection; the manifest's `rate`
      replaces the EMA interval.
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
      node", "Node not reading <module>", "before restart"): the snapshot carries them; the
      UI shows only the generic connection states and stale ages so far.
- [ ] **Mosquitto conformance in CI:** a service container so the `needs_broker` tests
      (`tests/test_mqtt_mosquitto.py`) run instead of skipping; add TLS and the ACL there.
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
