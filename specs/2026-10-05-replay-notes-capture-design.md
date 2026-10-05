---
title: "Whole-app replay, notes, audio and accelerometer recording, replay map v2, Decode/Label admin — design"
area: specs
status: stable
version: 1.0
updated: 2026-10-05
depends_on: [specs/2026-10-05-session-logbook-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md]
summary: >
  Sessions record an events stream so every page can be replayed read-only from a root-level replay context with a global transport and Exit to live; live (⚑) and retrospective notes on the timeline (Capture labels become notes); opt-in phone/Pi audio and phone/Pi/GPS accelerometer from a recording-options modal; replay map gains two side-by-side traces, CVD-safe high-contrast ramps, a satellite switcher and a tiered channel picker; admin Map/Capture become Decode/Label with plain-English steps.
---

# Whole-app replay, notes, audio and accelerometer — design

## Context

The owner approved this on 2026-10-05. The research (Grafana/Foxglove annotations, VBOX event markers, MediaRecorder and DeviceMotion constraints, AiM/MoTeC acceleration conventions, MapLibre `line-offset`, Esri/USGS imagery terms) is summarised in ADR-0010.

## 1. The events stream

Each session gets `events.jsonl` next to `data.csv`.
- It is append-only.
- It is synced with the data (fsync at most once per second).
- One JSON object per line: `{"t": <session ms>, "type": <str>, ...}`.

| type | fields | when |
|---|---|---|
| `state` | `conn, status, module, mode, active_test, fault_watch, logging` | first line of every part |
| `conn` | `conn` | it changes |
| `status` | `status` | it changes |
| `connect_phase` | `phase` | it changes |
| `module` | `module` | it changes |
| `mode` | `mode` | it changes |
| `active_test` | `active_test` (object or null) | it changes |
| `command` | `action, ok, message?, error?` | every module command and inline command |
| `fault_watch` | `on` | it changes |
| `logging` | `recording, file?` | it changes |
| `error` | `error` | it changes |
| `audio` | `track, state: start\|stop\|lost, source` | audio track events |
| `accel_cal` | `matrix: 3×3, source, method` | each calibration |

**Rules:**
- `command` never stores params or identity payloads. For `read_identity` it records only `{action, ok}`, so the VIN never lands in a session (tested).
- `trust` is stripped from everything.

**`meta.channels[]`** gains:
- `c`: `proven` or `candidate` from the signal store, or `null` for GPS and acceleration.
- `limits`: `[lo, hi]` or `null`.
- `group`: as served by `/fields`. GPS channels use `gps`; acceleration channels use `accel`.

A session continues across a module switch. The `module` column and the `module` event change at that moment.

**API:** `GET /sessions/<id>/events` returns `{"id", "events": [...]}`. It uses the same public filter as the other session routes.

## 2. Notes

Each session gets `notes.jsonl`.
- It is a revision log: every line is a full note or `{"id", "deleted": true}`, and the last line for an id wins.
- **Note fields:**
  - `id`: 8 hex digits.
  - `t` and `t_end`: session ms. `t_end` is optional and makes the note a range.
  - `text` and `tags[]`.
  - `kind`: `mark`, `note` or `capture`.
  - `source`: `live` or `retro`.
  - `created`: UTC ISO, plus `edited` when changed.
  - `capture` (only on capture notes): `{module, lid, raw, value}`.

**Routes.** All except `GET` are refused in public mode and on synthetic sessions.

| Route | Returns |
|---|---|
| `GET /sessions/<id>/notes` | `{"id", "notes": [...]}`, sorted by `t` |
| `POST /sessions/<id>/notes` with `{t, t_end?, text, tags?, kind?}` | the note (`source: retro` unless given) |
| `PATCH /sessions/<id>/notes/<nid>` with any of `text, tags, t, t_end` | the note |
| `DELETE /sessions/<id>/notes/<nid>` | `{ok}` |
| `POST /notes/live` with `{text?, tags?, kind: "mark"\|"note"\|"capture", capture?}` | the note, stamped "now" in the recording session; if nothing is recording, a session is started first |

**`GET /captures?module=`** (admin) returns the server-side capture labels, from the capture notes and `logs/labeled_captures.jsonl`: `{"captures": [{module, lid, raw, value, t?, session?}]}`.

**Exports:**
- **CSV:** an `event` column holds the note id on the row nearest each note. Notes also export separately as `?fmt=notes` (CSV).
- **VBO:** notes go in the `[comments]` lines, plus an `event1` column.
- **GPX:** one `<wpt>` per note, when GPS is present.

