---
title: "muki01 projects: synthesis, licence verdicts, merged feature inventory and build order"
area: references
status: stable
version: 1.1
updated: 2026-10-06
depends_on: [references/research/muki01/obd2_kline_reader.md, references/research/muki01/obd2_diagnostic_ui.md, references/research/muki01/obd2_can_bus_library.md, references/research/muki01/bmw_ibus_kbus.md]
summary: >
  Synthesis of the four muki01 audits (K-line reader and library, Diagnostic UI, CAN library, BMW I/K-Bus). The repos are GPL-3.0 since 2026-10-03, so under ADR-0025 they may be taken whole into GPL-3-marked modules or packs, or reimplemented; the UI is MIT; the KLine library has non-commercial headers and stays reimplement-only; DTC description text is never copied. Gives one licence table, a deduplicated inventory of 53 features with destination, phase, tier, reuse and effort, a build order (K-line profiles and auto-detect, a shared J1979 layer, ISO-TP with passive bitrate detection, an I/K-Bus framer, the generic_obd2 and read-only bmw_e packs), the four ADRs (ADR-0022 to ADR-0025), safety anti-patterns and conflicts with our design turned into rules, test fixtures from their bugs, and housekeeping fixes.
---

# muki01 projects: synthesis and plan

The owner's direction: "we'll roll in every feature into our app". This note merges the four
audits into one plan. Each row below cites the note it comes from:
[K-line reader and library](obd2_kline_reader.md) (K), [Diagnostic UI](obd2_diagnostic_ui.md) (U),
[CAN library](obd2_can_bus_library.md) (C) and [BMW I/K-Bus](bmw_ibus_kbus.md) (B).
"Every feature" means every feature is placed. Rows the audits rejected outright are in (e).
Nothing here is built without a spec. The rules in
[ADR-0019](../../../decisions/adr-0019-reuse-from-ovms-and-obdb.md),
[ADR-0020](../../../decisions/adr-0020-can-links-listen-only-by-default.md) and the four ADRs
from this work ([ADR-0022](../../../decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md)
to [ADR-0025](../../../decisions/adr-0025-reuse-and-licences-pragmatic.md)) apply. Decoded vehicle
information (PIDs, CAN IDs, I/K-Bus messages, module addresses) goes into **vehicle packs only**;
the platform stays generic.

## (a) Summary and licence verdicts

All of muki01's repos moved from MIT to **GPL-3.0 plus a commercial licence** on 2026-10-03.
Under [ADR-0025](../../../decisions/adr-0025-reuse-and-licences-pragmatic.md) the **current licence
counts**, and we do not hunt licence dates. A GPL-3.0 repo may be **taken whole into a clearly
marked GPL-3 module or pack** (SPDX `GPL-3.0-or-later`, REUSE annotation; preferably a separate
pack), as a conscious per-use choice, so that core stays commercially licensable (ADR-0012); or its
ideas are **reimplemented in our own words**, which is always fine. Non-commercial sources are
reimplement-only. **Descriptive text is never copied verbatim**, above all the DTC descriptions.
Given the code quality (no tests, many defects), reimplementing will usually win; the choice is
made per use.

