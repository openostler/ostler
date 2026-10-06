---
title: "Vehicle packs: generic_obd2 (the OBD-II fallback) and bmw_e (BMW E-series I/K-Bus, read-only) — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [CONSTITUTION.md, src/openostler/pack.py, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-j1979-service-layer-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-06-canlink-isotp-design.md, specs/2026-10-06-u0-seams-design.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0015-repo-split-executed.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0024-body-bus-links-passive-by-default.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, references/research/muki01/README.md, references/research/muki01/bmw_ibus_kbus.md, references/research/ui/vehicle_data_model.md, references/research/ovms_reuse.md, vss/ostler.vspec]
summary: >
  Implementation design for the first two packs after the D2. generic_obd2: a separate distribution kept in the platform repo (packs/generic_obd2/) and installed by default, marked fallback so the loader picks it only when no specific pack is installed; it imports OBDb SAEJ1979 (CC BY-SA, attributed) through a pinned importer, adds the 18 O2 PIDs OBDb lacks as candidates, gives every signal a VSS metric (new Vehicle.Ostler.OBD.* nodes proposed for review), builds its capability manifest at connect time from the J1979 support bitmaps, collapses to one system, gates Mode 04 as Tier 1 and never sees the full VIN. bmw_e: its own repo (openostler/ostler-pack-bmw-e), read-only, with the I/K-Bus framer inside the pack over the byte Transport, a module address table and message set reimplemented from facts, VSS mapping plus three or four Vehicle.Ostler.* event leaves, alarm triggers for the guardian, steering-wheel buttons later, no transmit, 117 checksum vectors and a FakeIbus. Covers pyproject, layout.json, CI, REUSE, docs and rollout for both.
---

# Vehicle packs: `generic_obd2` and `bmw_e` — design

**Status:** draft for owner review. Nothing here is built before approval (CONSTITUTION).
It carries out rows 14–25 and 42–53 of the [muki01 synthesis](../references/research/muki01/README.md)
(build-order steps 5 and 7) and the U4 "second pack" row of the
[UI architecture](2026-10-06-ui-architecture-design.md) §10. The J1979 mechanics (request
builder, multi-ECU parser, support bitmaps, J1979-2) are in the
[J1979 service layer spec](2026-10-06-j1979-service-layer-design.md), written in parallel;
this spec only says what the packs ask of it.

## 1. Shared rules

- **Vehicle data lives in packs only** (ADR-0024): PIDs, I/K-Bus messages, addresses.
  Platform code names neither pack (CONSTITUTION, `tests/test_layering.py`).
- **Every field starts `candidate`**; only a car result in the pack's
  `references/test_plan.md` makes it `proven`, never an import or a standard's formula.
- **Read-only first:** `generic_obd2` has one Tier 1 action (Mode 04); `bmw_e` has none.
- **Each is a normal `VehiclePack`** (API 1) with the D2 pack's shape: lazy `PACK`, stores,
  `layout.json`, a contract test, CI that installs the platform first.
- **Naming:** repo or directory, and distribution, `ostler-pack-<x>`; import `ostler_<x>`;
  pack id `<x>`. The D2 pack keeps `d2diag`/`lr_d2`.

## 2. `generic_obd2`

### 2.1 Repo placement

| Option | For | Against |
|---|---|---|
| **A. Inside `src/openostler/`** (a built-in pack) | One install; `NoVehiclePackError` disappears | Breaks the constitution rule "the platform never imports a vehicle pack" and ADR-0015, which removed the built-in fallback; puts OBD data under the platform package; the literal guard would have to allow its ids |
| **B. Its own repo** (`ostler-pack-generic-obd2`) | Clean boundary, like the D2 pack | It moves in lockstep with the platform's J1979 layer, CanLink and capability builder (U3/U4), so every change becomes two PRs and a pinned ref; a car with no pack works only if the installer remembers it |
| **C. A separate distribution kept in the platform repo**, `packs/generic_obd2/` with its own `pyproject.toml`, installed by default | Same contract and import boundary as B (the loader finds it by entry point; `src/openostler/` never imports it); one PR when J1979 changes; platform CI tests it directly; Docker, `deploy.sh` and `mac/install.sh` install it, so every install has a safe default | Two distributions in one repo; a pip-only platform user still has to install it (the error hint says how) |

