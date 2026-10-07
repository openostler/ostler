---
title: "UI audit — Ostler's current styling, page by page, against the Speedometer reference (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/ui/head_unit_ui.md, references/research/ui/obd_apps.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0008-unified-status-vocabulary.md]
summary: >
  An honest audit of the built Ostler PWA (commit 1d5161e), screenshotted from the recorded-session
  test server at phone 390×844, tablet 1024×768, HU 1024×600, 1280×480 and 800×480, light and dark,
  with axe 4.13 and measured font sizes and target sizes. The owner's verdict holds: the foundations
  (tokens, layout classes, honest status words) are sound, but the surface has no visual system.
  There are a dozen button styles, 16 font sizes, emoji icons and a small light map inside a dark UI.
  Drive mode scrolls on every head unit, and post-trip analysis has no summary stats. Ranks the top
  15 problems with file:line citations, and ends with Copy / Avoid / Decide.
---

# UI audit — current styling (October 2026)

**Verdict.** The owner is right. Ostler has a sound *skeleton*: W3C design tokens with a dark set,
layout classes, a status strip, honest status words (ADR-0008) and a mostly clean axe run. It has
no *visual system* on top of that. Every block is a bordered white or grey box of the same weight.
Buttons come in about a dozen styles. Type comes in 16 sizes. Icons are half Material Symbols and
half emoji. The map, the thing the owner loves in Speedometer, is a small light card that steals
the page's scroll. The head-unit Drive mode, the one screen that must be glanceable, scrolls at
every landscape size, including the spec's own 1024×600 design point.

## How this was made

- **Build and data.** The platform repo at `1d5161e` (2026-10-07), served from
  `src/openostler/web/static`. Data came from `tests/e2e_server.py --replay e2e/sniff-demo.txt`, a
  simulated car with the pack's demo logs. ADR-0011 allows this only in tests. Map tiles came from
  OpenFreeMap, and Figtree came from Google Fonts. A first pass without network fell back to
  system fonts, which is what an offline car shows (§P7).
- **Viewports.** Phone 390×844 (class `phone`) and tablet 1024×768 (detected as `hu9`, not
  `tablet`). HU 1024×600 is `hu7`, 1280×480 is `huwide` (aspect 2.67) and 800×480 is `hu7`. Each
  ran in light and dark (`prefers-color-scheme`), on every destination: Home, Diagnose (all five
  areas), Logs, live Analysis, a replayed session (map, G-G, chart, notes), More, Preferences,
  Drive mode, the fault sheet, and admin (More, Decode, Label, Docs). There is no Network page and
  no Security page in this build: Security needs a node device (`ui/src/shell/destinations.ts:52`).
- **Measurements.** axe-core 4.13 (WCAG 2.0/2.1/2.2 A and AA). In-page measurements covered each
  visible interactive box against 24, 44 and 76 px, the histogram of visible text sizes, and
  `main` scroll height against client height.
- **Screenshots.** 196 PNGs in the session scratchpad (`r9/shots/`, listed in `r9/SHOTS.txt`),
  named `<scheme>-<viewport>-<nn>-<page>.png`. They are not committed.
- **Reference.** The owner's two Speedometer screenshots. The full teardown is a sibling note
  (`app_teardown_speedometer.md`, in progress).

## What is already good (keep it)

| Strength | Where |
|---|---|
| W3C token files (colour light and dark, sizes per layout class), compiled to CSS variables, with a test | `ui/tokens/*.tokens.json`, `ui/tokens/tokens.ts:51-69`, `ui/src/shell/tokens.test.ts` |
| Layout classes by aspect and height, plus a kiosk override and a driver-side rail | `ui/src/shell/layoutClass.ts:31-60`, spec §3.1 |
| Status never relies on colour alone: an icon and a word, with ISO 2575 hues for telltales only | `ui/src/styles.css:14-22`, `ui/src/shell/shell.css:53-63` |
| Tabular numerals everywhere, and big values with small units | `ui/src/styles.css:42`, `:134` |
| Reduced motion respected, focus rings visible | `ui/src/shell/shell.css:67-70`, `ui/src/styles.css:237` |
| axe is clean on Home, Diagnose, Logs, More and Drive at every size and in both schemes | only 3 rule types fail, all on the replay screen (P13) |
| Gauges read well at head-unit size: 1.25 bar and 88 °C are legible at arm's length | `dark-hu1024x600-07-drive.png` |

