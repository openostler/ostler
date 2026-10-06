---
title: "K-line profiles and detection — design"
area: specs
status: stable
version: 0.5
updated: 2026-10-06
depends_on: [decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0024-body-bus-links-passive-by-default.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, references/research/muki01/obd2_kline_reader.md, references/research/muki01/README.md, specs/2026-10-06-u0-seams-design.md, CONSTITUTION.md]
summary: >
  Approved by the owner on 2026-10-06. Implements ADR-0022. A frozen KLineProfile dataclass in kline/profiles.py (line format, iso9141 or kwp2000 framing, header and length modes, checksum, P1–P4, W1–W5, pre-init and abandoned-session idle, keep-alive, release, init method fast/5baud/none) with three built-ins; packs override through a new ModuleSpec.kline mapping that the future pack manifest transport block mirrors. kline.detect() tries functional fast init, then 5-baud 0x33 sent 8N1, requires the inverted address, classifies and decodes key bytes, and is refused unless Parked (an interim server flag, a parked confirmation and a speed veto until U2); module-scan sweeps are Parked-only too, and a detected profile is remembered per vehicle (vid) so a re-init never probes. Adds ISO 9141-2 framing, a poll-thread keep-alive, release and P3-min rules, a snapshot `link` object with OpenAPI and Zod updates, fakes and muki01 regression fixtures. The D2 pack's behaviour and golden test are unchanged; manufacturer protocols stay in U7. Amended for the node/brain direction (ADR-0032): the profile JSON schema is the canonical cross-language form the node's C link layer will read, the remembered profile also lives in node NVS for Ostler Diagnostics alone, the ESP32 node path becomes production and KKL dev-only, and a later step ports the link layer to C with shared test vectors.
---

# K-line profiles and detection — design

