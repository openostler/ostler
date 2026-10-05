---
title: "Phase 0 — VehiclePack decoupling in place (ADR-0013 step 1) — design"
area: specs
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, specs/2026-10-06-platform-direction-design.md, SCOPE.md, CONSTITUTION.md]
summary: >
  Moves every Discovery 2 specific behind a VehiclePack contract (src/d2diag/pack.py, entry point "ostler.vehicle", built-in fallback d2diag.vehicles.lr_d2) with no behaviour change: D2 code moves under vehicles/lr_d2 with a meta-path import shim, canonical module ids (td5 replaces the "motor" alias, migrated on read), generic catalog/commands/menus/faultscan/sniff/logbook/server, a /pack endpoint and a data-driven UI layout, layering + literal guards, a fake-pack platform test suite and a golden before/after diff.
---

# Phase 0 — VehiclePack decoupling in place — design

**Approval:** the owner approved this plan on 2026-10-06 (repo-structure plan, Step 1).
It records the agreed design; the implementation follows it. Open item for the owner:
`esp32/kline_node/live_html.h` fetches fault maps from a GitHub raw path that moves,
and deployed firmware falls back to its cached copy.

## Phase 0 plan (ADR-0013 step 1): move D2 behind `VehiclePack` in place, with no behaviour change

Everything below was checked against the repo at HEAD `d6a7028`. All the listed hotspots are confirmed, and I found more: `sniff/fault_import.py:206-221`, `sniff/library.py` (`KNOWN`), `sniff/emulator_map.py`, `sniff/importer.py`, `logbook/channels.py:74` (orders "td5" first), `logbook/demo/__init__.py` `DEMO_ROOT`, `web/server.py:264,433,437,441,872` (`_MODULE_COMMAND_PREFIXES`), `web/sources.py:243` (`_conf_of` special-cases slabs) and `web/sources.py:261` (`signal_status` from td5), `tools/dashboard.py:158-174` (docs and answer-key paths), `esp32/kline_node/live_html.h:77` (fetches `src/d2diag/td5|slabs/faultmap.json` from GitHub raw), `tests/test_logbook.py:547` (byte-for-byte golden of the regenerated demo).

Repo rule (CLAUDE.md "design before code"): ADR-0013 says Phase 0 gets its own spec. The integrator writes `specs/2026-10-xx-phase0-vehiclepack-decoupling.md` from this plan and gets owner approval first.

