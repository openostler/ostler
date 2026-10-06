# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Session exports: AiM-named CSV, Racelogic VBO, GPX 1.1 (ADR-0009)."""

import pytest

import csv
import io
import xml.etree.ElementTree as ET

from openostler.logbook.channels import export_name, group_for
from openostler.logbook.export import to_csv, to_gpx, to_vbo, vbo_lat, vbo_long
from openostler.logbook.store import SessionStore

pytestmark = pytest.mark.fake_pack

META = {"id": "20261006T090000Z", "start_utc": "2026-10-06T09:00:00.000Z",
        "channels": [{"name": "GPS_Speed", "units": "km/h", "group": "gps"},
                     {"name": "rpm", "units": "rpm", "group": "engine"},
                     {"name": "coolant_temp", "units": "°C", "group": "temperatures"}]}
UTC0 = 1791277200000  # 2026-10-06T09:00:00Z
ROWS = [
    {"Interval": 0, "Utc": UTC0, "GPS_Latitude": 52.0, "GPS_Longitude": -1.5, "GPS_Speed": 36.0,
     "GPS_Heading": 90.0, "GPS_Altitude": 100.0, "GPS_Nsat": 9, "rpm": 1500,
     "coolant_temp": 80.5, "module": "motor", "faults": "P0100, P0200"},
    {"Interval": 250, "Utc": UTC0 + 250, "rpm": 1510},
    {"Interval": 500, "Utc": UTC0 + 500, "GPS_Latitude": 52.0001, "GPS_Longitude": -1.5001,
     "GPS_Speed": 37.5, "GPS_Heading": 91.0, "GPS_Altitude": 100.5, "GPS_Nsat": 10},
]


@pytest.mark.needs_pack
def test_export_names():
    assert export_name("rpm") == "RPM"
    assert export_name("speed") == "Speed"
    assert export_name("coolant_temp") == "Water_Temp"
    assert export_name("GPS_Latitude") == "GPS_Latitude"
    assert export_name("Interval") == "Time"
    assert export_name("egr_inlet") == "Egr_Inlet"
    assert group_for("rpm") == "engine" and group_for("GPS_HDOP") == "gps"


def test_csv_aim_names_and_time_in_seconds():
    rows = list(csv.reader(io.StringIO(to_csv(ROWS, META))))
    head = rows[0]
    assert head[:4] == ["Time", "GPS_Speed", "RPM", "Water_Temp"]
    assert "GPS_Latitude" in head and head[-2:] == ["Module", "Faults"]
    assert [r[0] for r in rows[1:]] == ["0", "0.25", "0.5"]
    assert rows[1][head.index("Faults")] == "P0100, P0200"
    assert rows[2][head.index("Water_Temp")] == ""  # sparse stays sparse


def test_vbo_coordinate_convention():
    assert vbo_lat(52.0) == "+03120.00000"
    assert vbo_lat(-33.5) == "-02010.00000"
    assert vbo_long(-1.5) == "+00090.00000"  # West is positive in VBO
    assert vbo_long(2.25) == "-00135.00000"


def test_vbo_sections_and_data():
    text = to_vbo(ROWS, META)
    assert "\r\n" in text and "\n" not in text.replace("\r\n", "")
    lines = text.split("\r\n")
    assert lines[0].startswith("File created on 06/10/2026")
    idx = [lines.index(s) for s in ("[header]", "[channel units]", "[comments]",
                                    "[column names]", "[data]")]
    assert idx == sorted(idx)
    cols = lines[idx[3] + 1].split(" ")
    assert cols[:7] == ["sats", "time", "lat", "long", "velocity", "heading", "height"]
    assert "RPM" in cols and "Water_Temp" in cols and "Module" not in cols
    data = [ln for ln in lines[idx[4] + 1:] if ln]
    assert len(data) == 2  # one line per GPS sample
    first = data[0].split(" ")
    assert len(first) == len(cols)
    assert first[:7] == ["009", "090000.00", "+03120.00000", "+00090.00000", "036.000",
                         "090.00", "+00100.00"]
    second = data[1].split(" ")
    assert second[1] == "090000.50" and second[cols.index("RPM")] == "1510"  # carried forward
    header = lines[idx[0] + 1:idx[1]]
    assert header[:7] == ["satellites", "time", "latitude", "longitude", "velocity kmh",
                          "heading", "height"]


def test_vbo_time_falls_back_to_session_time():
    rows = [{"Interval": 61_250, "Utc": None, "GPS_Latitude": 1.0, "GPS_Longitude": 1.0}]
    data = to_vbo(rows, META).split("[data]\r\n")[1]
    assert data.split(" ")[1] == "000101.25"


def test_gpx_is_valid_track():
    root = ET.fromstring(to_gpx(ROWS, META).encode("utf-8"))
    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    assert root.tag == "{http://www.topografix.com/GPX/1/1}gpx" and root.get("version") == "1.1"
    pts = root.findall("g:trk/g:trkseg/g:trkpt", ns)
    assert len(pts) == 2
    assert float(pts[0].get("lat")) == pytest.approx(52.0)
    assert float(pts[0].get("lon")) == pytest.approx(-1.5)
    assert pts[0].find("g:time", ns).text == "2026-10-06T09:00:00.000Z"
    assert pts[1].find("g:ele", ns).text == "100.5"
    no_time = to_gpx([{"Interval": 0, "Utc": None, "GPS_Latitude": 1.0, "GPS_Longitude": 2.0}], META)
    assert "<trkpt" in no_time and "<time>" not in no_time.split("</metadata>")[1]


