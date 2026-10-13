---
title: "How Ostler is meant to work — the designer's full picture of the system for the builder (13 October 2026)"
area: references
status: stable
version: 1.0
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/IMPLEMENTATION.md, references/design/2026-10/shell-session/README.md]
summary: >
  The designer's explanation of the whole system, saved as delivered with frontmatter added: the Gateway, apps as PWAs and the shell library; the Android home-screen model with tiling; pages on screens of every size with Wide and Single-page versions; edit mode; stacks and full screen; two-level wheel focus; alerts and how attention is routed; why each choice was made.
---

# How Ostler is meant to work: the full picture

This is written for the builder: what the system is, why it behaves as it does, and how the pieces fit. `README.md` lists the decisions, `IMPLEMENTATION.md` explains how to build them, and the tokens and specs give exact values.

## 1. What Ostler is
Ostler is a **modular car-data system**, not an operating system or a launcher.

- **The Gateway** is the only part that talks to the car and its hardware, and it stores everything: logs, car profiles, settings and alerts. It runs on an Ostler Brain, on the Gateway Android app, on a node, or briefly inside the browser. The Gateway Android app is also the only native app; it exists to handle Android permissions, widgets, notifications and keys.
- **Apps** (Diagnose, Logs, Maps, Security, Convoy and others) are PWAs. They are viewers and controls on top of the Gateway, and they only ever talk to the Gateway. If an app is closed, nothing is lost.
- **The shell** is a small library that every app bundles. It does exactly one job: lay out pages from any installed app as tiles on screen, like an aviation display where any screen can show anything. It also routes attention when something goes wrong.

## 2. The mental model: Android's home screen, with tiling
We copied the Android home screen on purpose, because everyone already knows it, and then added tiling.

- **Pages:** the screen shows **pages** of tiles. You swipe between pages like home-screen pages. Page dots appear at the bottom only while you're paging or editing.
- **Tiles:** each tile shows one **page** from an app, for example Diagnose's fault list or the Speed instrument. A tile works out its size class (Badge, Chip, Compact, Standard or Expanded) from its own size in dp, and the app draws the design for that class. Content is added or removed between classes, never squeezed.
- **No top bar:** there's no permanent strip. The screen is all content, and things appear only when they need you.

## 3. Screens of every size
- **What a page is:** a column at least 720 dp wide.
- **Small windows** (5″, 7″, phone, Android split screen) show one page at a time.
- **Extra-large windows** (12–15″ head units) show two pages side by side, like an unfolded phone.
  - A **pinned driver column** (Speed, say) stays put while the pages turn.
  - A tile can **span** both pages, for example a big map.
- **When the window shrinks** (open Spotify beside Ostler, for example), the layout switches to its **single-page version**.
  - The driver-side instrument stays put; the rest spills onto the next page.
  - Close Spotify and the wide version comes back exactly.
  - The two versions are saved separately and never overwrite each other.
- **Physical size:** everything is in dp, so text and touch targets are the same physical size on any panel.

## 4. Changing the layout: edit mode
- **You can only edit while parked.**
- **Entering:** hold anywhere for half a second, as on Android.
  - The pages zoom out, each on a faint panel, with a selector around the one you're working on. The neighbouring pages peek in.
  - On a 15″ screen, both pages are editable at once.
- **Resizing:** tap a tile to get its **resize frame**, then drag any edge. Neighbouring tiles give way and edges snap.
- **Window style:** hold a selected tile to choose Normal, Transparent or None, which makes it a widget. What's inside belongs to the app, so its settings stay in the app.
- **Moving a tile:** pick it up and three destinations appear:
  1. **Up:** a row of shapes (2+1, Halves, Quad…). Drop into a slot to rearrange the page.
  2. **Onto another tile:**
     - hover and the tiles slide aside to swap;
     - hold on the centre to make a **stack**;
     - drop on an edge zone to split it.
     - On small screens there are no zones: the side of the tile your finger is on decides.
  3. **Down:** the **delete circle**.
- **Moving to another page:** drag a tile to the edge of the screen and the next page slides in; past the last page, a new one appears.
- **Adding pages:** use **Layout** to pick a shape, then tap the **+** in any empty slot. That shows pages that fit the slot, with suggestions first. The next empty slot asks straight away.
- **Leaving:** **Done** asks whether to save over the layout, save it as new, or discard. If the car starts moving, edit mode closes at once and your edits are kept.

## 5. Quick switching: stacks and full screen
- **Stacks:** a stack is one tile holding several pages, with **badges** along its edge.
  - One tap on a badge switches the page. This is safe while moving, like an aviation display's page buttons.
  - There's no limit on pages: badges come in pages of their own.
  - They sit next to the head unit's physical keys if it has them, and can be linked to those keys.
- **Full screen for a while:** double-tap any tile and the others shrink to badges; tap the last badge to restore the layout. Nothing is saved.

## 6. Steering wheel and keyboard
- **Two levels.** The arrows move between tiles; OK goes inside a page, and the arrows then move through that app's own controls. Back comes out.
- **No accidents at the edge:** the arrows never leave a page at its edge.
- **Long-press Select** opens the alerts list.

## 7. When something goes wrong: alerts
**The split:** the app writes the message and styles its own content (for example, it turns its coolant value amber). The shell only says which app is alerting and puts the message where you'll see it.

- **Cautions:**
  - **If the cause is on screen:** a ring goes round that tile with a small tag carrying the message. No pop-up.
  - **If it isn't on screen:** a card appears centred over the page with the message, **Diagnose** and **ACK**.
    - After 4 s it shrinks to a readable **tab** in the passenger-side top corner.
    - The tab stays until the problem clears, so you always know what's wrong without touching anything.
- **Warnings:**
  - **If the cause is on screen:** the warning appears on that tile itself.
  - **If it isn't on screen:** it takes over a non-instrument tile on the passenger side, with ACK.
  - Either way it is never modal and never covers an instrument's values.
- **Where the problem is:**
  - The page dot for the page holding the cause gets an amber or red border.
  - Inside a stack, the badge gets a thin border.
- **Sound:**
  - Cautions: a chime and one spoken line.
  - Warnings: a tone and one spoken line, with the tone repeating quietly until ACK.
  - ACK is Select on the wheel, so your hands stay put.
- **Diagnose** takes you straight to the app's page for that problem. Pull the tab down for the full list.
- **Android notifications:** the Gateway also posts these for the phone, watch and lock screen when Ostler isn't on screen. They're silent while Ostler is showing, and Ostler never depends on them.

## 8. Old cars and partial data
Not every module is awake all the time. On a Discovery 2 the Td5 engine computer can be live while the SLABS ABS module is asleep. So there's no global "connected" light: **each app says what's stale, row by row** ("ABS asleep · last 10:42"). The Gateway app holds the detailed connection status.

## 9. While driving
- **Blocked:** editing, hold-to-edit and saving.
- **Still allowed:** page changes by the wheel or by triggers (no swipe), stacks, full screen, focus, ACK and Diagnose.
- **Readability:**
  - text is at least 24 dp and touch targets at least 60 dp;
  - effects are off;
  - transparent instrument tiles turn solid;
  - toasts are text-only.
- **Unknown motion** counts as moving.

## 10. What the shell is not
- No settings screens of its own: the gear opens the Gateway's shared settings.
- No car logic and no connection fixing: that's the Gateway's job.
- No launcher, dock or app drawer: Ostler sits alongside other Android apps.
- It never draws inside an app's page.
