---
title: "Core screens adoption — the owner's Home, Drive mode, Logs and log summary designs as separate PWAs (front door, Logs, Diagnostics, Drive), with a Map tab, per-log stats and the connect prompts — design"
area: specs
status: draft
version: 0.2
updated: 2026-10-11
depends_on: [references/design/2026-10/core-screens/README.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-logs-at-scale-design.md, references/design/2026-10/brief/50-vehicle-f-trips.md]
summary: >
  Draft v0.2. Adopts the owner's core screens design (references/design/2026-10/core-screens) under the owner's direction of 2026-10-11 (ADR-0049 v1.3, in progress): every screen is a PWA in its own repo, sharing one template and theme, served from ostler.app and by the Brain, installable via Chrome and runnable side by side. Home goes to the front door (`ostler-app-hub`), the Logs list, Map and log summary to Logs (`ostler-app-trips`), Diagnose to Diagnostics, Drive mode to a new Drive PWA; Security is an add-on PWA. The design's nav becomes a shared app switcher; deep links join a fault and the drives around it. The owner's changes stay: Trips is called Logs, Map is a tab inside Logs, a log opens to its summary first; the design corrections stay (token speed ramp, outlined icons, no sparkline while Moving). Adds the front door's connect, pair and choose-gateway prompts with a per-device options table, and four dismissible banners (never in Drive mode, one at a time). The gateway runs on the most permanent device (Brain, else the Android gateway app, else a node live only, else a browser session recording nothing) and holds history; `GET /sessions/{id}/stats` lives on its history API (the Brain's Python service today) for Logs and Diagnostics. Build order: PWA entry points on today's one UI codebase, then Logs, the front door, Drive and the Diagnostics links. Open questions: migration path, Map with no drive, Statistics scope, design file, optional accounts, per-car HTTPS name.
---

# Core screens adoption — design

**Status: draft, v0.2, for the owner's approval.** It turns the owner's design of 2026-10-08
([core screens][design], PNG renders) into build work under the direction of 2026-10-11. It
does not redesign: where design and an approved spec differ, it says which wins and why.

## 1. Context

The design draws **01 Home**, **02 Drive mode**, **03 Trips** (list) and **04 Trip detail** for
the reference car (2002 Discovery 2 Td5, RHD) on phone (393×852), HU-7 (1024×600, Parked) and
HU-5 (800×480, Moving): nav on the driver's side (right), maps on the passenger side (left).

[ADR-0049][adr49] v1.2 framed one Ostler app; the owner's direction of 2026-10-11 (ADR-0049
v1.3 and an ADR-0050 amendment, in progress) replaces it: **every screen is a PWA in its own
repo**, one shared template and theme, served from ostler.app and by the Brain (which can
install them), installable via Chrome, two side by side on a head unit:

| Design | PWA (repo) | Its screens |
|---|---|---|
| 01 Home | **Ostler front door** (`ostler-app-hub`) | welcome, connect, pair, choose gateway, Home, Apps gallery, Garage, Devices, Permissions, Outputs, Settings |
| 03 Logs list, Map, 04 log summary | **Logs** (`ostler-app-trips`) | logs list, statistics, log summary, playback, Map, export |
| Diagnose (nav item) | **Diagnostics** (`ostler-app-diagnostics`) | overview, faults and fault detail (linking to drives), live data, tests (guarded), procedures, decode lab, docs |
| 02 Drive mode | **Drive** (`ostler-app-drive`, new) | drive mode; edit layout, Parked only |
| — | add-ons, each its own repo | Security, Maintenance, friends' map, Social, mesh |

The design's nav (Home · Diagnose · Logs · Map · More) becomes the cross-app switcher (§3);
Map is a tab inside Logs. Security is an add-on PWA, no longer a nav item or a More row.

