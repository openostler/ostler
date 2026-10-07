---
title: "Designer brief 10-e — onboarding: backup, restore, adding a Brain to a node, and moving to a new Brain"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0041-brain-ed25519-signing.md]
summary: >
  Fifth onboarding brief file. It covers making a backup of a Brain, restoring one onto a
  fresh Brain from the welcome screen, adding a Brain to an Ostler Diagnostics node that a
  phone already owns (the Brain adopts the node through the owner's phone and imports the
  roster), and the owner-led move from an old Brain to a new one as a step table. It is
  honest about what cannot move: the Brain's signing key and certificate authority stay
  behind, so every node is re-adopted with a press, phones trust the new Brain again, and
  passkeys may need adding again. Backup, restore and move are Proposed.
---

# 10-e — Backup, restore, add a Brain, move to a new Brain

**What can and cannot move.** No approved spec covers backup or a Brain move yet; these
screens follow the hard lines that do exist:
- The Brain's signing key **never leaves it**, not even in a backup ([ADR-0041][adr-41]
  item 5). A new Brain makes its own key, so each node must take the new key by **pairing
  or adoption**, which needs a press on the node ([ADR-0039 §7][adr-39]).
- The local CA and pairing authority **never move automatically** ([ADR-0037][adr-37]);
  ADR-0021 forbids sharing a CA key between devices. So phones trust the new Brain again
  (`setup-trust`).
- Anything that leaves the device is scrubbed of the VIN and identity replies
  ([ADR-0036 §3][adr-36]). The garage keeps only a masked VIN and an HMAC under a
  device-local secret ([UI §4.4][ui-4.4]), so the new Brain recognises the car again at
  first contact.
- Every app that keeps user data exports it in an open format ([App model §14][am-14],
  item 14.6), which a restore can read back.

### F8. Move to a new Brain

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `setup-move-brain` (old Brain) | starts the move, reads what will change | old Brain dead → skip to step 3 with the latest backup |
| 2 | `setup-backup` | makes a backup with a passphrase, saves it to the phone or a USB stick | not enough space → choose fewer trips |
| 3 | `setup-welcome` (new Brain) → `setup-restore` | picks the file, types the passphrase, checks the preview | wrong passphrase → retry; damaged file → "Can't read this backup" |
| 4 | `setup-trust` (each phone) | trusts the new Brain | fingerprint differs → stop |
| 5 | `setup-node-pair` (each node) | presses each node's button | node still claims the old Brain → **Remove old Brain** on its page |
| 6 | `setup-first-contact` | runs the check; the car is recognised | not recognised → "Is this *Discovery 2 Td5*?" **Yes** links it |
| 7 | `setup-move-brain` (new Brain) | finishes: retires the old Brain | old Brain unreachable → it is listed as removed |

### setup-backup — Make a backup  [Proposed]
- **Owner:** os
- **Why the app needs it:** a Brain holds users, the garage, layouts, settings and trips;
  without a backup a dead SD card loses all of it, and the exit guarantee needs one file.
- **Purpose:** write one encrypted file the owner keeps somewhere else.
- **Opens from → goes to:** Settings → System → **Backup**; `setup-move-brain` step 2. → a
  download (phone, desktop) or a USB stick on the Brain; back.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):**
  1. **What goes in** (each a ListRow with size and a check): "People and sign-in", "Garage
     and vehicles", "Home pages and layouts", "Installed apps", "Settings and places",
     "Trips" (Segmented "All · Last 90 days · None", with the size), "App data" (one row per app).
  2. **Never in a backup** (read-only list): "The Brain's signing key", "Its certificate
     authority", "Your car's VIN", "Raw captures".
  3. **Passphrase** and confirm, with a strength line; "Without it, nobody can open the
     backup, including us."
  4. **Save to**: Segmented "This phone · USB stick on the Brain".
  5. Button **Make backup** → progress (long job pattern) → `check_circle` "Backup ready ·
     size · date".
- **States:** last backup line at the top ("Last backup" with its age, or "Never"). Error:
  out of space, USB stick missing. Brain asleep: `shell-brain-wake`. Moving (phone):
  allowed; on a head unit: locked view.
- **Safety and driving rules:** owner only, local links only; Parked on head units.
- **Components:** ListRow, Segmented, text field, Button, progress rows, Card.
- **Spec refs:** [ADR-0041][adr-41] · [ADR-0036][adr-36] · [App model §14][am-14] ·
  [Drive modes §8.3 (layouts storage)][dm-8.3].
- **Open questions:** (1) Encrypted with a passphrase, or plain with a warning? (2) Are
  passkeys worth backing up, given each works only on the name it was made on?
  (3) Scheduled automatic backups to a USB stick?

### setup-restore — Restore from a backup  [Proposed]
- **Owner:** os
- **Why the app needs it:** a replaced or reset Brain must come back with its people,
  vehicles and trips, not start from nothing.
- **Purpose:** read a backup onto a Brain that has no owner yet.
- **Opens from → goes to:** `setup-welcome` → **Restore from a backup**. → the re-pair
  checklist (§5) → `setup-summary`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; hu7 Night.
