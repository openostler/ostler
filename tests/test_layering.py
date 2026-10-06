# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Layering guard — the core must never import the consumer/presentation layer.

Core = car communication + data interpretation (see SCOPE.md). It must not import from
`web` (or a future `apps`) — data flows one way: comms -> interpretation -> snapshot ->
consumers. This AST scan fails if any core module imports a forbidden package, so the
drift can't creep back in silently.
"""
import ast
import pathlib

import pytest

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "openostler"

# Everything that is CORE (comms + interpretation). Excludes web/ (consumer) and
# community/ (opt-in upload client — consumer side).
_CORE = [
    "transport", "kline", "kwp2000", "session.py", "ports.py", "signals", "menus.py", "catalog.py",
    "commands.py", "faultscan.py", "modscan.py", "sniff", "dtc",
    "gps", "logbook",  # ADR-0009: session logbook + GPS are core (stdlib + pyserial)
    "geo",  # ADR-0011: place names (offline GeoNames + OSM enrichment)
    "imu",  # ADR-0010: Pi IMU input is core (stdlib only)
    "pack.py",  # ADR-0013: the VehiclePack contract
]
_FORBIDDEN = {"web", "apps"}
_CORE_EXCEPT: "set[str]" = set()


def _core_files() -> "list[pathlib.Path]":
    out: "list[pathlib.Path]" = []
    for name in _CORE:
        p = _SRC / name
        if p.is_dir():
            out += sorted(p.rglob("*.py"))
        elif p.exists():
            out.append(p)
    return [p for p in out if p.relative_to(_SRC).as_posix() not in _CORE_EXCEPT]


def _imported_modules(path: pathlib.Path):
    """Yield every module path referenced by an import in this file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            yield node.module or ""
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name


@pytest.mark.parametrize("path", _core_files(), ids=lambda p: p.relative_to(_SRC).as_posix())
def test_core_does_not_import_consumer_layer(path: pathlib.Path):
    for mod in _imported_modules(path):
        parts = set(mod.split("."))
        offending = parts & _FORBIDDEN
        assert not offending, f"{path.relative_to(_SRC)} imports consumer layer: {mod!r}"


def test_core_file_list_is_present():
    # Guard against the scan silently matching nothing (e.g. a path rename).
    files = _core_files()
    assert len(files) > 15


def test_logbook_gps_and_imu_are_scanned():
    # ADR-0009/0010: the new core packages must be part of the scan, not silently skipped.
    names = {p.relative_to(_SRC).parts[0] for p in _core_files()}
    assert {"gps", "logbook", "imu"} <= names


# ---- ADR-0013 / ADR-0015: the platform never reaches into a vehicle pack ------------------- #
# Platform = every src/openostler/**/*.py. It talks to the vehicle only through
# openostler.pack.active_pack(); no vehicle pack (the reference pack is the separate
# distribution "d2diag") may be imported or loaded by name.
_PACK_PREFIXES = ("d2diag",)
# The Discovery 2 reference pack's module ids and aliases: the platform must not name them.
_D2_MODULE_LITERALS = frozenset({"td5", "motor", "slabs", "bcu", "airbag", "ace", "autobox",
                                 "eat", "gearbox"})


# Strings equal to a pack name that are not pack references (with why).
_PACK_STRING_ALLOW = {
    # ~/.config/d2diag/community.json: consent given before the split is still honoured.
    "community/__init__.py": frozenset({"d2diag"}),
}


def _platform_files() -> "list[pathlib.Path]":
    return sorted(_SRC.rglob("*.py"))


def _guarded_platform_files() -> "list[pathlib.Path]":
    return _platform_files()


def _package_of(path: pathlib.Path) -> str:
    """Dotted package a file's relative imports resolve against."""
    rel = path.relative_to(_SRC.parent).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        return ".".join(parts[:-1])
    return ".".join(parts[:-1])


