"""SQLite session index (spec 2026-10-06-logs-at-scale §3). Core: never imports web.

Contract:
* ``SessionIndex(db_path, store)``: ``sync(sid)``, ``remove(sid)``, ``rebuild()``,
  ``page(limit=50, before=None, q=None, frm=None, to=None, module=None, has_notes=False,
  min_km=None, public=False) -> {"sessions": [meta], "next": cursor | None}``,
  ``histogram(group="month", year=None, public=False) -> {"group", "buckets": [{key, count, km}]}``.
  Keyset order: start_ms DESC, id DESC; cursor "<start_ms>:<id>". FTS5 when available, else LIKE.
  WAL + synchronous=NORMAL; rebuilt from meta.json files when missing or schema changes.
"""
