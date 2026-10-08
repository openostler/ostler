---
title: "Core screens adoption — the owner's Home, Drive mode, Logs and log summary designs in the web UI, with a Map tab and per-log stats — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [references/design/2026-10/core-screens/README.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-logs-at-scale-design.md, references/design/2026-10/brief/50-vehicle-f-trips.md]
summary: >
  Draft. Adopts the owner's core screens design (references/design/2026-10/core-screens) into the existing web UI (`ui/`): Home, Drive mode, the Logs list and a new log summary, all on the existing tokens and layout classes. Every frame is adopted except the HU-5 Moving message alert. The owner's changes: Trips is called Logs; Security leaves the nav and Map (the telemetry map we already have, `TraceMap`) takes its place, so the nav is Home, Diagnose, Logs, Map, More, with Security under More (hidden until a node reports); opening a log shows a summary first (distance hero, 3×3 stats with sustained best, time-at-speed donut, signal chart, map sheet on the passenger side) and Play back enters the existing replay. Backend: a new `GET /sessions/{id}/stats` reusing the trip-sharing stats code for the owner's own view, adding idle time, time and distance per speed band and sustained best, cached in the session index. Drive mode keeps its Moving rules (no sparklines while Moving). Five PRs: nav and Map tab, stats and log summary, Logs list, Home, Drive mode, each with checks and screenshots against the design. Open questions on Security's place, the Map tab default, the Statistics tab scope and the design file (PNG renders kept, not the 4.5 MB HTML).
---

# Core screens adoption — design

**Status: draft, v0.1, for the owner's approval.** It turns the owner's design of
2026-10-08 ([core screens][design], kept as PNG renders of each section) into build work on the web UI
we already have. It does not redesign: where the design and an approved spec agree, it points to
the spec; where they differ, it says which wins and why.

## 1. Context

The design draws four core screens for the reference car (2002 Discovery 2 Td5, right-hand
drive): **01 Home**, **02 Drive mode**, **03 Trips** (list) and **04 Trip detail**, on phone
(393×852), HU-7 (1024×600, Parked) and HU-5 (800×480, Moving). Nav items on head units sit in a
rail on the driver's side (right on this car); on the phone they are a bottom bar. Maps sit on
the passenger side (left).

It fits [ADR-0049][adr49]: Ostler is a diagnostic and logging platform, not an operating
system. The app shape it builds towards, recorded in ADR-0049 v1.2, is one Ostler app with Home, Diagnose (with Decode), Logs, Map, More and Drive mode,
the same on phone and head unit. The web UI here is that app's reference build: the screens
and their data contracts carry over to the Android app (ADR-0050) unchanged.

Most of the design was already specified: the trip list, detail and playback in
[UI §12.2][ui-12.2] and the designer brief ([trips-detail][brief]), the donut and trip detail
restyle in [visual §8 and §10][vds], the Drive mode rules in [drive modes §4.3][dm-4.3] and the
stats in [trip sharing §5.4][ts-5.4]. This spec records what the owner chose on top of them.

## 2. What is adopted

**Adopted:** every frame of 01 Home, 02 Drive mode (phone and HU-5 Moving), 03 Trips and
04 Trip detail, as the default look (themes may restyle it; [visual §13][vds-13]).

**Not adopted:** "HU-5 · Moving · message alert (text never shown)". Message alerts are not
part of this work (ADR-0049 dropped the Phone app); any future alert card follows
[UI §14][ui-14] under its own spec.

**The owner's changes** (all binding on this spec):

1. **Trips is called Logs** everywhere, as the UI already does. The destination id, routes and
   strings stay `logs`; [UI §12.2][ui-12.2]'s rename to Trips is not carried out.
2. **Security leaves the nav. Map takes its place**: the telemetry map we already built. By
   default Security becomes an entry under More, still hidden until a node reports (open
   question 1).
