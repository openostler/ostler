# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The raw tap beside a recorded session (NodeSource spec §7; ADR-0032 §9, ADR-0036).

While a session records from a node, every tap batch the Brain receives
(``tap/<session>/data``) is written to ``<session dir>/tap/<tap session>.otap``: the
raw-tap v1 records (``node/tap.py``) one after another, appended as they arrive and
fsynced at most once a second, like ``data.csv``. ``meta.json`` lists each file under
``tap`` with the header facts and the counts below. Decoded rows and tap records are linked
by the node's ``t_us`` (raw-tap §2.4).

- **Sequence.** ``seq`` gaps are logged as ``tap_gap`` events and counted, never filled;
  a ``seq`` already written (a QoS 1 redelivery) is skipped. ``overflow`` events from the
  node are counted and logged.
- **Time.** The node's ``time`` events (raw-tap §2.4, CBOR ``{t_us, utc_ns, source,
  err_us}``) are stored with the other records and counted (``time_marks`` in the meta);
  readers map ``t_us`` to UTC from them (``node/tap.py`` ``TimeMap``, the pcapng export).
  A file without one keeps the node's clock only.
- **Identity scrub, checked again (ADR-0036).** A header with ``scrub: on``: the Brain
  re-applies the node's rule and logs anything the node missed. ``scrub: off`` (or no
  header yet) is accepted only when this install's own option ``OSTLER_RECORD_IDENTITY``
  is on; otherwise the Brain scrubs (``scrub: "brain"`` in the meta). The option is read
  from the process environment only (local install configuration), never from the API,
  MQTT or a pack.
- Exports scrub and drop unframed records whatever the setting (``logbook/pcapng.py``).
"""
from __future__ import annotations

import os
import re
from typing import Callable, Optional

from ..node.tap import (EV_OVERFLOW, IdentityScrub, TapRecord, encode_record, is_time_event,
                        parse_header, parse_records, valid_session)

RECORD_IDENTITY_ENV = "OSTLER_RECORD_IDENTITY"
_TRUE = frozenset({"1", "true", "yes", "on"})
TAP_DIR = "tap"
EXT = ".otap"
FSYNC_S = 1.0
_SAFE = re.compile(r"[^A-Za-z0-9_.-]")


def identity_recording_enabled(environ=None) -> bool:
    """The install-level option (ADR-0036 §1): off unless ``OSTLER_RECORD_IDENTITY`` is
    set in this process's environment."""
    env = os.environ if environ is None else environ
    return str(env.get(RECORD_IDENTITY_ENV, "")).strip().lower() in _TRUE


class _Stream:
    """One tap session's file within one recorded session."""

    def __init__(self, device: str, session: str, path: str, header: "dict | None") -> None:
        self.device, self.session, self.path = device, session, path
        self.header = header
        self.fh = None
        self.expected: "int | None" = None
        self.seq_first: "int | None" = None
        self.seq_last: "int | None" = None
        self.records = 0
        self.bytes = 0
        self.gaps = 0
        self.lost = 0
        self.duplicates = 0
        self.overflow = 0
        self.time_marks = 0
        self.malformed = 0
        self.scrub = IdentityScrub()
        self.mode: "str | None" = None
        self.dirty = False

    def entry(self) -> dict:
        h = self.header or {}
        return {"session": self.session, "device": self.device,
                "file": f"{TAP_DIR}/{os.path.basename(self.path)}",
                "boot_id": h.get("boot_id"), "scrub": self.mode,
                "buses": h.get("buses") if isinstance(h.get("buses"), list) else [],
                "clock": h.get("clock") if isinstance(h.get("clock"), dict) else None,
                "started": h.get("started") if isinstance(h.get("started"), str) else None,
                "seq_first": self.seq_first, "seq_last": self.seq_last,
                "records": self.records, "bytes": self.bytes,
                "gaps": self.gaps, "lost": self.lost, "overflow": self.overflow,
                "time_marks": self.time_marks,
                "brain_scrubbed": self.scrub.scrubbed, "brain_dropped": self.scrub.dropped}


