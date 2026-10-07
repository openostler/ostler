---
title: "Maintenance and fuel trackers — what a Maintenance & Garage add-on should hold"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/addons_catalogue.md, references/research/features_backlog.md, references/research/ui/obd_apps.md, references/research/ui/vehicle_data_model.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Reviews consumer maintenance, fuel and cost trackers (MyAutoLog/carmaintenance.app, Fuelly, aCar, Drivvo, Simply Auto, Road Trip MPG, myCARFAX, FIXD; LubeLogger and Tracktor for the landscape; Autozen turns out to be a driving launcher, not a tracker): schedules by distance, time and hours, reminders, fault-linked tasks, fuel economy, costs, attachments, multi-vehicle, sharing, CSV formats and business models. None of them reads the car; Ostler can. Sketches an optional Maintenance & Garage app fed by odometer, engine hours, DTCs and battery voltage with honest provenance, plus Styling and Copy/Avoid/Decide.
---

# Maintenance and fuel trackers (October 2026)

R6 of the ecosystem research. It asks what the **Maintenance & Garage** add-on (owner's
direction: services, reminders by distance/time/hours, fault-triggered tasks, fuel and
costs) should hold, by looking at what drivers already use. Facts were checked live on
**2026-10-07** unless marked **(U)** (unverified). Diagnostic-app garages are covered in
[ui/obd_apps.md](ui/obd_apps.md); the add-on list is in [addons_catalogue.md](addons_catalogue.md).

**Headline.** Every popular tracker is a *typing* app: the driver keys in odometer, litres
and cost. None reads the car (FIXD reads codes but its "maintenance" is a generic
schedule). Ostler already holds a logbook, DTCs with freeze frames, battery voltage and,
where the car reports it, the odometer. That is the gap to fill, provided we are honest
about where each number came from.

## 1. The apps at a glance

| App | Platforms | Schedules / reminders | Fuel and costs | Files | Multi-vehicle / sharing | Export | Business model |
|---|---|---|---|---|---|---|---|
| **MyAutoLog** (carmaintenance.app, Tapronix LLC) [S1, S2] | iOS; Android in rollout | time, mileage or both; service presets plus custom | MPG, cost per vehicle, EV charging sessions | receipt photos, documents (registration, insurance, inspection) | free = 1 vehicle; Pro up to 15; no sharing mentioned | **PDF** service history (Pro); no CSV found | free + Pro monthly/yearly or lifetime (iPhone); adds an AI assistant |
| **Fuelly** (iOS, Fuelly LLC) [S3] | iOS + fuelly.com | custom service reminders | MPG in many units, gas price, expense and service charts | photos and PDFs (Premium) | multi-vehicle; public fuelly.com profiles | **CSV** by e-mail; photos are lost on export (user review) | free with ads; Premium $0.99/mo or $7.99/yr |
| **aCar** (Android, now Fuelly LLC) [S4, S5, S6] | Android | time and mileage reminders (oil, air filter …); a reminder can be auto-created from a service record | fuel, services, expenses, trips | — | multi-vehicle; cloud backup via fuelly.com | **CSV** and HTML; full backup `.abp`; imports many other apps | ads + IAP; old one-off Pro buyers now nagged to subscribe |
| **Drivvo** [S7, S8] | Android, iOS, web | reminders for services, inspection, insurance, tax | fuel, expense **and income**, routes | (U) | multi-vehicle; fleet plan with driver assignment and checklists | **CSV/PDF** reports; imports aCar, Fuelio, Fuel Manager, My Cars | personal "free forever"; fleet $42/vehicle/yr |
| **Simply Auto** [S9] | iOS, Android, web | distance- or time-based, custom categories | fuel by octane/brand/station, EV kWh, GPS trip log for tax mileage | receipts (Drive storage on top tier) | unlimited vehicles and **multi-driver sync** on top tier | **CSV import and export** | Gold $9.99 one-off; Platinum $9.99/yr or $29.99 one-off |
| **Road Trip MPG** (Darren Stone) [S10] | iOS | maintenance and expense reminders | fuel economy | (U) | (U) | **CSV import/export/backup** | **$7 one-off, no ads, no subscription** |
| **myCARFAX** [S11] | iOS, Android, web | **manufacturer schedule** looked up from the plate; push and e-mail | — | — | multiple cars | — | free; fed by ~26,000 partner shops that write service history in (US) |
| **FIXD** [S12] | iOS, Android + $39.99 dongle | mileage-based reminders | — | — | (U) | — | Premium $12.99/mo or $99.99/yr: repair cost estimates, issue forecast, emissions pre-check |
| **LubeLogger** (self-hosted) [S13, S14] | web | date, odometer or whichever first; 4 urgency tiers; recurring, "fixed interval" | fuel, service, repair, upgrade, tax, supplies, planner | attachments | collaborators per vehicle | CSV import with column aliases; e-mail and **webhook** alerts; shop calendar | free, open source |
| **Tracktor** (self-hosted) [S15] | web (Svelte, Node, SQLite) | renewal reminders for insurance and inspection documents | refuelling and maintenance logs, dashboard | documents | multi-vehicle, small fleets | (U) | free, open source; ~918 stars, last push April 2026 |
| **Autozen** [S16] | Android | — | — | — | — | — | free; it is a **driving launcher** (maps, media, calls, messages, speed cameras, Coolwalk-style split, speedometer layouts), not a tracker. Relevant to Drive mode, not here |

