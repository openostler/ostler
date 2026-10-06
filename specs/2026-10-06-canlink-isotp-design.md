---
title: "CanLink, passive bitrate detection and ISO-TP — design"
area: specs
status: stable
version: 0.6
updated: 2026-10-06
depends_on: [CONSTITUTION.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0023-passive-can-bitrate-detection.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-j1979-service-layer-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, references/research/canbus_headunit.md, references/research/muki01/obd2_can_bus_library.md, references/research/muki01/README.md, references/research/ui/decode_pipeline.md]
summary: >
  Approved by the owner on 2026-10-06. The CAN path of the comms core: a frame-level CanLink beside the byte Transport (ADR-0020) with SocketCAN on stdlib AF_CAN first, then slcan (serial or TCP, for the WiCAN Pro) and GVRET, and python-can only as an optional desktop extra. Links open listen-only. Passive bitrate detection follows ADR-0023 (500k then 250k, 20 clean frames, then a single 01 00; one Parked-only one-shot probe per rate on a silent bus, 500k then 250k automatically; a pack-declared rate skips detection) and send() raises until the rate is confirmed. 11-bit and 29-bit OBD addressing. An IsoTpChannel (our own pure Python everywhere, kernel CAN_ISOTP as an option on SocketCAN; can-isotp only as a dev-time test reference, superseding that detail of ADR-0020) with SF/FF/CF/FC, STmin, block size and ISO 15765-4 timeouts, and a mux that collects one reply per ECU. A TxGate (pack allowlist + Parked + server grant beyond Tier 0 reads), LoggingCanLink with VIN scrub, a FakeCanBus for tests, and hardware notes (CarPiHAT MCP2515 limits; gs_usb or MCP2518FD for 500k). Amended for the node/brain direction (ADR-0032, ADR-0034): this Python CanLink and TxGate are the lab/reference; production CAN I/O is the node's TWAI in C and the production gate is the node's C TxGate, the only path to the car, verifying grants minted by the brain or a paired phone; SocketCAN, slcan and python-can on the Pi are lab/dev paths. v0.4: the first implementation step is built on fakes (src/openostler/can/, tests T1–T17, shared vectors in tests/vectors/can/); server wiring and the Pi unit remain. v0.5.1: a CI job runs the needs_vcan tests on a real vcan0. v0.6 (owner, 2026-10-06): a new refusal grant_invalid (bad signature or unknown key) behind an injectable grant verifier, and the 3E sweep guard: only a physical 3E is Tier 0 in any state; not Parked, a functional 3E or a 3E to a third distinct ECU within 5 s is sweep_not_parked.
---

# CanLink, passive bitrate detection and ISO-TP — design

