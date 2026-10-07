---
title: "App UI model — what an app contributes to the empty OS: drawer entry, pages, shortcuts, widgets, setup and options flows, notification channels, themes and data classes; object kinds; App info; manifest schema 2 — design"
area: specs
status: stable
version: 0.2
updated: 2026-10-07
depends_on: [decisions/adr-0045-ux-first.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-store-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, references/research/ha_integrations_dashboards.md, references/research/ha_architecture_addons.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all", OS round; decision list items 22–27 and 56–58), v0.2; every decision answered as recommended. Amends the app-model spec for the empty OS (ADR-0046). An app contributes a drawer entry, pages (schema-rendered by the OS from data, or custom views), static and dynamic shortcuts, widgets (the launcher spec's contract), a setup flow in the Home Assistant config-flow style (steps of OS-drawn schema forms with validation, per-field and base errors, discovery confirmation, progress, external sign-in, reauth and reconfigure), an options flow, notification channels (alarm and critical reserved for the OS), themes, data classes, dashboard presets and Drive menu rows. Backend-only apps (integrations: vehicle packs, data sources, bridges) have a setup page and App info only; hardware access is for first-party or verified integrations and never for car buses. System Settings and the App info page (permissions, data, storage, notifications, version, logs, disable, uninstall with export first). Eight object kinds: app, integration, widget pack, theme pack, icon pack, wallpaper pack, dashboard preset, sound or EQ preset, with what each may hold and where it installs (data objects install on the phone; code apps stay bundled or Brain-served). The manifest `ostler-app.json` goes to schema 2: `kind`, `backend`, `permissions.network` and `hardware`, and `contributes` drawer, pages, shortcuts, setup, options, notifications, themes, dashboards. Tests, phases UA1–UA4 and owner decisions.
---

# App UI model — design

**Status:** approved by the owner on 2026-10-07 ("approve all", OS round; decision list
items 22–27 and 56–58), v0.2. It **amends** the
[app-model spec](2026-10-06-app-model-design.md) (draft v0.9): §3 (app kinds) and §14.1 (the
core list) give way to [ADR-0046](../decisions/adr-0046-empty-os-every-app-an-add-on.md);
§4 (the manifest) goes to schema 2 (§10 here); §14.2's More → Add-ons gives way to the drawer,
Settings → Apps and the [Store](2026-10-07-store-design.md). Everything else there stands:
isolation kinds (§5), the SDK (§6, §15.5), the phone build (§7.1), the hard lines (§8, §14.6),
templates (§14.5), widgets and user overrides (§15). Nothing is built before its UX briefs
are approved ([ADR-0045](../decisions/adr-0045-ux-first.md)): the setup-flow form, the App
info page, the permissions sheet and system Settings come first.

## 1. Context

The owner (2026-10-07): "Every app can have its own setup menus. Some apps are backend-only
(integrations) with just a setup page, like Home Assistant. Some apps are just widget packs."
Home Assistant's config flows, options flows and integration pages are the model
([HA integrations §1](../references/research/ha_integrations_dashboards.md)); Android's App
info page is the model for permissions, storage and notifications.

## 2. What an app contributes

| Contribution | Manifest field | Drawn by | Where it shows |
|---|---|---|---|
| **Drawer entry** | `contributes.drawer` | OS | the drawer, Settings → Apps, the Store |
| **Pages** | `contributes.pages` | OS (schema) or app (custom) | opened from the drawer, a shortcut, a deep link, a notification |
| **Shortcuts** | `contributes.shortcuts`; SDK `shortcuts.setDynamic` (≤ 4) | OS | long press in the drawer; placed on pages and the dock |
| **Widgets** | `contributes.widgets` | OS frame; OS view or app view | the widget picker ([launcher §8](2026-10-07-launcher-and-widgets-design.md)) |
| **Setup flow** | `contributes.setup` | OS (forms) | first open, the Store's install sheet, Settings → Vehicles and integrations |
| **Options flow** | `contributes.options` | OS (forms) | App info → App settings; the app's own settings page |
| **Notification channels** | `contributes.notifications.channels` | OS | Settings → Notifications; App info |
| **Themes** | `contributes.themes` | OS (tokens) | the theme wizard |
| **Data classes** | `contributes.data_classes` | OS | Settings → Privacy (accounts spec §14.1; each starts in ghost) |
| **Dashboard presets** | `contributes.dashboards` | OS | the dashboard builder, the pages overview |
| **Drive menu rows** | `contributes.drive_menu` | OS | ShellInput's Drive menu (app-model §15.3, unchanged) |

An app never places itself: shortcuts, widgets and pages appear only where the user puts them
or where the OS lists them.

## 3. Pages: schema-rendered or custom

### 3.1 Schema-rendered pages

The OS draws the page from a small page schema and the app's data. These pages are data only,
so they work for declarative apps and in the phone binary.

| Page type | What it shows |
|---|---|
| `list` | rows (icon, title ≤ 30, meta, trailing value or chevron), sections, search Parked |
| `detail` | sections of label and value pairs, with honest states (stale, candidate, missing) |
| `form` | an options form (the same renderer as flows, §4) |
| `tiles` | a grid of signal tiles over VSS paths |
| `map` | the OS map with the app's layers |
| `media` | now playing with controls, through the audio-focus service |

```jsonc
{ "page": 1, "type": "list", "title": "presets.title",
  "source": { "feed": "presets" },                        // data the app publishes, or "signals"
  "row": { "title": "/name", "value": "/frequency", "icon": "radio",
           "open": { "page": "station", "params": { "id": "/id" } } },
  "driving": { "moving": { "template": "short_list" } } }
```

Fields are JSON Pointers into each feed item. Text limits, units and the Moving template come
from the OS, as for widgets.

### 3.2 Custom pages

A custom page is the app's own view: a bundled React component (first party and reviewed
publishers) or an iframe (community, web hosts only), as app-model §5. Its driving rule is
`full` or `false` for Parked and Idling and a template or `false` for Moving (app-model
§4.2, unchanged); while Moving the OS draws the template from the app's published data.

