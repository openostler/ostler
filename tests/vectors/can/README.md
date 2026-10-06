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
one case: single-use grants, the FC window and the Tier 0 rate limit. File-level
`defaults` give `tier0_min_gap` (50 ms), `fc_window` (5.5 s), `link_kind` and `rate_ok`.

- `grants`: name → `{action, tier, origin, at, ttl}`, minted at time `at` by the gate;
  `expect_mint` names the refusal when minting must fail (a remote origin without the
  override); `forged: true` builds the grant without minting it.
- `probes`: name → `{at, driving_state}`, a silent-bus probe grant minted at `at`;
  `expect_mint` as above (`not_parked`).
- A send step: `{t, driving_state, frame, grant, rate_ok?, link_kind?, expect}`, where
  `grant` is `"tier0"`, a grant name or `null` (no grant).
- A probe step: `{t, probe, one_shot, driving_state, frame, expect}`.
- `expect` is `{allowed, reason, action?}`. Allowed reasons: `tier0`, `fc`, `allowlist`,
  `probe`. Refusals: `rate_not_confirmed`, `mqtt_link`, `remote`, `tier4_service`,
  `mode08`, `rate_limited`, `not_allowlisted`, `driving_state`, `no_grant`,
  `grant_used`, `grant_expired`, `grant_mismatch`, `entry_rate`, `no_one_shot`,
  `probe_used`, `not_parked`, `probe_frame`.

Adding a case: add it to the file (or a new file with a new `kind`), and teach
`tests/test_can_vectors.py` the kind if it is new. Vectors are CC BY-SA 4.0 like the other
fixtures (`REUSE.toml`).
