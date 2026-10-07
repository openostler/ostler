---
title: "Designer brief: vehicle and diagnostics (J) — Maintenance & Garage home and its five tabs"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Tenth file of the vehicle and diagnostics brief. It gives full page content for the
  existing Maintenance & Garage add-on screens per vehicle: the Maintenance home (total
  cost hero, this-month donut in the three categorical tokens, category tiles with Add,
  Insights, Due list and the Records link to Trips) and the five tabs Due, Timeline, Costs,
  Fuel and Documents, with band pills, provenance suffixes (from car, est., you, mechanic)
  and the D2's honest odometer state: the Td5 reports no odometer, so distance is always
  estimated from trips. Every number says where it came from.
---

# Vehicle and diagnostics brief (J): Maintenance & Garage

An add-on (`ostler-app-maintenance`, off by default). It never touches the car; its one car
action, a pack's service-interval reset, goes through diagnose-confirm (Maintenance, Tier 1)
([Maintenance §1][mg-1]). **Bands** (four): Not due · Urgent · Very urgent · Past due; default
leads urgent 30 d / 1 500 km / 20 h, very urgent 7 d / 500 km / 5 h ([§3][mg-3]).
**The D2 today:** the Td5 does not report an odometer, so the odometer is rung 2, "≈ … km,
estimated from trips since <date>" (`candidate`); D2 Td5 service intervals wait for sourcing,
so the pack ships no schedule yet and Due holds only the owner's own tasks ([§4][mg-4], [§6][mg-6]).
Driving rules for every tab: Parked full; Idling edits need Park evidence; while Moving
nothing but the trip start or end alert card ([§7][mg-7], [§8][mg-8]).

### maint-home — Maintenance home per vehicle  [Existing]
- **Purpose:** what this vehicle costs and what is due, at a glance.
- **Owner:** app:maintenance
- **Opens from → goes to:** dock or app drawer → Maintenance; Service due widget; garage card; Home card; strip chip at very urgent → maint-due, maint-timeline, maint-costs, maint-fuel, maint-documents, maint-add-record, trips-records.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night and Day, hu9 Night (Parked), tablet Night.
- **Content (top to bottom):**
  1. Tabs: **Overview · Due · Timeline · Costs · Fuel · Documents**.
  2. **Total cost** HeroStat with "this year" sub-line (currency per preference).
  3. **This month** Donut in `series-1…3` (Fuel, Maintenance, Expenses) with legend rows and delta vs last month ("+12 % vs September" style, computed).
  4. Three **category tiles** (Card), each with its total and its own **+ Add**.
  5. **Insights** ListRows: vs year average, top category, costliest month, cost per km (marked "est." on the D2).
  6. **Due** list (top three) with band pill → maint-due.
  7. **Records** Card → Trips → Statistics → Records.
- **States:** empty: "Nothing recorded yet. Add a service, a fill-up or a document." with three Add buttons. No vehicle: "Add a vehicle in Garage". Offline: local data (stored on the device that owns the vehicle). Idling without Park evidence: view only. Moving: nothing (the page is locked); only the §8 alert card at trip start or end.
- **Safety and driving rules:** categorical chart never also draws status colours or accent marks ([Visual §3.3][vds-3.3]).
- **Components:** HeroStat, Donut, Card (tile + Add), ListRow, Chip (band pill), TabBar.
- **Spec refs:** [Maintenance §7][mg-7] · [Visual §3.3][vds-3.3].

### maint-due — Maintenance: Due tab  [Existing]
- **Purpose:** every open task, ordered by how soon, with why.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-home; strip chip (very urgent or past due); alert card → maint-task (a row), maint-add-record (Log service), maint-templates.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):**
  1. Groups by band: **Past due**, **Very urgent**, **Urgent**, **Not due**; band pill with icon and word (`alarm`, `warn`, neutral).
  2. Rows: title ("Oil and filter" style task from the owner), the axis that fired and its signed remainder ("in 300 km", "12 days ago"), provenance suffix on the distance ("est."), trigger Chip (schedule, fault `5.2`, battery trend, you).
  3. **Suggested** section: fault-raised suggestions with one-tap **Add task** ("TD5 5.2 coolant temp. circuit").
  4. **Watching** section: "not seen for 2 of 3 clean drives".
