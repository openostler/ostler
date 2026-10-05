# ui/

The dashboard: Vite + React + TypeScript. `npm run build` writes to
`src/d2diag/web/static/`, which is committed so the Pi needs no Node (ADR-0004).

## Files

- `src/api/` — `schemas.ts` (Zod contract), `client.ts`, `useSnapshot`/`useSniff`/`useCatalog`,
  `useAction` (every module action; adds `trust: "experimental"` in Experimental mode), `fixtures/`.
- `src/screens/` — one component per tab; `registry.ts` lists them (`admin` ones only on /admin).
- `src/components/` — shared pieces (Value, Gauge, Readout, Sheet, Preferences, ConnectionSheet,
  StatusTag, CoverageBar, PlaceholderReadout, ActionButton, ProcedureSheet, …).
- `src/screens/Analysis.tsx` + `components/replay/AnalysisView.tsx` — the map/chart/G-G/notes view,
  live (the drive in progress, marker on `snap.gps`) or replay; `components/RewindButton.tsx`
  in the header jumps 30 s back into the drive in progress (or opens the latest log).
- `src/screens/Logs.tsx` + `src/components/replay/` — session browser and replay (MapLibre map,
  Canvas chart, transport bar) over `/sessions` (ADR-0009). `replay/maplibre.ts` is the only
  module that imports `maplibre-gl`; it is reached through `import()` so the main chunk stays
  small (`maplibreChunk.test.ts` enforces it). `src/state/playback.ts` is the shared cursor.
- `src/state/replay.tsx` + `replayState.ts` — whole-app replay (ADR-0010): while a session is open,
  `useApp()` returns a snapshot synthesised at the cursor, every action is refused, and
  the header pill becomes a flashing "Replay · Exit to live" button and `GlobalTransport`
  (with the note chip floating over the page above it) shows on every tab. `lib/audio.ts`, `lib/motion.ts` and
  `RecordingCard`/`RecordingOptions`/`MarkButton` are the recording side.
- `src/lib/catalog.ts` — the Stable/Experimental visibility rules over `/catalog` (ADR-0008).
- `src/layout.ts` — the only place that names signals (Drive tiles, body view, LID presets).
  Outputs, Settings and Utilities come from `/catalog`, never from a hard-coded list.
- `src/styles.css` — the calm-instrument tokens (auto day/night) and all styles.
- `e2e/` — Playwright smoke test against the test-only server `tests/e2e_server.py` (simulated car; ADR-0011).

## Editing rules

- Dev: `PYTHONPATH=src python3 tests/e2e_server.py` (test-only simulated car) in the repo root, then `npm run dev`. The product itself always runs live.
- Never hard-code signal labels, groups or units — they come from `/fields` (the signal store).
- A server response change → `UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`, then
  update `schemas.ts`.
- Before committing: `npm run check` (lint, typecheck, test, build) and commit `web/static`.
- Anything that writes to an ECU goes through `components/confirm.ts` (catalog actions via
  `ActionButton`, which applies the registry's `confirm` level).
- One status vocabulary (ADR-0008): `StatusTag` + `CoverageBar`, shown in Experimental only.
  Stable shows verified items only. Never show a stale value as live (`Readout`).

## Design rules (calm instrument — ISA-101 + automotive HMI)

- Neutral when healthy. Colour (warn/alarm) only for abnormal values, always with an icon
  and a word (`StatusChip` for value ranges); OK values show no badge at all.
- Every number in context: `RangeBar` (span + `normal` band from the signal store) and a
  60 s `Sparkline`. Bands live in `signals/*.json` (`span`, `normal`), never in components.
- `HealthStrip` leads Drive and Inputs with the one-line answer and links to the cause.
- Status hues are validated with the dataviz `validate_palette.js` in both modes — re-run it
  if you change `--ok/--warn/--alarm/--accent`.
- Screens scroll: never let flex shrink a block (`main > *` is `flex-shrink: 0`).
