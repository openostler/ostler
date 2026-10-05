"""Layering guard — the core must never import the consumer/presentation layer.

Core = car communication + data interpretation (see SCOPE.md). It must not import from
`web` (or a future `apps`) — data flows one way: comms -> interpretation -> snapshot ->
consumers. This AST scan fails if any core module imports a forbidden package, so the
drift can't creep back in silently.
"""
import ast
import pathlib

import pytest

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "d2diag"

# Everything that is CORE (comms + interpretation). Excludes web/ (consumer) and
# community/ (opt-in upload client — consumer side).
_CORE = [
    "transport", "kline", "kwp2000", "session.py", "ports.py", "signals", "menus.py", "catalog.py",
    "commands.py",
    "faultscan.py", "sniff", "td5", "slabs", "airbag", "bcu", "ace", "autobox",
    "gps", "logbook",  # ADR-0009: session logbook + GPS are core (stdlib + pyserial)
    "geo",  # ADR-0011: place names (offline GeoNames + OSM enrichment)
    "imu",  # ADR-0010: Pi IMU input is core (stdlib only)
    "pack.py", "_compat.py",  # ADR-0013: the VehiclePack contract and the import shim
    "vehicles",  # the Discovery 2 pack (td5, slabs, bcu, airbag, ace, autobox, sniff, …)
]
_FORBIDDEN = {"web", "apps"}
# The pack's data-source module is the consumer boundary (it builds web DataSources).
_CORE_EXCEPT = {"vehicles/lr_d2/sources.py"}


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


def test_vehicle_pack_is_scanned():
    # ADR-0013: the moved Discovery 2 module layers must stay under the guard.
    rel = {p.relative_to(_SRC).as_posix() for p in _core_files()}
    assert "vehicles/lr_d2/td5/td5.py" in rel and "vehicles/lr_d2/slabs/slabs.py" in rel
    assert "vehicles/lr_d2/sources.py" not in rel


# ---- ADR-0013 / Phase 0: the platform never reaches into a vehicle pack ------------------- #
# Platform = every src/d2diag/**/*.py except the packs (vehicles/) and the old-name import
# shim (_compat.py). It talks to the vehicle only through d2diag.pack.active_pack().
_LEGACY_D2 = (
    *(f"d2diag.{m}" for m in ("td5", "slabs", "bcu", "airbag", "ace", "autobox")),
    *(f"d2diag.sniff.{m}" for m in ("library", "emulator_map", "importer", "fault_import")),
    "d2diag.logbook.synth",
)
_PACK_PREFIX = "d2diag.vehicles"



def _platform_files() -> "list[pathlib.Path]":
    out = []
    for p in sorted(_SRC.rglob("*.py")):
        rel = p.relative_to(_SRC)
        if rel.parts[0] == "vehicles" or rel.as_posix() == "_compat.py":
            continue
        out.append(p)
    return out


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
    if mod == _PACK_PREFIX or mod.startswith(_PACK_PREFIX + "."):
        return True
    return any(mod == old or mod.startswith(old + ".") for old in _LEGACY_D2)


def _dynamic_pack_imports(path: pathlib.Path):
    """``import_module("…vehicles…")`` / ``__import__("…vehicles…")`` calls, and any other
    string naming a pack module — except ``pack._BUILTIN_FALLBACK`` (the Phase 0 fallback)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    allowed = set()
    if path.relative_to(_SRC).as_posix() == "pack.py":
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_BUILTIN_FALLBACK"
                                                    for t in node.targets)):
                allowed.add(id(node.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name in ("import_module", "__import__") and node.args:
                arg = node.args[0]
                if (isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                        and "vehicles" in arg.value and id(arg) not in allowed):
                    yield node.lineno, arg.value
        elif (isinstance(node, ast.Constant) and isinstance(node.value, str)
              and node.value.startswith(_PACK_PREFIX) and id(node) not in allowed):
            yield node.lineno, node.value


@pytest.mark.parametrize("path", _guarded_platform_files(), ids=lambda p: p.relative_to(_SRC).as_posix())
def test_platform_never_imports_a_pack(path: pathlib.Path):
    for lineno, mod in _absolute_imports(path):
        assert not _is_pack_module(mod), (
            f"{path.relative_to(_SRC)}:{lineno} imports vehicle-pack code {mod!r}: "
            f"go through d2diag.pack.active_pack()")
    for lineno, ref in _dynamic_pack_imports(path):
        assert False, f"{path.relative_to(_SRC)}:{lineno} loads a vehicle pack by name: {ref!r}"


def _pack_module_literals() -> "frozenset[str]":
    from d2diag.vehicles.lr_d2 import PACK

    return frozenset(PACK.module_ids()) | frozenset(PACK.aliases())


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
    assert not any(r.startswith("vehicles/") for r in rel) and "_compat.py" not in rel
    assert len(_guarded_platform_files()) > 30
    # the pack itself stays under the web guard (except its consumer-boundary sources.py)
    core = {p.relative_to(_SRC).as_posix() for p in _core_files()}
    assert any(r.startswith("vehicles/lr_d2/") for r in core)


def test_import_resolution_catches_relative_and_legacy_names():
    # The guard resolves ``from .. import td5`` in d2diag/web/x.py to d2diag.td5.
    probe = _SRC / "web" / "_probe_never_written.py"
    assert _package_of(probe) == "d2diag.web"
    src = "from .. import td5\nfrom ..vehicles.lr_d2 import PACK\nfrom . import server\n"
    mods = [m for _ln, m in _absolute_imports(probe, src)]
    assert "d2diag.td5" in mods and "d2diag.vehicles.lr_d2" in mods
    assert [m for m in mods if _is_pack_module(m)] == [
        "d2diag.td5", "d2diag.vehicles.lr_d2", "d2diag.vehicles.lr_d2.PACK"]
    init = _SRC / "sniff" / "__init__.py"
    assert [m for _ln, m in _absolute_imports(init, "from .importer import x\n")] == [
        "d2diag.sniff.importer", "d2diag.sniff.importer.x"]
    assert _is_pack_module("d2diag.td5.td5") and _is_pack_module("d2diag.vehicles.lr_d2")
    assert _is_pack_module("d2diag.sniff.importer") and not _is_pack_module("d2diag.sniff.modules")
    assert not _is_pack_module("d2diag.td5x")
