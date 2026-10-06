# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Always-on session recording (ADR-0009, specs/2026-10-05-session-logbook-design.md).

``SessionRecorder.feed(snapshot, gps)`` is called once per poll. A session opens only
when the car is connected (``conn == "connected"``, or ``status == "connected"`` when
``conn`` is absent); GPS movement never opens one (ADR-0011). While the car is
disconnected the open session is **paused**: no data rows are written (not even GPS),
state events are still logged, and it ends after ``IDLE_S`` without a connected poll, or
on ``close()``. ``status()["state"]`` is ``"recording"`` or ``"paused"``; ``note()`` and
``split()`` raise ``NotRecording`` unless recording. On close the offline place names
(``place_start``/``place_end``/``place``) are written to the meta, and the optional
``on_change(session_id)`` callback runs after a session opens, closes, is renamed or
gets a live note (the server wires it to ``SessionStore.sync``). Each session is a directory ``<root>/<id>/`` with RaceCapture-style CSV parts
and an atomically rewritten ``meta.json``. Only ``signals``, ``faults``, ``module``, GPS
and acceleration are recorded — never the VIN or any identity read.

ADR-0010 additions (specs/2026-10-05-replay-notes-capture-design.md):

* ``events.jsonl``: ``event(type, **fields)``; ``feed()`` derives the state-ish events
  (conn, status, connect_phase, module, mode, active_test, fault_watch, logging, error)
  from the snapshot, on change only, and writes a ``state`` line at the start of every
  part. ``command`` events keep only ``action, ok, message?, error?`` (never params; for
  identity reads only ``action, ok``).
* Notes: ``note(...)`` stamps a live note "now" in the recording session.
* Acceleration: ``feed_accel(samples, source)`` and ``set_accel_cal(matrix, source,
  method)``; ``GPS_LonAcc``/``GPS_LatAcc`` from every GPS fix.
* Audio: ``audio_put(...)``/``audio_stop(...)`` for phone chunks, ``set_pi_audio(PiAudio)``
  for the Pi's microphone; tracks are listed in ``meta.audio``.

U0 (specs/2026-10-06-u0-seams-design.md): every new non-synthetic session's ``meta.json``
carries ``vid``, the vehicle id from ``vid=``, ``OSTLER_VEHICLE_ID`` or
``<state_dir>/vehicle.json`` (``logbook/vehicle.py``).

Node sessions (NodeSource spec §7, P2; the rules are in ``logbook/node.py``): a snapshot
with ``source_kind: "node"`` opens a session only with the node online, awake or held and a
live value; ``status: asleep`` ends it at once (``end_reason: node_asleep``); stale values
are never written; ``vss`` readings add ``<path>`` and ``<path>@<device>`` columns; ``Utc``
follows the node's synced clock. ``tap_message()`` (called from the MQTT thread) writes
the raw tap beside the CSV (``logbook/tap.py``). Their ``meta.json`` adds ``source:
"node"``, ``devices``, ``device_info`` (each device's firmware and manifest ``etag``, P3;
changes are ``node_manifest`` events), ``pack``, ``tap`` and ``end_reason``.
"""
from __future__ import annotations

import calendar
import csv
import io
import json
import math
import os
import re
import shutil
import threading
import time
from typing import Callable

from ..timefmt import rfc3339_utc
from . import channels as ch
from . import motion
from . import node as _node
from . import places as _places
from .audio import AudioTrackWriter
from .notes import NoteLog, read_notes
from .tap import TapRecorder, identity_recording_enabled
from .vehicle import local_vid, state_dir_for

IDLE_S = 300.0          # end after this long without a connected poll
FSYNC_S = 1.0           # fsync the data file at most this often
META_S = 30.0           # rewrite meta.json this often while recording
PART_S = 3600.0         # split parts hourly
GPS_MIN_S = 0.095       # GPS rows capped at 10 Hz
GPS_RATE_HZ = 10
DEFAULT_RATE_HZ = 2
MIN_FREE_BYTES = 200 * 1024 * 1024
JITTER_KMH = 1.0        # GPS segments slower than this don't add distance (stationary jitter)

# Signal names that would be identity reads: never recorded even if a source put one in.
_IDENTITY = re.compile(r"(^|_)(vin|eka|ident|identity|serial|part_?no|part_number)($|_)",
                       re.IGNORECASE)
_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z(-[0-9]+)?$")
# meta fields another writer (SessionStore.update_meta / set_place) may change while the
# session is still recording: the recorder adopts such external edits on its next write.
USER_KEYS = ("name", "description", "place_start", "place_end", "place")


class NotRecording(RuntimeError):
    """A live note or a split was asked for while no session is recording (none open,
    or the open one is paused because the car is disconnected)."""

    def __init__(self, msg: str = "Not recording — connect to the car first") -> None:
        super().__init__(msg)


# ---------------------------------------------------------------- helpers -- #

def fmt_num(v: float, dp: int = 6) -> str:
    """A plain decimal (no exponent, trailing zeros stripped)."""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    s = f"{v:.{dp}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def iso_utc(epoch_s: float) -> str:
    """Epoch seconds → ``2026-10-05T09:00:00.000Z``."""
    ms = int(round(epoch_s * 1000))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def header_cell(name: str, units: str, rate: int) -> str:
    return f'"{name}"|"{units}"|{rate}'


_CELL_RE = re.compile(r'"([^"]*)"\|"([^"]*)"\|([0-9.]+)')


def parse_header(line: str) -> "list[tuple[str, str, float]]":
    """A header row → ``[(name, units, rate_hz)]``."""
    return [(n, u, float(r)) for n, u, r in _CELL_RE.findall(line)]


def write_json_atomic(path: str, obj: dict) -> None:
    """Write JSON to a temp file in the same directory, fsync, then rename over ``path``."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def _read_meta(path: str) -> "dict | None":
    try:
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
        return m if isinstance(m, dict) else None
    except (OSError, ValueError):
        return None


