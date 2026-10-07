---
title: "Designer brief: vehicle and diagnostics (C) — actuator tests, procedures and approvals"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, decisions/adr-0033-action-categories-and-approvals.md, specs/2026-10-07-source-adapters-design.md]
summary: >
  Third file of the vehicle and diagnostics brief. It covers car actions on the Discovery 2
  Td5 with the ADR-0033 tiers and categories: the module's Tests area (Outputs) listing real
  pack actions with tier, status and Parked requirements; the running-test banner with Stop
  and auto-timeout; phone approval of Tier 2 and 3 over local links; the Procedures area
  (Utilities) including Tier 4 rows listed for honesty; and a multi-step procedure flow
  (start with typed confirm, each step with progress, re-checked preconditions, 12 V floor
  and Abort, then the end screen). All screens are new pages under approved UI spec §7.
---

# Vehicle and diagnostics brief (C): tests, procedures and approvals

**Tiers and categories** ([UI §7][ui-7], [UI §7.1][ui-7.1]): Tier 0 Read (all states) ·
Tier 1 Clear and Maintenance (Parked, or Idling with Park evidence) · Tier 2 Actuate, category
Actuator tests (Parked; Idling only if the action declares `engine_running_ok`) · Tier 3
Procedure (Parked, typed confirm) · Tier 4 Code (listed, never runnable). Roles: Owner up to
Tier 3; Driver no actuator tests; Mechanic time-boxed; the head-unit kiosk session gets Read and
Comfort only.

### diagnose-tests — Module Tests area (Outputs)  [New]
- **Purpose:** list and run a module's actuator tests with their tier friction.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-system → Outputs; diagnose-fault "Related tests" → diagnose-confirm (Tier 2) → diagnose-active-test.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night (SLABS), phone Night (TD5), phone Day.
- **Content (top to bottom):**
  1. Kicker "Actuator tests · Parked only", with a one-line rule: "Vehicle stationary, handbrake on, ignition on, nobody under the car."
  2. One ListRow per test in pack order: name, status Chip (`verified` · `experimental` · `planned`), tier Chip ("Tier 2"), trailing **Run** Button (secondary). SLABS: Buzzer test, Compressor test, Exhaust valve test, ABS pump on (latched; its Stop is "ABS pump off"). TD5: Fuel pump, MIL lamp, A/C clutch, A/C fan, Glow plugs, Rev counter, Temp gauge, EGR throttle, Wastegate modulator, Injector 1–5 click (all `experimental`, "Engine off").
  3. `planned` rows show "Not implemented yet" instead of Run.
  4. Replay variant: the row whose test ran at the cursor is highlighted, each row shows "ran at 09:14:03" with a check or cross icon and word ([Replay §4][rn-4]).
  5. Empty module (SRS): "No output tests by design. Airbag outputs are never activated."
- **States:** not connected: Run disabled with "Connect to run tests". Role without the category (Driver): rows visible, Run replaced by "Needs Owner or Mechanic". Idling: Run disabled "Switch the engine off". Moving: locked view. Remote link: "Read only over a remote link". Adapter with no node and opt-in off: "Adapter actions are off" → adapter-soft-gate.
- **Safety and driving rules:** Tier 2, Parked ([UI §7][ui-7]); refused while Moving; experimental shown on the button and in the confirm.
- **Components:** ListRow, Chip (status, tier), Button (secondary), ActiveTestBanner (kit component).
- **Spec refs:** [UI §7][ui-7] · [UI §7.1][ui-7.1] · [UI §4.2][ui-4.2].

### diagnose-active-test — Running test banner and Stop  [New]
- **Purpose:** say on every screen that a test is running, with Stop.
- **Owner:** os
- **Opens from → goes to:** diagnose-confirm (Run test) → stays on top of every page until Stop, timeout or leaving.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night over diagnose-tests, phone Night over diagnose-overview.
- **Content (top to bottom):**
  1. Banner (`warn-bg` with `warn` edge): icon `bolt`, "**ABS pump on** is running · 0:07", **Stop** (danger, large: 48 px phone, 76 px head unit).
  2. Live values that the test moves, when the pack links them (Compressor test: Height left and right).
  3. End line after Stop: "Stopped · ABS pump off sent"; after timeout: "Stopped by itself after the time limit"; after leaving the screen: "Stopped because you left the page".
