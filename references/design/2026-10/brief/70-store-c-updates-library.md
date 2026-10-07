---
title: "Designer brief: Store (part C): updates, auto-update, rollback, My library and uninstall"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, references/research/ha_architecture_addons.md]
summary: >
  Part C of the Store brief: keeping items current and managing what is installed. The
  updates list shows waiting updates with changelogs and "Update all"; auto-update settings
  choose per kind and per item, with Wi-Fi-only and Parked-only rules that cannot be relaxed;
  a rollback sheet returns an item to its kept previous version. The Existing
  `addons-catalogue` screen keeps its ID and becomes My library: installed and previously
  installed items, reinstall, uninstall and "Finish setup". An uninstall sheet says what
  happens to the item's data and offers an export first.
---

# Store brief, part C: updates and My library

Parts: [A: rules, home, browse](70-store-a-home-browse.md) ·
[B: item detail and install](70-store-b-item-install.md) · **C** (this file) ·
[D: publisher, report, offline, sideload](70-store-d-publisher-sideload.md).
OS, firmware and Brain updates are Settings → Updates (`settings-updates`, settings brief
part E); this file covers Store items only, and `settings-updates` links here for apps.

### store-updates — Updates  [Proposed]
- **Owner:** os
- **Why the app needs it:** packs and apps change often (a pack's proven signals grow with
  each capture); owners need one list to review and apply updates.
- **Purpose:** list every installed item with an update, with what changed, and apply them.
- **Opens from → goes to:** `store-home` **Updates** button (count badge); Settings →
  Updates → Apps row; the "Updates ready" notification. Goes to `store-item-versions`,
  `store-install-sheet` (an update that asks for more), `store-update-settings`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Title "Updates"; gear icon button → `store-update-settings`.
  2. Summary line: "3 updates · ‹size› · Last checked ‹time›" and **Check now**.
  3. **Update all** (primary) — skips items that ask for more; those wait for review.
  4. One ListRow per item: icon, name, "‹old› → ‹new›", size, the first changelog line
     ("SLABS: front-left height now proven"), **Update** button. Badges: `warn` "Asks for
     more: Location"; "Breaking: update by hand"; "Beta".
  5. **Recently updated** (last 30 days): rows with "Updated ‹date›" and a **Roll back**
     link (→ `store-rollback`).
  6. **Waiting**: rows paused for a reason: "Waits until you park", "Waits for Wi-Fi",
     "Needs Ostler ‹x.y›: update Ostler first" (→ `settings-updates`).
- **States:** empty: "Everything is up to date" with the last-checked time. Loading: "Checking…".
  Error: "Couldn't check for updates · Retry". Offline: "Offline · updates from a file:
  Install from a file" (Developer mode) or the bundled catalogue's newer items after an OS
  update. Moving (head unit): locked view; (phone): list readable, buttons read **Update when
  parked**. Locked (not owner): list readable, no buttons, "Only an owner can update".
- **Safety and driving rules:** no update starts or finishes while Moving; never over a
  metered link over its quota ([ADR-0028][adr-28]); an update that adds a data class, an
  action or a host asks again through `store-install-sheet` and is never auto-applied.
- **Components:** ListRow, Button, Chip (status), Card (summary).
- **Spec refs:** [app model §7][am-7] (SemVer, "Needs Ostler x.y"), [HA research §3.3][ha-arch-3.3]
  (channels, `breaking_versions`, rollback), [UI §12.4][ui-12.4].
- **Open questions:** none.

### store-update-settings — Auto-update  [Proposed]
- **Owner:** os
- **Why the app needs it:** a car Brain sleeps, roams on mobile data and must never update
  while driving; owners need to choose what updates by itself and when.
- **Purpose:** choose when items update themselves, per kind and per item.
- **Opens from → goes to:** `store-updates` gear; Settings → Updates → "App updates". Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):**
  1. **Update automatically** Segmented: "Off · Security fixes only · All" (default
     "Security fixes only").
  2. **Per kind** toggles: Apps · Integrations and vehicle packs · Widgets · Looks (themes,
     icon packs, wallpapers, gauge styles) · Dashboards · Sound and EQ.
  3. **When**: "Only on Wi-Fi or Ethernet" (on; can be turned off only for items under
     ‹size›), "Only when parked" (on, shown locked with `lock` icon and "Always on"),
     "Preferred time" ("Overnight while charging", "When the Brain next wakes").
  4. **Channel**: "Stable" (default) · "Beta" per item, in the item list below.
  5. **Per item**: ListRows with a three-way control "Follow the default · Always ·
     Never".
  6. **Keep the previous version for rollback** (on) with the space it uses.
  7. Caption: "Updates that ask for more access always wait for you."
- **States:** loading; not owner: read-only with "Only an owner can change this". Offline:
  editable. Moving: the Settings lock (locked view).
- **Safety and driving rules:** "Only when parked" cannot be turned off; the screen is
  Parked only on head units.
- **Components:** Segmented, toggle (as Segmented "On · Off"), ListRow, Card (caption).
- **Spec refs:** [ADR-0028][adr-28] (metered uplinks), [HA research §8][ha-arch-8] (Copy 4,
  Avoid 6).
- **Open questions:** should "Security fixes only" be the default, and who labels a release
  as a security fix?

### store-rollback — Roll back  [Proposed]
- **Owner:** os
- **Why the app needs it:** a pack or app update can break reading on one car; the owner
  needs a one-step return to the last version that worked.
