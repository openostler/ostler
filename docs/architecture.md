---
title: Architecture and key seams
area: docs
status: stable
version: 1.6
updated: 2026-10-06
depends_on: [SCOPE.md, CONSTITUTION.md]
summary: >
  Developer map of the platform code: the bottom-up protocol stack, the VehiclePack seam,
  the seams to understand before changing things (frame formats, EcuSession, signal store,
  VSS metrics, vehicle id, schemas, DataSource boundary, the two command paths, the API
  contracts in api/) and the dev commands.
---

# Architecture and key seams

The boundary and mission are in [SCOPE.md](../SCOPE.md). The rules that must not be
broken are in [CONSTITUTION.md](../CONSTITUTION.md). This page is the working map.

## Commands

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"          # only runtime dep is pyserial; dev adds pytest, jsonschema, vss-tools
# the Discovery 2 reference pack (integration tests, the dashboard, e2e)
pip install --no-deps "d2diag @ git+https://github.com/JamesWrightDavid/discovery2-diag"

pytest -q                        # whole suite, no hardware needed
python tools/build_metrics.py    # regenerate metrics.json after editing vss/ (--check in CI)
pytest -m "not needs_pack" -q    # platform-only (fake pack)
pytest tests/test_web.py -k slabs_empty_read_grace -q   # one test

# Dashboard: always live (ignition on, stationary); there is no mock/demo mode
PYTHONPATH=src python3 tools/dashboard.py --serial /dev/cu.usbserial-XXXX [--module slabs] [--fault-watch] [--csv] [--geocoder URL|off] [--replay FILE|pack]

