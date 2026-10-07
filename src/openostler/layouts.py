# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The ``ostler.layout/1`` validator, server side (drive-modes spec §4, §8.2). Stdlib only.

One set of rules on both sides: the shell's ``ui/src/drive/validate.ts`` and this module
read the same limits (``layout_limits.json``, package data) and are run against the same
fixtures (``tests/fixtures/layouts/``), so a client that skips its check cannot store a
layout the server would refuse. The JSON Schema ``schemas/ostler-layout.schema.json`` is the
published shape; this module checks the same shape by hand (``jsonschema`` is dev-only)
and adds what a schema cannot say: the strict Moving rules per layout class (§4.3, §4.4):
at most six tiles (a status line counts two), the pane limits per class and one pane of a
kind, minimum tile and pane sizes, the 56 px digit and 24 px label floors, refresh at most
4 Hz, no sparkline, no Parked-only widget and no animation while Moving.

Errors refuse a save or an import; warnings (an unknown VSS path, widget or add-on) are
reported and render as honest placeholders. DM1 checks ``drive_mode`` layouts in full; the
``home``, ``rail`` and ``strip`` guardrails (§8.2 step 7) arrive with their editors in DM3.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

LIMITS_FILE = Path(__file__).resolve().parent / "layout_limits.json"

KINDS = ("drive_mode", "home", "rail", "strip")
SIZES = ("small", "medium", "wide", "hero")
STYLES = ("number", "arc", "bar", "chip", "text", "sparkline", "inclinometer", "compass")
_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_SLOT = re.compile(r"^[a-z0-9_]{1,16}$")
_WIDGET = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
_ICON = re.compile(r"^[a-z0-9_]+(-fill)?$")
_PATH = re.compile(r"^Vehicle(\.[A-Za-z0-9_]+)+$")
_URL = re.compile(r"(?i)\b(?:https?://|www\.)|[a-z0-9-]+\.(?:com|net|org|io|app|dev)\b")
# C0/C1 controls and the bidi embedding, override and isolate characters (§4.2, §7.6)
_CONTROL = re.compile("[\u0000-\u001f\u007f-\u009f‪-‮⁦-⁩]")