def rotate_sessions(root: str, min_free_bytes: int = MIN_FREE_BYTES,
                    usage: Callable = shutil.disk_usage, keep=()) -> "list[str]":
    """Delete the oldest non-synthetic sessions under ``root`` until free space is at
    least ``min_free_bytes``. Sessions in ``keep`` (the one recording) are never deleted.
    Returns the deleted ids, oldest first."""
    deleted: "list[str]" = []
    if not os.path.isdir(root):
        return deleted
    ids = sorted(d for d in os.listdir(root) if _ID_RE.match(d) and d not in keep
                 and os.path.isdir(os.path.join(root, d)))
    for sid in ids:
        try:
            if usage(root).free >= min_free_bytes:
                break
        except OSError:
            break
        meta = _read_meta(os.path.join(root, sid, "meta.json")) or {}
        if meta.get("synthetic") or meta.get("source") == "demo":
            continue
        shutil.rmtree(os.path.join(root, sid), ignore_errors=True)
        deleted.append(sid)
    return deleted


def _num_value(v) -> "float | int | None":
    if isinstance(v, dict):
        v = v.get("v")
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)) and math.isfinite(v):
        return v
    return None



# ----------------------------------------------------------------- events -- #

# state-ish event type → the snapshot-derived key it de-duplicates on
STATE_TYPES = ("conn", "status", "connect_phase", "module", "mode", "active_test",
               "fault_watch", "logging", "error")
STATE_LINE = ("conn", "status", "module", "mode", "active_test", "fault_watch", "logging")
_EVENT_FIELD = {"connect_phase": "phase", "fault_watch": "on"}  # type → its field name
_STRIP = ("trust", "params", "param", "payload", "identity", "vin")
_IDENTITY_ACTION = re.compile(r"(ident|vin|eka|serial)", re.IGNORECASE)
_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
MAX_ACCEL_SAMPLES = 5000      # per feed_accel call
DEFAULT_ACCEL_HZ = 25
# Sources whose sensor is mounted in the vehicle frame (x forward, y left, z up) unless
# calibrated otherwise. A phone always needs a calibration before vehicle channels.
_ALIGNED_SOURCES = ("imu", "pi", "mock")


def _norm_active_test(v) -> "dict | None":
    if not isinstance(v, dict) or not v.get("action"):
        return None
    return {k: v[k] for k in ("action", "label", "stop") if v.get(k) is not None}


def _norm_logging(v) -> dict:
    if not isinstance(v, dict):
        return {"recording": False}
    out = {"recording": bool(v.get("recording"))}
    if out["recording"] and v.get("file"):
        out["file"] = os.path.basename(str(v["file"]))
    return out


def _canonical_module(mid):
    """A module id (or legacy alias) as the active vehicle pack's canonical id; anything
    that is not a non-empty string is returned unchanged."""
    if not isinstance(mid, str) or not mid:
        return mid
    from ..pack import canonical_module

    return canonical_module(mid) or mid


def derive_state(snap: dict) -> dict:
    """The event state carried by a snapshot (values as they appear in events)."""
    return {
        "conn": snap.get("conn"),
        "status": snap.get("status"),
        "connect_phase": snap.get("connect_phase"),
        "module": _canonical_module(snap.get("module")),
        "mode": snap.get("mode"),
        "active_test": _norm_active_test(snap.get("active_test")),
        "fault_watch": bool(snap.get("fault_watch")),
        "logging": _norm_logging(snap.get("logging")),
        "error": str(snap.get("error") or ""),
    }


def _event_value(etype: str, fields: dict):
    """The de-dup value of a state-ish event built from its fields."""
    if etype == "active_test":
        return _norm_active_test(fields.get("active_test"))
    if etype == "logging":
        return _norm_logging({"recording": fields.get("recording"), "file": fields.get("file")})
    if etype == "fault_watch":
        return bool(fields.get("on"))
    if etype == "error":
        return str(fields.get("error") or "")
    if etype == "module":
        return _canonical_module(fields.get("module"))
    return fields.get(_EVENT_FIELD.get(etype, etype))


def _event_fields(etype: str, value) -> dict:
    if etype == "logging":
        return dict(value)
    return {_EVENT_FIELD.get(etype, etype): value}


def clean_command(fields: dict) -> dict:
    """``command`` events keep ``action, ok, message?, error?`` only — never params — and an
    identity read keeps only ``action, ok`` (the VIN never lands in a session)."""
    action = str(fields.get("action") or "")
    out: dict = {"action": action, "ok": bool(fields.get("ok"))}
    if _IDENTITY_ACTION.search(action):
        return out
    for k in ("message", "error"):
        v = fields.get(k)
        if isinstance(v, str) and v:
            out[k] = v[:300]
    return out


# ---------------------------------------------------------------- session -- #

class _Session:
    def __init__(self, sid: str, path: str, start_s: float, start_m: float) -> None:
        self.id, self.dir = sid, path
        self.start_s, self.start_m = start_s, start_m
        self.parts: "list[str]" = []
        self.fh: "io.TextIOWrapper | None" = None
        self.columns: "list[str]" = []
        self.units: "dict[str, str]" = {}
        self.signals: "list[str]" = []
        self.extra: "list[str]" = []        # acceleration channels, once seen
        self.rows = 0
        self.accel_rows = 0
        self.part_start_m = start_m
        self.last_sync_m = -math.inf
        self.last_meta_m = start_m
        self.last_conn_m = start_m
        self.last_fix_mono: "float | None" = None
        self.last_gps_m = -math.inf
        self.utc_offset: "float | None" = None
        self.modules: "list[str]" = []
        self.has_gps = False
        self.dist_m = 0.0
        self.max_speed: "float | None" = None
        self.bbox: "list[float] | None" = None
        self.start_pos: "list[float] | None" = None
        self.end_pos: "list[float] | None" = None
        self.last_pt: "tuple[float, float] | None" = None
        self.end_s: "float | None" = None
        self.end_m: "float | None" = None
        # ADR-0010
        self.efh: "io.TextIOWrapper | None" = None
        self.events_dirty = False
        self.state: dict = {}
        self.gps_accel = motion.GpsAccel()
        self.accel_cal: "dict | None" = None
        self.writers: "dict[str, AudioTrackWriter]" = {}
        self.audio: "list[dict]" = []       # finished phone tracks and every Pi track
        self.pi_entry: "dict | None" = None
        # ADR-0011
        self.paused = False
        self.user: dict = {k: None for k in USER_KEYS}   # name, description, place*
        self.written: dict = {}                            # user fields last written
        self.vid: "str | None" = None                      # U0: the vehicle id
        # NodeSource P2
        self.node = False                                  # recorded from a node source
        self.tap: "TapRecorder | None" = None
        self.devices: "set[str]" = set()
        self.device_info: "dict[str, dict]" = {}         # NodeSource P3: {device: {fw, etag}}
        self.pack: "dict | None" = None
        self.end_reason: "str | None" = None
        self.clock_synced: "bool | None" = None

    @property
    def name(self) -> "str | None":
        return self.user.get("name")

    @name.setter
    def name(self, v: "str | None") -> None:
        self.user["name"] = v

    def ms(self, m: float) -> int:
        return int(round((m - self.start_m) * 1000.0))