**Recommendation: C.** It gives the UI spec §8.2 outcome (a car with no pack still works,
the `NoVehiclePackError` dead end is gone on every supported install) without reopening
ADR-0015: the platform still never imports a pack by name. It needs one loader change and
an ADR that amends ADR-0015's loader paragraph:

- `VehiclePack` gains `fallback: bool = False` (defaulted, so `PACK_API_VERSION` stays 1).
- `_resolve()`: `OSTLER_VEHICLE` still wins. Otherwise, if exactly one **non-fallback**
  pack is installed, use it; if none, use the single fallback pack; several non-fallback
  packs still raise and ask for `OSTLER_VEHICLE`. `NoVehiclePackError` remains for an
  install with no pack at all, and its hint names both the D2 pack and `generic_obd2`.
- Detection-based choice (a D2 install meeting a Golf) waits for the garage (U6) and pack
  `detection` (UI spec §4.4); until then the user sets the vehicle in the garage or
  `OSTLER_VEHICLE=generic_obd2`. Should the pack later need its own cadence, `git
  filter-repo` moves it to its own repo with no name change.

### 2.2 Names, pyproject and layout

`pyproject.toml`: distribution `ostler-pack-generic-obd2`, licence `AGPL-3.0-or-later AND
CC-BY-SA-4.0`, `dependencies = ["openostler"]`, `[project.entry-points."openostler.vehicle"]
generic_obd2 = "ostler_generic_obd2:PACK"`, package data for the JSON files and `demo/`.
`pip install "ostler-pack-generic-obd2 @ git+https://github.com/openostler/ostler#subdirectory=packs/generic_obd2"`.

```
packs/generic_obd2/  pyproject.toml README.md CLAUDE.md GOALS.md NOTICE references/test_plan.md
  src/ostler_generic_obd2/
    __init__.py        PACK (lazy, as in d2diag), fallback=True
    signals/obd2.json  one store: OBDb import + O2 overlay, written via upsert_field
    dtc/obd2.json      codes only, no descriptive text (§2.6)
    obdb.lock.json     {repo, sha, file, imported_utc, signal_count}
    sources.py actions.py menus.py faultscan.py sniff_spec.py layout.json vehicle.json demo/
  tools/import_obdb.py dev-only importer (§2.3)
  tests/  fixtures/obdb/ (converted OBDb cases)  fixtures/j1979/ (ours)
```

### 2.3 Data: the OBDb import

- **Source:** `OBDb/SAEJ1979` `signalsets/v3/default.json` at a pinned SHA (103 commands,
  294 signals when surveyed), CC BY-SA 4.0, the primary polled-data source (ADR-0019).
- **`tools/import_obdb.py`** (stdlib, dev-time) reads a checkout at the `obdb.lock.json`
  SHA and writes **only through `upsert_field`**: `name` from the OBDb `id`, `lid` = PID,
  `offset`/`kind`/`scale`/`bias` from `fmt`, `unit` from the metric, `group` from `path`,
  `label` from the OBDb name (attributed), `candidate`, `source:
  "OBDb/SAEJ1979@<sha> <command>"`, `x-obd: {service, pid, freq}` and
  `x-ostler.evidence.source`. `description` is ours or empty.
- **Skipped:** Mode 09 identity (VIN, CALID, CVN, ECU name): read by the platform (§2.7),
  never a signal. **Idempotent:** only records with `x-ostler.origin: obdb` are rewritten;
  a dry run prints the diff.
- **Upstream faults** (muki01 fixture 19: PID `24` divisor 8196, not 8192; `5D` offset
  −38665, not `/128 − 210`) sit in a reviewed `corrections.json`, applied, reported and
  offered upstream.
- **Attribution:** `NOTICE` and the README name OBDb, the SHA and CC BY-SA 4.0; the store
  is an adaptation, CC BY-SA; every record carries its source.

**The 18 O2 PIDs OBDb lacks** (`16 17 1A 1B`, `25–2B`, `35–3B`; muki01 row 15): written
from the J1979 formulas in our own words (voltage and short-term trim; wide-range ratio
with voltage; ratio with current), about 36 fields, `x-ostler.origin: "j1979-overlay"`,
all `candidate`, each with a fixture. They are offered to OBDb as a PR.