Others seen but not reviewed: Fuelio (Sygic; CSV backup, a converter ecosystem [S17]),
WhenService (engine-hour reminders for boats [S18]), Autosist. The Speedometer: Driving
Tracker app's **Garage** tab is the styling benchmark (§6).

## 2. Feature by feature

### 2.1 Schedules: distance, time, engine hours

- **Distance + time, "whichever first"** is universal (MyAutoLog, aCar, Simply Auto,
  LubeLogger). Users expect both on every item.
- **Engine hours** are almost absent from car apps. Only boat/plant apps (WhenService)
  offer them. A Td5 that idles off-road, tows or winches wears by hours, not miles; this is
  a gap Ostler can fill because it sees RPM. VSS already has
  `Vehicle.Powertrain.CombustionEngine.EngineHours` (time with rpm > 0) and `IdleHours`
  [S19].
- **"From last done" vs "fixed interval"**. LubeLogger's fixed-interval option stops a
  renewal date drifting when you pay early. Needed for MOT, tax and insurance; oil should
  re-base from the actual service.
- **Manufacturer schedules** come only from myCARFAX (a licensed US database keyed by
  plate) and FIXD (generic). Everyone else ships presets the user edits. Nobody shares
  community schedules as open data.

### 2.2 Reminders

- Urgency tiers beat a single due date. LubeLogger: Not urgent (> 30 days / > 100 mi),
  Urgent, Very urgent (< 7 days / < 50 mi), Past due; thresholds are configurable [S14].
- Delivery: push + e-mail (myCARFAX), e-mail + webhook (LubeLogger), calendar view
  (LubeLogger). aCar can **create the next reminder automatically when a service is
  logged**, which removes the commonest chore.
- Reminders are **"due in X km"** only if the app knows today's odometer. Typing apps guess
  from the last fill-up; that is why their reminders drift.

### 2.3 Fault- or OBD-triggered tasks

- **Nobody links a fault code to a maintenance task.** FIXD shows codes with severity and
  separately sends mileage reminders; myCARFAX tracks recalls. A "P0401 seen → task:
  check EGR, with freeze frame attached → closes when the code stays away for N drives"
  loop does not exist in any app reviewed.

### 2.4 Fuel logs and economy

- Fields everyone uses: date, odometer, quantity, total price, **partial fill**, **missed
  fill-up**, station/brand, tags, notes, location. Economy is computed only between two
  full fills; a partial or missed flag breaks the chain honestly (Fuelly, LubeLogger).
- Units: Fuelly offers MPG US/UK/CA, L/100 km, km/L and more [S3]. UK users need MPG
  (UK) and litres together.

### 2.5 Expenses and total cost of ownership

- Categories (fuel, maintenance, repair, insurance, tax, parking, tolls, fines, finance)
  and charts per month are standard. Drivvo adds **income** (ride-share drivers). Cost per
  km and "this year vs last" are the insights people share (Speedometer's Garage shows
  total vehicle cost, this-month split, top category and costliest month).

### 2.6 History, attachments, multi-vehicle, sharing

