---
title: "Session logbook — always-on recording, GPS, and a Logs tab with map replay — design"
area: specs
status: stable
version: 1.0
updated: 2026-10-05
depends_on: [specs/2026-10-05-ui-overhaul-design.md, decisions/adr-0009-session-logbook-and-location.md, specs/2026-10-02-gps-tracker-alarm-design.md]
summary: >
  Every connected period is recorded on the device as a session (RaceCapture-style CSV + meta.json), GPS comes from a USB NMEA receiver (mock/replay sources for development), and a new Logs tab browses sessions and replays them on a MapLibre map with a channel-coloured trace, synced chart cursor and a bottom transport bar. Exports VBO/GPX/CSV. Also: header label + % mapped pill, connection notice on every module page, 60 s re-prompt.
---

# Session logbook — design

## Context

The owner approved this design on 2026-10-05. The project is heading toward a race-logger / telematics tool. The design follows the research in the plan:

- **Race Studio 3, MoTeC i2, RaceChrono, DovesDataviewer:** a synced cursor, a channel-coloured trace with a legend, play/pause, and a scrubber.
- **RaceCapture:** its log reference shapes the native file format.
- **Racelogic:** its `.vbo` documentation defines the main export.
- **OSM tile policy and EDPB guidance on location:** these shape the map and privacy rules.

Not built now (roadmap):
- phone geolocation, which needs HTTPS on the Pi plus a wake lock;
- accelerometer data (DeviceMotion, or an IMU on the Pi);
- offline maps (PMTiles);
- laps and sectors, and delta-T;
- the ESP32 writing the same CSV schema;
- retiring mock mode in favour of the demo session.

## Part A: header and connection

- **Header:**
  - No "D2 Diag" title. On `/admin`, a small "admin" chip replaces it.
  - The module selector is one bordered control on the header row: a muted "Module" label, the module name, then a ▾ chevron. It is a native `<select>`, styled.
  - In Experimental mode only, a pill next to it reads `NN% mapped`, in the accent colour (not a status hue). The percentage is verified items over total.
- **`ConnectionNotice`:** a non-blocking strip ("No connection — Open connection") shown on every module page when `conn` is not live: Faults, Inputs, Outputs, Settings and Utilities. Drive keeps its full gate.
- **Re-prompt:** after a dismissal, if the connection is still not live 60 s later (`REPROMPT_MS`), the connection sheet re-opens. It shows how long the link has been down ("No connection for 1 m 20 s"). Each dismissal restarts the timer. The sheet never opens over Consent.

## Part B: the logbook

### Native session format

The format follows RaceCapture's log file reference (CSV with a header row of channel cells).

Each session is a directory `logs/sessions/<id>/`, where `<id>` is `YYYYMMDDTHHMMSSZ` (UTC at start) plus `-N` if it collides.

**`data.csv`** (UTF-8, `\n` line endings):
- **Row 1, the header.** Each cell is `"Name"|"Units"|rateHz`.
  - The first two cells are `"Interval"|"ms"|10` (milliseconds since the session started) and `"Utc"|"ms"|10` (epoch ms, or empty until a GPS fix or a trusted clock).
  - Then the channels in a fixed order:
    - GPS channels: `GPS_Latitude`, `GPS_Longitude`, `GPS_Speed`, `GPS_Heading`, `GPS_Altitude`, `GPS_Nsat`, `GPS_HDOP`;
    - every store signal seen in the session, by its store name (for example `rpm`, `coolant_temp`);
    - the text channels `module` and `faults`.
- **Data rows:** written at the poll cadence (the GPS rate is capped at 10 Hz).
  - A channel that was not sampled in that row is left empty (sparse rows).
  - Numbers are plain decimals.
- **Durability:**
  - The file is flushed and fsynced at most once per second.
  - Readers ignore a last line that is truncated or malformed.
  - A new channel appearing mid-session closes the file (`data.csv` → `data-0.csv`) and opens a new part with a new header. Parts are also split hourly. `meta.json` lists the parts.

**`meta.json`:**

