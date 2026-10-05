---
title: "ADR-0011 — No demo mode; record only while connected; offline place names with OSM enrichment"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md]
summary: >
  The product has no mock/demo mode — replaying committed demo logs is the demo, and simulated sources exist only in tests; sessions record only while the car is connected (paused otherwise); places are named offline from GeoNames and refined online via OSM Nominatim within its usage policy.
---

# ADR-0011 — No demo mode; record only while connected; place names

- **Date:** 2026-10-06
- **Status:** accepted (amends ADR-0009's start rule)

## Context

- Mock mode let the UI and the homelab look connected to a car that didn't exist. Combined with GPS-only starts (ADR-0009), the app showed "recording" with no vehicle attached.
- Whole-app replay (ADR-0010) now gives a truthful demo: a recorded drive.
- Owners want sessions named by place rather than by coordinates.

## Decision

**No demo mode.**
- No `--mock` flag, no server modes, no Mock/Live switch.
- The simulated ECU exists only in `tests/`, as test scaffolding.
- Two committed synthetic sessions, "Demo log 1" and "Demo log 2", are the demo. They are read-only and are the only sessions the public server lists.

**Record only while connected.**
- A session starts when the car is connected.
- While the car is disconnected the session is **paused**: no rows are written, and the session ends after 5 minutes.
- GPS movement alone never records anything. This supersedes the GPS-start rule in ADR-0009.

**Place names.**
- Offline names come from GeoNames `cities1000` (CC BY 4.0), using the nearest town within a reach that scales with population, otherwise the region.
- When the Pi is online, OSM Nominatim refines the name. The Nominatim policy is followed:
  - at most 1 request per second;
  - a custom User-Agent;
  - every result is cached permanently;
  - the endpoint is configurable or can be turned off.
- Both sources are credited in the UI.
- Coordinates still stay on the device (ADR-0009). The lookup sends one rounded point per session start and end to the configured geocoder, and only when it is enabled.

## Consequences

- Tests and Playwright use the test-only fakes, and developers without a car run `tests/e2e_server.py`.
- The homelab shows "No connection" plus the demo logs.
- Session meta gains `place*`, `name` and `description`, and a SQLite index serves paged, searchable lists.

## Alternatives considered

- **Keep mock mode behind a flag.** Rejected by the owner: replay is the demo.
- **Nominatim only.** Rejected: the Pi is often offline in the car.
- **GPS-start recording.** Rejected: it records without the car.
