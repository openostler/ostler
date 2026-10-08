---
title: "ShellInput — a D-pad input model for the shell: intents, focus zones, spatial navigation, Drive menu, bindings and key test — design"
area: specs
status: stable
version: 0.5
updated: 2026-10-07
depends_on: [references/research/dmd2_ui_teardown.md, references/research/dmd2_features.md, references/research/driver_distraction_rules.md, references/research/addons_catalogue.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0024-body-bus-links-passive-by-default.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md, specs/2026-10-07-navigation-addon-design.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3; every decision answered as recommended. `ShellInput`, a core-platform input model so every screen can be
  driven without touch, from DMD2's remote-control lesson. Eight intents (up, down, left, right, ok, back, menu by
  long-press, mark; optional zoom and push-to-talk) from four sources: keyboard, HID remotes (they arrive as key
  events), the Gamepad API, and read-only steering-wheel and keypad events from vehicle packs and hardware add-ons
  over a new `event/input.button` module-bus topic. Focus zones (strip, rail, main, sheet) with geometric
  spatial navigation; repeat only for movement; long-press 600 ms. Drive mode: left/right switch faces, up/down
  zoom the map, ok opens the Drive menu (a `short_list` of at most six driver-safe rows while Moving), nothing
  scrolls. Confirm sheets for gate actions open with Cancel focused and never auto-confirm. A 3 px focus-ring
  token with no glow and no resize. Bindings belong to the display's install configuration, edited Parked only,
  with a key-test screen. Accessibility and keyboard-only Playwright tests; ships in U2; names the UI spec,
  visual spec, app-model and module-bus sections it amends. v0.2 (amendment §14, DMD round, approved): a long
  `ok` (600 ms) on a focused strip chip, rail item or widget enters edit mode when Parked ("Park to edit" while
  Moving); while Moving in Drive mode, `back` with nothing open moves focus to the Drive-mode chip wherever it sits;
  the switcher is found by id (drive-modes spec v0.2 decision 15). Amended 2026-10-07 (OS round): voice control is no longer a non-goal; a local-first assistant comes later. Amended 2026-10-07 (openness round, ADR-0047): the focus-ring values are defaults a theme may restyle while focus stays visible and nothing reflows in Moving templates.
---

# ShellInput — design

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("this should
> be an open system", then "apply the loosenings";
> [ADR-0047](../decisions/adr-0047-openness-round.md)):** the focus-ring token values are the
> default look; a theme may restyle the ring (colour, width, glow) as long as focus stays
> clearly visible (WCAG 2.4.13) and the focused item does not resize or reflow in Moving
> templates (§9). Cancel focused on confirm sheets and no auto-confirm are unchanged.

> **Amended 2026-10-07 (OS round), approved by the owner on 2026-10-07 ("approve all", OS
> round; decision list item 54):** voice control is no longer a non-goal (§1); a local-first
> assistant comes later ([head-unit apps](2026-10-07-head-unit-apps-design.md) §10). A spoken
> yes never confirms a gated action.

**Status:** approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3, with the
amendment §14 (editing and the movable switcher), approved. Its amendments to other specs (§11)
are approved with it; where those specs' DMD-round amendments (approved the same day) do not
already carry them, they are folded in when those specs are next revised. Evidence: [DMD2 UI teardown](../references/research/dmd2_ui_teardown.md) §5 (the
remote-control model and the proposal this spec decides), §11 Copy 1–3 and Decide 2, 6, 7;
[DMD2 features](../references/research/dmd2_features.md) §10; [driver-distraction
rules](../references/research/driver_distraction_rules.md) §7. Today the shell is touch and
mouse only: `Escape` closes sheets, the focus ring is the browser default and there is no
spatial navigation (teardown, "Ostler today").

## 1. Goals and non-goals

