---
title: "Designer brief — components (a): the OS frame and launcher components"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  The first part of the component inventory: how to read it, the size steps per layout
  class, and the components the OS draws around every app. The status strip and its chips,
  badges, the page chip, the dock and dock items, the app drawer grid and app icons, folders,
  the home-page grid, page indicator dots, the widget frame with resize handles, the widget
  picker gallery card, the wallpaper layer, the edit bar, the item sheet and the frames for
  service mode and Passenger view. Each has purpose, variants, sizes per class, states and
  tokens, and what exists in ui/src today. Amended 2026-10-07 (openness round, ADR-0047): style values are the default look under visual §13 and the theme engine; safety rules unchanged.
---

# Components (a): the OS frame and launcher

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("apply the
> loosenings"; [ADR-0047](../../../../decisions/adr-0047-openness-round.md)):** OS components may be restyled by themes, apps style their own pages freely, and dock size, anchors and name lengths are defaults. Style values here are the default look;
> themes, add-ons and users may change them within [visual §13](../../../../specs/2026-10-07-visual-design-system-design.md#13-design-language-themes-amendment-2026-10-07) and the
> [theme engine](../../../../specs/2026-10-07-theme-engine-design.md#11-decisions-for-the-owner). Safety rules are unchanged.

## How to read the inventory

- **Names** are the visual spec's kit names ([visual §8][vds-8]) where they exist; new names
  are marked **new**. Use these names in every screen block's Components line.
- **Owner** for every component here is **os**: the OS draws them and the user's theme
  restyles them; an app cannot restyle OS chrome, but styles its own pages freely. Default
  values come from tokens ([visual §3–§5][vds-3]); themes may use any values.
- **Size steps.** Four columns are enough for every component:

| Step | Classes | Target | Body text | Label | Icon | Card padding |
|---|---|---|---|---|---|---|
| **P** | phone | 48 | 15 | 13 | 20 / 24 | `space-4` |
| **T** | tablet, desktop | 48 (pointer 40) | 15 | 13 | 24 | `space-4` |
| **H7** | hu5, hu7 | 76 | 24 | 20 | 32 / 40 | `space-6` |
| **H9** | hu9, huwide | 76 | 24 | 22 | 40 | `space-6` |

- **States** every interactive component draws: default, pressed (`accent-hi` or a lighter
  surface), **focus** (3 px `focus-ring-color` ring, 2 px `bg` gap; [shell input §9][si-9]),
  disabled (40 %, with the reason in words nearby), loading, and where it applies selected
  (`accent-soft` + `accent`) and stale (`text-3` + age).
- **In code today** names the file in `ui/src/` that the component replaces or grows from.

## 1. Status strip and its parts

| Component | Purpose | Variants | Sizes | States | Tokens | In code today |
|---|---|---|---|---|---|---|
| **Status strip** | one row of chips on every page | normal, Drive (adds Back and the page chip) | height P 48, T 56, H7 48/56, H9 64 | never scrolls; edit mode shows drag handles | `surface-2`, `line` | `shell/Strip.tsx`, `shell/strip.ts` |
| **Strip chip** (Chip, status variant) | one status with icon + word that opens a sheet | telltale (safety), Link, REC, Security (safety), device slot, 12 V, Clock, Mark, Vehicle, profile, visibility, ride/call | drawn ≥ 48 tall, hit 48 (P, T) or 76 (H) | ok, warn, alarm (icon + word), neutral, stale, alarm pulse (only motion) | `ok/warn/alarm`, `*-bg`, `warn-ink`, `type-label` | `StatusChip.tsx`, `MarkButton.tsx` |
| **Strip badge** | shell-drawn mode marker | Service mode, Replay, Passenger view, Remote control enabled | as a chip, not tappable | always on while its mode is | `warn`, `line-strong` | admin chip in `strip.ts` |
| **Page chip** (new; was the Drive-mode chip) | names the current dashboard and switches it | tap cycles, long press lists | as a strip chip | current page name; never hidden | `accent-soft` when focused | `strip.ts` `drive_mode` |

## 2. Launcher

| Component | Purpose | Variants | Sizes | States | Tokens | In code today |
|---|---|---|---|---|---|---|
| **Home page grid** (new) | the cell grid a home page holds | Home page 1, dashboard page; Parked grid and Moving section | cells: P 4×6, H7 HU-5 6×4 and HU-7 6×4, H9 8×4, HU-wide 12×4 ([Drive modes §4.4][dm-4.4]) | viewing; editing (cell outlines in `line`, empty cells show **+**); drop target highlighted `accent-soft` | `--gap`, `bg` over wallpaper | `drive/DriveFace.tsx`, `destinations/Home.tsx` |
| **Page indicator dots** (new) | where you are in the carousel | dots; edit mode adds a "+" dot for a new page | dot 8 (P) / 12 (H), gap 8 / 12, hit 48 / 76 for the row | current dot `text-1`, others `text-3`; hidden in Drive mode (the page chip says it) | `text-1`, `text-3` | — |
| **Dock** (was the rail and bottom bar) | by default 5 to 7 slots one tap away (phone, HU-5, HU-7 5; HU-9/10 6; HU-wide, tablet, desktop 7; item 17); the user may add slots, overflow scrolls | bottom (phone, tablet), driver side (head units, desktop optional); with labels on desktop | P 72 + safe area; T 88; H7 80 / 96; H9 112 | active slot `accent-soft` pill; edit mode drag handles; hidden in Drive mode | `surface-2`, `accent`, `accent-soft` | `shell/Nav.tsx` |
| **Dock item** | one app, shortcut or the App drawer button | app, shortcut, widget, Home and App drawer (default anchors, hideable while the recovery path stays; the Drive button is retired, item 16) | icon P 24 / H 40, word below (long words ellipsised) | default, active, focused, badge dot | `type-label`, `text-2`, `accent` | `Nav.tsx` items |
| **App drawer grid** (new; was More) | every installed app | grid, search on top, Settings and Store first, Hidden apps last | columns: P 4, T 6, H7 5, H9 7; rows scroll Parked | locked apps show a lock badge; search empty "No apps match" | `surface-1`, `text-1` | `destinations/More.tsx` |
| **App icon** (new) | one app in the drawer, dock or a page | plain, with badge dot (update or unread count), disabled | P 56 tile with 24 icon; H 96 tile with 40 icon; name below (ellipsised when long) | long press opens App info, Add to home, Add to dock, Hide | `surface-3` tile, `radius-md`, icon in `text-1` | — |
| **Folder** (new) | a group of shortcuts on a home page or in the dock | closed (2×2 mini icons), open (sheet with a grid and an editable name) | one cell; open sheet as Sheet | empty folder disappears; long names ellipsised | `surface-3`, `radius-md` | — |
| **Shortcut** (new) | a home-page link to one app page or action route | app page, saved filter, Drive menu row | one cell | shows the target app's icon with a small corner mark | as App icon | — |
| **Widget frame** (new) | the box every widget sits in, with edit controls | sizes small, medium, wide, hero; viewing and editing | frame = the widget's cells; resize handles 24 drawn / 48 hit (P), 40 / 76 (H) on each edge in edit mode; remove (×) top corner | viewing (no chrome), editing (outline `line-strong`, handles), picked up (ring doubles), safety (no ×, a lock note "Can move, can't be removed"), "Widget stopped" | `surface-1`, `radius-md`, `focus-ring-*` | `drive/widgets.tsx` |
| **Widget picker gallery card** (new) | one widget to add, in the picker | per app group; sizes shown as chips | P full width × 120; H 2 columns × 200 | default, focused, "Needs the Maps app · Get" (not installed), disabled for Moving ("Parked only") | `surface-1`, `type-label`, `text-2` | `shell-widget-picker` design only |
| **Wallpaper layer** (new) | the background behind home pages | solid `bg` (default), theme image, Night top glow (phone only) | full bleed under the grid | default: dimmed in Night dim; never animated while Moving; the theme decides how it shows in Drive mode | `bg`, `bg-glow` (default off on HU) | — |
| **Edit bar** | the top bar in edit mode | tabs Dock · Strip · Home · Dashboards · Apps; Done, Cancel, Undo, Redo, Preview, Reset; "Editing for: this screen ▾" (P, T) | height as the strip | Undo disabled at the start of the stack | `surface-2`, Button | — |
| **Item sheet** | options for one selected item | Move, Size, Icon, Name, Hide or Remove, Replace with…, Use defaults; safety variant | Sheet | absent rows, not greyed | Sheet | — |

## 3. Frames and banners the OS draws

| Component | Purpose | Variants | Sizes | States | Tokens | In code today |
|---|---|---|---|---|---|---|
| **Frame** (new) | a border round the viewport for a mode | Service mode, Passenger view | 6 px (P) / 8 px (H) inside the viewport edge | always on while the mode is | `warn` (service), `info` (passenger), `line-strong` | — |
| **Banner** (new) | a compact bar under the strip | offline, reconnecting, remote read-only, Moving (phone), node offline | height 40 (P) / 56 (H) | with one ghost Button | `*-bg` tones, `text-1` | `ConnectionNotice.tsx` |
| **Locked view card** | stands in for a locked page | with Open on phone, Passenger view, Back to Drive | ≥ 24 px text | — | `surface-1`, `type-body` | `StatusGate.tsx` (pattern) |
| **App stopped** card | an app crashed; the OS keeps running | page, widget ("Widget stopped") | fills the page or the widget | **Reload** | `surface-1`, `text-2` | `shell/Boundary.tsx` |

[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[si-9]: ../../../../specs/2026-10-07-shell-input-design.md#9-focus-visuals
[vds-3]: ../../../../specs/2026-10-07-visual-design-system-design.md#3-colour
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
