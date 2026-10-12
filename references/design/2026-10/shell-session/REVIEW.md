---
title: "Review of the 12–13 October shell session — what it changes, conflicts with decided docs, and decisions for the owner"
area: references
status: draft
version: 0.1
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/README.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, specs/2026-10-11-ostler-shell-design.md, references/design/2026-10/brief/11-edit-mode-brief.md]
summary: >
  Review of the designer's shell session handoff against ADR-0052 v0.7 and the shell spec v1.2. Most of it refines decided direction (Android-style edit mode, no permanent bars, layout carousel, Show frame as widgets). It overturns some decided points: the top strip is removed (connection, vehicle and settings chips go); swiping works anywhere a page does not claim; the soft-key row is not mentioned. Conflicts to settle: D-pad paging at the screen edge (owner) against arrows never leaving a page (designer); warnings on the passenger side (table) against the driver side on big screens (summary); the 720 dp page minimum against phones and 5″ screens; alerts drawn above the Gateway app, which a web page cannot do. Recommends using the designer's kit as the visual source by generated tokens and screenshot tests, and moving the designer onto the real component library. Ten decisions for the owner.
---

# Review: shell session of 12–13 October 2026

Against [ADR-0052](../../../../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md) v0.7
and the [shell spec](../../../../specs/2026-10-11-ostler-shell-design.md) v1.2 §19. The designer's
brief ([HANDOFF.txt](HANDOFF.txt)) says it replaces the edit-mode parts of
[11-edit-mode-brief](../brief/11-edit-mode-brief.md) where they conflict.

## Matches decided direction

- Android-style edit mode entered by a 0.5 s hold, parked only; no permanent divider bars; snaps
  at ⅓, ½, ⅔ and class boundaries; Undo and Done.
- A carousel of saved layouts with page dots; swiping parked only; layouts and full screen still
  work while moving.
- Window style "None" is a widget (our "Show frame" off).
- Split on drop by the target's halves; shapes as quick starts.
- Warning takeover avoids instrument pages; ACK is Select on the wheel.

## New in this session

- **Pages:** a column at least 720 dp wide; one page on small windows, two on 15″, three
  ultra-wide; a pinned driver column from 12″; spanning across the page line; a **Wide** and a
  **Single-page** version of each layout, neither overwriting the other.
- **Edit mode detail:** pages zoom out to about 84% on translucent panels with a selector;
  an edit bar (settings, Undo, Layout, Done); a resize frame on tap; hold a selected tile for
  window style (Normal, Transparent, None) and corners; drag to the screen edge to change page;
  a delete circle at the bottom; layout-first adding with + slots and a slot picker (Snap
  Assist).
- **Stacks:** hold one page on another tile's centre; badges on an edge (auto next to bezel keys,
  else passenger side), in pages; badges can map to physical keys.
- **Full screen for a while:** double-tap or OK twice; works while moving; nothing saved.
- **Two-level focus:** arrows between tiles; OK enters a page, arrows move through its controls,
  Back leaves.
- **Alerts:** on screen, a ring and a tag (caution) or the warning on the tile; off screen, a
  centred card for about 4 s (caution, never modal, with Diagnose and ACK) or a takeover
  (warning); afterwards a readable tab in the passenger-side top corner; bordered page dots and
  badges show where; a chime and one spoken line for cautions, a repeating tone for warnings; no
  master caution; Gateway posts Android notifications on separate channels.
- **Sizes in dp.**

## Conflicts with decided docs

1. **Top strip removed.** ADR-0052 §2 and the spec §11 have a strip with the connection chip,
   vehicle chip, alert pill and settings button (≤ 48 px on 480 px screens). The session removes
   it: stale data per app and module, a "Viewing …" pill and a one-off gateway-lost banner,
   settings in the edit bar and the Gateway app.
2. **D-pad at the screen edge.** The owner decided (v0.7) that the cursor moving off the screen
   edge pages to the next layout. The session says arrows never leave a page at its edge; only
   Back does.
3. **Swiping.** v0.7: swipe on the strip or screen edge, never on a tile. Session: swipe anywhere
   a page does not claim (maps, sliders and lists claim first).
4. **Soft-key row.** v0.7 made it optional; the session does not mention it, and bezel keys map to
   stack badges instead.
5. **Warning side.** The alert table puts the takeover on the passenger side; the system summary
   says warnings go to the driver side on big screens.
6. **720 dp page minimum** against phones (393 dp wide) and the 5″ head unit (800 dp), which the
   session also says show one page.
7. **Alerts drawn above the Gateway app.** A web page cannot draw over another app; only the
   native Gateway app (or Ostler Controls) can, with the overlay permission and its limits
   (research note §4).
8. **Units.** Our thresholds are CSS px; the session uses dp. In Chrome on Android a CSS px is one
   dp at default zoom, so the numbers carry over; head-unit WebViews need a bench check.

## Recommendation: use the designer's components as the source, not a copy

The designer's `shell-kit.js` and `shell-edit-kit.js` render static HTML with inline styles (no
events, state or accessibility), so they cannot run the shell. Rather than hand-translating them
again: (1) **generate** `tokens.ts` from the kit's palette and values; (2) **screenshot-test**
our components against the kit's frames at the same sizes, so drift fails a test; (3) going
forward, the designer **works in the real component library** (the playground or a component
catalogue), so there is one set of components.

## Decisions for the owner

1. **Remove the top strip?** Recommend yes, as designed, keeping a quiet connection state per
   app and the gateway-lost banner.
2. **D-pad at the edge.** Recommend: at tile level, moving off the left or right edge pages to
   the next page (owner, v0.7); inside a page, arrows never leave (designer).
3. **Swipe anywhere unclaimed, parked only?** Recommend yes.
4. **Soft-key row:** drop it, with app controls reached by OK and bezel keys mapped to badges?
   Recommend yes.
5. **Warning side on big screens:** passenger side (the table) or driver side (the summary)?
   Recommend passenger side, never covering an instrument.
6. **Page minimum:** recommend 720 dp only decides how many pages fit; one page always fills a
   smaller window.
7. **Alerts over other apps:** only through the Gateway app or Ostler Controls, natively.
8. **Wide and Single-page versions:** adopt as designed.
9. **Spoken cautions and repeating warning tone:** adopt, with a mute in Display settings.
10. **Designer workflow:** generated tokens and screenshot tests now; the designer on the real
    components next.
