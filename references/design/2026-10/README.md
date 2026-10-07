---
title: "Design hand-off, October 2026 — how designs come in, how they are reviewed, and every screen to design"
area: references
status: stable
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-phone-comms-addon-design.md, references/research/driver_distraction_rules.md, references/research/message_alerts_android_auto.md, references/research/visual_design_direction.md]
summary: >
  The hand-off folder for the owner's one combined designer prompt (DMD round, October 2026). It says how designs arrive (claude.ai design artifact links read by the manager, plus exported PNG and HTML saved here as `<screen-id>/<layout-class>-<theme>.png` and `.html`, with optional state and variant suffixes), what is recorded per screen (link, date, designer prompt version, status awaiting · received · reviewed · matches-spec · differs, and each difference), and how each screen is reviewed against its spec section before the V2 component kit and V3 page work. It holds a designer prompt checklist of the hard constraints (Moving templates and their limits, minimum sizes, tokens only, one icon set, no glow on head units at night or in Drive mode, Park to edit, non-removable safety items, no message text while Moving, no video on driver-facing screens) with citations, and the full screen index: 127 screens and sheets across the shell, Home, Drive modes and their faces, alerts and calls, Trips and sharing, Places, Diagnose and the help flow, Decode lab, Vehicles & Map, Social, Phone & Comms (linked to its spec), Navigation, Ostler Community (the closed, Ostler-run hub: web P1–P14 including Forum, Thread, Vehicle project, Decode card and Wiki page, and More → Community), adapters, Maintenance & Garage, Network, More, Preferences, accounts S1–S10 and the Add-ons catalogue, each with layout classes, themes, driving states, spec sections and tokens. The machine-readable copy is `screens.json` in this folder. Approved by the owner on 2026-10-07 ("approve all", DMD round; decision list items 92–96): key frames first, design files under the CLA annotated like the docs, PNG plus HTML per frame (≤ 2 MB each), the approved message card (sender and app with Play / Reply), and every spec of the round now approved, so no screen is provisional.
---

# Design hand-off, October 2026

**Status: approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3.** Every
spec this folder cites was approved the same day. This folder receives the designs the owner commissions with
one combined designer prompt covering every screen of this round: the editable UI, Drive
modes, D-pad and remote input, message alerts, the Phone & Comms add-on, trip sharing,
Navigation, Ostler Community, source adapters, and updates to the existing pages (Home,
Trips, Diagnose, Vehicles & Map, Social, Maintenance & Garage, Network, More, Decode lab and
the admin surfaces: service mode, Developer and About). Nothing here is a design decision:
the specs decide, and a design that differs from a spec is either a proposal to change the
spec or a design to fix (see **Review**).

Two files:

- **This README**: the process, the designer prompt checklist and the screen index table.
- **[`screens.json`](screens.json)**: the same index, machine-readable, and the **register**
  where each delivery and review is recorded. `screens.json` is the source of truth; the
  table below mirrors it and is updated in the same commit.

The **Phone & Comms** screens link the sections of the approved
[Phone & Comms spec](../../../specs/2026-10-07-phone-comms-addon-design.md) (dialer, contacts,
recents, favourites, incoming call, the message card for SMS/iMessage and the notification
bridge, More → Phone, widgets, pairing and the companion bridge setup). **Ostler Community**
screens follow the [community hub spec](../../../specs/2026-10-07-community-hub-design.md)
v0.2: a closed service run by Ostler (one instance), web screens P1–P14 and the in-shell More
→ Community with tabs Discover · Forum · Help · Mine, plus Wiki links.

## 1. How designs are handed over

1. **Artifact links.** The designer shares each screen, or a set, as a claude.ai design
   artifact link (and/or images). The owner passes the links on; the **manager** (whoever
   runs the review, person or agent) reads each link and never edits the designer's artifact.
2. **Exports saved here.** For every screen, the manager saves a **PNG and the exported
   HTML** for each layout class and theme delivered, under this folder:

   ```
   references/design/2026-10/<screen-id>/<layout-class>-<theme>[-<state>][-<variant>].png
   references/design/2026-10/<screen-id>/<layout-class>-<theme>[-<state>][-<variant>].html
   ```

   - `<screen-id>`: exactly as in the index (for example `drive-dashboard-cluster`).
   - `<layout-class>`: `phone`, `tablet`, `desktop`, `hu5`, `hu7`, `hu9` (HU-9/10) or
     `huwide` ([UI §3.1][ui-3.1], HU-5 from [UI §12.3][ui-12.3]).
   - `<theme>`: `night`, `day`, `night-dim` or `deep-night`
     ([visual §3.1][vds-3.1]).
   - `<state>` (only where the driving state changes the render): `parked`, `idling`,
     `moving` or `passenger`. Omitted means Parked.
   - `<variant>` (only for a listed variant): a short kebab-case word from the screen's
     `variants`, for example `hu7-night-moving-burst.png` for `alert-message`.
   - Example: `drive-dashboard-cluster/hu7-night-dim-moving.png` and `.html`.
   - Images that came without HTML are saved as PNG only and the record says so. Exports are
     saved as delivered (no re-drawing); a crop or resize is noted in the record.
3. **Record the delivery** in `screens.json`, in the screen's `deliveries` list (one entry per
   delivery):

   | Field | Content |
   |---|---|
   | `date` | the day it arrived (YYYY-MM-DD) |
   | `prompt_version` | the designer prompt version it answers, for example `DP-2026-10-07.1` (the owner bumps the number whenever the prompt changes) |
   | `links` | the artifact link(s), exactly as shared |
   | `files` | the paths saved under this folder |
   | `status` | `received` → `reviewed` → `matches-spec` or `differs` |
   | `reviewer` | who checked it |
   | `differences` | one entry per difference: `spec_ref`, `design`, `spec`, `proposal` (`update spec`, `update design` or `owner decides`) |

   The screen's `review.status` holds the latest state (`awaiting` until anything arrives).
4. **Licence line.** Before design files are committed, add their
   [REUSE](../../../REUSE.toml) annotation with the copyright holder the owner confirms
   (Decision 2). `screens.json` is already covered.

## 2. Review

