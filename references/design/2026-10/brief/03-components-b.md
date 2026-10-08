---
title: "Designer brief — components (b): the kit, data display, maps, Moving templates and widgets"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md]
summary: >
  The second part of the component inventory. The kit controls (Button, Segmented, Chip,
  ListRow, Card, text field, toggle, Sheet, Sheet over map, Toast, inline notice, empty state,
  skeleton, checklist), the data components (Value, StatTile, HeroStat, calm Gauge, RangeBar,
  Sparkline, Donut, DistributionBars, area line, chart lanes, Scrubber, map and trace,
  connection ladder, status tag), the eleven Moving templates with their limits, the starter
  widgets, and the mapping from today's ui/src files. Sizes per class, states and tokens. Amended 2026-10-07 (openness round, ADR-0047): style values are the default look under visual §13 and the theme engine; safety rules unchanged.
---

# Components (b): kit, data, maps, Moving templates, widgets

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("apply the
> loosenings"; [ADR-0047](../../../../decisions/adr-0047-openness-round.md)):** Toast length and the card's hover behaviour are defaults. Style values here are the default look;
> themes, add-ons and users may change them within [visual §13](../../../../specs/2026-10-07-visual-design-system-design.md#13-design-language-themes-amendment-2026-10-07) and the
> [theme engine](../../../../specs/2026-10-07-theme-engine-design.md#11-decisions-for-the-owner). Safety rules are unchanged.

Size steps P, T, H7 and H9 are defined in [03-components-a](03-components-a.md#how-to-read-the-inventory).
Owner of every component: **os**.

## 1. Controls

| Component | Purpose | Variants | Sizes | States | Tokens | In code today |
|---|---|---|---|---|---|---|
| **Button** | one action, named by its verb | primary (accent, one per screen), secondary (`surface-3`), ghost, danger (alarm text) | P/T 48, `radius-sm`, `type-label`; H 76, `type-body` | default, pressed, focus, disabled with reason, loading ("Scanning…"), queued ("Queued · expires 14:35") | `accent`, `on-accent`, `surface-3`, `alarm` | `.btn`, `ActionButton.tsx` |
| **Segmented** | 2–4 exclusive options | text, icon + text | P 40 drawn / 48 hit; H 76 | selected `accent-soft` + `accent` text (the only selected style) | `surface-3`, `accent-soft` | `.seg`, `RadioOpt.tsx` |
| **Chip** | filter, choice or status | filter, choice, status (tone + icon + word), capability ("Clone: read-only"), countdown | P 32 drawn / 48 hit; H 48 / 76 | selected as Segmented; status tones | `*-bg`, `ok/warn/alarm` | `.chip`, `StatusChip.tsx` |
| **ListRow** | one row in a list | icon, title, meta, trailing value, chevron, switch or button; `short_list` row ≤ 30 characters | P 56; H 76 | pressed tint, focused `accent-soft`, disabled with reason | `line` between rows | `.morerow`, `.sysrow` |
| **Card** | a group on `surface-1` | plain, tappable (chevron; no hover scale by default), tone (`*-bg` + 4 px edge) | padding P 16, H 24; `radius-md` | — | `surface-1`, `*-bg` | `ItemCard.tsx`, `HealthStrip.tsx` |
| **Text field** (new in kit) | typed input, Parked only on head units | single line, search, multi-line, typed confirm | P 48; H 76; placeholder in `text-2` | focus ring, error line in `alarm`, locked while Moving | `surface-3`, `line-strong` | `InlineEdit.tsx` |
| **Toggle** (new in kit) | on/off setting | with label and one-line help | P 48 row; H 76 row | on (`accent`), off, disabled with reason | `accent`, `surface-3`, `radius-pill` | — |
| **Sheet** | a panel over the page; the only focus trap | bottom (phone), side on the passenger side (H, 520 px), full height (share, confirm) | grab handle; `radius-xl` top | open/close is the allowed motion; scrim `overlay` | `surface-2`, `overlay`, `elev-3` | `Sheet.tsx`, `ConfirmSheet.tsx` |
| **Sheet over map** | stats and controls over a full-bleed map | peek 25 %, half, full | as Sheet; no blur on H | `surface-glass` | `surface-glass` | `AnalysisView.tsx` |
| **Toast** (new) | short note with optional Undo | info, with action, queued, "Park to edit", "Sent" | ≤ 60 characters (P), ≤ 30 (H) recommended | one at a time; 4 s or 8 s | `surface-2`, `radius-sm` | toast in `state/` |
| **Inline notice** (new) | why a control cannot act | role, kiosk, remote, refused by the gate | `type-caption` under the control | — | `text-2`, `warn-ink` | — |
| **Empty state** (new) | nothing to show and why | a–f in `ia-empty-state` | icon 24 / 40, title, line, one Button | — | `text-2` | `Security.tsx` text |
| **Skeleton** (new) | the page's shape while loading | row, stat grid, map, chart | as the final layout | static, no shimmer | `surface-3`, `bg` | — |
| **Checklist** (new) | Tier 2 preconditions | auto-ticked from live data, user-ticked | ListRow with a tick | met, not met (reason), stale | `ok`, `text-2` | `ActionButton.tsx` |
| **ActiveTestBanner** | a latched test is running | with Stop and time left | full width under the strip | always on while running | `warn-bg` | `ActiveTestBanner.tsx` |

## 2. Data display

| Component | Purpose | Variants | Sizes | States | Tokens | In code today |
|---|---|---|---|---|---|---|
| **Value** | number + unit, tabular | with decimals, converted units | number step per context; unit × 0.45 | missing "—", stale grey + age, `candidate` dashed underline | `text-1`, `text-2`, `unit-ratio` | `Value.tsx` |
| **StatTile** | kicker + value + unit (Boost "1.2 bar") | plain, with RangeBar, with Sparkline (Parked), acting tile | P `type-num-l`; H `type-num-xl` (≥ 56 px digits in Drive) | stale, candidate, missing, warn, alarm (icon + word) | `type-num-*`, status tones | `StatTile.tsx`, `Readout.tsx` |
| **HeroStat** | the one big number per screen | with caption; optional `data-glow` (phone only) | P 64; T 72; H7 96; H9 120 | as StatTile | `type-hero` | — |
| **Gauge** | calm 240° arc (Coolant, RPM) | full, half, with normal band | track 8 (P) / 12 (H) | in range `text-2` arc; out of range `warn`/`alarm` + word; ≤ 4 Hz while Moving | `surface-3`, `band`, `text-2` | `Gauge.tsx` |
| **RangeBar** | value against its healthy band | horizontal | 4 / 8 px track | marker turns alarm only when flagged | `band`, `surface-3` | `RangeBar.tsx` |
| **Sparkline** | last ~60 s shape | 1.5 px line, last point dot | inside a tile | Parked only on head units; accent only when live | `text-2`, `text-1` | `Sparkline.tsx`, `Trend.tsx` |
| **Donut** | time at speed | Time / Distance | in a Card | Parked only on H | `speed-1…6` | — |
| **DistributionBars** | speed distribution | values labelled | in a Card | Parked only on H | `speed-*`, `chart-axis` | — |
| **Area line** | speed or a signal over time | with crosshair and tooltip | full width | gaps drawn as gaps | `speed-4`, `series-1`, `chart-grid` | `Chart.tsx` |
| **Chart lanes** | up to 3 signals on one time axis | zoom, select, cursor | full width | Parked only | `series-1…3` | `Chart.tsx` |
| **Scrubber** | move through a recording | 1× 2× 4× 8× chips, ±10 s, note ticks (24 hit) | P 48 hit; H 76 hit | engaged (D-pad), playing | `accent` thumb | `Transport.tsx`, `GlobalTransport.tsx` |
| **Map** | own position, trace, places | full bleed, card thumbnail, `map` template | full bleed; attribution collapsed `info` | offline: `bg` + trace + puck; cooperative gestures inside scrolling pages | Ostler Night/Day, `trace-casing`, `speed-*` | `TraceMap.tsx`, `maplibre.ts` |
| **Ladder** (new) | the connection rungs | five rungs + 12 V | ListRow per rung | ok, failed (named), not reached "—" | status tones | `ConnectionSheet.tsx` |
| **Status tag** | item confidence (Experimental only) | proven, candidate, sniff, untranscribed | `type-caption` | — | `info`, `warn-ink` | `StatusTag.tsx`, `CoverageBar.tsx` |
| **Vehicle silhouette** | D2 top-down body for vehicle views | body, SLABS heights | per page | doors, heights in values | `text-2`, status tones | `VehicleBase.tsx`, `SlabsCar.tsx`, `BodyCar.tsx` |

## 3. Moving templates (OS only)

While Moving on a driver-facing display, only these render ([UI §12.1][ui-12.1],
[Drive modes §4.3][dm-4.3]). Text ≥ 24 px, targets 76 px, no animation (glow and gradient are the theme's choice, under the render check).

| Template | Limit | Example (D2) |
|---|---|---|
| `telltale_list` | rows ≤ 30 characters | "Engine · Wastegate fault" |
| `value` | ≤ 2 values, one line ≤ 30 characters | Coolant and Battery on one line |
| `setpoint` | one setpoint with − and + | a climate setpoint |
| `camera_live` | driving cameras only | reverse camera |
| `arm` | arm only, never disarm | "Arm" |
| `tiles` | ≤ 6 tiles, digits ≥ 56 px, ≤ 4 Hz | RPM, Boost, Coolant, Battery, Height left, Height right |
| `map` | own position, route, next manoeuvre, convoy markers | own trace |
| `media` | title and artist ≤ 30, static artwork, play/pause/skip/volume | — |
| `alert_card` | one card, icon + ≤ 2 lines ≤ 30, ≤ 2 buttons | sender + app, **Play** / **Reply** |
| `short_list` | ≤ 6 rows, one level, ≤ 30 characters | Drive menu, page list |
| `call` | name ≤ 30, no photo, timer, ≤ 3 buttons | Answer / Decline |

## 4. Starter widgets (Owner: app:widgets-starter, drawn in the OS widget frame)

Signal tile, gauge, hero number, binary chip, enum text, sparkline (Parked only),
inclinometer, compass, altitude, clock, vehicle card. Each declares sizes (small, medium,
wide, hero) and a Moving template (`tiles` or `value`), and has a setup page
(`drive-widget-settings`: signal, style, units, decimals, label, icon, range, thresholds).
OS widgets that cannot be removed: **warnings** (fault telltale) and, with the Security app,
**Security alert** ([Drive modes §8.1 R3][dm-8.1], [§9][dm-9]).

[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
