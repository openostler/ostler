---
title: Architecture and key seams
area: docs
status: stable
version: 1.1
updated: 2026-10-01
depends_on: [SCOPE.md, CONSTITUTION.md]
summary: >
  Developer map of the code: the bottom-up protocol stack, the seams to understand before
  changing things (frame formats, EcuSession, signal store, DataSource boundary, the two
  command paths) and the dev commands.
---

# Architecture and key seams

The boundary and mission are in [SCOPE.md](../SCOPE.md). The rules that must not be
broken are in [CONSTITUTION.md](../CONSTITUTION.md). This page is the working map.

## Commands

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"          # only runtime dep is pyserial

pytest -q                        # whole suite, no hardware needed
pytest tests/test_slabs.py -q    # one file
pytest tests/test_web.py -k slabs_empty_read_grace -q   # one test

# Dashboard: mock (no car) / live (ignition on, stationary)
PYTHONPATH=src python3 tools/dashboard.py --mock
PYTHONPATH=src python3 tools/dashboard.py --serial /dev/cu.usbserial-XXXX [--slabs] [--fault-watch] [--csv]

# Read-only sanity check against a module
PYTHONPATH=src python3 tools/verify_ecu.py td5|slabs /dev/cu.usbserial-XXXX
```

`pyproject.toml` sets `pythonpath = ["src", "."]`, so `pytest` works without
`PYTHONPATH`; the `tools/*.py` scripts need it (or an editable install). There is no
linter or formatter config, so match the surrounding style.

## The stack

It is strictly bottom-up. No layer knows anything about the layer below it beyond that
layer's interface, and each layer is unit-tested in isolation.

```
Transport      transport/base.py: raw bytes in/out (SerialTransport, LoggingTransport)
K-Line         kline/frame.py (encode/decode) + kline/kline.py (fast/slow init, echo, retries)
KWP2000        kwp2000/: service IDs, negative responses (0x7F+NRC), responsePending (0x78)
EcuSession     session.py: shared lifecycle/keepalive/read_block + tolerant establish retry
Module layer   td5/ slabs/ airbag/ (+ bcu/ ace/ autobox/ menu stubs)
Web            web/: stdlib HTTP + SSE server, dashboard UI
```

## Key seams

- **Two frame formats.**
  - Addressed framing (`0x8n`, target+source) is used only for StartCommunication and
    fast init.
  - After that, the whole session uses unaddressed length-prefixed frames
    (`<len> <SID> … <cs>`). `kline.read_frame` sniffs the format byte.
  - Airbag is the exception: it uses addressed framing throughout at 0x5B.
- **`EcuSession` is where module layers share behaviour.**
  - Subclasses set `name` and call `_establish(after=…)`.
  - Td5 passes `after=self.connect` (StartDiagnosticSession + SecurityAccess seed→key).
  - SLABS passes `after=None`, because its services work right after fast init. It also
    sets `_keepalive_sub = None` so it gets a bare `3E`.
- **`EcuSession.read_block(lids) -> {lid_hex: bytes}`** has exactly the shape
  `sniff/automap.py` consumes. That lets a live session feed the differential mapper.
- **Signal store (`src/d2diag/signals/*.json`).**
  - Decoders, the dashboard and automap all read it.
  - Confirmed mappings are written back with `upsert_field`.
  - Each field carries `confidence`, either `proven` or `candidate`.
- **`web/sources.py` is the protocol/UI boundary.**
  - Each `DataSource.poll()` returns `{status, signals, faults}`.
  - Mock and live sources are interchangeable at runtime.
  - Adding a module to the dashboard means adding a source pair, not touching the server.
- **Two command paths in `web/server.py`.**
  - `_INLINE_COMMANDS` (CSV start/stop, fault-watch) run on the HTTP thread.
  - Everything that touches the K-line is queued for the poll thread. Queued commands can
    wait out a ~20 s reconnect, which is longer than the 8 s HTTP timeout.
- **`faultscan.py`** reads every module strictly in sequence: establish → read → release.
- **`web/docs.py`** serves the canonical markdown fresh on every request, with the
  frontmatter stripped. It is a window on the source. Never cache or duplicate it.
- **`server/endpoint.py`** is the separate community-contribution service (stdlib +
  sqlite3), paired with `community/`. Both are whitelist-based and PII-free.

## Why the protocol rules exist

- **SLABS load.** Block-reading many LIDs every 0.5 s killed the SLABS session after
  ~15 s ([references/slabs/overview.md](../references/slabs/overview.md)).
- **What `7F 81 10` means.** A generalReject on StartCommunication means a link is still
  open on the shared bus. There are two teardowns:
  - `20` StopDiagnosticSession ends a Td5 diagnostic session.
  - `82` StopCommunication ends the link that fast init created.
- **The link outlives the process.** This was proven in the car on 2026-08-18.

## Conventions

- **Fakes.** `tests/fakes.py::FakeKLineEcu` is a half-duplex ECU simulator at the
  transport level: it echoes frames like the real bus. A response can be:
  - static bytes,
  - a sequence,
  - a `callable(count)`, when a test needs different values between reads.
- **Comments explain *why*.** Say which sniff or log a protocol fact came from. When you
  learn something from the car or a capture, record it in the relevant
  `references/*.md` alongside the code change.
- **`references/test_plan.md` is the living test backlog.** Every open hardware question
  goes there, with a procedure and a decision rule written before the test. When a result
  arrives:
  - route it to its permanent home (the signal store, `references/`, or the sister
    project for the car's own faults),
  - move the item to **Resolved** with the date and outcome.
- **`TODO.md`** is code and infrastructure only.

## Changelog

- 2026-09-30 — Extracted from the former root CLAUDE.md during Vibes as Code adoption.
- 2026-10-01 — Confidence vocabulary is now `proven`/`candidate` (ADR-0006).
