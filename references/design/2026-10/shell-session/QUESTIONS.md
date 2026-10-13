---
title: "Questions for the designer after building the shell session's guide, and the rulings"
area: references
status: stable
version: 1.0
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/IMPLEMENTATION.md, specs/2026-10-11-ostler-shell-design.md]
summary: >
  Six questions for the designer from building and checking the v2 shell, all answered on 2026-10-13 and recorded in the shell spec §21. An instrument shows its own warning in place (red ring, a red ACK bar inside the tile, the app's value turned red, the main value always visible), falling back to the ring and tag with the takeover on a passenger-side non-instrument tile when the tile is too small. RHD mirrors the whole layout; the pinned column repeats on every page and is 360 dp in portrait; the delete circle sits at the bottom centre of the driver's half; all text is at least 24 dp while moving, labels included.
---

# Questions for the designer

## Rulings (2026-10-13)

The designer answered every question; the shell spec §21 records them.

1. **(c), falling back to (b).** An instrument that raises a warning shows it in place without
   hiding its value: a red warning ring around the tile, a red ACK bar inside the bottom of the
   tile holding the message, and the app turns its own value red. The main value always stays
   visible. If the tile is too small for the bar (Compact height under 200 dp, Chip or Badge):
   ring and tag on the instrument, and the takeover or band on a passenger-side non-instrument
   tile. An instrument's values are never covered.
2. **Mirror the whole layout, tiles included.** The main tile belongs on the driver's side; X-18
   was wrong.
3. **The pinned column repeats on every page;** that is what pinned means. L-10 was wrong.
4. **The pinned row is 360 dp,** the same token along the long axis. L-13 was wrong, and the
   strip is gone.
5. **The delete circle sits at the bottom centre of the driver's half,** as the token says. C-09
   was wrong.
6. **24 dp, no exception.** The 18 dp moving label was an error in the tokens and frames.

The designer will redraw the affected frames.


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
