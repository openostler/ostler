---
title: "Designer brief — Ostler Community web: sign-in, search, my account, report, moderation, helper viewer and decode workbench"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-community-hub-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Page content for seven Ostler Community web pages that the approved hub spec describes but the
  screen index does not hold: hub sign-in and sign-up (email and passkey first, 16+), search with
  exact matching of fault codes and hex, my account (export everything, delete, linked devices,
  linked GitHub, notifications), the report sheet with statement of reasons and appeal, the
  moderation queue for staff and appointed moderators, the browser-side helper viewer that
  decrypts a help attachment, and the decode workbench (H2). Content, states and components.
---

# Ostler Community web, part d: new web pages

Example numbers and names in quotes are label formats, not data.

Shared rules: [60-apps-hub-a.md](60-apps-hub-a.md). These pages are web only (phone, tablet,
desktop; Night and Day) and have no driving states.

### hub-web-signin — Community web: sign in and sign up  [New]
- **Owner:** app:community
- **Purpose:** the hub's own account: email plus passkey first, password, optional TOTP.
- **Opens from → goes to:** "Sign in" anywhere; a device code link from hub-link-account →
  "Approve this car" → back to the page or "You can close this tab".
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night and Day; desktop Night.
- **Content (top to bottom):**
  1. "Sign in" Button with passkey; "Use a password"; "Sign in with Google" or "Apple" (hub
     site only).
  2. Sign up: email, handle, "I am 16 or over" tick; passkey creation; terms and privacy links.
  3. Device approval: "Enter the code shown in your car" (WXYZ-1234) → "Allow 'Sam' on this car
     to publish, read and post help?" **Allow** / **Deny**.
- **States:** wrong code: "That code didn't work" · locked after tries · email unverified ·
  under 16: account not created.
- **Safety and driving rules:** a hub account never signs anyone into a car ([Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking)).
- **Components:** Card, Button, ListRow.
- **Spec refs:** [Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking) · [Community §13](../../../../specs/2026-10-07-community-hub-design.md#13-privacy-law-age-and-licences) · [Accounts §15.5a](../../../../specs/2026-10-06-accounts-sharing-design.md#155a-hub-identity-is-hub-owned-one-ostler-account-later-approved-changes-148-later)

### hub-web-search — Community web: search  [New]
- **Owner:** app:community
- **Purpose:** one search over threads, decode cards, wiki pages, routes and events.
- **Opens from → goes to:** the top bar field → a result.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):** 1. Query ("P0403" or "21 1B"); exact-token matches first with a
  "Exact match" Chip. 2. Filters: make, model, engine, category, kind, Solved · Open, has
  attachment. 3. Result rows: kind icon, title, vehicle chips, solved Chip, snippet.
- **States:** no results: "Ask a question" Button · loading.
- **Safety and driving rules:** web page; no ranking by popularity beyond explicit sorts.
- **Components:** ListRow, Chip, Segmented, Button.
- **Spec refs:** [Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum) · [Community §15.1](../../../../specs/2026-10-07-community-hub-design.md#151-web-app-ostler-hub)

### hub-web-me — Community web: my account and data  [New]
- **Owner:** app:community
- **Purpose:** my profile settings, devices, notifications, export and deletion.
- **Opens from → goes to:** avatar menu → `/me/…` sections.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):**
  1. Profile: public profile Toggle (18+), display name, bio.
  2. Sign-in: passkeys, password, TOTP; linked Google or Apple; linked GitHub (scope shown,
     "Unlink").
  3. Linked cars: rows "Sam · on a car · last used 2 d", **Revoke**.
  4. Notifications: email immediate or daily digest, Web Push; watch defaults.
  5. **Export everything** ("One zip within 24 h"), **Delete my account** with the choice
     "keep my answers as [deleted user]" or "delete everything".
