---
title: "Visual design direction — a dark, map-first refresh for Ostler (R10)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-05-replay-notes-capture-design.md, references/research/ui/head_unit_ui.md, references/research/ui/obd_apps.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, ui/tokens/color.dark.tokens.json]
summary: >
  Proposes Ostler's visual refresh after the owner's verdict that the styling is poor and his liking for the Speedometer app: dark and map-first by default with the light theme kept, built from near-black surfaces (Android Automotive's "build from black"), one cyan accent with a restrained glow, ISO 2575 status colours unchanged, a validated colour-blind-safe violet speed ramp, Figtree self-hosted with tabular numerals and big hero numbers, 4-pt spacing, larger radii, elevation by surface lightness, a night map as a Protomaps flavour on self-hosted PMTiles (OpenFreeMap as the online fallback), chart, gauge and component patterns, and head-unit versus phone density. Gives token tables the spec can lift, licences, and Copy/Avoid/Decide.
---

# Visual design direction (R10, October 2026)

The owner calls our styling "pretty terrible" and points at *Speedometer: Driving Tracker*
(screenshots in the research brief). This note turns that taste into tokens and patterns that
fit our rules (UI spec §2 principle 7 "calm instrument", head-unit first, ISO 2575 colours for
telltales only). Brands below are evidence only; none of their marks, fonts or signature colours
belong in our UI. All web sources checked 2026-10-07.

## 1. What is wrong today (code and screenshots)

Read from `ui/tokens/*.tokens.json`, `ui/src/styles.css`, `ui/src/shell/shell.css`,
`replay.css`, and the R9 screenshot set of the current build (light and dark; phone, tablet,
800×480 and 1280×480 head units; simulated car).

| # | Problem | Evidence |
|---|---|---|
| 1 | **Light-first; dark is a grey invert.** Dark surfaces step only 3–5 % apart (`#0e1012 → #16191c → #1c2024`), so cards barely separate and nothing reads as "lit". | `color.dark.tokens.json` |
| 2 | **Borders everywhere, hierarchy nowhere.** Cards, chips, buttons, strip chips and inputs all draw a 1 px outline, so screens look like boxes in boxes. | `.card`, `.btn`, `.schip`, `.iconbtn`, `.input` |
| 3 | **Radii small and inconsistent:** tokens give 6/12, but 4, 9999 and a hard-coded 10 px appear across files. | `styles.css`, `shell.css` |
| 4 | **Only colours, radii and shell sizes are tokens.** Type, spacing, elevation, motion and chart colours are hard-coded; shadows are raw `rgba()` in four files; a legacy alias layer (`--bg-card`, `--ic-red` …) doubles the names. | `styles.css` lines 23–34 |
| 5 | **The font loads from Google Fonts at run time.** Offline in the garage it silently falls back to the system font, and every page view tells Google the device's IP address. | `@import` in `styles.css`; `THIRD_PARTY_LICENSES.md` |
| 6 | **Text glyphs as icons:** ⏪ ⚙ ▶ ⏩ in buttons next to Material Symbols. | Logs, transport bar |
| 7 | **The map is an afterthought:** the replay map sits below a paragraph of description; on an 800×480 head unit about 70 px of it is visible above the transport bar. It is the bright "Liberty" style even in dark theme (night glare); offline it is a blank panel with "Map tiles unavailable". | `replay/maplibre.ts`; dark-hu800x480 session replay, light-phone session shots |
| 8 | **Numbers break their tiles:** "L/mil" unit clipped and "INTAKE A…" truncated on a 393 px phone (light); gauge arcs are thick and the track dominates. | light/dark phone Drive and Home shots |
| 8a | **Drive mode wastes the head unit:** at 800×480 a 76 px Back button and a title take a third of the height and the gauges fall below the fold. | dark-hu800x480 Drive shot |
| 9 | **One accent used as a slab:** a full-width saturated blue "Drive" bar is the loudest thing on Home, louder than the fault. | HU-9 Home shot |

What is right and must survive: the token pipeline (W3C DTCG JSON → CSS variables, UI spec
§10.1), the calm-instrument rules, word-plus-icon status, 76 px head-unit targets, the
perceptual plasma/mako trace ramps, tabular numerals already on `body`, and reduced-motion support.

## 2. What the references do (styling only)

| Source | Look | Borrow | Leave |
|---|---|---|---|
| **Speedometer** (brief screenshots) | Navy-black ground with a soft blue glow from the top edge; rounded cards (~16–20 px) one step lighter, hairline borders; huge bold numerals with a small grey unit; small caps kickers; cyan accent on the active tab pill and the gauge; full-bleed map with a floating playback sheet; donut and bar charts in green→yellow→orange→red | Hero number + unit, kicker + stat grid, floating sheet over a full-bleed map, pill tab bar, one cyan accent | The traffic-light speed palette (CVD-unsafe and it steals ISO red/amber); glow on everything |
| **RealDash** | Black canvas, skinnable gauges, everything user-placed (official site would not render for fetch; behaviour from `ui/obd_apps.md`) | Black canvas in Drive mode; gauges as a tile kind | Skeuomorphic chrome, per-user pixel layouts on the head unit |
| **Waze** | Night palette was map-only for years; a full app dark mode followed (Android Police, BGR) | Night must cover *all* chrome, not just the map | A light search sheet over a dark map at night |
| **Android Automotive** (developers.google.com/cars, colour and typography pages) | "Build from black"; a custom grey ladder because Material greys are too bright in cars; one saturated blue "car accent"; text at 88/72/56 % white; elevation shown by grey value; contrast ≥ 4.5:1; 24 dp minimum type while driving; Roboto, avoid bold for body | All of it: near-black base, elevation by lightness, 3 text levels, 24 px floor in Moving templates | — |
| **CarPlay HIG** (Apple, visual design page via search excerpt) | Prefers dark backgrounds, auto light/dark; warns that bright colours glare at night and low contrast washes out in sun; avoid red/green or blue/orange as the only cue; interactive and non-interactive must not share colours | Accent reserved for interactive things; data colours never equal the accent | — |
| **Polestar** (AAOS) | Black, minimal, squared-off; one orange accent carried into a customised Maps (9to5Google, Android Authority) | One brand accent applied consistently, even inside the map | Squared corners (the owner likes rounded) |
| **Tesla / Rivian** | Tesla's 2024 UI centres a large vehicle render while parked with the map as a pane (Not a Tesla App); Rivian's public material shows a near-black ink ladder (#151515 range) and one warm accent (third-party style digests, unverified) | Parked = vehicle hero; moving = map | Proprietary fonts and photography-led chrome |
| **Home Assistant** | Theme = CSS variables; 2025.5 added typed tokens (`--ha-font-family-*`, `--ha-font-size-2xs … 4xl`, weights, line heights) and removed the legacy `paper-*` variables (release notes); cards with a themeable radius; MDI icons | A documented token scale that third-party add-ons theme against; one card primitive | Per-user card-mod CSS hacks |
| **LubeLogger** (clone, read only) | Bootstrap 5 + Bootstrap Icons + Chart.js; 4 px cards with drop shadow that scale 1.05 on hover | Dense tables for the Garage add-on | Hover-scale cards (no hover in a car), 4 px radius |
| **Tracktor** (clone, read only) | shadcn-svelte on Tailwind, OKLCH greys, `--radius` 0.625 rem, a deliberately muted "vintage" chart palette (#5c7487, #b08a3c …), Lucide icons, LayerChart | OKLCH-defined neutrals; muted category palette for cost charts | Runtime Google Fonts import (same problem as ours) |

## 3. The direction in one paragraph

**Dark and map-first by default; light kept and equal.** Ostler opens on near-black surfaces
that step up in lightness for elevation, with no outlines on cards. The map is full-bleed
wherever there is a place (Trips, a trip, Vehicles & Map, Security fix) and everything else
floats over it as rounded sheets. Numbers are the hero: big, bold, tabular, with a small grey
unit. There is **one** accent, a clear cyan, for interactive and "live" things only, with a
soft glow on at most one element per screen and never in Moving templates. Status keeps the
ISO 2575 hues and word-plus-icon rule. Speed and other data use their own validated ramps,
never the accent and never red/amber/green. Light theme uses the same structure with white
cards on a cool grey ground and shadows instead of lightness steps.

## 4. Colour tokens

Contrast figures computed with WCAG relative luminance; the palette validator from the
dataviz method (`validate_palette.js`) was run on the accent+status set and both speed ramps.

### 4.1 Surfaces and text

| Token | Dark | Light | Notes |
|---|---|---|---|
| `bg` | `#0b0d10` | `#f3f5f7` | AAOS "build from black"; slight blue cast (Speedometer) |
| `bg-glow` | `radial-gradient(120% 60% at 50% 0%, #12304a66, transparent)` | none | top-edge glow, phone/tablet/desktop only; off on head units and in Drive mode |
| `surface-1` (card) | `#14181d` | `#ffffff` | cards: no border in dark; light uses `elev-1` |
| `surface-2` (raised, sheet) | `#1b2026` | `#ffffff` | sheets, popovers, strip |
| `surface-3` (control, pressed) | `#232a31` | `#e9edf1` | inputs, segmented track, gauge track |
| `surface-glass` | `rgba(20,24,29,0.86)` | `rgba(255,255,255,0.90)` | over the map; `backdrop-filter: blur(12px)` only on phone/desktop (cheap HU GPUs stutter) |
| `line` | `#ffffff14` (8 %) | `#0f141914` | hairlines inside cards and lists only |
| `line-strong` | `#ffffff24` | `#0f141929` | input outlines, focus fallback |
| `text-1` | `#eef2f6` (17.3:1 on bg) | `#0f1419` | values, titles |
| `text-2` | `#a9b3bd` (8.4:1 on card) | `#47515c` | labels, units |
| `text-3` | `#7d8893` (4.9:1 on card) | `#5f6a76` | captions; never below 4.5:1 |

### 4.2 Accent and semantic

| Token | Dark | Light | Rule |
|---|---|---|---|
| `accent` | `#22a6e0` | `#0070b8` (5.2:1 on white) | interactive and "live" only: selected tab, primary button, slider, current-position puck, live line |
| `accent-hi` | `#5cc4f0` | `#0a86d6` | hover/pressed; glow colour |
| `on-accent` | `#0b0d10` (7.0:1) | `#ffffff` (5.2:1) | text on accent |
| `accent-soft` | `#22a6e01f` | `#0070b81a` | selected chip, active tab pill background |
| `ok` / `warn` / `alarm` | keep `#2f9e63` / `#bf8a1a` / `#ef6a7d` | keep `#2e7d4f` / `#b08200` / `#d0263b` | ISO 2575, unchanged; already validated (CLAUDE.md design rules) |
| `ok-bg` / `warn-bg` / `alarm-bg` | keep | keep | |
| `info` | `#8aa4bf` (neutral blue-grey) | `#4a6178` | non-status notices; never the accent |

Validator (dark, surface `#0b0d10`, all pairs, `#22a6e0,#2f9e63,#bf8a1a,#ef6a7d`): chroma, normal
vision (ΔE ≥ 16.5) and contrast pass; worst CVD pair is the existing ok↔warn at 6.6 (legal only
with word+icon, as today); moving the accent from `#4f8ce8` to cyan raises its tritan
separation from 4.7 to 8.4. The "lightness band" check fails for accent and alarm because it is
a chart-mark rule; these are text/icon colours checked by contrast instead.

### 4.3 Speed ramp (colour-blind safe, 6 ordered bands)

Speedometer's green→yellow→orange→red fails red-green colour blindness and collides with ISO
amber/red, so a 120 km/h band would read as a warning. Ostler uses a **one-hue violet ramp**:
violet is free of every status and accent meaning, and "faster = brighter" on the dark map
reads as glow.

| Step | Dark (on dark map) | Light (on light map) | km/h band (default) | mph band (default) |
|---|---|---|---|---|
| 1 | `#5d3fa8` | `#bea0eb` | 0–30 | 0–20 |
| 2 | `#7e5acc` | `#a17ee4` | 30–50 | 20–30 |
| 3 | `#9e7be1` | `#8460d2` | 50–80 | 30–40 |
| 4 | `#bf9ef1` | `#6646b7` | 80–100 | 40–50 |
| 5 | `#dec4fb` | `#4b2e96` | 100–120 | 50–60 |
| 6 | `#f5e9fe` | `#311d6c` | 120+ | 60+ |

Validator `--ordinal`: both pass (monotone lightness, every gap ≥ 0.06 OKLCH L, hue spread
19°/14°). Dark light-end contrast 2.3:1 on `#15181c`. Light step 1 is only 1.7:1 on a beige
basemap, so the trace always gets a 2 px casing (dark map `#0b0d10`, light map `#ffffff`), as
`basemap.ts` already does. The same six colours fill the trace (stepped), the time-at-speed
donut and the speed-distribution bars, so the map and charts agree; every band is also
labelled in text. The existing continuous ramps (plasma, mako) stay for other channels.

## 5. Type

**Figtree**, self-hosted as woff2 (SIL OFL 1.1, bundling allowed; github.com/erikdkennedy/figtree).
Its Google Fonts build carries `tnum` and `pnum` (GSUB tables read 2026-10-07), so tabular
numerals work. Fallback: Inter (OFL 1.1, has `tnum` and slashed zero) if we ever need wider
script coverage; Noto Sans for scripts Figtree lacks (OFL). No runtime font CDN.

| Token | Phone | Head unit | Weight | Use |
|---|---|---|---|---|
| `num-hero` | 64/64 | 120/120 | 700, `tnum`, tracking −0.02em | one per screen: speed, total cost, all-time max |
| `num-xl` | 40/44 | 64/64 | 700 `tnum` | hero stat in a card, Drive tiles |
| `num-l` | 24/28 | 40/44 | 700 `tnum` | stat-grid values |
| `unit` | 0.42 × number | same | 600, `text-2` | always after the number, baseline-aligned, never wraps |
| `title` | 20/26 | 28/34 | 700 | screen and sheet titles |
| `body` | 15/22 | 24/32 | 400 / 500 | text; HU never below 24 while driving (AAOS) |
| `label` | 13/18 | 20/26 | 600 | field labels |
| `kicker` | 11/14 caps, +0.08em | 18/22 caps | 600, `text-2` | card headers ("TOTAL DIST"); parked/phone only |

Rules: numbers keep `font-variant-numeric: tabular-nums`; units shrink and labels truncate
before a number does (`min-width: 0` on the label, the number `white-space: nowrap`); a number
that cannot fit drops one size step, never clips (fixes problem 8).

## 6. Spacing, radius, elevation, glow, motion

| Group | Tokens |
|---|---|
| `space` (4-pt) | `1`=4 · `2`=8 · `3`=12 · `4`=16 · `5`=20 · `6`=24 · `8`=32 · `10`=40 · `12`=48 · `16`=64 |
| `radius` | `xs` 6 (tags) · `sm` 10 (chips, inputs, buttons) · `md` 16 (cards) · `lg` 24 (sheets, map overlays) · `xl` 32 (bottom-sheet top) · `pill` 9999 (tab pill, toggles) |
| `elev` (dark) | level by surface token only (`surface-1/2/3`) plus a 1 px top highlight `inset 0 1px 0 #ffffff0d`; no drop shadows |
| `elev` (light) | `elev-1` `0 1px 2px #0f14190f, 0 2px 8px #0f14190a` · `elev-2` `0 4px 16px #0f141914` · `elev-3` `0 12px 32px #0f14191f` |
| `glow` | `glow-accent` `0 0 0 1px #22a6e066, 0 0 24px #22a6e040` · `glow-trace` (map) `line-blur: 6`, `line-opacity: 0.35` under the trace |
| `motion` | `dur-fast` 120 ms · `dur-base` 200 ms · `dur-slow` 320 ms · `ease-standard` `cubic-bezier(0.2,0,0,1)` · `ease-exit` `cubic-bezier(0.3,0,1,1)` |

Glow and motion rules: at most one glowing element per screen (the hero number's gauge, the
live puck or the primary button); no glow on head units at night and none in Moving templates
(halation on the windscreen); motion only for sheet open/close, tab change and the
alarm pulse already specified; `prefers-reduced-motion` turns everything except state changes
off. The top `bg-glow` is decorative and off on head units.

## 7. Map

| Layer | Proposal | Licence and attribution |
|---|---|---|
| Renderer | MapLibre GL JS, as now (ADR-0009) | BSD-3-Clause |
| Offline tiles (default) | **PMTiles** regional extract (`pmtiles extract --maxzoom`, planet ≈ 120 GB at z0–15; a country at z14 should be low GB, unmeasured) served by the brain or bundled per region, read through the `pmtiles` protocol | PMTiles spec public domain; `pmtiles` JS BSD-3; tiles ODbL Produced Work → visible "© OpenStreetMap" in a map corner |
| Style | **Our own "Ostler Night" and "Ostler Day"** generated with `@protomaps/basemaps` flavours (a flavour is a typed colour object; the package ships light, dark, white, grayscale, black) | code BSD-3; map design CC0; a modified style must not be called Protomaps; icons MIT (Tangram); self-host glyphs and sprites |
| Online fallback | OpenFreeMap (no key, no limits stated, MIT project); "Dark" style for night, "Positron" or "Liberty" for day | Dark is derived from Dark Matter: design CC-BY 4.0 → credit "© OpenMapTiles" and "© OpenStreetMap contributors" in the corner |
| Imagery | unchanged (Esri personal use, USGS public domain; ADR-0010) | as today |

Ostler Night flavour overrides (start from Protomaps `DARK`): `background`/`earth` `#0e1114`,
`water` `#0f1a24`, `park_a` `#10181a`, `buildings` `#161b20`, `minor_a` `#1d2329`, `major`
`#283039`, `highway` `#34404b`, road labels `#8a96a2` with halo `#0b0d10`, place labels
`#a9b3bd`. Roads stay neutral grey so the violet trace and cyan puck are the only colour.
Ostler Day: Protomaps `LIGHT` with water `#cfe3f0` and greys pulled cooler. Attribution:
collapsed "ⓘ" button in the corner that expands on tap, which OSMF guidelines allow after
interaction; never removed. Schemas differ (Protomaps vs OpenMapTiles), so our layers insert
by a role (`below-labels`) that `maplibre.ts` resolves per style, not by a hard-coded layer id.

## 8. Charts and gauges

Following the dataviz method (one axis, thin marks, legend for ≥ 2 series, text in text tokens):

| Element | Spec |
|---|---|
| Grid / axes | grid `#ffffff0f` (dark) / `#0f141912`; axis labels `kicker`-size `text-3`, tabular |
| Line | 2 px `accent` for the live or primary series; area fill accent 24 % → 0 % vertical gradient; others in `text-2` grey |
| Bars | 4 px rounded data end at the top, square at the baseline, 2 px surface gap, speed bands use §4.3 |
| Donut | ring 14 % of diameter, 2 px surface gaps between segments, centre = `num-xl` total + `label`; legend rows with band, time and % (Speedometer's layout) |
| Gauge | 240° arc, 8 px track `surface-3`, value arc `accent` with round caps, `normal` band as two ticks; out of band: arc and value turn warn/alarm and the word appears (CLAUDE.md rule); number `num-xl` centred, unit below |
| Sparkline | 1.5 px `text-2`, last point dot `accent`; no axis |
| Hover / scrub | crosshair 1 px `text-3`, tooltip on `surface-2` |

## 9. Component patterns

| Pattern | Phone | Head unit (HU-7/9/wide) |
|---|---|---|
| **Hero stat** | kicker, `num-hero` + unit, one caption line; optional glow | `num-hero` 120; Drive mode = 1–3 hero stats only |
| **Stat grid** | 3 columns, `num-l` + kicker, hairline separators inside one card (Speedometer's trip card) | 2–3 columns, `num-l` 40, ≥ 24 px labels |
| **Donut / bar distribution** | in a card with a Time/Distance segmented control | parked only |
| **Scrubber** | 4 px track, 20 px thumb drawn, 48 px hit area; transport row 48 px icon buttons (Material Symbols, no text glyphs); speed chips 1×/2×/4×/8× | 76 px hit area; replay is parked-only |
| **Bottom sheet over map** | `surface-glass`, `radius-xl` top, grab handle, three snap points (peek 25 %, half, full) | side sheet on the passenger side, 520 px (existing `secondary-pane`) |
| **Card** | `surface-1`, `radius-md`, padding `space-4`, no border (dark), `elev-1` (light); tappable cards show a chevron, not a hover scale | padding `space-6` |
| **Tab bar** | floating pill bar: `surface-2`, `radius-pill`, active item `accent-soft` pill with accent icon and word | the existing driver-side rail with the same active pill |
| **Chips** | 32 px drawn / 48 px hit, `surface-3`, `radius-sm`; selected = `accent-soft` + accent text | 48 px drawn, 76 px hit |
| **Strip chips** | keep the strip, drop outlines: chips are text+icon on `surface-2`; only tone chips get a fill | same |
| **Primary action** | one accent button per screen, `radius-sm`, 48 px; no full-width accent slabs on Home | 76 px |

Density: the head unit uses the HU size tokens already in `size.tokens.json` plus the HU type
column above; phone shows more per screen but never below the 48 px target or 4.5:1 contrast.

## Copy / Avoid / Decide for Ostler

**Copy**

1. AAOS "build from black" surfaces, elevation by lightness, three text levels, 24 px floor in
   Moving templates → UI spec §2 (principle 4) and §10.1 (U1 tokens); app-model §4.4 templates.
2. Speedometer's hero number + kicker stat grid + floating sheet over a full-bleed map →
   replay spec §5 (the replay map); ADR-0009; Trips rename.
3. Home Assistant's typed token scale that add-ons theme against → app-model §2 (theming is a
   shell responsibility) and §6 (shell ↔ app API exposes tokens, not raw colours).
4. Self-hosted map style and tiles with visible OSM attribution → ADR-0009, ADR-0017,
   ADR-0025.
5. A validated, one-hue speed ramp shared by trace and charts → replay spec §5;
   `ui/CLAUDE.md` design rules (validator).

**Avoid**

1. Traffic-light speed colours (CVD-unsafe, steals ISO 2575 meaning) → UI spec §2 principle 7.
2. Glow, gradients or animation in Moving templates or at night on the head unit → UI spec §3.5.
3. Runtime font or icon CDNs (offline breaks, privacy) → ADR-0017, ADR-0025; `THIRD_PARTY_LICENSES.md`.
4. Outlines on every element and accent-coloured slabs as navigation → UI spec §3.4.
5. Backdrop blur on head-unit layout classes (frame drops on low-end GPUs) → UI spec §3.1.

**Decide** (recommendations for the owner)

1. **D1 Default theme.** Recommend: dark by default on every layout class, light kept as an
   equal choice, automatic switching (headlights / sun / OS) unchanged. → UI spec §2 principle 7, §10.1.
2. **D2 Accent.** Recommend: cyan `#22a6e0` (dark) / `#0070b8` (light) replacing `#4f8ce8` /
   `#1f6fe0`, interactive and live only. → `ui/tokens/color*.tokens.json`, UI spec §10.1.
3. **D3 Speed ramp.** Recommend: the validated six-step violet ramp in §4.3 for trace, donut and
   bars, with bands in the user's unit; plasma stays the default for other channels; no
   "classic" traffic-light option. → replay spec §5, ADR-0010.
4. **D4 Font.** Recommend: keep Figtree, self-host woff2 under OFL 1.1, add `OFL-1.1.txt` to
   `LICENSES/`, drop the Google Fonts import. → ADR-0025, `THIRD_PARTY_LICENSES.md`.
5. **D5 Map.** Recommend: Ostler Night/Day as Protomaps flavours (CC0 design) on self-hosted
   regional PMTiles served by the brain, OpenFreeMap Dark/Positron as the online fallback; a
   one-time region download in Settings. → amend ADR-0009.
6. **D6 Glow budget.** Recommend: one glowing element per screen on phone/desktop, none on head
   units at night or while Moving. → UI spec §2 principle 7 (amend wording "motion only for red
   alarms" to "motion and glow").
7. **D7 Token scope for U1.** Recommend: add type, space, radius, elevation, glow, motion and
   data-ramp tokens to `ui/tokens/` (DTCG JSON), retire the legacy alias layer, and ban raw
   colours in CSS with a lint rule. → UI spec §10 (U1), app-model §9 seams.

## Sources (checked 2026-10-07)

- Speedometer screenshots: research brief images `1.webp`, `2.png` (owner supplied).
- Android Automotive colour and typography: developers.google.com/cars/design/automotive-os/design-system/color and …/typography.
- CarPlay visual design (Apple HIG), via search excerpt of developer.apple.com/design/human-interface-guidelines/carplay (page did not render for fetch).
- Polestar maps accent: 9to5google.com, androidauthority.com (google-maps-custom-design-elements-polestar). Waze dark mode: androidpolice.com, bgr.com. Tesla V12 UI: notateslaapp.com/news/1988. Rivian palette: third-party style digests (unverified).
- Home Assistant 2025.5 release notes (typography tokens, `paper-*` removal): home-assistant.io/blog/2025/05/07/release-20255.
- Protomaps basemaps README (BSD-3 code, CC0 design, ODbL tiles, naming rule) and flavour source `styles/src/flavors.ts`; docs.protomaps.com (flavours, downloads, MapLibre `pmtiles` protocol).
- OpenFreeMap: openfreemap.org; styles and derivations: github.com/hyperknot/openfreemap-styles.
- Dark Matter licence (BSD-3 code, CC-BY 4.0 design, OpenMapTiles credit): github.com/openmaptiles/dark-matter-gl-style LICENSE.md.
- OSM attribution guidelines (corner, collapsible after interaction): osmfoundation.org/wiki/Licence/Attribution_Guidelines.
- Figtree (OFL 1.1): github.com/erikdkennedy/figtree; Inter (OFL 1.1, `tnum`): github.com/rsms/inter; OpenType feature tags read from the Google Fonts TTFs.
- Icons: Material Symbols Apache-2.0 (in use); Lucide ISC and Tabler MIT noted as alternatives, not proposed.
- LubeLogger and Tracktor: local read-only clones (`site.css`, `app.css`, `package.json`).
- Ramp and contrast checks: dataviz `validate_palette.js` and WCAG luminance, run locally.
