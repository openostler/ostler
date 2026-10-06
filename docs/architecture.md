---
title: Architecture and key seams
area: docs
status: stable
version: 2.1
updated: 2026-10-06
depends_on: [SCOPE.md, CONSTITUTION.md]
summary: >
  Developer map of the platform code: the bottom-up protocol stack, the VehiclePack seam,
  the seams to understand before changing things (frame formats, EcuSession, signal store,
  VSS metrics, vehicle id, schemas, DataSource boundary, the two command paths, the API
  contracts in api/, NodeSource and the MQTT client) and the dev commands.
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

# A Brain: read the car through the node's MQTT messages (read-only, NodeSource P1)
PYTHONPATH=src python3 tools/dashboard.py --source node --mqtt mqtts://brain.local:8883 \
    --mqtt-ca ca.pem --mqtt-cert brain.crt --mqtt-key brain.key [--vid VID]

# UI development without a car: the test-only server on simulated sources
# (the same one Playwright drives); --node serves them through NodeSource and a fake broker
PYTHONPATH=src python3 tests/e2e_server.py [--node]
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
               + kline/profiles.py (protocols as data) + detect.py, keywords.py, frame_iso9141.py
KWP2000        kwp2000/: service IDs, negative responses (0x7F+NRC), responsePending (0x78)
OBD-II         obd/: the J1979 service layer over an ObdRequestLink (kline/obd_link.py,
               can/obd.py)
CAN            can/: frame-level CanLink beside Transport (SocketCAN, slcan, GVRET,
               python-can), passive bitrate detection, ISO-TP, TxGate
MQTT / node    mqtt/: stdlib MQTT 5 codec + client; node/: the device table (a Brain
               reads the node's VSS messages; web/node_source.py is the DataSource)
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
  - SLABS passes `after=None`, because its services work right after fast init. Its
    K-line profile's `keepalive` is a bare `3E`, which `tester_present()` sends; a session
    built without a profile uses the legacy `_keepalive_sub` (SLABS sets it to `None`).
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
- **K-line profiles and detection (ADR-0022,
  [spec](../specs/2026-10-06-kline-profiles-detection-design.md)).**
  - A `KLineProfile` (`kline/profiles.py`) is the protocol as data; packs override it via
    `ModuleSpec.kline`. `KLine.from_profile`/`KWP2000.from_profile` build a link from it;
    the legacy constructors are unchanged (the D2 pack still uses them).
  - `kline.detect.detect()` is a probe (fast init, then 5-baud `0x33`). Probes, and
    `module_scan` sweeps, run only through the queued server commands `detect_protocol`
    and `module_scan`, behind the Parked gate in `web/kline_cmds.py` (until U2:
    `--kline-detect`, `params.confirm_parked`, no motion). Re-init of a known profile is
    never gated.
  - `web/kline_source.py::KLineLinkSource` is the generic link source: `needs-detect`
    without a profile, keep-alive via `tick()`, and the detected profile remembered per
    `vid` in `<state dir>/kline_profiles.json`. Snapshots carry `link` (null without one).
- **The J1979 service layer (`obd/`,
  [spec](../specs/2026-10-06-j1979-service-layer-design.md)).**
  - `J1979` talks to an `ObdRequestLink` that returns every responder's whole service
    messages keyed by ECU address (`EcuReply`); `obd` imports no transport, and the K-line
    adapter `kline/obd_link.py` (ISO 9141-2 and KWP2000 framing) imports `obd.link`.
    Pacing, the late-frame drop and the typed per-ECU status live in `obd/link.py`.
  - PID formulas are a pack's store records with `x-obd {service, pid, len}`
    (`PidTable.from_records`); the platform ships none. Decoders are pure (`obd/decode.py`)
    and checked by the shared vectors in `tests/vectors/j1979/` (ADR-0032).
  - Mode 08 is never sent; Mode 04 runs only through `J1979.clear_dtcs(grant)` with a
    grant from `obd/clear.py::ClearGate` (Parked or Idling, local link, one confirmation,
    automatic logbook snapshot first, audit; ADR-0033). No server route mints a grant
    until U2. The VIN goes only to an `on_vin` callback (ADR-0036).
- **The CAN path (`can/`, ADR-0020, ADR-0023,
  [spec](../specs/2026-10-06-canlink-isotp-design.md)).**
  - `CanLink` is frame-level, beside the byte `Transport`. Every backend opens
    listen-only (SocketCAN on stdlib `AF_CAN` with `CanIfControl` over `ip`; slcan over
    serial or TCP; GVRET; python-can only with the `[can]` extra). `send()` raises
    `RateNotConfirmed` until the rate is confirmed or declared, and every frame passes
    `TxGate`: Tier 0 reads (and their FCs) on the diagnostic ids in any driving state,
    anything else only with a pack allowlist entry, the entry's driving state and a
    single-use `TxGrant`. A permitted send turns listen-only off; the session end or
    30 s idle turns it back on.
  - `can.detect()` listens at 500k then 250k (20 clean frames), then sends one `01 00`;
    a silent bus gets one Parked-only one-shot probe per rate. ISO-TP is our own
    (`isotp.py`); `CanObdRequestLink` (`can/obd.py`) makes `J1979` work over CAN.
    `LoggingCanLink` writes JSONL and candump with the VIN scrubbed.
  - Lab/reference only: production CAN I/O and the production gate are the node's TWAI
    and C `TxGate` (ADR-0032), checked by the shared vectors in `tests/vectors/can/`.
    Tests run on `tests/fake_can.py` (a virtual-clock bus); `needs_vcan` tests use a real
    `vcan0` when the runner has one.
- **NodeSource: the Brain reads the node (`mqtt/`, `node/`, `web/node_source.py`,
  [spec](../specs/2026-10-06-node-source-design.md), ADR-0032).**
  - `openostler.mqtt` is our stdlib MQTT 5 client behind the `MqttClient` interface (a
    paho adapter could replace it without touching NodeSource); the same codec drives
    the test broker `tests/fake_broker.py`. TLS is mTLS via `tls_context()`; `mqtt://` is
    for a lab broker only (`--mqtt-insecure-lab`).
  - `NodeFeed` holds one read-only connection (`status`, `power`, `vss/+` of one `vid`;
    No Local, Retain As Published off, clean start) and fills `node.DeviceTable` from the
    MQTT thread; `NodeSource` (one per pack module, all over one feed) builds the snapshot
    from it under a lock. Selecting a module only filters the view.
  - Staleness is per signal on the node's own clock (`t_us`); a retained value at
    subscribe time is "last known"; reboots come from the payload's `boot` id (or `t_us`
    going backwards); confidence is never raised (the lower of node and store wins).
    Units pass through until U3.
  - A source declares `source_kind` (`serial`, `kline`, `node`), may map its statuses to
    `conn` (`conn_for`, used by `_next_conn`), and `touches_car = False` makes the server
    refuse the commands that open the serial port itself (`read_all_faults`, `set_port`,
    the probes). P1 publishes nothing and records no sessions (P2).
  - Fixtures are the firmware host tests' JSONL dumps in `tests/fixtures/node/`;
    `tests/fake_node.py` replays them; `needs_broker` tests use a real Mosquitto.
