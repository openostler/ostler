---
title: "Home Assistant's companion apps, cloud, foundation and community — what Ostler can copy for its phone app, car displays, Ostler Cloud, certification, hardware and community (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, docs/ecosystem.md, references/research/connectivity_uplink.md, references/research/driver_distraction_rules.md, references/research/product_family.md, references/research/third_party_adapters.md, references/research/ui/app_model.md]
summary: >
  Live research (2026-10-07) for the owner's line "we are building the automotive version of Home Assistant". HA's companion apps: sensors mostly off by default, actionable notifications (3 actions on Android, about 10 on iOS) and critical alerts, location by zones with an "exact / zone name only / never" choice per server, internal vs external URL by home SSID, onboarding by local discovery then login, widgets, Wear OS tiles and complications. In the car, HA's Android Auto and AAOS screens show favourite entities, a short set of controllable domains and navigation to zones, and read car sensors (fuel, EV battery, odometer, speed) back into HA through the Car API; its CarPlay app (since 2024.1) has Quick Access, Areas, Control and Servers tabs. Nabu Casa's paid cloud (USD 6.50 a month) is being renamed Home Assistant Link from 2026.12 because "Cloud" misled people; its relay is end-to-end (SniTun, GPL-3.0). The Open Home Foundation, a Swiss Stiftung, owns the code and brand; commercial partners must give it most of their profit; 2025 revenue CHF 8.84 m, 52 salaried staff, about 2.28 m homes (opt-in analytics times four). Community: Discourse forum, monthly releases with a week of beta, the Month of "What the Heck?!", HACS (now in the foundation, no security review), add-ons renamed Apps in 2026.2, Works with Home Assistant (CHF 500 a year, 19 partners, end devices only), hardware Green, Connect ZBT-2/ZWA-2 and Voice PE, Yellow ended 2025. Maps each to Ostler; Copy / Avoid / Decide.
---

# Home Assistant's companion apps, cloud, foundation and community (October 2026)

The owner: "we are building the automotive version of Home Assistant". This note looks at the
parts of Home Assistant (HA) around its core: the phone apps, what HA shows in cars, the paid
cloud, the foundation that owns it, and its community and hardware. It maps each onto Ostler's
plans: the one store app with native location, push and pairing
([ADR-0042](../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) decision 3;
[app-model §7.1](../../specs/2026-10-06-app-model-design.md)), the Phone & Comms
[companion bridge](../../specs/2026-10-07-phone-comms-addon-design.md), Ostler Cloud
([ADR-0028](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md) §6) and the
closed Ostler Community hub ([spec](../../specs/2026-10-07-community-hub-design.md)). Earlier
notes already cover HACS as an app-loading model ([app model](ui/app_model.md)), SniTun as
Ostler Cloud's transport ([connectivity §4](connectivity_uplink.md)) and car-screen rules
([driver distraction](driver_distraction_rules.md)); they are linked, not repeated. All
sources were read on 2026-10-07 and are paraphrased.

## 1. The companion apps (Android and iOS)