### 1. Contract: `src/d2diag/pack.py` (platform; never imports `vehicles`)
```python
PACK_API_VERSION = 1
@dataclass(frozen=True)
class ModuleSpec:
    id: str                         # canonical id = store id (signals/<id>.json, dtc/<id>.json, Command.module)
    name: str                       # "TD5 (engine)"
    address: int | None = None      # K-line diag address (0x13)
    init: str = "none"              # "fast" | "slow" | "none" (proprietary/unknown)
    keygen: Callable[[int, int], bytes] | None = None   # seed→key (td5.keygen.key_bytes_from_seed)
    aliases: tuple[str, ...] = ()   # legacy ids accepted on read ("motor")
    live: bool = True               # False → InfoDataSource
    fault_label: str = ""           # faultscan row label ("TD5")
@dataclass(frozen=True)
class FaultReader:  label: str; read: Callable[[str], list[str]]; note: str = ""   # read(real_port) owns establish/release
@dataclass(frozen=True)
class Detector:     module: str; how: str; match: Callable[[list[int]], bool]
@dataclass(frozen=True)
class SniffSpec:
    fast_init: Mapping[int, str]; slow_init: Mapping[int, str]
    extra_scan: tuple[int, ...] = ()          # modscan DEFAULT_SLOW extras (0x18, 0x5A)
    authoritative: tuple[Detector, ...] = ()  # always switch (airbag addressed)
    hints: tuple[Detector, ...] = ()          # seed only when module is None (EAT, ACE, BCU)
    tester: int = 0xF7
    importers: Mapping[str, Callable] = field(default_factory=dict)   # nanocom, fault_screen
@dataclass(frozen=True)
class DemoSpec:     sessions_dir: Path; sniff_log: Path | None; generate: Callable[[str], list[str]] | None
@dataclass(frozen=True)
class DocSource:    path: Path; group: str; title: str | None = None; recursive: bool = False; exclude: frozenset = frozenset(); optional: bool = False
@dataclass(frozen=True)
class VehiclePack:
    id: str; name: str; api_version: int
    modules: tuple[ModuleSpec, ...]; default_module: str
    sources: Callable[..., "dict[str, DataSource]"]   # sources(port, *, raw_log_dir=None, state_dir=None) → {id: src} in modules order
    signals_dir: Path; dtc_dir: Path
    actions: tuple["Command", ...]; menus: Mapping[str, list]
    unlinked_ok: Mapping[str, frozenset[str]]; derived_fields: Mapping[str, Mapping[str, dict]]
    writable_signal_modules: tuple[str, ...]      # was server._ALLOWED_MODULES
    module_command_prefixes: tuple[str, ...]      # was server._MODULE_COMMAND_PREFIXES
    faultscan: tuple[FaultReader, ...]; faultscan_unimplemented: tuple[tuple[str, str], ...]
    sniff: SniffSpec; demo: DemoSpec | None; docs: tuple[DocSource, ...]
    layout: Mapping[str, Any]                     # UI manifest (lr_d2/layout.json)
    root: Path                                    # repo/data root for relative paths
    def module(self, mid) -> ModuleSpec | None
    def module_ids(self) -> list[str]
    def canonical(self, mid: str | None) -> str | None   # lower-case, alias→id, unknown unchanged
    def aliases(self) -> dict[str, str]
    def manifest(self) -> dict                    # /pack body (below)
```
**Loader functions:**
- `active_pack()`: cached.
  1. A pack set with `set_active_pack(p)` (tests) wins.
  2. Otherwise read the `ostler.vehicle` entry points through `importlib.metadata.entry_points()`. On Python 3.9 this returns a dict; on 3.10+ use `.select(group=)`. Pick by env `OSTLER_VEHICLE` (an entry-point name or `module:attr`). If none is set, there must be exactly one entry point; more than one raises an error naming them.
  3. If no entry point exists, fall back to the string `_BUILTIN_FALLBACK = "d2diag.vehicles.lr_d2:PACK"`. This is needed because the repo runs uninstalled (pytest `pythonpath`, the Dockerfile and `tools/` all run from the source tree). The fallback is Phase-0-only and is deleted at the split.
- Also provided: `set_active_pack(p | None)`, the `use_pack(p)` context manager, and `canonical_module(mid)`, which is `active_pack().canonical(mid)`.
- Never resolve the pack at import time; every default is resolved lazily so tests can override it.

**`/pack` body:** `{id, name, api_version, default_module, modules:[{id,name,aliases,live}], aliases:{alias:id}, layout}`.

**`tests/fake_pack.py` → `FAKE_PACK`:**
- Modules: `alpha` (fast 0x10, live) and `beta` (`live=False`).
- Data: `tests/fixtures/fake_pack/{signals/alpha.json, dtc/alpha.json}`.
- Actions: `ping` (verified/read/none) and `zap` (planned/gated).
- One menu, alias `a`→`alpha`, a `FaultReader("ALPHA", lambda p: ["A1"])`, sniff fast `{0x10:"alpha"}`, `demo=None`, and layout `{"drive":{"alpha":{"kind":"tiles","tiles":[...]}}}`.
- Its `sources()` returns a fake `DataSource` and an `InfoDataSource`.

### 2. motor↔td5: one canonical id, legacy ids migrated on read
- **Canonical ids are the store ids:** `td5, slabs, bcu, ace, autobox, airbag`. The UI tab, server module key, snapshot `module`, `/fields`, `/catalog` and logbook all use `td5`. ADR-0013 says "drop the alias", and every data file, registry and esp32 header is already keyed `td5`.
- **Legacy aliases are declared once,** in the pack: `ModuleSpec("td5", aliases=("motor",))` and `autobox` aliases `("eat","gearbox")`. Platform code calls `canonical_module()` at every input boundary:
  - HTTP query `?module=`, the `select_module` param and the `/signal` upsert;
  - logbook `_complete_meta` (`meta.modules`), `read_events` (state lines `module`), `SessionStore.captures.norm`;
  - index row build (bump `logbook/index.py SCHEMA_VERSION` to 2 so existing sqlite rebuilds normalized; the filter then needs no `_MODULE_ALIASES`);
  - the community upload rows.
