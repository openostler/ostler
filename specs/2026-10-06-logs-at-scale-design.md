---
title: "Logs at scale — place names, paging/search/scrubber, editable records, live-only recording, no demo mode — design"
area: specs
status: stable
version: 1.2
updated: 2026-10-07
depends_on: [specs/2026-10-05-session-logbook-design.md, specs/2026-10-05-replay-notes-capture-design.md, decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md]
summary: >
  Sessions get human place names (offline GeoNames nearest town within a size-scaled radius, else region; enriched by OSM Nominatim when online, cached, attributed); a SQLite session index serves keyset-paged, searchable, filterable lists and a month histogram for a Google-Photos-style scrubber; name/description are editable in place; recording happens only while connected (paused otherwise); demo/mock mode is removed from the product (two committed Demo logs replace it); delete confirms by typing "Delete". Amended 2026-10-07 (openness round, ADR-0047): a badged developer demo mode is allowed and GPS-only trips are an owner opt-in.
---

# Logs at scale — design

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("apply the
> loosenings"; [ADR-0047](../decisions/adr-0047-openness-round.md)):** a developer demo mode,
> off by default and badged "Demo" on every screen, is allowed (§4; ADR-0011 amendment), and
> GPS-only trips are an owner opt-in.

## Context

The owner approved this on 2026-10-06. Research sources:
- the Nominatim usage policy and reverse API;
- the GeoNames dumps (CC BY 4.0);
- browsing patterns in Google Photos (scrubber), Strava (search, filters, calendar) and AiM RS3 (events and filters).

## 1. Record only while connected

- **Start:** a session opens only when the snapshot shows `conn == "connected"`, or `status == "connected"` when `conn` is absent. GPS movement never opens one.
- **Paused:** while the session is open and the car is not connected:
  - no data rows are written, not even GPS;
  - state events are still logged;
  - the session ends after `IDLE_S = 300` s, or at shutdown.
- **Snapshot `recording`:** `{session, since, rows, state: "recording" | "paused"}`.
- **`POST /notes/live` and the ⚑ button:** refused with 409 and "Not recording — connect to the car first" unless the state is `recording`.
- **`split_session`:** refused unless the state is `recording`.
- **Explicit start:** `start()` still exists for tests and tools, but no server route starts a session without a connection.

## 2. Place names (`src/openostler/geo/`)

### Offline lookup

**Data:** `geo/places.tsv.gz`, trimmed from GeoNames `cities1000`.
- Columns: `name, lat, lon, cc, admin1_name, admin2_name, population`.
- Built by `tools/build_places.py`, which downloads the dumps into a cache directory.
- A header comment carries the attribution.

**`geo.offline.label(lat, lon)`** returns:

```
{"label", "town", "region", "country", "dist_km", "source": "geonames"} | None
```
- The index is a grid of 0.25° buckets, searched in rings until a candidate is found or 100 km is reached.
- Candidates are scored by population within their radius. Reach depends on size:

  | Population | Reach |
  |---|---|
  | ≥50k | 25 km |
  | ≥5k | 15 km |
  | ≥1k | 8 km |
  | below 1k | 3 km |

- The largest qualifying place wins, with ties going to the nearest.
- Label forms:
  - within 1 km of the town: `"Town, Region"`;
  - beyond 1 km but within reach: `"near Town, Region"`;
  - no town within reach: `"Region, Country"`, using the nearest point's admin2, falling back to admin1;
  - nothing within 100 km: `"Country"`, or `None` at sea.

### Online enrichment

**`geo.nominatim.Enricher(url, cache_path, user_agent)`** is a daemon thread with one queue.
- At most one request per second.
- The request is `GET {url}/reverse?format=jsonv2&lat=&lon=&zoom=10&addressdetails=1`.
- The label is built from the first present of `city/town/village/hamlet`, followed by `county` (or `state`). With no settlement it is `county/state, country`.
- Results are cached in `logs/geocache.json`, keyed by lat/lon rounded to 3 decimals.
- Failures back off exponentially, from 60 s up to 1 h. When it is offline, items wait in the queue.
- `submit(key, lat, lon, callback)`.
- The URL comes from `--geocoder URL|off`.
  - The default is `https://nominatim.openstreetmap.org`.
  - Tests use `off`.
  - The User-Agent is `discovery2-diag/<version> (+https://github.com/JamesWrightDavid/discovery2-diag)`.

### Where the names are stored

- Session meta gains:
  - `place_start: {label, source} | null`, at the start position;
  - `place_end`, the same at the end position;
  - `place`, which is `place_start`, or `place_end` when there is no start.
- The offline label is written when the session closes, and when the index first meets a session that has none.
- Enrichment replaces `label` and sets `source: "osm"`. The offline label stays as `label_offline`.

**Attribution:** the Logs footer shows "Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)".

## 3. Session index and API

**`logbook/index.py` `SessionIndex(db_path, store)`:**
- A stdlib `sqlite3` database in WAL mode with `synchronous=NORMAL`.
- Table `sessions`: `id PK, start_ms, end_ms, duration_s, distance_km, max_speed_kmh, modules, place, place_end, name, description, note_count, has_gps, synthetic, recording, meta_json`.
- An FTS5 table over `name, description, place, place_end, notes` when it is available; otherwise `LIKE`.
- `sync(id)`, `remove(id)`, `rebuild()`. It rebuilds automatically if the database is missing or its schema version differs.

**`GET /sessions?limit=&before=&q=&from=&to=&module=&has_notes=&min_km=`** returns `{"sessions": [meta…], "next": cursor|null}`.
- Sorted newest first by `start_ms`, then `id`.
- The cursor is an opaque `"<start_ms>:<id>"`.
- `limit` defaults to 50 and is capped at 200.
- `from` and `to` are ISO dates.
- In public mode only synthetic sessions are returned.

**`GET /sessions/histogram?group=month`** returns `{"group": "month", "buckets": [{"key": "2026-10", "count", "km"}]}`.
- `group=day&year=YYYY` returns buckets keyed `"2026-10-05"`.

**`PATCH /sessions/<id>`** takes `{name?, description?}` and returns `{ok, meta}`.
- `name` is capped at 80 characters and `description` at 2000. Whitespace is trimmed, and an empty value becomes null.
- It is refused with 403 in public mode and for synthetic sessions.

## 4. No demo mode

*Amended 2026-10-07 (openness round):* the product ships with no demo mode on by default and
no Mock/Live switch for users; a developer demo mode, badged "Demo", may be added behind a
developer flag or service mode (ADR-0011 amendment).

**Removed from the product:**
- the `--mock` flag;
- server modes (`modes`, `set_mode`, snapshot `mode`/`modes`);
- the UI's Mock/Live switch and mode row.

**What runs instead:**
- The server always uses live sources.
- The simulated sources live in `tests/fake_sources.py`, used only by tests. Playwright starts `tests/e2e_server.py`.
- The homelab runs live with the geocoder on and no sniff feed (2026-10-07: the product
  has no `--replay`; the Decode tab reads only a live sniffer, `--sniff`).

**Demo logs:**
- The pack's demo sessions dir (for the D2 pack `src/d2diag/demo/sessions/`, ADR-0015) holds two synthetic sessions:
  - **"Demo log 1"**: the Rannoch Moor drive.
  - **"Demo log 2"**: a second synthetic route on open moorland away from any address. It is SLABS-focused, with height changes, faults and two notes.
- Each has a `description` and an offline `place`, and is read-only.

## 5. UI

**Logs browser:**
- Sticky year and month headers.
- Rows show the name, or the place label when there is no name. Under that, a muted line with the date and time, duration, distance, modules (display names) and the note count.
- Infinite scroll follows `next`.
- A right-edge month scrubber is built from the month histogram; dragging it jumps with `before=<end of that month>`.
- A search box, debounced by 300 ms.
- Filter chips: date range, module, has notes, minimum distance.
- A "this year" day heatmap strip; tapping a day filters to it.
- The recording card shows "Paused — no connection" when paused, and hides ⚑ then.

**Replay header:** an inline name ("Untitled session" placeholder) and description. Enter or blur saves through PATCH. Read-only on demo logs.

**Delete:** you type `Delete` to confirm (case-sensitive). The button is hidden for demo logs and in public mode.

**Connection sheet:**
- It no longer has the "Data source" block or the mode row.
- In live mode it opens immediately (0 ms) on load, and when leaving replay, if the connection is not live.
- `reconnecting` gets a 1 s debounce.
- It never opens during replay.

**Module names:** EAT is "EAT (auto gearbox)" and the airbag is "SRS (airbag)".

## Testing

- **pytest:**
  - GPS-only feeding records nothing;
  - the paused state and idle end;
  - the live note is refused while not recording;
  - geo: radius rules, region fallback, sea → None, the enricher's rate, cache and backoff (fake HTTP);
  - index: paging stability, search, filters and histogram over 2,000 synthetic metas, rebuild;
  - PATCH meta;
  - no `--mock` and no `set_mode`;
  - demo logs 1 and 2 are deterministic.
- **vitest:**
  - browser grouping, the scrubber jump, search and filters, the inline editor, the Delete confirm;
  - immediate sheet open in live mode and none in replay;
  - module names.
- **Playwright:** the demo logs are listed by name, search, inline edit on a non-demo session (the test server creates one), the scrubber, and the sheet in live mode.

## Changelog

- 2026-10-06: v1.0, approved.
- 2026-10-07: v1.2, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", ADR-0047): a badged developer demo mode and opt-in GPS-only trips.
