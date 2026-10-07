# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``ostler share verify``: the gate every share passes on its final bytes (trip-sharing
spec §9.3; R16). The bundle writer runs it and refuses to hand on a bundle that fails;
every delivery path re-runs it.

:func:`verify_bytes` / :func:`verify_bundle` return a :class:`VerifyResult` with exit code
0 (pass), 1 (fail, naming each failing check and its rule) or 2 (unreadable or not
``ostler.share/1``). The eight checks:

1. a file not in ``files``, a file listed but missing, a hash or size mismatch, an unknown
   top-level path, an entry time other than 1980-01-01 00:00 (and the zip shape: no
   directories, extra fields or comments, sorted paths);
2. a VIN pattern, a declared identity service or DID, or a seed/key exchange with data, in
   any file (R1–R3), inside reassembled ISO-TP too;
3. an ``unframed`` record in a tap file (R4): a K-line packet that does not frame, or a tap
   file that does not parse;
4. GPS, altitude, heading or ``Utc`` when ``location`` is ``none``; a point timestamp in a
   route; a route fix inside a privacy zone or the hidden ends (only with the owner's
   :class:`OwnerContext`, which knows them);
5. a timestamp, date or ULID outside ``time_basis``;
6. a MAC, IP, SSID, certificate fingerprint, bearer token or peer key anywhere (R14);
7. a level-content mismatch (a tap file in L2, ``data.csv`` in L0, a ``diag/`` file below L4);
8. a ``share.json`` with a forbidden or unknown field (VIN, HMAC, device id, user id).

Pure stdlib (``jsonschema`` is dev-only; ``schemas/share.schema.json`` is checked against the
same rules in the tests).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from ...node.identity import IdentityTable, is_placeholder, kline_data_offset, kline_frame_ok
from ..recorder import haversine_m, parse_header
from .capture import read_candump, read_pcapng, socketcan_to_tap
from .detect import find_vins, json_declared_hits, json_strings, network_hits
from .scrub import can_fields, isotp_messages, kline_legacy_scrubbed, message_keep

FORMAT = "ostler.share/1"
VERIFIER_VERSION = "1"
LEVELS = ("L0", "L1", "L2", "L3", "L4")
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
TIME_BASES = ("day", "relative", "real")
LOCATIONS = ("none", "coarse", "route")
EV_TIME = 6
LINKTYPE_USER0, LINKTYPE_USER1, LINKTYPE_SOCKETCAN = 147, 148, 227
RELATIVE_LIMIT_US = 946_684_800 * 1_000_000      # a relative stamp stays before 2000

# file → (lowest level, kind)
FILES = {
    "README.txt": (0, "readme"), "trip.json": (0, "summary"), "card.png": (0, "image"),
    "track.geojson": (1, "route"), "track.gpx": (1, "route"),
    "data.csv": (2, "data"), "faults.json": (2, "faults"), "notes.jsonl": (2, "notes"),
    "events.jsonl": (3, "events"),
    "diag/versions.json": (4, "diag"), "diag/modules.json": (4, "diag"),
    "diag/manifests.json": (4, "diag"), "diag/link_stats.json": (4, "diag"),
    "diag/log_tail.txt": (4, "diag"), "diag/config.json": (4, "diag"),
}
TAP_FILE = re.compile(r"^tap/bus(0|[1-9][0-9]{0,2})\.(pcapng|candump)$")
REQUIRED = ("README.txt", "trip.json")

SHARE_KEYS = {
    "format", "id", "level", "created_day", "expires", "pack", "platform_version",
    "firmware_versions", "vehicle", "time_basis", "location", "trim", "signals", "files",
    "redactions", "verifier", "request", "licence", "contribution_consent", "credit",
}
SHARE_REQUIRED = SHARE_KEYS - {"credit", "request", "expires"}
VEHICLE_KEYS = {"make", "model", "year", "engine", "market", "kind", "nickname", "plate"}
FORBIDDEN_KEYS = {"vin", "masked_vin", "vin_masked", "vin_hmac", "hmac", "device", "device_id",
                  "devices", "boot_id", "user_id", "user", "vid", "session_id", "session",
                  "brain_key", "key_id", "kid", "signature", "sig"}
# share.json values that are versions, not addresses (check 6 skips them)
_VERSION_PATHS = re.compile(r"^(platform_version|firmware_versions\[\d+\]|pack\.version|verifier\.version)$")