- **Purpose:** confirm going back to an item's kept previous version.
- **Opens from → goes to:** `store-updates` **Roll back**; `store-item-versions` **Roll
  back to this version**; App info's update section (`90-appframe-*`). Confirm →
  `store-installing` (rollback wording) → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):**
  1. Title "Roll back ‹item›?"; line "From ‹new› to ‹old›".
  2. What happens: "Your settings are kept." "Data made by the newer version may not open
     in the older one." For a pack: "Signals added in ‹new› go back to their old status."
  3. Checkbox "Don't update this item automatically" (on by default).
  4. Buttons **Roll back** (primary) and **Cancel** (focused on head units).
- **States:** no kept version: "No previous version is kept on this Brain" and **Find it in
  version history** (online). Offline: works if the previous version is kept. Moving: locked.
  Not owner: never reached.
- **Safety and driving rules:** owner only, Parked only, local link.
- **Components:** Sheet, Button, checkbox (ListRow with a check).
- **Spec refs:** [HA research §3.3][ha-arch-3.3] (rollback), [app model §5][am-5].
- **Open questions:** none.

### addons-catalogue — My library  [Existing]
- **Owner:** os
- **Purpose:** what is installed on this Brain (and what was), with update, setup,
  reinstall and uninstall. It keeps the ID of the old More → Add-ons screen and replaces
  its Available tab with the Store home.
- **Opens from → goes to:** `store-home` **My library**; the app drawer's long-press menu
  "Manage in the Store"; Settings → Apps (each row still opens App info). Goes to
  `store-item`, `store-uninstall`, App info (`90-appframe-*`), the app's setup flow.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (lock).
- **Content (top to bottom):**
  1. Title "My library"; Segmented tabs **Installed · Previously installed**.
  2. Kind filter Chips: All · Apps · Integrations · Widgets · Looks · Dashboards · Sound.
  3. **Installed**: one ListRow per item: icon, name, version, kind Chip, labels **System**
     (Settings, Store: no uninstall), **Preinstalled** (from the flavour), **Developer**,
     **Runs on the Brain**; trailing: **Update**, **Finish setup** (setup was skipped) or
     a chevron. Row menu: Open · App info · Version history · Uninstall. Example rows:
     "Diagnostics · Preinstalled", "Trips · Preinstalled", "Ostler pack for Land Rover
     Discovery 2 · Integration · In use by Discovery 2 Td5", "Starter widgets · Widget
     pack", "Default theme · Theme · In use".
  4. **Previously installed**: rows with "Removed ‹date›", "Data kept" or "Data deleted",
     **Reinstall** (→ `store-install-sheet`, permissions are asked again).
  5. Footer: storage line "Apps use ‹size› on the Brain" → `settings-storage`.
- **States:** empty Installed: impossible (System items always show). Empty Previously
  installed: "Nothing removed yet". Loading: skeleton rows. Offline: full (all local);
  Reinstall works for items kept or bundled, else "Needs the internet". Moving (head unit):
  locked view, "Available when parked" + Open on phone ([UI §12.1][ui-12.1]). Moving
  (phone): readable, buttons wait for Parked. Locked (not owner): readable, no buttons.
- **Safety and driving rules:** install, update and removal are owner operations on local
  links, Parked only ([UI §12.4][ui-12.4]); System items cannot be removed; nothing here
  removes a safety item.
- **Components:** Segmented (tabs), Chip, ListRow, Card (labels), Button.
- **Spec refs:** [UI §12.4][ui-12.4], [app model §14.2][am-14], [ADR-0042 §5][adr-42].
- **Open questions:** the approved spec's "Core cannot be removed" now means System only;
  may preinstalled apps such as Diagnostics be removed (the new direction says yes)?

### store-uninstall — Uninstall  [Proposed]
- **Owner:** os
- **Why the app needs it:** removing an app or a vehicle pack has effects on data and on
  reading the car; the exit guarantee says data can leave in an open format first.
- **Purpose:** confirm removal and choose what happens to the item's data.
- **Opens from → goes to:** `store-item` and `addons-catalogue` **Uninstall**; App info
  (`90-appframe-*`). Confirm → `addons-catalogue` with an undo toast for the removal of
  looks (theme, wallpaper), none for apps.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):**
  1. Title "Uninstall ‹item›?".
  2. **What goes:** its pages, widgets and dashboards ("2 widgets on your home pages will
     be removed"), its shortcuts in the dock.
  3. **Your data** RadioOpt rows: "Keep my data on this Brain" (default) · "Delete my data"
     (`alarm` tone). **Export first** button (open formats, [ADR-0042 §7][adr-42]).
  4. Warnings in a `warn` Card when they apply: for a vehicle pack in use: "Your Discovery
     2 Td5 will not be read until a pack is installed. Generic OBD-II stays available."
     For an app that holds Security alerts: "Alarm alerts stay on; only this app's pages go."
  5. Buttons **Uninstall** (danger) and **Cancel** (focused on head units).
- **States:** System item: never offered. Moving: locked. Not owner: never reached.
  Offline: works.
- **Safety and driving rules:** owner only, Parked only; safety items stay with the OS
  ([Drive modes §8.1][dm-8.1]); the fault telltale stays even with no Diagnostics app.
- **Components:** Sheet, RadioOpt (ListRow with a radio), Card (`warn`), Button (danger).
- **Spec refs:** [ADR-0042 §7][adr-42] (exit guarantee), [Drive modes §8.1][dm-8.1].
- **Open questions:** may Security be uninstalled while the car is armed?

<!-- refs -->
[adr-28]: ../../../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[adr-42]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ha-arch-3.3]: ../../../research/ha_architecture_addons.md#33-backups-updates-channels
[ha-arch-8]: ../../../research/ha_architecture_addons.md#8-copy--avoid--decide-for-ostler
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
