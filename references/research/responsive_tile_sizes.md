---
title: "Responsive tiles — size classes chosen from each tile's own box: container queries, ResizeObserver, precedents, hosting and recommended thresholds (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-11
depends_on: [references/design/2026-10/brief/00-structure.md, references/research/direction_standard_not_os.md, references/research/deep_theming_mechanics.md, references/research/canbus_headunit.md, specs/2026-10-07-theme-engine-design.md]
summary: >
  Research (2026-10-11) for the MFD model, where every page renders at a size class picked from its own tile, never the device. Container queries (size vs inline-size, cq units, style queries, Chrome 106+, repo floor 118, polyfill in maintenance mode); ResizeObserver patterns that avoid resize loops; precedents with discrete classes that drop content rather than scale it (Material 3 window size classes, Android widgets and Glance, iOS WidgetKit families, watch complications, Home Assistant sections, Grafana, Windows widgets); content priority (priority+, intrinsic layouts, fluid type only for hero numbers); window managers (Android split-screen snap targets and minimums, Windows Snap, react-resizable-panels); hosting another app's page (same-origin page modules, iframes only for third parties because each costs a renderer process). Recommends five classes (Badge, Chip, Compact, Standard, Expanded) with enter and exit thresholds, JavaScript as the source of truth and container queries for fine-tuning within a class.
---

# Responsive tiles: size classes from each tile's own box

Research for the MFD model (owner and designer brief, 2026-10-11): the screen is a layout of
tiles, each showing one page from any installed app, and **every page renders at a size class
picked from its own tile's box, never from the device**. Moving up a class adds content; moving
down removes the lowest-priority parts; nothing is squeezed. Lines marked *Recommendation* are
inferences, not sourced facts.

## 1. What the repo has today

- `ui/src/shell/layoutClass.ts` picks one of `hu5|hu7|hu9|huwide|phone|tablet|desktop` from the
  **window** (aspect ratio first, then height; `?display=` overrides detection because head-unit
  browsers report odd DPIs). It is a device class: right for chrome (rail or bottom bar, rail
  side), wrong for page content. *Recommendation:* rename it `deviceClass`.
- Container queries are already in use: `ui/src/drive/drive.css` (`.dm-cell`, `inline-size`,
  `@container (max-width: 300px)`) and `ui/src/styles.css` (`.gauge`, `size`). ResizeObserver
  is used in `ui/src/components/replay/Chart.tsx`.
- The theme engine spec sets a Chromium 118 floor with a built-in fallback below it
  ([theme engine](../../specs/2026-10-07-theme-engine-design.md)); the head-unit research warns
  that FYT WebViews may lag Chrome ([CAN-bus head units](canbus_headunit.md)).

## 2. CSS container queries

