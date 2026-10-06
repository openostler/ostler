# CAN shared test vectors

Frames in, results out, for ISO-TP and the transmit gate
([CanLink spec](../../../specs/2026-10-06-canlink-isotp-design.md) §6, §7, §7.1 and §11).
The Python code in `src/openostler/can/` is the lab/reference; the node's C ISO-TP and C
`TxGate` must pass the same files ([ADR-0032](../../../decisions/adr-0032-one-node-optional-brain.md)).
`tests/test_can_vectors.py` runs every file here against the Python reference.

## Format

Each file is one JSON object:

```json
{
  "format": "ostler-can-vectors/1",
  "kind": "isotp",
  "description": "what the cases check",
  "source": "where the facts come from",
  "cases": [{"id": "rx-F1c", "op": "reassemble", "...": "inputs", "expect": {"...": "outputs"}}]
}
```

- Bytes are spaced upper-case hex strings (`"02 01 00 55 55 55 55 55"`); CAN ids are hex
  strings (`"7DF"`, `"18DB33F1"`) with `ext` saying whether the id is 29-bit.
- Times are seconds on a virtual clock that starts at 0; nothing sleeps.
- No VIN or other identity reply appears here (ADR-0036); payloads are made-up bytes.

### `isotp.json` (`kind: "isotp"`)

| `op` | Input | Expected |
|---|---|---|
| `segment` | `payload` (or `payload_len` for an over-long one), `pad` (hex byte or `null`) | `frames` (SF, or FF + CFs), or `error` (`"length"`) |
| `reassemble` | `frames` fed in order to one receiver, `bs` (our block size, 0 = none) | `events`: one `[event, value]` per frame |
| `fc` | `status` (0 CTS, 1 WAIT, 2 OVFLW), `bs`, `stmin`, `pad` | `frame` |
| `stmin` | `values`: STmin byte (hex) → seconds | seconds (compare within `1e-9`) |
| `transmit` | `payload`, `pad`, `fcs`: the receiver's FC frames, one per FF and per block | `result` (`ok`, `overflow`, `max_wft`, `n_bs`) and the `frames` the sender put out |

Reassembly events: `["first", total]` (an FF: send FC), `["progress", block_full]` (a CF;
`true` when `bs` CFs are in and the next FC is due), `["message", payload]`,
`["aborted", reason]` (`sequence`, `short`) and `["ignored", reason]` (`stray`, `fc`,
`malformed`, `empty`). A transmit case uses the defaults `max_wft` 10 and N_Bs 75 ms;
STmin only paces the frames, so `frames` lists bytes, not times.

### `gate.json` (`kind: "gate"`)

A case is a fresh gate with an optional `allowlist` (entries as in
`schemas/can-tx-allowlist.schema.json`), `allow_remote` (the install override, default
false), `grants` and `probes`, and a list of `steps`. State carries across the steps of
one case: single-use grants, the FC window, the Tier 0 rate limit and the `3E` sweep
window. File-level `defaults` give `tier0_min_gap` (50 ms), `fc_window` (5.5 s),
`sweep_window` (5 s), `link_kind` and `rate_ok`.

- `grants`: name → `{action, tier, origin, at, ttl, signature?}`, minted at time `at` by
  the gate; `expect_mint` names the refusal when minting must fail (a remote origin
  without the override); `forged: true` builds a validly signed grant that this gate never
  minted (its nonce or challenge is unknown, so it is `grant_used` if no earlier check
  refuses it). `signature` is `valid` (the default), `bad` (a broken signature) or
  `unknown_key` (signed by a key outside the trust store); both of the last two are
  `grant_invalid`. Runners sign with a test key: the Python runner gives each grant a
  stand-in `token` and injects a fake verifier (`TxGate(grant_verifier=…)`); the C runner
  signs real tokens with a test key in its trust store.
- `probes`: name → `{at, driving_state}`, a silent-bus probe grant minted at `at`;
  `expect_mint` as above (`not_parked`).
- A send step: `{t, driving_state, frame, grant, rate_ok?, link_kind?, expect}`, where
  `grant` is `"tier0"`, a grant name or `null` (no grant).
- A probe step: `{t, probe, one_shot, driving_state, frame, expect}`.
- `expect` is `{allowed, reason, action?}`. Allowed reasons: `tier0`, `fc`, `allowlist`,
  `probe`. Refusals: `rate_not_confirmed`, `mqtt_link`, `remote`, `tier4_service`,
  `mode08`, `sweep_not_parked`, `rate_limited`, `not_allowlisted`, `driving_state`,
  `no_grant`, `grant_invalid`, `grant_used`, `grant_expired`, `grant_mismatch`,
  `entry_rate`, `no_one_shot`, `probe_used`, `not_parked`, `probe_frame`.

#### Check order

A frame can fail several rules; the first one in this order names the refusal, so every
port must check in exactly this order (`TxGate._decide` in `src/openostler/can/gate.py`).
"Diagnostic id" is `7DF`, `7E0`–`7E7`, `18DB33F1` or `18DAxxF1`; "functional" is `7DF`
or `18DB33F1`; the service byte is that of an ISO-TP SF or FF.

1. The rate is not confirmed: `rate_not_confirmed`.
2. The link is MQTT-fed: `mqtt_link`.
3. The grant's origin is remote and the install override is off: `remote`.
4. The service is Tier 4 (`27 2E 2F 31 3B 11 14 28 85`): `tier4_service`.
5. The service is OBD Mode 08: `mode08`.
6. An FC (PCI `3`) on a diagnostic id inside an open FC window: allowed, `fc`.
7. A single frame on a diagnostic id whose service is a Tier 0 read
   (`01 02 03 06 07 09 0A 22 19 3E`):
   1. a `3E` while not Parked that is functional, or physical while permitted physical
      `3E` frames to two other ids lie within `sweep_window` (this would be the third
      distinct ECU): `sweep_not_parked`;
   2. a permitted Tier 0 frame on the same id within `tier0_min_gap`: `rate_limited`;
   3. else allowed, `tier0` (it opens the FC window; a physical `3E` enters the sweep
      window, Parked or not).
8. A CF (PCI `2`) of a message whose FF the gate permitted: allowed, `allowlist`.
9. No allowlist entry matches: `not_allowlisted`.
10. The driving state is not in the entry's `states`: `driving_state`.
11. No `TxGrant` (none, or the Tier 0 marker): `no_grant`.
12. The grant's signature or key fails the verifier: `grant_invalid`.
13. The grant is not outstanding (used, or never minted): `grant_used`.
14. The grant has expired: `grant_expired`.
15. The grant's action or tier differs from the entry's: `grant_mismatch`.
16. The entry's `max_rate_hz` is exceeded: `entry_rate`.
17. Else allowed, `allowlist` (the grant is spent).

A refused frame changes no state (no grant spent, no rate-limit, FC or sweep entry). The
probe has its own order: `mqtt_link`, `no_one_shot`, `probe_used`, `not_parked`,
`probe_frame`, else `probe` (the probe grant is spent whatever the outcome).

Adding a case: add it to the file (or a new file with a new `kind`), and teach
`tests/test_can_vectors.py` the kind if it is new. Vectors are CC BY-SA 4.0 like the other
fixtures (`REUSE.toml`).
