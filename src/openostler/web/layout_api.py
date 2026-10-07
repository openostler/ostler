# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The server side of stored UI layouts (drive-modes spec §8.1 R1/R7, §8.3; DM2).

A mixin for :class:`~openostler.web.server.DiagServer` over
:class:`~openostler.layout_store.LayoutStore` (``<state dir>/settings.sqlite``):

* ``GET /ui/layouts/{vid}/{profile}/{class}[?kind=]``: every stored or pack layout at that
  key, resolved (user → car → pack), plus held changes and the Before reset snapshot.
* ``GET|PUT|DELETE /ui/layouts/{vid}/{profile}/{class}/{kind}/{id}``: one layout resolved
  with its ``source`` (``generated``: the shell's own preset, ``layout: null``) and an
  ``ETag``; a ``PUT`` validated by :mod:`openostler.layouts` (``If-Match`` optional); a
  ``DELETE`` reverts to what lies beneath (the base), keeping a Before reset snapshot.
* ``POST …/{class}/reset {kind?}`` and ``POST …/{class}/undo-reset`` (§7.8).
* ``GET|PUT /ui/drive-mode/{vid}/{profile}/{display}/{class}``: the selected Drive mode of one
  display (switching is allowed in every driving state, R1).

``vid`` may be ``current`` (this server's local vehicle). ``profile`` is ``car`` (the head
unit's kiosk session) or a user id; until accounts land (accounts spec P1) it is not
authenticated.

**Park to edit (R1, R7).** Every layout write (``PUT``, ``DELETE``, reset, undo reset) names
the requesting display's layout class in the ``Ostler-Layout-Class`` request header. While
the driving state is not Parked (or Idling) — and it is ``unknown`` until U2 — a write from
a driver-facing class (the head units and the phone; a missing or unknown header counts as
driver-facing) is refused with 409 ``park_to_edit`` and the ``driving_state``. A write from
tablet or desktop is allowed (spec §7.1: they are not driver-facing for editing); when its
*target* class is driver-facing it is held (202, ``held: true``) and applied at the next
Parked, so nothing changes under the driver (R7). Selecting a Drive mode is never gated,
except that reordering a stored rotation is an edit.
"""
from __future__ import annotations

import json
import os
from urllib.parse import unquote

from ..layout_store import (
    CAR,
    DISPLAY_RE,
    LayoutRejected,
    LayoutStore,
    check_document,
    check_key,
    check_selection,
    driver_facing,
    layout_classes,
)
from ..layouts import KINDS, limits, validate_layout

LAYOUT_CLASS_HEADER = "Ostler-Layout-Class"
SETTINGS_DB = "settings.sqlite"
EDIT_STATES = frozenset({"parked", "idling"})
# Kinds a PUT may store. Rail, strip and Home layouts wait for their guardrail check
# (§8.2 step 7: More, the safety items), which lands with their editors in DM3.
WRITABLE_KINDS = frozenset({"drive_mode"})
PARK_TO_EDIT = "Park to edit: layouts change only when the car is parked"


class LayoutRefusal(Exception):
    """A refusal that carries a whole ``ok: false`` reply (extra fields included)."""

    def __init__(self, reply: dict) -> None:
        super().__init__(reply.get("error"))
        self.reply = reply


def _fail(error: str, code: str, **extra) -> dict:
    return {"ok": False, "error": error, "code": code, **extra}


class LayoutApiMixin:
    """Mixed into DiagServer; uses its ``_state_dir``, ``_sessions_dir``, ``_public`` and
    ``_conn_log_early``."""

    _layouts: "LayoutStore | None" = None
    _pack_docs: "list | None" = None
    driving_state_fn = None

    # ---- wiring ---------------------------------------------------------- #
    def _layout_state_dir(self) -> str:
        from ..logbook.vehicle import state_dir_for

        return self._state_dir or state_dir_for(self._sessions_dir)

    def layout_store(self) -> LayoutStore:
        if self._layouts is None:
            self._layouts = LayoutStore(os.path.join(self._layout_state_dir(), SETTINGS_DB))
        return self._layouts

    def driving_state(self) -> str:
        """Parked, idling, moving or unknown. Unknown until U2 computes it."""
        fn = self.driving_state_fn
        try:
            state = fn() if callable(fn) else None
        except Exception:  # noqa: BLE001 — an unreadable state is unknown, never Parked
            state = None
        return state if state in ("parked", "idling", "moving") else "unknown"

    def _vid(self, vid: str) -> str:
        from ..logbook.vehicle import VID_RE, local_vid

        if vid == "current":
            return local_vid(self._layout_state_dir())
        if not VID_RE.match(vid or ""):
            raise LayoutRefusal(_fail(f"bad vehicle id: {vid!r}", "bad_request"))
        return vid

    def _pack_layouts(self) -> list:
        """The pack's own layouts (tier 2): ``layouts`` in its UI manifest, valid ones only."""
        if self._pack_docs is None:
            docs = []
            try:
                from ..pack import active_pack

                raw = (active_pack().layout or {}).get("layouts") or []
            except Exception:  # noqa: BLE001 — no pack: no tier 2
                raw = []
            for doc in raw if isinstance(raw, list) else []:
                if validate_layout(doc).ok:
                    docs.append(doc)
                else:
                    self._conn_log_early(f"layouts: the pack's {doc.get('id') if isinstance(doc, dict) else '?'} "
                                         "fails validation and is ignored")
            self._pack_docs = docs
        return self._pack_docs

    # ---- the gate -------------------------------------------------------- #
    def _layout_gate(self, requester: "str | None", target_cls: str) -> str:
        """``apply`` or ``hold`` a write; raise :class:`LayoutRefusal` (409) for Park to edit."""
        state = self.driving_state()
        if state in EDIT_STATES:
            self.layout_store().apply_held()
            return "apply"
        requester = requester if requester in layout_classes() else None
        if driver_facing(requester):
            raise LayoutRefusal(_fail(PARK_TO_EDIT, "park_to_edit", driving_state=state,
                                      layout_class=requester))
        return "hold" if driver_facing(target_cls) else "apply"

    def _tick(self) -> None:
        """Apply held changes once the car is Parked (checked on every layouts request)."""
        if self.driving_state() in EDIT_STATES:
            self.layout_store().apply_held()

    # ---- routes ---------------------------------------------------------- #
    def ui_route(self, method: str, path: str, *, query: dict, header, body=None) -> "tuple[dict, dict]":
        """Dispatch one ``/ui/…`` request → (reply, extra headers). ``header(name)`` reads a
        request header; ``body()`` reads the raw body (PUT/POST)."""
        parts = [unquote(p) for p in path.split("/") if p][1:]  # drop "ui"
        try:
            if not parts or parts[0] not in ("layouts", "drive-mode"):
                return _fail("not found", "not_found"), {}
            if method != "GET" and self._public:
                return _fail("not available in public mode", "public_mode"), {}
            if parts[0] == "drive-mode":
                if len(parts) != 5:
                    return _fail("not found", "not_found"), {}
                _, vid, profile, display, cls = parts
                if method == "GET":
                    return self._selection_get(vid, profile, display, cls), {}
                if method == "PUT":
                    return self._selection_put(vid, profile, display, cls, body, header), {}
                return _fail("not found", "not_found"), {}
            rest = parts[1:]
            if len(rest) == 3 and method == "GET":
                return self._layouts_list(*rest, kind=query.get("kind")), {}
            if len(rest) == 4 and method == "POST" and rest[3] == "reset":
                return self._layouts_reset(*rest[:3], body=body, header=header), {}
            if len(rest) == 4 and method == "POST" and rest[3] == "undo-reset":
                return self._layouts_undo(*rest[:3], body=body, header=header), {}
            if len(rest) == 5:
                if method == "GET":
                    reply = self._layout_get(*rest)
                    return reply, {"ETag": reply["etag"]}
                if method == "PUT":
                    reply = self._layout_put(*rest, body=body, header=header)
                    return reply, ({"ETag": reply["etag"]} if reply.get("etag") else {})
                if method == "DELETE":
                    body(4096)  # none expected; read any before a refusal
                    return self._layout_delete(*rest, header=header), {}
            return _fail("not found", "not_found"), {}
        except LayoutRefusal as exc:
            return exc.reply, {}
        except ValueError as exc:
            return _fail(str(exc), "bad_request"), {}

    def _key(self, vid: str, profile: str, cls: str, kind=None, lid=None) -> str:
        check_key(profile, cls, kind, lid)
        return self._vid(vid)

    def _layouts_list(self, vid: str, profile: str, cls: str, kind: "str | None") -> dict:
        vid = self._key(vid, profile, cls, kind or None)
        self._tick()
        store = self.layout_store()
        return {"vid": vid, "profile": profile, "class": cls, "driving_state": self.driving_state(),
                "layouts": store.list(vid, profile, cls, kind or None, self._pack_layouts()),
                "held": store.held(vid, profile, cls),
                "snapshot": store.snapshot(vid, profile, cls)}

    def _layout_get(self, vid: str, profile: str, cls: str, kind: str, lid: str) -> dict:
        vid = self._key(vid, profile, cls, kind, lid)
        self._tick()
        res = self.layout_store().resolve(vid, profile, cls, kind, lid, self._pack_layouts())
        return {"vid": vid, "class": cls, "kind": kind, "id": lid, **res,
                "requested_profile": profile}

    def _layout_put(self, vid: str, profile: str, cls: str, kind: str, lid: str, *, body,
                    header) -> dict:
        vid = self._key(vid, profile, cls, kind, lid)
        if kind not in WRITABLE_KINDS:
            raise LayoutRefusal(_fail(
                f"{kind} layouts can be stored once their guardrail check is in (DM3)",
                "kind_not_writable"))
        raw = body(limits()["max_bytes"])  # read before any refusal: never reset the client
        action = self._layout_gate(header(LAYOUT_CLASS_HEADER), cls)
        try:
            doc = json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, ValueError):
            raise LayoutRefusal(_fail("body must be an ostler.layout/1 JSON document",
                                      "bad_request")) from None
        try:
            report = check_document(doc, cls, kind, lid, raw_size=len(raw))
        except LayoutRejected as exc:
            raise LayoutRefusal(_fail(f"The layout was refused: {exc.message}", exc.rule,
                                      errors=exc.errors, warnings=exc.warnings)) from None
        store = self.layout_store()
        match = header("If-Match")
        if match and match.strip() != "*":
            now = store.resolve(vid, profile, cls, kind, lid, self._pack_layouts())["etag"]
            if match.strip() != now:
                raise LayoutRefusal(_fail("The layout changed since it was read; reload it",
                                          "etag_mismatch", etag=now))
        warnings = [{"rule": i.rule, "message": i.message} for i in report.warnings]
        if action == "hold":
            seq = store.hold(vid, profile, cls, "put", kind, lid, doc)
            return {"ok": True, "queued": True, "held": True, "seq": seq, "vid": vid,
                    "profile": profile, "class": cls, "kind": kind, "id": lid,
                    "warnings": warnings,
                    "message": "Applies when the car is parked"}
        res = store.put(vid, profile, cls, doc, raw_size=len(raw))
        return {"ok": True, "vid": vid, "class": cls, "kind": kind, "id": lid, **res}

    def _layout_delete(self, vid: str, profile: str, cls: str, kind: str, lid: str, *,
                       header) -> dict:
        vid = self._key(vid, profile, cls, kind, lid)
        action = self._layout_gate(header(LAYOUT_CLASS_HEADER), cls)
        store = self.layout_store()
        if action == "hold":
            seq = store.hold(vid, profile, cls, "delete", kind, lid)
            return {"ok": True, "queued": True, "held": True, "seq": seq,
                    "message": "Applies when the car is parked"}
        deleted = store.delete(vid, profile, cls, kind, lid)
        res = store.resolve(vid, profile, cls, kind, lid, self._pack_layouts())
        return {"ok": True, "deleted": deleted, "vid": vid, "class": cls, "kind": kind,
                "id": lid, "resolved": res, "snapshot": store.snapshot(vid, profile, cls)}

    def _layouts_reset(self, vid: str, profile: str, cls: str, *, body, header) -> dict:
        raw = body(4096)
        try:
            args = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError):
            raise LayoutRefusal(_fail("body must be JSON {kind?}", "bad_request")) from None
        if not isinstance(args, dict):
            raise LayoutRefusal(_fail("body must be JSON {kind?}", "bad_request"))
        kind = args.get("kind")
        if kind is not None and kind not in KINDS:
            raise LayoutRefusal(_fail(f"unknown layout kind: {kind!r}", "bad_request"))
        vid = self._key(vid, profile, cls, kind)
        action = self._layout_gate(header(LAYOUT_CLASS_HEADER), cls)
        store = self.layout_store()
        if action == "hold":
            seq = store.hold(vid, profile, cls, "reset", kind)
            return {"ok": True, "queued": True, "held": True, "seq": seq,
                    "message": "Applies when the car is parked"}
        n = store.reset(vid, profile, cls, kind)
        return {"ok": True, "reset": n, "vid": vid, "profile": profile, "class": cls,
                "kind": kind, "snapshot": store.snapshot(vid, profile, cls)}

    def _layouts_undo(self, vid: str, profile: str, cls: str, *, body, header) -> dict:
        body(4096)  # no body is needed; read any so a refusal never resets the client
        vid = self._key(vid, profile, cls)
        action = self._layout_gate(header(LAYOUT_CLASS_HEADER), cls)
        store = self.layout_store()
        if action == "hold":
            seq = store.hold(vid, profile, cls, "undo_reset")
            return {"ok": True, "queued": True, "held": True, "seq": seq,
                    "message": "Applies when the car is parked"}
        if store.snapshot(vid, profile, cls) is None:
            return _fail("Nothing to undo: no reset in the last 7 days", "not_found")
        n = store.undo_reset(vid, profile, cls)
        return {"ok": True, "restored": n, "vid": vid, "profile": profile, "class": cls}

    def _selection_key(self, vid: str, profile: str, display: str, cls: str) -> str:
        if not DISPLAY_RE.match(display or ""):
            raise ValueError(f"bad display id: {display!r}")
        return self._key(vid, profile, cls)

    def _selection_get(self, vid: str, profile: str, display: str, cls: str) -> dict:
        vid = self._selection_key(vid, profile, display, cls)
        sel = self.layout_store().selection(vid, profile, display, cls)
        return {"vid": vid, "profile": profile, "display": display, "class": cls,
                "selection": sel}

    def _selection_put(self, vid: str, profile: str, display: str, cls: str, body, header) -> dict:
        vid = self._selection_key(vid, profile, display, cls)
        raw = body(16384)
        try:
            state = check_selection(json.loads(raw.decode("utf-8")) if raw else None)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("body must be JSON {mode, faces?, rotation?}") from None
        store = self.layout_store()
        old = store.selection(vid, profile, display, cls) or {}
        old_rot, new_rot = old.get("rotation"), state.get("rotation")
        # switching is allowed in any state; reordering a stored rotation is an edit (R1).
        # Picking a mode that joins the rotation (§5.9) appends it, which is not.
        if (old_rot is not None and new_rot is not None and new_rot != old_rot
                and new_rot != [*old_rot, state["mode"]]):
            self._layout_gate(header(LAYOUT_CLASS_HEADER), cls)
        if new_rot is None and old_rot is not None:
            state["rotation"] = old_rot
        sel = store.set_selection(vid, profile, display, cls, state)
        return {"ok": True, "vid": vid, "profile": profile, "display": display, "class": cls,
                "selection": sel}


__all__ = ["CAR", "EDIT_STATES", "LAYOUT_CLASS_HEADER", "LayoutApiMixin", "WRITABLE_KINDS"]