- **Content (top to bottom):**
  1. The setup code field (the restore also proves you are at the Brain).
  2. **Choose the backup**: from this phone, or a USB stick on the Brain (a list of files
     with date and size).
  3. **Passphrase**.
  4. **Preview**: what the file holds (counts of people, vehicles by nickname such as "Discovery 2
     Td5", trips and apps) and the date it was made. Button **Restore**.
  5. **After restore, do these**: checklist rows "Trust this Brain on each phone", "Press
     the button on each node", "Check the first contact", "Add passkeys again if asked".
- **States:** wrong passphrase → inline; backup from a newer version → "Update this Brain
  first"; an app in the backup not installed → row `warn` "Install the Maintenance app
  to restore its data" (from the bundled catalogue when it has it). Moving / unknown: as `setup-welcome` (locked view on head units).
- **Safety and driving rules:** text entry Parked only on head units; restore never
  restores pairings or grants to nodes: each node is re-adopted with a press.
- **Components:** CodeInput (new), ListRow, text field, Card, progress rows, Button.
- **Spec refs:** [Accounts §2.1][acc-2.1] · [Accounts §14.10][acc-14.10] ·
  [ADR-0037][adr-37] · [ADR-0041][adr-41].
- **Open questions:** do restored users keep their roles and expiries as they were, or
  does a Mechanic's time box restart?

### setup-add-brain — Add a Brain to my node  [New]
- **Owner:** os
- **Purpose:** an owner of Ostler Diagnostics alone (node plus phone) adds a Brain; the
  Brain adopts the node through the owner's phone and imports the node's roster.
- **Opens from → goes to:** the new Brain's `setup-welcome` (it sees an owned node and
  offers **I already have an Ostler node**); the phone app's Settings → Network → **Add a Brain**.
  → `setup-trust` on the phone → `setup-summary`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (approve); hu7 Night (waiting).
- **Content (top to bottom):**
  1. Brain side: "Approve on your phone" with the node's name and a countdown; **Cancel**.
  2. Phone side Sheet: "Add this Brain to *Discovery 2 Td5*?" the Brain's name and
     fingerprint (compare with the Brain's screen); what changes: "The Brain will hold your
     users and keep your trips. Your phone stays the owner." Buttons **Approve**,
     **Cancel** (focused).
  3. Done: "Brain added. Your node's people were copied to it."
- **States:** phone not the node's owner → "Only the owner's phone can add a Brain".
  Phone not near the node → "Open the app next to the car". Moving: locked view on the
  Brain's head unit; the phone side is allowed (passenger device) but the node re-checks.
- **Safety and driving rules:** no silent takeover: the owner's paired phone authorises it
  ([ADR-0039 §7][adr-39]); a Brain added later imports the roster at pairing
  ([Accounts §14.10][acc-14.10]).
- **Components:** Sheet, Card, Button, countdown ring.
- **Spec refs:** [ADR-0039 §7][adr-39] · [Accounts §14.10][acc-14.10] · [ADR-0032][adr-32].
- **Open questions:** do trips the node recorded itself move to the Brain at this step or
  later in the background?

### setup-move-brain — Move to a new Brain  [Proposed]
- **Owner:** os
- **Why the app needs it:** replacing a Brain (a bigger one, a failed one) touches trust,
  keys and every node; doing it by hand in the right order is error-prone.
- **Purpose:** guide F8 from the old Brain and finish it on the new one.
- **Opens from → goes to:** Settings → System → **Move to a new Brain** (old); the new Brain
  after a restore that names an old Brain. → `setup-backup`; finishing → `setup-summary`.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Day.
- **Content (top to bottom):**
  1. **What will happen** (numbered): "Back up this Brain", "Restore on the new Brain",
     "Trust the new Brain on each phone", "Press the button on each node", "Retire this
     Brain".
  2. **What won't move** Card (info): "Approvals and certificates are made fresh on the new
     Brain. Each node needs one press. Passkeys may need adding again."
  3. Devices to re-pair: ListRows of the nodes from Settings → Network with **Pending** or
     **Done**.
  4. **Retire the old Brain** (danger Button, last): "Removes it from every node and signs
     it out everywhere. Its data is erased." Confirm Sheet, Cancel focused.
- **States:** a node still lists the old Brain → row `warn` with **Remove old Brain**
  (the device page's owner-only Remove device, [UI §3.7][ui-3.7]). Old Brain offline →
  "Retire it from here" removes it from the new Brain's records only.
- **Safety and driving rules:** owner only, local links only; never over a remote path.
- **Components:** ListRow, Card, Chip (status), Button (danger), Sheet.
- **Spec refs:** [ADR-0037][adr-37] · [ADR-0041][adr-41] · [UI §3.7][ui-3.7] ·
  [Accounts §14.10][acc-14.10].
- **Open questions:** should the move keep the old Brain's mDNS name so passkeys keep
  working ([Accounts §2.2][acc-2.2])?

[acc-2.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap
[acc-2.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always
[acc-14.10]: ../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[ui-3.7]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[adr-32]: ../../../../decisions/adr-0032-one-node-optional-brain.md#decision
[adr-36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md#decision
[adr-37]: ../../../../decisions/adr-0037-role-holders-and-handover.md#decision
[adr-39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[adr-41]: ../../../../decisions/adr-0041-brain-ed25519-signing.md#decision
