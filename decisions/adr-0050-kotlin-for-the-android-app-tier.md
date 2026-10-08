---
title: "ADR-0050 — Kotlin for the Android app tier: one shared hybrid shell around our React pages, Jetpack, Glance for the feed widget, minimum SDK 29"
area: decisions
status: locked
version: 1.0
updated: 2026-10-08
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0004-react-typescript-ui.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0045-ux-first.md, references/research/direction_standard_not_os.md, references/research/direction_host_platforms.md, references/research/direction_repo_audit.md]
summary: >
  Accepted: approved by the owner on 2026-10-08 (direction decisions 10, 13, 14, 35 and 37). Kotlin is the language of the Android app tier, amending ADR-0035, whose UI row put the phone app in a Capacitor wrapper. Every Ostler Android app (the gateway app, Diagnostics, Trips, Security, Maintenance and the add-ons) is built from one shared app template: a native Kotlin shell (its own process, services, notifications, settings, the VISS client and the theme-pack loader) around our existing React pages in a WebView, with screens moved to native Jetpack Compose only where it pays. Jetpack libraries throughout; the gateway app's feed widget uses Jetpack Glance at about 1 Hz; minimum SDK 29 (Android 10). The React UI stays TypeScript and stays the Brain's web console. Python, C and the rest of ADR-0035 are unchanged.
---

# ADR-0050 — Kotlin for the Android app tier

- **Date:** 2026-10-08
- **Status:** accepted. Approved by the owner on 2026-10-08 ("I agree with everything";
  [direction note](../references/research/direction_standard_not_os.md) decisions 10, 13,
  14, 35 and 37). It is the Kotlin ADR that
  [ADR-0049](adr-0049-open-vehicle-data-standard-and-app-suite.md) asks for. **Amends**
  [ADR-0035](adr-0035-languages-by-tier.md) (the UI row: the phone app is no longer the web
  build in a Capacitor wrapper); dated amendment note there. Evidence:
  [host platforms](../references/research/direction_host_platforms.md),
  [repo audit](../references/research/direction_repo_audit.md).

## Context

- ADR-0049 makes Ostler a set of separate Android apps: a required gateway app, then
  Diagnostics (with Decode lab), Trips, Security, Maintenance and add-ons.
- Each needs things a web build in a wrapper does badly: foreground services (the gateway's
  node link), a home-screen widget, notification channels, Bluetooth and USB access, and
  Android's package identity for the permissions controller.
- ADR-0035 has no language for native Android code. Its UI row says the phone app is "the
  same build in a native wrapper such as Capacitor".
- We already have React pages for Diagnostics, Trips, Security and more. Throwing them away
  costs months (the audit: 6–9 months native against 2–4 months hybrid).

## Decision drivers

- Ship the first apps soon, from code we already have.
- One template, so every app looks and behaves the same and follows one theme.
- Use the platform's own tools, not a cross-platform layer, where Android rules matter
  (services, widgets, identity).
- Keep the number of languages small for one owner with agents.

## Decision

1. **Kotlin** is the language for Android apps. Java is not used for new code.
2. **The hybrid shell.** Every app is a native Kotlin shell around our React pages in a
   WebView:
   - the shell owns the process, services, notifications, settings, permissions requests,
     deep links and back navigation;
   - the pages are the existing React UI, served from the APK's assets, not downloaded;
   - a screen moves to native **Jetpack Compose** only where it pays: speed, battery,
     a platform API, or a page the WebView cannot do well.
3. **One shared app template** (direction decision 35), used by every Ostler app:
   - the Kotlin shell;
   - the **VISS client** (ADR-0051): it gets the app's token from the gateway app, then
     speaks VISS over the loopback WebSocket; the pages use the same connection through a
     small bridge or their own TypeScript VISS client;
   - the **theme-pack loader**: it reads the active theme from the gateway app and applies
     it to the native views and, as CSS tokens, to the pages.
4. **Jetpack** libraries throughout (Lifecycle, Compose, DataStore, WorkManager where a job
   must survive), with Gradle Kotlin DSL builds.
5. **Glance for the feed widget.** The gateway app's normal feed widget is a Jetpack Glance
   app widget, updated at about 1 Hz from the running service. No other app ships widgets
   in v1.
6. **Minimum SDK 29** (Android 10), as direction decision 10 chose; target SDK follows the
   store's current rule.
7. **Unchanged:** the React UI stays TypeScript (ADR-0004) and stays the Brain's web
   console; Python and C keep their tiers (ADR-0035).

## Confirmation

- The template builds an APK that runs on Android 10 and on the two bench head units.
- A template test: a new app built from it gets a token from the gateway app, reads a
  basic signal over VISS and follows a theme change without a restart.
- The feed widget keeps its 1 Hz update for an hour on the bench units while the gateway
  service runs.

## Consequences

- ADR-0035's table gains an Android row (Kotlin) and its UI row loses the Capacitor
  wrapper; dated amendment there.
- The template lives in its own repo or in `ostler-feed`'s SDK, decided when it is created
  (ADR-0034 rules).
- CI gains an Android build (Gradle) beside Python, C and the UI.
- Contributors to the apps need Kotlin as well as TypeScript; the hybrid route keeps the
  Kotlin part to the shells.

## Alternatives considered

- **Capacitor wrapper (ADR-0035 as written).** Rejected: weak for foreground services,
  widgets and package identity, which the gateway app needs.
- **Fully native Compose from the start.** Kept as the end state; the hybrid route ships
  sooner.
- **Flutter or React Native.** Rejected: a third UI toolkit beside React and Compose, and an
  extra layer between us and Android's service and widget rules.

## Relation to other ADRs

- **ADR-0035:** amended (Android row; UI row without Capacitor).
- **ADR-0004:** the React pages stay; they now run inside the shell.
- **ADR-0049:** the apps this template builds.
- **ADR-0051:** the VISS client in the template.
- **ADR-0045:** a short UX brief per app before building still applies.

## Changelog

- 2026-10-08 — v1.0, accepted: approved by the owner on 2026-10-08 (direction decisions
  10, 13, 14, 35 and 37).
