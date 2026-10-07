# Ostler — an open, smart-home-like ecosystem for your car

> **Ostler: an open, smart-home-like ecosystem for your car. It reads your car's
> diagnostics and live data, then grows with add-ons.**

> **Proposed wording (2026-10-07, awaiting the owner; [ADR-0042](decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md)):**
> Ostler is an ecosystem whose main goal is **getting your car's data into apps**. A small
> core (the shell, Diagnose, Trips, Network, and Security once a node exists) reads and
> interprets the car; **add-ons are the product** (Social, Vehicles & Map, Maintenance &
> Garage, Cameras, Integrations), installed from Settings → Add-ons, Home Assistant style.
> One app, no separate apps per feature; every data class starts in ghost; Export all, and
> nothing in core needs an Ostler-run server. Map: [docs/ecosystem.md](docs/ecosystem.md).

**Ostler™** is an open, local-first automotive ecosystem: a smart-home-like platform for
your car. A diagnostic **node** interfaces with the vehicle you already have and turns its
existing systems into a connected IoT platform, with diagnostics and telemetry at the
core. **Ostler Diagnostics** is the node at the OBD port, working alone and offline with
your phone; **Ostler Brain** adds an optional Linux compute box for the full local app,
cameras, replay and analysis; **Ostler Guardian** is the hidden, battery-backed node variant.
Add-on modules join either over standard networking, the way devices join a smart home:
sensor nodes, cameras, I/O and relay modules, displays. Every device speaks IP
(10BASE-T1S for modules, faster Ethernet for cameras), and they all use the same
VSS-named, MQTT-style messages, so modules are interchangeable and integrate with Home
Assistant and the wider IoT world.

This repository is the **platform** (the OpenOstler code). Vehicle knowledge ships
separately, as **vehicle packs**.

- Website: **[ostler.tech](https://ostler.tech)**
- Code and community: the **[openostler](https://github.com/openostler)** organisation
- Reference pack: the **[Ostler pack for Land Rover Discovery 2](https://github.com/openostler/ostler-pack-lr-d2)**
  (`d2diag`), covering the Td5 engine, SLABS, BCU, airbag, ACE and the automatic gearbox
  over K-line.

> ⚠️ **Hobby / research project.** Pack data is reverse-engineered from bus traffic and
> community documentation. It is not a finished commercial tool. Use at your own risk, and
> read the safety notes.

## Goals

The goals, principles, hard lines and near-term roadmap are in **[GOALS.md](GOALS.md)**;
the long-term picture (add-ons, garage and sharing, connectivity, AI-native access) is in
**[references/vision.md](references/vision.md)**, with module ideas in the
[add-ons catalogue](references/research/addons_catalogue.md). The architecture is
[ADR-0027](decisions/adr-0027-ip-everywhere-ecosystem-architecture.md) and
[ADR-0032](decisions/adr-0032-one-node-optional-brain.md) (one node, optional brain) and
[ADR-0039](decisions/adr-0039-product-family-diagnostics-guardian-hub.md) (product names).

- **Ostler Diagnostics and Ostler Brain:** an ESP32 node (optional 4G) alone, or the node
  plus a Brain (a Raspberry Pi today), with diagnostics and telemetry at the core. The node interfaces
  with the car's own buses (K-line, CAN, OBD-II) at the edge and never replaces them: the
  Discovery 2 first, then other Land Rovers, any OBD-II car, modern CAN/UDS and pre-OBD
  cars, each as a community vehicle pack. The guardian is a hidden, battery-backed node
  hardware variant with no outputs.
- **Add-ons:** sensor nodes, cameras, a future I/O / relay module, buttons and displays,
  and more. Each module hosts its own small web page and works on its own. We are making
  a Home Assistant for cars, not reinventing the wheel.
- **Hard lines:** nothing writes to a car except through the node's transmit gate; no EKA
  or key programming in any default path; VIN and identity data are never recorded by
  default and never leave the device; private by default, no cloud needed.
- **Funding:** official hardware (the node, node + brain and add-on modules) and an
  optional Ostler Cloud subscription, with AGPL code plus a commercial licence.

Done so far: the `VehiclePack` decoupling, the platform/pack repo split, a dev server, a
version tracker and the UI research. Next: the UI seams and head-unit shell, then opt-in
MQTT/Home Assistant.

## What the platform does

- **Comms core (the Python lab and reference):** raw transport (pyserial, an ESP32
  bridge), K-line framing with fast and 5-baud slow init, KWP2000 with a tolerant mode for
  cheap KKL cables (a dev-only path), and a session lifecycle (establish → read →
  release). In production the link layer and decoder run on the node in portable C,
  reading the same pack JSON; the Python decoder stays the reference and the fallback.
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
  in [`ui/`](ui/). The built app is committed, so running it needs Python only, plus the
  optional native decoder library. The same app runs on the brain, in Ostler Cloud and on
  the phone as a PWA in a native wrapper (Capacitor) for Bluetooth and local Wi-Fi. A
  password-gated `/admin` console adds the mapping tabs.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
# a vehicle pack: the Discovery 2 reference pack (it depends on "openostler", installed above)
pip install --no-deps "d2diag @ git+https://github.com/openostler/ostler-pack-lr-d2"
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
# With the ESP32 sniffer on the K-line: its live feed in the admin Decode tab
PYTHONPATH=src python3 tools/dashboard.py --serial /dev/cu.usbserial-XXXX --sniff /dev/ttyUSB1
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

The stack above is this repo's Python code, which runs on the **brain** (and in the lab).
In production the car side lives on the **node** ([ADR-0032](decisions/adr-0032-one-node-optional-brain.md)):
it owns the K-line/CAN I/O, decodes to VSS with the portable C decoder from pack JSON,
and holds the **transmit gate, the only path to the car**. The brain never touches the
car; like the phone, the cloud and Home Assistant, it consumes the node's VSS messages
over IP and may mint grants that the node verifies.

[docs/architecture.md](docs/architecture.md) has the code map, and [SCOPE.md](SCOPE.md)
the layering boundary.

## Safety

K-line is a shared bus, and a pack can write to ECUs. The platform enforces a
conservative command gate ([ADR-0008](decisions/adr-0008-unified-status-vocabulary.md)),
which moves to the node in production; action categories and approvals follow
[ADR-0033](decisions/adr-0033-action-categories-and-approvals.md):

- Reads and live data are read-only.
- Actuator tests run only when you press the button, behind a confirmation. They are
  documented as stationary with the ignition on.
- Gated items (security writes, coding) have no runnable action.
- Phone approval of Tier 2–3 works over local links only; remote paths (Tailscale, cloud
  relay) are read-only unless the install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is
  set (off by default, never settable remotely).
- Pack-specific rules live in the pack. For example, the Discovery 2 airbag module is
  read-only by construction.

## Documentation

- [GOALS.md](GOALS.md) says what the project is for and what comes next;
  [references/vision.md](references/vision.md) says where it is going in the long term.
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

## Decisions for the owner

<!-- Draft-only section (2026-10-07): remove once the owner answers. -->

1. **Lead the README with the proposed wording?** Recommend: yes once ADR-0042 is accepted,
   replacing the tagline paragraph and keeping the rest. Alternative: keep the current
   tagline and add the add-on list under "Goals".