- A per-vehicle **timeline** of services, repairs, fuel and documents is the home screen of
  most trackers. Receipts as photos/PDFs are usually a paid tier; **exports often drop
  them** (Fuelly review) [S3].
- Multi-vehicle is the main paywall lever (MyAutoLog free = 1 car; Simply Auto top tier).
- Sharing is weak: Simply Auto multi-driver sync, LubeLogger collaborators, Drivvo's fleet
  driver assignment. None offers a time-boxed share for a buyer or a mechanic.

### 2.7 Import/export formats (CSV columns)

Verified columns:

- **Fuelly fuel-up CSV export** (unit names follow the account; also accepted by
  LubeLogger) [S20]: `car_name, model, mpg|l/100km, odometer, miles|km,
  gallons|litres, price, city_percentage, fuelup_date, date_added, tags, notes,
  missed_fuelup, partial_fuelup, latitude, longitude`. Fuelly imports fuel-ups only, not
  services [S5].
- **LubeLogger fuel import aliases** [S13]: date (`date`, `fuelup_date`, or day/month/year),
  `odometer|odo`, quantity (`gallons|liters|litres|consumption|quantity|qty|fuelconsumed`),
  cost (`cost|total cost|totalcost|total price`), `notes|note`,
  `partial_fuelup|partial tank|partial_fill`, `isfilltofull|filled up`,
  `missedfuelup|missed_fuelup|missed fill up|missed_fill`, `tags`.

Not verified (no public spec found): aCar `.abp` backup and its CSV, Drivvo CSV, Simply
Auto CSV, Road Trip CSV, Fuelio's sectioned CSV. Converters exist on GitHub (FuelioImport
reads aCar `.abp` and Drivvo CSV [S17]; aCarConverter), which suggests the formats are
stable but undocumented. **(U)**

Takeaway: there is no standard. A tolerant **alias-based importer** (LubeLogger's
approach) is the only practical way in; Fuelly's column set is the closest thing to a
lingua franca for fuel.

### 2.8 Business models

| Model | Who | User reaction |
|---|---|---|
| One-off purchase | Road Trip ($7), Simply Auto Gold/Platinum one-off | liked; "no subscription" is a selling line |
| Freemium, ads + Premium | Fuelly, aCar | anger when one-off buyers were moved to subscriptions and features (location, photos) went behind them [S6]; aCar's recent Play rating is reported very low [S4] **(U)** |
| Free, fleet pays | Drivvo | works at scale (claims 5 M+ users) |
| Free, data/shops pay | myCARFAX | free to user; the history belongs to the platform |
| Hardware + subscription | FIXD ($39.99 + $99.99/yr) | the costliest; sells fear (repair estimates, forecasts) |
| Open source, self-hosted | LubeLogger, Tracktor | strong homelab following; no phone-native UX |

## 3. What Ostler has that they don't

| Car data | Where it comes from today | Honest caveat |
|---|---|---|
| **Odometer** (`Vehicle.TraveledDistance`) | OBD PID `A6` on some cars; BMW E IKE `17` ([vehicle packs spec](../../specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md)) | `A6` is often missing ([vehicle_data_model.md](ui/vehicle_data_model.md)); **not read on the D2 Td5 today**. Fallback: a user-entered anchor plus logbook distance (GPS or road speed), labelled as an estimate |
| **Engine hours** | derived from the logbook: time with rpm > 0, and idle time (speed 0, rpm > 0) | counts only while Ostler was connected; needs a user anchor ("hour meter read X on date"); idle definition is ours (VSS leaves it open [S19]) |
| **DTCs + freeze frames** | Diagnose, Mode 03/07/0A, KWP on the D2; snapshot before clear ([UI spec](../../specs/2026-10-06-ui-architecture-design.md) Tier 1) | the code and the time it appeared/cleared are proven; the cause is not |
| **Battery voltage** | engine ECU / PID `42` / node ADC | resting voltage needs the car asleep; cranking dip needs a fast sample (node). A trend, not a battery test |
| **Trips** | logbook sessions ([ADR-0009](../../decisions/adr-0009-session-logbook-and-location.md)) | distance per trip; location opt-in |
| **Fuel level** | PID `2F` where present | missing on many cars; a jump while parked suggests a fill-up, nothing more |
| **Service interval reset** | a Tier 1 Maintenance action ([ADR-0033](../../decisions/adr-0033-action-categories-and-approvals.md)) | pack-specific; the D2 has none yet |

