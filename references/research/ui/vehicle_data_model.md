---
title: "Vehicle data model — canonical signals and capability manifest"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/platform.md]
summary: >
  What OBD-II (J1979), KWP2000/UDS and pre-OBD cars actually expose, how the open models (OBDb, VSS, SignalK, OVMS, opendbc, Android VHAL, Home Assistant) name it and under which licences, and a recommendation: VSS-aligned canonical paths with OVMS and HA aliases, plus a per-pack capability manifest (signals, systems, DTC sources, actions with a safety class, add-ons) that lets one UI auto-build a Home card set for any car. Includes the D2 and generic OBD-II mappings.
---

# Vehicle data model

**Question:** what does one UI need to know to render any vehicle, and which names
should every pack map onto? Today the pack contract (`src/openostler/pack.py`) carries
modules, a per-module signal store (`signals/<module>.json`: `lid`, `offset`, `kind`,
`scale`, `bias`, `unit`, `confidence`, `limits`, `span`, `normal`, `group`), actions with
a `safety` class (`commands.py`) and a hand-written `layout.json`. Nothing says that
`td5.rpm` and OBD PID `0x0C` are *the same thing*. That missing piece is the subject here.

## 1. What standard OBD-II exposes

### Services (SAE J1979 / ISO 15031-5)

| Service | Purpose | Notes |
|---|---|---|
| `01` | Current powertrain data (PIDs) | PID `00`, `20`, `40` … `E0` are **support bitmaps** (4 bytes → next 32 PIDs) |
| `02` | Freeze-frame data | Same PIDs as `01`, plus frame number; PID `02` = DTC that stored the frame |
| `03` | Confirmed (stored) emission DTCs | 2 bytes per DTC |
| `04` | Clear DTCs, freeze frame, monitor results | **Not a read**: resets readiness; an `actuator`-class action at least |
| `05` | O2 sensor monitor results | Not on CAN; replaced by `06` |
| `06` | On-board monitor test results (MIDs/TIDs) | Min/max/value per test |
| `07` | Pending DTCs (current/last drive cycle) | |
| `08` | Control of on-board system (e.g. EVAP leak test) | Rarely supported; treat as `service` |
| `09` | Vehicle info: `02` VIN, `04` CALID, `06` CVN, `08`/`0B` in-use performance, `0A` ECU name | |
| `0A` | Permanent DTCs | Cannot be cleared by `04`; only by the ECU after passing monitors |

Key PIDs for a Home: `01` monitor status (MIL bit, DTC count, readiness bits), `04` load,
`05` coolant (A−40 °C), `0C` RPM ((256A+B)/4), `0D` speed (A km/h), `0F` intake air,
`10` MAF, `11` throttle, `1C` OBD standard, `1F` run time, `21` distance with MIL on,
`2F` fuel level (100A/255 %), `31` distance since clear, `42` control-module voltage
((256A+B)/1000 V), `46` ambient, `5C` oil temp, `5E` fuel rate, `A6` odometer
(late addition, few cars). See <https://en.wikipedia.org/wiki/OBD-II_PIDs> and OBDb (§3).

**DTC format (SAE J2012 / ISO 15031-6).** Two bytes: the top two bits pick the system
letter **P** (powertrain), **C** (chassis), **B** (body), **U** (network); the next two
bits the first digit (0 = SAE generic, 1 = manufacturer, 2/3 mixed); then three hex
digits. Status is per service on classic OBD (pending = `07`, confirmed = `03`,
permanent = `0A`). On UDS the 3-byte DTC carries a **status byte** (testFailed,
pendingDTC, confirmedDTC, warningIndicatorRequested …) plus a failure-type byte.

**Readiness monitors.** PID `01` bytes B–D: per-monitor *supported* and *complete* bits
(misfire, fuel system, components; then catalyst, EVAP, O2, EGR … for spark, or NMHC
catalyst, NOx/SCR, boost, EGT, PM filter for compression ignition). PID `41` gives the
same for the current drive cycle.

**Freeze frame.** One snapshot (frame 0) of `01` PIDs when a DTC matured: a logbook event.

### Physical protocols and ELM327

