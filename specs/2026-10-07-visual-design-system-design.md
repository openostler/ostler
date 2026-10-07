---
title: "Visual design system — dark, map-first tokens, type, maps, charts and one component kit — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/visual_design_direction.md, references/research/ui_audit_current.md, references/research/app_teardown_speedometer.md, references/research/driver_distraction_rules.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, ui/tokens/color.dark.tokens.json]
summary: >
  Draft for owner approval, answering "our styling is pretty terrible". Ostler becomes dark by default and
  map-first, with numbers as the hero, calm gauges, one cyan accent and a glow budget, night-first on head
  units. Gives the full token set as tables ready to lift into ui/tokens/*.tokens.json (W3C DTCG, the
  existing pipeline): surfaces, text, accent and status for dark, dim, OLED and light; the validated violet
  speed ramp, a three-slot categorical set and the existing plasma/mako; type per layout class with
  minimums; space, radius, elevation, glow and motion; with contrast checks. Self-hosts Figtree (OFL), keeps
  Material Symbols as the one icon set and bans emoji glyphs. Maps are "Ostler Night/Day" Protomaps flavours
  on brain-served regional PMTiles with an OpenFreeMap fallback. Charts are our own SVG. One component kit
  (Button to TabBar) with phone and head-unit density, enforced by stylelint and Playwright, and a migration
  in small PRs (V1 tokens, font, maps; V2 kit; V3 pages) that lands before U2 build work.
---

# Visual design system — design (draft)

**Status:** draft for the owner's approval; nothing is built until it is approved. The evidence is
[visual design direction](../references/research/visual_design_direction.md) (values, references) and
the [UI audit](../references/research/ui_audit_current.md) (problems P1–P15 with file:line citations and
196 screenshots); this spec decides and does not repeat them. It changes no decision of the
[UI spec](2026-10-06-ui-architecture-design.md) except where a numbered item in **Decisions for the
owner** proposes an amendment. Other drafts of this round (Trips, Vehicles & Map, Social, Maintenance,
ADR-0042) reference **token names only**; this spec owns the values.

## 1. Principles

1. **Dark by default, light equal.** Every layout class opens dark; Day (light) is an equal, fully
   themed choice, and Auto (OS on phone/desktop; sun or headlights on head units) stays available.
2. **Map-first.** Where there is a place (a trip, Trips, Vehicles & Map, a Security fix) the map is
   full-bleed and everything else floats over it as a rounded sheet (P2).
3. **Data is the hero.** One hero number per screen, big, bold and tabular with a small grey unit, then a
   quiet borderless stat grid (P5, P6). A number never clips: it drops one type step first.
4. **Calm gauges.** Neutral when in range; warn or alarm (with icon and word) only out of range; accent
   never marks a value (P14, UI spec §2 principle 7).
5. **One accent.** Cyan, for interactive and *live* things only: the selected tab, the primary button,
   the scrub thumb, the live puck, the live series. Data ramps never use it; status never uses it.
6. **Glow budget.** At most one glowing element per screen on phone, tablet and desktop; **no glow** on
   head units in Night dim or Deep night, in Drive mode or in any Moving template (halation).
7. **Night-first head units.** Head units go to **Night dim** after dusk (Auto), with no top glow, no blur
   and no gradients; the alarm pulse is the only motion while Moving.
8. **Depth by surface, not borders.** Dark elevates by lightness plus a 1 px top highlight; light uses
   soft shadows. Hairlines only inside cards and lists (P3, P5).
9. **One vocabulary.** Tokens only, one component kit, one icon set; raw colours, sizes and emoji glyphs
   fail CI (§9).

## 2. Token pipeline (fits UI spec §10.1)

The files stay W3C DTCG JSON in `ui/tokens/`, compiled by `tokens.ts` into `virtual:design-tokens.css`.
Changes:

| File | Holds | CSS scope |
|---|---|---|
| `color.dark.tokens.json` | the default theme (Night) | `:root` (was `@media`/`[data-theme=dark]`) |
| `color.dim.tokens.json` (new) | Night dim overrides | `:root[data-theme="dim"]` |
| `color.oled.tokens.json` (new) | Deep night overrides | `:root[data-theme="oled"]` |
| `color.tokens.json` | Day (light) | `:root[data-theme="light"]` |
| `data.tokens.json` (new) | speed ramp, categorical, plasma/mako stops, chart neutrals, per theme group | `:root` and the theme selectors |
| `map.tokens.json` (new) | Ostler Night/Day flavour colours | build-time only: generates the two style JSONs (§6) |
| `size.tokens.json` | shared space, radius, motion, font tokens; per-class shell and **type** tokens | `:root`; `.app[data-layout=<class>]` |

`tokens.ts` gains DTCG types `shadow`, `duration`, `cubicBezier`, `fontFamily`, `fontWeight`, `number`
and `gradient`; the shell resolves Auto to a concrete `data-theme` before first render (no inline script;
CSP stays `script-src 'self'`). Canvas and MapLibre read colours through one `token(name)` helper over
`getComputedStyle`, so no component holds a hex value. `tokens.test.ts` asserts every theme file defines
the same names as the dark file.

## 3. Colour

All contrast ratios are WCAG relative luminance, computed 2026-10-07; categorical and ordinal sets were run
through the dataviz `validate_palette.js`.

### 3.1 Surfaces, text, accent and status per theme

| Token | Night (dark, default) | Night dim (HU after dusk) | Deep night (OLED) | Day (light) | Use |
|---|---|---|---|---|---|
| `bg` | `#0b0d10` | `#07090b` | `#000000` | `#f3f5f7` | page, map fallback |
| `bg-glow` | `radial-gradient(120% 60% at 50% 0%, #12304a66, transparent)` | `none` | `none` | `none` | phone/tablet/desktop top glow; off on HU and Drive mode |
| `surface-1` | `#14181d` | `#0e1114` | `#0d1014` | `#ffffff` | cards (no border) |
| `surface-2` | `#1b2026` | `#13171b` | `#14181d` | `#ffffff` | sheets, popovers, strip, tab bar |
| `surface-3` | `#232a31` | `#1a1f24` | `#1c2127` | `#e9edf1` | inputs, segmented track, gauge track |
| `surface-glass` | `#14181ddb` | `#0e1114f0` | `#000000e0` | `#ffffffe6` | sheets over the map; blur 12 px on phone/desktop only |
| `line` | `#ffffff14` | `#ffffff0f` | `#ffffff14` | `#0f141914` | hairlines inside cards and lists |
| `line-strong` | `#ffffff24` | `#ffffff1a` | `#ffffff24` | `#0f141929` | input outline, focus fallback |
| `band` | `#3a424a` | `#2c333a` | `#2c333a` | `#c9d0d8` | normal band on a track |
| `text-1` | `#eef2f6` | `#c4ccd4` | `#eef2f6` | `#0f1419` | values, titles |
| `text-2` | `#a9b3bd` | `#8e98a2` | `#a9b3bd` | `#47515c` | labels, units, in-range gauge arc |
| `text-3` | `#7d8893` | `#7e8892` | `#7d8893` | `#5f6a76` | captions; never on `surface-3` |
| `accent` | `#22a6e0` | `#1b8fc2` | `#22a6e0` | `#0070b8` | interactive and live only |
| `accent-hi` | `#5cc4f0` | `#3aa6d6` | `#5cc4f0` | `#005a94` | pressed; glow colour |
| `accent-soft` | `#22a6e01f` | `#1b8fc21f` | `#22a6e024` | `#0070b81a` | selected chip, tab pill |
| `on-accent` | `#0b0d10` | `#07090b` | `#000000` | `#ffffff` | text on accent |
| `ok` / `warn` / `alarm` | `#2f9e63` / `#bf8a1a` / `#ef6a7d` | same | same | `#2e7d4f` / `#b08200` / `#d0263b` | ISO 2575, unchanged; icon, edge, fill |
| `ok-bg` / `warn-bg` / `alarm-bg` | `#13281d` / `#2e2612` / `#33171c` | same | same | `#e2f2e8` / `#fbf1d9` / `#fbe3e6` | status tint |
| `warn-ink` (new) | `#bf8a1a` | same | same | `#8a6600` | warn-coloured *text* on white |
| `info` | `#8aa4bf` | `#7790aa` | `#8aa4bf` | `#4a6178` | neutral notices; never the accent |
| `overlay` | `#000000a6` | `#000000b3` | `#000000b3` | `#0a0c0f8c` | sheet scrim |

Status stays the same in Night dim because an alarm must stay salient after dusk; only text and accent
dim. `surface`, `raised` and `sunken` remain as aliases of `surface-1/2/3` until V3.5 retires them.

### 3.2 Contrast checks (text on its surfaces; target ≥ 4.5:1)

| Pair | Night | Dim | Deep night | Day |
|---|---|---|---|---|
| `text-1` on `bg` / `surface-1` / `surface-3` | 17.3 / 15.8 / 12.9 | 12.3 / 11.7 / 10.2 | 18.7 / 16.9 / 14.4 | 16.9 / 18.5 / 15.7 |
| `text-2` on `surface-1` / `surface-3` | 8.4 / 6.8 | 6.5 / 5.7 | 9.0 / 7.6 | 8.1 / 6.9 |
| `text-3` on `surface-1` / `surface-2` / `surface-3` | 4.9 / 4.5 / **4.0** | 4.8 / 4.6 / 4.6 | 5.3 / 4.9 / 4.5 | 5.5 / 5.5 / 4.7 |
| `accent` on `surface-1` / `surface-3` | 6.4 / 5.3 | 5.2 / 4.5 | 6.9 / 5.9 | 5.2 / 4.5 |
| `on-accent` on `accent` | 7.0 | 5.5 | 7.6 | 5.2 |
| `ok` / `warn` / `alarm` on `surface-1` | 5.3 / 5.8 / 6.0 | 5.6 / 6.2 / 6.3 | 5.6 / 6.2 / 6.4 | 5.0 / **3.5** / 5.2 |

Findings and rules: Night `text-3` on `surface-3` is 4.0, so `text-3` is banned on `surface-3`
(placeholders use `text-2`). Day `warn` on white is 3.5:1 (passes 3:1 for icons and edges only), hence
`warn-ink` (5.3:1) for warn-coloured words. Status words on a `*-bg` tint use `text-1` (Day 16.5:1 on
`warn-bg`; Day `ok`/`alarm` text on their tints is 4.3–4.4, below target). The accent fixes the axe
failure in P13 (active chip, 4.44:1 today; 5.2 on `surface-1` in Day).

### 3.3 Data ramps and chart colours (`data.tokens.json`)

**Speed ramp** (`speed-1` … `speed-6`; visual direction §4.3, ordinal validator passes both themes:
monotone L, gaps ≥ 0.06, hue spread 19°/14°). Used by the map trace, the time-at-speed donut, the speed
distribution bars and the speed-over-time line, so one colour means one speed everywhere; every band also
carries its label in text.

| Step | Dark themes | Day | km/h | mph |
|---|---|---|---|---|
| 1 | `#5d3fa8` | `#bea0eb` | 0–30 | 0–20 |
| 2 | `#7e5acc` | `#a17ee4` | 30–50 | 20–30 |
| 3 | `#9e7be1` | `#8460d2` | 50–80 | 30–40 |
| 4 | `#bf9ef1` | `#6646b7` | 80–100 | 40–50 |
| 5 | `#dec4fb` | `#4b2e96` | 100–120 | 50–60 |
| 6 | `#f5e9fe` | `#311d6c` | 120+ | 60+ |

Light ends are below 3:1 against the map (2.5:1 dark, 2.2:1 day), so the trace always has a 2 px casing
(`trace-casing`: `bg` in dark themes, `#ffffff` in Day). Bands are per unit preference, not converted.

**Categorical** (`series-1` … `series-3`; for identity, e.g. Maintenance cost categories):

| Slot | Dark themes | Day | Validator |
|---|---|---|---|
| 1 indigo | `#6a7de6` | `#4a5fd0` | all-pairs pass on `surface-1`: worst CVD ΔE 12.6 dark / 11.8 day, normal-vision ≥ 19.3 |
| 2 teal | `#2a9d8c` | `#008f7a` | |
| 3 orange | `#d06a30` | `#c0581f` | |

Three is the cap: accent, violet (speed) and the ISO hues leave no fourth hue that clears the floors.
Measured conflicts (normal-vision ΔE < 15): teal↔`ok` 6.0, orange↔`warn` 8.6, indigo↔`accent` 11.7,
so a categorical chart **never also draws status colours or an accent mark** (the scrub cursor stays
`text-3`); a fourth series folds into "Other" or small multiples. No diverging ramp is defined; one needs
a proposal with a validator run.

**Continuous** `plasma` and `mako` (20 stops each, today in `trace.ts`) move to `data.tokens.json`
unchanged for non-speed channels. **Chart neutrals:** `chart-grid` `#ffffff0f` / Day `#0f141912`;
`chart-axis` = `text-3`; `chart-crosshair` = `text-3`; `series-mono` = `series-1` for any single
recorded non-speed channel; `series-live` = `accent` for the drive in progress only.

## 4. Type

**Figtree** (SIL OFL 1.1), self-hosted variable woff2, Latin and Latin-ext subsets, weights 400–700,
`font-display: swap`, preloaded; the Google Fonts `@import` (`ui/src/styles.css:11`, P7) is deleted.
Fallback stack: `Figtree, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. `font-mono` is
unchanged. Numbers always `tabular-nums`.

Per layout class (`size.tokens.json` → `.app[data-layout]`), size/line-height in px:

| Token | Phone | Tablet, desktop | HU-7 | HU-9/10, HU-wide | Weight | Use |
|---|---|---|---|---|---|---|
| `type-hero` | 64/64 | 72/72 | 96/96 | 120/120 | 700, −0.02em | one per screen |
| `type-num-xl` | 40/44 | 48/52 | 64/64 | 72/72 | 700 | card hero, Drive tiles (≥ 56 px digits, template rule) |
| `type-num-l` | 24/28 | 28/32 | 40/44 | 40/44 | 700 | stat-grid values |
| `type-title` | 20/26 | 22/28 | 32/38 | 32/38 | 700 | screen and sheet titles (UI spec 32 px HU) |
| `type-body` | 15/22 | 15/22 | 24/32 | 24/32 | 400/500 | text |
| `type-label` | 13/18 | 13/18 | 20/26 | 22/28 | 600 | field and row labels |
| `type-kicker` | 12/16 caps +0.08em | 12/16 | 18/22 | 18/22 | 600, `text-2` | card headers; Parked only on HU |
| `type-caption` | 12/16 | 12/16 | 18/24 | 18/24 | 500, `text-3` | meta lines |
| `unit-ratio` | 0.45 | 0.45 | 0.45 | 0.45 | 600, `text-2` | unit size = digits × ratio, never below the class minimum |

**Minimums:** 12 px on phone, tablet and desktop; 18 px on any head-unit class when Parked; **24 px for
anything in a Moving template** (AAOS floor). The 9–11 px sizes in P4 disappear. `type-primary` and
`type-secondary` become aliases of `type-title` and `type-body`, then retire in V3.5. Fitting rule: label
`min-width: 0` with ellipsis, number `white-space: nowrap`; if a number cannot fit, the component drops
one step (`num-xl` → `num-l`); clipping is a test failure (fixes P8 "L/mil", "INTAKE A…").

## 5. Space, radius, elevation, glow, motion

| Group | Tokens |
|---|---|
| `space-*` (4-pt) | `1` 4 · `2` 8 · `3` 12 · `4` 16 · `5` 20 · `6` 24 · `8` 32 · `10` 40 · `12` 48 · `16` 64; card padding `space-4` phone, `space-6` HU; `--gap` per class unchanged |
| `radius-*` | `xs` 6 tags · `sm` 10 chips, inputs, buttons · `md` 16 cards · `lg` 24 map overlays, side sheet · `xl` 32 bottom-sheet top · `pill` 9999 tab pill, toggles (today `sm` 6 and `md` 12 change value in V1) |
| `elev-1/2/3` dark themes | surface step plus `inset 0 1px 0 #ffffff0d`; no drop shadows (`elev-3` sheets add `0 -8px 24px #00000066` over the map only) |
| `elev-1/2/3` Day | `0 1px 2px #0f14190f, 0 2px 8px #0f14190a` · `0 4px 16px #0f141914` · `0 12px 32px #0f14191f` |
| `glow-accent` | Night `0 0 0 1px #22a6e066, 0 0 24px #22a6e040`; Dim, Deep night, Day `none` |
| `glow-trace` (map) | `line-blur` 6, `line-opacity` 0.35 under the trace in Night only |
| motion | `dur-fast` 120 ms · `dur-base` 200 ms · `dur-slow` 320 ms · `ease-standard` `cubic-bezier(0.2,0,0,1)` · `ease-exit` `cubic-bezier(0.3,0,1,1)` |

Motion only for sheet open/close, tab change and the alarm pulse; `prefers-reduced-motion` sets every
duration to 0 and turns the pulse into a static ring. A glowing element carries `data-glow`; the shell
strips it on head units at night and in Drive mode; tests count it (§9).

## 6. Icons and fonts

**One icon set: Material Symbols** (outlined, Apache-2.0, already vendored in `ui/src/icons/`). Add the
glyphs that are emoji today (P8): `fast_rewind`, `play_arrow`, `pause`, `fast_forward`, `flag`,
`settings`, `history`, `check`, `priority_high`, `warning`, `expand_more`, `chevron_right`,
`chevron_left`, `bolt`, `speed`, `route`, `timer`. Icon sizes: 20/24 phone, 32/40 HU. Icons sit in text
colour; a status icon wears its status hue; never an emoji, dingbat or Unicode arrow in UI text (§9).
Medals for records are numerals in a `surface-3` disc, not gold/silver/bronze colour.

## 7. Maps

| Layer | Decision | Licence and attribution |
|---|---|---|
| Renderer | MapLibre GL JS, lazy chunk as today (ADR-0009) | BSD-3-Clause |
| Tiles (default) | regional **PMTiles** extract (`pmtiles extract`, z0–14, region picked once in Settings → Maps; size unmeasured) stored and served by the Brain with HTTP Range at `/maps/<region>.pmtiles`; the node-only setup uses the online fallback | PMTiles spec public domain, `pmtiles` JS BSD-3; tiles are an ODbL Produced Work |
| Styles | **Ostler Night** (from Protomaps `DARK`) and **Ostler Day** (from `LIGHT`), generated at build time with `@protomaps/basemaps` from `map.tokens.json`; never called "Protomaps" (naming rule) | code BSD-3, design CC0 |
| Glyphs, sprites | self-hosted from Protomaps basemaps-assets (Noto Sans PBF); licence of each file confirmed in V1c | Noto Sans OFL 1.1 |
| Online fallback | OpenFreeMap `dark` (Night, Dim, Deep night) and `positron` (Day); Liberty kept only as an optional "Detailed" basemap | design CC-BY 4.0 (OpenMapTiles, CARTO): "© OpenMapTiles © OpenStreetMap contributors" |
| Offline fallback | a background of `--bg`, the trace and the puck (replaces hard-coded `#eef0f2`, `maplibre.ts:35`) | — |
| Imagery | unchanged (ADR-0010) | as today |

`map.tokens.json` (Night): `earth`/`background` `#0e1114`, `water` `#0f1a24`, `park` `#10181a`,
`buildings` `#161b20`, `minor` `#1d2329`, `major` `#283039`, `highway` `#34404b`, `road-label`
`#8a96a2`, `place-label` `#a9b3bd`, `label-halo` `#0b0d10`. Day: Protomaps `LIGHT` with `water`
`#cfe3f0` and cooler greys. Roads stay grey so the violet trace and cyan puck are the only colour. Our
layers insert by role (`below-labels`, `top`) resolved per style in `maplibre.ts`, never by a layer id
(Protomaps and OpenMapTiles schemas differ).

**Interaction.** Full-bleed maps own their gestures; a map inside a scrolling page uses
`cooperativeGestures: true` (P2 scroll trap). Overlay controls are kit components on `surface-glass`,
not hard-coded white (`replay.css:96-119`). **Attribution** is a collapsed ⓘ control (Material
`info`) in a corner that expands on tap (OSMF guideline), never removed, in every theme. Head-unit
rules while Moving follow the shared lockout position: own position and route only; other vehicles
only as plain markers for opted-in convoy members.

## 8. Charts, gauges and the component kit

**Library decision: our own SVG**, with the existing Canvas `Chart.tsx` kept for dense replay lanes. We
need four forms (donut, distribution bars, area line, gauge) plus the sparkline we already draw; own SVG
reads tokens directly, adds no dependency or bundle weight on head-unit CPUs and matches the dataviz mark
specs. Recharts (MIT) is the alternative if a fifth form appears.

| Element | Spec |
|---|---|
| Gauge | 240° arc, 8 px track `surface-3` (HU 12 px), `band` ticks for the normal range, value arc `text-2` with round caps when in range; out of range arc and number turn `warn`/`alarm` and the word appears; no accent, no glow, ≤ 4 Hz redraw while Moving |
| Donut (time at speed) | ring 14 % of diameter, 2 px `surface-1` gaps, centre `type-num-xl` total + `type-label`; legend rows: band swatch, label, time, % (Time/Distance segmented above) |
| DistributionBars | 4 px rounded data end, square at baseline, 2 px gaps, `speed-*` fills, axis `chart-axis`, values labelled |
| Area line | 2 px line; area fill line colour 24 % → 0 %; speed uses `speed-4`; crosshair + tooltip on `surface-2` |
| Sparkline | 1.5 px `text-2`, last point dot `text-1` (accent only when live) |

Every chart has hover/scrub tooltips, a legend for ≥ 2 series and a table view; text wears text tokens.

**Component kit** (`ui/src/kit/`, one file each, exported to add-ons through the shell `ui` API):

| Component | Variants and states | Phone | Head unit |
|---|---|---|---|
| **Button** | primary (accent, one per screen), secondary (`surface-3`), ghost, danger (alarm text); default, pressed (`accent-hi`/lighter surface), focus-visible ring 2 px `accent`, disabled 40 %, loading | 48 px, `radius-sm`, `type-label` | `--target` 76 px, `type-body` |
| **Segmented** | 2–4 options; selected = `accent-soft` fill + `accent` text (the only selected style; P3) | 40 px drawn, 48 hit | 76 px |
| **Chip** | filter, choice, status (tone with icon + word); selected as Segmented | 32 drawn, 48 hit | 48 drawn, 76 hit |
| **ListRow** | icon, title, meta, trailing value or chevron; pressed tint; ≤ 30 characters in `short_list` | 56 px | 76 px |
| **Card** | `surface-1`, `radius-md`, no border; tappable shows a chevron, never hover-scale; tone variants use `*-bg` + 4 px edge | padding 16 | padding 24 |
| **StatTile** | kicker + value + unit; honest states: stale (`text-3`, "stale" word), candidate (dashed underline, Experimental only), missing ("—", never 0) | `type-num-l` | `type-num-xl` |
| **HeroStat** | kicker, `type-hero` + unit, one caption; optional `data-glow` | 64 px | 96–120 px |
| **Donut**, **DistributionBars** | as above | in a Card | Parked only |
| **Scrubber** | 4 px track, 20 px thumb (accent), note/flag ticks with 24 px hit areas (fixes P13), 1×/2×/4×/8× chips, Material transport icons | 48 hit | 76 hit; replay Parked only |
| **Sheet over map** | `surface-glass`, `radius-xl` top, grab handle, snap peek 25 % / half / full | bottom sheet | side sheet 520 px on the passenger side, no blur |
| **TabBar** | phone: floating pill bar on `surface-2`, active item `accent-soft` pill + accent icon + word | bottom | the existing driver-side rail with the same active pill |

Retired with V3: `.btn`, `.iconbtn`, `.chip`, `.rchip`, `.seg`, `.area-tab`, `.opt`, `.morerow`,
`.sysrow`, `.connnotice-btn`, `.replay-basemap-btn` (P3 list).

## 9. Enforcement

- **stylelint** (MIT) with `stylelint-declaration-strict-value` (MIT): `color`, `background*`,
  `border-color`, `fill`, `stroke`, `font-size`, `line-height`, `border-radius`, `box-shadow`, `gap`,
  `padding`, `margin`, `transition-duration` must be `var(--…)`, `0`, `inherit` or `currentColor`;
  `color-no-hex` everywhere except `ui/tokens/`. Warn in V1, error after V3.5.
- **ESLint:** no hex/rgb literals and no `fontSize` in `style={{}}` or TSX; a vitest scans `src/` for
  `\p{Extended_Pictographic}` and the dingbats ⏪ ⏩ ▶ ❚ ✓ ⚠ ▾ ▸ ‹ › in strings and JSX text.
- **Legacy aliases** (`--fg`, `--bg-card`, `--ic-red` …, `styles.css:27-36`) are rewritten to tokens in
  V2–V3 and deleted in V3.5; a test fails if any is defined.
- **Playwright** per layout class (phone 390×844, tablet 1024×768, HU 800×480, 1024×600, 1280×480,
  1280×720, 1920×720) × theme (Night, Dim, Day): `toHaveScreenshot` for Home, Trips list, trip detail,
  Drive mode, Diagnose faults and the fault sheet; **Drive mode `main` must not scroll** at every HU size
  (P1); no visible text below the class minimum; no element with clipped text (`scrollWidth >
  clientWidth` on numbers); ≤ 1 `[data-glow]` on phone, 0 on HU at night and in Drive mode; axe WCAG 2.2
  AA in all three themes; target sizes as today.

## 10. Before and after

| Screen | Today (audit) | After |
|---|---|---|
| **Home** | 20 px "Home" title, a full-width saturated-blue Drive slab louder than the fault, one Last-trip card, ~60 % empty at 1280×480 (P5, P9) | Night `bg` with top glow (phone); HealthStrip as a tone Card only when abnormal; the vehicle card with one HeroStat (battery or coolant by role) and a 3-column stat grid; a Last-trip Card with a small static dark map thumbnail, distance and duration as `num-l`; Drive is a secondary Button and the rail/tab item, not a slab |
| **Trip detail** | title, back, Export, a prose paragraph, then a 42 vh light Liberty map, values, G-G, lanes; transport outside the map, emoji buttons (P2, P6, P8) | full-bleed Ostler Night map with the violet trace and cyan puck; a Sheet over the map: peek = HeroStat (distance or max speed) + Scrubber with Material transport; half = 3×3 stat grid (distance, duration, moving, idle, avg, max, stops, elevation, avg moving), time-at-speed Donut with Time/Distance Segmented, DistributionBars; full = speed-over-time area line, lanes, notes, "About this trip" collapsed; on HU a 520 px side sheet, Parked only |
| **Drive mode** | 76 px Back button and title take ~45 % of the height; the red tile is below the fold at 1024×600; accent gauge arcs (P1, P14) | no title; Back moves into the strip; the fault folds into the telltale chip; ≤ 6 tiles sized by height (`grid-auto-rows: 1fr`), Night dim after dusk, `num-xl` digits, neutral arcs, the out-of-range tile in `alarm` with its word; no glow, no gradient; fits one screen at every HU size (tested) |

## 11. Migration (small PRs; waits for approval; all before U2 build work)

| PR | Ships | Test |
|---|---|---|
| **V1a** tokens | `tokens.ts` types and theme scopes; new files (dim, oled, data, map); values of §3–§5; old names aliased | `tokens.test.ts` name parity; contrast table as a unit test |
| **V1b** font | Figtree woff2 in `ui/public/fonts/`, `LICENSES/OFL-1.1.txt`, REUSE entry, `THIRD_PARTY_LICENSES.md`; delete the `@import` | e2e offline run renders Figtree |
| **V1c** maps | Ostler Night/Day generation, `pmtiles` protocol, Brain range route and region download (platform), OpenFreeMap dark/positron fallback, `--bg` offline, cooperative gestures, attribution control, roles for layer insertion | `maplibre.test.ts` per style; offline fixture |
| **V1d** icons and lint | Material glyphs replace emoji (P8); stylelint and ESLint rules in warn mode | glyph scan test |
| **V2a–c** kit | (a) Button, Segmented, Chip, ListRow, Card; (b) StatTile, HeroStat, calm Gauge, Sparkline; (c) Donut, DistributionBars, Scrubber, Sheet over map, TabBar | vitest per component; screenshot per class × theme |
| **V3.1** Drive mode | fit-one-screen layout, strip Back, telltale fold | no-scroll assert at all HU sizes |
| **V3.2–3.4** pages | Home; Trips list and trip detail (with the Trips spec); Diagnose, More, sheets, fault sheet (one fault design, P11) | Playwright snapshots |
| **V3.5** retire | legacy aliases and classes deleted; lint rules to error | lint in CI |

Add-on authoring ([ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md)) starts against the V2 kit, so add-ons inherit it.

## 12. Licences

| Item | Licence | Obligation |
|---|---|---|
| Figtree | SIL OFL 1.1 | ship `OFL-1.1.txt`; no sale of the font alone; reserved name kept |
| Material Symbols | Apache-2.0 | already in `LICENSES/` and notices |
| MapLibre GL JS, `pmtiles` | BSD-3-Clause | notices (existing) |
| `@protomaps/basemaps` | BSD-3 code, CC0 design | modified style not called "Protomaps" |
| Noto Sans glyphs | SIL OFL 1.1 | as Figtree |
| OpenStreetMap data (PMTiles, OpenFreeMap) | ODbL 1.0 | "© OpenStreetMap contributors" visible on every map |
| OpenFreeMap `dark` / `positron` styles | CC-BY 4.0 design | "© OpenMapTiles" credit while used |
| stylelint, `stylelint-declaration-strict-value` | MIT | dev-only |
| Recharts (not adopted) | MIT | — |

## Decisions for the owner

1. **Default theme?** Recommend: dark (Night) on every layout class, Day equal, Auto as an option.
   Alternative: phones follow the OS by default, head units dark (audit D1).
2. **Night variants?** Recommend: add Night dim (automatic on head units after dusk) and Deep night
   (OLED, opt-in). Alternative: one dark theme only.
3. **Accent?** Recommend: cyan `#22a6e0` / `#0070b8`, interactive and live only. Alternative: keep
   blue `#4f8ce8` / `#1f6fe0`.
4. **Speed colours?** Recommend: the validated violet ramp everywhere, no traffic-light option.
   Alternative: also offer Speedometer's green→red as an opt-in (CVD-unsafe, collides with ISO amber/red).
5. **Gauges?** Recommend: neutral arcs in range, status colour and word only out of range.
   Alternative: accent arcs as today.
6. **Glow?** Recommend: one glow per screen on phone/tablet/desktop, none on head units at night or in
   Drive mode; amend UI spec §2 principle 7 to "motion and glow only …". Alternative: no glow anywhere.
7. **Font?** Recommend: self-host Figtree (OFL), delete the Google Fonts import. Alternative: Inter (OFL).
8. **Icons?** Recommend: Material Symbols only, emoji and dingbats banned by test. Alternative: Lucide (ISC).
9. **Maps?** Recommend: Ostler Night/Day Protomaps flavours on Brain-served regional PMTiles, OpenFreeMap
   dark/positron online fallback, `--bg` offline; amend ADR-0009. Alternative: OpenFreeMap online only.
10. **Charts?** Recommend: our own SVG primitives plus the existing Canvas lanes. Alternative: Recharts (MIT).
11. **Type minimums?** Recommend: 12 px phone, 18 px head unit Parked, 24 px in Moving templates.
    Alternative: the audit's 16 px head-unit floor.
12. **Enforcement and order?** Recommend: stylelint/ESLint bans and Playwright checks as §9, V1–V3 before
    U2 build work, Drive mode fit (V3.1) allowed to land first. Alternative: migrate pages as they are
    touched, with no lint gate.
13. **800×480 head units?** Recommend: test them in Playwright now and propose an HU-5 layout class as a
    UI spec amendment. Alternative: keep them in HU-7.

## Changelog

- 0.1 (2026-10-07): first draft from the visual design direction and UI audit research.