_ISO_DATE = re.compile(r"(?<!\d)(?:19|20)\d\d-[01]\d-[0-3]\d(?!\d)")
_ISO_DATETIME = re.compile(r"(?<!\d)\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d")
_CLOCK = re.compile(r"(?<![\d:])[0-2]\d:[0-5]\d(?::[0-5]\d)?(?![\d:])")
_ULID = re.compile(r"(?<![0-9A-Z])[0-9A-HJKMNP-TV-Z]{26}(?![0-9A-Z])")
_HEX_TEXT = re.compile(r"^[0-9A-Fa-f]{2}(?: [0-9A-Fa-f]{2})+$")
_TIME_KEYS = {"utc", "utc_ns", "utc_ms", "start_utc", "end_utc", "ts_utc", "created",
              "edited", "since_utc", "time"}
_LOCATION_KEYS = {"lat", "lon", "latitude", "longitude", "altitude", "heading", "start_pos",
                  "end_pos", "bbox", "position", "coordinates"}
_REGION_KEYS = {"region", "start_region", "end_region", "place", "place_start", "place_end"}
_GPS_COL = re.compile(r"^(GPS_|Utc$)|(Latitude|Longitude|Altitude|Heading)", re.IGNORECASE)


class VerifyError(Exception):
    """The file is unreadable or not an ``ostler.share/1`` bundle (exit 2)."""


@dataclass
class Failure:
    check: int
    rule: str
    detail: str
    file: Optional[str] = None


@dataclass
class OwnerContext:
    """What only the owner's device knows: its privacy zones and the fixes the ends trim
    hid (``(lat, lon)``), for check 4's route-fix test."""

    zones: Sequence[Any] = ()
    hidden_fixes: Sequence[Tuple[float, float]] = ()


@dataclass
class VerifyResult:
    failures: "List[Failure]" = field(default_factory=list)
    level: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.failures

    @property
    def exit_code(self) -> int:
        return 2 if self.error is not None else (1 if self.failures else 0)

    def to_json(self) -> dict:
        return {"passed": self.ok, "exit_code": self.exit_code, "level": self.level,
                "error": self.error, "failures": [asdict(f) for f in self.failures]}

    def report(self) -> str:
        if self.error is not None:
            return f"unreadable: {self.error}"
        if self.ok:
            return f"passed ({self.level})"
        lines = [f"failed ({self.level}): {len(self.failures)} problem(s)"]
        for f in self.failures:
            where = f" [{f.file}]" if f.file else ""
            lines.append(f"  check {f.check} ({f.rule}){where}: {f.detail}")
        return "\n".join(lines)


