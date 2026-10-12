---
title: "Ostler shell implementation guide (designer, 13 October 2026) — architecture, dp units, page fitting, layout model, page contract, tiling engine, carousel, edit mode, stacks, focus, alerts, moving rules, Android integration, build order and acceptance checks"
area: references
status: stable
version: 1.0
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/README.md, references/design/2026-10/shell-session/REVIEW.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md]
summary: >
  The designer's implementation guide for the shell session (13 October 2026), saved as delivered with frontmatter added; the owner adopted it as the build spec ("use this, it has a full implementation guide"). Sixteen sections: architecture (layout, tiling, carousel, edit, focus, alerts, motion, theme, contract; PWA and Gateway-hosted runtimes behind host.capabilities); dp units; size classes with 16 dp hysteresis; fitPages (720 dp pages, 360 dp pinned column from 12 inches, up to three pages); the persisted layout model (fractional rects, guillotine tree, Wide and Single versions, stacks, spans, styles, triggers); the page contract; the tiling engine (snap anchors, limits, shapes, drag targets with slide-swap, stack, edge zones, edge paging and delete circle; the half rule on small screens); carousel and gesture arbitration; the edit-mode state machine; stacks and full screen; the two-level focus engine; alerts (message, routing, layering, tab and card, audio, Android channels); moving rules; no top strip; Android integration; persistence and sync; accessibility; build order; acceptance checks.
---

# Ostler shell: implementation guide

Companion to `README.md` (the design brief). This guide says **how** to build it. All sizes are in **dp**. The frame IDs (C-xx, A-xx, V-xx, L-xx, W-xx) refer to `Ostler Shell System.dc.html` and the section files.

---

## 0. Architecture

```
ostler-shell (library, bundled by every app)
├─ layout/      layout model, page fitting, size classes, rect solver
├─ tiling/      tile host, resize, drop zones, swap, stack, span
├─ carousel/    page pager, dots, gesture arbitration
├─ edit/        edit mode state machine, zoom-out, picker, shapes
├─ focus/       two-level D-pad focus engine
├─ alerts/      alert router, card/tab/ring/takeover renderers, audio
├─ motion/      moving / parked / unknown state, rule enforcement
├─ theme/       theme resolver (see the themes pack)
└─ contract/    page contract types (what apps implement)
```

- **Separation of concerns:** the shell owns the window, the tiles and attention routing. Apps own the pixels inside their page. The shell never draws inside a page.
- **Who talks to whom:** apps talk only to the Gateway. The shell gets alerts and motion state from the Gateway too.
- **Two runtimes, one codebase:**
  - In the **PWA**, it works with the browser and window size only.
  - Hosted in the **Gateway Android app**, it can also host Android widgets, use system notifications and TTS, and read physical keys.
  - Gate each capability with `host.capabilities`.

---

## 1. Units, size classes, pages

### 1.1 dp everywhere
`dp = px / devicePixelRatio`. On Android, use the platform dp. Never compare raw px.

### 1.2 Size classes (per tile, from its own box)

| Class | Rule (w × h, dp) |
|---|---|
| Expanded | w ≥ 640 and h ≥ 420 (page may raise min width, e.g. Diagnose/Logs 760) |
| Standard | w ≥ 360 and h ≥ 260 |
| Compact | w ≥ 220 and h ≥ 140 |
| Chip | w ≥ 120 and h ≥ 64 |
| Badge | otherwise |

- Add **hysteresis of 16 dp** at each boundary so dragging doesn't flicker between classes.
- A page declares which classes it supports. If it doesn't support the computed class, use the largest supported class that's smaller. If even that doesn't fit, show the fallback chip ("Needs a bigger tile").

### 1.3 Page fitting
```ts
const PAGE_MIN_W = 720, PIN_W = 360, SEAM = 24;
function fitPages(win: Size, opts: {pinAllowed: boolean}) {
  const pin = opts.pinAllowed && diagonalInches(win) >= 12;
  const avail = win.w - (pin ? PIN_W + SEAM : 0);
  const n = Math.max(1, Math.floor((avail + SEAM) / (PAGE_MIN_W + SEAM)));
  const pageW = (avail - (n - 1) * SEAM) / n;   // spare width widens pages
  return { pin, n: Math.min(n, 3), pageW, pageH: win.h };
}
```
- **Portrait:** use the same function on the window height, so pages stack vertically.
- **Diagonal:** the physical size comes from the host (head-unit profile) where available. Otherwise use window dp: ≥ 1600 dp wide counts as large.

