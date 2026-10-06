---
title: "U0 Seams — VSS metrics, vehicle id, schemas, API contracts, repo hygiene — design"
area: specs
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, references/research/standards.md, references/research/ui/vehicle_data_model.md, references/research/ovms_reuse.md]
summary: >
  The U0 phase of the UI architecture (§10): no visible UI change, only seams. A: vss/ (VSS 6.1 pinned and vendored, the ostler.vspec overlay with OVMS/HA/OBDb aliases and Vehicle.Ostler.*), the generated metrics.json and vss_leaves.json, an optional metric on signal-store records, a vehicle id (vid) in logs/vehicle.json and on every session, index schema 3, and JSON Schemas for the store, layout, vehicle.json and session meta. B: OpenAPI 3.1 and AsyncAPI 3.0 contracts. C: repo hygiene (REUSE, PEP 639, SECURITY.md, Dependabot, Scorecard, SBOM release, ruff and pre-commit, CHANGELOG). D: the Discovery 2 pack fills its metric keys.
---

# U0 Seams — design

## Context

The owner approved this on 2026-10-06. U0 is the first phase of the
[UI architecture](2026-10-06-ui-architecture-design.md) (§10, standards per phase §10.1):
small seams that later phases build on, with no visible UI change. The decisions it carries
out are [ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md) (VSS),
[ADR-0017](../decisions/adr-0017-open-standards-first.md) (open standards) and
[ADR-0018](../decisions/adr-0018-ui-architecture-decisions.md) (UI). The adoption order is
[standards §8.1](../references/research/standards.md#81-adopt-now-cheap-high-value-no-runtime-dependencies).

U0 is four work streams, each a separate branch and review:

| Stream | Ships | Repo |
|---|---|---|
| **A. Data seams** | `vss/`, `metrics.json`, `metric` on store records, `vid`, `schemas/` | platform |
| **B. API contracts** | `api/openapi.yaml`, `api/asyncapi.yaml` and their tests | platform |
| **C. Repo hygiene** | REUSE, PEP 639, SECURITY.md, Dependabot, Scorecard, SBOM release, ruff, pre-commit, CHANGELOG | platform |
| **D. D2 metrics** | `metric` keys on the Discovery 2 store | D2 pack |

Rules for all four: the runtime stays stdlib plus pyserial (ADR-0002), so every new tool
is dev-only; no VIN is ever logged, stored or put in a fixture (ADR-0018 Q7).

## A. Data seams

### A.1 `vss/`

- `vss/VERSION` holds `6.1`.
- `vss/upstream/` vendors the unmodified COVESA VSS 6.1 release artefacts (tag `v6.1`),
  MPL-2.0 with its licence text and a README naming the source and checksums:
  - `vss.json`, the release JSON export (370 KB, so it is vendored whole);
  - `model.vspec`, the composed standard tree from the release's `vss_compose.tar.gz`,
    because vss-tools reads `.vspec`, not JSON;
  - `units.yaml` and `quantities.yaml`.
- `vss/ostler.vspec` (CC BY-SA 4.0) is the overlay and the single source of aliases:
  - it annotates the common set ([vehicle data model §4.1](../references/research/ui/vehicle_data_model.md))
    with `ostler_role`, `ovms`, `ha_device_class`, `ha_state_class` and `obdb`;
  - it adds `Vehicle.Ostler.Diagnostics.*` (`MilOn`, `DtcCount`, `PendingDtcCount`,
    `IsReadinessComplete`, `ReadinessIncompleteCount`, `DistanceSinceDtcClear`) and
    `Vehicle.Ostler.Chassis.RideHeight.*` (raw counts);
  - an existing node is restated with its own `type`, so it is named even with no alias.
- **Aliases.** OVMS names come from `main/metrics_standard.h` (MIT, facts only). No engine
  node takes a `v.m.*` alias (OVMS `v.m.*` is the motor) and no fuel node takes a `v.b.*`
  alias (fuel is never `v.b.soc`). OBDb names are the SAEJ1979 `suggestedMetric` values.
  OVMS and OBDb aliases are unique; HA device and state classes are shared by design.

### A.2 `tools/build_metrics.py` and the generated files

- It runs `vspec export json` (vss-tools 6.1.0) over `upstream/model.vspec` with the
  overlay and the five extended attributes. vss-tools is in the `[dev]` extra with the
  marker `python_version >= '3.11'` (it installs cleanly there); a 3.9 dev install skips it.
- It writes two committed, sorted, deterministic files, both shipped as package data:
  - `src/openostler/metrics.json`: every leaf the overlay names, with path, type,
    datatype, VSS unit key, description, `ostler_role`, `aliases` and `extension`;
  - `src/openostler/vss_leaves.json`: every leaf of the pinned upstream tree and its unit.
- It fails on: `model.vspec` no longer exporting to `vss.json`; a restated type that
  differs from upstream; an overlay change to an upstream datatype, unit or description; a
  unit that is not a verbatim key of `units.yaml`; a duplicate OVMS or OBDb alias; fuel on
  an OVMS battery metric. `--check` exits 1 if either file is stale; CI runs it.

### A.3 `metric` on signal-store records

- A record may carry `metric`, a VSS path. `Signal.metric` defaults to `None`;
  `_record_to_signal` reads it; `upsert_field` keeps a known path, drops an empty one and
  raises `ValueError` on an unknown one.
- `openostler/metrics.py` (stdlib): `load_metrics()`, `metric_info(path)` (the
  `metrics.json` entry, else a minimal upstream entry, else `None`), `is_known(path)`
  (in `metrics.json` or a leaf of the pinned tree) and `vss_version()`.
- Pack units are unchanged in U0: the store keeps its display unit (`°C`, `bar`). U0 checks
  that every `metric` resolves; the check that a mapped field's unit converts to the
  metric's VSS unit lands with the U3 mapping step, which owns the conversion (vehicle data
  model §4.1 item 5).