- **States:** link lost: "Link lost — the module stops the test on its own timeout" in `alarm`. Phone approval: Stop also on the phone (diagnose-phone-approve). Moving starts: the node stops the test and the banner reads "Stopped: vehicle moving".
- **Safety and driving rules:** auto-timeout; leaving stops it ([UI §7][ui-7]); alarm pulse is the only motion.
- **Components:** ActiveTestBanner (kit component), Button (danger), StatTile.
- **Spec refs:** [UI §7][ui-7] · [ADR-0033 §6][adr33-6].

### diagnose-phone-approve — Approve on phone  [New]
- **Purpose:** let a paired phone approve a Tier 2 or 3 action asked for on the head unit or Brain.
- **Owner:** os
- **Opens from → goes to:** a Tier 2–3 request on another display of the same car → the phone sheet → diagnose-active-test or the procedure flow (on the phone, with Stop).
- **Layout classes:** phone · tablet. **Draw first:** phone Night, phone Day.
- **Content (top to bottom):**
  1. Title "Approve Compressor test on SLABS?" and "Asked from the head unit · 09:14".
  2. Link line: "Over the car's Wi-Fi (local)"; the node re-checks Parked and the preconditions.
  3. The same precondition checklist as diagnose-confirm.
  4. **Cancel** (focused) · **Approve**; after approval the phone shows **Stop** for the whole action.
- **States:** remote link: no approve button, "Approvals work only on the car's own links". Role lacks the category: "Your role cannot approve actuator tests." Phone link lost during the action: the action stops, "Stopped: phone link lost".
- **Safety and driving rules:** local links only; an accept inside an AI client never counts ([UI §7.2][ui-7.2], [ADR-0033 §6][adr33-6]).
- **Components:** Sheet, Checklist (new component), Button (Cancel focused).
- **Spec refs:** [UI §7.2][ui-7.2] · [ADR-0033 §6][adr33-6].

### diagnose-procedures — Module Procedures area (Utilities)  [New]
- **Purpose:** list service procedures and the actions that are listed but never sent.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-system → Utilities → diagnose-procedure-start.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night (SLABS), phone Night (BCU with Tier 4 only).
- **Content (top to bottom):**
  1. **Procedures** (Tier 3, Parked only) as ListRows with status Chip and step count: SLABS "Modulator bleed (4 steps)", "Power bleed — start" (latched, stop "Power bleed — stop"), "Wheel test FL/FR/RL/RR", "Raise left corner", "Raise right corner", "Lower left corner", "Lower right corner"; ACE "Oil bleed (3 steps)" `planned`; EAT "Reset adaptive values" `planned`.
  2. **Utilities** (Tier 0): TD5 "Read ECU identity", "Get security status".
  3. **Listed for honesty · never sent** (Tier 4, collapsed): "Store target heights", "Learn security code", "Read EKA code", "Set EKA code", "Key programming", "Calibrate accelerometer 1 and 2", "Set calibrated", each with its reason ("writes calibration — needs its own ADR").
  4. Service mode only: **Advanced** (raw block dump) → Decode lab Label.
- **States:** as diagnose-tests; Idling: "Switch the engine off"; Moving: locked view.
- **Safety and driving rules:** Tier 3 Parked, typed confirm; Tier 4 refused by the server ([UI §7][ui-7]).
- **Components:** ListRow, Chip (status, tier, "never sent"), disclosure row.
- **Spec refs:** [UI §7][ui-7] · [UI §4.2][ui-4.2].

## Flow: run a procedure (example: SLABS Modulator bleed, 4 steps)