**Where the gateway runs.** On the most permanent device present: the **Brain**; else the
native Android **Ostler Gateway** app (needed only when there is no gateway device); else a
**node** (live only); else **the browser itself** (a WebUSB or Web Bluetooth session, nothing
recorded). History lives in the gateway. Writes need a step-up approval on screen, then the
node gate (or, with no node, the host's soft gate under [ADR-0044][adr44]) decides
([ADR-0033][adr33]).

Much was already specified ([UI §12.2][ui-12.2], [trips-detail brief][brief],
[visual §8 and §10][vds], [drive modes §4.3][dm-4.3], [trip sharing §5.4][ts-5.4]); this spec
records what the owner chose on top.

## 2. What is adopted

**Adopted:** every frame of 01 Home, 02 Drive mode (phone and HU-5 Moving), 03 Trips and
04 Trip detail, as the default look (themes may restyle it; [visual §13][vds-13]).

**Not adopted:** "HU-5 · Moving · message alert" (ADR-0049 dropped the Phone app; any future
alert card follows [UI §14][ui-14] under its own spec).

**The owner's changes** (binding):

1. **Trips is called Logs**; routes and strings stay `logs` (the repo name `ostler-app-trips`
   stays). [UI §12.2][ui-12.2]'s rename to Trips is not carried out.
2. **Map replaces Security** in the design's nav, as a tab inside Logs (§5); Security is an
   add-on PWA.
3. **Opening a log shows its summary first**; **Play back** enters the existing replay.

**Design notes the build corrects:**

- The design's violet speed ramp is a placeholder; the build uses the token ramp `speed-1` …
  `speed-6` ([`data.tokens.json`][tokens], [visual §3.3][vds]), as `speedColors()` in
  [`trace.ts`](../ui/src/components/replay/trace.ts) already does.
- Icons keep the repo's outlined Material Symbols, not the design's Rounded set.
- No sparkline while Moving ([drive modes §4.3][dm-4.3]): only Parked and Idling (§10).

## 3. Moving between apps

- **Own nav per PWA.** Each app has its internal nav on the template's rail (driver's side on
  head units) or bottom bar (phone), via [`Nav.tsx`](../ui/src/shell/Nav.tsx) and
  [`layoutClass.ts`](../ui/src/shell/layoutClass.ts), unchanged. Logs: **Logs** (with frame 03's
  Logs | Statistics control) and **Map**. The front door: Home, Apps, Garage, Settings.
- **Shared app switcher** in the template: links to the front door and to the other apps the
  gateway lists as installed (the front door's Apps gallery is the same list). Where the
  browser captures links into an installed PWA, the link opens it; else it opens a tab.
- **Deep links:** Home's faults banner → Diagnostics faults; Drive card → Drive; last log →
  Logs summary; a fault's detail → Logs with the drives around it (Diagnostics asks the gateway,
  `GET /sessions?from=…&to=…`); a log's faults → Diagnostics fault detail. Every link is a URL,
  so Back and a reload work, and it degrades to a tab.

**Migration (proposed; open question 1).** `ui/` is one bundle today, one
[`manifest.webmanifest`](../ui/public/manifest.webmanifest) at scope `/`. First, one codebase
with **an entry point per PWA** (HTML entry, manifest with own `id`, `start_url` and `scope`,
service worker): `/` (front door), `/logs/`, `/diagnostics/`, `/drive/`, and `/security/` as
the first add-on; [`destinations.ts`](../ui/src/shell/destinations.ts) and
[`routes.ts`](../ui/src/shell/routes.ts) split per entry, the shared shell becomes the template.
Then each app moves to its repo. Nested scopes on one origin need checking on Chrome for Android.

## 4. Front door: connect, pair, choose gateway, banners

These are prompts for the designer brief, not pixel specs.

- **Welcome:** what Ostler is, then Connect.
- **Connect chooser:** offers only what this device can do; a found gateway comes first.

| Option | Android Chrome (phone, head unit) | Desktop Chrome or Edge | iPhone, Firefox, other |
|---|---|---|---|
| **Found gateway** (Brain, gateway app or node on this network) | yes | yes | yes |
| **Install the gateway app** (Android) | yes | — | — |
| **Get a permanent gateway** (opens the comparison) | yes | yes | yes |
| **Try in the browser** (WebUSB or Web Bluetooth, nothing recorded) | yes | yes | — |
| **View remotely** (read-only, a gateway elsewhere; [ADR-0028][adr28]) | yes | yes | yes |

- **Pair** over a local link ([ADR-0033][adr33]): code or QR, the role given, what it may approve.
- **Choose gateway:** Brain, gateway app, node only, browser session, compared on history, logging
  after the phone leaves, live data, writes (through the gate) and hardware; recommended first.

**Banners** (dismissible; **never in Drive mode**; **at most one at a time**, the first that
applies in this order):

| State | Text (draft) |
|---|---|
| Gateway unreachable | "Showing saved data. Can't reach the gateway." |
| Browser session | "Not recording. Logs need a gateway." |
| Phone as gateway | "Logs stop when your phone leaves the car." |
| No logs yet | "No logs yet. Drive with a gateway connected." |

PWAs need a **per-car HTTPS name** (open question 6) to install and to reach the local gateway
from an HTTPS page ([ADR-0021][adr21]).

## 5. Map (tab in Logs)