---

## 2. Layout model (persisted, synced by the Gateway)

```ts
type PageRef = { app: string; page: string; params?: Json };
type TileStyle = { frame: 'normal'|'transparent'|'none'; corners: 'theme'|'rounder'|'square' };
type Tile = {
  id: string;
  content: PageRef | { stack: PageRef[]; active: number; badgeEdge?: Edge };
  rect: { x: number; y: number; w: number; h: number };   // fractions 0..1 of its page (or span)
  span?: number;                                            // pages spanned, default 1
  style?: TileStyle;
};
type Page = { id: string; tiles: Tile[] };
type LayoutVersion = { pages: Page[]; pinned?: Tile };
type Layout = {
  id: string; name: string; car: string; screen: string;   // per car, per screen class
  wide?: LayoutVersion;        // used when fitPages().n >= 2
  single: LayoutVersion;       // used when n === 1; generated on first need
  triggers?: ('carStart'|'lowRange'|'parked')[];
  updatedAt: string;
};
```

### Rules
- **Rects are fractions of the page**, so a page can get wider without changing shape.
- **Every page is fully tiled:** the rects cover the page exactly, with no gaps and no overlaps. Validate this on every edit.
- **Never write one version from the other.** Editing while `n === 1` changes `single`; editing while `n >= 2` changes `wide`.
- **Generating `single` from `wide`** the first time it's needed:
  1. Keep the pinned tile on the driver side as a full-height column (300 dp).
  2. Rank the remaining tiles: spanning tiles, then instruments, then tiles with an active caution or warning, then most recently focused.
  3. Fill the first page with the best shape (see 4.2) that keeps every tile at Compact or larger. Spill the rest, in rank order, onto new pages.
- **Gaps:** 10 dp between tiles, 10 dp margin at the edges of the window.

---

## 3. Page contract (what each app implements)

```ts
interface PageDef {
  id: string; title: string; icon: string;
  sizes: SizeClass[];                         // supported classes
  minExpandedW?: number;                      // e.g. 760
  instrument?: boolean;                       // driver-facing gauge (Speed, Attitude, …)
  moving: 'safe'|'reduced'|'parkedOnly';
  summary(): { icon: string; value: string; badge?: string };   // Chip/Badge text
  claimsGestures?: ('pan'|'swipeH'|'swipeV'|'longPress')[];      // for arbitration
  render(el: HTMLElement, ctx: { size: SizeClass; moving: boolean; focusInside: boolean });
  focus?: FocusTree;                          // inner focusables for the D-pad
  deepLink?(alertId: string): PageRef;        // Diagnose target
}
```
The page's state (selection, scroll, zoom) is the app's. It must survive a change of size class.

---

## 4. Tiling engine

### 4.1 Solving rects
- Store each page as a **guillotine tree**: split nodes (horizontal or vertical, with a ratio) and leaf tiles. This makes resizing and splitting easy and guarantees no gaps.
- Rects are derived from the tree.
- **Resizing an edge** moves the ratio of the nearest split node that owns that edge. Neighbouring tiles on the same split give way together (C-08, V-01c).
- **Snap anchors:** ⅓, ½, ⅔, plus every size-class boundary of both tiles. Anchors closer than 24 dp merge into one. Give a light haptic at each snap and a strong one at a limit.
- **Limits:** stop the edge where either side would go above its page's largest class, or below its smallest. If a tile goes past its smallest class and removing it is allowed, mark it "will remove" (release removes it, with Undo).

### 4.2 Shapes (presets)
- Built in: Full, Halves, 2+1, 1+2, Thirds, Quad, Stacked.
- Users can also save their own shapes; a shape is just a tree with empty leaves.
- **Offer only shapes whose leaves are all ≥ Compact on the current page.** The quick row shows the 4 the user chose, then More.

