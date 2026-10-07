---
title: "Code review: LubeLogger (hargata/lubelog) — what Ostler can reuse for Maintenance & Garage"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0035-languages-by-tier.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, references/research/addons_catalogue.md, references/research/ui/obd_apps.md, REUSE.toml, THIRD_PARTY_LICENSES.md]
summary: >
  A read-only review of LubeLogger at dd69e59 (MIT, 2024 Hargata Softworks): an ASP.NET Core (.NET 10) MVC app with LiteDB or Postgres, jQuery and Bootstrap 5.3 (light, dark, system, drop-in CSS themes). It covers the data model (service, repair, upgrade, fuel, tax, odometer, reminders, plans, supplies, notes, equipment, inspections, extra fields, attachments), the reminder engine (date, distance or both; urgency thresholds; one real bug), CSV columns, the 74-method REST API with API keys, households and sharing, and the MIT-into-AGPL rules. Verdict: reimplement the reminder and fuel-economy logic in Python with a notice, read and write LubeLogger CSV, ship an optional LubeLogger bridge app, and copy nothing else.
---

# Code review: LubeLogger

**What it is.** LubeLogger is a self-hosted web app for tracking vehicle maintenance and fuel
([repo](https://github.com/hargata/lubelog); [docs](https://docs.lubelogger.com/)). About 2.9k
stars and 179 forks; MIT; C# (GitHub page, checked 2026-10-07). It is also packaged as a Home
Assistant OS add-on with ingress (a community "haos-apps" listing found by search, 2026-10-07;
not verified further). There is no official Home Assistant *integration* (entities); none found.

**What was read.** A shallow clone at `dd69e59b` (2026-09-12), read only and never built or run.
All paths below are relative to the repo root at that commit. This note feeds the planned
**Maintenance & Garage** add-on ([addons catalogue](addons_catalogue.md)) and the garage in the
[accounts spec §4](../../specs/2026-10-06-accounts-sharing-design.md). It does not repeat the
garage patterns in [obd_apps.md](ui/obd_apps.md).

## 1. Stack

| Layer | What LubeLogger uses | Where |
|---|---|---|
| Server | ASP.NET Core MVC on **.NET 10** (`net10.0`), Razor views, server-rendered partials | `CarCareTracker.csproj`, `Controllers/`, `Views/` |
| Storage | **LiteDB** 5.0.17 (one embedded document file) by default; **Postgres** (Npgsql) when `POSTGRES_CONNECTION` is set. Both sit behind `External/Interfaces/I*DataAccess.cs` | `Program.cs:43-47`, `External/Implementations/{Litedb,Postgres}` |
| CSV | CsvHelper 33 | `MapProfile/ImportMappers.cs` |
| Mail, auth | MailKit (reminder emails); OIDC login; JWT parsing | `Helper/MailHelper.cs`, `Models/OIDC/` |
| Push | SignalR hub at `/api/ws`; outgoing webhooks (generic or Discord) | `Program.cs:124,171`, `Logic/Event/EventLogic.cs` |
| Background | A hosted service for scheduled reminder emails, recurring taxes and clean-up | `Logic/Event/AutomatedEventLogic.cs`, `Enum/AutomatedEvent.cs` |
| Front end | jQuery, Bootstrap 5.3.2 and Bootstrap Icons, bootstrap-datepicker, bootstrap-tagsinput, Chart.js 4.4.1, SweetAlert2, Masonry, drawdown (Markdown), qrcode-generator, SignalR client | `Views/Shared/_Layout.cshtml:46-66`, `wwwroot/lib/` |
| Deploy | One Docker image (`ghcr.io/hargata/lubelogger`), port 8080, `/App/data` volume; also a Windows exe | `docker-compose.yml` |

About 18.5k lines of C# in controllers, helpers and logic, and 22 hand-written jQuery files.
Nothing of the stack fits Ostler's tiers (Python core and brain, TypeScript/React UI;
[ADR-0035](../../decisions/adr-0035-languages-by-tier.md)), so **porting files is off the
table. Only the logic is worth taking.**

## 2. Data model

Every record belongs to one `VehicleId` (an int). Most records carry `Tags` (a list of strings),
`Files` (a list of `{Name, Location, IsPending}`), and `ExtraFields` (a list of
`{Name, Value, IsRequired, FieldType}`).

| Record | Fields (beyond Id, VehicleId, Tags, Files, ExtraFields) | File |
|---|---|---|
| **Vehicle** | Year, Make, Model, LicensePlate, PurchaseDate/SoldDate, PurchasePrice/SoldPrice, IsElectric, IsDiesel, **UseHours** (the odometer counts engine hours), OdometerOptional, **OdometerMultiplier** and **OdometerDifference** (for a swapped cluster or a different unit), DashboardMetrics, VehicleIdentifier, ImageLocation, MapLocation | `Models/Vehicle/Vehicle.cs:5-41` |
| **Service / Repair / Upgrade** | All three share `GenericRecord`: Date, Mileage (int), Description, Cost (decimal), Notes, RequisitionHistory (supplies used). In code, Repair is named `CollisionRecord` | `Models/Shared/GenericRecord.cs:3-15`, `Models/Collision/CollisionRecord.cs` |
| **Fuel** (`GasRecord`) | Date, Mileage, **Gallons** (unitless in practice: litres when the user picks metric), Cost, IsFillToFull, MissedFuelUp, StartingSoc/EndingSoc (EV, defaults 20 and 80) | `Models/GasRecord/GasRecord.cs:5-25` |
| **Tax** | Date, Description, Cost, Notes, IsRecurring, RecurringInterval (months), CustomMonthInterval + unit | `Models/TaxRecord/TaxRecord.cs` |
| **Odometer** | Date, InitialMileage, Mileage, DistanceTraveled (derived), EquipmentRecordId (equipment fitted on that trip) | `Models/OdometerRecord/OdometerRecord.cs:5-15` |
| **Reminder** | Date, Mileage (the due point), Description, Notes, **Metric** (Date, Odometer, Both), IsRecurring, FixedIntervals, preset or custom distance and month/day intervals, optional per-reminder urgency thresholds | `Models/Reminder/ReminderRecord.cs:5-21` |
| **Plan** | A kanban card: Type (which record it becomes), Priority (Critical, Normal, Low), Progress (Backlog, InProgress, Testing, Done), Cost, linked reminder ids, DateCreated/Modified | `Models/PlanRecord/PlanRecord.cs`, `Enum/PlanPriority.cs`, `Enum/PlanProgress.cs` |
| **Supply** | Date, PartNumber, PartSupplier, Quantity (decimal), Description, Cost; may be shop-wide (VehicleId 0). Records that consume supplies log a requisition | `Models/Supply/SupplyRecord.cs` |
| **Note** | Description, NoteText (Markdown optional), Pinned | `Models/Note/Note.cs` |
| **Equipment** | Description, IsEquipped (e.g. a trailer or winter tyres; per-item distance follows from odometer records) | `Models/EquipmentRecord/EquipmentRecord.cs` |
| **Inspection** | A checklist from a template: text, check or radio fields, a fail flag per option, and an optional action item that becomes a plan | `Models/InspectionRecord/*.cs` |
| **Extra fields** | Per record type, the admin defines named fields (Text, Number, Decimal, Date, Time, Location) and marks them required | `Models/Shared/RecordExtraField.cs`, `Enum/ExtraFieldType.cs` |

**Design notes for Ostler.**
- **No units are stored.** Distance, fuel and currency are plain numbers whose meaning comes from
  user settings (`UseMPG`, `UseUKMPG`, `PreferredGasUnit`; `appsettings.json`). Mileage is an
  `int`. Fuel economy converts litres to UK gallons inline (`Helper/GasHelper.cs:154`). This
  breaks our data-honesty rule. We store SI (km, L, ISO 8601, ISO 4217) and convert only at the edge.
- **Engine hours replace distance.** It is one flag per vehicle, so a vehicle cannot have both
  distance and hours reminders (a Td5 with a hydraulic winch, or a boat, needs both). Ostler
  should treat distance, time and engine hours as three independent axes.
- **Equipment is a good idea:** fitted kit with its own distance (a trailer, roof tent, winch or
  tyre set). It maps onto Ostler add-on devices with service lives.

## 3. Reminder logic (the part worth reimplementing)

The whole engine lives in `Helper/ReminderHelper.cs` (175 lines).

**Urgency** (`GetReminderRecordViewModels`, lines 77-173). It compares the due point with
`now` and with the **current odometer**. That odometer is the highest mileage across all service,
repair, fuel, upgrade and odometer records (`Logic/VehicleLogic.cs:107-140`). Default thresholds
(`Models/Reminder/ReminderConfig.cs`): Urgent within **30 days** or **100 distance units**; Very
urgent within **7 days** or **50 units**. A server-wide config or per-reminder custom thresholds
override them.

| Metric | Order of checks | Lines |
|---|---|---|
| Date | Past due if due < now; Very urgent if due < now+7 d; Urgent if due < now+30 d | 137-152 |
| Odometer | Past due if due < odo; Very urgent if due < odo+50; Urgent if due < odo+100 | 153-169 |
| Both | Past due (date, then distance); Very urgent (date, then distance); Urgent (date, then distance). The view records which axis fired. Whichever comes first wins | 100-136 |

The result carries `DueDays` and `DueMileage` (signed remainders) and the urgency enum
(`Enum/ReminderUrgency.cs`: NotUrgent 0, Urgent 1, VeryUrgent 2, PastDue 3).

**Recurrence** (`GetUpdatedRecurringReminderRecord`, lines 17-76). The next due point is the
base plus the interval. The base is the date and odometer of the **service record that
completed it** (`Controllers/Vehicle/ServiceController.cs:48-53` pushes linked reminders back),
or the old due point when `FixedIntervals` is set or the push-back is automatic
(`Controllers/Vehicle/ReminderController.cs:17-46`, opt-in `EnableAutoReminderRefresh`).
Preset intervals are enums (`Enum/ReminderMileageInterval.cs`: 50 to 150,000;
`Enum/ReminderMonthInterval.cs`: 1 to 60 months), plus a custom count in months or days.

**Notifications.** A scheduled job emails reminders whose urgency is in a chosen set. It caches
`(id, urgency)` so that a reminder is sent again only when its urgency changes
(`Logic/Event/NotificationLogic.cs:218-263`). Reminders also export to iCal at `/api/calendar`
(`Helper/StaticHelper.cs:931-975`).

**Defects to fix when we reimplement.**
1. **Custom thresholds leak into later reminders.** `reminderUrgencyConfig` is set once before
   the loop (line 80) and overwritten by a reminder's custom thresholds (lines 83-86). It is never
   reset, so every reminder after that one in the list uses those thresholds too.
2. **Strict `<`.** A reminder due at exactly the current odometer or date is not past due
   (lines 102, 107, 139, 155).
3. **The odometer is "max of all records".** One typo (an extra digit) makes every
   distance reminder past due. Ostler has a measured `Vehicle.TraveledDistance` where the
   car reports one; we should prefer it and flag outliers.
4. **The iCal export** does not escape commas, semicolons or newlines in SUMMARY (RFC 5545 §3.3.11),
   and writes all-day events as local date-times without `VALUE=DATE`.
5. **Days vs months mix.** Custom month and day intervals truncate to `.Date` only on the Both
   path (lines 30, 34), but not on the Date path (67, 71).

**Fuel economy** (`Helper/GasHelper.cs:33-250`) uses the standard full-to-full method. Partial
fills accumulate distance and fuel until the next full fill (lines 193-216). A missed fill-up
resets the accumulators and yields no figure (lines 185-191). Economy is distance over volume,
or 100 over that for L/100 km. The EV path estimates the energy used from the SoC deltas and
an implied battery capacity. It is sound and small; reimplement it.

## 4. Import and export (CSV), exactly

**Import** (`Controllers/Vehicle/ImportController.cs:679-…`, `MapProfile/ImportMappers.cs`):
headers are trimmed and lower-cased, and unknown columns are ignored. Accepted aliases (Fuelly-
compatible on purpose):

| Field | Accepted headers |
|---|---|
| Date | `date`, `fuelup_date`; or `day` + `month` + `year` |
| Odometer | `odometer`, `odo`; `initialodometer` |
| Fuel | `gallons`, `liters`, `litres`, `consumption`, `quantity`, `fuelconsumed`, `qty` |
| Cost | `cost`, `total cost`, `totalcost`, `total price`; else `price` × volume |
| Fill flags | `isfilltofull`, `filled up` (1/true/full); `partial_fuelup`, `partial tank`, `partial_fill` (1 = partial); `missed_fuelup`, `missedfuelup`, `missed fill up`, `missed_fill` |
| Other | `description`, `notes`/`note`, `tags` (**space-separated**), `startingsoc`, `endingsoc`, `partnumber`, `partsupplier`, `partquantity`, `type`, `priority`, `progress`, `datecreated`, `datemodified`, `isequipped` |
| Extra fields | any `extrafield_<Name>` column |

**Export column order** (`Helper/StaticHelper.cs`), each followed by `extrafield_<Name>` columns:

| Record | Columns |
|---|---|
| Service, Repair, Upgrade | `Date, Description, Cost, Notes, Odometer, Tags` (560-590) |
| Fuel | `Date, Odometer, FuelConsumed, Cost, FuelEconomy, IsFillToFull, MissedFuelUp, [StartingSoc, EndingSoc], Notes, Tags` (884-930) |
| Odometer | `Date, InitialOdometer, Odometer, Notes, Tags` (591-) |
| Tax | `Date, Description, Cost, Notes, Tags` (620-) |
| Supply | `Date, PartNumber, PartSupplier, PartQuantity, Description, Notes, Cost, Tags` (649-) |
| Plan | `DateCreated, DateModified, Description, Notes, Type, Priority, Progress, Cost` (684-) |
| Equipment | `Description, Notes, Tags, IsEquipped` (719-) |

**Caveat:** the export writes dates with `ToShortDateString()` and cost with `ToString("C")`,
a currency string such as "£12.50" (`ImportController.cs:266-268`). The import parses with
`DateTime.Parse` (line 733), so a file is only reliably portable between servers with the same
locale (`LUBELOGGER_LOCALE_OVERRIDE`, `Program.cs:23-32`). Our importer must accept culture
strings and currency symbols; our exporter should write ISO dates and plain decimals, which
LubeLogger's invariant parse also reads.

## 5. HTTP API

74 documented methods (75 distinct `/api` route paths in code; `wwwroot/defaults/api.json`, 14 categories). Each record
type has the same five calls: `GET …/all` (every vehicle), `GET /api/vehicle/<kind>?vehicleId=`
(filters: `id`, `startDate`, `endDate`, `tags`), `POST …/add?vehicleId=`, `PUT …/update`, and
`DELETE …/delete?id=`. Kinds: `servicerecords`, `repairrecords`, `upgraderecords`,
`gasrecords`, `taxrecords`, `odometerrecords`, `supplyrecords`, `planrecords`, `reminders`,
`equipmentrecords`, `notes`. Extras: `GET /api/vehicles`, `/api/vehicle/info` (summary with
reminder urgencies and costs), `/api/vehicle/odometerrecords/latest`,
`/api/vehicle/adjustedodometer`, `PUT …/odometerrecords/recalculate`, `/api/calendar` (iCal),
`/api/vehicle/reminders/send`, `/api/makebackup`, `/api/documents/upload`, `/api/whoami`,
`/api/info`, `/api/version`, `/api/extrafields`, `/api/tempfiles`, `/api/cleanup`, `/api/vehicle/taxrecords/check`, `/health` (anonymous), and a SignalR change feed at `/api/ws`.

- **Bodies** are JSON (`Consumes("application/json")`) or form posts. Every value is a
  **string** (`Models/Shared/ImportModel.cs`, the `*ExportModel` classes). The add-fuel call
  needs `date, odometer, fuelConsumed, cost, isFillToFull, missedFuelUp`
  (`Controllers/API/GasController.cs:146-157`). The add-reminder call needs `description` and
  `metric`, plus `dueDate` and/or `dueOdometer` (`Controllers/API/ReminderController.cs:102-140`).
  **Recurrence cannot be set through the API.**
- **Locale:** GET results are locale strings unless `LUBELOGGER_INVARIANT_API=true` or a
  `culture-invariant` request header is sent (e.g. `Controllers/API/TaxController.cs:44`; docs
  checked 2026-10-07). POST parsing stays culture-sensitive, so send ISO dates.
- **Auth** (`Middleware/Authen.cs:34-185`): with auth on, a cookie, HTTP Basic, or an API key in
  `x-api-key` **or the `apiKey` query string** (lines 57-61; paths `/api`, `/kiosk`, `/images`,
  `/documents`, `/temp`: `Helper/StaticHelper.cs:1118-1121`). Keys belong to a user and carry
  View, Edit and Delete permissions (`Models/API/APIKey.cs`, `Filter/APIKeyFilter.cs`). The
  docs call these roles Viewer, Editor and Manager. A 401 tells the client to use Basic.
- **Webhooks** POST `{type, timestamp, data, vehicleId, username, action}` for every add, update
  and delete (`Models/Shared/WebHookPayload.cs`), with 5 retries and back-off. They are **not signed**.

## 6. Multi-user and sharing

- **Auth is off by default** (`appsettings.json: "EnableAuth": false`). Every visitor is then
  given a root identity (`Middleware/Authen.cs:36-48`).
- A root user (credentials hashed in config, or OIDC), admins, and users who register with tokens.
- **Collaborators:** a vehicle is shared with named users (`Models/User/UserAccess.cs`). A
  collaborator has full access.
- **Households:** a parent user grants child users View (always), Edit and/or Delete over *all*
  the parent's vehicles (`Models/User/UserHousehold.cs`, `Logic/UserLogic.cs:155-179`).
- **Kiosk:** a read-only wall display that cycles vehicles, reminders and plans
  (`Enum/KioskMode.cs`, `Controllers/KioskController.cs`), refreshed over SignalR.
- **Password and API-key hashing is unsalted SHA-256** (`Helper/StaticHelper.cs:1023-1035`;
  `Logic/LoginLogic.cs:289,322`). Do not copy it. Our accounts spec uses scrypt or passkeys.

Compared with [ADR-0029](../../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md):
LubeLogger shares records only, with no roles, expiry or audit. Our role × share × token
intersection (accounts spec §3) is stricter, and is already the right design.

## 7. UI and styling

Bootstrap 5.3 with stock components. The top bar holds icon-plus-label tabs (Dashboard, Planner,
Odometer, Service, Repairs, Upgrades, Fuel, Supplies, Taxes, …) and the vehicle name on the right.
Each tab is a dense table with an Add button, and modals for editing. The dashboard has a row of
four stat tiles (last odometer, distance, total cost, average economy). Below them: a cost-by-type
pie, cost and distance by month (bars plus a line), a reminders-by-urgency donut, and fuel
economy by month, all in Chart.js (screenshots `docs/dashboard.webp`, `docs/reminder.webp`).
Urgency uses Bootstrap badge colours: green Not urgent, amber Urgent, red Very urgent, grey Past
due. The grey for past due is an odd choice; it reads as less urgent.

- **Colour modes:** `<html data-bs-theme>` is light, dark or system (`_Layout.cshtml:31,168`;
  `UserConfig.UseDarkMode/UseSystemColorMode`). Custom rules are written twice, once per mode
  (`wwwroot/css/site.css:422-776`).
- **Themes:** an admin drops a CSS file into `data/themes/`. Users pick one, and it is served at
  `/css/theme.css` (`Controllers/SharedDataController.cs`, `Helper/FileHelper.cs:71-85`).
  Themes are plain CSS overrides with no token contract.
- PWA manifest and icons; garage cards in a Masonry grid with an urgent-reminder badge;
  translations are JSON key maps (only `wwwroot/defaults/en_US.json` ships in the repo).

**Borrow:** the garage card with an urgency badge; the four-tile summary row; the "by urgency"
breakdown; the kiosk as a model for a **parked head-unit Maintenance view**; drop-in themes,
but as W3C design-token files, not raw CSS (our U1 tokens). **Don't borrow:** a desktop,
table-first layout, a tab bar of ten record types, modal-heavy editing, or jQuery. It looks
like a competent admin panel, the opposite of the dark, map-first look the owner wants.

## 8. Licence: MIT into AGPL-3.0-or-later

[ADR-0025](../../decisions/adr-0025-reuse-and-licences-pragmatic.md): permissive code may be
**copied anywhere, notice kept**. MIT is compatible with our AGPL-3.0-or-later core and with
the commercial dual licence ([ADR-0012](../../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md)),
because MIT allows sublicensing. `LICENSES/MIT.txt` already exists.

- **If we translate code** (the reminder engine or fuel economy, line by line into Python or TS),
  the file gets
  a file copyright line for "2026 OpenOstler contributors" +
  a second one for "2024 Hargata Softworks" and
  a licence identifier of "AGPL-3.0-or-later AND MIT" (REUSE header tags). Add an entry to
  `THIRD_PARTY_LICENSES.md` (repo URL, commit `dd69e59b`, source files, MIT, the notice text),
  then run `reuse lint`.
- **If we reimplement from this note** (behaviour and thresholds in our own words and
  structure), no notice is legally needed. A courtesy line in `THIRD_PARTY_LICENSES.md` costs
  nothing; add it.
- **CSV headers and API field names** are interface facts. Reading and writing them needs no notice.
- **Third-party code inside the repo** (only if we lifted the bundled files, which we should not):
  Bootstrap and Bootstrap Icons, jQuery, jquery-validation, jquery-validation-unobtrusive,
  Chart.js, Masonry, SweetAlert2, qrcode-generator, bootstrap-tagsinput (all MIT), drawdown
  (copyright Adam Leggett, no licence header in the file; upstream says MIT, unverified here),
  SignalR client (MIT, .NET Foundation), and **bootstrap-datepicker (Apache-2.0)**.
- **Brand:** the LubeLogger name, logos and icons (`wwwroot/defaults/*logo*`, `*icon*`) are
  the project's identity. Use the name only to describe compatibility ("works with LubeLogger"),
  never a logo, and never imply endorsement.

## 9. Recommendation

| Option | Verdict | Why |
|---|---|---|
| **Port code** to Python/TS | **Only two small pieces:** the reminder urgency and recurrence engine (~120 lines) and full-to-full fuel economy (~100 lines), rewritten into `ostler-app-maintenance` (Python, brain/core side), with the defects in §3 fixed and tests from §3's tables | Everything else is MVC and jQuery plumbing that fits neither our tiers nor our look |
| **Reuse schema** | **As an interop map, not our storage.** Keep our own records (SI units, ISO dates, `vid` from the garage, VSS-linked odometer and hours, a `source` field), and keep a mapping table to LubeLogger kinds: service, repair, upgrade, fuel, tax, odometer, reminder, plan, supply, note, equipment | Their unitless numbers and int odometer clash with data honesty |
| **Reuse CSV** | **Yes, both directions.** Import with the full alias table in §4 (which also brings Fuelly users). Export LubeLogger-shaped CSVs with ISO dates and plain decimals | Cheap, and users can leave in either direction |
| **Integrate via API** | **Yes, as an optional bridge app** (`ostler-app-lubelogger`, off by default; a brain-side Python service). It pushes odometer readings at trip end (`POST odometerrecords/add`, from `Vehicle.TraveledDistance`, with engine hours where `UseHours`). It pulls reminders (`GET /api/vehicle/reminders`) into the Maintenance view. It optionally creates a Critical repair **plan** when a DTC is confirmed. It sends `x-api-key` (Edit only) in the header, plus `culture-invariant` | Many self-hosters already run LubeLogger; we become its sensor feed instead of competing |
| **Ideas only** | Equipment with its own distance; inspection templates whose failures become plans; kiosk cycling; reminders that fire again only on an urgency change; iCal feed | — |

## Copy / Avoid / Decide for Ostler

**Copy**
- The three reminder axes with "whichever first" and a signed due remainder, the 30/7-day and
  100/50-unit urgency tiers as defaults, and a separate past-due state. Make the axes date,
  distance and **engine hours**. → Maintenance & Garage add-on ([addons catalogue](addons_catalogue.md));
  Maintenance runs Parked or Idling ([ADR-0033](../../decisions/adr-0033-action-categories-and-approvals.md)).
- Recurrence that restarts from the completing service record (date and odometer), with an
  opt-in fixed-interval mode. → same.
- Full-to-full fuel economy with partial and missed fill-ups. → Maintenance & Garage; Trips
  can show economy per tank.
- Notify only when urgency *changes*. → the notification rules in the app-model spec
  ([app model](../../specs/2026-10-06-app-model-design.md)).
- The CSV header aliases and export column orders in §4. → importer and exporter in the add-on.
- Equipment items with their own distance, and inspection checklists that create plans. → the
  add-on backlog ([features backlog](features_backlog.md)).

**Avoid**
- Unitless numbers, an int odometer, and locale-formatted dates or currency in files and APIs. →
  CONSTITUTION data honesty; SI internally ([ADR-0016](../../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md)).
- Auth off by default meaning root for everyone; API keys in query strings; unsalted SHA-256;
  unsigned webhooks. → [accounts spec](../../specs/2026-10-06-accounts-sharing-design.md) (scrypt
  or passkeys, scoped tokens, signed outbound hooks).
- A "max odometer of all records" as the truth. Use the measured signal, and flag outliers.
- The table-and-modal admin UI and jQuery stack, and raw-CSS themes. → [UI spec](../../specs/2026-10-06-ui-architecture-design.md), U1 tokens.
- Any LubeLogger logo or icon; bootstrap-datepicker (Apache-2.0) if anything is ever lifted.

**Decide**
1. **Reimplement or translate?** Recommendation: **translate** the two engines (reminders,
   fuel economy) into Python, with the MIT notice and the `AGPL-3.0-or-later AND MIT` header in
   §8, and the defects fixed. It is faster than a clean-room rewrite and costs one REUSE line.
2. **Ship a LubeLogger bridge?** Recommendation: **yes, an optional `ostler-app-lubelogger`**
   after the Maintenance add-on's own MVP. It pushes odometer and hours, pulls reminders, and
   turns a confirmed DTC into a plan only with the owner's opt-in per vehicle. It needs local or
   Tailscale links only, an Edit-scoped key held in the brain's secret store, and Read-tier data only.
3. **Native storage shape?** Recommendation: **our own schema** (SI units, ISO 8601, `vid`,
   `source`, three reminder axes) with a published LubeLogger mapping. Not LubeLogger's model as-is.
4. **CSV compatibility as a promise?** Recommendation: **yes, for import** (all aliases, including
   Fuelly) and **for export of service, repair, upgrade, fuel, odometer and tax**. Test it
   against the sample CSVs that LubeLogger generates (`ImportController.cs:15-204`), with no LubeLogger code.

## Sources (checked 2026-10-07)

- Repo clone `hargata/lubelog` at `dd69e59b276e79b96bb459d8b1eda1501316086d` (2026-09-12),
  read only. `LICENSE`: MIT, © 2024 Hargata Softworks.
- [GitHub page](https://github.com/hargata/lubelog): about 2.9k stars, 179 forks. The latest
  release tag could not be read (GitHub API access blocked in this session).
- [LubeLogger docs](https://docs.lubelogger.com/) and the [API page](https://docs.lubelogger.com/Advanced/API):
  auth methods, key roles, `LUBELOGGER_INVARIANT_API` and the `culture-invariant` header.
- HAOS packaging: a third-party "haos-apps" listing found by web search; it names version 1.6.4.
  Unverified.
