"""GPS input (ADR-0009): NMEA parsing and fix sources. Core layer: never imports ``web``.

Contract (specs/2026-10-05-session-logbook-design.md, "GPS"):

* ``nmea.parse(line) -> dict | None`` — one checksum-validated RMC/GGA/VTG sentence
  (any talker) → partial fix fields; ``nmea.FixMerger`` merges them into a ``Fix``.
* ``reader.GpsReader(port="auto", baud=115200)`` / ``reader.MockGps(route)`` /
  ``reader.ReplayGps(path)`` — all expose ``start()``, ``stop()``, ``latest() -> Fix | None``
  and ``src`` ("usb" | "mock" | "replay"). ``reader.open_gps(spec)`` builds one from a
  ``--gps`` value (auto | none | mock | <path>) and returns None for "none".
* ``Fix`` fields: utc_ms, lat, lon, speed_kmh, heading, alt_m, sats, hdop, fix (bool),
  mono (time.monotonic() when received). ``Fix.snapshot()`` → the snapshot ``gps`` dict.
"""