### 4.3 Drag-and-drop targets (while a tile or tray page is lifted)

| Target | Action |
|---|---|
| Top shapes row | Rearrange the whole page into that shape; the lifted page takes the slot it's dropped in |
| Tile, hover ≥300 ms | **Slide-swap**: animate the others to the swapped arrangement; release commits |
| Tile centre, hover ≥800 ms | **Stack**: the target becomes a stack, with the lifted page appended |
| Tile edge zone (four triangles split by the diagonals) | Split the target on that side; **only zones that keep both pages within their size ranges are shown** |
| Screen edge, hold ≥600 ms | Turn the carousel; past the last page, create a new empty page |
| Delete circle (bottom centre of the driver half) | Remove the tile, with Undo |

- **5″ and phones:** no zone overlay. Use the half rule instead: split the target along its longer side, on the side of the finger.
- **Preview:** always show the real reflowed result before release. Never use guide lines or ghost outlines.

### 4.4 Spanning (wide only)
- A tile's right edge may cross the seam into the next page. The tile then gets `span: 2`.
- The tile belongs to its starting page (its home), and the next page's tree reflows around the spanned area.
- In the single-page version the tile simply shrinks back onto its home page.

---

## 5. Carousel and gesture arbitration

### 5.1 Who gets a touch
1. If the touch starts on a page's interactive region, and that page claims the gesture (`claimsGestures`), the page gets it.
2. Otherwise a horizontal drag of more than 12 dp, angled under 30°, belongs to the carousel. This only applies when parked.
3. On devices with Android's gesture navigation, ignore edge swipes that start within 24 dp of the screen edge. Those belong to the system's back gesture.

### 5.2 Paging
- **Paging:** the carousel moves one page at a time and never wraps round. Past the last page, show a short rubber-band stretch and a light haptic.
- **Wheel:** left or right off the edge of the outermost tile pages the carousel. The single "next layout" key loops round to the first.
- **Page dots:** at the bottom, shown only in edit mode or while paging. Fade them out after 1.5 s idle.
- **While moving:** page changes are a straight cut, never a slide.

---

## 6. Edit mode state machine

```
NORMAL --hold 500ms (parked)--> EDIT
EDIT: zoomOut(0.84), pages on panels, selector = page under focus/touch
  tapTile -> SELECTED(tile): resize frame
  SELECTED + hold -> STYLE sheet (frame/corners, link to app settings)
  liftTile (hold+move) -> DRAGGING: show shapes row, zones, delete circle; hide resize handles
  tap "Layout" -> SHAPES sheet; leftover slots show "+"
  tap "+" -> PICKER(slot): pages that fit, suggestions first, "All pages"
  after fill -> next empty slot opens PICKER (Snap Assist)
  Done -> if changed: Save over / Save as new / Discard
any state --vehicle moving or unknown--> NORMAL (keep edits as "Edited", toast once, cancel drag)
```
- **Undo** covers the whole session.
- **When the car starts moving mid-edit:** cancel the drag at once; the tile goes back to its last snapped spot.
- **Persistence:** keep unsaved edits for this screen until they're saved or discarded.

---

## 7. Stacks and full screen
- **Stack data:** `content.stack[]` plus `active`.
- **Badges:** use the **Badge** size class. The badge rail is 96 dp wide, and badges are 64 dp tall (72 dp while moving).
- **Badge pages:** work out how many badges fit, `k = floor((railLen + 8) / (badgeLen + 8))`, and page the badges in groups of k. Show the rail's own dots only while it's turning or in edit mode.
- **Which edge the badges go on** (`badgeEdge`), in priority order:
  1. the user's setting;
  2. the edge next to physical keys, if the host reports them;
  3. the passenger side;
  4. the bottom, in portrait.
- **Linked physical keys:** key *i* activates visible badge *i*.
- **Full screen:** double-tap a tile, or press OK twice on the wheel. This is a transient overlay with no change to the layout model. The other tiles become a badge rail, and the last badge restores. It's allowed while moving.

---

