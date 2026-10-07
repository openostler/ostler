---
title: "Source adapters — off-the-shelf scanners (ELM327, STN/OBDLink, KKL, SocketCAN dongles, WiCAN, J2534) as Ostler data sources — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/third_party_adapters.md, references/research/canbus_headunit.md, references/research/hardware.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0031-generic-obd2-pack-in-platform.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-06-canlink-isotp-design.md, specs/2026-10-06-j1979-service-layer-design.md, specs/2026-10-06-kline-profiles-detection-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, CONSTITUTION.md]
summary: >
  Draft for the owner's approval (DMD round, 2026-10-07). Lets an off-the-shelf adapter (ELM327 and clones, STN/OBDLink, vLinker, Veepeak, KKL/FTDI cables, CANable/candleLight, slcan, PCAN, Kvaser, WiCAN, Macchina, later J2534) feed the same snapshot, VSS stream, recorder and module bus as NodeSource. A SourceAdapter wraps one transport and offers the links the platform already has (ObdRequestLink, CanLink, the K-line Transport) plus a capabilities manifest, detect and clone checks, sniff, rate limits and health; an AdapterSource (source_kind adapter) decodes through the pack and J1979 decoders. Hosts: laptop and phone always; the Brain only for a vehicle with no node, which needs a Constitution and ADR-0032 amendment (a new ADR). With no hardware gate the host runs the reference TxGate in software (the soft gate, same shared vectors) and the rules are stricter than the node's: read-only by default (standard OBD and UDS reads, pack-declared read recipes); clear codes under ADR-0033 §5 only when Parked or Idling is evidenced from the bus; actuator tests, procedures and allowlisted frames only after a per-vehicle, per-adapter owner opt-in with warnings, Parked, local, never on a clone; Tier 4 never; never while Moving or with unknown speed; no remote trigger; one tester per bus, so an adapter is passive beside a node. Detection with a version-gated clone battery and a known-good list as data. Packaging in core (stdlib plus pyserial; BLE behind an optional extra), phone transports in the app binary, J2534 later as a separate add-on. Phases A0–A6, recorded-fixture tests (ADR-0011), and decisions.
---

# Source adapters — design

**Status:** draft v0.1 for the owner's approval (DMD round, 2026-10-07). Nothing here is built.
Evidence: [third-party adapters research](../references/research/third_party_adapters.md). It
needs a new ADR (number assigned on approval) because it amends a Constitution line (§3).

## 1. Context

- The owner asked for support of off-the-shelf scanners: ELM327 (Bluetooth Classic, BLE, Wi-Fi,
  USB), OBDLink/STN, USB K-line cables, SocketCAN dongles, and J2534 later, with honest limits
  against the Ostler node and safety rules where there is no hardware gate.
- Ostler is node-first: the Ostler Diagnostics node owns the car, its transmit gate is the only
  path to the car, and the Brain never touches the car (ADR-0032, ADR-0039, Constitution). The KKL
  cable path is the dev path.
