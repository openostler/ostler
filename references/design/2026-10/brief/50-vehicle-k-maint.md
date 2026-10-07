---
title: "Designer brief: vehicle and diagnostics (K) — Maintenance records, tasks, odometer, import, export, sharing and Garage"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  Eleventh file of the vehicle and diagnostics brief. It covers the rest of the Maintenance
  app: the existing Add record sheet, the parked head-unit Due kiosk and the system Garage
  page with its garage cards, plus new pages under the approved Maintenance spec: task
  detail (fault-suggested tasks, Watching for three clean drives), the odometer reading
  prompt with the three-rung ladder, task templates and pack schedules, the three-step CSV
  import wizard (upload, map columns, preview), the export bundle and the time-boxed buyer
  share. The D2's odometer is always estimated; no Td5 schedule is shipped yet.
---

# Vehicle and diagnostics brief (K): Maintenance records and Garage

### maint-add-record — Add record (service, fuel, expense, document)  [Existing]
- **Purpose:** add or edit one record, asking only for what the car cannot tell.
- **Owner:** app:maintenance
-
- **Opens from → goes to:** category tile + Add; maint-due Log service; maint-fuel, maint-documents → the tab; after an oil service: offer **Reset service interval** (diagnose-confirm, if the pack declares it).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (service), phone Day (fuel), hu9 Night.
- **Content (top to bottom):**
  1. Type Segmented: **Service · Fuel · Expense · Document**.
  2. Service: date, odometer (prefilled "≈ … km · est." with **Use this** or type), engine hours, kind (service, repair, upgrade), items (part no., brand, qty), labour, cost, who (myself, garage name), **Closes** (open tasks to tick), notes, tags, attachments (photo or PDF).
  3. Fuel: date and time, odometer, volume (L), cost, **Full** or **Partial**, "I missed a fill before this", station (place name, opt-in).
  4. Expense: date, category (insurance, tax, parking, tolls, fines, finance, parts, other), amount, recurring.
  5. Document: kind, issuer, number (local only), valid from, valid to, cost, attachment.
  6. **Save**, **Cancel**.
- **States:** an odometer far off the ladder (> 2 000 km or 10 %): "This is far from the estimate. Is it right?" with Confirm or Edit. Idling without Park evidence and Moving: locked view, Open on phone.
- **Safety and driving rules:** typing is Parked only ([UI §12.1][ui-12.1]); the reset goes through the gate ([Maintenance §10][mg-10]).
- **Components:** Sheet, Segmented, TextField (new component), Toggle (new component), Button.
- **Spec refs:** [Maintenance §2][mg-2] · [Maintenance §7][mg-7].

### maint-kiosk — Parked head-unit Due view (kiosk)  [Existing]
- **Purpose:** a big, calm Due list on the car screen when parked.
- **Owner:** app:maintenance
-
- **Opens from → goes to:** dock or app drawer on a head unit; the trip-end alert card "Oil service due in 300 km" → maint-task (Parked).
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim Parked, hu9 Night, hu5 Night.
- **Content (top to bottom):** 1. Vehicle name and odometer with suffix. 2. Up to six Due rows, ≤ 30 characters each, band pill with icon and word. 3. **Log it on your phone** hint; on the head unit one **Mark done** per row opens maint-add-record (Parked).
- **States:** nothing due: "Nothing due". Idling without Park evidence: view only. Moving: nothing but the trip start or end alert card ([Maintenance §8][mg-8]).
- **Safety and driving rules:** in-car reminders only at trip start or end, never mid-drive.
- **Components:** ListRow (head-unit size), Chip (band pill).
- **Spec refs:** [Maintenance §7][mg-7] · [Maintenance §8][mg-8].