| Area | What HA does | Source |
|---|---|---|
| **Sensors** | Phone state (battery, connectivity, storage, activity, media, Health Connect on Android) sent to HA as entities. **Mostly off by default**: Android enables only battery and charger sensors plus those whose permission was granted at setup; iOS since 2025.5 asks users to enable sensors. Android updates every 15 min, or every minute while charging or always by choice | [Sensors](https://companion.home-assistant.io/docs/core/sensors) |
| **Notifications** | Push with **actionable** buttons that fire an event back into HA, text-input replies, URI actions. Android allows **3 actions**, iOS **about 10** | [Actionable](https://companion.home-assistant.io/docs/notifications/actionable-notifications) |
| **Critical alerts** | iOS critical alerts sit at the top of the lock screen and sound through Do Not Disturb; Android has no equivalent, so HA uses high priority, `ttl: 0` and the alarm audio stream. The docs say critical alerts are the only kind shown on CarPlay | [Critical](https://companion.home-assistant.io/docs/notifications/critical-notifications) |
| **Location** | Geofences on HA zones (iOS automatic, Android opt-in, 100 zones max); iOS significant-change updates (about 500 m or 15 min); Android fused location every 1–3 min, a high-accuracy GPS mode that can be limited to a Bluetooth connection or a zone. **Per-server choice: Exact, Zone name only, or Never** | [Location](https://companion.home-assistant.io/docs/core/location) |
| **Local vs remote** | An internal URL on the home Wi-Fi SSID, an external URL or Nabu Casa elsewhere. Reading the SSID needs "always" location permission. Setup asks how strict to be about unencrypted URLs ("Most secure" uses the internal URL only on the named SSID) | [Networking](https://companion.home-assistant.io/docs/troubleshooting/networking), [Getting started](https://companion.home-assistant.io/docs/getting_started/) |
| **Onboarding** | Local network discovery lists servers; else manual address. Login with HA's own accounts, name the device, location consent, then notifications (and critical alerts on iOS). More servers can be added later | [Getting started](https://companion.home-assistant.io/docs/getting_started/) |
| **Widgets** | Android: action button, entity state, media, picture, template text, to-do. iOS widgets and Control Center controls; 2026.2 lets a dashboard entity be added straight to the watch, CarPlay or a widget | [Android widgets](https://companion.home-assistant.io/docs/integrations/android-widgets), [Notebookcheck](https://www.notebookcheck.net/Home-Assistant-app-update-brings-more-than-ten-new-features-and-improvements.1223484.0.html) |
| **Watch** | Wear OS works standalone over the watch's own Wi-Fi or cellular after phone setup: favourites, five tile types (shortcuts up to 7, template, camera, voice, thermostat), complications refreshed about every 15 min | [Wear OS](https://companion.home-assistant.io/docs/wear-os/) |

**Pattern.** The app is a client for the user's own server with a fixed set of native features
(sensors, location, push, widgets, car, watch); it never hosts third-party code. That is the
precedent Ostler's app-model §7.1 already leans on for the stores.

## 2. HA in the car: Android Auto, AAOS and CarPlay

- **Android Auto and Android Automotive OS.** One car app in the companion app. While driving it
  shows **favourite entities** in a grid, controls a short list of domains (alarm panel without a
  code, button, cover, fan, input boolean and button, light, lock, scene, script, switch), shows
  binary sensors and sensors as values, and **navigates to any zone, person or tracker** with a
  location. Favourites are set only while parked (on the phone for Android Auto, in the car for
  AAOS); since 2025.12 any entity can be made an automotive favourite from its info dialog. How
  many entities show is the car's limit. Notifications marked `car_ui: true` appear on the car
  screen. ([Android Auto docs](https://companion.home-assistant.io/docs/android-auto/),
  [launch post 2023](https://www.home-assistant.io/blog/2023/01/20/android-auto/).)
- **The car reports back.** Through the Android Car API the app exposes the car as sensors in
  HA: fuel level and type, EV battery and connector, odometer, speed, car name, connection
  status. Availability depends on the maker; users report many reading empty on Android Auto
  ([docs](https://companion.home-assistant.io/docs/android-auto/),
  [forum thread](https://community.home-assistant.io/t/car-sensors/733925)).
- **CarPlay** (iOS app 2024.1 onward): no content until configured on the phone; four tabs:
  **Quick Access** (chosen entities and voice prompts), **Areas**, **Control** (by domain) and
  **Servers**; controllable domains are button, cover, input boolean and button, light, lock,
  scene, script, switch. 2026.1 and 2026.2 refined it
  ([CarPlay docs](https://companion.home-assistant.io/docs/carplay/),
  [2024.1 post](https://home-assistant.io/blog/2024/01/29/companion-app-for-ios-20241-carplay)).
- **Gaps people fill themselves:** an unofficial AAOS app and dashboard-in-car requests on the
  forum ([HA Automotive thread](https://community.home-assistant.io/t/ha-automotive-unofficial-app-for-android-automotive-os/1020221)).

**What it means for Ostler.** HA in the car is a **remote control for the house**: lists,
toggles and a route to a zone, never a dashboard of live values. That is exactly the shape
ADR-0042 decision 2 allows Ostler (an `alert_card`, a `short_list` of values, trip status; no live
gauges on CarPlay). Two differences: Ostler's car screen is about the car itself, so remote
actions stay read-only or alerts (ADR-0033); and HA's Car API sensors show a phone app can read
basic car data (odometer, fuel, EV state) **without any Ostler hardware** on AAOS and some
Android Auto cars.

## 3. Nabu Casa and Home Assistant Link

- **What it sells.** Remote access, online backups, Alexa and Google voice, cloud speech-to-text
  and text-to-speech, media streaming and support: **USD 6.50 a month or 65 a year**, 31-day
  trial without a card ([pricing](https://www.nabucasa.com/pricing/)).
- **How remote access works.** SniTun, an end-to-end encrypted SNI proxy over a TCP multiplexer,
  so TLS ends on the user's own box; both SniTun and the HA client library `hass-nabucasa` are
  **GPL-3.0**, while the service itself is Nabu Casa's
  ([SniTun](https://github.com/NabuCasa/snitun), [hass-nabucasa](https://github.com/NabuCasa/hass-nabucasa)).
- **Renamed "Home Assistant Link"** in the 2026.12 release (announced 2026-10-02): new users
  thought "Cloud" meant HA ran in the cloud; the service stays optional, price and features
  unchanged, and Nabu Casa gives most of its subscription profit to the foundation
  ([blog](https://home-assistant.io/blog/2026/10/02/big-tech-ruined-the-cloud-so-were-renaming-ours/)).
- **It funds the project.** Started in 2018 to pay for development; no outside investors
  ([OHF newsletter](https://newsletter.openhomefoundation.org/investing-in-open-home/)).

## 4. Governance: the Open Home Foundation

- **Form.** Announced April 2024; a tax-exempt Swiss **Stiftung** that owns the code and the
  brand of Home Assistant, ESPHome, Improv, Music Assistant, HACS and 250+ projects, so no
  company can buy them ([organisation](https://www.openhomefoundation.org/organization),
  [CNX Software](https://www.cnx-software.com/2024/04/23/open-home-foundation-manage-home-assistant-esphome-zigpy-over-240-open-source-smart-home-projects/)).
- **Partner model.** Commercial partners (Nabu Casa, Apollo Automation) licence the names and
  logos and are **contractually bound to give a majority of their profit** from those products;
  money flows one way, partners to foundation; a partner sits on the board as a rotating member.
- **Numbers (annual report 2025, published June 2026).** Revenue CHF 8.84 m; over 60 % (CHF 5.58 m)
  paid 52 salaried staff; about **2.28 m homes**, estimated from opt-in analytics with a 4×
  multiplier; donations formalised into tiers (DuckDuckGo USD 50k, Espressif USD 25k)
  ([annual report](https://www.openhomefoundation.org/assets/documents/annual-report-2025-11-jun-2026.pdf)).
- **Principles** used as gates everywhere: privacy (local first, cloud optional), choice (open
  standards, local APIs), sustainability (durable, repairable)
  ([OHF](https://www.openhomefoundation.org/)).

## 5. Community structures

| Structure | How HA runs it | Source |
|---|---|---|
| **Forum** | Discourse at community.home-assistant.io, open to anyone; Discord for chat and the beta channel | [forum](https://community.home-assistant.io/categories) |
| **Docs** | Three public sites: user docs, developer docs, companion-app docs, all edited by PR on GitHub | [developers](https://developers.home-assistant.io/docs/development_index) |
| **Release cadence** | A release on the **first Wednesday** of each month, beta from the last Wednesday before it, then patch releases (often 3–4 a month); each release has a long blog post | [release FAQ](https://home-assistant.io/faq/release) |
| **"What the Heck?!"** | A forum category open for a month (2019, 2020, 2022, 2024 editions) where anyone posts annoyances and small requests without a GitHub issue; others vote; developers fix many in the following releases | [WTH 2024](https://home-assistant.io/blog/2024/11/30/the-month-of-what-the-heck) |
| **Apps (was add-ons)** | Containers beside HA; **renamed "Apps" in 2026.2** because "Add-ons" and "Integrations" confused newcomers. Community app repos (e.g. `hassio-addons`) are added by URL | [rename](https://frenck.dev/renaming-home-assistant-add-ons-to-apps/), [2026.2](https://www.home-assistant.io/blog/2026/02/04/release-20262/) |
| **HACS** | A community store for custom integrations, cards and themes from public GitHub repos; joined the foundation in 2025. Default-list inclusion checks structure and releases, **not code or security** | [HACS include](https://hacs.xyz/docs/publish/include/), [OHF year one](https://newsletter.openhomefoundation.org/big-first-year-bigger-second/) |
| **Analytics** | **Opt-in**, four levels (basic install count and version; usage, i.e. integration names; counts; crash reports); only aggregates published on a public dashboard; raw kept ≤ 60 days | [analytics](https://www.home-assistant.io/integrations/analytics/) |
| **Events and surveys** | Annual "State of the Open Home"; 40+ Community Day meetups (2025); a community survey with 8,600 answers; a Device Database project pooling device knowledge | [OHF year one](https://newsletter.openhomefoundation.org/big-first-year-bigger-second/), [State of the Open Home 2025](https://home-assistant.io/blog/2025/04/16/state-of-the-open-home-recap/) |

## 6. Works With Home Assistant

- **Run by the foundation** since 2025 (Nabu Casa ran it before); **CHF 500 a year**; 7 → 19
  partners in 2025 (Aqara, Eve, Reolink, Nuki among them).
- **Criteria:** local control, any cloud optional and opt-in; OTA updates through HA or a notice
  of updates; a shipping product (no pre-orders); Zigbee, Matter or Z-Wave certification where
  relevant; FCC/CE; the HA integration at **gold** on the quality scale or better; shared values.
- **Scope: end devices only**; hubs, bridges, repeaters and radio adapters are not certified.
  ([WWHA](https://works-with.home-assistant.io/), [annual report](https://www.openhomefoundation.org/assets/documents/annual-report-2025-11-jun-2026.pdf).)

## 7. Hardware

- **Home Assistant Green**, the plug-in box (about £112 or USD 165 at retail); **Connect ZBT-2**
  (Zigbee/Thread, about £38) and **ZWA-2** (Z-Wave, about £51); **Voice Preview Edition**
  (about £56) ([The Pi Hut](https://thepihut.com/products/home-assistant-connect-zbt-2),
  [ZWA-2](https://thepihut.com/products/home-assistant-connect-zwa-2),
  [Ameridroid](https://ameridroid.com/collections/all-products-ha-green)).
- **Yellow ended production on 2025-10-15**: Compute Module 4 supply and price, and falling sales;
  software support continues as long as HA runs on it
  ([blog](https://www.home-assistant.io/blog/2025/10/15/yellow-end-of-life/)).
- The hardware is sold by commercial partners under licence; profit goes to the foundation (§4).

## 8. Mapping to Ostler

**Companion app scope.** HA's list is a good checklist for Ostler's native features. Ostler
already has pairing, push and location fixed in the binary. Worth adding to the same fixed set:
phone sensors off by default (fits ghost), a per-server location choice like HA's three levels
(Ostler: exact, privacy-zone name only, never), actionable notifications that come back as events
through the gate's read/alert path, iOS critical alerts and Android alarm-stream alerts for the
alarm and Crash SOS (Apple grants the critical-alert entitlement by request; not rechecked here),
widgets (trip status, last alert, fuel/charge), a watch tile later. Home-SSID URL switching maps to
"on the car's Wi-Fi, talk to the Brain or node locally; elsewhere, Tailscale or Ostler Cloud".

**Car display support.** HA's car app is a favourites list plus navigation to places; it shows
that a store-approved car app from a home-automation project can live in tight templates. Ostler's
companions (ADR-0042 decision 2) match: alerts, a `short_list`, trip status, "navigate to my car"
(a zone-like target). Two Ostler-specific rules stay: no remote car actions beyond ADR-0033, and
no live gauges on CarPlay. New idea from HA: a **phone-only Car API source** (AAOS first) feeding
odometer, fuel and EV state into Trips and Maintenance for cars with no node.

**Ostler Cloud like Nabu Casa.** ADR-0028 already copies the SniTun model and "never the only
option". HA adds three lessons: one subscription bundles several conveniences (remote access,
backups, voice, push relay) at about a coffee a month; the client side is open while the service
is not; and the name matters (HA dropped "Cloud" so nobody thinks the product runs remotely).
Ostler Cloud's paid bundle could be remote access + parked MQTT bridge + push relay + off-car
backup of Trips + extra hub storage.

**Governance.** HA's trust rests on a foundation owning the code and brand, with the company
bound to fund it. Ostler today is a company-held AGPL + commercial dual licence with a CLA
(ADR-0012) and two closed services; the CLA is the lever a foundation would remove. A foundation
is a later question; a public written promise (exit guarantee, 90-day shutdown, export) is the
cheap step now and already exists in ADR-0042 and the hub spec.

**Release cadence.** A monthly platform release with a week's beta suits a small team and gives a
steady blog post. Packs release on their own (pack contract); the store app follows the platform
but only for native changes; the hub ships continuously.

**"Works with Ostler."** HA certifies end devices only; Ostler's value is in **adapters, head
units and sensor modules**, so its programme would cover exactly what HA excludes. Draft criteria:
works fully offline; reads through the node gate or a documented local protocol; listen-only on
CAN by default; OTA or a published update path; a tested profile in the pack or adapter list
([third-party adapters](third_party_adapters.md)); no VIN leaves the device. Tiers by device class:
OBD adapters (ELM/STN/WiCAN), Android head units, T1S or Wi-Fi modules.

**Hardware line.** Ostler Diagnostics (node), Guardian (variant) and Brain
([product family](product_family.md)) map to HA's Connect sticks (radio and bus access) and Green
(the server). Yellow's end is a warning for a Pi-based Brain: plan a second compute module and
promise software support after any board ends.

**Community vs the closed hub.** HA's community is open by default: Discourse, docs by PR, HACS
and app repos anyone can add, voting in WTH. Ostler's hub is closed, single-operator, with no
votes, and the forum is built in (hub spec B 7, 13, 19a). The parts of HA's model that still fit:
docs on GitHub by PR; contributions straight to pack repos (already a hard line); a yearly WTH-like
month (as a forum category without votes, or with "me too" counts); community meetups; a public
analytics dashboard if Ostler adds opt-in analytics (the hub spec says no analytics; that is the
hub site, not device counts). HA's Device Database is the same idea as the hub's generated
vehicle wiki pages.

**Naming.** HA left "add-ons" because users mixed it up with integrations. Ostler's "Add-ons"
mean features (apps in the app model), integrations and developer tools in one list; the same
confusion may follow once the catalogue grows.

## 9. Copy / Avoid / Decide for Ostler

**Copy**

- Phone sensors and data **off by default**, enabled per sensor; a per-server location level
  (exact / zone name only / never).
- Actionable notifications with a small fixed action count (3 fits Android); critical alerts on
  iOS and the alarm stream on Android for the alarm and Crash SOS only.
- In the car: favourites set only when parked, a short list, navigate to a place; nothing more.
- The cloud model: optional, end-to-end, open client, one modest subscription that funds the
  project, never required (ADR-0028 §6).
- Monthly releases with a one-week beta and a release blog post; patch releases as needed.
- A once-a-year "What the Heck?!" month for small annoyances, without a GitHub account.
- Opt-in anonymous install counts with only aggregates public.
- A certification badge with written, testable criteria and a small fee.
- A software-support promise that outlives each hardware board.

**Avoid**

- Calling the paid relay "Cloud" if users will read it as "Ostler runs in the cloud".
- A community store with no code review (HACS); Ostler's app model already forbids runtime code
  on the phone, and any web-host store needs signing (app-model §7, its ADR).
- Hardware built on one supply-constrained module with no second source (Yellow).
- Showing live car values on CarPlay, or remote car actions from any car screen.
- A forum that only staff can steer with no route for small requests.

**Decide**

1. **Ostler Cloud's name.** Keep "Ostler Cloud", or follow HA to a name that says "link" or
   "remote" (e.g. "Ostler Link"), before anything ships under the old name.
2. **Ostler Cloud's bundle and price.** Recommend one plan, priced near HA's (about USD 6.50 a
   month): remote access, parked MQTT bridge, push relay, Trips backup and extra hub storage;
   alternative: separate add-on prices per service.
3. **A foundation.** Recommend writing down now that the code, packs and brand move to a
   non-profit foundation once there is revenue to fund it, with partners bound to give it most of
   their profit; alternative: stay company-held with the CLA and the published exit promises.
4. **"Works with Ostler".** Recommend a programme for OBD adapters, head units and modules with
   the draft criteria in §8, after the node gate and the adapter list are stable; alternative:
   a tested-adapter list only, no badge.
5. **Phone-only Car API source.** Recommend specifying an AAOS (and later Android Auto) source
   that reads odometer, fuel and EV state into Trips and Maintenance for cars with no node;
   alternative: car data only from Ostler hardware.
6. **Release cadence.** Recommend a monthly platform release (first Wednesday, one-week beta);
   alternative: release when ready.
7. **Opt-in analytics.** Recommend opt-in, levelled, aggregate-only install analytics with a
   public dashboard, off by default and never with location or VIN; alternative: no analytics,
   size counted from store installs and hub accounts.
8. **WTH month and votes.** Recommend a yearly feedback month in the hub forum with "me too"
   counts shown only on that category; alternative: keep the hub's no-votes rule everywhere.
9. **The word "Add-ons".** Recommend keeping it for now and revisiting once integrations and
   feature add-ons outgrow one list (HA's 2026.2 rename is the warning); alternative: split now
   into "Apps" and "Integrations".
10. **Critical alerts.** Recommend applying for Apple's critical-alert entitlement for the alarm
    and Crash SOS only; alternative: ordinary time-sensitive notifications.

## Sources (all read 2026-10-07)

Companion: [sensors](https://companion.home-assistant.io/docs/core/sensors) ·
[actionable notifications](https://companion.home-assistant.io/docs/notifications/actionable-notifications) ·
[critical notifications](https://companion.home-assistant.io/docs/notifications/critical-notifications) ·
[location](https://companion.home-assistant.io/docs/core/location) ·
[networking](https://companion.home-assistant.io/docs/troubleshooting/networking) ·
[getting started](https://companion.home-assistant.io/docs/getting_started/) ·
[Android widgets](https://companion.home-assistant.io/docs/integrations/android-widgets) ·
[Wear OS](https://companion.home-assistant.io/docs/wear-os/) ·
[Android Auto](https://companion.home-assistant.io/docs/android-auto/) ·
[CarPlay](https://companion.home-assistant.io/docs/carplay/).
Cloud and foundation: [Nabu Casa pricing](https://www.nabucasa.com/pricing/) ·
[Link rename](https://home-assistant.io/blog/2026/10/02/big-tech-ruined-the-cloud-so-were-renaming-ours/) ·
[SniTun](https://github.com/NabuCasa/snitun) · [OHF organisation](https://www.openhomefoundation.org/organization) ·
[OHF annual report 2025](https://www.openhomefoundation.org/assets/documents/annual-report-2025-11-jun-2026.pdf).
Community and hardware: [release FAQ](https://home-assistant.io/faq/release) ·
[WTH 2024](https://home-assistant.io/blog/2024/11/30/the-month-of-what-the-heck) ·
[apps rename](https://frenck.dev/renaming-home-assistant-add-ons-to-apps/) ·
[HACS](https://hacs.xyz/docs/publish/include/) · [analytics](https://www.home-assistant.io/integrations/analytics/) ·
[WWHA](https://works-with.home-assistant.io/) ·
[Yellow end of life](https://www.home-assistant.io/blog/2025/10/15/yellow-end-of-life/).
