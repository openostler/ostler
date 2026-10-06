# decisions/

Immutable Architecture Decision Records: one locked decision per file.

## Files

- `adr-0001-adopt-vibes-as-code.md` — the documentation method.
- `adr-0002-layered-stdlib-core.md` — Python core and a stdlib server stay. Superseded in part by ADR-0032/0035 (production link and decode move to C on the node).
- `adr-0003-signal-store-source-of-truth.md` — signals JSON plus confidence tags.
- `adr-0004-react-typescript-ui.md` — React + TS dashboard shipped as static assets. Amended by ADR-0035 (generated types, Capacitor).
- `adr-0006-english-confidence-vocabulary.md` — `proven`/`candidate` replace the Swedish `belagt`/`kandidat`.
- `adr-0008-unified-status-vocabulary.md` — one derived item status (verified/candidate/sniff/untranscribed) + safety class, server-enforced.
- `adr-0009-session-logbook-and-location.md` — always-on RaceCapture-style session CSV; VBO/GPX exports; location stays on the device.
- `adr-0010-replay-notes-audio-motion.md` — read-only whole-app replay; per-session notes; opt-in audio/accel kept on the device; Esri imagery with attribution. Amended by ADR-0032 and ADR-0036.
- `adr-0011-no-demo-mode-live-only-recording-place-names.md` — no mock mode (demo logs instead); record only while connected; GeoNames + OSM place names.
- `adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md` — AGPL-3.0-or-later code + commercial licence; CC BY-SA 4.0 vehicle data; CLA.
- `adr-0013-repo-split-and-vehicle-pack-contract.md` — split into `ostler` platform, this repo as the D2 pack, `ostler-firmware`, private `ostler-cloud`; VehiclePack contract. Amended by ADR-0034.
- `adr-0014-ostler-handles.md` — handles: GitHub org/PyPI/import `openostler`, npm `@ostler`, entry point `openostler.vehicle`, `@ostler.tech`; trademark policy. Amended: Ostler Lite and Ostler.
- `adr-0015-repo-split-executed.md` — the split done: this repo is the `openostler` platform; the D2 pack (`d2diag`) is a separate distribution; what moved where. Amended by ADR-0034.
- `adr-0016-covesa-vss-canonical-signal-namespace.md` — VSS 6.1 paths are canonical; `vss/ostler.vspec` overlay (`Vehicle.Ostler.*`) is the single source; generated `metrics.json`; OVMS/HA/OBDb aliases; verbatim VSS units, QUDT not UCUM.
- `adr-0017-open-standards-first.md` — prefer open standards as files, not frameworks; the adopted set with verdicts; the rule for adding a dependency or standard; reference-only list.
- `adr-0018-ui-architecture-decisions.md` — UI spec Q2–Q11 answered (areas, driver-side rail, comfort class, lockouts, tiers, VIN, service mode, cameras incl. 360 later); capabilities as data, no vehicle-type checks. Amended by ADR-0033 (render class renamed "add-on device").
- `adr-0019-reuse-from-ovms-and-obdb.md` — import all OVMS vehicles and commands the licence allows (exclusions are licence/legal only); commands disabled behind the gates, Tier 4 until its own ADR; OBDb primary for polled data; importer with a review gate. Exclusion (c) amended by ADR-0025.
- `adr-0020-can-links-listen-only-by-default.md` — frame-level `CanLink` beside `Transport`, SocketCAN first; listen-only by default; TX only via pack allowlist + Parked + server gate; no MQTT→vehicle CAN. Amended by ADR-0023 (Tier 0 only after the bitrate is confirmed). Superseded in part by ADR-0032 (the node gate is the only transmit path) and ADR-0033.
- `adr-0021-local-https-on-the-device.md` — the Pi serves local HTTPS so phones get service workers; trust setup (per-device CA, ACME DNS) to design; stdlib `ssl`. Amended: Lite trust via phone pairing.
- `adr-0022-kline-protocol-profiles-and-auto-detection.md` — K-line profiles as data (init method its own field), packs override; detect fast init then 5-baud `0x33`; manufacturer protocols never auto-probed; probing Parked-only; keep-alive and `82`; 5-baud address 8N1. Amended: KKL dev-only; production K-line on the node.
- `adr-0023-passive-can-bitrate-detection.md` — amends ADR-0020: listen at 500k then 250k, accept after 20 clean frames, then one `01 00`; silent-bus probe Parked-only and one-shot; 11- and 29-bit IDs.
- `adr-0024-body-bus-links-passive-by-default.md` — I/K-Bus as byte `Transport` + framer, passive by default; allowlist + Parked + gate; no spoofing; IKE read exception; standing automations pre-authorised; data in packs. Superseded in part by ADR-0033 (notify-only dropped).
- `adr-0025-reuse-and-licences-pragmatic.md` — amends ADR-0019 (c): reimplement anything in our own words; never copy descriptive text; GPL-3 taken whole only into marked GPL-3 modules or packs; GPL-2.0-only, non-commercial and dealer material stay out.
- `adr-0026-module-bus-10base-t1s.md` — our own module bus: IP for the computer tier, 10BASE-T1S (PLCA, LAN8651 reference) for our modules; CAN/Wi-Fi on dev kits; CAN kept for µA-wake nodes; one VSS/MQTT-style message model; car buses out of scope. Amended: PLCA coordinator and broker on the node.
- `adr-0027-ip-everywhere-ecosystem-architecture.md` — builds on ADR-0026: IP everywhere on an automotive-Ethernet backbone (T1S modules, Ethernet/PoE cameras, 100BASE-T1 only for our own cameras, Wi-Fi/USB displays); the Pi routes; MQTT 5 with VSS topics; mDNS/DNS-SD; NTP; mTLS (envelope dropped, v1.1); the module contract and DevicePack adapters; car buses at the edge; CAN/wake fallback; Matter via a bridge only. Superseded in part by ADR-0032 and ADR-0033.
- `adr-0028-base-hardware-connectivity-and-remote-access.md` — the base is the Pi plus an always-on ESP32 "buddy" (wake, buses, small parked MQTT broker bridged to the Pi); the guardian is an add-on; uplinks (car/head-unit Wi-Fi, hotspot, any USB dongle, OpenWrt gateway, Starlink) with Auto failover and metering; remote access LAN → Tailscale → Ostler Cloud → HA Cloud; Improv provisioning; IANA `_ostler-mod._tcp`. Superseded in part by ADR-0032 (§1 base, power states, buddy → node).
- `adr-0029-accounts-multi-vehicle-sharing-and-social.md` — ACCEPTED (amended by ADR-0033: categories as a second axis): local users (passkeys + passwords), roles as tier ceilings, scoped revocable tokens, garage defaulting to the connected car, invites and revocable shares (no VIN, location opt-in), later groups/rides and outbound sharing.
- `adr-0030-ai-native-mcp-server-and-authoring-skill.md` — ACCEPTED (phone approval per ADR-0033; SDK extra `[mcp]`): an MCP server as a separate process over the local API, under the same tier gates (no AI bypass, read-only while moving); a `skill/pack-author/` skill for scaffolding and decoding packs.
- `adr-0031-generic-obd2-pack-in-platform.md` — amends ADR-0013/0015 for one pack: `generic_obd2` ships in-platform under `packs/` as the default fallback; other packs stay in `ostler-pack-<x>` repos. Amended: packs are portable JSON for the C decoder.
- `adr-0032-one-node-optional-brain.md` — Ostler Lite (an ESP32 node alone, optional 4G, works offline with a phone) and Ostler (node + Pi brain). The node owns the car and power (K-line/CAN, VSS decode, the only transmit gate, GPS, parked broker, brain power); the brain never touches the car. The guardian is a hidden node variant with no outputs. One firmware; one C decoder fed by pack JSON, with shared vectors and Python as the lab/reference.
- `adr-0033-action-categories-and-approvals.md` — action categories as a second axis to tiers; default roles; kiosk Read + Comfort; safe fault clearing (snapshot, parked or idling, audited); phone approval of Tier 2–3 over local links, install override `OSTLER_ALLOW_REMOTE_CONTROL`; alarm paths independent of brain and internet; notify-only dropped (outputs via a future I/O module).
- `adr-0034-repo-boundaries.md` — one platform repo (no UI split); `ostler-firmware` first-class now; packs in `ostler-pack-<x>`; `ostler-cloud` private; `ostler-hardware` at PCB time; module contract repo at v1; split only on toolchain, licence, cadence or contributors.
- `adr-0035-languages-by-tier.md` — C/C++ (ESP-IDF) for the node and decoder; Python for lab, tools, brain and MCP (stdlib + pyserial, optional extras, ctypes native decoder with Python fallback); TypeScript UI with generated types; Rust only for a measured hot path.
- `adr-0036-vin-and-identity-data-in-recordings.md` — identity replies scrubbed at write by default; opt-in install option for security decoding; never leaves the device.

