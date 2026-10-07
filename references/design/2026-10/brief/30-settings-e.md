---
title: "Designer brief: Settings (part E): updates, profiles and users, my account, Ostler Link"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Part E of the Settings brief. It covers a Proposed Updates page (release channel, the
  monthly release, app updates, and a link by name to the hardware brief's firmware
  update); a New Profiles and users hub (the head unit's Car kiosk profile, Lock car layouts,
  the head-unit profile switcher, user roles Owner, Driver, Mechanic and Viewer, and a note
  that ADR-0037's role holders are device duties shown in Network); a New Head-unit PIN page;
  a New My account page (name, passkeys, password and second factor, signed-in devices, the
  linked Ostler Community account); and a Proposed Ostler Link page for the optional cloud
  subscription (remote access, push, backup, public name).
---

# Settings brief, part E: Updates, Profiles, My account, Ostler Link

Tree, shared rules and the Settings lock: [part A](30-settings-a.md).

### settings-updates — Updates  [Proposed]
- **Owner:** os
- **Purpose:** keep Ostler, the vehicle packs and apps current, on the owner's terms.
- **Why proposed:** update channels and install flavours wait for their own research note and
  ADR ([ADR-0042][adr-0042], Home Assistant direction item 8); owners still need one place to
  see versions and apply the release.
- **Opens from → goes to:** Settings → Updates; an "Update ready" Home card; About. Goes to
  the hardware brief's **firmware update** page (by name, `20-hardware-*`) for node,
  guardian and module firmware, and to each app's App info (`90-appframe-*`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Status Card: "Ostler ‹version› · up to date", or "‹version› is ready" with "What's new"
     and **Install** (primary). The monthly release reads "‹Month year› release".
  2. **Channel**: Segmented "Stable (monthly) · Beta". Caption for Beta: "Early builds for
     testers. Things may break. Car actions still pass the same safety gate."
  3. **When**: Segmented "Ask me · Install when parked overnight"; caption "Never while
     driving. Never while a car action or a recording upload is running."
  4. **Vehicle packs**: one row per installed pack, for example "Land Rover Discovery 2 Td5
     · ‹version›", with "Update" where one is ready; signed by the pack's maintainers.
  5. **Apps**: one row per app with an update, "Update all"; each opens its detail.
  6. **Devices**: one row "Node and module firmware · ‹n› updates" → the hardware brief's
     firmware page.
  7. **On a metered uplink**: caption "Downloads wait for Wi-Fi when the SIM budget is
     reached."
- **States:** checking; up to date; download progress; install progress ("Ostler will
  restart. The car stays safe; no car action runs."); error ("Couldn't verify the update.
  Nothing was changed."); offline ("Check again when online"); Brain asleep ("Needs the
  Brain"); Parked full; Moving: the Settings lock; locked: owner only.
- **Safety and driving rules:** installs only Parked, refused while Moving or with a running
  action; owner only; an update never widens an app's permissions without asking again.
- **Components:** Card, Segmented, ListRow, Button, progress bar (new, part C).
- **Spec refs:** [ADR-0042][adr-0042], [ADR-0028][adr-0028] (metered budgets),
  [app model §4.2][am-4.2].
- **Open questions:** two channels or three (stable, beta, nightly)? Is "monthly" the
  owner's release cadence for the platform, and do packs follow it?

### settings-profiles — Profiles and users  [New]
- **Owner:** os
- **Purpose:** who uses this car's screens, and as what.
- **Opens from → goes to:** Settings → Profiles and users; the profile chip ("Car") in the
  strip when Parked. Goes to Users and roles (`accounts-s5`), the profile switcher
  (`accounts-s4`), Head-unit PIN, Display (Lock car layouts), Contacts (`accounts-s7`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. **On this head unit**: "Signed in as ‹name›" or "Car (no sign-in)"; Button "Switch
     profile" (Parked only) → `accounts-s4`; caption "Everyone is signed out when the
     ignition goes off."
  2. **The Car profile** (Card): "Car can read, use climate and media, and arm. Clearing codes
     and anything else needs a signed-in driver." Rows: "Layouts for Car" (edit Home and Drive
     modes as Car), **Lock car layouts** (owner only, Switch, mirrors Display).
  3. **People** (owner sees all): rows per user with role Chip, "shows on the head unit" and
     expiry, for example "Mechanic · until ‹date›". Button "Invite someone". → `accounts-s5`.
  4. **Roles explained** (read-only): Owner ("everything up to Tier 3; users, shares,
     tokens"), Driver ("drive, climate, arm, clear codes"), Mechanic ("tests and procedures;
     always time-limited"), Viewer ("read only; location only if you share it"). Caption:
     "A role here is what a person may do. The jobs devices hold, such as the transmit gate
     or the parked broker, are shown in Network."
  5. **My head-unit PIN** → `settings-hu-pin`.
- **States:** one user only ("Just you. Invite a driver?"); loading; offline ("Needs the
  Brain"); Ostler Diagnostics alone (paired phones as users, no head-unit rows); Parked
  full; Moving: the Settings lock; locked (Car profile): items 1, 2 and 4 read-only.
- **Safety and driving rules:** switching profile is Parked only; Tier 2–3 still need phone
  approval ([Accounts §14.7][acc-14.7] S4); roles narrow, never widen
  ([Accounts §3.2][acc-3.2]).
- **Components:** Card, ListRow, Chip (role), Switch (new), Button.
- **Spec refs:** [Accounts §2.3][acc-2.3], [Accounts §3.1][acc-3.1],
  [Accounts §14.7][acc-14.7], [Accounts §14.11][acc-14.11], [Drive modes §8.3][dm-8.3],
  [ADR-0037][adr-0037].
- **Open questions:** the brief asked for "guest"; the approved roles are Owner, Driver,
  Mechanic and Viewer, plus the Car kiosk session. Is "guest" the Viewer, or a new
  time-boxed Driver?

### settings-hu-pin — Head-unit PIN  [New]
- **Owner:** os
- **Purpose:** set the 6-digit PIN that unlocks your profile on this car's head unit.
- **Opens from → goes to:** Profiles and users → My head-unit PIN; first profile switch.
  Back to Profiles.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (the keypad), phone Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Caption: "Works only on this car's head unit. It never signs you in anywhere else."
  2. State row: "PIN set ‹date›" or "No PIN"; Switch "Show me on the head unit".
  3. Set or change: keypad (new component: 3 × 4 digits, 76 px keys on head units, no
     letters), "Enter 6 digits", then "Enter again"; dots show progress.
  4. "Remove PIN"; caption "You can also approve from your paired phone instead."
- **States:** mismatch ("The PINs don't match"); weak ("Avoid 123456 and repeated digits");
  locked after five wrong tries ("Locked for 15 minutes"); Parked full; Moving: the lock.
- **Safety and driving rules:** setting it needs a full sign-in; keypad Parked only; valid on
  `localhost` only; never mints a token ([Accounts §14.7][acc-14.7] S4).
- **Components:** keypad (new), Switch (new), ListRow, Button.
- **Spec refs:** [Accounts §14.7][acc-14.7], [Accounts §14.12][acc-14.12].
- **Open questions:** none.

### settings-account — My account  [New]
- **Owner:** os
- **Purpose:** the signed-in person's own sign-in and identity settings.
- **Opens from → goes to:** Settings → My account (top row of Settings). Goes to Passkeys
  (`accounts-s3`), Signed-in devices (`accounts-s6`), Ostler Link, Safety contacts
  (`accounts-s10`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Header: name, role Chip, "Local links only" Chip if set.
  2. **Sign-in**: "Passkeys · ‹n›" → `accounts-s3`; "Password · changed ‹date›" → change
     (≥ 12 characters); "Two-step code" Switch (TOTP, shows a QR to scan once).
  3. **Devices**: "Signed-in devices · ‹n›" → `accounts-s6`; "Sign out everywhere else".
  4. **Ostler Community**: "Linked as ‹hub name›" or "Link your Community account"; scopes
     publish, read, help; "Unlink". Caption: "A Community account never signs you into the
     car."
  5. **Ostler Link** row → `settings-ostler-link`.
  6. **Safety contacts** → `accounts-s10`.
  7. Button "Sign out".
- **States:** passkeys unavailable ("Passkeys need the optional security package"); remote
  path ("This account works only in the car" for a local-only user); Parked full; Moving:
  the Settings lock; locked (Car profile): "Sign in to see your account".
- **Safety and driving rules:** password and TOTP entry Parked only; deleting the last
  credential of the last owner warns and is refused ([Accounts §14.7][acc-14.7] S3).
- **Components:** ListRow, Chip, Switch (new), Button, password field (new, part D).
- **Spec refs:** [Accounts §2.2][acc-2.2], [Accounts §14.7][acc-14.7],
  [Accounts §15.5a][acc-15.5a].
- **Open questions:** none.

### settings-ostler-link — Ostler Link (cloud subscription)  [Proposed]
- **Owner:** os
- **Purpose:** the optional paid service: reach the car away from home, push alerts, and an
  encrypted backup.
- **Why proposed:** Ostler Cloud is a product in [ADR-0028][adr-0028] §6 with no screen; the
  research suggests one plan and a clearer name ("Ostler Link").
- **Opens from → goes to:** My account → Ostler Link; Network → Remote access; Backups.
  Goes to the Ostler Link portal in the browser (sign-up and billing are not in the app).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Status Card: "Not connected · Optional" or "Active · renews ‹date›"; Button "Learn
     more" or "Manage in browser".
  2. **What it adds** (Switch each, only when active): Remote access ("Your car's own page
     from anywhere; end-to-end encrypted; read-only plus arming"); Push alerts through Ostler
     Link; Backups to Ostler Link; Public name for passkeys ("‹name›.‹device›…").
  3. **Never** (read-only list): "Ostler Link can't read your data, can't send a car action,
     and isn't needed: Wi-Fi and Tailscale work without it."
  4. Row "Remote access options" → Network.
- **States:** not subscribed (items 2 greyed with "Needs Ostler Link"); offline; expired
  (`warn` "Remote access stopped ‹date›"); Parked full; Moving: the lock; locked: owner only.
- **Safety and driving rules:** remote paths stay read-only plus arming and disarming
  ([ADR-0033][adr-0033] §6); no remote write to the car, whatever the plan.
- **Components:** Card, Switch (new), ListRow, Button.
- **Spec refs:** [ADR-0028][adr-0028], [Accounts §5.4][acc-5.4], [Accounts §14.7][acc-14.7],
  [Accounts §14.10][acc-14.10].
- **Open questions:** the name (Ostler Cloud or Ostler Link) and the plan's contents are
  owner decisions; is billing shown in the app at all?

<!-- refs -->
[acc-14.10]: ../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery
[acc-14.11]: ../../../../specs/2026-10-06-accounts-sharing-design.md#1411-role-means-two-things
[acc-14.12]: ../../../../specs/2026-10-06-accounts-sharing-design.md#1412-data-model-api-and-tests-deltas
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[acc-15.5a]: ../../../../specs/2026-10-06-accounts-sharing-design.md#155a-hub-identity-is-hub-owned-one-ostler-account-later-approved-changes-148-later
[acc-2.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always
[acc-2.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#23-sessions
[acc-3.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#31-roles
[acc-3.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#32-the-one-rule
[acc-5.4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#54-transports
[adr-0028]: ../../../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[adr-0033]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-0037]: ../../../../decisions/adr-0037-role-holders-and-handover.md
[adr-0042]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