### garage — Garage (vehicles, garage cards)  [Existing]
- **Purpose:** the owner's vehicles, with cards apps add to.
- **Owner:** os
- **Opens from → goes to:** system Settings → Garage; the Vehicle chip sheet → a vehicle's details, the vehicle pack's integration setup page (app framework, `90-appframe-*`), maint-home (its card).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):** 1. Vehicle cards: name ("Discovery 2 Td5"), pack chip ("lr_d2"), driver side (right), transport ("K-line · node"), attached devices, last-known summary with age, **Active** marker. 2. App cards in the garage-card slot: Maintenance "Next due: … · band pill · this month £…". 3. **Add vehicle**; per vehicle **Edit**, **Remove**.
- **States:** one vehicle: no switcher in the strip. Inactive vehicle: summary in stale grey with age. Idling without Park evidence and Moving: locked view.
- **Safety and driving rules:** one live link per port; activating a vehicle stops the other's sources first ([UI §4.1][ui-4.1]).
- **Components:** Card, ListRow, Chip, Button.
- **Spec refs:** [UI §4.1][ui-4.1] · [Maintenance §7][mg-7].

### maint-task — Task detail  [New]
- **Purpose:** one reminder: why it is due, and close it honestly.
- **Owner:** app:maintenance
-
- **Opens from → goes to:** maint-due row; diagnose-fault "Add to maintenance" → maint-add-record (Log service), diagnose-fault, diagnose-clear-result (audit link).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (fault-raised task in Watching).
- **Content (top to bottom):** 1. Title and band pill. 2. Remainders per axis (distance, engine hours, time, fault seen) and which fired. 3. Trigger: "Raised by TD5 fault 5.2 · coolant temp. circuit" with the snapshot and session links. 4. **Watching**: "Not seen for 2 of 3 clean drives" (a clean drive is one where TD5 was read and the code was absent). 5. Actions: **Log service**, **Close** (offered at 3 clean drives); **Edit**.
- **States:** the code returns: "Seen again · reopened". Closed 180 days: a new linked task opens instead. Moving: locked.
- **Safety and driving rules:** suggestions, never auto-created ([Maintenance §6][mg-6]).
- **Components:** Card, Chip, ListRow, Button.
- **Spec refs:** [Maintenance §3][mg-3] · [Maintenance §6][mg-6].

### maint-odometer — Odometer reading  [New]
- **Purpose:** ask for a reading only when needed, and show where the number comes from.
- **Owner:** app:maintenance
-
- **Opens from → goes to:** fill-up and service records; maint-home odometer line → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Ladder rows: **From car** ("Not reported by the Td5"), **Estimated** ("≈ … km from trips since 3 Oct", `candidate`), **Last recorded** ("as of …"). 2. "Distance driven without Ostler connected is not counted." 3. Number field and **Save**.
- **States:** outlier: confirm as in maint-add-record. Moving: locked.
- **Safety and driving rules:** typing Parked only.
- **Components:** ListRow, TextField (new component), Button.
- **Spec refs:** [Maintenance §4][mg-4].

### maint-templates — Task templates and schedules  [New]
- **Purpose:** the recurring tasks: pack schedules and the owner's own.
- **Owner:** app:maintenance
-
- **Opens from → goes to:** maint-due → a template editor sheet.
- **Layout classes:** phone · tablet · desktop · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. **From the vehicle pack**: for the D2 "No Td5 schedule yet (sourcing in progress)"; for `generic_obd2` cars oil, filters, brake fluid, coolant, roadworthiness test, each with its citation. 2. **Yours**: name, category, interval (distance, engine hours, months, days), Rolling or Fixed, leads, "Raise on fault" patterns. 3. **Add template**.
- **States:** user edit overrides a pack template per vehicle ("Edited"). Moving: locked.
- **Safety and driving rules:** Park to edit.
- **Components:** ListRow, Segmented, TextField (new component), Button.
- **Spec refs:** [Maintenance §2][mg-2] · [Maintenance §6][mg-6].

## Flow: import records from CSV

