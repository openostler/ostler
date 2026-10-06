# J1979 shared test vectors

Bytes in, decoded results out, for the J1979 service layer
([spec](../../../specs/2026-10-06-j1979-service-layer-design.md) §9, §10.1). The Python
layer in `src/openostler/obd/` is the lab/reference; the future C link layer on the node
must pass the same files ([ADR-0032](../../../decisions/adr-0032-one-node-optional-brain.md)).
`tests/test_obd_vectors.py` runs every file here against the Python decoders.

## Format

Each file is one JSON object:

```json
{
  "format": "ostler-j1979-vectors/1",
  "decoder": "dtc",
  "description": "what the cases check",
  "source": "where the facts come from",
  "cases": [{"id": "F1a", "...": "inputs", "expect": {"...": "outputs"}}]
}
```

- Bytes are spaced upper-case hex strings (`"43 02 01 70 01 34"`).
- `messages` are whole service messages as the transport hands them over: K-line headers
  and checksums, CAN ISO-TP PCI and padding already removed. `can_frames` and
  `kline_burst` are informational, for the transport ports.
- IDs (PIDs, modes, MIDs, UASIDs) are two-digit hex strings; ECU addresses are strings
  (`"7E8"`, `"10"`).
- Floats compare within `1e-6`. `null` means absent or unknown, never zero.
- No VIN ever appears here: VIN cases are built at test time from parts (ADR-0036).

| File | `decoder` | Input → expected |
|---|---|---|
| `dtc.json` | `dtc` | `flavor`, `mode`, `ecu`, `messages` → `kind`, `codes`, `warnings` |
| `bitmap.json` | `bitmap` | `block`, 4-byte `data` → supported `pids`, `chains` |
| `pids.json` | `pids` | `mode`, `message` and the table `tests/fixtures/j1979/pids.json` → `values`, `errors` |
| `freeze_trigger.json` | `freeze_trigger` | Mode 02 PID 02 `message` → `trigger` |
| `readiness.json` | `readiness` | PID 01/41 `message` → MIL, count, ignition, `monitors` as `[supported, complete]` |
| `mode06.json` | `mode06` | CAN Mode 06 `message` → scaled `tests` and `errors` |
| `mode09.json` | `mode09` | `flavor`, `infotype`, `messages` → `calid`, `cvn` or `name` |
| `clear_gate.json` | `clear_gate` | Mode 04 `context`, current codes, `confirmed`, `allow_remote` → `allowed`, `reason`, `warning` |

Adding a case: add it to the file (or a new file with a new `decoder`), and teach
`tests/test_obd_vectors.py` the decoder if it is new. Vectors are CC BY-SA 4.0 like the
other fixtures (`REUSE.toml`).