class TapRecorder:
    """The tap files of one recorded session. Thread-safe use is the caller's job (the
    session recorder calls it under its lock)."""

    def __init__(self, session_dir: str, *, record_identity: bool = False,
                 emit: "Callable[[str, dict], None] | None" = None,
                 mono: "Callable[[], float] | None" = None,
                 fsync: Callable[[int], None] = os.fsync) -> None:
        import time

        self.dir = os.path.join(session_dir, TAP_DIR)
        self.record_identity = bool(record_identity)
        self._emit = emit if emit is not None else (lambda etype, fields: None)
        self._mono = mono if mono is not None else time.monotonic
        self._fsync = fsync
        self._streams: "dict[tuple[str, str], _Stream]" = {}
        self._headers: "dict[tuple[str, str], dict]" = {}
        self._last_sync = -1e18
        self._refused: "set[str]" = set()

    # ---- input ------------------------------------------------------------------------ #
    def header(self, device: str, session: str, payload: bytes) -> bool:
        """A ``tap/<session>/meta`` header (often a retained copy). Kept in memory; a file
        is only opened when that session's batches arrive."""
        if not valid_session(session):
            return False
        h = parse_header(payload)
        if h is None:
            self._once(f"hdr:{device}/{session}", "tap_error",
                       {"session": session, "device": device, "error": "unreadable header"})
            return False
        self._headers[(device, session)] = h
        st = self._streams.get((device, session))
        if st is not None:
            st.header = h
        return True

    def batch(self, device: str, session: str, payload: bytes) -> int:
        """One ``tap/<session>/data`` batch; returns the records written."""
        if not valid_session(session):
            self._once(f"id:{session}", "tap_error",
                       {"device": device, "error": "tap session id is not a ULID; dropped"})
            return 0
        st = self._stream(device, session)
        records, trailing = parse_records(payload)
        if trailing:
            st.malformed += 1
            self._emit("tap_error", {"session": session, "device": device,
                                     "error": f"{trailing} trailing bytes in a batch dropped"})
        out = []
        for r in records:
            if st.expected is not None and r.seq < st.expected:
                st.duplicates += 1
                continue
            if st.expected is not None and r.seq > st.expected:
                st.gaps += 1
                st.lost += r.seq - st.expected
                self._emit("tap_gap", {"session": session, "device": device,
                                       "from": st.expected, "to": r.seq - 1,
                                       "lost": r.seq - st.expected})
            st.expected = r.seq + 1
            if r.is_event and r.dir == EV_OVERFLOW:
                st.overflow += 1
                self._emit("tap_overflow", {"session": session, "device": device,
                                            "seq": r.seq})
            kept = self._check(st, r)
            if kept is None:
                continue
            if is_time_event(kept):
                st.time_marks += 1
            if st.seq_first is None:
                st.seq_first = r.seq
            st.seq_last = r.seq
            out.append(encode_record(kept))
        if out:
            data = b"".join(out)
            if st.fh is None:
                os.makedirs(self.dir, exist_ok=True)
                st.fh = open(st.path, "ab")
            st.fh.write(data)
            st.records += len(out)
            st.bytes += len(data)
            st.dirty = True
        self.sync()
        return len(out)

    def _check(self, st: _Stream, r: TapRecord) -> "Optional[TapRecord]":
        node_scrub = (st.header or {}).get("scrub")
        if node_scrub == "on":
            mode = "on"
        elif self.record_identity:
            mode = "off" if node_scrub == "off" else "unknown"
        else:
            mode = "brain"
        if st.mode != mode:
            if mode == "brain":
                self._emit("tap_scrub", {"session": st.session, "device": st.device,
                                         "by": "brain", "node_scrub": node_scrub})
            st.mode = mode
        if mode in ("off", "unknown"):
            return r  # the install option is on: stored here, never leaves (ADR-0036 §3)
        before = st.scrub.scrubbed
        kept = st.scrub.check(r)
        if mode == "on" and st.scrub.scrubbed > before:
            self._once(f"miss:{st.device}/{st.session}", "tap_scrub",
                       {"session": st.session, "device": st.device, "by": "brain",
                        "node_scrub": "on", "missed": True})
        return kept

    def _stream(self, device: str, session: str) -> _Stream:
        st = self._streams.get((device, session))
        if st is None:
            name = session + EXT
            if any(s.session == session for s in self._streams.values()):
                name = f"{session}-{_SAFE.sub('_', device)}{EXT}"
            st = _Stream(device, session, os.path.join(self.dir, name),
                         self._headers.get((device, session)))
            self._streams[(device, session)] = st
            h = st.header or {}
            self._emit("tap_start", {"session": session, "device": device,
                                     "boot_id": h.get("boot_id"), "scrub": h.get("scrub")})
        return st

    def _once(self, key: str, etype: str, fields: dict) -> None:
        if key not in self._refused:
            self._refused.add(key)
            self._emit(etype, fields)

    # ---- files ------------------------------------------------------------------------ #
    def sync(self, force: bool = False) -> None:
        m = self._mono()
        if not force and m - self._last_sync < FSYNC_S:
            return
        for st in self._streams.values():
            if st.fh is not None and st.dirty:
                st.fh.flush()
                try:
                    self._fsync(st.fh.fileno())
                except OSError:
                    pass
                st.dirty = False
        self._last_sync = m

    def close(self) -> None:
        self.sync(force=True)
        for st in self._streams.values():
            if st.fh is not None:
                st.fh.close()
                st.fh = None

    @property
    def records(self) -> int:
        return sum(st.records for st in self._streams.values())

    def entries(self) -> "list[dict]":
        return [st.entry() for st in self._streams.values() if st.records]

    def devices(self) -> "list[str]":
        return sorted({st.device for st in self._streams.values() if st.records})


def read_tap(session_dir: str, meta: dict) -> "list[tuple[dict, list[TapRecord]]]":
    """Each ``meta.tap`` entry with its records, read from its ``.otap`` file."""
    out = []
    for e in meta.get("tap") or []:
        if not isinstance(e, dict) or not isinstance(e.get("file"), str):
            continue
        name = os.path.basename(e["file"])
        if not name.endswith(EXT):
            continue
        path = os.path.join(session_dir, TAP_DIR, name)
        try:
            with open(path, "rb") as fh:
                records, _ = parse_records(fh.read())
        except OSError:
            continue
        out.append((e, records))
    return out


__all__ = ["RECORD_IDENTITY_ENV", "TapRecorder", "identity_recording_enabled", "read_tap"]
