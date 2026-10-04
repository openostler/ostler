"""Session exports: AiM-named CSV, Racelogic VBO and GPX 1.1 (ADR-0009).

Every exporter takes ``rows`` — a list of ``{channel: value}`` dicts in time order, with
``Interval`` (session ms) and ``Utc`` (epoch ms or None), numbers as int/float and the
text channels as str; missing = not sampled — and the session ``meta``, and returns text.
"""
from __future__ import annotations

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


def to_csv(rows: "list[dict]", meta: dict) -> str:
    """CSV with AiM-style names: ``Time`` (s since start) then each channel. Sparse rows
    stay sparse. Text cells are quoted when needed."""
    import csv
    import io

    cols = _columns(rows, meta)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Time", *[ch.export_name(c) for c in cols]])
    for r in rows:
        t = r.get("Interval")
        w.writerow([fmt_num((t or 0) / 1000.0, 3), *[_cell(r.get(c)) for c in cols]])
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


def to_vbo(rows: "list[dict]", meta: dict) -> str:
    """Racelogic VBO: ``[header]``, ``[channel units]``, ``[comments]``,
    ``[column names]``, ``[data]``; space-delimited, CRLF. One data line per GPS sample
    (every row when the session has no GPS), other channels carried forward."""
    extra = [c for c in _columns(rows, meta, numeric_only=True) if not c.startswith("GPS_")]
    names = [ch.export_name(c) for c in extra]
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
           "height", *names, "", "[channel units]",
           "", "s", "min", "min", "km/h", "deg", "m",
           *[units.get(c) or ch.UNITS.get(c, "") or "-" for c in extra], "",
           "[comments]", f"Session {meta.get('id', '')} exported by d2diag.",
           "Latitude and longitude are in minutes; longitude is positive West.",
           "Time is UTC hhmmss.ss.", "",
           "[column names]",
           " ".join(["sats", "time", "lat", "long", "velocity", "heading", "height",
                     *names]), "", "[data]"]
    has_gps = any(r.get("GPS_Latitude") is not None for r in rows)
    last: dict = {}
    for r in rows:
        for k, v in r.items():
            if v is not None and not isinstance(v, str):
                last[k] = v
        if has_gps and r.get("GPS_Latitude") is None:
            continue
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
        ]
        out.append(" ".join(line))
    return "\r\n".join(out) + "\r\n"


def _iso_ms(utc_ms: float) -> str:
    ms = int(round(utc_ms))
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + f".{ms % 1000:03d}Z"


def to_gpx(rows: "list[dict]", meta: dict) -> str:
    """GPX 1.1 with one track segment of every GPS point; ``<time>`` when ``Utc`` is known."""
    sid = escape(str(meta.get("id", "")))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<gpx version="1.1" creator="d2diag" xmlns="http://www.topografix.com/GPX/1/1">',
           "  <metadata>", f"    <name>{sid}</name>"]
    if meta.get("start_utc"):
        out.append(f"    <time>{escape(str(meta['start_utc']))}</time>")
    out += ["  </metadata>", "  <trk>", f"    <name>{sid}</name>", "    <trkseg>"]
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
