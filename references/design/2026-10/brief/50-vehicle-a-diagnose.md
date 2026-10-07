---
title: "Designer brief: vehicle and diagnostics (A) — Diagnose, the module list and the module page"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/design/2026-10/README.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-shell-input-design.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  First file of the vehicle and diagnostics brief. It explains the files in this set and the
  Discovery 2 Td5 module table every Diagnose frame draws from (Td5, SLABS, BCU, ACE, EAT and
  SRS, with their real live, fault and action coverage). It then gives full page content for
  the Diagnostics app (app:diagnostics): the existing module list with identity bar and Scan all
  (diagnose-systems) and the existing module page with its six areas (diagnose-system), plus
  three new pages: the module Overview tab, the Settings tab (identity reads and Not fitted)
  and the saved scan report with its before and after pairing and export.
---

# Vehicle and diagnostics brief (A): Diagnose and modules

This set covers Diagnose, Live data, faults, actions and procedures, Trips and recordings,
the help flow, Decode lab, adapters, Places and Maintenance & Garage. Files:
**A** Diagnose and modules (this file) · [B](50-vehicle-b-faults.md) faults ·
[C](50-vehicle-c-actions.md) tests and procedures · [D](50-vehicle-d-live.md) live data and
vehicle views · [E](50-vehicle-e-help-adapters.md) help flow and adapters ·
[F](50-vehicle-f-trips.md) Trips · [G](50-vehicle-g-share-places.md) sharing and Places ·
[H](50-vehicle-h-recordings.md) recordings, notes and replay · [I](50-vehicle-i-decode.md)
Decode lab · [J](50-vehicle-j-maint.md), [K](50-vehicle-k-maint.md) Maintenance & Garage ·
[L](50-vehicle-l-apps.md) the four apps' setup flows, settings and widgets.

**Apps and owners (owner direction, 2026-10-07).** Diagnostics (`app:diagnostics`), Trips
(`app:trips`), Maintenance (`app:maintenance`) and Decode lab (`app:decode-lab`) are separate
apps, each with its own drawer icon. Confirm sheets, the running-test banner, adapters, Places
and the Garage belong to the OS (`os`). The D2 pack is an **integration**, set up on its
integration page in the app framework area (`90-appframe-*`).

## The Discovery 2 module table (draw from this, never invent)

Real data from the D2 pack (`ostler-pack-lr-d2`: `src/d2diag/__init__.py`, `actions.py`,
`menus.py`, `signals/*.json`, `dtc/*.json`). Order is the pack's display order.

| Module (pack name) | Link | Live data | Faults | Tests and procedures |
|---|---|---|---|---|
| **TD5 (engine)** | K-line 0x13, fast init | 45 signals, most `proven` (RPM, Speed, Battery, Coolant, Turbo pressure, Injection, Injector 1–5 balance, Pedal tracks) | 211 fault bits with P-codes, e.g. `5.2` coolant temp. circuit (Current) P0115 | 14 output tests, all *experimental* (Fuel pump, Glow plugs, Wastegate modulator, Injector 1–5 click); Read ECU identity |
| **SLABS (ABS + air suspension)** | K-line 0x29, fast init | 18 signals: Height left/right (raw, `proven`), wheel speeds and ABS sensors (`candidate`), Centre diff lock, Transfer box low range | 65 faults, e.g. `3.4` right front wheel speed sensor — output too low | verified: Buzzer, Compressor, Exhaust valve, ABS pump on/off; procedures: Wheel test FL/FR/RL/RR, Power bleed, Modulator bleed (4 steps), Raise/Lower left/right corner |
| **BCU (body control)** | K-line 0x40, slow init | none yet: the BCU hides inputs until security access, so every item reads "Not supported yet" | not mapped | only Tier 4 rows, listed for honesty (Read EKA code, Set EKA code, Key programming) |
| **ACE (active cornering)** | needs a non-standard init | none yet (not sniffed) | 22 known codes, `candidate`, with the caveat "ACE codes are known to be misleading" | Oil bleed (3 steps) *planned*; calibrations Tier 4 |
| **EAT (auto gearbox)** | own `72` protocol | none yet | 38 P-codes, `candidate`, e.g. P1613-1 solenoid-valve supply relay stuck open, "limp-home" | Reset adaptive values *planned* |
| **SRS (airbag)** | K-line 0x5B, slow init | none by design | 4 known codes, e.g. `004` airbag warning lamp circuit, open circuit | none; read-only by construction, no Clear offered |

K-line carries **one session at a time**: only one module is "in session"; switching moves
the session ([UI §4.2][ui-4.2]). The pack labels areas with NanoCom words: Live reads
**Inputs**, Tests reads **Outputs**, Procedures reads **Utilities** ([UI §3.4][ui-3.4]).

---

