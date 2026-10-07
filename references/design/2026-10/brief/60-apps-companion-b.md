---
title: "Designer brief — Companion phone app: notifications, Trips sync, favourites pick, passenger prompt, approvals and account"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-phone-comms-addon-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Page content for the rest of the companion phone app: push notification settings per category
  (proposed), Trips sync to the phone (proposed), picking favourites from the phone's contacts
  for the Phone app, the phone's Moving banner and "I'm a passenger" prompt, approving a Tier 2
  or 3 action on the phone over a local link with Stop, and account settings gathering sign-in,
  passkeys, devices, cars and data (proposed). States, rules and components.
---

# Companion phone app, part b

Example numbers and names in quotes are label formats, not data.

Part a: [60-apps-companion-a.md](60-apps-companion-a.md).

### companion-notifications — Notification settings  [Proposed]
- **Owner:** os
- **Why the app needs it:** push is a native feature fixed in the binary, and apps ask the OS
  for it; the owner needs one place to choose categories, with alarm alerts locked on.
- **Purpose:** choose which pushes the phone gets, per car and per app.
- **Opens from → goes to:** connect flow step 4; Settings → Notifications.
- **Layout classes:** phone. **Draw first:** phone Night and Day.
- **Content (top to bottom):**
  1. "Alarm and security alerts": On, locked ("Can't be turned off here; use the phone's
     settings to silence").
  2. "New faults" (e.g. "P0403 EGR inlet throttle") Toggle.
  3. Per installed app: Social messages, Community replies, Maintenance reminders… Toggles.
  4. Quiet hours (except alarms).
  5. System permission state: "Notifications allowed" or "Open phone settings".
- **States:** permission denied banner · no apps installed: only system rows.
- **Safety and driving rules:** message content never shown on a head unit while Moving; the
  phone follows its own OS rules ([App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates), [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** ListRow, Toggle, Button.
- **Spec refs:** [ADR-0042](../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) · [App model §14](../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates) · [ADR-0033 §7](../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths)

### companion-trips-sync — Trips on this phone  [Proposed]
- **Owner:** os
- **Why the app needs it:** on Ostler Diagnostics alone the phone is the only screen, and with a
  Brain the owner may want trips readable offline; no approved spec defines the copy.
- **Purpose:** choose which trips the phone keeps a copy of, and see sync state.
- **Opens from → goes to:** Settings → Trips on this phone; Trips app "…".
- **Layout classes:** phone. **Draw first:** phone Night.
- **Content (top to bottom):** 1. "Keep trips on this phone": None · Last 7 days · Last 30
  days. 2. "Sync over": Car Wi-Fi only (default) · Any network. 3. State "Synced 12 trips ·
  14:20" or "Waiting for car Wi-Fi". 4. Line: "Trips stay on your own devices. Location never
  goes to Ostler." 5. "Remove copies from this phone".
- **States:** syncing progress · storage full · node only: "Trips come from the node over
  Bluetooth".
- **Safety and driving rules:** location stays on the user's devices ([ADR-0009](../../../../decisions/adr-0009-session-logbook-and-location.md)).
- **Components:** Segmented, ListRow, Button.
- **Spec refs:** [ADR-0009](../../../../decisions/adr-0009-session-logbook-and-location.md) · [App model §7.1](../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build)
- **Open questions:** does the owner want a phone copy at all, or should the phone only view
  trips from the Brain?

### companion-favourites-pick — Pick favourites from this phone  [New]
- **Owner:** app:phone
- **Purpose:** add a phone contact as a favourite for the car, one contact per pick, no
  contacts permission.
- **Opens from → goes to:** phone-favourites "Pick from phone" (on the phone, or pushed from the
  head unit) → the system contact picker → choose number → saved.
- **Layout classes:** phone. **Draw first:** phone Night and Day.
- **Content (top to bottom):** 1. "Choose a contact" → the system picker. 2. Number choice
  "mobile · work". 3. "Saved to Favourites in the car". 4. Line "Only this contact is shared
  with your car. Ostler can't see your other contacts."
- **States:** cancelled · no number on the contact · car not reachable: "Saves when connected".
- **Safety and driving rules:** no `READ_CONTACTS` in the store build ([Phone & Comms §3.3](../../../../specs/2026-10-07-phone-comms-addon-design.md#33-the-companion-bridge-path-a)).
- **Components:** Sheet, ListRow, Button.
- **Spec refs:** [Phone & Comms §3.3](../../../../specs/2026-10-07-phone-comms-addon-design.md#33-the-companion-bridge-path-a) · [Phone & Comms §5](../../../../specs/2026-10-07-phone-comms-addon-design.md#5-contacts-one-view-two-sources)

### companion-passenger — Moving banner and "I'm a passenger"  [New]
- **Owner:** os
- **Purpose:** the phone's Moving rules: a banner, and a once-per-trip passenger prompt for
  non-driving views.
- **Opens from → goes to:** opening Social, the Map, Trips analysis or Community while the car
  moves → prompt → the view; Open on phone from the head unit lands here.
- **Layout classes:** phone. **Draw first:** phone Night Moving (banner and prompt).
- **Content (top to bottom):** 1. Banner "Car is moving" (icon and word). 2. Prompt "Are you a
  passenger? The driver must not use this while driving." **I'm a passenger** · **Cancel**;
  no "always". 3. While granted: small "Passenger" badge.
- **States:** re-prompts after a stop or a new trip · car actions keep the stationary check.
- **Safety and driving rules:** logged locally, view-only, no "always" ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** Card (banner), Sheet, Button, Chip.
- **Spec refs:** [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)

### companion-approval — Approve an action on the phone  [New]
- **Owner:** os
- **Purpose:** approve a Tier 2–3 action on a paired phone over a local link, with Stop.
- **Opens from → goes to:** a head-unit or desktop request ("Approve on my phone") → approve →
  progress with **Stop** → done or refused.
- **Layout classes:** phone. **Draw first:** phone Night (approval and running).
- **Content (top to bottom):** 1. Card: the action name exactly as on the button that asked for it, tier and category words, `candidate` mark if any, preconditions checklist.
  2. **Approve** · **Decline** (Decline focused). 3. Running: progress and a large **Stop**;
  "Losing this phone's link stops the action."
- **States:** not on a local link: "Approve at the car (local link needed)" · refused by the
  node: "Not while moving" · expired request.
- **Safety and driving rules:** local links only; node re-checks Parked; an accept in an AI
  client never counts ([ADR-0033 §6](../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override), [UI §7.2](../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033)).
- **Components:** Card, Button, Chip.
- **Spec refs:** [ADR-0033 §6](../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override) · [UI §7.2](../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033) · [Accounts §3.2](../../../../specs/2026-10-06-accounts-sharing-design.md#32-the-one-rule)

### companion-account — Account and cars  [Proposed]
- **Owner:** os
- **Why the app needs it:** the account screens (S2, S3, S6) are written for any host; the
  phone needs one native entry gathering them with the cars this phone is paired to.
- **Purpose:** who I am on each car, how I sign in, and my data.
- **Opens from → goes to:** Settings → Account → accounts-s3, accounts-s6, accounts-s8,
  companion-connect.
- **Layout classes:** phone. **Draw first:** phone Night and Day.
- **Content (top to bottom):** 1. Cars: "Discovery · Owner", "Add a car", "Forget this car".
  2. Sign-in: passkeys (accounts-s3), password. 3. Devices (accounts-s6). 4. Sharing and ghost
  (accounts-s8, accounts-s9). 5. Linked accounts: Ostler Community. 6. "Sign out of this phone".
- **States:** signed out: "Sign in" · node only: owner by pairing key, no password.
- **Safety and driving rules:** a phone's pairing key can be revoked at the node ([Accounts §14.10](../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery)).
- **Components:** ListRow, Button.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §14.10](../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery)