@pytest.mark.parametrize("fmt,ext,ctype", [("csv", "csv", "text/csv"), ("vbo", "vbo", "text/plain"),
                                           ("gpx", "gpx", "application/gpx+xml")])
@pytest.mark.needs_pack
def test_store_export_demo(tmp_path, fmt, ext, ctype):
    store = SessionStore(str(tmp_path))
    name, content_type, body = store.export("20261005T090000Z", fmt, public=True)
    assert name == f"20261005T090000Z.{ext}" and content_type.startswith(ctype)
    assert len(body) > 1000
    if fmt == "gpx":
        ET.fromstring(body)
    with pytest.raises(ValueError):
        store.export("20261005T090000Z", "xrk")


# ------------------------------------------------ notes in exports (ADR-0010) -- #

NOTES = [
    {"id": "aaaa0001", "t": 240, "t_end": None, "text": "Clunk\nfront left", "tags": ["noise"],
     "kind": "note", "source": "live", "created": "2026-10-06T09:00:01.000Z", "edited": None,
     "capture": None},
    {"id": "bbbb0002", "t": 480, "t_end": 900, "text": "", "tags": [], "kind": "mark",
     "source": "retro", "created": "2026-10-06T09:05:00.000Z", "edited": None, "capture": None},
]


def test_csv_event_column_at_nearest_row():
    rows = list(csv.reader(io.StringIO(to_csv(ROWS, META, notes=NOTES))))
    assert rows[0][-1] == "event"
    assert [r[-1] for r in rows[1:]] == ["", "aaaa0001", "bbbb0002"]
    assert to_csv(ROWS, META) == to_csv(ROWS, META, notes=[])  # no notes: unchanged


def test_notes_csv():
    from openostler.logbook.export import notes_csv
    cap = dict(NOTES[1], id="cccc0003", kind="capture", t=1000,
               capture={"module": "td5", "lid": "09", "raw": "02 fa", "value": "762"})
    rows = list(csv.reader(io.StringIO(notes_csv([*NOTES, cap], META))))
    assert rows[0][:8] == ["id", "time_s", "end_s", "utc", "kind", "source", "text", "tags"]
    assert rows[1][:8] == ["aaaa0001", "0.24", "", "2026-10-06T09:00:00.240Z", "note", "live",
                           "Clunk\nfront left", "noise"]
    assert rows[2][2] == "0.9" and rows[3][-4:] == ["td5", "09", "02 fa", "762"]


def test_vbo_comments_and_event_column():
    lines = to_vbo(ROWS, META, notes=NOTES).split("\r\n")
    c0, c1 = lines.index("[comments]"), lines.index("[column names]")
    comments = lines[c0:c1]
    assert "Note aaaa0001 at 0.2s [noise]: Clunk front left" in comments
    assert "Note bbbb0002 at 0.5-0.9s: mark" in comments
    cols = lines[c1 + 1].split(" ")
    assert cols[-1] == "event1"
    assert "[header]" in lines
    h1 = lines.index("[channel units]")
    assert lines[h1 - 2] == "event1"
    data = [ln.split(" ") for ln in lines[lines.index("[data]") + 1:] if ln]
    assert [d[-1] for d in data] == ["1", "1"]  # 240 ms → the 0 ms line, 480 ms → 500 ms
    assert all(len(d) == len(cols) for d in data)


def test_gpx_waypoints_per_note():
    root = ET.fromstring(to_gpx(ROWS, META, notes=NOTES).encode("utf-8"))
    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    wpts = root.findall("g:wpt", ns)
    assert len(wpts) == 2
    assert wpts[0].get("lat") == "52" and wpts[0].find("g:name", ns).text == "Clunk front left"
    assert wpts[1].get("lat") == "52.0001" and wpts[1].find("g:type", ns).text == "mark"
    assert wpts[0].find("g:time", ns).text == "2026-10-06T09:00:00.000Z"
    assert list(root).index(wpts[-1]) < list(root).index(root.find("g:trk", ns))  # schema order
    no_gps = to_gpx([{"Interval": 0, "Utc": None, "rpm": 1}], META, notes=NOTES)
    assert "<wpt" not in no_gps


@pytest.mark.needs_pack
def test_store_exports_demo_notes(tmp_path):
    store = SessionStore(str(tmp_path))
    name, ctype, body = store.export("20261005T090000Z", "notes", public=True)
    assert name == "20261005T090000Z.notes.csv" and ctype.startswith("text/csv")
    assert len(body.decode().strip().split("\n")) == 4
    _, _, gpx = store.export("20261005T090000Z", "gpx", public=True)
    assert gpx.count(b"<wpt") == 3
    _, _, text = store.export("20261005T090000Z", "csv", public=True)
    rows = list(csv.reader(io.StringIO(text.decode())))
    assert rows[0][-1] == "event" and sum(1 for r in rows[1:] if r[-1]) == 3
    assert "GPS_LonAcc" in rows[0] and "Height_Left" in rows[0]