## 4. The setup flow

### 4.1 Shape

A flow is a list of steps. The OS draws every step; the app supplies schemas, text keys and,
when it has a backend, a handler that validates input and decides the next step.

```jsonc
{ "flow": 1, "id": "setup",
  "steps": [
    { "id": "user", "type": "form", "title": "flow.user.title", "description": "flow.user.text",
      "schema": { "type": "object", "required": ["region"],
                  "properties": { "region": { "enum": ["uk", "eu", "other"] },
                                  "dab": { "type": "boolean", "default": true } } } },
    { "id": "scan", "type": "progress", "title": "flow.scan.title", "task": "scan_stations" },
    { "id": "done", "type": "create_entry", "title": "flow.done.title" } ] }
```

### 4.2 Step types

| Type | What the OS shows |
|---|---|
| `form` | a form from a JSON Schema subset: string (`maxLength`), number (bounds), boolean, enum, the VSS signal picker, a device picker, a place picker, a secret (masked, stored in the OS keystore) |
| `confirm` | "Set up *thing* found on *link*?" for a discovered item; never auto-completed |
| `menu` | a short list of branches ("Use a USB tuner" / "Use a HAT") |
| `progress` | a backend task with progress and Cancel |
| `external` | sign-in in the system browser (OAuth and similar); an outbound path, asked first |
| `abort` | a stop with a reason ("No tuner found") and a help link |
| `create_entry` | the summary and Done; the app is set up |

### 4.3 Validation and errors

- The OS checks each form against its schema before sending it. The handler then returns
  `{ "next": "<step id>" }` or `{ "errors": { "<field>": "<i18n key>" }, "base": "<i18n
  key>" }`. Field errors sit under their fields; a base error sits at the top. Text is i18n
  keys only; the OS refuses raw strings over 120 characters.
- A declarative integration with no backend has schema validation only.
- Each finished flow has a stable **`unique_id`** (a serial or a device id, never an address,
  HA research C3), so a second setup of the same thing is refused as "Already set up".