- Tests: `metrics.json` is current (skipped with a reason without vss-tools; CI installs
  it); every unit is a key of the pinned file; aliases are unique per kind; no fuel on
  `v.b.*`; every fake-pack and D2 (`needs_pack`) `metric` resolves.

### A.4 Vehicle id (`vid`)

- `logs/vehicle.json` (the parent of the sessions directory) is created once, atomically
  and only if absent: `{vid, pack, created_utc}`, with `vid` 8 hex characters from
  `secrets`. It is never rewritten while valid. `OSTLER_VEHICLE_ID` overrides the vid
  without touching the file. An unwritable state directory gets an in-memory vid.
- The recorder writes `vid` into each new session's `meta.json`. Synthetic sessions (the
  packs' committed demo logs) get one only when it is passed in, so they stay byte-stable.
- The store reads a session without `vid` as the local vid, on read only. Files are never
  rewritten. `/sessions` and `/sessions/<id>` therefore always carry `vid`.
- The index moves to schema 3 with a `vid` column, so an older index rebuilds.
- UI: `vid` is `z.string().optional()` in `SessionMeta`; the fixtures gain it. No visible
  change; the committed static build is regenerated because the bundle changes.

### A.5 `schemas/`

JSON Schema 2020-12, `$id` `https://ostler.tech/schemas/<name>.schema.json`, custom keys
`x-…`, `jsonschema` in `[dev]`:

- `signal-store.schema.json`: a store module file; the existing keys plus an optional
  `metric` matching the VSS path pattern; no other key except `x-…`.
- `layout.schema.json`: a pack's `layout.json`; checks `group_order`, `drive` views and
  tiles, `util_lids` and `notices` where present and allows other keys.
- `vehicle.schema.json`: `logs/vehicle.json`; no other key (so never a VIN) except `x-…`.
- `session-meta.schema.json`: a session `meta.json`, with RFC 3339 UTC `Z` timestamps.

Tests validate the fake pack's store and layout, the D2 pack's (`needs_pack`), a freshly
recorded `meta.json` and `vehicle.json`. `capabilities.schema.json` waits for U3.

## B. API contracts

- `api/openapi.yaml` (OpenAPI 3.1.1) documents every HTTP route of `web/server.py`, with
  shared components for errors, RFC 3339 timestamps, VSS units, GeoJSON traces and `vid`
  on sessions. A pytest walks the server's routes and fails on any undocumented one.
- `api/asyncapi.yaml` (AsyncAPI 3.0) documents the SSE stream; MQTT channels come at U5.
- Response examples reuse the UI contract fixtures (`ui/src/api/fixtures/`), so the Zod
  schemas, the fixtures and the API files describe one shape.

## C. Repo hygiene

- **REUSE 3.3:** `LICENSES/` (AGPL-3.0-or-later, CC-BY-SA-4.0, MIT, MPL-2.0), `REUSE.toml`
  and SPDX headers on `.py`, `.ts` and `.tsx`; `reuse lint` in CI. `vss/upstream/**` is
  MPL-2.0; `vss/ostler.vspec` and pack-style data are CC-BY-SA-4.0; the generated
  `metrics.json` (overlay plus VSS descriptions) is `MPL-2.0 AND CC-BY-SA-4.0` and
  `vss_leaves.json` is MPL-2.0. Docs stay under the code licence (owner, 2026-10-06).
- **PEP 639:** `license = "AGPL-3.0-or-later"`, `license-files`, `setuptools>=77`.
- **Security:** `SECURITY.md` (private vulnerability reporting, 14-day acknowledgement,
  a stated support period); Dependabot for pip, npm, github-actions and docker; OpenSSF
  Scorecard; actions pinned by SHA; default `permissions: contents: read`.
- **Release:** a release workflow that attaches SPDX and CycloneDX SBOMs and provenance.
- **Tooling:** ruff (target py39) and pre-commit (ruff, reuse, frontmatter, index);
  `CHANGELOG.md` in Keep a Changelog form, recording the VSS pin.

## D. The Discovery 2 pack fills its metrics

- The pack adds `metric` to its common-set fields through `upsert_field`, per [vehicle
  data model §4.4](../references/research/ui/vehicle_data_model.md): speed, rpm, coolant,
  battery, external air temperature, MAP, MAF, accelerator pedal, low range and the raw
  ride heights (`Vehicle.Ostler.Chassis.RideHeight.*`). There is no fuel-level source.
- Units, confidence and labels are unchanged; D2 coverage stays the same. The platform's
  `needs_pack` test checks that every `metric` resolves, and the store schema validates.

## Acceptance

- `OSTLER_REQUIRE_PACK=1 pytest -q` passes, and `pytest -q` without the pack passes with
  skips; `python tools/build_metrics.py --check` passes.
- `npm run check` and `npm run e2e` pass; there is no visible UI change.
- The docs validators pass.

## Changelog

- 2026-10-06 — v1.0: U0 design, approved by the owner.
