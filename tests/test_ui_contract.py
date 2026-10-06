# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The HTTP contract between the Python server and the React UI (ADR-0004).

Real responses from a mock ``DiagServer`` are compared, by *shape*, against the JSON
fixtures committed in ``ui/src/api/fixtures/``. The UI's Vitest suite parses the same
fixtures with its Zod schemas. A server change that alters a response shape therefore
fails here until the fixtures are regenerated, and then fails in the UI until the
schemas follow:

    UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")


import json
import os
import threading
import time
import urllib.request
from pathlib import Path


from openostler.community import Community
from openostler.menus import MENUS
from tests.fake_sources import FakeSlabsSource, FakeTd5Source, fake_fault_report
from openostler.web.docs import DocLibrary
from openostler.web.server import DiagServer
from openostler.web.sniffer import SnifferFeed

FIXTURES = Path(__file__).resolve().parents[1] / "ui" / "src" / "api" / "fixtures"
UPDATE = os.environ.get("UPDATE_UI_FIXTURES") == "1"


def _shape(obj):
    """A value's structure: dicts by key, lists by their first element, scalars by type."""
    if isinstance(obj, dict):
        return {k: _shape(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_shape(obj[0])] if obj else []
    if obj is None:
        return None
    if isinstance(obj, bool):
        return "boolean"
    if isinstance(obj, (int, float)):
        return "number"
    return "string"


def _compatible(want, got, path="$"):
    """Shape equality where null and empty lists act as wildcards (values vary by poll)."""
    if want is None or got is None or want == [] or got == []:
        return []
    if isinstance(want, dict) and isinstance(got, dict):
        errs = []
        for k in sorted(set(want) | set(got)):
            if k not in got:
                errs.append(f"{path}.{k}: missing from the server response")
            elif k not in want:
                errs.append(f"{path}.{k}: new in the server response (regenerate fixtures)")
            else:
                errs += _compatible(want[k], got[k], f"{path}.{k}")
        return errs
    if isinstance(want, list) and isinstance(got, list):
        return _compatible(want[0], got[0], f"{path}[]")
    return [] if want == got else [f"{path}: fixture {want!r} vs server {got!r}"]


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("contract")
    doc = tmp / "notes.md"
    doc.write_text("# Notes\n\nA *test* document.\n", encoding="utf-8")
    sniffer = SnifferFeed(lambda: iter([]), source="test:contract")
    sniffer.store.ingest_line("[1] 81 13 f7 81 0c")
    sniffer.store.ingest_line("[2] 02 21 09 2c 04 61 09 02 fa 6a")
    srv = DiagServer(
        host="127.0.0.1", port=0, poll_interval=0.05, stream_interval=0.05,
        source={"td5": FakeTd5Source(), "slabs": FakeSlabsSource()},
        fault_scan=fake_fault_report, active="td5", menus=MENUS, docs=DocLibrary().add_file(doc),
        sniffer=sniffer, captures_path=str(tmp / "captures.jsonl"), csv_dir=str(tmp),
        # offline poster: nothing leaves the test; the opt-in is queued, not sent
        community=Community(config_path=str(tmp / "community.json"),
                            poster=lambda url, body: {"ok": False, "error": "offline"}),
    )
    srv.start_polling()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    deadline = time.time() + 5
    while time.time() < deadline:
        snap = json.loads(urllib.request.urlopen(url + "/snapshot", timeout=2).read())
        if snap.get("status") == "connected" and snap.get("signals"):
            break
        time.sleep(0.05)
    yield url
    srv.shutdown()
    srv.server_close()
    srv.stop()


def _get(base, path):
    return json.loads(urllib.request.urlopen(base + path, timeout=5).read())


def _get_error(base, path):
    """An error reply's body (the JSON envelope)."""
    req = urllib.request.Request(base + path, headers={"Accept": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as err:
        return json.loads(err.read())
    raise AssertionError(f"{path} did not fail")


def _not_recording(_base):
    """``split_session`` with nothing recording: a server that never polled (409)."""
    srv = DiagServer(host="127.0.0.1", port=0, source=FakeTd5Source(), csv_dir=_tmp_dir())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        return _post(f"http://127.0.0.1:{srv.server_address[1]}", "/command",
                     {"action": "split_session"})
    finally:
        srv.shutdown()
        srv.server_close()
        srv.stop()


def _tmp_dir() -> str:
    import tempfile
    return tempfile.mkdtemp(prefix="ostler-contract-")


def _kline_snapshot(_base):
    """A snapshot with a K-line ``link``: a generic link source on a fake KWP2000 ECU."""
    from openostler.kline.profiles import BUILTIN
    from openostler.web.kline_source import KLineLinkSource
    from tests.fakes import FakeClock, FakeKLineEcu, kwp_fast_reply

    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0xE9, 0x8F))
    clock = FakeClock()
    src = KLineLinkSource("auto", name="td5", profile=BUILTIN["kwp2000_fast"], origin="pack",
                          transport_factory=lambda port, profile: ecu, clock=clock,
                          sleep=clock.sleep, wall=lambda: 1_790_000_000.0)
    srv = DiagServer(host="127.0.0.1", port=0, source={"td5": src}, csv_dir=_tmp_dir(),
                     record_sessions=False, geocoder=None)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        srv.poll_once()
        return _get(f"http://127.0.0.1:{srv.server_address[1]}", "/snapshot")
    finally:
        srv.shutdown()
        srv.server_close()


def _node_snapshot(_base):
    """A snapshot from NodeSource: a simulated node replays the firmware's SLABS fixture
    through the fake broker (NodeSource spec §13, P1)."""
    from openostler.metrics import is_known
    from openostler.pack import active_pack
    from openostler.web.node_source import NodeFeed, node_sources, store_lookup
    from tests.fake_broker import FakeBroker
    from tests.fake_node import VID, FakeNode, case, load

    pack = active_pack()
    msgs = [m for m in load("slabs-vectors.jsonl") if "/vss/" in m["topic"]]
    with FakeBroker() as broker:
        node = FakeNode(broker.host, broker.port).connect()
        for m in msgs:
            node.send(m)  # stored before the Brain subscribes
        node.send(case("awake"))  # QoS 1: its PUBACK means the broker has stored them all
        feed = NodeFeed(VID, broker.host, broker.port, client_id="contract-nodesource",
                        pack_id=pack.id, lookup=store_lookup(), canonical=pack.canonical,
                        is_known=is_known, log=lambda _m: None)
        feed.start()
        srv = DiagServer(host="127.0.0.1", port=0, source=node_sources(feed, pack.module_ids()),
                         active="slabs", csv_dir=_tmp_dir(), record_sessions=False, geocoder=None)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            deadline = time.time() + 5
            while time.time() < deadline and len(feed.table.view("slabs", 0, 0)["signals"]) < 18:
                time.sleep(0.02)
            for m in msgs[-6:]:
                node.send(m)  # a few live values
            time.sleep(0.2)
            srv.poll_once()
            return _get(f"http://127.0.0.1:{srv.server_address[1]}", "/snapshot")
        finally:
            srv.shutdown()
            srv.server_close()
            feed.stop()
            node.stop()


def _queued(base):
    """A contribution while the endpoint is offline: 202 ``{ok: true, queued: true}``."""
    _post(base, "/community/consent", {"consent": True})
    try:
        return _post(base, "/community/contribute", {"module": "td5", "lid": "09",
                                                      "offset": 0, "name": "rpm"})
    finally:
        _post(base, "/community/consent", {"consent": False})


def _post(base, path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=50).read())
    except urllib.error.HTTPError as err:   # an error answers the JSON envelope
        return json.loads(err.read())