### diagnose-systems — Diagnose: identity bar, Scan all, systems  [Existing]
- **Purpose:** the module list for the active vehicle, with one honest state per module and Scan all.
- **Owner:** app:diagnostics
- **Opens from → goes to:** dock or app drawer → Diagnostics; a Diagnostics widget on a home page; the worst-telltale sheet; the home-page warnings widget; landing in service mode → a module row opens diagnose-system; Scan all → diagnose-scan-report.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night (list 380 + detail), phone Night and Day, hu7 Night-dim Idling.
- **Content (top to bottom):**
  1. **Identity bar:** vehicle name ("Discovery 2 Td5"), masked identity "SAL…****" with source chip ("from ECU" or "chosen by you"), pack chip "lr_d2 · version", Link rung chip ("ECU session: SLABS") ([UI §4.4][ui-4.4], [UI §4.5][ui-4.5]).
  2. **Scan all** primary Button; while running it becomes **Stop** with "Scanning 2 of 6 · SLABS". Caption: "One module at a time on K-line."
  3. **Systems** kicker, then one ListRow per module in pack order: icon, name ("TD5 (engine)"), meta (last read age, "12 min ago"), trailing status Chip from the one vocabulary: `Not scanned` · `Scanning` · `OK` · `Faults 2` · `No response` · `Not fitted` · `Not supported yet` ([UI §4.3][ui-4.3]). The module in session carries an "In session" tag.
  4. Footer row: **Last scan report** ListRow ("Today 09:12 · 2 faults") → diagnose-scan-report.
- **States:** empty (no pack match): "Unknown vehicle — help decode it" Card with **Open Decode lab** ([UI §8.2][ui-8.2]). Loading: row chips read `Scanning` in turn. Error: a row reads `No response · 30 s ago` with "Try again". Offline or no link: list renders last-known chips in stale grey with age, Scan all disabled, "Connect to scan" plus **Open connection**. No vehicle: "Add a vehicle in Garage". Parked: full. Idling: reading only; Scan all allowed (Tier 0). Moving: locked view (system switching is locked) with Open on phone. Passenger: not unlockable (diagnostics are not reg 109 content). Replay: chips read "Recorded".
- **Safety and driving rules:** Moving locks system switching ([UI §3.5][ui-3.5], [UI §12.1][ui-12.1]); the fault telltale stays in the strip ([Drive modes §8.1][dm-8.1]).
- **Components:** ListRow, Chip (status), Button (primary, Stop as danger), Card, StatusIdentityBar (new component).
- **Spec refs:** [UI §3.4][ui-3.4] · [UI §4.2][ui-4.2] · [UI §4.3][ui-4.3] · [UI §4.4][ui-4.4].
- **Open questions:** should a probed module the owner marked **Not fitted** stay in the list (greyed) or move under "Hidden modules"?

