# Claude Design bundle: Ostler Screens Mobile Design (2026-10-07)

The full export of the owner's Claude Design project "Ostler Screens Mobile Design", saved
as delivered so the builder can work from it.

**Owner, 2026-10-07: this bundle is the latest iteration, and its themes become the
project's design-language themes.** Where older design references in this repo differ (for
example the single Night/Day/Night dim/Deep night theme set in the visual design system
spec), this bundle is the newer direction. The owner approved the matching amendment the
same day:
[visual design system spec §13](../../../../specs/2026-10-07-visual-design-system-design.md)
covers the theme schema, the locked tokens, the Moving-safe variant, image textures, user
backgrounds, fonts and the build order T1–T4. Textures such as walnut, leather and carbon are
image assets in the theme pack; the CSS gradients in the prototypes are placeholders. Safety rules never relax by
themselves: UI §12.1, §14, Drive modes §8.1 and the visual spec's glow and type floors still
apply.

These are HTML/CSS/JS **prototypes**, not production code. Rebuild them in `ui/` on the
tokens.

## Build target

**Primary design: `project/Ostler Themes.dc.html`**, the
theme engine exploration. The owner chose this scope on 2026-10-07: **the engine and all 22 themes**.

- **Theme token schema.** It covers palette, accent, secondary, speed ramp, radius, type
  (body, heading and numeral fonts, numeral weight), glow, blur and transparency, borders,
  texture, gauge and sweep style, and map filter. The source is `project/ostler-themes.js`:
  the first block is the base list, and later blocks layer the structural options and the
  round 4 rebuild of the originals on top. The values that apply are the merged result
  (`OstlerThemes.resolve`).
- **Structural options per theme** (`sheetOf` / `SH` / `SX` in `ostler-themes.js`):
  - card, chip and tile corners;
  - label style (`LBL`);
  - heading size, weight, case and tracking;
  - numeral italic and tracking;
  - Home layout (`LAY`: grid, mapL, center, stack, stackMap);
  - rail style (`RAIL`), strip style (`STRIP`), speed-hero plate (`HERO`) and gap.
- **Locked for safety (every theme).** Status colours and words, the fault telltale and
  alarm look, the Moving limits and the minimum sizes. Light themes switch to the darker
  status-text tones (#1f7a4b / #8a6110 / #c0283f) for words on light backgrounds; filled
  chips are unchanged.
- **Automatic Moving-safe variant** (`resolve(id, {moving: true})`):
  - no blur, glow or texture;
  - the `*Safe` opaque surfaces replace translucent ones;
  - the numeral weight is lifted to at least 500.
- **The 22 themes.** Originals (rebuilt in round 4): Night, Heritage, Expedition, Glass,
  Minimal, Race, Deep night, High contrast. Round 2: Air, Ledger, Tide, Lunar, Tactile.
  Round 3: Slab, Prism, Paper, Soft, Bakelite, Clay, Tonal, Clarity, Blueprint.
- **Demo screens** each theme is drawn on:
  - `TH Home`, `TH Trip`, `TH Diagnose` and `TH Picker` at HU-7 and phone;
  - `TH Drive` at HU-7, HU-5 and phone, Moving, plus HU-7 Parked for the themes in `DIFF`;
  - `TH Sheet`, the theme sheet: swatches, contrast ratios computed by
    `OstlerThemes.contrast`, fonts and licences, settings.

What the transcript says the next step is: a visual-design-system amendment and a theme
schema for the owner's approval (which tokens stay locked, the automatic Moving-safe variant,
theme files shared on Ostler Community, and the decisions on user accent colours and on glow
and transparency on head units).

## Read first

1. [`chats/chat1.md`](chats/chat1.md): the whole conversation with the designer. Theme
   work starts at "Ostler is 'the automotive version of Home Assistant'…" (the eight-theme
   brief) and runs to round 4 ("now do that to the original themes").
2. `project/Ostler Themes.dc.html`, then what it imports: `project/ostler-themes.js`,
   `project/TH *.dc.html`, and `project/drive-maps.js` where it is used.
3. [`HANDOFF.txt`](HANDOFF.txt): Claude Design's own README for coding agents, kept as
   delivered.

## What else is in `project/`

Other canvases from the same session, kept for reference. They are not in this build's scope:

| Canvas | Component files | Content |
|---|---|---|
| `Ostler Screens.dc.html` | none | First screens: Home, Drive, Trips, Trip detail |
| `Ostler Drive Modes.dc.html` | `DM *.dc.html`, `Drive Strip.dc.html` | Seven Drive modes, switcher, editor, edit mode, message alerts |
| `Ostler Platform.dc.html` | `OS *.dc.html` | Edit and remote, messages, Phone & Comms, sharing, Navigation, adapters |
| `Ostler Market and Customise.dc.html` | `OS Market`, `OS Customise`, `OS Themes` | Add-ons market, full customisation, themes in Preferences |
| `OS Frame.dc.html` and `os-tokens.js` | none | Wave 1-2 launcher frames (unfinished: the designer stopped at a usage limit) |

`Ostler.dc.html`, `Theme Screen.dc.html` and `OS Test.dc.html` are stubs or scratch files.

## Opening the prototypes

`*.dc.html` files are Claude Design documents. `project/support.js` is the Claude Design
runtime (generated; React from the page). Serve `project/` over HTTP (for example
`python3 -m http.server`) and open a `.dc.html` file. Fonts load from Google Fonts and map
tiles from public services, so a browser offline shows fallbacks.

## Changes on import

- Frontmatter added to `chats/chat1.md` and the two `project/uploads/*.md` files so the
  docs validator accepts them. The bodies are unchanged.
- `project/uploads/pasted-1791409253531-0.png` is **not included**. It is the owner's mood
  reference for the Air theme: a third-party phone mockup with photos of people, which
  this repo has no licence to publish.
- Claude Design's own README is saved as `HANDOFF.txt`, so that this file can be the
  folder's README.
