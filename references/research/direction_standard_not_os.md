---
title: "Direction — Ostler as an open vehicle-data standard and app suite, not an OS: synthesis of the October 2026 direction round, with the owner's decision list"
area: references
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [references/research/direction_feed_standards.md, references/research/direction_host_platforms.md, references/research/direction_headunit_ecosystem.md, references/research/direction_repo_audit.md, references/research/direction_positioning.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md]
summary: >
  Recommendation: stop building an operating system inside an operating system. Ostler becomes an open vehicle-data standard (a profile of COVESA VISS 3.2 over our VSS tree, with an Android binding), a reference node that stays the only write path, one required "Ostler" service app on each Android phone or head unit that owns the node link, the gate client, driving state and alerts and serves the feed, and a small suite of first-party native Android apps with their own widgets: Diagnostics, Dash, Trips, then Security. No launcher in v1. The Brain becomes optional. Apps are built the cheap way first: a native Kotlin shell, widgets and services around our existing React pages in a WebView, moving screens to native only where it pays. The theme work is kept but re-targeted to token packs, gauge and widget styles and the Ostler apps. Synthesises five research notes; ends with 30 owner decisions.
---

# Direction: a standard and an app suite, not an OS

**Status:** draft for the owner, 2026-10-08. Nothing accepted changes until the owner
answers the decision list at the end. The research behind it:

| Note | Question |
|---|---|
| [Feed standards](direction_feed_standards.md) | which standard every app's feed should follow |
| [Host platforms](direction_host_platforms.md) | how apps get the feed and draw widgets on each host |
| [Head-unit ecosystem](direction_headunit_ecosystem.md) | what owners already use, and whether a launcher adds value |
| [Repo audit](direction_repo_audit.md) | what we keep, re-target or drop, and the rewrite cost |
| [Positioning](direction_positioning.md) | what Ostler should be, against its precedents |

## 1. The problem

The owner shared a chat about the Dudu7 head unit whose rule is "don't build an operating
system inside an operating system". The repo audit confirms it. ADR-0046 makes Ostler an
empty OS with its own launcher, Store, app runtime and theme engine, all inside one web
app. The fatal flaws, with evidence in the audit:

1. **The third-party app wall.** One web app cannot host Waze, Spotify or Home Assistant.
   Owners on Android head units want all three beside Ostler.
2. **Audio focus.** Since Android 12 the system manages audio focus between apps. Our "OS"
   would be one app and could never duck Spotify or a navigation prompt.
3. **No home for the services on Android.** The recorder, accounts and app backends are
   Python on the Brain. Without a Brain, an Android phone or head unit has nowhere to run
   them.
4. **The size of the OS.** A launcher, a Store, an app runtime and a skin engine are more
   than one owner with agents can build and keep working.

Serious, not fatal: one WebView crash takes everything down; a Store that downloads code
into a phone app breaks store rules; Android widgets cannot be live gauges.

**The good news.** Almost all of the ADR-0046 OS is unbuilt: the launcher, Store, runtime
and theme engine exist only as specs. What is built is the part that survives: about
27,700 lines of Python services, the node firmware with its C decoder and C gate, the D2
pack, VSS and the module bus. Changing direction costs specs, not code
([repo audit](direction_repo_audit.md)).

## 2. The recommendation

Ostler is **an open way to get a car's data into the apps people already use, safely**:

1. **The Ostler Feed, an open standard.** A small profile of COVESA **VISS 3.2** over the
   **VSS** tree we already use (ADR-0016). Reads and subscriptions follow VISS. Writes do
   not: they go through one `ostler.action` operation into the ADR-0033 tiers and the node
   gate. Two bindings:
   - **Android:** a bound service (one AIDL interface carrying VISS JSON) plus a read-only
     content provider for widgets and automation tools;
   - **LAN:** VISS over secure WebSocket, found by mDNS, on the Brain and later the node.

   The internal MQTT module bus stays internal; Home Assistant and OVMS topics stay
   exports ([feed standards](direction_feed_standards.md)).
2. **The node, unchanged.** It is the only path to the car's buses and guards every write.
   It also supplies what head units lack: ignition state and decoded data
   ([ecosystem](direction_headunit_ecosystem.md) §3).
3. **One required "Ostler" app per device.** On each Android phone or head unit it owns the
   node link in a `connectedDevice` foreground service, the gate client, driving state,
   alerts and the alarm path, pairing and sign-in, and serves the feed to every other app.
   It answers ADR-0042's objection to separate apps: the lockout, the gate client and the
   sign-in live once, in this app. This is how the Home Assistant companion app works.
4. **A few first-party native apps, each with its own widgets:** Diagnostics, Dash (gauges
   and widget packs), Trips, then Security when Guardian ships. Widgets show glanceable
   values at about 1 Hz; live gauges run in the app, in a split-screen pane or an optional
   floating overlay ([host platforms](direction_host_platforms.md) §5).