### diagnose-system — System areas (Overview, Faults, Live, Tests, Procedures, Settings)  [Existing]
- **Purpose:** one module's page: identity, live data, faults and actions in six areas.
- **Owner:** app:diagnostics
- **Opens from → goes to:** a diagnose-systems row; a fault telltale → its Faults area → diagnose-overview, diagnose-faults, live-browser, diagnose-tests, diagnose-procedures, diagnose-settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night with list pane, phone Night (compact switcher), phone Day.
- **Content (top to bottom):**
  1. **Header:** module name ("SLABS (ABS + air suspension)"), status Chip, "In session · 2 min" or **Move session here** (secondary Button, Parked or Idling).
  2. On phone and HU-5/7: a compact **current system** switcher (Chip with chevron) replaces the list pane.
  3. **Area tabs** (Segmented on phone, TabBar row on tablet and head unit), pack labels: Overview · Faults · Inputs · Outputs · Utilities · Settings. An area with no items is not drawn; a declared but unmapped area shows `untranscribed` ([UI §3.4][ui-3.4]). SRS shows Overview · Faults · Settings only.
  4. **Area body** (see each area's block).
  5. **ActiveTestBanner** pinned at the top of every area while a test runs (diagnose-active-test).
- **States:** loading: skeleton rows. Offline: stale values in grey with age; actions disabled with "Not connected — actions are disabled until the module answers". Session elsewhere: "Values from TD5 are not in this session. Move session here." Parked: full. Idling: Maintenance (clear codes) with Park evidence. Moving: locked view, Open on phone. Replay: lock icon and the word "replay" on every action.
- **Safety and driving rules:** Moving locks the page ([UI §12.1][ui-12.1]); action tiers in [UI §7][ui-7].
- **Components:** Segmented, TabBar, Chip, Button, ListRow.
- **Spec refs:** [UI §4.2][ui-4.2] · [UI §7][ui-7].

### diagnose-overview — Module Overview area  [New]
- **Purpose:** the first area of a module: what it is, its health and its key values at a glance.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-system default area → diagnose-faults (fault count), live-signal (a stat tile), live-vehicle-slabs or live-vehicle-body (vehicle view), diagnose-settings (identity).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night for TD5, phone Night and Day for SLABS.
- **Content (top to bottom):**
  1. **Health Card** (tone variant only when abnormal): "2 faults · 1 current" with chevron; OK reads "No faults · read 3 min ago".
  2. **Key values** stat grid (3 columns), from the pack's role tiles: TD5 Coolant °C, Turbo pressure bar, Battery V, Intake air °C; SLABS Height left, Height right (raw), Battery V. Each StatTile shows `candidate` as a dashed underline and stale in grey with age.
  3. **Vehicle view** Card (Proposed pages in [D](50-vehicle-d-live.md)): a small silhouette thumbnail for SLABS and BCU, "Open vehicle view".
  4. **Coverage** line: "Live 31 of 45 proven · Faults 211 · Tests 14 experimental" (service mode shows the CoverageBar).
  5. **Identity** short rows: protocol "KWP2000 · K-line 0x13", last identity read time; "Full identity" → diagnose-settings.
- **States:** module not live (BCU, ACE, EAT): key values replaced by "Live data is not supported yet for this module" with **Help decode it** (opens Decode lab in service mode, or the help flow at L3). SRS: "Read-only module. Faults only." Offline: stale grey. Moving: locked.
- **Safety and driving rules:** read only (Tier 0).
- **Components:** Card (tone), StatTile, Chip, ListRow, CoverageBar (service mode only).
- **Spec refs:** [UI §4.2][ui-4.2] · [UI §5.3][ui-5.3] · [UI §5.4][ui-5.4] · [Visual §8][vds-8].

### diagnose-settings — Module Settings area  [New]
- **Purpose:** identity reads and module settings, read only, plus Not fitted.
- **Owner:** app:diagnostics
- **Opens from → goes to:** diagnose-system → Settings; diagnose-overview identity row.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):**
  1. **Read ECU identity** secondary Button (TD5; Tier 0, "Ignition on"). Result rows: part and software numbers; the VIN row reads "VIN read on the ECU only · never stored" with the masked form "SAL…****" ([UI §4.4][ui-4.4]).
  2. **Settings** list from the pack menu: SLABS "Settings 21 45 (1 byte)" … each with a `candidate` Chip and the raw byte in mono ("7f"); "Left/Right stored height" reads `untranscribed`.
  3. **Get security status** (TD5, read only) row with its result.
  4. **This module is not fitted** toggle (only for probed modules that never answered), Parked.
  5. Replay variant: only "Identity read at 09:14:03".
- **States:** not read yet: "Not read in this session". Offline: last read with age. Moving: locked.
- **Safety and driving rules:** reads only; identity replies are never recorded ([UI §4.4][ui-4.4]).
- **Components:** ListRow, Chip, Button (secondary), Toggle (new component).
- **Spec refs:** [UI §4.2][ui-4.2] · [UI §4.4][ui-4.4].

### diagnose-scan-report — Scan report  [New]
- **Purpose:** the saved result of Scan all, kept in Trips, paired before and after a repair.
- **Owner:** app:diagnostics
- **Opens from → goes to:** Scan all finishing; diagnose-systems footer; a scan-report row in Trips (All events) → diagnose-fault (a code), help-flow (Share at L4), trips-list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night, hu9 Night.
- **Content (top to bottom):**
  1. Title "Scan report", date and time, vehicle name, masked identity "SAL…****".
  2. Summary Chips: "6 modules · 2 with faults · 1 not supported yet".
  3. One Card per module in scan order: status Chip, codes with Current/Logged and freeze frame where the protocol has one, key values **with confidence** (`proven` or `candidate`), actions run during the scan.
  4. **Pair** section: "Before repair · 3 Oct" and "After repair · today" side by side with codes gone, new and still present.
  5. Actions: **Export** (HTML, JSON), **Share…** (opens the help flow at L4), **Mark as before repair**.
- **States:** partial scan (stopped): "Stopped at SLABS · 2 of 6 scanned". Empty: "No scans yet. Scan all from Diagnose." Offline: still readable (stored). Moving: locked.
- **Safety and driving rules:** read only; uploads are opt-in ([UI §4.3][ui-4.3]).
- **Components:** Card, Chip, ListRow, Button.
- **Spec refs:** [UI §4.3][ui-4.3] · [UI §12.2][ui-12.2].
- **Open questions:** should Export also offer the PDF print layout the Maintenance export bundle uses?

[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-4.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#42-vehicle--systems--function-areas
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-5.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#53-three-rendering-tiers
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-8.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#82-generic_obd2-and-unknown-vehicle--help-decode-it