## 4. Sketch: what the Maintenance & Garage app should hold

An optional first-party app (`ostler-app-maintenance`, [app model §3, §7](../../specs/2026-10-06-app-model-design.md)),
stored per `vid` on the device that owns the vehicle ("data stays home",
[accounts spec §4](../../specs/2026-10-06-accounts-sharing-design.md)). The shell's
Garage page (More → Garage) stays the vehicle list; this app adds a **Maintenance** tab per
vehicle and a **cost card** slot on the garage card.

### 4.1 Data model (one store per vehicle)

| Record | Key fields | Notes |
|---|---|---|
| `meter_reading` | `kind` (odometer, engine_hours), value, unit, time, **`source`** (`vehicle`, `logbook_estimate`, `user`, `import`), confidence (`proven`/`candidate`, ADR-0006) | every derived number points back to readings |
| `task_template` | name, category, intervals `{km, months, engine_hours}`, rule `first_of`, `basis` (`from_last` or `fixed`), lead thresholds, `source` (`pack`, `user`, `community`) | a pack ships templates as data |
| `task` (open item) | template or ad hoc, due values, urgency, **`trigger`** (`schedule`, `dtc:<code>`, `battery`, `user`), links (DTC snapshot id, session id) | urgency maps to the unified status words where possible (ADR-0008) |
| `service_record` | date, odometer, engine hours, items done, parts (part number, brand), labour, cost, who (self, garage name), closes task ids, attachments | completing it re-bases the next task (aCar pattern) |
| `fuel_record` | date, odometer, quantity, unit, price, full/partial/missed, station, location (opt-in), notes | Fuelly-compatible fields |
| `expense` | date, category, amount, currency, recurring?, attachment | insurance, tax, MOT, parking, parts |
| `document` | kind (MOT, insurance, V5C, receipt, manual page), expiry, file | expiry feeds a fixed-basis task |
| `attachment` | file hash, MIME, size, local path | photos/PDFs kept on the device; export includes them |

### 4.2 Behaviours

1. **Odometer ladder.** Use the car's odometer when the pack reports one (proven); else
   last user anchor + logbook distance since (candidate, shown as "≈ 182,450 km, estimated
   from trips since 3 Oct"); prompt for a fresh reading at a fill-up or service.
2. **Engine hours** are "Ostler-observed hours since anchor" plus the user anchor. Offer
   idle hours as a separate figure (a Td5 that idles a lot gets an hours-based oil task).
3. **Fault-linked tasks.** When a new confirmed DTC appears, **suggest** a task (one tap)
   carrying the code, freeze frame and session. The task shows "not seen for N drives"
   after a fix and offers to close; a return of the same code reopens it. Clearing codes
   stays the Tier 1 Maintenance action with its audit entry; the task links that entry.
4. **Battery task.** If resting voltage trends below a pack threshold over several
   nights, or the cranking dip deepens, suggest "Test battery / check charging". Words:
   "trend", never "battery failing".
5. **Fill-up prompt.** On Parked, if fuel level jumped, offer "Log fill-up?" pre-filled
   with odometer and place name (location only if opted in).
6. **Service interval reset.** Logging an oil service on a car whose pack declares the
   reset action offers it (Tier 1, Parked or Idling) and records it on the service.
7. **Notifications** go through the node's notifier ladder (backlog #4: ntfy, Telegram,
   SMS) and Home Assistant: publish `Vehicle.Service.IsServiceDue`,
   `DistanceToService`, `TimeToService` (VSS [S19]) so HA users get it for free.
