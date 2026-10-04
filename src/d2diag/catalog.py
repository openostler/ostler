"""Catalog: every NanoCom function per module, each with one derived status and a safety class.

ADR-0008 and ``specs/2026-10-05-ui-overhaul-design.md`` are the contract. The module
menus (``src/d2diag/*/menu.py``, collected in :mod:`d2diag.menus`) say *what exists*; this
module derives *how far we are* from what each item links to, never from a hand copy:

1. ``sig``: the signal-store record (``at`` = ``"LID@offset"`` picks among same-name
   length variants, otherwise the first) → ``proven`` = verified, ``candidate`` = candidate.
2. ``actions``: the command registry (:mod:`d2diag.commands`). All gated → ``sniff`` and
   safety ``gated``; otherwise the worst non-gated action (planned → sniff, experimental →
   candidate, all verified → verified). Safety = the most severe action safety.
3. Otherwise the hand ``status`` (``verified`` only for session and fault items).

Core module: data only, no I/O beyond reading the signal store, never imports ``web``.
"""
from __future__ import annotations

from . import commands, signals
from .menus import MENUS

STATUSES = ("verified", "candidate", "sniff", "untranscribed")
SAFETY_RANK = {"read": 0, "actuator": 1, "service": 2, "gated": 3}
GROUP_PAGES = ("session", "faults", "inputs", "outputs", "settings", "utilities")
# Fixed page order of /catalog; session groups fold into faults.
PAGES = (("faults", "Faults"), ("inputs", "Inputs"), ("outputs", "Outputs"),
         ("settings", "Settings"), ("utilities", "Utilities"))
_PAGE_OF = {"session": "faults"}
# Hand "verified" is allowed only here (connection, read/clear faults: no store or registry entry).
HAND_VERIFIED_PAGES = ("session", "faults")
# Safety of an item with no link and no override, by the page it sits on.
_DEFAULT_SAFETY = {"outputs": "actuator", "utilities": "service"}

# UI module id ↔ store module. The UI calls the Td5 "motor"; the EAT has two common names.
UI_MODULE = {"td5": "motor"}
_STORE_ALIASES = {"motor": "td5", "eat": "autobox", "gearbox": "autobox"}

# Display names, matching ui/src/layout.ts MODULE_NAME (keyed by store module).
MODULE_NAMES = {
    "td5": "TD5 (engine)",
    "slabs": "SLABS (ABS + air suspension)",
    "bcu": "BCU (body control)",
    "ace": "ACE (active cornering)",
    "autobox": "Auto gearbox (EAT)",
    "airbag": "Airbag / SRS",
}

# Store signals deliberately not linked from any menu item (drift guard in tests/test_catalog.py).
UNLINKED_OK: "dict[str, set[str]]" = {
    "td5": {
        "ext_temp",  # phantom: the sensor is not fitted on the Td5, constant 150 °C (ignore)
    },
    "slabs": set(),
}

_LEGACY = {"verified": "ok", "candidate": "maybe"}


def store_module_for(ui_id: str) -> str:
    """Store module for a UI module id (``motor`` → ``td5``; ``eat``/``gearbox`` → ``autobox``)."""
    return _STORE_ALIASES.get(ui_id, ui_id)


def ui_module_for(store_module: str) -> str:
    return UI_MODULE.get(store_module, store_module)


def legacy_status(status: str) -> str:
    """verified → ok, candidate → maybe, anything else → todo (the admin /map vocabulary)."""
    return _LEGACY.get(status, "todo")


def _empty_cov() -> "dict[str, int]":
    return {"verified": 0, "candidate": 0, "sniff": 0, "untranscribed": 0, "total": 0}


def _add(cov: dict, status: str) -> None:
    cov[status] += 1
    cov["total"] += 1


def find_record(store_module: str, sig: str, at: "str | None" = None) -> "signals.Signal | None":
    """The signal-store record for ``sig``: the one at ``at`` (``"1C@4"``) if given, else the first."""
    for s in signals.load_signals(store_module):
        if s.name != sig:
            continue
        if at is None or f"{s.lid:02X}@{s.offset}" == at.upper():
            return s
    return None


def _ctx(store_module: str, group: dict, item: dict) -> str:
    return f"{store_module}/{group.get('id')}/{item.get('id')}"


