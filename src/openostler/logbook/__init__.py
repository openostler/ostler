# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Session logbook (ADR-0009): always-on recording, the session store and exports.
Core layer: never imports ``web``.

Contract (specs/2026-10-05-session-logbook-design.md):

* ``recorder.SessionRecorder(root, clock=time.time, mono=time.monotonic)``:
  ``feed(snapshot: dict, gps: Fix | None)`` once per poll; ``close()`` on shutdown;
  ``status() -> {"session", "since", "rows"} | None`` (the snapshot ``recording`` field).
* ``store.SessionStore(root, demo_root=<pack demo>)``: ``list(public=False) -> [meta]``,
  ``meta(id, public=False)``, ``data(id, channels, max_points=2000)``, ``delete(id)``,
  ``export(id, fmt) -> (filename, content_type, bytes)``, ``rotate(min_free_bytes)``.
  ``public=True`` returns only synthetic sessions (raises KeyError otherwise).
* ``channels.export_name(name) -> str`` (AiM-style names) and ``channels.UNITS``.
* ``export.to_csv / to_vbo / to_gpx(rows, meta) -> str``.
* ``demo.DEMO_ROOT`` — the pack's committed synthetic session(s) (lazy), built by
  ``tools/make_demo_session.py``.
* Extensions: ``SessionRecorder(..., source=, synthetic=, poll_hz=, trust_clock=,
  min_free_bytes=, fsync=)``; ``SessionStore.data/export/rows(..., public=False)``;
  ``delete`` raises ``PermissionError`` for demo/synthetic/live sessions and ``KeyError``
  for unknown ids; ``recorder.rotate_sessions(root, min_free_bytes)``;
  ``synth.generate(root)`` builds the demo session.
* ADR-0010 (specs/2026-10-05-replay-notes-capture-design.md): ``SessionRecorder.event(type,
  **fields)``, ``note(...)``, ``start()``, ``split()``, ``feed_accel(samples, source,
  session=None)``, ``set_accel_cal(matrix, source, method)``, ``audio_put(...)``,
  ``audio_stop(track)``, ``set_pi_audio(PiAudio | None)``; ``SessionStore.events / notes /
  add_note / edit_note / delete_note / audio_path / captures`` and ``export(id, "notes")``;
  ``notes.NoteLog``, ``audio.AudioTrackWriter``/``PiAudio``, ``motion.to_vehicle``/
  ``level_matrix``/``GpsAccel``. ``store.data`` also returns ``text: {faults, module}``.
* ADR-0011 (specs/2026-10-06-logs-at-scale-design.md): sessions open only while connected
  and pause (no rows) while disconnected; ``status()`` adds ``state: "recording" |
  "paused"``; ``note()``/``split()`` raise ``recorder.NotRecording`` (a ``RuntimeError``)
  unless recording; ``SessionRecorder(..., on_change=callable(sid))``.
  ``SessionStore(root, demo_root, index_path=None)``: ``update_meta(id, name=, description=,
  public=False)``, ``set_place(id, "start"|"end", label, source="osm")``,
  ``ensure_places(id)``, ``sync(id)``, ``index`` (``index.SessionIndex``: ``page``,
  ``histogram``, ``sync``, ``remove``, ``rebuild``, ``reconcile``). Meta gains
  ``description``, ``place_start``/``place_end``/``place`` (``places.py``) and a computed
  ``note_count``. ``synth.generate(root) -> [id]`` builds "Demo log 1" and "Demo log 2".
* U0 (specs/2026-10-06-u0-seams-design.md): ``vehicle.ensure_vehicle(state_dir)`` and
  ``vehicle.local_vid(state_dir)`` (``logs/vehicle.json``, ``OSTLER_VEHICLE_ID``);
  ``SessionRecorder(..., vid=None, state_dir=None)`` stamps ``vid`` into every new
  non-synthetic session; ``SessionStore(..., vid=None, state_dir=None)`` reads a session
  without one as the local vid; the index (schema 3) has a ``vid`` column.
"""
