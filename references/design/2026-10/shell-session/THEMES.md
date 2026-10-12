---
title: "Themes and the shell — how the designer's Themes v2 plugs in, what a theme may and may never change (13 October 2026)"
area: references
status: stable
version: 1.0
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/IMPLEMENTATION.md, references/design/2026-10/shell-session/README.md]
summary: >
  The designer's theme integration notes, saved as delivered with frontmatter added: the 22 themes in themes/ostler-themes.js (resolve(id, {moving})) and the visual reference; what a theme may change; what it may never change (locked safety colours and sizes); the moving variant; per-theme user customisation saved by the Gateway; custom CSS themes; window style and themes.
---

# Themes: how they plug into the shell

Files:
- `themes/Ostler Themes v2.dc.html`: the visual reference. It shows each theme by day and by night, including the mission themes (Military, Naval, Jet, Spy), Adventure and Knight Rider.
- `themes/ostler-themes.js`: the data for 22 themes, the source of truth. Use `OstlerThemes.resolve(id, {moving})`.

## 1. What a theme may change
A theme **overrides the colour and shape tokens** in `ostler-shell-tokens.json`, and nothing else.

| Theme field (ostler-themes.js) | Maps to token |
|---|---|
| `bg`, `bgImg` | `color.bg`, plus the wallpaper behind tiles |
| `s1`, `s2`, `s3` (and the `*Safe` versions) | `surface1/2/3` (the Safe versions are used while moving) |
| `tx`, `t2` | `text`, `text2` |
| `acc`, `on` | `accent`, `onAccent` (and `focus` on dark themes) |
| `r` | `shape.tile.theme` (Rounder = r+8, Square = max(r−12, 4)) |
| `border` | the tile edge / bevel (`box-shadow`) |
| `glow`, `tglow`, `blur`, `tex` | effects, **all off while moving** |
| `font`, `head`, `num`, `wN` | the type families and number weight (the type scale in dp stays the same) |
| `gauge`, `sweep`, `map`, `mapF` | hints passed to apps through the page context (apps choose whether to use them) |
| `hu`, `huNote` | recommended use, e.g. `day`, `night` or `safe` (head unit gets the opaque version) |

## 2. What a theme may never change
- **Caution and warning colours** (`caution`, `cautionText`, `warningText`, `warningFill`), plus the takeover and band.
- **The size-class thresholds, the 24 dp moving minimum and touch targets.**
- **The focus ring's visibility:** its width and gap are fixed; only its colour follows `focus`.
- **Safety icons:** warning, error and ACK.
- **Alert layering:** alerts always draw on top.

## 3. While moving (`resolve(id,{moving:true})`)
- `*Safe` surfaces replace translucent ones, and `blur`, `glow` and `tex` are cleared.
- Transparent **instrument** tiles render solid on `surface1`.
- Wallpaper stays only behind non-instrument tiles; behind instrument tiles it's plain `bg`.
- A minimum number weight of 500 applies (Minimal lifts from 300).

## 4. User customisation (per theme, saved by the Gateway)
- **Accent:** chosen from the theme's validated set; anything under 3:1 against `surface1` is hidden.
- **Wallpaper:** the theme's own, plain, or your own photo. Photos stay on the device only.
- **Corners:** Theme, Rounder or Square.
- **Effects:** glow, blur and texture, each switchable.
- **Font:** the theme's font, or Atkinson Hyperlegible.
- **Icon pack:** Rounded, Outlined or Sharp. Safety icons never change.
- **Day/night pairing:** for example Paper by day and Night after dusk, switched by light sensor or time.

## 5. Custom CSS themes (advanced)
- **Format:** a theme file is a set of CSS custom properties that map one-to-one onto the token names, plus an optional `wallpaper` image.
- **Import:** imports are checked for:
  - 4.5:1 contrast for text against each surface, and 3:1 for the accent;
  - minimum type sizes;
  - the locked tokens, which are rejected if present.
- **Export:** gives the same format, so themes can be shared.

## 6. Window style and themes
- **Transparent** shows the wallpaper through `surface1` at 55% (the theme may lower this to 40%).
- **None (widget)** draws no tile surface at all; the app's content sits straight on the wallpaper.
- Both obey the rules for moving above.
