---
title: "OVMS UI and menu structure: web UI, apps, and the generic-versus-vehicle split"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/ovms.md]
summary: >
  How OVMS structures its user interfaces: the v3 module web UI (four menus that pages register into, with a vehicle menu that appears with the vehicle type), the dashboard and metric widgets, web plugins and hooks, the Android and iOS apps, and how v2 messages map to screens. Covers licences and what Ostler should copy: register pages, don't hard-code them, and make capabilities machine-readable, which is where OVMS falls short.
---

# OVMS UI and menu structure

This file extends [ovms.md](../ovms.md) (interop: MQTT, metrics, poller, power) with UI and
structure only. Source read at heads: [OVMS3](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3)
Oct 2026; [Android](https://github.com/openvehicles/Open-Vehicle-Android) 2026-09-13 (5.3.1);
[iOS](https://github.com/openvehicles/Open-Vehicle-iOS) 2021-09-23; [Server](https://github.com/openvehicles/Open-Vehicle-Server) 2026-09-23.

## TL;DR

- **Web UI menu:** fixed top menu **Main · Tools · `<Vehicle>` · Config**, rebuilt on every load from a page registry (`RegisterPage(uri, label, handler, PageMenu_X, auth)`). Vehicle modules register pages on construction and deregister on destruction, so the vehicle dropdown appears, disappears and is retitled with the vehicle type.
- **Generic vs specific:** generic metrics (`v.b.soc` …) feed generic screens; modules add `x<id>.*` metrics, an `x<id>` command subtree and `/x<id>/…` pages, and opt in to **shared page handlers** (BMS cell monitor, climate schedule, brake light).
- **Dashboard:** EV-shaped (speed, plus voltage, SOC, efficiency, power and four temperatures, plus range). A vehicle can change only scales and bands (`GetDashboardConfig`), not which gauges appear.
- **Extensibility:** user **page plugins** (into any menu) and **hook plugins** (into named hook points); any `class="metric" data-metric="…"` element updates live over a websocket.
- **Android (ui2):** car render, **quick actions**, and tiles for Controls, Climate, Location, Charging, Energy and Settings; Notifications doubles as a console. Per-vehicle adaptation is almost all **hard-coded `car_type` checks** (`"SQ"` 39×, `"RT"` 25×, `"NL"` 15× in `ui2/`).
- **Root cause:** the v2 capabilities message (`V`) exists, but v3's `TransmitMsgCapabilities()` is an **empty stub**, so apps cannot discover support and users hit "unsupported operation" ([#179](https://github.com/openvehicles/Open-Vehicle-Android/issues/179), [#180](https://github.com/openvehicles/Open-Vehicle-Android/issues/180)). **Lesson: capabilities must be data.**
- **Vehicle-agnostic app, attempted:** in 2020 the founder proposed a **"virtual vehicle" metric set plus per-vehicle, per-screen-size templates** ([ovmsdev](https://lists.openvehicles.com/archives/list/ovmsdev@lists.openvehicles.com/thread/2LNSRDPRCUZ47UIBDCMZUTLFNH2O4SQ3/)). It became [Open-Vehicle-React-App](https://github.com/openvehicles/Open-Vehicle-React-App), a five-tab skeleton archived before the plugin layer existed. Ostler's exact problem, left unsolved.
- **Licences:** firmware and Android are MIT (bar annotated third-party code); iOS and server have **no licence file** (read only); bundled Highcharts is **not** free for commercial use.

## 1. The v3 module web UI

### 1.1 Framework

- **Stack:** mongoose, Bootstrap 3, jQuery, Highcharts 6; a single-page app. `/` loads a shell with `#menu` and `#main`; pages are HTML fragments AJAX-loaded into `#main`, with hash deep links (`/#/status`, `/#/dashboard?nm=1` for night mode).
- **Live data:** one websocket pushes metric deltas, events, logs and notifications to every `.receiver` element.
- **Display:** full-screen and night-mode toggles ("for night time driving"); installable as a web app.
- **Auth per page:** `PageAuth_None` (Dashboard, Home are public), `PageAuth_Cookie` (60-min sliding session), `PageAuth_File` (htaccess digest).

Sources: [webui.rst](https://docs.openvehicles.com/en/latest/userguide/webui.html), [web framework docs](https://docs.openvehicles.com/en/latest/components/ovms_webserver/docs/index.html), `ovms_webserver.cpp`.

### 1.2 Menu model

`ovms_webserver.h` defines `PageMenu_None | Main | Tools | Config | Vehicle`.
`CreateMenu()` (`web_framework.cpp`) walks the page registry in registration order and emits:

```
[Main items inline] | Tools ▾ | <VehicleShortName> ▾ (only if any Vehicle pages) | Config ▾ | ◱ ◐ Login/Logout
```

`/home` renders the same registry as big button groups ("Main menu", "Tools", "Vehicle",
"Config"). This is the touch-friendly landing page, and it shows setup and password warnings
at the top.

**Framework pages, as registered in `OvmsWebServer::OvmsWebServer()`:**

| Menu | Pages |
|---|---|
| Main | Dashboard (public), Status |
| Tools | Shell, Metrics, Editor |
| Config | Password, Vehicle, Wifi, Cellular/GPS*, Server V2 (MP)*, Server V3 (MQTT)*, Notifications*, Pushover*, Webserver, Web Plugins, Autostart, Firmware*, Partitioning*, Logging, Locations, Backup & Restore |
| none | `/cfg/init` setup wizard, `/api/execute`, `/api/file` |

`*` marks pages compiled in only when that component is enabled (`#ifdef CONFIG_OVMS_COMP_*`). The
menu therefore reflects the build as well as the vehicle.

**Inside the pages:** Status is a stack of panels (Live, Vehicle, Server, SD Card, Module,
Network, Wifi, Cellular). "Live" mixes generic metrics (memory, signal, GPS, main battery
SOC/V/A, 12 V, events); "Vehicle" shows `stat` output with **generic Start/Stop charge buttons,
even on non-EVs**. Config → Vehicle has tabs Vehicle / 12V Monitor / TPMS, and the **TPMS tab
appears only if `vehicle->UsesTpmsSensorMapping()`**: a small capability check of the right kind.

### 1.3 How a vehicle module adds menu pages

**Lifecycle:** the vehicle constructor calls `WebInit()`, the destructor `WebDeInit()`. Changing
type in Config → Vehicle destroys and rebuilds the object, so the menu swaps live. The dropdown
title is `VehicleShortName()` (default: the registered name; the Twizy says "Twizy").

Real menus from source (`vehicle_*/src/*_web.cpp`):

| Vehicle (type code) | Vehicle menu entries | Elsewhere |
|---|---|---|
| Nissan Leaf `NL` | Features · Battery config · BMS cell monitor* | — |
| Renault Twizy `RT` | Features · Brake Light* · Profile Editor · Drivemode Config · Battery Config · Battery Monitor* · Sevcon Monitor | **Main:** "Drivemode" console; **hook** into `/dashboard` (tuning sliders) |
| Kia Niro / Kona `KN` | BMS cell monitor* · Aux battery monitor · Features · Battery config | — |
| smart EQ 453 `SQ` | Features · Climate Schedule* · TPMS Config · ADC Calc · Battery config · BMS cell monitor* | — |
| smart ED gen 3 `SE` | Features · Battery config · BMS Cell Monitor* · Eco Scores · BMS Cell Capacity · Commands · Notifys | — |
| MG ZS EV / MG4 / MG5 | Battery config · BMS cell monitor* · Charging Metrics, plus **variant-specific** Version and Features | — |
| Volt / Ampera `VA` | — | **Main:** "Controls" |
| Cadillac CTS, Corvette (ICE) | *none*: no vehicle menu, default EV dashboard | — |

`*` = a **shared framework handler** (`OvmsWebServer::HandleBmsCellMonitor`,
`HandleCfgPreconditionSchedule`, `HandleCfgBrakelight`). Their source comments tell vehicle
authors to register them under their own URI and menu if supported: library pages a vehicle opts
in to, not pages every vehicle gets.

**Patterns across ~81 vehicle-menu registrations:**
- **"Features"** (vehicle config form) and **"Battery config"** are in almost every module: de facto standard names, each reimplemented.
- **Generic monitors are vehicle-registered:** the cell monitor reads only `v.b.c.*` but appears only where registered.
- **Vehicles rarely touch Main** (Twizy, Volt); Main stays for driving-time pages.
- **Namespacing** `/x<id>/…` matches `x<id>.*` metrics and the `x<id>` command; registration order decides menu order.

### 1.4 Dashboard and gauges

`HandleDashboard` (`web_displays.cpp`) draws one Highcharts gauge set:
- **Gauges:** a large speedometer, with aux gauges for voltage, SOC, efficiency, power, and charger, battery, inverter (PEM) and motor temperature.
- **Range overlay:** estimated and ideal range.
- **Vehicle input:** `GetDashboardConfig(DashboardConfig&)` fills only the `yAxis` scales and coloured bands. For example, the Leaf sets speed 0–135 with a green/yellow/red band split, and power −20…50 kW with a violet regen band.
- **Coverage:** 17 modules override it. The rest, including the ICE Cadillac and Corvette, get the EV defaults.

The dashboard's hook point is `body.pre`. The Twizy uses `RegisterCallback("xrt", "/dashboard", …)` to inject its tuning slider panel. A [solid-gauge plugin example](https://docs.openvehicles.com/en/latest/components/ovms_webserver/docs/solidgauge.html) shows how users build alternatives.

### 1.5 Metric widgets, web plugins and hooks

**Metric widgets** ([metrics.rst](https://docs.openvehicles.com/en/latest/components/ovms_webserver/docs/metrics.html)):
declarative markup such as `<div class="metric number" data-metric="v.b.12v.voltage" data-prec="1"><span class="value"></span><span class="unit">V</span></div>`.
Variants: text, number, progress bar, Highcharts gauge and chart (comma list for multi-series),
DataTables vector table (cells, TPMS). `metrics_user`/`metrics_label` (or `data-user`) convert
to the user's units; `msg:metrics` events serve scripts; `data-cmd` buttons run commands via
`/api/execute` and `loadcmd()` streams output.

**Plugins** (`RegisterPlugins()`; config `http.plugin.<key>.{enable,label,page,menu,auth,hook}`; files in `/store/plugin/<key>`):
- **Page plugin:** an HTML fragment registered with label, menu (Main/Tools/Config/Vehicle) and auth; installed via Config → Web Plugins (add → paste → choose menu); may override a built-in URI.
- **Hook plugin:** HTML injected at a named hook point. [hooks.htm](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/master/vehicle/OVMS.V3/components/ovms_webserver/dev/hooks.htm) lists `/` (html.pre, head.post, body.post), `/home`, `/dashboard` (body.pre), `/status`, `/shell` and the Twizy pages, and says "if you miss a hook somewhere, contact us".
- **Repositories:** `plugin repo install|refresh`, `plugin install|enable|update` (`ovms_plugins`). The documented flow is still manual copy-paste ([plugin README](https://docs.openvehicles.com/en/latest/plugin/README.html)); vehicle bundles exist (`v-twizy`, `v-vweup`).

### 1.6 Shell / command menu

- **Shell:** Tools → Shell is a web terminal: log monitor toggle (coloured by level), `OVMS#` prompt posting to `/api/execute`, streamed output (60 s timeout for `ota`, `test`, `co … scan`).
- **Command tree:** `MyCommandApp.RegisterCommand` → `cmd->RegisterCommand`, with usage strings and validators. Generic roots from `vehicle.cpp`: `vehicle module|list|status`, `stat [trip]`, `wakeup`, `homelink`, `climatecontrol on|off|schedule …`, `lock`/`unlock`/`valet`/`unvalet`, `charge mode|start|stop|current|cooldown`, `bms status|temp|volt|reset|alerts`, `vehicle aux monitor …`, `obdii …`.
- **Vehicle subtrees:** `xnl …` (Leaf), `xkn trip|tripch|tpms|aux|vin|trunk` (Kia), `xsq mtdata|hvcycles|ddt4all|canwrite|calcadc|ed4scan|preset|tpms …|show …` (smart EQ), `xrt …` (Twizy).
- **Support is implicit:** generic commands call virtuals (`CommandClimateControl`, `CommandLock` …) whose base returns `NotImplemented`; a vehicle "supports" one by overriding it (`NL`: ClimateControl, Lock, Wakeup). Only the firmware knows; see §3.

## 2. The apps

### 2.1 Android (current, Kotlin; MIT)

- **Two UIs:** the legacy `ui/` fragments plus the new **`ui2/`**, launched in 2025 with 5.x.
- **Navigation graph** (`res/navigation/mobile_navigation.xml`): Home leads to the screens below.

| Screen | Contents |
|---|---|
| **Home** (`HomeFragment`, 2,150 lines) | Car render with doors/lights/plug state (`CarRenderingUtils`), SOC and range header, **quick-action row**, then a **tab list**. Each tab is a tile with a live one-line summary. |
| Controls | Lock, valet, wakeup, homelink and TPMS (sub-pages Features, Parameters, Cellular stats, Logs) |
| Climate | Top-down car with cabin/ambient temperature, staleness label ("stale data, n mins"), climate quick action, climate schedule |
| Location | Map, plus map settings |
| Charging | Mode, limits (SOC/range), time to full, current |
| Energy | Battery, Power and Aux battery charts |
| Settings | Car list/editor, Control, app UI settings |
| Notifications | Separate screen; see §2.4 |

- **Tiles carry live summaries:** tyre pressures (Controls), "Cabin x, Ambient y" (Climate), geocoded address (Location), "~01:20h: 80%" (Charging), "Trip, Wh/km, Regen %" (Energy). Tabs can be hidden and recoloured; quick actions are user-picked; all of it is stored **per vehicle ID**.
- **Quick actions** are a closed set of classes (Charging, Climate, Lock, Wakeup, Valet, Homelink 1–3, ClimateSchedule, DDT4all, four TwizyDriveMode, plus **CustomCommand**: any shell command with an icon). Defaults are hard-coded per type: RT → charging, valet, drive profiles; SQ → lock, climate, schedule, wakeup, ddt4all; others → lock, charging, valet, wakeup, homelinks.
- **Multi-vehicle:** a toolbar spinner on Home switches car; car editor and groups live in Settings; switching re-logs into the server and re-subscribes push (`MP-0 p…`).
- **Per-vehicle adaptation** is by string checks on `car_type` (from the `F` message): Climate tile hidden for `RT`; climate schedule only for `NL, SE, SQ, VWUP, RZ, RZ2, VA*, VB*, OAE*`; an `SQ` Energy summary format; ~10 `SQ`/`RT` branches in Controls; feature-slot labels per type. **Only one** check uses the capability bitmap: `hasCommand(26)` for climate.

### 2.2 iOS (Objective-C; dormant since 2021; no licence file)

- **Tab bar:** Status (battery/charge) · Car (doors and lock images) · Location (map with car and charger annotations, clustering) · Messages · Settings.
- **Settings:** Cars list and form, Groups, Control → Features / Parameters / Cellular Usage / MMI-USSD / Reset module.
- **Separate iPad storyboard:** `ovmsStatusViewControllerPad`.
- **Vehicle visuals:** the car images in `carimages/` and `caroutlines/` give per-model artwork, selected per car in the car form.

### 2.3 OVMS Connect and the React attempt

- [**OVMS Connect**](https://apps.apple.com/app/id6747955064) is a **closed-source** paid app ($3.99, by Carsten Schmiemann) that speaks MQTT v3 directly.
  - Feature list: SOC/range/power dashboard, top-down vehicle view (doors, trunk, hood, charge port, headlights), and a "Hacker's Console" command line.
  - It confirms the pattern **render + summary metrics + console**. There is no code to reuse.
- **[Open-Vehicle-React-App](https://github.com/openvehicles/Open-Vehicle-React-App)** (archived 2022, no licence) was meant as a "unified app … plug-in architecture for vehicle API support, … highly customisable approach to displays". It only got as far as five bottom tabs: Status, Vehicle, Location, Messages, Settings.
- **[react-native-vehicle-gauges](https://github.com/openvehicles/react-native-vehicle-gauges)** (MIT, 2025) is a component library: speedometer, tachometer, battery (12 V half-dial), fuel, temperature, oil pressure and gear. Several of these suit an **ICE** cluster. It is React Native SVG, not DOM, but small enough to port ideas from.

### 2.4 Alarm / notification UX

- **Firmware** (see ovms.md): `info/alert/error/data/stream` types, dotted subtypes, per-channel filters.
- **Server:** push via APNS/FCM; per-type error-code text files (`v3/server/vece/<type>.vece`, e.g. `tr.vece` "23=SHUTTING DOWN PULL OVER SAFELY") turn numeric vehicle errors into words **server-side, per vehicle type**.
- **Android:** Notifications holds the **last 200 notifications, alerts, commands and results in one chat-style list**, filterable to the selected car; tap opens, long-press copies, tapping a past command reloads it. The input takes SMS-style (`STAT`), USSD (`*100#`), MSG (`#31`) and AT commands.
- **iOS:** the same idea under "Messages", with a chat view.
- **Command result feedback** is a toast with the v2 result code: 0 OK, 1 failed + text, 2 unsupported, 3 unimplemented.

### 2.5 Climate UX

- **One switch:** `climatecontrol on|off` (v2 command 26, wake-temperature subsystem 19).
- **Schedules:** the generic `climatecontrol schedule set|list|clear|copy|enable|disable` (per day, multiple times). It has a shared web page that vehicles opt in to (`/xsq/climateschedule`, `/xrz2/preconditioning`) and the app's ClimateSchedule action.
- **App screen:** the top-down car tinted by `car_hvac_on`, cabin and ambient temperatures with a staleness label, and the on/off action.
- **No target-temperature or zone control is generic.** Anything richer is vehicle-specific (e.g. SQ's 12 V trickle-charge coupling inside `CommandClimateControl`).

## 3. Server and v2 protocol → screens

- **Topology:** apps connect to the server (6867/6870), never to the car. The server relays car messages and caches the latest of each.
- **Message → screen map:**

| Msg | Content | App screen |
|---|---|---|
| `S` | SOC, range, charge state/mode/current, temps summary | Home header, Charging |
| `D` | Doors/lock/valet bitfields, cabin/ambient/motor temperatures, 12 V, staleness | Car render, Controls, Climate |
| `L` | Lat/lon, heading, speed, altitude, GPS lock | Location |
| `F` | Firmware, VIN, signal, **car type**, service | Drives all `car_type` adaptation |
| `V` | Command capabilities (`C1,C3-6,…`) | Should gate buttons; **v3 sends nothing** (`ovms_server_v2.cpp` stub) |
| `W` / `Y` | TPMS old/new format | Controls tile |
| `X` | Generator (V2G) | Energy/Charging |
| `P` / `p` | Push notification / subscription | Notifications |
| `C` / `c` | Command / result `<cmd>,<code>[,text]` | Toasts, console |
| `H` / `h` | Historical records (battery, power logs) | Energy charts |
| `G` / `g` | Car group subscription / update | Groups / map |

- **Commands are numeric:** 1–4 features/parameters (numbered slots), 10–25 charge/wakeup/lock/valet/homelink/cooldown, 30–32 history, 40–49 SMS/USSD/AT. So a vehicle setting reaches the app only as "feature #10", with labels the app hard-codes per type.

Sources: [messages](https://docs.openvehicles.com/en/latest/protocol_v2/messages.html), [commands](https://docs.openvehicles.com/en/latest/protocol_v2/commands.html), `ApiTask.kt`, `CarData.kt`.

## 4. Adding a vehicle (developer view)

- **Process** ([developers page](https://www.openvehicles.com/developers); [v3 Developer's Guide](https://docs.google.com/document/d/1q5M9Lb5jzQhJzPMnkMKwy4Es5YK12ACQejX_NWEixr0), a Google Doc): announce on the list → survey buses → record CAN dumps per activity → identify signals → C++ stub with basic metrics → PR with docs → iterate.
- **Layout:** `components/vehicle_<name>/{src,docs/index.rst,CMakeLists.txt,component.mk}`, a Kconfig switch `OVMS_VEHICLE_<NAME>` (depends e.g. on `OVMS_COMP_POLLER`), usually `<x>_web.cpp` for pages.
- **Hierarchy:**
  - Every module derives from `OvmsVehicle`. Some share intermediate bases: `KiaVehicle` → Kia Niro / Soul, `OvmsVehicleMgEv` → MG A/B, `OvmsVehicleToyotaETNGA` → Subaru Solterra, `OvmsVehicleDBC` → pure DBC.
  - A module registers one or more **type codes** with the factory, e.g. `RegisterVehicle<OvmsVehicleNissanLeaf>("NL","Nissan Leaf")`. There are 51 codes, and MG alone registers MGA/MGB/MGD/MG4/MG5.
  - Variants then pick web pages at runtime (`Mg4WebInit` versus `Mg5WebInit`).
- **What a module registers:** metrics (sets `StdMetrics.ms_v_*`; declares its own, e.g. `MyMetrics.InitFloat("xnl.v.b.soc.instrument", SM_STALE_HIGH, 0, Percentage)`, typed with unit and staleness class); commands (`x<id>` root plus `Command*` overrides); config (`MyConfig.RegisterParam("xkn", …)`, edited by its "Features" page); web (`WebInit`/`WebDeInit`, `GetDashboardConfig`); events.
- **Docs:** 40 of 49 vehicle docs carry a **"Support Overview"** table (Hardware / Controls / Additional Features / Metrics, each with a support status). It is a capability matrix, but only in prose. Neither the apps nor the web UI read it.

## 5. Licences and reuse

| Repo | Licence | Reuse in Ostler (AGPL-3.0) |
|---|---|---|
| OVMS3 firmware | MIT "for the majority"; third-party code annotated | Copy ideas or code with the MIT notice. Do **not** copy mongoose or wolfSSL/SSH (see ovms.md). |
| Web UI assets | Bootstrap 3 MIT, jQuery MIT, DataTables MIT, cbor.js MIT; **Highcharts 6 proprietary** (free only for non-commercial use) | Never vendor Highcharts; copy only the gauge-band and colour ideas. |
| Android app | MIT (majority) | Layouts and logic may be copied with notice; ideas freely. |
| iOS app | **No licence file**; Glyphish free icons (attribution) | Read only; no copying. |
| Server (Perl) | **No licence file**; GitHub shows none | Read only; reimplementing the documented protocol is fine. |
| react-native-vehicle-gauges | MIT | May port gauge geometry with notice. |
| Open-Vehicle-React-App | None, archived | Read only. |
| OVMS Connect | Proprietary app | Nothing. |

## 6. Synthesis for Ostler

### Adopt

1. **Use one page registry with menu slots, not a hard-coded nav.**
   - Each screen or module registers `{id, label, slot, auth/trust, order}`, and the shell builds its nav from that list. This is the same move as `RegisterPage(…, PageMenu_X)`.
   - Our `screens/registry.ts` plus `/catalog` already lean this way. Keep packs and add-on devices (guardian, AC controller, cameras) registering into it at load.
   - Keep the rule that nav entries vanish when their provider is absent. OVMS does this both with `#ifdef` and with vehicle teardown.
2. **Use four stable top-level slots, with the vehicle slot named after the vehicle.** OVMS's Main / Tools / `<Vehicle>` / Config maps cleanly onto ours:
   - **Drive/Main:** generic live and dashboard;
   - **Tools:** shell, metrics browser, logs, diagnostics;
   - **`<pack name>`:** pack pages such as D2 Slabs and body;
   - **Settings.**
   - Each add-on device (guardian, AC) gets its own entry in the same pattern, rather than being folded into Settings.
3. **Use shared page templates that a pack opts in to.** The BMS cell monitor and the climate schedule are generic pages a vehicle *chooses* to register. For us:
   - an "ECU list / DTC" page, a "live PID table", a "12 V monitor" and a "TPMS" page should be generic components;
   - a pack lists which ones apply, with its own labels;
   - this avoids every pack reinventing "Features" and "Battery config" (OVMS's duplication).
4. **Build declarative metric widgets.** `data-metric` plus `class="metric number|progress|chart"` is the right primitive:
   - a widget names a signal, and the unit, precision, staleness and band come from the signal store;
   - our `Readout`, `RangeBar` and `Sparkline` already follow the "no labels or units in components" rule;
   - extend it so a **pack-supplied layout (JSON) can compose any page** from these widgets. That is Mark Webb-Johnson's 2020 "templates per vehicle type and per screen type", which OVMS never shipped.
5. **Use hook points on generic pages.** A pack or device can inject a panel into Drive or Home at named slots, as with `/dashboard:body.pre`, instead of forking the page. Document the slot list, and avoid OVMS's "contact us if you miss a hook" by giving every generic page header, body and footer slots.
6. **Keep a notification log that doubles as a console.** The 200-entry chat-style list mixing alerts, commands and results, with tap-to-resend, is shared by Android and iOS, and OVMS Connect ships a console too. Fit for us:
   - put the alarm (notify-only) events in this log;
   - keep raw commands behind Experimental/admin.
7. **Store per-vehicle UI preferences**, keyed by vehicle ID: hidden tabs, quick actions, colours. Ostler will hold more than one vehicle pack and profile.
8. **Make quick actions a user-picked subset of catalog actions**, plus a "custom command" escape hatch for admin.
9. **Show staleness explicitly in the UI** ("stale data, 12 mins") — this matches our "never show a stale value as live" rule.

### Avoid

- **Hard-coded vehicle-type checks in the UI.** The Android app tests `car_type` dozens of times; adding a vehicle means an app release.
  - Our existing guard (no module IDs outside `src/vehicles/`) is the right control. Extend it to "no pack IDs in screens".
- **Capabilities that exist only in code.**
  - In OVMS, support is decided by which virtuals a vehicle overrides, and the `V` message is never sent.
  - Users then see controls that fail with "unsupported operation" ([#179](https://github.com/openvehicles/Open-Vehicle-Android/issues/179): Leaf charge-current controls shown although "all other vehicles apart from roadster" lack them). [#180](https://github.com/openvehicles/Open-Vehicle-Android/issues/180) asks to "automatically hide unsupported functions".
  - **Ostler packs must publish a machine-readable capability and action list (our `/catalog`), and the UI must render only what it lists.**
- **A dashboard with fixed gauges whose ranges are the only thing a vehicle can change.** The EV gauge set is meaningless on ICE vehicles, yet the Cadillac and Corvette inherit it. Our Drive tiles must come entirely from the pack layout.
- **Generic actions on the wrong vehicle**, such as Start/Stop charge on the Status page for every vehicle type.
- **Icon-only controls and ambiguous toggles.** [#180](https://github.com/openvehicles/Open-Vehicle-Android/issues/180) reports "not clear from the icons what each quick action button does" and asks whether "tapping the padlock will lock the car rather than unlock it". Always pair the icon with a word and show state and result explicitly, consistent with our calm-instrument rule.
- **Decoration over data.** [#141](https://github.com/openvehicles/Open-Vehicle-Android/issues/141): "more technical information over so much space used for a picture of a charging plug". [#180](https://github.com/openvehicles/Open-Vehicle-Android/issues/180): the headline metric (SOC) became "rather small" in the new UI. Keep the one-line health answer large, and keep any car render secondary.
- **Numbered opaque settings** (v2 "feature #10"). Settings need names, units and help from the pack.
- **Two diverging native apps.** The founder's own reason for wanting a unified app was that the two "are diverging too much". Our single PWA avoids this.

### How OVMS reconciles generic and vehicle-specific, and what we take from it

| Layer | OVMS mechanism | Works? | Ostler equivalent |
|---|---|---|---|
| Data | Standard metric tree plus `x<id>.*` | **Yes** | Signal store, using OVMS names where they apply, plus `xd2.*` |
| Actions | Generic command virtuals plus `x<id>` subtree | Partly: support is invisible | Catalog actions with explicit availability and trust |
| Capabilities | Implied by overrides; `V` message stubbed; prose "Support Overview" tables | **No** | Pack manifest: capabilities, actions, pages, gauges |
| Pages | `RegisterPage` into a slot; shared handlers; vehicle menu with vehicle name | **Yes** (web) | Registry plus pack-registered views and shared templates |
| Dashboard | Fixed EV gauges; vehicle sets scales only | Weak | Pack layout chooses the widgets; bands come from signals |
| Apps | Hard-coded `car_type` branches | **No** | UI reads the manifest; no pack IDs in screens |
| Extensibility | Page and hook plugins, metric widgets | **Yes** | Named slots plus declarative widget layouts |

**Bottom line:** OVMS solved the generic-versus-specific split well **inside the module**, through
its metrics namespace and page registry. It did not carry that split **across the wire to the
apps**: there is no capability manifest and no template layer. Ostler should copy the registry
and metric-widget model and close the gap with a per-pack manifest that the PWA consumes.

## Sources

- **OVMS3 source** (`vehicle/OVMS.V3/components/`): `ovms_webserver/src/{ovms_webserver,web_framework,web_displays,web_cfg,web_cfg_status,web_cfg_vehicle,web_cfg_climate}.cpp`, `ovms_webserver.h`, `ovms_webserver/dev/{hooks,metrics}.htm`, `vehicle/vehicle.{h,cpp}`, `vehicle_{nissanleaf,renaulttwizy,kianiroev,smarteq,smarted,mgev,renaultzoe,renaultzoe_ph2,voltampera}/src/*`, `ovms_server_v2/src/ovms_server_v2.cpp`, `ovms_plugins/src/ovms_plugins.cpp`, `ovms_webserver/assets/README.*`.
- **Android source:** `res/navigation/mobile_navigation.xml`, `ui2/pages/{Home,Climate,Controls,Notifications}Fragment.kt`, `ui/settings/FeaturesFragment.kt`, `entities/CarData.kt`, `api/ApiTask.kt`, `res/values/strings.xml`. **iOS:** `MainStoryboard_iPhone.storyboard`. **Server:** `README`, `v3/server/vece/*.vece`.
- **Docs:** [Web UI](https://docs.openvehicles.com/en/latest/userguide/webui.html) · [Web framework](https://docs.openvehicles.com/en/latest/components/ovms_webserver/docs/index.html) · [Plugins](https://docs.openvehicles.com/en/latest/plugin/README.html) · [Leaf guide](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html) · [Protocol v2](https://docs.openvehicles.com/en/latest/protocol_v2/index.html) · [Developers](https://www.openvehicles.com/developers).
- **Discussion:** [Unified app proposal (ovmsdev, 2020-06-15)](https://lists.openvehicles.com/archives/list/ovmsdev@lists.openvehicles.com/thread/2LNSRDPRCUZ47UIBDCMZUTLFNH2O4SQ3/) · Android issues [#141](https://github.com/openvehicles/Open-Vehicle-Android/issues/141), [#179](https://github.com/openvehicles/Open-Vehicle-Android/issues/179), [#180](https://github.com/openvehicles/Open-Vehicle-Android/issues/180) · [OVMS Connect](https://apps.apple.com/app/id6747955064) · [openvehicles repos](https://github.com/orgs/openvehicles/repositories).
