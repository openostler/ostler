---
title: "Designer brief — Ostler Community web: P8 Publish to P14 Wiki page"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-community-hub-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Page content for Ostler Community web pages P8 to P14: the four-step publish flow (choose,
  level, audience and time, a preview rendered from the scrubbed bundle, with the public
  checklist and review until trusted), My shares with revoke, the forum category list grouped by
  make and model, a thread with its accepted answer and watch level, a vehicle project with its
  status stepper and GitHub pull-request state, a decode card with evidence and fixture snippets,
  and a wiki page with generated pack sections and community sections. States, rules and
  components per page.
---

# Ostler Community web, part b: P8–P14

Example numbers and names in quotes are label formats, not data.

Shared rules: see part a, [60-apps-hub-a.md](60-apps-hub-a.md). Real examples come from the
Discovery 2 pack: Td5 fault "P0403 EGR inlet throttle", SLABS fault "right front wheel speed
sensor, output too low", signals RPM, Coolant, Turbo pressure, Height left (raw).

**Publish (flow, P8).**

| Step | What the user does | Can fail · recovery |
|---|---|---|
| 1 Choose | picks a trip, route, garage card or event | nothing publishable: "Share a trip from Trips first" |
| 2 Level | L0 Card or L1 Route (L2 only to a club) | level not allowed for the audience: greyed with the reason |
| 3 Audience and time | club, `link` or `public`; expiry; Allow download (off); Show in Discover (off) | public route < 24 h after the trip: "Publish after 18:00 tomorrow" |
| 4 Preview | sees the page rendered from the scrubbed bundle | verifier fails: the rule and what to do; no Publish |
| Publish | item goes Private → Pending review → Public (until trusted) | review rejects: statement of reasons and Appeal |

### hub-web-p8 — Community web: P8 Publish  [Existing]
- **Owner:** app:community
- **Purpose:** publish an item at a chosen level, audience and time.
- **Opens from → goes to:** "Publish" on the web, or the Trips share sheet "Publish to Ostler
  Community" → P2 or P9.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night (step 4); phone
  Night (each step).
- **Content (top to bottom):** 1. Stepper "1 Choose · 2 Level · 3 Audience and time · 4
  Preview". 2. Level rows with plain lines (as trips-share-sheet). 3. Public checklist inline:
  title, description ≥ 50 characters, region, vehicle, licence (CC BY-SA 4.0 default for
  routes). 4. Switches: Allow download (off), Show in Discover and search engines (off for
  routes from home regions). 5. Preview. 6. Publish (primary).
- **States:** pending review: "Waiting for review" Chip · rejected: reasons + Appeal · verifier
  fail: rule named, Publish replaced.
- **Safety and driving rules:** publishing is a grant, never a sync; the hub rejects rather
  than repairs ([Community §6](../../../../specs/2026-10-07-community-hub-design.md#6-what-can-be-published), [Community §7](../../../../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls)).
- **Components:** Stepper (new component), ListRow, Toggle, Card, Button, Chip.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §6](../../../../specs/2026-10-07-community-hub-design.md#6-what-can-be-published) · [Community §7](../../../../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls)

### hub-web-p9 — Community web: P9 My shares  [Existing]
- **Owner:** app:community
- **Purpose:** everything I published or linked, with state and revoke.
- **Opens from → goes to:** `/me/shares`, Settings → Sharing in the car → a row → item; New link.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):** 1. Rows: level Chip, audience Chip, state Chip (Pending ·
  Active · Full · Expired · Revoked), expiry countdown, views, downloads. 2. **Revoke** (two
  taps). 3. **New link**. 4. "Make private now" (one tap).
- **States:** empty: "Nothing published" · revoked row greyed.
- **Safety and driving rules:** revoke deletes stored copies at once ([Community §7](../../../../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls)).
- **Components:** ListRow, Chip, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §7](../../../../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls)

### hub-web-p10 — Community web: P10 Forum  [Existing]
- **Owner:** app:community
- **Purpose:** the category list, grouped by make, with model sub-rows.
- **Opens from → goes to:** top bar "Forum" → a category → thread list → P11.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):** 1. Vehicle switcher pinned to my garage's makes. 2. Make groups
  ("Land Rover") with model rows ("Discovery 2 · tags td5, v8, 1998–2004"), unread counts, "4
  open questions". 3. General categories: Announcements, Getting started, Hardware, Platform and
  add-ons, Pack development, Routes and trips, Clubs and events, Site feedback. 4. "Not yet
  supported" per make. 5. "New thread".