## Top 15 problems, ranked by impact

Impact is how much each problem costs the owner's two goals: a UI that looks as good as
Speedometer, and a head unit that is safe at a glance. Fix order follows the rank.

### P1. Drive mode does not fit one screen on any head unit

At the spec's own design point, 1024×600 (`hu7`), `main` is 764 px tall in a 543 px viewport.
Only 3 of the 6 tiles show, and the **red Intake Air 120 °C HIGH tile is below the fold**. At
1280×480 it is 842 in 415, and at 800×480 it is 695 in 423. Above the tiles sit a 76 px Back
button, the "Drive · TD5 (engine)" heading and a full-width fault banner. Together they take
about 45 % of the height (`ui/src/shell/Shell.tsx:117-121`, `ui/src/shell/shell.css:118-124`).
The grid has a fixed number of columns, not rows sized to the height (`ui/src/styles.css:287`,
`ui/src/shell/shell.css:123`). Spec §3.1 promises "Drive mode 3×2 tiles" at HU-7, and §3.5
forbids scrolling content while Moving. On the phone, Drive mode is just Home without the Drive
button (`light-phone-07-drive.png` against `light-phone-01-home.png`), so it earns no
separate mode.

### P2. The map is a small light card, not the hero, and it traps scrolling

- **Size.** The map is boxed at `clamp(220px, 42vh, 420px)` (`ui/src/replay.css:92`), below a
  title, a back button, an Export button and a paragraph of prose. On a phone in replay it starts
  about 410 px down. At 1280×480 only about 60 px of it shows above the fold
  (`light-hu1280x480-05-session-replay.png`).
- **Theme.** The only street style is OpenFreeMap **Liberty**, a light and colourful style
  (`ui/src/components/replay/maplibre.ts:22`). In dark mode it is a bright beige-and-blue slab
  inside a near-black UI (`dark-phone-05-session-replay.png`). The offline fallback is hard-coded
  light grey `#eef0f2` (`maplibre.ts:35`, and again at `replay.css:92`). OpenFreeMap also serves
  `positron`, `dark` (background rgb 12,12,12) and `fiord` (checked by HTTP, 2026-10-07).
- **Overlays.** The basemap switch and the note label are hard-coded white
  (`ui/src/replay.css:96-119`).
- **Scroll trap.** There is no `cooperativeGestures` (`maplibre.ts:86-96`). Scrolling the page
  over the map zooms the map instead: in `light-tablet-052-…` the page did not move and the map
  zoomed out. On a phone, a one-finger drag over a 42 vh map pans the map, not the page.

Speedometer is the opposite on every point: a full-bleed dark map, a floating glass stat card and
a transport docked on the map.

### P3. No component system: about a dozen button styles and five "selected" looks

The button-like classes are `.btn` (48 px), `.iconbtn` (36), `.chip` (36), `.rchip` (36),
`.seg button` (36), `.area-tab` (`--target`), `.schip`, `.navitem`, `.opt`, `.morerow`,
`.sysrow`, `.connnotice-btn` (32) and `.replay-basemap-btn` (36). They live in
`ui/src/styles.css:54-108,186-205,316-318,413-417`, `ui/src/shell/shell.css:29-35,88-103,146-176`
and `ui/src/replay.css:29-35,113-119`.

"Selected" has five treatments:

- an inverse near-black slab (`.seg`, `.area-tab`, `styles.css:318`, `shell.css:162,168`)
- an accent fill (Preferences, `ui/src/components/Preferences.tsx:65,74`)
- an accent outline and text (`.rchip`, `replay.css:34`)
- an accent border (`.opt`, `styles.css:191`)
- a raised surface (`.navitem`, `shell.css:94`)