@lru_cache(maxsize=1)
def limits() -> dict:
    """``layout_limits.json`` (cached; treat as read-only)."""
    return json.loads(LIMITS_FILE.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Issue:
    """One finding: a stable ``rule`` code, words for a person, and where it is."""

    rule: str
    message: str
    cls: "str | None" = None
    face: "str | None" = None
    slot: "str | None" = None


@dataclass
class Report:
    errors: "list[Issue]" = field(default_factory=list)
    warnings: "list[Issue]" = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def rules(self) -> "list[str]":
        """The error rule codes, sorted and unique (what the shared fixtures compare)."""
        return sorted({i.rule for i in self.errors})


def graphemes(text: str) -> int:
    """User-perceived characters, approximately: code points that are not combining marks,
    variation selectors or joiners (the shell counts with ``Intl.Segmenter``)."""
    n = 0
    prev_zwj = False
    for ch in text:
        if ch == "‍":
            prev_zwj = True
            continue
        if unicodedata.combining(ch) or "︀" <= ch <= "️" or prev_zwj:
            prev_zwj = False
            continue
        n += 1
    return n


def _known_path(path: str) -> bool:
    try:
        from .metrics import is_known
    except ImportError:  # pragma: no cover - metrics ships with the platform
        return True
    return bool(is_known(path))


class _Checker:
    def __init__(self, doc: object, raw_size: "int | None") -> None:
        self.doc = doc
        self.raw_size = raw_size
        self.report = Report()
        self.lim = limits()

    # -- reporting -------------------------------------------------------- #
    def err(self, rule: str, msg: str, **where) -> None:
        self.report.errors.append(Issue(rule, msg, **where))

    def warn(self, rule: str, msg: str, **where) -> None:
        self.report.warnings.append(Issue(rule, msg, **where))

    def schema(self, msg: str, **where) -> None:
        self.err("schema", msg, **where)

    # -- text ------------------------------------------------------------- #
    def text(self, value: object, limit: int, what: str, required: bool = False, **where) -> None:
        if value is None and not required:
            return
        if not isinstance(value, str) or (required and not value.strip()):
            self.schema(f"{what} must be text", **where)
            return
        if _CONTROL.search(value):
            self.warn("text.control", f"{what}: control or bidi characters are stripped", **where)
        if _URL.search(value):
            self.err("text.url", f"{what} may not contain a link", **where)
        if graphemes(_CONTROL.sub("", value).strip()) > limit:
            self.err("text.too_long", f"{what} is longer than {limit} characters", **where)

    # -- the document ----------------------------------------------------- #
    def run(self) -> Report:
        doc = self.doc
        if self.raw_size is not None and self.raw_size > self.lim["max_bytes"]:
            self.err("size.too_big", "The file is larger than 256 KB")
        if not isinstance(doc, dict):
            self.schema("A layout is a JSON object")
            return self.report
        fmt = doc.get("format")
        if fmt != self.lim["format"]:
            if isinstance(fmt, str) and fmt.startswith("ostler.layout/"):
                self.err("format.unknown", "Made for a newer Ostler")
            else:
                self.schema("format must be ostler.layout/1")
            return self.report
        kind = doc.get("kind")
        if kind not in KINDS:
            self.schema("kind must be drive_mode, home, rail or strip")
            return self.report
        if not isinstance(doc.get("id"), str) or not _ID.match(doc["id"]):
            self.schema("id must be lower-case letters, digits, '.', '_' or '-'")
        self.text(doc.get("name"), self.lim["text"]["name"], "The name", required=True)
        self.text(doc.get("description"), self.lim["text"]["description"], "The description")
        if "icon" in doc and not (isinstance(doc["icon"], str) and _ICON.match(doc["icon"])):
            self.schema("icon must be a Material Symbols name")
        hint = doc.get("vehicle_hint")
        if hint is not None and not (isinstance(hint, dict) and set(hint) <= {"pack"}):
            self.schema("vehicle_hint may name a pack only")
        if doc.get("theme_hint") not in (None, "night_dim"):
            self.schema("theme_hint may only darken (night_dim)")
        classes = doc.get("classes")
        if not isinstance(classes, dict) or not classes:
            self.schema("classes must hold at least one layout class")
            return self.report
        for cls, faces in classes.items():
            if cls not in self.lim["classes"]:
                self.schema(f"Unknown layout class {cls!r}")
                continue
            if kind == "drive_mode":
                self.faces(cls, faces, doc)
            elif not (isinstance(faces, list) and len(faces) == 1 and isinstance(faces[0], dict)):
                self.schema(f"A {kind} layout has one face per class", cls=cls)
        return self.report

    def faces(self, cls: str, faces: object, doc: dict) -> None:
        fl = self.lim["faces"]
        if not isinstance(faces, list) or not fl["min"] <= len(faces) <= fl["max"]:
            self.schema(f"{cls}: a mode has 1 to 3 faces", cls=cls)
            return
        ids: "set[str]" = set()
        for face in faces:
            if not isinstance(face, dict):
                self.schema(f"{cls}: a face is an object", cls=cls)
                continue
            fid = face.get("face")
            if not isinstance(fid, str) or not _SLOT.match(fid):
                self.schema(f"{cls}: a face needs an id", cls=cls)
                fid = "?"
            elif fid in ids:
                self.schema(f"{cls}: face {fid!r} appears twice", cls=cls, face=fid)
            ids.add(fid)
            self.face(cls, fid, face, doc)

    def face(self, cls: str, fid: str, face: dict, doc: dict) -> None:
        where = {"cls": cls, "face": fid}
        self.text(face.get("name"), self.lim["text"]["face"], "The face name", required=True, **where)
        grid = self.grid(face.get("grid"), **where)
        widgets = face.get("widgets")
        if not isinstance(widgets, list) or len(widgets) > 24:
            self.schema(f"{cls}/{fid}: widgets must be a list of at most 24", **where)
            widgets = []
        by_slot: "dict[str, dict]" = {}
        for w in widgets:
            slot = self.widget(cls, fid, w, grid, doc)
            if slot is None:
                continue
            if slot in by_slot:
                self.err("widget.duplicate_slot", f"Slot {slot!r} is used twice", slot=slot, **where)
            by_slot[slot] = w
        moving = face.get("moving")
        if moving is None:
            if self.lim["classes"][cls]["moving_required"]:
                self.err("moving.missing", f"{cls}: every face needs a Moving section", **where)
            return
        self.moving(cls, fid, moving, by_slot)

    def grid(self, g: object, **where) -> "tuple[int, int] | None":
        if not isinstance(g, dict):
            self.schema("grid needs cols and rows", **where)
            return None
        c, r = g.get("cols"), g.get("rows")
        if not (_int(c) and 1 <= c <= 12 and _int(r) and 1 <= r <= 8):
            self.schema("grid: 1-12 columns and 1-8 rows", **where)
            return None
        return c, r

    def bind(self, b: object, doc: dict, what: str, **where) -> None:
        if not isinstance(b, dict):
            self.schema(f"{what} must be an object", **where)
            return
        keys = set(b)
        if keys == {"path"}:
            p = b["path"]
            if not isinstance(p, str) or not _PATH.match(p):
                self.schema(f"{what}: a VSS path starts with Vehicle.", **where)
            elif not _known_path(p):
                self.warn("path.unknown", f"{p} is not a known VSS path: Not available on this car", **where)
        elif keys == {"pack", "signal"}:
            hint = (doc.get("vehicle_hint") or {}).get("pack")
            if hint != b.get("pack"):
                self.err("bind.pack", f"{what}: a pack signal needs vehicle_hint.pack {b.get('pack')!r}", **where)
        elif keys == {"drive_tile"}:
            if not (_int(b["drive_tile"]) and 0 <= b["drive_tile"] <= 11):
                self.schema(f"{what}: drive_tile is 0-11", **where)
        else:
            self.schema(f"{what}: one of path, pack+signal or drive_tile", **where)

    def widget(self, cls: str, fid: str, w: object, grid, doc: dict) -> "str | None":
        if not isinstance(w, dict):
            self.schema(f"{cls}/{fid}: a widget is an object", cls=cls, face=fid)
            return None
        slot = w.get("slot")
        if not isinstance(slot, str) or not _SLOT.match(slot):
            self.schema(f"{cls}/{fid}: a widget needs a slot id", cls=cls, face=fid)
            return None
        where = {"cls": cls, "face": fid, "slot": slot}
        kind = w.get("widget")
        if not isinstance(kind, str) or not _WIDGET.match(kind):
            self.schema(f"Slot {slot}: widget must be an id like ostler.gauge", **where)
        elif kind not in self.lim["widgets"]:
            self.warn("widget.unknown", f"Slot {slot}: {kind} needs an add-on", **where)
        at = w.get("at")
        at_ok = isinstance(at, list) and len(at) == 2 and all(_int(v) and v >= 0 for v in at)
        if not at_ok:
            self.schema(f"Slot {slot}: at is [column, row]", **where)
        elif grid and (at[0] >= grid[0] or at[1] >= grid[1]):
            self.err("widget.outside_grid", f"Slot {slot} is outside the {grid[0]}×{grid[1]} grid", **where)
        span = w.get("span")
        if span is not None:
            if not (isinstance(span, list) and len(span) == 2 and all(_int(v) and v >= 1 for v in span)):
                self.schema(f"Slot {slot}: span is [columns, rows]", **where)
            elif grid and at_ok and (at[0] + span[0] > grid[0] or at[1] + span[1] > grid[1]):
                self.err("widget.outside_grid", f"Slot {slot} runs outside the {grid[0]}×{grid[1]} grid", **where)
        if w.get("size") not in SIZES:
            self.schema(f"Slot {slot}: size is small, medium, wide or hero", **where)
        style = w.get("style")
        if style is not None:
            allowed = self.lim["widgets"].get(kind, {}).get("styles")
            if style not in STYLES:
                self.schema(f"Slot {slot}: unknown style {style!r}", **where)
            elif allowed is not None and style not in allowed:
                self.err("widget.style", f"Slot {slot}: {kind} cannot be drawn as {style}", **where)
        for key in ("bind", "bind2"):
            if key in w:
                self.bind(w[key], doc, f"Slot {slot} {key}", **where)
        values = w.get("values")
        if values is not None:
            if not isinstance(values, list) or len(values) > 2:
                self.schema(f"Slot {slot}: a status line has at most 2 values", **where)
            else:
                for v in values:
                    if isinstance(v, dict) and "bind" in v:
                        self.bind(v["bind"], doc, f"Slot {slot} value", **where)
                        self.text(v.get("label"), self.lim["text"]["label"], f"Slot {slot} value label", **where)
                    else:
                        self.schema(f"Slot {slot}: each value needs a bind", **where)
        self.text(w.get("label"), self.lim["text"]["label"], f"Slot {slot} label", **where)
        self.text(w.get("label2"), self.lim["text"]["label"], f"Slot {slot} label", **where)
        if "icon" in w and not (isinstance(w["icon"], str) and _ICON.match(w["icon"])):
            self.schema(f"Slot {slot}: icon must be a Material Symbols name", **where)
        if "dec" in w and not (_int(w["dec"]) and 0 <= w["dec"] <= 4):
            self.schema(f"Slot {slot}: dec is 0-4", **where)
        if "refresh_hz" in w and not (_num(w["refresh_hz"]) and w["refresh_hz"] > 0):
            self.schema(f"Slot {slot}: refresh_hz must be above 0", **where)
        self.levels(w, slot, where)
        return slot

    def levels(self, w: dict, slot: str, where: dict) -> None:
        rng = w.get("range")
        if rng is not None:
            if not _pair(rng):
                self.schema(f"Slot {slot}: range is [min, max]", **where)
                rng = None
            elif None not in rng and rng[0] >= rng[1]:
                self.err("levels.order", f"Slot {slot}: the range runs low to high", **where)
        lv = w.get("levels")
        if lv is None:
            return
        if not isinstance(lv, dict) or not set(lv) <= {"normal", "warning", "critical"}:
            self.schema(f"Slot {slot}: levels are normal, warning and critical", **where)
            return
        for name, p in lv.items():
            if not _pair(p):
                self.schema(f"Slot {slot}: {name} is [min, max]", **where)
                continue
            lo, hi = p
            if lo is not None and hi is not None and lo > hi:
                self.err("levels.order", f"Slot {slot}: {name} runs low to high", **where)
            if rng and None not in rng:
                for v in (lo, hi):
                    if v is not None and not rng[0] <= v <= rng[1]:
                        self.err("levels.range", f"Slot {slot}: {name} is outside the range", **where)

    # -- the Moving section (§4.3) ----------------------------------------- #
    def moving(self, cls: str, fid: str, mv: object, by_slot: "dict[str, dict]") -> None:
        where = {"cls": cls, "face": fid}
        lim, cl = self.lim, self.lim["classes"][cls]
        if not isinstance(mv, dict):
            self.schema("moving needs show, grid and place", **where)
            return
        show = mv.get("show")
        if not (isinstance(show, list) and show and all(isinstance(s, str) for s in show)) or len(set(show)) != len(show):
            self.schema("moving.show lists slot ids once each", **where)
            return
        grid = self.grid(mv.get("grid"), **where)
        place = mv.get("place")
        if not isinstance(place, dict):
            self.schema("moving.place gives each slot [col, row, cols, rows]", **where)
            place = {}
        floors = lim["moving"]
        if cl["type"]["digits"] < floors["digits_floor_px"] or cl["type"]["label"] < floors["label_floor_px"]:
            self.err("moving.type_floor", f"{cls}: Moving digits need {floors['digits_floor_px']} px and labels "
                     f"{floors['label_floor_px']} px", **where)
        tiles = 0
        panes: "dict[str, int]" = {}
        cells: "dict[tuple[int, int, str], str]" = {}
        content = cl["content"]
        for slot in show:
            w = by_slot.get(slot)
            sw = {**where, "slot": slot}
            if w is None:
                self.err("moving.unknown_slot", f"Moving shows {slot!r}, which is not on this face", **sw)
                continue
            if w.get("hidden"):
                self.err("moving.hidden", f"Slot {slot} is hidden and cannot show while Moving", **sw)
            spec = lim["widgets"].get(w.get("widget"))
            if spec is None:
                # fail closed (R2): it renders as an empty cell and still counts as a tile
                self.warn("moving.unknown_widget", f"Slot {slot}: an unknown widget renders as an empty cell while Moving", **sw)
                template = "tiles"
            else:
                template = spec["template"]
                if template is None:
                    self.err("moving.parked_only", f"Slot {slot} shows only when parked", **sw)
            if w.get("style") == "sparkline":
                self.err("moving.sparkline", f"Slot {slot}: no sparkline while Moving", **sw)
            if w.get("animate") is True:
                self.err("moving.animation", f"Slot {slot}: no animation while Moving", **sw)
            hz = w.get("refresh_hz")
            if _num(hz) and hz > floors["max_refresh_hz"]:
                self.err("moving.refresh", f"Slot {slot}: refresh at most {floors['max_refresh_hz']} Hz while Moving", **sw)
            kind = lim["templates"].get(template, {}).get("kind") if template else None
            if kind == "tile":
                tiles += lim["templates"][template]["cost"]
            elif kind == "pane":
                panes[template] = panes.get(template, 0) + 1
            p = place.get(slot)
            if not (isinstance(p, list) and len(p) == 4 and all(_int(v) and v >= 0 for v in p) and p[2] >= 1 and p[3] >= 1):
                self.err("moving.place", f"Slot {slot} has no place in the Moving grid", **sw)
                continue
            if grid and (p[0] + p[2] > grid[0] or p[1] + p[3] > grid[1]):
                self.err("moving.place", f"Slot {slot} runs outside the Moving grid", **sw)
                continue
            # a tile may sit over a pane (the map's speed overlay, §4.3); two tiles or two
            # panes may not share a cell
            layer = "pane" if kind == "pane" else "tile"
            for x in range(p[0], p[0] + p[2]):
                for y in range(p[1], p[1] + p[3]):
                    if (x, y, layer) in cells:
                        self.err("moving.overlap", f"Slots {cells[(x, y, layer)]} and {slot} overlap", **sw)
                    cells[(x, y, layer)] = slot
            if grid and content and kind:
                w_px = content[0] / grid[0] * p[2]
                h_px = content[1] / grid[1] * p[3]
                need = cl["min_tile"] if kind == "tile" else cl["min_pane"]
                if need and (w_px + 0.5 < need[0] or h_px + 0.5 < need[1]):
                    rule = "moving.tile_too_small" if kind == "tile" else "moving.pane_too_small"
                    what = "Tile" if kind == "tile" else "Pane"
                    self.err(rule, f"{what} {slot} too small on {cls}: {round(w_px)}×{round(h_px)} px, "
                             f"needs {need[0]}×{need[1]}", **sw)
        if tiles > floors["max_tiles"]:
            self.err("moving.too_many_tiles", f"{cls}: {tiles} tiles while Moving, at most {floors['max_tiles']}", **where)
        if sum(panes.values()) > cl["max_panes"]:
            self.err("moving.too_many_panes", f"{cls}: at most {cl['max_panes']} panes while Moving", **where)
        for t, n in panes.items():
            if n > 1:
                self.err("moving.duplicate_pane", f"{cls}: at most one {t} pane while Moving", **where)


def _int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _pair(v: object) -> bool:
    return isinstance(v, list) and len(v) == 2 and all(x is None or _num(x) for x in v)


def validate_layout(doc: object, raw_size: "int | None" = None) -> Report:
    """Check an ``ostler.layout/1`` document; ``raw_size`` is the file's byte length."""
    return _Checker(doc, raw_size).run()


def validate_bytes(data: bytes) -> Report:
    """Check a layout file as received (size limit, JSON, then :func:`validate_layout`)."""
    if len(data) > limits()["max_bytes"]:
        r = Report()
        r.errors.append(Issue("size.too_big", "The file is larger than 256 KB"))
        return r
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        r = Report()
        r.errors.append(Issue("schema", "Not a JSON file"))
        return r
    return validate_layout(doc, raw_size=len(data))