**Every signal gets a `metric`.** The importer resolves it in this order:
1. the reverse of the overlay's `obdb` alias (`speed` → `Vehicle.Speed`);
2. a reviewed `metric_map.json` for ids with a standard VSS leaf but no alias, only where
   the unit converts honestly;
3. otherwise a **`Vehicle.Ostler.OBD.<Name>`** node (e.g.
   `Vehicle.Ostler.OBD.O2.Bank1.Sensor2.Voltage`, `Vehicle.Ostler.OBD.FuelTrim.Bank1.ShortTerm`),
   named after the pre-6.0 VSS OBD branch so the tree stays familiar. These nodes are
   **proposed for review** as one PR to `vss/ostler.vspec` (ADR-0016: packs ship no
   overlays), regenerated into `metrics.json`. The importer refuses to write a record
   whose metric is not `is_known`.
4. The common-set Home roles come out right: `0D` speed, `0C` rpm, `05` coolant, `42`
   battery, `2F` fuel, `01` MIL/DTC count/readiness → `Vehicle.Ostler.Diagnostics.*`.

**One table, not two.** The [J1979 spec](2026-10-06-j1979-service-layer-design.md) §3 and
§12 Q1 put the same import (OBDb table, O2 overlay, corrections) in the platform at
`obd/data/saej1979.json`. Only one may exist. This spec recommends **the pack**: the
guardrail is that decoded vehicle data (PIDs) lives in packs (muki01 §c, ADR-0024), and
ADR-0019 names `generic_obd2` as the importer; the platform then ships the `fmt` engine,
bitmaps, DTCs and identity only. If the owner picks the platform instead, this section's
importer, overlay and corrections move there unchanged and the pack store becomes a thin
reviewed layer (metric, label, group, span) over that table.

### 2.4 Capability manifest at connect time

The store holds every known PID; the car supports a subset. `vehicle.json` declares
`{"manifest": "connect_time", "probe": "j1979"}`. On connect the platform's capability
builder (U3) asks the J1979 layer for `supported()` (chained `01 00/20/40…` and `09 00`
bitmaps per ECU; J1979-2 `F4xx` DIDs later, per that spec) and keeps a signal only if some ECU supports
its `x-obd` PID. The manifest has the UI spec §5.1 shape and an `etag` that changes with
the bitmap. Unsupported signals are absent, never zero; a Home role with no source shows
"Not available on this car"; coverage counts go to the identity bar. The builder is generic
and serves any later OBD-based pack; the pack only declares the two keys.

### 2.5 One system

One `ModuleSpec("obd2", "Engine and emissions (OBD-II)", address=0x33, init="none",
live=True, fault_label="OBD-II")`; the link comes from K-line detection (ADR-0022,
[K-line profiles spec](2026-10-06-kline-profiles-detection-design.md)) or passive CAN
detection (ADR-0023), never from the pack. With one live system the UI drops the system
level (UI spec §4.2). Several responders (`7E8`, `7E9`, K-line `48 6B 10`/`48 6B 18`) are a
**source tag** on each value and code, from the J1979 layer's per-ECU collection, never
modules. The id is `obd2`, not `obd`, so it cannot equal a platform string.

### 2.6 Actions, faults and safety

| Action | Service | Tier | Rules |
|---|---|---|---|
| Read codes (stored, pending, permanent) | `03`, `07`, `0A` | 0 | the one `FaultReader`; codes by J2012 letter and digit only |
| Freeze frame | `02` | 0 | Snapshot section of fault detail, with the `02 02` storing DTC |
| Readiness; distance with MIL on and since clear | `01 01`, `01 21`, `01 31` | 0 | health card |
| Monitor results | `05` (K-line only), `06` | 0 | Diagnose › Tests |
| **Clear codes** | **`04`** | **1** | `Command(safety="actuator", clears=True, status="experimental")`; Parked only; one confirm naming the consequence ("Clear 3 codes? Freeze frames and readiness monitors will be reset"); a report offered first; afterwards re-read `03`/`07`/`01` and show the result; refused while Moving, from a remote path or below the ECU-session rung |
| Control of on-board system | `08` | — | listed as `planned`, never runnable, under its own review |

The platform derives the tier from `clears` (UI spec §7, U2); the pack never types one.
**DTC text:** codes plus our own category words ("generic powertrain code"); J2012 wording
and `errorCodes.js` are never copied (ADR-0025); our own descriptions may follow, reviewed.