`Map.tsx` in the Logs PWA: [`TraceMap`](../ui/src/components/replay/TraceMap.tsx) full screen
under the strip, with its legend. It shows the **drive in progress** (trace re-fetched as
[`LiveAnalysis`](../ui/src/screens/Analysis.tsx) does, following the GPS fix); with **no drive**,
the last log framed to its `bbox`, a chip opening its summary; in **replay**, the replayed log
following `useReplay().t`; with **no GPS anywhere**, "No location yet".

Colour by speed (default, the six ramp bands of the user's unit) or a picked signal
(`ChannelPicker`, `Legend`); `BasemapSwitch`, styled by theme
([`mapStyle.ts`](../ui/src/components/replay/mapStyle.ts)); Moving on a driver-facing head unit,
TraceMap's `drive` mode ([drive modes §4.3][dm-4.3]). The map logic moves out of `Analysis.tsx`
into a shared hook, so Map and Analysis draw from one place.

## 6. Logs list

[`Logs.tsx`](../ui/src/screens/Logs.tsx), [`SessionBrowser.tsx`](../ui/src/components/replay/SessionBrowser.tsx)
and [`SessionList.tsx`](../ui/src/components/replay/SessionList.tsx), restyled per frame 03:

- **Logs | Statistics** control, replacing the Sessions | Analysis toggle in
  [`LogsDestination.tsx`](../ui/src/destinations/LogsDestination.tsx); Analysis stays reachable
  from Play back and Rewind.
- **Last 14 days strip:** a cell per day filled by km, today outlined, totals beside; from
  `GET /sessions/histogram?group=day&year=…`. Tapping a day scrolls to it.
- **Day groups** ("Today", "Yesterday · Tue 6 Oct", dates) with the day's km and logs. **Rows:**
  mini map in the speed ramp, start → end, time · km · duration, **MAX** speed trailing; two
  columns on HU-7 and wider; search, filters and month scrubber stay.
- **Opening a row** goes to the summary (§7); the drive in progress still opens live Analysis.
- **Statistics** (first cut, open question 3): year heatmap and period totals (distance, logs,
  time, moving, idle, average and max speed).
- Parked only on driver-facing head units ([UI §12.1][ui-12.1]).

## 7. Log summary

A new route and screen, `LogSummary.tsx`, per frame 04. `Logs.open()` selects the log and
goes to the summary instead of `replay.enter(id)`; the log id is in the URL (`/logs/…/{id}`),
so Back, a reload and deep links from Home or Diagnostics land on it.

**Layout.** Landscape: the map fills the screen, the sheet on the **passenger side** (left on
RHD, following the rail side setting), about 40 % wide. Phone: map on top (about 40 %), sheet
below, scrolling. The map is `TraceMap` by speed, start and end markers, no cursor.

**Sheet, top to bottom:**

1. Back, title (start → end place, or the log's name), date and time range, **Play back**.
2. **Hero:** distance (`type-num-xl`).
3. **3×3 grid:** distance, average speed, max speed (with **sustained best**, "best 30 s 91") /
   duration, idle, moving / elevation gain, stops, average moving speed.
4. **Time at speed:** donut in the six ramp bands, **Time / Distance** control, legend rows
   with label, value and % ([visual §8][vds-8]).
5. **Signal chart:** speed by default; Speed, Coolant, Boost, Battery (by VSS role, if
   recorded) and "More…" (`ChannelPicker`). Gaps drawn as gaps; the max labelled.
6. **Faults seen** link to Diagnostics fault detail (§3); notes later ([UI §12.2][ui-12.2]).

**Play back** calls `replay.enter(id)` and opens Analysis, the existing replay
([`replay.tsx`](../ui/src/state/replay.tsx)), unchanged.

**States:** **loading** (map on `bg`, skeleton sheet; meta from `GET /sessions/{id}` first,
stats fill in); **no GPS** (no map, "No location in this log"; distance and speeds from ECU road
speed when recorded, else "—"); **partial channels** (a figure without its source shows "—" with
a short reason on focus, such as "No altitude recorded"; no speed source, no donut); **recording
now** (no summary; the row opens live Analysis); **gateway unreachable** (the cached summary if
the service worker has it, with the banner; else "Could not load this log" with Retry).

## 8. Backend: per-log stats on the gateway's history API

History lives in the gateway, so the stats do too. **`GET /sessions/{id}/stats`** belongs to the
gateway's history API: on the Brain today, the existing Python service
([`logbook`](../src/openostler/logbook/index.py)); a gateway app implements the same OpenAPI
contract later. Logs (summary, Statistics, and Home's tiles in the front door) and Diagnostics
(drives around a fault) both use it. A browser session has no history, so no stats.

A separate call, not new fields on `GET /sessions/{id}`: meta stays cheap and stable and shows
at once; stats (the full recording, for older logs) follow. Public mode: `filtered`.

**Reply** (unrounded numbers; the UI rounds per [trip sharing §5.4][ts-5.4]'s L1–L4 column):

```json
{ "v": 1, "speed_source": "gps|ecu|none", "distance_m": 37200, "duration_s": 2880,
  "moving_s": 2640, "idle_s": 240, "avg_kmh": 46.5, "avg_moving_kmh": 50.7,
  "max_kmh": 96, "sustained_best_kmh": 91.2, "gain_m": 412, "stops": 3,
  "unit": "km/h", "bands": [ {"lo": 0, "hi": 30, "time_s": 410, "distance_m": 1900}, … ] }
```

**Code.** Reuse `trace_stats()`, `elevation_gain_m()` and `no_gps_stats()` in
[`share/trace.py`](../src/openostler/logbook/share/trace.py). A new
`src/openostler/logbook/stats.py` builds a `VisibleTrace` straight from `fixes(rows)` (no ends
trim or privacy zones, so not `visible_trace()`), and integrates no-GPS logs whole (the 2-minute
edges become a parameter, 0 here, unchanged for shares).

**Definitions** (as [trip sharing §5.4][ts-5.4] where it already defines them):

| Figure | Definition |
|---|---|
| Moving time | time at ≥ 5 km/h (`MOVING_KMH`) |
| Idle time | duration − moving time: stationary time inside the log |
| Average speed | distance ÷ duration; **average moving** = distance ÷ moving time, which is what `trace_stats()` calls `avg_kmh` (the design's 46 vs 51 km/h) |
| Max speed | max of the speed source (ECU road speed when recorded, else GPS) |
| Sustained best | the fastest average over any 30 s window: distance in the window ÷ 30 s; windows with a gap > 5 s are skipped |
| Time at speed | per band of `SPEED_BANDS` in the user's unit (trace.ts lines 52–60): time, and distance, of samples whose speed falls in the band; each sample weighted by the interval to the next |
| Elevation gain | 30 s median filter, sum of rises ≥ 3 m |
| Stops | still periods ≥ 60 s |

Bands come in the unit asked (`?unit=km/h|mph`, default the user preference), so one colour
means one speed, as the ramp requires.

**Cache.** Computed when a log ends, stored in the session index
([`index.py`](../src/openostler/logbook/index.py)) as a versioned `stats` JSON column; computed
on first request for older logs and when `v` changes (today only distance, duration and max
speed are stored, [`recorder.py`](../src/openostler/logbook/recorder.py) lines 1091–1100).

**Contract and tests.** `api/openapi.yaml` gains the path and a `SessionStats` schema
([api/README](../api/README.md)); `tests/test_session_stats.py` on synthetic fixtures (moving,
idle, stops, sustained best, band totals, no-GPS with ECU speed, no speed, mph bands), the
contract test, and `tests/test_share_trace.py` unchanged and passing.

## 9. Home (front door)

[`Home.tsx`](../ui/src/destinations/Home.tsx) restyled per frame 01, on existing tokens and
layout classes, as the front door's Home:

- Faults banner (count, first fault names) → Diagnostics faults; **Drive** card → Drive PWA.
- Vehicle card: photo (placeholder until set), name, year · engine · gearbox · drive side,
  **odometer** with an "Estimated" chip when it is not read from the car.
- Stat tiles: battery, fuel average, coolant (live); 7 days km, logs in 7 days, drive time,
  average speed, max speed, idle % (from the gateway's index and §8's cached stats). A tile
  with no source is hidden, not zero.
- Last log (mini map, start → end, km · duration), opening its Logs summary; the Apps card
  opens the Apps gallery.
- HU-7: banner and vehicle card left, tiles and last log right; HU-wide keeps the vehicle pane.

## 10. Drive (PWA)

[`Drive.tsx`](../ui/src/screens/Drive.tsx) and [`ui/src/drive/`](../ui/src/drive/) restyled
per frame 02, for the Diagnostic preset's six tiles (boost, coolant, battery, intake air, fuel
now, trip); edit layout Parked only:

- Top strip: back (to the app it came from), faults chip, module chip (TD5), REC, Ghost, clock,
  bookmark. No banners (§4).
- Tiles: label, value with unit, arc gauge or range bar with the normal band (Trip: km and
  duration, no bar); alarm ("HIGH") as border and value colour plus the word.
- **Moving rules unchanged** ([drive modes §4.3][dm-4.3]): ≤ 6 tiles, no scrolling, labels
  ≥ 24 px and the class's number floor, no glow, no animation, **no sparkline** (shown only
  Parked and Idling), refresh ≤ 4 Hz. The render check and no-scroll tests must pass on phone
  and HU-5.

## 11. Build order

Every step: `cd ui && npm run check`, `npm run e2e`, `pytest -q`, `reuse lint`, the docs
scripts, and Playwright screenshots at phone, HU-7 and HU-5 compared with the design frames and
attached to the PR. Styling only through tokens (`ui/tokens/*`): no raw colours or px font sizes.

| Step | Scope | Acceptance |
|---|---|---|
| 1 | PWA entry points, manifests and service workers on the existing UI (§3), served by the Brain with the per-car HTTPS name, or a dev certificate first ([HTTPS on the Pi](../docs/https_on_the_pi.md)) | Front door, Logs, Diagnostics, Drive and Security install in Chrome as separate apps, each opening at its own scope; two run side by side on a head unit; the switcher links between them; existing e2e green |
| 2 | Logs PWA: list, summary, stats endpoint, Map (§5–§8) | `/sessions/{id}/stats` matches the definitions on fixtures; OpenAPI updated; opening a log lands on the summary; Play back enters replay at the start; no-GPS and partial states render; Logs \| Statistics, 14-day strip, day groups, rows with MAX; Map follows a live drive (fixture), shows the last log, follows replay |
| 3 | Front door: welcome, connect, Home, Apps gallery (§4, §9) | Frame 01 at phone and HU-7, Night and Day; the connect chooser shows only this device's options; one banner at a time; hidden tiles without sources; stylelint ratchet not raised |
| 4 | Drive PWA (§10) | Frame 02 at phone and HU-5 Moving; no sparkline while Moving; no banners; render check and no-scroll tests pass |
| 5 | Diagnostics links (§3) | A fault's detail lists the drives around it from the gateway and opens their summaries; a summary's faults open Diagnostics; both degrade to a tab when the other app is not installed |

## 12. Open questions for the owner

1. **Migration path.** Default: one codebase with an entry point per PWA first (§3), then a
   repo per app once the template is a package. Alternative: separate repos at once.
2. **Map with no drive.** Default: the last log. Alternatives: the current position only, or
   the last 7 days of logs together.
3. **Statistics scope.** Default first cut: year heatmap and period totals. Alternative: the
   full [UI §12.2][ui-12.2] Statistics (hero, distribution, records, sprints) in step 2.
4. **The design file.** Default: PNG renders only (the 2 MB rule; the 4.5 MB HTML carries the
   design tool's runtime under an unknown licence; maps render blank). Alternative: commit it.
5. **Accounts optional?** Default: no account for local use (connect, pair, logs, diagnostics);
   an account only for view remotely and the social add-ons.
6. **Per-car HTTPS name.** Options: a name per car under ostler.app with a certificate by
   ACME DNS-01 and a local DNS answer; a per-device local CA ([ADR-0021][adr21]) installed on
   each phone; or a dev certificate only until one is chosen.

## Changelog

- 0.1 (2026-10-08): first draft from the owner's core screens design and changes.
- 0.2 (2026-10-11): the owner's PWA direction (ADR-0049 v1.3, in progress): screens map onto
  separate PWAs, Security an add-on; "Moving between apps"; front door prompts and banners;
  stats on the gateway's history API; build order around PWA entry points; open questions
  updated.

[design]: ../references/design/2026-10/core-screens/README.md
[adr21]: ../decisions/adr-0021-local-https-on-the-device.md
[adr28]: ../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[adr33]: ../decisions/adr-0033-action-categories-and-approvals.md
[adr44]: ../decisions/adr-0044-adapters-on-the-brain-without-a-node.md
[adr49]: ../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md
[ui-12.1]: 2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: 2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-14]: 2026-10-06-ui-architecture-design.md#14-amendment-2026-10-07-dmd-round-approved-message-alerts-amends-121-alert_card-and-the-u2-legal-check
[brief]: ../references/design/2026-10/brief/50-vehicle-f-trips.md
[vds]: 2026-10-07-visual-design-system-design.md
[vds-8]: 2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[vds-13]: 2026-10-07-visual-design-system-design.md#13-design-language-themes-amendment-2026-10-07
[dm-4.3]: 2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[ts-5.4]: 2026-10-07-trip-sharing-design.md#54-stats-from-the-visible-trace-only-r6
[tokens]: ../ui/tokens/data.tokens.json
