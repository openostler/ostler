---
title: "Tile navigation for ostler-shell — app instances in tiles, per-instance history, the navigation API for page modules and iframes, cross-app links, the Back order and app tabs from Standard — design"
area: specs
status: stable
version: 1.0
updated: 2026-10-13
depends_on: [specs/2026-10-11-ostler-shell-design.md, references/design/2026-10/shell-session/IMPLEMENTATION.md, specs/2026-10-07-shell-input-design.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md]
summary: >
  Approved by the owner on 2026-10-13 ("Spec it, then build"), from the `navigation` section of the designer's token pack of 2026-10-13. Each tile, and each stack member, holds an app instance { app, startingPoint, route }: the existing PageRef with `page` as the starting point and an optional `route`, additive in `ostler.layout/3` (no migration). Apps own their history and expose `back(): boolean` ("returns handled") and `navigate()`; they report the route and `canGoBack` through a port in the render context; iframes use `ostler.nav.*` postMessage messages with the same meaning. Cross-app links focus and navigate a matching instance on screen (switching a stack's active member, which Back undoes), or open the app full screen at the route with Back returning; a link never swaps an instrument out of view. The Back order (shell sheets, view in focused tile, exit full screen, undo last page swap, leave edit mode, then Android) for the wheel, keyboard, D-pad, Android system back (an armed OnBackPressedCallback) and the PWA's popstate guard; the wheel never exits the app. "Page swap" means a change of a stack's active member outside edit mode. App tab rows show from Standard up. Tests, build order N1 to N7, and open questions.
---

# Tile navigation — design

**Status: approved, v1.0** (the owner, 2026-10-13: "Spec it, then build"). Source: the
`navigation` section of the designer's token pack of 2026-10-13 (`ostler-shell-tokens.json`):

```
tile: "holds an app instance { app, startingPoint?, route }"   history: "per tile; back() returns handled"
crossApp: { appOnScreen: "focus that tile and navigate it", appNotOnScreen: "open full screen at the route; Back returns" }
tabsShownFrom: "Standard"
backOrder: ["view in focused tile", "exit full screen", "undo last page swap", "leave edit mode", "then Android"]
```

It builds on the [shell spec](2026-10-11-ostler-shell-design.md), the
[implementation guide](../references/design/2026-10/shell-session/IMPLEMENTATION.md) and the same
day's decisions: **full screen has no shell chrome** (phones exit by the back gesture; head units
get a 44 dp exit button in the driver-side top corner, fading after 3 s; Back walks the app's
views and exits at the entry view); **the picker lists apps once**, up to four starting points
each ("Add app"); **no swapping in edit mode** (shell spec §21). Code references are to
`openostler/ostler-shell` as read on 2026-10-13.

An **app instance** is one copy of an app in one place (a tile, a stack member, full screen) with
its own route and history; a **starting point** is the `PageDef` that draws it at every route (its
`sizes`, `summary` and `instrument` apply throughout); a **route** is a string the app owns and the
shell never parses.

## 1. The app instance model

### 1.1 Relation to TileContent

`TileContent` stays `PageRef | StackContent` (`src/layout/model.ts`). `PageRef` gains one
optional field; it **is** the app instance as stored:

```ts
export interface PageRef {
  readonly app: string;
  readonly page: string;    // the starting point: the PageDef that draws this instance
  readonly params?: Json;
  readonly route?: string;  // new: the route it starts at; absent = the entry view
}
```

The token's `startingPoint` is `page`. It is optional only in a request (a link, or picking the
app row rather than a chip); the shell fills in the default (§2.1) before storing, so the
validator (`refOk`: `app` and `page`) is unchanged. `pageKey` and `samePage` ignore `route`: two
tiles at one starting point are the same page for alerts and the picker, whatever their routes.

**Stacks:** every member of `StackContent.stack` is an instance with its own route and history;
switching members resets neither.

### 1.2 Live state versus stored state

The stored `route` is where a tile **starts**. Where it **is** now lives in the shell's
navigation store, never in the saved layout, so driving about never rewrites a layout through
the Gateway's last-writer-wins `saveLayout`. The store holds, per instance key
(`${layoutId}/${tileId}/${memberIndex}`, or `visit/${n}` in full screen), the stored `ref` and the
last reported `route` and `canGoBack`.

