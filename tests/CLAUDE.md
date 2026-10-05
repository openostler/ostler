# tests/

The hardware-free pytest suite. Run it with `pytest -q` from the repo root.

## Files

- `fakes.py` — `FakeKLineEcu`, a half-duplex ECU simulator at the transport level.
- `fake_sources.py` — simulated dashboard sources (`FakeTd5Source`, `FakeSlabsSource`,
  `FakeInfoSource`, fake GPS and fault scan). Test scaffolding only: the product has no
  demo mode (ADR-0011).
- `e2e_server.py` — a dashboard on those fakes for Playwright and UI dev without a car
  (`python3 tests/e2e_server.py --port 8765`). Never deployed.
- `test_layering.py` — AST guards: the core never imports `web`; the platform never imports a
  vehicle pack or names a module id (ADR-0013).
- `fake_pack.py` (`FAKE_PACK`) + `test_pack.py`, `test_platform_fake_pack.py` — the platform
  run against a fake vehicle pack. `phase0_golden.py` + `test_phase0_golden.py` — the
  Phase 0 no-behaviour-change golden.
- `test_<area>.py` — one file per package or area (kline, kwp2000, td5, slabs, web, …).

## Editing rules

- No test may need hardware or the network.
- Prefer a `FakeKLineEcu` response sequence or `callable(count)` over mocking internals.
- Do not hard-code the test count in docs. CI is the source.
