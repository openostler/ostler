"""Session exports: AiM-named CSV, Racelogic VBO and GPX 1.1 (ADR-0009).

Every exporter takes ``rows`` — a list of ``{channel: value}`` dicts in time order, with
``Interval`` (session ms) and ``Utc`` (epoch ms or None), numbers as int/float and the
text channels as str; missing = not sampled — and the session ``meta``, and returns text.
``notes`` (ADR-0010, the session's notes sorted by ``t``) adds markers: the CSV ``event``
column, VBO ``[comments]`` lines and an ``event1`` column, GPX ``<wpt>``s. ``notes_csv``
exports the notes themselves.
"""
from __future__ import annotations

import bisect
import time
from xml.sax.saxutils import escape, quoteattr

from . import channels as ch
from .recorder import fmt_num


def _columns(rows: "list[dict]", meta: dict, numeric_only: bool = False) -> "list[str]":
    cols = [c["name"] for c in meta.get("channels") or [] if isinstance(c, dict)]
    for r in rows:
        for k in r:
            if k not in cols and k not in ch.TIME_CHANNELS:
                cols.append(k)
    if numeric_only:
        cols = [c for c in cols if c not in ch.TEXT_CHANNELS]
    else:  # text channels last
        cols = [c for c in cols if c not in ch.TEXT_CHANNELS] + [
            c for c in cols if c in ch.TEXT_CHANNELS]
    return cols


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return fmt_num(v)


def nearest_index(times: "list[float]", t: float) -> "int | None":
    """Index of the value in sorted ``times`` nearest to ``t`` (earlier wins a tie)."""
    if not times:
        return None
    i = bisect.bisect_left(times, t)
    if i <= 0:
        return 0
    if i >= len(times):
        return len(times) - 1
    return i - 1 if t - times[i - 1] <= times[i] - t else i


def _note_marks(times: "list[float]", notes) -> "dict[int, list[dict]]":
    marks: "dict[int, list[dict]]" = {}
    for n in notes or []:
        if not isinstance(n, dict) or not isinstance(n.get("t"), (int, float)):
            continue
        i = nearest_index(times, n["t"])
        if i is not None:
            marks.setdefault(i, []).append(n)
    return marks


def _one_line(text) -> str:
    return " ".join(str(text or "").split())


def to_csv(rows: "list[dict]", meta: dict, notes=None) -> str:
    """CSV with AiM-style names: ``Time`` (s since start) then each channel. Sparse rows
    stay sparse. Text cells are quoted when needed. With notes, a last ``event`` column
    holds the note id(s) on the row nearest each note."""
    import csv
    import io

    cols = _columns(rows, meta)
    marks = _note_marks([r.get("Interval") or 0 for r in rows], notes) if notes else {}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Time", *[ch.export_name(c) for c in cols], *(["event"] if notes else [])])
    for i, r in enumerate(rows):
        t = r.get("Interval")
        ev = [";".join(n["id"] for n in marks.get(i, []))] if notes else []
        w.writerow([fmt_num((t or 0) / 1000.0, 3), *[_cell(r.get(c)) for c in cols], *ev])
    return buf.getvalue()


def _clock(meta: dict, t_ms: float) -> str:
    """UTC ISO time of session ms ``t_ms`` (from ``meta.start_utc``), or ''."""
    try:
        import calendar
        start = calendar.timegm(time.strptime(str(meta.get("start_utc"))[:19],
                                              "%Y-%m-%dT%H:%M:%S"))
    except (ValueError, TypeError):
        return ""
    return _iso_ms(start * 1000.0 + float(t_ms))