- The store lasts the session (32 instances, least recently shown dropped with `forget()`), so
  switching layouts and back finds tiles where they were. A per-device sessionStorage cache
  (try/catch) restores routes after a reload, by `navigate(route, { cause: "restore", replace:
  true })`.
- After an edit-mode save, an instance keeps its state when the same tile id still holds the
  same `pageKey` (the first such stack member); otherwise it starts at its stored route.
- This is the rule the stack's active member already follows (`withStacks` in
  `src/view/Shell.tsx`: transient, never saved).

### 1.3 Persistence and migration

- **Format:** stays `ostler.layout/3`. `route` is optional and additive; readers ignore unknown
  fields (`validateLayout` already does), so older shells read new layouts and drop nothing they
  understand. Writers must round-trip `route`: edit-mode operations move `PageRef` objects whole
  (a build check, §7).
- **Validation:** `route`, when present, is at most 512 characters, starts with `/`, and has no
  `//`, scheme or control characters. An invalid route is dropped (entry view), never failing
  the layout. Only a picker starting point with a `route` sets it (open question 1).
- **Migration:** none. Existing layouts have no `route`, so every tile starts at its entry view,
  which is what it shows today. `/1` and `/2` migration is unchanged.

## 2. The navigation API

### 2.1 What an app declares

```ts
export interface AppDef {
  readonly id: string; readonly title: string; readonly pages: readonly PageDef[];
  /** New. The picker's chips, at most 4 (default: the first 4 pages); the first is the default. */
  readonly startingPoints?: readonly { readonly page: string; readonly route?: string; readonly title?: string }[];
}

export interface PageDef {
  // … unchanged …
  /** New. Absent: the page has one view; back() is false and links land on its entry view. */
  readonly navigation?: PageNavigation;
}

export interface PageNavigation {
  /** Route prefixes this starting point serves, for links that name no starting point. */
  readonly routes?: readonly string[];
  /** Go back one view in this instance. True when handled (the app moved); false at the entry view. Synchronous. */
  back(instance: string): boolean;
  /** Show a route in this instance (a link, an alert, a restore). View only: never an action. */
  navigate(instance: string, route: string, how: NavigateHow): void;
  /** The instance is gone (closed, evicted): drop its history. */
  forget?(instance: string): void;
}

export interface NavigateHow {
  readonly cause: "link" | "alert" | "notification" | "restore";
  readonly replace: boolean;  // replace the current view rather than push
}
```

**Starting point for a request** (`resolveStartingPoint(app, req)`): the named `startingPoint`
if it is one of the app's pages; else the page whose `routes` has the longest prefix of the
route; else the default starting point. A pick or link with no route uses the starting point's
own `route`, if any.

### 2.2 What the shell gives an instance

`PageRenderContext` gains the instance and a port:

```ts
export interface PageRenderContext {
  // … unchanged; new:
  readonly instance?: string;  // this instance's key, stable for its life
  readonly route?: string;     // the route to show first: restored or stored, else ""
  readonly nav?: NavPort;      // always present; a page without `navigation` may ignore it
}

export interface NavPort {
  /** Report the view now showing. Call on every change of view, including tab switches. */
  report(state: { readonly route: string; readonly canGoBack: boolean; readonly title?: string }): void;
  /** Ask the shell to show a route in another app (or another starting point of this one). */
  link(req: LinkRequest): LinkOutcome;
}

export interface LinkRequest { readonly app: string; readonly startingPoint?: string; readonly route?: string; readonly params?: Json }

export type LinkOutcome =
  | { readonly kind: "navigated"; readonly tileId: string; readonly swapped: boolean }
  | { readonly kind: "full-screen" }
  | { readonly kind: "refused"; readonly reason: "not-installed" | "bad-route" | "no-activation" | "editing" };
```

**History is the app's.** The app keeps its own stack per instance; the shell keeps only the
last reported `route` and `canGoBack`, which it uses to decide whether Back is armed (§5.3) and
to restore. An app's in-page dialogs and drill-downs are views: its `back()` closes them first.
Tab switches replace rather than push; Back at the root of a tab other than the first goes to
the first tab (handled), and only at the first tab's root does `back()` return false (Android's
start-destination rule). A link into the same app and starting point from inside the instance is
not a cross-app link: the app navigates itself and reports.

### 2.3 Iframes (third-party pages)

