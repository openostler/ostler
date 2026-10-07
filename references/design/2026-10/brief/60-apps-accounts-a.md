---
title: "Designer brief — Accounts S1–S5: first run, sign in, passkeys, head-unit profiles, users and roles"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Page content for the first five OS account screens: S1 first run (physical setup code,
  name, passkey or password, recovery line; the phone-pairing variant for Ostler Diagnostics
  alone), S2 sign in (password, passkey where the origin allows, sign in with a code), S3
  passkeys (one per device name), S4 the head-unit profile switcher (kiosk session "Car",
  Parked-only switching with a local PIN or phone approval, sign-out at ignition off) and S5
  users and roles (user role, categories, expiry, local links only, show on head unit). States,
  rules and components.
---

# Accounts, part a: S1–S5

Example numbers and names in quotes are label formats, not data.

All account screens are OS system UI ([Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs)). Part b: [60-apps-accounts-b.md](60-apps-accounts-b.md).
The head unit starts in the **kiosk session** (Read and Comfort only); signing in is never
needed to drive ([Accounts §2.3](../../../../specs/2026-10-06-accounts-sharing-design.md#23-sessions)).

### accounts-s1 — Accounts S1: first run  [Existing]
- **Owner:** os
- **Purpose:** create the owner with the physical setup code; no default password.
- **Opens from → goes to:** any page when no owner exists ("Set up this Ostler") → S1 → optional
  "Name this car" and "Invite someone" (accounts-s7) → Home.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night and Day (also the pairing variant).
- **Content (top to bottom):**
  1. Title "Set up this Ostler".
  2. "Setup code" field (8 digits, Keypad on the head unit) with the hint "Shown on this
     screen's console or the Brain's display. Valid 15 minutes."
  3. "Your name".
  4. "Add a passkey" (when available) or "Choose a password" (≥ 12 characters).
  5. Recovery line: "Lost access? Run reset-owner on the device console."
  6. Optional: "Name this car" ("Discovery"), "Invite someone".
  7. Ostler Diagnostics alone (no Brain): "Pair your phone with the node: press the button on
     the node, or enter the code on its label" (companion-connect).
- **States:** wrong code: "That code didn't work · 4 tries left" · expired: "Get a new code on
  the console" · upgrade path: "Add a passkey or rename your account" banner · Parked: full ·
  Moving: locked view.
- **Safety and driving rules:** no email; no default password ([Accounts §2.1](../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap)).
- **Components:** ListRow, Button, Sheet, Chip, Keypad.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §2.1](../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap) · [Accounts §14.9](../../../../specs/2026-10-06-accounts-sharing-design.md#149-basic-auth-migration-replaces-the-overlap-line-in-21)

### accounts-s2 — Accounts S2: sign in  [Existing]
- **Owner:** os
- **Purpose:** sign in on a phone or desktop.
- **Opens from → goes to:** any signed-out route; companion-connect → the page asked for.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night and Day; desktop Night.
- **Content (top to bottom):** 1. User name and password; TOTP when set. 2. "Sign in with a
  passkey" (only when this origin can hold one). 3. "Sign in with a code" (for TVs and second
  screens: shows a code to approve in Settings). 4. "Forgot? Ask the owner for a reset invite."
- **States:** wrong password (rate-limited) · local-only user on a remote path: "This account
  works only in the car" · Moving (phone): allowed (passenger device).
- **Safety and driving rules:** passkeys only on a stable name ([Accounts §2.2](../../../../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always)).
- **Components:** ListRow, Button, Sheet, Chip.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §2.2](../../../../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always)

### accounts-s3 — Accounts S3: passkeys  [Existing]
- **Owner:** os
- **Purpose:** list, add and delete passkeys, each tied to the name it works on.
- **Opens from → goes to:** account menu → Passkeys → Add.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):** 1. Rows: passkey name, "Works on ostler-xxxx.local" (or the
  Tailscale or public name), created, last used, Delete. 2. "Add a passkey". 3. Guided CA
  install link for the no-cloud path.
- **States:** none: "No passkeys · use your password" · last credential of the last owner:
  delete warns and needs a confirm with Cancel focused.
- **Safety and driving rules:** head unit uses localhost and needs none ([Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs)).
- **Components:** ListRow, Button, Sheet, Chip.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §2.2](../../../../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always)

### accounts-s4 — Accounts S4: head-unit profile switcher  [Existing]
- **Owner:** os
- **Purpose:** switch from "Car" to a person on the head unit, Parked only.
- **Opens from → goes to:** the profile chip in the strip ("Car") → tile sheet → PIN or phone
  approval → signed in; ignition off → back to kiosk.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night Parked (tiles, PIN);
  hu7 Night-dim Moving (chip only).
- **Content (top to bottom):**
  1. Tiles of users who opted in to appear, plus people without a login (for "who drove"), plus
     "Car".
  2. PIN pad (6 digits, Keypad) or "Approve on my phone" (waits for the paired phone).
  3. Line "Signed out at ignition off."
- **States:** wrong PIN: "4 tries left"; after 5: "Locked for 15 minutes" · waiting for phone ·
  Moving: chip shows the current profile; tapping it says "Switch when parked".
- **Safety and driving rules:** switching Parked only; Tier 2–3 still need phone approval
  ([Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs), [ADR-0033 §6](../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override)).
- **Components:** ListRow, Button, Sheet, Chip, Keypad.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §2.3](../../../../specs/2026-10-06-accounts-sharing-design.md#23-sessions)

### accounts-s5 — Accounts S5: users and roles  [Existing]
- **Owner:** os
- **Purpose:** the owner manages people and users of this car.
- **Opens from → goes to:** Settings → Users → a user → edit; "Invite a person".
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night; phone Night.
- **Content (top to bottom):**
  1. Rows: name, user role Chip (Owner, Driver, Mechanic, Viewer), "Can sign in", "Shows on
     head unit", expiry (Mechanic always: "ends in 23 h").
  2. User detail: user role; categories added or removed (Read, Comfort, Security,
     Maintenance, Accessories…; never Coding); expiry; **Local links only** Toggle; Can sign
     in; Show on head unit; head-unit PIN reset; Disable; Delete ("trips keep 'former user'").
  3. "Invite a person" (one-time invite) and "Reset access".
- **States:** last owner: delete disabled with reason · Moving: locked view.
- **Safety and driving rules:** roles narrow, never widen; no role skips a confirm
  ([Accounts §3.2](../../../../specs/2026-10-06-accounts-sharing-design.md#32-the-one-rule)).
- **Components:** ListRow, Button, Sheet, Chip, Toggle.
- **Spec refs:** [Accounts §14.7](../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs) · [Accounts §3.1](../../../../specs/2026-10-06-accounts-sharing-design.md#31-roles) · [Accounts §3.2](../../../../specs/2026-10-06-accounts-sharing-design.md#32-the-one-rule)
