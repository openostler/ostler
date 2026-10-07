# Claude Design bundle: Ostler Screens Mobile Design (2026-10-07)

The full export of the owner's Claude Design project "Ostler Screens Mobile Design", saved
as delivered so the builder can work from it.

**Owner, 2026-10-07: this bundle is the latest iteration, and its themes become the
project's design-language themes.** Where older design references in this repo differ (for
example the single Night/Day/Night dim/Deep night theme set in the visual design system
spec), this bundle is the newer direction. The owner approved the matching amendment the
same day:
[visual design system spec §13](../../../../specs/2026-10-07-visual-design-system-design.md).
Read it before building. **It overrides parts of the prototype:**

- **Any CSS.** Themes can change anything, with custom CSS written against documented
  `data-part` hooks. No tokens are locked.
- **Same while Moving.** Themes look the same Parked and Moving. There is no Moving-safe
  variant, so ignore the prototype's `*Safe` values and the `moving` option of `resolve`.
- **Images for textures.** Walnut, leather, carbon and similar are image assets in the theme
  pack. The prototype's CSS gradients are placeholders.
- **Backgrounds.** Users can set their own background images.

The Moving *content* rules (templates, ≤ 6 tiles, no text entry, no message text) still
apply. The research behind the amendment is
[deep theming](../../../research/deep_theming.md).

These are HTML/CSS/JS **prototypes**, not production code. Rebuild them in `ui/`.

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
- **The 22 themes.** Originals (rebuilt in round 4): Night, Heritage, Expedition, Glass,
  Minimal, Race, Deep night, High contrast. Round 2: Air, Ledger, Tide, Lunar, Tactile.
  Round 3: Slab, Prism, Paper, Soft, Bakelite, Clay, Tonal, Clarity, Blueprint.
- **Demo screens** each theme is drawn on:
  - `TH Home`, `TH Trip`, `TH Diagnose` and `TH Picker` at HU-7 and phone;
  - `TH Drive` at HU-7, HU-5 and phone. The prototype draws a Moving-safe frame plus a
    Parked frame for the themes in `DIFF`; build the Parked look for all of them (§13.3).
  - `TH Sheet`, the theme sheet: swatches, contrast ratios computed by
    `OstlerThemes.contrast`, fonts and licences, settings.

The transcript said the next step was a visual-design-system amendment and a theme schema.
That amendment is now §13 of the spec, with build order T1–T5 and the open decisions D1–D3.

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