```json
{"id": "...", "start_utc": "ISO", "end_utc": "ISO|null", "duration_s": 0, "rows": 0,
 "parts": ["data.csv"], "modules": ["motor"], "channels": [{"name","units","group"}],
 "has_gps": false, "distance_km": 0.0, "max_speed_kmh": null,
 "bbox": [minLon, minLat, maxLon, maxLat] | null, "start_pos": [lon, lat] | null,
 "end_pos": [lon, lat] | null, "synthetic": false, "recording": false, "source": "mock|live|demo"}
```

- `meta.json` is rewritten atomically (write to a temp file, then rename) when the session starts, every 30 s, and when it ends.
- Coordinates are `[lon, lat]` (GeoJSON order). In `start_pos` and `end_pos` they are rounded to 3 decimals, about 100 m, so the list never shows an exact location.

### Recording rules (`SessionRecorder`)

- **Start:**
  - when `conn` first becomes `connected`, or
  - when GPS speed goes above 3 km/h with no session open.
- **End:**
  - after 300 s (`IDLE_S`) with no `connected` poll **and** GPS speed below 3 km/h (or no GPS), or
  - when the server shuts down.
- **Always on.** There is no setting in v1. Manual "Log CSV" keeps working on its own.
- **Never recorded:** the VIN or identity reads. Only `signals`, `faults`, `module` and GPS go into a session.
- **Rotation:** when free space under `logs/` falls below 200 MB, the oldest non-synthetic sessions are deleted.

### GPS

- **`gps.nmea.parse(line) -> dict | None`**
  - Accepts `$xxRMC`, `$xxGGA` and `$xxVTG` with any talker prefix, and validates the checksum.
  - Merges into a `Fix`: `{utc_ms, lat, lon, speed_kmh, heading, alt_m, sats, hdop, fix}`.
  - `fix` is true only for RMC status `A`, or GGA quality ≥ 1.
- **`GpsReader(port, baud=115200)`**
  - A daemon thread that reads lines over pyserial and keeps the latest fix.
  - `port="auto"` probes the u-blox USB VID `1546` and `/dev/ttyACM*`.
- **`MockGps(route)`** follows the synthetic demo route in real time.
- **`ReplayGps(path)`** replays an `.nmea` file, for tests.
- **`--gps auto|none|mock|<path>`** selects the source. The default is `mock` in `--mock` mode and `auto` in live mode; `auto` with no device behaves as `none`.
- **Snapshot `gps`:** `{fix, lat, lon, speed_kmh, heading, sats, hdop, src, age_s}`, or `null` when there is no source.
  - `src` is one of `usb`, `mock` or `replay`.
  - `age_s` is the age of the last fix.
- GPS channels carry no store confidence: they are not ECU data. They are candidate until T-31 runs on the car.

### Demo session

- `tools/make_demo_session.py` deterministically generates the pack's demo sessions (`pack.demo.sessions_dir/<id>/`; for the D2 pack `src/d2diag/demo/sessions/` in its repo).
- The drive is about 12 minutes on a **synthetic** route: a parametric loop away from any real address, in an empty area.
- Speed, rpm, coolant, boost and battery follow a consistent profile at 5 Hz.
- It is marked `synthetic: true, source: "demo"`.
- The demo session is always listed, read-only, and can't be deleted.

### API

| Route | Access | Returns |
|---|---|---|
| `GET /sessions` | public | `{"sessions": [meta…]}`, newest first. **In public mode only synthetic sessions are listed.** |
| `GET /sessions/<id>` | public (same filter) | `meta` |
| `GET /sessions/<id>/data?ch=a,b&max=N` | public (same filter) | `{"id", "t": [ms…], "utc": [ms\|null…], "ch": {"name": [v\|null…]}, "track": [[lon,lat,t_ms]…], "decimated": bool}` |
| `GET /sessions/<id>/export?fmt=csv\|vbo\|gpx` | public (same filter) | file download (`Content-Disposition: attachment`) |
| `POST /command {"action":"delete_session","params":{"id"}}` | refused in public mode | `{ok}` |