- **States:** nothing due: "Nothing due." No schedule for this car: "No manufacturer schedule for the Td5 yet. Add your own tasks." Moving: locked.
- **Safety and driving rules:** notifications only on a band change ([Maintenance §3][mg-3]).
- **Components:** ListRow (provenance suffix), Chip (band pill, trigger), Button.
- **Spec refs:** [Maintenance §7][mg-7] · [Maintenance §2][mg-2] · [Maintenance §3][mg-3].

### maint-timeline — Maintenance: Timeline tab  [Existing]
- **Purpose:** one history of everything done to the car.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-home → a record detail (maint-add-record in edit), diagnose-fault-history (a clear entry), trips-detail (a linked session).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night.
- **Content (top to bottom):** 1. Filter Chips by record type: service, repair, upgrade, fuel, expense, document, meter reading. 2. Month headers; rows coloured by record type (categorical slots, three at most, the rest neutral icons): date, title, odometer with provenance suffix ("from car", "est.", "you", "mechanic"), cost, attachment count. 3. Linked items: "Closes: Oil and filter", "Cleared codes · audit".
- **States:** empty: "No records yet". Moving: locked.
- **Safety and driving rules:** read only here; editing Parked or Idling with Park evidence.
- **Components:** ListRow (provenance suffix), Chip (type), Card.
- **Spec refs:** [Maintenance §7][mg-7] · [Maintenance §2][mg-2].

### maint-costs — Maintenance: Costs tab  [Existing]
- **Purpose:** where the money goes over time.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-home → maint-timeline (filtered), maint-add-record (expense).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, tablet Night.
- **Content (top to bottom):** 1. Period Segmented (Month · Year · All). 2. HeroStat total for the period. 3. Stacked monthly bars in the three categories (Fuel, Maintenance, Expenses; finer expense categories fold into "Other"). 4. Category rows with totals and share. 5. Cost per km ("est." on the D2) and cost per engine hour where known.
- **States:** one month only: bars hidden, rows shown. Moving: locked.
- **Safety and driving rules:** at most three categorical series ([Visual §3.3][vds-3.3]).
- **Components:** HeroStat, DistributionBars (stacked variant, new), ListRow, Segmented.
- **Spec refs:** [Maintenance §7][mg-7] · [Maintenance §2][mg-2].

### maint-fuel — Maintenance: Fuel tab  [Existing]
- **Purpose:** fill-ups and honest fuel economy.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-home → maint-add-record (fuel), maint-odometer.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, phone Day.
- **Content (top to bottom):** 1. HeroStat headline economy: total distance ÷ total fuel over complete full-to-full windows, unit per preference (L/100 km, mpg UK, mpg US, km/L), "estimated" on the D2. 2. Economy per window as a line with gaps where a fill was missed. 3. Fill-up rows: date, volume, cost, full or partial, odometer with suffix, "Missed fill before" flag, station place name if opted in. 4. **+ Add fill-up**.
- **States:** fewer than two full fills: "Needs two full fill-ups for a figure". A missed fill: that window shows no figure. Moving: locked.
- **Safety and driving rules:** place names only, opt-in ([Maintenance §2][mg-2]).
- **Components:** HeroStat, Area line (with gaps), ListRow, Button.
- **Spec refs:** [Maintenance §7][mg-7] · [Maintenance §5][mg-5] · [Maintenance §2][mg-2].

### maint-documents — Maintenance: Documents tab  [Existing]
- **Purpose:** MOT, insurance, tax and other papers with their expiry.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-home → maint-add-record (document), an attachment viewer.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Rows by kind: Roadworthiness (MOT), Insurance, Registration and tax, Emissions, Warranty, Other; issuer, valid from and to, band pill as it nears expiry, attachment count. 2. The document number is shown on this device only, with a lock icon and "never shared". 3. **+ Add document**.
- **States:** expired: `alarm` pill "Expired"; its alert can be resolved (renewed), not dismissed. Moving: locked.
- **Safety and driving rules:** document numbers never leave the device ([Maintenance §10][mg-10]).
- **Components:** ListRow, Chip (band pill), Button.
- **Spec refs:** [Maintenance §7][mg-7] · [Maintenance §2][mg-2].

[vds-3.3]: ../../../../specs/2026-10-07-visual-design-system-design.md#33-data-ramps-and-chart-colours-datatokensjson
[mg-2]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#2-schema
[mg-3]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#3-reminder-engine
[mg-4]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#4-odometer-and-engine-hours-ladder
[mg-5]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#5-fuel-economy
[mg-6]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#6-faults-and-manufacturer-schedules
[mg-7]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#7-garage-screens
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[mg-10]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#10-sharing
[mg-1]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#1-scope-and-boundaries
