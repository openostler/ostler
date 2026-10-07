---
title: "Designer brief — Trip sharing: share sheet with levels L0–L4, preview, history, audiences and link controls"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-community-hub-design.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md]
summary: >
  Page content for sharing one trip: the indexed Trips share sheet (audience first, the five
  level rows L0 Card, L1 Route, L2 Telemetry, L3 Full log and L4 Diagnostics, options, expiry and
  the named send paths), the "What they will see" preview with the redaction report and verifier
  fail, and the share history with revoke; plus two new OS sheets used by every app that shares:
  the audience picker (me, person, group, household, link, public, with what each tier may
  carry) and the link controls (Locked or Download, available from, access until, limits,
  states). States, driving rules and components.
---

# Sharing, part a: trip shares, audiences and link controls

Example numbers and names in quotes are label formats, not data.

The Trips app owns the trip and its share sheet; the OS owns grants, audiences, ghost, link
controls and the audit ([Trip sharing §14](../../../../specs/2026-10-07-trip-sharing-design.md#14-where-each-piece-lives), [Accounts §14](../../../../specs/2026-10-06-accounts-sharing-design.md#14-amendment-2026-10-07-approved-one-permission-model-and-the-shell-screens)). **L0–L2 are grants** (live, revocable,
audited). **L3–L4 are hand-overs**, never grants: a scrubbed, verified bundle sent once to named
people ([Trip sharing §3](../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels), [ADR-0043](../../../../decisions/adr-0043-gps-and-logs-in-shared-trips.md)). Part b: [60-apps-share-b.md](60-apps-share-b.md).

**Permission tiers at a glance** (what each audience may ever receive; [Accounts §15.2](../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142)):

| Audience | May carry | Never |
|---|---|---|
| Me | everything | — |
| Person (a friend) | L0–L2, live location ≤ 24 h, card, faults; L3–L4 by hand-over | — |
| Group or ride (a hub club is a group) | L0–L2; live location for the ride only | L3–L4 as a grant |
| Household | as Person | — |
| Link (anyone with the URL) | L0–L1, faults, vehicle card; always an expiry | L2, live, presence, audio, video, raw logs |
| Public (Ostler Community, explicit publish only) | L0–L1 (route ≥ 24 h after the trip), vehicle card | L2–L4, live, audio, video |

### trips-share-sheet — Trips share sheet  [Existing]
- **Owner:** app:trips
- **Purpose:** share one trip, or a marked range, at a chosen level, to one audience, for a time.
- **Opens from → goes to:** trip detail share button, a trip row "…", a marked range in
  playback, Diagnose "Get help" (L4), Decode lab "Ask for help decoding" (L3) →
  trips-share-preview → sent → trips-share-history.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day (full height); hu7 Night Parked; hu7 Night-dim Moving (locked frame).
- **Content (top to bottom):**
  1. **Audience first** (share-audience-picker row): Me · a contact · a group · household ·
     anyone with the link · publish to Ostler Community · get help (named helpers, a pack's
     maintainers). Levels the audience cannot take are greyed with the reason ("Full logs go
     to named people only", "Telemetry is never public").
  2. **Level ladder**, five stacked rows with chips (map, chart, raw, wrench) and one line:
     - L0 Card: "A card with the day, the area, distance and time. No map."
     - L1 Route: "The card plus your route on a map. The first and last 500 m and your
       private places are hidden. No times on the route."
     - L2 Telemetry: "Chosen readings (speed, revs, temperatures…) as charts, with times
       counted from the start. No map unless you add the route."
     - L3 Full log: "Everything the car's computers said on this trip, so someone can help
       decode it. Your VIN and serial numbers are removed. Goes to named people only."
     - L4 Diagnostics: "Fault codes, freeze frames and module information, so someone can
       help find a fault. Goes to named people only."
     L3 and L4 rows use the warning token. Default: L0 from Trips, L4 from Diagnose, L3 from
     Decode lab.
  3. Options for the level: signal picker (L2; default Speed, RPM, Coolant; e.g. add Turbo
     pressure); Include the route (L2–L4; refused for public); shareable notes; plate; Show max
     speed (off for link and public); Keep real date and time (L3–L4, one named person, naming
     them).
  4. Durations: 1 h · End of day · 7 days · 30 days · Until I stop (where allowed); "More
     options" → share-link-controls.
  5. Privacy line: "Hidden: first and last 500 m, 2 private places · Edit in Places".
  6. Send Button naming the path: Share · Copy link · Save file · Send to helper · Ask on Ostler
     Community (only with the Community app linked).
  7. File and pack-issue paths: "This can't be taken back once sent" in the warning token.
- **States:** trip still recording: only "Share live" (→ vehicles-share live options) · trip
  under 1 km: L0 only, "under 1 km" · no GPS (K-line only): L0 duration only, no map · offline:
  Save file works; links wait · Parked: full; phone any time · Idling: with Park evidence ·
  Moving: locked view "Available when parked" + Open on phone.
- **Safety and driving rules:** Parked only on a driver-facing display ([UI §13.1](../../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export)); ghost
  does not hide past-trip grants and the sheet says so ([Trip sharing §11](../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit)).
- **Components:** Sheet, ListRow (L0–L4 with chips), Chip (countdown), Segmented (durations),
  Button.
- **Spec refs:** [UI §13.1](../../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export) · [Trip sharing §3](../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels) · [Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls) · [Accounts §15.2](../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142) · [Accounts §15.4](../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412) · [Community §15.2](../../../../specs/2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub)

### trips-share-preview — "What they will see" and redaction report  [Existing]
- **Owner:** app:trips
- **Purpose:** show the exact output the recipient gets, rendered by the same filter.
- **Opens from → goes to:** the share sheet's preview area → Send or back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night (L1 map); phone Night (L4 redaction report); desktop Night (hex before and after).
- **Content (top to bottom):**
  1. L1+: map in the map theme; hidden ends as a **dashed fade to `bg`**, never a circle.
  2. The recipient's stats (rounded as they will see them, e.g. "84 km · 1 h 35 min").
  3. L3–L4 redaction report Chip row: "VIN ×3", "Ends 500 m", "2 zones", "Relative time", "No
     GPS", "2 notes left out"; tapping a Chip explains the rule.
  4. Owner-only hex view of scrubbed frames, before and after, mono face, scrubbed bytes muted.
  5. Verifier fail: Send replaced by "Blocked: a VIN-like pattern in tap/bus1, frame 2,341.
     Ask the pack maintainers to declare this frame." No "send anyway".
- **States:** loading: "Building the share…" · fail · Parked: full · Moving: locked view.
- **Safety and driving rules:** preview is the bundle, not an imitation ([Trip sharing §11](../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit), [Trip sharing §9.3](../../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli)).
- **Components:** Sheet, Chip row (redaction report), Card.
- **Spec refs:** [UI §13.1](../../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export) · [Trip sharing §11](../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit) · [Trip sharing §9.3](../../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli)

### trips-share-history — Share history and revoke  [Existing]
- **Owner:** app:trips
- **Purpose:** every share of one trip with state, opens and revoke.
- **Opens from → goes to:** trip row "…" "Shared 2× · 1 active" → revoke; Settings → Sharing
  (accounts-s8) for all shares.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked.
- **Content (top to bottom):** 1. Rows: level Chip, audience, path (Grant · Relay link · File ·
  Help thread · Pack issue), created day, opens, downloads, state Chip (Pending · Active · Full
  · Expired · Revoked). 2. **Revoke** per row (one tap; files and pack issues say "cannot be
  revoked").
- **States:** empty: "Not shared" · Parked: full · Idling: with Park evidence · Moving: locked.
- **Safety and driving rules:** revoke deletes relay and hub copies at once ([Trip sharing §11](../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit)).
- **Components:** ListRow, Chip (state), Button (Revoke).
- **Spec refs:** [UI §13.1](../../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export) · [Trip sharing §11](../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit)

### share-audience-picker — Who to share with  [New]
- **Owner:** os
- **Purpose:** the one audience picker used by every app's share sheet, with the tier rules.
- **Opens from → goes to:** trips-share-sheet, vehicles-share, accounts-s8 "Add a grant", hub
  publish → back with the audience.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):**
  1. Rows with icon and word: Only me (`lock`) · A person (`person`) · A group or ride
     (`group`) · Household (`home`) · Anyone with the link (`link`) · Publish publicly
     (`public`, only via Ostler Community).
  2. Each row's one line from the tier table above ("Links always expire").
  3. For what is being shared, rows that cannot take it are greyed with the reason.
  4. Person and group open a list of contacts and groups; "Invite someone".
- **States:** no contacts: "Invite someone" · Community app absent: Public row hidden ·
  Moving: locked view.
- **Safety and driving rules:** the default audience is always Me; public needs an explicit
  publish act ([Accounts §15.2](../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142)).
- **Components:** Sheet, ListRow, Button.
- **Spec refs:** [Accounts §14.2](../../../../specs/2026-10-06-accounts-sharing-design.md#142-audiences-and-grants) · [Accounts §15.2](../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142) · [Trip sharing §3](../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels)

### share-link-controls — Link controls (More options)  [New]
- **Owner:** os
- **Purpose:** the DMD-style controls on any grant to a person, group or link.
- **Opens from → goes to:** "More options" in any share sheet → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; desktop Night.
- **Content (top to bottom):**
  1. Mode Segmented **Locked · Download**, with "Locked stops casual copies. Anyone who can see
     data can still copy it." and "Download copies survive revoke."
  2. Available from (date and time). 3. Link expiry (last time a new person may open it).
  4. Access until (Locked only). 5. Number of people (collection limit). 6. Downloads each.
  7. State preview Chip: "Pending until Sat 09:00" / "Active · 6 d".
- **States:** invalid (access until before available from): inline error · Moving: locked.
- **Safety and driving rules:** every link has an expiry ([Accounts §15.4](../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412)).
- **Components:** Sheet, Segmented, ListRow, Chip (state).
- **Spec refs:** [Accounts §15.4](../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412) · [Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls)
