# specs/

Design docs (`YYYY-MM-DD-<topic>-design.md`) and living specs. A design must be approved
here before implementation starts.

## Files

- `2026-09-30-vibes-adoption-design.md` — adopting Vibes as Code (docs layer).
- `2026-10-01-docs-restructure-design.md` — splitting, de-duplicating and translating the docs.
- `2026-10-01-web-ui-design.md` — the Vite + React + TypeScript dashboard (ADR-0004).
- `2026-10-01-nanocom-capture-design.md` — NanoCom capture readiness + full system map (ADR-0005/0007).
- `2026-10-02-vehicle-integration-roadmap-design.md` — umbrella: the integration feature set, shared hardware, phased plan.
- `2026-10-02-hardware-platform-design.md` — Pi + Pico + tracker ESP32; two power domains; K-line front-end reuse.
- `2026-10-02-canbus-and-fast-signals-design.md` — CAN emulation for head units + fast RPM/speed pulse taps.
- `2026-10-02-hevac-control-design.md` — climate control via display sniff + button injection.
- `2026-10-02-gps-tracker-alarm-design.md` — GPS/cellular tracker + alarm taps + authenticated fob-emulation disarm.
- `2026-10-02-remote-start-design.md` — transponder-present bypass + mandatory safety interlocks (highest risk).
- `2026-10-03-vehicle-view-suite-design.md` — per-module vehicle-view pages on one shared silhouette.
- `2026-10-04-dtc-coverage-design.md` — filling the fault-meaning store from forum lists, with confidence.
- `2026-10-04-fault-screen-import-design.md` — pairing labelled NanoCom fault screens with raw fault frames (T-30).
- `2026-10-04-reply-length-layouts-design.md` — store records restricted to one reply length (Td5 `21 1B` short/long).
- `2026-10-05-ui-overhaul-design.md` — every NanoCom function per module in place, one derived status, header module select + connection sheet (ADR-0008).
- `2026-10-05-session-logbook-design.md` — always-on session recording, GPS, Logs tab with map replay, VBO/GPX/CSV export (ADR-0009).
- `2026-10-05-replay-notes-capture-design.md` — whole-app read-only replay, notes, audio + accel recording, map v2, Decode/Label admin (ADR-0010).
- `2026-10-06-logs-at-scale-design.md` — place names, paged/searchable logs + scrubber, editable records, live-only recording, no demo mode (ADR-0011).
- `2026-10-06-platform-direction-design.md` — DRAFT: the open vehicle platform direction (packs, guardian hardware, MQTT/HA, alarm, IA, phases).

## Editing rules

- Specs are living: bump `version` and `updated`, and append to `## Changelog`.
- Rebuild INDEX.md after editing.