The inverse slabs are the loudest objects on Logs and Diagnose. In dark mode they turn into
near-white blocks (`dark-tablet-03-logs.png`). There are also two token vocabularies, the
"legacy aliases" `--fg`, `--bg-card` and `--ic-red` beside `--text-1`, `--surface` and `--alarm`
(`styles.css:27-36`). Components use either, so the same intent drifts.

### P4. Typography has no scale

The size tokens define `--type-primary` and `--type-secondary` per layout class
(`ui/tokens/size.tokens.json`), but only **one** rule uses them (`shell.css:129`). The CSS holds
**117 hard-coded `font-size` values across 16 sizes** from 9 px to 40 px. The commonest are 13 px
(28), 12 px (21) and 11 px (14). Home renders 13 distinct text sizes.

On head units the smallest visible text is **9 px**: gauge limits (`.g2 .lim`, `styles.css:302`)
and range-bar edges (`styles.css:279`). There are 10-11 px labels everywhere: `.kicker`,
`.stag`, `.status` and the strip sub-labels. Principle 4 of the UI spec asks for 32/24 px text
on head units. Body text is 14 px everywhere (`styles.css:41`), including the head unit.

### P5. Weak hierarchy: everything is a bordered card of equal weight

- **Titles.** Page titles are a 20 px `h2` with a 12 px grey "· subtitle" (`styles.css:67-69`,
  `ui/src/destinations/Home.tsx:27`). They often sit *below* the page's own controls: the
  Sessions/Analysis segment sits above "Logs" (`ui/src/destinations/LogsDestination.tsx:22`), and
  the module picker and area tabs sit above "Outputs".
- **No hero.** No screen has a single hero. Home's loudest element is a 64-76 px saturated-blue
  Drive slab (`shell.css:127-130`). Logs' loudest are the black segment and an emoji ⏪ Rewind
  button.
- **Flat surfaces.** Cards, rows, tiles, readouts and sheets all use the same 1 px border and the
  same radius (10-12 px). There is no elevation and no grouping by surface tone.

Speedometer gives each screen one big number (186 km/h, 15K $), then a quiet stat grid.

### P6. Post-trip analysis has no summary

A replayed session opens on a title, a prose description, the map, values at the cursor, a G-G
plot, a three-lane chart and notes (`ui/src/components/replay/AnalysisView.tsx:161-194`). The
following are all missing:

- a trip stat grid: distance, duration, moving and idle time, average and max speed, stops,
  elevation
- time-at-speed
- speed distribution
- records

These are exactly the Speedometer screens the owner singled out. The session list shows only
duration, distance and module. The year heatmap is the only overview, with 10 px cells.

### P7. The web font comes from Google at runtime

`@import url("https://fonts.googleapis.com/…Figtree…")` (`ui/src/styles.css:11`) causes three
problems:

- **Offline.** In the garage or on a head unit with no data connection, the UI falls back to
  system sans, so the product looks different from the screenshots. Our first, network-less pass
  rendered in the fallback.
- **Privacy.** Every load sends the user's IP address to Google, against the privacy-first stance.
- **Speed.** It is a render-blocking cross-origin request on a slow link.

Figtree is OFL-licensed and can ship in the bundle.

### P8. Mixed icon language

Navigation and the strip use Material Symbols SVGs (`ui/src/icons/Icon.tsx`). Elsewhere the UI
uses Unicode and emoji glyphs:

- ⏪ ⏩ ▶ ❚❚ in the replay transport (`ui/src/components/replay/Transport.tsx:61-65`)
- ⚑ Mark and ⚙ Options (`ui/src/components/RecordingCard.tsx:143-149`)
- ⏪ Rewind (`ui/src/components/RewindButton.tsx`)
- ✓ ! … in the health line (`ui/src/components/HealthStrip.tsx:9`)
- ▾ ▸ ‹ in pickers and back links
- ⚠ in the fault sheet title

