# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""tests/e2e_server.py — the test/dev-only dashboard on simulated sources (ADR-0011)."""

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")

import ast
import json
import threading
import urllib.request
from pathlib import Path

from tests import e2e_server

REPO = Path(__file__).resolve().parents[1]


def _build(tmp_path, monkeypatch, *argv):
    """Run ``main()`` like the command line does, but capture the server instead of serving."""
    from openostler.web.server import DiagServer

    captured = {}
    monkeypatch.setattr(DiagServer, "serve", lambda self: captured.update(srv=self))
    monkeypatch.setattr(e2e_server.signal, "signal", lambda *a: None)
    assert e2e_server.main(["--port", "0", "--sessions-dir", str(tmp_path / "sessions"),
                            "--replay", "off", *argv]) == 0
    return captured["srv"]


def test_e2e_server_builds_a_simulated_car_with_a_seeded_editable_session(tmp_path,
                                                                           monkeypatch):
    srv = _build(tmp_path, monkeypatch)
    try:
        assert set(srv._modules) == {"td5", "slabs", "airbag", "ace", "autobox", "bcu"}
        assert all(getattr(s, "simulated", False) for s in srv._modules.values())
        assert srv._enricher is None and srv.gps is not None
        snap = srv.poll_once()
        assert snap["status"] == "connected" and "mode" not in snap
        assert srv._read_all_faults()["ok"]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        body = json.loads(urllib.request.urlopen(base + "/sessions", timeout=10).read())
        real = [m for m in body["sessions"] if not m["synthetic"]]
        demos = {m.get("name") for m in body["sessions"] if m["synthetic"]}
        assert len(real) == 1 and not real[0]["recording"]       # the seeded session
        assert {"Demo log 1", "Demo log 2"} <= demos
        req = urllib.request.Request(base + f"/sessions/{real[0]['id']}", method="PATCH",
                                     data=json.dumps({"name": "Edited"}).encode(),
                                     headers={"Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(req, timeout=10).read())
        assert out["ok"] and out["meta"]["name"] == "Edited"
        srv.shutdown()
    finally:
        srv.stop()
        srv.server_close()


def test_e2e_server_can_start_disconnected(tmp_path, monkeypatch):
    srv = _build(tmp_path, monkeypatch, "--start", "disconnected", "--no-seed", "--no-gps")
    try:
        assert srv.poll_once()["conn"] == "disconnected" and srv.gps is None
    finally:
        srv.stop()
        srv.server_close()


def test_no_product_code_imports_the_fakes():
    for path in list((REPO / "src").rglob("*.py")) + list((REPO / "tools").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("tests"), path
            elif isinstance(node, ast.Import):
                assert not any(a.name.startswith("tests") for a in node.names), path