- `adr-0037-role-holders-and-handover.md` — PROPOSED: single-holder roles (transmit gate per bus, never handed over; parked broker; time source; PLCA coordinator; uplink manager) with static priority set at pairing, retained claims + LWT + mDNS hints, timeouts and split-brain rules; authority always stays with the executing gate.
- `adr-0038-mesh-car-to-car-and-off-grid.md` — PROPOSED: mesh only between cars, to a base or off-grid, as its own subnet; a mesh is a remote path (Read and alerts only); Meshtastic-compatible LoRa add-on first behind a separate GPL-3 VSS bridge; MeshCore and Reticulum to bench-test; Babel if a Wi-Fi IP mesh is wanted.

ADR-0005 (NanoCom sniff workflow) and ADR-0007 (BCU SecurityAccess) are Discovery 2
decisions and stay in the D2 pack repo; their numbers are not reused.

## Editing rules

- Never edit an accepted ADR's decision. Supersede it with a new ADR and set the old
  one's frontmatter `status: superseded`.
- Name new ADRs `adr-NNNN-kebab-title.md`, with the next number (never reused).
- New ADRs (from ADR-0016) follow MADR: add **Decision drivers** and **Confirmation** sections
  (ADR-0017).
- Rebuild INDEX.md after adding an ADR.
