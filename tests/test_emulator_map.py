"""Hardware-free tests for the NanoCom emulator menu-tree parser.

The real emulator JSON is a gitignored third-party reference (captures/nanocom/), so these
tests drive the parsing logic with a small synthetic fixture. A second, skippable test
checks the real export's module counts when it is present locally.
"""
from __future__ import annotations

import json
import os

import pytest

from d2diag.sniff import emulator_map as em


def _page(image, *areas):
    return {"kind": "page", "image": image, "title": "", "areas": list(areas)}


def _nav(label, target):
    return {"label": label, "action": {"type": "navigate", "target": target}}


# A miniature emulator graph mirroring the real shape: a module with a faults leaf (two
# pages), an inputs submenu with one paginated leaf, and the "Open <name>" labels the parser
# turns into display names.
FIXTURE = {
    "version": 1,
    "pages": {
        "homepage": {"discovery": {"td5": {
            "page1": _page("/images/list.jpg",
                           _nav("Open td5 engine", "homepage/discovery/td5/td5_engine/page1")),
            "td5_engine": {
                "page1": _page("/images/td5.jpg",
                               _nav("Open faults", "homepage/discovery/td5/td5_engine/faults/page1"),
                               _nav("Open inputs", "homepage/discovery/td5/td5_engine/inputs/page1")),
                "faults": {
                    "page1": _page("/images/faults.gif", _nav("Next page", "homepage/discovery/td5/td5_engine/faults/page2")),
                    "page2": _page("/images/faultsclear.gif", _nav("Back", "homepage/discovery/td5/td5_engine/page1")),
                },
                "inputs": {
                    "page1": _page("/images/inputs.jpg",
                                   _nav("Open abs", "homepage/discovery/td5/td5_engine/inputs/abs/page1")),
                    "abs": {
                        "page1": _page("/images/abs.jpg", _nav("Next page", "homepage/discovery/td5/td5_engine/inputs/abs/page2")),
                        "page2": _page("/images/abs2.jpg", _nav("Back", "homepage/discovery/td5/td5_engine/inputs/page1")),
                    },
                },
            },
        }}},
        # cruise lives under the motronic branch in the real data
        "homepage/discovery/motronic/hella_cc": None,  # placeholder; real nesting below
    },
}
# fix the cruise placeholder to a real nested page so td5_tree's CRUISE_PATH resolves
FIXTURE["pages"]["homepage"]["discovery"]["motronic"] = {"hella_cc": {
    "page1": _page("/images/cc.jpg",
                   _nav("Open faults", "homepage/discovery/motronic/hella_cc/faults/page1")),
    "faults": {"page1": _page("/images/ccfaults.gif")},
}}
del FIXTURE["pages"]["homepage/discovery/motronic/hella_cc"]


def _write_fixture(tmp_path):
    p = os.path.join(tmp_path, "emu.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(FIXTURE, fh)
    return p


def test_load_pages_flattens(tmp_path):
    pages = em.load_pages(_write_fixture(tmp_path))
    assert "homepage/discovery/td5/td5_engine/faults/page1" in pages
    assert pages["homepage/discovery/td5/td5_engine/faults/page1"]["image"] == "/images/faults.gif"


def test_open_labels_name_submenus(tmp_path):
    pages = em.load_pages(_write_fixture(tmp_path))
    tree = em.build_subtree(pages, em.TD5_ROOT)
    engine = next(c for c in tree["children"] if c["name"] == "td5_engine")
    assert engine["label"] == "td5 engine"           # from "Open td5 engine"
    faults = next(c for c in engine["children"] if c["name"] == "faults")
    assert faults["label"] == "faults"               # from "Open faults"
    # pagination is folded into the function's pages, not a child node
    assert {p["path"].rsplit("/", 1)[-1] for p in faults["pages"]} == {"page1", "page2"}
    assert faults["children"] == []


def test_iter_functions_finds_leaves(tmp_path):
    pages = em.load_pages(_write_fixture(tmp_path))
    tree = em.build_subtree(pages, em.TD5_ROOT)
    leaves = [trail[-1] for trail, _ in em.iter_functions(tree)]
    assert "faults" in leaves and "abs" in leaves      # abs is the paginated inputs leaf


def test_markdown_renders_counts(tmp_path):
    pages = em.load_pages(_write_fixture(tmp_path))
    md = em.to_markdown(em.build_subtree(pages, em.TD5_ROOT))
    assert "**faults**" in md and "page(s)" in md and "faults.gif" in md


# --- optional: validate against the real export when it is present locally ----------- #
_REAL = os.path.join(os.path.dirname(__file__), "..", "captures", "nanocom", "emulator.json")


@pytest.mark.skipif(not os.path.exists(_REAL), reason="real emulator export not staged")
def test_real_export_module_counts():
    tree = em.td5_tree(_REAL)
    counts = {c["name"]: em._count_pages(c) for c in tree["children"]}
    # the six D2 Td5 modules + the shared cruise module, with their known page counts
    assert counts["td5_engine"] == 23
    assert counts["slabs"] == 29
    assert counts["valeo_bcu"] == 54
    assert counts["d2_autogb"] == 16
    assert counts["d2_airbag"] == 7
    assert counts["ace"] == 9
    assert counts["hella_cc"] == 9
