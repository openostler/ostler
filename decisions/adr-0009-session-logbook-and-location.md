---
title: "ADR-0009 — Always-on session logbook; location stays on the device"
area: decisions
status: locked
version: 1.0
updated: 2026-10-05
depends_on: [decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0004-react-typescript-ui.md]
summary: >
  Every connected period is recorded on the device as a session in a RaceCapture-style CSV with a meta.json; VBO, GPX and AiM-named CSV are the interop exports; GPS comes from an NMEA receiver parsed by our own stdlib code; location never leaves the device by default and the public server serves only synthetic sessions.
---

# ADR-0009 — Always-on session logbook; location stays on the device

- **Date:** 2026-10-05
- **Status:** accepted

## Context

The project is heading toward race logging and telematics. Owners want every drive recorded and replayable on a map. Motorsport tools have no single open log standard:
- MoTeC `.ld` and AiM `.xrk` are closed.
- VBOX `.vbo` is documented and widely imported (RaceChrono, AiM).
- RaceCapture's CSV is documented and handles mixed sample rates.

Location is personal data: the EDPB treats connected-car location as highly sensitive.

## Decision

- **Native format:** each session is a directory holding a RaceCapture-style CSV and a `meta.json`.
  - The CSV header row has `"Name"|"Units"|rateHz` cells.
  - Rows are sparse, with `Interval` and `Utc` time columns.
  - The file is fsynced once per second.
  - The schema is in `specs/2026-10-05-session-logbook-design.md`. The ESP32 will write the same schema.
- **Exports:** VBO, GPX, and CSV with AiM-style channel names. We do not write closed formats.
- **Always-on:** a session starts on connection, or when GPS shows movement, and ends after 5 minutes idle. There is no setting in v1. Old sessions are rotated out by free space.
- **GPS:** our own checksum-validated NMEA parser over pyserial, so there is no new runtime dependency.
- **Map:** MapLibre GL, lazy-loaded and bundled (BSD-3), with OpenFreeMap vector tiles. No tile prefetching from openstreetmap.org (its usage policy forbids it).
- **Location privacy:**
  - Real sessions stay on the device.
  - The public server lists only synthetic sessions.
  - Community uploads never include GPS channels unless a later ADR adds a per-upload opt-in, with trimmed ends and a preview.
  - Session lists show start and end positions rounded to about 100 m.
  - The VIN and identity reads are never recorded.
- **Third-party code:** DovesDataviewer (GPL-3.0) informs the design. Its code may be copied only once the author's grant to use it under MIT is recorded in writing in the repo (`THIRD_PARTY_NOTICES.md`). Until then we re-implement from the published ideas.

## Consequences

- New core packages `gps/` and `logbook/` (stdlib plus pyserial).
- New routes `/sessions*`.
- New snapshot fields `gps` and `recording`.
- A synthetic demo session ships in the repo, so the Logs tab and the e2e tests always have data.
- GPS data stays candidate until a car test (T-31) checks it against the road.

## Alternatives considered

- **SQLite per sample:** larger, and harder for the ESP32 to share. Rejected for the data itself; a later index may use it.
- **MoTeC `.ld` as the native format:** closed and reverse-engineered. Rejected.
- **Leaflet with raster OSM tiles:** lighter, but offline caching of OSM tiles is forbidden and the trace drawing is slower. Rejected.
