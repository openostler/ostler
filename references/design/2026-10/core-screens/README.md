---
title: "Core screens design (2026-10-08): Home, Drive mode, Trips and Trip detail"
area: references
status: stable
version: 0.1
updated: 2026-10-08
depends_on: [specs/2026-10-08-core-screens-adoption-design.md, references/design/2026-10/README.md]
summary: >
  The owner's design of the four core screens, kept as PNG renders of the owner's HTML export: 01 Home (phone Night and Day, HU-7 Parked), 02 Drive mode (phone and HU-5 Moving, plus an HU-5 message alert that is not adopted), 03 Trips list and 04 Trip detail (phone and HU-7). Reference car: the 2002 Discovery 2 Td5, right-hand drive. How it is adopted, and the owner's changes (Trips is Logs, Map replaces Security in the nav, a log opens to its summary first), are in the core screens adoption spec.
---

# Core screens design (2026-10-08)

The owner's design of the core screens, saved as delivered so the builder can work from it.
**What is adopted, what is not and the owner's changes are in the
[core screens adoption spec](../../../../specs/2026-10-08-core-screens-adoption-design.md).**
Read that first; where this design and the spec differ, the spec wins.

## The files

The owner's design came as one self-contained HTML page (about 4.5 MB). Following the hand-off
folder's rule (HTML at most 2 MB, larger kept outside the repo; [hand-off decisions](../README.md),
item 4), the repo keeps PNG renders of each section; the owner keeps the HTML. The bundle also
embeds the design tool's page runtime, whose licence is unknown, which is a second reason not to
commit it. The maps load live tiles, so they render blank in these PNGs.

| File | Section | Frames |
|---|---|---|
| `01-home-a.png`, `01-home-b.png` | 01 Home | Phone · Night; HU-7 · Night · Parked (1024×600); Phone · Day |
| `02-drive-mode.png` | 02 Drive mode | Phone · Moving; HU-5 · Moving (800×480); HU-5 · Moving · message alert (**not adopted**) |
| `03-trips.png` | 03 Trips | Phone · Night; HU-7 · Night · Parked |
| `04-trip-detail.png` | 04 Trip detail | Phone · Night; HU-7 · Night · Parked, sheet on the passenger side (left) |

The page's own notes: the speed ramp is a six-step violet placeholder (build with the
`speed-1` … `speed-6` tokens instead); coolant's normal band is "below 105 °C"; the Trip tile
has no normal range, so it shows time and average speed instead of a bar; the Faults,
Ghost/Visible and live-data tweaks apply to every screen. These are prototypes: rebuild them
in `ui/`.
