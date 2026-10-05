"""``GET /version``: platform and pack versions and commits for Settings → Version."""
from __future__ import annotations

import subprocess

from openostler import version
from tests.fake_pack import FAKE_PACK


def test_env_commit_wins(monkeypatch):
    monkeypatch.setenv("OSTLER_COMMIT", "abc1234")
    monkeypatch.setenv("OSTLER_BUILT", "2026-10-05T22:00:00Z")
    info = version.build_info(FAKE_PACK)
    assert info["platform"]["commit"] == "abc1234"
    assert info["platform"]["name"] == "Ostler" and info["platform"]["version"]
    assert info["platform"]["source"] == version.PLATFORM_SOURCE
    assert info["built"] == "2026-10-05T22:00:00Z"
    assert info["started"].endswith("Z")


def test_build_commit_file_then_git(tmp_path, monkeypatch):
    monkeypatch.delenv("OSTLER_COMMIT", raising=False)
    (tmp_path / "pyproject.toml").write_text("")
    assert version._commit("OSTLER_COMMIT", [tmp_path]) is None
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    head = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    assert version._commit("OSTLER_COMMIT", [tmp_path]) == head
    (tmp_path / "BUILD_COMMIT").write_text("feedface\n")   # the Docker image's file wins
    assert version._commit("OSTLER_COMMIT", [tmp_path]) == "feedface"


def test_a_pack_without_an_entry_point_reports_only_its_name():
    info = version.build_info(FAKE_PACK)["pack"]
    assert info == {"id": FAKE_PACK.id, "name": FAKE_PACK.name, "version": None,
                    "commit": None, "source": None}


def test_build_meta_reads_loose_packed_and_detached_heads(tmp_path):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "build_meta", Path(__file__).resolve().parents[1] / "tools" / "build_meta.py")
    bm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bm)
    git = tmp_path / ".git"
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\n")
    (git / "packed-refs").write_text("# pack-refs\naaaa111 refs/heads/main\n")
    assert bm.head_commit(git) == "aaaa111"
    (git / "refs" / "heads" / "main").write_text("bbbb222\n")
    assert bm.head_commit(git) == "bbbb222"
    (git / "HEAD").write_text("cccc333\n")
    assert bm.head_commit(git) == "cccc333"
    assert bm.head_commit(tmp_path / "missing") == ""
    bm.main(str(tmp_path))
    assert (tmp_path / "BUILD_COMMIT").read_text() == "cccc333\n"
    assert (tmp_path / "BUILD_TIME").read_text().strip().endswith("Z")
