# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The installed vehicle pack's K-line overrides (spec K-line profiles §1, migration step 2):
every module's ``ModuleSpec.kline`` validates against ``schemas/kline-profile.schema.json``
and resolves to a valid profile at pack load. Holds for a pack with or without overrides."""
import json
from pathlib import Path

import pytest

from openostler.kline.profiles import KLineProfile
from openostler.pack import active_pack

pytestmark = pytest.mark.needs_pack

SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "kline-profile.schema.json"


def _manifest_form(overrides) -> dict:
    """The override mapping as the manifest's ``transport`` block writes it (hex strings)."""
    out = {}
    for k, v in overrides.items():
        if isinstance(v, (bytes, bytearray)):
            v = bytes(v).hex(" ").upper()
        elif k == "timing":
            v = dict(v)
        out[k] = v
    return out


def test_pack_module_overrides_match_the_schema():
    jsonschema = pytest.importorskip("jsonschema")
    v = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    for m in active_pack().modules:
        assert list(v.iter_errors(_manifest_form(m.kline))) == [], m.id


def test_pack_module_profiles_resolve():
    for m in active_pack().modules:
        p = m.kline_profile()
        if m.init == "none" and "base" not in m.kline:
            assert p is None, m.id
            continue
        assert isinstance(p, KLineProfile) and p.name == m.id
        if m.address is not None:
            assert p.init_address == p.target == m.address
