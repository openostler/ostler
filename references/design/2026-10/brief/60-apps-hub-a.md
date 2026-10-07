---
title: "Designer brief — Ostler Community web: P1 Discover to P7 Profile"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-community-hub-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Page content for the first seven Ostler Community web pages (the closed, Ostler-run hub at one
  domain, readable in any browser): P1 Discover with make, model, engine and year filters and no
  people feed, P2 a shared trip at the level granted (L0 card with no map, L1 route, L2
  telemetry tabs), P3 a help thread with its time-boxed encrypted attachment and named helpers,
  P4 a group or club, P5 a live ride page (at most 24 h, positions never stored), P6 an event and
  P7 a profile with no map of the person's places. States, rules and components per page.
---

# Ostler Community web, part a: P1–P7

Example numbers and names in quotes are label formats, not data.

Ostler Community is one closed service run by Ostler (`ostler-hub`), reached in any browser
and, in the car, through the open add-on `ostler-app-hub` ([Community §3](../../../../specs/2026-10-07-community-hub-design.md#3-repos-licences-and-stack)). Web pages have no
driving states; they follow the visual system: dark by default, Day equal, Ostler Night maps,
one accent, Material Symbols, no social-network buttons, no third-party scripts ([Community §15](../../../../specs/2026-10-07-community-hub-design.md#15-screens)).
Every object its owner sees carries the visibility chip (`lock` Only me · `group` Peak 4x4 ·
`link` Link · 6 d · `public` Public). Sign-in walls: public pages readable signed out; `link`
needs only the link; club content and help attachments need a member or named helper.
Parts b–d: [hub-b](60-apps-hub-b.md), [hub-c](60-apps-hub-c.md), [hub-d](60-apps-hub-d.md).

### hub-web-p1 — Community web: P1 Discover  [Existing]
- **Owner:** app:community
- **Purpose:** the directory of public items, threads, wiki pages and clubs; no people feed.
- **Opens from → goes to:** `/` → any card (P2 trip, route, P6 event, P11 thread, P4 club, P14
  wiki); "Sign in" → hub-web-signin; search → hub-web-search.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night and Day.
- **Content (top to bottom):**
  1. Top bar: Ostler Community wordmark (our name), search field, "Forum", "Wiki", "Sign in".
  2. Chips: Routes · Trips · Events · Help wanted · Threads · Clubs.
  3. Filters: Make → Model → Engine → Year (e.g. Land Rover · Discovery 2 · Td5 · 1998–2004),
     region, vehicle type, "has faults", "has telemetry"; sort Segmented Newest · Nearest
     (coarse) · Most useful.
  4. Card grid: static Ostler Night thumbnail, title, kind chip, vehicle chips, distance,
     region label ("Derbyshire").
  5. Side column: "Help wanted on your vehicles", "Upcoming near you" (coarse region).
- **States:** empty filter: "Nothing yet for Discovery 2 Td5 · Ask on the forum" · loading:
  skeleton cards · error: "Couldn't load · Retry" · signed out: full public content · offline
  (browser): the browser's own page.
- **Safety and driving rules:** web page; no ranking algorithm, no points or leaderboards
  ([Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments), [Community §1](../../../../specs/2026-10-07-community-hub-design.md#1-purpose-and-non-goals)).
- **Components:** Card, ListRow, Chip, Segmented, Sheet over map (thumbnail), HeroStat.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)

### hub-web-p2 — Community web: P2 Shared trip  [Existing]
- **Owner:** app:community
- **Purpose:** show a shared trip at exactly the level granted.
- **Opens from → goes to:** a link, Discover, a profile or a club → back; "Download" when
  allowed; Report → hub-web-report.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night (L1 with side
  sheet); phone Night (L1 bottom sheet); phone Night (L0 card, no map).
- **Content (top to bottom):**
  1. Full-bleed map (L1+): trace in `series-1` with casing; hidden ends as a dashed fade to
     `bg`, never a circle; speed ramp only if the owner granted `show_speed`.
  2. Title card: title, day only ("Tue 6 Oct"), level Chip (L0 Card · L1 Route · L2
     Telemetry), audience Chip.
  3. Side sheet 420 px (bottom sheet on phone): HeroStat distance "84.2 km", stat strip
     (duration, moving time, average speed; max speed absent on public cards), elevation
     profile with its source.
  4. Tabs, only for the level granted: Overview (L0+), Signals (L2: e.g. RPM, Coolant, Turbo
     pressure on relative time), Faults (L2 with faults, e.g. "P0403 EGR inlet throttle").
  5. Vehicle line: "Land Rover Discovery 2 · Td5 · 2002"; never a VIN or plate unless ticked.
  6. Comments (off by default).
- **States:** L0: card only, no map, "under 1 km" when short · expired or revoked: "This share
  has ended" · loading · not allowed: "Ask the owner for access".
- **Safety and driving rules:** stats from the visible trace only; no point times
  ([Trip sharing §3](../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels), [Trip sharing §5](../../../../specs/2026-10-07-trip-sharing-design.md#5-trimming-privacy-zones-and-stats)).
- **Components:** Sheet over map, HeroStat, StatTile, Segmented (tabs), Chip, Card.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §6](../../../../specs/2026-10-07-community-hub-design.md#6-what-can-be-published) · [Trip sharing §3](../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels)

### hub-web-p3 — Community web: P3 Help thread  [Existing]
- **Owner:** app:community
- **Purpose:** a forum thread of kind Help with an encrypted log or diagnostics attachment.
- **Opens from → goes to:** hub-help-compose (posted from the car), the forum, a notification
  → hub-web-helper-viewer (named helpers), "Name a helper" (owner).
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):**
  1. Everything in P11 (title, kind "Help", solved chip, vehicle chips "Discovery 2 · Td5 ·
     pack lr_d2 0.9").
  2. Attachment Chip: "L4 Diagnostics · time-boxed access: 6 days left · downloads 1 of 3".
  3. Helper list: names, "opened", "downloaded"; owner sees **Name a helper** and Revoke.
  4. Requests from helpers ("Can you share the SLABS module too?") shown as a line; answered on
     the owner's device.
- **States:** attachment expired: "attachment expired", text stays · not a named helper:
  attachment hidden, "Only named helpers can open this" · solved: "Solved by @ali".
- **Safety and driving rules:** the hub stores ciphertext only; helpers never send actions to
  the car ([Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs)).
- **Components:** ListRow, Chip (kind, solved, status, vehicle, countdown), Card, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs) · [Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)

### hub-web-p4 — Community web: P4 Group or club  [Existing]
- **Owner:** app:community
- **Purpose:** a club's home: forum category, rides, routes, events, members and files.
- **Opens from → goes to:** Discover, a link, a code → tabs; "Join with code".
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):** 1. Name, kind Chip (Club), member count, "Join with code" or
  "Request to join". 2. Tabs: Forum · Rides · Routes · Events · Members · Files. 3. Map of
  shared routes (never members' homes). 4. About text.
- **States:** not a member: public face only · pending approval · empty tabs: "No events yet".
- **Safety and driving rules:** members list only to members ([Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)).
- **Components:** Card, ListRow, Chip, Segmented (tabs), Sheet over map.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)

### hub-web-p5 — Community web: P5 Live ride  [Existing]
- **Owner:** app:community
- **Purpose:** the web face of a live ride, ride-scoped, at most 24 h (H3).
- **Opens from → goes to:** the ride's link, Discover "Live now" (opt-in listing) → "This ride
  has ended".
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):** 1. Full-bleed map. 2. One title pill "Live · 4 riding · ends
  18:00" (`fiber_manual_record` icon, not a glyph). 3. Member pucks (accent for me), Leader and
  Sweep badges, delay badge "Delayed 15 min". 4. No viewer chat.
- **States:** ended: "This ride has ended" and no positions · ghosted rider: disappears ·
  under 18 or not listed: not in Discover.
- **Safety and driving rules:** positions in memory only, never stored ([Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)).
- **Components:** Sheet over map, Chip, Card.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments) · [Vehicles & Map §8](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#8-viewers-without-ostler-later)

### hub-web-p6 — Community web: P6 Event  [Existing]
- **Owner:** app:community
- **Purpose:** an event page with going status and files.
- **Opens from → goes to:** Discover, club Events, a link → "Add to calendar" (ICS).
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):** 1. Title Card. 2. When & where: dates in the event's zone,
  "Add to calendar", "Copy coordinates". 3. Segmented Going · Maybe · Not going; capacity
  "18 of 30". 4. Files "locked until start". 5. Payment info as text only. 6. Comments.
- **States:** full: "Event full" · past: "This event has ended" · signed out: Sign in to reply.
- **Safety and driving rules:** web page; no money handled ([Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)).
- **Components:** Card, Segmented, ListRow, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)

### hub-web-p7 — Community web: P7 Profile  [Existing]
- **Owner:** app:community
- **Purpose:** a person's public face (18+, opt-in).
- **Opens from → goes to:** a handle anywhere → their public routes, trips, garage cards.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):** 1. Avatar, display name, handle, bio. 2. Garage row of cards.
  3. Public routes and trips. 4. Linked GitHub (if shown). 5. Counts "helped with 12 decodes",
  "completed 3 routes". **No map of the person's places.** 6. Report and Block in "…".
- **States:** private profile: "This profile is private" · blocked: not visible.
- **Safety and driving rules:** no scores; counts only ([Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)).
- **Components:** Card, ListRow, Chip, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §12](../../../../specs/2026-10-07-community-hub-design.md#12-discover-following-clubs-events-live-rides-comments)
