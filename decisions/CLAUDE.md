# decisions/

Immutable Architecture Decision Records: one locked decision per file.

## Files

- `adr-0001-adopt-vibes-as-code.md` — the documentation method.
- `adr-0002-layered-stdlib-core.md` — Python core and a stdlib server stay.
- `adr-0003-signal-store-source-of-truth.md` — signals JSON plus confidence tags.
- `adr-0004-react-typescript-ui.md` — React + TS dashboard shipped as static assets.
- `adr-0005-nanocom-sniff-workflow.md` — passive NanoCom capture, candidate-only import.
- `adr-0006-english-confidence-vocabulary.md` — `proven`/`candidate` replace the Swedish `belagt`/`kandidat`.
- `adr-0007-bcu-security-access.md` — derive the BCU seed→key offline freely; gate every live SecurityAccess byte.
- `adr-0008-unified-status-vocabulary.md` — one derived item status (verified/candidate/sniff/untranscribed) + safety class, server-enforced.
- `adr-0009-session-logbook-and-location.md` — always-on RaceCapture-style session CSV; VBO/GPX exports; location stays on the device.
- `adr-0010-replay-notes-audio-motion.md` — read-only whole-app replay; per-session notes; opt-in audio/accel kept on the device; Esri imagery with attribution.
- `adr-0011-no-demo-mode-live-only-recording-place-names.md` — no mock mode (demo logs instead); record only while connected; GeoNames + OSM place names.

## Editing rules

- Never edit an accepted ADR's decision. Supersede it with a new ADR and set the old
  one's frontmatter `status: superseded`.
- Name new ADRs `adr-NNNN-kebab-title.md`, with the next number (never reused).
- Rebuild INDEX.md after adding an ADR.
