# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The redaction pipeline and the ``ostler.share/1`` bundle writer (trip-sharing spec §3,
§4, §6, §7, §9; TS1).

:func:`build_share` reads one recorded session (never changing it: every rule works on a
copy), applies R1–R15 for the chosen level and writes the zip in memory; then it runs the
verifier (R16) on the **final bytes** and raises :class:`ShareBlocked` when it fails, so a
bundle that fails is never handed on. :func:`write_share` saves a built bundle as
``ostler-share-<8 random>.zip`` (the File path; TS1 has no other delivery path).

Levels: **L0** card (stats only, ``trip.json``), **L1** route (``track.gpx`` and
``track.geojson``), **L2** telemetry (``data.csv`` of the picked signals on relative time,
``faults.json``, shareable notes if ticked), **L3** full log (every decoded channel,
``events.jsonl`` by type, the scrubbed raw tap as ``tap/bus<N>.pcapng`` and, for CAN,
``tap/bus<N>.candump``) and **L4** diagnostics (L3 plus ``diag/``). ``card.png`` is drawn by
the share sheet (TS2) and is not written here.

Policy refusals (:class:`ShareRefused`): L3–L4 are hand-overs, never grants; L2 never goes
to ``link`` or ``public``; L3–L4 go to one named person, a pack's maintainers or named
helpers; a route at L3–L4 only to one named person; "keep real date and time" only at
L3–L4 to one named person by relay link (never a file, hub thread or pack issue); public
destinations force L3–L4 to location none and relative time; a route needs a visible trace
of at least 1 km; a public route needs the publish act at least 24 h after the trip ended.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ...node.identity import IdentityTable, is_placeholder, placeholder
from ...node.tap import (DIR_TX_ECHO, PROTO_CAN, PROTO_CAN_FD, TapRecord, TimeMap,
                         is_time_event)
from .. import channels as ch
from ..node import identity_path
from ..notes import read_notes
from ..recorder import _read_meta, fmt_num, header_cell
from ..store import read_events, read_rows
from ..tap import read_tap
from . import trace as tr
from .capture import EventPacket, Packet, cbor_t_us, write_candump, write_pcapng
from .detect import REDACTED, find_vins, redact_json, redact_text
from .ids import IdMap, bundle_id, file_tag
from .scrub import ScrubCounts, scrub_records
from .verify import (FILES, FORMAT, LEVELS, VERIFIER_VERSION, Failure, OwnerContext,
                     VerifyResult, ZIP_TIME, verify_bytes)
from .zones import PrivacyZone

AUDIENCES = ("me", "person", "group", "household", "link", "public", "maintainers", "helpers")
PATHS = ("file", "grant", "relay", "hub", "pack_issue")
HANDOVER_AUDIENCES = ("person", "maintainers", "helpers")
DEFAULT_SIGNALS = ("Vehicle.Speed", "Vehicle.Powertrain.CombustionEngine.Speed",
                   "Vehicle.Powertrain.CombustionEngine.ECT", "speed", "rpm", "coolant_temp")
SPEED_CHANNELS = ("Vehicle.Speed", "speed", "road_speed", "vehicle_speed")
_ODOMETER = re.compile(r"odometer|odo_|^odo$|traveleddistance|mileage", re.IGNORECASE)
_HOURS = re.compile(r"enginehours|engine_hours|operatinghours|operating_hours|(^|_)hours$",
                    re.IGNORECASE)
_HEADING_ALT = re.compile(r"heading|altitude|latitude|longitude|currentlocation", re.IGNORECASE)
_HEX_TEXT = re.compile(r"^[0-9A-Fa-f]{2}(?: [0-9A-Fa-f]{2})+$")
# dates and times of day in free text (the L4 log tail) at relative time (R9)
_TIMES = re.compile(r"(?<!\d)\d{4}-[01]\d-[0-3]\d(?:[T ][0-2]\d:[0-5]\d(?::[0-5]\d(?:\.\d+)?)?Z?)?"
                    r"|(?<![\d:])[0-2]\d:[0-5]\d(?::[0-5]\d(?:\.\d+)?)?(?![\d:])")
TIME_REDACTED = "**TIME**"
EVENT_FIELDS = ("type", "module", "conn", "status", "mode", "phase")
PUBLIC_DELAY_S = 24 * 3600


class ShareRefused(ValueError):
    """The requested share breaks a sharing rule (nothing is built)."""


class ShareBlocked(RuntimeError):
    """The built bundle fails the verifier (R3 VIN block or any other check): nothing
    leaves. ``failures`` names each file, frame and offset."""

    def __init__(self, failures: "List[Failure]") -> None:
        self.failures = failures
        lines = "; ".join(f"check {f.check} ({f.rule}) {f.file or ''}: {f.detail}"
                          for f in failures[:8])
        super().__init__(f"share blocked: {lines}")


