---
title: "Store — the system app that finds, installs and updates apps, integrations, widget packs, themes, icons, wallpapers, dashboards and sound presets: signed catalogue, publisher keys and review, Works with Ostler, bundled offline catalogue, sideloading — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0045-ux-first.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0041-brain-ed25519-signing.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0017-open-standards-first.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-community-hub-design.md, references/research/ha_architecture_addons.md, references/research/ha_companion_community.md, references/research/ha_integrations_dashboards.md]
summary: >
  Draft for the owner (2026-10-07). The Store is a system app (ADR-0046), like Google Play on Android: home, categories, search, detail pages, an install sheet that shows permissions and outbound hosts in plain words, updates, a library and publisher pages; Parked only on driver-facing displays. It hosts every object kind of the app UI model. The catalogue is static, signed data in TUF-style roles with Ed25519 keys (root, targets, snapshot, timestamp), with delegated publisher keys; packages are pinned by hash and fetched from their repos' releases. Review levels: System, First party, Verified publisher, Community, Sideloaded; revocation disables an item with a notice. "Works with Ostler" badges certify hardware, apps and integrations against written, testable criteria, separate from review. A bundled offline catalogue ships in the OS image and the phone binary, so flavours install with no internet; browsing online is an opt-in outbound path that needs its own ADR. Sideloading is for developers in service mode, on web hosts and the Brain; the phone installs only data objects and declarative apps. Ratings are an owner decision (recommend none, keeping the hub's no-votes rule); paid items are an owner decision (recommend none in v1). Updates, privacy, phases S0–S4, tests and decisions.
---

# Store — design (draft)

**Status:** draft v0.1 for the owner. Nothing is built before its UX briefs are approved
([ADR-0045](../decisions/adr-0045-ux-first.md)): Store home, detail page, install and
permissions sheet, updates and library come first. Browsing an **online** catalogue is a new
outbound path, so it waits for its own ADR ([ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md)
decision 5; app-model Q7); this spec is the design that ADR will cite. The bundled offline
catalogue (§7) needs no such ADR.

## 1. Context

- The owner (2026-10-07): "A store app like Google Play hosts apps, theme packs, widget packs
  and other objects."
- [ADR-0046](../decisions/adr-0046-empty-os-every-app-an-add-on.md) makes every feature an
  app, so the Store is how a bare OS becomes useful.
- Home Assistant's lessons: repositories added by URL with no review (HACS) and a numeric
  security score that users cannot read are to be avoided; signed images, channels, written
  certification criteria and plain permission summaries are to be copied
  ([HA architecture §3, §8](../references/research/ha_architecture_addons.md),
  [HA community §6, §9](../references/research/ha_companion_community.md)).
- The phone app may not download code that changes features (app-model §7.1). The Community
  hub has no points, ranks or votes ([community hub](2026-10-07-community-hub-design.md)).

## 2. Goals and non-goals

**Goals.** One place to find and install every object kind; plain words about what each item
can do and reach; signed, revocable items; installs that work offline; no tracking.

**Non-goals.** Runtime code on the phone; an account to browse; ranking by popularity or
votes; advertising; items that define car actions.

## 3. The Store app

The Store is system UI (ADR-0046 §1): it cannot be uninstalled. On a driver-facing display it
is **Parked only**, like the rest of the drawer's non-driving apps.

| Screen | Content |
|---|---|
| **Home** | "Set up your car" (items that match the vehicle, its integrations and devices found), "For this screen" (head unit, phone), "New and updated", "Picks" (curated by the project, with a written reason), then category rows |
| **Categories** | Apps · Integrations (vehicles, data sources, bridges, devices) · Widgets · Themes · Icons · Wallpapers · Dashboards · Sound; each with sub-categories (media, navigation, gauges, off-road …) |
| **Search** | by name, publisher, signal ("boost"), vehicle ("Discovery 2") and device ("DAB"); results grouped by kind |
| **Detail** | icon, name, publisher and review level, Works with badges, one-line summary, screenshots rendered from recorded fixtures per layout class and driving state, description, **What it needs** ("Needs the Brain", "Needs a DAB tuner", "Needs the Audio app"), **What it can do** (permissions in words), **Where it connects** (each network host), data classes, version, size, changelog, source repo and licence, hosts, known issues (publisher-written) |
| **Install sheet** | the permissions and hosts again, each host as a switch (off by default); what will also be installed (`requires.apps`); the setup flow starts after install if required |
| **Updates** | pending updates with changelogs; auto-update settings; "Needs your approval" for permission changes or breaking versions |
| **Library** | installed items by kind, previously installed items (reinstall), and uninstalled items' exported data |
| **Publisher** | name, verified identity (for verified publishers), key fingerprint, their items, source org, contact link |