**Status:** approved by the owner on 2026-10-06; the answers are in
[Decisions](#decisions-2026-10-06). The questions the owner did not take up stay open and
block nothing in the first step. Amended on 2026-10-06 (v0.4) for the node/brain
direction without undoing the implemented v0.3; see
[§8.1](#81-the-node-path-adr-0032).

## Context

[ADR-0022](../decisions/adr-0022-kline-protocol-profiles-and-auto-detection.md) makes
K-line protocols data and adds auto-detection for cars with no pack profile; this is its
implementation design, ahead of U4 (`generic_obd2` over KKL). Today `KLine` takes loose
timing kwargs (`init_idle`, `init_low`/`init_high`, `write_gap`, `timeout`), `KWP2000`
takes `tolerant`/`addressed`, `ModuleSpec.init` is `"fast" | "slow" | "none"`, the
transport is fixed 10400 8N1, and `SerialTransport.slow_init` reads but never checks the
`~address` byte. Facts come from the [K-line audit](../references/research/muki01/obd2_kline_reader.md)
and ISO 9141-2 / 14230-2, reimplemented in our own words (ADR-0025).

## 1. The profile schema (`src/openostler/kline/profiles.py`)

```python
@dataclass(frozen=True)
class Timing:                       # seconds; ISO 14230-2 normal set unless noted
    p1_max: float = 0.020           # ECU inter-byte gap; ends a reply (ISO 9141 burst split)
    p2_min: float = 0.025; p2_max: float = 0.050   # request end → reply start
    p3_min: float = 0.055; p3_max: float = 5.0     # reply end → next request
    p4: float = 0.0                 # tester inter-byte gap (today's write_gap; 0 = one sweep)
    w1_max: float = 0.300           # 5-baud address end → 0x55
    w2_max: float = 0.020; w3_max: float = 0.020   # 0x55 → KW1, KW1 → KW2
    w4: float = 0.030               # KW2 → ~KW2 (spec window 25–50 ms)
    w5: float = 0.300               # bus idle before any init
    reply_timeout: float = 1.0      # today's KLine timeout; covers extended P2

@dataclass(frozen=True)
class KLineProfile:
    name: str                                   # "iso9141_2", "kwp2000_fast", "td5", …
    framing: Literal["iso9141", "kwp2000"]
    init: Literal["fast", "5baud", "none"]
    init_address: int = 0x33                    # 5-baud address, or fast-init target
    init_address_parity: Literal["none", "odd", "even"] = "none"   # 8N1 (§5)
    init_functional: bool = True                # fast init C1 vs 81 format byte
    target: int = 0x33; source: int = 0xF1
    baud: int = 10400; parity: Literal["N", "E", "O"] = "N"        # 8 data bits, 1 stop
    header: Literal["auto", "none", "physical", "functional", "iso9141"] = "auto"
    length: Literal["auto", "format", "separate", "none"] = "auto"
    iso9141_header: bytes = b"\x68\x6A\xF1"     # request header (iso9141 framing only)
    checksum: Literal["sum8", "xor", "twos_complement"] = "sum8"
    timing: Timing = Timing()
    timing_set: Literal["normal", "extended"] = "normal"
    init_low: float = 0.025; init_high: float = 0.025              # fast-init TiniL/TiniH
    pre_init_idle: float | None = None          # None → timing.w5
    abandoned_idle: float | None = None         # None → timing.p3_max (§4.3)
    keepalive: bytes | None = b"\x3E\x01"       # None = no keep-alive
    keepalive_interval: float = 2.0             # must be < p3_max / 2
    release: bytes | None = b"\x82"             # None = stop and wait (ISO 9141)
    confirm_address: Literal["require", "report"] = "require"      # 5-baud ~address
    tolerant: bool = True                       # CONSTITUTION: keep for KKL cables
    evidence: str = ""                          # car result behind a non-default parity
```

**Built-ins** (`BUILTIN: Mapping[str, KLineProfile]`, generic only, per ADR-0022):

| name | framing | init | header / length | keep-alive | release |
|---|---|---|---|---|---|
| `iso9141_2` | iso9141 | 5baud `0x33` | `68 6A F1` / none | `01 00` | none (wait P3max) |
| `kwp2000_slow` | kwp2000 | 5baud `0x33` | auto (from key bytes) | `3E 01` | `82` |
| `kwp2000_fast` | kwp2000 | fast `C1 33 F1 81` | auto (from key bytes) | `3E 01` | `82` |

`checksum` implements all three enums (a few lines each), but only `sum8` is used by a
built-in; `xor` and `twos_complement` exist for pack-declared U7 profiles.

**Validation** (`resolve(base, overrides) -> KLineProfile`, `dataclasses.replace` plus
checks, raising `ValueError` at pack load): unknown keys; wrong types; `keepalive_interval
>= timing.p3_max / 2`; `iso9141` framing with `release` or a `header` other than `iso9141`;
`init_address_parity != "none"` with an empty `evidence` (ADR-0022: parity only with a car
result). `Timing` overrides are a nested mapping (`{"timing": {"p3_min": 0.0}}`).

**Pack overrides.** `ModuleSpec` gains `kline: Mapping[str, Any]` (an empty read-only
mapping by default). `ModuleSpec.kline_profile()` in `pack.py` picks the base from `init`
(`"fast"` → `kwp2000_fast`, `"slow"` → `kwp2000_slow`, `"none"` → no profile), sets
`init_address`/`target` from `address`, applies `kline` (which may also name a base with
`"base": "iso9141_2"`), and names the result after the module id. `kline/` never imports
`pack.py` (layering test unchanged). When the declarative pack manifest lands (U3, [vehicle
data model](../references/research/ui/vehicle_data_model.md) `systems[].transport`), its
`transport` block carries the same keys and maps onto `ModuleSpec.kline`;
`schemas/kline-profile.schema.json` validates both. This is not `logs/vehicle.json` (the
U0 `vid` file).

**D2 examples** (values the pack passes today, moved into data in migration step 2, §8):

```python
ModuleSpec("td5", …, address=0x13, init="fast", kline={
    "init_functional": False, "source": 0xF7, "header": "none", "length": "format",
    "pre_init_idle": 5.0, "abandoned_idle": 0.0, "keepalive": b"\x3E\x01",
    "timing": {"p3_min": 0.0}})                 # 81 13 F7 81 0C, then unaddressed frames
ModuleSpec("slabs", …, address=0x29, init="fast", kline={
    "init_functional": True, "source": 0xF1, "header": "none", "length": "format",
    "pre_init_idle": 0.3, "abandoned_idle": 0.0, "keepalive": b"\x3E",   # bare 3E
    "keepalive_interval": 1.0, "timing": {"p3_min": 0.0}})
ModuleSpec("airbag", …, address=0x5B, init="slow", kline={
    "header": "physical", "confirm_address": "report", "timing": {"p3_min": 0.0}})
```

SLABS's source cycling, `1A 8A` confirm and retry sleeps (8 s, 28 s) stay pack code.

## 2. `kline.detect()` (`src/openostler/kline/detect.py`)

```python
def detect(transport, *, clock=time.monotonic, sleep=time.sleep,
           on_event=None) -> DetectResult      # (link, profile, key_bytes, method, log)
```

1. **Listen first.** Hold the line idle for W5 (300 ms) and read RX. Any byte means another
   tester or an open session: abort with `bus-busy`, send nothing.
2. **Fast init.** `KLine(target=0x33, source=0xF1).fast_init_tolerant(functional=True)`
   sends `C1 33 F1 81 66`. The existing echo skip, glitch tolerance and unaddressed
   `03 C1 …` handling apply. `C1 KB1 KB2` → KWP2000 fast, decode key bytes (step 4).
   A negative reply (`7F 81 …`) means a KWP ECU is there but refused: stop with
   `ecu-refused` and do **not** go on to 5-baud (an ignition cycle is the remedy).
3. **5-baud `0x33`** after another W5: address 8N1 (§5), read `55 KW1 KW2` within W1–W3,
   send `~KW2` after W4, then read `~0x33 = 0xCC`. A missing or wrong `~address` is
   `init-failed`, never a guess (`confirm_address="require"` on built-ins). No `55` is
   `no-ecu`.
4. **Classify** (`src/openostler/kline/keywords.py`, pure):
   - `KW1 == KW2` (`08 08`, `94 94`) → `iso9141_2`.
   - Otherwise KWP2000: `kwp2000_slow` (5-baud) or `kwp2000_fast`. Decode KB1 (bits 0–6
     after the odd-parity bit 7): bit 0 AL0 (length in the format byte), bit 1 AL1
     (separate length byte), bit 2 HB0 (header without addresses), bit 3 HB1 (header with
     target and source), bits 5–4 TP (`01` normal, `10` extended timing), bit 6 set. KB2
     is `0x8F`. Header: HB1 → `functional` to `0x33` (the OBD convention), else HB0 →
     `none`; length: AL0 → `format`, else `separate`. `timing_set` from TP.
   - A byte with bad parity, KB2 ≠ `0x8F` or a TP of `00`/`11` is logged as `odd key bytes`
     and the KWP defaults stay (functional, format length, normal timing); detection is not
     failed (ADR-0022 says "otherwise KWP2000").
   - Cross-check, candidate: the D2 SLABS answers `C1 57 8F` (`0x57` → AL0, AL1, HB0 only,
     normal) and runs unaddressed frames; the D2 airbag answers `E9 8F` (`0x69` → AL0, HB1,
     extended) and runs addressed frames. Both fit this decode; neither is proof of the
     bit table, which the implementer re-checks against ISO 14230-2.
5. The result is logged and reported in the snapshot (§6). One `detect()` is at most one
   fast and one 5-baud attempt; it never sends KW1281, DS2, KW82 or Honda frames.

**The Parked-only gate.** Detection runs only through the queued server command
`detect_protocol`, executed on the poll thread (CONSTITUTION: K-line access is serialized
there); a source never auto-probes on connect or server start. A source with no profile
connects to status `needs-detect` and sends nothing.

- **With U2:** `refusal()` asks the U2 driving state; only `parked` passes. Unknown speed
  counts as Moving on head-unit classes (ADR-0018 Q5).
- **Until U2** (interim, owner Q3, 2026-10-06; removed by the U2 spec): `detect_protocol`
  is refused unless the server was started with `--kline-detect`, the request carries
  `params.confirm_parked: true` (the UI asks "Vehicle parked?"), and no evidence of motion
  exists (GPS fix speed ≥ 3 km/h, or a pack speed signal > 0, refuses). Refusal text:
  "probing an unknown car is allowed only when Parked".
- **Re-init of a known profile** (pack-declared, detected earlier, or remembered for this
  vehicle) after a link drop or a restart is allowed in every state, with backoff 1, 2, 4,
  8 … capped at 30 s unless the pack's own retry policy is set. A re-init uses only the
  known profile's own init; it never falls back to the other init method.
- **Remembered per vehicle** (owner Q5, 2026-10-06). A profile confirmed by `detect()` is
  stored per `vid` (the U0 vehicle id, never the VIN; ADR-0018 Q7) in the server's state
  directory beside the remembered CAN rate ([CanLink spec §4](2026-10-06-canlink-isotp-design.md)):
  `{profile, key_bytes, address, detected_utc}`. On the next connect for that `vid` the
  source starts from it (`origin: "remembered"`), so a reboot while driving re-inits
  without probing. Key bytes that differ from the stored ones (a different car on the same
  `vid`) end the session at once and count as a failure. If the remembered profile's init
  fails three times, the source drops to
  `needs-detect` and waits for a Parked `detect_protocol`; it never probes on its own. A
  vehicle switch in the garage (U6) or `detect_protocol` replaces the entry; Developer can
  forget it.
- **Module-scan sweeps are probing** (owner Q4, 2026-10-06). `ModuleScanner.scan()` and
  `probe_fast`/`probe_slow` sweeps (fast and slow init across addresses) run only under the
  same Parked gate: through a queued server command, the U2 driving state once it exists
  and the interim rules above until then. The `module_scan.py` tool refuses to start
  without `--confirm-parked` (or a "Vehicle parked?" yes at its prompt) and states the
  rule. A single pack-declared module init is not a sweep.
- **Manual override:** only in Developer under service mode (U2). Until then a server flag
  `--kline-profile NAME` sets it for the process; no HTTP override.

## 3. ISO 9141-2 framing (`src/openostler/kline/frame_iso9141.py`)

- `encode(data, header=b"\x68\x6A\xF1") -> header + data + sum8`, data 1–7 bytes. Example:
  keep-alive `68 6A F1 01 00 C4`.
- Replies are `48 6B <ecu> data… cs` with no length byte. `split(burst) -> list[Iso9141Frame]`
  strips our exact echo first, then cuts the burst at each `48 6B` where the preceding
  segment's checksum verifies (4–11 bytes per frame), keeps the ECU address per frame, and
  drops (and logs) segments that never verify. Multi-frame and multi-ECU bursts therefore
  come back as separate frames.
- `KLine` selects the framer from `profile.framing`: `kwp2000` keeps today's `frame.py`
  and `_scan_for_frame` byte for byte; `iso9141` uses `converse()` with `gap = p1_max` +
  margin and `split()`. A thin `Iso9141Session` offers `request(data) -> list[frame]`,
  `keepalive_if_due()` and `release()`. J1979 is U4's. `69 6A F1` is not adopted (open question 3).

## 4. Session hygiene

**4.1 Keep-alive.** `KLine` records `last_tx` and `last_rx_end` through an injectable
clock. `EcuSession.keepalive_if_due()` and `Iso9141Session.keepalive_if_due()` send
`profile.keepalive` when `now - last_tx >= keepalive_interval`, else nothing. Any request
resets the timer, so a busy poll sends no extra frames. DataSources call it at the start
of `poll()`, and the server's poll loop calls an optional `source.tick()` between polls,
so a session idle for 10 s still gets keep-alive. A failed keep-alive is logged, never
fatal on its own (as the D2 SLABS source does). The existing `_keepalive_sub` stays as the
legacy path until migration step 2 replaces it with `profile.keepalive`.

**4.2 Release.** KWP: `EcuSession.release()` sends `82` (unchanged) on exit, module switch
and error paths; `_establish`'s best-effort `82` stays. ISO 9141 `release()` sends nothing.

**4.3 Abandoned sessions.** A session that ended without a confirmed `C2` (ISO 9141
always) is *abandoned*: the next init on that bus waits until `abandoned_idle` (P3max,
5 s) has passed since `last_tx`. Otherwise only `pre_init_idle` (W5) applies. The muki01
5.5 s idle before every init is not copied. D2 profiles set `abandoned_idle: 0.0` and keep
their own idles.

**4.4 P3 minimum.** `KLine._send` waits until `last_rx_end + timing.p3_min` before the
first byte. In tolerant mode the 60 ms burst gap already exceeds 55 ms, so the guard
mostly matters for strict reads. D2 profiles set `p3_min: 0.0` until a car run confirms
55 ms is harmless (a D2 test-plan item).

## 5. The 5-baud address is 8N1

`SerialTransport.slow_init_bits(address, parity="none")` keeps its current output for the
default: start, eight data bits LSB first, stop (the 2026-08-04 fix; `0x29` never becomes
`0xA9`). `odd`/`even` (seven data bits plus parity) exist only for a pack profile with
`evidence` (U7). `slow_init` gains `bit_seconds`, `w4` and `read_timeout` from the profile
(defaults unchanged). A new pure `parse_slow_init_reply(raw, address) -> SlowInitReply(kw1,
kw2, inverted_address, confirmed)` accepts the `~address` with or without the `~KW2` echo
in front of it. `KLine.slow_init()` keeps returning `(kw1, kw2)`; `KLine.slow_init_reply()`
returns the full result, and `confirm_address="require"` turns `confirmed=False` into
`KLineTimeout`. `EspTransport` exposes the same hook; if its bridge does not pass the
`~address` through, detection over it fails closed (open question 4).

## 6. API and integration

- **Construction.** `KLine.from_profile(transport, profile)` and
  `KWP2000.from_profile(kline, profile)` (`tolerant`, `addressed` from `header`). The old
  constructors and kwargs stay and win when given, so existing pack code is untouched.
  `EcuSession(kwp, profile=None)` takes defaults (`idle`, keep-alive, release) from the
  profile when the caller passes none.
- **Transport.** `web/sources.py::_transport(port, raw_log_path, profile=None)` opens
  `SerialTransport(baudrate=profile.baud)` with the profile's parity (today 10400 8N1).
- **Pack DataSources** use `spec.kline_profile()`. **The generic source (U4)** holds
  `profile=None`, reports `needs-detect`, runs `detect()` when the gated command arrives,
  then re-inits with the detected profile on drops.
- **Logging.** `KLine` takes `on_event(kind, **fields)`; the server writes these to
  `connection.log`: `listen`, `fast-init` (with `last_pulse`), `5baud` (address, key bytes,
  `~address`), `classified` (profile, decoded bits), `keepalive`, `release`, `refused`.
  `LoggingTransport` already logs every byte; detection reads no VIN.
- **Snapshot.** Sources add `link` (null when no K-line link):
  `{"bus": "kline", "profile": "kwp2000_fast", "protocol": "kwp2000" | "iso9141_2",
  "init": "fast" | "5baud" | "none", "origin": "pack" | "detected" | "remembered" | "override",
  "address": "0x33", "key_bytes": "E9 8F" | null, "timing": "normal" | "extended" | null,
  "since": <epoch s>}`. `status` gains `needs-detect`.
- **Contracts.** `api/openapi.yaml`: a `KLineLink` component, `Snapshot.link` as
  `oneOf [null, KLineLink]`, `needs-detect` in `status`, and `detect_protocol` with its
  refusal. `ui/src/api/schemas.ts`: `link: KLineLink.nullable().optional()`, plus a fixture
  in `ui/src/api/fixtures/`. `api/asyncapi.yaml` follows if it restates the Snapshot.
  `schemas/kline-profile.schema.json` is new (§1).

## 7. Tests (no hardware; `FakeKLineEcu` and a `FakeClock`)

`FakeKLineEcu` gains `slow_init_reply` (default today's `55 E9 8F`), `fast_reply` and an
`inits` order list; new `FakeIso9141Ecu` (`08 08`, `~addr CC`, `48 6B 10 …`),
`FakeKwpSlowEcu`, and `FakeClock` (`now()`/`sleep()`, so timing tests never sleep).

| Area | Cases |
|---|---|
| Init paths | fast success; fast silent → 5-baud ISO 9141; 5-baud KWP; nothing → `no-ecu`; RX during W5 → `bus-busy`, nothing sent; `7F 81` → `ecu-refused`, no 5-baud |
| Order | `inits == ["fast", "5baud"]`; no KW1281/DS2/KW82/Honda bytes ever in `sent` |
| Key bytes | `08 08`, `94 94` → ISO 9141; `E9 8F`, `57 8F`, `EF 8F`, `D0 8F` decode to the expected header/length/timing; bad parity, KB2 ≠ `8F` → logged defaults |
| Inverted address | `~addr` wrong (`0x33`), missing, or echo-only → `init-failed`; `report` mode returns `confirmed=False` |
| 8N1 | `0x29` bits unchanged (not `0xA9`); `0x33` unchanged; non-`none` parity without `evidence` → `ValueError` |
| P3 | two requests 10 ms apart wait to 55 ms after the reply end; `p3_min=0` sends at once |
| Keep-alive | 10 s idle on `FakeClock` → `3E 01` at 2, 4, 6, 8 s (KWP) and `68 6A F1 01 00 C4` (ISO 9141), all inside P3max; continuous polling → no extra frames; bare `3E` override |
| Release | KWP close → `82` sent; ISO 9141 close → nothing sent, next init waits P3max; confirmed `C2` → only W5 |
| ISO 9141 framing | encode checksum; echo stripped; bad checksum rejected |
| Server | `detect_protocol` refused without the flag, without `confirm_parked`, with GPS speed; allowed otherwise; re-init of a known profile is not refused while "moving"; no probe on connect |
| Remembered | detect stores `{profile, …}` under the `vid`, never a VIN; restart with "moving" → re-init from it, nothing else sent; three failed re-inits → `needs-detect`, no probe |
| Module scan | sweep refused without the Parked gate (server) or `--confirm-parked` (tool); allowed with it |
| Contracts | `link` validates in OpenAPI and Zod; the profile schema accepts the D2 overrides |

**muki01 regression fixtures (K-line only):** 4+ DTCs over two `48 6B` frames split into
two frames (header bytes never read as DTCs); a merged two-ECU burst keeps both
addresses; a reply checksum is verified, not read at fixed offsets; after detection every
request carries the detected header (the vendored copy's headerless "Automatic" frames);
the reply `03 C1 …` and a glitch byte before `C1` are accepted; key bytes are decoded, not
ignored; any `~address` is not accepted; no 5.5 s idle before a first init.

## 8. Migration

1. **Platform** (this spec): profiles, detect, framing, hygiene, contracts. Old
   constructors are untouched, and `ModuleSpec.kline` defaults to empty, so the D2 pack
   runs byte for byte as before. CI runs the D2 golden test (`needs_pack`) and the D2 pack
   tests; both must stay green with no fixture regeneration.
2. **D2 pack** (its own repo, later): declare the §1 overrides and build sessions through
   `from_profile`; the golden test and a raw-capture replay must show identical TX bytes
   and timings. Raising `p3_min` or the abandoned rule for the D2 is a car-test item.
3. **Port to C, later** ([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md)):
   once the K-line facts are stable, port profiles, detection, framing and hygiene to the
   node's portable C link layer (in `ostler-firmware`). Shared test vectors (bytes on the
   line in, profile, key bytes and frames out, plus the init and gate cases) are seeded
   from the golden tests and the §7 fixtures, and run in CI against both the C build and
   this Python reference.

### 8.1 The node path (ADR-0032)

The implemented v0.3 stays as built; this section only places it in the node/brain
direction.

- **The schema is the cross-language contract.** `schemas/kline-profile.schema.json` is
  the canonical form of a profile. The node's C link layer reads profiles as JSON in this
  form (built-ins and pack overrides alike), so `KLineProfile` in Python and the C struct
  are two readers of one schema, never two definitions.
- **The remembered profile also lives on the node.** For Ostler Diagnostics alone (a
  node with no hub) the remembered `{profile, key_bytes, address, detected_utc}` entry per `vid` is
  kept in the node's NVS, so a node reboot while driving re-inits without probing, as in
  §2. With a brain present the brain's state file and the node's NVS copy hold the same
  entry; the node's copy is the one the link layer uses.
- **Production K-line is the ESP32 node; the KKL cable is dev-only.** The KKL/FTDI
  `SerialTransport` path stays for the lab, bench work and the Python reference tests.
  The node runs the same profiles, the Parked-only probing rule and the same gate, and the
  gate on the node is the only path to the car.
- Open question 4 (the `~address` byte over the ESP32 bridge) now belongs to the node
  firmware's K-line driver.

## 9. Out of scope

Manufacturer protocols (KW1281, DS2, KW82, Honda) and their framers are U7; only their
schema fields exist here. Also out: J1979 (U4), the Link sheet UI, CAN and body buses
(ADR-0020, ADR-0024), and `modscan` changes beyond its Parked gate (§2).

## Decisions (2026-10-06)

The owner answered on 2026-10-06 (owner question numbers in brackets).

| # | Question | Decision |
|---|---|---|
| 1 | Interim gate until U2, or wait for U2? | (Q3) Yes: probing before U2 with the server flag, `confirm_parked` and the speed check (§2) |
| 2 | Does `modscan` count as probing? | (Q4) Yes: module-scan sweeps are Parked-only (§2) |
| 6 | Persist a detected profile per vehicle? | (Q5) Yes: remembered per `vid`, re-init without probing (§2) |

**Still open** (not raised with the owner; none blocks migration step 1):

3. `69 6A F1` for ISO 9141 modes 02/05 (needs a J1979 check)?
4. Does the ESP32 bridge return the `~address` byte, or does detection over it need
   firmware work? Until known, detection over it fails closed (§5).
5. D2 airbag/BCU use `confirm_address: "report"`; should a car run move them to `require`?

## Changelog

- 2026-10-06 — v0.1: first draft from ADR-0022.
- 2026-10-06 — v0.2: approved by the owner. Interim pre-U2 gate confirmed; module-scan
  sweeps Parked-only; detected profile remembered per `vid` (`origin: "remembered"`);
  questions 3–5 stay open.
- 2026-10-06 — v0.3: migration step 1 implemented in the platform. Implementation notes:
  the generic source is `web/kline_source.py::KLineLinkSource`; the gate and the
  remembered-profile wiring are in `web/kline_cmds.py`; the remembered entries are in
  `<state dir>/kline_profiles.json`; the server command is `module_scan` (reply `scan`).
  The module-scan gate sits at the entry points (the server command and
  `tools/module_scan.py`), not inside `AddressScanner`, so the D2 pack's own copy of the
  tool is unchanged until migration step 2. ISO 9141 bursts are read with a gap of
  `p1_max` + 40 ms (so a second ECU's frame within P2max stays in the burst). The KB1
  decode was re-checked against the ISO 14230-2 key-word layout (2000–2031); a KB1 with
  neither HB bit set keeps the functional header, and with neither AL bit the format
  length.
- 2026-10-06 — v0.4: amendment for the node/brain direction (ADR-0032); the implemented
  v0.3 is unchanged. The profile JSON schema is the canonical cross-language form the
  node's C link layer reads; the remembered profile also lives in node NVS for Lite; the
  ESP32 node path becomes production and KKL dev-only (§8.1); a later migration step 3
  ports the link layer to C with shared test vectors seeded from the golden tests.
- 2026-10-06: v0.5, wording only: "Ostler Lite" reads Ostler Diagnostics (ADR-0039).