- `container-type: inline-size` contains the inline axis only; `size` contains both, and an
  element with size containment "will collapse" without an explicit size
  ([MDN container-type](https://developer.mozilla.org/en-US/docs/Web/CSS/container-type)).
  Tiles have a fixed box, so `size` is safe on the tile root, not on content-sized children.
- Queries resolve against the nearest ancestor container
  ([MDN guide](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_size_and_style_queries)).
  *Recommendation:* name the tile container (`container-name: tile`) so inner containers such as
  `.gauge` do not shadow it.
- Container units `cqw/cqh/cqi/cqb/cqmin/cqmax` are 1% of the container's dimensions
  ([MDN mirror](https://docs.w3cub.com/css/css_containment/container_queries)); supported from
  Chrome 105, Firefox 110, Safari 16 ([caniuse](https://caniuse.com/mdn-css_types_length_container_query_length_units)).
- Size queries: Chrome 106+ full ([caniuse](https://www.caniuse.com/css-container-queries));
  Baseline since February 2023 ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/container-type)).
  Style queries work only on custom properties and are partial across engines
  ([caniuse](https://caniuse.com/css-container-queries-style)); attribute selectors work
  everywhere.
- Chrome 139+ needs Android 10 and Chrome 138 was the last for Android 8–9
  ([Android Authority](https://www.androidauthority.com/chrome-dropping-support-android-8-9-3571442)),
  so an Android 10 head unit can run current Chrome. WebView updates through Play
  ([Android Police](https://www.androidpolice.com/2015/03/10/android-webview-app-is-out-of-beta-and-ready-to-keep-your-lollipop-device-up-to-date/));
  units without Play may ship a frozen one, which is a bench-test item.
- The Chrome Labs polyfill is in maintenance mode
  ([README](https://github.com/GoogleChromeLabs/container-query-polyfill/blob/f6831ec85e8db047218f8f8807667f1429aba457/README.md?plain=1)).
  Do not depend on it.

## 3. ResizeObserver

- Callbacks run after layout and before paint; changing sizes in them re-runs layout, and loops
  raise "ResizeObserver loop completed with undelivered notifications". The fixes: change sizes
  in `requestAnimationFrame` and skip updates when nothing changed
  ([MDN ResizeObserver](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver)). The
  error is usually benign ([TrackJS](https://trackjs.com/javascript-errors/resizeobserver-loop-completed-with-undelivered-notifications/)).
- *Recommendation:* observe the **tile frame**, whose size comes from the divider, not the page;
  compute the class in a pure function `(w, h, previous) → class`; set state only when the class
  changes; coalesce with rAF while dragging; keep page state above the class switch so a size
  change swaps the view, not the state.

## 4. Precedents: a few discrete classes, content dropped, not scaled

| System | How size is chosen | Classes | Content rule |
|---|---|---|---|
| Material 3 window size classes | width < 600, 600–839, 840–1199, 1200–1599, ≥ 1600 dp; "not intended for isTablet-type logic" | 5 width × 3 height | layout changes per class ([Android](https://developer.android.com/develop/ui/compose/layouts/adaptive/window-size-classes)) |
| Android 12+ widgets | `Map<SizeF, RemoteViews>`, each layout covers a range | developer-defined | separate layouts ([Android](https://developer.android.com/guide/topics/appwidgets/layouts)) |
| Glance `SizeMode.Responsive` | the declared size that fits best; **the smallest if none fits**; Exact risks "UI jumps" | e.g. 3 | discrete layouts ([Glance](https://developer.android.com/develop/ui/compose/glance/build-ui)) |
| iOS WidgetKit | `supportedFamilies`; the view reads `widgetFamily` | small, medium, large, extra large, accessory circular, rectangular, inline | a view per family ([Apple](https://developer.apple.com/documentation/widgetkit/widgetfamily)) |
| watchOS complications | WidgetKit accessory families since watchOS 9 | 4 | a view per family ([WWDC22](https://developer.apple.com/videos/play/wwdc2022/10051/)) |
| Home Assistant sections | 12-column grid, 56 px rows; the card declares rows, columns, minimums and maximums | continuous with minimums | left to the card ([HA](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/)) |
| Grafana | 24-column grid; the panel gets width and height | continuous | left to the panel ([Grafana](https://grafana.com/docs/reference/dashboard)) |
| Windows 11 widgets | the user picks | small, medium, large | small: one piece of information, one target; do not force large into small ([MS Learn](https://learn.microsoft.com/en-us/windows/apps/design/widgets/widgets-design-fundamentals)) |

The common pattern matches the brief: a small fixed set of classes, the component declares which
it supports, each class is its own composed view, and the system falls back to the smallest.

## 5. Content priority

- **Priority+:** show what fits by importance, the rest behind "more"
  ([Brad Frost](https://bradfrost.com/blog/post/revisiting-the-priority-pattern/)); it can hide
  things people need. *Recommendation:* each page ranks its parts; each class shows the top N;
  moving rules remove parts that are not safe first.
- **Intrinsic layouts** inside a class: the RAM grid `repeat(auto-fit, minmax(X, 1fr))`
  ([web.dev](https://web.dev/patterns/layout/repeat-auto-minmax)) and the sidebar pattern
  ([web.dev](https://web.dev/articles/one-line-layouts)) fit continuously without breakpoints.
- **Fluid type:** capped `clamp()` can fail WCAG 1.4.4
  ([Smashing](https://smashingmagazine.com/2023/11/addressing-accessibility-concerns-fluid-type)).
  *Recommendation:* `clamp(<rem floor>, <n>cqmin, <rem cap>)` for hero numbers only; body text
  never goes below its floor, content is dropped instead. Use `tabular-nums` for live values.

## 6. Window managers and dividers

- Android split screen: AOSP `DividerSnapAlgorithm` has snap targets including 1/3, 1/2 and 2/3
  and dismiss targets at the edges
  ([AOSP](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/WindowManager/Shell/src/com/android/wm/shell/common/split/DividerSnapAlgorithm.java));
  apps should work down to 220 × 220 dp
  ([Android blog](https://android-developers.googleblog.com/2016/05/designing-for-multi-window.html)).
- Windows Snap: apps should support a minimum width of at most 500 epx
  ([MS Learn](https://learn.microsoft.com/sv-se/windows/apps/desktop/modernize/apply-snap-layout-menu)).
- React split libraries: react-resizable-panels (widely used, min and max sizes, collapse) and
  Allotment (per-pane minimums, snap to zero)
  ([comparison](https://www.pkgpulse.com/guides/react-resizable-panels-vs-split-js-vs-allotment-2026)).
  *Recommendation:* react-resizable-panels with our own snap targets (1/3, 1/2, 2/3) and a
  "collapse to Badge" target.

## 7. Hosting another app's page in a tile

- Each iframe can cost its own renderer process (one informal measurement: about 17 MB)
  ([dev.to](https://dev.to/pete_gleeson/what-is-an-iframe-3bi2)); Quip saw over 500 MB with five
  frames and moved to one app controlling them ([Quip](https://desktop.quip.com/blog/multi-frame-application)).
- Home Assistant cards are custom elements in one document; Grafana panels are React
  components given width and height
  ([Grafana](https://grafana.com/developers/plugin-tools/tutorials/build-a-panel-plugin)).
- *Recommendation:* our own apps, served from one origin, export **page modules** that the host
  loads into one document; **iframes only for third-party pages**, with the shell posting
  `{sizeClass, w, h}` and the child also observing its own viewport. Tiles share state on one
  origin over `BroadcastChannel`.

## 8. Recommendations

**Implementation:** JavaScript is the source of truth for the class (the shell needs it to pick
a supported size, mount the right view, show the summary value at Badge and Chip, and apply
hysteresis, which CSS cannot). It writes `data-size` on the tile. CSS uses
`container-type: size; container-name: tile` for fine-tuning within a class only, never a second
set of breakpoints.

**Thresholds** (CSS px of the tile's content box; a class needs both width and height):

| Class | Enter upward at | Drop back below |
|---|---|---|
| Badge | anything smaller than Chip | — |
| Chip | 120 × 64 | 108 × 56 |
| Compact | 220 × 140 | 204 × 128 |
| Standard | 360 × 260 | 336 × 244 |
| Expanded | 640 × 420 | 608 × 400 |

- The margins (about 5–8%, at least 12 px) exceed divider jitter and snap overshoot.
- Evaluate from the current class: step down while below its exit size, then up while at or above
  the next enter size. If the page does not support the result, use the largest supported class
  that is no bigger (Glance's rule).
- While dragging, apply classes live (rAF-coalesced); commit snap targets on release.
- Checks, allowing about 48 px of chrome: a full 800 × 480 tile (about 728 × 430) is Expanded;
  half of it is Standard; a third of 1024 × 600 (about 340 wide) is Compact; Android's 220 dp
  multi-window minimum sits at the Compact edge.

**Bench-test items:** container queries and ResizeObserver on the Dudu7's WebView or Chrome;
several PWA installs from one origin; memory with four live tiles and a map.

## Changelog

- 0.1 (2026-10-11): first version, from live research for the MFD model.
