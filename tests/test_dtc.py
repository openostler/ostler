"""The fault-meaning store (d2diag.dtc): loader, enrich join, and freshness guards."""
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
    assert m and "012" in m and m["012"].system.startswith("brakes")


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
