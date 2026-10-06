---
title: "ADR-0010 — Read-only whole-app replay; notes, audio and motion capture"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0008-unified-status-vocabulary.md]
summary: >
  Sessions also record an events stream so the whole UI can be replayed read-only; notes (live ⚑ and retrospective, Grafana/Foxglove-style points or ranges with tags) live per session and absorb Capture labels; cabin audio (phone or Pi) and acceleration (phone, Pi IMU or GPS-derived) are opt-in, stay on the device and are never public; satellite imagery is Esri World Imagery with attribution, swappable.
---

# ADR-0010 — Read-only whole-app replay; notes, audio and motion capture

> **Amended by [ADR-0036](adr-0036-vin-and-identity-data-in-recordings.md) and [ADR-0032](adr-0032-one-node-optional-brain.md), 2026-10-06:** "Identity reads never store their values" becomes "never recorded by default; never leaves the device" (ADR-0036); recordings keep raw bytes alongside decoded values and replay follows the recorded vehicle's pack (ADR-0032).

- **Date:** 2026-10-05
- **Status:** accepted (extends ADR-0009)

## Context

Owners want to replay a drive across every page, mark moments while driving, hear what happened, and log acceleration. Our research found:
- Grafana and Foxglove model annotations as points or ranges with text and tags, shown on a global timeline.
- VBOX logs a one-tap event marker as a data column.
- Browsers allow the microphone (MediaRecorder) and the motion sensors (DeviceMotion; iOS needs `requestPermission` from a tap) only on HTTPS, and only while the page is visible.
- AiM names acceleration channels InlineAcc/LateralAcc/VerticalAcc, in g.
- Esri World Imagery is free with attribution, but its terms for non-Esri clients are unclear.
- USGS imagery is public domain but covers the US only.

## Decision

- **Replay is read-only.** Replay is rebuilt from the recorded `data.csv` and `events.jsonl`. While a session is open, nothing is sent to a car. Every action is refused client-side, and a banner with **Exit to live** is always visible.
- **Events are recorded without payloads.** Commands are logged as action plus outcome only. Identity reads never store their values.
- **Notes belong to a session.** Each session keeps an append-only revision log. Capture labels become notes with a value, and the Decode solver reads them.
- **Audio and acceleration are opt-in per device.**
  - Audio stays on the device: it is never served in public mode and never uploaded.
  - Raw acceleration is stored together with the calibration matrix, so a session can be re-calibrated later.
  - Lateral is positive for a left turn (MoTeC/ISO).
- **HTTPS on the Pi.** The Pi gains `--tls-cert/--tls-key` (stdlib `ssl`), because the phone mic and motion sensors need HTTPS.
- **Satellite imagery** comes from Esri World Imagery with its full attribution, for personal, non-commercial use. US sessions use the USGS layer. The URL can be configured.

## Consequences

- New per-session files: `events.jsonl`, `notes.jsonl`, `audio-*.{webm,m4a,wav}`.
- New snapshot field `recording_sources`.
- New routes for events, notes, audio, acceleration, calibration and captures.
- The UI moves playback to the app root.
- Pi audio needs `arecord`, and the Pi IMU needs an LSM6DS-family part. Both stay candidate until a car test passes (T-32).

## Alternatives considered

- **Record full snapshots as JSON every poll.** Rejected: about 10× the size of events plus columns, and the information is redundant.
- **A paid or keyed satellite provider by default.** Rejected: owners shouldn't need an account. The provider can be swapped by configuration.
- **BNO055/085 IMUs.** Rejected: they need I2C clock stretching, which the Pi handles badly.

## Amendments (2026-10-06)

Recorded with the node/brain direction
([ADR-0032](adr-0032-one-node-optional-brain.md)); the decision above otherwise stands.

- **Whole-app replay is kept**, read-only, as decided above.
- **Replay across vehicles.** Replaying another vehicle's session switches the UI to that
  session's vehicle pack and capability manifest, and switches back on exit; the active
  vehicle and its live link are untouched
  ([UI spec §4.1](../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher)).
- **Sessions record the pack id, the pack version and the manifest `etag`**, so a replay
  renders with what was recorded.
- **Logs replay also covers parked periods and alarm events**, not only drives.
- **Identity data** follows [ADR-0036](adr-0036-vin-and-identity-data-in-recordings.md):
  recording identity replies is an opt-in, off by default; when off they are scrubbed at
  write and every other raw byte is kept; when on they still never leave the device.
- **"HTTPS on the Pi" means HTTPS on the brain.** Wherever this ADR says "the Pi" as a
  host (HTTPS, cabin audio, the IMU), read "the brain". The IMU may instead be on the
  guardian variant of the node (ADR-0032), whose readings arrive as source-tagged VSS
  signals in the same session.
