---
title: "Decode pipeline — from an unknown car to a pack with verified signals"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/platform.md]
summary: >
  A defined, read-only dev pipeline (connect, identify, inventory, baseline, capture, correlate, label, verify, package, contribute) that takes any car, from generic OBD-II through CAN/UDS and K-line multi-ECU to pre-OBD, to a pack with verified signals. It builds on our sniff/automap/catalog/modscan code, OBDb-compatible CC BY-SA data with test fixtures from real captures, a local-only VIN rule, and a Decode mode in the app with an "unknown vehicle — help decode it" fallback.
---

# Decode pipeline — from an unknown car to a pack with verified signals

## 0. Where we are today

The Discovery 2 pack was decoded by hand, and that path is the template we generalise:

| Step (D2) | Code / doc today | What it generalises to |
|---|---|---|
| Find who answers on pin 7 | `src/openostler/modscan.py`: fast/5-baud init then `82` release; read-only by construction | **Inventory** for any bus |
| Passive tap while a NanoCom runs | ESP32 RX-only tap; pack `references/nanocom_capture_protocol.md` | **Capture** (dealer-tool sniff) |
| Mark screens and plaintext | `>>> screen m/p`, `>>> value k=v` markers; `/capture` (admin **Label** tab) | **Label** |
| Bytes ↔ displayed value | `sniff/automap.py` (search every `(lid, offset, kind)`, R² fit, clean scales; bit search for states), `sniff/calib.py` | **Correlate** |
| Track the active ECU | `sniff/modules.py` (fast-init signature, pack `SniffSpec`, `unknown:0xNN` kept) | ECU attribution for every bus |
| Store with confidence | signal store `proven`/`candidate` (ADR-0003, ADR-0006); UI status `verified/candidate/sniff/untranscribed` + safety class (ADR-0008, `catalog.py`) | **Verify** |
| Share | `community/__init__.py`: opt-in, whitelist payload, coarse descriptor, never VIN | **Contribute** |

Gaps this document closes:
- **No car without a pack works.** `pack.active_pack()` raises `NoVehiclePackError` when no pack is installed (ADR-0015 removed the fallback). An unknown car has nowhere to land.
- Everything is **K-line/KWP-shaped**: `automap` takes `21 xx` LID bytes, `capture.py` parses length-prefixed KWP frames. There is no CAN ID enumeration, no UDS sweep, no bit-flip analysis and no reference-signal correlation.
- **No test fixtures from captures.** Promotion to `proven` is a human call with no recorded evidence attached.
- **No export** to the formats the community uses (OBDb signalsets, DBC).

## 1. Discovery: what the car tells us for free

### 1.1 Protocol auto-detect (ELM327 and our own interfaces)

- ELM327 `AT SP 0` (or `AT SP A6`) searches protocols in order; `AT DP`/`AT DPN` reports the winner. Protocol numbers: 1 J1850 PWM, 2 J1850 VPW, 3 ISO 9141-2, 4 ISO 14230 5-baud, 5 ISO 14230 fast, 6–9 ISO 15765 CAN (11/29-bit, 500/250 k), A J1939. Useful raw tools: `AT SH` (header), `AT CRA` (receive filter), `AT MA` (monitor all, i.e. passive CAN/K-line), `AT IIA` (K-line init address), `AT WM` (wake-up message). The datasheet is at <https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf>. Clones misreport versions and drop `AT MA` frames, so treat a clone's sniff as lossy.
- Auto-detect only finds the **legislated OBD** path. A K-line car may expose other ECUs on the same pin 7 with non-OBD addresses (the D2 has seven), or on pin 8 or other pins. A pre-1996 car may expose nothing at all. Detection must therefore be **layered**: first OBD auto-detect, then pack-driven probes (modscan address lists, KWP `1A` ident), then passive listening.
- On our own transports (SocketCAN, ESP32), auto-detect means trying 500 k then 250 k (then 125/33.3 k on body buses) **in listen-only mode first**. Only when frames are seen do we send anything.

### 1.2 OBD-II identity and capability (SAE J1979)

