---
title: "ADR-0054 — One native cross-platform shell: Compose Multiplatform cards, per-device layouts, the map as home on head units, and how cards and apps are delivered"
area: decisions
status: locked
version: 1.1
updated: 2026-10-17
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, decisions/adr-0048-ostler-as-an-android-launcher.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0047-openness-round.md, references/research/touch_tiling_edit_mode.md, references/research/responsive_tile_sizes.md]
summary: >
  Accepted: approved by the owner on 2026-10-16 ("Agreed"; "I agree, fold it into the ADRs"). The shell and every card are one Kotlin Multiplatform codebase drawn with Compose Multiplatform, native on Android Automotive head units, Android phones and tablets, iPhone and desktop, plus a small web build for viewing in a browser. ADR-0052's ideas stay (page contract, size classes, layout format, cursor, Android-style edit mode) but become shared data and a Kotlin library, not web code; this reverses ADR-0049 v1.3's every-screen-a-PWA and ADR-0050 v1.1's Kotlin-for-the-gateway-only. One app with a saved layout per device: on a head unit the live map is the desktop with app windows tiled over it, an Android-style taskbar, guidance cards and a music widget (v1.1: the designer's approved shell of 2026-10-17 replaces the card-page carousel of v1.0); on a phone the map shows where the car is and the cards are security, lock, remote start and trips. Cards come from four sources: built-in Compose cards, declarative cards (data templates bound to VISS paths and actions, no downloaded code), Android app widgets (Android only, with the user's consent) and sandboxed web cards as an escape hatch. No APK store: our own apps update through an F-Droid-format repo only on our own head-unit image; elsewhere the normal stores. ADR-0048 is unparked as Ostler Lite, an ordinary Android launcher with the map as its background that mimics the full Android Automotive build, which comes first and sets the direction.
---

# ADR-0054 — One native cross-platform shell, cards, and the map as home

- **Date:** 2026-10-16
- **Status:** accepted. Approved by the owner on 2026-10-16 in the head-unit design session
  ("Agreed"; "Let's do that, I agree, fold it into the ADRs").
- **Amends:** [ADR-0049](adr-0049-open-vehicle-data-standard-and-app-suite.md) v1.3 (screens as
  PWAs; no widget apps; launcher parked), [ADR-0050](adr-0050-kotlin-for-the-android-app-tier.md)
  v1.1 (Kotlin for the gateway app only), [ADR-0052](adr-0052-mfd-pages-sizes-and-the-shell-library.md)
  §2 (the shell as a web library, "no launcher") and
  [ADR-0035](adr-0035-languages-by-tier.md) (the UI row).
- **Unparks:** [ADR-0048](adr-0048-ostler-as-an-android-launcher.md) as Ostler Lite (§6).

## Context

- ADR-0049 v1.3 made every screen a PWA, and ADR-0052 made the MFD shell a web library that
  every app bundles. ADR-0050 v1.1 kept Kotlin for the gateway app only.
- Since then the head-unit work (the Android Automotive flavour in
  `openostler/ostler-android-automotive`) has shown what a web shell costs in a car:
  - a web view of cards over a live map on an integrated GPU is the most expensive
    combination;
  - driving restrictions, car properties, media sessions, steering-wheel keys, the cluster
    and audio focus are native Android APIs, so a PWA reaches them only through a native
    bridge (two apps in one);
  - Android app widgets cannot be placed inside a web view (touch tiling research §4);
  - a launcher is a native activity.
- The owner wants cross-platform reach anyway: the same cards on the car and the phone, so
  "you can open the same cards the car uses", and the app not just a launcher.
- The owner also set the head-unit home direction (2026-10-16): the map is the real home
  screen, never covered full screen, with the tiler becoming an overlay of card pages.
- Ostler is an open, multi-vehicle platform that may one day ship as a sold head unit; nothing
  may be fixed to the reference Discovery 2.

## Decision drivers

- One codebase for the car, phones, tablets and desktop; native performance next to a map.
- Native access to car APIs and safety rules without a bridge.
- The same card, data and layout format everywhere.
- Customisable and modular, yet still beautiful: the system, not the user, keeps the design
  coherent.
- Allowed by every store's rules (no downloaded executable code where stores forbid it).
- Works offline and on cheap hardware.

## Decision

### 1. One Kotlin Multiplatform shell and card library

- The shell (tiling engine, size classes, page contract, layout format, cursor and focus, edit
  mode, moving rules, theme resolver) and Ostler's cards are **one Kotlin Multiplatform
  codebase drawn with Compose Multiplatform**, native on:
  - Android Automotive head units (the full Ostler flavour and Ostler Lite);
  - Android phones and tablets;
  - **iPhone, native** (owner, 2026-10-16);
  - desktop.
- **A small web build** (Compose for Web or a thin web renderer of the same layout and card
  format) for viewing in a browser without installing anything, for example a passenger's
  phone. Its maturity is checked before it carries anything more (U).
- **ADR-0052's model stays and becomes shared data:** the page contract, the five size classes
  from the tile's own box, the versioned layout format, two-level focus and the cursor, stacks,
  the Android-style zoom-out edit mode and the moving rules. The `ostler-shell` repo becomes a
  Kotlin Multiplatform library instead of a web library.
- Vehicle data stays **VISS v3 over VSS** (ADR-0051) on every device: locally on the head unit,
  through the gateway from a phone. Actions stay requests under ADR-0033.

### 2. One app, a saved layout per device

The app is not just a launcher. Every device runs the same shell and cards with its own
default layout, owned by the designer:

| Device | The map shows | Default cards |
|---|---|---|
| Head unit | Navigation | Media, vehicle glance, route, trip |
| Phone | Where the car is | Security, lock and unlock, remote start, fuel or charge, trips |
| Tablet or passenger | Route and ETA | Media, trip, places |

- A card shows only what the vehicle profile and connected hardware support (for example,
  remote start only where the car has hardware for it).
- **Remote actions** (unlock, remote start) need strong authentication, confirmation and the
  approvals of ADR-0033, and they respect local law (for example rules on leaving an engine
  running unattended).

### 3. On a head unit, the map is the desktop (v1.1: the approved shell)

> **v1.1 (owner, 2026-10-17, "This is the approved design"):** the designer's builder pack
> `ostler-aaos-2026-10-17` (taskbar demo, `SPEC.md`, `DECISIONS.md`) is the approved head-unit
> shell. It replaces v1.0's carousel of card pages. The pack lives with the head-unit flavour
> (`openostler/ostler-android-automotive`, builder summary in its Android Automotive skill,
> `references/ostler-shell-approved.md`); designer files stay out of this repo.

- **The live map is the desktop** and is never covered full screen. It centres the vehicle on
  the largest free area.
- **Apps open as windows on the passenger side,** 2/3 wide by default, leaving the driver third
  for the map. Users tile freely with Windows-style snap zones (quarters, halves, thirds, full
  screen, minimise), auto-tiling, dividers and push-aside; windows never overlap.
- **An Android-style taskbar** holds the apps button, pinned and running apps, app pairs and
  pinned layouts (any layout, even one app, can be pinned), the music chip and the turn chip; the
  driver end holds the temperature pill and one tray pill (status, clock, bell).
- **System panels** (tray drawer with quick controls and notifications, climate card, app
  drawer) rise from the bar on the driver side, dim the screen and never move the guidance cards.
- **Guidance cards** (turn and trip) move to free space when covered, fold when tight and
  minimise to the taskbar's turn chip; the turn card is never covered by panels.
- **Gestures:** swipe up on the bar for home, swipe up and hold for recents, edge swipes for
  back; no caption bars.
- **Cards in this ADR's sense** (§4) are the home widgets and tiles: the music widget (chip,
  card, tiled window) and vehicle cards, built from the same Compose card library as the phone.