### 2.7 Identity and VIN

`09 02` is read by the platform (`J1979.read_identity`, J1979 spec §4.7), not the pack,
and decoded **in memory** against the bundled WMI/model-year table; only `{make,
model_year, region}`, the masked form (`WVW…****`) and the garage HMAC leave it. The shared
scrub patterns make `LoggingTransport` and `LoggingCanLink` drop the identity bytes, so
logs, captures, sessions and demo data never hold them. The pack stores nothing about identity; make and year only pick the
banner text and, later, an OBDb make/model overlay (UI spec §8.2).

### 2.8 Other pack members

`sources` → `{"obd2": Obd2Source}` over the J1979 layer (it owns keep-alive and the `82`
release on K-line). `menus` are generated from the store groups. `faultscan` = one reader.
`sniff`: fast and slow init at `0x33`; detectors on `68 6A F1` and `C2 33 F1` headers.
`writable_signal_modules = ()` (standard PIDs are not remapped in the admin mapper).
`demo` from the fakes. `layout.json`: `group_order` from the OBDb paths and a `drive` block
for speed, rpm, coolant, battery and fuel (U4 replaces it with role-built Home).

### 2.9 Tests

- **Importer:** a trimmed SAEJ1979 input → the expected store; idempotence; corrections;
  identity skipped; every record has a known metric, a source and `candidate`. The importer
  also converts SAEJ1979's YAML cases (`response` → `expected_values`) into
  `tests/fixtures/obdb/`, and pytest decodes each through our store.
- **Our J1979 fixtures** (own words): muki01 (f) 1–11 and 19, plus the O2 overlay.
- **Fake ECUs** (shared with the J1979 spec): ISO 9141-2 and KWP fast-init `FakeKLineEcu`,
  `FakeObdLink`, and `FakeCanBus` with `7E8` + `7E9` nodes. The connect-time manifest matches a golden
  per fake; one system; source tags on a double reply.
- **Safety and VIN:** Mode 04 refused while Moving, unconfirmed or remote, re-read after
  clear; a VIN-bearing fake session leaves no VIN in logs, captures, sessions or fixtures
  (ISO 3779 pattern scan); the contract test; the loader-fallback tests.

## 3. `bmw_e`

### 3.1 Repo and names

Repo **`openostler/ostler-pack-bmw-e`**, distribution `ostler-pack-bmw-e`, import
`ostler_bmw_e`, pack id `bmw_e`, entry point `bmw_e = "ostler_bmw_e:PACK"`, display name
"BMW E-series body bus (I/K-Bus)". BMW is used only to say which car it is for, as with
"Ostler pack *for* Land Rover Discovery 2" (ADR-0013); never in our brand. First car: an
**E46** (everything on the K-Bus); E38/E39/E53 (I + K) and E83/E85 are later variants.

```
ostler-pack-bmw-e/  pyproject.toml README.md CLAUDE.md GOALS.md LICENSE LICENSE-DATA REUSE.toml
                    LICENSES/ THIRD_PARTY_LICENSES.md .github/workflows/ci.yml skill/
  src/ostler_bmw_e/  __init__.py (lazy PACK)  addresses.json  signals/{ike,gm,lcm,ews,mfl}.json
    ibus/{frame,framer,listener}.py   sources.py sniff_spec.py menus.py layout.json vehicle.json demo/
  tests/  fakes.py (FakeIbus)  fixtures/ibus_vectors.json
  references/  test_plan.md  message_set.md  hardware_tap.md
```

`pyproject.toml` mirrors the D2 pack: `dependencies = ["openostler", "pyserial>=3.5"]`,
`license = "AGPL-3.0-or-later AND CC-BY-SA-4.0"`, package data for the JSON files and
`demo/`. `listener.py` runs one RX thread, keeping the latest frame per `(src, cmd)`.

### 3.2 The framer

- **Placement:** inside the pack until a second body-bus pack (the L322 Range Rover is the
  candidate) needs it; then it moves to the platform unchanged (ADR-0024 rule of two).
- **Link:** a byte `Transport` opened at **9600 baud, 8E1**. `SerialTransport` hard-codes
  `PARITY_NONE` today; the [K-line profiles spec](2026-10-06-kline-profiles-detection-design.md)
  adds a parity setting, and this pack depends on it. No `CanLink`.
