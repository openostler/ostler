---
title: "Designer brief: Settings (part A): tree, rules, Settings app, Display, Units and region"
area: references
status: draft
version: 0.4
updated: 2026-10-07
depends_on: [references/design/2026-10/README.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Part A of the Settings brief for the designer, revised for the owner's Android-style OS
  direction. It gives the whole tree of the system Settings app (an OS app in the app drawer),
  with every page's tag, owner (os or an app) and moving-state behaviour, an Apps section that
  opens each installed app's App info page, and a Wallpaper & style row that opens the theme
  wizard; the rules every Settings page shares (the Settings lock while Moving, Park to edit,
  honest states, owner-only rows); and the page blocks for the Settings root, Display (the
  Existing `preferences` screen: themes Night, Day, Night dim, Deep night, Auto, map theme,
  brightness, text size, dock and Lock car layouts) and Units, language and region. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# Settings brief, part A: tree, shared rules, Settings app, Display, Units

Parts: **A** (this file) · [B: Alerts and Driving rules](30-settings-b.md) ·
[C: Privacy and data](30-settings-c.md) · [D: Sharing, Storage, Backups](30-settings-d.md) ·
[E: Updates, Profiles, Accounts](30-settings-e.md) · [F: Apps and Maps](30-settings-f.md) ·
[G: Developer](30-settings-g.md) · [H: About and Reset](30-settings-h.md).
Process and the constraints checklist: [design hand-off README][readme].

## 1. The tree

Ostler is now an Android-style OS: system Settings is an **OS app** in the app drawer (once
"More"), with the Store client, the launcher and first-run setup beside it. Everything else
(Diagnostics, Trips, Security, Maintenance, Phone, Map and the rest) is an app with its own
settings in its own area; Settings reaches them through **Apps → App info**. The app drawer
keeps Edit layout and Reset layout reachable (never hideable, [Drive modes §7.8][dm-7.8]).
Tags: **E** Existing, **N** New, **P** Proposed. Owner: **os** or **app:‹name›**. Moving
column: **L** = the Settings lock (§2).

| Settings page | Screen id | Tag | Owner | Moving (head unit) |
|---|---|---|---|---|
| **Settings** (root) | `settings-root` | N | os | L |
| ├ Display | `preferences` | E | os | L |
| │ └ Wallpaper & style | theme wizard (`45-launcher-*`, by name) | link | os | "Park to edit" |
| ├ Units, language and region | `settings-units-region` | P | os | L |
| ├ Alerts: message alerts | `alert-settings` | E | os | L |
| ├ Notifications, quiet hours, critical alerts | `settings-notifications` | N | os | L |
| ├ Driving rules | `settings-driving` | N | os | L |
| ├ Privacy and data | `settings-privacy` | N | os | L |
| │ ├ What can be shared (data classes) | `settings-data-classes` | P | os | L |
| │ ├ Location | `settings-location` | P | os | L |
| │ ├ Ghost mode | `accounts-s9` (chip and sheet) | E, link | os | going ghost: one tap allowed |
| │ ├ Usage and crash reports | `settings-usage-reports` | P | os | L |
| │ ├ Export my data | `settings-export-data` | P | os | L |
| │ └ Delete my data | `settings-delete-data` | P | os | L |
| ├ Sharing ("who sees what") | `accounts-s8` | E, link | os | L |
| │ └ Trip sharing defaults | `settings-sharing-defaults` | P | app:trips | L |
| ├ Storage | `settings-storage` | P | os | L |
| │ └ Recording sources | `settings-recording` | N | app:trips | L |
| ├ Backups | `settings-backups` | N | os | L |
| │ └ Restore from a backup (flow) | `settings-restore` | N | os | L |
| ├ Updates | `settings-updates` | N | os | L |
| ├ Profiles and users | `settings-profiles` | N | os | L |
| │ ├ Users and roles | `accounts-s5` | E, link | os | L |
| │ └ Head-unit PIN | `settings-hu-pin` | N | os | L |
| ├ My account | `settings-account` | N | os | L |
| │ └ Ostler Link (cloud) | `settings-ostler-link` | P | os | L |
| ├ **Apps** (installed apps; each row → App info) | App info (`90-appframe-*`, by name) | link | os | L |
| │ ├ Store (get apps, integrations, packs, themes) | Store (`70-store-*`, by name) | link | os (system app) | L |
| │ ├ Security and locks | `security` | E, link | app:security | arming only |
| │ ├ Maps: offline regions | `maps-regions` | E | app:map | L |
| │ └ Phone | `phone-page` | E, link | app:phone | L |
| ├ Network | `network` | E, link | os | L |
| ├ Developer | `settings-developer` | N | os | L |
| │ ├ API tokens and scripts | `settings-api-tokens` | N | os | L |
| │ ├ New token (sheet) | `settings-token-create` | N | os | L |
| │ ├ Approve a sign-in code | `setup-device-code` (onboarding brief) | N, link | os | L |
| │ ├ Connected apps and MCP server | `settings-connected-apps` | N | os | L |
| │ ├ Platform log | `settings-platform-logs` | P | os | L |
| │ └ Raw bus | `decode-lab` (Sniff) | E, link | app:decode-lab | refused |
| ├ Service mode | `shell-service-mode` | E, link | os | refused, exits |
| ├ About | `settings-about` | N | os | L |
| │ ├ Using Ostler while driving | `shell-driving-page` | E, link | os | L |
| │ ├ Licences and credits | `settings-licences` | P | os | L |
| │ ├ Legal and privacy policy | `settings-legal` | P | os | L |
| │ └ Report a problem | `settings-report-problem` | P | os | L |
| └ Reset | `settings-reset` | N | os | "Park to edit" |
|   ├ Reset layout (sheet) | `shell-reset-confirm` | E, link | os | "Park to edit" |
|   └ Factory reset (flow) | `settings-factory-reset` | P | os | L |

**Apps section.** One row per installed app (icon, name, version, "Needs update" chip),
grouped "On this car" and "Integrations" (backend-only apps with just a setup page). A row
opens that app's **App info** (`90-appframe-*`): permissions and data classes, notifications,
storage, enable or disable, update, uninstall, and "Open app settings", which lands in the
app's own settings in its own area. **Get more apps** opens the Store (`70-store-*`). The
former app detail and Integrations pages are folded into App info and the Store; the
Integrations versus Apps split is decided: one Apps list, integrations labelled (item 56).

Pages owned by other briefs, by name only: the **device pages and firmware update** (the
hardware brief, `20-hardware-*`), **Places** (`places`, app:trips), **Passkeys**
(`accounts-s3`), **Signed-in devices** (`accounts-s6`), the **dock editor** and the **theme
wizard** (`45-launcher-*`), and **Trips → Export all** (`trips-export-all`).

## 2. Rules every Settings page shares

- **The Settings lock (L).** Every head-unit layout class is driver-facing
  ([UI §12.1][ui-12.1]). While Moving, or Idling without Park evidence, a Settings page shows
  the shell's locked view (`shell-locked-view`): "Available when parked" and **Open on phone**.
  Settings content is not reg 109 content, so **Passenger view is never offered** here. The
  page you were on comes back 3 s after Parked. The app drawer stays reachable (it is an anchor).
- **Park to edit.** Any edit on a head unit needs Parked or Idling with Park evidence; typing,
  PIN pads and keypads are Parked only ([UI §12.1][ui-12.1], [Drive modes §8.1][dm-8.1]).
- **The phone** is a passenger device: while Moving it shows the Moving banner and the page
  asks "I'm a passenger" once per trip, view-only; changes to a head unit's layout from the
  phone apply at that display's next Parked ([Drive modes §8.1][dm-8.1] R7).
- **Owner-only rows** show to other roles as read-only rows with a lock icon and "Owner only".
  The kiosk **Car** profile can read Display and Units but changes nothing that is owner-only.
- **Honest states** ([visual §8][vds-8]): "Needs the Brain" where a page lives on the Brain and
  it is asleep or absent (Ostler Diagnostics alone); "Not available on this car"; values the
  device does not have show "—".
- **Live values** in this brief are written ‹like this›: draw them with neutral sample text;
  never a fake vehicle, fake fault code or fake signal. The vehicle in every example is the
  Discovery 2 Td5 from the pack.
- **Look.** Settings pages are lists: ListRow, Segmented, Button, Card and Sheet from the kit
  ([visual §8][vds-8]). One new component is shared by all parts: **Switch** (new component:
  a pill toggle on `surface-3`, on = `accent` thumb with the word "On"; 48 px hit on phone,
  76 px on head units; focus ring as every control). Head units use 76 px rows and 18 px type
  at least; no glow on head units in the default look ([visual §1][vds-1]).

### settings-root — Settings app  [New]
- **Owner:** os
- **Purpose:** the system Settings app: one place for every OS setting, grouped, with the
  installed apps listed under Apps.
- **Status:** approved in principle by the owner (Android-style OS direction, 2026-10-07);
  it also answers the specs that say "Settings → …" (Alerts, Sharing, Connected apps,
  Scripts) while [UI §12.4][ui-12.4] had no Settings page.
- **Opens from → goes to:** the app drawer (Settings icon); a dock slot if pinned; a search
  result; the cog in a sheet. Goes to every page in the tree; Back returns to the app drawer.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night, hu7 Night dim Moving (the Settings lock), tablet Night
  (two panes: the root list 360 px and the open page).
- **Content (top to bottom):**
  1. Title "Settings"; a search field "Search settings" (Parked only on head units).
  2. Group **You**: My account (‹name› · ‹role›), Profiles and users, Alerts, Driving rules.
  3. Group **This car**: Display, Wallpaper & style (→ the theme wizard, `45-launcher-*`),
     Units, language and region, Storage, Backups, Updates.
  4. Group **Privacy and sharing**: Privacy and data, Sharing, Ghost (shows the visibility
     chip's state, "Ghost" or "Visible to ‹audience› · ‹time left›").
  5. Group **Apps**: "‹n› apps installed" → the Apps list (each row → App info); "Get more
     apps" → the Store.
  6. Group **Connections**: Network, My account → Ostler Link.
  7. Group **Advanced**: Developer, About, Reset.
  Each row: icon, title, one-line meta (for example "Night dim after dusk"), chevron.
- **States:** loading (row skeletons); offline (rows that need the Brain show "Needs the
  Brain"); no vehicle ("This car" group reads "No car connected" but stays usable); no apps
  installed (Apps reads "No apps yet" with "Open the Store"); Parked full; Idling as Parked,
  search only with Park evidence; Moving: the Settings lock; Passenger: not offered; locked
  (signed out): only Display, Units and About.
- **Safety and driving rules:** the Settings lock ([UI §12.1][ui-12.1]); search is text
  entry, so Parked only; safety rules stay with the OS, so no app's settings can change them.
- **Components:** ListRow, Card (group), search field (new component: a `surface-3` input
  with a `search` icon), TabBar.
- **Spec refs:** [UI §3.4][ui-3.4], [UI §12.4][ui-12.4], [UI §13.4][ui-13.4],
  [Phone & Comms §8][pc-8], [MCP §8][mcp-8], [Accounts §14.9][acc-14.9],
  [app UI model §8][ua-8].
- **Open questions:** **Decided (item 57):** the Settings app is in the app drawer and can
  be pinned to the dock like any app; Guardian's default dock holds it (item 42).

### preferences — Display  [Existing]
- **Owner:** os
- **Purpose:** how Ostler looks on this display: theme, auto switching, map theme,
  brightness, text size, dock and car layouts.
- **Opens from → goes to:** Settings → Display (once More → Preferences). Goes to the dock
  editor (`shell-rail-editor` today; `45-launcher-*`), the theme wizard and Units.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day, hu7 Night and Night dim, hu7 Night dim Moving (the Settings lock).
- **Content (top to bottom):**
  1. **Theme**: Segmented "Night · Day · Auto"; under Auto a row "At night use" with
     Segmented "Night · Night dim · Deep night" (Night dim on head units by default, Deep night
     for OLED). A caption per choice: "Night dim is darker for head units after dusk. Deep
     night is pure black for OLED screens."
  2. **Auto switching**: "Switch on" Segmented "This device's setting · Sunset and sunrise ·
     Headlights". Phone and desktop default to the device's setting; head units default to
     sunset and sunrise from the car's own GPS (stays on the device). Headlights on the
     Discovery 2 reads "Not available on this car" (the body unit's dipped-beam input is not
     decoded yet).
  3. **Map theme**: Segmented "Follow app · Day · Night · High contrast" ([UI §13.5][ui-13.5]);
     High contrast draws the setting only (no style is defined yet).
  4. **Brightness** (head units with a backlight the Brain controls; else hidden): a slider
     (new component) "Day ‹%›" and "Night ‹%›", and a Switch "Dim with the headlights" (hidden
     where headlights are not available). Proposed rows.
  5. **Text size**: Segmented "Standard · Large · Larger". Only grows type; never goes below
     the floors (12 px phone, 18 px Parked head unit, 24 px Moving). A live sample: "Coolant
     ‹°C›". Proposed rows.
  6. **Dock**: row "Edit dock" → the dock editor. **Wallpaper & style**: row → the theme
     wizard (`45-launcher-*`: wallpaper, colours, icon pack, gauge style). **Lock car layouts** (owner only):
     Switch, caption "Only a signed-in owner can change the Car profile's layouts" ([Drive modes
     §8.3][dm-8.3]).
  7. Row "Units, language and region" → that page.
- **States:** loading; error ("Couldn't save. Try again."); offline (theme still applies
  locally); Parked full; Idling as Moving without Park evidence; Moving: the Settings lock;
  locked (Car profile): Theme and Text size editable, Lock car layouts read-only.
- **Safety and driving rules:** no theme change while Moving except Auto's own switching,
  which never animates ([visual §5][vds-5]); Drive mode at night uses Night or Night dim, never
  Day; the default themes draw no glow in Night dim or Deep night ([visual §1][vds-1]).
- **Components:** Segmented, ListRow, Switch (new), slider (new component: 4 px track, accent
  thumb, 76 px target on head units), Card.
- **Spec refs:** [visual §1][vds-1], [visual §3.1][vds-3.1], [visual §4][vds-4],
  [UI §13.5][ui-13.5], [Drive modes §7.3][dm-7.3], [Drive modes §8.3][dm-8.3].
- **Open questions:** brightness and text size are not in a spec yet; approve them as
  Proposed rows? Does the Brain drive the head unit's backlight at all?

### settings-units-region — Units, language and region  [Proposed]
- **Owner:** os
- **Purpose:** how numbers, dates and words read.
- **Why proposed:** units are on Preferences today with two choices only; Td5 readings need
  pressure and economy units, and i18n keys and `Intl` formatting are already in the app
  model ([app model §4.2][am-4.2]) with no page to choose a language or region.
- **Opens from → goes to:** Settings → Units, language and region; Display row. Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night, hu7 Night dim Moving (the Settings lock).
- **Content (top to bottom):**
  1. **Units** Segmented rows, each with a sample: Distance and speed "km · km/h" or "miles ·
     mph" (sample: road speed); Temperature "°C · °F" (coolant); Pressure "bar · kPa · psi"
     (boost); Volume "litres · UK gallons · US gallons"; Fuel economy "L/100 km · mpg (UK) ·
     mpg (US)". A preset row first: "UK · Metric · US", which fills all of them.
  2. **Language**: a list with the current language ticked; "More languages come with
     translations" caption.
  3. **Region**: Date format (sample "‹date›"), Clock "12-hour · 24-hour", First day of week.
  4. Caption: "Units change how values look. Recordings keep the car's own units."
  5. **Applies to**: Segmented "Everyone on this device · Just me". The owner sets the device
     default; any user may override it for themselves (item 63).
- **States:** loading; error; Parked full; Moving: the Settings lock; locked (Car profile):
  read-only with "Sign in to change".
- **Safety and driving rules:** the Settings lock; a units change never alters a Drive tile's
  thresholds, only their labels (Drive modes widget settings own thresholds).
- **Components:** Segmented, ListRow, Card.
- **Spec refs:** [app model §4.2][am-4.2], [visual §4][vds-4], [Drive modes §8.1][dm-8.1].
- **Open questions:** **Decided (item 63):** a device default with a per-user override; the
  Car profile uses the device default.

<!-- refs -->
[acc-14.9]: ../../../../specs/2026-10-06-accounts-sharing-design.md#149-basic-auth-migration-replaces-the-overlap-line-in-21
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[mcp-8]: ../../../../specs/2026-10-06-mcp-server-design.md#8-audit-log
[pc-8]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#8-alerts-and-rate-limits-shared
[readme]: ../README.md
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[ui-13.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order
[ui-13.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-4]: ../../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[ua-8]: ../../../../specs/2026-10-07-app-ui-model-design.md#8-system-settings-and-the-app-info-page
