---
title: "Designer brief: vehicle and diagnostics (I) — Decode lab: sniff, candidates, correlate, label, verify, contribute"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-05-replay-notes-capture-design.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-trip-sharing-design.md]
summary: >
  Ninth file of the vehicle and diagnostics brief. It covers Decode lab, the developer
  add-on shown only in service mode and refused while Moving: the existing lab page with
  its Detect to Contribute stepper, and new pages for each stage on the Discovery 2 Td5:
  Sniff (byte grid with a bit-flip heat map and marks), Candidates (unsolved bytes such as
  the four SLABS settings blocks), Correlate (a candidate against a reference with R² and
  lag), Label (name, VSS path and unit, saved as candidate), Verify (the evidence
  checklist), Contribute (exact JSON preview, consent and Propose decode card on Ostler
  Community) and the per-module Coverage map.
---

# Vehicle and diagnostics brief (I): Decode lab

Decode lab is a **developer app** (app:decode-lab, `requires.mode: "service"`), with its own
drawer icon shown only while service mode is on (thick coloured frame, strip badge). Every stage is
read-only: sweeps send only `3E`, `10 01`, `22`, `19`, `1A`, `21` and inits; Parked, ignition on,
engine off; K-line always releases ([UI §8.1][ui-8.1]). While Moving it is refused and exits.
`candidate` becomes `proven` only by the evidence rules ([UI §8.3][ui-8.3]).

### decode-lab — Decode lab (Detect → Scan → Sniff → Correlate → Label → Verify → Contribute)  [Existing]
- **Purpose:** the workbench that turns raw bytes into named, proven signals for a pack.
- **Owner:** app:decode-lab
- **Opens from → goes to:** the app drawer → Decode lab (service mode); Home "Unknown vehicle — help decode it"; live-browser "Help decode it" → each stage page, decode-coverage.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night, tablet Night, hu9 Night, phone Night.
- **Content (top to bottom):**
  1. Stepper (StepProgress): **Detect · Scan · Sniff · Correlate · Label · Verify · Contribute**, each with a count ("Candidates 7").
  2. **Detect:** connection rung, adapter or node, pack match ("lr_d2 · Discovery 2 Td5"), identity source; "Unknown vehicle" path to `generic_obd2`.
  3. **Scan:** read-only module sweep with per-row progress and Stop; result rows per module: answered, protocol, LIDs found; "Saved as ecus.json, identity removed".
  4. Glossary popover (LID, `21 xx`, reference tool, sniff tap).
  5. Side panel: **Coverage** summary per module → decode-coverage.
- **States:** service mode off: the add-on is hidden. Moving: refused, "Decode lab closes while moving", exits to the Drive home page. No sniffer: Sniff shows "No sniff source". Not connected: Detect shows the failed rung.
- **Safety and driving rules:** service mode only; read-only stages ([UI §8.4][ui-8.4], [App model §14.1][am-14]).
- **Components:** StepProgress (new component), ListRow, Button, Chip, Glossary popover (new component).
- **Spec refs:** [UI §8.4][ui-8.4] · [UI §13.3][ui-13.3] · [App model §14.1][am-14] · [UI §8.1][ui-8.1].

### decode-sniff — Sniff  [New]
- **Purpose:** watch frames from the bus and see which bits move when something changes.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-lab stepper → decode-candidates (a highlighted byte), help-flow (Ask for help decoding on a frame, L3).
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night, tablet Night.
- **Content (top to bottom):**
  1. Source badge: "Sniffer · K-line" or "No sniff source — connect the sniffer".
  2. Frame list by request: "21 1A" (TD5 temperatures), "21 54" (SLABS heights) with rate and last seen.
  3. **ByteGrid** (new component): bytes as columns, time as rows, mono hex; a **bit-flip heat map** colours bits by change count (`plasma` continuous ramp, never the accent).
  4. Marks timeline with ⚑ ticks from the recording ("Rear fog on", "Rear fog off").
  5. Actions on a selection: **Make candidate**, **Ask for help decoding**.
- **States:** paused: grid frozen with "Paused". Identity frames are scrubbed and drawn as "scrubbed". Moving: refused.
- **Safety and driving rules:** listen only.
- **Components:** ByteGrid (new component), ListRow, Chip, Button.
- **Spec refs:** [UI §8.4][ui-8.4] · [UI §13.3][ui-13.3] · [Replay §6][rn-6].

### decode-candidates — Candidates  [New]
- **Purpose:** the list of unsolved bytes and proposals, ranked.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-sniff; the stepper → decode-correlate, decode-label.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Filter by module. 2. Rows from the D2 pack's real open work: SLABS "Settings 21 45 (1 byte) · raw 7f · one of 4 settings, pairing unsolved · try a differential"; SLABS "Wheel speed FL · 21 43@0 · corner order unconfirmed"; TD5 "EGR · 21 1D byte 15 · candidate". 3. Each row: request and position in mono, current proposal (formula, unit), best R², source (solver, importer, capture). 4. **Correlate**, **Label**.
- **States:** none: "No open candidates for this module".
- **Safety and driving rules:** read only.
- **Components:** ListRow, Chip, Button.
- **Spec refs:** [UI §8.1][ui-8.1] · [UI §8.3][ui-8.3].