Each screen is checked against **its spec sections** (the index's "Spec sections" column),
the **visual design system** ([visual spec][vds-1]) and the **designer prompt checklist**
(§3):

1. **Received.** Files saved, record written, nothing judged yet.
2. **Reviewed.** For each layout class, theme and state delivered: the content matches the
   spec's elements and order; the driving-state renders obey the template limits; tokens,
   type sizes, targets and icons are the visual spec's; nothing on the checklist is broken.
   A missing class, theme or state required by the index is a difference.
3. **Matches spec** when nothing differs. **Differs** otherwise: each difference is listed for
   the owner in `differences`, with a proposal: **update the spec** (the design is better and
   no rule is broken), **update the design** (it breaks a rule or a spec's content), or
   **owner decides**. A design never relaxes a safety rule by itself: anything touching UI
   §12.1, §14, Drive modes §8.1 or the visual spec's glow and type floors goes to the owner.
4. **Before the V2 component kit and V3 pages are built** ([visual §11][vds-11]), every
   screen in that slice is `matches-spec`, or its differences are resolved by a spec
   amendment (in a dated "Proposed amendment" section of the spec, approved by the owner) or a
   revised design. A
   spec changed this way names the design file it followed.
5. A design for a **proposed** (not yet approved) spec section is reviewed against the
   proposal and marked as such; it is re-checked once the owner answers.

## 3. Designer prompt checklist

Constraints the designer must honour on every screen. Paste this list into the prompt.

1. **Moving uses templates only.** On a head unit while Moving, only `telltale_list`,
   `value`, `setpoint`, `camera_live`, `arm`, `map`, `media`, `tiles`, `alert_card`,
   `short_list` and `call`, within their limits: ≤ 6 tiles; `short_list` ≤ 6 rows, one level,
   ≤ 30 characters a row; `alert_card` one card, icon + ≤ 2 lines of ≤ 30 characters, ≤ 2
   buttons; `call` ≤ 3 buttons; `map` own position, route, next manoeuvre, no free panning
   or search; task depth ≤ 3 screens ending back in Drive mode. ([UI §12.1][ui-12.1],
   [Drive modes §4.3][dm-4.3])
2. **Minimum sizes.** Text ≥ 12 px on phone, tablet and desktop; ≥ 18 px on a Parked head
   unit; ≥ 24 px in any Moving template; Drive digits ≥ 56 px; strip chips ≥ 48 px tall;
   head-unit targets 76 px; Moving tile and pane minimums per class. Numbers never clip:
   drop one type step. ([visual §4][vds-4], [visual §8][vds-8], [UI §3.2][ui-3.2],
   [Drive modes §4.4][dm-4.4])
3. **Tokens only.** Colours, type, space, radius, elevation and motion come from the visual
   spec's tokens in all four themes (Night, Night dim, Deep night, Day); no raw colours.
   ([visual §2][vds-2], [visual §3.1][vds-3.1], [visual §9][vds-9])
4. **One icon set.** Material Symbols, outlined; never an emoji, dingbat or Unicode arrow in
   UI text; every icon paired with a word where it carries meaning. ([visual §6][vds-6])
5. **No glow on head units at night.** At most one glowing element per screen on phone,
   tablet and desktop; none on head units in Night dim or Deep night, in Drive mode or in
   any Moving template; no blur or gradients on head units. ([visual §1][vds-1],
   [visual §5][vds-5], [UI §12.5][ui-12.5])
6. **Motion** only for sheet open and close, tab change and the alarm pulse; none while
   Moving (an rpm sweep steps, it does not glide). ([visual §5][vds-5],
   [Drive modes §4.3][dm-4.3])
7. **One accent, calm gauges.** Cyan accent for interactive and live things only; status
   colours (ISO 2575) with icon and word, only out of range; data ramps never use the
   accent; at most three categorical series. ([visual §1][vds-1], [visual §3.3][vds-3.3])
8. **Park to edit.** Edit mode, the widget picker, the rail editor and the Drive editor exist
   only Parked (or Idling with Park evidence) on a driver-facing display; while Moving a
   long-press shows "Park to edit" and nothing else. ([Drive modes §8.1][dm-8.1],
   [UI §15.2][ui-15.2])
9. **Safety items are not removable.** The fault telltale, alarm and Security alerts, the
   core strip chips (including Drive mode), Mark, and the Passenger-view and service-mode
   frames are drawn by the shell outside any layout; Home's warnings and Security cards may
   move, never go. ([Drive modes §8.1][dm-8.1], [UI §15.2][ui-15.2])
10. **No message text while Moving.** A message alert shows the sender and the app with Play
    and Reply (approved 2026-10-07; the earlier "Message from *name*" with Play and Later was
    not chosen); never text, images, avatars or previews while Moving; the opt-in first-line
    preview only for a message that arrived while Parked.
    ([UI §12.1][ui-12.1], [UI §14][ui-14], [Social §12][soc-12])
11. **No video on driver-facing screens** while Idling or Moving, Passenger view included;
    calls are audio only. ([UI §12.1][ui-12.1], [Social §5][soc-5])
12. **No other people on the head-unit map while Moving**, except plain convoy markers for
    an opted-in ride: no names, avatars, photos or plates. ([UI §12.1][ui-12.1],
    [Vehicles & Map §7][vm-7])
13. **No text entry while Moving** (or Idling without Park evidence); no "always" option for
    Passenger view anywhere. ([UI §3.5][ui-3.5], [UI §12.1][ui-12.1])
14. **Honest states.** Stale values in grey with their age, missing as "—" never 0,
    `candidate` marked, "Not available on this car", "Needs the Brain", "Not in this
    session". ([visual §8][vds-8], [UI §3.8][ui-3.8], [UI §5.4][ui-5.4])
15. **Map-first.** Full-bleed Ostler Night or Day map with sheets over it; on head units the
    sheet sits on the passenger side; attribution as a collapsed control; hidden trip ends
    drawn as a dashed fade, never a circle. ([visual §7][vds-7], [UI §12.3][ui-12.3],
    [UI §13.1][ui-13.1])
16. **D-pad reachable.** Every interactive element has a focus state: a 3 px accent ring with
    a 2 px gap, no glow, shadow or size change; confirm sheets open with Cancel focused.
    ([Shell input §7][si-7], [Shell input §9][si-9])
17. **Driver side.** The rail sits on the driver's side; draw right-hand drive (the D2) and
    left-hand drive where the layout differs. ([UI §3.3][ui-3.3])
18. **Rail and destinations.** Five slots; More is always one of them (movable, renamable,
    re-iconable, never removed); any core destination, Home included, or add-on page may sit
    in any slot (default: Home first, More last); Home stays the landing page and the root
    of Back; everything else is under More → Pages. ([Drive modes §7.3][dm-7.3])
19. **No score.** Trips shows neutral facts only: no driving score, speed ranking or
    speed-limit history. ([UI §12.2][ui-12.2])
20. **Our names only.** No other brand's marks, fonts or signature colours; Figtree is the
    face. ([visual §4][vds-4], [visual §7][vds-7])

## 4. Reading the index

- **Layout classes** ([UI §3.1][ui-3.1], [UI §12.3][ui-12.3]): Phone 393×852 · Tablet ·
  Desktop · HU-5 800×480 · HU-7 1024×600 · HU-9/10 1280×720 · HU-wide 1920×720 (1280×480 is
  a HU-wide test size). Desktop follows Tablet unless it is listed.
- **Themes** ([visual §3.1][vds-3.1]): **N** Night (default), **D** Day, **Nd** Night dim
  (head-unit classes only), **Dn** Deep night (OLED).
- **Driving states** ([UI §3.5][ui-3.5], [UI §12.1][ui-12.1]): **P** Parked, **I** Idling
  (text entry, Maintenance and edits need Park evidence), **M** Moving (unknown speed counts
  as Moving on head units), **PV** Passenger view on a head unit or "I'm a passenger" on a
  phone. A state listed with a render needs its own frame (`-moving`, `-passenger`).
- **Token codes** ([visual §3–§8][vds-3]): **S** surfaces and text (`surface-1/2/3`,
  `text-1/2/3`, `line`) · **G** `surface-glass` and Sheet over map · **A** `accent`,
  `accent-soft` · **St** `ok`/`warn`/`alarm`, `*-bg`, `warn-ink` · **T** Figtree type tokens,
  tabular numerals · **M** Ostler Night/Day maps · **Sp** `speed-1…6` and `trace-casing` ·
  **Se** `series-1…3` · **F** `focus-ring-*` · **I** Material Symbols. Named tokens are
  written out.
- **Area**: core (platform shell and core apps), an add-on by name, the developer add-on
  (Decode lab), Ostler Community web (`ostler-hub`) or a device's own firmware page.

## 5. Screen index

127 screens and sheets. Drive modes are listed per face; each face is designed in every
listed class, theme and state.

<!-- screens:begin (mirrors screens.json; keep both in step) -->
| Screen id | Name | Area | Layout classes | Themes | Driving states | Spec sections | Components · **tokens** |
|---|---|---|---|---|---|---|---|
| **Shell** | | | | | | | |
| `shell-strip` | Status strip (all chips) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: all chips for the class; M: same chips; Drive mode chip after Back in Drive mode; PV: Passenger view badge | [UI §3.2][ui-3.2] · [UI §12.1][ui-12.1] · [UI §15.1][ui-15.1] · [Drive modes §6][dm-6] · [Drive modes §8.1][dm-8.1] · [Accounts §14.7][acc-14.7] · [Maintenance §8][mg-8] · [Visual §8][vds-8] | Chip (status); Button (Back) · **S · St · A · I · type-label · F** |
| `shell-rail` | Driver-side rail and phone bottom bar | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: five slots + Drive button (HU); M: Drive mode is full screen; rail stays | [UI §3.3][ui-3.3] · [UI §3.4][ui-3.4] · [UI §12.2][ui-12.2] · [UI §15.2][ui-15.2] · [Drive modes §7.3][dm-7.3] · [Visual §8][vds-8] | TabBar (floating pill on phone, driver-side rail on HU) · **S · A · I · type-label · F** |
| `shell-rail-editor` | Rail editor (More → Preferences → Rail) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; I: full with Park evidence, else as Moving; M: 'Park to edit' toast, 3 s | [Drive modes §7.3][dm-7.3] · [UI §15.2][ui-15.2] · [Drive modes §8.1][dm-8.1] | ListRow (drag handle); Button; Sheet · **S · A · F** |
| `shell-home-edit` | Home edit mode (edit bar, handles, size, remove) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: long-press shows 'Park to edit' 3 s; editor closes to Drive, 'Finish editing when parked' | [Drive modes §7.1][dm-7.1] · [Drive modes §7.2][dm-7.2] · [UI §15.2][ui-15.2] | Card; Button (Done, Cancel, Undo, Redo, Preview, Reset); Segmented (class picker on phone/desktop) · **S · A · F · radius-md** |
| `shell-widget-picker` | Widget picker sheet | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §7.2][dm-7.2] · [App model §15.1][am-15.1] · [App model §15.2][am-15.2] | Sheet; ListRow (icon, bold name, one line, sizes); Chip (sizes) · **G · S · I** |
| `shell-reset-confirm` | Reset to default / Discard changes confirm | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §7.1][dm-7.1] · [Shell input §7][si-7] | Sheet; Button (Cancel focused); Chip ('All screen sizes') · **S · F** |
| `shell-connection-sheet` | Link chip sheet (connection ladder, queued actions) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full sheet; M: rows only, no new chip; lost role holder appears here | [UI §4.5][ui-4.5] · [UI §3.8][ui-3.8] · [UI §3.7][ui-3.7] · [Adapters §9][sa-9] | Sheet; ListRow; Button (Cancel queued); Chip · **S · St · I** |
| `shell-vehicle-switcher` | Active-vehicle switcher sheet | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; M: locked (system switching) | [UI §4.1][ui-4.1] | Sheet; Card (vehicle card with age) · **S · A** |
| `shell-telltale-sheet` | Worst-telltale sheet | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full fault list; M: telltale_list template, ≤ 30 characters a line | [UI §3.2][ui-3.2] · [UI §3.5][ui-3.5] · [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1] | Sheet; ListRow · **St · S · type-body (≥ 24 px Moving)** |
| `shell-locked-view` | Locked view ('Available when parked', Open on phone) | core | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | M: locked card with Open on phone and, where allowed, Passenger view | [UI §3.5][ui-3.5] · [UI §12.1][ui-12.1] | Card; Button · **S · I · type-body** |
| `shell-passenger-view` | Passenger prompt, Passenger view badge and frame | core | HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | M: prompt 'Are you a passenger?' (I'm a passenger / Cancel), then badge + frame + Back to Drive; PV: frame drawn by the shell | [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1] | Sheet; Button; Chip (badge) · **S · A · St** |
| `shell-phone-moving-banner` | Phone Moving banner and 'I'm a passenger' | core | Phone | N D | M: banner; non-driving views ask once per trip; PV: view-only | [UI §12.1][ui-12.1] | Card (tone); Button · **S · St** |
| `shell-service-mode` | Service mode frame and strip badge | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: frame + badge; M: refused; exits | [UI §3.5][ui-3.5] · [Drive modes §8.1][dm-8.1] | Chip (badge) · **St · line-strong** |
| `shell-brain-wake` | Brain wake sheet, queued button, 'Needs the Brain' card | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: no wake prompt in Drive mode | [UI §3.8][ui-3.8] | Sheet; Button (Wake and run / Cancel); Card · **S · A · St** |
| `shell-focus-states` | D-pad focus states across the kit | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: every kit component focused; M: Drive mode: alert card focus on safest button | [Shell input §4][si-4] · [Shell input §9][si-9] · [Shell input §10][si-10] · [Visual §8][vds-8] | Button; ListRow; Chip; Segmented; StatTile (acting tile); Scrubber (engaged); map (engaged, centre target) · **F · A · accent-soft (focused ListRow)** |
| **Network** | | | | | | | |
| `shell-buttons` | Display Buttons: bindings and Test buttons | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Shell input §8][si-8] · [UI §3.7][ui-3.7] | ListRow ('press the key now'); Button (Reset to defaults); Chip (tick per intent) · **S · A · St** |
| **More** | | | | | | | |
| `shell-driving-page` | 'Using Ostler while driving' page | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.1][ui-12.1] | Card · **S · type-body** |
| **Home** | | | | | | | |
| `home` | Home | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full; M: head units land on Drive mode; phone shows Moving banner | [UI §3.4][ui-3.4] · [UI §5.4][ui-5.4] · [UI §12.4][ui-12.4] · [UI §15.2][ui-15.2] · [Drive modes §7.2][dm-7.2] · [Visual §10][vds-10] · [App model §14.7][am-14.7] · [App model §15.4][am-15.4] | Card; HeroStat; StatTile; Button (Drive, secondary); Card (tone, warnings) · **S · St · T · bg-glow (phone only) · radius-md** |
| **Security** | | | | | | | |
| `security` | Security (alarm, events, tracker map) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full (landing when armed); M: arming only; clips locked | [UI §3.4][ui-3.4] · [UI §6][ui-6] | Card; Button; ListRow · **S · St · M** |
| **Drive modes** | | | | | | | |
| `drive-diagnostic-tiles` | Drive mode: Diagnostic · Tiles | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.1][dm-5.1] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | StatTile; Gauge · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow** |
| `drive-diagnostic-system` | Drive mode: Diagnostic · System view (Parked face) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: Parked face only; M: face absent | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.1][dm-5.1] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | StatTile; Gauge · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow** |
| `drive-dashboard-cluster` | Drive mode: Dashboard · Cluster | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.2][dm-5.2] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | HeroStat; Gauge (240° arc, rpm stepped); StatTile · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow** |
| `drive-dashboard-map` | Drive mode: Dashboard · Map with speed overlay | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.2][dm-5.2] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | HeroStat; Gauge (240° arc, rpm stepped); StatTile · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-map-map` | Drive mode: Map · Map | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.3][dm-5.3] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] · [Navigation §5.2][nav-5.2] | map template; StatTile (overlays) · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-convoy-map-ptt` | Drive mode: Convoy / Ride · Map + PTT | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.4][dm-5.4] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] · [Social §5][soc-5] | map template; call template (HOLD TO TALK); StatTile · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-convoy-ride` | Drive mode: Convoy / Ride · Ride | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.4][dm-5.4] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] · [Social §5][soc-5] | map template; call template (HOLD TO TALK); StatTile · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-offroad-tilt` | Drive mode: Off-road (D2) · Tilt | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.5][dm-5.5] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | inclinometer tile (static silhouette); StatTile; map template · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-offroad-trail` | Drive mode: Off-road (D2) · Trail map | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.5][dm-5.5] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | inclinometer tile (static silhouette); StatTile; map template · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-split-split` | Drive mode: Split / Media · Split | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.6][dm-5.6] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] · [Navigation §5.2][nav-5.2] | map template; media template; StatTile · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow · M** |
| `drive-minimal-minimal` | Drive mode: Minimal / Night · Minimal | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full Parked grid; M: Moving section only (≤ 6 tiles, panes, no animation); PV: full grid only if every widget is vehicle state / own location / driving camera | [UI §12.3][ui-12.3] · [UI §15.1][ui-15.1] · [Drive modes §4.3][dm-4.3] · [Drive modes §4.4][dm-4.4] · [Drive modes §5.7][dm-5.7] · [Drive modes §5.8][dm-5.8] · [Drive modes §5.9][dm-5.9] | HeroStat; value line · **type-hero · type-num-xl (digits ≥ 56 px) · S · St · band · no glow, no bg-glow** |
| `drive-switcher` | Drive mode chip and mode list | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: list adds 'Edit modes…'; M: tap cycles ≤ 4; long-press short_list ≤ 6, no Edit row | [Drive modes §6][dm-6] · [UI §15.1][ui-15.1] · [Shell input §6][si-6] | Chip; short_list (ListRow ≤ 30 characters, tick) · **S · A · F · type-body (≥ 24 px)** |
| `drive-menu` | Drive menu | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | M: short_list ≤ 6 rows, one level, state on the right; P: same; order editable Parked | [Shell input §6][si-6] · [App model §15.3][am-15.3] · [Navigation §5.6][nav-5.6] | short_list; ListRow (state text ≤ 12 characters) · **S · F · type-body (≥ 24 px)** |
| `drive-modes-list` | Drive modes list (rotation, add, rename, share) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §7.4][dm-7.4] · [Drive modes §8.4][dm-8.4] | ListRow (drag); Button; Sheet · **S · A** |
| `drive-mode-editor` | Drive mode editor (faces, grid, Moving strip) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §7.1][dm-7.1] · [Drive modes §7.4][dm-7.4] · [Drive modes §8.2][dm-8.2] | Segmented (face tabs); StatTile; Chip ('Moving: 5 of 6 tiles, 1 of 2 panes'); Button · **S · A · F · St** |
| `drive-widget-settings` | Widget settings sheet (signal, style, units, thresholds) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §7.4][dm-7.4] · [App model §15.2][am-15.2] | Sheet; ListRow (VSS picker with confidence word); Segmented; Gauge (live band preview) · **S · St · band** |
| `drive-mode-preview` | Preview: Parked and Moving side by side, failed rules | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §7.4][dm-7.4] · [Drive modes §8.2][dm-8.2] | Card; ListRow (rule failures in words) · **S · St** |
| `drive-layout-import` | Layout import / export (file, link, QR) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Drive modes §8.4][dm-8.4] · [UI §15.2][ui-15.2] | Sheet; Button (Save as file, Copy link, QR, Share); Card (preview) · **S · St** |
| **Alerts** | | | | | | | |
| `alert-message` | Message alert card | core (any add-on raises it) | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | M: line 1 sender ≤ 30, line 2 app; Play / Reply; no text; P: optional first-line preview (opt-in, off by default) | [UI §14][ui-14] · [UI §12.1][ui-12.1] · [Social §12][soc-12] · [Social §13][soc-13] · [Phone & Comms §8][pc-8] · [Shell input §6][si-6] | alert_card; Button (Play, Reply) · **S · F · type-body (≥ 24 px) · I** |
| `alert-reply-list` | Reply list (Speak a reply + canned replies) | core | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | M: short_list ≤ 6 rows; voice reply read back Send / Cancel (Cancel focused); no transcript | [UI §14][ui-14] · [Social §12][soc-12] | short_list; Button · **S · F** |
| `alert-other` | Other alert cards (alarm, maintenance due, convoy, community) | core | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | M: alert_card ≤ 2 lines, ≤ 2 buttons; P: same | [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1] · [Maintenance §8][mg-8] · [Vehicles & Map §7][vm-7] · [Community §15.2][hub-15.2] | alert_card · **St · S** |
| `alert-settings` | Message alert settings (canned replies, preview, group alerts, auto-reply) | core | Phone Tablet Desktop HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §14][ui-14] · [Social §12][soc-12] | ListRow; Segmented; Button · **S · A** |
| `call-template` | Call template (incoming, in call, PTT) | core template; Social and Phone & Comms use it | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | M: name ≤ 30, no photo, timer, ≤ 3 buttons ≥ 76 px; audio only; P: same template; video only on non-driver-facing displays | [UI §12.1][ui-12.1] · [App model §14.5][am-14.5] · [App model §15.5][am-15.5] · [Social §5][soc-5] · [Social §13][soc-13] · [Phone & Comms §6.1][pc-6.1] · [Phone & Comms §6.2][pc-6.2] | call template; Button · **S · St · F · I** |
| **Trips** | | | | | | | |
| `trips-list` | Trips list | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.2][ui-12.2] · [Visual §9][vds-9] | ListRow (mini dark map); Card ('Recording now' + End trip now); Chip (filters, All events) · **S · M · Sp · T** |
| `trips-detail` | Trip detail (map + sheet) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.2][ui-12.2] · [UI §12.3][ui-12.3] · [Visual §10][vds-10] | Sheet over map; HeroStat; StatTile (3×3 grid); Donut + Segmented (Time / Distance); Area line; Button · **G · M · Sp · T · chart-grid, chart-axis** |
| `trips-playback` | Trip playback | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked (replay scrubbing) | [UI §12.2][ui-12.2] · [Visual §8][vds-8] | Scrubber; Chip (1×/2×/4×/8×); HeroStat (readout) · **G · M · Sp · A** |
| `trips-statistics` | Statistics tab | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.2][ui-12.2] | HeroStat; StatTile; DistributionBars; year heatmap + month calendar · **S · Sp · T** |
| `trips-records` | Records and Sprints | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.2][ui-12.2] · [Visual §6][vds-6] | Card (per band); ListRow (rank, time, delta) · **S · T · surface-3 rank disc** |
| `trips-export-all` | Export all | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.2][ui-12.2] · [App model §14.6][am-14.6] | Card; Button · **S** |
| `trips-share-sheet` | Trips share sheet (audience, level ladder, options, expiry) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; phone any time; I: with Park evidence; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §13.1][ui-13.1] · [Trip sharing §3][ts-3] · [Trip sharing §10][ts-10] · [Accounts §15.2][acc-15.2] · [Accounts §15.4][acc-15.4] · [Community §15.2][hub-15.2] | Sheet; ListRow (L0–L4 with chips); Chip (countdown); Segmented (durations); Button (Share / Copy link / Save file / Send to helper / Ask on Ostler Community) · **G · warn token for L3/L4 rows and 'can't be taken back' · S · A** |
| `trips-share-preview` | 'What they will see' preview and redaction report | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §13.1][ui-13.1] · [Trip sharing §11][ts-11] · [Trip sharing §9.3][ts-9.3] | Sheet; Chip row (redaction report); Card · **M · bg (dashed fade at hidden ends, never a circle) · font-mono + text-3 for scrubbed bytes · St** |
| `trips-share-history` | Trip share history and revoke | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §13.1][ui-13.1] · [Trip sharing §11][ts-11] | ListRow; Chip (state); Button (Revoke) · **S · St** |
| **More** | | | | | | | |
| `places` | More → Places (privacy zones, ends trim) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §13.4][ui-13.4] · [Trip sharing §5.1][ts-5.1] · [Trip sharing §5.2][ts-5.2] | ListRow; Segmented (radius); slider (ends trim 200 m–1.5 km); map with offset circle + note · **M · S · A** |
| **Diagnose** | | | | | | | |
| `diagnose-systems` | Diagnose: identity bar, Scan all, systems | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: reading; M: locked (system switching) | [UI §3.4][ui-3.4] · [UI §4.2][ui-4.2] · [UI §4.3][ui-4.3] · [UI §4.4][ui-4.4] | ListRow (status chip + fault count); Button (Scan all, Stop); Chip · **S · St** |
| `diagnose-system` | System areas (Overview, Faults, Live, Tests, Procedures, Settings) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: Maintenance with Park evidence; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §4.2][ui-4.2] · [UI §7][ui-7] | Segmented / tabs; StatTile; ListRow · **S · St · T** |
| `diagnose-fault` | Fault detail sheet + Get help with this fault | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: telltale sheet only | [UI §13.2][ui-13.2] · [Visual §9][vds-9] | Sheet; Button (Get help, secondary); ListRow (related live data and tests) · **S · St** |
| `diagnose-confirm` | Action confirm sheets (Tier 1–3, clear codes) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Shell input §7][si-7] · [UI §7][ui-7] · [UI §7.2][ui-7.2] | Sheet; Button (Cancel focused, danger) · **S · St** |
| `help-flow` | Help flow (decode or diagnose; recipe; recipient; preview; send) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Trip sharing §13][ts-13] · [UI §13.2][ui-13.2] · [UI §13.3][ui-13.3] · [Community §8][hub-8] · [Community §15.2][hub-15.2] | Sheet; ListRow; Chip; Button (Send to helper / Ask on Ostler Community) · **S · St** |
| **Decode lab** | | | | | | | |
| `decode-lab` | Decode lab (Detect → Scan → Sniff → Correlate → Label → Verify → Contribute) | developer add-on (Decode lab) | Tablet Desktop HU-9/10 HU-wide Phone | N D Nd | P: service mode only; M: refused, exits | [UI §8.4][ui-8.4] · [UI §13.3][ui-13.3] · [App model §14.1][am-14.1] | byte grid + bit-flip heat map; ListRow (evidence checklist); Card (JSON preview); Button (Ask for help decoding) · **S · font-mono · plasma/mako (heat map) · St** |
| **Vehicles & Map** | | | | | | | |
| `vehicles-map` | Vehicles & Map: map with bottom sheet | add-on: Vehicles & Map | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence; M: no other vehicles; convoy markers only in Drive; PV: never unlocked; Open on phone | [Vehicles & Map §3][vm-3] · [Vehicles & Map §7][vm-7] | Sheet over map; pin (silhouette badge, heading, age ring); Chip (visibility) · **M · G · status vocabulary (ADR-0008) · A** |
| `vehicles-list` | Vehicles list (Mine, Shared with me, groups) | add-on: Vehicles & Map | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence; M: no other vehicles; convoy markers only in Drive; PV: never unlocked; Open on phone | [Vehicles & Map §2.1][vm-2.1] | ListRow · **S · St** |
| `vehicles-garage-card` | Garage card and View as… | add-on: Vehicles & Map | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence; M: no other vehicles; convoy markers only in Drive; PV: never unlocked; Open on phone | [Vehicles & Map §2.2][vm-2.2] · [Accounts §14.7][acc-14.7] | Card; StatTile (≤ 6 live) · **S · T** |
| `vehicles-visibility` | Visibility sheet (ghost off: 1 h, 24 h, until I go ghost) | add-on: Vehicles & Map (core toggle) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd Dn | P: full; M: going ghost one tap; becoming visible waits for Parked | [Vehicles & Map §4][vm-4] · [Accounts §14.3][acc-14.3] · [Accounts §14.7][acc-14.7] | Sheet; Segmented; Chip · **S · A** |
| `vehicles-share` | Per-friend, group and field sharing; Share live options | add-on: Vehicles & Map | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Vehicles & Map §5][vm-5] · [Accounts §15.3][acc-15.3] · [Trip sharing §12][ts-12] | Sheet; ListRow; Segmented (trail window, delay); toggle (show speed, show values) · **S · A** |
| **Social** | | | | | | | |
| `social-chats` | Social: Chats (1:1, groups, ride channels) and conversation | add-on: Social | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: replaced by alert_card / call template; PV: phone only: full Social | [Social §2][soc-2] · [Social §3][soc-3] · [Social §4][soc-4] · [Social §5][soc-5] · [Social §6][soc-6] | ListRow; Card; Button; Chip (link badge) · **S · A · St** |
| `social-calls` | Social: Calls (history) | add-on: Social | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: replaced by alert_card / call template; PV: phone only: full Social | [Social §2][soc-2] · [Social §3][soc-3] · [Social §4][soc-4] · [Social §5][soc-5] · [Social §6][soc-6] | ListRow; Card; Button; Chip (link badge) · **S · A · St** |
| `social-rides` | Social: Rides (live ride panel) | add-on: Social | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: replaced by alert_card / call template; PV: phone only: full Social | [Social §2][soc-2] · [Social §3][soc-3] · [Social §4][soc-4] · [Social §5][soc-5] · [Social §6][soc-6] | ListRow; Card; Button; Chip (link badge) · **S · A · St** |
| `social-cameras` | Social: Cameras (S4) | add-on: Social | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: replaced by alert_card / call template; PV: phone only: full Social | [Social §2][soc-2] · [Social §7][soc-7] | ListRow; Card; Button; Chip (link badge) · **S · A · St** |
| **Phone & Comms** | | | | | | | |
| `phone-page` | More → Phone (Favourites, Recents, Contacts, Keypad, Messages, Settings) | add-on: Phone & Comms | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: as Parked, no keypad; M: locked view: 'Available when parked' + Open on phone (UI §12.1); PV: nothing beyond the templates; Open on phone | [Phone & Comms §10][pc-10] · [Phone & Comms §12][pc-12] · [App model §15.4][am-15.4] | Segmented (tabs); ListRow; Button · **S · A · I** |
| `phone-dialer` | Phone & Comms: Dialer (keypad and voice dial) | add-on: Phone & Comms | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: keypad, voice dial, emergency entry; I: keypad locked; voice dial; M: no keypad; voice dial only, > 1 match as short_list ≤ 6, read back, no transcript | [Phone & Comms §4][pc-4] · [UI §12.1][ui-12.1] · [Shell input §6][si-6] | keypad grid; Button (Call, voice dial); short_list (matches) · **S · A · F · T** |
| `phone-favourites` | Phone & Comms: Favourites | add-on: Phone & Comms | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: grid/list, edit, reorder, pick from phone; I: read and call; M: short_list ≤ 6 rows, name ≤ 30, source glyph; tap calls | [Phone & Comms §4][pc-4] · [Phone & Comms §5][pc-5] · [Phone & Comms §12][pc-12] · [Social §13][soc-13] · [App model §15.2][am-15.2] | ListRow (source badge); short_list; Button · **S · A · F** |
| `phone-recents` | Phone & Comms: Recents | add-on: Phone & Comms | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full list, filter, call back; I: read and call; M: not shown; Drive menu 'Call back last' | [Phone & Comms §4][pc-4] · [Phone & Comms §6.5][pc-6.5] · [Social §13][soc-13] | ListRow (direction, source, time); Button (call back) · **S · St** |
| `phone-contacts` | Phone & Comms: Contacts (Ostler + phone, badged) | add-on: Phone & Comms | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; I: read and call; no keypad; search only with Park evidence; M: not shown on a driver-facing display; voice dial instead | [Phone & Comms §5][pc-5] · [Accounts §14.6][acc-14.6] | ListRow (badge Ostler / Phone / both); Sheet (consent: read this phone's contacts); Button ('Same person') · **S · A** |
| `phone-incoming` | Phone & Comms: incoming call and in call | add-on: Phone & Comms (core call template) | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | P: full call screen (DTMF keypad, hold, swap, audio route); I: call template; M: call template: name ≤ 30, no photo, Answer / Decline, then Mute / End / Audio | [Phone & Comms §6.1][pc-6.1] · [Phone & Comms §6.2][pc-6.2] · [Phone & Comms §6.4][pc-6.4] · [Social §13][soc-13] · [App model §15.5][am-15.5] | call template; Button · **S · St · F · I** |
| `phone-message-card` | Phone & Comms: message card (SMS/iMessage, notification bridge) | add-on: Phone & Comms (core alert_card) | HU-5 HU-7 HU-9/10 HU-wide Phone | N D Nd Dn | M: line 1 sender ≤ 30, line 2 the real app ('Messages', 'WhatsApp'); Play / Reply; no text; P: optional first-line preview (opt-in, off by default) | [Phone & Comms §7.1][pc-7.1] · [Phone & Comms §7.2][pc-7.2] · [Phone & Comms §8][pc-8] · [UI §14][ui-14] · [Social §13][soc-13] | alert_card; short_list (Reply) · **S · F · type-body (≥ 24 px) · I** |
| `phone-widgets` | Phone & Comms widgets (Favourites tile, Phone pane, Recent calls) | add-on: Phone & Comms | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: Parked views; M: Favourites as short_list ≤ 6; Phone pane as call template (idle: phone name, battery, signal, voice dial); Recent calls 'Available when parked' | [Phone & Comms §12][pc-12] · [App model §15.1][am-15.1] · [App model §15.2][am-15.2] · [Drive modes §4.3][dm-4.3] | short_list; call template; ListRow · **S · A · St** |
| `phone-pairing` | Phone & Comms: Pair a phone (numeric comparison, hands-free owner) | add-on: Phone & Comms | HU-5 HU-7 HU-9/10 HU-wide Phone Tablet | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Phone & Comms §13][pc-13] · [Phone & Comms §3.2][pc-3.2] | Sheet; Card (six digits); Segmented ('Ostler is the hands-free' / 'My head unit'); Button · **S · A · St** |
| `phone-bridge-setup` | Companion: notification bridge setup and allow list (Android) | add-on: Phone & Comms (companion app) | Phone | N D | P: full, on the phone; M: phone Moving banner | [Phone & Comms §7.2][pc-7.2] · [Phone & Comms §3.3][pc-3.3] · [Phone & Comms §9][pc-9] | Card (what it reads); ListRow (per-app allow list); Button (open Android notification access) · **S · A** |
| **Navigation** | | | | | | | |
| `nav-turn-card` | Turn card (next manoeuvre in the map template) | add-on: Navigation | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | M: map template: arrow, stepped distance, road ≤ 30, then-preview, lanes, ETA toggle, NAV/TRACK badge | [Navigation §5.2][nav-5.2] · [UI §12.1][ui-12.1] · [UI §13.5][ui-13.5] | map template; StatTile (distance to go) · **G · text-1 / text-3 (lanes) · type-num-xl · M · I** |
| `nav-off-route` | Off route card ('rerouting in 8 s') | add-on: Navigation | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | M: alert_card, Reroute focused, seconds as text | [Navigation §5.3][nav-5.3] · [Shell input §7][si-7] | alert_card; Button · **S · F** |
| `nav-page` | Navigation page (search, destinations, profiles) | add-on: Navigation | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Navigation §4][nav-4] · [Navigation §6.4][nav-6.4] · [Navigation §3][nav-3] · [Navigation §9][nav-9] | ListRow; Chip (profile); Card ('Check local access rules') · **S · M** |
| `nav-planner` | Planner (Parked) | add-on: Navigation | Phone Tablet Desktop HU-7 HU-9/10 HU-wide | N D Nd | P: full; I: locked; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Navigation §6.5][nav-6.5] | Sheet over map; ListRow (stops, drag); Button (Start on head unit) · **M · G · S** |
| `nav-library` | GPX library and follow a track | add-on: Navigation | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Navigation §6.1][nav-6.1] · [Navigation §6.2][nav-6.2] · [Navigation §6.3][nav-6.3] | ListRow (folders, tags); Segmented (Turns / Line / Hybrid); Button (Export library) · **S · M · Se** |
| `nav-roadbook` | Roadbook view (N4) | add-on: Navigation | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide | N D Nd Dn | P: full roadbook; M: CAP and partials as tiles; tulip as next manoeuvre | [Navigation §6.6][nav-6.6] | ListRow (tulip rows); StatTile · **S · type-num-xl** |
| **Preferences** | | | | | | | |
| `maps-regions` | Settings → Maps: offline regions | core (extended by Navigation) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Navigation §3][nav-3] · [Visual §7][vds-7] | ListRow (size, date, Update); Button · **S · St** |
| **Ostler Community** | | | | | | | |
| `hub-web-p1` | Ostler Community web: P1 Discover | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §12][hub-12] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p2` | Ostler Community web: P2 Shared trip | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §6][hub-6] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p3` | Ostler Community web: P3 Help thread | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §8][hub-8] · [Community §9][hub-9] | ListRow; Chip (kind, solved, status, vehicle); Card; Button · **S · M · Se · A · visibility chip** |
| `hub-web-p4` | Ostler Community web: P4 Group or club | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §12][hub-12] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p5` | Ostler Community web: P5 Live ride | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §12][hub-12] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p6` | Ostler Community web: P6 Event | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §12][hub-12] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p7` | Ostler Community web: P7 Profile | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §12][hub-12] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p8` | Ostler Community web: P8 Publish | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §6][hub-6] · [Community §7][hub-7] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p9` | Ostler Community web: P9 My shares | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §7][hub-7] | Card; ListRow; Chip; Sheet over map; HeroStat · **S · M · Se · A · visibility chip** |
| `hub-web-p10` | Ostler Community web: P10 Forum | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §9][hub-9] | ListRow; Chip (kind, solved, status, vehicle); Card; Button · **S · M · Se · A · visibility chip** |
| `hub-web-p11` | Ostler Community web: P11 Thread | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §9][hub-9] | ListRow; Chip (kind, solved, status, vehicle); Card; Button · **S · M · Se · A · visibility chip · font-mono (exact tokens, fixtures)** |
| `hub-web-p12` | Ostler Community web: P12 Vehicle project | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §10.3][hub-10.3] · [Community §10.1][hub-10.1] | ListRow; Chip (kind, solved, status, vehicle); Card; Button · **S · M · Se · A · visibility chip** |
| `hub-web-p13` | Ostler Community web: P13 Decode card | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §10.2][hub-10.2] · [Community §10.4][hub-10.4] | ListRow; Chip (kind, solved, status, vehicle); Card; Button · **S · M · Se · A · visibility chip · font-mono (exact tokens, fixtures)** |
| `hub-web-p14` | Ostler Community web: P14 Wiki page | Ostler Community web (ostler-hub, closed, Ostler-run) | Phone Tablet Desktop | N D | P: web page; no driving rules | [Community §15.1][hub-15.1] · [Community §11][hub-11] | ListRow; Chip (kind, solved, status, vehicle); Card; Button · **S · M · Se · A · visibility chip** |
| `hub-shell` | More → Community (Discover · Forum · Help · Mine, plus Wiki links) | add-on: Ostler Community (ostler-app-hub, open; closed Ostler-run hub) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1); PV: phone only | [Community §15.2][hub-15.2] · [Community §4][hub-4] · [App model §15.4][am-15.4] | ListRow; Card; Segmented (tabs) · **S · A** |
| **Adapters** | | | | | | | |
| `adapter-connect` | Use an adapter: transport, pair, detection | core (source adapters) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full (detection steps 3–6 Parked only); M: locked | [Adapters §9][sa-9] · [Adapters §5][sa-5] · [Adapters §6][sa-6] | Sheet; ListRow; Button; progress rows · **S · St** |
| `adapter-verdict` | Adapter verdict and capability chips (clone chip) | core (source adapters) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: link chip shows kind + verdict | [Adapters §5][sa-5] · [Adapters §7][sa-7] · [Adapters §9][sa-9] | Chip ('Clone: read-only', 'ELM: limited', 'Listen-only: requested', 'Soft gate'); Card · **St · S** |
| `adapter-soft-gate` | Adapter actions opt-in (soft gate warning) and badge | core (source adapters) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: every action refused; speed unknown counts as Moving | [Adapters §7][sa-7] · [Adapters §7.1][sa-7.1] · [Adapters §9][sa-9] | Sheet; Button (Cancel focused); Chip (persistent badge) · **St · S** |
| **Maintenance & Garage** | | | | | | | |
| `maint-home` | Maintenance home per vehicle | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Visual §3.3][vds-3.3] | HeroStat (total cost); Donut (this month); Card (category tiles + Add); ListRow (Insights, Due) · **S · Se · T · St** |
| `maint-due` | Maintenance: Due tab | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Maintenance §2][mg-2] · [Maintenance §3][mg-3] | ListRow (provenance suffix); Chip (band pill) · **S · Se · St** |
| `maint-timeline` | Maintenance: Timeline tab | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Maintenance §2][mg-2] | ListRow (provenance suffix); Chip (band pill) · **S · Se · St** |
| `maint-costs` | Maintenance: Costs tab | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Maintenance §2][mg-2] | ListRow (provenance suffix); Chip (band pill) · **S · Se · St** |
| `maint-fuel` | Maintenance: Fuel tab | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Maintenance §2][mg-2] | ListRow (provenance suffix); Chip (band pill) · **S · Se · St** |
| `maint-documents` | Maintenance: Documents tab | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Maintenance §2][mg-2] | ListRow (provenance suffix); Chip (band pill) · **S · Se · St** |
| `maint-add-record` | Add record (service, fuel, expense, document) | add-on: Maintenance & Garage | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Maintenance §2][mg-2] · [Maintenance §7][mg-7] | Sheet; form fields; Button · **S** |
| `maint-kiosk` | Parked head-unit Due view (kiosk) | add-on: Maintenance & Garage | HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; I: editing with Park evidence; M: nothing but trip start/end alert | [Maintenance §7][mg-7] · [Maintenance §8][mg-8] | ListRow; Chip (band pill) · **S · St** |
| `garage` | More → Garage (vehicles, garage cards) | core (+ Maintenance garage card) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §4.1][ui-4.1] · [Accounts §4][acc-4] · [Maintenance §7][mg-7] | Card; ListRow · **S** |
| **Network** | | | | | | | |
| `network` | More → Network (devices, links, roles, uplinks, remote, pairing, power) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §3.7][ui-3.7] · [UI §3.8][ui-3.8] | ListRow; Chip (power state words); Button (Wake); Card · **S · St** |
| `network-device` | Device page (Remove device, Buttons, power) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §3.7][ui-3.7] · [UI §3.8][ui-3.8] · [Shell input §8][si-8] | ListRow; Button (Remove device, danger; Acknowledge); Sheet (confirm) · **S · St** |
| `device-local-page` | A device's own local web page (peers section) | firmware page (outside the shell) | Phone Tablet Desktop | N D | P: read-only peers | [UI §3.7][ui-3.7] · [App model §12][am-12] | ListRow · **S · St** |
| **More** | | | | | | | |
| `more` | More (Pages, Add-ons, Garage, Network, Places, … About) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §3.4][ui-3.4] · [UI §12.4][ui-12.4] · [UI §13.4][ui-13.4] · [Drive modes §7.3][dm-7.3] | ListRow · **S · I** |
| `addons-catalogue` | More → Add-ons (Installed, Available) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [UI §12.4][ui-12.4] · [App model §14.2][am-14.2] | Segmented (tabs); Card (Core / Add-on / Developer label, requires, data classes); Button · **S · A** |
| **Preferences** | | | | | | | |
| `preferences` | Preferences (theme, map theme, units, rail) | core | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; I: full with Park evidence, else as Moving; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Visual §1][vds-1] · [Visual §2][vds-2] · [UI §13.5][ui-13.5] · [Drive modes §7.3][dm-7.3] | Segmented (Night · Day · Auto; map theme Follow app · Day · Night · High contrast); ListRow · **S · A** |
| **Accounts** | | | | | | | |
| `accounts-s1` | Accounts S1: First run (owner creation) | core (accounts) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] · [Accounts §2.1][acc-2.1] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s2` | Accounts S2: Sign in | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s3` | Accounts S3: Passkeys | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s4` | Accounts S4: Profile switcher (head unit) | core (accounts) | HU-5 HU-7 HU-9/10 HU-wide | N D Nd | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s5` | Accounts S5: Users and roles | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s6` | Accounts S6: Signed-in devices | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s7` | Accounts S7: Contacts, groups and invites | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] · [Accounts §14.6][acc-14.6] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s8` | Accounts S8: Sharing ('who sees what') with View as… | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] · [Accounts §15.4][acc-15.4] · [Trip sharing §11][ts-11] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s9` | Accounts S9: Ghost toggle (visibility chip and sheet) | core (accounts) | Phone Tablet HU-5 HU-7 HU-9/10 HU-wide Desktop | N D Nd Dn | P: full; M: going ghost one tap while Moving | [Accounts §14.7][acc-14.7] · [Accounts §14.3][acc-14.3] | ListRow; Button; Sheet; Chip · **S · A · St** |
| `accounts-s10` | Accounts S10: Safety contacts | core (accounts) | Phone Tablet Desktop | N D | P: full; M: locked view: 'Available when parked' + Open on phone (UI §12.1) | [Accounts §14.7][acc-14.7] | ListRow; Button; Sheet; Chip · **S · A · St** |
<!-- screens:end -->

Phone & Comms rows cite sections of the Phone & Comms spec (approved 2026-10-07); if its
section numbers change, regenerate both `screens.json` and this table.

## Changelog

- **0.1 (2026-10-07):** first draft for the DMD round: hand-over and naming, the per-screen
  record, the review process, the designer prompt checklist and the index of 116 screens in
  this README and `screens.json`.
- **0.2 (2026-10-07, cross-spec reconcile):** Phone & Comms rows link the exact sections of
  the draft Phone & Comms spec (the four provisional rows replaced by ten: More → Phone,
  dialer, favourites, recents, contacts, incoming call, message card, widgets, pairing,
  companion bridge setup); Ostler Community rows follow hub spec v0.2 (closed, Ostler-run; web
  P10–P14 Forum, Thread, Vehicle project, Decode card and Wiki page added; More → Community
  reads Discover · Forum · Help · Mine, plus Wiki links; hub section links renumbered); the
  share sheet and help flow show "Ask on Ostler Community"; the call template links the shell's
  call session; 127 screens.
- **0.3 (2026-10-07):** approved by the owner on 2026-10-07 ("approve all", DMD round;
  decision list items 92–96): every decision answered as recommended (alternatives not
  chosen); the cited specs and amendments approved, so their links follow the renamed
  "Amendment (2026-10-07, DMD round), approved" headings (here and in `screens.json` 0.3,
  whose review statuses are unchanged); checklist item 10 shows the approved message card
  and item 18 the approved editable rail.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each recommendation
below is the decision; each alternative was not chosen. Decision 3 is settled by the same
approval: items 57–61 (M1–M4) were approved, so the designer draws the sender-and-app card;
the "Message from *name*" card is no longer needed. Decision 5: the Phone & Comms spec is
approved, so its screens are no longer provisional.

1. **How much of the class × theme matrix in the first pass?** *Recommend:* key frames first:
   Night on every listed class; Night dim and the Moving state for every Drive-mode face,
   alert, call and turn card on HU-7 and HU-5; Day on phone; the rest after the first review.
   *Alternative:* the full matrix in one delivery.
2. **Licence of the design files committed here.** *Recommend:* the designer contributes
   under the CLA (ADR-0012) and the files are annotated AGPL-3.0-or-later like the docs, in
   `REUSE.toml` in the same commit, naming the copyright holder you confirm. *Alternative:*
   keep only links and screenshots outside the repo; this folder holds the register only.
3. **Message alert designs while M1–M4 are open.** *Recommend:* draw both cards (proposed:
   sender and app with Play and Reply; approved: "Message from *name*" with Play and Later).
   *Alternative:* draw only the proposed card and accept rework if it is not approved.
4. **HTML exports in the repo.** *Recommend:* PNG plus HTML per frame, each file ≤ 2 MB;
   larger HTML is kept as the artifact link only. *Alternative:* PNG only.
5. **Phone & Comms screens before its spec is approved? (revised, reconcile)** *Recommend:*
   include the ten screens in the prompt, linked to the draft Phone & Comms spec's sections and
   bound by the shared rules (`call`, `short_list` ≤ 6, keypad Parked only, no text entry
   while Moving); re-review if the spec changes at approval. *Alternative:* leave them out of
   this prompt until the spec is approved.
6. **Desktop class.** *Recommend:* Desktop follows Tablet unless a screen lists it
   (web, editors, Decode lab, accounts). *Alternative:* a Desktop frame for every screen.

[acc-14.3]: ../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode
[acc-14.6]: ../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites
[acc-14.7]: ../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[acc-15.2]: ../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142
[acc-15.3]: ../../../specs/2026-10-06-accounts-sharing-design.md#153-live-trip-grant-options-changes-142-used-by-vehicles--map
[acc-15.4]: ../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412
[acc-2.1]: ../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap
[acc-4]: ../../../specs/2026-10-06-accounts-sharing-design.md#4-multi-vehicle-garage
[am-12]: ../../../specs/2026-10-06-app-model-design.md#12-the-network-app-and-device-pages-accepted-2026-10-06
[am-14.1]: ../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-14.2]: ../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-14.5]: ../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-14.6]: ../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-14.7]: ../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-15.1]: ../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.2]: ../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.3]: ../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.4]: ../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.5]: ../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.3]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-4.4]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-5.1]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#51-diagnostic-todays-six-tiles
[dm-5.2]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#52-dashboard-realdash-style-cluster
[dm-5.3]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#53-map
[dm-5.4]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#54-convoy--ride
[dm-5.5]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[dm-5.6]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media
[dm-5.7]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#57-minimal--night
[dm-5.8]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#58-faces-per-preset
[dm-5.9]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[dm-6]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#6-the-switcher
[dm-7.1]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-7.2]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.3]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-7.4]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-8.1]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[dm-8.4]: ../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[hub-10.1]: ../../../specs/2026-10-07-community-hub-design.md#101-the-path
[hub-10.2]: ../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench
[hub-10.3]: ../../../specs/2026-10-07-community-hub-design.md#103-vehicle-projects
[hub-10.4]: ../../../specs/2026-10-07-community-hub-design.md#104-the-github-bridge
[hub-11]: ../../../specs/2026-10-07-community-hub-design.md#11-the-wiki
[hub-12]: ../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments
[hub-15.1]: ../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub
[hub-15.2]: ../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub
[hub-4]: ../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking
[hub-6]: ../../../specs/2026-10-07-community-hub-design.md#6-what-can-be-published
[hub-7]: ../../../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls
[hub-8]: ../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs
[hub-9]: ../../../specs/2026-10-07-community-hub-design.md#9-the-forum
[mg-2]: ../../../specs/2026-10-07-maintenance-garage-addon-design.md#2-schema
[mg-3]: ../../../specs/2026-10-07-maintenance-garage-addon-design.md#3-reminder-engine
[mg-7]: ../../../specs/2026-10-07-maintenance-garage-addon-design.md#7-garage-screens
[mg-8]: ../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[nav-3]: ../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions
[nav-4]: ../../../specs/2026-10-07-navigation-addon-design.md#4-profiles
[nav-5.2]: ../../../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre
[nav-5.3]: ../../../specs/2026-10-07-navigation-addon-design.md#53-off-route-and-reroute
[nav-5.6]: ../../../specs/2026-10-07-navigation-addon-design.md#56-drive-menu-rows
[nav-6.1]: ../../../specs/2026-10-07-navigation-addon-design.md#61-library
[nav-6.2]: ../../../specs/2026-10-07-navigation-addon-design.md#62-import-and-export
[nav-6.3]: ../../../specs/2026-10-07-navigation-addon-design.md#63-follow-a-track
[nav-6.4]: ../../../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois
[nav-6.5]: ../../../specs/2026-10-07-navigation-addon-design.md#65-planner-parked
[nav-6.6]: ../../../specs/2026-10-07-navigation-addon-design.md#66-roadbook-view-n4
[nav-9]: ../../../specs/2026-10-07-navigation-addon-design.md#9-manifest-sketch
[pc-10]: ../../../specs/2026-10-07-phone-comms-addon-design.md#10-ui-per-layout-class-and-driving-state
[pc-12]: ../../../specs/2026-10-07-phone-comms-addon-design.md#12-widgets-and-drive-menu-app-model-15-contract
[pc-13]: ../../../specs/2026-10-07-phone-comms-addon-design.md#13-security
[pc-3.2]: ../../../specs/2026-10-07-phone-comms-addon-design.md#32-ostler-hfp-on-the-brain-path-b
[pc-3.3]: ../../../specs/2026-10-07-phone-comms-addon-design.md#33-the-companion-bridge-path-a
[pc-4]: ../../../specs/2026-10-07-phone-comms-addon-design.md#4-dialer
[pc-5]: ../../../specs/2026-10-07-phone-comms-addon-design.md#5-contacts-one-view-two-sources
[pc-6.1]: ../../../specs/2026-10-07-phone-comms-addon-design.md#61-incoming
[pc-6.2]: ../../../specs/2026-10-07-phone-comms-addon-design.md#62-in-call-call-template-while-moving-ui-121-app-model-145
[pc-6.4]: ../../../specs/2026-10-07-phone-comms-addon-design.md#64-messenger-calls-whatsapp-signal-telegram-messenger
[pc-6.5]: ../../../specs/2026-10-07-phone-comms-addon-design.md#65-call-log
[pc-7.1]: ../../../specs/2026-10-07-phone-comms-addon-design.md#71-sms-and-imessage-map-both-platforms
[pc-7.2]: ../../../specs/2026-10-07-phone-comms-addon-design.md#72-android-notification-bridge-opt-in
[pc-8]: ../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared
[pc-9]: ../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy
[sa-5]: ../../../specs/2026-10-07-source-adapters-design.md#5-detection-and-clone-checks
[sa-6]: ../../../specs/2026-10-07-source-adapters-design.md#6-hosts-and-transports
[sa-7]: ../../../specs/2026-10-07-source-adapters-design.md#7-safety-with-no-hardware-gate
[sa-7.1]: ../../../specs/2026-10-07-source-adapters-design.md#71-driving-state-without-a-node
[sa-9]: ../../../specs/2026-10-07-source-adapters-design.md#9-ui-summary-detail-in-u-phase-specs
[si-10]: ../../../specs/2026-10-07-shell-input-design.md#10-accessibility
[si-4]: ../../../specs/2026-10-07-shell-input-design.md#4-focus-zones-and-spatial-navigation
[si-6]: ../../../specs/2026-10-07-shell-input-design.md#6-drive-mode
[si-7]: ../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[si-8]: ../../../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test
[si-9]: ../../../specs/2026-10-07-shell-input-design.md#9-focus-visuals
[soc-12]: ../../../specs/2026-10-07-social-addon-design.md#12-amendment-2026-10-07-dmd-round-approved-message-alerts-while-moving
[soc-13]: ../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap
[soc-2]: ../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell
[soc-3]: ../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides
[soc-4]: ../../../specs/2026-10-07-social-addon-design.md#4-messaging
[soc-5]: ../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls
[soc-6]: ../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules
[soc-7]: ../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4
[ts-10]: ../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls
[ts-11]: ../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit
[ts-12]: ../../../specs/2026-10-07-trip-sharing-design.md#12-live-trips
[ts-13]: ../../../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose
[ts-3]: ../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels
[ts-5.1]: ../../../specs/2026-10-07-trip-sharing-design.md#51-ends-trim-every-trip-r5
[ts-5.2]: ../../../specs/2026-10-07-trip-sharing-design.md#52-privacy-zones-saved-places-r5
[ts-9.3]: ../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli
[ui-12.1]: ../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-12.3]: ../../../specs/2026-10-06-ui-architecture-design.md#123-drive-mode-changes-31-35-53-54-10-u1-and-its-test
[ui-12.4]: ../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-12.5]: ../../../specs/2026-10-06-ui-architecture-design.md#125-visual-design-system-changes-2-principle-7
[ui-13.1]: ../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export
[ui-13.2]: ../../../specs/2026-10-06-ui-architecture-design.md#132-get-help-with-this-fault-diagnose-changes-34s-diagnose-row
[ui-13.3]: ../../../specs/2026-10-06-ui-architecture-design.md#133-ask-for-help-decoding-decode-lab-changes-84
[ui-13.4]: ../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order
[ui-13.5]: ../../../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence
[ui-14]: ../../../specs/2026-10-06-ui-architecture-design.md#14-amendment-2026-10-07-dmd-round-approved-message-alerts-amends-121-alert_card-and-the-u2-legal-check
[ui-15.1]: ../../../specs/2026-10-06-ui-architecture-design.md#151-drive-modes-changes-123
[ui-15.2]: ../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[ui-3.1]: ../../../specs/2026-10-06-ui-architecture-design.md#31-layout-classes
[ui-3.2]: ../../../specs/2026-10-06-ui-architecture-design.md#32-the-persistent-status-strip
[ui-3.3]: ../../../specs/2026-10-06-ui-architecture-design.md#33-driver-side-rail-versus-bottom-bar
[ui-3.4]: ../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-3.5]: ../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-3.7]: ../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-3.8]: ../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-4.1]: ../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-4.2]: ../../../specs/2026-10-06-ui-architecture-design.md#42-vehicle--systems--function-areas
[ui-4.3]: ../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-5.4]: ../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[ui-6]: ../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-7]: ../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-7.2]: ../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-8.4]: ../../../specs/2026-10-06-ui-architecture-design.md#84-decode-mode-in-the-ui
[vds-1]: ../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-10]: ../../../specs/2026-10-07-visual-design-system-design.md#10-before-and-after
[vds-11]: ../../../specs/2026-10-07-visual-design-system-design.md#11-migration-small-prs-approved-2026-10-07-all-before-u2-build-work
[vds-2]: ../../../specs/2026-10-07-visual-design-system-design.md#2-token-pipeline-fits-ui-spec-101
[vds-3]: ../../../specs/2026-10-07-visual-design-system-design.md#3-colour
[vds-3.1]: ../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-3.3]: ../../../specs/2026-10-07-visual-design-system-design.md#33-data-ramps-and-chart-colours-datatokensjson
[vds-4]: ../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-5]: ../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-6]: ../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[vds-7]: ../../../specs/2026-10-07-visual-design-system-design.md#7-maps
[vds-8]: ../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[vds-9]: ../../../specs/2026-10-07-visual-design-system-design.md#9-enforcement
[vm-2.1]: ../../../specs/2026-10-07-vehicles-and-map-addon-design.md#21-vehicles-list
[vm-2.2]: ../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle
[vm-3]: ../../../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles
[vm-4]: ../../../specs/2026-10-07-vehicles-and-map-addon-design.md#4-ghost-mode-and-the-visibility-sheet
[vm-5]: ../../../specs/2026-10-07-vehicles-and-map-addon-design.md#5-per-friend-group-and-field-sharing
[vm-7]: ../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving
