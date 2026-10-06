# Ostler — an open, smart-home-like ecosystem for your car

> **Ostler: an open, smart-home-like ecosystem for your car. It connects the car you already
> have, then lets you add on.**

**Ostler™** starts from the car you already have. A base hardware pack talks to the car's
own buses and makes its systems connected: diagnostics, live data, a session logbook with
replay, place names and GPS, and a mobile-first dashboard. Add-on modules then join over
standard IP networking, the way devices join a smart home. This repository is the
**platform** (the OpenOstler code). Vehicle knowledge ships separately, as **vehicle packs**.

- Website: **[ostler.tech](https://ostler.tech)**
- Code and community: the **[openostler](https://github.com/openostler)** organisation
- Reference pack: the **[Ostler pack for Land Rover Discovery 2](https://github.com/JamesWrightDavid/discovery2-diag)**
  (`d2diag`), covering the Td5 engine, SLABS, BCU, airbag, ACE and the automatic gearbox
  over K-line.

> ⚠️ **Hobby / research project.** Pack data is reverse-engineered from bus traffic and
> community documentation. It is not a finished commercial tool. Use at your own risk, and
> read the safety notes.

## Goals

Ostler is an open, local-first automotive ecosystem: a smart-home-like platform for your
car, on hardware you own. The full statement is in **[GOALS.md](GOALS.md)**; the
architecture is [ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md).

- **A base hardware pack, with diagnostics and telemetry at the core.** It interfaces with
  the car's own buses (K-line, CAN, OBD-II) at the edge and never replaces them. It covers
  the Discovery 2 first, then other Land Rovers, any OBD-II car, modern CAN/UDS and pre-OBD
  cars, each as a community vehicle pack.
- **Add-on modules:** an always-on guardian (GPS tracker and **notify-only alarm**, with
  its own battery and IoT SIM), relay boxes, sensor and button nodes, cameras (dashcam,
  parking, reversing, underbody) and displays. Displays are thin clients of one
  head-unit-first PWA.
- **Standard networking:** every device speaks IP on an automotive-Ethernet backbone
  (10BASE-T1S for modules, Ethernet for cameras, Wi-Fi/USB for screens). Devices are found
  by mDNS and speak VSS-named MQTT. One module contract makes modules interchangeable,
  third-party ones included.
- **Integrations:** COVESA VSS signal paths, OBDb-compatible data, MQTT with Home Assistant
  discovery, OVMS and OwnTracks compatibility. Matter ecosystems are reached through a
  bridge. In smart-home terms, the comparison is "the Home Assistant of the automotive
  world".
- **A decode pipeline** that turns an unknown car into a pack with verified signals.
- **Hard lines:** nothing writes to a car without the safety gates; no EKA or key
  programming; the VIN is never logged or uploaded; private by default, no cloud needed.
- **Anti-bloat:** features are core, add-on (off by default) or moonshot (own ADR).
- **Funding:** official hardware (the base pack and add-on modules) and an optional Ostler
  Cloud subscription, with AGPL code plus a commercial licence.

Done so far: the `VehiclePack` decoupling, the platform/pack repo split, a dev server, a
version tracker and the UI research. Next: the UI seams and head-unit shell, then opt-in
MQTT/Home Assistant.

## What the platform does

- **Comms core:** raw transport (pyserial, an ESP32 bridge), K-line framing with fast and
  5-baud slow init, KWP2000 with a tolerant mode for cheap KKL cables, and a session
  lifecycle (establish → read → release).
- **The `VehiclePack` contract**
  ([ADR-0013](decisions/adr-0013-repo-split-and-vehicle-pack-contract.md)): modules, data
  sources, the signal and fault-meaning stores, actions, menus, the fault scan, sniff
  detection, demo data, docs and the UI layout all come from the active pack. Packs
  register under the entry-point group `openostler.vehicle`. The platform never imports a
  pack.
- **A signal store and a catalog:** declarative LID field mappings with honest confidence
  (`proven` or `candidate`), and a status for every menu item derived from them.
- **The session logbook:** it records only while connected. It has offline GeoNames place
  names with optional OSM Nominatim refinement, notes, audio, IMU acceleration, a SQLite
  index, and CSV, VBO and GPX export.
- **A passive sniff decoder** and capture tooling for reverse engineering.
- **A mobile-first web dashboard:** a stdlib HTTP + SSE server and a React + TypeScript app
  in [`ui/`](ui/). The built app is committed, so running it needs Python only. A
  password-gated `/admin` console adds the mapping tabs.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
# a vehicle pack: the Discovery 2 reference pack (it depends on "openostler", installed above)
pip install --no-deps "d2diag @ git+https://github.com/JamesWrightDavid/discovery2-diag"
pytest -q
```

Tests run without hardware against a simulated half-duplex ECU.

- Platform tests use a fake pack (`tests/fake_pack.py`).
- Integration tests marked `needs_pack` use the Discovery 2 pack. Without it they are
  skipped, with a reason. CI installs the pack and sets `OSTLER_REQUIRE_PACK=1`, so there
  they always run.

Run the dashboard:

```bash
# Against the vehicle (ignition on, stationary); the port is auto-detected when omitted:
PYTHONPATH=src python3 tools/dashboard.py --serial /dev/cu.usbserial-XXXX
# No car: loop the pack's demo sniff log into the admin Decode tab
PYTHONPATH=src python3 tools/dashboard.py --replay pack
```

Then open <http://localhost:8080>, from the same machine or from your phone on the same
network.

- There is no demo mode
  ([ADR-0011](decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md)). The
  dashboard always runs live; you can replay the pack's committed demo sessions from the
  Logs tab.
- For UI work without a car, `PYTHONPATH=src python3 tests/e2e_server.py` serves the
  test-only simulated sources. See [`ui/CLAUDE.md`](ui/CLAUDE.md).
- With no pack installed, the platform stops with an error that names the entry-point
  group and how to install a pack. `OSTLER_VEHICLE` picks one when several are installed.

### Deploying

- **Docker / homelab:** the [`Dockerfile`](Dockerfile) installs the platform plus the
  Discovery 2 pack at `PACK_REF` (`--build-arg PACK_REF=…`, default `main`).
  [`docker-compose.yml`](docker-compose.yml) is the Dokploy stack.
- **Raspberry Pi in the car:** [`tools/deploy.sh`](tools/deploy.sh) mirrors the platform
  and a pack checkout (`PACK_DIR`) to the Pi and restarts the service. For HTTPS (needed
  for the phone mic and motion sensors), see [docs/https_on_the_pi.md](docs/https_on_the_pi.md).
- **Mac testers:** [`mac/install.sh`](mac/install.sh) is a one-paste installer.

### Serial ports

- **macOS:** use `/dev/cu.*`, never `/dev/tty.*`. `resolve_serial_port("auto")` finds
  FTDI, CH34x and CP210x cables.
- **Linux / Pi:** use `/dev/ttyUSB*` or `/dev/serial/by-id/*`; the user must be in
  `dialout`. FTDI cannot do the ~360-baud fast-init trick on Linux, so the transport uses
  an OS-timed `send_break` instead. Set the FTDI latency timer to 1 ms.

## Architecture

```
Web dashboard   (stdlib HTTP + SSE server · React/TS UI, prebuilt — no Node at runtime)
Logbook · catalog · commands · sniff    (generic; vehicle data comes from the active pack)
VehiclePack     (openostler.pack — entry-point group "openostler.vehicle")
KWP2000 → K-Line → Transport            (no vehicle knowledge)
```

[docs/architecture.md](docs/architecture.md) has the code map, and [SCOPE.md](SCOPE.md)
the layering boundary.

## Safety

K-line is a shared bus, and a pack can write to ECUs. The platform enforces a
conservative command gate ([ADR-0008](decisions/adr-0008-unified-status-vocabulary.md)):

- Reads and live data are read-only.
- Actuator tests run only when you press the button, behind a confirmation. They are
  documented as stationary with the ignition on.
- Gated items (security writes, coding) have no runnable action.
- Pack-specific rules live in the pack. For example, the Discovery 2 airbag module is
  read-only by construction.

## Documentation

- [GOALS.md](GOALS.md) says what the project is for and where it is going.
- [INDEX.md](INDEX.md) lists every doc, and [CONSTITUTION.md](CONSTITUTION.md) holds the
  hard rules.
- [decisions/](decisions/CLAUDE.md) holds the ADRs, and [specs/](specs/CLAUDE.md) the
  designs.
- [ADR-0015](decisions/adr-0015-repo-split-executed.md) records what moved where at the
  repo split.
- [CHANGELOG.md](CHANGELOG.md) lists notable changes and the versioning policy.
- [SECURITY.md](SECURITY.md) says how to report a vulnerability, privately.
- [CONTRIBUTING.md](CONTRIBUTING.md) covers licences, the CLA and the checks to run.

## Credits

- The project was started by **leijoma**; their MIT-licensed work stays credited.
- **K-line front-end** know-how (fast-init timing, burst reads, L9637D):
  [muki01/OBD2_K-line_Reader](https://github.com/muki01/OBD2_K-line_Reader) (MIT snapshot; upstream GPL-3.0 since 2026-10-03).
- **UI theme tokens:** [facebook/astryx](https://astryx.atmeta.com/) neutral theme (MIT),
  colour and spacing values only.
- **Place names:** GeoNames `cities1000` (CC BY 4.0) and OpenStreetMap Nominatim (ODbL).

[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) has the full licences and exactly
what was used. Vehicle-specific credits live in each pack.

## License

- **Code:** [AGPL-3.0-or-later](LICENSE). If you run a modified version as a network
  service, you must offer its source to its users. A **commercial licence** (for closed or
  embedded use without the AGPL obligations) is available from the maintainer.
- **Data** (vehicle data in packs, bundled data sets): [CC BY-SA 4.0](LICENSE-DATA),
  unless a third-party licence says otherwise.
- **Per file:** the repo follows [REUSE](https://reuse.software/). Each file's licence
  is in its SPDX header or in [REUSE.toml](REUSE.toml), and the texts are in
  [LICENSES/](LICENSES/).
- **Contributions** are accepted under the [Contributor License Agreement](CLA.md). See
  [CONTRIBUTING.md](CONTRIBUTING.md).
- Versions published before 2026-10-06 were MIT-licensed; copies obtained under those
  terms keep them. Decision: ADR-0012.
- **Trademarks:** "Ostler" and "OpenOstler" are trademarks. The licences grant no rights
  to the names; see [TRADEMARKS.md](TRADEMARKS.md).