3. **Opening a log shows its summary first** (top speed and the other figures), not replay.
   **Play back** on the summary enters the existing replay.

**Design notes the build corrects:**

- The speed ramp in the design is a placeholder violet ramp ("swap them once you have §4.3").
  The build uses the token ramp `speed-1` … `speed-6` in [`data.tokens.json`][tokens]
  ([visual §3.3][vds]), already used by `speedColors()` in
  [`trace.ts`](../ui/src/components/replay/trace.ts) (lines 45–67).
- The design uses Material Symbols **Rounded**; the repo ships the outlined set. Icons keep
  the repo's set and names.
- Drive mode draws sparklines while Moving. [Drive modes §4.3][dm-4.3] (unchanged
  by the openness round) allows no sparkline and no animation while Moving. The build draws the
  arc gauge and range bar while Moving and adds the sparkline only Parked and Idling (§9).

## 3. Navigation

The nav becomes **Home · Diagnose · Logs · Map · More**, on every class.

- [`ui/src/shell/destinations.ts`](../ui/src/shell/destinations.ts): replace the `security`
  entry (order 40) with `map` (`icon: "map"`, route `map`, `trust: "core"`, no `requires`).
  `MAX_DESTINATIONS` stays 5.
- [`ui/src/shell/routes.ts`](../ui/src/shell/routes.ts): add `map`, `logs.detail` and
  `more.security`; `DestinationId` swaps `security` for `map`. The old `security` route stays
  for one release as an alias that opens `more.security`.
- **Security under More** (default): a More row ("Security", `shield`) that opens
  `more.security`, rendering today's [`Security.tsx`](../ui/src/destinations/Security.tsx). The
  row carries the same `requires: { devices: [{ kind: "node" }] }`, so it stays hidden until a
  node reports, as today.
- [`Nav.tsx`](../ui/src/shell/Nav.tsx) and [`layoutClass.ts`](../ui/src/shell/layoutClass.ts)
  are unchanged: the rail sits on the driver's side on `hu5`, `hu7`, `hu9`, `huwide`, `tablet`
  and `desktop`, the bottom bar on `phone`.

## 4. Map tab

A new destination, `ui/src/destinations/Map.tsx`: [`TraceMap`](../ui/src/components/replay/TraceMap.tsx)
full screen under the strip, with its legend.

| State | What the map shows |
|---|---|
| A drive in progress | The live session's trace, re-fetched as [`LiveAnalysis`](../ui/src/screens/Analysis.tsx) does, the marker on the live GPS fix, following it |
| No drive, logs exist | The last log's trace, framed to its `bbox`; a chip names it and opens its summary |
| Replay active | The replayed log, following the replay cursor (`useReplay().t`) |
| No GPS anywhere | The empty state of `LiveAnalysis`: "No location yet" |

- **Colour by** speed (default, the six speed-ramp bands of the user's unit) or a picked signal,
  with the existing `ChannelPicker` and `Legend`.
- **Basemap switch** (`BasemapSwitch`, Streets / Satellite / Hybrid); the style follows the theme
  ([`mapStyle.ts`](../ui/src/components/replay/mapStyle.ts): OpenFreeMap dark or positron).
- **Moving on a driver-facing head unit:** TraceMap's existing `drive` mode (no gestures, no
  basemap switch, follows the cursor), the `map` template of [drive modes §4.3][dm-4.3].
- The map logic moves out of `Analysis.tsx` into a shared hook, so Map and Analysis draw the
  same thing from one place.

## 5. Logs list

[`Logs.tsx`](../ui/src/screens/Logs.tsx), [`SessionBrowser.tsx`](../ui/src/components/replay/SessionBrowser.tsx)
and [`SessionList.tsx`](../ui/src/components/replay/SessionList.tsx), restyled per frame 03:

- **Logs | Statistics** segmented control at the top. It replaces today's Sessions | Analysis
  toggle in [`LogsDestination.tsx`](../ui/src/destinations/LogsDestination.tsx); Analysis stays
  reachable from the summary (Play back) and from Rewind.
- **Last 14 days strip:** one cell per day, filled by kilometres, today outlined; total km and
  log count beside it. Data: `GET /sessions/histogram?group=day&year=…` (two calls across a
  year end). Tapping a day scrolls the list to it.
- **Day groups:** "Today", "Yesterday · Tue 6 Oct", then dates; each header carries the day's
  km and log count.
- **Rows:** mini map of the route (trace in the speed ramp, `bg` fallback), start → end place,
  start time · km · duration, and **MAX** speed on the trailing edge. Two columns on HU-7 and
  wider. The search, filters and month scrubber stay (behind the filter button on phone).
- **Opening a row** goes to `logs.detail` (§6). The drive in progress still opens live
  Analysis, as `open()` does today (lines 25–28).
- **Statistics** (first cut, open question 3): the year heatmap and totals over the index for
  a period (distance, logs, time, moving, idle, average and max speed). Records and sprints wait.
- Parked only on driver-facing head units, as [UI §12.1][ui-12.1] says today.

## 6. Log summary (`logs.detail`)

A new route and screen, `ui/src/screens/LogSummary.tsx`, per frame 04. `Logs.open()` changes
from `replay.enter(id); goTo("logs.analysis")` to selecting the log and `goTo("logs.detail")`.
`goTo` takes a route name only, so the selected log id lives in Logs state (beside the
browser view it already keeps) and in the URL, so Back and a reload return to the same log.

**Layout.** On landscape classes: the map fills the screen and the sheet sits on the
**passenger side** (left on RHD; it follows the rail side setting), about 40 % of the width.
On phone: the map on top (about 40 % of the height), the sheet below, scrolling. The map is
`TraceMap` coloured by speed, with start and end markers, no cursor.

**Sheet, top to bottom:**