## 8. Focus engine (wheel and D-pad)
- **Two levels.**
  - **Tile level:** the arrows move the ring between tiles. Pick the nearest tile in the pressed direction, scoring by distance plus cross-axis overlap. Ties go to the last-focused tile, then the driver side.
  - **Inside a page:** OK enters the page, and the arrows then walk that page's `focus` tree. Back returns to tile level.
  - **At a page's edge** the arrows don't leave the page: give a short bump haptic and stay put.
- **Focus ring:** 3 dp, with a 2 dp gap, no glow. It shows only after a key press, never after a touch.
- **Long Select** opens the alerts list.

---

## 9. Alerts

### 9.1 Message (app → Gateway → shell)
```ts
type Alert = {
  id: string; level: 'caution'|'warning'|'notice';
  app: string; page?: PageRef;            // source page (for ring / dots / deep link)
  title: string;                          // e.g. "Coolant 108 °C ↑" (app-written)
  speak?: string;                         // TTS line; default = title
  diagnose?: PageRef;                     // deep link
  active: boolean;                        // false = cleared
  acked?: boolean;
};
```
- **Apps style their own content.** The shell never recolours anything inside a page; it only draws the ring, the tag, the card, the tab and the takeover.

### 9.2 Routing
```
onAlert(a):
  src = findTilesShowing(a.page)              // visible tiles on current page(s), incl. stack actives
  if a.level == 'warning':
     if src: renderWarningOnTile(src)         // the tile itself, with ACK
     else:   t = pickTakeoverTile()           // passenger side, not instrument, not widget
             t ? takeover(t) : band(passengerSide)
     playTone(repeatUntilAck=true); speak(a.speak)
  if a.level == 'caution':
     if src: ring(src) + ringTag(src, a.title)          // no card
     else:   card(centred, 4s) -> tab(passengerTopCorner)
     chime(); speak(a.speak)
  markLocation(a): page dot border (amber/red) for the page holding a.page; badge border in stacks
  tab persists until a.active == false; shows highest level, "+n" for others
```
- **Layering:** the alert layer is the topmost z-layer, above sheets, edit mode and full screen.
- **The tab:** 44 dp tall, text ≥ 24 dp. It goes in the passenger-side top corner and sits just inside a badge rail on that edge. It never covers an instrument's values.
- **The card:** centred over the page for 4 s and never modal; touches outside it still work. It carries **Diagnose** and **ACK**. On 12″ and up, the tab goes top centre, next to the seam.
- **Tapping the card or tab** goes to `a.diagnose`, or else to `a.page`.
  - If that page is in a layout, page the carousel there and focus the tile.
  - If not, open it full screen; Back returns.
- **ACK:** Select on the wheel, or the button. After ACK the takeover is released, and the outlined tab and ring stay until the alert clears.

### 9.3 Audio
- Use Android `TextToSpeech` and audio focus, with the **notification/alarm stream**, ducking any media.
- **Caution:** a chime, then the spoken line once.
- **Warning:** a distinct tone, then the spoken line. The tone repeats every 10 s, quietly, until ACK.
- Respect a user volume setting, but **warnings can't be muted**.

### 9.4 Android notifications (Gateway app)
- **Channels:** `ostler.warning` (importance HIGH, alarm category, bypasses Do Not Disturb with permission), `ostler.caution` (HIGH) and `ostler.notice` (DEFAULT).
- **When to post:** only when no Ostler shell is in the foreground on that device. Cancel the notification when the alert clears.
- **Content:** title = the app's `title`. The tap action is a deep link to `diagnose`.
- **Independence:** the in-shell alert system must work with notification permission denied, and offline.

---

## 10. Moving rules (enforced by `motion/`)
- **State:** the Gateway reports moving, parked or unknown. **Unknown counts as moving.**
- **While moving:**
  - Text is at least 24 dp and touch targets at least 60 dp.
  - Blur, glow and texture are off; Transparent tiles render solid if they're instruments.
  - Toasts are text-only.
- **Allowed while moving:**
  - page and layout changes (wheel, triggers; no swipe);
  - stack badges;
  - full screen;
  - focus;
  - ACK and Diagnose.
