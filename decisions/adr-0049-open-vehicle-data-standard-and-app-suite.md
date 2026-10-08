---
title: "ADR-0049 — Ostler is an open vehicle-data standard and an app suite, not an operating system"
area: decisions
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [references/research/direction_standard_not_os.md, references/research/direction_feed_standards.md, references/research/direction_host_platforms.md, references/research/direction_headunit_ecosystem.md, references/research/direction_repo_audit.md, references/research/direction_positioning.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md]
summary: >
  Proposed (draft for the owner). Ostler stops being an operating system inside an app and becomes: the Ostler Feed, an open standard (a profile of COVESA VISS 3.2 over the VSS tree, with an Android binding and a LAN binding); the node, unchanged, as the only write path; one required Ostler app per Android phone or head unit that owns the node link, the gate client, driving state, alerts and sign-in and serves the feed; and a few first-party native apps with their own widgets (Diagnostics, Dash, Trips, then Security), built first as native shells around our React pages. No launcher in v1; the Brain is optional. Would supersede ADR-0046's OS boundary (keeping its safety list and hard lines) and ADR-0042's one-app rule, and park ADR-0048. The decisions are the 30 items of the direction note.
---

# ADR-0049 — An open vehicle-data standard and an app suite

- **Date:** 2026-10-08
- **Status:** proposed (draft). It records the owner's 2026-10-08 direction ("we should
  instead probably be making a standard … the apps can pull their data all the same way")
  and the [direction note](../references/research/direction_standard_not_os.md), which holds
  the evidence and the 30 decisions. It takes effect only when the owner answers them.
- **Would supersede in part:** [ADR-0046](adr-0046-empty-os-every-app-an-add-on.md) (the OS
  boundary: launcher, dock, drawer, app runtime, Store as code distribution, own audio
  focus; its safety list and hard lines stay) and
  [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) (one app per store).
- **Would park:** ADR-0048 (Ostler as an Android launcher, proposed on the theme branch).

## Context

- ADR-0046 builds an operating system inside one web app. On Android it cannot host other
  apps, cannot manage audio focus (the system does since Android 12), has nowhere to run
  the Python services without a Brain, and is larger than one owner can maintain.
- Almost all of that OS is unbuilt. The built parts (node, gate, decoders, packs, VSS,
  module bus, Python services) are the durable value.
- The owner chose Android head units and Android phones as the first hosts.

## Decision (proposed)

1. **The Ostler Feed** is an open standard: VSS names, VISS 3.2 messages for reads and
   subscriptions, one `ostler.action` operation for writes (ADR-0033 tiers, the node
   gate), an Android binding (bound service plus content provider) and a LAN binding
   (`wss`, mDNS).
2. **The node** stays the only path to the car's buses and guards every write.
3. **One required Ostler app** per Android device owns the node link, the gate client,
   driving state, alerts and the alarm path, pairing and sign-in, and serves the feed.
   Other apps, ours and third parties', bind to it.
4. **First-party apps** are separate native Android apps with their own widgets:
   Diagnostics, Dash, Trips, then Security. They are built first as Kotlin shells around
   our React pages in a WebView; screens move to native where it pays.
5. **No launcher in v1.** Widgets live on the device's own launcher.
6. **The Brain is optional.** Node plus phone or head unit is a complete product.
7. **Theming** is re-targeted: token packs, widget and gauge styles, and skins for the
   Ostler apps' own pages. The six-layer skin engine is parked.

## What stays

The node and its gate, the C decoder, packs, VSS, the module bus (internal), the Python
services on the Brain, accounts and sharing, the safety list and hard lines of ADR-0046 and
the openness round, UX first for our own apps.

## Consequences

- The app-model, app UI model, Store and launcher specs are superseded or parked; the
  head-unit apps spec is cut back.
- A Kotlin ADR is needed under ADR-0035.
- ADR-0039 gains a USB serial link from the node to a head unit.
- The designer brief is re-scoped to per-app screens and widgets.

## Alternatives considered

- **Keep the web OS (ADR-0046).** Rejected by the research: four fatal flaws.
- **Fully native apps from the start.** Kept as the end state; the hybrid route ships
  sooner.
- **Our own launcher now.** Deferred until a sleep and wake test shows it is needed.

## Changelog

- 2026-10-08 — v0.1, proposed: drafted from the direction research round.