@dataclass
class ShareOptions:
    level: str
    audience: str = "me"
    path: str = "file"
    recipient: Optional[str] = None          # the one named person (by name)
    route: bool = False                      # "L1 ticked" on L2–L4
    keep_real_time: bool = False
    public_destination: bool = False         # a public thread or pack issue
    publish: bool = False                    # the explicit publish act (public L0–L1)
    ends_m: int = tr.DEFAULT_TRIM_M
    zones: Sequence[PrivacyZone] = ()
    signals: Optional[Sequence[str]] = None  # L2 picker; None = the defaults
    include_notes: bool = False
    include_faults_count: bool = False
    show_max_speed: Optional[bool] = None    # None = R15 default for the audience
    t_from_ms: Optional[float] = None
    t_to_ms: Optional[float] = None
    vehicle: Mapping[str, Any] = field(default_factory=dict)
    show_nickname: bool = False
    show_plate: bool = False
    request: Optional[Mapping[str, Any]] = None
    contribution_consent: bool = False
    credit: Optional[str] = None
    log_tail: Optional[str] = None
    config: Optional[Mapping[str, Any]] = None
    expires: Optional[str] = None
    wmi: Optional[str] = None


@dataclass
class ShareBundle:
    name: str
    data: bytes
    manifest: dict
    id_map: dict                 # owner's device only: new id → real id
    report: "List[dict]"         # the redaction report (same as manifest["redactions"])
    verify: VerifyResult
    owner: OwnerContext


# ---- policy ------------------------------------------------------------------------------ #
def check_policy(o: ShareOptions) -> None:
    """The level, audience and path rules (spec §3, §6, §10; ADR-0043)."""
    if o.level not in LEVELS:
        raise ShareRefused(f"unknown level {o.level!r}")
    if o.audience not in AUDIENCES:
        raise ShareRefused(f"unknown audience {o.audience!r}")
    if o.path not in PATHS:
        raise ShareRefused(f"unknown delivery path {o.path!r}")
    lv = LEVELS.index(o.level)
    if lv >= 3:
        if o.path == "grant":
            raise ShareRefused(f"{o.level} is a hand-over, never a grant (ADR-0043 §2)")
        if o.audience not in HANDOVER_AUDIENCES:
            raise ShareRefused(f"{o.level} goes only to one named person, a pack's "
                               "maintainers or named helpers")
        if o.route and (o.audience != "person" or not o.recipient or o.public_destination):
            raise ShareRefused("a full log or diagnostics bundle carries location only to "
                               "one named person")
    if lv == 2 and o.audience in ("link", "public"):
        raise ShareRefused("L2 never goes to a link or the public")
    if lv <= 1 and o.path not in ("file", "grant", "relay", "hub"):
        raise ShareRefused(f"{o.level} cannot be sent by {o.path}")
    if o.keep_real_time:
        if lv < 3 or o.audience != "person" or not o.recipient or o.path != "relay" \
                or o.public_destination:
            raise ShareRefused("keep real date and time is only for L3–L4 to one named "
                               "person by relay link (never a file, hub thread, pack issue "
                               "or several people)")
    if o.route and lv in (0, 1):
        raise ShareRefused("route is the L1 tick on L2–L4")
    tr.check_trim(o.ends_m)


# ---- helpers ----------------------------------------------------------------------------- #
def _num(v) -> "float | None":
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _local_day(epoch_ms: "float | None", tz_offset_s: "int | None" = None) -> "str | None":
    if epoch_ms is None:
        return None
    s = epoch_ms / 1000.0
    st = time.gmtime(s + tz_offset_s) if tz_offset_s is not None else time.localtime(s)
    return time.strftime("%Y-%m-%d", st)


def _start_epoch_ms(meta: dict) -> "float | None":
    import calendar

    try:
        return calendar.timegm(time.strptime(str(meta.get("start_utc"))[:19],
                                             "%Y-%m-%dT%H:%M:%S")) * 1000.0
    except (TypeError, ValueError):
        return None


def _utc_at(rows: "Sequence[dict]", meta: dict, t_ms: float) -> "float | None":
    """Epoch ms of session ms ``t_ms``: the nearest row's ``Utc``, else the meta start."""
    best = None
    for r in rows:
        u, t = _num(r.get("Utc")), _num(r.get("Interval"))
        if u is None or t is None:
            continue
        if best is None or abs(t - t_ms) < abs(best[0] - t_ms):
            best = (t, u)
    if best is not None:
        return best[1] + (t_ms - best[0])
    start = _start_epoch_ms(meta)
    return None if start is None else start + t_ms


def _region(lat: float, lon: float) -> "str | None":
    """A GeoNames admin-2 region label (e.g. "Derbyshire"), never a town."""
    try:
        from ...geo import offline

        hit = offline.label(lat, lon)
    except Exception:  # noqa: BLE001 — no gazetteer: no label
        return None
    if not isinstance(hit, dict):
        return None
    return hit.get("region") or hit.get("country") or None