class SessionRecorder:
    """Records every connected (or moving) period as a session under ``root``.

    ``clock`` (epoch s) and ``mono`` (monotonic s) are injectable for tests. Extra keyword
    arguments: ``source`` (default: the snapshot's ``mode``, else ``live``), ``synthetic``,
    ``poll_hz`` (header rate hint; otherwise estimated from the feed cadence, default 2),
    ``trust_clock`` (fill ``Utc`` from ``clock`` until a GPS fix gives time),
    ``min_free_bytes`` (rotation threshold; 0 disables), ``fsync`` (the function used
    for data-file syncs) and ``accel_hz`` (header rate of the acceleration channels).
    """

    def __init__(self, root: str, clock: Callable[[], float] = time.time,
                 mono: Callable[[], float] = time.monotonic, *, source: "str | None" = None,
                 synthetic: bool = False, poll_hz: "float | None" = None,
                 trust_clock: bool = True, min_free_bytes: int = MIN_FREE_BYTES,
                 fsync: Callable[[int], None] = os.fsync,
                 accel_hz: int = DEFAULT_ACCEL_HZ,
                 on_change: "Callable[[str], None] | None" = None,
                 vid: "str | None" = None, state_dir: "str | None" = None,
                 record_identity: "bool | None" = None) -> None:
        self.root = str(root)
        # ADR-0036: identity data in the raw tap is scrubbed unless the install-level option
        # (OSTLER_RECORD_IDENTITY, local configuration only) is on.
        self.record_identity = (identity_recording_enabled() if record_identity is None
                                else bool(record_identity))
        # U0: every new session carries the vehicle id. ``vid`` pins it (tests, tools);
        # otherwise it is resolved when a session opens from ``OSTLER_VEHICLE_ID`` or
        # ``<state_dir>/vehicle.json`` (default state dir: the parent of ``root``).
        # Synthetic sessions get one only when ``vid`` is given.
        self.vid = vid
        self.state_dir = state_dir or state_dir_for(self.root)
        self._clock, self._mono = clock, mono
        self.source, self.synthetic = source, synthetic
        self.poll_hz, self.trust_clock = poll_hz, trust_clock
        self.min_free_bytes = min_free_bytes
        self.accel_hz = accel_hz
        self._fsync = fsync
        self.fsyncs = 0
        self._lock = threading.RLock()
        self._s: "_Session | None" = None
        self._src: str = source or "live"
        self._last_feed_m: "float | None" = None
        self._dt_ema: "float | None" = None
        self._cal: "dict[str, dict]" = {}   # source → {matrix, source, method}
        self._pi = None                       # audio.PiAudio while Pi audio is on
        self.on_change = on_change
        self._recover()

    # ---- public ------------------------------------------------------- #

    def feed(self, snapshot: "dict | None", gps=None) -> None:
        """One poll: maybe open a session, record state changes, write a row, maybe end."""
        with self._lock:
            now, m = self._clock(), self._mono()
            self._note_cadence(m)
            snap = snapshot or {}
            conn = snap.get("conn")
            connected = (conn == "connected") if conn is not None else (
                snap.get("status") == "connected")
            fix = gps if (gps is not None and getattr(gps, "fix", False)
                          and gps.lat is not None and gps.lon is not None) else None
            s = self._s
            if s is None:
                if not connected:  # GPS movement never opens a session (ADR-0011)
                    return
                if _node.is_node(snap) and not _node.may_open(snap):
                    return  # a node: online, awake or held, and a live value (spec §7)
                s = self._open(now, m, snap)
            else:
                self._state_changes(s, m, snap)
                if s.node and _node.asleep(snap):  # a clean sleep ends it (owner answer 8)
                    self._end(s, now, m, reason="node_asleep")
                    return
            self._check_pi(s, m)
            s.paused = not connected
            if connected:
                s.last_conn_m = m
                self._row(s, now, m, snap, fix)
            if m - s.last_conn_m >= IDLE_S:
                self._end(s, now, m, reason="idle")
            elif m - s.last_meta_m >= META_S:
                self._write_meta(s, m)

    def close(self) -> None:
        """End the open session (server shutdown)."""
        with self._lock:
            if self._s is not None:
                self._end(self._s, self._clock(), self._mono(), reason="closed")

    def status(self) -> "dict | None":
        """The snapshot ``recording`` field: ``{session, since, since_utc, rows, state}`` or
        None; ``state`` is ``"recording"`` or ``"paused"`` (open but disconnected).
        ``since`` (epoch seconds) is deprecated for ``since_utc`` (RFC 3339 UTC ``Z``) and
        goes in 0.2.0 (specs/2026-10-06-api-consistency-design.md §4)."""
        s = self._s
        return None if s is None else {"session": s.id, "since": s.start_s,
                                       "since_utc": rfc3339_utc(s.start_s), "rows": s.rows,
                                       "state": "paused" if s.paused else "recording"}

    @property
    def recording(self) -> bool:
        """True while a session is open and not paused."""
        s = self._s
        return s is not None and not s.paused

    @property
    def session_id(self) -> "str | None":
        s = self._s
        return None if s is None else s.id

    def set_name(self, name: "str | None") -> None:
        """Name the session being recorded (meta ``name``); None clears it. With no session
        open, the name is kept for the next one."""
        with self._lock:
            sess = self._s
            if sess is None:
                self._next_name = name or None
                return
            self._adopt_external(sess, os.path.join(sess.dir, "meta.json"))
            sess.name = name or None
            self._write_meta(sess, self._mono())
        self._changed(sess.id)

    def session_ms(self) -> "int | None":
        """Now, in session milliseconds (None when nothing is recording)."""
        s = self._s
        return None if s is None else s.ms(self._mono())

    def tap_message(self, device: str, session: str, part: str, payload: bytes) -> int:
        """A raw-tap message from a node (``tap/<session>/meta`` or ``…/data``; NodeSource
        spec §7). Written only while a node session is open (owner answer 9: no rolling
        buffer); returns the records written. Thread-safe (the MQTT thread calls it)."""
        with self._lock:
            s = self._s
            if s is None or s.tap is None:
                return 0
            if part == "meta":
                s.tap.header(str(device), str(session), bytes(payload))
                return 0
            if part != "data":
                return 0
            first = not s.tap.entries()
            n = s.tap.batch(str(device), str(session), bytes(payload))
            if n and first:
                self._write_meta(s, self._mono())  # list the tap at once
            return n

    def start(self, snapshot: "dict | None" = None) -> str:
        """Open a session now if none is open; returns its id. For tests and tools only:
        no server route starts a session without a connection (ADR-0011). It ends by the
        usual idle rule."""
        with self._lock:
            if self._s is None:
                self._open(self._clock(), self._mono(), snapshot or {})
            return self._s.id

    def split(self, snapshot: "dict | None" = None) -> str:
        """End the recording session and start a new one; returns the new id.
        ``NotRecording`` unless a session is recording (not paused)."""
        with self._lock:
            if self._s is None or self._s.paused:
                raise NotRecording()
            prev = self._s
            self._end(prev, self._clock(), self._mono(), reason="split")
            self._open(self._clock(), self._mono(), snapshot or (
                {"source_kind": "node"} if prev.node else {}))
            return self._s.id

    def event(self, etype: str, **fields) -> "dict | None":
        """Append ``{"t", "type", ...fields}`` to the open session's ``events.jsonl``.
        State-ish types are written only when they change; ``command`` is reduced to
        ``action, ok, message?, error?``; ``trust``/``params`` are always stripped. Returns
        the line written, or None (no session open, or no change)."""
        with self._lock:
            s = self._s
            if s is None or not isinstance(etype, str) or not _TYPE_RE.match(etype):
                return None
            m = self._mono()
            if etype in STATE_TYPES:
                value = _event_value(etype, fields)
                if s.state.get(etype, object()) == value:
                    return None
                s.state[etype] = value
                return self._emit(s, m, etype, _event_fields(etype, value))
            if etype == "command":
                return self._emit(s, m, etype, clean_command(fields))
            if etype == "accel_cal":
                return self._emit(s, m, etype, {k: fields.get(k) for k in
                                                ("matrix", "source", "method")})
            return self._emit(s, m, etype, fields)

    def note(self, text: str = "", tags=(), kind: str = "mark", capture=None,
             t_end=None, snapshot: "dict | None" = None) -> "tuple[str, dict]":
        """A live note stamped now in the recording session. Returns ``(session_id,
        note)``; ``NotRecording`` when nothing is recording (no session, or paused),
        ``ValueError`` on bad input. ``snapshot`` is accepted for compatibility."""
        with self._lock:
            s = self._s
            if s is None or s.paused:
                raise NotRecording()
            note = NoteLog(s.dir, clock=self._clock).add(
                s.ms(self._mono()), text=text, tags=tags, kind=kind, source="live",
                t_end=t_end, capture=capture)
        self._changed(s.id)
        return s.id, note

    # ---- acceleration -------------------------------------------------- #

    def set_accel_cal(self, matrix, source: str = "phone", method: str = "level") -> dict:
        """Store a sensor→vehicle calibration for ``source`` (kept for later sessions too),
        record it in ``meta.accel_cal`` and as an ``accel_cal`` event."""
        if not motion.valid_matrix(matrix):
            raise ValueError("matrix must be 3x3 numbers")
        cal = {"matrix": [[float(x) for x in row] for row in matrix],
               "source": str(source or "phone"), "method": str(method or "manual")}
        with self._lock:
            self._cal[cal["source"]] = cal
            s = self._s
            if s is not None:
                s.accel_cal = cal
                self._emit(s, self._mono(), "accel_cal", dict(cal))
                self._write_meta(s, self._mono())
        return cal

    def accel_matrix(self, source: str):
        cal = self._cal.get(source)
        if cal is not None:
            return cal["matrix"]
        return motion.IDENTITY if source in _ALIGNED_SOURCES else None

    def feed_accel(self, samples, source: str = "phone",
                   session: "str | None" = None) -> int:
        """Write ``[[epoch_ms, ax, ay, az], ...]`` (m/s², specific force) as sparse rows at
        their own times: ``Acc_X/Y/Z`` raw and, when a calibration applies, ``InlineAcc``/
        ``LateralAcc``/``VerticalAcc`` in g. Returns the rows written (0 when nothing is
        recording). ``session`` must name the recording session if given (``KeyError``)."""
        with self._lock:
            s = self._s
            if session is not None and (s is None or s.id != session):
                raise KeyError(session)
            if s is None or s.paused or not samples:  # paused: no data rows
                return 0
            m = self._mono()
            if not s.extra:
                self._ensure_columns(s, m, [], list(ch.ACCEL_CHANNELS))
            matrix = self.accel_matrix(source)
            start_ms = s.start_s * 1000.0
            limit_ms = s.ms(m) + 5000
            n = 0
            for smp in list(samples)[:MAX_ACCEL_SAMPLES]:
                try:
                    ep, ax, ay, az = (float(x) for x in smp[:4])
                except (TypeError, ValueError):
                    continue
                if not all(math.isfinite(x) for x in (ep, ax, ay, az)):
                    continue
                t_ms = int(round(ep - start_ms))
                if t_ms < 0 or t_ms > limit_ms:
                    continue
                vals = {"Acc_X": fmt_num(ax, 3), "Acc_Y": fmt_num(ay, 3),
                        "Acc_Z": fmt_num(az, 3)}
                if matrix is not None:
                    il, lt, vt = motion.to_vehicle((ax, ay, az), matrix)
                    vals.update(InlineAcc=fmt_num(il, 4), LateralAcc=fmt_num(lt, 4),
                                VerticalAcc=fmt_num(vt, 4))
                vals["Interval"] = str(t_ms)
                vals["Utc"] = str(int(round(ep)))
                self._write_row(s, m, vals)
                n += 1
            s.accel_rows += n
            return n

    # ---- audio --------------------------------------------------------- #

    def audio_put(self, track: str, seq: int, data: bytes, mime: str = "audio/webm",
                  start_ms: "float | None" = None, session: "str | None" = None,
                  source: str = "phone") -> dict:
        """Append a phone audio chunk to ``audio-<track>.<ext>`` of the recording session.
        ``start_ms`` is the epoch ms of the track start (sent with seq 0). Returns the
        track's ``meta.audio`` entry. ``KeyError`` when no/another session is recording,
        ``ValueError`` for a bad track, type or chunk."""
        with self._lock:
            s = self._s
            if s is None or (session is not None and s.id != session):
                raise KeyError(session or "no session is recording")
            m = self._mono()
            w = s.writers.get(track)
            if w is None:
                if any(e["track"] == track for e in s.audio):
                    raise ValueError("track already finished")
                t0 = s.ms(m) if start_ms is None else max(
                    0, int(round(float(start_ms) - s.start_s * 1000.0)))
                w = AudioTrackWriter(s.dir, track, mime, t0, source=source)
                s.writers[track] = w
                self._emit(s, m, "audio", {"track": w.track, "state": "start",
                                           "source": source})
                self._write_meta(s, m)
            w.put(seq, data)
            w.end_ms = s.ms(m)
            return w.entry()

    def audio_stop(self, track: str, state: str = "stop") -> "dict | None":
        """Close a phone track (``state`` ``stop`` or ``lost``); its entry, or None."""
        with self._lock:
            s = self._s
            if s is None or track not in s.writers:
                return None
            return self._close_writer(s, self._mono(), track, state)

    def set_pi_audio(self, pi) -> None:
        """Turn Pi audio on (a ``PiAudio``; recorded for every session from now) or off
        (None). Never raises."""
        with self._lock:
            s = self._s
            if pi is None:
                if s is not None:
                    self._stop_pi(s, self._mono())
                elif self._pi is not None:
                    try:
                        self._pi.stop()
                    except Exception:  # noqa: BLE001
                        pass
                self._pi = None
                return
            self._pi = pi
            if s is not None and s.pi_entry is None:
                self._start_pi(s, self._mono())

    # ---- internals ---------------------------------------------------- #

    def _note_cadence(self, m: float) -> None:
        if self._last_feed_m is not None:
            dt = m - self._last_feed_m
            if 0 < dt < 10:
                self._dt_ema = dt if self._dt_ema is None else 0.8 * self._dt_ema + 0.2 * dt
        self._last_feed_m = m

    def _rate(self) -> int:
        if self.poll_hz:
            return max(1, int(round(self.poll_hz)))
        if self._dt_ema:
            return max(1, min(50, int(round(1.0 / self._dt_ema))))
        return DEFAULT_RATE_HZ

    def _changed(self, sid: str) -> None:
        cb = self.on_change
        if cb is None:
            return
        try:
            cb(sid)
        except Exception:  # noqa: BLE001 — an index failure never stops recording
            pass

    def _recover(self) -> None:
        """Mark sessions left ``recording`` by a crash as ended."""
        if not os.path.isdir(self.root):
            return
        for sid in os.listdir(self.root):
            p = os.path.join(self.root, sid, "meta.json")
            meta = _read_meta(p) if _ID_RE.match(sid) else None
            if meta and meta.get("recording"):
                meta["recording"] = False
                if not meta.get("end_utc"):
                    try:
                        start = calendar.timegm(time.strptime(meta["start_utc"][:19],
                                                              "%Y-%m-%dT%H:%M:%S"))
                        meta["end_utc"] = iso_utc(start + float(meta.get("duration_s") or 0))
                    except (KeyError, ValueError, TypeError, OverflowError):
                        pass
                try:
                    write_json_atomic(p, meta)
                except OSError:
                    pass

    def _open(self, now: float, m: float, snap: dict) -> _Session:
        os.makedirs(self.root, exist_ok=True)
        if self.min_free_bytes:
            try:
                rotate_sessions(self.root, self.min_free_bytes)
            except OSError:
                pass
        base = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
        sid, n = base, 0
        while os.path.exists(os.path.join(self.root, sid)):
            n += 1
            sid = f"{base}-{n}"
        path = os.path.join(self.root, sid)
        os.makedirs(path)
        mode = snap.get("mode")
        node = _node.is_node(snap)
        self._src = self.source or ("node" if node else
                                    mode if mode in ("mock", "live", "demo") else "live")
        s = _Session(sid, path, now, m)
        if node:
            s.node = True
            s.pack = _node.pack_info()
            s.devices.update(d for d in snap.get("devices") or [] if isinstance(d, str))
            s.tap = TapRecorder(path, record_identity=self.record_identity,
                                emit=lambda etype, fields: self._emit(
                                    s, self._mono(), etype, fields),
                                mono=self._mono, fsync=self._fsync)
        # A synthetic session (the pack's committed demo logs) belongs to no vehicle and
        # stays byte-stable: it gets a vid only when one is passed in.
        s.vid = self.vid or (None if self.synthetic else local_vid(self.state_dir))
        s.name, self._next_name = getattr(self, "_next_name", None), None
        s.columns = self._columns(s)
        s.units = {c: ch.UNITS.get(c, "") for c in s.columns}
        s.state = derive_state(snap)
        s.efh = open(os.path.join(path, "events.jsonl"), "w", encoding="utf-8")
        self._s = s
        self._new_part(s, m)  # writes the state line
        if s.state.get("connect_phase"):
            self._emit(s, m, "connect_phase", {"phase": s.state["connect_phase"]})
        if s.state.get("error"):
            self._emit(s, m, "error", {"error": s.state["error"]})
        for cal in self._cal.values():
            s.accel_cal = cal
            self._emit(s, m, "accel_cal", dict(cal))
        if self._pi is not None:
            self._start_pi(s, m)
        self._write_meta(s, m)
        self._changed(sid)
        return s

    @staticmethod
    def _columns(s: _Session) -> "list[str]":
        return [*ch.TIME_CHANNELS, *ch.GPS_CHANNELS, *ch.GPS_ACCEL_CHANNELS, *s.signals,
                *s.extra, *ch.TEXT_CHANNELS]

    def _sync_device_info(self, s: _Session, m: float, snap: dict) -> None:
        """Each device's firmware and manifest ``etag`` (NodeSource spec §7, P3; UI spec
        §4.1: replay renders what was recorded). The latest goes to ``meta.json``
        ``device_info``; every first sight and change is a ``node_manifest`` event."""
        for dev, info in sorted((snap.get("device_info") or {}).items()):
            if not isinstance(dev, str) or not isinstance(info, dict):
                continue
            cur = {"fw": info.get("fw") if isinstance(info.get("fw"), str) else None,
                   "etag": info.get("etag") if isinstance(info.get("etag"), str) else None}
            if s.device_info.get(dev) != cur:
                s.device_info[dev] = cur
                self._emit(s, m, "node_manifest", {"device": dev, **cur})

    def _emit(self, s: _Session, m: float, etype: str, fields: dict) -> "dict | None":
        if s.efh is None:
            return None
        line = {"t": s.ms(m), "type": etype}
        for k, v in fields.items():
            if k in ("t", "type") or k in _STRIP:
                continue
            line[k] = v
        try:
            s.efh.write(json.dumps(line, ensure_ascii=False, separators=(",", ":"),
                                   default=str) + "\n")
        except (OSError, ValueError):
            return None
        s.events_dirty = True
        self._sync(s, m)
        return line

    def _state_line(self, s: _Session, m: float) -> None:
        self._emit(s, m, "state", {k: s.state.get(k) for k in STATE_LINE})

    def _state_changes(self, s: _Session, m: float, snap: dict) -> None:
        new = derive_state(snap)
        for etype in STATE_TYPES:
            if new[etype] != s.state.get(etype, object()):
                s.state[etype] = new[etype]
                self._emit(s, m, etype, _event_fields(etype, new[etype]))

    def _part_name(self, idx: int) -> str:
        return "data.csv" if idx == 0 else f"data-{idx}.csv"

    def _new_part(self, s: _Session, m: float, state_line: bool = True) -> None:
        if s.fh is not None:  # close the current part; data.csv → data-0.csv on first split
            self._sync(s, m, force=True)
            s.fh.close()
            s.fh = None
            if s.parts == ["data.csv"]:
                os.replace(os.path.join(s.dir, "data.csv"), os.path.join(s.dir, "data-0.csv"))
                s.parts = ["data-0.csv"]
        name = "data.csv" if not s.parts else f"data-{len(s.parts)}.csv"
        s.parts.append(name)
        s.fh = open(os.path.join(s.dir, name), "w", encoding="utf-8", newline="")
        rate = self._rate()
        cells = []
        for c in s.columns:
            r = (10 if c in ch.TIME_CHANNELS else GPS_RATE_HZ if c.startswith("GPS_")
                 else int(self.accel_hz) if c in ch.ACCEL_CHANNELS else rate)
            cells.append(header_cell(c, s.units.get(c, ""), r))
        s.fh.write(",".join(cells) + "\n")
        s.part_start_m = m
        s.last_sync_m = -math.inf
        if state_line:
            self._state_line(s, m)

    def _sync(self, s: _Session, m: float, force: bool = False) -> None:
        if s.fh is None:
            return
        if force or m - s.last_sync_m >= FSYNC_S:
            s.fh.flush()
            try:
                self._fsync(s.fh.fileno())
            except OSError:
                pass
            self.fsyncs += 1
            if s.efh is not None and s.events_dirty:
                s.efh.flush()
                try:
                    self._fsync(s.efh.fileno())
                except OSError:
                    pass
                s.events_dirty = False
            for w in s.writers.values():
                w.sync(self._fsync)
            if s.tap is not None:
                s.tap.sync(force=force)
            s.last_sync_m = m

    def _ensure_columns(self, s: _Session, m: float, new_signals: "list[str]",
                        new_extra: "list[str]") -> None:
        """Add channels; a new part (or, before the first row, a rewritten header)."""
        if not new_signals and not new_extra:
            return
        s.signals.extend(new_signals)
        s.extra.extend(new_extra)
        for c in new_extra:
            s.units.setdefault(c, ch.UNITS.get(c, ""))
        s.columns = self._columns(s)
        if s.rows > 0:
            self._new_part(s, m)
            self._write_meta(s, m)
        else:  # nothing written yet: rewrite this part's header in place
            s.fh.seek(0)
            s.fh.truncate()
            s.parts.pop()
            fh, s.fh = s.fh, None
            fh.close()
            self._new_part(s, m, state_line=False)
            # new channels → meta.channels now (not at the next 30 s rewrite), so a live view
            # of the drive in progress can chart them straight away
            self._write_meta(s, m)

    def _write_row(self, s: _Session, m: float, vals: dict) -> None:
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerow([vals.get(c, "") for c in s.columns])
        s.fh.write(buf.getvalue())
        s.rows += 1
        self._sync(s, m)

    def _row(self, s: _Session, now: float, m: float, snap: "dict | None",
             fix) -> None:
        vals: "dict[str, str]" = {}
        new_signals: "list[str]" = []
        if snap is not None:
            sigs = snap.get("signals") or {}
            if s.node:  # a stale value is a last known one, never a live row (spec §7)
                sigs = {k: v for k, v in sigs.items() if _node.is_live(v)}
                s.devices.update(d for d in snap.get("devices") or [] if isinstance(d, str))
                self._sync_device_info(s, m, snap)
            for name, sv in sigs.items():
                if not isinstance(name, str) or _IDENTITY.search(name):
                    continue
                v = _num_value(sv)
                if v is None:
                    continue
                if name not in s.signals and name not in new_signals:
                    if name in ch.ACCEL_CHANNELS or name in ch.GPS_ACCEL_CHANNELS:
                        continue  # reserved for feed_accel / GPS
                    new_signals.append(name)
                    unit = sv.get("u") if isinstance(sv, dict) else None
                    s.units[name] = str(unit) if unit else ch.UNITS.get(name, "")
                vals[name] = fmt_num(v)
                if name == "speed":
                    s.max_speed = v if s.max_speed is None else max(s.max_speed, v)
            if s.node:
                for col, (v, unit) in _node.vss_values(snap).items():
                    if col not in s.signals and col not in new_signals:
                        new_signals.append(col)
                        s.units[col] = unit
                    vals[col] = fmt_num(v)
            module = _canonical_module(snap.get("module"))
            if isinstance(module, str) and module:
                vals["module"] = module
                if module not in s.modules:
                    s.modules.append(module)
            faults = snap.get("faults")
            if isinstance(faults, list):
                vals["faults"] = "; ".join(str(f) for f in faults)
        if fix is not None and fix.mono != s.last_fix_mono and m - s.last_gps_m >= GPS_MIN_S:
            s.last_fix_mono, s.last_gps_m = fix.mono, m
            if fix.utc_ms is not None:
                s.utc_offset = fix.utc_ms - (fix.mono if fix.mono else m) * 1000.0
            self._gps_vals(s, m, fix, vals)
        if not vals:
            return
        if s.node and not any(c not in ch.TEXT_CHANNELS for c in vals):
            return  # nothing live from the node this poll: no row (spec §7)
        if new_signals:
            self._ensure_columns(s, m, new_signals, [])
        elif m - s.part_start_m >= PART_S:
            self._new_part(s, m)
            self._write_meta(s, m)
        node_ms = _node.node_utc_ms(snap) if (s.node and snap is not None) else None
        if s.node and s.utc_offset is None:
            self._note_clock(s, m, node_ms is not None)
        if s.utc_offset is not None:
            utc = str(int(round(m * 1000.0 + s.utc_offset)))
        elif node_ms is not None:
            utc = str(int(round(node_ms)))
        elif self.trust_clock:
            utc = str(int(round(now * 1000.0)))
        else:
            utc = ""
        vals["Interval"] = str(s.ms(m))
        vals["Utc"] = utc
        self._write_row(s, m, vals)

    def _note_clock(self, s: _Session, m: float, synced: bool) -> None:
        """A node session's ``Utc`` source changed: the node's synced clock, or the Brain's
        (``time_unsynced``; spec §7)."""
        if s.clock_synced == synced:
            return
        if not synced:
            self._emit(s, m, "time_unsynced", {"utc_from": "brain"})
        elif s.clock_synced is not None:
            self._emit(s, m, "time_synced", {"utc_from": "node"})
        s.clock_synced = synced

    def _gps_vals(self, s: _Session, m: float, fix, vals: dict) -> None:
        lat, lon = float(fix.lat), float(fix.lon)
        vals["GPS_Latitude"] = fmt_num(lat, 7)
        vals["GPS_Longitude"] = fmt_num(lon, 7)
        if fix.speed_kmh is not None:
            vals["GPS_Speed"] = fmt_num(fix.speed_kmh, 2)
            s.max_speed = (fix.speed_kmh if s.max_speed is None
                           else max(s.max_speed, fix.speed_kmh))
        if fix.heading is not None:
            vals["GPS_Heading"] = fmt_num(fix.heading, 1)
        if fix.alt_m is not None:
            vals["GPS_Altitude"] = fmt_num(fix.alt_m, 1)
        if fix.sats is not None:
            vals["GPS_Nsat"] = fmt_num(int(fix.sats))
        if fix.hdop is not None:
            vals["GPS_HDOP"] = fmt_num(fix.hdop, 2)
        acc = s.gps_accel.feed(fix.utc_ms if fix.utc_ms is not None else m * 1000.0,
                               fix.speed_kmh, fix.heading)
        if acc is not None:
            vals["GPS_LonAcc"] = fmt_num(acc[0], 3)
            vals["GPS_LatAcc"] = fmt_num(acc[1], 3)
        s.has_gps = True
        if s.last_pt is not None and (fix.speed_kmh is None or fix.speed_kmh >= JITTER_KMH):
            s.dist_m += haversine_m(s.last_pt[0], s.last_pt[1], lat, lon)
        s.last_pt = (lat, lon)
        if s.bbox is None:
            s.bbox = [lon, lat, lon, lat]
        else:
            b = s.bbox
            s.bbox = [min(b[0], lon), min(b[1], lat), max(b[2], lon), max(b[3], lat)]
        pos = [round(lon, 3), round(lat, 3)]
        if s.start_pos is None:
            s.start_pos = pos
        s.end_pos = pos

    # ---- audio internals ---- #

    def _close_writer(self, s: _Session, m: float, track: str, state: str) -> dict:
        w = s.writers.pop(track)
        w.close(end_ms=s.ms(m))
        entry = w.entry()
        s.audio.append(entry)
        self._emit(s, m, "audio", {"track": track, "state": state if state in (
            "stop", "lost") else "stop", "source": w.source})
        self._write_meta(s, m)
        return entry

    def _start_pi(self, s: _Session, m: float) -> None:
        pi = self._pi
        try:
            track = pi.start(s.dir)
        except Exception:  # noqa: BLE001
            track = None
        if not track:
            return
        s.pi_entry = {"track": track, "mime": getattr(pi, "MIME", "audio/wav"),
                      "start_ms": s.ms(m), "end_ms": None, "source": "pi", "bytes": 0}
        s.audio.append(s.pi_entry)
        self._emit(s, m, "audio", {"track": track, "state": "start", "source": "pi"})

    def _stop_pi(self, s: _Session, m: float, state: str = "stop") -> None:
        e, pi = s.pi_entry, self._pi
        if e is None:
            return
        s.pi_entry = None
        size = 0
        if pi is not None:
            try:
                size = pi.stop()
            except Exception:  # noqa: BLE001
                size = 0
        e["end_ms"], e["bytes"] = s.ms(m), int(size or 0)
        self._emit(s, m, "audio", {"track": e["track"], "state": state, "source": "pi"})

    def _check_pi(self, s: _Session, m: float) -> None:
        if s.pi_entry is None or self._pi is None:
            return
        try:
            alive = self._pi.running
        except Exception:  # noqa: BLE001
            alive = False
        if not alive:
            self._stop_pi(s, m, state="lost")

    def _audio_entries(self, s: _Session) -> "list[dict]":
        out = [dict(e) for e in s.audio]
        out += [w.entry() for w in s.writers.values()]
        return sorted(out, key=lambda e: (e.get("start_ms") or 0, e["track"]))

    # ---- meta / end ---- #

    def _meta(self, s: _Session, m: float) -> dict:
        recording = s.end_s is None
        dur = (m if recording else s.end_m) - s.start_m
        numeric = [c for c in s.columns if c not in ch.TIME_CHANNELS
                   and c not in ch.TEXT_CHANNELS and (s.has_gps or not c.startswith("GPS_"))]
        meta = {
            "id": s.id,
            "vid": s.vid,
            "name": s.user.get("name"),
            "description": s.user.get("description"),
            "place_start": s.user.get("place_start"),
            "place_end": s.user.get("place_end"),
            "place": s.user.get("place"),
            "start_utc": iso_utc(s.start_s),
            "end_utc": None if recording else iso_utc(s.end_s),
            "duration_s": int(round(max(0.0, dur))),
            "rows": s.rows,
            "parts": list(s.parts),
            "modules": list(s.modules),
            "channels": [{"name": c, "units": s.units.get(c, ""), "group": ch.group_for(c),
                          "c": ch.confidence_for(c), "limits": ch.limits_for(c)}
                         for c in numeric],
            "has_gps": s.has_gps,
            "distance_km": round(s.dist_m / 1000.0, 2),
            "max_speed_kmh": None if s.max_speed is None else round(float(s.max_speed), 1),
            "bbox": None if s.bbox is None else [round(x, 5) for x in s.bbox],
            "start_pos": s.start_pos,
            "end_pos": s.end_pos,
            "synthetic": bool(self.synthetic),
            "recording": recording,
            "source": self._src,
            "audio": self._audio_entries(s),
            "accel_cal": s.accel_cal,
        }
        if meta["vid"] is None:
            del meta["vid"]
        if s.node:  # NodeSource spec §7 (ADR-0010 amendment)
            devices = set(s.devices) | set(s.tap.devices() if s.tap is not None else ())
            meta["devices"] = sorted(devices)
            meta["device_info"] = {d: dict(s.device_info[d]) for d in sorted(s.device_info)}
            meta["pack"] = s.pack
            meta["tap"] = s.tap.entries() if s.tap is not None else []
            meta["end_reason"] = s.end_reason
        return meta

    def _adopt_external(self, s: _Session, path: str) -> None:
        """Keep edits another writer made to the user fields since our last write."""
        if not s.written:
            return
        disk = _read_meta(path)
        if not disk:
            return
        for k in USER_KEYS:
            if k in disk and disk[k] != s.written.get(k):
                s.user[k] = s.written[k] = disk[k]

    def _write_meta(self, s: _Session, m: float) -> None:
        path = os.path.join(s.dir, "meta.json")
        self._adopt_external(s, path)
        meta = self._meta(s, m)
        try:
            write_json_atomic(path, meta)
            s.written = {k: meta.get(k) for k in USER_KEYS}
        except OSError:
            pass
        s.last_meta_m = m

    def _fill_places(self, s: _Session) -> None:
        """Offline place names at close (unless another writer already set them)."""
        if s.user.get("place_start") or s.user.get("place_end"):
            return
        found = _places.places_for(s.start_pos, s.end_pos)
        if found is not None:
            s.user.update(found)

    def _end(self, s: _Session, now: float, m: float, reason: str = "idle") -> None:
        s.end_reason = reason
        if s.tap is not None:
            s.tap.close()
        for track in list(s.writers):
            self._close_writer(s, m, track, "stop")
        self._stop_pi(s, m)
        if s.fh is not None:
            self._sync(s, m, force=True)
            s.fh.close()
            s.fh = None
        if s.efh is not None:
            try:
                s.efh.flush()
                if s.events_dirty:
                    self._fsync(s.efh.fileno())
            except OSError:
                pass
            s.efh.close()
            s.efh = None
        s.end_s, s.end_m = now, m
        self._s = None
        has_data = (s.rows > 0 and (s.signals or s.has_gps or s.accel_rows)) or bool(
            s.tap is not None and s.tap.records)
        if not has_data and not s.audio and not read_notes(s.dir):
            # no signal value, GPS fix, note or audio (e.g. a server restart): leave no
            # empty session
            shutil.rmtree(s.dir, ignore_errors=True)
            self._changed(s.id)
            return
        self._adopt_external(s, os.path.join(s.dir, "meta.json"))
        self._fill_places(s)
        self._write_meta(s, m)
        self._changed(s.id)