- **Ostler Lite and phones** reuse the cards and as much of the shell as an ordinary app can
  host; the map must still be embeddable as a library.

### 4. Where cards come from

| Source | What it is | Where |
|---|---|---|
| **Built-in cards** | Ostler's own Compose cards, native and GPU-drawn | Everywhere |
| **Declarative cards** | A card as data: a designer template plus bindings to VISS paths and ADR-0033 actions, drawn natively by our renderer. No downloaded code, so Play and the App Store allow it. Shared and synced like layouts. | Everywhere |
| **Android app widgets** | Other apps' widgets hosted by our launcher, with the user's bind consent | Android only |
| **Web cards** | A sandboxed web view in one tile, for rich third-party content; an escape hatch, used sparingly | Everywhere |

- Cards follow the page contract: sizes, a summary value, ranked parts, per-action moving
  safety and VSS data requirements.
- **Keeping it beautiful:** users choose cards and sizes, not styles; cards come from
  designer-made templates with fixed size classes, the grid and theme tokens (ADR-0047 keeps
  style a default that themes may change); page and density limits are defaults (for example
  at most five pages); the defaults per device are the design, and a glance-time test on the
  bench comes before they freeze.
- **GPU:** native cards render in the app's own process beside the map surface. The shell caps
  card refresh rates and pauses cards that are off screen.

