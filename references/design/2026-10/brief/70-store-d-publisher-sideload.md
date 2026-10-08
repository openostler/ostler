---
title: "Designer brief: Store (part D): publisher, report, catalogues and offline, developer sideload, open questions"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-community-hub-design.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0041-brain-ed25519-signing.md, references/research/ha_architecture_addons.md, references/research/ha_companion_community.md, references/research/ha_integrations_dashboards.md]
summary: >
  Part D of the Store brief. The publisher page lists one publisher's items, verified key
  and source links. The report sheet sends a reason about an item to whoever runs the
  catalogue and can hide the item on this Brain. The catalogues page shows where items come
  from (the bundled catalogue, the opt-in online catalogue, publisher keys the owner trusts) and how
  the Store works offline, including refreshing from a file. Developer sideload installs an
  item from a file behind Developer mode, with a warning sheet that names what is unsigned.
  The file ends with the owner's decisions of 2026-10-07 on ratings, paid items, review
  levels, the signing model, the online catalogue and the Store's owner. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# Store brief, part D: publisher, report, offline, sideload, questions

Parts: [A: rules, home, browse](70-store-a-home-browse.md) ·
[B: item detail and install](70-store-b-item-install.md) ·
[C: updates and My library](70-store-c-updates-library.md) · **D** (this file).

### store-publisher — Publisher page  [New]
- **Owner:** os
- **Purpose:** one publisher: who they are, their key, their items.
- **Opens from → goes to:** `store-item` publisher row; `store-install-sheet` publisher
  line. Goes to `store-item`, the publisher's source (browser or QR).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night ("openostler"), desktop Night.
- **Content (top to bottom):**
  1. Name ("openostler"), review level Chip "First party" (or "Verified publisher",
     "Community"), `verified` icon with
     "Verified key" and the key fingerprint in mono, short form with **Show full key**.
  2. One line about them; links **Source code** (GitHub organisation) and **Website**.
  3. Facts row: "‹n› items · Open source: ‹n› of ‹n› · On Ostler since ‹date›". No ratings.
  4. **Items** grouped by kind as StoreItemCards (for openostler: Diagnostics, Trips,
     Security, Maintenance & Garage, Navigation, the Ostler pack for Land Rover Discovery
     2, Starter widgets, Default theme).
  5. **Report this publisher** link (→ `store-report`).