- **Never rewrite files on disk.** Real logs on disk (`logs/sessions/*/meta.json` and `events.jsonl` hold `"motor"`) stay as they are. The UI also canonicalizes via `/pack.aliases` (its `moduleOf()` fallback and `SessionList`).
- **Regenerate the committed demo sessions** with `tools/make_demo_session.py` (synth now emits `td5`). Verify the diff is only `motor`→`td5`. Add a legacy fixture `tests/fixtures/legacy_session_motor/` to cover read-migration.
- **The only intended API change is the id string;** labels and screens stay the same. `catalog.module_summary()` keeps the `{module, store_module, name, coverage}` shape, with `module == store_module`.

### 3. File move map (Step 0, integrator, `git mv` keeps history)
- `src/d2diag/{td5,slabs,bcu,airbag,ace,autobox}/` → `src/d2diag/vehicles/lr_d2/<same>/`. The faultmap JSON files travel with them.
- `signals/{td5,slabs}.json` → `vehicles/lr_d2/signals/`.
- `dtc/*.json` → `vehicles/lr_d2/dtc/`.
- `logbook/demo/2026*/` → `vehicles/lr_d2/demo/sessions/`.
- `web/demo/sniff-demo.txt` → `vehicles/lr_d2/demo/sniff-demo.txt`.
- `logbook/synth.py` → `vehicles/lr_d2/synth.py`.
- `sniff/{library,emulator_map,importer,fault_import}.py` → `vehicles/lr_d2/sniff/`.
- New pack files:
  - `vehicles/__init__.py` (empty);
  - `vehicles/lr_d2/__init__.py` (assembles `PACK`; integrator-owned);
  - `actions.py`, `menus.py`, `catalog_data.py` (`UNLINKED_OK`), `faultscan.py`, `sniff_spec.py`;
  - `sources.py` (Td5/Slabs sources, `DERIVED_FIELDS` keyed `td5`, `_FuelComputer`, `_sig`, `_slabs_*`, `TD5_ACTIONS`, `_SLABS_ACTUATORS`, `_security_message`, `_INJ_PER_REV`, `_DIESEL_G_PER_L`);
  - `layout.json`.
- **Compatibility shims:** one file, `src/d2diag/_compat.py`, installed from `d2diag/__init__.py`.
  - It is a `MetaPathFinder` aliasing `d2diag.{td5,slabs,bcu,airbag,ace,autobox}[.*]` and `d2diag.sniff.{library,emulator_map,importer,fault_import}` and `d2diag.logbook.synth` to the real modules. It returns the same module object, so there are no duplicate copies and `monkeypatch` works through either name.
  - This keeps the ~50 `tools/` and tests importers working.
  - Its test asserts `import d2diag.td5.td5 as a; a is d2diag.vehicles.lr_d2.td5.td5`.
  - Do not use per-package `sys.modules` swaps: those reload submodules twice.
- **`pyproject.toml`:**
  - Drop the `d2diag.signals`, `d2diag.logbook.demo` and `web demo/*.txt` package-data entries.
  - Add `"d2diag.vehicles.lr_d2" = ["layout.json","signals/*.json","dtc/*.json","td5/*.json","slabs/*.json","demo/*.txt","demo/sessions/*/*"]`. This also fixes the dtc and faultmap files currently missing from package-data.
  - Add `[project.entry-points."ostler.vehicle"] lr_d2 = "d2diag.vehicles.lr_d2:PACK"`.