- **States:** signed out: read only · empty category: "Be the first to ask".
- **Safety and driving rules:** no direct messages anywhere ([Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)).
- **Components:** ListRow, Chip, Card, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)

### hub-web-p11 — Community web: P11 Thread  [Existing]
- **Owner:** app:community
- **Purpose:** read and reply to a thread; mark solved.
- **Opens from → goes to:** P10, search, notifications → reply composer; Report.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night and Day.
- **Content (top to bottom):** 1. Title, kind Chip (Discussion · Question · Help · Pack
  proposal), solved Chip, vehicle chips. 2. Accepted answer under the question, "Solved by
  @ali". 3. Posts as ListRows with quote and reply; code blocks for hex ("21 1B"). 4. Watch
  level Segmented Watching · Tracking · Normal · Muted. 5. **Mark as solved** (asker). 6.
  Composer (Markdown, code blocks, @mentions; no images before H4).
- **States:** pending first post: "Waiting for review" · locked: "Closed by a moderator" ·
  signed out: "Sign in to reply".
- **Safety and driving rules:** private "thanks" only; no votes ([Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)).
- **Components:** ListRow, Chip (kind, solved, status, vehicle), Card, Button, Segmented.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)

### hub-web-p12 — Community web: P12 Vehicle project  [Existing]
- **Owner:** app:community
- **Purpose:** the visible path from captures to a released pack for one vehicle.
- **Opens from → goes to:** wiki vehicle page, forum, decode cards → GitHub PR links.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):** 1. Status Stepper Wanted → Capturing → Decoding → Pack draft →
  PR open → Released. 2. Target pack repo ("ostler-pack-lr-d2"). 3. Decode cards table with
  status chips (`candidate`, `proven`). 4. "Still needed" list ("a capture of the ABS module at
  idle"). 5. Open threads. 6. PR links with GitHub state (opened, changes requested, merged).
  7. People who helped, by chosen credit.
- **States:** no project: "Propose a pack" · released: "Released in 0.9".
- **Safety and driving rules:** the pack repo decides; the hub proposes ([Community §10.1](../../../../specs/2026-10-07-community-hub-design.md#101-the-path)).
- **Components:** Stepper, ListRow, Chip, Card, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §10.3](../../../../specs/2026-10-07-community-hub-design.md#103-vehicle-projects) · [Community §10.1](../../../../specs/2026-10-07-community-hub-design.md#101-the-path)

### hub-web-p13 — Community web: P13 Decode card  [Existing]
- **Owner:** app:community
- **Purpose:** a structured, public decode proposal with evidence.
- **Opens from → goes to:** a thread, a project → "Propose to pack" (trusted) → P12.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):** 1. Fields: signal ("fuel_temp", VSS path), module and protocol
  ("Td5 ECU · KWP2000 over K-line"), request and response bytes (mono), byte positions,
  formula, unit, range, expected values. 2. Status Chip `candidate`. 3. Evidence links to
  thread moments. 4. Fixture snippets (mono). 5. Licence line "CC BY-SA 4.0". 6. **Propose to
  pack**.
- **States:** verifier fail: "Fixture failed: …" · merged: "Decoded in ostler-pack-lr-d2 0.9".
- **Safety and driving rules:** a card never holds a log ([Community §10.2](../../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench)).
- **Components:** Card, ListRow, Chip, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §10.2](../../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench) · [Community §10.4](../../../../specs/2026-10-07-community-hub-design.md#104-the-github-bridge)

### hub-web-p14 — Community web: P14 Wiki page  [Existing]
- **Owner:** app:community
- **Purpose:** a vehicle page generated from pack releases plus community sections.
- **Opens from → goes to:** Discover, search, app drawer → Community Wiki links → Suggest a change
  (decode card or PR), Edit, History.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):** 1. Band "From ostler-pack-lr-d2 v0.9". 2. Generated sections:
  modules and protocols, signals with `proven`/`candidate`, fault codes with meaning and
  confidence, service schedules, supported features, required hardware. 3. "Suggest a change".
  4. Community sections with Edit and History. 5. Side column: forum category, open threads,
  project status.
- **States:** pending edit: "Your edit is waiting for review" · no page: "Not yet supported".
- **Safety and driving rules:** generated sections read-only ([Community §11](../../../../specs/2026-10-07-community-hub-design.md#11-the-wiki)).
- **Components:** ListRow, Chip, Card, Button.
- **Spec refs:** [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub) · [Community §11](../../../../specs/2026-10-07-community-hub-design.md#11-the-wiki)
