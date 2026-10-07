---
title: "Designer brief — Sharing: before-visible summary, received shares, relay viewer and invites"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Page content for five new sharing screens from approved specs: the one-screen summary of what
  each audience will see before leaving ghost, the view of a trip someone shared with me (L0 to
  L2, Locked or Download), the browser viewer of a relay link for L0 to L2 shares, entering an
  8-character invite code with the six-digit key check, and accepting an invite with the
  inviter's offered preset. States, rules and components; owners are the OS or the Trips app.
---

# Sharing, part b: ghost summary, received shares and invites

Example numbers and names in quotes are label formats, not data.

Part a: [60-apps-share-a.md](60-apps-share-a.md).

### share-visible-summary — "What each audience will see"  [New]
- **Owner:** os
- **Purpose:** the one-screen summary shown before turning ghost off.
- **Opens from → goes to:** vehicles-visibility or accounts-s9 "Become visible" → confirm →
  visible with a countdown.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked.
- **Content (top to bottom):**
  1. Title "If you become visible for 1 h".
  2. One row per audience with live grants: "Peak District ride: live location, speed off",
     "Sam: coarse location (±3 km)", "Household: presence".
  3. "Not affected by ghost": trips, faults and cards you shared stay as they are.
  4. Buttons **Become visible** · Cancel (Cancel focused).
- **States:** no live grants: "Nobody would see anything new." · Moving: not offered (only Go
  ghost while Moving).
- **Safety and driving rules:** timers only move toward ghost ([Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode)).
- **Components:** Sheet, ListRow, Button.
- **Spec refs:** [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode) · [Vehicles & Map §4](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#4-ghost-mode-and-the-visibility-sheet)

### share-recipient-view — A trip shared with me  [New]
- **Owner:** app:trips
- **Purpose:** view a friend's shared trip inside Ostler at the level they granted.
- **Opens from → goes to:** a share notification, Trips "Shared with me" filter, a friend's
  garage card trips row → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night (L1); hu7 Night Parked (L2 charts).
- **Content (top to bottom):** 1. Header: friend's name, level Chip, "Locked · until 14 Oct"
  or "Download". 2. L0 card; L1 map with dashed faded ends; L2 charts on relative time (e.g.
  RPM, Coolant). 3. "Download" (Download mode only). 4. Line: "Sam can withdraw this at any
  time."
- **States:** revoked or past access until: "This share has ended" and the copy is removed ·
  offline: held in memory only, "Reconnect to view" · Moving: locked view.
- **Safety and driving rules:** held in memory, not on disk, so revoke is real ([Accounts §4](../../../../specs/2026-10-06-accounts-sharing-design.md#4-multi-vehicle-garage)).
- **Components:** Sheet over map, StatTile, Card, Chip.
- **Spec refs:** [Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls) · [Accounts §15.4](../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412) · [Vehicles & Map §2.2](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#22-garage-card-the-face-of-a-shared-vehicle)

### share-relay-viewer — Relay link viewer (browser)  [New]
- **Owner:** os
- **Purpose:** what a person without Ostler sees when opening a relay link to an L0–L2 share.
- **Opens from → goes to:** the link (key in the URL fragment) → the page; "Get Ostler" link.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night and Day.
- **Content (top to bottom):** 1. Title, level Chip, day only, expiry "Link ends in 6 d".
  2. Card or map as granted; stats from the visible part only. 3. Download (if allowed).
  4. Footer: "Shared with Ostler. Ostler can't read this: it is decrypted in your browser."
- **States:** expired · revoked · full ("This link has reached its limit") · wrong key.
- **Safety and driving rules:** L3–L4 relay links are bundles (download only) ([Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls)).
- **Components:** Card, Sheet over map, Chip, Button.
- **Spec refs:** [Trip sharing §10](../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls) · [Accounts §5.2](../../../../specs/2026-10-06-accounts-sharing-design.md#52-invite-payload)

### share-invite-code — Enter an invite code  [New]
- **Owner:** os
- **Purpose:** redeem an invite that can't travel as a link (read aloud, typed Parked).
- **Opens from → goes to:** accounts-s7 "Enter code" → key check → share-invite-accept.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night.
- **Content (top to bottom):** 1. Field "Invite code" (8 characters, "7K3M-Q9TD"; no
  ambiguous letters). 2. Key check: "Check that both screens show 418 207" with **They match**
  · **They don't**. 3. Caption "Codes last 10 minutes and work once."
- **States:** wrong code: "4 tries left"; after 5 the address is locked · expired · mismatch:
  "Not connected. Ask for a new code." · Idling: Park evidence for typing · Moving: locked.
- **Safety and driving rules:** the share activates only on a match ([Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)).
- **Components:** Sheet, Keypad, Card, Button.
- **Spec refs:** [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)

### share-invite-accept — Accept an invite  [New]
- **Owner:** os
- **Purpose:** accept a friend or group invite and see what is offered.
- **Opens from → goes to:** an invite link or QR, share-invite-code → accounts-s7 contact.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day.
- **Content (top to bottom):** 1. "Sam invites you" (or "to Peak 4x4 club"). 2. "They offer:
  Vehicle card, Faults". 3. "You share nothing until you choose. You stay a ghost." 4. Buttons
  **Accept** · Decline.
- **States:** expired (48 h default) · already used · offline: "Can't reach Sam's car".
- **Safety and driving rules:** nothing live flows until each side leaves ghost ([Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites)).
- **Components:** Card, Button.
- **Spec refs:** [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites) · [Accounts §5.2](../../../../specs/2026-10-06-accounts-sharing-design.md#52-invite-payload)