- **Path updates elsewhere:**
  - `Dockerfile:35`, `docker-compose.yml:18`, the `tools/dashboard.py` docstring, `tests/e2e_server.py:35` and `tests/test_replay_api.py:575-583`: replay path becomes `src/d2diag/vehicles/lr_d2/demo/sniff-demo.txt`.
  - `tools/gen_signal_header.py`: import from `d2diag.vehicles.lr_d2.sources` and fix the comment paths, then regenerate `esp32/kline_node/signals_td5.h` (comment-only diff).
  - `esp32/kline_node/live_html.h:77`: new raw path. Deployed firmware falls back to its localStorage cache, so flag this to the owner. Upstream is Leijoma/main.
- **Minimal loader changes in Step 0** so the tree stays green:
  - `signals/__init__.py` and `dtc/__init__.py`: keep the module attribute `_DIR` (default `None`), and route every use through `_dir() = _DIR or active_pack().signals_dir` (for dtc, `dtc_dir`). Tests monkeypatch `_DIR`.
  - `logbook/demo/__init__.py`: `DEMO_ROOT` through module `__getattr__` → `active_pack().demo.sessions_dir`.
- **Docs, at the end:** CONSTITUTION "SSOT path" amendment plus changelog; SCOPE, `docs/architecture.md`, `src/d2diag/CLAUDE.md` and `esp32/CLAUDE.md` paths. Then run `validate_frontmatter.py` and `build_index.py`.

### 4. Hotspot → what platform code calls on the pack
| Hotspot | Replacement |
|---|---|
| catalog.py:34-53 | Delete `UI_MODULE`, `_STORE_ALIASES`, `MODULE_NAMES`, `UNLINKED_OK`, `ui_module_for`. Names come from `pack.module(id).name`, menus from `pack.menus`, drift guard from `pack.unlinked_ok`. Keep `store_module_for = canonical_module` (deprecated wrapper). |
| commands.py:58-121 | Keep `Command`, the enums, `STATIONARY`, `get/for_module/refusal`, plus a new `registry()` built from `pack.actions` and cached per pack. `REGISTRY` stays reachable through module `__getattr__`. `_td5_out`, `ENGINE_OFF`, `BRAKES` and `_ALL` move to `lr_d2/actions.py`. |
| menus.py | `MENUS` through `__getattr__` → `active_pack().menus`; `menu_for(m)`. The D2 dict moves to `lr_d2/menus.py`. |
| faultscan.py:54-80 | Generic `read_all(port, sleep)`: resolve the port, then for each `FaultReader` call `read(real_port)` → `_row`, on exception `_err`, then `sleep(0.5)`. A missing cable gives an `_err` per reader label. Keep `unimplemented_rows()` from `pack.faultscan_unimplemented` and the `_row`/`_err` signatures. The TD5/SLABS/Airbag bodies move verbatim to `lr_d2/faultscan.py`. |
| modscan.py:23, sniff/modules.py:35-36 | `sniff/modules.py` becomes generic: `name_for_address(a, spec=None)`, `fast_init_signal(b, spec=None)`, `scan(b, spec=None)`, `ModuleTracker(spec=None)` with authoritative vs hint semantics kept exactly. Constants are lazily re-exported via `__getattr__`. The address maps and `_airbag/_eat/_ace/_bcu` predicates move to `lr_d2/sniff_spec.py`. `modscan.DEFAULT_FAST/SLOW` are computed from `spec.fast_init` and `slow_init`, plus `extra_scan`. |
| web/sources.py:17-20,130-150,227-261,385-788 | Platform keeps `DataSource`, `InfoDataSource`, `_RawLogPaused`, `_raw_log_path`, `_transport`, `_parse_lids`, `_read_block_cmd`, `_sleep_kw` and the `resolve_serial_port` re-export, with no td5 import. Everything D2 moves to `lr_d2/sources.py`. |
| server.py:39,97-102,264,297 | Delete `_UI_TO_STORE`; `_store_module_for` becomes `canonical_module`. `_fields_list` uses `pack.derived_fields[canonical]`. |
| server.py:215 | `_ALLOWED_MODULES` → `pack.writable_signal_modules`. |
| server.py:433,437,441 | Default `?module=` → `pack.default_module`. |
| server.py:872,885 | `pack.module_command_prefixes`, `commands.registry()`. |
| server.py:2133,2145,2241 | `store_module()` = `source.store_module` or `canonical(self._active)`. |
| server.py:2351 | Unchanged call to `faultscan.read_all` (now generic). |
| server.py `_select` | `_select(canonical(name))`. |
| server.py new route | `GET /pack` (public) → `active_pack().manifest()`. |
| server.py:1951,1959 | "· motor: rpm …" is connection-log prose: leave it and allowlist it in the literal guard. |
| tools/dashboard.py:126-141 | `modules = pack.sources(port, raw_log_dir=…, state_dir=_repo)`. `active = canonical(args.module) or pack.default_module`; add `--module`, keep `--slabs` as a hidden alias. `menus=pack.menus`. Docs built from `pack.docs`; the `--dict-path` override replaces the `optional` answer-key `DocSource`. |
| logbook/channels.py:74 | Glob `pack.signals_dir`, ordered by `pack.modules` (first module wins). |
| logbook/index.py:40 | Normalize at row build; filter with `canonical(module)`. |
| logbook/store.py:51 | `_STORE_MODULE` → `canonical_module`. `SessionStore(demo_root=_PACK)` sentinel → `pack.demo.sessions_dir`. |
| signals/__init__, dtc/__init__ | Platform loaders over `pack.signals_dir` / `pack.dtc_dir` (Step 0). |
| sniff/fault_import.py | Moves to the pack. `sniff/calib.py` is a docstring-only mention. |