The same contract over `postMessage`, under the existing rules (shell spec §8: posted to the
frame's origin only, only `ostler.*` messages accepted from it, `v: 1`). One frame hosts one
instance, so `instance` is a check, not a selector.

| Direction | Message | Meaning |
|---|---|---|
| shell → frame | `{ type: "ostler.nav.init", v: 1, instance, route }` | after load; the route to show first |
| shell → frame | `{ type: "ostler.nav.navigate", v: 1, instance, route, how }` | `navigate()` |
| shell → frame | `{ type: "ostler.nav.back", v: 1, instance, seq }` | `back()` |
| frame → shell | `{ type: "ostler.nav.backResult", v: 1, instance, seq, handled }` | its answer, within 500 ms |
| frame → shell | `{ type: "ostler.nav.route", v: 1, instance, route, canGoBack, title? }` | `report()` |
| frame → shell | `{ type: "ostler.nav.link", v: 1, instance, req }` | `link()`; the outcome is posted back as `ostler.nav.linkResult` |

- **Back across the boundary:** the shell decides at once from the last `canGoBack`; if true it
  sends `ostler.nav.back` and counts the press handled. A `handled: false` answer, with no input
  since, runs the order from step 2 for that press; no answer in 500 ms counts as handled.
- **Frames route in memory:** `history.pushState` in a frame adds to the top-level session
  history and breaks the PWA guard (§5.3).
- **Links need a user action:** `ostler.nav.link` is accepted only within 1 s of an input routed
  to that frame's tile, one per input; else `no-activation`. Module pages (own apps) are not
  gated, but any source gets at most one link per input or shell cause.

## 3. Cross-app links

`followLink(scene, req, source)` is pure over the scene (as `src/alerts/scene.ts` builds it) and
returns the outcome. It validates (`not-installed` shows the refusal toast "{App} isn't
installed"; `bad-route` does nothing), resolves the starting point (§2.1), then picks a target.

### 3.1 App on screen: focus that tile and navigate it

**On screen** means a tile visible now: the carousel page or pages showing, and the pinned
column. **Candidates** are instances of the app at the resolved starting point, as the active
member of a tile, or as an inactive member of a stack on screen. The target is the first of:

1. the focused tile, if it is a candidate;
2. an active member, the most recently focused first (the focus engine's `recent`), then in
   focus order (driver side first);
3. an inactive stack member, by the same order.

The shell focuses the tile (`focusTile`) and calls `navigate(route, { cause: "link", replace:
false })` when the request has a route. An inactive stack member is first made active: a **page
swap** recorded for Back (§4.2), `swapped: true`.

**A link never swaps an instrument out of view.** If the stack's active member is an instrument
page (`isInstrument`), its inactive members are not candidates, and the request falls to §3.2.

### 3.2 App not on screen: open full screen at the route; Back returns

The shell opens a **visiting instance** full screen, at the resolved starting point and route.
It is transient: not in the layout, dropped with its history (`forget`) when it closes. This
replaces today's alert-only full screen (`alertPage` and `ALERT_PAGE` in `Shell.tsx`), and the
alert router's `openFullScreen` and the Android bridge's `deepLink` event use it too.

- **Full screen is a stack of entries:** an optional base (a tile opened by double-tap or OK
  twice), then visitors. A link to an off-screen app pushes a visitor (at most 8, oldest dropped);
  a link to the top entry's app navigates it. While full screen is open only its top entry is on
  screen for §3.1, so a link never closes full screen to reach a tile underneath.
- **Back returns to where you were:** a visitor walks its views (step 1), then closes (step 2),
  uncovering the entry below or the tiles with carousel page, focus and stacks as they were. The
  head unit's exit button closes all entries at once.
- **In the layout but on another carousel page** counts as not on screen: the link opens a
  visitor rather than paging away from what the driver is looking at (the alert router still
  pages there; open question 2).

### 3.3 Edit mode, moving, and pages that do not fit

- **Edit mode:** pages are previews; links are refused (`editing`).
- **While moving:** allowed (navigation is not editing; full screen is allowed while moving).
  `navigate()` is view-only, so a link never starts an action; the moving rules and the node gate
  apply to whatever the user does next.
- **No class fits:** the existing fallback chip, full screen.

## 4. What Back acts on

### 4.1 The focused instance

The focused tile is the focus engine's `tile` (set by keys, and quietly by a touch through
`pointer(tile)`). Its instance is the tile's active member; in full screen, the top entry. A
tile covered by an alert takeover is skipped (its page is hidden), and the order moves to step 2.

### 4.2 "Undo last page swap": the interpretation

Shell spec §21 removed swapping from edit mode, and the v2 shell has no tile label menu (its
"Swap page" went with the top strip, §20). So a page swap is a **change of a stack's active
member outside edit mode**: a badge tap, a physical badge key, the alert router's `pageTo` with a
`stackIndex`, or a link landing on an inactive member (§3.1). Edit mode's "Change page" is an
edit, covered by edit mode's Undo and by leaving edit mode. Chosen because it is the only swap
made at any speed, it is unsaved view state (`withStacks`), and it makes links into stacks
reversible.

The shell keeps **one** record, `{ tileId, from, to }`, of the last swap. It is replaced by the
next swap, and cleared when it is undone, when that tile leaves the screen (carousel paged, layout
switched, window refit), when edit mode opens, or when that stack's active member changes by any
other means. Undo sets the stack back to `from`; the member's own route and history are kept.

## 5. The Back order

### 5.1 Steps

`backStep(state, input)` is a pure function returning the one action a press takes; the shell
carries it out. Held keys never repeat Back (`repeat > 0` is ignored; ShellInput §5).

0. **Shell surfaces first:** close the alerts list if open (the alert layer is topmost); else
   close the topmost shell sheet or dialog (edit sheets and picker, save sheet, settings, a
   confirm) as Cancel, never confirming. Warnings (takeover, band, in-place bar) and caution
   cards are neither closed nor acknowledged by Back (ACK stays Select or the button), and
   toasts time out; the press goes on to step 1.
1. **View in focused tile:** call the focused instance's `back()`. Handled: done.
   - **D-pad at page level** (focus inside the page): handled, focus stays inside (the engine
     re-resolves the item; the page's `initial` if the old one is gone). Not handled: focus
     leaves the page to tile level (`leavePage`), and that is the press.
2. **Exit full screen:** if full screen is open, close its top entry (§3.2). Done.
3. **Undo last page swap:** if the record exists and its tile is on screen, undo it. Done.
4. **Leave edit mode:** in edit mode, if a tile is lifted, cancel the drag (it goes back to its
   last snapped spot); else if a tile is selected, deselect it; else Done: with changes, the
   save sheet (Save over, Save as new, Discard; Back on that sheet is step 0, keep editing);
   without, back to the normal screen. Edit mode is entered from the normal screen and closes
   full screen and clears the swap record, so steps 1 to 3 are empty while it is open.
5. **Then Android:** the shell does not handle the press (below, per input).

### 5.2 Inputs

| Input | Arrives as | At step 5 |
|---|---|---|
| Wheel or bezel Back key (key profile role `back`, consumed by native) | bridge `key` event → intent `back` | nothing: an edge-bump haptic; it never exits the app (ShellInput §4.3) |
| Keyboard Escape; Backspace outside an editable element | intent `back` (`src/focus/keys.ts`) | nothing |
| D-pad or gamepad B | intent `back` | nothing |
| Android system back (gesture or nav bar), Gateway Android app | bridge `back` event (§5.3) | Android's default: the callback is disabled, so the system leaves the app |
| Browser back on a phone (PWA) | `popstate` on the guard entry (§5.3) | the browser's default: no guard, so Back leaves the page |
| Head unit's full-screen exit button | not Back: closes all full-screen entries | — |

All inputs run the same `backStep`; only step 5 differs.

### 5.3 Arming the system back

`backArmed(state)` is true when step 0, 1 (from the last `canGoBack`, or focus at page level),
2, 3 or 4 would act. The shell recomputes it on every state change.

- **Gateway Android app:** new bridge method `back.armed { armed }` (shell → native, sent on
  change) and event `back {}` (native → shell). Native keeps an `OnBackPressedCallback` whose
  `isEnabled` is `armed`; `handleOnBackPressed` sends `back`. When disarmed, Android's own back
  (and the predictive-back animation to home) runs. `src/android/PROTOCOL.md` gains a section.
- **PWA:** while armed, the shell keeps one guard entry (`history.pushState({ ostler: "guard" },
  "")`, same URL). `popstate` runs `backStep` and re-pushes the guard if still armed; on
  disarming, the shell pops it with `history.back()` and ignores that `popstate`. Browsers may
  skip entries pushed without user activation, so the guard is pushed in the arming input's
  handler where possible.

### 5.4 Moving and parked

Back is the same at any speed: every step is navigation or closing, none is an edit. Edit mode
cannot be open while moving (the machine closes it, keeping edits as "Edited"), so step 4 does
not occur while moving. Full screen, its exit button and visitors work while moving. While
moving, apps keep their own moving rules on the views Back reveals; the shell adds none.

## 6. App tabs from Standard

**Tabs** are an app's own top-level view row (Diagnose's Faults, Live, Tests; Logs' Drives,
Charts; the mock `Tabs` part in `src/mock/pages/parts.tsx`). The shell draws no tabs, in tiles
or full screen (the app draws its own); ADR-0052 v0.5 already put each app's navigation at
Standard and Expanded only.

- **Rule:** a page shows its tab row only at fitted class `standard` or `expanded`; the contract
  exports `showsTabs(size)`, reading `navigation.tabsShownFrom` from the generated kit tokens.
- **Below Standard** the page shows the current tab's view without the row. A class change never
  changes the route, so the tab is kept. The row is a D-pad focus group only when shown.
- **While moving** tab labels meet the 24 dp floor and 60 dp targets; a row that cannot fit is
  the page's to drop. Full screen is normally Expanded, so tabs show there.

## 7. Testing

- **Vitest, pure:** `resolveStartingPoint`; `followLink` (focused tile, recency, stack swap,
  instrument guard, full-screen top only, other carousel page, edit mode); `backStep` for every
  step, step 0's surfaces, page-level D-pad, covered tile, edit sub-steps; the swap record's
  lifecycle; `backArmed`; route validation and `route` round-tripping through edits; instance
  remapping after a save; `showsTabs` against the tokens.
- **Vitest, hosts:** the iframe messages with a fake `postMessage` (origin, `seq`, fall-through,
  timeout, activation); the PWA guard with a fake `history`; the bridge mock's `back.armed`.
- **Playwright (`e2e/v2-navigation.spec.ts`)**, with routes in the mock apps (Diagnose
  `/faults/:code`, Logs `/drives/:id`): Back walks views then stops; links on screen, into a
  stack (Back undoes) and off screen (Back restores page and focus); phone popstate; the exit
  button fading after 3 s; Back during a takeover does not ACK.

## 8. Build order

1. **N1** `PageRef.route` and its validation; pure `src/nav/` (`instance`, `link`, `back`,
   `armed`); `showsTabs` once the token pack is in `design/kit/` and `gen:tokens` has run.
2. **N2** `ctx.instance`, `ctx.route`, `ctx.nav` and the navigation store; routes and tabs in the
   mock apps.
3. **N3** The Back order in `OstlerShell` (replacing the focus engine's `onBack` wiring), the
   swap record, page-level D-pad Back asking the app first.
4. **N4** Full screen as an entry stack; `alertPage` and the bridge `deepLink` moved onto it.
   After the no-chrome full screen change, which removes `FullScreen.tsx`'s badge rail.
5. **N5** Cross-app links, refusal strings through `t()`.
6. **N6** The PWA guard; the bridge's `back.armed` and `back`, documented in PROTOCOL.md.
7. **N7** `ostler.nav.*` in the iframe host, when it is built (shell spec §16 step 4).

## 9. Open questions

1. **Save live routes?** Should "Save over" store each tile's current route? Built: no.
2. **Links to another carousel page:** a visitor (built, per the token) or page there as alerts do?
3. **Swap record expiry:** none (cleared when its tile leaves the screen), or 10 s like close-Undo?
4. **D-pad Back asks the app first** at page level, changing guide §8 and ShellInput §4.3; confirm.
5. **Iframe Back race:** the 500 ms window, with no answer counting as handled.
6. **Limits:** 8 visitors, 32 instances per session, and the route cache across reloads.
7. **Starting points** are declared here (`AppDef.startingPoints`); the picker change uses them.

## Changelog

- 2026-10-13 — v1.0, approved by the owner ("Spec it, then build"): first design, from the token
  pack's `navigation` section and the same day's full-screen, picker and move-aside decisions.
