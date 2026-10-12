---
title: "Designer hand-off doc — proposed ADR: Ostler is an MFD, one shell, tiled pages, no drive modes (as received, 2026-10-11)"
area: references
status: draft
version: 1.0
updated: 2026-10-11
depends_on: [references/design/2026-10/mfd/REVIEW.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md]
summary: >
  The designer's proposed ADR from the MFD hand-off of 2026-10-11, kept as received for reference (frontmatter added on import). The MFD of tiles, the ostler-shell library, the Gateway as the only app that talks to the car, driving as shell rules (22 px floor), tiling and window rules, four page sizes, aviation-style warnings, shell elements, twelve themes with day and night versions, and a build order. Not a decision of this repo: ADR-0052 is authoritative; differences are listed in the hand-off review (REVIEW.md in the parent folder).
---

# ADR (proposed): Ostler is an MFD: one shell, tiled pages, no drive modes

Status: proposed · 11 Oct 2026
Relates to: ADR-0049 (not an OS), ADR-0051 (one server per car), ADR-proposed-adaptive-page-sizes
Reference designs: `Ostler MFD v2.dc.html`, `Ostler Tiling v2.dc.html`, `Ostler Core.dc.html`, `Ostler Core Sizes.dc.html`, `Ostler Gateway.dc.html`, `Ostler Themes v2.dc.html`

## Context
Ostler is a set of separate apps: Gateway, Diagnose, Logs, Security, Maintenance, Convoy and others. Each must work on its own as a PWA, and all of them must work well together on a head unit, a phone or a tablet. Earlier designs had a separate "drive mode" shell with its own dashboards, which meant building and maintaining two shells.

## Decision
1. **The screen is a multi-function display (MFD), modelled on aircraft displays.**
   - The screen is a layout of tiles; each tile shows one page from any installed app.
   - Car instruments (speed, attitude, heading, transfer, engine) are ordinary pages.
   - There are no drive modes. "Off-road" or "Commute" is simply a saved layout, and layouts can switch automatically: when the car starts, when low range engages, or when parked.
2. **ostler-shell is a separate library repo that every app bundles.**
   - It holds:
     - the tiling engine;
     - the window rules;
     - size snapping;
     - the page contract;
     - the moving rules;
     - the theme resolver;
     - the apps menu;
     - the layout format.
   - It holds no settings screens, no car logic and no connection code.
   - It is minimal: not a launcher.
3. **The Gateway is the only app that talks to the car.**
   - Every other app talks only to the Gateway and owns only its own screen state and layout.
4. **Driving is a rule the shell applies, not a separate shell.** While the car is moving:
   - Dividers and layout editing are locked. Saved layouts and page swaps are still one tap.
   - Text is never smaller than 22 px, and touch targets are larger.
   - Pages that need a closer look wait until the car is parked.
   - Blur, glow and textures switch off.

## Tiling
- **Layouts:**
  - Full, Halves, Two thirds, Main + two, Three columns, Quad.
  - At most 2 tiles on a 5″ screen, 3 on 7″ and 4 on a tablet.
- **Dividers:**
  - Drag to resize; they snap to ⅓, ½ and ⅔.
  - Double-tap a divider to swap the two sides.
  - Dragging a tile below its minimum size closes it, with Undo.
- **Moving and opening tiles:**
  - Drag a tile's label onto another tile to swap them, or onto a screen edge to split.
  - Press and hold an item and choose "Open beside". The new tile opens on the passenger side, already linked to the first.
- **Linked tiles share a cursor.** Picking a fault in Diagnose moves Logs to that moment.
- **One level only:** tiles never nest inside tiles.
- **Driver side comes from the car:** right-hand-drive cars mirror the whole layout.
- **Window rules, applied in order:**
  1. Shape: a tall window splits top and bottom; a short window puts tiles in one row.
  2. Size: each tile picks a page size from its own space.
  3. Overflow: if tiles would be too small, the main page keeps the space and the others become chips.
- **Ostler sits alongside other Android apps.** Android split screen just gives Ostler a smaller window, and the same rules apply.

## Page sizes
Every page is designed at four sizes:
- **Chip:** icon, name and one value.
- **Compact:** the most important item and its next step.
- **Standard:** the normal design.
- **Expanded:** Standard plus extra parts, e.g. freeze-frame and live values in Diagnose.

The size comes from the tile's actual space, never from the device type. Content is added at bigger sizes; it is never squeezed to fit. See `ADR-proposed-adaptive-page-sizes.md`.

## Warnings (from aviation, kept restrained)
- **Colour is used only for state.**
- **Caution (amber):** rings the tile the problem is about, lights the strip, and plays a chime.
- **Warning (red):**
  - Takes over one passenger-side tile until the driver presses ACK.
  - Never covers a Drive page; if the tile it would use is only a chip, it opens as a band across the bottom or side instead.
  - The WARNING label stays in the strip until the problem clears.
- No green-on-black text, no cryptic codes, no decorative bezels.

## Shell elements
- **Top strip, no clock:**
  1. Layout switcher.
  2. Connection chip: the value comes from the Gateway, e.g. "Connected", "Last seen 10:42". Tapping it opens the Gateway app.
  3. Warning strip.
  4. Shared settings.
- **Tile label menu:** Swap page · Page settings · Open beside · Close.
- **Each app keeps its own navigation and settings inside its tile:** an app's own navigation row shows at Standard and Expanded sizes, and hides at Compact and Chip.
- **Shared settings, which apply to every app:** display (units, theme, text size), account and sync, layouts.

## Themes
- **Full custom CSS, changing structure as well as colour:**
  - frame;
  - labels;
  - numbers;
  - gauges;
  - controls;
  - strip;
  - divider.
- **Each theme ships a day and a night version.** The choice is Auto, Day or Night; Auto follows the headlights, then the light sensor, then sunset.
- **Themes never change:**
  - layout and tile sizes;
  - touch targets;
  - the drag handles between tiles;
  - warning and caution colours;
  - safety icons.
- **Current set:**
  - Night;
  - Heritage;
  - Expedition;
  - Blueprint;
  - Race;
  - Adventure;
  - Knight Rider;
  - Paper/Ink;
  - Military;
  - Naval (red bridge lighting at night);
  - Jet fighter;
  - Spy.
- **Physical controls are not part of a theme.** Steering-wheel controls and soft keys will come later as a separate overlay app.

## Consequences
- One shell to build, test and theme; there is no drive-mode codebase.
- Every page must implement the page contract:
  - the sizes it supports;
  - its summary value;
  - whether it is safe while moving;
  - its links to other pages.
- Apps stay independent (they install and run alone) but compose cleanly on a shared screen.
- Old drive dashboards (Dashboard, Minimal, Off-road) are kept as saved layouts made of pages, not as modes.

## Suggested build order
1. The shell: tile engine, window rules, size snapping, top strip, moving rules.
2. The page contract.
3. The Gateway app: connect, status, cars, permissions.
4. Theme resolver and validation.
5. Port Diagnose and Logs to the four sizes, then the instruments, then Maps and Convoy.
6. Warnings.
7. Drag-and-drop editing and automatic layout switching.
