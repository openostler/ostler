---
title: "Shell UI kit, 12 October 2026 — the designer's tokens, component renderers, component catalogue and the 114 shell frames with answers to the brief's open questions"
area: references
status: draft
version: 0.1
updated: 2026-10-12
depends_on: [references/design/2026-10/brief/10-shell-brief.md, specs/2026-10-11-ostler-shell-design.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md]
summary: >
  The designer's answer to the shell brief (10-shell-brief v1.0), saved as delivered less the design tool's runtime (support.js): tokens.json (Night and Day palettes, locked caution and warning colours, size-class thresholds, strip heights, moving rules, rings, presets, warning takeover order, fonts Figtree and Material Symbols Rounded), ostler-shell-ui.js (static HTML renderers for every shell part, as an ES module and a classic script), Components.dc.html (the catalogue) and frames/ (all 114 frames A-01 to D-25, two files per section, each ending with the designer's proposals for its open questions). The proposals are adopted in the shell spec §18. The build of @openostler/shell works from this kit.
---

# Shell UI kit, 12 October 2026

The designer's shell UI kit, built from the [shell designer brief](../brief/10-shell-brief.md).
The `.dc.html` files need the design tool's `support.js` beside them to open; it is not kept in
the repo. The designer's proposals for the open questions are adopted in the
[shell spec](../../../../specs/2026-10-11-ostler-shell-design.md) §18.

**Proposed changes (ADR-0052 v0.6, pending the owner):** the divider bars and snap guides
(A-section frames on dividers and snapping) and the strip's layout dropdown and Manage layouts
sheet (B-section switcher frames) would be replaced by edit mode and a layout carousel; a
designer brief addendum will cover the new frames.

The designer's README follows, as delivered.

## Ostler shell UI kit

The shell's shared parts as a component kit, from the shell designer brief v1.0. Every one of the 114 frames is built from these.

## Files
- `Components.dc.html`: visual catalogue of every component, Night and Day. Open in a browser (keep `support.js` beside it).
- `ostler-shell-ui.js`: ES module. `ostler-shell-ui.classic.js`: same, as `window.OstlerShellUI`.
- `tokens.json`: palettes, locked safety colours, size-class thresholds, strip heights, moving rules, rings, presets, warning takeover order.
- `frames/`: the 114 frames (A–D, two parts each) with open-question proposals. Start at `Ostler Shell Frames.dc.html`.

## API (all return HTML strings with inline styles)
| Function | What it draws | Key options |
|---|---|---|
| `cls(w,h)` | Size class from a tile's own box | returns `B`, `Ch`, `C`, `S`, `E` |
| `tile(p,o)` | A tile with its label, nav row and page | `x,y,w,h,pg`, `mv`, `focus`, `caution`, `warn`, `stale`, `loading`, `fail`, `link`, `drag`, `show`, `cls` |
| `strip(p,o)` | Top strip | `w,h,y`, `mv`, `rhd`, `narrow`, `layout`, `conn` (`live/brain/conn/seen/browser/none`), `car`, `view`, `alert:{lvl:'c'|'w',acked,n}`, `unknown` |
| `preset(name,A,rhd,n)` | Tile rectangles for a layout | presets in tokens.json |
| `dividers(p,R,o)` | Drag handles between tiles | `locked`, `drag` |
| `softkeys(p,o)` | Soft-key row for the focused tile | `owner`, `keys:[{i,l,dis}]`, `overlay`, `iconOnly` |
| `banner(p,o)` | Banner under the strip | `i,t,a,lvl` |
| `menu(p,o)` / `sheet(p,o)` | Popover menu / sheet | `items:[{i,l,d,dis,on,focus,sep,head}]` |
| `act(p,o)` | Action permission states | `s: ok/confirm/no`, `why` |
| `tv(p,o)` | Value with trust level | `s: live/est/stale/na` |
| `scr(p,o)` | A whole screen: strip, tiles, dividers, soft keys, overlays | `w,h,phone,layout,pages,t,sk,banner,over` |

`p` is a palette: `PAL.n` (Night) or `PAL.d` (Day). Pages live in `PG`; each has an app, a name, a summary for Chip/Badge, and a renderer for C/S/E.

## Rules baked in
- Size comes from the tile, never the device; lower-priority rows drop whole, never squeezed.
- Moving: 24 px minimum text, 52 px label row, editing locked, Compact labels become icons.
- Strip: no clock; alert pill and settings button never shrink; other chips ellipsize.
- Caution: amber ring + icon. Warning: red takeover in the brief's order, or a band.
