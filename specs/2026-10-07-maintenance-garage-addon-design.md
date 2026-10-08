---
title: "Maintenance & Garage add-on — services, reminders, fuel, costs and documents fed by the car — design"
area: specs
status: stable
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-api-consistency-design.md, specs/2026-10-06-u0-seams-design.md, decisions/adr-0006-english-confidence-vocabulary.md, decisions/adr-0008-unified-status-vocabulary.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0041-brain-ed25519-signing.md, references/research/maintenance_trackers.md, references/research/code_review_lubelogger.md, references/research/code_review_tracktor.md, references/research/app_teardown_speedometer.md, references/research/driver_distraction_rules.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all"). Maintenance & Garage (`ostler-app-maintenance`, optional first-party add-on) tracks services, reminders, fuel, costs and documents per vehicle, fed by the car where it can be. Own schema (SI units, ISO 8601, `vid`, `source`, confidence) with records for meter readings, task templates, tasks, services, fuel, expenses, generic compliance documents (MOT, insurance, tax as kinds) and attachments. A reminder engine over distance, engine hours, time and "fault seen", whichever first, with four urgency bands and fixed or rolling intervals, translated from LubeLogger with its defects fixed (MIT notice, `AGPL-3.0-or-later AND MIT` REUSE header). Fuel economy full-to-full as total distance over total fuel. An odometer and engine-hours ladder (car value, else user anchor plus Trips distance, labelled estimated). Fault-triggered task suggestions that close after N clean drives and reopen if the code returns. Manufacturer schedules as vehicle-pack data (`maintenance.json`). Garage screens in the Speedometer style; reminders on a Home card, strip chip, notifications and VSS `Vehicle.Service.*`, in the car only at trip start or end. Fuelly and LubeLogger CSV import/export and an export bundle; a `maintenance` data class off by default, a time-boxed buyer share and mechanic records; an optional LubeLogger bridge later; signed history deferred. Phases, tests and decisions. Amended 2026-10-07 (openness round, ADR-0047): the visual tokens are the default look and the add-on may style its own pages.
---

# Maintenance & Garage add-on — design

**Status:** approved by the owner on 2026-10-07 ("approve all"), v0.2. Not built before U1, U6 (garage) and app-model UA.
**Owner direction:** a maintenance tracker add-on; of LubeLogger and Tracktor, "we can use
the code likely". Evidence: [maintenance trackers](../references/research/maintenance_trackers.md),
[LubeLogger review](../references/research/code_review_lubelogger.md),
[Tracktor review](../references/research/code_review_tracktor.md),
[Speedometer teardown](../references/research/app_teardown_speedometer.md) §3.6.
Ecosystem framing: [ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) (accepted). Every other tracker is a typing app; this one reads
odometer, engine hours and faults from the car and says where every number came from.

## 1. Scope and boundaries

- **Own repo** `ostler-app-maintenance` (ADR-0034), Python service on the Brain (in the phone
  app on Ostler Diagnostics alone) plus a React UI bundled into the shell (app model §3, §7).
