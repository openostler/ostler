---
title: "Designer brief — Accounts S6–S10: devices, contacts and invites, sharing with View as…, ghost toggle, safety contacts"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Page content for OS account screens S6 to S10: signed-in devices and tokens with revoke,
  contacts, groups and invites (QR, link and an 8-character code with a six-digit key check),
  Sharing ("who sees what") as a matrix of audiences by data classes with presets, the audit
  and View as…, the ghost toggle (visibility chip and sheet; ghost by default, timers only
  toward ghost) and safety contacts with a test button. States, driving rules and components.
---

# Accounts, part b: S6–S10

Example numbers and names in quotes are label formats, not data.

Part a: [60-apps-accounts-a.md](60-apps-accounts-a.md). Sharing sheets used across add-ons are
in [60-apps-share-a.md](60-apps-share-a.md) and [60-apps-share-b.md](60-apps-share-b.md).

### accounts-s6 — Accounts S6: signed-in devices  [Existing]
- **Owner:** os
- **Purpose:** every session and token, with revoke.
- **Opens from → goes to:** account menu → Devices → revoke.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):** 1. Rows: device label ("Head unit", "Sam's Pixel"), last used,
  last path Chip (Head unit · LAN · Tailscale · Relay), "This device". 2. Tokens: name, scopes
  in words, expiry, last used. 3. **Sign out everywhere else**. 4. Caption: "Unused for 90 days:
  signed out automatically."
- **States:** owner sees all users' sessions · empty tokens.
- **Safety and driving rules:** revoke is immediate ([Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs)).
- **Components:** ListRow, Button, Sheet, Chip.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §2.4](../../../../specs/2026-10-06-accounts-sharing-design.md#24-tokens)

### accounts-s7 — Accounts S7: contacts, groups and invites  [Existing]
- **Owner:** os
- **Purpose:** friends, groups (friends, club, safety) and invites in and out.
- **Opens from → goes to:** Settings → Contacts; Social "Invite someone" → Add (QR, link, code) or
  Enter code → share-invite-code → share-invite-accept.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night and Day; desktop Night.
- **Content (top to bottom):**
  1. Segmented: Contacts · Groups · Invites.
  2. Contact rows: name, presence (if they share it), "You share: Card, Location coarse",
     "They share: Card", Block.
  3. Groups: name, kind Chip (Friends, Club, Safety), members, host ("my car", "relay").
  4. Invites: sent and received with countdown "expires in 46 h", Revoke.
  5. **Add**: QR, Copy link, Share (WhatsApp or any app via the share sheet), code "7K3M-Q9TD"
     (10 minutes). **Enter code** / Scan.
- **States:** empty: "No contacts. Friends appear only after an invite." · offline: invites
  queue · Moving (phone): allowed as passenger.
- **Safety and driving rules:** no address-book upload, no directory ([Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)).
- **Components:** Segmented, ListRow, Button, Sheet, Chip, QRCode.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites) · [Social §9](../../../../specs/2026-10-07-social-addon-design.md#9-media-stack-and-integrations)

### accounts-s8 — Accounts S8: Sharing ("who sees what")  [Existing]
- **Owner:** os
- **Purpose:** the matrix of who sees what, per vehicle and for me, with the audit.
- **Opens from → goes to:** Settings → Sharing; links from every share sheet → add a
  grant (who → what → how precise → how long); View as…; hub linked account; P9 rows.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night (matrix); phone
  Night (one audience at a time).
- **Content (top to bottom):**
  1. Vehicle picker ("Discovery") and "Me".
  2. Matrix: rows audiences (Household, Sam, Peak 4x4 club, Link, Public), columns classes
     (Presence, Location, Vehicle card, Live, Trips, Faults, Notes, Maintenance, Video); each
     cell its detail and countdown ("Coarse", "Route", "Live · 1 h 20 m").
  3. "Add a grant" (share-audience-picker first), presets (View, View + logs).
  4. **View as…** picker → renders the car through the real filter.
  5. Audit: pulls and hand-overs (time, who, class, path, size); trip shares "Shared 2× · 1
     active".
  6. Linked accounts: Ostler Community "@handle" with Unlink.
- **States:** all ghost: banner "You are a ghost: live classes send nothing" · Moving: locked.
- **Safety and driving rules:** only the data owner grants ([Accounts §14.2](../../../../specs/2026-10-06-accounts-sharing-design.md#142-audiences-and-grants)).
- **Components:** ListRow, Button, Sheet, Chip.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §15.4](../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412) · [Trip sharing §11](../../../../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit)

### accounts-s9 — Accounts S9: ghost toggle  [Existing]
- **Owner:** os
- **Purpose:** the visibility chip on every host and its sheet.
- **Opens from → goes to:** the strip chip, Settings → Sharing, Social and Vehicles & Map
  headers → vehicles-visibility (same sheet) → share-visible-summary.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving (chip and one-tap ghost); phone Night; hu7 Deep night Moving.
- **Content (top to bottom):** 1. Chip: neutral "Ghost" (`visibility_off`), or accent
  "Visible to Ride: Peak District · 1 h 20 m". 2. Sheet as vehicles-visibility.
- **States:** Moving: going ghost one tap; becoming visible waits for Parked or the phone.
- **Safety and driving rules:** ghost by default; never ends by itself ([Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode)).
- **Components:** ListRow, Button, Sheet, Chip.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode)

### accounts-s10 — Accounts S10: safety contacts  [Existing]
- **Owner:** os
- **Purpose:** who gets my SOS, crash alert and optional ride notices.
- **Opens from → goes to:** Settings → Safety contacts; social-ride-new Toggle.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night and Day.
- **Content (top to bottom):** 1. Contacts list with "Add". 2. Per contact: SOS, Crash alert,
  Ride start and end (opt-in). 3. Channel: paired-app push, my notify endpoint, the guardian's
  SMS. 4. **Send a test**. 5. Line: "Only your own SOS sends a precise position, even in ghost.
  It is logged and shown to you."
- **States:** none set: "Add someone you trust" · test sent · Moving: locked.
- **Safety and driving rules:** no one else can raise my precision ([Accounts §14.5](../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it)).
- **Components:** ListRow, Button, Sheet, Chip, Toggle.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §14.5](../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it) · [ADR-0033 §7](../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths)
