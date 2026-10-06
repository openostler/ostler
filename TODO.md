---
title: "TODO — Ostler platform"
area: root
status: draft
version: 2.0
updated: 2026-10-06
summary: >
  Platform code and infrastructure to-do list: repo-split follow-ups (org move, PyPI, PACK_REF to main, UI composition root), comms-glitch tagging, packaging, retiring the legacy dashboard pages, data-hub ideas. Vehicle work lives in each pack.
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
      for `KernelIsoTpChannel`).
- [x] **CI job with `vcan`** so the `needs_vcan` tests run instead of skipping: the `vcan`
      job in `.github/workflows/ci.yml` (`OSTLER_REQUIRE_VCAN=1`).
- [ ] **Wire the CAN path into the server** (after U2/U4): the link chip (mode, rate,
      `listen_only: "requested"`), the connection ladder's Bus rung from `DetectResult`,
      `RateMemory` under the state dir, the server gate minting `TxGrant`s, and the pack
      `vehicle.json` schema referencing `can-tx-allowlist.schema.json#/$defs/transport`.

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
