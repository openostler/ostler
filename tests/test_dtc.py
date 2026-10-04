"""The fault-meaning store (d2diag.dtc): loader, enrich join, and freshness guards."""
import re

import tools.gen_dtc_seed as seed
import tools.gen_fault_docs as docs
from d2diag import dtc
from d2diag.td5.faults import FAULTS


def _td5_key(f):
    return f"{f.offset}.{f.mask.bit_length() - 1}"


def test_meanings_load_with_shape():
    m = dtc.load_meanings("td5")
    assert m, "td5 meanings should load"
    coolant = dtc.meaning("td5", "1.2")  # coolant temp. circuit (Logged Low)
    assert coolant and coolant.description and coolant.pcode == "P0115"


def test_enrich_td5_named_fault():
    [row] = dtc.enrich("td5", ["coolant temp. circuit (Logged Low)"])
    assert row["key"] == "1.2" and row["pcode"] == "P0115"
    assert "sensor-circuit" in row["description"] and row["cause"]


def test_enrich_td5_generic_bit_resolves():
    # The decoder emits byte<off>.bit<n> for any set bit; enrich maps it back to its meaning.
    [row] = dtc.enrich("td5", ["byte18.bit1"])  # offset 18 bit 1 = can rx/tx error (Logged)
    assert row["key"] == "18.1" and "can" in row["name"].lower()


def test_enrich_passes_unknown_through():
    [row] = dtc.enrich("td5", ["byte99.bit7"])  # not a real fault
    assert row["name"] == "byte99.bit7" and row["key"] == ""  # never dropped, no crash


def test_td5_store_covers_every_decoder_bit():
    """The coverage guard: every named Td5 fault has a meaning (keeps the store honest
    as faults.py grows — re-run tools/gen_dtc_seed.py to fill new bits)."""
    store = set(dtc.load_meanings("td5"))
    missing = sorted({_td5_key(f) for f in FAULTS} - store)
    assert not missing, f"td5 fault bits without a meaning: {missing}"


def test_slabs_meanings_load():
    m = dtc.load_meanings("slabs")
    assert m and "rsw-012" in m and m["rsw-012"].system.startswith("brakes")
    assert "012" not in m  # rsw numbering is not the reference tool's — never a bare number


def test_seed_store_is_in_sync():
    """What the seeder would build matches what is committed (no stale/missing entries)."""
    for module, build in seed._BUILDERS.items():
        built = {r["key"] for r in build()}
        stored = set(dtc.load_meanings(module))
        assert built <= stored, f"{module}: seeder would add {sorted(built - stored)}"


def test_fault_dictionary_docs_are_fresh():
    """Generated docs match the store (the --check guard, as a test)."""
    for path, text in docs._targets().items():
        assert path.read_text(encoding="utf-8") == text, (
            f"{path.name} is stale — run tools/gen_fault_docs.py")


# --- coverage + confidence (specs/2026-10-04-dtc-coverage-design.md) ---------------

_MODULES = ("td5", "slabs", "airbag", "autobox", "ace")


def test_every_record_has_honest_confidence():
    """Every meaning says how sure it is; nothing sourced from a forum/vendor list is proven."""
    for module in _MODULES:
        rows = dtc.load_records(module)
        assert rows, f"{module} store is empty"
        for r in rows:
            assert r.get("confidence") in ("proven", "candidate"), (module, r["key"])
            assert r.get("source"), (module, r["key"])
            src = r["source"].lower()
            if "http" in src or "rswsolutions" in src or "forum" in src:
                assert r["confidence"] == "candidate", (module, r["key"], "forum ≠ proven")


def test_new_module_stores_load_with_expected_keys():
    assert dtc.meaning("airbag", "008").name.lower().startswith("driver")
    assert dtc.meaning("autobox", "P1884-33") and "torque" in dtc.meaning("autobox", "P1884-33").name
    assert dtc.meaning("ace", "flat-20-04") and dtc.meaning("ace", "dtc33")
    # this car's NanoCom family owns the plain XX-YY keys (04-02 and 06-01 were seen on RDL 016)
    assert "direction control valve 2" in dtc.meaning("ace", "04-02").name.lower()
    assert "pressure too low" in dtc.meaning("ace", "06-01").name.lower()
    # the three ACE display schemes stay apart: every key belongs to exactly one
    for k in dtc.load_meanings("ace"):
        assert re.fullmatch(r"\d{2}-\d{2}|flat-\d{2}-\d{2}|dtc\d{1,2}", k), k


def test_airbag_decoder_number_resolves():
    from d2diag.airbag.faults import decode_faults
    nums = [str(f["number"]) for f in decode_faults(bytes.fromhex("9004901600 00".replace(" ", "")))]
    rows = dtc.enrich("airbag", nums)  # 4 → "004", 22 → "022"
    assert [r["key"] for r in rows] == ["004", "022"]
    assert all(r["confidence"] == "candidate" for r in rows)


def test_slabs_car_anchors_resolve_to_proven_tool_meaning():
    """The car-proven anchors resolve by raw bit / decoder text, never via a display number."""
    from d2diag.slabs.faults import decode_fault_block
    block = bytes.fromhex("00000010000000000000100000000000")  # sniff 2026-08-07
    rows = dtc.enrich("slabs", decode_fault_block(block))
    assert [r["key"] for r in rows] == ["3.4", "10.4"]
    assert "wheel speed" in rows[0]["name"].lower() and rows[0]["confidence"] == "proven"
    assert "shuttle valve" in rows[1]["name"].lower() and rows[1]["confidence"] == "proven"
    assert all(k in ("3.4", "10.4") or k.startswith("rsw-") for k in dtc.load_meanings("slabs"))
    [unk] = dtc.enrich("slabs", ["unknown (byte 3, bit 4)"])  # generic form resolves by bit
    assert unk["key"] == "3.4"


def test_td5_candidate_bit_and_unknowns_stay_generic():
    from d2diag.td5.faults import FAULTS, decode_faults
    cand = [f"{f.offset}.{f.mask.bit_length() - 1}" for f in FAULTS if f.confidence != "proven"]
    assert sorted(cand) == ["11.6", "13.6", "20.7"]
    assert all(dtc.meaning("td5", k).confidence == "candidate" for k in cand)
    # 11.6 / 13.6 corrected from NanoCom screens: the glow-plug LAMP, not a second "relay"
    for k in ("11.6", "13.6"):
        assert dtc.meaning("td5", k).name == "glowplug lamp drive open load (Current)"
        assert not dtc.meaning("td5", k).pcode
    block = bytearray(35)
    block[20] |= 0x80   # 20.7 candidate → named
    block[15] |= 0x80   # 15.7 seen on the car, no public name → stays generic
    out = decode_faults(bytes(block))
    assert "injector trim data corrupted (Logged)" in out and "byte15.bit7" in out


def test_enrich_resolves_a_tagged_generic_td5_bit():
    # The decoder tags unknown bits with their byte's group: "byte18.bit1 (Logged)".
    [row] = dtc.enrich("td5", ["byte18.bit1 (Logged)"])
    assert row["key"] == "18.1"
