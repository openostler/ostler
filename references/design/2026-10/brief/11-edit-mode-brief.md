---
title: "Designer brief addendum — edit mode, the layout carousel and the D-pad, and native Android extras (95 frames)"
area: references
status: draft
version: 1.0
updated: 2026-10-12
depends_on: [references/design/2026-10/brief/10-shell-brief.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, specs/2026-10-11-ostler-shell-design.md, references/research/touch_tiling_edit_mode.md, references/design/2026-10/shell-ui/README.md]
summary: >
  The addendum to the shell designer brief (10-shell-brief) for the owner and designer's layout-manager rethink, decided in ADR-0052 v0.7 on 2026-10-12, written per section by three sub-agents and assembled. No permanent divider bars: a parked-only, press-and-hold edit mode like the Android home-screen editor (grabbable edges, remove buttons, a page tray like a widget picker with live previews, a live snap preview with class labels and haptics, the dwindle split, move and swap, Show frame for Chip and Compact widgets, a non-drag path driven by the D-pad cursor, Done and Undo, and leaving edit mode when the car moves). A slimmer strip with layout dots, a carousel of saved layouts (swipe when parked; the D-pad cursor crossing the screen edge pages to the next layout, also while moving; triggers), layout management inside edit mode, and the optional soft-key row. Native Android extras only when the Gateway app hosts the shell: Android widgets as tiles with consent, and Open beside. Three sections: E edit mode (33 frames), F layouts, the carousel and the D-pad (40), G native Android extras (22). Supersedes the shell kit's divider and snap frames and the strip's layout switcher and Manage layouts frames.
---

# Designer brief addendum — edit mode, the carousel and the D-pad

**For the designer of the shell.** This adds to the [shell brief](10-shell-brief.md) and uses its
format, terms, screens and size classes. It follows the owner's decisions of 2026-10-12, recorded
in [ADR-0052](../../../../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md) §2a and §4a
and the [shell spec](../../../../specs/2026-10-11-ostler-shell-design.md) §19, with the
[touch tiling research](../../../research/touch_tiling_edit_mode.md) behind them. Themes are
decided (Themes v2); this addendum adds no theme rules.

## What changes

- **No permanent divider bars.** Outside edit mode tiles are separated only by the gap and stay
  fully usable. The snap guide lines go too.
- **Edit mode,** like the Android home-screen editor, parked only: press and hold a tile or empty
  space, or start it from the wheel. Edges become grabbable, each tile gets a remove button, a
  page tray works like a widget picker, snapping shows the result itself, and Done leaves.
- **The steering wheel is a D-pad with a cursor.** It moves the focus ring to the nearest tile;
  up from the top row reaches the strip; moving off the left or right screen edge pages to the
  previous or next saved layout (no wrap-round). This works while moving, and in edit mode it
  selects the tile that edit actions apply to.
- **A carousel of saved layouts** with dots in the strip replaces the layout dropdown. Swipe on
  the strip or from the screen edge when parked; while moving, only the wheel and automatic
  triggers change layouts. Layouts are named, saved, ordered and deleted in edit mode.
- **The soft-key row is optional** (a shared setting, on by default on head units).
- **Widgets:** a Chip or Compact tile with "Show frame" off.
- **Native Android extras** only when the Gateway Android app hosts the shell: Android widgets
  as tiles and Open beside for native apps.

## Kit frames this replaces

- **Section A:** the divider bars, drag handles and snap guides (A.5) and their frames; drag
  editing moves into edit mode (section E).
- **Section B:** the layout switcher menu (B5) and the Manage layouts sheet (B6); the top strip
  (B1) is updated (section F).
- **Section C:** the focus order (C8) becomes spatial, and the soft-key row (C7) becomes optional
  (section F).

## How to read a block

As in the shell brief: **Purpose**, what it **Holds**, its **States**, the **Sizes** it uses, the
frames to **Draw**, the **Rules**, its **Interactions** and **Reference**. Each section ends
with its frame list (ids E-01, F-01, G-01) and open questions.

## E. Edit mode

Edit mode is the one place where the owner changes a layout: resizing, moving, adding, splitting and removing tiles. It replaces the permanent divider bars and drag handles in section A (A.5 and frames A-09 to A-13). Outside edit mode there are no bars: tiles are separated only by the gap and every tile stays fully usable. Edit mode works like the Android home-screen editor. It is for the parked car only, and every action in it can be done without dragging.

Terms used in this section:

- **Tile:** one rectangle on screen that shows one page from any app.
- **Page:** one screen from an app, for example Diagnose's fault list or the Heading instrument.
- **Layout:** an arrangement of tiles. A **saved layout** has a name, such as Trail, Commute or Workshop. Saved layouts sit side by side like home-screen pages, with dots in the strip.
- **Size class:** one of five designs a page can show (Badge, Chip, Compact, Standard, Expanded). The class comes from the tile's own pixel box, never from the device.
- **Size range:** the smallest and largest size class a page declares it can show. A tile's edges cannot be dragged beyond that range.
- **Edit mode:** a separate state of the screen in which drags move and resize tiles instead of reaching the page. It opens only while parked.
- **Page tray:** the picker of pages in edit mode, like Android's widget picker.
- **Anchor:** a point an edge snaps to while being dragged: ⅓, ½, ⅔ of the screen, and each size-class boundary.
- **Live snap preview:** while an edge is dragged, the tiles redraw at the snapped result, each showing the class it will land in. There are no guide lines.
- **Haptic:** a short vibration, where the device can give one (through the Gateway Android app on head units, or the browser where it supports it). Every haptic must also have a visible cue.
- **D-pad cursor:** the steering-wheel buttons act as a D-pad (up, down, left, right, OK and Back). Up, down, left and right move a cursor (the focus ring) to the nearest tile in that direction. In edit mode the cursor picks the **selected tile** that edit actions apply to.
- **Soft-key row:** an optional row of labelled actions along the bottom. It is a shared setting: on by default on head units and off on phones and desktops. When it is off, the same actions are in the tile's label menu and on the D-pad.
- **Widget:** a Chip or Compact tile with "Show frame" turned off. There is no separate widget system.
- **Unsaved edits:** changes to a layout that have not yet been saved over it or saved as a new layout.
- **Moving / Parked:** car state from the gateway. "Motion unknown" counts as moving.
- **Gateway-hosted shell:** an option in which the Gateway Android app shows the shell full screen. Only there can native Android widgets be tiles. This never happens in the browser or the installed web app (PWA).

Kit components to reuse: tile, strip, menu, sheet, softkeys, banner, toast.

### E1. Entering edit mode

**Purpose**
- Open edit mode on purpose, by touch or by the wheel, and never while moving.

**Holds**
- A press-and-hold cue on the pressed tile or empty space, showing the hold is being counted.
- An "Edit layout" item that the wheel can reach. Where it lives is open (question 1).
- A refusal toast for when the car is moving.

**States**
- **Holding:** after about 0.5 s the cue completes, a haptic fires, and edit mode opens.
- **Released early:** nothing happens. A tap still reaches the page as usual.
- **Entered from the wheel:** edit mode opens with the D-pad cursor's tile already selected (E8).
- **Moving:** edit mode does not open. A text-only toast gives the reason, for example "Edit layout: park first". The toast lasts about 4 s and comes with a stronger "refused" haptic. The same toast covers a hold, the wheel and a keyboard.

**Sizes**
- Any tile class, and empty space. On a Badge the cue must still be visible around the tile.

**Draw**
- The hold cue on a tile and on empty space, then the moment edit mode opens. 7in, Parked.
- Entry from the wheel. 7in, Parked.
- The refusal toast. 7in, Moving.

**Rules**
- Parked only. Nothing in edit mode is reachable while moving.
- The hold must not fire by accident on maps and charts that have their own long press (question 2).
- A gloved thumb resting on the bezel must not start a hold (question 3).

**Interactions**
- Press and hold a tile or empty space for about 0.5 s.
- From the wheel: move the cursor to "Edit layout" and press OK.
- Keyboard and desktop: the same "Edit layout" item, reached by focus.

**Reference**
- Kit: toast (refusal), tile (hold cue), menu.

### E2. The edit-mode screen

**Purpose**
- Make it obvious that the layout is being edited, and show what can be grabbed.

**Holds**
- The whole layout, scaled down slightly so there is room around it.
- On each tile: grabbable edges, a remove button, the page name and its current size class.
- A large **Done**. An **Undo**. A way to open the page tray (E3) and the presets (E5).
- The layout's name, and a mark when there are unsaved edits.
- Layout management (name, save, save as new, order, delete, automatic triggers, Save to phone) also lives in edit mode. It is covered in its own block of this addendum and only needs a way in here.

**States**
- At rest, with no tile selected.
- A tile selected by the cursor or a tap: a clear selection ring and its edit actions (E8).
- Dragging an edge (E4) or a tile (E6): the other controls step back.
- Unsaved edits: the mark is shown and Done leads to the save choice (E9).
- One tile left: its remove button is disabled with a reason ("A layout needs one tile").
- A warning arrives: it takes its usual place (a takeover or a band) over edit mode, and edits are kept.

