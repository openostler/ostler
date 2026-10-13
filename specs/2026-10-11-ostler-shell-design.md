---
title: "ostler-shell — the library every app bundles: size classes, layouts, window rules, page contract, hosting, moving rules, warnings, soft keys, theme resolver and layout format — design"
area: specs
status: stable
version: 1.9
updated: 2026-10-13
depends_on: [decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, references/research/responsive_tile_sizes.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-theme-engine-design.md, specs/2026-10-11-gateway-settings-design.md, references/design/2026-10/brief/00-direction-mfd.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, specs/2026-10-07-drive-modes-and-editing-design.md]
summary: >
  Approved by the owner on 2026-10-12 ("let's go ahead and build the front end", on receiving the designer's shell UI kit); §18 adopts the designer's 31 answers to the brief's open questions. First drafted 2026-10-11, following the owner's "we'll try and build out the shell". The design of the `ostler-shell` library (repo `openostler/ostler-shell`, package `@openostler/shell`, Apache-2.0) that ADR-0052 (proposed) asks every app to bundle. Scope: no settings screens, no car logic, no connection code; the shell talks to the gateway only through an injected client interface. Public TypeScript API and package layout. Modules: five size classes as a pure function with hysteresis plus a React hook observing the tile frame; the layout model (six presets, a tree one level deep, dividers snapping to a third, a half and two thirds, collapse-to-close with Undo, swap, open beside on the passenger side, right-hand-drive mirroring); the window rules in order (shape, size, overflow to chips); page contract types and validation; the page registry and hosting (same-origin page modules, iframes with postMessage for third parties); moving rules (state from the gateway, locked dividers and editing, a 24 px text floor, effects off, a per-action gate); warnings (caution ring, strip, chime hook, warning takeover of a passenger-side non-instrument tile or a band, ACK, label until clear); the top strip; the soft-key row; ShellInput intent mapping; the theme resolver contract with locked safety tokens; the versioned layout format `ostler.layout/3`; BroadcastChannel messages; performance rules. Testing with Vitest first, Playwright component tests later; build order; open questions referencing ADR-0052 §9.
---

# ostler-shell — design

**Status: approved, v1.0** (the owner, 2026-10-12: "let's go ahead and build the front end"). The visual design is the [shell UI kit](../references/design/2026-10/shell-ui/README.md); §18 records the designer's answers to the brief's open questions, adopted as decided behaviour. It designs the library that
[ADR-0052](../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md) (proposed) asks
every Ostler app to bundle. Where this spec and ADR-0052 differ, the ADR wins; open points are
in §17. Evidence: [responsive tiles research](../references/research/responsive_tile_sizes.md),
the [direction brief](../references/design/2026-10/brief/00-direction-mfd.md).

## 1. Scope

**The shell is** a library, `@openostler/shell`, in the repo
[`openostler/ostler-shell`](https://github.com/openostler/ostler-shell) (Apache-2.0). Whichever
app is open imports it and hosts the tiles (ADR-0052 §2). It holds: size classes, the layout
model and window rules, the page contract and registry, page hosting, moving rules, warnings,
the top strip and soft-key row, ShellInput intent mapping, the theme resolver, the layout
format, and the messages tiles exchange.

**The shell is not:**

- **an app or launcher:** no routes of its own, no install, no home screen;
- **settings:** no settings screens; the gateway owns shared preferences and each app owns its
  own settings (ADR-0052 §6, [gateway settings spec](2026-10-11-gateway-settings-design.md));
- **car logic:** no decoding, no signal store, no VSS meaning beyond paths in a page contract;
- **connection code:** no VISS client, no USB, Bluetooth or network code. It talks to the
  gateway only through a `ShellGateway` interface the host app injects (§3.1).

The shell enforces the safety rules it owns (moving rules, warnings, locked safety tokens); an
app cannot switch them off. The node gate still decides every car action (Constitution).

## 2. Package layout

```
ostler-shell/
├── src/
│   ├── index.ts           public API (named exports only)
│   ├── sizeClass.ts       classes, thresholds, nextSizeClass, fitSupported, refresh rates
│   ├── useSizeClass.ts    React hook: ResizeObserver + rAF, writes data-size
│   ├── layout.ts          presets, tree, snap, swap, close/undo, open beside, mirror, rects
│   ├── windowRules.ts     shape → size → overflow
│   ├── pageContract.ts    manifest types, validatePageManifest, effectiveSizes
│   ├── moving.ts          motion state, action gate, effects and editing locks, text floor
│   ├── warnings.ts        alert reducer, takeover choice, strip item, chime hook
│   ├── theme.ts           ThemeData, resolveTheme, locked safety tokens, built-in Night
│   ├── layoutFormat.ts    ostler.layout/3 types, migrate, JSON Schema
│   ├── gateway.ts         ShellGateway interface (types only)
│   └── (later) registry.ts, host/, input.ts, channel.ts, components/
├── test/ or src/*.test.ts Vitest
└── dist/                  tsc output: ESM + .d.ts
```

ESM only; React 19 is a peer dependency used only by hooks and components. No runtime
dependencies in the pure modules, so apps of any framework can use them.

## 3. Public API (TypeScript)

The pure modules export plain functions over plain data; nothing holds global state. The
first-round surface is listed in each section below; components (`<Shell>`, `<Tile>`,
`<TopStrip>`, `<SoftKeyRow>`) follow owner review.

### 3.1 The gateway client the host injects

```ts
interface ShellGateway {
  motion(cb: (s: MotionState) => void): () => void;          // moving, idling, parked, unknown
  preferences(cb: (p: SharedPreferences) => void): () => void; // driverSide, units, theme, …
  loadLayouts(): Promise<unknown>;                            // ostler.layout/3 document
  saveLayouts(doc: LayoutDocument): Promise<void>;
  alerts(cb: (e: AlertEvent) => void): () => void;            // raise, clear
  commands(cb: (c: ShellCommand) => void): () => void;        // Ostler Controls: ack, next-layout, …
  connection(cb: (c: ConnectionStatus) => void): () => void;  // for the connection chip
  vehicle(cb: (v: VehicleChip | null) => void): () => void;   // the connected car's label
}
```

Every value is the gateway's; the shell caches nothing but the last value for rendering.

## 4. Size classes

- **Classes:** `badge < chip < compact < standard < expanded`, thresholds exactly as research
  §8 and ADR-0052 §3, in CSS px of the tile's content box; a class needs both width and height:

| Class | Enter at (w × h) | Exit below (w × h) |
|---|---|---|
| badge | always | — |
| chip | 120 × 64 | 108 × 56 |
| compact | 220 × 140 | 204 × 128 |
| standard | 360 × 260 | 336 × 244 |
| expanded | 640 × 420 | 608 × 400 |

- **`nextSizeClass(w, h, prev?)`** (pure): start from `prev` (or `badge`); step down while
  `w < exit.w || h < exit.h` of the current class; then step up while `w ≥ enter.w && h ≥
  enter.h` of the next class. Without `prev` this is the plain enter table.
- **`fitSupported(cls, supported)`**: the largest supported class no bigger than `cls`, else
  the smallest supported (Glance's rule); `null` if the list is empty.
- **Badge and Chip are drawn by the shell** from the page's summary (icon, name, one value)
  unless the page lists them to draw its own (`effectiveSizes`). So a page that does not fit
  falls to a chip, never squeezed into a bigger view.
- **`useSizeClass(ref, { supported })`** observes the **tile frame** (sized by dividers, not
  the page) with `ResizeObserver`, coalesces with `requestAnimationFrame`, sets state only when
  the class changes, and writes `data-size` (the fitted class) and `data-size-raw` on the
  element. CSS fine-tunes inside a class with `container-type: size; container-name: tile`.
- Page state lives above the size switch, so a class change swaps the view, not the state.
- While a divider is dragged, classes apply live (rAF); snap targets commit on release.

## 5. Layout model

- **Presets:** `full`, `halves`, `twoThirds`, `mainPlusTwo`, `threeColumns`, `quad`
  (`buildPreset(id, tileIds)`).
- **Tree one level deep:** a root split (`axis: "row" | "column"`, `sizes` summing to 1) whose
  children are tile ids or one group (a split of tile ids). Tiles never nest; groups never
  nest. Main + two is `row[main, column[a, b]]`; Quad is `row[column[a, b], column[c, d]]`.
- **Stored driver side first.** A layout is stored as if the driver sat on the left; the start
  of a row is the driver side, the end the passenger side. `mirror(tree, driverSide)` reverses
  every row when the car is right-hand drive (driver side from the gateway's car profile).
- **Dividers:** `snapRatio(r)` snaps to ⅓, ½ or ⅔ within 0.04 (configurable); `moveDivider`
  sets the boundary between two siblings. On release, a tile below its minimum along the axis
  (Compact's exit size: 204 px wide or 128 px tall) **closes**, with Undo.
- **Close with Undo:** `closeTile(layout, id, now)` returns the new layout and an undo record
  (the previous layout and an expiry, 10 s by default); `undoClose(record, now)` gives the
  previous layout back while not expired. The last tile never closes. A group left with one
  tile collapses into its parent; sizes renormalise; if the main tile closes, the largest
  remaining tile becomes main.
- **Swap:** `swapTiles(layout, a, b)` swaps two tiles' pages (drag a label onto a tile);
  `swapAcross(layout, path)` swaps the two sides of a divider (double-tap).
- **Open beside:** `openBeside(layout, source, page, newId, now)` inserts the new tile on the
  passenger side of `source`, sharing the source's share, linked to it (beside the whole column
  when the source sits in one); at four tiles it replaces the nearest passenger-side tile's page
  instead (with Undo).
- **Geometry:** `computeRects(tree, w, h, gap)` gives each tile's rectangle.

## 6. Window rules (in order)

`applyWindowRules({ width, height, layout, sizes, previous, driverSide })` returns per-tile rectangles,
size classes (raw and fitted), the chip list and the orientation:

1. **Shape:** a portrait window (height > width) turns every split's axis (rows become columns).
   In landscape, if the tile area is under about 320 px tall and the layout stacks tiles, all
   tiles go in one row, each keeping its share of the area. (This reads the ADR's "320 px of
   tile height" as the whole area's height, as the brief words it.)
2. **Size:** each tile's class from `nextSizeClass` with its previous class, then
   `fitSupported` against the page's effective sizes.
3. **Overflow:** while any non-chip tile is below Compact, the smallest non-main tile leaves
   the tree and becomes a chip (ties: the one nearest the passenger edge). Chips sit in a chip
   column on the passenger side in landscape (128 px wide) or a chip row along the bottom in
   portrait (72 px tall); the rules re-run. The main tile always keeps the space.
   Tapping a chip swaps its page with the main tile's.

Tile limits therefore come from pixels, not device type (ADR-0052 §1).

## 7. The page contract

```ts
interface PageManifest {
  contract: 1;
  app: string; id: string; title: string; icon: string;     // icon: Material Symbols name
  sizes: SizeClass[];                                        // views the page draws
  summary: { label: string; signal?: VssPath; unit?: string };
  parts: { id: string; priority: number; from?: SizeClass; hideWhileMoving?: boolean }[];
  actions: { id: string; label: string; moving: MovingSafety; kind?: ActionKind }[];
  softKeys?: { slot: 1 | 2 | 3 | 4 | 5; label: string; action: string }[];
  data: { uses: VssPath[]; requires: VssPath[] };
  links?: { page: PageRef; kind: "open-beside" | "shared-cursor" }[];
  instrument?: boolean;                                      // never covered by a warning
  host: { kind: "module"; entry: string } | { kind: "iframe"; url: string };
}
type MovingSafety = "safe" | "confirm" | "not-while-moving";
```

- **Parts** rank 1 (most important) upwards; each class shows the parts it can fit, lowest
  priority dropped first; `hideWhileMoving` parts go first while moving.
- **Soft keys** are up to five, with stable slots; each names one of the page's actions, so its
  moving safety comes from that action.
- **`validatePageManifest(x)`** returns `{ ok: true, manifest }` or `{ ok: false, errors }`:
  known classes, at least one size, unique part, action and slot ids, soft keys naming existing
  actions, `requires ⊆ uses`, VSS paths shaped `Vehicle.…`, and a host entry.
- The shell never mounts a page at a class outside its effective sizes.

## 8. Page registry and hosting

- **Registry:** the host app registers the pages it can load (`registerPage(manifest, loader)`);
  apps on the same origin publish their manifests at a known path the gateway lists.
- **Page modules (own apps, same origin):** `loader()` returns a React component (or a custom
  element name) that receives `{ sizeClass, width, height, motion, tile }`. Loaded lazily, one
  document.
- **Iframes (third-party pages only):** the shell posts
  `{ type: "ostler.size", v: 1, sizeClass, w, h }` to the frame's origin on every class change
  and accepts only `ostler.*` messages from that origin. The child also observes its own
  viewport. Sandboxed; no car actions except through the gateway's own permission flow.
- **Unrenderable** (not installed, contract version mismatch, blocked, failed to load): a chip
  that opens the page's own app.

## 9. Moving rules

- **State from the gateway:** `moving`, `idling`, `parked` or `unknown`; `unknown` counts as
  moving (ADR-0044's unknown-speed rule).
- **`actionGate(action, state)`** → `{ allowed, confirm, reason? }`; `isActionAllowed` is its
  boolean. `safe` is always allowed; `confirm` needs an on-screen confirm while moving;
  `not-while-moving` is refused while moving with "Not while moving". Some kinds are always
  `not-while-moving` whatever the page declares: `typing`, `edit`, `layout-edit`,
  `clear-faults`, `actuator-test`, `video` (ADR-0052 §5, ADR-0033).
- **`layoutEditAllowed(state)`**: dividers, drag and Save layout only parked or idling; saved
  layout switching and chip swaps stay one tap at any speed.
- **`effectsAllowed(state)`**: blur, glow and texture only parked or idling.
- **Text floor:** `minTextPx(state)` is 24 px while moving (ADR-0052 §9 decision 1, recommended)
  and 12 px otherwise (visual spec decision 11's phone value; apps may raise it);
  the resolver writes it as `--ostler-text-min`. Targets grow by the visual spec's Moving sizes.
- Settings screens are the apps'; the shell exposes `canChangeSettings(state)` for their
  "Park to change" pill.

## 10. Warnings

- **Model:** `alertsReducer(state, event)` over events `raise`, `ack`, `clear`. Each alert has
  `severity: "caution" | "warning"`, a plain-words title and one instruction, and optionally
  the tile it concerns. Phases: `unacked` → `acked` → removed on `clear`.
- **ACK and repeats:** `ack` without an id takes the takeover warning, else the newest unacked
  caution. A repeated raise of a known alert keeps its ACK; an escalation to warning re-arms it.
- **Caution:** rings the tile it concerns (`data-alert="caution"`), lights the strip, chimes.
  Never takes over.
- **Warning:** `pickTakeover(tiles, driverSide)` picks the tile nearest the passenger edge that
  is not an instrument page; if that tile is a chip, or none qualifies, the warning shows as a
  **band** (bottom in landscape, passenger side in portrait). It never covers an instrument
  page. The takeover stays until ACK; the strip's WARNING label stays until `clear`.
- **Strip:** `stripItem(state)` shows one item: unacked warnings, then unacked cautions, then
  acked warnings, newest first.
- **Chime hook:** `chimeFor(prev, event)` returns the severity on a new raise, else `null`; the
  host plays its sound.
- **Select acknowledges only while a warning is unacked** (`ackOnSelect(state)`, ADR-0052 §4a).

## 11. Top strip and soft-key row

- **Top strip, from the driver's side outward:** layout switcher (saved layouts, Save this
  layout, Manage layouts), connection chip (gateway's text; tap opens the gateway app), warning
  strip, settings entry (opens the host app's settings; shared ones link to the gateway),
  vehicle chip (the connected car; switching is the gateway's). No clock.
- **Soft-key row:** drawn from the focused tile's `softKeys`, slots fixed so they work without
  looking; a key whose action the gate refuses shows its reason ("Not while moving") and does
  nothing. Hidden when no page with soft keys has focus or the user turns the row off.
- **Tile label menu:** Swap page · Page settings (the page's app) · Open beside · Close.

## 12. ShellInput mapping

Intents per the [ShellInput spec](2026-10-07-shell-input-design.md), plus ADR-0052 §4a's
`softkey-1`…`softkey-5`, `next-layout` and `ack`. Gateway `commands` (Ostler Controls) arrive as
the same intents.

| Intent | Effect |
|---|---|
| `ok` | ACK while a warning is unacked; else activate the focused item |
| `ack` | ACK the takeover warning, else the newest unacked caution |
| `softkey-n` | the focused page's slot n through `actionGate` |
| `next-layout` | switch to the next saved layout (allowed while moving) |
| `focus-next` | move focus to the next tile in a stable order (driver side first) |
| `up` `down` `left` `right` `back` `menu` `mark` | as ShellInput, inside the focused tile |

No intent changes the car beyond acknowledging a warning; confirmations stay on screen with
Cancel focused (ShellInput §7).

## 13. Theme resolver

- **Contract:** `resolveTheme(theme, { moving, mode })` → `{ id, mode, vars }`, where `vars` are
  CSS custom properties (`--ostler-bg`, `--ostler-surface-1..3`, `--ostler-text-1..2`,
  `--ostler-accent`, `--ostler-on-accent`, `--ostler-radius`, `--ostler-blur`, `--ostler-glow`,
  `--ostler-texture`, `--ostler-bg-image`, fonts and weights). `theme` is one `ThemeData` or a
  `{ day, night }` pair; `mode` picks one.
- **Theme data** follows the designer's theme entries (`bg`, `s1`–`s3`, `tx`, `t2`, `acc`, `on`,
  `r`, `blur`, `glow`, `tex`, `bgImg`, fonts, and `…Safe` opaque variants); the themes
  themselves live in the platform repo, and the shell ships only a built-in **Night**.
- **While moving:** `…Safe` surfaces, no blur, glow, texture or background image, number weight
  at least 500, `--ostler-text-min: 24px`.
- **Locked safety tokens:** `--ostler-ok`, `--ostler-caution`, `--ostler-warning` and
  `--ostler-text-min` come from the shell's constants (a dark and a light set chosen by the
  background's luminance), never from theme data. Custom CSS passes the theme engine's
  sanitiser and render check ([theme engine spec](2026-10-07-theme-engine-design.md)); safety
  icons are the shell's.
- `applyTheme(el, resolved)` writes the variables on an element.

## 14. Layout format, `ostler.layout/3`

Successor to `ostler.layout/1` (drive-modes spec §4) and `/2` (parked launcher spec).

```json
{ "format": "ostler.layout/3", "updated": "2026-10-11T10:00:00Z", "active": "commute",
  "layouts": [ { "id": "commute", "name": "Commute", "screen": null,
    "tree": { "axis": "row", "sizes": [0.6667, 0.3333], "children": ["t1", "t2"] },
    "pages": { "t1": { "app": "logs", "page": "chart" }, "t2": { "app": "gateway", "page": "car" } },
    "main": "t1", "links": [["t1", "t2"]], "switchOn": ["car-started"] } ] }
```

- Stored and synced by the gateway in the car profile (gateway settings spec §3) through
  `ShellGateway.loadLayouts/saveLayouts`; the app keeps only a cache.
- `LAYOUT_SCHEMA` (JSON Schema 2020-12) is exported; `migrate(doc)` accepts `/3`, and will
  migrate `/1` and `/2` (stubbed in the first build: refused with a clear error).
- `switchOn` triggers: `car-started`, `low-range`, `parked` (ADR-0052 §9 decision 5).

## 15. Tile messages and performance

- **BroadcastChannel `ostler.shell`** (same origin): `{ v: 1, type: "cursor", link, from, at }`
  (shared cursor: a time or a fault id), `{ v: 1, type: "open-beside", from, page }`,
  `{ v: 1, type: "focus", tile }`. Unknown types and versions are ignored.
- **Refresh by class:** Badge and Chip at most every 2 s, Compact every 1 s, Standard and
  Expanded live (`refreshIntervalMs(cls)`); pages receive it as a prop.
- **One live map:** only the main tile may run a live map; others show a still or a chip.

## 16. Testing and build order

**Testing.** Vitest for every pure module: the research §8 checks (728 × 430 → Expanded;
364 × 430 → Standard; 340 × 552 → Compact), hysteresis both ways across each margin, snap and
collapse, window rules per preset and orientation, overflow keeping main, the action gate per
state and kind, takeover choice and band fallback, theme locking. The hook with a fake
`ResizeObserver` in jsdom. Later: Playwright component tests for dragging, focus order and
the warning takeover; a bench run on the Dudu7 (four tiles, one map). CI: `npm run check`
(lint, typecheck, test) and `reuse lint`.

**Build order.**

1. Pure logic and the hook (this round): size classes, layout, window rules, page contract,
   moving, warnings, theme resolver, layout format.
2. `<Shell>`, `<Tile>` and the registry with page modules, on recorded fixtures (UX first).
3. Top strip, soft-key row, ShellInput mapping, warnings UI.
4. Iframe host and BroadcastChannel.
5. Drag-and-drop editing and automatic layout switching; first app bundles it.

## 17. Open questions

1. **Text floor 22 or 24 px** (ADR-0052 §9.1): built as 24, one constant.
2. **Module or iframe boundary** (§9.2): built as modules for own apps, iframes otherwise.
3. **Shared preferences in the gateway** (§9.3): the `ShellGateway` interface assumes yes.
4. **Gateway app repo name** (§9.4): no effect on the shell.
5. **Automatic switching triggers** (§9.5): the format allows the three recommended.
6. **New here:** the collapse minimum (Compact's exit size), the chip column and row sizes and
   placement, Undo's 10 s window, the one-row reading of the 320 px rule (§6), and whether
   Badge and Chip are always shell-drawn.

## 18. Decided by the UI kit (2026-10-12)

The designer's answers to the [shell brief](../references/design/2026-10/brief/10-shell-brief.md)
open questions, adopted as decided behaviour. Tokens, thresholds and colours come from the
kit's `tokens.json`.

**A. Frame and layout**

1. **Open beside while moving:** one tap when it adds no tile (it replaces the passenger tile,
   with Undo). Close stays parked only.
2. **Soft keys on 5″:** the row overlays the bottom 48 px of the focused tile for 4 s after a
   wheel key or a tap; the tile keeps its class. On 7″ and larger it counts against the tile
   area.
3. **Compact label while moving:** the page icon and chevron; the name stays in the menu and
   for screen readers.
4. **Portrait:** the main tile at the top; the driver side still sets soft-key order and chip
   side in landscape.
5. **Too many chips:** the last chip becomes "+n" and opens a list sheet; nothing is dropped.
6. **"Show sizes":** a designer and debug aid, off by default, under About in the gateway's
   shared settings, never shown while moving.
7. **Links:** a visible link mark; tapping it offers Unlink. Links also end when either tile
   is swapped or closed.

**B. Top strip and menus**

1. **No gateway or no car:** the vehicle chip is hidden; the connection chip says "No
   gateway".
2. **Open beside:** a page action, allowed while moving when it replaces a tile; adding a tile
   waits until parked.
3. **Two layouts on one trigger:** blocked; picking a taken trigger asks "Move it from
   Commute?".
4. **Automatic switch while moving:** the strip name changes and a text-only toast with Undo
   shows for 4 s; no sound.
5. **Merged chip:** the status word whenever not connected; the car name only when connected.
6. **Layout switcher while moving:** six rows, in the user's order from Manage layouts.
7. **Saved icons:** a tiles badge for layouts and a square badge for single pages, bottom
   right.

**C. Driving, warnings and input**

1. **Motion unknown:** the moving rules apply; the strip shows an outlined "Motion unknown"
   with a help icon instead of the lock.
2. **Focus order:** the driver-side column first, top to bottom, then the passenger side, then
   the strip.
3. **No soft keys on the page:** on 5″ the row is hidden (overlay only); on 7″ and up the row
   stays with the owner tag and empty slots, so tiles never jump.
4. **Soft-key owner:** a tag at the driver end of the row with the page icon and name in the
   focus-ring colour.
5. **Warning band on a portrait phone:** across the bottom.
6. **Tapping a caution pill:** opens the alerts list; each row opens its page beside, or in
   place if already on screen.
7. **Several alerts:** "+n" in the strip; the alerts list is one tap from the pill and on a
   long Select.
8. **Long Select with no warning:** opens the active alerts list, or shows "No alerts" in the
   strip for 2 s.
9. **Warnings while another app is in front:** Ostler Controls shows the band over that app;
   cautions only chime and light its strip.
10. **Refusal for a wheel action off screen:** a text-only toast at the top for 4 s, for
    example "Clear faults: not while moving".

**D. States and hand-offs**

1. **Dismissed banner:** stays away until its condition changes; it returns if the condition
   comes back.
2. **Banner on 480 px-high screens:** overlays the top of the tiles, so no tile drops a class.
3. **Banner when moving starts:** hidden at once; the chip carries the state.
4. **"Last seen":** the time today, "Yesterday 18:10", then a date, "2 Oct 18:10"; never
   relative times.
5. **"Get more apps":** in the apps menu when only the gateway is installed, not in the layout
   switcher.
6. **Third-party mark at Badge:** a 14 px puzzle icon in the corner; the full text is in the
   label menu.
7. **Stale tile:** "Last seen" in the label; the page dims its values.

**Kit values the build uses:** strip 48 px at 480 px high, 56 px by default, 52 px on a phone;
label row 42 px parked and 52 px moving; tile gap 10 px, radius 20 px (Badge 14 px); a
per-page Expanded minimum (Diagnose and Logs 760 px wide); fonts Figtree and Material Symbols
Rounded, self-hosted.

## 19. Decided: edit mode, the layout carousel and the D-pad (ADR-0052 v0.7)

Approved by the owner on 2026-10-12. Where this section conflicts with §5, §11, §12 or §18, this
section wins:

- **§5 dividers and §18 A.1, A.5:** no permanent divider bars. Resizing, moving, adding,
  splitting (along the longer side) and removing happen in a parked-only, press-and-hold edit
  mode with grabbable edges, a page tray, a live snap preview with class labels and haptics, a
  non-drag path driven by the D-pad cursor, and Done. The foundation's layout operations
  (`moveDivider`, `releaseDivider`, `splitToEdge`, `swapPages`) are reused; a `splitTile` along
  the longer side is added.
- **§11 top strip and §18 B.2, B.6:** the layout dropdown and the Manage layouts sheet move into
  edit mode; the strip shows layout dots and, briefly, the layout's name. Layouts switch by a
  carousel: swipe on the strip or screen edge (parked only), the D-pad cursor crossing the
  screen edge, or a trigger; no wrap-round.
- **§11 soft-key row:** optional, a gateway shared setting (on by default on head units, off on
  phones and desktops). When off, the focused page's soft keys are in its label menu and on the
  D-pad.
- **§12 and §18 C.2 focus:** the wheel is a D-pad. Arrows move focus spatially to the nearest
  tile in that direction (replacing "driver-side column first"); up from the top row reaches the
  strip; left or right off the screen edge pages to the adjacent layout. `focus-next` stays for
  keyboards and a single "next" key. In edit mode arrows move the selection.
- **Widgets:** a Chip or Compact tile with "Show frame" off.
- **Native Android extras:** only where the Gateway Android app hosts the shell, as an option.

## 20. Build spec: the shell session implementation guide (ADR-0052 v0.8)

Decided by the owner on 2026-10-13. The designer's
[implementation guide](../references/design/2026-10/shell-session/IMPLEMENTATION.md) is the
build spec for the shell; where it differs from §1 to §19 it wins. The foundation's layout model
moves to the guide's (fractional rects in a guillotine tree per page, pages, Wide and Single
versions, stacks, spans, styles); size classes use dp with 16 dp hysteresis; the top strip and
the soft-key row are removed; focus, alerts, carousel and edit mode follow the guide's sections
5 to 10.

## 21. Owner rulings on the build guide after the safety review

Decided by the owner on 2026-10-13 ("yes to all"), after an adversarial review of the v2 shell
against the guide's moving and alert rules found 29 gaps (5 critical). Where these differ from
the [implementation guide](../references/design/2026-10/shell-session/IMPLEMENTATION.md), they
win.

1. **A warning on its own instrument tile** (the designer's ruling, which replaces the owner's
   interim ruling that the takeover covers the tile). The instrument shows the warning in place
   and its main value always stays visible: a red warning ring around the tile, a red ACK bar
   inside the bottom of the tile holding the message, and the app turns its own value red. If the
   tile is too small for the bar (Compact height under 200 dp, Chip or Badge), the instrument
   gets the ring and tag, and the takeover or band goes to a passenger-side non-instrument tile.
   An instrument's values are never covered. The tokens are in `alerts.instrumentWarning` of
   `ostler-shell-tokens.json`: the bar is 68 dp tall (78 while moving) and takes space from the
   page, which is inset by the bar's height and reflows; the bar never overlays page content.
2. **The alert tab is 60 dp tall while moving.** The guide's 44 dp tab stays when parked. While
   moving, every touch target, the tab included, is at least 60 dp (`space.touchMinMoving`). This
   also lifts the tokens' ACK buttons that are 56 dp while moving (`alerts.takeover.ack.height`
   and `alerts.instrumentWarning.bar.ack.heightMoving`) to 60 dp.
3. **Alert colours pass contrast in every theme.** A contrast check for the locked warning and
   caution colours (ring, tag, tab, takeover text) against each theme's surfaces runs in CI,
   in both the Night and Day versions. Themes that fail are tuned until they pass, even where
   that changes the designer's palette. The locked alert colours themselves don't change.

The review's fixes follow the guide's rules as written: unknown motion (missing, stale, an
unreachable Gateway, a new host, or a value such as `idling` that the shell doesn't know) counts
as moving; every warning shows; a stale value never looks fresh; and alerts stay above edit
mode.

The designer's other rulings on the same day, from the visual check of the built shell
([designer questions](../references/design/2026-10/shell-session/QUESTIONS.md) 2 to 6), settle
frames that disagreed with the guide:

- **Right-hand drive mirrors the whole layout, tiles included,** so the main tile is on the
  driver's side (X-18 was wrong).
- **The pinned column repeats on every page,** in split screen too (L-10 was wrong).
- **In portrait the pinned row is 360 dp,** the same token along the long axis (L-13 was wrong;
  the strip is gone).
- **The delete circle sits at the bottom centre of the driver's half,** as the token says (C-09
  was wrong). Later replaced by the owner: the bottom centre of the screen (below).
- **All text is at least 24 dp while moving, labels included.** The tokens' 18 dp moving label
  was an error; `ostler-shell-tokens.json` now gives 24.

The owner's rulings on edit mode after trying the built shell (2026-10-13), which win over the
guide's §4 and §6:

- **Lift after 250 ms.** In edit mode a tile lifts when the finger moves after a 250 ms hold (half
  the 500 ms hold). A quicker press and move is a swipe; a tap selects; holding still 500 ms and
  letting go opens window style.
- **The long press carries its tile.** The long press that opens edit mode lifts the tile under the
  finger at once, its ghost under the finger with no further movement; moving drags it, and
  letting go where it was drops it back with nothing changed.
- **The lifted tile is a ghost:** half opacity with an outline, fainter still over a shape, More
  or the delete circle, so they show through it.
- **A stack keeps its slot.** Stacking onto a tile leaves the stack in that tile's slot; the slot
  the lifted tile left stays, empty with its +. In edit mode a stack shows its badge rail.
- **Resizing never removes a tile.** The edge stops at the smaller tile's minimum; removing is the
  delete circle's (and Remove's) alone.
- **A page-border edge drags in to make space.** Any tile's edge on the page's border, a lone
  tile's included, can be dragged in: the tile shrinks and an empty slot opens on that side,
  offering + (a space smaller than a Chip snaps back). **Space you make stays:** saved layouts
  keep a page's empty slots as its `space` (fractional rects in `ostler.layout/3`, optional),
  and the normal screen leaves them blank.
- **The shapes row stays once reached:** after the lifted tile has been over it, the row stays for
  the rest of the drag.
- **Space dragged back goes:** an empty slot dragged smaller than a Chip loses its + and closes on
  release, its neighbour taking the room (in the drag that made it or a later one).
- **The delete circle is on every screen, a ghost, at the bottom centre:** 5″ and phones have it
  too; it sits at the bottom centre of the screen whatever the drive side (replacing the
  designer's ruling 5, the driver's half), at half opacity until a tile is over it.
- **Pages claim only where they mark it:** a page can mark the elements that claim its gestures
  (`data-claims-area`, such as a map's canvas); then the rest of the page swipes the carousel. The
  tile's label row never claims.
- **Phones page sideways:** a phone (portrait, one page, no pinned column) pages its carousel
  left and right, so a sideways swipe pages while vertical drags stay the page's, for lists and
  maps (L-13's vertical stacking is for portrait screens that show two pages).
- **In edit mode a stack's preview is its slot's size,** not shrunk to a Chip.
- **No swapping in edit mode; tiles move out of the way, as on Android** (owner, 2026-10-13,
  replacing the drag-onto-a-tile swap). Over a tile's outer band the layout previews the move
  after a short settle: the lifted tile's old slot closes, it goes in beside that tile on the
  finger's side, and the other tiles slide aside; letting go commits what the preview showed.
- **Stacking is Android's folder gesture:** holding the lifted tile over another tile's centre
  arms a stack (the target shrinks a little with a ring behind it); letting go stacks them, and
  a quick pass over a tile does nothing. In edit mode an app's badge can be dragged out of a
  stack to unstack it.
- **Caution strokes on light themes are the darker amber** (owner and designer, 2026-10-13): on
  themes with a light background, and contrast themes, rings, tile borders, the outlined tab,
  bordered page dots and stack badges use `cautionText` (#8a5a00 on Day; 6.2:1 on white), and
  fills keep `caution`. The token is `ring.caution.colorOnLight`.
- **Every settings row opens its page,** the theme page re-theming the shell live; a page
  not yet designed says so rather than leaving a dead tap.
- **Full screen's restore badge comes first:** the top of a side rail, the left of a bottom rail,
  so it never moves (the guide's §7 said last).

## Changelog

- 2026-10-11 — v0.1, draft: first design of the library, from ADR-0052 v0.4.
- 2026-10-12 — v1.0, approved by the owner ("let's go ahead and build the front end"); §18 adopts the designer's answers from the shell UI kit.
- 2026-10-12 — v1.1: §19 records the proposed edit mode and layout carousel (ADR-0052 v0.6), pending the owner; §1 to §18 unchanged.
- 2026-10-12 — v1.2: §19 decided by the owner (ADR-0052 v0.7), adding the D-pad cursor that pages to the adjacent layout off the screen edge, and the optional soft-key row.
- 2026-10-13 — v1.3: §20 makes the designer's implementation guide the build spec (ADR-0052 v0.8).
- 2026-10-13 — v1.4: §21 records the owner's rulings after the safety review: a warning covers its own instrument tile until the designer rules, the tab is 60 dp while moving, and a CI contrast check tunes themes for the alert colours.
- 2026-10-13 — v1.5: §21 takes the designer's rulings: an instrument shows its own warning in place (ring, an ACK bar inside the tile, the value turned red), falling back to the ring and tag with the takeover elsewhere on small tiles; RHD mirrors the tiles; the pinned column repeats on every page and is 360 dp in portrait; the delete circle sits in the driver's half; moving labels are 24 dp. The designer's tokens add `alerts.instrumentWarning`; the 56 dp moving ACK buttons are lifted to 60 dp by ruling 2.
- 2026-10-13 — v1.6: §21 records the owner's edit-mode rulings: a 250 ms lift, the long press carrying its tile, the ghost, stacks keeping their slot, no removal by resize, page-border edges making space that saved layouts keep, and full screen's restore badge first.
- 2026-10-13 — v1.7: §21 adds the owner's later edit-mode rulings: the shapes row stays once reached, space dragged back goes, the delete circle on every screen as a ghost at the bottom centre, and pages claiming only where they mark it.
- 2026-10-13 — v1.8: §21 adds that phones page sideways, and that a stack's edit-mode preview is its slot's size.
- 2026-10-13 — v1.9: §21 replaces swapping with Android-style move-aside and folder-style stacking, takes the darker amber for caution strokes on light themes, and requires every settings row to open its page.