## 4. What the Store hosts

Every object kind of the [app UI model §9](2026-10-07-app-ui-model-design.md):

| Kind | Listing shows also | Installs on the phone binary |
|---|---|---|
| App | pages per layout class, Moving templates used | declarative apps; code apps are enabled if bundled, or served by the user's Brain |
| Integration | integration type, `iot_class`, vehicles or devices supported, signal counts in our words | vehicle packs as data; others as apps |
| Widget pack | each widget with its sizes and Moving template | declarative packs |
| Theme pack | previews in Night, Day and Dim; contrast results | yes |
| Icon pack | a sample grid over the catalogue names | yes |
| Wallpaper pack | thumbnails; image sizes | yes |
| Dashboard preset | Parked and Moving previews per class; widgets it needs | yes |
| Sound or EQ preset | curves drawn; which Audio features it uses | yes |

## 5. The catalogue and signing

- **Static files.** The catalogue is a set of static JSON files built in the `ostler-catalogue`
  repo (ADR-0046 §7) and served from a plain static host with mirrors. The device downloads
  whole files, never per-item queries, so the server cannot see what a device looks at.
- **Signed in roles** (the open model of The Update Framework, ADR-0017): **root** (offline
  keys, held by the project, threshold 2 of 3), **targets** (the item list, delegating to
  **publisher keys** per publisher namespace), **snapshot** and **timestamp** (short expiry,
  so a stale or frozen catalogue is detected). Keys are Ed25519 through the existing
  `cryptography` extra ([ADR-0041](../decisions/adr-0041-brain-ed25519-signing.md)); the
  verifier is small stdlib-plus-extra code in the OS. Adopting a TUF library instead is a new
  dependency and needs the catalogue ADR.
- **Packages** stay in each item's own repo releases. The catalogue pins each by SHA-256 and
  size; the device refuses any mismatch. UI apps are built bundles; Brain backends are
  wheels; data objects are archives with a manifest.
- **Publisher keys.** A publisher registers a key (fingerprint shown on its page); every
  release is signed by it. The project's targets role delegates the publisher's id namespace
  to that key. An owner may add a publisher key locally for their own devices (app-model Q3),
  shown as "Trusted by you".
- **Revocation.** The project can revoke a key or an item version. A revoked item installed
  on a device is **disabled** at the next catalogue check, with a notice and Export data; it
  is never deleted silently.

## 6. Review levels and Works with Ostler

### 6.1 Review levels

| Level | Who | What is checked | What it may be |
|---|---|---|---|
| **System** | the OS | the OS's own review | system services and UI only |
| **First party** | `openostler` | full code review in its repo | any kind |
| **Verified publisher** | identity checked, key registered | automated checks plus a human review of the manifest, permissions and network hosts against the code | any kind; `device` integrations allowed |
| **Community** | any publisher with a key | automated checks plus a manifest review; no code review is claimed | data objects, declarative apps and widgets anywhere; code apps as iframes on web hosts only |
| **Sideloaded** | a developer, outside the catalogue | nothing | §8 |

**Automated checks** for every item: the manifest validates (app UI model §10); data objects
carry no code, URLs or scripts; widgets declare `moving`; previews are recorded fixtures;
declared network hosts match the hosts the bundle calls (a static scan); no item defines a
car action, tier or category; the licence is compatible with the host it ships to (ADR-0012;
app-model Q4 stays open for iframe apps).

### 6.2 Works with Ostler

A badge, separate from review, for **hardware** (adapters, head units, tuners, DACs and DSPs,
cameras, modules) and **apps and integrations**. Written, testable criteria, checked again
each major OS version:

- works locally, with any cloud optional and off by default;
- passes the conformance tests (the module contract kit for hardware; the app test kit for
  apps: Moving templates, gate use, export);
- exports user data in an open format;
- has an active maintainer and a public issue tracker.

Badges are listed on the detail page with the version tested. A fee is an owner decision
(HA charges one, [HA community §6](../references/research/ha_companion_community.md)).

## 7. The bundled offline catalogue

- The OS image and the phone binary ship a **signed snapshot** of the catalogue's first-party
  items, and the OS image also ships their packages. Flavours (ADR-0046 §5) install from it
  at first run with no internet.
- The Store works fully offline on it: browse, install, update by OS update.
- With the online catalogue switched on (an opt-in outbound path, Settings → Store), the
  device fetches the timestamp and snapshot roles on a schedule (daily, on an unmetered
  uplink, never while Moving) and items on demand.

## 8. Sideloading for developers