### 5. UI (data-driven layout)
- **`lr_d2/layout.json`,** transcribed from `layout.ts`:
  - `group_order`;
  - `drive`: `{td5:{kind:"tiles",tiles:[{signal,label,gauge?,dec?,unit?,scale?}]}, slabs:{kind:"slabs_car",health:true}, bcu:{kind:"body_car"}}`. `per10km` becomes `scale:0.1`, unit "L/mil";
  - `body:{signals,groups}`;
  - `util_lids`;
  - `notices:{slabs:{record_confirm, inputs_banner}}`, replacing the Inputs.tsx:23 and :112 strings;
  - `replay:{group_categories:{slabs:"Chassis/SLABS",...}}`, replacing replay/channels.ts:22.
- **New and changed UI files:**
  - New `ui/src/api/usePack.ts` and `PackSchema` in `api/schemas.ts`.
  - New `ui/src/pack/store.ts`: `setPack`, `getPack`, `usePack`. Non-hook callers keep working.
  - `layout.ts` becomes accessors: `moduleName(m)`, `moduleNames()`, `groupOrder()`, `driveView(m)`, `bodyLayout()`, `utilLids(m)`, `canonicalModule(m)`, falling back to the raw id before load.
  - App fetches `/pack` once at boot (it is local and fast); a failure shows the existing error card.
- **View registry:**
  - New `ui/src/vehicles/registry.ts` (platform) with `registerViews(packId, {slabs_car, body_car})` and `getView(packId, kind)`.
  - `ui/src/vehicles/lr_d2/index.ts` registers views moved from `components/{SlabsCar,BodyCar}.tsx` to `ui/src/vehicles/lr_d2/`.
  - `VehicleBase` stays platform.
  - `main.tsx` imports `./vehicles/lr_d2`. This is the composition root; flag it as an open question for the split.
- **Screens and state:**
  - `Drive.tsx:19-21` dispatches on `driveView(module).kind`, and "tiles" is generic.
  - Delete `catalogModule` (catalog.ts:128) and `format.ts storeModule`; ids are canonical.
  - `replayState.ts:185` fallback → `getPack().default_module`.
  - `live.ts:26` initial module `""`.
  - `ModuleSelect` and `SessionFilters` read `moduleNames()`.
  - `api/schemas.ts:73` comment.
- **Tests:**
  - `test/renderWithApp.tsx` seeds `setPack(packFixture)` and module `"td5"`.
  - Fixtures are renamed: `fields-motor.json`→`fields-td5.json`, `catalog-motor.json`→`catalog-td5.json`; add a new `pack.json`.
  - e2e `smoke.spec.ts:136,239` `switchModule(page,"td5")`.
