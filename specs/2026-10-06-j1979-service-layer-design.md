---
title: "J1979 service layer — modes 01–0A over K-line and CAN — design"
area: specs
status: stable
version: 0.5
updated: 2026-10-06
depends_on: [CONSTITUTION.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0031-generic-obd2-pack-in-platform.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-u0-seams-design.md, specs/2026-10-06-canlink-isotp-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, references/research/muki01/README.md, references/research/muki01/obd2_can_bus_library.md, references/research/muki01/obd2_kline_reader.md, references/research/ui/vehicle_data_model.md, references/research/ui/decode_pipeline.md]
summary: >
  Approved by the owner on 2026-10-06. A stdlib-only, transport-agnostic SAE J1979 layer in src/openostler/obd/, shared by K-line (ISO 9141-2, KWP2000) and CAN (ISO 15765-4). It speaks to an ObdRequestLink that returns replies keyed by ECU address and does its own multi-frame work (ISO-TP on CAN, multi-message sequences on K-line). It covers chained support bitmaps for modes 01, 02, 06 and 09; decoders for modes 01–0A that read PID formulas as data (OBDb SAEJ1979, CC BY-SA, imported into the generic_obd2 pack's store); P/C/B/U DTCs for modes 03, 07 and 0A; freeze frame with its trigger DTC; readiness into Vehicle.Ostler.Diagnostics.*; Mode 06 results; and Mode 09 CALID, CVN and ECU name, with the VIN decoded locally and never logged. Mode 04 is a Tier 1 Maintenance action (Parked or Idling, an automatic snapshot first, one confirmation, an audit entry; ADR-0033); Mode 08 is never sent; a CAN DTC reply whose count disagrees with its length falls back and warns. supported() feeds the connect-time capability manifest, values carry their store record's VSS metric and the platform derives Vehicle.Ostler.Diagnostics.*, and the tests are written first from the muki01 defects. J1979-2 (OBD on UDS) is noted for later. This Python layer is the lab/reference; the production link layer moves to the node in C later, checked by shared test vectors (ADR-0032).
---

# J1979 service layer — design

**Status:** approved by the owner on 2026-10-06; the answers are in
[§12](#12-decisions-2026-10-06). The questions the owner did not take up stay open and
block nothing before a car fixture. Amended on 2026-10-06 (v0.3) for the node/brain
direction: Mode 04 follows the action categories of
[ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md), and this layer is
the lab/reference for a later C port on the node
([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md)); see
[§10.1](#101-lab-reference-and-the-node).

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
  separate distribution at `packs/generic_obd2/` in the platform repo, marked fallback;
  [ADR-0031](../decisions/adr-0031-generic-obd2-pack-in-platform.md)) imports OBDb
  `SAEJ1979` at a pinned SHA into its signal store through `upsert_field`, with
  `x-obd {service, pid, freq}`, its corrections (`24`, `5D`, muki01 fixture 19), the 18 O2
  PIDs OBDb lacks, and a `metric` on the common set and the O2 and fuel-trim families first
  (owner Q11; packs spec §2.3). The import copies data, never code.
- The platform ships no PID table, formulas or units: only the machinery (request engine,
  bitmaps, multi-ECU and multi-frame handling, DTC, freeze-frame, readiness and identity
  decode, Mode 04 gating). `obd/uas.json` is the J1979 Mode 06 unit-and-scaling
  convention, not vehicle data; still-open question 5 asks whether it moves too.
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
  padding) and tagged `warning: count_mismatch` (owner Q7, 2026-10-06: fall back and warn,
  never reject the reply as `malformed`). muki01's `07 43 01 70 01 34 00 00` (F1b)
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

## 5. Mode 04: clear DTCs is a Tier 1 Maintenance action

Mode 04 also erases freeze frames, readiness and Mode 06 results. Clearing codes is made
safe rather than restricted
([ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)): it sits in the
**Maintenance** category at Tier 1, so drivers may clear as well as owners and mechanics.
It reaches the car **only** through `J1979.clear_dtcs(grant)`; a guard test checks no
other path builds `04`.

1. **Server gate (U2):** the pack's `Command(clears=True)` derives Tier 1, category
   Maintenance (UI spec §7). It is refused unless:
   - the driving state is **Parked or Idling** (never Moving);
   - the user's role grants Maintenance (Owner, Driver and Mechanic by default; Viewer and
     the unsigned head-unit kiosk session never do: clearing needs a signed-in user);
   - the request comes over a **local link** (the in-car LAN, the node's Wi-Fi AP or BLE).
     Remote paths (Tailscale, cloud relay) stay read-only unless the install-level
     override `OSTLER_ALLOW_REMOTE_CONTROL` is set in the environment or install config
     (default off, never settable remotely; ADR-0033);
   - the user gives **one confirmation**. It names the ECUs and the cost ("Clear 3 codes?
     Freeze frames and readiness monitors will be reset; permanent codes stay. A snapshot
     is saved to the logbook first.").
   The gate mints a short-lived, single-use `ClearGrant`; on CAN the frame also needs the
   pack's allowlist entry ([CanLink spec §7](2026-10-06-canlink-isotp-design.md)).
2. **Safety-system warning:** when any code to be cleared belongs to a safety system
   (airbag/SRS, ABS, brakes, as tagged by the pack or by the code's system category), the
   confirmation carries an extra warning that the fault may be real and the system may not
   work as intended. It is still one confirmation, not a second dialog. Airbag/SRS ECUs
   that a pack marks read-only by construction (CONSTITUTION) are never cleared at all.
3. **Automatic snapshot first:** before `04` is sent, the layer stores 03, 07, 0A,
   freeze frames and readiness (identity masked) to the logbook as a "before clear" event.
   This is automatic and replaces the former optional "Save a report first". If the
   snapshot cannot be written, the clear is not sent.
4. **Send** one functional `04`; record each ECU's `44` or NRC. **NRC `0x22`
   (conditions not correct)** is shown honestly per ECU: while idling many ECUs refuse,
   and the UI says so ("The engine ECU refused while the engine is running. Switch the
   engine off, ignition on, and try again.") rather than reporting a generic failure or
   pretending the clear worked.
5. **Re-read** 03, 07, 0A and PID 01, and log before and after with the action (UI spec §7).
   Remaining permanent codes are explained, not shown as a failure.
6. **Audit:** every attempt writes an audit entry: who (user and device), when, the driving
   state, which ECUs and codes were cleared, each ECU's `44` or NRC, and a link to the
   snapshot. Refusals at the gate are audited too.

**Mode 08 is never sent** (owner Q6, 2026-10-06; inventory row 22), not even its `08 00`
bitmap: it is listed as `planned` and not runnable. A guard test checks that no path builds
a request whose service byte is `08`, alongside the Mode 04 guard.

## 6. VSS mapping through `metrics.json`

- **PID values** carry their store record's `metric` where it has one, which the pack
  importer resolved (the reverse of the `obdb` alias in `metrics.json`, then a reviewed
  map, then a proposed `Vehicle.Ostler.OBD.*` node; packs spec §2.3). The common set and
  the O2 and fuel-trim families get one first (owner Q11); a record without one decodes
  under its pack name only. Unit conversion (`km` → `m`) is folded into
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
| F16a | Mode 04 snapshot | 03, 07, 0A, freeze frames and readiness stored to the logbook before `04` is sent; a failed snapshot write blocks the clear |
| F16b | Mode 04 driving state | granted when Parked and when Idling; refused when Moving; an idling ECU's NRC `22` shown per ECU, others' `44` kept |
| F16c | Mode 04 safety warning | a code from an airbag, ABS or brake system adds the warning to the single confirmation; no warning otherwise; SRS read-only ECUs never sent `04` |
| F16d | Mode 04 audit | one audit entry per attempt (user, device, state, ECUs, codes, per-ECU result, snapshot link); gate refusals audited; remote request refused unless `OSTLER_ALLOW_REMOTE_CONTROL` is set |
| F17 | Mode 08 guard | no code path builds a service `08` request, `08 00` included |

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

### 10.1 Lab reference and the node

This Python layer is built as approved and stays the **lab/reference** implementation
([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md)). The production link layer
(K-line and CAN I/O, the transmit gate, and the request engine) moves to the node in
portable C once the facts are stable. The two builds are checked by **shared test
vectors** (bytes in, results out, plus the gate and Mode 04 cases), seeded from the §9
fixtures and run in CI against both. On the node, the brain or a paired phone mints the
`ClearGrant` and the node's gate verifies it. Discovery, re-decoding of recordings and
analysis stay in Python.

## 11. Out of scope

- J1979-2 / UDS (§8), J1939, J1850; any Mode 08 request (never sent); decoding Mode 05 and K-line Mode 06
  beyond raw records; DTC description text (ADR-0025).
- The local VIN decoder and WMI table (U4), the capability schema and route (U3), the
  driving state and server gate (U2), and the `generic_obd2` pack and its importer (U4).
- Make or model overlays (UDS `22` DIDs from OBDb make repos) and polling-rate policy (U3).

## 12. Decisions (2026-10-06)

The owner answered on 2026-10-06 (owner question numbers in brackets).

| # | Question | Decision |
|---|---|---|
| 1 | Read Mode 08's bitmap, or never send Mode 08? | (Q6) Never send Mode 08, `08 00` included (§5) |
| 3 | `count_mismatch` fallback, or reject as `malformed`? | (Q7) Fall back and warn (§4.4) |

Related owner answers: `generic_obd2` lives in the platform repo under `packs/` (Q10,
[ADR-0031](../decisions/adr-0031-generic-obd2-pack-in-platform.md)), which is where §3's
PID data goes; DTC text is codes, categories and our own short descriptions for common
codes (Q12, [packs spec §2.6](2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md)).

**Still open** (not raised with the owner; none blocks the fake-only work):

2. Does `DistanceSinceDtcClear` come from the engine ECU only, or the largest value?
   §6 drafts "the engine ECU, otherwise the largest value".
4. Mode 05 and K-line Mode 06 stay raw until a car fixture exists. Is a K-line OBD car
   available for the test plan?
5. `uas.json` (Mode 06 scaling IDs) is a J1979 convention, so it is drafted as platform
   machinery. Should it move to the `generic_obd2` pack's data under the packs-only rule?

## Changelog

- 2026-10-06 — v0.1: first draft.
- 2026-10-06 — v0.2: approved by the owner. Mode 08 never sent (guard test F17); the
  `count_mismatch` fallback confirmed; questions 2, 4 and 5 stay open.
- 2026-10-06 — v0.3: amendment for the node/brain direction (stays approved). Mode 04 is
  a Tier 1 Maintenance action (ADR-0033): Parked or Idling, an automatic logbook snapshot
  replaces "save a report first", one confirmation, an extra safety-system warning, an
  audit entry, NRC `0x22` shown honestly, drivers may clear; remote clearing only with the
  `OSTLER_ALLOW_REMOTE_CONTROL` install override. This layer is the lab/reference for a
  later C link layer on the node (ADR-0032) with shared test vectors (§10.1). Tests
  F16a–F16d added.
- 2026-10-06 — v0.4: first implementation step (fakes only; no D2 behaviour change).
  Built: `obd/` (`link.py`, `decode.py`, `pids.py`, `diagnostics.py`, `vin.py`,
  `j1979.py`, `uas.json`), the K-line adapter `kline/obd_link.py` (ISO 9141-2 and
  KWP2000 functional `C2 33 F1` / physical framing, `78` read-on, Mode 09 read-on to
  `expect_messages`, keep-alive), `openostler.testing.FakeObdLink`, store kinds `s8` and
  `u32`, the layering guard for `obd`, and tests F1a–F17 plus golden `SupportReport`s.
  Shared vectors (bytes in, results out, Mode 04 gate cases) are in `tests/vectors/j1979/`
  with their format in its README. Implementation notes:
  - **`obd/clear.py`** (not in the §1 table) holds the Mode 04 policy: `plan()` (the one
    confirmation, the safety warning by pack tag or by code category, `C` and `B00xx`)
    and `ClearGate` (driving state, role or category, local link or the env override read
    once at start, confirmation) minting a short-lived single-use `ClearGrant`;
    `J1979.clear_dtcs` redeems it with a driving-state re-check. No server route mints a
    grant yet (U2), so nothing in the app can clear.
  - **Read-only ECUs:** when the pack lists any read-only ECU, `04` goes out physically to
    each ECU to clear instead of one functional request, so a functional `04` can never
    reach an SRS ECU.
  - **Mode 06 on CAN** is decoded as 9-byte records that each repeat the MID
    (`MID TID UASID value min max`, ISO 15765-4); `uas.json` holds the UASIDs we could
    state as facts, `candidate`; an unknown UASID decodes raw with `unknown_uasid`.
  - **Identity:** the scrub patterns also cover `49 04` (CALID), per ADR-0036 §1; the
    decoded CALID and CVN stay in the in-memory `SupportReport` as §4.6 says. The "before
    clear" snapshot holds no identity data at all.
  - **PID data:** `PidTable.from_records` (alias `from_signals`) reads store records with
    `x-obd {service, pid, len}`; offsets count from data byte A. Platform tests use
    `tests/fixtures/j1979/pids.json`; PID `31` is read through the table for
    `DistanceSinceDtcClear` (a record still in `km` is converted).
  - `supported()` sends no Mode 05 request (§7 lists none).
  Remaining: the CAN adapter `can/obd.py` and the ISO-TP halves of F1c/F11 on
  `FakeCanBus` (with CanLink); wiring the scrub into `LoggingTransport` and
  `LoggingCanLink` with the ADR-0036 opt-in; the U2 route, `Command(clears=True)` and
  install-config override; the U3 capability builder and `etag`; the `generic_obd2` pack
  and importer (U4) re-running the value fixtures through its store; Mode 05 and K-line
  Mode 06 decoding; the C port running the shared vectors in CI; J1979-2.
- 2026-10-06 — v0.5: the CAN adapter lands with the CanLink spec's first step
  ([CanLink spec](2026-10-06-canlink-isotp-design.md) v0.4). `can/obd.py`
  (`CanObdRequestLink`) implements `ObdRequestLink` over ISO-TP: functional `7DF` and
  `18DB33F1`, physical `7E0`–`7E7` and `18DAxxF1`, replies keyed `"7E8"` or
  `"18DAF110"`, `7F xx 78` waited out under P2\*. The ISO-TP halves of F1c (five codes
  over FF/CF) and F11 (the VIN over FF/CF/FC to `on_vin` only), plus F3–F5 and the golden
  two-ECU `SupportReport`, now also run on `FakeCanBus` (`tests/test_can_obd.py`). Mode 04
  over CAN needs a `TxGrant` for the pack's allowlist entry as well as the `ClearGrant`.