- **Receive FSM:** read `SRC`, `LEN`; `LEN` outside 3–36 → drop one byte, resync; wait for
  `LEN + 2` bytes; the XOR of every byte before `CHK` must equal `CHK`, else drop one byte,
  resync and count it. Emits `IbusFrame{ts, src, len, dst, cmd, data, chk_ok}` and a raw
  hex line to the `LoggingTransport` JSONL. An optional `src` filter doubles as a capture filter.
- **`encode(src, dst, payload)`** computes `LEN` and `CHK`, refuses over 32 bytes, and serves
  only the vectors and the fake: **no pack module calls `Transport.send`**.
- **Bus sleep:** no frame for N s → status `bus asleep` (not `no-cable`); the next frame is
  a **bus wake** event in the snapshot.

### 3.3 Modules and the address table

`addresses.json` is the address → short name table (about 57 I/K-Bus and 25 D-Bus entries),
facts in our own words from node-bmw-client (MIT), re-checked on the car; sniff and capture
use it for naming. Systems (a flat list, UI spec §4.2):

| id | Name | Addr | live | Decodes (first set) |
|---|---|---|---|---|
| `ike` | Instrument cluster | `80` | yes | `11` ignition, `13` sensor status, `17` odometer, `18` speed/RPM, `19` temperatures, `24` OBC values |
| `gm` | General module (body) | `00` | yes | `72` key fob, `7A` doors, windows, sunroof, boot, bonnet, lock state, `76` alarm/crash |
| `lcm` | Light control | `D0` | yes | `5B` lamp-on and lamp-fault bitmaps |
| `ews` | Immobiliser | `44` | yes | `74` key in/out |
| `mfl` | Steering-wheel buttons | `50` | yes | `32`, `3B` button events |
| `infotainment` | Radio, DSP, phone, CD changer | — | no | names only in v1 (`68`, `6A`, `C8`, `18`) |

`ModuleSpec.address` is the bus address, `init="none"`. A silent module shows `No response`
with its age; the user may mark it **Not fitted**.

### 3.4 Message set and the signal store

Records use the existing store shape: `lid` = command byte, `offset` into the data after
it, `kind`/`scale`/`bias`/`bit`/`states`, plus `x-ibus: {src, dst}`. All `candidate`, each
with `source` naming node-bmw-client (file, SHA) or the audit row, until a car reading.
Fields needing store kinds the schema lacks (`s8` temperatures, `u24le` odometer, `ascii`
OBC values from IKE `24`) wait on the same store-kind change as §2.3 (§4).

