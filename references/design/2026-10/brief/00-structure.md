---
title: "Designer brief — the structure: separate apps (PWAs) on one gateway"
area: references
status: draft
version: 1.0
updated: 2026-10-11
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, references/research/direction_standard_not_os.md, references/design/2026-10/brief/00-start-here.md]
summary: >
  Read this first (owner, 2026-10-11). Ostler is a family of small apps, each its own PWA and its own repo: the Ostler front door (welcome, connect, Home, apps gallery, garage, devices, permissions, settings), Logs, Diagnostics, Drive and add-ons (Security, Maintenance, friends' map, Social, mesh). They install from Chrome on a phone, head unit or laptop, run side by side on a head unit, link to each other and share one look. All of them read one gateway: the Brain (which also hosts and installs the apps), otherwise the Ostler Gateway Android app, otherwise a node for live data, otherwise the browser itself. The brief gives the diagram, what the designer needs to know, prompts for what we need (not how to lay it out) and the site map in XML. It supersedes the brief's launcher, Store and app-frame screens.
---

# Designer brief — the structure

**Read this first.** It replaces the "Ostler is an operating system" model in
[00-start-here](00-start-here.md) and the sitemap files: the launcher, Store and app-frame
screens there are superseded. Screens inside each app (Home, Logs, the log summary, Drive mode)
keep their briefs and the owner's core screens design (the core screens adoption spec, in
review).

## The structure

```
                    ┌──────────────────────────────────────────┐
                    │        OSTLER  (front door, PWA)         │
                    │  Welcome · Connect · Home · Apps gallery │
                    │  Garage · Devices · Permissions · Settings│
                    └───────┬──────────┬──────────┬──────────┬─┘
                  links to  │          │          │          │
            ┌───────────────▼┐ ┌───────▼──────┐ ┌─▼────────┐ ┌▼─────────────┐
            │ LOGS (PWA)     │ │ DIAGNOSTICS  │ │ DRIVE    │ │ ADD-ONS      │
            │ own repo       │ │ (PWA)        │ │ (PWA)    │ │ Security,    │
            │                │ │ own repo     │ │ own repo │ │ Maintenance, │
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
```

## What you need to know

- **Ostler is a family of small apps, not one big app.** Logs, Diagnostics, Drive, Security,
  Maintenance and the rest are each their own project and repo. Each installs on its own (phone,
  head unit, laptop), and two can sit side by side on a head unit.
- **They should feel like one product:** one look, one theme system, one way to move between
  apps.
- **The front door ("Ostler") is where everyone starts:** it welcomes new people, gets their car
  connected, shows the car at a glance (Home) and leads to the apps.
- **Every app talks to one gateway** for live data and history. The owner may have a permanent
  device (the Brain), only their phone with the gateway app, or nothing yet; the design handles
  all of these calmly.
- **On the Brain the apps are installed onto the car's computer.** Any phone or screen in the car
  opens them from there, and the Brain's settings are the front door's pages.

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
- **A Home** that shows the car at a glance, faults first, and is the jumping-off point to the
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
<ostler>
  <!-- Front door: ostler.app, also the Brain's own console -->
  <app id="ostler" repo="ostler-app-hub" role="front-door">
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
    <page id="home"/>
    <page id="apps"/>                  <!-- gallery: install / open -->
    <page id="garage">
      <page id="vehicle"/>
      <page id="add-vehicle"/>
    </page>
    <page id="devices">
      <page id="gateway"/>
      <page id="nodes"/>               <!-- each links to the node's own page -->
      <page id="adapters"/>
    </page>
    <page id="permissions">
      <page id="app-access"/>
      <page id="access-log"/>
    </page>
    <page id="outputs"/>               <!-- Home Assistant, RealDash, ... -->
    <page id="settings">
      <page id="account"/>
      <page id="theme"/>
      <page id="units"/>
      <page id="sharing"/>
    </page>
  </app>

  <app id="logs" repo="ostler-app-trips">
    <page id="logs-list"/>
    <page id="statistics"/>
    <page id="log-summary"/>
    <page id="playback"/>
    <page id="map"/>
    <page id="export"/>
  </app>

  <app id="diagnostics" repo="ostler-app-diagnostics">
    <page id="overview"/>
    <page id="faults">
      <page id="fault-detail"/>        <!-- links to the drives it was seen on -->
    </page>
    <page id="live-data"/>
    <page id="tests" guarded="true"/>
    <page id="procedures"/>
    <page id="decode-lab"/>
    <page id="docs"/>
  </app>

  <app id="drive" repo="ostler-app-drive">
    <page id="drive-mode"/>
    <page id="edit-layout" parked-only="true"/>
  </app>

  <addons>
    <app id="security" repo="ostler-app-security"/>
    <app id="maintenance" repo="ostler-app-maintenance"/>
    <app id="friends-map" repo="ostler-app-map"/>
    <app id="social" repo="ostler-app-social"/>
    <app id="mesh"/>
  </addons>

  <!-- Native, Android only: needed only when there is no gateway device -->
  <gateway-app id="ostler-gateway" platform="android">
    <page id="first-run"/>
    <page id="status"/>
    <page id="hardware"/>
    <page id="apps"/>
    <page id="permissions" shared-with="ostler"/>
    <page id="outputs" shared-with="ostler"/>
    <page id="floating-gauge"/>
  </gateway-app>

  <!-- Small built-in page on each node -->
  <node-page>
    <page id="status"/>
    <page id="signals"/>
    <page id="wifi-setup"/>
    <page id="firmware"/>
  </node-page>
</ostler>
```

`ostler-app-drive` is a new repo; `ostler-app-trips` holds Logs.

## Changelog

- 1.0 (2026-10-11): written from the owner's structure discussion of 2026-10-11 (ADR-0049
  v1.3).
