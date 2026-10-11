---
title: "Designer hand-off doc — proposed ADR: pages adapt to their tile at four sizes (as received, 2026-10-11)"
area: references
status: draft
version: 1.0
updated: 2026-10-11
depends_on: [references/design/2026-10/mfd/REVIEW.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md]
summary: >
  The designer's proposed ADR from the MFD hand-off of 2026-10-11, kept as received for reference (frontmatter added on import). Four size classes (Chip, Compact, Standard, Expanded) picked from the tile's space, with rules: content added never squeezed, parts ranked by priority, shape picks arrangement, classes snap, state survives, missing parts collapse, each page declares sizes, summary value and moving safety. Not a decision of this repo: ADR-0052 (five classes with thresholds) is authoritative; see the hand-off review.
---

# ADR (proposed): Pages adapt to their tile at four sizes

Status: Proposed
Date: 2026-10-11
Related: ADR-0049 (Ostler is not an OS), "One MFD shell, no drive modes" (to be written)

## Context

Ostler apps run on phones, head units (800×480, 1024×600), tablets and browsers, as standalone PWAs, side by side under Android split screen, and inside Ostler's own tiles. The same page can be given a 180 px strip or a full 1280 px screen. Designing per device doesn't scale, and stretching one layout either squeezes content or leaves empty space.

## Decision

Every page is designed at four size classes. The shell picks the class from the space the page's tile actually has, never from the device, screen size or app.

| Size | Typical space | What the page shows |
|---|---|---|
| Chip | Under ~200 px wide or ~130 px tall | Icon, name and one summary value. Tapping it opens the page. |
| Compact | Narrow column or small tile | The single most important thing and its next step. |
| Standard | Half screen | Today's design. |
| Expanded | ≥640 px wide and ≥440 px tall (≥760 px for Diagnose and Logs) | Standard plus extra parts beside or below it. |

Rules:

1. **Content is added, never squeezed.** Moving up a size adds parts; moving down removes the lowest-priority parts. Type and touch targets never shrink below the minimums (22 px text and 44 px targets while moving).
2. **Each page ranks its parts by priority.** For example:
   - Diagnose: top fault and next step → systems list → freeze-frame and live values.
   - Logs: chart → events → drive summary.
   - Attitude: pitch and roll → trail maximums and limits.
3. **Shape picks the arrangement within a size.** Wide tiles put parts side by side; tall tiles stack them.
4. **Classes snap.** There's no continuous stretching, and a small buffer stops the layout flickering while a divider is dragged.
5. **State survives a size change.** Selected fault, chart cursor and zoom are kept.
6. **A missing part collapses** (see the trust and availability rules). Expanded never shows empty boxes to fill space.
7. **Each page declares, for the shell:** the sizes it supports, its summary value (for Chip and Compact), and whether it is safe while moving, parked-only, or reduced while moving. The shell won't put a page in a size it doesn't support.

## Consequences

- One page definition works in Android split screen, Ostler tiles, standalone PWAs and on the Guardian.
- App teams build four layouts per page instead of one per device; design reviews check all four.
- The shell owns size measurement, snapping and the moving rules; pages never read the device type.
- Drive "modes" are no longer needed: car instruments are ordinary pages, and saved layouts replace modes.

## Reference

Demo: `Ostler MFD v2.dc.html`. The tile label shows the app and its current size class.