- **Where:** service mode → Settings → Developer → **Install from file** (a local file or a
  URL on the local network, such as a developer's build server). Web hosts and the Brain
  only.
- **Phone binary:** data objects and declarative apps only; never code (app-model §7.1).
- A sideloaded item wears a **Sideloaded** badge everywhere (App info, drawer long press, the
  Store's library), may be unsigned (with a warning) or signed by a developer key, and is
  disabled when service mode is turned off unless the owner keeps it ("Keep after service
  mode").
- Sideloading never bypasses the manifest validator, the permissions sheet, the gate or the
  Moving rules.

## 9. Updates

- Auto-update per item (default on for First party, off for others), **never while Moving**
  on a driver-facing display, and only on an unmetered uplink unless the owner allows it.
- An update that adds a permission, a network host or a data class, or crosses a
  `breaking_versions` entry, waits for the owner's approval.
- An update that fails its health check rolls back to the previous version; the previous
  package is kept until the next successful start.
- The registry refuses an item outside the OS's SDK range ("Needs Ostler *x.y*").

## 10. Privacy

- No account is needed to browse or install. A Community hub account is never required.
- The catalogue is fetched as whole files (§5); the device sends no installed list,
  vehicle, VIN or location. Packages come from their repos' release hosts, named on the
  detail page as "Downloads from *host*".
- Opt-in, aggregate install counts are a separate decision (HA community Decide 7) and are
  not part of the Store.

## 11. Ratings and paid items (owner decisions)

- **Ratings.** The Community hub has **no points, ranks or votes**. Recommend: **no stars and
  no review text** in the Store; show the review level, Works with badges, last update, the
  publisher's known issues and a link to the item's issue tracker. Alternative: stars and
  short reviews from signed-in Community accounts, which would break the hub's no-votes rule
  for the Store.
- **Paid items.** Recommend: **none in v1**; everything free; a publisher may link a donation
  or support page (opened in the browser, Parked). Alternative: paid data objects (themes,
  wallpapers, icon packs) sold through an external checkout on web hosts only, because the
  phone stores require their own in-app payment for digital goods and code under the AGPL
  stays free to share. Safety, decoding and input are never sold (ADR-0042, DMD round).

## 12. Phases

| Phase | Ships | Needs |
|---|---|---|
| **S0** | UX briefs; the catalogue format and signing roles written down | ADR-0045 |
| **S1** | The Store app on the **bundled offline catalogue**: home, categories, search, detail, install sheet, library; first-party items only | UA1 |
| **S2** | Data objects (themes, icons, wallpapers, presets, EQ) and declarative apps from the bundled catalogue on every host, the phone included | S1, UA4 |
| **S3** | The **online catalogue** (after its ADR): roles, publisher keys, verified and community levels, revocation, updates | the catalogue ADR |
| **S4** | Sideloading, Works with Ostler badges, publisher pages | S3 |

## 13. Tests

- **Signing:** a tampered item, a wrong hash, an expired timestamp, a rolled-back snapshot and
  a key outside its delegated namespace are each refused; a revoked item is disabled with a
  notice and its data kept.
- **Offline:** with the network off, a fresh OS installs its flavour from the bundled
  catalogue and the Store browses it.
- **Phone:** the phone build never downloads or evaluates code; a sideload of a code app is
  refused there.
- **Install sheet:** every declared host appears and starts off; an update adding a host waits
  for approval.
- **Moving:** the Store, installs and updates are refused on a Moving driver-facing display.
- **Privacy:** a catalogue fetch sends no device, vehicle or installed-item data (request
  capture test).

## 14. Decisions for the owner

1. **Store as a system app?** Recommend: yes. Alternative: an uninstallable first-party app.
2. **Signed catalogue in TUF-style roles with our own small verifier?** Recommend: yes.
   Alternative: a TUF library (a new dependency).
3. **Review levels as §6.1?** Recommend: yes. Alternative: first party and verified only, no
   community items.
4. **Bundled offline catalogue in the OS image and the phone binary?** Recommend: yes.
   Alternative: in the OS image only.
5. **Online catalogue opt-in and off by default?** Recommend: yes, one switch at first run.
   Alternative: on by default with a notice.
6. **Ratings?** Recommend: none. Alternative: stars and reviews through Community accounts.
7. **Paid items?** Recommend: none in v1. Alternative: paid data objects on web hosts.
8. **Works with Ostler fee?** Recommend: free until the programme has criteria tests and
   partners. Alternative: a yearly fee from the start.
9. **Sideloaded items after service mode?** Recommend: disabled unless the owner keeps them.
   Alternative: always kept.

## Changelog

- 2026-10-07: v0.1, first draft from the owner's direction of 2026-10-07, for ADR-0046.