### 4.4 Rules

- Adding or removing an integration and any `external` step are **owner-role** operations
  (ADR-0029 §5). Secrets never reach the app's UI after entry.
- Every flow is text entry, so on a driver-facing display it is **Parked only**; a phone may
  run it any time. A flow never runs a car action; anything that reaches the gate goes
  through `actions.request` with its own confirm.
- **Reauth** (credentials expired) and **reconfigure** (required data changed) reuse the setup
  flow's steps from a named entry step; the entry keeps its `unique_id`.
- **Discovery** (`discovery` in the manifest: `usb` vendor and product ids, `bluetooth`
  service or name, `mdns` service type, `mqtt` topic, `node` capability) only lists the item
  under **Discovered** in Settings → Vehicles and integrations. The user confirms it.

## 5. The options flow

The options flow changes optional settings after setup. It uses the same step types (usually
one `form`), opens from App info → **App settings** and from the app's own settings page, and
saves through the app's handler. An app's own settings page may be custom; the OS still
offers the options flow in App info so every app has one place for its settings.

## 6. Backend-only apps (integrations)

- An integration has **no drawer entry and no pages**. It has a setup flow, an options flow
  and an App info page, listed in Settings → **Vehicles and integrations**.
- Integration types: `vehicle` (a vehicle pack), `data_source` (the node source, a source
  adapter, a phone Car API source), `bridge` (MQTT and Home Assistant discovery, OwnTracks,
  Traccar, ntfy, RealDash CAN out, LubeLogger) and `device` (a driver for our own hardware,
  such as a DAB tuner or a DSP). Each shows its `iot_class` (local push, local poll, cloud),
  HA research C14.
- What it provides shows on its page: for a vehicle pack, systems and signal counts in our
  words ("Engine: 24 proven, 9 candidate signals; 3 verified actions"); for a bridge, what it
  sends and where.
- **Vehicle packs** keep the `VehiclePack` contract and entry point (ADR-0013); they add an
  `ostler-app.json` with `kind: integration` and `integration.type: vehicle`. The car buses
  stay the OS's: no integration gets bus access beyond the contract and the gate.
- **Hardware access** (`permissions.hardware`) is only for `device` integrations from first
  party or verified publishers, names the device by USB class or ids, and never covers a car
  bus, the node link or the module bus. Apps use such a device through the SDK `devices`
  service, never directly.

## 7. Notification channels

- An app declares channels: `{ "id", "name", "importance": "high" | "default" | "low",
  "sound": true }`. **`alarm` and `critical` are reserved for the OS** (alarm alerts, red
  telltales, Crash SOS).
- The user turns each channel on or off and sets its sound in Settings → Notifications and in
  App info. A notification needs its channel.
- **While Moving** on a driver-facing display: `high` may raise one `alert_card` (≤ 2 lines
  of ≤ 30 characters, ≤ 2 buttons; message rules of UI spec §12.1 apply); `default` and `low`
  only add to a count until Parked. The OS rate limits as for message alerts.
- On the phone, channels map to the OS notification channels of the native app.

## 8. System Settings and the App info page

**System Settings** (system UI, ADR-0046): Network and devices · Vehicles and integrations
(Discovered, installed integrations, garage) · Apps (all apps, driving apps order, defaults,
hidden) · Home screen (edit, dashboard builder, dock, driving set) · Display and theme (theme
wizard, brightness, night) · Sound (system volume, audio focus, link to Audio) ·
Notifications · Driving and safety (Using Ostler while driving, Passenger view, Crash SOS
later) · Privacy (data classes, sharing, Places, outbound paths) · Users and accounts · Input
(key test, bindings, steering-wheel learning) · Backups · Updates · Store (online catalogue,
channel) · Developer (service mode, sideloading) · About.

**App info** (one page per installed object):

