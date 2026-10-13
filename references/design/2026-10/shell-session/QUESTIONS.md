---
title: "Questions for the designer after building the shell session's guide"
area: references
status: draft
version: 0.2
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/IMPLEMENTATION.md, specs/2026-10-11-ostler-shell-design.md]
summary: >
  Open questions for the designer that came out of building and safety-reviewing the v2 shell. First question: the guide's §9.2 sends a warning to the tile of the page that raised it, but its §16 checks A-04 and A-06 say an instrument's values are never covered, so a warning raised by an instrument page has nowhere to go. Until the designer rules, the takeover covers its own instrument tile (shell spec §21). Questions 2 to 6 come from the visual check of the built shell against the frames: whether right-hand drive mirrors the tiles or only the edit bar (X-18); whether the pinned column repeats on the spilled split-screen page (L-10); the pinned row's height in 15-inch portrait (L-13); where the delete circle sits (C-09 against X-18); and the 18 dp moving label token against the 24 dp moving text floor.
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

## 2. Right-hand drive: do the tiles mirror?

X-18 says "the edit bar and delete circle mirror", and keeps Diagnose on the left with Logs and
Engine on the right. The shell mirrors the whole layout for RHD: tiles, the pinned column and
the edit bar (pages-18 and view-1 too). Should a layout's tiles mirror for RHD, or only the
shell's chrome (edit bar, delete circle, pinned column)?

## 3. Split screen: does the pinned column repeat on the spilled page?

L-10 shows the second Single page with Transfer, Heading and Attitude across the full width, and
no pinned Speed. The shell repeats Speed's 300 dp pinned column on every page. Is the pinned
column on the first page only, or on every page?

## 4. 15″ portrait: how tall is the pinned row?

L-13 has a 1200 × 1920 window with the pinned Route row about 640 dp tall, about a third of the
height. The shell uses the pinned column's 360 dp, run along the height. Is it 360 dp, or a
third of the height? (L-13 still shows the old bottom strip, which is dropped.)

## 5. Where does the delete circle sit?

C-09 puts the delete circle at the bottom centre of the window. X-18 and the token put it in the
driver's half. The shell follows the token. Which frame wins?

## 6. Moving labels: 18 dp or 24 dp?

The tokens give `type.label.moving` 18 dp, and A-13 and X-14 show 18 dp labels and units while
moving. The guide's moving rule and `type.movingMinimum` say 24 dp. The shell will follow the
24 dp floor for all text while moving, labels included. Is there a reason labels should be the
exception?
