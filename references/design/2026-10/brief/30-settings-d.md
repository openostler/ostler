---
title: "Designer brief: Settings (part D): sharing defaults, storage, recording and backups"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0041-brain-ed25519-signing.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Part D of the Settings brief. It covers a Proposed Sharing defaults page (the trip share
  levels L0 Card to L4 Diagnostics, which audiences each may reach among a friend, a group,
  the household, a link and the public, and the owner's defaults for expiry, max speed and
  Locked or Download), a Proposed Storage page (disk use by recordings, captures, trips,
  audio, maps and apps, and the automatic rotation at low space), a New Recording sources
  page (audio and acceleration opt-in per device, the identity-recording install option shown
  read-only), a Proposed Backups page (schedule and destination) and a Proposed four-step
  Restore flow.
---

# Settings brief, part D: Sharing defaults, Storage, Recording, Backups

Tree, shared rules and the Settings lock: [part A](30-settings-a.md). Sharing itself ("who
sees what", S8) is the Existing `accounts-s8`; the share sheet is `trips-share-sheet`.

### settings-sharing-defaults — Sharing defaults  [Proposed]
- **Owner:** app:trips
- **Purpose:** show what each share level holds and where it may go, and set the owner's own
  defaults inside those rules.
- **Why proposed:** the share sheet pre-selects fixed defaults ([UI §13.1][ui-13.1]); owners
  who share often want their own expiry and max-speed defaults, and need the level ladder
  explained once, outside a share.
- **Opens from → goes to:** Sharing (`accounts-s8`) → Defaults; the share sheet's "Change
  defaults" link. Goes to Places (ends trim and zones).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, tablet Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. **Levels** (read-only ladder, five stacked rows, L0 top): "L0 Card: the day, the area,
     distance and time. No map." · "L1 Route: your route with the first and last 500 m and
     private places hidden." · "L2 Telemetry: chosen readings such as speed, RPM, coolant,
     boost, on time from the start." · "L3 Full log: everything the car's computers said;
     VIN removed; named people only." · "L4 Diagnostics: fault codes, freeze frames and
     module information; named people only." L3 and L4 rows use the `warn` token.
  2. **Audiences** matrix (read-only), rows Me · A friend · A group · Household · Anyone
     with the link · Public (Ostler Community); columns L0–L4; cells show a `check` icon or are
     greyed with the reason ("Telemetry is never public", "Full logs go to named people
     only"). Link: L0–L1 only; Public: L0–L1 by explicit publish, routes 24 h after the trip.
  3. **Starting level by place** (Segmented each): Trips "L0", Diagnose "L4", Decode lab
     "L3" (spec defaults, editable within the audience rules).
  4. **Default expiry**: Segmented "1 h · End of day · 7 days · 30 days · Until I stop"
     (only lengths the class allows).
  5. **Default mode for links**: Segmented "Locked · Download"; caption "Locked stops casual
     copies. Anyone who can see data can still copy it."
  6. Switch "Show max speed on link and public cards" (off by default).
  7. Row "Ends trim and privacy zones · ‹500 m› · ‹n› places" → Places.
- **States:** loading; error; Parked full; Moving: the Settings lock; locked: owner only;
  other users see the read-only parts.
- **Safety and driving rules:** no default can widen an audience beyond the registry
  ([Accounts §15.2][acc-15.2]); public is never a default; L3–L4 never go to a link or public.
- **Components:** ListRow, Segmented, Switch (new), a matrix table (new component: rows ×
  columns of icon cells, a greyed cell explains itself on tap), Card.
- **Spec refs:** [Trip sharing §3][ts-3], [Trip sharing §10][ts-10], [UI §13.1][ui-13.1],
  [Accounts §15.2][acc-15.2], [Accounts §15.4][acc-15.4].
- **Open questions:** may the owner change the starting level per place, or are those fixed?

### settings-storage — Storage  [Proposed]
- **Owner:** os
- **Purpose:** how much space is used, by what, and what happens when it runs low.
- **Why proposed:** recordings rotate out silently below 200 MB free
  ([session logbook][slb]); owners need to see it coming and free space on purpose.
- **Opens from → goes to:** Settings → Storage; a "Storage low" card on Home. Goes to Trips,
  Recording sources, Maps (`maps-regions`), Apps, Backups.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Hero: "‹used› of ‹total› used" with a stacked bar (series tokens, at most three plus
     "Other"), on the Brain; a second bar for the phone app's own store where it has one.
  2. Rows with sizes: Trips and recordings (‹n› trips), Raw captures (K-line `kline-diag`
     bus taps for decoding), Audio (only if turned on), Offline maps, App data, System.
  3. **When space runs low** (read-only): "Below 200 MB free, the oldest trips are deleted
     first. Trips you've shared stay until their shares end." A Switch "Warn me at 1 GB free".
  4. **Keep trips** Segmented "Until space runs low · 1 year · 90 days" (Proposed).
  5. Buttons: "Delete raw captures older than 30 days", "Clear map cache".
- **States:** loading; error; Brain absent (Ostler Diagnostics alone: "Recordings live on
  your phone"); low space (`warn` Card); Parked full; Moving: the lock.
- **Safety and driving rules:** recording is always on and cannot be paused
  ([ADR-0011][adr-0011]); deletes confirm with Cancel focused; owner only.
- **Components:** HeroStat, stacked bar (new component), ListRow, Button, Card.
- **Spec refs:** [session logbook][slb], [ADR-0009][adr-0009], [ADR-0011][adr-0011],
  [UI §12.2][ui-12.2].
- **Open questions:** should a retention period exist at all, given ADR-0009 says "no setting
  in v1"?

### settings-recording — Recording sources  [New]
- **Owner:** app:trips
- **Purpose:** the per-device opt-ins for what a trip records besides the car.
- **Opens from → goes to:** Storage → Recording sources (today Preferences → "Recording &
  flags"). Goes to the flag manager.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Switch "Record cabin audio from this device" (off): "Stays on this device. Never shared,
     never uploaded."
  2. Switch "Record acceleration from this device" (off), with "Calibrate" (Parked, level
     ground).
  3. **Identity data in recordings** (read-only): "Off · set in the install configuration.
     When off, the VIN and identity replies are replaced before anything is stored."
  4. Row "Flags on the transport" → the flag manager.
- **States:** no microphone or motion sensor ("This device has no ‹sensor›"); permission
  denied (link to the OS setting); not HTTPS ("Needs a secure connection"); Parked full;
  Moving: the lock.
- **Safety and driving rules:** the identity option cannot be set here, remotely, by a pack
  or by an MCP client ([ADR-0036][adr-0036] §1).
- **Components:** Switch (new), ListRow, Button.
- **Spec refs:** [ADR-0010][adr-0010], [ADR-0036][adr-0036].
- **Open questions:** none.

### settings-backups — Backups  [Proposed]
- **Owner:** os
- **Purpose:** keep a copy of settings, users and trips somewhere else, on a schedule.
- **Why proposed:** a lost or failed SD card loses everything; Home Assistant's backup model
  is in the research round ([ADR-0042][adr-0042]) with no spec yet.
- **Opens from → goes to:** Settings → Backups. Goes to Restore (`settings-restore`) and
  Ostler Link.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Status Card: "Last backup ‹date› · ‹size› · ‹destination›", or `warn` "No backup yet".
  2. **Schedule**: Segmented "Off · Daily · Weekly"; "Keep the last ‹3›".
  3. **What**: rows Settings and layouts (always), Users and sign-ins (encrypted), Trips
     (Switch, sizes), App data.
  4. **Where**: Segmented "USB drive · Network folder · Ostler Link"; Ostler Link shows
     "Encrypted on this car before it leaves" and needs the subscription.
  5. **Backup password** (shown once at set-up; "Without it the backup can't be opened").
  6. Buttons "Back up now" (primary), "Restore from a backup".
- **States:** empty; running (progress); error ("USB drive not found"); offline (Ostler Link
  waits); Brain absent ("Needs the Brain"); Parked full; Moving: the lock.
- **Safety and driving rules:** owner only; the Brain's signing key and the VIN are never in
  a backup ([ADR-0041][adr-0041], [ADR-0036][adr-0036]); Ostler Cloud never holds `auth.db`
  readable ([Accounts §14.10][acc-14.10]).
- **Components:** Card, Segmented, Switch (new), ListRow, Button, progress bar (new).
- **Spec refs:** [ADR-0042][adr-0042], [Accounts §14.10][acc-14.10], [ADR-0041][adr-0041].
- **Open questions:** may an encrypted copy of `auth.db` go to Ostler Link at all, given
  §14.10 says the cloud never holds it?

### settings-restore — Restore from a backup  [Proposed]
- **Owner:** os
- **Purpose:** bring a backup back onto this Brain, or onto a new one.
- **Why proposed:** the other half of Backups; also the first-run path after a lost card.

| Step | Screen | The user | Can fail · recovery |
|---|---|---|---|
| 1 | settings-restore | picks the source (USB drive, network folder, Ostler Link) and a backup | none found · "Choose another place" |
| 2 | settings-restore | types the backup password | wrong · five tries, then wait 15 min |
| 3 | settings-restore | reviews what will be replaced and ticks parts | newer than this version · "Update Ostler first" |
| 4 | settings-restore | confirms (Cancel focused); the Brain restarts | fails mid-way · the old data is kept and restored |

- **Opens from → goes to:** Backups → Restore; first run ("Restore from a backup"). Ends at
  sign-in (`accounts-s2`).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):** step header "Step ‹n› of 4"; the step's list or field; a
  summary Card in step 3 ("Settings · 2 users · ‹n› trips · layouts"); Back and Next.
- **States:** loading; error per step as the table; Parked full; Moving: the lock.
- **Safety and driving rules:** Parked only; owner only; nothing reaches the car; paired
  phones re-confirm after a restore onto new hardware.
- **Components:** ListRow, password field (new component), Card, Button, Sheet.
- **Spec refs:** [ADR-0042][adr-0042], [Accounts §14.10][acc-14.10].
- **Open questions:** none.

<!-- refs -->
[acc-14.10]: ../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery
[acc-15.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142
[acc-15.4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412
[adr-0009]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[adr-0010]: ../../../../decisions/adr-0010-replay-notes-audio-motion.md
[adr-0011]: ../../../../decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md
[adr-0036]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[adr-0041]: ../../../../decisions/adr-0041-brain-ed25519-signing.md
[adr-0042]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md
[slb]: ../../../../specs/2026-10-05-session-logbook-design.md#recording-rules-sessionrecorder
[ts-10]: ../../../../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls
[ts-3]: ../../../../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-13.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#131-the-trips-share-sheet-changes-122s-trip-detail-share-and-export