**Goals.** Every destination, sheet and Drive mode works from a D-pad plus two buttons, so a
gloved rider, a wet screen, a steering-wheel button or a handlebar remote can drive Ostler
safely; keyboard users on desktop get the same model (WCAG 2.1.1). Input is **core and free**
(teardown Avoid 8). **Non-goals:** input never adds a capability a tap does not have; no text
entry by D-pad while Moving; no pointer emulation. (*Amended 2026-10-07, OS round:* "no voice
control" is lifted; a local-first assistant comes later.)

## 2. Intents

The shell maps sources to **intents**; views and add-ons see intents and focus, never keys.

| Intent | Default keyboard | Meaning | Repeats |
|---|---|---|---|
| `up` `down` `left` `right` | arrow keys | move focus (§4), or adjust an engaged control | yes (§5) |
| `ok` | Enter (Space on a focused button, as native) | activate the focused item | no |
| `back` | Escape | close the sheet, leave the zone, go up one level (§4.3) | no |
| `menu` | long-press `back`, or a dedicated key | Drive mode: open the Drive menu; elsewhere: focus the rail | no |
| `mark` | `M` | Mark (UI spec §3.2, safe at any speed) | no |
| `zoom_in` `zoom_out` (optional) | `+` `-` | map zoom, in steps | yes |
| `ptt` (optional) | unbound | push-to-talk while held (Social's `call` template) | hold, not repeat |

Tab and Shift+Tab keep native order everywhere. Media keys pass to the `media` template.

## 3. Sources

| Source | How it arrives | Notes |
|---|---|---|
| **Keyboard** | DOM key events | defaults above; no setup |
| **HID remotes** (Bluetooth handlebar and wheel remotes, Android TV-style D-pads) | the same key events (DMD's key codes 19–22, 66, 111 are the D-pad, Enter and Escape) | an Android browser's own Back may arrive as history navigation; the shell guards history so Back maps to `back` (U per head unit) |
| **Gamepad API** | `navigator.getGamepads()` polled per frame while connected | needs a secure context (local HTTPS, ADR-0021) and a first button press; standard mapping D-pad → arrows, A → `ok`, B → `back` |
| **Vehicle packs and hardware add-ons** | node-sourced **input events** over the module bus and the Brain's WebSocket (§3.1) | read-only; an intent does only what a tap could (ADR-0033) |

### 3.1 Input events from packs and keypads

A pack that decodes steering-wheel buttons (the `bmw_e` `mfl` module emits
`Vehicle.Ostler.Cabin.SteeringWheelButton`, [vehicle-packs spec §3.5](2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md))
and the "Dash buttons and keypads" hardware add-on ([catalogue](../references/research/addons_catalogue.md))
publish button events. Today a VSS reading is retained (module-bus §6), so a reconnecting display
could replay an old press. Proposal (a module-bus amendment, Decision 5):

- **Topic** `ostler/v1/<vid>/<device>/event/input.button`, the §6.1 event shape with
  `class: "input"`, plus `button` (pack-declared name, e.g. `wheel.next`), `phase` (`down`, `up`)
  and `source`. QoS 0, **never retained**, Message Expiry **1 s** (a written exception to §6.1's
  3600 s). The VSS reading may still be recorded for logs and Home Assistant.
- **Delivery:** the Brain forwards live events to displays as an `input` message on the existing
  WebSocket and drops any it receives more than 500 ms after publication (best clock,
  ADR-0037). The shell turns `down`/`up` into press, long-press and repeat itself (§5).
- **Default bindings** come from the pack: an optional `input.json` maps button names to
  suggested intents (`wheel.next` → `right`, `wheel.voice` → `ptt`). The display's bindings
  (§8) decide.
- **Read-only:** input events never reach the gate; an event names a button, never an action.
  The D2 has no known wheel buttons on its diagnostic K-line; the first car is a BMW E-series
  once the deferred `bmw_e` pack exists.
- **Idea, not a plan:** a motorcycle pack decoding a BMW-style handlebar wheel from the bike's
  CAN passively (ADR-0024), as DMD's Sync Box does, gives a bike remote with no extra hardware.

## 4. Focus zones and spatial navigation

### 4.1 Zones

Four zones: **`strip`** (status chips), **`rail`** (destinations; the bottom bar on phone),
**`main`** (the page), **`sheet`** (any sheet, dialog or `alert_card`). An open sheet **traps**
focus until `back` or a choice closes it (the only trap). Focusable elements carry
`data-focus` (kit Button, ListRow, Segmented, Chip, rail items, tiles that act, map controls).

### 4.2 Movement

Inside a zone, an arrow moves to the **nearest focusable in that direction**: candidates whose
centre lies in the 90° cone of the direction, scored by distance along the axis plus twice the
off-axis distance (the TV-platform rule). At a zone's edge the move enters the neighbouring zone
(rail ↔ main across the driver side, strip above main), landing on the item last focused there,
else the nearest. Focus moves scroll the focused item into view in `main` (Parked); a list
remembers its focused row. A view may declare a **group** (a grid, a chip row) so arrows stay
inside it until its edge.

### 4.3 `back` and `menu`

`back` closes a sheet; else leaves an engaged control; else moves focus from `main` to the rail
item of the current destination; else goes up one route level. It never leaves Drive mode while
Moving and never exits the app. `menu` (long-press `back`, 600 ms) jumps to the rail from anywhere
outside Drive mode (DMD's "menu focus"). `back` reaches Home or Drive mode in ≤ 3 presses from any
screen (tested).

### 4.4 Engaged controls

Sliders, setpoints, scrubbers and the map are **engaged** by `ok` (a visible state): arrows then
adjust, and `ok` or `back` release. Text fields: arrows edit, `up`/`down` leave a single-line field,
`back` leaves; no text entry while Moving (UI spec §3.5). On a Parked map, engaged arrows pan with
a centre target that "Navigate here" and "Save place" act on; while Moving the map is never pannable.

### 4.5 Pointer and touch together

Focus shows only after a non-pointer intent (`:focus-visible`); a tap clears it. Touch and D-pad
share one selected state: in the Drive menu a first tap focuses a row, a second activates it
(teardown §5.6). On phone, tablet and desktop, arrows move focus only when focus is already on a
`data-focus` element, so page scrolling by arrows keeps working; on head-unit classes arrows
always navigate.

## 5. Repeat and long press

- Repeat only for `up`, `down`, `left`, `right`, `zoom_in`, `zoom_out`: first repeat at 400 ms,
  then every 100 ms, in lists, scrubbers, engaged controls and the map; never across a zone edge
  or into a sheet. `ok`, `back`, `menu`, `mark` never repeat; OS key repeat for them is ignored.
- Long press = 600 ms held. Only `back` has a long-press meaning by default (`menu`); a binding
  may add one per key (§8). Double press binds nothing in v1 (DMD's double tap, Decision 7).
- `ok` presses within 500 ms of a sheet opening are ignored (no double-press approval).

## 6. Drive mode

While Moving on a driver-facing display (UI spec §12.1), Drive mode is mostly not focusable:

| Intent | Effect |
|---|---|
| `left` / `right` | switch the layout's **faces** (tiles, map; teardown Copy 5), wrapping |
| `up` / `down` | zoom the map face in steps; nothing on the tiles face |
| `ok` | open the **Drive menu** |
| `menu` | open the Drive menu (same) |
| `mark` | Mark |
| `back` | close the Drive menu or an `alert_card`; otherwise nothing |

Unbound intents do nothing; **nothing scrolls**. An `alert_card` takes focus while shown, on its
safest button. Parked, Drive mode is an ordinary `main` zone.

**The Drive menu** is a `short_list` sheet: **≤ 6 rows, one level, ≤ 30 characters a row**, each
a driver-safe item with its state on the right ("On", "Armed"). Default rows in order: **Mark**,
**Mute alerts**, media play/pause and skip (when a `media` source exists), climate setpoint
(Comfort, opens the `setpoint` template), **Arm** (Security; never disarm), **Back to Drive**.
Add-ons contribute rows through `contributes.drive_menu` (for example the
[navigation add-on](2026-10-07-navigation-addon-design.md) §5.6); each contributed row is a
navigation or display choice, or an existing Moving-allowed action named with its category and
tier. With more than six candidates the shell shows the first six of the **display's** order,
set Parked only; families and reordering exist only Parked. A row that would need a confirm
sheet while Moving is not offered.

## 7. Confirms and countdowns

- Every sheet that confirms an action reaching the gate (Tier 1+ in any category) opens with
  **Cancel focused**; the confirm button is reached by an arrow, so a double press cannot
  approve. Typed confirms (Tier 3) stay typed and are Parked only.
- **No countdown auto-confirm for anything that reaches the gate.** A countdown that applies its
  focused choice is allowed only for navigation and display choices, such as the navigation
  add-on's off-route card, and shows its seconds as text, never as an animated bar.
- Approvals on a phone (UI spec §7.2) are unchanged: the D-pad never approves on another
  device's behalf.

## 8. Bindings and the key test

- **Owned by the display.** Bindings (intent → key, button or gamepad control, with an optional
  long-press binding) live in the display's entry in the **install configuration**, keyed by
  display id; defaults need no setup. A remote is physical, so it belongs to the screen it is
  fitted to (teardown Decide 6). A signed-in user's preferences **never change a driver-facing
  display's bindings while Moving**; editing is Parked only, by the owner or a signed-in driver.
- **Screen:** More → Network → *the display's device page* (UI spec §3.7) → **Buttons**: a table
  of intents with "press the key now" capture per row, the source of each binding (keyboard,
  remote, gamepad, pack button), **Reset to defaults**, and **Test buttons**: a key-test screen
  that ticks each intent as it arrives (press, long press, repeat shown) until "All buttons OK",
  with no game. Pack and keypad buttons appear when their device publishes them.
- Bindings are not synced between displays; export and import ride the install configuration.

## 9. Focus visuals

A new token group for the [visual spec](2026-10-07-visual-design-system-design.md) §5, with
these **defaults**: `focus-ring-width` **3 px**, `focus-ring-color` `accent`, `focus-ring-gap`
**2 px** of `bg` (so it reads on any surface and the map), drawn as an outline outside the
element, with no glow, shadow, size change or animation. *Amended 2026-10-07 (openness round):*
a theme may restyle the ring (visual §13) provided focus stays clearly visible (WCAG 2.4.13);
in Drive mode and Moving templates the focused item still never enlarges or reflows (teardown
Avoid 5). The kit's "focus-visible ring
2 px `accent`" (visual spec §8, Button) becomes this token for every kit component. Focus is
never colour alone: the ring is a shape change, and a focused ListRow also takes `accent-soft`.

## 10. Accessibility

Native semantics stay: real buttons and links, Tab order, ARIA roles from the kit; spatial
navigation sits on top of, never instead of, Tab. Covered: WCAG 2.1.1 Keyboard, 2.1.2 (the only
trap is a sheet, exited by Escape), 2.4.3 Focus order, 2.4.7 Focus visible, 2.4.11 Focus not
obscured (the strip and sheets never cover the focused item), and 2.4.13 Focus appearance
(≥ 2 px perimeter, ≥ 3:1 contrast; tested per theme). `prefers-reduced-motion` already zeroes
motion; focus moves have none. Screen readers keep their own navigation; the shell does not
intercept keys while a text field or `role="application"` region has focus.

## 11. Amendments this spec makes (for the owners of those specs)

| Spec | Section | Change |
|---|---|---|
| [UI spec](2026-10-06-ui-architecture-design.md) | new **§3.9 Input** | §2–§8 of this spec in short |
| UI spec | §3.5 Moving row; §12.1 `short_list` | the Drive menu as the Moving `short_list` of driver-safe actions; `ok` opens it |
| UI spec | §12.3 Drive mode | layout **faces** (tiles, map) switched by `left`/`right`; nothing scrolls |
| UI spec | §7 tiers | confirm sheets open with Cancel focused; no countdown auto-confirm for gate actions |
| UI spec | §3.7 device pages; §10 U2 and §10.1 | Buttons and Test buttons on a display's page; U2 ships ShellInput; tests below |
| [Visual spec](2026-10-07-visual-design-system-design.md) | §5 tokens; §8 kit; §9 tests | focus-ring tokens; kit focus uses them; focus-appearance assert |
| [App model](2026-10-06-app-model-design.md) | §2 shell duties; §4.1–§4.2 manifest; §6 SDK | input and focus are a shell duty; `contributes.drive_menu`; a read-only `input` service (focus requests, intent events for engaged views) |
| [Module bus](2026-10-06-module-bus-messages-design.md) | §3, §6.1 | `event/input.button`, QoS 0, 1 s expiry, class `input` |

## 12. Where it lives and phases

`ui/src/shell/input.ts` (sources, intents, repeat, long press), `ui/src/shell/focus.ts`
(zones, spatial search, memory), a `useFocusZone` hook, `data-focus` in the V2 kit, the Drive
menu sheet, the Buttons page, and the Brain's WebSocket `input` forwarder. No new dependency.

| Phase | Ships |
|---|---|
| **I1 (U2)** | keyboard and HID sources, zones, spatial navigation, repeat and long press, Drive-mode intents and Drive menu, confirm rules, focus-ring tokens, tests |
| **I2 (U2)** | display bindings, Buttons page and key test, Gamepad API |
| **I3 (after U2)** | `event/input.button`, pack `input.json`, keypad hardware add-on; steering-wheel buttons once a pack emits them |

## 13. Tests

Playwright, keyboard only, at every layout class (HU-5, HU-7, HU-9/10, HU-wide, phone, tablet,
desktop) and each theme:
- Every destination and its sheets are reachable and operable with arrows, Enter and Escape;
  `document.activeElement` is always inside a zone and visibly focused (ring present, ≥ 3:1).
- No trap outside sheets; `back` reaches Home or Drive mode in ≤ 3 presses from every route.
- Moving fixture: in Drive mode only the §6 intents act; `main` never scrolls; `ok` opens a Drive
  menu of ≤ 6 rows of ≤ 30 characters with no nested level; contributed rows beyond six absent.
- Every gate-action confirm sheet opens with Cancel focused; `ok` within 500 ms does nothing; no
  gate-action sheet has a countdown; the off-route card's countdown applies its focused choice.
- `ok`, `back`, `menu`, `mark` never repeat; arrows repeat at 400/100 ms; long press at 600 ms.
- The focused item's bounding box is identical focused and unfocused (no resize); no
  `box-shadow` glow on focus in Drive mode.
- A retained or late (> 500 ms) input event changes nothing; a binding change while Moving is
  refused by the server.
- Unit tests for the spatial scorer on fixture layouts.

## 14. Amendment (2026-10-07, DMD round), approved: editing and the movable switcher

*Approved by the owner on 2026-10-07 ("approve all", DMD round); added in v0.2. It adopts
[drive-modes spec](2026-10-07-drive-modes-and-editing-design.md) v0.2 decision 15 (its §6 and
§7.1 rely on it), written for the owner's "the entire UI is editable, with no fixed icons":
the strip is user-ordered, the Drive-mode chip may sit anywhere in it, and a D-pad user must
reach both edit mode and the switcher without touch. §14 changes §4.3, §5, §6 and §13 as noted and nothing
else; where it differs from them, it wins.*

**14.1 Long `ok` enters edit mode (changes §5).** `ok` gains one long-press meaning: a long
`ok` (600 ms held, §5's timing) on a focused **strip chip**, **rail item** or **widget** (Home
or a Drive face) opens edit mode for that surface with that item selected, as a long touch
press does (drive-modes spec §7.1).
- **Parked only on a driver-facing display.** While Moving (UI spec §12.1) a long `ok` there
  shows the **"Park to edit"** toast for 3 s and does nothing else; the server refuses layout
  writes from a Moving display anyway (drive-modes rule R1). Phones, desktops and passenger-only displays may
  edit at any time.
- **Exceptions**, so the binding never steals a control's own meaning: an **engaged** control
  (§4.4) and a text field keep their own `ok`; on the **`drive_mode` chip** a long `ok` opens
  the mode list (drive-modes §6), whose **Edit modes…** row (Parked only) is the way in from
  there; inside an open sheet, including the Drive menu, a long `ok` is a plain `ok`.
- A short `ok` keeps every meaning it had (activate; in Drive mode, open the Drive menu from
  `main`, cycle modes on the `drive_mode` chip). The long press fires at 600 ms while held, so
  the release does not also activate. Bindings (§8) may not remove the long `ok`; **Edit
  layout** in More (drive-modes §7.8) stays the always-present D-pad path.

**14.2 `back` finds the switcher while Moving (changes §6's `back` row).** In Drive mode while
Moving, with **nothing open** (no Drive menu, sheet or `alert_card`), `back` moves focus to the
**`drive_mode` chip wherever it sits** in the strip; then a short `ok` cycles modes and a long
`ok` lists them. A second `back` returns focus to `main` (the current face). §6's table row
becomes: "`back` — close the Drive menu or an `alert_card`; otherwise focus the Drive-mode
chip; on the chip, return to the face". `back` still never leaves Drive mode while Moving.
Parked, §4.3 applies unchanged.

**14.3 The switcher is found by id (adds to §4.2).** The strip zone's focus order is its
rendered order, so a reordered strip needs no new arrow rule; the shell locates the switcher
by its id, `drive_mode` (`data-chip="drive_mode"`), never by position. Entering the strip zone
in Drive mode lands on `drive_mode` the first time, then on the chip last focused there (§4.2).
Because the chip is an anchor item (drive-modes §8.1 R9) it can be moved and re-iconed but not
hidden, so the 14.2 target always exists in Drive mode. `left`/`right` inside the strip move
between chips and never switch faces.

**14.4 Tests (adds to §13).** At every head-unit class and with the strip in a shuffled order
(`drive_mode` first, middle, last): while Moving, one `back` from any face focuses the
`drive_mode` chip and one `ok` changes mode; a long `ok` on a strip chip, rail item or widget
opens edit mode Parked and shows "Park to edit" Moving with no layout write; a long `ok` on an
engaged map or slider and in a text field does not open edit mode; a long `ok` on `drive_mode`
opens the mode list; the long press never also fires a short `ok`; Playwright locates the
switcher only by `data-chip="drive_mode"`.

## Changelog

- 2026-10-07: v0.1, draft (DMD round): intents, sources, zones, Drive menu, confirm rules,
  focus-ring token, display-owned bindings and key test, amendments listed, U2 phasing.
- 2026-10-07: v0.2, proposed amendment §14 (DMD round, cross-spec reconcile), pending the
  owner: adopts drive-modes spec v0.2 decision 15: a long `ok` (600 ms) on a focused strip
  chip, rail item or widget enters edit mode when Parked ("Park to edit" toast while Moving);
  while Moving in Drive mode, `back` with nothing open moves focus to the Drive-mode chip
  wherever it sits; the switcher is found by id; tests; decisions 10–12.
- 2026-10-07: v0.3, approved by the owner on 2026-10-07 ("approve all", DMD round; decision
  list items 41–46 and 90): every decision answered as recommended (alternatives not
  chosen); §14 renamed "Amendment (2026-10-07, DMD round), approved"; ships with U2 (I1–I2).
- 2026-10-07: v0.4, amended (OS round, approved by the owner on 2026-10-07, "approve all";
  decision list item 54): voice control is no longer a non-goal.
- 2026-10-07: v0.5, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", [ADR-0047](../decisions/adr-0047-openness-round.md)): the focus-ring values
  are defaults a theme may restyle while focus stays visible and nothing reflows in Moving
  templates.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each recommendation
below is the decision; each alternative was not chosen.

1. **Adopt ShellInput in core?** Recommend: yes, a platform feature, free, with hardware remotes as
   hardware add-ons that only supply key events. Alternative: an input add-on.
2. **Ship in U2?** Recommend: I1 and I2 in U2 alongside the lockouts. Alternative: after U2.
3. **Drive menu while Moving?** Recommend: one `short_list`, ≤ 6 driver-safe rows, order set Parked
   per display. Alternative: DMD's family rail at speed (breaks §12.1).
4. **Who owns bindings?** Recommend: the display's install configuration; user preferences never
   change a driver-facing display's bindings while Moving. Alternative: per signed-in user.
5. **Input events on the module bus?** Recommend: `event/input.button`, QoS 0, never retained,
   1 s expiry, dropped after 500 ms. Alternative: read the retained VSS reading and de-duplicate.
6. **Focus ring?** Recommend: 3 px `accent` with a 2 px `bg` gap everywhere, no glow, no resize.
   Alternative: 4 px on head units (teardown §5).
7. **Double-press bindings?** Recommend: not in v1. Alternative: DMD-style double press bound to
   one Drive-menu row.
8. **Arrows on desktop?** Recommend: navigate only once focus is on a focusable, so arrow scrolling
   still works. Alternative: always navigate, as on head units.
9. **Touch lock for wet or gloved displays?** Recommend: a strip chip that disables touch with the
   D-pad still live, on head units only, as a follow-up (teardown Copy 7). Alternative: none.
10. **Long `ok` for editing (§14.1)?** Recommend: yes, a long `ok` (600 ms) on a focused strip
    chip, rail item or widget enters edit mode when Parked, "Park to edit" for 3 s while
    Moving; engaged controls, text fields and the `drive_mode` chip keep their own long `ok`;
    bindings cannot remove it. Alternative: no new binding; the D-pad reaches edit mode only
    through More → Edit layout.
11. **`back` focuses the switcher while Moving (§14.2)?** Recommend: yes, in Drive mode with
    nothing open, `back` moves focus to the `drive_mode` chip wherever it sits and a second
    `back` returns to the face. Alternative: keep §6's "otherwise nothing" and reach the chip
    by arrows into the strip zone (more presses, depends on strip order).
12. **Find the switcher by id (§14.3)?** Recommend: yes, `drive_mode` by id for focus rules and
    tests, the strip's focus order following its rendered order. Alternative: pin the chip to a
    fixed strip position (contradicts the movable strip of drive-modes v0.2).