- **States:** export pending: "Preparing your export" · deleted: confirmation page.
- **Safety and driving rules:** deletion never touches the car's copy ([Community §13](../../../../specs/2026-10-07-community-hub-design.md#13-privacy-law-age-and-licences)).
- **Components:** ListRow, Toggle, Button, Card.
- **Spec refs:** [Community §5](../../../../specs/2026-10-07-community-hub-design.md#5-exit-guarantee-and-data-rights) · [Community §4](../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking) · [Community §13](../../../../specs/2026-10-07-community-hub-design.md#13-privacy-law-age-and-licences)

### hub-web-report — Community web: report  [New]
- **Owner:** app:community
- **Purpose:** report any object; see the decision and appeal it.
- **Opens from → goes to:** "…" → Report on any object; block and mute from the same menu.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Reason list (illegal content, harassment, privacy, wrong
  route warning…), text box, optional map pin for routes. 2. Send. 3. Later: decision with a
  **statement of reasons** and **Appeal**.
- **States:** sent: "Thanks. A moderator will look." · decided · appealed.
- **Safety and driving rules:** block hides items both ways ([Community §14](../../../../specs/2026-10-07-community-hub-design.md#14-moderation-and-abuse)).
- **Components:** Sheet, ListRow, Button.
- **Spec refs:** [Community §14](../../../../specs/2026-10-07-community-hub-design.md#14-moderation-and-abuse) · [Community §13](../../../../specs/2026-10-07-community-hub-design.md#13-privacy-law-age-and-licences)

### hub-web-mod-queue — Community web: moderation queue  [New]
- **Owner:** app:community
- **Purpose:** staff and appointed moderators review pending items, reports and wiki edits.
- **Opens from → goes to:** staff menu → an item → Approve, Reject (with reasons), Lock, Move,
  Merge, Split, Slow mode, Pin, Close.
- **Layout classes:** tablet · desktop. **Draw first:** desktop Night and Day.
- **Content (top to bottom):** 1. Tabs: Pending items · Reports · Wiki edits · Appeals.
  2. Rows: object, author (account age, approved count), reason. 3. Detail with the action
  bar; every decision asks for a statement of reasons.
- **States:** empty queue · conflict: "Another moderator is reviewing this".
- **Safety and driving rules:** trust is a flag, never shown as a score ([Community §14](../../../../specs/2026-10-07-community-hub-design.md#14-moderation-and-abuse)).
- **Components:** Segmented, ListRow, Button, Card.
- **Spec refs:** [Community §14](../../../../specs/2026-10-07-community-hub-design.md#14-moderation-and-abuse) · [Community §9](../../../../specs/2026-10-07-community-hub-design.md#9-the-forum)

### hub-web-helper-viewer — Community web: helper attachment viewer  [New]
- **Owner:** app:community
- **Purpose:** a named helper opens an L3 or L4 bundle in the browser, decrypted locally.
- **Opens from → goes to:** the helper's own link (key in the URL fragment) → P3 thread.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Header "L4 Diagnostics · Discovery 2 Td5 · 6 days left ·
  downloads 1 of 3". 2. Tabs: Signals (plot of RPM, Coolant, Turbo pressure on relative time),
  Faults and freeze frames ("P0403 EGR inlet throttle"), Modules (names, part and software
  numbers, no serials), Redactions ("VIN ×3", "Relative time", "No GPS"). 3. "Download"
  (only if allowed). 4. "Link a moment" to quote "00:12:31 on Engine.Speed" in the thread.
- **States:** check fails: "This file failed its checks and won't open" · expired · not named:
  403 page.
- **Safety and driving rules:** decrypted in the browser only; the hub holds ciphertext
  ([Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs), [Trip sharing §9.3](../../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli)).
- **Components:** Segmented, Card, Chip, Button, Area line chart.
- **Spec refs:** [Community §8](../../../../specs/2026-10-07-community-hub-design.md#8-help-threads-and-l3l4-hand-overs) · [Trip sharing §9.3](../../../../specs/2026-10-07-trip-sharing-design.md#93-ostler-share-verify-platform-library-and-cli) · [Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls)

### hub-web-workbench — Community web: decode workbench (H2)  [New]
- **Owner:** app:community
- **Purpose:** mark bytes, try a formula against the plot and save a decode card.
- **Opens from → goes to:** the helper viewer "Open workbench" → save → P13 decode card.
- **Layout classes:** tablet · desktop. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Frame list (mono hex, e.g. response "61 1B …"), byte
  selection. 2. Formula field ("(A*256+B)/100"), unit, range. 3. Live plot of the candidate
  against time. 4. "Save as decode card" (status `candidate`).
- **States:** formula error · no frames.
- **Safety and driving rules:** a card holds derived data only, never the log ([Community §10.2](../../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench)).
- **Components:** ListRow, Card, Button, Area line chart.
- **Spec refs:** [Community §10.2](../../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench)
