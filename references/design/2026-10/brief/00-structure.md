---
title: "Designer brief — the structure: separate apps (PWAs) on one gateway"
area: references
status: draft
version: 1.1
updated: 2026-10-11
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md, references/design/2026-10/brief/00-direction-mfd.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, references/research/direction_standard_not_os.md, references/design/2026-10/brief/00-start-here.md]
summary: >
  Read this first (owner, 2026-10-11). Since v1.1 (MFD, proposed ADR-0052/0053): every app has its own home and settings and bundles the ostler-shell library, so any app's pages tile side by side; the gateway is an app (welcome, connect, Car page, instrument pages, garage, devices, permissions, outputs) and ostler.app is its web form; there is no Drive app and no separate front door. Ostler is a family of small apps, each its own PWA and its own repo: the gateway app, Logs, Diagnostics and add-ons (Security, Maintenance, friends' map, Social, mesh). They install from Chrome on a phone, head unit or laptop, run side by side on a head unit, link to each other and share one look. All of them read one gateway: the Brain (which also hosts and installs the apps), otherwise the Ostler Gateway Android app, otherwise a node for live data, otherwise the browser itself. The brief gives the diagram, what the designer needs to know, prompts for what we need (not how to lay it out) and the site map in XML. It supersedes the brief's launcher, Store and app-frame screens.
---

# Designer brief — the structure

**Read this first.** It replaces the "Ostler is an operating system" model in
[00-start-here](00-start-here.md) and the sitemap files: the launcher, Store and app-frame
screens there are superseded. Screens inside each app (Home, Logs, the log summary, Drive mode)
keep their briefs and the owner's core screens design (the core screens adoption spec, in
review).

## MFD (2026-10-11)

The owner and designer's [direction brief](00-direction-mfd.md), with the owner's
corrections, changes this structure (proposed:
[ADR-0052](../../../../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md) and
[ADR-0053](../../../../decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md)):

- The screen is a layout of tiles (an MFD), each showing one page from any installed app.
  Every app bundles the `ostler-shell` library, so whichever app is open hosts the tiles. No
  launcher, no shell app.
- Each app has its own **home** and **settings** pages.
- The **gateway is an app**: welcome, connect, the Car page, the instrument pages (attitude,
  heading, transfer, speed, engine), garage, devices and hardware detection, permissions,
  outputs and the shared preferences. `ostler.app` is its web form; there is no separate
  front door.
- **No Drive app, no drive modes:** "Off-road" is a saved layout; moving rules limit actions.

## The structure

```
                    ┌──────────────────────────────────────────┐
                    │   GATEWAY APP  (ostler.app, PWA)         │
                    │  Welcome · Connect · Car · Instruments   │
                    │  Garage · Devices · Permissions · Get apps│
                    └───────┬──────────┬──────────┬──────────┬─┘
                  links to  │          │          │          │
            ┌───────────────▼┐ ┌───────▼──────┐ ┌─▼────────┐ ┌▼─────────────┐
            │ LOGS (PWA)     │ │ DIAGNOSTICS  │ │ (more    │ │ ADD-ONS      │
            │ own repo       │ │ (PWA)        │ │  apps)   │ │ Security,    │
            │                │ │ own repo     │ │          │ │ Maintenance, │
            └───────┬────────┘ └──────┬───────┘ └────┬─────┘ │ Map, Mesh…   │
                    │                 │              │       │ each own repo│
                    └────────┬────────┴──────────────┴───────┴──────┬───────┘
                             │ one live feed + history (VISS)       │
              ┌──────────────▼──────────────────────────────────────▼──┐
              │ GATEWAY — whichever the owner has:                      │
              │   Brain (in-car computer: hosts and installs all apps)  │
              │   or Ostler Gateway app (Android phone / head unit)     │
              │   or a node (live view only) · or the browser itself    │
              └──────────────┬──────────────────────────────────────────┘
                             │
              Nodes (each with its own small page) · dongles · sensors

  Every app bundles ostler-shell: any app's pages tile side by side (MFD).
```

## What you need to know

- **Ostler is a family of small apps, not one big app.** Logs, Diagnostics, Security,
  Maintenance and the rest are each their own project and repo. Each installs on its own (phone,
  head unit, laptop), and two can sit side by side on a head unit.
- **They should feel like one product:** one look, one theme system, one way to move between
  apps.
- **The gateway app is where everyone starts** (at `ostler.app` on the web; it replaced the
  front door in v1.1): it welcomes new people, gets their car connected, shows the car at a
  glance (the Car page) and leads to the apps.
- **Every app talks to one gateway** for live data and history. The owner may have a permanent
  device (the Brain), only their phone with the gateway app, or nothing yet; the design handles
  all of these calmly.
- **On the Brain the apps are installed onto the car's computer.** Any phone or screen in the car
  opens them from there, and the Brain's settings are the gateway app's pages.

## Prompts (what we need, not how to lay it out)

- **A welcome** that explains Ostler in seconds and gets someone to "connected" with the least
  friction.
- **A way to connect** that offers only what suits the device in hand: found a gateway nearby;
  install the free gateway app (Android); get a permanent gateway; try it in the browser now
  (Chrome); view my car remotely.