8. **Driving lockout.** Editing and lists run Parked or Idling. While Moving only the
   **alert card** template shows, and only at trip start or end ("Oil service due in
   300 km"), never mid-drive.

### 4.3 Manufacturer schedules as pack data

Schedules belong to the **vehicle pack** (ADR-0013 contract), as a
`maintenance.json` of task templates under the pack's CC BY-SA data licence
([ADR-0012](../../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md)).
Written by the community from owners' knowledge and cited sources, never copied from a
copyrighted handbook. `generic_obd2` ships a short generic set (oil, filters, brake fluid,
coolant, MOT). D2 Td5 intervals are not stated here: they need sourcing **(U)**.

### 4.4 Import, export, sharing

- **Import**: an alias-based CSV importer seeded with Fuelly and LubeLogger columns
  (§2.7), with a preview and unit picker; aCar/Drivvo/Fuelio later, from user-supplied
  samples.
- **Export**: CSV per record type (Fuelly-compatible fuel CSV) + a JSON bundle with
  attachments (zip) + a printable service-history page. Never drop attachments.
- **Integration**: a LubeLogger push (its API) for homelab users, the "own webhook" way
  out of [accounts spec §7](../../specs/2026-10-06-accounts-sharing-design.md).
- **Sharing**: a new data class `maintenance` on the share levels (accounts spec §5.3):
  off by default, included in `view+logs` only if ticked. A **mechanic** person invite may
  add service records (attributed). A time-boxed **"service history for a buyer"** share,
  no VIN, no locations.

### 4.5 Business

Free and AGPL like the rest; no paywall on vehicle count, export or attachments. If Ostler
Cloud sells anything here, sell sync and off-device backup of attachments, not the user's
own history.

## 5. Where the other trackers fall short (complaints to design against)

- Reminders drift because the odometer is guessed (all typing apps).
- Export loses photos (Fuelly).
- Paid features moved behind subscriptions after purchase (aCar/Fuelly).
- History locked to a platform or shop network (myCARFAX).
- Fear-selling and repair estimates (FIXD Premium).
- Self-hosted tools look like admin panels on a phone (LubeLogger) **(U, from demo)**.

## 6. Styling

What the apps look like, and what to borrow:

- **Speedometer: Driving Tracker, Garage tab** (owner's benchmark; screenshot reviewed):
  dark navy gradient, one **hero number** ("Total vehicle cost 15K, this year 4.3K"), a
  **donut** for this month split three ways (fuel, maintenance, expenses) with percentages
  and a "−10 % vs last month" delta, three **spending tiles** each with its own "+ Add",
  then an **Insights** list (vs year average, top category, costliest month). Bottom tab
  bar with a lit pill for the active tab. Borrow all of it: hero number, donut, tile with
  inline add, insight rows.
- **MyAutoLog**: clean light cards, presets as icon chips, a health/overview dashboard and
  home-screen widgets [S1]. Borrow the preset chips for "log service".
- **Fuelly/aCar**: chart-heavy, dated, ad slots. Avoid the density; keep the economy
  chart with partial-fill gaps shown honestly.
- **Drivvo**: colour per record type in a single timeline **(U)**. Borrow: one timeline
  per vehicle, colour = record type (fuel, service, repair, expense, fault).
- **LubeLogger**: tables and tabs per record type, urgency colour badges. Borrow the
  four urgency badges, not the table layout.

For Ostler: the dark theme from the UI overhaul, a garage card showing **next due item +
cost this month**, a Maintenance tab ordered *Due → Timeline → Costs → Documents*, urgency
as coloured pills using the status palette, and provenance as a small suffix ("est.",
"from car", "you") rather than a separate column.

## 7. Copy / Avoid / Decide for Ostler

### Copy

| Item | From | Maps to |
|---|---|---|
| Distance + time + **engine hours**, whichever first; from-last vs fixed basis | LubeLogger, aCar, WhenService | §4.1; new app spec |
| Auto-create next task when a service is logged | aCar | §4.2 |
| Four urgency tiers with configurable thresholds | LubeLogger | ADR-0008 vocabulary; §4.1 |
| Partial / missed fill-up flags; Fuelly-compatible fuel CSV | Fuelly, LubeLogger | §2.7, §4.4 |
| Alias-based CSV import with preview | LubeLogger | §4.4 |
| Hero total cost, donut, tiles with inline add, insight rows | Speedometer Garage | UI spec §4.1 garage card; §6 |
| One-off or free; no vehicle-count paywall | Road Trip, LubeLogger | ADR-0012 |

### Avoid

| Item | Why | Maps to |
|---|---|---|
| Showing an estimated odometer as if read from the car | data honesty | CONSTITUTION; ADR-0006 |
| Mid-drive reminder pop-ups | driver distraction | UI spec §3.5 lockouts; app model §4.4 |
| Exports that drop attachments | lock-in | §4.4 |
| Feature regressions behind subscriptions | trust (aCar) | ADR-0012 |
| Copying handbook schedules verbatim | copyright | ADR-0012 data licence |
| Sharing maintenance history by default, or with VIN/locations | privacy | accounts spec §5.3; ADR-0036 |

### Decide (recommendations for the owner)

1. **Where the app lives.** Recommend an optional first-party app `ostler-app-maintenance`
   (app model §3, §7), with the shell's Garage page keeping the vehicle list and gaining a
   cost/next-due card slot. Not core: many users only diagnose.
2. **Odometer when the car does not report one.** Recommend the ladder in §4.2: user
   anchor plus logbook distance, always labelled "estimated" (candidate), with a prompt for
   a fresh reading at each fill-up or service.
3. **Engine hours.** Recommend "Ostler-observed hours + user anchor", publishing
   `EngineHours` and `IdleHours` with candidate confidence; hours-based intervals offered
   on every task template.
4. **Fault-triggered tasks: suggest or create?** Recommend **suggest** (one tap) for every
   new confirmed DTC; auto-reopen a closed task only when the same code returns.
5. **Manufacturer schedules.** Recommend task templates as **vehicle-pack data**
   (`maintenance.json`, ADR-0013 contract, CC BY-SA, ADR-0012), community-sourced with
   citations; `generic_obd2` ships a generic set.
6. **Interop first.** Recommend Fuelly fuel CSV (import and export) and LubeLogger CSV
   import first, plus an export bundle (CSV + JSON + attachments). aCar/Drivvo/Fuelio
   importers only from user-donated samples.
7. **Sharing.** Recommend a new `maintenance` data class, off by default in every share
   level, and a time-boxed "service history for a buyer" share; mechanic invites may add
   attributed records (accounts spec §5).
8. **Signed history (later).** Recommend deferring a signed service-history export
   (Ed25519, ADR-0041) until the Brain signs anything else; note it as the answer to
   "can a buyer trust this log?".
9. **Notifications.** Recommend publishing VSS `Vehicle.Service.*` to MQTT/Home
   Assistant and using the node notifier ladder (backlog #4); in-car only as an alert card
   at trip start/end.

## Sources (checked 2026-10-07)

- [S1] carmaintenance.app/mobile-app — MyAutoLog features and Pro tier.
- [S2] carmaintenance.app — Tapronix LLC, PDF export, document storage, lifetime unlock.
- [S3] App Store, Fuelly: MPG & Service Tracker (id295905460) — features, Premium prices, CSV export, review on lost photos.
- [S4] apppricinglab.com, aCar (com.zonewalker.acar) — features, CSV/HTML export, Fuelly LLC; reported Play rating.
- [S5] Fuelly forums, "Importing Services" (search snippet) — services export-only.
- [S6] justuseapp.com Fuelly reviews; Fuelly forum "aCar premium subscription says Pro" — subscription complaints.
- [S7] drivvo.com/en/personal-use — free personal features, imports, CSV/PDF.
- [S8] drivvo.com/en/pricing — fleet $42/vehicle/yr.
- [S9] App Store, Simply Auto (id893278325) — features and Gold/Platinum prices.
- [S10] App Store / AlternativeTo, Road Trip MPG (id298398207) — $7 one-off, CSV.
- [S11] autoshopowner.com and press coverage of myCARFAX service reminders.
- [S12] FIXD app listings (mwm.ai, apppricinglab) — Premium $12.99/mo or $99.99/yr, $39.99 sensor.
- [S13] docs.lubelogger.com, Fuel Records — CSV aliases.
- [S14] docs.lubelogger.com, Reminders — metrics, urgency tiers, fixed intervals, webhook.
- [S15] mariushosting.com and gittrend.io on Tracktor (javedh-dev/tracktor).
- [S16] autozenapp.com — launcher features.
- [S17] github.com/marten-cz/FuelioImport README — converts aCar `.abp`, Drivvo CSV.
- [S18] App Store, WhenService (id6757406729), via search snippet — engine-hour reminders.
- [S19] COVESA VSS `spec/Vehicle/Service.vspec`, `spec/Powertrain/CombustionEngine.vspec`, `spec/VehicleSignalSpecification.vspec` (master).
- [S20] Fuelly forums, "CSV export column names mismatched" (search snippet) — export columns.