⏪ renders as an **orange colour emoji** (`light-hu800x480-03-logs.png`). The glyphs also differ
in weight and baseline between platforms.

### P9. Head-unit space is badly used

- **Home at 1280×480 (`huwide`).** The 520 px vehicle pane holds the tiles. Main holds a
  "Home" heading, the Drive slab and one "Last trip" card, and is about 60 % empty
  (`dark-hu1280x480-01-home.png`).
- **Replay at 1280×480.** The strip, the amber replay frame and the transport leave **315 px**
  of the 480 px height for content (measured).
- **Diagnose on tablet.** The 380 px "Systems" list holds two rows beside a long scrolling
  detail (`dark-tablet-021-diagnose-inputs.png`, `shell.css:142-143`).
- **Tablet class.** A 1024×768 iPad-sized tablet is classed `hu9` (head unit), not `tablet`,
  so it gets head-unit density with nothing gained.
- **800×480.** Common on cheap Android head units, but not a class in spec §3.1. It falls into
  `hu7`, sized for 1024×600.

### P10. Dark mode is only half themed

The token pipeline themes the shell. Several things sit outside it:

- chart series and the chart note colours (`ui/src/replay.css:12-26`)
- canvas fallbacks (`ui/src/components/replay/Chart.tsx:93-135`)
- map overlays and the cursor (`replay.css:92-119`)
- the map style (P2)

The dark surfaces are too close together. `--bg` is #0e1012 and `--surface` is #16191c (about
1.1:1), so cards separate only by 1 px #262b30 borders. The result reads as grey-on-grey, not the
"glowing card on deep navy" depth of Speedometer. Head units also have no deeper night setting
(an OLED-black option, or dimmed accents after dusk). The Display preference is only
Auto/Day/Night.

### P11. One fault, three designs

The same fault appears in three forms:

- **Health line.** A red banner with a ! disc (`ui/src/styles.css:240-252`).
- **Diagnose cards.** A circle icon, a 16 px title, a mono code chip and a word
  (`styles.css:361-368`).
- **Fault sheet.** A left colour bar, a code, then a coloured "Logged Low" or "Current" chip
  (`dark-phone-11-fault-sheet.png`).

Fault titles are lower case ("air flow circuit"), while every other label is sentence or title
case. The sheet title uses ⚠ instead of the Material icon.

### P12. Visual vocabulary contradicts itself

The dashed border is documented as "placeholder, never a value" (`ui/src/styles.css:449-453`,
`.status.exp`, `.stag.untranscribed`), but the replay readouts that *are* values use it too
(`ui/src/replay.css:166-169`). Unexplained "◆" badges sit on the Fuel tiles. The pack shows fuel
in "L/mil" (`ostler-pack-lr-d2/src/d2diag/layout.json:46,53`) on a UK car with an mph
preference, and the unit clips to "L/mil" at phone width.

### P13. Small targets where it matters

| Element | Size | Rule |
|---|---|---|
| Note and flag ticks on the replay scrubber | 4×8 px (axe `target-size`, serious, every size) | `styles.css:519-525` (the `::after` pad does not count) |
| Inputs "About" (i) buttons | 27×23 px | `.infobtn`, `styles.css:135` |
| "Recording now, N min — open" link | 20 px tall | Logs |
| Year heatmap day cells | 10×10 px (excluded in our e2e axe run) | `replay.css:254` |
| Replay speed chips, transport | 36 px, also on head units | `.rchip`, `replay.css:30` |
| Logs at 800×480 (`hu7`) | 14 of 22 interactive elements under 76 px (20 of 29 at 1024×768) | UI spec §2 principle 4 asks 76 px |

axe also flags **color-contrast** on the active 1× speed chip in light mode (4.44:1, accent on
`--raised`). On huwide it flags `scrollable-region-focusable` on the vehicle pane `aside`.

### P14. Colour is spent on the wrong things