- Rebuild `src/d2diag/web/static` (generated, committed).
- **New vitest literal guard:** no `"motor"|"td5"|"slabs"|"bcu"` string literals in `ui/src/**` outside `ui/src/vehicles/`, tests and fixtures.

### 6. Tests
- **`tests/test_layering.py`:**
  - Keep the web guard, applied to `vehicles/lr_d2/**` except `lr_d2/sources.py`.
  - **New `test_platform_never_imports_a_pack`:**
    - Platform = every `src/d2diag/**/*.py` except `vehicles/` and `_compat.py`.
    - Resolve relative imports properly: `node.level` plus the file's package. Fail on `d2diag.vehicles*` and on legacy D2 names `d2diag.{td5,slabs,bcu,airbag,ace,autobox}` and `d2diag.sniff.{library,emulator_map,importer,fault_import}`, `d2diag.logbook.synth`.
    - Also fail on any `import_module`/`__import__` whose literal contains "vehicles", except `pack._BUILTIN_FALLBACK`.
  - **New `test_platform_has_no_module_literals`:** AST string constants, excluding docstrings, equal to any lr_d2 module id or alias. The allowlist is only the server log-prose line.
  - **Guard the scan itself:** assert the platform file count is >30 and that `vehicles/lr_d2` is scanned.
- **Platform tests run against FakePack** (new `tests/test_pack.py` and `tests/test_platform_fake_pack.py`):
  - loader: entry-point selection monkeypatched, env override, fallback, multiple-pack error;
  - `canonical()`;
  - `commands.registry`/`refusal`, `catalog.build_catalog`/`module_summary`, menus;
  - `faultscan.read_all` with fake readers;
  - `ModuleTracker`/`modscan` with a fake spec;
  - `DiagServer` with the fake pack: `/pack`, `/fields?module=a` (alias), `select_module`, the gated refusal;
  - logbook alias normalization and the index filter.
- **D2 pack tests stay as they are** (td5, slabs, bcu*, airbag, identifiers, keygen, faults, gen_faultmap, gen_signal_header, importer, fault_import, emulator_map, modules, catalog D2 drift guard, ui_contract, e2e_server). They exercise the real pack through the fallback. Update imports from `d2diag.web.sources` → `d2diag.vehicles.lr_d2.sources` in test_web, test_commands, test_connection_state, test_sessions_api and fake_sources. The `_compat` finder covers the rest.
- **Required green:** `pytest -q`, `cd ui && npm run check && npm run e2e`, `python tools/gen_signal_header.py --check`.

### 7. Work packages (disjoint ownership)
**Step 0 (integrator, serial, ends green):**
- spec;
- baseline golden capture (§8);
- `pack.py` (full);
- `tests/fake_pack.py` plus fixtures;
- `_compat.py` plus the `d2diag/__init__.py` hook;
- all `git mv`s in §3;
- `vehicles/lr_d2/__init__.py` assembling `PACK` from the agreed module names, with temporary stubs that re-export current objects;
- `pyproject.toml`, `Dockerfile`, `docker-compose.yml`;
- the signals/dtc/`DEMO_ROOT` loader tweaks;
- an initial `layout.json` and a hand-written `ui/src/api/fixtures/pack.json`.

Contract frozen in Step 0: canonical ids and aliases, the `/pack` shape, `lr_d2/sources.py` export names, `commands.registry()`, the `read_all` and `sniff.modules` signatures, fixture filenames. `lr_d2/__init__.py`, `pack.py` and `pyproject.toml` stay integrator-only.

**A, platform core plus pack data.**
- Generic code: `catalog.py`, `commands.py`, `menus.py`, `faultscan.py`, `modscan.py`, `sniff/modules.py`, `signals/__init__.py`, `dtc/__init__.py`, `sniff/calib.py`.
- Pack modules: `lr_d2/{actions,menus,catalog_data,faultscan,sniff_spec}.py`, `lr_d2/sniff/*`, plus everything moved under `lr_d2/{td5,…}`.
- Tools: `tools/*` except `dashboard.py` and `make_demo_session.py`; `esp32/kline_node/{signals_td5.h,live_html.h}`.
- Tests: the D2 tests listed in §6, test_layering, test_pack, test_catalog, test_commands, test_faultscan, test_modscan, test_modules, test_menus, test_signal_store, test_dtc, test_sniff, test_capture, test_importer, test_fault_import, `tests/fakes.py`.