| Protocol | ELM327 `ATSP` | Bus | Where |
|---|---|---|---|
| SAE J1850 PWM | 1 | 41.6 kbaud | Ford, to ~2003 |
| SAE J1850 VPW | 2 | 10.4 kbaud | GM, to ~2007 |
| ISO 9141-2 | 3 | K-line 10.4 kbaud, 5-baud init | European/Asian, ~1996–2004 |
| ISO 14230-4 KWP (5-baud / fast) | 4 / 5 | K-line 10.4 kbaud | European, ~2000–2008 |
| ISO 15765-4 CAN 11/29-bit, 500/250 k | 6–9 | CAN | **Mandatory US MY2008, EU from ~2008** |
| SAE J1939 | A | CAN 250 k | Heavy duty |

ELM327 behaviour that matters to the model (datasheet:
<https://cdn.sparkfun.com/assets/learn_tutorials/8/3/datasheet.pdf>, AT list:
<https://cdn.sparkfun.com/assets/4/e/5/0/2/ELM327_AT_Commands.pdf>):
`ATSP0` auto-detects by trying protocols in order (slow, and can pick the wrong K-line
ECU set); `ATH1` shows headers, which is the **only way to tell which ECU answered** when
several reply (`7E8`, `7E9` …); `ATCAF0` turns off ISO-TP formatting for raw UDS;
`ATSH` sets the request header (functional `7DF` vs physical `7E0`). Clones commonly
misreport the version, drop long multi-frame replies and mishandle K-line init, so a
driver must treat "NO DATA" as *unknown*, never as *zero*.

### Mandatory vs optional, and real-world counts

- **Required on essentially all OBD-II/EOBD cars:** service `01` PID `00` (support
  bitmap), PID `01` (monitor status), services `03`/`04`, and the emission-relevant PIDs
  the certification needs. Mode `09` VIN is required for CAN cars (MY2005+ US); CALID/CVN
  for later model years. Permanent DTCs (`0A`) are required from roughly MY2010 (US).
  The exact set is in CARB 13 CCR 1968.2 and the paywalled J1979.
- **Everything else is optional**, which is why the support bitmaps exist. Notably
  **fuel level (`2F`), odometer (`A6`) and ambient (`46`) are often missing**; speed,
  RPM and coolant are effectively universal.
- **Typical count (estimate, not a survey):** older K-line cars ~15–25 Mode 01 PIDs,
  2010s CAN cars ~30–50, recent cars more. We found no published survey; collect real
  bitmaps from users (a community upload of `01 00/20/40/…` replies is cheap and safe).
- **OBDonUDS (SAE J1979-2)** replaces services `01`–`0A` with UDS `22`/`19`/`14`/`31`
  over the same PID numbers as 2-byte DIDs (`F4xx`); phased in from 2023 and required for
  US combustion vehicles by MY2027 (CARB guidance: <https://ww2.arb.ca.gov/sae-j1979-2-guidance>;
  overview: <https://automotive.softing.com/standards/protocols/obdonuds-sae-j1979-2.html>).
  A generic OBD pack must therefore speak **both** classic J1979 and J1979-2.

## 2. Manufacturer data beyond OBD

| Layer | Read data | DTCs | Actuate / routines | Security | Addressing |
|---|---|---|---|---|---|
| **KWP2000 (ISO 14230-3)** — the D2 | `21` ReadDataByLocalIdentifier (1-byte **LID**), `22` by CommonIdentifier, `1A` ECU ident | `18` ReadDTCsByStatus, `17`, `14` clear | `30` IO control by LID, `31` StartRoutine, `3B` write | `27` seed/key | K-line target byte (`0x13` Td5, `0x29` SLABS); 5-baud or fast init per ECU |
| **UDS (ISO 14229)** | `22` ReadDataByIdentifier (2-byte **DID**), `2C` dynamic DIDs, `23` by address | `19` (sub-functions 01/02/04/06…), `14` clear | `2F` IO control, `31` RoutineControl, `2E` write DID | `27` / `29` | ISO-TP request/response ID pairs per ECU (e.g. `7E0/7E8`), or 29-bit `18DAxxF1`; DoIP on Ethernet |
| **Passive CAN broadcast** | Periodic frames (DBC `BO_`/`SG_`) | none | none (writing = injection; gated) | — | Arbitration ID |

Implications for the model: a signal's *request* must be explicit (`21 09`, `22 F40C`,
`01 0C`, broadcast `0x3E9`), a module must carry its own transport and address, and a
DTC source must say which service and status semantics it uses. Standard ranges such as
UDS DIDs `F190` (VIN), `F187`/`F18C` (part/serial) give free identity data on UDS cars.

**Pre-OBD / OBD-I.** No common service model, so the pack supplies everything:
- **Blink codes**: count flashes of a lamp (or a jumper on a diagnostic plug); output is a
  DTC list only, read by a human or an opto input. Model as a DTC source `blink`.
- **GM ALDL**: 160 baud (early) or 8192 baud data stream, per-ECU "mask" definitions;
  definitions circulate as community files, often unlicensed (check before importing).
- **Rover 14CUX** (Lucas, ~1990–95 V8): 7812.5 baud serial, the tool reads ECU RAM
  addresses directly; **Rover MEMS** 1.x/2J/3: K-line-like, fixed data frames
  (`0x7D`/`0x80`). The best open references, Colin Bourassa's `libcomm14cux` and
  `librosco`, are **GPL-3.0**: learn the facts, do not copy code into our dual-licensed
  AGPL core.

All three still fit the same manifest: a memory address or frame offset is just another
`request` + `offset`, exactly as a KWP LID is today.

## 3. Existing open models and datasets

| Model | Shape | Naming example (speed / RPM / coolant / 12 V / fuel) | Licence | Use it for |
|---|---|---|---|---|
| **OBDb** (<https://github.com/OBDb>) | One repo per make+model; `signalsets/v3/default.json`: `commands[]` {`hdr`,`rax`,`cmd`,`freq`,`signals[]` {`id`,`path`,`fmt`{`len`,`mul`,`div`,`add`,`unit`},`suggestedMetric`}} | `speed` / *(none on RPM in SAEJ1979)* / `engineCoolantTemperature` / `starterBatteryVoltage` / `fuelTankLevel` | **CC BY-SA 4.0** (same as our data) | Import SAEJ1979 (103 commands, 294 signals today) and per-model signalsets; contribute D2 back |
| **COVESA VSS** (<https://covesa.github.io/vehicle_signal_specification/>) | Tree of branches/sensors/actuators/attributes in `.vspec` YAML; units and enums; overlays for custom signals | `Vehicle.Speed` / `Vehicle.Powertrain.CombustionEngine.Speed` / `…CombustionEngine.EngineCoolant.Temperature` / `Vehicle.LowVoltageBattery.CurrentVoltage` / `Vehicle.Powertrain.FuelSystem.RelativeLevel` | **MPL-2.0** (v6.1 latest) | Canonical path vocabulary; `Vehicle.OBD` was **removed in 6.0** (an overlay remains), so map OBD PIDs to real VSS paths |
| **OVMS metrics** (<https://docs.openvehicles.com/en/latest/userguide/metrics.html>) | Flat dotted names, typed, unit-aware, staleness tracked | `v.p.speed` / `v.m.rpm` / `v.m.temp` / `v.b.12v.voltage` / *(no fuel metric)* | **MIT** (firmware) | MQTT interop names; already planned in [ovms.md](../ovms.md) |
| **SignalK** (<https://github.com/SignalK/specification>) | Marine tree, strict SI | `propulsion.<id>.revolutions` (**Hz**), `…coolantTemperature` (**K**), `…alternatorVoltage` (V) | **CC BY-SA 2.0** (spec) | Lesson only: SI-only storage is unambiguous but every UI must convert; not a namespace for cars |
| **opendbc** (<https://github.com/commaai/opendbc>) | DBC per platform: messages, signals, scaling | per-car names (`WHEEL_SPEEDS`, `ENGINE_RPM` …) | **MIT** | Passive-CAN packs; import DBC signals as `request: broadcast` |
| **Android VHAL** (<https://source.android.com/docs/automotive/vhal/system-properties>) | Integer property IDs + areas; `OBD2_LIVE_FRAME` / `OBD2_FREEZE_FRAME` | `PERF_VEHICLE_SPEED` (**m/s**) / `ENGINE_RPM` / `ENGINE_COOLANT_TEMP` / *(n/a)* / `FUEL_LEVEL` (**ml**) | **Apache-2.0** | Optional export target; confirms the "common five" |
| **Home Assistant** (<https://github.com/home-assistant/core/blob/dev/homeassistant/components/sensor/const.py>) | `device_class` + `unit_of_measurement` + `state_class` | `speed` / *(no class; unit `rpm`)* / `temperature` / `voltage` / `volume_storage` or none for % | **Apache-2.0** | MQTT discovery metadata, generated from our registry |

**Licence rules for us** (AGPL-3.0 code, CC BY-SA 4.0 data, ADR-0012): OBDb data can be
imported with attribution; VSS and OVMS *names* are identifiers, so we reference them,
and if we ever vendor the `.vspec` files they stay MPL-2.0 in their own directory;
SignalK and VHAL are lessons and export targets only. Never import GPL-2.0-only,
non-commercial or unlicensed definition files, and never ship dealer databases
(ODX/PDX from a dealer tool, SMR-D, NanoCom tables) — see [platform.md](../platform.md).

## 4. Recommendation

### 4.1 Canonical namespace: VSS paths, OVMS and HA as generated aliases

1. **The canonical id of a meaning is its VSS path** (`Vehicle.Speed`). VSS is the only
   open, maintained, multi-domain tree; it is OEM-backed; and its 6.0 decision to drop the
   one-to-one OBD branch is the same decision we need (one meaning, many sources).
2. **Our own extensions go in an overlay branch `Vehicle.Ostler.*`**, used only where VSS
   has nothing (MIL lamp, DTC count, readiness, boost pressure, injector balance, ride
   height raw counts). The overlay is a small file in the platform, CC BY-SA 4.0.
3. **Pack-private fields need no canonical path.** `td5.balance_3` stays a module field;
   it shows up in Diagnose → Live but not on Home. Adding a `metric` is optional and
   never blocks a field.
4. **A platform registry (`metrics.json`) carries, per canonical path:** VSS unit,
   display unit choices, OVMS alias, HA `device_class`/`state_class`, OBDb
   `suggestedMetric`, default `span`, and the *Home role* if any. MQTT/HA/OVMS exports
   are generated from it; packs never repeat this metadata.
5. **Units:** store in the VSS unit (`km/h`, `rpm`, `celsius`, `V`, `percent`, `l`,
   `kPa`); the UI converts for display (°F, mph, L/mil). A pack field whose unit differs
   (the Td5 boost is in `bar`, VSS `MAP` is `kPa`) declares its own unit and the core
   converts once at the mapping step.

Recommended registry rows (the "common set"):

| Canonical (VSS) | Unit | OVMS | HA class | OBDb metric | Home role |
|---|---|---|---|---|---|
| `Vehicle.Speed` | km/h | `v.p.speed` | `speed` | `speed` | **speed** |
| `Vehicle.Powertrain.CombustionEngine.Speed` | rpm | `v.m.rpm` | — (unit `rpm`) | — | **rpm** |
| `Vehicle.Powertrain.CombustionEngine.EngineCoolant.Temperature` | celsius | `v.m.temp` | `temperature` | `engineCoolantTemperature` | **coolant** |
| `Vehicle.LowVoltageBattery.CurrentVoltage` | V | `v.b.12v.voltage` | `voltage` | `starterBatteryVoltage` | **battery** |
| `Vehicle.Powertrain.FuelSystem.RelativeLevel` | percent | — | — | `fuelTankLevel` | **fuel** |
| `Vehicle.Powertrain.FuelSystem.Range` | m | `v.b.range.est` | `distance` | — | fuel (fallback) |
| `Vehicle.Powertrain.FuelSystem.InstantConsumption` | l/100km | — | — | — | fuel (fallback) |
| `Vehicle.Exterior.AirTemperature` | celsius | `v.e.temp` | `temperature` | — | — |
| `Vehicle.TraveledDistance` | m | `v.p.odometer` | `distance` | `odometer` | — |
| `Vehicle.Powertrain.CombustionEngine.MAF` | g/s | — | — | `massAirFlow` | — |
| `Vehicle.Powertrain.CombustionEngine.MAP` | kPa | — | `pressure` | — | — |
| `Vehicle.Chassis.Accelerator.PedalPosition` | percent | `v.e.throttle` | — | — | — |
| `Vehicle.Powertrain.Transmission.IsLowRangeEngaged` | bool | — | — | — | — |
| `Vehicle.Ostler.Diagnostics.MilOn` | bool | — | `problem` (binary) | `checkEngineLightOn` | health |
| `Vehicle.Ostler.Diagnostics.DtcCount` | count | — | — | `storedDTCCount` | health |

### 4.2 Capability manifest (one per pack, `GET /pack` grows into it)

The manifest is *data the UI renders*, generated by the platform from the pack's stores
(signal JSON, dtc JSON, actions) plus one short `vehicle.json`. A generic OBD pack builds
the same shape **at runtime** from the support bitmaps and Mode 09.

```jsonc
{
  "vehicle": { "pack": "lr_d2_td5", "name": "Land Rover Discovery 2 Td5",
               "identity": { "vin": "Vehicle.VehicleIdentification.VIN", "source": "bcu|obd09|manual" },
               "fuel": "diesel", "variant": "D2a-auto" },
  "systems": [                                   // = ModuleSpec, plus transport and role
    { "id": "td5", "name": "TD5 (engine)", "role": "engine",
      "transport": { "bus": "kline", "init": "fast", "address": "0x13", "protocol": "kwp2000" },
      "live": true, "security": "seedkey" } ],
  "signals": [
    { "id": "td5.rpm",                            // module.field, stable store key
      "metric": "Vehicle.Powertrain.CombustionEngine.Speed",   // optional
      "request": { "service": "21", "id": "09" }, "offset": 0, "kind": "u16",
      "unit": "rpm", "span": [0, 4800], "normal": [650, 4200], "limits": [0, 4800],
      "confidence": "proven", "source": "RDL 016", "rate": { "parked": 0, "ignition": 1, "driving": 5 } } ],
  "dtc_sources": [
    { "system": "td5", "kind": "kwp_18", "states": ["logged", "current"],
      "codes": "dtc/td5.json", "mapped_to": "SAE-J2012", "clear_action": "td5.clear_faults" },
    { "system": "obd", "kind": "obd_03|obd_07|obd_0a", "states": ["confirmed", "pending", "permanent"] } ],
  "actions": [
    { "id": "slabs.compressor", "system": "slabs", "safety": "actuator",
      "status": "verified", "confirm": "preconditions", "remote": false } ],
  "addons": [
    { "id": "gps",      "provides": ["Vehicle.CurrentLocation.Latitude", "Vehicle.CurrentLocation.Longitude", "Vehicle.Speed"] },
    { "id": "imu",      "provides": ["Vehicle.Acceleration.Longitudinal", "Vehicle.Ostler.Body.Tilt"] },
    { "id": "guardian", "provides": ["Vehicle.LowVoltageBattery.CurrentVoltage", "Vehicle.Ostler.Security.State"] } ]
}
```

Rules:
- **`confidence` stays two-valued** (CONSTITUTION). A J1979 decode is still `candidate`
  for a given car until a car result exists; record the basis in `source` ("SAE J1979
  PID 0C, supported per bitmap"). The UI may show "standard formula" as a badge.
- **`safety` is the existing vocabulary** (`read`, `actuator`, `service`, `gated`), with
  `remote: false` unless `read`. OBD `04` (clear) is `actuator` with `confirm:
  preconditions` (it wipes readiness and freeze frames); OBD `08` is `service`.
- **DTC entries normalise to** `{code (J2012 form if known), native_key, system, state,
  severity, description, confidence}`; the D2 `pcode` field already does this.
- **Add-ons provide metrics too**, at a lower priority than vehicle sources, so a car
  with no speed on the bus still gets a GPS speed.
- **`request`** replaces the implicit KWP `21`, as proposed in platform.md §1.

### 4.3 Auto-generated Home

The UI asks one question per Home role: *which source of this metric is best right now?*

1. Roles in fixed order: **speed, rpm, coolant, battery, fuel**, then health (MIL/DTC
   count, readiness), then up to N pack-declared "extra" tiles (`layout.json` keeps that
   job, e.g. D2 boost).
2. For each role, collect every signal and add-on with a matching `metric`. Rank by:
   vehicle over add-on, `proven` over `candidate`, fresh over stale, then manifest order.
3. A role with no source shows a quiet "not available on this car" (never a fake zero),
   or falls back by registry: fuel → range → instant consumption; speed → ABS wheel
   speed mean → GPS.
4. Gauge `span`/`normal` come from the signal, else from the registry default.
5. `candidate` sources render with the existing candidate styling; a stale value greys
   out (`expire_after` semantics, as for HA).

### 4.4 The D2 mapped onto it

| Home role / metric | D2 source | Confidence | Notes |
|---|---|---|---|
| speed `Vehicle.Speed` | `td5.speed` (LID `0D`) | proven | fallback `slabs.wheel_speed_*` (candidate), GPS |
| rpm `…CombustionEngine.Speed` | `td5.rpm` (LID `09`) | proven | |
| coolant `…EngineCoolant.Temperature` | `td5.coolant_temp` (LID `1A`+0) | proven | |
| battery `Vehicle.LowVoltageBattery.CurrentVoltage` | `td5.battery` (LID `10`) | proven | also `slabs.battery`; guardian when parked |
| fuel (level) | **none known** | — | the tank sender is not on any decoded LID; Home falls back to `economy` (derived, candidate) |
| `Vehicle.Exterior.AirTemperature` | `td5.ext_temp` | candidate | |
| `…CombustionEngine.MAP` | `td5.manifold_press` (bar → kPa ×100) | proven | the D2 "Boost" tile |
| `…CombustionEngine.MAF` | `td5.maf_sensor` (kg/h → g/s ÷3.6) | proven | |
| `Vehicle.Chassis.Accelerator.PedalPosition` | `td5.accel_pedal_pct` | proven | |
| `…Transmission.IsLowRangeEngaged` | `slabs.transfer_low` | proven | |
| `Vehicle.Ostler.Chassis.RideHeight.*` | `slabs.height_left/right` (raw) | proven (raw) | overlay; no unit until calibrated |
| pack-private | `td5.balance_1..5`, `smoke_limit`, `egr_*` … | mixed | Diagnose only |
| DTC sources | `td5` (KWP `18`, `pcode`), `slabs`, `bcu`, `airbag`, `autobox`, `ace` | per row | proprietary keys, J2012 where known |
| actions | `commands.py` rows | as stored | unchanged; gated stay gated |

Only one store change is needed: an optional `metric` key per record, written through
`upsert_field`. `layout.json` shrinks to the extras and the D2 body picture.

### 4.5 A generic OBD-II car mapped onto it

1. Probe: `01 00` (then `20`, `40` … while bit 32 is set) on functional `7DF` with
   headers on, giving the **set of ECUs** (`7E8` engine, `7E9` gearbox …) as `systems`;
   then `09 02` VIN, `09 0A` ECU names, `01 1C` OBD standard, `01 51` fuel type.
2. Build `signals` from the intersection of the bitmap and the OBDb SAEJ1979 definitions
   (`0D` → `Vehicle.Speed`, `0C` → RPM, `05` → coolant, `42` → battery, `2F` → fuel
   level, `46` → air temp, `A6` → odometer, `01` → MIL/DTC count). All `candidate`.
3. If the VIN's WMI and model year match an OBDb make/model repo, add its extended
   signals (UDS `22` DIDs) on top, still `candidate`.
4. `dtc_sources`: `obd_03`, `obd_07`, `obd_0a` per responding ECU; freeze frame via
   `02` attached to the logbook event; readiness from `01 01` as a health card.
5. `actions`: only `obd_04` (clear, `actuator`), plus `read` actions such as "read
   readiness". No routines without a model-specific pack.
6. On a J1979-2 car the same steps run over UDS `22 F4xx` / `19`, producing the same
   manifest.

**Open:** overlay name (`Vehicle.Ostler.*` vs `Vehicle.Private.*`); an opt-in upload of
real support bitmaps to replace the §1 estimate; shipping a VSS subset vs path strings.

## Sources

All URLs are inline above. Primary: OBDb SAEJ1979 <https://github.com/OBDb/SAEJ1979>;
VSS repo and changelog <https://github.com/COVESA/vehicle_signal_specification>; OVMS
`metrics_standard.h` <https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3>;
GPL-3.0 (facts only) <https://github.com/colinbourassa/libcomm14cux>,
<https://github.com/colinbourassa/librosco>.