# name → how to obtain the response. Order matters only for CSV start before stop.
CASES = {
    "snapshot": lambda b: _get(b, "/snapshot"),
    "snapshot-kline": _kline_snapshot,
    "snapshot-node": _node_snapshot,
    "pack": lambda b: _get(b, "/pack"),
    "version": lambda b: _get(b, "/version"),
    "fields-td5": lambda b: _get(b, "/fields?module=td5"),
    "fields-slabs": lambda b: _get(b, "/fields?module=slabs"),
    "faults-airbag": lambda b: _get(b, "/faults?module=airbag"),
    "map": lambda b: _get(b, "/map?module=td5"),
    "catalog-td5": lambda b: _get(b, "/catalog?module=td5"),
    "catalog-bcu": lambda b: _get(b, "/catalog?module=bcu"),
    "catalog-modules": lambda b: _get(b, "/catalog"),
    "sessions": lambda b: _get(b, "/sessions"),
    "session-histogram": lambda b: _get(b, "/sessions/histogram?group=month"),
    "session-meta": lambda b: _get(b, "/sessions/20261005T090000Z"),
    "session-data": lambda b: _get(b, "/sessions/20261005T090000Z/data?ch=rpm,GPS_Speed&max=50"),
    "session-events": lambda b: _get(b, "/sessions/20261005T090000Z/events"),
    "notes": lambda b: _get(b, "/sessions/20261005T090000Z/notes"),
    "sniff": lambda b: _get(b, "/sniff?module=td5"),
    "docs": lambda b: _get(b, "/docs"),
    "community": lambda b: _get(b, "/community"),
    "community-consent": lambda b: _post(b, "/community/consent", {"consent": False}),
    "community-queued": _queued,
    "command-ok": lambda b: _post(b, "/command", {"action": "set_fault_watch",
                                                  "params": {"on": False}}),
    "command-error": lambda b: _post(b, "/command", {"action": "no_such_command"}),
    "command-not-recording": _not_recording,
    "error-not-found": lambda b: _get_error(b, "/no/such/route"),
    "csv-start": lambda b: _post(b, "/command", {"action": "start_csv"}),
    "csv-stop": lambda b: _post(b, "/command", {"action": "stop_csv"}),
    "read-all-faults": lambda b: _post(b, "/command", {"action": "read_all_faults"}),
    "automap": lambda b: _post(b, "/automap", {
        "samples": [{"text": "762", "raws": {"09": "02fa"}},
                    {"text": "1500", "raws": {"09": "05dc"}},
                    {"text": "2200", "raws": {"09": "0898"}}],
        "candidate_lids": ["09"], "name": "rpm", "unit": "rpm"}),
    "capture": lambda b: _post(b, "/capture", {"module": "td5", "lid": "09",
                                               "raw": "02 fa", "text": "762 rpm"}),
    # after "capture": the merged list holds at least that row
    "captures": lambda b: _get(b, "/captures?module=td5"),
}