- Most of the plumbing exists ([research §1](../references/research/third_party_adapters.md#1-what-the-platform-already-has)):
  SocketCAN, slcan (serial and WiCAN TCP), GVRET and python-can `CanLink`s; the KKL
  `SerialTransport`; the `ObdRequestLink` protocol with pacing; the Python `TxGate`; `DataSource`
  with `source_kind` and `touches_car`. Missing: an ELM/STN `ObdRequestLink`, BLE and RFCOMM
  transports, detection and clone checks, a source that decodes adapter data into the VSS stream,
  phone transports, and the safety rules for running all this without a node.
- Users already own these adapters (Torque, Car Scanner, FORScan; [ui/obd_apps.md](../references/research/ui/obd_apps.md)).
  Supporting them lets someone try Ostler, read a second car, or work in a garage with no node.

## 2. Goals and non-goals

**Goals.**
1. One `SourceAdapter` interface over every adapter class, with a capabilities manifest the UI
   follows, as it follows the node's manifest (ADR-0032 §6).
2. Adapter data in the same snapshot, VSS stream, recorder and (optionally) module bus as
   NodeSource, tagged with its source and honest about timing and confidence.
3. Detection and clone checks that downgrade capabilities, and a known-good list as data.
4. Safety without a hardware gate: read-only by default, stricter than the node, never weaker.
5. Clear hosts: what runs on a laptop, a phone and (with a decision) a Brain.

**Non-goals.** Replacing the node or its raw tap; Tier 4 (coding, flashing, SecurityAccess beyond
pack read recipes); relaying raw K-line bytes over Bluetooth or a network (ADR-0039 rejected raw
serial over the network); MQTT to vehicle CAN (ADR-0020); a demo or simulated adapter in the
product (ADR-0011); importing closed apps' code or data.

## 3. Where adapters sit with the node-first rules

| Host | Allowed? | Why |
|---|---|---|
| **Laptop** (Linux, macOS, Windows) | yes | Already the dev path (KKL, slcan, SocketCAN). Becomes a supported path, not only dev. |
| **Phone app** (Android, iOS; ADR-0032 §11 wrapper) | yes, phase A5 | Native transports are fixed in the app binary (ADR-0042); decode and gate run in the app (§6.3). |
| **Brain** | **only for a vehicle with no node** (recommended, decision 1) | "The Brain never touches the car" exists so the node's gate is the only path. With no node there is no gate to bypass; without this exception a Brain owner with an ELM adapter gets nothing. |
| **Browser only** (no app) | read-only, later (decision 6) | Chromium only: Web Bluetooth (BLE), Web Serial (USB and RFCOMM); nothing on iOS or Firefox. |

The **new ADR** (number assigned on approval) would: amend the Constitution's "The brain never
touches the car" and "The node transmit gate is the only path to the car" to add "**…or, for a
vehicle with no node, a third-party adapter driven through the soft gate under the adapter rules
(this spec §7)**"; amend ADR-0032 §2/§3 to the same effect; keep ADR-0039's rejection of raw serial
over the network; and keep the KKL path's dev status for the D2 node work while adding adapters as
a supported product path for reads.

**How it sits with the product.** Adapters are the "no hardware yet" path: they read and clear,
nothing always-on. The node stays the product for alarm, geofence, Brain wake and 12 V watch
(ADR-0040), gated actions with signed grants, the raw tap with MCU timestamps (ADR-0039 §3), and
K-line on cars no adapter can reach (the D2's Td5 and SLABS, research §6). The UI says so plainly
in one place (§9), without nagging.

## 4. The `SourceAdapter` interface

### 4.1 Layers

```
SourceAdapter (core, comms layer; one per physical adapter)
  ├─ transport: serial | rfcomm | ble | tcp | socketcan | pycan | j2534
  ├─ links():  ObdRequestLink (ELM/STN, J2534) · CanLink (SocketCAN, slcan, GVRET, python-can, can327)
  │            · Transport (KKL, for pack K-line profiles)
  ├─ detect() → AdapterIdentity · capabilities() → AdapterCaps · health() → AdapterHealth
  └─ sniff(filters) → iterator of RawRecord      (where the class can)
AdapterSource(DataSource)  (web layer boundary, like NodeSource)
  ├─ source_kind = "adapter", touches_car = True
  ├─ decodes via J1979 decoders + metrics.json, or the active pack's sources over the K-line link
  └─ every transmit through SoftGate (the Python TxGate, §7)
```

`SourceAdapter` lives in core (`openostler/adapters/`, a new package beside `can/`, `kline/`,
`obd/`) and imports nothing from `web` (`tests/test_layering.py`). Existing links are reused, not
re-implemented: an ELM/STN adapter is a new `ElmObdLink(ObdRequestLink)`; a CANable is the existing
`SocketCanLink`; a KKL cable is the existing `SerialTransport` under the pack's K-line profiles.

### 4.2 Methods

```python
class SourceAdapter(Protocol):
    kind: str                         # elm327 | stn | kkl | socketcan | slcan | gvret | pycan | can327 | j2534
    def detect(self) -> AdapterIdentity: ...            # no bus traffic; §5 steps 1-2
    def probe(self, state: DrivingState) -> AdapterIdentity: ...  # Parked only; §5 steps 3-6
    def capabilities(self) -> AdapterCaps: ...
    def open(self, profile: VehicleLinkProfile) -> None: ...      # protocol from the vehicle profile
    def obd(self) -> "ObdRequestLink | None": ...
    def can(self) -> "CanLink | None": ...
    def kline(self) -> "Transport | None": ...
    def sniff(self, filters) -> "Iterator[RawRecord]": ...        # raises NotCapable
    def health(self) -> AdapterHealth: ...
    def release(self) -> None: ...                               # ends sessions, closes protocol
```

- `open()` takes the vehicle's stored link profile (protocol, bitrate, addresses), never an
  automatic search while not Parked (§7 R6). `release()` sends what the protocol needs to leave the
  bus quiet (KWP `82` per the Constitution; `ATPC` on ELM/STN so the chip's own keep-alives stop).
- `sniff()` yields the same `RawRecord` the recorder's tap codec takes, with `clock: "host"` or
  `"device"` and a timestamp quality (§8).

### 4.3 Capabilities manifest

`AdapterCaps` is JSON (schema `schemas/adapter-caps.schema.json`, new) and shaped like the node's
capability manifest so one UI renders both:

```json
{"kind": "elm327", "verdict": "clone", "identity": {"claimed": "ELM327 v1.5", "chip": null, "fw": null},
 "transport": "rfcomm", "protocols": ["can11_500", "can29_500", "kwp_fast", "iso9141"],
 "obd": {"multi_pid": false, "headers": true, "max_request_bytes": 2},
 "sniff": {"can": "limited", "listen_only": "unsupported", "rated_fps": 120},
 "kline": {"raw": false, "one_byte_header": false, "custom_fast_init": false, "slow_init": true},
 "uds": {"isotp": "in_chip", "max_reply_bytes": 4095},
 "tx": {"gate": "soft", "allowed_tiers": [0], "reason": "clone"},
 "power": {"sleep_cmd": false, "voltage": true}, "buses": 1,
 "timestamps": {"source": "host", "quality_ms": 40}}
```

A capability we cannot verify is `"requested"`, `"unknown"` or absent, never assumed (CanLink spec
§2). The verdict only removes capabilities.

### 4.4 Rate limits and health

- **Pacing** is the shared `obd/link.py` pacer (one request in flight, ≥ 50 ms per ECU, `0x21`
  back-off; ADR-0020), plus a **per-adapter ceiling**: clone or unknown 10 requests/s, genuine ELM
  and BLE 20/s, STN and wired CAN 50/s (bench-tune in A1). The ceiling protects the adapter and a
  shared Bluetooth link, not the car.
- **Health** reports `BUFFER FULL` and overrun counts, `NO DATA`, `?` and `STOPPED` counts, p50/p95
  round-trip latency, reconnects, battery voltage (`ATRV`/`STVR`) and link RSSI where the transport
  gives it. The snapshot carries it as `adapter.health`; the connection chip turns amber on
  overruns, as the node's tap reports losses.

## 5. Detection and clone checks

Run on connect; steps 1–2 send nothing to the car; steps 3–6 only when Parked, once per adapter
and vehicle, cached with the adapter's identity (serial number from `STSN`, else the BT address or
USB serial).

1. **Identify:** `ATZ`/`ATWS`, `ATE0`, `ATI`, `AT@1`; `STI`, `STDI`, `STMFR` (STN); vendor strings
   for vLinker. "v1.5" or "v1.4a" → clone (never made).
2. **Version battery:** one command per claimed version (`CSM1` v1.4b, `AMC` v2.0, `CTM1` v2.1,
   `IB12` v2.2); any `?` at or below the claimed version → clone. STN: `STPX` and `STCMM` must
   answer. The table is data (`adapters.json`), not code.
3. **Request length:** multi-PID `01 00 20 40` on a CAN car must return all three bitmaps.
4. **K-line presence** (vehicle profile says K-line): `BUS INIT: ...OK` on the profile's protocol.
5. **Latency:** 20 × `0100`, record p50/p95.
6. **Sniff rating** (CAN, optional, 10 s): frames before `BUFFER FULL`, frames per second.

Verdicts: **genuine** (identity and battery agree; STN, or ELM v2.x), **compatible** (an
ST-compatible or ELM-compatible chip that passes the battery), **limited** (passes but slow or
partial), **clone** (fails 1–3), **unknown**. Raw links (KKL, SocketCAN, slcan, GVRET, python-can)
skip 1–3 and report what the driver states (`ip -details link`, `LinkCaps`).

**Known-good list.** `src/openostler/adapters/adapters.json` (CC BY-SA data, ADR-0012):
`{name, vendor, chip, firmware_tested, transports, ble_service_uuids, verdict, features, tested_on,
tested_by, evidence}`; seeded from [research §9](../references/research/third_party_adapters.md#9-known-good-list-what-is-verifiable-today)
with only documented facts, then owner bench runs and community reports with logs. An entry is
"tested" only with a bench log; otherwise "documented" or "reported".

## 6. Hosts and transports

### 6.1 Python hosts (laptop; Brain per §3)

| Transport | Implementation | Dependency |
|---|---|---|
| USB serial (ELM, STN, KKL, slcan, GVRET) | existing pyserial streams | none new |
| Bluetooth Classic SPP | Linux: stdlib `socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM)` after BlueZ pairing; macOS and Windows: the OS's virtual serial port via pyserial | none new |
| Wi-Fi TCP (ELM Wi-Fi, WiCAN) | stdlib `socket` (existing `TcpStream`) | none new |
| BLE GATT (OBDLink CX, vLinker MC+, Veepeak BLE) | `bleak` (MIT) behind an optional `[ble]` extra, lazily imported like python-can; MTU chunking | optional extra |
| SocketCAN, python-can | existing `SocketCanLink`, `PythonCanLink` | none new / `[can]` |
| J2534 | `ctypes` over the vendor DLL, Windows only | none (phase A6) |

Port discovery extends `ports.py` (it already prefers KKL chips and skips u-blox GPS) with the
known-good list's USB IDs and Bluetooth names.

### 6.2 Phone (phase A5)

- **Android:** BLE, Classic SPP, Wi-Fi TCP and USB OTG serial through native plugins in the
  Capacitor build (plugin choice and licences to verify at A5).
- **iOS:** BLE and Wi-Fi only; Classic adapters are impossible except MFi accessories through the
  External Accessory framework, which needs the accessory maker's approval of our app (decision 7).
- The phone runs **no Python**. It runs the portable C decoder and the C gate compiled to
  WebAssembly (ADR-0032 §8: one decoder in portable C; the shared vectors run against this build
  too), with ELM/STN framing in TypeScript tested against the same recorded transcripts as the
  Python `ElmObdLink`.
- **Browser without the app:** later and read-only (decision 6).

### 6.3 What runs where

| | Laptop | Brain (no node) | Phone app | Browser |
|---|---|---|---|---|
| ELM/STN OBD reads | A1 | A1 | A5 | later |
| KKL K-line (pack profiles) | A1 (exists) | A1 | never (timing) | never |
| CAN sniff (gs_usb, slcan, PCAN, Kvaser, WiCAN) | A2 | A2 | WiCAN over Wi-Fi only, A5 | never |
| STN monitor sniff | A3 | A3 | A5 | never |
| BLE adapters | A3 | A3 | A5 | later |
| J2534 | A6 (Windows) | never | never | never |

## 7. Safety with no hardware gate

The **soft gate** is the existing Python `TxGate` (and on the phone its C build in WebAssembly),
run in the process that owns the adapter. It is the same code the shared gate vectors check
(`tests/vectors/can/`), extended to ELM/STN requests and K-line requests. It is honest about what
it is: software on a general-purpose host, with no driving-state sensor of its own. So the adapter
rules are **stricter** than the node's:

- **R1 Default read-only.** Allowed by default: Tier 0 reads only. On CAN and ISO-TP: OBD services
  `01 02 03 06 07 09 0A` and UDS `22 19` and a physical `3E` (the gate's existing Tier 0 list and
  sweep guard); on K-line: OBD over ISO 9141/KWP and **pack-declared read recipes** (the pack's
  init, session and key exchange that precede its `21`/`18`/`1A` reads, exactly as the KKL dev path
  runs them today). Mode 08 never.
- **R2 Clear codes** (ADR-0033 §5, Maintenance, Tier 1) is allowed without opt-in, with all of §5
  (automatic snapshot, one confirmation, extra warning for safety systems, audit, honest NRC
  `0x22`), **only when Parked or Idling is evidenced from the bus** (§7.1). Airbag/SRS: never.
- **R3 Opt-in for more.** Actuator tests (Tier 2), procedures (Tier 3) and pack-allowlisted raw
  frames (any category) run only when the **owner** has switched on "Adapter actions" for **this
  vehicle and this adapter identity**, after a warning that names what a node would add (an
  independent gate and Stop that survives a host crash). The switch is local-only, audited, shown
  as a persistent badge while on, and off by default. Each run still needs every ADR-0033 rule:
  role, category, tier friction, Parked re-check before every frame, Stop. Refused on a clone or
  unknown verdict, and over Wi-Fi adapters (no link supervision).
- **R4 Tier 4 never** (coding, flashing, writes, UDS `27 2E 2F 31 3B 11 14 28 85` outside pack
  read recipes), as everywhere (ADR-0018, ADR-0033).
- **R5 Never while Moving or unknown.** Every action above Tier 0 is refused when speed is above
  zero or unknown; the soft gate re-reads speed from the bus before every frame of an action and
  stops the action on a stale reading (older than 1 s).
- **R6 No transmit to find the bus while not Parked.** No `ATSP0` automatic search, no probe and no
  wrong-rate frame while not Parked (ADR-0022, ADR-0023). Use the vehicle's stored profile; first
  connection detection runs Parked, ignition on, engine off.
- **R7 Rate limits** (§4.4) plus ADR-0020's per-ECU pacing; one request in flight per adapter.
- **R8 Local only.** Adapter actions come only from the host's own UI on a local link. No remote
  path, share, token, MCP client, Home Assistant or MQTT can start one, and the
  `OSTLER_ALLOW_REMOTE_CONTROL` override does not extend to adapters. An AI client's accept never
  counts (ADR-0033 §6).
- **R9 Listen-only is shown as verified or not.** Sniffing reports `listen_only: true` only when
  the device confirms it (`ip link` on SocketCAN, `STCMM 0` acknowledged on STN); ELM `CSM1`
  without readback is `"requested"`; clones are `"unsupported"` (they ACK). WiCAN is set to `silent`
  with MQTT TX off before use (ADR-0020).
- **R10 Identity data.** VIN and identity replies are scrubbed on the host at write time (ADR-0036;
  the existing `_RawLogPaused` and `LoggingCanLink` rules apply to adapter links).

### 7.1 Driving state without a node

The UI spec §3.5 states (Parked, Idling, Moving, unknown) are computed from the adapter's own
Tier 0 reads: OBD `0D` speed and `0C` rpm (or the pack's equivalents), polled at ≥ 1 Hz while any
action is offered, plus the phone's GPS speed as a cross-check (both must agree for Parked).
Idling needs rpm above zero and speed zero for ≥ 3 s; Parked needs speed zero and, for R3, engine
off where the action declares it. A missing, stale or disagreeing reading is unknown, which locks
everything but Tier 0.

### 7.2 One tester per bus

- **K-line is a shared bus** (Constitution): one adapter per vehicle K-line, serialized on one
  thread; establish → read → release; the pack's quiet periods respected (SLABS needs tens of
  seconds of silence before init). Before the first init the adapter listens for 3 s and refuses if
  it sees foreign traffic (another tool on a splitter).
- **Beside a node:** if the vehicle has a node (its manifest or a gate claim on `kline*` or a CAN
  bus seen through NodeSource, or a node registered in the garage), the adapter is **passive only**:
  verified listen-only CAN sniffing; no K-line access at all; no OBD requests (two testers using
  `F1`/`7E0` collide in ISO-TP flow control). This extends the existing serial-source refusal
  (NodeSource spec §15 Q7) to every adapter.
- **Module-bus claims:** an adapter that holds a K-line or CAN session on a Brain or laptop that is
  on the car LAN publishes a gate claim with `"reason": "adapter"` and `"gate": "soft"` (module-bus
  spec §7.2) so a node arriving later sees it and reports `gate_conflict`, and the Network page
  shows "Adapter on this bus" (decision 9).

## 8. Data into the stream

- **Snapshot:** `source_kind: "adapter"` (new value beside `node`, `serial`, `kline`), `adapter:
  {kind, verdict, transport, identity, health, caps}`; signals keep `c` from the decoder (confidence
  is never raised by an adapter, and a `candidate` decode stays `candidate`).
- **VSS:** decoded through the J1979 decoders and `metrics.json` (generic OBD) or the active pack's
  sources (K-line). Source tags as ADR-0032 §13: `src: "adapter:<kind>:<id>"`.
- **Module bus (optional):** a laptop or phone adapter may publish its VSS values to the Brain's
  broker as a device of `kind: "module"`, `variant: "adapter"`, read-only, with its manifest, so the
  Brain and cloud merge it like a node's values (ADR-0032 §13 selection rules: a node's value wins
  over an adapter's for the same signal).
- **Recording:** sessions and decoded columns as today; raw records in the existing tap record
  format with `clock: "host"` (or `"device"` for slcan `Z1` and GVRET µs) and a
  `ts_quality_ms` (host Bluetooth ≈ tens of ms; FTDI with the latency timer at 1 ms ≈ 1–2 ms).
  pcapng and candump export as today. The FTDI latency timer is set to 1 ms on open where the OS
  allows, and the health block says when it could not be.
- **Honesty:** "NO DATA" is unknown, never zero (J1979 spec §2.1); a `BUFFER FULL` gap is a
  recorded loss, as the node's tap reports overflow.

## 9. UI (summary; detail in U-phase specs)

- **Connection sheet → "Use an adapter"**: pick transport, pair or select, run detection, show the
  verdict and the capability chips: "ELM: limited", "Clone: read-only", "Listen-only: requested",
  "Soft gate". One line on what a node adds, with a link to the hardware page.
- **Adapter actions** switch on the vehicle's settings page (owner only), with the R3 warning.
- The link chip shows the adapter kind and verdict; the Network page lists the adapter as a device
  when it publishes (§8).

## 10. Packaging

- **Core** (`openostler`, AGPL): `adapters/` (interface, ELM/STN link, detection, RFCOMM via
  stdlib), `adapters.json`, the soft gate (existing `can/gate.py` widened). Stdlib plus pyserial
  (ADR-0002, ADR-0035); BLE behind an optional `[ble]` extra (`bleak`, MIT), like `[can]`.
- **Why not an `ostler-adapters` add-on:** these are links in the comms core, beside slcan and
  GVRET which are already core; the gate and safety rules must be the core's; ADR-0034 splits a
  repo only when toolchain, licence, cadence or contributors differ, and none do (decision 3).
- **Phone:** native transports are part of the app binary (ADR-0042: native features fixed in the
  binary; no fetched code).
- **J2534:** a separate Windows-only add-on later (`ostler-adapter-j2534`), because its toolchain
  and testing differ and vendor DLLs are closed (decision 8).

## 11. Phases

| Phase | Ships | Done when |
|---|---|---|
| **A0 Data** | `adapters.json` schema and seed; `adapter-caps` schema; this spec's ADR | schemas validate; owner approves the ADR |
| **A1 ELM/STN reads** | `ElmObdLink` (serial, TCP, RFCOMM); detection steps 1–5; `AdapterSource` with generic OBD via `generic_obd2`; clear under R2; laptop and Brain-without-node | recorded-transcript tests pass; owner bench: one genuine or STN adapter and one clone on a CAN car |
| **A2 CAN sniff** | `AdapterSource` over existing `CanLink`s; R9; recorder `clock`/quality fields | a sniff session exports pcapng with host or device timestamps and losses |
| **A3 BLE and STN monitor** | `[ble]` extra, MTU chunking, `STMA`/`STCMM`, can327 as a degraded link | BLE transcript tests; bench with OBDLink CX or vLinker MC+ |
| **A4 Pack K-line on STN** | pack profiles over `STIFI` and one-byte headers (bench first) | the D2 test plan's STN item: Td5 `C1` and live reads, or a recorded "not possible" |
| **A5 Phone** | Capacitor transports, TS framing, WASM decoder and gate | shared vectors pass on the WASM build; Android and iOS bench |
| **A6 J2534** | Windows add-on, read-only | one vendor DLL on the bench |

## 12. Tests (written before the code; ADR-0011: fakes only in tests)

- **Recorded transcripts:** `tests/fixtures/adapters/<adapter>/<case>.jsonl`, each a scrubbed
  AT/ST dialogue captured from a real adapter on the bench (`{t, dir, bytes}`), replayed by a
  `FakeElm327` that answers from the transcript and fails on any unexpected command. Seed cases:
  genuine v2.x, STN, a "v1.5" clone, a "v2.1" clone with two-byte truncation, Wi-Fi, BLE with
  20-byte chunking. Until bench captures exist, hand-written transcripts carry `"synthetic": true`
  and cannot mark a feature tested.
- **Detection:** each transcript yields the expected verdict and caps; a clone never gets `tx`
  above Tier 0 or `listen_only: true`.
- **ObdRequestLink conformance:** the J1979 fixtures F1c, F3–F5, F11 through `ElmObdLink` give the
  decoder-level results (as CanLink T15); `NO DATA`, `?`, `STOPPED`, `SEARCHING...`, `BUFFER FULL`,
  `CAN ERROR`, `BUS INIT: ...ERROR` map to typed errors.
- **Soft gate matrix:** the shared gate vectors run against the soft gate unchanged, plus adapter
  cases: R1 reads in every state; R2 clear Parked, Idling, Moving, unknown; R3 without opt-in, with
  opt-in on a clone, on Wi-Fi, while Moving; R4 Tier 4; R6 `ATSP0` while not Parked; R8 remote
  origin with the override on (refused).
- **Driving state:** stale speed, GPS disagreement and missing rpm give unknown and lock actions.
- **Coexistence:** a node's gate claim or manifest makes the adapter passive; foreign K-line
  traffic before init refuses the init; the adapter's own claim is published and released.
- **Scrub:** a Mode 09 VIN through each adapter link is absent from JSONL, candump and pcapng.
- **Layering:** `openostler.adapters` imports nothing from `web` or any pack; `bleak` is imported
  only inside the BLE transport.

## 13. Out of scope

Reflashing and coding through any adapter; J1939 heavy vehicles; CAN-FD adapters (later, with the
CanLink FD work); OEM-protocol emulation for closed apps; selling or certifying adapters.

## Changelog

- 0.1 (2026-10-07): first draft for the owner (DMD round).

## Decisions for the owner

1. **May the Brain host an adapter?** Recommendation: yes, only for a vehicle with no node, through
   a new ADR that amends the Constitution's two lines and ADR-0032 §2–§3 as in §3. Alternative:
   laptop and phone only; the Brain stays car-free with no exception.
2. **Clones: refuse or read-only?** Recommendation: allow clones for Tier 0 reads and R2 clears with
   a visible "Clone: read-only" chip; refuse R3 actions and manufacturer K-line on them.
   Alternative: refuse clones entirely (simpler support, loses most cheap-adapter users).
3. **Core or add-on?** Recommendation: core (`openostler/adapters/`, stdlib plus pyserial, BLE as an
   optional extra), since the links and the gate are comms core. Alternative: an `ostler-adapters`
   add-on repo with its own release cadence.
4. **Clear codes without opt-in (R2)?** Recommendation: yes, under ADR-0033 §5 with bus-evidenced
   Parked or Idling, since it is a standard OBD service drivers may run. Alternative: clears also
   behind the per-vehicle opt-in.
5. **Tier 2–3 through adapters at all (R3)?** Recommendation: yes, owner opt-in per vehicle and per
   adapter, Parked, local, genuine or compatible verdict, wired or Bluetooth (not Wi-Fi), with the
   warning. Alternative: never; actions need a node.
6. **Browser-only adapters (Web Bluetooth, Web Serial)?** Recommendation: later, Tier 0 reads only,
   Chromium only, after A5 reuses the WASM decoder and gate. Alternative: never; app only.
7. **iOS MFi (OBDLink MX+)?** Recommendation: ask the vendor about app approval at A5; ship iOS with
   BLE and Wi-Fi adapters first. Alternative: skip MFi.
8. **J2534?** Recommendation: last, as a Windows-only read-only add-on (`ostler-adapter-j2534`) on
   demand. Alternative: drop it.
9. **Gate claims by adapters on the module bus?** Recommendation: yes, a soft claim with
   `reason: "adapter"` so a node and the Network page see it. Alternative: no claims; rely on the
   start-time refusal only.
10. **Known-good list as community data?** Recommendation: `adapters.json` in core under CC BY-SA,
    "tested" only with a bench log, community reports accepted with logs. Alternative: owner-tested
    entries only.
11. **STN bench session for the D2 (A4)?** Recommendation: yes, one OBDLink MX+ or EX session on the
    reference car for Td5 and SLABS, recorded in the D2 pack's test plan. Alternative: treat the D2
    as KKL- and node-only.
