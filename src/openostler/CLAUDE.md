# src/openostler/

The platform package (`openostler`): comms core → interpretation → web consumer. The map is in
`docs/architecture.md`.

## Files

- `transport/`, `kline/`, `kwp2000/`, `session.py`, `ports.py` — the comms core.
- `obd/` — the SAE J1979 (OBD-II) service layer shared by K-line and CAN: request model and
  pacing (`link.py`), pure decoders (`decode.py`), `PidTable` from a pack's store
  (`pids.py`), `Vehicle.Ostler.Diagnostics.*` (`diagnostics.py`), VIN handling and identity
  scrub (`vin.py`), the Mode 04 gate (`clear.py`) and `J1979` (`j1979.py`). It imports no
  transport; the K-line adapter is `kline/obd_link.py`. Mode 08 is never sent.
- `testing/` — shipped stdlib test fakes (`FakeObdLink`) for the platform and pack tests.
- `pack.py` — the `VehiclePack` contract and loader (`active_pack()`, entry-point group
  `openostler.vehicle`, legacy `ostler.vehicle` still read; no pack installed →
  `NoVehiclePackError`); module ids are canonical, aliases are migrated on read
  (ADR-0013, ADR-0015). Packs are separate distributions (the D2 pack is `d2diag`).
- `signals/`, `dtc/` — the platform loaders over the active pack's data.
- `sniff/` — capture parsing, generic module detection (`modules.py`, driven by the pack's
  `SniffSpec`), automap and calibration.
- `commands.py` — the command registry: every module action's status, safety class and confirm
  level (ADR-0008); the server's `/command` gate (`refusal()`).
- `catalog.py` — per-module pages (faults/inputs/outputs/settings/utilities) built from the
  menus, with each item's status derived from the signal store or the registry (`/catalog`).
- `gps/` — NMEA parsing (`nmea.py`) and fix sources (`reader.py`: USB, mock, replay; ADR-0009).
- `logbook/` — always-on session recording (`recorder.py`), the session store and `/sessions`
  data (`store.py`), VBO/GPX/CSV exports; the demo logs come from the pack
  (`tools/make_demo_session.py`). Location never leaves the device.
  Also per-session `events.jsonl` (whole-app replay), `notes.jsonl`, audio tracks and acceleration
  channels (`motion.py`, `audio.py`, `notes.py`; ADR-0010).
- `layouts.py` + `layout_limits.json` — the `ostler.layout/1` validator (drive-modes spec
  §8.2); `layout_store.py` — the `ui_layouts` store (`<state dir>/settings.sqlite`: vid ×
  profile × class × kind × id, resolution user → car → pack → generated, the 7-day Before
  reset snapshot, held writes, the selected Drive mode per display; §8.3).
- `imu/` — Pi IMU (LSM6DS family over `/dev/i2c-1`, stdlib ioctl) and a mock IMU.
- `faultscan.py`, `modscan.py`, `menus.py`, `community/` — cross-module helpers
  (`modscan.py` = the read-only address scan) and opt-in upload.
- `web/` — consumer: stdlib HTTP + SSE server, data sources; `web/layout_api.py` serves
  `/ui/layouts` and `/ui/drive-mode` with Park to edit (R1/R7, the `Ostler-Layout-Class` header). `web/static/` is the built
  UI from `ui/` (generated — rebuild, never edit); `dashboard*.html` are legacy references.

## Editing rules

- Core modules never import `web`; platform modules never import a pack (`d2diag`) or name
  a module id (`tests/test_layering.py`). Platform tests use `tests/fake_pack.py`;
  integration tests on the D2 pack are marked `needs_pack`.
- Obey the protocol rules in `CONSTITUTION.md` (release(), SLABS polling, tolerant).
- Every change comes with a hardware-free test using `tests/fakes.py`.