**`/data`:**
- `t` is session milliseconds.
- When rows exceed `max` (default 2000), each requested channel is reduced by min/max per bucket, so peaks are kept.
- `track` keeps every GPS point up to 5000, then Ramer–Douglas–Peucker.
- An unknown id returns 404.

**Exports:**
- **`csv`:** AiM-style names (`channels.export_name`): `Time` (s), `GPS_Latitude`, `GPS_Longitude`, `GPS_Speed`, `RPM`, `Speed`, `Water_Temp`, and so on.
- **`vbo`:** per Racelogic's VBO file structure. Sections `[header]`, `[channel units]`, `[comments]`, `[column names]` and `[data]`. Latitude and longitude are in minutes, with longitude sign inverted (West is positive). Time is UTC `hhmmss.ss`.
- **`gpx`:** a 1.1 track with `<time>` per point when `Utc` is known.

**Snapshot additions:**
- `gps` (above).
- `recording`: `{session, since, rows}`, or `null`.

### UI

**Logs tab:** the seventh tab ("Logs"), shown in Stable and in Experimental.

**Session browser:**
- Sessions are grouped by day.
- Each row shows start time, duration, distance, rounded start position (or "no GPS"), modules, max speed, and a `demo` chip on synthetic sessions.
- A "Recording now · N min" card appears while `snap.recording` is set.

**Replay view:**
- **Map:**
  - MapLibre GL, **lazy-loaded** with `import()`, so it is never in the main chunk.
  - Online style: OpenFreeMap (`https://tiles.openfreemap.org/styles/liberty`), with attribution always visible.
  - When the style fails or there is no network: a blank style with only the trace.
  - The trace is split into segment features coloured into 20 buckets of the selected channel. `speed` is the default; GPS speed is used when there is no ECU speed.
  - Channel picker, and a gradient legend showing min and max.
  - A heading arrow marks the cursor position.
  - The map starts fitted to the session's `bbox`.
- **Chart:**
  - A Canvas strip with up to 3 stacked channels (dataviz-skill palette).
  - The shared cursor sits at the playback time.
  - Tap or drag on the chart to seek; pinch or drag-select to zoom, with a reset button.
- **Readouts at the cursor:** the value of each chart channel, plus GPS speed. They use replay styling, never the live/stale styling.
- **Transport bar:** at the bottom, above the tabs.
  - A play/pause toggle.
  - ⏪ and ⏩ jump 10 s.
  - Speed 1×/2×/4×/8×.
  - A scrubber showing the start, current and end clock times (UTC converted to local time; session time when there is no UTC).
  - One `PlaybackContext` (requestAnimationFrame over `t`; seeking re-anchors) drives the map, chart and readouts.
- **Actions:** Export menu (CSV, VBO, GPX), and Delete (typed confirm; hidden for synthetic sessions and in public mode).
- **Live session:** shows the trace growing (re-fetched every 5 s), with "Follow live" pinning the cursor to the end.

**Third-party code:** DovesDataviewer is GPL-3.0. Its ideas inform the design, but **no code is copied** unless the author's permission to use it under MIT is recorded in writing (see ADR-0009).

## Testing

- **pytest:**
  - NMEA parsing: checksums, talker prefixes, empty fields, RMC/GGA merge.
  - Recorder: start/idle-end, sparse rows, a new channel splits parts, truncated last line, fsync cadence (injected clock).
  - Store: list, data decimation keeps min/max, track RDP.
  - Exports: VBO sections and coordinate conventions, GPX validity, CSV export names.
  - API: public filter, 404, `delete_session` refused in public mode.
  - Layering: `gps/` and `logbook/` never import `web`.
  - The demo session is deterministic and synthetic.
  - The snapshot carries no VIN.
- **vitest:**
  - playback maths (time → index, seek, speed);
  - bucket colouring and legend;
  - transport controls;
  - re-prompt timing;
  - the notice on Settings and Utilities;
  - the header label and pill.
- **Playwright:**
  - open the demo session, scrub, play and pause;
  - change the trace channel;
  - header label;
  - the main chunk excludes maplibre.

## Changelog

- 2026-10-05: v1.0, approved.