## 3. Audio and accelerometer capture

**Recording options** are kept per device in the browser.
- **Server-side sources** (Pi audio, IMU) are switched with `POST /command {"action": "recording_options", "params": {"audio": "off|pi", "imu": "off|on", "accel_hz": 10|25|50}}`. The command answers `{ok, options}`.
- The snapshot gains **`recording_sources`**:
  - `gps`: `usb`, `mock` or `none`;
  - `pi_audio`: `available` or `unavailable` (with a `reason`) or `on`;
  - `imu`: `available`, `unavailable` or `on`;
  - `accel_hz`.

**Phone audio:**
- `POST /sessions/<id>/audio?track=<uuid>&seq=<n>&mime=<type>&start=<epoch ms, on seq 0>`, with the raw chunk bytes as the body.
- The server appends chunks in `seq` order to `audio-<track>.<ext>`. An out-of-order chunk is held until its predecessor arrives, up to 10 chunks.
- The track is registered in `meta.audio[]` as `{track, mime, start_ms, end_ms?, source: "phone"|"pi", bytes}`.
- `GET /sessions/<id>/audio/<track>` serves the track with HTTP Range support.
- Audio is never served in public mode.

**Pi audio:**
- `--audio pi` starts `arecord -q -f S16_LE -r 16000 -c 1 <dir>/audio-<track>.wav` for the session and stops it at session end.
- If `arecord` is missing or fails, that is reported in `recording_sources` and nothing else breaks.

**Phone accelerometer:**
- `POST /sessions/<id>/accel` with `{"source": "phone", "samples": [[epoch_ms, ax, ay, az], ...]}`. Values are `accelerationIncludingGravity` in m/s².
- `POST /sessions/<id>/accel_cal` with `{matrix, source, method}` stores the calibration.
- The recorder writes `Acc_X/Y/Z` (raw, m/s²) and `InlineAcc`/`LateralAcc`/`VerticalAcc` (g) in the vehicle frame:
  - inline is positive when accelerating;
  - lateral is positive in a left turn;
  - vertical is positive upward, with gravity removed.
- Samples are written as sparse rows at their own timestamps (session ms = epoch − session start).

**Pi IMU:**
- `--imu auto|none|mock`. The `imu/` package drives an LSM6DSOX or LSM6DS3TR-C over `/dev/i2c-1` (addresses 0x6A/0x6B) with stdlib `fcntl` ioctl, at ±4 g and 104 Hz ODR, polled at `accel_hz`.
- Mock mode uses a deterministic synthetic IMU.

**GPS-derived acceleration:**
- `GPS_LonAcc` = Δspeed/Δt and `GPS_LatAcc` = v·Δheading/Δt, both in g and smoothed.
- Always computed when GPS is present.

## 4. Whole-app replay (UI)

**`ui/src/state/replay.tsx`** exports `ReplayProvider`, `useReplay()` and `ReplayState`. `useReplay()` returns:

```
{active, session?: SessionMeta, data?: SessionData, events: SessionEvent[], notes: Note[],
 t, playing, speed, enter(id), exit(), seek(t), play(), pause(), setSpeed(n),
 addNote(...), refreshNotes()}
```

- It is mounted at the root of `App.tsx`.
- Opening a session in Logs calls `enter(id)`.
- `exit()` returns to live.

**`useApp()` in replay** returns a synthesised `snap` and `live`, built at `t`:
- **Signals:** `v` from the session data, `u` and `c` from `meta.channels`, `s` recomputed from `limits`.
- **Faults:** split from the `faults` column.
- **State:** the event state at `t` gives `module`, `status`/`conn`, `active_test`, `logging`, `fault_watch` and `battery_v`. `gps` comes from the GPS channels.
- **`live`:** rebuilt from the 60 samples before `t`.
- **Module:** the module in view follows the recorded module; the live connection is never touched.

**Read-only in replay:**
- `useAction` returns `{ok: false, error: "Replay — read only"}` without sending anything.
- ActionButton and Faults "Clear" show a lock and the word "replay".
- **Outputs** highlights the item whose action matches `active_test` at `t`, and shows the last `command` event for each item: "ran at HH:MM:SS ✓/✗".
- **Settings** shows only "identity read at HH:MM:SS".

**Clearly replay:**
- An amber `ReplayBanner` replaces the experimental strip: "REPLAY · <date time> · ⏱ <cursor clock> · [Exit to live]". It shows a note chip as the cursor passes a note.
- The header connection pill reads "Replay".
- `main` gets an amber edge.
- The connection notice and the automatic connection sheet are suppressed.

