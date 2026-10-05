---
title: "OVMS reuse audit: decoded vehicles, licences, and an import pipeline"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/ovms.md, references/research/ui/ovms_ui.md]
summary: >
  An inventory of all 48 OVMS v3 vehicle modules (plus 2 v2-only ones): what each decodes, over which bus, under which licence, and how well it is maintained. It separates what Ostler can reuse as data (DIDs, scalings, CAN IDs) from what it can reuse as code, compares OVMS with OBDb, designs a `tools/import_ovms.py` pipeline with worked examples, and recommends the first imports, an OVMS→VSS alias table, and gauge ideas. OVMS is almost entirely EV and CAN, has no K-line, and has nothing for the D2.
---

# OVMS reuse audit

This audit extends [ovms.md](ovms.md), which covers interop, MQTT, power and the poller, and
[ovms_ui.md](ui/ovms_ui.md), which covers UI structure and app licences. Neither is repeated here.

**Sources read.** Clones were made in a scratchpad, outside this repo, and nothing was vendored:
- [OVMS3](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3) at
  `7c87784` (2026-10-03; last tag 3.3.006);
- [OVMS v2](https://github.com/openvehicles/Open-Vehicle-Monitoring-System) at `260a842` (2021);
- [Android](https://github.com/openvehicles/Open-Vehicle-Android) at `e4b1b53`;
- [react-native-vehicle-gauges](https://github.com/openvehicles/react-native-vehicle-gauges) at `8cc8505`;
- 33 [OBDb](https://github.com/OBDb) repos (SHAs are in the overlap table).

All paths below are relative to `vehicle/OVMS.V3/components/` at `7c87784`. The full per-module
record is in [ovms_vehicle_inventory.json](ovms_vehicle_inventory.json): one object per
module, with buses, poll types, counts, signals, commands, licence, maintenance and the matching OBDb repo.

## TL;DR

1. **48 `vehicle_*` components** fall into these groups:
   - 37 production EVs (36 plus the NIU scooter);
   - 1 PHEV (Volt/Ampera);
   - **3 ICE cars**: Cadillac CTS 2008–14, Cadillac CT5 2020–26 and Corvette C6 2005–13;
   - the generic OBD-II module;
   - 2 EV-conversion controllers;
   - 4 utility modules: DBC, demo, none and track.
   v2 adds only two small EVs (Kyburz, Tazzari).
2. **Everything is CAN.**
   - **There is no K-line vehicle code.** VW TP2.0 is in the poller but no module uses it.
   - The modules hold about 3,200 poll-table entries and about 490 passive CAN IDs.
   - About 2,050 of the poll entries are generated BMW i3 and Mini SE tables under **GPL-3.0**, derived from BMW SGBD data. **Exclude them.**
3. **Nothing here helps the D2 directly.** The only **JLR** content is `vehicle_jaguaripace` (2021, dormant). Its value is a **map of 45 JLR UDS ECU addresses** and about 25 BECM/TPMS/HVAC DIDs. Those match what OBDb's `Land-Rover`, `Land-Rover-Defender` and `Jaguar-I-PACE` repos publish, so they are good cross-check evidence for a future CAN-era JLR pack.
4. **The ICE modules are thin.**
   - They poll the 7 J1979 PIDs that OBDb's SAEJ1979 already covers.
   - On top of that they add a few passive GMLAN frames: VIN halves, engine running, C6 TPMS and CT5 fuel.
   - They store fuel in `v.b.soc` and coolant in `v.b.temp`, because the OVMS metric tree has no ICE names.
5. **`vehicle_obdii` is a stub.** It has 8 PIDs (SAEJ1979 in OBDb has 103 commands and 294 signals), CAN 500 kbit/s only, no DTCs, no support bitmap and no 29-bit addressing, and it was last touched in 2023. Use OBDb instead.
6. **Where OBDb also has a model, OBDb is the better source for polled data in most of the roughly 20 overlapping modules.** It uses the same schema we adopted, is licensed CC BY-SA, and has YAML test cases (the Bolt has 1,319). OVMS uniquely adds:
   - passive-CAN decodes;
   - state semantics: charge states and the poll state machine;
   - roughly 15 models OBDb lacks or leaves empty: Maxus ×4, Atto 3, Twizy, i-MiEV, Think, B250e, Energica, NIU and others.
7. **Quality is uneven, and there are almost no tests.** Only `vehicle_vwegolf` ships native tests and a `.dbc`. Bugs found on a quick read:
   - the I-PACE stores TPMS pressure unscaled, and its rear-left/rear-right order disagrees with OBDb;
   - the C6 fuel level is divided by 256, not 255;
   - the CTS polls RPM but never decodes it;
   - the I-PACE handles battery current but never polls it.
8. **Licence edge cases inside "MIT":**
   - **GPL-3** `ecu_definitions/` in `bmwi3` and `minise`;
   - the Roadster `*_ctp.*` files are "License granted for inclusion on OVMS", which is **not MIT**;
   - the Zoe Ph1 PID list is "extracted from CanZE" (GPL-3);
   - smart EQ and Zoe Ph2 carry **DDT4all** command sets, which come from a dealer database.
9. **What to reuse as code: almost nothing.**
   - It is ESP-IDF C++. Python already has MIT ISO-TP/UDS libraries, and cantools for DBC.
   - Copy **designs** instead: per-state poll intervals with start offsets, once-off poll series, handling of NRC 0x78 (response pending), and the TP2.0 state machine if a VW pack ever needs it.
   - The **gauge geometry** from react-native-vehicle-gauges (MIT) is worth porting to DOM SVG.
10. **Recommendation:**
    - Build the **OVMS→VSS alias table now** from `main/metrics_standard.{h,cpp}`: 207 names, 169 of them vehicle names, about half with a direct VSS leaf.
    - Write `import_ovms.py` as a cross-check and gap-filler next to the OBDb importer, never as a primary source.
    - Import first: **I-PACE, Volt, the GM ICE trio, Leaf and Maxus eDeliver 3**.

## 1. Licences, per repo and per directory

| Repo / path | Licence found | Use in Ostler (AGPL-3.0 code, CC BY-SA 4.0 data, dual commercial, ADR-0012) |
|---|---|---|
| OVMS3 root `LICENSE` | MIT for "the majority"; "Software which uses other licenses will be annotated" | Port with the notice kept: `Copyright (c) 2011-2017 Open Vehicles` plus the MIT text, plus each file's `(C)` lines (e.g. `ipace_*.cpp`: "(C) 2021 Didier Ernotte"; `vehicle_voltampera.cpp`: Stegen, Webb-Johnson, Sonny Chen, Juhanne, Kiiashko) |
| 45 of 48 vehicle dirs | Every `.cpp`/`.h` has the MIT header, or none (repo MIT applies: `maxus_t90`, `energica/*_pids.h`, `kiasoulev/kia_common.*`, `vwegolf/tests/mock`) | OK |
| `vehicle_bmwi3/ecu_definitions`, `dev/*.json`; same in `vehicle_minise` | **GPL-3.0**: "derived from the Ediabaslib project … DeepOBD"; generated by `tools/generate_ecu_code.pl` | GPL-3 is AGPL-compatible but **cannot enter the commercial build or CC BY-SA data**, and the lineage is BMW SGBD (dealer data, ADR-0012 "No"). **Exclude.** |
| `vehicle_teslaroadster/src/vehicle_teslaroadster_ctp.*` | "Copyright (c) 2013-2018 Tom Saxton. License granted for inclusion on OVMS." | **Not reusable**; ideas only |
| `vehicle_renaultzoe/docs/PIDs_Renault_Zoe.txt` | Says "extraidos de CanZE Fields.java" (CanZE: GPL-3.0) | Facts are usable with attribution to CanZE; keep them out of commercial-only artefacts |
| `vehicle_smarteq` (eq_poller.h, eq_commands.cpp), `vehicle_renaultzoe_ph2/rz2_commands_ddt.cpp` | MIT headers, but DDT4all-derived requests (40× `2E` writes in SQ) | Read-only DIDs may be cross-checked; **never import the write payloads** |
| `vehicle_vwegolf/src/bap/*` | MIT, "(C) 2026 Jona Wagner" (SPDX MIT) | OK |
| `vehicle_vwegolf/docs/vwegolf.dbc` | Repo MIT | Directly importable with cantools: 27 messages, 60 signals |
| OVMS v2 | MIT (majority) | Only Kyburz and Tazzari are new; trivial |
| Android | MIT (majority); see ovms_ui.md | No vehicle decodes; UI ideas only |
| react-native-vehicle-gauges | MIT, "Copyright (c) 2024 React Native Vehicle Gauges" (author Mark Webb-Johnson) | Port the geometry with the notice kept |
| Firmware third-party code | mongoose, wolfSSL (GPL-2), wolfSSH (GPL-3), Highcharts (non-commercial) | Never copy (ovms.md, ovms_ui.md) |

**Facts and attribution.**
- Request IDs, offsets and scalings are facts and are not copyrightable.
- A substantial extraction of tables could still touch UK/EU **database right**. The MIT grant covers that, provided the notice travels with the data.
- So every imported signal carries `x-ostler.evidence.source` (repo URL, SHA, file and line).
- The pack's `THIRD_PARTY_LICENSES.md` carries the OVMS MIT notice and the per-file `(C)` lines.
- This is the same practice as CC BY-SA attribution.

## 2. Inventory of all 48 modules

The table is generated by a regex scan, then hand-checked for the ICE and JLR rows.

**Columns:**
- **Polls/ECUs**: `poll_pid_t` entries and distinct request IDs.
- **CAN**: passive IDs in `switch(MsgID)`, with `#ifdef notdef` excluded.
- **Signals**: which standard metrics are set. This is approximate: ICE modules reuse EV metrics, and grep can over-match.
- **Cmds**: overridden `Command*` virtuals. **(W)** means raw CAN writes or UDS write, IO or security services.
- **Last · n**: the last commit, and the number of commits since 2025-01-01.
- **Buses**: kbit/s; `L` means listen-only.

| Module | Make, model (years) | PT | Buses | Polls/ECUs | CAN | Signals | Cmds | Last · n | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `bmwi3` | BMW i3/i3s (2013–22) | EV (REx opt.) | 500 | 1024/15 ExtAdr | – | SOC,SOH,odo,doors,lock,clim,VIN,fuel(REx) | – | 2024-04 · 0 | GPL-3 SGBD-derived tables; exclude |
| `boltev` | Chevrolet Bolt EV / Opel Ampera-e (2017–23) | EV | 500/33 SWCAN | 19/5 | 34 | SOC,cells,TPMS,odo,doors,lock,clim,VIN,12V,DTC | lock,clim,chg,wake,hl (W) | 2026-05 · 6 | |
| `byd_atto3` | BYD Atto 3 (2022–) | EV | 500 | 6/1 | 7 | SOC,odo,gear,charge state | – | 2025-05 · 1 | OBDb repo empty |
| `cadillac_c2_cts` | **Cadillac CTS gen 2 (2008–14)** | **ICE** | 500 + 33 SWCAN | 7/1 J1979 | 3 | coolant, speed, IAT, fuel, ambient, oil; VIN (29-bit `0x10024040/…6040`); running `0x134` | wake (W, SWCAN `0x102`) | 2026-03 · 1 | RPM polled, not decoded; most CAN cases `#ifdef notdef` |
| `cadillac_ct5` | **Cadillac CT5 (2020–26)** | **ICE** | 500 L (amp bus #5) | – | 4 | running `0x063`, fuel `0x5E4`, VIN `0x75F`+`0x49B` | – | 2026-07 · 3 | Global B blocks polling; custom cable |
| `chevrolet_c6_corvette` | **Chevrolet Corvette C6 (2005–13)** | **ICE** | 500 | 7/1 J1979 | 4 | J1979 ×7; VIN `0x670`+`0x131`; running `0x300`; TPMS ×4 `0x390` | – | 2026-03 · 2 | fuel `>>8` (÷256) |
| `dbc` | DBC-driven (any) | any | per DBC, L | – | – | as mapped | – | 2025-04 · 2 | "experimental" |
| `demo` | Demo | sim | – | – | – | all (fake) | all | 2024-04 · 0 | |
| `energica` | Energica motorbikes (2014–24) | EV | 500 | – | 8 | SOC,SOH,odo,rpm | – | 2026-06 · 2 | |
| `fiat500` | Fiat 500e (2013–19) | EV | 500/50 | – | 15 | SOC,odo,doors,lock,clim | lock,chg,wake,hl,valet (W) | 2024-04 · 0 | 40 raw writes |
| `fiatedoblo` | Fiat e-Doblò (2022–24) | EV | 500 | 18/4 | 13 | SOC,SOH,odo,doors,lock,clim,VIN | – | 2026-06 · 9 | |
| `hyundai_ioniq5` | Hyundai Ioniq 5 / Kia EV6 (2021–) | EV | 500 | 30/6 | – | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V | lock,wake (W) | 2026-05 · 16 | |
| `hyundai_ioniqvfl` | Hyundai Ioniq Electric pre-FL (2016–19) | EV | 500 | 9/5 | – | SOC,SOH,cells,TPMS,odo,doors,VIN | – | 2026-06 · 4 | |
| `jaguaripace` | **Jaguar I-PACE (2018–24)** | EV | 500 | 29/5 | – | BECM SOC/SOH/cell V/temps/regen, odo `DD01`, cabin, VIN `F190`, ambient, speed, TPMS ×8, GPS | – | 2024-01 · 0 | only JLR module; see §4 |
| `kianiroev` | Kia e-Niro / Hyundai Kona EV / Ioniq FL (2018–24) | EV | 500 | 23/9 | – | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V | lock (W) | 2026-09 · 6 | |
| `kiasoulev` | Kia Soul EV gen 1 (2014–19) | EV | 500/100 | 11/5 | 27 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V | lock (W) | 2026-09 · 4 | |
| `maple60s` | Maple 60S (2021–) | EV | 500 L | – | 9 | SOC,odo,doors,lock | – | 2025-12 · 1 | no docs |
| `maxus_edeliver3` | Maxus eDeliver 3 (2020–) | EV | 500 | 19/2 | 4 | SOC,SOH,cells,odo,doors,VIN,12V | – | 2026-03 · 2 | OBDb repo empty |
| `maxus_euniq56` | Maxus Euniq 5 (2022–) | EV | 500 | 19/2 | 4 | as eDeliver 3 | – | 2026-01 · 1 | copy of eDeliver 3 |
| `maxus_euniq6` | Maxus Euniq 6 (2022–) | EV | 500 | 7/2 | 7 | SOC,TPMS,odo,doors,lock | – | 2025-12 · 1 | |
| `maxus_t90` | Maxus T90 EV (2022–) | EV | 500 | 7/1 | 2 | SOC,SOH,odo,lock,VIN | – | 2025-11 · 1 | no header |
| `mercedesb250e` | Mercedes B250e W242 (2014–17) | EV | 500 | – | 11 | TPMS,odo,clim,12V | – | 2024-04 · 0 | |
| `mgev` | MG ZS EV (A/B/D), MG4, MG5 (2019–23) | EV | 500 (bus configurable) | 304/11 | 1 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V | wake (W: `27`,`2F`,`31` gateway wake) | 2026-01 · 2 | |
| `minise` | Mini Cooper SE F56 (2020–24) | EV | 500 | 1022/15 ExtAdr | – | as i3 | – | 2023-11 · 0 | GPL-3 SGBD-derived tables; exclude |
| `mitsubishi` | i-MiEV / C-Zero / iOn (2009–20) | EV | 500 | 6/4 | 25 | SOC,SOH,cells,odo,doors,lock,clim,VIN,12V | – | 2026-01 · 1 | |
| `nissanleaf` | Nissan Leaf / e-NV200 (2011–24) | EV | 500 ×2 | 17/2 | 29 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V,DTC | lock,clim,chg,wake,hl (W) | 2026-09 · 135 | most active |
| `niu_gtevo` | NIU MQi GT EVO (2023–) | EV | 500 | – | 30 | SOC,SOH,cells,odo,lock,DTC | chg,wake,hl (W) | 2026-03 · 4 | |
| `none` | Empty | – | – | – | – | – | – | 2023-02 · 0 | |
| `obdii` | **Generic OBD-II over CAN** | ICE | 500 only | 8/1 (`7DF`) | – | J1979 `05,0C,0D,0F,2F,46,5C` + `09 02` VIN | – | 2023-11 · 0 | fuel→`v.b.soc`, coolant→`v.b.temp`, IAT→`v.i.temp`, oil→`v.m.temp` |
| `renaulttwizy` | Renault Twizy (2012–23) | EV | 500 | 4/1 | 20 | SOC,SOH,cells,odo,lock,VIN,DTC | lock,chg,valet (W: SEVCON) | 2026-01 · 6 | 13 k lines |
| `renaultzoe` | Renault Zoe Ph1 / Kangoo ZE (2012–19) | EV | 500 | 12/3 | 61 | SOC,SOH,cells,TPMS,odo,doors,lock,VIN,12V | lock,clim,wake,hl,valet (W) | 2026-05 · 4 | CanZE lineage |
| `renaultzoe_ph2` | Renault Zoe Ph2 (2019–24) | EV | 500 | 334/6 (281 29-bit) | 1 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V | lock,clim,wake,hl (W: DDT `2E`/`31`) | 2026-09 · 10 | |
| `smarted` | smart ED 451 (2012–15) | EV | 500 ×2 | 38/3 | 23 | SOC,SOH,cells,odo,doors,lock,clim,VIN,12V | lock,clim,chg,wake,hl,valet (W) | 2026-05 · 5 | |
| `smarteq` | smart EQ 453 (2017–24) | EV | 500 | 51 (0x21 groups) | 13 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V | lock,clim,chg,wake,hl,valet (W: 40× `2E`) | 2026-09 · 328 | DDT4all lineage |
| `subaru_solterra` | Subaru Solterra (2022–) | EV | via e-TNGA | (inherits) | – | – | – | 2026-09 · 2 | 96-line subclass |
| `teslamodel3` | Tesla Model 3 | EV | – | – | – | – | – | 2024-04 · 0 | empty stub |
| `teslamodels` | Tesla Model S (2012–20) | EV | 500/500/125 | – | 17 | SOC,cells,TPMS,odo,doors,VIN | – (W) | 2024-04 · 0 | |
| `teslaroadster` | Tesla Roadster (2008–12) | EV | 1000 | – | 5 (muxed `0x100`) | SOC,SOH,TPMS,odo,doors,lock,clim,VIN,DTC | lock,chg,wake,hl,valet (W) | 2024-04 · 0 | CTP files not MIT |
| `thinkcity` | Think City (2008–12) | EV | 500 | 4/1 | 12 | SOC,TPMS | lock,valet | 2026-01 · 6 | |
| `toyota_bz4x` | Toyota bZ4X (2022–) | EV | via e-TNGA | (inherits) | – | – | – | 2026-09 · 2 | subclass |
| `toyota_etnga` | e-TNGA base | EV | 500 (CAN2) | 66/6 | – | SOC,SOH,cells,TPMS,odo,doors,clim,VIN,12V | – | 2026-09 · 2 | new |
| `toyotarav4ev` | Toyota RAV4 EV (2012–14) | EV | 500 ×2 | – | 15 | SOC,cells,odo,doors | – | 2024-04 · 0 | |
| `track` | GPS tracking only | – | – | – | – | – | – | 2023-02 · 0 | |
| `voltampera` | **Chevrolet Volt / Opel-Vauxhall Ampera (2011–19)** | **PHEV** | 500/500/33/33 | 29/7 | 43 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V,**fuel, coolant, fuel used/economy, engine mode** | lock,clim,chg,wake,hl (W) + `xva engine on/off` | 2026-08 · 5 | only real engine data |
| `vwegolf` | VW e-Golf (2014–20) | EV | 500 L FCAN / 500 KCAN | – | 24 | SOC,odo,doors,lock,clim,VIN | lock,clim,chg,wake (W) | 2026-09 · 57 | tests + `.dbc` |
| `vweup` | VW e-Up / Citigo-e / Mii (2013–23) | EV | 500 / 100 (T26) | 55 (runtime vector) | 19 | SOC,SOH,cells,TPMS,odo,doors,lock,clim,VIN,12V,DTC | lock,clim,chg,wake,hl,valet (W) | 2026-05 · 21 | |
| `zeva` | ZEVA BMS (conversion) | EV | 250 | – | 1 | SOC,SOH,cells | many (defaults) | 2024-04 · 0 | |
| `zombie_vcu` | ZombieVerter VCU (conversion) | EV | 500 | 14/1 (`0x2A` custom) | – | SOC | – | 2025-12 · 1 | |
| v2 `kyburz.c` | Kyburz DXP | EV | 125 | 2 DIDs | – | SOC, charge current | – | 2021 | v2 only |
| v2 `tazzari.c` | Tazzari Zero | EV | – | 5 DIDs | – | SOC, batt temp, capacity, charge state | – | 2021 | v2 only |

**Counts by powertrain (v3, 48):**

| Group | Count |
|---|---|
| EV | 37 |
| PHEV | 1 |
| ICE | 3 |
| Generic ICE OBD-II | 1 |
| Conversion | 2 |
| Utility | 4 |

**Counts by access:**

| Access | Count |
|---|---|
| Poll + passive | 21 |
| Passive only | 11 |
| Poll only | 9 |
| None or inherited | 7 |

**Protocols:**
- **CAN speeds:** 500 kbit/s on every module. 33.3 k SWCAN on GM (Bolt, Volt, CTS); 50 k on the Fiat 500e; 100 k on the Soul and e-Up; 125 k on the Model S; 250 k on ZEVA; 1 M on the Roadster.
- **ISO-TP addressing:** standard 11-bit in nearly all; extended addressing in the i3, Mini and e-TNGA; 29-bit extended frames in Zoe Ph2.
- **Services:** `22` ReadDataByIdentifier dominates. Others: `21` local IDs (Kia, Leaf, i-MiEV, Twizy, smart EQ), GMLAN `1A` (Volt, Niro), J1979 `01`/`09` (generic, GM ICE, MG) and the custom `2A` (Zombie).
- **No K-line, J1850 or KWP-on-K-line** anywhere.
- **ICE and older vehicles:** CTS, CT5, C6 Corvette and generic OBD-II. The Volt is the only real engine decode. The oldest models covered are the Roadster (2008) and the C6 (2005), both CAN.

**Land Rover / JLR / Rover content:** `vehicle_jaguaripace` only. There is nothing for Rover, MG Rover (the MG modules are SAIC EVs), Land Rover, or any K-line LR.

**`vehicle_obdii`:**
- `src/vehicle_obdii.cpp` is 187 lines and has 8 polls on functional `0x7DF`.
- It has no support-bitmap walk, no DTC read, no 29-bit addressing and no freeze frame, and it maps meanings onto EV metrics.
- Poll state 1 is entered when RPM > 0.
- About **5% of OBDb SAEJ1979** (103 commands, 294 signals). **Do not import it.**

## 3. Reuse as data versus as code

| Asset | Where | As data | As code | Verdict |
|---|---|---|---|---|
| Poll tables (`poll_pid_t`) | each module | **Yes**: tx/rx, service, DID, per-state intervals | – | Import through §4, as `candidate` |
| Handler maths (`IncomingPollReply`) | each module | **Partly**: byte offsets and scaling where the expression is simple | – | Parse simple expressions; flag the rest |
| Passive CAN decodes | `IncomingFrameCan*` | **Yes**: ID, bytes, scaling, mux guard | – | Emit as broadcast signals, exported to DBC |
| Poller design | `poller/src/vehicle_poller*.{h,cpp}` (ISO-TP 566 lines, TP2.0 844) | – | Ideas | Copy: `polltime[state]` plus `.ts` start offsets to stagger polls; once-off `PollSeriesEntry`; throttling; NRC `0x78` wait. Implement in Python over can-isotp/udsoncan (MIT). Port TP2.0 (MIT, keep the notice) only if a pre-2010 VW pack appears |
| ISO-TP/UDS framing | same | – | No | ESP32 TWAI-bound; Python libraries already exist |
| DBC component | `dbc/` (bison/flex C++, MIT) | `vwegolf.dbc` only | No | Use cantools; import `vwegolf.dbc` directly |
| `metrics_standard.{h,cpp}` | `main/` | **Yes**: 207 names with type, staleness and unit | – | Basis of the alias table (§6) |
| Unit enum and `UnitConvert` | `main/ovms_metrics.{h,cpp}` | Unit list as a checklist | No | Trivial; it has **no litre or fuel units** |
| PID scanner | `retools_pidscan/` | – | Idea | Same UX as our Decode-mode Scan: `<bus> <ecu> <start> <end> -s step -t type` |
| Web UI widgets | `ovms_webserver/` | – | No | Highcharts is non-commercial; ideas are in ovms_ui.md |
| RN gauges | `src/components/Gauge*.tsx` (2.8 k lines) | – | **Port geometry** | §6 |
| Vehicle docs (`docs/index.rst`) | each module | Wiring and pinout facts (CTS OnStar J1, CT5 amp X1) | – | Cite in pack docs |

## 4. Import pipeline design (`tools/import_ovms.py`, design only)

**Inputs and outputs:**
- **Inputs:** an OVMS3 checkout, a pinned SHA, a module name, and optionally the matching OBDb repo.
- **Output:** written to `build/ovms_import/<module>/` and never committed straight. A human promotes it into a pack repo.

**Stages:**
1. **Parse.**
   - Use tree-sitter-cpp (MIT) over the module's `src/`, with `#ifdef notdef` and `//` blocks stripped.
   - Build a symbol table from `#define`, `static const` and `enum` (I-PACE `becmId=0x7e4u`, `rxFlag=0x8`; e-Up `VWUP_BAT_MGMT` expands to two fields).
   - Collect every `poll_pid_t` initialiser in `{tx, rx, type, pid, {polltime…}|{.ts=…}, bus, proto}`.
   - Entries built at runtime (`m_poll_vector.push_back`, as in vweup and smarted) are listed for review only.
2. **Map handlers.**
   - Starting from `IncomingPollReply`, follow `switch(job.moduleid_rec|job.pid)` and calls into sub-handlers (`IncomingBecmPoll`).
   - In each `case`, find `X->SetValue(expr)` and `SetElemValue(idx, expr)`.
   - Resolve `value8/value16/value24`, `data[i]`, `(d[i]<<8|d[j])`, `* k`, `/ k`, `- k` and `- 0x28` against the locals' declarations, giving `fmt{bix,len,sign,mul,div,add}`.
   - Anything else (state machines, `mlremain` multi-frame accumulation, cross-metric maths such as `power = V*I`) becomes `needs_review`, with a snippet hash and line.
3. **Passive CAN.**
   - For each `switch(p_frame->MsgID)` case, run the same expression grammar over `d[i]`.
   - Nested `switch(d[0])` gives a mux signal.
   - The output is `x-ostler.broadcast` signals, plus a generated `.dbc` (cantools) for exchange.
4. **Name.**
   - The metric target (`StandardMetrics.ms_v_*` or `MyMetrics.Init*("x..")`) goes through the alias table to a VSS path.
   - `x<veh>.*` stays pack-private, with the OVMS name kept as an alias.
   - **ICE modules override the metric meaning with the J1979 PID meaning** (rule: `01 2F` is always fuel level, whatever the metric).
5. **Cross-check.** Diff against OBDb on `(hdr, cmd, bix, len, mul/div/add)`, giving `agree`, `conflict`, `ovms_only` or `obdb_only`.
   - Agreement adds evidence but **imports never rise above `candidate`** (UI spec §8.3).
   - A conflict blocks promotion until a car reading settles it.
6. **Emit.**
   - **`vehicle.json`:** detection left `TODO`; type codes kept as hints.
   - **`ecus/<hdr>.json`:** names come from constant comments (e.g. "Battery Energy Control Module").
   - **`signals/<ecu>.json`:** in OBDb `commands[]` form, with `x-ostler`.
   - **`actions.json`:** each `Command*` override is listed as `{status: untranscribed, safety: gated}`. **No request bytes are copied for any write, IO control, routine or security-access service.**
   - **`NOTICE`:** the OVMS MIT text plus the file's `(C)` lines.
   - **`report.md`:** coverage, conflicts and `needs_review`.
7. **Freq.** OBDb `freq` (seconds) is the smallest non-zero `polltime` in the "on" state, or else in "awake". The full array goes in `x-ostler.poll.states` (off, awake, on, charging).

### Worked example 1: Volt fuel level (ICE-relevant, agrees with OBDb)

The source is `vehicle_voltampera/src/vehicle_voltampera.cpp`:
- line 122 declares `{ 0x7e0, 0x7e8, VEHICLE_POLL_TYPE_OBDIIEXTENDED, 0x002F, { 0, 600, 0, 0 }, 0, ISOTP_STD }`;
- line 1566 decodes it with `mt_fuel_level->SetValue((int)value * 100 / 255)` (custom metric `xva.v.e.fuel`, Percentage).

```json
{ "hdr": "7E0", "rax": "7E8", "proto": "15765-4", "cmd": {"22": "002F"}, "freq": 600,
  "signals": [{ "id": "VOLT_FUEL_LEVEL", "name": "Fuel level", "path": "Fuel",
    "fmt": {"len": 8, "mul": 100, "div": 255, "unit": "percent"}, "suggestedMetric": "fuelTankLevel",
    "x-ostler": { "vss": "Vehicle.Powertrain.FuelSystem.RelativeLevel", "ovms": "xva.v.e.fuel",
      "confidence": "candidate", "span": [0, 100],
      "poll": {"states": {"off": 0, "awake": 600, "on": 0, "charging": 0}},
      "evidence": {"source": "ovms3@7c87784:vehicle_voltampera/src/vehicle_voltampera.cpp#L122,L1566",
        "crosscheck": {"OBDb/Chevrolet-Volt@7d57c6b": "agree (VOLT_FLI)"}, "readings": 0, "fixtures": 0}}}]}
```

**A human checks two things:**
- The OVMS polls only while parked ("awake"). Ostler would poll while driving too, so the right rate needs a choice.
- The OVMS uses integer truncation, which the `fmt` drops.

### Worked example 2: Corvette C6 TPMS (passive GMLAN; no OBDb equivalent)

The source is `vehicle_chevrolet_c6_corvette.cpp`, `case 0x390`. It accepts the frame `if (len == 6 && ((d[0]<<8)|d[1]) == 0x1111)` and decodes `SetElemValue(FL, d[2]*4.0, kPa)`. `d[3]` is RL, `d[4]` is RR and `d[5]` is FR.

```json
{ "x-ostler": {"broadcast": {"bus": "HS-GMLAN", "bitrate": 500000, "id": "0x390", "dlc": 6,
    "guard": {"bix": 0, "len": 16, "equals": "0x1111"}}},
  "signals": [
    { "id": "C6_TP_FL", "fmt": {"bix": 16, "len": 8, "mul": 4, "unit": "kilopascal"},
      "suggestedMetric": "frontLeftTirePressure",
      "x-ostler": {"vss": "Vehicle.Chassis.Axle.Row1.Wheel.Left.Tire.Pressure", "ovms": "v.t.pressure[fl]",
        "confidence": "candidate", "evidence": {"source": "ovms3@7c87784:vehicle_chevrolet_c6_corvette/src/vehicle_chevrolet_c6_corvette.cpp case 0x390"}}},
    { "id": "C6_TP_RL", "fmt": {"bix": 24, "len": 8, "mul": 4, "unit": "kilopascal"}, "x-ostler": {"vss": "…Row2.Wheel.Left.Tire.Pressure"}},
    { "id": "C6_TP_RR", "fmt": {"bix": 32, "len": 8, "mul": 4, "unit": "kilopascal"}, "x-ostler": {"vss": "…Row2.Wheel.Right.Tire.Pressure"}},
    { "id": "C6_TP_FR", "fmt": {"bix": 40, "len": 8, "mul": 4, "unit": "kilopascal"}, "x-ostler": {"vss": "…Row1.Wheel.Right.Tire.Pressure"}}]}
```

**A human checks two things:**
- The **FL, RL, RR, FR** byte order is unusual and needs a car check.
- OBDb's Corvette repo has polled TPMS (`hdr 241`, DIDs `5005…`), which should be preferred when actively polling.

### Worked example 3: Jaguar I-PACE BECM SOC (agrees) and TPMS (conflicts)

The source is `vehicle_jaguaripace/src/`:
- `vehicle_jaguaripace.cpp:40` declares `{ becmId, becmId | rxFlag, OBDIIEXTENDED, batterySoCPid, {0,30,30,60}, 0, ISOTP_STD }`;
- `ipace_obd_pids.h` defines `becmId=0x7e4`, `rxFlag=0x8` and `batterySoCPid=0x4910`;
- `ipace_poll_becm.cpp:65` decodes it with `ms_v_bat_soc->SetValue(value16 / 100.0f)`.

```json
{ "hdr": "7E4", "rax": "7EC", "proto": "15765-4", "cmd": {"22": "4910"}, "freq": 30,
  "signals": [{ "id": "IPACE_SOC", "fmt": {"len": 16, "div": 100, "unit": "percent"},
    "suggestedMetric": "stateOfCharge",
    "x-ostler": {"vss": "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current", "ovms": "v.b.soc",
      "confidence": "candidate", "poll": {"states": {"off": 0, "awake": 30, "on": 30, "charging": 60}},
      "evidence": {"source": "ovms3@7c87784:vehicle_jaguaripace/src/ipace_poll_becm.cpp#L65",
        "crosscheck": {"OBDb/Jaguar-I-PACE@922ebf8": "agree (IPACE_SOC)", "OBDb/Land-Rover@42ae6fd": "agree (LANDROVER_SOC)"}}}}]}
```

The same run on **TPMS `0x751` / `22 2076`** reports a **conflict**:
- **Scaling:** OVMS stores `value16` with no scaling, whereas OBDb reads `bix 8, len 8, mul 0.01373` bar.
- **Wheel order:** OVMS maps `2078` to RL and `2079` to RR; OBDb has them the other way round.
- **Outcome:** both are recorded and the signal is not promoted. **A human must take a car reading.**

**Never automatic:**
- multi-frame cell arrays (`BmsSetCellVoltage` loops);
- `PollSetState` logic;
- muxed frames (Roadster `0x100`);
- derived metrics (power, consumption, range);
- variant selection (MG A/B/D, Leaf ZE0/AZE0/ZE1);
- runtime poll vectors (e-Up, smart);
- handlers for DIDs that are never polled;
- every command.

**A human always checks:**
- units and signedness against a fixture;
- metric semantics in ICE modules;
- wheel order;
- provenance (CanZE, DDT4all, SGBD);
- that no write payload slipped through.

## 5. OBDb versus OVMS overlap

The OBDb columns give commands, signals and YAML test files at the SHA probed on 2026-10-05.

| OVMS module | OBDb repo @SHA | OVMS (polls + CAN) | OBDb (cmd/sig/tests) | Better source |
|---|---|---|---|---|
| `boltev` | Chevrolet-Bolt-EV @da47244 | 19 + 34 | 294/295/1319 | OBDb polls; OVMS CAN and SWCAN |
| `voltampera` | Chevrolet-Volt @7d57c6b | 29 + 43 | 275/275/1002 | OBDb polls; OVMS CAN, engine mode, charge semantics |
| `cadillac_c2_cts` | Cadillac-CTS @00bf34d | 7 + 3 | 0/0/18 | Neither (use SAEJ1979); OVMS GMLAN VIN/running |
| `cadillac_ct5` | Cadillac-CT5 @45fcc13 | 0 + 4 | 123/126/1 | OBDb, but test whether polling works (OVMS: Global B blocks it); OVMS passive |
| `chevrolet_c6_corvette` | Chevrolet-Corvette @4e20a49 | 7 + 4 | 152/155/112 | OBDb; OVMS `0x390` TPMS and VIN frames |
| `jaguaripace` | Jaguar-I-PACE @922ebf8; Land-Rover @42ae6fd | 29 + 0 | 23/23/76; 74/82/0 | OBDb (scaled, tested); OVMS adds SoH min/max, regen, and the 45-ECU address map |
| `nissanleaf` | Nissan-Leaf @cc1fa6e | 17 + 29 | 43/155/227 | OBDb polls; OVMS CAN, charge and climate states |
| `hyundai_ioniq5` | Hyundai-IONIQ-5 @1343243 | 30 | 38/397/183 | OBDb |
| `kianiroev` | Kia-Niro-EV @39d012c, Hyundai-Kona-Electric @43c5384 | 23 | 64/627/92, 112/760/110 | OBDb |
| `hyundai_ioniqvfl` | Hyundai-IONIQ-Electric @076ab6c | 9 | 118/907/110 | OBDb |
| `kiasoulev` | Kia-Soul @623709d | 11 + 27 | 73/345/248 | OBDb polls; OVMS CAN |
| `bmwi3` / `minise` | BMW-i3 @0a6dcbc / MINI-Cooper-SE @dcf00c2 | 1024 / 1022 (GPL) | 43/146/168 / 7/12/0 | **OBDb only** (licence-clean) |
| `mgev` | MG-ZS-EV @86335be, MG-MG4 @12e80a9 | 304 | 98/189/140, 43/115/132 | Both; OVMS larger, OBDb tested |
| `renaultzoe(_ph2)` | Renault-Zoe @7d96fbf | 12 + 61 / 334 | 193/298/58 | OBDb polls; OVMS CAN (mind CanZE/DDT lineage) |
| `smarted` / `smarteq` | Smart-ForTwo @1c38612 | 38 + 23 / 51 + 13 | 80/329/1 | OBDb; OVMS EQ is DDT4all-tainted |
| `vwegolf` | Volkswagen-e-Golf @c5bc667 | 0 + 24 (+ DBC) | 280/312/253 | Complementary: OBDb polls, OVMS KCAN DBC |
| `vweup` | Volkswagen-e-up @8c49783 | 55 + 19 | 242/248/0 | OBDb polls; OVMS T26 CAN |
| `fiat500` | Fiat-500e @edb4d9f | 0 + 15 | 43/280/4 | Complementary |
| `toyota_etnga` | Toyota-bZ4X @5a6ec53 | 66 | 69/99/201 | Comparable; OBDb tested |
| `byd_atto3`, `maxus_edeliver3`, `teslamodel3/s` | repos exist but are **empty** | 6+7, 19+4, 0+17 | 0 | **OVMS only** |
| i-MiEV, Twizy, Think, B250e, Maxus Euniq/T90, e-Doblò, Energica, NIU, Maple, RAV4 EV, Roadster | none found | – | – | **OVMS only** |

**Rule:**
- For request/response data, prefer OBDb: same schema, CC BY-SA, test cases.
- Import OVMS for passive CAN, for state semantics, and for models OBDb lacks.
- Use OVMS as cross-check evidence everywhere else.

## 6. Recommendations

**Import first:** 1 and 3 are ICE or JLR; 2 is the only engine decode.

| # | Module | Why |
|---|---|---|
| 1 | `jaguaripace` | Proves the cross-check stage against two OBDb repos. Seeds a JLR UDS address map (`0x726` BCM/GWM, `0x733` HVAC, `0x751` TPMS, `0x7E4` BECM…) for a future CAN-era Land Rover pack. Whether Discovery 3/4/5 share it is **unverified**. |
| 2 | `voltampera` | Fuel, coolant, fuel used/economy, plus 43 GMLAN IDs, with 1002 OBDb tests to check against. |
| 3 | GM ICE trio (`chevrolet_c6_corvette`, `cadillac_c2_cts`, `cadillac_ct5`) | One small "GM broadcast" overlay (VIN halves, running flag, TPMS, CT5 fuel) on top of SAEJ1979 and OBDb polls. Small enough to review by hand. |
| 4 | `nissanleaf` | Most active module. Exercises poll + passive + `21` groups, with 227 OBDb tests as an oracle. |
| 5 | `maxus_edeliver3` | OVMS-only coverage (the OBDb repo is empty): a common UK van, 19 DIDs. |

Quick win outside the parser: `vwegolf/docs/vwegolf.dbc` goes straight through cantools into broadcast signals.

**Build the OVMS→VSS alias table now (yes).**
- It is needed for U0 MQTT interop anyway.
- **Source:** parse `main/metrics_standard.cpp`, which gives name, type, staleness and unit for 198 instantiated metrics (169 `v.*`). Map them by hand to VSS (pinned commit `9236923`). Store them in the platform `metrics.json` alias column.
- **Estimated coverage**, by prefix:

  | Prefix | Metrics | Direct VSS leaves (estimate) | VSS target / notes |
  |---|---|---|---|
  | `v.b` | 51 | ≈20 | `TractionBattery.*`, `LowVoltageBattery.*` |
  | `v.c` | 28 | ≈12 | `…Charging.*` |
  | `v.g` | 24 | ≈1 | V2G |
  | `v.d` | 7 | all 7 | `Cabin.Door.*`, `Body.Hood/Trunk` |
  | `v.e` | 29 | ≈15 | |
  | `v.p` | 22 | ≈10 | |
  | `v.t`/`v.tp` | 12 | ≈8 | |
  | `v.m` | 2 | 2 | ambiguous between motor and engine |

  That is **about 80–90 of 169**. The rest are `Vehicle.Ostler.*` or unmapped.
- **Mark explicitly:**
  - OVMS has no fuel, oil or coolant names;
  - `v.m.rpm` and `v.m.temp` mean the motor;
  - `v.tp.*` is deprecated in favour of the `v.t.*` arrays;
  - ICE modules overload `v.b.soc` and `v.b.temp`.
- **Reverse mapping (VSS→OVMS)** for publishing must be one-way and lossy, and must never publish fuel as `v.b.soc`.

**Code to port:**
- No C++.
- Reimplement the poll-scheduler ideas in our Python poller and cite OVMS in a comment: per-state intervals, `.ts` start offsets, once-off series, NRC 0x78, a throttle.
- Keep the MIT notice only if code is transliterated (TP2.0, later).

**Gauges.** The PWA is React DOM, and `react-native-svg` primitives map 1:1 to DOM `<svg>`/`<path>`/`<g>`/`<text>`. `View`/`Text` become `div`/`span`. The library's own Vite demo already aliases RN to `react-native-web`.

Our `ui/src/components/Gauge.tsx` (240° arc and normal band) stays the base. Borrow these ideas, as code with the MIT notice, or as ideas only:

| Gauge | What to borrow | For |
|---|---|---|
| **Tachometer** | redline zone, auto tick step, "×1000" label | Td5 RPM |
| **Temperature** | cold/normal/hot bands | coolant, ATF |
| **Fuel** | E–¼–½–¾–F ticks, low warning | the D2's derived economy and fuel once decoded |
| **Battery** | **half-dial 10–16 V** with a low-voltage zone | 12 V and guardian |
| **Oil pressure** | | only if a pack has it |
| **Gear** | strip (P R N D 3 2 1) | the D2 auto box via `autobox` |

Skip the speedometer, since ours is fine. The colours must come from our tokens, not the library's hard-coded hex.

**Risks:**
1. **Licence:**
   - GPL-3 SGBD tables (i3, Mini);
   - the non-MIT Roadster CTP files;
   - CanZE and DDT4all lineage, which also blocks those items from the **commercial** dual-licence build;
   - database right, met by keeping the MIT notice and per-signal sources.
2. **Untested decodes:** 1 of 48 modules has tests. Four scaling or mapping bugs were found in a light read. Every import is `candidate` until a fixture exists.
3. **EV-centric data:**
   - 37 of 48 modules are EVs;
   - the metric tree lacks ICE names;
   - DTC reading is rare (about 9 modules touch DTCs);
   - **zero K-line**, so no value for the D2 and none for pre-2008 European cars.
4. **Actuation:** OVMS commands write to cars:
   - the Volt can force its engine on or off;
   - smart EQ sends DDT4all `2E` writes;
   - MG uses `27`/`2F`/`31`;
   - the Twizy reconfigures its SEVCON controller;
   - raw lock and wake frames.
   The importer never copies them. Any action needs its own ADR and a `gated` safety class.
5. **Drift:** 14 modules have had no commits since 2025. Pin the SHA and record it in each evidence entry.
6. **Metric semantics:** a naive OVMS-alias import would label fuel level as SOC. The importer must key on PID meaning.

## Sources

**Repos:**
- [OVMS3 @7c87784](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/tree/7c877840706624e76b8f20f9100a6dba5220342f)
- [OVMS v2 @260a842](https://github.com/openvehicles/Open-Vehicle-Monitoring-System/tree/260a842953d2f031aa64cfef13484893c42daf9e)
- [react-native-vehicle-gauges @8cc8505](https://github.com/openvehicles/react-native-vehicle-gauges/tree/8cc85056e80193bcded6fb55827cd8006e3b1afd)
- OBDb repos (SHAs in §5) and [SAEJ1979 @6711808](https://github.com/OBDb/SAEJ1979)
- [COVESA VSS @9236923](https://github.com/COVESA/vehicle_signal_specification)

**Files read:**
- `vehicle_obdii/src/vehicle_obdii.cpp`
- `vehicle_cadillac_c2_cts/src/*`, `vehicle_cadillac_ct5/src/*`, `vehicle_chevrolet_c6_corvette/src/*` and their `docs/index.rst`
- `vehicle_jaguaripace/src/{vehicle_jaguaripace.cpp,ipace_obd_pids.h,ipace_poll_*.cpp}`
- `vehicle_voltampera/src/vehicle_voltampera.cpp`
- `vehicle_bmwi3/{ecu_definitions,dev}/README`
- `vehicle_teslaroadster/src/vehicle_teslaroadster_ctp.cpp`
- `vehicle_renaultzoe/docs/PIDs_Renault_Zoe.txt`
- `vehicle_smarteq/src/{eq_poller.h,eq_commands.cpp}`
- `vehicle_vwegolf/{docs/vwegolf.dbc,tests/*}`
- `poller/src/vehicle_poller.h`, `vehicle/vehicle_common.h`
- `main/{metrics_standard.h,metrics_standard.cpp,ovms_metrics.h}`
- `retools_pidscan/src/retools_pid.cpp`
- the per-module scan in [ovms_vehicle_inventory.json](ovms_vehicle_inventory.json)
