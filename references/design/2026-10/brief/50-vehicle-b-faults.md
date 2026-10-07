---
title: "Designer brief: vehicle and diagnostics (B) — faults, fault detail, clear codes and history"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, decisions/adr-0033-action-categories-and-approvals.md, specs/2026-10-06-j1979-service-layer-design.md, specs/2026-10-07-maintenance-garage-addon-design.md]
summary: >
  Second file of the vehicle and diagnostics brief. It gives full page content for fault
  codes on the Discovery 2 Td5: the module's Faults area with Current and Logged groups and
  fault watch (new), the existing fault detail sheet with Get help with this fault, the
  existing confirm sheets for Tier 1 to 3 actions with the ADR-0033 §5 clear-codes rules
  (automatic snapshot, one confirm naming system and consequence, the extra safety-system
  warning, no Clear for the airbag), the clear result with re-read and honest refusals (new)
  and the fault history per vehicle with audit entries (new). Examples are real pack codes.
---

# Vehicle and diagnostics brief (B): faults

Real codes to draw (from the D2 pack's `dtc/*.json`): TD5 `5.2` "coolant temp. circuit
(Current)" P0115, `23.0` "turbocharger under boosting (Current)" P0299, `20.7` "injector trim
data corrupted (Logged)" P1633 (`candidate`); SLABS `3.4` "right front wheel speed sensor —
output too low" (Logged) and `10.4` "shuttle valve switch — electrical failure" (Current), both
seen in Demo log 2; SRS `004` "airbag warning lamp circuit, open circuit"; ACE `04-02` with
its caveat; EAT `P1613-1` "solenoid-valve supply relay stuck open · limp-home".

### diagnose-faults — Module Faults area  [New]
- **Purpose:** read, watch, report and clear one module's fault codes.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-system → Faults; worst-telltale sheet; Home warnings card → diagnose-fault (a row), diagnose-confirm (Clear codes), diagnose-fault-history, help-flow.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night (SLABS with 2 faults), phone Night and Day, hu7 Night-dim Idling.
- **Content (top to bottom):**
  1. Header actions: **Read** (secondary), **Fault watch** toggle Chip ("Polls every 0.5 s instead of every 5 s"; on reads "Watch on").
  2. **Current** group, kicker "Present now": ListRows with the `alarm` edge, code in mono ("10.4"), name, P-code Chip where the pack has one ("P0115"), `candidate` Chip where unproven, chevron.
  3. **Logged** group, kicker "Stored history — not necessarily present now": the same rows with the `warn` edge.
  4. Clean state: `ok` tone Card "No fault codes — this module reports a clean fault memory."
  5. **Report** Card: "2 codes on SLABS (ABS + air suspension)", **Write to file**, **Clear codes** (danger; absent for SRS), **Fault history** link, **Get help with these faults**.
  6. ACE only: an info notice "ACE codes are known to be misleading: confirm with live pressure and valve currents."
- **States:** loading: "Reading faults…" rows. Not connected: last read in stale grey with age, Clear disabled. Module not in session: "Move session here to read". Parked: full. Idling: Clear allowed with Park evidence; otherwise Clear shows "Park to clear". Moving: the page is locked; the strip's worst-telltale chip carries the faults ([UI §3.2][ui-3.2]). Replay: "Clear codes · replay" with a lock.
- **Safety and driving rules:** clearing is Maintenance, Tier 1, Parked or Idling with Park evidence ([UI §7.1][ui-7.1], [UI §12.1][ui-12.1]); the head-unit kiosk session cannot clear (needs a signed-in driver).
- **Components:** ListRow (status edge), Chip (P-code, candidate, toggle), Card (tone), Button (danger).
- **Spec refs:** [UI §4.2][ui-4.2] · [UI §7][ui-7] · [ADR-0033 §5][adr33-5].

### diagnose-fault — Fault detail sheet + Get help with this fault  [Existing]
- **Purpose:** what one code means, what to check and where to go next.
- **Owner:** app:diagnostics
- **Opens from → goes to:** a diagnose-faults row; the telltale sheet's "Details" (Parked); a fault flag in playback → live-signal (related value), diagnose-tests (related test), help-flow, maint-task (suggested task).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night bottom sheet, hu9 Night side sheet on the passenger side, phone Day.
- **Content (top to bottom):**
  1. Title with status icon and word: "Current" (`alarm`) or "Logged" (`warn`); code "5.2" in mono, P-code Chip "P0115", module name "TD5 (engine)".
  2. Name "Coolant temp. circuit" and description "Sensor-circuit fault."
  3. **What to check:** "Check the sensor, its wiring and connector." (the pack's `cause`).
  4. **Freeze frame** stat grid where the protocol has one; otherwise "No freeze frame on this module".
  5. **Related live data** ListRows with values: Coolant °C, Coolant sensor V (`candidate`) → live-signal.
  6. **Related tests:** Temp gauge (experimental) → diagnose-tests.
  7. **Seen** line: "First seen 3 Oct · seen on 4 drives" → diagnose-fault-history.
  8. **Source and confidence:** "Meaning `proven` · TD5 fault list"; for `candidate` codes "Meaning not confirmed on a car yet".
  9. Buttons: **Get help with this fault** (secondary; opens help-flow at L4) ([UI §13.2][ui-13.2]); **Add to maintenance** (when the add-on is on); **Close**.
- **States:** unknown code: "Code 21.3 · no meaning in the pack yet" with Get help. Offline: still shown from the last read. Moving: never drawn; the shell-telltale-sheet shows the code and ≤ 30-character name only. Passenger: not unlockable.
- **Safety and driving rules:** Get help never clears or changes anything; Parked only on a driver-facing display ([UI §13.2][ui-13.2]).
- **Components:** Sheet (bottom on phone, side on head unit), Chip, StatTile, ListRow, Button (secondary).
- **Spec refs:** [UI §13.2][ui-13.2] · [Visual §9][vds-9] (fault sheet screenshot test).

### diagnose-confirm — Action confirm sheets (Tier 1–3, clear codes)  [Existing]
- **Purpose:** the one shell-drawn confirmation for anything that reaches the gate.
- **Owner:** os
- **Opens from → goes to:** Clear codes, a test (diagnose-tests), a procedure start (diagnose-procedure-start), a service-interval reset from Maintenance → diagnose-clear-result, diagnose-active-test, the procedure flow; Cancel returns.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** each variant on hu9 Night and phone Night; Tier 1 clear on phone Day.
- **Content (top to bottom), per variant (all open with Cancel focused; no countdown):**
  1. **Tier 1 · Clear codes:** title "Clear 2 codes from SLABS (ABS + air suspension)?"; consequence "Freeze frames will be lost. A snapshot of the codes is saved to Trips first."; **safety-system warning** in a `warn` Card for SLABS: "This is a brake and suspension system. The fault may still be present and the system may be degraded." Line "Ignition on, engine off." Buttons **Cancel** · **Clear codes** (danger).
  2. **Tier 1 · Reset service interval** (when a pack declares it): "Reset the service interval on TD5?" with the same layout.
  3. **Tier 2 · Actuator test:** title "Run Compressor test on SLABS?"; status Chip `verified` or `experimental`; a precondition checklist ticked live where the car reports it, else ticked by hand: "Vehicle stationary, handbrake on", "Ignition on", "Nobody under or beside the car", plus "Engine off" for TD5 tests; "Stops by itself (auto-timeout)" line; **Cancel** · **Run test** (enabled when every box is ticked).
  4. **Tier 3 · Procedure:** title "Start Modulator bleed (4 steps)?"; the same checklist ("Brake bleed in progress (fluid topped up, bleed nipples ready)"); "12 V must stay above the floor"; a TextField "Type Modulator bleed (4 steps) to confirm"; **Cancel** · **Start**.
  5. **Tier 4 rows** never open a confirm: tapping shows "Listed for honesty. Ostler never sends this."
  6. Over an adapter with no node: a "Soft gate" Chip in the header (adapter-soft-gate).
- **States:** refused at once by the node ("Not while moving") right after the confirm ([UI §7.2][ui-7.2]); Brain asleep: "Waking Brain…" on the button; remote path: actions absent, "Read only over a remote link". Idling without Park evidence and Moving: locked view.
- **Safety and driving rules:** Cancel focused, typed confirm Parked only, no countdown for gate actions ([Shell input §7][si-7]); confirm then sign ([UI §7.2][ui-7.2]); candidate and experimental shown on the button and in the sheet ([UI §7][ui-7]).
- **Components:** Sheet, Button (Cancel focused, danger, primary), Checklist (new component), TextField (new component), Card (warn tone), Chip.
- **Spec refs:** [Shell input §7][si-7] · [UI §7][ui-7] · [UI §7.2][ui-7.2] · [ADR-0033 §5][adr33-5].

### diagnose-clear-result — Clear codes result  [New]
- **Purpose:** show what really cleared, from the re-read, and every honest refusal.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-confirm (Clear codes) → diagnose-faults, diagnose-fault-history (audit entry), maint-task (watching).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (success and refusal), hu9 Night.
- **Content (top to bottom):**
  1. Progress rows while working: "Snapshot saved to Trips" (check) → "Clearing on SLABS…" → "Re-reading faults…".
  2. **Result:** "1 of 2 codes cleared" with rows: `3.4` "Cleared"; `10.4` "Still present — the fault is current" (`alarm`).
  3. **Refusal variant:** "The ECU refused with the engine running (7F 14 22). Switch the engine off with the ignition on, then try again." Snapshot kept; no automatic retry ([ADR-0033 §5][adr33-5]).
  4. Footer: "Audit: cleared by Owner · head unit · 09:14" and **View snapshot**, **Done**.
- **States:** link lost mid-clear: "Link lost before the re-read. Read faults to see what cleared." Moving during the flow: the gate refuses; the sheet shows the refusal.
- **Safety and driving rules:** snapshot first, no option to skip; audited ([ADR-0033 §5][adr33-5], [J1979 §5][j1979-5]).
- **Components:** Sheet, progress rows (as adapter-connect), ListRow, Button.
- **Spec refs:** [ADR-0033 §5][adr33-5] · [UI §7][ui-7].

### diagnose-fault-history — Fault history  [New]
- **Purpose:** every fault event, snapshot and clear for this vehicle, by module and code.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-fault "Seen" line; diagnose-faults link; diagnose-clear-result → trips-detail (the drive where it first appeared), diagnose-scan-report.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night.
- **Content (top to bottom):**
  1. Filters: module Chips (All, TD5, SLABS…), "Current only", period.
  2. **By code** list: code, name, module, first and last seen, drives seen ("4"), state Chip (Present · Cleared · Watching · Gone for 3 clean drives).
  3. Code detail timeline: "First seen · Demo log 2 · 02:40", "Snapshot before clear", "Cleared by Owner", "Seen again".
  4. **Audit entries** (Tier 1): who, device and transport, codes before and after.
- **States:** empty: "No faults recorded for this vehicle." Offline: from the local store. Moving: locked.
- **Safety and driving rules:** read only.
- **Components:** ListRow, Chip (state), Segmented, timeline rows (as maint-timeline).
- **Spec refs:** [ADR-0033 §5][adr33-5] · [UI §4.3][ui-4.3] · [UI §12.2][ui-12.2] · [Maintenance §6][mg-6].
- **Open questions:** should a code that has been gone for 3 clean drives show here without the Maintenance add-on (the clean-drive rule lives in the add-on)?

[ui-3.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#32-the-persistent-status-strip
[ui-4.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#42-vehicle--systems--function-areas
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-13.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#132-get-help-with-this-fault-diagnose-changes-34s-diagnose-row
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[adr33-5]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#5-clearing-fault-codes-made-safe
[j1979-5]: ../../../../specs/2026-10-06-j1979-service-layer-design.md#5-mode-04-clear-dtcs-is-a-tier-1-maintenance-action
[mg-6]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#6-faults-and-manufacturer-schedules
[vds-9]: ../../../../specs/2026-10-07-visual-design-system-design.md#9-enforcement