- **Reads from core:** the garage (`vid`, U6), the odometer/engine-hours series written by
  **Trips** (§4), fault events and snapshots from Diagnose, the pack's `maintenance.json`
  (§6), the data-class registry ([accounts-sharing spec §14](2026-10-06-accounts-sharing-design.md#14-amendment-2026-10-07-approved-one-permission-model-and-the-shell-screens), approved).
- **Never** touches the car itself. The one car action it offers, a pack's service-interval
  reset, is requested through the shell's action API and the gate (Maintenance, Tier 1).
- **Tracktor:** ideas and schema shape only (generic compliance documents, stable
  notification keys, the three-step CSV mapping wizard). **LubeLogger:** two engines
  translated (§3, §5), CSV interop, an optional bridge later (§11). Nothing else is copied.

## 2. Schema

Stored per device in `maintenance.db` (SQLite, WAL, schema-versioned; app storage), one row
set per `vid`, on the device that owns the vehicle ("data stays home", accounts spec §4).
JSON Schemas (2020-12) in the app repo; routes follow the api-consistency spec.

**Common fields on every record:** `id` (ULID), `vid`, `created_utc`, `updated_utc` (RFC 3339),
`source` (`vehicle` · `logbook_estimate` · `user` · `mechanic` · `import:<format>` · `pack` ·
`bridge:lubelogger`), `author` (user id or `car`), `confidence` (`proven` · `candidate`,
ADR-0006), `tags[]`, `notes`, `attachments[]` (ids).

**Units:** distance in **m**, time and engine time in **s**, volume in **L**, energy in
**kWh**, money as integer minor units plus an ISO 4217 code. Converted only at the edge
(display, CSV), per the user's unit preferences.

| Record | Main fields | Notes |
|---|---|---|
| `meter_reading` | `kind` (`odometer`, `engine_hours`, `idle_hours`), `value`, `at_utc` | the ladder (§4) and every due computation point back to these |
| `task_template` | `name`, `category` (oil, filters, fluids, brakes, tyres, belts, battery, compliance, other), `interval {distance_m?, engine_s?, months?, days?}`, `basis` (`rolling` · `fixed`), `lead {urgent, very_urgent}` per axis (optional), `on_fault[]` (DTC patterns), `citation` (required when `source: pack`) | shipped by packs, written by users |
| `task` | `template_id?`, `title`, `due {at_date?, at_m?, at_engine_s?}`, `band` (§3), `trigger` (`schedule` · `fault:<code>` · `battery_trend` · `user`), `state` (`open` · `suggested` · `watching` · `closed`), links (`dtc_snapshot_id`, `session_id`, `clear_audit_id`) | the reminders users see |
| `service_record` | `date`, `odometer_m?`, `engine_s?`, `items[]` (part no., brand, qty), `labour`, `cost`, `who` (self, garage name), `closes_task_ids[]`, `kind` (`service` · `repair` · `upgrade`) | completing it re-bases rolling tasks |
| `fuel_record` | `at_utc`, `odometer_m`, `volume_l` (or `energy_kwh`), `cost`, `fill` (`full` · `partial`), `missed_before` (bool), `station?`, `place?` (opt-in, place name only) | Fuelly-compatible |
| `expense` | `date`, `category` (insurance, tax, parking, tolls, fines, finance, parts, other), `amount`, `recurring?` | |
| `document` | `kind` (`roadworthiness` e.g. MOT · `insurance` · `registration_tax` · `emissions` · `warranty` · `other` + label), `issuer`, `number` (local only, never shared), `valid_from`, `valid_to` (ISO 8601 dates), `cost?` | expiry creates a **fixed** task; its alert can be resolved, not dismissed (Tracktor) |
| `attachment` | `sha256`, `mime`, `size`, local path, `stripped` (EXIF removed copy for sharing) | photos and PDFs; export always includes them |

A published **LubeLogger mapping table** (service, repair, upgrade, fuel, tax→expense,
odometer, reminder→task) is part of the schema docs; LubeLogger's model is not our storage.

## 3. Reminder engine

Translated from LubeLogger's `Helper/ReminderHelper.cs` at `dd69e59b` into
`ostler_app_maintenance/reminders.py` (LubeLogger review §3, §8).

- **Axes:** distance, engine hours, time, and **fault seen**. Distance, hours and time are
  independent (not LubeLogger's per-vehicle hours flag); a task is due on **whichever comes
  first**. A template's `on_fault` patterns make a matching confirmed DTC raise the task to
  `very_urgent` at once and attach the snapshot.
- **Bands** (four, ADR-0008 words in the UI): `not_due`, `urgent`, `very_urgent`,
  `past_due`. Default leads, configurable per vehicle and per template: urgent within 30 d,
  1 500 km or 20 h; very urgent within 7 d, 500 km or 5 h. The result carries signed
  remainders per axis and which axis fired.
- **Fixed vs rolling:** `rolling` re-bases on the completing service record's date, odometer
  and hours (aCar/LubeLogger); `fixed` advances from the previous due point by whole
  intervals until after the completion (MOT, insurance, tax do not drift when paid early).
- **Notifications fire only on a band change**, keyed `task:<id>:<band>` with upsert and
  stale-key clean-up (Tracktor), so restarts and syncs never re-notify.

**Defects fixed against the source** (each with a regression test):
1. Custom thresholds no longer leak: leads are resolved **per task**, never carried across
   the loop.
2. **Inclusive comparisons:** due at exactly now, or exactly the current odometer or hours,
   is `past_due`.
3. **Current odometer from the ladder** (§4), not the maximum of all records; a reading more
   than 2 000 km or 10 % off the ladder is flagged as an outlier and asks for confirmation.
4. **iCal** feed escapes `,` `;` `\` and newlines (RFC 5545 §3.3.11) and writes date-only
   events with `VALUE=DATE`.
5. **One calendar rule:** months are added with end-of-month clamping and days as days, in
   the vehicle's local date, on every path.
6. Recurrence is settable through our API (LubeLogger's API cannot set it).

**Licence:** the translated files carry REUSE headers
a file copyright line for "2026 OpenOstler contributors",
a second for "2024 Hargata Softworks" and
the licence expression "AGPL-3.0-or-later AND MIT" (REUSE header tags); the app repo's
`THIRD_PARTY_LICENSES.md` names the repo, commit `dd69e59b`, the source files and the MIT
notice; `LICENSES/MIT.txt` is present; `reuse lint` passes in CI (ADR-0025).

## 4. Odometer and engine-hours ladder

Trips writes an **odometer and engine-hours series as platform data** (core, per `vid`); this
app reads it and never asks for typing it can avoid.

| Rung | Odometer | Engine hours | Label |
|---|---|---|---|
| 1 | `Vehicle.TraveledDistance` from the pack | `Vehicle.Powertrain.CombustionEngine.EngineHours` where reported | "from car" (proven) |
| 2 | last user anchor + Trips distance since (GPS or road speed) | user anchor + Ostler-observed time with rpm > 0; idle (speed 0, rpm > 0) kept separately | "≈ 182 450 km, **estimated** from trips since 3 Oct" (candidate) |
| 3 | last recorded value, no trips since | same | "as of <date>" |

A fresh reading is asked for at each fill-up and service. Distance driven without Ostler
connected is invisible to rung 2, so the label always says "estimated". The D2 Td5 does not
report an odometer today; it lives on rung 2.

## 5. Fuel economy

Translated from LubeLogger's `Helper/GasHelper.cs` (same header and notice as §3) into
`fuel.py`: full-to-full windows; partial fills accumulate distance and fuel to the next full
fill; a `missed_before` flag closes the window with **no figure**. The headline economy is
**total distance ÷ total fuel over complete windows** (Tracktor), not a mean of per-tank
figures. Shown as L/100 km, mpg (UK), mpg (US) or km/L. A window whose odometer came from
rung 2 is labelled estimated; gaps are drawn as gaps. EV energy follows later.

## 6. Faults and manufacturer schedules

**Fault-triggered suggestions.** A new confirmed DTC (Diagnose or a Trips fault event)
**suggests** a task in one tap, carrying the code, freeze frame snapshot and session; a
matching `on_fault` template pre-fills it. After a linked service or a clear (the ADR-0033
Tier 1 Maintenance action, whose audit entry is linked), the task moves to `watching` and
shows "not seen for N clean drives" (default **N = 3**). A **clean drive** is a trip in which
the module that set the code was actually read and the code was absent; a trip without that
read does not count. At N it offers **Close**; the same code returning reopens the task (or,
after 180 days closed, opens a new one linked to it). A battery task is suggested on a
resting-voltage or cranking-dip **trend**, never "battery failing".

**Manufacturer schedules as pack data.** A vehicle pack may ship `maintenance.json`: an array
of `task_template` objects (§2) with `applies_to` (engine, market, years), required
`citation`, and `confidence`, validated by `schemas/maintenance.schema.json`, under the pack's
CC BY-SA data licence (ADR-0012). Community-sourced, never copied from a handbook.
`generic_obd2` ships a generic set (oil, filters, brake fluid, coolant, roadworthiness test);
D2 Td5 intervals wait for sourcing **(U)**. User edits override pack templates per vehicle.

## 7. Garage screens

Speedometer Garage style (teardown §3.6); colours, ramps and type from the visual design system's tokens by default (2026-10-07 visual design spec); as an add-on it may style its own pages freely (visual §11 and §13, amended 2026-10-07, openness round, [ADR-0047](../decisions/adr-0047-openness-round.md)).

- **Garage card** (shell garage, new slot): next due item with its band pill, cost this
  month.
- **Maintenance home per vehicle:** **total cost** hero with "this year" sub-line; **this
  month donut** (fuel, maintenance, expenses in category tokens) with delta vs last month;
  three **category tiles** each with its own **+ Add**; **Insights** rows (vs year average,
  top category, costliest month, cost per km); a **Due** list; a **Records** card linking to
  Trips → Statistics → Records (sprints live in Trips, not here).
- Tabs: **Due · Timeline · Costs · Fuel · Documents**. One timeline, colour = record type;
  provenance as a small suffix ("from car", "est.", "you", "mechanic").
- Parked head unit: a kiosk-style Due view (LubeLogger kiosk idea); editing and lists run
  Parked, or Idling **with Park evidence**; while Moving nothing but §8's alert card.

## 8. Reminder delivery

| Surface | Rule |
|---|---|
| **Home card** | next due item per active vehicle; band pill |
| **Strip chip** | appears only at `very_urgent` or `past_due`; opens the Due list |
| **Notifications** | on band change only (§3), through the phone's native push and the node notifier ladder (ntfy, Telegram, SMS) per the owner's choices |
| **VSS / MQTT / HA** | publishes `Vehicle.Service.IsServiceDue`, `Vehicle.Service.DistanceToService`, `Vehicle.Service.TimeToService`; engine hours to service in an Ostler overlay path (ADR-0016) |
| **In the car** | `alert_card` **only at trip start or trip end** ("Oil service due in 300 km"), ≤ 2 lines, never mid-drive |

## 9. Import and export

- **Import:** an alias-based CSV importer seeded with the Fuelly and LubeLogger header tables
  (LubeLogger review §4; trackers §2.7), in a three-step wizard: upload, map columns and
  units, preview. Tolerates locale dates (with an explicit date-order pick), currency symbols
  and space-separated tags. It **merges** (dedupe on date + odometer + amount), never
  replaces, and validates against the JSON Schemas. aCar, Drivvo and Fuelio only from
  user-donated samples.
- **Export:** Fuelly-compatible fuel CSV; LubeLogger-shaped CSVs for service, repair,
  upgrade, fuel, odometer and tax with ISO dates and plain decimals; an **export bundle**
  (zip: our JSON, the CSVs, **all attachments**, a printable history page). Export never
  drops attachments and is never paywalled.

## 10. Sharing

- The **`maintenance`** data class (accounts §14.1: detail `history · with costs`, never in a
  preset), **off by default** for every audience. This app proposes two further ticks per
  grant, **documents** and **attachments**, unticked by default (Decision 9). Document
  numbers, the VIN (masked or not), the plate and locations are never in it (ADR-0036).
- **Buyer share** (the registry's "for a buyer" preset, no locations): time-boxed (default 7
  days, max 30), read-only service history: records,
  due list, odometer series rounded to 1 000 km, document kinds and dates; audited, revocable.
- **Mechanic invites:** a time-boxed Mechanic person invite may **add** service records,
  attributed (`source: mechanic`, author), never edit or delete the owner's. Remote peers
  cannot write; a remote mechanic sends a proposed record the owner accepts.
- Service-interval reset (if the pack declares it) is offered after logging an oil service:
  Maintenance, Tier 1, through the gate, local links only.

## 11. Later

- **`ostler-app-lubelogger` bridge** (optional, off by default): pushes odometer and hours at
  trip end, pulls reminders into Due, and with a per-vehicle opt-in turns a confirmed DTC into
  a Critical plan. Local or Tailscale only, an Edit-scoped key in the Brain's secret store
  sent as `x-api-key` (never a query string), `culture-invariant` header.
- **Signed history** (Ed25519, ADR-0041): deferred until the Brain signs other exports; the
  answer to "can a buyer trust this log?".

## 12. Phases

| Phase | Ships | Depends on |
|---|---|---|
| **M0 Seams** | Trips odometer/hours series; `maintenance.json` schema in the pack contract; `maintenance` class used from the registry; garage-card and Home-card slots | U0/U6, accounts §14 registry, app model UA |
| **M1 Records** | schema, timeline, odometer ladder, services, fuel + economy, expenses, documents, attachments, Garage screens, export bundle | M0 |
| **M2 Reminders** | engine (§3), bands, notifications, VSS `Vehicle.Service.*`, alert card, fault suggestions | M1; Diagnose fault events |
| **M3 Interop and schedules** | CSV wizard (Fuelly, LubeLogger), LubeLogger-shaped export, `generic_obd2` schedule | M1 |
| **M4 Sharing** | `maintenance` grants, buyer share, mechanic records | accounts P2 |
| **M5 Bridge** | `ostler-app-lubelogger` | M2 |

## 13. Tests

- The six defects of §3 each have a failing-then-passing test; reminder tables from
  LubeLogger review §3 reproduce with inclusive bounds.
- Full-to-full: partial chains, a missed fill (no figure) and total ÷ total against hand sums.
- Ladder: rung 2 values are always `candidate` and labelled estimated; an outlier reading is
  flagged, not adopted.
- Fault loop: N clean drives closes; a trip without the module read does not count; the code
  returning reopens.
- No alert card while Moving except at trip start or end; editing refused Idling without Park
  evidence.
- Export bundle round-trips through import with every attachment; Fuelly and LubeLogger
  sample CSVs import with no LubeLogger code.
- No VIN, plate, document number or location in any share response; `reuse lint` passes.

## Changelog

- 2026-10-07: v0.1, first draft for owner review (ecosystem drafts).
- 2026-10-07: v0.2, approved by the owner on 2026-10-07 ("approve all"): every §14 decision
  answered as recommended (alternatives not chosen); `maintenance.json` is added to the
  vehicle-pack contract (ADR-0013 amendment, 2026-10-07); the LubeLogger bridge add-on
  `ostler-app-lubelogger` is listed in ADR-0034, not yet created.
- 2026-10-07: v0.3, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", ADR-0047): §7's tokens are the default look; the add-on may style its own
  pages.

## 14. Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **Own app and schema?** Recommend: `ostler-app-maintenance` with our own SI schema and a
   published LubeLogger mapping. Alternative: adopt LubeLogger's model as our storage.
2. **Translate or clean-room the two engines?** Recommend: translate LubeLogger's reminder and
   fuel-economy engines with the MIT notice and `AGPL-3.0-or-later AND MIT` header, defects
   fixed. Alternative: reimplement from the review in our own words, courtesy line only.
3. **Reminder axes.** Recommend: distance, engine hours, time and fault seen, whichever first,
   four bands, fixed or rolling. Alternative: distance and time only at first.
4. **Default urgency leads.** Recommend: urgent 30 d / 1 500 km / 20 h, very urgent 7 d /
   500 km / 5 h, configurable. Alternative: LubeLogger's 100/50 distance units as given.
5. **Odometer without a car value.** Recommend: user anchor + Trips distance, always
   "estimated", prompted at fill-ups and services. Alternative: typed readings only.
6. **Fault-triggered tasks.** Recommend: suggest in one tap, close after 3 clean drives,
   reopen when the code returns. Alternative: create automatically.
7. **Manufacturer schedules.** Recommend: `maintenance.json` as optional vehicle-pack data
   (CC BY-SA, cited), a pack-contract addition. Alternative: a separate community schedule
   repo.
8. **In-car reminders.** Recommend: alert card only at trip start or end; strip chip only at
   very urgent or past due. Alternative: no in-car reminders at all.
9. **Sharing.** Recommend: `maintenance` off by default with extra ticks for documents and
   attachments, buyer share ≤ 30 days, mechanic adds attributed records locally (remote
   mechanics propose). Alternative: no sharing until signed history exists.
10. **LubeLogger bridge.** Recommend: optional `ostler-app-lubelogger` after M2.
    Alternative: CSV interop only.
11. **Signed history.** Recommend: defer until the Brain signs other exports (ADR-0041).
    Alternative: sign exports from M1.