The "calm instrument" rule says neutral when healthy. Yet every gauge arc is saturated accent
blue all the time (`.g2 .val`, `styles.css:297`). Accent also marks the Drive button, the
selected nav icon, links, Preferences choices, the heatmap and chart series 1. So nothing stands
out, and the one colour Speedometer uses for emphasis (its cyan) is spread thin here.

Speed is encoded with the plasma ramp on the map (`ui/src/components/replay/trace.ts:70`) but as
blue `--series-1` in the chart (`replay.css:13`). The same channel gets two encodings on one
screen. On the light Liberty map, plasma's yellow end (the high-speed half of the trip) has poor
contrast against the beige land.

### P15. Empty and thin states are bare

- **Outputs and Utilities.** One centred grey sentence ("Nothing verified here yet — switch to
  Experimental…"), with no icon and no button for the action it names
  (`dark-hu800x480-022-diagnose-outputs.png`).
- **More.** Two rows on an otherwise empty page.
- **Accelerator pedal and Air flow.** "—" with an empty range bar.

These are honest (spec §2.3) but read as broken.

## Side by side with Speedometer

| Aspect | Speedometer (owner's screenshots) | Ostler today |
|---|---|---|
| Canvas | Deep navy with a soft radial glow, always dark | Light grey by default (follows the OS), dark is grey on grey |
| Accent | One cyan-to-blue family; status colours only in charts | Blue everywhere, plus red, amber and green status, plus plasma, plus 3 chart hues |
| Hero | One huge number per screen (186 km/h), with a small unit and a caption | None. A 20 px title, then equal cards |
| Stats | 3-column grids of tiny caps labels over 15-17 px values, no borders | Bordered cards, each with its own label style |
| Map | Full-bleed, dark-tinted satellite or street, glass card over it, transport on the map | A 42 vh light card in a scrolling page, transport outside it |
| Charts | Donut (time at speed), bars (speed distribution), area line (speed over time) | Line lanes, G-G scatter, heatmap. No distribution or time-at-speed |
| Nav | Five-icon bottom bar with a pill highlight | Bottom bar or rail with a bordered selected box. Fine, but heavier |
| Icons | One line-icon family | Material Symbols plus emoji |
| Records | Sprint 0-60/80/100 lists with medals | None |

What Speedometer does *not* have, and we should not lose: honest states (stale, candidate,
untranscribed), ISO telltales, head-unit target sizes and a driver-side rail. Its look sits on
top of a far simpler data model.

## Copy / Avoid / Decide for Ostler

**Copy**

1. **One hero number per screen, then a quiet borderless stat grid.** Caps labels at 11-12 px,
   values at 17-20 px, the unit at 60 % size. This goes in UI spec §5.4 (Home from roles) and in
   the Trips Analysis header (ADR-0009).
2. **A full-bleed, theme-matched map with a floating stat card and the transport docked on the
   map.** Use OpenFreeMap `positron` or `dark` per theme (ADR-0009), with `cooperativeGestures`
   on scrolling pages (UI spec §3.4 Logs/Trips).
3. **Trip summary, time-at-speed (donut or stacked bar), speed distribution (bars) and
   records.** These belong in the core Trips Analysis (ADR-0009 and ADR-0010 replay). Encode
   speed with **one** ramp on map, chart and legend alike.
4. **Depth by surface tone, not borders.** Dark: three or four steps from about #0b0f14 to
   #1b2430 with a faint inner highlight. Light: white cards on #eceef1 with no borders. Applies
   to the `ui/tokens/color*.tokens.json` sets (ADR-0018).
5. **A single icon family.** Material Symbols is already vendored (`ui/src/icons/`). Add the
   transport, flag, gear and rewind glyphs to it.

**Avoid**

1. Saturated full-width CTA slabs (the Drive button) as the loudest thing on Home. Drive mode
   opens automatically when Moving on head units anyway (UI spec §3.5).
2. Inverse black or white segment slabs for "selected" (P3).
3. Raw `font-size`, hex colours and `style={{}}` in components. There are 117 raw font sizes,
   more than 40 raw colours and 129 inline styles today. Enforce with stylelint and an ESLint
   rule in CI (ADR-0004 tooling).
4. Prose before data on Analysis. Move the description into a collapsible "About this trip".
5. Copying Speedometer's always-on gradients and glow on head units. At night they reduce
   contrast and add glare. Keep its depth, not its decoration.
6. Runtime third-party fetches for styling. Fonts, map glyphs and sprites should be bundled or
   cached for offline use (P7).

**Decide** (recommendations for the owner to approve)

- **D1. Night-first on head units.** Head-unit classes and Drive mode default to dark whatever
  the OS says, and phones keep following the OS. Add a "Night (deep)" OLED variant.
  *Recommend: yes.* Goes in UI spec §2 principle 7 and §3.5.
- **D2. Map styles.** Streets = OpenFreeMap `positron` (light) or `dark` (dark), switched with the
  theme. Liberty becomes an optional "Detailed" basemap. The offline fallback takes `--bg`, not
  `#eef0f2`. Analysis is map-first: about 55 % of the height on the phone, a left half on
  landscape, with a glass stat card. *Recommend: yes.* Amend ADR-0009 and the session-logbook
  spec.
- **D3. Self-host the font.** Bundle Figtree (OFL, variable weight) or switch to Inter, and drop
  the Google Fonts `@import`. *Recommend: bundle Figtree, about 40 KB woff2 for the Latin subset.*
  Goes in ADR-0018 and `THIRD_PARTY_LICENSES.md`.
- **D4. Type scale as tokens, enforced.** Six steps per layout class (caption, label, body, title,
  value, hero) in `ui/tokens/size.tokens.json`, with a minimum of 12 px on phone and 16 px on
  head units, and a stylelint rule that rejects raw sizes and colours. *Recommend: yes.* Goes in
  ADR-0018 and UI spec §2 principle 4.
- **D5. One component kit.** Button (primary, secondary, ghost, danger; height bound to
  `--target`), Segmented, Chip, ListRow, Card, StatTile, Sheet. Retire `.rchip`, `.iconbtn`,
  `.chip` and the legacy `--fg`/`--bg-*` aliases. One selected style: an accent-tinted fill with
  accent text. *Recommend: yes, before any add-on authoring starts, so add-ons inherit it* (app
  model spec, slots).
- **D6. Drive mode fits one screen, always.** No page heading, the Back button moves into the
  strip, the fault banner folds into the telltale chip, and rows are sized by height
  (`grid-auto-rows: 1fr` over the remaining height). Add **HU-5 (800×480)** to UI spec §3.1, and
  add a Playwright assert that `main` does not scroll in Drive mode at every head-unit class.
  *Recommend: yes, as the first fix.*
- **D7. Calm gauges.** Neutral arcs (`--text-2`) when in range, amber or red only out of range,
  and accent kept for interactive elements. *Recommend: yes.* This is UI spec §2 principle 7
  applied literally.

## Sources

- Live app screenshots, axe-core 4.13.0 and in-page measurements: the platform at `1d5161e`,
  `tests/e2e_server.py` replay, run 2026-10-07. MapLibre GL 6.12.0 is in `ui/node_modules`.
- OpenFreeMap style endpoints `liberty`, `bright`, `positron`, `dark` and `fiord` all answered
  HTTP 200, with `dark` background rgb(12,12,12) (tiles.openfreemap.org, checked 2026-10-07).
- Speedometer: Driving Tracker, App Store id6759611784. Two store screenshots supplied by the
  owner (layout, colour and chart types read from them). Not independently re-verified here.
- Spec numbers: [UI architecture spec](../../specs/2026-10-06-ui-architecture-design.md) §2,
  §3.1, §3.5. Head-unit numbers: [head_unit_ui.md](ui/head_unit_ui.md). App landscape:
  [obd_apps.md](ui/obd_apps.md).