# UI development without a car: the test-only server on simulated sources
# (the same one Playwright drives)
PYTHONPATH=src python3 tests/e2e_server.py
```

`pyproject.toml` sets `pythonpath = ["src", "."]`, so `pytest` works without
`PYTHONPATH`; the `tools/*.py` scripts need it (or an editable install). There is no
linter or formatter config, so match the surrounding style.

## The stack

It is strictly bottom-up. No layer knows anything about the layer below it beyond that
layer's interface, and each layer is unit-tested in isolation.

```
Transport      transport/base.py: raw bytes in/out (SerialTransport, LoggingTransport)
K-Line         kline/frame.py (encode/decode) + kline/kline.py (fast/slow init, echo, retries)
KWP2000        kwp2000/: service IDs, negative responses (0x7F+NRC), responsePending (0x78)
EcuSession     session.py: shared lifecycle/keepalive/read_block + tolerant establish retry
VehiclePack    pack.py: the contract + loader (entry-point group "openostler.vehicle");
               module layers (D2: td5/ slabs/ airbag/ …) live in the pack repo
Side inputs    gps/ (NMEA fixes) → logbook/ (session recorder + store + index + exports,
               ADR-0009/0011); geo/ (offline GeoNames + OSM Nominatim place names)
Web            web/: stdlib HTTP + SSE server; serves the built UI from web/static
UI             ui/: Vite + React + TypeScript app → npm run build → web/static (committed)
```

## Key seams

- **The `VehiclePack` seam (`pack.py`, ADR-0013/0015).**
  - `active_pack()` resolves the installed pack from the `openostler.vehicle` entry points
    (legacy `ostler.vehicle` read for one release); `OSTLER_VEHICLE` picks one when several
    are installed. With none it raises `NoVehiclePackError` naming the group and the fix.
  - Everything vehicle-specific (modules, sources, stores, actions, menus, fault readers,
    sniff detection, demo data, docs, the UI `layout`) comes from the pack. The platform
    imports no pack; `tests/test_layering.py` enforces it.
  - Platform tests run against `tests/fake_pack.py`; `needs_pack` tests use the D2 pack.
- **Two frame formats.**
  - Addressed framing (`0x8n`, target+source) is used only for StartCommunication and
    fast init.
  - After that, the whole session uses unaddressed length-prefixed frames
    (`<len> <SID> … <cs>`). `kline.read_frame` sniffs the format byte.
  - Airbag is the exception: it uses addressed framing throughout at 0x5B.
- **`EcuSession` is where module layers share behaviour.**
  - Subclasses set `name` and call `_establish(after=…)`.
  - Td5 passes `after=self.connect` (StartDiagnosticSession + SecurityAccess seed→key).
  - SLABS passes `after=None`, because its services work right after fast init. It also
    sets `_keepalive_sub = None` so it gets a bare `3E`.
- **`EcuSession.read_block(lids) -> {lid_hex: bytes}`** has exactly the shape
  `sniff/automap.py` consumes. That lets a live session feed the differential mapper.
- **Signal store (each pack's `signals/*.json`, loaded by `signals/`).**
  - Decoders, the dashboard and automap all read it.
  - Confirmed mappings are written back with `upsert_field`.
  - Each field carries `confidence`, either `proven` or `candidate`.
  - A field may carry `metric`, a COVESA VSS path (below); pack-private fields need none.
- **Metrics: the VSS namespace (`metrics.py`, `vss/`, ADR-0016).**
  - `vss/` pins VSS 6.1 (`vss/upstream/`, MPL-2.0) and holds the overlay
    `vss/ostler.vspec`: the OVMS, Home Assistant and OBDb aliases and the Home role on
    existing nodes, plus the `Vehicle.Ostler.*` extensions. It is the only alias source.
  - `tools/build_metrics.py` (dev-only, vss-tools) writes `src/openostler/metrics.json`
    (the annotated and extension leaves) and `vss_leaves.json` (every upstream leaf and
    its unit). Both are committed and shipped; `--check` runs in CI.
  - At runtime `openostler.metrics` (stdlib) reads them: `load_metrics()`,
    `metric_info(path)`, `is_known(path)`. `upsert_field` refuses an unknown `metric`.
  - Units are VSS unit keys copied verbatim from `vss/upstream/units.yaml` (`Celsius`,
    `km/h`). Pack store units stay display units until U3 converts at the mapping step.
- **`web/sources.py` is the protocol/UI boundary.**
  - Each `DataSource.poll()` returns `{status, signals, faults}`.
  - The product always uses live sources; there are no server modes (ADR-0011). The
    simulated sources live only in `tests/` (`tests/fake_sources.py`), used by the tests
    and by `tests/e2e_server.py`.
  - Adding a module to the dashboard means adding a source pair, not touching the server.
- **Two command paths in `web/server.py`.**
  - `_INLINE_COMMANDS` (CSV start/stop, fault-watch) run on the HTTP thread.
  - Everything that touches the K-line is queued for the poll thread. Queued commands can
    wait out a ~20 s reconnect, which is longer than the 8 s HTTP timeout.
- **The UI contract.** `ui/src/api/schemas.ts` (Zod) describes every response.
  `tests/test_ui_contract.py` checks the real server against the fixtures in
  `ui/src/api/fixtures/`, and the UI tests parse the same fixtures. Signal labels,
  groups and descriptions come from `/fields`, which reads the signal store plus
  `sources.DERIVED_FIELDS`. The UI never hard-codes them.
- **The API contracts (`api/`, ADR-0017).** `api/openapi.yaml` (OpenAPI 3.1.1) documents
  every HTTP route of `web/server.py`: parameters, bodies, response schemas, errors,
  admin gating (`x-ostler-access`) and public-mode behaviour (`x-ostler-public-mode`).
  `api/asyncapi.yaml` (AsyncAPI 3.0) documents the `/events` SSE stream and reuses the
  OpenAPI `Snapshot` schema. `components.x-ostler-wire-conventions` holds the wire rules
  (RFC 3339 UTC `Z`, VSS units, GeoJSON, `vid`). `tests/test_api_contracts.py` reads the
  routes from the server's source, so adding or removing a route without updating
  `openapi.yaml` fails, and it validates the UI fixtures against the response schemas.
  How to view and maintain them: [api/README.md](../api/README.md).
- **Session logbook (`logbook/`, ADR-0009/0011).**
  - The recorder opens a session only while the car is connected. While disconnected
    it is *paused*: no data rows (not even GPS), and it ends after 300 s.
  - The demo is the pack's committed, read-only synthetic sessions (`pack.demo`, for the D2
    pack "Demo log 1" and "Demo log 2"), replayed through the whole app. The public
    server lists only these.
  - `logbook/index.py` `SessionIndex` is a stdlib-`sqlite3` index (FTS5 where available)
    behind `GET /sessions` (keyset paging, search, filters), `/sessions/histogram` (the
    month scrubber) and `PATCH /sessions/<id>` (name and description). It rebuilds itself
    from the session files when missing or on a schema change.
- **Vehicle id (`logbook/vehicle.py`, UI spec §4.1).**
  - `logs/vehicle.json` (`{vid, pack, created_utc}`) is created once, next to
    `logs/sessions/`; `OSTLER_VEHICLE_ID` overrides the vid. It never holds a VIN.
  - The recorder stamps `vid` into every new non-synthetic session's `meta.json`. The store
    reads a session without one (older logs, demo logs) as the local vid, on read only.
  - The session index (schema 3) has a `vid` column; `/sessions` responses carry `vid`.
- **Schemas (`schemas/`, ADR-0017).** JSON Schema 2020-12 for the signal-store module
  file, a pack's `layout.json`, `logs/vehicle.json` and a session `meta.json` (RFC 3339 UTC
  `Z` timestamps), `$id` under `https://ostler.tech/schemas/`, custom keys `x-…`.
  `tests/test_schemas.py` validates the fake pack, the D2 pack and freshly written files;
  `jsonschema` is dev-only.
- **Place names (`geo/`).**
  - `geo.offline.label(lat, lon)` names a point from a trimmed GeoNames `cities1000`
    table (`geo/places.tsv.gz`, built by `tools/build_places.py`, CC BY 4.0).
  - `geo.nominatim.Enricher` refines it from OSM Nominatim when online, within the usage
    policy: at most 1 request/s, a custom User-Agent, results cached in
    `logs/geocache.json`, exponential back-off. `--geocoder URL|off` sets the endpoint;
    tests use `off`.
  - The Logs footer credits OpenStreetMap contributors (ODbL) and GeoNames (CC BY 4.0).
- **`faultscan.py`** reads every module strictly in sequence: establish → read → release.
- **`web/docs.py`** serves the canonical markdown fresh on every request, with the
  frontmatter stripped. It is a window on the source. Never cache or duplicate it.
- **`community/`** is the opt-in contribution client. Its service (the former
  `server/endpoint.py`) moved to the private `ostler-cloud` seed at the split; both are
  whitelist-based and PII-free.

## Why the protocol rules exist

- **SLABS load.** Block-reading many LIDs every 0.5 s killed the SLABS session after
  ~15 s (the D2 pack's `references/slabs/overview.md`).
- **What `7F 81 10` means.** A generalReject on StartCommunication means a link is still
  open on the shared bus. There are two teardowns:
  - `20` StopDiagnosticSession ends a Td5 diagnostic session.
  - `82` StopCommunication ends the link that fast init created.
- **The link outlives the process.** This was proven in the car on 2026-08-18.

## Conventions

- **Fakes.** `tests/fakes.py::FakeKLineEcu` is a half-duplex ECU simulator at the
  transport level: it echoes frames like the real bus. A response can be:
  - static bytes,
  - a sequence,
  - a `callable(count)`, when a test needs different values between reads.
- **Comments explain *why*.** Say which sniff or log a protocol fact came from. Vehicle
  findings from the car or a capture are recorded in the pack's `references/*.md`.
- **The car-test backlog is per pack** (D2: `references/test_plan.md` in the pack repo).
  Every open hardware question goes there, with a procedure and a decision rule written
  before the test.
- **`TODO.md`** is code and infrastructure only.

## Changelog

- 2026-09-30 — Extracted from the former root CLAUDE.md during Vibes as Code adoption.
- 2026-10-01 — Confidence vocabulary is now `proven`/`candidate` (ADR-0006).
- 2026-10-01 — Added the React/TypeScript UI layer and its contract.
- 2026-10-05 — Added `gps/` and `logbook/`: the server feeds every poll and the latest GPS fix
  to the session recorder; `/sessions*` serves replay data (ADR-0009).
- 2026-10-06 — No mock/demo mode: always live, demo logs replayed, simulated sources
  test-only (`tests/e2e_server.py` for UI work); record only while connected; `geo/` place
  names and the SQLite session index (ADR-0011).
- 2026-10-06 — Repo split (ADR-0015): this is the platform (`openostler`); the
  `VehiclePack` seam; module layers, the signal store data and the car-test backlog live in
  the packs; `needs_pack` integration tests; `--replay pack`.
- 2026-10-06 — Added the API contracts (`api/openapi.yaml`, `api/asyncapi.yaml`) and their
  route-documentation test (ADR-0017).
- 2026-10-06 — U0 seams (specs/2026-10-06-u0-seams-design.md): VSS metrics
  (`metrics.py`, `vss/`, `tools/build_metrics.py`), `metric` on store records, the
  vehicle id, index schema 3 and `schemas/`.
