---
title: "API consistency — error envelope, status codes, query strings, RFC 3339 timestamps, GeoJSON traces — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [decisions/adr-0017-open-standards-first.md, specs/2026-10-06-u0-seams-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md]
summary: >
  Makes the HTTP/SSE API consistent before U1. Every API error becomes one JSON envelope {ok: false, error, code?} (HTML only for app pages), status codes follow one table (400/401/403/404/409/413/500, plus the existing 416/503), and one route matcher ignores the query string everywhere. Epoch timestamps gain RFC 3339 UTC `Z` siblings (`ts_utc`, `since_utc`, `t0_utc`, `start_utc`), the replay track gains a GeoJSON LineString Feature (`trace`) and a GeoJSON export, and the old fields are removed one minor release later. Covers OpenAPI versioning, deprecation markers, the new contract-test rules, a non-breaking step order and the D2 pack impact.
---

# API consistency — design

## Context

U0-B documented the API as it is ([U0 seams §B](2026-10-06-u0-seams-design.md#b-api-contracts)),
including its warts: `components.x-ostler-wire-conventions.timestamp-deviations`, the
`x-ostler-query-string: refused` marks and the `NotFoundHtml` responses in
`api/openapi.yaml`. [ADR-0017](../decisions/adr-0017-open-standards-first.md) adopts
RFC 3339 (UTC `Z`) for every wire timestamp and GeoJSON (RFC 7946) for traces. U1 builds a
new shell on this API ([UI architecture §10](2026-10-06-ui-architecture-design.md#10-phased-migration)),
so the contract should be fixed first, not after more screens depend on it.

Verified in `src/openostler/web/server.py` (2026-10-06, `claude/specs-t1s-obd`):

1. **Query strings 404.** `do_GET`/`do_POST` compare the raw `self.path` with `==`/`in` for
   the app pages, `/events`, `/snapshot`, `/community`, `/docs`, and POST `/command`,
   `/calib`, `/automap`, `/capture`, `/signal`, `/community/consent`,
   `/community/contribute`. Other routes use `self.path.split("?")[0]`. Sixteen
   operations carry `x-ostler-query-string: refused`.
2. **Status codes.** `/command` maps every `ok: false` to 400, including public-mode
   refusals (the `partial` mode), `split_session` while not recording (`NOT_RECORDING`;
   `/notes/live` answers the same condition with 409) and an unknown command.
   `_calibrate`, `_automap` and `_append_capture` failures are sent with 200. `/signal`
   answers 400 for everything, including an `OSError` on write. `community disabled` is
   400. `GET /sessions/<id>/data|export` maps an `OSError` to 400.
3. **Timestamps.** Epoch seconds: the snapshot `ts` (`_decorate`), `recording.since`
   (`SessionRecorder.status`) and `active_test.since` (`_note_command_result`). Epoch ms:
   `SessionData.utc` (per sample) and the audio `start` query. `_append_capture` writes
   `t` with `time.strftime("%Y-%m-%d %H:%M:%S")`: local time, no offset.
4. **Track.** `SessionStore.data()` returns `track` as `[lon, lat, Interval]`; in GeoJSON
   a third member is altitude.
5. **HTML errors.** The `else` branches of `do_GET`/`do_POST`, a missing `/doc` id and a
   missing static file call `send_error(404)`: the stdlib HTML page. `_require_admin`
   sends 401 with an empty body. A method the handler lacks (e.g. `PUT`) gets the stdlib
   501 HTML page.

`ui/src/api/client.ts` `parse()` reads the JSON body whatever the status, and the UI keys
on `ok`/`error`. Status-code changes therefore do not break the UI; field renames do.

## 1. Error envelope

- Every API error body is `ErrorReply`, `{ok: false, error, code?}`, as
  `application/json`. `error` is one English sentence for people; clients never parse it.
  `code` is an optional stable token (`^[a-z][a-z0-9_]*$`) for programs: `bad_request`,
  `auth_required`, `public_mode`, `read_only`, `not_found`, `not_recording`,
  `disconnected`, `too_large`, `unavailable`, `internal`. Extra fields stay allowed
  (`diff` on automap, `queued` on community).
- **Rule:** a 4xx/5xx JSON body is always the envelope, and a 2xx body never carries
  `ok: false`.
- **HTML stays only for app pages** (`/`, `/admin`, legacy pages), whose success is HTML
  and whose 401 stays bodiless so the browser shows its Basic Auth prompt. `/doc` success
  stays an HTML fragment; its 404 becomes the envelope.
- **Mechanism.** `_Handler.send_error()` is overridden to write the envelope (no body
  for `HEAD`), which also covers the stdlib's own 501, 400 and 414. One
  `_error(status, error, code=None)` helper replaces the inline `self._json({"ok": False,
  …}, n)` calls. `ApiError` gains an optional `kind` (sent as `code`); its `.code` stays
  the HTTP status. `_require_admin` sends the envelope (`auth_required`) with
  `WWW-Authenticate` on API routes.

## 2. Status codes

| Status | Meaning | Examples |
|---|---|---|
| 400 | Bad input | malformed JSON, invalid param, unknown command or export format, calibration or automap samples that cannot be solved |
| 401 | Admin auth missing or wrong | any `x-ostler-access: admin` route |
| 403 | Refused by policy | public-mode refusal (`_PUBLIC_REFUSAL`), a write to a synthetic session |
| 404 | Unknown | route, session, note, track, doc, static file; public-mode `hidden`/`filtered` |
| 409 | Conflict with server state | not recording, disconnected, community off, shutdown not enabled |
| 413 | Body too large | `_read_capped` |
| 416 | Bad range (unchanged) | `GET /sessions/{id}/audio/{track}` |
| 500 | Unexpected failure | an uncaught exception, an `OSError` writing the store or captures |
| 503 | Temporarily unavailable (unchanged) | index not ready, recording or catalog not available |

Corrections:

| Route | Today | New |
|---|---|---|
| `POST /command` refusal in public mode | 400 | 403 `public_mode` |
| `POST /command` `split_session` not recording, `disconnected — connect first`, shutdown not enabled | 400 | 409 |
| `POST /command` recording not available | 400 | 503 |
| `POST /command` unknown command or bad params | 400 | 400 (unchanged) |
| `POST /calib`, `/automap` failure | 200 | 400 (`no_match` for an automap with no fit) |
| `POST /capture` write failure | 200 | 500 |
| `POST /signal` unknown module, missing fields, bad `metric` / `OSError` | 400 / 400 | 400 / 500 |
| `POST /community/*` community disabled | 400 | 409 |
| `GET /sessions/{id}/data` or `/export` `OSError` | 400 | 500 |
| unknown route, missing `/doc`, missing static file, unsupported method | HTML | envelope |

For `/command`, `refusal()` and the inline commands return `{ok: false, error, code}`; one
table `_STATUS_FOR_CODE` maps `code` to the status. An `ok: false` without a `code` keeps
400 until every producer sets one. An action the car itself fails, or a poll-thread
timeout, is an open question (Q1).

## 3. Query strings

- Each `do_*` computes `path = self._path()` once (`urlsplit(self.path).path`). Every
  exact route compares `path`, not `self.path`, and the query is read with `self._query()`.
  `_static_file`, `_session_parts` and `_sessions_get` take the same `path`.
- No percent-decoding or trailing-slash folding is added for exact routes (behaviour
  stays as is for paths without a query). `/sessions/…` keeps its `unquote`.
- OpenAPI drops `x-ostler-query-string` and its description paragraph; AsyncAPI drops
  "a query string answers 404" from the `events` channel.

## 4. Timestamps

Format: RFC 3339, UTC, `Z`, millisecond precision (`2026-10-05T09:00:00.000Z`), from one
stdlib helper (`openostler/timefmt.py`, `rfc3339_utc(epoch_s)`), promoted from
`logbook/export.py::_iso_ms`. New names use the `_utc` suffix already used by `start_utc`,
`end_utc` and `created_utc`, and keep it after the old field goes (no second rename).

| Where | Today | Added (0.1.0) | Removed (0.2.0) |
|---|---|---|---|
| Snapshot (`/snapshot`, `/events`) | `ts` epoch s | `ts_utc` | `ts` |
| `recording` | `since` epoch s | `since_utc` | `since` |
| `active_test` | `since` epoch s | `since_utc` | `since` |
| `SessionData` | `utc[]` epoch ms per sample | `t0_utc`: the wall-clock instant of session ms 0, from the first sample with `Utc` (`null` without one) | `utc` |
| `POST /sessions/{id}/audio` | `start` epoch ms | `start_utc` query; both accepted, `start_utc` wins | `start` |
| `logs/labeled_captures.jsonl` | `t` local, no offset | written as RFC 3339 UTC `Z` | — |

- `t0_utc` replaces the per-sample array because the UI uses `utc` only for the offset
  (`utcAt`/`utcOffset` take the first non-null `utc - t`); this also drops 2,000 numbers
  from a `/data` reply.
- The captures file is append-only and never rewritten: old rows keep local time. Its
  `t` is not on the wire (`/captures` sends `t: null` for file rows); any reader treats a
  naive time as unknown, never guesses an offset.
- **Exemptions, documented in the wire conventions:** durations and session offsets in
  ms (`t`, `t_ms`, `start_ms`); CSV columns; the accel sample arrays (Q4).

## 5. Tracks

`SessionData` gains `trace`, a GeoJSON Feature (RFC 7946) next to `track`:

```json
{"type": "Feature",
 "geometry": {"type": "LineString", "coordinates": [[-4.68, 56.62], [-4.67, 56.63]]},
 "properties": {"t_ms": [0, 1000]}}
```

- Positions are `[lon, lat]` only. `properties.t_ms` is session ms, the same length and
  order as `coordinates`: the documented equivalent of the togeojson `coordTimes`
  convention, in session time because the replay timeline is session ms
  (`t0_utc + t_ms` gives the instant). It uses the same `reduce_track` points as `track`.
- `trace` is `null` when there are fewer than two positions (a LineString needs two).
- `track` stays for one minor release, marked deprecated, then goes (§6).
- **GeoJSON export:** `GET /sessions/{id}/export?fmt=geojson` returns
  `application/geo+json`, `<id>.geojson`, from `logbook/export.py::to_geojson`: a
  FeatureCollection with one LineString Feature of every GPS point (full resolution, like
  GPX) with properties `coordTimes` (RFC 3339 UTC `Z`, the togeojson convention, so other
  tools read the time), `t_ms`, `id` and `start_utc`, plus a Point Feature per note
  (`kind`, `text`, `tags`, `t_ms`, `time`), as GPX has `<wpt>`. No `crs` member; the same
  public-mode filtering as GPX. Added to `_EXPORT_FORMATS`, `_EXPORTS`, the OpenAPI `fmt`
  enum and `api.sessionExportUrl`.

## 6. Versioning and deprecation

- **API version = platform version.** `info.version` in both API files equals
  `openostler.__version__` (already tested). Each step below bumps it with the release.
- **SemVer note in `CHANGELOG.md` (Versioning):** while on `0.y.z`, a field, parameter or
  route of the HTTP/SSE API is removed or renamed only after one minor release in which
  it is marked deprecated. Additions can come in any release. Status-code and
  error-body corrections are listed under *Changed*.
- **Markers:** in OpenAPI the old property or parameter gets `deprecated: true` (JSON
  Schema 2020-12) and `x-ostler-removed-in: "0.2.0"`; the wire conventions list each
  deviation with its replacement and removal version; the CHANGELOG has a *Deprecated*
  entry. Responses carrying a deprecated field (and the `/events` response) send
  `Deprecation: @<epoch of the deprecating release>` (RFC 9745) and a `Link` with
  `rel="deprecation"` to the CHANGELOG. No `Sunset`: a field is not a resource.

## 7. Contracts and tests

`tests/test_api_contracts.py` gains:

- **No query-string 404s.** Statically, no `self.path ==`/`in` comparison remains in
  `do_*` (the route extractor reads the `path` local) and no operation has
  `x-ostler-query-string`. At runtime, against a fake-pack `DiagServer` with an admin
  password, every documented exact GET and POST route with `?_=1` answers the same status
  as without it, never 404.
- **Error bodies are the envelope.** Every documented 4xx/5xx of a non-app operation
  references `ErrorReply` (with its optional `code`), and `NotFoundHtml` is gone. At
  runtime an unknown GET/POST/PATCH/DELETE path, `PUT /snapshot`, `/doc?id=nope`,
  `/nope.js` and an admin route without auth return a valid envelope.
- **Status table.** Every documented status is in §2's table; every `ok: false` fixture
  maps to a non-2xx status and every 2xx fixture lacks `ok: false`.
- **Timestamps.** Every schema property named `*_utc` references `Rfc3339Utc`; every
  `EpochSeconds` use is `deprecated: true` until 0.2.0, then the schema is absent; every
  `*_utc` fixture string matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`;
  a unit test checks the captures writer.
- **Traces.** The `session-data` fixture's `trace` validates as a Feature whose geometry
  is `GeoJsonLineString`, `len(t_ms) == len(coordinates)`, and positions have two
  members; a `to_geojson` test validates its FeatureCollection.

UI side: `schemas.ts` adds the new fields; fixtures are regenerated
(`UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`), plus new fixtures
`command-not-recording` (409) and `error-not-found` (404) mapped in `FIXTURE_ROUTES` and
`schemas.test.ts`. Existing asserts follow: the public refusals in `tests/test_web.py`
and `tests/test_sessions_api.py` become 403 (step 1); `tests/test_logbook.py`,
`test_replay_api.py` and `test_connection_state.py` move to the new fields (step 4).

## 8. Migration

Each step is one PR, green on `pytest -q`, `npm run check` and `npm run e2e`, and none
breaks the UI or a pack on its own.

1. **Errors, statuses and routing (server, OpenAPI, tests).** §1–§3 and their tests;
   `ErrorReply.code`; CHANGELOG *Changed*/*Fixed*. The UI needs no change because
   `parse()` reads bodies whatever the status. This is a behaviour change for outside
   clients that key on status, which `0.y` allows; it is listed in the CHANGELOG.
2. **Additive fields (server, OpenAPI, fixtures).** Add `ts_utc`, both `since_utc`,
   `t0_utc`, `trace`, the `start_utc` param, UTC capture rows and `fmt=geojson`; mark the
   old fields deprecated (§6); regenerate the fixtures; CHANGELOG *Added*/*Deprecated*.
   Release **0.1.0**.
3. **UI moves (UI, D2 pack).** `schemas.ts` makes the new fields required (the UI ships
   with its server). `RecordingCard` and `Logs` use `since_utc`/`ts_utc`; replay uses
   `t0_utc` for the offset and synthesizes `ts_utc`; `trace.ts` and `AnalysisView` read
   `trace`; `lib/audio.ts` sends `start_utc`; the export menu offers GeoJSON. A small
   `lib/time.ts` parses RFC 3339 for arithmetic. The static build is regenerated. The D2
   pack moves its test to `trace` in the same window. Done before U1 starts.
4. **Removal, release 0.2.0 or later (server, OpenAPI, UI, fixtures).** Drop `ts`, both
   `since`, `utc`, `track` and `start`, plus `EpochSeconds` and the deviations list; Zod
   drops them; fixtures are regenerated; the contract test asserts they are absent.
   CHANGELOG *Removed*. It can land during U1, which reads only the new fields.

## 9. The Discovery 2 pack

Checked in the pack repo (2026-10-06):

- The pack calls no HTTP route. `server/endpoint.py` is its own community endpoint that
  receives the platform's outbound contributions; nothing here changes that protocol.
- `synth.py` passes `active_test.since` (epoch) to the recorder as a Python dict, not on
  the wire. `recorder._norm_active_test` drops `since`, so the committed demo logs stay
  byte-stable. Their CSV `Utc` epoch columns are exempt, and `meta.start_utc` is already
  RFC 3339.
- **One touch:** `tests/test_demo_sessions.py` asserts on `store.data(...)["track"]`. It
  moves to `trace` in step 3, before the platform removes `track` in step 4. No
  `PACK_API_VERSION` change; the `VehiclePack` contract is untouched.

## Out of scope

Auth changes (done in #7); URL versioning (`/v1/…`, U6); MQTT and HA discovery (U5);
`405`/`HEAD`/`OPTIONS`; serving the app shell for unknown HTML navigations (Q5); on-disk
session formats (CSV columns keep epoch `Utc`, which the wire conventions allow).

## Open questions

1. **Car-side `/command` failures:** an ECU negative response as 502 and a poll-thread
   timeout as 504 (outside the listed table), or both stay 400?
2. **Queued community contributions** (`{ok: false, queued: true}`): 202 with `ok: true`?
   It changes the UI's toast.
3. **Automap with no fit:** 400, or 422 for "valid input, no answer"?
4. **Accel samples** (`[epoch_ms, ax, ay, az]`, up to 5,000 per POST): a documented
   exemption, or `t0_utc` plus ms offsets?
5. **Unknown path with `Accept: text/html`:** the JSON 404, or the app shell?
6. Are `Deprecation`/`Link` headers worth it, or do OpenAPI `deprecated` and the
   CHANGELOG suffice for a local API with one first-party client?
7. **Shutdown not enabled:** 409 (state) or 403 (policy, kept for public mode)?

## Changelog

- 2026-10-06 — v0.1: first draft.
