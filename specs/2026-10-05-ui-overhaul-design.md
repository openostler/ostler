---
title: "UI overhaul — every NanoCom function per module, in situ, one status system — design"
area: specs
status: stable
version: 1.1
updated: 2026-10-05
depends_on: [specs/2026-10-01-web-ui-design.md, decisions/adr-0008-unified-status-vocabulary.md, decisions/adr-0007-bcu-security-access.md]
summary: >
  The dashboard shows, for the selected module, everything the NanoCom exposes on Faults / Inputs / Outputs / Settings / Utilities, each item with one derived status (verified / candidate / sniff / untranscribed) and a safety class. The module is picked in the header, the connection lives in a sheet that opens on loss, the Capabilities and Connect pages go, and Stable mode shows only verified items. The contract: GET /catalog, the command registry and the snapshot connection fields.
---

# UI overhaul — design

## Context

The owner approved this design on 2026-10-05 ("merge and go ahead"). Problems it fixes:

- There is no Settings page, and Utilities is only a raw LID dump.
- SLABS procedures sit under Outputs.
- Coverage lives on a separate Capabilities page that drifts from the code.
- Six status vocabularies are in use.
- The Connect page interrupts navigation.
- A lost connection is invisible, so stale values look live.
- The Experimental lock is client-only.

The research is summarised in the plan:
- Autel, VCDS, Tesla Toolbox and NanoCom use module → Faults / Live data / Active tests /
  Service functions.
- Autel keeps a persistent connection indicator plus the battery voltage.
- Home Assistant never shows stale values as live.
- VCDS shows a banner while a test is still running.
- NN/g: friction proportional to consequence, and honest placeholders at most two levels
  deep.

## Information architecture

**Header**
- `ModuleSelect` dropdown: module name and coverage %. Switching keeps the current tab.
- Car battery voltage.
- `ConnectionPill`, which opens the `ConnectionSheet`.
- ⚙ Preferences.
- `ActiveTestBanner` (with a Stop button) whenever `snap.active_test` is set.

**Tabs:** Drive · Faults · Inputs · Outputs · Settings · Utilities. Admin keeps Map ·
Capture · Docs. The Connect and Capabilities pages are removed.

**What goes where (the NanoCom split):**
- **Outputs:** simple on/off/pulse tests (lamps, relays, valves, pump, injectors,
  buzzer).
- **Utilities:** multi-step or latched procedures, calibrations, bleeding, height,
  security, adaptive reset and key programming. Sub-groups follow the NanoCom, at most two
  levels. The raw LID dump sits under an "Advanced" group, shown in Experimental only.
- **Inputs:** stays one page.
- **Settings:** identity and configuration.

## Status model

See ADR-0008. Every item has exactly one status:

| status | meaning |
|---|---|
| `verified` | proven on a car |
| `candidate` | mapped or implemented, unproven |
| `sniff` | transcribed from the NanoCom, not mapped |
| `untranscribed` | a NanoCom page we know exists, fields not transcribed yet (placeholder) |

Each item also has a safety class: `read | actuator | service | gated`.

**Derivation, in `src/openostler/catalog.py`.** The first rule that applies wins:

1. **`sig` (signal-store name):**
   - Pick the record: the one whose `lid@offset` equals the item's `at` (for example
     `"1C@4"`) if `at` is given, otherwise the first record with that name. Length
     variants share a name (`signals.BY_NAME` keeps the first).
   - Map `proven` → verified and `candidate` → candidate.
   - A `sig` that isn't in the store is an error caught by the tests.
2. **`actions` (list of action names in `commands.REGISTRY`):**
   - If every action is gated: `sniff` when unimplemented, and safety `gated`.
   - Otherwise take the worst non-gated action: planned → `sniff`, experimental →
     `candidate`, all verified → `verified`.
   - The item's safety is the most severe action safety, ranked
     gated > service > actuator > read.
3. **Otherwise the hand-written `status`**, which must be one of `verified | candidate |
   sniff | untranscribed`. Hand-written `verified` is allowed only for session and fault
   items (connection, read/clear faults), which have no store or registry entry.

An item that has `sig` or `actions` **must not** also carry a hand `status`. The test
`tests/test_catalog.py` enforces this.

**Legacy view (`/map`, admin):** `/map` and `DiagServer.coverage()` keep their old shape
for the admin Map tab:
- items keep `status ∈ ok/maybe/todo`;
- `coverage()` keeps `{ok, maybe, total}`.

`catalog.legacy_status()` converts: verified→ok, candidate→maybe, sniff/untranscribed→todo.

## Menu data model (`src/openostler/*/menu.py`)

The module menus remain lists of groups.

**Group:**
```python
{"id": "inputs-fuelling", "page": "inputs", "cat": "Inputs — Fuelling / live (22)",
 "nanocom": "td5_engine/inputs_fuelling", "items": [...]}
```
- `page` is one of `session | faults | inputs | outputs | settings | utilities`.
- `cat` is the display title.
- Keep the substrings "Fuelling" and "Switches" in those group titles (`tests/test_sniff.py`
  matches on them).
- An optional `parent` gives a Utilities sub-menu (for example BCU "Key programming" →
  "Key codes / UPDATE"). Two levels at most.

**Item:**
```python
{"id": "air-flow", "name": "12. Air Flow (kg/hr)", "sig": "maf_sensor", "at": "1C@4",
 "lid": "1c", "ref": "21 1C@4 ×0.1 kg/h", "note": "",
 "actions": ["..."],            # instead of sig, for outputs/utilities
 "safety": "read",              # optional override; default read for sig, else from actions
 "status": "sniff",             # ONLY when there is no sig/actions
 "untranscribed": True, "pages": 4}   # placeholder for a NanoCom page not yet transcribed
```