5. **No launcher in v1.** Our widgets live on the launcher the device already has. Custom
   launchers are fragile on the head units we target, and owners complain about sleep and
   wake, not launchers. Revisit only if a test on two head units shows our apps or widgets
   die on ignition-off when a home app would survive.
6. **The Brain becomes optional.** Node plus phone, or node plus head unit, is a complete
   product. The Brain stays for people who want a box: long recording, cameras, Home
   Assistant, the decode lab and the web console.
7. **SDKs:** an Android client library under a permissive licence first, then web and
   Python. Third-party apps use the same feed as ours.

**How the apps are built: the cheap way first.** Each app is a native Kotlin shell (its own
process, widgets, notifications, MediaSession where needed) around our existing React pages
in a WebView, with screens moved to native only where it pays. The audit costs this at
about 2–4 months for Diagnostics, Trips and Security with widgets, against 6–9 months for a
fully native rewrite and 6–10 months to finish the web OS. Kotlin is a new language under
ADR-0035 and needs its own ADR.

**What we keep from the current plan:**
- the React UI, as the Brain's web console and as pages inside the apps;
- the designer brief, re-scoped to per-app screens and widgets (about 108 of 424 new
  screens are dropped: the launcher, the Store and the app frame);
- the theme work, re-targeted (§4);
- the 17 app repos, which are empty, become Android projects where they still apply.

**What we drop or park:** the empty OS (ADR-0046's launcher, dock, drawer, app runtime and
our own audio focus), the in-app Store as a way to ship code, the Android launcher idea
(ADR-0048, parked), and own Radio, Media, Phone and Navigation apps, which Android and the
head unit already do (owner decision 9).

## 3. The standard in more detail

| Part | Decision recommended | Source |
|---|---|---|
| Data model | VSS 6.1 tree, plus the `Vehicle.Ostler.*` overlay | ADR-0016 |
| Messages | VISS 3.2 `get`, `subscribe`, `unsubscribe`, metadata; values `{value, ts}` plus optional `c`, `stale`, `src`, `unit` | [feed standards](direction_feed_standards.md) §3 |
| Writes | VISS `set` refused on car paths; one `ostler.action` → ADR-0033 tiers → node gate; Tier 2+ confirmed in the Ostler app's own screen | §4 there |
| Android binding | bound service, one AIDL file, `getVersion()`, VISS JSON strings; content provider for snapshots | §5 there |
| LAN binding | `wss` with subprotocol `VISSv3`, mDNS `_ostler-feed._tcp` | §6 there |
| Auth | Android: consent pinned to the calling package and its signing key. LAN: Signal K-style access request approved by the owner, token scoped by ADR-0033 category and ADR-0029 data class | §7 there |
| Versioning | VISS subprotocol, `getVersion()`, `Server.Support.Ostler.Profile`, the VSS pin | §8 there |

Signal K is the precedent and the warning: an open data standard plus a reference server
plus apps worked for boats, but its written spec stalled while the server defined the
behaviour. So the spec and the Ostler app ship together, with conformance tests.

## 4. Theming, kept and re-targeted

The owner likes the theming. Without a web OS it lives in three places:

1. **A token pack** (the 22 built-in themes from the design bundle, as data) compiled into
   each Ostler app's theme. The Ostler app holds the active theme, so every Ostler app
   follows it. "Follow system colours" (Material You) is an option.
2. **Widget and gauge styles** as widget packs: gauge faces, needles and dial layouts as
   options on our AppWidgets and in-app gauges, bound to VSS paths so they work in any
   vehicle (RealDash's channel-file problem avoided).
3. **Skins for the Ostler apps' own pages** (the WebView pages can still take CSS against
   the documented hooks), plus a launcher skin if a launcher is ever built.

The theme engine spec's six-layer skin engine is parked; its token schema, theme options,
safety render check, protected surfaces and required parts carry over. Whether skins may
still restyle safety colours (the openness round) is owner decision 18.

## 5. Interop

In order of value for cost ([ecosystem](direction_headunit_ecosystem.md) §6):

1. **RealDash output:** its CAN-over-TCP protocol is public; one channel file gives every
   RealDash dashboard Discovery 2 data.
2. **Home Assistant** over MQTT discovery (already an export).
3. **Raise CAN-box emulation**, so the head unit's own screens show doors and reverse.
4. **Torque as an input** for OBD-only cars.

## 6. Risks

- **Sleep and wake on head units.** They force-stop apps 20–30 s after ignition off;
  stopped apps miss `BOOT_COMPLETED`. Every wake is a cold start; per-unit setup guidance
  is needed. Bench test on two units first.
- **Widgets are slow by design.** About 1 Hz pushed from a running service; no live gauges
  on the home screen.
- **Play policy:** foreground-service declarations with a video; developer verification,
  which also covers sideloaded apps, from 2027.
- **Signal K's trap:** a spec that lags the implementation. Conformance tests from day one.
- **A new language (Kotlin)** for one owner with agents; the hybrid route limits it to the
  shells.

## 7. What changes in the repo (only after the owner decides)

