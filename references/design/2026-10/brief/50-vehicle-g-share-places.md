---
title: "Designer brief: vehicle and diagnostics (G) — trip sharing sheet, preview, history and Places"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-community-hub-design.md]
summary: >
  Seventh file of the vehicle and diagnostics brief. It gives full page content for the
  existing per-trip sharing screens and Places: the Trips share sheet (audience first, the
  five-level ladder L0 Card to L4 Diagnostics, options, expiry and link controls, send
  paths including Ask on Ostler Community and the help hand-over), the "What they will see"
  preview rendered from the real output with the redaction report and verifier result, the
  trip's share history with revoke, and Places (system Settings) with privacy zones, their radius and
  offset note, and the ends trim slider. It links the help flow for L3 and L4.
---

# Vehicle and diagnostics brief (G): sharing and Places

Levels ([Trip sharing §3][ts-3]): **L0 Card** · **L1 Route** · **L2 Telemetry** · **L3 Full
log** · **L4 Diagnostics**. L0–L2 are grants (revocable at once); L3–L4 are hand-overs to named
people only, and open through the help flow ([E](50-vehicle-e-help-adapters.md)).

### trips-share-sheet — Trips share sheet (audience, level ladder, options, expiry)  [Existing]
- **Purpose:** share one trip, or a marked range, at one level, to one audience, for one window.
- **Owner:** app:trips
- **Opens from → goes to:** trips-detail Share; a trip row "…"; a marked range in trips-playback → trips-share-preview, help-flow (Get help audience), places (Edit in Places), Vehicles & Map (Share live, for a trip still recording).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (full height), hu9 Night (side sheet), phone Day.
- **Content (top to bottom):**
  1. **Audience first:** Me · a contact · a group (a hub club is a group) · household · anyone with the link · publish to Ostler Community · get help. Levels the audience cannot take are greyed with the reason ("Full logs go to named people only", "Telemetry is never public").
  2. **Level ladder:** five stacked rows L0 at the top, L0 preselected from Trips; each with chips for what it adds (map, chart, raw, wrench) and its plain line, e.g. L1 "The card plus your route on a map. The first and last 500 m and your private places are hidden. No times on the route." L3 and L4 rows in the warning token.
  3. **Options:** signal picker (L2; default Speed, RPM, Coolant); include the route (L2–L4; refused for public); shareable notes; plate; show max speed (off for link and public); keep real date and time (L3–L4, one named person only).
  4. **Preview** (fills the sheet; see trips-share-preview).
  5. **Expiry:** 1 h · end of day · 7 days · 30 days · until I stop (where allowed); **More options**: Locked or Download, available from, access until, number of people, downloads each; state Chip (Pending, Active, Full, Expired, Revoked) with countdown.
  6. Privacy line: "Hidden: first and last 500 m, 2 private places · Edit in Places".
  7. **Send** names the path: Share · Copy link · Save file · Send to helper · **Ask on Ostler Community** (only with the hub add-on linked). File and public paths add "This can't be taken back once sent" in the warning token.
  8. A trip still recording offers only **Share live** (hands over to Vehicles & Map).
- **States:** short trip (visible trace under 1 km): only L0, card reads "under 1 km". No GPS: L1 greyed "No location in this trip". Offline: link and hub paths wait; file works. Idling without Park evidence and Moving: locked view (a phone may share any time).
- **Safety and driving rules:** Parked only on a driver-facing display ([UI §13.1][ui-13.1]); ghost does not hide past-trip shares, and the sheet says so ([Trip sharing §11][ts-11]).
- **Components:** Sheet, ListRow (ladder), Chip, Segmented, Toggle (new component), Button.
- **Spec refs:** [UI §13.1][ui-13.1] · [Trip sharing §3][ts-3] · [Trip sharing §10][ts-10] · [Accounts §15.4][acc-15.4] · [Community §15.2][hub-15.2].