**Status:** approved by the owner on 2026-10-06; the answers are in
[§14](#14-decisions-2026-10-06). The questions the owner did not take up stay open and
block nothing before bench work. Amended on 2026-10-06 (v0.3) for the node/brain
direction; see [§7.1](#71-production-the-nodes-twai-and-c-txgate).

## Context

ADR-0020 decided a frame-level `CanLink` beside the byte-level `Transport`, listen-only by
default, and ADR-0023 amended it: no transmit until the bitrate is confirmed. Both point to
this spec for the detail. The [CAN research §A5](../references/research/canbus_headunit.md)
drafted the interface; the [muki01 CAN audit](../references/research/muki01/obd2_can_bus_library.md)
is the anti-pattern (normal mode, transmit-probing at guessed rates, accept-all filter, no
ISO-TP, first reply wins). The first user is the [J1979 layer](2026-10-06-j1979-service-layer-design.md)
through `CanObdRequestLink`; later users are CAN/UDS packs, passive sniffing (decode pipeline
S0/S2/S4) and the private add-on bus. U4 needs this for `generic_obd2` on CAN (UI spec §10.1).

Rules: runtime stays stdlib plus pyserial (ADR-0002); core never imports `web` or a pack;
never transmit at an unconfirmed rate; no remote path transmits on a vehicle bus; no VIN in
any log; tests run without hardware.

## 1. Placement

New core package `src/openostler/can/`, a sibling of `transport/`:

| File | Holds |
|---|---|
| `frame.py` | `CanFrame(id, extended, data, dlc, ts, error=False, fd=False, channel="")`; `data` ≤ 8 (≤ 64 reserved for FD) |
| `link.py` | `CanLink` ABC, `LinkCaps`, `LinkState`, errors (`TxRefused`, `RateNotConfirmed`) |
| `socketcan.py` | `SocketCanLink` (stdlib `socket.AF_CAN`, `CAN_RAW`, optional `CAN_ISOTP`), `CanIfControl` |
| `slcan.py` | `SlcanLink` over pyserial or a TCP socket |
| `gvret.py` | `GvretLink` (ESP32RET-compatible binary protocol, serial or TCP) |
| `pycan.py` | `PythonCanLink`, imported lazily, only with the `[can]` extra |
| `logging_link.py` | `LoggingCanLink` (JSONL + candump, scrub) |
| `detect.py` | passive bitrate and ID-width detection (§4) |
| `gate.py` | `TxGate`, the allowlist model and `TxGrant` (§7) |
| `isotp.py` | `IsoTpChannel`, `IsoTpMux`, `IsoTpSniffer`, `KernelIsoTpChannel` (§6) |
| `obd.py` | `CanObdRequestLink`: implements the J1979 `ObdRequestLink` (§5) |

`tests/test_layering.py` adds `can` to the core set; `can` imports `obd.link` (the protocol)
and nothing above it. `ports.py` gains `list_can_interfaces()` (`/sys/class/net/*/type` 280).

## 2. The `CanLink` interface

```python
class CanLink(abc.ABC):
    caps: LinkCaps   # tx, listen_only, set_bitrate, one_shot, error_frames, err_counters,
                     # timestamps, fd, max_rx_rate (frames/s), kind ("socketcan", "slcan", …)
    state: LinkState # closed | listening | confirmed | active
    bitrate: int | None; id_widths: frozenset[int]; rate_source: str  # detected|declared|manual
    def open(self, bitrate: int | None, *, listen_only: bool = True) -> None
    def close(self) -> None
    def recv(self, timeout: float | None) -> CanFrame | None   # error frames have error=True
    def set_filters(self, filters: list[tuple[int, int, bool]]) -> None  # (id, mask, extended)
    def flush_rx(self) -> int
    def error_counters(self) -> tuple[int, int] | None   # (tec, rec)
    def send(self, frame: CanFrame, *, grant: TxGrant | Tier0) -> None
    def send_oneshot(self, frame: CanFrame, *, probe: ProbeGrant) -> OneShotResult
```

- **Listen-only is the default and the open state.** `open()` without `listen_only=False` is
  listen-only on every backend: SocketCAN `listen-only on`, slcan `L`, GVRET listen-only flag.
  The link chip shows the mode (ADR-0020).
- **`send()` raises `RateNotConfirmed`** in `listening` (ADR-0023), and `TxRefused` unless
  `TxGate` passes the frame (§7). `confirmed` → `active` (listen-only off) happens inside
  the first permitted `send()`, and the link drops back to listen-only when the OBD session
  ends or after 30 s without a permitted transmit.
- **A capability we cannot verify is reported, not assumed.** A WiCAN set to `silent` in its
  own config but reached over slcan reports `listen_only: "requested"`; the chip says so.
- MQTT ingest (`MqttCanLink`, ADR-0020) is out of scope here; when it comes, `send()` raises.

## 3. Backends

| Order | Backend | How | Dependency |
|---|---|---|---|
| 1 | **SocketCAN** (CarPiHAT, gs_usb, MCP2518FD, can327, `vcan`) | `socket(AF_CAN, SOCK_RAW, CAN_RAW)`; `CAN_RAW_FILTER`; `CAN_RAW_ERR_FILTER` = `CAN_ERR_MASK`; `CAN_RAW_RECV_OWN_MSGS` to see a one-shot frame's TX confirmation | **stdlib** (`socket.AF_CAN` on Linux, Python ≥ 3.9) |
| 2 | **slcan / LAWICEL**, serial (ESP32 node, CANable slcan) or **TCP** (WiCAN Pro, port 3333) | `C`, `S5`/`S6`, `L` (listen-only) or `O`, `t`/`T` frames, `F` status flags, `Z1` timestamps | pyserial (already a dependency) or stdlib `socket` |
| 3 | **GVRET** (ESP32-CAN-X2, ESP32RET firmware, SavvyCAN-compatible) | binary mode, set bus config with the listen-only flag, frame and keep-alive commands, numbers checked against ESP32RET (MIT) at a pinned SHA | pyserial / stdlib `socket` |
| 4 | **python-can** (PCAN, Kvaser, Vector on Mac/Windows desktops) | `PythonCanLink` wraps `can.Bus`; listen-only where the backend supports it, else `tx: false` | optional extra `[can]`, never on the Pi |

**Why stdlib for SocketCAN and not python-can.** ADR-0002 allows nothing above pyserial at
runtime, and ADR-0020 rejected python-can in core. SocketCAN needs only `AF_CAN` raw
sockets, filters and error frames, all in the standard library; slcan and GVRET are short
line or binary protocols over pyserial or a TCP socket. python-can is LGPL-3: fine as an
optional extra for desktop dongles that have no SocketCAN driver, but it buys nothing on the
Pi and would add a licence line to the commercial build.

**Interface control (SocketCAN).** Bitrate, `listen-only`, `one-shot`, `berr-reporting` and
`restart-ms` are netlink link settings that need `CAP_NET_ADMIN`. `CanIfControl` runs
`ip link set <if> down|type can …|up` (iproute2, present on Pi OS); the systemd unit grants
`AmbientCapabilities=CAP_NET_ADMIN`. It reads `ip -details -json link show` to learn which
ctrlmodes the driver supports and fills `LinkCaps`. On `vcan` there is no bitrate or
ctrlmode, so `set_bitrate` and `listen_only` are false and the rate must be declared (tests).

**slcan and error frames.** LAWICEL has no error frames; `SlcanLink` polls `F` every
200 ms during detection and treats any bus-error, error-passive or overrun flag as an error
frame. `caps.error_frames = "flags"` marks this as weaker evidence (§4).

## 4. Passive bitrate and ID-width detection (ADR-0023)

`detect(link, *, declared=None, remembered=None, driving_state) -> DetectResult`:

1. **Declared rate** (pack `vehicle.json` `transport: {bus: "can", bitrate, id_width}`, or a
   manual choice in service mode): open listen-only at that rate, mark `confirmed`,
   `rate_source = "declared"`. No detection, no probe.
2. **Listen** at each rate in `[remembered, 500k, 250k]` (deduplicated; a remembered rate only
   sets the order): open listen-only with error reporting on, for up to 2 s. Count valid
   frames; any error frame, or growth of the RX error counter, rejects the rate for this
   attempt. **20 clean frames confirm it.** Record the ID widths seen (11, 29 or both).
3. **Then one request:** a single functional `01 00`, on `0x7DF` if 11-bit traffic was seen,
   else on `0x18DB33F1`; RX flushed first; replies collected per ECU (`0x7E8`–`0x7EF`,
   `0x18DAF1xx`). With no reply, the other width is tried once as an ordinary Tier 0 request.
4. **Silent bus** (no frames at either rate, e.g. a gateway OBD port): refused unless the
   driving state is **Parked** (unknown counts as Moving on head units; UI spec §3.5). If
   Parked: per rate, 500k first, reopen with `one-shot on` and listen-only off, send one
   `0x7DF 02 01 00` frame. An ACK (own-message echo) with no error frame confirms the rate.
   **The first error frame stops detection**: back to listen-only, `"bitrate not confirmed"`.
   No ACK and no error moves to 250k automatically (owner Q9, 2026-10-06), after the
   driving state is read again: still Parked, or the 250k probe is refused. A link without
   `one_shot` refuses the probe.
5. **Noisy bus** (frames seen, never 20 clean): stay listen-only, `"bitrate not confirmed"`;
   the user may retry or set the rate in Developer under service mode.

`DetectResult{rate, widths, source, frames, errors, ecus, reason}` feeds the connection
ladder's Bus rung (UI spec §4.5). A confirmed rate is remembered per `vid`, never per VIN.

## 5. OBD addressing and `CanObdRequestLink`

| | Functional request | Physical request | Replies | FC sent to |
|---|---|---|---|---|
| 11-bit | `0x7DF` | `0x7E0`–`0x7E7` | `0x7E8`–`0x7EF` | reply id − 8 |
| 29-bit | `0x18DB33F1` | `0x18DAxxF1` | `0x18DAF1xx` | `0x18DAxxF1` (swap target/source) |

`CanObdRequestLink.request(payload, target=None)` implements the J1979 `ObdRequestLink`
(J1979 spec §2.1): flush RX, send a padded single frame (DLC 8, ISO 15765-4; pad byte
configurable, default `0x55`) through `TxGate` as Tier 0, then let `IsoTpMux` collect one
message per responding ECU until P2 (50 ms) passes with every started message complete, or
P2\* (5 s) after `7F xx 78`. Keys are `"7E8"` or `"18DAF110"`. Pacing (one in flight, ≥ 50 ms
per ECU, `0x21` backoff) is the shared logic in `obd/link.py`. Functional requests are
always single frames; a payload over 7 bytes on a functional ID is refused.

## 6. ISO-TP (ISO 15765-2)

**Our own implementation** (owner Q8, 2026-10-06). ISO-TP is written here in pure Python
(stdlib only): one code path on every backend, every frame visible to `TxGate`, no new
runtime dependency. **can-isotp (MIT) is used only as a test reference**: a dev-only
differential test (T16) checks our channel against it; it is never imported at runtime,
vendored or shipped. **This supersedes one detail of
[ADR-0020](../decisions/adr-0020-can-links-listen-only-by-default.md)**, which named
userspace can-isotp for non-SocketCAN links; the rest of ADR-0020 stands, and the ADR
itself is not edited.

**`IsoTpChannel`** (pure Python, one `(tx_id, rx_id, extended)` pair) and **`IsoTpMux`**
(one functional TX, many RX reassemblers keyed by rx id) share one state machine:

- **SF** `0L` (L 1–7); **FF** `1LLL` (12-bit length, up to 4095; the 32-bit escape is FD-era,
  out of scope); **CF** `2N`, N from 1, wrapping F → 0; **FC** `3S BS STmin` with S = 0 CTS,
  1 WAIT, 2 OVFLW.
- **Receiving** (the tester case): on FF, send FC `30 00 00` (BS 0, STmin 0, as ISO 15765-4
  asks of test equipment) through `TxGate` as a Tier 0 FC tied to a request we sent; then
  expect CFs. A wrong sequence number aborts that message (`malformed: sequence`); a new FF
  restarts it; stray CFs are ignored and counted. A link whose `max_rx_rate` is too low
  (MCP2515, §10) may send a configured STmin instead (open question 2).
- **Sending** multi-frame (UDS later; OBD requests are always SF): wait for FC within N_Bs;
  honour BS (a new FC after each block) and STmin (`0x00–0x7F` ms, `0xF1–0xF9` 100–900 µs,
  reserved values read as 127 ms; timed like `kline._precise_wait`); WAIT up to `max_wft`
  (default 10); OVFLW aborts.
- **Timeouts** (ISO 15765-4 values as defaults, checked against the text when coding):
  N_As/N_Ar 25 ms, N_Bs 75 ms, N_Cr 150 ms; P2 50 ms, P2\* 5000 ms. All live in
  `IsoTpParams` so a pack can override them.
- **Padding:** TX pads to DLC 8; RX accepts any DLC ≥ PCI length and ignores pad bytes.

**`IsoTpSniffer`** reassembles both directions of someone else's session **without sending
FC** (listen-only), for decode-pipeline capture (S4) and for logging.

**Kernel `CAN_ISOTP`** (`KernelIsoTpChannel`) is an option on SocketCAN for *physical*
channels when the module is present (Linux ≥ 5.10): it times CFs and FCs in the kernel,
which matters on slow SPI controllers. Opening one goes through `TxGate` (its tx id must be
a Tier 0 diagnostic id or allowlisted), because the kernel then sends FCs itself; payloads
still pass the gate before `send()`. The functional multi-ECU mux and all non-SocketCAN
backends use the pure-Python channel, which is also what every test exercises. A sniffer may
use `CAN_ISOTP_LISTEN_MODE`.

## 7. Transmit gating (`TxGate`)

Every frame any `CanLink.send()` emits passes `TxGate.check(frame, grant, state)`:

1. **Rate:** `confirmed` or `declared`, else `RateNotConfirmed` (ADR-0023).
2. **Tier 0 exception** (every driving state, ADR-0020 as amended): the id is a diagnostic id
   (`0x7DF`, `0x7E0`–`0x7E7`, `0x18DB33F1`, `0x18DAxxF1`) and the frame is either a single
   frame whose service is a read (OBD `01 02 03 06 07 09 0A`; UDS `22 19 3E`) or an FC for
   an ISO-TP message we are receiving in reply to such a request. Rate-limited per ECU.
   **The `3E` sweep guard** (owner, 2026-10-06, from the node CAN spec's open question 3):
   only a *physical* `3E` (one ECU id) is a Tier 0 read in every driving state. While not
   Parked the gate refuses, as `sweep_not_parked`, a functional `3E` (`0x7DF`,
   `0x18DB33F1`, which reaches every ECU) and a physical `3E` to a third distinct ECU id
   within 5 s of permitted `3E` frames to two others. Parked is unchanged: a functional
   `3E` and `3E` to any number of ECUs pass as Tier 0, still rate-limited per id.
3. **Everything else needs all three:** a **pack allowlist** entry that matches; **Parked**
   (re-read from the injected driving-state callable at send time); and a **`TxGrant`** minted
   by the server gate for that entry's action and tier, short-lived and single-use. Mode 04
   (`7DF 01 04`) is such an entry in `generic_obd2`. Discovery sweeps (`10 01`, physical
   `3E`) are allowlisted Parked-only reads (UI spec §8.1). A single physical `3E` to one
   ECU stays a Tier 0 read in any state (owner, 2026-10-06): it changes nothing and is
   rate-limited; a sweep of `3E` across ECU ids is the Parked-only discovery read, which
   the sweep guard in step 2 enforces at the gate.
   **Grant verification** (owner, 2026-10-06, from the node CAN spec's open question 2):
   the gate first passes the grant to an injected verifier; a bad signature or an unknown
   key is refused as `grant_invalid`, distinct from `grant_used` (a nonce or challenge
   already spent or never issued). The Python reference's default verifier accepts its
   own unsigned in-process grants and refuses any grant carrying a token it cannot check;
   it implements no signature scheme (no new runtime dependency), and tests inject a fake
   verifier.
4. **Never:** a frame from a remote path (the server mints no grant for one), Tier 4
   services (`27 2E 2F 31 3B 11 14 28 85` on UDS) unless an ADR enables them, or anything
   on a link opened by `MqttCanLink`.

**Allowlist** (pack `vehicle.json` `can.tx_allowlist`, `schemas/can-tx-allowlist.schema.json`):
`{bus, id, extended, dlc, data` (hex with `xx` wildcards)`, max_rate_hz, action, tier,
states` (default `["parked"]`)`}`. `TxGrant` is a plain core dataclass (`action, tier,
expires, nonce, origin, token`) so the web layer can mint it without core importing
`web`; `token` is empty for an unsigned lab grant. Every refusal is logged with its
reason; every permitted non-Tier-0 frame is logged with the action. The exact order of
the checks, which decides the refusal code when several rules fail, is listed in
[`tests/vectors/can/README.md`](../tests/vectors/can/README.md) and mirrored by the C
port.

### 7.1 Production: the node's TWAI and C TxGate

Amendment, 2026-10-06 ([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md),
[ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md),
[ADR-0034](../decisions/adr-0034-repo-boundaries.md)). This spec is still built as
approved, in Python, and it becomes the **lab/reference** implementation:

- **Production CAN I/O is the node's TWAI controller, in C.** The node opens it
  listen-only, runs the same ADR-0023 detection and the same ISO-TP rules, and publishes
  decoded VSS messages; the brain never touches the car bus.
- **The production gate is the node's C `TxGate`, the only path to the car.** It applies
  the same rules as above (rate, Tier 0 exception, allowlist + Parked + grant, the
  "never" list) and re-reads the driving state on the node at send time.
- **Grants are minted by the brain or a paired phone and verified by the node.** A
  `TxGrant` becomes a signed, short-lived, single-use token for one action and tier; the
  node checks the signature (`grant_invalid`), the nonce (`grant_used`), the expiry and
  its own state before any frame leaves. Grants are minted only over local links; a remote path mints none unless the
  install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is set (ADR-0033).
- **SocketCAN, slcan and python-can on the Pi are lab/dev paths** (bench work, decoding,
  sniffing and the reference tests), not the production route to the car.
- **Shared test vectors** (frames in, results out, plus the gate cases T4, T5, T8 and
  T17) are seeded from §11 and run in CI against both the C build and this Python
  reference.
- The TWAI node firmware is tracked in `ostler-firmware` (ADR-0034), not in this repo.

## 8. `LoggingCanLink` and scrub

Wraps any `CanLink` and keeps `LoggingTransport`'s discipline (line-buffered, fsync every
2 s). It writes JSONL `{ts, dir, id, ext, dlc, data, err}` and candump
`(ts) can0 7E8#0641000000000000`. A stateful scrubber follows ISO-TP messages per id and
blanks the data bytes of VIN and serial payloads (`49 02`, `62 F1 90`, `62 F1 8C`; patterns
from `obd/vin.py`) across FF and CFs: JSONL holds `<redacted n bytes>` (as in the packs spec
§2.7) and candump, which must stay parseable, holds zero bytes. Captures stay out
of git (CONSTITUTION).

## 9. Fake CAN bus for tests

`tests/fake_can.py`:
- `FakeCanBus(bitrate, widths)`: an in-memory bus with a virtual clock; links attach with
  their own configured rate. **A link at the wrong rate receives only error frames** (and RX
  error growth); a listen-only link never puts a frame on the bus; every transmitted frame is
  recorded with its sender for assertions.
- `FakeObdEcu(addr, pids, dtcs, …)`: replies to J1979 requests with ISO-TP, honours FC,
  STmin and BS, and can be told to send late, drop a CF or answer with `7F xx 78`.
- `FakeCanLink`: a `CanLink` on the bus with chosen `LinkCaps` (slcan-like flags only, no
  one-shot, low `max_rx_rate`).
- Optional `needs_vcan` tests run `SocketCanLink` against a real `vcan0` where the CI
  runner can load it; everything else runs on the fake.

## 10. Hardware notes

- **CarPiHAT (MCP2515 over SPI):** two RX buffers, so a busy 500 kbit/s bus overruns them
  ([CAN research A1](../references/research/canbus_headunit.md)). Fine for the private
  250 kbit/s add-on bus and for request/response OBD, where traffic is light; not for
  sniffing a busy powertrain bus. ISO-TP replies at STmin 0 can lose CFs: use a configured
  STmin in our FC, or the kernel ISO-TP channel. Check `ip -details link show` for
  `listen-only` and `one-shot` support; without `one-shot` the silent-bus probe is refused.
- **500 kbit/s sniffing:** gs_usb (candleLight/CANable, MIT firmware) on USB, or an
  MCP2518FD HAT (`mcp251xfd`, deep FIFOs; bench-test bring-up). Both are SocketCAN.
- **WiCAN Pro:** ships in `normal` mode and transmits anything published to `…/can/tx`; set
  `silent` and disable MQTT TX before use. We reach it by slcan over TCP 3333.
- **Bench items** for the owner's test plan: CarPiHAT drop rate at 500k; WiCAN `silent`
  against `can/tx`; one-shot support on each adapter; detection time on a body bus.

## 11. Test plan (written before the code)

| # | Test | Asserts |
|---|---|---|
| T1 | 500k bus, 20 clean frames | 500k confirmed; **zero frames sent** before the lock |
| T2 | error frame at 500k, clean 250k | 250k confirmed |
| T3 | 29-bit-only traffic | the one request goes to `0x18DB33F1` |
| T4 | `send()` before confirmation | `RateNotConfirmed`; nothing on the bus |
| T5 | silent bus, not Parked / Parked / error at 500k / no one-shot cap | refused / one frame per rate, one-shot / stops, listen-only / refused |
| T6 | declared rate | no detection, no probe |
| T7 | slcan with only `F` flags | a bus-error flag rejects the rate |
| T8 | TxGate: Tier 0 read on `7DF` while Moving; `04` without allowlist, Moving, no grant, expired grant; remote path | allowed; each refused with its reason |
| T9 | ISO-TP RX: VIN over FF/CF/FC; SN wrap at 16 CFs; wrong SN; new FF mid-message; stray CF | message; abort; restart; ignored |
| T10 | ISO-TP TX: BS 2, STmin 10 ms and `F5`, WAIT ×3, OVFLW, N_Bs timeout | pacing and aborts |
| T11 | mux: `7E8` + `7E9` multi-frame replies interleaved; late reply after P2 | two messages; late frame dropped |
| T12 | `0x78` then the reply after 2 s | waits under P2\*; one message |
| T13 | LoggingCanLink with a VIN reply | VIN absent from JSONL and candump (ASCII and hex) |
| T14 | `IsoTpSniffer` on someone else's session | reassembled, no FC sent |
| T15 | J1979 fixtures F1c, F3–F5, F11 over `CanObdRequestLink` | same results as the decoder-level tests |
| T16 | differential, dev-only: the same SF/FF/CF/FC sequences (BS, STmin, WAIT, SN wrap) through our channel and can-isotp | identical payloads and FC bytes; skipped when can-isotp is absent, never a runtime import |
| T17 | silent bus: no ACK at 500k, then Moving before the 250k probe | the 250k probe is refused; listen-only |

## 12. Migration

- Purely additive: `transport/`, `kline/`, `kwp2000/` and the D2 pack are untouched; the D2
  has no CAN.
- `pyproject.toml` gains the optional `[can]` extra (python-can) with a comment that it is
  never installed on a Pi; `THIRD_PARTY_LICENSES.md` notes it as optional LGPL-3.
  can-isotp goes only in the `[dev]` extra, as T16's reference; no runtime code imports it.
- The Pi image gains the systemd capability and a note on loading `can-isotp` (optional).
- The 2026-10-02 CAN emulation spec (head-unit side) later reuses `CanLink` for the private
  bus; its device traffic follows the add-on device rules, not this allowlist (ADR-0020).
- `schemas/can-tx-allowlist.schema.json` and the `transport` block in `vehicle.schema.json`
  land with this spec.

## 13. Out of scope

CAN-FD frames and ISO-TP FD; J1939; `ObdRequestLink` for ELM/STN; `MqttCanLink`; J2534;
UDS services beyond Tier 0 reads; extended and mixed ISO-TP addressing; the TWAI firmware
node (tracked in `ostler-firmware`, ADR-0034; see §7.1); netlink without `ip`; any write, routine or security service (Tier 4 needs an ADR).

## 14. Decisions (2026-10-06)

The owner answered on 2026-10-06 (owner question numbers in brackets).

| # | Question | Decision |
|---|---|---|
| 1 | ISO-TP in userspace: our own, or vendor can-isotp? | (Q8) Our own pure-Python channel; can-isotp (MIT) only as a test reference (§6, T16). Supersedes ADR-0020's can-isotp detail |
| 5 | After a no-ACK, no-error 500k probe, move to 250k automatically? | (Q9) Yes, automatically, Parked only, re-checked before the 250k probe (§4, T17) |

**Still open** (not raised with the owner; none blocks the fake-bus work):

2. May our FC carry a non-zero STmin on slow controllers (MCP2515), departing from the
   ISO 15765-4 tester values, or must such links use the kernel channel only?
3. `ip` with `CAP_NET_ADMIN` now, or a stdlib rtnetlink client later to drop the iproute2
   dependency?
4. Default pad byte: `0x55`, `0xAA` or `0x00`? §5 drafts `0x55`.

## Changelog

- 2026-10-06 — v0.1: first draft.
- 2026-10-06 — v0.2: approved by the owner. Our own ISO-TP, can-isotp as a dev-only test
  reference (supersedes that ADR-0020 detail; T16); silent-bus 500k → 250k automatic and
  Parked only (T17); questions 2–4 stay open.
- 2026-10-06 — v0.3: amendment for the node/brain direction (stays approved; §7.1). The
  Python `CanLink` and `TxGate` are the lab/reference; production CAN I/O is the node's
  TWAI in C and the production gate is the node's C `TxGate`, the only path to the car;
  grants are minted by the brain or a paired phone and verified by the node; SocketCAN,
  slcan and python-can on the Pi are lab/dev paths; the TWAI node is tracked in
  `ostler-firmware` (ADR-0034).
- 2026-10-06 — v0.4: first implementation step (fakes only; no D2 behaviour change).
  Built: `src/openostler/can/` (`frame.py`, `link.py`, `socketcan.py` with
  `CanIfControl`, `slcan.py`, `gvret.py`, `pycan.py`, `logging_link.py`, `detect.py`,
  `gate.py`, `isotp.py`, `obd.py`), `ports.list_can_interfaces()`, the optional `[can]`
  extra (python-can) and can-isotp in `[dev]`, `schemas/can-tx-allowlist.schema.json`,
  the layering guard for `can`, `tests/fake_can.py` (virtual-clock bus, `FakeCanLink`,
  `FakeObdEcu`, `FakeIsoTpPeer`, `FakeSlcanDevice`), tests T1–T17 (T16 differential
  against can-isotp, skipped without it; `needs_vcan` skipped without `vcan0`), the J1979
  adapter `can/obd.py` with fixtures F1c, F3–F5 and F11 and the golden two-ECU
  `SupportReport` over ISO-TP, and shared vectors for the node's C port in
  `tests/vectors/can/` (ISO-TP segmentation, reassembly, FC, STmin, transmit outcomes;
  gate cases T4, T5, T8, T17), with the format in its README. Open questions 2–4 use the
  drafted defaults: our FC is `30 00 00` (STmin configurable in `IsoTpParams`), `ip` with
  `CAP_NET_ADMIN`, pad `0x55`. Implementation notes:
  - **Gate details.** Tier 0 single frames are rate-limited to one per 50 ms per request
    id; an FC is Tier 0 for 5.5 s (P2\* plus margin) after a permitted request on the
    matching id (functional `7DF` opens `7E0`–`7E7`; `18DB33F1` opens `18DAxxF1`). The UDS
    Tier 0 list is taken literally (`22 19 3E`), so a physical `3E` is a Tier 0 read; the
    Parked-only discovery sweeps stay the caller's rule. An allowlisted FF covers its own
    CFs. An entry's `states` may be `parked` and `idling` (Mode 04 is Maintenance, Parked
    or Idling per ADR-0033) and never `moving`. Refusals carry a machine code (the vector
    README lists them), are logged and go to an optional audit sink.
  - **`TxGrant` gains `origin`** (`local` or `remote`): the lab gate's `issue()` mints no
    remote grant without `OSTLER_ALLOW_REMOTE_CONTROL` (read once, fixed), and a remote
    grant is refused at send time likewise (ADR-0033 §6). Grants are single-use by nonce.
    The node's signed token (§7.1) is not modelled here.
  - **Mode 04 over CAN:** `CanObdRequestLink(grant_for=…)` asks for a `TxGrant` for any
    request that is not a Tier 0 read; without one the gate refuses it on the bus.
  - **The probe** has its own grant (`TxGate.probe_grant()`, Parked only) and check (a
    one-shot capable link, exactly `7DF 02 01 00` at DLC 8, Parked re-read, single use).
  - **Schemas.** `schemas/vehicle.schema.json` is the local `logs/vehicle.json` record,
    not the pack's `vehicle.json` (which has no schema yet), so the pack `transport`
    block is `$defs/transport` in `can-tx-allowlist.schema.json` for that schema to
    reference when it lands.
  - **Scrub.** `LoggingCanLink` always scrubs identity replies; the ADR-0036 install
    opt-in is not wired yet. A confirmed rate is remembered per `vid` by `RateMemory`.
  Remaining: server wiring (link chip, Bus rung, grant minting, `RateMemory` under the
  state dir), the Pi unit's `CAP_NET_ADMIN` and the optional `can-isotp` module note, a CI
  job with `vcan`, `MqttCanLink`, the pack `vehicle.json` schema, and the C port running
  the shared vectors.
- 2026-10-06 — v0.5: owner confirmed the UDS `3E` reading (§7): a single physical `3E` is a
  Tier 0 read in any state, rate-limited; `3E` sweeps across ECU ids stay Parked-only.
- 2026-10-06 — v0.5.1: the `vcan` CI job loads `vcan` (and `can-isotp` when the runner
  kernel has it) and runs the `needs_vcan` tests, now including `KernelIsoTpChannel` on
  `vcan0`; `OSTLER_REQUIRE_VCAN=1` turns their skip into a failure there (§9).
- 2026-10-06 — v0.6: owner approval of the node CAN spec's open questions 2 and 3
  (`ostler-firmware` `docs/specs/node-can.md` §11), platform first so the C port can
  match (§7). **`grant_invalid`:** `TxGate(grant_verifier=…)` takes an injectable
  verifier (`"ok"` or `"invalid"`; one that raises counts as invalid), checked after
  `no_grant` and before `grant_used`; `TxGrant` gains `token` and `issue()` a `token`
  argument; the default `accept_unsigned` passes the lab's unsigned grants and refuses a
  token it cannot check, so nothing else changes. **The `3E` sweep guard:** while not
  Parked a functional `3E` and a physical `3E` to a third distinct ECU within 5 s
  (`sweep_window`) are refused as `sweep_not_parked`, before the per-id rate limit;
  Parked is unchanged. Gate vectors T8j–T8m added; the T8a rate-limit step moved from a
  functional `3E` to `01 0C`; the vectors README now lists the exact check order.
