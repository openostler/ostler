# specs/

Design docs (`YYYY-MM-DD-<topic>-design.md`) and living specs. A design must be approved
here before implementation starts.

## Files

- `2026-09-30-vibes-adoption-design.md` — adopting Vibes as Code (docs layer).
- `2026-10-01-docs-restructure-design.md` — splitting, de-duplicating and translating the docs.
- `2026-10-01-web-ui-design.md` — the Vite + React + TypeScript dashboard (ADR-0004).
- `2026-10-02-vehicle-integration-roadmap-design.md` — umbrella: the integration feature set, shared hardware, phased plan.
- `2026-10-02-hardware-platform-design.md` — Pi + Pico + tracker ESP32; two power domains; K-line front-end reuse.
- `2026-10-02-canbus-and-fast-signals-design.md` — CAN emulation for head units + fast RPM/speed pulse taps.
- `2026-10-02-gps-tracker-alarm-design.md` — GPS/cellular tracker + alarm taps + authenticated fob-emulation disarm.
- `2026-10-02-remote-start-design.md` — transponder-present bypass + mandatory safety interlocks (highest risk).
- `2026-10-03-vehicle-view-suite-design.md` — per-module vehicle-view pages on one shared silhouette.
- `2026-10-05-ui-overhaul-design.md` — every NanoCom function per module in place, one derived status, header module select + connection sheet (ADR-0008).
- `2026-10-05-session-logbook-design.md` — always-on session recording, GPS, Logs tab with map replay, VBO/GPX/CSV export (ADR-0009).
- `2026-10-05-replay-notes-capture-design.md` — whole-app read-only replay, notes, audio + accel recording, map v2, Decode/Label admin (ADR-0010).
- `2026-10-06-logs-at-scale-design.md` — place names, paged/searchable logs + scrubber, editable records, live-only recording, no demo mode (ADR-0011).
- `2026-10-06-platform-direction-design.md` — DRAFT: the open vehicle platform direction, reframed on the node and optional brain (ADR-0032): packs, node firmware, MQTT/HA, alarm, app, phases.
- `2026-10-06-phase0-vehiclepack-decoupling-design.md` — Phase 0: D2 behind a VehiclePack contract in place (ADR-0013 step 1).
- `2026-10-06-u0-seams-design.md` — APPROVED: U0 seams: VSS 6.1 overlay and `metrics.json`, `metric` on store records, vehicle id (`vid`), JSON Schemas, OpenAPI/AsyncAPI, repo hygiene, D2 metrics.
- `2026-10-06-api-consistency-design.md` — APPROVED: one JSON error envelope, status-code table, query strings everywhere, RFC 3339 `_utc` fields and GeoJSON traces with a one-release deprecation window.
- `2026-10-06-kline-profiles-detection-design.md` — APPROVED (ADR-0022): K-line profiles as data, Parked-only `detect()`, ISO 9141-2 framing, keep-alive and release; no D2 behaviour change.
- `2026-10-06-j1979-service-layer-design.md` — APPROVED: shared OBD-II (J1979) service layer for K-line and CAN; PID data from the pack's store; VIN never logged; Mode 04 as Tier 1.
- `2026-10-06-canlink-isotp-design.md` — APPROVED (ADR-0020/0023): frame-level `CanLink` (SocketCAN, slcan/WiCAN, GVRET), passive bitrate detection, pure-Python ISO-TP, transmit grants.
- `2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md` — APPROVED for `generic_obd2` (ADR-0024/0025/0031): fallback pack (OBDb import) in-platform; the read-only `bmw_e` I/K-Bus pack is DEFERRED until a car or bench exists.
- `2026-10-06-accounts-sharing-design.md` — APPROVED (ADR-0029/0033): local users, passkeys and passwords, roles, tokens, garage shares and invites, later social and integrations; §14 (approved 2026-10-07): one data-class registry, ghost by default, contacts, groups and rides, the shell screens. §15 (approved 2026-10-07, DMD round): the `route` detail, `link` and `public` audiences, live-trip options, link controls, L3–L4 as hand-overs; §15.5a hub-owned identity, later the one Ostler account.
- `2026-10-06-mcp-server-design.md` — APPROVED (ADR-0030/0033): Ostler MCP server (resources, tools, prompts) under the tier gates, and the `skill/pack-author/` skill.
- `2026-10-06-ui-architecture-design.md` — APPROVED (ADR-0016, ADR-0018): head-unit-first UI for any vehicle: layout classes, status strip, five destinations, driving lockouts, garage, capability manifest and render tiers, add-on devices, safety tiers, decode pipeline. §12 (approved 2026-10-07): U2 lockouts and Passenger view, Logs → Trips, Drive layouts and HU-5, More → Add-ons. §13–§15 (approved 2026-10-07, DMD round): the Trips share sheet, help entry points, More → Places and map theme; message alerts (sender and app with Play / Reply, canned replies, opt-in parked-only preview; applied into §12.1); Drive modes and editing.
- `2026-10-06-app-model-design.md` — DRAFT: one shell with features as apps declared by a manifest (driver-safe templates, core apps in-platform, optional apps from own repos); not before U1. §14 approved 2026-10-07 (ADR-0042): small core and add-ons, More → Add-ons, new slots `more:social`, `more:vehicles`, `home:card`. §15 approved 2026-10-07 (DMD round): `contributes.widgets` and `drive_menu`, slots `home:widget`, `drive:widget`, `more:hub`, `more:navigation`, `more:phone`, pinnable `more:*` pages, SDK `widgets`, `input`, `drive_menu`, `calls`.
- `2026-10-06-node-source-design.md` — APPROVED v0.2 (ADR-0032/0037/0040): NodeSource, the Brain ingests node VSS, power, status and raw tap over MQTT 5; snapshot mapping, recording, Network data, requests to the node gate; stdlib MQTT 5 client; P1–P4.
- `2026-10-06-module-bus-messages-design.md` — APPROVED (ADR-0026/0027/0028/0032/0037/0038/0039/0040): the module-bus message spec: `ostler/v1/<vid>/<device>/…` topics and payloads (`vss`, `power`, `status`, `manifest`, `role/#`, `tap/`, `lab/`, `act/`, `wake/`), the transmit-grant format, parked set and bridges, ACLs, TXT keys, mesh bridge, timeouts, versioning. v1.3: the owner's answers to every open question (grant challenge and signing at delivery, `event/` and `faults/` topics, alarm-state enum, primary module, `off` and `feeds`, gate claims never expire and Remove device, check-in caps). v1.4: §19 as built on the Brain (signing extra, faults and events, alarm state, primary selection, feeds, Remove device).
- `2026-10-07-social-addon-design.md` — APPROVED (2026-10-07, ADR-0042): the Social add-on: messaging, push-to-talk, calls, later camera sharing, over the internet and meshes (S1–S4). §12–§13 (approved 2026-10-07, DMD round): message alerts while Moving (new Decision 5), the comms overlap with Phone & Comms (one call session, alert pipeline, favourites, call log), Social the only messenger.
- `2026-10-07-vehicles-and-map-addon-design.md` — APPROVED (2026-10-07, ADR-0042): the Vehicles & Map add-on: friends' shared vehicles on a built-in dark map, ghost by default.
- `2026-10-07-maintenance-garage-addon-design.md` — APPROVED (2026-10-07, ADR-0042): the Maintenance & Garage add-on: services, reminders, fuel, costs and documents fed by the car; pack `maintenance.json`.
- `2026-10-07-visual-design-system-design.md` — APPROVED (2026-10-07): dark, map-first tokens, Figtree, Material Symbols, Ostler Night/Day maps, own SVG charts, one component kit (V1–V3 before U2).
- `2026-10-07-trip-sharing-design.md` — APPROVED (2026-10-07, DMD round; ADR-0043): per-trip sharing at five levels (L0 Card, L1 Route, L2 Telemetry as grants; L3 Full log, L4 Diagnostics as verified hand-overs), redaction rules, the `ostler.share/1` bundle and `ostler share verify` (TS1 first), link controls, help me decode or diagnose.
- `2026-10-07-community-hub-design.md` — APPROVED (2026-10-07, DMD round): Ostler Community, a closed, Ostler-run hub (`ostler-hub`, private) with the open `ostler-app-hub` add-on: publishing, the forum, vehicle development with a GitHub bridge, the wiki; E2E help threads, no DMs, no federation (H0–H4).
- `2026-10-07-navigation-addon-design.md` — APPROVED (2026-10-07, DMD round): `ostler-app-navigation`: Valhalla on the Brain, guidance through the `map` template, voice, GPX library and follow, planner, roadbook (N0–N4).
- `2026-10-07-shell-input-design.md` — APPROVED (2026-10-07, DMD round): `ShellInput`, the shell's D-pad input model (intents, focus zones, Drive menu ≤ 6 rows, Cancel-focused confirms, display-owned bindings, key test); §14 editing by long `ok` and the movable switcher (I1–I3, with U2).
- `2026-10-07-drive-modes-and-editing-design.md` — APPROVED (2026-10-07, DMD round): several Drive modes (seven presets, Dashboard the head-unit default) with faces, `ostler.layout/1`, everything editable with safety items that move but never go, Park to edit, Reset layout (DM1–DM5).
- `2026-10-07-source-adapters-design.md` — APPROVED (2026-10-07, DMD round; ADR-0044): third-party adapters (ELM327, STN/OBDLink, KKL, SocketCAN, WiCAN, later J2534) as data sources through the soft gate, clone checks, one tester per bus; the Brain only for a vehicle with no node (A0–A6).
- `2026-10-07-phone-comms-addon-design.md` — APPROVED (2026-10-07, DMD round): `ostler-app-phone` Phone & Comms: calls through the Brain as a Bluetooth hands-free kit, dialer, contacts, recents, messages, the Android message bridge (PH0–PH4).

Discovery 2 specs (NanoCom capture, HEVAC control, DTC coverage, fault-screen import,
reply-length layouts) stay in the D2 pack repo (ADR-0015).

## Editing rules

- Specs are living: bump `version` and `updated`, and append to `## Changelog`.
- Rebuild INDEX.md after editing.