| Section | Content |
|---|---|
| Header | icon, name, publisher, review level, version, **Open**, **App settings** |
| **Permissions** | data classes, signals, actions (category and tier, copied from the capability manifest), notifications, network hosts (each an outbound path, on or off), storage, background and wake, calls, audio focus, hardware; each switchable where the OS allows |
| **Data** | storage used, **Export data** (open format), Clear data |
| **Notifications** | its channels |
| **Version and updates** | version, source repo and licence, changelog, auto-update, channel |
| **Logs** | recent errors, "App stopped" history, a log viewer (owner role); copy for a bug report, scrubbed |
| **Disable** | keeps data, removes every contribution |
| **Uninstall** | offers Export data first; removes contributions, data and (where the host allows) code |

System services and system UI show an App info page with no Disable or Uninstall.

## 9. Object kinds

| Kind | Holds | Code? | Phone binary | Review |
|---|---|---|---|---|
| **app** | drawer entry, pages, shortcuts, widgets, flows, channels, optional backend | yes, or declarative | bundled or Brain-served only; declarative apps install | per publisher (Store) |
| **integration** | setup and options flows, a backend; types vehicle, data_source, bridge, device | yes (backend), or declarative | as app; vehicle packs as JSON data | as app; `device` first party or verified only |
| **widget pack** | widgets only | declarative, or code as an app | declarative packs install | as app |
| **theme pack** | token values within the allowed set, accents, default gauge style | no | installs | automatic checks (contrast, safety tokens untouched) |
| **icon pack** | SVG glyphs mapped to the catalogue names | no | installs | automatic checks (names, size, no safety glyphs) |
| **wallpaper pack** | images (≤ 2 MB each, EXIF stripped) | no | installs | automatic checks, then review |
| **dashboard preset** | `ostler.layout/2` pages | no | installs | the layout validator |
| **sound or EQ preset** | EQ curves, balance and fade, crossover and delay values for the Audio app | no | installs | range checks |

Data objects (the last five) never carry code, URLs or scripts; the OS refuses one that does.

## 10. Manifest schema 2

`ostler-app.json`, `"schema": 2`, validated by `schemas/app-manifest.schema.json` (created in
UA1). Schema 1 manifests are read and upgraded in memory (`kind: app`, `contributes.slots`
mapped to pages and the drawer).

```jsonc
{ "$schema": "https://ostler.tech/schemas/app-manifest.schema.json",
  "schema": 2,
  "id": "ostler.radio", "name": "Radio", "version": "0.1.0",
  "shell": "^2.0",                                   // the SDK range
  "kind": "app",                                     // app | integration | widget_pack | theme_pack | icon_pack | wallpaper_pack | dashboard_preset | sound_preset
  "source": { "repo": "https://github.com/openostler/ostler-app-radio", "publisher": "openostler" },
  "entry": { "kind": "bundled", "module": "@ostler/app-radio" },
  "backend": { "kind": "python", "entry_point": "ostler_radio.service:main",
               "hosts": ["brain"], "limits": { "memory_mb": 64, "cpu": 0.25, "disk_mb": 50 } },
  "hosts": ["head_unit", "phone", "desktop"],
  "requires": { "product": ["ostler"], "devices": [{ "kind": "tuner" }], "apps": ["ostler.audio"] },
  "permissions": { "data": [], "notifications": true, "network": [], "storage": "app",
                   "audio": "media", "hardware": [] },
  "contributes": {
    "drawer": { "title": "drawer.title", "icon": "radio", "category": "media", "page": "home" },
    "pages": [ { "id": "home", "render": "custom", "view": "RadioHome",
                 "driving": { "parked": "full", "idling": "full", "moving": { "template": "media" } } },
               { "id": "presets", "render": "schema", "schema": "pages/presets.json" } ],
    "shortcuts": [ { "id": "presets", "label": "shortcut.presets", "icon": "list", "page": "presets" } ],
    "widgets": [],
    "setup": { "flow": "flows/setup.json", "required": true },
    "options": { "flow": "flows/options.json" },
    "notifications": { "channels": [ { "id": "station", "name": "channel.station", "importance": "low" } ] },
    "themes": [], "data_classes": [], "dashboards": [], "drive_menu": ["next_preset"] },
  "i18n": { "default": "en", "messages": "i18n/{locale}.json" },
  "icons": [ { "symbol": "radio" } ] }
```

