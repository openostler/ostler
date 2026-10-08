---
title: "ADR-0048 — Ostler as an Android launcher: the same single Android app can be the home app of a phone, tablet or Android head unit"
area: decisions
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, specs/2026-10-07-theme-engine-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-store-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Proposed (draft for the owner). The owner said Ostler "can also be a launcher for Android"; the theme engine spec §2.6 describes it. This ADR makes it a platform decision: the one Ostler Android app (ADR-0042) may also declare the Android home-screen role, so an owner can set it as the launcher of a phone, tablet or Android head unit. As a launcher it hosts native Android widgets through AppWidgetHost next to Ostler widgets, lists installed Android apps in the drawer and dock, reads Android icon packs (appfilter.xml), can use or set the system wallpaper and can seed colours from Material You. It never downloads code, and phone add-ons stay bundled or declarative. The Moving rules apply to hosted Android widgets: those without a Moving template are hidden while Moving. It changes nothing in ADR-0046's OS boundary. Risks: store policy for launchers, old WebViews on cheap head units, and the privacy of hosting other apps' widgets. Five owner decisions.
---

# ADR-0048 — Ostler as an Android launcher

- **Date:** 2026-10-08
- **Status:** proposed (draft). Basis: the owner's "this can also be a launcher for Android"
  (2026-10-07) and the [theme engine spec](../specs/2026-10-07-theme-engine-design.md) §2.6,
  which holds the theming detail. Raised in the owner's review of the theme branch on
  2026-10-08 as a platform decision that needs its own ADR.

## Context

- [ADR-0046](adr-0046-empty-os-every-app-an-add-on.md) makes Ostler an Android-style OS:
  a launcher, a dock, an app drawer, widgets and a Store. On Android hardware the natural
  next step is for Ostler to *be* the launcher.
- [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) fixes one Ostler app
  per store, no separate Android apps, and phone add-ons that are bundled or declarative,
  never fetched code.
- Many aftermarket head units run Android. Owners want Ostler as the home screen, with their
  other Android apps (music, navigation, messaging) one tap away.

## Decision drivers

- One app, not a second product to maintain.
- Store rules for code and for home-screen apps.
- The driving rules must hold for everything shown while Moving, including other apps'
  widgets.
- Owners keep their Android apps and icon packs.

## Decision

1. **Same app, extra role.** The one Ostler Android app also declares the home-screen role
   (an intent filter for the home category). Owners choose it as the launcher in Android's
   settings; nothing changes for owners who don't.
2. **What the launcher adds:**
   - native Android widgets hosted through `AppWidgetHost` on the same home pages as Ostler
     widgets; their content is drawn by their own apps, and skins style only the frame;
   - installed Android apps in the app drawer and dock, next to Ostler apps;
   - icon packs that also map Android apps, including the `appfilter.xml` format used by
     Nova, Lawnchair and others;
   - the background can use the Android system wallpaper, or be set as it;
   - skins may seed colours from Material You (Android 12+), off by default.
3. **Driving rules apply to hosted widgets.** On a driver-facing head unit while Moving, a
   hosted Android widget is shown only if it maps to a Moving template; otherwise it is
   hidden. Editing stays Parked only.
4. **WebView floor.** The shell runs in Android System WebView. Below the theme engine's
   browser floor the launcher shows the built-in look with a plain message, never a broken
   screen (theme engine §7, TE1).

## What changes and what stays

| Changes | Stays |
|---|---|
| The Android app can also be the home app | One Ostler app per store (ADR-0042) |
| Android apps and widgets appear in the drawer and on pages | Ostler never downloads or runs fetched code; phone add-ons stay bundled or declarative |
| Icon packs may map Android apps | ADR-0046's OS boundary and the Moving rules |

## Risks

- **Store policy.** Launchers must handle the home role, the default-app prompt and
  "query all packages" permission rules; review may ask for a justification.
- **Old WebViews.** Cheap Android head units often ship an old WebView that can't be
  updated. They fall back to the built-in look, so full skins won't run there.
- **Privacy of widget hosting.** A host can see the widgets it shows. Ostler must never read,
  store or record their content, and must never include it in trips or shares.

## Confirmation

- A test head unit and a phone set Ostler as the launcher, host one Android widget, and show
  it Parked and hide it Moving.
- A WebView below the floor shows the fallback message.
- An `appfilter.xml` pack maps at least one Android app icon.

## Consequences

- Owners can run an Android head unit with Ostler as the whole home screen.
- The launcher spec and theme engine spec gain an Android section (engine §2.6 already has it).
- The Store listing explains the launcher role.

## Alternatives considered

- **A separate Ostler Launcher app.** Rejected: it breaks ADR-0042's one-app rule and
  doubles maintenance.
- **No launcher role.** Rejected by the owner's direction.

## Relation to other ADRs

- [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md): keeps one app per
  store and the no-fetched-code rule.
- [ADR-0046](adr-0046-empty-os-every-app-an-add-on.md): the launcher is part of the OS's
  system UI; this ADR adds an Android host for it.

## Decisions for the owner

1. **Launcher role default.** *Recommend:* the role is offered, never set automatically;
   first run on Android asks once. *Alternative:* first run on a head unit sets it by default.
2. **WebView floor.** *Recommend:* the theme engine's floor with the built-in-look fallback.
   *Alternative:* refuse to run as the launcher below the floor.
3. **Android widgets while Moving.** *Recommend:* hidden unless mapped to a Moving template
   (media, map). *Alternative:* hide every Android widget while Moving.
4. **Widget-host privacy.** *Recommend:* never read, store or record hosted widgets' content;
   stated in the privacy notes. *Alternative:* none; this is the minimum.
5. **Material You.** *Recommend:* off by default for skins with their own palette.
   *Alternative:* on by default on Android 12+.

## Changelog

- 2026-10-08 — v0.1, proposed: drafted from theme engine spec §2.6 after the owner's review
  of the theme branch.
