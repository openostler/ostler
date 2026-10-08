# Claude Design bundle: Ostler Screens Mobile Design (2026-10-07)

The export of the owner's Claude Design project "Ostler Screens Mobile Design", saved
as delivered (less the files listed under "Changes on import") so the builder can work from it.

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

## Where the design conversation landed

- The 22 themes, built in four rounds, become the project's design-language themes. Night
  stays the default.
- Themes can change anything, with custom CSS written against the documented `data-part`
  hooks. No tokens are locked.
- Themes look the same Parked and Moving. There is no Moving-safe variant; the Moving
  content rules still apply.
- Textures are image assets in the pack. The prototypes' CSS gradients are placeholders.
- The background belongs to the user, not the theme.
- The approved engine is the
  [theme engine spec](../../../../specs/2026-10-07-theme-engine-design.md): `ostler.skin/1`
  with six layers, separate packs (OS skin, widgets, icons, wallpapers, sounds) and theme
  options.
- Safety is carried by protected surfaces, required parts and the Drive-mode render check
  (engine spec decisions 5–7).
- The build order is the engine spec's phases TE1–TE6.

## Read first

1. `project/Ostler Themes.dc.html`, then what it imports: `project/ostler-themes.js`,
   `project/TH *.dc.html`, and `project/drive-maps.js` where it is used.
2. The [theme engine spec](../../../../specs/2026-10-07-theme-engine-design.md).

## What else is in `project/`

Other canvases from the same session, kept for reference. They are not in this build's scope:

| Canvas | Component files | Content |
|---|---|---|
| `Ostler Screens.dc.html` | none | First screens: Home, Drive, Trips, Trip detail |
| `Ostler Drive Modes.dc.html` | `DM *.dc.html`, `Drive Strip.dc.html` | Seven Drive modes, switcher, editor, edit mode, message alerts |
| `Ostler Platform.dc.html` | `OS *.dc.html` | Edit and remote, messages, Phone & Comms, sharing, Navigation, adapters |
| `Ostler Market and Customise.dc.html` | `OS Market`, `OS Customise`, `OS Themes` | Add-ons market, full customisation, themes (now the Wallpaper & style wizard) |
| `OS Frame.dc.html` and `os-tokens.js` | none | Wave 1-2 launcher frames (unfinished: the designer stopped at a usage limit) |

`Ostler.dc.html`, `Theme Screen.dc.html` and `OS Test.dc.html` are stubs or scratch files.

## Opening the prototypes

`*.dc.html` files are Claude Design documents. They ran on the design tool's own runtime,
which is not redistributed here, so they are reference source only: read the HTML, CSS and
JS directly.

## Changes on import

- The design conversation transcript, the design tool's own README and its runtime
  (`support.js`) are not included. "Where the design conversation landed" above records
  the outcome.
- The owner's uploads are not included: copies of repo docs, and a mood image for the Air
  theme (a third-party phone mockup with photos of people) that this repo has no licence to
  publish.