| Repo | Last MIT commit | Since | What we may do (ADR-0025) |
|---|---|---|---|
| `OBD2_K-line_Reader` (firmware) | `91ae045` (2026-10-01); last code change `e0cb395` | GPL-3.0 at `aef63b4` (2026-10-03) | GPL-3 module/pack, or reimplement |
| D2 vendored copy (`Basic_Code`, schematics) | `a1946a7` (2025-09-24), MIT | — | MIT: copy with the notice; its README needs fixing, see (g) |
| `OBD2_KLine_Library` | v1.1.0 (`2becca2^`); MIT from `f08eec9` | "Source-available, non-commercial" from `2becca2` (2026-06-26); root GPL-3.0 at `678e7f1`, but file headers still demand a paid commercial licence | **Reimplement only** (non-commercial headers). The v2 ideas (KW1281, DS2, KW82, profile table) are rebuilt in our own words |
| `OBD2_CAN_Bus_Library` | `3dfba62` (2026-07-10); `src/` unchanged to HEAD | GPL-3.0 at `b2f0c4e` (2026-10-03) | GPL-3 module/pack, or reimplement; little is worth taking, test ideas mainly |
| `OBD2_CAN_Bus_Reader` (firmware) | MIT history not checked | GPL-3.0 at HEAD `29fece7` | GPL-3 module/pack, or reimplement |
| `OBD2-Diagnostic-UI` | **still MIT** at HEAD `56e9153` (2026-08-30) | — | Port with the MIT notice. **Excluded:** the car art, the Icons8-style tick, Montserrat (no OFL text) and `errorCodes.js` (DTC descriptions derived from SAE J2012: descriptive text, never copied) |
| `BMW_IBus_KBus` (firmware) | `6213cc6` (2026-10-02) | GPL-3.0 at `6b5424d` (2026-10-03) | GPL-3 module/pack, or reimplement. Its history held NavCoder and BMW training PDFs, which we **never use** (dealer material); `E46_Codes.h` is of mixed lineage, so verify every frame on a car |
| `BMW_IBus_KBus_Library` | `87b58c6` | GPL-3.0 at `b3cffb8` | **Reimplement only.** The core appears to derive from a third party's `IbusSerial`, whose grant is unclear |
| `VAG_KW1281` | not audited | — | Not used until audited |

Related libraries named in the audits: `kmalinich/node-bmw-client` (**MIT**): copy with the notice,
or reimplement; the best open decode reference for IKE, GM and LCM. `tedsalmon/BlueBus`
(BSD-3-style with a no-profit hardware clause): reimplement its software ideas, and never its
hardware. `piersholt/walter` (GPL-3.0): GPL-3 module/pack, or reimplement. `kw1281test` (MIT): cross-check KW1281 against it.
`can-isotp` (MIT) and OBDb SAEJ1979 (CC BY-SA) are the data sources. NavCoder, BMW dealer material
and the HackTheIBus lists: **never**.

**Net value.** The code has no tests and is full of defects. The value is in protocol breadth
(ISO 9141-2, KW1281, DS2, KW82, I/K-Bus), the protocol-profile-as-data design, the J1979 scope,
page-driven polling, small UI ideas and a body-bus use case. Their bugs become our test fixtures.

## (b) Merged feature inventory (deduplicated)

Tiers follow UI spec §7: read 0, clear 1, actuate 2, procedure 3, code 4; `comfort` is for our own
add-ons only. **Phase** names a UI phase (U0–U7), a direction phase (P1–P4), or one of the new
tracks: **BMW** is the new BMW E-series pack and **iii** means it waits for ADR (iii), now
[ADR-0024](../../../decisions/adr-0024-body-bus-links-passive-by-default.md). Reuse
([ADR-0025](../../../decisions/adr-0025-reuse-and-licences-pragmatic.md)): "facts" means reimplemented
in our own words from the source, the standard or OBDb; "GPL-3 / facts" means the GPL-3 code may be
taken whole into a marked GPL-3 module or pack, or reimplemented; "ideas" means a design idea only.
Rows whose source is the KLine library or the I/K-Bus library stay "facts" (non-commercial headers;
unclear grant).