1. Back, title (start → end place, or the log's name), date and time range, **Play back**.
2. **Hero:** distance (`type-num-xl`).
3. **3×3 grid:** distance, average speed, max speed / duration, idle, moving / elevation gain,
   stops, average moving speed. **Sustained best** sits beside max speed as a second line
   ("best 30 s 91").
4. **Time at speed:** donut in the six speed-ramp bands of the user's unit, with a
   **Time / Distance** segmented control; legend rows give band label, value and %
   ([visual §8][vds-8] row "Donut").
5. **Signal chart:** speed over time by default; a picker of Speed, Coolant, Boost and Battery
   (from the log's channels, by VSS role; missing ones are not offered) plus "More…" for any
   recorded channel (the existing `ChannelPicker`). Gaps are drawn as gaps; the max is labelled.
6. Faults seen, notes and "About this trip" follow [UI §12.2][ui-12.2] later; not in this work.

**Play back** calls `replay.enter(id)` and then `goTo("logs.analysis")`: the existing replay
([`replay.tsx`](../ui/src/state/replay.tsx), [`playback.ts`](../ui/src/state/playback.ts),
[`Transport.tsx`](../ui/src/components/replay/Transport.tsx)), unchanged.

**States:**

- **Loading:** map on `bg`, skeleton sheet; meta from `GET /sessions/{id}` renders first, the
  stats fill in.
- **No GPS:** no map; the sheet becomes the page with "No location in this log". Distance and
  speeds come from the ECU road speed when recorded, else show "—".
- **Partial channels:** a figure without its source shows "—" with a short reason on focus
  (for example "No altitude recorded"); the donut needs a speed source, else it is hidden.
- **Recording now:** the summary is not offered; the row opens live Analysis.
- **Error:** "Could not load this log" with Retry; Back works.

## 7. Backend: per-log stats

**Endpoint.** Recommend **`GET /sessions/{id}/stats`**, not new fields on `GET /sessions/{id}`.
Meta is cheap and read by the list, public mode and replay; the stats need the full recording
for older logs, and a separate call lets the summary show meta at once and the stats when
ready. It also keeps `SessionMeta` stable for the Android app. Public mode: `filtered`, like
`/sessions/{id}/data`.

**Reply** (unrounded numbers; the UI rounds per [trip sharing §5.4][ts-5.4]'s L1–L4 column):

```json
{ "v": 1, "speed_source": "gps|ecu|none", "distance_m": 37200, "duration_s": 2880,
  "moving_s": 2640, "idle_s": 240, "avg_kmh": 46.5, "avg_moving_kmh": 50.7,
  "max_kmh": 96, "sustained_best_kmh": 91.2, "gain_m": 412, "stops": 3,
  "unit": "km/h", "bands": [ {"lo": 0, "hi": 30, "time_s": 410, "distance_m": 1900}, … ] }
```

**Code.** Reuse, do not copy: `trace_stats()`, `elevation_gain_m()` and `no_gps_stats()` in
[`share/trace.py`](../src/openostler/logbook/share/trace.py), today used only by
[`share/bundle.py`](../src/openostler/logbook/share/bundle.py). A new
`src/openostler/logbook/stats.py` computes the owner's view: a `VisibleTrace` built straight
from `fixes(rows)` (no ends trim, no privacy zones; `visible_trace()` refuses a trim below
200 m, so it is not called), and for no-GPS logs the whole trip integrated (the 2-minute edges
are a sharing rule, passed as a parameter defaulting to 0 here and unchanged for shares).

**Definitions** (as [trip sharing §5.4][ts-5.4] where it already defines them):

| Figure | Definition |
|---|---|
| Moving time | time at ≥ 5 km/h (`MOVING_KMH`) |
| Idle time | duration − moving time: stationary time inside the log |
| Average speed | distance ÷ duration; **average moving** = distance ÷ moving time, which is what `trace_stats()` calls `avg_kmh` (the design's 46 vs 51 km/h) |
| Max speed | max of the speed source (ECU road speed when recorded, else GPS) |
| Sustained best | the fastest average over any 30 s window: distance in the window ÷ 30 s; windows with a gap > 5 s are skipped |
| Time at speed | per band of `SPEED_BANDS` in the user's unit (trace.ts lines 52–60): time, and distance, of samples whose speed falls in the band; speed from the speed source, each sample weighted by the interval to the next |
| Elevation gain | 30 s median filter, sum of rises ≥ 3 m |
| Stops | still periods ≥ 60 s |

Bands are returned for the unit asked (`?unit=km/h|mph`, default the user preference), so one
colour means one speed, as the ramp requires.

**Cache.** Computed when a log ends and stored in the session index
([`index.py`](../src/openostler/logbook/index.py)) as a `stats` JSON column with its version
`v`; computed on first request for older logs and when `v` changes. The index can always be
rebuilt from recordings. Today only `distance_km`, `duration_s` and `max_speed_kmh` are stored
([`recorder.py`](../src/openostler/logbook/recorder.py) lines 1091–1100).

**Contract and tests.** `api/openapi.yaml` gains the path and a `SessionStats` schema
([api/README](../api/README.md)). Tests: `tests/test_session_stats.py` on synthetic fixtures
(moving, idle, stops, sustained best, band totals equal duration and distance, no-GPS with ECU
speed, no speed at all, mph bands), the API contract test, and `tests/test_share_trace.py`
unchanged and passing (shares keep their behaviour).

## 8. Home

[`Home.tsx`](../ui/src/destinations/Home.tsx) restyled per frame 01, on existing tokens and
layout classes:

- Faults banner (count and the first fault names), opening Diagnose → Faults.
- Vehicle card: photo (placeholder until set), name, year · engine · gearbox · drive side,
  **odometer** with an "Estimated" chip when it is not read from the car.
- **Drive** card ("Full-screen gauges · 6 tiles"), opening Drive mode.
- Stat tiles: battery, fuel average, coolant (live); 7 days km, logs in 7 days, drive time,
  average speed, max speed, idle % (from the index and §7's cached stats over the last 7 days).
  A tile with no source is hidden, not zero.
- Last log (mini map, start → end, km · duration), opening its summary; Add-ons card.
- HU-7: banner and vehicle card left, tiles and last log right; HU-wide keeps the vehicle pane.

## 9. Drive mode

[`Drive.tsx`](../ui/src/screens/Drive.tsx) and [`ui/src/drive/`](../ui/src/drive/) restyled
per frame 02, for the Diagnostic preset's six tiles (boost, coolant, battery, intake air, fuel
now, trip):

- Top strip: back, faults chip, module chip (TD5), REC, Ghost, clock, bookmark.
- Tiles: label, value with unit, an arc gauge or range bar with the normal band; the alarm
  state (intake air "HIGH") as border and value colour plus the word, never colour alone.
- The Trip tile shows km and duration, no bar.
- **Moving rules unchanged** ([drive modes §4.3][dm-4.3]): ≤ 6 tiles, no scrolling, labels
  ≥ 24 px and the class's number floor, no glow, no animation, **no sparkline** (shown only
  Parked and Idling), refresh ≤ 4 Hz. The render check and no-scroll tests must pass on phone
  and HU-5.

## 10. Build order

Five PRs, each small and reviewable. Every PR: `cd ui && npm run check`, `npm run e2e`,
`pytest -q`, `reuse lint`, the docs scripts, and Playwright screenshots at phone (393×852),
HU-7 (1024×600) and HU-5 (800×480) compared by eye with the design frames and attached to
the PR. All styling goes through tokens (`ui/tokens/*`), Figtree and Material Symbols: no raw
colours, no px font sizes (the stylelint ratchet).

| PR | Scope | Acceptance |
|---|---|---|
| 1 | Nav and Map tab (§3, §4) | Nav reads Home, Diagnose, Logs, Map, More on every class; Security under More hidden without a node; old `security` route opens `more.security`; Map follows a live drive (fixture), shows the last log, follows replay; e2e for each |
| 2 | Stats endpoint and log summary (§6, §7) | `/sessions/{id}/stats` matches the definitions on fixtures; OpenAPI updated; opening a log lands on the summary; Play back enters replay at the start; no-GPS and partial states render |
| 3 | Logs list (§5) | Logs \| Statistics, 14-day strip, day groups, rows with MAX; drive in progress still opens live Analysis; existing logs e2e green |
| 4 | Home (§8) | Frame 01 at phone and HU-7, Night and Day; hidden tiles without sources; stylelint ratchet not raised |
| 5 | Drive mode (§9) | Frame 02 at phone and HU-5 Moving; no sparkline while Moving; render check and no-scroll tests pass |

## 11. Open questions for the owner

1. **Where Security goes.** Default: a More row, hidden until a node reports. Alternatives: a
   Map layer (alarm events and tracker on the Map tab), or a sixth destination shown only with
   a node.
2. **Map tab with no drive.** Default: the last log. Alternatives: the current position only, or
   the last 7 days of logs together.
3. **Statistics tab scope.** Default first cut: year heatmap and period totals. Alternative: the
   full [UI §12.2][ui-12.2] Statistics (hero, distribution, records, sprints) in PR 3.
4. **The design file.** Following the hand-off folder's 2 MB rule, the repo keeps PNG
   renders of each section, not the 4.5 MB HTML bundle (which also carries the design tool's
   runtime under an unknown licence). The owner keeps the HTML; the maps render blank in the
   PNGs because tiles were offline. Alternative: commit the HTML anyway.

## Changelog

- 0.1 (2026-10-08): first draft from the owner's core screens design and changes.

[design]: ../references/design/2026-10/core-screens/README.md
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