def notes_csv(notes, meta: dict) -> str:
    """The notes as CSV (``?fmt=notes``): one row per note, times in session seconds and
    UTC."""
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "time_s", "end_s", "utc", "kind", "source", "text", "tags",
                "created", "edited", "module", "lid", "raw", "value"])
    for n in notes or []:
        cap = n.get("capture") or {}
        t, t_end = n.get("t") or 0, n.get("t_end")
        w.writerow([n.get("id", ""), fmt_num(t / 1000.0, 3),
                    "" if t_end is None else fmt_num(t_end / 1000.0, 3), _clock(meta, t),
                    n.get("kind", ""), n.get("source", ""), n.get("text", ""),
                    ";".join(n.get("tags") or []), n.get("created") or "",
                    n.get("edited") or "", cap.get("module", ""), cap.get("lid", ""),
                    cap.get("raw", ""), cap.get("value", "")])
    return buf.getvalue()


def _vbo_time(utc_ms: "float | None", interval_ms: float) -> str:
    """UTC time of day ``hhmmss.ss``; session time when the UTC is unknown."""
    ms = int(round(utc_ms if utc_ms is not None else interval_ms)) % 86_400_000
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    return f"{h:02d}{m:02d}{rem / 1000.0:05.2f}"


def vbo_lat(lat_deg: float) -> str:
    """Latitude in minutes, North positive: ``+03121.20000``."""
    return f"{lat_deg * 60.0:+012.5f}"


def vbo_long(lon_deg: float) -> str:
    """Longitude in minutes with the sign inverted (West positive): ``+00072.00000``."""
    return f"{-lon_deg * 60.0:+012.5f}"


def to_vbo(rows: "list[dict]", meta: dict, notes=None) -> str:
    """Racelogic VBO: ``[header]``, ``[channel units]``, ``[comments]``,
    ``[column names]``, ``[data]``; space-delimited, CRLF. One data line per GPS sample
    (every row when the session has no GPS), other channels carried forward. Notes become
    ``[comments]`` lines and an ``event1`` column (1 on the line nearest each note)."""
    extra = [c for c in _columns(rows, meta, numeric_only=True)
             if not c.startswith("GPS_") or c in ch.GPS_ACCEL_CHANNELS]
    names = [ch.export_name(c) for c in extra]
    ev_names = ["event1"] if notes else []
    comments = []
    for n in notes or []:
        t = float(n.get("t") or 0) / 1000.0
        span = (f"-{float(n['t_end']) / 1000.0:.1f}s" if n.get("t_end") is not None else "s")
        tags = f" [{', '.join(n.get('tags') or [])}]" if n.get("tags") else ""
        text = _one_line(n.get("text")) or n.get("kind", "note")
        comments.append(f"Note {n.get('id', '')} at {t:.1f}{span}{tags}: {text}")
    start = meta.get("start_utc") or ""
    try:
        st = time.strptime(start[:19], "%Y-%m-%dT%H:%M:%S")
        created = time.strftime("%d/%m/%Y @ %H:%M:%S", st)
    except ValueError:
        created = start
    units = {c["name"]: c.get("units", "") for c in meta.get("channels") or []
             if isinstance(c, dict)}
    out = [f"File created on {created}", "", "[header]",
           "satellites", "time", "latitude", "longitude", "velocity kmh", "heading",
           "height", *names, *ev_names, "", "[channel units]",
           "", "s", "min", "min", "km/h", "deg", "m",
           *[units.get(c) or ch.UNITS.get(c, "") or "-" for c in extra],
           *["-" for _ in ev_names], "",
           "[comments]", f"Session {meta.get('id', '')} exported by Ostler (openostler).",
           "Latitude and longitude are in minutes; longitude is positive West.",
           "Time is UTC hhmmss.ss.", *comments, "",
           "[column names]",
           " ".join(["sats", "time", "lat", "long", "velocity", "heading", "height",
                     *names, *ev_names]), "", "[data]"]
    has_gps = any(r.get("GPS_Latitude") is not None for r in rows)
    emitted = [r for r in rows if not has_gps or r.get("GPS_Latitude") is not None]
    marks = _note_marks([r.get("Interval") or 0 for r in emitted], notes) if notes else {}
    line_no = -1
    last: dict = {}
    for r in rows:
        for k, v in r.items():
            if v is not None and not isinstance(v, str):
                last[k] = v
        if has_gps and r.get("GPS_Latitude") is None:
            continue
        line_no += 1
        lat = float(last.get("GPS_Latitude", 0.0))
        lon = float(last.get("GPS_Longitude", 0.0))
        line = [
            f"{int(last.get('GPS_Nsat', 0)):03d}",
            _vbo_time(r.get("Utc"), r.get("Interval") or 0),
            vbo_lat(lat), vbo_long(lon),
            f"{float(last.get('GPS_Speed', 0.0)):07.3f}",
            f"{float(last.get('GPS_Heading', 0.0)) % 360:06.2f}",
            f"{float(last.get('GPS_Altitude', 0.0)):+09.2f}",
            *[fmt_num(last.get(c, 0), 4) for c in extra],
            *(["1" if line_no in marks else "0"] if notes else []),
        ]
        out.append(" ".join(line))
    return "\r\n".join(out) + "\r\n"