| # | Feature | From | Destination | Phase | Tier | Reuse | Effort |
|---|---|---|---|---|---|---|---|
| 1 | K-line protocol profiles as data: baud, serial format, address parity, checksum, header, length mode, P1–P4, W1–W5, idle; init method as its own axis | K | platform `kline/profiles.py`; packs override in `vehicle.json` `transport` | U4 (spec now) | read | facts | M |
| 2 | Keyword read, ~addr check, classification (KW1==KW2 → 9141) and KWP key-byte decode | K | platform `kline.keywords` | U4 | read | GPL-3 / facts | S |
| 3 | K-line auto-detect (9141 / 14230 slow / 14230 fast) and a manual override | K, U | platform `kline.detect()`; override only in Developer under service mode | U4 | read; probe Parked (ADR-0022) | GPL-3 / facts | M |
| 4 | ISO 9141-2 framing (`68 6A F1` / `48 6B xx`) and keep-alive (`01 00` on 9141, `3E` on KWP) | K | platform `kline/frame_iso9141.py` | U4 | read | GPL-3 / facts | S |
| 5 | P3-min guard before each request; long idle only after an abandoned session | K | platform `KLine._send`, `init_idle` | U4 | read | GPL-3 / facts | S |
| 6 | Manufacturer K-line framing: KW1281 (ack by complement, counter), BMW DS2 (8E1, XOR), Opel KW82 (streaming, sliding window), Honda (two's complement) | K | platform profiles + framers; VAG, BMW, Opel and Honda packs | U7 | read | facts; KW1281 checked against kw1281test | M each |
| 7 | Passive 5-baud init decoder, and the fast-init `0x00` sniff signature | K | platform `sniff` (`ModuleTracker`) + ostler-firmware RX tap | U7, P2 | read | facts | S |
| 8 | `CanLink` listen-only, then **passive** bitrate and ID-width detection, then one `01 00` | C | platform `SocketCanLink` + detect | U4 | read | facts (redesigned) | M |
| 9 | ISO-TP (FF/CF/FC, P2/P2\*, NRC `0x78`/`0x21` backoff) | C | platform `IsoTpChannel` (kernel `CAN_ISOTP`; can-isotp MIT elsewhere) | U4 | read | own | M |
| 10 | Functional and physical addressing, reply filter `7E8–7EF` / `18DAF1xx`, per-ECU collection, RX flush before each request | C | platform `ObdService` | U4 | read | GPL-3 / facts | M |
| 11 | Raw send at three levels (framed, checksum-only, verbatim) | K, C | platform raw send behind the pack allowlist; More › Developer | U7 | code | GPL-3 / facts | S |
| 12 | Link health: lost after 3 misses, re-init with backoff | K, C, U | platform session health → strip Link chip | U1, U4 | read | GPL-3 / facts | S |
| 13 | **J1979 service layer**, shared by K-line and CAN: request builder, multi-frame and multi-ECU parser, chained support bitmaps for 01/02/05/06/08/09 | K, C | platform `obd/j1979.py` (`supported()` feeds `generateViews()`) | U4 | read | GPL-3 / facts | M |
| 14 | Mode 01 live PIDs, including multi-field and signed ones | K, C | `generic_obd2` (OBDb SAEJ1979 import); Home, Diagnose › Live | U4 | read | facts (OBDb) | M |
| 15 | The 18 O2 PIDs OBDb lacks (`16 17 1A 1B 25–2B 35–3B`), offered upstream | C | `generic_obd2` overlay, `candidate` | U4 | read | facts (J1979) | S |
| 16 | PID 01: MIL, DTC count, readiness monitors (bytes B–D) | K, C | `generic_obd2` → `Vehicle.Ostler.Diagnostics.*`; Home health card | U4 | read | GPL-3 / facts | S |
| 17 | Mode 03 / 07 / 0A DTCs, multi-frame and multi-ECU; J2012 P/C/B/U decode; a Pending group | K, C, U | platform J1979 + `dtc` decoder; `generic_obd2` `dtc_sources`; Diagnose › Faults | U4 | read | GPL-3 / facts | S |
| 18 | Freeze frame as a "Snapshot" section of fault detail, with the `02 02` stored-by DTC | K, C, U | Diagnose fault detail (D2 where KWP stores it); `generic_obd2` Mode 02 | U3, U4 | read | GPL-3 / facts | M |
| 19 | Distance travelled with MIL on (PID `21`) | K, U | `generic_obd2` fault detail | U4 | read | GPL-3 / facts | S |
| 20 | Mode 04 clear as a `clears` action: Parked, confirm, report first, re-read 03/07/01 | K, C, U | `generic_obd2` action through the server gate | U2 gate, U4 | **clear** | GPL-3 / facts | S |
| 21 | Mode 05 (K-line only) and Mode 06 test results | K, C | `generic_obd2`; Diagnose › Tests | U4+ | read | GPL-3 / facts | M |
| 22 | Mode 08 control | K, C | listed only, under its own review | — | actuate | — | — |
| 23 | Mode 09 VIN (local decode, redacted), CALID, CVN (non-CAN counts `03`/`05`), ECU name `0A` | K, C, U | platform J1979 + local VIN decode; masked identity bar; fingerprint | U4, U7 | read | GPL-3 / facts | S |
| 24 | Coverage counts from the support bitmaps | U | identity bar + More › Developer › Coverage | U4 | read | ideas | S |
| 25 | Generic DTC text | K, U | our own wording or OBDb; **never** `errorCodes.js` | U4 | read | none | M |
| 26 | **Poll by demand without starving recording**: the recording set is the baseline and always polled; the "visible signals" subscription only raises the priority or rate of what is on screen; signals neither recorded nor visible may be dropped | K, C, U | platform poll scheduler + UI subscription | U3 | read | ideas | M |
| 27 | Searchable signal picker that also sets the poll set | U, K | Diagnose › Live | U4 | read | ideas | M |
| 28 | 12 V chip with three bands from `normal`/`limits`, shifted while the engine runs, with a word | U | status strip + Home card on `Vehicle.LowVoltageBattery` | U1 | read | ideas | S |
| 29 | Link chip with two rungs (adapter, ECU), words, grey on silence; selected and connected protocol on the Link sheet | U | status strip | U1 | read | ideas | S |
| 30 | Per-area accent tokens (clear of ISO telltale colours); no splash; hero beside, not above, the cards | U | `ui/tokens`, Home | U1 | read | ideas | S |
| 31 | Faults empty state with scan age ("No codes · Engine · read 40 s ago"), distinct from "Not scanned" | U | Diagnose › Faults | U3 | read | ideas | S |
| 32 | Glossary "i" chips (for example "What is a freeze frame?"), hidden while Moving | U | Diagnose | U3 | read | ideas | S |
| 33 | Performance timing (0–100): armed Parked, computed after the run from logged speed with interpolation | K, U | Logs session detail; Drive shows only the result | U2, U7 | read | ideas | M |
| 34 | Device JSON contract tests | U | AsyncAPI / JSON Schema CI | U0, U5 | — | ideas | S |
| 35 | Device settings template: network (octet filter), protocol or bitrate, update | U | More › Devices | U5 | comfort | port (MIT) or clean-room | S |
| 36 | Battery ADC (16× oversampling + EMA) | K, C | ostler-firmware → `Vehicle.LowVoltageBattery.CurrentVoltage` | P2 | read | GPL-3 / facts | S |
| 37 | Signed, authenticated OTA with progress and a reboot sheet | K, U | ostler-firmware + More › Devices › Update | P2 (U5) | procedure | GPL-3 / facts | M |
| 38 | No default AP password: the build refuses to compile without one | B, K | ostler-firmware build rule | P2 | — | facts (pattern) | S |
| 39 | ESP32 TWAI node: listen-only at boot, slcan/GVRET to `CanLink` | C | ostler-firmware | P4 | read | GPL-3 / facts | S |
| 40 | K-line interface hardware: L9637D/MC33290 plus TVS and series R; check LIN parts' dominant timeout | K | ostler-firmware hardware docs | P2 | — | facts (redrawn) | S |
| 41 | Status LED and beep cues | K, U | ostler-firmware device action | U5 | comfort | ideas | S |
| 42 | **I/K-Bus framer**: 9600 8E1, `SRC LEN DST DATA CHK`, XOR, 1-byte resync, LEN 3–36, source filter; `FakeIbus` | B | BMW pack first, then platform once a second body-bus pack needs it | BMW | read | facts | S |
| 43 | I/K-Bus capture kind: module naming, a last-N monitor, per-(src, cmd) change heat | B | platform `sniff/` + UI Decode | U7 | read | GPL-3 / facts | S |
| 44 | **BMW E-series pack**, read-only: GM `72`/`7A`, EWS `74`, IKE `11 13 17 18 19 24`, LCM `5B`, MFL, radio, DSP, phone; three new `Vehicle.Ostler.*` event leaves | B (+ node-bmw-client) | new `bmw_e` pack (E46 first; L322 a candidate) | BMW | read | GPL-3 / facts; MIT (node-bmw-client) | M |
| 45 | Body-bus alarm triggers: door, boot or bonnet open, unlock without our disarm, key in, ignition, any bus wake | B | guardian alarm (notify-only) | P2, BMW | read | GPL-3 / facts | S |
| 46 | Bus-wake power gating; "still powered after 3 s, so on the bench: stay on" | B | ostler-firmware body-bus node | P2, BMW | read | GPL-3 / facts | M |
| 47 | Body-bus hardware: an RX-only opto tap by default; a TH3122 / Elmos 10026B TX variant with SEN/STA idle, echo compare and retry | B | ostler-firmware hardware | BMW; TX iii | read; actuate | facts (redrawn) | M |
| 48 | IKE requests: odometer `16`, time `41` | B | BMW pack poll under the ADR (iii) Tier 0 exception | iii | read (transmits) | GPL-3 / facts | S |
| 49 | LCM and GM IO jobs (lamps, locks, windows, sunroof, wipers); OBC reset | B | BMW pack actions, disabled by default | iii + U5 threat model | actuate (windows need an occupant confirm) | GPL-3 / facts, verified on a car | M |
| 50 | Standing automations: welcome, goodbye, follow-me-home | B | BMW pack "standing automation" | iii | actuate (autonomous) | GPL-3 / facts | M |
| 51 | MFL buttons as Drive-mode input; CDC emulation; display text injection | B | head-unit integration | U2 (read); P4 / U5+ (TX) | read; actuate | GPL-3 / facts | L |
| 52 | Vehicle-report issue form (protocol, keywords, supported PIDs, model) | K, C, B | `.github/ISSUE_TEMPLATE` | U4 | — | ideas | S |
| 53 | ECU simulators: an ISO 9141 / J1979 fake and `FakeIbus` | K, B | `tests/fakes` | U4, BMW | — | facts | S |

**Not taken:** the unpublished manufacturer ECU files, the multi-MCU ports (we target ESP32-S3),
the two-colour titles, the page fade, the 3 s splash and the hero art.

## (c) Recommended build order

1. **Now, documents only:** apply (g). ADRs (i)–(iv) are written and accepted as ADR-0022 to
   ADR-0025 (see (d)).
2. **U1–U3 (Phase 0), add to the existing phase specs:**
   - U1: rows 28–30 (12 V bands, the two-rung Link chip with staleness, accent tokens), plus a
     Playwright check that every Home card is above the fold at 1024×600.
   - U2: the Mode 04 server-gate test (row 20) and the "arm Parked, show only the result" pattern
     for performance timing (row 33).
   - U3: the **visible-signals subscription** (row 26), under the polling rule: the recording
     set is always polled, the subscription only raises the priority or rate of what is on
     screen, and only signals neither recorded nor visible may be dropped; freeze frame in fault detail (row 18), the
     scan-age empty state (row 31) and glossary chips (row 32).
3. **New spec: "K-line profiles and detection"** (needs ADR i). `kline/profiles.py`, `kline.keywords`,
   ISO 9141-2 framing, `kline.detect()`, the P3-min guard and keep-alive (rows 1–5). The D2 pack
   declares its profile and never auto-probes. Write it before U4, because `generic_obd2` over a
   KKL cable depends on it.
4. **New spec: "J1979 service layer"**, transport-agnostic and shared by K-line and CAN (rows 13–25),
   **test-first** from the fixtures in (f). It can start before U4 with fakes only.
5. **U4 / Phase 3 (`generic_obd2`, the first new pack: OBDb SAEJ1979 plus the extra O2 PIDs):** the K-line path from step 3; then the CAN path from a new
   **"CanLink, passive detect and ISO-TP" spec** (rows 8–10, needs ADR ii); OBDb import with the
   O2 overlay; Mode 04 as `clears`; local VIN decode; coverage; the signal picker; the issue form.
6. **Phase 2 / U5 (ostler-firmware and devices):** rows 35–38 and 40–41, which are the battery
   EMA, signed OTA, no default AP password, the device settings template and the K-line hardware
   docs; and the device contract tests (row 34). U5 needs the threat model first.
7. **New track: BMW E-series, read-only (`bmw_e`, the second new pack, built from the I/K-Bus
   facts).** A spec for the I/K-Bus framer, `FakeIbus` and the
   capture kind (rows 42–43, 53), then the `bmw_e` pack (row 44), then the alarm triggers into the
   guardian (row 45) and the RX-only tap hardware (rows 46–47). This needs only stdlib and no
   hardware in CI, so it can run in parallel once the owner has an E-series car or a bench.
8. **U7:** manufacturer K-line protocols, one at a time, each with a fixture (row 6); the passive
   5-baud decoder (row 7); raw send (row 11); performance from logs (row 33).
9. **After ADR (iii) and the U5 threat model:** body-bus transmit (rows 47–51). **P4:** the TWAI
   node (row 39) and CDC emulation and display text (row 51).

Guardrails: **vehicle data goes into packs only.** Decoded vehicle information (PIDs, CAN IDs,
I/K-Bus messages, module addresses) lives in `generic_obd2`, `bmw_e` and later packs; the platform
keeps only generic mechanisms. K-line profiles and J1979 are comms core, and each has at least two users (D2 and
`generic_obd2`; K-line and CAN). The I/K-Bus framer starts **inside the BMW pack** under the rule
of two, and moves to the platform when a second body-bus pack (L322) needs it.

## (d) ADRs needed

All four are written and accepted (2026-10-06); each row links its ADR, which is the
authority where it differs from the proposal below.

| | ADR | Proposed decision |
|---|---|---|
| i | **K-line protocol profiles and auto-detection**: [ADR-0022](../../../decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md) | Profiles are data records in the platform (fields as in row 1), and packs override them. The probe order for an unknown car: KWP fast init, then 5-baud `0x33`; classify by keywords and verify ~addr. KW1281, DS2 and KW82 are never auto-probed; they come from a pack or Developer. **Probing an unknown car is Parked-only** (an init pulse can break another tester's session, or one still alive in the ECU). Re-initialising a known profile after a link loss is allowed in every state, like ADR-0020's Tier 0 exception. Keep-alive is required, `82` release on exit, W5 ≥ 300 ms, and a P3max idle only after an abandoned session. Address bytes go out 8N1; parity applies only where a profile names it |
| ii | **Passive bitrate detection before the first CAN request** (amends ADR-0020): [ADR-0023](../../../decisions/adr-0023-passive-can-bitrate-detection.md) | The Tier 0 exception applies only once the bitrate is confirmed. On an unknown bus, `CanLink` listens at 500k and then 250k, and accepts a rate after N clean frames with no growth in the error counters; it learns the ID width from the traffic. Only then does it send one functional `01 00`. On a silent bus (a gateway OBD port), it sends a single `01 00` per rate, 500k first, **Parked only**, and stops on the first error frame. A known pack bitrate skips detection. Flush RX before each request and collect replies per ECU |
| iii | **Body-bus links (BMW I/K-Bus): passive by default**: [ADR-0024](../../../decisions/adr-0024-body-bus-links-passive-by-default.md) | A byte `Transport` plus a framer, not a `CanLink`. Listen-only by default, with an RX-only tap as the reference hardware. Transmit needs a pack allowlist keyed on `(src, dst, cmd, data mask, rate)`, plus Parked and the server gate. **No spoofing:** never send with the source address of a module present in the car (GM `00`, EWS `44`, IKE `80`, MFL `50`, RAD `68`); `3F` only for allowlisted IO jobs; emulate a device such as CDC `18` only when none answers. A rate-limited Tier 0 exception for IKE `16`/`41`. TX hardware needs SEN/STA idle, echo compare and bounded retries. Nothing transmits from a remote path, and lock/unlock waits for the U5 threat model. **Standing automations** are pre-authorised once, Parked only, rate-limited and logged frame by frame; they are neither `comfort` nor a per-action confirm. Alarm triggers stay read-only, because the alarm is notify-only |
| iv | **Reuse and licences, pragmatic** (amends ADR-0019 (c)): [ADR-0025](../../../decisions/adr-0025-reuse-and-licences-pragmatic.md) | Revised by the owner from the first "facts-only, pinned commit" proposal. Reimplementing ideas from any source in our own words is fine; descriptive text (DTC descriptions, J2012 wording) is never copied; GPL-3 repos may be taken whole under their current licence into marked GPL-3 modules or packs, so core stays commercially licensable; GPL-2.0-only, non-commercial and dealer-derived material stay out |

No new ADR is needed for Mode 04 (UI spec §7 Tier 1; the U4 spec confirms that `generic_obd2`
inherits it) or for manufacturer K-line actuators, which inherit ADR-0019's disabled-by-default
gating.

## (e) Safety anti-patterns found, and what each becomes

| Anti-pattern (where) | Our rule | Test |
|---|---|---|
| **Ungated DTC clear**: one tap, WS `clear_dtc`, `GET /api/clearDTCs`, a clear in `setup()` (K, C, U) | Every clear goes through the server gate as Tier 1: Parked, confirm, report first, re-read | No `GET` route mutates; a clear is refused while Moving, without confirmation, or from a remote path |
| **Unauthenticated OTA** `POST /firmwareUpdate` (K, U) | OTA is a Tier 3 procedure: signed image, authenticated, Parked, with progress | An unsigned or wrongly signed image is rejected; an unauthenticated upload gets 401 |
| **Default AP password** `12345678` (K) | No default secret; a per-device secret is set at provisioning | A firmware CI build fails without one (the `static_assert` pattern from B) |
| **Transmitting while probing the bus speed**, in normal mode at a guessed rate (C) | ADR (ii) (ADR-0023): listen first | On `vcan`, detection sends zero frames before it locks a rate; a silent-bus probe is refused unless Parked |
| **No keep-alive** and no `82` on exit, so an idle page drops the link (K) | Every session sends keep-alive and releases with `82` | A `FakeKLineEcu` with nothing selected for 10 s still gets `3E`/`01 00` inside P3max, and `82` on close |
| Body-bus `/api/cmd` sends any frame with no auth and no driving-state check (B) | ADR (iii) (ADR-0024); one server gate | A body-bus frame is refused while Moving, remotely, or when off the allowlist |
| Autonomous transmit on key-fob events (B) | Only as standing automations under ADR (iii) | An automation is refused when not pre-authorised or not Parked; every frame is logged |
| Spoofing another module's frames (B) | No spoofing (ADR iii) | TX with a present module's source address is refused |
| `innerHTML` from bus data; colour-only status; stale green after the socket dies; reconnect with no backoff (U) | Text nodes only; icon plus word; a staleness timer; backoff | XSS fixture; axe 1.4.1; the chip goes grey on silence |
| Full VIN shown and printed to debug (K, C, U) | Local decode, masked form only | No VIN reaches logs, captures or fixtures (U4 test) |
| In-band float sentinels `-1/-2/-4`; first-frame-wins replies; no reply checksum check (K, C) | Typed value plus status; per-ECU collection; verify every checksum | Fixtures 7, 4 and 5 in (f) |
| Even parity on 5-baud addresses; 5.5 s idle before every init; LIN parts that time out a 200 ms bit (K) | 8N1 addresses; W5 idle; a transceiver check | Fixture 12; a hardware-doc checklist |
| I/K-Bus TX with no echo compare or retry; opto and MCP2025 TX with no SEN/STA (B) | ADR (iii) TX hardware rule | A `FakeIbus` collision is detected and retried, with bounded retries |

**Conflicts with what we already have.** Where their design meets ours, ours wins:

| Their approach | Ours, which stays | Why |
|---|---|---|
| Even (or odd) parity on the 5-baud address byte | **8N1, no parity bit** (ADR-0022), per the 2026-08-04 fix | `0x29` went out as `0xA9` and failed; the ISO wording stays open in the D2 init-timing slab |
| Poll only the page on screen | **The recording set is always polled**; the visible-signals subscription only raises priority or rate (UI spec §10, U3) | Demand-only polling would starve whole-app recording and replay |
| Mode 04 clear on one tap, GET or a socket message | **A gated Tier 1 `clears` action**: Parked, confirm, report first, re-read (UI spec §7) | A clear loses freeze frames and readiness |
| WebSocket push driven by the open page | **Our snapshot plus SSE model** stays | One server state for every client; their per-page socket does not replace it |

## (f) Test fixtures to create from their bugs

All are written from the standard (J1979, ISO 9141-2/14230/15765-4) or re-derived on a car,
never copied from their output. Fixture files are CC BY-SA under `tests/fixtures/`.

1. **DTC parser skipping codes:** CAN Mode 03 with the count byte (their example
   `07 43 01 70 01 34 00 00`, expected result from J1979, not their output), and 3+ DTCs over ISO-TP.
2. **K-line DTC burst with 4+ DTCs**, where the next frame's `48 6B xx` header must not decode as DTCs.
3. **Support-bitmap overflow:** a chain of 160 set bits; a group with no reply that must not desync.
4. **Multi-ECU:** a merged K-line burst (`48 6B 10` + `48 6B 18`), and a `7E8` + `7E9` double reply.
5. **Late reply:** a second ECU's late frame must not be taken as the answer to the next request.
6. **Signed and mis-scaled PIDs:** `32` and `54` signed; `23` ×10 kPa (they divide, a 100× error);
   `50` ×10 g/s.
7. **Negative values next to sentinels:** STFT −100 %, IAT −40 °C, timing below zero, torque `A−125`.
8. **Multi-field PIDs:** `01` readiness bytes B–D, `14–1B` STFT byte B, `24–2B` voltage, `34–3B`
   current.
9. **Freeze frame `02 02`** as a two-byte DTC.
10. **VIN:** over ISO-TP FF/CF/FC; on K-line with the `09 01` count; CALID and CVN counts
    `09 03`/`09 05`; a redaction test that no VIN reaches logs.
11. **Index binding:** their page shows PID `23` as "distance with MIL on" (it is `21`), so a
    manifest test checks that the signal id binds to the PID, not to an array index.
12. **5-baud parity:** `0x29` goes out 8N1 (not `0xA9`); `0x33` is unchanged.
13. **Fast init:** a glitch byte before `C1`, and an unaddressed `03 C1 …` reply.
14. **No headerless frames:** every 9141/KWP request carries the connected protocol's header (the
    vendored copy's Automatic-mode bug).
15. **I/K-Bus vectors:** about 117 frames re-derived as `(src, dst, cmd, data)` facts. Our framer
    computes LEN and XOR, and the result must match the audit's checked values. Add a resync after a
    bad checksum, LEN outside 3–36, and TX over 32 bytes refused.
16. **KW82:** sliding-window lock-on from every offset of a looping stream.
17. **KW1281:** ack by complement, and block-counter wrap.
18. **Contract drift:** a device payload with `SupportedLiveData` fails the AsyncAPI schema.
19. **OBDb import checks:** `24` divisor 8196 against J1979's 8192; `5D` offset −38665 against
    `/128 − 210`.

## (g) Housekeeping

1. **`landscape.md`** (done in this change): the reader is "MIT until `91ae045` (2026-10-01),
   GPL-3.0 since 2026-10-03"; the library is marked non-commercial and facts-only.
2. **Platform `THIRD_PARTY_LICENSES.md` and `README.md`** (proposed, not applied): the heading says
   MIT without a date, and the link points at the PlatformIO entry, which is the **library**. Link
   the reader repo, and state its current licence (GPL-3.0) and how we use it (ADR-0025).
3. **D2 pack `references/muki01_OBD2_K-line_Reader/README.md`** (to apply in the pack repo).
   Replace everything from the title down to "## What we take from here" with:

```markdown
# muki01 / OBD2_K-line_Reader — reference

A saved copy of `Basic_Code/` and `Schematics/` from
[muki01/OBD2_K-line_Reader](https://github.com/muki01/OBD2_K-line_Reader), a ready-to-flash
OBD2 K-line scan-tool firmware (ISO 9141-2 / ISO 14230 KWP2000, slow and fast init) for
Arduino/ESP32. Author: Muksin Muksin (muki01).

- **Snapshot:** upstream commit `a1946a7` (2025-09-24), byte-identical except for a trailing
  newline. The repository is still on GitHub; an earlier version of this note wrongly said
  it had been removed.
- **Licence of this copy: MIT** ("Copyright (c) 2023 Muksin Muksin"). Upstream was MIT until
  `91ae045` (2026-10-01) and has been GPL-3.0, with a commercial licence offered, since
  `aef63b4` (2026-10-03). Under the platform's ADR-0025, this MIT copy may be used with the
  notice kept, and current upstream code may be taken whole only into a GPL-3-marked module
  or pack; reimplementing in our own words is always fine.
- **Not the library.** The PlatformIO entry "muki01/OBD2 K-Line" is the companion
  [OBD2_KLine_Library](https://github.com/muki01/OBD2_KLine_Library). Its current files carry
  non-commercial or conflicting licence headers, so we reimplement its ideas and take no code.
- **Known bug in this snapshot:** request headers come from the *selected* protocol, so
  Automatic mode sends frames with no header. Upstream later switched to the *connected*
  protocol. Use this copy as a timing reference, not as working code.
- Full audit: the Ostler platform repo, `references/research/muki01/obd2_kline_reader.md`.
```

   Also cite the 5-baud parity divergence (fixture 12) in the D2 init-timing slab, and update the
   pack's `THIRD_PARTY_LICENSES.md` entry in the same way.
