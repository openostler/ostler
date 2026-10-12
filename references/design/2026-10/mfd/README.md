---
title: "MFD design hand-off, 11 October 2026 — the designer's MFD, tiling, core, gateway and themes designs, with renders and the review"
area: references
status: draft
version: 0.1
updated: 2026-10-11
depends_on: [references/design/2026-10/mfd/REVIEW.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, specs/2026-10-11-gateway-settings-design.md, specs/2026-10-07-theme-engine-design.md, references/design/2026-10/brief/00-direction-mfd.md, references/design/2026-10/brief/00-structure.md]
summary: >
  The designer's MFD hand-off of 2026-10-11, saved as delivered less the design tool's runtime: eight .dc.html designs (MFD v2, Tiling v2, Core, Core Sizes, Gateway, Themes v2, and the v1 MFD and Tiling), three docs (two proposed ADRs and the direction brief with its Gateway update), and PNG renders as the in-repo view. The owner: "there is some drift here but you get the idea". The repo's ADR-0052, the gateway settings spec and the theme engine spec stay authoritative; REVIEW.md lists what matches, the drift and the decisions for the owner.
---

# MFD design hand-off, 11 October 2026

The designer's hand-off for the MFD direction, saved here so the builder can work from it.
The owner's note: "there is some drift here but you get the idea".

**Authority.** These are reference designs. Where they differ from
[ADR-0052](../../../../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md), the
[gateway settings spec](../../../../specs/2026-10-11-gateway-settings-design.md) or the
[theme engine spec](../../../../specs/2026-10-07-theme-engine-design.md), the repo wins until
the owner decides. **Read [REVIEW.md](REVIEW.md) first:** design by design, what matches, the
drift and the decisions for the owner.

## What is here

| Path | What it is |
|---|---|
| `designs/` | The eight `.dc.html` designs, as delivered |
| `docs/` | The designer's three docs, as delivered (frontmatter added so the index can list them) |
| `png/` | Renders of every design (31 PNGs, about 5 MB): the in-repo view |
| [REVIEW.md](REVIEW.md) | The design-by-design review and the owner's decision list |

## Designs

| Design | Shows | Renders |
|---|---|---|
| `Ostler MFD v2.dc.html` | Interactive MFD: saved layouts (Trail, Convoy, Commute, Workshop, Bench), the six layouts (locked while moving), car moving, caution, master warning, right-hand drive; tile labels show app and size | `mfd-v2-*.png` |
| `Ostler Tiling v2.dc.html` | The window rules: 7″ whole screen, Android split half and third, 10″ split top and bottom, master warning as a band, 5″ head unit, phone Workshop and Convoy | `tiling-v2-00…04.png` |
| `Ostler Core.dc.html` | Interactive bare shell: Not connected, Connected no apps (Car page and suggestions), First app beside Car, car moving, Settings sheet with themes | `core-*.png` |
| `Ostler Core Sizes.dc.html` | The same four states at five screens: phone 393×852, 5″ 800×480, 7″ 1024×600, 10″ 1280×720, tablet 1180×820 | `core-sizes-*.png` |
| `Ostler Gateway.dc.html` | Gateway app: first-run connect, Status, New car found, per-app car permissions, car profile settings, This device (web permissions), This gateway (one server per car), offline app, the connection chip states and action permission states | `gateway-00…04.png` |
| `Ostler Themes v2.dc.html` | Twelve themes, each drawn day and night on one Diagnose + Engine screen, with what each changes (frame, labels, numbers, gauges, controls, strip, divider) | `themes-v2-*.png` |
| `Ostler MFD.dc.html` (v1) | Earlier interactive MFD with a layout rail and edge soft keys; kept for reference | `v1-mfd.png` |
| `Ostler Tiling.dc.html` (v1) | Earlier tiling first look: linked tiles, four sizes, Open beside, phone tab bar; kept for reference | `v1-tiling.png` |

## Docs

- `docs/ADR-proposed-mfd-shell.md`: the designer's MFD decision (one shell, tiles, no drive modes).
- `docs/ADR-proposed-adaptive-page-sizes.md`: the designer's four page sizes.
- `docs/Ostler Direction Brief.md`: the direction brief with the 11 October Gateway
  architecture update at the top. The body is the brief already kept, with the owner's
  corrections, in [brief/00-direction-mfd.md](../brief/00-direction-mfd.md).

The names "ADR (proposed)" are the designer's; they are not numbered ADRs of this repo.

## Opening the designs

- The `.dc.html` files run on the design tool's runtime, `support.js`. **It is not in the
  repo:** it is the tool's generated runtime ("GENERATED from dc-runtime/src/*.ts"), its
  licence is unknown, and the earlier import left it out the same way
  ([claude-design README](../claude-design/README.md), "Changes on import"). Use the PNGs.
- `Ostler Core.dc.html` also loads `ostler-themes.js`. The delivered copy is byte-identical to
  [`../claude-design/project/ostler-themes.js`](../claude-design/project/ostler-themes.js) (the
  22-theme set), so it is not duplicated here.
- To render them again: copy `designs/`, `support.js` and `ostler-themes.js` into one folder
  outside the repo, serve it over local HTTP (the runtime fetches the page, so `file://`
  fails) and screenshot with a headless browser after about 6 s. Maps are placeholders.

## Changes on import

- `support.js` (the design tool's runtime) left out, as above.
- `ostler-themes.js` not duplicated (identical to the copy already in the repo).
- Frontmatter added to the three docs; their text is unchanged.
- PNG renders added (31 of the 64 taken; the rest repeat these).

## Licence

Owner and designer work, annotated in `REUSE.toml` like the earlier design export
(AGPL-3.0-or-later, OpenOstler contributors).