| Message | VSS metric |
|---|---|
| GM `7A` | `Vehicle.Cabin.Door.Row{1,2}.{DriverSide,PassengerSide}.IsOpen`, `….IsLocked`, `….Window.IsOpen`, `Vehicle.Cabin.Sunroof.Position` (if only open/closed is sent, a pack-private bit), `Vehicle.Body.Trunk.Rear.IsOpen`, `Vehicle.Body.Hood.IsOpen`, `Vehicle.Cabin.Light.IsDomeOn` |
| LCM `5B` | `Vehicle.Body.Lights.{Beam.Low,Beam.High,Fog.Front,Fog.Rear,Parking,Backup,LicensePlate}.IsOn` and `.IsDefect`, `Brake.IsActive`, `Hazard.IsSignaling`, `DirectionIndicator.{Left,Right}.IsSignaling` |
| IKE `17` | `Vehicle.TraveledDistance` (km × 1000 → m at mapping) |
| IKE `18` | `Vehicle.Speed` (× 2 km/h), `Vehicle.Powertrain.CombustionEngine.Speed` (× 100 rpm) |
| IKE `19` | `Vehicle.Exterior.AirTemperature`, `…CombustionEngine.EngineCoolant.Temperature` (signed °C) |
| IKE `24` | `Vehicle.Powertrain.FuelSystem.Range`; consumption → `…FuelSystem.AverageConsumption` (the OBC figure is an average, not the audit's `InstantConsumption`) |
| IKE `11` | `Vehicle.LowVoltageSystemState` (`OFF`, `ACC` for KL-R, `ON` for KL-15) |
| IKE `13` | `Vehicle.Chassis.ParkingBrake.IsEngaged`; the other bits pack-private |

**Proposed `Vehicle.Ostler.*` additions** (one reviewed PR to `vss/ostler.vspec`):
`Vehicle.Ostler.Body.KeyFobEvent` (string: `LOCK`, `UNLOCK`, `TRUNK`), `Vehicle.Ostler.Body.IsKeyPresent`
(boolean, EWS `74`; the key number stays pack-private), `Vehicle.Ostler.Cabin.SteeringWheelButton`
(string event), and, if GM `76` decodes cleanly on the car, `Vehicle.Ostler.Body.AlarmEvent`.
Events are values with a timestamp in the snapshot; the store marks them `x-ostler.event: true`.

### 3.5 Alarm triggers, steering-wheel buttons, transmit

- **Alarm (Phase 2, read-only):** the guardian keys on **metrics, not the pack**: a door,
  boot or bonnet opening, `KeyFobEvent = UNLOCK` without our disarm, `IsKeyPresent`,
  `LowVoltageSystemState` leaving `OFF`, and the bus-wake event. Notify-only (ADR-0024).
- **Steering-wheel buttons (later, U2):** `SteeringWheelButton` events become Drive-mode
  input (next card, mute alerts), mapped in the UI by metric. Read-only.
- **Transmit is out of scope:** no allowlist, actions, `send` call, IKE `16`/`41` request,
  CDC emulation, display text or standing automation until ADR-0024's conditions and the U5
  threat model are met, and then only under its own spec. A test enforces it.

**Other members:** `sources` gives one `IbusSource` per live module, all fed by one
listener; `faultscan = ()` with `faultscan_unimplemented` naming DS2 over the D-Bus (a later
spec; ADR-0022 never auto-probes DS2); `sniff` has no inits and one `authoritative` detector
per source address; `actions = ()`; `writable_signal_modules = ()`; `layout.json` holds
`group_order` (Doors and locks, Lights, Instruments) and a `drive` block for speed, rpm,
coolant and outside temperature; `demo` replays a synthetic `FakeIbus` log.

### 3.6 Licence and provenance

- Code AGPL-3.0-or-later; data (`addresses.json`, `signals/`, vectors) CC BY-SA 4.0.
- **Facts only, our own words.** node-bmw-client (MIT) is the main decode reference: facts,
  or a port with the MIT notice in `THIRD_PARTY_LICENSES.md`. muki01's firmware is GPL-3:
  facts only; its library stays reimplement-only (unclear `IbusSerial` lineage). NavCoder,
  BMW training material and the HackTheIBus lists are **never** used. No comment, label or
  description text is copied from any source.
- **GPL-3, if ever:** taken whole only as a conscious choice into a separate
  `ostler-pack-bmw-e-gpl` distribution (preferred) or `src/ostler_bmw_e/gpl3/` with SPDX
  `GPL-3.0-or-later` headers, a REUSE annotation, a `THIRD_PARTY_LICENSES.md` row and a
  test that no other pack module imports it (ADR-0025).

### 3.7 Hardware

The reference link is a **listen-only tap**: a USB-UART that supports 8E1 plus the RX half
of a PC817 opto stage (or a TH3122/Elmos 10026B with TXD tied recessive), fused, taken at
the E46 boot CD-changer plug. No TX path exists in the hardware. The ESP32 body-bus node in
RX mode follows in ostler-firmware. `references/hardware_tap.md` uses our own photos only.

### 3.8 Tests

- **Checksum vectors:** the ~117 send-table frames re-derived as `(src, dst, cmd, data)`
  facts in `fixtures/ibus_vectors.json`; `encode` must reproduce the audit's checked `LEN`
  and `CHK` for every one, and the framer must decode each back.
- **`FakeIbus`** (a `Transport`): streams frames with noise, a bad checksum (resync),
  `LEN` outside 3–36 (dropped), a frame split across reads, bus sleep and wake; `send`
  raises. Tests: TX over 32 bytes refused by `encode`; decodes per message; metrics resolve;
  snapshot shape; the no-transmit test; the contract test; demo sessions replay.

## 4. Platform changes these packs need

Each goes to its own spec or PR in the platform repo; none names a pack.

| Change | Needed by | Where |
|---|---|---|
| `VehiclePack.fallback` and loader order; ADR amending ADR-0015 | generic_obd2 | `pack.py`, new ADR |
| J1979 layer, `supported()`, identity redaction | generic_obd2 | [J1979 spec](2026-10-06-j1979-service-layer-design.md) |
| K-line profiles and detect; parity on `SerialTransport` | both | [K-line profiles spec](2026-10-06-kline-profiles-detection-design.md) |
| CanLink, passive bitrate, ISO-TP | generic_obd2 (CAN path) | [CanLink spec](2026-10-06-canlink-isotp-design.md) |
| Store kinds `s8`, `u24le`, `u32`, `ascii`, bit fields of any length | both | signal-store schema and decoder |
| `Command.clears` and the Tier 1 gate | generic_obd2 | U2 |
| Connect-time capability builder (`vehicle.json` `manifest`) | generic_obd2 | U3/U4 |
| `Vehicle.Ostler.OBD.*` and the bmw_e event leaves | both | `vss/ostler.vspec` |
| Shipped test fakes (`openostler.testing`: K-line, CAN, J1979) | both | platform, stdlib only |
| Installers add generic_obd2 by default | generic_obd2 | Dockerfile, `deploy.sh`, `mac/install.sh` |

## 5. CI, REUSE and docs

- **generic_obd2:** a platform CI job installs the platform, then
  `pip install -e packs/generic_obd2[dev]`, runs its tests and `import_obdb.py --check`.
  The D2 job runs with both packs installed and must still resolve `lr_d2`. Root
  `REUSE.toml` marks its `signals/`, `dtc/`, fixtures and `obdb.lock.json` CC-BY-SA-4.0.
- **bmw_e:** the D2 pack's `ci.yml` (platform at `PLATFORM_REF`, then the pack, `pytest -q`),
  plus `reuse lint` and the docs job (frontmatter, links, INDEX). `REUSE.toml` marks data
  CC-BY-SA-4.0, code AGPL-3.0-or-later.
- **Docs per pack:** `CLAUDE.md` (links the platform constitution; layout, commands, the
  read-only rule), a short `GOALS.md` (mission, a few goals, not this pack's job), `README.md`
  (install, attribution) and `references/test_plan.md`.

## 6. Rollout

**generic_obd2:** (1) approve this spec and the fallback ADR; (2) J1979 layer and K-line
profiles land with fakes; (3) store kinds, overlay PR for `Vehicle.Ostler.OBD.*`; (4)
`packs/generic_obd2/` skeleton, importer, O2 overlay, contract tests; (5) loader fallback
and installers; (6) KKL path on a first car, results in its test plan; (7) CAN path after the
CanLink spec; (8) U4 UI: `generateViews()`, single-system collapse, unknown-vehicle banner.

**bmw_e:** (1) approve; (2) serial format in the platform; (3) owner creates the repo; (4)
framer, `FakeIbus`, vectors; (5) address table, message set, overlay PR; (6) sources,
layout, demo; (7) bench or car with the RX tap, promoting fields; (8) Phase 2 guardian
triggers; U2 steering-wheel input; (9) the framer moves to the platform with a second
body-bus pack; transmit only under its own spec after ADR-0024 and U5.

## 7. Acceptance

Both packs pass their contract tests against platform `main`; the loader picks `lr_d2` with
D2 and generic_obd2 installed and generic_obd2 alone; every generic_obd2 record has a known
metric, a source and `candidate`; no VIN reaches a log or fixture; bmw_e decodes all
vectors, resyncs, and has no `send` call and no action.

## 8. Open questions

1. Placement C and the ADR amending ADR-0015's loader: agreed?
2. Where the SAEJ1979 table lives: the pack (this spec, §2.3) or the platform (J1979 spec
   §12 Q1)? The two specs must agree before either is built.
3. A metric on **every** OBD signal means roughly 150–200 `Vehicle.Ostler.OBD.*` nodes.
   Acceptable, or only the common set plus the O2 and trim families?
4. Pack naming convention `ostler-pack-<x>`, and "BMW" in a repo name (nominative use).
5. Generic DTC text: ship codes and categories only, or write our own for common codes?
6. `openostler.testing` as shipped fakes, or keep copying fakes into each pack?
7. Which E-series car or bench the owner has; it decides when any bmw_e field can be proven.
8. bmw_e infotainment: one grouped system or per-node systems?

## Changelog

- 2026-10-06 — v0.1: first draft.
