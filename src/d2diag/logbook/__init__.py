"""Session logbook (ADR-0009): always-on recording, the session store and exports.
Core layer: never imports ``web``.

Contract (specs/2026-10-05-session-logbook-design.md):

* ``recorder.SessionRecorder(root, clock=time.time, mono=time.monotonic)``:
  ``feed(snapshot: dict, gps: Fix | None)`` once per poll; ``close()`` on shutdown;
  ``status() -> {"session", "since", "rows"} | None`` (the snapshot ``recording`` field).
* ``store.SessionStore(root, demo_root=DEMO_ROOT)``: ``list(public=False) -> [meta]``,
  ``meta(id, public=False)``, ``data(id, channels, max_points=2000)``, ``delete(id)``,
  ``export(id, fmt) -> (filename, content_type, bytes)``, ``rotate(min_free_bytes)``.
  ``public=True`` returns only synthetic sessions (raises KeyError otherwise).
* ``channels.export_name(name) -> str`` (AiM-style names) and ``channels.UNITS``.
* ``export.to_csv / to_vbo / to_gpx(rows, meta) -> str``.
* ``demo.DEMO_ROOT`` — the committed synthetic session(s), built by
  ``tools/make_demo_session.py``.
* Extensions: ``SessionRecorder(..., source=, synthetic=, poll_hz=, trust_clock=,
  min_free_bytes=, fsync=)``; ``SessionStore.data/export/rows(..., public=False)``;
  ``delete`` raises ``PermissionError`` for demo/synthetic/live sessions and ``KeyError``
  for unknown ids; ``recorder.rotate_sessions(root, min_free_bytes)``;
  ``synth.generate(root)`` builds the demo session.
"""