- **Blocked while moving:**
  - edit mode, hold, resize, saving;
  - settings changes (browsing is allowed);
  - parked-only pages.
- **Refusals:** a one-line toast, e.g. "Park to edit the layout".

---

## 11. No top strip: the surfaces that do exist
- **Stale data:** this belongs to each app, per module. The shell shows nothing global.
- **Viewing another car:** a pill at the bottom centre, shown while it applies, with ✕ to return.
- **Gateway lost:** a banner shown once. The tiles make room for it, then it's dismissible; while moving it's a toast instead.
- **Settings:** the gear sits in the edit bar. Shared settings are owned by the Gateway.

---

## 12. Android integration (Gateway-hosted shell only)
- **Widgets:** host other apps' widgets with `AppWidgetHost`.
  - Binding needs Android's own consent dialog, with no restyling.
  - Ostler never records, captures or syncs widget content.
  - Widget tiles never take a warning.
- **Split screen:** react to window size changes with `fitPages` and switch between the wide and single versions. Treat this as a layout change, not an edit.
- **Physical keys:** map them through the head-unit key profile. Expose the key positions to the badge-edge logic.

---

## 13. Persistence and sync
- **What's stored where:**
  - Layouts are stored per car and per screen class on the Gateway, and synced through the account.
  - Unsaved edit sessions are kept locally on the device.
- **Conflicts:** last writer wins per layout version (`wide` or `single`), with the losing copy kept in history for 30 days.
- **Offline:** edits save locally and show "Not synced yet".

---

## 14. Accessibility
- Every touch action has a D-pad or keyboard route; in edit mode these are Move before / after, Wider / Narrower, Taller / Shorter, Add beside and Remove.
- Announce changes through `aria-live` or Android `announceForAccessibility`, e.g. "Speed: one third wide, Compact".
- Don't rely on colour alone: alerts always pair an icon and text with the ring.

---

## 15. Build order
1. `layout/`: dp, size classes, `fitPages`, the guillotine tree, validation.
2. `contract/` plus a sample page (Speed), rendered at all five classes.
3. Carousel, gesture arbitration, page dots.
4. `motion/` enforcement.
5. Edit mode: zoom-out, panels, selector, resize frame, Undo, save choice.
6. Dragging: slide-swap, delete circle, edge paging, new page.
7. Shapes row and More, slot picker with Snap Assist.
8. Drop zones on 7″ and up; the half rule on small screens.
9. Stacks, badge pages, full screen.
10. The focus engine at both levels.
11. Alerts: router, ring and tag, card and tab, takeover and band, audio, Android channels.
12. Large screens: pinned column, two pages, spanning, wide and single versions.
13. Android extras: widgets, split-screen handling, physical keys.

## 16. Acceptance checks (match the frames)
- [ ] **One page or two:** a 7″ screen shows one page (C-01); a 15″ screen shows the pinned column plus two pages (C-02).
- [ ] **Split screen:** opening Spotify beside Ostler switches to the single version with the driver-side instrument unmoved; closing it restores the wide version exactly (C-04, L-09 to L-11).
- [ ] **Edit mode:** zooms out without reflowing, with panels and the selector (C-06, C-07).
- [ ] **Dragging:** the shapes row, zones and delete circle appear, and invalid zones are hidden (C-09).
- [ ] **Edge paging:** dragging to the edge pages over and the selector follows (C-10, C-11).
- [ ] **Stack badges:** come in pages with their own dots; linked keys follow the visible badges (C-14b, C-14c).
- [ ] **Focus:** never leaves a page at its edge; Back exits (C-16).
- [ ] **Caution, cause on screen:** ring plus tag and no card (A-03).
- [ ] **Caution, cause off screen:** centred card, then a tab that stays until the alert clears (A-01, A-02).
- [ ] **Warning:** shows on the source tile if it's visible, otherwise takes over a non-instrument tile (A-07, A-08).
- [ ] **Alerts never cover an instrument's values**, and the tab sits inside any badge rail (A-04, A-06).
- [ ] **Moving or unknown** cancels edit mode immediately and keeps the edits (E-32, E-33).