### decode-correlate — Correlate  [New]
- **Purpose:** test a candidate against a reference signal and read the fit.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-candidates → decode-label (accept the proposal).
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night (SLABS wheel speed against GPS speed).
- **Content (top to bottom):** 1. Candidate and **reference** picker (GPS speed, an OBD value, the IMU, a proven pack signal). 2. Overlaid lines (two categorical series) and a scatter with the fitted line. 3. Results: R², lag, formula ("raw × k + b"). 4. Method Segmented: automap · bit-flip segmentation · lagged correlation. 5. **Use this proposal**.
- **States:** too little movement: "Not enough change in this window. Record the item switching on and off." Moving: refused.
- **Safety and driving rules:** read only.
- **Components:** Area line, scatter chart (new component), Segmented, StatTile, Button.
- **Spec refs:** [UI §8.1][ui-8.1] (S5).

### decode-label — Label  [New]
- **Purpose:** name a field and save it as `candidate`.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-correlate or decode-sniff → decode-verify.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Request and position ("21 1A@8"). 2. Name, VSS path picker ("Vehicle.Exterior.AirTemperature" or pack-private), unit from the VSS unit list, scale and offset, group, normal band. 3. **Read a LID directly** with the decoded value now. 4. **Save as candidate** (also saves a capture note to the recording).
- **States:** a name already used: "Already in the pack: External temp (candidate)". Moving: refused.
- **Safety and driving rules:** typing is Parked only.
- **Components:** TextField (new component), ListRow, Button.
- **Spec refs:** [UI §8.1][ui-8.1] (S6) · [Replay §6][rn-6].

### decode-verify — Verify  [New]
- **Purpose:** show what evidence a field has and what is still missing for `proven`.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-label → decode-contribute.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** EvidenceChecklist (new component): "≥ 2 distinct readings at R² ≥ 0.999 against a reference", "≥ 1 committed fixture from a real capture", "A second person's review"; each with state and link; footer "A failing fixture demotes the field".
- **States:** all met: "Ready to propose as proven". Moving: refused.
- **Safety and driving rules:** read only.
- **Components:** EvidenceChecklist (new component), Chip.
- **Spec refs:** [UI §8.3][ui-8.3].

### decode-contribute — Contribute and propose a decode card  [New]
- **Purpose:** send derived data upstream, after showing exactly what leaves.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-verify → Ostler Community decode card (in the hub add-on), Save file, or the pack's PR bundle.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. **Exact JSON preview** (mono) of the field and its short labelled fixture snippets, after scrub. 2. Consent tick, off by default: CC BY-SA 4.0 for derived data only, credit name. 3. **Propose decode card** (to the vehicle project "Land Rover Discovery 2 · Td5" on Ostler Community), **Save file**, **Make PR bundle**.
- **States:** hub add-on off: only Save file and PR bundle. Scrub found identity: blocked with the rule. Moving: refused.
- **Safety and driving rules:** nothing leaves before the preview; a card never holds a log ([Community §10.2][hub-10.2]).
- **Components:** Card (mono preview), Checkbox (new component), Button.
- **Spec refs:** [UI §8.4][ui-8.4] · [UI §13.3][ui-13.3] · [Community §10.2][hub-10.2] · [Community §10.3][hub-10.3].

### decode-coverage — Coverage map  [New]
- **Purpose:** how far each module is decoded, item by item.
- **Owner:** app:decode-lab
- **Opens from → goes to:** decode-lab side panel → decode-candidates (an item).
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. Module picker in pack order (TD5, SLABS, BCU, ACE, EAT, SRS). 2. Per page (Faults, Inputs, Outputs, Settings, Utilities) a CoverageBar with counts: verified, candidate, sniff, untranscribed. 3. Item rows with their status from the catalog.
- **States:** a module never sniffed (ACE): all rows `sniff`, "Needs a non-standard init".
- **Safety and driving rules:** read only.
- **Components:** CoverageBar (kit), ListRow, Chip.
- **Spec refs:** [UI §8.4][ui-8.4].

[ui-8.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#81-stages
[ui-8.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#83-data-evidence-fixtures-and-scrub
[ui-8.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#84-decode-mode-in-the-ui
[ui-13.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#133-ask-for-help-decoding-decode-lab-changes-84
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[rn-6]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#6-admin-decode-and-label
[hub-10.2]: ../../../../specs/2026-10-07-community-hub-design.md#102-decode-cards-and-the-workbench
[hub-10.3]: ../../../../specs/2026-10-07-community-hub-design.md#103-vehicle-projects
