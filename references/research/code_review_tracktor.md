---
title: "Code review: Tracktor (self-hosted vehicle costs and reminders) for Maintenance & Garage"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, REUSE.toml, THIRD_PARTY_LICENSES.md, references/research/addons_catalogue.md, references/research/ui/obd_apps.md]
summary: >
  A read-only review of javedh-dev/tracktor (MIT, commit a60e826): SvelteKit 5, Drizzle on SQLite, shadcn-svelte and Tailwind 4, LayerChart. It covers its data model (vehicles, fuel logs, maintenance logs, compliance documents, reminders, notifications), date-only reminder logic, the destructive JSON import, single-tenant auth with an open register endpoint, and a well-made oklch token theme with dim and OLED dark variants. Little code ports to our React UI; the theme tokens, fill-to-fill mileage maths, notification-key sync and CSV mapping wizard are worth taking as ideas. Against LubeLogger, which has odometer reminders and an odometer API, the advice is: ideas and schema shape only from Tracktor, integrate with LubeLogger, build our own Maintenance & Garage app.
---

# Code review: Tracktor

**What it is.** A self-hosted web app for a household fleet: garage, fuel log, service log,
insurance and inspection documents, reminders, an expenses dashboard. Reviewed from a shallow
clone of [javedh-dev/tracktor](https://github.com/javedh-dev/tracktor) at commit `a60e826`
(committed 2026-09-04), MIT, © 2025 Javed Hussain. The repo page showed about 1.0k stars and
83 forks, and the README warns it is not yet stable for production (checked 2026-10-07).
Read only; nothing was built or run, so every behaviour below is from reading code.

Why it matters to us: the owner's planned **Maintenance & Garage** add-on (services, reminders
by distance, time or hours, fault-triggered tasks, fuel and costs) is exactly Tracktor's
domain, and the owner said "we can use the code likely". The short answer is that the
*shapes* are useful, the *code* mostly is not, because of the stack and because Tracktor
never sees a car. Related: [addons_catalogue.md](addons_catalogue.md),
[ui/obd_apps.md](ui/obd_apps.md) (consumer apps' cost tracking).

## 1. Stack

| Layer | Tracktor | Ostler today |
|---|---|---|
| UI framework | Svelte 5 + SvelteKit 2 (`package.json`) | React 19 + TS + Vite (`ui/package.json`) |
| Server | SvelteKit server routes in Node, `adapter-node`, Docker | Python core; Pi stays Node-free (ADR-0004 via app-model §7) |
| DB / ORM | SQLite through libsql + Drizzle ORM, snake_case columns (`src/server/db/index.ts:5-11`); 22 SQL migrations | JSONL logbook, SQLite planned for logs at scale |
| Styling | Tailwind 4 + shadcn-svelte (zinc base, `components.json`), bits-ui, tailwind-variants, `mode-watcher` | Hand-written CSS on W3C design tokens (`ui/tokens/*.tokens.json`, `ui/src/styles.css`) |
| Charts | LayerChart 2.1 on d3-scale/d3-shape | none bundled beyond MapLibre |
| Forms / validation | sveltekit-superforms + formsnap + zod 4 | zod 4 |
| i18n | Paraglide (inlang), 14 message files, RTL support | `Intl` (CLDR), own i18n |
| Other | node-cron, nodemailer, pdfkit, csv-parse, bcrypt, svelte-dnd-action | — |
| Tests | Vitest, 5 test files (`src/__tests__/`) | Vitest + Playwright + axe |

## 2. Data model

All tables use a text UUID id and text ISO timestamps (`src/server/db/schema/audit.ts:4-20`).
Every child row cascades on vehicle delete.

| Table | Key fields | Cite |
|---|---|---|
| `vehicles` | make, model, year (required); plate, VIN, colour, odometer, image (all optional); `fuelType` enum petrol/diesel/electric/lpg/cng; `vehicleType` enum car…yacht/rv/other; `customFields` JSON text | `schema/vehicle.ts:5-43` |
| `fuel_logs` | date, odometer?, fuelAmount?, rate?, cost, `filled` (full tank), `missedLast` (a fill was not logged), notes, attachment | `schema/fuel-log.ts:6-28` |
| `maintenance_logs` | date, odometer (required), serviceCenter, cost, notes, attachment. **No parts, no service type, no interval** | `schema/maintenance-logs.ts:6-25` |
| `compliance_documents` | type (insurance / emissions / roadworthiness / registration / other + `otherLabel`), documentNumber, issuer, start/end date, recurrence, cost, attachment | `schema/compliance.ts:6-30`, `lib/domain/compliance.ts:23-29` |
| `reminders` | type (maintenance, insurance, pollution, registration, inspection, custom), `dueDate`, `remindSchedule` (same day … one month before), recurrence type/interval/end, note, `isCompleted` | `schema/reminder.ts:6-26`, `lib/domain/reminder.ts:9-32` |
| `notifications` | vehicleId, type, channel (reminder/alert/information), `notificationKey` (unique), message, source, dueDate, isRead, clearedAt | `schema/notification.ts:6-30` |
| `notification_providers` | name, type (email / webhook / Gotify), config JSON (encrypted with `APP_SECRET`), channels | `schema/notification-provider.ts:5-13`, `lib/domain/notification-provider.ts:4` |
| `users`, `sessions` | username + bcrypt hash; session id = SHA-256 of the token | `schema/auth.ts:6-22`, `server/utils/session.ts:14-20` |
| `configs` | key/value app settings, including the dashboard layout | `schema/config.ts:5-10`, `services/dashboardWidgetService.ts:8-24` |

The 2026-08 migrations folded separate insurance and PUCC (Indian pollution certificate)
tables into one generic `compliance_documents` table
(`migrations/20260804090000_add_compliance_documents.sql` … `090200_drop_insurance_pucc_tables.sql`).
That generalisation (insurance, emissions test, roadworthiness such as MOT/TÜV/WoF,
registration/road tax) is the right shape for a UK D2 owner too.

**Gaps that matter for Ostler:** no odometer history table (only `vehicles.odometer` plus the
odometers on fuel and service rows; the "latest" odometer is the max of the three,
`lib/domain/fuel/mileage.ts:8-17`); no engine hours; no parts or consumables; no tie from a
service to a reminder; no user ownership of any row (see §5).

## 3. Reminder logic

- **Date only.** A reminder has one `dueDate`; there is no distance or hours trigger anywhere
  in the schema or services. This is the biggest functional gap against the owner's brief.
- **When it fires.** `calculateReminderNotificationDate` subtracts the lead time (1 day, 3 days,
  1 week, 1 month) from the due date; `isReminderAvailable` is true once that date is today or
  past (`services/notification-service.helper.ts:37-65`).
- **Materialised notifications.** On every reminder create/update/delete, and from a node-cron
  job (default `0 9 * * *`, configurable, `services/notificationSchedulerService.ts:10-21`),
  `syncVehicleNotifications` rebuilds the vehicle's due items, upserts them on a stable
  `notificationKey` such as `reminder:<id>:<schedule>` or `compliance:<id>:<endDate>`, and
  deletes stale system rows (`services/notificationService.ts:26-149`). Compliance documents
  raise an alert from 30 days before expiry (`notificationService.ts:60`). Alerts cannot be
  dismissed, only resolved (`notificationService.ts:227-229`). Idempotent and simple: a good
  pattern.
- **Recurrence is half done.** `getNextDueDate` computes the next yearly/monthly/weekly/daily
  occurrence (`lib/helper/recurrence.helper.ts:12-60`) and the compliance list uses it, but
  nothing on the server rolls a completed recurring reminder forward; the reminder service only
  stores the fields (`services/reminderService.ts:46-86`). Dispatch goes to email, a generic
  webhook or Gotify.

## 4. Import and export

- **Full backup:** `POST /api/data/export` dumps every table except users/sessions as JSON,
  optionally encrypted with a password (scrypt + AES-256-GCM, legacy PBKDF2 read path;
  `services/data-transfer.service.ts:22-55`, `services/crypto.service.ts:1-19`).
- **Restore is destructive:** import deletes all vehicles, logs, reminders and providers in a
  transaction, then inserts the file's rows with no schema validation beyond "is an object"
  (`data-transfer.service.ts:57-131`). Fine for one-user backup; wrong for anything shared.
- **Fuel CSV import:** a three-step wizard (upload, map columns, preview) with required/optional
  column hints (`components/feature/fuel/fuel-log-import.svelte.ts:12-60`,
  `ImportStepMapping.svelte`). The mapping UX is worth copying for importing other apps' logs.
- **PDF:** a pdfkit maintenance report per vehicle (`services/maintenanceLogPdfService.ts`).
  No CSV export of single tables, no OpenAPI description.

## 5. API and auth

- REST under `/api`: vehicles and nested fuel/maintenance/compliance/reminders/notifications,
  plus fleet-wide GET lists, dashboard summary/layout, files, config, data import/export,
  health. Hand-written handlers, no OpenAPI.
- **Auth** (`server/middlewares/auth.ts:7-66`): only `/api/*` is checked; a session cookie
  (httpOnly, SameSite=Lax) or `Authorization: Bearer` token; 30-day sessions refreshed at 15
  days left (`server/utils/session.ts:19,63-65`). `TRACKTOR_DISABLE_AUTH` turns it off.
- **Single tenant.** Users exist but own nothing: no service filters by user, so every account
  sees and edits every vehicle. Nothing like our roles or sharing (ADR-0029, ADR-0037).
- **Open registration (read from code, not tested):** `/api/auth` is on the bypass list and
  `POST /api/auth/register` creates a user without checking that none exists or that the caller
  is signed in (`routes/api/auth/register/+server.ts:7-27`). On an exposed instance anyone could
  register and then see all data. Worth reporting upstream; a pattern to avoid.
- Uploads: filename guard against `..` and separators (`server/utils/file-route.ts:27`).

## 6. UI, styling and charts

**Look.** Clean, quiet, admin-dashboard style: sidebar shell, cards, data tables, sheets for
forms, a 12-column drag-and-resize widget dashboard (13 widgets such as fuel trend, expense
breakdown, upcoming reminders, vehicle health, a calendar), a vehicle "hub" page with hero
image and quick actions, a maintenance timeline. It looks like a well-kept shadcn app, not
like a car app; nothing here resembles the dark, map-first *Speedometer* look the owner likes.

**Theme tokens** (`src/styles/app.css:25-135`) are the most reusable visual asset:
- shadcn's zinc oklch neutrals for light and dark, with a deliberately desaturated status set
  (destructive `#9c5a4c`, success `#74845c`, warning `#b08a3c`, info `#5c7487`) and a matching
  five-colour chart set — calm, close to our "calm instrument" principle;
- **two extra dark variants** selected by `data-dark-variant`: `dim` (lifted greys for evening
  reading) and `oled` (true black surfaces, 8 % borders) — directly relevant to a head unit at
  night (`app.css:107-135`, `lib/utils/theme.ts:74-93`);
- a runtime accent override that only touches `--primary`, `--primary-foreground` and `--ring`
  (`lib/utils/theme.ts:35-60`), so users get a brand colour without breaking contrast;
- radius scale from one `--radius` token (`app.css:136-140`).
Weak spots: fonts pulled from Google Fonts at runtime (`app.css:1`, Epunda Sans + JetBrains
Mono), which fails offline (we do the same with Figtree, `ui/src/styles.css:12` — both should
self-host); chart value formatters hard-code litres (`dashboard/widgets/FuelConsumptionTrendWidget.svelte`).

**Charts.** LayerChart (Svelte-only) behind shadcn's `chart` container/tooltip
(`components/ui/chart/`), area and line trends per vehicle, a donut, a calendar heat view.
No maps, no time-at-speed, no route views.

**What ports to React.** shadcn-svelte is a port of shadcn/ui (React, MIT) — so the React
originals exist for every component Tracktor uses (sidebar, sheet, data table, calendar,
chart). The *Svelte* files themselves do not port. LayerChart has no React build; the React
equivalents are Recharts (what shadcn/ui charts use) or visx. Domain TS (zod schemas,
`mileage.ts`, `recurrence.helper.ts`, the notification helper) is framework-free and would
port with light edits. The token sheet ports by copying values into `ui/tokens/*.tokens.json`.

**Mileage maths worth keeping** (`lib/domain/fuel/mileage.ts:24-89`): a fill-to-fill window
only counts when both ends are full fills, a `missedLast` flag breaks the chain, and fuel is
summed over partial fills in between. One flaw: the average is a mean of per-window ratios,
not total distance over total fuel, so short windows weigh as much as long ones (line 73).

## 7. Licence: MIT into AGPL-3.0-or-later

- **Permitted.** MIT is in ADR-0025's "copy anywhere, notice kept" row, and ADR-0012 accepts
  permissive code in core and in `ostler-app-<x>` repos. Ideas need no notice at all.
- **Attribution if any file or substantial snippet is copied:** keep "Copyright (c) 2025 Javed
  Hussain" and the MIT text; add a REUSE annotation with both copyright holders and
  `AGPL-3.0-or-later AND MIT` (the pattern already used for the Astryx tokens in `REUSE.toml`),
  and a section in `THIRD_PARTY_LICENSES.md` (repo, commit `a60e826`, files). `LICENSES/MIT.txt`
  already exists.
- **Third-party assets inside the repo:** shadcn-svelte, bits-ui, LayerChart, Paraglide output
  and other npm deps are MIT/Apache; the Epunda Sans and JetBrains Mono fonts come from Google
  Fonts (OFL, not checked file by file). The logo, `hero-bg.svg`, PWA icons and default vehicle
  images under `static/` are Tracktor's brand: **do not take them**. Translations in
  `i18n/messages/*.json` are MIT text but written for Tracktor's strings; reuse only where a key
  means the same thing.
- **AGPL side effect:** none for upstream; anything we copy becomes part of an AGPL work, which
  MIT allows.

## 8. Head-to-head with LubeLogger

LubeLogger ([hargata/lubelog](https://github.com/hargata/lubelog), MIT, © 2024 Hargata
Softworks; clone at `dd69e59`, 2026-09-12; docs at docs.lubelogger.com, checked 2026-10-07):
ASP.NET Core, LiteDB or PostgreSQL, Bootstrap + Chart.js.

| | Tracktor | LubeLogger |
|---|---|---|
| Stack | SvelteKit, Node, SQLite/Drizzle | ASP.NET Core, LiteDB/Postgres |
| Record types | fuel, service, compliance docs, reminders | fuel, service, repair, upgrade, tax, inspection, odometer, equipment, supplies, plans, notes |
| Reminder triggers | **date only** | **date, odometer, or both** (`Enum/ReminderMetric.cs`), urgency levels not urgent → past due (`Enum/ReminderUrgency.cs`), custom thresholds, fixed vs rolling intervals (`Models/Reminder/ReminderRecord.cs:3-21`) |
| Odometer history | none (max of logs) | first-class `OdometerRecord` with an API: `POST /api/vehicle/odometerrecords/add`, `GET …/latest` (`Controllers/API/OdometerController.cs:12-131`) |
| Multi-user | users see everything | collaborators per vehicle, OIDC |
| API | undocumented REST | documented REST per record type |
| Look | modern shadcn, dark variants, widget grid | older Bootstrap, functional |
| Maturity | ~1k stars, "not production stable" | longer-lived, wider record set |
| Home Assistant | none | community integrations reported; **not verified** |

**Which fits Ostler.** LubeLogger's model is closer to the brief (distance reminders, an odometer
log, an API we can push to). Tracktor's front end is nicer but in the wrong framework.

## 9. Recommendation

**Ideas and schema shape only from Tracktor; integrate with LubeLogger; build our own
Maintenance & Garage app** (an `ostler-app-maintenance` repo per app-model §7, React, our
tokens). Reasons: no Svelte code ports into a React shell; Tracktor's server is Node, which
the Pi does not run; its reminders cannot use the one thing Ostler uniquely has, the car's own
odometer, engine hours and fault codes. Ostler should be the *source* of odometer, hours and
faults: our app evaluates distance/time/hours reminders locally, and an optional integration
pushes odometer readings to a user's LubeLogger (and, if wanted, Tracktor's vehicle odometer
via its Bearer-token API). Copy small pure functions (mileage windows, next-due-date) only if
it saves time, with the MIT notice.

