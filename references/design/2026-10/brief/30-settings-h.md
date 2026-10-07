---
title: "Designer brief: Settings (part H): about, licences, legal, report a problem and reset"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-phone-comms-addon-design.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md]
summary: >
  Part H of the Settings brief. It covers a New About page (versions of the platform, pack,
  firmware and apps; the version line whose long-press is the service-mode entry; the
  "Using Ostler while driving" page), Proposed Licences and credits (the network-use source
  offer, data and font licences, third-party notices, map attribution), a Proposed Legal and
  privacy policy page, a Proposed Report a problem flow built on the scrubbed diagnostics
  bundle and its verifier, a New Reset page (Reset layout from the drive-modes spec, always
  reachable, with Undo reset) and a Proposed four-step Factory reset flow.
---

# Settings brief, part H: About and Reset

Tree, shared rules and the Settings lock: [part A](30-settings-a.md). "Using Ostler while
driving" is the Existing `shell-driving-page`; the Reset layout sheet is the Existing
`shell-reset-confirm`; service mode is the Existing `shell-service-mode`.

### settings-about — About  [New]
- **Owner:** os
- **Purpose:** what this Ostler is, which versions run, and the doors to help and legal text.
- **Opens from → goes to:** Settings → About (More → About in the UI spec). Goes to Using
  Ostler while driving, Licences, Legal, Report a problem, Updates; a long-press on the
  version line starts service mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Product line: "Ostler" with the setup ("Brain and Diagnostics node" or "Ostler
     Diagnostics alone").
  2. **Version line** (a ListRow, no chevron): "Ostler ‹version› · ‹month year› release".
     A long-press (600 ms) asks for the server password and turns on service mode. No hint is
     drawn on the row.
  3. **Versions**: Vehicle pack "Land Rover Discovery 2 Td5 · ‹version›"; Node firmware
     "‹version›"; Companion app "‹version›" (phone only); each app "‹name› ‹version›".
  4. Rows: "Using Ostler while driving", "Updates", "Licences and credits", "Legal and
     privacy policy", "Report a problem", "Ostler Community and help" (opens the hub, or
     "Install Ostler Community").
  5. Footer caption: "Made in the open. The code is yours to read and change."
- **States:** loading versions; a device offline ("Node · offline since ‹time›", version
  "—"); Parked full; Moving: the Settings lock (service-mode entry refused); locked (Car
  profile): visible; the long-press still asks for the password.
- **Safety and driving rules:** service mode is refused and exits when Moving
  ([UI §3.5][ui-3.5]); the "Using Ostler while driving" page is required here
  ([UI §12.1][ui-12.1]).
- **Components:** ListRow, Card.
- **Spec refs:** [UI §3.4][ui-3.4], [UI §3.5][ui-3.5], [UI §12.1][ui-12.1].
- **Open questions:** none.

### settings-licences — Licences and credits  [Proposed]
- **Owner:** os
- **Purpose:** the source offer, every licence Ostler ships under, and who made it.
- **Why proposed:** the code licence's network clause means anyone using Ostler over a
  network must be offered the source ([ADR-0012][adr-0012]); fonts, icons and map data carry
  notice duties ([visual §12][vds-12]).
- **Opens from → goes to:** About → Licences and credits. Each row → a text page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. **Source code**: "Get the source for this exact version" (a link to the tagged source,
     and "Save source archive", kept on the Brain for offline use).
  2. **Ostler**: "Code: GNU Affero General Public License, version 3 or later. A commercial
     licence is available." "Vehicle data and packs: Creative Commons Attribution-ShareAlike
     4.0."
  3. **Third-party software**: a searchable list from the shipped notices, each name with its
     licence name and full text on tap.
  4. **Fonts and icons**: Figtree (SIL Open Font License 1.1), Material Symbols (Apache
     License 2.0).
  5. **Map data**: "© OpenStreetMap contributors", "© OpenMapTiles" when online styles are used.
  6. **Credits**: contributors, the vehicle pack's maintainers, and the open projects reused.
- **States:** loading; offline (texts are bundled, so it works); Parked full; Moving: lock.
- **Safety and driving rules:** the Settings lock only.
- **Components:** ListRow, search field, a long-text page (new component: `type-body`, mono
  for licence text, Parked only).
- **Spec refs:** [ADR-0012][adr-0012], [visual §12][vds-12].
- **Open questions:** none.

### settings-legal — Legal and privacy policy  [Proposed]
- **Owner:** os
- **Purpose:** the terms that apply to this device and the privacy policy in plain words.
- **Why proposed:** hardware sales and the cloud subscription need a privacy notice and
  terms ([UI §12.1][ui-12.1] names a product-liability opinion due before sales).
- **Opens from → goes to:** About → Legal and privacy policy; Ostler Link; first run.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):** rows "Privacy policy (this device)", "Ostler Link terms",
  "Ostler Community terms", "Trademarks", "Safety notice: using Ostler while driving"; each
  opens a long-text page with the date it was last changed.
- **States:** offline (bundled); Parked full; Moving: the lock.
- **Safety and driving rules:** the Settings lock only.
- **Components:** ListRow, long-text page (new).
- **Spec refs:** [UI §12.1][ui-12.1], [ADR-0012][adr-0012].
- **Open questions:** who writes the texts, and which apply without a subscription?