- **States:** loading; offline (only bundled items, line "Offline · showing items on this
  Brain"); key revoked: `alarm` Card "This publisher's key was revoked on ‹date›. Their
  items no longer install." Moving (head unit): locked view. Locked: readable.
- **Safety and driving rules:** as `store-home`.
- **Components:** Chip, ListRow, StoreItemCard (new), Card (tone), mono key text (visual
  type `type-mono`, as Decode lab).
- **Spec refs:** [app model §4.1][am-4.1] (`source.publisher`, `ostler.*` reserved),
  [app model §7][am-7] (publisher keys), [ADR-0041][adr-41] · [Store §3][st-3] · [Store §5][st-5].
- **Open questions:** **Decided (item 29):** every release is signed by its publisher's
  Ed25519 key, delegated by the project's TUF-style targets role; see question 4 below.

### store-report — Report an item  [Proposed]
- **Owner:** os
- **Why the app needs it:** an open catalogue needs a way to flag a broken, unsafe or
  misleading item; the hub already has report on every object ([hub §14][hub-14]).
- **Purpose:** send a report about an item or publisher, and hide it on this Brain.
- **Opens from → goes to:** `store-item` **Report this item**; `store-publisher`. Send →
  back with the toast "Report sent. Thank you."
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night with the keyboard, hu7 Night.
- **Content (top to bottom):**
  1. Title "Report ‹item›".
  2. **Reason** RadioOpt rows: "It doesn't work with my car" · "It reads more than it
     says" · "It tried to do something unsafe" · "Misleading description or screenshots" ·
     "Copies someone else's work" · "Other".
  3. **Details** text field (optional, ≤ 500 characters; Parked only on head units).
  4. Checkbox "Include the item's version and my vehicle model" (on; never the VIN, line
     "Your VIN is never sent", [ADR-0036][adr-36]).
  5. Checkbox "Hide this item on this Brain".
  6. Buttons **Send** (primary) and **Cancel**.
- **States:** offline: "Saved. Sends when you are online." Sent; error "Couldn't send ·
  Retry". Moving (head unit): locked view; phone: works. Not signed in to a hub account: the
  report goes anonymously to the catalogue operator. An item from a file or an added
  catalogue: "This item isn't from the Ostler catalogue. Report it to its publisher" with
  their link.
- **Safety and driving rules:** typing Parked only on head units; "It tried to do something
  unsafe" also shows "Car actions always pass the car's own checks. To stop an action now,
  press Stop."
- **Components:** Sheet, RadioOpt (ListRow with a radio), text field, checkbox, Button.
- **Spec refs:** [hub §14][hub-14] (moderation, statement of reasons), [ADR-0036][adr-36].
- **Open questions:** who reviews reports: the hub's moderators, or a separate Store team?

### store-sources — Catalogues and offline  [New]
- **Owner:** os
- **Purpose:** show and manage where Store items come from, and the offline state.
- **Opens from → goes to:** `store-home` overflow menu → "Catalogues"; the offline banner's
  **Details**. Goes to `store-sideload` (Developer mode), the file picker.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night (offline).
- **Content (top to bottom):**
  1. **Bundled with Ostler ‹version›**: "‹n› items · always available · updates with
     Ostler". Line: "Works with no internet."
  2. **Ostler catalogue** (online): toggle **Use the online catalogue** (owner), off by
     default and offered once at first run (item 32); when on, a status Chip "Up to date ·
     ‹time›" or "Offline" and **Refresh**.
  3. **Publisher keys you trust** (item 29): keys the owner added on this Brain, rows with
     name, key fingerprint and "Trusted by you", **Remove**; **Add a key** (Developer
     mode).
  4. **Update the catalogue from a file**: "Copy a catalogue file from the Ostler website to a
     USB stick or your phone, then pick it here." Button **Choose file**. The file is
     checked against the catalogue key before use.
  5. Caption: "Items you install stay working when the catalogue is offline."
- **States:** offline (section 2 shows "Offline · last refreshed ‹date›"); file check
  failed: "This catalogue file isn't signed by a key you trust"; refreshing. Moving (head
  unit): locked view. Not owner: read-only.
- **Safety and driving rules:** owner only for toggles and files; Parked only on head units.
- **Components:** Card, ListRow, Chip (status), toggle (as Segmented "On · Off"), Button.
- **Spec refs:** [ADR-0042 §5–7][adr-42] (no remote catalogue yet, exit guarantee),
  [app model §11 Q7][am-11], [HA research §8 Decide 8][ha-arch-8] · [Store §5][st-5] · [Store §7][st-7].
- **Open questions:** **Decided (items 29 and 32):** see questions 4 and 5 below.

## Developer sideload (flow)

| # | Screen | The user | What can fail → recovery |
|---|---|---|---|
| 1 | `settings-developer` | turns on service mode and **Allow installs from a file** | not owner → hidden |
| 2 | `store-sideload` | picks a file (USB stick on a head unit, file picker on desktop and phone browser) | not an Ostler package → "This file isn't an Ostler item" |
| 3 | `store-sideload-warning` | reads what is unchecked, types the item's name to confirm | Cancel → nothing installed |
| 4 | `store-install-sheet` | reviews access as usual | requirements not met → disabled with the reason |
| 5 | `store-installing` | waits | as part B |

### store-sideload — Install from a file  [New]
- **Owner:** os
- **Purpose:** pick a package file and inspect it before install.
- **Opens from → goes to:** `store-home` overflow → **Install from a file** (only in
  Developer mode); `store-sources`. Goes to `store-sideload-warning`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  desktop Night, hu7 Night (USB stick list).
- **Content (top to bottom):**
  1. Card `warn`: "Developer mode: items from files skip the Store's checks."
  2. **Choose file** (desktop, phone browser) or a list of packages found on a USB stick
     (head unit), each row with name and size.
  3. After picking: the manifest read out: id, name, version, kind, publisher, signature
     status Chip ("Signed by openostler", "Signed by an unknown key", "Not signed"), data
     classes, actions with categories, hosts.
  4. Buttons **Continue** and **Cancel**.
- **States:** no file; reading; unreadable ("This file isn't an Ostler item"); manifest
  refused by the registry ("Asks for an action whose category doesn't match the car's
  list", [app model §4.2][am-4.2]); native phone app: not offered ("Install from a file
  works in a browser or on the head unit"). Moving: locked. Not owner, or Developer mode
  off: hidden.
- **Safety and driving rules:** the registry's checks still apply (shell range, action
  categories, data classes, widget limits); a sideloaded item gets no more power than a
  catalogue one, and community code still runs only sandboxed on web hosts
  ([app model §5][am-5], [§7.1][am-7.1]).
- **Components:** Card (`warn`), ListRow, Chip (status), Button.
- **Spec refs:** [app model §4.2][am-4.2], [§5][am-5], [§7.1][am-7.1] · [Store §8][st-8].
- **Open questions:** **Decided ([Store §8][st-8]):** a sideloaded item may be unsigned
  (with this warning) or signed by a developer key; it wears a Sideloaded badge and is
  disabled when service mode is turned off unless the owner keeps it.

### store-sideload-warning — Unchecked item warning  [New]
- **Owner:** os
- **Purpose:** state plainly what is not checked, and confirm.
- **Opens from → goes to:** `store-sideload` **Continue**. Confirm → `store-install-sheet`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  desktop Night, hu7 Night.
- **Content (top to bottom):**
  1. Icon `warning` and title "Install an unchecked item?"
  2. List of what is not checked: "Not from the Ostler catalogue", "Signed by an unknown
     key" or "Not signed", "Nobody has reviewed its code".
  3. What still holds: "It can only read what it lists. Every car request still passes the
     car's own checks. It never runs while you drive unless as a driving template."
  4. Field "Type the item's name to confirm" (Parked only).
  5. Buttons **Install anyway** (danger) and **Cancel** (focused).
- **States:** name mismatch keeps the button disabled. Moving: locked.
- **Safety and driving rules:** typed confirm, Parked only; the item is labelled
  "Sideloaded" in My library and App info for as long as it is installed.
- **Components:** Sheet, ListRow, text field, Button (danger).
- **Spec refs:** [ADR-0033][adr-33], [app model §8][am-8] · [Store §8][st-8].
- **Open questions:** none.

## Open questions for the owner (Store)

All seven were answered on 2026-10-07.

1. **Decided (items 33 and 62):** no ratings: no stars, reviews or download counts. Items
   show the review level, badges, last update, the publisher's known issues and the
   item's issue tracker ([Store §11][st-11]).
2. **Decided (item 34):** no paid items in v1; a publisher may link a donation page.
3. **Decided (item 30):** review levels System, First party, Verified publisher,
   Community (data objects and declarative items anywhere; code only as iframes on web
   hosts) and Sideloaded ([Store §6.1][st-6.1]).
4. **Decided (item 29):** a signed catalogue in TUF-style roles with Ed25519 keys and a
   small verifier of our own; every release signed by its publisher's key; an owner may
   add a publisher key locally, never remotely ([Store §5][st-5]).
5. **Decided (item 32):** the online catalogue is opt-in, off by default, one switch at
   first run, and comes after its own ADR; it is a set of signed static files in the
   `ostler-catalogue` repo that anyone can mirror ([Store §5][st-5], [§7][st-7]).
6. **Decided (item 28):** the Store is a system app, owner `os`.
7. **Decided (item 49):** icon packs are glyph sets mapped to Material Symbols names;
   safety icons never change. *Amended (openness round): safety icons may be restyled under
   the render check.*

<!-- refs -->
[adr-13]: ../../../../decisions/adr-0013-repo-split-and-vehicle-pack-contract.md
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[adr-41]: ../../../../decisions/adr-0041-brain-ed25519-signing.md
[adr-42]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md
[am-4.1]: ../../../../specs/2026-10-06-app-model-design.md#41-shape
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[am-8]: ../../../../specs/2026-10-06-app-model-design.md#8-explicit-non-goals-and-hard-lines
[am-11]: ../../../../specs/2026-10-06-app-model-design.md#11-open-questions-for-the-owner
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[ha-arch-8]: ../../../research/ha_architecture_addons.md#8-copy--avoid--decide-for-ostler
[ha-comm-9]: ../../../research/ha_companion_community.md#9-copy--avoid--decide-for-ostler
[hub-1]: ../../../../specs/2026-10-07-community-hub-design.md#1-purpose-and-non-goals
[hub-14]: ../../../../specs/2026-10-07-community-hub-design.md#14-moderation-and-abuse
[st-3]: ../../../../specs/2026-10-07-store-design.md#3-the-store-app
[st-5]: ../../../../specs/2026-10-07-store-design.md#5-the-catalogue-and-signing
[st-7]: ../../../../specs/2026-10-07-store-design.md#7-the-bundled-offline-catalogue
[st-8]: ../../../../specs/2026-10-07-store-design.md#8-sideloading-for-developers
[st-11]: ../../../../specs/2026-10-07-store-design.md#11-ratings-and-paid-items-owner-decisions
[st-6.1]: ../../../../specs/2026-10-07-store-design.md#61-review-levels
