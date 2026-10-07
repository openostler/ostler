---
title: "Designer brief, October 2026 — start here"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [references/design/2026-10/README.md, references/design/2026-10/screens.json, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-shell-input-design.md]
summary: >
  The entry point of the designer brief for the October 2026 round. It says who the brief is
  for and what Ostler is (an Android-style OS plus apps and flavours), how to read a screen
  block (purpose, owner, entry and exit, layout classes,
  key frames, content, states, safety rules, components, spec links, open questions) and the
  Existing, New and Proposed tags. It condenses the hand-off README's hard-constraints
  checklist with citations, sets the draw-first order from decision 92 (Night on every size;
  Night dim and Moving for every driver-facing head-unit frame; Day on phone), gives the
  export file naming, and lists every file of the brief by area: foundation 00–03,
  onboarding, hardware, settings, drive, launcher, vehicle, apps, store and app frame.
---

# Designer brief, October 2026 — start here

## Who this is for

You are the UX designer drawing every Ostler page for this round. Ostler is an open,
local-first car platform built like an **Android-style operating system** (owner's
direction, 2026-10-07). The **OS** holds only the system services and the system UI: the
launcher (home pages, dock, app drawer), the status strip, the Connection sheet, system
Settings, the theme engine and first-run setup. **Everything else is an app** in its own
repo, installed from the **Store**: Diagnostics, Trips, Security, Maintenance, Social, Map,
Navigation, Phone, Radio, Audio, Media, Camera, Decode lab, Community and the starter
widget pack. A **flavour** is the OS plus a preinstalled set of apps (Ostler Diagnostics,
Ostler Guardian; see [01-sitemap-b](01-sitemap-b.md#3-flavours-preinstalled-sets)).
Safety stays with the OS, never with an app.

The OS runs on a small computer in the car (the **Brain**) and opens on the car's head
unit, a phone or tablet browser, a desktop browser and the **companion phone app**. A
**node** plugged into the car is the only path to the car's buses. The first car is a Land
Rover Discovery 2 Td5 (right-hand drive, K-line).

**UX first.** The designs come first; the UI is then built against fixtures, and wiring
comes last.

This brief turns the approved specs into page content. The specs decide; the brief tells you
what is on each page, in what order, in every state. When the brief and a spec differ, the
spec wins and the difference is a bug in the brief: tell the owner.

## How to read the brief

Every screen, sheet or frame has one block in this shape:

| Line | What it tells you |
|---|---|
| `### <screen-id> — <Name> [tag]` | The ID you use for folders and file names. Keep it exactly. |
| **Purpose** | One line: why the page exists. |
| **Owner** | `os`, or `app:<name>` (diagnostics, trips, security, maintenance, social, map, navigation, phone, radio, audio, media, camera, decode-lab, community, store, widgets-starter). |
| **Opens from → goes to** | Every way in and every way out. |
| **Layout classes** and **Draw first** | Which sizes exist, and the key frames to deliver in the first pass. |
| **Content (top to bottom)** | Numbered sections with every label, field, row and action, in order. |
| **States** | Empty, loading, error, offline, no vehicle, Parked, Idling, Moving, Passenger, locked. |
| **Safety and driving rules** | What Moving hides, locks or limits, and any confirmation. |
| **Components** | Names from the component list ([03-components-a](03-components-a.md)). |
| **Spec refs** and **Open questions** | Where the rule comes from, and what the owner still has to answer. |

Flows and wizards start with a step table (step, screen ID, what the user does, what can fail
and how to recover), then one block per step.

**Tags.**
- **Existing:** already in the index ([`screens.json`](../screens.json)). Keep its ID.
- **New:** an approved spec covers it, but it is not in the index yet. Draw it like any other.
- **Proposed:** no approved spec covers it yet. The block says why the app needs it. Draw it,
  but expect changes when the owner answers.

**Example data.** All examples come from the Discovery 2 Td5 pack: RPM, Boost, Coolant,
Battery, Fuel temp, the SLABS ride heights (Height left, Height right), and fault codes such
as P0243 "Turbocharger wastegate diagnostics (logged low)" on the engine and "Right front
wheel speed sensor — output too low" on SLABS. Never draw a made-up car, person or value
as if it were real ([ADR-0011][adr-11]).

## Hard constraints (check every frame)

Condensed from the hand-off [designer prompt checklist](../README.md#3-designer-prompt-checklist).

1. **Moving uses templates only.** On a head unit while Moving: `telltale_list`, `value`,
   `setpoint`, `camera_live`, `arm`, `map`, `media`, `tiles` (≤ 6), `alert_card` (one card,
   icon + ≤ 2 lines of ≤ 30 characters, ≤ 2 buttons), `short_list` (≤ 6 rows, one level,
   ≤ 30 characters) and `call` (≤ 3 buttons). Tasks are ≤ 3 screens and end in Drive mode.
   ([UI §12.1][ui-12.1], [Drive modes §4.3][dm-4.3])
2. **Minimum sizes.** Text ≥ 12 px on phone, tablet and desktop; ≥ 18 px on a Parked head
   unit; ≥ 24 px in a Moving template; Drive digits ≥ 56 px; strip chips ≥ 48 px tall;
   head-unit targets 76 px. Numbers never clip: drop one type step. ([visual §4][vds-4],
   [Drive modes §4.4][dm-4.4])
3. **Tokens only.** Colour, type, space, radius, elevation and motion come from tokens in
   Night, Night dim, Deep night and Day. No raw colours. ([visual §3.1][vds-3.1])
4. **One icon set.** Material Symbols, outlined. No emoji, dingbats or Unicode arrows. An icon
   that carries meaning has a word beside it. ([visual §6][vds-6])
5. **No glow on head units at night.** At most one glowing element per screen on phone,
   tablet and desktop. None on head units in Night dim or Deep night, in Drive mode or in a
   Moving template. No blur or gradients on head units. ([visual §5][vds-5])
6. **Motion** only for sheet open and close, tab change and the alarm pulse. None while
   Moving. ([visual §5][vds-5])
7. **One accent, calm gauges.** Cyan is for interactive and live things only. Status colours
   come with an icon and a word, and only out of range. ([visual §1][vds-1])
8. **Park to edit.** Edit mode, pickers and editors exist only Parked (or Idling with Park
   evidence) on a driver-facing display. While Moving a long-press shows "Park to edit" and
   nothing else. ([Drive modes §8.1][dm-8.1])
9. **Safety items move, never go.** The fault telltale, alarm alerts, safety widgets, the
   dock's App drawer button, and in Drive mode Back and the page chip are always there.
   Apps cannot remove, cover or restyle them. ([Drive modes §8.1][dm-8.1])
10. **No message text while Moving.** A message card shows sender and app, with Play and
    Reply. ([UI §12.1][ui-12.1])
11. **No video on driver-facing screens** while Idling or Moving; calls are audio only.
12. **No other people on the head-unit map while Moving**, except plain convoy markers.
13. **No text entry while Moving**, and no "always" option for Passenger view anywhere.
    ([UI §3.5][ui-3.5])
14. **Honest states.** Stale values grey with their age; missing is "—", never 0;
    `candidate` is marked. ([visual §8][vds-8], [UI §3.8][ui-3.8])
15. **Map-first.** Full-bleed map, sheets over it; on head units the sheet sits on the
    passenger side. ([visual §7][vds-7])
16. **D-pad reachable.** Every control has a focus state: a 3 px accent ring with a 2 px gap;
    confirm sheets open with Cancel focused. ([shell input §7][si-7], [§9][si-9])
17. **Driver side.** On head units the dock sits on the driver's side. Draw right-hand drive (the D2); add
    left-hand drive where the layout differs. ([UI §3.3][ui-3.3])
18. **Five dock slots,** the App drawer button always one of them; home pages in a
    carousel with page dots. ([Drive modes §7.3][dm-7.3])
19. **No score** in Trips. ([UI §12.2][ui-12.2])
20. **Our names only.** No other brand's marks, fonts or colours. Figtree is the face.
21. **The node is the only path to the car.** The Brain uses an adapter only when no node is
    fitted ([ADR-0044][adr-44]). Location stays on the device unless shared ([ADR-0009][adr-9]).
    The VIN never leaves the car ([ADR-0036][adr-36]).

## Draw first (decision 92)

The owner approved key frames first ([README decision 1, item 92](../README.md#decisions-for-the-owner)).
The first pass for every screen is:

- **Night** on every layout class the block lists;
- **Night dim + Moving** for every driver-facing head-unit frame (HU-5, HU-7, HU-9/10,
  HU-wide), that is every frame a driver sees while the car moves: dashboard pages, the strip,
  alerts, calls, turn cards, the locked view and Passenger view;
- **Day** on phone.

Deep night, the remaining Day frames and the full class × theme matrix come after the first
review. Draw in this order, so the shared parts are settled before the pages that use them:

| Wave | What | Where in the brief |
|---|---|---|
| 1 | Kit sheets, launcher components and the Moving templates | [03-components-c](03-components-c.md) |
| 2 | OS: launcher (home pages, dock, app drawer), strip, Connection sheet, locked view, Passenger view | [01-sitemap-a](01-sitemap-a.md), `40-drive-*`, `45-launcher-*`, [02-global-patterns-b](02-global-patterns-b.md) |
| 3 | OS-wide states (empty, loading, errors, offline, long jobs) | [02-global-patterns-a](02-global-patterns-a.md), [02-global-patterns-c](02-global-patterns-c.md) |
| 4 | First run, hardware set-up, system Settings, the Store, the app frame | `10-onboarding-*`, `20-hardware-*`, `30-settings-*`, `70-store-*`, `90-appframe-*` |
| 5 | Dashboard pages, alerts and calls | `40-drive-*` |
| 6 | Apps: Diagnostics, Trips, Security, Maintenance, Decode lab | `50-vehicle-*` |
| 7 | Other apps and the Community web | `60-apps-*`, `80-hu-*` |

## Naming exported files

From the [hand-off README §1](../README.md#1-how-designs-are-handed-over):

```
references/design/2026-10/<screen-id>/<layout-class>-<theme>[-<state>][-<variant>].png
references/design/2026-10/<screen-id>/<layout-class>-<theme>[-<state>][-<variant>].html
```

- `<layout-class>`: `phone`, `tablet`, `desktop`, `hu5`, `hu7`, `hu9`, `huwide`.
- `<theme>`: `night`, `day`, `night-dim`, `deep-night`.
- `<state>`: `parked` (the default, so usually left out), `idling`, `moving`, `passenger`.
- `<variant>`: a short kebab-case word from the block, for example `-empty` or `-error`.
- Example: `ia-error-node-offline/hu7-night-dim-moving.png` and `.html`, each ≤ 2 MB.

Name the design artifact the same way, so the reviewer can match link and file.

## The files of this brief

| Files | Area | Covers |
|---|---|---|
| [00-start-here](00-start-here.md) | foundation | this page |
| [01-sitemap-a](01-sitemap-a.md), [01-sitemap-b](01-sitemap-b.md), [01-sitemap-c](01-sitemap-c.md), [01-sitemap-d](01-sitemap-d.md) | foundation | surfaces and navigation model; the OS tree and flavours; the Apps tree; other surfaces and what each driving state hides |
| [02-global-patterns-a](02-global-patterns-a.md), [02-global-patterns-b](02-global-patterns-b.md), [02-global-patterns-c](02-global-patterns-c.md) | foundation | empty, loading, errors, offline, toasts, confirms, permissions, Moving lockout, Park to edit, Passenger view, long jobs, undo, empty vehicle, updates, accessibility |
| [03-components-a](03-components-a.md), [03-components-b](03-components-b.md), [03-components-c](03-components-c.md) | foundation | component inventory, sizes and tokens; launcher components; kit sheets; new components |
| `10-onboarding-*` | onboarding | first run, owner account, consent, pairing the node and Brain, choosing or detecting the vehicle |
| `20-hardware-*` | hardware | node, Brain, adapters, display buttons, wiring, calibration, firmware |
| `30-settings-*` | settings | system Settings: display, notifications, privacy, accounts and sharing, apps, integrations, maps, updates |
| `40-drive-*` | drive | the strip, dock, app drawer, Home, dashboard pages, page chip, Drive menu, editing, alerts, calls |
| `45-launcher-*` | launcher | home-page grid, widgets, widget picker and setup, dashboard builder and theme wizards |
| `50-vehicle-*` | vehicle | the Diagnostics, Trips, Maintenance and Decode lab apps |
| `60-apps-*` | apps | Social, Phone, Navigation, Map, Community |
| `70-store-*` | store | the Store app |
| `80-hu-*` | head-unit apps | Radio, Audio, Media, Camera, Clock, Weather, Voice, steering-wheel controls, projection, climate |
| `90-appframe-*` | app frame | App info, app setup and options flows |
| `85-security-*` | Security app | the Security app: the whole Ostler Guardian flavour (arm, events, tracker, geofences, widgets, Guardian home) |
| [99-index-a](99-index-a.md), [b](99-index-b.md), [c](99-index-c.md) | index | every screen in one generated list, grouped by owner, with its tag and brief link |
| `screens-<area>.json`, `screens-<area>-existing.json` | all | machine-readable New and Proposed screens, and brief links for Existing ones |

Files may be split into `-a`, `-b` and so on. The foundation files define the IDs that start
with `ia-`; each area file defines its own. The JSON entries carry an `"owner"` key with the
same value as the block's Owner line.

[adr-9]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[adr-11]: ../../../../decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md
[adr-36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[adr-44]: ../../../../decisions/adr-0044-adapters-on-the-brain-without-a-node.md
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[si-9]: ../../../../specs/2026-10-07-shell-input-design.md#9-focus-visuals
[ui-3.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#33-driver-side-rail-versus-bottom-bar
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-4]: ../../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