**Sizes**
- Every screen: phone 393x852, 5in 800x480, 7in 1024x600, 10in 1280x720, tablet, desktop, and Android split half and third.
- On 5in and in a split third, space is tight. The scale-down, Done and the tray entry must still leave tiles large enough to grab.

**Draw**
- A 2+1 layout at rest on 7in (Night and Day), 5in, phone and Android split third.
- The same on 7in, mirrored for RHD.

**Rules**
- Tiles are not live inputs in edit mode: a drag moves or resizes and never reaches the page. Pages keep showing real content.
- The remove button and edges are large enough for a gloved finger. Their touch areas may be larger than they look.
- Done is the largest control and sits in a stable place.
- RHD mirrors the whole screen, edit controls included.

**Interactions**
- Tap a tile to select it. Tap empty space to clear the selection.
- Tap a remove button: the tile goes at once, with Undo (no confirmation dialogue).
- Tap Done to leave (E9). Back on the wheel also asks to leave.

**Reference**
- Kit: tile, strip, toast. Replaces the A.5 divider frames.

### E3. Page tray

**Purpose**
- Choose a page to add, the way Android's widget picker works.

**Holds**
- Search.
- Categories by app (Diagnose, Logs, Map, the gateway's instruments and so on).
- A live preview of each page, drawn at the size class it would land in on this screen and in this layout.
- In the gateway-hosted shell only, a category for Android widgets from other apps, with a one-time consent step from Android.

**States**
- Open (a bottom panel on head units, a sheet on phone and in split windows).
- Searching. No results ("No pages match").
- A page dragged out of the tray: the tray gets out of the way and drop targets show (E5).
- A page picked with the D-pad, waiting for a place (select and place).
- A page that cannot fit anywhere in this layout: shown, but marked with the reason.
- An app that is installed but offline or stale: its preview shows that state, as section D does.

**Sizes**
- Previews are at the class the page would land in: usually Chip to Standard. A preview may fall back to a Chip if that is what would really show.

**Draw**
- The tray with categories and previews. 7in, Night and Day.
- Search results. Phone.
- The gateway-hosted tray with an Android widgets category and the consent step. 10in.
- A page selected by D-pad and waiting to be placed. 7in.

**Rules**
- Previews tell the truth: what the tray shows is what the tile will show.
- Native Android widgets appear only in the gateway-hosted shell, never in the PWA.
- The tray must not hide the drop targets it is used with.

**Interactions**
- Drag a preview onto a tile or a screen edge (E5).
- Or select it, then move the cursor to a tile or edge and press OK to place it.
- Back closes the tray.

**Reference**
- Kit: sheet, menu, tile. Replaces the Swap page picker (A-05) as a way to add tiles; Swap page stays in the label menu.

### E4. Resize with the live snap preview

**Purpose**
- Resize tiles by dragging an edge, and show the result before release.

**Holds**
- A grabbable edge on each tile side that touches another tile.
- Anchors at ⅓, ½, ⅔ and at each size-class boundary.
- Each tile's size-class name, shown while dragging.

**States**
- **Grabbed:** a light haptic. The edge is clearly held.
- **Dragging:** the edge snaps from anchor to anchor. All affected tiles reflow to the snapped result and show the class they will land in. A light haptic fires on each snap.
- **At the limit:** the edge stops where a neighbour would go above its largest class, or where this tile would go below its smallest, if removal is not allowed. A stronger haptic marks the stop.
- **Will be removed:** dragging a tile past its smallest class shows that it will go on release.
- **Released:** the result stays. A removed tile leaves an Undo toast for about 10 s.

**Sizes**
- All classes. On 5in the class boundaries sit close together, so snaps come quickly.

**Draw**
- Mid-drag at ½, with tiles reflowed and class labels. 7in.
- An edge stopped at a page's largest class. 7in.
- Past the smallest class, then the Undo toast after release. 7in.
- Mid-drag on 5in 800x480.

**Rules**
- No guide lines and no ghost outline: the preview is the reflowed tiles themselves.
- Edges never crop a page. They stop at its size range.
- A resize never silently pushes another tile off the screen.
- The last tile cannot be removed.

**Interactions**
- Drag an edge and release. Drag past the smallest class to remove, then Undo to bring it back.

**Reference**
- Kit: tile (class label), toast (Undo). Replaces A-09 and A-10.

### E5. Add and split

**Purpose**
- Add a page by splitting the space it is dropped on, and offer quick starting layouts.

**Holds**
- Drop targets: each tile, and each screen edge.
- Presets: Full, Halves, 2+1 and Quad.

**States**
- **Over a tile:** a preview shows the tile split along its longer side (side by side if it is wide, top and bottom if it is tall), with both halves at their resulting classes.
- **Over a screen edge:** a preview shows a new tile along that edge, with the rest reflowed.
- **Cannot split:** a half would fall below either page's smallest class. The target says so and refuses the drop.
- **Preset chosen:** the current pages are placed into the preset. Pages that do not fit become chips, as the window rules do. Undo is available.

**Sizes**
- All screens. On phone portrait most tiles are tall, so most splits are top and bottom.

**Draw**
- A tray page held over a tile, showing the split. 10in 1280x720.
- The same held over a screen edge. 10in.
- A refused split. 5in.
- The presets applied to the current pages. 7in.

**Rules**
- Split along the longer side by default. No user choice of direction is needed.
- Presets are starting points, not modes. After a preset, everything can still be edited.

**Interactions**
- Drag from the tray and release on a target, or select and place with the D-pad.
- Tap a preset.

**Reference**
- Kit: preset, tile. Replaces A-12's "edge split" half.

### E6. Move and swap

**Purpose**
- Rearrange tiles without changing the layout's shape.

**Holds**
- A held tile that follows the finger, and a clear swap target under it.

**States**
- Picked up (after a short hold in edit mode, with a haptic). Over a tile (swap target shown). Over nothing (the tile returns home on release). Swapped.

**Sizes**
- Any. When a page lands at a size outside its range, it falls back as the window rules say, and the preview shows that before release.

**Draw**
- A tile held over another, with the swap target. 10in 1280x720.
- After the swap. 10in.

**Rules**
- A swap exchanges the two pages and keeps both rectangles.
- Swapping ends any link between the two tiles, as section A says.

**Interactions**
- Drag a tile onto another and release. With the D-pad, use Move before or Move after (E8).

**Reference**
- Kit: tile (drag state). Replaces A-11 and the swap half of A-12.

### E7. "Show frame" (widgets)

**Purpose**
- Let a small tile drop its frame and label so it reads as a widget.

**Holds**
- A "Show frame" switch in the selected tile's edit actions.

**States**
- On (the normal tile, with frame and label).
- Off (a widget: page content only, no frame or label).
- Not available: the tile is Standard or larger. The switch is hidden or disabled with a reason.
- A frameless tile resized to Standard: the frame comes back, and the setting is kept for when the tile is small again (question 8).

**Sizes**
- Chip and Compact only.

**Draw**
- A Compact tile with its frame on and off. 7in, Night and Day.
- The switch not available at Standard. 7in.

**Rules**
- A widget still takes focus, shows the focus ring and shows caution and warning states. Locked safety colours and icons are never hidden.
- The label menu must stay reachable without a label (question 7).
- Pages do not need to opt in. This is a tile setting.

**Interactions**
- Select the tile, then toggle "Show frame".

**Reference**
- Kit: tile (frameless variant to add).

### E8. The non-drag path (D-pad, keyboard and switch access)

**Purpose**
- Do every edit without dragging: by the wheel, a keyboard or switch access.

**Holds**
- A selected tile, moved by the D-pad cursor.
- Edit actions for it: **Move before**, **Move after**, **Wider**, **Narrower**, **Taller**, **Shorter**, **Remove**, **Add beside** and **Show frame** (Chip and Compact only).
- An announcement after each action, giving the new size, for example "Logs: two thirds wide, Standard".

**States**
- **Soft-key row on:** the row shows the selected tile's edit actions.
- **Soft-key row off:** the actions are in the selected tile's edit menu, opened with OK.
- **An action that would break a size range:** disabled, with the reason ("Logs is already at its largest").
- **Add beside:** opens the tray (E3), then places the page beside the selected tile, splitting along the longer side.

**Sizes**
- All. Wider and Narrower step to the next anchor, the same anchors as dragging.

**Draw**
- A selected tile with edit actions in the soft-key row. 7in.
- The same actions in the tile's edit menu, with the soft-key row off. 7in.
- The announcement after "Wider". 7in.
- Edit mode with keyboard focus. Desktop 1440x900.

**Rules**
- Every action that touch can do here, the D-pad can do too.
- Announcements are visible on screen and read by screen readers.
- Focus moves spatially to the nearest tile, as outside edit mode.

**Interactions**
- Arrows move the selection. OK opens the actions (or uses a soft key). Back steps out of a menu, then asks to leave edit mode.
- Whether moving the cursor off a screen edge still pages to the next layout in edit mode is open (question 5).

**Reference**
- Kit: softkeys, menu, tile (focus ring).

### E9. Done, Undo and unsaved edits

**Purpose**
- Leave edit mode safely, and never lose or silently overwrite a layout.

**Holds**
- **Undo:** steps back through this session's edits one at a time.
- **Done.**
- A save choice when there are unsaved edits: **Save over "Trail"**, **Save as new** (asks for a name) and **Discard**.

**States**
- **No changes:** Done just leaves.
- **Changes:** Done opens the save choice. Backing out of the choice returns to edit mode.
- **Save as new:** the new layout is added to the carousel next to the old one and becomes current.
- **Discard:** the layout returns to its saved state.
- **Offline:** saves are kept on this screen and marked "Not synced yet", as section B does.

**Sizes**
- A sheet on phone and in split windows. A menu or centre sheet on head units.

**Draw**
- The save choice. 7in and phone.
- Undo after several edits. 7in.

**Rules**
- Removal never asks for confirmation. It uses Undo instead. Discard is the only step that throws edits away, and it is clearly labelled.
- Renaming uses the keyboard, so only while parked.

**Interactions**
- Tap or press OK on Done, then pick one of the three choices. Tap Undo, or use it from the D-pad.

**Reference**
- Kit: sheet, menu, toast. Replaces the save parts of B6 (Manage layouts).

### E10. When the car starts moving in edit mode

**Purpose**
- Get out of the driver's way at once, without losing work.

**Holds**
- The normal, non-edit screen showing the edited arrangement.
- The layout's unsaved mark in the strip.
- One text-only toast, for example "Layout edits kept. Park to save."

**States**
- **Moving starts mid-drag:** the drag is cancelled. The tile goes back to its last snapped result.
- **Moving starts with the tray or a save choice open:** they close.
- **Edits kept as unsaved:** the screen keeps working normally with the edited layout.
- **Parked again:** how the owner is asked to save is open (question 6).
- **Motion unknown:** treated as moving.

**Sizes**
- All. Moving rules apply: text at least 24 px, larger targets.

**Draw**
- Edit mode on 7in, then the same screen just after moving starts, with the toast and unsaved mark. Moving, LHD and RHD.
- Moving starts mid-drag. 7in.

**Rules**
- Edit mode leaves at once. There is no countdown and no dialogue.
- The driver is told once. Nothing repeats or makes a sound.
- Layout paging by the wheel and automatic triggers still works while moving.

**Interactions**
- None needed from the driver.

**Reference**
- Kit: toast, strip. Replaces A-13 (layout locked while moving).

### Frame list

1. E-01 — Press and hold: hold cue on a tile and on empty space, then edit mode opening · 7in 1024x600 · LHD · Night · Parked
2. E-02 — Edit mode entered from the wheel ("Edit layout" with the cursor) · 7in 1024x600 · LHD · Night · Parked
3. E-03 — Refused while moving: refusal toast · 7in 1024x600 · LHD · Night · Moving
4. E-04 — Edit-mode screen at rest, 2+1 layout · 7in 1024x600 · LHD · Night, Day · Parked
5. E-05 — Edit-mode screen at rest · 5in 800x480 · LHD · Night · Parked
6. E-06 — Edit-mode screen at rest, mirrored · 7in 1024x600 · RHD · Night · Parked
7. E-07 — Edit-mode screen at rest · phone 393x852 · LHD · Night · Parked
8. E-08 — Edit-mode screen at rest · Android split third (~340x600) · LHD · Night · Parked
9. E-09 — One tile left: remove disabled with reason · 5in 800x480 · LHD · Night · Parked
10. E-10 — Page tray: categories and live previews · 7in 1024x600 · LHD · Night, Day · Parked
11. E-11 — Page tray: search results · phone 393x852 · LHD · Night · Parked
12. E-12 — Page tray in the gateway-hosted shell: Android widgets category and consent step · 10in 1280x720 · LHD · Night · Parked
13. E-13 — Page selected by D-pad, waiting to be placed · 7in 1024x600 · LHD · Night · Parked
14. E-14 — Edge drag mid-snap at ½: tiles reflowed with class labels · 7in 1024x600 · LHD · Night · Parked
15. E-15 — Edge stopped at a page's largest class · 7in 1024x600 · LHD · Night · Parked
16. E-16 — Drag past the smallest class, then the Undo toast after release · 7in 1024x600 · LHD · Night · Parked
17. E-17 — Edge drag with close class boundaries · 5in 800x480 · LHD · Night · Parked
18. E-18 — Tray page held over a tile: split along the longer side · 10in 1280x720 · LHD · Night · Parked
19. E-19 — Tray page held over a screen edge: edge split · 10in 1280x720 · LHD · Night · Parked
20. E-20 — Refused split (a half below a page's smallest class) · 5in 800x480 · LHD · Night · Parked
21. E-21 — Presets (Full, Halves, 2+1, Quad) applied to the current pages · 7in 1024x600 · LHD · Night · Parked
22. E-22 — Move and swap: a tile held over another, then after the swap · 10in 1280x720 · LHD · Night · Parked
23. E-23 — "Show frame" on and off on a Compact tile (widget look) · 7in 1024x600 · LHD · Night, Day · Parked
24. E-24 — "Show frame" not available at Standard · 7in 1024x600 · LHD · Night · Parked
25. E-25 — D-pad selection with edit actions in the soft-key row · 7in 1024x600 · LHD · Night · Parked
26. E-26 — D-pad edit actions in the tile's edit menu (soft-key row off) · 7in 1024x600 · LHD · Night · Parked
27. E-27 — Announcement after "Wider" · 7in 1024x600 · LHD · Night · Parked
28. E-28 — Edit mode with keyboard focus · desktop 1440x900 · LHD · Day · Parked
29. E-29 — Done with unsaved edits: Save over, Save as new, Discard · 7in 1024x600 and phone 393x852 · LHD · Night · Parked
30. E-30 — Undo after several edits · 7in 1024x600 · LHD · Night · Parked
31. E-31 — A warning arriving in edit mode (takeover or band over the edit screen) · 7in 1024x600 · LHD · Night · Parked
32. E-32 — Car starts moving in edit mode: normal screen, unsaved mark, one toast · 7in 1024x600 · LHD, RHD · Night · Moving
33. E-33 — Car starts moving mid-drag: the drag is cancelled · 7in 1024x600 · LHD · Night · Moving

### Open questions

1. **"Edit layout" from the wheel.** Where should it live: in the strip (reached by pressing up from the top row), in each tile's label menu, or both? Is a dedicated wheel gesture also needed, given that a long Select already opens the alerts list?
2. **Press and hold against a page's own long press.** Maps and charts may use long press themselves, and section A's label menu (Open beside) used one too. Should press and hold enter edit mode only on the label and empty space, with a page's own long press taking priority on its content, or everywhere after 0.5 s?
3. **A thumb resting on the bezel.** Should tiles keep a margin near the screen edge where a resting thumb cannot start a hold?
4. **Soft-key row in edit mode.** When the row is on, nine edit actions do not fit in five keys. Which actions get keys, and which go in the edit menu? Should "More" always be the last key?
5. **Paging off the screen edge in edit mode.** Should moving the cursor off the left or right edge still page to the next saved layout (carrying edits as unsaved), stop at the edge, or ask first?
6. **Saving unsaved edits after the car parks.** Should a banner offer "Save layout edits?" on parking, or should the unsaved mark wait until the owner next opens edit mode? How long are unsaved edits kept, and do they survive switching layouts?
7. **The label menu on a widget.** With "Show frame" off there is no label to tap. Should the menu open by a tap on the widget, the D-pad's OK, or only in edit mode?
8. **"Show frame" when a widget grows.** When a frameless tile is resized to Standard or larger, should the setting come back on its own when the tile shrinks again, or reset to on?
9. **A limit on tiles.** Should edit mode cap the number of tiles per screen (for example four, as Open beside does), or rely on size ranges and the window rules alone?
10. **Undo history.** Should Undo reach back through the whole edit session, or only the last action? Should a removed tile's 10 s Undo toast also appear in edit mode, where the Undo button is already shown?

## F. Layouts, the carousel and the D-pad

This section replaces the layout switcher menu (B5) and the Manage layouts sheet (B6) from the original brief, and updates the top strip (B1), the soft-key row (C7) and the focus ring (C8). Saved layouts now sit side by side like the pages of a phone's home screen. You move between them by swiping when parked, by the steering wheel at any time, or by an automatic trigger. Layouts are created, named and organised only in edit mode.

Terms used here:
- **Layout:** an arrangement of tiles on one screen. A **saved layout** has a name, such as Trail, Commute or Workshop. Each saved layout belongs to one car and one screen (head unit, phone and so on), and the gateway stores and syncs it.
- **Carousel:** the row of saved layouts, side by side in the user's order. Only one shows at a time. The carousel stops at the first and last layouts, with **no wrap-round** (moving past the last layout does not bring you back to the first).
- **Layout dots:** one small dot per saved layout in the top strip. The filled dot is the layout on screen.
- **Name flash:** the layout's name, shown briefly in the strip after every change of layout and then replaced by the dots.
- **Edit mode:** the parked-only mode for changing a layout, like a phone's home-screen editor. You enter it by pressing and holding a tile or empty space (about 0.5 s, with a haptic, which is a short vibration) or from the wheel, and leave it with a large Done. All layout management lives here.
- **D-pad:** the car's existing steering-wheel buttons used as up, down, left, right and Select. Ostler adds no buttons of its own.
- **Cursor / focus ring:** the visible outline (3 px, with a 2 px gap, no glow, no animation) that shows which tile or item the D-pad is on. It appears only after a button press, never after touch.
- **Automatic trigger:** a car event that switches layout by itself. There are three: the car starts, low range engages, or the car is parked.
- **Soft-key row:** an optional row of up to five labelled actions along the bottom of the screen, belonging to the focused tile's page.
- **Tile label menu:** the menu that opens from a tile's label (Swap page, Page settings, Open beside, Close).
- **ACK:** acknowledging a warning. Steering-wheel Select does this, but only while a warning is showing.
- **Moving / Parked:** the car's state, as reported by the gateway. "Unknown" counts as moving. While moving, text is at least 24 px, touch targets are larger and editing is locked.
- **Toast:** a short message that appears and disappears by itself. While moving it is text only.

Kit components used: strip, tile, menu, sheet, softkeys, banner, toast. Do not invent new chrome where one of these fits.

### F1. Top strip, slimmer

**Purpose**
- The same glanceable bar as B1, but lighter: the layout dropdown goes, and the layout dots take its place.

**Holds** (from the driver's side outward)
1. **Layout dots**, with the name flash in the same spot. A small lock icon sits beside them while moving. It shows status only and is not a button.
2. **Connection chip**, as B2.
3. **Vehicle chip**, as B3. It reads together with the connection chip, for example "Connected · Discovery 2".
4. **Warning strip**, as B1. It takes the remaining width.
5. **Settings button** (gear), at the passenger-side end, as B4.

There is no clock and nothing else.

**States**
- **Resting:** dots only, with the current dot filled.
- **Name flash:** after any change of layout (swipe, wheel, trigger, Done in edit mode, or app open), the layout's name replaces the dots briefly and then fades back to them. While moving, it cuts back with no fade.
- **Triggered switch:** the name flash carries the reason, for example "Off-road · low range". See F4.
- **One saved layout, or none:** no dots. See F6.
- **Moving:** the dots and lock appear at moving size. The name flash text is at least 24 px.
- **Many layouts:** the dots must still fit in the slot without pushing the chips. One option is to compress the outer dots, as phone launchers do; this is an open question.
- **Not connected, caution, warning, several alerts, offline, viewing another car:** as B1 to B3, unchanged.
- **RHD (right-hand drive):** the strip mirrors, so the dots sit at the right edge and the gear at the left.

**Sizes**
- Height as before: 48 px or less on 480 px-high screens, 56 px by default and 52 px on a phone (kit tokens).
- **Wide (10in, tablet, desktop):** dots, and the full name flash.
- **Medium (7in, 5in, Android split half):** dots, and the name flash shortened with an ellipsis.
- **Narrow (phone, Android split third):** dots, or a compact form such as "2 / 5" if the dots do not fit (open question). The connection and vehicle chips merge as in B1.
- The space freed by removing the dropdown goes to the warning strip. Chips do not move to fill it.

**Draw**
- 7in 1024x600: resting, and the name flash just after a change (two states, one frame).
- 7in 1024x600, moving: dots, lock and a 24 px name flash.
- 7in 1024x600, RHD: mirrored.
- 5in 800x480: measured at 48 px, with a full tile still reaching Expanded.
- Phone 393x852 and Android split third: narrow form.
- Day for the 7in resting frame only. Theme styling comes from the decided Themes v2.

**Rules**
- The order is fixed and mirrors for RHD. Users cannot reorder the strip.
- The dots show position, not identity. The name flash is the only place the strip shows a layout's name.
- The name flash must never cover a warning or caution in the warning strip.
- The strip never grows to fit the name.

**Interactions**
- **Swipe left or right on the strip** (parked): pages the carousel (F2).
- **Tap the dots:** shows the name flash again. Whether a tap on a single dot jumps straight to that layout is an open question.
- **Focus:** the strip is a focus zone above the tiles. Left and right move along its items; OK on the dots shows the name flash.
- **No long press** on the strip. Edit mode is entered from the tiles or the wheel, not from here.

**Reference**
- Kit: strip (its `layout` option becomes the dots). Replaces frames B-15 to B-19 (layout switcher menu).
- png: mfd-v2-trail-moving.png, mfd-v2-right-hand-drive.png, core-sizes-5in.png.

### F2. Layout carousel

**Purpose**
- Make switching between saved layouts feel like turning pages of a phone home screen: fast, spatial and predictable.

**Holds**
- All saved layouts for this car and this screen, side by side in the user's order.
- The layout dots in the strip, showing where you are.

**States**
- **Resting:** one layout fills the tile area.
- **Dragging (parked):** the current layout follows the finger and the next one slides in beside it. Release past a threshold to commit; otherwise it springs back.
- **Committed:** the new layout settles, the dot moves and the name flash shows.
- **At the first or last layout:** a pull past the end gives resistance (a short rubber-band stretch that springs back), a light haptic where available, and the end dot pulses once. Nothing wraps round.
- **Moving:** swiping does nothing, because while moving layouts change only by the wheel and triggers. When the wheel or a trigger switches layout, it uses a short slide or a straight cut with no effects (open question).
- **Edit mode open:** the carousel is frozen. Paging and triggers wait until Done.
- **Warning showing:** the warning keeps its place, either as a takeover or as a band, on every layout you move to. A switch never hides it.
- **Offline:** switching works from the cached layouts.

**Sizes**
- The same on every screen. The edge gesture zone (the strip of screen edge where a swipe starts) stays narrow, so a thumb resting on the bezel does not trigger it.

**Draw**
- 7in 1024x600, parked: mid-swipe between Workshop and Trail, both layouts partly visible.
- 7in 1024x600, parked: pulling past the last layout (resistance and end dot).
- 7in 1024x600, RHD, parked: mid-swipe, mirrored strip.
- Phone 393x852, parked: edge swipe in portrait.
- 10in 1280x720, parked: a swipe starting on a map tile does not page (show the map panning instead, with a note).

**Rules**
- Swipes page the carousel only on the strip or from the screen's left or right edge. **Never on a tile**, because maps, charts and lists need the swipe.
- No wrap-round.
- Swiping is parked only. The wheel and triggers work while moving.
- The carousel order is the order set in edit mode (F5), and the wheel's single "next layout" key uses the same order.
- No permanent divider bars appear in any carousel state. Tiles are separated only by the gap.
- In the PWA (the web app installed from the browser), the carousel shows only Ostler pages. When the Gateway Android app hosts the shell full screen (an option inside that app), a layout may also hold native Android widgets as tiles. They page with the layout like any other tile.

**Interactions**
- Swipe on the strip or from the screen edge (parked). The D-pad off the screen edge (F3). The "next layout" key. Automatic triggers (F4).

**Reference**
- Kit: scr, tile, strip. Research pattern: home-screen pages with page dots.

### F3. D-pad cursor

**Purpose**
- Let the driver reach every tile, the strip and other layouts with the steering-wheel buttons alone, at any speed.

**Holds**
- The focus ring on a tile, on an item inside a tile, or on a strip item.
- The name flash in the strip when the cursor pages to another layout.

**States**
- **No ring:** after touch. The first button press shows the ring on the last focused tile, without moving it.
- **Tile focused:** the ring is on the tile frame. The tile's soft keys show in the row if the row is on.
- **Moving between tiles:** up, down, left and right move the ring to the **nearest tile in that direction**, measured on screen (spatial), not by a fixed order.
- **Up from the top row:** the ring enters the strip, on the item nearest above. Down from the strip returns to the tile below.
- **Down from the bottom row:** the ring enters the soft-key row if it is on. Otherwise nothing happens.
- **Off the left or right screen edge:** the ring pages to the previous or next saved layout. The name flash shows, and the ring lands on the **nearest tile of the new layout** at the edge it came in from (for example, paging right lands on the new layout's left-most tile at about the same height).
- **At the first or last layout:** the ring stays where it is. The end dot pulses and the name flash reads, for example, "Trail · first layout". The ring itself never animates.
- **Inside a tile:** arrows move between items first. At the tile's edge they move to the next tile. Paging to another layout happens only from the tile frame, not from inside a tile (open question).
- **Engaged control** (a slider or map taking the arrows): arrows adjust the control and never page.
- **Warning takeover:** the ring is on ACK and does not leave until the warning is acknowledged or Back is pressed.
- **Moving:** everything above works the same, including paging. Text in the name flash is at least 24 px.
- **Edit mode:** the same cursor selects the tile the edit actions apply to. Paging is off.
- **RHD:** left and right stay screen directions. Whether "next layout" sits to the right in RHD too is an open question.

**Sizes**
- Badge and Chip tiles are one focus stop. Compact and larger tiles can be entered.

**Draw**
- 7in 1024x600, Quad layout: arrows overlaid to show the nearest-tile moves from one tile, and up into the strip.
- 7in 1024x600, a 2+1 layout with uneven tiles: where right goes from the tall tile, to show the spatial rule.
- 7in 1024x600, moving: two frames, before and after paging off the right edge, with the name flash and the ring on the landing tile.
- 7in 1024x600, moving: at the last layout, with the end dot and the "last layout" flash.
- 7in 1024x600, RHD: the ring in the strip after up from the top row.
- 5in 800x480, moving: the ring with a warning band showing after a page change (the warning keeps its place).

**Rules**
- Every touch action can also be reached with the cursor.
- Focus is never shown by colour alone and is never hidden under the strip, a sheet or a toast.
- **Select and ACK are unchanged:** Select acknowledges a warning only while one is showing, and otherwise activates the focused item. Long Select opens the alerts list, or shows "No alerts" in the strip for 2 s.
- Steering-wheel buttons never change the car beyond acknowledging a warning. Confirmations stay on screen with Cancel focused.
- "Focus next" (one key that steps through tiles in a stable order) stays for keyboards and single-key setups.

**Interactions**
- up, down, left, right: move the ring as above. OK: activate. Back: leave a tile or close a sheet. Menu (long Back): jump to the strip. "next layout": the next saved layout, while moving too.

**Reference**
- Kit: tile (`focus`), strip. Updates C8: spatial movement replaces "driver-side column first".

### F4. Automatic triggers and the triggered switch

**Purpose**
- Bring up the right layout without the driver doing anything, and make clear why the screen changed.

**Holds**
- Three triggers, chosen per layout in edit mode (F5): "When the car starts", "When low range engages", "When parked", or "None".
- A note on the strip and a toast when a trigger fires.

**States**
- **Trigger fires:** the carousel moves to that layout, as if the wheel had paged it. The name flash shows the layout and the reason, for example "Off-road · low range engaged". A toast shows "Switched to Off-road" with Undo for 4 s.
- **Moving:** the same, but the toast is text only with no sound, and the switch is a cut or short slide (as F2).
- **Undo:** returns to the previous layout. The trigger does not fire again until its condition changes.
- **Already on that layout:** nothing shows.
- **Warning takeover showing:** the trigger waits until the warning is acknowledged, then switches.
- **Edit mode open:** the trigger waits until Done.
- **Offline:** triggers come from the gateway. If the gateway is unreachable, no trigger fires.

**Sizes**
- The toast sits at the top, under the strip, and never covers the warning strip or a focused item. On a phone it is the full width.

**Draw**
- 7in 1024x600, moving: low range engages, with the switch to Off-road, the name flash with the reason and a text-only toast with Undo.
- 7in 1024x600, parked: "When parked" fires and Workshop appears.
- 5in 800x480, moving: the trigger waiting behind a warning takeover (show the takeover, plus a note that the switch follows ACK).
- Phone 393x852, parked: car started, with the toast.

**Rules**
- The shell does not detect triggers. It switches only on the gateway's signal.
- One trigger belongs to one layout at most (F5).
- A triggered switch never needs a confirmation. Undo is enough.

**Interactions**
- Tap Undo, or focus the toast and press OK. The toast is a focus stop only while it shows.

**Reference**
- Kit: toast, strip. Carries over B5's automatic-switch state and B6's trigger list.

### F5. Managing layouts in edit mode

**Purpose**
- One place, parked, to name, save, order, delete and automate layouts, and to save one to the phone's home screen.

**Holds**
- A layout bar at the top of edit mode, standing in for the strip. It holds:
  - the layout name, which you tap to rename;
  - a row of layout thumbnails (small previews of each layout's tile arrangement) in carousel order, used for reordering;
  - **Save**, **Save as new** and a more menu.
- The more menu holds: Automatic switching, Save to phone, Delete.
- **Automatic switching** opens a sheet with the three triggers and "None".
- **Save to phone** opens B8's sheet for this layout.
- Edit mode's own parts (page tray, remove buttons, Done) are covered elsewhere and are not redrawn here.

**States**
- **Saved layout, no changes:** Save is disabled.
- **Edited:** the name shows "Edited". Save updates this layout; Save as new asks for a name.
- **Done with unsaved changes:** offers "Update Trail", "Save as new" or "Discard". Whether Done should just save is an open question.
- **New, unsaved arrangement:** named "Unsaved layout", with Save as the main action.
- **Reorder:** drag a thumbnail. With the D-pad, select a thumbnail, then Move before and Move after, each announcing the new position ("Trail, 2 of 4").
- **Trigger already taken:** picking a trigger used by another layout asks "Move it from Commute?", with Move and Cancel. Two layouts never share a trigger.
- **Delete:** removes the layout with Undo for 10 s. The last layout cannot be deleted.
- **Rename:** uses the system keyboard. Names must be unique per car and screen; a duplicate shows an inline message.
- **Car starts moving while edit mode is open:** edit mode closes and nothing is lost. Unsaved changes stay as "Edited" for the next time you park (open question).
- **Offline:** edits are kept on this screen and marked "Not synced yet". Save to phone notes "Will load your layout when connected".
- **Sync error:** "Couldn't sync. Your changes are kept on this screen." with Retry.

**Sizes**
- Head units, tablet and desktop: the layout bar fits within strip height plus one row; menus anchor under it on the driver's side.
- 5in: thumbnails may scroll sideways in the bar.
- Phone and Android split third: the bar holds the name and Done, and the rest moves into a bottom sheet.

**Draw**
- 7in 1024x600, parked: edit mode with the layout bar, showing Edited, Save and Save as new.
- 7in 1024x600, parked: reordering thumbnails by drag.
- 7in 1024x600, parked: Automatic switching sheet with the "Move it from Commute?" prompt.
- 7in 1024x600, parked: Done with unsaved changes (Update, Save as new, Discard).
- 7in 1024x600, RHD, parked: the layout bar mirrored.
- 5in 800x480, parked: the layout bar at 480 px high.
- Phone 393x852, parked: the bar and its bottom sheet.
- 7in 1024x600, parked: reorder by D-pad, with the announcement shown as a caption.
- 7in 1024x600, parked: deleted, with an Undo toast.

**Rules**
- Parked only. None of these controls appear while moving.
- Every action has a non-drag path for the wheel, keyboard and switch access.
- The shell edits the layout. The gateway stores and syncs it, and the gateway's Layouts settings show the same data.
- There is no fixed or locked tile in any layout, but a warning always has a place (takeover or band).

**Interactions**
- Tap, drag, and the D-pad cursor with OK and Back. Back closes a menu or sheet. Back at the top level is the same as Done.

**Reference**
- Kit: menu, sheet, toast. Replaces frames B-20 to B-24 (Manage layouts). Save to phone: B8.

### F6. Empty and single-layout states

**Purpose**
- Keep the strip calm and honest when there is nothing to page between.

**Holds**
- The strip without dots, and an invitation to save.

**States**
- **No saved layouts** (only the open app, as D7): no dots. The name slot is empty, or shows the app's name in the name flash on open. Pressing and holding offers edit mode, where Save is the main action.
- **One saved layout:** no dots. The name flash still shows on app open. A swipe, or the D-pad off the edge, gives the end feedback (resistance, or "Trail · only layout") and nothing else.
- **Two or more:** dots as F1.
- **Moving:** the same; nothing invites saving while moving.

**Sizes**
- As F1.

**Draw**
- 7in 1024x600, parked: no saved layouts, with the hold hint.
- 7in 1024x600, moving: one layout, with the D-pad off the edge and the "only layout" flash.
- Phone 393x852, parked: one layout, no dots.

**Rules**
- No dots for fewer than two layouts.
- The hint to save appears at most once per session, and never while moving.

**Interactions**
- As F1 to F3.

**Reference**
- Kit: strip, tile. Frame D7 (the empty layout).

### F7. Optional soft-key row

**Purpose**
- Give pages with soft keys a fixed row where it helps (head units), and give the space back to tiles where it does not (phones, desktops), without losing any action.

**Holds**
- **On:** the row from C7. It has five fixed slots, with the owner tag (the page icon and name in the focus-ring colour) at the driver's end.
- **Off:** no row. The focused page's keys appear in its tile label menu as a "Soft keys" group, in slot order, above Swap page. They are also reached with the D-pad: OK on the tile label opens that menu, and any wheel buttons mapped to soft keys 1 to 5 still fire them.

**States**
- **On, 5in:** the row overlays the bottom 48 px of the focused tile for 4 s after a wheel key or tap. The tile keeps its size class.
- **On, 7in and larger:** the row counts against the tile area. It stays with the owner tag and empty slots even when a page has none, so tiles never jump.
- **Off, any screen:** tiles take the full height. The label menu carries the keys.
- **Off, key refused while moving:** the menu row shows the reason ("Not while moving") and does nothing, as the row would.
- **Off, page has no soft keys:** the label menu has no Soft keys group.
- **Setting changed:** tiles reflow once and may change size class. This happens only when parked.

**Sizes**
- Default on for head units (5in, 7in, 10in). Default off for phones, tablets and desktops, and for Android split screen (open question for tablets and split).

**Draw**
- 7in 1024x600, moving: row on, Diagnose focused, one key refused.
- 7in 1024x600, parked: row off, with the tile label menu open showing the Soft keys group.
- 5in 800x480, moving: row on, as an overlay.
- 5in 800x480, moving: row off, with the label menu reached by D-pad and OK.
- Phone 393x852, parked: row off (default), with the label menu.
- Desktop, parked: row off.
- 7in 1024x600, RHD: row on, with the owner tag at the right end.

**Rules**
- The setting lives in the gateway's shared settings ("Soft-key row: On / Off", which each screen can override). The shell draws no setting of its own, and the gear opens the gateway's.
- The setting can be browsed but not changed while moving ("Park to change").
- Slot order is the same in the row and in the menu. The same action always stays in the same slot.
- Turning the row off never removes an action.

**Interactions**
- On: as C7. Off: the label menu by tap, or by D-pad and OK, and mapped wheel buttons fire soft keys 1 to 5 directly.

**Reference**
- Kit: softkeys, menu (label menu). Updates C7.

### Frame list

1. F-01: Slim strip, resting and name flash; 7in 1024x600; LHD; Night and Day; Parked
2. F-02: Slim strip with lock and 24 px name flash; 7in 1024x600; LHD; Night; Moving
3. F-03: Slim strip, mirrored; 7in 1024x600; RHD; Night; Parked
4. F-04: Slim strip height check at 48 px, with a full tile reaching Expanded; 5in 800x480; LHD; Night; Parked
5. F-05: Slim strip, narrow form; phone 393x852; LHD; Night; Parked
6. F-06: Slim strip, narrow form; Android split third; LHD; Night; Moving
7. F-07: Carousel mid-swipe, Workshop to Trail; 7in 1024x600; LHD; Night; Parked
8. F-08: Carousel pulled past the last layout; 7in 1024x600; LHD; Night; Parked
9. F-09: Carousel mid-swipe, mirrored strip; 7in 1024x600; RHD; Night; Parked
10. F-10: Edge swipe in portrait; phone 393x852; LHD; Day; Parked
11. F-11: Swipe on a map tile pans the map and does not page; 10in 1280x720; LHD; Night; Parked
12. F-12: D-pad nearest-tile moves and up into the strip, Quad layout; 7in 1024x600; LHD; Night; Parked
13. F-13: D-pad spatial rule on an uneven 2+1 layout; 7in 1024x600; LHD; Night; Parked
14. F-14: D-pad paging off the right edge, before and after (two frames); 7in 1024x600; LHD; Night; Moving
15. F-15: D-pad at the last layout, end feedback; 7in 1024x600; LHD; Night; Moving
16. F-16: D-pad ring in the strip; 7in 1024x600; RHD; Night; Parked
17. F-17: Page change with a warning band kept in place; 5in 800x480; LHD; Night; Moving
18. F-18: Low range trigger, name flash with reason and text-only toast; 7in 1024x600; LHD; Night; Moving
19. F-19: "When parked" trigger to Workshop; 7in 1024x600; LHD; Day; Parked
20. F-20: Trigger waiting behind a warning takeover; 5in 800x480; LHD; Night; Moving
21. F-21: "Car starts" trigger with toast; phone 393x852; LHD; Night; Parked
22. F-22: Edit mode layout bar, Edited, Save and Save as new; 7in 1024x600; LHD; Night; Parked
23. F-23: Reordering layouts by dragging thumbnails; 7in 1024x600; LHD; Night; Parked
24. F-24: Automatic switching sheet with "Move it from Commute?"; 7in 1024x600; LHD; Night; Parked
25. F-25: Done with unsaved changes; 7in 1024x600; LHD; Night; Parked
26. F-26: Layout bar, mirrored; 7in 1024x600; RHD; Night; Parked
27. F-27: Layout bar at 480 px high; 5in 800x480; LHD; Night; Parked
28. F-28: Layout bar and bottom sheet; phone 393x852; LHD; Night; Parked
29. F-29: Reorder by D-pad, with the announcement caption; 7in 1024x600; LHD; Night; Parked
30. F-30: Layout deleted, with Undo toast; 7in 1024x600; LHD; Night; Parked
31. F-31: No saved layouts, with the hold hint; 7in 1024x600; LHD; Night; Parked
32. F-32: One layout, D-pad off the edge, "only layout" flash; 7in 1024x600; LHD; Night; Moving
33. F-33: One layout, no dots; phone 393x852; LHD; Night; Parked
34. F-34: Soft-key row on, Diagnose focused, one key refused; 7in 1024x600; LHD; Night; Moving
35. F-35: Soft-key row off, label menu with the Soft keys group; 7in 1024x600; LHD; Night; Parked
36. F-36: Soft-key row on, as an overlay; 5in 800x480; LHD; Night; Moving
37. F-37: Soft-key row off, label menu reached by D-pad; 5in 800x480; LHD; Night; Moving
38. F-38: Soft-key row off (default), label menu; phone 393x852; LHD; Day; Parked
39. F-39: Soft-key row off; desktop; LHD; Day; Parked
40. F-40: Soft-key row on, owner tag at the right end; 7in 1024x600; RHD; Night; Parked

### Open questions

1. How long should the name flash stay before the dots return (we suggest about 2 s), and should it be longer after a triggered switch?
2. With many layouts, should the dots compress at the ends, or switch to a "2 / 5" counter, and at what count?
3. Should tapping a single dot jump straight to that layout (parked), or should the dots only show position?
4. In RHD, should "next layout" still sit to the right (reading order), or mirror with the rest of the screen?
5. Should the D-pad page to another layout only from the tile frame, or also when focus is inside a tile and reaches its outer edge?
6. When several tiles are equally near in the direction pressed, which should win: the one most overlapping on the cross axis, the driver-side one, or the last one focused?
7. The single "next layout" key: should it stop at the last layout like the carousel, or loop back to the first because it has no direction?
8. While moving, should a swipe attempt show a hint ("Use the wheel while moving"), or do nothing?
9. Should a layout change while moving slide briefly or cut, given that effects are off?
10. Should Done in edit mode save changes to the current layout without asking (with Undo), or always offer Update, Save as new and Discard?
11. If the car starts moving with unsaved edits, should they be kept as "Edited" for later, or saved automatically?
12. Screen-edge swipes can clash with Android's back gesture on phones and some head units. Should the carousel swipe start only from the strip on those devices?
13. Should the soft-key row default to off on tablets and in Android split screen, or follow the screen size?

## G. Native Android extras (Gateway app only)

This section covers what the shell can add when it runs inside the **Gateway Android app** rather than in a browser: other apps' home-screen widgets as tiles, and Open beside for a native Android app. Everything else in this brief (tiles, strip, edit mode, warnings, moving rules) works the same way in both places. None of this reaches the browser version. Draw it as an extra layer on the existing kit, not as a second shell.

Terms used here:
- **Gateway Android app:** the one native Ostler app. It owns hardware, connections, car profiles, permissions and shared settings. It is also a gateway (see section B).
- **PWA:** an Ostler app installed from Chrome (a progressive web app). Most people use Ostler this way.
- **Full-screen shell:** an option inside the Gateway Android app that shows the MFD (the screen of tiles) across the whole app window, with the same layouts, pages, strip and rules as the PWA. It is an app screen. It is **not** the Android home screen, and Ostler never asks to become the home app.
- **Native:** built for Android itself, not a web page.
- **Android widget:** a small live panel that another Android app offers for the home screen, for example a music player's controls or a calendar's agenda.
- **Widget tile:** a tile that shows an Android widget instead of an Ostler page.
- **Ostler widget:** an Ostler page at Chip or Compact with "Show frame" off. This is not the same as an Android widget. Both can sit frameless.
- **Page tray:** the picker at the bottom of edit mode, which works like a phone's widget picker (search, and live previews at the size class each page would land in).
- **Edit mode:** the parked-only mode for changing a layout. You enter it by pressing and holding a tile or empty space (about 0.5 s, with a haptic) or from the wheel, and leave it with Done.
- **Consent dialog:** Android's own permission window. Ostler cannot change its words or look.
- **Open beside:** the label-menu action that opens a related item next to the current tile. Here it opens a native Android app.
- **Split screen:** Android's own side-by-side mode. Android draws the bar between the two apps and decides how they share the screen.
- **Freeform window:** a floating, resizable app window. Only some head units support it.
- **D-pad cursor:** the steering-wheel arrows move a focus ring to the nearest tile in that direction. Up from the top row reaches the strip. Moving off the left or right screen edge pages to the next saved layout, with no wrap-round.
- **Moving / Parked:** as reported by the gateway. "Unknown" counts as moving.
- **Toast:** the kit's short text-only message at the top, shown for 4 s.

### G1. The full-screen shell in the Gateway app

**Purpose**
- Let a head-unit owner run the MFD inside the Gateway app, which is the only way to get Android widgets as tiles and Open beside for native apps.

**Holds**
- **How it is offered:**
  - a switch in the Gateway app's settings for this screen: "Show Ostler full screen in this app" (off by default);
  - an "Open full screen" entry on the Gateway app's own home.
  - The offer explains in one line what it adds: "Adds Android widgets and opening Android apps beside Ostler."
- **What is the same as the PWA:** the strip, layouts (synced), the layout carousel, pages, edit mode, warnings, soft keys and moving rules. A user moving between the two should not notice a difference except the extras.
- **What differs:**
  - the page tray has an "Android widgets" group (G2);
  - Open beside can pick an installed Android app (G5);
  - haptics come from Android, so they are stronger and more reliable than in the browser.
  - There is no extra chrome, badge or "native mode" marker on the strip.
- **How to go back:**
  - "Leave full screen" in the shell's settings menu (the gear) returns to the Gateway app's own home;
  - Android Back on the top level does the same;
  - Android's Home button goes to the real Android home screen, as with any app.

**States**
- Off (default): the Gateway app shows its own screens. The MFD is reached through the PWA.
- On, first open: a one-time short sheet that names the two extras, with "Got it".
- On, normal: the MFD, identical to the PWA plus extras.
- Gateway app busy as a gateway with no screen in front: no change. The full-screen shell is only a view.

**Sizes**
- The same screens as the PWA, but Android only: phone 393x852, 5in 800x480, 7in 1024x600, 10in 1280x720, Android tablet, and Android split half and third. There is no desktop.

**Draw**
- The settings switch and the home entry, 7in, Parked.
- The one-time sheet, 7in and phone.
- The full-screen shell next to the same layout in the PWA, to show they match, 7in.

**Rules**
- Never ask to be the default home app, and never show "Set as home".
- Leaving full screen never changes the layout or closes widgets. They are back as they were the next time.
- Turning the option on or off is parked only ("Park to change"), like all settings.

**Interactions**
- Tap the switch or the entry. The gear's menu gains "Leave full screen".
- D-pad: as everywhere. "Leave full screen" is reachable from the strip's gear.

**Reference**
- Existing kit: strip, sheet, menu. There are no renders yet.

### G2. Android widgets in the page tray

**Purpose**
- Let the owner add another app's widget to a layout the same way they add an Ostler page.

**Holds**
- A group headed "Android widgets" in the page tray, after the Ostler pages. It is grouped by app, with the app icon and name, then each widget's name and Android's preview picture.
- Each preview is labelled with the class it would land in (Chip, Compact or Standard).
- The tray's search also finds widgets by app and widget name.
- Before consent is given (G3), the group header carries one quiet line: "Android will ask before Ostler can show widgets."

**States**
- Normal: the group lists every app that offers widgets.
- No apps with widgets: the group says "No Android widgets on this device."
- Consent refused earlier: the line reads "Not allowed. Try again", with a text button.
- Search with only widget results.

**Sizes**
- The tray is the same as in edit mode. The widget previews are Android's own still pictures, not live content.

**Draw**
- Tray open with the Android widgets group, 7in 1024x600, Parked, LHD and RHD.
- The same, searching "music", phone 393x852.
- An empty group, 5in.

**Rules**
- Previews are Android's pictures, not captures of the live widget.
- A widget that cannot fit any tile on this screen is still listed, marked "Too big for this screen", and cannot be dragged.
- The group exists only in the full-screen shell (see G6 for the PWA).

**Interactions**
- Drag a widget onto a tile or edge (it splits along the longer side, as for pages), or tap it to "Add beside" the selected tile.
- Non-drag path: with the D-pad cursor on a tile, choose Add beside, then pick from the tray.

**Reference**
- Existing kit: the page tray from the edit-mode addendum, sheet.

### G3. Consent to show widgets

**Purpose**
- Get Android's permission to host widgets, once, and make the system dialog unsurprising.

**Holds**
- **Before:** an Ostler sheet appears the first time a widget is dropped:
  - title: "Show Android widgets in Ostler";
  - two or three short lines: Android will ask for permission; the widget is drawn by its own app; Ostler never records what it shows;
  - buttons: "Continue" and "Not now".
- **The system dialog:** Android's own, for example "Allow Ostler to create widgets and access their data?", with an "always allow" option. Draw it greyed or as a placeholder, because it is not ours.
- **The widget's own set-up:** some widgets then open their app's own set-up screen (for example, choose a playlist). This also is not ours.
- **After:**
  - Allowed: return to edit mode, with the widget in its tile and the usual snap haptic. A toast: "Widget added".
  - Refused, or the set-up was cancelled: return to edit mode, with the tile not added and the layout unchanged. A toast: "Widget not added". The tray line changes to "Not allowed. Try again".

**States**
- First use, before the sheet.
- Sheet showing.
- System dialog (placeholder).
- Allowed, with the widget placed.
- Refused, with the tray line.
- "Always allow" already given: no sheet and no dialog. The widget lands at once.

**Sizes**
- The sheet follows the kit's sheet rules: from the bottom on a phone, centred or at the side on wider screens.

**Draw**
- The sequence (sheet, then system dialog placeholder, then the result), 7in, Parked.
- The refused result with the tray line, 7in.
- The sheet on a phone 393x852 and on 5in 800x480.

**Rules**
- Never show the sheet or the dialog unless the user has just chosen a widget.
- Never repeat the request on its own. Only "Try again" asks again.
- Words are plain, with no legal tone and no mention of permissions names.
- Edit mode is parked only, so this whole flow is parked only.

**Interactions**
- Continue, Not now, Try again. The D-pad reaches every button. Cancel or "Not now" has focus first.

**Reference**
- Existing kit: sheet, toast.

### G4. A widget in a tile

**Purpose**
- Show an Android widget as a tile that obeys the shell's sizing, moving and privacy rules, even though its content is drawn by another app.

**Holds**
- **Label row:** the widget's name, a chevron, and a small Android mark with the app name in the label menu, like the third-party mark (D6).
- **Label menu:** Swap page · Widget settings (only if the widget offers its own) · Open app beside (G5) · About this widget · Close.
- **About this widget:** the app, the widget's name, and "Ostler doesn't record what this widget shows."
- **Show frame:** a tile setting, as for Ostler pages. It can be off at Chip and Compact, so the widget looks as it does on a home screen.

**States**
- Normal, Parked: the live widget.
- Focused: the focus ring on the tile.
- **Moving (proposed rule, see Rules):** covered.
- **Cannot fit:** the window got too small (Android split third, or rotation to a phone). Shows as a chip with the app icon, the widget name and "Too small here".
- **Cannot render:** shows as a chip with the reason:
  - "Not installed" (the app was removed);
  - "Widget removed" (the app dropped it);
  - "Didn't load" (with Retry in the chip menu);
  - "Not allowed" (consent withdrawn in Android settings).
- **Stale or frozen:** if the widget's app stops updating it, Ostler cannot tell. Show nothing extra.

**Sizes**
- **Chip, Compact and Standard only.** A widget never goes to Badge or Expanded.
- Each widget brings its own smallest and largest size from Android. In edit mode, edges stop there, as they do at a page's declared size range.
- The shell still shows the class label while resizing.

**Draw**
- A widget at Chip, Compact and Standard, each with the frame on and off where allowed, 7in, Parked, Night and Day.
- The moving cover on the same layout, 7in, Moving, LHD and RHD.
- "Too small here" chip, 7in Android split third (about 340x600).
- Each cannot-render chip, 7in.
- The label menu and About this widget, 7in.

**Rules**
- **Moving (proposed):** Android widgets declare nothing about driving, and Ostler cannot enforce the 24 px text floor or target sizes inside them. So while moving (or Unknown):
  - every widget tile is covered by a plain cover with the app icon, the widget name and "Shows when parked", at 24 px or more;
  - the tile keeps its size, so the layout never jumps;
  - the cover draws the tile frame even when Show frame is off, so the space never looks broken;
  - touches on the cover do nothing.
  - The cover lifts as soon as the car is parked. A reviewed exception list (for example media controls) is an open question.
- **Privacy:** Ostler never records, captures, logs, syncs or analyses widget content. Layout previews, carousel thumbnails, Save to phone icons and edit-mode previews show the app icon and widget name, never a picture of the widget.
- Only these are synced in the layout: which app, which widget, its tile and its size.
- Widgets cannot be linked, and they have no shared cursor and no soft keys. With the soft-key row on, the row shows the owner tag and empty slots.
- A widget tile never takes a warning. The takeover order skips it, as it does instrument pages. A widget that is the only candidate gives way to the band.
- Error states are chips, never an error across the tile (as A.9).

**Interactions**
- Parked: touch the widget as on a home screen. Long press enters edit mode, not the widget's own long press.
- D-pad: the cursor stops on the tile like any tile. OK opens the label menu, because widgets cannot be steered by the wheel (proposed).
- Tap a chip: Retry, or open the app.

**Reference**
- Existing kit: tile, menu, sheet. D5 and D6 in this brief.

### G5. Open beside for a native Android app

**Purpose**
- Put a native app (for example a navigation app) next to Ostler without pretending Ostler can tile it.

**Holds**
- **Picking:** in the label menu, Open beside gains an "Android apps" group listing installed apps (recent first, with search). A widget tile's "Open app beside" skips the picker.
- **Split screen (the usual result):** Android splits the screen between Ostler and the app.
  - Android draws the bar between the two apps and decides the split.
  - Ostler simply gets a smaller window, and the window rules (A.7, A.8) apply.
- **Freeform (only on head units recorded as supporting it):** the app opens as a floating window over the chosen tile's rectangle. After that, Android owns it.
- **Failure (best effort):** if Android cannot split, the app opens full screen and a toast says "Opened full screen. Split screen isn't available here."
- **Going back:** Android's own controls (drag its bar to the edge, Recents, Back). Ostler cannot close or move the other app.

**States**
- Picker open.
- Split succeeded, with Ostler in the smaller part.
- Freeform window over a tile.
- Fell back to full screen, with the toast.
- Moving: the Android apps group is shown but refused, "Not while moving" (proposed: parked only, because it reshapes the whole screen).

**Sizes**
- After a split, Ostler's window is often a half or a third. Draw what the layout becomes.

**Draw**
- The picker with the Android apps group, 7in, Parked.
- After a split: Ostler as a half and a navigation app beside it, 10in 1280x720, LHD and RHD.
- Freeform over a tile, 10in (low fidelity for the other app).
- The fallback toast over the native app full screen, 7in.
- The refused item while moving, 7in, Moving.

**Rules**
- Call it best effort in the words. Never promise a side or a size.
- On RHD, Android may put the app on the driver side. Ostler does not fight it (open question).
- Ostler's moving rules do not reach the other app. Do not draw Ostler marks over it.
- Warnings still show inside Ostler's window (takeover or band). Over the other app, Ostler Controls handles them (C10).

**Interactions**
- Tap an app in the picker. The D-pad reaches the picker. The fallback toast needs no action.

**Reference**
- A.6 and A.9 in this brief. Existing kit: menu, sheet, toast.

### G6. What the PWA in Chrome shows instead

**Purpose**
- Keep the PWA honest and calm: no Android extras, and one quiet pointer to where they live.

**Holds**
- The page tray has no "Android widgets" group, and the Open beside picker has no "Android apps" group.
- **One quiet note** at the very end of the page tray: "Android widgets and Android apps beside Ostler are in the Gateway app." It has a text link: "Open the Gateway app" if it is installed, else "Get the Gateway app", and a small "Don't show again".
- **A synced layout with a widget tile:** the tile shows as a chip, "Android widget · Only in the Gateway app". Tapping it opens the Gateway app if it is installed.

**States**
- Android browser: the note shows.
- Not Android (iOS, desktop): no note at all, and widget tiles show the chip without a link.
- Note dismissed: gone for this screen.
- Moving: edit mode cannot open, so the note can never show.

**Sizes**
- One line plus the link, in the tray's own type. It wraps to two lines on a phone.

**Draw**
- Tray end with the note, 7in, Parked.
- The same, phone 393x852.
- A synced layout with the widget chip, 7in PWA, Parked and Moving.

**Rules**
- Never a banner, toast, pop-up, badge or a count, and never repeated in other places.
- Never while moving.
- The chip for a widget tile is the error state (A.9), not an advert.

**Interactions**
- Tap the link, or Don't show again. The D-pad reaches both.

**Reference**
- Existing kit: tile chip state, page tray.

### Frame list

1. G-01: Gateway app settings switch and home entry, "Show Ostler full screen" · 7in 1024x600 · LHD · Night · Parked
2. G-02: One-time sheet on first full-screen open · 7in 1024x600 and phone 393x852 · LHD · Night · Parked
3. G-03: The full-screen shell next to the same layout in the PWA · 7in 1024x600 · LHD · Night, Day · Parked
4. G-04: The gear menu with "Leave full screen" · 5in 800x480 · LHD, RHD · Night · Parked
5. G-05: Page tray with the Android widgets group · 7in 1024x600 · LHD, RHD · Night · Parked
6. G-06: Page tray search showing widgets, and an empty group · phone 393x852 and 5in 800x480 · LHD · Night · Parked
7. G-07: Consent sequence (Ostler sheet, then system dialog placeholder, then widget placed) · 7in 1024x600 · LHD · Night · Parked
8. G-08: Consent refused (toast, then tray line "Not allowed. Try again") · 7in 1024x600 · LHD · Night · Parked
9. G-09: Consent sheet at small sizes · phone 393x852 and 5in 800x480 · LHD · Night, Day · Parked
10. G-10: A widget at Chip, Compact and Standard, with the frame on and off where allowed · 7in 1024x600 · LHD · Night, Day · Parked
11. G-11: Widget tiles covered while moving ("Shows when parked") · 7in 1024x600 · LHD, RHD · Night · Moving
12. G-12: Widget too small here, shown as a chip · 7in Android split third (~340x600) · LHD · Night · Parked
13. G-13: Cannot-render chips (Not installed, Widget removed, Didn't load, Not allowed) · 7in 1024x600 · LHD · Night, Day · Parked
14. G-14: Widget label menu and About this widget · 7in 1024x600 · LHD · Night · Parked
15. G-15: Warning takeover skipping a widget tile, or the band · 7in 1024x600 · LHD · Night · Moving
16. G-16: Open beside picker with the Android apps group · 7in 1024x600 · LHD · Night · Parked
17. G-17: Native app opened beside through Android split screen · 10in 1280x720 · LHD, RHD · Night · Parked
18. G-18: Native app as a freeform window over a tile (low fidelity) · 10in 1280x720 · LHD · Night · Parked
19. G-19: Fallback to full screen with the toast · 7in 1024x600 · LHD · Night, Day · Parked
20. G-20: Android apps refused while moving ("Not while moving") · 7in 1024x600 · LHD · Night · Moving
21. G-21: PWA tray end with the quiet note · 7in 1024x600 and phone 393x852 · LHD · Night · Parked
22. G-22: PWA with a synced widget tile shown as a chip · 7in 1024x600 · LHD · Night · Parked, Moving

### Open questions

1. **Widgets while moving.** This draft covers every widget while moving. Should a short, reviewed list (for example media play and skip controls) stay live while moving? If so, who reviews it, and does the cover rule still apply to small text?
2. **The D-pad on a widget tile.** OK opens the label menu in this draft. Should it open the widget's app beside instead?
3. **Native Open beside while moving.** This draft makes it parked only, because it reshapes the whole screen. Should it be one tap while moving, like Ostler's own Open beside when it replaces a tile?
4. **Which side the native app lands on.** Android chooses. On RHD it may land on the driver side. Accept it, or fall back to full screen when the side is wrong?
5. **Widgets on another screen.** Layouts sync, but widget permission and set-up are per device. On a second head unit with the Gateway app, should a widget tile show as a chip with "Add on this screen", or re-ask at once when parked?
6. **Android's bars in full screen.** Keep Android's status and navigation bars, which show the time and give a way out, or hide them and reveal them with a swipe from the edge?
7. **How the full-screen option is offered.** Is a settings switch plus a home entry enough, or should the Gateway app offer it once the first time it runs on a head unit?
8. **The Android mark on widget labels.** Is a mark like the third-party mark (D6) right, or is the app name in the label menu enough?

## Deliverables

- **95 frames:** E-01 to E-33, F-01 to F-40, G-01 to G-22, one design file per section
  (`shell-E-edit-mode`, `shell-F-layouts-dpad`, `shell-G-native`) plus a PNG per frame named by
  its id.
- **Components** added to the kit: edit-mode tile (edges, remove button, selection ring), page
  tray and its previews, snap preview label, Done and Undo, layout dots and name flash, the
  D-pad cursor at a screen edge, the soft-key row on and off, the Android widget tile and its
  consent states.
- **Answers or proposals** for the open questions, marked with the section and number.

## Changelog

- 1.0 (2026-10-12): first version, written per section by three sub-agents from ADR-0052 v0.7,
  the shell spec §19 and the touch tiling research.
