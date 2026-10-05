# decisions/

Immutable Architecture Decision Records: one locked decision per file.

## Files

- `adr-0001-adopt-vibes-as-code.md` — the documentation method.
- `adr-0002-layered-stdlib-core.md` — Python core and a stdlib server stay.
- `adr-0003-signal-store-source-of-truth.md` — signals JSON plus confidence tags.
- `adr-0004-react-typescript-ui.md` — React + TS dashboard shipped as static assets.
- `adr-0006-english-confidence-vocabulary.md` — `proven`/`candidate` replace the Swedish `belagt`/`kandidat`.
- `adr-0008-unified-status-vocabulary.md` — one derived item status (verified/candidate/sniff/untranscribed) + safety class, server-enforced.
- `adr-0009-session-logbook-and-location.md` — always-on RaceCapture-style session CSV; VBO/GPX exports; location stays on the device.
- `adr-0010-replay-notes-audio-motion.md` — read-only whole-app replay; per-session notes; opt-in audio/accel kept on the device; Esri imagery with attribution.
- `adr-0011-no-demo-mode-live-only-recording-place-names.md` — no mock mode (demo logs instead); record only while connected; GeoNames + OSM place names.
- `adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md` — AGPL-3.0-or-later code + commercial licence; CC BY-SA 4.0 vehicle data; CLA.
- `adr-0013-repo-split-and-vehicle-pack-contract.md` — split into `ostler` platform, this repo as the D2 pack, `ostler-firmware`, private `ostler-cloud`; VehiclePack contract.
- `adr-0014-ostler-handles.md` — handles: GitHub org/PyPI/import `openostler`, npm `@ostler`, entry point `openostler.vehicle`, `@ostler.tech`; trademark policy.
- `adr-0015-repo-split-executed.md` — the split done: this repo is the `openostler` platform; the D2 pack (`d2diag`) is a separate distribution; what moved where.

ADR-0005 (NanoCom sniff workflow) and ADR-0007 (BCU SecurityAccess) are Discovery 2
decisions and stay in the D2 pack repo; their numbers are not reused.

## Editing rules

- Never edit an accepted ADR's decision. Supersede it with a new ADR and set the old
  one's frontmatter `status: superseded`.
- Name new ADRs `adr-NNNN-kebab-title.md`, with the next number (never reused).
- Rebuild INDEX.md after adding an ADR.