- **Support bitmaps.** Mode 01 PIDs `00`, `20`, `40`, … each return a 32-bit mask of the next 32 PIDs. Mode 09 PID `00` does the same for vehicle info. On CAN, a functional request to `7DF` gets one reply per emissions ECU (`7E8`–`7EF`), so the bitmaps also enumerate ECUs. Mode 01 PID `1C` names the OBD standard (OBD-II, EOBD, JOBD…) and PID `51` the fuel type.
- **Mode 09.** `02` VIN, `04` CALID, `06` CVN, `0A` ECU name (CAN only). CALIDs and ECU names make a strong, **non-identifying** fingerprint, the same idea as opendbc's firmware-version fingerprints (<https://github.com/commaai/opendbc>, MIT).
- **Data source.** OBDb's `SAEJ1979` repo (<https://github.com/OBDb/SAEJ1979>, CC BY-SA 4.0) holds the standard PIDs as a signalset, so we import it rather than retype J1979.
- **Licence warning.** python-OBD (<https://github.com/brendan-w/python-OBD>) declares **GPL-2.0-only** on PyPI. Do not copy its code. J1979 facts come from OBDb data instead.

### 1.3 VIN: decode locally, never log or upload

- **Local decode only.** The VIN gives WMI (chars 1–3: maker and region), VDS (4–8), the model-year code (char 10) and the plant (char 11). Chars 12–17 are the serial, which is identifying. The decode runs **in memory, on the device**: WMI and year come from a bundled table, and the result is reduced to `{make, model_year, region}`. Only that coarse descriptor reaches pack matching or community payloads, which `_VEHICLE_KEYS` already enforces. The VIN itself is never written to logs, sessions, captures or fixtures. `web/sources.py` already redacts the KWP `1A` identity block, and the recorder drops identity actions.
- **NHTSA vPIC.** vPIC (<https://vpic.nhtsa.dot.gov/api/>) offers `DecodeVinValues`, `DecodeWMI` and batch decoding, and accepts **partial VINs with `*` wildcards**. Sending a full VIN would break our rule. Use vPIC only through one of two routes:
  - (a) **offline**: build the WMI/make table at release time from vPIC's downloadable standalone database (US-government data);
  - (b) an **opt-in** online lookup that sends only `WMI+VDS+year` with the check digit and serial masked (`SALLTGM8*YA******`).
- **Coverage.** vPIC is built from manufacturers' NHTSA filings, so European-market cars (the D2 among them) decode partially at best. The WMI table plus pack `detection` rules must carry those cars.
- **GDPR.** EU regulators can treat a VIN as personal data when it is linkable to an owner. That is one more reason to keep it on the device.

### 1.4 ECU discovery (active, read-only)

| Bus | Sweep | Notes |
|---|---|---|
| CAN 11-bit | For IDs `0x700–0x7FF` (then `0x600–0x6FF` for some makes) send `02 3E 00` (TesterPresent) or `02 10 01` (default session); record any ISO-TP reply on `id+8` / the observed reply ID | CaringCaribou `uds discovery` automates this (<https://github.com/CaringCaribou/caringcaribou>, **GPL-3**: run it as an external tool, do not vendor it) |
| CAN 29-bit | Normal-fixed addressing `18DA<tgt>F1`, tgt `00–FF`, plus functional `18DB33F1` | Same sweep, 256 targets |
| UDS identity | `22 F187` part no., `F189` SW version, `F18A`/`F197` supplier/system name, `F195`; `19 02 FF` DTCs | **Never store `F190` (VIN) or `F18C` (serial)**. Redact both in the transport log like the KWP `1A 87` block |
| K-line KWP2000 | modscan: fast init `81 <addr> F1 81` / 5-baud init per address, record key bytes, `82` release, settle | Today's `AddressScanner`; extend its address list from the pack, or `0x00–0xFF` in "full sweep" with a long settle |
| K-line ident | KWP `1A 80/87/9x` | Identity bytes are redacted as on the D2 |
| Passive CAN | Listen-only: enumerate IDs, DLC, period, jitter, per-byte entropy | Like OVMS `re start` / `re list` (<https://docs.openvehicles.com/>) and SavvyCAN's sniffer |

**Libraries.**
- **python-udsoncan** (MIT, <https://github.com/pylessard/python-udsoncan>) and **can-isotp** (MIT, <https://github.com/pylessard/python-can-isotp>) for UDS/ISO-TP.
- **python-can** (LGPL-3.0, a dependency only) for interfaces.
- **cantools** (MIT) for DBC.
- **odxtools** (MIT, <https://github.com/mercedes-benz/odxtools>) for an ODX import path, used only with data the user lawfully holds.

**Discovery is read-only by rule.** These are allowed: `3E`, `10 01`, `22`, `19`, `1A`, `21` and the inits. These are never sent in any sweep: `27`, `2E`, `2F`, `30`, `31`, `3B`, `11` (ECU reset), `14`, `28`/`85` (comms/DTC control), or anything out of a fuzzer. Further rules:
- Ignition on, engine off, stationary.
- Rate-limit the sweep, and stop it on the first negative response burst or bus-off.
- On K-line, always release with `82`, as `modscan.py` does.

This extends CONSTITUTION's shared-bus rule to CAN.

## 2. Passive capture and reverse engineering

### 2.1 Tools and what to borrow

| Tool | Licence | Borrow |
|---|---|---|
| SavvyCAN <https://github.com/collin80/SavvyCAN> | MIT | Sniffer (bits that change, colour-coded), **range-state** view per byte, flip-bit stepping, DBC editing, replay. UX reference for our Sniff screen |
| cabana (comma.ai; now inside openpilot tools) <https://github.com/commaai/openpilot/tree/master/tools/cabana> | MIT | Message list + bit heat map + click-to-define signal + plot against time; DBC as the output |
| opendbc <https://github.com/commaai/opendbc> | MIT | One DBC per platform (generated from shared fragments), FW-version fingerprints, car ports reviewed by maintainers against recorded routes; an unvalidated port runs "dashcam only" |
| OBDb <https://github.com/OBDb> + `.schemas` | CC BY-SA 4.0 | Signalset JSON, per-model-year `tests/test_cases`, repo per make-model |
| OVMS v3 <https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3> | MIT (mostly) | `re` toolkit (`re start/list`, `re obdii extended <min> <max>` to watch active polling), per-vehicle module with `poll_pid_t` and a canonical metric namespace |
| CaringCaribou | GPL-3 | UDS/XCP discovery as an external CLI. **Its fuzzer is out of scope** |
| ELM327-emulator (Ircama) | CC BY-NC-SA | Local testing only; never ship it or depend on it |

### 2.2 Four techniques, in order of how much they prove

1. **Dealer/reference-tool sniff (strongest for request/response buses).**
   - Method: tap passively, then type markers for the screen and its displayed plaintext. `automap` searches offsets, types and scales.
   - Origin: this is the D2 method (ADR-0005 in the pack).
   - Hard rule (pack `nanocom_capture_protocol.md`): every write, security, coding or actuator frame is **recorded but never replayed**.
   - On CAN/UDS, the same works with an OEM or aftermarket tool on a Y-splitter. The tool's `22 xxxx` requests reveal which DIDs matter, and the screen labels them.
2. **Differential ("change one input").**
   - Method: toggle one physical input and diff the snapshot. It works for bit fields that a single plaintext can't map (e.g. Td5 `21 1E` bit `0x20`, SLABS settings).
   - Change needed: `automap`'s state solver already does this. Extend it to CAN payloads.
3. **Drive and correlate (broadcast CAN, no reference tool).**
   - Method: record the bus while also logging **reference series** (generic OBD-II Mode 01 speed, rpm, coolant, throttle; GPS speed; IMU accel and yaw from our phone/ESP32), then cross-correlate each candidate field against them, allowing for a time lag.
   - Source: LibreCAN (Pesé et al., ACM CCS 2019) does exactly this with OBD-II PIDs plus IMU.
   - Our part: our logbook already records GPS and IMU (ADR-0009/0010), so the reference series are free.
4. **Statistical bit-flip segmentation (finds field boundaries first).**
   - **READ** (Marchetti & Stabili, IEEE TIFS 2019; <https://iris.unimore.it/handle/11380/1185929>) computes per-bit flip rates and splits signals where the flip magnitude drops between adjacent bits. It also tags counters and CRCs.
   - **CAN-D** (Verma et al., 2021) adds bit-distribution and entropy features and endianness.
   - **ByCAN** (<https://arxiv.org/pdf/2408.09265>) goes from bit to byte level.
   - Implementation: write a clean-room version **from the papers**, not from any code. Its output is *proposed fields*, which feed technique 3 or a label.

**Multi-ECU K-line specifics.**
- Attribute every frame to an ECU. Use `ModuleTracker` (init signatures plus pack `authoritative` detectors), and trust operator markers over heuristics.
- Anchor values to the **polling regime**, not the nearest packet. The handoff doc notes that markers land mid-stream.
- Expect non-KWP framings, such as the D2 Autobox `72…` and the BCU `CC`.

**Older cars** (pre-OBD, J1850, KW1281, BMW DS2, Ford EEC-IV, blink codes):
- Expect no auto-detect.
- Detection is by pack rule (make + year + pin map) or by the user choosing the car.
- Capture is the same RX-only tap with the right line driver.
- The fallback is "codes only" (blink-code or DTC readers).
- The landscape doc lists the permissively licensed references per make.

## 3. Verification and confidence

**How others do it.**
- **OBDb** has no confidence field. Its trust comes from two places:
  - **test cases**: `tests/test_cases/<year>/commands/<hdr>.<rax>.<cmd>.yaml`, e.g. `response: 7CC036126FF` mapped to `expected_values: {RAV4_ECT: 90.55}`;
  - `command_support.yaml`, which lists per ECU which commands answered on a real car, with year filters (`f=2013-`).

  Per-command `dbg`/`dbgfilter` flags mark commands under investigation. Contributions are pull requests to the make-model repo with CI schema validation.
- **opendbc/openpilot.** Maintainers review the port and test it against recorded routes. A car that is fingerprinted but not validated stays dashcam-only. DBC signals carry `CM_` comments, and the DBC files carry no confidence.
- **Ours is stricter and should stay so.** The signal store keeps `proven` vs `candidate` per field. The UI derives `verified/candidate/sniff/untranscribed` (ADR-0008) and never copies a status by hand.

**Recommended evidence model.** Add an `evidence` block to each field:
`{source: dealer_sniff|differential|drive_correlate|obd_standard|import:obdb|manual, readings: n, distinct: n, r2, cars: n, fixtures: [ids], reviewer}`.

Promotion rules:

| To | Requires |
|---|---|
| `candidate` | One importer or solver hit (any source). OBDb or DBC imports enter here, never higher |
| `proven` | ≥2 **distinct** readings (scale and offset locked) with R² ≥ 0.999 against a reference (tool plaintext, standard OBD PID or physical measurement), **and** ≥1 committed fixture from a real capture, **and** a second person's review (PR). State bits need both states observed. A field proven on one car is labelled "1 car"; packs show the car count |
| demotion | Any fixture failure or contradicting capture sets it back to `candidate` automatically (the CI run fails) |

**Fixtures.** A new `fixtures` tool turns a labelled capture into OBDb-style YAML (`response` hex → `expected_values`), scrubbed (§5) and stored in the pack `tests/`. `pytest` decodes every fixture through the signal store, so a mapping change that breaks a real response fails CI. This mechanises the "record the finding in the same commit" rule.

## 4. Packaging: how a vehicle definition is born

**Models compared.**
- OBDb: **one repo per make-model**, `signalsets/v3/default.json` plus year-range overrides, CC BY-SA.
- opendbc: **one DBC per platform**, with Python car ports in-tree, MIT.
- Us: **one pack per vehicle family**, a Python distribution with an `openostler.vehicle` entry point (ADR-0013). Its code is AGPL; its data is CC BY-SA (ADR-0012).

**Four stages of a vehicle's life.**

1. **`generic_obd2` (built in).**
   - Contents: the OBDb SAEJ1979 signalset, imported as data with attribution, plus a J1979 DTC reader.
   - Selection: whenever no pack's `detection` matches. It is a real pack behind the same contract, which fixes the `NoVehiclePackError` dead end.
   - Status: J1979 PIDs show `verified` as standard, but a *value* is only trusted where the support bitmap says the car has it.
2. **Make overlay (`candidate`).** If OBDb has a repo for the make or model, import its mode `21`/`22` commands as `candidate` overlays keyed by WMI + year. Cache them locally and never fetch them at runtime with the VIN.
3. **Pack skeleton.**
   - Creation: `ostler pack new` generates `vehicle.json` (detection: WMI/year, CALID/ECU-name or UDS `F187` patterns, K-line addresses) and `ecus/*.json` from the Inventory results.
   - Contents: empty signal stores and the menus/catalog scaffold, with every item `untranscribed`.
4. **Full pack.** The skeleton gains signals (candidate → proven), DTC tables, actions with safety classes (`gated` by default until an ADR says otherwise), fixtures and docs. The D2 pack is the reference.

**Data formats.**
- **Store.** Keep our store as the source of truth (ADR-0003). Make each field **OBDb-expressible**: `hdr`/`rax`/`cmd`/`proto`/`freq` per request; `fmt{bix,len,sign,blsb,mul,div,add,map,min,max,unit}`; `path`; `suggestedMetric`. Our extras (`confidence`, `evidence`, `limits`/`span`/`normal`, safety) go in an `x-ostler` block that OBDb tooling ignores.
- **K-line fits too.** OBDb's schema lists `proto` values `9141-2`/`14230`/`15765-4` and `cmd` services `01`/`21`/`22`. KWP local-ID signals like the D2's should therefore round-trip. Seed/key and custom inits stay in pack `hooks.py`.
- **Correction to platform.md.** It records OBDb `freq` as Hz; the schema defines it **in seconds**.
- **Exporters.** OBDb signalset + `test_cases` (for upstream PRs); DBC via cantools (for passive CAN signals); Torque CSV.
- **Importers.** OBDb JSON; DBC; ODX via odxtools (user's own data only).
- **Captures.** The ESP32 `[ms] hex` log with `>>>` markers (K-line), and candump `(ts) can0 123#…` (CAN), bundled as `trace.json` with markers, the interface, the bitrate and the coarse descriptor.

## 5. Privacy and legal

- **VIN.** Decode it locally (§1.3). Strip it from every artefact: Mode 09 `02` replies, UDS `F190`, KWP `1A 87/90`. The same goes for ECU serials (`F18C`), immobiliser/EKA codes and seed/key pairs. A `scrub` tool runs before any fixture commit or upload, and the CI fails if a 17-char VIN pattern or a known identity DID appears in `tests/`.
- **Traces.** Community upload stays **opt-in**, whitelist-built and anonymous (`community/__init__.py`). Full traces are shared only after scrubbing, after the user previews the exact payload, and with GPS, timestamps and odometer removed or coarsened. Contributed data is CC BY-SA 4.0, like OBDb, so it can flow upstream.
- **DMCA §1201.** The Copyright Office's exemption at 37 CFR 201.40(b)(13), renewed in 2024 (<https://www.copyright.gov/1201/2024/>), lets owners circumvent access controls on vehicle software **for diagnosis, repair or lawful modification**. It does **not** cover trafficking in circumvention tools, it excludes violations of DOT/EPA rules, and it does not reach other copyrighted works such as entertainment content. SEMA has petitioned to renew it for 2027. Our reading-and-sniffing pipeline mostly needs no circumvention at all. Where a pack needs security access (D2 BCU keygen, ADR-0007), it stays `gated`, is documented as the owner's repair use, and is never offered as a generic unlock tool. This is a summary of research, not legal advice; outside the US, check local law (EU interoperability rules differ).
- **Dealer data.** Never ship dealer databases or anything converted from them (ODX/PDX, SDD, CBF, SMR-D, ddt4all or pyren DBs, NanoCom internals). OpenVehicleDiag's SMR-D parser was taken down by DMCA. Values *observed on the wire* while a lawfully used tool runs are facts we record. The tool's software, databases and screen text in bulk are not ours to copy.
- **Code licences.** Permissive (MIT/BSD/Apache) we reuse with attribution. GPL-3 we run as an external tool, or reuse with notice under AGPL. Never copy GPL-2.0-only code (python-OBD), non-commercial code (ELM327-emulator, PolyForm NC) or unlicensed code. Algorithms from papers are reimplemented clean-room.

## 6. Recommendation: the Ostler decode pipeline

### 6.1 Stages

| # | Stage | What happens | Tools (existing / **new**) | Output and status reached |
|---|---|---|---|---|
| S0 | **Connect** | Pick the interface, then do listen-only bitrate probing, then ELM `AT SP 0` / OBD auto-detect, then pack probes | transport, ELM driver; **`detect`** | `link.json` (protocol, pins, bitrate) |
| S1 | **Identify** | Local VIN → `{make, year, region}`; Mode 09 CALID / ECU names; KWP `1A`; match pack `detection` | **`vin`** (local WMI table), **pack matcher** | Pack chosen, **or generic_obd2 + "unknown vehicle"** |
| S2 | **Inventory** | Read-only ECU sweep per §1.4 | `modscan.AddressScanner`; **`udsscan`** (udsoncan + can-isotp); **`canids`** (passive ID stats) | `ecus.json`: address, protocol, ident (redacted), answering services |
| S3 | **Baseline** | Read the generic PIDs the bitmaps support; read DTCs (J1979 / `19 02` / `18`) | generic_obd2 pack | A working dashboard on day one |
| S4 | **Capture** | Pick a recipe: dealer-tool sniff with markers, differential toggles, or drive-and-correlate with GPS/IMU/OBD references | ESP32 tap, `esp32_read`, markers, logbook; **`trace` bundler** | Scrubbed `trace.json` |
| S5 | **Correlate** | Propose fields (READ-style bit-flip), then fit against plaintext or reference series | `sniff/automap.py`, `calib.py`; **`bitflip`**, **`correlate`** (lagged cross-correlation) | Ranked proposals with R² and lag |
| S6 | **Label** | A human accepts a proposal and names it (`metric`, `path`, unit, enum `map`) | admin **Label**/**Decode** tabs, `/capture`, `/automap`, `upsert_field` | Signal-store field, `candidate` |
| S7 | **Verify** | Collect more distinct readings and a second car; generate a fixture; get a review | **`fixtures`**, `pytest`, `catalog.py` derivation | `proven` / `verified` with evidence |
| S8 | **Package** | Skeleton → full pack; export OBDb/DBC | **`ostler pack new`**, **OBDb/DBC exporters** | Installable pack + upstreamable data |
| S9 | **Contribute** | Opt-in anonymous readings, or a PR bundle (signalset + fixtures) to the pack repo or OBDb | `community`; **PR bundle export** | Shared, reviewed data |

### 6.2 Per car family

| Family | S0–S2 | Best S4 recipe | Typical ceiling |
|---|---|---|---|
| Generic OBD-II | Auto-detect; bitmaps; `7E8+` replies | None needed; then OBDb overlay | J1979 set + make overlay |
| CAN / UDS | Listen-only ID census; 11/29-bit UDS sweep; `F187/F189` | Drive and correlate for broadcast; tool sniff for `22` DIDs | Full pack + DBC |
| K-line multi-ECU (D2) | modscan per pin; KWP `1A` | Dealer-tool sniff with markers + differential | Full pack (the D2 is the proof) |
| Older / pre-OBD | Manual pick or pack rule; RX tap | Tool sniff, or manual/blink codes | Codes + a few live values |

### 6.3 UI: a Decode mode

**Access and safety.**
- Where it lives: Decode mode is a developer toggle under **More → Developer**, guarded by the existing admin password (the mapping surface already is).
- It grows today's admin **Decode** and **Label** tabs into one guided flow.
- The sniff screens are read-only. Every active scan shows the exact services it will send, and refuses to run while the logbook says the car is moving.

**Screens.**

1. **Detect.** A wizard (S0–S1): link, protocol, coarse identity ("Land Rover, 2001, EU"). The VIN is never shown or stored beyond a masked `SAL…****`. It ends with the pack match, or the unknown-vehicle path.
2. **Scan.** The ECU map from S2 as a list of cards (address, protocol, part/SW, services). Each card links to the catalog coverage.
3. **Sniff.** A live grid per ECU, LID, DID or CAN ID: raw bytes, current decode, a bit-flip heat map and a per-byte range state. This is the SavvyCAN/cabana idea on the existing `/sniff` feed.
4. **Correlate.** Ranked proposals from automap/bitflip/correlate, each plotted against its reference series (plaintext marker, OBD PID, GPS, IMU), with R², lag and scale.
5. **Label.** Today's marker entry and `/capture`. Accept a proposal and set the name, metric, unit and map. The field is written as `candidate`.
6. **Verify.** Per field: an evidence checklist (distinct readings, R², fixture, cars, reviewer). "Make fixture" scrubs and saves. A field is promoted only when the checklist is green.
7. **Contribute.** A preview of the exact JSON that would leave the device. Choose opt-in upload, or export a PR bundle (OBDb signalset + `test_cases`, or a pack patch).

The catalog/coverage map (`CoverageMap.tsx`) stays the progress view. A pack shows `verified/candidate/sniff/untranscribed` counts per ECU.

### 6.4 The unknown-vehicle fallback

When S1 finds no pack:
1. Ostler activates **generic_obd2**. The user gets a normal Home/Diagnose experience with the PIDs the bitmaps report, plus a DTC read and clear.
2. Home shows a dismissible banner: **"Unknown vehicle — help decode it"**, with the coarse identity and the count of ECUs that answered but have no definition.
3. If an OBDb overlay exists for the WMI and year, Ostler offers it, with its items marked `candidate`.
4. The banner opens Decode mode at **Scan**. Every unknown ECU becomes a pack skeleton whose items are `untranscribed` until they are decoded.
5. Nothing is uploaded unless the user opts in at **Contribute**.

On a non-OBD car the same banner leads to "choose your vehicle / start a pack" instead of generic data.

### 6.5 Build order

1. `generic_obd2` pack + `detect` + local `vin`. This removes the `NoVehiclePackError` dead end and proves the platform beyond the D2.
2. `fixtures` + the evidence block + scrub CI. Make the D2's existing proven fields carry fixtures first.
3. OBDb import/export (round-trip the D2 store; upstream a Land Rover Discovery 2 repo).
4. `canids` / `udsscan` / `bitflip` / `correlate`, and the Sniff/Correlate screens.
5. Decode-mode wizard, Verify and Contribute screens.

Each stage gets its own spec in `specs/` before code, per the working rules.

## Sources

- OBDb org, `SAEJ1979`, `.schemas` and the Toyota-RAV4 test cases: <https://github.com/OBDb>, <https://github.com/OBDb/SAEJ1979>, <https://github.com/OBDb/.schemas>, <https://github.com/OBDb/Toyota-RAV4> (CC BY-SA 4.0).
- opendbc and cabana: <https://github.com/commaai/opendbc>, <https://github.com/commaai/openpilot> (MIT). SavvyCAN: <https://github.com/collin80/SavvyCAN> (MIT).
- OVMS docs and code: <https://docs.openvehicles.com/>, <https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3> (MIT, mostly).
- CaringCaribou: <https://github.com/CaringCaribou/caringcaribou> (GPL-3). udsoncan and can-isotp: <https://github.com/pylessard> (MIT). python-OBD: <https://pypi.org/project/obd/> (GPL-2.0-only).
- NHTSA vPIC: <https://vpic.nhtsa.dot.gov/api/>. ELM327 datasheet: <https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf>.
- Papers: READ, Marchetti & Stabili, IEEE TIFS 2019 (<https://iris.unimore.it/handle/11380/1185929>); LibreCAN, Pesé et al., ACM CCS 2019; ByCAN (<https://arxiv.org/pdf/2408.09265>).
- DMCA §1201: <https://www.copyright.gov/1201/2024/>, 37 CFR 201.40(b)(13), and the SEMA 2027 renewal petition (<https://www.copyright.gov/1201/2027/petitions/renewal/Renewal-Pet-Vehicle-Repair-SEMA.pdf>).
- Internal sources: `src/openostler/{sniff,catalog.py,modscan.py,pack.py,community}`; pack `references/nanocom_capture_protocol.md` and `protocol_state_handoff.md`; ADR-0003/0006/0008/0012/0013/0015; `references/research/landscape.md` and `platform.md`.