- **A comparison** that makes the gateway choice honest and easy: the free app against a
  permanent device.
- **Gentle prompts** when someone has less than they need (for example "not recording" in a
  browser session): dismissible, one at a time, never nagging, **never while driving**.
- **A Car page** that shows the car at a glance, faults first, and is the jumping-off point to the
  apps.
- **An apps gallery:** what is installed, what is available and what each does, with install
  and open. It works on a phone, a head unit and in the Brain.
- **Moving between apps,** so a diagnosis flows from a fault to the drives it happened on and
  back.
- **Devices and permissions a non-expert understands:** what is connected, what each app may see
  or do, and how to switch it off.
- **Every state:** offline, gateway unreachable, no drives yet, no GPS, Parked and Moving.
- **Sizes:** phone, 7" and 5" head units, desktop; Night and Day; right- and left-hand drive.

## Site map

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- v1.1 (MFD, proposed ADR-0052/0053): every app bundles ostler-shell and has its own
     home and settings; any app's page can sit in any tile. -->
<ostler>
  <!-- The gateway app. Web form at ostler.app (also the Brain's console); native form on
       Android (Ostler Gateway). There is no separate front door. -->
  <app id="gateway" repo="ostler-app-hub" role="gateway">
    <page id="home"/>                  <!-- web entry: welcome, connect, get apps -->
    <page id="welcome"/>
    <page id="connect">
      <option id="found-gateway"/>
      <option id="install-gateway-app" devices="android"/>
      <option id="get-permanent-gateway"/>
      <option id="try-in-browser" devices="chrome-desktop,chrome-android"/>
      <option id="view-remotely"/>
    </page>
    <page id="choose-gateway"/>        <!-- comparison: app vs node vs Brain -->
    <page id="pair"/>
    <page id="car"/>                   <!-- health, pinned gauges, suggestions -->
    <page-set id="instruments">        <!-- ordinary pages; "Off-road" is a saved layout -->
      <page id="attitude"/>
      <page id="heading"/>
      <page id="transfer"/>
      <page id="speed"/>
      <page id="engine"/>
    </page-set>
    <page id="apps"/>                  <!-- get apps that work with this car -->
    <page id="garage">                 <!-- vehicle switcher; sets the connected car -->
      <page id="vehicle"/>
      <page id="add-vehicle"/>
    </page>
    <page id="devices">                <!-- found, added and stale (ADR-0053) -->
      <page id="gateway"/>
      <page id="nodes"/>               <!-- each links to the node's own page -->
      <page id="adapters"/>
      <page id="new-device"/>
    </page>
    <page id="permissions">
      <page id="app-access"/>
      <page id="access-log"/>
    </page>
    <page id="outputs"/>               <!-- Home Assistant, RealDash, ... -->
    <page id="layouts"/>               <!-- saved layouts, synced -->
    <page id="settings">               <!-- holds the shared preferences -->
      <page id="account"/>
      <page id="theme"/>
      <page id="units"/>
      <page id="driver-side"/>
      <page id="sharing"/>
    </page>
  </app>

  <app id="logs" repo="ostler-app-logs">
    <page id="home"/>
    <page id="logs-list"/>
    <page id="statistics"/>
    <page id="log-summary"/>
    <page id="playback"/>
    <page id="map"/>
    <page id="export"/>
    <page id="settings"/>              <!-- with a Shared section -->
  </app>

  <app id="diagnostics" repo="ostler-app-diagnostics">
    <page id="home"/>
    <page id="overview"/>
    <page id="faults">
      <page id="fault-detail"/>        <!-- links to the drives it was seen on -->
    </page>
    <page id="live-data"/>
    <page id="tests" guarded="true"/>
    <page id="procedures"/>
    <page id="decode-lab"/>
    <page id="docs"/>
    <page id="settings"/>              <!-- with a Shared section -->
  </app>

  <addons>                             <!-- each with home and settings -->
    <app id="security" repo="ostler-app-security"/>
    <app id="maintenance" repo="ostler-app-maintenance"/>
    <app id="friends-map" repo="ostler-app-map"/>
    <app id="social" repo="ostler-app-social"/>
    <app id="mesh"/>
  </addons>

  <!-- Library, not an app: bundled by every app above -->
  <library id="ostler-shell" repo="ostler-shell"/>

  <!-- Small built-in page on each node -->
  <node-page>
    <page id="status"/>
    <page id="signals"/>
    <page id="wifi-setup"/>
    <page id="firmware"/>
  </node-page>
</ostler>
```

`ostler-app-logs` holds Logs. Since v1.1 `ostler-app-drive` is not created; `ostler-app-hub`
holds the gateway app's web form (repo name open, ADR-0052 §9).

## Changelog

- 1.1 (2026-10-11): MFD section (proposed ADR-0052/0053); the site map drops the Drive app,
  gives each app home and settings, moves connect, pair, choose-gateway, devices, garage,
  permissions and outputs into the gateway app (whose web form is `ostler.app`) with the Car
  page and instrument pages, and adds the `ostler-shell` library; diagram updated.
- 1.0 (2026-10-11): written from the owner's structure discussion of 2026-10-11 (ADR-0049
  v1.3).
