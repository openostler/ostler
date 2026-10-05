"""Session audio (ADR-0010; spec §3). Core: never imports web.

Contract:
* ``AudioTrackWriter(session_dir, track, mime, start_ms, source="phone")``:
  ``put(seq, data: bytes)`` appends chunks in seq order (holds up to 10 early chunks),
  ``close()``; files ``audio-<track>.<ext>`` (webm | m4a | wav).
* ``PiAudio(arecord="arecord")``: ``available() -> (bool, reason)``, ``start(session_dir) ->
  track | None``, ``stop()`` — runs ``arecord -q -f S16_LE -r 16000 -c 1`` as a subprocess.
* Tracks are registered in ``meta.audio[]``: ``{track, mime, start_ms, end_ms, source, bytes}``.
"""