def derive(store_module: str, group: dict, item: dict) -> "tuple[str, str, list]":
    """``(status, safety, [Command])`` for one menu item. Raises ValueError on a bad item."""
    where = _ctx(store_module, group, item)
    sig, acts = item.get("sig"), item.get("actions")
    if (sig or acts) and "status" in item:
        raise ValueError(f"{where}: an item with sig/actions must not carry a hand status")
    if sig:
        rec = find_record(store_module, sig, item.get("at"))
        if rec is None:
            raise ValueError(f"{where}: sig {sig!r} (at {item.get('at')}) is not in the store")
        status = "verified" if rec.confidence == signals.PROVEN else "candidate"
        return status, item.get("safety", "read"), []
    if acts:
        cmds = []
        for a in acts:
            c = commands.get(store_module, a)
            if c is None:
                raise ValueError(f"{where}: action {a!r} is not in commands.REGISTRY")
            cmds.append(c)
        safety = max((c.safety for c in cmds), key=SAFETY_RANK.__getitem__)
        live = [c for c in cmds if c.safety != "gated"]
        if not live:
            status = "sniff"
        elif any(c.status == "planned" for c in live):
            status = "sniff"
        elif any(c.status == "experimental" for c in live):
            status = "candidate"
        else:
            status = "verified"
        return status, item.get("safety", safety), cmds
    status = item.get("status") or ("untranscribed" if item.get("untranscribed") else None)
    if status not in STATUSES:
        raise ValueError(f"{where}: hand status {status!r} not in {STATUSES}")
    if status == "verified" and group.get("page") not in HAND_VERIFIED_PAGES:
        raise ValueError(f"{where}: hand 'verified' is only allowed on session/fault items")
    if item.get("untranscribed") and status != "untranscribed":
        raise ValueError(f"{where}: an untranscribed placeholder must have status 'untranscribed'")
    page = group.get("page", "")
    return status, item.get("safety", _DEFAULT_SAFETY.get(page, "read")), []


def _item_out(store_module: str, group: dict, item: dict) -> dict:
    status, safety, cmds = derive(store_module, group, item)
    lid = item.get("lid")
    if lid is None and item.get("sig"):
        rec = find_record(store_module, item["sig"], item.get("at"))
        lid = f"{rec.lid:02x}" if rec else None
    return {
        "id": item["id"], "name": item["name"], "status": status, "safety": safety,
        "sig": item.get("sig"), "lid": lid, "ref": item.get("ref", ""),
        "note": item.get("note", ""), "placeholder": bool(item.get("untranscribed")),
        "pages": item.get("pages"), "actions": [c.as_dict() for c in cmds],
    }


def build_catalog(store_module: str) -> dict:
    """The /catalog page structure for one module (the server adds the outer ``module`` key)."""
    store_module = store_module_for(store_module)
    pages = {pid: {"id": pid, "title": title, "coverage": _empty_cov(), "groups": []}
             for pid, title in PAGES}
    total = _empty_cov()
    for group in MENUS.get(store_module, []):
        gpage = group.get("page")
        if gpage not in GROUP_PAGES:
            raise ValueError(f"{store_module}/{group.get('id')}: page {gpage!r} not in {GROUP_PAGES}")
        page = pages[_PAGE_OF.get(gpage, gpage)]
        items = [_item_out(store_module, group, it) for it in group.get("items", [])]
        for it in items:
            _add(page["coverage"], it["status"])
            _add(total, it["status"])
        page["groups"].append({"id": group["id"], "title": group["cat"],
                               "parent": group.get("parent"), "nanocom": group.get("nanocom"),
                               "items": items})
    return {"store_module": store_module, "coverage": total,
            "pages": [pages[pid] for pid, _ in PAGES]}


def module_summary() -> list:
    """One row per module for the header dropdown: ``{module, store_module, name, coverage}``."""
    return [{"module": ui_module_for(m), "store_module": m, "name": MODULE_NAMES.get(m, m),
             "coverage": build_catalog(m)["coverage"]} for m in MENUS]


def legacy_menu(store_module: str) -> list:
    """The pre-ADR-0008 menu shape for the admin /map and ``DiagServer.coverage()``:
    ``[{"cat", "items": [{"name", "status" (ok/maybe/todo), "ref", "lid"?, "sig"?}]}]``
    (``lid``/``sig`` only on items that have them, as the old menus did)."""
    store_module = store_module_for(store_module)
    out = []
    for group in MENUS.get(store_module, []):
        items = []
        for it in group.get("items", []):
            status, _, _ = derive(store_module, group, it)
            row = {"name": it["name"], "status": legacy_status(status), "ref": it.get("ref", "")}
            row.update({k: it[k] for k in ("lid", "sig") if it.get(k)})  # only when set, as before
            items.append(row)
        out.append({"cat": group["cat"], "items": items})
    return out
