"""Fault-screen import (T-30): labelled NanoCom fault screens paired with raw fault replies.

Synthetic captures: a Td5 `61 3B` block, the RDL016 SLABS and airbag replies, an ACE raw
block. Checks the verdicts (supported / text conflict / name proposal / not in raw), the
leftovers, and that write-back promotes only fully supported table rows.
"""
import shutil
from pathlib import Path

from d2diag.sniff import fault_import as fi
from d2diag.sniff.importer import collect_samples
from d2diag.sniff import capture

_REFS = Path(__file__).resolve().parents[1] / "references"


def _kwp(*payload: int) -> str:
    frame = [len(payload), *payload]
    frame.append(sum(frame) & 0xFF)
    return " ".join(f"{b:02x}" for b in frame)


def _log(tmp_path, rows) -> str:
    p = tmp_path / "cap.log"
    p.write_text("".join(rows), encoding="utf-8")
    return str(p)


def _screen(tmp_path, module, data_line, shown):
    rows = [f">>> screen {module}/faults\n", f"[10] {data_line}\n"]
    rows += [f">>> value fault={s}\n" for s in shown]
    return fi.import_faults(_log(tmp_path, rows))["screens"][0]


def _by_key(sc):
    return {r["key"]: r for r in sc["rows"]}


def test_td5_screen_verdicts(tmp_path):
    block = bytearray(35)
    block[0] |= 0x40    # 0.6 air flow (Logged Low), proven
    block[11] |= 0x40   # 11.6 glowplug lamp drive open load (Current), candidate
    block[9] |= 0x04    # 9.2 tachometer open load — shown with the wrong text below
    block[15] |= 0x80   # 15.7 no public name
    block[18] |= 0x40   # 18.6 no name and not displayed → leftover
    sc = _screen(tmp_path, "td5", _kwp(0x61, 0x3B, *block), [
        "(1,7) AIR FLOW CIRCUIT, (LOGGED LOW)",
        "(12,7) GLOWPLUG LAMP DRIVE OPEN LOAD, (CURRENT)",
        "(10,3) FUEL PUMP DRIVE OPEN LOAD, (LOGGED)",
        "(16,8) SOMETHING NEW, (LOGGED)",
        "(5,1) EGR INLET THROTTLE DIAGNOSTICS, (CURRENT)",
    ])
    r = _by_key(sc)
    assert r["0.6"]["verdict"] == "supported" and not r["0.6"]["promotable"]  # already proven
    assert r["11.6"]["verdict"] == "supported" and r["11.6"]["promotable"]    # candidate → proven
    assert r["9.2"]["verdict"] == "text conflict"
    assert r["15.7"]["verdict"] == "name proposal"
    assert r["4.0"]["verdict"] == "not in raw"
    assert sc["leftovers"] == ["18.6"]


def test_slabs_text_match_and_count(tmp_path):
    block = bytes.fromhex("00000010000000000000100000000000")  # RDL016 21 11
    sc = _screen(tmp_path, "slabs", _kwp(0x61, 0x11, *block), [
        "20-05 right front wheel speed sensor output too low intermittent 254 times",
        "11-05 shuttle valve electrical fail 011 times",
    ])
    rows = sc["rows"]
    assert [x["key"] for x in rows] == ["3.4", "10.4"]
    assert all(x["verdict"] == "supported" for x in rows)
    assert [x["count"] for x in rows] == [254, 11]
    assert sc["leftovers"] == []


def test_airbag_rdl016_reply(tmp_path):
    reply = "82 5b f7 21 02 1d 86 f7 5b 61 02 90 04 90 16 c4"
    sc = _screen(tmp_path, "airbag", reply, [
        "Code 004 - airbag warning lamp open circuit (intermittent)",
        "Code 022 - left hand pretensioner measures open circuit (intermittent)",
        "Code 008 - the drivers airbag measures open circuit (permanent)",
    ])
    r = _by_key(sc)
    assert sc["raw_keys"] == ["004", "022"]
    assert r["004"]["promotable"] and r["022"]["promotable"]
    assert r["008"]["verdict"] == "not in raw"


def test_ace_raw_kept_never_promoted(tmp_path):
    sc = _screen(tmp_path, "ace", "67 67 11 e0 e0 f0 f0 00 00 00 1a 00 00 08 09 80 92 00 00",
                 ["04-02 DCV 2 Current out of range"])
    [row] = sc["rows"]
    assert row["key"] == "04-02" and row["verdict"] == "text agrees" and not row["promotable"]
    assert sc["raw_lines"] and sc["raw_lines"][0].startswith("67 67 11")


def test_empty_screen_and_value_importer_skips_faults(tmp_path):
    rows = [">>> screen td5/faults\n", f"[1] {_kwp(0x61, 0x3B, *bytes(35))}\n",
            ">>> value fault=none\n"]
    path = _log(tmp_path, rows)
    sc = fi.import_faults(path)["screens"][0]
    assert sc["rows"] == [] and sc["raw_keys"] == [] and sc["leftovers"] == []
    assert collect_samples(capture.parse_log(path)) == {}  # live-data importer ignores fault=


def test_text_agrees_rejects_wrong_fault_kind():
    assert fi.text_agrees("the right hand pre-tensioner measures short to ground",
                          "Right-hand seat-belt pretensioner circuit, short to ground")
    assert not fi.text_agrees("right hand pretensioner measures open circuit",
                              "Right-hand seat-belt pretensioner circuit, short to ground")


def test_promote_in_reference_flips_only_candidate_rows(tmp_path):
    shutil.copy(_REFS / "airbag_fault_codes.md", tmp_path / "airbag_fault_codes.md")
    assert fi.promote_in_reference("airbag", "004", "cap.log", tmp_path)
    text = (tmp_path / "airbag_fault_codes.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| `004`"))
    assert "| proven |" in row and "proven: nanocom:cap.log (T-30)" in row
    assert not fi.promote_in_reference("airbag", "004", "cap.log", tmp_path)  # already proven
    assert not fi.promote_in_reference("td5", "11.6", "cap.log", tmp_path)    # decoder-owned


def test_report_renders(tmp_path):
    block = bytearray(35)
    block[11] |= 0x40
    rows = [">>> screen td5/faults\n", f"[1] {_kwp(0x61, 0x3B, *block)}\n",
            ">>> value fault=(12,7) GLOWPLUG LAMP DRIVE OPEN LOAD, (CURRENT)\n"]
    md = fi.render_fault_report(fi.import_faults(_log(tmp_path, rows)))
    assert "promotable" in md and "edit by hand" in md
