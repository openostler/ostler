# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""HTTP + SSE server for the dashboard (stdlib, no external dependencies).

A background thread polls the data source and updates ``latest``; ``/events``
streams it via Server-Sent Events. ``/command`` runs server commands and module actions;
every module action passes the command gate (:func:`openostler.commands.refusal`, ADR-0008)
first. ``/catalog`` serves the per-module UI catalog (specs/2026-10-05-ui-overhaul-design.md).
``/sessions*`` serves the always-on session logbook (specs/2026-10-05-session-logbook-design.md,
ADR-0009); the poll loop feeds every snapshot (plus the GPS fix) to the ``SessionRecorder``.
The replay routes (session events, notes, audio, acceleration, ``/captures``) and the
``recording_options`` command follow specs/2026-10-05-replay-notes-capture-design.md
(ADR-0010): public mode refuses every write and never serves audio, and synthetic
sessions are read-only. Logs at scale (specs/2026-10-06-logs-at-scale-design.md, ADR-0011):
there is no demo mode (the sources are always the car; tests inject fakes); ``/sessions``
is keyset-paged and filtered through the SQLite ``SessionIndex``, ``/sessions/histogram``
feeds the scrubber, ``PATCH /sessions/<id>`` edits name/description; live notes and
``split_session`` are refused (409) unless a session is ``recording``; closed sessions'
start/end points go to the optional OSM enricher (``--geocoder``).
"""
from __future__ import annotations

import base64
import hmac
import ipaddress
import json
import mimetypes
import os
import queue
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from ..kwp2000.kwp2000 import NegativeResponse
from ..pack import active_pack, canonical_module
from ..ports import list_serial_ports, resolve_serial_port
from ..timefmt import rfc3339_utc
from .docs import DocLibrary
from .kline_cmds import PROBE_COMMANDS, KLineCommandsMixin
from .sources import DataSource


# Session ids are directory names (``YYYYMMDDTHHMMSSZ[-N]``, demo ids alike): anything else
# is answered 404 before it reaches the store (no path traversal through the URL).
_SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")
_EXPORT_FORMATS = ("csv", "vbo", "gpx", "geojson", "notes", "pcapng")
_DEFAULT_MAX_POINTS = 2000

# ---- replay API (ADR-0010) ---- #
_NOTE_ID = re.compile(r"^[0-9a-f]{8}$")
_TRACK_ID = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,63}$")  # = logbook.audio.TRACK_RE
_NOTE_KINDS = ("mark", "note", "capture")
_NOTE_SOURCES = ("live", "retro")
_NOTE_TEXT_MAX = 2000
_NOTE_TAGS_MAX = 16
_AUDIO_CHUNK_MAX = 2 * 1024 * 1024   # bytes per POSTed audio chunk
_JSON_BODY_MAX = 2 * 1024 * 1024     # bytes of a JSON body on the replay routes
_ACCEL_SAMPLES_MAX = 5000            # samples per POST /accel
_ACCEL_HZ = (10, 25, 50)
_PUBLIC_REFUSAL = "not available in public mode"
# Live notes / split need an open session in the "recording" state (ADR-0011).
NOT_RECORDING = "Not recording — connect to the car first"
_NAME_MAX = 80
_DESCRIPTION_MAX = 2000
_PAGE_LIMIT_MAX = 200
_INDEX_WAIT_S = 5.0         # a /sessions request waits this long for a building index
_INDEX_RESYNC_S = 30.0      # the recording session's index row is refreshed this often
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYNTHETIC_REFUSAL = "synthetic sessions are read-only"
# Command actions whose outcome text could carry an identity payload: only {action, ok}
# reaches the events stream (spec §1 — the VIN never lands in a session).
_IDENTITY_ACTION = re.compile(r"identity|vin|eka|serial", re.IGNORECASE)


class _NoSuchError(Exception):
    """Stands in for ``logbook.recorder.NotRecording`` if the recorder lacks it."""


def _not_recording_error() -> "type[Exception]":
    """``logbook.recorder.NotRecording`` (raised by ``note``/``split`` while paused)."""
    try:
        from ..logbook.recorder import NotRecording
        return NotRecording
    except ImportError:
        return _NoSuchError


# ---- errors (specs/2026-10-06-api-consistency-design.md §1-§2) ---- #
# Every API error body is ``{ok: false, error, code?}``: ``error`` is an English sentence
# for people, ``code`` a stable token for programs. ``_STATUS_FOR_CODE`` maps a ``code`` to
# its HTTP status (a ``/command`` reply with ``ok: false`` and no ``code`` answers 400).
_STATUS_FOR_CODE = {
    "bad_request": 400,
    "no_match": 400,          # /automap: valid samples, no raw field explains them
    "auth_required": 401,
    "public_mode": 403,       # refused on the public server (_PUBLIC_REFUSAL)
    "not_local": 403,         # an owner action asked over a remote path (Remove device)
    "read_only": 403,         # a write to a synthetic (demo) session
    "not_found": 404,
    "not_recording": 409,
    "disconnected": 409,
    "community_off": 409,     # community disabled on this server, or sharing not enabled
    "conflict": 409,          # another conflict with server state (shutdown not enabled …)
    "too_large": 413,
    "internal": 500,
    "car_refused": 502,       # the ECU answered with a negative response (0x7F + NRC)
    "unavailable": 503,
    "car_timeout": 504,       # no answer from the poll thread in time
}
# The code an error gets when its producer names none.
_CODE_FOR_STATUS = {400: "bad_request", 401: "auth_required", 403: "public_mode",
                    404: "not_found", 409: "conflict", 413: "too_large", 500: "internal",
                    502: "car_refused", 503: "unavailable", 504: "car_timeout"}
# "NegativeResponse: negative response to service 0x31: NRC 0x22 (…)": how a source that
# catches its own exceptions reports the ECU's refusal (kwp2000.NegativeResponse).
_NRC_TEXT = re.compile(r"\bNegativeResponse\b.*?NRC 0x([0-9A-Fa-f]{2})")


def _status_for(result: "dict") -> int:
    """The HTTP status of a ``{ok, error?, code?}`` reply: 200 when ``ok``, else by
    ``code`` (400 without one)."""
    if result.get("ok"):
        return 200
    return _STATUS_FOR_CODE.get(str(result.get("code") or ""), 400)


def _fail(error: str, code: "str | None" = None, **extra) -> "dict":
    """An ``ok: false`` reply (``code`` omitted when None)."""
    out: "dict" = {"ok": False, "error": error}
    if code:
        out["code"] = code
    out.update(extra)
    return out


def _car_coded(result: "dict") -> "dict":
    """A source reply as the ``/command`` route sends it: an ECU negative response that the
    source reported as text gets ``code: car_refused`` and its ``nrc`` (a source that sets
    ``code`` itself is left alone)."""
    if not isinstance(result, dict) or result.get("ok") or result.get("code"):
        return result
    m = _NRC_TEXT.search(str(result.get("error") or ""))
    if m:
        return {**result, "code": "car_refused", "nrc": int(m.group(1), 16)}
    return result


class ApiError(Exception):
    """An API refusal: HTTP ``code`` plus an English ``error`` message and an optional
    stable ``kind`` (sent as the envelope's ``code``)."""

    def __init__(self, code: int, error: str, kind: "str | None" = None) -> None:
        super().__init__(error)
        self.code = code
        self.error = error
        self.kind = kind


def _store_module_for(mid: "str | None") -> str:
    """A module id or legacy alias → its canonical id (the store/registry id), via the
    active vehicle pack. Unknown ids come back unchanged; ``None`` → ``""``."""
    return canonical_module(mid or "") or ""


def _query_module(q: "dict", default: "str | None" = None) -> str:
    """``?module=`` from a parsed query string, canonical; the pack's default module when
    absent or empty."""
    raw = (q.get("module", [None])[0]) or default or active_pack().default_module
    return _store_module_for(raw)


def _catalog_response(module: "str | None") -> "tuple[dict, int]":
    """``GET /catalog[?module=]`` → (body, HTTP code). Public: read-only metadata."""
    from .. import catalog

    if not module:
        return {"modules": catalog.module_summary()}, 200
    store = _store_module_for(module)
    module = store
    known = {m.get("store_module") for m in catalog.module_summary()}
    if store not in known:
        return _fail(f"unknown module: {module}", "not_found"), 404
    try:
        body = catalog.build_catalog(store)
    except (KeyError, ValueError) as exc:
        return _fail(f"unknown module: {module} ({exc})", "not_found"), 404
    return {"module": module, **body}, 200

_DASHBOARD = Path(__file__).with_name("dashboard.html")        # legacy v1 (reference only)
_DASHBOARD_V2 = Path(__file__).with_name("dashboard_v2.html")  # legacy v2 (fallback + reference)
# The React/TypeScript app (ui/ in the repo), built ahead of time by `npm run build`.
# Committed and shipped as package-data so a Pi never needs Node (ADR-0004).
_STATIC = Path(__file__).with_name("static")

_CONTENT_TYPES = {
    ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8", ".svg": "image/svg+xml",
    ".json": "application/json", ".map": "application/json",
    ".woff2": "font/woff2", ".png": "image/png", ".ico": "image/x-icon",
}


def _app_html() -> bytes:
    """The built app's index.html, or the legacy v2 page when no build is present
    (a fresh checkout without `npm run build` still has a working dashboard)."""
    index = _STATIC / "index.html"
    return index.read_bytes() if index.is_file() else _DASHBOARD_V2.read_bytes()


def _static_file(url_path: str) -> "Path | None":
    """Resolve a request path to a file inside the static dir, or None.

    Guards against traversal: the resolved path must stay inside ``_STATIC``."""
    rel = url_path.split("?", 1)[0].lstrip("/")
    if not rel or rel.endswith("/"):
        return None
    root = _STATIC.resolve()
    try:
        target = (root / rel).resolve()
    except (OSError, ValueError):
        return None
    if root not in target.parents or not target.is_file():
        return None
    return target


def _calibrate(req: "dict") -> "dict":
    """Solve scale/offset from submitted (raw, displayed) samples → Signal suggestion."""
    from ..sniff.calib import solve_linear, suggest_signal

    samples = req.get("samples") or []
    try:
        fit = solve_linear([(float(s[0]), float(s[1])) for s in samples])
    except (TypeError, ValueError, IndexError):
        fit = None
    if fit is None:
        return _fail("need ≥2 samples with different raw values", "bad_request")
    try:
        lid = req.get("lid", 0)
        if isinstance(lid, str):
            lid = int(lid, 16)
        sig = suggest_signal(
            (req.get("name") or "signal"), int(lid), int(req.get("offset", 0)),
            (req.get("kind") or "u16"), fit["scale"], fit["bias"], (req.get("unit") or ""),
        )
    except (TypeError, ValueError) as exc:
        return _fail(f"{type(exc).__name__}: {exc}", "bad_request")
    return {"ok": True, "signal": sig, **fit}


_capture_lock = threading.Lock()

# RFC 9745: the responses that still carry a deprecated field say so. The deprecations of
# specs/2026-10-06-api-consistency-design.md §6 date from 2026-10-06 (release 0.1.0); the
# fields go in 0.2.0. The Link points at the CHANGELOG's Deprecated entry.
_DEPRECATED_SINCE = 1791244800  # 2026-10-06T00:00:00Z
_DEPRECATION_HEADERS = {
    "Deprecation": f"@{_DEPRECATED_SINCE}",
    "Link": '<https://github.com/openostler/ostler/blob/main/CHANGELOG.md>; '
            'rel="deprecation"; type="text/markdown"',
}


def _stamp(now: float) -> "dict":
    """The snapshot's time: ``ts_utc`` (RFC 3339 UTC ``Z``) and the deprecated ``ts``
    (epoch seconds, removed in 0.2.0)."""
    return {"ts": now, "ts_utc": rfc3339_utc(now)}


def _audio_start_ms(query: "dict") -> "float | None":
    """The track start of ``POST /sessions/<id>/audio`` in epoch ms: ``start_utc`` (RFC 3339
    UTC) wins over the deprecated ``start`` (epoch ms); None when neither is given."""
    import datetime as _dt

    stamp = query.get("start_utc")
    if stamp:
        try:
            t = _dt.datetime.fromisoformat(stamp.strip().replace("Z", "+00:00"))
        except ValueError:
            raise ApiError(400, "start_utc must be an RFC 3339 date-time") from None
        if t.tzinfo is None:
            raise ApiError(400, "start_utc must carry a UTC offset (Z)")
        return t.timestamp() * 1000.0
    start = query.get("start")
    if start in (None, ""):
        return None
    try:
        return float(start)
    except ValueError:
        raise ApiError(400, "start must be epoch ms") from None


def _append_capture(path: "str | None", rec: "dict") -> "dict":
    """Append a labelled capture {module, lid, raw, text} to a JSONL file (durable
    dataset for mapping analysis)."""
    if not path:
        return {"ok": True, "stored": False}
    # ``t`` is RFC 3339 UTC ``Z`` (spec §4). The file is append-only: rows written before
    # 0.1.0 keep a local time without an offset, which a reader treats as unknown.
    row = {"t": rfc3339_utc(time.time()),
           "module": rec.get("module"), "lid": rec.get("lid"),
           "raw": rec.get("raw"), "text": rec.get("text")}
    try:
        with _capture_lock, open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        return _fail(f"{type(exc).__name__}: {exc}", "internal")
    return {"ok": True, "stored": True}


def _automap(req: "dict") -> "dict":
    """Auto-search the right raw field (offset/type/scale or byte.bit) from plaintext readings."""
    from ..sniff.automap import solve

    try:
        res = solve(
            req.get("samples") or [],
            [str(x) for x in (req.get("candidate_lids") or [])],
            (req.get("name") or "signal"),
            (req.get("unit") or ""),
        )
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return _fail(f"{type(exc).__name__}: {exc}", "bad_request")
    if not res.get("ok") and not res.get("code"):
        # with a byte diff the readings were usable but nothing fits; without, too few
        res = {**res, "code": "no_match" if "diff" in res else "bad_request"}
    return res


def _writable_modules() -> "tuple[str, ...]":
    """Store modules whose signal store the admin mapper may read and write."""
    return tuple(active_pack().writable_signal_modules)


def _signal_upsert(req: "dict") -> "dict":
    """Write a confirmed/candidate mapping to the declarative signal store
    (write-back — closes the mapping loop). Replaces localStorage for the
    valuable RE work: mapping done in the car survives server-side."""
    from ..signals import upsert_field

    module = _store_module_for(str(req.get("module") or "").lower())
    if module not in _writable_modules():
        return _fail(f"unknown module: {module!r}", "bad_request")
    rec = req.get("record") or {}
    if not isinstance(rec, dict) or not rec.get("name") or rec.get("lid") is None \
            or rec.get("offset") is None:
        return _fail("record requires at least name, lid, offset", "bad_request")
    try:
        upsert_field(module, rec)
    except OSError as exc:  # the store could not be written: our failure, not the request's
        return _fail(f"{type(exc).__name__}: {exc}", "internal")
    except (ValueError, TypeError, KeyError) as exc:
        return _fail(f"{type(exc).__name__}: {exc}", "bad_request")
    return {"ok": True, "module": module, "name": rec["name"]}


def _signals_list(module: str) -> "dict":
    """Read the store for a module (for the UI: show mapped fields + confidence)."""
    from ..signals import load_records

    module = _store_module_for(module)
    if module not in _writable_modules():
        return {"module": module, "signals": []}
    return {"module": module, "signals": load_records(module)}


def _fields_list(module: str) -> "dict":
    """Expected fields for a module — name/unit/confidence/limits plus the presentation
    metadata (label/group/description) — so the UI can show the layout with empty
    placeholders even WITHOUT a cable/live data. The UI's only metadata source."""
    from ..signals import load_signals

    def _span(span, limits):
        """Display span: explicit, else the limits padded by 10 % each side."""
        if span:
            return list(span)
        if limits:
            lo, hi = limits
            pad = (hi - lo) * 0.1
            return [round(lo - pad, 3), round(hi + pad, 3)]
        return None

    module = store_mod = _store_module_for(module)  # a legacy alias → the canonical id
    derived = active_pack().derived_fields.get(store_mod, {})
    fields = []
    seen: "set[str]" = set()
    for s in load_signals(store_mod):
        if s.name in seen:  # a reply-length variant of a field already listed
            continue
        seen.add(s.name)
        limits = list(s.limits) if s.limits else None
        fields.append({
            "name": s.name, "unit": s.unit, "c": s.confidence, "limits": limits,
            "label": s.label or s.name, "group": s.group or "Other",
            "description": s.description, "derived": False,
            "span": _span(s.span, limits),
            # only an explicit band: falling back to the alarm limits would draw a
            # meaningless "normal 0–200 km/h" across the whole scale
            "normal": list(s.normal) if s.normal else None,
            # the COVESA VSS path the field publishes (ADR-0016); Drive modes bind to it
            "metric": s.metric,
        })
    for name, m in derived.items():
        fields.append({"name": name, "unit": m.get("unit", ""), "c": m.get("c", "candidate"),
                       "limits": None, "label": m.get("label", name),
                       "group": m.get("group", "Other"),
                       "description": m.get("description", ""), "derived": True,
                       "span": m.get("span"), "normal": m.get("normal"), "metric": None})
    return {"module": module, "fields": fields}


def _faults_list(module: str) -> "dict":
    """The fault-meaning dictionary for a module (the ``dtc`` store) — so the UI can show
    what a fault code MEANS, not just its name. Keyed by each module's stable fault key
    (td5 ``offset.bit``, slabs/airbag display number, autobox ``P-code-NN``, ace ``XX-YY``)."""
    from ..dtc import load_records

    module = _store_module_for(module)  # a legacy alias → the canonical id
    return {"module": module, "faults": load_records(module)}


def _parse_range(header: "str | None", size: int):
    """A single ``bytes=`` range → (start, end) inclusive; None = whole file;
    ``"invalid"`` = unsatisfiable (416). Multi-range requests are served whole."""
    if not header:
        return None
    m = re.fullmatch(r"\s*bytes=(\d*)-(\d*)\s*", header)
    if not m:
        return None if "," in header else "invalid"
    a, b = m.group(1), m.group(2)
    if not a and not b:
        return "invalid"
    if not a:  # suffix: the last N bytes
        n = int(b)
        if n == 0 or size == 0:
            return "invalid"
        return max(0, size - n), size - 1
    start = int(a)
    end = int(b) if b else size - 1
    if start >= size or end < start:
        return "invalid"
    return start, min(end, size - 1)


def _num(v, name: str, *, minimum: "float | None" = None) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
        raise ApiError(400, f"{name} must be a number")
    if minimum is not None and v < minimum:
        raise ApiError(400, f"{name} must be ≥ {minimum:g}")
    return float(v)


def _note_fields(body: "dict", partial: bool) -> "dict":
    """Validate note fields (spec §2) → the subset present (all required ones unless
    ``partial``). Raises :class:`ApiError` 400."""
    out: "dict" = {}
    if "t" in body or not partial:
        out["t"] = int(round(_num(body.get("t"), "t", minimum=0)))
    if "t_end" in body and body["t_end"] is not None:
        out["t_end"] = int(round(_num(body["t_end"], "t_end", minimum=0)))
    elif "t_end" in body:
        out["t_end"] = None
    if "t" in out and out.get("t_end") is not None and out["t_end"] < out["t"]:
        raise ApiError(400, "t_end must not be before t")
    if "text" in body or not partial:
        text = body.get("text", "")
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise ApiError(400, "text must be a string")
        out["text"] = text[:_NOTE_TEXT_MAX]
    if "tags" in body or not partial:
        tags = body.get("tags") or []
        if not isinstance(tags, list) or not all(isinstance(x, str) for x in tags):
            raise ApiError(400, "tags must be a list of strings")
        out["tags"] = [x.strip()[:40] for x in tags if x.strip()][:_NOTE_TAGS_MAX]
    return out


def _capture_value(cap) -> "dict":
    """A capture note's ``capture`` {module, lid, raw, value}, all strings."""
    if not isinstance(cap, dict):
        raise ApiError(400, "capture must be an object {module, lid, raw, value}")
    lid = cap.get("lid")
    if isinstance(lid, int) and not isinstance(lid, bool):
        lid = f"{lid:02x}"
    out = {"module": cap.get("module"), "lid": lid, "raw": cap.get("raw"),
           "value": cap.get("value", cap.get("text"))}
    for k, v in out.items():
        if v is None:
            out[k] = ""
        elif not isinstance(v, (str, int, float)) or isinstance(v, bool):
            raise ApiError(400, f"capture.{k} must be a string")
        out[k] = str(out[k])[:200]
    out["lid"] = out["lid"].strip().lower()
    return out


def _prefers_html(accept: "str | None") -> bool:
    """Whether an ``Accept`` header ranks HTML above JSON: a browser navigating to a page,
    not an API client (``*/*`` alone or no header is an API client)."""
    html = as_json = 0.0
    for part in (accept or "").split(","):
        media, _, params = part.partition(";")
        q = 1.0
        for param in params.split(";"):
            key, _, value = param.partition("=")
            if key.strip().lower() == "q":
                try:
                    q = float(value)
                except ValueError:
                    q = 0.0
        media = media.strip().lower()
        if media in ("text/html", "application/xhtml+xml"):
            html = max(html, q)
        elif media == "application/json":
            as_json = max(as_json, q)
    return html > 0 and html > as_json


# The last path segment has an extension: a file (``/app.js``), never an app page.
_FILE_EXT = re.compile(r"\.[^/]*$")
_AUTH_REALM = 'Basic realm="Ostler admin"'


# Remote paths (ADR-0033 §6): the Tailscale ranges and any proxy or relay header.
_TAILSCALE_NETS = (ipaddress.ip_network("100.64.0.0/10"),
                   ipaddress.ip_network("fd7a:115c:a1e0::/48"))
_LOCAL_NETS = (ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"),
               ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("169.254.0.0/16"),
               ipaddress.ip_network("fc00::/7"), ipaddress.ip_network("fe80::/10"))
_PROXY_HEADERS = ("Forwarded", "X-Forwarded-For", "X-Forwarded-Host", "X-Real-IP",
                  "CF-Connecting-IP", "Tailscale-User-Login", "Via")


def is_local_link(peer: "str | None", headers=None) -> bool:
    """A local link (module-bus spec §7.2, UI spec §3.7): see ``_Handler._local_link``."""
    if headers is not None and any(headers.get(h) for h in _PROXY_HEADERS):
        return False
    try:
        ip = ipaddress.ip_address((peer or "").split("%", 1)[0])
    except ValueError:
        return False
    if getattr(ip, "ipv4_mapped", None) is not None:
        ip = ip.ipv4_mapped
    if any(ip in n for n in _TAILSCALE_NETS):
        return False
    return ip.is_loopback or any(ip in n for n in _LOCAL_NETS)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # silent log
        pass

    # Routing compares ``path`` (the request path without its query string, computed once
    # per request by ``_path``), never ``self.path``: a query string is accepted on every
    # route (specs/2026-10-06-api-consistency-design.md §3).
    def do_GET(self) -> None:  # noqa: N802
        path = self._path()
        # The app is served at "/" ("/v2" kept as an alias for old bookmarks). "/admin"
        # is the same app behind a password: the page detects /admin and shows the
        # mapping tabs. The hand-written legacy pages stay reachable behind admin as a
        # reference until the new app has been used in the car (ADR-0004).
        if path in ("/", "/index.html", "/v2", "/v2.html"):
            self._send(_app_html(), "text/html; charset=utf-8")
        elif path in ("/admin", "/admin/", "/admin.html"):
            if not self._require_admin(page=True):
                return
            self._send(_app_html(), "text/html; charset=utf-8")
        elif path in ("/legacy/v2", "/legacy/v2.html"):
            if not self._require_admin(page=True):
                return
            self._send(_DASHBOARD_V2.read_bytes(), "text/html; charset=utf-8")
        elif path in ("/v1", "/v1.html", "/legacy/v1", "/legacy/v1.html"):
            if not self._require_admin(page=True):
                return
            self._html()
        elif path == "/events":
            self._sse()
        elif path == "/snapshot":
            self._json(self.server.latest, headers=_DEPRECATION_HEADERS)
        elif path == "/map":
            if not self._require_admin():
                return
            q = self._qs()
            mod = _query_module(q, self.server._active)
            mp = self.server.legacy_menu(mod)
            if mp is None:
                mp = self.server.source.menu_map()
            self._json({
                "module": mod, "map": mp,
                "modules": list(self.server._menus),
                "coverage": self.server.coverage(),
            })
        elif path == "/sniff":
            if not self._require_admin():
                return
            if self.server.sniffer is None:
                self._json({"module": None, "modules": [], "lids": []})
            else:
                q = self._qs()
                self._json(self.server.sniffer.snapshot(q.get("module", [None])[0]))
        elif path == "/signals":
            if not self._require_admin():
                return
            self._json(_signals_list(_query_module(self._qs())))
        elif path == "/fields":
            self._json(_fields_list(_query_module(self._qs())))
        elif path == "/faults":
            self._json(_faults_list(_query_module(self._qs())))
        elif path == "/pack":
            # Public (also in public mode): the vehicle pack's manifest (modules, aliases,
            # UI layout). The UI loads it once at boot.
            self._json(active_pack().manifest())
        elif path == "/cluster":
            # The Network page's data (NodeSource spec §11, P3): built from what the devices
            # publish; read-only. Refused on the public server (no device topology there).
            if self.server._public:
                self._error(403, _PUBLIC_REFUSAL, "public_mode")
                return
            self._json(self.server.cluster())
        elif path == "/cluster/events":
            # The devices' events (module-bus spec §6.1), de-duplicated by id; read-only.
            if self.server._public:
                self._error(403, _PUBLIC_REFUSAL, "public_mode")
                return
            self._api(lambda: self.server.node_events(self._query()))
        elif path == "/cluster/events/stream":
            if self.server._public:
                self._error(403, _PUBLIC_REFUSAL, "public_mode")
                return
            self._event_stream()
        elif path == "/version":
            # Public: what is running (platform + pack versions and commits) for Settings.
            from ..version import build_info
            self._json(build_info(active_pack()))
        elif path == "/catalog":
            # Public (also in public mode): read-only item metadata for the module pages.
            q = self._qs()
            try:
                body, code = _catalog_response(q.get("module", [None])[0])
            except ImportError:
                body, code = _fail("catalog not available", "unavailable"), 503
            self._json(body, code=code)
        elif path == "/sessions" or path.startswith("/sessions/"):
            self._sessions_get(path)
        elif path == "/captures":
            if not self._require_admin():
                return
            q = self._qs()
            self._api(lambda: self.server.captures(q.get("module", [None])[0]))
        elif path == "/community":
            c = self.server.community
            self._json(c.state() if c is not None else {"consent": None, "endpoint": None})
        elif path == "/docs":
            if not self._require_admin():
                return
            self._json({"docs": self.server.docs.index()})
        elif path == "/doc":
            if not self._require_admin():
                return
            doc_id = self._qs().get("id", [""])[0]
            frag = self.server.docs.html(doc_id)
            if frag is None:
                self._error(404, f"unknown document: {doc_id}", "not_found")
            else:
                self._send(frag.encode("utf-8"), "text/html; charset=utf-8")
        else:
            f = _static_file(path)
            if f is not None and f.name != "index.html":
                ctype = _CONTENT_TYPES.get(f.suffix) or (
                    mimetypes.guess_type(f.name)[0] or "application/octet-stream")
                # Vite fingerprints everything under /assets/ → safe to cache forever.
                cache = ("public, max-age=31536000, immutable"
                         if path.startswith("/assets/") else "no-cache")
                self._send(f.read_bytes(), ctype, cache=cache)
            elif self._wants_app_shell(path):
                # A browser deep link to a page the server does not know: the app shell,
                # so the UI shows its own not-found view and a reload keeps the URL.
                self._send(_app_html(), "text/html; charset=utf-8")
            else:
                self._error(404, "not found", "not_found")

    def do_POST(self) -> None:  # noqa: N802
        path = self._path()
        if path == "/command":
            self._api(self._command)
        elif path == "/calib":
            if not self._require_admin():
                return
            self._api(lambda: _calibrate(self._json_body()))
        elif path == "/automap":
            if not self._require_admin():
                return
            self._api(lambda: _automap(self._json_body()))
        elif path == "/capture":
            if not self._require_admin():
                return
            self._api(self._capture)
        elif path == "/notes/live":
            self._api(lambda: self.server.live_note(self._json_body()))
        elif path == "/cluster/remove":
            # The owner's Remove device (module-bus spec §7.2, §13; UI spec §3.7): admin
            # (the owner until accounts land), never in public mode, local links only.
            if self.server._public:
                self._error(403, _PUBLIC_REFUSAL, "public_mode")
                return
            if not self._require_admin():
                return
            if not self._local_link():
                self._error(403, "Remove device works only over a local link (the head "
                                 "unit, the in-car network, the node's Wi-Fi), never over "
                                 "a remote path", "not_local")
                return
            self._api(lambda: self.server.remove_device(self._json_body()))
        elif path.startswith("/sessions/"):
            self._sessions_post(path)
        elif path == "/signal":
            if not self._require_admin():
                return
            self._api(lambda: _signal_upsert(self._json_body()))
        elif path in ("/community/consent", "/community/contribute") and self.server._public:
            # A public visitor must not change this device's sharing choice or upload
            # readings in its name.
            self._error(403, _PUBLIC_REFUSAL, "public_mode")
        elif path == "/community/consent":
            # Not admin-gated: the first-run Consent screen and Preferences belong to the
            # device's own user (the LAN UI); public mode is refused above.
            c = self.server.community
            if c is None:
                self._error(409, "community disabled", "community_off")
            else:
                def _consent() -> dict:
                    body = self._json_body()
                    return c.set_consent(bool(body.get("consent")), body.get("vehicle"))
                self._api(_consent)
        elif path == "/community/contribute":
            # Contributions come from the admin Coverage Map, so they need admin auth.
            if not self._require_admin():
                return
            c = self.server.community
            if c is None:
                self._error(409, "community disabled", "community_off")
            else:
                # queued offline → 202 {ok: true, queued: true} (see _api)
                self._api(lambda: c.contribute(self._json_body()))
        else:
            self._error(404, "not found", "not_found")

    def do_PATCH(self) -> None:  # noqa: N802
        path = self._path()
        sid, rest = self._session_parts(path)
        if sid is not None and not rest:  # PATCH /sessions/<id> {name?, description?}
            if not _SESSION_ID.match(sid):
                self._error(404, f"unknown session: {sid}", "not_found")
                return
            self._api(lambda: self.server.patch_session(sid, self._json_body()))
            return
        if sid is None or len(rest) != 2 or rest[0] != "notes":
            self._error(404, "not found", "not_found")
            return
        self._api(lambda: self.server.edit_note(sid, rest[1], self._json_body()))

    def do_DELETE(self) -> None:  # noqa: N802
        path = self._path()
        sid, rest = self._session_parts(path)
        if sid is None or len(rest) != 2 or rest[0] != "notes":
            self._error(404, "not found", "not_found")
            return
        self._api(lambda: self.server.delete_note(sid, rest[1]))

    # ---- request helpers ----------------------------------------------- #
    def _path(self) -> str:
        """The request path without its query string or fragment."""
        return urlsplit(self.path).path

    def _qs(self) -> "dict[str, list[str]]":
        """The parsed query string (every value of every parameter)."""
        return parse_qs(urlsplit(self.path).query)

    def _query(self) -> "dict[str, str]":
        """The parsed query string, the first value of each parameter."""
        return {k: v[0] for k, v in self._qs().items() if v}

    def _wants_app_shell(self, path: str) -> bool:
        """An unknown ``GET`` answered with the app shell: a browser page (``Accept``
        prefers HTML) whose path has no file extension (a missing ``.js`` stays 404)."""
        return not _FILE_EXT.search(path) and _prefers_html(self.headers.get("Accept"))

    def _command(self) -> dict:
        """``POST /command``: queue or run the command; the reply's ``code`` sets the status."""
        cmd = self._json_body()
        srv = self.server
        # The basic-mode scan is sequential over several modules (slow init
        # for airbag) → give it plenty of time; other commands are fast.
        timeout = srv.scan_timeout if cmd.get("action") in ("read_all_faults", "detect_protocol",
                                                            "module_scan") \
            else srv.command_timeout
        return srv.enqueue_command(cmd, timeout=timeout)

    def _capture(self) -> dict:
        body = self._json_body()
        res = _append_capture(self.server.captures_path, body)
        if res.get("ok"):
            self.server.capture_note(body)  # into the recording session, if any
        return res

    # ---- replay API helpers (ADR-0010) --------------------------------- #
    def _session_parts(self, path: str) -> "tuple[str | None, list[str]]":
        """``/sessions/<id>/a/b`` → ("<id>", ["a", "b"]); (None, []) for anything else."""
        from urllib.parse import unquote

        parts = [unquote(p) for p in path.split("/") if p]
        if len(parts) < 2 or parts[0] != "sessions":
            return None, []
        return parts[1], parts[2:]

    def _api(self, fn) -> None:
        """Run an API call and send its dict. A reply with ``ok: false`` gets the status of
        its ``code`` (400 without one), a queued one (``ok: true, queued: true``) 202,
        anything else 200. An :class:`ApiError` → its status and the error envelope; any
        other exception → 500 ``internal``."""
        try:
            body = fn()
        except ApiError as exc:
            self._api_error(exc)
            return
        except Exception as exc:  # noqa: BLE001
            self._error(500, f"{type(exc).__name__}: {exc}", "internal")
            return
        if isinstance(body, dict) and body.get("ok") is False:
            code = _status_for(body)
            if "code" not in body and code in _CODE_FOR_STATUS:
                body = {**body, "code": _CODE_FOR_STATUS[code]}
            self._json(body, code)
        elif isinstance(body, dict) and body.get("ok") is True and body.get("queued") is True:
            self._json(body, 202)
        else:
            self._json(body)

    def _api_error(self, exc: ApiError) -> None:
        self._error(exc.code, exc.error, exc.kind)

    def _read_capped(self, cap: int) -> bytes:
        """The request body, refusing (413) anything over ``cap`` bytes unread."""
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            raise ApiError(400, "bad Content-Length") from None
        if length < 0:
            raise ApiError(400, "bad Content-Length")
        if length > cap:
            if length <= 4 * cap:  # drain it so the client reads the 413, not a reset
                left = length
                while left > 0:
                    chunk = self.rfile.read(min(65536, left))
                    if not chunk:
                        break
                    left -= len(chunk)
            else:
                self.close_connection = True  # far too large: left unread
            raise ApiError(413, f"body too large (max {cap} bytes)")
        return self.rfile.read(length) if length else b""

    def _json_body(self) -> "dict":
        """The JSON object body (an empty body is ``{}``); 400 when it is not one."""
        raw = self._read_capped(_JSON_BODY_MAX)
        try:
            body = json.loads(raw or b"{}")
        except (ValueError, TypeError):
            raise ApiError(400, "body must be JSON") from None
        if not isinstance(body, dict):
            raise ApiError(400, "body must be a JSON object")
        return body

    def _sessions_post(self, path: str) -> None:
        """``POST /sessions/<id>/notes | audio | accel | accel_cal``."""
        sid, rest = self._session_parts(path)
        if sid is None or len(rest) != 1:
            self._error(404, "not found", "not_found")
            return
        what = rest[0]
        srv = self.server
        if what == "notes":
            self._api(lambda: srv.add_note(sid, self._json_body()))
        elif what == "audio":
            def _audio() -> dict:
                try:
                    srv.check_writable(sid)  # refuse before keeping a (large) body
                except ApiError:
                    try:
                        self._read_capped(_AUDIO_CHUNK_MAX)  # discard it: a clean refusal
                    except ApiError:
                        pass
                    raise
                return srv.put_audio(sid, self._query(), self._read_capped(_AUDIO_CHUNK_MAX))
            self._api(_audio)
        elif what == "accel":
            self._api(lambda: srv.put_accel(sid, self._json_body()))
        elif what == "accel_cal":
            self._api(lambda: srv.put_accel_cal(sid, self._json_body()))
        else:
            self._error(404, "not found", "not_found")

    def _send_audio(self, sid: str, track: str) -> None:
        """``GET /sessions/<id>/audio/<track>`` with single-range HTTP Range support."""
        try:
            path, ctype = self.server.audio_file(sid, track)
            size = os.path.getsize(path)
        except ApiError as exc:
            self._api_error(exc)
            return
        except OSError:
            self._error(404, f"unknown track: {track}", "not_found")
            return
        rng = _parse_range(self.headers.get("Range"), size)
        if rng == "invalid":
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        start, end = rng if rng else (0, size - 1)
        length = max(0, end - start + 1)
        self.send_response(206 if rng else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(path, "rb") as fh:
            fh.seek(start)
            left = length
            while left > 0:
                chunk = fh.read(min(65536, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    # ---- session logbook (public, filtered in public mode) ------------- #
    def _sessions_get(self, path: str) -> None:
        """``/sessions`` (paged), ``/sessions/histogram``, ``/sessions/<id>``,
        ``/sessions/<id>/data``, ``/sessions/<id>/export``.

        Public routes; in public mode the store only exposes synthetic sessions, so a real
        (location-bearing) session answers 404 exactly like an unknown id (ADR-0009)."""
        q = self._qs()
        parts = [p for p in path.split("/") if p][1:]  # drop "sessions"
        store = self.server.session_store
        public = self.server._public
        if store is None:
            if not parts:
                self._json({"sessions": [], "next": None})
            elif parts == ["histogram"]:
                self._json({"group": "month", "buckets": []})
            else:
                self._error(404, "session logbook not available", "not_found")
            return
        if not parts:  # paged + filtered through the SessionIndex (spec 2026-10-06 §3)
            self._api(lambda: self.server.sessions_page(self._query()))
            return
        if parts == ["histogram"]:
            self._api(lambda: self.server.sessions_histogram(self._query()))
            return
        sid, rest = parts[0], parts[1:]
        if rest and rest[0] == "audio" and len(rest) == 2 and _SESSION_ID.match(sid):
            self._send_audio(sid, rest[1])
            return
        if not _SESSION_ID.match(sid) or len(rest) > 1 or (
                rest and rest[0] not in ("data", "export", "events", "notes")):
            self._error(404, f"unknown session: {sid}", "not_found")
            return
        if rest and rest[0] == "events":
            self._api(lambda: self.server.session_events(sid))
            return
        if rest and rest[0] == "notes":
            self._api(lambda: self.server.list_notes(sid))
            return
        try:
            meta = store.meta(sid, public=public)  # KeyError → 404 (incl. filtered in public)
            if not rest:
                self._json(meta)
            elif rest[0] == "data":
                ch_arg = (q.get("ch", [""])[0] or "").strip()
                channels = [c for c in (x.strip() for x in ch_arg.split(",")) if c]
                try:
                    max_points = int(q.get("max", [_DEFAULT_MAX_POINTS])[0])
                except (TypeError, ValueError):
                    self._error(400, "max must be an integer", "bad_request")
                    return
                if max_points < 2:
                    self._error(400, "max must be ≥ 2", "bad_request")
                    return
                self._json(store.data(sid, channels, max_points=max_points, public=public),
                           headers=_DEPRECATION_HEADERS)
            else:
                fmt = (q.get("fmt", ["csv"])[0] or "").lower()
                if fmt not in _EXPORT_FORMATS:
                    self._error(400, f"unknown export format: {fmt!r} "
                                f"({'|'.join(_EXPORT_FORMATS)})", "bad_request")
                    return
                filename, ctype, body = store.export(sid, fmt, public=public)
                self._send_download(body, ctype, filename)
        except KeyError:
            self._error(404, f"unknown session: {sid}", "not_found")
        except ValueError as exc:
            self._error(400, f"{type(exc).__name__}: {exc}", "bad_request")
        except OSError as exc:  # the session files could not be read: our failure
            self._error(500, f"{type(exc).__name__}: {exc}", "internal")

    def _send_download(self, body: bytes, content_type: str, filename: str) -> None:
        safe = re.sub(r'[^A-Za-z0-9_.-]', "_", os.path.basename(filename or "session"))
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{safe}"')
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- admin gate (HTTP Basic Auth) --------------------------------- #
    # Protects the mapping/dev surface (/admin + automap/capture/signal/calib/…).
    # If no password is set, admin is UNGATED (local dev, backwards-compatible) — the Pi
    # runs with --admin-password. Basic Auth over HTTP without TLS is "keep the curious
    # off the LAN", not strong crypto; no sensitive data lives behind it.
    def _admin_ok(self) -> bool:
        pw = getattr(self.server, "_admin_password", None)
        if not pw:
            return True
        hdr = self.headers.get("Authorization", "")
        if hdr.startswith("Basic "):
            try:
                decoded = base64.b64decode(hdr[6:]).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                decoded = ""
            supplied = decoded.partition(":")[2]  # optional username, only the password counts
            if hmac.compare_digest(supplied, pw):
                return True
        return False

    def _local_link(self) -> bool:
        """The request came over a local link (ADR-0033 §6; accounts spec §2.3): a
        loopback, private (RFC 1918), link-local or unique-local peer, and no proxy or relay
        header. Tailscale (100.64.0.0/10, ``fd7a:115c:a1e0::/48``), any public address and
        any forwarded request are remote paths."""
        return is_local_link(self.client_address[0] if self.client_address else None,
                             self.headers)

    def _event_stream(self) -> None:
        """``GET /cluster/events/stream``: the events feed as SSE, one ``node_event`` per
        event with its ``seq`` as the SSE ``id`` (a reconnect sends ``Last-Event-ID``, or
        ``?after=``); a comment every 15 s keeps the connection open."""
        feed = getattr(self.server.source, "feed", None)
        if feed is None or not hasattr(feed, "events"):
            self._error(503, "no node source: events come from the devices' MQTT messages "
                             "(--source node)", "unavailable")
            return
        try:
            after = int(self.headers.get("Last-Event-ID") or self._query().get("after") or 0)
        except ValueError:
            after = 0
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            while not self.server._stop.is_set():
                for ev in feed.events(after)["events"]:
                    after = max(after, ev["seq"])
                    self.wfile.write(f"id: {ev['seq']}\nevent: node_event\n"
                                     f"data: {json.dumps(ev)}\n\n".encode())
                self.wfile.flush()
                if not feed.wait_events(after, self.server.event_keepalive):
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # the client closed

    def _require_admin(self, page: bool = False) -> bool:
        """True if the call may proceed; otherwise a 401 is sent and False returned.

        An app ``page`` gets an empty body, so the browser shows its Basic Auth prompt;
        an API route gets the error envelope (``auth_required``)."""
        if self._admin_ok():
            return True
        if page:
            self.send_response(401)
            self.send_header("WWW-Authenticate", _AUTH_REALM)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._error(401, "admin authentication required", "auth_required",
                        headers={"WWW-Authenticate": _AUTH_REALM})
        return False

    # ---- responses ----------------------------------------------------- #
    def _send(self, body: bytes, content_type: str, code: int = 200,
              cache: "str | None" = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        if cache:
            self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self) -> None:
        self._send(_DASHBOARD.read_bytes(), "text/html; charset=utf-8")

    def _json(self, obj: "dict", code: int = 200, headers: "dict | None" = None) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, error: str, code: "str | None" = None,
               headers: "dict | None" = None, **extra) -> None:
        """Send the error envelope ``{ok: false, error, code}``."""
        self._json(_fail(error, code or _CODE_FOR_STATUS.get(status), **extra), status,
                   headers=headers)

    def send_error(self, code: int, message: "str | None" = None,
                   explain: "str | None" = None) -> None:
        """The stdlib's own errors (400 bad request line, 414, 501 unsupported method …)
        as the JSON envelope instead of its HTML page; no body for ``HEAD``."""
        short = self.responses.get(code, ("Error", ""))[0]
        body = json.dumps(_fail(message or short, _CODE_FOR_STATUS.get(code))).encode("utf-8")
        self.send_response(code, message)
        self.send_header("Connection", "close")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD" and code >= 200 and code not in (204, 205, 304):
            self.wfile.write(body)

    def _sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        for name, value in _DEPRECATION_HEADERS.items():  # the snapshot's ts and since
            self.send_header(name, value)
        self.end_headers()
        try:
            while True:
                payload = json.dumps(self.server.latest)
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.flush()
                time.sleep(self.server.stream_interval)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the client closed


# Commands that do NOT touch K-line and may therefore run straight on the HTTP thread.
# Queuing them behind the poller thread means they have to wait out an ongoing
# establishment (SLABS: bus-idle + 3 attempts × 5 s retry ≈ 20 s) and then time out
# at 8 s in the UI — even though they later succeed once the queue drains. They only
# touch the server's own state (CsvLogger object, fault_every attribute).
_INLINE_COMMANDS = frozenset({"start_csv", "stop_csv", "set_fault_watch", "shutdown",
                              "delete_session", "recording_options", "split_session"})

# Server-level commands handled on the poll thread (they release/establish sessions or
# switch sources). Not module commands: the registry gate does not apply to them.
_SERVER_COMMANDS = frozenset({"select_module", "read_all_faults",
                              "connect", "disconnect", "set_port"}) | PROBE_COMMANDS
# Server commands that open the serial port themselves. With a source that never touches
# the car (NodeSource: the node reads it, ADR-0032) they are refused.
_BUS_COMMANDS = frozenset({"read_all_faults", "set_port"}) | PROBE_COMMANDS
# Generic per-source commands every module offers (not in the command registry).
_GENERIC_SOURCE_COMMANDS = frozenset({"clear_faults", "read_block"})
# Prefixes of module-command families (``active_pack().module_command_prefixes``): an
# action like these that is NOT registered for the active module is refused as unknown
# instead of reaching a source.

# Snapshot `conn` values (spec: Connection UX).
CONN_STATES = ("disconnected", "connecting", "connected", "lost", "reconnecting", "error")
_PORT_INFO_TTL = 2.0  # seconds between serial-port rescans for the snapshot


def _looks_like_module_command(action: str) -> bool:
    from .. import commands

    if action.startswith(tuple(active_pack().module_command_prefixes)):
        return True
    return any(c.action == action for c in commands.registry().values())


class ConnectAborted(Exception):
    """Establishment aborted because a command is waiting (e.g. module switch)."""


class DiagServer(KLineCommandsMixin, ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    # How long ``POST /command`` waits for the poll thread (seconds); past it the reply is
    # 504 ``car_timeout``. The multi-module fault scan gets longer.
    command_timeout = 8.0
    scan_timeout = 45.0

    def __init__(
        self,
        source: "DataSource | dict | None" = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        poll_interval: float = 0.5,
        stream_interval: float = 0.5,
        logger=None,
        active: "str | None" = None,
        menus: "dict | None" = None,
        docs: "DocLibrary | None" = None,
        sniffer=None,
        captures_path: "str | None" = None,
        scan_port: str = "auto",
        csv_dir: str = "logs",
        community=None,
        public: bool = False,
        fault_watch: bool = False,
        admin_password: "str | None" = None,
        allow_shutdown: bool = False,
        gps=None,
        sessions_dir: "str | None" = None,
        record_sessions: bool = True,
        audio: str = "off",
        imu: "str | None" = None,
        accel_hz: int = 25,
        pi_audio=None,
        fault_scan=None,
        geocoder: "str | None" = None,
        enricher=None,
        index_path: "str | None" = None,
        kline_detect: bool = False,
        kline_profile: "str | None" = None,
        state_dir: "str | None" = None,
        module_scan=None,
        device_revoker=None,
    ) -> None:
        if public and not admin_password:
            # Public mode is for a bind other people can reach; with no password every
            # admin route (signal write-back, /capture, …) would be open to them.
            raise ValueError("public mode needs an admin password (--admin-password or "
                             "D2DIAG_ADMIN_PW)")
        super().__init__((host, port), _Handler)
        # None/"" = admin ungated (local dev). Set = /admin + mapping endpoints
        # behind HTTP Basic Auth. See _Handler._admin_ok.
        self._admin_password = admin_password or None
        self._fault_watch = fault_watch  # True = poll fault codes every cycle (fast)
        self._scan_port = scan_port  # port for "read all fault codes" (basic mode)
        self._csv_dir = csv_dir  # where CSV live logs go (start/stop in the UI)
        self._csv = None  # active CsvLogger or None
        self._csv_lock = threading.Lock()  # start/stop on the HTTP thread, log() in the poller
        self.community = community  # opt-in contribution client (Community) or None
        self._public = public  # public mode: simpler UI (hides Map/Capture/Docs + actuators)
        # allow_shutdown: expose a "Shut down Pi" button in Settings. Off by default so
        # dev on a laptop can never power off the host; the Pi's systemd unit passes
        # --allow-shutdown. Stopgap until proper power control exists.
        self._allow_shutdown = bool(allow_shutdown)
        self._menus = menus or {}  # module → menu list (Map tab)
        self.docs = docs or DocLibrary()  # markdown view (Documents tab)
        self.sniffer = sniffer  # passive sniff feed (Mapping tab), optional
        self.captures_path = captures_path  # labelled live captures → JSONL
        # ``source`` = a single DataSource or {module: DataSource}. Always the car (ADR-0011:
        # no demo mode; the tests inject their fakes here). Only ONE module is active at a
        # time (K-line = shared bus) → a tab switch releases the old session and
        # establishes a new one.
        # Keys are canonical module ids (a legacy alias such as the old UI id is mapped).
        if isinstance(source, dict) and source:
            self._modules: "dict[str, DataSource]" = {
                _store_module_for(k) or k: v for k, v in source.items()}
        elif source is not None and not isinstance(source, dict):
            self._modules = {_store_module_for(source.name) or source.name: source}
        else:
            raise ValueError("DiagServer requires a source")
        # "Read all fault codes": openostler.faultscan.read_all(port) unless injected (tests).
        self._fault_scan = fault_scan
        active = _store_module_for(active) if active else active
        self._active = active if active in self._modules else next(iter(self._modules))
        self.source = self._modules[self._active]
        self.poll_interval = poll_interval
        self.stream_interval = stream_interval
        self.logger = logger  # optional SnapshotLogger → logs every poll to file
        # Connection state machine (snapshot `conn`): see _next_conn.
        self._conn = "connecting"
        self._ever_connected = False  # since the last (re)start: module/port switch, connect
        self._paused = False          # True after `disconnect` until `connect`/`set_port`
        # A latched test that is on ({action,label,since,stop}), or None.
        self._active_test: "dict | None" = None
        self._port_cache: "tuple[float, dict] | None" = None
        # Session logbook (ADR-0009): the GPS source (gps.reader.open_gps(...) or None) and
        # the always-on recorder + store under ``sessions_dir`` (default <csv_dir>/sessions,
        # i.e. logs/sessions). ``record_sessions=False`` keeps the store but never records.
        self.gps = gps
        self._sessions_dir = sessions_dir or os.path.join(self._csv_dir, "sessions")
        self._recorder = None
        self.session_store = None
        self._rec_lock = threading.Lock()  # feed() on the poller vs close() on shutdown
        self._rec_closed = False
        self._init_logbook(record_sessions)
        # Session index (logs/sessions.sqlite next to the sessions dir) + place-name
        # enrichment (spec 2026-10-06 §2-3). Built in the background when missing.
        self._init_index(index_path, geocoder, enricher)
        # Replay capture sources (ADR-0010): Pi audio (--audio off|pi; ``pi_audio`` injects a
        # PiAudio-like object) and the Pi IMU (--imu auto|none; tests inject "mock"). Both are opt-in via the
        # ``recording_options`` command; phone audio/acceleration arrive over HTTP. The
        # recorder owns the per-session files (audio tracks, events, notes, Acc_* columns).
        self._audio_mode = audio if audio in ("off", "pi") else "off"
        self._pi_audio = pi_audio                 # handed to the recorder while audio == pi
        self._pi_error: "str | None" = None       # PiAudio could not be built
        self._imu_spec = imu or "none"
        self._imu_source = None                   # opened IMU (or None) — see _probe_imu
        self._imu_reason: "str | None" = None
        self._imu_reader = None                   # running ImuReader while imu is on
        self._rec_opts = {"audio": "off", "imu": "off",
                          "accel_hz": accel_hz if accel_hz in _ACCEL_HZ else 25}
        self._notes_lock = threading.Lock()
        self._session_name: "str | None" = None   # recording_options ``name``
        self._recent_capture: "tuple[float, str, dict, dict] | None" = None
        self._tls = None                          # ssl.SSLContext once enable_tls() ran
        self._init_sources()
        self.latest: "dict" = self._decorate({
            "status": "connecting", "source": self.source.name,
            "signals": {}, "faults": [],
        }, module=self._active)
        self._apply_fault_watch()  # set the fault-polling cadence on all sources
        for s in self._all_sources():  # live feedback during blocking establishment
            s.on_progress = self._connect_progress
            s.on_sleep = self._connect_sleep
        # Connection log: the whole establishment sequence + errors are written here (and to stderr)
        # so you can debug a session that "dies" shortly after connecting.
        self._conn_log_path = os.path.join(self._csv_dir, "connection.log")
        self._last_conn_status: "tuple | None" = None  # (module, status) — see _log_conn_transition
        self._last_conn_error: "str | None" = None
        self._last_phase_logged: "str | None" = None  # dedupe of identical progress lines
        # Last known engine context (rpm/speed/battery) from TD5. K-line is a shared
        # bus so we can't read the engine while SLABS is active — but a SLABS attempt
        # is almost always preceded by a TD5 session, and then the values are seconds old.
        # Without this you can't tell afterwards whether a silent init attempt was made
        # while moving (SLABS refuses comms >8–20 km/h) or at idle.
        self._engine: "dict | None" = None
        self._stop = threading.Event()
        self._commands: "queue.Queue" = queue.Queue()
        self._poller = threading.Thread(target=self._poll_loop, daemon=True)
        # K-line probing gate, process override and remembered profiles (kline_cmds.py).
        self._init_kline(kline_detect=kline_detect, kline_profile=kline_profile,
                         state_dir=state_dir, module_scan=module_scan)
        # Remove device (module-bus spec §7.2): the Brain's revocation list in the state
        # directory, and the install's hook that revokes the certificate and ACL entry on
        # the broker host (``device_revoker(vid, device) -> str``; None: not configured).
        self._state_dir = state_dir
        self._device_revoker = device_revoker
        self.event_keepalive = 15.0
        self._load_removed()

    # ---- session logbook --------------------------------------------- #
    def _init_logbook(self, record: bool) -> None:
        """Build the SessionStore (+ SessionRecorder). Lazy import: a missing/broken
        logbook package must never stop the dashboard from serving live data."""
        try:
            from ..logbook.store import SessionStore
            self.session_store = SessionStore(self._sessions_dir)
        except Exception as exc:  # noqa: BLE001
            self._conn_log_early(f"logbook: store unavailable ({type(exc).__name__}: {exc})")
            return
        if not record:
            return
        try:
            from ..logbook.recorder import SessionRecorder
            self._recorder = SessionRecorder(self._sessions_dir,
                                             on_change=self._recorder_changed)
        except Exception as exc:  # noqa: BLE001
            self._conn_log_early(f"logbook: recorder unavailable ({type(exc).__name__}: {exc})")

    @staticmethod
    def _conn_log_early(msg: str) -> None:
        try:
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)
        except Exception:  # noqa: BLE001
            pass

    def _gps_fix(self):
        """The GPS source's latest Fix, or None (never raises)."""
        if self.gps is None:
            return None
        try:
            return self.gps.latest()
        except Exception:  # noqa: BLE001
            return None

    def _gps_snapshot(self) -> "dict | None":
        """Snapshot ``gps``: ``Fix.snapshot()``; a no-fix dict while a source has no fix
        yet; null when there is no source."""
        if self.gps is None:
            return None
        fix = self._gps_fix()
        if fix is not None:
            try:
                return fix.snapshot()
            except Exception:  # noqa: BLE001
                pass
        return {"fix": False, "lat": None, "lon": None, "speed_kmh": None, "heading": None,
                "alt_m": None, "sats": None, "hdop": None, "src": getattr(self.gps, "src", None),
                "age_s": None}

    def _recording_status(self) -> "dict | None":
        rec = self._recorder
        if rec is None or self._rec_closed:
            return None
        try:
            return rec.status()
        except Exception:  # noqa: BLE001
            return None

    def record_poll(self) -> None:
        """Feed the latest snapshot + GPS fix to the recorder (once per poll, also while
        disconnected so the idle timer runs) and refresh ``recording`` in ``latest``.
        Only signals/faults/module/GPS reach a session — the recorder ignores the rest,
        and identity reads never enter a snapshot. Free-space rotation of old sessions is
        the recorder's job (on session start). Never fells the poll loop."""
        rec = self._recorder
        if rec is None:
            return
        with self._rec_lock:
            if self._rec_closed:
                return
            try:
                rec.feed(self.latest, self._gps_fix())
            except Exception as exc:  # noqa: BLE001
                self._conn_log(f"logbook: feed failed ({type(exc).__name__}: {exc})")
            status = self._recording_status()
            self._feed_imu(rec, status)
        tap = self._sync_tap(status)
        self._track_session(status)
        self.latest = {**self.latest, "recording": status,
                       "recording_sources": self.recording_sources()}
        node = self.latest.get("node")
        if tap is not False and isinstance(node, dict):
            self.latest["node"] = {**node, "tap": tap}  # the tap as of this poll

    def _feed_imu(self, rec, status: "dict | None") -> None:
        """Hand the IMU samples gathered since the last poll to the recorder (dropped
        while nothing is recording). Caller holds ``_rec_lock``."""
        reader = self._imu_reader
        if reader is None:
            return
        try:
            samples = reader.drain()
            if samples and status and hasattr(rec, "feed_accel"):
                rec.feed_accel(samples, "imu")
        except Exception as exc:  # noqa: BLE001
            self._conn_log(f"imu: feed failed ({type(exc).__name__}: {exc})")

    def cluster(self) -> dict:
        """``GET /cluster`` (NodeSource spec §11): a node source's cluster view; with a
        cable source there is no cluster to read, so the lists are empty and ``note``
        says why."""
        feed = getattr(self.source, "feed", None)
        if feed is not None and hasattr(feed, "cluster"):
            try:
                return feed.cluster()
            except Exception as exc:  # noqa: BLE001 — the page shows an empty, stale view
                self._conn_log(f"node: cluster view {type(exc).__name__}: {exc}")
        return {"vid": getattr(feed, "vid", None),
                "source_kind": getattr(self.source, "source_kind", "serial"),
                "built_utc": rfc3339_utc(time.time()), "as_of_utc": None,
                "stale": feed is not None, "broker": None, "devices": [], "roles": [],
                "alerts": [],
                "note": ("the cluster view failed; see the connection log" if feed is not None
                         else "no node source: the cluster is read from the node's MQTT "
                              "messages (--source node)")}

    # ---- events and Remove device (module-bus spec v1.3 §6.1, §7.2, §13) -------- #
    def _removed_registry(self):
        from ..logbook.vehicle import state_dir_for
        from ..node.removal import REGISTRY_FILE, RemovedRegistry

        sd = self._state_dir or state_dir_for(self._sessions_dir)
        return RemovedRegistry(os.path.join(sd, REGISTRY_FILE))

    def _load_removed(self) -> None:
        feed = getattr(self.source, "feed", None)
        if feed is None or not hasattr(feed, "load_removed"):
            return
        try:
            feed.load_removed(self._removed_registry().devices(feed.vid))
        except Exception as exc:  # noqa: BLE001 — the view then shows them again
            self._conn_log_early(f"node: removed devices unreadable ({type(exc).__name__}: {exc})")

    def node_events(self, query: "dict[str, str]") -> dict:
        """``GET /cluster/events``: the events feed (``?after=<seq>``, ``?limit=``)."""
        feed = getattr(self.source, "feed", None)
        if feed is None or not hasattr(feed, "events"):
            return {"vid": None, "events": [], "last_seq": 0, "duplicates": 0,
                    "stale": False, "note": "no node source: events come from the devices' "
                                            "MQTT messages (--source node)"}
        try:
            after = max(0, int(query.get("after") or 0))
            limit = min(200, max(1, int(query.get("limit") or 200)))
        except ValueError:
            raise ApiError(400, "after and limit must be integers", "bad_request") from None
        return feed.events(after, limit)

    def remove_device(self, body: dict) -> dict:
        """``POST /cluster/remove {device, confirm: true}``: the owner's Remove device. The
        route has checked the owner (admin) and the local link. Records the revocation,
        runs the install's revoke hook, then the broker-host purge of the device's
        retained topics; answers what was done, and 503 when the purge was incomplete."""
        from ..node.removal import check_device

        feed = getattr(self.source, "feed", None)
        if feed is None or not hasattr(feed, "remove_device"):
            raise ApiError(409, "no node source: devices are removed from the Brain's broker "
                                "(--source node)", "conflict")
        try:
            device = check_device(body.get("device"))
        except ValueError as exc:
            raise ApiError(400, str(exc), "bad_request") from None
        if body.get("confirm") is not True:
            raise ApiError(400, "Remove device needs one confirmation (confirm: true)",
                           "bad_request")
        registry = self._removed_registry()
        known = device in feed.table.devices() or device in registry.devices(feed.vid)
        if not known:
            raise ApiError(404, f"no device {device!r} under vehicle {feed.vid}", "not_found")
        registry.add(feed.vid, device, by="owner")
        if self._device_revoker is not None:
            try:
                broker_revoked = str(self._device_revoker(feed.vid, device) or "done")
            except Exception as exc:  # noqa: BLE001
                broker_revoked = f"failed: {type(exc).__name__}: {exc}"
        else:
            broker_revoked = "not configured"
        res = feed.remove_device(device)
        registry.update(feed.vid, device, topics_purged=res["purged"])
        self._conn_log(f"node: owner removed device {device} (purged {len(res['purged'])}, "
                       f"refused {len(res['refused'])}, left {len(res['remaining'])})")
        out = {"ok": True, "vid": feed.vid, **res,
               "revoked": {"brain": True, "broker": broker_revoked}}
        problem = res.get("error") or (
            "the broker refused to clear some retained topics (the broker-host identity "
            "needs write access to the vehicle's topics)" if res["refused"] else None) or (
            "some retained topics are still on the broker" if res["remaining"] else None)
        if problem:
            out.update(ok=False, error=f"Device removed from this Brain, but the purge is "
                                       f"incomplete: {problem}", code="unavailable")
        return out

    def _sync_tap(self, status: "dict | None"):
        """A node source's raw tap follows the recorder (NodeSource spec §7, owner answer
        9): subscribed while a session is open, unsubscribed when it ends. Returns the
        snapshot ``node.tap`` now, or False for a source without a tap. Never raises."""
        feed = getattr(self.source, "feed", None)
        if feed is None or not hasattr(feed, "start_tap"):
            return False
        try:
            if status and self._recorder is not None and not self._rec_closed:
                feed.start_tap(self._tap_sink)
            elif feed.tap_running:
                feed.stop_tap()
            return feed.tap_state()
        except Exception as exc:  # noqa: BLE001 — the tap never fells the poll loop
            self._conn_log(f"node: raw tap {type(exc).__name__}: {exc}")
            return False

    def _tap_sink(self, device: str, session: str, part: str, payload: bytes,
                  props: "dict | None" = None) -> None:
        """Raw-tap messages from the MQTT thread into the open session (if any), with the
        publish's MQTT 5 properties (a batch's content type and ``first_seq``)."""
        rec = self._recorder
        if rec is None or self._rec_closed:
            return
        try:
            rec.tap_message(device, session, part, payload, props)
        except Exception as exc:  # noqa: BLE001
            self._conn_log(f"logbook: tap write failed ({type(exc).__name__}: {exc})")

    def close_recorder(self) -> None:
        """End the open session (server shutdown). Idempotent."""
        feed = getattr(self.source, "feed", None)
        if feed is not None and getattr(feed, "tap_running", False):
            try:
                feed.stop_tap()
            except Exception:  # noqa: BLE001
                pass
        with self._rec_lock:
            if self._rec_closed:
                return
            self._rec_closed = True
            if self._recorder is not None:
                try:
                    self._recorder.close()
                except Exception:  # noqa: BLE001
                    pass

    def delete_session(self, params: "dict | None") -> "dict":
        """``delete_session {id}``: refused in public mode, for synthetic (demo) sessions
        and for the session being recorded right now."""
        if self._public:
            return _fail("deleting sessions is not available in public mode", "public_mode")
        sid = str((params or {}).get("id") or "")
        store = self.session_store
        if store is None:
            return _fail("session logbook not available", "unavailable")
        if not _SESSION_ID.match(sid):
            return _fail(f"unknown session: {sid}", "not_found")
        try:
            meta = store.meta(sid)
        except KeyError:
            return _fail(f"unknown session: {sid}", "not_found")
        if meta.get("synthetic"):
            return _fail(_SYNTHETIC_REFUSAL, "read_only")
        if (self._recording_status() or {}).get("session") == sid:
            return _fail("session is being recorded", "conflict")
        try:
            store.delete(sid)
        except KeyError:
            return _fail(f"unknown session: {sid}", "not_found")
        except PermissionError as exc:
            return _fail(str(exc), "conflict" if "recorded" in str(exc) else "read_only")
        except ValueError as exc:
            return _fail(str(exc), "bad_request")
        return {"ok": True, "deleted": sid}

    # ---- session index + place names (spec 2026-10-06 §2-3) ------------ #
    def _init_index(self, index_path: "str | None", geocoder: "str | None", enricher) -> None:
        """Open the SessionIndex (synchronously when its file exists, else built in a
        background thread) and set up the OSM enricher (never in public mode: the public
        server lists only the synthetic demo logs, which are never geocoded)."""
        self._index = None
        self._index_lock = threading.RLock()
        self._index_ready = threading.Event()
        self._index_path = index_path or os.path.join(self._sessions_dir, "index.sqlite")
        self._enricher = None
        self._geo_pending: "set[str]" = set()
        self._geo_lock = threading.Lock()
        self._rec_sid: "str | None" = None       # the session the recorder had last poll
        self._rec_synced = 0.0                   # monotonic time of its last index sync
        self._index_started = False
        if self.session_store is None:
            self._index_started = True
            self._index_ready.set()
            return
        if not self._public:
            if enricher is not None:
                self._enricher = enricher
            elif geocoder and geocoder != "off":
                try:
                    from ..geo.nominatim import Enricher
                    cache = os.path.join(os.path.dirname(self._sessions_dir.rstrip("/\\"))
                                         or ".", "geocache.json")
                    self._enricher = Enricher(geocoder, cache)
                except Exception as exc:  # noqa: BLE001 — no geocoder must never stop serving
                    self._conn_log_early(f"geo: enricher unavailable ({type(exc).__name__}: {exc})")

    def _start_index(self) -> None:
        """Open the index once: synchronously when its file exists, else built in a
        background thread (a large logbook must not delay serving). Runs at startup
        (``start_polling``) or on first use."""
        with self._index_lock:
            if self._index_started:
                return
            self._index_started = True
        if os.path.exists(self._index_path):
            self._open_index()
        else:
            threading.Thread(target=self._open_index, name="session-index",
                             daemon=True).start()

    def _open_index(self) -> None:
        """Attach the SessionIndex to the store (``store.index``): from then on every store
        write (meta edits, places, notes, deletes) and ``store.sync`` keep it current."""
        idx = None
        try:
            from ..logbook.index import SessionIndex
            os.makedirs(os.path.dirname(self._index_path) or ".", exist_ok=True)
            idx = SessionIndex(self._index_path, self.session_store)
        except Exception as exc:  # noqa: BLE001
            self._conn_log_early(f"logbook: index unavailable ({type(exc).__name__}: {exc})")
        with self._index_lock:
            self._index = idx
            if idx is not None:
                self.session_store.index = idx
        self._index_ready.set()
        if idx is not None:
            self._enrich_backlog()

    def index(self, wait: float = 0.0):
        """The SessionIndex once it is ready (waiting up to ``wait`` s), else None."""
        self._start_index()
        if not self._index_ready.is_set() and wait > 0:
            self._index_ready.wait(wait)
        return self._index

    def _index_sync(self, sid: str) -> None:
        """``store.sync(sid)`` (re-index; a missing session leaves the index). Never raises."""
        if not sid or self.session_store is None:
            return
        try:
            self.session_store.sync(sid)
        except Exception as exc:  # noqa: BLE001 — the index is a cache; never fail the caller
            self._conn_log(f"logbook: index sync {sid} failed ({type(exc).__name__}: {exc})")

    def _recorder_changed(self, sid: str) -> None:
        """``SessionRecorder.on_change``: a session opened, closed, was renamed or got a
        live note. Re-index it; once it is closed, ask for its OSM place names. A session
        the recorder discarded (nothing recorded) leaves the index."""
        if not sid or not hasattr(self, "_index_lock"):
            return
        self._index_sync(sid)
        try:
            meta = self.session_store.meta(sid)
        except Exception:  # noqa: BLE001 — removed (empty) or unreadable
            return
        if not meta.get("recording"):
            self._enrich(meta)

    def _track_session(self, status: "dict | None") -> None:
        """Refresh the open session's index row (rows, distance …) every 30 s."""
        sid = (status or {}).get("session")
        now = time.monotonic()
        if sid != self._rec_sid:
            self._rec_sid, self._rec_synced = sid, now
        elif sid and now - self._rec_synced >= _INDEX_RESYNC_S:
            self._rec_synced = now
            self._index_sync(sid)

    def _enrich_backlog(self) -> None:
        """Queue every closed real session that lacks an OSM label (at index startup)."""
        if self._enricher is None:
            return
        try:
            metas = self.session_store.list(public=False)
        except Exception:  # noqa: BLE001
            return
        for meta in metas:
            self._enrich(meta)

    def _enrich(self, meta: "dict") -> None:
        """Submit a closed real session's start/end points to the enricher (once each)."""
        enricher = self._enricher
        if enricher is None or self._public or not isinstance(meta, dict):
            return
        if meta.get("synthetic") or meta.get("recording"):
            return
        sid = meta.get("id")
        if not isinstance(sid, str) or not _SESSION_ID.match(sid):
            return
        for which in ("start", "end"):
            place = meta.get(f"place_{which}")
            if isinstance(place, dict) and place.get("source") == "osm":
                continue
            pos = meta.get(f"{which}_pos")  # [lon, lat]
            if (not isinstance(pos, (list, tuple)) or len(pos) != 2 or not all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) for x in pos)):
                continue
            key = f"{sid}|{which}"
            with self._geo_lock:
                if key in self._geo_pending:
                    continue
                self._geo_pending.add(key)
            try:
                enricher.submit(key, float(pos[1]), float(pos[0]), self._on_place)
            except Exception as exc:  # noqa: BLE001
                with self._geo_lock:
                    self._geo_pending.discard(key)
                self._conn_log(f"geo: submit failed ({type(exc).__name__}: {exc})")

    def _on_place(self, key: str, label: "str | None") -> None:
        """Enricher callback (its thread): store the OSM label, then re-index."""
        with self._geo_lock:
            self._geo_pending.discard(key)
        if not label or not isinstance(key, str) or "|" not in key:
            return
        sid, which = key.rsplit("|", 1)
        try:  # the store re-indexes the session itself
            self.session_store.set_place(sid, which, label, source="osm")
        except PermissionError:
            return  # a demo log: committed, never geocoded
        except Exception as exc:  # noqa: BLE001
            self._conn_log(f"geo: set_place {sid} failed ({type(exc).__name__}: {exc})")

    def sessions_page(self, query: "dict[str, str]") -> "dict":
        """``GET /sessions?limit=&before=&q=&from=&to=&module=&has_notes=&min_km=``."""
        kw: "dict" = {}
        try:
            limit = int(query.get("limit", 50))
        except ValueError:
            raise ApiError(400, "limit must be an integer") from None
        if limit < 1:
            raise ApiError(400, "limit must be ≥ 1")
        kw["limit"] = min(limit, _PAGE_LIMIT_MAX)
        before = query.get("before")
        if before:  # a cursor from ``next``, or an ISO date/datetime (the scrubber)
            if len(before) > 120:
                raise ApiError(400, "before must be a cursor from next or an ISO date")
            kw["before"] = before
        filters: "dict" = {}
        if query.get("q", "").strip():
            filters["q"] = query["q"].strip()[:200]
        for arg, name in (("from", "frm"), ("to", "to")):
            v = query.get(arg)
            if v:
                if not _ISO_DATE.match(v):
                    raise ApiError(400, f"{arg} must be an ISO date (YYYY-MM-DD)")
                filters[name] = v
        if query.get("module"):
            filters["module"] = _store_module_for(query["module"])  # a legacy alias → its id
        hn = query.get("has_notes")
        if hn is not None and hn.lower() in ("1", "true", "yes"):
            filters["has_notes"] = True
        if query.get("min_km"):
            try:
                filters["min_km"] = float(query["min_km"])
            except ValueError:
                raise ApiError(400, "min_km must be a number") from None
        idx = self.index(wait=_INDEX_WAIT_S)
        if idx is None:
            if filters:
                raise ApiError(503, "the session index is not ready — try again shortly")
            return self._fallback_page(kw["limit"], kw.get("before"))
        try:
            return idx.page(public=self._public, **kw, **filters)
        except ValueError as exc:
            raise ApiError(400, str(exc)) from None

    def _fallback_page(self, limit: int, before: "str | None") -> "dict":
        """Unfiltered keyset paging straight from the store (no index available)."""
        import datetime as _dt

        def start_ms(m: dict) -> int:
            try:
                t = _dt.datetime.fromisoformat(str(m.get("start_utc")).replace("Z", "+00:00"))
                return int(t.timestamp() * 1000)
            except ValueError:
                return 0

        rows = sorted(((start_ms(m), str(m.get("id")), m)
                       for m in self.session_store.list(public=self._public)),
                      key=lambda r: (r[0], r[1]), reverse=True)
        if before:
            ms, _, bid = before.partition(":")
            try:
                key = (int(ms), bid)
            except ValueError:
                raise ApiError(503, "the session index is not ready — try again shortly") from None
            rows = [r for r in rows if (r[0], r[1]) < key]
        page = rows[:limit]
        nxt = f"{page[-1][0]}:{page[-1][1]}" if len(rows) > limit else None
        return {"sessions": [r[2] for r in page], "next": nxt}

    def sessions_histogram(self, query: "dict[str, str]") -> "dict":
        """``GET /sessions/histogram?group=month`` or ``?group=day&year=YYYY``."""
        group = query.get("group", "month")
        if group not in ("month", "day"):
            raise ApiError(400, "group must be month or day")
        year = None
        if query.get("year"):
            try:
                year = int(query["year"])
            except ValueError:
                raise ApiError(400, "year must be an integer") from None
        idx = self.index(wait=_INDEX_WAIT_S)
        if idx is None:
            raise ApiError(503, "the session index is not ready — try again shortly")
        try:
            return idx.histogram(group=group, year=year, public=self._public)
        except ValueError as exc:
            raise ApiError(400, str(exc)) from None

    def patch_session(self, sid: str, body: "dict") -> "dict":
        """``PATCH /sessions/<id> {name?, description?}`` → ``{ok, meta}``. Trimmed, capped
        (80 / 2000 characters), empty → null. 403 in public mode and for synthetic sessions."""
        if self._public:
            raise ApiError(403, _PUBLIC_REFUSAL, "public_mode")
        fields: "dict" = {}
        for key, cap in (("name", _NAME_MAX), ("description", _DESCRIPTION_MAX)):
            if key not in body:
                continue
            v = body[key]
            if v is None:
                fields[key] = None
                continue
            if not isinstance(v, str):
                raise ApiError(400, f"{key} must be a string")
            v = " ".join(v.split()) if key == "name" else v.strip()
            fields[key] = v[:cap].strip() or None
        if not fields:
            raise ApiError(400, "nothing to change (name, description)")
        self.check_writable(sid)  # 404 unknown, 403 synthetic
        store = self.session_store
        try:
            with self._notes_lock:
                meta = store.update_meta(sid, **fields)
        except KeyError:
            raise ApiError(404, f"unknown session: {sid}") from None
        except PermissionError as exc:
            raise ApiError(403, str(exc) or _SYNTHETIC_REFUSAL, "read_only") from None
        except ValueError as exc:
            raise ApiError(400, str(exc)) from None
        # (The recorder adopts this edit on its next meta write of an open session.)
        if not isinstance(meta, dict):
            meta = store.meta(sid)
        return {"ok": True, "meta": meta}

    # ---- recording sources (ADR-0010 §3) ------------------------------- #
    def _init_sources(self) -> None:
        """Build the Pi audio helper and probe the IMU once (never raises)."""
        if self._audio_mode == "pi" and self._pi_audio is None:
            try:
                from ..logbook.audio import PiAudio
                self._pi_audio = PiAudio()
            except Exception as exc:  # noqa: BLE001
                self._pi_error = f"Pi audio unavailable ({type(exc).__name__}: {exc})"
        self._probe_imu()

    def _probe_imu(self) -> None:
        spec = self._imu_spec
        if spec == "none":
            self._imu_reason = "no IMU configured (start with --imu auto)"
            return
        try:
            from ..imu import reader as imu_reader
            src = imu_reader.open_imu(spec, self._rec_opts["accel_hz"])
        except Exception as exc:  # noqa: BLE001
            self._imu_reason = f"IMU unavailable ({type(exc).__name__}: {exc})"
            return
        if src is None:
            self._imu_reason = (getattr(imu_reader, "last_reason", None)
                                or "no IMU found on /dev/i2c-1")
            return
        self._imu_source = src
        self._imu_reason = None

    def _pi_audio_state(self) -> "dict":
        pi = self._pi_audio
        if self._audio_mode != "pi":
            return {"state": "unavailable", "reason": "Pi audio is off (start with --audio pi)"}
        if self._recorder is None:
            return {"state": "unavailable", "reason": "session recording is not available"}
        if pi is None:
            return {"state": "unavailable", "reason": self._pi_error or "Pi audio unavailable"}
        if self._rec_opts["audio"] == "pi" and getattr(pi, "running", False):
            return {"state": "on", "reason": None}
        try:
            ok, reason = pi.available()
        except Exception as exc:  # noqa: BLE001
            ok, reason = False, f"{type(exc).__name__}: {exc}"
        if not ok:
            return {"state": "unavailable", "reason": reason or "arecord unavailable"}
        return {"state": "available", "reason": None}

    def _imu_state(self) -> "dict":
        if self._imu_reader is not None:
            return {"state": "on", "reason": None}
        if self._imu_source is None:
            return {"state": "unavailable", "reason": self._imu_reason or "no IMU"}
        return {"state": "available", "reason": None}

    def recording_sources(self) -> "dict":
        """Snapshot ``recording_sources``: what can be recorded right now."""
        src = getattr(self.gps, "src", None) if self.gps is not None else None
        gps = "none" if self.gps is None else ("usb" if src == "usb" else "mock")
        return {"gps": gps, "pi_audio": self._pi_audio_state(), "imu": self._imu_state(),
                "accel_hz": self._rec_opts["accel_hz"]}

    def recording_options(self, params: "dict | None") -> "dict":
        """``recording_options {audio: off|pi, imu: off|on, accel_hz: 10|25|50}`` →
        ``{ok, options}``. A source that cannot be used refuses the whole change."""
        params = params if isinstance(params, dict) else {}
        opts = dict(self._rec_opts)
        audio = params.get("audio", opts["audio"])
        imu = params.get("imu", opts["imu"])
        hz = params.get("accel_hz", opts["accel_hz"])
        if audio not in ("off", "pi"):
            return _fail("audio must be off or pi", "bad_request", options=opts)
        if imu not in ("off", "on"):
            return _fail("imu must be off or on", "bad_request", options=opts)
        if isinstance(hz, bool) or hz not in _ACCEL_HZ:
            return _fail("accel_hz must be 10, 25 or 50", "bad_request", options=opts)
        name = params.get("name")
        if name is not None and not isinstance(name, str):
            return _fail("name must be a string", "bad_request", options=opts)
        if audio == "pi" and opts["audio"] != "pi":
            st = self._pi_audio_state()
            if st["state"] == "unavailable":
                return _fail(f"Pi audio unavailable: {st['reason']}", "conflict", options=opts)
        if imu == "on" and self._imu_source is None:
            return _fail(f"IMU unavailable: {self._imu_reason}", "conflict", options=opts)
        self._rec_opts = {"audio": audio, "imu": imu, "accel_hz": int(hz)}
        rec = self._recorder
        if name is not None:
            self._set_session_name(name)
        if rec is not None and hasattr(rec, "accel_hz"):
            rec.accel_hz = int(hz)  # header rate of the acceleration channels
        # The IMU reader follows the switch and the rate.
        if imu == "off":
            self._stop_imu()
        elif self._imu_reader is None:
            self._start_imu()
        elif int(hz) != opts["accel_hz"]:
            self._imu_reader.set_hz(int(hz))
        # Pi audio: the recorder records it for every session while it is set.
        if audio != opts["audio"] and rec is not None:
            try:
                rec.set_pi_audio(self._pi_audio if audio == "pi" else None)
            except Exception as exc:  # noqa: BLE001
                self._conn_log(f"audio: {type(exc).__name__}: {exc}")
        self.latest = {**self.latest, "recording_sources": self.recording_sources()}
        return {"ok": True, "options": dict(self._rec_opts)}

    def _set_session_name(self, name: str) -> None:
        """The optional session name (meta ``name``). Handed to the recorder when it
        supports it (``set_name``); otherwise accepted and kept here only."""
        name = " ".join(name.split())[:80]
        self._session_name = name or None
        rec = self._recorder
        fn = getattr(rec, "set_name", None) if rec is not None else None
        if callable(fn):
            try:
                fn(self._session_name)
            except Exception as exc:  # noqa: BLE001
                self._conn_log(f"logbook: set_name failed ({type(exc).__name__}: {exc})")

    def split_session(self) -> "dict":
        """``split_session``: end the recording session and start a new one now. Refused in
        public mode and unless a session is ``recording`` (ADR-0011). → ``{ok, session}``."""
        if self._public:
            return _fail("splitting sessions is not available in public mode", "public_mode")
        rec = self._recorder
        if rec is None:
            return _fail("session recording is not available", "unavailable")
        with self._rec_lock:
            if self._rec_closed:
                return _fail("session recording is not available", "unavailable")
            if not self.is_recording():
                return _fail(NOT_RECORDING, "not_recording")
            try:
                sid = rec.split(self.latest)
            except _not_recording_error() as exc:
                return _fail(str(exc) or NOT_RECORDING, "not_recording")
            status = self._recording_status()
        self.latest = {**self.latest, "recording": status}
        return {"ok": True, "session": sid}

    def is_recording(self) -> bool:
        """A session is open and in the ``recording`` state (not ``paused``)."""
        st = self._recording_status()
        return bool(st) and st.get("state", "recording") == "recording"

    def _start_imu(self) -> None:
        try:
            from ..imu.reader import ImuReader
            reader = ImuReader(self._imu_source, self._rec_opts["accel_hz"])
            reader.start()
            self._imu_reader = reader
        except Exception as exc:  # noqa: BLE001
            self._imu_reader = None
            self._conn_log(f"imu: failed to start ({type(exc).__name__}: {exc})")

    def _stop_imu(self, reopen: bool = True) -> None:
        """Stop the reader (it closes its source), then reopen the source so the next
        ``imu: on`` finds it again."""
        reader, self._imu_reader = self._imu_reader, None
        if reader is None:
            return
        try:
            reader.stop()
        except Exception:  # noqa: BLE001
            pass
        self._imu_source = None
        if reopen:
            self._probe_imu()

    # ---- events stream hooks (spec §1) --------------------------------- #
    def record_event(self, type_: str, **fields) -> None:
        """Append an event to the recording session (no-op without one). Never raises."""
        rec = self._recorder
        if rec is None or self._rec_closed or not hasattr(rec, "event"):
            return
        try:
            rec.event(type_, **fields)
        except Exception as exc:  # noqa: BLE001
            self._conn_log(f"logbook: event failed ({type(exc).__name__}: {exc})")

    def _record_command(self, action: str, result: "dict | None") -> None:
        """A ``command`` event: action + outcome only — never params, never an identity
        payload (``read_identity`` → ``{action, ok}``)."""
        action = re.sub(r"[^A-Za-z0-9_.-]", "", str(action or ""))[:64]
        if not action:
            return
        result = result if isinstance(result, dict) else {}
        fields: "dict" = {"action": action, "ok": bool(result.get("ok"))}
        if not _IDENTITY_ACTION.search(action):
            for key in ("message", "error"):
                v = result.get(key)
                if isinstance(v, str) and v:
                    fields[key] = v[:200]
        self.record_event("command", **fields)

    # ---- session paths ------------------------------------------------- #
    def _session_path(self, sid: str, public: bool) -> "tuple[str, dict]":
        """(directory, meta) of a session; :class:`ApiError` 404 when unknown or (in
        public mode) not synthetic."""
        store = self.session_store
        if store is None:
            raise ApiError(404, "session logbook not available")
        if not isinstance(sid, str) or not _SESSION_ID.match(sid):
            raise ApiError(404, f"unknown session: {sid}")
        try:
            path, _demo, meta = store._resolve(sid, public)
        except KeyError:
            raise ApiError(404, f"unknown session: {sid}") from None
        return path, meta

    def check_writable(self, sid: str) -> "tuple[str, dict]":
        """(directory, meta) of a session that may be written: refused (403) in public
        mode and for synthetic sessions; 404 when unknown."""
        if self._public:
            raise ApiError(403, _PUBLIC_REFUSAL, "public_mode")
        path, meta = self._session_path(sid, False)
        if meta.get("synthetic"):
            raise ApiError(403, _SYNTHETIC_REFUSAL, "read_only")
        return path, meta

    def _require_recording(self, sid: str) -> "dict":
        status = self._recording_status()
        if not status or status.get("session") != sid:
            raise ApiError(409, f"session {sid} is not being recorded", "not_recording")
        return status

    # ---- events -------------------------------------------------------- #
    def session_events(self, sid: str) -> "dict":
        """``GET /sessions/<id>/events`` → ``{id, events}`` (public filter applies)."""
        _path, meta = self._session_path(sid, self._public)
        rec = self._recorder
        if rec is not None and (self._recording_status() or {}).get("session") == sid:
            flush = getattr(rec, "flush", None)  # the open session syncs at most once a second
            if callable(flush):
                try:
                    flush()
                except Exception:  # noqa: BLE001
                    pass
        try:
            events = self.session_store.events(sid, public=self._public)
        except KeyError:
            raise ApiError(404, f"unknown session: {sid}") from None
        return {"id": meta.get("id", sid), "events": events}

    # ---- notes (spec §2) ----------------------------------------------- #
    def _note_call(self, fn, *args, **kw):
        """Run a store note write, mapping its exceptions onto HTTP codes."""
        try:
            with self._notes_lock:
                return fn(*args, **kw)
        except KeyError as exc:
            raise ApiError(404, f"unknown note: {exc.args[0] if exc.args else ''}") from None
        except PermissionError as exc:
            raise ApiError(403, str(exc), "read_only") from None
        except ValueError as exc:
            raise ApiError(400, str(exc)) from None

    def list_notes(self, sid: str) -> "dict":
        _path, meta = self._session_path(sid, self._public)
        try:
            notes = self.session_store.notes(sid, public=self._public)
        except KeyError:
            raise ApiError(404, f"unknown session: {sid}") from None
        return {"id": meta.get("id", sid), "notes": notes}

    def add_note(self, sid: str, body: "dict") -> "dict":
        self.check_writable(sid)
        f = _note_fields(body, partial=False)
        kind = body.get("kind") or "note"
        if kind not in _NOTE_KINDS:
            raise ApiError(400, "kind must be mark, note or capture")
        src = body.get("source") or "retro"
        if src not in _NOTE_SOURCES:
            raise ApiError(400, "source must be live or retro")
        capture = _capture_value(body.get("capture")) if kind == "capture" else None
        note = self._note_call(self.session_store.add_note, sid, f["t"], text=f["text"],
                               tags=f["tags"], kind=kind, source=src, t_end=f.get("t_end"),
                               capture=capture)
        return {"ok": True, "note": note, "session": sid}

    def edit_note(self, sid: str, nid: str, body: "dict") -> "dict":
        self.check_writable(sid)
        if not _NOTE_ID.match(nid or ""):
            raise ApiError(404, f"unknown note: {nid}")
        f = _note_fields(body, partial=True)
        if not f:
            raise ApiError(400, "nothing to change (text, tags, t, t_end)")
        note = self._note_call(self.session_store.edit_note, sid, nid, **f)
        return {"ok": True, "note": note, "session": sid}

    def delete_note(self, sid: str, nid: str) -> "dict":
        self.check_writable(sid)
        if not _NOTE_ID.match(nid or ""):
            raise ApiError(404, f"unknown note: {nid}")
        self._note_call(self.session_store.delete_note, sid, nid)
        return {"ok": True}

    def live_note(self, body: "dict") -> "dict":
        """``POST /notes/live``: a note stamped "now" in the recording session. Refused with
        409 unless a session is ``recording`` (ADR-0011: never while paused or idle)."""
        if self._public:
            raise ApiError(403, _PUBLIC_REFUSAL, "public_mode")
        kind = body.get("kind") or "mark"
        if kind not in _NOTE_KINDS:
            raise ApiError(400, "kind must be mark, note or capture")
        f = _note_fields({k: body[k] for k in ("text", "tags") if k in body}, partial=True)
        capture = _capture_value(body.get("capture")) if kind == "capture" else None
        rec = self._recorder
        if rec is None:
            raise ApiError(503, "session recording is not available")
        with self._rec_lock:
            if self._rec_closed:
                raise ApiError(503, "session recording is not available")
            if not self.is_recording():
                raise ApiError(409, NOT_RECORDING, "not_recording")
            if capture is not None:  # the same capture via /capture and /notes/live → one
                recent, sid = self._recent_capture, getattr(rec, "session_id", None)
                if recent and recent[1] == sid and recent[2] == capture and \
                        time.monotonic() - recent[0] < 10.0:
                    return {"ok": True, "note": recent[3], "session": sid}
            try:
                sid, note = rec.note(text=f.get("text", ""), tags=f.get("tags", []), kind=kind,
                                     capture=capture, snapshot=self.latest)
            except _not_recording_error() as exc:
                raise ApiError(409, str(exc) or NOT_RECORDING, "not_recording") from None
            except ValueError as exc:
                raise ApiError(400, str(exc)) from None
            if capture is not None:
                self._recent_capture = (time.monotonic(), sid, capture, note)
            status = self._recording_status()
        self.latest = {**self.latest, "recording": status}
        return {"ok": True, "note": note, "session": sid}

    def capture_note(self, body: "dict") -> None:
        """``/capture`` also lands as a ``capture`` note in the recording session (if one is
        ``recording`` — a capture never starts a session). Never raises."""
        if self._public or not self.is_recording():
            return
        try:
            cap = _capture_value({"module": body.get("module"), "lid": body.get("lid"),
                                  "raw": body.get("raw"),
                                  "value": body.get("value", body.get("text"))})
            self.live_note({"kind": "capture", "text": cap["value"], "capture": cap})
        except Exception as exc:  # noqa: BLE001
            self._conn_log(f"logbook: capture note failed ({type(exc).__name__}: {exc})")

    def captures(self, module: "str | None") -> "dict":
        """``GET /captures?module=`` (admin): the store's capture notes from every session
        merged with ``labeled_captures.jsonl``; a row also saved as a note appears once
        (the note, which carries ``t``/``session``)."""
        store = self.session_store
        if store is None:
            return {"captures": []}
        with _capture_lock:
            rows = store.captures(module, labeled_path=self.captures_path)
        out: "list[dict]" = []
        seen: "set[tuple]" = set()
        for r in sorted(rows, key=lambda r: r.get("session") is None):  # notes first
            key = (_store_module_for(str(r.get("module") or "").lower()),
                   str(r.get("lid") or "").strip().lower(),
                   " ".join(str(r.get("raw") or "").lower().split()),
                   str(r.get("value") or "").strip())
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return {"captures": out}

    # ---- audio (spec §3) ----------------------------------------------- #
    def put_audio(self, sid: str, query: "dict", data: bytes) -> "dict":
        """``POST /sessions/<id>/audio?track=&seq=&mime=&start_utc=[&end=1]``: one chunk of
        a phone track into the session being recorded (``end=1`` closes the track). The
        track start is ``start_utc`` (RFC 3339) or the deprecated ``start`` (epoch ms);
        ``start_utc`` wins when both are given."""
        self.check_writable(sid)
        track = query.get("track") or ""
        if not _TRACK_ID.match(track):
            raise ApiError(400, "track must be 1-64 letters, digits, dashes or underscores")
        try:
            seq = int(query.get("seq", ""))
        except ValueError:
            raise ApiError(400, "seq must be an integer") from None
        if seq < 0:
            raise ApiError(400, "seq must be ≥ 0")
        mime = (query.get("mime") or "audio/webm").strip()
        start_ms = _audio_start_ms(query)
        end = query.get("end") in ("1", "true")
        rec = self._recorder
        if rec is None or self._rec_closed:
            raise ApiError(409, f"session {sid} is not being recorded", "not_recording")
        try:
            entry = rec.audio_put(track, seq, data, mime=mime, start_ms=start_ms, session=sid,
                                  source="phone")
            if end:
                entry = rec.audio_stop(track) or entry
        except KeyError:
            raise ApiError(409, f"session {sid} is not being recorded", "not_recording") from None
        except (ValueError, OSError) as exc:
            raise ApiError(400, str(exc)) from None
        return {"ok": True, "track": track, "seq": seq, "bytes": entry.get("bytes", 0),
                "closed": end}

    def audio_file(self, sid: str, track: str) -> "tuple[str, str]":
        """(path, content type) of a session's audio track. Never in public mode (404)."""
        if self._public:
            raise ApiError(404, "not found")
        self._session_path(sid, False)
        if not _TRACK_ID.match(track or ""):
            raise ApiError(404, f"unknown track: {track}")
        try:
            path = self.session_store.audio_path(sid, track, public=False)
        except KeyError:
            raise ApiError(404, f"unknown track: {track}") from None
        return path, self.session_store.audio_mime(path)

    # ---- acceleration (spec §3) ---------------------------------------- #
    def put_accel(self, sid: str, body: "dict") -> "dict":
        """``POST /sessions/<id>/accel {source, samples: [[epoch_ms, ax, ay, az], …]}``
        into the session being recorded."""
        self.check_writable(sid)
        source = body.get("source") or "phone"
        if source not in ("phone", "imu"):
            raise ApiError(400, "source must be phone or imu")
        samples = body.get("samples")
        if not isinstance(samples, list):
            raise ApiError(400, "samples must be a list of [epoch_ms, ax, ay, az]")
        if len(samples) > _ACCEL_SAMPLES_MAX:
            raise ApiError(413, f"at most {_ACCEL_SAMPLES_MAX} samples per request")
        clean = []
        for s in samples:
            if (not isinstance(s, (list, tuple)) or len(s) != 4 or any(
                    isinstance(x, bool) or not isinstance(x, (int, float)) or x != x
                    for x in s)):
                raise ApiError(400, "each sample must be [epoch_ms, ax, ay, az] numbers")
            clean.append((float(s[0]), float(s[1]), float(s[2]), float(s[3])))
        self._require_recording(sid)
        with self._rec_lock:
            if self._rec_closed:
                raise ApiError(409, f"session {sid} is not being recorded", "not_recording")
            try:
                rows = self._recorder.feed_accel(clean, source, session=sid)
            except KeyError:
                raise ApiError(409, f"session {sid} is not being recorded", "not_recording") from None
            except (ValueError, TypeError) as exc:
                raise ApiError(400, f"{type(exc).__name__}: {exc}") from None
        return {"ok": True, "samples": len(clean), "rows": rows}

    def put_accel_cal(self, sid: str, body: "dict") -> "dict":
        """``POST /sessions/<id>/accel_cal {matrix: 3×3, source, method}``."""
        self.check_writable(sid)
        m = body.get("matrix")
        if (not isinstance(m, list) or len(m) != 3 or not all(
                isinstance(r, list) and len(r) == 3 and all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) and x == x
                    for x in r) for r in m)):
            raise ApiError(400, "matrix must be 3×3 numbers")
        matrix = [[float(x) for x in r] for r in m]
        source = body.get("source") or "phone"
        if source not in ("phone", "imu"):
            raise ApiError(400, "source must be phone or imu")
        method = body.get("method") or "manual"
        if not isinstance(method, str) or not re.fullmatch(r"[A-Za-z0-9+_-]{1,32}", method):
            raise ApiError(400, "method must be a short name (level, level+gps, manual)")
        self._require_recording(sid)
        with self._rec_lock:
            if self._rec_closed:
                raise ApiError(409, f"session {sid} is not being recorded", "not_recording")
            try:  # also writes meta.accel_cal and the accel_cal event
                cal = self._recorder.set_accel_cal(matrix, source, method)
            except ValueError as exc:
                raise ApiError(400, str(exc)) from None
        return {"ok": True, "accel_cal": cal}

    # ---- TLS (ADR-0010: phone mic/motion need HTTPS) ------------------- #
    def enable_tls(self, certfile: str, keyfile: str) -> None:
        """Serve HTTPS with this certificate/key (stdlib ``ssl``). The handshake runs on
        the request thread, so a slow or plain-HTTP client never blocks ``accept``."""
        import ssl

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile, keyfile)
        self.socket = ctx.wrap_socket(self.socket, server_side=True,
                                      do_handshake_on_connect=False)
        self._tls = ctx

    def finish_request(self, request, client_address) -> None:
        if self._tls is not None:
            import ssl
            try:
                request.settimeout(10.0)
                request.do_handshake()
                request.settimeout(None)
            except (ssl.SSLError, OSError):
                return  # plain HTTP or a dropped client: shutdown_request closes it
        super().finish_request(request, client_address)

    def _remember_engine(self, snap: "dict") -> None:
        """Save rpm/speed/battery from a TD5 snapshot (for _engine_note)."""
        sig = snap.get("signals") or {}
        if not {"rpm", "battery"} <= set(sig):
            return
        self._engine = {
            "rpm": sig["rpm"].get("v"), "battery": sig["battery"].get("v"),
            "speed": (sig.get("speed") or {}).get("v"), "t": time.monotonic(),
        }

    def _engine_note(self) -> str:
        """`· motor: rpm 761, 0 km/h, 13.9 V (12s ago)` — empty if we know nothing."""
        e = self._engine
        if not e:
            return ""
        age = time.monotonic() - e["t"]
        if age > 600:  # older than 10 min says nothing about the present
            return ""
        speed = "?" if e["speed"] is None else f"{e['speed']:.0f} km/h"
        return f" · motor: rpm {e['rpm']:.0f}, {speed}, {e['battery']:.1f} V ({age:.0f}s ago)"

    def _connect_sleep(self, seconds: float) -> None:
        """Sleep used by the establishment — interrupted by a queued command.

        The SLABS quiet period is 28 s and a full establishment can take ~90 s. Without
        this the poller thread sleeps while a module switch sits in the queue, and the UI
        times out even though the command is valid. We sleep in slices and raise
        :class:`ConnectAborted` as soon as anything is queued — the establishment is
        aborted, the queue drains, and the next poll restarts against the right module.
        """
        deadline = time.monotonic() + seconds
        while True:
            if not self._commands.empty():
                raise ConnectAborted("aborted by a queued command")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            self._stop.wait(min(0.2, remaining))
            if self._stop.is_set():
                return

    def _conn_log(self, msg: str, module: "str | None" = None) -> None:
        """Write a timestamped line to the connection log and stderr. Must never
        fell the poll loop — swallows all errors.

        ``module`` stamps the line with the module the snapshot concerns; without it
        the currently active one is used. The difference matters mid module-switch,
        where a snapshot from the old module would otherwise be labelled with the new.
        """
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{module or self._active}] {msg}"
        try:
            print(line, flush=True)  # → the task/stderr log
        except Exception:  # noqa: BLE001
            pass
        try:
            os.makedirs(os.path.dirname(self._conn_log_path), exist_ok=True)
            with open(self._conn_log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:  # noqa: BLE001
            pass

    def _connect_progress(self, phase: str) -> None:
        """The sources call in here during the blocking establishment (on the poller
        thread). We update ``self.latest`` immediately so the SSE thread pushes the
        phase live to the browser while poll is still blocking. Only meaningful while
        we're actually trying to connect — poll overwrites with a fresh snapshot later.

        Identical lines in a row are logged ONCE: without a cable the reconnect shouts
        "opening the cable" twice a second forever (1.9 MB of noise over one evening
        2026-08-18), which drowns out the lines you actually debug with.
        """
        if phase != self._last_phase_logged:
            ctx = self._engine_note() if phase.startswith("sending init") else ""
            self._conn_log(f"establish: {phase}{ctx}")
            self._last_phase_logged = phase
        self._conn = self._next_conn("connecting")
        self.latest = {
            **self.latest,
            "status": "connecting",
            "module": self._active,
            "source": self.source.name,
            "connect_phase": phase,
            "conn": self._conn,
            **_stamp(time.time()),
        }

    def _all_sources(self) -> list:
        return list(self._modules.values())

    def _apply_fault_watch(self) -> None:
        """Set the fault-polling cadence on all sources: 1 = every cycle (~0.5 s,
        catches intermittent faults), otherwise every 10th (~5 s, saves bus traffic)."""
        every = 1 if self._fault_watch else 10
        for s in self._all_sources():
            if hasattr(s, "fault_every"):
                s.fault_every = every

    def set_fault_watch(self, on: bool) -> "dict":
        """Turn fast fault-polling on/off (to catch e.g. three-amigos in the moment)."""
        self._fault_watch = bool(on)
        self._apply_fault_watch()
        return {"ok": True, "fault_watch": self._fault_watch}

    def _run_inline(self, action: str, params: "dict") -> "dict":
        """Run a command that doesn't touch K-line (see :data:`_INLINE_COMMANDS`)."""
        if action == "start_csv":
            return self.start_csv()
        if action == "stop_csv":
            return self.stop_csv()
        if action == "set_fault_watch":
            return self.set_fault_watch(params.get("on"))
        if action == "shutdown":
            return self.shutdown_host(params)
        if action == "delete_session":
            return self.delete_session(params)
        if action == "recording_options":
            return self.recording_options(params)
        if action == "split_session":
            return self.split_session()
        return _fail(f"unknown command: {action}", "bad_request")

    def _spawn_poweroff(self) -> None:
        """Fire the OS poweroff after a short delay so the HTTP reply flushes to the
        browser before the box goes down. Isolated so tests can stub it. ``sudo -n``
        fails fast instead of hanging if passwordless sudo is not configured."""
        def _go() -> None:
            time.sleep(1.0)
            try:
                subprocess.Popen(["sudo", "-n", "shutdown", "-h", "now"])
            except Exception:  # noqa: BLE001 — nothing to report to; the caller already replied
                pass
        threading.Thread(target=_go, daemon=True).start()

    def shutdown_host(self, params: "dict | None" = None) -> "dict":
        """Power off the host (the Pi in the car). Guarded by --allow-shutdown so dev
        on a laptop can never trigger it. A stopgap until proper power control exists."""
        if not self._allow_shutdown:
            return _fail("shutdown is not enabled on this host", "conflict")
        self._spawn_poweroff()
        return {"ok": True, "shutting_down": True}

    def enqueue_command(self, cmd: "dict", timeout: float = 8.0) -> "dict":
        """Queue a write command to the poller thread and wait for the result.

        Serialized with the polling so K-line access never collides."""
        action = cmd.get("action", "")
        if action in _INLINE_COMMANDS:
            # Immediate reply — must not get stuck behind an ongoing connection in the poller.
            try:
                res = self._run_inline(action, cmd.get("params") or {})
            except Exception as exc:  # noqa: BLE001
                res = _fail(f"{type(exc).__name__}: {exc}", "internal")
            self._record_command(action, res)
            return res
        why, code = self._refusal(action, cmd.get("params") or {})
        if why:
            if action not in _SERVER_COMMANDS:
                self._record_command(action, {"ok": False, "error": why})
            return _fail(why, code)
        holder = {"result": None, "event": threading.Event()}
        self._commands.put((cmd, holder))
        if holder["event"].wait(timeout):
            return holder["result"]
        # The poll thread did not answer in time (a slow establishment, a silent ECU): the
        # car side, not the request, is the problem → 504 (spec §2).
        return _fail("timeout — no response from the diagnostic layer", "car_timeout")

    def handle_error(self, request, client_address) -> None:
        """Silence harmless client disconnects (the browser closing fetch/SSE)."""
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)

    def modules(self) -> "list[str]":
        return list(self._modules)

    def legacy_menu(self, store_module: str) -> "list | None":
        """The admin Map view of a module (items with ok/maybe/todo), derived by
        :func:`openostler.catalog.legacy_menu`; the raw menu while the catalog is missing.
        None = no menu known for this module."""
        if store_module not in self._menus:
            return None
        try:
            from .. import catalog
        except ImportError:
            return self._menus.get(store_module)
        try:
            return catalog.legacy_menu(store_module)
        except (KeyError, ValueError):
            return self._menus.get(store_module)

    # ---- command gate (ADR-0008) -------------------------------------- #
    def store_module(self) -> str:
        """The registry/store module of the active source (its ``store_module``, else the
        canonical id of the active module)."""
        return getattr(self.source, "store_module", None) or _store_module_for(self._active)

    def refusal(self, action: str, params: "dict | None" = None) -> "str | None":
        """Why ``action`` must not run now (None = allowed); see :meth:`_refusal`."""
        return self._refusal(action, params)[0]

    def _refusal(self, action: str,
                 params: "dict | None" = None) -> "tuple[str | None, str | None]":
        """Why ``action`` must not run now (None = allowed).

        Server commands and the generic ``clear_faults``/``read_block`` are not module
        commands. Everything else that is registered goes through
        :func:`openostler.commands.refusal`; an unregistered action that looks like a module
        command (``output_*``, ``injector_*``, a SLABS actuator name …) is refused as unknown.
        While disconnected, no source command runs.

        → ``(why, code)``: the reason and its error ``code`` (``public_mode`` for a refusal
        only the public server makes, ``disconnected``, ``bad_request`` for an unknown
        action; None for the other policy refusals, which answer 400).
        """
        from .. import commands

        if action in _BUS_COMMANDS and not getattr(self.source, "touches_car", True):
            return ("the Brain never touches the car: the node reads it (ADR-0032), so "
                    f"{action} is not available with a node source"), "conflict"
        if action in PROBE_COMMANDS:
            # Probing an unknown car (detection, an init sweep) is Parked-only (spec §2).
            return self._probe_refusal(params), None
        if action in _SERVER_COMMANDS or action in _INLINE_COMMANDS:
            return None, None
        store = self.store_module()
        if action not in _GENERIC_SOURCE_COMMANDS:
            if commands.get(store, action) is None:
                if _looks_like_module_command(action):
                    return f"unknown action for {store}: {action}", "bad_request"
            else:
                trust = str((params or {}).get("trust", ""))
                why = commands.refusal(store, action, trust=trust, public=self._public)
                if why:
                    public_only = self._public and not commands.refusal(
                        store, action, trust=trust, public=False)
                    return why, ("public_mode" if public_only else None)
        if self._paused:
            return "disconnected — connect first", "disconnected"
        return None, None

    # ---- connection state ---------------------------------------------- #
    def _next_conn(self, status: "str | None") -> str:
        """Next snapshot `conn` from the current one and a poll/establish ``status``.

        * ``connected`` → connected (and remembered: this target has worked).
        * a failed poll: ``error`` if this target never connected (no cable, no answer),
          ``lost`` on the first failure after ``connected``, then ``reconnecting`` while
          the poll loop keeps retrying.
        * establishing (``connecting``): ``reconnecting`` after a loss, stays ``error`` while
          retrying a target that never answered, else ``connecting``.
        """
        if self._paused:
            return "disconnected"
        fixed = getattr(self.source, "conn_for", None)
        fixed = fixed(status) if fixed is not None else None
        if fixed is not None:  # the source defines its states (NodeSource spec §10)
            if fixed == "connected":
                self._ever_connected = True
            return fixed
        if status == "connected":
            self._ever_connected = True
            return "connected"
        if status == "needs-detect":
            return "disconnected"   # no profile: nothing is sent until a Parked detection
        if status == "connecting":
            if self._ever_connected:
                return "reconnecting"
            return "error" if self._conn == "error" else "connecting"
        if not self._ever_connected:
            return "error"
        return "lost" if self._conn == "connected" else "reconnecting"

    def _restart_conn(self) -> None:
        """A new target (module or port) or a manual connect: start over."""
        self._ever_connected = False
        self._conn = "disconnected" if self._paused else "connecting"

    def _port_info(self) -> "dict":
        """``{spec, resolved, candidates}`` for the snapshot; rescanned every couple of s."""
        now = time.monotonic()
        if self._port_cache is not None and now - self._port_cache[0] < _PORT_INFO_TTL:
            return self._port_cache[1]
        spec = self._scan_port or "auto"
        try:
            resolved: "str | None" = resolve_serial_port(spec)
        except (FileNotFoundError, OSError):
            resolved = None
        try:
            candidates = list_serial_ports()
        except Exception:  # noqa: BLE001 — never fell the poll loop over a port listing
            candidates = []
        info = {"spec": spec, "resolved": resolved, "candidates": candidates}
        self._port_cache = (now, info)
        return info

    def _decorate(self, snap: "dict", module: "str | None" = None) -> "dict":
        """Add the server-level snapshot fields (module, conn, ts, battery_v, port,
        active_test, gps, recording …) to a source snapshot."""
        snap["module"] = module or self._active  # which tab the data belongs to
        snap["logging"] = self._csv.status() if self._csv is not None else {"recording": False}
        snap["public"] = self._public  # the UI is simplified in public mode
        snap["fault_watch"] = self._fault_watch  # fast fault-polling on/off
        snap["allow_shutdown"] = self._allow_shutdown  # Settings "Shut down Pi" button
        snap["conn"] = self._conn
        snap.update(_stamp(time.time()))
        snap.setdefault("source_kind", getattr(self.source, "source_kind", "serial"))
        bat = (snap.get("signals") or {}).get("battery")
        if not isinstance(bat, dict):
            # A node's selected battery voltage when no ``battery`` field is present
            # (NodeSource spec §6.5); a stale one is never shown as the live voltage.
            sel = (snap.get("vss") or {}).get("Vehicle.LowVoltageBattery.CurrentVoltage")
            bat = ({"v": sel.get("value")} if isinstance(sel, dict) and not sel.get("stale")
                   else None)
        elif bat.get("stale") is True:
            bat = None  # a node's stale reading (per-signal ``stale``) is not the voltage now
        v = bat.get("v") if isinstance(bat, dict) else None
        snap["battery_v"] = (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool)
                             else None)
        snap["port"] = self._port_info()
        snap["active_test"] = dict(self._active_test) if self._active_test else None
        snap["gps"] = self._gps_snapshot()
        snap["recording"] = self._recording_status()
        snap["recording_sources"] = self.recording_sources()
        snap["link"] = self._kline_link_for(snap)
        return snap

    # ---- latched tests ------------------------------------------------- #
    def _note_command_result(self, action: str, result: "dict") -> None:
        """Set/clear ``active_test`` after a module action ran on the active source."""
        from .. import commands

        if not result.get("ok"):
            return
        if self._active_test and action == self._active_test["stop"]:
            self._active_test = None
        else:
            c = commands.get(self.store_module(), action)
            if c is not None and c.stop:
                now = time.time()
                # ``since`` (epoch s) is deprecated for ``since_utc``; removed in 0.2.0
                self._active_test = {"action": c.action, "label": c.label, "since": now,
                                     "since_utc": rfc3339_utc(now), "stop": c.stop}
        self.latest = {**self.latest,
                       "active_test": dict(self._active_test) if self._active_test else None}

    def _stop_active_test(self) -> None:
        """Send the stop action of a latched test before the session goes away (module
        switch, disconnect, port change). Best effort; the banner clears either way."""
        test = self._active_test
        if not test:
            return
        try:
            self.source.command(test["stop"], {})
        except Exception:  # noqa: BLE001
            pass
        self._active_test = None

    def _release_source(self) -> None:
        """Stop any latched test, then release the session (``disconnect`` → ``release()``)."""
        self._stop_active_test()
        try:
            self.source.disconnect()
        except Exception:  # noqa: BLE001
            pass

    def _disconnect(self) -> "dict":
        """Release the session and pause polling until ``connect``."""
        self._release_source()
        self._paused = True
        self._restart_conn()
        self.latest = self._decorate({"status": "disconnected", "source": self.source.name,
                                      "signals": {}, "faults": [], "connect_phase": None,
                                      "error": ""})
        return {"ok": True, "message": "disconnected", "conn": self._conn}

    def _connect(self) -> "dict":
        """Resume polling; the next poll establishes the session."""
        self._paused = False
        self._restart_conn()
        self.latest = self._decorate({**self.latest, "status": "connecting",
                                      "source": self.source.name, "connect_phase": None,
                                      "error": ""})
        return {"ok": True, "message": "connecting", "conn": self._conn}

    def _set_port(self, port: "str | None") -> "dict":
        """Use ``port`` (``auto`` or a device path) for every live source: release the
        session and reconnect with it."""
        spec = port.strip() if isinstance(port, str) else ""
        if not spec:
            return _fail("port required ('auto' or a device path)", "bad_request")
        if spec.startswith("/dev/tty."):
            return _fail("macOS: use the /dev/cu.* port, never /dev/tty.*", "bad_request")
        self._release_source()
        for src in self._all_sources():
            try:
                src.set_port(spec)
            except Exception:  # noqa: BLE001
                pass
        self._scan_port = spec
        self._port_cache = None
        self._paused = False
        self._restart_conn()
        self.latest = self._decorate({**self.latest, "status": "connecting", "signals": {},
                                      "faults": [], "connect_phase": None, "error": ""})
        return {"ok": True, "message": f"port: {spec}", "port": spec}

    def coverage(self) -> "dict":
        """Coverage per module: {module: {ok, maybe, total}} — drives the Map picker.
        Counted from :meth:`legacy_menu` (derived statuses, ADR-0008)."""
        cov: "dict[str, dict]" = {}
        for name in self._menus:
            menu = self.legacy_menu(name) or []
            ok = mb = tot = 0
            for group in menu:
                for item in group.get("items", []):
                    tot += 1
                    status = item.get("status")
                    if status == "ok":
                        ok += 1
                    elif status == "maybe":
                        mb += 1
            cov[name] = {"ok": ok, "maybe": mb, "total": tot}
        return cov

    def _select(self, name: "str | None") -> "dict":
        """Switch the active module: release the old session, activate the new one
        (established lazily on the next poll). K-line is a shared bus → only one session at a time.
        A legacy alias selects its canonical module."""
        name = _store_module_for(name) if name else name
        if name not in self._modules:
            return _fail(f"unknown module: {name}", "bad_request")
        if name != self._active:
            self._release_source()  # stop a latched test, then release the K-line session
            self._active = name
            self.source = self._modules[name]
            self._restart_conn()
            # preserve public/fault_watch/logging — otherwise the UI loses public mode
            self.latest = self._decorate({**self.latest, "status": "connecting",
                                          "source": self.source.name, "signals": {},
                                          "faults": [], "connect_phase": None, "error": ""},
                                         module=name)
        return {"ok": True, "message": f"module: {name}", "module": name}

    def _read_all_faults(self) -> "dict":
        """Basic mode: read fault codes from all modules sequentially. Releases the
        active session first (frees the K-line port), scans, then lets normal
        polling reconnect. Runs on the poller thread → serialized with the bus."""
        self._release_source()  # stop a latched test, free the port before the scan
        scan = self._fault_scan
        if scan is None:
            from ..faultscan import read_all as scan
        try:
            report = scan(self._scan_port)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return {"ok": True, "report": report}

    def start_csv(self, path: "str | None" = None) -> "dict":
        """Start logging live data to a CSV file (for the user — following temps etc.).
        Logs the ACTIVE module's signals, one row per poll. Idempotent."""
        from .logger import CsvLogger
        with self._csv_lock:  # start/stop on the HTTP thread, log() in the poller
            if self._csv is not None:
                return {"ok": True, "file": os.path.basename(self._csv.path),
                        "message": "already recording"}
            if path is None:
                path = os.path.join(self._csv_dir,
                                    f"livedata-{time.strftime('%Y%m%d-%H%M%S')}.csv")
            self._csv = CsvLogger(path)
        return {"ok": True, "file": os.path.basename(path), "path": path, "message": "recording"}

    def stop_csv(self) -> "dict":
        """Stop the CSV logging. Returns filename + number of rows."""
        with self._csv_lock:
            if self._csv is None:
                return {"ok": True, "message": "not recording", "rows": 0}
            rows, fname = self._csv.rows, os.path.basename(self._csv.path)
            self._csv = None
        return {"ok": True, "file": fname, "rows": rows, "message": "stopped"}

    def _drain_commands(self) -> None:
        while True:
            try:
                cmd, holder = self._commands.get_nowait()
            except queue.Empty:
                return
            action = cmd.get("action", "")
            try:
                if action == "select_module":
                    params = cmd.get("params") or {}
                    holder["result"] = self._select(params.get("module") or cmd.get("module"))
                elif action == "read_all_faults":
                    holder["result"] = self._read_all_faults()
                elif action == "detect_protocol":
                    holder["result"] = self._detect_protocol(cmd.get("params") or {})
                elif action == "module_scan":
                    holder["result"] = self._run_module_scan(cmd.get("params") or {})
                elif action == "disconnect":
                    holder["result"] = self._disconnect()
                elif action == "connect":
                    holder["result"] = self._connect()
                elif action == "set_port":
                    params = cmd.get("params") or {}
                    holder["result"] = self._set_port(params.get("port") or cmd.get("port"))
                elif action in _INLINE_COMMANDS:
                    holder["result"] = self._run_inline(action, cmd.get("params") or {})
                else:
                    # re-check on the poll thread: the module may have switched since queuing
                    why, code = self._refusal(action, cmd.get("params") or {})
                    if why:
                        holder["result"] = _fail(why, code)
                    else:
                        res = _car_coded(self.source.command(action, cmd.get("params")))
                        self._note_command_result(action, res)
                        holder["result"] = res
            except NegativeResponse as exc:  # the ECU refused: 502 with its NRC (spec §2)
                holder["result"] = _fail(f"{type(exc).__name__}: {exc}", "car_refused",
                                         nrc=exc.nrc)
            except Exception as exc:  # noqa: BLE001
                holder["result"] = _fail(f"{type(exc).__name__}: {exc}", "internal")
            if action not in _SERVER_COMMANDS:  # module commands (inline ones: enqueue_command)
                self._record_command(action, holder["result"])
            holder["event"].set()

    def _log_conn_transition(self, snap: "dict") -> None:
        """Log only when the status actually changes (connected↔error) or when
        the error text changes — otherwise a dropped cable would spam every ~0.5 s.
        Simulated sources (``simulated = True``, test fakes) aren't logged.

        The transition is keyed on (MODULE, status): if you switch from one connected
        module to another, the status is "connected" at both ends, and a plain status
        comparison then silences the new module's CONNECTED line. That hid a successful
        SLABS session 2026-08-18 23:08:54 ("session established" without CONNECTED) and
        made the log outright misleading during debugging.
        """
        status = snap.get("status")
        if getattr(self.source, "simulated", False):
            return  # a fake is always "connected" without a real session → nothing to log
        err = snap.get("error") or ""
        key = (snap.get("module"), status)
        if key == self._last_conn_status and err == self._last_conn_error:
            return
        if status == "connected":
            n = len(snap.get("signals") or {})
            self._conn_log(
                f"CONNECTED — {n} signals, {len(snap.get('faults') or [])} fault codes",
                module=snap.get("module"))
        elif status == "error":
            self._conn_log(f"ERROR — {err}", module=snap.get("module"))
        self._last_conn_status = key
        self._last_conn_error = err
        self._last_phase_logged = None  # new status → the next establishment phase is logged again

    def poll_once(self) -> "dict":
        """One poll of the active source → decorated snapshot in ``latest``, stepping the
        connection state machine. While disconnected, the source is not touched."""
        active = self._active
        if self._paused:
            self._conn = "disconnected"
            snap = self._decorate({"status": "disconnected", "source": self.source.name,
                                   "signals": {}, "faults": [], "connect_phase": None}, active)
            self.latest = snap
            return snap
        try:
            snap = self.source.poll()
        except Exception as exc:  # noqa: BLE001
            snap = {
                "status": "error", "source": self.source.name,
                "signals": {}, "faults": [], "error": f"{type(exc).__name__}: {exc}",
            }
        # An establishment aborted for a queued command (module switch …) says nothing
        # about the link: keep the current conn and let the command restart it.
        if "ConnectAborted" not in (snap.get("error") or ""):
            self._conn = self._next_conn(snap.get("status"))
        self._decorate(snap, active)
        self._remember_engine(snap)      # save engine context for the SLABS log
        self._log_conn_transition(snap)  # log connected/error transitions
        self.latest = snap
        return snap

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            self._drain_commands()  # writes first, serialized with poll
            self.poll_once()
            self.record_poll()  # always-on session logbook (also while paused: idle timer)
            if self._paused:
                self._stop.wait(self.poll_interval)
                continue
            self._tick_source()  # a due keep-alive between polls (K-line link sources)
            if self.logger is not None:
                try:
                    self.logger.log(self.latest)
                except Exception:  # noqa: BLE001 — a log error must never fell the poll loop
                    pass
            csv_log = self._csv  # local ref: stop_csv may null it mid-logging
            # Only record real rows: with CSV auto-started (--csv), this keeps
            # connecting/error rows (no cable / between reconnects) out of the file,
            # so an auto-logged CSV holds only the actual drive.
            if csv_log is not None and self.latest.get("status") == "connected":
                try:
                    csv_log.log(self.latest)
                except Exception:  # noqa: BLE001 — a CSV error must never fell the poll loop
                    pass
            self._stop.wait(self.poll_interval)
        self.close_recorder()

    def start_polling(self) -> None:
        self._start_index()
        if self._enricher is not None:
            try:
                self._enricher.start()
            except Exception as exc:  # noqa: BLE001 — no geocoder must never stop the dashboard
                self._conn_log(f"geo: start failed ({type(exc).__name__}: {exc})")
        if self.gps is not None:
            try:
                self.gps.start()
            except Exception as exc:  # noqa: BLE001 — no GPS must never stop the dashboard
                self._conn_log(f"gps: start failed ({type(exc).__name__}: {exc})")
        if not self._poller.is_alive():
            self._poller.start()

    def stop(self) -> None:
        """Stop polling, end the open session and stop the GPS source."""
        self._stop.set()
        if self._poller.is_alive() and self._poller is not threading.current_thread():
            self._poller.join(timeout=self.poll_interval + 2.0)
        self._stop_imu(reopen=False)
        # idempotent; also covers a poller stuck in establishment. Ending the session
        # closes its audio tracks and stops Pi audio.
        self.close_recorder()
        if self.gps is not None:
            try:
                self.gps.stop()
            except Exception:  # noqa: BLE001
                pass
        if self._enricher is not None:
            try:
                self._enricher.stop()
            except Exception:  # noqa: BLE001
                pass

    def serve(self) -> None:
        self.start_polling()
        if self.sniffer is not None:
            self.sniffer.start()
        try:
            self.serve_forever()
        finally:
            self.stop()
