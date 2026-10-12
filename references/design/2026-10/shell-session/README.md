---
title: "Shell design session, 12–13 October 2026 — pages, Android-style edit mode with tiling, stacks, two-level focus and alerts with no top strip"
area: references
status: draft
version: 0.1
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/REVIEW.md, references/design/2026-10/brief/11-edit-mode-brief.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, specs/2026-10-11-ostler-shell-design.md, references/design/2026-10/shell-ui/README.md]
summary: >
  The owner and designer's shell session of 12–13 October 2026, saved as delivered less the design tool's runtime: five .dc.html designs (Ostler Shell System, 34 frames, the current reference; edit mode v3; zoom-out edit; large screens; drop zones), the designer's frame generators (shell-kit.js, shell-edit-kit.js, build/*.js) and PNG renders as the in-repo view. It replaces the edit-mode parts of 11-edit-mode-brief where they conflict: pages at least 720 dp wide (one on small windows, two on 15″, a pinned driver column from 12″, spanning, Wide and Single-page versions of each layout); no top strip (per-app stale data, a Viewing pill, a gateway-lost banner); an Android-style zoom-out edit mode with a selector, an edit bar (settings, Undo, Layout, Done), a resize frame, shapes, swap, stack and split zones and a delete circle; layout-first adding with a slot picker; stacks with badges and full screen by double-tap; two-level focus; alerts as a ring and tag on screen or a centred card off screen, readable tabs, spoken cautions, no master caution. REVIEW.md lists what matches, the conflicts with decided docs and the owner decisions.
---

# Shell design session, 12–13 October 2026

The owner and designer's shell session, saved here for the builder. **Read
[REVIEW.md](REVIEW.md) first**: what it changes, what conflicts with the decided docs, and the
decisions for the owner.

| Path | What it is |
|---|---|
| `designs/Ostler Shell System.dc.html` | The current reference: 34 frames, the whole system |
| `designs/shell-E-edit-mode-v3.dc.html` | Edit mode in detail |
| `designs/shell-W-zoom-out-edit.dc.html` | Android-style zoom-out edit, page panels, window style |
| `designs/shell-L-large-screens.dc.html` | 15″ landscape and portrait, pinned column, spanning, split screen |
| `designs/shell-E-drop-zones.dc.html` | Drop-zone research |
| `designs/shell-kit.js`, `shell-edit-kit.js`, `build/*.js` | The designer's frame generators (static HTML, exact values) |
| `png/` | Renders of every design, in 1800 px slices (the in-repo view) |
| `IMPLEMENTATION.md` | The designer's implementation guide: **the build spec** (adopted by the owner) |
| `HANDOFF.txt` | The designer's builder brief, as delivered |

The `.dc.html` files need the design tool's `support.js` beside them to open; it is not kept in
the repo.