**B, server, web and logbook.**
- Web: `web/server.py`, `web/sources.py`, `lr_d2/sources.py`.
- Tools: `tools/dashboard.py`, `tools/make_demo_session.py`.
- Logbook and pack demo: `logbook/{channels,index,store,recorder,demo/__init__}.py`, `lr_d2/synth.py` plus the regenerated demo sessions.
- Tests: `tests/{e2e_server,fake_sources}.py`, test_web, test_connection_state, test_sessions_api, test_replay_api, test_logbook, test_index, test_ui_contract, test_e2e_server, test_notes, test_audio, test_motion, test_export, test_csv_logger, test_platform_fake_pack.
- Generated: `ui/src/api/fixtures/*.json` (regenerated).

**C, UI.** All of `ui/src/**` except fixture JSON; `ui/e2e/*`; `lr_d2/layout.json`; `src/d2diag/web/static/` (rebuilt).

**Integration order:**
1. Merge A, then run `pytest`.
2. Merge B. Run `UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`, then `pytest`.
3. Merge C. Run `npm run check`, `npm run build` (commit static), `npm run e2e`.
4. Update docs and INDEX, then do the golden diff (§8).

### 8. Risks and how to prove no behaviour change
**Golden diff.** Before Step 0, `tools/phase0_golden.py` (scratch, or committed as `tests/fixtures/phase0_golden/` with `tests/test_phase0_golden.py` until the split) dumps:
- every route `test_ui_contract` hits, by value not just shape, with fake sources;
- `/catalog` for all modules, `/fields` and `/faults` for all modules, the coverage map;
- the `refusal()` matrix for all (module, action) × trust × public;
- `read_all_faults` with fakes;
- the per-line `ModuleTracker`/`scan` output over `sniff-demo.txt` and `tests/fixtures`;
- `modscan` DEFAULT_FAST/SLOW;
- `/sessions` plus meta, events and data for both demos;
- `channels.group_for` for all store names.

Re-run it after each merge and compare with `motor→td5` normalization. Any other diff is a bug.

**Known risks:**
- Duplicate module objects through shims: the identity test.
- `monkeypatch(signals._DIR)` semantics: keep the attribute.
- Import-time pack resolution breaking FakePack tests: lazy only.
- The demo-golden test (`test_logbook.py:547`): regenerate the demo, review the diff.
- Index cache: schema bump.
- Old logs: the legacy fixture, plus a manual run of `tools/dashboard.py` on the real `logs/sessions/*` (contains `"motor"`) checking that the list, filters `module=td5` and `module=motor`, and replay all work.
- ESP32 GitHub fetch path: owner decision.
- Hidden D2 literals: the literal guards.
- Docker: `docker build` and the `/snapshot` healthcheck with the new replay path.
- First-paint labels before `/pack` loads: App gates on pack load.

### Critical Files for Implementation
- /home/user/discovery2-diag/src/d2diag/pack.py (new; the contract)
- /home/user/discovery2-diag/src/d2diag/web/server.py
- /home/user/discovery2-diag/src/d2diag/web/sources.py (split to /home/user/discovery2-diag/src/d2diag/vehicles/lr_d2/sources.py)
- /home/user/discovery2-diag/src/d2diag/catalog.py, /home/user/discovery2-diag/src/d2diag/commands.py, /home/user/discovery2-diag/src/d2diag/sniff/modules.py
- /home/user/discovery2-diag/ui/src/layout.ts, /home/user/discovery2-diag/tests/test_layering.py, /home/user/discovery2-diag/tools/dashboard.py
## Changelog

- 2026-10-06: v1.0, approved design (from the Phase 0 planning pass).