Rules:
- `id` is a slug, unique per module.
- `name` stays as today wherever it already exists, because admin localStorage keys and
  CoverageMap readings use it.
- An `untranscribed` item stands for a whole NanoCom page or group whose fields are not
  transcribed yet, for example the gearbox "Pressures (4 pages)".

## API contract

**`GET /catalog?module=<ui id>`** is public, and `motor` is accepted for td5. It returns:

```json
{"module": "motor", "store_module": "td5",
 "coverage": {"verified": 0, "candidate": 0, "sniff": 0, "untranscribed": 0, "total": 0},
 "pages": [{"id": "inputs", "title": "Inputs", "coverage": {…},
   "groups": [{"id": "inputs-fuelling", "title": "Inputs — Fuelling / live (22)",
               "parent": null, "nanocom": "td5_engine/inputs_fuelling",
     "items": [{"id": "air-flow", "name": "…", "status": "verified", "safety": "read",
                "sig": "maf_sensor", "lid": "1c", "ref": "…", "note": "",
                "placeholder": false, "pages": null,
                "actions": [{"action": "…", "label": "…", "status": "verified|experimental|planned",
                             "safety": "…", "confirm": "none|preconditions|typed",
                             "preconditions": ["…"], "stop": "…", "ref": "…"}]}]}]}]}
```

Pages come in the fixed order faults, inputs, outputs, settings, utilities, with session
folded into faults. A page with no groups is still listed, with zero coverage.

**`GET /catalog`** (no module) returns `{"modules": [{"module", "store_module", "name",
"coverage"}…]}` for the header dropdown.

**Function:** `catalog.build_catalog(store_module: str) -> dict` is the page structure
above without the outer `module` key; the server adds it. Also
`catalog.module_summary() -> list` and `catalog.legacy_status(status) -> str`.

**`POST /command`** checks `commands.refusal(store_module, action, trust=params.get("trust",""),
public=self.public)`:
- A refused action answers `{ok:false, error}` with HTTP 400.
- The UI sends `params.trust = "experimental"` when the user is in Experimental mode.

New server commands:
- `disconnect`: release the session and pause polling. `conn` becomes `disconnected`.
- `connect`: resume polling.
- `set_port {port}`: `auto` or a device path; it releases and reconnects.
- New source actions: `security_status` and `read_identity` (Td5 only).
  `read_identity` returns `{ok, identity:{part_no, vin_masked, …}}`, and the VIN never
  goes into logs, CSV or community uploads.

**Snapshot additions** (all optional; `status` stays for the legacy pages):
- `conn`: `disconnected | connecting | connected | lost | reconnecting | error`
  - `lost`: the first poll that fails after `connected`.
  - `reconnecting`: re-establishing after a loss.
  - `error`: never connected (no cable, no answer).
- `ts`: server epoch seconds of the snapshot.
- `battery_v`: car battery in volts (Td5 `battery` or SLABS `battery`), or null.
- `port`: `{spec, resolved, candidates[]}` from `ports.list_serial_ports()`.
- `active_test`: `{action, label, since, stop}` while a latched test (one with `stop`) is
  on, otherwise null.

## Modes

| | Stable (`prefs.trust="trusted"`) | Experimental |
|---|---|---|
| Items | `verified` only | all four statuses |
| Status chips, coverage bars, placeholders, exp banner | hidden | shown |
| Candidate actions | hidden | runnable, with the confirm from the registry |
| Gated items | hidden | visible, locked, no button |
| Module dropdown | modules with ≥ 1 verified item | all, with coverage % |
| Advanced (raw LID dump) | hidden | shown |
| Empty page | "Nothing verified here yet — switch to Experimental to see what's in progress." | — |

## Connection UX

The `ConnectionSheet` shows:
- the connect phases (moved from the Connect page);
- mock/live mode;
- the auto-selected port, with candidates for override;
- Retry, Disconnect and Connect.

When it opens:
- automatically after 3 s in `error | lost | disconnected`;
- never over Consent;
- once dismissed, it stays closed until `conn` changes.

**Staleness:**
- `Readout` greys a value and shows "last seen N s ago" when a signal hasn't updated for
  more than 5 s, or the SSE link is down.
- Values are never shown as live when they are stale.

## Testing

- **`tests/test_catalog.py`:**
  - every derivation rule;
  - every `sig` resolves;
  - every action is registered;
  - no link plus hand status on the same item;
  - gated items have no runnable action;
  - airbag is read/gated only;
  - unique ids and coverage sums;
  - drift guard: every store signal is linked from some item, or listed in
    `catalog.UNLINKED_OK`.
- **`tests/test_commands.py`:** the registry matches the source dispatch in both directions.
- **Server tests:**
  - `/catalog` is public;
  - refusals for gated, experimental-without-trust and public-mode actions;
  - the lost → reconnecting → connected sequence;
  - `disconnect`, `connect` and `set_port`.
- **Vitest:**
  - visibility filter, CoverageBar and status chip;
  - sheet auto-open;
  - stale readout;
  - Stable hides chips and placeholders;
  - no Connect or Capabilities tab.
- **Playwright** smoke tests updated.

## Changelog

- 2026-10-05: v1.0, approved and implemented.
- 2026-10-05: v1.1. The header and connection changes are specified in
  [2026-10-05-session-logbook-design.md](2026-10-05-session-logbook-design.md) (Part A):
  - no "D2 Diag" title, a labelled module control and a "% mapped" pill;
  - `ConnectionNotice` on every module page;
  - a 60 s re-prompt.