- A new ADR (draft: [ADR-0049](../../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md))
  supersedes ADR-0046's OS boundary (keeping its safety list and hard lines) and ADR-0042's
  "one app" rule, parks ADR-0048 and needs a Kotlin ADR under ADR-0035.
- The app-model, app UI model, Store and launcher specs are superseded or parked; the
  head-unit apps spec is cut back; the theme engine spec is re-scoped (§4).
- The brief is re-scoped to per-app screens and widgets.
- PR #65 is merged with its theme engine marked as re-scoped, or rebased on this ADR
  (decision 27).

## 8. Decisions for the owner

Reply "approve all", or by number. Each gives the recommendation, then the alternative.

**What Ostler is**
1. **Direction:** a standard plus one Ostler app plus a few native apps, no launcher (A,
   built the hybrid way). *alt:* keep the web OS (B).
2. **Mission statement** as in §2's first line and the [positioning](direction_positioning.md)
   note. *alt:* rewrite it together.
3. **Supersede ADR-0046's OS boundary and ADR-0042's one-app rule** with ADR-0049, keeping
   ADR-0046's safety list and hard lines. *alt:* amend them in place.

**The standard**
4. **Adopt VISS 3.2 as "Ostler Feed profile 1"** over VSS. *alt:* our own JSON over MQTT.
5. **Android binding:** bound service plus content provider, VISS JSON on the wire. *alt:*
   a typed AIDL API.
6. **LAN binding:** VISS over `wss` with mDNS. *alt:* MQTT 5 for apps too.
7. **Writes only through `ostler.action`** and the Ostler app's own confirmation. *alt:*
   no third-party writes at all.
8. **Licences:** the spec CC BY-SA, the client SDKs Apache 2.0, the Ostler app AGPL.
   *alt:* everything AGPL.
9. **Offer the Android binding to COVESA** once it works. *alt:* keep it ours.

**Apps and hosts**
10. **First hosts:** Android head units and Android phones, minimum Android 10. *alt:*
    Android 12 minimum.
11. **One required Ostler app** owning the node link and the feed. *alt:* each app talks to
    the node itself.
12. **First apps:** Ostler, Diagnostics, Dash; then Trips; Security with Guardian. *alt:*
    Diagnostics only first.
13. **Build the hybrid way:** Kotlin shells around our React pages, native where it pays.
    *alt:* fully native (Jetpack Compose) from the start.
14. **Kotlin ADR** under ADR-0035. *alt:* a cross-platform toolkit (Flutter or React
    Native).
15. **Drop own Radio, Media, Phone and Navigation apps;** feed Waze, Spotify and the head
    unit's apps instead. *alt:* keep them on the roadmap.
16. **No launcher in v1;** test sleep and wake on two head units first. *alt:* build
    "Ostler Home" now.
17. **Live gauges** in the Dash app, a split-screen pane or an optional overlay; widgets at
    about 1 Hz. *alt:* widgets only.

**Theming and design**
18. **Safety colours:** restylable under the render check, as the openness round decided.
    *alt:* fixed again in native apps.
19. **Theme work re-targeted** to token packs, widget and gauge styles and app skins (§4);
    the six-layer skin engine parked. *alt:* keep the full skin engine for the WebView
    pages.
20. **Re-scope the brief** to per-app screens and widgets; drop the launcher, Store and
    app-frame screens. *alt:* keep the full brief for later.

**Hardware**
21. **The Brain is optional,** not needed for v1. *alt:* the Brain stays required.
22. **Head-unit link to the node:** USB serial first, BLE for phones, Wi-Fi as fallback;
    amend ADR-0039. *alt:* Wi-Fi only.
23. **Bench test two head units** (one FYT UIS7862, one UIS7870 such as a Dudu7) for sleep,
    widgets and the USB link before building. *alt:* build first.

**Interop and distribution**
24. **RealDash output first,** then Home Assistant, then Raise CAN-box emulation. *alt:*
    Home Assistant first.
25. **Distribution:** Play Store plus F-Droid plus direct APK; register as a verified
    developer. *alt:* direct APK only.
26. **No Store of our own** for code; the Store spec becomes a catalogue of packs and themes
    as data. *alt:* drop the Store spec entirely.

**Housekeeping**
27. **PR #65:** merge it now with a note that the theme engine is re-scoped by ADR-0049.
    *alt:* rebase it on ADR-0049 first.
28. **The 17 app repos:** keep Diagnostics, Trips, Security, Maintenance, Decode lab, Map,
    Social and Community as future Android projects; archive Radio, Audio, Media, Camera,
    Navigation and Phone (decision 15); keep the widget, theme and catalogue repos as data
    repos.
    *alt:* archive everything except the first three apps.
29. **A spec repo** `ostler-feed` for the standard, with conformance tests. *alt:* keep it
    in `ostler`.
30. **UX first still applies** to the Ostler app and the first apps: a short brief per app
    before building. *alt:* build the Ostler app straight from the feed spec.