## 10. Copy / Avoid / Decide for Ostler

**Copy**
- The **dim and OLED dark variants** as extra token sets beside light/dark in
  `ui/tokens/color.dark.tokens.json`, chosen by a data attribute; OLED for the head unit at
  night (UI spec §2 principles, U1 tokens).
- The **accent-only override** (primary, its foreground, ring) so owners can theme without
  breaking contrast or status colours (UI spec §2; status never by colour alone).
- The **desaturated status and chart palette** idea, run through our palette validator first
  (UI spec §2, "calm instrument").
- **Generic compliance documents** (insurance, emissions, roadworthiness, registration, other)
  with expiry alerts that cannot be dismissed, only resolved (Maintenance & Garage app,
  app-model §3 row to add).
- **Stable notification keys** (`kind:id:due`) with upsert and stale-row cleanup, so reminders
  stay idempotent across restarts and syncs (app-model §13 queued actions; ADR-0033 audit).
- **Fill-to-fill fuel windows** with `filled` and `missedLast`, but averaged as total distance
  over total fuel (Maintenance & Garage app).
- The **three-step CSV mapping wizard** for importing other apps' fuel and service logs.

**Avoid**
- Date-only reminders; ours trigger on distance, engine hours, time and fault codes read from
  the car, whichever comes first (owner brief; ADR-0033 Maintenance category).
