# ui/

The dashboard: Vite + React + TypeScript. `npm run build` writes to
`src/openostler/web/static/`, which is committed so the Pi needs no Node (ADR-0004).

## Files

- `src/api/` — `schemas.ts` (Zod contract), `client.ts`, `useSnapshot`/`useSniff`/`useCatalog`,
  `useAction` (every module action; adds `trust: "experimental"` in Experimental mode), `fixtures/`.
- `src/shell/` — the shell (U1, UI spec §3): `layoutClass.ts` (HU-7, HU-9/10, HU-wide, phone,
  tablet, desktop; kiosk flag `?display=headunit&side=left|right`), `strip.ts` (the status strip
  as chip descriptors; `Strip.tsx` draws them), `destinations.ts` (the registry the rail or
  bottom bar is built from: `slot`, `order`, `requires`, `trust`, a lazy chunk), `routes.ts`
  (route names), `landing.ts` (driving state and landing), `context.tsx` (`useShell()`),
  `Shell.tsx` (layout, Drive mode, sheets, an error boundary per destination), `shell.css`.
- `src/destinations/` — Home, Diagnose (system list or switcher + the five areas), Logs
  (sessions, Analysis, Rewind), More (Preferences, Connection, Developer on /admin), Security
  (registered; shown only with a node in the capability manifest, U5).
- `src/screens/` — today's screens, held by the destinations (`Drive.tsx` also gives Home's
  vehicle card and Drive mode).
- `src/icons/` — the Material Symbols subset (`material-symbols/*.svg`, Apache-2.0, copied
  verbatim) and `Icon`; list a new symbol in `symbols.ts` (a test keeps both in step).
- `tokens/*.tokens.json` (in `ui/`) — W3C design tokens: colours (light, dark), radii and the
  shell sizes per layout class; `tokens/tokens.ts` turns them into `virtual:design-tokens.css`.
- `src/lib/units.ts` — quantities and the clock through `Intl` (CLDR units where they exist).
- `src/components/` — shared pieces (Value, Gauge, Readout, Sheet, Preferences, ConnectionSheet,
  StatusTag, CoverageBar, PlaceholderReadout, ActionButton, ProcedureSheet, …).
- `src/screens/Analysis.tsx` + `components/replay/AnalysisView.tsx` — the map/chart/G-G/notes view,
  live (the drive in progress, marker on `snap.gps`) or replay; `components/RewindButton.tsx`
  in Logs opens the drive in progress at its latest sample and follows it as it grows
  (or opens the latest log at its end).
- `src/lib/flags.ts` + `state/flags.ts` — automatic flags derived from a session's data on load
  (sensor outside its `normal` band, faults appearing); never stored. `FlagSheet` shows one;
  the flag manager is the Flags section of `RecordingOptions` ("Recording & flags").
- `src/screens/Logs.tsx` + `src/components/replay/` — session browser and replay (MapLibre map,
  Canvas chart, transport bar) over `/sessions` (ADR-0009). `replay/maplibre.ts` is the only
  module that imports `maplibre-gl`; it is reached through `import()` so the main chunk stays
  small (`maplibreChunk.test.ts` enforces it). `src/state/playback.ts` is the shared cursor.
- `src/state/replay.tsx` + `replayState.ts` — whole-app replay (ADR-0010): while a session is open,
  `useApp()` returns a snapshot synthesised at the cursor, every action is refused, and
  the strip's Link chip becomes a flashing "Replay · Exit to live" button and `GlobalTransport`
  (with the note chip floating over the page above it) shows on every tab. `lib/audio.ts`, `lib/motion.ts` and
  `RecordingCard`/`RecordingOptions`/`MarkButton` are the recording side.
- `src/lib/catalog.ts` — the Stable/Experimental visibility rules over `/catalog` (ADR-0008).
- `src/layout.ts` — accessors over the active vehicle pack's layout (`/pack`, loaded at boot
  into `src/pack/store.ts`). Signal names for Drive tiles, the body view and LID presets live in
  the pack's `layout.json`, never in UI code. `src/vehicles/` holds pack-specific views
  (`lr_d2/`: SlabsCar, BodyCar) registered by pack id; a literal guard keeps module ids out of
  the rest of `src/`.
  Outputs, Settings and Utilities come from `/catalog`, never from a hard-coded list.
- `src/styles.css` — the screens' styles over the tokens (auto day/night); `src/shell/shell.css` the shell's.
- `e2e/` — Playwright against the test-only server `tests/e2e_server.py` (simulated car; ADR-0011);
  `shell.spec.ts` runs the four reference viewports with target-size asserts and axe (WCAG 2.2 AA).

## Editing rules

- Dev: `PYTHONPATH=src python3 tests/e2e_server.py` (test-only simulated car) in the repo root, then `npm run dev`. The product itself always runs live.
- Never hard-code signal labels, groups or units — they come from `/fields` (the signal store).
- A server response change → `UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`, then
  update `schemas.ts`.
- Before committing: `npm run check` (lint, typecheck, test, build) and commit `web/static`.
- Anything that writes to an ECU goes through `components/confirm.ts` (catalog actions via
  `ActionButton`, which applies the registry's `confirm` level). Actions are sent by `useAction`;
  a lint rule forbids naming `/command` outside `api/client.ts` and importing the raw `command()`
  outside the server-state senders listed in `eslint.config.js`.
- Navigate with route names (`goTo("diagnose.faults")`, `useShell().nav.open`), never tab ids.
  Screens read data from `useApp()` and shell services (layout, driving state, nav, sheets,
  formatting) from `useShell()`. New destinations, strip chips and slots are shell changes.
- No inline scripts and no `eval`: the built page sends `script-src 'self'` (zod runs jitless).
- Unit tests run as a 393×852 phone (`test/setup.ts`); call `setViewport()` for another class.
- One status vocabulary (ADR-0008): `StatusTag` + `CoverageBar`, shown in Experimental only.
  Stable shows verified items only. Never show a stale value as live (`Readout`).

## Design rules (calm instrument — ISA-101 + automotive HMI)

- Neutral when healthy. Colour (warn/alarm) only for abnormal values, always with an icon
  and a word (`StatusChip` for value ranges); OK values show no badge at all.
- Every number in context: `RangeBar` (span + `normal` band from the signal store) and a
  60 s `Sparkline`. Bands live in `signals/*.json` (`span`, `normal`), never in components.
- `HealthStrip` leads Home, Drive mode and Inputs with the one-line answer and links to the cause.
- Shell targets: 76 px on head units (`--target`), strip chips ≥ 48 px with an icon and a word,
  nothing interactive under 24 × 24 px (WCAG 2.2). Size with the layout tokens, not media queries.
- Status hues are validated with the dataviz `validate_palette.js` in both modes — re-run it
  if you change `--ok/--warn/--alarm/--accent`.
- Screens scroll: never let flex shrink a block (`main > *` is `flex-shrink: 0`).
