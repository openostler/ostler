# tests/

The hardware-free pytest suite. Run it with `pytest -q` from the repo root.

## Files

- `conftest.py` — the Discovery 2 pack as an optional test dependency: modules and tests
  marked `needs_pack` skip (with an install hint) when `d2diag` is not installed;
  `OSTLER_REQUIRE_PACK=1` (CI) makes a missing pack an error. Tests in modules marked
  `fake_pack` run with `FAKE_PACK` active unless also marked `needs_pack`.
- `fakes.py` — `FakeKLineEcu`, a half-duplex ECU simulator at the transport level.
- `fake_pack.py` (`FAKE_PACK`) + `test_pack.py`, `test_platform_fake_pack.py` — the platform
  run against a fake vehicle pack (no D2 data).
- `fake_sources.py` — simulated dashboard sources on the D2 pack (`FakeTd5Source`,
  `FakeSlabsSource`, `FakeInfoSource`, fake GPS and fault scan). Test scaffolding only: the
  product has no demo mode (ADR-0011).
- `e2e_server.py` — a dashboard on those fakes for Playwright and UI dev without a car
  (`python3 tests/e2e_server.py --port 8765`). Needs the D2 pack. Never deployed.
- `test_layering.py` — AST guards: the core never imports `web`; the platform never imports a
  vehicle pack or names a module id (ADR-0013, ADR-0015).
- `obd_fakes.py` — scripted J1979 cars (two-ECU CAN, petrol K-line) on
  `openostler.testing.FakeObdLink`, and `make_vin()`: no VIN literal sits in the tree.
- `vectors/j1979/` — shared J1979 test vectors (bytes in → decoded out, plus Mode 04 gate
  cases) for the Python layer and the future C port; the format is in its `README.md`.
  `fixtures/j1979/` holds the J1979 PID table and the golden `SupportReport`s.
- `test_<area>.py` — one file per package or area. Pure D2 unit tests (td5, slabs, bcu,
  airbag, keygen, faults, importers, generators, the Phase 0 golden) live in the pack repo.

## Editing rules

- No test may need hardware or the network.
- Prefer `FAKE_PACK` for platform logic; mark a test `needs_pack` only when it exercises
  D2 data or code.
- Prefer a `FakeKLineEcu` response sequence or `callable(count)` over mocking internals.
- Do not hard-code the test count in docs. CI is the source.