- Destructive whole-database restore without validation; imports must merge and validate with
  zod against our schemas (api-consistency spec).
- Unowned rows and open self-registration; every record belongs to a vehicle under ADR-0029
  roles and sharing.
- Fonts from Google Fonts at runtime — self-host ours (Figtree today) so the garage works
  offline (UI spec §2).
- Taking Tracktor's logo, hero art, icons or default vehicle images (ADR-0025, brand assets).
- A generic admin-dashboard look for the driver; the head unit stays template-bound (UI spec
  §7, app-model §4.4).

**Decide**
1. **Maintenance & Garage is our own app, not a fork.** Recommendation: approve a new
   `ostler-app-maintenance` repo (ADR-0034 amendment), React + our tokens, with Tracktor and
   LubeLogger as idea sources only; write its spec before code.
2. **Reminder triggers.** Recommendation: distance, engine hours, calendar time, and "fault
   code seen", whichever first, with LubeLogger-style urgency bands (not urgent, urgent, very
   urgent, past due) and fixed vs rolling intervals.
3. **An odometer/hours history as platform data**, written by Trips from the car, not typed
   in. Recommendation: yes, as a logbook-derived series the Garage app reads (ADR-0009).
4. **LubeLogger integration.** Recommendation: an optional integration that pushes odometer
   readings (and later service events) to a user's LubeLogger through its API, off by default,
   token stored like other uplink secrets; Tracktor push only if a user asks.
5. **Dim and OLED dark variants in U1 tokens.** Recommendation: add both now; it is a cheap,
   visible styling win the owner asked for.
6. **Charts library for the React UI.** Recommendation: pick one (Recharts, MIT, matches
   shadcn/ui charts) in a short ADR before the Garage and Trips statistics screens, rather
   than per-app choices.

## Sources (checked 2026-10-07)

- Tracktor clone, commit `a60e826` (2026-09-04), MIT; repo page for stars, forks and the
  stability warning: <https://github.com/javedh-dev/tracktor>.
- LubeLogger clone, commit `dd69e59` (2026-09-12), MIT, README and source; feature list:
  <https://docs.lubelogger.com/>. Home Assistant integrations: not verified.
- Ostler: `REUSE.toml`, `THIRD_PARTY_LICENSES.md`, ADR-0025, `ui/package.json`,
  `ui/src/styles.css`.
