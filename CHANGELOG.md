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
