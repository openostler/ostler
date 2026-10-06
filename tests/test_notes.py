# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Per-session notes and capture labels (ADR-0010; replay-notes-capture spec §2)."""

import pytest

import json

from openostler.logbook.notes import NoteLog, read_notes
from openostler.logbook.recorder import NotRecording, SessionRecorder
from openostler.logbook.store import SessionStore

pytestmark = pytest.mark.fake_pack

T0 = 1791277200.0
DEMO = "20261005T090000Z"
NOTE_KEYS = {"id", "t", "t_end", "text", "tags", "kind", "source", "created", "edited",
             "capture"}


def test_add_edit_delete_revisions(tmp_path):
    log = NoteLog(str(tmp_path), clock=lambda: T0)
    a = log.add(5000, "Rough idle", tags=["issue", "issue", " noise "])
    b = log.add(1000, kind="mark", source="live")
    assert set(a) == NOTE_KEYS and len(a["id"]) == 8 and int(a["id"], 16) >= 0
    assert a["tags"] == ["issue", "noise"] and a["source"] == "retro" and a["t_end"] is None
    assert a["created"] == "2026-10-06T09:00:00.000Z" and a["edited"] is None
    assert [n["id"] for n in log.list()] == [b["id"], a["id"]]  # sorted by t
    e = log.edit(b["id"], text="Clunk over the cattle grid", tags=["noise"], t_end=2500)
    assert e["text"] == "Clunk over the cattle grid" and e["t_end"] == 2500 and e["edited"]
    assert e["kind"] == "mark" and e["created"] == b["created"]
    log.delete(a["id"])
    notes = read_notes(str(tmp_path))
    assert [n["id"] for n in notes] == [b["id"]] and notes[0]["text"].startswith("Clunk")
    lines = (tmp_path / "notes.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4 and json.loads(lines[-1]) == {"id": a["id"], "deleted": True}
    with pytest.raises(KeyError):
        log.edit("deadbeef", text="x")
    with pytest.raises(KeyError):
        log.delete(a["id"])


def test_validation(tmp_path):
    log = NoteLog(str(tmp_path))
    for kw in ({"t": -1}, {"t": "5"}, {"t": 10, "t_end": 5}, {"t": 0, "kind": "bogus"},
               {"t": 0, "source": "x"}):
        with pytest.raises(ValueError):
            log.add(**kw)
    n = log.add(0)
    with pytest.raises(ValueError):
        log.edit(n["id"], kind="capture")  # not editable
    with pytest.raises(ValueError):
        log.edit(n["id"], t_end=-3)


def test_capture_note_and_truncated_line(tmp_path):
    log = NoteLog(str(tmp_path))
    n = log.add(100, "rpm", kind="capture",
                capture={"module": "td5", "lid": "09", "raw": "02 fa", "value": 762})
    assert n["capture"] == {"module": "td5", "lid": "09", "raw": "02 fa", "value": "762"}
    with open(tmp_path / "notes.jsonl", "a", encoding="utf-8") as fh:
        fh.write('{"id": "0000000')  # power cut mid-line
    assert [x["id"] for x in log.list()] == [n["id"]]


def _session(tmp_path):
    c = {"t": 0.0}
    r = SessionRecorder(str(tmp_path / "sessions"), clock=lambda: T0 + c["t"],
                        mono=lambda: c["t"], min_free_bytes=0)
    r.feed({"conn": "connected", "module": "motor", "mode": "live",
            "signals": {"rpm": {"v": 800}}, "faults": []}, None)
    return c, r


@pytest.mark.needs_pack
def test_store_notes_crud_and_refusals(tmp_path):
    c, r = _session(tmp_path)
    sid = r.status()["session"]
    r.close()
    store = SessionStore(str(tmp_path / "sessions"))
    n = store.add_note(sid, 1500, "after the junction", tags=["issue"], t_end=3000)
    assert store.notes(sid) == [n]
    e = store.edit_note(sid, n["id"], text="changed")
    assert store.notes(sid)[0]["text"] == "changed" and e["edited"]
    with pytest.raises(PermissionError):
        store.add_note(sid, 0, "x", public=True)
    with pytest.raises(PermissionError):
        store.edit_note(sid, n["id"], public=True, text="y")
    with pytest.raises(PermissionError):
        store.delete_note(sid, n["id"], public=True)
    with pytest.raises(KeyError):
        store.notes(sid, public=True)  # real sessions are hidden in public mode
    for call in (lambda: store.add_note(DEMO, 0, "x"),
                 lambda: store.edit_note(DEMO, "a1b2c3d4", text="x"),
                 lambda: store.delete_note(DEMO, "a1b2c3d4")):
        with pytest.raises(PermissionError):
            call()
    assert len(store.notes(DEMO, public=True)) == 3
    with pytest.raises(KeyError):
        store.add_note("20991231T000000Z", 0, "x")
    store.delete_note(sid, n["id"])
    assert store.notes(sid) == []


def test_live_note_needs_a_recording_session_and_keeps_it(tmp_path):
    c = {"t": 0.0}
    r = SessionRecorder(str(tmp_path / "sessions"), clock=lambda: T0 + c["t"],
                        mono=lambda: c["t"], min_free_bytes=0)
    assert r.status() is None
    with pytest.raises(NotRecording):  # a live note never starts a session (ADR-0011)
        r.note(kind="mark")
    assert r.status() is None
    sid = r.start()
    c["t"] = 2.0
    sid1, note = r.note(kind="mark")
    assert sid1 == sid and note["source"] == "live" and note["t"] == 2000
    c["t"] = 4.5
    sid2, note2 = r.note("noise", tags=["noise"], kind="note")
    assert sid2 == sid and note2["t"] == 4500
    r.close()  # no data rows, but the notes keep the session
    store = SessionStore(str(tmp_path / "sessions"), demo_root=None)
    assert [n["id"] for n in store.notes(sid)] == [note["id"], note2["id"]]
    assert store.meta(sid)["note_count"] == 2
    ev = store.events(sid)
    assert ev[0]["type"] == "state"


def test_live_note_refused_while_paused(tmp_path):
    c = {"t": 0.0}
    r = SessionRecorder(str(tmp_path / "sessions"), clock=lambda: T0 + c["t"],
                        mono=lambda: c["t"], min_free_bytes=0)
    r.feed({"conn": "connected", "signals": {"rpm": {"v": 800}}}, None)
    c["t"] = 1.0
    r.feed({"conn": "lost", "signals": {}}, None)
    assert r.status()["state"] == "paused"
    with pytest.raises(NotRecording) as exc:
        r.note("x")
    assert "connect to the car" in str(exc.value) and isinstance(exc.value, RuntimeError)
    with pytest.raises(NotRecording):
        r.split()
    c["t"] = 2.0
    r.feed({"conn": "connected", "signals": {"rpm": {"v": 810}}}, None)
    assert r.status()["state"] == "recording"
    assert r.note("ok")[0] == r.status()["session"]
    r.close()


@pytest.mark.needs_pack
def test_captures_merge_notes_and_jsonl(tmp_path):
    c, r = _session(tmp_path)
    c["t"] = 1.0
    sid, _ = r.note("rpm", kind="capture",
                    capture={"module": "td5", "lid": "09", "raw": "02 fa", "value": "762 rpm"})
    r.note("other", kind="capture", capture={"module": "slabs", "lid": "54", "raw": "95",
                                             "value": "149"})
    r.note("just a note", kind="note")
    r.close()
    jl = tmp_path / "labeled_captures.jsonl"
    jl.write_text("\n".join([
        json.dumps({"t": "2026-08-19 10:00:00", "module": "td5", "lid": "1A",
                    "raw": "0b b8", "text": "30.0"}),
        "not json",
        json.dumps({"module": "td5"}),  # no lid: skipped
    ]) + "\n", encoding="utf-8")
    store = SessionStore(str(tmp_path / "sessions"))
    caps = store.captures(module="motor", labeled_path=str(jl))
    assert caps == [
        {"module": "td5", "lid": "09", "raw": "02 fa", "value": "762 rpm", "t": 1000,
         "session": sid},
        {"module": "td5", "lid": "1A", "raw": "0b b8", "value": "30.0", "t": None,
         "session": None},
    ]
    assert len(store.captures()) == 2  # no jsonl path: notes only, every module
    assert len(store.captures(labeled_path=str(tmp_path / "missing.jsonl"))) == 2
