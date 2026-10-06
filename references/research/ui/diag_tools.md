---
title: "Diagnostic-tool UX: how pro and enthusiast scan tools structure vehicle → system → function, and what Ostler should copy"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/landscape.md]
summary: >
  A survey of Autel, Launch, Snap-on, Bosch, Topdon, VCDS, the Land Rover tools (NanoCom, Faultmate, HawkEye, IIDTool) and open tools (OpenVehicleDiag, ddt4all, pyren, python-OBD, ScanTool.net). They all use vehicle → system list → function menu, plus a whole-car scan that becomes a report. We recommend a hierarchy that drops the system level when a vehicle has one ECU, a seven-state scan vocabulary, a connection ladder, and five safety tiers that make writes reversible.
---

# Diagnostic-tool UX and information hierarchy

## How this was made

- **Sources.** Public manuals, vendor training pages, forum reviews and READMEs, read on
  2026-10-05/06. Every claim links to a source in [Sources](#sources).
- **Manuals read in full.** The Autel MaxiSys MS919S2 manual (330 pp) and the Topdon
  Phoenix Elite manual. The others come from vendor pages, training transcripts or
  third-party summaries.
- **NanoCom.** It has no public manual. Its menu split comes from our own
  [UI overhaul spec](../../../specs/2026-10-05-ui-overhaul-design.md) and from forum posts.
- **Scope.** This is about UX patterns only. We copy no code, databases or artwork, and
  no screen layout pixel for pixel.

## 1. What each tool does

| Tool | Entry | Hierarchy | Per-system function menu | Whole-car scan |
|---|---|---|---|---|
| **Autel MaxiSys** | VID drop-down: Auto Detect (VIN), Manual Input, camera scan of VIN or plate; else make → model → capacity → engine → year [A1] | Vehicle → nav bar (Auto Scan · Control Unit · Service · Hot Functions · Programming) → system → functions [A2] | ECU Information · Trouble Codes (read/erase) · Live Data · Active Test · Special Functions [A3] | Auto Scan with Topology and List tabs; colours and four result states [A4] |
| **Launch X431** | Intelligent Diagnosis (VIN over the VCI, manual VIN, camera) or Local Diagnosis (make/model/year) [L1] | Health Report/Quick Test · System Scan · System Selection [L1] | Version Information · Read Fault Code · Clear Fault Memory · Read Data Stream · Actuation Test · Special Function [L1] | Faulted systems red, OK systems black. Reports tagged Pre-Repair / Post-Repair / Diagnostic Scan [L1] |
| **Topdon Phoenix** | AutoScan reads the VIN; fallback VINSCAN (camera or typed, with a format rule) or manual make/model/year [T1] | Topology **or** list view of the same systems, "switch according to personal preference" [T1] | Version Information · Read Fault Code · Clear · Read Data Stream … [T1] | Smart Scan: health report, systems with DTCs in red [T1] |
| **Snap-on ZEUS** | Vehicle ID from the PCM link [S1] | Vehicle → Code Scan → **code** → cards [S2] | Per code: TSBs · Top Repairs · Smart Data (only PIDs relevant to the code) · Functional Tests · Guided Component Tests [S2] | One-touch full-vehicle Code Scan and Clear [S3] |
| **Bosch KTS/ESI[tronic]** | KBA key or VIN, about 20 s [B1] | System overview → double-click a system → ECU diagnosis [B1] | ECU id, codes, parameters, actuators, adjustments [B2] | "Up to 60 ECUs … in less than a minute" on some brands [B2] |
| **VCDS (VAG)** | Chassis type (VIN digits 7–8) or Auto Detect on CAN cars [V1] | Select Control Module → module → functions [V2] | Measuring blocks, coding, adaptation | Auto-Scan "can take several minutes" (non-CAN). Faulted modules in red [V3][V1] |
| **NanoCom Evolution** | Unlock per vehicle kit (Td5/V8, SLABS, BCU, ACE, Autobox, Airbag) [N1] | Vehicle → module → page | Faults · Inputs · Outputs · Settings · Utilities [N2]. Settings can be saved to SD and reloaded [N3] | Per module, no car-wide scan in our notes |
| **Faultmate MSV-2** | Reads the VIN and **locks** a single-vehicle licence to it [F1] | "Vehicle Explorer", with systems in a left menu [F1] | Faults · live data · component control · EAS height settings [F1] | Readouts saved as editable HTML [F1] |
| **HawkEye Total** | Model menu (Defender to Evoque, "tested on vehicles up to 2014") [H1] | Model → system | Read/clear codes · live data · actuators · ECM data · service reset [H1] | — |
| **GAP IIDTool** | Per model | Per system | Codes plus many convenience **configuration** toggles (relock, alarm beeps, Nav on the go) [G1] | — |

## 2. The shared hierarchy

Every professional tool converges on one tree. Only the entry point and the names differ.

```
Vehicle identity (auto VIN → fallback manual make/model/year/engine → generic OBD-II)
└─ Whole-car view: scan all systems → topology or list → report
└─ System (control unit) list
   └─ Function menu: Identification · Codes (read/clear, freeze frame) · Live data
                     · Active/actuation tests · Special/service functions · Coding/programming
```

**Observations:**

- **Identity first, with a ladder of fallbacks.** Autel goes VIN auto-detect → manual VIN
  → camera → manual tree → OBD-II direct entry "for vehicles not included in the database"
  [A1][A5]. Topdon and Launch follow the same order [T1][L1]. Manual selection always asks
  for **engine and capacity**, not just the model, because these decide which systems exist
  [A1].
- **Two ways in are always present.** These are the whole-car scan and pick-one-system.
  Autel shows them side by side in its nav bar as "Auto Scan" and "Control Unit" [A2]. Launch
  does the same with "System Scan" and "System Selection" [L1].
- **The function menu is fixed, but items appear only when supported.** Autel: "Available
  functions may vary by vehicle … Only the available operations display" [A3][A6]. Topdon:
  "available only when the diagnostic software supports it" [T1]. Names vary by brand. Autel
  admits that Special Functions "may sometimes appear as Control Unit Adaptations, Variant
  Coding, Configuration" [A3]. So a fixed set of canonical function areas with brand-specific
  labels is industry practice.
- **Snap-on pivots on the code, not the module.** After a code scan you pick a code, and
  every card is scoped to it, including a Smart Data PID list that "filters out all the
  non-relevant PIDs" [S2]. This is a second axis, fault → related data/tests, layered on top
  of the module tree.
- **Land Rover enthusiast tools are module-first and flat.** NanoCom's
  Faults/Inputs/Outputs/Settings/Utilities [N2] matches the generic menu one to one. Inputs
  is Live data, Outputs is Active test, Settings is Coding, and Utilities is Special
  functions.

## 3. Auto-scan, topology and the health report

- **Result vocabulary.** Autel's list tab uses four states: *Fault | #*, *Pass | No Fault*,
  *Not Scanned* and *No Response*. On the topology the colours are green, red with a count
  badge, grey for no response and blue for not scanned. A total fault count sits top right
  [A4]. Launch and Topdon reduce this to red against black [L1][T1]. VCDS uses "Malfunction"
  in red on the gateway list [V4].
- **Topology is a view, not a level.** Topdon offers topology and list "with the same
  functions" [T1]. Autel draws a topology only "for a number of vehicle brands", and the
  list is always there [A4]. Selecting a node opens a side panel with ECU description, DTCs,
  location graphic and a ping test, and an **Enter System** button [A4].
- **Scan controls.** Autel offers Fault Scan, Pause, Quick Erase, Report and Enter System
  [A4].
- **Plausible-module lists.** On non-CAN cars VCDS cannot discover modules. You pick a
  chassis type "that contains only those modules that are plausible", because "no one car
  has all Modules" [V1]. A K-line D2 is in the same position. There is no gateway to ask,
  so the pack must declare the candidate list and each one must be probed.
- **Health report = a scan snapshot.** Autel pairs a pre-scan and a post-scan under one
  repair-order number into a single PDF. The pre-scan cannot be redone or edited [A7].
  Launch tags reports Pre-Repair / Post-Repair / Diagnostic Scan [L1]. Bosch's "Protocol"
  report gathers ECU ids, codes, erasures, parameter values, graph screenshots, actuator
  tests and adjustments. It is editable with customer, job and advisory notes, then exported
  as PDF or printed [B2].

## 4. One ECU versus fifty

- **Fifty:** a scan, then a list or topology filtered by fault state, plus search. Bosch
  scans up to 60 ECUs in under a minute on CAN [B2]; older cars take "several minutes" [V3].
- **One (generic OBD-II):** Autel's OBD-II path has **no system list**. After protocol
  auto-detect it goes straight to DTC & FFD, I/M readiness, live data, monitors, component
  test and vehicle info [A5]. python-OBD treats the car as one command space: support comes
  from the PID bitmaps, and unsupported commands return a null response [P1].
- **So the collapse already ships:** one vendor shows a module tree for make-specific
  diagnosis and a flat menu for OBD-II [A2][A5].

## 5. Unknown and unsupported data

| Pattern | Who | Lesson |
|---|---|---|
| Hide what is unsupported | Autel, Topdon [A6][T1] | Clean, but the user cannot tell "not supported by the car" from "not supported by the tool" |
| Educated guess when the label file is missing | VCDS: "base the elaboration on an educated guess" [V5] | Show raw or guessed values, **marked as guessed** |
| Community mapping of unknown modules | VCDS Control Module Maps are user-submitted, "PLB/PLA/CSV" sent with an Auto-Scan [V6] | The same loop as our sniff → candidate → verified pipeline |
| Null response; `force` to try anyway | python-OBD [P1] | Distinguish *not advertised* from *advertised but empty* |
| No Response / Not Scanned states | Autel [A4] | Never let an unscanned system look healthy |
| Expert mode gate for raw access | ddt4all: non-expert mode "is meant to be harmless" [D1]; pyren "be very careful in expert mode" [R1] | Raw or unknown writes belong behind an explicit mode |

Our status model (verified / candidate / sniff / untranscribed, ADR-0008) is **more honest
than any commercial tool surveyed**. None of them shows confidence per value. Keep it, and
make it survive into reports.

## 6. How dangerous functions are gated

- **Message classes.** Autel separates *Confirmation* (irreversible or already started),
  *Warning* ("irreversible change or loss of data", e.g. Erase Codes) and *Error* (cable
  or communication loss) [A8].
- **Erase codes:** a data-loss warning, preconditions (ignition ON, engine off), then a
  re-read to verify [A9]. **Active tests:** named tests, on-screen instructions, explicit
  ESC to stop [A10]; ZEUS states preconditions (idle, warm, loads off) [S2].
- **Coding:** current value beside the edit, "check the vehicle condition and the coding
  information carefully", one **Send**, then a completion status [A11]. **Programming:**
  battery maintainer, no ignition-off, a failed flash "can also ruin the control module" [A12].
- **Backup and restore:** pyren "save dump of ECU configuration … compare … rollback" [R1];
  VCDS "Restore original value" [V4]; NanoCom saves Td5 settings (injector codes) to SD [N3].
- **Licence/VIN lock** (Faultmate [F1]) is a business gate, not safety. Do not copy it.
- **Friction matches consequence.** Overused confirmations get clicked through ("if you
  cry wolf too many times"); use specific wording, action-named buttons, and undo [NN].

## 7. Keeping session and connection state visible

Autel keeps a status bar on every diagnostic screen with network, VCI link and **vehicle
battery** icons [A13], plus a breadcrumb "current directory path" [A2]. python-OBD exposes
a ladder, *Not Connected → ELM Connected → OBD Connected → Car Connected*, where each step
names the link that failed [P1]. VCDS greys out every function until the interface is tested
[V2]. Launch shows the Bluetooth pairing state to the VCI before diagnosis [L1]. K-line
carries one session at a time, so our indicator must also name **which module holds the
session**. ModuleSelect already warns about this when recording.

## 8. Report export

Autel saves PDFs to Data Manager and shares cloud reports by QR, email or link, with an
upload badge and retry [A14]. VCDS copies or saves text to Logs/Scans and loses unsaved
output on close [V1][V3]. Bosch exports an editable protocol with customer and job fields
to PDF or print [B2]. Faultmate saves HTML that can be edited and reloaded [F1]. ZEUS keeps
screenshots, PID data, scope movies and Code Scan reports in a Data Manager [S1]. For us, a
local-first export is a **self-contained HTML/PDF** for humans plus **JSON** for machines,
with no cloud.

## 9. Open tools: licences and what is reusable

| Project | Licence (checked) | Reuse stance |
|---|---|---|
| OpenVehicleDiag | GPL-3.0 (LICENSE file) [O1] | Ideas only (ECU → variants → functions schema). Its SMR-D parser was removed by DMCA [O1] |
| ddt4all | GPL-3.0-or-later (README badge; no root LICENSE found) [D1] | UX ideas (expert-mode switch, auto-scan). Its ECU databases are user-supplied Renault dealer data: **never ship** |
| pyren | **No licence file**, so all rights reserved [R1][R2] | **Do not copy code.** It needs the CLIP/DDT2000 dealer DBs: **never ship** |
| python-OBD | LICENSE text GPLv2. Source headers say "version 2 … or (at your option) any later version", so GPL-2.0-or-later [P2][P3] | AGPL-compatible through "or later", but **we need no code from it**. Take the status ladder and supported-PID idea only |
| ScanTool.net OBD-II software | GPL-2.0-or-later (U) [ST] | Historical reference only |
| SAE J1979 PIDs, OBDb | Standard, and CC BY-SA (see landscape.md) | The data path for a generic OBD-II pack |

Commercial tools (Autel, Launch, Snap-on, Bosch, Topdon, NanoCom, Faultmate, HawkEye, GAP)
are closed. We learn from their **public manuals** and **sniffed protocol behaviour on our
own car** only. We do not copy their texts, icons, DTC descriptions or databases.

## 10. Recommended hierarchy for Ostler

**The tree.** It is the same everywhere, and the levels collapse when they carry no
information.

```
Diagnose
├─ Identity bar: pack/vehicle · variant · VIN (if readable) · connection ladder · battery V
├─ Scan  (whole-car health; becomes a Report)
├─ Systems  ← shown only when the pack declares >1 system
│   └─ <System>  ← header shows status chip + coverage
│       └─ Function areas: Overview · Faults · Live · Tests · Procedures · Settings
└─ Fault → related (cross-cutting: a fault opens its related Live items and Tests)
```

**Canonical function areas.** A pack maps them to its own labels, as Autel does [A3].

| Canonical | D2 label today (NanoCom) | OBD-II | Safety class |
|---|---|---|---|
| Overview | (ident in Settings) | Vehicle info (Mode 09), readiness | read |
| Faults | Faults | DTC & FFD: stored · pending · permanent | read, plus *clear* (confirm) |
| Live | Inputs | Mode 01 PIDs | read |
| Tests | Outputs | Mode 08 component test (rare) | actuator |
| Procedures | Utilities | — (hidden) | service / gated |
| Settings | Settings | — (hidden) | gated (write) |

**Collapse rules.** The pack manifest drives these. No vehicle-specific UI code.

1. **One system** (generic OBD-II, a single-ECU car): drop the Systems level. Diagnose opens
   straight on the function areas, as Autel's OBD-II menu does [A5]. The system name becomes
   a subtitle. When several emission ECUs answer on CAN (e.g. 7E8/7E9), show the source as a
   **tag on each code or value**, not as a module level, matching python-OBD's single
   command space [P1].
2. **2–12 systems** (D2 = 6): a flat **list** with one status chip per row and a fault count,
   as in Autel's List tab [A4]. No topology. On phones this replaces the header
   ModuleSelect. On a wide head unit it becomes a left rail, like Autel's nav bar [A2]. The
   header keeps a compact "current system" switcher so you can jump between systems.
3. **More than 12 systems**: group by domain (powertrain · chassis · body · comfort ·
   safety), collapse groups with no faults, and add search. Offer topology **only if** the
   pack declares bus wiring, since topology is an optional view of the same list [T1][A4].
4. **Empty function areas disappear.** An area that exists but is unmapped stays visible with
   an honest placeholder (`untranscribed`). Never fake support.
5. **Variants decide the candidate list.** Manual selection asks only for what changes the
   topology, such as engine, gearbox and ACE fitted. On K-line there is no gateway, so the
   pack lists plausible systems, as VCDS chassis types do [V1]. A probed system can then be
   marked **Not fitted** by the user.

**Scan states.** Use one vocabulary in the scan, the system list and reports:
`Not scanned` · `Scanning` · `OK` · `Faults n` · `No response` · `Not fitted` ·
`Not supported yet`. The first five follow Autel [A4]. The last two are ours and separate
"absent from the car" from "absent from the tool" (§5). An unscanned or non-responding
system is **never** shown as OK. K-line scans are sequential, so each row shows its own
progress, with Pause/Stop [A4].

**Report.** A Scan saves a report session into Logs and can be paired **before/after
repair** [A7][L1]. It holds the identity bar, a row for every system (non-responders
included), codes with freeze frame, key values **with their status** (verified/candidate),
and every action performed, as Bosch's protocol does [B2]. Export as self-contained
HTML/PDF and JSON through the OS share sheet; uploads are opt-in.

## 11. Recommended safety gating

Use **five tiers** on the existing safety classes (`read | actuator | service | gated`) and
apply them identically on every path. That includes the UI, MQTT, HA and schedules, and
remote paths stay read-only by default (ADR-0033 §6: phone approval over local links only; install override for developers).

| Tier | Examples | Gate |
|---|---|---|
| 0 Read | codes, live, ident | None. Values go **stale-grey** the moment the session drops |
| 1 Clear codes | erase DTCs | One specific confirm: "Clear 3 codes from SLABS? Freeze frames will be lost." It offers to save a report first, then re-reads to verify [A9][NN] |
| 2 Actuator | lamps, relays, pump, injector test | Precondition checklist taken from **live data** (ignition on, engine off or idle, speed 0) [A9][S2]. A persistent **ActiveTestBanner** with Stop. An auto-timeout. Navigating away stops the test |
| 3 Procedure | bleed, height calibration, adaptive reset | Step wizard with preconditions re-checked at every step, a battery-voltage floor [A12], and abort at every step |
| 4 Write / coding | settings, injector codes, key/security | **Automatic backup before write** and a **diff view** (current against new) [A11]. Hold-to-confirm or a typed module name. A **Restore** button keeps the last backup [R1][V4][N3]. Experimental mode only, unlocked per session and server-enforced. Verified items only in Stable |
| (5 Flash) | reprogramming | Out of scope. If ever added: battery maintainer required, no-ignition-off warning, and recovery path documented [A12] |

**Cross-cutting rules:**

- **Confirm only at tier 1 and above.** Write the consequence and the module into the text,
  and name buttons after the action ("Clear codes" / "Keep"), never "Yes/No" [NN].
- **Block tiers 2–4 when the vehicle is moving or the link is degraded** (any rung below
  "ECU session" on the ladder).
- **Expert mode is a visible state, not a hidden setting.** Default to harmless, as
  ddt4all's non-expert mode is [D1]. Show a header badge while it is on.
- **Candidate-status actions carry their status** on the button and in the confirm text.
- **Log every tier-1+ action** into the session and the report, with before/after values.

**The connection ladder** goes in the header pill and expands in the ConnectionSheet:
`No adapter → Adapter → Bus (K-line init / CAN) → ECU session: <module>`, plus **battery
V**. It mirrors python-OBD [P1] and Autel's VCI and battery icons [A13], and adds the
active-session name that K-line needs.

## 12. Do not copy

- **Dealer or vendor databases:** DDT2000/CLIP, ODX/CBF/SMR-D, Autel or Launch DTC text.
  There is DMCA precedent with OpenVehicleDiag [O1].
- **Code from pyren** (no licence) or from GPL-2.0-only projects. Treat any project whose
  headers lack "or later" as GPL-2.0-only.
- **Vendor icons, trade-dress colour schemes or manual text.** Generic patterns (status
  colours, list/topology, pre/post scan) are fine.

## Sources

- [A1] Autel MaxiSys MS919S2 User Manual §6.3 (VID, Manual Selection), https://cdn.shopify.com/s/files/1/0575/5407/5815/files/MaxiSys_MS919S2_User_Manual_EN_V1.0.pdf
- [A2]–[A14] same manual: §6.4.1 layout and nav bar (A2); §6.6 Control Unit functions (A3); §6.6 Auto Scan topology/list states and buttons (A4); §6.10 Generic OBDII (A5); §6.9 "Only the available operations display" (A6); §6.11.1 pre/post scan (A7); §6.4.2 message types (A8); Erase Codes (A9); §6.6.4 Active Test (A10); §6.9.1 Coding (A11); §6.9 programming warnings (A12); §6.4.1.3 status bar (A13); §6.11.2 and §10.5 reports (A14).
- [L1] Launch X-431 Euro Turbo manual, https://www.manualslib.com/manual/2208191/Launch-X-431-Euro-Turbo.html
- [T1] Topdon Phoenix Elite User Manual §2, https://web-file.topdon.com/topdon-web/information_download/Phoenix-Elite-User-Manual.pdf
- [S1] Snap-on ZEUS Training Module 2, https://snapon.com/Diagnostics/US/KB/ZEUS-Training-Module-2.htm
- [S2] Snap-on ZEUS Training Module 7, https://snapon.com/Diagnostics/US/KB/ZEUS-Training-Module-7.htm
- [S3] Snap-on ZEUS product page, https://www.snapon.com/diagnostics/us/ZEUS
- [B1] Bosch ESI[tronic] diagnostic solutions brochure, https://www.boschaftermarket.com/xrm/media/images/country_specific/gb/equipment_2/ecu_diagnostic_tools/xx_pdfs_15/diagnostic_solutions_brochure.pdf
- [B2] PMM, "How to improve your KTS diagnostics capabilities, Part 2: System overview and protocol reports", https://pmmonline.co.uk/?p=5115
- [V1] Ross-Tech VCDS Tour: AutoScan, https://www.ross-tech.com/vcds/tour/autoscan.php
- [V2] Ross-Tech VCDS Tour: Main Screen, https://www.ross-tech.com/vcds/tour/main_screen.php
- [V3] Ross-Tech VCDS-Lite Manual: Autoscan, https://www.ross-tech.com/vcds-lite/manual/autoscan.html
- [V4] Ross-Tech VCDS Tour: Gateway Installation List, https://www.ross-tech.com/vcds/tour/installation-list.php
- [V5] Ross-Tech Label Files, http://www.ross-tech.com/vag-com/labels.php
- [V6] Ross-Tech Wiki: Control Module Maps, https://wiki.ross-tech.com/wiki/index.php/Control_Module_Maps
- [N1] NanoCom Evolution Discovery II kit listing (module unlocks), https://plastiquealaloupe.fondationtaraocean.org/products/evolution-for-motronic-v8-discovery-ii-kit/211810023/
- [N2] Ostler UI overhaul spec (NanoCom split), [specs/2026-10-05-ui-overhaul-design.md](../../../specs/2026-10-05-ui-overhaul-design.md)
- [N3] AULRO, "Idiot's guide: changing injector codes and saving them using NanoCom", https://www.aulro.com/afvb/technical-chatter/249017-idiots-guide-changing-injector-codes-saving-them-using-nanocom-ecu.html
- [F1] Faultmate MSV-2 review (P38), https://stockholmviews.com/p38/faultmate-review.html
- [H1] Bearmach HawkEye Total product sheet, https://rimmerbros.com/ItemFiles/Manuals/HawkEye_NPI%20Jan%2017%20Fina-2.pdf
- [G1] Disco3.co.uk, "IID BT 1st time use", https://disco3.co.uk/forum/iid-bt-1st-time-use-qs-131650.html
- [P1] python-OBD docs: Connections, https://python-obd.readthedocs.io/en/latest/Connections/
- [P2] python-OBD LICENSE, https://github.com/brendan-w/python-OBD/blob/master/LICENSE
- [P3] python-OBD `obd/__init__.py` header, https://github.com/brendan-w/python-OBD/blob/master/obd/__init__.py
- [O1] OpenVehicleDiag README and LICENSE (GPL-3.0; SMRParser "removed due to DMCA takedown notice"), https://github.com/rnd-ash/OpenVehicleDiag
- [D1] ddt4all README (Warnings, licence badge), https://github.com/cedricp/ddt4all
- [R1] pyren README (CLIP/DDT modes, expert mode, dump/rollback), https://gitlab.com/py_ren/pyren
- [R2] pyren repository tree (no LICENSE file; GitLab API `license: null`), https://gitlab.com/api/v4/projects/py_ren%2Fpyren
- [ST] openSUSE SDB: ELM327-based OBD2 scan tool (ScanTool.net, GPL), https://en.opensuse.org/SDB:Obd-II_scan_tool
- [NN] Nielsen Norman Group, "Confirmation Dialogs Can Prevent User Errors", https://www.nngroup.com/articles/confirmation-dialog/