| Step | Screen | The user | What can fail and the recovery |
|---|---|---|---|
| 1 | diagnose-procedure-start | reads, ticks preconditions, types the name, Start | not Parked, 12 V low, session elsewhere: Start disabled with the reason |
| 2–5 | diagnose-procedure-step | follows step *n* of 4, presses Next | precondition breaks, 12 V under the floor, link lost, Moving: the step stops and offers Abort or Retry step |
| 6 | diagnose-procedure-end | reads the result, Done | aborted: lists what ran and what to check |

### diagnose-procedure-start — Procedure start  [New]
- **Purpose:** explain the procedure and collect its Tier 3 friction.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-procedures → diagnose-confirm (typed) → diagnose-procedure-step; Cancel → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night, phone Night.
- **Content (top to bottom):** 1. Title "Modulator bleed", module "SLABS", `verified` Chip, "4 steps · Parked only". 2. **What it does** (pack text). 3. **Before you start** checklist: "Vehicle stationary, handbrake on", "Ignition on", "Nobody under or beside the car", "Brake bleed in progress (fluid topped up, bleed nipples ready)". 4. **12 V** live StatTile with floor line. 5. **Start** → typed confirm (diagnose-confirm Tier 3).
- **States:** pack step texts missing: "Step texts not written yet" and Start disabled. Moving: locked.
- **Safety and driving rules:** [UI §7][ui-7] Tier 3; typed confirm Parked only ([Shell input §7][si-7]).
- **Components:** Card, Checklist (new component), StatTile, Button.
- **Spec refs:** [UI §7][ui-7].

### diagnose-procedure-step — Procedure step  [New]
- **Purpose:** one step at a time, with progress and Abort always visible.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-procedure-start → next step → diagnose-procedure-end; Abort → diagnose-procedure-end (aborted).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night step 2 of 4, phone Night, hu7 Night-dim (Parked).
- **Content (top to bottom):** 1. StepProgress (new component): "Step 2 of 4" with four segments. 2. Step instruction from the pack (≤ 3 short lines) and its live values (Battery V, the moving height). 3. Status line: "Running · 0:12" then "Step done". 4. Preconditions re-checked each step as compact Chips. 5. **Abort** (danger, always present) and **Next** (primary, enabled when the step is done).
- **States:** 12 V below the floor: step stops, `alarm` Card "Battery is below the floor (value in V). Connect a charger, then Retry step." Link lost: "Link lost — the module ends the step on its own." Moving: the gate stops it ("Stopped: vehicle moving").
- **Safety and driving rules:** preconditions re-checked each step, 12 V floor, abort anywhere ([UI §7][ui-7]).
- **Components:** StepProgress (new component), Button (danger, primary), Chip, StatTile, Card (alarm tone).
- **Spec refs:** [UI §7][ui-7].

### diagnose-procedure-end — Procedure finished or aborted  [New]
- **Purpose:** report the outcome and what was logged.
- **Owner:** app:diagnostics
- **Opens from → goes to:** the last step or Abort → diagnose-procedures, diagnose-faults (re-read).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night (done and aborted).
- **Content (top to bottom):** 1. "Modulator bleed finished" (`ok` icon and word) or "Aborted at step 3 of 4" (`warn`). 2. Steps list with done or not run. 3. "Logged to Trips with before and after values". 4. **Read faults** (secondary), **Done**.
- **States:** aborted by the car: the refusal text from the gate.
- **Safety and driving rules:** every Tier 1+ action is logged with before and after values ([UI §7][ui-7]).
- **Components:** Card, ListRow, Button.
- **Spec refs:** [UI §7][ui-7] · [ADR-0033 §5][adr33-5].
- **Open questions:** the D2 pack has no per-step texts for Modulator bleed yet; should Start stay disabled until the pack supplies them?

[ui-4.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#42-vehicle--systems--function-areas
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[adr33-5]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#5-clearing-fault-codes-made-safe
[adr33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[rn-4]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#4-whole-app-replay-ui
