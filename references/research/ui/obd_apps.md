---
title: "Consumer OBD-II and dealer-level phone apps — UI patterns for a vehicle-agnostic Ostler"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/landscape.md]
summary: >
  How ten phone and desktop diagnostic apps (Torque Pro, Car Scanner, OBD Fusion, OBDeleven, Carista, BimmerCode/Link, FORScan, Infocar, RealDash, plus OVMS/HA layouts) handle connection, garages, dashboards, DTCs, readiness, custom PIDs, module lists, navigation and paywalls; what users praise and hate; and the patterns Ostler should adopt to treat a one-ECU OBD-II car and a six-ECU D2 the same way.
---

# Consumer OBD-II and dealer-level phone apps (October 2026)

## How this was made, and how to read it

- **Sources:** one research pass on 2026-10-05, using app-store listings, vendor sites, independent reviews, Trustpilot and owner forums. Reddit threads could not be fetched directly, so forum and review-site posts stand in for "what users say". Each claim carries its link. Store listings are the vendors' own words, so treat feature claims as marketing until they are tested.
- **Licences:** every app here is closed-source and proprietary unless the text says otherwise. We can learn from their UI, but we take no code or data from them. Reusable open material is listed under [Reuse and licences](#reuse-and-licences).
- **Ostler context:** the current UI has eight tabs (Drive, Faults, Inputs, Outputs, Settings, Utilities, Logs, Analysis) and a header module selector (`ui/src/screens/registry.ts`). The platform spec proposes a five-destination IA (`specs/2026-10-06-platform-direction-design.md`).

## At a glance

| App | Scope | Module model | Garage | Pricing model |
|---|---|---|---|---|
| Torque Pro | Generic OBD-II, Android only | Engine ECU only; plugins add makes | Vehicle profiles | ~$5 one-off |
| Car Scanner | Generic + per-make "connection profiles" | Engine only, or all ECUs if the profile supports the make | Per-vehicle settings | Free with ads; Pro $4–8 |
| OBD Fusion | Generic + paid per-make "enhanced" packs | Engine only; ABS/SRS/TCM via add-on | Vehicle editor | ~$10 + per-make IAPs |
| OBDeleven | Dealer-level for licensed makes | Full control-unit list | Garage | Credits + PRO/ULTIMATE |
| Carista | Diagnose / Customise / Service | All modules (paid) | Not documented | Subscription |
| BimmerLink / BimmerCode | BMW, MINI, Supra | All control units | Not documented | One-off unlocks |
| FORScan | Ford/Mazda dealer-level | Network scan, module list | Saved vehicle profiles | Free; extended licence for config |
| Infocar | Generic + maker data, driving scores | Results grouped by ECU | Not documented | Subscriptions + "forever" |
| RealDash | Dashboard engine, many ECUs | Whatever the XML defines | Multiple vehicle profiles | Free; subscription and paid themes |
| OVMS Connect | EV telematics over MQTT | n/a (one vehicle, many metrics) | Multiple vehicles | $3.99 |

## Per app

### Torque Pro (Android)

- **Connection:** pairs with a Bluetooth ELM327 such as a Veepeak, for about $25 in all ([iamcarhacker](https://iamcarhacker.com/torque-pro-app/)). Protocol detection is the ELM327's own automatic search, `AT SP 0`, checked with `AT DP` ([ELM327 datasheet](https://cdn.sparkfun.com/assets/learn_tutorials/8/3/datasheet.pdf)).
- **Vehicle profiles:** each profile holds engine displacement, weight, fuel type, boost adjustment and volumetric efficiency, and the app uses them to calculate derived values such as MPG and power ([audizine](https://audizine.com/threads/torque-software-settings.457217/)). You can switch between profiles ([datamyte](https://blog.datamyte.com/torque-app)).
- **Dashboards:** several pre-built dashboards, with gauges you can move and resize, and a HUD mode ([datamyte](https://blog.datamyte.com/torque-app)). Dials, themes and scripting are documented on the [wiki](https://wiki.torque-bhp.com/view/Main_Page).
- **Custom PIDs:** a CSV with the columns `Name, ShortName, ModeAndPID, Equation, Min Value, Max Value, Units, Header`. The `Header` column targets a specific ECU, and owner forums trade these files ([audizine](https://audizine.com/threads/torque-non-standard-pids.920460/), [F150 Lightning forum](https://www.f150lightningforum.com/forum/threads/f150-lightning-torque-app-and-pid-list.28216/post-526407)).
- **Plugins:** per-make "Advanced EX" plugins (Toyota, Nissan, Hyundai/Kia, Renault and others) add engine and automatic-gearbox data. Other plugins add charts, knock detection, racing dashboards and track video, and are distributed through Google Play ([wiki: Plugins](https://wiki.torque-bhp.com/view/Plugins)).
- **Modules:** engine only. It cannot reach ABS or airbag systems ([iamcarhacker](https://iamcarhacker.com/torque-pro-app/)).
- **Users:** praise the price and the customisation. They complain that it is Android only, that the learning curve is steep, and that watching several values at once is "fiddly" ([iamcarhacker](https://iamcarhacker.com/torque-pro-app/), [carinterior roundup](https://carinterior.alibaba.com/question/best-obd2-scanner-app-guide)). The last update was in February 2025 ([apppricinglab](https://apppricinglab.com/app/google_play/org.prowl.torque)).

### Car Scanner ELM OBD2 (iOS, Android)

- **Connection:** setup pages cover Wi-Fi, Android Bluetooth and iOS BLE adapters ([carscanner.info](https://www.carscanner.info/)). The key step is choosing a **connection profile** per make. Generic OBD reaches the engine only; the right profile unlocks ABS, airbag and other modules, and the wrong one limits you to the engine ([iamcarhacker guide, via search](https://iamcarhacker.com/obd2-scanner/tool-guides/how-to-use-car-scanner-elm-obd2-app/), [iamcarhacker review](https://iamcarhacker.com/?p=3970)). One reviewer suggests users screenshot the profile list and ask a chatbot which to choose, which says a lot about how discoverable the step is ([iamcarhacker review](https://iamcarhacker.com/?p=3970)).
- **Features:** a dashboard builder, extended PIDs, DTCs with freeze frame, Mode 06, emissions readiness, HUD, 0–60 timing, a trip computer, and CSV recording with graphs ([App Store](https://apps.apple.com/app/id1259933623)). Logs replay with the map and graphs synced ([iamcarhacker review](https://iamcarhacker.com/?p=3970)).
- **Garage:** "remembers settings for each vehicle" ([App Store](https://apps.apple.com/app/id1259933623)).
- **Coding:** experimental, on VAG MQB/PQ26/MLB-Evo and some Toyota ([carscanner.info/coding](https://www.carscanner.info/), [iamcarhacker review](https://iamcarhacker.com/?p=3970)).
- **Paid gating:** the free version has ads and allows two live graphs at once. Pro costs $3.99 for a month or $7.99 for life ([App Store](https://apps.apple.com/app/id1259933623), [iamcarhacker review](https://iamcarhacker.com/?p=3970)).
- **Users:** praise the free feature set and the "user friendly GUI display builder". They complain the UI is "a little clunky" and want several parameters on one gauge ([App Store](https://apps.apple.com/app/id1259933623), [carinterior roundup](https://carinterior.alibaba.com/question/best-obd2-scanner-app-guide)).

### OBD Fusion (iOS, Android)

- **Features:** dashboards built from 250+ PIDs, with import and export; freeze frame; Mode 05/06/09; custom PIDs with equations, text states and IEEE-754 decoding; trip stats; and CarPlay without live gauges ([App Store IL](https://apps.apple.com/il/app/id650684932), [App Store JO](https://apps.apple.com/jo/app/id650684932)).
- **Readiness:** "Emissions readiness for each US state" answers the question "will I pass?" rather than showing a raw monitor list ([App Store JO](https://apps.apple.com/jo/app/id650684932)).
- **Vehicles:** a vehicle editor shows what your vehicle supports, and the app has a connection wizard ([App Store JO](https://apps.apple.com/jo/app/id650684932)).
- **Paid gating:** the base app is about $10. ABS, SRS and transmission data are **per-make, per-model-year in-app purchases**, for example "Ford 2024–2026" ([App Store IL](https://apps.apple.com/il/app/id650684932)).
- **Users:** praise the clean interface and DTC explanations ([carinterior roundup](https://carinterior.alibaba.com/question/best-obd2-scanner-app-guide)). They complain of paying and then finding their make unsupported (a Fiat owner) ([App Store IL](https://apps.apple.com/il/app/id650684932)), and that paywalls stacked on a paid app erode trust ([gridinsoft review](https://support-antimalware.gridinsoft.com/?p=1476)).

### OBDeleven (iOS, Android, own dongle)

- **Connection:** the app works with its own Bluetooth dongle; the free tier also takes an ELM327 for basic OBD-II ([App Store](https://apps.apple.com/us/app/-/id1643119107)).
- **Garage:** lists connected vehicles with their VIN data, model and year ([App Store](https://apps.apple.com/us/app/-/id1643119107), [ECS](https://www.ecstuning.com/b-obdeleven-parts/obdeleven-pro-pack-next-generation/024871obd02~obd/)).
- **Module list:** a full scan lists every control unit with green or red status, and each fault has a search shortcut ([iamcarhacker](https://iamcarhacker.com/?p=575)). Officially licensed makes (VW Group, BMW Group, Toyota, Ford US, Mercedes) get the full scan; other makes get engine and transmission only ([App Store](https://apps.apple.com/us/app/-/id1643119107)). Inside a control unit you find info, sub-units, live data, charts, coding and reset ([Turner](https://www.turnermotorsport.com/BMW-G80/m-1310-obdeleven)). A full scan takes about two minutes on the new hardware ([iamcarhacker 3 vs 2](https://iamcarhacker.com/?p=42496)), and 30–50-module cars take longer ([iamcarhacker](https://iamcarhacker.com/?p=575)).
- **Safety:** coding history logs every value change so it can be reverted, and backups appear in a History tab ([iamcarhacker](https://iamcarhacker.com/?p=575), [search summary of iamcarhacker guide](https://iamcarhacker.com/?p=43272)).
- **Paid gating:** three layers. **Credits** pay for each "One-Click App" (700+ recipes), **PRO** adds manual coding, and **ULTIMATE** gives unlimited apps. Prices run from $69.99 to $239.99 ([App Store](https://apps.apple.com/us/app/-/id1643119107)). Output tests are free ([iamcarhacker](https://iamcarhacker.com/?p=575)).
- **Users:** praise the speed, VAG depth and support ([Trustpilot](https://uk.trustpilot.com/review/obdeleven.com?page=7)). They complain that credits "burn money fast", are sometimes charged for features the car cannot support, and that free ad-earned credits were removed ([iamcarhacker](https://iamcarhacker.com/?p=575), [Trustpilot CA](https://ca.trustpilot.com/review/obdeleven.com?page=7)). Vehicle identification is slow ([App Store](https://apps.apple.com/us/app/-/id1643119107)).

### Carista (iOS, Android, own dongle or any ELM327)

- **Flow:** plug in, then auto-pair. The app checks its servers to identify the car, then shows three sections: **Diagnose**, **Service** and **Customize** ([carwitter](https://carwitter.com/carista-bluetooth-obd2-review/)). Customisation is presented as categories of toggles for the exact car ([iamcarhacker](https://www.iamcarhacker.com/?p=820)).
- **Paid gating:** basic OBD codes and check-engine reset are free. All-module diagnosis, service resets and coding need a subscription of about £34 a year ([pocketables via search](https://pocketables.com/?p=108742), [carwitter](https://carwitter.com/carista-bluetooth-obd2-review/)). Coded changes stay after you cancel ([iamcarhacker](https://www.iamcarhacker.com/?p=820)).
- **Users:** call it the "easiest, cleanest way to customize". They complain that diagnostics and live data are shallow, with no graphing, and about the subscription ([iamcarhacker](https://www.iamcarhacker.com/?p=820)). Its Trustpilot score is 2/5 ([Trustpilot](https://ca.trustpilot.com/review/caristaapp.com)).
- **Ostler takeaway:** the identify-the-car-via-server step is a cloud dependency, which conflicts with our local-first principle.

### BimmerLink and BimmerCode (BMW, MINI, Supra)

- **The family is split by risk:** BimmerLink does diagnostics and live data; BimmerCode does coding. They are separate apps with separate purchases ([App Store](https://apps.apple.com/gb/app/id1065360416), [bimmercode.app](https://bimmercode.app/)).
- **BimmerLink:** reads and clears DTCs from **all** control units, has a personalised dashboard, and offers service functions: battery registration, DPF status, EPB service mode, and exhaust-flap and active-sound control. The full unlock is £39.99, plus £9.99 for CarPlay ([App Store](https://apps.apple.com/gb/app/id1065360416)).
- **BimmerCode:** shows a control-unit overview (FEM, HU, KOMBI) and you drill into options ([bimmercode.app](https://bimmercode.app/)). It backs up each module automatically before every write, and the oldest backup restores stock ([supramkv](https://www.supramkv.com/threads/need-some-help-with-bimmercode-problems.15263/latest)).
- **Users:** praise the one-off price over subscriptions. They complain there is no search or filter when picking sensors and no guidance on what a fault means ([App Store](https://apps.apple.com/gb/app/id1065360416)).

### FORScan (Windows; Lite on iOS and Android)

- **Connection:** press Connect, and the app finds the adapter, reads the VIN and module part numbers, then unlocks the main menu. After the first module scan it offers to **save a vehicle profile**. All functions sit in a left-hand main menu ([bronco6g forum](https://www.bronco6g.com/forum/threads/forscan.133574/), [FG Falcon wiki](https://github.com/jakka351/FG-Falcon/wiki/The-Ultimate-Guide-to-Coding-FG-Module-VIN-numbers-with-Forscan)).
- **Organisation:** module-first. Each module (PCM, ABS, TCM, BCM…) offers live data, self-tests and configuration where supported ([obdadvisor via search](https://obdadvisor.com/forscan-review/)). The features are: network configuration detection, DTCs from all modules, PIDs from all modules, tests, service procedures, and configuration and programming ([forscan.org](https://forscan.org/home.html)).
- **Paid gating:** Lite costs $6.99 on iOS and leaves out configuration, programming and some service functions ([App Store](https://apps.apple.com/app/id892347083)). On Windows these need the **Extended License**, which has a free, endlessly renewable two-month trial ([obdadvisor via search](https://obdadvisor.com/forscan-review/)).
- **Users:** praise it as "NOT a lite app" ([App Store](https://apps.apple.com/app/id892347083)). The pain points are as-built hex editing and the need for backups before each session ([F150 Lightning forum](https://www.f150lightningforum.com/forum/threads/f150-lightning-forscan-thread.11406/post-421815)), and cheap ELM327s, which the authors no longer recommend ([forscan.org](https://forscan.org/home.html)).

### Infocar (iOS, Android)

- **Features:** faults with **three severity levels**, results grouped by ECU, 800+ generic and 2,000+ maker sensors, a dashboard and HUD, safe/eco **driving scores**, drive replay by time and place, maintenance and expense tracking, and Excel export ([App Store](https://apps.apple.com/us/app/-/id1447599519)).
- **Paid gating:** Pro is $3.99–8.99, "Manufacturer Data Plus" is $12.99–34.99, and a "Forever" plan is $23.99 ([App Store](https://apps.apple.com/us/app/-/id1447599519)). The app has 8.5 million downloads and leads its home market of Korea ([dealroom via search](https://app.dealroom.co/companies/infocar)).
- **Users:** the main complaint is that you must open the app and wait for it to connect; there is no auto-connect ([App Store](https://apps.apple.com/us/app/-/id1447599519)).

### RealDash (Android, iOS, Windows)

- **Scope:** a dashboard engine rather than a scan tool. It connects to OBD-II through an ELM327 and to aftermarket ECUs (Megasquirt, Consult, EMU) and racing games. It offers "Pixel Perfect" editing, a gallery of free and paid themes ($1.99–5.99), a trigger-to-action system for alarms and effects, and **multiple vehicle profiles with per-vehicle warning and critical levels**. The "My RealDash" subscription costs €24 a year ([App Store](https://apps.apple.com/us/app/-/id1088758424)).
- **Data definitions:** OBD-II XML files have an `init` list and a `rotation` list of commands, with attributes `send`, `header`, `ecu`, `conversion`, `units`, `enum`, `skipCount` and multi-value `<values>`. These are **public domain (Unlicense)** in [RealDash-extras](https://github.com/janimm/RealDash-extras/tree/master/OBD2), and include Opel KWP2000 and Fiat pre-CAN examples.
- **Users:** call it "criminally underrated", and complain of crashes and slow support ([App Store](https://apps.apple.com/us/app/-/id1088758424)).

### OVMS Connect and Home Assistant (briefly; OVMS is covered in depth elsewhere)

- **OVMS Connect:** the screens are Dashboard (SoC, range, odometer, power), an **interactive top-down vehicle view** (doors, boot, lights, TPMS per tyre), a live map with trail, telemetry sub-screens (HV, 12 V, charging, trip, network, system, vehicle-specific), a command terminal, commands **pinned to the dashboard**, and home widgets. It supports multiple vehicles, any MQTT broker, and credentials stored only on the device ([App Store](https://apps.apple.com/app/id6747955064)).
- **Home Assistant:** builds a default dashboard "automatically generated from the devices you add" ([HA dashboards](https://www.home-assistant.io/dashboards/)). Entities are categorised: primary entities have no category, `config` entities change settings, and `diagnostic` entities are read-only device health ([HA entity docs](https://developers.home-assistant.io/docs/core/entity/)). This is the same three-way split we need between signals, settings and module health.

## Cross-cutting patterns

| Dimension | What the apps do |
|---|---|
| Connection | All wrap the ELM327 auto-search ([datasheet](https://cdn.sparkfun.com/assets/learn_tutorials/8/3/datasheet.pdf)). The best then identify the car (VIN, module scan) and **persist a profile** (FORScan, OBDeleven); the weakest make the user pick from a long profile list (Car Scanner). Users expect auto-connect (Infocar complaints), and FORScan surfaces adapter quality. |
| Garage | OBDeleven, OBD Fusion, RealDash, OVMS Connect and FORScan keep a vehicle list holding identity (VIN, model, year), derived-value constants (Torque), warning levels (RealDash), dashboards, and history (scans, backups, coding log). |
| Dashboards | Universal: a grid of gauges, graphs and text bound to signals, with thresholds and alarms; import/export (OBD Fusion), shareable themes (RealDash), HUD. Complaints: one value per gauge (Car Scanner, Torque), no sensor search (BimmerLink). |
| DTCs, freeze frame | All read and clear; most show freeze frame. Better: a search link per code (OBDeleven, Carista), severity (Infocar), plain-English text (OBD Fusion, BlueDriver ([carinterior](https://carinterior.alibaba.com/question/best-obd2-scanner-app-guide))). Dealer tools scan **all modules in one action**, show per-module status, then drill in. |
| Readiness | Generic-OBD only. OBD Fusion turns it into a yes/no per jurisdiction. Pre-OBD modules (the Td5) have no equivalent. |
| Custom PIDs | A power-user CSV/XML: Torque `ModeAndPID, Equation, Header`; RealDash `send, header, ecu, conversion`; OBD Fusion equations, enums, IEEE-754. The `Header`/`ecu` field is how a "single-ECU" app quietly reaches other modules. Forums trade the files. |
| Paid gating | One-off unlock (Torque, BimmerLink, Car Scanner Pro); per-make add-on (OBD Fusion); subscription (Carista, Infocar); credits per action (OBDeleven); tier by platform (FORScan Lite vs Windows). Credits and post-purchase paywalls draw the angriest reviews. |

**Navigation: three shapes recur.**
1. **Function-first** (Torque, Car Scanner, OBD Fusion, Infocar): a home grid of Dashboard, Faults, Live data, Readiness, Logs, Settings. It fits one ECU; modules are bolted on via profiles or add-ons.
2. **Vehicle → modules → functions** (OBDeleven, FORScan, BimmerCode): garage, full scan, module list, then a module page with data, codes, tests and coding.
3. **Task-first** (Carista Diagnose/Service/Customize; BimmerLink service functions; OBDeleven One-Click Apps): recipes that hide the modules.

## How apps reconcile "one-ECU OBD car" with "many control units"

1. **Generic first, modules as an upgrade:** OBD Fusion, Car Scanner and Torque model the car as one ECU. Extra modules arrive through a per-make profile, add-on or plugin, and appear as more ECU choices inside the same Faults and Live screens. The cost is that discoverability depends on choosing the right profile.
2. **Module list as the spine:** in OBDeleven, FORScan and BimmerCode, even a basic car is just a module list with one entry (OBDeleven's non-licensed makes see engine and transmission only). Full scan is the home action, and every function lives under a module.
3. **Cross-module aggregation on top:** OBDeleven and FORScan both run a full scan that gathers DTCs from every module into one list, then link each fault back to its module. Carista and BimmerLink go further and present tasks (battery registration, service reset) that hide which module they talk to.

**The consensus:** the data model is always *vehicle → modules (one or many) → signals,
DTCs, actions*. The UI offers two lenses on it:
- an **aggregate** lens (all faults, dashboard, tasks);
- a **per-module** lens (the module page).

A generic OBD-II car is simply a vehicle with one module (`engine`), or a few on CAN, where
mode 01 answers can come from any of the standard 7E8–7EF responders (engine, gearbox).

## Patterns Ostler should adopt

1. **Model "vehicle → modules" for every pack, even when there is only one module.** The OBD-II pack declares one module, `engine`, and the D2 declares six. Hide the header module selector when `len(modules) == 1`, rather than writing a separate UI.
2. **Make "Scan all" a first-class home action.** It lists modules with green, amber, red or grey status (grey for no response), like OBDeleven's coloured module list. Grey is honest about K-line modules that are asleep or absent.
3. **Offer two lenses, not two apps.** Faults and Dashboard are aggregate views across modules, with each row tagged by its module. A module page shows one module's signals, codes, settings, outputs and utilities. This maps our current tabs onto destinations inside a module page.
4. **Persist a garage profile from detection.** Use the VIN where the vehicle reports one, and otherwise the pack plus a user label (the D2 has no OBD VIN). Store per-vehicle dashboards, thresholds (as RealDash does) and constants (as Torque does).
5. **Use a connection wizard with remembered adapters,** plus auto-connect on launch, since users complain when it is missing. Show the adapter's class and quality as a hint, as FORScan does with its recommended-adapter list.
6. **Write safety into the flow.** Back up automatically before any write (BimmerCode), keep a coding and actuation history with one-tap revert (OBDeleven), and split by risk: read-only views are separate from actions behind our safety gate.
7. **Map readiness to an outcome.** For OBD-II packs, show "would pass / would not pass" (OBD Fusion), and hide readiness for packs that lack it, such as the D2.
8. **Explain faults,** with severity (Infocar), plain text and a search link per code. The text belongs in the pack's `dtc/` data.
9. **Publish dashboards and PID files as shareable data.** Import and export Torque CSV (already planned) and RealDash XML. That covers the formats forums already trade.
10. **Add a vehicle view widget,** the OVMS-style top-down car showing doors, lights and tyres. It suits the bcu body module and a later alarm destination.
11. **Follow HA's entity categories.** Pack signals carry a role (primary, config or diagnostic) so a module page can group them the way HA groups entities.

## Anti-patterns to avoid

- **Making the user pick a protocol or profile from a long list** (Car Scanner). Detect first and ask only when detection is ambiguous.
- **Charging per action, or for actions the car cannot support** (OBDeleven credits). Ostler is AGPL and has no paywalls, so it should **never show greyed-out "Pro" items**. It shows only what the pack and the vehicle support.
- **Requiring a cloud server to identify the car** (Carista). This breaks local-first.
- **Feature splits by platform** (FORScan Lite vs Windows). The PWA should be one app, with capability set by the connected hardware rather than the device.
- **One value per gauge with no sensor search** (Car Scanner, BimmerLink). Build signal pickers with search and filtering by module from day one.
- **Hiding the module behind a task with no way to see it.** Task recipes are fine, but each one must say which module it touches. That is also our safety-gate audit.
- **Raw hex editing as the main config UI** (FORScan as-built). Expose named settings from the pack, and keep raw access in admin.

## Reuse and licences

| Material | Licence | Use |
|---|---|---|
| [RealDash-extras](https://github.com/janimm/RealDash-extras) OBD2/CAN XML and protocol docs | Unlicense (public domain) | Safe to read, import and export. A good model for an `init`/`rotation` poll list. |
| Torque PID CSV column layout ([audizine](https://audizine.com/threads/torque-non-standard-pids.920460/)) | A file format; individual community files have no clear licence | Implement the format, but do not bundle community PID files without permission. |
| [AndrOBD](https://github.com/fr3ts0n/AndrOBD) | GPL-3.0 | Ideas only (plugin and MQTT architecture). Compatible with AGPL, but we take no code by default. |
| [OBDb](https://github.com/OBDb) signal sets | CC BY-SA | Already planned for import (landscape.md). |
| Torque, Car Scanner, OBD Fusion, OBDeleven, Carista, Bimmer*, FORScan, Infocar, RealDash apps | Proprietary | UI study only. Do not use their DTC text, coding databases or One-Click recipes; these are dealer-derived or vendor IP. |