def _in_windows(t: float, windows) -> bool:
    return windows is None or any(a <= t <= b for a, b in windows)


def _scrub_hex_text(s: str, table: IdentityTable) -> "Tuple[str, bool]":
    if not _HEX_TEXT.match(s.strip()):
        return s, False
    msg = bytes.fromhex(s.replace(" ", ""))
    k = table.match(msg)
    if not k or is_placeholder(msg[k:]):
        return s, False
    return (msg[:k] + placeholder(len(msg) - k)).hex(" ").upper(), True


class _Report:
    """The redaction record: ``[{rule, count, detail}]`` (``share.json`` ``redactions``)."""

    def __init__(self) -> None:
        self.items: "Dict[Tuple[str, str], int]" = {}

    def add(self, rule: str, count: int, detail: str) -> None:
        if count:
            self.items[(rule, detail)] = self.items.get((rule, detail), 0) + count

    def list(self) -> "List[dict]":
        return [{"rule": r, "count": n, "detail": d} for (r, d), n in
                sorted(self.items.items(), key=lambda kv: (int(kv[0][0][1:]), kv[0][1]))]


# ---- the pipeline ------------------------------------------------------------------------ #
class _Builder:
    def __init__(self, session_dir: str, o: ShareOptions, table: IdentityTable,
                 now: float, tz_offset_s: "int | None") -> None:
        self.dir, self.o, self.table, self.now = session_dir, o, table, now
        self.tz = tz_offset_s
        self.lv = LEVELS.index(o.level)
        self.meta = _read_meta(os.path.join(session_dir, "meta.json")) or {}
        if not self.meta:
            raise ShareRefused(f"no session at {session_dir}")
        cols, rows = read_rows(session_dir, self.meta)
        self.units = {name: units for name, units, _r in cols}
        lo = o.t_from_ms if o.t_from_ms is not None else float("-inf")
        hi = o.t_to_ms if o.t_to_ms is not None else float("inf")
        self.rows = [r for r in rows if lo <= float(r.get("Interval") or 0) <= hi]
        self.ids = IdMap()
        self.ids.mint_session(self.meta.get("id"))
        if self.meta.get("vid"):
            self.ids.get("vid", self.meta["vid"])
        self.rep = _Report()
        self.files: "Dict[str, bytes]" = {}
        self.public = o.audience == "public" or o.path == "pack_issue" or o.public_destination

    # -- R5, R6: the visible trace and stats ------------------------------------------- #
    def trace(self) -> None:
        o = self.o
        self.vt = tr.visible_trace(self.rows, ends_m=o.ends_m, zones=o.zones)
        self.speed_channel = next((c for c in SPEED_CHANNELS
                                   if any(c in r for r in self.rows)), None)
        if self.vt.has_gps:
            self.stats = tr.trace_stats(self.vt, self.rows, self.speed_channel)
        else:
            self.stats = tr.no_gps_stats(self.rows, self.speed_channel)
        self.route = self.lv == 1 or (self.lv >= 2 and o.route and not self.public)
        if self.route:
            if not self.vt.has_gps:
                raise ShareRefused("this trip has no GPS fixes, so it has no route")
            if self.vt.distance_m() < tr.MIN_SHARE_KM * 1000:
                raise ShareRefused("the visible trace is under 1 km: this trip can be "
                                   "shared as a card (L0) only")
            if self.o.audience == "public" and self.lv <= 1:
                end = _utc_at(self.rows, self.meta, max(float(r.get("Interval") or 0)
                                                        for r in self.rows))
                if not o.publish:
                    raise ShareRefused("a public route needs the explicit publish act")
                if end is None or self.now * 1000 - end < PUBLIC_DELAY_S * 1000:
                    raise ShareRefused("a route is publishable only 24 h after the trip ended")
        if self.vt.hidden_trim:
            self.rep.add("R5", self.vt.hidden_trim, f"fixes hidden by the {o.ends_m} m ends trim")
        if self.vt.hidden_zone:
            self.rep.add("R5", self.vt.hidden_zone,
                         f"fixes hidden by {self.vt.zones_hit} privacy zone(s)")
        if self.lv == 0:
            self.location = "coarse" if self.vt.segments and self._region_first() else "none"
        else:
            self.location = "route" if self.route else "none"
        self.basis = "day" if self.lv <= 1 else ("real" if o.keep_real_time and not self.public
                                                 else "relative")
        # the time base and, with a route, the visible windows rows are limited to
        if self.route and self.lv >= 2:
            self.windows = self.vt.windows()
            self.t0 = self.windows[0][0]
        else:
            self.windows = None
            self.t0 = float(self.rows[0].get("Interval") or 0) if self.rows else 0.0
        self.visible_fix_t = {p.t for p in self.vt.points}

    def _region_first(self) -> "str | None":
        if not hasattr(self, "_reg"):
            pts = self.vt.points
            self._reg = _region(pts[0].lat, pts[0].lon) if pts else None
        return self._reg

    # -- trip.json --------------------------------------------------------------------- #
    def trip(self) -> dict:
        o, st = self.o, self.stats
        fine = tr.round_stats(st, card=False)
        card = self.lv == 0
        show_max = o.show_max_speed if o.show_max_speed is not None else \
            o.audience not in ("link", "public") or self.lv >= 2
        out: dict = {"level": o.level}
        if self.basis == "day":
            first_t = self.vt.points[0].t if self.vt.points else self.t0
            out["day"] = _local_day(_utc_at(self.rows, self.meta, first_t), self.tz)
        else:
            out["session"] = self.ids.session
            out["start_s"] = 0
            dur = st.get("duration_s") if self.route else (
                (float(self.rows[-1].get("Interval") or 0) - self.t0) / 1000 if self.rows else 0)
            out["end_s"] = round(dur or 0)
        short = self.vt.has_gps and self.vt.distance_m() < tr.MIN_SHARE_KM * 1000
        if card:
            coarse = {k: v for k, v in fine.items()
                      if k in ("distance_km", "duration_min", "moving_min", "avg_kmh",
                               "max_kmh")}
            coarse = _card_round(coarse)
            if short:
                out["distance"] = "under 1 km"
                coarse = {"avg_kmh": coarse.get("avg_kmh"), "max_kmh": coarse.get("max_kmh")}
            out.update(coarse)
            if self.location == "coarse":
                out["region"] = self._region_first()
        else:
            out.update(fine)
            if self.route:
                pts = self.vt.points
                out["start_region"] = _region(pts[0].lat, pts[0].lon)
                out["end_region"] = _region(pts[-1].lat, pts[-1].lon)
        if not show_max:
            out.pop("max_kmh", None)
            self.rep.add("R15", 1, f"max speed hidden for {o.audience}")
        if o.include_faults_count or self.lv >= 2:
            out["faults_seen"] = len(self.fault_codes())
        v = self.vehicle
        out["vehicle"] = {k: v[k] for k in ("make", "model", "year", "engine") if v.get(k)}
        if v.get("nickname"):
            out["vehicle"]["nickname"] = v["nickname"]
        return out

    def _vehicle(self) -> dict:
        """The vehicle card fields (R12: nickname and plate only when ticked)."""
        v = dict(self.o.vehicle or {})
        out = {k: v.get(k) for k in ("make", "model", "year", "engine", "market")}
        out["kind"] = v.get("kind") if v.get("kind") in ("car", "motorcycle") else "car"
        if self.o.show_nickname and v.get("nickname"):
            out["nickname"] = str(v["nickname"])
        elif v.get("nickname"):
            self.rep.add("R12", 1, "vehicle nickname left out")
        if self.o.show_plate and v.get("plate"):
            out["plate"] = str(v["plate"])
        elif v.get("plate"):
            self.rep.add("R12", 1, "plate hidden")
        return out

    # -- route (R7) -------------------------------------------------------------------- #
    def tracks(self) -> None:
        segs = tr.simplified(self.vt)
        before = sum(len(s) for s in self.vt.segments)
        after = sum(len(s) for s in segs)
        self.rep.add("R7", before - after, "points removed by simplification (10 m); "
                     "point times removed; coordinates to 5 decimals")
        self.files["track.gpx"] = tr.to_route_gpx(segs).encode()
        self.files["track.geojson"] = tr.to_route_geojson(segs).encode()

    # -- data.csv (R1, R8, R9, R11) ------------------------------------------------------ #
    def columns(self) -> "List[str]":
        names: "List[str]" = []
        for c in (self.meta.get("channels") or []):
            if isinstance(c, dict) and c.get("name") and c["name"] not in names:
                names.append(c["name"])
        for r in self.rows:
            for k in r:
                if k not in names and k not in ch.TIME_CHANNELS:
                    names.append(k)
        out, dropped_gps, dropped_ident = [], 0, 0
        picked = None
        if self.lv == 2:
            want = list(self.o.signals) if self.o.signals is not None else list(DEFAULT_SIGNALS)
            picked = [c for c in names if c in want or c.split("@")[0] in want]
        for c in names:
            if picked is not None and c not in picked:
                continue
            if identity_path(c):
                dropped_ident += 1
                continue
            gps = c.startswith("GPS_") or _HEADING_ALT.search(c.split("@")[0] or "")
            if gps and not (self.route and self.lv >= 3):
                dropped_gps += 1
                continue
            out.append(c)
        if dropped_gps:
            self.rep.add("R8", dropped_gps, "GPS, heading and altitude channels dropped")
        if dropped_ident:
            self.rep.add("R1", dropped_ident, "identity channels dropped")
        self.signals = [c.split("@")[0] for c in out]
        return out

    def _col_name(self, c: str) -> str:
        if "@" in c:
            path, dev = c.split("@", 1)
            return f"{path}@{self.ids.get('device', dev)}"
        return c

    def data_csv(self) -> None:
        cols = self.columns()
        real = self.basis == "real"
        header = [header_cell("Interval", "ms", 0)]
        if real:
            header.append(header_cell("Utc", "ms", 0))
        header += [header_cell(self._col_name(c), self.units.get(c, ch.UNITS.get(c, "")), 0)
                   for c in cols]
        buf = io.StringIO()
        buf.write(",".join(header) + "\n")
        w = csv.writer(buf, lineterminator="\n")
        coarsened = hidden_cells = 0
        n_rows = 0
        for r in self.rows:
            t = float(r.get("Interval") or 0)
            if not _in_windows(t, self.windows):
                continue
            vals = []
            has_fix = r.get("GPS_Latitude") is not None
            for c in cols:
                v = r.get(c)
                if c.startswith("GPS_") and has_fix and t not in self.visible_fix_t:
                    if v is not None:
                        hidden_cells += 1
                    v = None
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if _ODOMETER.search(c):
                        v, coarsened = (v // 1000) * 1000, coarsened + 1
                    elif _HOURS.search(c):
                        v, coarsened = (v // 100) * 100, coarsened + 1
                vals.append("" if v is None else v if isinstance(v, str) else fmt_num(v))
            rel = t if real else t - self.t0
            row = [fmt_num(rel)] + ([fmt_num(r["Utc"]) if _num(r.get("Utc")) is not None
                                     else ""] if real else []) + vals
            w.writerow(row)
            n_rows += 1
        buf_s = buf.getvalue()
        if hidden_cells:
            self.rep.add("R5", hidden_cells, "GPS cells of hidden fixes blanked")
        if coarsened:
            self.rep.add("R11", coarsened, "odometer (1,000 km) and hours (100 h) coarsened")
        self.files["data.csv"] = buf_s.encode()

    # -- faults, events, notes (R11, R13) ---------------------------------------------- #
    def fault_codes(self) -> "Dict[Tuple[str, str], List[float]]":
        seen: "Dict[Tuple[str, str], List[float]]" = {}
        for r in self.rows:
            t = float(r.get("Interval") or 0)
            if not _in_windows(t, self.windows if hasattr(self, "windows") else None):
                continue
            f = r.get("faults")
            if not isinstance(f, str) or not f.strip():
                continue
            for code in (s.strip() for s in f.split(";")):
                if code:
                    k = (str(r.get("module") or ""), code)
                    seen.setdefault(k, [t, t])[1] = t
        return seen

    def faults(self) -> None:
        out = []
        for (module, code), (a, b) in sorted(self.fault_codes().items()):
            for off in find_vins(code, self.o.wmi):
                raise ShareBlocked([Failure(2, "R3", f"VIN pattern in a fault text at {off}",
                                            "faults.json")])
            out.append({"module": module or None, "code": code,
                        "first_s": round((a - self.t0) / 1000, 3) if self.basis != "real" else None,
                        "last_s": round((b - self.t0) / 1000, 3) if self.basis != "real" else None})
        doc = {"faults": out, "freeze_frames": [], "readiness": None}
        self.files["faults.json"] = (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode()

    def events(self) -> None:
        lines, dropped = [], 0
        for ev in read_events(self.dir):
            t = float(ev.get("t") or 0)
            if not _in_windows(t, self.windows):
                continue
            kept = {"t": round(t - self.t0, 3) if self.basis != "real" else t}
            for k in EVENT_FIELDS:
                v = ev.get(k)
                if isinstance(v, (str, int, float, bool)) or v is None:
                    if k in ev:
                        kept[k] = v
            dropped += len([k for k in ev if k not in kept])
            lines.append(json.dumps(kept, ensure_ascii=False, sort_keys=True))
        if dropped:
            self.rep.add("R13", dropped, "event fields dropped (free text, ids, payloads)")
        self.files["events.jsonl"] = ("\n".join(lines) + ("\n" if lines else "")).encode()

    def notes(self) -> None:
        notes = read_notes(self.dir)
        lines, left = [], 0
        for n in notes:
            t = float(n.get("t") or 0)
            if not (self.o.include_notes and n.get("shareable") is True) or \
                    not _in_windows(t, self.windows):
                left += 1
                continue
            cap = n.get("capture") if isinstance(n.get("capture"), dict) else None
            out = {"id": f"note-{len(lines) + 1}", "t": round(t - self.t0, 3),
                   "t_end": None if n.get("t_end") is None else round(float(n["t_end"]) - self.t0, 3),
                   "kind": n.get("kind") or "note", "text": str(n.get("text") or ""),
                   "tags": list(n.get("tags") or [])}
            if cap:
                raw, hit = _scrub_hex_text(str(cap.get("raw") or ""), self.table)
                if hit:
                    self.rep.add("R1", 1, "identity bytes in a note capture scrubbed")
                out["capture"] = {k: cap.get(k) for k in ("module", "lid", "value")}
                out["capture"]["raw"] = raw
            lines.append(json.dumps(out, ensure_ascii=False, sort_keys=True))
        if left:
            self.rep.add("R13", left, "notes left out (not marked shareable or not ticked); "
                         "audio never")
        if lines:
            self.files["notes.jsonl"] = ("\n".join(lines) + "\n").encode()

    # -- the raw tap (R1, R2, R4, R9, R10) ---------------------------------------------- #
    def _stamp(self, r: TapRecord, tmap: TimeMap, first_us: int,
               t0_utc_us: "int | None") -> int:
        """A record's timestamp on the bundle's time base (µs)."""
        if self.basis == "real":
            return tmap.utc_ns(r.t_us) // 1000 if tmap else r.t_us
        if tmap and t0_utc_us is not None:
            return tmap.utc_ns(r.t_us) // 1000 - t0_utc_us
        return r.t_us - first_us

    def tap(self) -> None:
        """The scrubbed raw tap, one ``tap/bus<N>`` per (tap, bus) in order of first
        appearance; events (code only, ``time`` rebased) go with their tap's first bus."""
        taps = read_tap(self.dir, self.meta)
        self.tap_entries = taps
        counts = ScrubCounts()
        slots: "Dict[Tuple[int, int], dict]" = {}
        t0_utc_us = None
        if self.basis != "real" and self.rows:
            u = _utc_at(self.rows, self.meta, self.t0)
            t0_utc_us = None if u is None else int(u * 1000)
        for ti, (entry, records) in enumerate(taps):
            if isinstance(entry.get("device"), str):
                self.ids.get("device", entry["device"])
            if entry.get("boot_id") is not None:
                self.ids.get("boot", f"{entry.get('device')}:{entry.get('boot_id')}")
            buses = {b.get("idx"): b for b in entry.get("buses") or [] if isinstance(b, dict)}
            scrubbed, c = scrub_records(records, self.table,
                                        {k: str(b.get("bus_id")) for k, b in buses.items()
                                         if b.get("bus_id")})
            for f in ("identity", "isotp_frames", "unframed", "kept_scrubbed"):
                setattr(counts, f, getattr(counts, f) + getattr(c, f))
            if not any(not r.is_event for r in scrubbed):
                continue
            tmap = TimeMap(records)
            aligned = bool(tmap) and t0_utc_us is not None
            if self.windows is not None and not aligned:
                raise ShareRefused("the raw tap has no time marks to align with the visible "
                                   "trace: share it without location")
            if not aligned and self.basis != "real":
                self.tap_note = "the raw tap's time base is its first record (no time marks)"
            first_us = min(r.t_us for r in records)
            events = []
            for r in scrubbed:
                ts = self._stamp(r, tmap, first_us, t0_utc_us)
                if ts < 0 or (self.windows is not None
                              and not _in_windows(ts / 1000 + self.t0, self.windows)):
                    continue
                if r.is_event:
                    payload = cbor_t_us(ts) if is_time_event(r) and self.basis != "real" else b""
                    events.append(EventPacket(ts, r.dir, payload))
                    continue
                can = r.proto in (PROTO_CAN, PROTO_CAN_FD)
                slot = slots.setdefault((ti, r.bus), {"proto": "can" if can else "kline",
                                                      "packets": [], "events": []})
                slot["packets"].append((Packet(ts, r.payload, r.dir == DIR_TX_ECHO),
                                        r.proto == PROTO_CAN_FD))
            mine = sorted(k for k in slots if k[0] == ti)
            if mine:
                slots[mine[0]]["events"] += events
        self.rep.add("R1", counts.identity, "identity replies scrubbed (VIN, serials, "
                     "identification, seed/key, declared frames)")
        self.rep.add("R1", counts.kept_scrubbed, "records already scrubbed on the node or "
                     "Brain")
        self.rep.add("R2", counts.isotp_frames, "ISO-TP frames scrubbed")
        self.rep.add("R4", counts.unframed, "unframed records dropped")
        note = ("Timestamps are UTC." if self.basis == "real" else
                "Timestamps are relative: microseconds from the first visible sample, "
                "written from the Unix epoch.")
        for n, key in enumerate(sorted(slots)):
            slot = slots[key]
            if not slot["packets"]:
                continue
            pk = [p for p, _fd in slot["packets"]]
            self.files[f"tap/bus{n}.pcapng"] = write_pcapng(n, slot["proto"], pk,
                                                            slot["events"], note)
            if slot["proto"] == "can":
                self.files[f"tap/bus{n}.candump"] = write_candump(n, slot["packets"]).encode()

    # -- L4 diag ------------------------------------------------------------------------ #
    def diag(self) -> None:
        pack = self.meta.get("pack") if isinstance(self.meta.get("pack"), dict) else None
        fw = sorted({str(i.get("fw")) for i in (self.meta.get("device_info") or {}).values()
                     if isinstance(i, dict) and i.get("fw")})
        self.firmware = fw
        from ... import __version__ as platform_version  # noqa: PLC0415

        versions = {"pack": {"id": (pack or {}).get("id"), "version": (pack or {}).get("version")},
                    "platform_version": platform_version, "firmware_versions": fw}
        modules = []
        try:
            from ...pack import active_pack  # noqa: PLC0415

            p = active_pack()
            names = {m.id: m.name for m in p.modules}
            canon = p.canonical
        except Exception:  # noqa: BLE001
            names, canon = {}, (lambda x: x)
        for m in self.meta.get("modules") or []:
            cid = canon(m) or m
            entry = {"id": cid, "name": names.get(cid)}
            if entry not in modules:
                modules.append(entry)
        manifests = []
        for dev, info in sorted((self.meta.get("device_info") or {}).items()):
            if isinstance(info, dict):
                manifests.append({"device": self.ids.get("device", dev), "fw": info.get("fw")})
        stats = {}
        for i, (entry, _recs) in enumerate(getattr(self, "tap_entries", None) or []):
            stats[f"tap-{i + 1}"] = {k: entry.get(k) for k in
                                     ("records", "gaps", "lost", "overflow", "time_marks",
                                      "refused", "unlabelled", "first_seq_mismatch",
                                      "brain_scrubbed", "brain_dropped")}
            stats[f"tap-{i + 1}"]["buses"] = [{"proto": b.get("proto"), "baud": b.get("baud")}
                                              for b in entry.get("buses") or []
                                              if isinstance(b, dict)]
        r14 = 0
        files = {"diag/versions.json": versions, "diag/modules.json": {"modules": modules},
                 "diag/manifests.json": {"devices": manifests},
                 "diag/link_stats.json": {"taps": stats}}
        if self.o.config is not None:
            cfg, n = redact_json(dict(self.o.config))
            r14 += n
            files["diag/config.json"] = cfg
        for name, doc in files.items():
            red, n = redact_json(doc)
            r14 += n
            self.files[name] = (json.dumps(red, indent=1, ensure_ascii=False, sort_keys=True)
                                + "\n").encode()
        if self.o.log_tail is not None:
            text, n = redact_text(self.o.log_tail)
            r14 += n
            if self.basis != "real":
                text, k = _TIMES.subn(TIME_REDACTED, text)
                self.rep.add("R9", k, "log tail times and dates removed")
            self.files["diag/log_tail.txt"] = text.encode()
        if r14:
            self.rep.add("R14", r14, f"network identity values replaced with {REDACTED}")

    # -- README and share.json ---------------------------------------------------------- #
    def readme(self) -> None:
        o = self.o
        what = {"L0": "a trip card: rounded statistics only, no map",
                "L1": "a route: the trimmed, simplified trace with rounded statistics",
                "L2": "telemetry: the picked signals on relative time, faults seen",
                "L3": "a full log: every decoded channel and the scrubbed raw tap",
                "L4": "a diagnostics bundle: the full log plus versions, module info and "
                      "link statistics"}[o.level]
        removed = [f"- {r['rule']}: {r['detail']} ({r['count']})" for r in self.rep.list()]
        lines = [
            "Ostler share bundle (ostler.share/1)",
            "",
            f"Level {o.level}: {what}.",
            f"Time basis: {self.basis}. Location: {self.location}.",
            "",
            "What was removed or changed before this bundle was written:",
            *(removed or ["- nothing beyond the fixed rules"]),
            "- the VIN and identity replies never leave the owner's device (ADR-0036)",
            "- ids are fresh for this bundle; nothing here links to another bundle",
            "",
            "Integrity: every file's SHA-256 is listed in share.json. The bundle is not "
            "signed with any device key.",
            "Check it with: ostler share verify <this file>",
        ]
        if getattr(self, "tap_note", None):
            lines.append(f"Note: {self.tap_note}.")
        if o.contribution_consent:
            lines += ["", "Licence for derived data: decoded definitions and short labelled "
                      "snippets derived from this log may be published under CC BY-SA 4.0"
                      + (f", credited to {o.credit}" if o.credit else "")
                      + ". The log itself is never published."]
        else:
            lines += ["", "The owner has not consented to publishing anything derived from "
                      "this log."]
        self.files["README.txt"] = ("\n".join(lines) + "\n").encode()

    def manifest(self, bid: str, ran_day: str) -> dict:
        o = self.o
        pack = self.meta.get("pack") if isinstance(self.meta.get("pack"), dict) else None
        if pack is None:
            from ..node import pack_info  # noqa: PLC0415

            pack = pack_info()
        from ... import __version__ as platform_version  # noqa: PLC0415

        files = []
        for name in sorted(self.files):
            body = self.files[name]
            kind = FILES[name][1] if name in FILES else "tap"
            files.append({"path": name, "sha256": hashlib.sha256(body).hexdigest(),
                          "bytes": len(body), "kind": kind})
        consent = bool(o.contribution_consent)
        req = None
        if o.request:
            req = {k: o.request.get(k) for k in ("kind", "question", "symptoms", "module",
                                                  "fault_codes")}
        return {
            "format": FORMAT, "id": bid, "level": o.level, "created_day": ran_day,
            "expires": o.expires,
            "pack": {"id": (pack or {}).get("id"), "version": (pack or {}).get("version")},
            "platform_version": platform_version,
            "firmware_versions": getattr(self, "firmware", []) if self.lv == 4 else [],
            "vehicle": self.vehicle, "time_basis": self.basis, "location": self.location,
            "trim": {"ends_m": int(o.ends_m), "zones": self.vt.zones_hit},
            "signals": list(dict.fromkeys(self.signals)) if self.lv >= 2 else [],
            "files": files, "redactions": self.rep.list(),
            "verifier": {"version": VERIFIER_VERSION, "passed": True, "ran_day": ran_day},
            "request": req,
            "licence": {"derived_data": "CC-BY-SA-4.0" if consent else None},
            "contribution_consent": consent,
            "credit": (str(o.credit) if o.credit and consent else None),
        }

    def run(self) -> "Tuple[dict, Dict[str, bytes]]":
        self.trace()
        self.signals: "List[str]" = []
        self.vehicle = self._vehicle()
        trip = self.trip()
        if self.lv >= 1 and self.route:
            self.tracks()
        if self.lv >= 2:
            self.data_csv()
            self.faults()
            self.notes()
        if self.lv >= 3:
            self.events()
            self.tap()
        if self.lv == 4:
            self.diag()
        if self.basis == "relative":
            self.rep.add("R9", 1, "relative time: t = 0 at the first visible sample")
        elif self.basis == "day":
            self.rep.add("R9", 1, "day only: no start time, no point times")
        self.rep.add("R10", 1, "ids re-minted for this bundle")
        self.files["trip.json"] = (json.dumps(trip, indent=1, ensure_ascii=False,
                                              sort_keys=True) + "\n").encode()
        self.readme()
        return trip, self.files


def _card_round(fine: dict) -> dict:
    """L0 figures from the L1 figures (§5.4), so an L0 and an L1 of one trip agree: the L0
    distance is the L1 distance rounded to 1 km."""
    def half_up(v, step):
        if v is None:
            return None
        import math

        r = math.floor(v / step + 0.5) * step
        return int(r)
    return {"distance_km": half_up(fine.get("distance_km"), 1),
            "duration_min": half_up(fine.get("duration_min"), 5),
            "moving_min": half_up(fine.get("moving_min"), 5),
            "avg_kmh": half_up(fine.get("avg_kmh"), 5),
            "max_kmh": half_up(fine.get("max_kmh"), 5)}


def zip_bytes(files: "Mapping[str, bytes]") -> bytes:
    """The bundle zip: sorted paths, deflate, entry times 1980-01-01 00:00, no comments,
    no extra fields, no directory entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[name])
    return buf.getvalue()


def build_share(session_dir: str, options: ShareOptions, *,
                table: "IdentityTable | None" = None, clock=time.time,
                tz_offset_s: "int | None" = None, owner: "OwnerContext | None" = None
                ) -> ShareBundle:
    """Build and verify one share of a recorded session. Raises :class:`ShareRefused` for a
    request that breaks a rule and :class:`ShareBlocked` when the verifier fails."""
    check_policy(options)
    if table is None:
        from ...pack import active_identity_table  # noqa: PLC0415

        table = active_identity_table()
    b = _Builder(session_dir, options, table, clock(), tz_offset_s)
    _trip, files = b.run()
    bid = bundle_id()
    ran_day = _local_day(clock() * 1000, tz_offset_s) or time.strftime("%Y-%m-%d")
    manifest = b.manifest(bid, ran_day)
    files = dict(files)
    files["share.json"] = (json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True)
                           + "\n").encode()
    data = zip_bytes(files)
    if owner is None:
        owner = OwnerContext(zones=list(options.zones),
                             hidden_fixes=[(p.lat, p.lon) for p in b.vt.trimmed])
    res = verify_bytes(data, table=table, wmi=options.wmi, owner=owner)
    if not res.ok:
        raise ShareBlocked(res.failures or [Failure(1, "R16", res.error or "unreadable")])
    return ShareBundle(f"ostler-share-{file_tag()}.zip", data, manifest,
                       b.ids.owner_record(), manifest["redactions"], res, owner)


def write_share(bundle: ShareBundle, out_dir: str) -> str:
    """Save a verified bundle (the File path) and return its path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, bundle.name)
    with open(path, "xb") as fh:
        fh.write(bundle.data)
    return path


__all__ = ["AUDIENCES", "PATHS", "ShareBlocked", "ShareBundle", "ShareOptions", "ShareRefused",
           "build_share", "check_policy", "write_share", "zip_bytes"]