- **The UI contract.** `ui/src/api/schemas.ts` (Zod) describes every response.
  `tests/test_ui_contract.py` checks the real server against the fixtures in
  `ui/src/api/fixtures/`, and the UI tests parse the same fixtures. Signal labels,
  groups and descriptions come from `/fields`, which reads the signal store plus
  `sources.DERIVED_FIELDS`. The UI never hard-codes them.
- **Admin and public mode.** Admin routes sit behind HTTP Basic auth when an admin password
  is set (`_Handler._require_admin`); with none they are open, which is for local dev only.
  `--public` therefore refuses to start without a password, and public mode refuses
  actuators, uploads and community writes (`_PUBLIC_REFUSAL`).
- **The API contracts (`api/`, ADR-0017).** `api/openapi.yaml` (OpenAPI 3.1.1) documents
  every HTTP route of `web/server.py`: parameters, bodies, response schemas, errors,
  admin gating (`x-ostler-access`) and public-mode behaviour (`x-ostler-public-mode`).
  `api/asyncapi.yaml` (AsyncAPI 3.0) documents the `/events` SSE stream and reuses the
  OpenAPI `Snapshot` schema. `components.x-ostler-wire-conventions` holds the wire rules
  (RFC 3339 UTC `Z`, VSS units, GeoJSON, `vid`). `tests/test_api_contracts.py` reads the
  routes from the server's source, so adding or removing a route without updating
  `openapi.yaml` fails, and it validates the UI fixtures against the response schemas.
  How to view and maintain them: [api/README.md](../api/README.md).
  - Every API error is one envelope, `{ok: false, error, code?}`, sent by
    `_Handler._error`; `/command` maps its reply's `code` to the status through
    `_STATUS_FOR_CODE` (502 when the car refuses, 504 on a poll timeout). Routes match
    `path` (no query string), and an unknown browser page gets the app shell
    ([API consistency spec](../specs/2026-10-06-api-consistency-design.md)).
  - Wire timestamps are RFC 3339 UTC `Z` from `openostler.timefmt.rfc3339_utc`; traces
    are GeoJSON (`SessionData.trace`, `?fmt=geojson`).
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
- 2026-10-06 — API consistency: one error envelope and status table, query strings on
  every route, `timefmt`, GeoJSON traces (specs/2026-10-06-api-consistency-design.md).
- 2026-10-06 — K-line profiles and detection (ADR-0022): `kline/profiles.py`, `detect()`,
  ISO 9141-2 framing, session hygiene, the Parked gate and the snapshot `link`.
- 2026-10-06 — J1979 service layer (`obd/`, `kline/obd_link.py`, `testing/`): request
  model, decoders, `PidTable`, Diagnostics, the Mode 04 gate, shared vectors.
- 2026-10-06 — CAN path (`can/`): CanLink and backends, passive bitrate detection,
  ISO-TP, TxGate, the J1979 CAN adapter, LoggingCanLink, the fake bus and shared vectors.
- 2026-10-06 — v2.1, NodeSource P1: `mqtt/` (stdlib MQTT 5 client), `node/` (the device
  table), `web/node_source.py`, `--source node`, `source_kind`, `conn_for`, `touches_car`.
