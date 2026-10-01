# tests/

The hardware-free pytest suite. Run it with `pytest -q` from the repo root.

## Files

- `fakes.py` — `FakeKLineEcu`, a half-duplex ECU simulator at the transport level.
- `test_layering.py` — AST guard: the core never imports `web`.
- `test_<area>.py` — one file per package or area (kline, kwp2000, td5, slabs, web, …).

## Editing rules

- No test may need hardware or the network.
- Prefer a `FakeKLineEcu` response sequence or `callable(count)` over mocking internals.
- Do not hard-code the test count in docs. CI is the source.
