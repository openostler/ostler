"""The NanoCom capture importer: markers → automap → candidate store records.

A synthetic capture built from KNOWN Td5 LIDs must reproduce the proven mappings
(rpm = 09 ×1, battery = 10 ×0.001, coolant = 1A ×0.1 − 273.2), prove that a constant
decoy LID is rejected, and that --write lands candidates in a temp store.
"""
import json

import pytest

import tools.esp32_read as reader
from d2diag.sniff import importer
from d2diag.sniff.importer import collect_samples, import_capture, parse_marker


def _frame(lid: int, value: int) -> str:
    """A `61 <lid> <hi> <lo>` ReadDataByLocalId response with a valid checksum."""
    payload = [0x61, lid, (value >> 8) & 0xFF, value & 0xFF]
    frame = [len(payload)] + payload
    frame.append(sum(frame) & 0xFF)
    return " ".join(f"{b:02x}" for b in frame)


def _line(ms: int, *frames: str) -> str:
    return f"[{ms}] " + " ".join(frames) + "\n"


# A screen that polls rpm(09), battery(10) and coolant(1A); only `vary` moves per reading.
def _capture(tmp_path):
    log = tmp_path / "nanocom.log"
    rows = ["=== SESSION ===\n", "[0] 81 13 f7 81 0c\n"]  # Td5 fast init

    def screen(name, lid_values_per_sample, const):
        rows.append(f">>> screen td5/{name}\n")
        for ms, (lid, val, text) in lid_values_per_sample:
            frames = [_frame(lid, val)] + [_frame(c, cv) for c, cv in const.items()]
            rows.append(_line(ms, *frames))
            rows.append(f">>> value {name}={text}\n")

    screen("rpm", [(10, (0x09, 762, "762")), (20, (0x09, 1500, "1500")),
                   (30, (0x09, 2200, "2200"))],
           const={0x10: 13000, 0x1A: 3550})
    screen("battery", [(40, (0x10, 14200, "14.2")), (50, (0x10, 12000, "12.0"))],
           const={0x09: 800, 0x1A: 3550})
    screen("coolant", [(60, (0x1A, 3532, "80.0")), (70, (0x1A, 3632, "90.0"))],
           const={0x09: 800, 0x10: 13000})
    log.write_text("".join(rows), encoding="utf-8")
    return str(log)


def test_parse_marker_forms():
    assert parse_marker("screen td5/fuelling") == {"kind": "screen", "module": "td5", "page": "fuelling"}
    assert parse_marker("value rpm=1500") == {"kind": "value", "name": "rpm", "text": "1500"}
    assert parse_marker("just a note")["kind"] == "note"


def test_expand_marker_shorthand_matches_parse():
    assert reader.expand_marker("s td5/rpm") == "screen td5/rpm"
    assert reader.expand_marker("v rpm=1500") == "value rpm=1500"
    assert reader.expand_marker("free text") == "free text"


def test_collect_groups_values_by_module_and_name(tmp_path):
    from d2diag.sniff import capture
    events = capture.parse_log(_capture(tmp_path))
    grouped = collect_samples(events)
    assert ("td5", "rpm") in grouped
    assert len(grouped[("td5", "rpm")]["samples"]) == 3
    assert "09" in grouped[("td5", "rpm")]["lids"]


def test_import_reproduces_known_td5_mappings(tmp_path):
    report = import_capture(_capture(tmp_path))
    by_name = {m["name"]: m for m in report["mappings"]}

    rpm = by_name["rpm"]["result"]
    assert rpm["ok"] and rpm["lid"] == "09" and rpm["offset"] == 0
    assert rpm["scale"] == 1.0

    batt = by_name["battery"]["result"]
    assert batt["ok"] and batt["lid"] == "10" and batt["scale"] == 0.001

    cool = by_name["coolant"]["result"]
    assert cool["ok"] and cool["lid"] == "1a" and cool["scale"] == 0.1
    assert cool["bias"] == pytest.approx(-273.2, abs=0.5)


def test_write_persists_candidates(tmp_path, monkeypatch):
    # Redirect the signal store to a temp dir so the test never touches the real JSON.
    import d2diag.signals as sig
    monkeypatch.setattr(sig, "_DIR", tmp_path)
    sig._CACHE.clear()

    report = import_capture(_capture(tmp_path), write=True, module_filter="td5")
    assert all(m["stored"] for m in report["mappings"] if m["result"]["ok"])

    stored = json.loads((tmp_path / "td5.json").read_text(encoding="utf-8"))
    names = {r["name"]: r for r in stored}
    assert names["rpm"]["confidence"] == "candidate"
    assert names["rpm"]["source"].startswith("nanocom:")
    assert names["battery"]["scale"] == 0.001