**Changes from schema 1:**

- **`kind`** is now the object kind (§9). The registry still assigns `trust` (`system`,
  `first_party`, `verified`, `community`) and never reads it from the file; `system` replaces
  `core`.
- **`backend`** (new): a Python service on the Brain (an entry point in the `openostler.app`
  group, run by the OS with the declared limits, a scoped local API token, no bus access);
  `container` waits for its ADR (ADR-0042 HA direction item 99).
- **`permissions.network`** (new): every host the app reaches; each is an outbound path,
  off until the owner turns it on. **`permissions.audio`** (`media`, `call`, `alert`) for
  audio focus; **`permissions.hardware`** (§6).
- **`requires.apps`** (new): apps it needs, offered together at install.
- **`contributes.slots`** is replaced by `drawer`, `pages`, `shortcuts` and `widgets`;
  `destination:*` and `more:*` slots retire with the rail and More (launcher spec).
- **`contributes.setup`, `options`, `notifications`, `themes`, `dashboards`** are new;
  `widgets`, `drive_menu` and `data_classes` are unchanged.

## 11. Tests

- **Schema:** each object kind's example validates; a data object with a script, URL or code
  entry is refused; `alarm` or `critical` channels from an app are refused; `hardware` on a
  non-`device` kind or a community publisher is refused; schema 1 manifests upgrade.
- **Flows:** a form step refuses input that breaks its schema before the handler runs; field
  and base errors render under the right field; a second setup with the same `unique_id` is
  refused; a discovered item never completes without `confirm`; every flow is refused on a
  Moving driver-facing display; an `external` step asks for the outbound path first.
- **App info:** Disable removes every contribution and keeps data; Uninstall offers Export
  first; a system service has no Disable or Uninstall.
- **Notifications:** while Moving, `default` and `low` never raise a card; `high` obeys the
  rate limits.
- **Pages:** a schema page renders with no app code; a custom page that throws shows "App
  stopped" and the launcher keeps running.

## 12. Phases

| Phase | Ships | Needs |
|---|---|---|
| **UA1** | Manifest schema 2 and its validator; the registry with `kind` and `trust: system`; Settings → Apps and App info (read-only) | UX briefs approved |
| **UA2** | The flow renderer and handler API; options flow; notification channels; schema pages; the widget contract (launcher LW2) | UA1 |
| **UA3** | Backends on the Brain (Python entry points, limits, scoped token); integrations page with Discovered; vehicle packs with `ostler-app.json` | UA2 |
| **UA4** | Data objects (themes, icons, wallpapers, presets, EQ) installed from the Store | Store S2 |

## 13. Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", OS round; decision list items
22–27 and 56–58). Each recommendation below is the decision; each alternative was not chosen.

1. **Schema-rendered pages as a page kind?** Recommend: yes (list, detail, form, tiles, map,
   media). Alternative: custom pages only.
2. **Config-flow setup drawn by the OS?** Recommend: yes, apps supply schemas and handlers.
   Alternative: each app draws its own setup.
3. **Reserve `alarm` and `critical` channels for the OS?** Recommend: yes. Alternative: allow
   reviewed first-party apps to use `critical`.
4. **Declared network hosts as outbound paths?** Recommend: yes, each off until the owner
   allows it. Alternative: one "Internet" switch per app.
5. **Hardware for `device` integrations only?** Recommend: yes, first party or verified, never
   car buses. Alternative: no hardware access outside the OS.
6. **Python backends on the Brain now, containers later?** Recommend: yes. Alternative: wait
   for containers.

## Changelog

- 2026-10-07: v0.1, first draft from the owner's direction of 2026-10-07, for ADR-0046.
- 2026-10-07: v0.2, approved by the owner on 2026-10-07 ("approve all", OS round; decision
  list items 22–27 and 56–58): every decision answered as recommended (alternatives not chosen).
