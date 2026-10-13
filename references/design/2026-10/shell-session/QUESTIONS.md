---
title: "Questions for the designer after building the shell session's guide"
area: references
status: draft
version: 0.1
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/IMPLEMENTATION.md, specs/2026-10-11-ostler-shell-design.md]
summary: >
  Open questions for the designer that came out of building and safety-reviewing the v2 shell. First question: the guide's §9.2 sends a warning to the tile of the page that raised it, but its §16 checks A-04 and A-06 say an instrument's values are never covered, so a warning raised by an instrument page has nowhere to go. Until the designer rules, the takeover covers its own instrument tile (shell spec §21).
---

# Questions for the designer

## 1. A warning raised by an instrument page

The guide's §9.2 routes a warning on a page that is on screen to that page's own tile. Its §16
acceptance checks A-04 and A-06 say an instrument's values are never covered. When an instrument
page (Speed, Attitude, Engine as an instrument) raises a warning, the two rules collide.

Until you rule, the shell lets the takeover cover the instrument's own tile (shell spec §21).
Which should win?

- **(a)** The takeover covers the instrument's own tile, as today.
- **(b)** The takeover goes to a passenger-side non-instrument tile, or the band, and the
  instrument tile keeps its values with the ring and tag only.
- **(c)** Something else, such as a takeover that leaves the instrument's main value visible.

Please send a frame for 7″ and 15″, Night and Day, parked and moving.
