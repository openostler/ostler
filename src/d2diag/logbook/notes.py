"""Per-session notes (ADR-0010; spec 2026-10-05-replay-notes-capture §2). Core: never imports web.

Contract:
* ``NoteLog(session_dir)``: ``list() -> [note]`` (sorted by t, revisions resolved),
  ``add(t, text="", tags=(), kind="note", source="retro", t_end=None, capture=None) -> note``,
  ``edit(nid, **fields) -> note`` (KeyError if unknown), ``delete(nid)``.
  Storage ``notes.jsonl``: append-only revision log; the last line per id wins;
  ``{"id", "deleted": true}`` removes. Ids are 8 hex chars.
* ``read_notes(session_dir) -> [note]`` for exports.
"""