def _absolute_imports(path: pathlib.Path, source: "str | None" = None):
    """Yield ``(lineno, module)`` for every module an import statement can load, with
    relative imports resolved (``node.level`` against the file's package). For
    ``from X import a`` both ``X`` and ``X.a`` are yielded (``a`` may be a submodule)."""
    tree = ast.parse(source if source is not None else path.read_text(encoding="utf-8"))
    pkg = _package_of(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = pkg.split(".")
                base_parts = base_parts[: len(base_parts) - (node.level - 1)]
                base = ".".join(base_parts)
                mod = f"{base}.{node.module}" if node.module else base
            else:
                mod = node.module or ""
            yield node.lineno, mod
            for alias in node.names:
                if alias.name != "*":
                    yield node.lineno, f"{mod}.{alias.name}"


def _is_pack_module(mod: str) -> bool:
    return any(mod == p or mod.startswith(p + ".") for p in _PACK_PREFIXES)


def _dynamic_pack_imports(path: pathlib.Path):
    """``import_module("d2diag…")`` / ``__import__("…vehicles…")`` calls, and any other
    string constant that is a pack module reference (``d2diag``, ``d2diag.x``, ``d2diag:PACK``).
    Prose that merely mentions the pack (an install hint) is not a reference."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name in ("import_module", "__import__") and node.args:
                arg = node.args[0]
                if (isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                        and ("vehicles" in arg.value or _is_pack_module(arg.value))):
                    yield node.lineno, arg.value
        elif (isinstance(node, ast.Constant) and isinstance(node.value, str)
              and " " not in node.value and _is_pack_module(node.value.split(":")[0])):
            yield node.lineno, node.value


@pytest.mark.parametrize("path", _guarded_platform_files(), ids=lambda p: p.relative_to(_SRC).as_posix())
def test_platform_never_imports_a_pack(path: pathlib.Path):
    for lineno, mod in _absolute_imports(path):
        assert not _is_pack_module(mod), (
            f"{path.relative_to(_SRC)}:{lineno} imports vehicle-pack code {mod!r}: "
            f"go through openostler.pack.active_pack()")
    allow = _PACK_STRING_ALLOW.get(path.relative_to(_SRC).as_posix(), frozenset())
    for lineno, ref in _dynamic_pack_imports(path):
        if ref in allow:
            continue
        assert False, f"{path.relative_to(_SRC)}:{lineno} loads a vehicle pack by name: {ref!r}"


def _pack_module_literals() -> "frozenset[str]":
    return _D2_MODULE_LITERALS


def _docstring_nodes(tree) -> "set[int]":
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.add(id(body[0].value))
    return out


# String literals the platform may carry although they equal a pack module id (with why).
# The spec's "· motor: rpm …" connection-log prose sits inside an f-string, so it is not a
# bare constant equal to an id and needs no entry today.
_LITERAL_ALLOW: "dict[str, frozenset[str]]" = {}


@pytest.mark.parametrize("path", _guarded_platform_files(), ids=lambda p: p.relative_to(_SRC).as_posix())
def test_platform_has_no_module_literals(path: pathlib.Path):
    ids = _pack_module_literals()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = _docstring_nodes(tree)
    allow = _LITERAL_ALLOW.get(path.relative_to(_SRC).as_posix(), frozenset())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs
                and node.value.strip().lower() in ids and node.value not in allow):
            assert False, (f"{path.relative_to(_SRC)}:{node.lineno} names vehicle module "
                           f"{node.value!r}: ask the active pack instead")


def test_platform_scan_covers_the_platform():
    files = _platform_files()
    rel = {p.relative_to(_SRC).as_posix() for p in files}
    assert len(files) > 30
    assert {"catalog.py", "commands.py", "menus.py", "faultscan.py", "modscan.py", "pack.py",
            "sniff/modules.py", "signals/__init__.py", "dtc/__init__.py"} <= rel
    assert not (_SRC / "vehicles").exists() and not (_SRC / "_compat.py").exists()


def test_import_resolution_catches_relative_and_pack_names():
    # The guard resolves ``from .. import x`` in openostler/web/x.py against openostler.
    probe = _SRC / "web" / "_probe_never_written.py"
    assert _package_of(probe) == "openostler.web"
    src = "from .. import pack\nimport d2diag\nfrom d2diag.td5 import Td5\nfrom . import server\n"
    mods = [m for _ln, m in _absolute_imports(probe, src)]
    assert "openostler.pack" in mods and "openostler.web.server" in mods
    assert [m for m in mods if _is_pack_module(m)] == ["d2diag", "d2diag.td5", "d2diag.td5.Td5"]
    assert _is_pack_module("d2diag:PACK".split(":")[0]) and not _is_pack_module("d2diagx")
    assert not _is_pack_module("openostler.sniff.modules")
