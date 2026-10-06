---
title: "J1979 service layer — modes 01–0A over K-line and CAN — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [CONSTITUTION.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-u0-seams-design.md, specs/2026-10-06-canlink-isotp-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, references/research/muki01/README.md, references/research/muki01/obd2_can_bus_library.md, references/research/muki01/obd2_kline_reader.md, references/research/ui/vehicle_data_model.md, references/research/ui/decode_pipeline.md]
summary: >
  Draft. A stdlib-only, transport-agnostic SAE J1979 layer in src/openostler/obd/, shared by K-line (ISO 9141-2, KWP2000) and CAN (ISO 15765-4). It speaks to an ObdRequestLink that returns replies keyed by ECU address and does its own multi-frame work (ISO-TP on CAN, multi-message sequences on K-line). It covers chained support bitmaps for modes 01, 02, 06 and 09; decoders for modes 01–0A that read PID formulas as data (OBDb SAEJ1979, CC BY-SA, imported into the generic_obd2 pack's store); P/C/B/U DTCs for modes 03, 07 and 0A; freeze frame with its trigger DTC; readiness into Vehicle.Ostler.Diagnostics.*; Mode 06 results; and Mode 09 CALID, CVN and ECU name, with the VIN decoded locally and never logged. Mode 04 is a Tier 1 action. supported() feeds the connect-time capability manifest, values carry their store record's VSS metric and the platform derives Vehicle.Ostler.Diagnostics.*, and the tests are written first from the muki01 defects. J1979-2 (OBD on UDS) is noted for later.
---

# J1979 service layer — design

## Context

The [muki01 synthesis §c](../references/research/muki01/README.md#c-recommended-build-order)
step 4 asks for one J1979 layer, written test-first and shared by the K-line and CAN paths
(inventory rows 13–25). It comes before U4 (`generic_obd2`, UI spec
[§8.2](2026-10-06-ui-architecture-design.md#82-generic_obd2-and-unknown-vehicle--help-decode-it)),
and it can start now with fakes only. It has two users from day one, the K-line path
([K-line profiles spec](2026-10-06-kline-profiles-detection-design.md)) and the CAN path
([CanLink spec](2026-10-06-canlink-isotp-design.md)), so it is platform comms core. The
`generic_obd2` pack ([packs spec §2](2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md))
owns the PID data, the metrics and the action; this layer owns the mechanics.

The muki01 libraries show J1979's scope and its traps: a DTC loop that skips every second
code, a bitmap overflowing a 32-entry array, signed PIDs read unsigned, PID `23` off by 100×,
multi-field PIDs cut to byte A, first reply wins, and the VIN in the debug output
([CAN audit §4](../references/research/muki01/obd2_can_bus_library.md),
[K-line audit §4](../references/research/muki01/obd2_kline_reader.md)). Each becomes a
fixture before any decoder exists.

Rules: stdlib only (ADR-0002); core never imports `web` or a pack; J1979 facts come from
the standard and OBDb, no muki01 code (ADR-0025); no DTC description text is copied; no VIN
is logged, stored or put in a fixture (ADR-0018 Q7); values stay `candidate` until a car
result promotes them (UI spec §5.1).

## 1. Placement and layering

| File | Holds |
|---|---|
| `src/openostler/obd/__init__.py` | the public API: `J1979`, the result types and `ObdRequestLink` |
| `obd/link.py` | the `ObdRequestLink` protocol, `EcuReply` and request pacing (§2) |
| `obd/j1979.py` | the service layer: discovery, the reads, `clear_dtcs` |
| `obd/decode.py` | pure decoders, bytes → typed results, with no I/O (§4) |
| `obd/pids.py` | `PidTable`, built from a pack's signal records (§3) |
| `obd/uas.json` | Mode 06 unit and scaling IDs, written from J1979 as facts (CC BY-SA) |
| `obd/diagnostics.py` | `Vehicle.Ostler.Diagnostics.*` derivation (§6) |
| `obd/vin.py` | in-memory VIN handling and the scrub patterns (§4.7) |
| `kline/obd_link.py`, `can/obd.py` | the K-line and CAN `ObdRequestLink` adapters |

`tests/test_layering.py` adds `obd` to the core set. `obd` imports nothing from `kline`,
`kwp2000` or `can`; the adapters import `obd.link`, never the other way round. Test fakes
ship in `openostler.testing` (packs spec §2.9).

## 2. Request and response model

### 2.1 `ObdRequestLink`

```python
@dataclass(frozen=True)
class EcuReply:
    ecu: str                       # "7E8", "18DAF110", or the K-line source byte "10"
    messages: tuple[bytes, ...]    # whole service messages, headers and checksums removed

class ObdRequestLink(Protocol):
    flavor: str                    # "can11" | "can29" | "iso9141" | "kwp"
    def request(self, payload: bytes, *, target: "str | None" = None,
                expect_messages: "int | None" = None,
                timeout: "float | None" = None) -> "dict[str, EcuReply]": ...
```

- **Replies are keyed by ECU address.** No "first reply wins": every responder is collected
  until P2 (or P2\* after `7F xx 78`) expires. `target=None` is functional addressing (`7DF`,
  `18DB33F1`, `68 6A F1`, `C2 33 F1`); a target is a physical request.
- **The transport does the multi-frame work.** CAN: the `IsoTpMux` reassembles one message
  per ECU. K-line: `Iso9141Session`/`EcuSession` split the burst at verified checksums
  (K-line spec §3) and the adapter groups messages by source byte; `expect_messages` ends a
  Mode 09 sequence early. ELM/STN (later) runs with `ATH1` to key by ECU, else "ELM: limited".
- **Pacing lives in `obd/link.py`** and is shared by every adapter, following ADR-0020:
  one request in flight; at least 50 ms between requests to the same ECU; on NRC `0x21`
  a backoff of 50, 100 and then 200 ms; on `0x78` the adapter waits up to P2\*, at most
  six times (like `KWP2000._resolve_pending`).
- **RX is flushed before every request.** A reply counts only if its service byte is
  `request + 0x40` and it echoes the PID, MID or InfoType asked for; a late frame from the
  previous request is dropped and counted (fixture F5).
- **Errors are typed, never sentinels:** `ok`, `negative` (NRC), `malformed` (reason) or
  `no_reply` per ECU. "NO DATA" is unknown, never zero; an unsupported PID is absent.

### 2.2 Flavour differences the decoders must respect

| Topic | CAN (`can11`, `can29`) | K-line (`iso9141`, `kwp`) |
|---|---|---|
| PIDs per Mode 01/02 request | up to 6 | 1 |
| Mode 03/07/0A reply | `43 N` and then N codes (a count byte) | `43` and then 3 codes per message, zero-padded, over several messages |
| Mode 09 reply | `49 PID NODI data…` | `49 PID seq data…`, with the count from `09 01/03/05/07` |
| Mode 05 (O2 tests) | not used | supported |
| Mode 06 | MID/TID/UASID records | TID-based layout: raw only in v1 |
| Keep-alive | none needed | `01 00` on ISO 9141-2 and `3E` on KWP (ADR-0022), owned by the adapter |

## 3. PID data: read from the pack's store

- **Vehicle data lives only in packs** (owner, 2026-10-06). The `generic_obd2` pack (a
  separate distribution at `packs/generic_obd2/`, marked fallback) imports OBDb `SAEJ1979`
  at a pinned SHA into its signal store
  through `upsert_field`, with `x-obd {service, pid, freq}`, its corrections (`24`, `5D`,
  muki01 fixture 19), the 18 O2 PIDs OBDb lacks and a `metric` on every record (packs spec
  §2.3). The import copies data, never code. The platform ships no PID table, formulas or units: only the machinery (request engine, bitmaps, multi-ECU and multi-frame handling, DTC, freeze-frame, readiness and identity decode, Mode 04 gating). `obd/uas.json` is the J1979 Mode 06 unit-and-scaling convention, not vehicle data; open question 5 asks whether it moves too.
- `PidTable.from_signals(signals)` groups records by `(service, pid)` and gives each PID a
  **response length** (`x-obd.len`, a field this spec adds, else the largest `offset + width`). Values decode with
  `Signal.decode`, so a multi-field PID yields every field, not only byte A, and signed
  kinds stay signed. The store gains a `u32` kind (PID `A6` odometer) and `s8` (§10).
- The length is what lets a multi-PID CAN reply (`41 0C a b 0D c 05 d`) be walked one PID at
  a time. At a PID with no length the walk stops and marks the rest
  `malformed: unknown_pid_length`. It never guesses.
- **Signals bind to `(service, pid, signal name)`, never to an array index** (muki01
  fixture 11: their page showed PID `23` as "distance with MIL on", which is PID `21`).
- Platform tests use a small table written from J1979 (`tests/fixtures/j1979/pids.json`), so
  they need no pack; the pack re-runs the value fixtures through its imported store.

## 4. Decoders, mode by mode

All decoders live in `obd/decode.py` and are pure (`bytes` in, frozen dataclasses out).

### 4.1 Support bitmaps (modes 01, 02, 06, 09)

- Blocks `00`, `20` … `E0` (`02 00 00` for Mode 02); a block's last bit chains the next,
  **per ECU**. The result is `{ecu: {mode: frozenset[int]}}`, so nothing can overflow (F3, a
  160-bit chain); an ECU missing one block ends its chain as `partial`, others unaffected.
- Mode 0A has no bitmap: one `0A` request decides. Mode 05 (`05 00`) is K-line only.

### 4.2 Mode 01 and 02: values

- A `PidValue` holds `ecu`, `mode`, `pid`, `signal`, `value`, `unit`, `raw` and `ts`.
  Signed fields use signed kinds (`32` and `54`, fixture F6). PID `23` is ×10 kPa and `50`
  is ×10 g/s, both straight from the record's scale.
- **Freeze frame (Mode 02):** `read_freeze_frame(ecu, frame=0)` first reads PID `02`. It is
  the **two-byte DTC that stored the frame** (fixture F9), and `00 00` means "no frame
  stored". Then it reads the Mode 02 supported PIDs, so the result is a `FreezeFrame` with
  `trigger` (a `Dtc`), `frame` and `values`. It is attached to the fault and to a logbook
  event, never polled.

### 4.3 PID 01 readiness (and PID 41)

`Readiness` from bytes A–D: `mil` (A7), `dtc_count` (A0–A6), `ignition` (B3: spark or
compression); `{supported, complete}` per continuous monitor (B0–B2 supported, B4–B6
incomplete) and per non-continuous monitor (C supported, D incomplete), named by ignition
type (spark: catalyst, heated catalyst, EVAP, secondary air, A/C, O2 sensor, O2 heater, EGR;
compression: NMHC catalyst, NOx/SCR, boost, exhaust gas sensor, PM filter, EGR/VVT). An
incomplete bit counts only for a supported monitor. PID `41` (this drive cycle) uses the
same decoder without MIL or count. Labels are our own words.

### 4.4 DTCs (modes 03, 07, 0A)

- **J2012 two-byte decode.** The top two bits give `P`, `C`, `B` or `U`. The next two bits
  give the first digit. The remaining three nibbles are hex. `01 70` is therefore `P0170`.
  `Dtc{code, raw, ecu, kind: stored|pending|permanent}`.
- **On CAN** the byte after `43`/`47`/`4A` is the count. If `len == 2 + 2N` the reply is
  decoded counted. Otherwise the uncounted reading is tried (code pairs, dropping `00 00`
  padding) and tagged `warning: count_mismatch`. muki01's `07 43 01 70 01 34 00 00` (F1b)
  then yields `P0170` and `P0134` with the warning, and is never truncated to one code.
- **On K-line** each message holds three codes with zero padding. Every message of every
  ECU is decoded. A header byte is never read as a code, because the adapter has already
  removed headers and checksums (fixture F2).
- `P0000` is padding only on K-line and in the uncounted fallback. On counted CAN replies
  every counted code is returned, and a counted `0000` is tagged `warning: zero_code`.
- No description text ships here. Meanings come from the `dtc/` store, from our own
  wording, or from an openly licensed set (ADR-0025).

### 4.5 Mode 05 and Mode 06

- **Mode 06 on CAN:** `46 MID {TID UASID value min max}…` → `MonitorTest{mid, tid, value,
  min, max, unit, passed = min ≤ value ≤ max}`, scaled through `uas.json`; MIDs from `06 00`.
- **Mode 06 on K-line and Mode 05:** raw `{tid, data}`, `candidate`, until a car fixture.

### 4.6 Mode 09: identity

`09 00` is the bitmap. K-line message counts come from `09 01/03/05/07` (passed down as
`expect_messages`); on CAN, `NODI` counts the items.

| InfoType | Result | Kept |
|---|---|---|
| `02` VIN | handed to `vin.handle()` in memory (§4.7) | never |
| `04` CALID | a list of 16-byte ASCII strings, NUL-trimmed | yes: a non-identifying fingerprint |
| `06` CVN | a list of 4-byte hex strings | yes |
| `0A` ECU name | 20 ASCII bytes, as an acronym and a name | yes: the system's display name |
| `08`/`0B` IPT | raw | later |

### 4.7 The VIN is decoded locally and never logged

- `J1979.read_identity(on_vin)` reassembles the 17 characters, calls `on_vin(vin)`
  synchronously and drops its reference. The callback (U4's local decoder) keeps only
  `{make, model_year, region, vin_masked, fingerprint}`, the fingerprint an HMAC under the
  device secret (ADR-0018 Q7). No result, exception, `repr` or log line carries the VIN.
- **Scrub patterns** in `obd/vin.py` are shared with the transports: K-line `49 02`
  messages; on CAN the ISO-TP message starting `49 02` (stateful across FF and CFs, CanLink
  spec §8); UDS `62 F1 90` and `62 F1 8C`. `LoggingTransport` and `LoggingCanLink` write
  `<redacted n bytes>` in their place (packs spec §2.7).

## 5. Mode 04: clear DTCs is a Tier 1 action

Mode 04 also erases freeze frames, readiness and Mode 06 results. It reaches the car
**only** through `J1979.clear_dtcs(grant)`; a guard test checks no other path builds `04`.

1. **Server gate (U2):** the pack's `Command(clears=True)` derives Tier 1 (UI spec §7):
   refused unless Parked, local (remote paths get Tier 0 only) and confirmed. The confirm
   names the ECUs and the cost ("Clear 3 codes? Freeze frames and readiness monitors will be
   reset; permanent codes stay."). The gate mints a short-lived, single-use `ClearGrant`; on
   CAN the frame also needs the pack's allowlist entry ([CanLink spec §7](2026-10-06-canlink-isotp-design.md)).
2. **A report first:** "Save a report first" stores 03, 07, 0A, freeze frames and
   readiness (identity masked) to Logs.
3. **Send** one functional `04`; record each ECU's `44` or NRC. NRC `0x22` (engine running)
   reads "Switch the engine off, ignition on, and try again".
4. **Re-read** 03, 07, 0A and PID 01, and log before and after with the action (UI spec §7).
   Remaining permanent codes are explained, not shown as a failure.

Mode 08 is listed, `planned`, and never sent (inventory row 22).

## 6. VSS mapping through `metrics.json`

- **PID values** carry their store record's `metric`, which the pack importer resolved
  (the reverse of the `obdb` alias in `metrics.json`, then a reviewed map, then a proposed
  `Vehicle.Ostler.OBD.*` node; packs spec §2.3). Unit conversion (`km` → `m`) is folded into
  the record's scale at import, so the store unit is the metric's VSS unit (ADR-0016).
- **Diagnostics** are derived here, because they combine services and ECUs. Each ECU's
  value keeps its source tag, and the leaf takes the aggregate:

| VSS path | From | Aggregation |
|---|---|---|
| `Vehicle.Ostler.Diagnostics.MilOn` | 01 A7 | any ECU |
| `…DtcCount` | 01 A0–A6 | sum |
| `…PendingDtcCount` | Mode 07 | count of distinct codes |
| `…IsReadinessComplete` | 01 B–D | every monitor that any ECU supports is complete on every ECU that supports it |
| `…ReadinessIncompleteCount` | 01 B–D | distinct monitors still incomplete |
| `…DistanceSinceDtcClear` | 01 `31` (km → m) | the engine ECU, otherwise the largest value |

## 7. Capabilities at connect

`J1979.supported()` runs once per connection. It reads the 01 chain (which also enumerates
the ECUs), 09 00 with CALID, CVN and ECU names, 02 00 00, 06 00, one `0A` probe, PID `1C`
(OBD standard) and PID `51` (fuel type). It returns a `SupportReport`
`{ecus: {addr: {modes: {mode: frozenset}, partial, calid, cvn, name}}, flavor}`, which never
holds the VIN.

The U3 capability builder consumes it (packs spec §2.4): a signal stays only if some ECU
supports its PID; the pack's one system carries the ECUs as **source tags**, not systems;
the DTC source is one reader whose codes are tagged by ECU; `09 0A` names label the tags;
`etag` hashes the bitmaps, the CALIDs and the store version, so a reflash or a re-import
changes it. Unsupported signals are absent, never zero. Support bitmaps without identity
are safe for opt-in community uploads (vehicle data model §1). This spec owns
`SupportReport` and its golden files; U3 owns the schema and the route.

## 8. J1979-2 (OBD on UDS), later

J1979-2 carries the same PIDs as DIDs `F4xx` over `22`, DTCs over `19` (three bytes plus a
status byte) and clears over `14`; US combustion vehicles need it from MY2027. The decoders
are keyed by PID, so a later `obd/j1979_2.py` maps `22 F4 pid` onto the same table and emits
the same `SupportReport`. Detection and the DTC status model wait for a car or fixture.

## 9. Test plan (written before the code)

Fixtures are JSON under `tests/fixtures/j1979/` (CC BY-SA), written from J1979 and ISO
15765-4 / 9141-2 / 14230, never copied from muki01 output. Decoder tests feed bytes; request
tests use a scripted `FakeObdLink`, `FakeCanBus` with ECU nodes (CanLink spec §9) and an
ISO 9141 / J1979 `FakeKLineEcu`.

| # | Fixture (muki01 source) | Asserts |
|---|---|---|
| F1a | CAN `43 02 01 70 01 34` | `P0170`, `P0134` |
| F1b | `07 43 01 70 01 34 00 00` (CAN D1, their skipping loop) | both codes and `count_mismatch`; none skipped |
| F1c | 5 codes over ISO-TP FF/CF | all 5, in order |
| F2 | K-line burst, 2 messages, 4 codes (K-line §4) | 4 codes; no `48 6B` bytes decoded as codes |
| F3 | 160-bit chain on `7E8`, no reply to `40` on `7E9` (D3) | full set on 7E8; 7E9 `partial`; no index drift |
| F4 | `7E8` + `7E9` reply; merged K-line `10` + `18` burst | two ECUs, values keyed correctly |
| F5 | late `7E9` frame after the next request | dropped and counted, not decoded |
| F6 | PIDs `32`, `54` with negative raw values (D6) | negative pascals |
| F6b | PID `23` = `01 F4` (D5); PID `50` (D7) | 5000 kPa; ×10 g/s |
| F7 | STFT −100 %, IAT −40 °C, timing −64°, torque `A−125` = −125 % (D4) | exact negatives; no sentinels |
| F8 | PIDs `14`, `24`, `34` and `4F`, every field (D8) | every signal of the PID |
| F9 | Mode 02 PID `02` = `01 33`; `00 00` (D9) | trigger `P0133`; "no frame stored" |
| F10 | readiness: spark and diesel, mixed supported and incomplete bits; PID 41 | monitor table and diagnostics leaves |
| F11 | VIN over ISO-TP FF/CF/FC; K-line with the `09 01` count of 5; CALID/CVN counts | VIN reaches `on_vin` only; CALID/CVN lists |
| F12 | VIN scrub | the VIN (ASCII and hex) is absent from logs, `repr`, exceptions and the report |
| F13 | PID `21` against `23` binding (index binding) | ids bind to PIDs |
| F14 | multi-PID reply `41 0C … 0D … 05 …` and an unknown PID in the middle | walk stops, rest `malformed` |
| F15 | Mode 06 CAN records across UASIDs | scaling and `passed` |
| F16 | Mode 04 | refused without a grant; one functional `04`; re-read 03/07/0A/01; NRC `22` text |

Fixture VINs are built at test time from parts, so no VIN literal sits in the tree and the
scrub CI (UI spec §8.3) needs no allowlist. Golden `SupportReport`s: a petrol K-line fake and
a two-ECU CAN fake.

## 10. Migration

- Purely additive: the D2 pack's KWP fault paths, `dtc/` meanings and store are untouched.
- `tests/test_layering.py` gains `obd` as a core package; `REUSE.toml` marks
  `obd/uas.json` and `tests/fixtures/j1979/` CC-BY-SA-4.0.
- `signals` gains `u32` and `s8` kinds (readers, widths, schema); records are unchanged.
- `THIRD_PARTY_LICENSES.md` notes that no muki01 code was used (the OBDb pin is the pack's).
- `clears` and `ClearGrant` arrive with the U2 gate; until then no route mints a grant, so
  `clear_dtcs` cannot run.

## 11. Out of scope

- J1979-2 / UDS (§8), J1939, J1850; Mode 08 control; decoding Mode 05 and K-line Mode 06
  beyond raw records; DTC description text (ADR-0025).
- The local VIN decoder and WMI table (U4), the capability schema and route (U3), the
  driving state and server gate (U2), and the `generic_obd2` pack and its importer (U4).
- Make or model overlays (UDS `22` DIDs from OBDb make repos) and polling-rate policy (U3).

## 12. Open questions

1. Read Mode 08's bitmap (`08 00`) for coverage, or never send Mode 08? Recommendation: never.
2. Does `DistanceSinceDtcClear` come from the engine ECU only, or the largest value?
3. Is the `count_mismatch` fallback (§4.4) right, or should a CAN reply whose count byte
   disagrees with its length be rejected as `malformed`? Recommendation: fall back and warn,
   because a dropped code is worse than a flagged one.
4. Mode 05 and K-line Mode 06 stay raw until a car fixture exists. Is a K-line OBD car
   available for the test plan?
5. `uas.json` (Mode 06 scaling IDs) is a J1979 convention, so it is drafted as platform
   machinery. Should it move to the `generic_obd2` pack's data under the packs-only rule?

## Changelog

- 2026-10-06 — v0.1: first draft.