| Step | Screen | The user | What can fail and the recovery |
|---|---|---|---|
| 1 | maint-import-upload | picks a file and its source (Fuelly, LubeLogger, other) | unreadable file: "Not a CSV we can read" |
| 2 | maint-import-map | checks column and unit mapping, date order | unknown column: left unmapped, shown |
| 3 | maint-import-preview | reviews new and duplicate rows, Import | schema errors: rows listed and skipped |

### maint-import-upload — Import: upload  [New]
- **Purpose:** start an import.
- **Owner:** app:maintenance
- **Opens from → goes to:** Maintenance settings → Import → maint-import-map.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night, phone Night.
- **Content (top to bottom):** 1. Step "1 of 3". 2. **Choose file**. 3. Source Segmented: Fuelly · LubeLogger · Other. 4. "Imports merge with what you have; nothing is replaced."
- **States:** large file: progress row. Moving: locked.
- **Safety and driving rules:** Parked only on head units.
- **Components:** StepProgress (new component), Segmented, Button.
- **Spec refs:** [Maintenance §9][mg-9].

### maint-import-map — Import: map columns  [New]
- **Purpose:** match the file's columns to records.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-import-upload → maint-import-preview.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Rows: file column → field (auto-matched by alias), unit picker (km, mi, L, gal), currency. 2. Date order pick (day first or month first) with a sample row. 3. **Next**.
- **States:** required field unmapped: Next disabled with the field named.
- **Safety and driving rules:** as above.
- **Components:** ListRow, select (new component), Segmented, Button.
- **Spec refs:** [Maintenance §9][mg-9].

### maint-import-preview — Import: preview  [New]
- **Purpose:** see exactly what will be added.
- **Owner:** app:maintenance
- **Opens from → goes to:** maint-import-map → maint-timeline.
- **Layout classes:** phone · tablet · desktop. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Counts: new, duplicates skipped (same date, odometer and amount), errors. 2. First rows as they will appear, with "import:fuelly" provenance. 3. **Import**.
- **States:** all duplicates: "Nothing new to import".
- **Safety and driving rules:** validated against the schemas.
- **Components:** Card, ListRow, Button.
- **Spec refs:** [Maintenance §9][mg-9].

### maint-export — Export bundle  [New]
- **Purpose:** take everything out, attachments included.
- **Owner:** app:maintenance
- **Opens from → goes to:** Maintenance settings → Export → a saved file.
- **Layout classes:** phone · tablet · desktop · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. **Export bundle** (zip: data, CSVs, all attachments, a printable history page). 2. Fuelly fuel CSV; LubeLogger-shaped CSVs. 3. **Export**, then Save or Share.
- **States:** large attachments: size shown first. Moving: locked.
- **Safety and driving rules:** export never drops attachments and is never paywalled.
- **Components:** ListRow, Button.
- **Spec refs:** [Maintenance §9][mg-9].

### maint-buyer-share — Share history with a buyer  [New]
- **Purpose:** a time-boxed, read-only service history for a buyer.
- **Owner:** app:maintenance
- **Opens from → goes to:** Maintenance settings → Share → the system sharing page (accounts S8).
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night.
- **Content (top to bottom):** 1. What they see: records, Due list, odometer rounded to 1 000 km, document kinds and dates. 2. Never: VIN, plate, document numbers, locations. 3. Ticks (off by default): documents, attachments. 4. Expiry 7 days (max 30). 5. **Create link**; then state, **Revoke**.
- **States:** expired or revoked chips. Moving: locked.
- **Safety and driving rules:** audited and revocable ([Maintenance §10][mg-10]).
- **Components:** Sheet, Checkbox (new component), Chip, Button.
- **Spec refs:** [Maintenance §10][mg-10] · [Accounts §14.7][acc-14.7].

[ui-4.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[mg-2]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#2-schema
[mg-3]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#3-reminder-engine
[mg-4]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#4-odometer-and-engine-hours-ladder
[mg-6]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#6-faults-and-manufacturer-schedules
[mg-7]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#7-garage-screens
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[mg-9]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#9-import-and-export
[mg-10]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#10-sharing
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