class _Checker:
    def __init__(self, table: IdentityTable, wmi: "str | None", owner: "OwnerContext | None"):
        self.table, self.wmi, self.owner = table, wmi, owner
        self.failures: "List[Failure]" = []

    def fail(self, check: int, rule: str, detail: str, file: "str | None" = None) -> None:
        self.failures.append(Failure(check, rule, detail, file))

    # ---- shared ------------------------------------------------------------------------ #
    def vin_text(self, name: str, text: str, where: str = "") -> None:
        for off in find_vins(text, self.wmi):
            self.fail(2, "R3", f"VIN pattern in {where} at offset {off}" if where
                      else f"VIN pattern at offset {off}", name)

    def vin_bytes(self, name: str, data: bytes, where: str) -> None:
        for off in find_vins(data, self.wmi):
            self.fail(2, "R3", f"VIN pattern in {where} at byte {off}", name)

    def hex_identity(self, name: str, text: str, where: str) -> None:
        if _HEX_TEXT.match(text.strip()):
            msg = bytes.fromhex(text.replace(" ", ""))
            k = self.table.match(msg)
            if k and not is_placeholder(msg[k:]):
                self.fail(2, "R1", f"identity message in {where}", name)

    def network(self, name: str, text: str, where: str = "") -> None:
        for kind, off in network_hits(text):
            self.fail(6, "R14", f"{kind} at {where + ' ' if where else ''}offset {off}", name)

    def times(self, name: str, text: str, basis: str, where: str = "") -> None:
        w = f" in {where}" if where else ""
        if basis == "relative":
            if _ISO_DATE.search(text):
                self.fail(5, "R9", f"a date{w} in a relative-time bundle", name)
        if basis in ("relative", "day"):
            if _ISO_DATETIME.search(text) or _CLOCK.search(text):
                self.fail(5, "R9", f"a time of day{w} in a {basis} bundle", name)
        if _ULID.search(text):
            self.fail(5, "R10", f"a ULID{w}", name)

    def text_file(self, name: str, text: str, basis: str) -> None:
        self.vin_text(name, text)
        self.network(name, text)
        self.times(name, text, basis)

    def json_doc(self, name: str, doc: Any, basis: str, location: str) -> None:
        for path, s in json_strings(doc):
            self.vin_text(name, s, path)
            self.hex_identity(name, s, path)
            if not (name == "share.json" and _VERSION_PATHS.match(path)):
                self.network(name, s, path)
            if name != "share.json":
                self.times(name, s, basis, path)
        for path in json_declared_hits(doc):
            self.fail(6, "R14", f"declared network key {path} is not redacted", name)
        if name == "share.json":
            return
        for path, key in _json_keys(doc):
            k = key.lower()
            if basis != "real" and k in _TIME_KEYS:
                self.fail(5, "R9", f"time field {path} in a {basis} bundle", name)
            if location == "none" and (k in _LOCATION_KEYS or k in _REGION_KEYS):
                self.fail(4, "R8", f"location field {path} with location none", name)
            if location == "coarse" and k in _LOCATION_KEYS:
                self.fail(4, "R8", f"position field {path} with location coarse", name)

    # ---- tap files --------------------------------------------------------------------- #
    def can_frames(self, name: str, frames: "Sequence[Tuple[int, int, bool, bytes]]") -> None:
        """``(index, can id, extended, data)`` on one bus."""
        diag, other = [], {}
        for idx, cid, ext, data in frames:
            self.vin_bytes(name, data, f"frame {idx}")
            if self.table.is_diagnostic_id(cid, ext):
                diag.append((idx, (cid, ext), data))
            else:
                other.setdefault((cid, ext), []).append((idx, data))
                bc = self.table.broadcast_frame(None, cid, data)
                if bc is not None and len(data) > len(bc.prefix) and \
                        not is_placeholder(data[len(bc.prefix):]):
                    self.fail(2, "R1", f"declared identity frame {cid:X} at frame {idx} not "
                                       "scrubbed", name)
        for m in isotp_messages(diag):
            first = m.parts[0][0]
            self.vin_bytes(name, bytes(m.data), f"ISO-TP message from frame {first}")
            k = message_keep(m, self.table)
            if k is not None and not is_placeholder(bytes(m.data[k:])):
                what = "identity message" if m.complete else "unreassembled ISO-TP message"
                self.fail(2, "R2" if m.multi else "R1",
                          f"{what} on {m.key[0]:X} from frame {first} is not scrubbed", name)
        for (cid, _ext), items in other.items():
            for strip in (0, 1):
                joined = b"".join(d[strip:] for _i, d in items)
                for off in find_vins(joined, self.wmi):
                    pos, idx = 0, items[0][0]
                    for i, d in items:
                        if pos + len(d) - strip > off:
                            idx = i
                            break
                        pos += len(d) - strip
                    self.fail(2, "R3", f"VIN pattern spelled across frames of CAN id {cid:X} "
                                       f"(frame {idx}, offset {off})", name)

    def kline_packets(self, name: str, packets: "Sequence[Tuple[int, bytes]]") -> None:
        for idx, msg in packets:
            self.vin_bytes(name, msg, f"frame {idx}")
            if kline_frame_ok(msg):
                d = kline_data_offset(msg)
                data = msg[d:-1]
                k = self.table.match(data)
                if k and not is_placeholder(data[k:]):
                    self.fail(2, "R1", f"identity reply at frame {idx} is not scrubbed", name)
            elif not kline_legacy_scrubbed(msg, self.table):
                self.fail(3, "R4", f"frame {idx} does not frame (unframed record)", name)

    def stamps(self, name: str, stamps: "Iterable[int]", basis: str) -> None:
        if basis == "relative" and any(t >= RELATIVE_LIMIT_US for t in stamps):
            self.fail(5, "R9", "a timestamp outside relative time", name)

    def pcapng(self, name: str, data: bytes, basis: str) -> None:
        try:
            cap = read_pcapng(data)
        except ValueError as exc:
            self.fail(3, "R4", f"tap file does not parse: {exc}", name)
            return
        for s in cap.strings:
            self.text_file(name, s, basis)
        self.stamps(name, (t for _i, t, _d in cap.packets), basis)
        kline, can = [], []
        for n, (iface, _t, pkt) in enumerate(cap.packets):
            lt = cap.linktypes[iface]
            if lt == LINKTYPE_USER0:
                kline.append((n, pkt))
            elif lt == LINKTYPE_SOCKETCAN:
                try:
                    raw, ext, cid, d = can_fields(socketcan_to_tap(pkt))
                except ValueError:
                    self.fail(3, "R4", f"packet {n} is not a SocketCAN frame", name)
                    continue
                can.append((n, cid, ext, d))
            elif lt == LINKTYPE_USER1:
                if pkt[:1] == bytes([EV_TIME]) and basis != "real" and b"utc_ns" in pkt:
                    self.fail(5, "R9", f"time event {n} keeps utc_ns", name)
            else:
                self.fail(3, "R4", f"unknown link type {lt}", name)
        self.kline_packets(name, kline)
        self.can_frames(name, can)

    def candump(self, name: str, text: str, basis: str) -> None:
        try:
            frames = read_candump(text)
        except ValueError as exc:
            self.fail(3, "R4", f"candump does not parse: {exc}", name)
            return
        self.stamps(name, (t for t, *_ in frames), basis)
        for _t, iface, *_ in frames:
            if not re.match(r"^bus\d+$", iface):
                self.fail(6, "R14", f"interface name {iface!r} is not a bus ordinal", name)
                break
        self.can_frames(name, [(i, cid, ext, d) for i, (_t, _f, cid, ext, d) in enumerate(frames)])

    # ---- location ---------------------------------------------------------------------- #
    def route(self, name: str, text: str, location: str) -> "List[Tuple[float, float]]":
        if location != "route":
            self.fail(4, "R8", "a route file with location " + location, name)
        pts: "List[Tuple[float, float]]" = []
        if name.endswith(".gpx"):
            if "<time" in text:
                self.fail(4, "R7", "a point timestamp in the route", name)
            for m in re.finditer(r'<trkpt lat="([-0-9.]+)" lon="([-0-9.]+)"', text):
                pts.append((float(m.group(1)), float(m.group(2))))
        else:
            try:
                doc = json.loads(text)
            except ValueError:
                self.fail(4, "R7", "route GeoJSON does not parse", name)
                return pts
            for f in doc.get("features") or [] if isinstance(doc, dict) else []:
                if f.get("properties"):
                    self.fail(4, "R7", "route GeoJSON carries properties (point times?)", name)
                g = f.get("geometry") or {}
                if g.get("type") != "MultiLineString":
                    self.fail(4, "R7", "route geometry is not a MultiLineString", name)
                    continue
                for line in g.get("coordinates") or []:
                    pts += [(float(c[1]), float(c[0])) for c in line]
        if self.owner is not None:
            for lat, lon in pts:
                if any(z.contains(lat, lon) for z in self.owner.zones):
                    self.fail(4, "R5", f"route fix {lat:.5f},{lon:.5f} inside a privacy zone", name)
                    break
            for lat, lon in pts:
                if any(haversine_m(lat, lon, a, b) < 1.5 for a, b in self.owner.hidden_fixes):
                    self.fail(4, "R5", f"route fix {lat:.5f},{lon:.5f} inside the ends trim", name)
                    break
        return pts

    def data_csv(self, name: str, text: str, basis: str, location: str, level: int) -> None:
        lines = text.split("\n")
        header = parse_header(lines[0]) if lines else []
        if not header or header[0][0] != "Interval":
            self.fail(7, "R16", "data.csv is not a logbook CSV", name)
            return
        cols = [h[0] for h in header]
        for c in cols:
            self.vin_text(name, c, "header")
            self.network(name, c, "header")
            if _ULID.search(c):
                self.fail(5, "R10", f"a ULID in column {c!r}", name)
        for c in cols:
            if c == "Utc" and basis != "real":
                self.fail(5, "R9", "a Utc column outside real time", name)
            elif _GPS_COL.search(c) and c != "Utc" and (location != "route" or level < 3):
                self.fail(4, "R8", f"location column {c!r} "
                          + ("with location none" if location != "route"
                             else "at L2 (a route carries no point times)"), name)
        for i, row in enumerate(csv.reader(lines[1:]), 2):
            for cell in row:
                if cell and not _is_number(cell):
                    self.vin_text(name, cell, f"line {i}")
                    self.hex_identity(name, cell, f"line {i}")
                    self.network(name, cell, f"line {i}")
                    self.times(name, cell, basis, f"line {i}")

    def png(self, name: str, data: bytes) -> None:
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            self.fail(7, "R12", "card.png is not a PNG", name)
            return
        off = 8
        while off + 8 <= len(data):
            ln = int.from_bytes(data[off:off + 4], "big")
            ctype = data[off + 4:off + 8]
            if ctype in (b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"):
                self.fail(6, "R12", f"card.png carries a {ctype.decode()} chunk", name)
            off += 12 + ln


def _json_keys(obj: Any, path: str = "") -> "Iterable[Tuple[str, str]]":
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            yield p, str(k)
            yield from _json_keys(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _json_keys(v, f"{path}[{i}]")


def _is_number(cell: str) -> bool:
    try:
        float(cell)
        return True
    except ValueError:
        return False


def check_share_json(doc: Any) -> "List[Failure]":
    """Check 8: the manifest's fields and types (the rules ``schemas/share.schema.json``
    states)."""
    out: "List[Failure]" = []

    def bad(detail: str) -> None:
        out.append(Failure(8, "R16", detail, "share.json"))

    if not isinstance(doc, dict):
        bad("share.json is not an object")
        return out
    for path, key in _json_keys(doc):
        if key.lower() in FORBIDDEN_KEYS:
            bad(f"forbidden field {path}")
    for k in sorted(set(doc) - SHARE_KEYS):
        bad(f"unknown field {k}")
    for k in sorted(SHARE_REQUIRED - set(doc)):
        bad(f"missing field {k}")
    if not (isinstance(doc.get("id"), str) and re.fullmatch(r"[0-9a-f]{32}", doc["id"])):
        bad("id is not 32 hex characters")
    if doc.get("level") not in LEVELS:
        bad("level is not L0 to L4")
    if doc.get("time_basis") not in TIME_BASES:
        bad("time_basis is not day, relative or real")
    if doc.get("location") not in LOCATIONS:
        bad("location is not none, coarse or route")
    if not (isinstance(doc.get("created_day"), str)
            and re.fullmatch(r"\d{4}-\d\d-\d\d", doc["created_day"])):
        bad("created_day is not a date")
    v = doc.get("vehicle")
    if not isinstance(v, dict) or set(v) - VEHICLE_KEYS:
        bad("vehicle has fields other than make, model, year, engine, market, kind, "
            "nickname, plate")
    elif v.get("kind") not in ("car", "motorcycle", None):
        bad("vehicle.kind is not car or motorcycle")
    trim = doc.get("trim")
    if not isinstance(trim, dict) or set(trim) - {"ends_m", "zones"}:
        bad("trim has fields other than ends_m and zones")
    if not isinstance(doc.get("files"), list):
        bad("files is not a list")
    if not isinstance(doc.get("redactions"), list):
        bad("redactions is not a list")
    ver = doc.get("verifier")
    if not isinstance(ver, dict) or set(ver) - {"version", "passed", "ran_day"}:
        bad("verifier has fields other than version, passed, ran_day")
    lic = doc.get("licence")
    if not isinstance(lic, dict) or lic.get("derived_data") not in ("CC-BY-SA-4.0", None):
        bad("licence.derived_data is not CC-BY-SA-4.0 or null")
    if not isinstance(doc.get("contribution_consent"), bool):
        bad("contribution_consent is not a boolean")
    elif not doc["contribution_consent"] and isinstance(lic, dict) and lic.get("derived_data"):
        bad("a derived-data licence without contribution consent")
    req = doc.get("request")
    if req is not None and (not isinstance(req, dict) or req.get("kind") not in
                            ("decode", "diagnose", "show")):
        bad("request.kind is not decode, diagnose or show")
    return out


def verify_bytes(data: bytes, *, table: "IdentityTable | None" = None,
                 wmi: "str | None" = None, owner: "OwnerContext | None" = None) -> VerifyResult:
    """Run every check on a bundle's bytes."""
    if table is None:
        from ...pack import active_identity_table

        table = active_identity_table()
    res = VerifyResult()
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        infos = zf.infolist()
        names = [i.filename for i in infos]
        if "share.json" not in names:
            raise VerifyError("no share.json: not an ostler.share/1 bundle")
        doc = json.loads(zf.read("share.json").decode("utf-8"))
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, ValueError, KeyError) as exc:
        res.error = str(exc) or type(exc).__name__
        return res
    except VerifyError as exc:
        res.error = str(exc)
        return res
    if not isinstance(doc, dict) or not isinstance(doc.get("format"), str) or \
            doc["format"].split("/")[0] != "ostler.share" or doc["format"] != FORMAT:
        res.error = f"format {doc.get('format') if isinstance(doc, dict) else None!r} is not {FORMAT}"
        return res
    res.level = doc.get("level") if doc.get("level") in LEVELS else None
    ck = _Checker(table, wmi, owner)
    ck.failures += check_share_json(doc)
    level = LEVELS.index(res.level) if res.level else 4
    basis = doc.get("time_basis") if doc.get("time_basis") in TIME_BASES else "relative"
    location = doc.get("location") if doc.get("location") in LOCATIONS else "none"

    # check 1: the zip and the file list
    if zf.comment:
        ck.fail(1, "R16", "the zip has a comment")
    if names != sorted(names):
        ck.fail(1, "R16", "zip entries are not in sorted order")
    if len(set(names)) != len(names):
        ck.fail(1, "R16", "duplicate zip entries")
    listed = {}
    for f in doc.get("files") or [] if isinstance(doc.get("files"), list) else []:
        if isinstance(f, dict) and isinstance(f.get("path"), str):
            listed[f["path"]] = f
    for info in infos:
        n = info.filename
        if info.date_time != ZIP_TIME:
            ck.fail(1, "R9", f"entry time {info.date_time} is not 1980-01-01 00:00", n)
        if info.is_dir() or info.extra or info.comment:
            ck.fail(1, "R16", "a directory, extra field or entry comment", n)
        if n == "share.json":
            continue
        if n not in FILES and not TAP_FILE.match(n):
            ck.fail(1, "R16", "unknown path", n)
        if n not in listed:
            ck.fail(1, "R16", "file not listed in share.json", n)
            continue
        body = zf.read(n)
        f = listed[n]
        if f.get("sha256") != hashlib.sha256(body).hexdigest() or f.get("bytes") != len(body):
            ck.fail(1, "R16", "hash or size mismatch", n)
    for n in listed:
        if n not in names:
            ck.fail(1, "R16", "listed in share.json but missing", n)
    for n in REQUIRED:
        if n not in names:
            ck.fail(7, "R16", "required file missing", n)

    # check 7: level content
    for n in names:
        if n == "share.json":
            continue
        lowest = FILES[n][0] if n in FILES else (3 if TAP_FILE.match(n) else None)
        if lowest is not None and level < lowest:
            ck.fail(7, "R16", f"not allowed at {res.level}", n)
    if res.level == "L1" and location != "route":
        ck.fail(7, "R16", "an L1 bundle without a route")
    if res.level in ("L0", "L1") and basis != "day":
        ck.fail(5, "R9", f"{res.level} must use the day time basis")
    if level >= 2 and basis == "day":
        ck.fail(5, "R9", f"{res.level} must use relative or real time")
    if location == "route" and res.level == "L0":
        ck.fail(7, "R16", "an L0 card with a route")

    ck.json_doc("share.json", doc, basis, location)
    for n in names:
        if n == "share.json":
            continue
        body = zf.read(n)
        if n == "card.png":
            ck.png(n, body)
            continue
        if n.endswith(".pcapng"):
            ck.pcapng(n, body, basis)
            continue
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            ck.fail(1, "R16", "not UTF-8 text", n)
            continue
        if n.endswith(".candump"):
            ck.candump(n, text, basis)
        elif n in ("track.gpx", "track.geojson"):
            ck.route(n, text, location)
            ck.network(n, text)
            ck.times(n, text, basis if basis != "day" else "day")
        elif n == "data.csv":
            ck.data_csv(n, text, basis, location, level)
        elif n.endswith(".json"):
            try:
                ck.json_doc(n, json.loads(text), basis, location)
            except ValueError:
                ck.fail(1, "R16", "JSON does not parse", n)
        elif n.endswith(".jsonl"):
            for i, line in enumerate(text.splitlines(), 1):
                try:
                    ck.json_doc(n, json.loads(line), basis, location)
                except ValueError:
                    ck.fail(1, "R16", f"line {i} is not JSON", n)
        else:
            ck.text_file(n, text, basis)
    res.failures = ck.failures
    return res


def verify_bundle(path: str, **kw) -> VerifyResult:
    """:func:`verify_bytes` on a file; an unreadable path is exit 2."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        return VerifyResult(error=f"cannot read {path}: {exc.strerror or exc}")
    return verify_bytes(data, **kw)


__all__ = ["FILES", "FORMAT", "Failure", "LEVELS", "OwnerContext", "TAP_FILE", "VERIFIER_VERSION",
           "VerifyError", "VerifyResult", "ZIP_TIME", "check_share_json", "verify_bundle",
           "verify_bytes"]