def _iso_ms(utc_ms: float) -> str:
    ms = int(round(utc_ms))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def _gpx_wpts(rows: "list[dict]", notes) -> "list[str]":
    pts = [r for r in rows if isinstance(r.get("GPS_Latitude"), (int, float))
           and isinstance(r.get("GPS_Longitude"), (int, float))]
    if not pts or not notes:
        return []
    times = [r.get("Interval") or 0 for r in pts]
    out = []
    for n in notes:
        if not isinstance(n.get("t"), (int, float)):
            continue
        r = pts[nearest_index(times, n["t"])]
        inner = []
        if isinstance(r.get("GPS_Altitude"), (int, float)):
            inner.append(f"<ele>{fmt_num(r['GPS_Altitude'], 1)}</ele>")
        if isinstance(r.get("Utc"), (int, float)):
            inner.append(f"<time>{_iso_ms(r['Utc'])}</time>")
        name = _one_line(n.get("text")) or str(n.get("kind") or "note")
        inner.append(f"<name>{escape(name[:80])}</name>")
        if n.get("text"):
            inner.append(f"<desc>{escape(_one_line(n.get('text')))}</desc>")
        inner.append(f"<type>{escape(str(n.get('kind') or 'note'))}</type>")
        out.append(f"  <wpt lat={quoteattr(fmt_num(r['GPS_Latitude'], 7))} "
                   f"lon={quoteattr(fmt_num(r['GPS_Longitude'], 7))}>" + "".join(inner)
                   + "</wpt>")
    return out


def to_gpx(rows: "list[dict]", meta: dict, notes=None) -> str:
    """GPX 1.1 with one track segment of every GPS point; ``<time>`` when ``Utc`` is known.
    Each note becomes a ``<wpt>`` at the GPS point nearest its time (when GPS exists)."""
    sid = escape(str(meta.get("id", "")))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<gpx version="1.1" creator="openostler" xmlns="http://www.topografix.com/GPX/1/1">',
           "  <metadata>", f"    <name>{sid}</name>"]
    if meta.get("start_utc"):
        out.append(f"    <time>{escape(str(meta['start_utc']))}</time>")
    out += ["  </metadata>", *_gpx_wpts(rows, notes), "  <trk>", f"    <name>{sid}</name>", "    <trkseg>"]
    for r in rows:
        lat, lon = r.get("GPS_Latitude"), r.get("GPS_Longitude")
        if lat is None or lon is None or isinstance(lat, str) or isinstance(lon, str):
            continue
        pt = f"      <trkpt lat={quoteattr(fmt_num(lat, 7))} lon={quoteattr(fmt_num(lon, 7))}>"
        inner = []
        if isinstance(r.get("GPS_Altitude"), (int, float)):
            inner.append(f"<ele>{fmt_num(r['GPS_Altitude'], 1)}</ele>")
        if isinstance(r.get("Utc"), (int, float)):
            inner.append(f"<time>{_iso_ms(r['Utc'])}</time>")
        out.append(pt + "".join(inner) + "</trkpt>")
    out += ["    </trkseg>", "  </trk>", "</gpx>"]
    return "\n".join(out) + "\n"