### trips-share-preview — "What they will see" preview and redaction report  [Existing]
- **Purpose:** show the recipient's exact view, rendered from the produced output.
- **Owner:** app:trips
- **Opens from → goes to:** trips-share-sheet (step 4) → Send, or back to change options.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (L1 with dashed fade ends), desktop Night (L3 hex view).
- **Content (top to bottom):**
  1. The map in the map theme; hidden ends drawn as a **dashed fade to `bg`, never a circle**; segments split at zones with no line across the gap.
  2. The recipient's stats, computed from the visible trace only and rounded per level (L0: distance 1 km, duration 5 min).
  3. L3–L4: **redaction report** Chips ("VIN ×3", "Ends 500 m", "2 zones", "Relative time", "No GPS", "2 notes left out"); a tap explains the rule.
  4. L3–L4: hex before and after of each scrubbed frame (owner's device only, mono, scrubbed bytes muted).
  5. Verifier result: "Checked: passes".
- **States:** verifier fail: Send replaced by the rule that failed and what to do next. Building: "Preparing…". Moving: locked.
- **Safety and driving rules:** preview is the bundle, not an imitation ([Trip sharing §11][ts-11], [§9.3][ts-9.3]).
- **Components:** Sheet, Chip row, Card, Area line (L2 charts).
- **Spec refs:** [UI §13.1][ui-13.1] · [Trip sharing §11][ts-11] · [Trip sharing §9.3][ts-9.3] · [Trip sharing §5.4][ts-5.4].

### trips-share-history — Trip share history and revoke  [Existing]
- **Purpose:** every share of this trip, and one-tap revoke.
- **Owner:** app:trips
- **Opens from → goes to:** a trip row "Shared 2× · 1 active"; Settings → Sharing (S8) → trips-share-sheet (Share again).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Rows: level Chip, audience, path (grant, relay link, file, hub thread, pack issue), created, opens, downloads, state Chip with countdown. 2. **Revoke** on grants, links and threads; file and pack-issue rows say "Cannot be revoked" in the warning token. 3. Audit line per pull for grants (time, peer, class).
- **States:** none shared: "Not shared". Moving: locked.
- **Safety and driving rules:** a revoked relay or hub object is deleted at once ([Trip sharing §11][ts-11]).
- **Components:** ListRow, Chip (state), Button (Revoke, danger).
- **Spec refs:** [UI §13.1][ui-13.1] · [Trip sharing §11][ts-11].

### places — Places (privacy zones, ends trim)  [Existing]
- **Purpose:** the owner's private places and the trim that hide trip ends in every share.
- **Owner:** os
- **Opens from → goes to:** system Settings → Places (formerly More → Places); the share sheet's "Edit in Places" → a place editor sheet (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night, phone Day.
- **Content (top to bottom):**
  1. Map (owner's own) with each zone drawn at its **offset centre** and a plain note: "Your place is somewhere inside this circle, not at its centre. Sharing many routes near one place still narrows it down."
  2. **Privacy zones** list: Home, Work, others; each with radius Segmented **500 m · 1 km · 1.5 km · 2 km** (Home defaults to 1 km); **Add place**.
  3. **Ends trim** slider 200 m to 1.5 km, default 500 m, floor 200 m: "Hides the first and last part of every shared trip".
  4. Used by: Trips, Social, Vehicles & Map, Ostler Community.
- **States:** moving a place by more than its radius: "A new offset will be drawn." Empty: "No private places yet. Add Home to hide it in every share." Offline: map fallback `bg`. Idling without Park evidence and Moving: locked view.
- **Safety and driving rules:** location stays on the device unless shared (ADR-0009); the offset is never re-rolled ([Trip sharing §5.2][ts-5.2]).
- **Components:** Sheet over map, ListRow, Segmented (radius), Slider (new component), Button.
- **Spec refs:** [UI §13.4][ui-13.4] · [Trip sharing §5.1][ts-5.1] · [Trip sharing §5.2][ts-5.2].

[ui-13.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export
[ui-13.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order
[ts-3]: ../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels
[ts-5.1]: ../../../../specs/2026-10-07-trip-sharing-design.md#51-ends-trim-every-trip-r5
[ts-5.2]: ../../../../specs/2026-10-07-trip-sharing-design.md#52-privacy-zones-saved-places-r5
[ts-5.4]: ../../../../specs/2026-10-07-trip-sharing-design.md#54-stats-from-the-visible-trace-only-r6
[ts-9.3]: ../../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli
[ts-10]: ../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls
[ts-11]: ../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit
[hub-15.2]: ../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub
[acc-15.4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412