def base_tmp(got):
    """The pytest tmp dir a response may embed (CSV path) — scrubbed from fixtures."""
    path = got.get("path") if isinstance(got, dict) else None
    return str(Path(path).parent) if path else None


@pytest.mark.parametrize("name", list(CASES))
def test_response_matches_ui_fixture(base, name):
    got = CASES[name](base)
    path = FIXTURES / f"{name}.json"
    if UPDATE or not path.exists():
        if not UPDATE:
            pytest.fail(f"missing fixture {path.name}: run UPDATE_UI_FIXTURES=1 pytest {__file__}")
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(got, indent=2, ensure_ascii=False)
        tmp = str(Path(base_tmp(got) or "/nonexistent"))
        path.write_text(text.replace(tmp, "/tmp/d2diag-test") + "\n", encoding="utf-8")
        return
    want = json.loads(path.read_text(encoding="utf-8"))
    errs = _compatible(_shape(want), _shape(got))
    assert not errs, f"{name}: the server no longer matches the UI contract:\n  " + \
        "\n  ".join(errs) + "\nRegenerate: UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py"


def test_shape_comparison_catches_drift():
    assert _compatible(_shape({"a": 1, "b": [1]}), _shape({"a": 2.5, "b": []})) == []
    assert _compatible(_shape({"a": 1}), _shape({"a": "x"}))
    assert _compatible(_shape({"a": 1}), _shape({"a": 1, "new": True}))
    assert _compatible(_shape({"a": None}), _shape({"a": "anything"})) == []