### 5. Delivery: no APK store

- Ostler does **not** become an APK store. Google Play forbids apps that download and install
  other apps or executable code from outside Play, sideloading needs a prompt per install on
  ordinary Android, and iPhone allows it only through EU alternative marketplaces.
- **On our own head-unit image:** our apps update from an F-Droid-format repository through a
  privileged installer included in the image; the Android image updates over the air; the host
  side (gateway services, audio, radio) updates as Linux packages.
- **Everywhere else** (Ostler Lite, phones, tablets, iPhone): the normal stores (Play, F-Droid,
  App Store).
- **Declarative cards and layouts** are data, synced through the gateway, not installs.

### 6. Ostler Lite and build order

- **The full Ostler Android Automotive flavour comes first** and sets the direction.
- **Ostler Lite** comes later: an ordinary Android launcher with the map as its background that
  mimics the full flavour, reusing its UIs and Ostler apps. It keeps the launcher, cards, map and
  Ostler apps; it cannot replace the system bar, notifications, other apps' styling, the cluster,
  the vehicle HAL or the audio architecture. ADR-0048 is unparked for this and rewritten against
  this ADR when Lite starts.
- **Name check:** "Lite" was the old name of the Diagnostics node (ADR-0039). Before Lite ships,
  confirm the name does not clash (owner).

## Confirmation

- A head-unit bench test: the map with two tiled app windows, guidance cards and the music card
  on the reference integrated GPU, with the map holding its frame rate.
- A cross-platform test: the same declarative card renders on the head unit, an Android phone
  and an iPhone from one definition.
- A store-rules check: the Play and App Store builds contain no code download path.
- A moving test: the moving rules of the approved shell (parked-only actions such as theatre
  mode) hold.
- A glance-time test of the default head-unit layout with real drivers before it freezes.

## Consequences

- `ostler-shell` is rewritten as a Kotlin Multiplatform library; the React pages become the
  Brain's web console and the web build's reference until replaced.
- The app template of ADR-0050 becomes the Compose Multiplatform template for every Ostler app.
- A declarative card format and renderer join the page contract spec.
- The navigation app ships as an embeddable library as well as an app.
- The head-unit flavour builds the approved shell from the designer's pack; its page list
  (`docs/design-brief/` in `ostler-android-automotive`) tracks the frames.

## Alternatives considered

- **PWAs for the cards, a native launcher for the map** (ADR-0049 v1.3 plus a launcher).
  Rejected: web views over the map cost GPU and memory on the target hardware, need a native
  bridge for car APIs, and cannot host Android widgets.
- **Ostler as an APK store.** Rejected: store policies and the iPhone; works only on our own
  image, where the F-Droid-format repo covers it.
- **Native Android only, iPhone on the web.** Rejected by the owner: iPhone native.
- **Flutter or React Native.** Not chosen: the Android tier is already Kotlin (ADR-0050) and the
  car APIs are Android-native; Compose Multiplatform keeps one language.

## Relation to other ADRs

- **ADR-0049:** amends v1.3 (screens as PWAs), "no widget apps" (Android widgets and declarative
  cards are allowed as cards, not as separate apps) and the parked launcher. The open feed, the
  gateway, the node as the only write path and the separate apps stand.
- **ADR-0050:** Kotlin again covers every Ostler app, now Kotlin Multiplatform with Compose
  Multiplatform; Glance stays for the Android feed widget.
- **ADR-0052:** §2's web library and "no launcher" are replaced by §1 and §6 here; §2a, §2b, §3,
  §4, §4a and §5 carry over as the shell's behaviour.
- **ADR-0048:** unparked as Ostler Lite.
- **ADR-0051:** VISS on every device. **ADR-0033:** actions and approvals. **ADR-0029:** users
  and sharing for phone access to the car. **ADR-0047:** style stays a default.
- **ADR-0035:** the UI row gains Kotlin Multiplatform; TypeScript stays for the Brain's web
  console.

## Changelog

- 2026-10-16 — v1.0, accepted by the owner in the head-unit design session.
- 2026-10-17 — v1.1, amended by the owner: the designer's approved shell (map as desktop, tiled
  app windows, taskbar, panels, guidance cards, music widget) replaces the card-page carousel in §3.