### settings-report-problem — Report a problem  [Proposed]
- **Owner:** os
- **Purpose:** send the maintainers what they need to fix a fault in Ostler or the pack.
- **Why proposed:** the L4 bundle, its scrub and its verifier already exist for help with a
  car fault ([Trip sharing §13][ts-13]); a report about Ostler itself has no entry.

| Step | Screen | The user | Can fail · recovery |
|---|---|---|---|
| 1 | settings-report-problem | picks "Ostler", "The vehicle pack" or "An app" and writes what happened (Parked) | — |
| 2 | settings-report-problem | ticks what to attach: platform log tail, the last trip's L4 bundle, screenshots | verifier fails · the failing rule and what to untick |
| 3 | settings-report-problem | sees the redaction chips ("VIN ×3", "No GPS", "Relative time") | — |
| 4 | settings-report-problem | sends: Save file, Copy for a pack issue, or Ask on Ostler Community | offline · "Saved; send it later" |

- **Opens from → goes to:** About → Report a problem; an app log; an error toast's
  "Report". Ends on "Sent" or the saved file.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night, desktop Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):** step header; text box; attach ListRows with sizes; the
  redaction Chip row; the warning line "This can't be taken back once sent" for file and
  issue paths; Send Buttons naming the path.
- **States:** loading; verifier fail; offline; Parked full; Moving: the lock.
- **Safety and driving rules:** typing Parked only; the VIN-pattern block has no "send
  anyway" ([Trip sharing §3][ts-3] R3); public paths force no location and relative time.
- **Components:** text field, ListRow (checkbox), Chip, Card (warn), Button.
- **Spec refs:** [Trip sharing §3][ts-3], [Trip sharing §10][ts-10],
  [Trip sharing §13][ts-13].
- **Open questions:** does a report go to the pack's issue tracker or the hub by default?

### settings-reset — Reset  [New]
- **Owner:** os
- **Purpose:** put layouts back, or wipe this Ostler, from one always-reachable page.
- **Opens from → goes to:** the app drawer's Reset layout row (it can't be hidden, moved out of the drawer
  or renamed); Settings → Reset; the Connection sheet's row. Goes to the Reset layout sheet
  (`shell-reset-confirm`) and Factory reset.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night, hu7 Night dim Moving ("Park to edit").
- **Content (top to bottom):**
  1. **Reset layout** → the sheet: "This surface", "Everything on this screen", "All screen
     sizes"; Cancel focused. Caption: "Your presets don't change."
  2. **Undo reset** (only within 7 days): "Restore the layout from before ‹date›".
  3. **Reset settings** (owner): display, units and alert settings back to defaults; users,
     trips and pairings stay.
  4. **Factory reset** (owner, danger text) → the flow below.
- **States:** no snapshot (row 2 hidden); Parked full; Idling with Park evidence as Parked;
  Moving: "Park to edit" for rows 1–3 (the page itself stays reachable), row 4 locked.
- **Safety and driving rules:** Reset is an edit, so Park to edit ([Drive modes §7.8][dm-7.8],
  R1); every confirm opens with Cancel focused; reset never removes safety items or the app drawer.
- **Components:** ListRow, Sheet, Button (danger).
- **Spec refs:** [Drive modes §7.8][dm-7.8], [Drive modes §8.1][dm-8.1],
  [UI §15.2][ui-15.2].
- **Open questions:** none.

### settings-factory-reset — Factory reset  [Proposed]
- **Owner:** os
- **Purpose:** wipe users, data and pairings before selling or handing on the car or Brain.
- **Why proposed:** factory reset is named (setup mode starts after it, [ADR-0039][adr-0039]
  §7; "Forget all phones", [Phone & Comms §13][pc-13]; `auth.db` wiped,
  [Accounts §12][acc-12]) but has no screen.

| Step | Screen | The user | Can fail · recovery |
|---|---|---|---|
| 1 | settings-factory-reset | reads what goes: users, trips, captures, pairings, layouts, app data | — |
| 2 | settings-factory-reset | offered "Export my data" and "Back up now" first | backup fails · retry or skip |
| 3 | settings-factory-reset | types "RESET" and signs in again as owner (password or passkey) | wrong sign-in · five tries, then wait |
| 4 | settings-factory-reset | confirms (Cancel focused); the Brain wipes and restarts in setup mode | power lost mid-way · it resumes the wipe at boot |

- **Opens from → goes to:** Reset → Factory reset. Ends on the Brain's setup screen
  (onboarding brief `setup-welcome`).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu7
  Night, phone Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):** an `alarm-bg` Card listing what is deleted; the export and
  backup rows; the typed field; Button "Erase everything" (danger).
- **States:** progress ("Erasing… don't switch off"); error; Parked full; Moving: the lock.
- **Safety and driving rules:** Parked and owner only, on a local link; nothing is sent to
  the car; node and module resets are on their device pages (the hardware brief).
- **Components:** Card (alarm tone), ListRow, text field, Button (danger).
- **Spec refs:** [ADR-0039][adr-0039], [Accounts §12][acc-12], [Phone & Comms §13][pc-13].
- **Open questions:** does a Brain reset also reset the node's roster, or only on the node's
  own page?

<!-- refs -->
[acc-12]: ../../../../specs/2026-10-06-accounts-sharing-design.md#12-threat-notes-feed-referencesthreat_modelmd
[adr-0012]: ../../../../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md
[adr-0039]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[pc-13]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#13-security
[ts-10]: ../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls
[ts-13]: ../../../../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose
[ts-3]: ../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[vds-12]: ../../../../specs/2026-10-07-visual-design-system-design.md#12-licences