**Global transport:** a bottom bar above the nav on every tab while in replay. It has play/pause, ±10 s, 1–8× and a scrubber with note ticks.

## 5. Recording UI, notes UI and the replay map

**Logs recording card:**
- status: duration, modules, sources;
- ⚑ Mark, Note…, ⚙ Options (the modal: sources, accelerometer rate, Calibrate, session name), and "Split".
- The Options apply tap also asks for the iOS motion and mic permissions and the wake lock.
- A source that can't be used is greyed out with its reason, for example "Needs HTTPS — see the HTTPS guide".

**Header ⚑ (every page, while recording):**
1. One tap posts a `mark` straight away.
2. A sheet asks "What happened?", with text and quick tags (issue, fault, noise, driving, test).
3. Saving PATCHes the mark with what was entered.

**Replay notes:**
- "Add note at cursor"; dragging on the chart makes a range note.
- Tapping a marker opens an editor.
- A notes list jumps to the note.
- Markers appear on the scrubber, and as lines or bands on the chart.

**Map:**
- **Traces:**
  - Trace A, plus an optional trace B drawn as a parallel lane (`line-offset` ±3 px, after a ~1 m Douglas-Peucker smooth, round joins).
  - A uses plasma; B uses mako. Each has 20 buckets, trimmed so neither end is near black, plus a casing (white on streets, dark on satellite).
  - "Classic" turbo is an option.
- **Basemap switcher:** Streets / Satellite / Hybrid.
  - The raster satellite layer is toggled with `visibility`, so the trace layers survive.
  - The default source is Esri World Imagery, with its required attribution.
  - The USGS Imagery Only layer is used automatically inside the US bbox.
  - The source URL can be overridden with `localStorage d2diag.satUrl`.
- **G-G panel:** lateral vs inline scatter with 0.5 g rings, coloured by speed. It appears when acceleration channels exist.

**`ChannelPicker`:** a bottom sheet for each chart lane and for traces A and B.
- Pinned and recent chips (default pins: speed, rpm, accelerator pedal, LateralAcc).
- Search over label, unit and name.
- Collapsible categories by `group` (GPS/Motion, Engine, Fuelling, Temperatures, Electrical, Switches, Chassis/SLABS, Accelerometer, Other).
- A pin toggle on each row.

## 6. Admin: Decode and Label

**Tab names:**
- The Map tab becomes **Decode** ("match our values to the NanoCom").
- Capture becomes **Label**.

Each tab gets a three-step header and a glossary popover explaining LID, `21 xx`, reference tool and sniff tap.

**Label:**
- **Save** writes the capture to `/capture` (as today), and also to `POST /notes/live` with `kind: "capture"`.
- "Read a LID directly" works in mock mode. Mock `read_block` builds the blocks from the mock signals.
- The Utilities → Advanced dump links to Label.

**Decode:**
- Its solver merges `GET /captures` with its local readings.
- With no feed, the badge reads "No tap connected" and suggests the demo feed.

**Homelab:** the compose runs with `--replay` on the committed demo sniff log.

All errors are in English.

## Testing

- **pytest:**
  - events: state line, on-change only, command without params, no VIN;
  - a module switch keeps the session;
  - notes: revisions, delete, live note starts a session, refused in public mode and on synthetic sessions;
  - audio: chunk ordering, Range requests, never served publicly;
  - accel: ingestion, rotation, sign conventions, GPS-derived acceleration;
  - IMU: driver against a fake fd, and the mock;
  - exports: event column, VBO comments, GPX waypoints;
  - mock `read_block`;
  - `/captures` merge;
  - `recording_options`;
  - TLS flag smoke test.
- **vitest:**
  - snap synthesis at `t` (signals, faults, module switch, active_test);
  - read-only actions;
  - banner and Exit;
  - global transport on another tab;
  - notes CRUD UI;
  - ⚑ flow;
  - options modal (unavailable reasons);
  - motion calibration maths;
  - audio chunker with fake MediaRecorder;
  - ramps (end-contrast check);
  - picker grouping and search;
  - Decode/Label help.
- **Playwright:**
  - open the demo → Drive shows replay values → switch to Outputs (highlight) → Exit to live;
  - ⚑ mark;
  - retro note;
  - satellite toggle;
  - trace B;
  - picker;
  - Decode help.

## Changelog

- 2026-10-05: v1.0, approved.
